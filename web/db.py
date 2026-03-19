"""
Phase 4.1 — Web database layer for the Skiri Pawnee dictionary.

Extends DB/query_api.py SkiriDictionary with web-specific queries:
semantic tags, Blue Book attestations, verb paradigms, combined search,
browse helpers, and lightweight entry summaries.
"""

import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple

# Add parent directory so we can import from DB/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from DB.query_api import (
    SkiriDictionary,
    DictionaryEntry,
    GlossResult,
    ParadigmResult,
    ExampleResult,
    CognateResult,
    EtymologyResult,
    CrossRefResult,
)


@dataclass
class EntrySummary:
    """Lightweight entry for result lists (avoids full _build_entry overhead)."""
    entry_id: str
    headword: str
    normalized_form: Optional[str] = None
    simplified_pronunciation: Optional[str] = None
    grammatical_class: Optional[str] = None
    verb_class: Optional[str] = None
    first_gloss: Optional[str] = None
    blue_book_attested: bool = False
    tags: List[str] = field(default_factory=list)
    example_snippet: Optional[str] = None


@dataclass
class VerbParadigmForm:
    """A single conjugated verb form from the verb_paradigms table."""
    mode: str
    person_number: str
    skiri_form: str
    english_form: Optional[str] = None


class SkiriWebDictionary(SkiriDictionary):
    """Extended dictionary interface for the web application."""

    def __init__(self, db_path: str):
        # Open read-only
        self.db_path = db_path
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    # ------------------------------------------------------------------
    # Entry summaries (lightweight, for result lists)
    # ------------------------------------------------------------------

    def _build_entry_summary(self, entry_id: str) -> Optional[EntrySummary]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT entry_id, headword, normalized_form, simplified_pronunciation, "
            "grammatical_class, verb_class, blue_book_attested "
            "FROM lexical_entries WHERE entry_id = ?",
            (entry_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        # First gloss
        cur.execute(
            "SELECT definition FROM glosses WHERE entry_id = ? ORDER BY sense_number LIMIT 1",
            (entry_id,),
        )
        gloss_row = cur.fetchone()

        # Tags
        cur.execute(
            "SELECT tag FROM semantic_tags WHERE entry_id = ? ORDER BY tag",
            (entry_id,),
        )
        tags = [r["tag"] for r in cur.fetchall()]

        return EntrySummary(
            entry_id=row["entry_id"],
            headword=row["headword"],
            normalized_form=row["normalized_form"],
            simplified_pronunciation=row["simplified_pronunciation"],
            grammatical_class=row["grammatical_class"],
            verb_class=row["verb_class"],
            first_gloss=gloss_row["definition"] if gloss_row else None,
            blue_book_attested=bool(row["blue_book_attested"]),
            tags=tags,
        )

    def build_entry_summaries(self, entry_ids: List[str]) -> List[EntrySummary]:
        return [s for eid in entry_ids if (s := self._build_entry_summary(eid))]

    # ------------------------------------------------------------------
    # Semantic tags
    # ------------------------------------------------------------------

    def get_semantic_tags(self, entry_id: str) -> List[str]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT tag FROM semantic_tags WHERE entry_id = ? ORDER BY tag",
            (entry_id,),
        )
        return [r["tag"] for r in cur.fetchall()]

    def get_all_tags(self) -> List[Tuple[str, int]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT tag, COUNT(*) as c FROM semantic_tags "
            "GROUP BY tag ORDER BY c DESC"
        )
        return [(r["tag"], r["c"]) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Grammatical classes
    # ------------------------------------------------------------------

    def get_all_classes(self) -> List[Tuple[str, int]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT grammatical_class, COUNT(*) as c FROM lexical_entries "
            "WHERE grammatical_class IS NOT NULL "
            "GROUP BY grammatical_class ORDER BY c DESC"
        )
        return [(r["grammatical_class"], r["c"]) for r in cur.fetchall()]

    def get_all_verb_classes(self) -> List[Tuple[str, int]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT verb_class, COUNT(*) as c FROM lexical_entries "
            "WHERE verb_class IS NOT NULL AND verb_class != '' "
            "GROUP BY verb_class ORDER BY c DESC"
        )
        return [(r["verb_class"], r["c"]) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Blue Book attestation
    # ------------------------------------------------------------------

    def get_blue_book_info(self, entry_id: str) -> dict:
        cur = self.conn.cursor()
        # Flag on lexical_entries
        cur.execute(
            "SELECT blue_book_attested FROM lexical_entries WHERE entry_id = ?",
            (entry_id,),
        )
        row = cur.fetchone()
        attested = bool(row["blue_book_attested"]) if row else False

        # Detailed attestations
        cur.execute(
            "SELECT bb_skiri_form, bb_english, context_type, lesson_number, "
            "match_type, match_confidence "
            "FROM blue_book_attestations WHERE entry_id = ? ORDER BY lesson_number",
            (entry_id,),
        )
        attestations = [dict(r) for r in cur.fetchall()]

        return {"attested": attested, "attestations": attestations}

    # ------------------------------------------------------------------
    # Verb paradigms (full conjugation table from Appendix 1)
    # ------------------------------------------------------------------

    def get_verb_paradigm_table(self, entry_id: str) -> Optional[dict]:
        """Get full conjugation table for a verb, keyed by mode then person."""
        cur = self.conn.cursor()

        # Get the headword to match against verb_paradigms.dictionary_form
        cur.execute(
            "SELECT headword FROM lexical_entries WHERE entry_id = ?",
            (entry_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        headword = row["headword"]

        # Try matching by verb_heading (which is the English gloss like "to come")
        # First try matching dictionary_form to headword
        cur.execute(
            "SELECT DISTINCT verb_heading FROM verb_paradigms "
            "WHERE dictionary_form = ?",
            (headword,),
        )
        heading_row = cur.fetchone()

        if not heading_row:
            return None

        verb_heading = heading_row["verb_heading"]

        cur.execute(
            "SELECT mode, person_number, skiri_form, english_form "
            "FROM verb_paradigms WHERE verb_heading = ? "
            "ORDER BY mode, person_number",
            (verb_heading,),
        )
        rows = cur.fetchall()
        if not rows:
            return None

        # Build nested dict: {mode: {person: VerbParadigmForm}}
        table = {}
        modes = []
        persons = []
        for r in rows:
            mode = r["mode"]
            pn = r["person_number"]
            if mode not in table:
                table[mode] = {}
                modes.append(mode)
            if pn not in persons:
                persons.append(pn)
            table[mode][pn] = VerbParadigmForm(
                mode=mode,
                person_number=pn,
                skiri_form=r["skiri_form"],
                english_form=r["english_form"],
            )

        return {
            "verb_heading": verb_heading,
            "modes": modes,
            "persons": persons,
            "table": table,
        }

    # ------------------------------------------------------------------
    # Random entry (word of the day)
    # ------------------------------------------------------------------

    def get_random_entry(self) -> Optional[EntrySummary]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT entry_id FROM lexical_entries ORDER BY RANDOM() LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            return self._build_entry_summary(row["entry_id"])
        return None

    def get_word_of_day(self) -> Optional[EntrySummary]:
        """Deterministic daily selection from Blue Book attested entries."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE blue_book_attested = 1 ORDER BY entry_id"
        )
        bb_entries = [r["entry_id"] for r in cur.fetchall()]

        if not bb_entries:
            # Fallback to random entry if no BB entries
            return self.get_random_entry()

        today_str = date.today().isoformat()
        seed = int(hashlib.md5(today_str.encode()).hexdigest(), 16)
        idx = seed % len(bb_entries)

        return self._build_entry_summary(bb_entries[idx])

    # ------------------------------------------------------------------
    # Headword set (for example filtering)
    # ------------------------------------------------------------------

    def get_all_headwords(self) -> List[str]:
        """Return all headwords from lexical_entries (for example_filter)."""
        cur = self.conn.cursor()
        cur.execute("SELECT headword FROM lexical_entries WHERE headword IS NOT NULL")
        return [r["headword"] for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        cur = self.conn.cursor()
        result = {}
        for table in ["lexical_entries", "glosses", "examples", "semantic_tags",
                       "blue_book_attestations", "verb_paradigms"]:
            try:
                cur.execute(f"SELECT COUNT(*) as c FROM {table}")
                result[table] = cur.fetchone()["c"]
            except sqlite3.OperationalError:
                result[table] = 0
        cur.execute(
            "SELECT COUNT(DISTINCT tag) as c FROM semantic_tags"
        )
        result["distinct_tags"] = cur.fetchone()["c"]
        return result

    # ------------------------------------------------------------------
    # Enhanced entry building (adds tags + BB info)
    # ------------------------------------------------------------------

    def build_full_entry(self, entry_id: str) -> Optional[dict]:
        """Build a complete entry dict with all data for the detail view."""
        entry = self._build_entry(entry_id)
        if not entry:
            return None

        tags = self.get_semantic_tags(entry_id)
        bb_info = self.get_blue_book_info(entry_id)
        paradigm_table = self.get_verb_paradigm_table(entry_id)

        # Get derived stems
        cur = self.conn.cursor()
        cur.execute(
            "SELECT stem_form, phonetic_form, definition "
            "FROM derived_stems WHERE entry_id = ? ORDER BY id",
            (entry_id,),
        )
        derived_stems = [dict(r) for r in cur.fetchall()]

        return {
            "entry": entry,
            "tags": tags,
            "bb_info": bb_info,
            "paradigm_table": paradigm_table,
            "derived_stems": derived_stems,
        }
