#!/usr/bin/env python3
"""
audit_listicle.py - Bilingual (ES/EN) viral listicle-as-story script auditor for Webres Studio.

Combines:
1. Hook scoring & sentence-length burstiness / slop heuristics adapted for ES + EN
   from Jakeschincariol/instagram-agent-skill (MIT License).
2. 3-Channel Non-Duplication Rule from coreyhaines31/marketingskills.
3. Anti-Catalog ("Pero / Entonces" story vs. flat "Uno, Dos, Tres"), Spatial CTA check,
   and Verbal Loop check from vyralcontent/content-skills + TikTok Promote catalog.
4. Webres Studio AGENTS.md rules: Google Flow 1.0x take budget (12-22 words/take),
   sub-cuts <= 4.0s, <= 6 words on-screen text, and Guatemala-neutral Spanish checks.

Usage:
  python3 audit_listicle.py draft_es.json --lang es
  python3 audit_listicle.py draft_en.json --lang en --output report.json
"""

import argparse
import json
import re
import statistics
import sys
import unicodedata

# Unicode-aware word tokenizer supporting Spanish accents & contractions
WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)?|\$\d[\d,.]*", re.UNICODE)
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*", re.UNICODE)
NUMBER_RE = re.compile(r"\$\s?\d[\d,.]*|\b\d[\d,.]*%?\b")
PROPER_RE = re.compile(r"(?<![.!?¿¡]\s)(?<!^)(?<![¿¡])\b[A-ZÁÉÍÓÚÑ][a-záéíóúñüA-Z0-9_-]{2,}\b")

LANG_CONFIG = {
    "es": {
        "spoken_numbers": {
            "cero", "un", "uno", "una", "dos", "tres", "cuatro", "cinco", "seis",
            "siete", "ocho", "nueve", "diez", "doce", "quince", "veinte", "treinta",
            "cuarenta", "cincuenta", "cien", "ciento", "mil", "millón", "millones",
            "mitad", "doble", "triple", "minuto", "minutos", "segundos",
        },
        "stakes": {
            "suelta", "deja", "para", "nunca", "jamás", "mal", "error", "errores",
            "pierdes", "perder", "arruina", "rompe", "fallo", "falla", "nadie",
            "no", "sin", "prohibido", "feo", "horrible", "trampa", "secreto",
            "antes", "pero", "mejor", "peor", "desastre", "cuidado", "olvida",
            "gratis", "dormir", "medianoche", "prisa",
        },
        "imperatives": {
            "suelta", "deja", "mira", "prueba", "escribe", "pon", "guarda",
            "mándaselo", "envíaselo", "olvida", "borra", "cambia", "acepta", "apaga",
        },
        "weak_openers": [
            "hola", "buenas", "bienvenidos", "hoy te", "hoy vamos", "en este video",
            "en el video", "como sabes", "básicamente", "literalmente", "bueno pues",
        ],
        "pronouns_re": re.compile(
            r"\b(tú|tu|tus|te|ti|contigo|yo|me|mi|mis|conmigo|nosotros|nos|"
            r"suelta|deja|pides|pones|escribes|mándaselo|déjame|sé)\b",
            re.IGNORECASE,
        ),
        "stopwords": {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
            "a", "en", "con", "por", "para", "sin", "sobre", "y", "o", "u", "pero",
            "que", "qué", "se", "su", "sus", "tu", "tus", "te", "lo", "le", "les",
            "es", "son", "como", "más", "ya", "si", "no", "mi", "me", "eso", "esto",
        },
        "slop_phrases": [
            "en el mundo actual", "sumérgete", "revolucionario", "cambiará las reglas del juego",
            "cabe destacar", "es importante recordar", "sin más preámbulos", "lleva tu",
            "al siguiente nivel", "desbloquea el poder", "hoy en día",
        ],
        "regionalisms_forbidden": [
            "ocupas", "ocupamos", "ojo con", "chaval", "tío", "vos sabés", "ustedes saben",
            "parce", "che ", "güey", "neta ", "chido", "currar", "flipar",
        ],
        "flat_list_re": re.compile(
            r"^\s*(?:número\s+)?(?:uno|dos|tres|cuatro|cinco|seis|primero|segundo|tercero|[1-9])[\s:.,-]",
            re.IGNORECASE,
        ),
        "bad_like_spatial": ["aquí abajo", "acá abajo", "abajo dale like", "botón de abajo"],
    },
    "en": {
        "spoken_numbers": {
            "zero", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "twelve", "fifteen", "twenty", "thirty", "forty", "fifty", "sixty",
            "hundred", "thousand", "million", "half", "twice", "triple", "seconds", "minute",
        },
        "stakes": {
            "stop", "quit", "never", "wrong", "mistake", "lost", "lose", "wreck",
            "cost", "broken", "fail", "nobody", "no", "not", "don't", "aren't",
            "banned", "worst", "hated", "hate", "unfair", "secret", "before",
            "until", "but", "better", "bug", "sleep",
        },
        "imperatives": {
            "stop", "quit", "steal", "copy", "delete", "try", "watch", "save",
            "use", "type", "send", "tap", "admit", "hand",
        },
        "weak_openers": [
            "hey", "hi ", "hello", "welcome", "in this video", "in today's",
            "today i", "let's talk", "so basically", "guys ",
        ],
        "pronouns_re": re.compile(
            r"\b(you|your|you're|yourself|i|me|my|mine|we|us|our)\b",
            re.IGNORECASE,
        ),
        "stopwords": {
            "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on",
            "for", "with", "that", "this", "it", "is", "are", "was", "were", "be",
            "you", "your", "i", "my", "me", "we", "our", "so", "not", "no", "one",
        },
        "slop_phrases": [
            "in today's fast-paced", "game-changer", "game changer", "delve",
            "unleash", "unlock the power", "take your", "to the next level",
            "without further ado", "buckle up", "mind-blowing",
        ],
        "regionalisms_forbidden": [],
        "flat_list_re": re.compile(
            r"^\s*(?:number\s+)?(?:one|two|three|four|five|six|first|second|third|[1-9])[\s:.,-]",
            re.IGNORECASE,
        ),
        "bad_like_spatial": ["down below", "like button below", "tap below"],
    },
}


