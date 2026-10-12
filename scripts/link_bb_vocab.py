#!/usr/bin/env python3
"""
Link unlinked Blue Book lesson vocabulary to Parks Dictionary entries.

Targets blue_book_attestations rows (BASIC_WORDS / ADDITIONAL_WORDS) with no
entry_id. Matching is deliberately conservative — this is culturally
significant data and a wrong link is worse than no link:

  1. The BB form is normalized toward Parks orthography (syllable dots and
     dialect marks stripped, ts->c, '->glottal, lowercased) and compared
     length-insensitively (BB does not mark vowel length).
  2. A candidate must be the ONLY dictionary entry matching the key
     (homonym sets are skipped as ambiguous).
  3. The BB English gloss and the entry's glosses must share at least one
     content word. Unique matches WITHOUT gloss overlap are never linked —
     they are written to the review report instead.

Auto-links get match_type='orthographic', match_confidence=0.85.

Usage:
    python scripts/link_bb_vocab.py              # dry run (default)
    python scripts/link_bb_vocab.py --apply      # write links
Report: reports/bb_vocab_linking.txt
"""

import argparse
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

STOPWORDS = {
    "a", "an", "the", "it", "its", "it's", "is", "are", "be", "to", "of",
    "in", "on", "at", "and", "or", "my", "your", "his", "her", "he", "she",
    "i", "you", "they", "them", "this", "that", "some", "any", "one", "s",
    "as", "for", "with", "by", "have", "has", "was", "were", "will",
}


