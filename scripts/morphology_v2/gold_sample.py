#!/usr/bin/env python3
"""Draw the G2 hand-check sample (seeded, stratified) and split off the held-out half.

Run ONCE, before any segmentation heuristics are written.  The sample depends
only on the database, the v1 confidence labels and the fixed seed, so it can be
regenerated and compared byte for byte.

    python scripts/morphology_v2/gold_sample.py            # writes gold/g2_sample.json
    python scripts/morphology_v2/gold_sample.py --check    # verify the saved sample
"""
import argparse
import random
from collections import defaultdict

from common import (GOLD, SEED, V1, connect, dump_json, headword_key, load_json,
                    load_jsonl, load_page_index, out, pdf_file_for, syllable_count)

# entries per (class group, v1 stratum) cell
ALLOC = {"high": 7, "medium": 6, "low": 4, "no_etymology": 3}
N_SHORT = 20
BATCH = 20


def class_group(gc):
    gc = (gc or "").split(",")[0].strip()
    if gc.startswith("N"):
        return "N"
    if gc in ("VT", "VI", "VD"):
        return gc
    return "other"


def build():
    conn = connect()
    v1 = {r["entry_id"]: r for r in load_jsonl(V1 / "segmentation_log.jsonl")}
    idx = load_page_index()
    pool = []
    for r in conn.execute("""select entry_id, headword, grammatical_class, verb_class,
                                    page_number, column_position, source
                             from lexical_entries order by entry_id"""):
        if r["source"] == "blue_book" or r["page_number"] is None:
            continue                       # no Parks page to check against
        f, book_page, verified = pdf_file_for(r["page_number"], r["headword"], idx)
        if not verified:
            continue                       # page could not be confirmed from the text layer
        v = v1.get(r["entry_id"], {})
        stratum = "no_etymology" if v.get("method") == "no_etymology" else v.get("confidence", "low")
        pool.append({"entry_id": r["entry_id"], "headword": r["headword"],
                     "grammatical_class": r["grammatical_class"], "verb_class": r["verb_class"],
                     "pdf_file": f, "book_page": book_page, "column": r["column_position"],
                     "class_group": class_group(r["grammatical_class"]), "v1_stratum": stratum,
                     "syllables": syllable_count(headword_key(r["headword"]))})
    rng = random.Random(SEED)
    cells = defaultdict(list)
    for p in pool:
        cells[(p["class_group"], p["v1_stratum"])].append(p)
    chosen, taken = [], set()
    for key in sorted(cells):
        items = sorted(cells[key], key=lambda p: p["entry_id"])
        rng.shuffle(items)
        for p in items[:ALLOC[key[1]]]:
            p = dict(p, stratum_cell="%s/%s" % key, short_stratum=False)
            chosen.append(p)
            taken.add(p["entry_id"])
    short = sorted((p for p in pool if p["syllables"] <= 2 and p["entry_id"] not in taken),
                   key=lambda p: p["entry_id"])
    rng.shuffle(short)
    for p in short[:N_SHORT]:
        chosen.append(dict(p, stratum_cell="short/%s" % p["class_group"], short_stratum=True))
    # held-out half: alternate within each cell after a seeded shuffle
    by_cell = defaultdict(list)
    for p in chosen:
        by_cell[p["stratum_cell"]].append(p)
    flip = 0
    for key in sorted(by_cell):
        items = by_cell[key]
        rng.shuffle(items)
        for p in items:
            p["split"] = "heldout" if flip % 2 else "dev"
            flip += 1
    chosen.sort(key=lambda p: (p["pdf_file"], p["entry_id"]))
    for i, p in enumerate(chosen):
        p["batch"] = i // BATCH + 1
    return {"seed": SEED, "pool_size": len(pool), "n": len(chosen),
            "allocation": ALLOC, "n_short": N_SHORT, "entries": chosen}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the saved sample is reproducible")
    args = ap.parse_args()
    sample = build()
    path = GOLD / "g2_sample.json"
    if args.check:
        saved = load_json(path)
        same = saved["entries"] == sample["entries"]
        out("g2_sample reproducible: %s (%d entries)" % (same, len(saved["entries"])))
        raise SystemExit(0 if same else 1)
    dump_json(path, sample)
    n_held = sum(1 for p in sample["entries"] if p["split"] == "heldout")
    out("pool %d, sampled %d (dev %d / heldout %d), pages %d, batches %d" % (
        sample["pool_size"], sample["n"], sample["n"] - n_held, n_held,
        len({p["pdf_file"] for p in sample["entries"]}), sample["entries"][-1]["batch"]))
    # annotator work lists: no DB etymology, no v1 analysis, no split label
    for b in range(1, sample["entries"][-1]["batch"] + 1):
        items = [{"entry_id": p["entry_id"], "headword": p["headword"],
                  "grammatical_class": p["grammatical_class"], "pdf_file": p["pdf_file"],
                  "book_page": p["book_page"], "column": p["column"]}
                 for p in sample["entries"] if p["batch"] == b]
        dump_json(GOLD / "g2_batches" / ("batch_%d.json" % b), items)


if __name__ == "__main__":
    main()
