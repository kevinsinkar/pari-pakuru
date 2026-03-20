#!/usr/bin/env python3
"""
Populate simplified_pronunciation and semantic_tags for BB-imported entries.
==========================================================================
The 93 entries added by import_bb_items.py have source='blue_book' but lack
phonetic_form and simplified_pronunciation. This script generates
simplified_pronunciation directly from the headword (practical orthography)
using the same vowel/consonant mappings as respell_and_normalize.py, then
assigns semantic tags based on the English gloss.

Usage:
    python scripts/populate_bb_pronunciation.py --db skiri_pawnee.db --dry-run
    python scripts/populate_bb_pronunciation.py --db skiri_pawnee.db
"""

import argparse
import logging
import re
import sqlite3
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pronunciation generation from headword (practical orthography)
# ---------------------------------------------------------------------------

# Same mappings as respell_and_normalize.py but applied to headword directly
# (no IPA available for BB imports).

# Accent stripping
ACCENT_MAP = {
    '\u00e1': 'a', '\u00ed': 'i', '\u00fa': 'u',
    '\u00e0': 'a', '\u00ec': 'i', '\u00f9': 'u',
}

# Order matters: longer sequences first
RESPELLING_RULES = [
    # Long vowels
    ('aa', 'ah'),
    ('ii', 'ee'),
    ('uu', 'oo'),
    # Consonant digraphs / special
    ('\u0294', "'"),  # glottal stop
    # Short vowels (after long vowels consumed)
    ('a', 'uh'),
    ('i', 'ih'),
    ('u', 'oo'),
    # Consonants
    ('r', 'd'),
    ('c', 'ts'),
]

# Consonants that pass through unchanged
PASSTHROUGH = set('ptkshwn')


def _strip_accents(s: str) -> str:
    return ''.join(ACCENT_MAP.get(ch, ch) for ch in s)


def generate_simplified_pronunciation(headword: str) -> str:
    """Convert Parks practical orthography headword to English respelling."""
    if not headword:
        return ""
    hw = _strip_accents(headword.lower().strip())

    # Build respelled syllables
    result = []
    i = 0
    while i < len(hw):
        matched = False
        # Try longest match first (2-char sequences)
        if i + 1 < len(hw):
            digraph = hw[i:i+2]
            for pattern, replacement in RESPELLING_RULES:
                if len(pattern) == 2 and digraph == pattern:
                    result.append(replacement)
                    i += 2
                    matched = True
                    break
        if not matched:
            ch = hw[i]
            for pattern, replacement in RESPELLING_RULES:
                if len(pattern) == 1 and ch == pattern:
                    result.append(replacement)
                    i += 1
                    matched = True
                    break
        if not matched:
            if ch in PASSTHROUGH:
                result.append(ch)
            else:
                result.append(ch)  # keep unknown chars as-is
            i += 1

    # Join and insert syllable breaks between consonant clusters and vowels
    raw = ''.join(result)

    # Simple syllabification: insert hyphens at V-C or C-V boundaries
    # Strategy: split into onset+nucleus groups
    # For simplicity, just return the raw respelling — it's readable enough
    # and matches the format of existing entries
    return raw


# ---------------------------------------------------------------------------
# Semantic tag assignment from English gloss
# ---------------------------------------------------------------------------

TAG_RULES = [
    # (tag, keywords that trigger it)
    ("kinship", {"mother", "father", "sister", "brother", "son", "daughter",
                 "uncle", "aunt", "grandmother", "grandfather", "wife",
                 "husband", "cousin", "nephew", "niece", "child", "family",
                 "boy", "girl", "man", "woman", "elder", "elderly", "baby",
                 "maiden", "adolescent", "youth", "old man", "old woman"}),
    ("animal", {"dog", "horse", "bird", "fish", "eagle", "hawk", "owl",
                "wolf", "bear", "deer", "elk", "buffalo", "beaver", "rabbit",
                "coyote", "bull", "cow", "frog", "turtle", "snake", "insect",
                "fly", "housefly", "spider", "bee", "louse", "cat", "chicken",
                "turkey", "duck", "goose", "mouse", "squirrel", "skunk",
                "otter", "fox", "crow", "magpie", "quail", "grouse"}),
    ("body", {"head", "face", "eye", "ear", "nose", "mouth", "tongue",
              "tooth", "hair", "arm", "leg", "hand", "foot", "breast",
              "heart", "bone", "skin", "blood", "body", "throat", "neck",
              "shoulder", "knee", "belly", "chest", "feather", "horn"}),
    ("food", {"food", "bread", "meat", "corn", "bean", "potato", "potatoes",
              "salt", "sugar", "fruit", "berry", "apple", "cooking",
              "flour", "lard", "feast", "meal", "eat"}),
    ("number", {"one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve", "hundred",
                "thousand", "first", "second"}),
    ("clothing", {"moccasin", "robe", "blanket", "shawl", "shirt", "dress",
                  "hat", "cap", "belt", "shoe", "legging", "cloth"}),
    ("housing", {"house", "lodge", "tipi", "village", "door", "room",
                 "chair", "table", "bed", "school", "church", "barn",
                 "camp", "fire", "stove"}),
    ("celestial", {"sun", "moon", "star", "sky", "cloud", "rain", "snow",
                   "wind", "thunder", "lightning", "night", "day", "month",
                   "winter", "summer", "spring", "weather", "cold", "hot"}),
    ("water", {"water", "river", "creek", "lake", "pond", "spring",
               "flood", "ice", "swim", "bridge"}),
    ("plant", {"tree", "grass", "flower", "leaf", "wood", "bush", "corn",
               "bean", "seed", "root", "bark", "branch", "willow", "cedar"}),
    ("tool", {"knife", "arrow", "bow", "gun", "pipe", "bucket", "rope",
              "bag", "basket", "shield", "hammer", "axe", "saw"}),
    ("land", {"land", "ground", "earth", "hill", "mountain", "valley",
              "prairie", "rock", "stone", "sand", "mud", "cave",
              "north", "south", "east", "west", "road"}),
    ("emotion", {"happy", "sad", "angry", "afraid", "love", "hate",
                 "jealous", "shame", "proud", "cry", "laugh"}),
    ("ceremony", {"dance", "ceremony", "sacred", "medicine", "bundle",
                  "pipe", "song", "drum", "prayer", "spirit", "chief",
                  "warrior", "doctor"}),
    ("social", {"people", "tribe", "band", "chief", "warrior", "friend",
                "enemy", "soldier", "sheriff", "law", "office", "council",
                "picture", "story"}),
    ("motion", {"go", "walk", "run", "come", "ride", "travel", "fly",
                "swim", "crawl", "jump"}),
    ("location", {"place", "village", "town", "city", "camp", "north",
                  "south", "east", "west", "middle", "road", "path"}),
    ("speech", {"voice", "speak", "talk", "say", "tell", "word",
                "language", "name", "song", "sing", "call", "shout",
                "hello", "yes", "no", "okay"}),
]


