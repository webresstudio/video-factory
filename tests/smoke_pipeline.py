#!/usr/bin/env python3
"""Offline integration: new preview, synthetic voice, cues, mix, real CDP render, QA and share.

No Flow generation, model download or external message is performed.
"""
from functools import partial
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/tools'))
from env_config import get_chrome
from playwright.sync_api import sync_playwright


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def run(project,*args,env=None):
    proc=subprocess.run([str(ROOT/'bin/wvf'),*map(str,args)],cwd=project,env=env,capture_output=True,text=True)
    if proc.returncode:
        raise RuntimeError(f"wvf {' '.join(map(str,args))}:\n{proc.stdout}\n{proc.stderr}")
    print(f"PASS wvf {' '.join(map(str,args))}",flush=True)
    return proc.stdout


def main():
    with tempfile.TemporaryDirectory(prefix='wvf-smoke-') as td:
        project=Path(td)/'project'
        run(Path(td),'new','project','--path',project)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(project)))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}/index.html'
        env=dict(os.environ,WVF_PREVIEW_URL=url+'?render=1')
        try:
            with sync_playwright() as play:
                kwargs={'headless':True}
                if get_chrome():kwargs['executable_path']=get_chrome()
                browser=play.chromium.launch(**kwargs)
                page=browser.new_page(viewport={'width':540,'height':960})
                page.goto(url);page.wait_for_function('window.READY || window.BOOT_ERROR',timeout=30000)
                error=page.evaluate('window.BOOT_ERROR || null');assert not error,error
                assert page.get_by_text('Plantilla de ejemplo',exact=False).count()==1
                print('PASS fresh-project preview',flush=True)
                page.goto(url+'?render=1');page.wait_for_function('window.BOOT_ERROR',timeout=10000)
                assert 'Timeline pendiente' in page.evaluate('window.BOOT_ERROR')
                print('PASS preview-only demo cannot export',flush=True)
                browser.close()
            script=json.loads((project/'script.json').read_text())
            for line in script:
                line['cam']=False
                words=line['text'].split();duration=1.5
                step=duration/len(words)
                transcript=[{'w':w,'t':0.08+i*step,'e':0.08+(i+0.8)*step} for i,w in enumerate(words)]
                t=np.arange(int(1.7*48000))/48000
                voice=(0.2*np.sin(2*np.pi*220*t)*(0.55+0.45*np.sin(2*np.pi*4*t)**2)).astype('float32')
                sf.write(project/'flow'/f"{line['id']}.wav",voice,48000)
                (project/'flow'/f"{line['id']}.words.json").write_text(json.dumps(transcript))
            (project/'script.json').write_text(json.dumps(script,ensure_ascii=False))
            run(project,'timeline',env=env)
            run(project,'cues',env=env)
            run(project,'audio',env=env)
            run(project,'frames','1.0','10.0','15.0',env=env)
            with sync_playwright() as play:
                kwargs={'headless':True}
                if get_chrome():kwargs['executable_path']=get_chrome()
                browser=play.chromium.launch(**kwargs);page=browser.new_page(viewport={'width':1080,'height':1920})
                page.goto(url+'?render=1');page.wait_for_function('window.READY || window.BOOT_ERROR',timeout=30000)
                assert not page.evaluate('window.BOOT_ERROR || null')
                shots={}
                for t in (1,10,15,1,10,15):
                    page.evaluate('(async t=>{await window.prepare(t);window.renderAt(t)})',t)
                    digest=hashlib.sha256(page.screenshot()).hexdigest()
                    if t in shots: assert digest==shots[t],f'Non-deterministic frame at {t}'
                    shots[t]=digest
                print('PASS identical frames after out-of-order seeks',flush=True)
                browser.close()
            run(project,'render','--workers','2','--fps','30','--test',env=env)
            probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(project/'test_render.mp4')],capture_output=True,text=True,check=True).stdout)
            video=next(s for s in probe['streams'] if s['codec_type']=='video')
            assert video['r_frame_rate']=='30/1' and int(video['nb_frames'])==60,video
            print('PASS --test exports exactly 2 seconds at requested 30 fps',flush=True)
            run(project,'render','--workers','2','--fps','60','--duration','3',env=env)
            run(project,'qa','--technical-only',env=env)
            report=json.loads((project/'check/qa_report.json').read_text());assert report['passed']
            run(project,'share',env=env)
            assert (project/'share/mobile_share.mp4').stat().st_size<15*1024**2
            # A genuinely invalid clip must cause a nonzero CLI exit.
            invalid=project/'invalid.mp4'
            subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=size=320x240:rate=24:duration=3','-f','lavfi','-i','sine=frequency=440:sample_rate=44100:duration=3','-c:v','libx264','-c:a','aac','-ac','1','-shortest',str(invalid)],capture_output=True,check=True)
            failed=subprocess.run([str(ROOT/'bin/wvf'),'qa',str(invalid),'--technical-only'],cwd=project,env=env,capture_output=True,text=True)
            assert failed.returncode==1,failed.stdout
            print('PASS invalid real video rejected by CLI QA',flush=True)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)
    print('Offline integration passed; temporary projects removed.',flush=True)


if __name__=='__main__':main()
