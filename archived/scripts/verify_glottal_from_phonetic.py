#!/usr/bin/env python3
"""
verify_glottal_from_phonetic.py — Cross-reference phonetic_form to verify headword glottal stops
=================================================================================================

For each NOUN_MISSING_GLOTTAL candidate, checks whether the phonetic_form
ends in ʔ. This is the definitive local check:

  - phonetic ends in ʔ, headword doesn't  → OCR_MISS (concrete fix)
  - phonetic also lacks final ʔ           → CONFIRMED_NO_GLOTTAL (headword correct)
  - no phonetic_form available            → UNVERIFIABLE (needs manual/Gemini check)

This replaces linguistic guesswork with direct evidence from the source data.

Usage:
  python scripts/verify_glottal_from_phonetic.py ^
      --s2e "Dictionary Data\\skiri_to_english_respelled.json" ^
      --flags reports\\flags_final.json ^
      --report reports\\glottal_phonetic_verification.txt ^
      --fixes reports\\glottal_confirmed_fixes.json

For Gemini follow-up on UNVERIFIABLE entries:
  python scripts/verify_glottal_from_phonetic.py ^
      --s2e "Dictionary Data\\skiri_to_english_respelled.json" ^
      --flags reports\\flags_final.json ^
      --use-gemini ^
      --report reports\\glottal_full_verification.txt ^
      --fixes reports\\glottal_all_fixes.json ^
      --checkpoint reports\\glottal_phonetic_checkpoint.json

Dependencies: Python 3.8+ (local mode), google-genai (Gemini mode)
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
# Local Phonetic Verification
# ---------------------------------------------------------------------------

def extract_final_segment(phonetic_form):
    """
    Extract the final phonetic segment from a phonetic_form string.
    Handles:
      - Bracket stripping: [•paa-ʔə-tʊʔ•] → paa-ʔə-tʊʔ
      - Comma-separated variants: takes the FIRST variant
      - Preverb stripping: removes trailing (ʊt...) / (ut...)
      - Optional sounds: (h), (r) etc. → included as part of form

    Returns the cleaned final portion, or None if unparseable.
    """
    if not phonetic_form or not isinstance(phonetic_form, str):
        return None

    pf = phonetic_form.strip()

    # Take first variant if comma-separated
    if ',' in pf:
        pf = pf.split(',')[0].strip()

    # Strip brackets
    pf = pf.strip('[]')

    # Strip stem boundary markers
    pf = pf.strip('–—')

    # Strip syllable dots at edges
    pf = pf.strip('•')

    # Remove preverb notation at end
    pf = re.sub(r'\s*\(ʊt\.\.\.\)\s*$', '', pf)
    pf = re.sub(r'\s*\(ut\.\.\.\)\s*$', '', pf)

    # Strip prefix notation like +raar-
    pf = re.sub(r'^\+[a-zʔ]+-\]?\[?', '', pf)

    pf = pf.strip('•–— ')

    if not pf:
        return None

    return pf


def phonetic_ends_in_glottal(phonetic_form):
    """
    Determine if a phonetic_form ends in glottal stop ʔ.

    Returns:
      True  — phonetic form ends in ʔ (possibly followed by optional sounds)
      False — phonetic form does NOT end in ʔ
      None  — cannot determine (empty/unparseable)
    """
    final = extract_final_segment(phonetic_form)
    if not final:
        return None

    # Get the very end of the form, ignoring structural chars
    # Remove trailing optional sound markers but check inside them too
    # e.g., [•paa-tʊʔ•] → ends in ʔ
    # e.g., [•paa-tʊ(h)•] → does NOT end in ʔ (ends in optional h)

    # Work backwards through the cleaned string
    end = final.rstrip()

    # Strip trailing optional sound notation to see what's underneath
    # But we need to check: does the UNDERLYING form end in ʔ?
    # e.g., "tʊʔ" → yes
    # e.g., "tʊ(h)" → the real ending is ʊ with optional h, no ʔ
    # e.g., "ʔuu(h)" → real ending has ʔ earlier but not finally

    # Remove all parenthesized optional sounds from the end
    cleaned = re.sub(r'\([^)]+\)\s*$', '', end).strip()
    # Could be multiple: e.g., "(h)(k)" at end
    while re.search(r'\([^)]+\)\s*$', cleaned):
        cleaned = re.sub(r'\([^)]+\)\s*$', '', cleaned).strip()

    # Also strip alternation markers at end
    cleaned = re.sub(r'\{[^}]+\}\s*$', '', cleaned).strip()

    if not cleaned:
        return None

    # Now check: does the cleaned form end in ʔ?
    # Need to look at the actual last character(s), skipping structural chars
    last_chars = cleaned.rstrip('•–— -')

    if not last_chars:
        return None

    # Null morpheme Ø alone is not real phonetic data
    if last_chars.replace('Ø', '').replace('ø', '') == '':
        return None

    return last_chars[-1] == 'ʔ'


def verify_candidates_locally(candidates, s2e_by_id):
    """
    Cross-reference phonetic_form with headword for each candidate.
    Returns list of result dicts with classification.
    """
    results = []

    for cand in candidates:
        eid = cand['entry_id']
        entry = s2e_by_id.get(eid)
        if not entry:
            results.append({
                'entry_id': eid,
                'classification': 'unverifiable',
                'reason': 'Entry not found in S2E',
                'headword': cand.get('headword', ''),
                'phonetic_form': '',
            })
            continue

        headword = entry.get('headword', '')
        part_I = entry.get('part_I') or {}
        phonetic_form = part_I.get('phonetic_form') or ''

        result = {
            'entry_id': eid,
            'headword': headword,
            'phonetic_form': phonetic_form,
        }

        if not phonetic_form:
            result['classification'] = 'unverifiable'
            result['reason'] = 'No phonetic_form available'
            results.append(result)
            continue

        pf_has_glottal = phonetic_ends_in_glottal(phonetic_form)

        if pf_has_glottal is None:
            result['classification'] = 'unverifiable'
            result['reason'] = f'Could not parse final segment of phonetic_form: {phonetic_form}'
        elif pf_has_glottal:
            result['classification'] = 'ocr_miss'
            result['reason'] = (f'Phonetic form ends in ʔ but headword does not. '
                               f'headword: {headword} | phonetic: {phonetic_form}')
        else:
            result['classification'] = 'confirmed_no_glottal'
            result['reason'] = (f'Phonetic form also lacks final ʔ — headword is correct. '
                               f'phonetic: {phonetic_form}')

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Gemini Verification for Unverifiable Entries
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5

GEMINI_SYSTEM_INSTRUCTION = """You are an expert in Skiri Pawnee linguistics reviewing dictionary entries.

