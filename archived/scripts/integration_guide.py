"""
Phase 3.1.5 — Integration Guide
=================================

This file shows how to wire the possession engine, example filter,
and updated widget into your Flask app. Copy the relevant pieces
into your app.py or equivalent.

Files to deploy:
    possession_engine.py     → same directory as your app (or on PYTHONPATH)
    api_possession.py        → same directory as your app
    example_filter.py        → same directory as your app
    _possession_widget.html  → your templates/ directory (replaces existing)
"""

# ─── 1. App startup: build the headword set once ─────────────────────────

import json
from example_filter import build_headword_set

def load_headword_set():
    """
    Build the headword set from your S2E dictionary.
    Call this ONCE at app startup and cache the result.
    """
    with open("extracted_data/skiri_to_english_respelled.json", "r", encoding="utf-8") as f:
        s2e_entries = json.load(f)
    return build_headword_set(s2e_entries)

# At app init:
# HEADWORD_SET = load_headword_set()


# ─── 2. Register the possession API blueprint ────────────────────────────

from flask import Flask
from api_possession import possession_bp

app = Flask(__name__)
app.register_blueprint(possession_bp)

# The widget fetches: GET /api/possession/<headword>
# Returns JSON consumed by _possession_widget.html


# ─── 3. Filter examples before rendering ─────────────────────────────────

from example_filter import filter_examples, filter_blue_book_refs
from possession_engine import extract_noun_stem

def get_filtered_examples(entry, headword_set):
    """
    Filter an entry's examples and Blue Book references to remove
    false substring matches.

    Call this in your entry-detail route before passing to the template.
    """
    headword = entry.get("headword", "")
    stem, _ = extract_noun_stem(headword)

    # Filter dictionary examples (from part_II.examples)
    raw_examples = entry.get("part_II", {}).get("examples", [])
    filtered_examples = filter_examples(
        headword,
        raw_examples,
        headword_set,
        stem=stem,
        text_key="skiri_text",   # adjust to match your example dict keys
    )

    return filtered_examples


def get_filtered_bb_refs(entry, bb_refs, headword_set):
    """
    Filter Blue Book cross-references for a headword.
    """
    headword = entry.get("headword", "")
    stem, _ = extract_noun_stem(headword)

    return filter_blue_book_refs(
        headword,
        bb_refs,
        headword_set,
        stem=stem,
    )


# ─── 4. Example: updated entry-detail route ──────────────────────────────

# HEADWORD_SET = load_headword_set()  # at startup

# @app.route('/entry/<headword>')
# def entry_detail(headword):
#     entry = lookup_entry(headword)  # your existing lookup
#     bb_refs = lookup_bb_refs(headword)  # your existing BB lookup
#
#     # FILTER before rendering (the new part)
#     entry_examples = get_filtered_examples(entry, HEADWORD_SET)
#     bb_refs_filtered = get_filtered_bb_refs(entry, bb_refs, HEADWORD_SET)
#
#     return render_template(
#         'entry_detail.html',
#         entry=entry,
#         examples=entry_examples,        # was: entry.part_II.examples
#         bb_refs=bb_refs_filtered,        # was: bb_refs (unfiltered)
#     )


# ─── 5. Possession API: noun_class lookup stub ───────────────────────────

# api_possession.py includes a _lookup_noun_class() stub that guesses
# the grammatical class from the engine's known stem lists. Replace it
# with a real DB query once Phase 1.2 (database schema) is done:
#
#     def _lookup_noun_class(headword: str) -> str:
#         row = db.execute(
#             "SELECT grammatical_class FROM lexical_entries WHERE headword = ?",
#             (headword,)
#         ).fetchone()
#         return row[0] if row else "N"


# ─── 6. Template: _possession_widget.html ────────────────────────────────
#
# The updated widget is a drop-in replacement. Changes:
#
#   OLD: morpheme breakdown as plain string "ti(IND.3) + ri(PHY.POSS) + ..."
#   NEW: color-coded chips from morpheme_chips[] array, with role-based CSS
#
#   OLD: no case forms
#   NEW: locative/instrumental panel from locative_forms[] in API response
#
#   OLD: dots for confidence (●●○)
#   NEW: labeled badges (✓ ATTESTED / ●●● COMPUTED / ●○○ LOW CONF.)
#
#   Backward compatible: falls back to plain string if morpheme_chips
#   is absent (e.g., if API returns old-format data).
#
# CSS variables used (provide in your site stylesheet):
#   --earth-*   (50, 100, 200, 300, 500, 700, 800)
#   --sage-*    (100, 300, 600, 700, 800)
#   --sand-*    (100, 300, 700, 800)
#   --sky-*     (100, 300, 800)
#   --plum-*    (100, 300, 800)
#   --clay-*    (100, 300, 600, 700, 800)
#   --stone-*   (100, 300, 800)
#   --font-mono
#
# All have safe hex fallbacks in the widget CSS, so it works even without
# the variables defined.


if __name__ == "__main__":
    print("This is an integration guide, not a runnable script.")
    print("Copy the relevant pieces into your Flask app.")
    print()
    print("Files to deploy:")
    print("  possession_engine.py     → app directory")
    print("  api_possession.py        → app directory")
    print("  example_filter.py        → app directory")
    print("  _possession_widget.html  → templates/")
