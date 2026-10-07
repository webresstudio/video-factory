#!/usr/bin/env python3
"""Compress a master under a measured byte limit and true peak; optionally send to the selected WhatsApp chat."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from env_config import find_master, get_ffmpeg, get_ffprobe, get_project_root
from qa import measure_loudness

MAX_TRUE_PEAK = -1.0
# Same targets as build_audio.py, but AAC at 128 kbps raised peaks ~1 dB on a real master
# (WhatsApp Ahorro: -1.8 dBTP before encoding, -0.8 after), so the ceiling leaves 2 dB.
LIMITER = 'loudnorm=I=-14:TP=-3:LRA=9'


def loudness(path):
    measured = measure_loudness(path)
    return float(measured['input_i']), float(measured['input_tp'])


def compress(master, output, max_mb=15):
    if max_mb <= 0:
        raise ValueError('El límite de tamaño debe ser positivo.')
    meta = json.loads(subprocess.run([get_ffprobe(), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(master)], capture_output=True, text=True, check=True).stdout)
    has_audio = any(s.get('codec_type') == 'audio' for s in meta.get('streams', []))
    duration = float(meta['format']['duration'])
    if duration <= 0:
        raise ValueError('El master tiene duración inválida.')
    budget = int(max_mb * 1024 * 1024)
    audio_rate = 128000
    video_rate = min(3000000, int(budget * 8 * 0.92 / duration) - audio_rate)
    if video_rate < 100000:
        raise ValueError('El límite de tamaño es demasiado pequeño para la duración del video.')
    output.parent.mkdir(parents=True, exist_ok=True)
    if master.resolve() == output.resolve():
        raise ValueError('La salida no puede sobreescribir el master.')
    with tempfile.TemporaryDirectory(prefix='wvf-share-') as tmp:
        encoded = Path(tmp)/'mobile.mp4'
        common = [get_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(master), '-c:v', 'libx264',
                  '-preset', 'slow', '-b:v', str(video_rate), '-pix_fmt', 'yuv420p', '-passlogfile', str(Path(tmp)/'pass')]
        subprocess.run(common + ['-pass', '1', '-an', '-f', 'null', '-'], check=True)
        subprocess.run(common + ['-pass', '2', '-c:a', 'aac', '-b:a', str(audio_rate), '-movflags', '+faststart', str(encoded)], check=True)
        # Re-encoding AAC at a lower bitrate can push inter-sample peaks over the limit.
        peak = loudness(encoded)[1] if has_audio else None
        if peak is not None and peak > MAX_TRUE_PEAK:
            print(f'⚠️ True peak {peak:.2f} dBTP en la versión móvil; limitando el audio...')
            limited = Path(tmp)/'mobile_limited.mp4'
            subprocess.run([get_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(encoded), '-i', str(master),
                            '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', LIMITER, '-ar', '48000', '-ac', '2',
                            '-c:a', 'aac', '-b:a', str(audio_rate), '-movflags', '+faststart', str(limited)], check=True)
            integrated, peak = loudness(limited)
            if peak > MAX_TRUE_PEAK or abs(integrated + 14) > 1:
                raise RuntimeError(f'Tras limitar quedó en {integrated:.2f} LUFS y {peak:.2f} dBTP '
                                   f'(se requiere -14 ±1 LUFS y máximo {MAX_TRUE_PEAK} dBTP); no se enviará.')
            encoded = limited
        shutil.move(str(encoded), str(output))
    if output.stat().st_size >= budget:
        raise RuntimeError(f'La salida supera el límite de {max_mb} MB; no se enviará.')
    return output.stat().st_size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--master'); ap.add_argument('--out')
    ap.add_argument('--max-mb', type=float, default=15)
    ap.add_argument('--send-wa', action='store_true')
    ap.add_argument('--contact', default='William Romero')
    args = ap.parse_args(argv)
    root = Path(get_project_root(args.master))
    try:
        master = args.master or find_master(str(root))
    except RuntimeError as exc:
        ap.error(str(exc))
    if not master:
        ap.error('No se encontró un master MP4.')
    master = Path(master)
    output = Path(args.out) if args.out else root/'share/mobile_share.mp4'
    try:
        size = compress(master, output, args.max_mb)
        print(f'✅ Versión móvil: {output} ({size / 1024**2:.2f} MB)')
        if args.send_wa:
            from wajs import send_file
            send_file(output, args.contact)
            print(f'✅ Video enviado al chat de {args.contact}.')
    except Exception as exc:
        print(f'❌ {exc}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
