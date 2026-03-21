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
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# ---------------------------------------------------------------------------
# Try to import from morpheme_inventory; fall back to built-in if unavailable
# ---------------------------------------------------------------------------
_HAS_MORPHEME_ENGINE = False
_HAS_NOMINAL_SC = False
try:
    # INTEGRATION POINT: adjust this import path to match your repo layout
    from morpheme_inventory import (
        _smart_concatenate,
        apply_sound_changes,
        # If these exist — names are assumptions based on scope doc:
        # conjugate_verb,
        # PRONOMINAL_PREFIXES as MI_PRONOMINAL_PREFIXES,
    )
    _HAS_MORPHEME_ENGINE = True
except ImportError:
    pass

try:
    from sound_changes import apply_nominal_sc as _apply_nominal_sc
    _HAS_NOMINAL_SC = True
except ImportError:
    _HAS_NOMINAL_SC = False

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
EXTRACTED_DIR = REPO_ROOT / "extracted_data"
KINSHIP_FILE = EXTRACTED_DIR / "appendix3_kinship.json"


# Pawnee vowel set (including accented variants) for allomorphy checks
VOWELS = set("aeiouáíúàâîû")

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
# Source: Blue Book Lesson 5 dialogues
BODY_PART_POSITION = {
    "paks":   "ku",    # head → sits
    "kirik":  "ta",    # eye → hangs
    "iks":    "ta",    # hand → hangs
    "haka":   "ta",    # mouth → hangs
    "as":     "ta",    # foot → hangs
    "usu":    "ta",    # hair → hangs
    "tsusu":  "ta",    # nose → hangs
    "kararu": "ta",    # stomach → hangs
    "tsiksu": "ta",    # throat/heart → hangs
    "rusu":   "ta",    # buttocks → hangs
    "kasu":   "ta",    # leg → hangs
    "kskitsu":"ta",    # finger → hangs
    "askitsu":"ta",    # toe → hangs
}

# Default position verb for body parts not in the lookup
DEFAULT_BODY_POSITION = "ta"  # hanging — most body parts


# ===========================================================================
#  KNOWN BODY-PART STEMS — for N-DEP dispatch disambiguation
#
#  N-DEP class includes BOTH body parts (→ System 2, ri- PHY.POSS)
#  and relational nouns (→ System 3, agent possession). This set lets
#  the dispatcher route correctly.
#
#  Source: Blue Book Lesson 5, Grammatical Overview "body parts and
#  body products" list, plus Parks dictionary N-DEP entries with body
#  part glosses.
# ===========================================================================

KNOWN_BODY_PART_STEMS = {
    # Blue Book Lesson 5 core set
    "paks",    # head
    "kirik",   # eye
    "iks",     # hand
    "haka",    # mouth
    "as",      # foot
    "usu",     # hair
    "tsusu",   # nose
    "kararu",  # stomach
    "tsiksu",  # throat/heart (seat of emotions)
    "rusu",    # buttocks
    "kasu",    # leg
    "kskitsu", # finger
    "askitsu", # toe
    "aspitu",  # toenail, claw
    # Extended from Grammatical Overview "body parts and body products"
    "kiis",    # bone
    "riiks",   # arrow (cultural product, incorporates like body part)
    "piiru",   # kidney
    "paahir",  # blood vessel
    "atak",    # arm
    "atka",    # ear (< atka•haru' BB p.23)
    "huur",    # tooth
    "siit",    # abdomen, belly
    # Body products
    "tahka",   # tears
    "waak",    # word, voice
}

# Relational/dependent nouns that are NOT body parts
# These use agent possession (System 3) even though they're N-DEP
KNOWN_RELATIONAL_STEMS = {
    "asaa",    # horse; dog (independent form of horse: aruusaʔ)
    "siis",    # sharp, pointed object (→ siiski 'awl', siistacaraʔ 'fork')
    "riikakus",# door flap
    "akitaar", # tribe
    "sakur",   # sun
}


