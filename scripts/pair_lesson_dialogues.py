#!/usr/bin/env python3
"""The dialogues of the lessons: each Pawnee line with its English (2026-11-14).

The Blue Book prints a dialogue in two columns, the Pawnee line on the left
and its English on the same row on the right. `scripts/build_lessons.py` read
the OCR text line by line, and where the OCR had not kept the two columns
together it stored the English as a line of its own, in the field for the
Pawnee: in 83 of the 156 dialogue lines the English stood in the Pawnee field
or was missing, and the lesson pages showed them so.

This script pairs them. It changes no Pawnee word; a word that the page
breaks at the end of a line is joined, as in the reading of lesson 20.

1. A Pawnee line without English takes the English that the page prints to
   its right on the same row. The scan's text layer has the place of every
   word, and scripts/source_audit/lesson_text_reading.py knows on which line
   of the page each stored line stands. The same English stored further down
   as a line of its own is then dropped.
2. A line that holds the Pawnee and its English in one string is cut where
   the English begins.
3. An English line that continues the English of the line before it
   ("No, my grandfather has" / "passed away.") is joined to it; an English
   line after a Pawnee line that has none becomes its English.
4. A Pawnee line that continues the Pawnee line before it is joined to it:
   with nothing between if that line ends in a hyphen (tatuks•á•ka- /
   wahtsu'.), with a space otherwise (Kaas raku•káriu / tatutak•érit.).
5. A section of the notes that the parser had put into a dialogue (lesson 2,
   NOUN PHRASE: Noun•Adjective) becomes the first of the lesson's notes.

Left as printed, with no English of their own: the second dialect's form of
the line above (Haú, tí hitu'. (SK)), an alternative in brackets, and a
breakdown line under a dialogue line.

    python scripts/pair_lesson_dialogues.py            # lists what it would change; changes nothing
    python scripts/pair_lesson_dialogues.py --apply    # backs up, writes, appends to the report, writes the dump
    python scripts/pair_lesson_dialogues.py --check    # exit 0 if every dialogue line is a pair
"""
import argparse
import collections
import copy
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
REPORT = ROOT / "reports" / "lesson_dialogues_pairing_report.txt"
DIALECT = ("(SB)", "(SK)")
out = fl.out


def norm(text):
    return " ".join((text or "").lower().split())


def is_english_line(text, lexicon):
    tokens = text.split()
    return bool(tokens) and all(lt.is_english(t, lexicon) for t in tokens)


def split_merged(text, lexicon):
    """Pawnee and its English in one string: (Pawnee, English), or None. The English is the longest run of English
    words at the end; it begins with a capital or a bracket and is two words or more. A dialect label after the
    Pawnee, (SB) or (SK), stays with the Pawnee."""
    tokens = text.split()
    k = len(tokens)
    while k > 0 and lt.is_english(tokens[k - 1], lexicon):
        k -= 1
    while k < len(tokens) and tokens[k] in DIALECT:
        k += 1
    tail = tokens[k:]
    if k > 0 and len(tail) >= 2 and (tail[0][:1].isupper() or tail[0][:1] in "(\""):
        return " ".join(tokens[:k]), " ".join(tail)
    return None


def row_right(doc, line):
    """What the page prints to the right of a line, on the same row."""
    x0, y0, x1, y1 = line["box"]
    words = []
    for wx0, wy0, wx1, wy1, word, _b, _l, _n in doc[line["page"] - 1].get_text("words"):
        high = min(y1, wy1) - max(y0, wy0)
        if high >= 0.5 * min(y1 - y0, wy1 - wy0) and wx0 >= x1 - 1:
            words.append((wx0, word))
    return " ".join(w for _, w in sorted(words))


def join_text(pieces):
    """Lines of prose as one text; a word broken at the end of a line is joined."""
    text = ""
    for piece in pieces:
        if text.endswith("-") and piece[:1].islower():
            text = text[:-1] + piece
        else:
            text = (text + " " + piece).strip()
    return text


def letters(lesson, moved=()):
    """How often each letter stands in the dialogues of a lesson (and in text moved out of them): pairing lines
    must not lose or double a word."""
    count = collections.Counter()
    strings = [ln.get(k) or "" for dia in lesson["dialogues"] for ln in dia.get("lines", []) for k in ("skiri", "english")]
    for s in strings + list(moved):
        count.update(ch for ch in lt.plain(s) if ch.isalpha())       # a line number is not text
    return count


