"""
Search Result Ranking for Pari Pakuru Web Dictionary
=====================================================

Drop-in relevance scoring for search results. Call rank_results() after
collecting candidates from FTS and english_index queries.

Five scoring signals, weighted by how strongly they predict "this is what
the learner meant":

  1. E2S exact match (100pts) — "dog" == "dog" in english_index
  2. Gloss position (up to 80pts) — "dog." as entire definition >> "...as a dog"
  3. Blue Book attested (20pts) — classroom-relevant entries
  4. Data completeness (up to 18pts) — entries with examples/forms are more useful
  5. Noun boost (3pts) — slight preference for nouns on noun-like queries

Integration:
    # In web/search.py or web/app.py, after collecting raw results:
    from search_ranking import rank_results
    ranked = rank_results(conn, raw_results, query)

The E2S join uses skiri_term → headword because english_index.entry_id
is NULL for all 8,067 rows. If that gets fixed upstream, the JOIN
can simplify.
"""

import re
import sqlite3
from typing import List, Dict, Any, Optional


def score_entry(
    query: str,
    ei_words: List[str],
    glosses: List[tuple],  # [(sense_number, definition), ...]
    bb_attested: bool,
    example_count: int,
    form_count: int,
    grammatical_class: str,
) -> float:
    """
    Compute a relevance score for a single entry against a query.

    Higher score = more relevant. Typical ranges:
      - Exact match: 150–200
      - Strong match: 80–150
      - Incidental mention: 20–50
      - Barely related: 0–20
    """
    score = 0.0
    q = query.lower().strip()

    # ── Signal 1: English-to-Skiri index match ──────────────────────
    # The english_index is the E2S dictionary. An exact match here
    # means Parks explicitly listed this as the translation.
    ei_score = 0.0
    for ew in ei_words:
        ew_lower = ew.lower().strip()
        ew_words = ew_lower.split()

        if ew_lower == q:
            ei_score = max(ei_score, 100)   # exact: "dog" == "dog"
        elif ew_lower.startswith(q + ",") or ew_lower.startswith(q + " "):
            # Query is the head word of a compound entry
            # "dog, female" or "go inside" — stronger if fewer total words
            if len(ew_words) <= 2:
                ei_score = max(ei_score, 70)   # "dog, female" — strong
            else:
                ei_score = max(ei_score, 50)   # "go around in circles" — weaker
        elif q in ew_words:
            # Query is a non-initial word: "prairie dog", "hot dog"
            ei_score = max(ei_score, 30)
        elif q in ew_lower:
            ei_score = max(ei_score, 10)       # substring: "dogwood"

    score += ei_score

    # ── Signal 2: Gloss position ────────────────────────────────────
    # Where the query lands in the S2E definition matters enormously.
    # "dog." (entire definition) vs. "...as when shooing a dog away..."
    for sense_num, definition in glosses:
        d = definition.lower().strip()

        if d.rstrip(".") == q:
            score += 80           # definition IS the query word
        elif d.startswith(q + ".") or d.startswith(q + ",") or d.startswith(q + ";"):
            score += 60           # definition starts with query
        elif re.search(r"\b" + re.escape(q) + r"\b", d[:40]):
            score += 35           # whole word in first 40 chars
        elif re.search(r"\b" + re.escape(q) + r"\b", d):
            score += 15           # whole word anywhere
        elif q in d:
            score += 5            # substring only

        # Earlier sense = more relevant
        if sense_num == 1:
            score += 8
        elif sense_num == 2:
            score += 4

    # ── Signal 3: Blue Book attested ────────────────────────────────
    if bb_attested:
        score += 20

    # ── Signal 4: Data completeness ─────────────────────────────────
    if example_count > 0:
        score += min(example_count * 2, 10)
    if form_count > 0:
        score += min(form_count, 8)

    # ── Signal 5: Grammatical class hint ────────────────────────────
    # Slight noun boost — most English search terms are nouns
    if grammatical_class in ("N", "N-DEP", "N-KIN"):
        score += 3

    return score


