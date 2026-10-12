#!/usr/bin/env python3
"""
Freeze the flashcard curriculum to a versioned data file (audit item B4).

The weekly sets were previously recomputed from the live DB on every build,
so any DB change silently renumbered weeks and misattached learners'
localStorage progress. This script snapshots the generated sets to
curriculum/flashcard_sets.json; web/flashcards.py loads that file when it
exists, so the curriculum only changes when this script is deliberately
re-run (an editorial act, reviewable in git diff).

Usage:
    python scripts/freeze_flashcard_sets.py            # dry run (summary only)
    python scripts/freeze_flashcard_sets.py --apply    # write the file
"""

import argparse
import dataclasses
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from web.flashcards import generate_all_sets

OUT_PATH = PROJECT_ROOT / "curriculum" / "flashcard_sets.json"


def out(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def main():
    parser = argparse.ArgumentParser(description="Freeze flashcard curriculum")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "skiri_pawnee.db"))
    parser.add_argument("--apply", action="store_true",
                        help="Write curriculum/flashcard_sets.json")
    args = parser.parse_args()

    sets = generate_all_sets(args.db)
    payload = {
        "_comment": (
            "Frozen flashcard curriculum. Learner progress is keyed to these "
            "week numbers, so do NOT regenerate casually - re-run "
            "scripts/freeze_flashcard_sets.py --apply only for a deliberate, "
            "reviewed curriculum change."
        ),
        "version": 1,
        "frozen_date": date.today().isoformat(),
        "weeks": [
            {
                "week": s.week,
                "category": s.category,
                "category_label": s.category_label,
                "cards": [dataclasses.asdict(c) for c in s.cards],
            }
            for s in sets
        ],
    }

    total = sum(len(w["cards"]) for w in payload["weeks"])
    out(f"{'[APPLY]' if args.apply else '[DRY RUN]'} "
        f"{len(payload['weeks'])} weeks, {total} cards")

    if OUT_PATH.exists():
        old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        old_weeks = {w["week"]: w for w in old.get("weeks", [])}
        changed = []
        for w in payload["weeks"]:
            ow = old_weeks.get(w["week"])
            if not ow:
                changed.append(f"week {w['week']}: new")
                continue
            old_ids = [c["entry_id"] for c in ow["cards"]]
            new_ids = [c["entry_id"] for c in w["cards"]]
            if old_ids != new_ids:
                changed.append(f"week {w['week']}: card list changed "
                               f"({len(old_ids)} -> {len(new_ids)})")
        if changed:
            out("Differences vs existing freeze:")
            for c in changed:
                out(f"  {c}")
        else:
            out("No set-membership changes vs existing freeze.")

    if args.apply:
        OUT_PATH.parent.mkdir(exist_ok=True)
        OUT_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1),
            encoding="utf-8")
        out(f"Wrote {OUT_PATH}")
    else:
        out("(re-run with --apply to write)")


if __name__ == "__main__":
    main()
