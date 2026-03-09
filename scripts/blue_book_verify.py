#!/usr/bin/env python3
"""
Phase 2.2 — Blue Book Cross-Verification
==========================================
Uses the Blue Book (Pari Pakuru') as a verification corpus against the Parks
dictionary. Two-stage pipeline:

  STAGE 1 — Extraction (--extract):
    Parse the Blue Book text file lesson-by-lesson and send each chunk to
    Gemini API to extract structured vocabulary entries. Saves to a JSON
    extraction file (blue_book_extracted.json) with checkpointing.

  STAGE 2 — Matching + DB Import (--match):
    Load extracted entries, normalize BB orthography → Parks orthography,
    match against lexical_entries in SQLite, then:
      - Create blue_book_attestations table
      - Populate matches (and gaps)
      - Add Blue Book dialogues as new examples where not already present
      - Update lexical_entries with blue_book_attested flag
      - Write report

Usage:
    # Full pipeline (extract then match):
    python scripts/blue_book_verify.py \\
        --text "pari pakuru/Blue_Book_Pari_Pakuru.txt" \\
        --db skiri_pawnee.db \\
        --extracted blue_book_extracted.json \\
        --report reports/phase_2_2_blue_book.txt

    # Extract only (uses Gemini):
    python scripts/blue_book_verify.py --extract-only \\
        --text "pari pakuru/Blue_Book_Pari_Pakuru.txt" \\
        --extracted blue_book_extracted.json

    # Match only (uses already-extracted JSON):
    python scripts/blue_book_verify.py --match-only \\
        --extracted blue_book_extracted.json \\
        --db skiri_pawnee.db \\
        --report reports/phase_2_2_blue_book.txt

    # Dry run (no DB writes):
    python scripts/blue_book_verify.py \\
        --extracted blue_book_extracted.json \\
        --db skiri_pawnee.db \\
        --dry-run

Dependencies: Python 3.8+, sqlite3 (stdlib), google-genai (for extraction)
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 4  # seconds
MAX_PAGES_PER_CHUNK = 6  # lessons larger than this get split into sub-chunks

# Pages in the Blue Book text that are not lesson content
SKIP_PAGES = set(range(1, 29))  # front matter (title, TOC, sound key)

# Lesson detection: all-caps LESSON N anywhere in line (avoids "Lesson 3" refs
# which use mixed case). The false positives all used title-case "Lesson".
LESSON_HEADER_RE = re.compile(r'\bLESSON\s+(\d+)\b')
# Bare "LESSON" without number on its own line (OCR dropped the number)
LESSON_BARE_RE = re.compile(r'^LESSON\s*$', re.MULTILINE)

# Pronunciation in parentheses: (rak-ta-rih-ka-ru-kus)
BB_PRONUNCIATION_RE = re.compile(r'\(([a-z0-9\-\'\. ]+)\)', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Gemini system prompt
# ---------------------------------------------------------------------------

GEMINI_SYSTEM_INSTRUCTION = """\
You are a computational linguist processing pages from "Pari Pakuru'", a 1979 \
Pawnee language textbook (Skiri dialect). Your task is to extract all Pawnee \
vocabulary items from the provided text and return them as structured JSON.

ORTHOGRAPHY NOTES:
- The textbook uses a practical (learner) orthography, different from the Parks \
  linguistic dictionary notation.
- Pawnee words appear in BASIC WORDS sections, ADDITIONAL WORDS sections, USEFUL \
  PHRASES sections, and in Dialogue lines.
- Pronunciation guides appear in parentheses after the word, using hyphens to \
  show syllables, e.g., (rak-ta-rih-ka-ru-kus).
- Pawnee words often contain: r, k, t, s, ts, p, h, w, ' (glottal stop).
- The apostrophe ' marks a glottal stop (voice catch) in this orthography.
- (SK) = Skiri dialect, (SB) = South Band dialect. Prefer SK forms when both given.
- The link (•) or dot between words indicates root boundaries.
- Lines with only zeros (0, u, a, B, etc.) are image artifacts from the PDF — ignore them.

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "entries": [
    {
      "skiri_form": "exact Pawnee word/phrase as written in text",
      "bb_pronunciation": "(hyphenated form if given, else null)",
      "english_translation": "English gloss",
      "context_type": "BASIC_WORDS | ADDITIONAL_WORDS | DIALOGUE | PHRASE | GRAMMAR_EXAMPLE",
      "dialect_note": "SK | SB | both | null",
      "full_sentence_pawnee": "full dialogue sentence if from dialogue, else null",
      "full_sentence_english": "English translation of full sentence, else null",
      "lesson_number": <integer or null>,
      "page_number": <integer>
    }
  ]
}

