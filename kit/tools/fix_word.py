#!/usr/bin/env python3
"""Replace a word with an aligned patch, preserving the original duration and word clock."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import re
import numpy as np
import soundfile as sf
from env_config import get_ffmpeg, get_project_root


def norm(text):
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c)))


def find_word(words, word, occurrence=1):
    matches = [i for i, item in enumerate(words) if norm(item['w']) == norm(word)]
    if occurrence < 1 or len(matches) < occurrence:
        raise ValueError(f'No se encontró {word!r}, ocurrencia {occurrence}, en la transcripción.')
    return matches[occurrence-1]


def apply_patch(original, words, target_index, patch_audio, patch_words, patch_index, sample_rate=48000):
    target, replacement = words[target_index], patch_words[patch_index]
    start, end = round(target['t']*sample_rate), round(target['e']*sample_rate)
    pstart, pend = round(replacement['t']*sample_rate), round(replacement['e']*sample_rate)
    if not 0 <= start < end <= len(original) or not 0 <= pstart < pend <= len(patch_audio):
        raise ValueError('Los timestamps están fuera del audio.')
    segment = patch_audio[pstart:pend]
    speed = len(segment)/(end-start)
    if not 0.5 <= speed <= 2:
        raise ValueError('El parche requiere una modificación de velocidad excesiva; generar otra toma.')
    with tempfile.TemporaryDirectory(prefix='wvf-word-') as td:
        source, stretched = Path(td)/'source.wav', Path(td)/'stretched.wav'
        sf.write(source, segment, sample_rate)
        subprocess.run([get_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(source), '-af', f'atempo={speed:.8f}', str(stretched)], check=True)
        adjusted, sr = sf.read(stretched, dtype='float32')
    adjusted = adjusted.mean(axis=1) if adjusted.ndim > 1 else adjusted
    adjusted = np.pad(adjusted, (0, max(0,end-start-len(adjusted))))[:end-start]
    source_level = np.sqrt(np.mean(original[start:end]**2))
    patch_level = np.sqrt(np.mean(adjusted**2))
    if patch_level < 1e-5:
        raise ValueError('El parche está vacío o en silencio.')
    adjusted *= min(4, source_level/patch_level)
    fade = min(round(0.008*sample_rate), (end-start)//4)
    envelope = np.ones(end-start,dtype='float32')
    if fade:
        envelope[:fade] = np.linspace(0,1,fade); envelope[-fade:] = np.linspace(1,0,fade)
    output = original.copy()
    output[start:end] = original[start:end]*(1-envelope)+adjusted*envelope
    updated = [dict(w) for w in words]
    updated[target_index]['w'] = replacement['w']
    return output, updated


def transcribe(path):
    from faster_whisper import WhisperModel
    segments, _ = WhisperModel('small', device='cpu', compute_type='int8').transcribe(str(path), language='es', word_timestamps=True, vad_filter=False)
    return [{'w':w.word.strip(), 't':round(w.start,3), 'e':round(w.end,3)} for segment in segments for w in segment.words]


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('line_id'); ap.add_argument('target_word'); ap.add_argument('phonetic_phrase')
    ap.add_argument('--patch-file', help='Usar una toma local en lugar de generar en Flow')
    ap.add_argument('--patch-word', help='Palabra pronunciada que se extraerá de la toma')
    ap.add_argument('--patch-words', help='Transcripción JSON del parche; opcional, evita retranscribir')
    ap.add_argument('--occurrence',type=int,default=1)
    ap.add_argument('--timeout',type=float,default=300)
    ap.add_argument('--dry',action='store_true')
    args=ap.parse_args(argv); root=Path(get_project_root())
    if not re.fullmatch(r'L\d{2}',args.line_id): ap.error('line_id debe tener formato L01')
    audio_path=root/'flow'/f'{args.line_id}.wav'; words_path=root/'flow'/f'{args.line_id}.words.json'
    try:
        words=json.loads(words_path.read_text(encoding='utf-8'))
        target=find_word(words,args.target_word,args.occurrence)
        prompt=root/'scratch'/f'{args.line_id}_fix.txt'; prompt.parent.mkdir(parents=True,exist_ok=True)
        # A full presenter prompt is necessary to generate audible speech, not only text.
        prompt.write_text('Vertical video of me using the attached likeness and my own voice. Speak clearly in Latin American Spanish: '+json.dumps(args.phonetic_phrase,ensure_ascii=False)+'. No music, subtitles or on-screen text.',encoding='utf-8')
        if args.dry:
            print(f'Validado; prompt: {prompt}. No se modificó el audio.'); return 0
        script=json.loads((root/'script.json').read_text(encoding='utf-8'))
        if next(line for line in script if line['id']==args.line_id).get('cam'):
            raise ValueError('Esta línea muestra al presentador. Regenerar su toma completa para conservar la sincronización labial; fix-word es para voz en off.')
        patch_file=Path(args.patch_file) if args.patch_file else None
        if patch_file is None:
            subprocess.run([sys.executable,str(Path(__file__).with_name('flow_submit.py')),'--dur','8','--res','720p','--prompt-file',str(prompt)],check=True)
            from flow_download import status, download
            deadline=time.monotonic()+args.timeout
            patch_dir=root/'flow'/f'{args.line_id}_PATCH'
            while time.monotonic()<deadline:
                found=status(args.phonetic_phrase)
                if found and download(found[0]['i'],str(patch_dir)):
                    clips=sorted(patch_dir.glob('**/*.mp4'),key=lambda p:p.stat().st_mtime)
                    if clips: patch_file=clips[-1]; break
                time.sleep(2)
            if patch_file is None: raise RuntimeError('Flow no entregó el parche dentro del plazo; el audio original se conserva.')
        patch_words=json.loads(Path(args.patch_words).read_text(encoding='utf-8')) if args.patch_words else transcribe(patch_file)
        patch_index=find_word(patch_words,args.patch_word or args.target_word)
        with tempfile.TemporaryDirectory(prefix='wvf-patch-') as td:
            patch_wav=Path(td)/'patch.wav'
            subprocess.run([get_ffmpeg(),'-y','-loglevel','error','-i',str(patch_file),'-ar','48000','-ac','1',str(patch_wav)],check=True)
            patch_audio,_=sf.read(patch_wav,dtype='float32')
        original,sr=sf.read(audio_path,dtype='float32')
        if sr!=48000: raise ValueError('La voz original debe estar a 48000 Hz.')
        if original.ndim>1: original=original.mean(axis=1)
        output,updated=apply_patch(original,words,target,patch_audio,patch_words,patch_index)
        backup=root/'scratch'/('word-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(); shutil.copy2(audio_path,backup/audio_path.name); shutil.copy2(words_path,backup/words_path.name)
        sf.write(audio_path,output,48000,subtype='PCM_24')
        words_path.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf-8')
        try:
            subprocess.run([sys.executable,str(Path(__file__).with_name('build_timeline.py'))],cwd=root,check=True)
        except Exception:
            shutil.copy2(backup/audio_path.name,audio_path); shutil.copy2(backup/words_path.name,words_path)
            raise
        print(f'✅ Palabra corregida y timeline actualizado. Respaldo: {backup}. Ejecutar wvf audio y wvf render para actualizar el master.')
        return 0
    except Exception as exc:
        print(f'❌ {exc}'); return 1


if __name__=='__main__': raise SystemExit(main())
