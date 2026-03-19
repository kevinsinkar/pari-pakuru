#!/usr/bin/env python3
"""
Import high-value Blue Book gap items into the dictionary.
============================================================
Queries bb_gap_triage for rows with category IN ('noun_unlisted',
'function_word', 'loanword') and creates new lexical_entries + glosses.

Normalization (BB -> Parks orthography):
  ts -> c,  ' / \u2019 -> \u0294,  \u2022 (link dot) -> removed,  trailing . -> stripped

Usage:
    python scripts/import_bb_items.py --db skiri_pawnee.db --dry-run
    python scripts/import_bb_items.py --db skiri_pawnee.db
"""

import argparse
import logging
import re
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_bb_to_parks(bb_form: str) -> str:
    """Convert Blue Book orthography to Parks-compatible headword form."""
    if not bb_form:
        return ""
    s = bb_form.strip().rstrip(".")
    # Remove link dot (structural marker in BB)
    s = s.replace("\u2022", "")
    # Remove stray spaces around link-dot positions
    s = re.sub(r"\s+", "", s) if " " not in bb_form.replace(" .", "").replace(". ", "").strip() else s.strip()
    # Glottal stop: BB ' / \u2019 / \u02bc -> Parks \u0294
    s = s.replace("'", "\u0294").replace("\u2019", "\u0294").replace("\u02bc", "\u0294")
    # ts -> c (BB affricate notation)
    s = re.sub(r"ts", "c", s, flags=re.IGNORECASE)
    # Lowercase
    s = s.lower()
    # Collapse residual whitespace
    s = re.sub(r"\s+", "", s)
    return s


# ---------------------------------------------------------------------------
# Grammatical class inference
# ---------------------------------------------------------------------------

# BB function_word items we can subclassify by gloss keywords
_FUNCTION_WORD_CLASS_MAP = [
    (re.compile(r"\bhello\b|\bnow\b|\bokay\b", re.I), "INTERJ"),
    (re.compile(r"\byes\b|\bno\b", re.I), "INTERJ"),
    (re.compile(r"\bwhat\b|\bwho\b|\bwhere\b|\bwhen\b|\bhow\b", re.I), "PRON"),
    (re.compile(r"\bthis\b|\bthat\b|\bother\b|\bpast\b", re.I), "DEM"),
    (re.compile(r"\ba lot\b|\bvery\b|\bsome\b|\bone\b", re.I), "ADV"),
    (re.compile(r"\band\b|\bbut\b|\bor\b", re.I), "CONJ"),
    (re.compile(r"\bis\b|\bcopula\b", re.I), "PART"),
    (re.compile(r"\bindefinite\b", re.I), "PART"),
]


