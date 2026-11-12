#!/usr/bin/env python3
"""
audit_listicle.py - Bilingual (ES/EN) viral listicle-as-story & causal script auditor v2 for Webres Studio.

Combines:
1. Hook scoring, conditional-modal gate (<1.2s direct opening) & sentence-length burstiness / slop
   heuristics adapted for ES + EN.
2. 3-Channel Non-Duplication Rule (<40% overlap between spoken hook and screen text).
3. Anti-Catalog ("Pero / Entonces" story vs. flat "Uno, Dos, Tres"), Zero Empty Rhetorical Bridges
   (preventing 5.7s filler drops between statistics), Spatial CTA check, and Verbal Loop check.
4. Split Conversion CTA & Commercial Protection: prohibits "Guarda... o comenta..." disjunction
   and prohibits sending business leads to external third-party web/marketing agencies.
5. Approachable 2-Tier Google Flow 1.0x Phonetic Word Cadence:
   - Tier 1 (Agile 6s): 10-18 phonetic words -> 6s 720p clip, 1 visual state.
   - Tier 2 (Extended 8s): 19-24 phonetic words -> 8s 720p clip + mid-take visual shift in engine.js.
   - Supports --allow-override when an intentional line exceeds 24 words.

Usage:
  python3 audit_listicle.py draft_es.json --lang es
  python3 audit_listicle.py GUION.md --lang es --allow-override --output report.json
"""

import argparse
import json
import re
import statistics
import sys
import unicodedata

WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)?|\$\d[\d,.]*", re.UNICODE)
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*", re.UNICODE)
NUMBER_RE = re.compile(r"\$\s?\d[\d,.]*|\b\d[\d,.]*%?\b")
PROPER_RE = re.compile(r"(?<![.!?¿¡]\s)(?<!^)(?<![¿¡])\b[A-ZÁÉÍÓÚÑ][a-záéíóúñüA-Z0-9_-]{2,}\b")

