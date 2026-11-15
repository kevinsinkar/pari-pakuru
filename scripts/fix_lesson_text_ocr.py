#!/usr/bin/env python3
"""The lessons' text and titles: the audit's reading of the Blue Book scan.

The audit of 2026-11-13 read every Blue Book form from the scan and corrected
the Blue Book table. In the `lessons` table it corrected a dialogue line only
where the whole line was identical to an old reading. Old readings inside
running text (the grammar notes, a few dialogue lines) and in the lesson
titles were left, and are on the public lesson pages. This script applies
what the audit already established. It reads nothing new and makes no form.

1. Running text. Every correction "old -> new" of
   reports/source_audit_2026-11/bluebook_applied_report.txt (all three runs,
   the latest reading of a form winning) whose old reading still stands in
   the dialogues or grammar notes of a lesson that covers the page the audit
   read it on, PROVIDED the two differ inside the form in more than an accent or a capital:
   in letters, spacing, a bullet or punctuation. Such an old reading is OCR
   damage and is not what the page prints anywhere.
   Where only an accent, a capital or the punctuation at the end differs, nothing is changed: the OCR
   dropped every accent, the audit read the form at one place, and the same
   letters may stand elsewhere on the page without the accent. Those places
   are counted and listed; they need the page. The page was read on
   2026-11-14, line by line: scripts/apply_lesson_page_reading.py. Of the
   196 places listed here then, 173 now agree with the audit's reading; at
   10 the page has the form without the accent at that place (asaki in the
   dialogue of lesson 8, asáki in its word list), and 13 differ only in the
   punctuation of the sentence or a plus sign.
2. Titles. The title of a lesson becomes the Blue Book table's reading of
   the title line, where the table has one: a row of that lesson, on the
   lesson's first page, in capitals, whose English is the lesson's English
   title. Titles without such a row are left and listed.
   Since 2026-11-14 all twenty titles are the title lines as read from the
   page (apply_lesson_page_reading.py). This script still checks that a
   title holds the table's reading where there is one; a title of two lines
   (lesson 20) holds more than the row of its second line.
3. extracted_data/lessons.json is written as a copy of the table.

Usage:
    python scripts/fix_lesson_text_ocr.py            # lists what it would change; changes nothing
    python scripts/fix_lesson_text_ocr.py --apply    # backs up, writes, appends to the report, writes the dump
    python scripts/fix_lesson_text_ocr.py --check    # exit 0 if nothing is left to do
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"
AUDIT_REPORT = ROOT / "reports" / "source_audit_2026-11" / "bluebook_applied_report.txt"
LESSONS_JSON = ROOT / "extracted_data" / "lessons.json"
REPORT = ROOT / "reports" / "lesson_text_ocr_report.txt"

# what extracted_data/lessons.json holds of each lesson ("templates" is the table's template_ids)
COPIED = ("skiri_title", "english_title", "page_start", "page_end", "dialogues", "grammar_notes", "templates")

KINDS = ("accent restored", "OCR slip corrected", "two readings agree", "read at its own place",
         "apostrophe, dot or space")
PAIR = re.compile(r"^\s*p\. (\d+)\s+(%s)\s+(.+?) -> (.+?)\s*$" % "|".join(re.escape(k) for k in KINDS))


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def fold(text):
    """Without accents, capitals, and the punctuation or the '+' of a formula at either end.

    Two readings that fold alike differ only by an accent, a capital, or by where the audit's reader let the
    form end (a full stop, a comma, brackets, the '+' after a prefix). None of that is OCR damage inside the
    form, and none of it may be carried into running text.
    """
    plain = "".join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)).lower()
    return plain.strip(" .,;:!?()\"“”+")


def audit_pairs():
    """old reading -> (the audit's final reading, pages the audit read it on).

    The report holds three runs. A later line for the same old reading wins, and a reading that was itself
    corrected later is followed to its last form.
    """
    step, pages = {}, {}
    for line in AUDIT_REPORT.read_text(encoding="utf-8").split("\n"):
        m = PAIR.match(line)
        if not m:
            continue
        page, old, new = int(m.group(1)), m.group(3), m.group(4)
        step[old] = new
        pages.setdefault(old, set()).add(page)
    pairs = {}
    for old in step:
        new, seen = step[old], {old}
        while new in step and new not in seen:
            seen.add(new)
            new = step[new]
        if new != old:
            pairs[old] = (new, pages[old])
    for w in withdrawn_pairs():
        if pairs.get(w["old"], (None,))[0] == w["new"]:
            del pairs[w["old"]]
    return pairs


def withdrawn_pairs():
    """Corrections of the audit that the reading of the lessons' pages withdrew (2026-11-14): the audit's crop
    had been cut at another line than the row's own. reports/source_audit_2026-11/lesson_text_reading/decisions.json"""
    decisions = AUDIT_REPORT.parent / "lesson_text_reading" / "decisions.json"
    if not decisions.exists():
        return []
    return json.loads(decisions.read_text(encoding="utf-8")).get("audit_pairs_withdrawn", [])


def stands_alone(text, start, end):
    """True if the match is a whole word or phrase of the running text, not part of a longer one.

    The OCR wrote the bullet between the parts of a word as " ." or lost it, so a match that is followed by
    a dot and a letter, or that touches a bullet, an apostrophe or a hyphen, may be the middle of a word.
    """
    before = text[start - 1] if start > 0 else " "
    after = text[end:end + 3]
    nxt = after[:1] or " "                      # the end of the text counts as a space
    if before.isalnum() or before in "•'’-":
        return False
    if nxt.isalnum() or nxt in "•'’-":
        return False
    if re.match(r"\s?\.\s?\w", after):
        return False
    return True


def replace_in(text, usable, found):
    """Replace every old reading that stands in the string; longest first."""
    for old, new in usable:
        at = text.find(old)
        while at != -1:
            if stands_alone(text, at, at + len(old)):
                text = text[:at] + new + text[at + len(old):]
                found.append((old, new))
                at = text.find(old, at + len(new))
            else:
                at = text.find(old, at + 1)
    return text


def walk(node, usable, found):
    """The same structure with the old readings replaced in every string."""
    if isinstance(node, str):
        return replace_in(node, usable, found)
    if isinstance(node, list):
        return [walk(x, usable, found) for x in node]
    if isinstance(node, dict):
        return {k: walk(v, usable, found) for k, v in node.items()}
    return node


def plain_english(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def title_reading(conn, number, page_start, english_title):
    """The table's reading of the title line of a lesson, or None."""
    if not english_title:
        return None
    rows = conn.execute(
        "select bb_skiri_form, bb_english from blue_book_attestations "
        "where lesson_number = ? and page_number = ? order by id", (number, page_start)).fetchall()
    readings = [form for form, english in rows
                if form and form == form.upper() and form != form.lower()
                and plain_english(english) == plain_english(english_title)]
    if len(set(readings)) != 1:
        return None
    return readings[0]


def plan(conn):
    pairs = audit_pairs()
    damage = {old: v for old, v in pairs.items() if fold(old) != fold(v[0])}       # letters, spacing, punctuation
    accent = {old: v for old, v in pairs.items() if fold(old) == fold(v[0])}       # an accent or a capital only
    longest = lambda items: sorted(items, key=lambda x: (-len(x[0]), x[0]))
    changes = []          # (lesson, column, new text for the table, [(old, new)])
    titles = []           # (lesson, stored, reading)
    no_reading = []       # (lesson, stored)
    elsewhere = []        # (lesson, old) damage on a page the audit did not read it on
    accent_only = []      # (lesson, old, new) left: needs the page
    after = {}            # lesson -> the row as it will be
    for number, s_title, e_title, p_start, p_end, dialogues, notes, template_ids in conn.execute(
            "select lesson_number, skiri_title, english_title, page_start, page_end, dialogues, "
            "grammar_notes, template_ids from lessons order by lesson_number"):
        row = {"skiri_title": s_title, "english_title": e_title, "page_start": p_start, "page_end": p_end,
               "templates": json.loads(template_ids) if template_ids else []}
        here = lambda v: any(p_start <= p <= p_end for p in v[1])
        usable = longest((old, v[0]) for old, v in damage.items() if here(v))
        other = longest((old, v[0]) for old, v in damage.items() if not here(v))
        accents_here = longest((old, v[0]) for old, v in accent.items() if here(v))
        for column, stored in (("dialogues", dialogues), ("grammar_notes", notes)):
            data = json.loads(stored) if stored else None
            if stored and json.dumps(data, ensure_ascii=False) != stored:
                raise SystemExit("lesson %s, %s: the stored JSON is not written the way this script writes it" % (number, column))
            found = []
            new_data = walk(data, usable, found)
            row[column] = new_data
            if found:
                changes.append((number, column, json.dumps(new_data, ensure_ascii=False), found))
            stray = []
            walk(new_data, other, stray)
            elsewhere += [(number, old) for old, new in stray]
            left = []
            walk(new_data, accents_here, left)
            accent_only += [(number, old, new) for old, new in left]
        reading = title_reading(conn, number, p_start, e_title)
        if reading is None:
            no_reading.append((number, s_title))
        elif reading not in (s_title or ""):       # a title of two lines holds more than the row of one of them
            titles.append((number, s_title, reading))
            row["skiri_title"] = reading
        after[number] = row
    return pairs, damage, changes, titles, no_reading, elsewhere, accent_only, after


def file_differences(after):
    """Where extracted_data/lessons.json is not what the table will hold."""
    data = json.loads(LESSONS_JSON.read_text(encoding="utf-8"))
    diffs = []
    for lesson in data:
        row = after[lesson["lesson_number"]]
        for key in COPIED:
            if lesson.get(key) != row[key]:
                diffs.append((lesson["lesson_number"], key))
    return data, diffs


def write_json_like(path, data):
    """Write a JSON file the way it is written now: its indentation, its line endings, its last newline."""
    raw = path.read_text(encoding="utf-8")
    indent = 2 if raw.startswith(("{\n  ", "[\n  ")) else 1 if raw.startswith(("{\n ", "[\n ")) else None
    ending = "\r\n" if b"\r\n" in path.read_bytes() else "\n"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""),
                    encoding="utf-8", newline=ending)


