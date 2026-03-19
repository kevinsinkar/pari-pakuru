"""
Example Filter — Skiri-aware headword matching for Blue Book examples
=====================================================================

Skiri Pawnee is polysynthetic: morphemes fuse into long words, and
substring matching produces false positives. This module provides
functions to check whether an example sentence genuinely contains
a target headword (not just a string prefix of a different word).

Problem:
    headword "kiri" (cat) substring-matches:
        "Kirike ru'?"   ← FALSE: "kirike" = "what?" (different headword)
        "kirihkaatit"   ← TRUE:  "kiri" + h + kaatit = "black cat"

Solution:
    1. Find candidate match positions in the example text
    2. Extract the full "Skiri word" at each position
    3. Reject if that full word is a different known headword
    4. Accept if the headword sits at a word boundary or is the stem
       of a recognized compound

Usage:
    from example_filter import matches_headword, filter_examples

    # Single check
    matches_headword("kiri", "kirihkaatit", headword_set)  # True
    matches_headword("kiri", "Kirike ru'?", headword_set)  # False

    # Batch filter
    good = filter_examples("kiri", example_list, headword_set)

Integration:
    In your Flask route or Jinja template, call filter_examples()
    before rendering the examples list. The headword_set should be
    built once at app startup from your dictionary data.
"""

import re
from typing import Set, List, Optional, Dict, Any


# ─── Skiri word boundary characters ───────────────────────────────────────
# In Blue Book / Parks orthography:
#   • (interpunct)  = morpheme boundary WITHIN a word
#   - (hyphen)      = morpheme boundary WITHIN a word
#   space           = word boundary
#   ' or ʔ          = glottal stop (part of the word, not a boundary)
#   . at end        = sentence punctuation
#   ? at end        = question punctuation

_WORD_BOUNDARY_RE = re.compile(r'[\s,;:!?.]+')

# Characters that can follow a noun stem in a compound without a separator.
# In Skiri, when a noun incorporates into a verb or compound:
#   kiri + h + kaatit  →  kirihkaatit   (h is epenthetic before k)
#   paks + ku          →  paksku        (direct concatenation)
#   iks + ta           →  iksta         (direct concatenation)
# The "linking" consonants are h (before stops), and sometimes Ø.
_COMPOUND_LINK_CHARS = set("hrstpk•\u2022-")


def _normalize_for_match(s: str) -> str:
    """Lowercase and normalize glottal stop variants for matching."""
    result = (s.lower()
              .replace("ʔ", "'")
              .replace("\u2019", "'")   # right single quote
              .replace("\u2018", "'")   # left single quote
              .replace("č", "c")       # c-hacek → c for matching
              .replace("j", "e")       # OCR artifact: uppercase italic E → J
              )
    # OCR artifact: digit 1 inside a Skiri word is misread E
    # (Blue Book headers: "KIRIK1 RU'?" = "KIRIKE RU'?")
    # Only replace 1 when surrounded by letters (not standalone numbers)
    import re
    result = re.sub(r'(?<=[a-z])1(?=[a-z\s\'•\u2022?!.,;:\-]|$)', 'e', result)
    return result


def _extract_skiri_word(text: str, pos: int) -> str:
    """
    Extract the full Skiri 'word' starting at position `pos` in `text`.

    A Skiri word runs until we hit whitespace, comma, or end-of-string.
    Interpuncts (•) and hyphens are internal to words. Trailing
    punctuation ('?', '.', '!') is stripped.
    """
    i = pos
    n = len(text)
    while i < n and text[i] not in ' \t\n,;:!':
        # Allow ? only if not at end of word (could be sentence-final)
        if text[i] == '?' and (i + 1 >= n or text[i + 1] in ' \t\n'):
            break
        if text[i] == '.' and (i + 1 >= n or text[i + 1] in ' \t\n'):
            break
        i += 1
    word = text[pos:i]
    # Strip trailing punctuation
    word = word.rstrip("?.!,;:")
    return word


def _is_word_start(text: str, pos: int) -> bool:
    """Check if `pos` is at the start of a word (after space/start/punct)."""
    if pos == 0:
        return True
    prev = text[pos - 1]
    return prev in ' \t\n,;:!?.'


