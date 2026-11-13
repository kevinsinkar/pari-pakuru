#!/usr/bin/env python3
"""
Stage 1d: where each accent code occurs, over the whole text layer
==================================================================

The phonetic font draws the lax i as a bare stem, so a lax i with an accent and
a tense i with an accent look the same on the page. What tells the two codes
apart is where they stand: Parks writes a long vowel as two tense letters with
the accent on the second, and a short vowel as one lax letter. So a code that
always follows a plain vowel letter of its own quality is the second half of a
long vowel, and a code that never does is a short vowel.

This counts, for every accent code of the phonetic font, the character before
it and the character after it, on all 471 text-layer pages. Every occurrence,
not a sample.

    python scripts/source_audit/char_distribution.py     # writes work/char_distribution.json

Also gives --zoom, which renders a few occurrences of named codes much larger,
for the glyphs that the normal sheets leave in doubt.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import textlayer as tl  # noqa: E402

ACCENT_CODES = "àá‡æˆçŠ÷‹øÑÒ"
PHON = ("PAdothyphen",)


def distribution():
    before = collections.defaultdict(collections.Counter)
    after = collections.defaultdict(collections.Counter)
    in_other_fonts = collections.Counter()
    for source, unit, pdf, idx in tl.sources():
        prev = None                                      # (family, char) of the previous character
        pending = None
        for font, size, flags, ch, bbox, b, l, s in tl.page_chars(pdf, idx):
            fam, _ = tl.family(font)
            if pending is not None:
                after[pending][ch if fam in PHON else "<%s>" % fam] += 1
                pending = None
            if ch in ACCENT_CODES:
                if fam in PHON:
                    before[ch][prev[1] if prev and prev[0] in PHON else "<start>"] += 1
                    pending = ch
                else:
                    in_other_fonts[(fam, ch)] += 1
            prev = (fam, ch)
    return before, after, in_other_fonts


def zoom(pairs, per_pair, scale):
    inv = json.loads((state.WORK / "char_inventory.json").read_text(encoding="utf-8"))
    pdf_of = {(s, u): (p, i) for s, u, p, i in tl.sources()}
    wanted = [it for it in inv["pairs"] if "%s:%s" % (it["family"], it["char"]) in pairs]
    wanted.sort(key=lambda it: pairs.index("%s:%s" % (it["family"], it["char"])))
    half, cell_h = 11.0, 15.0
    cell_w = half * 2 * scale
    doc = fitz.open()
    page = doc.new_page(width=90 + per_pair * (cell_w + 10), height=len(wanted) * (cell_h * scale + 10) + 10)
    for r, item in enumerate(wanted):
        y = 10 + r * (cell_h * scale + 10)
        page.insert_text((6, y + cell_h * scale / 2), "Z%02d" % (r + 1), fontsize=20, color=(0, 0, 0.6))
        places = sorted(item["places"], key=lambda p: (p[0], p[1]))
        step = max(1, len(places) // per_pair)
        for c, (source, unit, bbox, style, size) in enumerate(places[::step][:per_pair]):
            pdf, idx = pdf_of[(source, unit)]
            src = fitz.open(str(pdf))
            x0, y0, x1, y1 = bbox
            cx, mid = (x0 + x1) / 2, (y0 + y1) / 2
            clip = fitz.Rect(cx - half, mid - cell_h / 2, cx + half, mid + cell_h / 2) & src[idx].rect
            x = 90 + c * (cell_w + 10)
            page.show_pdf_page(fitz.Rect(x, y, x + clip.width * scale, y + clip.height * scale), src, idx, clip=clip)
            page.draw_line((x + (x0 - clip.x0) * scale, y + cell_h * scale - 3), (x + (x1 - clip.x0) * scale, y + cell_h * scale - 3),
                           color=(1, 0, 0), width=3)
            src.close()
    out_path = state.WORK / "char_sheets" / "zoom.png"
    page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(str(out_path))
    (state.WORK / "char_sheets" / "zoom_key.json").write_text(
        json.dumps({"Z%02d" % (i + 1): "%s:%s" % (it["family"], it["char"]) for i, it in enumerate(wanted)}, ensure_ascii=False), encoding="utf-8")
    state.out("zoom sheet: %s (%d rows)" % (out_path.relative_to(state.ROOT).as_posix(), len(wanted)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zoom", nargs="+", metavar="FAMILY:CHAR", help="render these pairs large instead of counting")
    ap.add_argument("--per-pair", type=int, default=3)
    ap.add_argument("--scale", type=float, default=16.0)
    args = ap.parse_args()
    if args.zoom:
        zoom(args.zoom, args.per_pair, args.scale)
        return
    before, after, other = distribution()
    data = {}
    for ch in ACCENT_CODES:
        total = sum(before[ch].values())
        data[ch] = {"code": "U+%04X" % ord(ch), "occurrences": total,
                    "before": dict(before[ch].most_common()), "after": dict(after[ch].most_common())}
        state.out("%s %s  x%-5d before: %-60s after: %s" % (
            ch, data[ch]["code"], total,
            " ".join("%s:%d" % kv for kv in before[ch].most_common(9)),
            " ".join("%s:%d" % kv for kv in after[ch].most_common(7))))
    data["_in_other_fonts"] = {"%s %s" % k: v for k, v in other.items()}
    (state.WORK / "char_distribution.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
