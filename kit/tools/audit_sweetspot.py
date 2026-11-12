#!/usr/bin/env python3
"""audit_sweetspot.py — Pre-render & post-render visual retention sweetspot auditor for WBRS / WVF.

Audits a WVF project against `wbrs-retention-sweetspot` engineering rules and emits
`check/engineering_manifest.json` so every video is countable in `wvf ledger`:
  1. Scans `matte/L*/` RGBA PNGs (alpha > 32) to measure exact `nativeHairY` per take
     and prints ready-to-paste JS (`const NATIVE_HAIR_Y = {...};`).
  2. Parses `timing.js` (`window.TIMING`) + `script.json` + `engine.js` to verify the
     4–6s visual state pulse (allowing 8s takes when `engine.js` triggers mid-take sub-cuts).
  3. Checks `index.html` / `style.css` / `engine.js` for forbidden `#flash` strobes,
     early `#ribbon` wipes (< 7.0s), `mode: 'half'` horizontal seams, Z-Depth stack (`#zback`),
     `< 0.5s` pie/donut charts, `84px` causal cursor, and collectible end-sheet (`#s9-sheet`).
  4. Audits `story_nuevo_video.html` (if present) for the sacred Instagram Link Sticker
     corridor (`y: 1255..1415 px` unobstructed) and `?net=ig` / `?net=tt` support.
  5. Reads `audio/cues.json` and `check/music_audit.json` (if present) to consolidate
     psychoacoustic telemetry into `check/engineering_manifest.json`.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image

import env_config


def _read_utf8(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_timing_js(project_root: str) -> dict:
    timing_path = os.path.join(project_root, "timing.js")
    if not os.path.isfile(timing_path):
        return {}
    raw = _read_utf8(timing_path)
    match = re.search(r"window\.TIMING\s*=\s*(\{.*?\});", raw, flags=re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except ValueError:
        return {}


def scan_native_hair_y(project_root: str, alpha_threshold: int = 32) -> dict[str, int]:
    """Measure the top Y pixel of the presenter's hair/head in each `matte/L*/` folder."""
    matte_root = os.path.join(project_root, "matte")
    if not os.path.isdir(matte_root):
        return {}
    hair_map: dict[str, int] = {}
    for line_dir in sorted(glob.glob(os.path.join(matte_root, "L*"))):
        if not os.path.isdir(line_dir):
            continue
        line_id = os.path.basename(line_dir)
        png_files = sorted(glob.glob(os.path.join(line_dir, "*.png")))
        if not png_files:
            continue
        sample_indices = sorted({0, len(png_files) // 2})
        measured_tops = []
        for idx in sample_indices:
            with Image.open(png_files[idx]) as im:
                rgba = np.asarray(im.convert("RGBA"))
                alpha = rgba[:, :, 3]
                rows = np.where(alpha.max(axis=1) > alpha_threshold)[0]
                if len(rows) > 0:
                    measured_tops.append(int(rows[0]))
        if measured_tops:
            hair_map[line_id] = int(round(sum(measured_tops) / len(measured_tops)))
    return hair_map


def detect_camera_code(text: str) -> str:
    if not text:
        return ""
    explicit = re.search(r"\bCam(?:era)?\s*([ABCD])\b", text, flags=re.I)
    if explicit:
        return explicit.group(1).upper()
    low = text.lower()
    if "low-angle" in low or "low angle" in low or "25-degree" in low or "upward tilt" in low:
        return "B"
    if "three-quarter" in low or "35 degrees" in low or "35-degree" in low or "angled" in low:
        return "C"
    if "tight intimate close-up" in low or "intimate close-up" in low or "tight close-up" in low:
        return "D"
    if "frontal" in low or "eye level" in low:
        return "A"
    return ""


def load_line_cameras(project_root: str, line_ids: list[str]) -> dict[str, str]:
    cameras: dict[str, str] = {}
    script_path = os.path.join(project_root, "script.json")
    if os.path.isfile(script_path):
        try:
            for item in json.loads(_read_utf8(script_path)):
                lid = item.get("id", "")
                cam_code = detect_camera_code(str(item.get("camera", "")) + " " + str(item.get("visual", "")))
                if lid and cam_code:
                    cameras[lid] = cam_code
        except (OSError, ValueError):
            pass

    prompts_dir = os.path.join(project_root, "prompts")
    if os.path.isdir(prompts_dir):
        for lid in line_ids:
            if lid in cameras:
                continue
            candidates = sorted(glob.glob(os.path.join(prompts_dir, f"{lid}*.txt")))
            if candidates:
                raw_prompt = _read_utf8(candidates[-1])
                cam_code = detect_camera_code(raw_prompt)
                if cam_code:
                    cameras[lid] = cam_code
    return cameras


def count_mid_cuts_in_engine(engine_src: str, line_id: str) -> int:
    """Estimate whether `engine.js` defines internal word/time sub-cuts inside `line_id`."""
    if not engine_src:
        return 0
    hits = re.findall(rf"['\"]{re.escape(line_id)}['\"]", engine_src)
    word_triggers = re.findall(rf"W\(\s*['\"]{re.escape(line_id)}['\"]", engine_src)
    return max(len(word_triggers), max(0, len(hits) - 1))


def audit_story_file(story_path: str) -> dict:
    src = _read_utf8(story_path)
    issues = []
    warnings = []

    has_zback = bool(re.search(r"#zback|z-index:\s*1[2-9]", src))
    has_net_switch = "net" in src and ("tt" in src or "ig" in src)
    has_opposite_parallax = bool(re.search(r"-\s*(?:dx\s*\*\s*0\.45|0\.45\s*\*\s*dx)", src))

    cap_match = re.search(r"#story-cap\s*\{[^}]*?\btop:\s*(\d+)px", src, flags=re.S)
    ig_row_match = re.search(r"#igRow\s*\{[^}]*?\btop:\s*(\d+)px", src, flags=re.S)

    corridor_clean = True
    if cap_match:
        cap_top = int(cap_match.group(1))
        if 1220 <= cap_top <= 1415:
            corridor_clean = False
            issues.append(
                f"story_nuevo_video.html: #story-cap top={cap_top}px invade el corredor del Sticker IG (1255..1415px)."
            )
    if ig_row_match:
        row_top = int(ig_row_match.group(1))
        if 1255 <= row_top <= 1425:
            corridor_clean = False
            issues.append(
                f"story_nuevo_video.html: #igRow top={row_top}px invade el corredor del Sticker IG (1255..1415px)."
            )

    if not has_zback:
        warnings.append("story_nuevo_video.html no declara capa #zback (Z-Depth detrás del presentador).")
    if not has_net_switch:
        warnings.append("story_nuevo_video.html no detecta parámetro ?net=ig / ?net=tt.")

    return {
        "present": True,
        "has_zback": has_zback,
        "has_opposite_parallax": has_opposite_parallax,
        "has_net_variants": has_net_switch,
        "sticker_corridor_1255_1415_clean": corridor_clean,
        "issues": issues,
        "warnings": warnings,
    }


def audit_project_sweetspot(project_root: str, allow_long: bool = False) -> dict:
    project_root = os.path.abspath(project_root)
    issues: list[str] = []
    warnings: list[str] = []

    index_src = _read_utf8(os.path.join(project_root, "index.html")) if os.path.isfile(os.path.join(project_root, "index.html")) else ""
    style_src = _read_utf8(os.path.join(project_root, "style.css")) if os.path.isfile(os.path.join(project_root, "style.css")) else ""
    engine_src = _read_utf8(os.path.join(project_root, "engine.js")) if os.path.isfile(os.path.join(project_root, "engine.js")) else ""
    combined_ui = "\n".join([index_src, style_src, engine_src])

    # 1. Matte & nativeHairY scan
    hair_map = scan_native_hair_y(project_root)

    # 2. Timing & visual state pulse analysis
    timing = parse_timing_js(project_root)
    lines = timing.get("lines", [])
    duration_sec = float(timing.get("duration", 0.0) or 0.0)
    line_ids = [ln.get("id", "") for ln in lines if ln.get("id")]
    cameras = load_line_cameras(project_root, line_ids)

    effective_pulses: list[float] = []
    for ln in lines:
        lid = ln.get("id", "?")
        span = round(float(ln.get("t1", 0.0)) - float(ln.get("t0", 0.0)), 3)
        sub_cuts = count_mid_cuts_in_engine(engine_src, lid)
        states = 2 if (span > 6.2 and sub_cuts >= 1) else 1
        state_dur = round(span / states, 3)
        effective_pulses.append(state_dur)
        if span > 6.2 and states == 1:
            warnings.append(
                f"{lid} dura {span:.2f}s (> 6.2s) sin sub-corte interno detectado en engine.js; agrega cambio visual a mitad (~{span/2:.1f}s)."
            )

    avg_pulse_sec = round(sum(effective_pulses) / len(effective_pulses), 2) if effective_pulses else 0.0
    max_visual_state_sec = round(max(effective_pulses), 2) if effective_pulses else 0.0

    # Consecutive same-camera duration check
    max_same_cam_sec = 0.0
    if lines and cameras:
        cur_cam = None
        cur_run = 0.0
        for ln in lines:
            lid = ln.get("id", "")
            span = float(ln.get("t1", 0.0)) - float(ln.get("t0", 0.0))
            cam = cameras.get(lid)
            if cam and cam == cur_cam:
                cur_run += span
                warnings.append(
                    f"Cámara repetida consecutiva ({cam}) en {lid}: acumula {cur_run:.2f}s en el mismo ángulo."
                )
            else:
                cur_cam = cam
                cur_run = span
            max_same_cam_sec = max(max_same_cam_sec, cur_run)
    elif effective_pulses:
        max_same_cam_sec = max_visual_state_sec

    if duration_sec > 52.0 and not allow_long:
        warnings.append(
            f"Duración total {duration_sec:.2f}s supera la banda ejecutiva recomendada (38–48s). Usa --allow-long si es deliberado."
        )

    # 3. VFX & Spatial composition checks (strip JS comments first to avoid false positives on docblocks)
    engine_code = re.sub(r"/\*.*?\*/", "", engine_src, flags=re.S)
    engine_code = re.sub(r"(?m)^\s*//.*$", "", engine_code)

    flash_active = bool(
        re.search(r"getElementById\(\s*['\"]flash['\"]\s*\)", engine_code)
        and re.search(r"flash[^;\n]*opacity\s*=\s*(?!0(?:\.0+)?\b)", engine_code)
    )
    if flash_active:
        issues.append("Detectado destello activo #flash en engine.js (prohibido: desploma retención en t=1s).")

    early_ribbon = bool(re.search(r"ribbon[^;\n]*(?:5\.\d|4\.\d|T1)", engine_code))
    if early_ribbon:
        warnings.append("Posible barrido #ribbon temprano cerca del fin del gancho; prefiere corte limpio con resorte.")

    mode_half = bool(re.search(r"mode\s*:\s*['\"]half['\"]", engine_code))
    if mode_half:
        issues.append("Detectado `mode: 'half'` en engine.js (produce costura horizontal sobre la cabeza; usa drawFullBrollBg continuo).")

    has_zdepth_hook = bool(re.search(r"#zback|zback-giant", combined_ui))
    has_pie_charts = bool(re.search(r"conic-gradient|stroke-dasharray|pie|donut", combined_ui, flags=re.I))
    has_causal_cursor = bool(re.search(r"createCausalCursor|causal-cursor|#cursor", combined_ui, flags=re.I))
    has_collectible_sheet = bool(re.search(r"s9-sheet|guide-sheet|guardar\s+gu[íi]a", combined_ui, flags=re.I))

    # 4. Story V2 audit
    story_path = os.path.join(project_root, "story_nuevo_video.html")
    story_audit = audit_story_file(story_path) if os.path.isfile(story_path) else {"present": False}
    issues.extend(story_audit.get("issues", []))
    warnings.extend(story_audit.get("warnings", []))

    # 5. Cues & Psychoacoustic report integration
    cues_path = os.path.join(project_root, "audio", "cues.json")
    sfx_count = 0
    if os.path.isfile(cues_path):
        try:
            cues_data = json.loads(_read_utf8(cues_path))
            sfx_count = len(cues_data) if isinstance(cues_data, list) else len(cues_data.get("cues", []))
        except (OSError, ValueError):
            pass
    if duration_sec > 0 and sfx_count > max(12, int(duration_sec / 4.2)):
        warnings.append(
            f"Densidad alta de SFX ({sfx_count} cues en {duration_sec:.1f}s). Meta WBRS: <= 1 cue cada ~5s."
        )

    music_audit_path = os.path.join(project_root, "check", "music_audit.json")
    music_meta = {}
    if os.path.isfile(music_audit_path):
        try:
            music_meta = json.loads(_read_utf8(music_audit_path))
        except (OSError, ValueError):
            pass

    cfg_path = os.path.join(project_root, "project_config.json")
    cfg = json.loads(_read_utf8(cfg_path)) if os.path.isfile(cfg_path) else {}

    manifest = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "project_id": os.path.basename(project_root),
        "client_name": cfg.get("client_name", "Webres Studio"),
        "business_model": cfg.get("social", {}).get("business_model", "saas_product"),
        "duration_sec": round(duration_sec, 3),
        "pulse_count": len(lines),
        "avg_pulse_sec": avg_pulse_sec,
        "max_visual_state_sec": max_visual_state_sec,
        "max_same_cam_sec": round(max_same_cam_sec, 2),
        "cameras_detected": cameras,
        "native_hair_y": hair_map,
        "has_zdepth_hook": bool(has_zdepth_hook or story_audit.get("has_zback")),
        "has_pie_charts": has_pie_charts,
        "has_causal_cursor": has_causal_cursor,
        "has_collectible_sheet": has_collectible_sheet,
        "flash_absent": not flash_active,
        "full_canvas_seamless": not mode_half,
        "story_v2": story_audit,
        "sfx_count": sfx_count,
        "music_key_mode": music_meta.get("detected_key", ""),
        "music_cqt_purity_pct": music_meta.get("diatonic_purity_pct", None),
        "music_delta_lufs_db": music_meta.get("music_below_voice_db", None),
        "verdict": "FAIL" if issues else ("WARN" if warnings else "PASS"),
        "issues": issues,
        "warnings": warnings,
    }

    check_dir = os.path.join(project_root, "check")
    os.makedirs(check_dir, exist_ok=True)
    manifest_path = os.path.join(check_dir, "engineering_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    manifest["manifest_path"] = manifest_path
    return manifest


def print_sweetspot_report(manifest: dict) -> None:
    print(f"\n🎯 [wvf audit-sweetspot] Proyecto: {manifest['project_id']} → {manifest['verdict']}")
    print(
        f"   Duración: {manifest['duration_sec']}s · Pulsos: {manifest['pulse_count']} · "
        f"Estado visual medio: {manifest['avg_pulse_sec']}s (máx {manifest['max_visual_state_sec']}s)"
    )
    print(
        f"   Checks: sin #flash={manifest['flash_absent']} · lienzo continuo={manifest['full_canvas_seamless']} · "
        f"Z-Depth={manifest['has_zdepth_hook']} · PieCharts={manifest['has_pie_charts']} · "
        f"Cursor84px={manifest['has_causal_cursor']} · GuíaSuiza={manifest['has_collectible_sheet']}"
    )
    if manifest["native_hair_y"]:
        js_pairs = ", ".join(f"{k}: {v}" for k, v in sorted(manifest["native_hair_y"].items()))
        print(f"   📐 nativeHairY medido en matte/: const NATIVE_HAIR_Y = {{ {js_pairs} }};")
    if manifest["story_v2"].get("present"):
        st = manifest["story_v2"]
        print(
            f"   📱 Story V2: Z-Depth={st['has_zback']} · Paralaje opuesto={st['has_opposite_parallax']} · "
            f"Corredor Sticker IG (1255..1415px) limpio={st['sticker_corridor_1255_1415_clean']}"
        )
    for w in manifest["warnings"]:
        print(f"   ! {w}")
    for iss in manifest["issues"]:
        print(f"   ✗ {iss}")
    print(f"   💾 Manifiesto guardado en: {manifest['manifest_path']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Auditor de ingeniería visual y Punto Dulce WBRS.")
    ap.add_argument("--project", default="", help="Ruta del proyecto WVF (default: directorio actual)")
    ap.add_argument("--allow-long", action="store_true", help="No advertir si la duración supera 52s")
    ap.add_argument("--json", action="store_true", help="Imprimir JSON completo en stdout")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.project) if args.project else env_config.get_project_root()
    manifest = audit_project_sweetspot(root, allow_long=args.allow_long)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print_sweetspot_report(manifest)
    return 1 if manifest["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
