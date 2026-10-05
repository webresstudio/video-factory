#!/usr/bin/env python3
"""Partitura original + diseño sonoro + mezcla final (48 kHz estéreo, -14 LUFS).

- Música: pads armónicos en Re menor que cambian con cada acto, pulso en Sonnet/selector, resolución final.
- SFX sintetizados, uno por cada movimiento en pantalla (hoja de cues exportada desde engine.js).
- Ducking por sidechain de la voz, limitador suave, loudnorm EBU R128.
"""
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

from env_config import get_project_root
HERE = get_project_root()
AUD = os.path.join(HERE, "audio")
SR = 48000
from env_config import get_ffmpeg
FFMPEG = get_ffmpeg()
rng = np.random.default_rng(11)

cfg = json.load(open(os.path.join(AUD, "cues.json")))
DUR = cfg["duration"]
_tm = open(os.path.join(HERE, "timing.js"), encoding="utf-8").read()
_tm = _tm.split("window.TIMING = ", 1)[1].split(";\nwindow.CAM_FRAMES", 1)[0].rstrip().rstrip(";")
LT = {l["id"]: l["t0"] for l in json.loads(_tm)["lines"]}
N = int(DUR * SR) + SR // 2


def t_axis(n):
    return np.arange(n) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def note(name):
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)


def saw(f, n, phase=0.0, maxf=2400.0):
    t = t_axis(n)
    out = np.zeros(n)
    k = 1
    while k * f < maxf and k <= 24:
        out += np.sin(2 * np.pi * k * f * t + phase * k) / k
        k += 1
    return out * 0.6


def reverb_ir(seconds=2.8, decay=3.2):
    n = int(seconds * SR)
    t = t_axis(n)
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1)
    ir *= np.exp(-t * decay)[:, None]
    ir = lp(ir, 6500)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0))


IR = reverb_ir()


