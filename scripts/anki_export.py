#!/usr/bin/env python3
"""Export Skiri Pawnee dictionary entries to Anki .apkg decks.

Generates one deck per semantic tag plus a parent "All Words" deck.
Uses display_headword() for clean learner-facing headwords and
format_pitch_anki() for HTML pitch accent marking.

Usage:
  python scripts/anki_export.py                        # default export
  python scripts/anki_export.py --dry-run              # preview card counts
  python scripts/anki_export.py --deck animal           # single tag
  python scripts/anki_export.py --bb-only              # Blue Book entries only
  python scripts/anki_export.py --verbs-only           # verbs only
  python scripts/anki_export.py --advanced             # one card per sense
"""

import argparse
import hashlib
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import genanki

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from display_utils import (
    MORPH_CLASS_NOTES,
    display_headword,
    gram_class_label,
    morph_class_note,
)


# ── Constants ────────────────────────────────────────────────────

VERB_CLASSES = {"VT", "VI", "VD", "VP", "VL", "VR"}

DEFAULT_CONFIDENCE = 0.75

# Stable model ID (must not change across exports or Anki loses card history)
MODEL_ID = 1607392319

MODEL_CSS = """\
.card { font-family: Arial, sans-serif; font-size: 18px; text-align: center; }
.skiri { font-size: 24px; font-weight: bold; color: #1a5276; }
.pronunciation { font-size: 14px; color: #555; margin-top: 4px; }
.grammar { font-size: 12px; color: #888; font-style: italic; }
.example { border-left: 3px solid #aed6f1; padding-left: 8px;
           font-size: 14px; margin-top: 12px; text-align: left; }
.note { font-size: 12px; color: #b7950b; margin-top: 8px; }
b u { text-decoration: underline; }
"""

FRONT_TEMPLATE = """\
<div class="skiri">{{skiri}}</div>
<div class="pronunciation">{{pronunciation}}</div>
<div class="grammar">{{grammar_class}}</div>
"""

BACK_TEMPLATE = """\
{{FrontSide}}
<hr id="answer">
<div style="font-size: 20px;">{{english}}</div>
{{#grammar_note}}<div class="note">{{grammar_note}}</div>{{/grammar_note}}
{{#class_note}}<div class="note">{{class_note}}</div>{{/class_note}}
{{#verb_form}}<div style="margin-top: 8px;"><i>{{verb_form_label}}</i> <b>{{verb_form}}</b></div>{{/verb_form}}
{{#example_skiri}}
<div class="example">
  <div lang="x-paw">{{example_skiri}}</div>
  <div>{{example_english}}</div>
</div>
{{/example_skiri}}
{{#pitch_note}}<div class="note">{{pitch_note}}</div>{{/pitch_note}}
{{#source_note}}<div class="note" style="color: #888;">{{source_note}}</div>{{/source_note}}
"""

ANKI_MODEL = genanki.Model(
    MODEL_ID,
    "Skiri Pawnee Dictionary",
    fields=[
        {"name": "entry_id"},
        {"name": "skiri"},
        {"name": "pronunciation"},
        {"name": "english"},
        {"name": "grammar_class"},
        {"name": "grammar_note"},
        {"name": "class_note"},
        {"name": "example_skiri"},
        {"name": "example_english"},
        {"name": "verb_form"},
        {"name": "verb_form_label"},
        {"name": "pitch_note"},
        {"name": "source_note"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": FRONT_TEMPLATE,
            "afmt": BACK_TEMPLATE,
        }
    ],
    css=MODEL_CSS,
)


# ── Query ────────────────────────────────────────────────────────

MAIN_QUERY = """\
SELECT
    le.entry_id,
    le.headword,
    le.normalized_form,
    le.grammatical_class,
    le.verb_class,
    le.phonetic_form,
    le.simplified_pronunciation,
    le.form2_confidence,
    le.blue_book_attested,
    le.source,
    (SELECT definition FROM glosses
     WHERE entry_id = le.entry_id AND sense_number = 1) AS gloss_1,
    (SELECT COUNT(*) FROM glosses WHERE entry_id = le.entry_id) AS sense_count,
    (SELECT skiri_form FROM paradigmatic_forms
     WHERE entry_id = le.entry_id AND form_number = 2) AS form_2,
    (SELECT skiri_text FROM examples e
     WHERE e.entry_id = le.entry_id
     ORDER BY
       CASE WHEN e.source = 'blue_book' THEN 0 ELSE 1 END,
       e.id
     LIMIT 1) AS example_skiri,
    (SELECT english_translation FROM examples e
     WHERE e.entry_id = le.entry_id
     ORDER BY
       CASE WHEN e.source = 'blue_book' THEN 0 ELSE 1 END,
       e.id
     LIMIT 1) AS example_english,
    (SELECT GROUP_CONCAT(tag, ',') FROM semantic_tags
     WHERE entry_id = le.entry_id) AS tags
FROM lexical_entries le
WHERE le.headword != 'Ø'
ORDER BY le.headword
"""

