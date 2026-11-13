#!/usr/bin/env python3
"""
Stage 1b: contact sheets of every stand-in character, cut from the printed pages
================================================================================

For each (font family, character) pair in work/char_inventory.json, takes
occurrences spread over the book and places a magnified crop of each on a
sheet: the printed word, with a red tick under the character in question.

Rows are labelled with a random id only (K01, K02 ...), so that whoever reads
the sheet writes down what is printed without knowing which code it is or what
the current table says. The key is in work/char_sheets/key.json; compare.py
joins the readings with it afterwards.

    python scripts/source_audit/char_sheets.py

The crops are placed as vector graphics (PyMuPDF show_pdf_page with a clip
rectangle), so they are as sharp as the PDF itself at any magnification.
"""
import json
import random
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import textlayer as tl  # noqa: E402

SHEETS = state.WORK / "char_sheets"
SCALE = 7.0                 # magnification of the crop
HALF_WIDTH = 20.0           # points of page to either side of the character
COLS, ROWS = 4, 13
LABEL_W, GAP = 74, 10

# how many occurrences to look at
MANY = {("PAdothyphen", c): 12 for c in "à‡æÑŠ÷"}
MANY.update({("PlainsArial", c): 8 for c in "ÑóæÙ÷Ýí?"})
MANY.update({("TruteauGaramond", c): 8 for c in "®íá"})
MANY[("LucidaSansUnicode", "?")] = 8
ALL_IF_AT_MOST = 9
DEFAULT = 4


def pick(item, rng):
    key = (item["family"], item["char"])
    places = item["places"]
    if item["count"] <= ALL_IF_AT_MOST:
        return places
    n = MANY.get(key, DEFAULT)
    # spread over sources and pages: sort by place, take evenly spaced ones
    places = sorted(places, key=lambda p: (p[0], p[1], p[2][1]))
    step = len(places) / float(n)
    return [places[int(i * step + rng.random() * step)] for i in range(n)]


def main():
    inv = json.loads((state.WORK / "char_inventory.json").read_text(encoding="utf-8"))
    pdf_of = {(s, u): (p, i) for s, u, p, i in tl.sources()}
    rng = random.Random(1113)
    pairs = list(inv["pairs"])
    rng.shuffle(pairs)
    key, rows = {}, []
    for n, item in enumerate(pairs, 1):
        kid = "K%02d" % n
        chosen = pick(item, rng)
        key[kid] = {"family": item["family"], "char": item["char"], "code": item["code"], "count": item["count"],
                    "pages": item["pages"], "looked_at": len(chosen),
                    "places": [[p[0], p[1]] for p in chosen]}
        for r in range(0, len(chosen), COLS):
            rows.append((kid + "abcdefgh"[r // COLS], chosen[r:r + COLS]))

    SHEETS.mkdir(parents=True, exist_ok=True)
    for old in SHEETS.glob("sheet_*.png"):
        old.unlink()
    cell_w = HALF_WIDTH * 2 * SCALE
    cell_h = 15.0 * SCALE
    width = LABEL_W + COLS * (cell_w + GAP)
    n_sheets = 0
    cache = {}
    for first in range(0, len(rows), ROWS):
        n_sheets += 1
        chunk = rows[first:first + ROWS]
        doc = fitz.open()
        page = doc.new_page(width=width, height=len(chunk) * (cell_h + GAP) + GAP)
        for r, (label, places) in enumerate(chunk):
            y = GAP + r * (cell_h + GAP)
            page.insert_text((6, y + cell_h / 2 + 5), label, fontsize=17, color=(0, 0, 0.6))
            for c, (source, unit, bbox, style, size) in enumerate(places):
                pdf, idx = pdf_of[(source, unit)]
                if pdf not in cache:
                    cache[pdf] = fitz.open(str(pdf))
                src = cache[pdf]
                x0, y0, x1, y1 = bbox
                cx = (x0 + x1) / 2
                mid = (y0 + y1) / 2
                clip = fitz.Rect(cx - HALF_WIDTH, mid - 7.5, cx + HALF_WIDTH, mid + 7.5) & src[idx].rect
                x = LABEL_W + c * (cell_w + GAP)
                target = fitz.Rect(x, y, x + clip.width * SCALE, y + clip.height * SCALE)
                page.draw_rect(fitz.Rect(x, y, x + cell_w, y + cell_h), color=(0.75, 0.75, 0.75), width=0.5)
                page.show_pdf_page(target, src, idx, clip=clip)
                # red tick under the character
                tx0 = x + (x0 - clip.x0) * SCALE
                tx1 = x + (x1 - clip.x0) * SCALE
                page.draw_line((tx0, y + cell_h - 3), (tx1, y + cell_h - 3), color=(1, 0, 0), width=3)
        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
        pix.save(str(SHEETS / ("sheet_%02d.png" % n_sheets)))
        doc.close()
    (SHEETS / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    state.out("pairs: %d; occurrences on sheets: %d; rows: %d; sheets: %d (%s)" % (
        len(key), sum(v["looked_at"] for v in key.values()), len(rows), n_sheets, SHEETS.relative_to(state.ROOT).as_posix()))
    state.out("row labels per sheet:")
    for first in range(0, len(rows), ROWS):
        state.out("  sheet_%02d: %s" % (first // ROWS + 1, " ".join(label for label, _ in rows[first:first + ROWS])))


if __name__ == "__main__":
    main()
