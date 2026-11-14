#!/usr/bin/env python3
"""
A second reading of the Blue Book forms the first reading left open (2026-11-14)
===============================================================================

After the first blind reading of the scan, 77 stored forms were left for a
person: the reader's letters differed from the stored ones, the reader was
unsure, or the crop showed something else. One reading against one OCR
reading settles nothing. This makes new sheets for those forms, with wider
crops (the whole line and the lines above and below), for a second reader
who sees only the images.

    python scripts/source_audit/bluebook_second_look.py           # sheets and key in work/bluebook_second/
    python scripts/source_audit/bluebook_second_look.py --grade   # compare the two readings

The second reading is expected in
reports/source_audit_2026-11/blind_readings/bluebook_second_look.json,
a JSON object {crop id: {"form": ..., "english": ..., "note": ...}}.

--grade writes bluebook_second_look.json. For every form:
    two readings agree     both readers, independently, read the same letters, accents, dots and
                           apostrophes: settled, and scripts/apply_bluebook_scan_fixes.py takes it
    second reading agrees with the stored form    the first reader slipped: the stored form stands
    readings differ        still open, for a person with the book
    reader unsure          one of the readers marked a letter [?]: still open
"""
import argparse
import collections
import json
import sys
import unicodedata
import re
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state  # noqa: E402
from bluebook_check import PDF  # noqa: E402

FOLDER = state.WORK / "bluebook_second"
READING = state.OUT / "blind_readings" / "bluebook_second_look.json"
PER_SHEET = 8


def clean(reading):
    """A transcription in the database's Blue Book conventions: • for the raised dot, ' for the glottal stop."""
    s = unicodedata.normalize("NFC", reading or "").replace("·", "•").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


def open_forms():
    """The forms the first reading left open: (crop id of the first reading, page, box, stored form, first reading, kind)."""
    from apply_bluebook_scan_fixes import decide
    out = []
    rest = json.loads((state.OUT / "bluebook_rest_graded.json").read_text(encoding="utf-8"))["rows"]
    for r in rest:
        new, kind = decide(r["stored_form"], r["read"])
        if new is None and kind != "same":
            out.append({"first_crop": r["crop"], "page": r["page"], "box": r["box"], "stored_form": r["stored_form"],
                        "attestation_ids": r["attestation_ids"], "first_reading": r["read"], "first_kind": kind})
    first = json.loads((state.OUT / "bluebook_graded.json").read_text(encoding="utf-8"))["rows"]
    key = json.loads((state.WORK / "bluebook" / "key.json").read_text(encoding="utf-8"))
    for r in first:
        if r.get("stored_form_is", "").startswith("the headword"):
            continue
        new, kind = decide(r["stored_form"], r["read"])
        if new is None and kind != "same":
            k = key.get(r["crop"]) or {}
            out.append({"first_crop": r["crop"], "page": r["page"], "box": k.get("box"), "stored_form": r["stored_form"],
                        "attestation_ids": [r["attestation_id"]] if r.get("attestation_id") else [], "entry_id": r.get("entry_id"),
                        "first_reading": r["read"], "first_kind": kind})
    out.sort(key=lambda r: (r["page"], r["first_crop"]))
    return out


def sheets():
    items = [r for r in open_forms() if r["box"]]
    doc = fitz.open(str(PDF))
    FOLDER.mkdir(parents=True, exist_ok=True)
    for old in FOLDER.glob("bb2_*.png"):
        old.unlink()
    key = {}
    for s in range(0, len(items), PER_SHEET):
        chunk = items[s:s + PER_SHEET]
        sheet = fitz.open()
        row_h = 190
        pg = sheet.new_page(width=1280, height=len(chunk) * row_h + 10)
        for i, it in enumerate(chunk):
            cid = "S%03d" % (s + i + 1)
            x0, y0, x1, y1 = it["box"]
            src = doc[it["page"] - 1]
            # the whole line across the column, with the line above and the line below
            clip = fitz.Rect(max(0, x0 - 150), max(0, y0 - 24), min(src.rect.width, x1 + 260), min(src.rect.height, y1 + 24))
            y = 6 + i * row_h
            pg.insert_text((6, y + 60), cid, fontsize=16, color=(0, 0, 0.7))
            scale = min(3.0, 1190.0 / clip.width, (row_h - 14) / clip.height)
            target = fitz.Rect(84, y, 84 + clip.width * scale, y + clip.height * scale)
            pg.show_pdf_page(target, doc, it["page"] - 1, clip=clip)
            ux0, ux1 = 84 + (x0 - clip.x0) * scale, 84 + (x1 - clip.x0) * scale
            uy = y + (y1 - clip.y0) * scale + 2
            pg.draw_line((ux0, uy), (ux1, uy), color=(1, 0, 0), width=2)
            pg.draw_line((84, y + row_h - 8), (1270, y + row_h - 8), color=(0.75, 0.75, 0.75), width=0.5)
            key[cid] = it
        sheet[0].get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False).save(str(FOLDER / ("bb2_%02d.png" % (s // PER_SHEET + 1))))
        sheet.close()
    (FOLDER / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    state.out("forms left open by the first reading: %d; crops: %d on %d sheets (%s)" % (
        len(open_forms()), len(key), (len(items) + PER_SHEET - 1) // PER_SHEET, FOLDER.relative_to(state.ROOT).as_posix()))


def grade():
    key = json.loads((FOLDER / "key.json").read_text(encoding="utf-8"))
    second = json.loads(READING.read_text(encoding="utf-8"))
    tally, rows = collections.Counter(), []
    for cid, k in sorted(key.items()):
        r = second.get(cid)
        if r is None:
            tally["not read"] += 1
            continue
        b = clean(r["form"] if isinstance(r, dict) else r)
        a = clean(k["first_reading"])
        if "[?]" in a or "[?]" in b:
            verdict = "reader unsure"
        elif a == b:
            verdict = "two readings agree"
        elif b == clean(k["stored_form"]):
            verdict = "second reading agrees with the stored form"
        else:
            verdict = "readings differ"
        tally[verdict] += 1
        rows.append(dict(k, crop=cid, second_reading=b, english_read=(r.get("english") if isinstance(r, dict) else ""),
                         pawnee=(r.get("pawnee", True) if isinstance(r, dict) else True),
                         note=(r.get("note") if isinstance(r, dict) else ""), verdict=verdict))
    (state.OUT / "bluebook_second_look.json").write_text(json.dumps(
        {"crops": len(key), "tally": dict(tally), "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("crops %d; %s" % (len(key), dict(tally)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grade", action="store_true")
    args = ap.parse_args()
    if args.grade:
        grade()
    else:
        sheets()


if __name__ == "__main__":
    main()
