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
        "agent": "t",           # slot 11: 1.A (t-) — same as 1sg/1pl_excl
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
    "3":   {"sub_suffix": "aha",  "desc": "Class 3: subordinate suffix -aha"},
    "4":   {"sub_suffix": "",    "desc": "Class 4: no stem change (zero suffix)"},
    "4-i": {"sub_suffix": "",    "desc": "Class 4-i: -i (imperfective)"},
    "u":   {"sub_suffix": "a",   "desc": "Descriptive verb: suffix -a (same as class 1)"},
    "wi":  {"sub_suffix": "a",   "desc": "Locative verb: suffix -a (same as class 1)"},
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
# Suppletive Stem System
# ---------------------------------------------------------------------------
# Many verbs use different stems in dual and/or plural number.
# Keys: verb stem (singular) -> {"du_stem": ..., "pl_stem": ..., "du_incl_stem": ...}
# "du_incl_stem" is used when 1du_incl has a different stem from other duals.
# If a key is None, the singular stem is used for that number.

SUPPLETIVE_STEMS = {
    # "to come": sg aʔ, du waʔaʔ (non-sub) / waʔa (sub)
    "aʔ": {
        "du_stem": "waʔaʔ",
        "du_stem_sub": "waʔa",
        "pl_stem": None,        # plural uses sg stem + 3pl suffix
        "pl_absorbs_raak": False,  # raak- IS used in plural (preverb+stem dropped instead)
    },
    # "to do it": sg uutaar, du iitaar (incl) / uutaar (excl), pl uuhaakaa
    "uutaar": {
        "du_incl_stem": "iitaar",
        "du_stem": None,        # excl/2du/3du use sg stem
        "pl_stem": "uuhaakaar",
        "pl3_stem": "iitaar",   # 3pl uses same as du_incl (final r for Rule 23)
        "pl_absorbs_raak": True,  # raak absorbed into suppletive stem
    },
    # "to go": sg ʔat, du war, pl wuu/at
    # Agent+stem fusions in dual: t+war→tpa, s+war→spa (w→p after consonant)
    "ʔat": {
        "du_stem": "war",       # underlying 'war', final r handled by Rule 23
        "du_agent_fusions": {   # agent+stem fusions for dual
            "t": "tpa",         # 1du_excl: t- + war → tpa
            "s": "spa",         # 2du: s- + war → spa
        },
        "pl_stem": "wuu",
        "pl_absorbs_raak": False,  # raak- still needed
        "notes": "Highly irregular. Du 1du_excl/2du use special agent+stem fusions.",
    },
    # "to be good": sg hiir, du hiir (same), pl iwaa (suppletive)
    "hiir": {
        "du_stem": None,
        "pl_stem": "iwaa",
        "pl_absorbs_raak": False,  # raak- still needed before iwaa
    },
    # "to have it": sg raa, du/pl same — Class 3 uses si- for ALL non-sg
    "raa": {
        "du_stem": None,
        "pl_stem": None,
        "pl_uses_si": True,     # Class 3: plural uses si- (like dual)
        "pl_absorbs_raak": True,  # no raak- used
    },
}

