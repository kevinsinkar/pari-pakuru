#!/usr/bin/env python3
"""
Stage 4e: the abbreviation list against its text layer
======================================================

The chapter "Abbreviations and Sound Key" (six pages) has a text layer. The
stored copy is the table morpheme_abbreviations (164 rows) and
extracted_data/abbreviations.json. Each stored abbreviation, meaning and
morpheme form is looked for in the decoded text of the chapter.

    python scripts/source_audit/abbrev_compare.py     # writes abbreviations_differences.json
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_core as cc  # noqa: E402
import state  # noqa: E402


def main():
    spans = []
    for f in sorted((state.WORK / "textlayer").glob("abbrev_*.json")):
        page = json.loads(f.read_text(encoding="utf-8"))
        last = None
        for s in page["spans"]:
            key = (s["blk"], s["ln"])
            spans.append({"f": s["f"], "st": s["st"], "sz": s["sz"], "t": s["t"], "p": page["unit"], "b": s["b"], "nl": 1 if key != last else 0})
            last = key
    block = cc.Block(spans)
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    rows = conn.execute("select id, abbreviation, meaning, morpheme_form, notes from morpheme_abbreviations order by id").fetchall()
    diffs, checked, equal = [], 0, 0
    for rid, abbr, meaning, form, notes in rows:
        for field, value in (("abbreviation", abbr), ("meaning", meaning), ("morpheme_form", form)):
            if value is None or str(value).strip() in ("", "None"):
                continue
            checked += 1
            sk = cc.skeleton(str(value))
            if sk in block.sk:
                equal += 1
                continue
            # a list of forms is printed with its own punctuation; look for each form by itself
            parts = [p for p in cc.skeleton(str(value).replace(",", " ").replace("/", " ")).split() if p] if field == "morpheme_form" else []
            pieces = [cc.skeleton(p) for p in str(value).replace(",", " ").replace("/", " ").split()] if field == "morpheme_form" else []
            missing = [p for p in pieces if p and p not in block.sk]
            if field == "morpheme_form" and pieces and not missing:
                equal += 1
                continue
            ratio, a, z = cc.nearest(block, sk)
            diffs.append({"id": rid, "abbreviation": abbr, "field": field, "stored": value,
                          "printed_nearest": cc.tidy(block.printed(a, z)) if z > a else "", "ratio": round(ratio, 3),
                          "pieces_not_printed": missing, "grade": "text-layer", "severity": 1 if field == "morpheme_form" else 3})
    (state.OUT / "abbreviations_differences.json").write_text(json.dumps(
        {"rows": len(rows), "values_checked": checked, "values_printed": equal, "differences": diffs}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    state.out("abbreviation rows %d; values checked %d; printed as stored %d; differences %d" % (len(rows), checked, equal, len(diffs)))
    for d in diffs:
        state.out("  %-12s %-14s stored %-44r nearest %r" % (d["abbreviation"], d["field"], str(d["stored"])[:44], d["printed_nearest"][:50]))


if __name__ == "__main__":
    main()
