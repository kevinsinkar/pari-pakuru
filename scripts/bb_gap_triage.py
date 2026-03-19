#!/usr/bin/env python3
"""
Blue Book 518-Gap Triage
========================
Sends unmatched Blue Book vocabulary items to Gemini for classification,
then stores results in the DB and generates a report.

Categories:
  inflected_verb   — Verb with prefix (ti-, tiku-, etc.) whose root may be in Parks
  loanword         — English borrowing (paisits = nickel, etc.)
  function_word    — Particle, demonstrative, conjunction, interjection
  phrase           — Multi-word expression or full sentence
  possessed_form   — Noun with possessive prefix (irari' = my brother)
  noun_unlisted    — Standalone noun not in Parks dictionary
  descriptor       — Color term, stative predicate (ti pahaat = it's red)
  dialectal_variant— Same word, different orthography/pronunciation
  ocr_artifact     — Extraction error, garbled text, duplicate
  unknown          — Cannot confidently classify

Usage:
    python scripts/bb_gap_triage.py --db skiri_pawnee.db \
        --report reports/bb_gap_triage.txt

    # Dry run (no DB writes):
    python scripts/bb_gap_triage.py --db skiri_pawnee.db --dry-run

    # Resume from checkpoint:
    python scripts/bb_gap_triage.py --db skiri_pawnee.db \
        --checkpoint bb_gap_triage_checkpoint.json
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 4
BATCH_SIZE = 50  # items per Gemini call

VALID_CATEGORIES = {
    "inflected_verb", "loanword", "function_word", "phrase",
    "possessed_form", "noun_unlisted", "descriptor",
    "dialectal_variant", "ocr_artifact", "unknown",
}

GEMINI_SYSTEM_INSTRUCTION = """\
You are a computational linguist classifying unmatched Pawnee vocabulary items \
from "Pari Pakuru'" (a 1979 Skiri Pawnee textbook) that did not match against \
the Parks linguistic dictionary.

For each item, assign exactly ONE category from this list:

  inflected_verb    — A verb with morphological prefixes/suffixes (ti-, tiku-, \
tuku-, suks-, stiks-, siks-, we-, tat-, tas-, sitat-, sitas-, siti-, ri-, ra-, \
a-, i-, ku-, etc.). The bare root may exist in Parks but this inflected form \
does not match. Include negated verbs (kaaki-), imperatives, and subordinate forms.

  loanword          — An English borrowing adapted into Pawnee phonology. \
Common patterns: money terms (paisits, terisits, tupits), days of week, \
proper nouns from English.

  function_word     — A short grammatical particle, demonstrative, conjunction, \
interjection, or discourse marker. Examples: ti' (copula "this is"), nawa \
(hello/now), had (yes), ka (what), hawa (and/but), rawe (some/one), tii (this).

  phrase            — A multi-word expression, full sentence from dialogue, \
or compound phrase. Contains spaces or link dots (•) separating multiple words.

  possessed_form    — A noun with a possessive prefix (i-/ir-/it-/is-/a-/at- \
etc.) or kin term in possessed form. Examples: irari' (my brother), itahri' \
(my sister), ispahat (his eye).

  noun_unlisted     — A standalone, uninflected noun (no verb prefixes, no \
possessive markers) that simply isn't in the Parks dictionary. May be a \
cultural term, food item, animal, place name, etc.

  descriptor        — A stative/descriptive predicate, often with copula ti, \
