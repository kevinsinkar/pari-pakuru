#!/usr/bin/env python3
"""
Stage 5c: the rest of the Blue Book forms, cut from the scan for reading
========================================================================

The first pass (bluebook_crops.py) read the Blue Book-only entries and a
sample of 60 other forms. This cuts out every remaining stored form that has a
page: one crop for each distinct form on a page, shared by all the rows that
hold it.

    python scripts/source_audit/bluebook_rest.py            # sheets and key in work/bluebook_rest/
    python scripts/source_audit/bluebook_rest.py --grade    # compare the readings with the stored forms

Readings are expected in reports/source_audit_2026-11/blind_readings/bluebook_rest_part*.json,
each a JSON object {crop id: {"form": ..., "english": ...}}.

--grade writes bluebook_rest_graded.json: for every crop, the stored form, the
reading, and a verdict:
    same                      letter for letter
    accent-mark-missing       the scan has an accent the stored form lacks; letters agree
    apostrophe-dot-or-space   only an apostrophe, a raised dot or a space differs
    letters-differ            other letters: an OCR slip in the stored form, or a slip of the reader
    crop-shows-something-else the form was not found where the OCR layer said; nothing learned
"""
import argparse
import collections
import difflib
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
from bluebook_check import PDF, squash  # noqa: E402
from bluebook_crops import exact, find_on_pages  # noqa: E402

FOLDER = state.WORK / "bluebook_rest"
READINGS = state.OUT / "blind_readings"
ZOOM, PER_SHEET = 2.7, 11


def plain(s):
    return squash("".join(ch for ch in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(ch)))


def verdict_for(stored, read):
    if exact(read) == exact(stored):
        return "same"
    likeness = difflib.SequenceMatcher(None, plain(read), plain(stored), autojunk=False).ratio()
    if likeness < 0.6:
        return "crop-shows-something-else"
    if plain(read) == plain(stored):
        marks = [ch for ch in unicodedata.normalize("NFD", read) if unicodedata.combining(ch)]
        return "accent-mark-missing" if marks else "apostrophe-dot-or-space"
    return "letters-differ"


def grade():
    key = json.loads((FOLDER / "key.json").read_text(encoding="utf-8"))
    readings = {}
    for f in sorted(READINGS.glob("bluebook_rest_part*.json")):
        readings.update(json.loads(f.read_text(encoding="utf-8")))
    tally = collections.Counter()
    rows = []
    for cid, k in sorted(key.items()):
        r = readings.get(cid)
        if r is None:
            tally["not read"] += 1
            continue
        read = (r["form"] if isinstance(r, dict) else r).strip()
        v = verdict_for(k["stored_form"], read)
        if "[?]" in read and v != "same":
            v += " (reader unsure)"
        tally[v] += 1
        rows.append(dict(k, crop=cid, read=read, english_read=(r.get("english") if isinstance(r, dict) else ""), verdict=v))
    (state.OUT / "bluebook_rest_graded.json").write_text(json.dumps(
        {"crops": len(key), "tally": dict(tally), "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("crops %d; %s" % (len(key), dict(tally)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grade", action="store_true")
    args = ap.parse_args()
    if args.grade:
        grade()
        return
    doc = fitz.open(str(PDF))
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    first = json.loads((state.WORK / "bluebook" / "key.json").read_text(encoding="utf-8"))
    already = set()
    for k in first.values():
        if k["group"] == "sample-of-other-forms" or k.get("stored_form_is", "").startswith("the printed form"):
            already.add((k["page"], squash(k["stored_form"])))
    groups = collections.OrderedDict()
    for rid, form, english, page in conn.execute("select id, bb_skiri_form, bb_english, page_number from blue_book_attestations "
                                                 "where page_number is not null and bb_skiri_form is not null order by page_number, id"):
        sq = squash(form)
        if not sq:
            continue
        groups.setdefault((page, sq), []).append((rid, form, english))
    items, not_located, skipped = [], [], 0
    for (page, sq), rows in groups.items():
        p, box = find_on_pages(doc, sq, [page, page - 1, page + 1])
        if box is None:
            not_located.append({"page": page, "form": rows[0][1], "attestation_ids": [r[0] for r in rows]})
            continue
        if (p, sq) in already or (page, sq) in already:
            skipped += 1
            continue
        items.append({"group": "rest", "attestation_ids": [r[0] for r in rows], "stored_form": rows[0][1],
                      "stored_forms_all": sorted({r[1] for r in rows}), "gloss_stored": rows[0][2], "page": p,
                      "box": [round(v, 1) for v in box]})
    FOLDER.mkdir(parents=True, exist_ok=True)
    for old in FOLDER.glob("bbr_*.png"):
        old.unlink()
    key = {}
    for s in range(0, len(items), PER_SHEET):
        chunk = items[s:s + PER_SHEET]
        sheet = fitz.open()
        row_h = 128
        pg = sheet.new_page(width=1180, height=len(chunk) * row_h + 10)
        for i, it in enumerate(chunk):
            cid = "R%04d" % (s + i + 1)
            x0, y0, x1, y1 = it["box"]
            src_page = doc[it["page"] - 1]
            clip = fitz.Rect(max(0, x0 - 30), max(0, y0 - 9), min(src_page.rect.width, max(x1 + 60, x0 + 330)), min(src_page.rect.height, y1 + 9))
            y = 6 + i * row_h
            pg.insert_text((6, y + 40), cid, fontsize=16, color=(0, 0, 0.7))
            scale = min(ZOOM, 1090.0 / clip.width, (row_h - 12) / clip.height)
            target = fitz.Rect(84, y, 84 + clip.width * scale, y + clip.height * scale)
            pg.show_pdf_page(target, doc, it["page"] - 1, clip=clip)
            ux0, ux1 = 84 + (x0 - clip.x0) * scale, 84 + (x1 - clip.x0) * scale
            uy = y + (y1 - clip.y0) * scale + 3
            pg.draw_line((ux0, uy), (ux1, uy), color=(1, 0, 0), width=2)
            key[cid] = it
        sheet[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(str(FOLDER / ("bbr_%03d.png" % (s // PER_SHEET + 1))))
        sheet.close()
    (FOLDER / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    (FOLDER / "not_located.json").write_text(json.dumps(not_located, ensure_ascii=False, indent=1), encoding="utf-8")
    n_sheets = (len(items) + PER_SHEET - 1) // PER_SHEET
    state.out("distinct forms with a page: %d; already read in the first pass: %d; not located in the OCR layer: %d" % (
        len(groups), skipped, len(not_located)))
    state.out("crops: %d on %d sheets (%s); they stand for %d stored rows" % (
        len(key), n_sheets, FOLDER.relative_to(state.ROOT).as_posix(), sum(len(v["attestation_ids"]) for v in key.values())))


if __name__ == "__main__":
    main()
