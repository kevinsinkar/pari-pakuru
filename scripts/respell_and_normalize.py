#!/usr/bin/env python3
"""
Phase 1.1c — Pronunciation Respelling + Orthographic Normalization
===================================================================
Produces two new fields for each S2E entry:

1. simplified_pronunciation  (in part_I, derived from phonetic_form)
   IPA phonetic_form → learner-friendly English respelling
   e.g. [•paa-ʔə-tʊʔ•] → pah-'uh-too'

2. normalized_form  (top-level, derived from headword + phonetic_form)
   Headword → learner orthography with circumflex long vowels, č, '
   e.g. paaʔatuʔ → pâ'atu'

Sources of truth for all mappings:
  - Parks Dictionary Sound Key (PDF 01, p. xvii)
  - Blue Book — Pari Pakuru' (pp. xvii–xxi)

Usage:
  python scripts/respell_and_normalize.py \\
      --input  Dictionary\\ Data/skiri_to_english_linked.json \\
      --output Dictionary\\ Data/skiri_to_english_respelled.json \\
      --report reports/phase_1_1c_report.txt

Dependencies: Python 3.8+ (stdlib only, no external packages)
"""

import argparse
import json
import logging
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants — Mapping tables derived from Parks & Blue Book
# ---------------------------------------------------------------------------

# Accent stripping map  (acute = high pitch in Pawnee)
ACCENT_MAP = {
    'á': 'a', 'í': 'i', 'ú': 'u',
    'à': 'a', 'ì': 'i', 'ù': 'u',
    'Á': 'A', 'Í': 'I', 'Ú': 'U',
}
ACCENTED_CHARS = set(ACCENT_MAP.keys())

# --- Simplified Pronunciation (IPA → English respelling) ---

# Vowel respellings  (Parks Sound Key + Blue Book vowel descriptions)
VOWEL_MAP = {
    # Long vowels
    'aa': 'ah',   # Parks: "father"  / Blue Book: "father"
    'ii': 'ee',   # Parks: "weed"    / Blue Book: "machine"
    'uu': 'oo',   # Parks: "rude"    / Blue Book: "ruler"
    # Short vowels
    'a':  'uh',   # Parks: "putt"    / Blue Book: "above"; "sounds like u in mud"
    'i':  'ih',   # Parks: "pit"     / Blue Book: "hit"
    'u':  'oo',   # Parks: "boot"    / Blue Book: "push" (lips rounded)
    # IPA vowels (from Parks' more precise transcription)
    'ɪ':  'ih',   # IPA near-close front  → same quality as short i
    'ʊ':  'oo',   # IPA near-close back   → same quality as short u
    'ə':  'uh',   # IPA schwa             → same quality as short a
}

# Consonant respellings  (Parks Sound Key + Blue Book consonant notes)
CONSONANT_MAP = {
    'r':  'd',    # Parks: "Spanish pero" / Blue Book: "a very soft d", "fast d as in ready"
    'c':  'ts',   # Parks: "patch/cents"  / Blue Book: "catsup"
    'č':  'ch',   # Blue Book: "often like ch in church" (especially non-final syllables)
    'ʔ':  "'",    # Parks: "uh-uh"       / Blue Book: "co-operate" (voice stop)
    # Pass-through consonants (unaspirated stops + fricatives)
    'p':  'p',    # Parks: "spot" / Blue Book: "spin"
    't':  't',    # Parks: "stop" / Blue Book: "start"
    'k':  'k',    # Parks: "skate"/ Blue Book: "skin"
    's':  's',    # Parks: "sit"  / Blue Book: "super"
    'w':  'w',    # Parks: "wall" / Blue Book: "watch"
    'h':  'h',    # Parks: "hit"  / Blue Book: "harm"
}

# All known phonetic characters (for validation in 1.1d, used here for unknown-char flagging)
VALID_PHONETIC_CHARS = set(
    'ptkcsčwrhʔ'      # consonants
    'aiuɪʊə'          # vowels (base)
    'áíúàìù'          # accented vowels
    'ː'               # IPA length mark (from ÷ fix)
    '•–-[]{}() '      # structural
    '0123456789'       # rare: form numbers leaking in
    "'"                # apostrophe (Blue Book glottal)
    ','                # variant separator (comma-separated forms)
    '/'                # alternation marker in {k/t}
    'Ø'               # null morpheme symbol (linguistics)
)

