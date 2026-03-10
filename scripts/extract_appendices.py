#!/usr/bin/env python3
"""
Phase 3.1 — Appendix Extraction via Gemini OCR
================================================
Extracts verb conjugation paradigms from scanned PDF appendices using
PyMuPDF (fitz) for rendering and Gemini for OCR.

Appendix 1: 7 verbs × 10 modes × 11 person/number = ~770 forms
Appendix 2: Irregular dual/plural verb roots (~9 entries)
Appendix 3: Kinship terminology — consanguineal and affinal (~40 terms)
Also: Abbreviations (PDF 01) and Grammatical Overview (PDF 04)

Usage:
    # Extract Appendix 1 (verb conjugations):
    python scripts/extract_appendices.py --appendix1

    # Extract Appendix 2 (irregular roots):
    python scripts/extract_appendices.py --appendix2

    # Extract abbreviations list:
    python scripts/extract_appendices.py --abbreviations

    # Extract grammatical overview:
    python scripts/extract_appendices.py --grammar

    # Resume from checkpoint:
    python scripts/extract_appendices.py --appendix1 --resume

    # Import extracted data into DB:
    python scripts/extract_appendices.py --import-db --db skiri_pawnee.db

Dependencies: Python 3.8+, PyMuPDF (fitz), google-genai (GEMINI_API_KEY)
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import base64
import sqlite3
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PDF_DIR = Path("Dictionary Data/Dictionary PDF Split")
APPENDIX1_PDF = PDF_DIR / "Appendix 1 - Illustrative Skiri Verb Conjugations.pdf"
APPENDIX2_PDF = PDF_DIR / "Appendix 2 - Verb Roots with Irregular Dual or Plural Agents.pdf"
APPENDIX3_PDF = PDF_DIR / "Appendix 3 - Kinship Terminology - Consanguineal and Affinal.pdf"
ABBREV_PDF = PDF_DIR / "01-Abbreviations_and_Sound_Key.pdf"
GRAMMAR_PDF = PDF_DIR / "04-Grammatical_Overview.pdf"

CHECKPOINT_FILE = Path("appendix_extraction_checkpoint.json")
OUTPUT_DIR = Path("extracted_data")

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Person/number labels in order (from Appendix 1 template, page 1)
PERSON_NUMBER_LABELS = [
    "1sg",          # 1st person (I)
    "2sg",          # 2nd person (you)
    "3sg",          # 3rd person (he/she/it)
    "1du_incl",     # 1st person inclusive (you and I)
    "1du_excl",     # 1st person exclusive (he/she and I)
    "2du",          # 2nd person (you two)
    "3du",          # 3rd person (they two)
    "1pl_incl",     # 1st person inclusive (we, incl. you)
    "1pl_excl",     # 1st person exclusive (we, not you)
    "2pl",          # 2nd person (you all)
    "3pl",          # 3rd person (they)
]

# 10 modal categories
MODE_LABELS = [
    "indicative_perfective",
    "negative_indicative_perfective",
    "contingent_perfective",
    "assertive_perfective",
    "absolutive_perfective",
    "potential_perfective",
    "gerundial_perfective_subordinate",
    "contingent_perfective_subordinate",
    "subjunctive_perfective_subordinate",
    "infinitive_perfective_subordinate",
]

# ---------------------------------------------------------------------------
# Gemini API helpers
# ---------------------------------------------------------------------------

def _get_gemini_client():
    """Create and return Gemini client."""
    import google.genai as genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def _pdf_page_to_png(pdf_path, page_num, dpi=300):
    """Render a PDF page to PNG bytes using PyMuPDF."""
    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


def _call_gemini_with_image(client, image_bytes, prompt, system_instruction,
                            response_json=True):
    """Send image + prompt to Gemini and return parsed response."""
    from google.genai import types
    try:
        from google.api_core import exceptions as google_exceptions
        rate_limit_errors = (google_exceptions.ResourceExhausted,)
        server_errors = (google_exceptions.ServiceUnavailable,
                        google_exceptions.InternalServerError)
    except ImportError:
        rate_limit_errors = ()
        server_errors = ()

    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    config_kwargs = {
        "system_instruction": system_instruction,
        "temperature": 0.0,
        "max_output_tokens": 16384,
    }
    if response_json:
        config_kwargs["response_mime_type"] = "application/json"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = response.text.strip() if response.text else ""
            if not text:
                log.warning(f"  Empty response on attempt {attempt}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return None

            if response_json:
                # Try to parse JSON, handle truncation
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Try to recover partial JSON
                    return _recover_partial_json(text)
            return text

        except rate_limit_errors as e:
            wait = RETRY_DELAY * attempt * 2
            log.warning(f"  Rate limited, waiting {wait}s... ({e})")
            time.sleep(wait)
        except server_errors as e:
            log.warning(f"  Server error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
        except Exception as e:
            log.error(f"  Unexpected error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise

    return None


def _recover_partial_json(text):
    """Attempt to recover truncated JSON."""
    # Strip markdown code fences if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try closing open structures
    for suffix in [']', ']}', '"]}', '"}]', '"}}]', '"]}}']:
        try:
            return json.loads(text + suffix)
        except json.JSONDecodeError:
            continue

    log.warning("  Could not recover partial JSON")
    return {"_raw": text, "_partial": True}


# ---------------------------------------------------------------------------
# Checkpoint management
# ---------------------------------------------------------------------------

def _load_checkpoint(path):
    """Load extraction checkpoint."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_checkpoint(path, data):
    """Save extraction checkpoint."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Appendix 1: Verb Conjugation Paradigms
# ---------------------------------------------------------------------------

APPENDIX1_SYSTEM = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading scanned pages from "Appendix 1: Illustrative Skiri Verb Conjugations"
of the Parks Skiri Pawnee dictionary.

Each page contains paradigms for ONE verb across 10 modal categories.
The page is laid out in two columns, each with 5 modal sections.

Left column (top to bottom):
1. Indicative (Perfective)
2. Negative Indicative (Perfective)
3. Contingent (Perfective)
4. Assertive (Perfective)
5. Absolutive (Perfective)

Right column (top to bottom):
6. Potential (Perfective)
7. Gerundial (Perfective) Subordinate
8. Contingent (Perfective) Subordinate
9. Subjunctive (Perfective) Subordinate
10. Infinitive (Perfective) Subordinate

Each modal section lists 11 forms in this order:
1. 1st person singular (I)
2. 2nd person singular (you)
3. 3rd person singular (he/she/it)
4. 1st person dual inclusive (you and I)
5. 1st person dual exclusive (he/she and I)
6. 2nd person dual (you two)
7. 3rd person dual (they two)
8. 1st person plural inclusive (we, incl. you)
9. 1st person plural exclusive (we, not you)
10. 2nd person plural (you all)
11. 3rd person plural (they)

IMPORTANT OCR notes for Skiri Pawnee:
- The glottal stop looks like a superscript question mark or apostrophe: transcribe as ʔ (U+0294)
- Long vowels: aa, ii, uu (doubled letters)
- The letter c represents /ts/ (NOT English "c")
- Accent marks (á, í, ú) indicate high pitch
- Some forms may have comma-separated variants
- Preserve EXACT spelling from the page — do NOT normalize or correct

Return JSON with this structure:
{
  "verb_heading": "the verb name/gloss shown at top of page",
  "verb_class": "the verb class if shown (e.g., '1', '2-i', etc.)",
  "dictionary_form": "the citation/headword form of the verb",
  "english_gloss": "the English meaning",
  "modes": {
    "indicative_perfective": {
      "1sg": {"skiri": "...", "english": "..."},
      "2sg": {"skiri": "...", "english": "..."},
      ...all 11 person/number forms...
    },
    ...all 10 modes...
  }
}

For the person/number keys use: 1sg, 2sg, 3sg, 1du_incl, 1du_excl, 2du, 3du, 1pl_incl, 1pl_excl, 2pl, 3pl

Be extremely careful with:
- Distinguishing ʔ (glottal stop) from ' (apostrophe) — use ʔ
- Long vs short vowels (aa vs a, ii vs i, uu vs u)
- The superscript-like marks that indicate glottal stops
- Reading the correct number of forms per section (always 11)
"""

