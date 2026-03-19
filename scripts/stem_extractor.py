#!/usr/bin/env python3
"""
Phase 3.1 — Dictionary-Wide Stem Extraction & Form Prediction
==============================================================

Predicts paradigmatic form_2 (3sg indicative perfective) from:
    headword + verb_class + stem_preverb

The stem extraction problem: the conjugation engine works on 7 hand-tagged
Appendix 1 verbs (76.2%) but only 14.8% on all dictionary verbs because it
can't find the stem/class/preverb automatically. This script bridges that gap.

Pipeline:
    1. Parse stem_preverb field → preverb(s)
    2. Infer class for VD → (u), VL → (wi)
    3. Apply mode prefix (ti- for 3sg indicative)
    4. Apply Skiri sound changes at morpheme boundaries
    5. Apply perfective final-consonant rules
    6. Compare predicted form_2 to attested form_2
    7. Report accuracy by class/preverb combination

Usage:
    python stem_extractor.py --validate        # full validation run
    python stem_extractor.py --predict HEADWORD --class "(1)" --preverb "(ut...)"
    python stem_extractor.py --report          # accuracy report by category
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Dict

# ---------------------------------------------------------------------------
# Preverb parsing
# ---------------------------------------------------------------------------

# Map stem_preverb notation → list of preverb morphemes
PREVERB_PATTERNS = {
    "(ut...)":              ["ut"],
    "(uur...)":             ["uur"],
    "(ir...)":              ["ir"],
    "(ir...ut...)":         ["ir", "ut"],
    "(ir...ri...ut...)":    ["ir", "ri", "ut"],
    "(ir...ri...uur...)":   ["ir", "ri", "uur"],
    "(ir...uur...)":        ["ir", "uur"],
    "(ku...ir...)":         ["ku", "ir"],
    "(u t...)":             ["ut"],       # OCR space artifact
    "(i r...ut...)":        ["ir", "ut"], # OCR space artifact
    "( i r . . . )":        ["ir"],       # OCR space artifact
}


def parse_stem_preverb(raw: str) -> Tuple[List[str], List[str]]:
    """
    Parse the stem_preverb field into (preverbs, extra_markers).

    Returns:
        preverbs: list of preverb morphemes ["ut"], ["ir", "ut"], etc.
        extras: list of additional markers like "[+ raar-]", "[+ ku-]"
    """
    if not raw or not raw.strip():
        return [], []

    raw = raw.strip()
    preverbs = []
    extras = []

    # Extract [+ ...] markers
    bracket_matches = re.findall(r'\[.*?\]', raw)
    for bm in bracket_matches:
        extras.append(bm)
    # Remove brackets from the main pattern
    main = re.sub(r'\[.*?\]', '', raw).strip()

    if main in PREVERB_PATTERNS:
        preverbs = PREVERB_PATTERNS[main]
    elif main:
        # Try to parse unknown patterns
        # Extract content between parentheses
        m = re.match(r'\((.*?)\)', main)
        if m:
            inner = m.group(1).replace('.', '').replace(' ', '').strip()
            # Split on ... separators
            parts = [p.strip() for p in re.split(r'\.\.\.+', m.group(1)) if p.strip()]
            preverbs = [p.replace('.', '').replace(' ', '') for p in parts if p.replace('.', '').replace(' ', '')]

    return preverbs, extras


def infer_verb_class(gram_class: str, verb_class: str, stem_preverb: str) -> str:
    """
    Infer verb class when not explicitly provided.

    VD (descriptive) → (u) by default (unless has uur- preverb)
    VL (locative) → (wi)
    """
    if verb_class and verb_class not in ('', 'None', '(pl. subj.)'):
        # Clean up duplicates like "(1), (1)"
        vc = verb_class.split(',')[0].strip()
        return vc

    if gram_class == 'VD':
        return '(u)'
    if gram_class == 'VL':
        return '(wi)'
    if gram_class and 'VP' in gram_class:
        return '(4)'  # passive verbs are often class 4

    # Try to infer from stem_preverb or grammatical_class sub-notation
    if gram_class and '(' in gram_class:
        # e.g., "VI(1), VT(1)" → extract class
        m = re.search(r'\((\d[^)]*)\)', gram_class)
        if m:
            return f'({m.group(1)})'

    return '(1)'  # default fallback


# ---------------------------------------------------------------------------
# Sound change rules for form_2 prediction
# ---------------------------------------------------------------------------

def apply_initial_coalescence(prefix: str, stem: str) -> str:
    """
    Apply vowel coalescence at the prefix + stem boundary.

    Parks Ch. 3 Unrestricted Vowel Rules:

    Rule 5 (Same-vowel): V + V(same) → VV (long)
        ta + aciks... → taa + ciks... = taaciks...

    Rule 6 (u-domination): V + u → uu
        ti + ut → tuut

    Rule 7 (i/a contraction): i + a → ii; a + i → ii
        ti + acikstat → tii + cikstat = tiicikstat
        EXCEPTION: contraction does NOT apply when vowels precede
        a final consonant (Parks: "two vowels are in word-final
        position or preceding a final consonant")
        ti + at → tiʔat (NOT tiit) — 'a' precedes final 't'

    Applied in order after restricted rules (Rule 1R-4R).
    """
    if not stem:
        return prefix

    first = stem[0]
    rest = stem[1:]

    if prefix.endswith('i'):
        if first == 'a':
            # Rule 7: i + a → ii, UNLESS the 'a' precedes a final consonant
            # Heuristic: if stem is very short (≤2 chars: vowel + ≤1 consonant),
            # the 'a' is near word-end → glottal insertion instead
            # Also insert ʔ for isolated short stems like "at", "a"
            if len(stem) <= 2:
                # Short stem: "at", "a", "ak" — glottal insertion
                return prefix + 'ʔ' + stem
            else:
                # Long stem: contraction. Consumes FIRST 'a' only.
                # ti + aahkarah → tii + hkarah → tiihkarah
                # ti + acikstat → tii + cikstat → tiicikstat
                return prefix + 'i' + rest
        elif first == 'u':
            # Rule 6: i + u → uu (u-domination)
            return prefix[:-1] + stem
        elif first == 'i':
            # Rule 5: i + i → ii (same-vowel)
            return prefix + rest

    elif prefix.endswith('a'):
        if first == 'a':
            # Rule 5: a + a → aa (same-vowel contraction)
            # ta + aciksuuwicaks → taa + ciksuuwicaks = taaciksuuwicaks
            # KEEP both a's — they form a long vowel
            return prefix + stem
        elif first == 'i':
            # Rule 7: a + i → ii
            # But only in unrestricted contexts. For ir-preverb 3sg (ta + stem),
            # the stem-initial 'i' should just concatenate normally in most cases.
            # Restrict this to specific known environments.
            return prefix + stem  # safe default: just concatenate

    elif prefix.endswith('u'):
        if first == 'u':
            # Rule 5: u + u → uu
            return prefix + rest
        elif first == 'a':
            # Rule 6: u + a → uu? No — Parks says V + u → uu, not u + V.
            # u + a just concatenates
            return prefix + stem

    # Default: simple concatenation
    return prefix + stem


def apply_perfective_finals(form: str, verb_class: str = "") -> str:
    """
    Apply perfective aspect final consonant changes.

    Rules (order matters — cluster rules first, then single consonant):
        -hk → -t  (cluster: h drops, k→t; e.g., -iihk → -iit)
        -tk → -t  (k absorbed into t)
        -kus → -ku (position verb s-loss)
        Final k → t  (Rule 3R)
        Final -uuh → -uuʔ
        Final -aah → -aa
        Final -iih → -iiʔ
        Final h → Ø
        Final r → Ø  (Rule 23)
        Final short vowel → vowel + ʔ
    """
    if not form:
        return form

    # --- Cluster rules (before single-consonant) ---
    if form.endswith('hk'):
        return form[:-2] + 't'
    if form.endswith('tk'):
        return form[:-1]

    # --- Position verb s-loss ---
    if form.endswith('kus'):
        return form[:-1]

    # --- Single final consonant ---
    if form.endswith('k'):
        return form[:-1] + 't'

    if form.endswith('uuh'):
        return form[:-1] + 'ʔ'
    if form.endswith('aah'):
        return form[:-1]
    if form.endswith('iih'):
        return form[:-1] + 'ʔ'
    if form.endswith('h'):
        return form[:-1]

    if form.endswith('r'):
        return form[:-1]

    # Final short vowel → add ʔ (but NOT long vowels — those stay)
    if form and form[-1] in 'aiu':
        if len(form) >= 2 and form[-2] == form[-1]:
            # Long vowel ending (aa, ii, uu) — add ʔ
            return form + 'ʔ'
        else:
            # Short vowel — add ʔ
            return form + 'ʔ'

    return form


def apply_internal_sound_changes(form: str) -> str:
    """
    Apply internal sound changes that occur within the word.

    Rule 8R: r → t after {p, t, k, s, c} (obstruent)
    Rule 12R: r → h before consonant
    """
    result = list(form)
    i = 0
    while i < len(result):
        if result[i] == 'r':
            # Rule 8R: r → t after obstruent
            if i > 0 and result[i-1] in 'ptksc':
                result[i] = 't'
            # Rule 12R: r → h before consonant
            elif i + 1 < len(result) and result[i+1] in 'ptkscwhrbm':
                result[i] = 'h'
        i += 1
    return ''.join(result)


def build_prefix_and_stem(preverbs: List[str], verb_class: str, gram_class: str, stem: str) -> Tuple[str, str]:
    """
    Build form_2 by fusing prefix + preverb + stem with junction rules.

    Returns the FULL fused form (prefix already merged with stem),
    and the remaining stem portion for debugging.

    Junction rules (from empirical analysis of 2,211 attested forms):

    ut-preverb (ti+ut = tuut) + stem:
        + vowel  → tuut + stem  (no change)
        + r      → tuuh + stem[1:]  (t+r → h, r absorbed)
        + h      → tut + stem[1:]   (h absorbed, uu shortens)
        + k      → tutk + stem[1:]  (uu shortens, cluster preserved)
        + p      → tutp + stem[1:]  (uu shortens, cluster preserved)
        + c      → tuc + stem       (t absorbed before c, uu shortens)
        + t      → tuct + stem[1:]  (dissimilation: ut+t → uct)
        + w      → tuut + stem      (w preserved, but complex — simplified)

    uur-preverb (ti+uur = tuur) + stem:
        + vowel  → tuur + stem  (no change)
        + C      → tuuh + C + stem[1:]  (Rule 12R: r → h before consonant)
        + r      → tur + stem[1:]  (uur+r → ur, one r degeminated)

    ir-preverb 3sg: ti + a(PREV.3A) = ta + stem
        (no special junction — ta just concatenates)
    """
    if not preverbs:
        # No preverb — simple ti + stem
        return "ti", stem

    first_prev = preverbs[0]
    stem_initial = stem[0] if stem else ''
    vowels = set('aiuAIU')

    # --- ut- preverb ---
    if first_prev == "ut":
        if gram_class and 'VR' in gram_class:
            base_prefix = "wituut"
        else:
            base_prefix = "tuut"

        if not stem:
            return base_prefix, stem
        if stem_initial in vowels:
            return base_prefix, stem
        elif stem_initial == 'r':
            # tuut + r → tuuh + rest (r absorbed into h)
            return base_prefix[:-1].replace('tuut', 'tuuh').replace('wituut', 'wituuh'), stem[1:]
        elif stem_initial == 'h':
            # tuut + h → tut + rest (h absorbed, uu shortens)
            return base_prefix.replace('tuut', 'tut').replace('wituut', 'witut'), stem[1:]
        elif stem_initial == 'k':
            # tuut + k → tutk + rest (uu shortens)
            return base_prefix.replace('tuut', 'tut').replace('wituut', 'witut'), stem
        elif stem_initial == 'p':
            # tuut + p → tutp (uu shortens, but t+p preserved)
            return base_prefix.replace('tuut', 'tut').replace('wituut', 'witut'), stem
        elif stem_initial == 'c':
            # tuut + c → tuc (t absorbed, uu shortens)
            return base_prefix.replace('tuut', 'tu').replace('wituut', 'witu'), stem
        elif stem_initial == 't':
            # tuut + t → tuct (dissimilation)
            return base_prefix.replace('tuut', 'tuc').replace('wituut', 'wituc'), stem
        elif stem_initial == 's':
            # tuut + s → tus? or tuuts? Treat as: uu shortens
            return base_prefix.replace('tuut', 'tut').replace('wituut', 'witut'), stem
        elif stem_initial == 'w':
            # Complex — keep tuut for now
            return base_prefix, stem
        else:
            return base_prefix, stem

    # --- uur- preverb ---
    elif first_prev == "uur":
        base_prefix = "tuur"
        if not stem:
            return base_prefix, stem
        if stem_initial in vowels:
            return base_prefix, stem
        elif stem_initial == 'r':
            # tuur + r → tur (degemination)
            return "tur", stem[1:]
        else:
            # Rule 12R: r → h before any consonant
            return "tuuh", stem

    # --- ir- preverb (3sg uses a- instead of ir-) ---
    elif first_prev == "ir":
        base_prefix = "ta"
        # Handle additional preverbs after ir
        for pv in preverbs[1:]:
            if pv == "ri":
                base_prefix += "ri"
            elif pv == "ut":
                # ta + ri? + ut → complex; simplified
                base_prefix += "riut"
            elif pv == "uur":
                base_prefix += "ruur"
        return base_prefix, stem

    # --- ku- proclitic ---
    elif first_prev == "ku":
        base_prefix = "kuti"
        for pv in preverbs[1:]:
            if pv == "ir":
                base_prefix = "kuta"
        return base_prefix, stem

    return "ti", stem


def build_prefix(preverbs: List[str], verb_class: str, gram_class: str) -> str:
    """Legacy wrapper — returns just the prefix without stem fusion."""
    if not preverbs:
        return "ti"
    first_prev = preverbs[0]
    if first_prev == "ut":
        if gram_class and 'VR' in gram_class:
            return "wituut"
        return "tuut"
    elif first_prev == "uur":
        return "tuur"
    elif first_prev == "ir":
        prefix = "ta"
        for pv in preverbs[1:]:
            if pv == "ri": prefix += "ri"
            elif pv == "ut": prefix += "riut"
            elif pv == "uur": prefix += "ruur"
        return prefix
    elif first_prev == "ku":
        if len(preverbs) > 1 and preverbs[1] == "ir":
            return "kuta"
        return "kuti"
    if gram_class and 'VR' in gram_class:
        return "witi"
    return "ti"


# ---------------------------------------------------------------------------
# Form_2 predictor
# ---------------------------------------------------------------------------

def predict_form_2(
    headword: str,
    verb_class: str,
    stem_preverb: str,
    gram_class: str,
) -> Tuple[str, Dict]:
    """
    Predict form_2 (3sg indicative perfective) from entry fields.

    Returns (predicted_form, debug_info).
    """
    # Step 1: Parse preverb
    preverbs, extras = parse_stem_preverb(stem_preverb)

    # Step 2: Infer verb class
    vc = infer_verb_class(gram_class, verb_class, stem_preverb)

    # Step 3: Build prefix
    prefix = build_prefix(preverbs, vc, gram_class)

    # Step 4: Determine stem — headword IS the stem in Parks' dictionary
    stem = headword

    # Clean headword alternates: "acikstarahkiis/kis" → "acikstarahkiis"
    if '/' in stem:
        stem = stem.split('/')[0].strip()

    # Strip notation markers: "[+ neg.]", "[+ raar-]"
    stem = re.sub(r'\s*\[.*?\]\s*', '', stem).strip()

    # Strip trailing whitespace/punctuation artifacts
    stem = stem.strip().rstrip('.')

    # Step 5: Apply prefix+stem fusion (with preverb junction rules)
    if preverbs:
        fused_prefix, fused_stem = build_prefix_and_stem(preverbs, vc, gram_class, stem)
        raw = apply_initial_coalescence(fused_prefix, fused_stem)
    else:
        raw = apply_initial_coalescence(prefix, stem)

    # Step 6: Apply internal sound changes
    raw = apply_internal_sound_changes(raw)

    # Step 7: Apply perfective final changes
    # VL (wi) verbs don't add final glottal stop
    if vc == '(wi)':
        predicted = raw  # locative verbs: no perfective final changes
    elif vc == '(3)':
        # Class 3 perfective: -aʔuk contracts to -uʔ
        # acikstaʔuk → ...cikstuʔ, ahihaʔuk → ...hihuʔ
        if raw.endswith('aʔuk'):
            predicted = raw[:-4] + 'uʔ'
        elif raw.endswith("a'uk"):
            predicted = raw[:-4] + "uʔ"
        else:
            predicted = apply_perfective_finals(raw, verb_class=vc)
    else:
        predicted = apply_perfective_finals(raw, verb_class=vc)

    debug = {
        "preverbs": preverbs,
        "inferred_class": vc,
        "prefix": prefix,
        "stem": stem,
        "raw_concat": prefix + stem,
        "after_coalescence": apply_initial_coalescence(prefix, stem),
    }

    return predicted, debug


# ---------------------------------------------------------------------------
# Validation against DB
# ---------------------------------------------------------------------------

def validate_all(db_path: str, verbose: bool = False, limit: int = 0) -> Dict:
    """
    Run form_2 prediction on all dictionary verbs and report accuracy.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    sql = """
        SELECT le.entry_id, le.headword, le.verb_class, le.stem_preverb, 
               le.grammatical_class, pf.skiri_form as form_2
        FROM lexical_entries le
        JOIN paradigmatic_forms pf ON le.entry_id = pf.entry_id AND pf.form_number = 2
        WHERE le.grammatical_class LIKE 'V%'
        AND pf.skiri_form IS NOT NULL AND pf.skiri_form != ''
        AND pf.skiri_form NOT LIKE '%,%'
    """
    if limit:
        sql += f" LIMIT {limit}"

    cur = conn.execute(sql)

    total = 0
    exact = 0
    close = 0  # glottal-only difference
    miss = 0
    by_category = {}
    mismatches = []

    for r in cur:
        hw = r['headword']
        vc = r['verb_class'] or ''
        sp = r['stem_preverb'] or ''
        gc = r['grammatical_class'] or ''
        f2_attested = r['form_2']

        predicted, debug = predict_form_2(hw, vc, sp, gc)

        total += 1

        # Normalize for comparison
        pred_norm = predicted.replace("'", "ʔ").replace("\u2019", "ʔ").lower()

        # Handle semicolon-separated variant forms in attested data
        att_variants = [v.strip().replace("'", "ʔ").replace("\u2019", "ʔ").lower()
                        for v in f2_attested.split(';')]

        if pred_norm in att_variants:
            status = 'exact'
            exact += 1
        elif any(pred_norm.replace("ʔ", "") == v.replace("ʔ", "") for v in att_variants):
            status = 'close'
            close += 1
        else:
            status = 'miss'
            miss += 1
            if verbose or len(mismatches) < 50:
                mismatches.append({
                    "headword": hw,
                    "class": vc,
                    "preverb": sp,
                    "gram_class": gc,
                    "attested": f2_attested,
                    "predicted": predicted,
                    "debug": debug,
                })

        # Track by category
        cat_key = f"{infer_verb_class(gc, vc, sp)}|{sp[:12] if sp else 'none'}"
        if cat_key not in by_category:
            by_category[cat_key] = {'exact': 0, 'close': 0, 'miss': 0, 'total': 0}
        by_category[cat_key][status] += 1
        by_category[cat_key]['total'] += 1

    conn.close()

    return {
        "total": total,
        "exact": exact,
        "close": close,
        "miss": miss,
        "accuracy_exact": round(100 * exact / total, 1) if total else 0,
        "accuracy_with_close": round(100 * (exact + close) / total, 1) if total else 0,
        "by_category": by_category,
        "sample_mismatches": mismatches[:30],
    }


def print_report(results: Dict):
    """Print a formatted accuracy report."""
    print("=" * 70)
    print("STEM EXTRACTION — FORM_2 PREDICTION ACCURACY")
    print("=" * 70)
    print(f"Total verbs tested:  {results['total']}")
    print(f"Exact matches:       {results['exact']} ({results['accuracy_exact']}%)")
    print(f"Close (glottal):     {results['close']}")
    print(f"Miss:                {results['miss']}")
    print(f"Accuracy (exact):    {results['accuracy_exact']}%")
    print(f"Accuracy (w/ close): {results['accuracy_with_close']}%")

    print(f"\n{'─'*70}")
    print(f"{'Category':<30} {'Total':>5} {'Exact':>6} {'%':>6} {'Close':>6} {'Miss':>6}")
    print(f"{'─'*70}")
    for key, v in sorted(results['by_category'].items(), key=lambda x: -x[1]['total']):
        if v['total'] < 5:
            continue
        pct = 100 * v['exact'] / v['total'] if v['total'] else 0
        print(f"  {key:<28} {v['total']:>5} {v['exact']:>6} {pct:>5.1f}% {v['close']:>6} {v['miss']:>6}")

    if results['sample_mismatches']:
        print(f"\n{'─'*70}")
        print(f"SAMPLE MISMATCHES (first {len(results['sample_mismatches'])})")
        print(f"{'─'*70}")
        for m in results['sample_mismatches'][:20]:
            print(f"  {m['headword']:<25} class={m['class']:<8} prev={m['preverb']:<12}")
            print(f"    attested:  {m['attested']}")
            print(f"    predicted: {m['predicted']}")
            print(f"    prefix={m['debug']['prefix']}  preverbs={m['debug']['preverbs']}")
            print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 3.1 — Stem Extraction Pipeline")
    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skiri_pawnee.db")
    parser.add_argument("--db", default=default_db, help="Path to SQLite database")
    parser.add_argument("--validate", action="store_true", help="Run full validation")
    parser.add_argument("--report", action="store_true", help="Print accuracy report")
    parser.add_argument("--limit", type=int, default=0, help="Limit validation to N entries")
    parser.add_argument("--verbose", action="store_true", help="Show all mismatches")
    parser.add_argument("--predict", metavar="HEADWORD", help="Predict form_2 for a headword")
    parser.add_argument("--class", dest="verb_class", default="", help="Verb class for --predict")
    parser.add_argument("--preverb", default="", help="Stem preverb for --predict")
    parser.add_argument("--gram-class", default="VI", help="Grammatical class for --predict")
    args = parser.parse_args()

    if args.predict:
        predicted, debug = predict_form_2(args.predict, args.verb_class, args.preverb, args.gram_class)
        print(f"Headword:  {args.predict}")
        print(f"Class:     {args.verb_class or '(inferred)'}")
        print(f"Preverb:   {args.preverb or '(none)'}")
        print(f"Predicted: {predicted}")
        print(f"Debug:     {json.dumps(debug, ensure_ascii=False, indent=2)}")
        return

    if args.validate or args.report:
        results = validate_all(args.db, verbose=args.verbose, limit=args.limit)
        print_report(results)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