# --- Normalized Form (headword → learner orthography) ---

# Long vowel → circumflex
CIRCUMFLEX_MAP = {
    'aa': 'â', 'ii': 'î', 'uu': 'û',
    'AA': 'Â', 'II': 'Î', 'UU': 'Û',
    'Aa': 'Â', 'Ii': 'Î', 'Uu': 'Û',
}

# ---------------------------------------------------------------------------
# Phonetic Form Parser
# ---------------------------------------------------------------------------

def strip_accent(ch):
    """Return the base vowel for an accented character, or the char itself."""
    return ACCENT_MAP.get(ch, ch)


def parse_phonetic_form(pf):
    """
    Parse a phonetic_form string into a list of syllable strings.

    Input:  "[•paa-ʔə-tʊʔ•]"  or  "[–•ka•wii•ra•–]"
    Output: (["paa", "ʔə", "tʊʔ"], None)   — (syllables, error)

    Returns (None, error_string) on failure.
    """
    if not pf or not pf.strip():
        return None, "empty_phonetic_form"

    inner = pf.strip()

    # Strip brackets
    if inner.startswith('['):
        inner = inner[1:]
    if inner.endswith(']'):
        inner = inner[:-1]

    # Strip stem boundary markers (en-dash U+2013, em-dash U+2014, regular hyphen at edges)
    inner = inner.strip('–—')

    # Strip edge syllable dots
    inner = inner.strip('•')

    inner = inner.strip()
    if not inner:
        return None, "empty_after_stripping"

    # Normalize separators:  • and - both serve as syllable boundaries
    # Replace • with - then split
    inner = inner.replace('•', '-')

    syllables = [s.strip() for s in inner.split('-') if s.strip()]
    if not syllables:
        return None, "no_syllables_found"

    return syllables, None


def tokenize_syllable(syl):
    """
    Break a syllable string into a list of (token_type, base_value, is_accented) tuples.

    token_type: 'long_vowel', 'short_vowel', 'ipa_vowel', 'consonant', 'unknown'
    base_value: the base (unaccented) character(s)
    is_accented: True if any character in the token bore an accent mark
    """
    tokens = []
    i = 0
    while i < len(syl):
        ch = syl[i]
        base = strip_accent(ch)
        accented = ch in ACCENTED_CHARS

        # --- Try two-char long vowel ---
        if i + 1 < len(syl):
            ch2 = syl[i + 1]
            base2 = strip_accent(ch2)
            pair_base = base + base2
            if pair_base in ('aa', 'ii', 'uu'):
                acc = accented or (ch2 in ACCENTED_CHARS)
                tokens.append(('long_vowel', pair_base, acc))
                i += 2
                continue

        # --- IPA vowels (single char, non-ASCII) ---
        if base in ('ɪ', 'ʊ', 'ə'):
            tokens.append(('ipa_vowel', base, accented))
            i += 1
            continue

        # --- Short vowel ---
        if base in ('a', 'i', 'u'):
            tokens.append(('short_vowel', base, accented))
            i += 1
            continue

        # --- Consonant ---
        if base in CONSONANT_MAP:
            tokens.append(('consonant', base, accented))
            i += 1
            continue

        # --- Unknown character ---
        # Skip IPA length mark ː (should have been absorbed in preprocessing)
        if ch == 'ː':
            i += 1
            continue

        tokens.append(('unknown', ch, False))
        i += 1

    return tokens


