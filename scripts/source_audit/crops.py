#!/usr/bin/env python3
"""
Stage 3a: cut the differences out of the page, onto sheets for a blind reading
=============================================================================

For each difference chosen for reading, the printed line or lines it concerns
are cut from the page PDF (as vector graphics, so they stay sharp), the
stretch in question is underlined in red, and the crop gets an id (C0001 ...).
Crops are shuffled and packed onto sheets. A reader is given the sheets and
nothing else, and writes down the underlined text of each crop.

    python scripts/source_audit/crops.py s2e            # build sheets and the key

Which differences are read (the rest of a family is graded from the text layer
once the family's readings all come out the same way; see grade.py):
    every difference in a Pawnee form or its IPA, in English wording, in class,
    in a headword note, every printed stretch the database lacks, and every
    missing entry; a random 30 of each large mechanical family (stand-in
    characters in citations; spacing and line-break leftovers); and a random
    sample of 60 fields on which database and text layer agree.

Writes work/crops_<which>/sheet_NN.png and key.json. A sheet whose file exists
is not rebuilt unless --force is given.
"""
import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_core as cc  # noqa: E402
import state  # noqa: E402
import textlayer as tl  # noqa: E402

SCALE = 5.0
SHEET_W, SHEET_H = 1500.0, 1450.0
GAP, LABEL_H = 14.0, 24.0
SKIRI = ("headword", "phonetic_form", "additional_form", "form", "example.skiri", "cognate.form", "etymology")
SAMPLED = {"citation-standin": 30, "spacing-or-line-break": 30}


def base_field(field):
    return re.sub(r"\[.*\]", "", field)


def family(d):
    k, f = d["kind"], base_field(d["field"])
    if f == "column_position":
        return "column"
    if f == "page_number":
        return "page"
    if k == "citation-standin":
        return "citation-standin"
    if k in ("stored-keeps-line-break", "spacing", "hyphen"):
        return "spacing-or-line-break"
    if k == "printed-not-stored":
        return "printed-not-stored"
    if k == "phonetic-word-space-lost":
        return "phonetic-word-space"
    if k == "bracket-note-not-stored":
        return "bracket-note"
    if k == "class-differs":
        return "class"
    if k in ("stored-entry-not-printed", "printed-entry-not-stored"):
        return "entry"
    if f in SKIRI:
        return "skiri-letters"
    return "english-letters"


def pdf_for(which, page):
    if which == "s2e":
        return tl.S2E_DIR / ("page_%03d.pdf" % page)
    return tl.E2S_DIR / ("%03d_English to Skiri.pdf" % page)


class Margins:
    """Left margin of the text block of each page (pages alternate between two)."""

    def __init__(self, which):
        self.which, self.cache = which, {}

    def left(self, page):
        if page not in self.cache:
            d = json.loads((state.WORK / "textlayer" / ("%s_%03d.json" % (self.which, page))).read_text(encoding="utf-8"))
            xs = [s["b"][0] for s in d["spans"] if 56 < s["b"][1] < 652 and s["sz"] < 11.5 and s["t"].strip()]
            self.cache[page] = (min(xs) if xs else 59.0, d["width"], d["height"])
        return self.cache[page]


def regions(boxes, margins):
    """Group line boxes by page and column into crop rectangles: [(page, clip rect, [line boxes])]."""
    groups = collections.OrderedDict()
    for page, x0, y0, x1, y1 in boxes:
        left, width, height = margins.left(page)
        col = 0 if (x0 + x1) / 2 < left + 200 else 1
        groups.setdefault((page, col), []).append((x0, y0, x1, y1))
    out = []
    for (page, col), lines in groups.items():
        left, width, height = margins.left(page)
        col_x0, col_x1 = (left - 3, left + 200) if col == 0 else (left + 204, left + 408)
        x0 = min(l[0] for l in lines) - 26
        x1 = max(l[2] for l in lines) + 26
        if len(lines) > 1 or x1 - x0 < 110:
            mid = (x0 + x1) / 2
            x0, x1 = min(x0, mid - 62), max(x1, mid + 62)
        x0, x1 = max(col_x0, x0), min(col_x1, x1)
        y0 = min(l[1] for l in lines) - 4.5
        y1 = max(l[3] for l in lines) + 4.5
        out.append((page, fitz.Rect(x0, max(0, y0), x1, min(height, y1)), lines))
    return out


def choose(diffs, rng):
    chosen, counts = [], collections.Counter()
    by_family = collections.defaultdict(list)
    for i, d in enumerate(diffs):
        if d["class"] != "difference":
            continue
        by_family[family(d)].append(i)
    for fam, idx in by_family.items():
        counts[fam] = len(idx)
        if fam in ("column", "page"):
            continue
        if fam in SAMPLED and len(idx) > SAMPLED[fam]:
            idx = sorted(rng.sample(idx, SAMPLED[fam]))
        for i in idx:
            if diffs[i].get("boxes"):
                chosen.append(("difference", i))
    return chosen, counts


