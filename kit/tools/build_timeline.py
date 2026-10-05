#!/usr/bin/env python3
"""Assemble the narration from the Flow @me clips (his own voice) and emit timing.js.

For each line: trim the clip to its speech span (whisper words), place lines back to back
with authored gaps, and write:
  audio/voice.wav   48 kHz mono narration
  timing.js         window.TIMING = {duration, lines:[{id,t0,t1,clipIn,cam}], words:[{l,w,t,e}]}
"""
import json, os, glob, subprocess
import numpy as np
import soundfile as sf

from env_config import get_project_root
ROOT = get_project_root()
LINES = json.load(open(os.path.join(ROOT, "script.json"), encoding="utf-8"))
SR = 48000
LEAD = 0.30          # silence before the first word (cold open breathes for 0.3 s)
PRE, POST = 0.06, 0.18
# gap AFTER each line (seconds) — longer where a transition needs room to land
GAP = {"L01": 0.45, "L02": 0.40, "L03": 0.35, "L04": 0.40, "L05": 0.45,
       "L06": 0.45, "L07": 0.40, "L08": 0.45, "L09": 0.45, "L10": 0.0}
TAIL = 1.6

out, words, meta = [], [], []
cursor = LEAD
out.append(np.zeros(int(LEAD * SR), dtype=np.float32))


def compress_pauses(seg, W, s, keep=0.20, min_gap=0.30):
    """Shorten silent runs between words. Returns (new_seg, time_map) where time_map(t_rel)->t_rel'."""
    hop = int(0.01 * SR)
    rms = np.sqrt(np.convolve(seg ** 2, np.ones(hop) / hop, mode="same"))
    thr = max(rms.max() * 10 ** (-38 / 20), 1e-4)
    cuts = []  # (start_sample, end_sample) to remove
    for a, b in zip(W[:-1], W[1:]):
        g0, g1 = a["e"] - s, b["t"] - s
        if g1 - g0 < min_gap:
            continue
        i0, i1 = int(g0 * SR), int(g1 * SR)
        quiet = rms[i0:i1] < thr
        # longest quiet run inside the gap
        best, run, bs = (0, 0), 0, 0
        for k, q in enumerate(quiet):
            if q:
                if run == 0: bs = k
                run += 1
                if run > best[1] - best[0]: best = (bs, bs + run)
            else:
                run = 0
        qlen = (best[1] - best[0]) / SR
        if qlen > keep + 0.05:
            mid0 = i0 + best[0] + int(keep / 2 * SR)
            mid1 = i0 + best[1] - int(keep / 2 * SR)
            cuts.append((mid0, mid1))
    if not cuts:
        return seg, (lambda x: x)
    parts, last = [], 0
    xf = int(0.008 * SR)
    for c0, c1 in cuts:
        parts.append(seg[last:c0]); last = c1
    parts.append(seg[last:])
    new = parts[0]
    for q in parts[1:]:
        if len(new) > xf and len(q) > xf:
            fade = np.linspace(0, 1, xf)
            new = np.concatenate([new[:-xf], new[-xf:] * (1 - fade) + q[:xf] * fade, q[xf:]])
        else:
            new = np.concatenate([new, q])

    def tmap(x):
        xs = x * SR
        removed = 0
        for c0, c1 in cuts:
            if xs >= c1: removed += (c1 - c0) + xf
            elif xs > c0: removed += xs - c0
        return (xs - removed) / SR
    return new, tmap


for L in LINES:
    lid = L["id"]
    a, sr = sf.read(os.path.join(ROOT, "flow", f"{lid}.wav"), dtype="float32")
    assert sr == SR, sr
    if a.ndim > 1:
        a = a.mean(axis=1)
    W = json.load(open(os.path.join(ROOT, "flow", f"{lid}.words.json"), encoding="utf-8"))
    s = max(0.0, W[0]["t"] - PRE)
    e = min(len(a) / SR, W[-1]["e"] + POST)
    seg = a[int(s * SR):int(e * SR)].copy()
    tmap = lambda x: x
    if not L["cam"]:
        seg, tmap = compress_pauses(seg, W, s)
    f = int(0.012 * SR)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-f:] *= np.linspace(1, 0, f)
    out.append(seg)
    t0 = cursor
    meta.append({"id": lid, "t0": round(t0, 3), "t1": round(t0 + len(seg) / SR, 3), "clipIn": round(s, 3), "cam": L["cam"]})
    for w in W:
        words.append({"l": lid, "w": w["w"], "t": round(t0 + tmap(w["t"] - s), 3), "e": round(t0 + tmap(w["e"] - s), 3)})
    cursor = t0 + len(seg) / SR
    g = GAP.get(lid, 0.4) if L is not LINES[-1] else 0.0
    out.append(np.zeros(int(g * SR), dtype=np.float32))
    cursor += g
out.append(np.zeros(int(TAIL * SR), dtype=np.float32))
cursor += TAIL
voice = np.concatenate(out)
os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
dur = round(len(voice) / SR, 3)
T = {"duration": dur, "lines": meta, "words": words}
frames, cam_sources = {}, {}
from env_config import get_ffmpeg
for line in LINES:
    if not line.get("cam"):
        continue
    lid = line["id"]
    source = os.path.join(ROOT, "flow", f"{lid}_1080.mp4")
    if not os.path.isfile(source):
        source = os.path.join(ROOT, "flow", f"{lid}.mp4")
    if not os.path.isfile(source):
        raise RuntimeError(f"Falta el video de cámara para {lid}: {source}")
    dest = os.path.join(ROOT, "frames", lid)
    os.makedirs(dest, exist_ok=True)
    for previous in glob.glob(os.path.join(dest, "[0-9][0-9][0-9][0-9].jpg")):
        os.unlink(previous)
    subprocess.run([get_ffmpeg(), "-y", "-loglevel", "error", "-i", source,
                    "-vf", "fps=24", "-q:v", "2", os.path.join(dest, "%04d.jpg")], check=True)
    frames[lid] = len(glob.glob(os.path.join(dest, "[0-9][0-9][0-9][0-9].jpg")))
    cam_sources[lid] = os.path.relpath(source, ROOT)

sf.write(os.path.join(ROOT, "audio", "voice.wav"), voice, SR, subtype="PCM_24")
open(os.path.join(ROOT, "timing.js"), "w", encoding="utf-8").write(
    "window.TIMING = " + json.dumps(T, ensure_ascii=False, indent=0) + ";\nwindow.CAM_FRAMES = " + json.dumps(frames) + ";\nwindow.CAM_SOURCES = " + json.dumps(cam_sources) + ";\n")
for m in meta:
    print(m)
print("duration", dur)
