#!/usr/bin/env python3
"""Failing technical and transcript audit for a WVF master (48 kHz stereo, 60 fps)."""
import argparse
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import re
import subprocess
import unicodedata
from env_config import find_master, get_ffmpeg, get_ffprobe, get_project_root


def tokens(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return re.findall(r'[a-z0-9]+', text)


def word_error_rate(expected, actual):
    reference, hypothesis = tokens(expected), tokens(actual)
    if not reference:
        raise ValueError('El guion de referencia está vacío.')
    row = list(range(len(hypothesis) + 1))
    for i, word in enumerate(reference, 1):
        nxt = [i]
        for j, observed in enumerate(hypothesis, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j-1] + (word != observed)))
        row = nxt
    return row[-1] / len(reference)


def audit_metadata(meta, loudness):
    errors = []
    streams = meta.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video'), {})
    audio = next((s for s in streams if s.get('codec_type') == 'audio'), {})
    if (video.get('width'), video.get('height')) != (1080, 1920):
        errors.append('Resolución: se requiere 1080x1920.')
    for key in ('r_frame_rate', 'avg_frame_rate'):
        try:
            fps = float(Fraction(video.get(key, '0/1')))
        except (ValueError, ZeroDivisionError):
            fps = 0
        if abs(fps - 60) > 0.01:
            errors.append(f'Frame rate {key}: se requieren 60 fps constantes.')
    if video.get('codec_name') != 'h264' or video.get('pix_fmt') != 'yuv420p':
        errors.append('Video: se requiere H.264 yuv420p.')
    if str(audio.get('sample_rate')) != '48000' or audio.get('channels') != 2:
        errors.append('Audio: se requieren 48000 Hz y 2 canales.')
    try:
        duration = float(meta.get('format', {}).get('duration', 0))
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        errors.append('Duración ausente o inválida.')
    for key, label, check in (
        ('input_i', 'Volumen integrado: -14 LUFS ±1.', lambda x: abs(x + 14) <= 1),
        ('input_tp', 'True peak: máximo -1.0 dBTP.', lambda x: x <= -1),
    ):
        try:
            value = float(loudness[key])
            if not math.isfinite(value) or not check(value):
                errors.append(label)
        except (KeyError, TypeError, ValueError):
            errors.append(f'Medición ausente: {label}')
    return errors


def measure_loudness(path):
    result = subprocess.run([get_ffmpeg(), '-hide_banner', '-i', str(path), '-vn',
        '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True, check=True)
    start, end = result.stderr.rfind('{'), result.stderr.rfind('}')
    if start < 0 or end <= start:
        raise RuntimeError('FFmpeg no devolvió medición de volumen.')
    return json.loads(result.stderr[start:end+1])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file', nargs='?')
    ap.add_argument('--technical-only', action='store_true', help='Auditar únicamente parámetros técnicos, sin aprobar claridad vocal')
    ap.add_argument('--max-wer', type=float, default=0.05, help='Error máximo de palabras frente al guion (default: 0.05)')
    args = ap.parse_args(argv)
    if not 0 <= args.max_wer <= 1:
        ap.error('--max-wer debe estar entre 0 y 1')
    if args.file:
        target = Path(args.file).resolve()
        root = Path(get_project_root(target))
    else:
        root = Path(get_project_root())
        try:
            master = find_master(str(root))
        except RuntimeError as exc:
            ap.error(str(exc))
        if not master:
            ap.error('No se encontró un master MP4; especifica el archivo.')
        target = Path(master)
    report = {'file': str(target), 'scope': 'technical_only' if args.technical_only else 'full', 'errors': []}
    try:
        probe = subprocess.run([get_ffprobe(), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(target)], capture_output=True, text=True, check=True)
        report['metadata'] = json.loads(probe.stdout)
        report['loudness'] = measure_loudness(target)
        report['errors'].extend(audit_metadata(report['metadata'], report['loudness']))
    except Exception as exc:
        report['errors'].append(f'No se pudo medir el master: {exc}')
    # Transcribe even after technical failures so the report shows every problem; skip only unreadable files.
    if not args.technical_only and 'metadata' in report:
        try:
            script = json.loads((root/'script.json').read_text(encoding='utf-8'))
            expected = ' '.join(line.get('spoken_text', line['text']) for line in script)
            from whisper_compat import patch_av_open
            patch_av_open()
            from faster_whisper import WhisperModel
            segments, _ = WhisperModel('small', device='cpu', compute_type='int8').transcribe(str(target), language='es', vad_filter=False)
            actual = ' '.join(segment.text.strip() for segment in segments)
            report.update(transcription=actual, expected=expected, word_error_rate=word_error_rate(expected, actual))
            if report['word_error_rate'] > args.max_wer:
                report['errors'].append(f"Transcripción difiere del guion: WER {report['word_error_rate']:.1%} > {args.max_wer:.1%}.")
        except Exception as exc:
            report['errors'].append(f'Auditoría vocal incompleta: {exc}')
    check = root/'check'; check.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        try:
            duration = float(report.get('metadata', {}).get('format', {}).get('duration', 0))
        except (TypeError, ValueError):
            duration = 0
        # 12 tiles spread over the whole video, not only its first 24 s.
        rate = 12 / duration if math.isfinite(duration) and duration > 0 else 0.5
        try:
            subprocess.run([get_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(target),
                '-vf', f'fps={rate:.6f},scale=270:-1,tile=6x2', '-frames:v', '1', str(check/'qa_master_sheet.jpg')], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as exc:
            report['errors'].append(f'No se pudo generar la hoja de contactos: {exc}')
    report['passed'] = not report['errors']
    (check/'qa_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for error in report['errors']:
        print(f'❌ {error}')
    if report['passed']:
        print('✅ QA técnico aprobado.' if args.technical_only else '✅ QA técnico y transcripción aprobados; revisar visualmente y escuchar antes de publicar.')
    print(f"Informe: {check/'qa_report.json'}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