def respell_syllable(tokens):
    """
    Convert a list of tokens into an English respelling string.
    Returns (respelling, has_accent, unknowns).
    """
    parts = []
    has_accent = False
    unknowns = []

    for ttype, base, accented in tokens:
        if accented:
            has_accent = True

        if ttype in ('long_vowel', 'short_vowel', 'ipa_vowel'):
            mapped = VOWEL_MAP.get(base)
            if mapped:
                parts.append(mapped)
            else:
                parts.append(f'?{base}?')
                unknowns.append(base)
        elif ttype == 'consonant':
            mapped = CONSONANT_MAP.get(base)
            if mapped:
                parts.append(mapped)
            else:
                parts.append(f'?{base}?')
                unknowns.append(base)
        elif ttype == 'unknown':
            parts.append(f'?{base}?')
            unknowns.append(base)

    respelling = ''.join(parts)
    return respelling, has_accent, unknowns


def generate_simplified_pronunciation(phonetic_form):
    """
    Master function: phonetic_form → simplified_pronunciation string.

    Handles:
      - Comma-separated variant forms (produces "variant1 / variant2")
      - Preverb notation (ʊt...) / (ut...) stripped before respelling
      - Optional sounds (h), (k), (tə), (wi) rendered in parentheses
      - IPA length mark ː (vowel lengthener, absorbed into preceding vowel)
      - Null morpheme Ø (skipped)
      - Prefix notation [+raar-] (stripped)

    Returns (pronunciation, warnings_list).
    Warnings are non-fatal notes (unknown chars, edge cases).
    """
    warnings = []

    if not phonetic_form or not phonetic_form.strip():
        return None, ["parse_error: empty_phonetic_form"]

    # --- Handle comma-separated variant forms ---
    # e.g. "[kaá-ʔə-sə-sʊʔ,kaá-sə-sʊʔ]"
    pf = phonetic_form.strip()

    # Strip outer brackets once before splitting
    if pf.startswith('[') and pf.endswith(']'):
        pf = pf[1:-1]
    elif pf.startswith('['):
        pf = pf[1:]
    elif pf.endswith(']'):
        pf = pf[:-1]

    # Strip prefix notation like [+raar-] that may appear before the main form
    pf = re.sub(r'^\+[a-zʔ]+-\]?\[?', '', pf)

    # Split on comma to get variants
    variants = [v.strip() for v in pf.split(',') if v.strip()]
    if not variants:
        return None, ["parse_error: empty_after_stripping"]

    variant_pronunciations = []
    for variant in variants:
        pron, var_warnings = _respell_single_variant(variant)
        warnings.extend(var_warnings)
        if pron:
            variant_pronunciations.append(pron)

    if not variant_pronunciations:
        return None, warnings + ["no_variants_produced"]

    # Join variants with " / "
    pronunciation = ' / '.join(variant_pronunciations)
    return pronunciation, warnings


def _respell_single_variant(variant_str):
    """
    Respell a single phonetic form variant (no commas).
    Handles preverb notation and optional sounds.
    Returns (pronunciation, warnings).
    """
    warnings = []
    pf = variant_str.strip()

    # --- Strip preverb notation at end: •(ʊt...), •(ut...) ---
    pf = re.sub(r'[•]?\(ʊt\.\.\.\)$', '', pf)
    pf = re.sub(r'[•]?\(ut\.\.\.\)$', '', pf)

    # --- Handle optional sounds: (h), (k), (tə), (wi) etc. ---
    # Replace (X) with X but mark for lowercase in output (optional)
    # We'll include them in the respelling in parentheses
    optional_sounds = re.findall(r'\(([^.)]+)\)', pf)
    # Replace (X) with a marker we can detect after tokenization
    pf_clean = re.sub(r'\(([^.)]+)\)', r'\1', pf)

    # --- Strip structural chars ---
    pf_clean = pf_clean.strip('–—•')
    pf_clean = pf_clean.strip()

    # --- Handle null morpheme Ø ---
    pf_clean = pf_clean.replace('Ø', '')
    pf_clean = pf_clean.strip('•- ')

    if not pf_clean:
        return None, ["empty_variant_after_stripping"]

    # Check for alternation markers {k/t}
    if '{' in pf_clean:
        alt_match = re.findall(r'\{[^}]+\}', pf_clean)
        for m in alt_match:
            warnings.append(f"alternation_marker: {m}")

    # --- Handle IPA length mark ː ---
    # ː after a vowel means long vowel; replace Vː with VV for tokenizer
    pf_clean = re.sub(r'([aiuɪʊəáíúàìù])ː', r'\1\1', pf_clean)

    # Normalize separators: • and - both serve as syllable boundaries
    pf_clean = pf_clean.replace('•', '-')
    syllables = [s.strip() for s in pf_clean.split('-') if s.strip()]

    if not syllables:
        return None, ["no_syllables_found"]

    respelled_syllables = []
    for syl in syllables:
        # Skip alternation markers embedded in syllables
        clean_syl = re.sub(r'\{[^}]*\}', '', syl)
        if not clean_syl:
            continue

        tokens = tokenize_syllable(clean_syl)
        respelling, has_accent, unknowns = respell_syllable(tokens)

        if unknowns:
            for u in unknowns:
                warnings.append(f"unknown_char: U+{ord(u):04X} '{u}'")

        if has_accent:
            respelling = respelling.upper()

        respelled_syllables.append(respelling)

    if not respelled_syllables:
        return None, warnings + ["no_syllables_produced"]

    pronunciation = '-'.join(respelled_syllables)
    return pronunciation, warnings


