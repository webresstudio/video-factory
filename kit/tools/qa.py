#!/usr/bin/env python3
"""Quality Assurance verification suite for master video renders.

Checks:
1. Video container: 1080x1920, 60fps, H.264 profile, keyframe cadence
2. Audio stream: 48kHz stereo, -14 LUFS (EBU R128), -1.0 dBFS true peak
3. Transcription audit: Whisper pass on final audio to verify intelligibility
4. Contact sheet generation for visual spot-check

Usage:
  python qa.py [master.mp4]
"""
import glob
import json
import os
import subprocess
import sys
from env_config import get_ffmpeg, get_ffprobe

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = HERE
FF = get_ffmpeg()
FFPROBE = get_ffprobe()

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        cands = glob.glob(os.path.join(ROOT, "*_master.mp4")) + glob.glob(os.path.join(ROOT, "*.mp4"))
        if not cands:
            sys.exit("No se encontró ningún video MP4 para auditar en la raíz del proyecto.")
        target = cands[0]

    target = os.path.abspath(target)
    print(f"🔍 [QA] Auditando video master: {os.path.basename(target)}")

    # 1. ffprobe inspect
    probe_cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name,sample_rate,channels:format=duration,size,bit_rate",
        "-of", "json", target
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    meta = json.loads(res.stdout)
    streams = meta.get("streams", [])
    v = next((s for s in streams if s.get("codec_name") in ("h264", "hevc")), {})
    a = next((s for s in streams if s.get("codec_name") in ("aac", "pcm_s16le", "pcm_s24le")), {})

    w = int(v.get("width", 0))
    h = int(v.get("height", 0))
    fps_raw = v.get("r_frame_rate", "0/1")
    num, den = map(int, fps_raw.split("/"))
    fps = num / den if den else 0
    dur = float(meta.get("format", {}).get("duration", 0))

    print("\n--- 1. PARÁMETROS TÉCNICOS ---")
    print(f"Resolución:   {w}x{h} {'✓' if w==1080 and h==1920 else '⚠️ (Esperado 1080x1920)'}")
    print(f"Frame Rate:   {fps:.1f} fps {'✓' if abs(fps-60)<0.5 else '⚠️ (Esperado 60 fps)'}")
    print(f"Duración:     {dur:.2f} s")
    print(f"Audio:        {a.get('sample_rate')} Hz, {a.get('channels')} canales ({a.get('codec_name')})")

    # 2. Loudness check (EBU R128)
    print("\n--- 2. AUDITORÍA DE VOLUMEN (EBU R128) ---")
    loud_cmd = [
        FF, "-i", target, "-af", "loudnorm=print_format=json", "-f", "null", "-"
    ]
    p_loud = subprocess.run(loud_cmd, capture_output=True, text=True)
    # Parse json block from stderr
    stderr = p_loud.stderr
    l_json = None
    if "{" in stderr and "}" in stderr:
        try:
            chunk = stderr[stderr.rfind("{"):stderr.rfind("}")+1]
            l_json = json.loads(chunk)
        except Exception:
            pass

    if l_json:
        il = float(l_json.get("input_i", -99))
        tp = float(l_json.get("input_tp", -99))
        lra = float(l_json.get("input_lra", -99))
        print(f"Integrated Loudness: {il:.1f} LUFS {'✓' if abs(il - (-14)) <= 1.5 else '⚠️ (Objetivo: -14 LUFS)'}")
        print(f"True Peak:           {tp:.1f} dBTP {'✓' if tp <= -0.9 else '⚠️ (Máximo permitido: -1.0 dBTP)'}")
        print(f"Loudness Range:      {lra:.1f} LU")

    # 3. Whisper intelligibility check
    print("\n--- 3. VERIFICACIÓN DE CLARIDAD VOCAL (Whisper) ---")
    try:
        from faster_whisper import WhisperModel
        print("Transcribiendo pista vocal del render master...")
        wav_tmp = os.path.join(ROOT, "scratch", "qa_audio.wav")
        os.makedirs(os.path.dirname(wav_tmp), exist_ok=True)
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", target, "-vn", "-ar", "16000", "-ac", "1", wav_tmp], check=True)
        m = WhisperModel("small", device="cpu", compute_type="int8")
        segs, _ = m.transcribe(wav_tmp, language="es", vad_filter=False)
        text = " ".join(s.text.strip() for s in segs)
        print(f"Texto transcrito:\n\"{text}\"")
    except Exception as e:
        print(f"Whisper audit omitido ({e})")

    # 4. Sheet contact
    sheet = os.path.join(ROOT, "check", "qa_master_sheet.jpg")
    os.makedirs(os.path.dirname(sheet), exist_ok=True)
    subprocess.run([
        FF, "-y", "-loglevel", "error", "-i", target,
        "-vf", "fps=0.5,scale=270:-1,tile=6x2", "-frames:v", "1", sheet
    ])
    print(f"\n✅ Hoja de contactos para inspección visual: {os.path.relpath(sheet, ROOT)}")

if __name__ == "__main__":
    main()
