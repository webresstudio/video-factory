#!/usr/bin/env python3
"""audit_music_track.py — Psychoacoustic music & mix auditor for WBRS / WVF.

Analyzes any candidate music file (.m4a, .mp3, .wav) and optional voice/master stems:
  1. True Constant-Q (CQT, Q=34) Harmonic Chromagram across Octaves 3–5 (130.8–987.8 Hz)
     anchored by Bass Fundamental CQT (Octave 2, 65.4–123.5 Hz) to distinguish Major keys
     from relative Minor keys without STFT bass bin leakage.
  2. Octave Register & Bregman Stream Audit ("Cero Octavas Raras"):
     - Measures melodic energy in Octaves 3–4 (180–780 Hz) vs formant-clashing
       Octaves 6–7 (1600–3800 Hz) and sudden >1-octave melodic leaps.
  3. Groove Continuity & Syncopated Punch-Stab / Dropout Detector:
     - Uses 220 ms chordal-duration windows (ignoring 20 ms pop snare transients) to detect
       syncopated brass/funk stabs and stop-go silence pockets that stall spoken pacing.
  4. Uninterrupted Beat-1 Slice Finder (`0 splices` rule) + Consonant SFX Frequency Table (`Hz`).
  5. Optional Voice-to-Music Loudness Delta (`-12.0 to -13.5 dB` Golden Window) & `-14 LUFS` Master Check.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy import ndimage, signal

import env_config

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]
KRUMHANSL_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KRUMHANSL_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def decode_mono_float32(audio_path: str, sr: int = 24000) -> np.ndarray:
    ffmpeg = env_config.get_ffmpeg()
    proc = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            audio_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sr),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    )
    samples = np.frombuffer(proc.stdout, dtype=np.float32)
    if samples.size == 0:
        raise RuntimeError(f"No se pudo decodificar audio desde: {audio_path}")
    return samples


def measure_integrated_lufs_and_tp(
    audio_path: str,
    max_dur: float | None = None,
) -> tuple[float | None, float | None]:
    ffmpeg = env_config.get_ffmpeg()
    cmd = [ffmpeg, "-hide_banner", "-nostats"]
    if max_dur is not None and max_dur > 1.0:
        cmd += ["-t", f"{max_dur:.2f}"]
    cmd += [
        "-i",
        audio_path,
        "-af",
        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    match = re.search(r"\{\s*\"input_i\".*?\}", proc.stderr, flags=re.S)
    if not match:
        return None, None
    try:
        payload = json.loads(match.group(0))
        return float(payload["input_i"]), float(payload["input_tp"])
    except (KeyError, ValueError, TypeError):
        return None, None


def compute_cqt_filterbank_energy(
    samples: np.ndarray,
    sr: int,
    midi_low: int,
    midi_high: int,
    hop: int = 2400,
    q_factor: float = 34.0,
) -> np.ndarray:
    """Compute true Constant-Q power matrix (n_notes x n_frames) via FFT convolution."""
    n_notes = midi_high - midi_low + 1
    n_samples = len(samples)
    frame_centers = np.arange(hop // 2, max(hop // 2 + 1, n_samples - hop // 2), hop)
    n_frames = len(frame_centers)
    out = np.zeros((n_notes, n_frames), dtype=np.float64)

    n_fft = 1 << (n_samples - 1).bit_length()
    sig_fft = np.fft.rfft(samples.astype(np.float64), n=n_fft)

    for idx, midi_note in enumerate(range(midi_low, midi_high + 1)):
        freq = 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))
        win_len = int(min(max(round(q_factor * sr / freq), 512), sr * 2))
        t = np.arange(win_len, dtype=np.float64) - win_len / 2.0
        win = np.hanning(win_len)
        win /= max(np.sum(win), 1e-12)
        kernel_real = win * np.cos(2.0 * np.pi * freq * t / sr)
        kernel_imag = win * np.sin(2.0 * np.pi * freq * t / sr)

        resp_r = np.fft.irfft(sig_fft * np.fft.rfft(kernel_real, n=n_fft), n=n_fft)[:n_samples]
        resp_i = np.fft.irfft(sig_fft * np.fft.rfft(kernel_imag, n=n_fft), n=n_fft)[:n_samples]
        power_env = resp_r[frame_centers] ** 2 + resp_i[frame_centers] ** 2
        # Median-filter across 0.7s (7 hops of 100 ms) to suppress broadband drum transients
        out[idx, :] = ndimage.median_filter(power_env, size=7)
    return out


def compute_harmonic_chroma_and_bands(samples: np.ndarray, sr: int = 24000) -> dict:
    # 1. True CQT in Bass Octave 2 (MIDI 36..47: C2..B2) + Melodic/Chordal Octaves 3..5 (MIDI 48..83: C3..B5)
    hop = int(0.10 * sr)  # 100 ms frames
    bass_cqt = compute_cqt_filterbank_energy(samples, sr=sr, midi_low=36, midi_high=47, hop=hop, q_factor=26.0)
    harm_cqt = compute_cqt_filterbank_energy(samples, sr=sr, midi_low=48, midi_high=83, hop=hop, q_factor=34.0)

    chroma_frames = harm_cqt.reshape(3, 12, -1).sum(axis=0)  # 12 x n_frames
    frame_energy = chroma_frames.sum(axis=0)
    active = frame_energy > (np.percentile(frame_energy, 15) * 0.30 + 1e-18)

    chroma_vec = chroma_frames[:, active].sum(axis=1) if np.any(active) else chroma_frames.sum(axis=1)
    chroma_norm = chroma_vec / max(float(chroma_vec.sum()), 1e-18)

    bass_vec = bass_cqt[:, active].sum(axis=1) if np.any(active) else bass_cqt.sum(axis=1)
    bass_norm = bass_vec / max(float(bass_vec.sum()), 1e-18)

    best_score = -1e9
    best_entry = None
    best_major = None
    best_major_score = -1e9

    for root in range(12):
        maj_pcs = [(root + s) % 12 for s in MAJOR_STEPS]
        min_pcs = [(root + s) % 12 for s in MINOR_STEPS]

        maj_purity = float(chroma_norm[maj_pcs].sum())
        min_purity = float(chroma_norm[min_pcs].sum())

        maj_corr = float(np.corrcoef(chroma_norm, np.roll(KRUMHANSL_MAJOR, root))[0, 1])
        min_corr = float(np.corrcoef(chroma_norm, np.roll(KRUMHANSL_MINOR, root))[0, 1])

        # Bass tonic anchor + triad weight resolves relative Major vs Minor cleanly
        bass_tonic_weight = float(bass_norm[root]) + 0.25 * float(bass_norm[(root + 7) % 12])
        maj_triad = float(chroma_norm[root] + chroma_norm[(root + 4) % 12] + chroma_norm[(root + 7) % 12])
        min_triad = float(chroma_norm[root] + chroma_norm[(root + 3) % 12] + chroma_norm[(root + 7) % 12])

        maj_composite = (
            maj_purity * 0.45
            + max(0.0, maj_corr) * 0.15
            + bass_tonic_weight * 0.35
            + maj_triad * 0.25
        )
        min_composite = (
            min_purity * 0.45
            + max(0.0, min_corr) * 0.15
            + bass_tonic_weight * 0.35
            + min_triad * 0.25
        )

        maj_cand = {
            "root_pc": root,
            "root_name": PITCH_NAMES[root],
            "mode": "major",
            "label": f"{PITCH_NAMES[root]} Major",
            "purity_pct": round(maj_purity * 100.0, 2),
            "bass_root_pct": round(float(bass_norm[root]) * 100.0, 2),
            "profile_corr": round(maj_corr, 3),
            "composite": maj_composite,
        }
        min_cand = {
            "root_pc": root,
            "root_name": PITCH_NAMES[root],
            "mode": "minor",
            "label": f"{PITCH_NAMES[root]} Minor",
            "purity_pct": round(min_purity * 100.0, 2),
            "bass_root_pct": round(float(bass_norm[root]) * 100.0, 2),
            "profile_corr": round(min_corr, 3),
            "composite": min_composite,
        }
        if maj_composite > best_major_score:
            best_major_score = maj_composite
            best_major = maj_cand
        for cand in (maj_cand, min_cand):
            if cand["composite"] > best_score:
                best_score = cand["composite"]
                best_entry = cand

    # 2-second windowed purity in detected scale (20 hops of 100 ms)
    scale_steps = MAJOR_STEPS if best_entry["mode"] == "major" else MINOR_STEPS
    scale_pcs = [(best_entry["root_pc"] + s) % 12 for s in scale_steps]
    win_purities = []
    for col in range(0, chroma_frames.shape[1] - 20 + 1, 20):
        if not np.any(active[col : col + 20]):
            continue
        sub = chroma_frames[:, col : col + 20].sum(axis=1)
        tot = float(sub.sum())
        if tot > 0:
            win_purities.append(float(sub[scale_pcs].sum() / tot) * 100.0)
    p15_purity = round(float(np.percentile(win_purities, 15)), 2) if win_purities else best_entry["purity_pct"]

    # STFT median-filtered harmonic bands for wide register balance (20 Hz .. 3800 Hz)
    freqs, _, zxx = signal.stft(samples, fs=sr, window="hann", nperseg=4096, noverlap=3072)
    harm_power = ndimage.median_filter(np.abs(zxx) ** 2, size=(1, 9))

    def band_energy(f_lo: float, f_hi: float) -> float:
        mask = (freqs >= f_lo) & (freqs < f_hi)
        return float(harm_power[mask, :].sum()) if np.any(mask) else 0.0

    e_sub = band_energy(20.0, 55.0)
    e_bass = band_energy(55.0, 180.0)
    e_mid_sweet = band_energy(180.0, 780.0)
    e_oct5 = band_energy(780.0, 1600.0)
    e_formant_clash = band_energy(1600.0, 3800.0)
    e_non_bass = max(1e-18, e_mid_sweet + e_oct5 + e_formant_clash)
    e_total = max(1e-18, e_sub + e_bass + e_non_bass)

    # Melodic upper-register jump rate across CQT Octaves 3..5
    dom_note = np.argmax(harm_cqt, axis=0)
    note_jumps = np.abs(np.diff(dom_note))
    jump_events = (note_jumps > 13) & active[:-1] & active[1:]
    dur_min = max(len(samples) / sr / 60.0, 1e-3)

    return {
        "detected": best_entry,
        "best_major": best_major,
        "window_p15_purity_pct": p15_purity,
        "bands_pct": {
            "sub_lt_55hz": round(e_sub / e_total * 100.0, 2),
            "bass_55_180hz": round(e_bass / e_total * 100.0, 2),
            "melodic_sweetspot_of_midhigh_pct": round(e_mid_sweet / e_non_bass * 100.0, 2),
            "upper_oct5_of_midhigh_pct": round(e_oct5 / e_non_bass * 100.0, 2),
            "formant_clash_1600_3800_of_midhigh_pct": round(e_formant_clash / e_non_bass * 100.0, 2),
        },
        "octave_jumps_per_min": round(float(np.sum(jump_events)) / dur_min, 1),
    }


def detect_groove_and_best_slice(samples: np.ndarray, sr: int = 24000, target_dur: float = 48.0) -> dict:
    """Evaluate 220ms chordal-envelope continuity (distinguishing stop-go brass stabs from steady pop groove)."""
    sos = signal.butter(4, [350.0 / (sr / 2), 2600.0 / (sr / 2)], btype="bandpass", output="sos")
    mid_sig = signal.sosfilt(sos, samples)

    win = int(0.22 * sr)  # 220 ms window ignores 20 ms snare hits and measures chordal punch stabs
    n_frames = len(mid_sig) // win
    if n_frames < 8:
        return {
            "stab_spikes_gt_6db": 0,
            "groove_dropout_pct": 0.0,
            "chordal_crest_p98_db": 0.0,
            "recommended_start_sec": 0.0,
            "recommended_slice_splices": 0,
        }

    framed = mid_sig[: n_frames * win].reshape(n_frames, win)
    rms_db = 20.0 * np.log10(np.sqrt(np.mean(framed ** 2, axis=1) + 1e-12))
    baseline_db = ndimage.median_filter(rms_db, size=15)  # ~3.3s local phrase baseline
    active = baseline_db > (np.percentile(baseline_db, 15) - 5.0)
    delta_db = rms_db - baseline_db

    stabs = int(np.sum((delta_db > 6.0) & active))
    dropouts = float(np.mean((delta_db < -5.5) & active) * 100.0) if np.any(active) else 0.0
    crest_p98 = round(float(np.percentile(delta_db[active], 98)), 2) if np.any(active) else 0.0

    total_sec = len(samples) / sr
    if total_sec <= target_dur + 1.0:
        best_start = 0.0
    else:
        slice_len = max(1, int(round(target_dur / 0.22)))
        max_start = max(1, min(n_frames - slice_len, int(45.0 / 0.22)))
        best_cost = 1e18
        best_start = 0.0
        for s_idx in range(0, max_start):
            seg_db = rms_db[s_idx : s_idx + slice_len]
            seg_delta = delta_db[s_idx : s_idx + slice_len]
            dropout_pen = float(np.maximum(0.0, np.median(seg_db) - seg_db - 5.0).mean())
            stab_pen = float(np.maximum(0.0, seg_delta - 5.5).mean()) * 1.5
            onset_bonus = -0.25 if seg_delta[0] > 0.5 else 0.0
            cost = dropout_pen + stab_pen + onset_bonus
            if cost < best_cost:
                best_cost = cost
                best_start = round(s_idx * 0.22, 2)

    return {
        "stab_spikes_gt_6db": stabs,
        "groove_dropout_pct": round(dropouts, 2),
        "chordal_crest_p98_db": crest_p98,
        "recommended_start_sec": best_start,
        "recommended_slice_splices": 0,
    }


def build_consonant_sfx_table(root_pc: int) -> dict:
    midi_root4 = 60 + root_pc
    root_hz = 440.0 * (2.0 ** ((midi_root4 - 69) / 12.0))

    def f_semi(n: int) -> float:
        return round(root_hz * (2.0 ** (n / 12.0)), 2)

    return {
        "tonic_oct4_hz": round(root_hz, 2),
        "click": {"type": "athermal_sweep", "start_hz": 1700.0, "floor_hz": 220.0, "dur_ms": 24},
        "chime": {"notes_hz": [f_semi(12), f_semi(19)], "interval": "Octave5 + PerfectFifth6", "dur_ms": 340},
        "sub_soft": {"drop_hz": [f_semi(-12), f_semi(-24)], "interval": "Octave2 -> Octave1 Tonic", "dur_ms": 260},
        "bloom": {
            "chord_hz": [f_semi(0), f_semi(4), f_semi(7), f_semi(12)],
            "interval": "Major Triad I-III-V-VIII",
            "dur_ms": 750,
        },
    }


def audit_music_file(
    music_path: str,
    voice_path: str = "",
    master_path: str = "",
    target_dur: float = 48.0,
) -> dict:
    sr = 24000
    samples = decode_mono_float32(music_path, sr=sr)
    duration_sec = round(len(samples) / sr, 2)

    harmonic = compute_harmonic_chroma_and_bands(samples, sr=sr)
    rhythm = detect_groove_and_best_slice(samples, sr=sr, target_dur=target_dur)

    det = harmonic["detected"]
    best_maj = harmonic["best_major"]
    sfx_table = build_consonant_sfx_table(best_maj["root_pc"])

    issues = []
    warnings = []

    if det["mode"] == "minor":
        issues.append(
            f"Modo MENOR detectado ({det['label']}, pureza {det['purity_pct']}%). "
            f"Bajo locución ejecutiva suena tenso o desafinado; usa escala Mayor brillante (F#, G, A, E Major)."
        )
    if det["purity_pct"] < 80.0:
        issues.append(
            f"Pureza diatónica CQT insuficiente ({det['purity_pct']}% < 80%): "
            f"contiene cromatismo fuera de la escala mayor."
        )
    elif det["purity_pct"] < 83.0:
        warnings.append(f"Pureza diatónica CQT moderada ({det['purity_pct']}%); ideal >= 83%.")

    bands = harmonic["bands_pct"]
    if bands["formant_clash_1600_3800_of_midhigh_pct"] > 24.0:
        issues.append(
            f"Exceso de energía melódica aguda en Octavas 6-7 ({bands['formant_clash_1600_3800_of_midhigh_pct']}%): "
            f"octavas altas chocan con las consonantes de la voz."
        )
    elif bands["formant_clash_1600_3800_of_midhigh_pct"] > 17.0:
        warnings.append(
            f"Brillo melódico alto en 1.6-3.8 kHz ({bands['formant_clash_1600_3800_of_midhigh_pct']}%): "
            f"asegura bolsillo EQ -2.2 dB @ 1.9 kHz."
        )

    stabs_per_min = rhythm["stab_spikes_gt_6db"] / max(duration_sec / 60.0, 0.25)
    if stabs_per_min > 8.5 or rhythm["groove_dropout_pct"] > 12.0:
        warnings.append(
            f"Detectados acentos sincopados/cortes de groove (stabs={rhythm['stab_spikes_gt_6db']} [{stabs_per_min:.1f}/min], "
            f"huecos={rhythm['groove_dropout_pct']}%): verifica que no tenga 'punch/brass hits' que frenen la voz."
        )

    speech_span = (duration_sec - 3.8) if duration_sec > 15.0 else None
    music_lufs, music_tp = measure_integrated_lufs_and_tp(music_path, max_dur=speech_span)
    voice_lufs = None
    music_below_voice_db = None
    master_lufs = None
    master_tp = None

    if voice_path and os.path.isfile(voice_path):
        voice_lufs, _ = measure_integrated_lufs_and_tp(voice_path, max_dur=speech_span)
        mix_raw_candidate = os.path.join(os.path.dirname(os.path.abspath(music_path)), "mix_raw.wav")
        if (
            os.path.basename(music_path) == "music_only.wav"
            and os.path.isfile(mix_raw_candidate)
            and music_lufs is not None
        ):
            mix_speech_lufs, _ = measure_integrated_lufs_and_tp(mix_raw_candidate, max_dur=speech_span)
            if mix_speech_lufs is not None:
                p_voice = (10.0 ** (mix_speech_lufs / 10.0)) - (10.0 ** (music_lufs / 10.0))
                if p_voice > 1e-9:
                    import math
                    voice_lufs = round(10.0 * math.log10(p_voice), 2)
        if voice_lufs is not None and music_lufs is not None:
            music_below_voice_db = round(music_lufs - voice_lufs, 2)
            if music_below_voice_db > -10.5:
                issues.append(
                    f"Cama musical demasiado alta ({music_below_voice_db} dB respecto a la voz; ventana ideal -12.0 a -13.5 dB)."
                )
            elif music_below_voice_db < -15.5:
                issues.append(
                    f"Cama musical casi inaudible ({music_below_voice_db} dB respecto a la voz; ventana ideal -12.0 a -13.5 dB)."
                )

    if master_path and os.path.isfile(master_path):
        master_lufs, master_tp = measure_integrated_lufs_and_tp(master_path)
        if master_lufs is not None and not (-15.0 <= master_lufs <= -13.0):
            issues.append(f"Master fuera de norma EBU R128 ({master_lufs} LUFS; meta -14.0 ± 1.0 LUFS).")
        if master_tp is not None and master_tp > -1.0:
            issues.append(f"True Peak del master excesivo ({master_tp} dBTP > -1.0 dBTP).")

    verdict = "FAIL" if issues else ("WARN" if warnings else "PASS")
    return {
        "audited_at": dt.datetime.now().isoformat(timespec="seconds"),
        "music_file": music_path,
        "duration_sec": duration_sec,
        "verdict": verdict,
        "detected_key": det["label"],
        "detected_mode": det["mode"],
        "diatonic_purity_pct": det["purity_pct"],
        "window_p15_purity_pct": harmonic["window_p15_purity_pct"],
        "best_major_key": best_maj["label"],
        "register_bands_pct": bands,
        "octave_jumps_per_min": harmonic["octave_jumps_per_min"],
        "rhythm": rhythm,
        "sfx_frequencies_hz": sfx_table,
        "loudness": {
            "music_lufs": music_lufs,
            "music_tp_db": music_tp,
            "voice_lufs": voice_lufs,
            "music_below_voice_db": music_below_voice_db,
            "master_lufs": master_lufs,
            "master_tp_db": master_tp,
        },
        "issues": issues,
        "warnings": warnings,
    }


def print_music_audit(rep: dict) -> None:
    print(f"\n🎵 [wvf audit-music] {os.path.basename(rep['music_file'])} ({rep['duration_sec']}s) → {rep['verdict']}")
    print(
        f"   Tonalidad CQT: {rep['detected_key']} · Pureza diatónica: {rep['diatonic_purity_pct']}% "
        f"(p15={rep['window_p15_purity_pct']}%)"
    )
    b = rep["register_bands_pct"]
    print(
        f"   Registro melódico (sin bajo): Oct3-4 dulce (180-780Hz)={b['melodic_sweetspot_of_midhigh_pct']}% · "
        f"Choque vocal (1.6-3.8kHz)={b['formant_clash_1600_3800_of_midhigh_pct']}%"
    )
    r = rep["rhythm"]
    print(
        f"   Continuidad rítmica: stabs={r['stab_spikes_gt_6db']} · huecos={r['groove_dropout_pct']}% · "
        f"Corte continuo recomendado desde t={r['recommended_start_sec']}s (0 splices)"
    )
    sfx = rep["sfx_frequencies_hz"]
    print(
        f"   SFX afinados ({rep['best_major_key']}): chime={sfx['chime']['notes_hz']} Hz · "
        f"sub_soft={sfx['sub_soft']['drop_hz']} Hz · bloom={sfx['bloom']['chord_hz']} Hz"
    )
    ld = rep["loudness"]
    if ld["music_below_voice_db"] is not None:
        print(
            f"   Mezcla: voz={ld['voice_lufs']} LUFS · cama={ld['music_lufs']} LUFS "
            f"(delta={ld['music_below_voice_db']} dB, ideal -12.0 a -13.5 dB)"
        )
    if ld["master_lufs"] is not None:
        print(f"   Master: {ld['master_lufs']} LUFS · {ld['master_tp_db']} dBTP")
    for w in rep["warnings"]:
        print(f"   ! {w}")
    for iss in rep["issues"]:
        print(f"   ✗ {iss}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Auditor psicoacústico CQT y de mezcla broadcast (-14 LUFS) para WVF.")
    ap.add_argument("music", help="Archivo de música candidata o stem de cama musical (.m4a, .mp3, .wav)")
    ap.add_argument("--voice", default="", help="Opcional: stem de voz (audio/voice.wav) para verificar ventana -12 a -13.5 dB")
    ap.add_argument("--master", default="", help="Opcional: mezcla final (audio/master.wav) para verificar -14 LUFS")
    ap.add_argument("--target-dur", type=float, default=48.0, help="Duración objetivo del corte sin empalmes (default: 48s)")
    ap.add_argument("--out", default="", help="Ruta de salida JSON (default: check/music_audit.json si está en un proyecto)")
    args = ap.parse_args(argv)

    rep = audit_music_file(args.music, voice_path=args.voice, master_path=args.master, target_dur=args.target_dur)
    print_music_audit(rep)

    out_path = args.out
    if not out_path:
        proj_root = env_config.find_project_root(args.music) or os.getcwd()
        if os.path.isfile(os.path.join(proj_root, "script.json")) or os.path.isdir(os.path.join(proj_root, "check")):
            out_path = os.path.join(proj_root, "check", "music_audit.json")
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        print(f"   💾 Reporte guardado en: {out_path}")

    return 1 if rep["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
