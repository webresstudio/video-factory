#!/usr/bin/env python3
"""FlowMusic Resource Connector for WVF.

Connects to the client's FlowMusic project (via Chrome bridge or project URL),
inspects tracks, and imports exported music tracks directly into the project's
audio bus with automatic resampling (48kHz stereo) and duration alignment.

Usage:
  python flowmusic.py --status
  python flowmusic.py --nav
  python flowmusic.py --import <path/to/downloaded_track.mp3>
"""
import argparse
import json
import os
import subprocess
import sys
from env_config import get_ffmpeg

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.getcwd()
FF = get_ffmpeg()

CONFIG_FILE = os.path.join(ROOT, "project_config.json")
DEFAULT_URL = "https://www.flowmusic.app/"

def load_config():
    if os.path.isfile(CONFIG_FILE):
        try:
            return json.load(open(CONFIG_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {
        "flowmusic": {
            "project_url": DEFAULT_URL,
            "preferred_track": "Tech Commercial",
            "ducking_db": -9.5
        }
    }

def get_js_helper():
    p = os.path.join(os.path.dirname(__file__), "flowmusicjs.py")
    if not os.path.isfile(p):
        p = os.path.join(ROOT, "tools", "flowmusicjs.py")
    return p

def cmd_status():
    cfg = load_config()
    target_url = cfg.get("flowmusic", {}).get("project_url", DEFAULT_URL)
    print(f"🎵 [FlowMusic] Proyecto configurado: {target_url}")

    js_tool = get_js_helper()
    inspect_script = """(function(){
        const title = document.title;
        const url = location.href;
        const tracks = Array.from(document.querySelectorAll("*"))
            .filter(e => e.children.length === 0 && e.textContent && e.textContent.length > 2 && e.textContent.length < 50)
            .map(e => e.textContent.trim())
            .filter(t => !/^(Search|Close|New session|Songs|Playlists|Spaces|Music videos|Projects|Profile|Turntable|Invite|Back|Edit|More|Sessions)$/i.test(t));
        return JSON.stringify({
            title: title,
            url: url,
            tracks: [...new Set(tracks)].slice(0, 15)
        });
    })()"""
    res = subprocess.run([sys.executable, js_tool, "-e", inspect_script], capture_output=True, text=True)
    raw = res.stdout.strip()
    if raw == "NO_TAB" or not raw.startswith("{"):
        print("⚠️ No se detectó ninguna pestaña activa con FlowMusic en Chrome.")
        print(f"👉 Puedes abrirla con: wvf flowmusic --nav")
        return

    try:
        data = json.loads(raw)
        print(f"✓ Pestaña activa:    {data.get('title')}")
        print(f"✓ URL actual:        {data.get('url')}")
        tracks = data.get("tracks", [])
        if tracks:
            print("✓ Pistas detectadas en el proyecto:")
            for t in tracks:
                print(f"   • {t}")
        else:
            print("ℹ️ No se listaron pistas de audio en la vista actual.")
    except Exception as e:
        print(f"Error parseando estado: {e} | Raw: {raw[:120]}")

def cmd_nav(custom_url=None):
    cfg = load_config()
    target_url = custom_url or cfg.get("flowmusic", {}).get("project_url", DEFAULT_URL)
    print(f"🌐 [FlowMusic] Navegando Chrome hacia: {target_url}")
    js_tool = get_js_helper()
    res = subprocess.run([sys.executable, js_tool, "--nav", target_url], capture_output=True, text=True)
    print(f"✓ Resultado: {res.stdout.strip()}")

def cmd_import(file_path):
    if not os.path.isfile(file_path):
        sys.exit(f"❌ Error: Archivo de audio no encontrado: {file_path}")

    # Detect project duration if timing.js exists
    timing_file = os.path.join(ROOT, "timing.js")
    duration = None
    if os.path.isfile(timing_file):
        try:
            content = open(timing_file, encoding="utf-8").read()
            import re
            m = re.search(r'"duration"\s*:\s*([0-9.]+)', content)
            if m:
                duration = float(m.group(1))
        except Exception:
            pass

    out_dir = os.path.join(ROOT, "audio")
    os.makedirs(out_dir, exist_ok=True)
    dest_wav = os.path.join(out_dir, "music_flowmusic.wav")

    print(f"📥 [FlowMusic] Importando '{os.path.basename(file_path)}' como música de fondo...")
    
    # 48kHz stereo 24-bit PCM
    cmd = [
        FF, "-y", "-loglevel", "error", "-i", file_path,
        "-ar", "48000", "-ac", "2"
    ]
    if duration:
        print(f"✓ Ajustando duración exacta del video: {duration:.2f}s con fade-out al cierre")
        # Apply 1.5s fade out at the end
        fade_start = max(0.0, duration - 1.5)
        cmd += ["-af", f"afade=t=out:st={fade_start:.2f}:d=1.5", "-t", f"{duration:.2f}"]

    cmd.append(dest_wav)
    subprocess.run(cmd, check=True)
    print(f"✅ Pista importada con éxito: {dest_wav}")
    print("💡 Ahora wvf audio / build_audio.py usará esta pista con ducking inteligente de voz.")

def main():
    ap = argparse.ArgumentParser(description="FlowMusic Resource Manager")
    ap.add_argument("--status", action="store_true", help="Inspecciona el proyecto FlowMusic actual en Chrome")
    ap.add_argument("--nav", nargs="?", const="", help="Abre o navega Chrome al proyecto FlowMusic")
    ap.add_argument("--import", dest="import_file", help="Importa un archivo de audio descargado de FlowMusic")
    args = ap.parse_args()

    if args.status:
        cmd_status()
    elif args.nav is not None:
        cmd_nav(args.nav if args.nav else None)
    elif args.import_file:
        cmd_import(args.import_file)
    else:
        cmd_status()

if __name__ == "__main__":
    main()
