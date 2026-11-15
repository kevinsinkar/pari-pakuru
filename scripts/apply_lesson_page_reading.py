#!/usr/bin/env python3
"""The lessons' text as the page prints it (2026-11-14).

Every line of the twenty lessons' stored text that is not plain English was
cut from the scan of the Blue Book and read: 938 strips, 72 of them a second
time at a wider and larger cut (scripts/source_audit/lesson_text_reading.py;
the readings are in reports/source_audit_2026-11/lesson_text_reading/). This
script puts the readings into the `lessons` table. It makes no form: every
change is what a strip shows, and the report names the strip.

1. By hand. The changes of decisions.json: a word the OCR split over two
   lines, a piece of a breakdown line that the OCR read as an English word
   (to for ta), a line under a flaw in the scan. Each was looked at twice.
   Letters that a flaw in the scan covers stand in square brackets, filled
   in only where the same sentence stands whole elsewhere in the lesson.
2. Titles. A title becomes what the title line of the page shows.
3. The end of a lesson's last note. The extraction left there the title of
   the next lesson, and after lesson 20 the whole glossary (which is kept in
   extracted_data/blue_book_glossary.json). Both are cut.
4. From the comparison of the readings with the stored words, the kinds one
   reading settles, as in the audit of the Blue Book table: an accent the
   page has and the stored text lacks; a raised dot, apostrophe or space;
   the OCR's known slips on accented vowels. Never the other way: an accent,
   dot or apostrophe that the stored text has and the reading lacks is not
   taken from one reading. Sentence punctuation is not touched.
   For each change the report says whether the audit's reader, at the same
   place on the page, read the same.
5. Four rows of the Blue Book table that are lines of the lessons and were
   never read at their own line (decisions.json, "table_rows"), with their
   copies in bb_gap_triage and extracted_data/blue_book_extracted.json.
6. extracted_data/lessons.json is written as a copy of the table.

Usage:
    python scripts/apply_lesson_page_reading.py            # lists what it would change; changes nothing
    python scripts/apply_lesson_page_reading.py --apply    # backs up, writes, appends to the report, writes the dump
    python scripts/apply_lesson_page_reading.py --check    # exit 0 if the lessons hold the readings
"""
import argparse
import collections
import copy
import datetime as dt
import difflib
import json
import os
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
REPORT = ROOT / "reports" / "lesson_text_ocr_report.txt"
EXTRACTED = ROOT / "extracted_data" / "blue_book_extracted.json"
out = fl.out


def unit_text(lesson, where):
    node = lesson
    for p in where:
        node = node[p]
    return node or ""


def set_unit(lesson, where, text):
    node = lesson
    for p in where[:-1]:
        node = node[p]
    node[where[-1]] = text


def swallowed_title(text, title):
    """Where the next lesson's title begins, if the text ends with it (or with its first line); else None.

    The end of the text is compared in letters with the title as the page has it. The OCR damaged several of
    these titles (KI Rid RA. KU? for KIRÚ RA•KU?), so a close match of capitals is enough."""
    if not title:
        return None
    words = title.split()
    wanted = [lt.plain(" ".join(words[:j])) for j in range(1, len(words) + 1)]
    tokens = list(lt.re.finditer(r"\S+", text))
    best = (0.0, 0, None)                    # (how alike, how many words, where it begins)
    for k in range(1, min(6, len(tokens)) + 1):
        tail = text[tokens[-k].start():]
        letters = [ch for ch in tail if ch.isalpha()]
        if not letters or sum(ch.isupper() for ch in letters) < 0.6 * len(letters):
            continue
        for w in wanted:
            alike = 1.0 if lt.ocr_fold(tail) == lt.ocr_fold(w) else difflib.SequenceMatcher(None, lt.plain(tail), w, autojunk=False).ratio()
            if alike >= 0.8 and (alike, k) > best[:2]:
                best = (alike, k, tokens[-k].start())
    return best[2]


