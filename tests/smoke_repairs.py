#!/usr/bin/env python3
"""Exercise the actual local word-patch CLI and 24 fps camera-frame extraction."""
import json
from functools import partial
import http.server
import threading
import sys
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]


def run(project,*args):
    result=subprocess.run([str(ROOT/'bin/wvf'),*map(str,args)],cwd=project,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    return result


def main():
    with tempfile.TemporaryDirectory(prefix='wvf-repairs-') as td:
        project=Path(td)/'project';run(Path(td),'new','project','--path',project)
        lines=json.loads((project/'script.json').read_text())
        for line in lines:
            line['cam']=False
            words=[{'w':w,'t':round(0.2+i*0.1,3),'e':round(0.28+i*0.1,3)} for i,w in enumerate(line['text'].split())]
            (project/'flow'/f"{line['id']}.words.json").write_text(json.dumps(words))
            t=np.arange(4*48000)/48000
            sf.write(project/'flow'/f"{line['id']}.wav",0.2*np.sin(2*np.pi*220*t),48000)
        (project/'script.json').write_text(json.dumps(lines))
        run(project,'timeline')
        before=(project/'timing.js').read_text()
        source,sr=sf.read(project/'flow/L01.wav');words=json.loads((project/'flow/L01.words.json').read_text())
        target=next(w for w in words if w['w']=='API')
        t=np.arange(48000)/48000;patch_file=project/'patch.wav';sf.write(patch_file,0.2*np.sin(2*np.pi*440*t),48000)
        transcript=project/'patch.words.json';transcript.write_text(json.dumps([{'w':'ápi','t':0.1,'e':0.2}]))
        run(project,'fix-word','L01','API','la ápi','--patch-file',patch_file,'--patch-words',transcript,'--patch-word','ápi')
        updated,_=sf.read(project/'flow/L01.wav');actual=json.loads((project/'flow/L01.words.json').read_text())
        assert len(updated)==len(source)
        np.testing.assert_array_equal(updated[:round(target['t']*sr)],source[:round(target['t']*sr)])
        np.testing.assert_array_equal(updated[round(target['e']*sr):],source[round(target['e']*sr):])
        assert actual[next(i for i,w in enumerate(words) if w['w']=='API')]['w']=='ápi'
        assert list((project/'scratch').glob('word-backup-*/L01.wav'))
        # Only the word label changes; duration and timestamps stay fixed.
        assert before.replace('API','ápi')==(project/'timing.js').read_text()
        print('PASS actual fix-word CLI, backup, unchanged duration and rebuilt word clock',flush=True)
        lines[1]['cam']=True;(project/'script.json').write_text(json.dumps(lines))
        subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=teal:size=270x480:rate=24:duration=4','-c:v','libx264','-pix_fmt','yuv420p',str(project/'flow/L02.mp4')],check=True)
        run(project,'timeline')
        assert len(list((project/'frames/L02').glob('*.jpg')))==96
        assert 'window.CAM_SOURCES = {"L02": "flow/L02.mp4"}' in (project/'timing.js').read_text()
        print('PASS on-camera frame extraction and source metadata',flush=True)
        sys.path.insert(0, str(ROOT/'kit/tools'))
        from env_config import get_chrome
        from playwright.sync_api import sync_playwright
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(project)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with sync_playwright() as play:
                options = {'headless': True}
                if get_chrome(): options['executable_path'] = get_chrome()
                browser = play.chromium.launch(**options)
                page = browser.new_page(viewport={'width':1080,'height':1920})
                page.goto(f'http://127.0.0.1:{server.server_port}/index.html?render=1')
                page.wait_for_function('window.READY || window.BOOT_ERROR', timeout=30000)
                assert not page.evaluate('window.BOOT_ERROR || null'), page.evaluate('window.BOOT_ERROR')
                pixel = page.evaluate("""(async () => {
                    const t=window.TIMING.lines[1].t0+0.5;
                    await window.prepare(t); window.renderAt(t);
                    return Array.from(document.querySelector('#camc').getContext('2d').getImageData(540,960,1,1).data);
                })()""")
                assert pixel[3] == 255 and pixel[1] > 100 and pixel[2] > 100, pixel
                browser.close()
            print('PASS prepared camera frame paints into the real browser canvas', flush=True)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=5)

        failed=subprocess.run([str(ROOT/'bin/wvf'),'fix-word','L02','Meta','Meta','--patch-file',str(patch_file),'--patch-words',str(transcript)],cwd=project,capture_output=True,text=True)
        assert failed.returncode==1 and 'sincronización labial' in failed.stdout
        print('PASS visible-presenter patch refused before generation',flush=True)
    print('Local repair integration passed; temporary projects removed.',flush=True)


if __name__=='__main__':main()
