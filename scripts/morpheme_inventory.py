#!/usr/bin/env python3
"""
Phase 3.1 — Morpheme Inventory & Verb Slot System
===================================================
Defines the complete Skiri Pawnee verb template based on Parks Dictionary:
  - Grammatical Overview (PDF 04, Tables 6-8, 17)
  - Abbreviations (PDF 01)
  - Appendix 1 paradigms (7 verbs × 10 modes × 11 person/number)
  - Sound change rules (Phase 2.3)

The verb template has this structure (Parks Table 6):
  PROCLITICS → INNER PREFIXES (slots 9-26) → INCORP. NOUN → STEM → SUFFIXES

Inner Prefix Template (Parks Table 7, slots 9-26):
   9  EVIDENTIALS       (wi- QUOT, ar- EV, tiir- INFR)
  10  MODALS            (ta-/ti- IND, kaaka-/kaaki- NEG, rii- ASSR, etc.)
  11  AGENT PRONOUNS    (t- 1.A, s- 2.A, Ø- 3.A) + OBVIATIVE (ir-)
  12  INCLUSIVE PRONOUNS (acir- 1.DU.IN.A, a- 1.PL.IN.A)
  13  AGENT PL/POSS/PREV (rak- 1/2.PL, ir- A.POSS/PREV.1/2, a- PREV.3.A)
  14  EVIDENTIAL        (ar- EV, second position)
  15  PATIENT PRONOUNS  (ku- 1.P, a- 2.P, Ø- 3.P, ak- 3.PL.AN.P)
  16  INFINITIVE MODAL  (ku- INF.B)
  17  PHYSICAL POSS     (ri- PHY.POSS)
  18  BEN/POSS/PREV     (ut- BEN/PREV, uur- P.POSS)
  19  RESULTATIVE/SEQ   (i- SEQ)
  20  AORIST/JUSSIVE    (uks- AOR/JUSS)
  21  ADVERBIALS        (various)
  22  AGENT PL, PAT PL  (ak- compound PL)
  23  PAT PL, POSS PL   (raar- 3.PL.INAN.P/INDV.A)
  24  INDIV AGT PL, PAT PL
  25  NOUN ± PL         (incorporated nouns)
  26  STEM              (verb stem)

Suffix Template:
  27  ASPECT            (-Ø PERF, -hus IMPF, etc.)
  28  SUBORDINATION     (-a Class 1, -i Class 2, etc.)
  29  INTENTIVE         (-ta INT)
  30  SUBORDINATE INT   (-rit INT.SUB)

Usage:
    # Show morpheme inventory:
    python scripts/morpheme_inventory.py --inventory

    # Conjugate a verb:
    python scripts/morpheme_inventory.py --conjugate "aʔ" --class 1 \\
        --mode indicative --person 3sg --aspect perfective

    # Validate against Appendix 1:
    python scripts/morpheme_inventory.py --validate

    # Validate against dictionary paradigmatic forms:
    python scripts/morpheme_inventory.py --validate-dict --db skiri_pawnee.db

    # Import inventory to DB:
    python scripts/morpheme_inventory.py --import-db --db skiri_pawnee.db

    # Generate report:
    python scripts/morpheme_inventory.py --report reports/phase_3_1_morphemes.txt

Dependencies: Python 3.8+, sqlite3 (stdlib)
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path
from datetime import datetime

# Import sound change pipeline from Phase 2.3
sys.path.insert(0, str(Path(__file__).parent))
from sound_changes import apply_sound_changes, apply_unrestricted_rules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Slot System Definition
# ---------------------------------------------------------------------------

# Proclitic slots (outer prefixes, before the inner prefix complex)
PROCLITIC_SLOTS = OrderedDict([
    (1, {"name": "QUOTATIVE",     "morphemes": {"wi": "QUOT"}}),
    (2, {"name": "DUBITATIVE",    "morphemes": {"kuur": "DUB.1", "kuruur": "DUB.2"}}),
    (3, {"name": "INFERENTIAL",   "morphemes": {"tiir": "INFR"}}),
    (4, {"name": "EVIDENTIAL",    "morphemes": {"ar": "EV"}}),
    (5, {"name": "DUAL",          "morphemes": {"si": "DU"}}),
    (6, {"name": "INDEFINITE",    "morphemes": {"ku": "INDF"}}),
    (7, {"name": "REFLEXIVE",     "morphemes": {"witii": "REFL"}}),
    (8, {"name": "NEGATIVE",      "morphemes": {
        "kara": "NEG.1", "ka": "NEG.2", "kaaku": "NEG.POSS",
        "karii...i": "EMPH.NEG"
    }}),
])

# Inner prefix slots (Parks Table 7, slots 9-26)
INNER_PREFIX_SLOTS = OrderedDict([
    (10, {"name": "MODE",         "description": "Modal prefix (required)"}),
    (11, {"name": "AGENT",        "description": "Agent pronoun / Obviative"}),
    (12, {"name": "INCLUSIVE",     "description": "Inclusive agent pronoun"}),
    (13, {"name": "AGT_PL_POSS_PREV", "description": "Agent plural / Agent possessor / Preverb"}),
    (15, {"name": "PATIENT",      "description": "Patient pronoun"}),
    (16, {"name": "INF_MODE",     "description": "Infinitive modal (ku-)"}),
    (17, {"name": "PHY_POSS",     "description": "Physical possession (ri-)"}),
    (18, {"name": "BEN_POSS_PREV", "description": "Benefactive / Patient possessor / Preverb"}),
    (19, {"name": "RESULTATIVE",  "description": "Resultative/Sequential (i-)"}),
    (20, {"name": "AORIST",       "description": "Aorist/Jussive (uks-)"}),
    (22, {"name": "COMPOUND_PL",  "description": "Compound plural markers"}),
    (23, {"name": "PAT_PL",       "description": "Patient plural / Possessor plural"}),
    (24, {"name": "INDIV_PL",     "description": "Individuative plural"}),
    (25, {"name": "NOUN",         "description": "Incorporated noun"}),
    (26, {"name": "STEM",         "description": "Verb stem (required)"}),
])

# Suffix slots
SUFFIX_SLOTS = OrderedDict([
    (27, {"name": "ASPECT",       "description": "Aspect marker"}),
    (28, {"name": "SUBORDINATION", "description": "Subordination suffix (class-dependent)"}),
    (29, {"name": "INTENTIVE",    "description": "Intentive (-ta)"}),
    (30, {"name": "SUB_INTENTIVE", "description": "Subordinate intentive (-rit)"}),
])

# ---------------------------------------------------------------------------
# Modal Prefixes (Parks Table 8)
# ---------------------------------------------------------------------------
# Keys: (mode, person_group) where person_group is "1/2" or "3"
# For modes without person distinction, both map to the same form

MODAL_PREFIXES = {
    # Non-subordinate modes
    ("indicative", "1/2"):          "ta",
    ("indicative", "3"):            "ti",
    ("negative_indicative", "1/2"): "kaaka",
    ("negative_indicative", "3"):   "kaaki",
    ("assertive", "1/2"):           "rii",
    ("assertive", "3"):             "rii",
    ("contingent", "1/2"):          "i",
    ("contingent", "3"):            "ri",
    ("potential", "1/3"):           "kuus",   # discontinuous: kuus-...-i-
    ("potential", "2"):             "kaas",   # discontinuous: kaas-...-i-
    ("absolutive", "1/2"):          "ra",
    ("absolutive", "3"):            "ra",
    ("subjunctive", "1/2"):         "aa",
    ("subjunctive", "3"):           "ii",
    ("infinitive", "1/2"):          "ra",     # discontinuous: ra-...-ku-
    ("infinitive", "3"):            "ra",
    # Subordinate modes (same prefixes as non-subordinate counterparts)
    ("contingent_sub", "1/2"):      "i",
    ("contingent_sub", "3"):        "ri",
    ("gerundial", "1/2"):           "ra",     # absolutive subordinate
    ("gerundial", "3"):             "ra",
    ("subjunctive_sub", "1/2"):     "aa",
    ("subjunctive_sub", "3"):       "ii",
    ("infinitive_sub", "1/2"):      "ra",
    ("infinitive_sub", "3"):        "ra",
}

# Potential mode has a discontinuous second element -i- in slot 13/15 area
POTENTIAL_INNER_I = True  # Flag for the -i- that appears inner to the agent prefix


# ---------------------------------------------------------------------------
# Agent/Person Prefixes (Parks, slot 11-13 + number markers)
# ---------------------------------------------------------------------------
# Structure: (person_number) -> dict of slot fillers
# The actual position depends on the slot system, but we track which slots
# get filled for each person/number combination.

PERSON_NUMBER_PREFIXES = {
    "1sg": {
        "agent": "t",           # slot 11: 1.A
        "person_group": "1/2",
    },
    "2sg": {
        "agent": "s",           # slot 11: 2.A
        "person_group": "1/2",
    },
    "3sg": {
        "agent": "",            # slot 11: Ø (3.A)
        "person_group": "3",
    },
    "1du_incl": {
        "agent": "",            # slot 11: Ø
        "inclusive": "acir",     # slot 12: 1.DU.IN.A (acir-)
        "person_group": "1/2",
        "dual": True,           # si- proclitic
    },
    "1du_excl": {
        "agent": "t",           # slot 11: 1.A (t-)
        "patient_or_compound": "ih",  # slot complex: the 'ih' element
        "person_group": "1/2",
        "dual": True,
    },
    "2du": {
        "agent": "s",           # slot 11: 2.A (s-)
        "patient_or_compound": "ih",
        "person_group": "1/2",
        "dual": True,
    },
    "3du": {
        "agent": "",            # slot 11: Ø (3.A)
        "person_group": "3",
        "dual": True,
    },
    "1pl_incl": {
        "agent": "",            # slot 11: Ø
        "inclusive": "a",        # slot 12: 1.PL.IN.A (a- for plural)
        "pl_marker": "raak",    # slot 13 or later: 1/2.PL (rak-/raak-)
        "person_group": "1/2",
    },
    "1pl_excl": {
        "agent": "t",           # slot 11: 1.A
        "pl_marker": "iraak",   # slot 13: ir- + raak-
        "person_group": "1/2",
    },
    "2pl": {
        "agent": "s",           # slot 11: 2.A
        "pl_marker": "iraak",   # slot 13: ir- + raak-
        "person_group": "1/2",
    },
    "3pl": {
        "agent": "",            # slot 11: Ø (3.A)
        "person_group": "3",
        "has_3pl_suffix": True,  # 3pl has special suffixes: -aahuʔ or -raaraʔ
    },
}


# ---------------------------------------------------------------------------
# Verb Classes and Subordination Suffixes (Parks Table 17)
# ---------------------------------------------------------------------------

VERB_CLASSES = {
    "1":   {"sub_suffix": "a",   "desc": "Class 1: subordinate suffix -a"},
    "1-a": {"sub_suffix": "a",   "desc": "Class 1-a: -a, -asta (intentive perfective)"},
    "1-i": {"sub_suffix": "i",   "desc": "Class 1-i: -i (imperfective)"},
    "2":   {"sub_suffix": "i",   "desc": "Class 2: subordinate suffix -i"},
    "2-i": {"sub_suffix": "i",   "desc": "Class 2-i: -i (imperfective)"},
    "3":   {"sub_suffix": None,  "desc": "Class 3: final syllable change"},
    "4":   {"sub_suffix": "",    "desc": "Class 4: no stem change (zero suffix)"},
    "4-i": {"sub_suffix": "",    "desc": "Class 4-i: -i (imperfective)"},
    "u":   {"sub_suffix": "u",   "desc": "Descriptive verb: suffix -u"},
    "wi":  {"sub_suffix": "wi",  "desc": "Locative verb: suffix -wi"},
}

# Aspect suffixes
ASPECT_SUFFIXES = {
    "perfective": {
        "non_sub": "",        # -Ø (zero)
        "sub": "CLASS_DEP",   # depends on verb class
        "intentive": "his",   # -his + -ta
    },
    "imperfective": {
        "non_sub": "huʔ",     # -huʔ (or -hus before other suffixes)
        "sub": "hu",           # -hu
    },
}

# 3rd person plural suffixes (non-subordinate)
THIRD_PL_SUFFIXES = {
    "default": "aahuʔ",         # most common: -aahuʔ
    "alternative": "raaraʔ",    # alternative: -raaraʔ
}

# 3rd person plural suffixes (subordinate)
THIRD_PL_SUB_SUFFIXES = {
    "default": "aahu",
    "alternative": "raara",
}


# ---------------------------------------------------------------------------
# Gerundial (Absolutive Subordinate) prefix: irii-ra-
# ---------------------------------------------------------------------------
# The gerundial mode in Appendix 1 shows forms starting with irii- + ra-
# This is the absolutive subordinate prefix (GER = ra-) combined with
# what appears to be a mode/aspect prefix irii-

GERUNDIAL_PREFIX = "iriira"  # combined irii- + ra- after sound changes


# ---------------------------------------------------------------------------
# Conjugation Engine
# ---------------------------------------------------------------------------

def get_person_group(person_number):
    """Get the person group (1/2 or 3) for modal prefix selection."""
    pn = PERSON_NUMBER_PREFIXES.get(person_number, {})
    return pn.get("person_group", "3")


def get_modal_prefix(mode, person_number):
    """Get the modal prefix for a given mode and person/number."""
    pg = get_person_group(person_number)

    # Handle potential mode's special person grouping
    if mode == "potential":
        if pg == "1/2" and person_number.startswith("2"):
            key = (mode, "2")
        else:
            key = (mode, "1/3")
    elif mode in ("indicative", "negative_indicative", "contingent",
                  "contingent_sub", "subjunctive", "subjunctive_sub"):
        key = (mode, pg)
    else:
        # assertive, absolutive, gerundial, infinitive: same for all persons
        key = (mode, pg)

    return MODAL_PREFIXES.get(key, "")


def _smart_concatenate(morph_forms, morpheme_tuples):
    """Concatenate morphemes with boundary-aware adjustments.

    Handles restricted morphophonemic rules that the generic unrestricted
    pipeline cannot handle (these are morpheme-identity-dependent):

    1. Rule 2R (Dominant a): modal prefix ti-/ri-/ii- + a-dominant preverb a-
       → ta-/ra-/a- (i replaced by a). This is a restricted rule specific
       to the mode+preverb boundary.

    2. Glottal epenthesis: when a vowel-final prefix meets a vowel-initial
       stem with no intervening morpheme, a ʔ may be inserted (for some verbs
       this is inherent in the stem, e.g., stem 'ʔat' for 'to go').
    """
    if not morph_forms:
        return ""

    # Find which morphemes are MODE vs PREV vs STEM by slot label
    slot_labels = {m[1]: (i, m[2]) for i, m in enumerate(morpheme_tuples)}

    result_parts = list(morph_forms)

    # Rule 2R: Modal + a-preverb contraction
    # When MODE ends in 'i' and the immediately following morpheme is 'a' (PREV.3.A),
    # the 'i' of the mode prefix is replaced by 'a', and the a-preverb merges.
    if "MODE" in slot_labels and "PREV" in slot_labels:
        mode_idx, mode_form = slot_labels["MODE"]
        prev_idx, prev_form = slot_labels["PREV"]

        # Check if mode and prev are adjacent (no other morpheme between them)
        # In 3sg: mode is immediately before preverb (no agent prefix)
        if prev_form == "a" and mode_form.endswith("i"):
            # Adjacency check: they must be consecutive in morph_forms
            mode_pos = morph_forms.index(mode_form) if mode_form in morph_forms else -1
            prev_pos = morph_forms.index(prev_form) if prev_form in morph_forms else -1
            if prev_pos == mode_pos + 1:
                # ti + a → ta, ri + a → ra, ii + a → a, kaaki + a → kaaka
                if mode_form == "ii":
                    result_parts[mode_pos] = ""
                    # 'a' stays as is
                elif mode_form.endswith("i"):
                    result_parts[mode_pos] = mode_form[:-1] + "a"
                    result_parts[prev_pos] = ""  # absorbed into mode

    return "".join(p for p in result_parts if p)


def _get_preverb_form(preverb, person_number):
    """Get the person-appropriate preverb form.

    Parks distinguishes PREV.1/2.A (ir-) from PREV.3.A (a-).
    Similarly, other preverbs may have alternations.
    """
    pg = get_person_group(person_number)

    # Preverb alternation: ir-/a- (from abbreviations PREV.1/2.A / PREV.3.A)
    if preverb == "ir":
        return "iir" if pg == "1/2" else "a"
    # Inherent preverb a-: always present, same form for all persons
    if preverb == "a_inherent":
        return "a"
    # ut- and uur- don't alternate by person
    return preverb


def conjugate(stem, verb_class, mode, person_number, aspect="perfective",
              preverb=None, subordinate=False, intentive=False):
    """
    Conjugate a Skiri Pawnee verb.

    Parameters:
        stem: verb stem (e.g., "aʔ" for 'come', "aar" for 'do')
        verb_class: "1", "2", "3", "4", "u", "wi", etc.
        mode: "indicative", "contingent", "assertive", etc.
        person_number: "1sg", "2sg", "3sg", "1du_incl", etc.
        aspect: "perfective" or "imperfective"
        preverb: optional preverb (e.g., "ir", "ut", "uur")
        subordinate: True for subordinate forms
        intentive: True for intentive aspect

    Returns:
        dict with 'surface_form', 'morpheme_breakdown', 'slots'
    """
    pn_info = PERSON_NUMBER_PREFIXES.get(person_number, {})
    morphemes = []  # List of (slot, label, form)

    # --- Proclitics ---
    # Dual proclitic
    if pn_info.get("dual"):
        morphemes.append((5, "DU", "si"))

    # --- Modal prefix (slot 10) ---
    actual_mode = mode
    if subordinate:
        if mode == "contingent":
            actual_mode = "contingent_sub"
        elif mode == "absolutive":
            actual_mode = "gerundial"
        elif mode == "subjunctive":
            actual_mode = "subjunctive_sub"
        elif mode == "infinitive":
            actual_mode = "infinitive_sub"

    modal = get_modal_prefix(actual_mode, person_number)

    # Special handling for gerundial: uses irii- + ra- compound prefix
    if actual_mode == "gerundial":
        morphemes.append((10, "GER", GERUNDIAL_PREFIX))
    else:
        if modal:
            morphemes.append((10, "MODE", modal))

    # --- Agent prefix (slot 11) ---
    agent = pn_info.get("agent", "")
    if agent:
        morphemes.append((11, "AGENT", agent))

    # --- Inclusive prefix (slot 12) ---
    inclusive = pn_info.get("inclusive", "")
    if inclusive:
        morphemes.append((12, "INCLUSIVE", inclusive))

    # --- Plural/Possessor markers (slot 13) ---
    pl_marker = pn_info.get("pl_marker", "")
    if pl_marker:
        morphemes.append((13, "PL", pl_marker))

    # --- Potential mode inner -i- ---
    if mode == "potential":
        morphemes.append((13.5, "POT.i", "i"))

    # --- Patient compound for du exclusive/2du ---
    pat_compound = pn_info.get("patient_or_compound", "")
    if pat_compound:
        morphemes.append((15, "PAT_COMPOUND", pat_compound))

    # --- Infinitive ku- (slot 16) ---
    if actual_mode in ("infinitive", "infinitive_sub"):
        morphemes.append((16, "INF.B", "ku"))

    # --- Preverb (slot 18) ---
    if preverb:
        prev_form = _get_preverb_form(preverb, person_number)
        morphemes.append((18, "PREV", prev_form))

    # --- Stem (slot 26) ---
    morphemes.append((26, "STEM", stem))

    # --- Suffixes ---
    # Perfective aspect: -Ø for non-subordinate, class-dependent for subordinate
    if aspect == "perfective":
        if subordinate:
            vc = VERB_CLASSES.get(verb_class, {})
            sub_suffix = vc.get("sub_suffix", "")
            if sub_suffix:
                morphemes.append((28, "SUB", sub_suffix))
        if intentive:
            morphemes.append((27, "PERF.INT", "his"))
            morphemes.append((29, "INT", "ta"))
            if subordinate:
                morphemes.append((30, "INT.SUB", "rit"))

    # --- 3pl suffix ---
    if pn_info.get("has_3pl_suffix"):
        if subordinate:
            morphemes.append((31, "3PL", "aahu"))
        else:
            morphemes.append((31, "3PL", "aahuʔ"))

    # Sort by slot number
    morphemes.sort(key=lambda x: x[0])

    # Build morpheme list
    morph_forms = [m[2] for m in morphemes if m[2]]
    morpheme_str = " + ".join(morph_forms)

    # Apply morpheme-boundary-aware concatenation before general rules.
    # We handle specific restricted interactions directly rather than
    # using the Phase 2.3 restricted rule pipeline (which was designed
    # for the analytical direction and over-triggers in synthesis).
    try:
        concat = _smart_concatenate(morph_forms, morphemes)
        surface = apply_unrestricted_rules(concat)
    except Exception:
        surface = "".join(morph_forms)

    # Build breakdown string
    breakdown = " + ".join(
        f"{m[2]}({m[1]})" for m in morphemes if m[2]
    )

    return {
        "surface_form": surface,
        "morpheme_breakdown": breakdown,
        "morpheme_string": morpheme_str,
        "slots": {m[1]: m[2] for m in morphemes},
    }


# ---------------------------------------------------------------------------
# Validation against Appendix 1
# ---------------------------------------------------------------------------

# Mapping from Appendix 1 modes to our mode/subordinate parameters
APPENDIX1_MODE_MAP = {
    "indicative_perfective": ("indicative", False),
    "negative_indicative_perfective": ("negative_indicative", False),
    "contingent_perfective": ("contingent", False),
    "assertive_perfective": ("assertive", False),
    "absolutive_perfective": ("absolutive", False),
    "potential_perfective": ("potential", False),
    "gerundial_perfective_subordinate": ("absolutive", True),
    "contingent_perfective_subordinate": ("contingent", True),
    "subjunctive_perfective_subordinate": ("subjunctive", True),
    "infinitive_perfective_subordinate": ("infinitive", True),
}

# Known verbs from Appendix 1 with their stems and classes
# Derived from page analysis: comparing 3sg forms across modes
APPENDIX1_VERBS = {
    "page_2": {
        "english": "to come",
        "stem": "aʔ",
        "preverb": "ir",
        "verb_class": "1",
        "notes": "Stem 'aʔ' with alternating preverb ir-(1/2.A) / a-(3.A)"
    },
    "page_3": {
        "english": "to do it",
        "stem": "uutaar",
        "preverb": None,
        "verb_class": "1",
        "notes": "Stem 'uutaar' (ut- fused into stem). Underlying: ut- + aar."
    },
    "page_4": {
        "english": "to go",
        "stem": "ʔat",
        "preverb": None,
        "verb_class": "1",
        "notes": "Stem 'ʔat' (irregular: epenthetic glottal for 3.A; "
                 "compensatory lengthening in 1/2.A modes ending in -a). "
                 "Suppletive: sg ʔat, du war, pl at/wuu. Needs special handling."
    },
    "page_5": {
        "english": "to be good",
        "stem": "hiir",
        "preverb": "uur",
        "verb_class": "u",
        "notes": "Descriptive verb. Stem 'hiir' with preverb uur-"
    },
    "page_6": {
        "english": "to drink it",
        "stem": "kiikaʔ",
        "preverb": None,
        "verb_class": "1",
        "notes": "Transitive, stem 'kiikaʔ'"
    },
    "page_7": {
        "english": "to be sick",
        "stem": "kiraawaʔ",
        "preverb": None,
        "verb_class": "u",
        "notes": "Descriptive verb, stem 'kiraawaʔ'. ku- indefinite proclitic for 1sg."
    },
    "page_8": {
        "english": "to have it",
        "stem": "raa",
        "preverb": None,
        "verb_class": "3",
        "notes": "Class 3 verb, stem 'raa'"
    },
}


def validate_appendix1():
    """Validate conjugation engine against Appendix 1 paradigms."""
    a1_path = Path("extracted_data/appendix1_conjugations.json")
    if not a1_path.exists():
        log.error("Appendix 1 data not found. Run extract_appendices.py --appendix1 first.")
        return None

    with open(a1_path, "r", encoding="utf-8") as f:
        a1_data = json.load(f)

    results = {
        "total": 0,
        "exact_match": 0,
        "close_match": 0,  # edit distance <= 2
        "mismatch": 0,
        "details": [],
    }

    person_numbers = ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du",
                      "1pl_incl", "1pl_excl", "2pl", "3pl"]

    for page_key, verb_info in APPENDIX1_VERBS.items():
        page_data = a1_data.get(page_key, {})
        if "modes" not in page_data:
            continue

        stem = verb_info["stem"]
        vclass = verb_info["verb_class"]
        preverb = verb_info.get("preverb")
        eng = verb_info["english"]

        for a1_mode, (our_mode, is_sub) in APPENDIX1_MODE_MAP.items():
            mode_forms = page_data.get("modes", {}).get(a1_mode, {})

            for pn in person_numbers:
                expected_data = mode_forms.get(pn, {})
                expected = expected_data.get("skiri", "") if isinstance(expected_data, dict) else str(expected_data)
                if not expected:
                    continue

                # Handle comma-separated variants (take first)
                expected_primary = expected.split(",")[0].strip()

                try:
                    result = conjugate(
                        stem=stem,
                        verb_class=vclass,
                        mode=our_mode,
                        person_number=pn,
                        aspect="perfective",
                        preverb=preverb,
                        subordinate=is_sub,
                    )
                    predicted = result["surface_form"]
                except Exception as e:
                    predicted = f"ERROR: {e}"

                results["total"] += 1
                edit_dist = _edit_distance(predicted, expected_primary)

                if predicted == expected_primary:
                    results["exact_match"] += 1
                    match_type = "EXACT"
                elif edit_dist <= 2:
                    results["close_match"] += 1
                    match_type = f"CLOSE(d={edit_dist})"
                else:
                    results["mismatch"] += 1
                    match_type = f"MISS(d={edit_dist})"

                results["details"].append({
                    "verb": eng,
                    "mode": a1_mode,
                    "person": pn,
                    "expected": expected_primary,
                    "predicted": predicted,
                    "match": match_type,
                    "breakdown": result.get("morpheme_breakdown", "") if isinstance(result, dict) else "",
                })

    # Summary
    total = results["total"]
    exact = results["exact_match"]
    close = results["close_match"]
    miss = results["mismatch"]
    log.info(f"Validation: {total} forms tested")
    log.info(f"  Exact: {exact} ({100*exact/total:.1f}%)")
    log.info(f"  Close (d<=2): {close} ({100*close/total:.1f}%)")
    log.info(f"  Mismatch: {miss} ({100*miss/total:.1f}%)")

    return results


def _edit_distance(s1, s2):
    """Compute Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if c1 == c2 else 1)
            ))
        prev = curr
    return prev[len(s2)]