RULES:
1. Extract EVERY Pawnee word or phrase with an English equivalent.
2. For dialogues, extract each Pawnee sentence as one entry (full sentence), \
   AND individually extract any standalone vocabulary words used.
3. Skip image artifacts, page numbers, and pure English text.
4. If a section header like "BASIC WORDS" appears, all words in that block \
   get context_type "BASIC_WORDS", etc.
5. Verb conjugation examples (e.g., in VERB SET sections) count as GRAMMAR_EXAMPLE.
6. If a word appears in both SK and SB forms, create ONE entry with the SK form \
   and note dialect_note = "both".
7. Do NOT invent translations. Only extract what is explicitly given in the text.
"""

# ---------------------------------------------------------------------------
# Stage 1: Parse Blue Book text into lesson chunks
# ---------------------------------------------------------------------------

def parse_blue_book_text(text_path: Path) -> list[dict]:
    """
    Parse the Blue Book extracted text into lesson-sized chunks.
    Returns list of: {lesson_number, pages: [int], page_texts: [(page_num, text)]}

    Lessons with more than MAX_PAGES_PER_CHUNK pages are automatically split
    into sequential sub-chunks so Gemini gets manageable input sizes.
    """
    raw = text_path.read_text(encoding='utf-8')

    # Split into pages
    page_blocks = re.split(r'={10,}\s*\nPAGE (\d+)\s*\n={10,}', raw)
    pages = {}
    for i in range(1, len(page_blocks), 2):
        page_num = int(page_blocks[i])
        page_text = page_blocks[i + 1] if i + 1 < len(page_blocks) else ""
        pages[page_num] = page_text.strip()

    # Group pages into lessons (page_texts kept as list for later chunking)
    lessons_raw = []
    current_lesson = None
    current_page_texts = []
    last_seen_lesson = 0

    for page_num in sorted(pages.keys()):
        if page_num in SKIP_PAGES:
            continue

        page_text = pages[page_num]
        lesson_match = LESSON_HEADER_RE.search(page_text)
        bare_match = LESSON_BARE_RE.search(page_text) if not lesson_match else None

        if lesson_match:
            new_lesson = int(lesson_match.group(1))
            if current_lesson is not None:
                lessons_raw.append({"lesson_number": current_lesson, "page_texts": list(current_page_texts)})
            current_lesson = new_lesson
            last_seen_lesson = new_lesson
            current_page_texts = [(page_num, page_text)]
        elif bare_match:
            new_lesson = last_seen_lesson + 1
            log.info(f"Page {page_num}: bare LESSON header, inferred Lesson {new_lesson}")
            if current_lesson is not None:
                lessons_raw.append({"lesson_number": current_lesson, "page_texts": list(current_page_texts)})
            current_lesson = new_lesson
            last_seen_lesson = new_lesson
            current_page_texts = [(page_num, page_text)]
        elif current_lesson is not None:
            current_page_texts.append((page_num, page_text))
        else:
            if not lessons_raw and current_lesson is None:
                current_lesson = 0
                current_page_texts = [(page_num, page_text)]
            else:
                current_page_texts.append((page_num, page_text))

    if current_lesson is not None:
        lessons_raw.append({"lesson_number": current_lesson, "page_texts": list(current_page_texts)})

    # Post-process: split any lesson with > MAX_PAGES_PER_CHUNK pages
    lessons = []
    for lesson in lessons_raw:
        pts = lesson["page_texts"]
        if len(pts) <= MAX_PAGES_PER_CHUNK:
            pages_list = [p for p, _ in pts]
            lessons.append({
                "lesson_number": lesson["lesson_number"],
                "pages": pages_list,
                "first_page": pages_list[0],
                "is_split": False,
                "text": "\n".join(f"[PAGE {p}]\n{t}" for p, t in pts),
            })
        else:
            for chunk_idx in range(0, len(pts), MAX_PAGES_PER_CHUNK):
                chunk = pts[chunk_idx:chunk_idx + MAX_PAGES_PER_CHUNK]
                pages_list = [p for p, _ in chunk]
                lessons.append({
                    "lesson_number": lesson["lesson_number"],
                    "pages": pages_list,
                    "first_page": pages_list[0],
                    "is_split": True,
                    "text": "\n".join(f"[PAGE {p}]\n{t}" for p, t in chunk),
                })

    n_base = sum(1 for l in lessons if not l["is_split"])
    n_split = sum(1 for l in lessons if l["is_split"])
    log.info(f"Parsed {len(lessons)} chunks ({n_base} single-lesson, {n_split} from split lessons) "
             f"from Blue Book text (pages {min(pages.keys())} - {max(pages.keys())})")
    return lessons


# ---------------------------------------------------------------------------
# Stage 1: Gemini extraction
# ---------------------------------------------------------------------------

def _recover_partial_json(text: str, error_pos: int) -> dict | None:
    """
    Attempt to salvage a partial JSON response by truncating at the last
    complete entry object before the error position and closing the structure.
    """
    trunc = text[:error_pos]
    # Find the last complete entry closing brace
    last_brace = trunc.rfind('}')
    if last_brace < 10:
        return None
    # Try different ways to close the JSON array/object
    for suffix in ['\n  ]\n}', '\n]\n}', ']}']:
        candidate = trunc[:last_brace + 1] + suffix
        try:
            result = json.loads(candidate)
            if isinstance(result, dict) and result.get('entries'):
                return result
        except json.JSONDecodeError:
            pass
    return None


def _call_gemini(client, prompt_text: str, model_name: str):
    """Send a request to Gemini. Returns parsed JSON dict or None."""
    from google.genai import types
    try:
        from google.api_core import exceptions as google_exceptions
        rate_limit_errors = (
            google_exceptions.ResourceExhausted,
            google_exceptions.TooManyRequests,
        )
        server_errors = (
            google_exceptions.ServiceUnavailable,
            google_exceptions.InternalServerError,
        )
    except ImportError:
        rate_limit_errors = ()
        server_errors = ()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt_text],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    max_output_tokens=16384,
                    response_mime_type="application/json",
                ),
            )
            text = response.text.strip()
            # Strip markdown fences if present (shouldn't be with JSON mode)
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)

        except rate_limit_errors as e:
            wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning(f"Rate limited (attempt {attempt}/{MAX_RETRIES}), "
                        f"waiting {wait}s: {e}")
            time.sleep(wait)

        except server_errors as e:
            wait = RETRY_BACKOFF_BASE * attempt
            log.warning(f"Server error (attempt {attempt}/{MAX_RETRIES}), "
                        f"waiting {wait}s: {e}")
            time.sleep(wait)

        except json.JSONDecodeError as e:
            log.warning(f"Gemini JSON parse error (attempt {attempt}): {e}")
            # Try partial recovery — salvage entries before the error position
            recovered = _recover_partial_json(text, e.pos)
            if recovered and recovered.get("entries"):
                log.info(f"Partial JSON recovery: {len(recovered['entries'])} entries salvaged")
                return recovered
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                return None

        except Exception as e:
            log.warning(f"Gemini error (attempt {attempt}): {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE)
            else:
                return None

    return None


def extract_with_gemini(
    lessons: list[dict],
    checkpoint_path: Path,
    model_name: str = GEMINI_MODEL,
) -> list[dict]:
    """
    Extract vocabulary from each lesson using Gemini API.
    Returns list of extracted entry dicts (flattened from all lessons).
    Supports checkpointing (resume).
    """
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI-API-KEY')
    if not api_key:
        log.error("GEMINI_API_KEY not set.")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        log.error("google-genai not installed: pip install google-genai")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Load checkpoint
    checkpoint = {}
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        log.info(f"Resuming from checkpoint: {len(checkpoint)} lessons done")

    all_entries = []
    # Re-add already-completed entries from checkpoint
    for lesson_key, entries in checkpoint.items():
        all_entries.extend(entries)

    for lesson in lessons:
        # Checkpoint key: "lesson_N" for unsplit, "lesson_N_pPAGE" for split chunks
        if lesson["is_split"]:
            lesson_key = f"lesson_{lesson['lesson_number']}_p{lesson['first_page']}"
        else:
            lesson_key = f"lesson_{lesson['lesson_number']}"

        if lesson_key in checkpoint:
            log.info(f"  Skipping {lesson_key} (already done)")
            continue

        log.info(f"Processing {lesson_key} "
                 f"(pages {lesson['pages'][0]}-{lesson['pages'][-1]}, "
                 f"{len(lesson['text'])} chars)...")

        prompt = (
            f"Extract all Pawnee vocabulary from this Blue Book lesson text.\n"
            f"This is Lesson {lesson['lesson_number']} "
            f"(pages {lesson['pages'][0]}-{lesson['pages'][-1]}).\n\n"
            f"TEXT:\n{lesson['text']}"
        )

        result = _call_gemini(client, prompt, model_name)

        if result and "entries" in result:
            entries = result["entries"]
            for e in entries:
                if not e.get("lesson_number"):
                    e["lesson_number"] = lesson["lesson_number"]
            all_entries.extend(entries)
            checkpoint[lesson_key] = entries
            log.info(f"  -> {len(entries)} entries extracted")
        else:
            log.warning(f"  -> No entries from Gemini for {lesson_key}")
            checkpoint[lesson_key] = []

        checkpoint_path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        time.sleep(1)

    log.info(f"Total extracted: {len(all_entries)} entries")
    return all_entries


# ---------------------------------------------------------------------------
# Stage 2: Orthographic normalization (BB → Parks)
# ---------------------------------------------------------------------------

def normalize_bb_to_parks(bb_form: str) -> str:
    """
    Convert Blue Book orthography to Parks-compatible form for matching.

    Key mappings (from project scope and Blue Book pp. xix–xxv):
      BB `ts` → Parks `c`   (but note: at start of word, ts = Parks c)
      BB `'` → Parks `ʔ`   (glottal stop)
      BB `a` (long) → Parks `aa`   (long vowel — hard without explicit marking)
      BB long vowels marked by underline in book → not in text extraction
      BB link dot `•` → remove (structural marker)
      BB `•` as separator in compound → keep structure but normalize
    """
    if not bb_form:
        return ""

    # Work on a cleaned version
    s = bb_form.strip()

    # Remove link dot (word boundary marker in BB)
    s = s.replace('•', '')

    # Remove parenthetical pronunciation guides
    s = re.sub(r'\([a-z\-\'\. ]+\)', '', s, flags=re.IGNORECASE)

    # Strip leading/trailing whitespace
    s = s.strip()

    # Convert BB glottal stop apostrophe → Parks ʔ
    # (BB uses both ' and ' — handle both)
    s = s.replace("'", "ʔ").replace("\u2019", "ʔ").replace("\u02bc", "ʔ")

    # Lowercase for comparison
    s = s.lower()

    # Convert BB `ts` → Parks `c`
    # Must do this carefully to not affect `s` that follows `t` in other ways
    s = re.sub(r'ts', 'c', s)

    return s


def build_dictionary_index(conn: sqlite3.Connection) -> dict:
    """
    Build a lookup index from the SQLite dictionary for fast matching.
    Returns dict with multiple keys per entry for flexible lookup.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT entry_id, headword, normalized_form, phonetic_form,
               simplified_pronunciation, grammatical_class
        FROM lexical_entries
    """)
    rows = cur.fetchall()

    index = {}  # normalized_key → list of entry dicts
    for row in rows:
        entry_id, headword, normalized_form, phonetic_form, simp_pron, gram_class = row
        entry = {
            "entry_id": entry_id,
            "headword": headword,
            "normalized_form": normalized_form,
            "phonetic_form": phonetic_form,
            "simplified_pronunciation": simp_pron,
            "grammatical_class": gram_class,
        }

        # Index by multiple normalized keys
        keys_to_index = set()

        if headword:
            keys_to_index.add(_normalize_for_index(headword))

        if normalized_form:
            keys_to_index.add(_normalize_for_index(normalized_form))

        # Also index a "loose" version (no glottal, no diacritics)
        if headword:
            keys_to_index.add(_loose_normalize(headword))
        if normalized_form:
            keys_to_index.add(_loose_normalize(normalized_form))

        for key in keys_to_index:
            if key:
                index.setdefault(key, []).append(entry)

    log.info(f"Dictionary index: {len(index)} unique keys for {len(rows)} entries")
    return index


def _normalize_for_index(form: str) -> str:
    """Strict normalization for dictionary key lookup."""
    if not form:
        return ""
    s = form.lower().strip()
    # Standardize glottal stop
    s = s.replace("'", "ʔ").replace("\u2019", "ʔ").replace("\u02bc", "ʔ")
    # Remove structural chars from Parks notation
    s = re.sub(r'[\[\]•–—\s\(\)\{\}/,]', '', s)
    # Remove circumflex (long vowel marker in normalized form) → get base
    for c, base in [('â', 'aa'), ('î', 'ii'), ('û', 'uu')]:
        s = s.replace(c, base)
    return s


def _loose_normalize(form: str) -> str:
    """Loose normalization: remove glottal, diacritics, structural chars."""
    if not form:
        return ""
    s = _normalize_for_index(form)
    s = s.replace('ʔ', '')  # remove glottal
    s = s.replace('č', 'ts').replace('c', 'ts')  # unify affricates
    return s


def _bb_to_index_key(bb_form: str) -> str:
    """Normalize a BB form to the same key space as the dictionary index."""
    parks_form = normalize_bb_to_parks(bb_form)
    return _normalize_for_index(parks_form)


def _bb_to_loose_key(bb_form: str) -> str:
    parks_form = normalize_bb_to_parks(bb_form)
    return _loose_normalize(parks_form)


def _strip_bb_verb_prefix(bb_form: str) -> str:
    """
    Strip common BB verb inflection prefixes/particles to expose the root stem.
    The Blue Book uses prefixes like: ti• (3rd person), tiku• (1st person),
    tuks• (past evidential), we (continuative), tat• (1st person forms),
    t' (quotative evidential), siks•/suks• (imperative 2nd sg/pl).

    Returns the stripped form, or the original if no prefix found.
    """
    s = bb_form.strip()
    # Remove leading 'we ' particle (continuative aspect)
    s = re.sub(r"^we\s+", "", s, flags=re.IGNORECASE)
    # Remove evidential t' prefix
    s = re.sub(r"^t['\u2019]", "", s)
    # Remove common indicator prefixes (with optional link dot •)
    for prefix in [
        r"^tiku[•\.]",    # 1st person possessed/verb
        r"^tuks[•\.]",    # past/evidential
        r"^tat[•\.]",     # 1st person
        r"^tas[•\.]",     # 2nd person
        r"^ti[•\.]",      # 3rd person indicator / imperfective
        r"^sitat[•\.]",   # dual 1st person
        r"^sitas[•\.]",   # dual 2nd person
        r"^siti[•\.]",    # dual 3rd person
        r"^siks[•\.]",    # imperative 2nd sg
        r"^suks[•\.]",    # imperative
        r"^stiks[•\.]",   # imperative go-away form
    ]:
        stripped = re.sub(prefix, "", s, flags=re.IGNORECASE).strip("•. ")
        if stripped and stripped != s and len(stripped) >= 3:
            s = stripped
            break
    return s


def match_entry(bb_form: str, index: dict) -> tuple[list, str]:
    """
    Try to match a BB form against the dictionary index.
    Returns (matches, match_type) where match_type is one of:
      'exact_normalized', 'loose', 'prefix', 'stem', 'none'
    """
    if not bb_form:
        return [], 'none'

    # 1. Strict normalized match
    key = _bb_to_index_key(bb_form)
    if key and key in index:
        return index[key], 'exact_normalized'

    # 2. Loose match (no glottal, unified affricates)
    loose = _bb_to_loose_key(bb_form)
    if loose and loose in index:
        return index[loose], 'loose'

    # 3. Prefix match (BB form might be a shorter surface form)
    if key and len(key) >= 4:
        prefix_matches = [
            entry for k, entries in index.items()
            if k.startswith(key) or key.startswith(k)
            for entry in entries
        ]
        if prefix_matches:
            seen = set()
            unique = []
            for e in prefix_matches:
                if e['entry_id'] not in seen:
                    seen.add(e['entry_id'])
                    unique.append(e)
            return unique[:3], 'prefix'

    # 4. Verb stem match — strip inflection prefixes and retry exact/loose
    stem = _strip_bb_verb_prefix(bb_form)
    if stem and stem != bb_form:
        stem_key = _bb_to_index_key(stem)
        if stem_key and stem_key in index:
            return index[stem_key], 'stem'
        stem_loose = _bb_to_loose_key(stem)
        if stem_loose and stem_loose in index:
            return index[stem_loose], 'stem'

    return [], 'none'


# ---------------------------------------------------------------------------
# Stage 2: Database operations
# ---------------------------------------------------------------------------

def create_attestation_table(conn: sqlite3.Connection):
    """Create blue_book_attestations table if it doesn't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS blue_book_attestations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bb_skiri_form TEXT NOT NULL,
            bb_pronunciation TEXT,
            bb_english TEXT,
            context_type TEXT,
            dialect_note TEXT,
            lesson_number INTEGER,
            page_number INTEGER,
            full_sentence_pawnee TEXT,
            full_sentence_english TEXT,
            entry_id TEXT REFERENCES lexical_entries(entry_id),
            match_type TEXT,
            match_confidence REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_bba_entry_id
            ON blue_book_attestations(entry_id);
        CREATE INDEX IF NOT EXISTS idx_bba_lesson
            ON blue_book_attestations(lesson_number);
        CREATE INDEX IF NOT EXISTS idx_bba_match_type
            ON blue_book_attestations(match_type);
    """)
    conn.commit()
    log.info("blue_book_attestations table ready")


def add_bb_attested_column(conn: sqlite3.Connection):
    """Add blue_book_attested column to lexical_entries if not present."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(lexical_entries)")
    cols = [row[1] for row in cur.fetchall()]
    if 'blue_book_attested' not in cols:
        conn.execute(
            "ALTER TABLE lexical_entries ADD COLUMN blue_book_attested INTEGER DEFAULT 0"
        )
        conn.commit()
        log.info("Added blue_book_attested column to lexical_entries")