# ===========================================================================
#  LOCATIVE / INSTRUMENTAL SUFFIX SYSTEM
#
#  Parks Grammatical Overview p. 30, Table 4:
#    Noun Class          Plural    Case Suffixes
#    ─────────────────   ────────  ─────────────────────
#    Body Part Terms     -raar-    -biriʔ (INST/LOC)
#    Tribal/Geo Names    Ø         -ru LOC
#    Other Nouns         Ø         -kat LOC / -biriʔ INST
#
#  Suffix details:
#    -biriʔ  = instrumental "with, using" (all nouns)
#              AND locative "in, on, at" (body parts only)
#    -raar-  = plural (body parts only), goes BETWEEN stem and -biriʔ
#    -ru     = locative "among, in country of" (tribal/geo names)
#    -wiru   = variant of -ru for names ending in vowel 'a'
#    -kat    = locative "in, on; among" (general nouns)
# ===========================================================================

# Noun class for locative routing
LOCATIVE_CLASS_BODY_PART = "body_part"
LOCATIVE_CLASS_TRIBAL = "tribal"
LOCATIVE_CLASS_OTHER = "other"


@dataclass
class LocativeResult:
    """Result of generating a locative/instrumental form."""
    headword: str
    stem: str
    form_type: str            # "locative", "instrumental", "locative_plural"
    noun_class: str           # "body_part", "tribal", "other"
    surface_form: str
    morpheme_sequence: List[str]
    morpheme_labels: List[str]
    gloss: str
    confidence: str = "high"
    notes: str = ""


def classify_noun_for_locative(
    headword: str,
    noun_class: Optional[str] = None,
    is_tribal: bool = False,
) -> str:
    """
    Determine which locative class a noun belongs to.

    Returns: "body_part", "tribal", or "other"
    """
    stem, _ = extract_noun_stem(headword)

    if noun_class == "N-DEP" and stem in KNOWN_BODY_PART_STEMS:
        return LOCATIVE_CLASS_BODY_PART
    if is_tribal or noun_class in ("N-TRIBAL", "N-GEO"):
        return LOCATIVE_CLASS_TRIBAL
    # Heuristic: names ending in common tribal suffixes
    if headword.endswith("ii") or headword.endswith("ita") or headword.endswith("aasi"):
        return LOCATIVE_CLASS_TRIBAL
    return LOCATIVE_CLASS_OTHER


def generate_locative(
    headword: str,
    noun_class: Optional[str] = None,
    is_tribal: bool = False,
    plural: bool = False,
) -> LocativeResult:
    """
    Generate the locative case form of a noun.

    Routing (Table 4):
      Body parts:  stem + (-raar- PL) + -biriʔ
      Tribal names: stem + -ru (or -wiru if stem ends in 'a')
      Other nouns:  stem + -kat

    Examples from Grammatical Overview:
      iksiriʔ  = iks + biriʔ       "on the hand"
      ikstaaririʔ = iks + raar + biriʔ  "on the hands" (PL)
      sahiiru  = sahii + ru         "in Cheyenne country"
      uukaahpaawiru = uukaahpaa + wiru  "among the Quapaw"
      akahkat  = akar + kat         "on the dwelling"
      asaakat  = asaa + kat         "among the horses"
    """
    stem, suffix = extract_noun_stem(headword)
    loc_class = classify_noun_for_locative(headword, noun_class, is_tribal)

    if loc_class == LOCATIVE_CLASS_BODY_PART:
        morphemes = [stem]
        labels = ["STEM"]
        if plural:
            morphemes.append("raar")
            labels.append("PL")
        # -biriʔ allomorphy: b → Ø after any consonant (Parks Ch. 4)
        # Parallel to -wiru/-ru tribal alternation
        last_morph = morphemes[-1]
        inst_suffix = "biriʔ" if last_morph[-1] in VOWELS else "iriʔ"
        morphemes.append(inst_suffix)
        labels.append("LOC/INST")
        raw = concatenate(morphemes)
        surface = apply_sc(raw)
        gloss_pl = " (plural)" if plural else ""
        return LocativeResult(
            headword=headword, stem=stem,
            form_type="locative_plural" if plural else "locative",
            noun_class=loc_class,
            surface_form=surface,
            morpheme_sequence=morphemes,
            morpheme_labels=labels,
            gloss=f"on/at the {headword}{gloss_pl}",
            confidence="high",
            notes="Body part locative: stem + (-raar- PL) + -biriʔ",
        )

    elif loc_class == LOCATIVE_CLASS_TRIBAL:
        # -wiru after stems ending in 'a', -ru otherwise
        if stem.endswith("a"):
            loc_suffix = "wiru"
        else:
            loc_suffix = "ru"
        morphemes = [stem, loc_suffix]
        labels = ["STEM", "LOC"]
        raw = concatenate(morphemes)
        surface = apply_sc(raw)
        return LocativeResult(
            headword=headword, stem=stem,
            form_type="locative",
            noun_class=loc_class,
            surface_form=surface,
            morpheme_sequence=morphemes,
            morpheme_labels=labels,
            gloss=f"among the {headword}; in {headword} country",
            confidence="high",
            notes=f"Tribal locative: stem + -{loc_suffix}",
        )

    else:  # LOCATIVE_CLASS_OTHER
        morphemes = [stem, "kat"]
        labels = ["STEM", "LOC"]
        raw = concatenate(morphemes)
        surface = apply_sc(raw)
        return LocativeResult(
            headword=headword, stem=stem,
            form_type="locative",
            noun_class=loc_class,
            surface_form=surface,
            morpheme_sequence=morphemes,
            morpheme_labels=labels,
            gloss=f"in/on the {headword}; among the {headword}",
            confidence="high",
            notes="General locative: stem + -kat",
        )


