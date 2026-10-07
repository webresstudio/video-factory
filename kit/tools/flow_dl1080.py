#!/usr/bin/env python3
"""Download the 1080p (Flow-upscaled) version of a line's clip.
usage: flow_dl1080.py L02 [--take N]   (N = which match, 0 = newest)
"""
import json, os, sys, time, shutil
from flowjs import run_js
from flow_download import status, LINES, ROOT, DL

lid = sys.argv[1]
take = int(sys.argv[sys.argv.index("--take") + 1]) if "--take" in sys.argv else 0
st = status(LINES[lid]["text"][:60])
print(st)
idx = st[take]["i"]
run_js("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
before = set(os.listdir(DL))
print(run_js("""(function(){const tb=document.querySelectorAll('.batch-toolbar')[%d]; const row=tb.parentElement.parentElement; row.scrollIntoView({block:'center'}); const b=Array.from(row.querySelectorAll('button')).find(b=>b.getAttribute('aria-label')==='Más opciones'); b.dispatchEvent(new MouseEvent('click',{bubbles:true})); return 'menu'})()""" % idx))
time.sleep(1.2)
print(run_js("""(function(){const b=Array.from(document.querySelectorAll('.cdk-overlay-container [role=menuitem]')).find(e=>e.innerText.includes('Descargar')); b.click(); return 'sub'})()"""))
time.sleep(1.2)
print(run_js("""(function(){const b=Array.from(document.querySelectorAll('.cdk-overlay-container [role=menuitem], .cdk-overlay-container button')).find(e=>e.innerText.includes('1080p')); if(!b) return 'no 1080'; b.click(); return '1080 clicked'})()"""))
for _ in range(360):
    time.sleep(1)
    new = [f for f in set(os.listdir(DL)) - before if not f.endswith(".crdownload") and f.endswith(".mp4")]
    if new:
        time.sleep(1.5)
        dst = os.path.join(ROOT, "flow", f"{lid}_1080.mp4")
        shutil.move(os.path.join(DL, new[0]), dst)
        print("saved", dst)
        sys.exit(0)
print("timeout")
