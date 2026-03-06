#!/usr/bin/env python3
"""
phonetic_audit_agent.py — Phase 1.1: Pronunciation Respelling & Validation Agent

Place in: pari-pakuru/scripts/
Usage:
    python phonetic_audit_agent.py respell          # Generate respellings (local, no API)
    python phonetic_audit_agent.py validate          # AI-validate phonetic forms (uses Gemini)
    python phonetic_audit_agent.py audit             # Full audit: respell + validate + report
    python phonetic_audit_agent.py report            # Generate summary report from existing logs
    python phonetic_audit_agent.py validate --resume # Resume from last checkpoint

Requires: GEMINI_API_KEY environment variable (for validate/audit modes)
"""

import json
import os
import re
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# PATHS — relative to this script's location in scripts/
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DICT_DATA_DIR = PROJECT_ROOT / "Dictionary Data"

S2E_JSON = DICT_DATA_DIR / "skiri_to_english_complete.json"
E2S_JSON = DICT_DATA_DIR / "english_to_skiri_complete.json"

# Outputs
OUTPUT_DIR = DICT_DATA_DIR  # keep outputs alongside source data
AUDIT_LOG = SCRIPT_DIR / "phonetic_audit.log"
RESPELLING_OUTPUT_S2E = OUTPUT_DIR / "skiri_to_english_respelled.json"
RESPELLING_OUTPUT_E2S = OUTPUT_DIR / "english_to_skiri_respelled.json"
VALIDATION_LOG = OUTPUT_DIR / "phonetic_validation_results.json"
CHECKPOINT_FILE = OUTPUT_DIR / "phonetic_audit_checkpoint.json"
REPORT_FILE = OUTPUT_DIR / "phonetic_audit_report.md"

