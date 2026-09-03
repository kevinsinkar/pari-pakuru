"""
Phase 5.2b — In-app spaced repetition (SM-2 scheduling).
=========================================================

Server-side review scheduling over dictionary entries. Progress lives in the
SQLite DB (srs_cards / srs_reviews) — covered by the OneDrive-synced backup
regime; the review log is append-only so history is never lost.

Scheduler: classic SM-2 at day granularity.
  again  -> lapse: reps=0, due today (repeats within the session), ease -0.20
  hard   -> interval * 1.2, ease -0.15
  good   -> 1d, then 6d, then interval * ease
  easy   -> interval * ease * 1.3, ease +0.15
Ease is clamped to [1.3, 3.0].

New-card selection prefers Blue-Book-attested entries with pronunciations,
then high-confidence entries — the same priorities as the flashcard decks.
Scope filters: lesson=N (Blue Book lesson vocabulary) or tag=X (semantic tag).
"""

from datetime import date, timedelta

MAX_NEW_PER_SESSION = 10
MAX_DUE_PER_SESSION = 40

GRADES = ("again", "hard", "good", "easy")


def ensure_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS srs_cards (
            entry_id      TEXT PRIMARY KEY REFERENCES lexical_entries(entry_id),
            ease          REAL NOT NULL DEFAULT 2.5,
            interval_days REAL NOT NULL DEFAULT 0,
            reps          INTEGER NOT NULL DEFAULT 0,
            lapses        INTEGER NOT NULL DEFAULT 0,
            due           TEXT,                -- ISO date
            last_review   TEXT
        );
        CREATE TABLE IF NOT EXISTS srs_reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id        TEXT NOT NULL,
            grade           TEXT NOT NULL,
            interval_before REAL,
            interval_after  REAL,
            reviewed_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_srs_due ON srs_cards(due);
    """)
    conn.commit()


def schedule(ease, interval, reps, grade):
    """Pure SM-2 transition. Returns (ease, interval_days, reps, lapsed)."""
    if grade == "again":
        return max(1.3, ease - 0.20), 0.0, 0, True
    if grade == "hard":
        return max(1.3, ease - 0.15), max(1.0, interval * 1.2), reps + 1, False
    if grade == "easy":
        new_ease = min(3.0, ease + 0.15)
        base = interval * ease * 1.3 if reps >= 2 else (6.0 if reps == 1 else 2.0)
        return new_ease, max(1.0, base), reps + 1, False
    # good
    if reps == 0:
        return ease, 1.0, 1, False
    if reps == 1:
        return ease, 6.0, 2, False
    return ease, max(1.0, interval * ease), reps + 1, False


def grade_card(conn, entry_id, grade):
    """Apply a review grade; returns the new due date (ISO string)."""
    if grade not in GRADES:
        raise ValueError(f"bad grade {grade!r}")
    cur = conn.cursor()
    cur.execute("SELECT ease, interval_days, reps FROM srs_cards "
                "WHERE entry_id = ?", (entry_id,))
    row = cur.fetchone()
    ease, interval, reps = (row if row else (2.5, 0.0, 0))
    new_ease, new_interval, new_reps, lapsed = schedule(
        ease, interval, reps, grade)
    due = (date.today() + timedelta(days=round(new_interval))).isoformat()
    cur.execute(
        "INSERT INTO srs_cards (entry_id, ease, interval_days, reps, lapses, "
        "  due, last_review) VALUES (?,?,?,?,?,?,date('now')) "
        "ON CONFLICT(entry_id) DO UPDATE SET ease=?, interval_days=?, reps=?, "
        "  lapses=lapses+?, due=?, last_review=date('now')",
        (entry_id, new_ease, new_interval, new_reps, 1 if lapsed else 0, due,
         new_ease, new_interval, new_reps, 1 if lapsed else 0, due))
    cur.execute(
        "INSERT INTO srs_reviews (entry_id, grade, interval_before, "
        "  interval_after) VALUES (?,?,?,?)",
        (entry_id, grade, interval, new_interval))
    conn.commit()
    return due


CARD_FIELDS = """le.entry_id, le.headword, le.normalized_form,
    le.simplified_pronunciation, le.phonetic_form, le.grammatical_class,
    le.blue_book_attested,
    (SELECT definition FROM glosses g WHERE g.entry_id = le.entry_id
     ORDER BY sense_number LIMIT 1) AS definition"""


def _scope_clause(lesson=None, tag=None):
    """SQL fragment + params restricting entries to a lesson or tag scope."""
    if lesson:
        # vocabulary items only — matches what the lesson page lists as words
        # (dialogue/phrase rows carry weak prefix links to grammar particles)
        return ("""le.entry_id IN (
            SELECT entry_id FROM blue_book_attestations
            WHERE lesson_number = ? AND entry_id IS NOT NULL
              AND context_type IN ('BASIC_WORDS', 'ADDITIONAL_WORDS'))""",
            [lesson])
    if tag:
        return ("""le.entry_id IN (
            SELECT entry_id FROM semantic_tags WHERE tag = ?)""", [tag])
    return ("1=1", [])


def get_queue(conn, lesson=None, tag=None):
    """Cards for a study session: due reviews first, then new cards."""
    ensure_tables(conn)
    cur = conn.cursor()
    scope, params = _scope_clause(lesson, tag)
    today = date.today().isoformat()

    cur.execute(f"""
        SELECT {CARD_FIELDS}, s.reps, s.due
        FROM srs_cards s JOIN lexical_entries le ON le.entry_id = s.entry_id
        WHERE s.due <= ? AND {scope}
        ORDER BY s.due LIMIT ?""",
        [today] + params + [MAX_DUE_PER_SESSION])
    cols = [d[0] for d in cur.description]
    due_cards = [dict(zip(cols, r)) for r in cur.fetchall()]

    cur.execute(f"""
        SELECT {CARD_FIELDS}, 0 AS reps, NULL AS due
        FROM lexical_entries le
        WHERE le.entry_id NOT IN (SELECT entry_id FROM srs_cards)
          AND {scope} AND definition IS NOT NULL
        ORDER BY le.blue_book_attested DESC,
                 (le.simplified_pronunciation IS NOT NULL) DESC,
                 COALESCE(le.form2_confidence, 0) DESC,
                 le.entry_id
        LIMIT ?""", params + [MAX_NEW_PER_SESSION])
    new_cards = [dict(zip([d[0] for d in cur.description], r))
                 for r in cur.fetchall()]

    for c in due_cards:
        c["is_new"] = False
    for c in new_cards:
        c["is_new"] = True
    return due_cards + new_cards


def get_stats(conn, lesson=None, tag=None):
    ensure_tables(conn)
    cur = conn.cursor()
    scope, params = _scope_clause(lesson, tag)
    today = date.today().isoformat()
    cur.execute(f"""
        SELECT count(*) FROM srs_cards s
        JOIN lexical_entries le ON le.entry_id = s.entry_id
        WHERE s.due <= ? AND {scope}""", [today] + params)
    due = cur.fetchone()[0]
    cur.execute(f"""
        SELECT count(*) FROM srs_cards s
        JOIN lexical_entries le ON le.entry_id = s.entry_id
        WHERE {scope}""", params)
    learning = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM srs_reviews "
                "WHERE date(reviewed_at) = date('now')")
    today_reviews = cur.fetchone()[0]
    return {"due": due, "learning": learning, "reviews_today": today_reviews}
