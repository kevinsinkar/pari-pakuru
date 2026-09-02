#!/usr/bin/env python3
"""
Phase 5.1 follow-up — re-extract Lessons 3–4 vocabulary (Blue Book pp. 39–49)
==============================================================================

The Phase 2.2 extraction nearly missed these two lessons (7 + 4 items) because
the source text's two-column vocab layout reflowed into separated blocks of
forms and glosses. This script re-extracts JUST those lesson spans with
Gemini, pairs forms with glosses, matches items to dictionary entries using
the Phase 2.2 matching machinery (blue_book_verify), and inserts NEW items
into blue_book_attestations (existing rows are never modified).

Usage:
  python scripts/extract_lesson_gaps.py             # dry-run
  python scripts/extract_lesson_gaps.py --apply
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blue_book_verify import (          # Phase 2.2 machinery, reused
    build_dictionary_index,
    match_entry,
)

ROOT = Path(__file__).resolve().parent.parent
BB_TEXT = ROOT / 'pari pakuru' / 'Blue_Book_Pari_Pakuru.txt'
DB_PATH = ROOT / 'skiri_pawnee.db'
GEMINI_MODEL = 'gemini-2.5-flash'


def out(s):
    sys.stdout.buffer.write((str(s) + '\n').encode('utf-8', errors='replace'))
    sys.stdout.buffer.flush()


def call_gemini_json(client, prompt):
    """Direct JSON-mode call with parse retries.

    Phase 2.2's _call_gemini carries its own system instruction (tuned for
    full-book vocabulary extraction) which distorts this focused task and,
    at temperature 0, reproduced the same malformed JSON on every retry.
    Here: no system instruction, and the temperature is nudged up on parse
    failures so retries can actually produce different output.
    """
    import time
    from google.genai import types
    for attempt, temp in enumerate((0.0, 0.3, 0.6), 1):
        try:
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=temp,
                    max_output_tokens=8192,
                    response_mime_type='application/json',
                ),
            )
            text = re.sub(r'^```json\s*|\s*```$', '', resp.text.strip())
            return json.loads(text)
        except json.JSONDecodeError as e:
            out(f'  JSON parse failed (attempt {attempt}, temp {temp}): {e}')
            time.sleep(2)
        except Exception as e:
            out(f'  Gemini error (attempt {attempt}): {type(e).__name__}: {e}')
            time.sleep(5)
    return None


PROMPT = """You are extracting vocabulary from a 1979 Pawnee language textbook
(Skiri Pawnee, practical orthography). Below is the raw text of {label}.

The vocabulary sections (BASIC WORDS, ADDITIONAL WORDS) were printed in two
columns — Pawnee form on the left, English gloss on the right — but the text
extraction reflowed them, so you may see a block of Pawnee forms followed by a
block of English glosses IN THE SAME ORDER. Pair them up by position.

Rules:
- Extract ONLY vocabulary items that are actually printed in the text.
  Do not invent, complete, or normalize anything.
