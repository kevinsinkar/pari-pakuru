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
    ("negative_indicative", "1/2"): "kaakaa",
    ("negative_indicative", "3"):   "kaakii",
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
    # 3.A stem: ʔaʔ (initial glottal surfaces in non-indicative/non-negative modes)
    "aʔ": {
        "du_stem": "waʔaʔ",
        "du_stem_sub": "waʔa",
        "pl_stem": None,        # plural uses sg stem + 3pl suffix
        "pl_absorbs_raak": False,  # raak- IS used in plural (preverb+stem dropped instead)
        "3a_stem": "ʔaʔ",      # 3.A stem (glottal onset blocks vowel contraction)
        "3a_stem_sub": "ʔa",   # 3.A sub stem (sub suffix incorporated)
    },
    # "to do it": sg uutaar, du iitaar (incl) / uutaar (excl), pl uuhaakaar
    # Underlying: ut- (preverb) + aar (root). In potential mode, the preverb's
    # t palatalizes before POT.i: t+i → ci, with glottal ʔ before root (sg)
    # or raak inserted (pl). POT.i is fused into the potential stems.
    "uutaar": {
        "du_incl_stem": "iitaar",
        "du_stem": None,        # excl/2du/3du use sg stem
        "pl_stem": "uuhaakaar",
        "pl3_stem": "iitaar",   # 3pl uses same as du_incl (final r for Rule 23)
        "pl_absorbs_raak": True,  # raak absorbed into suppletive stem
        # Contingent mode: pl_stem shortens uu→u (preverb vowel doesn't lengthen)
        "contingent_pl_stem": "uhaakaar",
        # Potential mode decomposed stems (t→c palatalization + POT.i fused):
        "potential_stem": "ucíʔaar",          # sg/du_excl/2du/3du: u+cí+ʔ+aar
        "potential_du_incl_stem": "icíʔaar",  # 1du_incl: i+cí+ʔ+aar (from iitaar)
        "potential_pl_stem": "uciraakaar",    # 1/2 pl: u+ci+raak+aar (raak fused, no accent)
        "potential_pl3_stem": "iicíʔaar",     # 3pl: ii+cí+ʔ+aar (from iitaar)
    },
    # "to go": sg ʔat, du war, pl puuʔ (1/2 person) / wuuʔ (3pl)
    # Agent+stem fusions in dual: t+war→tpa, s+war→spa (w→p after consonant)
    # Plural: 1pl_excl uses ha+puuʔ, 2pl uses sta+puuʔ (same fusions as "to drink it")
    # Subordinate stem: puu (no final ʔ)
    "ʔat": {
        "du_stem": "war",       # underlying 'war', final r handled by Rule 23
        "du_agent_fusions": {   # agent+stem fusions for dual
            "t": "tpa",         # 1du_excl: t- + war → tpa
            "s": "spa",         # 2du: s- + war → spa
        },
        "du_agent_fusions_sub": {  # subordinate: preserve r before suffix
            "t": "tpar",        # 1du_excl sub: t- + war → tpar (+ a → tpara)
            "s": "spar",        # 2du sub: s- + war → spar (+ a → spara)
        },
        "pl_stem": "puuʔ",     # 1/2 person plural stem
        "pl_stem_sub": "puu",  # subordinate plural stem (no final ʔ)
        "pl3_stem": "wuuʔ",    # 3pl uses different stem
        "pl3_stem_sub": "wuu", # 3pl subordinate (no final ʔ)
        "pl3_has_preverb_a": True,  # 3pl needs 3.A preverb 'a' before wuuʔ
        "pl_absorbs_raak": False,  # raak- still needed
        "pl_agent_fusions": {   # plural agent fusions (same pattern as "to drink it")
            "1pl_excl": "ha",   # replaces t + iraak
            "2pl": "sta",       # replaces s + iraak
        },
        "notes": "Highly irregular. Du 1du_excl/2du use special agent+stem fusions.",
    },
    # "to be good": sg hiir, du hiir (same), pl iwaar (suppletive, underlying r)
    # Non-sub: iwaar → iwaa (Rule 23 final-r loss); Sub: iwaar+a → iwaara
    "hiir": {
        "du_stem": None,
        "pl_stem": "iwaar",
        "pl_absorbs_raak": False,  # raak- still needed before iwaar
    },
    # "to drink it": transitive, 3pl marked by raak- prefix (not aahuʔ suffix)
    # Stem shortens kiikaʔ → kikaʔ in subordinate + contingent modes
    "kiikaʔ": {
        "du_stem": None,
        "pl_stem": None,
        "sub_stem": "kikaʔ",       # shortened stem in sub + contingent modes
        "sub_stem_modes": {"contingent", "contingent_sub", "gerundial",
                           "subjunctive_sub", "infinitive_sub"},
        "no_3pl_suffix": True,      # 3pl uses raak prefix, not aahuʔ suffix
        "3pl_raak_prefix": True,    # add raak as 3pl prefix
        "pl_absorbs_raak": False,
        # Transitive plural: 1pl_excl uses 'ha', 2pl uses 'sta'
        # These replace agent+pl_marker
        "pl_agent_fusions": {
            "1pl_excl": "ha",       # replaces t + iraak
            "2pl": "sta",           # replaces s + iraak
        },
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
# Descriptive-ku Mode Prefix Overrides
# ---------------------------------------------------------------------------
# Descriptive-ku verbs (class u/wi without preverb, e.g., "to be sick") use a
# different mode prefix system with FOUR person categories:
#   "excl" = 1sg, 1du_excl, 1pl_excl  (uses 3.A form — existing logic)
#   "2"    = 2sg, 2du, 2pl            (special prefixes below)
#   "3"    = 3sg, 3du, 3pl            (uses 3.A form — existing logic)
#   "incl" = 1du_incl, 1pl_incl       (mode-dependent)
#
# This table lists ONLY overrides — entries that differ from the standard
# fallback (excl/3 → standard 3.A form, 2/incl → standard 1/2.A form).

DESC_KU_MODE_OVERRIDES = {
    # Contingent: 2nd and inclusive use "ra" (not standard "i");
    # 3pl uses "rii" (not "ri")
    ("contingent", "2"): "ra",
    ("contingent", "incl"): "ra",
    ("contingent", "3pl"): "rii",
    ("contingent_sub", "2"): "ra",
    ("contingent_sub", "incl"): "ra",
    ("contingent_sub", "3pl"): "rii",
    # Assertive: 2nd uses "raa" (not "rii")
    ("assertive", "2"): "raa",
    # Absolutive: excl/3/incl use "rii" (not "ra"), 2nd uses "raa"
    ("absolutive", "excl"): "rii",
    ("absolutive", "3"): "rii",
    ("absolutive", "incl"): "rii",
    ("absolutive", "2"): "raa",
    # Negative indicative: 2sg/2du uses "kaak" (not "kaaka"), 2pl keeps "kaaka"
    # Inclusive also uses "kaak" (so inclusive aca stays full, then a→u raising)
    ("negative_indicative", "2sg"): "kaak",
    ("negative_indicative", "2du"): "kaak",
    ("negative_indicative", "incl"): "kaak",
    # Desc-ku excl/3: keep short "kaaki" (underlying kaakii shortens before INDF ku)
    ("negative_indicative", "excl"): "kaaki",
    ("negative_indicative", "3"): "kaaki",
    # Infinitive: 2nd uses "raa" (not "ra"), 3rd uses "ri"
    ("infinitive", "2"): "raa",
    ("infinitive", "3"): "ri",
    ("infinitive_sub", "2"): "raa",
    ("infinitive_sub", "3"): "ri",
    # Indicative 2du/3du: use contingent-like prefixes
    ("indicative", "2du"): "ra",
    ("indicative", "3du"): "ri",
    # Potential: 2nd person uses "kus" (shortened kuus, not kaas)
    ("potential", "2"): "kus",
    # Potential: 3rd person uses "kus" (shortened kuus, not standard kuus)
    ("potential", "3"): "kus",
    # Potential: inclusive uses "kaas" (standard 2nd person form, then s-deletion
    # before inclusive handled by _smart_concatenate → kaa + cir)
    ("potential", "incl"): "kaas",
}

# Gerundial mode component (after irii-) for desc-ku:
# excl/3rd use "ri", 2nd/incl use "ra" (standard)
DESC_KU_GER_MODE = {
    "excl": "ri",
    "3": "ri",
    # "2" and "incl" use default "ra"
}

# Desc-ku 3pl prefix marker (replaces waa/waara suffix):
#   indicative: "ira", negative: "ra" (avoids i+i contraction with kaaki),
#   subjunctive: "raak", others: "raktah"
DESC_KU_3PL_PREFIX = {
    "indicative": "ira",
    "negative_indicative": "ra",
    "subjunctive_sub": "raak",
}
DESC_KU_3PL_PREFIX_DEFAULT = "raktah"

# Desc-ku plural marker for 1/2 person:
#   indicative/negative/subjunctive: "raak" (standard), others: "raktah"
DESC_KU_RAKTAH_MODES = {
    "contingent", "contingent_sub", "assertive", "absolutive",
    "gerundial", "potential", "infinitive", "infinitive_sub",
}


def _desc_ku_person_category(person_number):
    """Categorize person/number for desc-ku mode selection."""
    if person_number in ("1sg", "1du_excl", "1pl_excl"):
        return "excl"
    elif person_number.startswith("2"):
        return "2"
    elif person_number.startswith("3"):
        return "3"
    else:  # 1du_incl, 1pl_incl
        return "incl"


def _get_desc_ku_mode(mode, person_number):
    """Get the mode prefix for descriptive-ku verbs.

    Uses the DESC_KU_MODE_OVERRIDES table, then falls back to the standard
    logic where exclusive/3rd → 3.A form, 2nd/inclusive → standard 1/2 form.
    """
    cat = _desc_ku_person_category(person_number)

    # Check for person_number-specific override first (e.g., indicative 2du/3du)
    override = DESC_KU_MODE_OVERRIDES.get((mode, person_number))
    if override is not None:
        return override

    # Check category-level override
    override = DESC_KU_MODE_OVERRIDES.get((mode, cat))
    if override is not None:
        return override

    # Standard fallback: excl/3 → 3.A form, 2/incl → standard 1/2 form
    if cat in ("excl", "3"):
        return get_modal_prefix(mode, "3sg")
    else:
        return get_modal_prefix(mode, person_number)


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
        if pg == "1/2" and (person_number.startswith("2") or
                            person_number == "1du_incl"):
            # 2nd person and dual inclusive (includes listener) → kaas-
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


def _smart_concatenate(morph_forms, morpheme_tuples, preverb=None,
                       actual_mode=None):
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
    pos_to_label = {v: k for k, v in label_to_pos.items()}

    # Rule 2R: Modal + a-preverb contraction
    # When MODE ends in 'i' and the immediately following morpheme is 'a' (PREV.3.A),
    # the 'i' of the mode prefix is replaced by 'a', and the a-preverb merges.
    # Exception: negative mode (kaaki-) — the i→a change applies but the preverb
    # is NOT absorbed. This produces kaaka + a = kaakaa (long) at the boundary,
    # which is the correct form for negative 3.A with ir-preverb verbs.
    mode_pos = label_to_pos.get("MODE")
    prev_pos = label_to_pos.get("PREV")
    if mode_pos is not None and prev_pos is not None:
        mode_form = result_parts[mode_pos]
        prev_form = result_parts[prev_pos]
        if prev_form == "a" and prev_pos == mode_pos + 1:
            if mode_form.endswith("i"):
                is_negative = mode_form.startswith("kaak")
                # ii + a → aa (subjunctive 3.A: both i→a, preverb absorbed)
                if mode_form == "ii":
                    result_parts[mode_pos] = "aa"
                    result_parts[prev_pos] = ""  # absorbed into mode
                # rii + a → raa (long vowel ii → aa)
                elif mode_form.endswith("ii"):
                    result_parts[mode_pos] = mode_form[:-2] + "aa"
                    if not is_negative:
                        result_parts[prev_pos] = ""  # absorbed into mode
                # ti + a → ta, ri + a → ra, kaaki + a → kaaka (single i → a)
                elif mode_form.endswith("i"):
                    result_parts[mode_pos] = mode_form[:-1] + "a"
                    if not is_negative:
                        result_parts[prev_pos] = ""  # absorbed into mode
            elif mode_form.endswith("a"):
                # Mode already ends in 'a' (absolutive ra, gerundial ra,
                # infinitive ra): preverb 'a' is absorbed without lengthening.
                # ra + a → ra (not raa). This is specific to 3.A ir-preverb verbs.
                result_parts[prev_pos] = ""  # absorbed

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

    # Potential mode s-deletion + inclusive a-absorption:
    # kaas/kuus + acir → kaa/kuu + cir (s deleted, initial 'a' of acir absorbed)
    # This must happen as a combined operation since the a-absorption above
    # doesn't fire when mode ends in 's' (not 'a'/'i').
    if mode_pos is not None and incl_pos is not None:
        mode_form2 = result_parts[mode_pos]
        incl_form2 = result_parts[incl_pos]
        if (mode_form2 and mode_form2.endswith("s") and
                incl_form2 and incl_form2.startswith("a")):
            # Delete s from mode AND absorb initial 'a' of inclusive
            result_parts[mode_pos] = mode_form2[:-1]  # kaas → kaa
            result_parts[incl_pos] = incl_form2[1:]   # acir → cir

    # Mode vowel shortening: long modal vowel before agent + vowel/r-initial morpheme.
    # e.g., rii + t + iir → ri + t + iir = ritiir (not riitiir)
    #        aa + t + uutaar → a + t + uutaar = atuutaar (not aatuutaar)
    #        kaakaa + t + raa → kaaka + t + raa (r-initial triggers shortening too,
    #        because agent t + r → h via Rule 13, effectively opening the boundary)
    # Does NOT fire when:
    #   - Agent is followed by INCLUSIVE (a, acir) or DU inner (ih)
    #   - DU si precedes MODE and mode ends in 'ii' (dual proclitic protects
    #     long ii, e.g., si+rii stays sirii not siri; but kaakaa still shortens)
    agent_pos = label_to_pos.get("AGENT")
    du_pos = label_to_pos.get("DU")
    VOWELS = set("aiuAIUáíú")
    # DU si protects modes ending in 'ii' from shortening (not 'aa' modes)
    du_protects_ii = (du_pos is not None and mode_pos is not None
                      and du_pos == mode_pos - 1)
    if mode_pos is not None and agent_pos is not None:
        mode_form = result_parts[mode_pos]
        if mode_form and agent_pos == mode_pos + 1:
            shorten = False
            if mode_form.endswith("ii") or mode_form.endswith("aa"):
                # Skip if DU si protects ii-ending modes
                if du_protects_ii and mode_form.endswith("ii"):
                    pass  # DU si protects long ii
                else:
                    # Check what follows the agent — only shorten if it's the PREVERB
                    # or STEM starting with a vowel or 'r' (r triggers Rule 13 t→h)
                    # For INCLUSIVE: look past it to check the effective next morpheme
                    for k in range(agent_pos + 1, len(result_parts)):
                        if result_parts[k]:
                            lbl = pos_to_label.get(k)
                            # Look past INCLUSIVE to determine shortening from
                            # the effective next morpheme (works for kaakaa and rii)
                            if lbl == "INCLUSIVE":
                                continue
                            if ((result_parts[k][0] in VOWELS or result_parts[k][0] == "r")
                                    and lbl in ("PREV", "STEM", None)):
                                # Subjunctive 'aa' mode only shortens before 'u'-initial
                                # morphemes (e.g., uur-, uutaar-). It does NOT shorten
                                # before 'i'-initial (iir-) or 'r'-initial (raa-).
                                if mode_form == "aa" and result_parts[k][0] not in ("u", "U", "ú"):
                                    pass  # don't shorten
                                else:
                                    shorten = True
                            break
            if shorten:
                result_parts[mode_pos] = mode_form[:-1]

    # No-agent mode shortening: long modal vowels shorten before V/r-initial morphemes
    # when there is no AGENT morpheme. Applies to modes ending in 'ii' or 'aa' with
    # length > 2 (excludes standalone 'ii'/'aa' which behave differently).
    # Must respect DU protection (si+rii stays long) and label restrictions.
    # e.g., rii + raa → ri + raa (assertive 3sg "to have it")
    #        kaakaa + cir + uutaar → kaaka (V after inclusive)
    if mode_pos is not None and agent_pos is None:
        mode_form = result_parts[mode_pos]
        if (mode_form and len(mode_form) > 2
                and (mode_form.endswith("ii") or mode_form.endswith("aa"))):
            # DU si protects non-kaak modes ending in 'ii' from shortening
            # (e.g., si+rii stays sirii, but si+kaakii shortens to sikaaki)
            if (du_protects_ii and mode_form.endswith("ii")
                    and not mode_form.startswith("kaak")):
                pass  # DU si protects long ii (rii, etc.)
            else:
                # Find next non-empty morpheme after mode
                next_pos = None
                for k in range(mode_pos + 1, len(result_parts)):
                    if result_parts[k]:
                        next_pos = k
                        break
                if next_pos is not None:
                    next_label = pos_to_label.get(next_pos, "")
                    if mode_form.startswith("kaak"):
                        # kaakaa/kaakii modes: shorten before V/r regardless of label
                        # For kaakii specifically: also shorten before h (from r→h at
                        # morpheme boundary, e.g., 3pl PL prefix)
                        triggers = VOWELS | {"r"}
                        if mode_form.endswith("ii"):
                            triggers = triggers | {"h"}
                        # For INCLUSIVE: look past to determine from effective morpheme
                        if next_label == "INCLUSIVE":
                            for k in range(next_pos + 1, len(result_parts)):
                                if result_parts[k]:
                                    if result_parts[k][0] in triggers:
                                        result_parts[mode_pos] = mode_form[:-1]
                                    break
                        else:
                            if result_parts[next_pos][0] in triggers:
                                result_parts[mode_pos] = mode_form[:-1]
                    elif next_label == "INCLUSIVE":
                        # Non-kaak modes: look past INCLUSIVE to effective morpheme
                        # Only shorten before vowel-initial (not r-initial) stems
                        for k in range(next_pos + 1, len(result_parts)):
                            if result_parts[k]:
                                eff_label = pos_to_label.get(k, "")
                                if (eff_label in ("PREV", "STEM", None)
                                        and result_parts[k][0] in VOWELS):
                                    result_parts[mode_pos] = mode_form[:-1]
                                break
                    elif next_label in ("PREV", "STEM", None):
                        # Non-kaak modes (e.g. rii): only shorten if next is
                        # PREV/STEM (not PL prefix, DU, etc.)
                        if result_parts[next_pos][0] in VOWELS or result_parts[next_pos][0] == "r":
                            result_parts[mode_pos] = mode_form[:-1]

    # Potential mode shortening: kuus/kaas shorten to kus/kas before POT.i + vowel
    # Only when MODE is directly followed by POT.i (no agent in between).
    # e.g., kaas + i + uur → kas (2sg, agent already in kaas)
    #        kuus + i + uutaar → kus (3sg, no agent)
    # But NOT: kuus + t + i + uur → kuus stays (1sg, agent t between MODE and POT.i)
    pot_pos = label_to_pos.get("POT.i")
    if mode_pos is not None and pot_pos is not None:
        mode_form = result_parts[mode_pos]
        if mode_form in ("kuus", "kaas"):
            # Check if agent is between MODE and POT.i
            has_intervening_agent = (agent_pos is not None and
                                     agent_pos > mode_pos and
                                     agent_pos < pot_pos)
            if not has_intervening_agent:
                # Check what follows POT.i
                for k in range(pot_pos + 1, len(result_parts)):
                    if result_parts[k]:
                        if result_parts[k][0] in VOWELS:
                            # Shorten: kuus → kus, kaas → kas
                            result_parts[mode_pos] = mode_form[0] + mode_form[2:]
                        break

    # Potential mode shortening for ir-preverb 3rd person:
    # When POT.i is absent (ir-preverb potential) and MODE kuus/kaas is directly
    # followed by PREV 'aa' (no agent), shorten kuus → kus, kaas → kas.
    # Only for 3.A preverb 'aa', NOT for 1/2 preverb 'irii' (2sg keeps kaas).
    # e.g., kuus + aa + ʔaʔ → kus + aa + ʔaʔ = kusaaʔaʔ (3sg "to come")
    if mode_pos is not None and pot_pos is None and prev_pos is not None:
        mode_form = result_parts[mode_pos]
        if mode_form in ("kuus", "kaas"):
            has_intervening_agent = (agent_pos is not None and
                                     agent_pos > mode_pos and
                                     agent_pos < prev_pos)
            if not has_intervening_agent:
                prev_f = result_parts[prev_pos]
                if prev_f == "aa":
                    result_parts[mode_pos] = mode_form[0] + mode_form[2:]

    # Potential mode shortening for decomposed stems (e.g., "to do it" 3pl):
    # When POT.i is fused into the stem and stem starts with 'i', MODE still
    # shortens (kuus → kus) if no agent intervenes (same logic as POT.i shortening).
    stem_pos_sc = label_to_pos.get("STEM")
    if (mode_pos is not None and pot_pos is None and stem_pos_sc is not None
            and actual_mode == "potential"):
        mode_form = result_parts[mode_pos]
        if mode_form in ("kuus", "kaas"):
            stem_f = result_parts[stem_pos_sc]
            if stem_f and stem_f[0] in VOWELS and stem_f[0] != "u":
                has_intervening_agent = (agent_pos is not None and
                                         agent_pos > mode_pos and
                                         agent_pos < stem_pos_sc)
                if not has_intervening_agent:
                    result_parts[mode_pos] = mode_form[0] + mode_form[2:]

    # raak + p-initial stem: raak + p → raa + p (k deleted before p)
    # e.g., raak + puuʔ → raapuuʔ ("to go" plural)
    pl_pos2 = label_to_pos.get("PL")
    stem_pos3 = label_to_pos.get("STEM")
    if pl_pos2 is not None and stem_pos3 is not None:
        pl_form = result_parts[pl_pos2]
        stem_form3 = result_parts[stem_pos3]
        if pl_form and stem_form3 and pl_form.endswith("k") and stem_form3.startswith("p"):
            result_parts[pl_pos2] = pl_form[:-1]  # drop final k

    # (uur shortening now handled directly in conjugate() by person_number)

    # GER prefix shortening: irii + ra + C(agent) + V → iri + ra + C + V
    # When the gerundial prefix irii- is followed by ra- (MODE) and then
    # a consonant agent + vowel-initial morpheme, irii shortens to iri.
    ger_pos = label_to_pos.get("GER")
    if ger_pos is not None:
        ger_form = result_parts[ger_pos]
        if ger_form and ger_form.endswith("ii"):
            shorten_ger = False
            if agent_pos is not None:
                # With agent: check if agent is followed by V-initial STEM/PREV
                for k in range(agent_pos + 1, len(result_parts)):
                    if result_parts[k]:
                        if (result_parts[k][0] in VOWELS
                                and pos_to_label.get(k) in ("PREV", "STEM", None)):
                            shorten_ger = True
                        break
            elif mode_pos is not None:
                # No agent (inclusive forms): look past MODE and INCLUSIVE
                # to find effective V-initial STEM/PREV morpheme.
                # DU si between GER and MODE blocks shortening (protects long ii).
                du_blocks_ger = (du_pos is not None and ger_pos is not None
                                 and du_pos > ger_pos and du_pos < mode_pos)
                if not du_blocks_ger:
                    for k in range(mode_pos + 1, len(result_parts)):
                        if result_parts[k]:
                            lbl = pos_to_label.get(k)
                            if lbl == "INCLUSIVE":
                                continue  # look past INCLUSIVE
                            if (result_parts[k][0] in VOWELS
                                    and lbl in ("PREV", "STEM", None)):
                                shorten_ger = True
                            break
            if shorten_ger:
                result_parts[ger_pos] = ger_form[:-1]

    # INCLUSIVE r-loss before vowels: acir + V... → aci + V...
    # Parks' Rule: morpheme-final r of acir is deleted before vowel-initial morphemes.
    # Subsequent same-vowel contraction (Rule 5) merges i+i → ii.
    # e.g., acir + iitaar → aci + iitaar → (Rule 5) aciitaar
    # Exception: in potential mode, acir's r is preserved before POT.i
    # (e.g., kaaciriiwa, not kaaciiiwa)
    incl_pos2 = label_to_pos.get("INCLUSIVE")
    pot_pos2 = label_to_pos.get("POT.i")
    if incl_pos2 is not None:
        incl_form2 = result_parts[incl_pos2]
        if incl_form2 and incl_form2.endswith("r"):
            # Find next non-empty morpheme
            for k in range(incl_pos2 + 1, len(result_parts)):
                if result_parts[k]:
                    # Skip r-loss if next is POT.i (potential mode preserves r)
                    if k == pot_pos2:
                        break
                    if result_parts[k][0] in VOWELS:
                        result_parts[incl_pos2] = incl_form2[:-1]  # drop final r
                    break

    # Desc-ku inclusive a→u raising before INDF ku:
    # aca + ku → acu + ku (the final 'a' of aca raises to 'u' before ku)
    # Only applies when inclusive still starts with 'a' (i.e., initial 'a' was
    # NOT absorbed by a preceding vowel-final mode prefix).
    # e.g., kaak + aca + ku → kaak + acu + ku → kaakacuku
    # But:  ta + ca + ku → tacaku (no raising, 'ca' doesn't start with 'a')
    indf_pos = label_to_pos.get("INDF")
    if incl_pos2 is not None and indf_pos is not None:
        incl_f = result_parts[incl_pos2]
        indf_f = result_parts[indf_pos]
        if (incl_f and incl_f.startswith("a") and incl_f.endswith("a")
                and indf_f and indf_f.startswith("k")):
            # Check that INDF immediately follows INCLUSIVE (or only empty parts between)
            adjacent = True
            for k in range(incl_pos2 + 1, indf_pos):
                if result_parts[k]:
                    adjacent = False
                    break
            if adjacent:
                result_parts[incl_pos2] = incl_f[:-1] + "u"

    # Epenthetic glottal stop: si(DU) + V → siʔV
    # When the dual proclitic 'si' is followed by a vowel-initial morpheme,
    # insert ʔ. e.g., si + i → siʔi, si + aa → siʔaa
    du_pos = label_to_pos.get("DU")
    if du_pos is not None:
        du_form = result_parts[du_pos]
        if du_form == "si":
            # Find next non-empty morpheme
            for k in range(du_pos + 1, len(result_parts)):
                if result_parts[k]:
                    if result_parts[k][0] in VOWELS:
                        result_parts[du_pos] = "siʔ"
                    break

    # Glottal stop deletion after consonant (Parks' Rule 12) with
    # compensatory lengthening:
    # When a morpheme ending in a consonant (agent t-, s-) precedes a ʔ-initial
    # stem, the ʔ is deleted. e.g., t + ʔat → tat, s + ʔat → sat
    # The deleted ʔ triggers compensatory lengthening of the last vowel in the
    # nearest preceding vowel-containing morpheme:
    # e.g., ta + t + ʔat → (ʔ deleted, ta→taa) → taatat
    #        kaaka + t + ʔat → (ʔ deleted, kaaka→kaakaa) → kaakaatat
    CONSONANTS_FOR_GLOTTAL = set("ptkcčswhrnm")
    VOWELS_CL = set("aAá")  # only 'a' lengthens in compensatory lengthening
    stem_pos2 = label_to_pos.get("STEM")
    if stem_pos2 is not None:
        stem_form = result_parts[stem_pos2]
        if stem_form and stem_form.startswith("ʔ"):
            # Check preceding morpheme
            for k in range(stem_pos2 - 1, -1, -1):
                if result_parts[k]:
                    if result_parts[k][-1] in CONSONANTS_FOR_GLOTTAL:
                        result_parts[stem_pos2] = stem_form[1:]  # drop initial ʔ
                        # Compensatory lengthening: lengthen last vowel of
                        # nearest preceding vowel-containing morpheme
                        for vk in range(stem_pos2 - 1, -1, -1):
                            if result_parts[vk]:
                                morph = result_parts[vk]
                                found_vowel = False
                                for vi in range(len(morph) - 1, -1, -1):
                                    if morph[vi] in VOWELS_CL:
                                        found_vowel = True
                                        if vi == 0 or morph[vi - 1] != morph[vi]:
                                            result_parts[vk] = morph[:vi + 1] + morph[vi] + morph[vi + 1:]
                                        break
                                if found_vowel:
                                    break
                    break

    # Intervocalic ʔ-deletion in subordinate context:
    # When STEM starts with ʔ AND is preceded by a vowel-final morpheme
    # AND is followed by a vowel-initial suffix (SUB), delete the ʔ.
    # The resulting vowel sequences are resolved by unrestricted Rules 5/6/7.
    # e.g., ri + ʔat + a(SUB) → ri + at + a → riata → (Rule 7) riita
    # Does NOT apply without suffix: ri + ʔat → riʔat (ʔ preserved word-finally)
    sub_pos = label_to_pos.get("SUB")
    if stem_pos2 is not None and sub_pos is not None:
        sf = result_parts[stem_pos2]
        if sf and sf.startswith("ʔ"):
            # Check if preceded by vowel
            for k in range(stem_pos2 - 1, -1, -1):
                if result_parts[k]:
                    if result_parts[k][-1] in VOWELS:
                        result_parts[stem_pos2] = sf[1:]  # drop ʔ
                    break

    # r → h at morpheme boundaries:
    # 1. r → h before consonants (acir + C → acih + C)
    # 2. r → h before high vowels (i, u) when preceded by a vowel
    #    (Parks Ch 3.3.11: uur + iwaa → uuh + iwaa)
    # Exception: INCLUSIVE prefix 'r' (from acir) is preserved before POT.i
    # (e.g., kaaciriiwa, not kaacihiiwa)
    CONSONANTS = set("ptkcčswhʔrn")
    HIGH_VOWELS = set("iu")
    for i in range(len(result_parts) - 1):
        curr = result_parts[i]
        nxt = result_parts[i + 1]
        if curr and nxt and curr.endswith("r"):
            if nxt[0] in CONSONANTS and nxt[0] != "r":
                result_parts[i] = curr[:-1] + "h"
            elif nxt[0] in HIGH_VOWELS and len(curr) >= 2 and curr[-2] in VOWELS:
                # Skip r→h for INCLUSIVE before POT.i (acir preserved before potential i)
                if pos_to_label.get(i) == "INCLUSIVE":
                    pass
                else:
                    # r → h before i/u when preceded by vowel (VrV → VhV)
                    result_parts[i] = curr[:-1] + "h"

    # Parks' Rule 24: Final glottal stop deletion before vowel-initial suffix
    # When a stem/morpheme ends in ʔ and the next morpheme starts with a vowel,
    # delete the ʔ. e.g., kiraawaʔ + a(SUB) → kiraawaa
    # Exception: epenthetic ʔ (e.g., siʔ from DU proclitic) must be preserved.
    # Exception: short stems like "aʔ" — ʔ is etymological and preserved before
    # long suffixes (aʔ + aahuʔ → aʔaahuʔ). Only contract when followed by
    # a single-char suffix matching the pre-ʔ vowel (aʔ + a → a).
    stem_pos = label_to_pos.get("STEM")
    for i in range(len(result_parts) - 1):
        curr = result_parts[i]
        nxt = result_parts[i + 1]
        if curr and nxt and curr.endswith("ʔ") and nxt[0] in VOWELS:
            # Only apply at stem boundary or later (not to epenthetic ʔ in proclitics)
            if stem_pos is not None and i >= stem_pos:
                if i == stem_pos and len(curr) <= 2:
                    # Short stems (e.g., "aʔ"): only contract with short suffix
                    # aʔ + a(SUB) → a (contraction); aʔ + aahuʔ → aʔaahuʔ (preserve)
                    # Note: 3.A stem "ʔaʔ" (len 3) is NOT short — its final ʔ deletes
                    # Exception: preserve ʔ when more suffixes follow after SUB
                    # (e.g., 3PL aahu — the ʔ blocks unwanted vowel contraction)
                    # But NOT in infinitive mode (INF.B ku present) where stem
                    # contracts differently
                    has_more_suffixes = any(
                        result_parts[j] for j in range(i + 2, len(result_parts))
                    )
                    in_infinitive = "INF.B" in label_to_pos
                    if ((not has_more_suffixes or in_infinitive)
                            and len(nxt) <= 2 and len(curr) >= 2
                            and curr[-2] == nxt[0]):
                        result_parts[i] = curr[:-1]  # delete ʔ
                        result_parts[i + 1] = nxt[1:] if len(nxt) > 1 else ""
                    # else: preserve ʔ (don't delete)
                else:
                    # Long stems: standard ʔ deletion
                    result_parts[i] = curr[:-1]

    # Agent+Preverb boundary protection:
    # When AGENT ends in 't' and PREV starts with 'r' (potential rii),
    # insert a boundary marker to prevent Rule 13 (t→h before r) from firing.
    # The marker is stripped after apply_unrestricted_rules in conjugate().
    if agent_pos is not None and prev_pos is not None:
        ag = result_parts[agent_pos]
        pv = result_parts[prev_pos]
        if ag and pv and ag.endswith("t") and pv.startswith("r"):
            result_parts[agent_pos] = ag + TR_MARKER

    # --- Accent mark placement for ir-preverb verbs ---
    if preverb == "ir":
        _apply_ir_accents(result_parts, pos_to_label, label_to_pos,
                          actual_mode=actual_mode)

    return "".join(p for p in result_parts if p)


def _apply_ir_accents(parts, pos_to_label, label_to_pos,
                      actual_mode=None):
    """Apply accent marks for ir-preverb verb forms (e.g., 'to come').

    Modifies parts in place. Accented vowels (á, í, ú) are already in the
    VOWELS set used by sound_changes.py, so they survive apply_unrestricted_rules.

    Rules derived from Appendix 1 paradigm analysis (85 accented forms):
    - Infinitive mode: only INF.B ku -> kú
    - Other modes: agent-adjacent short i, inclusive i, mode prefix i,
      GER initial i, DU si (neg/abs/assr-3), POT.i second i
    """
    infb_pos = label_to_pos.get("INF.B")
    ger_pos = label_to_pos.get("GER")
    mode_pos = label_to_pos.get("MODE")
    agent_pos = label_to_pos.get("AGENT")
    incl_pos = label_to_pos.get("INCLUSIVE")
    du_pos = label_to_pos.get("DU")
    pot_pos = label_to_pos.get("POT.i")

    # Detect singular: no DU, PL, INCLUSIVE, PL_SUFFIX, or AGENT_PL morphemes
    is_sg = all(lbl not in label_to_pos
                for lbl in ("DU", "PL", "INCLUSIVE", "PL_SUFFIX", "AGENT_PL"))

    # --- Infinitive mode: only INF.B accent ---
    if infb_pos is not None:
        f = parts[infb_pos]
        if f and "u" in f:
            idx = f.index("u")
            parts[infb_pos] = f[:idx] + "ú" + f[idx + 1:]
        # In infinitive mode, no other accents apply
        return

    # --- GER accent: first i -> í ---
    if ger_pos is not None:
        f = parts[ger_pos]
        if f and "i" in f:
            idx = f.index("i")
            parts[ger_pos] = f[:idx] + "í" + f[idx + 1:]

    # --- MODE accent ---
    if mode_pos is not None:
        f = parts[mode_pos]
        # Contingent: mode "i" -> "í" ONLY for sg (1sg/2sg)
        if f == "i" and is_sg:
            parts[mode_pos] = "í"
        # Assertive: mode "ri"/"rii" -> "rí"/"ríi"
        # NOT when directly followed by INCLUSIVE (no AGENT) = 1du_incl
        elif f and len(f) >= 2 and f[:2] == "ri":
            has_agent_or_no_incl = (agent_pos is not None or incl_pos is None)
            if has_agent_or_no_incl:
                parts[mode_pos] = "r" + "í" + f[2:]

    # --- Agent-adjacent accent ---
    # After agent consonant (t/s), accent the first 'i' of the next morpheme
    # if it's short i (ih, iraak, irii). NOT for long ii (iir = sg preverb).
    if agent_pos is not None:
        for k in range(agent_pos + 1, len(parts)):
            if parts[k]:
                nxt = parts[k]
                nxt_label = pos_to_label.get(k, "")
                # Short i: PAT_COMPOUND (ih), PL (iraak), PREV (irii)
                if (nxt.startswith("i") and not nxt.startswith("ii")
                        and nxt_label in ("PAT_COMPOUND", "PL", "PREV")):
                    parts[k] = "í" + nxt[1:]
                break
    else:
        # No separate AGENT label: check if MODE ends with agent consonant
        # (e.g., potential 2sg: kaas embeds agent s)
        if mode_pos is not None:
            mf = parts[mode_pos]
            if mf and mf.endswith("s"):
                for k in range(mode_pos + 1, len(parts)):
                    if parts[k]:
                        nxt = parts[k]
                        nxt_label = pos_to_label.get(k, "")
                        if (nxt.startswith("i") and not nxt.startswith("ii")
                                and nxt_label in ("PAT_COMPOUND", "PL", "PREV")):
                            parts[k] = "í" + nxt[1:]
                        break

    # --- Inclusive accent ---
    # Accent the 'i' in inclusive morpheme (cir -> cír, ci -> cí)
    if incl_pos is not None:
        f = parts[incl_pos]
        if f and "i" in f:
            idx = f.index("i")
            parts[incl_pos] = f[:idx] + "í" + f[idx + 1:]

    # --- POT.i accent ---
    # When inclusive is also present, accent the last 'i' of POT.i (ii -> ií)
    if pot_pos is not None and incl_pos is not None:
        f = parts[pot_pos]
        if f and "i" in f:
            idx = f.rindex("i")
            parts[pot_pos] = f[:idx] + "í" + f[idx + 1:]

    # --- DU si accent ---
    # Accent si -> sí in negative and absolutive modes, or assertive 3A (no agent).
    # Uses actual_mode to distinguish absolutive 'ra' from contingent-contracted 'ra'.
    if du_pos is not None:
        du_f = parts[du_pos]
        if du_f and du_f.startswith("si"):
            accent_si = False
            if actual_mode in ("negative_indicative", "negative"):
                accent_si = True
            elif actual_mode == "absolutive":
                accent_si = True
            elif actual_mode == "assertive" and agent_pos is None:
                accent_si = True
            if accent_si:
                parts[du_pos] = "sí" + du_f[2:]


# Boundary marker to protect t+r from Rule 13 at agent+preverb boundary
TR_MARKER = "\x02"


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


def _select_stem(stem, person_number, subordinate=False, actual_mode=None):
    """Select the appropriate stem form based on number (sg/du/pl).

    Uses SUPPLETIVE_STEMS lookup for known verbs with du/pl alternations.
    Returns (actual_stem, stem_note) where stem_note describes the selection.
    """
    num_type = _get_number_type(person_number)
    suppl = SUPPLETIVE_STEMS.get(stem)

    if not suppl:
        return stem, None

    # Potential mode decomposed stems (e.g., "to do it" ut+aar → uciʔaar)
    # These have POT.i fused via palatalization: t+i → ci
    if actual_mode == "potential":
        pot_key = None
        if person_number == "1du_incl":
            pot_key = "potential_du_incl_stem"
        elif person_number == "3pl":
            pot_key = "potential_pl3_stem"
        elif num_type == "pl":
            pot_key = "potential_pl_stem"
        elif num_type in ("sg", "du"):
            pot_key = "potential_stem"
        if pot_key and suppl.get(pot_key):
            pot_stem = suppl[pot_key]
            # 1sg potential: no accent on the palatalized ci
            if person_number == "1sg":
                pot_stem = pot_stem.replace("í", "i")
            return pot_stem, pot_key

    # Contingent mode: some verbs shorten pl_stem (e.g., uuhaakaar → uhaakaar)
    if actual_mode in ("contingent", "contingent_sub") and num_type == "pl":
        cont_pl = suppl.get("contingent_pl_stem")
        if cont_pl and person_number != "3pl":
            return cont_pl, "contingent_pl_stem"

    # Stem alternation (e.g., kiikaʔ → kikaʔ in specific modes)
    base_stem = stem
    if suppl.get("sub_stem"):
        sub_modes = suppl.get("sub_stem_modes")
        if sub_modes and actual_mode in sub_modes:
            base_stem = suppl["sub_stem"]
        elif not sub_modes and subordinate:
            base_stem = suppl["sub_stem"]

    # 3.A stem: initial glottal onset surfaces in non-indicative/non-negative modes.
    # - Standard: only 3sg uses ʔaʔ (e.g., contingent 3sg raʔaʔ)
    # - Potential: ALL sg persons AND 3du/3pl use ʔaʔ (e.g., potential 1sg kuustíriiʔaʔ)
    # - Infinitive: ALL sg persons AND 3du/3pl use ʔaʔ/ʔa (e.g., infinitive 1sg ratihkuʔa)
    if suppl.get("3a_stem") and actual_mode not in ("indicative", "negative_indicative"):
        use_3a = False
        if actual_mode == "potential":
            # Potential: 3.A stem for all sg + 3rd person du/pl
            if num_type == "sg" or person_number.startswith("3"):
                use_3a = True
        elif actual_mode in ("infinitive", "infinitive_sub"):
            # Infinitive: 3.A stem for all sg only (du/pl use suppletive stems)
            if num_type == "sg":
                use_3a = True
        elif person_number == "3sg":
            # Other modes: only 3sg
            use_3a = True
        elif actual_mode == "gerundial" and person_number == "3pl":
            # Gerundial 3pl: 3.A stem (ʔ onset blocks boundary contraction)
            use_3a = True
        if use_3a:
            if subordinate and suppl.get("3a_stem_sub"):
                return suppl["3a_stem_sub"], "3a_stem_sub"
            return suppl["3a_stem"], "3a_stem"

    if num_type == "sg":
        return base_stem, ("sub_stem" if base_stem != stem else None)

    if num_type == "du":
        # Check for inclusive-specific dual stem
        if person_number == "1du_incl" and suppl.get("du_incl_stem"):
            return suppl["du_incl_stem"], "du_incl_suppletive"
        du_stem = suppl.get("du_stem")
        used_sub_stem = False
        if subordinate and suppl.get("du_stem_sub"):
            du_stem = suppl["du_stem_sub"]
            used_sub_stem = True
        tag = "du_suppletive_sub" if used_sub_stem else ("du_suppletive" if du_stem else ("sub_stem" if base_stem != stem else None))
        return (du_stem or base_stem), tag

    if num_type == "pl":
        # Check for 3pl-specific stem
        if person_number == "3pl" and suppl.get("pl3_stem"):
            pl3 = suppl["pl3_stem"]
            pl3_sub = False
            if subordinate and suppl.get("pl3_stem_sub"):
                pl3 = suppl["pl3_stem_sub"]
                pl3_sub = True
            return pl3, ("pl3_suppletive_sub" if pl3_sub else "pl3_suppletive")
        pl_stem = suppl.get("pl_stem")
        pl_sub = False
        if subordinate and suppl.get("pl_stem_sub"):
            pl_stem = suppl["pl_stem_sub"]
            pl_sub = True
        tag = "pl_suppletive_sub" if pl_sub else ("pl_suppletive" if pl_stem else ("sub_stem" if base_stem != stem else None))
        return (pl_stem or base_stem), tag

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

    # Compute actual_mode early (needed for stem selection)
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

    # --- Select stem based on number ---
    actual_stem, stem_note = _select_stem(stem, person_number, subordinate, actual_mode=actual_mode)

    # --- Proclitics ---
    # Dual proclitic: si- for 1du_excl, 2du, 3du ONLY (NOT 1du_incl)
    # In gerundial mode, si- goes AFTER irii- (slot 9.5) not before it (slot 5).
    # Expected: irii-si-ra-... (e.g., iriisiratuutaara), NOT si-irii-ra-...
    if pn_info.get("dual") and person_number != "1du_incl":
        if actual_mode == "gerundial":
            # Desc-ku gerundial: si goes AFTER mode (irii + MODE + si + ...)
            # Standard gerundial: si goes between GER and MODE (irii + si + MODE + ...)
            if is_descriptive_ku:
                morphemes.append((10.5, "DU", "si"))
            else:
                morphemes.append((9.5, "DU", "si"))
        else:
            morphemes.append((5, "DU", "si"))
    # Class 3 verbs: si- also used for ALL plural forms (plural = dual pattern)
    # In gerundial mode, si- goes after irii- (slot 9.5)
    suppl_info = SUPPLETIVE_STEMS.get(stem, {})
    if num_type == "pl" and suppl_info.get("pl_uses_si"):
        if actual_mode == "gerundial":
            morphemes.append((9.5, "DU", "si"))
        else:
            morphemes.append((5, "DU", "si"))

    # Descriptive verbs (no preverb): ALL 1st-person forms use ku- INDF
    # ku- appears AFTER the mode prefix (not as a proclitic), in slot 12.5
    # (between INCLUSIVE slot 12 and PL slot 13).
    # Pattern: 1sg, 1du_incl, 1du_excl, 1pl_incl, 1pl_excl all get ku-
    # 2nd and 3rd person forms do NOT get ku-.
    # In assertive mode, ku lengthens to kuu.
    if is_descriptive_ku and person_number in ("1sg", "1du_incl", "1du_excl",
                                                "1pl_incl", "1pl_excl"):
        ku_form = "kuu" if mode in ("assertive", "potential") else "ku"
        morphemes.append((12.5, "INDF", ku_form))

    # --- Modal prefix (slot 10) ---
    # (actual_mode already computed above for stem selection)

    # Descriptive-ku verbs use a four-way person category system for mode
    # prefixes (excl/2/3/incl) via _get_desc_ku_mode(), which handles all
    # overrides including absolutive rii-, contingent ra-, assertive raa-, etc.
    if is_descriptive_ku:
        modal = _get_desc_ku_mode(actual_mode, person_number)
    else:
        modal = get_modal_prefix(actual_mode, person_number)

    # Special handling for gerundial: uses irii- + MODE compound prefix
    # Decomposed: irii (GER marker, slot 9) + mode (slot 10)
    # For desc-ku: excl/3rd use "ri", 2nd/incl use "ra"
    # For standard verbs: always "ra"
    # Flag: ir-preverb gerundial sg skips MODE (and 1sg also skips AGENT)
    ger_ir_skip_mode = False
    ger_ir_skip_agent = False
    if actual_mode == "gerundial":
        morphemes.append((9, "GER", "irii"))
        if is_descriptive_ku:
            cat = _desc_ku_person_category(person_number)
            ger_mode = DESC_KU_GER_MODE.get(cat, "ra")
        else:
            ger_mode = "ra"
        # ir-preverb sg 1sg/2sg: skip MODE ra (preverb follows GER directly)
        # 1sg: GER + PREV + stem_sub (no mode, no agent)
        # 2sg: GER + AGENT + PREV + stem_sub (no mode)
        if preverb == "ir" and num_type == "sg" and person_number in ("1sg", "2sg"):
            ger_ir_skip_mode = True
            if person_number == "1sg":
                ger_ir_skip_agent = True
        if not ger_ir_skip_mode:
            morphemes.append((10, "MODE", ger_mode))
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
            # Skip agent for gerundial 1sg ir-preverb (GER directly precedes preverb)
            if ger_ir_skip_agent:
                pass  # 1sg gerundial ir-preverb: no agent
            # Skip agent for 2nd person potential (kaas- already includes s)
            elif mode == "potential" and person_number.startswith("2"):
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

    # --- Plural agent fusions (transitive verbs) ---
    # Some transitive verbs replace agent+pl_marker with a fused form
    # e.g., "to drink it": 1pl_excl ha (not t+iraak), 2pl sta (not s+iraak)
    # BUT: potential and infinitive modes use standard agent+iraak pattern
    pl_fusions = SUPPLETIVE_STEMS.get(stem, {}).get("pl_agent_fusions", {})
    pl_fusions_applied = False
    if person_number in pl_fusions and mode not in ("potential", "infinitive"):
        # Remove the agent prefix we just added
        morphemes = [(s, l, f) for s, l, f in morphemes if l != "AGENT"]
        # Add fused form as combined agent+pl marker (slot 11)
        morphemes.append((11, "AGENT_PL", pl_fusions[person_number]))
        pl_fusions_applied = True

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
    elif preverb == "uur" and num_type == "pl" and person_number == "1pl_incl":
        # uur preverb verbs: inclusive 'a' is absorbed — uur takes its place
        # e.g., tatuuraakiwaa = ta + t + uur + raak + iwaa (no separate 'a')
        pass
    elif (preverb == "ir" and person_number == "1pl_incl"
              and actual_mode in ("potential", "potential_sub")):
        # ir-preverb potential 1pl_incl: inclusive 'a' absorbed into preverb 'aa'.
        # s-deletion from mode would incorrectly fire if INCLUSIVE label present.
        # The preverb 'aa' already encodes inclusive + preverb contributions.
        pass
    elif (stem_note == "potential_pl_stem" and person_number == "1pl_incl"):
        # Decomposed potential plural stem already has raak fused in;
        # inclusive 'a' would cause unwanted u-domination (a+u→uu).
        # Agent t is retained instead of inclusive pattern.
        pass
    elif inclusive:
        # Infinitive 1pl_incl: INCLUSIVE 'a' lengthens to 'aa' before INF.B ku
        # (compensatory lengthening at morpheme boundary)
        if (person_number == "1pl_incl"
                and actual_mode in ("infinitive", "infinitive_sub")
                and inclusive == "a"):
            morphemes.append((12, "INCLUSIVE", "aa"))
        else:
            morphemes.append((12, "INCLUSIVE", inclusive))

    # --- Plural/Possessor markers (slot 13) ---
    # In plural, raak- appears for 1/2 person (not 3pl)
    # Some verbs absorb raak- into their suppletive plural stem
    pl_marker = pn_info.get("pl_marker", "")
    if pl_marker and not pl_fusions_applied:
        suppl = SUPPLETIVE_STEMS.get(stem, {})
        absorbs_raak = suppl.get("pl_absorbs_raak", False) if suppl else False
        if not absorbs_raak:
            # Descriptive-ku verbs: use raak or raktah depending on mode
            if is_descriptive_ku and pl_marker in ("iraak", "raak"):
                if actual_mode in DESC_KU_RAKTAH_MODES:
                    morphemes.append((13, "PL", "raktah"))
                else:
                    morphemes.append((13, "PL", "raak"))
            # uur preverb verbs: iraak → raak (ir- component absorbed by preverb)
            elif preverb == "uur" and pl_marker == "iraak":
                morphemes.append((13, "PL", "raak"))
            # Infinitive mode: iraak → raak (ir- component dropped)
            elif actual_mode in ("infinitive", "infinitive_sub") and pl_marker == "iraak":
                morphemes.append((13, "PL", "raak"))
            else:
                morphemes.append((13, "PL", pl_marker))

    # 3pl raak prefix: for transitive verbs where 3pl is marked by raak- prefix
    # rather than aahuʔ suffix. In 3pl, raak contracts to h.
    # e.g., "to drink it" 3pl: ti + h + kiikaʔ = tihkiikaʔ
    suppl_3pl = SUPPLETIVE_STEMS.get(stem, {})
    if person_number == "3pl" and suppl_3pl.get("3pl_raak_prefix"):
        morphemes.append((13, "PL", "h"))

    # Descriptive-ku 3pl: uses a PREFIX marker (ira/raktah/raak) before stem
    # instead of a suffix (waa/waara) after stem.
    # Potential 3pl uses "riktah" (not "raktah") as the i-colored variant.
    if is_descriptive_ku and person_number == "3pl":
        if mode == "potential":
            morphemes.append((13, "PL", "riktah"))
        else:
            pl3_marker = DESC_KU_3PL_PREFIX.get(actual_mode, DESC_KU_3PL_PREFIX_DEFAULT)
            morphemes.append((13, "PL", pl3_marker))

    # --- Potential mode inner -i- ---
    # POT.i is "ii" (long) after INCLUSIVE prefix (e.g., kaaciriikiikaʔ),
    # "i" (short) otherwise (e.g., kuustikiikaʔ).
    # For desc-ku: POT.i goes BEFORE INDF ku (slot 12.4), and desc-ku 2nd
    # person uses "aa" instead of POT.i, while 3rd person adds "rii" after.
    # When stem has potential_* decomposition, POT.i is fused into the stem
    # via palatalization (t+i→ci), so skip adding it separately.
    if mode == "potential":
        if stem_note and stem_note.startswith("potential_"):
            pass  # POT.i fused into decomposed potential stem
        elif is_descriptive_ku:
            cat = _desc_ku_person_category(person_number)
            if cat == "2":
                # 2nd person desc-ku potential: "aa" replaces POT.i
                morphemes.append((12.4, "POT.i", "aa"))
            elif cat == "3":
                # 3rd person desc-ku potential: POT.i + "rii" (absolutive marker)
                # For 3pl, no DESC_3PM — the plural marker handles 3rd person
                morphemes.append((12.4, "POT.i", "i"))
                if person_number != "3pl":
                    morphemes.append((12.45, "DESC_3PM", "rii"))
            elif cat == "excl":
                # Exclusive: POT.i before INDF
                morphemes.append((12.4, "POT.i", "i"))
            # Inclusive: no POT.i (kaas→kaa before aca, then kuu directly)
        elif preverb == "ir" and person_number != "1du_incl":
            # ir-preverb potential: irii/aa preverb replaces POT.i entirely
            # Exception: 1du_incl keeps POT.i (acir already contains ir)
            pass
        else:
            has_inclusive = pn_info.get("inclusive") is not None
            pot_i_form = "ii" if has_inclusive else "i"
            morphemes.append((13.5, "POT.i", pot_i_form))

    # --- Patient compound for du exclusive/2du ---
    # The 'ih' element in du_excl/2du comes from the preverb iir- reduced
    # to ih- in dual context. Only add when there IS a preverb ir-.
    # NOT added for uur- or other preverbs.
    pat_compound = pn_info.get("patient_or_compound", "")
    if pat_compound and preverb == "ir" and num_type == "du":
        # Preverb ir- becomes ih- before dual consonant-initial stems
        # In potential mode, rii preverb replaces PAT_COMPOUND ih
        if actual_mode not in ("potential", "potential_sub"):
            morphemes.append((15, "PAT_COMPOUND", pat_compound))

    # --- Infinitive ku- ---
    # In plural forms, ku- comes BEFORE the PL marker (slot 12.9).
    # In non-plural forms, ku- is at standard slot 16.
    # e.g., ratkuraakikaa = ra + t + ku + raak + kikaʔ + a
    # For desc-ku: INF.B ku suppressed only for du 1st-person forms
    # (where INDF ku already present and inclusive/dual context merges them).
    # 1sg keeps both ku's (INDF + INF.B), e.g., rakukukiraawaa.
    if actual_mode in ("infinitive", "infinitive_sub"):
        suppress_inf_ku = (is_descriptive_ku and num_type == "du"
                           and person_number in ("1du_incl", "1du_excl"))
        if not suppress_inf_ku:
            if num_type == "pl":
                morphemes.append((12.9, "INF.B", "ku"))
            else:
                morphemes.append((16, "INF.B", "ku"))

    # --- Preverb (slot 18) ---
    if (preverb and preverb == "ir"
            and actual_mode in ("infinitive", "infinitive_sub")
            and num_type != "du"):
        # Infinitive mode ir-preverb: ih for 1/2 person, a for 3rd person
        # Placed BEFORE INF.B ku: slot 12.85 for pl (ku at 12.9), 15 for sg (ku at 16)
        # Uses label INF_PREV to avoid mode+preverb absorption in _smart_concatenate
        # Du forms handled by standard logic (PAT_COMPOUND ih for excl/2du,
        # acir for 1du_incl, 3du preverb at slot 15)
        pg = get_person_group(person_number)
        if pg == "1/2" and person_number != "1pl_incl":
            inf_prev_form = "ih"
        else:
            inf_prev_form = "a"
        if num_type == "pl":
            # All plural: preverb before INF.B ku at 12.9
            morphemes.append((12.85, "INF_PREV", inf_prev_form))
        else:
            morphemes.append((15, "INF_PREV", inf_prev_form))
    elif (preverb and preverb == "ir"
            and actual_mode in ("potential", "potential_sub")
            and person_number != "1du_incl"):
        # Potential mode ir-preverb: irii for 1/2 person, aa for 3rd + 1pl_incl
        # Preverb retained for ALL persons (unlike other modes that drop for 1/2 pl)
        # Exception: 1du_incl — acir already contains ir, uses standard POT.i logic
        pg = get_person_group(person_number)
        if pg == "1/2" and person_number != "1pl_incl":
            pot_prev_form = "irii"
        else:
            pot_prev_form = "aa"
        # Plural non-3pl: slot 12.8 (before PL at slot 13)
        if num_type == "pl" and person_number != "3pl":
            morphemes.append((12.8, "PREV", pot_prev_form))
        else:
            morphemes.append((18, "PREV", pot_prev_form))
    elif preverb:
        prev_behavior = PREVERB_DUAL_BEHAVIOR.get(preverb, "retained")

        if num_type == "du" and prev_behavior == "absent_in_dual":
            # ir- preverb: for 3du use 3.A form (a-), for inclusive
            # the preverb is absorbed into acir-, for excl/2du → ih (handled above)
            if person_number == "3du":
                # 3.A preverb form in dual context
                prev_form = _get_preverb_form(preverb, person_number)
                # In infinitive: preverb goes BEFORE INF.B ku (slot 15)
                if actual_mode in ("infinitive", "infinitive_sub"):
                    morphemes.append((15, "INF_PREV", prev_form))
                else:
                    morphemes.append((18, "PREV", prev_form))
            elif person_number == "1du_incl":
                # Preverb absorbed — acir already contains the 'ir' element.
                # In potential mode, POT.i 'ii' provides the vowel component.
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
        elif person_number == "1du_incl" and preverb == "uur":
            # 1du_incl with uur preverb: uur reduces to just 'i'
            # (the 'ir' element in acir absorbs the preverb, leaving residual 'i')
            # e.g., ta + ci + i + hiir → taciihii
            morphemes.append((18, "PREV", "i"))
        else:
            # Non-alternating preverbs (uur-, ut-fused): use standard form
            prev_form = _get_preverb_form(preverb, person_number)
            # uur preverb in plural: place BEFORE raak (slot 12.8, before PL slot 13)
            # 1pl_incl: uur stays full; 1pl_excl/2pl: uur → u (shortened)
            # 3pl: standard slot 18
            if preverb == "uur" and num_type == "pl":
                if person_number == "3pl":
                    morphemes.append((18, "PREV", prev_form))
                elif person_number in ("1pl_excl", "2pl"):
                    morphemes.append((12.8, "PREV", "u"))  # shortened
                else:  # 1pl_incl
                    morphemes.append((12.8, "PREV", prev_form))  # full uur
            else:
                morphemes.append((18, "PREV", prev_form))

    # --- 3pl preverb 'a' for suppletive pl3_stem ---
    # "to go" 3pl: stem wuuʔ needs 3.A preverb 'a' to produce tiiwuuʔ, raawuuʔ
    # (ti+a→tii via Rule 7, ra+a→raa via Rule 5). But contingent ri+a→rii would
    # overshoot — for contingent 3pl, the preverb should NOT apply (riwuuʔ expected).
    suppl_prev_a = SUPPLETIVE_STEMS.get(stem, {})
    if person_number == "3pl" and suppl_prev_a.get("pl3_has_preverb_a"):
        # Add 3.A preverb 'a' — but NOT for contingent mode (ri already short)
        # Use PREV_3A label so Rule 2R (dominant a) doesn't fire on this boundary;
        # normal vowel contraction Rules 5/7 will handle it instead.
        if mode not in ("contingent", "contingent_sub"):
            morphemes.append((18, "PREV_3A", "a"))

    # --- Agent+Stem fusions (slot 26) ---
    # Some verbs have irregular agent+stem fusions in dual/plural.
    # When a fusion exists, the agent prefix (slot 11) is removed and
    # replaced by a fused agent+stem unit.
    suppl_fusions = SUPPLETIVE_STEMS.get(stem, {})
    du_fusions_key = "du_agent_fusions_sub" if subordinate else "du_agent_fusions"
    du_fusions = suppl_fusions.get(du_fusions_key, suppl_fusions.get("du_agent_fusions", {}))
    agent_form = pn_info.get("agent", "")
    if (num_type == "du" and agent_form and agent_form in du_fusions
            and mode not in ("potential", "infinitive")):
        # Replace agent + stem with fused form
        # NOT in potential/infinitive modes — standard agent + stem used
        morphemes = [(s, l, f) for s, l, f in morphemes if l != "AGENT"]
        actual_stem = du_fusions[agent_form]
        # When agent is fused into stem, negative mode kaakaa must shorten
        # to kaaka (agent no longer visible for _smart_concatenate shortening).
        # e.g., kaakaa + tpa → kaaka + tpa = sikaakatpa (not sikaakaatpa)
        morphemes = [(s, l, (f[:-1] if l == "MODE" and f == "kaakaa" else f))
                     for s, l, f in morphemes]

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
    # Skip SUB suffix if stem already incorporates subordinate change (du_stem_sub, etc.)
    stem_has_sub = stem_note and "_sub" in stem_note
    if aspect == "perfective":
        if subordinate and not stem_has_sub:
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
        # - Verbs with suppletive pl_stem: 3pl uses pl_stem, no aahuʔ suffix
        # - Verbs marked no_3pl_suffix: 3pl marked by prefix, not suffix
        # - Descriptive verbs (class u): use -waa (non-sub) / -waara (sub)
        # - Other intransitive: use -aahuʔ/-aahu
        suppl = SUPPLETIVE_STEMS.get(stem, {})
        has_pl3_stem = suppl.get("pl3_stem") is not None if suppl else False
        uses_si_for_pl = suppl.get("pl_uses_si", False) if suppl else False
        has_pl_stem = suppl.get("pl_stem") is not None if suppl else False
        no_3pl_suffix = suppl.get("no_3pl_suffix", False) if suppl else False

        if not has_pl3_stem and not uses_si_for_pl and not has_pl_stem and not no_3pl_suffix:
            if is_descriptive_ku:
                # Desc-ku 3pl uses prefix-based marking (added above), no suffix
                pass
            elif verb_class in ("u", "wi"):
                # Descriptive/locative verbs WITH preverb: 3pl marked by -waa/-waara
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
        concat = _smart_concatenate(morph_forms, morphemes, preverb=preverb,
                                    actual_mode=actual_mode)
        surface = apply_unrestricted_rules(concat)
        surface = surface.replace(TR_MARKER, "")
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