def rank_results(
    conn: sqlite3.Connection,
    results: List[Dict[str, Any]],
    query: str,
) -> List[Dict[str, Any]]:
    """
    Re-rank a list of search result dicts by relevance.

    Each result dict must have at least 'entry_id'. The function enriches
    with scoring data and returns the list sorted by descending score.
    A 'relevance_score' key is added to each result.

    Args:
        conn: SQLite connection to skiri_pawnee.db
        results: List of result dicts (from your existing search)
        query: The user's search string

    Returns:
        The same list, sorted by relevance_score (descending)
    """
    if not results or not query:
        return results

    cur = conn.cursor()
    q = query.lower().strip()

    for result in results:
        eid = result.get("entry_id")
        if not eid:
            result["relevance_score"] = 0
            continue

        # Gather glosses
        cur.execute(
            "SELECT sense_number, definition FROM glosses "
            "WHERE entry_id = ? ORDER BY sense_number",
            (eid,),
        )
        glosses = [(r[0], r[1]) for r in cur.fetchall()]

        # Gather E2S matches (join on headword since entry_id is NULL)
        headword = result.get("headword", "")
        cur.execute(
            "SELECT english_word FROM english_index "
            "WHERE (skiri_term = ? OR skiri_term = ?) "
            "AND english_word LIKE ?",
            (headword, headword.rstrip("ʔ'"), f"%{q}%"),
        )
        ei_words = [r[0] for r in cur.fetchall()]

        # Counts
        cur.execute(
            "SELECT COUNT(*) FROM examples WHERE entry_id = ?", (eid,)
        )
        example_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM paradigmatic_forms WHERE entry_id = ?", (eid,)
        )
        form_count = cur.fetchone()[0]

        bb = result.get("blue_book_attested", False)
        gram_class = result.get("grammatical_class", "")

        result["relevance_score"] = score_entry(
            query=query,
            ei_words=ei_words,
            glosses=glosses,
            bb_attested=bool(bb),
            example_count=example_count,
            form_count=form_count,
            grammatical_class=gram_class,
        )

    results.sort(key=lambda r: -r.get("relevance_score", 0))
    return results


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os

    query = sys.argv[1] if len(sys.argv) > 1 else "dog"

    db_path = os.environ.get("SKIRI_DB_PATH", "skiri_pawnee.db")
    if not os.path.exists(db_path):
        # Try common locations
        for p in ["skiri_pawnee.db", "../skiri_pawnee.db", "../../skiri_pawnee.db"]:
            if os.path.exists(p):
                db_path = p
                break

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Simulate search: collect candidates from both FTS sources
    candidates = {}

    # Gloss FTS
    cur.execute(
        "SELECT g.entry_id, g.definition, g.sense_number, "
        "l.headword, l.grammatical_class, l.blue_book_attested "
        "FROM fts_glosses fg "
        "JOIN glosses g ON fg.rowid = g.id "
        "JOIN lexical_entries l ON g.entry_id = l.entry_id "
        "WHERE fts_glosses MATCH ?",
        (query,),
    )
    for r in cur.fetchall():
        eid = r["entry_id"]
        if eid not in candidates:
            candidates[eid] = {
                "entry_id": eid,
                "headword": r["headword"],
                "grammatical_class": r["grammatical_class"],
                "blue_book_attested": r["blue_book_attested"],
            }

    # E2S (resolve via skiri_term → headword)
    cur.execute(
        "SELECT ei.english_word, ei.skiri_term, "
        "l.entry_id, l.headword, l.grammatical_class, l.blue_book_attested "
        "FROM english_index ei "
        "LEFT JOIN lexical_entries l "
        "  ON (l.headword = ei.skiri_term OR l.normalized_form = ei.skiri_term) "
        "WHERE ei.english_word LIKE ? AND l.entry_id IS NOT NULL",
        (f"%{query}%",),
    )
    for r in cur.fetchall():
        eid = r["entry_id"]
        if eid not in candidates:
            candidates[eid] = {
                "entry_id": eid,
                "headword": r["headword"],
                "grammatical_class": r["grammatical_class"],
                "blue_book_attested": r["blue_book_attested"],
            }

    results = list(candidates.values())
    ranked = rank_results(conn, results, query)

    print(f"'{query}' — {len(ranked)} results\n")
    for i, r in enumerate(ranked[:15], 1):
        bb = " [BB]" if r.get("blue_book_attested") else ""
        print(f"  {i:2d}. [{r['relevance_score']:5.0f}]  {r['headword']:25s}  ({r['grammatical_class']}){bb}")

    conn.close()
