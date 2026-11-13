#!/usr/bin/env python3
"""
Stage 4a: tiles of the image-only pages, for a blind reading
============================================================

The appendices and front-matter chapters 2 to 5 have no text layer (the print
is stored as outlines). A page is cut into tiles at a magnification where the
accents are clear, the tiles are put on sheets, and a reader who sees nothing
else writes down what is printed.

    python scripts/source_audit/appendix_tiles.py appendix1    # 7 pages, 70 tiles (one per mode), 14 sheets
    python scripts/source_audit/appendix_tiles.py overview --pdf "Appendix 3" --page 1   # a whole page, small, to plan tiles
    python scripts/source_audit/appendix_tiles.py bands --pdf "Appendix 3" --name appendix3 --bands 4

Appendix 1 has one fixed layout on pages 2 to 8: two columns of five modes,
eleven persons each. Odd pages are set 44 points further right than even ones.

Sheets go to work/appendix/<name>/.
"""
import argparse
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import textlayer as tl  # noqa: E402

OUT = state.WORK / "appendix"


def find_pdf(fragment):
    hits = [p for p in sorted(tl.PARTS_DIR.glob("*.pdf")) if fragment.lower() in p.name.lower()]
    if len(hits) != 1:
        sys.exit("no single PDF matches %r: %s" % (fragment, [h.name for h in hits]))
    return hits[0]


def sheet(tiles, src, path, zoom, cols):
    """tiles: [(label, page index, clip rect)]. Lays them out in rows of `cols`, label above each."""
    label_h, gap = 26, 12
    w = max(t[2].width for t in tiles) * zoom
    h = max(t[2].height for t in tiles) * zoom
    rows = (len(tiles) + cols - 1) // cols
    doc = fitz.open()
    page = doc.new_page(width=cols * (w + gap) + gap, height=rows * (h + label_h + gap) + gap)
    for n, (label, pno, clip) in enumerate(tiles):
        x = gap + (n % cols) * (w + gap)
        y = gap + (n // cols) * (h + label_h + gap)
        page.insert_text((x, y + 19), label, fontsize=19, color=(0, 0, 0.7))
        target = fitz.Rect(x, y + label_h, x + clip.width * zoom, y + label_h + clip.height * zoom)
        page.draw_rect(target, color=(0.75, 0.75, 0.75), width=0.6)
        page.show_pdf_page(target, src, pno, clip=clip)
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
    pix.save(str(path))
    doc.close()
    return pix.width, pix.height


def appendix1():
    src = fitz.open(str(find_pdf("Appendix 1")))
    folder = OUT / "appendix1"
    folder.mkdir(parents=True, exist_ok=True)
    made = []
    for pno in range(1, 8):                       # pages 2 to 8 of the file
        shift = 44.0 if (pno + 1) % 2 == 1 else 0.0
        tiles = []
        for band in range(5):
            y0 = 55.0 + 124.4 * band
            for side, x0 in (("L", 58.0 + shift), ("R", 260.0 + shift)):
                clip = fitz.Rect(x0, y0, x0 + (203.0 if side == "L" else 246.0), y0 + 131.0)
                tiles.append(("p%d-%s%d" % (pno + 1, side, band + 1), pno, clip))
        for part, chunk in (("a", tiles[:6]), ("b", tiles[6:])):
            path = folder / ("appendix1_p%d%s.png" % (pno + 1, part))
            size = sheet(chunk, src, path, 3.0, 2)
            made.append((path.name, size, [t[0] for t in chunk]))
    for name, size, labels in made:
        state.out("%s  %dx%d  %s" % (name, size[0], size[1], " ".join(labels)))


def overview(pdf, pno, zoom):
    src = fitz.open(str(find_pdf(pdf)))
    folder = OUT / "overview"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("%s_p%d.png" % (pdf.replace(" ", "").lower(), pno))
    pix = src[pno - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(str(path))
    state.out("%s  %dx%d  (%d pages in the file)" % (path.relative_to(state.ROOT).as_posix(), pix.width, pix.height, len(src)))


def bands(pdf, name, n_bands, zoom, top, bottom, left, right, first, last, per_sheet=2):
    """Whole-width bands of each page, with a small overlap, one band per tile, two tiles per sheet."""
    src = fitz.open(str(find_pdf(pdf)))
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    last = last or len(src)
    for pno in range(first - 1, last):
        step = (bottom - top) / float(n_bands)
        tiles = []
        for b in range(n_bands):
            y0 = top + step * b - 6
            clip = fitz.Rect(left, max(0, y0), right, min(src[pno].rect.height, y0 + step + 12))
            tiles.append(("p%d-b%d" % (pno + 1, b + 1), pno, clip))
        for i in range(0, len(tiles), per_sheet):
            path = folder / ("%s_p%d_%d.png" % (name, pno + 1, i // per_sheet + 1))
            size = sheet(tiles[i:i + per_sheet], src, path, zoom, 1)
            state.out("%s  %dx%d  %s" % (path.name, size[0], size[1], " ".join(t[0] for t in tiles[i:i + per_sheet])))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["appendix1", "overview", "bands"])
    ap.add_argument("--pdf")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--zoom", type=float, default=None)
    ap.add_argument("--name")
    ap.add_argument("--bands", type=int, default=4)
    ap.add_argument("--top", type=float, default=40.0)
    ap.add_argument("--bottom", type=float, default=740.0)
    ap.add_argument("--left", type=float, default=50.0)
    ap.add_argument("--right", type=float, default=562.0)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--per-sheet", type=int, default=2)
    args = ap.parse_args()
    if args.what == "appendix1":
        appendix1()
    elif args.what == "overview":
        overview(args.pdf, args.page, args.zoom or 1.5)
    else:
        bands(args.pdf, args.name, args.bands, args.zoom or 2.9, args.top, args.bottom, args.left, args.right, args.first, args.last, args.per_sheet)


if __name__ == "__main__":
    main()
