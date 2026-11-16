#!/usr/bin/env python3
"""Which dialect a Blue Book form is written in, as far as the book itself says (2026-11-15).

Pari Pakuru' writes for both dialects of Pawnee. Its alphabet chapter says
that its spelling and accent follow South Band speakers ("the South Band e is
pronounced by Skidi speakers just as if it were an i"; hr is h for Skidi
speakers; "The accent marked in this book is that of some South Band
speakers"), and it marks a form (SK) or (SB) where the two differ. The
statements, read from the scan, are in
extracted_data/blue_book_dialect_statements.json. The site had shown all of
it as Skiri.

This script gives each Blue Book row, and each dictionary entry made from a
Blue Book word, a label and the reason for it. It makes no form and changes
none:

    SK, SB        the book's own mark on the form's line of the page (found
                  with the text layer of the scan, or standing in the
                  lesson's text as read from the page)
    SB spelling   the form is written with e or with hr, which the alphabet
                  chapter says are the South Band way; or Parks prints these
                  same letters as the South Band form of one of his entries,
                  beside a Skiri headword that differs
    (no label)    the book says nothing that bears on the form

"SB spelling" is a statement about the spelling, by the book's own rule. It
does not say how a Skiri speaker says the word, and no Skiri form is worked
out from it. Where a row is tied to a Skiri dictionary entry, or Parks names
the entry, the label carries the entry's id so that a page can show the
dictionary's own form.

Usage:
    python scripts/label_bluebook_dialect.py            # what the table would hold; changes nothing
    python scripts/label_bluebook_dialect.py --apply    # backs up, writes the table bb_dialect_labels, reports, writes the dump
    python scripts/label_bluebook_dialect.py --check    # exit 0 if the table holds the labels
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import fix_bluebook_pairing as fp  # noqa: E402
import lesson_text_reading as lt  # noqa: E402
from bluebook_only_entries import letters, short  # noqa: E402
from web import learning  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "bluebook_dialect_report.txt"
MARK = re.compile(r"^\((S[KB])\)[.,;:]?$")
OFFSET = learning.BLUE_BOOK_PAGE_OFFSET
out = fp.out

TABLE = """create table if not exists bb_dialect_labels (
    attestation_id integer, entry_id text, form text not null, label text not null, basis text not null,
    skiri_entry_id text)"""
# A row whose form the text layer garbles, labelled from a sentence of the book instead. Each names the sentence,
# and the script refuses the label if the sentence no longer stands in the lesson's text.
BY_HAND = {
    1901: ("SK", 1, "the Skidi word for yes (haú)", "the book's own note in lesson 1 calls this \"the Skidi word for yes\""),
}
WHY = {
    "e": "written with e: the book says \"the South Band e is pronounced by Skidi speakers just as if it were an i\" (p. xxi)",
    "hr": "written with hr: the book says hr \"is pronounced simply as h by Skidi speakers\" (p. xx)",
}


def marks_in_text(lessons):
    """(lesson, form as letters) -> the marks (SK, SB) that stand straight after the form in the lesson's text."""
    found = collections.defaultdict(set)
    for lesson in lessons:
        strings = [ln.get("skiri") or "" for d in lesson["dialogues"] for ln in d.get("lines", [])]
        strings += [n.get("text") or "" for n in lesson["grammar_notes"]]
        for text in strings:
            tokens = text.split()
            for i, tok in enumerate(tokens):
                m = MARK.match(tok)
                if not m:
                    continue
                for n in range(1, 7):                      # the one to six words before the mark
                    if i - n < 0:
                        break
                    found[(lesson["lesson_number"], letters("".join(tokens[i - n:i])))].add(m.group(1))
    return found