def plan(conn, doc):
    """(lessons before, lessons after, log, the grading of the result)."""
    lessons = lt.load_lessons(conn)
    before = copy.deepcopy(lessons)
    by_no = {x["lesson_number"]: x for x in lessons}
    decided = lt.decisions()
    log = collections.defaultdict(list)

    # 1. by hand
    for ch in decided.get("change", []):
        try:
            text = unit_text(by_no[ch["lesson"]], ch["where"])
        except (IndexError, KeyError, TypeError):
            text = ""
        if ch["old"] not in text and ch["new"] not in text:
            # The place has moved since the decision was written (scripts/pair_lesson_dialogues.py took lines out of
            # the dialogues and put a note in front of lesson 2's): the text is looked for in the lesson's other strings.
            found = [u["where"] for u in lt.stored_units([by_no[ch["lesson"]]])[ch["lesson"]]["units"]
                     if ch["new"] in u["text"] or ch["old"] in u["text"]]
            if len(found) == 1:
                ch = dict(ch, where=found[0])
                text = unit_text(by_no[ch["lesson"]], ch["where"])
        # the old text may be the beginning of the new one ("We ti" in "We ti p[it]ku."): what is already new is set aside
        rest = text.replace(ch["new"], "\0")
        n = rest.count(ch["old"])
        if n == 1:
            set_unit(by_no[ch["lesson"]], ch["where"], rest.replace(ch["old"], ch["new"]).replace("\0", ch["new"]))
            log["hand"].append(ch)
        elif n == 0 and ch["new"] in text:
            log["hand done"].append(ch)
        else:
            log["problems"].append("L%d %s: %r stands %d times" % (ch["lesson"], "/".join(map(str, ch["where"])), ch["old"], n))
    for st in decided.get("set", []):
        if by_no[st["lesson"]][st["column"]] != st["value"]:
            log["set"].append(dict(st, was=by_no[st["lesson"]][st["column"]]))
            by_no[st["lesson"]][st["column"]] = st["value"]

    # 2. titles
    graded = lt.grade(conn, doc, lessons)
    read_title = {}
    for t in graded["titles"]:
        read_title[t["lesson"]] = t["read"]
        if t["kind"] != "same" and "[?]" not in t["read"]:
            log["titles"].append((t["lesson"], t["stored"], t["read"], t["kind"]))
            by_no[t["lesson"]]["skiri_title"] = t["read"]

    # 3. the end of the last note
    for lesson in lessons:
        n, notes = lesson["lesson_number"], lesson["grammar_notes"]
        if not notes:
            continue
        text = notes[-1]["text"]
        if n < 20:
            cut = swallowed_title(text, read_title.get(n + 1) or by_no[n + 1]["skiri_title"])
            if cut is not None:
                log["tails"].append((n, "the title of lesson %d" % (n + 1), text[cut:].strip()))
                notes[-1]["text"] = text[:cut].rstrip()
        else:
            at = text.find(decided.get("glossary_starts_with") or "\0")
            if at != -1:
                log["tails"].append((n, "the glossary", "%d characters, from %r" % (len(text) - at, text[at:at + 60].strip())))
                notes[-1]["text"] = text[:at].rstrip()

    # 4. what one reading settles; again until nothing is left, because a corrected word can change the line-up
    for _ in range(5):
        graded = lt.grade(conn, doc, lessons)
        todo = [d for d in graded["differences"]
                if d["one_reading"] and not d.get("left") and not d["audit_here"].startswith("otherwise")]
        if not todo:
            break
        by_unit = collections.defaultdict(list)
        for d in todo:
            by_unit[(d["lesson"], tuple(d["where"]))].append(d)
        moved = 0
        for (n, where), items in by_unit.items():
            text = unit_text(by_no[n], list(where))
            edge = len(text) + 1
            for d in sorted(items, key=lambda d: -d["start"]):
                if d["end"] > edge or text[d["start"]:d["end"]] != d["stored"]:
                    continue                                   # overlaps one already taken: the next round sees it
                text = text[:d["start"]] + d["read"] + text[d["end"]:]
                edge = d["start"]
                log["one reading"].append(d)
                moved += 1
            set_unit(by_no[n], list(where), text)
        if not moved:
            log["problems"].append("%d differences could not be placed" % len(todo))
            break
    graded = lt.grade(conn, doc, lessons)
    return before, lessons, log, graded


def table_rows(conn):
    """The rows of the Blue Book table of decisions.json, each with its form now, the form it is to have, whether
    it has it, and its copies: rows of bb_gap_triage and places in extracted_data/blue_book_extracted.json with
    the same form, lesson and English."""
    extracted = json.loads(EXTRACTED.read_text(encoding="utf-8"))
    rows = []
    for r in lt.decisions().get("table_rows", []):
        now, lesson, english = conn.execute(
            "select bb_skiri_form, lesson_number, bb_english from blue_book_attestations where id = ?", (r["id"],)).fetchone()
        if "replace" in r:
            a, b = r["replace"]
            done = a not in now and b in now
            old, new = (now.replace(b, a), now) if done else (now, now.replace(a, b))
        else:
            old, new, done = r["old"], r["new"], now == r["new"]
        triage = [t[0] for t in conn.execute(
            "select id from bb_gap_triage where bb_skiri_form = ? and lesson_number = ? and bb_english = ?", (old, lesson, english))]
        places = [i for i, e in enumerate(extracted)
                  if e.get("skiri_form") == old and e.get("lesson_number") == lesson and e.get("english_translation") == english]
        rows.append(dict(r, old=old, new=new, now=now, done=done, triage_ids=triage, extracted_index=places))
    return rows


