#!/usr/bin/env python3
"""
Look at the differences the audit found
=======================================

    python scripts/source_audit/show.py s2e                          # counts by field and kind
    python scripts/source_audit/show.py s2e --kind spacing --field phonetic_form --limit 20
    python scripts/source_audit/show.py s2e --entry SK-huupirit-p51-0850
    python scripts/source_audit/show.py s2e --residue 60             # the most frequent printed-not-stored texts

The first argument names the comparison: s2e or e2s.
"""
import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("which", choices=["s2e", "e2s"])
    ap.add_argument("--kind")
    ap.add_argument("--field")
    ap.add_argument("--entry")
    ap.add_argument("--grade")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--residue", type=int, default=0)
    ap.add_argument("--random", action="store_true", help="a random selection instead of the first ones")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()
    path = Path(args.file) if args.file else state.OUT / ("%s_differences.jsonl" % args.which)
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    if args.residue:
        c = collections.Counter(r["printed"] for r in rows if r["kind"] == "printed-not-stored")
        state.out("%d printed-not-stored stretches, %d distinct" % (sum(c.values()), len(c)))
        for text, n in c.most_common(args.residue):
            state.out("%6d  %r" % (n, text[:110]))
        return
    sel = rows
    if args.kind:
        sel = [r for r in sel if args.kind == r["kind"] or (args.kind.endswith("*") and r["kind"].startswith(args.kind[:-1]))]
    if args.field:
        sel = [r for r in sel if re.sub(r"\[.*\]", "", r["field"]) == args.field]
    if args.entry:
        sel = [r for r in sel if r["entry_id"] == args.entry]
    if args.grade:
        sel = [r for r in sel if r.get("grade") == args.grade]
    if not (args.kind or args.field or args.entry or args.grade):
        c = collections.Counter((re.sub(r"\[.*\]", "", r["field"]), r["kind"]) for r in rows)
        for (field, kind), n in c.most_common():
            state.out("%-26s %-46s %d" % (field, kind, n))
        return
    state.out("%d differences selected" % len(sel))
    if args.random:
        random.Random(7).shuffle(sel)
    for r in sel[:args.limit]:
        state.out("%s  p%s  %s  [%s | %s]" % (r["entry_id"], r["page_file"], r["headword"], r["field"], r["kind"]))
        state.out("    stored : %s" % r["stored"])
        state.out("    printed: %s" % r["printed"])
        if r.get("edits"):
            state.out("    edits  : %s" % "  ".join("%s>%s" % (a or "∅", b or "∅") for a, b in r["edits"]))


if __name__ == "__main__":
    main()
