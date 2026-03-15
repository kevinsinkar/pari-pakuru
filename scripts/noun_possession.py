#!/usr/bin/env python3
"""
Phase 3.1.5 — Noun Possession Morphology
=========================================

Extracts, catalogs, and generates possessive forms for Skiri Pawnee nouns.

Three possession systems in Skiri (from Parks Grammatical Overview pp. 36-37
and Blue Book Lessons 5, 7):

  System 1: KINSHIP POSSESSION (N-KIN)
    Suppletive stems — each kinship term has irregular my/your/his forms.
    Source: appendix3_kinship.json (23 terms with possessive paradigms).
    Example: "mother" → my: atiraʔ, your: asaas, his: isaastiʔ

  System 2: BODY-PART / PHYSICAL POSSESSION (N-DEP, some N)
    Expressed via the ri- (PHY.POSS) prefix in the verb introducer.
    Body parts drop their nominal suffix (-uʔ) when incorporated.
    Source: Blue Book Lesson 5, Grammatical Overview Table 7 slot 17.
    Example: ti + ri + t + kirik + ta → "Ti rit•kirik•ta" (Here is my eye)
             mode + phys.poss + 1.A + eye-stem + hang

  System 3: AGENT POSSESSION (general nouns — N, some N-DEP)
    Expressed via ku- (INDF) + ir-/a- (A.POSS) + possessive verb uk/uur.
    The noun stands independently (not incorporated).
    Source: Blue Book Lesson 7, Grammatical Overview pp. 36-37.
    Example: "kti•ratiru pakskuuku'" (my hat)
             ku + ti + ir + a + t + ir + uk → possessed construction

  System 4: PATIENT POSSESSION
    uur- prefix marks that the PATIENT (not agent) possesses the noun.
    Source: Grammatical Overview p. 37.
    Example: tatuuhkuutit aruusaʔ (I killed YOUR horse)
             ta + t + a(2.P) + uur(PHY.POSS) + kuutik(kill)

Usage:
    python noun_possession.py --extract        Extract and categorize all nouns
    python noun_possession.py --report         Generate possession system report
    python noun_possession.py --validate       Validate against Blue Book examples
    python noun_possession.py --generate STEM  Generate possessive forms for a noun
    python noun_possession.py --db             Populate DB tables
"""

import json
import os
import sys
import re
import argparse
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Path configuration — adapt to your repo layout
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = REPO_ROOT / "extracted_data"
DICT_DIR = REPO_ROOT / "Dictionary Data"
BB_DIR = REPO_ROOT / "pari pakuru"
DB_PATH = REPO_ROOT / "skiri_pawnee.db"
REPORTS_DIR = REPO_ROOT / "reports"

S2E_FILE = DICT_DIR / "skiri_to_english_respelled.json"
E2S_FILE = DICT_DIR / "english_to_skiri_linked.json"
KINSHIP_FILE = EXTRACTED_DIR / "appendix3_kinship.json"
GRAMMAR_FILE = EXTRACTED_DIR / "grammatical_overview.json"
BB_TEXT_FILE = BB_DIR / "Blue_Book_Pari_Pakuru.txt"
BB_EXTRACTED = EXTRACTED_DIR / "blue_book_extracted.json"

OUTPUT_FILE = EXTRACTED_DIR / "noun_possession_catalog.json"


# ===========================================================================
#  LINGUISTIC CONSTANTS — from Parks Grammatical Overview + Blue Book
# ===========================================================================

# Pronominal prefixes (Table 9)
PRONOMINAL_PREFIXES = {
    "agent": {
        "1sg": "t-",
        "2sg": "s-",
        "3sg": "Ø",       # zero morpheme
        "obv": "ir-",     # obviative
        "1du_incl": "acir-",
        "1pl_incl": "a-",
    },
    "patient": {
        "1sg": "ku-",
        "2sg": "a-",
        "3sg": "Ø",
        "obv": "a-",
        "1du_incl": "aca-",
    },
}

# Possessive prefix allomorphs for A.POSS (Grammatical Overview p. 36)
# Agent possession: ir- (1st/2nd person), a- (3rd person)
AGENT_POSS_PREFIX = {
    "1sg": "ir-",   # + agent t-
    "2sg": "ir-",   # + agent s-
    "3sg": "a-",    # zero agent
    "1du_incl": "ir-",  # + inclusive acir-
}

# Physical possession prefix (Table 7, slot 17)
PHY_POSS_PREFIX = "ri-"

# Patient possession prefix (Table 7, slot 18)
PAT_POSS_PREFIX = "uur-"

# Nominal suffixes that are stripped when noun incorporates
NOMINAL_SUFFIXES = {
    "-uʔ": "NOM (absolutive)",
    "-kis": "DIM (diminutive)",
    "-kusuʔ": "AUG (augmentative)",
    "-biriʔ": "INST/LOC",
}

# Locative suffixes (Table 4)
LOCATIVE_SUFFIXES = {
    "-biriʔ": {"class": "body_part", "meaning": "instrumental/locative ('with, on')"},
    "-ru": {"class": "tribal_geo", "meaning": "locative ('among, in territory of')"},
    "-wiru": {"class": "tribal_geo_a", "meaning": "locative variant (names ending in -a)"},
    "-kat": {"class": "other", "meaning": "locative ('in, on; among')"},
}

# Body part plural suffix
BODY_PART_PLURAL = "-raar-"


# ===========================================================================
#  DATA LOADING
# ===========================================================================

