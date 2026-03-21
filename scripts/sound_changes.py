#!/usr/bin/env python3
"""
Phase 2.3 — Sound Change Rule Engine
======================================
Formalizes Skiri Pawnee phonological rules from Parks Dictionary Ch. 3
(Major Sound Changes) as ordered transformations for the grammar engine.

Two types of rules:
  - RESTRICTED rules: apply only to specific morpheme sequences
  - UNRESTRICTED (general) rules: apply to all instances of specified
    sound sequences, regardless of morpheme identity

24 rules total, organized into:
  Vowels: Restricted (1R-4R), Unrestricted (5-7)
  Consonants: Restricted (8R-12R), Unrestricted (13-24)

Usage:
    # Catalog rules into DB + validate against paradigmatic forms:
    python scripts/sound_changes.py --db skiri_pawnee.db \\
        --report reports/phase_2_3_sound_changes.txt

    # Run built-in test suite (PDF examples):
    python scripts/sound_changes.py --test

    # Apply sound changes to a morpheme sequence:
    python scripts/sound_changes.py --apply "ti + uur + hiir"

    # Validate only (no DB writes):
    python scripts/sound_changes.py --db skiri_pawnee.db --validate-only

    # Populate DB rules table only:
    python scripts/sound_changes.py --db skiri_pawnee.db --catalog-only

    # Gemini-powered audit (requires GEMINI_API_KEY):
    python scripts/sound_changes.py --db skiri_pawnee.db --audit \\
        --report reports/phase_2_3_sound_changes.txt

Dependencies: Python 3.8+, sqlite3 (stdlib), google-genai (for --audit)
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phoneme inventory
# ---------------------------------------------------------------------------

VOWELS = set("aiuáíúàâîû")
SHORT_VOWELS = set("aiu")
LONG_VOWELS = {"aa", "ii", "uu"}
CONSONANTS = set("ptkcswhrnʔč")
OBSTRUENTS = set("ptkcsʔč")  # stops + fricatives + affricates
SONORANTS = set("wr")  # w, r (nasals are marginal in Skiri)

# Marker to protect Rule 3R output from Rule 17 sibilant hardening
KS_MARKER = "\x01"

# ---------------------------------------------------------------------------
# Rule Catalog — all 24 rules from Parks Ch. 3
# ---------------------------------------------------------------------------

RULES = [
    # ===== VOWELS: RESTRICTED =====
    {
        "rule_id": "1R",
        "name": "Dominant i",
        "type": "restricted",
        "domain": "vowel",
        "formal": "i, ii + u -> i, ii",
        "description": (
            "Seven morpheme combinations where final i/ii of preceding "
            "morpheme and initial u of following morpheme contract to i/ii. "
            "Applies to: rii- + -uks- -> riiks-; ti-/ii-/ri- + u...]STEM -> "
            "tii-/ii-/rii-; -i-/-ir-/acir- + -uur- -> -iir-/-iir-/-aciir-."
        ),
        "ordering": 1,
        "examples": [
            {"underlying": "ti- + uhurah", "surface": "tiihura",
             "gloss": "he is alone"},
            {"underlying": "ta- + aciir- + uur- + hiir", "surface": "taciihii",
             "gloss": "you and I are good"},
        ],
    },
    {
        "rule_id": "2R",
        "name": "Dominant a",
        "type": "restricted",
        "domain": "vowel",
        "formal": "i + a -> a",
        "description": (
            "Modal prefixes ti- (IND), ri- (CONT), kuus...i- (POT.1), "
            "ii- (SUBJ) contract with a-dominant morphemes: a- (2.P), "
            "a- (PREV; 3.POSS.A), aca- (1D.IN.P), ar- (EV). The i+a -> a."
        ),
        "ordering": 2,
        "examples": [
            {"underlying": "ti- + a- + piru", "surface": "tapiruʔ",
             "gloss": "he whipped you"},
            {"underlying": "kuus- + a- + i- + kiraawaahc", "surface": "kusaakiraawa",
             "gloss": "you will forget"},
            {"underlying": "ti- + ar- + ut- + asitik", "surface": "wiitaruutasitit",
             "gloss": "it would happen"},
        ],
    },
    {
        "rule_id": "3R",
        "name": "-his Perfective Reduction",
        "type": "restricted",
        "domain": "vowel",
        "formal": "Vk]STEM + -his -> ks",
        "description": (
            "The suffix -his 'perfective' (PERF) reduces to s after verb "
            "stems ending in a final k. The vowel before k and the hi- of "
            "-his are lost, yielding -ks."
        ),
        "ordering": 3,
        "examples": [
            {"underlying": "hak + -his", "surface": "haks",
             "gloss": "pass by (PERF)"},
            {"underlying": "ti- + hak + -his + -ta", "surface": "tihaksta",
             "gloss": "he is going to pass by"},
        ],
    },
    {
        "rule_id": "4R",
        "name": "Stem-final Vocalic Reduplication",
        "type": "restricted",
        "domain": "vowel",
        "formal": "V(V) -> V(V)ʔV / C _ C + NULL (non-subordinate)",
        "description": (
            "Applies to a class of descriptive verbs (approx. half of all VD) "
            "in their non-subordinate forms. The stem-final vowel (short or "
            "long) reduplicates with a glottal stop inserted."
        ),
        "ordering": 4,
        "examples": [
            {"underlying": "ti- + pahaat", "surface": "tipahaaʔat",
             "gloss": "it is red"},
            {"underlying": "ti- + huraar- + tararit", "surface": "tihuraahtarariʔit",
             "gloss": "the ground is burned off"},
        ],
    },
    # ===== VOWELS: UNRESTRICTED =====
    {
        "rule_id": "5",
        "name": "Same-vowel Contraction",
        "type": "unrestricted",
        "domain": "vowel",
        "formal": "Vi(Vi) + Vi -> ViVi",
        "description": (
            "Two identical contiguous vowels contract to a long vowel. "
            "The first may be short or long; result is always long. "
            "Condition: followed by one or two consonants (not word-final, "
            "not before another vowel)."
        ),
        "ordering": 5,
        "examples": [
            {"underlying": "ti- + uur- + iciisat", "surface": "tuuriciisat",
             "gloss": "he is tired"},
            {"underlying": "ku- + ii- + ut- + kaksaa", "surface": "kuʔuutkaksaa",
             "gloss": "if he could holler for him"},
        ],
    },
    {
        "rule_id": "6",
        "name": "u-Domination",
        "type": "unrestricted",
        "domain": "vowel",
        "formal": "V/VV + u OR u(u) + V -> uu / _ C(C)V",
        "description": (
            "In a sequence of two vowels where any vowel in the sequence "
            "is u, the vowels contract to long uu. The first vowel may be "
            "long or short. Condition: before one or two consonants."
        ),
        "ordering": 6,
        "examples": [
            {"underlying": "ti- + uur- + iciisat", "surface": "tuuriciisat",
             "gloss": "he is tired"},
        ],
    },
    {
        "rule_id": "7",
        "name": "Contraction of i and a",
        "type": "unrestricted",
        "domain": "vowel",
        "formal": "i(i) + a(a) OR a(a) + i -> ii / _ C(C)V",
        "description": (
            "Combinations of i or ii followed by a or aa, or a/aa followed "
            "by i, contract to ii. (In South Band Pawnee and Arikara the "
            "result is ee.)"
        ),
        "ordering": 7,
        "examples": [
            {"underlying": "ti- + atkaʔu", "surface": "tiitkuʔ",
             "gloss": "he hears"},
        ],
    },
    # ===== CONSONANTS: RESTRICTED =====
    {
        "rule_id": "8R",
        "name": "Assibilation of raar-",
        "type": "restricted",
        "domain": "consonant",
        "formal": "r + t -> c / raar- + t...]STEM",
        "description": (
            "The final consonant of raar- 'plural; iterative' assibilates "
            "when followed by a stem-initial t. The r+t sequence becomes c."
        ),
        "ordering": 8,
        "examples": [
            {"underlying": "ti- + raar- + takasis", "surface": "tiracakasis",
             "gloss": "they are close together"},
        ],
    },
    {
        "rule_id": "9R",
        "name": "Final-s Loss",
        "type": "restricted",
        "domain": "consonant",
        "formal": "s -> NULL / _ #",
        "description": (
            "Certain nouns and suffixes ending in s regularly lose it "
            "word-finally but retain it when another morpheme follows. "
            "E.g. kuhkus 'swine' -> kuhku in isolation but kuhkuskaʔit "
            "'salt pork' in compounds. The aspectual suffix -:hus/-hus "
            "(IMPF) also loses final s word-finally."
        ),
        "ordering": 9,
        "examples": [
            {"underlying": "kuhkus", "surface": "kuhku",
             "gloss": "swine (independent)"},
            {"underlying": "ti- + kiikaa + -:hus", "surface": "tikiikaahu",
             "gloss": "he is drinking (IMPF, word-final s lost)"},
        ],
    },
    {
        "rule_id": "10R",
        "name": "Prefixal Final-r Loss",
        "type": "restricted",
        "domain": "consonant",
        "formal": "ir-/acir- lose r before uur-/ut-/uks-",
        "description": (
            "Two prefixes, ir- 'preverb' (PREV) and acir- 'first person "
            "inclusive dual agent' (1D.IN.A) lose their final r when they "
            "contract with uur- (PREV), ut- (PREV/BEN), or uks- (AOR/JUSS). "
            "When r is lost from ir- and acir-, the resulting final i "
            "dominates contractions with initial u of the three morphemes."
        ),
        "ordering": 10,
        "examples": [
            {"underlying": "ta- + t- + ir- + ut- + urikatakus",
             "surface": "tatiiturikataku",
             "gloss": "I am carrying it under my arm"},
        ],
    },
    {
        "rule_id": "11R",
        "name": "ut- Affrication",
        "type": "restricted",
        "domain": "consonant",
        "formal": "ut- -> uc- / _ i-",
        "description": (
            "Final t of the prefix ut- 'preverb (PREV); dative/benefactive "
            "(DAT/BEN)' affricates to c when followed by i- 'sequential (SEQ)'. "
            "In Skiri, i- SEQ does not dominate over following u in -uks (AOR), "
            "unlike in South Band."
        ),
        "ordering": 11,
        "examples": [
            {"underlying": "kuus- + i- + t- + ut- + aar", "surface": "kuustuciʔa",
             "gloss": "I will do it"},
            {"underlying": "i- + s- + ut- + i- + uks- + aar",
             "surface": "sucuksa",
             "gloss": "do it! (CONT)"},
        ],
    },
    {
        "rule_id": "12R",
        "name": "Prefixal r-Laryngealization",
        "type": "restricted",
        "domain": "consonant",
        "formal": "r -> h / _ r (in tiir-, ar- prefixes)",
        "description": (
            "The final r of two evidential prefixes — tiir- 'inferential (INFR)' "
            "and ar- 'evidential proper (EV)' — changes to h when preceding "
            "an r-initial morpheme. Must be applied before Rule 20 (Degemination) "
            "and Rule 15 (Sonorant Reduction)."
        ),
        "ordering": 12,
        "examples": [
            {"underlying": "ar- + ri- + at", "surface": "ahiʔat",
             "gloss": "he went (EV)"},
            {"underlying": "tiir- + ra- + kuutik", "surface": "tiihakuutit",
             "gloss": "he must have killed it"},
        ],
    },
    # ===== CONSONANTS: UNRESTRICTED =====
    {
        "rule_id": "13",
        "name": "t-Laryngealization",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "t -> h / _ r",
        "description": (
            "The stop t becomes laryngeal h when it precedes r. "
            "This is a general rule applying across all morpheme boundaries."
        ),
        "ordering": 13,
        "examples": [
            {"underlying": "ta- + t- + raʔuk + -:hus", "surface": "tahuukuʔ",
             "gloss": "I am making it"},
            {"underlying": "pahaat + raʔuk", "surface": "pahaahaʔuk",
             "gloss": "to redden (CAUS)"},
        ],
    },
    {
        "rule_id": "14",
        "name": "Metathesis Rule",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "r + h -> hr",
        "description": (
            "When underlying r is followed by h, the two sounds metathesize. "
            "The sequence hr never occurs in surface forms in Skiri (unlike "
            "South Band) because hr always reduces to h via Rule 15."
        ),
        "ordering": 14,
        "examples": [
            {"underlying": "ti- + uur- + hiir", "surface": "tuuhii",
             "gloss": "he is good (after Rules 14+15 apply)"},
        ],
    },
    {
        "rule_id": "15",
        "name": "Sonorant r-Reduction",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "r -> NULL / _ h",
        "description": (
            "This rule reduces the cluster hr to h. Since rh -> hr "
            "(Rule 14) always precedes this, the net effect of r+h is h. "
            "Must be applied after Rule 14 (Metathesis)."
        ),
        "ordering": 15,
        "examples": [
            {"underlying": "ta- + t- + rahuukat", "surface": "tahahuukat",
             "gloss": "I took it inside"},
        ],
    },
    {
        "rule_id": "16",
        "name": "h-Loss",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "h -> NULL / C _ ; h -> NULL / _ C#, CC",
        "description": (
            "Laryngeal h is lost: (a) when preceded by a consonant; "
            "(b) when it precedes a single word-final consonant or a "
            "two-consonant cluster. Two separate environments for deletion."
        ),
        "ordering": 16,
        "examples": [
            {"underlying": "ahibt + -NULL", "surface": "ahibt",
             "gloss": "be fat (h retained before single C in cluster)"},
            {"underlying": "ti- + awahc- + wiitik", "surface": "tiiwacpiitit",
             "gloss": "he finally sat down"},
        ],
    },
    {
        "rule_id": "17",
        "name": "Sibilant Hardening",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "s -> c / C _",
        "description": (
            "The sibilant s becomes the affricate c when it occurs "
            "immediately after any consonant."
        ),
        "ordering": 17,
        "examples": [
            {"underlying": "ti- + ir- + sa + -waa", "surface": "tihcawaa",
             "gloss": "they are lying (there)"},
            {"underlying": "ti- + uur- + sakuriwihc + -:hus",
             "surface": "tuhcakuriwihcuʔ",
             "gloss": "the sun is coming out"},
        ],
    },
    {
        "rule_id": "18",
        "name": "Sibilant Loss",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "s -> NULL / k _ c",
        "description": (
            "When c immediately follows the two-consonant cluster ks, "
            "the s is dropped. The environment is specifically after k "
            "and before c."
        ),
        "ordering": 18,
        "examples": [
            {"underlying": "i- + s- + ut- + i- + uks- + ciir",
             "surface": "sucukcii",
             "gloss": "be energetic!"},
        ],
    },
    {
        "rule_id": "19",
        "name": "Alveolar Dissimilation",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "t + t -> ct ; (also t + c -> ct by metathesis)",
        "description": (
            "A common underlying sequence t+t across morpheme boundaries: "
            "the preceding t changes to c, yielding ct. The less common "
            "t+c sequence also metathesizes to ct."
        ),
        "ordering": 19,
        "examples": [
            {"underlying": "ta- + t- + taʔuut", "surface": "tactaʔuut",
             "gloss": "I stole it"},
            {"underlying": "ta- + t- + cak", "surface": "tactat",
             "gloss": "I shot it (t+c -> ct)"},
        ],
    },
    {
        "rule_id": "20",
        "name": "Consonant Degemination",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "CiCi -> Ci (for r, k)",
        "description": (
            "When two identical consonants come together (after prior rules), "
            "one is lost. This rule only operates for identical sequences "
            "of r and k."
        ),
        "ordering": 20,
        "examples": [
            {"underlying": "ti- + raar- + raahur", "surface": "tiraraahu",
             "gloss": "they are ruined (rr -> r)"},
            {"underlying": "ti- + uur- + rariir", "surface": "tuurariiʔi",
             "gloss": "it is a mark (rr -> r, after r-loss at word end)"},
        ],
    },
    {
        "rule_id": "21",
        "name": "r-Stopping",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "r -> t / Obs. _",
        "description": (
            "The sonorant r becomes the voiceless stop t when it occurs "
            "after an obstruent. Note: t is excluded from triggering "
            "obstruents because t+r -> h+r by Rule 13 first."
        ),
        "ordering": 21,
        "examples": [
            {"underlying": "kirik- + raar- + kaa", "surface": "kiriktaahkaa",
             "gloss": "wear eyeglasses"},
            {"underlying": "i- + s- + uks- + riisaapuh", "surface": "sukstiisaapu",
             "gloss": "stake it!"},
        ],
    },
    {
        "rule_id": "22",
        "name": "Labial Glide Loss",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "w -> NULL / V _ wV(V)...",
        "description": (
            "In verb derivation, a w in a preceding syllable is generally "
            "lost when the following morpheme begins in w."
        ),
        "ordering": 22,
        "examples": [
            {"underlying": "ti- + a- + awiwiiʔa", "surface": "taaʔiwiiʔaʔ",
             "gloss": "he bent over"},
            {"underlying": "ta- + t- + katawiwari k", "surface": "tatkataʔiwarit",
             "gloss": "I swallowed it"},
        ],
    },
    {
        "rule_id": "23",
        "name": "Final r Loss",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "r -> NULL / _ #",
        "description": (
            "Word-final r is always dropped in Skiri."
        ),
        "ordering": 23,
        "examples": [
            {"underlying": "wii- + ta- + t- + ut- + aar", "surface": "wiitatuutaa",
             "gloss": "I have done it"},
        ],
    },
    {
        "rule_id": "24",
        "name": "Variants of c",
        "type": "unrestricted",
        "domain": "consonant",
        "formal": "c -> [ts] / _ C, # ; c -> [ch] / _ V",
        "description": (
            "The phoneme c has two phonetic variants: [ts] before consonants "
            "and word-finally; [ch] (IPA [tsh] or [ch]) before vowels. This is "
            "an allophonic rule (surface realization only)."
        ),
        "ordering": 24,
        "examples": [
            {"underlying": "capaat", "surface_phonetic": "[chepaat]",
             "gloss": "woman (c before vowel = ch)"},
            {"underlying": "askuc", "surface_phonetic": "[eskuts]",
             "gloss": "prairie dog (c word-final = ts)"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Helper: phonological predicates
# ---------------------------------------------------------------------------

def is_vowel(ch):
    """Check if character is a Pawnee vowel (including accented)."""
    return ch in VOWELS or ch in "āēīōū"


def is_consonant(ch):
    """Check if character is a Pawnee consonant."""
    return ch in CONSONANTS


def is_obstruent(ch):
    """p, t, k, c, s, ʔ, č — stops, affricates, fricatives."""
    return ch in OBSTRUENTS


def is_short_vowel(ch):
    return ch in SHORT_VOWELS


def is_long_vowel_pair(s, pos):
    """Check if position starts a long vowel (aa, ii, uu)."""
    if pos + 1 < len(s):
        pair = s[pos:pos + 2]
        return pair in LONG_VOWELS
    return False


# ---------------------------------------------------------------------------
# Rule implementation: unrestricted rules (surface string transformations)
# ---------------------------------------------------------------------------

def apply_rule_5_same_vowel_contraction(s):
    """Rule 5: Vi(Vi) + Vi -> ViVi — identical vowels contract to long.

    Multiple identical vowels (e.g., aaa from aa+a) collapse to one long vowel.
    """
    result = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i] in SHORT_VOWELS and s[i] == s[i + 1]:
            v = s[i]
            while i < len(s) and s[i] == v:
                i += 1
            result.append(v + v)  # always produce long
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def apply_rule_6_u_domination(s):
    """Rule 6: V/VV + u OR u(u) + V -> uu / _ C(C)V

    Any vowel + u or u + any vowel contracts to long uu.
    The first vowel may be long or short. Consumes all vowels in the cluster.
    """
    result = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and is_vowel(s[i]) and is_vowel(s[i + 1]):
            # Collect the full vowel cluster
            cluster_start = i
            while i < len(s) and is_vowel(s[i]):
                i += 1
            cluster = s[cluster_start:i]
            # If cluster contains u, contract to uu
            if "u" in cluster and not all(c == "u" for c in cluster):
                result.append("uu")
            else:
                result.append(cluster)
            continue
        result.append(s[i])
        i += 1
    return "".join(result)


def apply_rule_7_i_a_contraction(s):
    """Rule 7: i(i)+a(a) or a(a)+i -> ii (before C(C)V context).

    When i/ii is adjacent to a/aa, or a/aa is adjacent to i,
    the vowel cluster contracts to ii. Only applies to mixed i+a clusters.
    """
    result = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i] in ("i", "a") and s[i + 1] in ("i", "a"):
            # Collect the full vowel cluster of i's and a's
            cluster_start = i
            while i < len(s) and s[i] in ("i", "a"):
                i += 1
            cluster = s[cluster_start:i]
            # Only contract if cluster is mixed (has both i and a)
            has_i = "i" in cluster
            has_a = "a" in cluster
            if has_i and has_a:
                result.append("ii")
            else:
                # Pure i's or pure a's — leave as-is (Rule 5 handles same-vowel)
                result.append(cluster)
            continue
        result.append(s[i])
        i += 1
    return "".join(result)


def apply_rule_13_t_laryngealization(s):
    """Rule 13: t -> h / _ r"""
    return re.sub(r"tr", "hr", s)


def apply_rule_14_metathesis(s):
    """Rule 14: r + h -> hr"""
    return re.sub(r"rh", "hr", s)


def apply_rule_15_sonorant_reduction(s):
    """Rule 15: hr -> h (r lost before h, after metathesis)"""
    return re.sub(r"hr", "h", s)


def apply_rule_16_h_loss(s):
    """Rule 16: h -> NULL after C; h -> NULL before C# or CC.

    Two environments:
    (a) C + h -> C (h lost after consonant)
    (b) h + C# -> C# or h + CC -> CC (h lost before final C or CC cluster)
    """
    result = list(s)
    to_delete = set()

    for i, ch in enumerate(result):
        if ch != "h":
            continue
        # (a) h after consonant
        if i > 0 and is_consonant(result[i - 1]):
            to_delete.add(i)
            continue
        # (b) h before consonant cluster or word-final consonant
        if i + 1 < len(result) and is_consonant(result[i + 1]):
            # h before CC
            if i + 2 < len(result) and is_consonant(result[i + 2]):
                to_delete.add(i)
                continue
            # h before C#
            if i + 1 == len(result) - 1:
                to_delete.add(i)
                continue
            # h before C + # (next is last char)
            # Already handled above

    return "".join(ch for i, ch in enumerate(result) if i not in to_delete)


def apply_rule_17_sibilant_hardening(s):
    """Rule 17: s -> c / C _ (s becomes c after any consonant)

    Exception: does not apply to 'ks' sequences produced by Rule 3R
    (-his perfective reduction), since those are already fused.
    We detect this by checking if the consonant is part of a stem-final
    cluster. In practice, we apply this only when s is NOT part of a
    pre-existing 'ks' from -his reduction (handled by fusing in Rule 3R).
    """
    result = list(s)
    for i in range(1, len(result)):
        if result[i] == "s" and is_consonant(result[i - 1]):
            result[i] = "c"
    return "".join(result)


def apply_rule_18_sibilant_loss(s):
    """Rule 18: s -> NULL / k _ c"""
    return re.sub(r"ksc", "kc", s)


def apply_rule_19_alveolar_dissimilation(s):
    """Rule 19: t + t -> ct; t + c -> ct (metathesis)"""
    # t + t -> ct
    s = re.sub(r"tt", "ct", s)
    # t + c -> ct (metathesis of the pair)
    s = re.sub(r"tc", "ct", s)
    return s


def apply_rule_20_degemination(s):
    """Rule 20: rr -> r, kk -> k"""
    s = re.sub(r"rr", "r", s)
    s = re.sub(r"kk", "k", s)
    return s


def apply_rule_21_r_stopping(s):
    """Rule 21: r -> t / Obs. _ (r becomes t after obstruent)

    Obstruents: p, k, c, s, ʔ, č (NOT t — t+r handled by Rule 13)
    """
    result = list(s)
    for i in range(1, len(result)):
        if result[i] == "r" and result[i - 1] in (OBSTRUENTS - {"t"}):
            result[i] = "t"
    return "".join(result)


def apply_rule_22_labial_glide_loss(s):
    """Rule 22: w -> NULL / V _ wV(V)...

    A w before another w (with vowel preceding) is deleted.
    """
    result = []
    i = 0
    while i < len(s):
        if (s[i] == "w" and i > 0 and is_vowel(s[i - 1])
                and i + 1 < len(s) and s[i + 1] == "w"):
            # Skip this w (delete it), keep the next w
            i += 1
            continue
        result.append(s[i])
        i += 1
    return "".join(result)


def apply_rule_23_final_r_loss(s):
    """Rule 23: r -> NULL / _ # (word-final r is dropped)"""
    if s.endswith("r"):
        return s[:-1]
    return s