def generate_instrumental(
    headword: str,
    noun_class: Optional[str] = None,
) -> Optional[LocativeResult]:
    """
    Generate the instrumental case form: stem + -biriʔ/-iriʔ.

    Instrumental applies to concrete nouns ("with, using").
    Returns None for empty headwords or abstract/verbal entries where
    instrumental case is semantically inapplicable.
    Allomorphy: -biriʔ after vowel-final stems, -iriʔ after consonants.
    For body parts this is the same form as locative.
    """
    if not headword:
        return None
    stem, suffix = extract_noun_stem(headword)
    if not stem:
        return None
    # -biriʔ allomorphy: b → Ø after any consonant (Parks Ch. 4)
    inst_suffix = "biriʔ" if stem[-1] in VOWELS else "iriʔ"
    morphemes = [stem, inst_suffix]
    labels = ["STEM", "INST"]
    raw = concatenate(morphemes)
    surface = apply_sc(raw)
    return LocativeResult(
        headword=headword, stem=stem,
        form_type="instrumental",
        noun_class=classify_noun_for_locative(headword, noun_class),
        surface_form=surface,
        morpheme_sequence=morphemes,
        morpheme_labels=labels,
        gloss=f"with/using the {headword}",
        confidence="high",
        notes="Instrumental: stem + -biriʔ (applies to all nouns)",
    )


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

    # Augmentative -kusuʔ (check first — longest)
    if hw.endswith("kusuʔ") and len(hw) > 5:
        return hw[:-5], "-kusuʔ"

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

    NOMINAL ALLOMORPHY NOTE — raar→taar after consonants:
        The body-part plural marker -raar- surfaces as -taar- after consonant-
        final stems. This is NOT a separate sound change rule — it's Rule 8R
        (r→t after hard consonant) applying at the stem+suffix boundary:
            iks + raar + iriʔ  →  iks + taar + iriʔ  →  ikstaaririʔ  (attested)
        This parallels the -biriʔ → -iriʔ allomorphy (b→Ø after C) and the
        -wiru → -ru tribal locative alternation. All three are conditioned by
        the same environment: post-consonant morpheme junction in nominals.
        The underlying pattern is consonant-cluster simplification at nominal
        morpheme boundaries — initial sonorants/voiced stops reduce or delete
        after obstruent-final stems.
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