# Preverb behavior in dual/plural:
# - ir- preverb: absent in du/pl for most persons (absorbed into stem complex)
# - uur- preverb: retained in dual, may combine with raak- in plural
# - ut- preverb: fused into stem (doesn't change)
PREVERB_DUAL_BEHAVIOR = {
    "ir": "absent_in_dual",     # preverb disappears, stem includes du form
    "uur": "retained",          # preverb kept
    "ut": "fused",              # already in stem
}


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

    2. Same-vowel contraction at MODE+INCLUSIVE boundary:
       ta + acir → tacir (a+a → a)

    3. r → h before consonants at morpheme boundaries:
       acir + waʔaʔ → acihwaʔaʔ (inclusive before consonant-initial stem)
    """
    if not morph_forms:
        return ""

    # Build a mapping from label to (position_in_morph_forms, form)
    # morpheme_tuples is list of (slot, label, form)
    label_to_pos = {}
    for i, m in enumerate(morpheme_tuples):
        if m[2]:  # has a form
            pos = None
            # Find position in morph_forms (match by form value)
            for j, mf in enumerate(morph_forms):
                if mf == m[2] and j not in label_to_pos.values():
                    pos = j
                    break
            if pos is not None:
                label_to_pos[m[1]] = pos

    result_parts = list(morph_forms)

    # Rule 2R: Modal + a-preverb contraction
    # When MODE ends in 'i' and the immediately following morpheme is 'a' (PREV.3.A),
    # the 'i' of the mode prefix is replaced by 'a', and the a-preverb merges.
    mode_pos = label_to_pos.get("MODE")
    prev_pos = label_to_pos.get("PREV")
    if mode_pos is not None and prev_pos is not None:
        mode_form = result_parts[mode_pos]
        prev_form = result_parts[prev_pos]
        if prev_form == "a" and mode_form.endswith("i"):
            if prev_pos == mode_pos + 1:
                # ii + a → a (subjunctive: mode disappears, preverb stays)
                if mode_form == "ii":
                    result_parts[mode_pos] = ""
                    # 'a' stays as is
                # rii + a → raa (long vowel ii → aa)
                elif mode_form.endswith("ii"):
                    result_parts[mode_pos] = mode_form[:-2] + "aa"
                    result_parts[prev_pos] = ""  # absorbed into mode
                # ti + a → ta, ri + a → ra, kaaki + a → kaaka (single i → a)
                elif mode_form.endswith("i"):
                    result_parts[mode_pos] = mode_form[:-1] + "a"
                    result_parts[prev_pos] = ""  # absorbed into mode

    # MODE + INCLUSIVE boundary contraction:
    # The initial 'a' of acir/a (inclusive prefix) is absorbed at the boundary.
    # i + acir → i + cir (a absorbed); ta + acir → ta + cir; rii + acir → rii + cir
    # kaaka + acir → kaaka + cir; etc.
    incl_pos = label_to_pos.get("INCLUSIVE")
    if mode_pos is not None and incl_pos is not None:
        incl_form = result_parts[incl_pos]
        if incl_form and incl_form.startswith("a"):
            # Find the morpheme immediately before inclusive
            pre_incl = None
            for k in range(incl_pos - 1, -1, -1):
                if result_parts[k]:
                    pre_incl = k
                    break
            if pre_incl is not None and pre_incl == incl_pos - 1:
                pre_form = result_parts[pre_incl]
                if pre_form and (pre_form.endswith("a") or pre_form.endswith("i")):
                    # Drop the initial 'a' of inclusive (it's absorbed)
                    result_parts[incl_pos] = incl_form[1:]

    # Mode vowel shortening: long vowels (ii, aa) in mode prefix shorten
    # when followed by consonant agent prefix + vowel-initial morpheme.
    # e.g., rii + t + iir → ri + t + iir = ritiir (not riitiir)
    #        aa + t + uutaar → a + t + uutaar = atuutaar (not aatuutaar)
    agent_pos = label_to_pos.get("AGENT")
    VOWELS = set("aiuAIU")
    if mode_pos is not None and agent_pos is not None:
        mode_form = result_parts[mode_pos]
        if mode_form and agent_pos == mode_pos + 1:
            shorten = False
            if mode_form.endswith("ii") or mode_form.endswith("aa"):
                # Check what follows the agent
                for k in range(agent_pos + 1, len(result_parts)):
                    if result_parts[k]:
                        if result_parts[k][0] in VOWELS:
                            shorten = True
                        break
            if shorten:
                result_parts[mode_pos] = mode_form[:-1]

    # Potential mode shortening: kuus/kaas shorten to kus/kas before POT.i + vowel
    # e.g., kuus + i + uur → kus + i + uur (kusuuhii, not kuusuuhii)
    pot_pos = label_to_pos.get("POT.i")
    if mode_pos is not None and pot_pos is not None:
        mode_form = result_parts[mode_pos]
        if mode_form in ("kuus", "kaas"):
            # Check what follows POT.i
            for k in range(pot_pos + 1, len(result_parts)):
                if result_parts[k]:
                    if result_parts[k][0] in VOWELS:
                        # Shorten: kuus → kus, kaas → kas
                        result_parts[mode_pos] = mode_form[0] + mode_form[2:]
                    break

    # GER prefix shortening: irii + ra + C(agent) + V → iri + ra + C + V
    # When the gerundial prefix irii- is followed by ra- (MODE) and then
    # a consonant agent + vowel-initial morpheme, irii shortens to iri.
    ger_pos = label_to_pos.get("GER")
    if ger_pos is not None and agent_pos is not None:
        ger_form = result_parts[ger_pos]
        if ger_form and ger_form.endswith("ii"):
            # Check if agent is followed by vowel-initial morpheme
            shorten_ger = False
            for k in range(agent_pos + 1, len(result_parts)):
                if result_parts[k]:
                    if result_parts[k][0] in VOWELS:
                        shorten_ger = True
                    break
            if shorten_ger:
                result_parts[ger_pos] = ger_form[:-1]

    # r → h before consonants at morpheme boundaries
    # This affects: acir + C... → acih + C..., and other r-final morphemes
    CONSONANTS = set("ptkcčswhʔrn")
    for i in range(len(result_parts) - 1):
        curr = result_parts[i]
        nxt = result_parts[i + 1]
        if curr and nxt and curr.endswith("r") and nxt[0] in CONSONANTS:
            # Exception: r + r → degemination (handled by unrestricted rules)
            if nxt[0] != "r":
                result_parts[i] = curr[:-1] + "h"

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


def _get_number_type(person_number):
    """Get the number type: 'sg', 'du', or 'pl'."""
    if "du" in person_number:
        return "du"
    elif "pl" in person_number:
        return "pl"
    return "sg"


def _select_stem(stem, person_number, subordinate=False):
    """Select the appropriate stem form based on number (sg/du/pl).

    Uses SUPPLETIVE_STEMS lookup for known verbs with du/pl alternations.
    Returns (actual_stem, stem_note) where stem_note describes the selection.
    """
    num_type = _get_number_type(person_number)
    suppl = SUPPLETIVE_STEMS.get(stem)

    if not suppl or num_type == "sg":
        return stem, None

    if num_type == "du":
        # Check for inclusive-specific dual stem
        if person_number == "1du_incl" and suppl.get("du_incl_stem"):
            return suppl["du_incl_stem"], "du_incl_suppletive"
        du_stem = suppl.get("du_stem")
        if subordinate and suppl.get("du_stem_sub"):
            du_stem = suppl["du_stem_sub"]
        return (du_stem or stem), ("du_suppletive" if du_stem else None)

    if num_type == "pl":
        # Check for 3pl-specific stem
        if person_number == "3pl" and suppl.get("pl3_stem"):
            return suppl["pl3_stem"], "pl3_suppletive"
        pl_stem = suppl.get("pl_stem")
        return (pl_stem or stem), ("pl_suppletive" if pl_stem else None)

    return stem, None


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
    num_type = _get_number_type(person_number)
    # Descriptive verbs WITHOUT a preverb (like "to be sick") use ku-proclitic
    # person marking. Descriptive verbs WITH a preverb (like "to be good" with
    # uur-) use standard agent prefix person marking.
    is_descriptive_ku = verb_class in ("u", "wi") and not preverb

    # --- Select stem based on number ---
    actual_stem, stem_note = _select_stem(stem, person_number, subordinate)

    # --- Proclitics ---
    # Dual proclitic: si- for 1du_excl, 2du, 3du ONLY (NOT 1du_incl)
    if pn_info.get("dual") and person_number != "1du_incl":
        morphemes.append((5, "DU", "si"))
    # Class 3 verbs: si- also used for ALL plural forms (plural = dual pattern)
    suppl_info = SUPPLETIVE_STEMS.get(stem, {})
    if num_type == "pl" and suppl_info.get("pl_uses_si"):
        morphemes.append((5, "DU", "si"))

    # Descriptive verbs (no preverb): ALL 1st-person forms use ku- INDF
    # ku- appears AFTER the mode prefix (not as a proclitic), in slot 12.5
    # (between INCLUSIVE slot 12 and PL slot 13).
    # Pattern: 1sg, 1du_incl, 1du_excl, 1pl_incl, 1pl_excl all get ku-
    # 2nd and 3rd person forms do NOT get ku-.
    if is_descriptive_ku and person_number in ("1sg", "1du_incl", "1du_excl",
                                                "1pl_incl", "1pl_excl"):
        morphemes.append((12.5, "INDF", "ku"))

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

    # Descriptive verbs (no preverb) use different person→mode mapping:
    # 1sg uses MODE.3 form (not 1/2), 2sg uses MODE.1/2, 3sg uses MODE.3
    if is_descriptive_ku:
        # Descriptive verbs (no preverb): exclusive 1st-person forms use
        # 3rd person modal form (ti- not ta- for indicative).
        # Inclusive forms (1du_incl, 1pl_incl) use 1/2 person form (ta-).
        if person_number in ("1sg", "1du_excl", "1pl_excl"):
            modal = get_modal_prefix(actual_mode, "3sg")
        else:
            modal = get_modal_prefix(actual_mode, person_number)
    else:
        modal = get_modal_prefix(actual_mode, person_number)

    # Special handling for gerundial: uses irii- + ra- compound prefix
    # Decomposed: irii (GER marker, slot 9) + ra (ABS mode, slot 10)
    if actual_mode == "gerundial":
        morphemes.append((9, "GER", "irii"))
        morphemes.append((10, "MODE", "ra"))
    else:
        if modal:
            morphemes.append((10, "MODE", modal))

    # --- Agent prefix (slot 11) ---
    # Descriptive verbs WITHOUT preverb: NO agent prefixes (person marked via ku-)
    # Potential 2nd person: kaas- already contains agent s, no separate agent
    # Class 3 pl_uses_si verbs: 1pl_incl uses acir- (no separate agent t-)
    suppl_info_agent = SUPPLETIVE_STEMS.get(stem, {})
    pl_uses_si = suppl_info_agent.get("pl_uses_si", False)
    if not is_descriptive_ku:
        agent = pn_info.get("agent", "")
        if agent:
            # Skip agent for 2nd person potential (kaas- already includes s)
            if mode == "potential" and person_number.startswith("2"):
                pass  # kaas- already contains agent s
            # Skip agent for 1pl_incl in pl_uses_si verbs (acir- handles it)
            elif pl_uses_si and person_number == "1pl_incl":
                pass  # acir- replaces agent+inclusive
            else:
                morphemes.append((11, "AGENT", agent))
    else:
        # 3sg descriptive: h- (3rd person patient marker) before stem
        if person_number == "3sg" or person_number == "3du":
            morphemes.append((11, "3PM", "h"))

    # --- Inclusive prefix (slot 12) ---
    # For descriptive verbs, inclusive still applies
    inclusive = pn_info.get("inclusive", "")
    if is_descriptive_ku and person_number in ("1pl_incl", "1du_incl"):
        # Descriptive-ku inclusive: uses aca- (not acir-)
        # Evidence: tacakukiraawaʔ (1du_incl) and tacakuraakiraawaʔ (1pl_incl)
        # show aca- not acir- before ku-. ku- already added at slot 12.5.
        morphemes.append((12, "INCLUSIVE", "aca"))
    elif pl_uses_si and person_number == "1pl_incl":
        # Class 3 pl_uses_si: 1pl_incl uses acir- (same as 1du_incl)
        # because plural collapses into dual pattern
        morphemes.append((12, "INCLUSIVE", "acir"))
    elif inclusive:
        morphemes.append((12, "INCLUSIVE", inclusive))

    # --- Plural/Possessor markers (slot 13) ---
    # In plural, raak- appears for 1/2 person (not 3pl)
    # Some verbs absorb raak- into their suppletive plural stem
    pl_marker = pn_info.get("pl_marker", "")
    if pl_marker:
        suppl = SUPPLETIVE_STEMS.get(stem, {})
        absorbs_raak = suppl.get("pl_absorbs_raak", False) if suppl else False
        if not absorbs_raak:
            # Descriptive-ku verbs: use raak only (strip ir- component)
            # because ir- is the preverb, not applicable to descriptive verbs
            if is_descriptive_ku and pl_marker == "iraak":
                morphemes.append((13, "PL", "raak"))
            else:
                morphemes.append((13, "PL", pl_marker))

    # --- Potential mode inner -i- ---
    if mode == "potential":
        morphemes.append((13.5, "POT.i", "i"))

    # --- Patient compound for du exclusive/2du ---
    # The 'ih' element in du_excl/2du comes from the preverb iir- reduced
    # to ih- in dual context. Only add when there IS a preverb ir-.
    pat_compound = pn_info.get("patient_or_compound", "")
    if pat_compound and preverb == "ir" and num_type == "du":
        # Preverb ir- becomes ih- before dual consonant-initial stems
        morphemes.append((15, "PAT_COMPOUND", pat_compound))
    elif pat_compound and not preverb:
        # For verbs without preverb, no ih element in dual
        pass
    elif pat_compound:
        morphemes.append((15, "PAT_COMPOUND", pat_compound))

    # --- Infinitive ku- (slot 16) ---
    if actual_mode in ("infinitive", "infinitive_sub"):
        morphemes.append((16, "INF.B", "ku"))

    # --- Preverb (slot 18) ---
    if preverb:
        prev_behavior = PREVERB_DUAL_BEHAVIOR.get(preverb, "retained")

        if num_type == "du" and prev_behavior == "absent_in_dual":
            # ir- preverb: for 3du use 3.A form (a-), for inclusive
            # the preverb is absorbed into acir-, for excl/2du → ih (handled above)
            if person_number == "3du":
                # 3.A preverb form in dual context
                prev_form = _get_preverb_form(preverb, person_number)
                morphemes.append((18, "PREV", prev_form))
            elif person_number == "1du_incl":
                # Preverb absorbed — acir already contains the 'ir' element
                pass
            # 1du_excl, 2du: preverb → ih (handled via PAT_COMPOUND above)
        elif num_type == "pl" and prev_behavior == "absent_in_dual":
            # ir- preverb in plural: preverb+stem are replaced by
            # raak+aahuʔ (the plural marker + 3pl suffix form the ending).
            # The preverb and stem are NOT used separately.
            if person_number == "3pl":
                prev_form = _get_preverb_form(preverb, person_number)
                morphemes.append((18, "PREV", prev_form))
            # 1pl_incl, 1pl_excl, 2pl: no preverb — raak+aahuʔ replaces it
        else:
            # Non-alternating preverbs (uur-, ut-fused): use standard form
            prev_form = _get_preverb_form(preverb, person_number)
            morphemes.append((18, "PREV", prev_form))

    # --- Agent+Stem fusions (slot 26) ---
    # Some verbs have irregular agent+stem fusions in dual/plural.
    # When a fusion exists, the agent prefix (slot 11) is removed and
    # replaced by a fused agent+stem unit.
    suppl_fusions = SUPPLETIVE_STEMS.get(stem, {})
    du_fusions = suppl_fusions.get("du_agent_fusions", {})
    agent_form = pn_info.get("agent", "")
    if num_type == "du" and agent_form and agent_form in du_fusions:
        # Replace agent + stem with fused form
        morphemes = [(s, l, f) for s, l, f in morphemes if l != "AGENT"]
        actual_stem = du_fusions[agent_form]

    # --- Stem (slot 26) ---
    # For ir- preverb verbs in 1/2 plural, the stem is not used separately
    # (raak + aahuʔ replaces preverb+stem). Check via pl_absorbs_raak flag.
    skip_stem = False
    if preverb == "ir" and num_type == "pl" and person_number != "3pl":
        skip_stem = True  # ir- verbs: raak+aahuʔ replaces preverb+stem
    if not skip_stem:
        morphemes.append((26, "STEM", actual_stem))

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
    elif aspect == "imperfective":
        # Imperfective: -huʔ (non-sub) / -hu (sub)
        if subordinate:
            morphemes.append((27, "IMPF", "hu"))
        else:
            morphemes.append((27, "IMPF", "huʔ"))

    # --- Plural suffix (aahuʔ) ---
    # For ir- preverb verbs, 1/2 plural forms also get aahuʔ (it replaces preverb+stem)
    if preverb == "ir" and num_type == "pl" and person_number != "3pl":
        if subordinate:
            morphemes.append((31, "PL_SUFFIX", "aahu"))
        else:
            morphemes.append((31, "PL_SUFFIX", "aahuʔ"))

    # --- 3pl suffix ---
    if pn_info.get("has_3pl_suffix"):
        # 3pl suffix depends on verb type:
        # - Verbs with suppletive pl3_stem: suffix absorbed into stem
        # - Descriptive verbs (class u): use -waa (non-sub) / -waara (sub)
        # - Other intransitive: use -aahuʔ/-aahu
        suppl = SUPPLETIVE_STEMS.get(stem, {})
        has_pl3_stem = suppl.get("pl3_stem") is not None if suppl else False
        uses_si_for_pl = suppl.get("pl_uses_si", False) if suppl else False

        if not has_pl3_stem and not uses_si_for_pl:
            if verb_class in ("u", "wi"):
                # Descriptive/locative verbs: 3pl marked by -waa/-waara
                if subordinate:
                    morphemes.append((31, "3PL", "waara"))
                else:
                    morphemes.append((31, "3PL", "waa"))
            else:
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
        "stem_note": stem_note,
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
# Dictionary Paradigmatic Form Validation
# ---------------------------------------------------------------------------

# Paradigmatic form definitions (from project scope):
# Form 1: 1sg indicative perfective
# Form 2: 3sg indicative perfective
# Form 3: 3sg indicative imperfective
# Form 4: 3sg absolutive subordinate perfective (gerundial)
# Form 5: 3sg indicative perfective intentive

DICT_FORM_PARAMS = {
    1: {"person_number": "1sg", "mode": "indicative", "aspect": "perfective",
        "subordinate": False, "intentive": False},
    2: {"person_number": "3sg", "mode": "indicative", "aspect": "perfective",
        "subordinate": False, "intentive": False},
    3: {"person_number": "3sg", "mode": "indicative", "aspect": "imperfective",
        "subordinate": False, "intentive": False},
    4: {"person_number": "3sg", "mode": "absolutive", "aspect": "perfective",
        "subordinate": True, "intentive": False},
    5: {"person_number": "3sg", "mode": "indicative", "aspect": "perfective",
        "subordinate": False, "intentive": True},
}


def _parse_preverb(stem_preverb):
    """Parse stem_preverb notation like '(ut...)' -> 'ut', '(ir...)' -> 'ir'.

    Returns the primary (simplest) preverb, or None.
    Complex multi-preverb entries like '(ir...ut...)' return only the outermost.
    """
    if not stem_preverb:
        return None
    # Match (PREVERB...) pattern
    m = re.match(r'^\((\w+)\.\.\.\)$', stem_preverb.strip())
    if m:
        return m.group(1)
    # Complex multi-preverb: (ir...ut...) — take first
    m = re.match(r'^\((\w+)\.\.\.', stem_preverb.strip())
    if m:
        return m.group(1)
    return None


def _parse_verb_class(vc_str):
    """Parse verb_class notation like '(1)' -> '1', '(2-i)' -> '2-i'."""
    if not vc_str:
        return None
    m = re.match(r'^\((.+)\)$', vc_str.strip())
    if m:
        return m.group(1)
    return vc_str.strip()


def _normalize_form(form):
    """Normalize a dictionary form for comparison.

    Strips accent marks, normalizes glottal stop variants, and removes
    the 'irii-'/'iriir-' prefix notation from form_4.
    """
    if not form:
        return ""
    # Remove irii-/iriir- prefix notation (form_4 often written as 'irii-raXXX')
    form = re.sub(r'^iriir?-', '', form)
    # Also handle ti- prefix notation in form_5 (e.g., 'ti-kaaʔaahista')
    form = form.replace('-', '')
    # Normalize glottal stop variants: ' (U+2019) and ' (U+2018) -> ʔ (U+0294)
    form = form.replace('\u2019', '\u0294').replace('\u2018', '\u0294')
    # Strip accent marks (acute, grave) for comparison
    import unicodedata
    result = []
    for ch in form:
        decomposed = unicodedata.normalize('NFD', ch)
        base = ''.join(c for c in decomposed
                       if unicodedata.category(c) != 'Mn')  # strip combining marks
        result.append(base)
    return ''.join(result)


def validate_dict(db_path):
    """Validate conjugation engine against dictionary paradigmatic forms.

    Loads all verb entries with paradigmatic forms from the DB,
    attempts to conjugate each using the engine, and reports results.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Load all verb entries with paradigmatic forms
    cur.execute("""
        SELECT le.entry_id, le.headword, le.stem_preverb, le.verb_class,
               le.grammatical_class,
               pf.form_number, pf.skiri_form
        FROM lexical_entries le
        JOIN paradigmatic_forms pf ON le.entry_id = pf.entry_id
        WHERE pf.skiri_form IS NOT NULL AND pf.skiri_form != ''
        AND le.grammatical_class LIKE 'V%'
        ORDER BY le.entry_id, pf.form_number
    """)

    # Group by entry
    entries = {}
    for row in cur.fetchall():
        eid, hw, sp, vc, gc, fn, sf = row
        if eid not in entries:
            entries[eid] = {
                "headword": hw, "stem_preverb": sp,
                "verb_class": vc, "gram_class": gc, "forms": {}
            }
        entries[eid]["forms"][fn] = sf

    conn.close()

    results = {
        "total": 0, "exact": 0, "exact_normalized": 0,
        "close": 0, "mismatch": 0, "skipped": 0,
        "by_form": {i: {"total": 0, "exact": 0, "exact_norm": 0, "close": 0}
                    for i in range(1, 6)},
        "by_class": {},
        "sample_mismatches": [],
    }

    for eid, info in entries.items():
        preverb = _parse_preverb(info["stem_preverb"])
        vc = _parse_verb_class(info["verb_class"])
        gc = info["gram_class"]
        hw = info["headword"]

        # Determine verb class for descriptive/locative verbs
        if not vc:
            if gc == "VD" or gc == "VD, VT":
                vc = "u"
            elif gc == "VL":
                vc = "wi"
            else:
                results["skipped"] += len(info["forms"])
                continue

        # Validate known verb classes only
        if vc not in VERB_CLASSES:
            results["skipped"] += len(info["forms"])
            continue

        # Use headword as stem (this is a simplification —
        # ut-preverb verbs need ut- fused into stem)
        stem = hw
        if preverb == "ut":
            # ut- is fused into the stem; headword IS the stem without ut-
            # For conjugation, the stem includes ut- already
            stem = "uu" + hw if not hw.startswith("uu") else hw

        # Track class stats
        class_key = f"{gc}({vc})"
        if class_key not in results["by_class"]:
            results["by_class"][class_key] = {
                "total": 0, "exact": 0, "exact_norm": 0, "close": 0
            }

        for form_num, expected in info["forms"].items():
            if form_num not in DICT_FORM_PARAMS:
                continue

            params = DICT_FORM_PARAMS[form_num]
            expected_primary = expected.split(",")[0].strip()
            # Normalize glottal stop for raw comparison
            expected_primary = expected_primary.replace('\u2019', '\u0294')
            expected_primary = expected_primary.replace('\u2018', '\u0294')

            # Skip forms with special notation (hyphens are notation, not part of form)
            if any(c in expected_primary for c in ["/", "~", "(", ")"]):
                results["skipped"] += 1
                continue
            # Remove hyphens (prefix notation like 'irii-raXXX')
            expected_primary = expected_primary.replace('-', '')

            try:
                result = conjugate(
                    stem=stem,
                    verb_class=vc,
                    mode=params["mode"],
                    person_number=params["person_number"],
                    aspect=params["aspect"],
                    preverb=preverb if preverb != "ut" else None,
                    subordinate=params["subordinate"],
                    intentive=params["intentive"],
                )
                predicted = result["surface_form"]
            except Exception as e:
                predicted = f"ERROR:{e}"

            results["total"] += 1
            results["by_form"][form_num]["total"] += 1
            results["by_class"][class_key]["total"] += 1

            # Normalize both for comparison
            pred_norm = _normalize_form(predicted)
            exp_norm = _normalize_form(expected_primary)

            edit_dist = _edit_distance(predicted, expected_primary)
            edit_dist_norm = _edit_distance(pred_norm, exp_norm)

            if predicted == expected_primary:
                results["exact"] += 1
                results["by_form"][form_num]["exact"] += 1
                results["by_class"][class_key]["exact"] += 1
            elif pred_norm == exp_norm:
                results["exact_normalized"] += 1
                results["by_form"][form_num]["exact_norm"] += 1
                results["by_class"][class_key]["exact_norm"] += 1
            elif edit_dist_norm <= 2:
                results["close"] += 1
                results["by_form"][form_num]["close"] += 1
                results["by_class"][class_key]["close"] += 1
            else:
                results["mismatch"] += 1
                if len(results["sample_mismatches"]) < 30:
                    results["sample_mismatches"].append({
                        "entry_id": eid, "headword": hw,
                        "class": class_key, "form": form_num,
                        "expected": expected_primary, "predicted": predicted,
                        "breakdown": result.get("morpheme_breakdown", "")
                            if isinstance(result, dict) else "",
                    })

    total = results["total"]
    if total == 0:
        log.info("No forms to validate.")
        return results

    exact = results["exact"]
    exact_norm = results["exact_normalized"]
    close = results["close"]
    miss = results["mismatch"]
    skip = results["skipped"]
    log.info(f"Dictionary validation: {total} forms tested, {skip} skipped")
    log.info(f"  Exact: {exact} ({100*exact/total:.1f}%)")
    log.info(f"  Exact (no accents): {exact_norm} ({100*exact_norm/total:.1f}%)")
    log.info(f"  Close (d<=2): {close} ({100*close/total:.1f}%)")
    log.info(f"  Mismatch: {miss} ({100*miss/total:.1f}%)")

    log.info(f"\n  By form:")
    for fn in range(1, 6):
        fd = results["by_form"][fn]
        if fd["total"]:
            log.info(f"    Form {fn}: {fd['exact']}/{fd['total']} exact "
                     f"({100*fd['exact']/fd['total']:.0f}%), "
                     f"+{fd['exact_norm']} norm, +{fd['close']} close")

    log.info(f"\n  By class (top 15):")
    sorted_classes = sorted(results["by_class"].items(),
                            key=lambda x: x[1]["total"], reverse=True)
    for cls, cd in sorted_classes[:15]:
        if cd["total"]:
            log.info(f"    {cls:12s}: {cd['exact']}/{cd['total']} exact "
                     f"({100*cd['exact']/cd['total']:.0f}%), "
                     f"+{cd['exact_norm']} norm, +{cd['close']} close")

    return results


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

