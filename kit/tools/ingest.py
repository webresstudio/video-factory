#!/usr/bin/env python3
"""Ingest research notes and media assets into the project.

Scans inputs/research/ and inputs/media/, validates technical specs,
and outputs facts.md and media_catalog.json for the script and engine.
Usage: python ingest.py [--dir inputs]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from env_config import get_ffprobe

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def probe_file(path):
    ffprobe = get_ffprobe()
    cmd = [
        ffprobe, "-v", "error",
        "-show_entries", "stream=width,height,codec_type,duration,r_frame_rate:format=duration,size",
        "-of", "json", path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    try:
        return json.loads(res.stdout)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "inputs"))
    args = ap.parse_args()

    inp_dir = os.path.abspath(args.dir)
    res_dir = os.path.join(inp_dir, "research")
    med_dir = os.path.join(inp_dir, "media")
    brief_file = os.path.join(inp_dir, "brief.md")

    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(med_dir, exist_ok=True)

    print(f"📦 [ingest] Escaneando inputs en: {inp_dir}")

    # 1. Analizar investigación
    research_files = []
    facts_found = []
    for ext in ("*.md", "*.txt", "*.json"):
        for f in glob.glob(os.path.join(res_dir, ext)):
            rel = os.path.relpath(f, HERE)
            research_files.append(rel)
            content = open(f, encoding="utf-8", errors="ignore").read()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(("-", "•", "*")) and len(line) > 5:
                    facts_found.append(line.lstrip("-•* ").strip())

    if os.path.isfile(brief_file):
        research_files.append(os.path.relpath(brief_file, HERE))
        brief_content = open(brief_file, encoding="utf-8").read()
        print("📄 Brief detectado.")

    facts_path = os.path.join(HERE, "facts.md")
    with open(facts_path, "w", encoding="utf-8") as fh:
        fh.write("# Hechos Verificados para Guion (Fact Check)\n\n")
        fh.write("> [!IMPORTANT]\n")
        fh.write("> Solo los hechos listados aquí pueden usarse en el guion. Cero cifras o porcentajes inventados.\n\n")
        fh.write(f"Archivos analizados: {len(research_files)}\n\n")
        if facts_found:
            fh.write("## Hechos Extraídos:\n")
            for f in sorted(set(facts_found)):
                fh.write(f"- {f}\n")
        else:
            fh.write("*(No se detectaron viñetas directas; redactar hechos confirmados manualmente aquí)*\n")

    print(f"✅ facts.md generado con {len(facts_found)} hechos preliminares.")

    # 2. Analizar medios
    media_catalog = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.svg", "*.mp4", "*.mov", "*.wav", "*.mp3"):
        for f in glob.glob(os.path.join(med_dir, ext)):
            base = os.path.basename(f)
            rel = os.path.relpath(f, HERE)
            probe = probe_file(f)
            meta = {
                "name": base,
                "path": rel,
                "type": "unknown",
                "width": None,
                "height": None,
                "duration": None,
                "aspect_ratio": None,
                "fit_note": "Ajuste automático"
            }
            if probe:
                streams = probe.get("streams", [])
                v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
                a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
                if v_stream:
                    w = v_stream.get("width")
                    h = v_stream.get("height")
                    meta["width"] = w
                    meta["height"] = h
                    meta["type"] = "video" if ext.endswith((".mp4", ".mov")) else "image"
                    if w and h:
                        meta["aspect_ratio"] = f"{w}:{h}"
                        if w < 1080 or h < 1920:
                            meta["fit_note"] = "Resolución menor a 1080x1920: se sugiere escalado enmarcado o fondo difuminado"
                        if w > h:
                            meta["fit_note"] = "Asset horizontal: usar en ventana suiza o marco centrado 9:16"
                elif a_stream:
                    meta["type"] = "audio"
                dur = probe.get("format", {}).get("duration")
                if dur:
                    meta["duration"] = round(float(dur), 2)
            media_catalog.append(meta)

    catalog_path = os.path.join(HERE, "media_catalog.json")
    with open(catalog_path, "w", encoding="utf-8") as fh:
        json.dump(media_catalog, fh, indent=2, ensure_ascii=False)

    print(f"✅ media_catalog.json generado con {len(media_catalog)} activos clasificados.")

if __name__ == "__main__":
    main()