def infer_grammatical_class(category: str, english_gloss: str) -> str:
    """Infer grammatical_class from triage category and English gloss."""
    if category == "noun_unlisted":
        return "N"
    if category == "loanword":
        return "N"
    if category == "function_word":
        gloss = english_gloss or ""
        for pattern, cls in _FUNCTION_WORD_CLASS_MAP:
            if pattern.search(gloss):
                return cls
        return "PART"  # default for function words
    return "N"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Import high-value BB gap items into dictionary"
    )
    parser.add_argument("--db", default="skiri_pawnee.db", help="SQLite database path")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be added without modifying the DB"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # ---- Ensure `source` column exists on lexical_entries ----
    cols = {r[1] for r in conn.execute("PRAGMA table_info(lexical_entries)")}
    if "source" not in cols:
        if args.dry_run:
            log.info("[dry-run] Would add column: lexical_entries.source TEXT")
        else:
            conn.execute("ALTER TABLE lexical_entries ADD COLUMN source TEXT")
            conn.commit()
            log.info("Added column: lexical_entries.source")

    # ---- Load high-value BB gap items ----
    rows = conn.execute("""
        SELECT bb_skiri_form, bb_english, category, confidence, notes
        FROM bb_gap_triage
        WHERE category IN ('noun_unlisted', 'function_word', 'loanword')
        ORDER BY category, bb_skiri_form
    """).fetchall()
    log.info("Loaded %d high-value rows from bb_gap_triage", len(rows))

    # ---- Deduplicate by normalized headword (keep highest confidence) ----
    existing_headwords = {
        r[0] for r in conn.execute("SELECT headword FROM lexical_entries")
    }

    items = {}  # normalized_headword -> best row dict
    for r in rows:
        hw = normalize_bb_to_parks(r["bb_skiri_form"])
        if not hw:
            continue
        conf = r["confidence"] or 0.0
        if hw not in items or conf > items[hw]["confidence"]:
            items[hw] = {
                "bb_form": r["bb_skiri_form"],
                "headword": hw,
                "english_gloss": r["bb_english"] or "",
                "category": r["category"],
                "confidence": conf,
                "notes": r["notes"] or "",
            }

    log.info("Deduplicated to %d unique normalized headwords", len(items))

    # ---- Filter out any that already exist ----
    existing_norm = {h.lower() for h in existing_headwords}
    new_items = {
        hw: it for hw, it in items.items()
        if hw.lower() not in existing_norm
    }
    skipped = len(items) - len(new_items)
    if skipped:
        log.info("Skipped %d items already in lexical_entries", skipped)
    log.info("Items to import: %d", len(new_items))

    # ---- Generate entry IDs ----
    # Pattern: BB-{headword_slug}-{seq}
    seq = 1
    to_insert = []
    for hw in sorted(new_items):
        it = new_items[hw]
        # Slug: replace non-alnum with dash, collapse
        slug = re.sub(r"[^a-z0-9]+", "-", hw).strip("-")[:40]
        entry_id = f"BB-{slug}-{seq:04d}"
        gram_class = infer_grammatical_class(it["category"], it["english_gloss"])
        to_insert.append({
            "entry_id": entry_id,
            "headword": hw,
            "grammatical_class": gram_class,
            "blue_book_attested": 1,
            "source": "blue_book",
            "english_gloss": it["english_gloss"],
            "category": it["category"],
            "bb_form": it["bb_form"],
        })
        seq += 1

    # ---- Output / insert ----
    if args.dry_run:
        sys.stdout.buffer.write(
            f"\n=== DRY RUN: {len(to_insert)} items would be added ===\n\n".encode("utf-8")
        )
        by_cat = {}
        for it in to_insert:
            by_cat.setdefault(it["category"], []).append(it)

        for cat in sorted(by_cat):
            sys.stdout.buffer.write(
                f"--- {cat.upper()} ({len(by_cat[cat])}) ---\n".encode("utf-8")
            )
            for it in by_cat[cat]:
                line = (
                    f"  {it['entry_id']:30s}  {it['headword']:30s}  "
                    f"{it['grammatical_class']:6s}  {it['english_gloss']}\n"
                )
                sys.stdout.buffer.write(line.encode("utf-8"))
            sys.stdout.buffer.write(b"\n")

        sys.stdout.buffer.write(
            f"Total: {len(to_insert)} new entries "
            f"({sum(1 for i in to_insert if i['category']=='noun_unlisted')} nouns, "
            f"{sum(1 for i in to_insert if i['category']=='function_word')} function words, "
            f"{sum(1 for i in to_insert if i['category']=='loanword')} loanwords)\n".encode("utf-8")
        )
    else:
        cur = conn.cursor()
        for it in to_insert:
            cur.execute(
                "INSERT INTO lexical_entries "
                "(entry_id, headword, grammatical_class, blue_book_attested, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (it["entry_id"], it["headword"], it["grammatical_class"],
                 it["blue_book_attested"], it["source"]),
            )
            cur.execute(
                "INSERT INTO glosses (entry_id, sense_number, definition) "
                "VALUES (?, 1, ?)",
                (it["entry_id"], it["english_gloss"]),
            )
        conn.commit()
        log.info("Inserted %d lexical_entries + glosses", len(to_insert))

    conn.close()


if __name__ == "__main__":
    main()