def clamp(val):
    return max(0.0, min(100.0, val))


def tokenize(text):
    return WORD_RE.findall(re.sub(r"(?<=\d),(?=\d)", "", text))


def strip_screen_notes(screen_text):
    """Remove parenthetical production notes or arrows when counting clean screen words."""
    cleaned = re.sub(r"\([^)]*\)", "", screen_text)
    cleaned = re.sub(r"[·→+/=|]", " ", cleaned)
    return tokenize(cleaned)


def score_first_sentence_hook(first_sentence, cfg):
    words = tokenize(first_sentence)
    n = len(words)
    low = [w.lower() for w in words]

    # 1. Length (target 4-9 words for sub-2.8s punch)
    if 4 <= n <= 9:
        len_score = 100.0
    elif n < 4:
        len_score = clamp(100 - (4 - n) * 20)
    else:
        len_score = clamp(100 - (n - 9) * 12)

    # 2. Specificity
    nums = NUMBER_RE.findall(first_sentence)
    propers = set(PROPER_RE.findall(first_sentence))
    spoken_nums = [w for w in low if w in cfg["spoken_numbers"]]
    spec_hits = len(nums) + len(propers) + len(spoken_nums)
    spec_score = 20.0 if spec_hits == 0 else clamp(50 + spec_hits * 25)

    # 3. Stakes
    stake_hits = [w for w in low if w in cfg["stakes"]]
    stake_score = 25.0 if not stake_hits else (75.0 if len(set(stake_hits)) == 1 else 100.0)

    # 4. Frontload
    joined_start = " ".join(low[:3])
    weak_hit = next((w for w in cfg["weak_openers"] if joined_start.startswith(w)), None)
    payload_idx = None
    for idx, tok in enumerate(low):
        if (
            tok in cfg["stakes"]
            or tok in cfg["spoken_numbers"]
            or NUMBER_RE.match(words[idx])
            or (idx > 0 and PROPER_RE.match(words[idx]))
        ):
            payload_idx = idx
            break
    if payload_idx is None:
        front_score = 30.0
    elif payload_idx <= 3:
        front_score = 100.0
    elif payload_idx <= 5:
        front_score = 75.0
    else:
        front_score = 40.0
    if weak_hit:
        front_score = clamp(front_score - 35)

    # 5. Direct Address
    if low and low[0] in cfg["imperatives"]:
        addr_score = 95.0
    elif cfg["pronouns_re"].search(first_sentence):
        addr_score = 100.0
    else:
        addr_score = 40.0

    sub = {
        "length": round(len_score, 1),
        "specificity": round(spec_score, 1),
        "stakes": round(stake_score, 1),
        "frontload": round(front_score, 1),
        "address": round(addr_score, 1),
    }
    vals = list(sub.values())
    overall = round(statistics.mean(vals) * 0.6 + min(vals) * 0.4, 1)
    verdict = "STRONG" if overall >= 75 and min(vals) >= 55 else ("OK" if overall >= 55 else "WEAK")
    return {"first_sentence": first_sentence, "words": n, "score": overall, "verdict": verdict, "subscores": sub}


