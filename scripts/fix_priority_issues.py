#!/usr/bin/env python3
"""
fix_priority_issues.py — Deterministic fixes for Phase 1.1d audit findings
==========================================================================

Applies mechanical, unambiguous corrections to skiri_to_english_linked.json:

  DATA FIXES (phonetic_form corrections):
    1. OCR artifacts missed by Phase 1.1a:
       ÷ (U+00F7)  → ː  (IPA length mark, 139 entries)
       ˆ (U+02C6)  → ɪ  (IPA near-close front, 3 entries)
       ‹ (U+2039)  → ʊ  (IPA near-close back, 1 entry)
       Ò (U+00D2)  → a  (plain vowel, 1 entry)
       ç (U+00E7)  → ʔ  (final glottal stop, 1 entry)
       ø (U+00F8)  → ː  (IPA length mark, 1 entry)
    2. Non-IPA phonetic forms → null:
       "[cross-referenceonly]"     (~96 entries)
       "NOT_PROVIDED"             (4 entries)
       "NOT_PROVIDED_IN_ENTRY"    (2 entries)
       "N/A"                      (5 entries)
       "Seeentryfor'...'"         (4 entries)

Outputs:
  - Corrected JSON file
  - Detailed changelog (every replacement logged per-entry)

Usage:
  python scripts/fix_priority_issues.py ^
      --input  "Dictionary Data\\skiri_to_english_linked.json" ^
      --output "Dictionary Data\\skiri_to_english_fixed.json" ^
      --log    "reports\\fix_priority_changelog.txt"

Dependencies: Python 3.8+ (stdlib only)
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# OCR correction map (Phase 1.1a supplement)
# ---------------------------------------------------------------------------

OCR_CORRECTIONS = {
    '÷': 'ː',   # U+00F7 division sign → U+02D0 IPA length mark
    'ˆ': 'ɪ',   # U+02C6 modifier circumflex → U+026A IPA near-close front
    '‹': 'ʊ',   # U+2039 left angle quote → U+028A IPA near-close back
    'Ò': 'a',   # U+00D2 O-grave → plain vowel (in context: raÒh → raah)
    'ç': 'ʔ',   # U+00E7 c-cedilla → glottal stop (in final position: čiç → čiʔ)
    'ø': 'ː',   # U+00F8 o-slash → IPA length mark (in context: ruø → ruː)
}

# Patterns that indicate the phonetic_form field contains text, not IPA
NON_IPA_PATTERNS = [
    re.compile(r'^\[?cross-reference', re.IGNORECASE),
    re.compile(r'^NOT_PROVIDED', re.IGNORECASE),
    re.compile(r'^notprovided', re.IGNORECASE),    # lowercase run-together variant
    re.compile(r'^N/A$', re.IGNORECASE),
    re.compile(r'^See\s*entry\s*for', re.IGNORECASE),
    re.compile(r'^Seeentryfor', re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Fix Functions
# ---------------------------------------------------------------------------

def fix_phonetic_ocr(phonetic_form, entry_id):
    """
    Apply OCR corrections to a phonetic_form string.
    Returns (corrected_string, list_of_changes).
    Each change is a tuple: (old_char, new_char, unicode_point).
    """
    if not phonetic_form:
        return phonetic_form, []

    changes = []
    result = []
    for ch in phonetic_form:
        if ch in OCR_CORRECTIONS:
            replacement = OCR_CORRECTIONS[ch]
            changes.append((ch, replacement, f"U+{ord(ch):04X}"))
            result.append(replacement)
        else:
            result.append(ch)

    return ''.join(result), changes


def is_non_ipa_phonetic(phonetic_form):
    """
    Check if a phonetic_form contains English text instead of IPA.
    Returns the matched pattern description or None.
    """
    if not phonetic_form:
        return None

    pf = phonetic_form.strip().strip('[]')

    for pattern in NON_IPA_PATTERNS:
        if pattern.search(pf):
            return pf

    return None


def fix_entry(entry):
    """
    Apply all deterministic fixes to a single S2E entry.
    Returns a list of change records for the changelog.
    """
    entry_id = entry.get('entry_id', 'UNKNOWN')
    part_I = entry.get('part_I') or {}
    phonetic_form = part_I.get('phonetic_form', '')

    changes = []

    if not phonetic_form:
        return changes

    # --- Check for non-IPA phonetic forms ---
    non_ipa = is_non_ipa_phonetic(phonetic_form)
    if non_ipa:
        changes.append({
            'entry_id': entry_id,
            'field': 'phonetic_form',
            'action': 'nulled_non_ipa',
            'old_value': phonetic_form,
            'new_value': None,
            'reason': f"Non-IPA text detected: '{non_ipa}'"
        })
        part_I['phonetic_form'] = None
        return changes

    # --- Apply OCR corrections ---
    corrected, ocr_changes = fix_phonetic_ocr(phonetic_form, entry_id)
    if ocr_changes:
        changes.append({
            'entry_id': entry_id,
            'field': 'phonetic_form',
            'action': 'ocr_correction',
            'old_value': phonetic_form,
            'new_value': corrected,
            'reason': f"OCR fix: {', '.join(f'{o}→{n} ({u})' for o, n, u in ocr_changes)}"
        })
        part_I['phonetic_form'] = corrected

    return changes


# ---------------------------------------------------------------------------
# Changelog Generation
# ---------------------------------------------------------------------------

def write_changelog(all_changes, output_path, total_entries):
    """Write a detailed changelog of all fixes applied."""
    lines = []
    lines.append("=" * 72)
    lines.append("fix_priority_issues.py — Changelog")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")

    # Summary
    action_counts = Counter(c['action'] for c in all_changes)
    entries_affected = len(set(c['entry_id'] for c in all_changes))

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total entries in file:     {total_entries:>6}")
    lines.append(f"Entries modified:          {entries_affected:>6}")
    lines.append(f"Total changes:            {len(all_changes):>6}")
    lines.append("")
    lines.append("Changes by type:")
    for action, count in action_counts.most_common():
        lines.append(f"  {action:<30} ×{count}")
    lines.append("")

    # OCR correction breakdown
    ocr_changes = [c for c in all_changes if c['action'] == 'ocr_correction']
    if ocr_changes:
        char_counts = Counter()
        for c in ocr_changes:
            # Parse the reason string to count individual char replacements
            reason = c['reason']
            for match in re.finditer(r'(\S)→(\S) \(([^)]+)\)', reason):
                old, new, ucode = match.groups()
                char_counts[f"{old} ({ucode}) → {new}"] += 1

        lines.append("OCR CORRECTIONS BY CHARACTER")
        lines.append("-" * 40)
        for desc, count in char_counts.most_common():
            lines.append(f"  {desc:<30} ×{count}")
        lines.append("")

    # Nulled non-IPA entries
    nulled = [c for c in all_changes if c['action'] == 'nulled_non_ipa']
    if nulled:
        lines.append(f"NON-IPA PHONETIC FORMS NULLED ({len(nulled)})")
        lines.append("-" * 40)
        for c in nulled:
            lines.append(f"  {c['entry_id']}: \"{c['old_value']}\" → null")
        lines.append("")

    # Full change log
    lines.append("DETAILED CHANGES (all)")
    lines.append("-" * 72)
    for c in all_changes:
        lines.append(f"  {c['entry_id']} | {c['field']} | {c['action']}")
        lines.append(f"    {c['reason']}")
        if c['action'] == 'ocr_correction':
            lines.append(f"    old: {c['old_value']}")
            lines.append(f"    new: {c['new_value']}")
        lines.append("")

    text = '\n'.join(lines)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Apply deterministic fixes from Phase 1.1d audit to S2E JSON"
    )
    parser.add_argument(
        '--input', '-i',
        default='Dictionary Data/skiri_to_english_linked.json',
        help='Path to input S2E JSON file'
    )
    parser.add_argument(
        '--output', '-o',
        default='Dictionary Data/skiri_to_english_fixed.json',
        help='Path to output corrected S2E JSON file'
    )
    parser.add_argument(
        '--log', '-l',
        default='reports/fix_priority_changelog.txt',
        help='Path for the detailed changelog'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Report changes without writing output'
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # Load
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logging.info(f"Loading {input_path} ...")
    with open(input_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    logging.info(f"Loaded {len(entries)} entries")

    # Fix
    all_changes = []
    for entry in entries:
        changes = fix_entry(entry)
        all_changes.extend(changes)

    # Report
    entries_affected = len(set(c['entry_id'] for c in all_changes))
    logging.info(f"Applied {len(all_changes)} changes across {entries_affected} entries")

    changelog = write_changelog(all_changes, args.log, len(entries))

    # Write
    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        logging.info(f"Output written to {output_path}")
    else:
        logging.info("Dry run — no output written")

    logging.info("Done.")


if __name__ == '__main__':
    main()