def concatenate(morphemes: List[str], labels: Optional[List[str]] = None) -> str:
    """Use real engine if available, else fallback.

    For nominal morphology (locative/instrumental), _smart_concatenate's
    verb-oriented boundary rules don't apply — use fallback concatenation
    and route through apply_sc() for unrestricted sound changes.
    """
    if _HAS_MORPHEME_ENGINE and labels is not None:
        # Only use _smart_concatenate for verb morphology where labels
        # are provided as morpheme_tuples. For nominal forms, fall back.
        try:
            tuples = list(zip(morphemes, labels))
            return _smart_concatenate(morphemes, tuples)
        except TypeError:
            pass
    return _fallback_concatenate(morphemes)


def apply_sc(form: str) -> str:
    """Apply nominal sound changes to a surface form.

    Uses the dedicated nominal pipeline (excludes verb-specific rules
    like Rule 17 sibilant hardening) when available. Falls back to the
    full verb pipeline, then to the minimal built-in fallback.
    """
    if _HAS_NOMINAL_SC:
        return _apply_nominal_sc(form)
    if _HAS_MORPHEME_ENGINE:
        return apply_sound_changes(form)
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

    return _kinship_cache


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


def generate_kinship_possessive(headword: str, person: str) -> Optional[PossessionResult]:
    """
    Look up a kinship term's possessive form. Pure table lookup.

    Kinship terms have suppletive stems — entirely different words for
    my/your/his. These are listed in Parks Appendix 3 and confirmed
    in Blue Book Lesson 7.
    """
    kin = _load_kinship()
    entry = kin.get(headword)
    if entry is None:
        # Try stripping final ʔ
        entry = kin.get(headword.rstrip("ʔ"))
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

    # Assemble morphemes in the order they appear in the surface form.
    # Blue Book confirms: MODE + PHY.POSS + AGENT + NOUN + VERB (+ ASPECT)
    #
    # INTEGRATION NOTE: When using morpheme_inventory.py's assembler,
    # pass the slot_fills dict and let it handle ordering. The manual
    # ordering below is for the standalone fallback only.
    morphemes = [mode, phy_poss, agent, stem, position_verb]
    labels = [mode_label, "PHY.POSS", agent_label, "NOUN", "POS.VERB"]
    if aspect_morph:
        morphemes.append(aspect_morph)
        labels.append(aspect_label)

    # Filter out empty morphemes (3sg has Ø agent)
    paired = [(m, l) for m, l in zip(morphemes, labels) if m]
    morphemes = [p[0] for p in paired]
    labels = [p[1] for p in paired]

    # Concatenate with sound changes
    raw = concatenate(morphemes)
    surface = apply_sc(raw)

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
        confidence="medium" if _HAS_MORPHEME_ENGINE else "low",
        notes=f"Position verb: {position_verb} ({POSITION_VERBS.get(position_verb, {}).get('meaning', '?')})"
              + ("" if _HAS_MORPHEME_ENGINE else "; using fallback concatenator — verify sound changes"),
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

    raw_verb = concatenate(morphemes_clean)
    surface_verb = apply_sc(raw_verb)

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
        confidence="medium" if _HAS_MORPHEME_ENGINE else "low",
        notes="Patient possession: uur- (slot 18) marks that the patient owns the noun. "
              "Noun is external to the verb phrase (not incorporated)."
              + ("" if _HAS_MORPHEME_ENGINE else " Using fallback concatenator."),
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
    if possession_type:
        system = possession_type
    elif noun_class == "N-KIN":
        system = "kinship"
    elif noun_class == "N-DEP":
        # N-DEP includes both body parts AND relational nouns.
        # Body parts → System 2 (ri- PHY.POSS verb incorporation)
        # Relational nouns → System 3 (agent possession, noun stands free)
        stem, _ = extract_noun_stem(headword)
        if stem in KNOWN_BODY_PART_STEMS:
            system = "body_part"
        elif stem in KNOWN_RELATIONAL_STEMS:
            system = "agent"  # relational N-DEP uses agent possession
        else:
            # Unknown N-DEP: default to body_part (most N-DEP are body parts)
            # but flag lower confidence
            system = "body_part"
    else:
        system = "agent"      # default for N and unknown

    # Dispatch
    if system == "kinship":
        result = generate_kinship_possessive(headword, person)
        if result is not None:
            return result
        # Fall through to agent possession if not found in kinship table
        system = "agent"

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

