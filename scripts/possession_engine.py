#!/usr/bin/env python3
"""
Phase 3.1.5 — Noun Possession Engine
======================================

Generates possessive forms for Skiri Pawnee nouns by filling the appropriate
slots in the existing verb template (morpheme_inventory.py).

ARCHITECTURE DECISION: Possession in Skiri is fundamentally *verbal*, not
nominal. "My head" is not head+prefix — it's a verb phrase meaning "here is
my head (sitting)." Therefore this module generates slot-fill dicts that
plug into the existing conjugation engine rather than building a parallel
concatenation system.

Four possession systems:
  1. Kinship (N-KIN)     — pure lookup, suppletive stems
  2. Body part (N-DEP)   — verb incorporation with ri- (PHY.POSS) in slot 17
  3. Agent (general N)   — gerundial possessive verb + independent noun
  4. Patient possession  — uur- in slot 18 when non-agent owns the noun

INTEGRATION POINTS WITH morpheme_inventory.py:
  - Uses the same slot numbering (Table 7: slots 10-26)
  - Calls _smart_concatenate for morpheme assembly (or fallback)
  - Calls apply_sound_changes for surface form (or fallback)
  - Shares pronominal prefix tables (Table 9)
  - Shares NOMINAL_SUFFIXES for stem extraction

Usage:
    # Standalone (uses built-in fallback concatenator)
    python possession_engine.py --test
    python possession_engine.py --generate paksuʔ --person 1sg
    python possession_engine.py --generate atiraʔ --person 2sg

    # When wired into morpheme_inventory.py, import and call:
    from possession_engine import generate_possessive, PossessionResult
    result = generate_possessive("paksuʔ", person="1sg", noun_class="N-DEP")
"""