# For --advanced mode: all senses per entry
ALL_GLOSSES_QUERY = """\
SELECT entry_id, sense_number, definition
FROM glosses
ORDER BY entry_id, sense_number
"""


# ── Helper functions ─────────────────────────────────────────────

def log(msg):
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))


_UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']*)")


def format_pitch_anki(simplified):
    """Port of web app format_pitch for Anki HTML output.

    Returns (html_str, pitch_unmarked: bool).
    """
    if not simplified:
        return "", True
    has_upper = any(c.isupper() for c in simplified if c.isalpha())
    if has_upper:
        result = _UPPER_RUN_RE.sub(
            lambda m: f"<b><u>{m.group(1).lower()}</u></b>", simplified
        )
        return result, False
    return simplified, True


def build_english_field(gloss_1, sense_count):
    """Option A: primary sense + note for multi-sense entries."""
    if not gloss_1:
        return ""
    if sense_count > 1:
        return f"{gloss_1.rstrip('.')} <i>(+{sense_count - 1} more senses)</i>"
    return gloss_1


def build_verb_form(form_2, confidence, gloss_1, gram_class, min_conf):
    """Build verb form field and label for card back."""
    if not gram_class:
        return "", ""
    # Extract primary class (handle compound like "VI, VT")
    primary = re.sub(r"\(\d+\)", "", gram_class).split(",")[0].strip()
    if primary not in VERB_CLASSES:
        return "", ""
    if not form_2 or not confidence or confidence < min_conf:
        return "", ""
    verb = gloss_1.split(";")[0].split(",")[0].rstrip(".").strip().lower() if gloss_1 else "..."
    label = f"he/she {verb}:"
    return form_2, label


def build_source_note(blue_book_attested, source):
    """Build source attestation note."""
    parts = []
    if source == "blue_book" or blue_book_attested:
        parts.append("Blue Book")
    parts.append("Parks Dictionary")
    return "Attested: " + " + ".join(parts)


def stable_deck_id(name):
    """Generate a stable integer deck ID from a name string."""
    h = hashlib.md5(name.encode()).hexdigest()
    return int(h[:8], 16)


def stable_note_guid(entry_id, sense_num=None):
    """Generate a stable GUID for a note (for Anki dedup across imports)."""
    key = entry_id if sense_num is None else f"{entry_id}::sense{sense_num}"
    return genanki.guid_for(key)


# ── Card building ────────────────────────────────────────────────

