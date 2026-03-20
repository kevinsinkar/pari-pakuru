#!/usr/bin/env python3
"""
Phase 1.2 — Query API for the Skiri Pawnee dictionary database.

Provides bidirectional lookup: English → Skiri and Skiri → English,
with full-text search, fuzzy matching, and filtering by grammatical class.

Usage as CLI:
    python query_api.py --db skiri_pawnee.db --english "bear"
    python query_api.py --db skiri_pawnee.db --skiri "kuruks"
    python query_api.py --db skiri_pawnee.db --search "to run"
    python query_api.py --db skiri_pawnee.db --english "stop" --class VT

Usage as library:
    from query_api import SkiriDictionary
    db = SkiriDictionary("skiri_pawnee.db")
    results = db.lookup_english("bear")
    results = db.lookup_skiri("kuruks")
    results = db.search("running")
"""

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# =============================================================================
# Data classes for structured results
# =============================================================================

@dataclass
class GlossResult:
    sense_number: int
    definition: str
    usage_notes: Optional[str] = None


@dataclass
class ParadigmResult:
    form_number: int
    skiri_form: str
    description: str = ""

    FORM_DESCRIPTIONS = {
        1: "1st person sg, indicative, perfective",
        2: "3rd person sg, indicative, perfective",
        3: "3rd person sg, indicative, imperfective",
        4: "3rd person sg, absolutive, subordinate perfective",
        5: "3rd person sg, indicative, perfective intentive",
    }

    def __post_init__(self):
        if not self.description:
            self.description = self.FORM_DESCRIPTIONS.get(self.form_number, "")


@dataclass
class ExampleResult:
    skiri_text: str
    english_translation: Optional[str] = None
    source: str = "parks_dictionary"


@dataclass
class CognateResult:
    language: str
    form: str


@dataclass
class EtymologyResult:
    raw_etymology: Optional[str] = None
    literal_translation: Optional[str] = None
    constituent_elements: Optional[list] = None


@dataclass
class CrossRefResult:
    to_english_term: str
    skiri_equivalents: Optional[list] = None


@dataclass
class DictionaryEntry:
    """A complete dictionary entry with all associated data."""
    entry_id: str
    headword: str
    normalized_form: Optional[str] = None
    phonetic_form: Optional[str] = None
    simplified_pronunciation: Optional[str] = None
    stem_preverb: Optional[str] = None
    grammatical_class: Optional[str] = None
    verb_class: Optional[str] = None
    page_number: Optional[int] = None
    glosses: List[GlossResult] = field(default_factory=list)
    paradigmatic_forms: List[ParadigmResult] = field(default_factory=list)
    examples: List[ExampleResult] = field(default_factory=list)
    etymology: Optional[EtymologyResult] = None
    cognates: List[CognateResult] = field(default_factory=list)
    cross_references: List[CrossRefResult] = field(default_factory=list)

    def summary(self) -> str:
        """One-line summary for display."""
        gloss_str = "; ".join(
            f"{g.sense_number}. {g.definition}" for g in self.glosses
        )
        parts = [self.headword]
        if self.normalized_form and self.normalized_form != self.headword:
            parts.append(f"({self.normalized_form})")
        if self.simplified_pronunciation:
            parts.append(f"[{self.simplified_pronunciation}]")
        if self.grammatical_class:
            parts.append(f"<{self.grammatical_class}>")
        parts.append(f"— {gloss_str}" if gloss_str else "— (no gloss)")
        return " ".join(parts)

    def full_display(self) -> str:
        """Multi-line formatted display."""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"  {self.headword}")
        if self.normalized_form:
            lines.append(f"  Normalized: {self.normalized_form}")
        if self.phonetic_form:
            lines.append(f"  Phonetic:   {self.phonetic_form}")
        if self.simplified_pronunciation:
            lines.append(f"  Pronounce:  {self.simplified_pronunciation}")
        info_parts = []
        if self.grammatical_class:
            info_parts.append(self.grammatical_class)
        if self.verb_class:
            info_parts.append(f"Class {self.verb_class}")
        if self.stem_preverb:
            info_parts.append(f"preverb: {self.stem_preverb}")
        if info_parts:
            lines.append(f"  Grammar:    {', '.join(info_parts)}")
        if self.page_number:
            lines.append(f"  Page:       {self.page_number}")

        if self.glosses:
            lines.append(f"\n  Definitions:")
            for g in self.glosses:
                note = f"  ({g.usage_notes})" if g.usage_notes else ""
                lines.append(f"    {g.sense_number}. {g.definition}{note}")

        if self.etymology:
            lines.append(f"\n  Etymology:")
            if self.etymology.raw_etymology:
                lines.append(f"    {self.etymology.raw_etymology}")
            if self.etymology.literal_translation:
                lines.append(f"    Lit: {self.etymology.literal_translation}")

        if self.paradigmatic_forms:
            lines.append(f"\n  Paradigmatic Forms:")
            for p in self.paradigmatic_forms:
                lines.append(f"    {p.form_number}. {p.skiri_form}")
                if p.description:
                    lines.append(f"       ({p.description})")

        if self.examples:
            lines.append(f"\n  Examples:")
            for ex in self.examples:
                lines.append(f"    {ex.skiri_text}")
                if ex.english_translation:
                    lines.append(f"      → {ex.english_translation}")

        if self.cognates:
            lines.append(f"\n  Cognates:")
            for c in self.cognates:
                lines.append(f"    {c.language} {c.form}")

        if self.cross_references:
            lines.append(f"\n  See also:")
            for xr in self.cross_references:
                equivs = ", ".join(xr.skiri_equivalents) if xr.skiri_equivalents else ""
                lines.append(f"    {xr.to_english_term}" + (f" ({equivs})" if equivs else ""))

        lines.append(f"{'='*60}")
        return "\n".join(lines)