import json
import os
import sys
import re
import argparse
import io
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Force UTF-8 output on Windows (cp1252 can't encode glottal stops, IPA, etc.)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Try to import the real 24-rule sound change pipeline from Phase 2.3.
#
# INTEGRATION NOTE (Phase 3.1.5 Round 2):
#   The possession engine needs the SOUND CHANGE pipeline, not the full
#   conjugation engine. sound_changes.apply_sound_changes(morphemes) takes
#   a simple list of morpheme strings and returns the surface form after
#   applying all 24 rules (restricted + concatenation + unrestricted).
#
#   We do NOT use morpheme_inventory._smart_concatenate because:
#     (a) its signature requires (morph_forms, morpheme_tuples, preverb,
#         actual_mode) — tuple-based tracking for the verb conjugation pipeline
#     (b) possession constructions are simpler and don't need preverb
#         alternation or compensatory lengthening logic
#     (c) apply_sound_changes already handles Rules 2R, 8R, 12R etc.
#         at morpheme boundaries via apply_restricted_rules()
# ---------------------------------------------------------------------------
_HAS_SOUND_ENGINE = False
_KS_MARKER = "\x01"  # same marker used in sound_changes.py to protect ks from Rule 17
try:
    from sound_changes import (
        apply_sound_changes as sc_apply_sound_changes,
        apply_unrestricted_rules as sc_apply_unrestricted_rules,
        KS_MARKER as _KS_MARKER,
    )
    _HAS_SOUND_ENGINE = True
except ImportError:
    pass

# Backward-compat alias for code that checks _HAS_MORPHEME_ENGINE
_HAS_MORPHEME_ENGINE = _HAS_SOUND_ENGINE

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = REPO_ROOT / "extracted_data"
KINSHIP_FILE = EXTRACTED_DIR / "appendix3_kinship.json"


# ===========================================================================
#  SLOT NUMBERS — from Parks Table 7 (The Inner Prefix Template)
#
#  These MUST match the slot numbers used in morpheme_inventory.py.
#  The scope doc confirms this layout:
#    Proclitics (1-8): QUOT, DUB, INFR, EV, DU, INDF, REFL, NEG
#    Inner (9-26): EVID, MODE, AGENT, INCLUSIVE, [ku-INDF@12.5],
#                  PL/POSS/PREV, EVID, PATIENT, INF.B, PHY.POSS,
#                  BEN/PREV, SEQ, AOR, ADV, PL, PL, PL, NOUN, STEM
#    Suffixes (27-30): ASPECT, SUB, INTENT, SUB.INTENT
# ===========================================================================

class Slot:
    # Proclitics
    DU = 5           # si- dual
    INDF_PROC = 6    # ku- indefinite (original position; moved to 12.5 in engine)

    # Inner prefixes
    MODE = 10        # ta- (IND.1/2), ti- (IND.3), ra- (ABS/GER), etc.
    AGENT = 11       # t- (1sg), s- (2sg), Ø (3sg)
    INCLUSIVE = 12    # acir- (1du_incl), a- (1pl_incl)
    INDF = 12.5      # ku- indefinite (moved here per scope doc)
    A_POSS_PREV = 13 # ir-/a- agent possessive / preverb
    PATIENT = 15     # ku- (1sg.P), a- (2sg.P)
    INF_B = 16       # ku- infinitive modal
    PHY_POSS = 17    # ri- physical possession
    BEN_PREV = 18    # uur- patient possession / ut- benefactive / preverb
    AOR = 20         # uks- aorist
    NOUN = 25        # incorporated noun stem (± raar- PL)
    STEM = 26        # verb root

    # Suffixes
    ASPECT = 27      # Ø (PERF), -huʔ (IMPF), etc.
    SUB = 28         # subordination suffix


# ===========================================================================
#  PRONOMINAL PREFIXES — from Parks Table 9
# ===========================================================================

# Agent prefixes (slot 11)
AGENT_PREFIX = {
    "1sg":      "t",
    "2sg":      "s",
    "3sg":      "",       # Ø — zero morpheme
    "1du_incl": "",       # uses INCLUSIVE slot instead (acir- in slot 12)
    "1du_excl": "t",
    "1pl_incl": "",       # uses INCLUSIVE a- in slot 12; scope says agent t- suppressed for Class 3
    "1pl_excl": "t",
}

# Patient prefixes (slot 15)
PATIENT_PREFIX = {
    "1sg":      "ku",
    "2sg":      "a",
    "3sg":      "",       # Ø
    "1du_incl": "aca",
}

# Inclusive prefixes (slot 12)
INCLUSIVE_PREFIX = {
    "1du_incl": "acir",
    "1pl_incl": "a",
}

# Agent possessive prefix (slot 13) — used in Systems 2 & 3
# Alternates: ir- for 1st/2nd person, a- for 3rd person
A_POSS_PREFIX = {
    "1sg":      "ir",
    "2sg":      "ir",
    "3sg":      "a",
    "1du_incl": "ir",
    "1du_excl": "ir",
    "1pl_incl": "ir",     # possibly a- for inclusive; needs verification
    "1pl_excl": "ir",
}

# Mode prefixes (slot 10)
MODE_PREFIX = {
    "indicative_1_2":  "ta",   # 1st/2nd person agent
    "indicative_3":    "ti",   # 3rd person agent
    "absolutive":      "ra",   # interrogative / gerundial
    "gerundial":       "ra",   # subordinate absolutive = gerundial
    "negative_1_2":    "kaakaa",
    "negative_3":      "kaaki",
    "assertive":       "rii",
}


# ===========================================================================
#  POSITION VERBS — for body-part possession (System 2)
# ===========================================================================

# Blue Book Lesson 5: head "sits" (+ku), most other body parts "hang" (+ta)
POSITION_VERBS = {
    "ku":   {"meaning": "sitting", "applies_to": "head, round objects"},
    "ta":   {"meaning": "hanging", "applies_to": "most body parts, limbs"},
    "arit": {"meaning": "standing", "applies_to": "torso, upright objects"},
}

# Map specific body-part stems to their position verb
# Source: Blue Book Lesson 5 dialogues + Parks dictionary N-DEP entries
#
# Position verb assignment rules (BB Lesson 5, p.22):
#   ku  (sitting)  — head, round objects
#   ta  (hanging)  — "almost every other part of your body hangs"
#   arit (standing) — torso, upright body parts
#
# Stems marked [BB] are Blue Book attested; [PD] are Parks Dictionary.
# Where BB and PD have different stems for the same body part (e.g.,
# haka [BB] vs haakaʔ [PD] for "mouth"), both are included.
BODY_PART_POSITION = {
    # --- HEAD region (ku = sitting) ---
    "paks":          "ku",    # [BB] head
    "astihaar":      "ku",    # [PD] crown of the head, pate

    # --- EYES ---
    "kirik":         "ta",    # [BB] eye
    "kiriik":        "ta",    # [PD] eye (Parks headword kiriikuʔ)
    "kaackaawiʔ":    "ta",    # [PD] white of the eye

    # --- NOSE ---
    "tsusu":         "ta",    # [BB] nose
    "cus":           "ta",    # [PD] nose (Parks headword cusuʔ)

    # --- MOUTH ---
    "haka":          "ta",    # [BB] mouth
    "haakaʔ":        "ta",    # [PD] mouth (Parks headword haakaʔuʔ)
    "haakaratawiʔ":  "ta",    # [PD] mouth opening, orifice
    "hatkatakus":    "ta",    # [PD] roof of the mouth, palatal region

    # --- EAR ---
    "itkahaar":      "ta",    # [PD] ear

    # --- THROAT / NECK ---
    "tsiksu":        "ta",    # [BB] throat/heart
    "kitut":         "ta",    # [PD] throat (N-DEP headword kitut-)
    "raruuc":        "ta",    # [PD] throat, larynx
    "paahiks":       "ta",    # [PD] throat, front part of the neck

    # --- HAND / FINGERS ---
    "iks":           "ta",    # [BB] hand
    "kskitsu":       "ta",    # [BB] finger
    "ikskiic":       "ta",    # [PD] finger (Parks headword ikskiicuʔ)
    "ikskakus":      "ta",    # [PD] palm of the hand
    "ikskatahc":     "ta",    # [PD] palm of the hand (variant)
    "kskiiciikawiʔ": "ta",    # [PD] middle finger
    "kskiicpita":    "ta",    # [PD] little finger, pinky

    # --- FOOT / LEG ---
    "as":            "ta",    # [BB] foot
    "askitsu":       "ta",    # [BB] toe
    "kasu":          "ta",    # [BB] leg
    "paa":           "ta",    # [PD] knee (N-DEP headword paa-)
    "askakiiriit":   "ta",    # [PD] heel of the foot
    "askatahc":      "ta",    # [PD] sole of the foot
    "asikitahaah":   "ta",    # [PD] instep of the foot

    # --- TORSO / ABDOMEN ---
    "kararu":        "ta",    # [BB] stomach/belly
    "karaar":        "ta",    # [PD] belly, abdomen, stomach (Parks headword karaaruʔ)
    "kickaraar":     "ta",    # [PD] abdomen, stomach
    "pakuus":        "ta",    # [PD] belly, abdomen, stomach

    # --- HAIR ---
    "usu":           "ta",    # [BB] hair
    "uus":           "ta",    # [PD] hair (Parks headword uusuʔ)
    "uuskaraar":     "ta",    # [PD] hairline, hair on the head
    "uuspiraar":     "ta",    # [PD] growing hair
    "ckuur":         "ta",    # [PD] wool, shaggy hair
    "raac":          "ta",    # [PD] pubic hair
    "hatkahuur":     "ta",    # [PD] part (as in hair)

    # --- BUTTOCKS ---
    "rusu":          "ta",    # [BB] buttocks
    "ripiit":        "ta",    # [PD] buttock, cheek

    # --- VOICE (abstract body function) ---
    "wak":           "ta",    # [PD] voice, sound, speech (N-DEP headword wak-)
}

# Default position verb for body parts not in the lookup
DEFAULT_BODY_POSITION = "ta"  # hanging — most body parts


# ===========================================================================
#  RELATIONAL / LOCATIVE NOUNS — N-DEP stems that are NOT body parts
# ===========================================================================
# These dependent stems are incorporated into verbs as spatial/locative
# modifiers. They are NOT independently possessed — you don't say "my inside"
# or "my road", you say "inside the house" or "standing in the road."
#
# Blue Book examples:
#   ka- "in, inside" → ti•kaku' "he's inside (sitting)"
#   hatur- "road" + ka- → ti•hatuh•kaarit "he's standing in the road"
#
# Stems NOT in this dict and NOT in BODY_PART_POSITION fall through to
# agent possession (System 3) as the default for N-DEP.

LOCATIVE_NOUNS = {
    # --- Spatial / locative stems ---
    "hat":    {"meaning": "hole", "type": "locative",
              "example": None},
    "hatawi": {"meaning": "hole", "type": "locative",
              "example": None, "variants": ["ratawi"]},
    "ratawi": {"meaning": "hole", "type": "locative",
              "example": None, "variants": ["hatawi"]},
    "hatuur": {"meaning": "path, trail; road", "type": "locative",
              "example": "ti\u2022hatuh\u2022kaarit \u2018he\u2019s standing in the road\u2019",
              "variants": ["hatuh"]},
    "hatuh":  {"meaning": "path, trail; road", "type": "locative",
              "example": "ti\u2022hatuh\u2022kaarit \u2018he\u2019s standing in the road\u2019",
              "variants": ["hatuur"]},
}

# Non-body N-DEP stems that route to agent possession (System 3).
# Listed here for documentation — they are NOT locative and are possessable
# via the general agent system ("my horse", "my food", etc.).
#
# Incorporable nouns (food, animals, natural phenomena, cultural products):
#   aras-      cooked food
#   asaa-/asa- horse; dog
#   haak-/rak- wood; tree
#   haas-/has- line; rope, cord
#   hiihis-    night (24-hour period)
#   iriwis-    war party; troop
#   rut-       snake
#   saak-      sun; day
#   tariir-    seam
#
# Abstract / body-related (not physical body parts):
#   aciks-     spirit, mind, thoughts; throat
#   iir-       carcass; corpse
#   iit-       body (living or dead); corpse
#   awi-       fleeting image; quick motion
#   raa-       way, custom, tradition
#   uhur-      way, behavior; image, shape


# ===========================================================================
#  NOMINAL SUFFIX STRIPPING — for stem extraction
# ===========================================================================

def extract_noun_stem(headword: str) -> Tuple[str, Optional[str]]:
    """
    Strip nominal suffix to recover the bound stem for incorporation.

    Returns (stem, suffix_stripped) where stem has trailing '-' removed.

    When a noun incorporates into a verb, it drops its independent-form
    suffix (Grammatical Overview p. 13):
        -uʔ  (absolutive, most common)
        -kis (diminutive)
        -kiʔ (diminutive variant)
        -kusuʔ (augmentative)

    Examples:
        iksuʔ   → iks     (hand)
        paksuʔ  → paks    (head)
        kirikuʔ → kirik   (eye)
        akaruʔ  → akar    (house)
        asaakiʔ → asaa    (dog, < asaa- + -kis DIM)
    """
    hw = headword.strip()

    # Strip trailing hyphen (bound-stem notation)
    if hw.endswith("-"):
        hw = hw[:-1]

    # Augmentative -kusuʔ (check first — longest)
    if hw.endswith("kusuʔ") and len(hw) > 5:
        return hw[:-5], "-kusuʔ"

    # Locative/relational -iriʔ (e.g., askatahciriʔ -> askatahc "sole")
    if hw.endswith("iriʔ") and len(hw) > 4:
        return hw[:-4], "-iriʔ"

    # Absolutive -uʔ (most common)
    if hw.endswith("uʔ") and len(hw) > 2:
        return hw[:-2], "-uʔ"

    # Diminutive -kiʔ
    if hw.endswith("kiʔ") and len(hw) > 3:
        return hw[:-3], "-kiʔ"

    # Diminutive -kis
    if hw.endswith("kis") and len(hw) > 3:
        return hw[:-3], "-kis"

    # No recognized suffix — return whole word (kinship, irregular)
    return hw, None


# ===========================================================================
#  SOUND CHANGE FALLBACK
#
#  Minimal sound change rules for standalone operation. When wired into
#  morpheme_inventory.py, these are replaced by the full 24-rule pipeline.
# ===========================================================================

def _fallback_concatenate(morphemes: List[str]) -> str:
    """
    Concatenate morphemes with basic Skiri sound changes.

    Implements only the rules visible in Blue Book possession examples.
    The real engine (morpheme_inventory._smart_concatenate) handles all 24
    rules from Parks Ch. 3. When available, use that instead.

    Rules applied here (from Blue Book + Grammatical Overview):
        Rule 2R:  a + i → a  (dominant a absorbs following i)
        Rule 4R:  i + u → u  (i drops before u; BB p.22 "ti+ku+iks=tiku'ks")
        Rule 8R:  r → t after {p,t,k,s,c}  (BB p.6 "rakis+rahkata=rakistahkata")
        Rule 12R: r → h before consonant  (BB p.13 "hir+wa=hihwa")
    """
    result = ""
    for morph in morphemes:
        if not morph:
            continue
        if not result:
            result = morph
            continue

        # Junction: last char of result + first char of morph
        if result and morph:
            last = result[-1]
            first = morph[0]

            # Rule 4R: i + u → u (i drops)
            if last == "i" and first == "u":
                result = result[:-1]

            # Rule 2R: a + i → a (dominant a)
            elif last == "a" and first == "i":
                morph = morph[1:]  # drop the i

            # Rule 8R: r → t after hard consonant
            elif last in "ptksc" and first == "r":
                morph = "t" + morph[1:]

            # Rule 12R: r → h before consonant
            elif last == "r" and first in "ptkscwhrbm":
                result = result[:-1] + "h"

        result += morph

    return result


def _fallback_apply_sound_changes(form: str) -> str:
    """
    Apply post-assembly sound changes for standalone mode.
    In integrated mode, use sound_changes.apply_pipeline() instead.
    """
    # Rule 24: glottal stop deletion between identical consonants
    # (minimal — the real pipeline is much more comprehensive)
    return form


def _apply_pipeline(morphemes: List[str]) -> str:
    """
    Apply the full sound change pipeline to a morpheme list.

    When the real engine (sound_changes.py) is available, this calls
    apply_sound_changes() which does:
        1. Restricted rules (morpheme-boundary-aware: 1R, 2R, 3R, 8R, 10R-12R)
        2. Concatenation (join modified morphemes)
        3. Unrestricted rules (string-level: 5-7, 13-24)

    In standalone mode, falls back to the 4-rule concatenator.
    """
    # Filter out empty morphemes before processing
    clean = [m for m in morphemes if m]
    if not clean:
        return ""

    if _HAS_SOUND_ENGINE:
        return sc_apply_sound_changes(clean)
    return _fallback_apply_sound_changes(_fallback_concatenate(clean))


# Legacy aliases — kept for any external callers
def concatenate(morphemes: List[str]) -> str:
    """Concatenate morphemes (legacy wrapper — use _apply_pipeline instead)."""
    clean = [m for m in morphemes if m]
    if _HAS_SOUND_ENGINE:
        # apply_sound_changes does concat + all rules in one pass
        return sc_apply_sound_changes(clean)
    return _fallback_concatenate(clean)


def apply_sc(form: str) -> str:
    """Post-concatenation sound changes (legacy wrapper).

    When using the real engine, this is a no-op because _apply_pipeline
    already applied all rules. Kept for backward compatibility.
    """
    if _HAS_SOUND_ENGINE:
        # Already applied in _apply_pipeline / concatenate — identity
        return form
    return _fallback_apply_sound_changes(form)


# ===========================================================================
#  DATA STRUCTURES
# ===========================================================================

@dataclass
class PossessionResult:
    """Result of generating a possessive form."""
    system: str                    # "kinship", "body_part", "agent", "patient"
    person: str                    # "1sg", "2sg", "3sg", etc.
    headword: str                  # original noun headword
    stem: str                      # extracted noun stem
    surface_form: str              # final surface form
    slot_fills: Dict               # slot → morpheme mapping
    morpheme_sequence: List[str]   # ordered morphemes before sound changes
    morpheme_labels: List[str]     # parallel labels for each morpheme
    gloss: str                     # English gloss of the construction
    is_attested: bool = False      # True if from kinship appendix / BB
    confidence: str = "computed"   # "attested" / "high" / "medium" / "low"
    notes: str = ""


# ===========================================================================
#  SYSTEM 1: KINSHIP POSSESSION — Pure lookup
# ===========================================================================

_kinship_cache: Optional[Dict] = None

def _load_kinship() -> Dict:
    """Load and index kinship paradigms from appendix3."""
    global _kinship_cache
    if _kinship_cache is not None:
        return _kinship_cache

    _kinship_cache = {}
    if not KINSHIP_FILE.exists():
        return _kinship_cache

    with open(KINSHIP_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("terms", []):
        if "category" in item and "terms" in item:
            for sub in item["terms"]:
                _index_kinship_term(sub)
        else:
            _index_kinship_term(item)

    # Load BB-attested supplements not in Appendix 3
    _load_kinship_supplements()

    return _kinship_cache


# ---------------------------------------------------------------------------
# KINSHIP SUPPLEMENTS — terms attested in Blue Book but not in Appendix 3
#
# These are added to the kinship cache after loading the appendix data.
# Source: Blue Book Lesson 7
# ---------------------------------------------------------------------------
KINSHIP_SUPPLEMENTS = [
    {
        "english_term": "son (male speaker)",
        "skiri_term": "tikiʔ",
        "possessive_forms": {
            "my": "tikiʔ",
            "your": None,
            "his_her": None,
        },
        "notes": "1sg only attested in BB Lesson 7. Not in Appendix 3.",
    },
    {
        "english_term": "daughter (male speaker)",
        "skiri_term": "tsuwat",
        "possessive_forms": {
            "my": "tsuwat",
            "your": None,
            "his_her": None,
        },
        "notes": "1sg only attested in BB Lesson 7. Not in Appendix 3.",
    },
    {
        "english_term": "niece/nephew (female speaker)",
        "skiri_term": "swat",
        "possessive_forms": {
            "my": None,
            "your": "swat",
            "his_her": None,
        },
        "notes": "2sg only; BB form uses s- agent prefix where Parks has a-/awaat. Not in Appendix 3.",
    },
]


def _load_kinship_supplements():
    """Add BB-attested kinship terms not in Appendix 3 to the cache."""
    global _kinship_cache
    if _kinship_cache is None:
        _kinship_cache = {}

    for term in KINSHIP_SUPPLEMENTS:
        pf = term.get("possessive_forms", {})
        entry = {
            "english": term.get("english_term", ""),
            "stem": term.get("skiri_term", ""),
            "1sg": pf.get("my"),
            "2sg": pf.get("your"),
            "3sg": pf.get("his_her"),
            "vocative": None,
            "notes": term.get("notes"),
            "_source": "BB_supplement",
        }

        # Index by all known forms (don't overwrite existing appendix entries)
        for key in ("stem", "1sg", "2sg", "3sg"):
            form = entry.get(key)
            if form and form not in _kinship_cache:
                _kinship_cache[form] = entry
            if form and form.endswith("ʔ"):
                bare = form[:-1]
                if bare not in _kinship_cache:
                    _kinship_cache[bare] = entry


def _index_kinship_term(term: dict):
    """Index a kinship term by all known surface forms."""
    pf = term.get("possessive_forms")
    if pf is None:
        return  # verb construction, not a noun

    entry = {
        "english": term.get("english_term", ""),
        "stem": term.get("skiri_term", ""),
        "1sg": pf.get("my"),
        "2sg": pf.get("your"),
        "3sg": pf.get("his_her"),
        "vocative": pf.get("vocative"),
        "notes": term.get("notes"),
    }

    # Index by every known form (for reverse lookup)
    for key in ("stem", "1sg", "2sg", "3sg", "vocative"):
        form = entry.get(key)
        if form and form not in _kinship_cache:
            _kinship_cache[form] = entry
        # Also index without final ʔ for fuzzy matching
        if form and form.endswith("ʔ"):
            bare = form[:-1]
            if bare not in _kinship_cache:
                _kinship_cache[bare] = entry
        # Index hi- variant of i- prefix (dictionary uses hi-, Appendix 3 uses i-)
        # e.g., iʔaastiʔ (Parks) → hiʔaastiʔ (dictionary headword)
        if form and form.startswith("i") and len(form) > 1 and form[1] not in "aeiou":
            hi_form = "h" + form
            if hi_form not in _kinship_cache:
                _kinship_cache[hi_form] = entry
            if hi_form.endswith("ʔ"):
                hi_bare = hi_form[:-1]
                if hi_bare not in _kinship_cache:
                    _kinship_cache[hi_bare] = entry


# ===========================================================================
#  BB ↔ PARKS NORMALIZATION
#
#  The Blue Book (Pari Pakuru') and Parks Dictionary use slightly different
#  orthographic conventions. The 10 close matches from Round 1 validation
#  are systematic:
#    - hi- ↔ i- for 3sg kinship prefix (BB uses hi-, Parks uses i-)
#    - aa ↔ a vowel length (BB sometimes shortens long vowels)
#    - ʔ presence/absence (atiʔas vs atias)
#    - ' (apostrophe) ↔ ʔ (IPA glottal) notation
# ===========================================================================

def normalize_for_comparison(form: str) -> str:
    """
    Normalize a Skiri form for comparison across BB and Parks notations.

    Strips orthographic variation that doesn't affect identity:
      - Removes glottal stops (ʔ) and apostrophes (')
      - Normalizes long vowels (aa → a, ii → i, uu → u)
      - Normalizes hi- → i- for 3sg kinship prefix
      - Lowercases

    Returns a normalized string for comparison (NOT for display).
    """
    if not form:
        return ""
    s = form.strip().lower()

    # Apostrophe variants → glottal
    s = s.replace("'", "ʔ").replace("'", "ʔ").replace("ʼ", "ʔ")

    # Normalize hi- prefix to i- at word start BEFORE glottal removal
    # (BB uses hi-, Parks uses i- for 3sg kinship prefix)
    # Must run before ʔ removal because hiʔV- looks like hiV- after removal
    if s.startswith("hi") and len(s) > 2:
        # hi- before consonant or glottal → i-
        if s[2] not in "aeiou" or s[2] == "ʔ":
            s = s[1:]

    # Remove all glottal stops
    s = s.replace("ʔ", "")

    # Contract long vowels
    s = s.replace("aa", "a").replace("ii", "i").replace("uu", "u")

    return s


def generate_kinship_possessive(headword: str, person: str) -> Optional[PossessionResult]:
    """
    Look up a kinship term's possessive form. Pure table lookup.

    Kinship terms have suppletive stems — entirely different words for
    my/your/his. These are listed in Parks Appendix 3 and confirmed
    in Blue Book Lesson 7.

    Uses normalize_for_comparison() to handle BB↔Parks orthographic
    differences (hi-/i-, aa/a, ʔ presence/absence).
    """
    kin = _load_kinship()
    entry = kin.get(headword)
    if entry is None:
        # Try stripping final ʔ
        entry = kin.get(headword.rstrip("ʔ"))
    if entry is None:
        # Try normalized form match
        norm_hw = normalize_for_comparison(headword)
        for cached_form, cached_entry in kin.items():
            if normalize_for_comparison(cached_form) == norm_hw:
                entry = cached_entry
                break
    if entry is None:
        return None

    form_key = person  # "1sg", "2sg", "3sg"
    possessive_form = entry.get(form_key)

    if possessive_form is None:
        return PossessionResult(
            system="kinship",
            person=person,
            headword=headword,
            stem=entry.get("stem", headword),
            surface_form="—",
            slot_fills={},
            morpheme_sequence=[],
            morpheme_labels=[],
            gloss=f"{_person_label(person)} {entry['english']} (form not attested)",
            is_attested=False,
            confidence="low",
            notes="No attested form in Appendix 3 for this person.",
        )

    person_english = {"1sg": "my", "2sg": "your", "3sg": "his/her"}.get(person, person)
    return PossessionResult(
        system="kinship",
        person=person,
        headword=headword,
        stem=entry.get("stem", headword),
        surface_form=possessive_form,
        slot_fills={"suppletive": possessive_form},
        morpheme_sequence=[possessive_form],
        morpheme_labels=["SUPPLETIVE_KIN"],
        gloss=f"{person_english} {entry['english']}",
        is_attested=True,
        confidence="attested",
        notes=entry.get("notes") or "",
    )


# ===========================================================================
#  SYSTEM 2: BODY PART POSSESSION — ri- (PHY.POSS) in verb
# ===========================================================================

def generate_body_part_possessive(
    headword: str,
    person: str = "1sg",
    position_verb: Optional[str] = None,
    aspect: str = "perfective",
) -> PossessionResult:
    """
    Generate a body-part possessive verb phrase.

    Body parts are incorporated into the verb. Possession is expressed by
    filling slot 17 (PHY.POSS) with ri- and slot 11 (AGENT) with the
    person prefix.

    Template (Blue Book Lesson 5):
        MODE(10) + PHY.POSS(17) + AGENT(11) + NOUN(25) + STEM/VERB(26) + ASPECT(27)

    IMPORTANT: The slot ordering in concatenation is NOT the same as slot
    numbering. The inner prefix template assembles left-to-right by slot
    number, but PHY.POSS (17) appears in the surface form BEFORE the agent
    because of how they fuse. Blue Book confirms:
        ti + ri + t + kirik + ta  (not ti + t + ri + kirik + ta)

    This is because ri- is in a *phonological* position between mode and
    agent, even though its slot number (17) is higher. The scope doc notes
    that the conjugation engine handles this via ordered assembly.

    INTEGRATION NOTE: In morpheme_inventory.py, the slot assembly should
    already handle this ordering. If it doesn't produce the right body-part
    order, look at how PHY.POSS interacts with AGENT in the concatenation
    sequence. The Blue Book examples are the ground truth.
    """
    stem, suffix = extract_noun_stem(headword)

    # Determine position verb
    if position_verb is None:
        position_verb = BODY_PART_POSITION.get(stem, DEFAULT_BODY_POSITION)

    # Mode prefix is ALWAYS ti- (IND.3) because the BODY PART is the subject
    # of the verb (it's the head that "sits", the eye that "hangs"), and the
    # body part is always 3rd person. The possessor is marked only by ri- + agent.
    # Blue Book confirms: "Ti rit•paks•ku" = "Here is my head" — ti, not ta.
    mode = "ti"
    mode_label = "IND.3"

    # Agent prefix
    agent = AGENT_PREFIX.get(person, "")
    agent_label = f"{person.upper()}.A"

    # Physical possession prefix
    phy_poss = "ri"

    # Aspect suffix
    if aspect == "imperfective":
        aspect_morph = "huʔ"  # BB: taari' = ta + arit + huʔ (? needs checking)
        aspect_label = "IMPF"
    else:
        aspect_morph = ""
        aspect_label = "PERF(Ø)"

    # Build slot fill dict
    slot_fills = {
        Slot.MODE: mode,
        Slot.PHY_POSS: phy_poss,
        Slot.AGENT: agent,
        Slot.NOUN: stem,
        Slot.STEM: position_verb,
    }
    if aspect_morph:
        slot_fills[Slot.ASPECT] = aspect_morph

    # Protect stem-internal Cs clusters from Rule 17 (sibilant hardening:
    # s->c after C). E.g. "paks" has internal ks that must NOT become kc.
    # Insert the same KS_MARKER that sound_changes.py uses for Rule 3R output.
    if _HAS_SOUND_ENGINE:
        protected_stem = re.sub(r'([ptkscʔ])s', lambda m: m.group(1) + _KS_MARKER + 's', stem)
    else:
        protected_stem = stem

    # Assemble morphemes in the order they appear in the surface form.
    # Blue Book confirms: MODE + PHY.POSS + AGENT + NOUN + VERB (+ ASPECT)
    #
    # INTEGRATION NOTE: When using morpheme_inventory.py's assembler,
    # pass the slot_fills dict and let it handle ordering. The manual
    # ordering below is for the standalone fallback only.
    pipeline_morphemes = [mode, phy_poss, agent, protected_stem, position_verb]
    display_morphemes = [mode, phy_poss, agent, stem, position_verb]
    labels = [mode_label, "PHY.POSS", agent_label, "NOUN", "POS.VERB"]
    if aspect_morph:
        pipeline_morphemes.append(aspect_morph)
        display_morphemes.append(aspect_morph)
        labels.append(aspect_label)

    # Filter out empty morphemes (3sg has Ø agent)
    paired = [(m, d, l) for m, d, l in zip(pipeline_morphemes, display_morphemes, labels) if m]
    pipeline_morphemes = [p[0] for p in paired]
    morphemes = [p[1] for p in paired]
    labels = [p[2] for p in paired]

    # Concatenate with sound changes — single pipeline call
    surface = _apply_pipeline(pipeline_morphemes)

    person_english = {"1sg": "my", "2sg": "your", "3sg": "his/her"}.get(person, person)
    pos_english = {"ku": "(sitting)", "ta": "(hanging)", "arit": "(standing)"}.get(position_verb, "")

    return PossessionResult(
        system="body_part",
        person=person,
        headword=headword,
        stem=stem,
        surface_form=surface,
        slot_fills=slot_fills,
        morpheme_sequence=morphemes,
        morpheme_labels=labels,
        gloss=f"here is {person_english} {headword} {pos_english}".strip(),
        is_attested=False,
        confidence="medium" if _HAS_SOUND_ENGINE else "low",
        notes=f"Position verb: {position_verb} ({POSITION_VERBS.get(position_verb, {}).get('meaning', '?')})"
              + ("" if _HAS_SOUND_ENGINE else "; using fallback concatenator — verify sound changes"),
    )


# ===========================================================================
#  SYSTEM 3: AGENT POSSESSION — gerundial possessive verb + noun
# ===========================================================================

# The three possessive verb forms are effectively fixed. They're gerundial
# forms of uk 'be, exist' with agent possession marking:
#   ratiru  = ra(GER) + t(1.A) + ir(A.POSS) + u(exist)
#   rasiru  = ra(GER) + s(2.A) + ir(A.POSS) + u(exist)
#   rau     = ra(GER) + Ø(3.A) + a(A.POSS) + u(exist)
#
# These are preceded by kti = ku(INDF) + ti(IND.3):
#   kti ratiru pakskuukuʔuʔ = my hat
#   kti rasiru pakskuukuʔuʔ = your hat
#   kti rau pakskuukuʔuʔ    = his hat
#
# Source: Blue Book Lesson 7 p. 35 ("Specifying Verbs — Possessives")

AGENT_POSS_VERB = {
    "1sg": {
        "form": "ratiru",
        "morphemes": ["ra", "t", "ir", "u"],
        "labels": ["GER", "1.A", "A.POSS", "exist"],
    },
    "2sg": {
        "form": "rasiru",
        "morphemes": ["ra", "s", "ir", "u"],
        "labels": ["GER", "2.A", "A.POSS", "exist"],
    },
    "3sg": {
        "form": "rau",
        "morphemes": ["ra", "", "a", "u"],
        "labels": ["GER", "3.A(Ø)", "A.POSS", "exist"],
    },
    # Dual/plural forms — not attested in Blue Book but derivable:
    "1du_incl": {
        "form": "raciru",     # ra + acir(DU.INCL) + u ? — UNVERIFIED
        "morphemes": ["ra", "acir", "", "u"],
        "labels": ["GER", "DU.INCL", "A.POSS(?)", "exist"],
        "_confidence": "low",
        "_note": "Not attested; derived by analogy with verb paradigm",
    },
}

# The kti prefix: ku(INDF) + ti(IND.3)
# From Grammatical Overview: agent possession "ordinarily preceded by
# the proclitic ku- 'indefinite'" and Blue Book confirms "ku+" on p.35.
KTI_PREFIX = "kti"
KTI_MORPHEMES = ["ku", "ti"]
KTI_LABELS = ["INDF", "IND.3"]


def generate_agent_possessive(
    headword: str,
    person: str = "1sg",
) -> PossessionResult:
    """
    Generate an agent-possessive construction for a general noun.

    The noun stands independently (not incorporated). Possession is
    expressed by a separate verb phrase that precedes the noun:

        kti + POSSESSIVE_VERB + NOUN

    Blue Book Lesson 7, p. 35:
        kti•ratiru paks•kuuku'     my hat
        kti rasiru paks•kuuku'     your hat
        kti•ra•u paks•kuuku'       his hat

    INTEGRATION NOTE: The possessive verb forms (ratiru/rasiru/rau) could
    in theory be generated via the conjugation engine:
        stem="u" (exist), mode="gerundial", + A.POSS slot
    But they're better treated as fixed forms since:
      (a) they're attested in Blue Book
      (b) the gerundial + A.POSS interaction hasn't been validated
      (c) three memorized forms vs. a fragile generation pipeline
    Revisit this once the engine handles gerundial A.POSS constructions.
    """
    poss_verb_entry = AGENT_POSS_VERB.get(person)
    if poss_verb_entry is None:
        return PossessionResult(
            system="agent",
            person=person,
            headword=headword,
            stem=headword,
            surface_form="—",
            slot_fills={},
            morpheme_sequence=[],
            morpheme_labels=[],
            gloss=f"({person}) {headword} — person form not available",
            confidence="low",
            notes=f"Agent possession for {person} not yet implemented",
        )

    poss_verb = poss_verb_entry["form"]
    confidence = poss_verb_entry.get("_confidence", "high")

    # Full morpheme sequence: ku + ti + [poss_verb morphemes] + noun
    all_morphemes = KTI_MORPHEMES + poss_verb_entry["morphemes"] + [headword]
    all_labels = KTI_LABELS + poss_verb_entry["labels"] + ["NOUN"]

    # Filter Ø morphemes for display
    display_morphemes = [m for m in all_morphemes if m]
    display_labels = [l for m, l in zip(all_morphemes, all_labels) if m]

    # Surface form: "kti" + possessive verb + noun (space-separated)
    surface = f"{KTI_PREFIX} {poss_verb} {headword}"

    person_english = {"1sg": "my", "2sg": "your", "3sg": "his/her"}.get(person, person)

    return PossessionResult(
        system="agent",
        person=person,
        headword=headword,
        stem=headword,  # noun is independent, not stemmed
        surface_form=surface,
        slot_fills={
            "kti": KTI_PREFIX,
            "poss_verb": poss_verb,
            "noun": headword,
        },
        morpheme_sequence=display_morphemes,
        morpheme_labels=display_labels,
        gloss=f"{person_english} {headword}",
        is_attested=(person in ("1sg", "2sg", "3sg")),
        confidence=confidence if person in ("1sg", "2sg", "3sg") else "low",
        notes=poss_verb_entry.get("_note", "Attested in Blue Book Lesson 7 p. 35")
              if person in ("1sg", "2sg", "3sg") else "Derived by analogy — not attested",
    )


# ===========================================================================
#  SYSTEM 4: PATIENT POSSESSION — uur- prefix
# ===========================================================================

def generate_patient_possessive_info(
    noun_headword: str,
    possessor_person: str = "2sg",
    verb_stem: str = "kuutik",
    verb_gloss: str = "kill",
    agent_person: str = "1sg",
) -> PossessionResult:
    """
    Document/generate a patient-possession construction.

    Patient possession is used when the PATIENT (not the agent) of the
    verb possesses the noun. Marked by uur- in slot 18.

    Grammatical Overview p. 37:
        tatuuhkuutit aruusaʔ  "I killed your horse"
        = ta(IND.1/2) + t(1.A) + a(2.P) + uur(PHY.POSS) + kuutik(kill)

    The possessor is indicated by the PATIENT prefix (slot 15):
        2sg possessor: a- (2.P)
        1sg possessor: ku- (1.P)
        3sg possessor: Ø

    INTEGRATION NOTE: This construction is a full transitive verb phrase.
    To generate it properly, you'd call the conjugation engine with:
        mode="indicative", agent=agent_person, patient=possessor_person,
        + PHY.POSS slot filled with uur-, + noun as external argument.
    The slot_fills dict below shows what goes where, but actual assembly
    should go through morpheme_inventory.conjugate_verb() or equivalent.
    """
    # Mode
    if agent_person in ("1sg", "2sg"):
        mode = "ta"
    else:
        mode = "ti"

    agent = AGENT_PREFIX.get(agent_person, "")
    patient = PATIENT_PREFIX.get(possessor_person, "")

    slot_fills = {
        Slot.MODE: mode,
        Slot.AGENT: agent,
        Slot.PATIENT: patient,
        Slot.BEN_PREV: "uur",    # Patient possession marker
        Slot.STEM: verb_stem,
    }

    morphemes = [mode, agent, patient, "uur", verb_stem]
    labels = ["MODE", f"AGENT({agent_person})", f"PATIENT({possessor_person})",
              "PAT.POSS", "VERB"]

    paired = [(m, l) for m, l in zip(morphemes, labels) if m]
    morphemes_clean = [p[0] for p in paired]
    labels_clean = [p[1] for p in paired]

    raw_verb = _apply_pipeline(morphemes_clean)
    surface_verb = raw_verb  # pipeline already produced final surface form

    possessor_english = {"1sg": "my", "2sg": "your", "3sg": "his/her"}.get(possessor_person, "?")
    agent_english = {"1sg": "I", "2sg": "you", "3sg": "he/she"}.get(agent_person, "?")

    return PossessionResult(
        system="patient",
        person=possessor_person,
        headword=noun_headword,
        stem=noun_headword,
        surface_form=f"{surface_verb} {noun_headword}",
        slot_fills=slot_fills,
        morpheme_sequence=morphemes_clean + [noun_headword],
        morpheme_labels=labels_clean + ["NOUN(external)"],
        gloss=f"{agent_english} {verb_gloss}(ed) {possessor_english} {noun_headword}",
        is_attested=False,
        confidence="medium" if _HAS_SOUND_ENGINE else "low",
        notes="Patient possession: uur- (slot 18) marks that the patient owns the noun. "
              "Noun is external to the verb phrase (not incorporated)."
              + ("" if _HAS_SOUND_ENGINE else " Using fallback concatenator."),
    )


# ===========================================================================
#  LOCATIVE / RELATIONAL STEMS — informational result (not possessable)
# ===========================================================================

def _generate_locative_info(
    headword: str,
    stem: str,
    person: str,
) -> PossessionResult:
    """
    Return an informational PossessionResult for locative/relational N-DEP
    stems that are incorporated into verbs as spatial modifiers rather than
    being independently possessed.
    """
    info = LOCATIVE_NOUNS.get(stem, {})
    meaning = info.get("meaning", "spatial modifier")
    example = info.get("example")

    note_parts = [
        f"Locative stem -- incorporated into verbs as spatial modifier, "
        f"not independently possessed.",
    ]
    if example:
        note_parts.append(f"Example: {example}")
    if info.get("variants"):
        note_parts.append(f"Variant stems: {', '.join(info['variants'])}")

    return PossessionResult(
        system="locative",
        person=person,
        headword=headword,
        stem=stem,
        surface_form=f"{stem}- \"{meaning}\"",
        slot_fills={},
        morpheme_sequence=[stem],
        morpheme_labels=["LOC.STEM"],
        gloss=f"{stem}- '{meaning}' (locative stem, not possessable)",
        is_attested=False,
        confidence="high",
        notes="\n".join(note_parts),
    )


# ===========================================================================
#  UNIFIED DISPATCHER
# ===========================================================================

def _person_label(person: str) -> str:
    return {"1sg": "my", "2sg": "your", "3sg": "his/her",
            "1du_incl": "our (incl)", "1du_excl": "our (excl)",
            "1pl_incl": "our (all)", "1pl_excl": "our (excl.pl)"}.get(person, person)


def generate_possessive(
    headword: str,
    person: str = "1sg",
    noun_class: Optional[str] = None,
    possession_type: Optional[str] = None,
    position_verb: Optional[str] = None,
    aspect: str = "perfective",
) -> PossessionResult:
    """
    Generate the possessive form for any noun, dispatching to the
    appropriate system based on noun_class or possession_type.

    Args:
        headword: The noun's dictionary headword (e.g., "paksuʔ", "atiraʔ")
        person: Possessor person ("1sg", "2sg", "3sg", etc.)
        noun_class: Grammatical class from dictionary ("N", "N-DEP", "N-KIN")
        possession_type: Override the system ("kinship", "body_part", "agent")
        position_verb: For body parts, override the position verb ("ku", "ta")
        aspect: "perfective" or "imperfective"

    Returns:
        PossessionResult with surface form, slot fills, morpheme breakdown
    """
    # Determine which system to use
    stem, _suffix = extract_noun_stem(headword)

    # For variant headwords like "hatuur-/hatuh-" or "hatawi-, ratawi-",
    # try each variant stem against the lookups.
    stem_variants = [stem]
    if "/" in stem or ", " in stem:
        for part in re.split(r"[/,]\s*", stem):
            clean = part.strip().rstrip("-")
            if clean and clean not in stem_variants:
                stem_variants.append(clean)

    if possession_type:
        system = possession_type
    else:
        # Always try kinship first — many kinship terms are classified as plain "N"
        # in the DB, not "N-KIN". The kinship cache is the authority.
        kin_result = generate_kinship_possessive(headword, person)
        if kin_result is not None:
            return kin_result

        # Then route by class
        if noun_class == "N-DEP":
            # Check if any variant stem is a body part, locative, or other
            matched_stem = None
            system = "agent"  # default fallthrough
            for sv in stem_variants:
                if sv in BODY_PART_POSITION:
                    system = "body_part"
                    matched_stem = sv
                    break
                if sv in LOCATIVE_NOUNS:
                    system = "locative"
                    matched_stem = sv
                    break
            if matched_stem:
                stem = matched_stem
        else:
            system = "agent"      # default for N and unknown

    # Dispatch (kinship already handled above)
    if system == "kinship":
        result = generate_kinship_possessive(headword, person)
        if result is not None:
            return result
        system = "agent"

    if system == "locative":
        return _generate_locative_info(headword, stem, person)

    if system == "body_part":
        return generate_body_part_possessive(
            headword, person=person,
            position_verb=position_verb, aspect=aspect,
        )

    if system == "patient":
        return generate_patient_possessive_info(
            headword, possessor_person=person,
        )

    # Default: agent possession
    return generate_agent_possessive(headword, person=person)


# ===========================================================================
#  PARADIGM TABLE GENERATION — for web UI
# ===========================================================================

def generate_paradigm_table(
    headword: str,
    noun_class: Optional[str] = None,
    possession_type: Optional[str] = None,
) -> Dict:
    """
    Generate a full possessive paradigm for web UI display.

    Returns a dict suitable for template rendering:
    {
        "headword": "paksuʔ",
        "system": "body_part",
        "system_label": "Body Part Possession (ri- PHY.POSS)",
        "persons": [
            {"person": "1sg", "label": "my", "form": "tiritpaksku", ...},
            {"person": "2sg", "label": "your", "form": "tirispaksku", ...},
            {"person": "3sg", "label": "his/her", "form": "tiripaksku", ...},
        ],
        "construction_note": "MODE + ri(PHY.POSS) + AGENT + NOUN + POS.VERB",
    }
    """
    # Check for locative stems early — they don't have person paradigms
    first_result = generate_possessive(headword, "1sg", noun_class, possession_type)

    if first_result.system == "locative":
        info = LOCATIVE_NOUNS.get(first_result.stem, {})
        return {
            "headword": headword,
            "system": "locative",
            "system_label": "Locative Stem (verb-incorporated spatial modifier)",
            "stem": first_result.stem,
            "meaning": info.get("meaning", "spatial modifier"),
            "example": info.get("example"),
            "variants": info.get("variants"),
            "persons": [],
            "construction_note": (
                "Locative stems are incorporated into verb phrases as "
                "spatial modifiers. They are not independently possessed."
            ),
        }

    persons = ["1sg", "2sg", "3sg"]
    rows = []

    # Reuse first_result for 1sg to avoid regenerating
    for p in persons:
        if p == "1sg":
            result = first_result
        else:
            result = generate_possessive(
                headword, person=p,
                noun_class=noun_class,
                possession_type=possession_type,
            )
        rows.append({
            "person": p,
            "label": _person_label(p),
            "form": result.surface_form,
            "morphemes": " + ".join(
                f"{m}({l})" for m, l in
                zip(result.morpheme_sequence, result.morpheme_labels)
            ),
            "gloss": result.gloss,
            "confidence": result.confidence,
            "is_attested": result.is_attested,
        })

    system_labels = {
        "kinship": "Kinship Term (suppletive stems)",
        "body_part": "Body Part Possession (ri- PHY.POSS in verb)",
        "agent": "Agent Possession (kti + possessive verb + noun)",
        "patient": "Patient Possession (uur- prefix)",
    }

    construction_notes = {
        "kinship": "Irregular stems -- each person has a unique form",
        "body_part": "MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + POSITION_VERB",
        "agent": "ku(INDF) + ti(IND) + ra(GER) + AGENT + ir/a(A.POSS) + u(exist) + NOUN",
        "patient": "MODE + AGENT + PATIENT + uur(PAT.POSS) + VERB + NOUN",
    }

    return {
        "headword": headword,
        "system": first_result.system,
        "system_label": system_labels.get(first_result.system, first_result.system),
        "persons": rows,
        "construction_note": construction_notes.get(first_result.system, ""),
    }


# ===========================================================================
#  DATABASE POPULATION — Phase 3.1.5 tables
# ===========================================================================

import sqlite3

def populate_db(db_path: str = "skiri_pawnee.db"):
    """
    Populate possession-related tables in the Skiri Pawnee database.

    Creates/populates:
      - noun_stems: entry_id, headword, stem, suffix, possession_type
      - kinship_paradigms: english_term, stem, 1sg, 2sg, 3sg forms
      - possession_examples: BB test cases with morpheme analyses

    Safe to re-run — uses INSERT OR REPLACE.
    """
    import logging
    log = logging.getLogger(__name__)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # --- Create tables ---
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS noun_stems (
            entry_id TEXT,
            headword TEXT NOT NULL,
            stem TEXT NOT NULL,
            suffix TEXT,
            possession_type TEXT NOT NULL,
            position_verb TEXT,
            notes TEXT,
            UNIQUE(headword, possession_type)
        );

        CREATE TABLE IF NOT EXISTS kinship_paradigms (
            english_term TEXT NOT NULL,
            stem TEXT NOT NULL,
            form_1sg TEXT,
            form_2sg TEXT,
            form_3sg TEXT,
            vocative TEXT,
            source TEXT DEFAULT 'appendix3',
            notes TEXT,
            UNIQUE(english_term, stem)
        );

        CREATE TABLE IF NOT EXISTS possession_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headword TEXT NOT NULL,
            person TEXT NOT NULL,
            noun_class TEXT,
            possession_type TEXT NOT NULL,
            expected_form TEXT NOT NULL,
            generated_form TEXT,
            morpheme_analysis TEXT,
            confidence TEXT,
            source TEXT DEFAULT 'BB',
            match_status TEXT,
            UNIQUE(headword, person, possession_type)
        );
    """)

    # --- Populate kinship_paradigms from appendix3 + supplements ---
    kin = _load_kinship()

    # Deduplicate: collect unique entries by (english, stem) pair
    seen_kin = set()
    for form, entry in kin.items():
        key = (entry.get("english", ""), entry.get("stem", ""))
        if key in seen_kin or not key[0]:
            continue
        seen_kin.add(key)

        source = entry.get("_source", "appendix3")
        cur.execute("""
            INSERT OR REPLACE INTO kinship_paradigms
            (english_term, stem, form_1sg, form_2sg, form_3sg, vocative, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.get("english", ""),
            entry.get("stem", ""),
            entry.get("1sg"),
            entry.get("2sg"),
            entry.get("3sg"),
            entry.get("vocative"),
            source,
            entry.get("notes"),
        ))

    log.info(f"Populated kinship_paradigms: {len(seen_kin)} terms")

    # --- Populate noun_stems from body-part lookup ---
    for stem, pos_verb in BODY_PART_POSITION.items():
        # Reconstruct approximate headword (stem + uʔ)
        headword_guess = stem + "uʔ"
        cur.execute("""
            INSERT OR REPLACE INTO noun_stems
            (headword, stem, suffix, possession_type, position_verb)
            VALUES (?, ?, ?, 'body_part', ?)
        """, (headword_guess, stem, "-uʔ", pos_verb))

    log.info(f"Populated noun_stems: {len(BODY_PART_POSITION)} body-part entries")

    # --- Populate noun_stems from locative/relational lookup ---
    loc_count = 0
    for stem, info in LOCATIVE_NOUNS.items():
        # Skip variant stems that are aliases (only insert canonical)
        variants = info.get("variants", [])
        headword_guess = stem + "-"  # dependent stems use trailing hyphen
        cur.execute("""
            INSERT OR REPLACE INTO noun_stems
            (headword, stem, suffix, possession_type, position_verb, notes)
            VALUES (?, ?, NULL, 'locative', NULL, ?)
        """, (headword_guess, stem, info.get("meaning", "")))
        loc_count += 1

    log.info(f"Populated noun_stems: {loc_count} locative entries")

    # --- Populate possession_examples from BB_TESTS ---
    for headword, person, noun_class, poss_type, expected in BB_TESTS:
        result = generate_possessive(
            headword, person=person,
            noun_class=noun_class,
            possession_type=poss_type,
        )
        match = "exact" if result.surface_form.strip() == expected.strip() else "mismatch"
        cur.execute("""
            INSERT OR REPLACE INTO possession_examples
            (headword, person, noun_class, possession_type, expected_form,
             generated_form, morpheme_analysis, confidence, source, match_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'BB', ?)
        """, (
            headword, person, noun_class, poss_type, expected,
            result.surface_form,
            " + ".join(f"{m}({l})" for m, l in
                       zip(result.morpheme_sequence, result.morpheme_labels)),
            result.confidence,
            match,
        ))

    log.info(f"Populated possession_examples: {len(BB_TESTS)} test cases")

    conn.commit()
    conn.close()
    log.info(f"DB population complete: {db_path}")