def changed_columns(before, after):
    out_ = []
    for b, a in zip(before, after):
        for col in ("skiri_title", "english_title", "dialogues", "grammar_notes"):
            if b[col] != a[col]:
                out_.append((a["lesson_number"], col))
    return out_


def as_rows(conn, lessons):
    """lesson -> the values extracted_data/lessons.json holds of it."""
    templates = dict(conn.execute("select lesson_number, template_ids from lessons"))
    rows = {}
    for x in lessons:
        rows[x["lesson_number"]] = {"skiri_title": x["skiri_title"], "english_title": x["english_title"],
                                    "page_start": x["page_start"], "page_end": x["page_end"], "dialogues": x["dialogues"],
                                    "grammar_notes": x["grammar_notes"],
                                    "templates": json.loads(templates[x["lesson_number"]]) if templates[x["lesson_number"]] else []}
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: list them only)")
    ap.add_argument("--check", action="store_true", help="exit 0 if the lessons hold the readings")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    doc = fitz.open(str(lt.PDF))
    before, after, log, graded = plan(conn, doc)
    rows = table_rows(conn)
    columns = changed_columns(before, after)
    data, file_diffs = fl.file_differences(as_rows(conn, after))
    still = [d for d in graded["differences"] if not d.get("left")]
    left = [d for d in graded["differences"] if d.get("left")]
    titles_open = [t for t in graded["titles"] if t["kind"] != "same"]
    conn.close()

    if args.check:
        problems = list(log["problems"])
        if columns:
            problems.append("%d values of the lessons table are not what the page reading gives" % len(columns))
        if still:
            problems.append("%d differences between the reading and the stored text are neither taken nor left by decision" % len(still))
        if titles_open:
            problems.append("%d titles differ from the title line of the page" % len(titles_open))
        if any(not r["done"] for r in rows):
            problems.append("%d rows of the Blue Book table are not as decided" % sum(not r["done"] for r in rows))
        if file_diffs:
            problems.append("extracted_data/lessons.json differs from the table in %d values" % len(file_diffs))
        if graded["not_read"]:
            problems.append("%d strips are not read" % len(graded["not_read"]))
        if problems:
            out("NOT in step: " + "; ".join(problems))
            return 1
        out("the lessons hold the page reading: %d strips read (%d twice), %d Pawnee words of the stored text in them; "
            "no difference is open; %d are left by decision, each with its reason; the 20 titles are the title lines of "
            "the page; extracted_data/lessons.json is a copy of the table" % (
                graded["read"], graded["read_twice"], graded["stored_words_not_english_in_strips_read"], len(left)))
        return 0

    kinds = collections.Counter(d["kind"] for d in log["one reading"])
    seen_by_audit = collections.Counter(d["audit_here"].split(":")[0] for d in log["one reading"])
    header = ["apply_lesson_page_reading — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "strips read: %d of %d (%d a second time); Pawnee words of the stored text in them: %d" % (
                  graded["read"], graded["strips"], graded["read_twice"], graded["stored_words_not_english_in_strips_read"]),
              "changes by hand after a second look: %d (already in place: %d); values set: %d" % (
                  len(log["hand"]), len(log["hand done"]), len(log["set"])),
              "titles taken from the title line: %d" % len(log["titles"]),
              "text of another section cut from the end of a last note: %d lessons" % len(log["tails"]),
              "changes one reading settles: %d  %s" % (len(log["one reading"]), dict(kinds)),
              "   of them, the audit's reader read the same at that place: %d; no audit reading at that place: %d; "
              "the audit's crop there showed another word: %d" % (
                  seen_by_audit["the same"], seen_by_audit["no reading"], seen_by_audit["another word"]),
              "rows of the Blue Book table to correct: %d" % sum(not r["done"] for r in rows),
              "values of the lessons table that change: %d; of extracted_data/lessons.json: %d" % (len(columns), len(file_diffs)),
              "differences left by decision: %d; neither taken nor left: %d" % (len(left), len(still))]
    where = lambda w: "/".join(str(p) for p in w)
    body = ["", "== 1. By hand, after a second look (lesson, where, strip: old -> new; why)"]
    for ch in log["hand"]:
        body.append("  L%-2d %-28s %-18s %s -> %s" % (ch["lesson"], where(ch["where"]), ch["strip"], ch["old"], ch["new"]))
        body.append("        %s" % ch["why"])
    for st in log["set"]:
        body.append("  L%-2d %-28s %r -> %r   %s" % (st["lesson"], st["column"], st["was"], st["value"], st["why"]))
    body += ["", "== 2. Titles (lesson, stored -> the title line of the page; kind)"]
    body += ["  L%-2d %s -> %s   (%s)" % t for t in log["titles"]] or ["  none"]
    body += ["", "== 3. Cut from the end of a lesson's last note (lesson, what, the text)"]
    body += ["  L%-2d %s: %s" % t for t in log["tails"]] or ["  none"]
    body += ["", "== 4. From one reading (lesson, strip, where: old -> new; kind; what the audit's reader read at that place)"]
    for d in sorted(log["one reading"], key=lambda d: (d["lesson"], lt.order_key((d["strip"],)))):
        body.append("  L%-2d %-9s %-28s %s -> %s   (%s; audit: %s)" % (
            d["lesson"], d["strip"], where(d["where"]), d["stored"], d["read"], d["kind"], d["audit_here"]))
    body += ["", "== 5. Rows of the Blue Book table (id: old -> new; why)"]
    for r in rows:
        body.append("  #%d %s -> %s%s" % (r["id"], r["old"] if len(r["old"]) < 70 else "... %s ..." % r["replace"][0],
                                          r["new"] if len(r["new"]) < 70 else "... %s ..." % r["replace"][1],
                                          "   (already so)" if r["done"] else "   (copies: %d in bb_gap_triage, %d in the extracted file)" % (
                                              len(r["triage_ids"]), len(r["extracted_index"]))))
        body.append("        %s" % r["why"])
    tail = ["", "== Left as they are, by decision (strip, stored | read: why)"]
    tail += ["  %-9s %s | %s: %s" % (d["strip"], d["stored"], d["read"], d["left"]) for d in left] or ["  none"]
    tail += ["", "== Neither taken nor left"]
    tail += ["  %-9s L%-2s %-40s %s | %s" % (d["strip"], d.get("lesson"), d["kind"], d["stored"], d["read"]) for d in still] or ["  none"]
    tail += ["  title L%d: %s | %s (%s)" % (t["lesson"], t["stored"], t["read"], t["kind"]) for t in titles_open]
    tail += ["  " + p for p in log["problems"]]

    if not args.apply:
        out("\n".join(header + body + tail))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0
    if log["problems"]:
        out("\n".join(header + tail))
        out("NOT applied: see the problems above")
        return 1

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_lesson_page_reading.db" % stamp))
    conn = sqlite3.connect(str(DB))
    by_no = {x["lesson_number"]: x for x in after}
    for n, col in columns:
        value = by_no[n][col]
        if col in ("dialogues", "grammar_notes"):
            value = json.dumps(value, ensure_ascii=False)
        conn.execute("update lessons set %s = ? where lesson_number = ?" % col, (value, n))
    note = "read at its own line of the page by lesson_text_reading %s (was %%s): %%s" % dt.date.today().isoformat()
    extracted = json.loads(EXTRACTED.read_text(encoding="utf-8"))
    extracted_changed = 0
    for r in rows:
        if r["done"]:
            continue
        old_note = conn.execute("select notes from blue_book_attestations where id = ?", (r["id"],)).fetchone()[0]
        new_note = (old_note + " | " if old_note else "") + note % (r["old"], r["why"])
        conn.execute("update blue_book_attestations set bb_skiri_form = ?, notes = ? where id = ? and bb_skiri_form = ?",
                     (r["new"], new_note, r["id"], r["old"]))
        conn.execute("update blue_book_attestations set full_sentence_pawnee = ? where id = ? and full_sentence_pawnee = ?",
                     (r["new"], r["id"], r["old"]))
        for tid in r["triage_ids"]:
            conn.execute("update bb_gap_triage set bb_skiri_form = ? where id = ? and bb_skiri_form = ?", (r["new"], tid, r["old"]))
        for i in r["extracted_index"]:
            for key in ("skiri_form", "full_sentence_pawnee"):
                if extracted[i].get(key) == r["old"]:
                    extracted[i][key] = r["new"]
                    extracted_changed += 1
    conn.commit()
    conn.close()
    if extracted_changed:
        fl.write_json_like(EXTRACTED, extracted)
    if file_diffs:
        fl.write_copy(data, as_rows(sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True), after))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    header += ["", "written: %d values of the lessons table, %d rows of the Blue Book table, %d values in "
               "extracted_data/blue_book_extracted.json, %d in extracted_data/lessons.json" % (
                   len(columns), sum(not r["done"] for r in rows), extracted_changed, len(file_diffs)),
               "backup: OneDrive/pari_pakuru_backups/skiri_pawnee_backup_%s_lesson_page_reading.db" % stamp]
    text = "\n".join(header + body + tail) + "\n"
    if REPORT.exists():            # the record of the earlier runs is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