# ---------------------------------------------------------------------------
# Normalized Form Engine
# ---------------------------------------------------------------------------

def extract_c_pattern_from_phonetic(phonetic_form):
    """
    Extract the sequence of c/č from a phonetic_form string.
    Returns a list like ['č', 'c'] indicating the identity of each
    /c/-like consonant in left-to-right order.

    This is used to disambiguate 'c' in headwords: if the phonetic form
    has 'č' at position N, the Nth 'c' in the headword should become 'č'.
    """
    if not phonetic_form:
        return []

    # Strip structural characters to get just the phonetic content
    content = phonetic_form
    for ch in '[]•–—':
        content = content.replace(ch, '')
    content = content.replace('-', '')

    pattern = []
    for ch in content:
        if ch in ('c', 'č'):
            pattern.append(ch)
    return pattern


def generate_normalized_form(headword, phonetic_form):
    """
    Master function: headword + phonetic_form → normalized_form string.

    Rules (Skiri words only):
      1. aa → â, ii → î, uu → û  (and uppercase variants)
      2. c → č  ONLY when phonetic_form shows /tʃ/ at that position
      3. ʔ → '  (glottal stop to apostrophe)

    Returns (normalized_form, warnings_list).
    """
    if not headword:
        return None, ["empty_headword"]

    warnings = []
    result = headword

    # --- Step 1: c → č disambiguation ---
    phonetic_c_pattern = extract_c_pattern_from_phonetic(phonetic_form)
    headword_c_positions = [i for i, ch in enumerate(result) if ch == 'c']

    if len(headword_c_positions) != len(phonetic_c_pattern):
        if headword_c_positions and phonetic_c_pattern:
            warnings.append(
                f"c_count_mismatch: headword has {len(headword_c_positions)} 'c', "
                f"phonetic has {len(phonetic_c_pattern)} c/č — skipping c→č"
            )
        # If headword has c's but no phonetic form, or counts differ, skip disambiguation
        # (entries without phonetic_form are handled by the None check below)
    else:
        # Apply č where phonetic form indicates it
        chars = list(result)
        for hw_pos, phon_val in zip(headword_c_positions, phonetic_c_pattern):
            if phon_val == 'č':
                chars[hw_pos] = 'č'
        result = ''.join(chars)

    # --- Step 2: Long vowels → circumflex ---
    # Process longest matches first to avoid partial replacement
    # Must handle case: 'aaa' should become 'âa' not 'aâ' (greedy left-to-right)
    normalized = []
    i = 0
    while i < len(result):
        matched = False
        if i + 1 < len(result):
            pair = result[i:i + 2]
            if pair in CIRCUMFLEX_MAP:
                normalized.append(CIRCUMFLEX_MAP[pair])
                i += 2
                matched = True
        if not matched:
            normalized.append(result[i])
            i += 1
    result = ''.join(normalized)

    # --- Step 3: Glottal stop → apostrophe ---
    result = result.replace('ʔ', "'")

    return result, warnings