def plan(conn, doc):
    """(lessons before, lessons after, log)."""
    lessons = lt.load_lessons(conn)
    before = copy.deepcopy(lessons)
    lexicon = lt.english_lexicon(conn)
    lines, _ = lt.lines_of(lessons, doc)
    first_line = {}
    for lid, line in lines.items():
        for t in line["stored"]:
            first_line.setdefault((t["lesson"], tuple(t["where"])), lid)
    log = collections.defaultdict(list)

    for lesson, was in zip(lessons, before):
        n = lesson["lesson_number"]
        expected = []                      # English taken from the page row: the same text stored as a line of its own goes
        moved = []
        dialogues = []
        for d, dia in enumerate(lesson["dialogues"]):
            source = dia.get("lines", [])
            # 5. a section of the notes inside a dialogue: from a heading in capitals to the end
            cut = next((i for i, ln in enumerate(source) if re.match(r"^[A-Z][A-Z ]+:", ln.get("skiri") or "")), None)
            if cut is not None:
                heading = " ".join(w.capitalize() if w.isupper() else w for w in source[cut]["skiri"].split())
                if not any(b.get("heading") == heading for b in lesson["grammar_notes"]):
                    pieces = [ln.get(k) for ln in source[cut + 1:] for k in ("skiri", "english") if ln.get(k)]
                    lesson["grammar_notes"].insert(0, {"heading": heading, "text": join_text(pieces)})
                    moved += [source[cut]["skiri"]] + pieces
                    log["moved"].append((n, d, heading, len(source) - cut))
                source = source[:cut]
            made = []
            for l, ln in enumerate(source):
                skiri, english = (ln.get("skiri") or "").strip(), (ln.get("english") or "").strip()
                where = "L%d dialogue %d line %d" % (n, d + 1, l + 1)
                if skiri and not re.search(r"[A-Za-z]", skiri) and english:
                    cutting = split_merged(english, lexicon)       # only a number in the Pawnee field: the line is in the other
                    if cutting:
                        log["split"].append((where, "%s | %s" % (skiri, english), "%s | %s" % cutting))
                        skiri, english = cutting
                if is_english_line(skiri, lexicon):
                    text = (skiri + " " + english).strip()
                    if norm(text) in expected:
                        expected.remove(norm(text))                # the row's English, stored a second time below
                        log["dropped"].append((where, text))
                    elif made and not made[-1]["english"]:
                        made[-1]["english"] = text
                        log["attached"].append((where, made[-1]["skiri"], text))
                    elif made and (text[:1].islower() or not made[-1]["english"].rstrip().endswith((".", "?", "!"))):
                        made[-1]["english"] += " " + text
                        log["continued"].append((where, made[-1]["skiri"], made[-1]["english"]))
                    else:
                        log["problems"].append("%s: an English line with no Pawnee line to belong to: %r" % (where, text))
                        made.append({"skiri": skiri, "english": english})
                    continue
                lid = first_line.get((n, ("dialogues", d, "lines", l, "skiri")))
                right = row_right(doc, lines[lid]).strip() if lid else ""
                if not english:
                    cutting = split_merged(skiri, lexicon)
                    if right and skiri.endswith(right):
                        log["split"].append((where, skiri, "%s | %s" % (skiri[:-len(right)].rstrip(), right)))
                        skiri, english = skiri[:-len(right)].rstrip(), right
                    elif cutting:
                        log["split"].append((where, skiri, "%s | %s" % cutting))
                        skiri, english = cutting
                    elif right and is_english_line(right, lexicon):
                        english = right
                        expected.append(norm(right))
                        log["from the row"].append((where, skiri, right))
                continues = (not english and made and skiri[:1].islower() and "+" not in skiri
                             and not made[-1]["skiri"].rstrip().endswith((".", "?", "!")))
                if continues:
                    head = made[-1]["skiri"].rstrip()
                    made[-1]["skiri"] = head[:-1] + skiri if head.endswith("-") else head + " " + skiri
                    log["joined"].append((where, made[-1]["skiri"]))
                else:
                    made.append({"skiri": skiri, "english": english})
            dialogues.append(dict(dia, lines=made))
        lesson["dialogues"] = dialogues
        for text in expected:
            log["page only"].append((n, text))
        if letters(lesson, moved) != letters(was):
            gone = letters(was) - letters(lesson, moved)
            more = letters(lesson, moved) - letters(was)
            if not log["page only"] or gone:
                log["problems"].append("L%d: the letters of the dialogues are not the same before and after "
                                       "(lost %s, gained %s)" % (n, dict(gone), dict(more)))
        for d, dia in enumerate(lesson["dialogues"]):
            for l, ln in enumerate(dia["lines"]):
                if is_english_line(ln["skiri"], lexicon):
                    log["still English"].append("L%d dialogue %d line %d: %s" % (n, d + 1, l + 1, ln["skiri"]))
                elif not ln["english"]:
                    log["no English"].append((n, d + 1, l + 1, ln["skiri"]))
    return before, lessons, log


