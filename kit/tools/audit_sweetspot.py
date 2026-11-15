#!/usr/bin/env python3
"""audit_sweetspot.py — Pre-render & post-render visual retention sweetspot auditor for WBRS / WVF.

Audits a WVF project against `wbrs-retention-sweetspot` engineering rules and emits
`check/engineering_manifest.json` so every video is countable in `wvf ledger`:
  1. Scans `matte/L*/` RGBA PNGs (alpha > 32) to measure exact `nativeHairY` per take
     and prints ready-to-paste JS (`const NATIVE_HAIR_Y = {...};`).
  2. Parses `timing.js` (`window.TIMING`) + `script.json` + `engine.js` to verify:
     - 4–6s visual state pulse (allowing 8s takes when `engine.js` triggers mid-take sub-cuts).
     - Cold-open visual proof (`0.0–1.5s`): flags projects whose fullscreen/UI demos wait > 8.5s
       without an opening visual flash (preventing the 93% Shorts swipe / 0:01 TikTok drop-off).
     - Executive duration band (`<= 64s`) and Collectible End-Sheet entry (`<= 56.0s`) so viewers
       actually reach the saveable summary card.
     - Pure narrative setup/bridge lines in `script.json` that announce tests instead of showing them.
  3. Checks `index.html` / `style.css` / `engine.js` for forbidden `#flash` strobes,
     early `#ribbon` wipes (< 7.0s), `mode: 'half'` horizontal seams, Z-Depth stack (`#zback`),
     `< 0.5s` pie/donut charts, `84px` causal cursor, and collectible end-sheet (`#s9-sheet`).
  4. Audits ALL `story_*.html` files in the project (keeping `story_v2` anchored to
     `story_nuevo_video.html` plus `stories_audited` for multi-story pairs like
     `story_tikal_tinta.html`) for the Instagram Link Sticker corridor (`y: 1255..1415 px`).
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


PURE_SETUP_BRIDGE_PATTERNS = (
    r"\bpusimos a los dos a\b",
    r"\bpero atento a la segunda prueba\b",
    r"\bles pedimos crear\b",
    r"\bvamos a poner a prueba\b",
    r"\bhicimos dos pruebas\b",
)


def _read_utf8(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _line_t0(ln: dict) -> float:
    return float(ln.get("t0", ln.get("start", 0.0)) or 0.0)


def _line_t1(ln: dict) -> float:
    return float(ln.get("t1", ln.get("end", 0.0)) or 0.0)


def parse_timing_js(project_root: str) -> dict:
    timing_path = os.path.join(project_root, "timing.js")
    if not os.path.isfile(timing_path):
        return {}
    raw = _read_utf8(timing_path)
    match = re.search(r"window\.TIMING\s*=\s*(\{.*?\});", raw, flags=re.S)
    if not match:
        return {}
    blob = match.group(1)
    try:
        return json.loads(blob)
    except ValueError:
        # Support relaxed JS object literals used in quick scaffolds/tests (e.g. { totalDuration: 42.0, lines: [{id:'L01',...}] })
        normalized = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', blob)
        normalized = normalized.replace("'", '"')
        normalized = re.sub(r",\s*([}\]])", r"\1", normalized)
        try:
            return json.loads(normalized)
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


def load_script_items(project_root: str) -> list[dict]:
    script_path = os.path.join(project_root, "script.json")
    if not os.path.isfile(script_path):
        return []
    try:
        data = json.loads(_read_utf8(script_path))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def load_line_cameras(project_root: str, line_ids: list[str]) -> dict[str, str]:
    cameras: dict[str, str] = {}
    for item in load_script_items(project_root):
        lid = item.get("id", "")
        cam_code = detect_camera_code(str(item.get("camera", "")) + " " + str(item.get("visual", "")))
        if lid and cam_code:
            cameras[lid] = cam_code

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
    fname = os.path.basename(story_path)
    src = _read_utf8(story_path)
    issues = []
    warnings = []

    has_zback = bool(re.search(r"#zback|z-index:\s*1[2-9]", src))
    is_visual_proof_story = bool(re.search(r"video|<canvas|tikal|tinta|demo|split", src, flags=re.I))
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
                f"{fname}: #story-cap top={cap_top}px invade el corredor del Sticker IG (1255..1415px)."
            )
    if ig_row_match:
        row_top = int(ig_row_match.group(1))
        if 1255 <= row_top <= 1425:
            corridor_clean = False
            issues.append(
                f"{fname}: #igRow top={row_top}px invade el corredor del Sticker IG (1255..1415px)."
            )

    if fname == "story_nuevo_video.html" and not has_zback:
        warnings.append(f"{fname} no declara capa #zback (Z-Depth detrás del presentador).")
    if not has_net_switch:
        warnings.append(f"{fname} no detecta parámetro ?net=ig / ?net=tt.")

    return {
        "file": fname,
        "present": True,
        "has_zback": has_zback,
        "is_visual_proof_story": is_visual_proof_story,
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
    serie_src = _read_utf8(os.path.join(project_root, "serie.js")) if os.path.isfile(os.path.join(project_root, "serie.js")) else ""
    combined_ui = "\n".join([index_src, style_src, engine_src, serie_src])

    # 1. Matte & nativeHairY scan
    hair_map = scan_native_hair_y(project_root)

    # 2. Timing & visual state pulse analysis
    timing = parse_timing_js(project_root)
    lines = timing.get("lines", [])
    duration_sec = float(timing.get("duration", timing.get("totalDuration", 0.0)) or 0.0)
    if duration_sec == 0.0 and lines:
        duration_sec = max(_line_t1(ln) for ln in lines)
    line_ids = [ln.get("id", "") for ln in lines if ln.get("id")]
    cameras = load_line_cameras(project_root, line_ids)

    effective_pulses: list[float] = []
    for ln in lines:
        lid = ln.get("id", "?")
        span = round(_line_t1(ln) - _line_t0(ln), 3)
        sub_cuts = count_mid_cuts_in_engine(engine_src + "\n" + serie_src, lid)
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
            span = _line_t1(ln) - _line_t0(ln)
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

    if duration_sec > 64.0 and not allow_long:
        warnings.append(
            f"Duración crítica {duration_sec:.2f}s (> 64s): penaliza tasa de completos y mata Guardados al final. Meta WBRS: 44–62s."
        )
    elif duration_sec > 52.0 and not allow_long:
        warnings.append(
            f"Duración total {duration_sec:.2f}s supera la banda ejecutiva recomendada (38–52s). Usa --allow-long si es deliberado."
        )

    # 2b. Cold-open visual proof gate (0.0–1.5s) & collectible sheet entry timestamp
    fullscreen_demo_lines = [ln for ln in lines if ln.get("cam") is False]
    first_visual_proof_sec = None
    has_cold_open_flash = bool(
        re.search(r"cold[_-]?open|hookPreview|t\s*<\s*1\.[2-8]", engine_src + "\n" + serie_src, flags=re.I)
        or (fullscreen_demo_lines and _line_t0(fullscreen_demo_lines[0]) <= 2.0)
    )
    if fullscreen_demo_lines:
        first_visual_proof_sec = round(0.0 if has_cold_open_flash else _line_t0(fullscreen_demo_lines[0]), 2)
        if first_visual_proof_sec > 8.5 and not has_cold_open_flash:
            warnings.append(
                f"Evidencia visual tardía: la primera demo pantalla completa ({fullscreen_demo_lines[0].get('id')}) "
                f"entra recién en {first_visual_proof_sec:.1f}s (> 8.5s) sin cold-open visual en 0.0–1.4s "
                "(causa directa de 93% swipe en YouTube Shorts y abandono 0:01 en TikTok)."
            )

    # 2c. Pure setup/bridge lines in script.json ("show-while-telling" check)
    bridge_lines_detected: list[str] = []
    for item in load_script_items(project_root):
        lid = item.get("id", "?")
        txt = str(item.get("spoken_text") or item.get("text") or "").lower()
        if any(re.search(pat, txt) for pat in PURE_SETUP_BRIDGE_PATTERNS):
            bridge_lines_detected.append(lid)
    if bridge_lines_detected:
        warnings.append(
            f"Tomas puente puramente narrativas detectadas ({', '.join(bridge_lines_detected)}): "
            "evita anunciar la prueba durante 6–7s antes de mostrarla; entra directo sobre el visual en vivo."
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
    has_collectible_sheet = bool(re.search(r"s9-sheet|guide-sheet|guardar\s+gu[íi]a|cheat-sheet|map-card", combined_ui, flags=re.I))

    collectible_sheet_start_sec = None
    if lines and (has_collectible_sheet or len(lines) >= 6):
        # Typically the closing summary card sits in the last 1-2 lines
        anchor_idx = -2 if len(lines) >= 8 else -1
        collectible_sheet_start_sec = round(_line_t0(lines[anchor_idx]), 2)
        if collectible_sheet_start_sec > 56.0 and not allow_long:
            warnings.append(
                f"Mapa/guía coleccionable entra muy tarde (~{collectible_sheet_start_sec:.1f}s > 56.0s): "
                "menos del 5% de espectadores llega a verla, reduciendo Guardados a cero en Instagram."
            )

    # 4. Multi-Story audit (story_nuevo_video.html + any companion visual-proof story_*.html)
    story_files = sorted(glob.glob(os.path.join(project_root, "story_*.html")))
    stories_audited = [audit_story_file(sp) for sp in story_files]
    primary_story_path = os.path.join(project_root, "story_nuevo_video.html")
    if os.path.isfile(primary_story_path):
        story_audit = next((s for s in stories_audited if s["file"] == "story_nuevo_video.html"), audit_story_file(primary_story_path))
    elif stories_audited:
        story_audit = stories_audited[0]
    else:
        story_audit = {"present": False}

    for st in stories_audited:
        issues.extend(st.get("issues", []))
        warnings.extend(st.get("warnings", []))

    has_dual_story_pair = len(stories_audited) >= 2

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
        "first_visual_proof_sec": first_visual_proof_sec,
        "has_cold_open_visual_flash": has_cold_open_flash,
        "bridge_lines_detected": bridge_lines_detected,
        "collectible_sheet_start_sec": collectible_sheet_start_sec,
        "cameras_detected": cameras,
        "native_hair_y": hair_map,
        "has_zdepth_hook": bool(has_zdepth_hook or story_audit.get("has_zback")),
        "has_pie_charts": has_pie_charts,
        "has_causal_cursor": has_causal_cursor,
        "has_collectible_sheet": has_collectible_sheet,
        "flash_absent": not flash_active,
        "full_canvas_seamless": not mode_half,
        "story_v2": story_audit,
        "stories_audited": stories_audited,
        "has_dual_story_pair": has_dual_story_pair,
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
    if manifest.get("first_visual_proof_sec") is not None:
        print(
            f"   🎬 Primera demo completa: {manifest['first_visual_proof_sec']}s · "
            f"Cold-open visual (0–1.5s)={manifest['has_cold_open_visual_flash']} · "
            f"Entrada mapa final={manifest.get('collectible_sheet_start_sec')}s"
        )
    if manifest["native_hair_y"]:
        js_pairs = ", ".join(f"{k}: {v}" for k, v in sorted(manifest["native_hair_y"].items()))
        print(f"   📐 nativeHairY medido en matte/: const NATIVE_HAIR_Y = {{ {js_pairs} }};")
    for st in manifest.get("stories_audited", []):
        print(
            f"   📱 Story [{st['file']}]: Z-Depth={st['has_zback']} · VisualProof={st['is_visual_proof_story']} · "
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