def generate_report(report_path, validation_results=None, dict_results=None):
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

    # Dictionary validation results
    if dict_results:
        total = dict_results["total"]
        if total > 0:
            lines.append(f"\n4. DICTIONARY PARADIGMATIC FORM VALIDATION")
            lines.append(f"   Total forms tested: {total}")
            lines.append(f"   Skipped: {dict_results['skipped']}")
            lines.append(f"   Exact: {dict_results['exact']} ({100*dict_results['exact']/total:.1f}%)")
            lines.append(f"   Exact (no accents): {dict_results['exact_normalized']} "
                         f"({100*dict_results['exact_normalized']/total:.1f}%)")
            lines.append(f"   Close (d<=2): {dict_results['close']} ({100*dict_results['close']/total:.1f}%)")
            lines.append(f"   Mismatch: {dict_results['mismatch']} ({100*dict_results['mismatch']/total:.1f}%)")

            lines.append(f"\n   By form:")
            for fn in range(1, 6):
                fd = dict_results["by_form"][fn]
                if fd["total"]:
                    lines.append(f"     Form {fn}: {fd['exact']}/{fd['total']} exact "
                                 f"({100*fd['exact']/fd['total']:.0f}%), "
                                 f"+{fd['exact_norm']} norm, +{fd['close']} close")

            lines.append(f"\n   By class (top 15):")
            sorted_classes = sorted(dict_results["by_class"].items(),
                                    key=lambda x: x[1]["total"], reverse=True)
            for cls, cd in sorted_classes[:15]:
                if cd["total"]:
                    lines.append(f"     {cls:12s}: {cd['exact']}/{cd['total']} exact "
                                 f"({100*cd['exact']/cd['total']:.0f}%), "
                                 f"+{cd['exact_norm']} norm, +{cd['close']} close")

            if dict_results.get("sample_mismatches"):
                lines.append(f"\n   Sample mismatches (first 20):")
                for d in dict_results["sample_mismatches"][:20]:
                    lines.append(f"     [{d['class']}] {d['headword']} form_{d['form']}")
                    lines.append(f"       Expected:  {d['expected']}")
                    lines.append(f"       Predicted: {d['predicted']}")
                    lines.append(f"       Breakdown: {d['breakdown']}")

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

    if args.validate_dict:
        results = validate_dict(args.db)
        if args.report and results:
            generate_report(args.report, dict_results=results)
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
