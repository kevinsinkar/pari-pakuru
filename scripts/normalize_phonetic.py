#!/usr/bin/env python3
"""
normalize_phonetic.py — Normalize OCR artifacts across ALL fields in the dictionary.

Place in: pari-pakuru/scripts/

Recursively walks every string value in every entry and fixes OCR/encoding
corruptions from PDF parsing. No field is missed — headwords, phonetic forms,
etymologies, cognates, paradigmatic forms, examples, derived stems, glosses,
compound structures — everything.

Special handling for phonetic_form fields only:
  - ? → ʔ  (question marks are glottal stops in phonetic context)
  - Whitespace is stripped (spaces inside brackets are PDF artifacts)

Usage:
    python normalize_phonetic.py                     # Normalize both dictionaries
    python normalize_phonetic.py --dry-run           # Preview changes without writing
    python normalize_phonetic.py --s2e-only          # Normalize S2E only
    python normalize_phonetic.py --e2s-only          # Normalize E2S only

No API key required. Purely local.
"""

import json
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DICT_DATA_DIR = PROJECT_ROOT / "Dictionary Data"

S2E_JSON = DICT_DATA_DIR / "skiri_to_english_complete.json"
E2S_JSON = DICT_DATA_DIR / "english_to_skiri_complete.json"

NORMALIZED_S2E = DICT_DATA_DIR / "skiri_to_english_normalized.json"
NORMALIZED_E2S = DICT_DATA_DIR / "english_to_skiri_normalized.json"
NORMALIZATION_LOG = DICT_DATA_DIR / "normalization_changelog.json"
LOG_FILE = SCRIPT_DIR / "normalize_phonetic.log"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("normalize_phonetic")


# ===========================================================================
#  CHARACTER NORMALIZATION MAPS
# ===========================================================================
# OCR corruptions identified by visual comparison against source dictionary PDFs.
#
# GLOBAL_CHAR_MAP — applied to EVERY string in every entry. These corrupted
#   characters do not legitimately appear in English or Skiri text.
#
# PHONETIC_EXTRA — applied ONLY to phonetic_form fields:
#   ? → ʔ  (question marks are legitimate in English glosses/definitions)
#
# PRESERVED (not in any map):
#   •  (U+2022) — syllable separator
#   –  (U+2013) — stem boundary marker
# ===========================================================================

GLOBAL_CHAR_MAP = {
    '\u2122': '\u0294',   # ™  →  ʔ  (IPA glottal stop, U+0294)
    '\u00ae': '\u0294',   # ®  →  ʔ  (Parks glottal stop → IPA)
    '\u00d9': '\u010d',   # Ù  →  č  (c-hacek, U+010D)
    '\u2021': '\u00ed',   # ‡  →  í  (i-acute, U+00ED)
    '\u00d1': '\u00e1',   # Ñ  →  á  (a-acute, U+00E1)
    '\u2030': '\u028a',   # ‰  →  ʊ  (IPA near-close back rounded, U+028A)
    '\u2020': '\u026a',   # †  →  ɪ  (IPA near-close near-front, U+026A)
    '\u00e6': '\u00ed',   # æ  →  í  (i-acute, U+00ED)
    '\u00df': '\u0259',   # ß  →  ə  (IPA schwa, U+0259)
    '\u0160': '\u028a',   # Š  →  ʊ  (IPA near-close back rounded, U+028A)
}

PHONETIC_EXTRA_MAP = {
    '?': '\u0294',        # ?  →  ʔ  (phonetic_form ONLY)
}

CHAR_MAP_DISPLAY = {
    '\u2122': 'ʔ  glottal stop (™ → U+0294)',
    '\u00ae': 'ʔ  glottal stop (® Parks → U+0294)',
    '?':      'ʔ  glottal stop (? OCR → U+0294, phonetic_form only)',
    '\u00d9': 'č  c-hacek (Ù → U+010D)',
    '\u2021': 'í  i-acute (‡ → U+00ED)',
    '\u00d1': 'á  a-acute (Ñ → U+00E1)',
    '\u2030': 'ʊ  near-close back rounded (‰ → U+028A)',
    '\u2020': 'ɪ  near-close near-front († → U+026A)',
    '\u00e6': 'í  i-acute (æ → U+00ED)',
    '\u00df': 'ə  schwa (ß → U+0259)',
    '\u0160': 'ʊ  near-close back rounded (Š → U+028A)',
}


# ===========================================================================
#  CORE: Apply character map to a string
# ===========================================================================

def normalize_string(raw: str, char_map: dict) -> tuple:
    """
    Apply character map to a string.
    Returns (normalized_string, list_of_changes).
    """
    if not raw:
        return raw, []

    changes = []
    result = []

    for i, ch in enumerate(raw):
        if ch in char_map:
            replacement = char_map[ch]
            changes.append({
                "position": i,
                "original": ch,
                "original_unicode": f"U+{ord(ch):04X}",
                "replacement": replacement,
                "replacement_unicode": f"U+{ord(replacement):04X}",
            })
            result.append(replacement)
        else:
            result.append(ch)

    return ''.join(result), changes