def verb(x, wet=0.3):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    w = np.stack([fftconvolve(x[:, c], IR[:, c])[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + w * wet


# ───────────────────────── MÚSICA ─────────────────────────
# (inicio, fin, notas del pad, raíz del bajo)
# harmony follows the story: cost (minor, tense) -> free (brighter) -> five tips (pulse) -> resolution (D major)
def _sec(a, b, notes, root):
    return (LT[a] - 0.15 if a != "start" else 0.0, (LT[b] - 0.1) if b != "end" else DUR + 0.5, notes, root)
HARMONIES = [
    (["D3", "A3", "F4", "C5", "E5"], "D2"),
    (["Bb2", "F3", "D4", "A4", "C5"], "Bb1"),
    (["F3", "C4", "A4", "G5", "E5"], "F2"),
    (["G3", "D4", "Bb4", "F5", "A5"], "G2"),
    (["F3", "C4", "A4", "E5", "G5"], "F2"),
]
line_ids = list(LT)
SECTIONS = []
for i, line in enumerate(line_ids):
    notes, root = HARMONIES[i % len(HARMONIES)]
    start = max(0, LT[line] - 0.15)
    end = LT[line_ids[i+1]] - 0.1 if i+1 < len(line_ids) else DUR + 0.5
    if i+1 == len(line_ids):
        notes, root = ["D3", "A3", "F#4", "E5", "A5"], "D2"
    SECTIONS.append((start, end, notes, root))


def section_env(n, a, b, att=0.7, rel=0.9):
    t = t_axis(n)
    e = np.clip((t - a) / att, 0, 1) * np.clip((b - t) / rel + 1, 0, 1)
    return np.sin(e * np.pi / 2) ** 2


def build_music():
    flowmusic_track = os.path.join(AUD, "music_flowmusic.wav")
    imported_track = os.path.join(AUD, "music_imported.wav")
    config_path = os.path.join(HERE, "project_config.json")
    preferences = json.load(open(config_path, encoding="utf-8")).get("flowmusic", {}) if os.path.isfile(config_path) else {}
    active_track = flowmusic_track if os.path.isfile(flowmusic_track) else (imported_track if os.path.isfile(imported_track) else None)
    if not preferences.get("use_imported_track", True):
        active_track = None

    if active_track:
        print(f"🎵 Usando pista de FlowMusic / externa: {os.path.basename(active_track)}")
        m_data, m_sr = sf.read(active_track, dtype="float64")
        if m_data.ndim == 1:
            m_data = np.stack([m_data, m_data], axis=1)
        mus = np.zeros((N, 2))
        take = min(N, len(m_data))
        mus[:take] = m_data[:take]
        mus = mus / (np.abs(mus).max() + 1e-9) * 0.75
        return mus

    mus = np.zeros((N, 2))
    t = t_axis(N)
    for (a, b, notes, root) in SECTIONS:
        s0, s1 = int(max(0, a - 0.05) * SR), min(N, int((b + 1.0) * SR))
        n = s1 - s0
        env = section_env(N, a, b)[s0:s1]
        tl = t[s0:s1]
        for i, nm in enumerate(notes):
            f = note(nm)
            amp = 0.10 / (1 + i * 0.35)
            for ch, det in ((0, -5), (1, 6)):
                ff = f * 2 ** (det / 1200)
                tone = saw(ff, n, phase=rng.uniform(0, 6.28), maxf=1800 if i < 2 else 3200)
                lfo = 0.82 + 0.18 * np.sin(2 * np.pi * (0.07 + i * 0.013) * tl + i)
                mus[s0:s1, ch] += tone * amp * lfo * env
        # sub bass
        fr = note(root)
        mus[s0:s1] += (np.sin(2 * np.pi * fr * tl) * 0.16 * env)[:, None]
    mus = lp(mus, 2600)

    # pulso rítmico (Sonnet + selector): bombo suave a 112 bpm con pumping del pad
    beat = 60 / 112
    pulse = np.zeros(N)
    pump = np.ones(N)
    for start, end in [(LT[a]+0.1, LT[b]-0.4) for a,b in (("L04", "L06"), ("L07", "L09")) if a in LT and b in LT]:
        k = start
        while k < end:
            s = int(k * SR)
            n = int(0.35 * SR)
            tt = t_axis(n)
            f = 48 + 70 * np.exp(-tt * 28)
            kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.42
            pulse[s:s + n] += kick[: max(0, min(n, N - s))]
            pm = 1 - 0.35 * np.exp(-tt * 6)
            pump[s:s + n] = np.minimum(pump[s:s + n], pm[: max(0, min(n, N - s))])
            k += beat
    mus *= pump[:, None]
    mus += np.stack([pulse, pulse], 1)

    # arpegio pluck en Sonnet (semicorcheas)
    arp_notes = [note(x) for x in ["G5", "D6", "Bb5", "A5", "D6", "Bb5", "F6", "D6"]]
    k, i = LT.get("L07", DUR) + 0.1, 0
    while k < LT.get("L08", DUR) - 0.3:
        s = int(k * SR)
        n = int(0.22 * SR)
        tt = t_axis(n)
        f = arp_notes[i % len(arp_notes)]
        pl = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 22) * 0.05
        pan = 0.5 + 0.35 * np.sin(i * 1.3)
        e = min(n, N - s)
        mus[s:s + e, 0] += pl[:e] * (1 - pan)
        mus[s:s + e, 1] += pl[:e] * pan
        k += beat / 4
        i += 1

    mus = verb(mus, 0.35)
    # fade final
    fade = np.clip((DUR - t) / 1.4, 0, 1)
    return mus * fade[:, None]


# ───────────────────────── SFX ─────────────────────────
def env_ar(n, a, r):
    t = t_axis(n)
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) * r)
    return e


