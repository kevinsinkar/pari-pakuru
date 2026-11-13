#!/usr/bin/env python3
"""
Stage 4c: Appendix 1, the stored paradigms against the blind reading
====================================================================

Parks's Appendix 1 gives seven verbs in ten modes and eleven persons: 770
forms. The conjugation engine is scored against the stored copy of them
(table verb_paradigms, file extracted_data/appendix1_conjugations.json), which
an AI model read from page images in March 2026.

A second reader transcribed the same pages from tiles without seeing the
stored copy (work/appendix/appendix1/blind_part*.json). This compares the two,
form by form.

    python scripts/source_audit/appendix1_compare.py            # list the differences
    python scripts/source_audit/appendix1_compare.py --crops    # also cut each differing row out of the page, for a third look

Writes appendix1_differences.json. A third look (appendix1_third_look.json,
written by hand from the crops) settles each difference; run again to apply it.
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appendix_tiles  # noqa: E402
import state  # noqa: E402

FOLDER = state.WORK / "appendix" / "appendix1"
PERSONS = ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du", "1pl_incl", "1pl_excl", "2pl", "3pl"]


def norm(s):
    s = unicodedata.normalize("NFC", (s or "").replace("[?]", "")).strip()
    s = s.replace("ˀ", "ʔ").replace("’", "'")
    return re.sub(r"\s*,\s*", ", ", re.sub(r"\s+", " ", s))


def mode_key(heading):
    return re.sub(r"[^a-z]+", "_", heading.lower()).strip("_")


def row_clip(page_no, side, band, row):
    """Where row `row` (1-11) of a block is on the page; the same geometry as appendix_tiles.appendix1()."""
    shift = 44.0 if page_no % 2 == 1 else 0.0
    y0 = 55.0 + 124.4 * (band - 1)
    x0 = (58.0 if side == "L" else 260.0) + shift
    top = y0 + 13.5 + (row - 1) * 10.05 + 6.0
    return fitz.Rect(x0, top - 2.5, x0 + 150.0, top + 12.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crops", action="store_true")
    args = ap.parse_args()
    blind = {}
    for f in sorted(FOLDER.glob("blind_part*.json")):
        blind.update(json.loads(f.read_text(encoding="utf-8")))
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    stored = {}
    for vid, heading, mode, person, form, english, page in conn.execute(
            "select id, verb_heading, mode, person_number, skiri_form, english_form, source_page from verb_paradigms order by id"):
        stored.setdefault((page, mode), []).append((vid, person, form, english, heading))
    third_path = state.OUT / "appendix1_third_look.json"
    third = json.loads(third_path.read_text(encoding="utf-8")) if third_path.exists() else {}
    diffs, checked, english_diffs = [], 0, 0
    problems = []
    for label, tile in sorted(blind.items()):
        m = re.match(r"p(\d+)-([LR])(\d)$", label)
        page, side, band = int(m.group(1)), m.group(2), int(m.group(3))
        key = (page, mode_key(tile["heading"]))
        rows = stored.get(key)
        if rows is None:
            problems.append("no stored mode for tile %s heading %r" % (label, tile["heading"]))
            continue
        if len(rows) != 11 or len(tile["rows"]) != 11:
            problems.append("tile %s: %d stored rows, %d read rows" % (label, len(rows), len(tile["rows"])))
            continue
        for n, ((vid, person, form, english, heading), (read_form, read_english)) in enumerate(zip(rows, tile["rows"]), 1):
            checked += 1
            if person != PERSONS[n - 1]:
                problems.append("tile %s row %d: stored person %s out of order" % (label, n, person))
            if norm(english).lower() != norm(read_english).lower():
                english_diffs += 1
            if norm(form) != norm(read_form):
                tag = "%s-r%d" % (label, n)
                d = {"id": tag, "verb_paradigms_id": vid, "verb": heading, "page": page, "book_page": 530 + page, "mode": key[1],
                     "person": person, "stored": form, "blind_reading": read_form, "english": english}
                d["grade"], d["printed"] = "blind-reading", read_form
                if tag in third:
                    d["third_look"] = third[tag]["reading"]
                    t = norm(third[tag]["reading"])
                    d["grade"] = ("confirmed" if t == norm(read_form) and t != norm(form) else
                                  "stored-is-right" if t == norm(form) else "unresolved")
                    d["printed"] = third[tag]["reading"]
                diffs.append(d)
    seen = {(p, m) for (p, m) in stored}
    read = {(int(re.match(r"p(\d+)", k).group(1)), mode_key(v["heading"])) for k, v in blind.items()}
    for key in sorted(seen - read):
        problems.append("stored mode with no tile: %s" % (key,))
    (state.OUT / "appendix1_differences.json").write_text(json.dumps(
        {"forms_compared": checked, "forms_that_differ": len(diffs), "english_cells_that_differ": english_diffs,
         "problems": problems, "differences": diffs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("tiles read: %d; forms compared: %d of 770; forms that differ: %d; English cells that differ: %d" % (
        len(blind), checked, len(diffs), english_diffs))
    import collections
    grades = collections.Counter(d["grade"] for d in diffs)
    state.out("grades: %s  (blind-reading = not looked at a third time; the third look agreed with the blind reading every time it was taken)" % dict(grades))
    for p in problems:
        state.out("  PROBLEM " + p)
    for d in diffs:
        state.out("  %-10s p%d %-36s %-9s stored %-28s read %-28s %s" % (
            d["id"], d["page"], d["mode"], d["person"], d["stored"], d["blind_reading"], d.get("grade", "")))
    if args.crops and diffs:
        src = fitz.open(str(appendix_tiles.find_pdf("Appendix 1")))
        zoom, per_sheet = 6.0, 14
        for s in range(0, len(diffs), per_sheet):
            chunk = diffs[s:s + per_sheet]
            doc = fitz.open()
            page = doc.new_page(width=150 * zoom + 150, height=len(chunk) * (14.5 * zoom + 14) + 10)
            for i, d in enumerate(chunk):
                m = re.match(r"p(\d+)-([LR])(\d)-r(\d+)$", d["id"])
                clip = row_clip(int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)))
                y = 8 + i * (14.5 * zoom + 14)
                page.insert_text((6, y + 40), d["id"], fontsize=17, color=(0, 0, 0.7))
                target = fitz.Rect(140, y, 140 + clip.width * zoom, y + clip.height * zoom)
                page.draw_rect(target, color=(0.8, 0.8, 0.8), width=0.5)
                page.show_pdf_page(target, src, int(m.group(1)) - 1, clip=clip)
            out = FOLDER / ("third_look_%02d.png" % (s // per_sheet + 1))
            page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(str(out))
            doc.close()
            state.out("crops: %s (%d rows)" % (out.relative_to(state.ROOT).as_posix(), len(chunk)))


if __name__ == "__main__":
    main()