def assign_tags(definition: str) -> list:
    """Return list of semantic tags matching the definition."""
    if not definition:
        return []
    defn_lower = definition.lower()
    tags = []
    for tag, keywords in TAG_RULES:
        if any(re.search(r'\b' + re.escape(kw) + r'\b', defn_lower) for kw in keywords):
            tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Populate pronunciation + semantic tags for BB-imported entries"
    )
    parser.add_argument("--db", default="skiri_pawnee.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # Fetch BB entries missing simplified_pronunciation
    rows = conn.execute("""
        SELECT le.entry_id, le.headword,
               (SELECT definition FROM glosses g
                WHERE g.entry_id = le.entry_id
                ORDER BY sense_number LIMIT 1) as definition
        FROM lexical_entries le
        WHERE le.source = 'blue_book'
          AND le.simplified_pronunciation IS NULL
    """).fetchall()

    log.info("Found %d BB entries needing pronunciation", len(rows))

    pron_updates = []
    tag_inserts = []

    for r in rows:
        entry_id = r["entry_id"]
        headword = r["headword"]
        definition = r["definition"] or ""

        # Generate simplified pronunciation
        pron = generate_simplified_pronunciation(headword)
        pron_updates.append((pron, entry_id))

        # Assign semantic tags
        tags = assign_tags(definition)
        for tag in tags:
            tag_inserts.append((entry_id, tag))

    if args.dry_run:
        out = sys.stdout.buffer
        out.write(f"\n=== DRY RUN: {len(pron_updates)} pronunciations ===\n\n".encode("utf-8"))
        for pron, eid in pron_updates:
            hw = [r["headword"] for r in rows if r["entry_id"] == eid][0]
            out.write(f"  {hw:30s} -> {pron}\n".encode("utf-8"))
        out.write(f"\n=== {len(tag_inserts)} semantic tags ===\n\n".encode("utf-8"))
        for eid, tag in tag_inserts:
            out.write(f"  {eid:35s} -> {tag}\n".encode("utf-8"))
        tagged = len(set(eid for eid, _ in tag_inserts))
        untagged = len(pron_updates) - tagged
        out.write(f"\nTagged: {tagged}, Untagged: {untagged}\n".encode("utf-8"))
    else:
        cur = conn.cursor()
        cur.executemany(
            "UPDATE lexical_entries SET simplified_pronunciation = ? WHERE entry_id = ?",
            pron_updates,
        )
        # Remove existing tags for these entries (in case of re-run)
        bb_ids = [eid for _, eid in pron_updates]
        cur.executemany(
            "DELETE FROM semantic_tags WHERE entry_id = ?",
            [(eid,) for eid in bb_ids],
        )
        cur.executemany(
            "INSERT INTO semantic_tags (entry_id, tag) VALUES (?, ?)",
            tag_inserts,
        )
        conn.commit()
        log.info("Updated %d pronunciations, inserted %d semantic tags", len(pron_updates), len(tag_inserts))

    # Verify
    count = conn.execute(
        "SELECT COUNT(*) FROM lexical_entries WHERE source='blue_book' AND simplified_pronunciation IS NOT NULL"
    ).fetchone()[0]
    log.info("BB entries with pronunciation: %d", count)

    conn.close()


if __name__ == "__main__":
    main()