# ---------------------------------------------------------------------------
# Entry Processing
# ---------------------------------------------------------------------------

def process_entry(entry):
    """
    Process a single S2E entry. Adds:
      - entry["normalized_form"]
      - entry["part_I"]["simplified_pronunciation"]

    Returns a dict of warnings/flags for the report.
    """
    entry_id = entry.get('entry_id', 'UNKNOWN')
    headword = entry.get('headword', '')
    part_I = entry.get('part_I', {})
    phonetic_form = part_I.get('phonetic_form') or ''

    report = {
        'entry_id': entry_id,
        'headword': headword,
        'phonetic_form': phonetic_form,
        'pronunciation_warnings': [],
        'normalization_warnings': [],
        'simplified_pronunciation': None,
        'normalized_form': None,
    }

    # --- Generate simplified_pronunciation ---
    if phonetic_form and phonetic_form.strip():
        pron, pron_warnings = generate_simplified_pronunciation(phonetic_form)
        report['simplified_pronunciation'] = pron
        report['pronunciation_warnings'] = pron_warnings
        part_I['simplified_pronunciation'] = pron if pron else None
    else:
        report['pronunciation_warnings'].append("missing_phonetic_form")
        part_I['simplified_pronunciation'] = None

    # --- Generate normalized_form ---
    if headword and headword.strip():
        norm, norm_warnings = generate_normalized_form(headword, phonetic_form)
        report['normalized_form'] = norm
        report['normalization_warnings'] = norm_warnings
        entry['normalized_form'] = norm if norm else headword
    else:
        report['normalization_warnings'].append("missing_headword")
        entry['normalized_form'] = None

    return report


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(entry_reports, output_path):
    """Write a human-readable audit report for Phase 1.1c."""
    total = len(entry_reports)
    pron_success = sum(1 for r in entry_reports if r['simplified_pronunciation'])
    pron_fail = total - pron_success
    norm_success = sum(1 for r in entry_reports if r['normalized_form'])
    norm_fail = total - norm_success

    # Collect all warnings
    all_pron_warnings = Counter()
    all_norm_warnings = Counter()
    unknown_chars = Counter()
    c_mismatches = []
    missing_phonetic = []
    alternation_entries = []

    for r in entry_reports:
        for w in r['pronunciation_warnings']:
            if w.startswith('unknown_char:'):
                unknown_chars[w] += 1
            elif w == 'missing_phonetic_form':
                missing_phonetic.append(r['entry_id'])
            elif w.startswith('alternation_marker:'):
                alternation_entries.append((r['entry_id'], w))
            all_pron_warnings[w] += 1

        for w in r['normalization_warnings']:
            if w.startswith('c_count_mismatch:'):
                c_mismatches.append((r['entry_id'], w))
            all_norm_warnings[w] += 1

    lines = []
    lines.append("=" * 72)
    lines.append("Phase 1.1c — Pronunciation Respelling + Orthographic Normalization")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total entries processed:           {total:>6}")
    lines.append(f"simplified_pronunciation produced:  {pron_success:>6}")
    lines.append(f"simplified_pronunciation failed:    {pron_fail:>6}")
    lines.append(f"normalized_form produced:           {norm_success:>6}")
    lines.append(f"normalized_form failed:             {norm_fail:>6}")
    lines.append("")

    # Missing phonetic forms
    lines.append(f"ENTRIES MISSING PHONETIC_FORM ({len(missing_phonetic)})")
    lines.append("-" * 40)
    if missing_phonetic:
        for eid in missing_phonetic[:50]:
            lines.append(f"  {eid}")
        if len(missing_phonetic) > 50:
            lines.append(f"  ... and {len(missing_phonetic) - 50} more")
    else:
        lines.append("  (none)")
    lines.append("")

    # Unknown characters
    lines.append(f"UNKNOWN CHARACTERS IN PHONETIC FORMS ({len(unknown_chars)} unique)")
    lines.append("-" * 40)
    if unknown_chars:
        for char_desc, count in unknown_chars.most_common():
            lines.append(f"  {char_desc}  ×{count}")
    else:
        lines.append("  (none — all characters recognized)")
    lines.append("")

    # c/č disambiguation failures
    lines.append(f"c/č DISAMBIGUATION FAILURES ({len(c_mismatches)})")
    lines.append("-" * 40)
    if c_mismatches:
        for eid, w in c_mismatches[:30]:
            lines.append(f"  {eid}: {w}")
        if len(c_mismatches) > 30:
            lines.append(f"  ... and {len(c_mismatches) - 30} more")
    else:
        lines.append("  (none)")
    lines.append("")

    # Alternation markers
    lines.append(f"ALTERNATION MARKERS ({{k/t}} etc.) ({len(alternation_entries)})")
    lines.append("-" * 40)
    if alternation_entries:
        for eid, w in alternation_entries[:20]:
            lines.append(f"  {eid}: {w}")
        if len(alternation_entries) > 20:
            lines.append(f"  ... and {len(alternation_entries) - 20} more")
    else:
        lines.append("  (none)")
    lines.append("")

    # All pronunciation warnings
    lines.append("ALL PRONUNCIATION WARNINGS (by frequency)")
    lines.append("-" * 40)
    for w, count in all_pron_warnings.most_common():
        lines.append(f"  [{count:>5}×] {w}")
    lines.append("")

    # All normalization warnings
    lines.append("ALL NORMALIZATION WARNINGS (by frequency)")
    lines.append("-" * 40)
    for w, count in all_norm_warnings.most_common():
        lines.append(f"  [{count:>5}×] {w}")
    lines.append("")

    # Sample outputs (first 20 successful entries)
    lines.append("SAMPLE OUTPUTS (first 20 entries with both fields)")
    lines.append("-" * 72)
    samples = [r for r in entry_reports
               if r['simplified_pronunciation'] and r['normalized_form']][:20]
    for r in samples:
        lines.append(f"  {r['entry_id']}")
        lines.append(f"    headword:       {r['headword']}")
        lines.append(f"    phonetic_form:  {r['phonetic_form']}")
        lines.append(f"    normalized:     {r['normalized_form']}")
        lines.append(f"    pronunciation:  {r['simplified_pronunciation']}")
        if r['pronunciation_warnings']:
            lines.append(f"    warnings:       {r['pronunciation_warnings']}")
        lines.append("")

    report_text = '\n'.join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logging.info(f"Report written to {output_path}")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1.1c: Generate simplified_pronunciation and normalized_form for S2E entries"
    )
    parser.add_argument(
        '--input', '-i',
        default='Dictionary Data/skiri_to_english_linked.json',
        help='Path to input S2E JSON file (default: Dictionary Data/skiri_to_english_linked.json)'
    )
    parser.add_argument(
        '--output', '-o',
        default='Dictionary Data/skiri_to_english_respelled.json',
        help='Path to output S2E JSON file with new fields'
    )
    parser.add_argument(
        '--report', '-r',
        default='reports/phase_1_1c_report.txt',
        help='Path for the text report'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Parse and report but do not write output JSON'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print every entry as it is processed'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logging.info(f"Loading {input_path} ...")
    with open(input_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    logging.info(f"Loaded {len(entries)} entries")

    # Process all entries
    entry_reports = []
    for idx, entry in enumerate(entries):
        report = process_entry(entry)
        entry_reports.append(report)

        if args.verbose:
            eid = report['entry_id']
            pron = report['simplified_pronunciation'] or '(none)'
            norm = report['normalized_form'] or '(none)'
            logging.debug(f"  [{idx+1}/{len(entries)}] {eid}: {norm} / {pron}")

    # Generate report
    report_text = generate_report(entry_reports, args.report)

    # Print summary to console
    pron_ok = sum(1 for r in entry_reports if r['simplified_pronunciation'])
    norm_ok = sum(1 for r in entry_reports if r['normalized_form'])
    logging.info(f"Results: {pron_ok}/{len(entries)} pronunciations, {norm_ok}/{len(entries)} normalizations")

    # Write output
    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        logging.info(f"Output written to {output_path}")
    else:
        logging.info("Dry run — no output JSON written")

    logging.info("Done.")


if __name__ == '__main__':
    main()