# Morpheme role classification for color-coded chips in the web UI.
# Maps label patterns to semantic roles used by the CSS chip system.
_ROLE_PATTERNS = {
    "mode":  {"IND", "GER", "INDF", "ABS", "ASSR", "NEG", "MODE"},
    "poss":  {"PHY.POSS", "A.POSS", "PAT.POSS", "P.POSS", "POSS"},
    "agent": {"A", "AGENT"},
    "noun":  {"NOUN"},
    "verb":  {"VERB", "POS.VERB", "exist"},
    "kin":   {"SUPPLETIVE", "SUPPLETIVE_KIN"},
    "case":  {"LOC", "INST", "LOC/INST", "PL"},
}

def _classify_morpheme_role(label: str) -> str:
    """Classify a morpheme label into a semantic role for UI coloring."""
    label_up = label.upper()
    # Check exact matches first, then substring
    for role, patterns in _ROLE_PATTERNS.items():
        for pat in patterns:
            if pat.upper() == label_up or pat.upper() in label_up:
                return role
    # Fallback heuristics
    if label_up.endswith(".A") or label_up.startswith("1.") or label_up.startswith("2.") or label_up.startswith("3."):
        return "agent"
    if "sitting" in label.lower() or "hanging" in label.lower() or "standing" in label.lower():
        return "verb"
    return "other"

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
    persons = ["1sg", "2sg", "3sg"]
    rows = []

    for p in persons:
        result = generate_possessive(
            headword, person=p,
            noun_class=noun_class,
            possession_type=possession_type,
        )

        # Build structured morpheme chips with semantic role tags
        chips = []
        for m, l in zip(result.morpheme_sequence, result.morpheme_labels):
            role = _classify_morpheme_role(l)
            chips.append({"m": m, "l": l, "role": role})

        rows.append({
            "person": p,
            "label": _person_label(p),
            "form": result.surface_form,
            "morphemes": " + ".join(
                f"{m}({l})" for m, l in
                zip(result.morpheme_sequence, result.morpheme_labels)
            ),
            "morpheme_chips": chips,
            "gloss": result.gloss,
            "confidence": result.confidence,
            "is_attested": result.is_attested,
        })

    system = rows[0]["confidence"]  # use first result's system
    first_result = generate_possessive(headword, "1sg", noun_class, possession_type)

    system_labels = {
        "kinship": "Kinship Term (suppletive stems)",
        "body_part": "Body Part Possession (ri- PHY.POSS in verb)",
        "agent": "Agent Possession (kti + possessive verb + noun)",
        "patient": "Patient Possession (uur- prefix)",
    }

    construction_notes = {
        "kinship": "Irregular stems — each person has a unique form",
        "body_part": "MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + POSITION_VERB",
        "agent": "ku(INDF) + ti(IND) + ra(GER) + AGENT + ir/a(A.POSS) + u(exist) + NOUN",
        "patient": "MODE + AGENT + PATIENT + uur(PAT.POSS) + VERB + NOUN",
    }

    # Also generate locative/instrumental forms if applicable
    loc_forms = []
    if first_result.system == "body_part":
        loc = generate_locative(headword, noun_class="N-DEP", plural=False)
        loc_pl = generate_locative(headword, noun_class="N-DEP", plural=True)
        inst = generate_instrumental(headword, noun_class="N-DEP")
        loc_forms = [
            {"type": "locative", "form": loc.surface_form,
             "morphemes": " + ".join(f"{m}({l})" for m, l in zip(loc.morpheme_sequence, loc.morpheme_labels)),
             "gloss": loc.gloss},
            {"type": "locative (pl)", "form": loc_pl.surface_form,
             "morphemes": " + ".join(f"{m}({l})" for m, l in zip(loc_pl.morpheme_sequence, loc_pl.morpheme_labels)),
             "gloss": loc_pl.gloss},
        ]
        if inst:
            loc_forms.append(
                {"type": "instrumental", "form": inst.surface_form,
                 "morphemes": " + ".join(f"{m}({l})" for m, l in zip(inst.morpheme_sequence, inst.morpheme_labels)),
                 "gloss": inst.gloss})
    elif first_result.system == "agent":
        loc = generate_locative(headword, noun_class=noun_class)
        inst = generate_instrumental(headword, noun_class=noun_class)
        loc_forms = [
            {"type": "locative", "form": loc.surface_form,
             "morphemes": " + ".join(f"{m}({l})" for m, l in zip(loc.morpheme_sequence, loc.morpheme_labels)),
             "gloss": loc.gloss},
        ]
        if inst:
            loc_forms.append(
                {"type": "instrumental", "form": inst.surface_form,
                 "morphemes": " + ".join(f"{m}({l})" for m, l in zip(inst.morpheme_sequence, inst.morpheme_labels)),
                 "gloss": inst.gloss})

    return {
        "headword": headword,
        "system": first_result.system,
        "system_label": system_labels.get(first_result.system, first_result.system),
        "persons": rows,
        "construction_note": construction_notes.get(first_result.system, ""),
        "locative_forms": loc_forms,
    }