def build_note(row, min_conf, sense_num=None, sense_def=None):
    """Build a genanki.Note from a query row.

    If sense_num is given, this is an --advanced per-sense card.
    """
    (entry_id, headword, normalized_form, gram_class, verb_class,
     phonetic_form, simplified_pron, form2_conf, bb_attested, source,
     gloss_1, sense_count, form_2, ex_skiri, ex_english, tags) = row

    # Display headword
    disp, grammar_note = display_headword(headword, normalized_form)
    if not disp:
        return None

    # Pronunciation with pitch marking
    pron_html, pitch_unmarked = format_pitch_anki(simplified_pron)

    # English field
    if sense_num is not None:
        english = sense_def or ""
    else:
        english = build_english_field(gloss_1, sense_count)

    if not english:
        return None

    # Grammar
    class_label = gram_class_label(gram_class) if gram_class else ""
    class_note = morph_class_note(gram_class) or ""

    # Verb form
    verb_form, verb_label = build_verb_form(
        form_2, form2_conf, gloss_1, gram_class, min_conf
    )

    # Pitch note
    pitch_note = "Pitch accent not marked for this entry in Parks Dictionary." if pitch_unmarked else ""

    # Source
    source_note = build_source_note(bb_attested, source)

    guid = stable_note_guid(entry_id, sense_num)

    note = genanki.Note(
        model=ANKI_MODEL,
        fields=[
            entry_id,
            disp,
            pron_html,
            english,
            class_label,
            grammar_note or "",
            class_note,
            ex_skiri or "",
            ex_english or "",
            verb_form,
            verb_label,
            pitch_note,
            source_note,
        ],
        guid=guid,
    )
    return note


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Export Skiri Pawnee dictionary to Anki .apkg"
    )
    parser.add_argument("--output", help="Output .apkg path (default: exports/skiri_pawnee_YYYYMMDD.apkg)")
    parser.add_argument("--deck", help="Export single semantic tag only (e.g. 'animal')")
    parser.add_argument("--advanced", action="store_true", help="One card per sense (Option B)")
    parser.add_argument("--verbs-only", action="store_true", help="Export verb entries only")
    parser.add_argument("--bb-only", action="store_true", help="Export Blue Book-attested entries only")
    parser.add_argument("--min-confidence", type=float, default=DEFAULT_CONFIDENCE,
                        help=f"Confidence threshold for verb form display (default: {DEFAULT_CONFIDENCE})")
    parser.add_argument("--dry-run", action="store_true", help="Print card counts, no file written")
    parser.add_argument("--db", default="skiri_pawnee.db", help="Path to SQLite database")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        log(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    # Output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path("exports") / f"skiri_pawnee_{datetime.now():%Y%m%d}.apkg"

    conn = sqlite3.connect(str(db_path))

    # Fetch all rows
    rows = conn.execute(MAIN_QUERY).fetchall()
    log(f"Fetched {len(rows)} entries from database")

    # Pre-fetch all glosses for --advanced mode
    all_glosses = {}
    if args.advanced:
        for eid, snum, defn in conn.execute(ALL_GLOSSES_QUERY).fetchall():
            all_glosses.setdefault(eid, []).append((snum, defn))

    conn.close()

    # Filter rows
    if args.bb_only:
        rows = [r for r in rows if r[8] or r[9] == "blue_book"]  # bb_attested or source
        log(f"  After --bb-only filter: {len(rows)}")

    if args.verbs_only:
        rows = [r for r in rows if r[3] and any(
            vc in re.sub(r"\(\d+\)", "", r[3]).split(",")[0].strip()
            for vc in VERB_CLASSES
        )]
        log(f"  After --verbs-only filter: {len(rows)}")

    if args.deck:
        rows = [r for r in rows if r[15] and args.deck in r[15].split(",")]
        log(f"  After --deck '{args.deck}' filter: {len(rows)}")

    # Build notes and assign to decks
    parent_name = "Skiri Pawnee"
    all_deck_name = f"{parent_name}::All Words"
    all_deck = genanki.Deck(stable_deck_id(all_deck_name), all_deck_name)

    # Per-tag decks
    tag_decks = {}
    deck_counts = {}

    skipped = 0
    total_notes = 0

    for row in rows:
        entry_id = row[0]
        tags_str = row[15]
        entry_tags = tags_str.split(",") if tags_str else []

        if args.advanced and entry_id in all_glosses:
            # One card per sense
            for sense_num, sense_def in all_glosses[entry_id]:
                note = build_note(row, args.min_confidence, sense_num, sense_def)
                if note is None:
                    skipped += 1
                    continue
                all_deck.add_note(note)
                total_notes += 1
                for tag in entry_tags:
                    if tag not in tag_decks:
                        deck_name = f"{parent_name}::{tag.title()}"
                        tag_decks[tag] = genanki.Deck(stable_deck_id(deck_name), deck_name)
                        deck_counts[tag] = 0
                    tag_decks[tag].add_note(note)
                    deck_counts[tag] += 1
        else:
            # Standard: one card per entry (Option A)
            note = build_note(row, args.min_confidence)
            if note is None:
                skipped += 1
                continue
            all_deck.add_note(note)
            total_notes += 1
            for tag in entry_tags:
                if tag not in tag_decks:
                    deck_name = f"{parent_name}::{tag.title()}"
                    tag_decks[tag] = genanki.Deck(stable_deck_id(deck_name), deck_name)
                    deck_counts[tag] = 0
                tag_decks[tag].add_note(note)
                deck_counts[tag] += 1

    # Summary
    log(f"\n--- Summary ---")
    log(f"Total cards: {total_notes}")
    log(f"Skipped (empty display/gloss): {skipped}")
    log(f"All Words deck: {len(all_deck.notes)}")
    log(f"Tag decks ({len(tag_decks)}):")
    for tag in sorted(deck_counts, key=lambda t: -deck_counts[t]):
        log(f"  {tag:15s} {deck_counts[tag]:5d} cards")

    if args.dry_run:
        log("\nDry run — no file written.")
        return

    # Write .apkg
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package([all_deck] + list(tag_decks.values()))
    package.write_to_file(str(out_path))
    log(f"\nExported to: {out_path}")
    log(f"File size: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
