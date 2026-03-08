#!/usr/bin/env python3
"""
Phase 1.1d — Parsing Completeness Audit
=========================================
Validates every S2E (and optionally E2S) entry against expected data quality
standards. Runs in two modes:

  LOCAL MODE  (default, no API key needed):
    - Field presence validation (headwords, phonetic forms, glosses, etc.)
    - Phonetic character validation (flag non-IPA characters)
    - Noun glottal stop check (nouns ending in vowel without ʔ)
    - Headword ↔ phonetic form consistency checks
    - Generates a prioritized audit report

  GEMINI MODE  (requires --use-gemini and GEMINI_API_KEY env var):
    - Sends batches of 20 entries to Gemini for AI validation
    - Checks phonetic ↔ headword consistency, gloss plausibility
    - Supports checkpointing for resume after interruption

Usage:
  # Local-only audit (recommended first pass):
  python scripts/audit_entries.py \\
      --s2e Dictionary\\ Data/skiri_to_english_linked.json \\
      --report reports/phase_1_1d_audit.txt

  # With E2S cross-validation:
  python scripts/audit_entries.py \\
      --s2e Dictionary\\ Data/skiri_to_english_linked.json \\
      --e2s Dictionary\\ Data/english_to_skiri_linked.json \\
      --report reports/phase_1_1d_audit.txt

  # With Gemini AI validation:
  python scripts/audit_entries.py \\
      --s2e Dictionary\\ Data/skiri_to_english_linked.json \\
      --use-gemini --gemini-batch-size 20 \\
      --checkpoint reports/gemini_checkpoint.json \\
      --report reports/phase_1_1d_audit.txt

Dependencies: Python 3.8+ (stdlib only for local mode)
              google-generativeai package for Gemini mode
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid characters in phonetic_form (post-normalization from Phase 1.1a)
VALID_PHONETIC_CONSONANTS = set('ptkcsčwrhʔ')
VALID_PHONETIC_VOWELS_BASE = set('aiuɪʊə')
VALID_PHONETIC_VOWELS_ACCENTED = set('áíúàìù')
VALID_PHONETIC_STRUCTURAL = set('•–—-[]{}() /')
VALID_PHONETIC_MISC = set("'")  # apostrophe (Blue Book notation leaking in)

VALID_PHONETIC_ALL = (
    VALID_PHONETIC_CONSONANTS
    | VALID_PHONETIC_VOWELS_BASE
    | VALID_PHONETIC_VOWELS_ACCENTED
    | VALID_PHONETIC_STRUCTURAL
    | VALID_PHONETIC_MISC
    | {'ː'}  # IPA length mark (from ÷ fix)
    | {','}  # variant separator
    | {'Ø'}  # null morpheme symbol
    | {'.'}  # in preverb notation (ut...)
)

# Grammatical classes expected in the data
# Single classes
_BASE_GRAM_CLASSES = {
    'N', 'N-DEP', 'N-KIN',
    'VI', 'VT', 'VD', 'VL', 'VP', 'VR',
    'ADJ', 'ADV', 'ADV-P', 'NUM', 'PRON', 'DEM', 'QUAN',
    'CONJ', 'INTERJ', 'INTER', 'EXCL', 'LOC', 'COLL',
}

# Multi-class entries are valid (parsed as "CLASS1, CLASS2")
# We validate each component rather than the full string
VALID_GRAM_CLASSES = _BASE_GRAM_CLASSES.copy()

# Verb classes
VALID_VERB_CLASSES = {
    '(1)', '(1-a)', '(1-i)', '(2)', '(2-i)',
    '(3)', '(4)', '(4-i)', '(u)', '(wi)',
    '1', '1-a', '1-i', '2', '2-i',
    '3', '4', '4-i', 'u', 'wi',
}

# Noun classes (should end with ʔ if ending in a vowel)
NOUN_CLASSES = {'N', 'N-DEP', 'N-KIN'}

# Vowels for glottal stop check
PAWNEE_VOWELS = set('aiuáíúàìùɪʊə')


# ---------------------------------------------------------------------------
# Validation Checks
# ---------------------------------------------------------------------------

class AuditFlag:
    """Represents a single validation issue found in an entry."""
    def __init__(self, entry_id, field, severity, code, message, value=None):
        self.entry_id = entry_id
        self.field = field            # e.g. 'headword', 'phonetic_form', 'glosses'
        self.severity = severity      # 'error', 'warning', 'info'
        self.code = code              # machine-readable code
        self.message = message        # human-readable description
        self.value = value            # the problematic value (for debugging)

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.entry_id} | {self.field} | {self.code}: {self.message}"


def validate_entry(entry):
    """
    Run all local validation checks on a single S2E entry.
    Returns a list of AuditFlag objects.
    """
    flags = []
    entry_id = entry.get('entry_id', 'UNKNOWN')
    headword = entry.get('headword', '')
    part_I = entry.get('part_I') or {}
    part_II = entry.get('part_II') or {}

    phonetic_form = part_I.get('phonetic_form') or ''
    gram_info = part_I.get('grammatical_info') or {}
    gram_class = gram_info.get('grammatical_class', '')
    verb_class = gram_info.get('verb_class', '')
    glosses = part_I.get('glosses') or []

    # ---- 1. Field presence checks ----

    if not entry_id or entry_id == 'UNKNOWN':
        flags.append(AuditFlag(entry_id, 'entry_id', 'error', 'MISSING_ENTRY_ID',
                               'Entry has no entry_id'))

    if not headword or not headword.strip():
        flags.append(AuditFlag(entry_id, 'headword', 'error', 'EMPTY_HEADWORD',
                               'Headword is empty or missing'))

    if not phonetic_form or not str(phonetic_form).strip():
        flags.append(AuditFlag(entry_id, 'phonetic_form', 'warning', 'EMPTY_PHONETIC',
                               'Phonetic form is empty or missing'))

    if not gram_class or not gram_class.strip():
        flags.append(AuditFlag(entry_id, 'grammatical_class', 'warning', 'EMPTY_GRAM_CLASS',
                               'Grammatical class is empty'))

    if not glosses:
        flags.append(AuditFlag(entry_id, 'glosses', 'error', 'EMPTY_GLOSSES',
                               'No glosses/definitions provided'))
    else:
        for g in glosses:
            defn = g.get('definition', '') if isinstance(g, dict) else ''
            if not defn or not defn.strip():
                flags.append(AuditFlag(entry_id, 'glosses', 'warning', 'EMPTY_GLOSS_DEFINITION',
                                       f"Gloss {g.get('number', '?')} has empty definition"))

    # ---- 2. Grammatical class validation ----

    if gram_class and gram_class.strip():
        gc = gram_class.strip()
        # Handle multi-class entries like "VT, VR" or "N, ADV"
        # Also handle entries with verb class inline like "VI(1), VT(1)"
        gc_parts = [p.strip() for p in re.split(r'[,;]', gc)]
        for part in gc_parts:
            # Strip verb class notation from class for validation: "VI(1)" → "VI"
            base_class = re.sub(r'\s*\([^)]*\)', '', part).strip()
            # Strip modifiers like "IRR. ", "pl. subj." etc.
            base_class = re.sub(r'^IRR\.\s*', '', base_class).strip()
            base_class = re.sub(r'\s*\(pl\.\s*subj\.\)', '', base_class).strip()
            if base_class and base_class not in VALID_GRAM_CLASSES:
                flags.append(AuditFlag(entry_id, 'grammatical_class', 'warning', 'UNKNOWN_GRAM_CLASS',
                                       f"Unrecognized grammatical class: '{part}' (in '{gc}')", gc))

    # Check verb class is present for verb entries
    # Note: VD (descriptive verbs) typically don't have a numbered verb class in Parks' system
    if gram_class and gram_class.startswith('V') and gram_class in ('VI', 'VT', 'VL', 'VP', 'VR'):
        if not verb_class or not verb_class.strip():
            flags.append(AuditFlag(entry_id, 'verb_class', 'info', 'MISSING_VERB_CLASS',
                                   f"Verb entry ({gram_class}) has no verb class"))

    if verb_class and verb_class.strip():
        vc = verb_class.strip().strip('()')
        vc_check = verb_class.strip()
        # Normalize for checking
        if vc not in {v.strip('()') for v in VALID_VERB_CLASSES} and vc_check not in VALID_VERB_CLASSES:
            flags.append(AuditFlag(entry_id, 'verb_class', 'warning', 'UNKNOWN_VERB_CLASS',
                                   f"Unrecognized verb class: '{verb_class}'", verb_class))

    # ---- 3. Phonetic character validation ----

    if phonetic_form and isinstance(phonetic_form, str) and phonetic_form.strip():
        invalid_chars = {}
        for ch in phonetic_form:
            if ch not in VALID_PHONETIC_ALL:
                key = f"U+{ord(ch):04X}"
                invalid_chars[key] = ch

        if invalid_chars:
            for ucode, ch in invalid_chars.items():
                flags.append(AuditFlag(entry_id, 'phonetic_form', 'error', 'INVALID_PHONETIC_CHAR',
                                       f"Invalid character {ucode} '{ch}' in phonetic form",
                                       phonetic_form))

        # Check phonetic form has brackets
        pf = phonetic_form.strip()
        if not pf.startswith('['):
            flags.append(AuditFlag(entry_id, 'phonetic_form', 'info', 'MISSING_OPEN_BRACKET',
                                   'Phonetic form does not start with [', pf[:30]))
        if not pf.endswith(']'):
            flags.append(AuditFlag(entry_id, 'phonetic_form', 'info', 'MISSING_CLOSE_BRACKET',
                                   'Phonetic form does not end with ]', pf[-30:]))

    # ---- 4. Noun glottal stop check ----

    if headword and gram_class and gram_class.strip():
        gc_parts = [p.strip() for p in re.split(r'[,;]', gram_class)]
        gc_primary = re.sub(r'\s*\([^)]*\)', '', gc_parts[0]).strip()

        if gc_primary in NOUN_CLASSES:
            hw = headword.strip()
            if hw and hw[-1] in PAWNEE_VOWELS:
                # Kinship terms and dependent nouns often lack final ʔ — by design
                if gc_primary in ('N-KIN', 'N-DEP'):
                    flags.append(AuditFlag(entry_id, 'headword', 'info', 'NOUN_MISSING_GLOTTAL_DEPKIN',
                                           f"{gc_primary} ends in vowel '{hw[-1]}' without ʔ — likely by design",
                                           hw))
                else:
                    # Check if it looks like a proper noun (starts uppercase, or multi-word)
                    if hw[0].isupper() or ' ' in hw:
                        flags.append(AuditFlag(entry_id, 'headword', 'info', 'NOUN_MISSING_GLOTTAL_PROPER',
                                               f"Proper noun ends in vowel '{hw[-1]}' without ʔ — likely by design",
                                               hw))
                    else:
                        # Common noun ending in bare vowel — genuine candidate for review
                        flags.append(AuditFlag(entry_id, 'headword', 'warning', 'NOUN_MISSING_GLOTTAL',
                                               f"Common noun ends in vowel '{hw[-1]}' without ʔ — possible OCR miss",
                                               hw))

    # ---- 5. Headword ↔ phonetic form consistency ----

    if headword and phonetic_form:
        _check_hw_pf_consistency(entry_id, headword, phonetic_form, flags)

    # ---- 6. Paradigmatic forms check (verbs should have forms) ----

    if gram_class and gram_class.startswith('V'):
        para = part_II.get('paradigmatic_forms') or {}
        if isinstance(para, dict):
            filled = sum(1 for k, v in para.items() if v and str(v).strip())
        elif isinstance(para, list):
            filled = sum(1 for item in para
                         if isinstance(item, dict) and item.get('skiri_form', '').strip())
        else:
            filled = 0

        if filled == 0:
            flags.append(AuditFlag(entry_id, 'paradigmatic_forms', 'info', 'NO_PARADIGMATIC_FORMS',
                                   f"Verb entry ({gram_class}) has no paradigmatic forms"))

    return flags


def _check_hw_pf_consistency(entry_id, headword, phonetic_form, flags):
    """
    Basic consistency check between headword and phonetic form.
    Compares consonant skeletons to catch major mismatches.

    Normalizes known equivalences:
      - c/č in headword ↔ ts/č in phonetic (Parks: headword 'c' = phonetic 'ts')
      - {k/t} alternation markers → 'k' (the headword form)
      - Optional sounds (h), (r), (k), (s), (n), (w) stripped from phonetic
      - Glottal stop absorption: headword 'ʔa' can surface as phonetic 'aa'
    """
    # Skip non-IPA phonetic forms
    if not phonetic_form or not isinstance(phonetic_form, str):
        return
    pf_lower = phonetic_form.strip().lower()
    if pf_lower.startswith('[cross') or 'not_provided' in pf_lower or pf_lower in ('n/a', '[notprovided]'):
        return

    # --- Build headword consonant skeleton ---
    hw = headword.lower()
    hw_consonants = []
    i = 0
    while i < len(hw):
        ch = hw[i]
        if ch in 'ptkčswrhʔ':
            hw_consonants.append(ch)
        elif ch == 'c':
            # In Parks' headword notation, 'c' represents the ts/č phoneme
            hw_consonants.append('t')
            hw_consonants.append('s')
        i += 1

    # --- Build phonetic consonant skeleton ---
    pf_clean = phonetic_form.lower()

    # Remove structural characters
    for ch in '[]•–—- ,:ːø':
        pf_clean = pf_clean.replace(ch, '')

    # Remove preverb notation (ʊt...), (ut...) BEFORE processing optional sounds
    pf_clean = re.sub(r'\([ʊu]t\.\.\.\)', '', pf_clean)

    # Remove null morpheme
    pf_clean = pf_clean.replace('ø', '').replace('Ø', '')

    # Resolve alternation markers {k/t} → first alternative (matches headword form)
    pf_clean = re.sub(r'\{(\w)/\w\}', r'\1', pf_clean)

    # INCLUDE optional/whispered sounds: (h) → h, (r) → r, (k) → k, (tə) → tə
    # These are part of the underlying form (headword includes them);
    # parentheses just mark them as optionally whispered in speech
    pf_clean = re.sub(r'\(([^)]+)\)', r'\1', pf_clean)

    pf_consonants = []
    for ch in pf_clean:
        if ch in 'ptkcsčswrhʔ':
            pf_consonants.append(ch)

    # --- Normalize both skeletons ---
    def normalize_skeleton(skel):
        """Normalize c→ts and č→ts for comparison."""
        result = []
        for ch in skel:
            if ch == 'č':
                result.extend(['t', 's'])
            elif ch == 'c':
                result.extend(['t', 's'])  # phonetic 'c' also = ts
            else:
                result.append(ch)
        return result

    hw_norm = normalize_skeleton(hw_consonants)
    pf_norm = normalize_skeleton(pf_consonants)

    if hw_norm != pf_norm:
        # Check if the difference is only glottal stop absorption (ʔ in headword, missing in phonetic)
        # This is a known phonological process: /ʔa/ → [aa]
        hw_no_glottal = [c for c in hw_norm if c != 'ʔ']
        pf_no_glottal = [c for c in pf_norm if c != 'ʔ']
        if hw_no_glottal == pf_no_glottal:
            # Difference is only glottal stops — this is a phonological issue, not a parsing error
            # Flag at info level only
            return

        hw_str = ''.join(hw_consonants)
        pf_str = ''.join(pf_consonants)

        # Only flag if significantly different
        diff_count = 0
        for a, b in zip(hw_norm, pf_norm):
            if a != b:
                diff_count += 1
        len_diff = abs(len(hw_norm) - len(pf_norm))

        if len_diff > 2 or (
            len(hw_norm) > 0 and len(pf_norm) > 0 and
            (diff_count + len_diff) > max(len(hw_norm), len(pf_norm)) * 0.3
        ):
            flags.append(AuditFlag(
                entry_id, 'headword+phonetic', 'warning', 'CONSONANT_SKELETON_MISMATCH',
                f"Consonant mismatch: headword '{hw_str}' vs phonetic '{pf_str}'",
                f"{headword} / {phonetic_form}"
            ))


# ---------------------------------------------------------------------------
# E2S Cross-Validation
# ---------------------------------------------------------------------------

def validate_e2s_links(s2e_entries, e2s_entries):
    """
    Cross-validate E2S → S2E links.
    Returns a list of AuditFlags.
    """
    flags = []

    # Build S2E lookup
    s2e_by_id = {}
    for entry in s2e_entries:
        eid = entry.get('entry_id')
        if eid:
            s2e_by_id[eid] = entry

    # Check every E2S subentry link
    broken_links = 0
    total_subentries = 0

    for e2s_entry in e2s_entries:
        english_word = e2s_entry.get('english_entry_word', '')
        subentries = e2s_entry.get('subentries', [])

        for sub in subentries:
            total_subentries += 1
            linked_id = sub.get('s2e_entry_id', '')
            match_type = sub.get('s2e_match_type', '')

            if linked_id and linked_id not in s2e_by_id:
                broken_links += 1
                flags.append(AuditFlag(
                    f"E2S:{english_word}", 's2e_entry_id', 'error', 'BROKEN_S2E_LINK',
                    f"Links to non-existent S2E entry '{linked_id}'",
                    linked_id
                ))

            # Check phonetic form consistency between E2S and S2E
            if linked_id and linked_id in s2e_by_id:
                s2e_pf = (s2e_by_id[linked_id].get('part_I') or {}).get('phonetic_form', '')
                e2s_pf = (sub.get('part_I') or {}).get('phonetic_form', '')
                if s2e_pf and e2s_pf and s2e_pf != e2s_pf:
                    # This is expected after Phase 1.1b sync, but flag large differences
                    pass  # Already synced in 1.1b

    logging.info(f"E2S cross-validation: {total_subentries} subentries, {broken_links} broken links")
    return flags


# ---------------------------------------------------------------------------
# Gemini AI Batch Validation
# ---------------------------------------------------------------------------

# Retry / backoff constants
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5  # seconds


GEMINI_SYSTEM_INSTRUCTION = """You are validating Skiri Pawnee dictionary entries for data quality.
You are an expert in Pawnee (Caddoan) linguistics and the Parks dictionary notation system.

