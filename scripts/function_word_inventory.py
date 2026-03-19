#!/usr/bin/env python3
"""
Phase 3.1.6 — Seed Function Word Inventory
============================================
Combines:
  1. bb_gap_triage rows with category = 'function_word' (11 items)
  2. lexical_entries with grammatical_class IN
     ('CONJ','DEM','PRON','QUAN','LOC','INTERJ','ADV','NUM')

Creates a `function_words` table with columns:
  headword, grammatical_class, subclass, usage_notes, bb_attested, source

Usage:
    python scripts/function_word_inventory.py --db skiri_pawnee.db --dry-run
    python scripts/function_word_inventory.py --db skiri_pawnee.db
"""

import argparse
import logging
import re
import sqlite3
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FUNC_CLASSES = ("CONJ", "DEM", "PRON", "QUAN", "LOC", "INTERJ", "ADV", "NUM")

# Subclass inference from grammatical_class or gloss keywords
_SUBCLASS_MAP = {
    "CONJ": "conjunction",
    "DEM": "demonstrative",
    "PRON": "pronoun",
    "QUAN": "quantifier",
    "LOC": "locative",
    "INTERJ": "interjection",
    "ADV": "adverb",
    "NUM": "numeral",
    "PART": "particle",
}

# For BB function words, infer subclass from English gloss
_GLOSS_SUBCLASS = [
    (re.compile(r"\bhello\b|\bnow\b|\bokay\b", re.I), "interjection"),
    (re.compile(r"\byes\b|\bno\b", re.I), "interjection"),
    (re.compile(r"\bwhat\b|\bwho\b|\bwhere\b|\bwhen\b|\bhow\b", re.I), "interrogative"),
    (re.compile(r"\bthis\b|\bthat\b|\bother\b", re.I), "demonstrative"),
    (re.compile(r"\ba lot\b|\bvery\b|\bsome\b", re.I), "adverb"),
    (re.compile(r"\band\b|\bbut\b|\bor\b", re.I), "conjunction"),
    (re.compile(r"\bis\b|\bcopula\b", re.I), "copula"),
    (re.compile(r"\bindefinite\b", re.I), "indefinite_marker"),
]


