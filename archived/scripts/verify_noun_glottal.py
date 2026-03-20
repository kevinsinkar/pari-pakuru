#!/usr/bin/env python3
"""
verify_noun_glottal.py — Gemini Agent for Noun Glottal Stop Verification
=========================================================================

Reads the audit flags JSON, extracts NOUN_MISSING_GLOTTAL entries,
loads their full entry data from S2E, and sends batches to Gemini
for verification against linguistic expectations.

Gemini classifies each entry as:
  - "ocr_miss"   → should end in ʔ, likely dropped by OCR
  - "legitimate"  → genuinely ends without ʔ (proper noun, loanword, etc.)
  - "uncertain"   → needs manual review against source PDF

Outputs:
  - Classification report with counts and entry lists
  - Recommended fixes JSON (entries Gemini says need ʔ added)

Usage:
  python scripts/verify_noun_glottal.py ^
      --s2e "Dictionary Data\\skiri_to_english_respelled.json" ^
      --flags reports\\flags_final.json ^
      --report reports\\noun_glottal_verification.txt ^
      --fixes reports\\noun_glottal_fixes.json ^
      --checkpoint reports\\glottal_checkpoint.json

Dependencies: Python 3.8+, google-genai
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5

SYSTEM_INSTRUCTION = """You are an expert in Skiri Pawnee (Caddoan) linguistics, specifically the Parks dictionary notation system.

You are reviewing noun entries that end in a bare vowel (no final glottal stop ʔ). In Parks' dictionary, most common nouns end in -ʔ (the nominal suffix -uʔ is typical). However, some nouns legitimately lack final ʔ:

LEGITIMATE bare vowel endings (classify as "legitimate"):
- Proper nouns: tribal names, place names, personal names, clan names (e.g., Ckirihki, Astarahi, Cawii)
- Kinship terms and dependent noun stems (N-KIN, N-DEP)
- Compound expressions or multi-word terms
- Loanwords from English
- Nouns that end in a consonant cluster where the final vowel is epenthetic
- Descriptive/adjectival nouns where the bare stem form is standard
- Entries whose gloss indicates they are names, titles, or fixed expressions

OCR MISS (classify as "ocr_miss"):
- Common object nouns (animals, body parts, tools, food, natural objects) ending in bare vowel
  where the standard form would be -Vʔ (e.g., *paksu should be paksuʔ "head")
- Nouns where the phonetic form shows a final glottal stop but the headword doesn't
- Nouns matching the typical -uʔ, -aʔ, -iʔ nominal suffix pattern

UNCERTAIN (classify as "uncertain"):
- Cases where you cannot determine from the available data alone