def mark_on_page(layer, form, pages, english):
    """The book's mark after the form on a row of the page: (mark or None, page, how sure)."""
    seen = []
    for page in pages:
        rows = layer.rows(page)
        for r, a, b in layer.places(page, form):
            row = rows[r][1]
            after = row[b + 1][2] if b + 1 < len(row) else ""
            m = MARK.match(after)
            rest = " ".join(w for _, _, w in row[b + 1:]) + " " + (" ".join(w for _, _, w in rows[r + 1][1]) if r + 1 < len(rows) else "")
            fits = bool(english) and fp.squash(english)[:14] in fp.squash(rest)
            seen.append((m.group(1) if m else None, page, fits))
    if not seen:
        return None, None, "the form was not found in the text layer"
    fitting = [s for s in seen if s[2]] or seen                # the place whose row holds the row's English, if any
    marks = {s[0] for s in fitting}
    if len(marks) == 1:
        return fitting[0][0], fitting[0][1], "on its row of the page"
    return None, None, "the form stands at %d places with different marks (%s)" % (
        len(fitting), ", ".join(sorted(str(m) for m in marks)))


def plan(conn, layer):
    conn.row_factory = sqlite3.Row
    lessons = lt.load_lessons(conn)
    pages = {x["lesson_number"]: (x["page_start"], x["page_end"]) for x in lessons}
    in_text = marks_in_text(lessons)
    source = {r[0]: (r[1] or "parks") for r in conn.execute("select entry_id, source from lexical_entries")}
    head = {r[0]: r[1] for r in conn.execute("select entry_id, headword from lexical_entries")}

    # the South Band forms Parks prints in his entries, where the Skiri headword is written otherwise
    south = collections.defaultdict(list)
    for entry_id, form in conn.execute("select entry_id, form from cognates where language = 'SB'"):
        for piece in re.split(r"[,;]\s*", form or ""):
            key = letters(re.sub(r"\([^)]*\)", "", piece))
            if len(key) >= 3 and key != letters(head.get(entry_id, "")) and short(key) != short(letters(head.get(entry_id, ""))):
                south[key].append((entry_id, piece.strip()))
                south[short(key)].append((entry_id, piece.strip()))

    rows, notes = [], collections.defaultdict(list)
    for r in conn.execute("select id, bb_skiri_form, bb_english, lesson_number, page_number, context_type, dialect_note, entry_id "
                          "from blue_book_attestations order by id"):
        form = (r["bb_skiri_form"] or "").strip()
        if not form:
            continue
        lesson, page = r["lesson_number"], r["page_number"]
        look = ([page] if page else []) + [p for p in range(pages.get(lesson, (1, 0))[0], pages.get(lesson, (1, 0))[1] + 1) if p != page]
        inside = re.search(r"\((S[KB])\)", form)
        if inside:
            mark, where, how = inside.group(1), page, "in the form as stored"
        else:
            mark, where, how = mark_on_page(layer, form, look[:1] or look, r["bb_english"])
            if mark is None:
                from_text = in_text.get((lesson, letters(form)), set())
                if len(from_text) == 1 and (r["dialect_note"] in from_text or how.startswith("the form was not found")):
                    mark, where, how = next(iter(from_text)), page, "in the lesson's text as read from the page"
        if mark is None and r["id"] in BY_HAND:
            hand_mark, hand_lesson, sentence, reason = BY_HAND[r["id"]]
            text = " ".join(n.get("text") or "" for x in lessons if x["lesson_number"] == hand_lesson for n in x["grammar_notes"])
            if sentence in text:
                mark, where, how = hand_mark, page, "by " + reason
            else:
                notes["a label given by hand has lost its sentence"].append("#%d: %r is not in lesson %d" % (r["id"], sentence, hand_lesson))
        stored = r["dialect_note"]
        if stored == "both" and mark is None:
            notes["the extraction says the book gives this in both dialects; no mark was found on the form's line"].append(
                "#%d L%s %s (%s)" % (r["id"], lesson, form, how))
        if stored in ("SK", "SB") and mark != stored:
            notes["the table's dialect_note has a mark the page does not show there"].append(
                "#%d L%s %s: dialect_note %s, the page: %s (%s)" % (r["id"], lesson, form, stored, mark, how))
        spelling = learning.south_band_spelling(form)
        key = letters(form)
        cognate = (south.get(key) or south.get(short(key)) or [None])[0] if " " not in form.strip(" .!?,") and len(key) >= 3 else None
        tied = r["entry_id"] if r["entry_id"] and source.get(r["entry_id"]) != "blue_book" else None
        if mark:
            label = mark
            basis = ("the book marks this form (%s) %s (lesson %s, p. %s of the book)" % (mark, how, lesson, (where - OFFSET) if where else "?")
                     if not how.startswith("by ") else "%s (lesson %s, p. %s of the book)" % (how[3:], lesson, (where - OFFSET) if where else "?"))
            if mark == "SK" and spelling:
                notes["marked (SK) by the book and written with e or hr"].append("#%d L%s %s" % (r["id"], lesson, form))
        elif spelling or cognate:
            label = "SB spelling"
            parts = [WHY[m] for m in spelling]
            if cognate:
                parts.append("Parks prints %s as the South Band form in his entry %s" % (cognate[1], head[cognate[0]]))
            basis = "; ".join(parts)
        else:
            continue
        rows.append((r["id"], None, form, label, basis, (cognate[0] if cognate else None) or tied))

    for entry_id, headword, variant_of in conn.execute(
            "select entry_id, headword, bb_variant_of from lexical_entries where source = 'blue_book' order by entry_id"):
        spelling = learning.south_band_spelling(headword)
        if not spelling:
            continue
        rows.append((None, entry_id, headword, "SB spelling", "; ".join(WHY[m] for m in spelling), variant_of))
    return rows, notes


