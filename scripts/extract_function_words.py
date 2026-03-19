#!/usr/bin/env python3
"""
Extract function words from BB phrase gaps (Phase 3.1.6 second pass).
======================================================================
Sends the 196 BB phrases (category='phrase' in bb_gap_triage) to Gemini
to identify any function words embedded within them. Compares against the
existing function_words table and lexical_entries to find genuinely new
items, then inserts them into function_words.

Usage:
    python scripts/extract_function_words.py --db skiri_pawnee.db --dry-run
    python scripts/extract_function_words.py --db skiri_pawnee.db
    python scripts/extract_function_words.py --db skiri_pawnee.db \
        --checkpoint extract_fw_checkpoint.json
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
BATCH_SIZE = 40  # phrases per Gemini call

SYSTEM_INSTRUCTION = """\
You are a computational linguist analysing Skiri Pawnee sentences from the \
"Pari Pakuru'" textbook.  Each sentence is a Pawnee phrase with its English \
translation.

Your task: identify any SHORT FUNCTION WORDS (particles, demonstratives, \
conjunctions, interjections, discourse markers, adverbs, copulas, \
interrogatives, quantifiers, or locatives) that appear as SEPARATE WORDS \
within the Pawnee phrase.

Rules:
1. Only extract words that stand alone (separated by spaces or link dots \u2022) \
and are NOT inflected verbs (no ti-/tiku-/suks- prefixes).
2. Only extract words <= ~12 characters long. Long words are almost \
certainly verbs or nouns, not function words.
3. If a word is clearly a proper noun, number, or standalone noun, skip it.
4. Provide the Pawnee form exactly as written, the likely English gloss, \
and a grammatical subclass from this list: \
conjunction, demonstrative, pronoun, interrogative, interjection, \
adverb, copula, quantifier, locative, particle, negation, temporal, \
discourse_marker.

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "extracted": [
    {
      "pawnee_form": "the function word as written",
      "english_gloss": "brief English meaning",
      "subclass": "one of the subclasses above",
      "source_phrase": "the full phrase it came from",
      "confidence": 0.0 to 1.0
    }
  ]
}