- Keep the Pawnee spelling EXACTLY as printed (including •, ', spaces).
- SKIP morpheme-breakdown lines (like "hak +", "wa +", "+ rar +") — those
  are analysis lines, not vocabulary.
- SKIP dialogue sentences and grammar-example sentences.
- context_type is "BASIC_WORDS" for items under BASIC WORDS,
  "ADDITIONAL_WORDS" for items under ADDITIONAL WORDS or later word lists.

Return a JSON array, no other text:
[{{"skiri_form": "...", "english_translation": "...",
   "context_type": "BASIC_WORDS", "lesson_number": {lesson}}}]

TEXT:
{text}
"""


# Source-verified gloss corrections. Gemini's column pairing in the Lesson 3
# BASIC WORDS block shifted by two: it skipped the morpheme-analysis FORMS
# ('hak +', 'wa +') but not their GLOSSES. The correct pairing below is read
# directly from Blue_Book_Pari_Pakuru.txt p. 39 (forms in order: ti hak•tsa,
# hak+, ti wa•ku, wa+, ti rihu', ti kata•rihu', ti keats, kaki keats,
# kaki rihu'; glosses in the same order incl. the morpheme lines').
CORRECTIONS = {
    (3, "ti kata•rihu'"): "it's broad",
    (3, 'ti keats'): "it's long",
    (3, 'kaki keats'): "it's short",
    (3, "kaki rihu'"): "it's small",
}


def get_lesson_span(text, start_marker, end_marker):
    i = text.find(start_marker)
    j = text.find(end_marker)
    return text[i:j] if 0 <= i < j else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        out('GEMINI_API_KEY not set'); sys.exit(1)
    from google import genai
    client = genai.Client(api_key=api_key)

    text = BB_TEXT.read_text(encoding='utf-8')
    spans = [
        (3, get_lesson_span(text, 'LESSON 3', 'LESSON 4')),
        (4, get_lesson_span(text, 'LESSON 4', 'LESSON 5')),
    ]

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    index = build_dictionary_index(con)

    # existing items so we never duplicate
    cur.execute("SELECT lesson_number, lower(trim(bb_skiri_form)) "
                "FROM blue_book_attestations WHERE lesson_number IN (3,4)")
    existing = {(r[0], r[1]) for r in cur.fetchall()}

    all_new = []
    for lesson, span in spans:
        if not span:
            out(f'lesson {lesson}: span not found'); continue
        prompt = PROMPT.format(label=f'LESSON {lesson}', lesson=lesson,
                               text=span[:12000])
        result = call_gemini_json(client, prompt)
        if isinstance(result, dict):
            items = result.get('items') or result.get('vocabulary') or []
        else:
            items = result or []
        out(f'lesson {lesson}: Gemini returned {len(items)} items')
        for it in items:
            form = (it.get('skiri_form') or '').strip()
            gloss = (it.get('english_translation') or '').strip()
            ctx = it.get('context_type') or 'ADDITIONAL_WORDS'
            if ctx not in ('BASIC_WORDS', 'ADDITIONAL_WORDS', 'PHRASE'):
                ctx = 'ADDITIONAL_WORDS'
            if not form or not gloss:
                continue
            # analysis-line guard (belt and braces)
            if form.endswith('+') or form.startswith('+'):
                continue
            key = (lesson, form.lower())
            if key in existing:
                out(f'  skip (exists): {form}')
                continue
            existing.add(key)          # in-batch dedupe too
            corrected = CORRECTIONS.get((lesson, form))
            if corrected and corrected != gloss:
                out(f'  CORRECTED gloss for {form!r}: {gloss!r} -> '
                    f'{corrected!r} (source-verified, see CORRECTIONS)')
                gloss = corrected
            matches, mtype = match_entry(form, index)
            entry_id = matches[0] if matches else None
            # the 'prefix' tier is too weak for learner-facing links —
            # it matched 'eight' to ta 'be lying'. An honest "not in Parks
            # dictionary" beats a wrong link; most of these are genuinely
            # BB-only compounds and phrases.
            if entry_id and mtype == 'prefix':
                entry_id, mtype = None, None
            if isinstance(entry_id, dict):
                entry_id = entry_id.get('entry_id')
            all_new.append((form, gloss, ctx, lesson, entry_id, mtype))
            linked = f'-> {entry_id} ({mtype})' if entry_id else '(no link)'
            out(f'  NEW [{ctx}] {form!r} = {gloss!r} {linked}')

    out(f'\ntotal new items: {len(all_new)} '
        f'(linked: {sum(1 for x in all_new if x[4])})')

    if args.apply and all_new:
        for form, gloss, ctx, lesson, entry_id, mtype in all_new:
            cur.execute(
                "INSERT INTO blue_book_attestations "
                "(bb_skiri_form, bb_english, context_type, lesson_number, "
                " entry_id, match_type, notes) VALUES (?,?,?,?,?,?,?)",
                (form, gloss, ctx, lesson, entry_id,
                 mtype if entry_id else None,
                 'gap re-extraction 2026-09-01 (extract_lesson_gaps.py)'))
        con.commit()
        out(f'[DB] inserted {len(all_new)} attestation rows')
    elif not args.apply:
        out('DRY-RUN: nothing written. Re-run with --apply.')
    con.close()


if __name__ == '__main__':
    main()