# ---------------------------------------------------------------------------
# Inventory Display
# ---------------------------------------------------------------------------

def print_inventory():
    """Print the complete morpheme inventory."""
    lines = []
    lines.append("=" * 70)
    lines.append("SKIRI PAWNEE VERB MORPHEME INVENTORY")
    lines.append("=" * 70)

    lines.append("\n--- PROCLITICS (Outer Prefixes) ---")
    for slot, info in PROCLITIC_SLOTS.items():
        lines.append(f"  Slot {slot}: {info['name']}")
        for form, label in info["morphemes"].items():
            lines.append(f"    {form}- ({label})")

    lines.append("\n--- INNER PREFIXES (Slots 10-26) ---")
    for slot, info in INNER_PREFIX_SLOTS.items():
        lines.append(f"  Slot {slot}: {info['name']} — {info['description']}")

    lines.append("\n--- MODAL PREFIXES (Slot 10) ---")
    current_mode = None
    for (mode, pg), form in sorted(MODAL_PREFIXES.items()):
        if mode != current_mode:
            lines.append(f"  {mode}:")
            current_mode = mode
        lines.append(f"    {pg}: {form}-")

    lines.append("\n--- PERSON/NUMBER PREFIXES (Slots 11-13+) ---")
    for pn, info in PERSON_NUMBER_PREFIXES.items():
        parts = []
        if info.get("dual"):
            parts.append("si-(DU)")
        if info.get("agent"):
            parts.append(f"{info['agent']}-(AGENT)")
        if info.get("inclusive"):
            parts.append(f"{info['inclusive']}-(INCL)")
        if info.get("pl_marker"):
            parts.append(f"{info['pl_marker']}-(PL)")
        if info.get("patient_or_compound"):
            parts.append(f"{info['patient_or_compound']}-(PAT)")
        lines.append(f"  {pn:12s}: {' + '.join(parts) if parts else 'Ø'}")

    lines.append("\n--- VERB CLASSES & SUBORDINATION (Suffixes) ---")
    for vc, info in VERB_CLASSES.items():
        lines.append(f"  ({vc}): {info['desc']}")

    lines.append("\n--- ASPECT SUFFIXES ---")
    lines.append(f"  Perfective non-sub: -Ø (zero)")
    lines.append(f"  Perfective sub: class-dependent (-a, -i, change, -Ø)")
    lines.append(f"  Perfective intentive: -his-ta")
    lines.append(f"  Imperfective non-sub: -huʔ")
    lines.append(f"  Imperfective sub: -hu")

    lines.append("\n--- 3PL SUFFIXES ---")
    lines.append(f"  Non-subordinate: -aahuʔ / -raaraʔ")
    lines.append(f"  Subordinate: -aahu / -raara")

    lines.append("\n" + "=" * 70)

    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(report_path, validation_results=None):
    """Generate Phase 3.1 report."""
    lines = []
    lines.append("=" * 70)
    lines.append("Phase 3.1 — Morpheme Inventory & Slot System Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    # Inventory summary
    lines.append("\n1. VERB TEMPLATE STRUCTURE")
    lines.append("   Proclitics -> Inner Prefixes (18 slots) -> Noun -> STEM -> Suffixes")
    lines.append(f"   Proclitic slots: {len(PROCLITIC_SLOTS)}")
    lines.append(f"   Inner prefix slots: {len(INNER_PREFIX_SLOTS)}")
    lines.append(f"   Suffix slots: {len(SUFFIX_SLOTS)}")
    lines.append(f"   Modal prefix forms: {len(MODAL_PREFIXES)}")
    lines.append(f"   Person/number combinations: {len(PERSON_NUMBER_PREFIXES)}")
    lines.append(f"   Verb classes: {len(VERB_CLASSES)}")

    # Source data summary
    lines.append("\n2. SOURCE DATA")
    a1_path = Path("extracted_data/appendix1_conjugations.json")
    if a1_path.exists():
        with open(a1_path, "r", encoding="utf-8") as f:
            a1 = json.load(f)
        total_forms = sum(
            len(forms)
            for pk, pd in a1.items()
            if isinstance(pd, dict) and "modes" in pd
            for forms in pd["modes"].values()
        )
        lines.append(f"   Appendix 1: {total_forms} conjugated forms extracted")

    a2_path = Path("extracted_data/appendix2_irregular_roots.json")
    if a2_path.exists():
        with open(a2_path, "r", encoding="utf-8") as f:
            a2 = json.load(f)
        lines.append(f"   Appendix 2: {len(a2)} irregular verb roots")

    ab_path = Path("extracted_data/abbreviations.json")
    if ab_path.exists():
        with open(ab_path, "r", encoding="utf-8") as f:
            ab = json.load(f)
        lines.append(f"   Abbreviations: {ab.get('total_count', '?')} entries")

    gr_path = Path("extracted_data/grammatical_overview.json")
    if gr_path.exists():
        lines.append(f"   Grammatical Overview: 23 pages extracted")

    # Validation results
    if validation_results:
        lines.append("\n3. VALIDATION AGAINST APPENDIX 1")
        total = validation_results["total"]
        exact = validation_results["exact_match"]
        close = validation_results["close_match"]
        miss = validation_results["mismatch"]
        lines.append(f"   Total forms tested: {total}")
        lines.append(f"   Exact matches: {exact} ({100*exact/total:.1f}%)")
        lines.append(f"   Close matches (d<=2): {close} ({100*close/total:.1f}%)")
        lines.append(f"   Mismatches: {miss} ({100*miss/total:.1f}%)")

        # Show some mismatches
        mismatches = [d for d in validation_results["details"] if "MISS" in d["match"]]
        if mismatches:
            lines.append(f"\n   Sample mismatches (first 20):")
            for d in mismatches[:20]:
                lines.append(f"   {d['verb']:15s} {d['mode']:35s} {d['person']:12s}")
                lines.append(f"     Expected:  {d['expected']}")
                lines.append(f"     Predicted: {d['predicted']}")
                lines.append(f"     Breakdown: {d['breakdown']}")

    lines.append("\n" + "=" * 70)

    report_text = "\n".join(lines)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    log.info(f"Report saved to {report_path}")

    return report_text


# ---------------------------------------------------------------------------
# DB Import
# ---------------------------------------------------------------------------

def import_to_db(db_path):
    """Import morpheme inventory to DB."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS morpheme_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number INTEGER NOT NULL,
            slot_name TEXT NOT NULL,
            morpheme_form TEXT NOT NULL,
            label TEXT NOT NULL,
            person_constraint TEXT,
            mode_constraint TEXT,
            verb_class_constraint TEXT,
            notes TEXT,
            UNIQUE(slot_number, morpheme_form, label)
        );

        CREATE TABLE IF NOT EXISTS verb_template_slots (
            slot_number INTEGER PRIMARY KEY,
            slot_name TEXT NOT NULL,
            slot_group TEXT NOT NULL,
            description TEXT,
            required INTEGER DEFAULT 0
        );
    """)

    # Insert slot definitions
    for slot, info in PROCLITIC_SLOTS.items():
        cur.execute("""
            INSERT OR REPLACE INTO verb_template_slots
            (slot_number, slot_name, slot_group, description, required)
            VALUES (?, ?, 'proclitic', ?, 0)
        """, (slot, info["name"], f"Proclitic: {info['name']}"))

    for slot, info in INNER_PREFIX_SLOTS.items():
        required = 1 if slot in (10, 26) else 0  # Mode and Stem are required
        cur.execute("""
            INSERT OR REPLACE INTO verb_template_slots
            (slot_number, slot_name, slot_group, description, required)
            VALUES (?, ?, 'inner_prefix', ?, ?)
        """, (slot, info["name"], info["description"], required))

    for slot, info in SUFFIX_SLOTS.items():
        cur.execute("""
            INSERT OR REPLACE INTO verb_template_slots
            (slot_number, slot_name, slot_group, description, required)
            VALUES (?, ?, 'suffix', ?, 0)
        """, (slot, info["name"], info["description"]))

    # Insert modal prefix morphemes
    for (mode, pg), form in MODAL_PREFIXES.items():
        if form:
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_inventory
                (slot_number, slot_name, morpheme_form, label, person_constraint, mode_constraint)
                VALUES (10, 'MODE', ?, ?, ?, ?)
            """, (form + "-", f"MODE.{mode}", pg, mode))

    # Insert person/number morphemes
    for pn, info in PERSON_NUMBER_PREFIXES.items():
        agent = info.get("agent", "")
        if agent:
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_inventory
                (slot_number, slot_name, morpheme_form, label, person_constraint)
                VALUES (11, 'AGENT', ?, ?, ?)
            """, (agent + "-", f"AGENT.{pn}", pn))

        inclusive = info.get("inclusive", "")
        if inclusive:
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_inventory
                (slot_number, slot_name, morpheme_form, label, person_constraint)
                VALUES (12, 'INCLUSIVE', ?, ?, ?)
            """, (inclusive + "-", f"INCL.{pn}", pn))

        pl_marker = info.get("pl_marker", "")
        if pl_marker:
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_inventory
                (slot_number, slot_name, morpheme_form, label, person_constraint)
                VALUES (13, 'PL', ?, ?, ?)
            """, (pl_marker + "-", f"PL.{pn}", pn))

    # Insert verb class subordination suffixes
    for vc, info in VERB_CLASSES.items():
        sub = info.get("sub_suffix")
        if sub is not None and sub != "":
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_inventory
                (slot_number, slot_name, morpheme_form, label, verb_class_constraint, notes)
                VALUES (28, 'SUB', ?, ?, ?, ?)
            """, ("-" + sub, f"SUB.{vc}", vc, info["desc"]))

    conn.commit()

    # Count entries
    cur.execute("SELECT COUNT(*) FROM morpheme_inventory")
    count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM verb_template_slots")
    slot_count = cur.fetchone()[0]
    conn.close()

    log.info(f"Imported {count} morphemes and {slot_count} slot definitions to DB")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.1: Morpheme Inventory & Verb Slot System"
    )
    parser.add_argument("--inventory", action="store_true",
                        help="Display complete morpheme inventory")
    parser.add_argument("--conjugate", type=str, metavar="STEM",
                        help="Conjugate a verb (provide stem)")
    parser.add_argument("--class", dest="verb_class", type=str, default="1",
                        help="Verb class (default: 1)")
    parser.add_argument("--mode", type=str, default="indicative",
                        help="Mode (default: indicative)")
    parser.add_argument("--person", type=str, default="3sg",
                        help="Person/number (default: 3sg)")
    parser.add_argument("--aspect", type=str, default="perfective",
                        help="Aspect (default: perfective)")
    parser.add_argument("--preverb", type=str, default=None,
                        help="Preverb (e.g., ir, ut, uur)")
    parser.add_argument("--subordinate", action="store_true",
                        help="Subordinate form")
    parser.add_argument("--validate", action="store_true",
                        help="Validate against Appendix 1 paradigms")
    parser.add_argument("--validate-dict", action="store_true",
                        help="Validate against dictionary paradigmatic forms")
    parser.add_argument("--import-db", action="store_true",
                        help="Import morpheme inventory to DB")
    parser.add_argument("--db", type=str, default="skiri_pawnee.db",
                        help="SQLite database path")
    parser.add_argument("--report", type=str, default=None,
                        help="Generate report to file")
    args = parser.parse_args()

    if args.inventory:
        print_inventory()
        return

    if args.conjugate:
        result = conjugate(
            stem=args.conjugate,
            verb_class=args.verb_class,
            mode=args.mode,
            person_number=args.person,
            aspect=args.aspect,
            preverb=args.preverb,
            subordinate=args.subordinate,
        )
        sys.stdout.buffer.write(
            f"Surface form: {result['surface_form']}\n"
            f"Breakdown:    {result['morpheme_breakdown']}\n"
            f"Morphemes:    {result['morpheme_string']}\n"
            .encode("utf-8", errors="replace")
        )
        return

    if args.validate:
        results = validate_appendix1()
        if args.report:
            generate_report(args.report, results)
        return

    if args.import_db:
        import_to_db(args.db)
        return

    if args.report:
        generate_report(args.report)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