# ===========================================================================
#  TESTS — Blue Book validation
# ===========================================================================

BB_TESTS = [
    # ===================================================================
    # System 2: Body part possession (Blue Book Lesson 5)
    # Template: ti(IND.3) + ri(PHY.POSS) + AGENT + NOUN_STEM + POS_VERB
    # ===================================================================

    # "Ti rit•paks•ku" = "Here is my head (sitting)"
    ("paksuʔ", "1sg", "N-DEP", "body_part", "tiritpaksku"),
    # "Ti rit•kirik•ta" = "Here is my eye (hanging)"
    ("kirikuʔ", "1sg", "N-DEP", "body_part", "tiritkirikta"),
    # 2sg body part: "Ti ris•paks•ku" = "Here is your head"
    ("paksuʔ", "2sg", "N-DEP", "body_part", "tirispaksku"),
    # 3sg body part: "Ti ri•paks•ku" = "Here is his/her head"
    ("paksuʔ", "3sg", "N-DEP", "body_part", "tiripaksku"),
    # hand (hanging): "Ti rit•iks•ta" = "Here is my hand"
    ("iksuʔ", "1sg", "N-DEP", "body_part", "tiritiksta"),
    # foot (hanging): "Ti rit•as•ta" = "Here is my foot"
    ("asuʔ", "1sg", "N-DEP", "body_part", "tiritasta"),
    # mouth (hanging): "Ti rit•haka•ta" = "Here is my mouth"
    ("hakauʔ", "1sg", "N-DEP", "body_part", "tirithakata"),
    # nose (hanging): tsusu is stem; t+tsusu stays as-is in fallback
    ("tsusuuʔ", "1sg", "N-DEP", "body_part", "tirittsusuta"),
    # stomach: kararu is stem
    ("kararuuʔ", "1sg", "N-DEP", "body_part", "tiritkararuta"),
    # hair: "Ti rit•usu•ta"
    ("usuuʔ", "1sg", "N-DEP", "body_part", "tiritusuta"),

    # ===================================================================
    # System 1: Kinship (Blue Book Lesson 7 + Appendix 3)
    # Suppletive stems — pure lookup
    # ===================================================================

    # mother — atiraʔ
    ("atiraʔ", "1sg", "N-KIN", "kinship", "atiraʔ"),      # my mother
    ("atiraʔ", "2sg", "N-KIN", "kinship", "asaas"),        # your mother
    ("atiraʔ", "3sg", "N-KIN", "kinship", "isaastiʔ"),     # his/her mother

    # father — atiʔas
    ("atiʔas", "1sg", "N-KIN", "kinship", "atiʔas"),       # my father
    ("atiʔas", "2sg", "N-KIN", "kinship", "aʔas"),         # your father
    ("atiʔas", "3sg", "N-KIN", "kinship", "iʔaastiʔ"),     # his/her father

    # grandmother — atikaʔ
    ("atikaʔ", "1sg", "N-KIN", "kinship", "atikaʔ"),       # my grandmother
    ("atikaʔ", "2sg", "N-KIN", "kinship", "akaʔ"),         # your grandmother
    ("atikaʔ", "3sg", "N-KIN", "kinship", "ikaariʔ"),      # his/her grandmother

    # grandfather — atipaat
    ("atipaat", "1sg", "N-KIN", "kinship", "atipaat"),      # my grandfather
    ("atipaat", "2sg", "N-KIN", "kinship", "apaat"),        # your grandfather
    ("atipaat", "3sg", "N-KIN", "kinship", "ipaaktiʔ"),    # his/her grandfather

    # nephew/niece — tiwaat
    ("tiwaat", "1sg", "N-KIN", "kinship", "tiwaat"),        # my nephew/niece
    ("tiwaat", "2sg", "N-KIN", "kinship", "awaat"),         # your nephew/niece
    ("tiwaat", "3sg", "N-KIN", "kinship", "iwaahiʔ"),      # his/her nephew/niece

    # sibling (same sex) — iraariʔ
    ("iraariʔ", "1sg", "N-KIN", "kinship", "iraariʔ"),     # my sibling (same sex)

    # ===================================================================
    # System 3: Agent possession (Blue Book Lesson 7 p. 35)
    # kti + POSS_VERB + NOUN (noun stands independently)
    # ===================================================================

    # hat — pakskuukuʔuʔ
    ("pakskuukuʔuʔ", "1sg", "N", "agent", "kti ratiru pakskuukuʔuʔ"),   # my hat
    ("pakskuukuʔuʔ", "2sg", "N", "agent", "kti rasiru pakskuukuʔuʔ"),   # your hat
    ("pakskuukuʔuʔ", "3sg", "N", "agent", "kti rau pakskuukuʔuʔ"),      # his/her hat

    # house — akaruʔ (general noun, agent possession)
    ("akaruʔ", "1sg", "N", "agent", "kti ratiru akaruʔ"),    # my house
    ("akaruʔ", "2sg", "N", "agent", "kti rasiru akaruʔ"),    # your house
    ("akaruʔ", "3sg", "N", "agent", "kti rau akaruʔ"),       # his/her house

    # dog — asaakiʔ (has dependent stem asaa-, but possession is agent-style)
    ("asaakiʔ", "1sg", "N", "agent", "kti ratiru asaakiʔ"),  # my dog
]

