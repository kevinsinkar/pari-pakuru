#!/usr/bin/env python3
"""
Phase 2.1 Follow-up — Gemini Semantic Tag Audit
=================================================
Batch-audits keyword-sourced semantic tags using Gemini to catch
polysemy false positives.

Problem: Keyword matching on English glosses produces false positives
from English polysemy:
  - "one" triggers `number` for "stamp one's foot"
  - "hide" triggers `animal` for "leather strap"  
  - "fly" triggers `animal` for "fly around"
  - "hand" triggers `body` for "hand over, give"

This script sends batches of (headword, gloss, tag) triples to Gemini
and asks: "Given this English definition, is the semantic tag correct?"

Usage:
    # Dry run — show what would be audited
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db --dry-run

    # Run audit (saves checkpoint for resume)
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db

    # Resume from checkpoint
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db --resume

    # Apply corrections (delete bad tags)
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db --apply

    # Audit specific tag only
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db --tag number

    # Generate report only (from checkpoint)
    python scripts/audit_semantic_tags.py --db skiri_pawnee.db --report-only

Dependencies: Python 3.8+, sqlite3, google-genai (GEMINI_API_KEY env var)
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
# Configuration
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"
BATCH_SIZE = 30          # entries per Gemini call
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 4
CHECKPOINT_FILE = "audit_tags_checkpoint.json"

# Tags to audit (keyword-sourced, known to have polysemy issues)
AUDIT_TAGS = [
    "number",    # worst offender — "one", "hand", "first" in glosses
    "animal",    # "hide", "fly", "stag", "horn" polysemy
    "body",      # "hand", "back", "head", "foot" as verbs
    "food",      # "water", "corn" in non-food contexts
    "plant",     # "wood", "tree", "bark" as materials/verbs
    "tool",      # "set", "cut", "strike" as general verbs
    "water",     # "float", "swim" metaphorical uses
    "color",     # "light", "dark" in non-color contexts
    "speech",    # "call", "tell", "say" in non-speech contexts
    "clothing",  # "wear", "cover" metaphorical uses
    "celestial", # "star", "moon", "day" in compound contexts
]

# Only audit keyword-sourced tags (gemini and gram_class are already clean)
AUDIT_SOURCES = ("keyword",)

# ---------------------------------------------------------------------------
# Gemini System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are auditing semantic category tags assigned to Skiri Pawnee dictionary entries.

Each entry has:
- A Skiri headword (you can ignore this — focus on the English definition)
- An English definition/gloss from the Parks Dictionary
- A semantic tag that was assigned by keyword matching on the English gloss

Your task: For each entry, judge whether the semantic tag CORRECTLY describes the MAIN MEANING of the word based on its English definition.

Rules:
- CORRECT: The tag matches the primary meaning. "bear" tagged `animal` = CORRECT.
- INCORRECT: The tag was triggered by a keyword that has a different sense in this context. "stamp one's foot" tagged `number` (triggered by "one") = INCORRECT.
- CORRECT even if secondary: If the word IS genuinely in that category even as a secondary meaning, mark CORRECT. "horse blanket" tagged `animal` = CORRECT (it's horse-related).
- INCORRECT for metaphorical/verb uses: "fly around (as a bird)" tagged `animal` = INCORRECT (it's a verb of motion, not an animal). "hand over" tagged `body` = INCORRECT (it's a transfer action).
- CORRECT for body-part actions ON body parts: "scratch one's head" tagged `body` = CORRECT.

Respond ONLY with a JSON array. Each element must have exactly these fields:
{"index": 0, "verdict": "correct", "reason": "brief explanation"}

verdict must be exactly "correct" or "incorrect" (lowercase).
index must match the input index (0-based).
Do NOT include any text outside the JSON array. No markdown, no backticks, no preamble."""

# ---------------------------------------------------------------------------
# Database Queries
# ---------------------------------------------------------------------------