# ===========================================================================
#  TESTS — Blue Book validation
# ===========================================================================

BB_TESTS = [
    # System 2: Body part possession (Blue Book Lesson 5)
    # "Ti rit•paks•ku" = "Here is my head"
    ("paksuʔ", "1sg", "N-DEP", "body_part", "tiritpaksku"),
    # "Ti rit•kirik•ta" = "Here is my eye"
    ("kirikuʔ", "1sg", "N-DEP", "body_part", "tiritkirikta"),

    # System 1: Kinship (Blue Book Lesson 7 + Appendix 3)
    ("atiraʔ", "1sg", "N-KIN", "kinship", "atiraʔ"),      # my mother
    ("atiraʔ", "2sg", "N-KIN", "kinship", "asaas"),        # your mother
    ("atiraʔ", "3sg", "N-KIN", "kinship", "isaastiʔ"),     # his mother
    ("atiʔas", "1sg", "N-KIN", "kinship", "atiʔas"),       # my father
    ("atiʔas", "2sg", "N-KIN", "kinship", "aʔas"),         # your father
    ("atiʔas", "3sg", "N-KIN", "kinship", "iʔaastiʔ"),     # his father
    ("atikaʔ", "1sg", "N-KIN", "kinship", "atikaʔ"),       # my grandmother
    ("atikaʔ", "2sg", "N-KIN", "kinship", "akaʔ"),         # your grandmother
    ("atikaʔ", "3sg", "N-KIN", "kinship", "ikaariʔ"),      # his grandmother
    ("atipaat", "1sg", "N-KIN", "kinship", "atipaat"),      # my grandfather
    ("atipaat", "2sg", "N-KIN", "kinship", "apaat"),        # your grandfather
    ("atipaat", "3sg", "N-KIN", "kinship", "ipaaktiʔ"),     # his grandfather
    ("tiwaat", "1sg", "N-KIN", "kinship", "tiwaat"),        # my nephew/niece
    ("tiwaat", "2sg", "N-KIN", "kinship", "awaat"),         # your nephew/niece
    ("tiwaat", "3sg", "N-KIN", "kinship", "iwaahiʔ"),       # his nephew/niece

    # System 3: Agent possession (Blue Book Lesson 7)
    # Noun stands independently — surface form is "kti POSS_VERB NOUN"
    ("pakskuukuʔuʔ", "1sg", "N", "agent", "kti ratiru pakskuukuʔuʔ"),   # my hat
    ("pakskuukuʔuʔ", "2sg", "N", "agent", "kti rasiru pakskuukuʔuʔ"),   # your hat
    ("pakskuukuʔuʔ", "3sg", "N", "agent", "kti rau pakskuukuʔuʔ"),      # his hat
]


