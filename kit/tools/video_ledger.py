#!/usr/bin/env python3
"""WVF Video Ledger & WBRS Retention/Business Score (0-100) Calculator.

Tracks every produced video across brands in `video-factory/research/video_ledger.jsonl`,
linking technical engineering telemetry (`check/engineering_manifest.json`) with
real multi-platform retention & business conversion metrics (`check/social_analytics.json`
across TikTok Studio, YouTube Studio Shorts, Meta Business Suite, and Instagram).

Usage:
  wvf ledger compare
  wvf ledger score --project /path/to/video
  wvf ledger record --project /path/to/video --exclude-self-follows 1 --notes "4h YT Shorts + 35h TT"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FACTORY_ROOT = HERE.parents[1]
DEFAULT_LEDGER_PATH = FACTORY_ROOT / "research" / "video_ledger.jsonl"


def _clamp01(val: float) -> float:
    return max(0.0, min(1.0, float(val)))


def _extract_window_str(entry_val: Any) -> str:
    if isinstance(entry_val, str) and entry_val.strip():
        return entry_val.strip()
    if isinstance(entry_val, dict):
        return str(
            entry_val.get("recommended_deploy_window")
            or entry_val.get("deploy_window")
            or "pendiente"
        )
    return "pendiente"


def compute_wbrs_score(metrics: dict[str, Any]) -> dict[str, Any]:
    """Compute the fair-weighted 4-pillar WBRS Retention & Business Score (0-100 pts).

    Pillars:
      1. Hook (35 pts): R_2s / 55%, R_3s / 40%, R_5s / 28% (or YT Stayed% / 55% if TT curve absent)
      2. Body (30 pts): Dynamically normalized over MEASURED channels (`None` != `0.0`):
         - R_15s / 16%
         - TT_avg_s / 13s
         - IG_avg_s / 12s (omitted when Meta Business Suite was not measured)
         - YT_avg_s / 18s (included when YouTube Shorts engaged watch duration is measured)
      3. Intent (25 pts): Per 500 qualified engaged views -> Saves/6, (Comments+Shares+Reposts)/3, NetFollows/2
      4. Funnel (10 pts): Story CTR / 3.5% (or Search SEO% / 3.0% when Story CTR unmeasured) [5 pts]
         + IG >=70% non-followers (2.5 pts) + clean no-AI-badge (2.5 pts)
    """
    rv = metrics.get("retention_vector") or {}
    r02 = float(rv.get("r_02s", metrics.get("r_02s", 0.0)) or 0.0)
    r03 = float(rv.get("r_03s", metrics.get("r_03s", 0.0)) or 0.0)
    r05 = float(rv.get("r_05s", metrics.get("r_05s", 0.0)) or 0.0)
    r15_raw = rv.get("r_15s", metrics.get("r_15s", None))
    yt_stayed = float(metrics.get("yt_stayed_to_watch_pct", 0.0) or 0.0)

    if r02 > 0 or r03 > 0 or r05 > 0:
        hook_norm = (_clamp01(r02 / 55.0) + _clamp01(r03 / 40.0) + _clamp01(r05 / 28.0)) / 3.0
    elif yt_stayed > 0:
        hook_norm = _clamp01(yt_stayed / 55.0)
    else:
        hook_norm = 0.0
    hook_pts = round(35.0 * hook_norm, 1)

    body_components: list[float] = []
    channels_measured: list[str] = []
    if r15_raw is not None:
        body_components.append(_clamp01(float(r15_raw) / 16.0))
    if metrics.get("tt_avg_watch_s") is not None:
        body_components.append(_clamp01(float(metrics["tt_avg_watch_s"]) / 13.0))
        channels_measured.append("tiktok")
    if metrics.get("ig_avg_watch_s") is not None:
        body_components.append(_clamp01(float(metrics["ig_avg_watch_s"]) / 12.0))
        channels_measured.append("instagram_meta")
    if metrics.get("yt_avg_watch_s") is not None and float(metrics["yt_avg_watch_s"]) > 0:
        body_components.append(_clamp01(float(metrics["yt_avg_watch_s"]) / 18.0))
        channels_measured.append("youtube_shorts")

    body_norm = (sum(body_components) / len(body_components)) if body_components else 0.0
    body_pts = round(30.0 * body_norm, 1)

    qualified_views = float(
        metrics.get("qualified_engaged_views")
        or metrics.get("total_organic_views")
        or 0.0
    )
    scale_500 = max(qualified_views / 500.0, 0.25)
    saves = float(metrics.get("total_saves", 0) or 0.0)
    comments = float(metrics.get("total_comments", 0) or 0.0)
    shares = float(metrics.get("total_shares_dms", 0) or 0.0)
    follows = float(metrics.get("new_followers", 0) or 0.0)

    saves_norm = _clamp01((saves / scale_500) / 6.0)
    conv_norm = _clamp01(((comments + shares) / scale_500) / 3.0)
    follows_norm = _clamp01((follows / scale_500) / 2.0)
    intent_pts = round(25.0 * (saves_norm + conv_norm + follows_norm) / 3.0, 1)

    story_ctr_raw = metrics.get("story_ctr_pct", None)
    search_pct = max(
        float(metrics.get("tt_search_pct", 0.0) or 0.0),
        float(metrics.get("yt_search_pct", 0.0) or 0.0),
        float(metrics.get("search_discovery_pct", 0.0) or 0.0),
    )
    if story_ctr_raw is not None and float(story_ctr_raw) > 0:
        top_funnel_pts = 5.0 * _clamp01(float(story_ctr_raw) / 3.5)
    elif search_pct > 0:
        top_funnel_pts = 5.0 * _clamp01(search_pct / 3.0)
    elif story_ctr_raw is not None:
        top_funnel_pts = 5.0 * _clamp01(float(story_ctr_raw) / 3.5)
    else:
        top_funnel_pts = 0.0

    ig_non_followers = float(metrics.get("ig_non_followers_pct", 0.0) or 0.0)
    ig_clean = bool(metrics.get("ig_clean_no_ai_badge", True))
    non_follower_pts = 2.5 * _clamp01(ig_non_followers / 70.0)
    badge_pts = 2.5 if ig_clean else 0.0
    funnel_pts = round(top_funnel_pts + non_follower_pts + badge_pts, 1)

    total = round(hook_pts + body_pts + intent_pts + funnel_pts, 1)
    return {
        "hook_pts": hook_pts,
        "body_pts": body_pts,
        "intent_pts": intent_pts,
        "funnel_pts": funnel_pts,
        "wbrs_score": total,
        "channels_measured": channels_measured,
    }


def _interp_curve_pct(curve_points: list[dict[str, Any]], target_sec: float) -> float:
    """Extract retention percentage at `target_sec` from [{t, pct}, ...] points."""
    if not curve_points:
        return 0.0
    best = min(curve_points, key=lambda p: abs(float(p.get("t", p.get("sec", 0.0))) - target_sec))
    if abs(float(best.get("t", best.get("sec", 0.0))) - target_sec) <= 1.2:
        return float(best.get("pct", best.get("y", 0.0)) or 0.0)
    return 0.0


def build_entry_from_project(project_dir: Path, overrides: argparse.Namespace | None = None) -> dict[str, Any]:
    """Assemble a ledger record from a WVF project folder's manifests and analytics."""
    project_dir = project_dir.resolve()
    cfg_path = project_dir / "project_config.json"
    eng_path = project_dir / "check" / "engineering_manifest.json"
    soc_path = project_dir / "check" / "social_analytics.json"

    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    eng = json.loads(eng_path.read_text(encoding="utf-8")) if eng_path.is_file() else {}
    soc = json.loads(soc_path.read_text(encoding="utf-8")) if soc_path.is_file() else {}

    social_cfg = cfg.get("social") or {}
    brand = cfg.get("client_name") or social_cfg.get("instagram_handle") or "Webres Studio"
    business_model = (
        social_cfg.get("business_model")
        or (soc.get("configuration") or {}).get("business_model")
        or soc.get("business_model")
        or "b2b_high_ticket"
    )

    tt_videos = (
        (soc.get("tiktok_studio") or {}).get("videos")
        or (soc.get("tiktok") or {}).get("videos")
        or soc.get("tiktok_videos")
        or []
    )
    yt_shorts = (
        (soc.get("youtube_studio") or {}).get("shorts")
        or (soc.get("youtube") or {}).get("shorts")
        or soc.get("youtube_shorts")
        or []
    )
    meta_items = (
        (soc.get("meta_business_suite") or {}).get("items")
        or (soc.get("meta") or {}).get("items")
        or soc.get("meta_items")
        or []
    )
    ig_reels = (
        (soc.get("instagram") or {}).get("reels")
        or soc.get("instagram_reels")
        or []
    )

    tt0 = tt_videos[0] if tt_videos else {}
    yt0 = yt_shorts[0] if yt_shorts else {}
    ig0 = ig_reels[0] if ig_reels else {}
    ig_meta = next(
        (m for m in meta_items if m.get("platform_channel") == "instagram" or not m.get("is_crossposted")),
        meta_items[0] if meta_items else {},
    )
    fb_meta = next((m for m in meta_items if m.get("platform_channel") == "facebook"), {})

    curve = tt0.get("retention_curve_points") or []
    r01 = _interp_curve_pct(curve, 1.0)
    r02 = _interp_curve_pct(curve, 2.0)
    r03 = _interp_curve_pct(curve, 3.0)
    r05 = _interp_curve_pct(curve, 5.0)
    r10 = _interp_curve_pct(curve, 10.0)
    r15 = _interp_curve_pct(curve, 15.0)
    r30 = _interp_curve_pct(curve, 30.0)

    if overrides:
        if getattr(overrides, "r02", None) is not None:
            r02 = overrides.r02
        if getattr(overrides, "r03", None) is not None:
            r03 = overrides.r03
        if getattr(overrides, "r05", None) is not None:
            r05 = overrides.r05
        if getattr(overrides, "r15", None) is not None:
            r15 = overrides.r15

    tt_views = int(tt0.get("views", 0) or 0)
    yt_views = int(yt0.get("views", 0) or 0)
    yt_engaged_views = int(yt0.get("engaged_views", 0) or 0)
    ig_views = int(ig0.get("views", ig_meta.get("views", 0)) or 0)
    fb_views = int(fb_meta.get("views", 0) or 0)
    total_views = tt_views + yt_views + ig_views + fb_views
    qualified_views = tt_views + ig_views + fb_views + (yt_engaged_views if yt_engaged_views > 0 else yt_views)

    total_saves = int(tt0.get("saves", 0) or 0) + int(ig0.get("saves", ig_meta.get("saves", 0)) or 0)
    total_comments = (
        int(tt0.get("comments", 0) or 0)
        + int(ig0.get("comments", ig_meta.get("comments", 0)) or 0)
        + int(fb_meta.get("comments", 0) or 0)
        + int(yt0.get("comments", 0) or 0)
    )
    total_shares = (
        int(tt0.get("shares", 0) or 0)
        + int(tt0.get("reposts", 0) or 0)
        + int(ig0.get("shares", ig_meta.get("shares", 0)) or 0)
        + int(fb_meta.get("shares", 0) or 0)
    )

    yt_net_subs = (
        int(yt0["net_subscribers"])
        if "net_subscribers" in yt0
        else int(yt0.get("subscribers_raw", 0) or 0)
    )
    raw_followers = int(tt0.get("new_followers", 0) or 0) + int(ig_meta.get("follows", 0) or 0) + yt_net_subs
    self_follows_excl = int(getattr(overrides, "exclude_self_follows", 0) or 0) if overrides else 0
    # Avoid double-subtracting if yt0 already excluded self_subscribers
    if self_follows_excl > 0 and yt0.get("self_subscribers_excluded", 0) == 0:
        new_followers = max(0, raw_followers - self_follows_excl)
    else:
        new_followers = max(0, raw_followers)
        self_follows_excl = max(self_follows_excl, int(yt0.get("self_subscribers_excluded", 0) or 0))

    tt_avg_s: float | None = float(tt0["average_watch_seconds"]) if tt0.get("average_watch_seconds") else None
    ig_avg_s: float | None = float(ig_meta["average_play_seconds"]) if ig_meta.get("average_play_seconds") else None
    yt_avg_s: float | None = (
        float(yt0["average_view_duration_seconds"])
        if yt0.get("average_view_duration_seconds")
        else None
    )

    story_ctr_override = getattr(overrides, "story_ctr", None) if overrides else None
    story_ctr: float | None = (
        float(story_ctr_override)
        if story_ctr_override is not None
        else (float(soc["story_ctr_pct"]) if soc.get("story_ctr_pct") is not None else None)
    )

    tt_search_pct = float((tt0.get("traffic_sources") or {}).get("Buscar", 0.0) or 0.0)
    yt_search_pct = float(yt0.get("search_traffic_percent", 0.0) or 0.0)
    yt_stayed_pct = float(yt0.get("stayed_to_watch_percent", 0.0) or 0.0)
    yt_desktop_pct = float(
        (yt0.get("device_types") or {}).get(
            "Ordenador",
            (yt0.get("device_types") or {}).get("Computer", 0.0),
        )
        or 0.0
    )

    ig_non_followers = float(ig0.get("non_followers_percent", 75.0 if not ig0 else 0.0) or 0.0)
    ig_clean = not bool(ig0.get("has_ai_content_label", False))

    if overrides:
        if getattr(overrides, "tt_avg", None) is not None:
            tt_avg_s = overrides.tt_avg
        if getattr(overrides, "ig_avg", None) is not None:
            ig_avg_s = overrides.ig_avg
        if getattr(overrides, "yt_avg", None) is not None:
            yt_avg_s = overrides.yt_avg
        if getattr(overrides, "views", None) is not None:
            total_views = overrides.views
            if qualified_views == 0:
                qualified_views = overrides.views
        if getattr(overrides, "yt_views", None) is not None:
            yt_views = overrides.yt_views
        if getattr(overrides, "saves", None) is not None:
            total_saves = overrides.saves
        if getattr(overrides, "comments", None) is not None:
            total_comments = overrides.comments
        if getattr(overrides, "shares", None) is not None:
            total_shares = overrides.shares
        if getattr(overrides, "follows", None) is not None:
            new_followers = max(0, overrides.follows - (self_follows_excl if yt0.get("self_subscribers_excluded", 0) == 0 else 0))
        if getattr(overrides, "search_pct", None) is not None:
            yt_search_pct = max(yt_search_pct, overrides.search_pct)

    metrics_payload = {
        "total_organic_views": total_views,
        "qualified_engaged_views": qualified_views if qualified_views > 0 else total_views,
        "tt_views": tt_views,
        "yt_views": yt_views,
        "yt_engaged_views": yt_engaged_views,
        "ig_views": ig_views,
        "fb_views": fb_views,
        "tt_avg_watch_s": tt_avg_s,
        "ig_avg_watch_s": ig_avg_s,
        "yt_avg_watch_s": yt_avg_s,
        "yt_stayed_to_watch_pct": yt_stayed_pct,
        "yt_desktop_pct": yt_desktop_pct,
        "tt_search_pct": tt_search_pct,
        "yt_search_pct": yt_search_pct,
        "tt_full_watch_pct": float(tt0.get("watched_full_percent", 0.0) or 0.0),
        "total_saves": total_saves,
        "total_comments": total_comments,
        "total_shares_dms": total_shares,
        "new_followers": new_followers,
        "self_follows_excluded": self_follows_excl,
        "story_ctr_pct": story_ctr,
        "ig_non_followers_pct": ig_non_followers,
        "ig_clean_no_ai_badge": ig_clean,
        "ig_caption_edited_post_publish": bool(ig0.get("caption_edited_post_publish", False)),
        "retention_vector": {
            "r_01s": r01,
            "r_02s": r02,
            "r_03s": r03,
            "r_05s": r05,
            "r_10s": r10,
            "r_15s": r15,
            "r_30s": r30,
        },
    }

    score_breakdown = compute_wbrs_score(metrics_payload)
    rel_id = getattr(overrides, "video_id", None) if overrides else None
    if not rel_id:
        try:
            rel_id = str(project_dir.relative_to(FACTORY_ROOT.parent))
        except ValueError:
            rel_id = project_dir.name

    opt_windows = (
        soc.get("optimal_publish_windows")
        or social_cfg.get("optimal_publish_windows")
        or {}
    )

    windows_dict = {
        "tiktok": _extract_window_str(opt_windows.get("tiktok")),
        "instagram": _extract_window_str(opt_windows.get("instagram")),
        "facebook": _extract_window_str(opt_windows.get("facebook")),
    }
    if opt_windows.get("youtube"):
        windows_dict["youtube"] = _extract_window_str(opt_windows.get("youtube"))

    return {
        "video_id": rel_id,
        "title": (
            (getattr(overrides, "title", None) if overrides else None)
            or yt0.get("title")
            or tt0.get("title")
            or tt0.get("caption", "")[:70]
            or project_dir.name
        ),
        "brand": brand,
        "business_model": business_model,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "publish_date": (
            (getattr(overrides, "publish_date", None) if overrides else None)
            or tt0.get("published_date")
            or dt.date.today().isoformat()
        ),
        "engineering": {
            "duration_s": eng.get("duration_sec", eng.get("total_duration_s", 0.0)),
            "takes_count": eng.get("pulse_count", eng.get("takes_count", 0)),
            "avg_visual_pulse_s": eng.get("avg_pulse_sec", eng.get("avg_visual_pulse_s", 0.0)),
            "max_visual_state_s": eng.get("max_visual_state_sec", eng.get("max_visual_state_s", 0.0)),
            "first_visual_proof_s": eng.get("first_visual_proof_sec"),
            "collectible_sheet_start_s": eng.get("collectible_sheet_start_sec"),
            "has_z_depth_text": eng.get("has_zdepth_hook", eng.get("has_z_depth_text", False)),
            "has_dual_story_pair": eng.get("has_dual_story_pair", False),
            "zero_white_flashes": eng.get("flash_absent", eng.get("zero_white_flashes", True)),
            "story_sticker_corridor_clean": (eng.get("story_v2") or {}).get(
                "sticker_corridor_1255_1415_clean",
                eng.get("story_sticker_corridor_clean", True),
            ),
        },
        "optimal_publish_windows": windows_dict,
        "metrics": metrics_payload,
        "score": score_breakdown,
        "notes": (getattr(overrides, "notes", None) if overrides else None) or "",
    }