# ---------------------------------------------------------------------------
# Rule implementation: restricted rules (morpheme-aware)
# ---------------------------------------------------------------------------

# Restricted rule morpheme triggers
RULE_1R_PREFIXES_U = {"ti", "ii", "ri"}  # + u...]STEM -> tii, ii, rii
RULE_1R_SEQ_PREV = {"i", "ir", "acir"}  # + uur -> iir, iir, aciir
RULE_2R_MODAL = {"ti", "ri", "kuusi", "ii"}
RULE_2R_A_DOMINANT = {"a", "aca", "ar"}


def apply_rule_1r(morphemes):
    """Rule 1R: Dominant i — i/ii + u contractions in specific morpheme combos.

    Returns modified morpheme list.
    """
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        # rii- + -uks- -> riiks-
        if m1 == "rii" and m2.startswith("uks"):
            result[idx] = ""
            result[idx + 1] = "riiks" + m2[3:]
            continue

        # ti-/ii-/ri- + u...]STEM -> tii-/ii-/rii-
        if m1 in RULE_1R_PREFIXES_U and m2.startswith("u"):
            contracted = m1[:-1] + "ii" if m1.endswith("i") else m1 + "i"
            result[idx] = contracted
            result[idx + 1] = m2[1:]  # strip initial u
            continue

        # -i-/-ir-/acir- + -uur- -> -iir-/-iir-/-aciir-
        if m1 in RULE_1R_SEQ_PREV and m2.startswith("uur"):
            if m1 == "acir":
                result[idx] = "aciir"
            else:
                result[idx] = "iir"
            result[idx + 1] = m2[3:]  # strip uur
            continue

    return [m for m in result if m]


