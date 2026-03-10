"""
Phase 4.1 — Search logic for the Skiri Pawnee dictionary web interface.

Handles language detection, FTS query sanitization, Levenshtein fuzzy
matching for learner misspellings, and combined bidirectional search
with pagination and filtering.
"""

import re
import sqlite3
from typing import List, Optional, Tuple

from web.db import SkiriWebDictionary, EntrySummary


# Characters that indicate Skiri input
SKIRI_CHARS = set("ʔâîûčəɪʊ")
SKIRI_DIGRAPH_PATTERNS = re.compile(r"(aa|ii|uu|aw|ir|ut|uur)")


# ---------------------------------------------------------------------------
# Levenshtein distance (pure Python, no dependencies)
# ---------------------------------------------------------------------------

def _levenshtein(s: str, t: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s) < len(t):
        return _levenshtein(t, s)
    if not t:
        return len(s)
    prev = list(range(len(t) + 1))
    for i, sc in enumerate(s):
        curr = [i + 1]
        for j, tc in enumerate(t):
            cost = 0 if sc == tc else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def detect_language(query: str) -> str:
    """
    Auto-detect whether query is Skiri or English.
    Returns 'skiri', 'english', or 'both'.
    """
    # If it contains Pawnee-specific characters, it's Skiri
    if any(c in SKIRI_CHARS for c in query):
        return "skiri"

    # If it contains common Skiri digraph patterns and no spaces
    if " " not in query.strip() and SKIRI_DIGRAPH_PATTERNS.search(query):
        return "skiri"

    # If it's a single word with no spaces and contains only lowercase ASCII,
    # could be either — search both
    if " " not in query.strip() and query.isascii() and query.islower():
        return "both"

    # Multi-word or capitalized = likely English
    return "english"


