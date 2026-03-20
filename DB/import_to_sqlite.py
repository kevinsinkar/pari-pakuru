#!/usr/bin/env python3
"""
Phase 1.2 — Import linked JSON data into SQLite database.

Reads:
  - skiri_to_english_respelled.json  (S2E — primary linguistic record, 4,273 entries)
  - english_to_skiri_linked.json     (E2S — English index layer, 6,414 entries)

Writes:
  - skiri_pawnee.db  (SQLite database per schema.sql)

Usage:
  python import_to_sqlite.py --s2e path/to/skiri_to_english_respelled.json \
                              --e2s path/to/english_to_skiri_linked.json \
                              --db  skiri_pawnee.db \
                              --schema schema.sql
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# =============================================================================
# Helpers
# =============================================================================

def safe_json_dumps(obj):
    """JSON-serialize, returning None for None/empty."""
    if obj is None:
        return None
    if isinstance(obj, (list, dict)) and not obj:
        return None
    return json.dumps(obj, ensure_ascii=False)


def safe_str(val):
    """Return stripped string or None."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def extract_nested(d, *keys, default=None):
    """Safely walk nested dicts/keys."""
    current = d
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, default)
        else:
            return default
    return current


# =============================================================================
# S2E Import
# =============================================================================

def import_s2e_entry(cursor, entry):
    """Import a single S2E entry into lexical_entries + child tables."""

    entry_id = entry.get("entry_id")
    if not entry_id:
        log.warning("S2E entry missing entry_id, skipping: %s", entry.get("headword", "?"))
        return False

    headword = safe_str(entry.get("headword"))
    normalized_form = safe_str(entry.get("normalized_form"))

    part_i = entry.get("part_I") or {}
    meta = entry.get("entry_metadata") or {}

    phonetic_form = safe_str(part_i.get("phonetic_form"))
    simplified_pronunciation = safe_str(part_i.get("simplified_pronunciation"))
    # Also check top-level (respelling script may write here)
    if not simplified_pronunciation:
        simplified_pronunciation = safe_str(entry.get("simplified_pronunciation"))
    if not normalized_form:
        normalized_form = safe_str(entry.get("normalized_form"))

    stem_preverb = safe_str(part_i.get("stem_preverb"))
    gram_info = part_i.get("grammatical_info") or {}
    grammatical_class = safe_str(gram_info.get("grammatical_class"))
    verb_class = safe_str(gram_info.get("verb_class"))
    additional_forms = safe_json_dumps(gram_info.get("additional_forms"))

    page_number = meta.get("page_number")
    column_position = safe_str(meta.get("column"))
    compound_structure = safe_json_dumps(entry.get("compound_structure"))

    # -- lexical_entries --
    cursor.execute("""
        INSERT OR REPLACE INTO lexical_entries
        (entry_id, headword, normalized_form, phonetic_form, simplified_pronunciation,
         stem_preverb, grammatical_class, verb_class, additional_forms,
         page_number, column_position, compound_structure, raw_entry_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry_id, headword, normalized_form, phonetic_form, simplified_pronunciation,
        stem_preverb, grammatical_class, verb_class, additional_forms,
        page_number, column_position, compound_structure,
        json.dumps(entry, ensure_ascii=False),
    ))

    # -- glosses --
    glosses = part_i.get("glosses") or []
    for g in glosses:
        sense_num = g.get("number") or 1
        definition = safe_str(g.get("definition"))
        if not definition:
            continue
        usage_notes = safe_str(g.get("usage_notes"))
        cursor.execute("""
            INSERT OR IGNORE INTO glosses (entry_id, sense_number, definition, usage_notes)
            VALUES (?, ?, ?, ?)
        """, (entry_id, sense_num, definition, usage_notes))

    # -- paradigmatic_forms --
    part_ii = entry.get("part_II") or {}
    paradigms = part_ii.get("paradigmatic_forms") or {}

    # S2E paradigms can be dict {"form_1": "...", "form_2": "..."} or list
    if isinstance(paradigms, dict):
        for key, form_str in paradigms.items():
            if form_str:
                # Extract number from "form_1", "form_2", etc.
                try:
                    form_num = int(key.split("_")[-1])
                except (ValueError, IndexError):
                    continue
                cursor.execute("""
                    INSERT OR IGNORE INTO paradigmatic_forms (entry_id, form_number, skiri_form)
                    VALUES (?, ?, ?)
                """, (entry_id, form_num, safe_str(form_str)))
    elif isinstance(paradigms, list):
        for p in paradigms:
            form_num = p.get("form_number")
            form_str = safe_str(p.get("skiri_form"))
            if form_num and form_str:
                cursor.execute("""
                    INSERT OR IGNORE INTO paradigmatic_forms (entry_id, form_number, skiri_form)
                    VALUES (?, ?, ?)
                """, (entry_id, form_num, form_str))

    # -- examples --
    examples = part_ii.get("examples") or []
    for ex in examples:
        skiri_text = safe_str(ex.get("skiri_text"))
        if not skiri_text:
            continue
        eng_trans = safe_str(ex.get("english_translation"))
        context = safe_str(ex.get("usage_context"))
        cursor.execute("""
            INSERT INTO examples (entry_id, skiri_text, english_translation, usage_context, source)
            VALUES (?, ?, ?, ?, 'parks_dictionary')
        """, (entry_id, skiri_text, eng_trans, context))

    # -- etymology --
    etym = part_i.get("etymology") or {}
    raw_etym = safe_str(etym.get("raw_etymology"))
    literal = safe_str(etym.get("literal_translation"))
    constituents = safe_json_dumps(etym.get("constituent_elements"))
    if raw_etym or literal or constituents:
        cursor.execute("""
            INSERT OR IGNORE INTO etymology (entry_id, raw_etymology, literal_translation, constituent_elements)
            VALUES (?, ?, ?, ?)
        """, (entry_id, raw_etym, literal, constituents))

    # -- cognates --
    cognates = part_i.get("cognates") or []
    for cog in cognates:
        lang = safe_str(cog.get("language"))
        form = safe_str(cog.get("form"))
        if lang and form:
            cursor.execute("""
                INSERT INTO cognates (entry_id, language, form)
                VALUES (?, ?, ?)
            """, (entry_id, lang, form))

    # -- derived_stems --
    derived = entry.get("derived_stems") or []
    for ds in derived:
        stem_form = safe_str(ds.get("stem_form") or ds.get("headword"))
        if not stem_form:
            continue
        cursor.execute("""
            INSERT INTO derived_stems (entry_id, stem_form, phonetic_form, definition, raw_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            entry_id,
            stem_form,
            safe_str(ds.get("phonetic_form")),
            safe_str(ds.get("definition")),
            json.dumps(ds, ensure_ascii=False),
        ))

    return True


