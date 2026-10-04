#!/usr/bin/env python3
"""Export window.CUES + DURATION from the page into audio/cues.json (single source of truth for the SFX mix)."""
import json, os
from playwright.sync_api import sync_playwright

from env_config import get_chrome

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
with sync_playwright() as p:
    launch_args = {"headless": True}
    ch = get_chrome()
    if ch:
        launch_args["executable_path"] = ch
    b = p.chromium.launch(**launch_args)
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.goto("http://127.0.0.1:4391/index.html?render=1")
    pg.wait_for_function("window.READY === true || window.BOOT_ERROR", timeout=20000)
    d = pg.evaluate("({duration: window.DURATION, cues: window.CUES, err: window.BOOT_ERROR || null})")
    b.close()
if d["err"]:
    raise SystemExit(d["err"])
bad = [c for c in d["cues"] if c[0] is None or c[0] != c[0]]
print("cues:", len(d["cues"]), "duration:", d["duration"], "bad:", bad[:5])
os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
json.dump({"duration": d["duration"], "cues": d["cues"]}, open(os.path.join(ROOT, "audio", "cues.json"), "w"))