def normalize_bb(form: str) -> str:
    """Normalize BB form to Parks orthography."""
    s = form.strip().rstrip(".")
    s = s.replace("\u2022", "")
    s = s.replace("'", "\u0294").replace("\u2019", "\u0294").replace("\u02bc", "\u0294")
    s = re.sub(r"ts", "c", s, flags=re.IGNORECASE)
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def infer_subclass_from_gloss(gloss: str) -> str:
    """Infer function word subclass from English gloss."""
    for pattern, subcls in _GLOSS_SUBCLASS:
        if pattern.search(gloss):
            return subcls
    return "particle"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed function_words table (Phase 3.1.6)"
    )
    parser.add_argument("--db", default="skiri_pawnee.db", help="SQLite database path")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be created without modifying the DB"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # ---- Source 1: BB function words from gap triage ----
    bb_rows = conn.execute("""
        SELECT bb_skiri_form, bb_english, confidence, notes
        FROM bb_gap_triage
        WHERE category = 'function_word'
        ORDER BY bb_skiri_form
    """).fetchall()
    log.info("BB function_word items: %d", len(bb_rows))

    bb_items = {}  # normalized headword -> dict
    for r in bb_rows:
        hw = normalize_bb(r["bb_skiri_form"])
        if not hw or hw in bb_items:
            continue
        gloss = r["bb_english"] or ""
        bb_items[hw] = {
            "headword": hw,
            "grammatical_class": "PART",
            "subclass": infer_subclass_from_gloss(gloss),
            "usage_notes": gloss,
            "bb_attested": 1,
            "source": "blue_book",
        }
    log.info("BB unique function words: %d", len(bb_items))

    # ---- Source 2: Existing lexical_entries with function-word classes ----
    placeholders = ",".join("?" for _ in FUNC_CLASSES)
    le_rows = conn.execute(f"""
        SELECT le.entry_id, le.headword, le.grammatical_class,
               le.blue_book_attested,
               (SELECT g.definition FROM glosses g
                WHERE g.entry_id = le.entry_id
                ORDER BY g.sense_number LIMIT 1) AS first_gloss
        FROM lexical_entries le
        WHERE le.grammatical_class IN ({placeholders})
        ORDER BY le.grammatical_class, le.headword
    """, FUNC_CLASSES).fetchall()
    log.info("Existing function-word entries: %d", len(le_rows))

    # ---- Merge: existing entries take priority, BB fills gaps ----
    inventory = {}  # headword -> dict

    for r in le_rows:
        hw = r["headword"]
        if hw in inventory:
            continue  # keep first occurrence
        gram = r["grammatical_class"]
        inventory[hw] = {
            "headword": hw,
            "grammatical_class": gram,
            "subclass": _SUBCLASS_MAP.get(gram, "other"),
            "usage_notes": r["first_gloss"] or "",
            "bb_attested": 1 if r["blue_book_attested"] else 0,
            "source": "parks_dictionary",
        }

    # Add BB items not already covered
    added_from_bb = 0
    for hw, it in bb_items.items():
        if hw not in inventory:
            inventory[hw] = it
            added_from_bb += 1
    log.info(
        "Combined inventory: %d (%d from Parks, %d new from BB)",
        len(inventory), len(inventory) - added_from_bb, added_from_bb,
    )

    # ---- Create table / insert ----
    create_sql = """
        CREATE TABLE IF NOT EXISTS function_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headword TEXT NOT NULL UNIQUE,
            grammatical_class TEXT NOT NULL,
            subclass TEXT,
            usage_notes TEXT,
            bb_attested INTEGER DEFAULT 0,
            source TEXT
        )
    """

    if args.dry_run:
        sys.stdout.buffer.write(
            f"\n=== DRY RUN: function_words table ===\n\n".encode("utf-8")
        )
        sys.stdout.buffer.write(
            f"Would create table with {len(inventory)} rows\n\n".encode("utf-8")
        )
        # Summary by class
        by_class = {}
        for it in inventory.values():
            by_class.setdefault(it["grammatical_class"], []).append(it)

        for cls in sorted(by_class):
            items = by_class[cls]
            sys.stdout.buffer.write(
                f"--- {cls} ({len(items)}) ---\n".encode("utf-8")
            )
            for it in sorted(items, key=lambda x: x["headword"]):
                bb = "*" if it["bb_attested"] else " "
                line = (
                    f"  {bb} {it['headword']:30s}  {it['subclass']:20s}  "
                    f"{it['source']:18s}  {it['usage_notes'][:50]}\n"
                )
                sys.stdout.buffer.write(line.encode("utf-8"))
            sys.stdout.buffer.write(b"\n")

        # Totals
        n_bb = sum(1 for it in inventory.values() if it["bb_attested"])
        sys.stdout.buffer.write(
            f"Total: {len(inventory)} function words "
            f"({n_bb} BB-attested, {len(inventory) - n_bb} Parks-only)\n".encode("utf-8")
        )
        sys.stdout.buffer.write(
            f"Sources: {len(inventory) - added_from_bb} from Parks, "
            f"{added_from_bb} new from BB\n".encode("utf-8")
        )
    else:
        conn.execute("DROP TABLE IF EXISTS function_words")
        conn.execute(create_sql)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_fw_class "
            "ON function_words(grammatical_class)"
        )
        for it in sorted(inventory.values(), key=lambda x: x["headword"]):
            conn.execute(
                "INSERT INTO function_words "
                "(headword, grammatical_class, subclass, usage_notes, bb_attested, source) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (it["headword"], it["grammatical_class"], it["subclass"],
                 it["usage_notes"], it["bb_attested"], it["source"]),
            )
        conn.commit()
        log.info("Created function_words table with %d rows", len(inventory))

    conn.close()


if __name__ == "__main__":
    main()