# Source PDFs for AI validation (page-by-page splits)
S2E_PAGES_DIR = DICT_DATA_DIR / "split_pdf_pages_SKIRI_TO_ENGLISH"
E2S_PAGES_DIR = DICT_DATA_DIR / "split_pdf_pages_ENGLISH_TO_SKIRI"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(AUDIT_LOG, mode="a"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("phonetic_audit")

# ===========================================================================
#  PART 1: DETERMINISTIC PRONUNCIATION RESPELLING ENGINE
#  No API calls. Pure local string transformation.
# ===========================================================================

# --- The Sound Key (Parks Dictionary, PDF 01 p. xvii) ---
# Maps Skiri orthographic symbols → English-approximation respelling

# Valid characters in a Parks phonetic form (after bracket stripping)
VALID_PHONETIC_CHARS = set(
    "aáàâãäåiíìîïuúùûüptkcswhræœøðñ®•–—−·.ː"
    "ɪɛɔʊəɑɨʌɯɤɵɐeEoO"  # IPA vowels sometimes seen
    "() {}/-+,;:' \"0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    " \t"
)

# Known grammatical class abbreviations
VALID_GRAM_CLASSES = {
    "N", "N-DEP", "N-KIN",
    "VI", "VT", "VD", "VL", "VP", "VR",
    "ADJ", "ADV", "NUM", "PRON", "DEM", "QUAN",
    "CONJ", "INTERJ", "LOC", "COLL",
    "ABS", "CONT", "INTER",
}

# Known verb classes
VALID_VERB_CLASSES = {
    "(1)", "(1-a)", "(1-i)",
    "(2)", "(2-i)",
    "(3)",
    "(4)", "(4-i)",
    "(u)", "(wi)",
}


class RespellingEngine:
    """
    Deterministic converter: Parks phonetic_form → simplified_pronunciation.
    
    Rules derived from Sound Key (PDF 01 p. xvii) and Blue Book alphabet.
    Processes left-to-right with longest-match-first tokenization.
    """

    # Ordered longest-first so 'aa' matches before 'a', 'ii' before 'i', etc.
    VOWEL_MAP = [
        # Long vowels (must come first)
        ("aa", "aah"),
        ("ii", "ee"),
        ("uu", "oo"),
        # Accented long vowels (acute accent on first char)
        ("áa", "AAH"),
        ("aá", "AAH"),
        ("íi", "EE"),
        ("ií", "EE"),
        ("úu", "OO"),
        ("uú", "OO"),
        # Accented short vowels → uppercase in respelling
        ("á", "AH"),
        ("í", "IH"),
        ("ú", "U"),
        # Short vowels
        ("a", "ah"),
        ("i", "ih"),
        ("u", "u"),
        # IPA variants sometimes found in parsed data
        ("ɪ", "ih"),
        ("ɛ", "eh"),
        ("ə", "uh"),
        ("ɑ", "aah"),
        ("ɔ", "aw"),
        ("e", "eh"),  # South Band vowel; Skiri maps to 'i'
        ("o", "oh"),  # rare
    ]

    CONSONANT_MAP = [
        # Multi-char first
        ("ts", "ts"),
        # Singles
        ("p", "p"),
        ("t", "t"),
        ("k", "k"),
        ("c", "ts"),   # Parks 'c' = Blue Book 'ts'
        ("s", "s"),
        ("w", "w"),
        ("r", "r"),
        ("h", "h"),
        ("®", "'"),    # glottal stop
        ("ʔ", "'"),    # IPA glottal stop variant
        ("'", "'"),    # apostrophe = glottal stop
        ("'", "'"),    # curly apostrophe
    ]

    SEPARATOR_MAP = [
        ("•", "-"),    # syllable bullet → hyphen
        ("·", "-"),    # middle dot variant
        (".", "-"),    # period used as syllable separator in some forms
    ]

    def __init__(self):
        # Build combined map, longest match first
        all_maps = self.VOWEL_MAP + self.CONSONANT_MAP + self.SEPARATOR_MAP
        # Sort by source length descending so 'aa' beats 'a'
        self.rules = sorted(all_maps, key=lambda x: len(x[0]), reverse=True)

    def clean_phonetic_form(self, raw: str) -> str:
        """
        Strip brackets, morpheme markers, alternation notation, 
        and grammatical annotations from the phonetic form.
        """
        s = raw.strip()

        # Remove enclosing brackets [...]
        if s.startswith("[") or s.startswith("["):
            s = s[1:]
        if s.endswith("]") or s.endswith("]"):
            s = s[:-1]

        # Remove leading/trailing dashes (stem boundary markers)
        s = s.strip("–—−-")

        # Remove alternation markers like {k/t}
        s = re.sub(r'\{[^}]*\}', '', s)

        # Remove parenthesized preverb notation like (ut...)
        s = re.sub(r'\([^)]*\.\.\.\)', '', s)

        # Remove remaining parentheses content that looks grammatical
        # but keep parenthesized pronunciation hints
        s = re.sub(r'\([A-Z][^)]*\)', '', s)

        # Collapse whitespace
        s = re.sub(r'\s+', ' ', s).strip()

        return s

    def respell(self, phonetic_form: str) -> str:
        """
        Convert a cleaned phonetic form into a simplified pronunciation string.
        Returns empty string if input is empty/unparseable.
        """
        if not phonetic_form or not phonetic_form.strip():
            return ""

        cleaned = self.clean_phonetic_form(phonetic_form)
        if not cleaned:
            return ""

        result = []
        i = 0
        while i < len(cleaned):
            matched = False
            for source, target in self.rules:
                if cleaned[i:i+len(source)] == source:
                    result.append(target)
                    i += len(source)
                    matched = True
                    break
            if not matched:
                char = cleaned[i]
                if char == ' ':
                    result.append(' ')
                elif char in '–—−':
                    result.append('-')
                elif char.isalpha():
                    # Unknown letter — pass through with warning marker
                    result.append(f"?{char}?")
                # Skip other unrecognized chars silently
                i += 1

        raw_respelling = ''.join(result)

        # Clean up: collapse multiple hyphens, trim
        raw_respelling = re.sub(r'-{2,}', '-', raw_respelling)
        raw_respelling = raw_respelling.strip('-').strip()

        # --- Accent propagation: capitalize entire syllable containing uppercase ---
        # Split on hyphens, find syllables with any uppercase (from accented vowels),
        # and capitalize the whole syllable.
        if '-' in raw_respelling:
            syllables = raw_respelling.split('-')
            processed = []
            for syl in syllables:
                if any(c.isupper() for c in syl):
                    processed.append(syl.upper())
                else:
                    processed.append(syl)
            raw_respelling = '-'.join(processed)
        else:
            # Single syllable — if it has any uppercase, capitalize all
            if any(c.isupper() for c in raw_respelling):
                raw_respelling = raw_respelling.upper()

        return raw_respelling

    def detect_accent(self, phonetic_form: str) -> bool:
        """Check if the phonetic form has an explicit accent mark."""
        return bool(re.search(r'[áíúàìùâîûãõ]', phonetic_form))


# ===========================================================================
#  PART 2: ENTRY FIELD VALIDATION (Local, no API)
# ===========================================================================

def validate_entry_fields_s2e(entry: dict) -> list:
    """
    Check a Skiri-to-English entry for completeness.
    Returns list of flag dicts.
    """
    flags = []
    entry_id = entry.get("headword", "<unknown>")

    # --- Part I checks ---
    part_i = entry.get("part_I", entry)  # handle both nested and flat

    headword = part_i.get("headword", "") or entry.get("headword", "")
    if not headword or not headword.strip():
        flags.append({"type": "incomplete_parse", "field": "headword",
                       "detail": "Headword is empty"})

    phonetic = part_i.get("phonetic_form", "") or entry.get("phonetic_form", "")
    if not phonetic or not phonetic.strip():
        flags.append({"type": "incomplete_parse", "field": "phonetic_form",
                       "detail": "Phonetic form is empty"})

    gram_class = ""
    gram_info = part_i.get("grammatical_info", entry.get("grammatical_info", {}))
    if isinstance(gram_info, dict):
        gram_class = gram_info.get("grammatical_class", "")
    elif isinstance(gram_info, str):
        gram_class = gram_info
    if not gram_class:
        flags.append({"type": "incomplete_parse", "field": "grammatical_class",
                       "detail": "Grammatical class is empty"})

    glosses = part_i.get("glosses", entry.get("glosses", []))
    if not glosses:
        flags.append({"type": "incomplete_parse", "field": "glosses",
                       "detail": "No glosses/definitions found"})

    # --- Phonetic form character validation ---
    if phonetic:
        cleaned = phonetic.strip("[] ")
        unknown_chars = []
        for ch in cleaned:
            if ch not in VALID_PHONETIC_CHARS and ch not in '®•·–—':
                unknown_chars.append(ch)
        if unknown_chars:
            flags.append({
                "type": "phonetic_char_error",
                "field": "phonetic_form",
                "detail": f"Unknown chars: {list(set(unknown_chars))}",
                "chars": list(set(unknown_chars))
            })

        # Check for syllable bullets
        if '•' not in cleaned and '·' not in cleaned:
            flags.append({
                "type": "missing_syllabification",
                "field": "phonetic_form",
                "detail": "No syllable bullets (•) found in phonetic form"
            })

    # --- Noun-specific: check for terminal glottal stop ---
    if gram_class in ("N", "N-DEP", "N-KIN") and headword:
        if not headword.endswith("®") and not headword.endswith("'"):
            # Many nouns end in -u® (nominative suffix)
            # Flag if noun doesn't end with glottal stop — possible OCR miss
            if headword.endswith(("u", "a", "i")):
                flags.append({
                    "type": "possible_ocr_glottal",
                    "field": "headword",
                    "detail": f"Noun '{headword}' ends in vowel without ® — possible OCR miss"
                })

    return flags


def validate_entry_fields_e2s(entry: dict) -> list:
    """
    Check an English-to-Skiri entry for completeness.
    Returns list of flag dicts.
    """
    flags = []
    entry_word = entry.get("english_entry_word", "<unknown>")

    if not entry_word or not entry_word.strip():
        flags.append({"type": "incomplete_parse", "field": "english_entry_word",
                       "detail": "English entry word is empty"})

    subentries = entry.get("skiri_subentries", [])
    if not subentries:
        flags.append({"type": "incomplete_parse", "field": "skiri_subentries",
                       "detail": "No Skiri subentries found"})
        return flags

    for idx, sub in enumerate(subentries):
        part_i = sub.get("part_I", sub)
        skiri_term = part_i.get("skiri_term", "") or sub.get("skiri_term", "")
        phonetic = part_i.get("phonetic_form", "") or sub.get("phonetic_form", "")

        if not skiri_term:
            flags.append({"type": "incomplete_parse", "field": f"subentry[{idx}].skiri_term",
                           "detail": f"Skiri term empty in subentry {idx}"})
        if not phonetic:
            flags.append({"type": "incomplete_parse", "field": f"subentry[{idx}].phonetic_form",
                           "detail": f"Phonetic form empty in subentry {idx}"})

    return flags


# ===========================================================================
#  PART 3: GEMINI AI VALIDATION AGENT
#  Used ONLY for tasks requiring judgment: verifying phonetic accuracy
#  against source PDFs, catching OCR errors, flagging discrepancies.
# ===========================================================================

def get_gemini_client():
    """Initialize Gemini API client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI-API-KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not found in environment variables.")
        log.error("Set it with: export GEMINI_API_KEY=your_key_here")
        sys.exit(1)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        log.info("Gemini API initialized (model: gemini-2.0-flash)")
        return model
    except ImportError:
        log.error("google-generativeai package not installed.")
        log.error("Install with: pip install google-generativeai")
        sys.exit(1)


def build_validation_prompt(entries_batch: list, dict_type: str) -> str:
    """
    Build a prompt for Gemini to validate a batch of entries.
    Keeps token usage low by sending only the fields that matter.
    """
    prompt = f"""You are a linguistic data auditor for the Skiri Pawnee dictionary.

TASK: Validate the phonetic transcription accuracy for each entry below.

SKIRI SOUND KEY (reference):
Consonants: p (as in 'spot'), t ('stop'), k ('skate'), c ('patch'/'cents'), s ('sit'), 
            w ('wall'), r (Spanish tapped 'pero'), h ('hit'), ® (glottal stop, 'uh-uh')
Vowels:     a (short, 'putt'), aa (long, 'father'), i (short, 'pit'), ii (long, 'weed'),
            u (short, 'boot'), uu (long, 'rude')
Syllable bullets (•) mark syllable breaks in the phonetic form.

For each entry, check:
1. PHONETIC CONSISTENCY: Does the phonetic_form plausibly match the headword? 
   (e.g., headword "piíta" should have phonetic like [pii•ta] not [ka•ri])
2. CHARACTER VALIDITY: Any unexpected characters that look like OCR errors?
   (e.g., ñ instead of ®, random numbers, garbled text)
3. COMPLETENESS: Any fields that look truncated or garbled?
4. GLOTTAL STOP CHECK: For nouns (N), does the headword end in ® as expected?

Respond ONLY with valid JSON — an array of objects, one per entry:
[
  {{
    "headword": "the headword",
    "phonetic_valid": true/false,
    "issues": ["list of specific issues found, or empty"],
    "suggested_fix": "correction if obvious, or null",
    "confidence": "high/medium/low"
  }}
]

ENTRIES TO VALIDATE ({dict_type}):
"""
    for entry in entries_batch:
        if dict_type == "s2e":
            hw = entry.get("headword", "")
            pf = entry.get("phonetic_form", "")
            gc = ""
            gi = entry.get("grammatical_info", {})
            if isinstance(gi, dict):
                gc = gi.get("grammatical_class", "")
            glosses = entry.get("glosses", [])
            gloss_str = "; ".join(glosses[:3]) if isinstance(glosses, list) else str(glosses)[:100]
            prompt += f'\n- headword: "{hw}" | phonetic: "{pf}" | class: {gc} | gloss: "{gloss_str}"'
        else:  # e2s
            ew = entry.get("english_entry_word", "")
            subs = entry.get("skiri_subentries", [])
            for sub in subs[:2]:  # limit subentries to keep tokens low
                pi = sub.get("part_I", sub)
                st = pi.get("skiri_term", "") or sub.get("skiri_term", "")
                pf = pi.get("phonetic_form", "") or sub.get("phonetic_form", "")
                prompt += f'\n- english: "{ew}" | skiri: "{st}" | phonetic: "{pf}"'

    return prompt


def validate_batch_with_gemini(model, entries: list, dict_type: str,
                                max_retries: int = 3) -> list:
    """
    Send a batch of entries to Gemini for phonetic validation.
    Returns list of validation result dicts.
    """
    prompt = build_validation_prompt(entries, dict_type)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Strip markdown code fences if present
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            results = json.loads(text)
            if isinstance(results, list):
                return results
            else:
                log.warning(f"Gemini returned non-list JSON, attempt {attempt+1}")
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error on attempt {attempt+1}: {e}")
            log.debug(f"Raw response: {text[:500]}")
        except Exception as e:
            log.warning(f"Gemini API error on attempt {attempt+1}: {e}")
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 30 * (attempt + 1)
                log.info(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(5)

    log.error(f"Failed to validate batch after {max_retries} attempts")
    return []


# ===========================================================================
#  PART 4: ORCHESTRATION — BATCH PROCESSING WITH CHECKPOINTING
# ===========================================================================

def load_json(path: Path) -> list:
    """Load a JSON file, returning empty list if not found."""
    if not path.exists():
        log.error(f"File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        log.info(f"Loaded {len(data)} entries from {path.name}")
        return data
    elif isinstance(data, dict):
        # Some files wrap entries in a top-level key
        for key in ("entries", "data", "results"):
            if key in data and isinstance(data[key], list):
                log.info(f"Loaded {len(data[key])} entries from {path.name}['{key}']")
                return data[key]
        log.warning(f"JSON is a dict but no known list key found in {path.name}")
        return [data]
    return []


def save_json(data, path: Path):
    """Save data as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} items to {path.name}")


