"""
Phase 4.4 — Add community_feedback table to skiri_pawnee.db.

Usage:
    python scripts/add_feedback_table.py          # default DB path
    python scripts/add_feedback_table.py --db path/to/db
"""

import argparse
import os
import sqlite3
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(PROJECT_ROOT, "skiri_pawnee.db")


def create_feedback_table(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS community_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            form_field TEXT,
            feedback_type TEXT NOT NULL CHECK (feedback_type IN ('flag', 'confirm')),
            issue_type TEXT,
            suggested_correction TEXT,
            comment TEXT,
            reporter_name TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'reviewed', 'accepted', 'rejected')),
            reviewer_note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            reviewed_at TEXT,
            FOREIGN KEY (entry_id) REFERENCES lexical_entries(entry_id)
        )
    """)

    # Index for quick lookups by status (admin queue) and entry (detail page counts)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_status
        ON community_feedback(status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_entry
        ON community_feedback(entry_id)
    """)

    conn.commit()

    # Report
    count = cur.execute("SELECT COUNT(*) FROM community_feedback").fetchone()[0]
    print(f"community_feedback table ready ({count} rows) in {db_path}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add community_feedback table")
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()
    create_feedback_table(args.db)
