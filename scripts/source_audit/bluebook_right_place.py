#!/usr/bin/env python3
"""
The open Blue Book forms, looked for at their own place on the page (2026-11-14)
===============================================================================

Two blind readings left 42 Blue Book forms open. For about half of them both
readers had read a longer or another word: the red line had been drawn at the
first place on the page where the OCR text holds the stored letters, and a
short form ("rakis", "Tuks•at.") also occurs inside longer words ("tirakis",
"Tatuks•at."). The English stored with the row shows it: the stored row says
"He, she went", the readers found "I went" beside the word they read.

This script finds the row's own place and has it read:

    python scripts/source_audit/bluebook_right_place.py           # find the places, cut the crops (work/bluebook_third/)
    python scripts/source_audit/bluebook_right_place.py --grade   # judge the reading; writes bluebook_right_place.json

A place is taken as the row's own when
    the row's English follows   the stored letters stand in the OCR text directly before the English stored
                                with the row, or
    the only whole word         the stored letters stand once on the page as a word by itself, and the blind
                                reader then finds the row's English beside it (checked by --grade)
and it is not the place that was read before.

The reading is expected in reports/source_audit_2026-11/blind_readings/bluebook_right_place.json, a JSON object
{crop id: {"form": ..., "english": ..., "pawnee": true/false, "note": ...}}, from a reader who sees only the sheets.

It is judged as the first reading of all the Blue Book forms was (decide() in scripts/apply_bluebook_scan_fixes.py):
where the reader's letters are the stored letters, the accents, raised dots and apostrophes the reader saw are taken,
because the OCR cannot see them; where the letters differ, one reading stands against one and the form stays open.
scripts/apply_bluebook_scan_fixes.py takes the verdicts "settled at its own place".
"""
import argparse
import collections
import difflib
import json
import sqlite3
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state  # noqa: E402
import bluebook_second_look as second_look  # noqa: E402
from bluebook_check import PDF  # noqa: E402
from bluebook_crops import squash  # noqa: E402

FOLDER = state.WORK / "bluebook_third"
READING = state.OUT / "blind_readings" / "bluebook_right_place.json"
RECORD = state.OUT / "bluebook_right_place.json"


def open_rows():
    """The forms two readings left open, each with the English stored with its row."""
    from apply_bluebook_scan_fixes import same_place
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    out = []
    for r in json.loads((state.OUT / "bluebook_second_look.json").read_text(encoding="utf-8"))["rows"]:
        if r["verdict"] == "second reading agrees with the stored form":
            continue
        if r["verdict"] == "two readings agree" and r.get("pawnee", True) and same_place(r["stored_form"], r["second_reading"]):
            continue
        english = ""
        for aid in r.get("attestation_ids") or []:
            row = conn.execute("select bb_english from blue_book_attestations where id = ?", (aid,)).fetchone()
            if row and row[0]:
                english = row[0]
                break
        if not english and r.get("entry_id"):
            row = conn.execute("select definition from glosses where entry_id = ? order by sense_number", (r["entry_id"],)).fetchone()
            english = row[0] if row else ""
        out.append({"first_crop": r["first_crop"], "second_crop": r["crop"], "page": r["page"], "old_box": r["box"],
                    "stored_form": r["stored_form"], "stored_english": english, "attestation_ids": r.get("attestation_ids") or [],
                    "entry_id": r.get("entry_id"), "earlier_verdict": r["verdict"], "earlier_reading": r["second_reading"]})
    return out