def load_tags_to_audit(db_path, tag_filter=None):
    """Load all keyword-sourced tags that need auditing."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    source_placeholders = ",".join("?" for _ in AUDIT_SOURCES)

    if tag_filter:
        cur.execute(f"""
            SELECT st.rowid, st.entry_id, le.headword, g.definition, st.tag, st.confidence
            FROM semantic_tags st
            JOIN lexical_entries le ON st.entry_id = le.entry_id
            JOIN glosses g ON st.entry_id = g.entry_id AND g.sense_number = 1
            WHERE st.source IN ({source_placeholders})
              AND st.tag = ?
            ORDER BY st.tag, le.headword
        """, (*AUDIT_SOURCES, tag_filter))
    else:
        cur.execute(f"""
            SELECT st.rowid, st.entry_id, le.headword, g.definition, st.tag, st.confidence
            FROM semantic_tags st
            JOIN lexical_entries le ON st.entry_id = le.entry_id
            JOIN glosses g ON st.entry_id = g.entry_id AND g.sense_number = 1
            WHERE st.source IN ({source_placeholders})
              AND st.tag IN ({",".join("?" for _ in AUDIT_TAGS)})
            ORDER BY st.tag, le.headword
        """, (*AUDIT_SOURCES, *AUDIT_TAGS))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "rowid": r[0],
            "entry_id": r[1],
            "headword": r[2],
            "definition": r[3],
            "tag": r[4],
            "confidence": r[5],
        }
        for r in rows
    ]


def apply_corrections(db_path, results):
    """Delete tags marked as incorrect."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    incorrect = [r for r in results if r.get("verdict") == "incorrect"]
    if not incorrect:
        log.info("No incorrect tags to remove.")
        conn.close()
        return 0

    rowids = [r["rowid"] for r in incorrect]
    placeholders = ",".join("?" for _ in rowids)
    cur.execute(f"DELETE FROM semantic_tags WHERE rowid IN ({placeholders})", rowids)
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    log.info(f"Deleted {deleted} incorrect tags from semantic_tags")
    return deleted


# ---------------------------------------------------------------------------
# Checkpoint Management
# ---------------------------------------------------------------------------

def load_checkpoint(path):
    """Load audit checkpoint."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"audited": {}, "stats": {"correct": 0, "incorrect": 0, "errors": 0}}


def save_checkpoint(path, checkpoint):
    """Save audit checkpoint."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------

def _salvage_partial_json(text):
    """Try to recover a partial JSON array by finding the last complete object."""
    if not text or not text.strip().startswith("["):
        return None
    # Find last complete closing brace that ends an object in the array
    depth = 0
    last_valid = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '[' or ch == '{':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                last_valid = i + 1
        elif ch == '}':
            depth -= 1
            if depth == 1:  # back to array level
                last_valid = i + 1
    if last_valid > 2:
        # Close the array if needed
        fragment = text[:last_valid].rstrip().rstrip(',')
        if not fragment.endswith(']'):
            fragment += ']'
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            return None
    return None


