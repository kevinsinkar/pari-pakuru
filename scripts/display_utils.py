#!/usr/bin/env python3
"""Display utilities for Pari Pakuru flashcard/PDF export.

Shared between the web app and export scripts. Core function:
  display_headword(headword, normalized_form) -> (display_str, grammar_note)
"""

import re
from typing import Optional, Tuple


# ── Rule 1 helpers: bracket notation → human-readable notes ──────

_BRACKET_NOTES = {
    "+ neg.": "used with negative proclitic (kara-/ka-)",
    "+ raar-": "distributive \u2014 used with raar- prefix",
    "+ i-": "used with i- prefix",
    "+ ruu-": "used with ruu- preverb",
    "+ (ku-, ruu-, irii-), i-": "used with aspect proclitics + i- prefix",
}


def _bracket_to_note(bracket_content: str) -> str:
    """Map bracket notation content to a human-readable grammar note."""
    key = bracket_content.strip()
    if key in _BRACKET_NOTES:
        return _BRACKET_NOTES[key]
    # Normalize diacritics in bracket keys (normalized_form has aa->â etc.)
    for canon_key, note in _BRACKET_NOTES.items():
        if _strip_diacritics(key) == _strip_diacritics(canon_key):
            return note
    return f"requires: {key}"


def _strip_diacritics(s: str) -> str:
    """Rough normalization for bracket-key matching."""
    return (
        s.replace("\u00e2", "aa")
        .replace("\u00ee", "ii")
        .replace("\u00fb", "uu")
        .replace("\u010d", "c")
        .replace("\u2019", "'")
    )


# ── Rule 0 helper: preverb notation (ir...), (ut...) ────────────

_PREVERB_RE = re.compile(r"\s*\([a-z]{1,3}\.{3}\)\s*")
_NULL_ONSET_RE = re.compile(r"^Ø\s*")


# ── Main function ────────────────────────────────────────────────

