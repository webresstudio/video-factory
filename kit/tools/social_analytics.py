#!/usr/bin/env python3
"""Multi-platform & multi-business-model social video analytics auditor for WBRS / WVF.

Connects automatically to Google Chrome via AppleScript (chromejs.py) with zero
manual remote-debugging setup, extracts video performance metrics from:
  1. TikTok Studio (account overview + per-video retention & audience demographics)
  2. Meta Business Suite Content Insights (Watch time, Video average play time, 3s views, Stories)
  3. Instagram Web Reels Insights (Reach/Viewers, Non-followers %, Saves, Shares, AI label)

Evaluates performance against industry-specific benchmarks configured per client/project.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from urllib.parse import urlencode

import chromejs
import env_config


BUSINESS_MODEL_PROFILES = {
    "b2b_high_ticket": {
        "label": "B2B / Servicios Profesionales y Alto Ticket",
        "examples": "AVALO CORP, INGENIEROS_PANAMA, software a medida, inmobiliaria, clínicas, consultoría",
        "recommended_duration_seconds": (30, 45),
        "target_average_watch_seconds": 14.0,
        "target_full_watch_percent": 12.0,
        "max_youth_18_24_percent": 35.0,
        "primary_kpis": [
            "Edad calificada 25-54 años (>70%)",
            "Envíos por DM a socios o tomadores de decisión",
            "Guardados y clics a WhatsApp / enlace en bio o Stories",
            "Tiempo promedio >= 14s sin pauta juvenil contaminada",
        ],
    },
    "saas_product": {
        "label": "SaaS / Producto Digital Autogestionado",
        "examples": "SCALAos, apps móviles/web, herramientas de IA y productividad",
        "recommended_duration_seconds": (25, 40),
        "target_average_watch_seconds": 15.0,
        "target_full_watch_percent": 15.0,
        "max_youth_18_24_percent": 38.0,
        "primary_kpis": [
            "Tiempo promedio >= 15s mostrando dolor (0-4s) y demo 2.5x antes del 5s",
            "Guardados de tarjeta resumen coleccionable",
            "Tráfico por Búsqueda SEO (>5%)",
            "Clics a prueba o demo en perfil / Stories",
        ],
    },
    "ecommerce_b2c": {
        "label": "E-commerce / Retail / Producto Físico o Local B2C",
        "examples": "Tiendas en línea, restaurantes, gadgets, moda, consumo directo",
        "recommended_duration_seconds": (12, 25),
        "target_average_watch_seconds": 9.0,
        "target_full_watch_percent": 28.0,
        "max_youth_18_24_percent": 65.0,
        "primary_kpis": [
            "Porcentaje que vio el video completo (>= 28%)",
            "Producto en uso físico desde los primeros 0.5s",
            "Clics directos a catálogo, tienda o WhatsApp",
            "Comentarios de intención de compra (precio, envío, ubicación)",
        ],
    },
    "editorial_news": {
        "label": "Noticias / Autoridad Editorial y Marca Personal",
        "examples": "Las Noticias Tech, medios especializados, opinión y actualidad",
        "recommended_duration_seconds": (25, 38),
        "target_average_watch_seconds": 14.0,
        "target_full_watch_percent": 18.0,
        "max_youth_18_24_percent": 50.0,
        "primary_kpis": [
            "Alcance en No seguidores (>= 70%)",
            "1 sola noticia por video corto sin cortinilla inicial",
            "Porcentaje que vio el video completo (>= 18%)",
            "Compartidos, debate en comentarios y seguidores nuevos",
        ],
    },
    "education_creator": {
        "label": "Educación / Tutoriales Paso a Paso e Infoproductos",
        "examples": "Listas de comandos, guías técnicas, cursos, academia",
        "recommended_duration_seconds": (35, 55),
        "target_average_watch_seconds": 16.0,
        "target_full_watch_percent": 15.0,
        "max_youth_18_24_percent": 50.0,
        "primary_kpis": [
            "Tasa de Guardados sobre alcance (Saves / Reach >= 3%)",
            "Asomar hoja resumen en los primeros 4s e iniciar punto #1 antes del 5s",
            "Tráfico por Búsqueda SEO (>5%)",
            "Envíos por DM a colegas o compañeros de equipo",
        ],
    },
}


def parse_compact_number(raw_value: str) -> int:
    if not raw_value:
        return 0
    cleaned = raw_value.strip().replace(",", "")
    multiplier = 1
    if cleaned.upper().endswith("K"):
        multiplier = 1_000
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith("M"):
        multiplier = 1_000_000
        cleaned = cleaned[:-1]
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return 0
    return int(round(float(match.group(0)) * multiplier))


def parse_seconds_value(raw_value: str) -> float:
    if not raw_value:
        return 0.0
    cleaned = raw_value.strip().lower()
    minutes_seconds_match = re.search(r"(?:(\d+)h:?)?(?:(\d+)m\s*)?(\d+(?:\.\d+)?)s", cleaned)
    if minutes_seconds_match and ("m" in cleaned or "h" in cleaned):
        hours = int(minutes_seconds_match.group(1) or 0)
        minutes = int(minutes_seconds_match.group(2) or 0)
        seconds = float(minutes_seconds_match.group(3) or 0.0)
        return round(hours * 3600 + minutes * 60 + seconds, 2)
    simple_seconds_match = re.search(r"(\d+(?:\.\d+)?)\s*s", cleaned)
    if simple_seconds_match:
        return round(float(simple_seconds_match.group(1)), 2)
    return 0.0


def parse_percentage_value(raw_value: str) -> float:
    if not raw_value:
        return 0.0
    cleaned = raw_value.strip()
    if cleaned.startswith("<"):
        return 0.05
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", cleaned)
    return round(float(match.group(1)), 2) if match else 0.0


def load_social_configuration(project_root: str, cli_overrides: dict | None = None) -> dict:
    cli_overrides = cli_overrides or {}
    configuration = {
        "client_name": "Webres Studio",
        "business_model": "saas_product",
        "instagram_handle": "",
        "tiktok_handle": "",
        "meta_asset_id": "",
        "meta_business_id": "",
    }
    config_file_path = os.path.join(project_root, "project_config.json")
    if os.path.isfile(config_file_path):
        try:
            with open(config_file_path, encoding="utf-8") as config_handle:
                project_data = json.load(config_handle)
            configuration["client_name"] = project_data.get("client_name", configuration["client_name"])
            social_section = project_data.get("social", {})
            for field_name in (
                "business_model",
                "instagram_handle",
                "tiktok_handle",
                "meta_asset_id",
                "meta_business_id",
            ):
                if social_section.get(field_name):
                    configuration[field_name] = str(social_section[field_name]).strip()
        except (OSError, ValueError):
            pass

    for field_name, override_value in cli_overrides.items():
        if override_value:
            configuration[field_name] = str(override_value).strip()

    configuration["instagram_handle"] = configuration["instagram_handle"].lstrip("@")
    configuration["tiktok_handle"] = configuration["tiktok_handle"].lstrip("@")
    if configuration["business_model"] not in BUSINESS_MODEL_PROFILES:
        raise ValueError(
            f"Modelo de negocio desconocido: {configuration['business_model']}. "
            f"Opciones válidas: {', '.join(sorted(BUSINESS_MODEL_PROFILES))}."
        )
    return configuration


def build_meta_insights_url(social_configuration: dict) -> str:
    base_url = "https://business.facebook.com/latest/insights/content"
    query_parameters = {}
    if social_configuration.get("meta_asset_id"):
        query_parameters["asset_id"] = social_configuration["meta_asset_id"]
    if social_configuration.get("meta_business_id"):
        query_parameters["business_id"] = social_configuration["meta_business_id"]
    if not query_parameters:
        return base_url
    return f"{base_url}?{urlencode(query_parameters)}"


def parse_hour_float(raw_value: str) -> float | None:
    """Parse local publish/activity hour (0.0..23.99) from Meta, TikTok, or ISO-8601 strings."""
    if not raw_value:
        return None
    text = raw_value.strip()
    # ISO-8601 datetime e.g. 2026-11-10T18:35:00.000Z
    iso_match = re.match(r"^\d{4}-\d{2}-\d{2}T(\d{2}):(\d{2})", text)
    if iso_match:
        try:
            normalized_iso = text.replace("Z", "+00:00")
            parsed_dt = dt.datetime.fromisoformat(normalized_iso)
            if parsed_dt.tzinfo is not None:
                local_tz = dt.datetime.now().astimezone().tzinfo
                parsed_dt = parsed_dt.astimezone(local_tz)
            return round(parsed_dt.hour + parsed_dt.minute / 60.0, 2)
        except ValueError:
            pass

    # 12-hour format e.g. "7:00am", "12:35pm", "1pm y las 2pm", "8 p. m."
    ampm_match = re.search(
        r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(a\.?\s*m\.?|p\.?\s*m\.?)\b",
        text,
        flags=re.IGNORECASE,
    )
    if ampm_match:
        hour = int(ampm_match.group(1))
        minute = int(ampm_match.group(2) or 0)
        meridiem = re.sub(r"[\s.]", "", ampm_match.group(3)).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        return round(hour + minute / 60.0, 2)

    # 24-hour format e.g. "14:30" or "08:15" (avoiding mm:ss video durations like 0:02)
    h24_match = re.search(r"(?:,\s*|\s+)([01]?\d|2[0-3]):([0-5]\d)\b", " " + text)
    if h24_match and "minuto" not in text.lower():
        return round(int(h24_match.group(1)) + int(h24_match.group(2)) / 60.0, 2)
    return None


def format_hour_12h(hour_float: float) -> str:
    total_minutes = int(round((hour_float % 24.0) * 60.0)) % (24 * 60)
    hour24, minute = divmod(total_minutes, 60)
    meridiem = "a. m." if hour24 < 12 else "p. m."
    hour12 = hour24 % 12 or 12
    return f"{hour12}:{minute:02d} {meridiem}"


def format_deploy_window_from_peak(peak_hour: float, lead_minutes: int = 30, span_minutes: int = 30) -> str:
    start_h = (peak_hour - lead_minutes / 60.0) % 24.0
    end_h = (start_h + span_minutes / 60.0) % 24.0
    return f"{format_hour_12h(start_h)} – {format_hour_12h(end_h)}"


def parse_tiktok_video_analytics(
    video_id: str,
    summary_text: str,
    audience_text: str = "",
    caption_hint: str = "",
    retention_curve_pct: list[float] | None = None,
) -> dict:
    lines = [line.strip() for line in (summary_text or "").splitlines() if line.strip()]
    published_date = ""
    caption_text = caption_hint.strip()
    top_counters = {"views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0}

    for index, line in enumerate(lines):
        if line.startswith("Publicado el"):
            published_date = line.replace("Publicado el", "").strip()
            if index >= 1 and not caption_text:
                caption_text = lines[index - 1]
            numeric_slice = lines[index + 1 : index + 6]
            if len(numeric_slice) == 5 and all(re.match(r"^[\d.,KMkm]+$", item) for item in numeric_slice):
                top_counters = {
                    "views": parse_compact_number(numeric_slice[0]),
                    "likes": parse_compact_number(numeric_slice[1]),
                    "comments": parse_compact_number(numeric_slice[2]),
                    "shares": parse_compact_number(numeric_slice[3]),
                    "saves": parse_compact_number(numeric_slice[4]),
                }
            break

    def value_after_label(label_text: str) -> str:
        for idx, current_line in enumerate(lines[:-1]):
            if current_line == label_text:
                return lines[idx + 1]
        return ""

    views_value = parse_compact_number(value_after_label("Vistas del video")) or top_counters["views"]
    average_watch_seconds = parse_seconds_value(value_after_label("Tiempo promedio de vista"))
    watched_full_percent = parse_percentage_value(value_after_label("Vieron el video completo"))
    new_followers = parse_compact_number(value_after_label("Nuevos seguidores"))

    dropoff_match = re.search(
        r"dejaron de mirar el video en el minuto\s+(\d+:\d+)",
        summary_text or "",
        flags=re.IGNORECASE,
    )
    primary_dropoff_timestamp = dropoff_match.group(1) if dropoff_match else ""

    traffic_sources = {}
    known_sources = (
        "Para ti",
        "Buscar",
        "Perfil personal",
        "Siguiendo",
        "Mensajes directos",
        "Sonido",
        "Otras",
    )
    for source_name in known_sources:
        raw_pct = value_after_label(source_name)
        if "%" in raw_pct:
            traffic_sources[source_name] = parse_percentage_value(raw_pct)

    age_brackets = {}
    countries = {}
    if audience_text:
        audience_lines = [line.strip() for line in audience_text.splitlines() if line.strip()]
        for idx, current_line in enumerate(audience_lines[:-1]):
            if current_line in ("18-24", "25-34", "35-44", "45-54", "55+"):
                age_brackets[current_line] = parse_percentage_value(audience_lines[idx + 1])
        if "Ubicaciones" in audience_lines:
            loc_start = audience_lines.index("Ubicaciones") + 1
            cursor = loc_start
            while cursor + 1 < len(audience_lines) and "%" in audience_lines[cursor + 1]:
                countries[audience_lines[cursor]] = parse_percentage_value(audience_lines[cursor + 1])
                cursor += 2

    parsed_video = {
        "video_id": video_id,
        "published_date": published_date,
        "published_hour": parse_hour_float(published_date),
        "caption": caption_text[:180],
        "views": views_value,
        "likes": top_counters["likes"],
        "comments": top_counters["comments"],
        "shares": top_counters["shares"],
        "saves": top_counters["saves"],
        "average_watch_seconds": average_watch_seconds,
        "watched_full_percent": watched_full_percent,
        "new_followers": new_followers,
        "primary_dropoff_timestamp": primary_dropoff_timestamp,
        "traffic_sources": traffic_sources,
        "age_brackets": age_brackets,
        "countries": countries,
    }
    if retention_curve_pct:
        parsed_video["retention_curve_pct"] = [round(float(x), 1) for x in retention_curve_pct]
    return parsed_video


def parse_tiktok_account_overview(overview_text: str, viewers_text: str = "") -> dict:
    overview_lines = [line.strip() for line in (overview_text or "").splitlines() if line.strip()]
    search_percent = 0.0
    for index, line in enumerate(overview_lines[:-1]):
        if line == "Buscar" and "%" in overview_lines[index + 1]:
            search_percent = parse_percentage_value(overview_lines[index + 1])
            break

    peak_match = re.search(
        r"estuvieron más activos el [^\n]+ entre las ([^\n.]+)",
        viewers_text or "",
        flags=re.IGNORECASE,
    )
    peak_window_str = peak_match.group(1).strip() if peak_match else ""
    return {
        "account_search_traffic_percent": search_percent,
        "peak_activity_window": peak_window_str,
        "peak_activity_start_hour": parse_hour_float(peak_window_str),
    }


def parse_meta_business_suite_rows(grid_rows: list[list[str]], instagram_handle: str = "") -> list[dict]:
    parsed_items = []
    seen_signatures = set()
    ig_norm = (instagram_handle or "").strip().lstrip("@").lower()
    for row_cells in grid_rows:
        if not row_cells or len(row_cells) < 15:
            continue
        first_cell = row_cells[0].strip()
        if first_cell.lower().startswith("title"):
            continue
        signature = (first_cell[:80], row_cells[1].strip(), row_cells[2].strip())
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        is_story = " Story " in f" {first_cell} "
        post_type = "story" if is_story else ("reel" if " Reel " in f" {first_cell} " else "post")
        is_crossposted = "Crossposted" in first_cell

        tail_match = re.search(r"\s(?:Reel|Story)\s+(.*)$", first_cell)
        account_tail = re.sub(r"\bBoost\b.*$", "", tail_match.group(1), flags=re.IGNORECASE).strip() if tail_match else ""
        if is_crossposted:
            platform_channel = "crossposted"
        elif ig_norm and ig_norm in account_tail.lower():
            platform_channel = "instagram"
        elif account_tail and re.fullmatch(r"@?[a-z0-9._]{3,32}", account_tail):
            platform_channel = "instagram"
        else:
            platform_channel = "facebook"

        clean_title = re.sub(r"\s*(Reel|Story)\s+(Crossposted\s+)?.*$", "", first_cell).strip()
        date_str = row_cells[1].strip()

        parsed_items.append(
            {
                "title": clean_title[:180],
                "post_type": post_type,
                "platform_channel": platform_channel,
                "is_crossposted": is_crossposted,
                "date_published": date_str,
                "published_hour": parse_hour_float(date_str),
                "views": parse_compact_number(row_cells[2]),
                "reach": parse_compact_number(row_cells[3]),
                "viewers": parse_compact_number(row_cells[4]),
                "interactions": parse_compact_number(row_cells[5]),
                "likes": parse_compact_number(row_cells[6]),
                "comments": parse_compact_number(row_cells[7]),
                "shares": parse_compact_number(row_cells[8]),
                "saves": parse_compact_number(row_cells[9]),
                "link_clicks": parse_compact_number(row_cells[10]),
                "follows": parse_compact_number(row_cells[12]),
                "watch_time_raw": row_cells[13].strip(),
                "average_play_seconds": parse_seconds_value(row_cells[14]),
                "three_second_views": parse_compact_number(row_cells[15]) if len(row_cells) > 15 else 0,
            }
        )
    return parsed_items


def parse_instagram_reel_insights(reel_url: str, insights_text: str, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    lines = [line.strip() for line in (insights_text or "").splitlines() if line.strip()]

    def metric_after(label_text: str) -> str:
        for index, current_line in enumerate(lines[:-1]):
            if current_line == label_text:
                if lines[index + 1] == label_text and index + 2 < len(lines):
                    return lines[index + 2]
                return lines[index + 1]
        return ""

    return {
        "reel_url": reel_url,
        "title": str(metadata.get("title", "")).strip()[:180],
        "published_at": str(metadata.get("time", "")).strip(),
        "has_ai_content_label": bool(metadata.get("aiLabel", False)),
        "views": parse_compact_number(metric_after("Visualizaciones")),
        "unique_viewers": parse_compact_number(metric_after("Espectadores")),
        "non_followers_percent": parse_percentage_value(metric_after("No seguidores")),
        "likes": parse_compact_number(metric_after("Me gusta")),
        "comments": parse_compact_number(metric_after("Comentarios")),
        "saves": parse_compact_number(metric_after("Veces que se guardó")),
        "shares": parse_compact_number(metric_after("Veces que se compartió")),
        "new_followers": parse_compact_number(metric_after("Actividad del perfil")),
    }


def evaluate_social_performance(
    business_model: str,
    tiktok_videos: list[dict],
    meta_items: list[dict],
    instagram_reels: list[dict],
    tiktok_overview: dict | None = None,
) -> dict:
    if business_model not in BUSINESS_MODEL_PROFILES:
        raise ValueError(f"Modelo de negocio inválido: {business_model}")

    profile = BUSINESS_MODEL_PROFILES[business_model]
    tiktok_overview = tiktok_overview or {}
    findings = []

    # 1. Early 0:01-0:02 hook drop-off check
    early_dropoff_videos = [
        video
        for video in tiktok_videos
        if video.get("primary_dropoff_timestamp") in ("0:01", "0:02")
    ]
    if early_dropoff_videos:
        findings.append(
            {
                "code": "EARLY_HOOK_DROPOFF",
                "severity": "critical",
                "summary": (
                    f"{len(early_dropoff_videos)}/{len(tiktok_videos)} videos en TikTok Studio pierden "
                    f"a la mayoría de espectadores en 0:01–0:02. Eliminar cortinillas iniciales (0.0s) y "
                    f"mostrar evidencia/acción real antes del segundo 4.5."
                ),
            }
        )

    # 2. Average watch time & completion rate vs business model target
    if tiktok_videos:
        mean_watch = round(
            sum(v.get("average_watch_seconds", 0.0) for v in tiktok_videos) / len(tiktok_videos),
            2,
        )
        mean_completion = round(
            sum(v.get("watched_full_percent", 0.0) for v in tiktok_videos) / len(tiktok_videos),
            2,
        )
        if mean_watch < profile["target_average_watch_seconds"] or mean_completion < profile["target_full_watch_percent"]:
            min_dur, max_dur = profile["recommended_duration_seconds"]
            findings.append(
                {
                    "code": "WATCH_TIME_BELOW_MODEL_TARGET",
                    "severity": "high",
                    "summary": (
                        f"Retención media TikTok ({mean_watch}s, {mean_completion}% completos) por debajo "
                        f"de la meta para '{profile['label']}' (>={profile['target_average_watch_seconds']}s, "
                        f">={profile['target_full_watch_percent']}%). Ajustar duración a {min_dur}-{max_dur}s."
                    ),
                }
            )

    # 3. Youth 18-24 audience contamination for B2B / SaaS
    for video in tiktok_videos:
        youth_share = video.get("age_brackets", {}).get("18-24", 0.0)
        if youth_share > profile["max_youth_18_24_percent"]:
            findings.append(
                {
                    "code": "AUDIENCE_AGE_MISMATCH",
                    "severity": "high",
                    "summary": (
                        f"El video {video.get('video_id')} concentró {youth_share}% de audiencia 18-24 años "
                        f"(máximo recomendado {profile['max_youth_18_24_percent']}% para {profile['label']}). "
                        f"Filtrar edad e intereses empresariales al pautar para no contaminar la cuenta."
                    ),
                }
            )

    # 4. Meta Business Suite Reels watch time & Crossposting drag
    meta_reels = [item for item in meta_items if item.get("post_type") == "reel"]
    crossposted_low = [
        item for item in meta_reels if item.get("is_crossposted") and 0 < item.get("average_play_seconds", 0) <= 4.0
    ]
    if crossposted_low:
        findings.append(
            {
                "code": "META_CROSSPOST_DRAG",
                "severity": "medium",
                "summary": (
                    f"{len(crossposted_low)} Reels publicados como Crossposted (IG+FB) en Meta Business Suite "
                    f"promedian <=4s de reproducción. Publicar Reels nativos en Instagram mejora la retención limpia."
                ),
            }
        )

    # 5. Saves & DM Shares check on Instagram
    if instagram_reels:
        total_saves = sum(reel.get("saves", 0) for reel in instagram_reels)
        total_shares = sum(reel.get("shares", 0) for reel in instagram_reels)
        if total_saves == 0 and total_shares == 0 and business_model != "ecommerce_b2c":
            findings.append(
                {
                    "code": "ZERO_SAVES_AND_DM_SHARES",
                    "severity": "high",
                    "summary": (
                        "0 Guardados y 0 Compartidos por DM en los Reels auditados de Instagram. "
                        "No revelar toda la lista en el copy y asomar la tarjeta resumen en los primeros 4s."
                    ),
                }
            )
        ai_labeled_count = sum(1 for reel in instagram_reels if reel.get("has_ai_content_label"))
        if ai_labeled_count > 0:
            findings.append(
                {
                    "code": "INSTAGRAM_AI_LABEL_VISIBLE",
                    "severity": "medium",
                    "summary": (
                        f"{ai_labeled_count}/{len(instagram_reels)} Reels muestran el sello 'Contenido de IA' en el encabezado. "
                        f"Abrir los primeros 2 segundos con prueba visual real/interfaz viva para evitar deslizamiento por prejuicio anti-avatar."
                    ),
                }
            )

    # 6. Search SEO check in TikTok
    account_search_pct = tiktok_overview.get("account_search_traffic_percent", 0.0)
    if tiktok_videos and account_search_pct < 1.0:
        findings.append(
            {
                "code": "LOW_SEARCH_SEO_TRAFFIC",
                "severity": "medium",
                "summary": (
                    f"Tráfico por Búsqueda en TikTok es {account_search_pct}% (<1%). "
                    f"Alinear primera oración hablada, titular en pantalla (0-3s) y Línea 1 del copy con consultas naturales."
                ),
            }
        )

    return {
        "business_model": business_model,
        "profile_label": profile["label"],
        "recommended_duration_seconds": list(profile["recommended_duration_seconds"]),
        "primary_kpis": profile["primary_kpis"],
        "findings": findings,
    }


def _best_publish_hour_from_posts(posts: list[dict], score_fn) -> tuple[float | None, int]:
    """Group historical posts into 2-hour buckets and return (weighted_best_hour, sample_count)."""
    buckets: dict[int, list[tuple[float, float]]] = {}
    valid_count = 0
    for item in posts:
        h = item.get("published_hour")
        if h is None:
            continue
        weight = max(float(score_fn(item)), 0.01)
        bucket_key = int(h) // 2
        buckets.setdefault(bucket_key, []).append((float(h), weight))
        valid_count += 1
    if not buckets:
        return None, 0
    best_bucket = max(
        buckets.items(),
        key=lambda kv: sum(w for _, w in kv[1]) / (len(kv[1]) ** 0.35),
    )[1]
    total_w = sum(w for _, w in best_bucket)
    weighted_hour = sum(h * w for h, w in best_bucket) / max(total_w, 1e-9)
    return round(weighted_hour % 24.0, 2), valid_count


def discover_brand_publish_windows(
    social_configuration: dict,
    tiktok_videos: list[dict] | None = None,
    meta_items: list[dict] | None = None,
    instagram_reels: list[dict] | None = None,
    tiktok_overview: dict | None = None,
    audience_activity: dict | None = None,
) -> dict:
    """Calculate SEPARATE optimal publish windows for Facebook, Instagram, and TikTok per brand.

    Never hardcodes a universal hour across brands or across networks: combines each network's
    audience active-hour peak (when available) with that brand's empirical post velocity per hour.
    """
    tiktok_videos = tiktok_videos or []
    meta_items = meta_items or []
    instagram_reels = instagram_reels or []
    tiktok_overview = tiktok_overview or {}
    audience_activity = audience_activity or {}
    brand_name = social_configuration.get("client_name", "Marca")

    def resolve_network_window(
        network_label: str,
        audience_peak_hour: float | None,
        hist_best_hour: float | None,
        hist_samples: int,
        low_conf_fallback: bool = False,
    ) -> dict:
        if audience_peak_hour is not None and hist_best_hour is not None:
            # Circular blend on 24h clock: 55% audience active peak, 45% best empirical post hour (+0.5h peak offset)
            import math
            a1 = audience_peak_hour * 2.0 * math.pi / 24.0
            a2 = ((hist_best_hour + 0.5) % 24.0) * 2.0 * math.pi / 24.0
            sin_m = 0.55 * math.sin(a1) + 0.45 * math.sin(a2)
            cos_m = 0.55 * math.cos(a1) + 0.45 * math.cos(a2)
            blended_peak = round((math.atan2(sin_m, cos_m) * 24.0 / (2.0 * math.pi)) % 24.0, 2)
            return {
                "recommended_deploy_window": format_deploy_window_from_peak(blended_peak, lead_minutes=30, span_minutes=30),
                "empirical_peak_hour": blended_peak,
                "source": "hybrid_audience_and_history",
                "sample_size": hist_samples,
                "rationale": (
                    f"{brand_name} en {network_label}: cruza pico activo de espectadores ({format_hour_12h(audience_peak_hour)}) "
                    f"con mejor velocidad histórica ({hist_samples} publicaciones, mejor salida ~{format_hour_12h(hist_best_hour)})."
                ),
            }
        if audience_peak_hour is not None:
            return {
                "recommended_deploy_window": format_deploy_window_from_peak(audience_peak_hour, lead_minutes=30, span_minutes=30),
                "empirical_peak_hour": round(audience_peak_hour, 2),
                "source": "audience_activity_peak",
                "sample_size": hist_samples,
                "rationale": (
                    f"{brand_name} en {network_label}: publicar 30 min antes del pico activo de su audiencia "
                    f"({format_hour_12h(audience_peak_hour)})."
                ),
            }
        if hist_best_hour is not None:
            src = "crosspost_fallback_low_confidence" if low_conf_fallback else "historical_post_velocity"
            start_str = format_hour_12h((hist_best_hour - 0.25) % 24.0)
            end_str = format_hour_12h((hist_best_hour + 0.25) % 24.0)
            extra_note = (
                " (calculado sobre crossposts; publica nativo en Facebook para aislar su curva propia)"
                if low_conf_fallback
                else ""
            )
            return {
                "recommended_deploy_window": f"{start_str} – {end_str}",
                "empirical_peak_hour": round((hist_best_hour + 0.5) % 24.0, 2),
                "source": src,
                "sample_size": hist_samples,
                "rationale": (
                    f"{brand_name} en {network_label}: franja con mayor retención×alcance empírico en {hist_samples} "
                    f"publicaciones de esta cuenta (~{format_hour_12h(hist_best_hour)}){extra_note}."
                ),
            }
        return {
            "recommended_deploy_window": "Pendiente de auditar historial propio de esta marca",
            "empirical_peak_hour": None,
            "source": "insufficient_data",
            "sample_size": 0,
            "rationale": (
                f"Sin horas activas ni publicaciones con hora en {network_label} para {brand_name}. "
                f"Ejecuta `wvf analytics --platform all` con la sesión de esta marca antes de programar."
            ),
        }

    # 1. TikTok window (specific to this brand's TikTok Studio)
    tt_aud_peak = audience_activity.get("tiktok_peak_hour")
    if tt_aud_peak is None:
        tt_aud_peak = tiktok_overview.get("peak_activity_start_hour")
        if tt_aud_peak is None and tiktok_overview.get("peak_activity_window"):
            tt_aud_peak = parse_hour_float(tiktok_overview["peak_activity_window"])
    tt_hist_hour, tt_n = _best_publish_hour_from_posts(
        tiktok_videos,
        lambda v: max(v.get("views", 1), 1)
        * max(v.get("average_watch_seconds", 2.0), 1.0)
        * (1.0 + 0.30 * v.get("saves", 0) + 0.35 * v.get("shares", 0)),
    )
    tt_win = resolve_network_window("TikTok", tt_aud_peak, tt_hist_hour, tt_n)

    # 2. Instagram window (strictly native IG reels/posts from Meta + IG Insights, excluding crossposts)
    ig_aud_peak = audience_activity.get("instagram_peak_hour")
    if isinstance(ig_aud_peak, str):
        ig_aud_peak = parse_hour_float(ig_aud_peak)
    ig_candidates = [
        m for m in meta_items if m.get("post_type") in ("reel", "post") and m.get("platform_channel") == "instagram"
    ]
    for reel in instagram_reels:
        h_ig = parse_hour_float(reel.get("published_at", ""))
        if h_ig is not None:
            ig_candidates.append(
                {
                    "published_hour": h_ig,
                    "views": reel.get("views", 0),
                    "reach": reel.get("unique_viewers", 0),
                    "average_play_seconds": 8.0,
                    "saves": reel.get("saves", 0),
                    "shares": reel.get("shares", 0),
                }
            )
    ig_hist_hour, ig_n = _best_publish_hour_from_posts(
        ig_candidates,
        lambda m: max(m.get("reach") or m.get("views", 1), 1)
        * max(m.get("average_play_seconds", 4.0), 2.0)
        * (1.0 + 0.35 * m.get("saves", 0) + 0.40 * m.get("shares", 0)),
    )
    ig_win = resolve_network_window("Instagram", ig_aud_peak, ig_hist_hour, ig_n)

    # 3. Facebook window (native Facebook Page reels/videos in Meta Business Suite)
    fb_aud_peak = audience_activity.get("facebook_peak_hour")
    if isinstance(fb_aud_peak, str):
        fb_aud_peak = parse_hour_float(fb_aud_peak)
    fb_native = [
        m for m in meta_items if m.get("post_type") in ("reel", "post") and m.get("platform_channel") == "facebook"
    ]
    fb_used_fallback = False
    if not fb_native:
        fb_native = [
            m for m in meta_items if m.get("post_type") in ("reel", "post") and m.get("is_crossposted")
        ]
        fb_used_fallback = bool(fb_native)
    fb_hist_hour, fb_n = _best_publish_hour_from_posts(
        fb_native,
        lambda m: max(m.get("views", 1), 1)
        * max(m.get("average_play_seconds", 2.0), 1.0)
        * (1.0 + 0.25 * m.get("interactions", 0) / max(m.get("views", 1), 1)),
    )
    fb_win = resolve_network_window("Facebook", fb_aud_peak, fb_hist_hour, fb_n, low_conf_fallback=fb_used_fallback)

    return {
        "brand": brand_name,
        "tiktok": tt_win,
        "instagram": ig_win,
        "facebook": fb_win,
    }


EXTRACT_TIKTOK_RETENTION_FIBER_JS = """
(() => {
  try {
    const nodes = Array.from(document.querySelectorAll('svg, div, canvas'));
    for (const el of nodes) {
      const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber$') || k.startsWith('__reactProps$'));
      if (!fiberKey) continue;
      let cur = el[fiberKey];
      for (let depth = 0; cur && depth < 14; depth++, cur = cur.return) {
        const p = cur.memoizedProps || cur.pendingProps || {};
        const candidates = [p.data, p.retentionData, p.series?.[0]?.data, p.option?.series?.[0]?.data];
        for (const arr of candidates) {
          if (Array.isArray(arr) && arr.length >= 8) {
            const nums = arr.map(it => typeof it === 'number' ? it : (it?.y ?? it?.value ?? it?.rate ?? null))
                            .filter(v => typeof v === 'number' && !Number.isNaN(v));
            if (nums.length >= 8 && nums[0] >= 80 && nums[0] <= 105) {
              return JSON.stringify(nums);
            }
          }
        }
      }
    }
  } catch (e) {}
  return '[]';
})()
"""


def collect_tiktok_studio_live(social_configuration: dict, limit: int) -> dict:
    chromejs.navigate_tab("https://www.tiktok.com/tiktokstudio/content", url_match="tiktok.com")
    time.sleep(5.0)
    content_js = """
    (() => {
      window.scrollTo(0, 2000);
      const links = Array.from(document.querySelectorAll('a[href*="/video/"]')).map(anchor => ({
        text: (anchor.innerText || '').trim(),
        href: anchor.href
      }));
      return JSON.stringify({ currentUrl: location.href, links });
    })()
    """
    content_payload = json.loads(chromejs.execute_javascript(content_js, url_match="tiktok.com"))
    discovered_links = content_payload.get("links", [])

    detected_handle = ""
    video_queue = []
    seen_ids = set()
    for entry in discovered_links:
        match = re.search(r"/@([^/]+)/video/(\d+)", entry.get("href", ""))
        if not match:
            continue
        handle_name, video_id = match.group(1), match.group(2)
        if not detected_handle:
            detected_handle = handle_name
        if video_id not in seen_ids:
            seen_ids.add(video_id)
            video_queue.append((video_id, entry.get("text", "")))
        if len(video_queue) >= limit:
            break

    expected_handle = social_configuration.get("tiktok_handle", "")
    account_mismatch_warning = ""
    if expected_handle and detected_handle and expected_handle.lower() != detected_handle.lower():
        account_mismatch_warning = (
            f"Atención: project_config.json espera @{expected_handle}, pero TikTok Studio en Chrome "
            f"está conectado como @{detected_handle}."
        )

    videos_analytics = []
    for video_id, caption_preview in video_queue:
        chromejs.navigate_tab(
            f"https://www.tiktok.com/tiktokstudio/analytics/{video_id}",
            url_match="tiktok.com",
        )
        time.sleep(3.8)
        summary_text = chromejs.execute_javascript(
            "(() => { window.scrollTo(0, 1200); return document.body.innerText; })()",
            url_match="tiktok.com",
        )
        raw_curve = chromejs.execute_javascript(EXTRACT_TIKTOK_RETENTION_FIBER_JS, url_match="tiktok.com")
        try:
            retention_curve = json.loads(raw_curve) if raw_curve else []
        except ValueError:
            retention_curve = []
        chromejs.execute_javascript(
            """(() => {
              const tab = Array.from(document.querySelectorAll('div, span, button, a'))
                .find(el => (el.innerText || '').trim() === 'Espectadores');
              if (tab) tab.click();
              return 'OK';
            })()""",
            url_match="tiktok.com",
        )
        time.sleep(2.0)
        audience_text = chromejs.execute_javascript("(() => document.body.innerText)()", url_match="tiktok.com")
        videos_analytics.append(
            parse_tiktok_video_analytics(
                video_id=video_id,
                summary_text=summary_text,
                audience_text=audience_text,
                caption_hint=caption_preview,
                retention_curve_pct=retention_curve,
            )
        )

    chromejs.navigate_tab("https://www.tiktok.com/tiktokstudio/analytics", url_match="tiktok.com")
    time.sleep(3.5)
    overview_text = chromejs.execute_javascript("(() => document.body.innerText)()", url_match="tiktok.com")
    chromejs.execute_javascript(
        """(() => {
          const tab = Array.from(document.querySelectorAll('div, span, button, a'))
            .find(el => (el.innerText || '').trim() === 'Espectadores');
          if (tab) tab.click();
          return 'OK';
        })()""",
        url_match="tiktok.com",
    )
    time.sleep(2.0)
    viewers_text = chromejs.execute_javascript("(() => document.body.innerText)()", url_match="tiktok.com")
    overview_metrics = parse_tiktok_account_overview(overview_text, viewers_text)

    return {
        "detected_handle": detected_handle,
        "account_mismatch_warning": account_mismatch_warning,
        "overview": overview_metrics,
        "videos": videos_analytics,
    }


def collect_meta_studio_live(social_configuration: dict) -> dict:
    target_url = build_meta_insights_url(social_configuration)
    chromejs.navigate_tab(target_url, url_match="business.facebook.com")
    time.sleep(6.0)
    resolved_url = chromejs.execute_javascript("location.href", url_match="business.facebook.com")

    all_rows = []
    for scroll_offset in (0, 900, 1800):
        grid_js = f"""
        (() => {{
          const containers = Array.from(document.querySelectorAll('div'))
            .filter(d => d.scrollHeight > d.clientHeight + 50 && d.clientHeight > 250);
          containers.forEach(d => {{ d.scrollTop = {scroll_offset}; }});
          return JSON.stringify(
            Array.from(document.querySelectorAll('[role="row"]')).map(row =>
              Array.from(row.querySelectorAll('[role="gridcell"], [role="columnheader"]'))
                .map(cell => cell.innerText.replace(/\\s+/g, ' ').trim())
            ).filter(r => r.length >= 15)
          );
        }})()
        """
        chromejs.execute_javascript(grid_js, url_match="business.facebook.com")
        time.sleep(1.0)
        batch = json.loads(chromejs.execute_javascript(grid_js, url_match="business.facebook.com"))
        all_rows.extend(batch)

    return {
        "resolved_url": resolved_url,
        "items": parse_meta_business_suite_rows(
            all_rows,
            instagram_handle=social_configuration.get("instagram_handle", ""),
        ),
    }


def collect_instagram_reels_live(social_configuration: dict, limit: int) -> dict:
    handle = social_configuration.get("instagram_handle", "")
    profile_url = f"https://www.instagram.com/{handle}/" if handle else "https://www.instagram.com/"
    chromejs.navigate_tab(profile_url, url_match="instagram.com")
    time.sleep(4.5)

    if not handle:
        discovered_profile = chromejs.execute_javascript(
            """(() => {
              const reelLink = document.querySelector('a[href*="/reels/"]');
              if (!reelLink) return '';
              const parts = new URL(reelLink.href).pathname.split('/').filter(Boolean);
              return parts[0] && parts[0] !== 'reels' ? parts[0] : '';
            })()""",
            url_match="instagram.com",
        )
        if discovered_profile:
            handle = discovered_profile
            chromejs.navigate_tab(f"https://www.instagram.com/{handle}/", url_match="instagram.com")
            time.sleep(4.0)

    reel_urls = json.loads(
        chromejs.execute_javascript(
            """(() => Array.from(new Set(
              Array.from(document.querySelectorAll('a[href*="/reel/"]')).map(a => a.href)
            )))()""",
            url_match="instagram.com",
        )
    )[:limit]

    reels_metrics = []
    for reel_url in reel_urls:
        chromejs.navigate_tab(reel_url, url_match="instagram.com")
        time.sleep(3.5)
        metadata = json.loads(
            chromejs.execute_javascript(
                """(() => ({
                  title: document.querySelector('meta[property="og:title"]')?.content || document.title,
                  time: document.querySelector('time')?.getAttribute('datetime') || '',
                  aiLabel: document.body.innerText.includes('Contenido de IA')
                }))()""",
                url_match="instagram.com",
            )
        )
        chromejs.execute_javascript(
            """(() => {
              const button = Array.from(document.querySelectorAll('div[role="button"], button, span, a'))
                .find(el => ['Ver estadísticas', 'View insights'].includes((el.innerText || '').trim()));
              if (button) button.click();
              return button ? 'CLICKED' : 'NO_BTN';
            })()""",
            url_match="instagram.com",
        )
        time.sleep(2.2)
        insights_text = chromejs.execute_javascript(
            "(() => (document.querySelector('main')?.innerText || document.body.innerText).slice(0, 2600))()",
            url_match="instagram.com",
        )
        reels_metrics.append(parse_instagram_reel_insights(reel_url, insights_text, metadata))

    return {
        "instagram_handle": handle,
        "reels": reels_metrics,
    }


def print_console_report(report: dict) -> None:
    config = report["configuration"]
    evaluation = report["evaluation"]
    print(f"\n📊 [wvf analytics] Cliente: {config['client_name']} · Modelo: {evaluation['profile_label']}")
    min_sec, max_sec = evaluation["recommended_duration_seconds"]
    print(f"   Duración recomendada: {min_sec}s–{max_sec}s")

    windows = report.get("optimal_publish_windows", {})
    if windows:
        print(f"\n🕒 Ventanas Óptimas de Despliegue para {config['client_name']} (Independientes por Red):")
        for net_key, net_label in (("tiktok", "TikTok"), ("instagram", "Instagram"), ("facebook", "Facebook")):
            w_info = windows.get(net_key, {})
            if w_info:
                print(f"   • {net_label:<10}: {w_info.get('recommended_deploy_window')}  [{w_info.get('source')}]")

    tiktok_section = report.get("tiktok_studio", {})
    if tiktok_section.get("account_mismatch_warning"):
        print(f"   ⚠️ {tiktok_section['account_mismatch_warning']}")

    tiktok_videos = tiktok_section.get("videos", [])
    if tiktok_videos:
        print(f"\n🎵 TikTok Studio (@{tiktok_section.get('detected_handle', '?')}) — {len(tiktok_videos)} videos:")
        for video in tiktok_videos:
            print(
                f"   • {video['published_date'] or video['video_id']}: {video['views']} vistas | "
                f"prom. {video['average_watch_seconds']}s | completo {video['watched_full_percent']}% | "
                f"abandono {video['primary_dropoff_timestamp'] or '-'} | {video['caption'][:55]}"
            )

    meta_items = [
        item
        for item in report.get("meta_business_suite", {}).get("items", [])
        if item.get("post_type") == "reel"
    ]
    if meta_items:
        print(f"\n📈 Meta Business Suite Reels — {len(meta_items)} Reels:")
        for item in meta_items:
            ch = item.get("platform_channel", "instagram")
            mode_tag = "Crosspost" if item["is_crossposted"] else ("FB Nativo" if ch == "facebook" else "IG Nativo")
            print(
                f"   • {item['date_published']} ({mode_tag}): {item['views']} vistas | "
                f"prom. {item['average_play_seconds']}s | guardados {item['saves']} | {item['title'][:50]}"
            )

    instagram_reels = report.get("instagram", {}).get("reels", [])
    if instagram_reels:
        print(f"\n📸 Instagram (@{report['instagram'].get('instagram_handle', '?')}) — {len(instagram_reels)} Reels:")
        for reel in instagram_reels:
            ai_flag = " [Contenido de IA]" if reel["has_ai_content_label"] else ""
            print(
                f"   • {reel['views']} vistas ({reel['non_followers_percent']}% no seg.) | "
                f"guardados {reel['saves']} | DM {reel['shares']}{ai_flag}"
            )

    print("\n🩺 Diagnóstico por Modelo de Negocio:")
    if not evaluation["findings"]:
        print("   ✓ Todas las métricas clave cumplen los umbrales de este modelo de negocio.")
    else:
        for finding in evaluation["findings"]:
            print(f"   [{finding['severity'].upper()}] {finding['summary']}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auditor automático de TikTok Studio, Meta Business Suite e Instagram por modelo de negocio."
    )
    parser.add_argument(
        "--platform",
        choices=["all", "tiktok", "meta", "instagram"],
        default="all",
        help="Plataformas a consultar en Google Chrome (default: all)",
    )
    parser.add_argument("--limit", type=int, default=5, help="Cantidad de videos recientes a inspeccionar (default: 5)")
    parser.add_argument(
        "--model",
        choices=sorted(BUSINESS_MODEL_PROFILES.keys()),
        default="",
        help="Modelo de negocio para calibrar el diagnóstico",
    )
    parser.add_argument("--ig", default="", help="Handle de Instagram del cliente (ej: webresstudio)")
    parser.add_argument("--tiktok", default="", help="Handle de TikTok del cliente (ej: williamromerovela)")
    parser.add_argument("--meta-asset", default="", help="asset_id de la cuenta en Meta Business Suite")
    parser.add_argument("--meta-business", default="", help="business_id del portafolio en Meta Business Suite")
    parser.add_argument(
        "--save-windows",
        action="store_true",
        help="Persistir las ventanas óptimas descubiertas (FB/IG/TikTok) en project_config.json",
    )
    parser.add_argument("--out", default="", help="Ruta de salida para el reporte JSON (default: check/social_analytics.json)")
    return parser


def main(argv=None) -> int:
    parser = build_argument_parser()
    parsed_args = parser.parse_args(argv)
    project_root = env_config.get_project_root()

    configuration = load_social_configuration(
        project_root,
        cli_overrides={
            "business_model": parsed_args.model,
            "instagram_handle": parsed_args.ig,
            "tiktok_handle": parsed_args.tiktok,
            "meta_asset_id": parsed_args.meta_asset,
            "meta_business_id": parsed_args.meta_business,
        },
    )

    tiktok_data = {}
    meta_data = {}
    instagram_data = {}

    if parsed_args.platform in ("all", "tiktok"):
        tiktok_data = collect_tiktok_studio_live(configuration, limit=parsed_args.limit)
    if parsed_args.platform in ("all", "meta"):
        meta_data = collect_meta_studio_live(configuration)
    if parsed_args.platform in ("all", "instagram"):
        instagram_data = collect_instagram_reels_live(configuration, limit=parsed_args.limit)

    evaluation = evaluate_social_performance(
        business_model=configuration["business_model"],
        tiktok_videos=tiktok_data.get("videos", []),
        meta_items=meta_data.get("items", []),
        instagram_reels=instagram_data.get("reels", []),
        tiktok_overview=tiktok_data.get("overview", {}),
    )
    optimal_windows = discover_brand_publish_windows(
        social_configuration=configuration,
        tiktok_videos=tiktok_data.get("videos", []),
        meta_items=meta_data.get("items", []),
        instagram_reels=instagram_data.get("reels", []),
        tiktok_overview=tiktok_data.get("overview", {}),
    )

    if parsed_args.save_windows:
        cfg_path = os.path.join(project_root, "project_config.json")
        if os.path.isfile(cfg_path):
            try:
                cfg_obj = json.load(open(cfg_path, encoding="utf-8"))
                cfg_obj.setdefault("social", {})["optimal_publish_windows"] = {
                    net: optimal_windows[net]["recommended_deploy_window"]
                    for net in ("tiktok", "instagram", "facebook")
                }
                with open(cfg_path, "w", encoding="utf-8") as cfh:
                    json.dump(cfg_obj, cfh, ensure_ascii=False, indent=2)
            except (OSError, ValueError):
                pass

    output_path = parsed_args.out or os.path.join(project_root, "check", "social_analytics.json")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    full_report = {
        "configuration": configuration,
        "optimal_publish_windows": optimal_windows,
        "tiktok_studio": tiktok_data,
        "meta_business_suite": meta_data,
        "instagram": instagram_data,
        "evaluation": evaluation,
    }
    with open(output_path, "w", encoding="utf-8") as report_handle:
        json.dump(full_report, report_handle, ensure_ascii=False, indent=2)

    print_console_report(full_report)
    print(f"\n💾 Reporte guardado en: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
