"""
Skiri Pawnee Dictionary — Step 3: Verification & Normalization via Claude API

This script verifies every extracted dictionary field against the original source PDFs
using Claude's vision capabilities, correcting errors and normalizing inconsistencies
from the initial Gemini extraction.

Normalizations performed:
  - Standardizing grammatical class abbreviations
  - Normalizing etymology field structures
  - Unifying example sentence formats
  - Fixing glottal stop encoding (ʔ vs ? vs ™ vs ®)
  - Mapping PDF font-specific characters to proper linguistic symbols

Usage:
  python verify_with_claude.py --mode s2e          # Verify Skiri-to-English
  python verify_with_claude.py --mode e2s          # Verify English-to-Skiri
  python verify_with_claude.py --mode s2e --resume # Resume from last checkpoint
  python verify_with_claude.py --mode s2e --start-page 50 --end-page 100

Requires:
  pip install anthropic
  Environment variable: CLAUDE_API_KEY
"""

import os
import sys
import json
import time
import glob
import base64
import logging
import argparse
from pathlib import Path
from collections import defaultdict

import anthropic

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Paths relative to the "Dictionary Data" folder
BASE_DIR = Path(__file__).resolve().parent.parent / "Dictionary Data"

CONFIG = {
    "s2e": {
        "input_json": BASE_DIR / "skiri_to_english_complete.json",
        "pdf_dir": BASE_DIR / "split_pdf_pages_SKIRI_TO_ENGLISH",
        "output_json": BASE_DIR / "skiri_to_english_verified.json",
        "progress_file": BASE_DIR / "verification_progress_s2e.json",
        "log_file": "verify_s2e.log",
        "section_name": "Skiri-to-English",
    },
    "e2s": {
        "input_json": BASE_DIR / "english_to_skiri_complete.json",
        "pdf_dir": BASE_DIR / "split_pdf_pages_ENGLISH_TO_SKIRI",
        "output_json": BASE_DIR / "english_to_skiri_verified.json",
        "progress_file": BASE_DIR / "verification_progress_e2s.json",
        "log_file": "verify_e2s.log",
        "section_name": "English-to-Skiri",
    },
}

MAX_RETRIES = 3
RETRY_BASE_DELAY = 30  # seconds
MAX_ENTRIES_PER_CHUNK = 15  # split large batches to avoid output truncation

# ---------------------------------------------------------------------------
# VERIFICATION PROMPT
# ---------------------------------------------------------------------------