def display_headword(
    headword: str, normalized_form: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """Clean a Parks Dictionary headword for learner-facing display.

    Returns (display_str, grammar_note) where grammar_note may be None.
    Uses normalized_form as base when available (has diacritics applied).

    Rules applied in order:
      0. Strip preverb notation: Ø prefix, (ir...), (ut...) mid-headword
      1. Extract [+ ...] bracket notation → grammar_note
      2. Take pre-slash form only (slash alternates)
      3. Strip (r) optional-onset paren
      4. Strip trailing suffix parens: (wi)-, (u)-, (a)-, (ta)-
      5. Strip leading and trailing dashes (bound morpheme markers)
    """
    base = normalized_form if normalized_form else headword
    grammar_note = None

    # Rule 0: Strip preverb notation (but preserve bare Ø as-is)
    if base.strip() != "Ø":
        base = _NULL_ONSET_RE.sub("", base)
    base = _PREVERB_RE.sub(" ", base)

    # Rule 1: Extract and strip bracket notation
    m = re.search(r"\s*\[([^\]]+)\]", base)
    if m:
        grammar_note = _bracket_to_note(m.group(1))
        base = re.sub(r"\s*\[[^\]]+\]", "", base)

    # Rule 2: Take pre-slash form only
    if "/" in base:
        base = base.split("/")[0]

    # Rule 3: Strip (r) optional-onset paren at start
    base = re.sub(r"^\(r\)", "", base)

    # Rule 4: Strip trailing suffix parens (may be followed by dash)
    base = re.sub(r"\s*\([^)]+\)\s*-?\s*$", "", base)

    # Rule 5: Strip leading and trailing dashes (per comma-part for alternants)
    if ", " in base:
        parts = [p.strip().strip("-").strip() for p in base.split(", ")]
        base = ", ".join(p for p in parts if p)
    else:
        base = base.strip("-").strip()

    return base, grammar_note


# ── Grammatical class labels and morphological notes ─────────────

GRAM_CLASS_LABELS = {
    "N": "noun",
    "N-KIN": "kinship term",
    "N-DEP": "dependent noun",
    "LOC": "locative",
    "ADV": "adverb",
    "ADV-P": "adverbial particle",
    "ADJ": "adjective",
    "CONJ": "conjunction",
    "DEM": "demonstrative",
    "EXCL": "exclamation",
    "INTER": "interrogative",
    "INTERJ": "interjection",
    "IRR. VI, VT": "irregular verb",
    "NUM": "numeral",
    "PART": "particle",
    "PRON": "pronoun",
    "QUAN": "quantifier",
    "VD": "descriptive verb",
    "VI": "intransitive verb",
    "VL": "locative verb",
    "VP": "patient verb",
    "VR": "reflexive verb",
    "VT": "transitive verb",
}

# Classes that get a back-of-card morphological note (bound morphemes)
MORPH_CLASS_NOTES = {
    "N-KIN": "Kinship term \u2014 form changes with possessor (my/your/his)",
    "N-DEP": "Dependent noun \u2014 requires possessive prefix",
    "LOC": "Locative directional \u2014 used as a verb prefix",
    "ADV-P": "Adverbial particle",
}


def gram_class_label(raw_class: str) -> str:
    """Return human-readable label for a grammatical class abbreviation."""
    if not raw_class:
        return ""
    # Handle compound classes like "VI, VT" or "VI(1), VT(1)"
    clean = re.sub(r"\(\d+\)", "", raw_class).strip()
    if clean in GRAM_CLASS_LABELS:
        return GRAM_CLASS_LABELS[clean]
    # Try first part of compound
    parts = [p.strip() for p in clean.split(",")]
    labels = []
    for p in parts:
        p = p.strip()
        if p in GRAM_CLASS_LABELS:
            labels.append(GRAM_CLASS_LABELS[p])
        else:
            labels.append(p)
    return ", ".join(labels)


def morph_class_note(raw_class: str) -> Optional[str]:
    """Return a morphological note for bound-morpheme classes, or None."""
    if not raw_class:
        return None
    clean = re.sub(r"\(\d+\)", "", raw_class).strip()
    return MORPH_CLASS_NOTES.get(clean)


# ── Surface-form modernization + respelling (Phase 3.2b sentence builder) ──
#
# For CONJUGATED verb forms there is no attested per-form phonetic, so the
# c/č split uses a context rule validated against all attested dictionary
# phonetics (2026-09-01): c is pronounced [č] before a vowel and [ts] before
# a consonant or word-finally — correct for 1,366/1,387 attested c-positions
# (98.5%; several of the misses are known low-fidelity duplicate-page
# phonetics). Long-vowel circumflexes and ʔ→' are exact.
#
# IPA is deliberately NOT generated here: Parks's IPA marks vowel reduction
# (ə/ɪ/ʊ) and pitch accent, neither of which is reliably predictable from
# the practical orthography. Only attested IPA (from lexical_entries) should
# ever be shown.

_ACCENTS = {"\u00e1": "a", "\u00ed": "i", "\u00fa": "u",
            "\u00e0": "a", "\u00ec": "i", "\u00f9": "u"}
_VOWELS = set("aiu")


def _apply_c_context(form: str, c_lower: str = "\u010d",
                     c_upper: str = "\u010c") -> str:
    """Replace c with č where the context rule says it is pronounced [č]."""
    chars = list(form)
    plain = "".join(_ACCENTS.get(ch, ch) for ch in form).lower()
    for i, ch in enumerate(chars):
        if ch in ("c", "C"):
            nxt = plain[i + 1] if i + 1 < len(plain) else ""
            if nxt in _VOWELS:
                chars[i] = c_upper if ch == "C" else c_lower
    return "".join(chars)


def modernize_form(form: str) -> str:
    """Practical-orthography surface form → learner orthography (â î û č ').

    Matches the dictionary's normalized_form convention. The č placement is
    rule-based (98.5% validated), not per-form attested — callers should
    label the output as derived when the form is not a dictionary headword.
    """
    if not form:
        return form
    s = _apply_c_context(form)
    for long_v, circ in (("aa", "\u00e2"), ("ii", "\u00ee"), ("uu", "\u00fb"),
                         ("AA", "\u00c2"), ("II", "\u00ce"), ("UU", "\u00db"),
                         ("Aa", "\u00c2"), ("Ii", "\u00ce"), ("Uu", "\u00db")):
        s = s.replace(long_v, circ)
    return s.replace("\u0294", "'")


def respell_form(form: str) -> str:
    """Practical-orthography surface form → approximate English respelling.

    Same vowel/consonant mapping as Phase 1.1c (a→uh, aa→ah, i→ih, ii→ee,
    u/uu→oo, r→d, ʔ→', c→ch/ts by the context rule). APPROXIMATE: derived
    from spelling, so it cannot mark stress or the reduced vowels that
    Parks's attested IPA records.
    """
    if not form:
        return form
    s = "".join(_ACCENTS.get(ch, ch) for ch in form.lower())
    s = _apply_c_context(s, c_lower="\u010d")
    out = []
    i = 0
    rules = [("aa", "ah"), ("ii", "ee"), ("uu", "oo"),
             ("\u010d", "ch"), ("\u0294", "'"),
             ("a", "uh"), ("i", "ih"), ("u", "oo"),
             ("r", "d"), ("c", "ts")]
    while i < len(s):
        matched = False
        for pat, rep in rules:
            if s.startswith(pat, i):
                out.append(rep)
                i += len(pat)
                matched = True
                break
        if not matched:
            out.append(s[i])
            i += 1
    return "".join(out)