def as_rows(conn, lessons):
    templates = dict(conn.execute("select lesson_number, template_ids from lessons"))
    return {x["lesson_number"]: {"skiri_title": x["skiri_title"], "english_title": x["english_title"],
                                 "page_start": x["page_start"], "page_end": x["page_end"], "dialogues": x["dialogues"],
                                 "grammar_notes": x["grammar_notes"],
                                 "templates": json.loads(templates[x["lesson_number"]]) if templates[x["lesson_number"]] else []}
            for x in lessons}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: list them only)")
    ap.add_argument("--check", action="store_true", help="exit 0 if every dialogue line is a pair")
    ap.add_argument("--show", action="store_true", help="print every dialogue as it will stand")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    doc = fitz.open(str(lt.PDF))
    before, after, log = plan(conn, doc)
    changed = [(a["lesson_number"], col) for b, a in zip(before, after) for col in ("dialogues", "grammar_notes") if b[col] != a[col]]
    data, file_diffs = fl.file_differences(as_rows(conn, after))
    count = lambda ls: sum(len(d.get("lines", [])) for x in ls for d in x["dialogues"])
    conn.close()

    if args.check:
        problems = list(log["problems"]) + list(log["still English"])
        if changed:
            problems.append("%d values of the lessons table would change" % len(changed))
        if file_diffs:
            problems.append("extracted_data/lessons.json differs from the table in %d values" % len(file_diffs))
        if problems:
            out("NOT in step: " + "; ".join(problems))
            return 1
        out("dialogues paired: %d lines in %d dialogues, each a Pawnee line; %d have their English beside them, %d are "
            "printed without one (a second dialect's form, an alternative in brackets, a breakdown line)" % (
                count(after), sum(len(x["dialogues"]) for x in after), count(after) - len(log["no English"]), len(log["no English"])))
        return 0

    header = ["pair_lesson_dialogues — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "dialogue lines: %d before, %d after" % (count(before), count(after)),
              "English taken from the row of the page: %d; the same English dropped where it stood as a line of its own: %d" % (
                  len(log["from the row"]), len(log["dropped"])),
              "English lines made the English of the Pawnee line before them: %d; joined to the English before them: %d" % (
                  len(log["attached"]), len(log["continued"])),
              "lines cut into Pawnee and English: %d; Pawnee lines joined to the line before: %d" % (len(log["split"]), len(log["joined"])),
              "sections of the notes moved out of a dialogue: %d" % len(log["moved"]),
              "values of the lessons table that change: %d; of extracted_data/lessons.json: %d" % (len(changed), len(file_diffs)),
              "Pawnee lines printed without English of their own: %d; problems: %d" % (
                  len(log["no English"]), len(log["problems"]) + len(log["still English"]))]
    body = ["", "== 1. English from the row of the page (where; Pawnee | English)"]
    body += ["  %s; %s | %s" % x for x in log["from the row"]] or ["  none"]
    body += ["", "== 1b. The same English, stored as a line of its own, dropped"]
    body += ["  %s; %s" % x for x in log["dropped"]] or ["  none"]
    body += ["", "== 2. Lines cut into Pawnee and English (where; before; after)"]
    body += ["  %s; %s  ->  %s" % x for x in log["split"]] or ["  none"]
    body += ["", "== 3. English lines given to the Pawnee line before them (where; Pawnee; English)"]
    body += ["  %s; %s | %s" % x for x in log["attached"] + log["continued"]] or ["  none"]
    body += ["", "== 4. Pawnee lines joined to the line before (where; the line now)"]
    body += ["  %s; %s" % x for x in log["joined"]] or ["  none"]
    body += ["", "== 5. Sections of the notes moved out of a dialogue (lesson, dialogue, heading, lines)"]
    body += ["  L%d dialogue %d: %s (%d lines), now the first of the lesson's notes" % (n, d + 1, h, k) for n, d, h, k in log["moved"]] or ["  none"]
    body += ["", "== Printed without English of their own (lesson, dialogue, line: Pawnee)"]
    body += ["  L%d dialogue %d line %d: %s" % x for x in log["no English"]] or ["  none"]
    body += ["", "== English of the page row that was not stored before"]
    body += ["  L%d %s" % x for x in log["page only"]] or ["  none"]
    body += ["", "== Problems"] + (["  " + p for p in log["problems"] + log["still English"]] or ["  none"])
    if args.show:
        body += ["", "== Every dialogue as it will stand"]
        for x in after:
            for d, dia in enumerate(x["dialogues"]):
                for ln in dia["lines"]:
                    body.append("  L%-2d %d  %-46s | %s" % (x["lesson_number"], d + 1, ln["skiri"], ln["english"]))

    if not args.apply:
        out("\n".join(header + body))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0
    if log["problems"] or log["still English"]:
        out("\n".join(header + body))
        out("NOT applied: see the problems above")
        return 1

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_dialogues.db" % stamp))
    conn = sqlite3.connect(str(DB))
    by_no = {x["lesson_number"]: x for x in after}
    for n, col in changed:
        conn.execute("update lessons set %s = ? where lesson_number = ?" % col, (json.dumps(by_no[n][col], ensure_ascii=False), n))
    conn.commit()
    rows = as_rows(conn, after)
    conn.close()
    if file_diffs:
        fl.write_copy(data, rows)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    header += ["", "written: %d values of the lessons table, %d in extracted_data/lessons.json" % (len(changed), len(file_diffs)),
               "backup: OneDrive/pari_pakuru_backups/skiri_pawnee_backup_%s_dialogues.db" % stamp]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