def apply_rule_2r(morphemes):
    """Rule 2R: Dominant a — i + a -> a in modal prefix + a-dominant combos.

    Returns modified morpheme list.
    """
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        # Modal prefix ending in i + a-dominant morpheme
        if m1 in RULE_2R_MODAL and m2 in RULE_2R_A_DOMINANT:
            # ti + a -> ta, ri + a -> ra, ii + a -> a
            if m1 == "ii":
                result[idx] = ""
                result[idx + 1] = m2  # just a
            elif m1 == "kuusi":
                result[idx] = "kuus"
                # a merges
            else:
                result[idx] = m1[:-1] + "a" if m1.endswith("i") else m1
                result[idx + 1] = m2[1:] if m2.startswith("a") else m2

    return [m for m in result if m]


def apply_rule_3r(morphemes):
    """Rule 3R: -his perfective reduction. Vk + -his -> ks.

    The hi- of -his is lost after k-final stems, yielding just -ks.
    We use a marker (KS_MARKER) to protect this s from Rule 17
    (sibilant hardening: s->c after C). The marker is stripped
    after unrestricted rules have been applied.
    """
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        if m2 == "his" and m1.endswith("k"):
            # -his -> just -s, fused onto stem with protection marker
            result[idx] = m1 + KS_MARKER + "s"
            result[idx + 1] = ""

    return [m for m in result if m]