def sanitize_fts_query(query: str) -> str:
    """
    Sanitize a query string for FTS5 MATCH syntax.
    Strips FTS operators that could cause syntax errors.
    """
    # Remove FTS5 special characters
    cleaned = query.replace('"', "").replace("*", "").replace("-", " ")
    cleaned = re.sub(r"\b(AND|OR|NOT|NEAR)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[(){}[\]]", "", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else query.strip()


def normalize_for_fuzzy(query: str) -> str:
    """
    Normalize a Skiri query for fuzzy matching:
    strip diacritics, normalize glottal stops, etc.
    """
    q = query.lower()
    # Learner might type apostrophe for glottal stop
    q = q.replace("'", "ʔ")
    # Circumflex to doubled vowels (learner might use either)
    q = q.replace("â", "aa").replace("î", "ii").replace("û", "uu")
    return q


def search_combined(
    db: SkiriWebDictionary,
    query: str,
    lang: str = "auto",
    gram_class: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[EntrySummary], int]:
    """
    Combined bidirectional search with pagination and filtering.

    Returns (results, total_count).
    """
    if not query or not query.strip():
        return [], 0

    query = query.strip()

    if lang == "auto":
        lang = detect_language(query)

    entry_ids = []  # ordered, deduplicated
    seen = set()

    def _add_ids(ids):
        for eid in ids:
            if eid and eid not in seen:
                seen.add(eid)
                entry_ids.append(eid)

    cur = db.conn.cursor()

    # --- Skiri direction ---
    if lang in ("skiri", "both"):
        # Exact match on headword / normalized_form
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE LOWER(headword) = LOWER(?) OR LOWER(normalized_form) = LOWER(?)",
            (query, query),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # Fuzzy / LIKE match
        fuzzy_q = normalize_for_fuzzy(query)
        pattern = f"%{fuzzy_q}%"
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE LOWER(headword) LIKE ? OR LOWER(normalized_form) LIKE ? "
            "OR LOWER(simplified_pronunciation) LIKE ? "
            "ORDER BY CASE "
            "  WHEN LOWER(headword) = LOWER(?) THEN 0 "
            "  WHEN LOWER(headword) LIKE ? THEN 1 "
            "  ELSE 2 END "
            "LIMIT 100",
            (pattern, pattern, pattern, query, f"{fuzzy_q}%"),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # Search paradigmatic forms (conjugated form lookup)
        cur.execute(
            "SELECT entry_id FROM paradigmatic_forms "
            "WHERE LOWER(skiri_form) LIKE ? LIMIT 50",
            (pattern,),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # Levenshtein fuzzy matching for learner misspellings
        # Only if we have few results so far (expensive scan)
        if len(entry_ids) < 5 and len(fuzzy_q) >= 3:
            max_dist = 1 if len(fuzzy_q) <= 5 else 2
            cur.execute(
                "SELECT entry_id, headword, normalized_form "
                "FROM lexical_entries "
                "WHERE LENGTH(headword) BETWEEN ? AND ? "
                "OR LENGTH(normalized_form) BETWEEN ? AND ?",
                (len(fuzzy_q) - max_dist, len(fuzzy_q) + max_dist,
                 len(fuzzy_q) - max_dist, len(fuzzy_q) + max_dist),
            )
            fuzzy_candidates = []
            for r in cur.fetchall():
                hw = (r["headword"] or "").lower()
                nf = (r["normalized_form"] or "").lower()
                d = min(_levenshtein(fuzzy_q, hw),
                        _levenshtein(fuzzy_q, nf) if nf else 999)
                if d <= max_dist:
                    fuzzy_candidates.append((d, r["entry_id"]))
            fuzzy_candidates.sort()
            _add_ids(eid for _, eid in fuzzy_candidates[:20])

    # --- English direction ---
    if lang in ("english", "both"):
        safe_q = sanitize_fts_query(query)

        # FTS on glosses
        if safe_q:
            try:
                cur.execute(
                    "SELECT entry_id FROM fts_glosses "
                    "WHERE fts_glosses MATCH ? ORDER BY rank LIMIT 100",
                    (safe_q,),
                )
                _add_ids(r["entry_id"] for r in cur.fetchall())
            except sqlite3.OperationalError:
                pass

            # Fallback LIKE on glosses
            if not entry_ids:
                cur.execute(
                    "SELECT entry_id FROM glosses "
                    "WHERE LOWER(definition) LIKE ? LIMIT 100",
                    (f"%{query.lower()}%",),
                )
                _add_ids(r["entry_id"] for r in cur.fetchall())

        # FTS on english_index -> join via skiri_term
        if safe_q:
            try:
                cur.execute(
                    "SELECT ei.skiri_term FROM fts_english_index fts "
                    "JOIN english_index ei ON fts.rowid = ei.id "
                    "WHERE fts_english_index MATCH ? ORDER BY rank LIMIT 100",
                    (safe_q,),
                )
                skiri_terms = [r["skiri_term"] for r in cur.fetchall() if r["skiri_term"]]
                if skiri_terms:
                    placeholders = ",".join("?" * len(skiri_terms))
                    cur.execute(
                        f"SELECT entry_id FROM lexical_entries "
                        f"WHERE headword IN ({placeholders})",
                        skiri_terms,
                    )
                    _add_ids(r["entry_id"] for r in cur.fetchall())
            except sqlite3.OperationalError:
                pass

    # --- Apply filters ---
    if gram_class or tag:
        filtered = []
        for eid in entry_ids:
            if gram_class:
                cur.execute(
                    "SELECT grammatical_class FROM lexical_entries WHERE entry_id = ?",
                    (eid,),
                )
                row = cur.fetchone()
                if not row or (row["grammatical_class"] or "").upper() != gram_class.upper():
                    continue
            if tag:
                cur.execute(
                    "SELECT 1 FROM semantic_tags WHERE entry_id = ? AND tag = ?",
                    (eid, tag),
                )
                if not cur.fetchone():
                    continue
            filtered.append(eid)
        entry_ids = filtered

    # --- Paginate ---
    total = len(entry_ids)
    start = (page - 1) * per_page
    page_ids = entry_ids[start : start + per_page]

    results = db.build_entry_summaries(page_ids)
    return results, total
