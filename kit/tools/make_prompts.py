#!/usr/bin/env python3
"""Writes prompts/Lxx.txt for every narration line (Flow @me, his own voice)."""
import json, os
from env_config import get_project_root

ROOT = get_project_root()
LINES = json.load(open(os.path.join(ROOT, "script.json"), encoding="utf-8"))

BASE = (
    'Vertical 9:16 video of me (the man in the likeness ingredient, using my own recorded voice) facing the camera, '
    'medium close-up, locked-off tripod shot. Dark graphite studio background, very soft out-of-focus teal rim light behind him, '
    'calm low-contrast backdrop with no objects and no text. {act} '
    'He speaks in Latin American Spanish, clear and energetic, with natural pacing, starting to speak immediately:\n"{text}"\n'
    'No music, no subtitles, no on-screen text.'
)

for L in LINES:
    p = BASE.format(act=L.get("acting", "Natural confident expression."), text=L.get("spoken_text", L["text"]))
    os.makedirs(os.path.join(ROOT, "prompts"), exist_ok=True)
    open(os.path.join(ROOT, "prompts", f"{L['id']}.txt"), "w", encoding="utf-8").write(p + "\n")
    print(L["id"], L["dur"], len(L["text"].split()), "words")
