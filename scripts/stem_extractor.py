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
import math
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
        # Long initial vowel on stem blocks coalescence → glottal epenthesis
        if len(stem) >= 2 and first in 'aiu' and stem[1] == first:
            # Stem starts with long vowel (aa, ii, uu): ti + VV... → tiʔVV...
            return prefix + 'ʔ' + stem

        if first == 'a':
            # Rule 7: i + a -> ii, with exceptions for glottal insertion
            if len(stem) <= 2:
                # Short stem: "at", "a", "ak" -- glottal insertion
                return prefix + 'ʔ' + stem
            else:
                # Long stem with short initial 'a': contraction
                # ti + acikstat -> tii + cikstat -> tiicikstat
                return prefix + 'i' + rest
        elif first == 'u':
            # Rule 6: i + u → uu (u-domination)
            return prefix[:-1] + stem
        elif first == 'i':
            # Rule 5: i + i → ii (same-vowel) — keep BOTH i's for long ii
            return prefix + stem

    elif prefix.endswith('a'):
        if first == 'a':
            # Rule 5: a + a → aa (same-vowel contraction)
            # ta + aciksuuwicaks → taa + ciksuuwicaks = taaciksuuwicaks
            # KEEP both a's — they form a long vowel
            return prefix + stem
        elif first == 'i':
            # Rule 7: a + i → ii
            # Long initial vowel on stem blocks coalescence -> glottal epenthesis
            if len(stem) >= 2 and stem[1] == 'i':
                # Stem starts with long ii: ta + iita -> taʔiita
                return prefix + 'ʔ' + stem
            # Short i: a + i -> ii (contraction)
            # ta + icawiʔa -> tiicawiʔa, ta + iksucaʔa -> tiiksucaaʔ
            return prefix[:-1] + 'i' + stem
        elif first == 'u':
            # Rule 6: V + u -> uu (u-domination)
            # ta + uʔa -> tuuʔa, ta + ucaʔa -> tuucaaʔ
            return prefix[:-1] + stem

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
    if form.endswith('hc'):
        # -hc → -c (h deleted before affricate)
        return form[:-2] + 'c'
    if form.endswith('sk'):
        # -sk → -s (k deleted in sibilant cluster)
        return form[:-1]
    if form.endswith('tk'):
        return form[:-1]

    # --- Position verb s-loss ---
    if form.endswith('kus'):
        return form[:-1]

    # --- Single final consonant ---
    if form.endswith('k'):
        return form[:-1] + 't'

    if form.endswith('uuh'):
        # Long uu shortens before h-deletion: -uuh -> -uʔ (not -uuʔ)
        # e.g., kaacuuh -> kaacuʔ, irikaacuuh -> irikaacuʔ
        return form[:-2] + 'ʔ'
    if form.endswith('aah'):
        return form[:-1]
    if form.endswith('iih'):
        return form[:-1] + 'ʔ'
    if form.endswith('h'):
        return form[:-1]

    if form.endswith('r'):
        # Rule 23: final r -> Ø
        # After r-deletion, apply vowel-specific rules:
        #   -uur  -> -uuʔ  (long uu preserved + glottal)
        #   -aar  -> -aa   (no ʔ)
        #   -wiir -> -wiʔ  (long ii shortens after glide w)
        #   -Ciir -> -Cii  (long ii preserved, no ʔ, after non-glide C)
        #   short V + r -> short V (no ʔ)
        form = form[:-1]
        if form.endswith('uu'):
            return form + 'ʔ'
        if form.endswith('wii'):
            # Glide w + long ii: shorten to wi + ʔ
            return form[:-1] + 'ʔ'
        return form

    # Final short vowel → add ʔ (but NOT long vowels — those stay)
    if form and form[-1] in 'aiu':
        if len(form) >= 2 and form[-2] == form[-1]:
            # Long vowel ending (aa, ii, uu) — add ʔ
            return form + 'ʔ'
        else:
            # Short vowel — add ʔ
            # Class (4) -sa endings: no final ʔ (perfective null alternation)
            if verb_class == '(4)' and form.endswith('sa'):
                return form
            return form + 'ʔ'

    return form