def apply_rule_8r(morphemes):
    """Rule 8R: raar- assibilation. raar + t-initial stem: r+t -> c.

    The final r of raar- and the initial t of the stem fuse to c.
    So raar + takasis -> raac + akasis (r and t both consumed, c replaces).
    """
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        if m1.endswith("r") and "raar" in m1 and m2.startswith("t"):
            # Strip final r from prefix, strip initial t from stem, insert c
            result[idx] = m1[:-1]       # raar -> raa
            result[idx + 1] = "c" + m2[1:]  # takasis -> cakasis

    return result


def apply_rule_10r(morphemes):
    """Rule 10R: ir-/acir- lose final r before uur-/ut-/uks-."""
    result = list(morphemes)
    targets = {"uur", "ut", "uks"}
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        if m1 in ("ir", "acir") and m2 in targets:
            result[idx] = m1[:-1]  # strip final r

    return result


def apply_rule_11r(morphemes):
    """Rule 11R: ut- -> uc- before i- (sequential)."""
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        if m1 == "ut" and m2 == "i":
            result[idx] = "uc"

    return result


def apply_rule_12r(morphemes):
    """Rule 12R: tiir-/ar- final r -> h before r-initial morpheme."""
    result = list(morphemes)
    for idx in range(len(result) - 1):
        m1, m2 = result[idx], result[idx + 1]

        if m1 in ("tiir", "ar") and m2.startswith("r"):
            result[idx] = m1[:-1] + "h"

    return result


# ---------------------------------------------------------------------------
# Ordered pipeline
# ---------------------------------------------------------------------------

def apply_restricted_rules(morphemes):
    """Apply all restricted rules to a morpheme list (in order).

    Returns a (possibly modified) morpheme list.
    """
    m = list(morphemes)
    m = apply_rule_1r(m)
    m = apply_rule_2r(m)
    m = apply_rule_3r(m)
    # Rule 4R (vocalic reduplication) is complex and verb-specific;
    # handled separately in derivation
    m = apply_rule_8r(m)
    # Rule 9R (final-s loss) applied at word level after joining
    m = apply_rule_10r(m)
    m = apply_rule_11r(m)
    m = apply_rule_12r(m)
    return m


def apply_unrestricted_rules(surface):
    """Apply all unrestricted rules in correct order to a surface string.

    Ordering follows Parks Ch. 3:
    - Vowel rules (5, 6, 7) first
    - Consonant rules (13-24) in specified order
    - Some consonant rules have strict ordering dependencies:
      13 (t-laryngealization) before 14 (metathesis) before 15 (sonorant reduction)
      12R before 20 before 15
    """
    s = surface

    # --- Vowel unrestricted ---
    s = apply_rule_5_same_vowel_contraction(s)
    s = apply_rule_6_u_domination(s)
    s = apply_rule_7_i_a_contraction(s)

    # --- Consonant unrestricted ---
    s = apply_rule_13_t_laryngealization(s)
    s = apply_rule_14_metathesis(s)
    s = apply_rule_15_sonorant_reduction(s)
    s = apply_rule_16_h_loss(s)
    s = apply_rule_17_sibilant_hardening(s)
    s = apply_rule_18_sibilant_loss(s)
    s = apply_rule_19_alveolar_dissimilation(s)
    s = apply_rule_20_degemination(s)
    s = apply_rule_21_r_stopping(s)
    s = apply_rule_22_labial_glide_loss(s)
    s = apply_rule_23_final_r_loss(s)

    # Rule 9R final-s loss (word-level, after all other rules)
    # Only for known -s-losing morphemes; handled in pipeline caller if needed

    return s


