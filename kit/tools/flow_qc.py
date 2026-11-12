#!/usr/bin/env python3
"""Chequeador de prompts y tomas de Flow + bitácora de créditos.

Objetivo: gastar menos créditos aprendiendo qué prompts le funcionan a Flow.

Subcomandos (correr siempre con `wvf tool flow_qc ...` desde la carpeta del proyecto):

  lint   --line L01 --prompt prompts/L01_r1.txt
         Revisa el prompt ANTES de enviarlo. Si hay un FAIL, no se envía.

  send   --line L01 --prompt prompts/L01_r1.txt [--res 720p --dur 8] [--force]
         Corre lint, envía a Flow con flow_submit.py, lee el costo que muestra Flow
         y lo anota en la bitácora.

  check  --line L01 --clip flow/L01/archivo.mp4 [--prompt prompts/L01_r1.txt]
         Revisa la toma generada: transcribe, compara palabra por palabra contra
         script.json (normalizando números y nombres fonéticos), mide arranque, ritmo,
         corte final, palabras repetidas y texto dibujado en el video (OCR).
         Da un veredicto y sugerencias concretas para el siguiente prompt.

  review --line L01 --take a --accent ok|mal --use si|no [--note "..."]
         Anota la escucha de William (el acento solo lo valida él).

  report
         Resume la bitácora: créditos gastados, tomas por línea, tasa de aciertos
         por plantilla de prompt y defectos más frecuentes.

  backfill --project <carpeta>
         Re-evalúa tomas viejas (formato flow/Lxx/*.json con "palabras") con el
         normalizador nuevo para medir cuántas se rechazaron por error de formato.

Bitácora compartida: video-factory/research/flow_ledger.jsonl
"""
import argparse
import datetime as dt
import difflib
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(PKG, "research", "flow_ledger.jsonl")
LEARN_MD = os.path.join(PKG, "research", "flow_prompt_learnings.md")

# ---------------------------------------------------------------- números en español
_U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
      "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho",
      "diecinueve", "veinte", "veintiuno", "veintidos", "veintitres", "veinticuatro", "veinticinco",
      "veintiseis", "veintisiete", "veintiocho", "veintinueve"]
_T = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_H = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
      6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _lt1000(n):
    if n == 100:
        return "cien"
    out = []
    h, r = divmod(n, 100)
    if h:
        out.append(_H[h])
    if r:
        if r < 30:
            out.append(_U[r])
        else:
            t, u = divmod(r, 10)
            out.append(_T[t] + (" y " + _U[u] if u else ""))
    return " ".join(out)


def num_es(n):
    """Entero a palabras en español (sin acentos, para comparar)."""
    if n == 0:
        return "cero"
    out = []
    mm, rest = divmod(n, 1_000_000)
    if mm:
        out.append("un millon" if mm == 1 else num_es(mm) + " millones")
    th, rest = divmod(rest, 1000)
    if th:
        out.append("mil" if th == 1 else _lt1000(th) + " mil")
    if rest:
        out.append(_lt1000(rest))
    return " ".join(out)


def _expand_numbers(text):
    text = re.sub(r"(\d)\s+([.,]\d)", r"\1\2", text)   # Whisper escribe "6 .300" o "4 .8"
    def pct(m):
        return f" {m.group(1)} por ciento "
    text = re.sub(r"(\d[\d.,]*)\s*%", pct, text)

    def repl(m):
        s = m.group(0)
        if re.fullmatch(r"\d{1,3}([., ]\d{3})+", s):           # 1,005 / 1.005 / 3 000 -> mil cinco
            return " " + num_es(int(re.sub(r"[., ]", "", s))) + " "
        if re.fullmatch(r"\d+[.,]\d+", s):                     # 4.8 -> cuatro punto ocho
            a, b = re.split(r"[.,]", s)
            sep = "punto" if "." in s else "coma"
            return f" {num_es(int(a))} {sep} {' '.join(num_es(int(c)) for c in b)} "
        return " " + num_es(int(re.sub(r"\D", "", s))) + " "
    return re.sub(r"\d{1,3}(?: \d{3})+(?!\d)|\d[\d.,]*\d|\d", repl, text)


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# Alias fonéticos: lo que escribimos para que Flow lo pronuncie bien vs. lo que Whisper transcribe.
DEFAULT_ALIASES = {
    "chat yi pi ti": "chatgpt", "chat ye pe te": "chatgpt", "chat ge pe te": "chatgpt",
    "chat gpt": "chatgpt", "chatgpt": "chatgpt", "chat g p t": "chatgpt",
    "gugol": "google", "google": "google",
    "yutub": "youtube", "youtube": "youtube", "you tube": "youtube",
    "yio surch": "geosurge", "yio-surch": "geosurge", "geo surge": "geosurge", "geosurge": "geosurge",
    "geo search": "geosurge", "yio search": "geosurge",
    "i a": "ia", "i-a": "ia", "ia": "ia",
    "tec": "tech", "tech": "tech",
    # marcas que ya salieron en Noticias Tech (escritura fonética → como lo escribe Whisper)
    "yemini": "gemini", "clod": "claude", "antropic": "anthropic", "bainans": "binance",
    "redit": "reddit", "crom": "chrome", "grei suan": "grey swan", "grey swan": "grey swan",
    "eliptic": "elliptic", "bitguet": "bitget", "bitket": "bitget", "jaquearon": "hackearon",
    "apol": "apple", "esquils": "skills",
    "gio surge": "geosurge", "gio surch": "geosurge", "yo surge": "geosurge", "yio surge": "geosurge",
    "un": "uno", "una": "uno",
}


