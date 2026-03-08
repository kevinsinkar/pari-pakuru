#!/usr/bin/env python3
"""
Test suite for Phase 1.1c and 1.1d scripts.
Validates respelling + normalization engines against known examples
from the project scope and source materials.

Run:  python scripts/test_phase_1_1.py
"""

import json
import sys
import os

# Add parent dir to path so we can import the scripts
sys.path.insert(0, os.path.dirname(__file__))

from respell_and_normalize import (
    parse_phonetic_form,
    tokenize_syllable,
    respell_syllable,
    generate_simplified_pronunciation,
    generate_normalized_form,
    extract_c_pattern_from_phonetic,
    process_entry,
)
from audit_entries import (
    validate_entry,
    AuditFlag,
)
from fix_priority_issues import (
    fix_phonetic_ocr,
    is_non_ipa_phonetic,
    fix_entry,
)


PASS = 0
FAIL = 0


def check(label, expected, actual):
    global PASS, FAIL
    if expected == actual:
        PASS += 1
        print(f"  ✓ {label}")
    else:
        FAIL += 1
        print(f"  ✗ {label}")
        print(f"    expected: {expected!r}")
        print(f"    actual:   {actual!r}")


# ===========================================================================
# Phase 1.1c — Respelling Engine Tests
# ===========================================================================

print("=" * 60)
print("PHASE 1.1c — Respelling Engine Tests")
print("=" * 60)

# --- Phonetic form parsing ---
print("\n--- Phonetic Form Parsing ---")

syls, err = parse_phonetic_form("[•paa-ʔə-tʊʔ•]")
check("Parse [•paa-ʔə-tʊʔ•]", ['paa', 'ʔə', 'tʊʔ'], syls)
check("No error", None, err)

syls, err = parse_phonetic_form("[•rə-hʊh-kaa-paa-kɪs•]")
check("Parse [•rə-hʊh-kaa-paa-kɪs•]", ['rə', 'hʊh', 'kaa', 'paa', 'kɪs'], syls)

syls, err = parse_phonetic_form("[–•ka•wii•ra•sii•ra•–]")
check("Parse [–•ka•wii•ra•sii•ra•–] (dot-separated)", ['ka', 'wii', 'ra', 'sii', 'ra'], syls)

syls, err = parse_phonetic_form("")
check("Empty string returns None", None, syls)
check("Empty string error", "empty_phonetic_form", err)

syls, err = parse_phonetic_form("[•čə-wii-rɪ{k/t}•]")
check("Parse with alternation marker", ['čə', 'wii', 'rɪ{k/t}'], syls)

# --- Syllable tokenization ---
print("\n--- Syllable Tokenization ---")

tokens = tokenize_syllable("paa")
check("Tokenize 'paa'", [('consonant', 'p', False), ('long_vowel', 'aa', False)], tokens)

tokens = tokenize_syllable("ʔə")
check("Tokenize 'ʔə'", [('consonant', 'ʔ', False), ('ipa_vowel', 'ə', False)], tokens)

tokens = tokenize_syllable("tʊʔ")
check("Tokenize 'tʊʔ'", [('consonant', 't', False), ('ipa_vowel', 'ʊ', False), ('consonant', 'ʔ', False)], tokens)

tokens = tokenize_syllable("kɪs")
check("Tokenize 'kɪs'", [('consonant', 'k', False), ('ipa_vowel', 'ɪ', False), ('consonant', 's', False)], tokens)

tokens = tokenize_syllable("hʊh")
check("Tokenize 'hʊh'", [('consonant', 'h', False), ('ipa_vowel', 'ʊ', False), ('consonant', 'h', False)], tokens)

# Accented syllable
tokens = tokenize_syllable("páa")
check("Tokenize 'páa' (accented long a)",
      [('consonant', 'p', False), ('long_vowel', 'aa', True)], tokens)

tokens = tokenize_syllable("kí")
check("Tokenize 'kí' (accented short i)",
      [('consonant', 'k', False), ('short_vowel', 'i', True)], tokens)

