#!/usr/bin/env python3
"""
Stage 5: Blue Book forms against the book's own OCR layer
=========================================================

The Blue Book is a scan. Its PDF carries the text an OCR program read from the
scan, with the position of every word. That text is a second reading that no
AI model made, but it is a poor one for Pawnee words (it reads ' as nothing,
I as 1 or l, and so on).

Each stored Blue Book form (table blue_book_attestations: the Pawnee form as
printed, its English, its page) is looked for in the OCR text of its page:
  found           the form is there, letter for letter (ignoring spaces, case and apostrophes)
  found-nearly    a word or phrase on the page differs from it by one or two characters:
                  either an OCR slip or a copying slip; these go to a look at the page
  english-only    the English is on the page and the Pawnee form is not recognisable near it
  not-on-page     neither is on the stated page

    python scripts/source_audit/bluebook_check.py           # writes bluebook_check.json
    python scripts/source_audit/bluebook_check.py --crops   # also cuts the doubtful ones out of the scan

Also lists the 93 Blue Book-only dictionary entries with the printed form each
was made from, since their headwords are a respelling and not what is printed.
"""
import argparse
import collections
import difflib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

PDF = state.ROOT / "pari pakuru" / "Blue Book - Pari Pakuru.pdf"


def squash(s):
    s = unicodedata.normalize("NFC", s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'").replace("ʔ", "'").replace("•", "").replace("·", "")
    return re.sub(r"[^a-z0-9?]", "", s)          # apostrophes dropped too: the OCR loses most of them


def best_window(needle, hay):
    """(ratio, start, end) of the stretch of `hay` most like `needle`."""
    if not needle or not hay:
        return 0.0, 0, 0
    if needle in hay:
        i = hay.index(needle)
        return 1.0, i, i + len(needle)
    m = difflib.SequenceMatcher(None, hay, needle, autojunk=False)
    blocks = [b for b in m.get_matching_blocks() if b.size]
    if not blocks:
        return 0.0, 0, 0
    votes = collections.Counter()
    for b in blocks:
        votes[b.a - b.b] += b.size
    off = votes.most_common(1)[0][0]
    a, z = max(0, off), min(len(hay), off + len(needle))
    return difflib.SequenceMatcher(None, hay[a:z], needle, autojunk=False).ratio(), a, z


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crops", action="store_true")
    args = ap.parse_args()
    doc = fitz.open(str(PDF))
    pages = {}
    for i, page in enumerate(doc):
        words = page.get_text("words")            # x0, y0, x1, y1, word, block, line, n
        text, spans = [], []
        for wd in words:
            sq = squash(wd[4])
            if not sq:
                continue
            spans.append((len("".join(text)), wd))
            text.append(sq)
        pages[i + 1] = ("".join(text), spans, words)
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    rows = conn.execute("select id, bb_skiri_form, bb_english, context_type, lesson_number, page_number, entry_id "
                        "from blue_book_attestations order by id").fetchall()
    # which PDF page is the book page? try the stated page and its neighbours, and learn the offset
    offsets = collections.Counter()
    for rid, form, english, ctx, lesson, page, entry_id in rows[:400]:
        if not page or not form or len(squash(form)) < 6:
            continue
        for off in range(-3, 12):
            if squash(form) in pages.get(page + off, ("",))[0]:
                offsets[off] += 1
    offset = offsets.most_common(1)[0][0] if offsets else 0
    results, tally = [], collections.Counter()
    for rid, form, english, ctx, lesson, page, entry_id in rows:
        if not page:
            tally["no-page-stored"] += 1
            results.append({"id": rid, "form": form, "english": english, "page": None, "status": "no-page-stored", "entry_id": entry_id})
            continue
        needle = squash(form)
        best = (0.0, None, 0, 0)
        for p in (page + offset, page + offset - 1, page + offset + 1):
            if p not in pages:
                continue
            r, a, z = best_window(needle, pages[p][0])
            if r > best[0]:
                best = (r, p, a, z)
        r, p, a, z = best
        eng = squash(english or "")
        eng_found = bool(eng) and p is not None and (eng in pages[p][0] or best_window(eng, pages[p][0])[0] >= 0.9)
        if r == 1.0:
            status = "found"
        elif r >= 0.8:
            status = "found-nearly"
        elif eng_found:
            status = "english-only"
        else:
            status = "not-on-page"
        tally[status] += 1
        rec = {"id": rid, "form": form, "english": english, "context": ctx, "lesson": lesson, "page": page, "pdf_page": p,
               "status": status, "ratio": round(r, 3), "entry_id": entry_id}
        if p is not None and status != "found":
            rec["ocr_reads"] = pages[p][0][a:z]
            # the words of the OCR layer that the stretch falls in, for a crop
            boxes = [wd[:4] for start, wd in pages[p][1] if start < z and start + len(squash(wd[4])) > a]
            if boxes and r >= 0.5:
                rec["box"] = [round(min(b[0] for b in boxes), 1), round(min(b[1] for b in boxes), 1),
                              round(max(b[2] for b in boxes), 1), round(max(b[3] for b in boxes), 1)]
        results.append(rec)
    bb_entries = []
    for entry_id, headword, cls in conn.execute("select entry_id, headword, grammatical_class from lexical_entries where source='blue_book' order by entry_id"):
        forms = [r[0] for r in conn.execute("select distinct bb_skiri_form from blue_book_attestations where entry_id=?", (entry_id,))]
        bb_entries.append({"entry_id": entry_id, "headword_stored": headword, "printed_forms": forms,
                           "same_as_printed": any(unicodedata.normalize("NFC", f).strip() == headword for f in forms)})
    out = {"pdf_page_minus_book_page": offset, "attestation_rows": len(rows), "tally": dict(tally),
           "blue_book_only_entries": {"count": len(bb_entries), "with_a_printed_form_on_record": sum(1 for e in bb_entries if e["printed_forms"]),
                                      "headword_equals_a_printed_form": sum(1 for e in bb_entries if e["same_as_printed"]), "entries": bb_entries},
           "rows": results}
    (state.OUT / "bluebook_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("PDF page = book page %+d" % offset)
    state.out("attestation rows %d: %s" % (len(rows), dict(tally)))
    by_ctx = collections.defaultdict(collections.Counter)
    for r in results:
        by_ctx[r.get("context")][r["status"]] += 1
    for ctx, c in by_ctx.items():
        state.out("  %-18s %s" % (ctx, dict(c)))
    e = out["blue_book_only_entries"]
    state.out("Blue Book-only entries: %d; with a printed form on record: %d; headword identical to a printed form: %d" % (
        e["count"], e["with_a_printed_form_on_record"], e["headword_equals_a_printed_form"]))
    for r in [x for x in results if x["status"] == "found-nearly"][:25]:
        state.out("  nearly  p%s %-34s OCR: %s" % (r["page"], r["form"][:34], r.get("ocr_reads")))
    if args.crops:
        doubtful = [r for r in results if r["status"] in ("found-nearly",) and r.get("box")]
        folder = state.WORK / "bluebook"
        folder.mkdir(parents=True, exist_ok=True)
        zoom, per_sheet = 2.6, 12
        key = {}
        for s in range(0, len(doubtful), per_sheet):
            chunk = doubtful[s:s + per_sheet]
            sheet = fitz.open()
            pg = sheet.new_page(width=1100, height=per_sheet * 112 + 10)
            for i, r in enumerate(chunk):
                x0, y0, x1, y1 = r["box"]
                src_page = doc[r["pdf_page"] - 1]
                clip = fitz.Rect(max(0, x0 - 60), max(0, y0 - 8), min(src_page.rect.width, x1 + 200), min(src_page.rect.height, y1 + 8))
                y = 8 + i * 112
                cid = "B%03d" % (s + i + 1)
                key[cid] = r["id"]
                pg.insert_text((6, y + 30), cid, fontsize=16, color=(0, 0, 0.7))
                w_ = min(1000.0, clip.width * zoom)
                pg.show_pdf_page(fitz.Rect(70, y, 70 + w_, y + clip.height * (w_ / clip.width)), doc, r["pdf_page"] - 1, clip=clip)
            sheet[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(str(folder / ("nearly_%02d.png" % (s // per_sheet + 1))))
            sheet.close()
        (folder / "key.json").write_text(json.dumps(key), encoding="utf-8")
        state.out("crops of %d doubtful forms: %s" % (len(doubtful), folder.relative_to(state.ROOT).as_posix()))


if __name__ == "__main__":
    main()
