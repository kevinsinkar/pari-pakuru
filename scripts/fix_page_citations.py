#!/usr/bin/env python3
"""
Make every page citation a page of the printed book (2026-11-14)
================================================================

`lexical_entries.page_number` held two things. For 733 entries it was the
page of the book; for 3,511 it was the number of the PDF file the entry was
parsed from, which is 348 less. The site and the cards print the value as
"Parks Dictionary, p. N", so most citations led to the wrong page.

This script sets the column to the book page for every Parks entry.

Where the page comes from
    The source-fidelity audit pairs every stored entry with the printed entry
    it was parsed from (scripts/source_audit/s2e_compare.py). The page is the
    one on which that printed entry's headword stands. An entry that runs over
    a page break is cited by the page it starts on.
    The step from file number to book page is not assumed: the script reads
    the page number printed at the head of each of the 181 pages from the PDF
    text layer and stops if any of them is not the file number plus 348.

What it writes (with --apply)
    skiri_pawnee.db                              lexical_entries.page_number
    Dictionary Data/skiri_to_english_respelled.json   entry_metadata.page_number
    curriculum/flashcard_sets.json               the page shown on each frozen card
    reports/page_citations_report.txt            the record (a later run is added below, never written over)

What it leaves alone
    Entry ids. `SK-paaqatuq-p112-2231` keeps the file number it was made with:
    ids are keys in saved study progress, in the reports and in git history.
    english_index.page_number and cross_references.source_page. They belong to
    the English-to-Skiri section and hold an early import (open item 32); the
    printed page there is the file number plus 60.
    blue_book_attestations.page_number: Blue Book pages, a different book.

    python scripts/fix_page_citations.py            # dry run: prints what it would do, writes nothing
    python scripts/fix_page_citations.py --apply    # backs up, then writes
    python scripts/fix_page_citations.py --check    # exit code 0 when every citation is the book page

After --apply: rebuild the weekly flashcards and the site, then
`python scripts/db_dump.py --write`.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import s2e_compare  # noqa: E402
import state  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
FROZEN = ROOT / "curriculum" / "flashcard_sets.json"
REPORT = ROOT / "reports" / "page_citations_report.txt"
OFFSET = 348                      # book page = file number + 348, proved below for every page
FIRST, LAST = 349, 529            # the Skiri-to-English section of the book
BODY_TOP, BODY_BOTTOM = 56.0, 652.0


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.flush()


def printed_folios():
    """{file number: page number printed on that page}, from the text layer's running heads."""
    folios = {}
    for f in sorted((state.WORK / "textlayer").glob("s2e_*.json")):
        page = json.loads(f.read_text(encoding="utf-8"))
        digits = [int(s["t"].strip()) for s in page["spans"]
                  if not (BODY_TOP < s["b"][1] < BODY_BOTTOM) and s["t"].strip().isdigit()]
        folios[page["unit"]] = digits
    return folios