These noun entries end in a bare vowel without a glottal stop (ʔ), and their phonetic_form
is missing or unparseable, so we cannot verify locally.

For each entry, determine based on the gloss, grammatical class, and any available context:
- "ocr_miss": The headword should likely end in ʔ (common object/animal/body part noun)
- "legitimate": The bare vowel ending is correct (proper noun, name, title, compound, loanword)
- "uncertain": Cannot determine without seeing the source PDF

Respond ONLY with JSON (no markdown): {"results": [{"entry_id": "...", "classification": "...", "reason": "..."}]}"""


def verify_unverifiable_with_gemini(unverifiable, s2e_by_id, client, model_name, batch_size, checkpoint_path):
    """Send unverifiable entries to Gemini for classification."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    # Load checkpoint
    completed = {}
    if checkpoint_path and Path(checkpoint_path).exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            cp = json.load(f)
            for r in cp.get('results', []):
                completed[r['entry_id']] = r
        logging.info(f"Resumed from checkpoint: {len(completed)} entries")

    remaining = [e for e in unverifiable if e['entry_id'] not in completed]
    total_batches = (len(remaining) + batch_size - 1) // batch_size
    logging.info(f"Gemini: {len(remaining)} unverifiable entries in {total_batches} batches")

    all_results = list(completed.values())

    for batch_start in range(0, len(remaining), batch_size):
        batch = remaining[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1

        batch_data = []
        for entry_info in batch:
            eid = entry_info['entry_id']
            entry = s2e_by_id.get(eid, {})
            part_I = entry.get('part_I') or {}
            gram_info = part_I.get('grammatical_info') or {}
            batch_data.append({
                'entry_id': eid,
                'headword': entry.get('headword', ''),
                'grammatical_class': gram_info.get('grammatical_class', ''),
                'glosses': [g.get('definition', '') for g in (part_I.get('glosses') or [])
                           if isinstance(g, dict)],
            })

        prompt = ("Classify these Skiri Pawnee nouns. Their phonetic forms are missing, "
                  "so classify based on gloss and grammatical class only.\n\n"
                  + json.dumps(batch_data, ensure_ascii=False, indent=2))

        result = _call_gemini(client, prompt, model_name)

        if result:
            for r in result.get('results', []):
                if isinstance(r, dict) and 'entry_id' in r:
                    completed[r['entry_id']] = r
                    all_results.append(r)
        else:
            logging.warning(f"Batch {batch_num} failed")

        if checkpoint_path:
            _save_checkpoint(checkpoint_path, list(completed.values()))

        time.sleep(1)
        logging.info(f"  Batch {batch_num}/{total_batches}")

    return all_results


def _call_gemini(client, prompt, model_name):
    """Send request to Gemini with retry. Returns parsed dict or None."""
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=8192,
                ),
            )
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            result = json.loads(text)
            if isinstance(result, list):
                return {"results": result}
            return result

        except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests):
            time.sleep(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))
        except (google_exceptions.ServiceUnavailable, google_exceptions.InternalServerError):
            time.sleep(RETRY_BACKOFF_BASE * attempt)
        except json.JSONDecodeError:
            if attempt == MAX_RETRIES:
                return None
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Error: {e}")
            if attempt == MAX_RETRIES:
                return None
            time.sleep(RETRY_BACKOFF_BASE)
    return None