def load_json(path):
    """Load a JSON file, returning None if not found."""
    if not path.exists():
        print(f"  WARNING: File not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_s2e():
    """Load S2E dictionary entries."""
    data = load_json(S2E_FILE)
    if data is None:
        return []
    return data if isinstance(data, list) else data.get("entries", data)


def load_kinship():
    """Load appendix3 kinship data, flattening nested category structure."""
    data = load_json(KINSHIP_FILE)
    if data is None:
        return []
    terms = []
    for item in data.get("terms", []):
        if "category" in item and "terms" in item:
            # Nested category (consanguineal, affinal)
            for sub in item["terms"]:
                sub["_category"] = item["category"]
                terms.append(sub)
        else:
            terms.append(item)
    return terms


# ===========================================================================
#  NOUN EXTRACTION & CLASSIFICATION
# ===========================================================================

NOUN_CLASSES = {"N", "N-DEP", "N-KIN"}


def extract_gram_class(entry):
    """Get grammatical class string from an S2E entry."""
    gi = entry.get("part_I", {}).get("grammatical_info", {})
    return (gi.get("grammatical_class") or "").strip()


def is_noun_entry(entry):
    """Check if entry is a noun (N, N-DEP, N-KIN, or multi-class containing one)."""
    gc = extract_gram_class(entry)
    if not gc:
        return False
    # Handle multi-class entries like "N, VT"
    classes = {c.strip() for c in gc.split(",")}
    return bool(classes & NOUN_CLASSES)


def get_noun_class(entry):
    """Return the specific noun class (N, N-DEP, N-KIN) for an entry."""
    gc = extract_gram_class(entry)
    classes = {c.strip() for c in gc.split(",")}
    # Priority: N-KIN > N-DEP > N
    if "N-KIN" in classes:
        return "N-KIN"
    if "N-DEP" in classes:
        return "N-DEP"
    if "N" in classes:
        return "N"
    return None


def extract_stem(headword):
    """
    Strip nominal suffix to recover the bound stem.

    Skiri independent nouns are typically: STEM + -uʔ (absolutive)
    or STEM + -kis (diminutive). The stem is what incorporates into verbs
    and what possessive prefixes attach to.

    Examples:
        iksuʔ → iks-   (hand)
        paksuʔ → paks-  (head)
        asaakiʔ → asaa- (dog; from asaa- + -kis → asaaki → asaakiʔ)
        aruusaʔ → aruusa- (horse)
        akaruʔ → akar-  (house)
    """
    hw = headword.strip()

    # Try longest suffix first
    # -kusuʔ (augmentative)
    if hw.endswith("kusuʔ"):
        return hw[:-5] + "-", "-kusuʔ"

    # -biriʔ (instrumental/locative — some body parts use this as absolutive)
    if hw.endswith("biriʔ") or hw.endswith("iriʔ"):
        # Be cautious — only strip if the result looks like a valid stem
        candidate = hw[:-5] if hw.endswith("biriʔ") else hw[:-4]
        if len(candidate) >= 2:
            return candidate + "-", "-biriʔ" if hw.endswith("biriʔ") else "-iriʔ"

    # -uʔ (absolutive — most common)
    if hw.endswith("uʔ"):
        stem = hw[:-2]
        # If stem ends in a vowel, the suffix was just -uʔ
        # If stem ends in consonant, same
        return stem + "-", "-uʔ"

    # -kis/-kiʔ (diminutive — surface as -ki or -kiʔ after sound changes)
    if hw.endswith("kiʔ") or hw.endswith("kis"):
        suffix = hw[-3:]
        stem = hw[:-3]
        # -kis DIM sometimes surfaces with final ʔ (kiʔ)
        if len(stem) >= 2:
            return stem + "-", f"-{suffix}"

    # Kinship and some other terms have no standard suffix
    # Return the whole word as the stem
    return hw, None


def _has_body_part_word(gloss_text, keywords):
    """
    Check if gloss refers to an actual body part, not a compound noun.

    We check that the keyword appears as a primary referent:
    - At the start of a definition segment (after ;)
    - As "of the KEYWORD" or "of KEYWORD" (possessive/locative context)
    - Not preceded by qualifiers that make it a compound object (e.g., "head strap")

    We exclude cases where body part words appear in compound nouns (footwear,
    footprint, hair tie, head strap) or in descriptions of non-body objects.
    """
    # Compound excluders: if the body part word is followed by these, skip it
    compound_suffixes = {
        "wear", "print", "bridge", "rest", "band", "board", "line", "work",
        "tie", "wrap", "strap", "dress", "style", "piece", "pin", "guard",
        "scraper", "hook", "covering", "cut",
    }
    # Prefixes that make the body-part word into a compound (red-head, hog-nose)
    compound_prefixes = {
        "red", "hog", "buck", "roan", "roach", "roached", "flat", "pig",
    }

    for kw in keywords:
        # Check each semicolon-delimited definition segment
        for segment in gloss_text.split(";"):
            segment = segment.strip()
            if not segment:
                continue

            # Does this segment contain the keyword as a whole word?
            match = re.search(r'\b' + re.escape(kw) + r'\b', segment)
            if not match:
                continue

            # Check it's not part of a compound (e.g. "head strap", "foot-bridge")
            after = segment[match.end():].lstrip("-").lstrip()
            first_after = after.split()[0] if after.split() else ""
            if first_after.rstrip(".,;:") in compound_suffixes:
                continue

            # Check it's not a modifier or material description
            before = segment[:match.start()].strip()
            before_words = before.split() if before else []

            # If more than 3 words before the keyword, likely a subordinate description
            if len(before_words) > 3:
                continue

            # "of KEYWORD" = material/possessive, not body-part identification
            # e.g., "trail of hair", "made of skin", "piece of bone"
            if before_words and before_words[-1] in ("of", "with", "like"):
                continue

            # Compound prefix: "red-head", "hog-nose", "roached head"
            if before_words and before_words[-1].rstrip("-") in compound_prefixes:
                continue

            return True
    return False


def classify_possession_type(entry, noun_class):
    """
    Determine which possession system applies to this noun.

    Returns one of:
        'kinship'    — N-KIN, suppletive stems (System 1)
        'body_part'  — N-DEP body parts, ri- PHY.POSS in verb (System 2)
        'general'    — Regular nouns, agent possession construction (System 3)
        'relational' — N-DEP non-body relational terms
    """
    if noun_class == "N-KIN":
        return "kinship"

    if noun_class == "N-DEP":
        # Check if it's a body part by looking at gloss
        glosses = entry.get("part_I", {}).get("glosses", [])
        gloss_text = " ".join(g.get("definition", "") for g in glosses).lower()

        body_part_keywords = {
            "hand", "head", "eye", "ear", "nose", "mouth", "foot", "leg",
            "finger", "toe", "hair", "stomach", "throat", "back", "neck",
            "bone", "knee", "arm", "shoulder", "lip", "tongue", "tooth",
            "heart", "buttock", "thumb", "nail", "claw", "skin", "face",
            "forehead", "cheek", "chin", "chest", "breast", "rib", "hip",
            "elbow", "wrist", "ankle", "heel", "palm", "sole", "skull",
            "brain", "blood", "sweat", "tear", "urine", "voice", "word",
        }
        if _has_body_part_word(gloss_text, body_part_keywords):
            return "body_part"

        return "relational"

    # Regular N — could still be a body part in some cases
    glosses = entry.get("part_I", {}).get("glosses", [])
    gloss_text = " ".join(g.get("definition", "") for g in glosses).lower()

    # Some body parts are class N but still use physical possession
    body_part_keywords_strict = {
        "hand", "head", "eye", "ear", "nose", "mouth", "foot",
        "finger", "toe", "hair", "stomach", "throat", "buttock",
    }
    if _has_body_part_word(gloss_text, body_part_keywords_strict):
        return "body_part"

    return "general"


def extract_all_nouns(s2e_data):
    """Extract and classify all noun entries from the dictionary."""
    nouns = []
    for entry in s2e_data:
        if not is_noun_entry(entry):
            continue

        hw = entry.get("headword", "")
        nc = get_noun_class(entry)
        stem, suffix = extract_stem(hw)
        poss_type = classify_possession_type(entry, nc)

        glosses = entry.get("part_I", {}).get("glosses", [])
        definition = "; ".join(g.get("definition", "").rstrip(".") for g in glosses)

        nouns.append({
            "entry_id": entry.get("entry_id"),
            "headword": hw,
            "normalized_form": entry.get("normalized_form"),
            "phonetic_form": entry.get("part_I", {}).get("phonetic_form"),
            "grammatical_class": nc,
            "stem": stem,
            "suffix_stripped": suffix,
            "possession_type": poss_type,
            "definition": definition,
            "etymology": entry.get("part_I", {}).get("etymology", {}),
        })

    return nouns


# ===========================================================================
#  KINSHIP POSSESSION — System 1
# ===========================================================================

def build_kinship_paradigms(kinship_data):
    """
    Build full possessive paradigm table for kinship terms.

    Kinship terms have suppletive stems — the 1st, 2nd, and 3rd person
    forms can be entirely different words. These are memorized, not derived.
    """
    paradigms = []
    for term in kinship_data:
        pf = term.get("possessive_forms")
        if pf is None:
            continue  # Affinal verbs, not nouns

        paradigms.append({
            "english": term.get("english_term"),
            "stem": term.get("skiri_term"),
            "grammatical_class": term.get("grammatical_class"),
            "category": term.get("_category", "basic"),
            "forms": {
                "1sg_my": pf.get("my"),
                "2sg_your": pf.get("your"),
                "3sg_his_her": pf.get("his_her"),
                "vocative": pf.get("vocative"),
            },
            "notes": term.get("notes"),
        })

    return paradigms


# ===========================================================================
#  BODY PART POSSESSION — System 2
# ===========================================================================

def generate_body_part_construction(stem, person="1sg", verb_root="ku", mode="indicative"):
    """
    Generate a body-part possessive verb phrase.

    Body parts are expressed via incorporation into the verb phrase:
        MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + POSITION_VERB

    From Blue Book Lesson 5:
        ti + ri + t + kirik + ta → Tiritkirikta (Here is my eye)
        ti + ri + t + paks + ku → Tiritpaksku  (Here is my head)

    Position verbs:
        ku  = sitting (head, round objects)
        ta  = hanging (most body parts)

    Person:
        1sg: ri + t (my)
        2sg: ri + s (your)  — but BB uses ra- (absolutive mode) for questions
        3sg: ri + Ø (his/her)
    """
    # Mode prefix
    modes = {
        "indicative_1_2": "ta",
        "indicative_3": "ti",
        "assertive": "rii",
        "absolutive": "ra",
    }

    agent_prefixes = {
        "1sg": "t",
        "2sg": "s",
        "3sg": "",
    }

    if person in ("1sg", "2sg"):
        mode_pfx = modes.get("indicative_1_2", "ta")
    else:
        mode_pfx = modes.get("indicative_3", "ti")

    agent = agent_prefixes.get(person, "")
    phy_poss = "ri"

    # Assemble: MODE + PHY.POSS + AGENT + STEM + VERB
    parts = [mode_pfx, phy_poss, agent, stem, verb_root]
    # Filter empty strings
    morpheme_string = " + ".join(p for p in parts if p)
    surface = "".join(parts)

    return {
        "morphemes": parts,
        "morpheme_string": morpheme_string,
        "surface_form": surface,
        "labels": ["MODE", "PHY.POSS", "AGENT", "NOUN.STEM", "POS.VERB"],
        "note": "Body-part possession via verb incorporation",
    }


# ===========================================================================
#  GENERAL NOUN POSSESSION — System 3
# ===========================================================================

def generate_agent_possession_info(person="1sg"):
    """
    Document the agent possession construction for general nouns.

    From Grammatical Overview p. 36 and Blue Book Lesson 7:
        ku- (INDF) + MODE + AGENT + ir-/a- (A.POSS) + VERB(uk)

    Blue Book examples (Lesson 7, "Specifying Verbs — Possessives"):
        kti•ratiru paks•kuuku'     my hat
        kti rasiru paks•kuuku'     your hat
        kti•ra•u paks•kuuku'       his hat

    The possessive construction is a VERB PHRASE ("the one that is mine")
    functioning as a modifier. It uses the gerundial (ra-) mode.

    Analysis of BB forms:
        kti = ku + ti (INDF + IND.3)  — base possessive indicator
        ratiru = ra + t + ir + u      — GER + 1.A + A.POSS + exist
        rasiru = ra + s + ir + u      — GER + 2.A + A.POSS + exist
        rau    = ra + Ø + a + u       — GER + 3.A + A.POSS + exist
    """
    constructions = {
        "1sg": {
            "gerundial": "ratiru",
            "breakdown": "ra(GER) + t(1.A) + ir(A.POSS) + u(exist)",
            "english": "my (the one that is mine)",
        },
        "2sg": {
            "gerundial": "rasiru",
            "breakdown": "ra(GER) + s(2.A) + ir(A.POSS) + u(exist)",
            "english": "your (the one that is yours)",
        },
        "3sg": {
            "gerundial": "rau",
            "breakdown": "ra(GER) + Ø(3.A) + a(A.POSS) + u(exist)",
            "english": "his/her (the one that is his/hers)",
        },
    }
    return constructions.get(person, constructions["3sg"])


# ===========================================================================
#  BLUE BOOK TEST CASES
# ===========================================================================

# Hand-extracted from Blue Book lessons — these are the validation set
BLUE_BOOK_POSSESSION_EXAMPLES = [
    # Lesson 5: Body part possession with ri- PHY.POSS
    {
        "source": "BB Lesson 5, p. 21",
        "skiri": "Ti rit•paks•ku",
        "english": "Here is my head",
        "system": "body_part",
        "person": "1sg",
        "noun_stem": "paks",
        "analysis": "ti(IND.3) + ri(PHY.POSS) + t(1.A) + paks(head) + ku(sit)",
    },
    {
        "source": "BB Lesson 5, p. 21",
        "skiri": "Ti rit•kirik•ta",
        "english": "Here is my eye",
        "system": "body_part",
        "person": "1sg",
        "noun_stem": "kirik",
        "analysis": "ti(IND.3) + ri(PHY.POSS) + t(1.A) + kirik(eye) + ta(hang)",
    },
    {
        "source": "BB Lesson 5, p. 21",
        "skiri": "Tiku•paks•taari'",
        "english": "My head hurts",
        "system": "body_part",
        "person": "1sg",
        "noun_stem": "paks",
        "analysis": "ti(IND) + ku(1.P) + paks(head) + taari'(hurt.IMPF)",
        "note": "Passive construction — 'it hurts to-me head'; ku- is patient, not agent poss",
    },
    {
        "source": "BB Lesson 5, p. 22",
        "skiri": "Tiku'ks•taari'",
        "english": "My hand hurts",
        "system": "body_part",
        "person": "1sg",
        "noun_stem": "iks",
        "analysis": "ti(IND) + ku(1.P) + iks(hand) + taari'(hurt.IMPF)",
        "note": "ti+ku+iks → tiku'ks (u+i drops; spelling rule BB p.22)",
    },

    # Lesson 7: Kinship possession
    {
        "source": "BB Lesson 7, p. 32",
        "skiri": "atias",
        "english": "my father",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-ias",
    },
    {
        "source": "BB Lesson 7, p. 32",
        "skiri": "atira'",
        "english": "my mother",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-ira'",
    },
    {
        "source": "BB Lesson 7, p. 32",
        "skiri": "atipat",
        "english": "my grandfather",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-ipat",
    },
    {
        "source": "BB Lesson 7, p. 32",
        "skiri": "atika'",
        "english": "my grandmother",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-ika'",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "aʔas",
        "english": "your father",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-ias",
        "note": "BB spells as 'hags' (OCR may garble ʔ)",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "asas",
        "english": "your mother",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-ira'",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "apat",
        "english": "your grandfather",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-ipat",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "aka'",
        "english": "your grandmother",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-ika'",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "ara",
        "english": "your brother",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-raar",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "atat",
        "english": "your sister",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-taat",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "tiwaciriks",
        "english": "my uncle",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-waciriks",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "paciriks",
        "english": "your uncle",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-waciriks",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "tiki'",
        "english": "my son",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-tiki",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "tsuwat",
        "english": "my daughter",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-tsuwat",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "tiwat",
        "english": "my niece/nephew",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-waat",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "swat",
        "english": "your niece/nephew",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-waat",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "raktiki",
        "english": "my grandchild",
        "system": "kinship",
        "person": "1sg",
        "noun_stem": "-rak-tiikis",
    },
    {
        "source": "BB Lesson 7, p. 33",
        "skiri": "arakis",
        "english": "your grandchild",
        "system": "kinship",
        "person": "2sg",
        "noun_stem": "-rak-tiikis",
    },

    # Lesson 7: Third person kinship
    {
        "source": "BB Lesson 7, p. 34",
        "skiri": "hiʔaastiʔ",
        "english": "his father",
        "system": "kinship",
        "person": "3sg",
        "noun_stem": "-ias",
        "note": "BB spells 'hidsti'' (OCR garbled)",
    },
    {
        "source": "BB Lesson 7, p. 34",
        "skiri": "hisaastiʔ",
        "english": "his mother",
        "system": "kinship",
        "person": "3sg",
        "noun_stem": "-ira'",
        "note": "BB spells 'hisdsti''",
    },
    {
        "source": "BB Lesson 7, p. 34",
        "skiri": "hikaariʔ",
        "english": "his grandmother",
        "system": "kinship",
        "person": "3sg",
        "noun_stem": "-ika'",
        "note": "BB spells 'hikdri''",
    },
    {
        "source": "BB Lesson 7, p. 34",
        "skiri": "ipaaktiʔ",
        "english": "his grandfather",
        "system": "kinship",
        "person": "3sg",
        "noun_stem": "-ipat",
        "note": "BB spells 'hipdkti''",
    },

    # Lesson 7: General possession — specifying verbs
    {
        "source": "BB Lesson 7, p. 35",
        "skiri": "kti•ratiru paks•kuuku'",
        "english": "my hat",
        "system": "general",
        "person": "1sg",
        "noun_stem": "paks•kuuku'",
        "analysis": "ku(INDF)+ti(IND) ra(GER)+t(1.A)+ir(A.POSS)+u(exist) paks-kuuku'(hat)",
    },
    {
        "source": "BB Lesson 7, p. 35",
        "skiri": "kti rasiru paks•kuuku'",
        "english": "your hat",
        "system": "general",
        "person": "2sg",
        "noun_stem": "paks•kuuku'",
        "analysis": "ku(INDF)+ti(IND) ra(GER)+s(2.A)+ir(A.POSS)+u(exist) paks-kuuku'(hat)",
    },
    {
        "source": "BB Lesson 7, p. 35",
        "skiri": "kti•ra•u paks•kuuku'",
        "english": "his hat",
        "system": "general",
        "person": "3sg",
        "noun_stem": "paks•kuuku'",
        "analysis": "ku(INDF)+ti(IND) ra(GER)+Ø(3.A)+a(A.POSS)+u(exist) paks-kuuku'(hat)",
    },

    # Lesson 4: "I have it" — possession via ra (have) verb
    {
        "source": "BB Lesson 4, p. 18",
        "skiri": "Tah•ra",
        "english": "I have it",
        "system": "verbal_have",
        "person": "1sg",
        "analysis": "ta(IND.1/2) + t(1.A) + ra(have)",
        "note": "Verbal possession — not morphological noun possession",
    },
    {
        "source": "BB Lesson 4, p. 18",
        "skiri": "Tas•ta",
        "english": "You have it",
        "system": "verbal_have",
        "person": "2sg",
        "analysis": "ta(IND.1/2) + s(2.A) + ra(have)",
        "note": "r→t after s (sound change Rule 8R)",
    },

    # Lesson 8: Searching for "my dog"
    {
        "source": "BB Lesson 8, p. 38",
        "skiri": "Tah•raspe' asaki",
        "english": "I'm looking for my dog",
        "system": "verbal_have",
        "person": "1sg",
        "analysis": "ta(IND.1/2) + t(1.A) + raspe'(look.for) asaki(dog)",
        "note": "'my' is implied by the 1sg agent — the dog is not morphologically possessed",
    },

    # Patient possession (Grammatical Overview p. 37)
    {
        "source": "Grammatical Overview p. 37",
        "skiri": "tatuuhkuutit aruusaʔ",
        "english": "I killed your horse",
        "system": "patient_possession",
        "person": "2sg",
        "noun_stem": "aruusa",
        "analysis": "ta(IND.1/2) + t(1.A) + a(2.P) + uur(PHY.POSS) + kuutik(kill)",
        "note": "Patient a- (2nd person) + uur- marks that the PATIENT possesses the noun",
    },
]


# ===========================================================================
#  REPORT GENERATION
# ===========================================================================

def generate_report(nouns, kinship_paradigms):
    """Generate comprehensive report on noun possession data."""
    lines = []
    lines.append("=" * 78)
    lines.append("PHASE 3.1.5 — NOUN POSSESSION MORPHOLOGY REPORT")
    lines.append("=" * 78)
    lines.append("")

    # --- Summary statistics ---
    lines.append("NOUN INVENTORY SUMMARY")
    lines.append("-" * 40)
    class_counts = Counter(n["grammatical_class"] for n in nouns)
    poss_type_counts = Counter(n["possession_type"] for n in nouns)
    suffix_counts = Counter(n["suffix_stripped"] for n in nouns if n["suffix_stripped"])

    lines.append(f"Total noun entries: {len(nouns)}")
    lines.append("")
    lines.append("By grammatical class:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {cls:8s} {count:5d}")
    lines.append("")
    lines.append("By possession system:")
    for pt, count in sorted(poss_type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {pt:15s} {count:5d}")
    lines.append("")
    lines.append("Nominal suffix distribution (stripped for stems):")
    for sfx, count in sorted(suffix_counts.items(), key=lambda x: -x[1]):
        label = NOMINAL_SUFFIXES.get(sfx, "")
        lines.append(f"  {sfx:12s} {count:5d}  {label}")
    no_suffix = sum(1 for n in nouns if n["suffix_stripped"] is None)
    lines.append(f"  {'(none)':12s} {no_suffix:5d}  (kinship, irregular, or unsuffixed)")
    lines.append("")

    # --- Kinship paradigms ---
    lines.append("=" * 78)
    lines.append("SYSTEM 1: KINSHIP POSSESSION (N-KIN)")
    lines.append("Suppletive stems — irregular my/your/his forms")
    lines.append("-" * 78)
    lines.append(f"Total kinship terms with paradigms: {len(kinship_paradigms)}")
    lines.append("")
    lines.append(f"{'English':<30} {'My (1sg)':<18} {'Your (2sg)':<18} {'His/Her (3sg)':<18}")
    lines.append("-" * 84)
    for p in kinship_paradigms:
        eng = p["english"][:29]
        my = p["forms"].get("1sg_my") or "—"
        your = p["forms"].get("2sg_your") or "—"
        his = p["forms"].get("3sg_his_her") or "—"
        lines.append(f"  {eng:<28} {my:<18} {your:<18} {his:<18}")
    lines.append("")

    # --- Body part nouns ---
    lines.append("=" * 78)
    lines.append("SYSTEM 2: BODY PART / PHYSICAL POSSESSION")
    lines.append("ri- (PHY.POSS) prefix in verb introducer; noun incorporated")
    lines.append("-" * 78)
    bp_nouns = [n for n in nouns if n["possession_type"] == "body_part"]
    lines.append(f"Body part nouns: {len(bp_nouns)}")
    lines.append("")
    lines.append("Construction template:")
    lines.append("  MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + POS_VERB")
    lines.append("  1sg: ti + ri + t + STEM + ku/ta  →  'Here is my [body part]'")
    lines.append("  2sg: (question) ra + s + STEM + ku/ta  →  'Where is your [body part]?'")
    lines.append("  3sg: ti + ri + Ø + STEM + ku/ta  →  'Here is his/her [body part]'")
    lines.append("")
    lines.append("Sample body part stems:")
    for n in bp_nouns[:20]:
        lines.append(f"  {n['headword']:<20} → stem: {n['stem']:<15} {n['definition'][:40]}")
    if len(bp_nouns) > 20:
        lines.append(f"  ... and {len(bp_nouns) - 20} more")
    lines.append("")

    # --- General nouns ---
    lines.append("=" * 78)
    lines.append("SYSTEM 3: AGENT POSSESSION (general nouns)")
    lines.append("ku-(INDF) + MODE + ir-/a-(A.POSS) + uk(exist) + NOUN")
    lines.append("-" * 78)
    gen_nouns = [n for n in nouns if n["possession_type"] == "general"]
    lines.append(f"General nouns: {len(gen_nouns)}")
    lines.append("")
    lines.append("Construction (from BB Lesson 7, p. 35):")
    lines.append("  1sg: kti ratiru NOUN     = my NOUN")
    lines.append("       ku(INDF)+ti(IND) ra(GER)+t(1A)+ir(A.POSS)+u(exist)")
    lines.append("  2sg: kti rasiru NOUN     = your NOUN")
    lines.append("       ku(INDF)+ti(IND) ra(GER)+s(2A)+ir(A.POSS)+u(exist)")
    lines.append("  3sg: kti rau NOUN        = his/her NOUN")
    lines.append("       ku(INDF)+ti(IND) ra(GER)+Ø(3A)+a(A.POSS)+u(exist)")
    lines.append("")

    # --- N-DEP relational ---
    lines.append("=" * 78)
    lines.append("DEPENDENT NOUNS — RELATIONAL (N-DEP, non-body)")
    lines.append("-" * 78)
    rel_nouns = [n for n in nouns if n["possession_type"] == "relational"]
    lines.append(f"Relational dependent nouns: {len(rel_nouns)}")
    lines.append("These require a possessor but are not body parts.")
    lines.append("Possession mechanism TBD — may use agent or physical possession.")
    lines.append("")
    for n in rel_nouns[:15]:
        lines.append(f"  {n['headword']:<25} stem: {n['stem']:<18} {n['definition'][:40]}")
    if len(rel_nouns) > 15:
        lines.append(f"  ... and {len(rel_nouns) - 15} more")
    lines.append("")

    # --- Blue Book validation ---
    lines.append("=" * 78)
    lines.append("BLUE BOOK VALIDATION EXAMPLES")
    lines.append("-" * 78)
    lines.append(f"Total test cases: {len(BLUE_BOOK_POSSESSION_EXAMPLES)}")
    by_system = Counter(ex["system"] for ex in BLUE_BOOK_POSSESSION_EXAMPLES)
    for sys, count in sorted(by_system.items(), key=lambda x: -x[1]):
        lines.append(f"  {sys:<25} {count:3d} examples")
    lines.append("")
    for ex in BLUE_BOOK_POSSESSION_EXAMPLES:
        lines.append(f"  [{ex['system']:<18}] {ex['skiri']}")
        lines.append(f"                      = {ex['english']}")
        if "analysis" in ex:
            lines.append(f"                      < {ex['analysis']}")
        if "note" in ex:
            lines.append(f"                      NOTE: {ex['note']}")
        lines.append("")

    # --- Suffix distribution for stems ---
    lines.append("=" * 78)
    lines.append("STEM EXTRACTION QUALITY CHECK")
    lines.append("-" * 78)
    lines.append("Verifying stem extraction by comparing stripped suffixes:")
    lines.append("")

    # Show examples of each suffix type
    by_suffix = defaultdict(list)
    for n in nouns:
        by_suffix[n["suffix_stripped"] or "(none)"].append(n)

    for sfx in sorted(by_suffix.keys()):
        examples = by_suffix[sfx][:5]
        lines.append(f"  Suffix: {sfx}")
        for ex in examples:
            lines.append(f"    {ex['headword']:<20} → {ex['stem']:<15} ({ex['definition'][:30]})")
        lines.append("")

    # --- Locative suffixes ---
    lines.append("=" * 78)
    lines.append("LOCATIVE SUFFIXES (from Grammatical Overview Table 4)")
    lines.append("-" * 78)
    for sfx, info in LOCATIVE_SUFFIXES.items():
        lines.append(f"  {sfx:<10} class: {info['class']:<15} {info['meaning']}")
    lines.append("")
    lines.append("  Body part plural: -raar- (before -biriʔ)")
    lines.append("  Example: ikstaaririʔ 'with the hands; on the hands'")
    lines.append("           < iks(hand) + -raar-(PL) + -biriʔ(INST/LOC)")
    lines.append("")

    return "\n".join(lines)


# ===========================================================================
#  CATALOG OUTPUT
# ===========================================================================

def build_catalog(nouns, kinship_paradigms):
    """Build the full noun possession catalog as a JSON structure."""
    return {
        "phase": "3.1.5",
        "description": "Noun Possession Morphology Catalog",
        "systems": {
            "kinship": {
                "description": "System 1: Suppletive kinship stems (N-KIN)",
                "mechanism": "Irregular my/your/his forms, memorized not derived",
                "paradigms": kinship_paradigms,
            },
            "body_part": {
                "description": "System 2: Physical possession via ri- prefix in verb",
                "mechanism": "MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + POS_VERB",
                "template": {
                    "1sg": "ti + ri + t + STEM + VERB",
                    "2sg": "ti + ri + s + STEM + VERB",
                    "3sg": "ti + ri + Ø + STEM + VERB",
                },
                "position_verbs": {
                    "ku": "sitting (head, round objects)",
                    "ta": "hanging (most body parts, limbs)",
                    "arit": "standing",
                },
                "nouns": [n for n in nouns if n["possession_type"] == "body_part"],
            },
            "general": {
                "description": "System 3: Agent possession for regular nouns",
                "mechanism": "ku(INDF) + ti(IND) + GER-POSS-VERB + NOUN",
                "possessive_verbs": {
                    "1sg": {
                        "form": "ratiru",
                        "analysis": "ra(GER) + t(1.A) + ir(A.POSS) + u(exist)",
                    },
                    "2sg": {
                        "form": "rasiru",
                        "analysis": "ra(GER) + s(2.A) + ir(A.POSS) + u(exist)",
                    },
                    "3sg": {
                        "form": "rau",
                        "analysis": "ra(GER) + Ø(3.A) + a(A.POSS) + u(exist)",
                    },
                },
                "nouns": [n for n in nouns if n["possession_type"] == "general"],
            },
            "patient_possession": {
                "description": "System 4: Patient possession via uur- prefix",
                "mechanism": "MODE + AGENT + PATIENT + uur(PHY.POSS) + VERB + NOUN",
                "note": "Used when someone other than the agent possesses the noun",
            },
            "relational": {
                "description": "Dependent nouns (N-DEP) — relational, non-body",
                "mechanism": "TBD — requires further investigation",
                "nouns": [n for n in nouns if n["possession_type"] == "relational"],
            },
        },
        "locative_suffixes": LOCATIVE_SUFFIXES,
        "nominal_suffixes": NOMINAL_SUFFIXES,
        "validation_examples": BLUE_BOOK_POSSESSION_EXAMPLES,
        "statistics": {
            "total_nouns": len(nouns),
            "by_class": dict(Counter(n["grammatical_class"] for n in nouns)),
            "by_possession_type": dict(Counter(n["possession_type"] for n in nouns)),
            "kinship_paradigms": len(kinship_paradigms),
            "validation_examples": len(BLUE_BOOK_POSSESSION_EXAMPLES),
        },
    }


# ===========================================================================
#  DATABASE OPERATIONS
# ===========================================================================

def populate_db(catalog):
    """Create/populate noun possession tables in the SQLite DB."""
    if not DB_PATH.exists():
        print(f"  WARNING: Database not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS noun_stems (
            entry_id TEXT PRIMARY KEY,
            headword TEXT NOT NULL,
            grammatical_class TEXT,
            stem TEXT,
            suffix_stripped TEXT,
            possession_type TEXT,
            definition TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kinship_paradigms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_term TEXT NOT NULL,
            stem TEXT,
            category TEXT,
            form_1sg TEXT,
            form_2sg TEXT,
            form_3sg TEXT,
            vocative TEXT,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS possession_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            skiri_form TEXT NOT NULL,
            english TEXT,
            possession_system TEXT,
            person TEXT,
            noun_stem TEXT,
            morpheme_analysis TEXT,
            notes TEXT
        )
    """)

    # Clear existing data
    cur.execute("DELETE FROM noun_stems")
    cur.execute("DELETE FROM kinship_paradigms")
    cur.execute("DELETE FROM possession_examples")

    # Insert noun stems
    all_nouns = []
    for system_name, system_data in catalog["systems"].items():
        if "nouns" in system_data:
            all_nouns.extend(system_data["nouns"])

    for n in all_nouns:
        if n.get("entry_id"):
            cur.execute("""
                INSERT OR REPLACE INTO noun_stems
                (entry_id, headword, grammatical_class, stem, suffix_stripped, possession_type, definition)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                n["entry_id"], n["headword"], n["grammatical_class"],
                n["stem"], n["suffix_stripped"], n["possession_type"],
                n["definition"],
            ))

    # Insert kinship paradigms
    for p in catalog["systems"]["kinship"]["paradigms"]:
        cur.execute("""
            INSERT INTO kinship_paradigms
            (english_term, stem, category, form_1sg, form_2sg, form_3sg, vocative, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["english"], p["stem"], p.get("category"),
            p["forms"].get("1sg_my"), p["forms"].get("2sg_your"),
            p["forms"].get("3sg_his_her"), p["forms"].get("vocative"),
            p.get("notes"),
        ))

    # Insert validation examples
    for ex in catalog["validation_examples"]:
        cur.execute("""
            INSERT INTO possession_examples
            (source, skiri_form, english, possession_system, person, noun_stem, morpheme_analysis, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ex.get("source"), ex["skiri"], ex.get("english"),
            ex["system"], ex.get("person"), ex.get("noun_stem"),
            ex.get("analysis"), ex.get("note"),
        ))

    conn.commit()
    inserted_nouns = cur.execute("SELECT COUNT(*) FROM noun_stems").fetchone()[0]
    inserted_kin = cur.execute("SELECT COUNT(*) FROM kinship_paradigms").fetchone()[0]
    inserted_ex = cur.execute("SELECT COUNT(*) FROM possession_examples").fetchone()[0]
    conn.close()

    print(f"  OK noun_stems: {inserted_nouns} rows")
    print(f"  OK kinship_paradigms: {inserted_kin} rows")
    print(f"  OK possession_examples: {inserted_ex} rows")
    return True