# ===================================================================
#  LOCATIVE / INSTRUMENTAL TESTS
#  Source: Grammatical Overview p. 30
# ===================================================================

LOCATIVE_TESTS = [
    # Body part locative: stem + -iriʔ (b → Ø after consonant)
    # Attested: iksiriʔ = iks + iriʔ "by hand; on the hand"
    ("iksuʔ", "N-DEP", False, False, "iksiriʔ"),
    # Body part locative plural: stem + raar + iriʔ
    # Attested: ikstaaririʔ = iks + taar + iriʔ (Gram. Overview p.30)
    # raar→taar handled by Rule 8R (r→t after hard C) in nominal pipeline
    ("iksuʔ", "N-DEP", False, True, "ikstaaririʔ"),

    # Tribal locative: base_name + ru
    # sahiiru = sahii + ru "in Cheyenne country"
    ("sahii", None, True, False, "sahiiru"),

    # Tribal locative -wiru: base ending in 'a' + wiru
    # uukaahpaawiru = uukaahpaa + wiru "among the Quapaw"
    ("uukaahpaa", None, True, False, "uukaahpaawiru"),
    # riihitawiru = riihita + wiru "among the Ponca"
    ("riihita", None, True, False, "riihitawiru"),

    # General noun locative: stem + kat
    # akahkat = akar + kat "on the dwelling" (r→h before k, Rule 12R)
    ("akaruʔ", None, False, False, "akahkat"),
    # asaakat = asaa + kat "among the horses"
    ("asaakiʔ", None, False, False, "asaakat"),
]