def audit_script(data, lang):
    cfg = LANG_CONFIG[lang]
    takes = data.get("takes", [])
    if len(takes) < 4:
        raise ValueError("Script JSON must contain at least 4 takes in 'takes'.")

    issues = []
    warnings = []

    # 1. Hook audit on L01 first sentence
    l01_spoken = takes[0]["spoken"].strip()
    first_sents = [s.strip() for s in SENT_RE.findall(l01_spoken) if s.strip()]
    first_sent = first_sents[0] if first_sents else l01_spoken
    hook_res = score_first_sentence_hook(first_sent, cfg)
    if hook_res["verdict"] != "STRONG":
        issues.append(
            f"L01 first sentence Hook Score is {hook_res['score']} ({hook_res['verdict']}); target >= 75 STRONG."
        )

    # 2. L01 3-Channel Non-Duplication check
    l01_screen_words = {w.lower() for w in strip_screen_notes(takes[0].get("screen_text", "")) if len(w) > 2}
    l01_spoken_words = {w.lower() for w in tokenize(l01_spoken) if len(w) > 2}
    overlap = len(l01_screen_words & l01_spoken_words) / max(len(l01_screen_words), 1)
    if overlap >= 0.40:
        issues.append(
            f"L01 screen_text duplicates spoken hook ({overlap*100:.0f}% lexical overlap; must be < 40%)."
        )

    # 3. Full-script Burstiness, Slop, Regionalisms & Typography
    full_spoken = "\n".join(t["spoken"].strip() for t in takes)
    all_sents = [s.strip() for s in SENT_RE.findall(full_spoken) if len(tokenize(s)) >= 2]
    sent_lens = [len(tokenize(s)) for s in all_sents]
    cv = statistics.pstdev(sent_lens) / statistics.mean(sent_lens) if len(sent_lens) >= 4 else 0.0
    if cv < 0.50:
        issues.append(
            f"Sentence-length burstiness CV is {cv:.2f} (robotic/uniform). Add 2-4 word micro-reactions to reach >= 0.55."
        )
    elif cv < 0.55:
        warnings.append(f"Burstiness CV is {cv:.2f} (borderline; ideal >= 0.55).")

    if "—" in full_spoken:
        issues.append("Em-dash '—' detected in spoken script (AI fingerprint).")
    invisible_count = sum(1 for c in full_spoken if unicodedata.category(c) == "Cf")
    if invisible_count:
        issues.append(f"{invisible_count} invisible Unicode format character(s) found.")

    low_full = full_spoken.lower()
    for phrase in cfg["slop_phrases"]:
        if phrase in low_full:
            issues.append(f"AI slop phrase detected: '{phrase}'.")
    for reg in cfg["regionalisms_forbidden"]:
        if reg in low_full:
            issues.append(f"Non-neutral regionalism forbidden by AGENTS.md B1: '{reg.strip()}'.")
    for bad_cta in cfg["bad_like_spatial"]:
        if bad_cta in low_cta_check(low_full):
            issues.append(f"Spatial error on vertical feed: '{bad_cta}' (Like button is on the right side, not below).")

    # 4. Anti-Flat-Dictionary check ("Uno: ... Dos: ...")
    flat_hits = [t["id"] for t in takes if cfg["flat_list_re"].search(t["spoken"])]
    if len(flat_hits) >= 2:
        issues.append(
            f"Flat numbered glossary detected in spoken lines ({', '.join(flat_hits)}). Chain items with 'Pero / Entonces' story transitions instead."
        )

    # 5. Per-take Flow 1.0x word budget, screen_text <= 6 words, and visual cut <= 4.0s
    take_stats = []
    for t in takes:
        tid = t["id"]
        w_count = len(tokenize(t["spoken"]))
        scr_words = strip_screen_notes(t.get("screen_text", ""))
        cuts = t.get("cuts_sec", [])
        if w_count > 22:
            issues.append(f"{tid} has {w_count} words (exceeds Google Flow 1.0x 8s max of 22 words).")
        elif w_count < 11:
            warnings.append(f"{tid} has {w_count} words (short; check pacing intentionally).")
        if len(scr_words) > 6:
            issues.append(f"{tid} screen_text has {len(scr_words)} words ('{t.get('screen_text')}'); max is 6.")
        for idx, dur in enumerate(cuts, 1):
            if dur > 4.0:
                issues.append(f"{tid} cut #{idx} lasts {dur:.1f}s (> 4.0s static-frame limit).")
        take_stats.append({"id": tid, "spoken_words": w_count, "screen_words": len(scr_words), "cuts_sec": cuts})

    # 6. Verbal Loop check (L01 <-> Final Take)
    first_kw = {w.lower() for w in tokenize(takes[0]["spoken"]) if w.lower() not in cfg["stopwords"] and len(w) > 2}
    last_kw = {w.lower() for w in tokenize(takes[-1]["spoken"]) if w.lower() not in cfg["stopwords"] and len(w) > 2}
    loop_words = sorted(first_kw & last_kw)
    if not loop_words:
        issues.append("No verbal loop between first and last take. Echo a hook keyword/brand at the end for replay boost.")

    verdict = "PASS" if not issues else "FAIL"
    return {
        "language": lang,
        "verdict": verdict,
        "total_takes": len(takes),
        "total_spoken_words": sum(t["spoken_words"] for t in take_stats),
        "hook": hook_res,
        "l01_screen_spoken_overlap": round(overlap, 2),
        "burstiness_cv": round(cv, 2),
        "sentence_lengths": sent_lens,
        "loop_keywords": loop_words,
        "issues": issues,
        "warnings": warnings,
        "takes": take_stats,
    }


