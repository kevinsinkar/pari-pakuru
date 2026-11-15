#!/usr/bin/env python3
"""The English beside a Blue Book word is the English of its own row of the page (2026-11-15).

The Blue Book prints its word lists and its Useful Phrases in two columns: the
Pawnee at the left, the English on the same row at the right. The extraction
read the two columns one after the other, and where a gloss runs over two
lines, or a heading stands between, it gave every following word the meaning
of its neighbour. The lesson pages showed those meanings.

The text layer of the scan knows where every word stands. This script takes
the row of the page a form stands on and reads what is to the right of it.
It makes no form and reads no image.

    --survey   every word-list and phrase row of the table against its row of
               the page: how many agree, and the rows that do not (most of
               those are a gloss on two lines, a dialect label, or a form the
               OCR garbled; the list is for a person to read)
    (nothing)  the corrections of reports/source_audit_2026-11/
               bluebook_pairing_fixes.json: what would change; changes nothing
    --apply    backs up the database, corrects the rows, their copies in
               bb_gap_triage and extracted_data/blue_book_extracted.json and
               the one dictionary entry made from a row, appends to
               reports/bluebook_pairing_report.txt, writes the dump
    --check    exit 0 if the table holds the corrections and the text layer
               still shows them

Every correction with "evidence": "layer" is proved again each time the script
runs: the form and the new English must stand on one row of the text layer at
the height the record names. A correction with "evidence": "seen" is one where
the text layer itself has a slip of the OCR; it was read in a cut of the scan
(reports/source_audit_2026-11/lesson_text_reading/second_02.json).
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import fix_lesson_text_ocr as fl  # noqa: E402
import lesson_text_reading as lt  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
FIXES = ROOT / "reports" / "source_audit_2026-11" / "bluebook_pairing_fixes.json"
REPORT = ROOT / "reports" / "bluebook_pairing_report.txt"
EXTRACTED = ROOT / "extracted_data" / "blue_book_extracted.json"
SHOWN = ("BASIC_WORDS", "ADDITIONAL_WORDS", "PHRASE")        # the rows a lesson page shows
out = fl.out


def squash(text):
    """Letters and digits only: the comparison does not turn on punctuation, quotation marks or spacing."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


class Layer:
    """The rows of the pages of the scan, from the text layer."""

    def __init__(self, doc):
        self.doc = doc
        self.pages = {}

    def rows(self, page):
        """[(height of the row, [(x0, x1, word)] left to right)], top to bottom."""
        if page not in self.pages:
            words = sorted(((w[1] + w[3]) / 2, w[0], w[2], w[4]) for w in self.doc[page - 1].get_text("words"))
            rows, band = [], None
            for yc, x0, x1, word in words:
                if band is None or yc - band > 5:
                    rows.append([yc, []])
                    band = yc
                rows[-1][1].append((x0, x1, word))
            self.pages[page] = [(yc, sorted(row)) for yc, row in rows]
        return self.pages[page]

    def places(self, page, form):
        """Where a form stands on a page: [(row index, first word, last word)]. The letters are compared as the
        audit compares them: accents, dots and the OCR's known slips do not count."""
        key = lt.ocr_fold(re.sub(r"\s+", "", form))
        hits = []
        if len(key) < 2:
            return hits
        for r, (_yc, row) in enumerate(self.rows(page)):
            for a in range(len(row)):
                got = ""
                for b in range(a, min(a + 8, len(row))):
                    got += row[b][2]
                    k = lt.ocr_fold(got)
                    if k == key:
                        hits.append((r, a, b))
                        break
                    if len(k) > len(key):
                        break
        return hits

    def beside(self, page, y, form, lines=1):
        """What the page prints to the right of a form on the row at height y; with lines=2, also what the next
        row has under those words (a gloss on two lines). None if the form is not on that row."""
        rows = self.rows(page)
        for r, a, b in self.places(page, form):
            if abs(rows[r][0] - y) > 4:
                continue
            right = rows[r][1][b + 1:]
            text = [w for _, _, w in right]
            if lines > 1 and right and r + 1 < len(rows):
                text += [w for x0, _, w in rows[r + 1][1] if x0 >= right[0][0] - 6]
            return " ".join(text)
        return None


def load_fixes():
    return json.loads(FIXES.read_text(encoding="utf-8"))


