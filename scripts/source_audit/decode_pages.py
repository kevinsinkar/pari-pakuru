#!/usr/bin/env python3
"""
Stage 1e: the whole text layer, decoded with the verified table
===============================================================

One file per page in work/textlayer/: every span with its font family, style,
size, position, the raw text and the text as printed. This is the second
reading that stages 2 and 6 compare the database with.

    python scripts/source_audit/decode_pages.py            # pages not yet done
    python scripts/source_audit/decode_pages.py --force    # all pages again

A page whose file exists is skipped, so an interrupted run can be continued.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chartable  # noqa: E402
import state  # noqa: E402
import textlayer as tl  # noqa: E402

OUT = state.WORK / "textlayer"


def page_file(source, unit):
    return OUT / ("%s_%03d.json" % (source, unit))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    units = tl.sources()
    done = skipped = 0
    unmapped = collections.Counter()
    for source, unit, pdf, idx in units:
        f = page_file(source, unit)
        if f.exists() and not args.force:
            skipped += 1
            continue
        spans, (w, h) = tl.page_spans(pdf, idx)
        rows = []
        for sp in spans:
            fam, style = tl.family(sp["font"])
            text = chartable.decode(sp["text"], sp["font"])
            if "⟦" in text:
                for i, ch in enumerate(text):
                    if ch == "⟦":
                        unmapped[(fam, text[i + 1])] += 1
            rows.append({"f": fam, "st": style, "sz": sp["size"], "b": sp["bbox"], "blk": sp["block"], "ln": sp["line"],
                         "raw": sp["text"], "t": text})
        f.write_text(json.dumps({"source": source, "unit": unit, "pdf": pdf.relative_to(state.ROOT).as_posix(),
                                 "page_index": idx, "width": w, "height": h, "spans": rows}, ensure_ascii=False), encoding="utf-8")
        done += 1
        if done % 100 == 0:
            state.out("  %d pages decoded" % done)
    state.out("decoded %d pages, skipped %d already done, of %d" % (done, skipped, len(units)))
    if unmapped:
        state.out("codes with no entry in the table (kept, marked): %s" % dict(unmapped))
    else:
        state.out("every non-ASCII code had an entry in the table")


if __name__ == "__main__":
    main()
