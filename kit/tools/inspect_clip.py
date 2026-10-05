#!/usr/bin/env python3
"""Inspect a Flow clip: probe, contact frames, and Spanish transcription with word timestamps.
usage: inspect_clip.py L02
"""
import json, os, subprocess, sys, glob
from env_config import get_ffmpeg

from env_config import get_project_root
ROOT = get_project_root()
FF = get_ffmpeg()
lid = sys.argv[1]
src = sorted(glob.glob(os.path.join(ROOT, "flow", lid, "*.mp4")))[-1]
dst = os.path.join(ROOT, "flow", f"{lid}.mp4")
if src != dst:
    os.replace(src, dst)
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate,channels:format=duration", "-of", "json", dst], capture_output=True, text=True).stdout
print(probe)
wav = os.path.join(ROOT, "flow", f"{lid}.wav")
subprocess.run([FF, "-y", "-loglevel", "error", "-i", dst, "-vn", "-ac", "1", "-ar", "48000", wav], check=True)
sheet = os.path.join(ROOT, "check", f"{lid}_frames.jpg")
subprocess.run([FF, "-y", "-loglevel", "error", "-i", dst, "-vf", "fps=0.75,scale=270:-1,tile=6x1", "-frames:v", "1", sheet], check=True)
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(wav, language="es", word_timestamps=True, vad_filter=False)
words = []
for s in segs:
    for w in s.words:
        words.append({"w": w.word.strip(), "t": round(w.start, 3), "e": round(w.end, 3)})
json.dump(words, open(os.path.join(ROOT, "flow", f"{lid}.words.json"), "w"), ensure_ascii=False, indent=0)
print("TEXT:", " ".join(w["w"] for w in words))
if words:
    print("speech span:", words[0]["t"], "->", words[-1]["e"])