def load_aliases(root):
    al = dict(DEFAULT_ALIASES)
    p = os.path.join(root, "qc_aliases.json")
    if os.path.isfile(p):
        al.update({_strip_accents(k.lower()): v for k, v in json.load(open(p, encoding="utf-8")).items()})
    return al


def normalize(text, aliases):
    t = _strip_accents(text.lower())
    t = t.replace("-", " ")
    t = _expand_numbers(t)
    t = re.sub(r"[^a-z0-9ñ ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # alias de varias palabras primero
    for k in sorted(aliases, key=lambda x: -len(x.split())):
        kk = re.sub(r"[^a-z0-9ñ ]+", " ", _strip_accents(k.lower())).strip()
        if " " in kk:
            t = re.sub(rf"\b{re.escape(kk)}\b", aliases[k], t)
    toks = [aliases.get(w, w) for w in t.split()]
    return toks


def align(expected, got):
    sm = difflib.SequenceMatcher(None, expected, got, autojunk=False)
    missing, extra, subs = [], [], []
    S = D = I = 0
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "replace":
            subs.append((" ".join(expected[a0:a1]), " ".join(got[b0:b1])))
            n, m = a1 - a0, b1 - b0
            S += min(n, m)
            D += max(0, n - m)
            I += max(0, m - n)
        elif op == "delete":
            missing.append(" ".join(expected[a0:a1]))
            D += a1 - a0
        elif op == "insert":
            extra.append(" ".join(got[b0:b1]))
            I += b1 - b0
    # «complétalo» vs «completa lo»: mismas letras, solo cambia el espacio → no es error de Flow.
    same = [(a, b) for a, b in subs if a.replace(" ", "") == b.replace(" ", "")]
    for a, b in same:
        subs.remove((a, b))
        n, m = len(a.split()), len(b.split())
        S -= min(n, m); D -= max(0, n - m); I -= max(0, m - n)
    wer = (S + D + I) / max(1, len(expected))
    return round(wer, 3), missing, extra, subs


# ---------------------------------------------------------------- utilidades de proyecto
def project_root():
    return os.getcwd()


def load_line(root, line):
    with open(os.path.join(root, "script.json"), encoding="utf-8") as fh:
        lines = json.load(fh)
    for L in lines:
        if L["id"] == line:
            return L
    sys.exit(f"No encontré {line} en script.json")


def ledger_append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rec.setdefault("ts", dt.datetime.now().isoformat(timespec="seconds"))
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def ledger_read():
    if not os.path.isfile(LEDGER):
        return []
    return [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]


def dialogue_span(prompt):
    m = re.search(r"«([^»]+)»", prompt)
    if m:
        return m.group(1).strip(), m.start(0), m.end(0)
    m2 = re.search(r"(?:Spanish|Exact dialogue)[^\"«:\n]*:\s*\"([^\"]+)\"", prompt, flags=re.I)
    if m2:
        q_start = prompt.find('"', m2.start(0))
        return m2.group(1).strip(), q_start, m2.end(0)
    return None, len(prompt), len(prompt)


def dialogue_of(prompt):
    dlg, _, _ = dialogue_span(prompt)
    return dlg


def detect_prompt_camera(stage_text):
    explicit = re.search(r"\bCam(?:era)?\s*([ABCD])\b", stage_text, flags=re.I)
    if explicit:
        return explicit.group(1).upper()
    low = stage_text.lower()
    if "low-angle" in low or "low angle" in low or "25-degree" in low or "upward tilt" in low:
        return "B"
    if "three-quarter" in low or "35 degrees" in low or "35-degree" in low:
        return "C"
    if "intimate close-up" in low or "tight close-up" in low:
        return "D"
    if "frontal" in low or "eye level" in low:
        return "A"
    return ""


def template_id(prompt):
    """Huella de la plantilla: el prompt sin etiqueta, diálogo ni actuación."""
    t = re.sub(r"^\[[^\]]+\]\s*", "", prompt.strip())
    t = re.sub(r"«[^»]+»", "«DIALOGO»", t)
    t = re.sub(r"ACTING:.*?(?=(Brisk|Exact dialogue|$))", "ACTING:{}", t, flags=re.S)
    return hashlib.sha1(t.encode()).hexdigest()[:8]


def exp_of(prompt):
    """Experimento = la parte Rn de la etiqueta [PROY Lxx Rn...] (sin la letra de variante)."""
    m = re.match(r"^\[[A-Z0-9]+ L\d{2}[A-Z0-9_]* (R\d+)", prompt.strip())
    return m.group(1) if m else "?"


def prompt_id(prompt):
    return hashlib.sha1(prompt.strip().encode()).hexdigest()[:8]


# ---------------------------------------------------------------- LINT (antes de gastar)
REQUIRED = [
    ("likeness", r"\bYo avatar\b|likeness|@Yo\b", "Falta pedir el avatar «Yo» (@Yo / likeness)."),
    ("acento", r"GUATEMALAN|Guatemalan", "Falta el bloque de acento neutro de Guatemala."),
    ("encuadre", r"Camera|camera|shot\b", "Falta el encuadre y la cámara."),
    ("dialogo", r"(?:Exact dialogue|Spanish)[^«\":\n]*:\s*[«\"]", "Falta el diálogo final delimitado ('Exact dialogue: «...»' o 'Spanish: \"...\"')."),
    ("arranque", r"Start speaking immediately|Speaking right away", "Falta 'Start speaking immediately' o 'Speaking right away' (arranque en 0 s)."),
    ("sin_texto", r"NO text|no on-screen text", "Falta el bloque anti-texto (Flow dibuja letras si no se prohíbe)."),
    ("formato", r"(?:6|8) seconds,\s*vertical 9:16|vertical 9:16", "Falta 'vertical 9:16'."),
]
RISKY_WORDS = [  # palabras que invitan a Flow a dibujar texto
    r"\bsign\b", r"\btitle\b", r"\bcaption that\b", r"\bwritten\b", r"\bscreen showing\b", r"\blogo of\b",
]
FORBIDDEN_BODY_WORDS = [  # descriptores que deforman torso/hombros del avatar @Yo (detectado en L01_b)
    r"\b200\s*lb\b", r"\b200lb\b", r"\brobust\s+exercised\b", r"\bmuscular\s+build\b", r"\bbodybuilder\b",
]


def lint(root, line, prompt_path, dur=None, allow_override=False):
    with open(prompt_path, encoding="utf-8") as fh:
        prompt = fh.read().strip()
    L = load_line(root, line)
    expected = L.get("spoken_text", L["text"]).strip()
    res = {"line": line, "prompt": os.path.relpath(prompt_path, root), "fails": [], "warns": [], "info": {}}
    dlg, dlg_start, _ = dialogue_span(prompt)
    stage_block = prompt[:dlg_start]

    # 1. Cero comillas simples o dobles dentro del bloque escénico en inglés (evita subtítulos quemados)
    stage_double_quotes = re.findall(r"\"([^\"]*)\"", stage_block)
    stage_single_quotes = re.findall(r"(?<![A-Za-z])'([^']+)'", stage_block)
    if stage_double_quotes or stage_single_quotes:
        found_q = stage_double_quotes + stage_single_quotes
        res["fails"].append(
            f"Comillas detectadas en el bloque escénico en inglés ({found_q}): Flow las dibuja como subtítulos "
            "quemados en la imagen. Deja comillas únicamente alrededor del diálogo final en español."
        )

    # 2. Prohibir descriptores físicos exagerados
    for bad_body in FORBIDDEN_BODY_WORDS:
        if re.search(bad_body, stage_block, flags=re.I):
            res["fails"].append(
                f"Descriptor corporal exagerado prohibido ({bad_body}): confía solo en @Yo para no deformar hombros ni torso."
            )

    if dlg is None:
        res["fails"].append("No hay diálogo final entre « » o \" \".")
    else:
        if re.sub(r"\s+", " ", dlg) != re.sub(r"\s+", " ", expected):
            res["fails"].append(f"El diálogo no es idéntico a script.json.\n    prompt: {dlg}\n    script: {expected}")
        words = dlg.replace("...", " ").split()
        n = len(words)
        rec_dur = 6 if n <= 18 else 8
        res["info"]["palabras"] = n
        res["info"]["dur_recomendada"] = rec_dur
        eff_dur = int(dur) if str(dur or "").isdigit() else rec_dur

        if eff_dur == 6 and n > 22:
            msg = f"{n} palabras para clip de 6 s: atropellará el cierre (>4.5 pal/s). Usa --dur 8 o acorta a <=18."
            (res["warns"] if allow_override else res["fails"]).append(msg)
        elif eff_dur == 6 and n > 18:
            res["warns"].append(f"{n} palabras en clip de 6 s: considera --dur 8 (Pulso Extendido) para cadencia holgada.")
        elif n > 28:
            res["fails"].append(f"{n} palabras: excede el tope físico de 8 s a 1.0x.")
        elif n > 24:
            msg = f"{n} palabras: supera el rango abordable de 19–24 pal. para 8 s (usa --allow-override si es intencional)."
            (res["warns"] if allow_override else res["fails"]).append(msg)

        if re.search(r"\d", dlg):
            res["fails"].append("Hay dígitos en el diálogo: escribe los números en letras.")
        acr = [w for w in re.findall(r"\b[A-ZÁÉÍÓÚ]{2,}\b", dlg)]
        if acr:
            res["fails"].append(f"Siglas en mayúscula {acr}: Flow las deletrea. Escríbelas fonéticas (p. ej. 'i-a').")
        for raw in ["ChatGPT", "Google", "YouTube", "GeoSurge", "Instagram", "WhatsApp", "Facebook"]:
            if raw in dlg:
                res["warns"].append(f"'{raw}' en inglés: considera la forma fonética (Chat yi pi tí, Gúgol, Yutub...).")
    for key, pat, msg in REQUIRED:
        if not re.search(pat, prompt, flags=re.M):
            res["fails"].append(msg)
    for pat in RISKY_WORDS:
        if re.search(pat, stage_block, flags=re.I):
            res["warns"].append(f"Palabra de riesgo de texto dibujado: {pat}")

    cam_angle = detect_prompt_camera(stage_block)
    res["info"]["camara"] = cam_angle or "sin_etiqueta"
    m_line = re.match(r"^L(\d{2})$", line)
    if cam_angle and m_line and int(m_line.group(1)) > 1:
        prev_line = f"L{int(m_line.group(1)) - 1:02d}"
        prev_candidates = sorted(glob.glob(os.path.join(root, "prompts", f"{prev_line}*.txt")))
        if prev_candidates:
            with open(prev_candidates[-1], encoding="utf-8") as fh:
                prev_raw = fh.read()
            _, prev_start, _ = dialogue_span(prev_raw)
            prev_cam = detect_prompt_camera(prev_raw[:prev_start])
            if prev_cam == cam_angle:
                res["warns"].append(
                    f"Ángulo de cámara repetido ({cam_angle}) respecto a {prev_line}: alterna Cam A/B/C/D para sostener retención."
                )

    res["info"]["caracteres"] = len(prompt)
    res["info"]["senales_entre_comillas"] = len(stage_double_quotes) + len(stage_single_quotes)
    res["info"]["exp"] = exp_of(prompt)
    res["info"]["template_id"] = template_id(prompt)
    res["info"]["prompt_id"] = prompt_id(prompt)
    res["verdict"] = "FAIL" if res["fails"] else ("WARN" if res["warns"] else "PASS")
    return res


def print_lint(r):
    print(f"\n== LINT {r['line']} · {r['prompt']} → {r['verdict']}")
    for f in r["fails"]:
        print("  ✗", f)
    for w in r["warns"]:
        print("  !", w)
    print("  ·", json.dumps(r["info"], ensure_ascii=False))


# ---------------------------------------------------------------- SEND
def next_take(project, line):
    used = [r.get("take") for r in ledger_read() if r.get("type") == "submit"
            and r.get("project") == project and r.get("line") == line]
    root = project_root()
    on_disk = [os.path.basename(p) for p in glob.glob(os.path.join(root, "flow", line, f"{line}_*.mp4"))]
    letters = set(filter(None, used)) | {re.sub(rf"^{line}_([a-z]).*", r"\1", f) for f in on_disk}
    for c in "abcdefghijklmnopqrstuvwxyz":
        if c not in letters:
            return c
    return "z"


def pick_model(name):
    """Elige el modelo en el panel de ajustes de Flow (no genera nada)."""
    sys.path.insert(0, HERE)
    import time
    from flowjs import run_js
    CLICK = "['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>b.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));"
    OPEN = ("(function(){const ov=document.querySelector('.cdk-overlay-container'); if(ov && /Ingredientes/.test(ov.innerText)) return 'open';"
            "const b=Array.from(document.querySelectorAll('button')).find(b=>(b.getAttribute('aria-label')||'')==='Activador de ajustes');"
            "if(!b) return 'notrig'; " + CLICK + " return 'clicked'})()")
    DROP = ("(function(){const b=Array.from(document.querySelectorAll('.cdk-overlay-container button')).find(e=>e.offsetParent!==null&&/Omni|Veo/.test(e.textContent)&&/arrow_drop_down/.test(e.textContent));"
            "if(!b) return 'nodrop'; b.click(); return 'dropped'})()")
    PICK = ("(function(){const N=%s; const o=Array.from(document.querySelectorAll('.cdk-overlay-container [role=menuitem]'))"
            ".find(e=>e.offsetParent!==null && e.innerText.split('\\n').map(s=>s.trim()).includes(N)); if(!o) return 'noopt'; o.click(); return 'picked'})()")
    CUR = "(Array.from(document.querySelectorAll('.cdk-overlay-container button')).find(e=>/Omni|Veo/.test(e.textContent))||{}).textContent"
    cur = ""
    for _ in range(3):
        if run_js(OPEN) != "open":
            time.sleep(1.2)
        r = run_js(PICK % json.dumps(name))
        if r == "noopt":
            run_js(DROP)
            time.sleep(1.0)
            r = run_js(PICK % json.dumps(name))
        time.sleep(1.2)
        if run_js(OPEN) != "open":
            time.sleep(1.2)
        cur = (run_js(CUR) or "").replace("arrow_drop_down", "").strip()
        if cur == name:
            break
    print(f"modelo: {cur}")
    if cur != name:
        sys.exit(f"ABORTADO: no pude seleccionar el modelo {name} (quedó {cur}). No se gastaron créditos.")


def send(root, line, prompt_path, res_, dur, force, model=None):
    r = lint(root, line, prompt_path, dur=dur, allow_override=force)
    print_lint(r)
    if r["verdict"] == "FAIL" and not force:
        sys.exit("ABORTADO: el prompt no pasó el lint. No se gastaron créditos.")
    if model:
        pick_model(model)
    py = sys.executable
    proc = subprocess.run([py, os.path.join(HERE, "flow_submit.py"), "--dur", str(dur), "--res", res_,
                           "--prompt-file", prompt_path], capture_output=True, text=True, cwd=root)
    out = proc.stdout + proc.stderr
    print(out)
    state = {}
    m = re.search(r"state:\s*(\{.*\})", out)
    if m:
        try:
            state = json.loads(m.group(1))
        except Exception:
            pass
    credits = None
    if state.get("cost"):
        n = re.search(r"(\d[\d.,]*)", state["cost"])
        credits = int(re.sub(r"\D", "", n.group(1))) if n else None
    ok = "submitted" in out
    project = os.path.basename(root)
    take = next_take(project, line) if ok else None
    prompt = open(prompt_path, encoding="utf-8").read().strip()
    ledger_append({"type": "submit", "project": project, "line": line, "take": take, "ok": ok,
                   "prompt_file": os.path.relpath(prompt_path, root), "prompt_id": prompt_id(prompt),
                   "template_id": template_id(prompt), "exp": exp_of(prompt), "chars": len(prompt),
                   "quoted_cues": len(re.findall(r"'([^']{2,60})'", prompt)), "res": res_, "dur": dur,
                   "model": (state.get("model") or "").replace("arrow_drop_down", "").strip(), "cost_text": state.get("cost"),
                   "credits": credits, "lint": r["verdict"]})
    print(f"\nBitácora: {line} toma '{take}' · créditos={credits} · enviado={ok}")
    if not ok:
        sys.exit(1)


# ---------------------------------------------------------------- CHECK (después de generar)
def transcribe(wav):
    sys.path.insert(0, HERE)
    from whisper_compat import patch_av_open
    patch_av_open()
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    # Sin initial_prompt: el 9 nov. sesgarlo con «i-a» hizo que Whisper escribiera «ida» donde Flow decía «IA» bien.
    segs, _ = m.transcribe(wav, language="es", word_timestamps=True, vad_filter=False)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
    return words


def ocr_frames(clip, outdir, step=0.5):
    """Busca texto dibujado (subtítulos quemados) cada medio segundo con tesseract."""
    import tempfile
    tmp = tempfile.mkdtemp(dir=outdir)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-vf",
                    f"fps=1/{step},scale=iw*2:ih*2,format=gray", os.path.join(tmp, "%03d.png")])
    hits = []
    for k, png in enumerate(sorted(glob.glob(os.path.join(tmp, "*.png")))):
        t = round(k * step, 1)
        tsv = subprocess.run(["tesseract", png, "-", "--psm", "11", "-l", "spa+eng", "tsv"],
                             capture_output=True, text=True).stdout
        if not tsv:
            tsv = subprocess.run(["tesseract", png, "-", "--psm", "11", "tsv"], capture_output=True, text=True).stdout
        for row in tsv.splitlines()[1:]:
            c = row.split("\t")
            if len(c) >= 12:
                try:
                    conf = float(c[10])
                except ValueError:
                    continue
                word = c[11].strip()
                letters = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúñÑ]", "", word)
                if conf >= 60 and len(letters) >= 2 and letters.lower() not in {"ll", "ii", "il", "li"}:
                    hits.append({"t": t, "word": word, "conf": round(conf)})
        os.remove(png)
    os.rmdir(tmp)
    return hits


