"""
Phase 4.1 — Search logic for the Skiri Pawnee dictionary web interface.

Handles language detection, FTS query sanitization, Levenshtein fuzzy
matching for learner misspellings, and combined bidirectional search
with pagination and filtering.
"""

import re
import sqlite3
import unicodedata
from typing import Dict, List, Optional, Tuple

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
    # could be either -- search both
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
    strip diacritics, normalize glottal stops, handle common
    learner misspellings (c/ts/ch equivalence, long vowel collapse).
    """
    q = query.lower()
    # Learner might type apostrophe for glottal stop
    q = q.replace("'", "ʔ").replace("\u2019", "ʔ").replace("\u02bc", "ʔ")
    # Circumflex to doubled vowels (learner might use either)
    q = q.replace("â", "aa").replace("î", "ii").replace("û", "uu")
    # Strip accent marks (e.g. á -> a)
    q = unicodedata.normalize("NFD", q)
    q = "".join(c for c in q if unicodedata.category(c) != "Mn" or c == "\u0294")
    # Re-add ʔ that may have been stripped
    q = q.replace("\u0294", "ʔ")
    return q


def normalize_for_comparison(form: str) -> str:
    """
    Aggressive normalization for fuzzy comparison:
    strips glottal stops, collapses long vowels, normalizes c/ts/ch.
    """
    q = normalize_for_fuzzy(form)
    # Strip glottal stops entirely
    q = q.replace("ʔ", "")
    # Normalize affricate variants: ts, ch -> c
    q = q.replace("ts", "c").replace("ch", "c")
    # Collapse long vowels
    q = q.replace("aa", "a").replace("ii", "i").replace("uu", "u")
    return q


def search_combined(
    db: SkiriWebDictionary,
    query: str,
    lang: str = "auto",
    gram_class: Optional[str] = None,
    tag: Optional[str] = None,
    verb_class: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[EntrySummary], int, str]:
    """
    Combined bidirectional search with pagination and filtering.

    Returns (results, total_count, detected_lang).
    """
    if not query or not query.strip():
        return [], 0, "auto"

    query = query.strip()

    if lang == "auto":
        lang = detect_language(query)

    entry_ids = []  # ordered, deduplicated
    seen = set()
    # Track which entries matched via examples (for display)
    example_matches: Dict[str, str] = {}

    def _add_ids(ids):
        for eid in ids:
            if eid and eid not in seen:
                seen.add(eid)
                entry_ids.append(eid)

    cur = db.conn.cursor()

    # --- Skiri direction ---
    if lang in ("skiri", "both"):
        # 1. Exact match on headword / normalized_form (highest priority)
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE LOWER(headword) = LOWER(?) OR LOWER(normalized_form) = LOWER(?)",
            (query, query),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # 2. Prefix match on headword
        fuzzy_q = normalize_for_fuzzy(query)
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE LOWER(headword) LIKE ? "
            "ORDER BY CASE "
            "  WHEN LOWER(headword) = LOWER(?) THEN 0 "
            "  WHEN LOWER(headword) LIKE ? THEN 1 "
            "  ELSE 2 END "
            "LIMIT 100",
            (f"{fuzzy_q}%", query, f"{fuzzy_q}%"),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # 3. Contains match on headword / normalized_form / pronunciation
        pattern = f"%{fuzzy_q}%"
        cur.execute(
            "SELECT entry_id FROM lexical_entries "
            "WHERE LOWER(headword) LIKE ? OR LOWER(normalized_form) LIKE ? "
            "OR LOWER(simplified_pronunciation) LIKE ? "
            "ORDER BY CASE "
            "  WHEN LOWER(headword) LIKE ? THEN 0 "
            "  ELSE 1 END "
            "LIMIT 100",
            (pattern, pattern, pattern, f"{fuzzy_q}%"),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # 4. Search paradigmatic forms (conjugated form lookup)
        cur.execute(
            "SELECT entry_id FROM paradigmatic_forms "
            "WHERE LOWER(skiri_form) LIKE ? LIMIT 50",
            (pattern,),
        )
        _add_ids(r["entry_id"] for r in cur.fetchall())

        # 5. Aggressive fuzzy: strip glottals, collapse vowels, normalize c/ts
        if len(entry_ids) < 5 and len(fuzzy_q) >= 3:
            comp_q = normalize_for_comparison(query)
            cur.execute(
                "SELECT entry_id, headword, normalized_form FROM lexical_entries"
            )
            fuzzy_candidates = []
            for r in cur.fetchall():
                hw = normalize_for_comparison(r["headword"] or "")
                nf = normalize_for_comparison(r["normalized_form"] or "")
                if comp_q in hw or comp_q in nf or hw.startswith(comp_q):
                    fuzzy_candidates.append((0 if hw == comp_q else 1, r["entry_id"]))
            fuzzy_candidates.sort()
            _add_ids(eid for _, eid in fuzzy_candidates[:20])

        # 6. Levenshtein fuzzy matching for learner misspellings
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

        # 1. FTS on glosses (primary)
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

        # 2. FTS on english_index -> join via skiri_term
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

        # 3. FTS on examples (weighted lower -- interesting but not primary)
        if safe_q:
            try:
                cur.execute(
                    "SELECT entry_id, english_translation FROM fts_examples "
                    "WHERE fts_examples MATCH ? ORDER BY rank LIMIT 50",
                    (safe_q,),
                )
                for r in cur.fetchall():
                    eid = r["entry_id"]
                    if eid and eid not in seen:
                        example_matches[eid] = r["english_translation"] or ""
                    _add_ids([eid])
            except sqlite3.OperationalError:
                pass

    # --- Re-rank: boost exact matches, BB attested, data completeness ---
    if entry_ids:
        # Fetch ranking data in bulk
        placeholders = ",".join("?" * len(entry_ids))
        cur.execute(
            f"SELECT entry_id, headword, blue_book_attested, "
            f"simplified_pronunciation, normalized_form "
            f"FROM lexical_entries WHERE entry_id IN ({placeholders})",
            entry_ids,
        )
        rank_data = {r["entry_id"]: dict(r) for r in cur.fetchall()}

        query_lower = query.lower()

        def _sort_key(eid):
            rd = rank_data.get(eid, {})
            hw = (rd.get("headword") or "").lower()
            # Tier 0: exact headword match (Skiri) or exact gloss word
            exact = 0 if hw == query_lower else 1
            # Tier 1: BB attested gets a small boost
            bb = 0 if rd.get("blue_book_attested") else 1
            # Tier 2: data completeness (has pronunciation + normalized form)
            completeness = 0
            if not rd.get("simplified_pronunciation"):
                completeness += 1
            if not rd.get("normalized_form"):
                completeness += 1
            # Tier 3: example-only matches rank last
            is_example = 1 if eid in example_matches and eid not in seen else 0
            # Preserve original insertion order as tiebreaker
            try:
                original_pos = entry_ids.index(eid)
            except ValueError:
                original_pos = 9999
            return (exact, is_example, bb, completeness, original_pos)

        entry_ids.sort(key=_sort_key)

    # --- Apply filters ---
    if gram_class or tag or verb_class:
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
            if verb_class:
                cur.execute(
                    "SELECT verb_class FROM lexical_entries WHERE entry_id = ?",
                    (eid,),
                )
                row = cur.fetchone()
                if not row or (row["verb_class"] or "") != verb_class:
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

    # Attach example match snippets to results
    for r in results:
        if r.entry_id in example_matches:
            r.example_snippet = example_matches[r.entry_id]

    return results, total, lang