For each entry, respond with ONLY a JSON object (no markdown, no preamble):
{"results": [
  {"entry_id": "...", "classification": "ocr_miss|legitimate|uncertain", "reason": "brief explanation"}
]}"""


# ---------------------------------------------------------------------------
# Gemini Client
# ---------------------------------------------------------------------------

def call_gemini(client, prompt, model_name):
    """Send request to Gemini with retry logic. Returns parsed dict or None."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=8192,
                ),
            )

            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)

            # Normalize: accept both {"results": [...]} and bare [...]
            if isinstance(result, list):
                return {"results": result}
            return result

        except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests) as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logging.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s")
            time.sleep(wait)

        except (google_exceptions.ServiceUnavailable, google_exceptions.InternalServerError) as e:
            wait = RETRY_BACKOFF_BASE * attempt
            logging.warning(f"Server error (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s")
            time.sleep(wait)

        except json.JSONDecodeError as e:
            logging.warning(f"JSON parse error (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                logging.debug(f"Raw response: {text[:500]}")
                return None

        except Exception as e:
            logging.warning(f"Error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE)
            else:
                return None

    return None


# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def load_candidates(flags_path, s2e_path):
    """
    Load NOUN_MISSING_GLOTTAL entries from flags + full entry data from S2E.
    Returns list of entry dicts with fields needed for verification.
    """
    with open(flags_path, 'r', encoding='utf-8') as f:
        flags = json.load(f)

    # Get entry IDs flagged as NOUN_MISSING_GLOTTAL
    target_ids = set()
    for fl in flags:
        if fl['code'] == 'NOUN_MISSING_GLOTTAL':
            target_ids.add(fl['entry_id'])

    logging.info(f"Found {len(target_ids)} NOUN_MISSING_GLOTTAL entries in flags")

    # Load S2E and extract relevant fields
    with open(s2e_path, 'r', encoding='utf-8') as f:
        s2e = json.load(f)

    candidates = []
    s2e_by_id = {e.get('entry_id'): e for e in s2e}

    for eid in sorted(target_ids):
        entry = s2e_by_id.get(eid)
        if not entry:
            logging.warning(f"Entry {eid} not found in S2E")
            continue

        part_I = entry.get('part_I') or {}
        gram_info = part_I.get('grammatical_info') or {}

        candidates.append({
            'entry_id': eid,
            'headword': entry.get('headword', ''),
            'phonetic_form': part_I.get('phonetic_form') or '',
            'grammatical_class': gram_info.get('grammatical_class', ''),
            'glosses': [g.get('definition', '') for g in (part_I.get('glosses') or [])
                       if isinstance(g, dict)],
        })

    logging.info(f"Loaded {len(candidates)} candidate entries from S2E")
    return candidates


def verify_with_gemini(candidates, client, model_name, batch_size, checkpoint_path):
    """
    Send candidates to Gemini in batches for classification.
    Returns list of result dicts.
    """
    # Load checkpoint
    completed = {}  # entry_id → result dict
    if checkpoint_path and Path(checkpoint_path).exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            cp = json.load(f)
            for r in cp.get('results', []):
                completed[r['entry_id']] = r
        logging.info(f"Resumed from checkpoint: {len(completed)} entries already verified")

    remaining = [c for c in candidates if c['entry_id'] not in completed]
    total_batches = (len(remaining) + batch_size - 1) // batch_size
    logging.info(f"Verifying {len(remaining)} entries in {total_batches} batches")

    all_results = list(completed.values())

    for batch_start in range(0, len(remaining), batch_size):
        batch = remaining[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1

        prompt = ("Classify these Skiri Pawnee noun entries. Each ends in a bare vowel "
                  "without final glottal stop ʔ. Determine if this is an OCR miss, "
                  "legitimate, or uncertain.\n\n"
                  + json.dumps(batch, ensure_ascii=False, indent=2))

        result = call_gemini(client, prompt, model_name)

        if result is not None:
            for r in result.get('results', []):
                if isinstance(r, dict) and 'entry_id' in r:
                    completed[r['entry_id']] = r
                    all_results.append(r)
        else:
            logging.warning(f"Batch {batch_num} failed — skipping")

        # Checkpoint after each batch
        if checkpoint_path:
            save_checkpoint(checkpoint_path, list(completed.values()))

        time.sleep(1)
        logging.info(f"  Batch {batch_num}/{total_batches}: "
                     f"{min(batch_start + batch_size, len(remaining))}/{len(remaining)}")

    return all_results


def save_checkpoint(path, results):
    """Save verification progress."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
        }, f, ensure_ascii=False, indent=2)


def generate_report(results, candidates, report_path, fixes_path):
    """Generate verification report and fixes JSON."""

    # Count classifications
    counts = Counter(r.get('classification', 'unknown') for r in results)
    by_class = {}
    for r in results:
        cls = r.get('classification', 'unknown')
        by_class.setdefault(cls, []).append(r)

    lines = []
    lines.append("=" * 72)
    lines.append("Noun Glottal Stop Verification — Gemini Agent Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")

    total_candidates = len(candidates)
    total_verified = len(results)

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total candidates:    {total_candidates:>6}")
    lines.append(f"Verified by Gemini:  {total_verified:>6}")
    lines.append(f"")
    lines.append(f"Classifications:")
    lines.append(f"  OCR miss (need ʔ added):  {counts.get('ocr_miss', 0):>6}")
    lines.append(f"  Legitimate (no fix):      {counts.get('legitimate', 0):>6}")
    lines.append(f"  Uncertain (manual check): {counts.get('uncertain', 0):>6}")
    lines.append(f"  Unclassified/error:       {counts.get('unknown', 0):>6}")
    lines.append("")

    # --- OCR misses ---
    ocr = by_class.get('ocr_miss', [])
    lines.append("=" * 72)
    lines.append(f"OCR MISSES — RECOMMENDED FIXES ({len(ocr)} entries)")
    lines.append("These headwords should have final ʔ added.")
    lines.append("=" * 72)
    lines.append("")
    for r in sorted(ocr, key=lambda x: x['entry_id']):
        lines.append(f"  {r['entry_id']}")
        lines.append(f"    Reason: {r.get('reason', '')}")
        lines.append("")

    # --- Legitimate ---
    legit = by_class.get('legitimate', [])
    lines.append("=" * 72)
    lines.append(f"LEGITIMATE — NO FIX NEEDED ({len(legit)} entries)")
    lines.append("=" * 72)
    lines.append("")
    for r in sorted(legit, key=lambda x: x['entry_id']):
        lines.append(f"  {r['entry_id']}: {r.get('reason', '')}")
    lines.append("")

    # --- Uncertain ---
    unc = by_class.get('uncertain', [])
    if unc:
        lines.append("=" * 72)
        lines.append(f"UNCERTAIN — MANUAL CHECK NEEDED ({len(unc)} entries)")
        lines.append("=" * 72)
        lines.append("")
        for r in sorted(unc, key=lambda x: x['entry_id']):
            lines.append(f"  {r['entry_id']}: {r.get('reason', '')}")
        lines.append("")

    report_text = '\n'.join(lines)

    # Write report
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logging.info(f"Report written to {report_path}")

    # Write fixes JSON — only OCR misses
    if fixes_path:
        fixes = []
        for r in ocr:
            # Find the original candidate to get the headword
            cand = next((c for c in candidates if c['entry_id'] == r['entry_id']), None)
            if cand:
                hw = cand['headword']
                # Determine what the corrected headword should be
                corrected = hw.rstrip() + 'ʔ' if not hw.endswith('ʔ') else hw
                fixes.append({
                    'entry_id': r['entry_id'],
                    'field': 'headword',
                    'current_value': hw,
                    'corrected_value': corrected,
                    'reason': r.get('reason', ''),
                    'confidence': 'gemini_verified',
                })

        Path(fixes_path).parent.mkdir(parents=True, exist_ok=True)
        with open(fixes_path, 'w', encoding='utf-8') as f:
            json.dump(fixes, f, ensure_ascii=False, indent=2)
        logging.info(f"Fixes JSON written to {fixes_path} ({len(fixes)} fixes)")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify noun glottal stop candidates with Gemini agent"
    )
    parser.add_argument(
        '--s2e', required=True,
        help='Path to S2E JSON file (respelled/fixed version)'
    )
    parser.add_argument(
        '--flags', required=True,
        help='Path to audit flags JSON file'
    )
    parser.add_argument(
        '--report', '-r',
        default='reports/noun_glottal_verification.txt',
        help='Path for the verification report'
    )
    parser.add_argument(
        '--fixes',
        default='reports/noun_glottal_fixes.json',
        help='Path for the recommended fixes JSON'
    )
    parser.add_argument(
        '--checkpoint',
        default='reports/glottal_checkpoint.json',
        help='Checkpoint file for resume'
    )
    parser.add_argument(
        '--model', default='gemini-2.5-flash',
        help='Gemini model (default: gemini-2.5-flash)'
    )
    parser.add_argument(
        '--batch-size', type=int, default=20,
        help='Entries per batch (default: 20)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Check API key
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI-API-KEY')
    if not api_key:
        logging.error("GEMINI_API_KEY not set")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        logging.error("google-genai not installed. pip install google-genai")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Load candidates
    candidates = load_candidates(args.flags, args.s2e)
    if not candidates:
        logging.info("No candidates to verify")
        sys.exit(0)

    # Verify
    results = verify_with_gemini(
        candidates, client, args.model,
        batch_size=args.batch_size,
        checkpoint_path=args.checkpoint,
    )

    # Report
    generate_report(results, candidates, args.report, args.fixes)

    # Summary
    counts = Counter(r.get('classification', 'unknown') for r in results)
    logging.info(f"Done: {counts.get('ocr_miss', 0)} OCR misses, "
                 f"{counts.get('legitimate', 0)} legitimate, "
                 f"{counts.get('uncertain', 0)} uncertain")


if __name__ == '__main__':
    main()