def _save_checkpoint(path, results):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'timestamp': datetime.now().isoformat(), 'results': results},
                  f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def generate_report(local_results, gemini_results, report_path, fixes_path, candidates):
    """Generate combined verification report."""
    # Merge results — Gemini overrides unverifiable entries
    merged = {}
    for r in local_results:
        merged[r['entry_id']] = r
    for r in gemini_results:
        if r.get('entry_id') in merged and merged[r['entry_id']]['classification'] == 'unverifiable':
            merged[r['entry_id']]['classification'] = r.get('classification', 'uncertain')
            merged[r['entry_id']]['reason'] = f"(Gemini) {r.get('reason', '')}"

    all_results = list(merged.values())
    counts = Counter(r['classification'] for r in all_results)

    lines = []
    lines.append("=" * 72)
    lines.append("Noun Glottal Stop Verification — Phonetic Cross-Reference")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total candidates:                   {len(candidates):>6}")
    lines.append(f"")
    lines.append(f"LOCAL VERIFICATION (phonetic_form cross-reference):")
    lines.append(f"  OCR miss (phonetic has ʔ):        {counts.get('ocr_miss', 0):>6}")
    lines.append(f"  Confirmed correct (no ʔ in both): {counts.get('confirmed_no_glottal', 0):>6}")
    lines.append(f"  Unverifiable (no phonetic_form):  {counts.get('unverifiable', 0):>6}")
    if gemini_results:
        gc = Counter(r.get('classification') for r in gemini_results)
        lines.append(f"")
        lines.append(f"GEMINI VERIFICATION (unverifiable entries):")
        lines.append(f"  OCR miss:                         {gc.get('ocr_miss', 0):>6}")
        lines.append(f"  Legitimate:                       {gc.get('legitimate', 0):>6}")
        lines.append(f"  Uncertain:                        {gc.get('uncertain', 0):>6}")
    lines.append("")

    # --- OCR misses (concrete fixes) ---
    ocr = [r for r in all_results if r['classification'] == 'ocr_miss']
    lines.append("=" * 72)
    lines.append(f"OCR MISSES — CONFIRMED BY PHONETIC FORM ({len(ocr)} entries)")
    lines.append("Phonetic form ends in ʔ but headword does not.")
    lines.append("=" * 72)
    lines.append("")
    for r in sorted(ocr, key=lambda x: x['entry_id']):
        lines.append(f"  {r['entry_id']}")
        lines.append(f"    headword:  {r.get('headword', '')}")
        lines.append(f"    phonetic:  {r.get('phonetic_form', '')}")
        lines.append("")

    # --- Confirmed correct ---
    correct = [r for r in all_results if r['classification'] == 'confirmed_no_glottal']
    lines.append("=" * 72)
    lines.append(f"CONFIRMED CORRECT — NO FIX NEEDED ({len(correct)} entries)")
    lines.append("Both headword and phonetic form lack final ʔ.")
    lines.append("=" * 72)
    lines.append("")
    for r in sorted(correct, key=lambda x: x['entry_id'])[:30]:
        lines.append(f"  {r['entry_id']}: {r.get('headword', '')} | {r.get('phonetic_form', '')}")
    if len(correct) > 30:
        lines.append(f"  ... and {len(correct) - 30} more")
    lines.append("")

    # --- Remaining unverifiable ---
    unv = [r for r in all_results if r['classification'] == 'unverifiable']
    if unv:
        lines.append("=" * 72)
        lines.append(f"STILL UNVERIFIABLE ({len(unv)} entries)")
        lines.append("No phonetic form, Gemini not run or could not classify.")
        lines.append("=" * 72)
        lines.append("")
        for r in unv:
            lines.append(f"  {r['entry_id']}: {r.get('reason', '')}")
        lines.append("")

    report_text = '\n'.join(lines)
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logging.info(f"Report: {report_path}")

    # --- Fixes JSON ---
    if fixes_path:
        cand_by_id = {c['entry_id']: c for c in candidates}
        fixes = []
        for r in ocr:
            hw = r.get('headword', '')
            if hw and not hw.endswith('ʔ'):
                fixes.append({
                    'entry_id': r['entry_id'],
                    'field': 'headword',
                    'current_value': hw,
                    'corrected_value': hw + 'ʔ',
                    'evidence': 'phonetic_form_ends_in_glottal',
                    'phonetic_form': r.get('phonetic_form', ''),
                })
        Path(fixes_path).parent.mkdir(parents=True, exist_ok=True)
        with open(fixes_path, 'w', encoding='utf-8') as f:
            json.dump(fixes, f, ensure_ascii=False, indent=2)
        logging.info(f"Fixes JSON: {fixes_path} ({len(fixes)} fixes)")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify noun glottal stops by cross-referencing phonetic_form"
    )
    parser.add_argument('--s2e', required=True, help='S2E JSON file path')
    parser.add_argument('--flags', required=True, help='Audit flags JSON path')
    parser.add_argument('--report', '-r', default='reports/glottal_phonetic_verification.txt')
    parser.add_argument('--fixes', default='reports/glottal_confirmed_fixes.json')
    parser.add_argument('--use-gemini', action='store_true',
                        help='Run Gemini on entries with no phonetic_form')
    parser.add_argument('--model', default='gemini-2.5-flash')
    parser.add_argument('--batch-size', type=int, default=20)
    parser.add_argument('--checkpoint', default='reports/glottal_phonetic_checkpoint.json')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Load flags
    with open(args.flags, 'r', encoding='utf-8') as f:
        flags = json.load(f)
    target_ids = set(fl['entry_id'] for fl in flags if fl['code'] == 'NOUN_MISSING_GLOTTAL')
    logging.info(f"Found {len(target_ids)} NOUN_MISSING_GLOTTAL candidates")

    # Load S2E
    with open(args.s2e, 'r', encoding='utf-8') as f:
        s2e = json.load(f)
    s2e_by_id = {e.get('entry_id'): e for e in s2e}

    # Build candidate list
    candidates = []
    for eid in sorted(target_ids):
        entry = s2e_by_id.get(eid)
        if entry:
            candidates.append({
                'entry_id': eid,
                'headword': entry.get('headword', ''),
            })

    # Local verification
    logging.info("Running local phonetic cross-reference...")
    local_results = verify_candidates_locally(candidates, s2e_by_id)

    counts = Counter(r['classification'] for r in local_results)
    logging.info(f"Local results: {counts.get('ocr_miss', 0)} OCR misses, "
                 f"{counts.get('confirmed_no_glottal', 0)} confirmed correct, "
                 f"{counts.get('unverifiable', 0)} unverifiable")

    # Gemini for unverifiable entries
    gemini_results = []
    if args.use_gemini:
        unverifiable = [r for r in local_results if r['classification'] == 'unverifiable']
        if unverifiable:
            api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI-API-KEY')
            if not api_key:
                logging.error("GEMINI_API_KEY not set")
                sys.exit(1)
            try:
                from google import genai
            except ImportError:
                logging.error("google-genai not installed")
                sys.exit(1)

            client = genai.Client(api_key=api_key)
            gemini_results = verify_unverifiable_with_gemini(
                unverifiable, s2e_by_id, client, args.model,
                args.batch_size, args.checkpoint
            )
        else:
            logging.info("No unverifiable entries — skipping Gemini")

    # Report
    generate_report(local_results, gemini_results, args.report, args.fixes, candidates)
    logging.info("Done.")


if __name__ == '__main__':
    main()
