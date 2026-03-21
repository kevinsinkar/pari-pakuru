#!/usr/bin/env python3
"""Deduplicate lexical entries in skiri_pawnee.db.

Handles two cases:
  1. p2/p71 duplicate pairs (22 pairs) — same headword + same sense-1 definition
     on pages 2 and 71. Keeps the p2 entry (higher-quality IPA with stress marks).
  2. kusisaar parser artifact — two entries on p103 where forms were split across
     entries. Merges into the more complete entry (-2019) and deletes -2018.

Does NOT touch:
  - hiksukac (VD vs VP — legitimate polysemy)
  - racawaktaarik (VI vs VT — legitimate polysemy)

Usage:
  python scripts/dedup_entries.py                  # dry-run (default)
  python scripts/dedup_entries.py --apply          # actually modify the DB
  python scripts/dedup_entries.py --db other.db    # specify DB path
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# Tables with entry_id column that need cascade deletion
CHILD_TABLES = [
    "glosses",
    "paradigmatic_forms",
    "examples",
    "etymology",
    "cognates",
    "derived_stems",
    "english_index",
    "semantic_tags",
    "blue_book_attestations",
    "noun_stems",
    "community_feedback",
]

# Same-page entries that are legitimate polysemy — NEVER delete
POLYSEMY_SKIP = {
    # VD vs VP — different grammatical classes and paradigmatic forms
    ("SK-hiksukac-p390-3864", "SK-hiksukac-p390-3865"),
    # VI vs VT — intransitive "telephone" vs transitive "telephone someone"
    ("SK-racawaktaarik-p478-4115", "SK-racawaktaarik-p478-4116"),
}

# Parser artifact: kusisaar -2018 is a subset of -2019 (forms 3/4/5 only,
# no examples). -2019 has all 5 forms + example sentence.
MERGE_CASES = {
    "SK-kusisaar-p103-2018": "SK-kusisaar-p103-2019",  # delete -> keep
}


def log(msg):
    """Safe print for Windows console."""
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))


def find_p2_p71_duplicates(conn):
    """Find duplicate pairs where p2 and p71 entries share headword + sense 1."""
    rows = conn.execute("""
        SELECT
            a.entry_id AS p2_id,
            b.entry_id AS p71_id,
            a.headword
        FROM lexical_entries a
        JOIN lexical_entries b
            ON a.headword = b.headword AND a.entry_id != b.entry_id
        JOIN glosses ga ON ga.entry_id = a.entry_id AND ga.sense_number = 1
        JOIN glosses gb ON gb.entry_id = b.entry_id AND gb.sense_number = 1
            AND ga.definition = gb.definition
        WHERE a.entry_id LIKE '%-p2-%'
          AND b.entry_id LIKE '%-p71-%'
        ORDER BY a.headword
    """).fetchall()
    return rows


def count_child_rows(conn, entry_id):
    """Count rows referencing this entry_id across all child tables."""
    counts = {}
    for table in CHILD_TABLES:
        try:
            n = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE entry_id = ?", (entry_id,)
            ).fetchone()[0]
            if n > 0:
                counts[table] = n
        except sqlite3.OperationalError:
            pass
    return counts


def migrate_tags(conn, from_id, to_id, dry_run=True):
    """Move semantic_tags from one entry to another, skipping duplicates."""
    existing = {
        r[0]
        for r in conn.execute(
            "SELECT tag FROM semantic_tags WHERE entry_id = ?", (to_id,)
        ).fetchall()
    }
    to_migrate = conn.execute(
        "SELECT tag FROM semantic_tags WHERE entry_id = ?", (from_id,)
    ).fetchall()

    migrated = []
    for (tag,) in to_migrate:
        if tag not in existing:
            migrated.append(tag)
            if not dry_run:
                conn.execute(
                    "INSERT INTO semantic_tags (entry_id, tag) VALUES (?, ?)",
                    (to_id, tag),
                )

    return migrated


def migrate_examples(conn, from_id, to_id, dry_run=True):
    """Move examples from one entry to another, skipping duplicates."""
    existing = {
        r[0]
        for r in conn.execute(
            "SELECT skiri_text FROM examples WHERE entry_id = ?", (to_id,)
        ).fetchall()
    }
    to_migrate = conn.execute(
        "SELECT skiri_text, english_translation, usage_context FROM examples WHERE entry_id = ?",
        (from_id,),
    ).fetchall()

    migrated = []
    for skiri, eng, ctx in to_migrate:
        if skiri not in existing:
            migrated.append(skiri)
            if not dry_run:
                conn.execute(
                    "INSERT INTO examples (entry_id, skiri_text, english_translation, usage_context) VALUES (?, ?, ?, ?)",
                    (to_id, skiri, eng, ctx),
                )

    return migrated


def delete_entry(conn, entry_id, dry_run=True):
    """Delete an entry and all its child rows from all tables."""
    for table in CHILD_TABLES:
        try:
            if dry_run:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE entry_id = ?", (entry_id,)
                ).fetchone()[0]
            else:
                cur = conn.execute(
                    f"DELETE FROM {table} WHERE entry_id = ?", (entry_id,)
                )
                n = cur.rowcount
        except sqlite3.OperationalError:
            continue

    # Delete from lexical_entries last
    if not dry_run:
        conn.execute("DELETE FROM lexical_entries WHERE entry_id = ?", (entry_id,))


def main():
    parser = argparse.ArgumentParser(description="Deduplicate lexical entries")
    parser.add_argument(
        "--db", default="skiri_pawnee.db", help="Path to SQLite database"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Actually modify the DB (default: dry-run)"
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        log(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    dry_run = not args.apply

    if dry_run:
        log("=" * 60)
        log("DRY RUN — no changes will be made")
        log("=" * 60)
    else:
        # Back up the DB outside the working directory
        backup_dir = Path.home() / ".pari_pakuru_backups"
        backup_dir.mkdir(exist_ok=True)
        backup_name = f"{db_path.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{db_path.suffix}"
        backup_path = backup_dir / backup_name
        shutil.copy2(db_path, backup_path)
        log(f"Backup created: {backup_path}")
        log(f"  (outside working tree: {backup_dir})")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    # ── Phase 1: p2/p71 duplicate pairs ──────────────────────────
    log("\n--- Phase 1: p2/p71 Duplicate Pairs ---")
    pairs = find_p2_p71_duplicates(conn)
    log(f"Found {len(pairs)} p2/p71 duplicate pairs")

    delete_ids = []
    for p2_id, p71_id, headword in pairs:
        # Skip known polysemy pairs
        pair_key = tuple(sorted([p2_id, p71_id]))
        if pair_key in POLYSEMY_SKIP or (p71_id, p2_id) in POLYSEMY_SKIP:
            log(f"  SKIP (polysemy): {headword} [{p2_id} / {p71_id}]")
            continue

        p71_children = count_child_rows(conn, p71_id)
        p2_children = count_child_rows(conn, p2_id)

        # Check for unique data on p71 that should migrate to p2
        migrated_tags = migrate_tags(conn, p71_id, p2_id, dry_run=True)
        migrated_examples = migrate_examples(conn, p71_id, p2_id, dry_run=True)

        log(f"  DELETE p71: {headword}")
        log(f"    Keep:   {p2_id} (children: {p2_children})")
        log(f"    Delete: {p71_id} (children: {p71_children})")
        if migrated_tags:
            log(f"    Migrate tags to p2: {migrated_tags}")
        if migrated_examples:
            log(f"    Migrate examples to p2: {migrated_examples}")

        delete_ids.append((p71_id, p2_id, headword))

    # ── Phase 2: kusisaar parser artifact ────────────────────────
    log("\n--- Phase 2: Parser Artifact Merges ---")
    for delete_id, keep_id in MERGE_CASES.items():
        headword = conn.execute(
            "SELECT headword FROM lexical_entries WHERE entry_id = ?", (delete_id,)
        ).fetchone()
        if not headword:
            log(f"  SKIP (not found): {delete_id}")
            continue
        headword = headword[0]

        del_children = count_child_rows(conn, delete_id)
        keep_children = count_child_rows(conn, keep_id)
        migrated_tags = migrate_tags(conn, delete_id, keep_id, dry_run=True)
        migrated_examples = migrate_examples(conn, delete_id, keep_id, dry_run=True)

        log(f"  MERGE: {headword}")
        log(f"    Keep:   {keep_id} (children: {keep_children})")
        log(f"    Delete: {delete_id} (children: {del_children})")
        if migrated_tags:
            log(f"    Migrate tags: {migrated_tags}")
        if migrated_examples:
            log(f"    Migrate examples: {migrated_examples}")

        delete_ids.append((delete_id, keep_id, headword))

    # ── Summary ──────────────────────────────────────────────────
    log(f"\n--- Summary ---")
    log(f"Entries to delete: {len(delete_ids)}")
    log(f"Polysemy pairs preserved: {len(POLYSEMY_SKIP)}")

    if dry_run:
        log("\nRe-run with --apply to execute these changes.")
        conn.close()
        return

    # ── Execute ──────────────────────────────────────────────────
    log("\nApplying changes...")
    for del_id, keep_id, headword in delete_ids:
        # Migrate unique data first
        migrate_tags(conn, del_id, keep_id, dry_run=False)
        migrate_examples(conn, del_id, keep_id, dry_run=False)
        # Delete the duplicate
        delete_entry(conn, del_id, dry_run=False)
        log(f"  Deleted: {del_id} ({headword})")

    conn.commit()

    # Verify
    remaining = conn.execute("SELECT COUNT(*) FROM lexical_entries").fetchone()[0]
    log(f"\nDone. Lexical entries: {remaining} (was {remaining + len(delete_ids)})")

    conn.close()


if __name__ == "__main__":
    main()
