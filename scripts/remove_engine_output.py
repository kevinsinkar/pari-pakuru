#!/usr/bin/env python3
"""Remove from the database what the withdrawn grammar engines stored.

The engines review of 2026-11-14 (reports/engines_review/decision.md) found
tables and values that an engine had computed and that stood beside copied
forms. The owner chose to remove them. Each step is one decision:

  3  drop `morpheme_inventory` and `verb_template_slots`: written by the
     conjugation engine; six of the 37 rows are pieces Parks does not print.
     Parks's own tables are in extracted_data/grammatical_overview_tables.json.
  5  empty `lexical_entries.form2_confidence`: the score of the form 2
     predictor, from March, no longer what the code gives, and measured only
     on the forms the predictor's rules were read from.
  7  drop `possession_examples` and `noun_stems`: the possession engine's
     own output; delete the rows of `kinship_paradigms` that are not from
     Appendix 3 (typed from the OCR text; the Blue Book's forms are in
     `blue_book_attestations` as read from the scan); delete from
     `function_words` four words that no source prints (OCR slips).

Nothing copied from a source is removed. A backup is made first, and what was
removed stays in git history (DB/dump/ at commit 814e8cc).

Usage:
    python scripts/remove_engine_output.py --decision 3            # says what it would remove; changes nothing
    python scripts/remove_engine_output.py --decision 3 --apply    # backs up, removes, appends to the report, writes the dump
    python scripts/remove_engine_output.py --check                 # exit 0 if none of it is left
"""
import argparse
import datetime as dt
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "engines_review" / "stage4_database_report.txt"

DROP = {"3": ["morpheme_inventory", "verb_template_slots"],
        "7": ["possession_examples", "noun_stems"]}
# rows of function_words that are OCR slips, not words: (id, headword as stored, what the scan reads there)
NON_WORDS = [(376, "ilanʔ", "Háu'"), (378, "kirti", "Kirú"), (382, "kti", "kú"), (400, "stiks", "Súks")]


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def has_table(conn, name):
    return conn.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def rows(conn, sql, args=()):
    try:
        return conn.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        return []


def plan(conn, decision):
    """(lines for the report, SQL statements to run)."""
    lines, sql = [], []
    for table in DROP.get(decision, []):
        if has_table(conn, table):
            n = conn.execute("select count(*) from %s" % table).fetchone()[0]
            lines.append("drop table %s (%d rows)" % (table, n))
            sql.append(("drop table %s" % table, ()))
    if decision == "5":
        n = conn.execute("select count(*) from lexical_entries where form2_confidence is not null").fetchone()[0]
        if n:
            lines.append("lexical_entries.form2_confidence: %d values set to NULL (the column stays; nothing reads it)" % n)
            sql.append(("update lexical_entries set form2_confidence = NULL where form2_confidence is not null", ()))
    if decision == "7":
        for rid, term, stem, source in rows(conn, "select rowid, english_term, stem, source from kinship_paradigms "
                                                  "where source != 'appendix3' order by rowid"):
            lines.append("kinship_paradigms: delete the row for '%s', stem %s, source %s (not from Appendix 3)" % (term, stem, source))
            sql.append(("delete from kinship_paradigms where rowid = ? and source != 'appendix3'", (rid,)))
        for rid, word, scan in NON_WORDS:
            if rows(conn, "select 1 from function_words where id = ? and headword = ?", (rid, word)):
                lines.append("function_words: delete row %d, %s (an OCR slip; the scan reads %s there)" % (rid, word, scan))
                sql.append(("delete from function_words where id = ? and headword = ?", (rid, word)))
    return lines, sql


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--decision", choices=["3", "5", "7"], help="which decision of the paper to carry out")
    ap.add_argument("--apply", action="store_true", help="remove (default: say what would be removed)")
    ap.add_argument("--check", action="store_true", help="exit 0 if nothing of any step is left")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    if args.check:
        left = [line for d in ("3", "5", "7") for line in plan(conn, d)[0]]
        conn.close()
        if left:
            out("engine output still in the database:")
            for line in left:
                out("  " + line)
            return 1
        out("no engine output is left in the database: the four engine tables are gone, the form 2 score is empty, "
            "kinship_paradigms holds Appendix 3 only, the four OCR slips are out of function_words")
        return 0
    if not args.decision:
        ap.error("give --decision 3, 5 or 7, or --check")
    lines, sql = plan(conn, args.decision)
    conn.close()
    header = "remove_engine_output — decision %s — %s — %s" % (
        args.decision, "APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    out(header)
    for line in lines:
        out("  " + line)
    if not lines:
        out("  nothing to remove: this step is already done")
        return 0
    if not args.apply:
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("skiri_pawnee_backup_%s_engines_decision%s.db" % (stamp, args.decision))
    shutil.copy2(DB, backup)
    conn = sqlite3.connect(str(DB))
    for statement, values in sql:
        conn.execute(statement, values)
    conn.commit()
    conn.close()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    text = "\n".join([header] + ["  " + line for line in lines] +
                     ["  backup: OneDrive/pari_pakuru_backups/%s" % backup.name]) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("  backup: OneDrive/pari_pakuru_backups/%s" % backup.name)
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