def sfx(kind):
    if kind == "hairline":
        n = int(0.9 * SR); tt = t_axis(n)
        f = 2200 + 2400 * tt / 0.9
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.25, 4) * 0.08
        return verb(x, 0.5)
    if kind in ("sub", "sub_soft"):
        n = int(1.2 * SR); tt = t_axis(n)
        f = 72 * np.exp(-tt * 2.2) + 36
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.006, 3.4)
        x += hp(rng.standard_normal(n), 2000) * env_ar(n, 0.001, 90) * 0.15
        return np.stack([x, x], 1) * (0.9 if kind == "sub" else 0.5)
    if kind == "swell":
        n = int(1.6 * SR); tt = t_axis(n)
        x = bp(rng.standard_normal(n), 300, 3000) * (tt / 1.6) ** 2.5 * np.exp(-np.maximum(tt - 1.45, 0) * 30) * 0.35
        return verb(x, 0.4)
    if kind in ("shimmer", "shimmer_soft"):
        n = int(1.6 * SR); tt = t_axis(n)
        x = np.zeros(n)
        for f in (2637, 3136, 3951, 5274):
            x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt * (3 + f / 2000))
        x += bp(rng.standard_normal(n), 6000, 12000) * env_ar(n, 0.15, 4) * 0.6
        x *= env_ar(n, 0.02, 1.0) * 0.05 * (1 if kind == "shimmer" else 0.6)
        return verb(x, 0.6)
    if kind == "chime":
        n = int(2.2 * SR); tt = t_axis(n)
        x = np.zeros(n)
        for f, a in ((880, 1), (1318.5, 0.6), (1760, 0.35), (2637, 0.2)):
            x += np.sin(2 * np.pi * f * tt) * a * np.exp(-tt * (2.2 + f / 1500))
        return verb(x * env_ar(n, 0.004, 0.6) * 0.07, 0.55)
    if kind == "hit":
        n = int(0.9 * SR); tt = t_axis(n)
        f = 110 * np.exp(-tt * 14) + 45
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7)
        click = hp(rng.standard_normal(n), 3500) * np.exp(-tt * 140) * 0.35
        return verb((body * 0.6 + click), 0.25)
    if kind in ("whoosh", "whoosh_s", "whoosh_fast", "whoosh_deep", "whoosh_rev", "ui_up", "swipe"):
        L = {"whoosh": 0.7, "whoosh_s": 0.45, "whoosh_fast": 0.28, "whoosh_deep": 0.9, "whoosh_rev": 0.55, "ui_up": 0.5, "swipe": 0.35}[kind]
        n = int(L * SR); tt = t_axis(n)
        noise = rng.standard_normal(n)
        lo, hi = {"whoosh": (250, 2600), "whoosh_s": (500, 4500), "whoosh_fast": (1200, 9000), "whoosh_deep": (90, 1400),
                  "whoosh_rev": (400, 3500), "ui_up": (600, 5000), "swipe": (900, 7000)}[kind]
        # band sweep in 6 slices
        out = np.zeros(n)
        segs = 8
        for i in range(segs):
            a, b = i * n // segs, (i + 1) * n // segs
            k = i / (segs - 1)
            c = lo * (hi / lo) ** (k if kind != "whoosh_rev" else 1 - k)
            seg = bp(noise, max(40, c * 0.6), min(SR / 2 - 100, c * 1.6))[a:b]
            out[a:b] = seg
        shape = np.sin(np.pi * np.clip(tt / L, 0, 1)) ** (1.6 if kind != "whoosh_rev" else 0.8)
        if kind == "whoosh_rev":
            shape = shape * np.exp(-tt * 3)
        x = out * shape * 0.5
        st = np.stack([x * np.linspace(1.1, 0.7, n), x * np.linspace(0.7, 1.1, n)], 1)
        return verb(st, 0.25)
    if kind == "riser":
        n = int(0.5 * SR); tt = t_axis(n)
        f = 300 + 2600 * (tt / 0.5) ** 2
        x = bp(rng.standard_normal(n), 800, 7000) * (tt / 0.5) ** 3 * 0.35
        x += np.sin(2 * np.pi * np.cumsum(f) / SR) * (tt / 0.5) ** 3 * 0.04
        return verb(x, 0.3)
    if kind == "snap":
        n = int(0.25 * SR); tt = t_axis(n)
        x = hp(rng.standard_normal(n), 3000) * np.exp(-tt * 55) * 0.7
        f = 5200 * np.exp(-tt * 30) + 900
        x += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40) * 0.25
        return verb(x, 0.2)
    if kind == "flash":
        n = int(1.0 * SR); tt = t_axis(n)
        sub = np.sin(2 * np.pi * 40 * tt) * np.exp(-tt * 8.3) * 0.95
        air = lp(rng.standard_normal(n), 3000) * np.exp(-tt * 14) * 0.25
        return verb(sub + air, 0.2)
    if kind in ("tick", "tick_soft", "click", "key"):
        n = int(0.08 * SR); tt = t_axis(n)
        f = {"tick": 3600, "tick_soft": 2600, "click": 2100, "key": 4200}[kind]
        x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 160) * 0.35
        x += hp(rng.standard_normal(n), 4000) * np.exp(-tt * 400) * 0.3
        if kind == "click":
            n2 = int(0.05 * SR)
            x[int(0.03 * SR):int(0.03 * SR) + n2] += np.sin(2 * np.pi * 1600 * tt[:n2]) * np.exp(-tt[:n2] * 200) * 0.3
        if kind == "key":
            x *= rng.uniform(0.6, 1.0)
        return verb(x, 0.15)
    if kind == "bloom":
        n = int(1.4 * SR)
        x = np.zeros((n, 2))
        for i in range(17):
            s = int(i * 0.03 * SR)
            m = int(0.25 * SR); tt = t_axis(m)
            f = 1800 + i * 90
            blip = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 30) * 0.05
            pan = 0.5 + 0.4 * np.sin(i * 0.9)
            e = min(m, n - s)
            x[s:s + e, 0] += blip[:e] * (1 - pan); x[s:s + e, 1] += blip[:e] * pan
        x += sfx("chime")[:n] * 0.8 if len(sfx("chime")) >= n else 0
        return verb(x, 0.4)
    if kind in ("pop", "pop_in"):
        n = int(0.14 * SR); tt = t_axis(n)
        f = (950 * np.exp(-tt * 38) + 480) if kind == "pop" else (420 + 700 * (1 - np.exp(-tt * 45)))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.002, 38) * 0.42
        x += hp(rng.standard_normal(n), 5000) * np.exp(-tt * 500) * 0.12
        return verb(x, 0.18)
    if kind == "coin":
        n = int(0.5 * SR); tt = t_axis(n)
        x = np.zeros(n)
        for f, a in ((2093, 1.0), (3136, 0.55), (4186, 0.25)):
            x += np.sin(2 * np.pi * f * tt) * a * np.exp(-tt * 14)
        x[int(0.045 * SR):] += (np.sin(2 * np.pi * 2637 * tt[:n - int(0.045 * SR)]) * np.exp(-tt[:n - int(0.045 * SR)] * 12)) * 0.7
        return verb(x * 0.06, 0.3)
    if kind == "iris":
        n = int(0.6 * SR); tt = t_axis(n)
        f = 1600 * np.exp(-tt * 6) + 120
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.01, 6) * 0.14
        x += bp(rng.standard_normal(n), 300, 4000) * env_ar(n, 0.05, 7) * 0.3
        return verb(x, 0.35)
    if kind == "dive":
        n = int(0.8 * SR); tt = t_axis(n)
        x = lp(rng.standard_normal(n), 900) * np.sin(np.pi * np.clip(tt / 0.5, 0, 1)) ** 2 * 0.5
        f = 90 * np.exp(-tt * 5) + 38
        x += np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.02, 5) * 0.6
        return verb(x, 0.25)
    if kind == "scan":
        n = int(0.6 * SR); tt = t_axis(n)
        f = 900 + 5200 * (tt / 0.6)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.6) * 0.05
        x += bp(rng.standard_normal(n), 4000, 11000) * np.sin(np.pi * tt / 0.6) * 0.12
        return verb(x, 0.35)
    if kind == "clack":
        n = int(0.09 * SR); tt = t_axis(n)
        x = bp(rng.standard_normal(n), 1200, 6000) * np.exp(-tt * 120) * 0.6
        x += np.sin(2 * np.pi * 320 * tt) * np.exp(-tt * 70) * 0.35
        return verb(x, 0.15)
    if kind == "shutter":
        n = int(0.5 * SR)
        x = np.zeros(n)
        c = sfx("clack")
        c = c[:, 0] if c.ndim > 1 else c
        for i in range(6):
            s0 = int(i * 0.022 * SR)
            e = min(len(c), n - s0)
            x[s0:s0 + e] += c[:e] * (1 - i * 0.1)
        return verb(x, 0.25)
    if kind == "laser":
        n = int(0.55 * SR); tt = t_axis(n)
        f = 6200 * np.exp(-tt * 7) + 700
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(n, 0.004, 7) * 0.08
        x += bp(rng.standard_normal(n), 2500, 9000) * env_ar(n, 0.01, 10) * 0.18
        st = np.stack([x * np.linspace(1.2, 0.5, n), x * np.linspace(0.5, 1.2, n)], 1)
        return verb(st, 0.35)
    raise ValueError(kind)