# =============================================================================
# E2S Import
# =============================================================================

def import_e2s_entry(cursor, entry):
    """Import a single E2S entry into english_index + cross_references."""

    english_word = safe_str(entry.get("english_entry_word"))
    if not english_word:
        log.warning("E2S entry missing english_entry_word, skipping")
        return 0

    entry_meta = entry.get("entry_metadata") or {}
    e2s_page = entry_meta.get("page_number")

    subentries = entry.get("subentries") or entry.get("skiri_subentries") or []
    imported = 0

    for sub in subentries:
        sub_num = sub.get("subentry_number") or 1
        s2e_id = safe_str(sub.get("s2e_entry_id"))
        match_type = safe_str(sub.get("s2e_match_type"))

        sub_part_i = sub.get("part_I") or {}
        skiri_term = safe_str(sub_part_i.get("skiri_term"))
        phonetic = safe_str(sub_part_i.get("phonetic_form"))
        gram = sub_part_i.get("grammatical_classification") or {}
        gram_class = safe_str(gram.get("class_abbr"))
        v_class = safe_str(gram.get("verb_class"))

        cursor.execute("""
            INSERT INTO english_index
            (english_word, subentry_number, entry_id, s2e_match_type,
             skiri_term, phonetic_form, grammatical_class, verb_class,
             page_number, raw_subentry_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            english_word, sub_num, s2e_id, match_type,
            skiri_term, phonetic, gram_class, v_class,
            e2s_page,
            json.dumps(sub, ensure_ascii=False),
        ))
        imported += 1

        # -- cross_references (Part III) --
        part_iii = sub.get("part_III") or {}
        xrefs = part_iii.get("cross_references") or []
        for xref in xrefs:
            to_term = safe_str(xref.get("english_term"))
            if not to_term:
                continue
            skiri_equivs = safe_json_dumps(xref.get("skiri_equivalents"))
            cursor.execute("""
                INSERT INTO cross_references
                (from_english_word, to_english_term, skiri_equivalents, source_page)
                VALUES (?, ?, ?, ?)
            """, (english_word, to_term, skiri_equivs, e2s_page))

    return imported


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Import Skiri Pawnee JSON data into SQLite")
    parser.add_argument("--s2e", required=True, help="Path to skiri_to_english_respelled.json")
    parser.add_argument("--e2s", required=True, help="Path to english_to_skiri_linked.json")
    parser.add_argument("--db", default="skiri_pawnee.db", help="Output SQLite database path")
    parser.add_argument("--schema", default="schema.sql", help="Path to schema.sql")
    args = parser.parse_args()

    # Validate inputs
    for path, label in [(args.s2e, "S2E"), (args.e2s, "E2S"), (args.schema, "Schema")]:
        if not os.path.exists(path):
            log.error("%s file not found: %s", label, path)
            sys.exit(1)

    # Remove existing DB for clean import
    if os.path.exists(args.db):
        log.info("Removing existing database: %s", args.db)
        os.remove(args.db)

    # Create database and apply schema
    log.info("Creating database: %s", args.db)
    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    log.info("Applying schema from: %s", args.schema)
    with open(args.schema, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    cursor = conn.cursor()

    # ---- Import S2E ----
    log.info("Loading S2E data from: %s", args.s2e)
    with open(args.s2e, "r", encoding="utf-8") as f:
        s2e_data = json.load(f)

    log.info("Importing %d S2E entries...", len(s2e_data))
    s2e_ok = 0
    s2e_skip = 0
    for entry in s2e_data:
        if import_s2e_entry(cursor, entry):
            s2e_ok += 1
        else:
            s2e_skip += 1

    conn.commit()
    log.info("S2E import complete: %d imported, %d skipped", s2e_ok, s2e_skip)

    # ---- Import E2S ----
    log.info("Loading E2S data from: %s", args.e2s)
    with open(args.e2s, "r", encoding="utf-8") as f:
        e2s_data = json.load(f)

    log.info("Importing %d E2S entries...", len(e2s_data))
    e2s_entries = 0
    e2s_subentries = 0
    for entry in e2s_data:
        count = import_e2s_entry(cursor, entry)
        if count > 0:
            e2s_entries += 1
            e2s_subentries += count

    conn.commit()
    log.info("E2S import complete: %d entries, %d subentries", e2s_entries, e2s_subentries)

    # ---- Record metadata ----
    now = datetime.now().isoformat()
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("import_timestamp", now))
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("s2e_source", os.path.basename(args.s2e)))
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("e2s_source", os.path.basename(args.e2s)))
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("s2e_count", str(s2e_ok)))
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("e2s_entry_count", str(e2s_entries)))
    cursor.execute("INSERT INTO import_metadata VALUES (?, ?)", ("e2s_subentry_count", str(e2s_subentries)))
    conn.commit()

    # ---- Summary stats ----
    stats = {}
    for table in ["lexical_entries", "glosses", "paradigmatic_forms", "examples",
                   "etymology", "cognates", "derived_stems", "english_index", "cross_references"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]

    log.info("=== Database Summary ===")
    for table, count in stats.items():
        log.info("  %-25s %6d rows", table, count)

    # Linked vs unlinked english_index
    cursor.execute("SELECT COUNT(*) FROM english_index WHERE entry_id IS NOT NULL")
    linked = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM english_index WHERE entry_id IS NULL")
    unlinked = cursor.fetchone()[0]
    log.info("  english_index linked:     %6d", linked)
    log.info("  english_index unlinked:   %6d", unlinked)

    db_size = os.path.getsize(args.db) / (1024 * 1024)
    log.info("Database size: %.2f MB", db_size)

    conn.close()
    log.info("Done. Database written to: %s", args.db)


if __name__ == "__main__":
    main()