def run_tests():
    """Run validation against Blue Book examples."""
    print("=" * 70)
    print("POSSESSION ENGINE -- VALIDATION")
    print("=" * 70)
    print(f"Engine mode: {'INTEGRATED (sound_changes.py -- 24-rule pipeline)' if _HAS_SOUND_ENGINE else 'STANDALONE (4-rule fallback concatenator)'}")
    print()

    total = len(BB_TESTS)
    passed = 0
    failed = 0
    close = 0

    for headword, person, noun_class, poss_type, expected in BB_TESTS:
        result = generate_possessive(
            headword, person=person,
            noun_class=noun_class,
            possession_type=poss_type,
        )

        actual = result.surface_form.strip()
        expected_clean = expected.strip()

        if actual == expected_clean:
            status = "PASS"
            passed += 1
        elif actual.replace("ʔ", "'") == expected_clean.replace("ʔ", "'"):
            status = "~ CLOSE (glottal notation)"
            close += 1
        else:
            status = "FAIL"
            failed += 1

        if status != "PASS":
            print(f"  {status}")
            print(f"    {headword} ({person}, {poss_type})")
            print(f"    expected: {expected_clean}")
            print(f"    got:      {actual}")
            print(f"    morphemes: {' + '.join(result.morpheme_sequence)}")
            print()
        else:
            print(f"  {status}  {headword} ({person}) -> {actual}")

    print()
    print("-" * 70)
    print(f"Results: {passed}/{total} pass, {close} close, {failed} fail")
    print(f"Accuracy: {passed/total*100:.1f}% exact" + (f", {(passed+close)/total*100:.1f}% with close" if close else ""))

    if not _HAS_SOUND_ENGINE and failed > 0:
        print()
        print("NOTE: Body-part failures are expected in standalone mode —")
        print("the fallback concatenator doesn't apply all 24 sound change rules.")
        print("Place this file alongside sound_changes.py for accurate forms.")


