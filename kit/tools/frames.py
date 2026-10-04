#!/usr/bin/env python3
"""Captura frames sueltos del HTML y arma una hoja de contactos para revisión.
Uso: python frames.py 1.0 3.5 7.9 ...   (o sin args para el set por defecto)
"""
import os
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(HERE, "check")
os.makedirs(OUT, exist_ok=True)
URL = "http://127.0.0.1:4391/index.html?render=1"
DEFAULT = [0.4, 3.5, 6.5, 7.75, 11.5, 16.5, 17.0, 20.5, 24.4, 27.5, 31.1, 35.0, 39.1, 39.5, 43.0, 46.5, 46.8, 51.0, 54.9, 58.5, 61.5, 66.0, 71.6, 72.2, 75.0, 78.5]
from env_config import get_chrome

with sync_playwright() as p:
    launch_args = {
        "headless": True,
        "args": ["--use-angle=metal", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--force-color-profile=srgb", "--autoplay-policy=no-user-gesture-required"]
    }
    ch = get_chrome()
    if ch:
        launch_args["executable_path"] = ch
    b = p.chromium.launch(**launch_args)
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.on("console", lambda m: print("console:", m.text) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.goto(URL)
    pg.wait_for_function("window.READY === true || window.BOOT_ERROR", timeout=20000)
    err = pg.evaluate("window.BOOT_ERROR || null")
    if err:
        print("BOOT_ERROR", err); sys.exit(1)
    files = []
    for t in times:
        pg.evaluate(f"(async () => {{ await window.prepare({t}); window.renderAt({t}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); }})()")
        f = os.path.join(OUT, f"f_{t:06.2f}.png")
        pg.screenshot(path=f)
        files.append((t, f))
    b.close()

# contact sheet: 4 por fila a 270x480
cols = 4
w, h = 360, 640
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
for i, (t, f) in enumerate(files):
    im = Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS)
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(os.path.join(OUT, "sheet.jpg"), quality=88)
print("ok", len(files))