def plan(db_path):
    folios = printed_folios()
    wrong = {n: d for n, d in folios.items() if d != [n + OFFSET]}
    if len(folios) != LAST - FIRST + 1 or wrong:
        raise SystemExit("stop: the printed page number is not the file number plus %d on every page: %s"
                         % (OFFSET, dict(list(wrong.items())[:8]) or "%d pages decoded" % len(folios)))
    diffs, pair_rows, summary, by_kind = s2e_compare.compare(str(db_path))
    file_of = {r["entry_id"]: r["page_file"] for r in pair_rows}
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("select entry_id, headword, page_number, coalesce(source, 'parks') from lexical_entries "
                        "order by entry_id").fetchall()
    conn.close()
    changes, tally, odd = [], Counter(), []
    for entry_id, headword, stored, source in rows:
        if source != "parks":
            tally["Blue Book-only entry, no dictionary page" if stored is None else "Blue Book-only entry with a page (left)"] += 1
            continue
        if entry_id not in file_of:
            tally["not paired with a printed entry (left)"] += 1
            odd.append((entry_id, headword, stored, None))
            continue
        book = file_of[entry_id] + OFFSET
        if stored == book:
            tally["already the book page"] += 1
        elif stored == file_of[entry_id]:
            tally["file number, set to the book page"] += 1
            changes.append((entry_id, headword, stored, book))
        else:
            tally["neither the file number nor the book page, set to the book page"] += 1
            odd.append((entry_id, headword, stored, book))
            changes.append((entry_id, headword, stored, book))
    return changes, tally, odd, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the database, the JSON, the frozen cards and the report")
    ap.add_argument("--check", action="store_true", help="change nothing; exit 0 when every Parks entry cites its book page")
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()

    changes, tally, odd, summary = plan(args.db)
    header = ["Page citations set to the page of the printed book",
              "run: %s%s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "" if args.apply else " (dry run)"),
              "",
              "printed page number read from the head of each page: file number + %d on all %d pages" % (OFFSET, LAST - FIRST + 1),
              "entries paired with a printed entry: %d of %d Parks entries" % (summary["paired"], summary["stored_entries"]),
              ""]
    header += ["%6d  %s" % (n, k) for k, n in sorted(tally.items(), key=lambda kv: -kv[1])]
    if odd:
        header += ["", "entries that fit neither convention or could not be paired:"]
        header += ["   %s  %s  stored %s -> %s" % o for o in odd]

    if args.check:
        out("\n".join(header))
        left = len(changes) + sum(1 for o in odd if o[3] is None)
        out("")
        out("check: %s" % ("every Parks entry cites its book page" if left == 0 else "%d entries do not cite their book page" % left))
        sys.exit(0 if left == 0 else 1)

    # the JSON and the frozen cards follow the database
    book_of = {eid: new for eid, hw, old, new in changes}
    data = json.loads(S2E_JSON.read_text(encoding="utf-8"))
    conn = sqlite3.connect(args.db)
    in_db = {r[0] for r in conn.execute("select entry_id from lexical_entries")}
    conn.close()
    json_changes, json_rule = [], []
    for e in data:
        meta = e.get("entry_metadata") or {}
        page, eid = meta.get("page_number"), e.get("entry_id")
        if eid in book_of and page != book_of[eid]:
            json_changes.append((e, book_of[eid]))
        elif eid not in in_db and isinstance(page, int) and page <= LAST - FIRST + 1:
            # an entry the database does not hold (a duplicate of the parse, or one stored under another id):
            # its number is a file number like the others, so the same step applies; not confirmed by pairing
            json_changes.append((e, page + OFFSET))
            json_rule.append((eid, e.get("headword"), page, page + OFFSET))
    sets = json.loads(FROZEN.read_text(encoding="utf-8"))
    cards = []

    def walk(o):
        if isinstance(o, dict):
            if "page_number" in o and o.get("entry_id") in book_of and o["page_number"] != book_of[o["entry_id"]]:
                cards.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(sets)

    header += ["",
               "database: %d entries to change" % len(changes),
               "%s: %d entries to change (%d of them not in the database, changed by the same step: file number + %d)"
               % (S2E_JSON.name, len(json_changes), len(json_rule), OFFSET),
               "%s: %d cards to change" % (FROZEN.name, len(cards))]
    body = ["", "every change (entry id, headword, old -> new):"]
    body += ["   %s  %s  %s -> %s" % c for c in changes]
    if json_rule:
        body += ["", "JSON entries not in the database (old -> new):"]
        body += ["   %s  %s  %s -> %s" % c for c in json_rule]

    if not args.apply:
        out("\n".join(header))
        out("\n".join(body[:14]))
        out("   ...")
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return
    if not changes and not json_changes and not cards:
        out("\n".join(header))
        out("")
        out("nothing to change; nothing written")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.db, backups / ("skiri_pawnee_backup_%s_pages.db" % stamp))
    for f in (S2E_JSON, FROZEN):
        shutil.copy2(f, backups / ("%s_backup_%s%s" % (f.stem, stamp, f.suffix)))
    conn = sqlite3.connect(args.db)
    conn.executemany("update lexical_entries set page_number=? where entry_id=? and page_number is ?",
                     [(new, eid, old) for eid, hw, old, new in changes])
    conn.commit()
    conn.close()
    for e, new in json_changes:
        e.setdefault("entry_metadata", {})["page_number"] = new
    S2E_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in cards:
        c["page_number"] = book_of[c["entry_id"]]
    FROZEN.write_text(json.dumps(sets, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    header += ["", "backups: OneDrive/pari_pakuru_backups (stamp %s)" % stamp]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("")
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
