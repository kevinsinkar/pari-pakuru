#!/usr/bin/env python3
"""
Stage 2a: cut the Skiri-to-English text layer into entries
==========================================================

Reads the decoded pages (work/textlayer/s2e_NNN.json) as one stream, in
reading order: page by page, left column then right column, top to bottom,
with running heads and page numbers left out. An entry starts at a headword:
a span in the bold Skiri font at headword size (10.1) that begins a line at
the column's left margin. Everything up to the next headword belongs to it,
across column and page breaks.

    python scripts/source_audit/s2e_segment.py     # writes work/s2e_printed_entries.jsonl

Each entry keeps its spans (font family, style, size, text as printed, page,
position, and whether the span begins a new line), so that later steps can
tell Skiri from English and can cut the entry out of the page image.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

TEXT = state.WORK / "textlayer"
OUT = state.WORK / "s2e_printed_entries.jsonl"
BODY_TOP, BODY_BOTTOM = 56.0, 652.0
HEAD_SIZE = 10.1


def page_lines(page):
    """Body lines of one page in reading order. A line is a list of spans."""
    # size 12 is the letter that heads each alphabetical section (A, C, H ...): not part of any entry
    spans = [s for s in page["spans"] if BODY_TOP < s["b"][1] < BODY_BOTTOM and s["t"] != "" and s["sz"] < 11.5]
    if not spans:
        return [], None
    left = min(s["b"][0] for s in spans)
    boundary = left + 190.0
    lines = {}
    for s in spans:
        lines.setdefault((s["blk"], s["ln"]), []).append(s)
    raw = []
    for key, line in lines.items():
        line.sort(key=lambda s: s["b"][0])
        x0 = line[0]["b"][0]
        bottom = max(s["b"][3] for s in line)
        raw.append((0 if x0 < boundary else 1, bottom, x0, line))
    # PyMuPDF often returns one printed row as several "lines" (a headword, its phonetic form and its
    # class are in different fonts and sizes, and their boxes end a point apart). Put lines whose
    # bottoms are within 3.5 points of each other on one row, then read rows top to bottom and each
    # row left to right. Rows are 10 points apart.
    ordered = []
    for col in (0, 1):
        col_lines = sorted((t for t in raw if t[0] == col), key=lambda t: t[1])
        rows, row_bottom = [], None
        for t in col_lines:
            if row_bottom is None or t[1] - row_bottom > 3.5:
                rows.append([])
                row_bottom = t[1]
            rows[-1].append(t)
        for row in rows:
            row.sort(key=lambda t: t[2])
            merged = []
            for t in row:
                merged += t[3]
            ordered.append((col, row[0][1], row[0][2], merged))
    return ordered, left


def is_headword_start(line, col, left):
    first = next((s for s in line if s["t"].strip()), None)
    if first is None:
        return False
    margin = left if col == 0 else left + 207.0
    at_margin = abs(first["b"][0] - margin) < 3.0
    if not at_margin:
        return False
    if first["f"] == "PlainsArial" and first["st"] == "Bold" and abs(first["sz"] - HEAD_SIZE) < 0.3:
        return True
    # the null headword: Ø in another font, at headword size, at the margin
    return first["f"] == "LucidaSansUnicode" and first["sz"] >= 10.0 and first["t"].strip().startswith("Ø")


def main():
    files = sorted(TEXT.glob("s2e_*.json"))
    entries, current = [], None
    front = []                    # text before the first headword of the section
    for f in files:
        page = json.loads(f.read_text(encoding="utf-8"))
        ordered, left = page_lines(page)
        for col, bottom, x0, line in ordered:
            if is_headword_start(line, col, left):
                current = {"seq": len(entries) + 1, "page": page["unit"], "col": col, "y": round(line[0]["b"][1], 1), "spans": []}
                entries.append(current)
            target = current["spans"] if current is not None else front
            for i, s in enumerate(line):
                target.append({"f": s["f"], "st": s["st"], "sz": s["sz"], "t": s["t"], "p": page["unit"], "b": s["b"],
                               "nl": 1 if i == 0 else 0})
    for e in entries:
        head = []
        for s in e["spans"]:
            if s["nl"] and head and not (s["st"] == "Bold" and abs(s["sz"] - HEAD_SIZE) < 0.3):
                break
            if (s["f"] == "PlainsArial" and s["st"] == "Bold" and abs(s["sz"] - HEAD_SIZE) < 0.3) or \
               (s["f"] == "LucidaSansUnicode" and s["sz"] >= 10.0):
                head.append(s["t"])
            elif s["t"].strip() == "":
                continue
            else:
                break
        e["head"] = " ".join("".join(head).split())
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    state.out("pages: %d; printed entries: %d; spans before the first headword: %d" % (len(files), len(entries), len(front)))
    state.out("first: %s" % " | ".join(e["head"] for e in entries[:12]))
    state.out("last:  %s" % " | ".join(e["head"] for e in entries[-6:]))


if __name__ == "__main__":
    main()