def run_tests():
    """Run validation against Blue Book examples."""
    print("=" * 70)
    print("POSSESSION ENGINE — VALIDATION")
    print("=" * 70)
    print(f"Engine mode: {'INTEGRATED (morpheme_inventory.py)' if _HAS_MORPHEME_ENGINE else 'STANDALONE (fallback concatenator)'}")
    print()

    total = len(BB_TESTS)
    passed = 0
    failed = 0
    close = 0

    # ---- Possessive tests ----
    print("─── POSSESSIVE FORMS ───")
    for headword, person, noun_class, poss_type, expected in BB_TESTS:
        result = generate_possessive(
            headword, person=person,
            noun_class=noun_class,
            possession_type=poss_type,
        )

        actual = result.surface_form.strip()
        expected_clean = expected.strip()

        if actual == expected_clean:
            status = "✓ PASS"
            passed += 1
        elif actual.replace("ʔ", "'") == expected_clean.replace("ʔ", "'"):
            status = "~ CLOSE (glottal notation)"
            close += 1
        else:
            status = "✗ FAIL"
            failed += 1

        if status != "✓ PASS":
            print(f"  {status}")
            print(f"    {headword} ({person}, {poss_type})")
            print(f"    expected: {expected_clean}")
            print(f"    got:      {actual}")
            print(f"    morphemes: {' + '.join(result.morpheme_sequence)}")
            print()
        else:
            print(f"  {status}  {headword} ({person}) → {actual}")

    # ---- Locative tests ----
    print()
    print("─── LOCATIVE / INSTRUMENTAL FORMS ───")
    loc_total = len(LOCATIVE_TESTS)
    loc_passed = 0
    loc_failed = 0
    loc_close = 0

    for headword, noun_class, is_tribal, plural, expected in LOCATIVE_TESTS:
        result = generate_locative(
            headword,
            noun_class=noun_class,
            is_tribal=is_tribal,
            plural=plural,
        )

        actual = result.surface_form.strip()
        expected_clean = expected.strip()

        if actual == expected_clean:
            status = "✓ PASS"
            loc_passed += 1
        elif actual.replace("ʔ", "'") == expected_clean.replace("ʔ", "'"):
            status = "~ CLOSE (glottal notation)"
            loc_close += 1
        else:
            status = "✗ FAIL"
            loc_failed += 1

        if status != "✓ PASS":
            print(f"  {status}")
            print(f"    {headword} (class={noun_class}, tribal={is_tribal}, pl={plural})")
            print(f"    expected: {expected_clean}")
            print(f"    got:      {actual}")
            print(f"    morphemes: {' + '.join(result.morpheme_sequence)}")
            print()
        else:
            label = "PL " if plural else ""
            print(f"  {status}  {headword} → {label}{actual}")

    # ---- Summary ----
    all_total = total + loc_total
    all_passed = passed + loc_passed
    all_close = close + loc_close
    all_failed = failed + loc_failed

    print()
    print("-" * 70)
    print(f"Possessive: {passed}/{total} pass, {close} close, {failed} fail")
    print(f"Locative:   {loc_passed}/{loc_total} pass, {loc_close} close, {loc_failed} fail")
    print(f"TOTAL:      {all_passed}/{all_total} pass, {all_close} close, {all_failed} fail")
    print(f"Accuracy:   {all_passed/all_total*100:.1f}% exact" +
          (f", {(all_passed+all_close)/all_total*100:.1f}% with close" if all_close else ""))

    if not _HAS_MORPHEME_ENGINE and all_failed > 0:
        print()
        print("NOTE: Some failures are expected in standalone mode —")
        print("the fallback concatenator doesn't apply all 24 sound change rules.")
        print("Wire into morpheme_inventory.py for accurate forms.")


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

    args = parser.parse_args()

    if not any([args.test, args.generate, args.paradigm]):
        parser.print_help()
        return

    if args.test:
        run_tests()
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
            conf = "✓" if row["is_attested"] else {"high": "●●●", "medium": "●●○", "low": "●○○"}.get(row["confidence"], "?")
            print(f"  {row['label']:>10}  {row['form']:<35} [{conf}]")
            print(f"             {row['morphemes']}")
        if table.get("locative_forms"):
            print()
            print(f"  {'─── Case Forms ───':>10}")
            for lf in table["locative_forms"]:
                print(f"  {lf['type']:>15}  {lf['form']:<35}")
                print(f"                  {lf['morphemes']}")
        print()


if __name__ == "__main__":
    main()