LANG_CONFIG = {
    "es": {
        "spoken_numbers": {
            "cero", "un", "uno", "una", "dos", "tres", "cuatro", "cinco", "seis",
            "siete", "ocho", "nueve", "diez", "doce", "quince", "veinte", "treinta",
            "cuarenta", "cincuenta", "sesenta", "ochenta", "cien", "ciento", "mil",
            "millón", "millones", "mitad", "doble", "triple", "minuto", "minutos", "segundos",
        },
        "stakes": {
            "suelta", "deja", "para", "nunca", "jamás", "mal", "error", "errores",
            "pierdes", "perder", "arruina", "rompe", "fallo", "falla", "nadie",
            "no", "sin", "prohibido", "feo", "horrible", "trampa", "secreto",
            "antes", "pero", "mejor", "peor", "desastre", "cuidado", "olvida",
            "gratis", "dormir", "medianoche", "prisa", "competencia", "rival", "fuera",
        },
        "imperatives": {
            "suelta", "deja", "mira", "prueba", "escribe", "pon", "guarda",
            "mándaselo", "envíaselo", "olvida", "borra", "cambia", "acepta", "apaga",
        },
        "weak_openers": [
            "hola", "buenas", "bienvenidos", "hoy te", "hoy vamos", "en este video",
            "en el video", "como sabes", "básicamente", "literalmente", "bueno pues",
        ],
        "conditional_openers": [
            "puede que ", "tal vez ", "quizás ", "quizá ", "a lo mejor ", "es posible que ",
            "sabías que ", "¿sabías que ",
        ],
        "empty_bridge_phrases": [
            "te dejo tres pasos", "te dejo estos pasos", "te traigo tres pasos",
            "te dejo cinco pasos", "una pista:", "por qué tan pocos? una pista",
            "¿por qué tan pocos? una pista", "¿por qué pasa esto? una pista",
        ],
        "third_party_leak_phrases": [
            "quien maneja tu página", "quien maneja tu web", "quien lleva tu página",
            "quien lleva tu marketing", "tu agencia de marketing", "al que te lleva las redes",
        ],
        "save_or_comment_re": re.compile(
            r"\bguarda\b[^.?!]{0,65}\bo\b[^.?!]{0,50}\b(?:escr[íi]benos|comenta|deja\s+un\s+comentario)\b",
            re.IGNORECASE,
        ),
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
            "eighty", "hundred", "thousand", "million", "half", "twice", "triple", "seconds", "minute",
        },
        "stakes": {
            "stop", "quit", "never", "wrong", "mistake", "lost", "lose", "wreck",
            "cost", "broken", "fail", "nobody", "no", "not", "don't", "aren't",
            "banned", "worst", "hated", "hate", "unfair", "secret", "before",
            "until", "but", "better", "bug", "sleep", "competitor", "competitors",
        },
        "imperatives": {
            "stop", "quit", "steal", "copy", "delete", "try", "watch", "save",
            "use", "type", "send", "tap", "admit", "hand",
        },
        "weak_openers": [
            "hey", "hi ", "hello", "welcome", "in this video", "in today's",
            "today i", "let's talk", "so basically", "guys ",
        ],
        "conditional_openers": [
            "maybe ", "perhaps ", "it might be that ", "did you know that ",
        ],
        "empty_bridge_phrases": [
            "here are three steps", "i will give you three steps", "want a hint?",
        ],
        "third_party_leak_phrases": [
            "whoever runs your website", "whoever manages your marketing", "your marketing agency",
        ],
        "save_or_comment_re": re.compile(
            r"\bsave\b[^.?!]{0,60}\bor\b[^.?!]{0,45}\b(?:comment|write\s+us|drop\s+a\s+comment)\b",
            re.IGNORECASE,
        ),
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


def count_phonetic_words(text):
    """Estimate spoken phonetic word count, expanding decimals and multi-digit numbers."""
    expanded = re.sub(r"(?<=\d),(?=\d)", "", text)
    # Decimal like 4.8 -> 3 spoken words ("cuatro punto ocho" / "four point eight")
    expanded = re.sub(r"\b\d+\.\d+\b", " num punto dec ", expanded)

    def _expand_int(match):
        val = int(match.group(0))
        if val <= 30 or val in (40, 50, 60, 70, 80, 90, 100, 1000):
            return " num "
        if val < 1000:
            return " num num "
        return " num num num "

    expanded = re.sub(r"\b\d+\b", _expand_int, expanded)
    return len(WORD_RE.findall(expanded))


def strip_screen_notes(screen_text):
    """Remove parenthetical production notes or arrows when counting clean screen words."""
    cleaned = re.sub(r"\([^)]*\)", "", screen_text)
    cleaned = re.sub(r"[·→+/=|]", " ", cleaned)
    return tokenize(cleaned)


def score_first_sentence_hook(first_sentence, cfg):
    words = tokenize(first_sentence)
    n = len(words)
    low = [w.lower() for w in words]

    if 4 <= n <= 9:
        len_score = 100.0
    elif n < 4:
        len_score = clamp(100 - (4 - n) * 20)
    else:
        len_score = clamp(100 - (n - 9) * 12)

    nums = NUMBER_RE.findall(first_sentence)
    propers = set(PROPER_RE.findall(first_sentence))
    spoken_nums = [w for w in low if w in cfg["spoken_numbers"]]
    spec_hits = len(nums) + len(propers) + len(spoken_nums)
    spec_score = 20.0 if spec_hits == 0 else clamp(50 + spec_hits * 25)

    stake_hits = [w for w in low if w in cfg["stakes"]]
    stake_score = 25.0 if not stake_hits else (75.0 if len(set(stake_hits)) == 1 else 100.0)

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


def audit_script(data, lang, allow_override=False):
    cfg = LANG_CONFIG[lang]
    takes = data.get("takes", [])
    if len(takes) < 4:
        raise ValueError("Script JSON must contain at least 4 takes in 'takes'.")

    issues = []
    warnings = []

    # 1. Hook audit on L01 first sentence + Conditional Modal check
    l01_spoken = takes[0]["spoken"].strip()
    l01_low = re.sub(r"^[¡¿\"'«]+", "", l01_spoken.lower()).strip()
    for cond in cfg["conditional_openers"]:
        if l01_low.startswith(cond.lstrip("¿")):
            msg = (
                f"L01 opens with weak conditional/hedging phrase ('{cond.strip()}'), delaying threat/reward past 2.0s. "
                f"Start with a direct fact or imperative."
            )
            if allow_override:
                warnings.append(msg)
            else:
                issues.append(msg)
            break

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

    # 3. Full-script Burstiness, Slop, Regionalisms, Empty Bridges & CTA Protection
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

    low_full = low_cta_check(full_spoken.lower())
    for phrase in cfg["slop_phrases"]:
        if phrase in low_full:
            issues.append(f"AI slop phrase detected: '{phrase}'.")
    for reg in cfg["regionalisms_forbidden"]:
        if reg in low_full:
            issues.append(f"Non-neutral regionalism forbidden by AGENTS.md B1: '{reg.strip()}'.")
    for bad_cta in cfg["bad_like_spatial"]:
        if bad_cta in low_full:
            issues.append(f"Spatial error on vertical feed: '{bad_cta}' (Like button is on the right side, not below).")
    for bridge in cfg["empty_bridge_phrases"]:
        if bridge in low_full:
            issues.append(
                f"Empty rhetorical bridge detected: '{bridge}' (caused -7pt drop in retention forensics; deliver data/steps directly)."
            )
    for leak in cfg["third_party_leak_phrases"]:
        if leak in low_full:
            issues.append(
                f"Commercial leak phrase detected: '{leak}' (sends business prospects to a third-party agency instead of your brand)."
            )
    if cfg["save_or_comment_re"].search(full_spoken):
        issues.append(
            "Spoken 'Save OR Comment' disjunction detected. Trigger Save visually via Causal Cursor on the end-sheet and ask for ONE spoken comment action."
        )

    # 4. Anti-Flat-Dictionary check ("Uno: ... Dos: ...")
    flat_hits = [t["id"] for t in takes if cfg["flat_list_re"].search(t["spoken"])]
    if len(flat_hits) >= 2:
        issues.append(
            f"Flat numbered glossary detected in spoken lines ({', '.join(flat_hits)}). Chain items with 'Pero / Entonces' story transitions instead."
        )

    # 5. Approachable 2-Tier Flow 1.0x phonetic word budget & visual cut pulse
    take_stats = []
    for t in takes:
        tid = t["id"]
        w_count = len(tokenize(t["spoken"]))
        phon_count = count_phonetic_words(t["spoken"])
        scr_words = strip_screen_notes(t.get("screen_text", ""))
        cuts = t.get("cuts_sec", [])

        if phon_count <= 18:
            tier = "agile_6s"
            rec_dur = 6
        elif phon_count <= 24:
            tier = "extended_8s"
            rec_dur = 8
        else:
            tier = "overflow"
            rec_dur = 8

        if phon_count > 24:
            msg = (
                f"{tid} has {phon_count} phonetic words ({w_count} written): exceeds 24-word 8s natural cadence budget. "
                f"Split into 2 causal pulses or pass --allow-override."
            )
            if allow_override and phon_count <= 28:
                warnings.append(msg)
            else:
                issues.append(msg)
        elif phon_count >= 19:
            if not cuts or (len(cuts) == 1 and cuts[0] > 5.8):
                warnings.append(
                    f"{tid} ({phon_count} phonetic words -> 8s Flow clip): remember to trigger a mid-take visual shift at ~4.0-4.8s in engine.js."
                )
        elif phon_count < 10:
            warnings.append(f"{tid} has {phon_count} phonetic words (short punchline; verify intentional pacing).")

        if len(scr_words) > 6:
            issues.append(f"{tid} screen_text has {len(scr_words)} words ('{t.get('screen_text')}'); max is 6.")

        for idx, dur in enumerate(cuts, 1):
            if dur > 6.2:
                issues.append(f"{tid} cut #{idx} lasts {dur:.1f}s (> 6.2s visual habituation ceiling).")
            elif dur > 5.8:
                warnings.append(f"{tid} cut #{idx} lasts {dur:.1f}s (borderline; optimal visual pulse is 4.0-5.8s).")

        take_stats.append(
            {
                "id": tid,
                "spoken_words": w_count,
                "phonetic_words": phon_count,
                "tier": tier,
                "recommended_flow_dur": rec_dur,
                "screen_words": len(scr_words),
                "cuts_sec": cuts,
            }
        )

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
        "total_phonetic_words": sum(t["phonetic_words"] for t in take_stats),
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
    print(f"\nVIRAL LISTICLE-AS-STORY AUDIT v2 ({rep['language'].upper()})  ->  {rep['verdict']}")
    print("=" * 76)
    print(
        f"  Takes: {rep['total_takes']}  |  Written words: {rep['total_spoken_words']}  |  "
        f"Phonetic words: {rep['total_phonetic_words']}"
    )
    print(f"  L01 Hook Score:      {rep['hook']['score']} ({rep['hook']['verdict']}) — \"{rep['hook']['first_sentence']}\"")
    print(f"  L01 Overlap:         {rep['l01_screen_spoken_overlap']*100:.0f}% (want < 40%)")
    print(f"  Burstiness (CV):     {rep['burstiness_cv']:.2f} (want >= 0.55) | lens={rep['sentence_lengths']}")
    print(f"  Verbal Loop Words:   {', '.join(rep['loop_keywords']) if rep['loop_keywords'] else 'NONE'}")
    print("-" * 76)
    for t in rep["takes"]:
        cuts_str = " + ".join(f"{c:.1f}s" for c in t["cuts_sec"]) if t["cuts_sec"] else "n/a"
        print(
            f"  {t['id']:<5} {t['phonetic_words']:>2} phon w ({t['recommended_flow_dur']}s {t['tier']:<11}) | "
            f"{t['screen_words']} screen w | cuts: {cuts_str}"
        )
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
        takes.append(
            {
                "id": tid.upper(),
                "cuts_sec": cuts,
                "screen_text": cols[2].strip(),
                "spoken": spoken,
            }
        )
    if not takes:
        raise ValueError(f"Could not parse JSON or Markdown L01..Lxx table from: {path}")
    return {"takes": takes}


def main():
    ap = argparse.ArgumentParser(description="Audit a viral listicle-as-story video script v2 (JSON or GUION.md).")
    ap.add_argument("input", help="Path to draft JSON or GUION.md file")
    ap.add_argument("--lang", choices=["es", "en"], required=True, help="Script language (es or en)")
    ap.add_argument("--allow-override", action="store_true", help="Downgrade soft cadence/opener gates to warnings")
    ap.add_argument("--output", help="Optional path to write full JSON report")
    args = ap.parse_args()

    data = load_script_input(args.input)
    report = audit_script(data, args.lang, allow_override=args.allow_override)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
        print(f"Audit report written to: {args.output} ({report['verdict']})")
    else:
        print_summary(report)

    sys.exit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