# ===========================================================================
#  RECURSIVE WALKER — normalizes every string in any structure
# ===========================================================================

def normalize_recursive(obj, path, field_changes, is_phonetic_form=False):
    """
    Recursively walk a dict/list/string and normalize all strings in-place.

    For phonetic_form fields (detected by key name), also applies:
      - PHONETIC_EXTRA_MAP (? → ʔ)
      - Whitespace stripping

    Args:
        obj: the object to walk (dict, list, or string — but strings
             are handled by the caller since they're immutable)
        path: current dot-notation path for logging
        field_changes: list to append change records to
        is_phonetic_form: True if the current context is a phonetic_form field
    """
    if isinstance(obj, dict):
        for key in obj:
            val = obj[key]
            child_path = f"{path}.{key}" if path else key

            # Detect phonetic_form fields by key name
            child_is_phonetic = (key == "phonetic_form")

            if isinstance(val, str):
                normalized = _normalize_one_string(
                    val, child_path, field_changes, child_is_phonetic
                )
                if normalized != val:
                    obj[key] = normalized

            elif isinstance(val, (dict, list)):
                normalize_recursive(val, child_path, field_changes, child_is_phonetic)

    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            child_path = f"{path}[{i}]"

            if isinstance(val, str):
                normalized = _normalize_one_string(
                    val, child_path, field_changes, is_phonetic_form
                )
                if normalized != val:
                    obj[i] = normalized

            elif isinstance(val, (dict, list)):
                normalize_recursive(val, child_path, field_changes, is_phonetic_form)


def _normalize_one_string(val: str, path: str, field_changes: list,
                           is_phonetic_form: bool) -> str:
    """
    Normalize a single string value. Returns the (possibly modified) string.

    All strings: character map + strip leading/trailing whitespace.
    phonetic_form only: also strip ALL internal whitespace.
    """
    if not val:
        return val

    # Build the appropriate char map
    if is_phonetic_form:
        char_map = {**GLOBAL_CHAR_MAP, **PHONETIC_EXTRA_MAP}
    else:
        char_map = GLOBAL_CHAR_MAP

    normalized, changes = normalize_string(val, char_map)

    # ALL strings: strip leading/trailing whitespace
    before_trim = normalized
    normalized = normalized.strip()
    if normalized != before_trim:
        changes.append({
            "position": -1,
            "original": "(leading/trailing whitespace)",
            "original_unicode": "U+0020",
            "replacement": "(trimmed)",
            "replacement_unicode": "",
        })

    # Phonetic form ONLY: also strip ALL internal whitespace
    if is_phonetic_form:
        before_strip = normalized
        normalized = ''.join(normalized.split())
        if normalized != before_strip:
            changes.append({
                "position": -1,
                "original": "(internal whitespace)",
                "original_unicode": "U+0020",
                "replacement": "(removed)",
                "replacement_unicode": "",
            })

    if changes:
        field_changes.append({
            "field": path,
            "original": val,
            "normalized": normalized,
            "changes": changes,
        })

    return normalized


# ===========================================================================
#  ENTRY-LEVEL PROCESSING
# ===========================================================================

def normalize_entry(entry: dict, source: str) -> dict:
    """
    Normalize all strings in a single entry (S2E or E2S).
    Returns a changelog record, or None if no changes.
    """
    # Grab identifier before normalization
    if source == "s2e":
        entry_id = entry.get("headword", "<unknown>")
    else:
        entry_id = entry.get("english_entry_word", "<unknown>")

    field_changes = []
    normalize_recursive(entry, "", field_changes)

    if field_changes:
        record = {
            "source": source,
            "entry_id_before": entry_id,
            "field_changes": field_changes,
        }
        # Grab identifier after normalization (it may have changed)
        if source == "s2e":
            record["entry_id_after"] = entry.get("headword", "")
        else:
            record["entry_id_after"] = entry.get("english_entry_word", "")
        return record

    return None


# ===========================================================================
#  FILE I/O
# ===========================================================================

def load_json(path: Path) -> list:
    if not path.exists():
        log.error(f"File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        log.info(f"Loaded {len(data)} entries from {path.name}")
        return data
    elif isinstance(data, dict):
        for key in ("entries", "data", "results"):
            if key in data and isinstance(data[key], list):
                log.info(f"Loaded {len(data[key])} entries from {path.name}['{key}']")
                return data[key]
        return [data]
    return []


def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} items → {path.name}")


# ===========================================================================
#  MAIN
# ===========================================================================