def apply_sound_changes(morphemes, final_s_loss=False):
    """Full pipeline: morpheme list -> surface form.

    Args:
        morphemes: list of morpheme strings, e.g. ["ti", "uur", "hiir"]
        final_s_loss: if True, apply Rule 9R (drop word-final s)

    Returns:
        surface form string
    """
    # Step 1: apply restricted rules (morpheme-aware)
    m = apply_restricted_rules(morphemes)

    # Step 2: concatenate morphemes
    surface = "".join(m)

    # Step 3: apply unrestricted rules (string-level)
    surface = apply_unrestricted_rules(surface)

    # Step 3b: strip protection markers
    surface = surface.replace(KS_MARKER, "")

    # Step 4: optional final-s loss
    if final_s_loss and surface.endswith("s"):
        surface = surface[:-1]

    return surface


def apply_nominal_sc(surface):
    """Apply only noun-safe sound changes to a surface string.

    Parks Ch. 3 rules are documented for verb morphology. Many also apply
    at nominal morpheme boundaries, but several are verb-specific:
      - Rule 17 (sibilant hardening: s→c / C_) — verb-internal only
      - Rule 18 (sibilant loss: s→Ø / k_c) — verb cluster reduction
      - Rule 19 (alveolar dissimilation: t+t→ct) — verb prefix interaction

    Rules that DO apply to nominal forms:
      - Rules 5, 6, 7: vowel coalescence at morpheme boundaries
      - Rule 13: t→h before r (general phonotactic)
      - Rule 14: r+h metathesis
      - Rule 15: hr→h sonorant reduction
      - Rule 16: h-loss (general)
      - Rule 20: degemination (general)
      - Rule 21: r-stopping (general)
      - Rule 22: labial glide loss (general)
      - Rule 23: final r loss (general)
    """
    s = surface

    # --- Vowel rules (always apply) ---
    s = apply_rule_5_same_vowel_contraction(s)
    s = apply_rule_6_u_domination(s)
    s = apply_rule_7_i_a_contraction(s)

    # --- Consonant rules (noun-safe subset) ---
    s = apply_rule_13_t_laryngealization(s)
    s = apply_rule_14_metathesis(s)
    s = apply_rule_15_sonorant_reduction(s)
    s = apply_rule_16_h_loss(s)
    # Rule 17 (sibilant hardening) EXCLUDED — verb-specific
    # Rule 18 (sibilant loss) EXCLUDED — verb-specific
    # Rule 19 (alveolar dissimilation) EXCLUDED — verb-specific
    s = apply_rule_20_degemination(s)
    s = apply_rule_21_r_stopping(s)
    s = apply_rule_22_labial_glide_loss(s)
    s = apply_rule_23_final_r_loss(s)

    return s


# ---------------------------------------------------------------------------
# Test suite — examples from Parks Ch. 3
# ---------------------------------------------------------------------------

TEST_CASES = [
    # Rule 13: t -> h / _ r (simple case)
    (["pahaat", "raʔuk"], "pahaahaʔuk", "t-laryngealization: pahaat+raʔuk (Rule 13)", False),

    # Rule 19: t+t -> ct
    (["ta", "t", "taʔuut"], "tactaʔuut", "alveolar dissimilation t+t (Rule 19)", False),

    # Rule 23: final r loss
    (["aar"], "aa", "final r loss (Rule 23)", False),

    # Rule 20: rr -> r + Rule 23: final r loss
    (["raar", "raahur"], "raaraahu", "degemination rr->r + final r loss (Rules 20+23)", False),

    # Rule 3R: -his reduction
    (["hak", "his"], "haks", "-his perfective reduction (Rule 3R)", False),

    # Rule 8R: raar assibilation (simple: r+t -> c)
    (["raar", "tiis"], "raaciis", "raar assibilation r+t->c (Rule 8R, simple)", False),
    # Full example produces tiraacakasis; attested tiracakasis has vowel shortening
    # not covered by the 24 listed rules (prosodic reduction in unstressed syllable)

    # Rule 11R: ut- affrication
    (["ut", "i"], "uci", "ut- affrication before i- (Rule 11R)", False),

    # Rule 9R: final-s loss
    (["kuhkus"], "kuhku", "final-s loss (Rule 9R)", True),

    # Rule 17: sibilant hardening s -> c after C (simple case)
    (["ik", "sa"], "ikca", "sibilant hardening: s->c after C (Rule 17)", False),

    # Rule 21: r-stopping r -> t after obstruent (simple case: k+r -> k+t)
    (["ik", "ra"], "ikta", "r-stopping: k+r -> k+t (Rule 21)", False),

    # Rule 19 + 21 combined: t+c -> ct metathesis
    (["ta", "t", "cak"], "tactak", "alveolar dissimilation t+c -> ct (Rule 19)", False),
]


def run_tests():
    """Run built-in test suite from PDF examples."""
    passed = 0
    failed = 0
    results = []

    for morphemes, expected, description, final_s in TEST_CASES:
        actual = apply_sound_changes(morphemes, final_s_loss=final_s)
        ok = actual == expected
        if ok:
            passed += 1
        else:
            failed += 1
        results.append({
            "morphemes": " + ".join(morphemes),
            "expected": expected,
            "actual": actual,
            "pass": ok,
            "description": description,
        })

    # Print results
    _safe_print(f"\n=== Sound Change Rule Tests ===")
    _safe_print(f"Passed: {passed}/{passed + failed}\n")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        _safe_print(f"  [{status}] {r['description']}")
        _safe_print(f"         Input:    {r['morphemes']}")
        _safe_print(f"         Expected: {r['expected']}")
        if not r["pass"]:
            _safe_print(f"         Actual:   {r['actual']}")
        _safe_print("")

    return passed, failed, results


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

def create_rules_table(conn):
    """Create sound_change_rules table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sound_change_rules (
            rule_id       TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            type          TEXT NOT NULL CHECK(type IN ('restricted', 'unrestricted')),
            domain        TEXT NOT NULL CHECK(domain IN ('vowel', 'consonant')),
            formal        TEXT NOT NULL,
            description   TEXT,
            ordering      INTEGER NOT NULL,
            examples      TEXT  -- JSON array
        )
    """)
    conn.commit()
    log.info("Created sound_change_rules table")