VERIFICATION_PROMPT = r"""# Skiri Pawnee Dictionary — Verification & Normalization Task

You are verifying machine-extracted dictionary entries against the **original source PDF page(s)** provided as images. Your role is critical for language preservation — accuracy is paramount.

## Your Task

You will receive:
1. **One or two source PDF pages** (the original dictionary pages as images)
2. **A JSON array of extracted entries** that were parsed from those pages by a prior AI system

For EACH entry, carefully compare every field against what you see in the source PDF and:
1. **Correct** any extraction errors (wrong characters, missing data, hallucinated content)
2. **Normalize** fields according to the rules below
3. **Preserve** anything that was correctly extracted

## Normalization Rules

### 1. Glottal Stop Encoding
The source PDF uses various representations for the glottal stop. **Standardize ALL to `ʔ`**:
- `™` → `ʔ`
- `®` (when used as glottal stop in phonetic forms) → `ʔ`
- `?` (when used as glottal stop) → `ʔ`
- The proper Unicode character is U+0294 (ʔ)
- Apply in: headwords, phonetic_form, paradigmatic forms, examples, etymology, derived stems

### 2. Grammatical Class Abbreviations
Standardize to these exact forms:
- `VI` — intransitive verb
- `VT` — transitive verb
- `VD` — descriptive verb
- `VL` — locative verb
- `VP` — patientive/passive verb
- `VR` — reflexive verb
- `N` — noun
- `N-DEP` — dependent noun stem
- `N-KIN` — kinship term
- `ADJ` — adjective
- `ADV` — adverb
- `PRON` — pronoun
- `DEM` — demonstrative
- `NUM` — numeral
Fix any variations (lowercase, extra spaces, typos).

### 3. Verb Class Format
Standardize to parenthesized form: `(1)`, `(1-a)`, `(1-i)`, `(2)`, `(2-i)`, `(3)`, `(4)`, `(4-i)`, `(u)`, `(wi)`
- Remove extra whitespace
- Ensure parentheses are present

### 4. Phonetic Form (HIGHEST PRIORITY)
- Must match the source PDF **character-for-character**
- Preserve all diacritics, syllable breaks (•), accent marks
- Fix any OCR artifacts
- Keep the square brackets `[...]`
- Normalize glottal stop characters to `ʔ` within phonetic forms

### 5. Etymology Normalization
- Keep angle brackets `<...>` content intact
- Normalize morpheme separators to `+`
- Ensure literal_translation is extracted if present in source
- Verify constituent_elements match the raw_etymology

### 6. Example Sentence Format
- Skiri text and English translation should be properly separated
- Remove any stray formatting artifacts
- Ensure bullet markers are not included in the text itself

### 7. PDF Font Character Mapping
Common substitutions needed from PDF font encoding:
- `fi` ligature → `fi`
- `fl` ligature → `fl`
- Curly/smart quotes → straight quotes where appropriate
- En-dash/em-dash → proper representation
- Any mojibake or garbled characters → correct form visible in PDF

## Output Format

Return a JSON object with this structure:
```json
{
  "verified_entries": [ ... ],
  "corrections_log": [
    {
      "entry_identifier": "headword or english_entry_word",
      "field": "field path that was corrected",
      "original": "what was in the extracted data",
      "corrected": "what it should be based on PDF",
      "reason": "brief explanation"
    }
  ]
}
```

The `verified_entries` array must contain ALL entries from the input, with corrections applied.
The `corrections_log` should list every change you made (one object per correction).

## IMPORTANT
- If an entry looks correct, include it unchanged in verified_entries
- Do NOT add entries that aren't in the input — only verify/correct what was extracted
- Do NOT remove entries — if an entry exists, keep it (even if you can't find it in the PDF)
- When uncertain, preserve the original and note the uncertainty in corrections_log
- Return ONLY valid JSON — no markdown fences, no explanatory text outside the JSON
"""

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

def setup_logging(log_file: str):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

# ---------------------------------------------------------------------------
# PDF HELPERS
# ---------------------------------------------------------------------------

def load_pdf_as_base64(pdf_path: Path) -> str | None:
    """Read a PDF file and return its base64-encoded content."""
    if not pdf_path.exists():
        logging.warning(f"PDF not found: {pdf_path}")
        return None
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_sorted_pdf_list(pdf_dir: Path) -> list[Path]:
    """Return a sorted list of all PDF files in the given directory."""
    return sorted(Path(p) for p in glob.glob(str(pdf_dir / "*.pdf")))

# ---------------------------------------------------------------------------
# PAGE-TO-PDF MAPPING
# ---------------------------------------------------------------------------

def build_s2e_mapping(entries: list, pdf_files: list[Path]) -> dict[int, int]:
    """
    Build a mapping from dictionary page_number → PDF file index.

    S2E entries store the printed dictionary page number in
    entry_metadata.page_number.  The PDF files (page_001.pdf …
    page_181.pdf) are sequential scans of those dictionary pages.
    There are 181 unique page numbers and 181 PDF files, so the
    Nth unique page number (sorted ascending) maps to the Nth PDF
    file (0-based index).
    """
    unique_pages = sorted(set(
        e.get("entry_metadata", {}).get("page_number")
        for e in entries
        if e.get("entry_metadata", {}).get("page_number") is not None
    ))

    if len(unique_pages) > len(pdf_files):
        logging.warning(
            f"More unique page numbers ({len(unique_pages)}) than PDF files "
            f"({len(pdf_files)}). Some pages won't have a source PDF."
        )

    mapping: dict[int, int] = {}
    for i, page_num in enumerate(unique_pages):
        if i < len(pdf_files):
            mapping[page_num] = i

    logging.info(f"  Built S2E mapping: {len(mapping)} page numbers → {len(pdf_files)} PDF files")
    return mapping


def build_e2s_mapping(entries: list, pdf_files: list[Path]) -> dict[int, int]:
    """
    Build a mapping from source_page → PDF file index.

    E2S entries store source_page (1-based processing index) in
    entry_metadata.source_page.  source_page=1 → pdf_files[0],
    source_page=2 → pdf_files[1], etc.
    """
    mapping: dict[int, int] = {}
    for e in entries:
        sp = e.get("entry_metadata", {}).get("source_page")
        if sp is not None and sp >= 1:
            pdf_idx = sp - 1  # convert 1-based → 0-based
            if pdf_idx < len(pdf_files):
                mapping[sp] = pdf_idx

    logging.info(f"  Built E2S mapping: {len(mapping)} source_pages → PDF files")
    return mapping


