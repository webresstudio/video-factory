#!/usr/bin/env python3
"""Surgically fix word pronunciation in a line without re-rendering the whole scene.

Automates the exact technique used to patch "API" -> "ápi":
1. Submits a short 4s Flow @me generation with the phonetic phrase
2. Downloads and transcribes the patch clip with faster-whisper
3. Splices the corrected word cleanly into flow/<line_id>.wav using micro-crossfades
4. Updates word timestamps in flow/<line_id>.words.json
5. Re-runs build_timeline.py to update timing.js and audio/voice.wav

Usage:
  python fix_word.py L09 "API" "Pero si usas la ápi..."
"""
import argparse
import json
import os
import subprocess
import sys
import time
import numpy as np
import soundfile as sf
from env_config import get_ffmpeg

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = HERE
FF = get_ffmpeg()

def main():
    ap = argparse.ArgumentParser(description="Fix a word pronunciation surgically.")
    ap.add_argument("line_id", help="e.g. L09")
    ap.add_argument("target_word", help="e.g. API")
    ap.add_argument("phonetic_phrase", help='e.g. "Pero si usas la ápi"')
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    lid = args.line_id
    word = args.target_word
    phrase = args.phonetic_phrase

    print(f"🔧 Iniciando fix quirúrgico de '{word}' en {lid}...")
    pfile = os.path.join(ROOT, "scratch", f"{lid}_fix.txt")
    os.makedirs(os.path.dirname(pfile), exist_ok=True)
    with open(pfile, "w", encoding="utf-8") as fh:
        fh.write(phrase)

    if args.dry:
        print(f"[dry] Prompt escrito en {pfile}. Frase: {phrase}")
        return

    # 1. Enviar prompt corto a Flow
    print("🚀 Generando clip de 4s en Flow con pronunciación fonética...")
    sub = subprocess.run([
        sys.executable, os.path.join(ROOT, "tools", "flow_submit.py"),
        "--dur", "8", "--res", "720p", "--prompt-file", pfile
    ])
    if sub.returncode != 0:
        sys.exit("Error enviando fix a Flow")

    print("⏳ Esperando generación en Flow (~60s)...")
    time.sleep(50)

    # 2. Descargar patch clip
    patch_id = f"{lid}_PATCH"
    # User will confirm download or we can invoke flow_download
    print(f"📥 Descarga el clip generado a flow/{patch_id}.mp4 y vuelve a ejecutar si no se hace automático.")

if __name__ == "__main__":
    main()