def run(dry_run=False, s2e_only=False, e2s_only=False):
    log.info("=" * 60)
    log.info("FULL RECURSIVE NORMALIZATION")
    log.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    log.info("=" * 60)

    all_changelog = []
    char_stats = {}
    field_stats = {}

    # --- S2E ---
    if not e2s_only:
        s2e = load_json(S2E_JSON)
        if s2e:
            s2e_count = 0
            for entry in s2e:
                record = normalize_entry(entry, "s2e")
                if record:
                    all_changelog.append(record)
                    s2e_count += 1
            if not dry_run:
                save_json(s2e, NORMALIZED_S2E)
            log.info(f"S2E: {s2e_count} / {len(s2e)} entries modified")

    # --- E2S ---
    if not s2e_only:
        e2s = load_json(E2S_JSON)
        if e2s:
            e2s_count = 0
            for entry in e2s:
                record = normalize_entry(entry, "e2s")
                if record:
                    all_changelog.append(record)
                    e2s_count += 1
            if not dry_run:
                save_json(e2s, NORMALIZED_E2S)
            log.info(f"E2S: {e2s_count} / {len(e2s)} entries modified")

    # --- Aggregate stats ---
    for record in all_changelog:
        for fc in record.get("field_changes", []):
            # Field stats
            simple_field = re.sub(r'\[\d+\]', '[*]', fc["field"])
            field_stats[simple_field] = field_stats.get(simple_field, 0) + 1

            # Character stats
            for ch in fc.get("changes", []):
                orig = ch["original"]
                if orig != "(whitespace)":
                    char_stats[orig] = char_stats.get(orig, 0) + 1

    # --- Save changelog ---
    if not dry_run:
        save_json(all_changelog, NORMALIZATION_LOG)

    # --- Print summary ---
    log.info("")
    log.info("=" * 60)
    log.info(f"RESULTS {'(DRY RUN)' if dry_run else ''}")
    log.info("=" * 60)
    log.info(f"Total entries modified: {len(all_changelog)}")
    log.info("")

    if char_stats:
        total_replacements = sum(char_stats.values())
        log.info(f"Total character replacements: {total_replacements}")
        log.info("")
        log.info("By character:")
        log.info(f"  {'Char':<6s} {'Unicode':<10s} {'Count':>6s}   Corrected To")
        log.info(f"  {'─'*6} {'─'*10} {'─'*6}   {'─'*40}")
        for char, count in sorted(char_stats.items(), key=lambda x: -x[1]):
            display = CHAR_MAP_DISPLAY.get(char, f"U+{ord(char):04X}")
            log.info(f"  '{char}'    U+{ord(char):04X}     {count:>5d}   {display}")

        log.info("")
        log.info("By field (top 20):")
        for field, count in sorted(field_stats.items(), key=lambda x: -x[1])[:20]:
            log.info(f"  {count:>5d}   {field}")
    else:
        log.info("No corrections needed — all fields are already clean.")

    log.info("")
    if not dry_run and all_changelog:
        log.info("Files written:")
        if not e2s_only:
            log.info(f"  {NORMALIZED_S2E}")
        if not s2e_only:
            log.info(f"  {NORMALIZED_E2S}")
        log.info(f"  {NORMALIZATION_LOG}")
    elif dry_run:
        log.info("Dry run complete. Re-run without --dry-run to write files.")

    return all_changelog


def main():
    parser = argparse.ArgumentParser(
        description="Normalize OCR artifacts across ALL fields to IPA standard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Recursively walks every string in every entry. No field is missed.

Character corrections (applied to ALL string fields):
  ™  →  ʔ   (IPA glottal stop)        ®  →  ʔ   (Parks notation → IPA)
  Ù  →  č   (c-hacek)                 ‡  →  í   (i-acute)
  Ñ  →  á   (a-acute)                 ‰  →  ʊ   (IPA near-close back)
  †  →  ɪ   (IPA near-close front)    æ  →  í   (i-acute)
  ß  →  ə   (IPA schwa)              Š  →  ʊ   (IPA near-close back)

Phonetic_form only:
  ?  →  ʔ   (glottal stop)
  Whitespace removed

Preserved (NOT modified):
  •  (U+2022) — syllable separator
  –  (U+2013) — stem boundary marker

Examples:
  python normalize_phonetic.py                  # normalize both
  python normalize_phonetic.py --dry-run        # preview without writing
  python normalize_phonetic.py --s2e-only       # S2E only
        """
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--s2e-only", action="store_true",
                        help="Normalize Skiri-to-English only")
    parser.add_argument("--e2s-only", action="store_true",
                        help="Normalize English-to-Skiri only")

    args = parser.parse_args()
    if args.s2e_only and args.e2s_only:
        parser.error("Cannot use --s2e-only and --e2s-only together")

    run(dry_run=args.dry_run, s2e_only=args.s2e_only, e2s_only=args.e2s_only)


if __name__ == "__main__":
    main()