# ===========================================================================
#  CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.1.5 — Noun Possession Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python possession_engine.py --test
  python possession_engine.py --generate paksuʔ --person 1sg --class N-DEP
  python possession_engine.py --generate atiraʔ --person 2sg --class N-KIN
  python possession_engine.py --generate akaruʔ --person 1sg --class N
  python possession_engine.py --paradigm paksuʔ --class N-DEP
        """,
    )
    parser.add_argument("--test", action="store_true", help="Run Blue Book validation tests")
    parser.add_argument("--generate", metavar="HEADWORD", help="Generate possessive form for a noun")
    parser.add_argument("--paradigm", metavar="HEADWORD", help="Generate full 1sg/2sg/3sg paradigm")
    parser.add_argument("--person", default="1sg", help="Possessor person (default: 1sg)")
    parser.add_argument("--class", dest="noun_class", help="Grammatical class: N, N-DEP, N-KIN")
    parser.add_argument("--type", dest="poss_type", help="Override possession type: kinship, body_part, agent, patient")
    parser.add_argument("--pos-verb", dest="pos_verb", help="Override position verb for body parts: ku, ta, arit")
    parser.add_argument("--populate-db", metavar="DB_PATH", nargs="?", const="skiri_pawnee.db",
                        help="Populate possession tables in DB (default: skiri_pawnee.db)")

    args = parser.parse_args()

    if not any([args.test, args.generate, args.paradigm, args.populate_db]):
        parser.print_help()
        return

    if args.test:
        run_tests()
        return

    if args.populate_db:
        import logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        populate_db(args.populate_db)
        return

    if args.generate:
        result = generate_possessive(
            args.generate,
            person=args.person,
            noun_class=args.noun_class,
            possession_type=args.poss_type,
            position_verb=args.pos_verb,
        )
        print(f"\n{'='*60}")
        print(f"  Headword:    {result.headword}")
        print(f"  Person:      {result.person} ({_person_label(result.person)})")
        print(f"  System:      {result.system}")
        print(f"  Stem:        {result.stem}")
        print(f"  Surface:     {result.surface_form}")
        print(f"  Morphemes:   {' + '.join(result.morpheme_sequence)}")
        print(f"  Labels:      {' + '.join(result.morpheme_labels)}")
        print(f"  Gloss:       {result.gloss}")
        print(f"  Confidence:  {result.confidence}")
        print(f"  Attested:    {result.is_attested}")
        if result.notes:
            print(f"  Notes:       {result.notes}")
        print(f"{'='*60}")
        return

    if args.paradigm:
        table = generate_paradigm_table(
            args.paradigm,
            noun_class=args.noun_class,
            possession_type=args.poss_type,
        )
        print(f"\n{'='*60}")
        print(f"  {table['headword']} — {table['system_label']}")
        print(f"  {table['construction_note']}")
        print(f"{'='*60}")
        for row in table["persons"]:
            conf = "ATT" if row["is_attested"] else {"high": "***", "medium": "**.", "low": "*.."}.get(row["confidence"], "?")
            print(f"  {row['label']:>10}  {row['form']:<35} [{conf}]")
            print(f"             {row['morphemes']}")
        print()


if __name__ == "__main__":
    main()
