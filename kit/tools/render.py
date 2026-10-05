#!/usr/bin/env python3
"""Render determinista frame a frame (60 fps) del HTML → MP4 master.

Cada worker abre su propio Chrome, llama renderAt(i/60) y captura el frame exacto (sin frames perdidos),
codifica su segmento en H.264 de alta calidad, y al final se concatenan y se multiplexa el audio master.
Uso: python render.py [--workers 4] [--fps 60] [--test]
"""
import argparse
import base64
import math
import os
import subprocess
import sys
import time
from multiprocessing import Process

from env_config import get_project_root
HERE = get_project_root()
from env_config import get_preview_url
URL = get_preview_url()
from env_config import get_ffmpeg, get_chrome
FFMPEG = get_ffmpeg()
CHROME = get_chrome()
SEG = os.path.join(HERE, "render_segments")
os.makedirs(SEG, exist_ok=True)


def worker(idx, f0, f1, fps, off=0):
    from playwright.sync_api import sync_playwright
    out = os.path.join(SEG, f"seg_{idx:02d}.mp4")
    enc = subprocess.Popen([
        FFMPEG, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
        "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-x264-params", f"keyint={fps}:min-keyint={fps}:scenecut=0", out,
    ], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        launch_args = {
            "headless": True,
            "args": ["--use-angle=metal", "--enable-gpu-rasterization", "--ignore-gpu-blocklist",
                     "--force-color-profile=srgb", "--hide-scrollbars"]
        }
        if CHROME:
            launch_args["executable_path"] = CHROME
        b = p.chromium.launch(**launch_args)
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto(URL)
        pg.wait_for_function("window.READY === true || window.BOOT_ERROR", timeout=30000)
        error = pg.evaluate("window.BOOT_ERROR || null")
        if error:
            raise RuntimeError(error)
        cdp = pg.context.new_cdp_session(pg)
        t0 = time.time()
        for i in range(f0, f1):
            pg.evaluate(f"(async () => {{ const t = {(i + off) / fps:.6f}; await window.prepare(t); window.renderAt(t); }})()")
            shot = cdp.send("Page.captureScreenshot", {"format": "png", "optimizeForSpeed": True, "captureBeyondViewport": False})
            enc.stdin.write(base64.b64decode(shot["data"]))
            if (i - f0) % 120 == 0:
                done = i - f0 + 1
                print(f"[w{idx}] {done}/{f1 - f0} frames · {done / (time.time() - t0):.1f} fps", flush=True)
        b.close()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"FFmpeg falló en el worker {idx}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--start", type=float, default=0.0)
    a = ap.parse_args()

    if a.workers < 1 or a.fps < 1 or not math.isfinite(a.start) or a.start < 0:
        ap.error("workers y fps deben ser positivos; start no puede ser negativo")
    import json
    if a.duration is not None:
        dur = a.duration
    else:
        with open(os.path.join(HERE, "audio", "cues.json"), encoding="utf-8") as cues_file:
            dur = json.load(cues_file)["duration"]
    if not math.isfinite(dur) or dur <= 0:
        ap.error("La duración debe ser finita y positiva")
    total = math.ceil(dur * a.fps)
    if a.test:
        total = math.ceil(min(dur, 2.0) * a.fps)
    # segments aligned on 1 s boundaries so every segment starts with an IDR frame
    per = math.ceil(total / a.workers / a.fps) * a.fps
    ranges = [(i, i * per, min(total, (i + 1) * per)) for i in range(a.workers) if i * per < total]
    print(f"{total} frames · {len(ranges)} workers", flush=True)
    t0 = time.time()
    off = round(a.start * a.fps)
    procs = [Process(target=worker, args=(i, s, e, a.fps, off)) for i, s, e in ranges]
    for pr in procs: pr.start()
    for pr in procs: pr.join()
    if any(pr.exitcode for pr in procs):
        sys.exit("worker failed")
    print(f"frames listos en {time.time() - t0:.0f}s", flush=True)

    lst = os.path.join(SEG, "list.txt")
    with open(lst, "w") as fh:
        for i, _, _ in ranges:
            fh.write(f"file 'seg_{i:02d}.mp4'\n")
    name = "test_render.mp4" if a.test else "whatsapp_ahorro_master.mp4"
    out = os.path.join(HERE, name)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ss", str(off / a.fps), "-i", os.path.join(HERE, "audio", "master.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out, flush=True)


if __name__ == "__main__":
    main()