describing a quality or state. Examples: ti pahaat (it's red), ti tareus \
(it's blue), ti takaa (it's white).

  dialectal_variant — The word exists in Parks but with different spelling, \
vowel length, glottal placement, or affricate notation. The meaning is the \
same but the orthographic form differs enough to prevent matching.

  ocr_artifact      — Garbled text, extraction error, truncated form, or \
duplicate of another entry that is clearly not a real vocabulary item.

  unknown           — Cannot confidently classify from the available information.

IMPORTANT RULES:
1. If the form contains spaces or link dots (•), it is almost certainly \
"phrase" unless it's clearly a descriptor pattern (ti + adjective).
2. "ti + WORD" patterns are usually "descriptor" (copular predicate).
3. Single words with verb prefixes (ti-, tiku-, suks-, etc.) are "inflected_verb".
4. Short words (1-3 characters) without clear verb morphology are likely \
"function_word".
5. Words with possessive prefixes (ir-, it-, is-, at-) are "possessed_form" \
if they're nouns.
6. English-sounding words adapted to Pawnee phonology are "loanword".

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "classifications": [
    {
      "skiri_form": "exact form as given",
      "category": "one of the valid categories",
      "confidence": 0.0 to 1.0,
      "notes": "brief reasoning (1 sentence max)"
    }
  ]
}

