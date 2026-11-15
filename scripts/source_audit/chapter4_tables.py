#!/usr/bin/env python3
"""
The tables of the grammar chapter, as printed (2026-11-14)
==========================================================

extracted_data/grammatical_overview.json holds the tables of chapter 4 as an
extraction of March 2026 rebuilt them: cells merged, rows regrouped. Table 17
was put back by hand on 2026-11-14 (chapter4_second_reading.py). This script
does the same for all of them without another reading: the two blind readings
of the chapter (blind_readings/chapter4_part*.json and
chapter4_second_part*.json) each wrote every table down row by row, tile by
tile, and they saw different cuts of the page.

    python scripts/source_audit/chapter4_tables.py           # put the tables together, compare the readings
    python scripts/source_audit/chapter4_tables.py --write   # also write extracted_data/grammatical_overview_tables.json
    python scripts/source_audit/chapter4_tables.py --show 11 # one table, both readings side by side

Putting a table together. A reader wrote one piece per tile. Pieces belong to
one table when they carry its number, or carry no title and follow it. Tiles
overlap by a line, so the row at a cut can be written twice, or once whole
and once cut short; of two such rows the fuller one is kept.

Comparing. The two readers divided rows differently: one wrote a row of the
table as one row, the other wrote every printed line as a row, so that a cell
of three lines became three rows. That is a difference of writing down, not
of reading, and it is told apart from a difference in what is printed:

    the same in both readings          the same rows with the same cells
    the same text, rows divided        every column reads the same from top to bottom in both
      differently                      readings (spaces aside). Stored with the rows of the reading
                                       that kept whole rows, and with the other reading beside it,
                                       because which row a cell printed between two rows belongs
                                       to is exactly what a person may want to check
    the readings differ                a column reads differently: both readings are stored and the
                                       columns that differ are listed; nothing is chosen

Reads the two readings; writes one file. Changes nothing else.
"""
import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

READINGS = state.OUT / "blind_readings"
OUT = state.ROOT / "extracted_data" / "grammatical_overview_tables.json"
NUMBER = re.compile(r"^\s*Table\s+(\d+)\b", re.I)
FIRST_BOOK_PAGE = 29