# ===========================================================================
#  VALIDATION
# ===========================================================================

def _normalize_for_compare(form):
    """Normalize a Skiri form for comparison: glottal stop notation."""
    s = form.replace("ʔ", "'")
    return s


def _shorten_vowels(form):
    """Shorten long vowels (BB convention): aa->a, ii->i, uu->u."""
    s = form
    s = re.sub(r'aa', 'a', s)
    s = re.sub(r'ii', 'i', s)
    s = re.sub(r'uu', 'u', s)
    return s


def _drop_glottals(form):
    """Remove glottal stops entirely (BB sometimes drops them)."""
    return form.replace("'", "").replace("ʔ", "")


def _strip_3sg_hi_prefix(form):
    """BB uses hi- prefix for 3rd person kinship; appendix3 uses i-."""
    if form.startswith("hi"):
        return "i" + form[2:]
    return form


def validate_against_blue_book(kinship_paradigms):
    """Validate kinship paradigms against Blue Book examples."""
    results = {"exact": 0, "close": 0, "fail": 0, "no_paradigm": 0, "details": []}

    # Build lookup from kinship paradigms
    kin_lookup = {}
    for p in kinship_paradigms:
        eng = p["english"].lower()
        kin_lookup[eng] = {"forms": p["forms"], "stem": p.get("stem")}

    bb_kinship = [ex for ex in BLUE_BOOK_POSSESSION_EXAMPLES if ex["system"] == "kinship"]

    for ex in bb_kinship:
        bb_form = ex["skiri"]
        person = ex["person"]
        bb_norm = _normalize_for_compare(bb_form)

        # Try to find matching paradigm
        form_key = f"{person}_{'my' if person == '1sg' else 'your' if person == '2sg' else 'his_her'}"

        best_match = None
        best_status = None
        for kin_eng, kin_data in kin_lookup.items():
            expected = kin_data["forms"].get(form_key)
            if not expected:
                continue
            exp_norm = _normalize_for_compare(expected)

            # Exact match (modulo glottal notation)
            if exp_norm == bb_norm:
                best_match = expected
                best_status = "EXACT"
                break

            # Close match: try vowel length normalization
            if _shorten_vowels(exp_norm) == _shorten_vowels(bb_norm):
                best_match = expected
                best_status = "CLOSE (vowel length)"
                continue

            # Close match: try glottal stop deletion (BB sometimes drops them)
            if _drop_glottals(exp_norm) == _drop_glottals(bb_norm):
                best_match = expected
                best_status = "CLOSE (glottal stop dropped)"
                continue

            # Close match: try vowel length + glottal drop together
            if _shorten_vowels(_drop_glottals(exp_norm)) == _shorten_vowels(_drop_glottals(bb_norm)):
                best_match = expected
                best_status = "CLOSE (vowel length + glottal)"
                continue

            # Close match: try vowel shortening + final vowel drop (BB truncates)
            exp_short = _shorten_vowels(exp_norm)
            bb_short = _shorten_vowels(bb_norm)
            if exp_short.rstrip("aeiou") == bb_short or exp_short == bb_short.rstrip("aeiou"):
                best_match = expected
                best_status = "CLOSE (vowel length + final vowel)"
                continue

            # Close match: try hi-/i- prefix swap for 3rd person
            if person == "3sg":
                bb_stripped = _strip_3sg_hi_prefix(bb_norm)
                exp_stripped = _strip_3sg_hi_prefix(exp_norm)
                if exp_stripped == bb_stripped:
                    best_match = expected
                    best_status = "CLOSE (hi-/i- prefix)"
                    continue
                # Try both normalizations together
                if _shorten_vowels(exp_stripped) == _shorten_vowels(bb_stripped):
                    best_match = expected
                    best_status = "CLOSE (hi-/i- + vowel length)"
                    continue

        if best_status and best_status.startswith("EXACT"):
            results["exact"] += 1
            results["details"].append({
                "status": "EXACT",
                "bb_form": bb_form,
                "expected": best_match,
                "english": ex["english"],
            })
        elif best_status:
            results["close"] += 1
            results["details"].append({
                "status": best_status,
                "bb_form": bb_form,
                "expected": best_match,
                "english": ex["english"],
                "note": f"BB form differs: {best_status}",
            })
        else:
            results["no_paradigm"] += 1
            results["details"].append({
                "status": "NO_PARADIGM",
                "bb_form": bb_form,
                "english": ex["english"],
                "note": "No matching paradigm in appendix3 data",
            })

    # Print detailed results (use buffer write for Unicode safety on Windows cp1252)
    def _safe_print(text):
        try:
            sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        except AttributeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))

    _safe_print(f"\nKinship validation: {results['exact']} exact, {results['close']} close, "
                f"{results['no_paradigm']} no_paradigm (of {len(bb_kinship)} BB examples)")
    _safe_print("")
    for d in results["details"]:
        status = d["status"]
        marker = "OK" if status == "EXACT" else "~" if "CLOSE" in status else "??"
        line = f"  [{marker}] {d['bb_form']:<18} = {d['english']}"
        if d.get("expected"):
            line += f"  (app3: {d['expected']})"
        if d.get("note"):
            line += f"  -- {d['note']}"
        _safe_print(line)

    return results


