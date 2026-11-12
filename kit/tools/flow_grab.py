#!/usr/bin/env python3
"""Descarga de Flow la toma cuyo prompt empieza con una etiqueta, con la interfaz de cuadrícula (nov. 2026).

usage: flow_grab.py --tag "[NT1108 L01 R1]" --line L01 --take a [--res 720p] [--scan 16]

--res: la opción del submenú «Descargar» (p. ej. 360p = tamaño original de una toma 360p,
       720p = «Resolución mejorada» de una toma 360p, o tamaño original de una 720p; 1080p = mejorada de una 720p).
Identifica la toma con «Reutilizar petición» (lee el prompt en la caja) para no bajar la equivocada.
"""
import argparse, json, os, shutil, sys, time
from flowjs import run_js
from env_config import get_project_root

DL = os.path.expanduser("~/Downloads")
CTX = ("(function(){const t=document.querySelectorAll('flow-grid-tile-container')[%d]; if(!t) return 'none';"
       "t.scrollIntoView({block:'center'}); const r=t.getBoundingClientRect();"
       "t.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,view:window,clientX:r.x+40,clientY:r.y+60,button:2}));"
       "return 'ctx'})()")
ITEM = ("(function(){const N=%s; const o=Array.from(document.querySelectorAll('.cdk-overlay-container [role=menuitem]'))"
        ".find(e=>e.offsetParent!==null && e.innerText.split('\\n').map(s=>s.trim()).some(s=>s===N||s.startsWith(N)));"
        "if(!o) return 'noitem'; o.click(); return 'ok'})()")
ESC = "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); 'esc'"
BOX = "(document.querySelector('.ProseMirror')||{}).innerText||''"


def esc():
    run_js(ESC); time.sleep(0.3); run_js(ESC); time.sleep(0.3)


def find_tile(tag, scan):
    for i in range(scan):
        esc()
        if run_js(CTX % i) != "ctx":
            return None
        time.sleep(0.9)
        if run_js(ITEM % json.dumps("Reutilizar petición")) != "ok":
            continue
        time.sleep(1.0)
        head = run_js(BOX)[:len(tag) + 2]
        print(f"  cuadro {i}: {head[:40]!r}")
        if head.startswith(tag):
            return i
    return None


def download(i, res, dest):
    esc()
    before = set(os.listdir(DL))
    run_js(CTX % i); time.sleep(0.9)
    if run_js(ITEM % json.dumps("Descargar")) != "ok":
        sys.exit("No encontré «Descargar».")
    time.sleep(1.2)
    opts = run_js("JSON.stringify(Array.from(document.querySelectorAll('.cdk-overlay-container [role=menuitem]')).map(e=>e.innerText.replace(/\\n/g,' | ')).filter(t=>/\\d+p/.test(t)))")
    print("  opciones:", opts)
    if run_js(ITEM % json.dumps(res)) != "ok":
        sys.exit(f"No hay opción {res}.")
    for _ in range(600):
        time.sleep(1)
        new = [f for f in set(os.listdir(DL)) - before
               if f.lower().endswith(".mp4") and not f.endswith(".crdownload")]
        if new:
            time.sleep(1.5)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(os.path.join(DL, new[0]), dest)
            print("  guardado:", dest)
            return True
    print("  timeout")
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--line", required=True)
    ap.add_argument("--take", required=True)
    ap.add_argument("--res", default="720p")
    ap.add_argument("--scan", type=int, default=16)
    a = ap.parse_args()
    root = get_project_root()
    i = find_tile(a.tag, a.scan)
    if i is None:
        sys.exit(f"No encontré la toma {a.tag} en los primeros {a.scan} cuadros.")
    dest = os.path.join(root, "flow", a.line, f"{a.line}_{a.take}_{a.res}.mp4")
    ok = download(i, a.res, dest)
    esc()
    sys.exit(0 if ok else 1)
