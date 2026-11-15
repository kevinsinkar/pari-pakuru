#!/usr/bin/env python3
"""The engines review: its test sets, and the Stage 1 and 2 measurements.

    python scripts/engines_review/run_all.py --check    # are the test sets still what the manifest says? (works today)
    python scripts/engines_review/run_all.py            # every number of Stages 1 and 2 again (see below)

The measurements were made on the engines as they stood in commit 814e8cc. Stage 4
then withdrew four engine files and repaired or rebuilt the others, so the plain
run now stops with an explanation and writes nothing: the record in
reports/engines_review/data/ is the evidence the decisions rest on. On a tree with
the reviewed files in place it runs as before: the Stage 1 trace, the test sets,
then one measurement per engine and the measurement of use. A second run gives
the same bytes. Nothing here changes an engine, the database or a data file.

What can be measured today is the repaired person derivation, on the open half of
its test: python scripts/engines_review/person_forms_repair.py --open
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    ("stage1_trace.py", "Stage 1: where the engines' test forms and stored values come from"),
    ("build_test_sets.py", "Stage 2: the test sets, from attested forms"),
    ("measure_conjugation.py", "conjugation engine and accent rules"),
    ("measure_sound_changes.py", "sound-change engine, beside the seam engine"),
    ("measure_form2.py", "form 2 predictor"),
    ("measure_person_forms.py", "person and mode derivation"),
    ("measure_possession.py", "possession engine"),
    ("measure_use.py", "sentence templates, and what the app shows"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        raise SystemExit(subprocess.call([sys.executable, str(HERE / "build_test_sets.py"), "--verify"]))
    sys.path.insert(0, str(HERE))
    from common import require_reviewed_state
    require_reviewed_state(__file__)
    for script, what in STEPS:
        print("\n=== %s (%s)" % (what, script), flush=True)
        code = subprocess.call([sys.executable, str(HERE / script)])
        if code:
            raise SystemExit("stopped: %s ended with code %d" % (script, code))
    print("\nall steps done; results are in reports/engines_review/data/")


if __name__ == "__main__":
    main()