APPENDIX1_PROMPT = """Please extract ALL verb conjugation forms from this page.

This is a page from Appendix 1 of the Parks Skiri Pawnee dictionary showing
the full conjugation paradigm for one verb.

Read EVERY form carefully. There should be exactly 10 modal sections with
11 person/number forms each (110 forms total on this page).

Return the data as a single JSON object."""


def extract_appendix1(client, resume=False):
    """Extract all verb conjugation paradigms from Appendix 1."""
    log.info("=== Extracting Appendix 1: Verb Conjugation Paradigms ===")

    checkpoint = _load_checkpoint(CHECKPOINT_FILE) if resume else {}
    a1_data = checkpoint.get("appendix1", {})

    doc = fitz.open(str(APPENDIX1_PDF))
    num_pages = len(doc)
    doc.close()
    log.info(f"Appendix 1: {num_pages} pages (page 1 = intro, pages 2-{num_pages} = verb paradigms)")

    # Page 1 is intro/template, pages 2-8 are the 7 verb paradigms
    for page_idx in range(1, num_pages):
        page_key = f"page_{page_idx + 1}"

        if page_key in a1_data and not a1_data[page_key].get("_partial"):
            log.info(f"  Page {page_idx + 1}: already extracted (skipping)")
            continue

        log.info(f"  Page {page_idx + 1}: rendering and sending to Gemini...")
        png_bytes = _pdf_page_to_png(APPENDIX1_PDF, page_idx)

        result = _call_gemini_with_image(
            client, png_bytes, APPENDIX1_PROMPT, APPENDIX1_SYSTEM
        )

        if result is None:
            log.error(f"  Page {page_idx + 1}: extraction failed!")
            a1_data[page_key] = {"_error": "extraction_failed"}
        else:
            a1_data[page_key] = result
            # Count extracted forms
            if "modes" in result:
                form_count = sum(
                    len(mode_forms)
                    for mode_forms in result["modes"].values()
                )
                log.info(f"  Page {page_idx + 1}: extracted {form_count} forms "
                         f"for '{result.get('verb_heading', '?')}'")
            else:
                log.warning(f"  Page {page_idx + 1}: unexpected format")

        # Save checkpoint after each page
        checkpoint["appendix1"] = a1_data
        _save_checkpoint(CHECKPOINT_FILE, checkpoint)
        time.sleep(2)  # Rate limit courtesy

    # Save final output
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "appendix1_conjugations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(a1_data, f, ensure_ascii=False, indent=2)
    log.info(f"Saved Appendix 1 data to {out_path}")

    # Summary
    total_forms = 0
    for page_key, page_data in a1_data.items():
        if isinstance(page_data, dict) and "modes" in page_data:
            for mode_forms in page_data["modes"].values():
                total_forms += len(mode_forms)
    log.info(f"Total forms extracted: {total_forms} (expected ~770)")

    return a1_data