def insert_attestations(
    conn: sqlite3.Connection,
    extracted_entries: list[dict],
    index: dict,
    dry_run: bool = False,
) -> dict:
    """
    Match extracted BB entries against dictionary and insert into
    blue_book_attestations. Returns stats dict.
    """
    stats = {
        "total": 0,
        "matched_exact": 0,
        "matched_loose": 0,
        "matched_prefix": 0,
        "matched_stem": 0,
        "unmatched": 0,
        "skipped_empty": 0,
        "examples_added": 0,
    }

    cur = conn.cursor()

    # Get existing example (skiri_text, entry_id) pairs to avoid duplication
    cur.execute("SELECT entry_id, skiri_text FROM examples")
    existing_examples = {(r[0], r[1]) for r in cur.fetchall()}

    rows_to_insert = []
    example_rows = []
    entries_to_attest = set()

    for entry in extracted_entries:
        bb_form = (entry.get("skiri_form") or "").strip()
        if not bb_form:
            stats["skipped_empty"] += 1
            continue

        stats["total"] += 1

        bb_pron = entry.get("bb_pronunciation")
        bb_english = (entry.get("english_translation") or "").strip()
        context_type = entry.get("context_type", "UNKNOWN")
        dialect = entry.get("dialect_note")
        lesson = entry.get("lesson_number")
        page = entry.get("page_number")
        full_pawnee = entry.get("full_sentence_pawnee")
        full_english = entry.get("full_sentence_english")

        matches, match_type = match_entry(bb_form, index)

        if match_type == 'exact_normalized':
            stats["matched_exact"] += 1
            confidence = 1.0
        elif match_type == 'loose':
            stats["matched_loose"] += 1
            confidence = 0.8
        elif match_type == 'prefix':
            stats["matched_prefix"] += 1
            confidence = 0.5
        elif match_type == 'stem':
            stats["matched_stem"] += 1
            confidence = 0.6
        else:
            stats["unmatched"] += 1
            confidence = 0.0

        # Take first match for primary link (best match)
        primary_match = matches[0] if matches else None
        entry_id = primary_match["entry_id"] if primary_match else None

        if entry_id:
            entries_to_attest.add(entry_id)

        rows_to_insert.append((
            bb_form,
            bb_pron,
            bb_english or None,
            context_type,
            dialect,
            lesson,
            page,
            full_pawnee,
            full_english,
            entry_id,
            match_type,
            confidence,
            "; ".join(m["entry_id"] for m in matches[1:]) if len(matches) > 1 else None,
        ))

        # Add full dialogue sentences as examples (for matched entries)
        if entry_id and full_pawnee and full_english:
            key = (entry_id, full_pawnee)
            if key not in existing_examples:
                example_rows.append((
                    entry_id,
                    full_pawnee,
                    full_english,
                    f"Blue Book Lesson {lesson}, p.{page}",
                ))
                existing_examples.add(key)
                stats["examples_added"] += 1

    if not dry_run:
        cur.executemany("""
            INSERT INTO blue_book_attestations (
                bb_skiri_form, bb_pronunciation, bb_english, context_type,
                dialect_note, lesson_number, page_number,
                full_sentence_pawnee, full_sentence_english,
                entry_id, match_type, match_confidence, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)

        if example_rows:
            cur.executemany("""
                INSERT INTO examples (entry_id, skiri_text, english_translation, usage_context)
                VALUES (?, ?, ?, ?)
            """, example_rows)

        # Update blue_book_attested flag
        if entries_to_attest:
            cur.executemany(
                "UPDATE lexical_entries SET blue_book_attested = 1 WHERE entry_id = ?",
                [(eid,) for eid in entries_to_attest],
            )

        conn.commit()
        log.info(f"Inserted {len(rows_to_insert)} attestation rows")
        log.info(f"Added {stats['examples_added']} new examples from BB dialogues")
        log.info(f"Attested {len(entries_to_attest)} dictionary entries")
    else:
        log.info(f"[DRY RUN] Would insert {len(rows_to_insert)} rows, "
                 f"{stats['examples_added']} examples")

    return stats


# ---------------------------------------------------------------------------
# Stage 2: Report generation
# ---------------------------------------------------------------------------

def generate_report(
    conn: sqlite3.Connection,
    stats: dict,
    output_path: Path,
    extracted_entries: list[dict],
):
    """Write a Phase 2.2 verification report."""
    cur = conn.cursor()

    # Unmatched entries (gaps)
    cur.execute("""
        SELECT bb_skiri_form, bb_english, context_type, lesson_number, page_number
        FROM blue_book_attestations
        WHERE match_type = 'none'
        ORDER BY lesson_number, page_number
    """)
    gaps = cur.fetchall()

    # Matched entries summary per lesson
    cur.execute("""
        SELECT lesson_number,
               COUNT(*) as total,
               SUM(CASE WHEN match_type != 'none' THEN 1 ELSE 0 END) as matched,
               SUM(CASE WHEN match_type = 'none' THEN 1 ELSE 0 END) as unmatched
        FROM blue_book_attestations
        GROUP BY lesson_number
        ORDER BY lesson_number
    """)
    by_lesson = cur.fetchall()

    # Total attested entries
    cur.execute("SELECT COUNT(*) FROM lexical_entries WHERE blue_book_attested = 1")
    total_attested = cur.fetchone()[0]

    # Total dictionary entries
    cur.execute("SELECT COUNT(*) FROM lexical_entries")
    total_dict = cur.fetchone()[0]

    lines = [
        "=" * 70,
        "PHASE 2.2 — BLUE BOOK CROSS-VERIFICATION REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        "SUMMARY",
        "-" * 40,
        f"Total BB vocabulary items extracted:  {stats['total']}",
        f"  Matched (exact normalized):         {stats['matched_exact']}",
        f"  Matched (loose / fuzzy):            {stats['matched_loose']}",
        f"  Matched (prefix):                   {stats['matched_prefix']}",
        f"  Matched (verb stem):                {stats['matched_stem']}",
        f"  Unmatched (gaps):                   {stats['unmatched']}",
        f"  Skipped (empty form):               {stats['skipped_empty']}",
        f"",
        f"New examples added to DB:             {stats['examples_added']}",
        f"Dictionary entries with BB attestation: {total_attested} / {total_dict} "
        f"({100*total_attested/total_dict:.1f}%)",
        "",
        "BY LESSON",
        "-" * 40,
    ]

    for row in by_lesson:
        lesson_num, total, matched, unmatched = row
        pct = 100 * matched / total if total else 0
        lines.append(
            f"  Lesson {lesson_num:2d}: {total:3d} items, "
            f"{matched:3d} matched ({pct:.0f}%), {unmatched:3d} gaps"
        )

    lines += [
        "",
        f"GAPS — BB WORDS NOT IN PARKS DICTIONARY ({len(gaps)} total)",
        "-" * 40,
        "(These may be: loanwords, dialectal variants, short function words,",
        " phrase components, or parsing/orthography differences)",
        "",
    ]

    for bb_form, bb_english, context, lesson, page in gaps:
        lines.append(
            f"  p.{page or '?':3} L{lesson or '?':2} [{context or '?':15}] "
            f"{bb_form!r:30} = {bb_english!r}"
        )

    # Sample matched entries for spot-check
    cur.execute("""
        SELECT bba.bb_skiri_form, bba.bb_english, bba.match_type,
               le.headword, le.normalized_form, bba.lesson_number, bba.page_number
        FROM blue_book_attestations bba
        JOIN lexical_entries le ON bba.entry_id = le.entry_id
        WHERE bba.match_type = 'exact_normalized'
        ORDER BY bba.lesson_number, bba.page_number
        LIMIT 50
    """)
    sample_matches = cur.fetchall()

    lines += [
        "",
        f"SAMPLE EXACT MATCHES (first 50)",
        "-" * 40,
    ]
    for bb_form, bb_eng, mtype, hw, norm, lesson, page in sample_matches:
        lines.append(
            f"  p.{page or '?':3} L{lesson or '?':2}  BB:{bb_form!r:25} → "
            f"Parks:{hw!r:25} ({norm})"
        )

    # Loose/prefix matches (may need review)
    cur.execute("""
        SELECT bba.bb_skiri_form, bba.bb_english, bba.match_type,
               le.headword, bba.lesson_number, bba.page_number
        FROM blue_book_attestations bba
        JOIN lexical_entries le ON bba.entry_id = le.entry_id
        WHERE bba.match_type IN ('loose', 'prefix')
        ORDER BY bba.match_type, bba.lesson_number
        LIMIT 100
    """)
    fuzzy_matches = cur.fetchall()

    lines += [
        "",
        f"LOOSE/PREFIX MATCHES — REVIEW RECOMMENDED ({len(fuzzy_matches)} shown)",
        "-" * 40,
    ]
    for bb_form, bb_eng, mtype, hw, lesson, page in fuzzy_matches:
        lines.append(
            f"  [{mtype:8}] p.{page or '?':3} L{lesson or '?':2}  "
            f"BB:{bb_form!r:25} → Parks:{hw!r}"
        )

    report_text = "\n".join(lines)
    output_path.write_text(report_text, encoding='utf-8')
    log.info(f"Report written to: {output_path}")
    # Safe print for Windows consoles that may not support all Unicode
    sys.stdout.buffer.write((report_text + "\n").encode('utf-8', errors='replace'))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 2.2 — Blue Book Cross-Verification"
    )
    parser.add_argument(
        "--text",
        default="pari pakuru/Blue_Book_Pari_Pakuru.txt",
        help="Path to Blue Book extracted text file",
    )
    parser.add_argument(
        "--db",
        default="skiri_pawnee.db",
        help="SQLite database path",
    )
    parser.add_argument(
        "--extracted",
        default="blue_book_extracted.json",
        help="Path to save/load extracted BB vocabulary JSON",
    )
    parser.add_argument(
        "--checkpoint",
        default="bb_extraction_checkpoint.json",
        help="Gemini extraction checkpoint file (for resume)",
    )
    parser.add_argument(
        "--report",
        default="reports/phase_2_2_blue_book.txt",
        help="Output report path",
    )
    parser.add_argument(
        "--model",
        default=GEMINI_MODEL,
        help=f"Gemini model name (default: {GEMINI_MODEL})",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only run Gemini extraction, don't import to DB",
    )
    parser.add_argument(
        "--match-only",
        action="store_true",
        help="Skip extraction, load from --extracted JSON and match",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database (report only)",
    )
    parser.add_argument(
        "--rerun-failed",
        action="store_true",
        help="Clear empty (failed) lesson entries from checkpoint so they get re-extracted",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Clear blue_book_attestations table and blue_book_attested flags before importing",
    )
    args = parser.parse_args()

    text_path = Path(args.text)
    db_path = Path(args.db)
    extracted_path = Path(args.extracted)
    checkpoint_path = Path(args.checkpoint)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Optional: clear failed checkpoint entries ---
    if args.rerun_failed and checkpoint_path.exists():
        ckpt = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        failed = [k for k, v in ckpt.items() if not v]
        for k in failed:
            del ckpt[k]
        checkpoint_path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding='utf-8')
        log.info(f"--rerun-failed: cleared {len(failed)} empty checkpoint entries: {failed}")

    # --- Stage 1: Extract ---
    if not args.match_only:
        if not text_path.exists():
            log.error(f"Blue Book text not found: {text_path}")
            sys.exit(1)

        log.info("=== Stage 1: Parsing Blue Book text ===")
        lessons = parse_blue_book_text(text_path)

        log.info("=== Stage 1: Gemini extraction ===")
        extracted = extract_with_gemini(lessons, checkpoint_path, args.model)

        # Save full extraction
        extracted_path.write_text(
            json.dumps(extracted, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        log.info(f"Saved {len(extracted)} entries to {extracted_path}")

        if args.extract_only:
            log.info("Extract-only mode: done.")
            return
    else:
        # Load from file
        if not extracted_path.exists():
            log.error(f"Extracted JSON not found: {extracted_path}")
            sys.exit(1)
        extracted = json.loads(extracted_path.read_text(encoding='utf-8'))
        log.info(f"Loaded {len(extracted)} entries from {extracted_path}")

    # --- Stage 2: Match + DB import ---
    if not db_path.exists():
        log.error(f"Database not found: {db_path}")
        sys.exit(1)

    log.info("=== Stage 2: Dictionary matching ===")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    create_attestation_table(conn)
    add_bb_attested_column(conn)

    # --- Optional: clear existing attestations for a fresh import ---
    if args.clear_db:
        conn.execute("DELETE FROM blue_book_attestations")
        conn.execute("UPDATE lexical_entries SET blue_book_attested = 0")
        conn.execute("DELETE FROM examples WHERE usage_context LIKE 'Blue Book%'")
        conn.commit()
        log.info("--clear-db: cleared blue_book_attestations, flags, and BB examples")

    index = build_dictionary_index(conn)

    stats = insert_attestations(conn, extracted, index, dry_run=args.dry_run)

    log.info("=== Stage 2: Generating report ===")
    generate_report(conn, stats, report_path, extracted)

    conn.close()
    log.info("Phase 2.2 complete.")


if __name__ == "__main__":
    main()
