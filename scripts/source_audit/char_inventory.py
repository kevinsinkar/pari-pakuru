#!/usr/bin/env python3
"""
Stage 1a: every stand-in character in the text layer, by font
=============================================================

Lists every (font family, character) pair that is not a plain ASCII letter,
digit or common punctuation mark, with how often it occurs and where. The
places are what the contact sheets (char_sheets.py) are cut from.

    python scripts/source_audit/char_inventory.py

Writes work/char_inventory.json. Reads all 471 text-layer pages; takes a minute.
"""
import collections
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import textlayer as tl  # noqa: E402

PLAIN = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?()[]{}<>/-'\"=+*&%#@_|\\~`^$\t\n")
KEEP_PER_PAIR = 400          # occurrences remembered per pair, to sample from
# ASCII characters that are looked at all the same: a custom font can draw them as something else
ALSO = {("PAdothyphen", "-"), ("PAdothyphen", "."), ("PAdothyphen", ","), ("PlainsArial", "?"), ("PlainsArial", "'"),
        ("PlainsArial", "!"), ("PlainsArial", "b"), ("PlainsArial", "d"), ("PlainsArial", "j"), ("LucidaSansUnicode", "?"),
        ("TruteauGaramond", "'"), ("CSNPdothyphen", "-")}


def main():
    units = tl.sources()
    counts = collections.Counter()
    pages = collections.defaultdict(set)
    places = collections.defaultdict(list)
    fonts = collections.Counter()
    rng = random.Random(20261113)
    for i, (source, unit, pdf, idx) in enumerate(units, 1):
        for font, size, flags, ch, bbox, b, l, s in tl.page_chars(pdf, idx):
            fam, style = tl.family(font)
            fonts[(fam, style, size)] += 1
            key = (fam, ch)
            if ch in PLAIN and key not in ALSO:
                continue
            counts[key] += 1
            pages[key].add((source, unit))
            where = [source, unit, [round(v, 2) for v in bbox], style, size]
            if len(places[key]) < KEEP_PER_PAIR:
                places[key].append(where)
            else:                               # reservoir sampling, so the sample is spread over the book
                j = rng.randrange(counts[key])
                if j < KEEP_PER_PAIR:
                    places[key][j] = where
        if i % 100 == 0 or i == len(units):
            state.out("  %d of %d pages read" % (i, len(units)))
    inventory = []
    for (fam, ch), n in sorted(counts.items(), key=lambda kv: (kv[0][0], -kv[1])):
        inventory.append({"family": fam, "char": ch, "code": "U+%04X" % ord(ch), "count": n,
                          "pages": len(pages[(fam, ch)]), "places": places[(fam, ch)]})
    data = {"pages_read": len(units),
            "fonts": [{"family": f, "style": st, "size": sz, "chars": n} for (f, st, sz), n in fonts.most_common()],
            "pairs": inventory}
    state.WORK.mkdir(parents=True, exist_ok=True)
    (state.WORK / "char_inventory.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    state.out("font families: %s" % sorted({f["family"] for f in data["fonts"]}))
    state.out("stand-in pairs: %d" % len(inventory))
    by_family = collections.defaultdict(list)
    for item in inventory:
        by_family[item["family"]].append("%s(%s)x%d" % (item["char"], item["code"][2:], item["count"]))
    for fam, items in by_family.items():
        state.out("%-18s %d pairs: %s" % (fam, len(items), "  ".join(items)))


if __name__ == "__main__":
    main()