SUGGEST = {
    "FALTAN_PALABRAS": "Flow omitió palabras: revisa si son nombres o cifras y escríbelos fonéticos; acorta a ≤20 palabras.",
    "SOBRAN_PALABRAS": "Flow añadió palabras: quita señales de actuación entre comillas que no estén en el diálogo y refuerza 'Say only this exact dialogue'.",
    "CORTADO": "La frase no terminó en 8 s: recorta 2–3 palabras o quita pausas pedidas en la actuación.",
    "ARRANQUE_TARDE": "Arrancó después de 1 s: se recorta en edición, pero le quita tiempo a la frase. Prueba 'speaking from the very first frame, no silent intro'.",
    "PALABRA_REPETIDA": "Repitió una palabra: evita repeticiones cercanas en el diálogo y pausas dramáticas.",
    "TEXTO_EN_IMAGEN": "Flow dibujó texto (subtítulos quemados): la toma no sirve. Hipótesis: las palabras entre comillas en la actuación se convierten en subtítulos; descríbelas sin citarlas.",
    "MUY_RAPIDO": "Habla muy rápido (>3.8 pal/s): recorta texto en vez de dejar que acelere.",
    "MUY_LENTO": "Habla lento (<2.3 pal/s): la toma tendrá aire muerto; puede servir si el corte lo absorbe.",
}