Respond with ONLY the JSON. No preamble, no markdown fences.
"""


# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------

def _call_gemini(client, prompt_text):
    """Send classification request to Gemini with retry logic."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt_text],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=16384,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            # Strip markdown fences if present despite response_mime_type
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            return json.loads(text)

        except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests) as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s: {e}")
            time.sleep(wait)
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
        except Exception as e:
            log.error(f"Gemini error (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                time.sleep(wait)

    log.error("All Gemini retries exhausted")
    return None


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

def load_gaps(db_path):
    """Load unique gap entries from blue_book_attestations."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT DISTINCT bb_skiri_form, bb_english, context_type, lesson_number
        FROM blue_book_attestations
        WHERE match_type = 'none'
        ORDER BY lesson_number, bb_skiri_form
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_triage_table(conn):
    """Create bb_gap_triage table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bb_gap_triage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bb_skiri_form TEXT NOT NULL,
            bb_english TEXT,
            context_type TEXT,
            lesson_number INTEGER,
            category TEXT NOT NULL,
            confidence REAL,
            notes TEXT,
            triaged_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gap_triage_cat ON bb_gap_triage(category)")
    conn.commit()


def insert_triage_results(conn, results, timestamp):
    """Insert classification results into bb_gap_triage."""
    conn.executemany("""
        INSERT INTO bb_gap_triage (bb_skiri_form, bb_english, context_type,
                                   lesson_number, category, confidence, notes, triaged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (r["bb_skiri_form"], r.get("bb_english"), r.get("context_type"),
         r.get("lesson_number"), r["category"], r.get("confidence"),
         r.get("notes"), timestamp)
        for r in results
    ])
    conn.commit()


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

def build_batch_prompt(items):
    """Build a prompt listing items for Gemini to classify."""
    lines = ["Classify each of the following Pawnee vocabulary items:\n"]
    for i, item in enumerate(items, 1):
        english = item.get("bb_english", "?")
        ctx = item.get("context_type", "?")
        lesson = item.get("lesson_number", "?")
        lines.append(f'{i}. "{item["bb_skiri_form"]}" = \'{english}\' [{ctx}, L{lesson}]')
    return "\n".join(lines)


def classify_batch(client, items):
    """Send a batch to Gemini, return list of classification dicts."""
    prompt = build_batch_prompt(items)
    result = _call_gemini(client, prompt)

    if not result or "classifications" not in result:
        log.error("No valid classifications returned")
        return None

    classifications = result["classifications"]

    # Merge Gemini output back with original item metadata
    merged = []
    form_to_item = {}
    for item in items:
        form_to_item[item["bb_skiri_form"]] = item

    for cls in classifications:
        form = cls.get("skiri_form", "")
        category = cls.get("category", "unknown")
        if category not in VALID_CATEGORIES:
            log.warning(f"Invalid category '{category}' for '{form}', defaulting to 'unknown'")
            category = "unknown"

        # Find matching original item
        orig = form_to_item.get(form)
        if not orig:
            # Try fuzzy match (Gemini may slightly alter the form)
            for key in form_to_item:
                if key.strip().lower() == form.strip().lower():
                    orig = form_to_item[key]
                    break
            if not orig:
                log.warning(f"Could not match Gemini output '{form}' to any input item")
                continue

        merged.append({
            "bb_skiri_form": orig["bb_skiri_form"],
            "bb_english": orig.get("bb_english"),
            "context_type": orig.get("context_type"),
            "lesson_number": orig.get("lesson_number"),
            "category": category,
            "confidence": cls.get("confidence", 0.5),
            "notes": cls.get("notes", ""),
        })

    return merged


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def load_checkpoint(path):
    """Load checkpoint: set of already-classified forms."""
    if path and Path(path).exists():
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return set(data.get("classified_forms", []))
    return set()


def save_checkpoint(path, classified_forms):
    """Save checkpoint."""
    if path:
        Path(path).write_text(
            json.dumps({"classified_forms": sorted(classified_forms)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(report_path, all_results, gaps_total, timestamp):
    """Write triage report."""
    lines = [
        "=" * 70,
        "BLUE BOOK GAP TRIAGE REPORT",
        f"Generated: {timestamp}",
        "=" * 70,
        "",
        "SUMMARY",
        "-" * 40,
        f"Total gap entries (with duplicates):    {gaps_total}",
        f"Unique forms classified:                {len(all_results)}",
        "",
    ]

    # Category counts
    cat_counts = {}
    for r in all_results:
        cat = r["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    lines.append("CATEGORY BREAKDOWN")
    lines.append("-" * 40)
    for cat in sorted(cat_counts, key=cat_counts.get, reverse=True):
        pct = 100 * cat_counts[cat] / len(all_results) if all_results else 0
        lines.append(f"  {cat:25s} {cat_counts[cat]:4d}  ({pct:5.1f}%)")
    lines.append("")

    # By lesson
    lesson_cats = {}
    for r in all_results:
        ln = r.get("lesson_number", 0)
        cat = r["category"]
        if ln not in lesson_cats:
            lesson_cats[ln] = {}
        lesson_cats[ln][cat] = lesson_cats[ln].get(cat, 0) + 1

    lines.append("BY LESSON")
    lines.append("-" * 40)
    for ln in sorted(lesson_cats):
        total = sum(lesson_cats[ln].values())
        top_cats = sorted(lesson_cats[ln].items(), key=lambda x: -x[1])[:3]
        top_str = ", ".join(f"{c}:{n}" for c, n in top_cats)
        lines.append(f"  Lesson {ln:2d}: {total:3d} gaps  ({top_str})")
    lines.append("")

    # Detailed listing by category
    lines.append("DETAILED LISTINGS BY CATEGORY")
    lines.append("-" * 40)
    for cat in sorted(cat_counts, key=cat_counts.get, reverse=True):
        items = [r for r in all_results if r["category"] == cat]
        lines.append(f"\n--- {cat.upper()} ({len(items)}) ---")
        for item in sorted(items, key=lambda x: (x.get("lesson_number", 0), x["bb_skiri_form"])):
            eng = item.get("bb_english", "?")
            ln = item.get("lesson_number", "?")
            conf = item.get("confidence", 0)
            note = item.get("notes", "")
            lines.append(f'  L{str(ln):>2s} "{item["bb_skiri_form"]}"  = \'{eng}\'  [{conf:.1f}] {note}')
    lines.append("")

    # High-value items (nouns, function words, loanwords — things to potentially add to DB)
    high_value_cats = {"noun_unlisted", "function_word", "loanword"}
    high_value = [r for r in all_results if r["category"] in high_value_cats]
    lines.append("HIGH-VALUE ITEMS FOR POTENTIAL DB ADDITION")
    lines.append("-" * 40)
    lines.append(f"Total: {len(high_value)} items (nouns, function words, loanwords)")
    for item in sorted(high_value, key=lambda x: (x["category"], x["bb_skiri_form"])):
        eng = item.get("bb_english", "?")
        lines.append(f'  [{item["category"]:15s}] "{item["bb_skiri_form"]}" = \'{eng}\'')
    lines.append("")

    report_text = "\n".join(lines)

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(report_text, encoding="utf-8")
    log.info(f"Report written to {report_path}")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Blue Book gap triage via Gemini")
    parser.add_argument("--db", default="skiri_pawnee.db", help="Path to SQLite database")
    parser.add_argument("--report", default="reports/bb_gap_triage.txt", help="Report output path")
    parser.add_argument("--checkpoint", default="bb_gap_triage_checkpoint.json", help="Checkpoint file")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB writes")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Items per Gemini call")
    args = parser.parse_args()

    # Load gaps
    gaps = load_gaps(args.db)
    log.info(f"Loaded {len(gaps)} unique gap entries from DB")

    if not gaps:
        log.info("No gaps to classify. Exiting.")
        return

    # Load checkpoint
    already_done = load_checkpoint(args.checkpoint)
    remaining = [g for g in gaps if g["bb_skiri_form"] not in already_done]
    log.info(f"Already classified: {len(already_done)}, remaining: {len(remaining)}")

    if not remaining:
        log.info("All gaps already classified. Generating report from checkpoint.")
        # Re-run report from DB
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM bb_gap_triage").fetchall()
        all_results = [dict(r) for r in rows]
        conn.close()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_report(args.report, all_results, len(gaps), timestamp)
        return

    # Init Gemini
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    client = genai.Client(api_key=api_key)

    # Init DB
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None
    if not args.dry_run:
        conn = sqlite3.connect(args.db)
        create_triage_table(conn)

    all_results = []

    # If resuming, load previous results from DB
    if already_done and conn:
        conn.row_factory = sqlite3.Row
        prev = conn.execute("SELECT * FROM bb_gap_triage").fetchall()
        all_results = [dict(r) for r in prev]
        conn.row_factory = None
        log.info(f"Loaded {len(all_results)} previous results from DB")

    # Process in batches
    batches = [remaining[i:i + args.batch_size] for i in range(0, len(remaining), args.batch_size)]
    log.info(f"Processing {len(remaining)} items in {len(batches)} batches of ~{args.batch_size}")

    for batch_idx, batch in enumerate(batches, 1):
        log.info(f"Batch {batch_idx}/{len(batches)} ({len(batch)} items)...")

        results = classify_batch(client, batch)

        if results is None:
            log.error(f"Batch {batch_idx} failed completely, skipping")
            continue

        log.info(f"  -> classified {len(results)} items")

        # Category summary for this batch
        batch_cats = {}
        for r in results:
            batch_cats[r["category"]] = batch_cats.get(r["category"], 0) + 1
        cat_str = ", ".join(f"{c}:{n}" for c, n in sorted(batch_cats.items(), key=lambda x: -x[1]))
        log.info(f"  -> {cat_str}")

        all_results.extend(results)

        # Save to DB
        if conn and not args.dry_run:
            insert_triage_results(conn, results, timestamp)

        # Update checkpoint
        for r in results:
            already_done.add(r["bb_skiri_form"])
        save_checkpoint(args.checkpoint, already_done)

        # Small delay between batches to be polite to API
        if batch_idx < len(batches):
            time.sleep(1)

    # Close DB
    if conn:
        conn.close()

    # Generate report
    total_gaps_with_dupes = len(load_gaps(args.db)) if not args.dry_run else len(gaps)
    report = write_report(args.report, all_results, total_gaps_with_dupes, timestamp)

    # Print summary to console
    cat_counts = {}
    for r in all_results:
        cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1

    sys.stdout.buffer.write("\n=== TRIAGE COMPLETE ===\n".encode("utf-8"))
    sys.stdout.buffer.write(f"Classified {len(all_results)} unique gap forms\n".encode("utf-8"))
    for cat in sorted(cat_counts, key=cat_counts.get, reverse=True):
        pct = 100 * cat_counts[cat] / len(all_results) if all_results else 0
        sys.stdout.buffer.write(f"  {cat:25s} {cat_counts[cat]:4d}  ({pct:.1f}%)\n".encode("utf-8"))


if __name__ == "__main__":
    main()