# --- Vowel mapping ---
print("\n--- Vowel Mapping (Parks + Blue Book) ---")

pron, _ = generate_simplified_pronunciation("[•a•]")
check("Short a → uh (Parks: 'putt', BB: 'above')", "uh", pron)

pron, _ = generate_simplified_pronunciation("[•aa•]")
check("Long aa → ah (Parks: 'father')", "ah", pron)

pron, _ = generate_simplified_pronunciation("[•i•]")
check("Short i → ih (Parks: 'pit')", "ih", pron)

pron, _ = generate_simplified_pronunciation("[•ii•]")
check("Long ii → ee (Parks: 'weed')", "ee", pron)

pron, _ = generate_simplified_pronunciation("[•u•]")
check("Short u → oo (BB: 'push')", "oo", pron)

pron, _ = generate_simplified_pronunciation("[•uu•]")
check("Long uu → oo (Parks: 'rude')", "oo", pron)

pron, _ = generate_simplified_pronunciation("[•ə•]")
check("Schwa ə → uh", "uh", pron)

pron, _ = generate_simplified_pronunciation("[•ɪ•]")
check("IPA ɪ → ih", "ih", pron)

pron, _ = generate_simplified_pronunciation("[•ʊ•]")
check("IPA ʊ → oo", "oo", pron)

# --- Consonant mapping ---
print("\n--- Consonant Mapping (Parks + Blue Book) ---")

pron, _ = generate_simplified_pronunciation("[•ra•]")
check("r → d (BB: 'a very soft d')", "duh", pron)

pron, _ = generate_simplified_pronunciation("[•ca•]")
check("c → ts (Parks: 'cents')", "tsuh", pron)

pron, _ = generate_simplified_pronunciation("[•ča•]")
check("č → ch (BB: 'ch in church')", "chuh", pron)

pron, _ = generate_simplified_pronunciation("[•ʔa•]")
check("ʔ → ' (glottal stop)", "'uh", pron)

pron, _ = generate_simplified_pronunciation("[•pa•]")
check("p passes through", "puh", pron)

pron, _ = generate_simplified_pronunciation("[•ta•]")
check("t passes through", "tuh", pron)

pron, _ = generate_simplified_pronunciation("[•ka•]")
check("k passes through", "kuh", pron)

pron, _ = generate_simplified_pronunciation("[•sa•]")
check("s passes through", "suh", pron)

pron, _ = generate_simplified_pronunciation("[•wa•]")
check("w passes through", "wuh", pron)

pron, _ = generate_simplified_pronunciation("[•ha•]")
check("h passes through", "huh", pron)

# --- Full examples from project scope ---
print("\n--- Full Examples (from Project Scope) ---")

pron, warnings = generate_simplified_pronunciation("[•paa-ʔə-tʊʔ•]")
check("paaʔatuʔ phonetic → pah-'uh-too'", "pah-'uh-too'", pron)

pron, warnings = generate_simplified_pronunciation("[•rə-hʊh-kaa-paa-kɪs•]")
check("rəhʊhkaapaaknɪs phonetic → duh-hooh-kah-pah-kihs", "duh-hooh-kah-pah-kihs", pron)

# --- Accent handling ---
print("\n--- Accent Handling ---")

pron, _ = generate_simplified_pronunciation("[•páa-ta•]")
check("Accented syllable is UPPERCASE", "PAH-tuh", pron)

pron, _ = generate_simplified_pronunciation("[•ka-ríi-ku•]")
check("Accent in middle syllable", "kuh-DEE-koo", pron)


# ===========================================================================
# Phase 1.1c — Normalization Engine Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Normalization Engine Tests")
print("=" * 60)

# --- Long vowel circumflex ---
print("\n--- Long Vowel → Circumflex ---")

norm, _ = generate_normalized_form("kawiirasiira", "[•ka-wii-ra-sii-ra•]")
check("kawiirasiira → kawîrasîra", "kawîrasîra", norm)