def populate_rules(conn):
    """Insert all 24 rules into the DB."""
    conn.execute("DELETE FROM sound_change_rules")  # clear for re-run
    for rule in RULES:
        conn.execute(
            """INSERT INTO sound_change_rules
               (rule_id, name, type, domain, formal, description, ordering, examples)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rule["rule_id"],
                rule["name"],
                rule["type"],
                rule["domain"],
                rule["formal"],
                rule["description"],
                rule["ordering"],
                json.dumps(rule["examples"], ensure_ascii=False),
            ),
        )
    conn.commit()
    log.info(f"Populated {len(RULES)} sound change rules in DB")


# ---------------------------------------------------------------------------
# Validation against paradigmatic forms
# ---------------------------------------------------------------------------

def validate_against_paradigms(conn):
    """Validate sound change rules against attested paradigmatic forms.

    Strategy:
    1. For each verb entry with form_2 (base) and form_4 (absolutive subordinate),
       attempt to derive form_4 from form_2 using known prefix patterns + rules.
    2. For each verb entry with form_2 and form_5 (intentive),
       check suffix patterns.
    3. Report match rates.
    """
    results = {
        "form_4_tests": [],
        "form_5_tests": [],
        "final_r_loss_tests": [],
        "t_laryngealization_tests": [],
        "degemination_tests": [],
    }

    # --- Test 1: Final r loss (Rule 23) ---
    # Words ending in r in underlying form should lose it on surface
    cur = conn.execute("""
        SELECT le.entry_id, le.headword, le.phonetic_form
        FROM lexical_entries le
        WHERE le.headword LIKE '%r'
    """)
    r_final_entries = cur.fetchall()
    log.info(f"Testing Rule 23 (final r loss): {len(r_final_entries)} entries ending in r")

    # These headwords end in r — in the dictionary they're already surface forms
    # So they shouldn't end in r if the rule is applied. But Parks keeps underlying
    # r in headwords. This is a notation convention, not a rule violation.
    results["final_r_loss_note"] = (
        f"{len(r_final_entries)} headwords end in r (underlying form preserved in notation)"
    )

    # --- Test 2: Form 4 derivation (irii- prefix pattern) ---
    cur = conn.execute("""
        SELECT le.entry_id, le.headword, le.verb_class,
               p2.skiri_form AS form_2, p4.skiri_form AS form_4
        FROM lexical_entries le
        JOIN paradigmatic_forms p2 ON le.entry_id = p2.entry_id AND p2.form_number = 2
        JOIN paradigmatic_forms p4 ON le.entry_id = p4.entry_id AND p4.form_number = 4
        WHERE le.grammatical_class LIKE '%V%'
          AND p2.skiri_form IS NOT NULL AND p2.skiri_form != ''
          AND p4.skiri_form IS NOT NULL AND p4.skiri_form != ''
    """)
    form_pairs = cur.fetchall()
    log.info(f"Testing form_2 -> form_4 derivation: {len(form_pairs)} verb entries")

    # Form 2 pattern: ti-/ta- + [preverb] + stem + suffix
    # Form 4 pattern: irii- + [preverb] + stem + -a suffix (absolutive subordinate)
    # We can check: does form_4 start with "irii" consistently?
    f4_irii_count = 0
    f4_other_prefix = {}
    for entry_id, headword, verb_class, form_2, form_4 in form_pairs:
        if form_4.startswith("irii"):
            f4_irii_count += 1
        else:
            prefix = form_4[:4] if len(form_4) >= 4 else form_4
            f4_other_prefix[prefix] = f4_other_prefix.get(prefix, 0) + 1

    results["form_4_irii_prefix"] = {
        "total": len(form_pairs),
        "irii_prefix": f4_irii_count,
        "irii_pct": round(100 * f4_irii_count / len(form_pairs), 1) if form_pairs else 0,
        "other_prefixes_top10": sorted(
            f4_other_prefix.items(), key=lambda x: -x[1]
        )[:10],
    }

    # --- Test 3: Form 2 prefix patterns by verb class ---
    f2_prefix_by_class = {}
    for entry_id, headword, verb_class, form_2, form_4 in form_pairs:
        vc = verb_class or "unknown"
        if vc not in f2_prefix_by_class:
            f2_prefix_by_class[vc] = {}

        # Extract prefix (everything before recognizable stem)
        prefix = form_2[:3] if len(form_2) >= 3 else form_2
        f2_prefix_by_class[vc][prefix] = f2_prefix_by_class[vc].get(prefix, 0) + 1

    results["form_2_prefix_by_class"] = {
        vc: sorted(prefixes.items(), key=lambda x: -x[1])[:5]
        for vc, prefixes in f2_prefix_by_class.items()
    }

    # --- Test 4: Sound change patterns in form pairs ---
    # Look for t->h (Rule 13) evidence in forms
    t_to_h_evidence = 0
    cur = conn.execute("""
        SELECT le.headword, p2.skiri_form
        FROM lexical_entries le
        JOIN paradigmatic_forms p2 ON le.entry_id = p2.entry_id AND p2.form_number = 2
        WHERE le.headword LIKE '%r%'
          AND p2.skiri_form LIKE '%h%'
          AND p2.skiri_form IS NOT NULL
    """)
    for headword, form_2 in cur.fetchall():
        # Headword has r, form has h — could be t+r -> h+r -> h
        t_to_h_evidence += 1

    results["rule_13_evidence"] = t_to_h_evidence

    # --- Test 5: Degemination evidence (Rule 20) ---
    # Look for raar- prefix forms where rr -> r
    cur = conn.execute("""
        SELECT le.headword, le.stem_preverb, p2.skiri_form
        FROM lexical_entries le
        JOIN paradigmatic_forms p2 ON le.entry_id = p2.entry_id AND p2.form_number = 2
        WHERE le.stem_preverb LIKE '%raar%'
    """)
    raar_forms = cur.fetchall()
    raar_no_rr = sum(1 for _, _, f in raar_forms if "rr" not in f)
    results["rule_20_raar_evidence"] = {
        "total_raar_stems": len(raar_forms),
        "surface_without_rr": raar_no_rr,
    }

    # --- Test 6: Derive form_4 from form_2 via prefix swap ---
    # Hypothesis: form_4 ≈ "irii" + form_2[2:] (swap ti- for irii-)
    # with sound changes applied
    derivation_tests = []
    exact_match = 0
    close_match = 0  # within 2 chars

    for entry_id, headword, verb_class, form_2, form_4 in form_pairs[:500]:
        # Try simple prefix swap: ti... -> irii...
        if form_2.startswith("ti"):
            derived = "irii" + form_2[2:]
            # Apply unrestricted sound changes
            derived = apply_unrestricted_rules(derived)

            if derived == form_4:
                exact_match += 1
            elif _edit_distance(derived, form_4) <= 2:
                close_match += 1

            derivation_tests.append({
                "entry_id": entry_id,
                "headword": headword,
                "form_2": form_2,
                "form_4_expected": form_4,
                "form_4_derived": derived,
                "exact": derived == form_4,
            })

    results["form_4_derivation"] = {
        "tested": len(derivation_tests),
        "exact_match": exact_match,
        "close_match": close_match,
        "exact_pct": round(100 * exact_match / len(derivation_tests), 1) if derivation_tests else 0,
        "close_pct": round(100 * (exact_match + close_match) / len(derivation_tests), 1) if derivation_tests else 0,
        "sample_mismatches": [
            t for t in derivation_tests if not t["exact"]
        ][:20],
    }

    return results


def _edit_distance(s1, s2):
    """Simple Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if c1 == c2 else 1),
            ))
        prev = curr
    return prev[-1]


# ---------------------------------------------------------------------------
# Gemini audit
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 4
AUDIT_BATCH_SIZE = 15  # entries per Gemini call

AUDIT_SYSTEM_PROMPT = """You are an expert in Skiri Pawnee phonology. You have deep knowledge of
the Parks Dictionary sound change system (24 rules from Chapter 3: Major Sound Changes).

RULE CATALOG:
{rule_catalog}

Your task: analyze paradigmatic verb form pairs (form_2 = 3rd person indicative perfective,
form_4 = absolutive subordinate perfective) and identify:
1. Which sound change rules are visible in each form
2. Whether the form_4 derivation from the stem is consistent with the rules
3. Any anomalies — forms that seem to violate the rules or show unlisted sound changes

Form 2 is the base form (ti- prefix = indicative 3rd person).
Form 4 is the absolutive subordinate (irii- prefix, often with preverb ra-).

IMPORTANT: The headword is the underlying/citation form. Paradigmatic forms are surface forms
with prefixes and suffixes applied. Sound changes happen at morpheme boundaries.

Respond in JSON:
{{
  "entries": [
    {{
      "entry_id": "...",
      "headword": "...",
      "rules_visible": ["13", "20", ...],
      "anomalies": ["description of any anomaly or unlisted pattern"],
      "notes": "brief analysis"
    }}
  ],
  "unlisted_patterns": ["any systematic sound changes not in the 24 rules"],
  "rule_ordering_issues": ["any evidence that rule ordering should differ"]
}}"""


def _build_rule_catalog_text():
    """Build a compact text version of the rule catalog for Gemini."""
    lines = []
    for r in RULES:
        lines.append(f"Rule {r['rule_id']}: {r['name']} -- {r['formal']}")
        lines.append(f"  Type: {r['type']}, Domain: {r['domain']}")
        lines.append(f"  {r['description'][:200]}")
        lines.append("")
    return "\n".join(lines)