def build_sfx():
    bus = np.zeros((N, 2))
    cache = {}
    for t0, kind, gain in cfg["cues"]:
        if kind not in cache or kind == "key":
            cache[kind] = sfx(kind)
        x = cache[kind]
        if x.ndim == 1:
            x = np.stack([x, x], 1)
        # whooshes/risers are designed to peak at the cue → anchor their apex on it
        offset = {"whoosh": 0.35, "whoosh_deep": 0.45, "riser": 0.5, "swell": 1.45}.get(kind, 0.0)
        s = int((t0 - offset) * SR)
        if s < 0:
            x = x[-s:]; s = 0
        e = min(len(x), N - s)
        bus[s:s + e] += x[:e] * gain
    return bus


# ───────────────────────── MEZCLA ─────────────────────────
def main():
    voice, sr = sf.read(os.path.join(AUD, "voice.wav"), dtype="float64")
    assert sr == SR
    v = np.zeros(N); v[: min(N, len(voice))] = voice[:N]
    v = v / (np.abs(v).max() + 1e-9) * 0.8
    vst = np.stack([v, v], 1)

    music = build_music()
    fx = build_sfx()

    # sidechain: envolvente de la voz → reducción de hasta -10 dB en la música
    envv = np.abs(v)
    envv = lp(envv, 6, order=1)
    envv = envv / (envv.max() + 1e-9)
    config_path = os.path.join(HERE, "project_config.json")
    preferences = json.load(open(config_path, encoding="utf-8")).get("flowmusic", {}) if os.path.isfile(config_path) else {}
    duck_db = float(preferences.get("ducking_db", -10))
    if not -10 <= duck_db <= -8:
        raise ValueError("flowmusic.ducking_db debe estar entre -10 y -8")
    duck = 1 - (1 - 10 ** (duck_db / 20)) * np.clip(envv * 3.2, 0, 1)
    duck = lp(duck, 3, order=1)
    music = music * duck[:, None]

    mix = vst * 1.0 + music * 0.55 + fx * 0.85
    # limitador suave
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    raw = os.path.join(AUD, "mix_raw.wav")
    sf.write(raw, mix.astype(np.float32), SR, subtype="FLOAT")
    sf.write(os.path.join(AUD, "music_only.wav"), (music * 0.55).astype(np.float32), SR, subtype="FLOAT")

    out_wav = os.path.join(AUD, "master.wav")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), "-t", f"{DUR:.3f}", out_wav], check=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", out_wav, "-c:a", "aac", "-b:a", "256k",
                    os.path.join(AUD, "master.m4a")], check=True)
    print("master listo:", out_wav)


if __name__ == "__main__":
    main()