norm, _ = generate_normalized_form("paaʔatuʔ", "[•paa-ʔə-tʊʔ•]")
check("paaʔatuʔ → pâ'atu'", "pâ'atu'", norm)

norm, _ = generate_normalized_form("uukawikis", "[•uu-ka-wi-kis•]")
check("uukawikis → ûkawikis", "ûkawikis", norm)

# --- Glottal stop ---
print("\n--- Glottal Stop → Apostrophe ---")

norm, _ = generate_normalized_form("paaʔatuʔ", "[•paa-ʔə-tʊʔ•]")
check("ʔ → ' in paaʔatuʔ", "pâ'atu'", norm)

# --- c/č disambiguation ---
print("\n--- c/č Disambiguation ---")

c_pat = extract_c_pattern_from_phonetic("[•ka-ruu-ra-su-či-raa-'uu•]")
check("Extract c/č pattern from phonetic (1 č)", ['č'], c_pat)

c_pat = extract_c_pattern_from_phonetic("[•cí-kɪc•]")
check("Extract c/č pattern from phonetic (2 c's)", ['c', 'c'], c_pat)

c_pat = extract_c_pattern_from_phonetic("[•ča-wii-rɪc•]")
check("Extract c/č pattern (č then c)", ['č', 'c'], c_pat)

# Full normalization with č disambiguation
norm, _ = generate_normalized_form("karuurasuciraaʔuu", "[•ka-ruu-ra-su-či-raa-'uu•]")
check("karuurasuciraaʔuu → karûrasučirâ'û (c→č from phonetic)",
      "karûrasučirâ'û", norm)

norm, _ = generate_normalized_form("cikic", "[•cí-kɪc•]")
check("cikic stays cikic (both plain c in phonetic)", "cikic", norm)

# --- Missing phonetic form ---
print("\n--- Edge Cases ---")

norm, warnings = generate_normalized_form("kawiirasiira", "")
check("Missing phonetic: long vowels still convert", "kawîrasîra", norm)
# c stays as c because no phonetic to disambiguate — but no c in this word, so no issue

norm, warnings = generate_normalized_form("cikic", "")
check("Missing phonetic: c stays c (no disambiguation possible)", "cikic", norm)


# ===========================================================================
# Phase 1.1c — Full Entry Processing Test
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Full Entry Processing")
print("=" * 60)

test_entry = {
    "entry_id": "SK-paaqatuq-p100-1234",
    "headword": "paaʔatuʔ",
    "part_I": {
        "phonetic_form": "[•paa-ʔə-tʊʔ•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "blood."}],
    },
    "part_II": {"paradigmatic_forms": {}, "examples": []},
}

report = process_entry(test_entry)
check("Entry gets normalized_form", "pâ'atu'", test_entry.get('normalized_form'))
check("Entry gets simplified_pronunciation", "pah-'uh-too'",
      test_entry['part_I'].get('simplified_pronunciation'))


# ===========================================================================
# Phase 1.1c — Comma-Separated Variant Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Comma-Separated Variants")
print("=" * 60)

pron, _ = generate_simplified_pronunciation("[kaá-ʔə-sə-sʊʔ,kaá-sə-sʊʔ]")
check("Two variants joined with ' / '",
      True, ' / ' in (pron or ''))
check("First variant has accent",
      True, (pron or '').startswith('KAH'))

pron, _ = generate_simplified_pronunciation("[čaás,í-čaas]")
check("Two simple variants", True, ' / ' in (pron or ''))


# ===========================================================================
# Phase 1.1c — Preverb Notation Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Preverb Notation Stripping")
print("=" * 60)

pron, _ = generate_simplified_pronunciation("[ə-wə-kə•(ʊt...)]")
check("Preverb (ʊt...) stripped, syllables processed", "uh-wuh-kuh", pron)

pron, _ = generate_simplified_pronunciation("[i-ri-ka-ta•(ut...)]")
check("Preverb (ut...) stripped", "ih-dih-kuh-tuh", pron)


