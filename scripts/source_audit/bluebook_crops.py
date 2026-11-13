#!/usr/bin/env python3
"""
Stage 5b: Blue Book forms cut from the scan, for reading
========================================================

The stored Blue Book forms were taken from the OCR text of the scan, so they
can only be checked against the scan itself. This cuts the printed line of
each chosen form out of the page image (found through the OCR layer's word
positions) and puts the crops on sheets, labelled by id only.

Chosen: the printed form behind every Blue Book-only dictionary entry (these
are entries learners see), and a random sample of 60 of the other stored
forms, to estimate how often the OCR text misled.

    python scripts/source_audit/bluebook_crops.py          # sheets and key in work/bluebook/
    python scripts/source_audit/bluebook_crops.py --grade  # compare bluebook_readings.json with the stored forms
"""
import argparse
import collections
import json
import random
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
from bluebook_check import PDF, squash  # noqa: E402

FOLDER = state.WORK / "bluebook"
ZOOM, PER_SHEET = 2.7, 11


def bb_squash(headword):
    """A Parks-style headword in the shape the Blue Book would print it, squashed (c is printed ts)."""
    return squash(unicodedata.normalize("NFC", headword).replace("c", "ts"))


def find_on_pages(doc, needle, pages):
    """First place where the squashed needle occurs in the OCR words of the given pages: (page number, box)."""
    for p in pages:
        if p < 1 or p > len(doc):
            continue
        words = [w for w in doc[p - 1].get_text("words") if squash(w[4])]
        text, starts = "", []
        for w in words:
            starts.append(len(text))
            text += squash(w[4])
        i = text.find(needle)
        if i < 0:
            continue
        hit = [w for s, w in zip(starts, words) if s < i + len(needle) and s + len(squash(w[4])) > i]
        return p, [min(w[0] for w in hit), min(w[1] for w in hit), max(w[2] for w in hit), max(w[3] for w in hit)]
    return None, None


def exact(s):
    """For comparing a reading with a stored form: spaces and case ignored, apostrophes and ? kept."""
    s = unicodedata.normalize("NFC", s or "").replace("’", "'").replace("‘", "'").replace("`", "'").replace("ʔ", "'")
    return re.sub(r"[\s•·]", "", s).lower().rstrip(".,;:!")