def contact_sheet(clip, out_jpg, every=1.0):
    """Hoja de contacto con los tiempos en una franja inferior (no tapa el cuadro)."""
    import tempfile
    from PIL import Image, ImageDraw, ImageFont
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-vf", f"fps=1/{every},scale=240:-1",
                    os.path.join(tmp, "%03d.jpg")])
    frames = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    if not frames:
        return
    ims = [Image.open(f) for f in frames]
    w, h = ims[0].size
    strip = 26
    sheet = Image.new("RGB", (w * len(ims), h + strip), "black")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for i, im in enumerate(ims):
        sheet.paste(im, (i * w, 0))
        d.text((i * w + 8, h + 4), f"{i * every:.1f} s", fill="white", font=font)
    sheet.save(out_jpg, quality=88)
    for f in frames:
        os.remove(f)
    os.rmdir(tmp)


def check(root, line, clip, prompt_path=None, take=None, record=True):
    L = load_line(root, line)
    aliases = load_aliases(root)
    expected_txt = L.get("spoken_text", L["text"])
    exp = normalize(expected_txt, aliases)
    outdir = os.path.join(root, "check", "flow_qc")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(clip))[0]
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                       "stream=codec_type,width,height:format=duration", "-of", "json", clip],
                                      capture_output=True, text=True).stdout or "{}")
    dur = float(probe.get("format", {}).get("duration", 0) or 0)
    wav = os.path.join(outdir, base + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    words = transcribe(wav)
    os.remove(wav)
    got_txt = " ".join(w["w"] for w in words)
    got = normalize(got_txt, aliases)
    wer, missing, extra, subs = align(exp, got)
    defects = []
    if missing or subs:
        defects.append("FALTAN_PALABRAS")
    if extra or subs:
        defects.append("SOBRAN_PALABRAS")
    first = words[0]["s"] if words else None
    last = words[-1]["e"] if words else None
    if first is not None and first > 1.0:
        defects.append("ARRANQUE_TARDE")
    tail_ok = exp[-2:] == got[-2:] if len(got) >= 2 else False
    if not tail_ok:
        defects.append("CORTADO")
    reps = [got[i] for i in range(1, len(got)) if got[i] == got[i - 1]
            and not any(exp[j] == exp[j - 1] == got[i] for j in range(1, len(exp)))]
    if reps:
        defects.append("PALABRA_REPETIDA")
    rate = None
    if words and last and first is not None and last > first:
        rate = round(len(got) / (last - first), 2)
        if rate > 3.8:
            defects.append("MUY_RAPIDO")
        elif rate < 2.3:
            defects.append("MUY_LENTO")
    ocr_raw = ocr_frames(clip, outdir)
    dlg_tokens = set(exp)
    ocr = []
    for o in ocr_raw:   # filtro de precisión: palabra larga, o palabra del diálogo (los subtítulos quemados repiten el diálogo)
        letters = re.sub(r"[^a-zñ]", "", _strip_accents(o["word"].lower()))
        if (len(letters) >= 5 and o["conf"] >= 75) or (len(letters) >= 3 and letters in dlg_tokens):
            ocr.append(o)
    if ocr:
        defects.append("TEXTO_EN_IMAGEN")
    sheet = os.path.join(outdir, base + "_hoja.jpg")
    contact_sheet(clip, sheet)
    hard = {"FALTAN_PALABRAS", "SOBRAN_PALABRAS", "CORTADO", "PALABRA_REPETIDA", "TEXTO_EN_IMAGEN"}
    verdict = "FAIL" if hard & set(defects) else ("REVISAR" if defects else "PASA_AUTO")
    res = {"type": "check", "project": os.path.basename(root), "line": line, "take": take,
           "clip": os.path.relpath(clip, root), "dur": round(dur, 2), "wer": wer,
           "missing": missing, "extra": extra, "subs": subs, "first_word": first, "last_word": last,
           "rate": rate, "repeats": reps, "ocr": ocr[:6], "defects": defects, "verdict": verdict,
           "heard": got_txt, "sheet": os.path.relpath(sheet, root)}
    if prompt_path:
        p = open(prompt_path, encoding="utf-8").read().strip()
        res.update({"prompt_id": prompt_id(p), "template_id": template_id(p)})
    if record:
        ledger_append(res)
    json.dump(res, open(os.path.join(outdir, base + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n== CHECK {line} · {os.path.basename(clip)} → {verdict}")
    print(f"  esperado : {expected_txt}")
    print(f"  escuchado: {got_txt}")
    print(f"  WER {wer} · arranque {first}s · fin {last}s de {dur:.2f}s · ritmo {rate} pal/s")
    for m_ in missing:
        print("  ✗ falta:", m_)
    for e_ in extra:
        print("  ✗ sobra:", e_)
    for a_, b_ in subs:
        print(f"  ✗ cambió: «{a_}» → «{b_}»")
    if ocr:
        print("  ! OCR:", ", ".join(f"{o['word']}@{o['t']}s" for o in ocr[:6]))
    for d in defects:
        print("  →", SUGGEST.get(d, d))
    print("  hoja:", res["sheet"])
    if verdict == "PASA_AUTO":
        print("  ✓ Pasa lo automático. Falta que William escuche el acento.")
    return res


# ---------------------------------------------------------------- REVIEW / REPORT
def review(root, line, take, accent, use, note):
    ledger_append({"type": "review", "project": os.path.basename(root), "line": line, "take": take,
                   "accent": accent, "use": use, "note": note})
    print("Anotado.")


def report():
    recs = ledger_read()
    subs = [r for r in recs if r["type"] == "submit" and r.get("ok")]
    checks = {(r["project"], r["line"], r.get("take")): r for r in recs if r["type"] == "check" and r.get("take")}
    reviews = {(r["project"], r["line"], r.get("take")): r for r in recs if r["type"] == "review"}
    lines = ["# Bitácora de prompts de Flow — aprendizajes", "",
             f"_Generado {dt.datetime.now():%Y-%m-%d %H:%M} desde `research/flow_ledger.jsonl`._", ""]
    total = sum(r.get("credits") or 0 for r in subs)
    lines += [f"**Tomas enviadas:** {len(subs)} · **Créditos registrados:** {total:,}", ""]
    by_t = {}
    for s in subs:
        k = (s["project"], s["line"], s.get("take"))
        key = f"{s.get('exp', '?')} · {s.get('model', '?')} · {s.get('res', '?')}"
        t = by_t.setdefault(key, {"n": 0, "auto": 0, "ok": 0, "cred": 0, "defects": {}})
        t["n"] += 1
        t["cred"] += s.get("credits") or 0
        c = checks.get(k)
        if c:
            if c["verdict"] == "PASA_AUTO":
                t["auto"] += 1
            for d in c["defects"]:
                t["defects"][d] = t["defects"].get(d, 0) + 1
        rv = reviews.get(k)
        if rv and rv.get("use") == "si":
            t["ok"] += 1
    lines += ["## Por experimento (versión de prompt · modelo · resolución)", "",
              "| Experimento | Tomas | Pasan lo automático | Aprobadas por William | Créditos | Créditos por toma usable | Defectos |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for tid, t in by_t.items():
        per = f"{t['cred'] / t['ok']:.0f}" if t["ok"] else "—"
        dd = ", ".join(f"{k}×{v}" for k, v in sorted(t["defects"].items(), key=lambda x: -x[1]))
        lines.append(f"| {tid} | {t['n']} | {t['auto']} | {t['ok']} | {t['cred']:,} | {per} | {dd} |")
    lines += ["", "## Por línea", "", "| Proyecto | Línea | Tomas | Créditos | Veredictos |", "|---|---|---:|---:|---|"]
    by_l = {}
    for s in subs:
        k = (s["project"], s["line"])
        e = by_l.setdefault(k, {"n": 0, "c": 0, "v": []})
        e["n"] += 1
        e["c"] += s.get("credits") or 0
        c = checks.get((s["project"], s["line"], s.get("take")))
        e["v"].append(f"{s.get('take')}:{c['verdict'] if c else '¿?'}")
    for (p, l), e in sorted(by_l.items()):
        lines.append(f"| {p} | {l} | {e['n']} | {e['c']:,} | {' '.join(e['v'])} |")
    bf = [r for r in recs if r["type"] == "backfill"]
    if bf:
        lines += ["", "## Línea base histórica (re-evaluada)", ""]
        for b in bf:
            lines.append(f"- **{b['project']}:** {b['takes']} tomas para {b['lines']} líneas "
                         f"({b['takes'] / max(1, b['lines']):.1f} por línea). Con el chequeador viejo "
                         f"{b['old_fail']} tenían WER > 0; con el normalizador nuevo, {b['new_fail']}. "
                         f"→ {b['old_fail'] - b['new_fail']} se veían mal solo por formato (números, nombres).")
    open(LEARN_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n→ {LEARN_MD}")


def backfill(project_dir):
    root = os.path.abspath(project_dir)
    aliases = load_aliases(root)
    script = {L["id"]: L for L in json.load(open(os.path.join(root, "script.json"), encoding="utf-8"))}
    takes = old_fail = new_fail = 0
    rows = []
    for j in sorted(glob.glob(os.path.join(root, "flow", "L*", "L*_?.json"))):
        d = json.load(open(j, encoding="utf-8"))
        if "palabras" not in d:
            continue
        lid = os.path.basename(j)[:3]
        if lid not in script:
            continue
        takes += 1
        exp_txt = script[lid].get("spoken_text", script[lid]["text"])
        got_txt = d.get("texto") or " ".join(w["w"] for w in d["palabras"])
        old = difflib.SequenceMatcher(None, _strip_accents(exp_txt.lower()).split(),
                                      _strip_accents(got_txt.lower()).split()).ratio() < 0.999
        wer, missing, extra, subs = align(normalize(exp_txt, aliases), normalize(got_txt, aliases))
        old_fail += int(old)
        new_fail += int(wer > 0)
        rows.append((os.path.basename(j), wer, missing, extra, subs))
    lines_n = len({r[0][:3] for r in rows})
    vm = os.path.join(root, "check", "voces.md")
    if os.path.isfile(vm):
        tot = fp = real = 0
        for row in open(vm, encoding="utf-8"):
            c = [x.strip() for x in row.strip().strip("|").split("|")]
            if len(c) < 7 or not re.fullmatch(r"L\d{2}", c[0]):
                continue
            tot += 1
            try:
                w = float(c[2])
            except ValueError:
                continue
            if w == 0:
                continue
            a_, b_ = sorted(normalize(c[5], aliases)), sorted(normalize(c[6], aliases))
            if a_ == b_:
                fp += 1
            else:
                real += 1
        print(f"voces.md: {tot} tomas generadas · {fp} marcadas con error solo por formato · {real} con error real")
        takes, old_fail, new_fail = tot, fp + real, real
    ledger_append({"type": "backfill", "project": os.path.basename(root), "takes": takes,
                   "lines": lines_n, "old_fail": old_fail, "new_fail": new_fail})
    for r in rows:
        if r[1] > 0:
            print(f"{r[0]}: WER {r[1]} falta={r[2]} sobra={r[3]} cambió={r[4]}")
    print(f"\n{takes} tomas · {lines_n} líneas · antes con diferencias: {old_fail} · con normalizador: {new_fail}")


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("lint"); a.add_argument("--line", required=True); a.add_argument("--prompt", required=True)
    a.add_argument("--dur", default=None, help="Duración objetivo del clip en Flow (6 u 8)")
    a.add_argument("--allow-override", action="store_true", help="Permitir exceder suavemente el rango de palabras")
    a = sp.add_parser("send"); a.add_argument("--line", required=True); a.add_argument("--prompt", required=True)
    a.add_argument("--res", default="720p"); a.add_argument("--dur", default="8"); a.add_argument("--force", action="store_true")
    a.add_argument("--model", help="p. ej. 'Omni 1.1 Flash', 'Veo 3.1 - Lite'")
    a = sp.add_parser("check"); a.add_argument("--line", required=True); a.add_argument("--clip", required=True)
    a.add_argument("--prompt"); a.add_argument("--take"); a.add_argument("--no-record", action="store_true")
    a = sp.add_parser("review"); a.add_argument("--line", required=True); a.add_argument("--take", required=True)
    a.add_argument("--accent", choices=["ok", "mal", "sin_dato"], default="sin_dato"); a.add_argument("--use", choices=["si", "no"], required=True)
    a.add_argument("--note", default="")
    sp.add_parser("report")
    a = sp.add_parser("backfill"); a.add_argument("--project", required=True)
    args = ap.parse_args()
    root = project_root()
    if args.cmd == "lint":
        r = lint(root, args.line, args.prompt, dur=args.dur, allow_override=args.allow_override)
        print_lint(r)
        sys.exit(1 if r["verdict"] == "FAIL" else 0)
    if args.cmd == "send":
        send(root, args.line, args.prompt, args.res, args.dur, args.force, args.model)
    if args.cmd == "check":
        check(root, args.line, args.clip, args.prompt, args.take, record=not args.no_record)
    if args.cmd == "review":
        review(root, args.line, args.take, args.accent, args.use, args.note)
    if args.cmd == "report":
        report()
    if args.cmd == "backfill":
        backfill(args.project)


if __name__ == "__main__":
    main()