def load_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for raw in ledger_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def save_ledger(ledger_path: Path, entries: list[dict[str, Any]]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(item, ensure_ascii=False) for item in entries) + ("\n" if entries else "")
    ledger_path.write_text(text, encoding="utf-8")


def upsert_entry(ledger_path: Path, entry: dict[str, Any]) -> list[dict[str, Any]]:
    entries = load_ledger(ledger_path)
    vid = entry["video_id"]
    replaced = False
    for idx, existing in enumerate(entries):
        if existing.get("video_id") == vid:
            entries[idx] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)
    save_ledger(ledger_path, entries)
    return entries


def format_comparison_markdown(entries: list[dict[str, Any]], brand_filter: str = "") -> str:
    rows = [e for e in entries if not brand_filter or brand_filter.lower() in str(e.get("brand", "")).lower()]
    if not rows:
        return "No hay videos registrados todavía en `video_ledger.jsonl`."

    lines = [
        "### Ledger Histórico Contable WBRS (`0–100 pts`)",
        "",
        "| Fecha | Video (`video_id`) | Marca | Vistas Org. | Dur. | Gancho (`/35`) | Cuerpo (`/30`) | Intención (`/25`) | Embudo (`/10`) | **WBRS Score** | Δ vs Previo |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    prev_score: float | None = None
    for item in rows:
        sc = item.get("score") or compute_wbrs_score(item.get("metrics") or {})
        total = float(sc.get("wbrs_score", 0.0))
        delta_str = "—" if prev_score is None else f"{total - prev_score:+.1f}"
        prev_score = total
        eng = item.get("engineering") or {}
        met = item.get("metrics") or {}
        views_tot = int(met.get("total_organic_views", 0) or 0)
        dur = f"{float(eng.get('duration_s', 0.0)):.0f}s" if eng.get("duration_s") else "—"
        lines.append(
            f"| `{item.get('publish_date', '—')}` | `{item.get('video_id')}` | {item.get('brand', '—')} "
            f"| `{views_tot:,}` | `{dur}` | `{sc['hook_pts']:.1f}` | `{sc['body_pts']:.1f}` "
            f"| `{sc['intent_pts']:.1f}` | `{sc['funnel_pts']:.1f}` | **`{total:.1f} / 100`** | `{delta_str}` |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WVF Video Ledger & WBRS Score (0-100) Manager")
    sub = parser.add_subparsers(dest="subcommand")

    def add_common_project_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--project", default=".", help="Ruta del proyecto de video")
        p.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH), help="Ruta a video_ledger.jsonl")
        p.add_argument("--video-id", help="Identificador único (ej. noticias/tech-2026-11-08)")
        p.add_argument("--title", help="Título corto del video")
        p.add_argument("--publish-date", help="Fecha YYYY-MM-DD de publicación")
        p.add_argument("--r02", type=float, help="Retención (%%) en 0:02")
        p.add_argument("--r03", type=float, help="Retención (%%) en 0:03")
        p.add_argument("--r05", type=float, help="Retención (%%) en 0:05")
        p.add_argument("--r15", type=float, help="Retención (%%) en 0:15")
        p.add_argument("--tt-avg", type=float, help="Promedio seg TikTok")
        p.add_argument("--ig-avg", type=float, help="Promedio seg Instagram")
        p.add_argument("--yt-avg", type=float, help="Promedio seg YouTube Shorts")
        p.add_argument("--views", type=int, help="Vistas orgánicas totales")
        p.add_argument("--yt-views", type=int, help="Vistas YouTube Shorts")
        p.add_argument("--saves", type=int, help="Guardados totales")
        p.add_argument("--comments", type=int, help="Comentarios totales")
        p.add_argument("--shares", type=int, help="Compartidos / Reposts / DMs totales")
        p.add_argument("--follows", type=int, help="Nuevos seguidores")
        p.add_argument("--exclude-self-follows", type=int, default=0, help="Descontar suscripciones/seguidores propios de prueba")
        p.add_argument("--story-ctr", type=float, help="CTR (%%) de Story de lanzamiento")
        p.add_argument("--search-pct", type=float, help="Porcentaje (%%) de tráfico por Búsqueda SEO")
        p.add_argument("--notes", help="Diagnóstico contable en 1 línea")

    p_rec = sub.add_parser("record", help="Calcula WBRS Score y registra/actualiza el video en video_ledger.jsonl")
    add_common_project_flags(p_rec)

    p_score = sub.add_parser("score", help="Calcula WBRS Score de un proyecto sin modificar el ledger")
    add_common_project_flags(p_score)

    p_cmp = sub.add_parser("compare", help="Muestra la tabla comparativa histórica de videos auditados")
    p_cmp.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH), help="Ruta a video_ledger.jsonl")
    p_cmp.add_argument("--brand", default="", help="Filtrar por nombre de marca/cliente")
    p_cmp.add_argument("--json", action="store_true", help="Imprimir salida en JSON")

    args = parser.parse_args(argv)
    cmd = args.subcommand or "compare"

    if cmd == "compare":
        entries = load_ledger(Path(args.ledger))
        if getattr(args, "json", False):
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            print(format_comparison_markdown(entries, getattr(args, "brand", "")))
        return 0

    entry = build_entry_from_project(Path(args.project), args)
    sc = entry["score"]
    print(
        f"📊 WBRS Score [{entry['video_id']}]: {sc['wbrs_score']:.1f} / 100 "
        f"(Gancho {sc['hook_pts']:.1f}/35 · Cuerpo {sc['body_pts']:.1f}/30 · "
        f"Intención {sc['intent_pts']:.1f}/25 · Embudo {sc['funnel_pts']:.1f}/10)"
    )
    if cmd == "record":
        ledger_path = Path(args.ledger)
        upsert_entry(ledger_path, entry)
        print(f"✓ Registrado en: {ledger_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