def group_entries_by_pdf(
    entries: list,
    mode: str,
    page_to_pdf: dict[int, int],
) -> tuple[dict[int, list], list]:
    """
    Group entries by PDF file index.

    Returns (groups_by_pdf_index, unmatched_entries).
    """
    groups: dict[int, list] = defaultdict(list)
    unmatched: list = []

    for entry in entries:
        meta = entry.get("entry_metadata", {})

        if mode == "s2e":
            page_num = meta.get("page_number")
            pdf_idx = page_to_pdf.get(page_num) if page_num is not None else None
        else:  # e2s
            source_page = meta.get("source_page")
            pdf_idx = page_to_pdf.get(source_page) if source_page is not None else None

        if pdf_idx is not None:
            groups[pdf_idx].append(entry)
        else:
            unmatched.append(entry)

    if unmatched:
        logging.warning(f"  {len(unmatched)} entries could not be mapped to a PDF file.")

    return dict(sorted(groups.items())), unmatched

# ---------------------------------------------------------------------------
# CLAUDE API CALL
# ---------------------------------------------------------------------------

def build_message_content(entries_json: str, pdf_pages: list[tuple[str, str]]) -> list[dict]:
    """Build the multimodal content array for Claude.

    pdf_pages: list of (label, base64_data) tuples
    """
    content: list[dict] = []

    # Add PDF pages as document blocks
    for label, b64_data in pdf_pages:
        content.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64_data,
            },
            "cache_control": {"type": "ephemeral"},
        })
        content.append({
            "type": "text",
            "text": f"[Above: {label}]",
        })

    # Add the extracted entries to verify
    content.append({
        "type": "text",
        "text": (
            "Below are the extracted entries to verify against the PDF page(s) above.\n\n"
            "```json\n" + entries_json + "\n```"
        ),
    })

    return content


