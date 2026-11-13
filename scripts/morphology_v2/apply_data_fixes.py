#!/usr/bin/env python3
"""List, and optionally apply, the data fixes proposed by the v2 morphology work.

    python scripts/morphology_v2/apply_data_fixes.py                 # dry run (default): list everything
    python scripts/morphology_v2/apply_data_fixes.py --kind page_number
    python scripts/morphology_v2/apply_data_fixes.py --apply --kind page_number   # writes to the database

Only fixes marked `auto_applicable` can be applied, and only with --apply.  At
present that is the `page_number` corrections.  Everything else (duplicate
rows, differences between the extraction and the printed page, letter-spaced
glosses) needs a person to look at the page first and is only ever listed.

--apply makes a timestamped backup of the database in ~/.pari_pakuru_backups
before it changes anything.
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DB_PATH, OUT, load_json, out  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write auto-applicable fixes to the database")
    ap.add_argument("--dry-run", action="store_true", help="list only (this is the default)")
    ap.add_argument("--kind", help="limit to one kind of fix")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()
    fixes = load_json(OUT / "proposed_data_fixes.json")["fixes"]
    if args.kind:
        fixes = [f for f in fixes if f["kind"] == args.kind]
    kinds = {}
    for f in fixes:
        kinds.setdefault(f["kind"], []).append(f)
    for kind, items in sorted(kinds.items()):
        auto = sum(1 for f in items if f.get("auto_applicable"))
        out("%s: %d proposed, %d auto-applicable" % (kind, len(items), auto))
        for f in items[:10]:
            target = f.get("entry_id") or ", ".join(f.get("entry_ids", []))
            out("    %s: %s -> %s" % (target, f.get("current"), f.get("proposed") or f.get("page_reads")))
        if len(items) > 10:
            out("    ... %d more in proposed_data_fixes.json" % (len(items) - 10))
    if not args.apply or args.dry_run:
        out("dry run: nothing was changed")
        return
    todo = [f for f in fixes if f.get("auto_applicable") and f["kind"] == "page_number"]
    if not todo:
        out("nothing auto-applicable in this selection")
        return
    backup_dir = Path.home() / ".pari_pakuru_backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / ("skiri_pawnee_backup_%s.db" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(args.db, backup)
    out("backup written to %s" % backup)
    conn = sqlite3.connect(args.db)
    with conn:
        for f in todo:
            conn.execute("update lexical_entries set page_number=? where entry_id=? and page_number=?",
                         (f["proposed"], f["entry_id"], f["current"]))
    out("applied %d page_number corrections" % len(todo))


if __name__ == "__main__":
    main()