def place(doc, row):
    """(box, how) of the row's own place on its page, or (None, why not)."""
    needle, english = squash(row["stored_form"]), squash(row["stored_english"])
    words = [w for w in doc[row["page"] - 1].get_text("words") if squash(w[4])]
    text, starts = "", []
    for w in words:
        starts.append(len(text))
        text += squash(w[4])
    hits, i = [], text.find(needle) if needle else -1
    while i >= 0:
        hit = [w for s, w in zip(starts, words) if s < i + len(needle) and s + len(squash(w[4])) > i]
        box = [min(w[0] for w in hit), min(w[1] for w in hit), max(w[2] for w in hit), max(w[3] for w in hit)]
        after = text[i + len(needle):i + len(needle) + len(english)]
        follows = bool(english) and difflib.SequenceMatcher(None, after, english, autojunk=False).ratio() >= 0.9
        hits.append((box, follows, "".join(squash(w[4]) for w in hit) == needle))
        i = text.find(needle, i + 1)
    same = lambda box: row["old_box"] and all(abs(a - b) < 1.0 for a, b in zip(box, row["old_box"]))
    by_english = [h for h in hits if h[1]]
    whole = [h for h in hits if h[2]]
    if len(by_english) == 1:
        box, how = by_english[0][0], "the row's English follows"
    elif len(whole) == 1:
        box, how = whole[0][0], "the only whole word"
    else:
        return None, "%d places in the OCR text, none singled out" % len(hits)
    if same(box):
        return None, "its own place is the one already read"
    return box, how


def sheets():
    doc = fitz.open(str(PDF))
    items, skipped = [], collections.Counter()
    for row in open_rows():
        box, how = place(doc, row)
        if box is None:
            skipped[how.split(" places")[-1].strip() if "places" in how else how] += 1
            continue
        items.append(dict(row, box=box, placed_by=how))
    key = second_look.draw(items, FOLDER, "bb3", "T")
    state.out("open forms: %d; found at another place: %d (%s); crops on %d sheets in %s" % (
        len(open_rows()), len(key), dict(collections.Counter(i["placed_by"] for i in items)),
        (len(items) + second_look.PER_SHEET - 1) // second_look.PER_SHEET, FOLDER.relative_to(state.ROOT).as_posix()))
    state.out("not cut: %s" % dict(skipped))


def english_agrees(read, stored):
    a, b = squash(read or ""), squash(stored or "")
    if not a or not b:
        return False
    short, long_ = sorted((a, b), key=len)
    return (len(short) >= 4 and short in long_) or difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.85


def grade():
    from apply_bluebook_scan_fixes import clean, decide
    key = json.loads((FOLDER / "key.json").read_text(encoding="utf-8"))
    reading = json.loads(READING.read_text(encoding="utf-8"))
    tally, rows = collections.Counter(), []
    for cid, k in sorted(key.items()):
        r = reading.get(cid)
        if r is None:
            tally["not read"] += 1
            continue
        form = clean(r.get("form", ""))
        placed = k["placed_by"] == "the row's English follows" or english_agrees(r.get("english"), k["stored_english"])
        new, kind = decide(k["stored_form"], form)
        if not r.get("pawnee", True):
            verdict = "not Pawnee text at that place"
        elif not placed and kind == "same":
            # the stored letters stand once on the page as a word, and the reader read them there as stored,
            # with no accent: there is nothing to change, whatever stands beside it
            verdict = "stored form confirmed at its own place"
        elif not placed:
            verdict = "place not confirmed by the English"
        elif new is not None:
            verdict = "settled at its own place"
        elif kind == "same":
            verdict = "stored form confirmed at its own place"
        else:
            verdict = kind                      # letters differ, reader unsure, capitals differ, crop shows something else
        tally[verdict] += 1
        rows.append(dict(k, crop=cid, reading=form, english_read=r.get("english", ""), pawnee=r.get("pawnee", True),
                         note=r.get("note", ""), kind=kind, new_form=new, verdict=verdict))
    RECORD.write_text(json.dumps({"crops": len(key), "tally": dict(tally), "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8", newline="\n")
    state.out("crops %d; %s" % (len(key), dict(tally)))
    for r in rows:
        state.out("  %s p. %-4s %-26r read %-28r %s%s" % (r["crop"], r["page"], r["stored_form"], r["reading"], r["verdict"],
                                                        (" (%s)" % r["kind"]) if r["new_form"] else ""))


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