def matches_headword(
    headword: str,
    example_text: str,
    headword_set: Set[str],
    stem: Optional[str] = None,
) -> bool:
    """
    Check if `example_text` genuinely contains `headword` (not a different word).

    Args:
        headword:      The target headword (e.g., "kiri")
        example_text:  The Skiri example sentence
        headword_set:  Set of ALL known headwords (normalized), for disambiguation
        stem:          Optional pre-extracted stem (e.g., "kiri" from "kiriʔ")

    Returns:
        True if the example contains a genuine reference to the headword.
    """
    hw_norm = _normalize_for_match(headword)
    text_norm = _normalize_for_match(example_text)

    # Also check stem form if different from headword
    stems_to_check = {hw_norm}
    if stem:
        stems_to_check.add(_normalize_for_match(stem))

    for target in stems_to_check:
        if not target:
            continue

        # Find all positions where the target appears
        start = 0
        while True:
            pos = text_norm.find(target, start)
            if pos == -1:
                break
            start = pos + 1

            # Rule 1: Must be at a word start (not mid-word)
            if not _is_word_start(text_norm, pos):
                continue

            # Extract the full word at this position
            full_word_norm = _normalize_for_match(
                _extract_skiri_word(example_text, pos)
            )

            # Rule 2: Exact match → always accept
            if full_word_norm == target:
                return True

            # Rule 3: The full word is a DIFFERENT known headword → reject
            # Check the full word and progressively longer prefixes
            if _is_different_headword(target, full_word_norm, headword_set):
                continue

            # Rule 4: Target is at start of word, rest looks like a compound
            remainder = full_word_norm[len(target):]
            if remainder:
                # If remainder starts with morpheme boundary marker → compound ✓
                if remainder[0] in '•\u2022-':
                    return True
                # Epenthetic h before a stop consonant is a real compound linker
                # e.g., kiri + h + kaatit = kirihkaatit "black cat"
                # Require h + at least 2 more chars (a real morpheme, not noise)
                if remainder[0] == 'h' and len(remainder) >= 3:
                    return True
                # Otherwise: unknown continuation → likely a different word
                continue
            else:
                # Exact match already handled above
                return True

    return False


def _is_different_headword(
    target: str,
    full_word: str,
    headword_set: Set[str],
) -> bool:
    """
    Check if `full_word` is a known headword that is DIFFERENT from `target`.

    Handles the case where "kirike" is in the headword set but "kiri" is the
    target — the match on "kirike" should be rejected.

    But: "kiri•wusu'" is a compound OF "kiri" (target + morpheme boundary),
    so even though it might be a separate headword, it's still a valid match.

    Also scans prefixes: "kiriks•pahat" contains prefix "kiriks" which is
    a different headword (bead), so the match for "kiri" is rejected.
    """
    if full_word == target:
        return False  # same word, not different

    # If the full word is a compound containing target + morpheme boundary,
    # it's a compound OF the target, not a different word.
    remainder = full_word[len(target):]
    if remainder and remainder[0] in "•\u2022-":
        return False  # compound of the target → not "different"

    # Direct check on full word
    if full_word in headword_set:
        return True
    if (full_word + "'") in headword_set:
        return True
    if full_word.endswith("'") and full_word[:-1] in headword_set:
        return True

    # Prefix scan: check if any prefix LONGER than target is a known headword.
    # This catches cases like "kiriks•pahat" where "kiriks" (bead) is a
    # different headword than "kiri" (cat).
    # Scan up to the first morpheme boundary or the full word length.
    for end in range(len(target) + 1, len(full_word) + 1):
        prefix = full_word[:end]
        # Stop scanning at morpheme boundaries — anything after • is a suffix
        if end < len(full_word) and full_word[end - 1] in "•\u2022-":
            break
        if prefix in headword_set:
            return True
        if (prefix + "'") in headword_set:
            return True

    return False


def build_headword_set(entries: List[Dict[str, Any]]) -> Set[str]:
    """
    Build the normalized headword set from dictionary entries.

    Args:
        entries: List of S2E entry dicts with 'headword' field.

    Returns:
        Set of normalized headword strings for use in matches_headword().
    """
    hw_set = set()
    for entry in entries:
        hw = entry.get("headword", "")
        if hw:
            hw_set.add(_normalize_for_match(hw))
            # Also add without final glottal
            norm = _normalize_for_match(hw)
            if norm.endswith("'"):
                hw_set.add(norm[:-1])
    return hw_set


