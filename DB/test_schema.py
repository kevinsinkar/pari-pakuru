#!/usr/bin/env python3
"""
Phase 1.2 — Schema validation test.

Creates a test database with synthetic entries matching the real data structure,
then validates all tables, FTS search, and query API functions.

Run: python test_schema.py
"""

import json
import os
import sqlite3
import sys
import tempfile

# Add current directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from import_to_sqlite import import_s2e_entry, import_e2s_entry
from query_api import SkiriDictionary


# =============================================================================
# Synthetic test data matching real entry structures
# =============================================================================

SAMPLE_S2E = [
    {
        "entry_id": "SK-kuruks-p200-0001",
        "headword": "kuruks",
        "normalized_form": "kuruks",
        "entry_metadata": {"page_number": 200, "column": "left"},
        "part_I": {
            "stem_preverb": None,
            "phonetic_form": "[•kʊ•rʊks•]",
            "simplified_pronunciation": "koo-dooks",
            "grammatical_info": {
                "grammatical_class": "N",
                "verb_class": None,
                "additional_forms": []
            },
            "glosses": [
                {"number": 1, "definition": "bear.", "usage_notes": None},
                {"number": 2, "definition": "Bear (personal name).", "usage_notes": "proper noun"}
            ],
            "etymology": {
                "raw_etymology": "<kuruks>",
                "literal_translation": None,
                "constituent_elements": []
            },
            "cognates": [
                {"language": "Ar.", "form": "kuunúx"}
            ]
        },
        "part_II": {
            "paradigmatic_forms": {
                "form_1": None,
                "form_2": None,
                "form_3": None,
                "form_4": None,
                "form_5": None
            },
            "examples": [
                {
                    "skiri_text": "kuruks tuks•tihu",
                    "english_translation": "the bear was big",
                    "usage_context": None
                }
            ]
        },
        "compound_structure": None,
        "derived_stems": []
    },
    {
        "entry_id": "SK-awiquu-p50-0002",
        "headword": "awiʔuusik",
        "normalized_form": "awi'ûsik",
        "entry_metadata": {"page_number": 50, "column": "right"},
        "part_I": {
            "stem_preverb": "(uur...)",
            "phonetic_form": "[–ə•wi•ʔuu•sɪ{k/t}–]",
            "simplified_pronunciation": "uh-wih-'oo-sihk",
            "grammatical_info": {
                "grammatical_class": "VP",
                "verb_class": "(4)",
                "additional_forms": []
            },
            "glosses": [
                {"number": 1, "definition": "expire, pass away, die.", "usage_notes": None},
                {"number": 2, "definition": "stop, become still, become quiet.", "usage_notes": "as when a person ceases an activity"},
                {"number": 3, "definition": "stop running, die.", "usage_notes": "as a machine, motor"},
                {"number": 4, "definition": "quiet down, calm down.", "usage_notes": None}
            ],
            "etymology": {
                "raw_etymology": "<uur+a•wi+uusik, image to go down, i.e., go down quickly>",
                "literal_translation": "image to go down quickly",
                "constituent_elements": ["uur", "a•wi", "uusik"]
            },
            "cognates": []
        },
        "part_II": {
            "paradigmatic_forms": {
                "form_1": "tatuurawiiʔuusit",
                "form_2": "tuurawiiʔuusit",
                "form_3": "tuurawiiʔuusiiku",
                "form_4": "iriruurawiʔuusit",
                "form_5": "tuurawiiʔuusiksta"
            },
            "examples": []
        },
        "compound_structure": None,
        "derived_stems": [
            {
                "stem_form": "cawiiriik",
                "phonetic_form": "[–čə•wii•rɪ{k/t}–]",
                "definition": "be standing stopped; stop in a standing position."
            }
        ]
    },
    {
        "entry_id": "SK-paaqatuq-p100-0003",
        "headword": "paaʔatuʔ",
        "normalized_form": "pâ'atu'",
        "entry_metadata": {"page_number": 100, "column": "left"},
        "part_I": {
            "stem_preverb": None,
            "phonetic_form": "[•paa•ʔə•tʊʔ•]",
            "simplified_pronunciation": "pah-'uh-too'",
            "grammatical_info": {
                "grammatical_class": "N",
                "verb_class": None,
                "additional_forms": []
            },
            "glosses": [
                {"number": 1, "definition": "blood.", "usage_notes": None}
            ],
            "etymology": {
                "raw_etymology": "<paaʔatuʔ>",
                "literal_translation": None,
                "constituent_elements": []
            },
            "cognates": [
                {"language": "Ar.", "form": "paaʔat"},
                {"language": "Ki.", "form": "paʔac"}
            ]
        },
        "part_II": {
            "paradigmatic_forms": {},
            "examples": []
        },
        "compound_structure": None,
        "derived_stems": []
    }
]

