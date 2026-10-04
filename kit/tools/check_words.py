#!/usr/bin/env python3
"""List every W()/WE() word lookup in engine.js that is missing from the whisper transcripts."""
import json, os, re, unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src = open(os.path.join(ROOT, "engine.js"), encoding="utf-8").read()


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


calls = set()
for m in re.finditer(r'\bWE?\(\s*(L|"L\d\d")\s*,\s*"([^"]+)"\s*(?:,\s*(\d+))?\)', src):
    calls.add((m.group(1), m.group(2), int(m.group(3) or 1), m.start()))

# resolve `const L = "L0x"` scopes: nearest preceding declaration
decls = [(m.start(), m.group(1)) for m in re.finditer(r'const L = "(L\d\d)"', src)]
missing = []
for line, word, n, pos in sorted(calls, key=lambda c: c[3]):
    if line == "L":
        prev = [d for d in decls if d[0] < pos]
        if not prev:
            continue
        line = prev[-1][1]
    else:
        line = line.strip('"')
    p = os.path.join(ROOT, "flow", f"{line}.words.json")
    if not os.path.exists(p):
        missing.append((line, word, n, "NO TRANSCRIPT")); continue
    ws = [norm(w["w"]) for w in json.load(open(p, encoding="utf-8"))]
    if ws.count(norm(word)) < n:
        missing.append((line, word, n, " ".join(ws)))
for m in missing:
    print(m)
print("missing:", len(missing))