def plan(conn, layer):
    """(what to do, what is already done, problems)."""
    fixes = load_fixes()
    todo, done, problems = [], [], []
    for fx in fixes["english"]:
        row = conn.execute("select bb_skiri_form, bb_english, lesson_number, page_number, context_type from blue_book_attestations where id = ?",
                           (fx["id"],)).fetchone()
        if row is None:
            problems.append("row %d is not in the table" % fx["id"])
            continue
        form, english, lesson, page, context = row
        if form != fx["form"] or lesson != fx["lesson"]:
            problems.append("row %d holds %r (lesson %s), not %r" % (fx["id"], form, lesson, fx["form"]))
            continue
        if fx["evidence"] == "layer":
            seen = layer.beside(fx["page"], fx["y"], fx["form"], fx.get("lines", 1))
            if seen is None or squash(seen) != squash(fx["new"]):
                problems.append("row %d: the text layer has %r beside %s on page %d, not %r" % (fx["id"], seen, fx["form"], fx["page"], fx["new"]))
                continue
        item = dict(fx, context=context)
        if english == fx["new"]:
            done.append(("english", item))
        elif english == fx["old"]:
            todo.append(("english", item))
        else:
            problems.append("row %d holds the English %r, neither the old nor the new" % (fx["id"], english))
    for nr in fixes["new_rows"]:
        seen = layer.beside(nr["page"], nr["y"], nr["form"])
        if seen is None or squash(seen) != squash(nr["english"]):
            problems.append("new row %s: the text layer has %r beside it, not %r" % (nr["form"], seen, nr["english"]))
            continue
        n = conn.execute("select count(*) from blue_book_attestations where lesson_number = ? and context_type = ? and bb_skiri_form = ?",
                         (nr["lesson"], nr["context_type"], nr["form"])).fetchone()[0]
        (done if n == 1 else todo if n == 0 else problems).append(
            ("row", nr) if n < 2 else "new row %s stands %d times" % (nr["form"], n))
    for en in fixes["entries"]:
        gloss = [r[0] for r in conn.execute("select definition from glosses where entry_id = ? order by sense_number", (en["entry_id"],))]
        cls = conn.execute("select grammatical_class from lexical_entries where entry_id = ?", (en["entry_id"],)).fetchone()
        tags = {r[0] for r in conn.execute("select tag from semantic_tags where entry_id = ?", (en["entry_id"],))}
        if cls is None:
            problems.append("entry %s is not in the dictionary" % en["entry_id"])
        elif gloss == [en["gloss_new"]] and cls[0] == en["class_new"] and not tags & set(en["drop_tags"]):
            done.append(("entry", en))
        elif gloss in ([en["gloss_old"]], [en["gloss_new"]]):
            todo.append(("entry", en))
        else:
            problems.append("entry %s holds the gloss %r" % (en["entry_id"], gloss))
    return todo, done, problems


def copies(conn, item):
    """The same form with the same old English in bb_gap_triage, and in the extraction file: (ids, indices)."""
    ids = [r[0] for r in conn.execute("select id from bb_gap_triage where bb_skiri_form = ? and lesson_number = ? and bb_english = ?",
                                      (item["form"], item["lesson"], item["old"]))]
    data = json.loads(EXTRACTED.read_text(encoding="utf-8"))
    idx = [i for i, it in enumerate(data) if it.get("skiri_form") == item["form"] and it.get("lesson_number") == item["lesson"]
           and it.get("english_translation") == item["old"]]
    return ids, idx


def describe(kind, item):
    if kind == "english":
        return ["  #%d L%d p.%d %-24s %s  ->  %s   [%s]" % (item["id"], item["lesson"], item["page"], item["form"], item["old"], item["new"], item["evidence"]),
                "        %s" % item["why"]]
    if kind == "row":
        return ["  new row: L%d p.%d %s  %s = %s" % (item["lesson"], item["page"], item["context_type"], item["form"], item["english"]),
                "        %s" % item["why"]]
    return ["  entry %s: gloss %r -> %r; class %r -> %r; tags dropped: %s" % (
        item["entry_id"], item["gloss_old"], item["gloss_new"], item["class_old"], item["class_new"], ", ".join(item["drop_tags"]) or "none"),
        "        %s" % item["why"]]