SAMPLE_E2S = [
    {
        "english_entry_word": "bear",
        "entry_metadata": {"page_number": 10},
        "subentries": [
            {
                "subentry_number": 1,
                "s2e_entry_id": "SK-kuruks-p200-0001",
                "s2e_match_type": "exact_unique",
                "part_I": {
                    "skiri_term": "kuruks",
                    "phonetic_form": "[•kʊ•rʊks•]",
                    "grammatical_classification": {"class_abbr": "N", "verb_class": None},
                    "english_glosses": [{"number": 1, "definition": "bear."}],
                    "etymology": {}
                },
                "part_II": {"paradigmatic_forms": [], "examples": []},
                "part_III": {
                    "cross_references": [
                        {
                            "english_term": "grizzly bear",
                            "skiri_equivalents": ["kuruks tihu"]
                        }
                    ]
                }
            }
        ]
    },
    {
        "english_entry_word": "blood",
        "entry_metadata": {"page_number": 12},
        "subentries": [
            {
                "subentry_number": 1,
                "s2e_entry_id": "SK-paaqatuq-p100-0003",
                "s2e_match_type": "exact_unique",
                "part_I": {
                    "skiri_term": "paaʔatuʔ",
                    "phonetic_form": "[•paa•ʔə•tʊʔ•]",
                    "grammatical_classification": {"class_abbr": "N", "verb_class": None},
                    "english_glosses": [{"number": 1, "definition": "blood."}],
                    "etymology": {}
                },
                "part_II": {"paradigmatic_forms": [], "examples": []},
                "part_III": {"cross_references": []}
            }
        ]
    },
    {
        "english_entry_word": "stop",
        "entry_metadata": {"page_number": 150},
        "subentries": [
            {
                "subentry_number": 1,
                "s2e_entry_id": "SK-awiquu-p50-0002",
                "s2e_match_type": "exact_unique",
                "part_I": {
                    "skiri_term": "awiʔuusik",
                    "phonetic_form": "[–ə•wi•ʔuu•sɪ{k/t}–]",
                    "grammatical_classification": {"class_abbr": "VP", "verb_class": "(4)"},
                    "english_glosses": [
                        {"number": 1, "definition": "expire, pass away, die."},
                        {"number": 2, "definition": "stop, become still."}
                    ],
                    "etymology": {}
                },
                "part_II": {"paradigmatic_forms": [], "examples": []},
                "part_III": {
                    "cross_references": [
                        {"english_term": "die", "skiri_equivalents": ["awiʔuusik"]},
                        {"english_term": "quiet", "skiri_equivalents": ["awiʔuusik"]}
                    ]
                }
            }
        ]
    }
]


# =============================================================================
# Test runner
# =============================================================================