def apply_vd_echo_insertion(form: str) -> str:
    """
    Apply VD (descriptive verb) perfective ʔ-echo insertion.

    Descriptive verbs insert ʔ + echo vowel before final stop consonants
    in the perfective aspect. The echo vowel is the short version of
    the vowel immediately preceding the final consonant.

    Pattern: ...VC(final) -> ...VʔVC(final)
        kaac -> kaaʔac  (aa + c -> aaʔa + c)
        awirit -> awiriʔit  (i + t -> iʔi + t)
        huut -> huuʔut  (uu + t -> uuʔu + t)

    Also handles h+stop clusters: -Vht -> -VʔVt (h drops, echo inserts)
        huuruht -> huuruʔut  (u + ht -> uʔu + t)
        racakiht -> racakit   (i + ht -> i + t, short vowel no echo)

    Does NOT apply when ʔ+V already precedes the final consonant (echo exists).
    Does NOT apply before s when preceded by ii, uu, or short vowels.
    """
    if len(form) < 2:
        return form

    vowels_set = set('aiuáíú')

    # Walk backwards to find final consonant cluster
    i = len(form) - 1
    while i >= 0 and form[i] not in vowels_set and form[i] != 'ʔ':
        i -= 1

    if i < 0:
        return form  # no vowel found

    final_consonants = form[i+1:]
    preceding_vowel_pos = i

    # Check if echo already present: ...ʔV+C pattern
    # e.g., kickuuʔat -> the ʔa before t means echo already exists
    if form[preceding_vowel_pos] in vowels_set and preceding_vowel_pos >= 1 and form[preceding_vowel_pos - 1] == 'ʔ':
        return form  # echo already present, don't double-insert

    # Handle h+stop clusters: -Vht -> -VʔVt (h drops, echo inserts)
    if len(final_consonants) == 2 and final_consonants[0] == 'h' and final_consonants[1] in 'ctk':
        vowel_char = form[preceding_vowel_pos]
        short_vowel = vowel_char.replace('á', 'a').replace('í', 'i').replace('ú', 'u')
        is_long = (preceding_vowel_pos > 0 and
                   form[preceding_vowel_pos - 1] == form[preceding_vowel_pos])
        final_stop = final_consonants[1]
        if is_long:
            # Long vowel + ht: insert echo (h drops)
            # huuruht -> huuruʔut, icaʔuuht -> icaʔuuʔut
            return form[:i+1] + 'ʔ' + short_vowel + final_stop
        else:
            # Short vowel + ht: h drops, no echo
            # racakiht -> racakit, racapaht -> racapat -> then perfective adds ʔ
            return form[:i+1] + final_stop

    # Only insert echo for SINGLE final consonant (not clusters)
    if len(final_consonants) != 1:
        return form

    final_c = final_consonants[0]

    # Get the preceding vowel(s)
    vowel_char = form[preceding_vowel_pos]
    short_vowel = vowel_char.replace('á', 'a').replace('í', 'i').replace('ú', 'u')

    # Check if long vowel (same char repeated)
    is_long = (preceding_vowel_pos > 0 and
               form[preceding_vowel_pos - 1] == form[preceding_vowel_pos])

    if final_c in 'ctk':
        # Always insert echo before stops
        return form[:i+1] + 'ʔ' + short_vowel + final_consonants
    elif final_c == 's' and is_long and short_vowel == 'a':
        # Only insert before s when preceded by long aa
        return form[:i+1] + 'ʔ' + short_vowel + final_consonants

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
    # VR (reflexive) verbs get witi- prefix BEFORE the regular prefix
    # But "VT, VR" dual class uses VT form (no witi-)
    is_pure_vr = (gram_class == 'VR')

    if not preverbs:
        if is_pure_vr:
            # witi + ti + stem → wititi + coalescence
            return "wititi", stem
        # No preverb — simple ti + stem
        return "ti", stem

    first_prev = preverbs[0]
    stem_initial = stem[0] if stem else ''
    vowels = set('aiuAIU')

    # --- ut- preverb ---
    if first_prev == "ut":
        if is_pure_vr:
            base_prefix = "witituut"
        else:
            base_prefix = "tuut"

        if not stem:
            return base_prefix, stem
        # Helper: replace the trailing ut-preverb portion of prefix
        def _ut_junction(replacement):
            # base_prefix ends with "tuut" (or "witituut"); replace that tail
            return base_prefix[:-4] + replacement

        if stem_initial in vowels:
            return base_prefix, stem
        elif stem_initial == 'r':
            # tuut + r → tuuh + rest (r absorbed into h)
            return _ut_junction("tuuh"), stem[1:]
        elif stem_initial == 'h':
            # tuut + h → tut + rest (h absorbed, uu shortens)
            return _ut_junction("tut"), stem[1:]
        elif stem_initial == 'k':
            # tuut + k → tutk + rest (uu shortens)
            return _ut_junction("tut"), stem
        elif stem_initial == 'p':
            # tuut + p → tutp (uu shortens, but t+p preserved)
            return _ut_junction("tut"), stem
        elif stem_initial == 'c':
            # tuut + c → tuc (t absorbed, uu shortens)
            return _ut_junction("tu"), stem
        elif stem_initial == 't':
            # tuut + t → tuct (dissimilation)
            return _ut_junction("tuc"), stem
        elif stem_initial == 's':
            # tuut + s → tuts (uu shortens)
            return _ut_junction("tut"), stem
        elif stem_initial == 'w':
            # ut+w junction: w → p after t (bilabial fortition), uu shortens
            # tuut + w... → tutp + rest_after_w (w→p, uu→u)
            return _ut_junction("tut") + 'p', stem[1:]
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
        elif stem_initial == 'h':
            # tuur + h → tuuh (h absorbed, like ut+h rule)
            return "tuuh", stem[1:]
        elif stem_initial == 's':
            # Rule 12R: r → h before C, then Rule: s → c after h
            return "tuuh", 'c' + stem[1:]
        else:
            # Rule 12R: r → h before any consonant
            return "tuuh", stem

    # --- ir- preverb (3sg uses a- instead of ir-) ---
    elif first_prev == "ir":
        # For ir+ut and ir+uur combinations, the inner preverb gets
        # junction rules. ir- 3sg is realized as a- (3.A prefix).
        inner_prevs = preverbs[1:]

        if inner_prevs and inner_prevs[-1] == "ut":
            # ir + (ri?) + ut → ta(ri?) + ut → coalescence a+u=uu → t(ari)uut
            # Then apply ut-junction rules with stem
            ri_part = "ri" if "ri" in inner_prevs else ""
            # a + ut → uut (a+u coalescence = uu, + t)
            ut_prefix = "t" + ri_part + "uut"
            if is_pure_vr:
                ut_prefix = "witi" + ut_prefix

            if not stem:
                return ut_prefix, stem
            # Apply ut-junction rules (same as regular ut-preverb)
            def _ir_ut_junction(replacement):
                return ut_prefix[:-4] + replacement

            if stem_initial in vowels:
                return ut_prefix, stem
            elif stem_initial == 'r':
                return _ir_ut_junction("tuuh"), stem[1:]
            elif stem_initial == 'h':
                # ir+ut+h: h absorbed but uu stays (unlike regular ut+h which shortens)
                return _ir_ut_junction("tuut"), stem[1:]
            elif stem_initial == 'k':
                # ir+ut+k: uu preserved (unlike regular ut+k which shortens)
                return _ir_ut_junction("tuut"), stem
            elif stem_initial == 'p':
                return _ir_ut_junction("tuut"), stem
            elif stem_initial == 's':
                return _ir_ut_junction("tuut"), stem
            elif stem_initial == 'c':
                # ir+ut+c: tuut+c -> tuuc (uu preserved, t+c -> c)
                return _ir_ut_junction("tuu"), stem
            elif stem_initial == 't':
                return _ir_ut_junction("tuc"), stem
            elif stem_initial == 'w':
                return ut_prefix, stem
            else:
                return ut_prefix, stem

        elif inner_prevs and inner_prevs[-1] == "uur":
            ri_part = "ri" if "ri" in inner_prevs else ""
            # ir+uur -> tuur for 3sg; ir+ri+uur -> taruur (ri+uur fuses to ruur)
            if ri_part:
                base_prefix = "ta" + "ruur"  # ri + uur -> ruur (i absorbed)
            else:
                # a + uur -> uur (a absorbed into uur)
                base_prefix = "tuur"
            if not stem:
                return base_prefix, stem
            if stem_initial in vowels:
                return base_prefix, stem
            elif stem_initial == 'r':
                return base_prefix[:-2] + "r", stem[1:]
            elif stem_initial == 'h':
                # h absorbed into junction (like regular uur+h)
                return base_prefix[:-1] + "h", stem[1:]
            else:
                return base_prefix[:-1] + "h", stem
        else:
            base_prefix = "ta"
            for pv in inner_prevs:
                if pv == "ri":
                    base_prefix += "ri"
            return base_prefix, stem

    # --- ku- proclitic ---
    elif first_prev == "ku":
        base_prefix = "kuti"
        for pv in preverbs[1:]:
            if pv == "ir":
                base_prefix = "kuta"
        return base_prefix, stem

    # --- raar- inner preverb (from [+ raar-] bracket notation) ---
    elif first_prev == "raar":
        # ti + raar + stem → tiraar + stem
        # At boundary: final r of raar → h before consonant (Rule 12R)
        base_prefix = "tiraar"
        if stem and stem[0] not in vowels:
            # r → h before consonant
            base_prefix = "tirah"
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

    # Extract bracket notation from headword before stripping
    hw_brackets = re.findall(r'\[.*?\]', stem)
    all_brackets = extras + hw_brackets

    # Strip notation markers: "[+ neg.]", "[+ raar-]"
    stem = re.sub(r'\s*\[.*?\]\s*', '', stem).strip()

    # Strip trailing whitespace/punctuation artifacts
    stem = stem.strip().rstrip('.')

    # Strip class notation suffix: "-i" (class 2 subordinate marker)
    # e.g., "as-i" → "as", "kuksas-i" → "kuksas", "askatatiir-i" → "askatatiir"
    if stem.endswith('-i'):
        stem = stem[:-2]

    # Step 4b: Apply bracket notation modifiers
    bracket_prefix_override = None
    for bracket in all_brackets:
        b = bracket.lower().replace('[', '').replace(']', '').replace('+', '').strip()
        if 'neg' in b:
            # [+ neg.] → negative mode prefix kaaki- (replaces ti-)
            bracket_prefix_override = 'kaaki'
        elif b.strip() == 'i-' or b.strip().endswith(', i-') or b.startswith('i-'):
            # [+ i-] → prepend i- to stem (coalescence will handle ti+i→tii)
            stem = 'i' + stem
        elif 'raar-' in b or 'raar' in b:
            # [+ raar-] → raar preverb (ti + raar + stem → tiraar+stem)
            # raar- is treated as an inner preverb after the mode prefix
            if not preverbs:
                preverbs = ['raar']
        elif 'ruu-' in b or 'ruu' in b:
            # [+ ruu-, i-] or [+ ruu-] → ruu- prefix replaces ti-
            bracket_prefix_override = 'ruuti'
            # Also check for ", i-" in the bracket
            if 'i-' in b and 'ruu' in b:
                stem = 'i' + stem
        elif 'ku-' in b:
            # [+ ku-] → ku- proclitic
            if not preverbs:
                bracket_prefix_override = 'kuti'

    # Step 5: Apply prefix+stem fusion (with preverb junction rules)
    if bracket_prefix_override:
        prefix = bracket_prefix_override
        raw = apply_initial_coalescence(prefix, stem)
    else:
        # Always use build_prefix_and_stem for proper VR/junction handling
        fused_prefix, fused_stem = build_prefix_and_stem(preverbs, vc, gram_class, stem)
        raw = apply_initial_coalescence(fused_prefix, fused_stem)

    # Step 6: Apply internal sound changes
    raw = apply_internal_sound_changes(raw)

    # Step 6b: VD (descriptive) verb echo insertion before perfective finals
    is_vd = gram_class in ('VD',)
    if is_vd and vc == '(u)':
        raw = apply_vd_echo_insertion(raw)

    # Step 7: Apply perfective final changes
    # VL (wi) verbs don't add final glottal stop
    if vc == '(wi)':
        # Locative verbs: k→t applies, but no other perfective finals
        if raw.endswith('hk'):
            predicted = raw[:-2] + 't'
        elif raw.endswith('k'):
            predicted = raw[:-1] + 't'
        else:
            predicted = raw
    elif vc == '(3)':
        # Class 3 perfective contractions:
        #   -aʔuk → -uʔ  (e.g., acikstaʔuk → cikstuʔ)
        #   -aʔu  → -uʔ  (e.g., awirictaʔu → wirictuʔ)
        #   -aʔa  → -aaʔ (e.g., huutaʔa → huutaaʔ)
        if raw.endswith('aʔuk') or raw.endswith("a'uk"):
            predicted = raw[:-4] + 'uʔ'
        elif raw.endswith('aʔu') or raw.endswith("a'u"):
            predicted = raw[:-3] + 'uʔ'
        elif raw.endswith('aʔa') or raw.endswith("a'a"):
            # Check for long aa + ʔa pattern (aaʔa): the ʔ is root-internal,
            # NOT the class 3 derivational suffix boundary.
            # E.g., kaaʔa -> kaaʔaʔ (no contraction), not kaaaʔ
            pos = len(raw) - 4 if raw.endswith('aʔa') else len(raw) - 4
            if pos >= 0 and raw[pos] == 'a':
                # Long aa + ʔa: skip contraction, use regular perfective
                predicted = apply_perfective_finals(raw, verb_class=vc)
            else:
                predicted = raw[:-3] + 'aaʔ'
        else:
            predicted = apply_perfective_finals(raw, verb_class=vc)
    else:
        predicted = apply_perfective_finals(raw, verb_class=vc)

    # Step 7b: VD-specific post-processing
    if is_vd:
        # VD verbs: final long -wii shortens to -wi before ʔ
        # e.g., kariwiiʔ -> kariwiʔ, wiiʔ -> wiʔ
        if predicted.endswith('wiiʔ'):
            predicted = predicted[:-3] + 'iʔ'
        # VD -kus endings: s is NOT stripped (kus -> kus, not ku)
        # Already handled by echo insertion for most cases;
        # override the kus -> ku stripping for VD
        if raw.endswith('kus') and predicted.endswith('ku'):
            predicted = raw  # preserve -kus for VD

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
    def _p(text: str):
        """Print Unicode-safe on Windows (cp1252 console)."""
        sys.stdout.buffer.write((text + '\n').encode('utf-8', errors='replace'))

    _p("=" * 70)
    _p("STEM EXTRACTION -- FORM_2 PREDICTION ACCURACY")
    _p("=" * 70)
    _p(f"Total verbs tested:  {results['total']}")
    _p(f"Exact matches:       {results['exact']} ({results['accuracy_exact']}%)")
    _p(f"Close (glottal):     {results['close']}")
    _p(f"Miss:                {results['miss']}")
    _p(f"Accuracy (exact):    {results['accuracy_exact']}%")
    _p(f"Accuracy (w/ close): {results['accuracy_with_close']}%")

    _p(f"\n{'-'*70}")
    _p(f"{'Category':<30} {'Total':>5} {'Exact':>6} {'%':>6} {'Close':>6} {'Miss':>6}")
    _p(f"{'-'*70}")
    for key, v in sorted(results['by_category'].items(), key=lambda x: -x[1]['total']):
        if v['total'] < 5:
            continue
        pct = 100 * v['exact'] / v['total'] if v['total'] else 0
        _p(f"  {key:<28} {v['total']:>5} {v['exact']:>6} {pct:>5.1f}% {v['close']:>6} {v['miss']:>6}")

    if results['sample_mismatches']:
        _p(f"\n{'-'*70}")
        _p(f"SAMPLE MISMATCHES (first {len(results['sample_mismatches'])})")
        _p(f"{'-'*70}")
        for m in results['sample_mismatches'][:20]:
            _p(f"  {m['headword']:<25} class={m['class']:<8} prev={m['preverb']:<12}")
            _p(f"    attested:  {m['attested']}")
            _p(f"    predicted: {m['predicted']}")
            _p(f"    prefix={m['debug']['prefix']}  preverbs={m['debug']['preverbs']}")
            _p("")