# ---------------------------------------------------------------------------
# Appendix 2: Irregular Verb Roots
# ---------------------------------------------------------------------------

APPENDIX2_SYSTEM = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading "Appendix 2: Verb Roots with Irregular Dual or Plural Agents"
from the Parks Skiri Pawnee dictionary.

This appendix lists verbs that have different stems for singular, dual, and
plural agents (suppletive roots), and verbs marked with the distributive
prefix *uus-* for dual/plural.

IMPORTANT OCR notes for Skiri Pawnee:
- Glottal stop: transcribe as ʔ (U+0294)
- Long vowels: aa, ii, uu
- The letter c represents /ts/
- Accent marks (á, í, ú) indicate high pitch
- Preserve EXACT spelling — do NOT normalize

Return JSON as an array of entries:
[
  {
    "headword": "the dictionary headword",
    "english_gloss": "English meaning",
    "singular_stem": "stem used with singular agent",
    "dual_stem": "stem used with dual agent (or null)",
    "plural_stem": "stem used with plural agent (or null)",
    "distributive_prefix": true/false,
    "notes": "any additional notes from the page"
  }
]"""

APPENDIX2_PROMPT = """Extract ALL irregular verb root entries from this page.
Each entry should include the headword, English gloss, and the different
stems used for singular/dual/plural agents. Return as a JSON array."""


def extract_appendix2(client, resume=False):
    """Extract irregular verb roots from Appendix 2."""
    log.info("=== Extracting Appendix 2: Irregular Verb Roots ===")

    checkpoint = _load_checkpoint(CHECKPOINT_FILE) if resume else {}

    if "appendix2" in checkpoint and not checkpoint["appendix2"].get("_partial"):
        if resume:
            log.info("  Already extracted (skipping)")
            return checkpoint["appendix2"]

    png_bytes = _pdf_page_to_png(APPENDIX2_PDF, 0)
    log.info("  Sending to Gemini...")

    result = _call_gemini_with_image(
        client, png_bytes, APPENDIX2_PROMPT, APPENDIX2_SYSTEM
    )

    if result is None:
        log.error("  Extraction failed!")
        return None

    entry_count = len(result) if isinstance(result, list) else "?"
    log.info(f"  Extracted {entry_count} entries")

    checkpoint["appendix2"] = result
    _save_checkpoint(CHECKPOINT_FILE, checkpoint)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "appendix2_irregular_roots.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log.info(f"Saved to {out_path}")

    return result


# ---------------------------------------------------------------------------
# Appendix 3: Kinship Terminology — Consanguineal and Affinal
# ---------------------------------------------------------------------------

APPENDIX3_SYSTEM = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading "Appendix 3: Kinship Terminology — Consanguineal and Affinal"
from the Parks Skiri Pawnee dictionary.

This appendix lists kinship terms organized in tables. Each term includes:
- The English kinship relationship (e.g., "father", "mother's brother")
- The Skiri Pawnee term (headword)
- Possessive/vocative paradigm forms (my X, your X, his/her X, vocative form)
- Some terms are verb-based constructions (e.g., aktaku "to have as spouse")

IMPORTANT OCR notes for Skiri Pawnee:
- Glottal stop: transcribe as ʔ (U+0294), NOT as apostrophe
- Long vowels: aa, ii, uu (doubled letters)
- The letter c represents /ts/
- Accent marks (á, í, ú) indicate high pitch — preserve exactly
- Preserve EXACT spelling — do NOT normalize or correct
- Some entries may have parenthetical notes or cross-references

The kinship terms are split into two categories:
1. Consanguineal (blood relatives): father, mother, brother, sister, etc.
2. Affinal (marriage relatives): spouse, in-laws, etc.

Return JSON:
{
  "category": "consanguineal" or "affinal",
  "terms": [
    {
      "english_term": "father",
      "skiri_term": "aatiiʔa",
      "grammatical_class": "N-KIN",
      "possessive_forms": {
        "my": "aatiiʔa",
        "your": "aatiiʔa",
        "his_her": "raatiiʔa",
        "vocative": "atiiʔa"
      },
      "verb_construction": null,
      "notes": "any additional notes"
    }
  ]
}

IMPORTANT: Not all entries will have all possessive forms. Include whatever
forms are visible on the page. If a field is not present, use null."""