# ===========================================================================
# Phase 1.1c — Optional Sound Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Optional Sounds")
print("=" * 60)

pron, _ = generate_simplified_pronunciation("[•kaats-kə-wʊ(h)•]")
check("Optional (h) included in respelling", True, pron is not None)
check("Optional (h) produces 'h' in output", True, 'h' in (pron or '').lower())

pron, _ = generate_simplified_pronunciation("[•kaa-čət(k)•]")
check("Optional (k) included", True, pron is not None)


# ===========================================================================
# Phase 1.1c — IPA Length Mark Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — IPA Length Mark ː")
print("=" * 60)

# After fix_priority_issues, ÷ becomes ː
pron, _ = generate_simplified_pronunciation("[ə-rə-huː-sɪ-riʔ]")
check("ː treated as long vowel (huː → hoo)", True, 'hoo' in (pron or '').lower())

pron, _ = generate_simplified_pronunciation("[čɪ-ruː]")
check("ruː → doo", True, (pron or '').lower().endswith('doo'))


# ===========================================================================
# Phase 1.1c — Null Morpheme Ø Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Null Morpheme Ø")
print("=" * 60)

pron, _ = generate_simplified_pronunciation("[•pɪts•Ø]")
check("Ø stripped, rest processed", "pihts", pron)

pron, _ = generate_simplified_pronunciation("[•Ø•]")
check("Lone Ø produces None", None, pron)


# ===========================================================================
# Phase 1.1c — Prefix Notation Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Prefix Notation")
print("=" * 60)

pron, _ = generate_simplified_pronunciation("[+raar-][•taa-wə-tət(k)•]")
check("Prefix [+raar-] stripped", True, pron is not None)
check("Main form respelled", True, (pron or '').startswith('tah'))


# ===========================================================================
# Phase 1.1c — Null Phonetic Form in Entry
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1c — Null Phonetic Form Entry")
print("=" * 60)