def survey(conn, layer):
    """Every row a lesson page shows against its row of the page."""
    counts, differ = collections.Counter(), []
    pages = {n: (a, b) for n, a, b in conn.execute("select lesson_number, page_start, page_end from lessons")}
    for rid, lesson, page, context, form, english in conn.execute(
            "select id, lesson_number, page_number, context_type, bb_skiri_form, bb_english from blue_book_attestations "
            "where context_type in (%s) order by lesson_number, id" % ",".join("?" * len(SHOWN)), SHOWN):
        form = (form or "").strip()
        look = ([page] if page else []) + [p for p in range(*[(a, b + 1) for a, b in [pages.get(lesson, (1, 0))]][0]) if p != page]
        found = []
        for p in look:
            for r, a, b in layer.places(p, form):
                row = layer.rows(p)[r][1]
                nxt = layer.rows(p)[r + 1][1] if r + 1 < len(layer.rows(p)) else []
                found.append((p, " ".join(w for _, _, w in row[b + 1:]), " ".join(w for _, _, w in nxt)))
            if found and p == page:
                break
        if not found:
            counts["form not found in the text layer"] += 1
            continue
        want = squash(english)
        if any(want and (squash(right) == want or (not right and squash(below) == want)) for _, right, below in found):
            counts["the same"] += 1
        elif any(want and squash(right) and (squash(right).startswith(want) or want.startswith(squash(right))) for _, right, _b in found):
            counts["begins the same (a gloss on two lines)"] += 1
        else:
            counts["differs"] += 1
            differ.append((rid, lesson, page, context, form, english, found[0]))
    return counts, differ


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="back up and write")
    ap.add_argument("--check", action="store_true", help="exit 0 if the corrections are in the table")
    ap.add_argument("--survey", action="store_true", help="compare every shown row with its row of the page")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB)) if args.apply else sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    layer = Layer(fitz.open(str(lt.PDF)))

    if args.survey:
        counts, differ = survey(conn, layer)
        out("rows a lesson page shows (%s) against the row of the page they stand on:" % ", ".join(SHOWN))
        for k, v in counts.most_common():
            out("  %4d  %s" % (v, k))
        out("")
        out("rows whose English is not what stands to the right of the form (id, lesson, page, context, form | stored | the page):")
        for rid, lesson, page, context, form, english, (p, right, below) in differ:
            out("  %4d L%-2s p%-3s %-16s %-28s | %s | p%s: %s" % (rid, lesson, page, context, form, english, p,
                                                                 right or "(nothing; the row below: %s)" % below[:50]))
        return

    todo, done, problems = plan(conn, layer)
    if args.check:
        for p in problems:
            out("PROBLEM  " + p)
        for kind, item in todo:
            out("NOT DONE " + describe(kind, item)[0].strip())
        ok = not problems and not todo
        out("the Blue Book rows hold the English of their own row of the page: %d corrections, %d rows added, %d entry corrected; "
            "each proved on the text layer or read in a cut" % (
                sum(1 for k, _ in done if k == "english"), sum(1 for k, _ in done if k == "row"), sum(1 for k, _ in done if k == "entry"))
            if ok else "the corrections are not all in the table")
        raise SystemExit(0 if ok else 1)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    head = ["fix_bluebook_pairing — %s — %s" % ("APPLY" if args.apply else "DRY RUN", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
            "to do: %d; already done: %d; problems: %d" % (len(todo), len(done), len(problems)), ""]
    body = []
    for kind, item in todo:
        body += describe(kind, item)
        if kind == "english":
            ids, idx = copies(conn, item)
            body.append("        copies: %d in bb_gap_triage, %d in the extraction file" % (len(ids), len(idx)))
    body += ["", "problems:"] + (["  " + p for p in problems] or ["  none"])
    for line in head + body:
        out(line)
    if problems:
        out("\nnothing is written while there are problems")
        raise SystemExit(1)
    if not args.apply:
        out("\ndry run: nothing was changed and no report was written (use --apply)")
        return
    if not todo:
        out("\nnothing to do")
        return

    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("skiri_pawnee_backup_%s_bluebook_pairing.db" % stamp)
    shutil.copy2(DB, backup)

    data = json.loads(EXTRACTED.read_text(encoding="utf-8"))
    today = dt.date.today().isoformat()
    # the copies are looked up before anything is written: one row's old English is another row's new one
    found = {item["id"]: copies(conn, item) for kind, item in todo if kind == "english"}
    for kind, item in todo:
        if kind == "english":
            note = "English set to that of the row of the page by fix_bluebook_pairing.py %s (was: %s)" % (today, item["old"])
            conn.execute("update blue_book_attestations set bb_english = ?, notes = case when notes is null or notes = '' then ? "
                         "else notes || ' | ' || ? end where id = ? and bb_english = ?", (item["new"], note, note, item["id"], item["old"]))
            ids, idx = found[item["id"]]
            for i in ids:
                conn.execute("update bb_gap_triage set bb_english = ? where id = ?", (item["new"], i))
            for i in idx:
                data[i]["english_translation"] = item["new"]
        elif kind == "row":
            note = "added by fix_bluebook_pairing.py %s: a line of the page the extraction left out" % today
            conn.execute("insert into blue_book_attestations (bb_skiri_form, bb_english, context_type, lesson_number, page_number, "
                         "match_type, match_confidence, notes, created_at) values (?, ?, ?, ?, ?, 'none', 0.0, ?, ?)",
                         (item["form"], item["english"], item["context_type"], item["lesson"], item["page"], note,
                          dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            at = next((i for i, it in enumerate(data) if it.get("lesson_number") == item["lesson"] and it.get("context_type") == item["context_type"]
                       and it.get("skiri_form") == item["after_form"]), len(data) - 1)
            data.insert(at + 1, {"skiri_form": item["form"], "bb_pronunciation": None, "english_translation": item["english"],
                                 "context_type": item["context_type"], "dialect_note": None, "full_sentence_pawnee": None,
                                 "full_sentence_english": None, "lesson_number": item["lesson"], "page_number": item["page"]})
        else:
            conn.execute("update glosses set definition = ? where entry_id = ? and definition = ?", (item["gloss_new"], item["entry_id"], item["gloss_old"]))
            conn.execute("update lexical_entries set grammatical_class = ? where entry_id = ?", (item["class_new"], item["entry_id"]))
            for tag in item["drop_tags"]:
                conn.execute("delete from semantic_tags where entry_id = ? and tag = ?", (item["entry_id"], tag))
    conn.commit()
    fl.write_json_like(EXTRACTED, data)

    text = "\n".join(head + body + ["", "backup: OneDrive/pari_pakuru_backups/%s" % backup.name]) + "\n"
    if REPORT.exists():
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\nwritten; backup: %s" % backup.name)
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], check=True)


if __name__ == "__main__":
    main()