APPENDIX3_PROMPT = """Extract ALL kinship terminology entries from this page.
Each entry should include the English relationship term, the Skiri Pawnee term,
and any possessive/vocative paradigm forms shown. Carefully transcribe all
Pawnee text using proper IPA glottal stops (ʔ) and preserving accent marks.
Return as JSON."""


def extract_appendix3(client, resume=False):
    """Extract kinship terminology from Appendix 3."""
    log.info("=== Extracting Appendix 3: Kinship Terminology ===")

    checkpoint = _load_checkpoint(CHECKPOINT_FILE) if resume else {}
    kinship_data = checkpoint.get("appendix3", {})

    doc = fitz.open(str(APPENDIX3_PDF))
    num_pages = len(doc)
    doc.close()
    log.info(f"Appendix 3 PDF: {num_pages} pages")

    all_terms = []

    for page_idx in range(num_pages):
        page_key = f"page_{page_idx + 1}"

        if page_key in kinship_data and kinship_data[page_key]:
            if resume:
                log.info(f"  Page {page_idx + 1}: already extracted (skipping)")
                page_result = kinship_data[page_key]
            else:
                page_result = None
        else:
            page_result = None

        if page_result is None:
            log.info(f"  Page {page_idx + 1}: rendering and sending to Gemini...")
            png_bytes = _pdf_page_to_png(APPENDIX3_PDF, page_idx, dpi=300)

            page_result = _call_gemini_with_image(
                client, png_bytes, APPENDIX3_PROMPT, APPENDIX3_SYSTEM
            )

            if page_result is None:
                log.warning(f"  Page {page_idx + 1}: extraction failed!")
                continue

            kinship_data[page_key] = page_result
            checkpoint["appendix3"] = kinship_data
            _save_checkpoint(CHECKPOINT_FILE, checkpoint)

        # Collect terms
        if isinstance(page_result, dict):
            terms = page_result.get("terms", [])
            all_terms.extend(terms)
            log.info(f"  Page {page_idx + 1}: {len(terms)} terms")
        elif isinstance(page_result, list):
            all_terms.extend(page_result)
            log.info(f"  Page {page_idx + 1}: {len(page_result)} terms")

    log.info(f"Total kinship terms extracted: {len(all_terms)}")

    # Save output
    OUTPUT_DIR.mkdir(exist_ok=True)
    output = {
        "total_terms": len(all_terms),
        "pages_extracted": num_pages,
        "terms": all_terms,
    }
    out_path = OUTPUT_DIR / "appendix3_kinship.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info(f"Saved to {out_path}")

    return output