def call_gemini(client, batch):
    """Send a batch of entries to Gemini for tag audit.
    
    Args:
        client: google.genai client
        batch: list of dicts with headword, definition, tag
        
    Returns:
        list of dicts with index, verdict, reason — or None on failure
    """
    from google.genai import types

    # Build the prompt
    lines = ["Audit the following semantic tags:\n"]
    for i, entry in enumerate(batch):
        defn = entry["definition"][:120]  # truncate long definitions
        lines.append(f'{i}. headword="{entry["headword"]}" definition="{defn}" tag="{entry["tag"]}"')

    prompt = "\n".join(lines)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            results = json.loads(text)

            # Validate structure
            if not isinstance(results, list):
                log.warning(f"Gemini returned non-list: {type(results)}")
                results = results.get("results", results.get("entries", []))

            # Validate each result
            valid = []
            for r in results:
                if isinstance(r, dict) and "index" in r and "verdict" in r:
                    v = r["verdict"].lower().strip()
                    if v in ("correct", "incorrect"):
                        r["verdict"] = v
                        valid.append(r)

            if len(valid) < len(batch) * 0.8:
                log.warning(f"Only {len(valid)}/{len(batch)} valid results, retrying...")
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                    continue

            return valid

        except json.JSONDecodeError as e:
            # Try to salvage partial JSON — find last complete object in array
            salvaged = _salvage_partial_json(text)
            if salvaged and len(salvaged) >= len(batch) * 0.5:
                log.info(f"Salvaged {len(salvaged)}/{len(batch)} from truncated JSON")
                valid = []
                for r in salvaged:
                    if isinstance(r, dict) and "index" in r and "verdict" in r:
                        v = r["verdict"].lower().strip()
                        if v in ("correct", "incorrect"):
                            r["verdict"] = v
                            valid.append(r)
                if valid:
                    return valid
            log.warning(f"JSON parse error (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)

        except Exception as e:
            ename = type(e).__name__
            if "ResourceExhausted" in ename or "TooManyRequests" in ename:
                wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                log.warning(f"Rate limited (attempt {attempt}), waiting {wait}s")
                time.sleep(wait)
            elif "ServiceUnavailable" in ename or "InternalServerError" in ename:
                wait = RETRY_BACKOFF_BASE * attempt
                log.warning(f"Server error (attempt {attempt}), waiting {wait}s")
                time.sleep(wait)
            else:
                log.error(f"Gemini error (attempt {attempt}): {ename}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE)

    return None


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(checkpoint, report_path="reports/audit_semantic_tags.txt"):
    """Generate human-readable audit report from checkpoint data."""
    audited = checkpoint.get("audited", {})
    stats = checkpoint.get("stats", {})

    # Aggregate by tag
    by_tag = {}
    incorrect_entries = []

    for rowid, result in audited.items():
        tag = result.get("tag", "?")
        verdict = result.get("verdict", "?")

        if tag not in by_tag:
            by_tag[tag] = {"correct": 0, "incorrect": 0, "total": 0}
        by_tag[tag]["total"] += 1
        if verdict == "correct":
            by_tag[tag]["correct"] += 1
        elif verdict == "incorrect":
            by_tag[tag]["incorrect"] += 1
            incorrect_entries.append(result)

    lines = []
    lines.append("=" * 70)
    lines.append("Semantic Tag Audit Report — Gemini-powered")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total audited:  {sum(t['total'] for t in by_tag.values())}")
    lines.append(f"Correct:        {sum(t['correct'] for t in by_tag.values())}")
    lines.append(f"Incorrect:      {sum(t['incorrect'] for t in by_tag.values())}")
    lines.append(f"API errors:     {stats.get('errors', 0)}")
    lines.append("")

    lines.append("BY TAG:")
    lines.append(f"  {'Tag':15s} {'Total':>6s} {'Correct':>8s} {'Incorrect':>10s} {'Error%':>7s}")
    lines.append("  " + "-" * 50)
    for tag in sorted(by_tag.keys()):
        t = by_tag[tag]
        err_pct = f"{100*t['incorrect']/t['total']:.1f}%" if t['total'] > 0 else "—"
        lines.append(f"  {tag:15s} {t['total']:>6d} {t['correct']:>8d} {t['incorrect']:>10d} {err_pct:>7s}")

    lines.append("")
    lines.append("INCORRECT TAGS (to be removed):")
    lines.append(f"  {'Headword':25s} {'Tag':12s} {'Reason':40s}")
    lines.append("  " + "-" * 80)
    for entry in sorted(incorrect_entries, key=lambda x: (x.get("tag", ""), x.get("headword", ""))):
        hw = entry.get("headword", "?")[:25]
        tag = entry.get("tag", "?")[:12]
        reason = entry.get("reason", "")[:40]
        lines.append(f"  {hw:25s} {tag:12s} {reason:40s}")

    report_text = "\n".join(lines)

    os.makedirs(os.path.dirname(report_path) if os.path.dirname(report_path) else ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    log.info(f"Report written to {report_path}")

    # Print summary to stdout (handle Windows cp1252 encoding)
    try:
        print(report_text[:2000])
    except UnicodeEncodeError:
        sys.stdout.buffer.write(report_text[:2000].encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')
    if len(report_text) > 2000:
        print(f"... ({len(incorrect_entries)} incorrect entries total -- see full report)")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 2.1 Follow-up: Gemini Semantic Tag Audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_semantic_tags.py --db skiri_pawnee.db --dry-run
  python scripts/audit_semantic_tags.py --db skiri_pawnee.db
  python scripts/audit_semantic_tags.py --db skiri_pawnee.db --tag number
  python scripts/audit_semantic_tags.py --db skiri_pawnee.db --apply
  python scripts/audit_semantic_tags.py --db skiri_pawnee.db --report-only
        """,
    )
    parser.add_argument("--db", required=True, help="Path to skiri_pawnee.db")
    parser.add_argument("--tag", help="Audit only this tag (e.g., 'number')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be audited without calling Gemini")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint (skip already-audited entries)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply corrections: delete tags marked incorrect")
    parser.add_argument("--report-only", action="store_true",
                        help="Generate report from existing checkpoint (no API calls)")
    parser.add_argument("--checkpoint", default=CHECKPOINT_FILE,
                        help=f"Checkpoint file path (default: {CHECKPOINT_FILE})")
    parser.add_argument("--report", default="reports/audit_semantic_tags.txt",
                        help="Report output path")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Entries per Gemini call (default: {BATCH_SIZE})")

    args = parser.parse_args()

    if not os.path.exists(args.db):
        log.error(f"Database not found: {args.db}")
        sys.exit(1)

    # --- Load tags to audit ---
    entries = load_tags_to_audit(args.db, tag_filter=args.tag)
    log.info(f"Found {len(entries)} keyword-sourced tags to audit"
             + (f" (tag={args.tag})" if args.tag else ""))

    if not entries:
        log.info("Nothing to audit.")
        return

    # --- Dry run ---
    if args.dry_run:
        by_tag = {}
        for e in entries:
            by_tag.setdefault(e["tag"], 0)
            by_tag[e["tag"]] += 1
        print(f"\nWould audit {len(entries)} tags:")
        for tag, ct in sorted(by_tag.items(), key=lambda x: -x[1]):
            print(f"  {tag:15s} {ct:5d}")
        print(f"\nBatches needed: {(len(entries) + args.batch_size - 1) // args.batch_size}")
        print(f"Estimated Gemini calls: {(len(entries) + args.batch_size - 1) // args.batch_size}")
        return

    # --- Report only ---
    if args.report_only:
        checkpoint = load_checkpoint(args.checkpoint)
        if not checkpoint.get("audited"):
            log.error("No checkpoint data found. Run audit first.")
            sys.exit(1)
        generate_report(checkpoint, args.report)
        return

    # --- Apply corrections ---
    if args.apply:
        checkpoint = load_checkpoint(args.checkpoint)
        if not checkpoint.get("audited"):
            log.error("No checkpoint data found. Run audit first.")
            sys.exit(1)

        incorrect = [
            {**v, "rowid": int(k)}
            for k, v in checkpoint["audited"].items()
            if v.get("verdict") == "incorrect"
        ]
        log.info(f"Found {len(incorrect)} incorrect tags to remove")

        if incorrect:
            deleted = apply_corrections(args.db, incorrect)
            print(f"\nDeleted {deleted} incorrect tags.")

            # Generate report
            generate_report(checkpoint, args.report)
        return

    # --- Run audit ---
    try:
        from google import genai
    except ImportError:
        log.error("google-genai not installed. Run: pip install google-genai")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set. Export it as an environment variable.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Load or create checkpoint
    checkpoint = load_checkpoint(args.checkpoint) if args.resume else {
        "audited": {}, "stats": {"correct": 0, "incorrect": 0, "errors": 0}
    }

    # Filter out already-audited entries
    already_done = set(checkpoint.get("audited", {}).keys())
    remaining = [e for e in entries if str(e["rowid"]) not in already_done]
    log.info(f"Remaining to audit: {len(remaining)} (skipping {len(entries) - len(remaining)} already done)")

    if not remaining:
        log.info("All entries already audited. Use --apply to apply corrections or --report-only for report.")
        generate_report(checkpoint, args.report)
        return

    # Process in batches
    total_batches = (len(remaining) + args.batch_size - 1) // args.batch_size
    processed = 0

    for batch_idx in range(0, len(remaining), args.batch_size):
        batch = remaining[batch_idx:batch_idx + args.batch_size]
        batch_num = batch_idx // args.batch_size + 1
        log.info(f"Batch {batch_num}/{total_batches}: {len(batch)} entries ({batch[0]['tag']}...)")

        results = call_gemini(client, batch)

        if results is None:
            log.error(f"Batch {batch_num} failed after {MAX_RETRIES} retries. Saving checkpoint.")
            checkpoint["stats"]["errors"] += len(batch)
            save_checkpoint(args.checkpoint, checkpoint)
            continue

        # Map results back to entries
        result_map = {r["index"]: r for r in results}

        for i, entry in enumerate(batch):
            r = result_map.get(i)
            if r:
                record = {
                    "rowid": entry["rowid"],
                    "entry_id": entry["entry_id"],
                    "headword": entry["headword"],
                    "tag": entry["tag"],
                    "definition": entry["definition"][:100],
                    "verdict": r["verdict"],
                    "reason": r.get("reason", ""),
                }
                checkpoint["audited"][str(entry["rowid"])] = record

                if r["verdict"] == "correct":
                    checkpoint["stats"]["correct"] += 1
                else:
                    checkpoint["stats"]["incorrect"] += 1
            else:
                checkpoint["stats"]["errors"] += 1

        processed += len(batch)
        save_checkpoint(args.checkpoint, checkpoint)
        log.info(f"  → {checkpoint['stats']['correct']} correct, "
                 f"{checkpoint['stats']['incorrect']} incorrect, "
                 f"{checkpoint['stats']['errors']} errors so far")

        # Brief pause between batches to avoid rate limits
        if batch_idx + args.batch_size < len(remaining):
            time.sleep(1)

    # Final report
    log.info(f"\nAudit complete: {processed} entries processed")
    generate_report(checkpoint, args.report)

    incorrect_count = checkpoint["stats"]["incorrect"]
    if incorrect_count > 0:
        print(f"\n{incorrect_count} incorrect tags found. Run with --apply to remove them.")


if __name__ == "__main__":
    main()
