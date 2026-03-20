#!/usr/bin/env python3
"""
Extract function words from Blue Book phrase gaps via Gemini API.

Reads the 196 phrase-category items from bb_gap_triage, sends them
to Gemini in batches, and collects standalone function words
(particles, demonstratives, pronouns, conjunctions, etc.).

Results are written to:
  - DB table: bb_function_words (word, class, meaning, source_phrase, lesson)
  - Report: reports/bb_function_words.txt

Usage:
    python scripts/extract_function_words.py                # full run
    python scripts/extract_function_words.py --dry-run      # show phrases, no API calls
    python scripts/extract_function_words.py --report-only  # just print existing results

Requires: GEMINI_API_KEY environment variable
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DB_PATH = REPO_ROOT / "skiri_pawnee.db"
REPORT_PATH = REPO_ROOT / "reports" / "bb_function_words.txt"
CHECKPOINT_PATH = REPO_ROOT / "extracted_data" / "bb_function_words_checkpoint.json"

BATCH_SIZE = 40  # phrases per Gemini call

SYSTEM_PROMPT = """You are a Skiri Pawnee linguistic analyst working with data from the Parks Dictionary and the Blue Book (Pari Pakuru').

You will be given a list of Pawnee phrases from the Blue Book that didn't match standalone dictionary entries. For each phrase, identify any STANDALONE FUNCTION WORDS — particles, demonstratives, pronouns, conjunctions, interjections, question words, or discourse markers.

Rules:
- Only extract words that function as standalone particles or grammatical words — NOT prefixes, verb morphology, or incorporated nouns.
- Common Pawnee function words include: nawa (now/and), ti/tiʔ (here/this), ka (quotative), kirike/kirikuʔ (what?), kici (also), re/reʔ (and/then), haʔa (yes), katka (no), piira (very), tii (this), tiku (that).
- If a phrase contains no identifiable standalone function words, return an empty array for that phrase.
- Normalize orthography: ts→c, '→ʔ where appropriate.
- For each function word found, provide: the word form, grammatical class (CONJ, DEM, PRON, INTERJ, QUAN, ADV, PART), and English meaning.

Respond ONLY with a JSON array, no preamble, no markdown fences. Each element:
{"phrase": "the original phrase", "function_words": [{"word": "nawa", "class": "CONJ", "meaning": "now, and"}, ...]}

If a phrase has no function words, include it with an empty array:
{"phrase": "the phrase", "function_words": []}
"""


def get_phrases(db_path: str) -> list:
    """Get all phrase-category items from bb_gap_triage."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("""
        SELECT bb_skiri_form AS bb_form, bb_english AS english_gloss, lesson_number AS lesson
        FROM bb_gap_triage
        WHERE category = 'phrase'
        ORDER BY lesson_number, bb_skiri_form
    """)
    phrases = [dict(r) for r in cur]
    conn.close()
    return phrases


def call_gemini(phrases_batch: list, api_key: str) -> list:
    """Send a batch of phrases to Gemini and get function word extraction."""
    import urllib.request
    import urllib.error

    # Format the input
    lines = []
    for i, p in enumerate(phrases_batch, 1):
        lines.append(f"{i}. Pawnee: {p['bb_form']}  |  English: {p['english_gloss']}  |  Lesson: {p['lesson']}")
    
    user_prompt = f"Extract standalone function words from these {len(phrases_batch)} Pawnee phrases:\n\n" + "\n".join(lines)

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 16384,
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP error {e.code}: {e.read().decode()[:200]}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

    # Extract text from response
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        print(f"  Unexpected response structure: {json.dumps(result)[:200]}")
        return []

    # Parse JSON from response
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        else:
            print(f"  Response is not a list: {type(parsed)}")
            return []
    except json.JSONDecodeError as e:
        # Try to recover partial JSON by finding the last complete object
        # Look for the last "}," or "}\n]" and truncate there
        last_complete = text.rfind('},')
        if last_complete > 0:
            truncated = text[:last_complete + 1] + ']'
            try:
                parsed = json.loads(truncated)
                if isinstance(parsed, list):
                    print(f"  Recovered {len(parsed)} items from truncated JSON")
                    return parsed
            except json.JSONDecodeError:
                pass
        # Try finding last complete object ending with }]
        last_bracket = text.rfind('}')
        if last_bracket > 0:
            truncated = text[:last_bracket + 1] + ']'
            try:
                parsed = json.loads(truncated)
                if isinstance(parsed, list):
                    print(f"  Recovered {len(parsed)} items from truncated JSON (v2)")
                    return parsed
            except json.JSONDecodeError:
                pass
        print(f"  JSON parse error: {e}")
        print(f"  Raw text: {text[:300]}")
        return []


def load_checkpoint() -> dict:
    """Load checkpoint of already-processed batches."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"processed_batches": [], "results": []}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def populate_db(results: list, db_path: str):
    """Write extracted function words to DB table."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bb_function_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            grammatical_class TEXT,
            meaning TEXT,
            source_phrase TEXT,
            lesson TEXT,
            normalized_word TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("DELETE FROM bb_function_words")  # fresh import

    inserted = 0
    for item in results:
        phrase = item.get("phrase", "")
        fws = item.get("function_words", [])
        lesson = item.get("lesson", "")
        for fw in fws:
            word = fw.get("word", "").strip()
            if not word:
                continue
            # Normalize
            normalized = word.lower().replace("ts", "c").replace("'", "ʔ").replace("\u2019", "ʔ")
            cur.execute("""
                INSERT INTO bb_function_words (word, grammatical_class, meaning, source_phrase, lesson, normalized_word)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (word, fw.get("class", ""), fw.get("meaning", ""), phrase, lesson, normalized))
            inserted += 1

    conn.commit()
    conn.close()
    return inserted


