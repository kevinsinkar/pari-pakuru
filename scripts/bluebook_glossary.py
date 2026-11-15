#!/usr/bin/env python3
"""
The Blue Book's glossary, item by item (2026-11-14)
===================================================

The last eight pages of Pari Pakuru' (book pages 95 to 102; pages 123 to 130
of the PDF) are a glossary: an alphabetical list of English words, each with
the page or pages of the book on which its Pawnee equivalent can be found. It
prints no Pawnee. Until now it was not itemised (open item 28).

    python scripts/bluebook_glossary.py            # read it, check it, report; writes nothing
    python scripts/bluebook_glossary.py --write    # also writes extracted_data/blue_book_glossary.json
    python scripts/bluebook_glossary.py --list     # the rows that are not confirmed, in full

Reading. The scan has a text layer made by OCR. Its words are taken with
their place on the page, put into lines and two columns, and each line is
cut into the English term and its page numbers. English words and figures are
what OCR reads well; accents are not at stake here.

Checking. A page number is the part OCR can get wrong unnoticed, so every
reference is checked against the book itself: the English term has to occur
in the text of the page it points to (book page + 28 = page of the PDF). A
reference that passes is confirmed by two independent places of the scan. One
that does not is listed; it may be an OCR slip in the number, or the lesson
may use another English word than the glossary.

Linking. For every confirmed reference the Pawnee forms the database holds
for that page with that English (table blue_book_attestations, whose forms
were read from the scan in November 2026) are listed beside it. The forms
are copied from that table; none is made here.

Reads the PDF and the database. Changes neither.
"""
import argparse
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "pari pakuru" / "Blue Book - Pari Pakuru.pdf"
DB = ROOT / "skiri_pawnee.db"
OUT = ROOT / "extracted_data" / "blue_book_glossary.json"
FIRST, LAST, OFFSET = 123, 130, 28            # pages of the PDF; book page = PDF page - 28
REF = re.compile(r"^\d{1,3}(?:[,\-–]\d{1,3})*[,.;:]*$")
ROMAN = re.compile(r"^(?=[ivx])x{0,2}(?:ix|iv|v?i{0,3})[,.;:]*$")      # a page of the front matter: iii, v, xi
STOP = {"the", "a", "an", "of", "to", "in", "on", "it", "is", "be", "at", "and", "or", "for", "one's", "you", "your", "adj", "past", "future"}
# Rows the OCR text layer does not give whole, read from the page image by the session that wrote this script
# (one reading): {term: (page references as printed, what was seen)}
BY_EYE = {
    "Amen": ("iii", "the page prints Amen with the roman page number iii; the text layer has the word and no number"),
}


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def lines_of(page, top):
    """Lines of one page as lists of (x, word), left column then right, each top to bottom."""
    words = [w for w in page.get_text("words") if w[1] > top]
    # the two columns are told apart by the left margin of the right one
    # (the pages are not set at the same place on the sheet)
    starts = collections.Counter(int(w[0] // 2) * 2 for w in words if 185 <= w[0] <= 275)
    margin = None
    if starts:                                     # the left margin of the right column: where most words begin
        best = max(starts, key=lambda x: starts[x] + starts.get(x + 2, 0))
        if starts[best] + starts.get(best + 2, 0) >= 12:
            margin = best
    mid = (margin - 5) if margin is not None else page.rect.width / 2.0
    cols = {0: [], 1: []}
    for w in words:
        cols[0 if w[0] < mid else 1].append(w)
    result = []
    for c in (0, 1):
        rows, last_y = [], None
        for w in sorted(cols[c], key=lambda w: (round(w[1]), w[0])):
            if last_y is None or abs(w[1] - last_y) > 4.5:
                rows.append([])
                last_y = w[1]
            rows[-1].append((w[0], w[4]))
        for r in rows:
            r.sort()
            result.append((c, r))
    return result


def read_glossary(doc):
    rows = []
    for pno in range(FIRST, LAST + 1):
        page = doc[pno - 1]
        top = 0.0
        if pno == FIRST:                           # the introduction stands above the first letter
            a = [w for w in page.get_text("words") if w[4] == "A" and w[1] > 200]
            top = a[0][1] - 2 if a else 300.0
        base = {}
        for col, line in lines_of(page, top):
            toks = [(x, t) for x, t in line if re.search(r"[A-Za-z0-9]", t)]
            if not toks:
                continue
            if len(toks) == 1 and re.fullmatch(r"[A-Z]", toks[0][1]):
                continue                           # the letter that heads a section
            if len(toks) == 1 and toks[0][1].isdigit() and toks[0][0] > 150 and not rows:
                continue
            term, refs = [], []
            for n, (x, t) in enumerate(toks):
                rest_are_refs = all(REF.match(u) or ROMAN.match(u) for _, u in toks[n:])
                if term and rest_are_refs and (REF.match(t) or ROMAN.match(t)):
                    refs.append(t)
                else:
                    term.append((x, t))
            if not term:
                continue
            if len(term) == 1 and term[0][1].isdigit():
                continue                           # the page's own number at the foot
            x0 = term[0][0]
            base[col] = min(base.get(col, x0), x0)
            rows.append({"glossary_page": pno - OFFSET, "column": "left" if col == 0 else "right", "x": x0, "col_key": (pno, col),
                         "english": " ".join(t for _, t in term).strip(" .:"), "refs": " ".join(refs)})
        for r in rows:
            if r["col_key"][0] == pno and "indent" not in r:
                r["indent"] = r["x"] - base[r["col_key"][1]] > 6
    return rows


def pages_of(refs):
    """'28, 32' -> [28, 32]; '76-78' -> [76, 77, 78]; anything else is kept as printed."""
    nums, other = [], []
    for part in re.split(r"[,\s]+", refs.strip()):
        part = part.strip(".;:")
        if not part:
            continue
        m = re.fullmatch(r"(\d{1,3})(?:[-–](\d{1,3}))?", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            nums += list(range(a, b + 1)) if a <= b <= a + 12 else [a]
        else:
            other.append(part)
    return nums, other


def keys_of(term):
    words = re.findall(r"[a-z']+", re.sub(r"\([^)]*\)", " ", term.lower()))
    keys = [w.strip("'") for w in words if w.strip("'") not in STOP and len(w.strip("'")) >= 2]
    return keys or [w.strip("'") for w in words]


def stems(word):
    yield word
    for end in ("ing", "ed", "es", "s", "y", "e"):
        if word.endswith(end) and len(word) - len(end) >= 3:
            yield word[:-len(end)]


def occurs(keys, text):
    return all(any(re.search(r"\b%s" % re.escape(s), text) for s in stems(k)) for k in keys)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write extracted_data/blue_book_glossary.json")
    ap.add_argument("--list", action="store_true", help="print the rows that are not confirmed")
    args = ap.parse_args()
    doc = fitz.open(str(PDF))
    text = {n: doc[n - 1].get_text().lower() for n in range(1, len(doc) + 1)}
    conn = sqlite3.connect("file:%s?mode=ro" % DB.resolve().as_posix(), uri=True)
    forms = collections.defaultdict(list)
    for form, english, page, entry in conn.execute("select bb_skiri_form, bb_english, page_number, entry_id from blue_book_attestations "
                                                    "where page_number is not null order by id"):
        forms[page].append((form, english or "", entry))
    conn.close()
    rows = read_glossary(doc)
    entries, tally, open_rows = [], collections.Counter(), []
    parent = None
    for r in rows:
        refs = r["refs"]
        note = None
        if not refs and r["english"] in BY_EYE:
            refs, note = BY_EYE[r["english"]][0], "read from the page image: " + BY_EYE[r["english"]][1]
        if not r["indent"]:
            parent = r["english"]
        nums, other = pages_of(refs)
        keys = keys_of(r["english"])
        e = {"english": r["english"], "glossary_page": r["glossary_page"], "column": r["column"], "page_references_as_printed": refs,
             "pages": []}
        if r["indent"] and parent and parent != r["english"]:
            e["under"] = parent
        if note:
            e["note"] = note
        for pg in other:
            e["pages"].append({"page": pg, "checked": "not a page of the lessons (front matter)"})
            tally["references to the front matter"] += 1
        for pg in nums:
            pdf_page = pg + OFFSET
            here = occurs(keys, text.get(pdf_page, ""))
            found = [{"form": f, "english": en, **({"entry_id": eid} if eid else {})} for f, en, eid in forms.get(pdf_page, [])
                     if occurs(keys, en.lower())]
            item = {"page": pg, "checked": "the English is on that page" if here else "the English was not found on that page"}
            if found:
                item["pawnee_forms_stored_for_that_page"] = found
            e["pages"].append(item)
            tally["references"] += 1
            tally["references confirmed by the page they point to" if here else "references not confirmed"] += 1
            if found:
                tally["references with a stored Pawnee form"] += 1
            if not here:
                open_rows.append("%s (glossary p. %d): p. %d  [looked for %s]" % (r["english"], r["glossary_page"], pg, ", ".join(keys)))
        if not nums and not other:
            tally["rows without a page number"] += 1
            open_rows.append("%s (glossary p. %d): no page number read" % (r["english"], r["glossary_page"]))
        entries.append(e)
    out("glossary rows: %d on book pages %d-%d" % (len(entries), FIRST - OFFSET, LAST - OFFSET))
    for k, v in tally.most_common():
        out("  %-52s %d" % (k, v))
    out("  rows by page: %s" % dict(sorted(collections.Counter(e["glossary_page"] for e in entries).items())))
    if args.list:
        out("")
        out("Not confirmed (%d):" % len(open_rows))
        for line in open_rows:
            out("  " + line)
    if args.write:
        doc_out = {"_about": {
            "source": "Pawnee Cultural Retention Committee, Pari Pakuru' (1979), Glossary, book pages %d-%d (pages %d-%d of the PDF)" % (
                FIRST - OFFSET, LAST - OFFSET, FIRST, LAST),
            "what": "The glossary item by item: each English term with the pages of the book it points to. The glossary prints no "
                    "Pawnee. Read from the scan's OCR text layer by scripts/bluebook_glossary.py.",
            "checked": "Every page reference was looked up: the English term has to occur in the text of the page it points to. "
                       "\"pawnee_forms_stored_for_that_page\" are the forms the database holds for that page with that English "
                       "(table blue_book_attestations, read from the scan); they are copied, not made.",
            "page_numbers": "Book pages, as the glossary prints them. The PDF page is the book page plus %d." % OFFSET,
            "counts": dict(tally), "rows": len(entries)}, "entries": entries}
        OUT.write_text(json.dumps(doc_out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        out("written: %s" % OUT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