def agreement_sample(which, rng, n_each=20):
    """Fields on which database and text layer agree: (entry_id, field, value, boxes)."""
    import s2e_compare
    printed = [json.loads(line) for line in s2e_compare.PRINTED.open(encoding="utf-8")]
    pairs = [json.loads(line) for line in (state.WORK / "s2e_pairs.jsonl").open(encoding="utf-8")]
    db = s2e_compare.load_db(state.ROOT / "skiri_pawnee.db")
    rng.shuffle(pairs)
    picks = {"phonetic_form": [], "skiri": [], "english": []}
    for r in pairs:
        if all(len(v) >= n_each for v in picks.values()):
            break
        e, p = db[r["entry_id"]], printed[r["seq"] - 1]
        block = cc.Block(p["spans"])
        cands = []
        if e["phonetic_form"] and len(picks["phonetic_form"]) < n_each:
            cands.append(("phonetic_form", "phonetic_form", cc.stored_phonetic_as_printed(e["phonetic_form"]), "P"))
        if len(picks["skiri"]) < n_each:
            for f in e["forms"]:
                cands.append(("skiri", "form[%s]" % f["form_number"], "%s. %s" % (f["form_number"], f["skiri_form"]), "S"))
            for n, x in enumerate(e["examples"], 1):
                cands.append(("skiri", "example.skiri[%d]" % n, x["skiri_text"], "S"))
        if len(picks["english"]) < n_each:
            for g in e["glosses"]:
                cands.append(("english", "gloss[%s]" % g["sense_number"], g["definition"], "E"))
            for n, x in enumerate(e["examples"], 1):
                cands.append(("english", "example.english[%d]" % n, x["english_translation"], "E"))
        rng.shuffle(cands)
        for group, field, value, prefer in cands:
            if len(picks[group]) >= n_each or not value:
                continue
            sk = cc.skeleton(value)
            pos = block.find(sk, prefer, value)
            if pos is None or not block.whole_words(pos, pos + len(sk), value):
                continue
            if cc.tidy(value) not in cc.readings(block.printed(pos, pos + len(sk), value)):
                continue
            picks[group].append({"entry_id": e["entry_id"], "headword": e["headword"], "field": field, "value": value,
                                 "boxes": block.boxes(pos, pos + len(sk)), "page_file": p["page"]})
            break
    return [x for v in picks.values() for x in v]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("which", choices=["s2e"])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    folder = state.WORK / ("crops_%s" % args.which)
    folder.mkdir(parents=True, exist_ok=True)
    key_path = folder / "key.json"
    if key_path.exists() and not args.force:
        state.out("sheets already built (%s); use --force to rebuild" % folder.relative_to(state.ROOT).as_posix())
        return
    rng = random.Random(20261113)
    diffs = [json.loads(line) for line in (state.OUT / ("%s_differences.jsonl" % args.which)).open(encoding="utf-8")]
    chosen, counts = choose(diffs, rng)
    items = []
    for _, i in chosen:
        d = diffs[i]
        items.append({"what": "difference", "index": i, "entry_id": d["entry_id"], "headword": d["headword"], "field": d["field"],
                      "kind": d["kind"], "family": family(d), "stored": d["stored"], "printed": d["printed"], "boxes": d["boxes"]})
    for a in agreement_sample(args.which, rng):
        items.append({"what": "agreement", "entry_id": a["entry_id"], "headword": a["headword"], "field": a["field"],
                      "kind": "agree", "family": "agreement-sample", "stored": a["value"], "printed": a["value"], "boxes": a["boxes"]})
    rng.shuffle(items)
    margins = Margins(args.which)
    docs = {}
    key, sheet_no = {}, 0
    doc = page = None
    x = y = row_h = 0.0

    def new_sheet():
        nonlocal doc, page, x, y, row_h, sheet_no
        if doc is not None:
            close_sheet()
        sheet_no += 1
        doc = fitz.open()
        page = doc.new_page(width=SHEET_W, height=SHEET_H)
        x, y, row_h = GAP, GAP, 0.0

    def close_sheet():
        nonlocal doc
        # trim the sheet to what is used
        used_h = min(SHEET_H, y + row_h + GAP)
        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=fitz.Rect(0, 0, SHEET_W, used_h), alpha=False)
        pix.save(str(folder / ("sheet_%02d.png" % sheet_no)))
        doc.close()
        doc = None

    for old in folder.glob("sheet_*.png"):
        old.unlink()
    new_sheet()
    for n, item in enumerate(items, 1):
        cid = "C%04d" % n
        regs = regions(item["boxes"], margins)
        w = max(r[1].width for r in regs) * SCALE
        h = sum(r[1].height * SCALE + 6 for r in regs) + LABEL_H
        if x + w > SHEET_W - GAP and x > GAP:
            x, y, row_h = GAP, y + row_h + GAP, 0.0
        if y + h > SHEET_H - GAP:
            new_sheet()
        page.insert_text((x, y + 17), cid, fontsize=17, color=(0, 0, 0.7))
        cy = y + LABEL_H
        for pg, clip, lines in regs:
            path = pdf_for(args.which, pg)
            if path not in docs:
                docs[path] = fitz.open(str(path))
            target = fitz.Rect(x, cy, x + clip.width * SCALE, cy + clip.height * SCALE)
            page.draw_rect(target, color=(0.8, 0.8, 0.8), width=0.5)
            page.show_pdf_page(target, docs[path], 0, clip=clip)
            for lx0, ly0, lx1, ly1 in lines:
                ux0 = x + (max(lx0, clip.x0) - clip.x0) * SCALE
                ux1 = x + (min(lx1, clip.x1) - clip.x0) * SCALE
                uy = cy + (ly1 - clip.y0) * SCALE + 4
                page.draw_line((ux0, uy), (ux1, uy), color=(1, 0, 0), width=2.2)
            cy += clip.height * SCALE + 6
        key[cid] = dict(item, sheet=sheet_no)
        x += w + GAP * 2
        row_h = max(row_h, h)
    close_sheet()
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    fam = collections.Counter(v["family"] for v in key.values())
    state.out("differences by family: %s" % dict(counts))
    state.out("crops: %d on %d sheets; by family: %s" % (len(key), sheet_no, dict(fam)))
    per_sheet = collections.Counter(v["sheet"] for v in key.values())
    state.out("crops per sheet: %s" % [per_sheet[i] for i in range(1, sheet_no + 1)])


if __name__ == "__main__":
    main()