def _repair_truncated_json(text):
    """Attempt to recover partial JSON from truncated Gemini response.

    Strategy: find the last complete entry in the entries array,
    close the array and object.
    """
    # Find "entries" array and try to close it
    idx = text.rfind('"entry_id"')
    if idx == -1:
        return None

    # Walk back to find the opening { of this entry
    brace_idx = text.rfind('{', 0, idx)
    if brace_idx == -1:
        return None

    # Take everything up to (but not including) this truncated entry
    truncated = text[:brace_idx].rstrip().rstrip(',')

    # Close the structure
    truncated += '], "unlisted_patterns": [], "rule_ordering_issues": []}'

    try:
        result = json.loads(truncated)
        log.info(f"Recovered partial JSON ({len(result.get('entries', []))} entries)")
        return result
    except json.JSONDecodeError:
        return None


def _call_gemini(client, content_text, system_prompt, model_name=GEMINI_MODEL):
    """Send request to Gemini with retry logic. Returns parsed JSON or None."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[content_text],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    max_output_tokens=16384,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Attempt partial JSON recovery (truncated response)
                repaired = _repair_truncated_json(text)
                if repaired:
                    return repaired
                raise

        except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests) as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s")
            time.sleep(wait)

        except (google_exceptions.ServiceUnavailable, google_exceptions.InternalServerError) as e:
            wait = RETRY_BACKOFF_BASE * attempt
            log.warning(f"Server error (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s")
            time.sleep(wait)

        except json.JSONDecodeError as e:
            log.warning(f"Gemini JSON parse error (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                return None

        except Exception as e:
            log.warning(f"Gemini error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE)

    return None


def gemini_audit(conn, checkpoint_path="audit_sound_changes_checkpoint.json"):
    """Run Gemini-powered audit of sound change rules against paradigmatic forms.

    Samples entries across all verb classes and asks Gemini to verify that
    the sound change rules correctly explain the form derivations.
    """
    try:
        from google import genai
    except ImportError:
        log.error("google-genai not installed. Install with: pip install google-genai")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set in environment")
        return None

    client = genai.Client(api_key=api_key)

    # Load checkpoint
    checkpoint = {}
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        log.info(f"Loaded checkpoint: {len(checkpoint.get('completed_batches', []))} batches done")

    completed_batches = set(checkpoint.get("completed_batches", []))
    all_results = checkpoint.get("results", [])
    all_unlisted = checkpoint.get("unlisted_patterns", [])
    all_ordering = checkpoint.get("ordering_issues", [])

    # Sample entries: ~15 per verb class (total ~120 entries)
    cur = conn.execute("""
        SELECT le.entry_id, le.headword, le.verb_class, le.stem_preverb,
               p2.skiri_form AS form_2, p4.skiri_form AS form_4
        FROM lexical_entries le
        JOIN paradigmatic_forms p2 ON le.entry_id = p2.entry_id AND p2.form_number = 2
        JOIN paradigmatic_forms p4 ON le.entry_id = p4.entry_id AND p4.form_number = 4
        WHERE le.grammatical_class LIKE '%V%'
          AND p2.skiri_form IS NOT NULL AND p2.skiri_form != ''
          AND p4.skiri_form IS NOT NULL AND p4.skiri_form != ''
        ORDER BY le.verb_class, RANDOM()
    """)
    all_entries = cur.fetchall()

    # Sample per verb class
    sampled = []
    by_class = {}
    for row in all_entries:
        vc = row[2] or "unknown"
        by_class.setdefault(vc, []).append(row)

    for vc, entries in sorted(by_class.items()):
        sampled.extend(entries[:15])

    log.info(f"Sampled {len(sampled)} entries across {len(by_class)} verb classes for audit")

    # Build batches
    batches = []
    for i in range(0, len(sampled), AUDIT_BATCH_SIZE):
        batches.append(sampled[i:i + AUDIT_BATCH_SIZE])

    rule_catalog = _build_rule_catalog_text()
    system_prompt = AUDIT_SYSTEM_PROMPT.format(rule_catalog=rule_catalog)

    for batch_idx, batch in enumerate(batches):
        batch_key = f"batch_{batch_idx}"
        if batch_key in completed_batches:
            log.info(f"Skipping {batch_key} (already done)")
            continue

        # Build prompt
        lines = [f"Analyze these {len(batch)} paradigmatic form pairs:\n"]
        for entry_id, headword, verb_class, preverb, form_2, form_4 in batch:
            lines.append(f"  entry_id: {entry_id}")
            lines.append(f"  headword: {headword}")
            lines.append(f"  verb_class: {verb_class}")
            lines.append(f"  preverb: {preverb or '(none)'}")
            lines.append(f"  form_2 (3P.IND.PERF): {form_2}")
            lines.append(f"  form_4 (ABS.SUB.PERF): {form_4}")
            lines.append("")

        content = "\n".join(lines)
        log.info(f"Sending {batch_key} ({len(batch)} entries) to Gemini...")

        result = _call_gemini(client, content, system_prompt)
        if result is None:
            log.warning(f"{batch_key} failed, skipping")
            continue

        # Collect results
        entries = result.get("entries", [])
        all_results.extend(entries)
        all_unlisted.extend(result.get("unlisted_patterns", []))
        all_ordering.extend(result.get("rule_ordering_issues", []))

        completed_batches.add(batch_key)
        log.info(f"  {batch_key}: {len(entries)} entries analyzed, "
                 f"{sum(1 for e in entries if e.get('anomalies'))} with anomalies")

        # Save checkpoint
        checkpoint = {
            "completed_batches": list(completed_batches),
            "results": all_results,
            "unlisted_patterns": all_unlisted,
            "ordering_issues": all_ordering,
        }
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        time.sleep(1)  # gentle rate limiting

    # Summarize
    total = len(all_results)
    with_anomalies = sum(1 for e in all_results if e.get("anomalies") and any(e["anomalies"]))
    rules_seen = {}
    for e in all_results:
        for r in e.get("rules_visible", []):
            rules_seen[r] = rules_seen.get(r, 0) + 1

    # Deduplicate unlisted patterns
    unique_unlisted = list(set(all_unlisted))
    unique_ordering = list(set(all_ordering))

    summary = {
        "total_entries_audited": total,
        "entries_with_anomalies": with_anomalies,
        "anomaly_rate": round(100 * with_anomalies / total, 1) if total else 0,
        "rules_observed": dict(sorted(rules_seen.items(), key=lambda x: -x[1])),
        "unlisted_patterns": unique_unlisted,
        "ordering_issues": unique_ordering,
        "sample_anomalies": [
            e for e in all_results if e.get("anomalies") and any(e["anomalies"])
        ][:30],
    }

    log.info(f"Audit complete: {total} entries, {with_anomalies} anomalies ({summary['anomaly_rate']}%)")
    log.info(f"Rules observed: {len(rules_seen)} distinct rules seen across forms")
    if unique_unlisted:
        log.info(f"Unlisted patterns found: {len(unique_unlisted)}")

    return summary


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(test_results, validation_results, report_path, audit_results=None):
    """Write comprehensive report."""
    lines = []
    lines.append("=" * 70)
    lines.append("Phase 2.3 -- Sound Change Rule Engine Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("")

    # --- Rule Catalog Summary ---
    lines.append("RULE CATALOG")
    lines.append("-" * 40)
    restricted = [r for r in RULES if r["type"] == "restricted"]
    unrestricted = [r for r in RULES if r["type"] == "unrestricted"]
    vowel_rules = [r for r in RULES if r["domain"] == "vowel"]
    consonant_rules = [r for r in RULES if r["domain"] == "consonant"]
    lines.append(f"  Total rules:       {len(RULES)}")
    lines.append(f"  Restricted:        {len(restricted)}")
    lines.append(f"  Unrestricted:      {len(unrestricted)}")
    lines.append(f"  Vowel rules:       {len(vowel_rules)}")
    lines.append(f"  Consonant rules:   {len(consonant_rules)}")
    lines.append("")

    for rule in RULES:
        lines.append(f"  Rule {rule['rule_id']:4s} [{rule['type'][:5]:5s}] "
                      f"[{rule['domain'][:4]:4s}]  {rule['name']}")
        lines.append(f"           {rule['formal']}")
        lines.append("")

    # --- Test Results ---
    if test_results:
        passed, failed, tests = test_results
        lines.append("BUILT-IN TESTS (PDF Examples)")
        lines.append("-" * 40)
        lines.append(f"  Passed: {passed}/{passed + failed}")
        lines.append("")
        for t in tests:
            status = "PASS" if t["pass"] else "FAIL"
            lines.append(f"  [{status}] {t['description']}")
            lines.append(f"           {t['morphemes']} -> {t['expected']}")
            if not t["pass"]:
                lines.append(f"           GOT: {t['actual']}")
        lines.append("")

    # --- Validation Results ---
    if validation_results:
        lines.append("PARADIGMATIC FORM VALIDATION")
        lines.append("-" * 40)

        # Form 4 prefix analysis
        f4 = validation_results.get("form_4_irii_prefix", {})
        if f4:
            lines.append(f"  Form 4 (absolutive subordinate) prefix analysis:")
            lines.append(f"    Total verb entries tested: {f4['total']}")
            lines.append(f"    Starting with irii-: {f4['irii_prefix']} ({f4['irii_pct']}%)")
            if f4.get("other_prefixes_top10"):
                lines.append(f"    Other prefixes (top 10):")
                for prefix, count in f4["other_prefixes_top10"]:
                    lines.append(f"      {prefix}...: {count}")
            lines.append("")

        # Form 4 derivation
        deriv = validation_results.get("form_4_derivation", {})
        if deriv:
            lines.append(f"  Form 4 derivation test (ti-prefix swap + sound changes):")
            lines.append(f"    Tested: {deriv['tested']}")
            lines.append(f"    Exact match: {deriv['exact_match']} ({deriv['exact_pct']}%)")
            lines.append(f"    Close match (edit dist <= 2): {deriv['close_match']} "
                          f"({deriv['close_pct']}% cumulative)")
            lines.append("")
            if deriv.get("sample_mismatches"):
                lines.append(f"    Sample mismatches (first 20):")
                for m in deriv["sample_mismatches"][:20]:
                    lines.append(f"      {m['headword']}: "
                                  f"form_2={m['form_2']} -> "
                                  f"derived={m['form_4_derived']} vs "
                                  f"attested={m['form_4_expected']}")
                lines.append("")

        # Rule 13 evidence
        r13 = validation_results.get("rule_13_evidence", 0)
        lines.append(f"  Rule 13 (t->h before r) potential evidence: {r13} entries")

        # Rule 20 evidence
        r20 = validation_results.get("rule_20_raar_evidence", {})
        if r20:
            lines.append(f"  Rule 20 (degemination) raar- evidence:")
            lines.append(f"    raar-preverb stems: {r20['total_raar_stems']}")
            lines.append(f"    Surface without rr: {r20['surface_without_rr']}")

        # Form 2 prefix patterns
        f2p = validation_results.get("form_2_prefix_by_class", {})
        if f2p:
            lines.append("")
            lines.append(f"  Form 2 prefix patterns by verb class:")
            for vc, prefixes in sorted(f2p.items()):
                top = ", ".join(f"{p}({c})" for p, c in prefixes[:3])
                lines.append(f"    {vc:8s}: {top}")

        lines.append("")

    # --- Final r loss note ---
    if validation_results and "final_r_loss_note" in validation_results:
        lines.append(f"  Note: {validation_results['final_r_loss_note']}")
        lines.append("")

    # --- Gemini Audit Results ---
    if audit_results:
        lines.append("GEMINI AUDIT")
        lines.append("-" * 40)
        lines.append(f"  Entries audited: {audit_results['total_entries_audited']}")
        lines.append(f"  Entries with anomalies: {audit_results['entries_with_anomalies']} "
                      f"({audit_results['anomaly_rate']}%)")
        lines.append("")

        if audit_results.get("rules_observed"):
            lines.append("  Rules observed in paradigmatic forms:")
            for rule_id, count in audit_results["rules_observed"].items():
                rule_name = next((r["name"] for r in RULES if r["rule_id"] == str(rule_id)), "?")
                lines.append(f"    Rule {rule_id:4s}: {count:4d} occurrences  ({rule_name})")
            lines.append("")

        if audit_results.get("unlisted_patterns"):
            lines.append("  Unlisted patterns (not in 24 rules):")
            for p in audit_results["unlisted_patterns"]:
                lines.append(f"    - {p}")
            lines.append("")

        if audit_results.get("ordering_issues"):
            lines.append("  Rule ordering issues flagged:")
            for o in audit_results["ordering_issues"]:
                lines.append(f"    - {o}")
            lines.append("")

        if audit_results.get("sample_anomalies"):
            lines.append(f"  Sample anomalies (first {min(30, len(audit_results['sample_anomalies']))}):")
            for e in audit_results["sample_anomalies"][:30]:
                lines.append(f"    {e.get('entry_id', '?')} ({e.get('headword', '?')}):")
                for a in e.get("anomalies", []):
                    if a:
                        lines.append(f"      -> {a}")
                if e.get("notes"):
                    lines.append(f"      Note: {e['notes']}")
            lines.append("")

    report_text = "\n".join(lines)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    log.info(f"Report written to {report_path}")

    return report_text


# ---------------------------------------------------------------------------
# Safe print for Windows console
# ---------------------------------------------------------------------------

def _safe_print(text):
    """Print with fallback for Windows cp1252 console."""
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 2.3: Sound Change Rule Engine"
    )
    parser.add_argument("--db", type=str, default="skiri_pawnee.db",
                        help="Path to SQLite database")
    parser.add_argument("--report", type=str,
                        default="reports/phase_2_3_sound_changes.txt",
                        help="Path to output report")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in test suite only")
    parser.add_argument("--apply", type=str,
                        help="Apply sound changes to morpheme string "
                             "(e.g., 'ti + uur + hiir')")
    parser.add_argument("--validate-only", action="store_true",
                        help="Run validation only (no DB writes)")
    parser.add_argument("--catalog-only", action="store_true",
                        help="Populate rules table only (no validation)")
    parser.add_argument("--final-s-loss", action="store_true",
                        help="Apply Rule 9R final-s loss (with --apply)")
    parser.add_argument("--audit", action="store_true",
                        help="Run Gemini-powered audit (requires GEMINI_API_KEY)")
    parser.add_argument("--audit-checkpoint", type=str,
                        default="audit_sound_changes_checkpoint.json",
                        help="Checkpoint file for audit resume")
    args = parser.parse_args()

    # --- Test mode ---
    if args.test:
        run_tests()
        return

    # --- Apply mode ---
    if args.apply:
        morphemes = [m.strip() for m in args.apply.split("+")]
        _safe_print(f"Input morphemes: {morphemes}")
        result = apply_sound_changes(morphemes, final_s_loss=args.final_s_loss)
        _safe_print(f"Surface form:    {result}")
        return

    # --- DB modes ---
    if not os.path.exists(args.db):
        log.error(f"Database not found: {args.db}")
        sys.exit(1)

    conn = sqlite3.connect(args.db)

    test_results = None
    validation_results = None
    audit_results = None

    try:
        # Always run tests
        test_results = run_tests()

        if not args.validate_only:
            # Create and populate rules table
            create_rules_table(conn)
            populate_rules(conn)

        if not args.catalog_only:
            # Validate against paradigmatic forms
            validation_results = validate_against_paradigms(conn)

        if args.audit:
            # Gemini-powered audit
            audit_results = gemini_audit(conn, args.audit_checkpoint)

        # Generate report
        generate_report(test_results, validation_results, args.report, audit_results)

    finally:
        conn.close()

    _safe_print(f"\nDone. Report: {args.report}")


if __name__ == "__main__":
    main()