# ---------------------------------------------------------------------------
# Abbreviations & Sound Key (PDF 01)
# ---------------------------------------------------------------------------

ABBREV_SYSTEM = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading the "Abbreviations and Sound Key" section from the Parks
Skiri Pawnee dictionary.

This section contains:
1. A list of abbreviations used throughout the dictionary, many of which are
   morpheme labels (e.g., QUOT = quotative, PERF = perfective, etc.)
2. A sound/phonetic key

For the abbreviations, extract EVERY abbreviation and its full meaning.
These are critical for understanding the verb morphology system.

IMPORTANT OCR notes:
- Preserve exact formatting and special characters
- Some abbreviations have sub-categories (e.g., different verb classes)
- Morpheme forms may include Pawnee text with glottal stops (ʔ), long vowels, etc.

Return JSON:
{
  "abbreviations": [
    {"abbrev": "ADV", "meaning": "adverb", "morpheme_form": null, "notes": null},
    {"abbrev": "QUOT", "meaning": "quotative", "morpheme_form": "wi-", "notes": "proclitic"},
    ...
  ],
  "sound_key": {
    "consonants": [...],
    "vowels": [...]
  }
}"""

ABBREV_PROMPT = """Extract ALL abbreviations and their meanings from this page.
Include any morpheme forms shown. Return as JSON."""


def extract_abbreviations(client, resume=False):
    """Extract abbreviations from PDF 01."""
    log.info("=== Extracting Abbreviations (PDF 01) ===")

    checkpoint = _load_checkpoint(CHECKPOINT_FILE) if resume else {}
    abbrev_data = checkpoint.get("abbreviations", {})

    doc = fitz.open(str(ABBREV_PDF))
    num_pages = len(doc)
    doc.close()
    log.info(f"Abbreviations PDF: {num_pages} pages")

    all_abbreviations = []
    sound_key = {}

    for page_idx in range(num_pages):
        page_key = f"page_{page_idx + 1}"

        if page_key in abbrev_data and not abbrev_data[page_key].get("_partial"):
            log.info(f"  Page {page_idx + 1}: already extracted (skipping)")
            page_result = abbrev_data[page_key]
        else:
            log.info(f"  Page {page_idx + 1}: rendering and sending to Gemini...")
            png_bytes = _pdf_page_to_png(ABBREV_PDF, page_idx)

            page_result = _call_gemini_with_image(
                client, png_bytes, ABBREV_PROMPT, ABBREV_SYSTEM
            )

            if page_result is None:
                log.error(f"  Page {page_idx + 1}: extraction failed!")
                abbrev_data[page_key] = {"_error": "extraction_failed"}
                continue

            abbrev_data[page_key] = page_result
            checkpoint["abbreviations"] = abbrev_data
            _save_checkpoint(CHECKPOINT_FILE, checkpoint)
            time.sleep(2)

        # Collect results
        if isinstance(page_result, dict):
            if "abbreviations" in page_result:
                all_abbreviations.extend(page_result["abbreviations"])
            if "sound_key" in page_result:
                sound_key.update(page_result["sound_key"])

    # Deduplicate abbreviations
    seen = set()
    unique_abbrevs = []
    for a in all_abbreviations:
        key = a.get("abbrev", "")
        if key and key not in seen:
            seen.add(key)
            unique_abbrevs.append(a)

    combined = {
        "abbreviations": unique_abbrevs,
        "sound_key": sound_key,
        "total_count": len(unique_abbrevs),
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "abbreviations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(unique_abbrevs)} abbreviations to {out_path}")

    return combined


# ---------------------------------------------------------------------------
# Grammatical Overview (PDF 04)
# ---------------------------------------------------------------------------

GRAMMAR_SYSTEM = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading the "Grammatical Overview" section from the Parks Skiri Pawnee dictionary.

This section describes the grammatical structure of the Skiri Pawnee language including:
- Word classes and their properties
- Verb morphology: prefixes, preverbs, stems, suffixes
- Slot ordering in the verb template
- Person/number marking
- Modal categories
- Aspect markers
- Proclitic system

Extract the content as structured text, preserving:
- All morpheme forms with their Pawnee spellings
- Slot position descriptions
- Paradigm tables
- Example forms
- All linguistic terminology and category labels

Use ʔ for glottal stops, preserve long vowels (aa, ii, uu), accent marks.

Return JSON:
{
  "page_number": N,
  "sections": [
    {
      "heading": "section heading",
      "content": "full text content of this section",
      "morphemes_mentioned": [
        {"form": "wi-", "label": "quotative", "slot": "proclitic", "notes": "..."}
      ],
      "tables": [
        {"caption": "...", "rows": [["col1", "col2", ...], ...]}
      ]
    }
  ]
}"""