def summary(rows):
    count = collections.Counter(r[3] for r in rows if r[0])
    entries = sum(1 for r in rows if r[1])
    named = sum(1 for r in rows if r[5])
    return ("Blue Book rows labelled: %d (the book's own mark: SK %d, SB %d; South Band spelling: %d); "
            "Blue Book-only entries written the South Band way: %d; labels that name a Skiri dictionary entry: %d" % (
                sum(count.values()), count["SK"], count["SB"], count["SB spelling"], entries, named))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="back up and write the table")
    ap.add_argument("--check", action="store_true", help="exit 0 if the table holds the labels")
    ap.add_argument("--show", action="store_true", help="list every label")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB)) if args.apply else sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    layer = fp.Layer(fitz.open(str(lt.PDF)))
    rows, notes = plan(conn, layer)
    conn.row_factory = None
    has = conn.execute("select count(*) from sqlite_master where type='table' and name='bb_dialect_labels'").fetchone()[0]
    now = [tuple(r) for r in conn.execute("select * from bb_dialect_labels")] if has else []
    same = sorted(now, key=repr) == sorted(rows, key=repr)

    if args.check:
        if not same:
            out("the table bb_dialect_labels does not hold the labels (%d rows in it, %d by the page): run --apply" % (len(now), len(rows)))
            raise SystemExit(1)
        out("the dialect labels are in the table: " + summary(rows) + ". Every label has its reason beside it: the book's "
            "mark on the form's line, a statement of the book's alphabet chapter, or a South Band form Parks prints")
        raise SystemExit(0)

    head = ["label_bluebook_dialect — %s — %s" % ("APPLY" if args.apply else "DRY RUN", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
            summary(rows), "in the table now: %d rows; %s" % (len(now), "the same" if same else "to be written"), ""]
    body = []
    for title, lines in notes.items():
        body += ["== %s (%d)" % (title, len(lines))] + ["  " + x for x in lines] + [""]
    if args.show or args.apply:
        body.append("== every label (row or entry, form, label, the Skiri entry it names: basis)")
        for att, entry, form, label, basis, skiri in rows:
            body.append("  %-22s %-34s %-12s %-28s %s" % ("#%d" % att if att else entry, form, label, skiri or "", basis))
    for line in head + (body if args.show else [x for x in body if not x.startswith("  #") and not x.startswith("  BB-")][:60]):
        out(line)
    if not args.apply:
        out("dry run: nothing was changed (use --apply; --show lists every label)")
        return
    if same:
        out("nothing to do")
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("skiri_pawnee_backup_%s_dialect_labels.db" % stamp)
    shutil.copy2(DB, backup)
    conn.execute(TABLE)
    conn.execute("delete from bb_dialect_labels")
    conn.executemany("insert into bb_dialect_labels values (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    text = "\n".join(head + body + ["", "backup: OneDrive/pari_pakuru_backups/%s" % backup.name]) + "\n"
    if REPORT.exists():
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("written; backup: %s; report: %s" % (backup.name, REPORT.relative_to(ROOT).as_posix()))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], check=True)


if __name__ == "__main__":
    main()