def norm(cell):
    cell = unicodedata.normalize("NFC", cell or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    cell = re.sub(r"\s+", " ", cell).strip()
    return re.sub(r"\s*([+/])\s*", r" \1 ", cell).replace(" / ", "/") if "+" in cell else cell


def fuller(a, b):
    """Is row b row a written more fully (every cell of a begins the same cell of b)?"""
    if len(a) != len(b):
        return False
    return all(y.startswith(x) for x, y in zip(a, b)) and a != b


def tail_of(a, b):
    """Is row b the end of row a (every cell of b ends the same cell of a, or is empty)?"""
    if len(a) != len(b) or not any(b):
        return False
    return all((not y) or x.endswith(y) for x, y in zip(a, b)) and a != b


def tile_key(label):
    m = re.match(r"p(\d+)-b(\d+)", label)
    return int(m.group(1)), int(m.group(2))


def assemble(pattern):
    """{table number: {"title", "pages", "rows"}} from one reading."""
    tiles = {}
    for f in sorted(READINGS.glob(pattern)):
        tiles.update(json.loads(f.read_text(encoding="utf-8")))
    tables, current = collections.OrderedDict(), None
    for label in sorted(tiles, key=tile_key):
        page = tile_key(label)[0]
        for piece in tiles[label].get("tables") or []:
            title = re.sub(r"\s+", " ", piece.get("title") or "").strip()
            title = re.sub(r"\s*\((?:continued|title not)[^)]*\)\s*$", "", title, flags=re.I)     # a reader's own note
            m = NUMBER.match(title)
            if m:
                current = int(m.group(1))
            if current is None:
                continue
            t = tables.setdefault(current, {"title": "", "pages": [], "rows": []})
            if m and len(title) > len(t["title"]):
                t["title"] = title
            if page + FIRST_BOOK_PAGE - 1 not in t["pages"]:
                t["pages"].append(page + FIRST_BOOK_PAGE - 1)
            for row in piece.get("rows") or []:
                row = [norm(c) for c in row]
                if not any(row):
                    continue
                if t["rows"]:
                    last = t["rows"][-1]
                    if row == last or tail_of(last, row):
                        continue
                    if fuller(last, row):
                        t["rows"][-1] = row
                        continue
                t["rows"].append(row)
    return tables


def squeeze(text):
    return re.sub(r"\s+", "", text)


def columns(rows):
    """Each column read from top to bottom as one string; None when the rows have different numbers of cells."""
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        return None
    return [" ".join(r[c] for r in rows if r[c]) for c in range(widths.pop())]


def compare(a, b):
    """("same" | "rows" | "differ", [(column, text in a, text in b)])."""
    if len(a) == len(b) and all(len(x) == len(y) and all(squeeze(p) == squeeze(q) for p, q in zip(x, y)) for x, y in zip(a, b)):
        return "same", []
    ca, cb = columns(a), columns(b)
    if ca is None or cb is None or len(ca) != len(cb):
        # the readers did not give every row the same number of cells: compare the whole table read row by row
        ta, tb = " ".join(c for r in a for c in r if c), " ".join(c for r in b for c in r if c)
        return ("rows", []) if squeeze(ta) == squeeze(tb) else ("differ", [("whole table", ta, tb)])
    d = [(n, x, y) for n, (x, y) in enumerate(zip(ca, cb), 1) if squeeze(x) != squeeze(y)]
    return ("differ", d) if d else ("rows", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write extracted_data/grammatical_overview_tables.json")
    ap.add_argument("--show", type=int, metavar="N", help="print table N in both readings")
    args = ap.parse_args()
    first, second = assemble("chapter4_part*.json"), assemble("chapter4_second_part*.json")
    if args.show:
        for name, t in (("first reading", first.get(args.show)), ("second reading", second.get(args.show))):
            state.out("--- %s: %s" % (name, t and t["title"]))
            for row in (t or {}).get("rows", []):
                state.out("   " + " | ".join(row))
        return
    stored, same, rows_only, differ = [], 0, 0, 0
    for n in sorted(set(first) | set(second)):
        a, b = first.get(n), second.get(n)
        if not a or not b:
            only = "first" if a else "second"
            t = a or b
            stored.append({"number": n, "title": t["title"], "book_pages": t["pages"], "status": "in the %s reading only" % only, "rows": t["rows"]})
            differ += 1
            state.out("Table %d: in the %s reading only (%d rows)" % (n, only, len(t["rows"])))
            continue
        verdict, d = compare(a["rows"], b["rows"])
        title = b["title"] if len(b["title"]) >= len(a["title"]) else a["title"]
        pages = sorted(set(a["pages"]) | set(b["pages"]))
        whole, lines = (a, b) if len(a["rows"]) <= len(b["rows"]) else (b, a)      # the reading that kept whole rows
        if verdict == "same":
            same += 1
            stored.append({"number": n, "title": title, "book_pages": pages, "status": "the same in both readings", "rows": b["rows"]})
            state.out("Table %d: the same in both readings (%d rows)  %s" % (n, len(b["rows"]), title))
        elif verdict == "rows":
            rows_only += 1
            stored.append({"number": n, "title": title, "book_pages": pages, "status": "the same text, rows divided differently",
                           "rows": whole["rows"], "rows_as_the_other_reader_divided_them": lines["rows"]})
            state.out("Table %d: the same text in both readings, rows divided differently (%d and %d rows)  %s" % (
                n, len(a["rows"]), len(b["rows"]), title))
        else:
            differ += 1
            stored.append({"number": n, "title": title, "book_pages": pages, "status": "the readings differ",
                           "rows_first_reading": a["rows"], "rows_second_reading": b["rows"],
                           "differences": [{"column": c, "first": x, "second": y} for c, x, y in d]})
            state.out("Table %d: the readings differ in %d column(s)  %s" % (n, len(d), title))
            for c, x, y in d[:6]:
                import difflib
                sm = difflib.SequenceMatcher(None, x.split(), y.split(), autojunk=False)
                for tag, i0, i1, j0, j1 in sm.get_opcodes():
                    if tag != "equal":
                        state.out("     column %s: %r | %r" % (c, " ".join(x.split()[max(0, i0 - 2):i1 + 2]), " ".join(y.split()[max(0, j0 - 2):j1 + 2])))
    state.out("%d tables: %d the same in both readings, %d the same text with rows divided differently, %d where the readings differ" % (
        len(stored), same, rows_only, differ))
    if args.write:
        doc = {"_about": {
            "source": "Parks and Pratt, A Dictionary of Skiri Pawnee (2008), chapter 4, \"Grammatical Overview\", pp. 29-51",
            "what": "The tables of the chapter as printed, row by row, put together from the two blind readings of the page images "
                    "(reports/source_audit_2026-11/blind_readings/chapter4_part*.json and chapter4_second_part*.json) by "
                    "scripts/source_audit/chapter4_tables.py. No third reading was made.",
            "status": "\"the same in both readings\": both readers wrote the same rows and cells. \"the same text, rows divided "
                      "differently\": every column reads the same from top to bottom in both; one reader wrote each printed line "
                      "as a row, and both divisions are given. \"the readings differ\": the table is given in both readings with "
                      "the columns that differ; neither is chosen.",
            "supersedes": "The tables inside extracted_data/grammatical_overview.json, which an extraction of March 2026 rebuilt "
                          "with merged cells. Use this file for a table; that file for the chapter's examples.",
            "tables": len(stored), "the_same_in_both_readings": same, "the_same_text_rows_divided_differently": rows_only,
            "the_readings_differ": differ}, "tables": stored}
        OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        state.out("written: %s" % OUT.relative_to(state.ROOT).as_posix())


if __name__ == "__main__":
    main()