def generate_report(results: list, db_path: str):
    """Generate a text report of findings."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Deduplicate function words
    word_info = {}
    for item in results:
        for fw in item.get("function_words", []):
            word = fw.get("word", "").lower().replace("ts", "c").replace("'", "ʔ")
            if word and word not in word_info:
                word_info[word] = {
                    "class": fw.get("class", "?"),
                    "meaning": fw.get("meaning", "?"),
                    "count": 0,
                    "phrases": [],
                }
            if word:
                word_info[word]["count"] += 1
                if len(word_info[word]["phrases"]) < 3:
                    word_info[word]["phrases"].append(item.get("phrase", ""))

    lines = []
    lines.append("=" * 70)
    lines.append("BLUE BOOK FUNCTION WORD EXTRACTION")
    lines.append("=" * 70)
    lines.append(f"Phrases analyzed: {len(results)}")
    lines.append(f"Unique function words found: {len(word_info)}")
    lines.append(f"Total occurrences: {sum(v['count'] for v in word_info.values())}")
    lines.append("")
    lines.append(f"{'Word':<20} {'Class':<8} {'Count':>5}  {'Meaning'}")
    lines.append("-" * 70)

    for word, info in sorted(word_info.items(), key=lambda x: -x[1]["count"]):
        lines.append(f"  {word:<18} {info['class']:<8} {info['count']:>5}  {info['meaning']}")
        for p in info["phrases"][:2]:
            lines.append(f"    ex: {p}")

    report_text = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    sys.stdout.buffer.write(report_text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(f"\n\nReport saved to {REPORT_PATH}\n".encode("utf-8"))
    return word_info


def main():
    parser = argparse.ArgumentParser(description="Extract function words from BB phrase gaps via Gemini")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Show phrases without calling Gemini")
    parser.add_argument("--report-only", action="store_true", help="Generate report from existing checkpoint")
    parser.add_argument("--clear", action="store_true", help="Clear checkpoint and start fresh")
    args = parser.parse_args()

    db_path = args.db

    if args.clear and CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        print("Checkpoint cleared.")

    if args.report_only:
        checkpoint = load_checkpoint()
        if not checkpoint["results"]:
            print("No results in checkpoint. Run extraction first.")
            return
        generate_report(checkpoint["results"], db_path)
        return

    # Get phrases
    phrases = get_phrases(db_path)
    print(f"Found {len(phrases)} phrases to analyze")

    if args.dry_run:
        for i, p in enumerate(phrases, 1):
            print(f"  {i:>3}. L{p['lesson']:<3} {p['bb_form']:<35} {p['english_gloss'][:45]}")
        print(f"\n{len(phrases)} phrases would be sent to Gemini in {(len(phrases) + BATCH_SIZE - 1) // BATCH_SIZE} batches of {BATCH_SIZE}")
        return

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    # Load checkpoint
    checkpoint = load_checkpoint()
    processed_set = set(checkpoint["processed_batches"])

    # Process in batches
    batches = [phrases[i:i+BATCH_SIZE] for i in range(0, len(phrases), BATCH_SIZE)]
    print(f"Processing {len(batches)} batches of up to {BATCH_SIZE} phrases each")
    print(f"Already processed: {len(processed_set)} batches")

    for batch_idx, batch in enumerate(batches):
        batch_key = f"batch_{batch_idx}"
        if batch_key in processed_set:
            print(f"  Batch {batch_idx + 1}/{len(batches)}: already processed, skipping")
            continue

        print(f"  Batch {batch_idx + 1}/{len(batches)}: sending {len(batch)} phrases to Gemini...")
        results = call_gemini(batch, api_key)

        if results:
            # Merge lesson info back into results
            for r in results:
                for p in batch:
                    if p['bb_form'] in r.get('phrase', ''):
                        r['lesson'] = p['lesson']
                        break

            checkpoint["results"].extend(results)
            checkpoint["processed_batches"].append(batch_key)
            processed_set.add(batch_key)
            save_checkpoint(checkpoint)
            print(f"    Got {sum(len(r.get('function_words', [])) for r in results)} function words from {len(results)} phrases")
        else:
            print(f"    WARNING: Empty result for batch {batch_idx + 1}")

        # Rate limit
        if batch_idx < len(batches) - 1:
            time.sleep(2)

    # Populate DB
    print(f"\nPopulating bb_function_words table...")
    inserted = populate_db(checkpoint["results"], db_path)
    print(f"Inserted {inserted} function word occurrences")

    # Generate report
    print()
    generate_report(checkpoint["results"], db_path)


if __name__ == "__main__":
    main()