# ---------------------------------------------------------------------------
# Phase 4.3 — Confidence Scoring
# ---------------------------------------------------------------------------

# Complexity indicators that reduce confidence
_COMPLEXITY_PATTERNS = [
    re.compile(r'\['),          # bracket notation [+ ...]
    re.compile(r'/'),           # slash alternates
    re.compile(r'\s'),          # multi-word headwords
    re.compile(r'-i$'),         # class 2 subordinate marker
]


def compute_confidence(
    entry_id: str,
    headword: str,
    verb_class: str,
    stem_preverb: str,
    gram_class: str,
    category_rates: Dict[str, Dict[str, float]],
) -> float:
    """
    Compute confidence score (0.0-1.0) for a predicted form_2.

    Inputs:
        category_rates: {cat_key: {"exact_rate": float, "close_rate": float, "total": int}}
            from validate_all() by_category data.

    Scoring factors:
        1. Category accuracy (base prior, 0.0-1.0) — 50% weight
        2. Prediction method — explicit verb_class/preverb boost — 20% weight
        3. Stem complexity — multi-word, brackets, slashes penalize — 15% weight
        4. Category sample size — small samples lower confidence — 15% weight
    """
    vc = infer_verb_class(gram_class, verb_class, stem_preverb)
    cat_key = f"{vc}|{stem_preverb[:12] if stem_preverb else 'none'}"

    # --- Factor 1: Category accuracy (base prior) ---
    cat_info = category_rates.get(cat_key)
    if cat_info and cat_info["total"] > 0:
        # Use (exact + close) rate as the base — close matches are structurally correct
        cat_rate = cat_info["close_rate"]
    else:
        # Unknown category — use global average as fallback (conservative)
        cat_rate = 0.5

    # --- Factor 2: Prediction method reliability ---
    method_score = 0.5  # baseline
    if verb_class and verb_class not in ('', 'None', '(pl. subj.)'):
        method_score += 0.25  # explicit verb class is more reliable
    if stem_preverb and stem_preverb.strip():
        method_score += 0.25  # explicit preverb narrows the prediction
    method_score = min(method_score, 1.0)

    # --- Factor 3: Stem complexity ---
    complexity_penalty = 0
    for pat in _COMPLEXITY_PATTERNS:
        if pat.search(headword or ''):
            complexity_penalty += 0.25
    complexity_score = max(0.0, 1.0 - complexity_penalty)

    # --- Factor 4: Category sample size (Bayesian shrinkage) ---
    if cat_info:
        n = cat_info["total"]
        # Sigmoid-like ramp: 1 sample -> 0.3, 5 -> 0.7, 20+ -> ~1.0
        size_score = 1.0 - 0.7 * math.exp(-n / 8.0)
    else:
        size_score = 0.2  # unknown category

    # --- Weighted combination ---
    confidence = (
        0.50 * cat_rate +
        0.20 * method_score +
        0.15 * complexity_score +
        0.15 * size_score
    )

    return round(max(0.0, min(1.0, confidence)), 3)