# =============================================================================
# Dictionary class
# =============================================================================

class SkiriDictionary:
    """Query interface to the Skiri Pawnee dictionary database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ---- Internal helpers ----

    def _build_entry(self, entry_id: str) -> Optional[DictionaryEntry]:
        """Build a full DictionaryEntry from its entry_id."""
        cur = self.conn.cursor()

        cur.execute("SELECT * FROM lexical_entries WHERE entry_id = ?", (entry_id,))
        row = cur.fetchone()
        if not row:
            return None

        entry = DictionaryEntry(
            entry_id=row["entry_id"],
            headword=row["headword"],
            normalized_form=row["normalized_form"],
            phonetic_form=row["phonetic_form"],
            simplified_pronunciation=row["simplified_pronunciation"],
            stem_preverb=row["stem_preverb"],
            grammatical_class=row["grammatical_class"],
            verb_class=row["verb_class"],
            page_number=row["page_number"],
        )

        # Glosses
        cur.execute("SELECT * FROM glosses WHERE entry_id = ? ORDER BY sense_number", (entry_id,))
        entry.glosses = [
            GlossResult(r["sense_number"], r["definition"], r["usage_notes"])
            for r in cur.fetchall()
        ]

        # Paradigms
        cur.execute("SELECT * FROM paradigmatic_forms WHERE entry_id = ? ORDER BY form_number", (entry_id,))
        entry.paradigmatic_forms = [
            ParadigmResult(r["form_number"], r["skiri_form"])
            for r in cur.fetchall()
        ]

        # Examples
        cur.execute("SELECT * FROM examples WHERE entry_id = ? ORDER BY id", (entry_id,))
        entry.examples = [
            ExampleResult(r["skiri_text"], r["english_translation"], r["source"])
            for r in cur.fetchall()
        ]

        # Etymology
        cur.execute("SELECT * FROM etymology WHERE entry_id = ?", (entry_id,))
        etym_row = cur.fetchone()
        if etym_row:
            constituents = None
            if etym_row["constituent_elements"]:
                try:
                    constituents = json.loads(etym_row["constituent_elements"])
                except json.JSONDecodeError:
                    constituents = None
            entry.etymology = EtymologyResult(
                etym_row["raw_etymology"],
                etym_row["literal_translation"],
                constituents,
            )

        # Cognates
        cur.execute("SELECT * FROM cognates WHERE entry_id = ?", (entry_id,))
        entry.cognates = [
            CognateResult(r["language"], r["form"])
            for r in cur.fetchall()
        ]

        # Cross-references (via english_index)
        cur.execute("""
            SELECT DISTINCT cr.to_english_term, cr.skiri_equivalents
            FROM cross_references cr
            JOIN english_index ei ON cr.from_english_word = ei.english_word
            WHERE ei.entry_id = ?
        """, (entry_id,))
        for r in cur.fetchall():
            equivs = None
            if r["skiri_equivalents"]:
                try:
                    equivs = json.loads(r["skiri_equivalents"])
                except json.JSONDecodeError:
                    pass
            entry.cross_references.append(CrossRefResult(r["to_english_term"], equivs))

        return entry

    def _entry_ids_from_rows(self, rows) -> List[str]:
        """Deduplicate entry_ids while preserving order."""
        seen = set()
        ids = []
        for r in rows:
            eid = r["entry_id"]
            if eid and eid not in seen:
                seen.add(eid)
                ids.append(eid)
        return ids

    # ---- Public API ----

    def lookup_english(self, word: str, gram_class: str = None, verb_class: str = None) -> List[DictionaryEntry]:
        """
        Look up an English word → Skiri entries.
        Uses the english_index table (E2S layer).
        """
        cur = self.conn.cursor()
        query = "SELECT entry_id FROM english_index WHERE LOWER(english_word) = LOWER(?)"
        params = [word]

        if gram_class:
            query += " AND UPPER(grammatical_class) = UPPER(?)"
            params.append(gram_class)
        if verb_class:
            query += " AND verb_class = ?"
            params.append(verb_class)

        query += " ORDER BY subentry_number"
        cur.execute(query, params)

        entry_ids = self._entry_ids_from_rows(cur.fetchall())
        return [e for eid in entry_ids if (e := self._build_entry(eid))]

    def lookup_skiri(self, word: str) -> List[DictionaryEntry]:
        """
        Look up a Skiri word → full dictionary entries.
        Searches headword and normalized_form.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT entry_id FROM lexical_entries
            WHERE LOWER(headword) = LOWER(?)
               OR LOWER(normalized_form) = LOWER(?)
            ORDER BY page_number
        """, (word, word))

        entry_ids = self._entry_ids_from_rows(cur.fetchall())
        return [e for eid in entry_ids if (e := self._build_entry(eid))]

    def search(self, query: str, limit: int = 20) -> List[DictionaryEntry]:
        """
        Full-text search across glosses and examples.
        Uses FTS5 for relevance-ranked results.
        """
        cur = self.conn.cursor()
        entry_ids = []

        # Search glosses
        try:
            cur.execute("""
                SELECT entry_id, rank FROM fts_glosses
                WHERE fts_glosses MATCH ?
                ORDER BY rank LIMIT ?
            """, (query, limit))
            for r in cur.fetchall():
                if r["entry_id"] not in entry_ids:
                    entry_ids.append(r["entry_id"])
        except sqlite3.OperationalError:
            # Fallback to LIKE if FTS match syntax fails
            cur.execute("""
                SELECT entry_id FROM glosses
                WHERE LOWER(definition) LIKE ?
                ORDER BY entry_id LIMIT ?
            """, (f"%{query.lower()}%", limit))
            for r in cur.fetchall():
                if r["entry_id"] not in entry_ids:
                    entry_ids.append(r["entry_id"])

        # Also search english_index
        try:
            cur.execute("""
                SELECT entry_id FROM fts_english_index
                WHERE fts_english_index MATCH ?
                ORDER BY rank LIMIT ?
            """, (query, limit))
            for r in cur.fetchall():
                eid = r["entry_id"]
                if eid and eid not in entry_ids:
                    entry_ids.append(eid)
        except sqlite3.OperationalError:
            pass

        return [e for eid in entry_ids[:limit] if (e := self._build_entry(eid))]

    def search_fuzzy(self, query: str, limit: int = 20) -> List[DictionaryEntry]:
        """
        Fuzzy search for learner misspellings.
        Uses LIKE with wildcards on headword, normalized_form, and simplified_pronunciation.
        """
        cur = self.conn.cursor()
        pattern = f"%{query.lower()}%"

        cur.execute("""
            SELECT entry_id FROM lexical_entries
            WHERE LOWER(headword) LIKE ?
               OR LOWER(normalized_form) LIKE ?
               OR LOWER(simplified_pronunciation) LIKE ?
            ORDER BY
                CASE
                    WHEN LOWER(headword) = LOWER(?) THEN 0
                    WHEN LOWER(normalized_form) = LOWER(?) THEN 1
                    WHEN LOWER(headword) LIKE ? THEN 2
                    ELSE 3
                END
            LIMIT ?
        """, (pattern, pattern, pattern, query, query, f"{query.lower()}%", limit))

        entry_ids = self._entry_ids_from_rows(cur.fetchall())
        return [e for eid in entry_ids if (e := self._build_entry(eid))]

    def browse_by_class(self, gram_class: str, limit: int = 50) -> List[DictionaryEntry]:
        """List entries by grammatical class."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT entry_id FROM lexical_entries
            WHERE UPPER(grammatical_class) = UPPER(?)
            ORDER BY headword LIMIT ?
        """, (gram_class, limit))
        entry_ids = self._entry_ids_from_rows(cur.fetchall())
        return [e for eid in entry_ids if (e := self._build_entry(eid))]

    def stats(self) -> dict:
        """Return database statistics."""
        cur = self.conn.cursor()
        result = {}
        for table in ["lexical_entries", "glosses", "paradigmatic_forms", "examples",
                       "etymology", "cognates", "derived_stems", "english_index", "cross_references"]:
            cur.execute(f"SELECT COUNT(*) as c FROM {table}")
            result[table] = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(DISTINCT grammatical_class) as c FROM lexical_entries WHERE grammatical_class IS NOT NULL")
        result["distinct_gram_classes"] = cur.fetchone()["c"]

        cur.execute("SELECT grammatical_class, COUNT(*) as c FROM lexical_entries WHERE grammatical_class IS NOT NULL GROUP BY grammatical_class ORDER BY c DESC")
        result["class_distribution"] = {r["grammatical_class"]: r["c"] for r in cur.fetchall()}

        # Import metadata
        cur.execute("SELECT key, value FROM import_metadata")
        result["metadata"] = {r["key"]: r["value"] for r in cur.fetchall()}

        return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Query the Skiri Pawnee dictionary")
    parser.add_argument("--db", default="skiri_pawnee.db", help="Path to database")
    parser.add_argument("--english", "-e", help="Look up English word")
    parser.add_argument("--skiri", "-s", help="Look up Skiri word")
    parser.add_argument("--search", "-q", help="Full-text search")
    parser.add_argument("--fuzzy", "-f", help="Fuzzy search (Skiri)")
    parser.add_argument("--class", dest="gram_class", help="Filter by grammatical class")
    parser.add_argument("--browse", help="Browse by grammatical class")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--brief", action="store_true", help="Show one-line summaries only")
    parser.add_argument("--limit", type=int, default=20, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not any([args.english, args.skiri, args.search, args.fuzzy, args.browse, args.stats]):
        parser.print_help()
        sys.exit(1)

    with SkiriDictionary(args.db) as db:

        if args.stats:
            s = db.stats()
            if args.json:
                print(json.dumps(s, indent=2, ensure_ascii=False))
            else:
                print("\n=== Skiri Pawnee Dictionary Statistics ===\n")
                for table, count in s.items():
                    if table in ("class_distribution", "metadata"):
                        continue
                    print(f"  {table:<25} {count:>6}")
                print(f"\n  Grammatical class distribution:")
                for cls, count in s.get("class_distribution", {}).items():
                    print(f"    {cls:<10} {count:>5}")
                meta = s.get("metadata", {})
                if meta:
                    print(f"\n  Import: {meta.get('import_timestamp', '?')}")
                    print(f"  S2E entries: {meta.get('s2e_count', '?')}")
                    print(f"  E2S entries: {meta.get('e2s_entry_count', '?')} ({meta.get('e2s_subentry_count', '?')} subentries)")
            return

        results = []
        if args.english:
            results = db.lookup_english(args.english, gram_class=args.gram_class)
            label = f"English → Skiri: \"{args.english}\""
        elif args.skiri:
            results = db.lookup_skiri(args.skiri)
            label = f"Skiri → English: \"{args.skiri}\""
        elif args.search:
            results = db.search(args.search, limit=args.limit)
            label = f"Search: \"{args.search}\""
        elif args.fuzzy:
            results = db.search_fuzzy(args.fuzzy, limit=args.limit)
            label = f"Fuzzy search: \"{args.fuzzy}\""
        elif args.browse:
            results = db.browse_by_class(args.browse, limit=args.limit)
            label = f"Browse class: {args.browse}"

        if args.json:
            output = [asdict(e) for e in results]
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(f"\n{label}  ({len(results)} result{'s' if len(results) != 1 else ''})\n")
            for entry in results:
                if args.brief:
                    print(f"  {entry.summary()}")
                else:
                    print(entry.full_display())
                    print()


if __name__ == "__main__":
    main()