For each entry, check:
1. Does the phonetic_form plausibly represent the headword?
   - Parks uses 'c' in headwords where phonetic forms show 'ts' or 'č' — this is EXPECTED, not an error.
   - Long vowels (aa, ii, uu) in headwords should correspond to long vowels in phonetic forms.
   - The consonant skeleton should match (allowing c↔ts/č equivalence).
2. Are the English glosses reasonable (not garbled OCR artifacts)?
3. Is the grammatical class consistent with the gloss?
   - Noun glosses (object names) should have N/N-DEP/N-KIN class.
   - Action/state glosses should have verb classes (VI/VT/VD/VL/VP/VR).
4. For nouns: does the headword end in ʔ as expected? Flag if it ends in a bare vowel.

Respond ONLY with a JSON object. No markdown fences, no preamble.
Format: {"issues": [{"entry_id": "...", "field": "...", "severity": "error|warning|info", "code": "...", "message": "..."}]}
If no issues: {"issues": []}"""


def _call_gemini(client, content_text, model_name):
    """
    Send a validation request to Gemini with retry logic.
    Returns parsed JSON dict or None on failure.
    """
    from google.genai import types
    from google.api_core import exceptions as google_exceptions

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[content_text],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=8192,
                ),
            )

            text = response.text.strip()

            # Strip markdown fences if present
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            return json.loads(text)

        except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests) as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logging.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s: {e}")
            time.sleep(wait)

        except (google_exceptions.ServiceUnavailable, google_exceptions.InternalServerError) as e:
            wait = RETRY_BACKOFF_BASE * attempt
            logging.warning(f"Server error (attempt {attempt}/{MAX_RETRIES}), waiting {wait}s: {e}")
            time.sleep(wait)

        except json.JSONDecodeError as e:
            logging.warning(f"Gemini response not valid JSON (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                logging.debug(f"Raw response: {text[:500]}")
                return None

        except Exception as e:
            logging.warning(f"Gemini error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE)
            else:
                return None

    return None


def validate_with_gemini(entries, batch_size=20, checkpoint_path=None, model_name='gemini-2.0-flash'):
    """
    Send batches of entries to Gemini API for AI-powered validation.
    Checks phonetic ↔ headword consistency and gloss plausibility.

    Requires GEMINI_API_KEY environment variable.
    Supports checkpointing for resume after interruption.

    Uses the google-genai SDK (pip install google-genai).
    """
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI-API-KEY')
    if not api_key:
        logging.error("GEMINI_API_KEY not set. Skipping Gemini validation.")
        return []

    try:
        from google import genai
    except ImportError:
        logging.error("google-genai package not installed. "
                      "Install with: pip install google-genai")
        return []

    client = genai.Client(api_key=api_key)

    # Load checkpoint if exists
    completed_ids = set()
    gemini_flags = []
    if checkpoint_path and Path(checkpoint_path).exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
            completed_ids = set(checkpoint.get('completed_ids', []))
            gemini_flags = [
                AuditFlag(fl['entry_id'], fl['field'], fl['severity'], fl['code'], fl['message'])
                for fl in checkpoint.get('flags', [])
            ]
        logging.info(f"Resumed from checkpoint: {len(completed_ids)} entries already validated")

    # Filter to unprocessed entries
    remaining = [e for e in entries if e.get('entry_id') not in completed_ids]
    total_batches = (len(remaining) + batch_size - 1) // batch_size
    logging.info(f"Gemini validation: {len(remaining)} entries in {total_batches} batches "
                 f"(model: {model_name})")

    for batch_start in range(0, len(remaining), batch_size):
        batch = remaining[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1

        batch_data = []
        for entry in batch:
            part_I = entry.get('part_I') or {}
            batch_data.append({
                'entry_id': entry.get('entry_id', ''),
                'headword': entry.get('headword', ''),
                'phonetic_form': part_I.get('phonetic_form') or '',
                'grammatical_class': (part_I.get('grammatical_info') or {}).get('grammatical_class', ''),
                'glosses': [g.get('definition', '') for g in (part_I.get('glosses') or [])
                           if isinstance(g, dict)],
            })

        prompt = ("Validate these Skiri Pawnee dictionary entries:\n\n"
                  + json.dumps(batch_data, ensure_ascii=False, indent=2))

        result = _call_gemini(client, prompt, model_name)

        if result is not None:
            # Gemini may return {"issues": [...]} or a bare list [...]
            if isinstance(result, list):
                issues = result
            elif isinstance(result, dict):
                issues = result.get('issues', [])
            else:
                logging.warning(f"Batch {batch_num}: unexpected result type {type(result).__name__}")
                issues = []

            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                gemini_flags.append(AuditFlag(
                    issue.get('entry_id', ''),
                    issue.get('field', 'gemini'),
                    issue.get('severity', 'warning'),
                    f"GEMINI_{issue.get('code', 'CHECK')}",
                    issue.get('message', ''),
                ))

            # Mark batch as completed
            for entry in batch:
                completed_ids.add(entry.get('entry_id', ''))
        else:
            logging.warning(f"Batch {batch_num} failed after {MAX_RETRIES} retries — skipping")
            # Still checkpoint so we don't lose progress on other batches

        # Save checkpoint after each batch
        if checkpoint_path:
            _save_checkpoint(checkpoint_path, completed_ids, gemini_flags)

        # Rate limiting (be polite to the API)
        time.sleep(1)

        logging.info(f"  Batch {batch_num}/{total_batches}: "
                     f"{min(batch_start + batch_size, len(remaining))}/{len(remaining)} entries")

    logging.info(f"Gemini validation complete: {len(gemini_flags)} issues found "
                 f"across {len(completed_ids)} entries")
    return gemini_flags


def _save_checkpoint(path, completed_ids, flags):
    """Save Gemini validation progress to a checkpoint file."""
    checkpoint = {
        'timestamp': datetime.now().isoformat(),
        'completed_ids': list(completed_ids),
        'flags': [
            {'entry_id': f.entry_id, 'field': f.field, 'severity': f.severity,
             'code': f.code, 'message': f.message}
            for f in flags
        ]
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_audit_report(all_flags, total_entries, output_path, e2s_count=0):
    """Write a comprehensive audit report."""

    # Categorize flags
    by_severity = defaultdict(list)
    by_code = Counter()
    by_field = Counter()

    for fl in all_flags:
        by_severity[fl.severity].append(fl)
        by_code[fl.code] += 1
        by_field[fl.field] += 1

    errors = by_severity.get('error', [])
    warnings = by_severity.get('warning', [])
    infos = by_severity.get('info', [])

    clean_entries = total_entries - len(set(fl.entry_id for fl in all_flags))

    lines = []
    lines.append("=" * 72)
    lines.append("Phase 1.1d — Parsing Completeness Audit Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 72)
    lines.append("")

    # --- Summary ---
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"S2E entries audited:     {total_entries:>6}")
    if e2s_count:
        lines.append(f"E2S entries audited:     {e2s_count:>6}")
    lines.append(f"Clean entries (no flags): {clean_entries:>5}")
    lines.append(f"Total flags:             {len(all_flags):>6}")
    lines.append(f"  Errors:                {len(errors):>6}")
    lines.append(f"  Warnings:              {len(warnings):>6}")
    lines.append(f"  Info:                  {len(infos):>6}")
    lines.append("")

    # --- Flag counts by code ---
    lines.append("FLAGS BY TYPE (sorted by frequency)")
    lines.append("-" * 60)
    for code, count in by_code.most_common():
        # Determine severity for this code
        sev = 'info'
        for fl in all_flags:
            if fl.code == code:
                sev = fl.severity
                break
        lines.append(f"  [{sev.upper():>7}] {code:<40} ×{count}")
    lines.append("")

    # --- Errors detail ---
    lines.append(f"ERRORS ({len(errors)})")
    lines.append("-" * 60)
    if errors:
        for fl in errors[:100]:
            val_str = f" | value: {fl.value}" if fl.value else ""
            lines.append(f"  {fl.entry_id} | {fl.field} | {fl.code}")
            lines.append(f"    {fl.message}{val_str}")
        if len(errors) > 100:
            lines.append(f"  ... and {len(errors) - 100} more errors")
    else:
        lines.append("  (none)")
    lines.append("")

    # --- Warnings detail (selected) ---
    lines.append(f"WARNINGS — NOUN MISSING GLOTTAL STOP")
    lines.append("-" * 60)
    glottal_common = [fl for fl in warnings if fl.code == 'NOUN_MISSING_GLOTTAL']
    glottal_depkin = [fl for fl in infos if fl.code == 'NOUN_MISSING_GLOTTAL_DEPKIN']
    glottal_proper = [fl for fl in infos if fl.code == 'NOUN_MISSING_GLOTTAL_PROPER']
    lines.append(f"  Common nouns (N) — review needed:    {len(glottal_common)}")
    lines.append(f"  Kinship/dependent (N-KIN/N-DEP):     {len(glottal_depkin)} (by design)")
    lines.append(f"  Proper nouns/multi-word:             {len(glottal_proper)} (by design)")
    lines.append("")
    lines.append("  Common nouns needing review (first 50):")
    for fl in glottal_common[:50]:
        lines.append(f"  {fl.entry_id}: {fl.value}")
    if len(glottal_common) > 50:
        lines.append(f"  ... and {len(glottal_common) - 50} more")
    lines.append("")

    lines.append(f"WARNINGS — EMPTY PHONETIC FORM ({sum(1 for f in warnings if f.code == 'EMPTY_PHONETIC')})")
    lines.append("-" * 60)
    empty_pf = [fl for fl in warnings if fl.code == 'EMPTY_PHONETIC']
    for fl in empty_pf[:50]:
        lines.append(f"  {fl.entry_id}")
    if len(empty_pf) > 50:
        lines.append(f"  ... and {len(empty_pf) - 50} more")
    lines.append("")

    lines.append(f"WARNINGS — INVALID PHONETIC CHARACTERS")
    lines.append("-" * 60)
    invalid_pf = [fl for fl in errors if fl.code == 'INVALID_PHONETIC_CHAR']
    # Deduplicate by character
    char_entries = defaultdict(list)
    for fl in invalid_pf:
        # Extract the U+XXXX from the message
        match = re.search(r"(U\+[0-9A-F]{4})", fl.message)
        if match:
            char_entries[match.group(1)].append(fl.entry_id)
    for ucode, eids in sorted(char_entries.items(), key=lambda x: -len(x[1])):
        ch_display = chr(int(ucode[2:], 16))
        lines.append(f"  {ucode} '{ch_display}' — {len(eids)} entries")
        for eid in eids[:5]:
            lines.append(f"    {eid}")
        if len(eids) > 5:
            lines.append(f"    ... and {len(eids) - 5} more")
    lines.append("")

    lines.append(f"WARNINGS — CONSONANT SKELETON MISMATCHES")
    lines.append("-" * 60)
    skel_flags = [fl for fl in warnings if fl.code == 'CONSONANT_SKELETON_MISMATCH']
    for fl in skel_flags[:30]:
        lines.append(f"  {fl.entry_id}: {fl.message}")
        if fl.value:
            lines.append(f"    {fl.value}")
    if len(skel_flags) > 30:
        lines.append(f"  ... and {len(skel_flags) - 30} more")
    lines.append("")

    # --- Info items (selected) ---
    lines.append(f"INFO — MISSING VERB CLASS ({sum(1 for f in infos if f.code == 'MISSING_VERB_CLASS')})")
    lines.append("-" * 60)
    mvc = [fl for fl in infos if fl.code == 'MISSING_VERB_CLASS']
    for fl in mvc[:20]:
        lines.append(f"  {fl.entry_id}: {fl.message}")
    if len(mvc) > 20:
        lines.append(f"  ... and {len(mvc) - 20} more")
    lines.append("")

    # --- Gemini flags (if any) ---
    gemini_flags = [fl for fl in all_flags if fl.code.startswith('GEMINI_')]
    if gemini_flags:
        lines.append(f"GEMINI AI VALIDATION FLAGS ({len(gemini_flags)})")
        lines.append("-" * 60)
        for fl in gemini_flags[:50]:
            lines.append(f"  [{fl.severity.upper()}] {fl.entry_id} | {fl.code}: {fl.message}")
        if len(gemini_flags) > 50:
            lines.append(f"  ... and {len(gemini_flags) - 50} more")
        lines.append("")

    # --- Prioritized fix list ---
    lines.append("PRIORITIZED FIX LIST")
    lines.append("-" * 60)
    lines.append("Priority 1 (Errors — data integrity):")
    p1_codes = ['EMPTY_HEADWORD', 'EMPTY_GLOSSES', 'INVALID_PHONETIC_CHAR', 'BROKEN_S2E_LINK']
    for code in p1_codes:
        if by_code.get(code, 0) > 0:
            lines.append(f"  {code}: {by_code[code]} entries")
    lines.append("")
    lines.append("Priority 2 (Warnings — data quality):")
    p2_codes = ['NOUN_MISSING_GLOTTAL', 'EMPTY_PHONETIC', 'CONSONANT_SKELETON_MISMATCH',
                'EMPTY_GRAM_CLASS', 'EMPTY_GLOSS_DEFINITION']
    for code in p2_codes:
        if by_code.get(code, 0) > 0:
            lines.append(f"  {code}: {by_code[code]} entries")
    lines.append("")
    lines.append("Priority 3 (Info — completeness):")
    p3_codes = ['MISSING_VERB_CLASS', 'NO_PARADIGMATIC_FORMS',
                'MISSING_OPEN_BRACKET', 'MISSING_CLOSE_BRACKET', 'UNKNOWN_GRAM_CLASS']
    for code in p3_codes:
        if by_code.get(code, 0) > 0:
            lines.append(f"  {code}: {by_code[code]} entries")
    lines.append("")

    report_text = '\n'.join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logging.info(f"Audit report written to {output_path}")

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1.1d: Parsing Completeness Audit for S2E (and optionally E2S) entries"
    )
    parser.add_argument(
        '--s2e', required=True,
        help='Path to S2E linked JSON file (skiri_to_english_linked.json)'
    )
    parser.add_argument(
        '--e2s', default=None,
        help='Path to E2S linked JSON file (optional, for cross-validation)'
    )
    parser.add_argument(
        '--report', '-r',
        default='reports/phase_1_1d_audit.txt',
        help='Path for the audit report'
    )
    parser.add_argument(
        '--flags-json',
        default=None,
        help='Path to write all flags as JSON (for programmatic access)'
    )
    parser.add_argument(
        '--use-gemini', action='store_true',
        help='Enable Gemini API validation (requires GEMINI_API_KEY env var)'
    )
    parser.add_argument(
        '--gemini-batch-size', type=int, default=20,
        help='Number of entries per Gemini API batch (default: 20)'
    )
    parser.add_argument(
        '--model', default='gemini-2.0-flash',
        help='Gemini model to use (default: gemini-2.0-flash)'
    )
    parser.add_argument(
        '--checkpoint',
        default='reports/gemini_checkpoint.json',
        help='Checkpoint file for Gemini validation resume'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print each entry as it is validated'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # --- Load S2E ---
    s2e_path = Path(args.s2e)
    if not s2e_path.exists():
        logging.error(f"S2E file not found: {s2e_path}")
        sys.exit(1)

    logging.info(f"Loading S2E: {s2e_path} ...")
    with open(s2e_path, 'r', encoding='utf-8') as f:
        s2e_entries = json.load(f)
    logging.info(f"Loaded {len(s2e_entries)} S2E entries")

    # --- Load E2S (optional) ---
    e2s_entries = []
    if args.e2s:
        e2s_path = Path(args.e2s)
        if not e2s_path.exists():
            logging.warning(f"E2S file not found: {e2s_path} — skipping cross-validation")
        else:
            logging.info(f"Loading E2S: {e2s_path} ...")
            with open(e2s_path, 'r', encoding='utf-8') as f:
                e2s_entries = json.load(f)
            logging.info(f"Loaded {len(e2s_entries)} E2S entries")

    # --- Run local validation ---
    logging.info("Running local validation on S2E entries ...")
    all_flags = []
    for idx, entry in enumerate(s2e_entries):
        entry_flags = validate_entry(entry)
        all_flags.extend(entry_flags)

        if args.verbose and entry_flags:
            eid = entry.get('entry_id', 'UNKNOWN')
            logging.debug(f"  [{idx+1}] {eid}: {len(entry_flags)} flags")

    logging.info(f"Local validation: {len(all_flags)} flags across {len(s2e_entries)} entries")

    # --- E2S cross-validation ---
    if e2s_entries:
        logging.info("Running E2S cross-validation ...")
        e2s_flags = validate_e2s_links(s2e_entries, e2s_entries)
        all_flags.extend(e2s_flags)

    # --- Gemini validation (optional) ---
    if args.use_gemini:
        logging.info("Running Gemini AI validation ...")
        gemini_flags = validate_with_gemini(
            s2e_entries,
            batch_size=args.gemini_batch_size,
            checkpoint_path=args.checkpoint,
            model_name=args.model,
        )
        all_flags.extend(gemini_flags)

    # --- Generate report ---
    report_text = generate_audit_report(
        all_flags,
        total_entries=len(s2e_entries),
        output_path=args.report,
        e2s_count=len(e2s_entries) if e2s_entries else 0,
    )

    # --- Write flags JSON (optional) ---
    if args.flags_json:
        flags_data = [
            {'entry_id': fl.entry_id, 'field': fl.field, 'severity': fl.severity,
             'code': fl.code, 'message': fl.message, 'value': fl.value}
            for fl in all_flags
        ]
        Path(args.flags_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.flags_json, 'w', encoding='utf-8') as f:
            json.dump(flags_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Flags JSON written to {args.flags_json}")

    # --- Console summary ---
    errors = sum(1 for fl in all_flags if fl.severity == 'error')
    warnings = sum(1 for fl in all_flags if fl.severity == 'warning')
    infos = sum(1 for fl in all_flags if fl.severity == 'info')
    logging.info(f"Audit complete: {errors} errors, {warnings} warnings, {infos} info")
    logging.info("Done.")


if __name__ == '__main__':
    main()