GRAMMAR_PROMPT = """Extract ALL grammatical information from this page.
Focus especially on:
1. Morpheme forms and their labels/meanings
2. Slot positions in the verb template
3. Person/number paradigms
4. Any tables or paradigm charts

Return as structured JSON."""


def extract_grammar(client, resume=False):
    """Extract grammatical overview from PDF 04."""
    log.info("=== Extracting Grammatical Overview (PDF 04) ===")

    checkpoint = _load_checkpoint(CHECKPOINT_FILE) if resume else {}
    grammar_data = checkpoint.get("grammar", {})

    doc = fitz.open(str(GRAMMAR_PDF))
    num_pages = len(doc)
    doc.close()
    log.info(f"Grammatical Overview: {num_pages} pages")

    for page_idx in range(num_pages):
        page_key = f"page_{page_idx + 1}"

        if page_key in grammar_data and not grammar_data[page_key].get("_partial"):
            log.info(f"  Page {page_idx + 1}: already extracted (skipping)")
            continue

        log.info(f"  Page {page_idx + 1}/{num_pages}: rendering and sending to Gemini...")
        png_bytes = _pdf_page_to_png(GRAMMAR_PDF, page_idx)

        result = _call_gemini_with_image(
            client, png_bytes, GRAMMAR_PROMPT, GRAMMAR_SYSTEM
        )

        if result is None:
            log.error(f"  Page {page_idx + 1}: extraction failed!")
            grammar_data[page_key] = {"_error": "extraction_failed"}
        else:
            grammar_data[page_key] = result

        checkpoint["grammar"] = grammar_data
        _save_checkpoint(CHECKPOINT_FILE, checkpoint)
        time.sleep(2)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "grammatical_overview.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(grammar_data, f, ensure_ascii=False, indent=2)
    log.info(f"Saved grammatical overview to {out_path}")

    return grammar_data


# ---------------------------------------------------------------------------
# DB Import
# ---------------------------------------------------------------------------