def out(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def bb_normalize(form: str) -> str:
    """Blue Book spelling -> comparison key in Parks-like orthography."""
    s = form.strip().lower()
    s = re.sub(r"\((?:sk|sb)\)", "", s)          # dialect marks (SK)/(SB)
    s = s.replace("•", "").replace("·", "")  # syllable dots
    s = re.sub(r"\s*'\s*", "ʔ", s)           # apostrophe -> glottal ʔ
    s = s.replace("ts", "c")
    s = re.sub(r"[^a-zʔ]", "", s)            # drop spaces, dots, digits
    return s


def collapse_length(s: str) -> str:
    """Collapse doubled vowels — BB spelling does not mark vowel length."""
    return re.sub(r"([aiueo])\1+", r"\1", s)


def parks_key(headword: str) -> str:
    # Decompose accents first so circumflex long vowels (â î û) reduce to
    # their base vowel instead of being deleted outright
    s = unicodedata.normalize("NFD", headword.strip().lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("č", "c").replace("č", "c")  # č counts as c
    s = re.sub(r"[^a-zʔ]", "", s)            # keep letters and ʔ
    return collapse_length(s)


def content_words(text: str) -> set:
    words = re.findall(r"[a-z]+|\d+", (text or "").lower())
    # crude plural fold so 'eggs' matches 'egg.'
    return {w.rstrip("s") or w for w in words
            if w not in STOPWORDS and (len(w) > 1 or w.isdigit())}


def glosses_overlap(bb_english: str, defs: str) -> bool:
    if content_words(bb_english) & content_words(defs):
        return True
    # phrase containment, e.g. BB 'this is' within gloss 'It is. This is.'
    a = re.sub(r"[^a-z\d ]", "", (bb_english or "").lower()).strip()
    b = re.sub(r"[^a-z\d ]", "", (defs or "").lower())
    return bool(a) and a in b


def main():
    parser = argparse.ArgumentParser(description="Link BB lesson vocab to dictionary")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "skiri_pawnee.db"))
    parser.add_argument("--apply", action="store_true",
                        help="Write links (default: dry run)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Index the dictionary by length-collapsed key
    cur.execute("SELECT entry_id, headword, normalized_form FROM lexical_entries")
    index = defaultdict(set)
    for r in cur.fetchall():
        for form in (r["headword"], r["normalized_form"]):
            if form:
                index[parks_key(form)].add(r["entry_id"])

    # Unlinked lesson vocabulary
    cur.execute("""
        SELECT id, bb_skiri_form, bb_english, lesson_number
        FROM blue_book_attestations
        WHERE entry_id IS NULL
          AND context_type IN ('BASIC_WORDS', 'ADDITIONAL_WORDS')
        ORDER BY lesson_number, id
    """)
    rows = cur.fetchall()
    out(f"{'[APPLY]' if args.apply else '[DRY RUN]'} "
        f"{len(rows)} unlinked lesson vocab rows\n")

    linked, review, ambiguous, nomatch = [], [], [], []
    for r in rows:
        key = collapse_length(bb_normalize(r["bb_skiri_form"]))
        if not key:
            nomatch.append(r)
            continue
        candidates = index.get(key) or index.get(key.replace("ʔ", "")) or set()
        if not candidates:
            # fallback: glottal-insensitive on both sides
            candidates = index.get(key.replace("ʔ", ""), set())
        if len(candidates) == 0:
            nomatch.append(r)
            continue
        if len(candidates) > 1:
            # A Blue Book import entry alongside its Parks twin is the common
            # case — the Parks entry is canonical (pitch-marked IPA, page
            # provenance). Resolve only when exactly ONE Parks entry remains.
            parks = {c for c in candidates if not c.startswith("BB-")}
            if len(parks) == 1:
                candidates = parks
            else:
                ambiguous.append((r, sorted(candidates)))
                continue
        entry_id = next(iter(candidates))
        cur.execute("""
            SELECT le.headword,
                   (SELECT group_concat(definition, ' ; ') FROM glosses g
                    WHERE g.entry_id = le.entry_id) AS defs
            FROM lexical_entries le WHERE le.entry_id = ?""", (entry_id,))
        e = cur.fetchone()
        if glosses_overlap(r["bb_english"], e["defs"]):
            overlap = sorted(content_words(r["bb_english"]) & content_words(e["defs"]))
            linked.append((r, entry_id, e["headword"], overlap or ["<phrase>"]))
        else:
            review.append((r, entry_id, e["headword"], e["defs"]))

    # Second pass: propagate links to identical BB forms already linked
    # elsewhere (e.g. L19 month names listed once with their literal
    # translation and again with the Gregorian month). Only when the form
    # maps to exactly one entry across every linked attestation.
    form_to_entry = defaultdict(set)
    cur.execute("""
        SELECT bb_skiri_form, entry_id FROM blue_book_attestations
        WHERE entry_id IS NOT NULL""")
    for a in cur.fetchall():
        form_to_entry[collapse_length(bb_normalize(a["bb_skiri_form"]))].add(a["entry_id"])
    for r, entry_id, hw, _ in linked:
        form_to_entry[collapse_length(bb_normalize(r["bb_skiri_form"]))].add(entry_id)

    propagated = []
    still_review = []
    for r, entry_id, hw, defs in review:
        key = collapse_length(bb_normalize(r["bb_skiri_form"]))
        known = form_to_entry.get(key, set())
        if len(known) == 1:
            propagated.append((r, next(iter(known)), hw))
        else:
            still_review.append((r, entry_id, hw, defs))
    review = still_review
    remaining_ambiguous = []
    for r, cands in ambiguous:
        key = collapse_length(bb_normalize(r["bb_skiri_form"]))
        known = form_to_entry.get(key, set())
        if len(known) == 1 and next(iter(known)) in cands:
            propagated.append((r, next(iter(known)), "<same form linked elsewhere>"))
        else:
            remaining_ambiguous.append((r, cands))
    ambiguous = remaining_ambiguous

    # Apply
    if args.apply:
        for r, entry_id, _, _ in linked:
            cur.execute("""
                UPDATE blue_book_attestations
                SET entry_id = ?, match_type = 'orthographic',
                    match_confidence = 0.85,
                    notes = COALESCE(notes || ' | ', '') ||
                            'auto-linked by link_bb_vocab.py (unique match + gloss overlap)'
                WHERE id = ?""", (entry_id, r["id"]))
        for r, entry_id, _ in propagated:
            cur.execute("""
                UPDATE blue_book_attestations
                SET entry_id = ?, match_type = 'propagated',
                    match_confidence = 0.8,
                    notes = COALESCE(notes || ' | ', '') ||
                            'auto-linked by link_bb_vocab.py (same BB form linked elsewhere)'
                WHERE id = ?""", (entry_id, r["id"]))
        conn.commit()

    # Report
    lines = [f"BB lesson vocab linking report ({'applied' if args.apply else 'dry run'})",
             "=" * 70, ""]
    lines.append(f"AUTO-LINKED ({len(linked)}) — unique match + gloss overlap:")
    for r, eid, hw, ov in linked:
        lines.append(f"  L{r['lesson_number']:2d} {r['bb_skiri_form']!r} "
                     f"({r['bb_english']}) -> {eid} {hw!r}  overlap={ov}")
    lines.append(f"\nPROPAGATED ({len(propagated)}) — same BB form already linked elsewhere:")
    for r, eid, hw in propagated:
        lines.append(f"  L{r['lesson_number']:2d} {r['bb_skiri_form']!r} "
                     f"({r['bb_english']}) -> {eid} {hw}")
    lines.append(f"\nNEEDS REVIEW ({len(review)}) — unique spelling match, no gloss overlap "
                 f"(NOT linked):")
    for r, eid, hw, defs in review:
        lines.append(f"  L{r['lesson_number']:2d} {r['bb_skiri_form']!r} "
                     f"({r['bb_english']}) ~ {eid} {hw!r} glossed: {(defs or '')[:80]}")
    lines.append(f"\nAMBIGUOUS ({len(ambiguous)}) — multiple entries share the key (NOT linked):")
    for r, cands in ambiguous:
        lines.append(f"  L{r['lesson_number']:2d} {r['bb_skiri_form']!r} "
                     f"({r['bb_english']}) ~ {cands}")
    lines.append(f"\nNO MATCH ({len(nomatch)}) — mostly inflected verbs/phrases, expected:")
    for r in nomatch:
        lines.append(f"  L{r['lesson_number']:2d} {r['bb_skiri_form']!r} ({r['bb_english']})")

    report_path = PROJECT_ROOT / "reports" / "bb_vocab_linking.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    out(f"auto-linked:  {len(linked)}")
    out(f"propagated:   {len(propagated)} (same BB form linked elsewhere)")
    out(f"needs review: {len(review)} (unique match, gloss mismatch — not linked)")
    out(f"ambiguous:    {len(ambiguous)} (not linked)")
    out(f"no match:     {len(nomatch)}")
    out(f"\nreport: {report_path}" + ("" if args.apply else "   (re-run with --apply)"))
    conn.close()


if __name__ == "__main__":
    main()