If no function words are found in the batch, return {"extracted": []}.
Respond with ONLY the JSON. No preamble, no markdown fences.
"""


# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------

def _call_gemini(client, prompt_text):
    """Send extraction request to Gemini with retry logic."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt_text],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=16384,
                    response_mime_type="application/json",
                ),
            )
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)

        except (google_exceptions.ResourceExhausted,
                google_exceptions.TooManyRequests) as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning("Rate limited (attempt %d/%d), waiting %ds: %s",
                        attempt, MAX_RETRIES, wait, e)
            time.sleep(wait)
        except json.JSONDecodeError as e:
            log.warning("JSON parse error (attempt %d/%d): %s",
                        attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(2)
        except Exception as e:
            log.error("Gemini error (attempt %d/%d): %s",
                      attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                time.sleep(wait)

    log.error("All Gemini retries exhausted")
    return None


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_to_parks(form: str) -> str:
    """Normalize a BB word to Parks orthography for dedup."""
    s = form.strip().rstrip(".")
    s = s.replace("\u2022", "")
    s = s.replace("'", "\u0294").replace("\u2019", "\u0294").replace("\u02bc", "\u0294")
    s = re.sub(r"ts", "c", s, flags=re.IGNORECASE)
    s = s.lower().strip()
    s = re.sub(r"\s+", "", s)
    return s


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def load_checkpoint(path):
    if path and Path(path).exists():
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("processed_batches", 0), data.get("extracted", [])
    return 0, []


def save_checkpoint(path, processed_batches, extracted):
    if path:
        Path(path).write_text(
            json.dumps({
                "processed_batches": processed_batches,
                "extracted": extracted,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract function words from BB phrases via Gemini"
    )
    parser.add_argument("--db", default="skiri_pawnee.db")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show results without modifying the DB")
    parser.add_argument("--checkpoint", default="extract_fw_checkpoint.json")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--report", default="reports/extract_function_words.txt")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # ---- Load phrases ----
    phrases = conn.execute("""
        SELECT bb_skiri_form, bb_english
        FROM bb_gap_triage
        WHERE category = 'phrase'
        ORDER BY bb_skiri_form
    """).fetchall()
    log.info("Loaded %d phrases from bb_gap_triage", len(phrases))

    # ---- Load existing function words + headwords for dedup ----
    existing_fw = {
        r[0].lower()
        for r in conn.execute("SELECT headword FROM function_words")
    }
    existing_hw = {
        r[0].lower()
        for r in conn.execute("SELECT headword FROM lexical_entries")
    }
    known_words = existing_fw | existing_hw
    log.info("Known words for dedup: %d function_words + %d lexical_entries",
             len(existing_fw), len(existing_hw))

    # ---- Checkpoint ----
    done_batches, all_extracted = load_checkpoint(args.checkpoint)

    # ---- Init Gemini ----
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    client = genai.Client(api_key=api_key)

    # ---- Batch processing ----
    batches = [
        phrases[i:i + args.batch_size]
        for i in range(0, len(phrases), args.batch_size)
    ]
    log.info("Processing %d phrases in %d batches (resuming from batch %d)",
             len(phrases), len(batches), done_batches + 1)

    for batch_idx, batch in enumerate(batches):
        if batch_idx < done_batches:
            continue

        # Build prompt
        lines = [
            "Extract any function words from these Pawnee phrases:\n"
        ]
        for i, row in enumerate(batch, 1):
            lines.append(
                f'{i}. "{row["bb_skiri_form"]}" = \'{row["bb_english"]}\''
            )
        prompt = "\n".join(lines)

        log.info("Batch %d/%d (%d phrases)...",
                 batch_idx + 1, len(batches), len(batch))
        result = _call_gemini(client, prompt)

        if not result or "extracted" not in result:
            log.error("Batch %d failed, skipping", batch_idx + 1)
            continue

        items = result["extracted"]
        log.info("  -> %d function words extracted", len(items))
        all_extracted.extend(items)

        # Checkpoint
        save_checkpoint(args.checkpoint, batch_idx + 1, all_extracted)

        if batch_idx + 1 < len(batches):
            time.sleep(1)

    # ---- Deduplicate and filter ----
    log.info("Total raw extractions: %d", len(all_extracted))

    # Normalize and dedup
    seen = {}  # normalized -> best item
    for item in all_extracted:
        raw = item.get("pawnee_form", "")
        norm = normalize_to_parks(raw)
        if not norm or len(norm) > 15:
            continue
        conf = item.get("confidence", 0.5)
        if norm not in seen or conf > seen[norm].get("confidence", 0):
            seen[norm] = {
                "headword": norm,
                "pawnee_form_raw": raw,
                "english_gloss": item.get("english_gloss", ""),
                "subclass": item.get("subclass", "particle"),
                "source_phrase": item.get("source_phrase", ""),
                "confidence": conf,
            }

    log.info("Unique normalized forms: %d", len(seen))

    # Filter out already-known words
    new_items = {
        hw: it for hw, it in seen.items()
        if hw not in known_words
    }
    log.info("After dedup against known words: %d new", len(new_items))

    # ---- Report ----
    report_lines = [
        "=" * 70,
        "FUNCTION WORD EXTRACTION FROM BB PHRASES",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        f"Phrases analysed:          {len(phrases)}",
        f"Raw extractions:           {len(all_extracted)}",
        f"Unique normalized forms:   {len(seen)}",
        f"Already known (filtered):  {len(seen) - len(new_items)}",
        f"New function words:        {len(new_items)}",
        "",
        "NEW FUNCTION WORDS",
        "-" * 40,
    ]
    for hw in sorted(new_items):
        it = new_items[hw]
        report_lines.append(
            f"  {hw:20s}  {it['subclass']:18s}  "
            f"{it['english_gloss']:30s}  [{it['confidence']:.1f}]  "
            f"from: {it['source_phrase'][:50]}"
        )
    report_lines.append("")

    # Already-known items (for reference)
    already = {hw: it for hw, it in seen.items() if hw in known_words}
    if already:
        report_lines.append("ALREADY KNOWN (skipped)")
        report_lines.append("-" * 40)
        for hw in sorted(already):
            it = already[hw]
            report_lines.append(
                f"  {hw:20s}  {it['subclass']:18s}  {it['english_gloss']}"
            )
        report_lines.append("")

    report_text = "\n".join(report_lines)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report_text, encoding="utf-8")
    log.info("Report written to %s", args.report)

    # ---- Insert new items ----
    if new_items:
        subcls_to_class = {
            "conjunction": "CONJ", "demonstrative": "DEM",
            "pronoun": "PRON", "interrogative": "PRON",
            "interjection": "INTERJ", "adverb": "ADV",
            "copula": "PART", "quantifier": "QUAN",
            "locative": "LOC", "particle": "PART",
            "negation": "PART", "temporal": "ADV",
            "discourse_marker": "INTERJ",
        }

        if args.dry_run:
            sys.stdout.buffer.write(
                f"\n=== DRY RUN: {len(new_items)} new function words ===\n\n"
                .encode("utf-8")
            )
            for hw in sorted(new_items):
                it = new_items[hw]
                gram = subcls_to_class.get(it["subclass"], "PART")
                line = (
                    f"  {hw:20s}  {gram:6s}  {it['subclass']:18s}  "
                    f"{it['english_gloss']:30s}  [{it['confidence']:.1f}]\n"
                )
                sys.stdout.buffer.write(line.encode("utf-8"))
        else:
            cur = conn.cursor()
            inserted = 0
            for hw in sorted(new_items):
                it = new_items[hw]
                gram_class = subcls_to_class.get(it["subclass"], "PART")
                try:
                    cur.execute(
                        "INSERT INTO function_words "
                        "(headword, grammatical_class, subclass, "
                        " usage_notes, bb_attested, source) "
                        "VALUES (?, ?, ?, ?, 1, 'blue_book_phrase')",
                        (hw, gram_class, it["subclass"],
                         it["english_gloss"]),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    log.warning("Duplicate headword skipped: %s", hw)
            conn.commit()
            log.info("Inserted %d new function words", inserted)
    else:
        log.info("No new function words to insert")

    conn.close()

    # ---- Console summary ----
    sys.stdout.buffer.write(
        f"\n=== EXTRACTION COMPLETE ===\n"
        f"Phrases: {len(phrases)}, Raw extractions: {len(all_extracted)}, "
        f"Unique: {len(seen)}, New: {len(new_items)}\n".encode("utf-8")
    )


if __name__ == "__main__":
    main()