null_pf_entry = {
    "entry_id": "SK-test-null-pf",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": None,
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
report = process_entry(null_pf_entry)
check("Null phonetic_form → pronunciation is None",
      None, null_pf_entry['part_I'].get('simplified_pronunciation'))
check("normalized_form still produced from headword",
      "test'", null_pf_entry.get('normalized_form'))


# ===========================================================================
# Phase 1.1d — Audit Engine Tests
# ===========================================================================

print("\n" + "=" * 60)
print("PHASE 1.1d — Audit Engine Tests")
print("=" * 60)

# --- Good entry (minimal flags) ---
print("\n--- Clean Entry ---")
good_entry = {
    "entry_id": "SK-test-p1-1",
    "headword": "paaʔatuʔ",
    "part_I": {
        "phonetic_form": "[•paa-ʔə-tʊʔ•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "blood."}],
    },
    "part_II": {"paradigmatic_forms": {}, "examples": []},
}
flags = validate_entry(good_entry)
flag_codes = [f.code for f in flags]
check("Clean noun entry has no errors",
      True, not any(f.severity == 'error' for f in flags))

# --- Empty headword ---
print("\n--- Missing Fields ---")
bad_entry = {
    "entry_id": "SK-bad-p1-1",
    "headword": "",
    "part_I": {
        "phonetic_form": "[•test•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(bad_entry)
flag_codes = [f.code for f in flags]
check("Empty headword flagged", True, 'EMPTY_HEADWORD' in flag_codes)

# --- Empty phonetic form ---
no_pf_entry = {
    "entry_id": "SK-nopf-p1-1",
    "headword": "test",
    "part_I": {
        "phonetic_form": "",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(no_pf_entry)
flag_codes = [f.code for f in flags]
check("Empty phonetic_form flagged", True, 'EMPTY_PHONETIC' in flag_codes)

# --- No glosses ---
no_gloss_entry = {
    "entry_id": "SK-nogloss-p1-1",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": "[•test•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [],
    },
    "part_II": {},
}
flags = validate_entry(no_gloss_entry)
flag_codes = [f.code for f in flags]
check("Empty glosses flagged as error", True, 'EMPTY_GLOSSES' in flag_codes)

# --- Invalid phonetic character ---
print("\n--- Phonetic Character Validation ---")
bad_pf_entry = {
    "entry_id": "SK-badpf-p1-1",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": "[•tə™-ka•]",  # ™ is an OCR artifact
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(bad_pf_entry)
flag_codes = [f.code for f in flags]
check("Invalid phonetic char (™) flagged", True, 'INVALID_PHONETIC_CHAR' in flag_codes)

# --- Noun missing glottal stop ---
print("\n--- Noun Glottal Stop Check ---")
noun_no_glottal = {
    "entry_id": "SK-noglottal-p1-1",
    "headword": "paatu",  # ends in vowel, no ʔ
    "part_I": {
        "phonetic_form": "[•paa-tu•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "blood."}],
    },
    "part_II": {},
}
flags = validate_entry(noun_no_glottal)
flag_codes = [f.code for f in flags]
check("Noun ending in vowel without ʔ flagged", True, 'NOUN_MISSING_GLOTTAL' in flag_codes)

# Noun ending in ʔ — should NOT be flagged
noun_with_glottal = {
    "entry_id": "SK-glottal-p1-1",
    "headword": "paatuʔ",
    "part_I": {
        "phonetic_form": "[•paa-tʊʔ•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "blood."}],
    },
    "part_II": {},
}
flags = validate_entry(noun_with_glottal)
flag_codes = [f.code for f in flags]
check("Noun ending in ʔ NOT flagged", True, 'NOUN_MISSING_GLOTTAL' not in flag_codes)

# --- Verb missing verb class ---
print("\n--- Verb Class Checks ---")
verb_no_class = {
    "entry_id": "SK-verb-p1-1",
    "headword": "kawiitʔ",
    "part_I": {
        "phonetic_form": "[•ka-wiit-ʔ•]",
        "grammatical_info": {"grammatical_class": "VI", "verb_class": None},
        "glosses": [{"number": 1, "definition": "to go."}],
    },
    "part_II": {"paradigmatic_forms": {}, "examples": []},
}
flags = validate_entry(verb_no_class)
flag_codes = [f.code for f in flags]
check("Verb without verb_class flagged (info)", True, 'MISSING_VERB_CLASS' in flag_codes)

# VD (descriptive verbs) should NOT be flagged — by design in Parks
vd_entry = {
    "entry_id": "SK-vd-test",
    "headword": "kaacʔ",
    "part_I": {
        "phonetic_form": "[•kaats•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "to be black."}],
    },
    "part_II": {},
}
flags = validate_entry(vd_entry)
flag_codes = [f.code for f in flags]
check("VD without verb_class NOT flagged (by design)", True, 'MISSING_VERB_CLASS' not in flag_codes)

# --- c ↔ ts skeleton normalization (false positive elimination) ---
print("\n--- c↔ts Skeleton Normalization ---")
c_ts_entry = {
    "entry_id": "SK-kaac-p2-0016",
    "headword": "kaac",
    "part_I": {
        "phonetic_form": "[•kaats•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "to be black."}],
    },
    "part_II": {},
}
flags = validate_entry(c_ts_entry)
flag_codes = [f.code for f in flags]
check("kaac/kaats: c↔ts NOT flagged as mismatch",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# Optional sound (h) — headword has it, phonetic has (h)
opt_h_entry = {
    "entry_id": "SK-awuh-test",
    "headword": "awuh",
    "part_I": {
        "phonetic_form": "[•ə-wʊ(h)•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(opt_h_entry)
flag_codes = [f.code for f in flags]
check("awuh/ə-wʊ(h): optional (h) NOT flagged",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# Alternation {k/t} — headword has k, phonetic has {k/t}
alt_entry = {
    "entry_id": "SK-ahak-test",
    "headword": "ahak",
    "part_I": {
        "phonetic_form": "[•ə-hə{k/t}•]",
        "grammatical_info": {"grammatical_class": "VI", "verb_class": "(4)"},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {"paradigmatic_forms": {"form_1": "test"}},
}
flags = validate_entry(alt_entry)
flag_codes = [f.code for f in flags]
check("ahak/ə-hə{k/t}: alternation NOT flagged",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# Optional (r) at end
opt_r_entry = {
    "entry_id": "SK-akiihaar-test",
    "headword": "akiihaar",
    "part_I": {
        "phonetic_form": "[•ə-kii-haa(r)•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(opt_r_entry)
flag_codes = [f.code for f in flags]
check("akiihaar/ə-kii-haa(r): optional (r) NOT flagged",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# Combined: optional (h) + {k/t}
combo_entry = {
    "entry_id": "SK-combo-test",
    "headword": "arikiihk",
    "part_I": {
        "phonetic_form": "[•ə-rɪ-kii(h){k/t}•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(combo_entry)
flag_codes = [f.code for f in flags]
check("arikiihk/ə-rɪ-kii(h){k/t}: combo NOT flagged",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# More complex c↔ts
c_ts_entry2 = {
    "entry_id": "SK-ackiriku-p8-0079",
    "headword": "ackiriku",
    "part_I": {
        "phonetic_form": "[•əts-kɪ-rɪ-kʊ•]",
        "grammatical_info": {"grammatical_class": "VD", "verb_class": None},
        "glosses": [{"number": 1, "definition": "to be dry."}],
    },
    "part_II": {},
}
flags = validate_entry(c_ts_entry2)
flag_codes = [f.code for f in flags]
check("ackiriku/əts-kɪ-rɪ-kʊ: c↔ts NOT flagged",
      True, 'CONSONANT_SKELETON_MISMATCH' not in flag_codes)

# Genuine mismatch should still be caught
bad_skel_entry = {
    "entry_id": "SK-bad-skel",
    "headword": "paakisʔ",
    "part_I": {
        "phonetic_form": "[•tuu-raa-wɪ•]",
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(bad_skel_entry)
flag_codes = [f.code for f in flags]
check("Genuine skeleton mismatch still caught",
      True, 'CONSONANT_SKELETON_MISMATCH' in flag_codes)

# --- Multi-class grammatical entries ---
print("\n--- Multi-Class Gram Validation ---")
multi_class_entry = {
    "entry_id": "SK-multi-p1-1",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": "[•test•]",
        "grammatical_info": {"grammatical_class": "VT, VR", "verb_class": "(1)"},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {"paradigmatic_forms": {"form_1": "test"}, "examples": []},
}
flags = validate_entry(multi_class_entry)
flag_codes = [f.code for f in flags]
check("'VT, VR' NOT flagged as unknown", True, 'UNKNOWN_GRAM_CLASS' not in flag_codes)

# N, ADV multi-class
multi2 = {
    "entry_id": "SK-multi2-p1-1",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": "[•test•]",
        "grammatical_info": {"grammatical_class": "N, ADV", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(multi2)
flag_codes = [f.code for f in flags]
check("'N, ADV' NOT flagged as unknown", True, 'UNKNOWN_GRAM_CLASS' not in flag_codes)

# ADV-P recognized
advp = {
    "entry_id": "SK-advp-p1-1",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": "[•test•]",
        "grammatical_info": {"grammatical_class": "ADV-P", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(advp)
flag_codes = [f.code for f in flags]
check("'ADV-P' NOT flagged as unknown", True, 'UNKNOWN_GRAM_CLASS' not in flag_codes)

# --- Null phonetic_form from fix script ---
print("\n--- Null Phonetic Form (post-fix) ---")
null_pf_audit = {
    "entry_id": "SK-null-pf",
    "headword": "testʔ",
    "part_I": {
        "phonetic_form": None,
        "grammatical_info": {"grammatical_class": "N", "verb_class": None},
        "glosses": [{"number": 1, "definition": "test."}],
    },
    "part_II": {},
}
flags = validate_entry(null_pf_audit)
flag_codes = [f.code for f in flags]
check("None phonetic_form flagged as EMPTY_PHONETIC", True, 'EMPTY_PHONETIC' in flag_codes)
check("None phonetic_form no crash", True, 'INVALID_PHONETIC_CHAR' not in flag_codes)


# ===========================================================================
# fix_priority_issues — OCR Fix Tests
# ===========================================================================

print("\n" + "=" * 60)
print("FIX PRIORITY ISSUES — OCR Corrections")
print("=" * 60)

# --- OCR character fixes ---
print("\n--- OCR Character Corrections ---")

result, changes = fix_phonetic_ocr("[ə-rə-hu÷-sɪ-riʔ]", "test")
check("÷ → ː", "[ə-rə-huː-sɪ-riʔ]", result)
check("One change logged", 1, len(changes))

result, changes = fix_phonetic_ocr("[à-kəh-wɪ-rɪ-wˆ-sɪ-sʊʔ]", "test")
check("ˆ → ɪ", "[à-kəh-wɪ-rɪ-wɪ-sɪ-sʊʔ]", result)

result, changes = fix_phonetic_ocr("[ɪ-rií-rə-sə-k‹-hə-kʊ]", "test")
check("‹ → ʊ", "[ɪ-rií-rə-sə-kʊ-hə-kʊ]", result)

result, changes = fix_phonetic_ocr("[tií-hii-rə-raÒh-kə-sə]", "test")
check("Ò → a", "[tií-hii-rə-raah-kə-sə]", result)

result, changes = fix_phonetic_ocr("[aá-čɪ-kɪ-čiç]", "test")
check("ç → ʔ", "[aá-čɪ-kɪ-čiʔ]", result)

result, changes = fix_phonetic_ocr("[•paa-ʔə-tʊʔ•]", "test")
check("Clean form unchanged", "[•paa-ʔə-tʊʔ•]", result)
check("No changes for clean form", 0, len(changes))

# --- Non-IPA detection ---
print("\n--- Non-IPA Phonetic Form Detection ---")

check("cross-referenceonly detected", True, is_non_ipa_phonetic("[cross-referenceonly]") is not None)
check("NOT_PROVIDED detected", True, is_non_ipa_phonetic("NOT_PROVIDED") is not None)
check("NOT_PROVIDED_IN_ENTRY detected", True, is_non_ipa_phonetic("NOT_PROVIDED_IN_ENTRY") is not None)
check("[notprovided] detected", True, is_non_ipa_phonetic("[notprovided]") is not None)
check("N/A detected", True, is_non_ipa_phonetic("N/A") is not None)
check("Seeentryfor detected", True, is_non_ipa_phonetic("Seeentryfor'bold'") is not None)
check("[cross-reference] detected", True, is_non_ipa_phonetic("[cross-reference]") is not None)
check("Real IPA not flagged", None, is_non_ipa_phonetic("[•paa-ʔə-tʊʔ•]"))

# --- Full entry fix ---
print("\n--- Full Entry Fix ---")

xref_entry = {
    "entry_id": "SK-xref-test",
    "headword": "test",
    "part_I": {
        "phonetic_form": "[cross-referenceonly]",
        "grammatical_info": {"grammatical_class": "N"},
        "glosses": [{"number": 1, "definition": "test"}],
    },
    "part_II": {},
}
changes = fix_entry(xref_entry)
check("Cross-ref phonetic_form nulled", None, xref_entry['part_I']['phonetic_form'])
check("One change logged", 1, len(changes))
check("Action is nulled_non_ipa", "nulled_non_ipa", changes[0]['action'])


# ===========================================================================
# Summary
# ===========================================================================

print("\n" + "=" * 60)
total = PASS + FAIL
if FAIL == 0:
    print(f"ALL {total} TESTS PASSED ✓")
else:
    print(f"{PASS}/{total} tests passed, {FAIL} FAILED ✗")
print("=" * 60)

sys.exit(1 if FAIL > 0 else 0)