def low_cta_check(text):
    return re.sub(r"\s+", " ", text)


def print_summary(rep):
    print(f"\nVIRAL LISTICLE-AS-STORY AUDIT ({rep['language'].upper()})  ->  {rep['verdict']}")
    print("=" * 68)
    print(f"  Takes: {rep['total_takes']}  |  Total words: {rep['total_spoken_words']}")
    print(f"  L01 Hook Score:      {rep['hook']['score']} ({rep['hook']['verdict']}) — \"{rep['hook']['first_sentence']}\"")
    print(f"  L01 Overlap:         {rep['l01_screen_spoken_overlap']*100:.0f}% (want < 40%)")
    print(f"  Burstiness (CV):     {rep['burstiness_cv']:.2f} (want >= 0.55) | lens={rep['sentence_lengths']}")
    print(f"  Verbal Loop Words:   {', '.join(rep['loop_keywords']) if rep['loop_keywords'] else 'NONE'}")
    print("-" * 68)
    for t in rep["takes"]:
        cuts_str = " + ".join(f"{c:.1f}s" for c in t["cuts_sec"]) if t["cuts_sec"] else "n/a"
        print(f"  {t['id']:<5} {t['spoken_words']:>2} spoken w  |  {t['screen_words']} screen w  |  cuts: {cuts_str}")
    if rep["warnings"]:
        print("\n  Warnings:")
        for w in rep["warnings"]:
            print(f"    ! {w}")
    if rep["issues"]:
        print("\n  Blocking Issues:")
        for iss in rep["issues"]:
            print(f"    X {iss}")
    print("")


def load_script_input(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        return json.loads(raw)
    takes = []
    range_re = re.compile(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*s")
    for line in raw.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cols = [c.strip() for c in s.strip("|").split("|")]
        if len(cols) < 5:
            continue
        tid = re.sub(r"[*`]", "", cols[0]).strip()
        if not re.match(r"^L\d+$", tid, re.IGNORECASE):
            continue
        cuts = [round(float(b) - float(a), 2) for a, b in range_re.findall(cols[1])]
        spoken = cols[4].strip().strip("«»\"“”")
        takes.append({
            "id": tid.upper(),
            "cuts_sec": cuts,
            "screen_text": cols[2].strip(),
            "spoken": spoken,
        })
    if not takes:
        raise ValueError(f"Could not parse JSON or Markdown L01..Lxx table from: {path}")
    return {"takes": takes}


def main():
    ap = argparse.ArgumentParser(description="Audit a viral listicle-as-story video script (JSON or GUION.md).")
    ap.add_argument("input", help="Path to draft JSON or GUION.md file")
    ap.add_argument("--lang", choices=["es", "en"], required=True, help="Script language (es or en)")
    ap.add_argument("--output", help="Optional path to write full JSON report")
    args = ap.parse_args()

    data = load_script_input(args.input)

    report = audit_script(data, args.lang)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
        print(f"Audit report written to: {args.output} ({report['verdict']})")
    else:
        print_summary(report)

    sys.exit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