def load_checkpoint() -> dict:
    """Load progress checkpoint."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"s2e_respell_idx": 0, "e2s_respell_idx": 0,
            "s2e_validate_idx": 0, "e2s_validate_idx": 0}


def save_checkpoint(checkpoint: dict):
    """Save progress checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


# --- Extract phonetic form from potentially nested entry structures ---

def get_s2e_phonetic(entry: dict) -> str:
    """Extract phonetic_form from an S2E entry (handles nesting variations)."""
    if "part_I" in entry and isinstance(entry["part_I"], dict):
        return entry["part_I"].get("phonetic_form", "") or ""
    return entry.get("phonetic_form", "") or ""


def set_s2e_pronunciation(entry: dict, pronunciation: str):
    """Set simplified_pronunciation on an S2E entry."""
    if "part_I" in entry and isinstance(entry["part_I"], dict):
        entry["part_I"]["simplified_pronunciation"] = pronunciation
    else:
        entry["simplified_pronunciation"] = pronunciation


def get_e2s_subentries(entry: dict) -> list:
    """Extract subentries from an E2S entry."""
    return entry.get("skiri_subentries", [])


# ===========================================================================
#  COMMAND: respell — Generate pronunciation respellings (local only)
# ===========================================================================

def cmd_respell():
    """Generate simplified_pronunciation for all entries. No API calls."""
    engine = RespellingEngine()
    stats = {"s2e_total": 0, "s2e_respelled": 0, "s2e_empty": 0, "s2e_unknown_chars": 0,
             "e2s_total": 0, "e2s_respelled": 0, "e2s_empty": 0, "e2s_unknown_chars": 0}

    # --- Skiri-to-English ---
    s2e_entries = load_json(S2E_JSON)
    if s2e_entries:
        for entry in s2e_entries:
            stats["s2e_total"] += 1
            phonetic = get_s2e_phonetic(entry)
            if phonetic:
                respelling = engine.respell(phonetic)
                set_s2e_pronunciation(entry, respelling)
                if respelling:
                    if "?" in respelling:
                        stats["s2e_unknown_chars"] += 1
                    stats["s2e_respelled"] += 1
                else:
                    stats["s2e_empty"] += 1
            else:
                set_s2e_pronunciation(entry, "")
                stats["s2e_empty"] += 1

        save_json(s2e_entries, RESPELLING_OUTPUT_S2E)

    # --- English-to-Skiri ---
    e2s_entries = load_json(E2S_JSON)
    if e2s_entries:
        for entry in e2s_entries:
            stats["e2s_total"] += 1
            for sub in get_e2s_subentries(entry):
                part_i = sub.get("part_I", sub)
                phonetic = part_i.get("phonetic_form", "") or sub.get("phonetic_form", "")
                if phonetic:
                    respelling = engine.respell(phonetic)
                    if "part_I" in sub and isinstance(sub["part_I"], dict):
                        sub["part_I"]["simplified_pronunciation"] = respelling
                    else:
                        sub["simplified_pronunciation"] = respelling
                    if respelling:
                        if "?" in respelling:
                            stats["e2s_unknown_chars"] += 1
                        stats["e2s_respelled"] += 1
                    else:
                        stats["e2s_empty"] += 1
                else:
                    stats["e2s_empty"] += 1

        save_json(e2s_entries, RESPELLING_OUTPUT_E2S)

    # Print summary
    log.info("=" * 60)
    log.info("RESPELLING COMPLETE")
    log.info(f"  S2E: {stats['s2e_respelled']}/{stats['s2e_total']} respelled "
             f"({stats['s2e_empty']} empty, {stats['s2e_unknown_chars']} with unknown chars)")
    log.info(f"  E2S: {stats['e2s_respelled']}/{stats['e2s_total']} respelled "
             f"({stats['e2s_empty']} empty, {stats['e2s_unknown_chars']} with unknown chars)")
    log.info(f"  Output: {RESPELLING_OUTPUT_S2E.name}, {RESPELLING_OUTPUT_E2S.name}")

    return stats


