#!/usr/bin/env python3
"""
generate_review_list.py — Produce a focused, actionable review list
====================================================================

Reads the audit flags JSON (from audit_entries.py --flags-json) and produces
a prioritized review list separating:

  1. Mechanical issues that can be fixed by script (for future fix rounds)
  2. Items requiring manual review against source PDFs
  3. Issues that are by-design and can be closed

Usage:
  python scripts/generate_review_list.py ^
      --flags reports/phase_1_1d_flags.json ^
      --output reports/manual_review_list.txt

Dependencies: Python 3.8+ (stdlib only)
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def categorize_flags(flags):
    """
    Categorize flags into actionable buckets.
    Returns dict of category → list of flags.
    """
    categories = {
        'script_fixable': [],          # Can be fixed deterministically
        'manual_phonetic_review': [],  # Need source PDF comparison
        'manual_noun_review': [],      # Noun glottal stop — needs judgment
        'by_design': [],               # Expected behavior, close
        'gemini_phonetic': [],         # Gemini-found phonetic issues
        'gemini_noun': [],             # Gemini-found noun issues (overlap with local)
        'gemini_other': [],            # Other Gemini findings
        'low_priority': [],            # Info-level, nice to have
    }

    for f in flags:
        code = f['code']
        severity = f['severity']
        value = f.get('value', '') or ''

        # --- By-design (close these) ---
        # VD verbs without verb class is normal in Parks
        if code == 'MISSING_VERB_CLASS' and 'VD' in f.get('message', ''):
            categories['by_design'].append(f)
            continue

        # Missing brackets on entries that use • instead of [] — valid notation variant
        if code in ('MISSING_OPEN_BRACKET', 'MISSING_CLOSE_BRACKET'):
            categories['low_priority'].append(f)
            continue

        # --- Script-fixable ---
        # Remaining non-IPA phonetic forms
        if code == 'INVALID_PHONETIC_CHAR':
            # Check if the whole value is a non-IPA string
            if value and any(x in value.lower() for x in ['notprovided', 'cross-reference', 'n/a', 'seeentry']):
                categories['script_fixable'].append(f)
            else:
                categories['script_fixable'].append(f)
            continue

        if code == 'EMPTY_PHONETIC':
            categories['low_priority'].append(f)
            continue

        # --- Manual review: phonetic ---
        if code == 'CONSONANT_SKELETON_MISMATCH':
            categories['manual_phonetic_review'].append(f)
            continue

        # --- Manual review: nouns ---
        if code == 'NOUN_MISSING_GLOTTAL':
            categories['manual_noun_review'].append(f)
            continue

        # Noun glottal by-design categories
        if code in ('NOUN_MISSING_GLOTTAL_DEPKIN', 'NOUN_MISSING_GLOTTAL_PROPER'):
            categories['by_design'].append(f)
            continue

        # --- Gemini flags ---
        if code.startswith('GEMINI_'):
            code_upper = code.upper()
            if any(x in code_upper for x in ['PHONETIC', 'VOWEL_LENGTH', 'SKELETON', 'MISMATCH',
                                              'INCONSISTEN', 'C_REALIZATION', 'FORM_FORMAT']):
                if 'NOUN' not in code_upper:
                    categories['gemini_phonetic'].append(f)
                    continue
            if any(x in code_upper for x in ['NOUN', 'BARE_VOWEL', 'GLOTTAL', 'CONSONANT_ENDING']):
                categories['gemini_noun'].append(f)
                continue
            if any(x in code_upper for x in ['EMPTY', 'MISSING']):
                categories['low_priority'].append(f)
                continue
            if 'OCR' in code_upper:
                categories['script_fixable'].append(f)
                continue
            categories['gemini_other'].append(f)
            continue

        # --- Remaining info-level ---
        if severity == 'info':
            categories['low_priority'].append(f)
            continue

        # --- Everything else ---
        if code == 'UNKNOWN_VERB_CLASS':
            categories['low_priority'].append(f)
            continue
        if code == 'UNKNOWN_GRAM_CLASS':
            categories['low_priority'].append(f)
            continue

        categories['low_priority'].append(f)

    return categories


def generate_review_report(categories, total_flags, output_path):
    """Write the focused review report."""
    lines = []
    lines.append("=" * 72)
    lines.append("MANUAL REVIEW LIST — Prioritized Action Items")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")

    # Summary
    lines.append("DISPOSITION SUMMARY")
    lines.append("-" * 50)
    lines.append(f"Total flags in audit:          {total_flags:>6}")
    lines.append(f"")
    lines.append(f"By-design (close, no action):  {len(categories['by_design']):>6}")
    lines.append(f"Script-fixable (next fix run):  {len(categories['script_fixable']):>6}")
    lines.append(f"Low priority / info:           {len(categories['low_priority']):>6}")
    lines.append(f"")
    lines.append(f"** MANUAL REVIEW NEEDED **")
    lines.append(f"  Phonetic mismatches (local): {len(categories['manual_phonetic_review']):>6}")
    lines.append(f"  Noun glottal stop (local):   {len(categories['manual_noun_review']):>6}")
    lines.append(f"  Phonetic issues (Gemini):    {len(categories['gemini_phonetic']):>6}")
    lines.append(f"  Noun issues (Gemini):        {len(categories['gemini_noun']):>6}")
    lines.append(f"  Other Gemini findings:       {len(categories['gemini_other']):>6}")
    total_manual = (len(categories['manual_phonetic_review']) + len(categories['manual_noun_review'])
                    + len(categories['gemini_phonetic']) + len(categories['gemini_noun'])
                    + len(categories['gemini_other']))
    lines.append(f"  TOTAL needing review:        {total_manual:>6}")
    lines.append("")

    # =====================================================================
    # SECTION 1: Gemini phonetic findings (highest value, smallest set)
    # =====================================================================
    gp = categories['gemini_phonetic']
    # Deduplicate by entry_id
    seen = set()
    unique_gp = []
    for f in gp:
        if f['entry_id'] not in seen:
            seen.add(f['entry_id'])
            unique_gp.append(f)

    lines.append("=" * 72)
    lines.append(f"REVIEW GROUP 1: GEMINI PHONETIC FINDINGS ({len(unique_gp)} entries)")
    lines.append("Action: Compare against source PDF pages")
    lines.append("=" * 72)
    lines.append("")
    for f in unique_gp:
        lines.append(f"  [{f['severity'].upper():>7}] {f['entry_id']}")
        lines.append(f"    {f['code']}")
        lines.append(f"    {f['message']}")
        lines.append("")

    # =====================================================================
    # SECTION 2: Gemini other findings
    # =====================================================================
    if categories['gemini_other']:
        lines.append("=" * 72)
        lines.append(f"REVIEW GROUP 2: OTHER GEMINI FINDINGS ({len(categories['gemini_other'])})")
        lines.append("=" * 72)
        lines.append("")
        for f in categories['gemini_other']:
            lines.append(f"  [{f['severity'].upper():>7}] {f['entry_id']}")
            lines.append(f"    {f['code']}: {f['message']}")
            lines.append("")

    # =====================================================================
    # SECTION 3: Local consonant skeleton mismatches (sample)
    # =====================================================================
    skel = categories['manual_phonetic_review']
    lines.append("=" * 72)
    lines.append(f"REVIEW GROUP 3: CONSONANT SKELETON MISMATCHES ({len(skel)} entries)")
    lines.append("Action: Spot-check sample against source PDFs; many may be")
    lines.append("        optional sounds (h)/(k) or preverb boundaries")
    lines.append("=" * 72)
    lines.append("")
    for f in skel[:40]:
        val = f.get('value', '')
        lines.append(f"  {f['entry_id']}: {f['message']}")
        if val:
            lines.append(f"    {val}")
    if len(skel) > 40:
        lines.append(f"  ... and {len(skel) - 40} more")
    lines.append("")

    # =====================================================================
    # SECTION 4: Noun glottal stop (combined local + Gemini)
    # =====================================================================
    noun_local = categories['manual_noun_review']
    noun_gemini = categories['gemini_noun']
    # Merge by entry_id
    all_noun_ids = set()
    noun_entries = {}
    for f in noun_local:
        eid = f['entry_id']
        all_noun_ids.add(eid)
        noun_entries[eid] = {'local': f, 'gemini': None}
    for f in noun_gemini:
        eid = f['entry_id']
        all_noun_ids.add(eid)
        if eid in noun_entries:
            noun_entries[eid]['gemini'] = f
        else:
            noun_entries[eid] = {'local': None, 'gemini': f}

    both = [eid for eid, v in noun_entries.items() if v['local'] and v['gemini']]
    local_only = [eid for eid, v in noun_entries.items() if v['local'] and not v['gemini']]
    gemini_only = [eid for eid, v in noun_entries.items() if not v['local'] and v['gemini']]

    lines.append("=" * 72)
    lines.append(f"REVIEW GROUP 4: NOUN GLOTTAL STOP ({len(all_noun_ids)} unique entries)")
    lines.append(f"  Flagged by both local + Gemini: {len(both)} (high confidence)")
    lines.append(f"  Flagged by local only:          {len(local_only)}")
    lines.append(f"  Flagged by Gemini only:         {len(gemini_only)}")
    lines.append("Action: Batch review — many are proper nouns, place names, or")
    lines.append("        kinship terms that legitimately lack final ʔ.")
    lines.append("        Focus on common nouns (N class) that end in bare vowel.")
    lines.append("=" * 72)
    lines.append("")

    lines.append("High confidence (both flagged) — first 30:")
    for eid in sorted(both)[:30]:
        f = noun_entries[eid]['local']
        lines.append(f"  {eid}: {f.get('value', '')}")
    if len(both) > 30:
        lines.append(f"  ... and {len(both) - 30} more")
    lines.append("")

    # =====================================================================
    # SECTION 5: Script-fixable (for next fix_priority_issues.py run)
    # =====================================================================
    sf = categories['script_fixable']
    lines.append("=" * 72)
    lines.append(f"SCRIPT-FIXABLE ({len(sf)} flags)")
    lines.append("Action: Already handled by updated fix_priority_issues.py.")
    lines.append("        Re-run fix script, then re-run audit to confirm.")
    lines.append("=" * 72)
    lines.append("")
    sf_codes = Counter(f['code'] for f in sf)
    for code, count in sf_codes.most_common():
        lines.append(f"  {code}: {count}")
    lines.append("")

    # =====================================================================
    # SECTION 6: By-design (no action needed)
    # =====================================================================
    bd = categories['by_design']
    lines.append("=" * 72)
    lines.append(f"BY-DESIGN / CLOSED ({len(bd)} flags)")
    lines.append("No action needed.")
    lines.append("=" * 72)
    lines.append("")
    bd_codes = Counter(f['code'] for f in bd)
    for code, count in bd_codes.most_common():
        lines.append(f"  {code}: {count}")
    lines.append("")

    report_text = '\n'.join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

    return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Generate a focused, actionable review list from audit flags"
    )
    parser.add_argument(
        '--flags', '-f', required=True,
        help='Path to flags JSON file (from audit_entries.py --flags-json)'
    )
    parser.add_argument(
        '--output', '-o',
        default='reports/manual_review_list.txt',
        help='Path for the review list output'
    )
    args = parser.parse_args()

    flags_path = Path(args.flags)
    if not flags_path.exists():
        print(f"Error: flags file not found: {flags_path}", file=sys.stderr)
        sys.exit(1)

    with open(flags_path, 'r', encoding='utf-8') as f:
        flags = json.load(f)

    print(f"Loaded {len(flags)} flags from {flags_path}")

    categories = categorize_flags(flags)
    report = generate_review_report(categories, len(flags), args.output)

    print(f"Review list written to {args.output}")
    # Print summary to console
    for line in report.split('\n'):
        if line.startswith('  ') and '**' not in line:
            continue
        if line.strip():
            print(line)


if __name__ == '__main__':
    main()