def write_copy(data, after):
    """extracted_data/lessons.json with the table's values (after: lesson -> the row)."""
    for lesson in data:
        row = after[lesson["lesson_number"]]
        for key in COPIED:
            lesson[key] = row[key]
    write_json_like(LESSONS_JSON, data)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: list them only)")
    ap.add_argument("--check", action="store_true", help="exit 0 if nothing is left to do")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    pairs, damage, changes, titles, no_reading, elsewhere, accent_only, after = plan(conn)
    conn.close()
    data, diffs = file_differences(after)
    n_places = sum(len(found) for _, _, _, found in changes)
    n_readings = len({old for _, _, _, found in changes for old, new in found})

    if args.check:
        problems = []
        if changes:
            problems.append("%d old OCR readings stand in the lessons' text" % n_places)
        if titles:
            problems.append("%d titles differ from the Blue Book table's reading of the title line" % len(titles))
        if diffs:
            problems.append("extracted_data/lessons.json differs from the table in %d values" % len(diffs))
        if problems:
            out("NOT in step: " + "; ".join(problems))
            return 1
        out("lessons in step with the audit: none of the %d old readings it corrected in letters, spacing or "
            "punctuation stands in the text; %d titles are the table's reading of the title line, %d have no "
            "reading; extracted_data/lessons.json is a copy of the table"
            % (len(damage), 20 - len(no_reading), len(no_reading)))
        out("not this script's business: %d places where the audit read a form with an accent or a capital at one "
            "place and the same letters stand in the text without it, and %d where an old reading stands on a page "
            "the audit did not read it on. The page decides those, and it was read on 2026-11-14: "
            "scripts/apply_lesson_page_reading.py --check" % (len(accent_only), len(elsewhere)))
        return 0

    header = ["fix_lesson_text_ocr — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "old readings the audit corrected: %d distinct; %d of them differ from the reading in letters, spacing or "
              "punctuation" % (len(pairs), len(damage)),
              "still standing in the lessons' text: %d places, %d distinct readings, in %d lessons" % (
                  n_places, n_readings, len({c[0] for c in changes})),
              "titles to take from the Blue Book table's reading of the title line: %d; titles with no such reading, left: %d" % (
                  len(titles), len(no_reading)),
              "values of extracted_data/lessons.json that are not the table's: %d" % len(diffs),
              "left on purpose: %d places where only an accent or a capital differs" % len(accent_only)]
    body = ["", "== 1. Running text (lesson, where, old reading -> the audit's reading)"]
    for number, column, _, found in changes:
        for old, new in found:
            body.append("  L%-2d %-13s %s -> %s" % (number, column, old, new))
    body += ["", "== 2. Titles (lesson, stored -> the table's reading of the title line)"]
    body += ["  L%-2d %s -> %s" % t for t in titles] or ["  none"]
    body += ["", "== Titles the table has no reading of: left as they are, for a person with the page"]
    body += ["  L%-2d %s" % (n, t if t else "(no Skiri title stored)") for n, t in no_reading]
    body += ["", "== Old readings standing on a page the audit did not read them on: left"]
    body += ["  L%-2d %s" % e for e in elsewhere] or ["  none"]
    body += ["", "== 3. extracted_data/lessons.json (lesson, value that is not the table's)"]
    body += ["  L%-2d %s" % d for d in diffs] or ["  none"]
    tail = ["", "== Left on purpose: only an accent or a capital differs (lesson, as it stands, the audit's reading)"]
    tail += ["  L%-2d %s | %s" % a for a in accent_only] or ["  none"]

    if not args.apply:
        out("\n".join(header + body))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_lesson_text.db" % stamp))
    conn = sqlite3.connect(str(DB))
    for number, column, text, found in changes:
        conn.execute("update lessons set %s = ? where lesson_number = ?" % column, (text, number))
    for number, stored, reading in titles:
        conn.execute("update lessons set skiri_title = ? where lesson_number = ? and skiri_title = ?", (reading, number, stored))
    conn.commit()
    conn.close()
    if diffs:
        write_copy(data, after)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    header += ["", "written: %d places in %d lessons, %d titles, %d values in extracted_data/lessons.json" % (
        n_places, len({c[0] for c in changes}), len(titles), len(diffs)),
               "backup: OneDrive/pari_pakuru_backups/skiri_pawnee_backup_%s_lesson_text.db" % stamp]
    text = "\n".join(header + body + tail) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