def import_to_db(db_path):
    """Import extracted appendix data into SQLite database."""
    log.info(f"=== Importing extracted data to {db_path} ===")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables for appendix data
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS verb_paradigms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verb_heading TEXT NOT NULL,
            verb_class TEXT,
            dictionary_form TEXT,
            english_gloss TEXT,
            mode TEXT NOT NULL,
            person_number TEXT NOT NULL,
            skiri_form TEXT NOT NULL,
            english_form TEXT,
            source_page INTEGER,
            UNIQUE(verb_heading, mode, person_number)
        );

        CREATE TABLE IF NOT EXISTS irregular_verb_roots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headword TEXT NOT NULL,
            english_gloss TEXT,
            singular_stem TEXT,
            dual_stem TEXT,
            plural_stem TEXT,
            distributive_prefix INTEGER DEFAULT 0,
            notes TEXT,
            UNIQUE(headword)
        );

        CREATE TABLE IF NOT EXISTS morpheme_abbreviations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abbreviation TEXT NOT NULL UNIQUE,
            meaning TEXT NOT NULL,
            morpheme_form TEXT,
            notes TEXT
        );
    """)

    # Import Appendix 1
    a1_path = OUTPUT_DIR / "appendix1_conjugations.json"
    if a1_path.exists():
        with open(a1_path, "r", encoding="utf-8") as f:
            a1_data = json.load(f)

        paradigm_count = 0
        for page_key, page_data in a1_data.items():
            if not isinstance(page_data, dict) or "modes" not in page_data:
                continue
            page_num = int(page_key.split("_")[1]) if "_" in page_key else 0
            verb_heading = page_data.get("verb_heading") or page_data.get("english_gloss") or f"verb_{page_key}"
            verb_class = page_data.get("verb_class") or ""
            dict_form = page_data.get("dictionary_form") or ""
            eng_gloss = page_data.get("english_gloss") or ""

            for mode, forms in page_data["modes"].items():
                for pn, form_data in forms.items():
                    skiri = form_data.get("skiri", "") if isinstance(form_data, dict) else str(form_data)
                    english = form_data.get("english", "") if isinstance(form_data, dict) else ""
                    if skiri:
                        cur.execute("""
                            INSERT OR REPLACE INTO verb_paradigms
                            (verb_heading, verb_class, dictionary_form, english_gloss,
                             mode, person_number, skiri_form, english_form, source_page)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (verb_heading, verb_class, dict_form, eng_gloss,
                              mode, pn, skiri, english, page_num))
                        paradigm_count += 1

        log.info(f"  Imported {paradigm_count} verb paradigm forms")

    # Import Appendix 2
    a2_path = OUTPUT_DIR / "appendix2_irregular_roots.json"
    if a2_path.exists():
        with open(a2_path, "r", encoding="utf-8") as f:
            a2_data = json.load(f)

        if isinstance(a2_data, list):
            for entry in a2_data:
                cur.execute("""
                    INSERT OR REPLACE INTO irregular_verb_roots
                    (headword, english_gloss, singular_stem, dual_stem, plural_stem,
                     distributive_prefix, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get("headword", ""),
                    entry.get("english_gloss", ""),
                    entry.get("singular_stem"),
                    entry.get("dual_stem"),
                    entry.get("plural_stem"),
                    1 if entry.get("distributive_prefix") else 0,
                    entry.get("notes"),
                ))
            log.info(f"  Imported {len(a2_data)} irregular verb root entries")

    # Import abbreviations
    abbrev_path = OUTPUT_DIR / "abbreviations.json"
    if abbrev_path.exists():
        with open(abbrev_path, "r", encoding="utf-8") as f:
            abbrev_data = json.load(f)

        abbrevs = abbrev_data.get("abbreviations", [])
        for a in abbrevs:
            cur.execute("""
                INSERT OR REPLACE INTO morpheme_abbreviations
                (abbreviation, meaning, morpheme_form, notes)
                VALUES (?, ?, ?, ?)
            """, (
                a.get("abbrev", ""),
                a.get("meaning", ""),
                a.get("morpheme_form"),
                a.get("notes"),
            ))
        log.info(f"  Imported {len(abbrevs)} abbreviations")

    conn.commit()
    conn.close()
    log.info("  DB import complete")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.1: Extract appendix data via Gemini OCR"
    )
    parser.add_argument("--appendix1", action="store_true",
                        help="Extract Appendix 1 verb conjugations")
    parser.add_argument("--appendix2", action="store_true",
                        help="Extract Appendix 2 irregular roots")
    parser.add_argument("--appendix3", action="store_true",
                        help="Extract Appendix 3 kinship terminology")
    parser.add_argument("--abbreviations", action="store_true",
                        help="Extract abbreviations from PDF 01")
    parser.add_argument("--grammar", action="store_true",
                        help="Extract grammatical overview from PDF 04")
    parser.add_argument("--all", action="store_true",
                        help="Extract everything")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint")
    parser.add_argument("--import-db", action="store_true",
                        help="Import extracted data into SQLite DB")
    parser.add_argument("--db", type=str, default="skiri_pawnee.db",
                        help="SQLite database path (default: skiri_pawnee.db)")
    args = parser.parse_args()

    if args.import_db:
        import_to_db(args.db)
        return

    if not any([args.appendix1, args.appendix2, args.appendix3,
                args.abbreviations, args.grammar, args.all]):
        parser.print_help()
        return

    client = _get_gemini_client()

    if args.appendix1 or args.all:
        extract_appendix1(client, resume=args.resume)

    if args.appendix2 or args.all:
        extract_appendix2(client, resume=args.resume)

    if args.appendix3 or args.all:
        extract_appendix3(client, resume=args.resume)

    if args.abbreviations or args.all:
        extract_abbreviations(client, resume=args.resume)

    if args.grammar or args.all:
        extract_grammar(client, resume=args.resume)


if __name__ == "__main__":
    main()