def filter_examples(
    headword: str,
    examples: List[Dict[str, Any]],
    headword_set: Set[str],
    stem: Optional[str] = None,
    text_key: str = "skiri_text",
) -> List[Dict[str, Any]]:
    """
    Filter a list of example dicts, keeping only those that genuinely
    reference the target headword.

    Args:
        headword:      Target headword
        examples:      List of example dicts
        headword_set:  Set of all known headwords (from build_headword_set)
        stem:          Optional pre-extracted stem
        text_key:      Key in each example dict containing the Skiri text

    Returns:
        Filtered list of examples.
    """
    return [
        ex for ex in examples
        if matches_headword(
            headword,
            ex.get(text_key, ""),
            headword_set,
            stem=stem,
        )
    ]


def filter_blue_book_refs(
    headword: str,
    refs: List[Dict[str, Any]],
    headword_set: Set[str],
    stem: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter Blue Book cross-references for a headword.

    Blue Book refs typically have 'Form' (Skiri) and 'English' fields.
    This checks the 'Form' field for genuine headword matches.
    """
    result = []
    for ref in refs:
        skiri_form = ref.get("Form", ref.get("form", ""))
        english = ref.get("English", ref.get("english", ""))

        # Accept if the Skiri form matches
        if skiri_form and matches_headword(headword, skiri_form, headword_set, stem):
            result.append(ref)
            continue

        # Accept if the English translation explicitly mentions the headword gloss
        # (catches cases like "cat" in the English column for context=BASIC_WORDS)
        context = ref.get("Context", ref.get("context", ""))
        if context in ("BASIC_WORDS", "ADDITIONAL_WORDS"):
            # These are vocabulary listings — keep them if they're for this entry
            # (they're usually pre-filtered by the BB extraction, so trust them)
            result.append(ref)
            continue

    return result


# ─── Self-test ────────────────────────────────────────────────────────────

def _self_test():
    """Quick validation of the filter logic."""
    # Simulate a headword set with common Skiri words
    hw_set = {
        "kiri", "kirike", "kiriks", "kiriku'", "kiri•wusu'",
        "kirik•erisu'",
        "paks", "paksu'", "pakskuuku'u'",
        "asaki", "asaaki'", "atira'",
        "ti", "ta", "ra",
    }

    tests = [
        # (headword, example, expected)
        ("kiri", "kirihkaatit",             True),   # compound: black cat
        ("kiri", "kiri, pus",               True),   # standalone: cat
        ("kiri", "kiri pus",                True),   # standalone: cat
        ("kiri", "Kirike ru'?",             False),  # different word: "what?"
        ("kiri", "Kirike ras•taspe'?",      False),  # different word: "what?"
        ("kiri", "KIRIKJ RUT•U'?",          False),  # OCR J variant of kirike
        ("kiri", "KIRIK1 RU'?",             False),  # OCR 1 variant of kirike
        ("kiri", "kiriks ti pahaat",         False),  # different word: "bead"
        ("kiri", "kiriks•pahat",            False),  # different word: "red bead"
        ("kiri", "kiri•wusu'",              True),   # compound: beer (cat-water)
        ("kiri", "Tah•raspe' kiri.",         True),   # standalone at end
        ("kiri", "kirik•erisu'",            False),  # different word: scout
        ("paksu'", "tiritpaksku",           False),  # incorporated stem, not headword
        ("paksu'", "paksu' ti pahaat",      True),   # standalone headword
    ]

    passed = 0
    failed = 0
    for hw, text, expected in tests:
        result = matches_headword(hw, text, hw_set)
        status = "✓" if result == expected else "✗"
        if result != expected:
            failed += 1
            print(f"  {status} matches_headword({hw!r}, {text!r}) = {result}, expected {expected}")
        else:
            passed += 1
            print(f"  {status} {hw!r} in {text[:40]!r} → {result}")

    print(f"\n  {passed}/{passed + failed} passed")
    return failed == 0


if __name__ == "__main__":
    print("Example Filter — self-test")
    print("=" * 50)
    ok = _self_test()
    if not ok:
        exit(1)
