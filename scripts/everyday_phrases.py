#!/usr/bin/env python3
"""The phrases the site gathers by situation are the book's, each with its own English (2026-11-15).

curriculum/everyday_phrases.json lists the Useful Phrases of the lessons of
Pari Pakuru' and the two Useful Conversations of lesson 20, and says under
which situation the site shows each ("At the table", "Coming and going").
The file holds copied forms; this script proves that they are copies.

    --check   exit 0 if
              1. every Pawnee line, dialect label and English line stands,
                 letter for letter, in a note of its lesson headed "Useful
                 Phrases" or "Useful Conversations" (the lessons' text, read
                 from the scan line by line on 2026-11-14);
              2. every line and its English share a row of the printed page,
                 or the English is the next line under the Pawnee: the place
                 of each stored word on the page comes from the text layer of
                 the scan, so a meaning cannot slide to its neighbour;
              3. the table of Blue Book rows agrees: a PHRASE row that is one
                 of these phrases has the same English, and no phrase row of
                 a Useful Phrases section is missing from the file.
    --list    the phrases by situation, as the page shows them

No form is made and no image is read. Step 2 needs the scan
(pari pakuru/Blue Book - Pari Pakuru.pdf); without it only 1 and 3 run, and
the script says so.
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
from web import learning  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
HEADINGS = ("Useful Phrases", "Useful Conversations")


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def squash(text):
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def spans(text, piece):
    """Where a piece stands in a text as whole words: [(start, end)]."""
    return [m.span() for m in re.finditer(r"(?<!\S)" + re.escape(piece) + r"(?!\S)", text)]


def rows_of_the_page(conn):
    """(lesson, index of the note, offset of a word in the note's text) -> (page, height on the page)."""
    import fitz
    import lesson_text_reading as lt

    doc = fitz.open(str(lt.PDF))
    lessons = lt.load_lessons(conn)
    lines, _lost = lt.lines_of(lessons, doc)
    place = {}
    for line in lines.values():
        _x0, y0, _x1, y1 = line["box"]
        for tok in line["stored"]:
            if tok["where"][0] == "grammar_notes" and tok["where"][-1] == "text":
                place[(tok["lesson"], tok["where"][1], tok["start"])] = (line["page"], (y0 + y1) / 2)
    return place


def same_row_problems(conn, data):
    """Lines whose English is neither on the row of the Pawnee nor on the line under it."""
    place = rows_of_the_page(conn)
    notes = {n: json.loads(raw or "[]") for n, raw in conn.execute("select lesson_number, grammar_notes from lessons")}
    problems, proved = [], 0

    def rows(lesson, index, text, piece):
        """For each place the piece stands: (row of its first word, row of its last word)."""
        found = []
        for a, b in spans(text, piece):
            at = [place[(lesson, index, m.start() + a)] for m in re.finditer(r"\S+", text[a:b]) if (lesson, index, m.start() + a) in place]
            if at:
                found.append((at[0], at[-1]))
        return found

    def check(lesson, heading, skiri, english, label):
        nonlocal proved
        for index, note in enumerate(notes[lesson]):
            if note.get("heading") != heading:
                continue
            text = note.get("text") or ""
            for (sp, sy), (lp, ly) in rows(lesson, index, text, skiri):
                for (ep, ey), _ in rows(lesson, index, text, english):
                    beside = ep == sp and abs(ey - sy) <= 5
                    under = ep == lp and 5 < ey - ly <= 26
                    if beside or under:
                        proved += 1
                        return
        problems.append("%s: %r and %r do not share a row of the page" % (label, skiri, english))

    for p in data["phrases"]:
        if p.get("english"):
            form = p["skiri"] + (" (%s)" % p["dialect"] if p.get("dialect") else "")
            check(p["lesson"], "Useful Phrases", form, p["english"], "lesson %d" % p["lesson"])
    for conv in data["conversations"]:
        for line in conv["lines"]:
            check(conv["lesson"], "Useful Conversations", line["skiri"], line["english"],
                  "lesson %d, conversation %d" % (conv["lesson"], conv["number"]))
    return problems, proved


def table_problems(conn, data):
    """PHRASE rows of the Blue Book table against the file."""
    notes = {n: json.loads(raw or "[]") for n, raw in conn.execute("select lesson_number, grammar_notes from lessons")}
    by_form = {}
    for p in data["phrases"]:
        by_form.setdefault((p["lesson"], learning._phrase_key(p["skiri"]).lower()), []).append(p)
    for conv in data["conversations"]:
        for line in conv["lines"]:
            by_form.setdefault((conv["lesson"], learning._phrase_key(line["skiri"]).lower()), []).append(line)
    left_out = {(p["lesson"], learning._phrase_key(p["skiri"]).lower()) for p in data.get("left_out", [])}
    problems, compared = [], 0
    for rid, lesson, form, english in conn.execute(
            "select id, lesson_number, bb_skiri_form, bb_english from blue_book_attestations where context_type = 'PHRASE' order by id"):
        form = (form or "").strip()
        section = [n.get("text") or "" for n in notes.get(lesson, []) if n.get("heading") in HEADINGS]
        if not any(spans(t, form) for t in section):
            continue                          # a title, a line of verse, a piece of a grammar example: not a useful phrase
        key = (lesson, learning._phrase_key(form).lower())
        if key in left_out:
            continue
        items = by_form.get(key)
        if not items:
            # a row may be a piece of a line of the file (the conversations are stored whole)
            if any(form in it["skiri"] for its in by_form.values() for it in its if True) and lesson == 20:
                continue
            problems.append("row %d (lesson %s) %r is a useful phrase of the table and is not in the file" % (rid, lesson, form))
            continue
        compared += 1
        wanted = [it.get("english") or "" for it in items]
        if not any(squash(w) == squash(english) or (not w) for w in wanted):
            problems.append("row %d (lesson %s) %r: the table has %r, the file %r" % (rid, lesson, form, english, wanted))
    return problems, compared


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 0 if every line is proved")
    ap.add_argument("--list", action="store_true", help="print the phrases by situation")
    args = ap.parse_args()
    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    data = json.loads(learning.PHRASES_FILE.read_text(encoding="utf-8"))

    if args.list or not args.check:
        shown = learning.phrases_data(conn)
        for s in shown["situations"]:
            out("== %s (%d)" % (s["label"], len(s["rows"])))
            for row in s["rows"]:
                forms = " / ".join(("or " if f["after_or"] else "") + f["skiri"] + (" (%s)" % f["dialect"] if f["dialect"] else "") for f in row["forms"])
                glosses = " · ".join("%s [lesson %s]" % (g["english"], ", ".join(map(str, g["lessons"]))) for g in row["glosses"])
                out("   %-44s %s%s" % (forms, glosses, "  " + " ".join(row["also"]) if row["also"] else ""))
        for conv in shown["conversations"]:
            out("== Conversation %d of lesson %d" % (conv["number"], conv["lesson"]))
            for line in conv["lines"]:
                out("   %-2s %-52s %s" % (line["who"], line["skiri"], line["english"]))
        out("")
        out("%d phrases of %d lessons in %d situations; %d conversation lines" % (
            shown["count"], len(shown["lessons"]), len(shown["situations"]), sum(len(c["lines"]) for c in shown["conversations"])))
        if not args.check:
            return

    problems = learning.phrase_problems(conn, data)
    n_lines = len(data["phrases"]) + sum(len(c["lines"]) for c in data["conversations"])
    try:
        row_problems, proved = same_row_problems(conn, data)
        with_scan = True
    except (ImportError, FileNotFoundError, RuntimeError) as error:       # no PyMuPDF, or no scan in this copy
        row_problems, proved, with_scan = [], 0, False
        out("the rows of the page were NOT checked: %s" % error)
    tab_problems, compared = table_problems(conn, data)
    for p in problems + row_problems + tab_problems:
        out("PROBLEM  " + p)
    ok = not (problems or row_problems or tab_problems)
    if ok:
        with_english = sum(1 for p in data["phrases"] if p.get("english")) + sum(len(c["lines"]) for c in data["conversations"])
        out("the phrases are the book's: %d lines (%d phrases of %d lessons, %d conversation lines) stand letter for letter in the lessons' text; "
            "%s; %d rows of the Blue Book table say the same" % (
                n_lines, len(data["phrases"]), len({p["lesson"] for p in data["phrases"]}),
                sum(len(c["lines"]) for c in data["conversations"]),
                "%d of the %d lines with an English of their own share a row of the page with it, or stand over it" % (proved, with_english)
                if with_scan else "the rows of the page were not checked", compared))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