# ===========================================================================
#  COMMAND: validate — AI-powered phonetic form validation
# ===========================================================================

def cmd_validate(resume: bool = False, batch_size: int = 20,
                 rate_limit_delay: float = 2.0):
    """
    Use Gemini to validate phonetic form accuracy.
    Processes in batches to stay within token limits.
    """
    model = get_gemini_client()
    engine = RespellingEngine()

    checkpoint = load_checkpoint() if resume else {
        "s2e_validate_idx": 0, "e2s_validate_idx": 0
    }

    all_results = []
    if resume and VALIDATION_LOG.exists():
        all_results = load_json(VALIDATION_LOG)
        log.info(f"Resuming with {len(all_results)} existing results")

    # --- Phase A: Local field validation (fast, no API) ---
    log.info("Phase A: Local field validation...")
    s2e_entries = load_json(S2E_JSON)
    local_flags = {"total": 0, "flagged": 0, "flags_by_type": {}}

    for entry in s2e_entries:
        local_flags["total"] += 1
        flags = validate_entry_fields_s2e(entry)
        if flags:
            local_flags["flagged"] += 1
            headword = entry.get("headword", "<unknown>")
            for f in flags:
                ftype = f["type"]
                local_flags["flags_by_type"][ftype] = local_flags["flags_by_type"].get(ftype, 0) + 1
            all_results.append({
                "source": "s2e",
                "headword": headword,
                "validation_type": "local_field_check",
                "flags": flags,
                "timestamp": datetime.now().isoformat()
            })

    log.info(f"Local validation: {local_flags['flagged']}/{local_flags['total']} entries flagged")
    for ftype, count in local_flags["flags_by_type"].items():
        log.info(f"  {ftype}: {count}")

    # --- Phase B: AI phonetic validation (batched, uses Gemini) ---
    log.info("Phase B: AI phonetic validation (Gemini)...")
    start_idx = checkpoint.get("s2e_validate_idx", 0)

    # Only send entries that have a phonetic form to validate
    entries_with_phonetic = [
        e for e in s2e_entries if get_s2e_phonetic(e)
    ]
    total_batches = (len(entries_with_phonetic) - start_idx + batch_size - 1) // batch_size

    log.info(f"Processing {len(entries_with_phonetic) - start_idx} entries "
             f"in ~{total_batches} batches of {batch_size}")

    for batch_start in range(start_idx, len(entries_with_phonetic), batch_size):
        batch_end = min(batch_start + batch_size, len(entries_with_phonetic))
        batch = entries_with_phonetic[batch_start:batch_end]
        batch_num = (batch_start - start_idx) // batch_size + 1

        log.info(f"Batch {batch_num}/{total_batches}: entries {batch_start}-{batch_end-1}")

        # Flatten entries for the prompt (extract key fields only)
        flat_batch = []
        for e in batch:
            flat = {
                "headword": e.get("headword", ""),
                "phonetic_form": get_s2e_phonetic(e),
                "grammatical_info": e.get("grammatical_info", {}),
                "glosses": e.get("glosses", [])
            }
            flat_batch.append(flat)

        # Call Gemini
        ai_results = validate_batch_with_gemini(model, flat_batch, "s2e")

        if ai_results:
            for result in ai_results:
                result["source"] = "s2e"
                result["validation_type"] = "ai_phonetic_check"
                result["batch"] = batch_num
                result["timestamp"] = datetime.now().isoformat()
            all_results.extend(ai_results)

        # Checkpoint after each batch
        checkpoint["s2e_validate_idx"] = batch_end
        save_checkpoint(checkpoint)
        save_json(all_results, VALIDATION_LOG)

        # Rate limit
        if batch_end < len(entries_with_phonetic):
            time.sleep(rate_limit_delay)

    log.info(f"AI validation complete. {len(all_results)} total results.")
    save_json(all_results, VALIDATION_LOG)
    return all_results