# ===========================================================================
#  MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 3.1.5 — Noun Possession Morphology")
    parser.add_argument("--extract", action="store_true", help="Extract and categorize all nouns")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--validate", action="store_true", help="Validate against Blue Book")
    parser.add_argument("--db", action="store_true", help="Populate database tables")
    parser.add_argument("--generate", metavar="HEADWORD", help="Generate possessive forms for a noun")
    parser.add_argument("--all", action="store_true", help="Run all steps")

    args = parser.parse_args()

    if not any([args.extract, args.report, args.validate, args.db, args.generate, args.all]):
        parser.print_help()
        return

    # Load data
    print("Loading data...")
    s2e_data = load_s2e()
    kinship_data = load_kinship()

    if not s2e_data:
        print("ERROR: Could not load S2E data. Check path:", S2E_FILE)
        sys.exit(1)

    print(f"  Loaded {len(s2e_data)} S2E entries")
    print(f"  Loaded {len(kinship_data)} kinship terms")

    # Extract nouns
    print("\nExtracting nouns...")
    nouns = extract_all_nouns(s2e_data)
    print(f"  Found {len(nouns)} noun entries")

    # Build kinship paradigms
    kinship_paradigms = build_kinship_paradigms(kinship_data)
    print(f"  Built {len(kinship_paradigms)} kinship paradigms")

    if args.extract or args.all:
        # Build and save catalog
        catalog = build_catalog(nouns, kinship_paradigms)
        os.makedirs(EXTRACTED_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\nOK Catalog saved: {OUTPUT_FILE}")
        print(f"  {catalog['statistics']}")

    if args.report or args.all:
        report = generate_report(nouns, kinship_paradigms)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = REPORTS_DIR / "phase_3_1_5_noun_possession.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nOK Report saved: {report_path}")

    if args.validate or args.all:
        print("\nValidating against Blue Book...")
        results = validate_against_blue_book(kinship_paradigms)

    if args.db or args.all:
        print("\nPopulating database...")
        catalog = build_catalog(nouns, kinship_paradigms)
        populate_db(catalog)

    if args.generate:
        # Find the entry
        target = args.generate.lower()
        match = None
        for n in nouns:
            if n["headword"].lower() == target or (n.get("normalized_form") or "").lower() == target:
                match = n
                break

        if not match:
            print(f"Noun '{args.generate}' not found in dictionary.")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"POSSESSIVE FORMS FOR: {match['headword']}")
        print(f"  Class: {match['grammatical_class']}")
        print(f"  Stem: {match['stem']}")
        print(f"  Possession system: {match['possession_type']}")
        print(f"  Definition: {match['definition']}")
        print(f"{'='*60}")

        if match["possession_type"] == "kinship":
            # Look up in kinship paradigms
            for p in kinship_paradigms:
                if p["stem"] == match["headword"] or match["headword"] in (
                    p["forms"].get("1sg_my", ""),
                    p["forms"].get("2sg_your", ""),
                    p["forms"].get("3sg_his_her", ""),
                ):
                    print(f"\n  Kinship term: {p['english']}")
                    print(f"  My:      {p['forms'].get('1sg_my', '—')}")
                    print(f"  Your:    {p['forms'].get('2sg_your', '—')}")
                    print(f"  His/Her: {p['forms'].get('3sg_his_her', '—')}")
                    break
            else:
                print("  (Kinship paradigm not found in appendix3 data)")

        elif match["possession_type"] == "body_part":
            stem = match["stem"].rstrip("-")
            print(f"\n  Body part incorporation:")
            for person in ["1sg", "2sg", "3sg"]:
                result = generate_body_part_construction(stem, person=person)
                print(f"  {person}: {result['morpheme_string']}")
                print(f"         -> {result['surface_form']} (COMPUTED -- needs sound change rules)")

        elif match["possession_type"] == "general":
            print(f"\n  Agent possession construction:")
            for person in ["1sg", "2sg", "3sg"]:
                info = generate_agent_possession_info(person)
                print(f"  {person}: kti {info['gerundial']} {match['headword']}")
                print(f"         = {info['english']}")
                print(f"         < {info['breakdown']}")

        else:
            print(f"\n  Possession mechanism for '{match['possession_type']}' not yet implemented.")


if __name__ == "__main__":
    main()
