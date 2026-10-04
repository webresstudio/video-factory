#!/usr/bin/env python3
"""Download the Flow batch whose prompt contains a given text.

usage: flow_download.py L02   (matches script.json text of that line)
"""
import json, os, sys, time, zipfile, glob, shutil
sys.path.insert(0, os.path.dirname(__file__))
from flowjs import run_js

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DL = os.path.expanduser("~/Downloads")
LINES = {L["id"]: L for L in json.load(open(os.path.join(ROOT, "script.json"), encoding="utf-8"))}


def status(needle):
    for y in range(0, 40000, 700):
        js = """(function(){const N=%s; const sc=Array.from(document.querySelectorAll('*')).filter(e=>e.scrollHeight>e.clientHeight+200&&getComputedStyle(e).overflowY!=='visible'&&!e.closest('.cdk-overlay-container')).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]; if(sc) sc.scrollTop=%d;
        return JSON.stringify({h: sc?sc.scrollHeight:0});})()""" % (json.dumps(needle), y)
        h = json.loads(run_js(js) or "{}").get("h", 0)
        time.sleep(0.6)
        js2 = """(function(){const N=%s; const tbs=Array.from(document.querySelectorAll('.batch-toolbar')); const out=[];
        tbs.forEach((tb,i)=>{const c=tb.parentElement; const t=c.innerText; if(t.includes(N)) out.push({i, vids:0});});
        return JSON.stringify(out);})()""" % json.dumps(needle)
        res = json.loads(run_js(js2) or "[]")
        if res or y > h:
            return res
    return []


def download(idx, dest):
    for f in glob.glob(os.path.join(DL, "*.zip")) + glob.glob(os.path.join(DL, "*.mp4")):
        if time.time() - os.path.getmtime(f) < 3600 and ("descarga" in os.path.basename(f).lower() or "download" in os.path.basename(f).lower()):
            os.remove(f)
    before = set(os.listdir(DL))
    r = run_js("""(function(){const tb=document.querySelectorAll('.batch-toolbar')[%d]; const b=tb.querySelector('button[aria-label="Descargar lote"]'); b.scrollIntoView({block:'center'}); b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window})); return 'clicked'})()""" % idx)
    print(r)
    for _ in range(80):
        time.sleep(0.5)
        new = [f for f in set(os.listdir(DL)) - before if not f.endswith(".crdownload")]
        if new:
            time.sleep(1.0)
            p = os.path.join(DL, new[0])
            os.makedirs(dest, exist_ok=True)
            if p.endswith(".zip"):
                with zipfile.ZipFile(p) as z:
                    z.extractall(dest)
                    print("extracted", z.namelist())
                os.remove(p)
            else:
                shutil.move(p, os.path.join(dest, os.path.basename(p)))
                print("moved", p)
            return True
    print("timeout")
    return False


if __name__ == "__main__":
    lid = sys.argv[1]
    needle = sys.argv[sys.argv.index("--needle") + 1] if "--needle" in sys.argv else LINES[lid]["text"][:60]
    st = status(needle)
    print(lid, st)
    if not st:
        sys.exit(2)
    ready = st
    if "--status" in sys.argv:
        sys.exit(0)
    if ready:
        download(ready[0]["i"], os.path.join(ROOT, "flow", lid))
