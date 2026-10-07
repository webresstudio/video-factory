#!/usr/bin/env python3
"""Submit one Flow generation with the @me likeness chip.

usage: flow_submit.py --dur 10 --res 720p --prompt-file p.txt
"""
import argparse, json, time, sys, os
from flowjs import run_js

ap = argparse.ArgumentParser()
ap.add_argument("--dur", default="8")
ap.add_argument("--res", default="720p")
ap.add_argument("--prompt-file", required=True)
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
prompt = open(a.prompt_file, encoding="utf-8").read().strip()


def js(code):
    return run_js(code)

# 1) make sure the "Yo" likeness chip is attached (Ingredients menu -> Avatares -> Yo -> Añadir a petición)
CHIP = "!!document.querySelector('flow-base-prompt-box flow-likeness-ingredient-chip img[alt=\"Imagen de ingrediente de retrato\"]')"
for attempt in range(3):
    if js(CHIP) == "true":
        break
    js("(function(){Array.from(document.querySelectorAll('button')).find(b=>b.getAttribute('aria-label')==='Añadir ingredientes a ventana para peticiones').click(); return 'ok'})()")
    time.sleep(2)
    js("(function(){Array.from(document.querySelectorAll('[role=tab]')).find(e=>/Avatares/.test(e.innerText)).click(); return 'ok'})()")
    time.sleep(2)
    js("(function(){const b=Array.from(document.querySelectorAll('button')).find(b=>b.innerText.trim()==='Añadir a petición' && b.offsetParent); b&&b.click(); return 'ok'})()")
    time.sleep(2)
chip = js(CHIP)
print("chip:", chip)
if chip != "true":
    sys.exit("ABORT: likeness chip missing")

# 2) settings: video / ingredientes / 9:16 / Omni / res / dur / x1
SET_JS = "(function(){const L=%s; const b=Array.from(document.querySelectorAll('.cdk-overlay-container button')).find(e=>e.offsetParent!==null && e.textContent.replace(/^(videocam|image|crop_free|chrome_extension|crop_16_9|crop_9_16)/,'').replace('info','').trim()===L); if(!b) return 'missing '+L; if(b.getAttribute('aria-selected')!=='true') b.click(); return 'ok '+L})()"
TRIG = "(function(){const b=Array.from(document.querySelectorAll('button')).find(b=>(b.getAttribute('aria-label')||'')==='Activador de ajustes'); b.click(); return 'ok'})()"
for attempt in range(3):
    if js(SET_JS % json.dumps("x1")).startswith("ok"):
        break
    js(TRIG)
    time.sleep(1.2)
for label in ["Vídeo", "Ingredientes", "9:16", a.res, f"{a.dur} s", "x1"]:
    r = js(SET_JS % json.dumps(label))
    print(r)
    time.sleep(0.5)
state = js("JSON.stringify({model:(Array.from(document.querySelectorAll('.cdk-overlay-container button')).find(e=>/Omni|Veo/.test(e.textContent))||{}).textContent, cost:(Array.from(document.querySelectorAll('.cdk-overlay-container *')).find(e=>e.children.length===0&&/puntos/.test(e.textContent))||{}).textContent})")
print("state:", state)
js("(function(){const pm=document.querySelector('.ProseMirror'); ['keydown','keyup'].forEach(t=>pm.dispatchEvent(new KeyboardEvent(t,{key:'Escape',code:'Escape',keyCode:27,bubbles:true}))); const bd=document.querySelector('.cdk-overlay-backdrop'); bd&&bd.click(); return 'ok'})()")
time.sleep(0.8)

# 3) type prompt
r = js("(function(){const pm=document.querySelector('.ProseMirror'); pm.focus(); document.execCommand('selectAll'); document.execCommand('delete'); document.execCommand('insertText', false, %s); return pm.innerText.length})()" % json.dumps(prompt))
print("typed chars:", r, "of", len(prompt))
time.sleep(0.8)
label = js("(Array.from(document.querySelectorAll('button')).find(b=>(b.getAttribute('aria-label')||'')==='Activador de ajustes')||{}).innerText")
print("settings label:", label)
if f"{a.res} · {a.dur} s" not in label:
    sys.exit("ABORT: settings mismatch")
if a.dry:
    sys.exit(0)
if js(CHIP) != "true":
    sys.exit("ABORT: likeness chip lost before submit")
# 4) go
result = js("(function(){const b=Array.from(document.querySelectorAll('button')).find(b=>(b.getAttribute('aria-label')||'')==='Iniciar generación'); if(!b) return 'no go'; if(b.disabled) return 'disabled'; b.click(); return 'submitted'})()")
print(result)
if result != "submitted":
    sys.exit("ABORT: Flow no confirmó la generación")