def call_claude(
    client: anthropic.Anthropic,
    content: list[dict],
    model: str = CLAUDE_MODEL,
) -> dict | None:
    """Send verification request to Claude via streaming and parse the JSON response."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Use streaming to support large max_tokens values
            text = ""
            stop_reason = None

            with client.messages.stream(
                model=model,
                max_tokens=64000,
                temperature=0.0,
                system=VERIFICATION_PROMPT,
                messages=[{"role": "user", "content": content}],
            ) as stream:
                for event_text in stream.text_stream:
                    text += event_text
                # Get the final message for stop_reason
                final_message = stream.get_final_message()
                stop_reason = final_message.stop_reason

            # Check for truncated output
            if stop_reason == "max_tokens":
                logging.warning("  Response truncated (hit max_tokens).")
                return None

            # Parse JSON — strip markdown fences if present
            clean = text.strip()
            if clean.startswith("```"):
                first_newline = clean.find("\n")
                clean = clean[first_newline + 1:] if first_newline != -1 else clean[3:]
            if clean.endswith("```"):
                clean = clean[: clean.rfind("```")]
            clean = clean.strip()

            result = json.loads(clean)
            return result

        except anthropic.RateLimitError:
            wait = RETRY_BASE_DELAY * attempt
            logging.warning(f"  Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
        except anthropic.APIError as e:
            logging.error(f"  API error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(10 * attempt)
            else:
                return None
        except json.JSONDecodeError as e:
            logging.error(f"  Failed to parse Claude response as JSON: {e}")
            logging.debug(f"  Raw response (first 500 chars): {text[:500]}...")
            if attempt < MAX_RETRIES:
                time.sleep(5)
            else:
                return None
        except Exception as e:
            logging.error(f"  Unexpected error: {e}")
            return None

    return None


def verify_entries_chunked(
    client: anthropic.Anthropic,
    entries: list,
    pdf_pages: list[tuple[str, str]],
    active_model: str,
) -> tuple[list, list]:
    """
    Verify a list of entries, automatically splitting into chunks if needed.

    Returns (verified_entries, corrections).
    """
    # Split into chunks of MAX_ENTRIES_PER_CHUNK
    chunks = [
        entries[i : i + MAX_ENTRIES_PER_CHUNK]
        for i in range(0, len(entries), MAX_ENTRIES_PER_CHUNK)
    ]

    all_verified: list = []
    all_corrections: list = []

    for chunk_idx, chunk in enumerate(chunks):
        if len(chunks) > 1:
            logging.info(f"    Chunk {chunk_idx + 1}/{len(chunks)}: {len(chunk)} entries")

        entries_json = json.dumps(chunk, indent=2, ensure_ascii=False)
        content = build_message_content(entries_json, pdf_pages)
        result = call_claude(client, content, model=active_model)

        if result and "verified_entries" in result:
            all_verified.extend(result["verified_entries"])
            all_corrections.extend(result.get("corrections_log", []))
        else:
            logging.warning(f"    Chunk {chunk_idx + 1} failed — keeping original entries.")
            all_verified.extend(chunk)

        # Small delay between chunks
        if chunk_idx < len(chunks) - 1:
            time.sleep(1)

    return all_verified, all_corrections

# ---------------------------------------------------------------------------
# PROGRESS TRACKING
# ---------------------------------------------------------------------------

def load_progress(progress_file: Path) -> dict:
    """Load verification progress (which PDF indices are done)."""
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"verified_pdf_indices": [], "total_corrections": 0}


def save_progress(progress_file: Path, progress: dict):
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# RESULT SAVING
# ---------------------------------------------------------------------------

def load_existing_verified(output_path: Path) -> list:
    """Load already-verified entries from the output file."""
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_verified(output_path: Path, entries: list):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def run_verification(
    mode: str,
    resume: bool = False,
    start_page: int | None = None,
    end_page: int | None = None,
    model: str | None = None,
):
    cfg = CONFIG[mode]
    setup_logging(cfg["log_file"])
    active_model = model or CLAUDE_MODEL

    logging.info("=" * 60)
    logging.info("Skiri Pawnee Dictionary — Verification & Normalization")
    logging.info(f"Section: {cfg['section_name']}")
    logging.info(f"Model:   {active_model}")
    logging.info("=" * 60)

    # --- API client ---
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        logging.error("CLAUDE_API_KEY environment variable not set. Aborting.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    # --- Load input data ---
    input_path = cfg["input_json"]
    if not input_path.exists():
        logging.error(f"Input JSON not found: {input_path}")
        sys.exit(1)

    logging.info(f"Loading extracted entries from {input_path.name}...")
    with open(input_path, "r", encoding="utf-8") as f:
        all_entries = json.load(f)
    logging.info(f"  Loaded {len(all_entries)} entries.")

    # --- Discover PDF files ---
    pdf_files = get_sorted_pdf_list(cfg["pdf_dir"])
    if not pdf_files:
        logging.error(f"No PDF files found in {cfg['pdf_dir']}")
        sys.exit(1)
    logging.info(f"  Found {len(pdf_files)} source PDFs in {cfg['pdf_dir'].name}/")

    # --- Build page-number → PDF-file mapping ---
    if mode == "s2e":
        page_to_pdf = build_s2e_mapping(all_entries, pdf_files)
    else:
        page_to_pdf = build_e2s_mapping(all_entries, pdf_files)

    # --- Group entries by PDF ---
    pdf_groups, unmatched = group_entries_by_pdf(all_entries, mode, page_to_pdf)
    pdf_indices = sorted(pdf_groups.keys())
    logging.info(f"  Entries grouped into {len(pdf_indices)} PDF-file batches.")

    # --- Apply --start-page / --end-page filters ---
    # These refer to PDF file numbers (1-based for user convenience)
    if start_page is not None:
        pdf_indices = [i for i in pdf_indices if (i + 1) >= start_page]
    if end_page is not None:
        pdf_indices = [i for i in pdf_indices if (i + 1) <= end_page]

    # --- Resume support ---
    progress = load_progress(cfg["progress_file"]) if resume else {
        "verified_pdf_indices": [], "total_corrections": 0
    }
    verified_entries = load_existing_verified(cfg["output_json"]) if resume else []

    if resume:
        already_done = set(progress["verified_pdf_indices"])
        pdf_indices = [i for i in pdf_indices if i not in already_done]
        logging.info(
            f"  Resuming — {len(already_done)} PDF batches already done, "
            f"{len(pdf_indices)} remaining."
        )

    if not pdf_indices:
        logging.info("No PDF batches to process. Done!")
        return

    logging.info(f"  Will process {len(pdf_indices)} PDF batches.\n")

    # --- Corrections log ---
    all_corrections: list[dict] = []

    # --- Process each PDF batch ---
    for seq, pdf_idx in enumerate(pdf_indices):
        entries_for_pdf = pdf_groups[pdf_idx]
        pdf_path = pdf_files[pdf_idx]
        pdf_name = pdf_path.name

        logging.info(
            f"[{seq + 1}/{len(pdf_indices)}] {pdf_name}: "
            f"{len(entries_for_pdf)} entries"
        )

        # Load source PDF(s): current + next for cross-page context
        pdf_pages: list[tuple[str, str]] = []
        b64 = load_pdf_as_base64(pdf_path)
        if b64:
            pdf_pages.append((f"Source PDF — {pdf_name}", b64))
        else:
            logging.warning(f"  Could not load {pdf_name}. Passing entries through unverified.")
            verified_entries.extend(entries_for_pdf)
            progress["verified_pdf_indices"].append(pdf_idx)
            save_progress(cfg["progress_file"], progress)
            save_verified(cfg["output_json"], verified_entries)
            continue

        # Load next PDF for cross-page context
        if pdf_idx + 1 < len(pdf_files):
            next_path = pdf_files[pdf_idx + 1]
            b64_next = load_pdf_as_base64(next_path)
            if b64_next:
                pdf_pages.append((f"Next page — {next_path.name}", b64_next))

        # Verify entries (automatically splits into chunks if needed)
        page_verified, page_corrections = verify_entries_chunked(
            client, entries_for_pdf, pdf_pages, active_model
        )

        verified_entries.extend(page_verified)
        all_corrections.extend(page_corrections)
        progress["total_corrections"] += len(page_corrections)

        if page_corrections:
            logging.info(f"  ✓ Verified with {len(page_corrections)} correction(s):")
            for c in page_corrections[:5]:
                ident = c.get("entry_identifier", "?")
                field = c.get("field", "?")
                orig  = str(c.get("original", ""))[:40]
                fixed = str(c.get("corrected", ""))[:40]
                why   = c.get("reason", "")
                logging.info(f"    - [{ident}] {field}: '{orig}' → '{fixed}' ({why})")
            if len(page_corrections) > 5:
                logging.info(f"    ... and {len(page_corrections) - 5} more.")
        else:
            logging.info("  ✓ All entries correct — no corrections needed.")

        # Save progress after each batch
        progress["verified_pdf_indices"].append(pdf_idx)
        save_progress(cfg["progress_file"], progress)
        save_verified(cfg["output_json"], verified_entries)

        # Rate-limit courtesy delay
        if seq < len(pdf_indices) - 1:
            time.sleep(1)

    # Append unmatched entries (no page info — pass through unverified)
    if unmatched:
        logging.info(f"Appending {len(unmatched)} unmatched entries (unverified).")
        verified_entries.extend(unmatched)
        save_verified(cfg["output_json"], verified_entries)

    # Save full corrections log
    corrections_path = cfg["output_json"].with_name(
        cfg["output_json"].stem + "_corrections.json"
    )
    with open(corrections_path, "w", encoding="utf-8") as f:
        json.dump(all_corrections, f, indent=2, ensure_ascii=False)

    # --- Summary ---
    logging.info("")
    logging.info("=" * 60)
    logging.info("VERIFICATION COMPLETE")
    logging.info("=" * 60)
    logging.info(f"Section:            {cfg['section_name']}")
    logging.info(f"Total entries out:  {len(verified_entries)}")
    logging.info(f"Total corrections:  {progress['total_corrections']}")
    logging.info(f"Output:             {cfg['output_json']}")
    logging.info(f"Corrections log:    {corrections_path}")
    logging.info("=" * 60)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify Skiri Pawnee dictionary entries against source PDFs using Claude.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["s2e", "e2s"],
        help="Which section to verify: s2e (Skiri-to-English) or e2s (English-to-Skiri)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint instead of starting fresh",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="Start verification at this PDF file number (1-based, inclusive)",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="End verification at this PDF file number (1-based, inclusive)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Override Claude model (default: {CLAUDE_MODEL})",
    )

    args = parser.parse_args()

    run_verification(
        mode=args.mode,
        resume=args.resume,
        start_page=args.start_page,
        end_page=args.end_page,
        model=args.model,
    )


if __name__ == "__main__":
    main()