# ===========================================================================
#  COMMAND: audit — Full pipeline (respell + validate + report)
# ===========================================================================

def cmd_audit(batch_size: int = 20, rate_limit_delay: float = 2.0):
    """Run full audit: respell locally, then validate with AI, then report."""
    log.info("=" * 60)
    log.info("FULL AUDIT — Phase 1.1")
    log.info("=" * 60)

    # Step 1: Respell
    log.info("\n--- STEP 1: Pronunciation Respelling ---")
    respell_stats = cmd_respell()

    # Step 2: Validate
    log.info("\n--- STEP 2: AI Phonetic Validation ---")
    validation_results = cmd_validate(resume=False, batch_size=batch_size,
                                       rate_limit_delay=rate_limit_delay)

    # Step 3: Report
    log.info("\n--- STEP 3: Generating Report ---")
    cmd_report()


# ===========================================================================
#  COMMAND: report — Generate human-readable audit report
# ===========================================================================

def cmd_report():
    """Generate a markdown summary report from validation results."""
    results = []
    if VALIDATION_LOG.exists():
        results = load_json(VALIDATION_LOG)

    # Count stats
    total = len(results)
    local_checks = [r for r in results if r.get("validation_type") == "local_field_check"]
    ai_checks = [r for r in results if r.get("validation_type") == "ai_phonetic_check"]

    # Local flag breakdown
    flag_counts = {}
    for r in local_checks:
        for f in r.get("flags", []):
            ftype = f.get("type", "unknown")
            flag_counts[ftype] = flag_counts.get(ftype, 0) + 1

    # AI issue breakdown
    ai_issues = 0
    ai_clean = 0
    issue_entries = []
    for r in ai_checks:
        if r.get("phonetic_valid") is False or r.get("issues"):
            issues = r.get("issues", [])
            if issues and issues != [] and issues != [""]:
                ai_issues += 1
                issue_entries.append(r)
            else:
                ai_clean += 1
        else:
            ai_clean += 1

    # Build report
    report = f"""# Phonetic Audit Report — Phase 1.1
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Count |
|--------|-------|
| Total validation results | {total} |
| Local field checks | {len(local_checks)} |
| AI phonetic checks | {len(ai_checks)} |
| AI — clean entries | {ai_clean} |
| AI — entries with issues | {ai_issues} |

## Local Validation Flags

| Flag Type | Count | Priority |
|-----------|-------|----------|
"""
    priority_order = [
        ("phonetic_char_error", "P1 — fix first"),
        ("incomplete_parse", "P2 — fill fields"),
        ("possible_ocr_glottal", "P3 — review"),
        ("missing_syllabification", "P4 — low priority"),
    ]
    for ftype, priority in priority_order:
        count = flag_counts.get(ftype, 0)
        report += f"| `{ftype}` | {count} | {priority} |\n"
    for ftype, count in flag_counts.items():
        if ftype not in dict(priority_order):
            report += f"| `{ftype}` | {count} | — |\n"

    report += f"""
## AI-Flagged Entries (Top Issues)

"""
    for entry in issue_entries[:50]:  # Top 50
        hw = entry.get("headword", "?")
        issues = entry.get("issues", [])
        fix = entry.get("suggested_fix", "")
        conf = entry.get("confidence", "")
        issue_str = "; ".join(issues) if isinstance(issues, list) else str(issues)
        report += f"- **{hw}**: {issue_str}"
        if fix:
            report += f" → Suggested: `{fix}`"
        report += f" [{conf}]\n"

    if len(issue_entries) > 50:
        report += f"\n... and {len(issue_entries) - 50} more. See `{VALIDATION_LOG.name}` for full details.\n"

    report += f"""
## Next Steps

1. Resolve `phonetic_char_error` flags first — these indicate data corruption
2. Fill in `incomplete_parse` entries by re-examining source PDFs
3. Review AI-flagged entries, prioritizing "high" confidence issues
4. Re-run `python phonetic_audit_agent.py respell` after corrections
5. Cross-reference against Blue Book (Phase 1.1e — next milestone)

## Files Generated

| File | Description |
|------|-------------|
| `{RESPELLING_OUTPUT_S2E.name}` | S2E entries with simplified_pronunciation |
| `{RESPELLING_OUTPUT_E2S.name}` | E2S entries with simplified_pronunciation |
| `{VALIDATION_LOG.name}` | Full validation results (JSON) |
| `{REPORT_FILE.name}` | This report |
"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    log.info(f"Report written to {REPORT_FILE.name}")


# ===========================================================================
#  CLI ENTRY POINT
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1.1: Phonetic Audit & Pronunciation Respelling Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  respell    Generate pronunciation respellings (local, no API cost)
  validate   AI-validate phonetic forms using Gemini
  audit      Full pipeline: respell + validate + report
  report     Generate summary report from existing logs

Examples:
  python phonetic_audit_agent.py respell
  python phonetic_audit_agent.py validate --batch-size 15 --delay 3
  python phonetic_audit_agent.py validate --resume
  python phonetic_audit_agent.py audit
        """
    )

    parser.add_argument("command", choices=["respell", "validate", "audit", "report"],
                        help="Which operation to run")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Entries per Gemini API call (default: 20)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between API calls (default: 2.0)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume validation from last checkpoint")

    args = parser.parse_args()

    log.info(f"{'='*60}")
    log.info(f"Phonetic Audit Agent — Command: {args.command}")
    log.info(f"{'='*60}")

    if args.command == "respell":
        cmd_respell()

    elif args.command == "validate":
        cmd_validate(resume=args.resume, batch_size=args.batch_size,
                     rate_limit_delay=args.delay)

    elif args.command == "audit":
        cmd_audit(batch_size=args.batch_size, rate_limit_delay=args.delay)

    elif args.command == "report":
        cmd_report()


if __name__ == "__main__":
    main()
