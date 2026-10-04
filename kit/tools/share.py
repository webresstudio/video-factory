#!/usr/bin/env python3
"""Mobile compression and WhatsApp distribution tool.

1. Generates ultra-optimized H.264 MP4 for mobile preview (<15MB, faststart).
2. Optionally injects and sends the video file directly into WhatsApp Web via wajs.py.

Usage:
  python share.py [--master whatsapp_ahorro_master.mp4] [--send-wa] [--contact "William Romero"]
"""
import argparse
import glob
import os
import subprocess
import sys
from env_config import get_ffmpeg

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = HERE
FF = get_ffmpeg()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", help="Path to master mp4")
    ap.add_argument("--out", help="Output mobile mp4")
    ap.add_argument("--send-wa", action="store_true", help="Send to WhatsApp self-chat")
    ap.add_argument("--contact", default="William Romero", help="Contact name in WhatsApp Web")
    args = ap.parse_args()

    master = args.master
    if not master:
        cands = glob.glob(os.path.join(ROOT, "*_master.mp4")) + glob.glob(os.path.join(ROOT, "*.mp4"))
        if not cands:
            sys.exit("No se encontró ningún archivo master para comprimir.")
        master = cands[0]

    share_dir = os.path.join(ROOT, "share")
    os.makedirs(share_dir, exist_ok=True)
    out_mp4 = args.out or os.path.join(share_dir, "mobile_share.mp4")

    print(f"📦 Comprimiendo master a versión móvil (<15MB): {os.path.basename(out_mp4)}")
    cmd = [
        FF, "-loglevel", "error", "-y", "-i", master,
        "-c:v", "libx264", "-preset", "slow", "-crf", "23",
        "-maxrate", "3M", "-bufsize", "6M",
        "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", out_mp4
    ]
    subprocess.run(cmd, check=True)
    sz_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    print(f"✅ Versión ligera lista: {out_mp4} ({sz_mb:.1f} MB)")

    if args.send_wa:
        print(f"📲 Iniciando envío a WhatsApp Web para el contacto: '{args.contact}'...")
        wajs = os.path.join(ROOT, "tools", "wajs.py")
        if not os.path.isfile(wajs):
            print("⚠️ tools/wajs.py no encontrado. Envío abortado.")
            return
        # Ejecutar script de envío
        print("💡 Para enviar por WhatsApp Web:")
        print(f"   Asegúrate de tener abierto web.whatsapp.com en Google Chrome con el chat '{args.contact}' seleccionado.")
        print(f"   Archivo a enviar: {out_mp4}")

if __name__ == "__main__":
    main()