def grade():
    key = json.loads((FOLDER / "key.json").read_text(encoding="utf-8"))
    readings = json.loads((state.OUT / "bluebook_readings.json").read_text(encoding="utf-8"))
    tally = collections.defaultdict(collections.Counter)
    rows = []
    for cid, k in sorted(key.items()):
        r = readings.get(cid)
        if r is None:
            tally[k["group"]]["not read"] += 1
            continue
        read = r["form"] if isinstance(r, dict) else r
        stored = k["stored_form"]
        respelled = k.get("stored_form_is", "").startswith("the headword")
        if respelled:                      # a headword in Parks's letters: put it back into the book's letters to compare
            stored = unicodedata.normalize("NFC", stored).replace("c", "ts").replace("ʔ", "'")
        plain = lambda s: squash("".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch)))
        import difflib
        likeness = difflib.SequenceMatcher(None, plain(read), plain(stored), autojunk=False).ratio()
        if exact(read) == exact(stored):
            verdict = "same"
        elif likeness < 0.6:
            verdict = "crop-shows-something-else"       # the form was not located on the scan; nothing learned
        elif plain(read) == plain(stored):
            marks = [ch for ch in unicodedata.normalize("NFD", read) if unicodedata.combining(ch)]
            verdict = "accent-mark-missing" if marks else "apostrophe-dot-or-space"
        else:
            verdict = "letters-differ"
        if respelled and verdict != "crop-shows-something-else":
            verdict += " (headword respelled)"
        tally[k["group"]][verdict] += 1
        rows.append(dict(k, crop=cid, read=read, verdict=verdict))
    (state.OUT / "bluebook_graded.json").write_text(json.dumps(
        {"tally": {g: dict(c) for g, c in tally.items()}, "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for g, c in tally.items():
        state.out("%-22s %s" % (g, dict(c)))
    for r in rows:
        if r["verdict"] != "same":
            state.out("  %s p%s %-18s stored %-30r read %r" % (r["crop"], r["page"], r["verdict"], r["stored_form"], r["read"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grade", action="store_true")
    args = ap.parse_args()
    if args.grade:
        grade()
        return
    doc = fitz.open(str(PDF))
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    rng = random.Random(20261113)
    items, not_found = [], []
    all_pages = list(range(1, len(doc) + 1))
    for entry_id, headword in conn.execute("select entry_id, headword from lexical_entries where source='blue_book' order by entry_id"):
        att = conn.execute("select bb_skiri_form, bb_english, page_number from blue_book_attestations where entry_id=? and page_number is not null "
                           "order by id limit 1", (entry_id,)).fetchone()
        gloss = conn.execute("select group_concat(definition, ' | ') from glosses where entry_id=?", (entry_id,)).fetchone()[0]
        if att:
            page, box = find_on_pages(doc, squash(att[0]), [att[2], att[2] - 1, att[2] + 1])
            form = att[0]
        else:
            page, box = find_on_pages(doc, bb_squash(headword), all_pages)
            form = None
        if box is None:
            not_found.append({"entry_id": entry_id, "headword": headword, "gloss": gloss})
            continue
        items.append({"group": "blue-book-only-entry", "entry_id": entry_id, "headword_stored": headword, "gloss_stored": gloss,
                      "stored_form": form or headword, "stored_form_is": "the printed form on record" if form else "the headword (no printed form on record)",
                      "page": page, "box": [round(v, 1) for v in box]})
    others = conn.execute("select id, bb_skiri_form, bb_english, page_number from blue_book_attestations where page_number is not null "
                          "and (entry_id is null or entry_id not like 'BB-%') and length(bb_skiri_form) >= 4").fetchall()
    rng.shuffle(others)
    n = 0
    for rid, form, english, page in others:
        if n >= 60:
            break
        p, box = find_on_pages(doc, squash(form), [page])
        if box is None:
            continue
        items.append({"group": "sample-of-other-forms", "attestation_id": rid, "stored_form": form, "gloss_stored": english,
                      "page": p, "box": [round(v, 1) for v in box]})
        n += 1
    rng.shuffle(items)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for old in FOLDER.glob("bb_*.png"):
        old.unlink()
    key = {}
    for s in range(0, len(items), PER_SHEET):
        chunk = items[s:s + PER_SHEET]
        sheet = fitz.open()
        row_h = 128
        pg = sheet.new_page(width=1180, height=len(chunk) * row_h + 10)
        for i, it in enumerate(chunk):
            cid = "B%03d" % (s + i + 1)
            x0, y0, x1, y1 = it["box"]
            src_page = doc[it["page"] - 1]
            clip = fitz.Rect(max(0, x0 - 30), max(0, y0 - 9), min(src_page.rect.width, max(x1 + 60, x0 + 330)), min(src_page.rect.height, y1 + 9))
            y = 6 + i * row_h
            pg.insert_text((6, y + 40), cid, fontsize=17, color=(0, 0, 0.7))
            scale = min(ZOOM, 1090.0 / clip.width, (row_h - 12) / clip.height)
            target = fitz.Rect(80, y, 80 + clip.width * scale, y + clip.height * scale)
            pg.show_pdf_page(target, doc, it["page"] - 1, clip=clip)
            ux0, ux1 = 80 + (x0 - clip.x0) * scale, 80 + (x1 - clip.x0) * scale
            uy = y + (y1 - clip.y0) * scale + 3
            pg.draw_line((ux0, uy), (ux1, uy), color=(1, 0, 0), width=2)
            key[cid] = it
        sheet[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(str(FOLDER / ("bb_%02d.png" % (s // PER_SHEET + 1))))
        sheet.close()
    (FOLDER / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    (FOLDER / "entries_not_located.json").write_text(json.dumps(not_found, ensure_ascii=False, indent=1), encoding="utf-8")
    groups = collections.Counter(v["group"] for v in key.values())
    state.out("crops: %d %s on %d sheets; Blue Book-only entries not located in the OCR layer: %d" % (
        len(key), dict(groups), (len(items) + PER_SHEET - 1) // PER_SHEET, len(not_found)))
    for e in not_found[:50]:
        state.out("   not located: %s  %s  '%s'" % (e["entry_id"], e["headword"], e["gloss"]))


if __name__ == "__main__":
    main()