def populate_confidence(db_path: str, verbose: bool = False):
    """
    Compute and store form2_confidence for all verb entries in the DB.

    1. Runs validate_all() to get per-category accuracy rates.
    2. Computes confidence for every verb entry (not just those with attested form_2).
    3. Writes confidence to lexical_entries.form2_confidence.
    """
    def _p(text: str):
        sys.stdout.buffer.write((text + '\n').encode('utf-8', errors='replace'))

    # Step 1: Get category accuracy rates from validation
    _p("Running validation to build category accuracy rates...")
    results = validate_all(db_path)

    category_rates = {}
    for cat_key, stats in results["by_category"].items():
        total = stats["total"]
        if total > 0:
            category_rates[cat_key] = {
                "exact_rate": stats["exact"] / total,
                "close_rate": (stats["exact"] + stats["close"]) / total,
                "total": total,
            }

    _p(f"  {len(category_rates)} categories with accuracy data")

    # Step 2: Ensure DB column exists
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("ALTER TABLE lexical_entries ADD COLUMN form2_confidence REAL")
        _p("  Added form2_confidence column to lexical_entries")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Step 3: Compute confidence for all verb entries
    cur = conn.execute("""
        SELECT entry_id, headword, verb_class, stem_preverb, grammatical_class
        FROM lexical_entries
        WHERE grammatical_class LIKE 'V%'
    """)
    rows = cur.fetchall()

    updates = []
    score_dist = {"high": 0, "medium": 0, "low": 0}

    for r in rows:
        conf = compute_confidence(
            r["entry_id"], r["headword"],
            r["verb_class"] or '', r["stem_preverb"] or '',
            r["grammatical_class"] or '',
            category_rates,
        )
        updates.append((conf, r["entry_id"]))

        if conf >= 0.75:
            score_dist["high"] += 1
        elif conf >= 0.50:
            score_dist["medium"] += 1
        else:
            score_dist["low"] += 1

    conn.executemany(
        "UPDATE lexical_entries SET form2_confidence = ? WHERE entry_id = ?",
        updates,
    )
    conn.commit()
    conn.close()

    _p(f"\nConfidence scores written for {len(updates)} verb entries")
    _p(f"  High (>= 0.75):  {score_dist['high']}")
    _p(f"  Medium (0.50-0.74): {score_dist['medium']}")
    _p(f"  Low (< 0.50):    {score_dist['low']}")

    # Print category accuracy table
    _p(f"\n{'Category':<30} {'Rate':>6} {'N':>5} {'Level':>8}")
    _p("-" * 55)
    for cat_key, info in sorted(category_rates.items(), key=lambda x: -x[1]["total"]):
        if info["total"] < 3:
            continue
        rate = info["close_rate"]
        level = "HIGH" if rate >= 0.85 else ("MED" if rate >= 0.60 else "LOW")
        _p(f"  {cat_key:<28} {rate:>5.1%} {info['total']:>5} {level:>8}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 3.1 — Stem Extraction Pipeline")
    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skiri_pawnee.db")
    parser.add_argument("--db", default=default_db, help="Path to SQLite database")
    parser.add_argument("--validate", action="store_true", help="Run full validation")
    parser.add_argument("--report", action="store_true", help="Print accuracy report")
    parser.add_argument("--confidence", action="store_true",
                        help="Compute and store form2_confidence scores in the DB")
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

    if args.confidence:
        populate_confidence(args.db, verbose=args.verbose)
        return

    if args.validate or args.report:
        results = validate_all(args.db, verbose=args.verbose, limit=args.limit)
        print_report(results)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