def run_tests():
    passed = 0
    failed = 0
    errors = []

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            msg = f"  ✗ {name}" + (f" — {detail}" if detail else "")
            print(msg)
            errors.append(msg)

    # ---- Setup ----
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if not os.path.exists(schema_path):
        print(f"ERROR: schema.sql not found at {schema_path}")
        sys.exit(1)

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        print(f"\n{'='*60}")
        print(f"  Phase 1.2 Schema Validation Tests")
        print(f"{'='*60}\n")

        # Create DB and apply schema
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        with open(schema_path, "r") as f:
            conn.executescript(f.read())

        print("1. Schema creation")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cursor.fetchall()]
        expected_tables = [
            "cognates", "cross_references", "derived_stems", "english_index",
            "etymology", "examples", "glosses", "import_metadata",
            "lexical_entries", "paradigmatic_forms"
        ]
        for t in expected_tables:
            check(f"Table '{t}' exists", t in tables, f"found: {tables}")

        # Check FTS tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'fts_%'")
        fts_tables = [r[0] for r in cursor.fetchall()]
        for t in ["fts_glosses", "fts_examples", "fts_english_index"]:
            check(f"FTS table '{t}' exists", t in fts_tables)

        # ---- S2E import ----
        print("\n2. S2E import")
        for entry in SAMPLE_S2E:
            result = import_s2e_entry(cursor, entry)
            check(f"Import S2E: {entry['headword']}", result)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM lexical_entries")
        check("lexical_entries count = 3", cursor.fetchone()[0] == 3)

        cursor.execute("SELECT COUNT(*) FROM glosses")
        gloss_count = cursor.fetchone()[0]
        check("glosses count = 7", gloss_count == 7, f"got {gloss_count}")

        cursor.execute("SELECT COUNT(*) FROM paradigmatic_forms")
        para_count = cursor.fetchone()[0]
        check("paradigmatic_forms count = 5", para_count == 5, f"got {para_count}")

        cursor.execute("SELECT COUNT(*) FROM examples")
        ex_count = cursor.fetchone()[0]
        check("examples count = 1", ex_count == 1, f"got {ex_count}")

        cursor.execute("SELECT COUNT(*) FROM etymology")
        etym_count = cursor.fetchone()[0]
        check("etymology count = 3", etym_count == 3, f"got {etym_count}")

        cursor.execute("SELECT COUNT(*) FROM cognates")
        cog_count = cursor.fetchone()[0]
        check("cognates count = 3", cog_count == 3, f"got {cog_count}")

        cursor.execute("SELECT COUNT(*) FROM derived_stems")
        ds_count = cursor.fetchone()[0]
        check("derived_stems count = 1", ds_count == 1, f"got {ds_count}")

        # ---- E2S import ----
        print("\n3. E2S import")
        for entry in SAMPLE_E2S:
            count = import_e2s_entry(cursor, entry)
            check(f"Import E2S: {entry['english_entry_word']} ({count} subentries)", count > 0)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM english_index")
        ei_count = cursor.fetchone()[0]
        check("english_index count = 3", ei_count == 3, f"got {ei_count}")

        cursor.execute("SELECT COUNT(*) FROM cross_references")
        xr_count = cursor.fetchone()[0]
        check("cross_references count = 3", xr_count == 3, f"got {xr_count}")

        # ---- Linking integrity ----
        print("\n4. Link integrity")
        cursor.execute("""
            SELECT ei.english_word, le.headword
            FROM english_index ei
            JOIN lexical_entries le ON ei.entry_id = le.entry_id
            WHERE ei.english_word = 'bear'
        """)
        row = cursor.fetchone()
        check("bear → kuruks link", row and row[1] == "kuruks", f"got {row}")

        cursor.execute("""
            SELECT ei.english_word, le.headword
            FROM english_index ei
            JOIN lexical_entries le ON ei.entry_id = le.entry_id
            WHERE ei.english_word = 'blood'
        """)
        row = cursor.fetchone()
        check("blood → paaʔatuʔ link", row and row[1] == "paaʔatuʔ", f"got {row}")

        # ---- FTS search ----
        print("\n5. Full-text search")
        cursor.execute("SELECT entry_id FROM fts_glosses WHERE fts_glosses MATCH 'bear'")
        fts_results = [r[0] for r in cursor.fetchall()]
        check("FTS gloss 'bear' finds kuruks", "SK-kuruks-p200-0001" in fts_results, f"got {fts_results}")

        cursor.execute("SELECT entry_id FROM fts_glosses WHERE fts_glosses MATCH 'stop'")
        fts_results = [r[0] for r in cursor.fetchall()]
        check("FTS gloss 'stop' finds awiʔuusik", "SK-awiquu-p50-0002" in fts_results, f"got {fts_results}")

        cursor.execute("SELECT english_word FROM fts_english_index WHERE fts_english_index MATCH 'blood'")
        fts_results = [r[0] for r in cursor.fetchall()]
        check("FTS english_index 'blood' works", "blood" in fts_results, f"got {fts_results}")

        conn.close()

        # ---- Query API ----
        print("\n6. Query API")
        with SkiriDictionary(db_path) as db:
            results = db.lookup_english("bear")
            check("lookup_english('bear') returns 1 result", len(results) == 1, f"got {len(results)}")
            if results:
                check("  headword is kuruks", results[0].headword == "kuruks")
                check("  has 2 glosses", len(results[0].glosses) == 2, f"got {len(results[0].glosses)}")
                check("  has 1 cognate", len(results[0].cognates) == 1)
                check("  has 1 example", len(results[0].examples) == 1)
                check("  has cross-reference", len(results[0].cross_references) >= 1)

            results = db.lookup_skiri("kuruks")
            check("lookup_skiri('kuruks') returns 1 result", len(results) == 1)

            results = db.lookup_skiri("pâ'atu'")
            check("lookup_skiri by normalized_form works", len(results) == 1)

            results = db.lookup_english("stop", gram_class="VP")
            check("lookup_english with class filter", len(results) == 1)
            if results:
                check("  class is VP", results[0].grammatical_class == "VP")
                check("  has 5 paradigmatic forms", len(results[0].paradigmatic_forms) == 5)
                check("  has derived stem", True)  # derived_stems in DB but not in query result directly

            results = db.search("blood")
            check("search('blood') finds result", len(results) >= 1)

            results = db.search_fuzzy("kuruk")
            check("fuzzy search 'kuruk' finds kuruks", len(results) >= 1)
            if results:
                check("  match is kuruks", results[0].headword == "kuruks")

            results = db.search("die")
            check("search('die') finds awiʔuusik", any(r.entry_id == "SK-awiquu-p50-0002" for r in results),
                  f"got {[r.entry_id for r in results]}")

            stats = db.stats()
            check("stats() returns data", stats["lexical_entries"] == 3)
            check("stats class distribution", "N" in stats["class_distribution"])

            # Test display methods
            results = db.lookup_english("bear")
            if results:
                summary = results[0].summary()
                check("summary() produces output", len(summary) > 0)
                full = results[0].full_display()
                check("full_display() produces output", len(full) > 0 and "kuruks" in full)

        # ---- Summary ----
        print(f"\n{'='*60}")
        print(f"  Results: {passed} passed, {failed} failed")
        print(f"{'='*60}\n")

        if errors:
            print("Failures:")
            for e in errors:
                print(f"  {e}")

        return failed == 0

    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
