#!/usr/bin/env python3
"""Run the pipeline twice and confirm that every output file is byte-identical.

    python scripts/morphology_v2/check_determinism.py

Writes curriculum/roots_v2/determinism.json and exits 1 if any file differs.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import OUT, ROOT, dump_json, out, sha256  # noqa: E402

FILES = ["evidence.jsonl", "roots.json", "affixes.json", "decisions.json", "coverage.json", "stats.json",
         "construction_guide.md", "learning_path.md", "review_queue.md"]


def run_once():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "run.py"), "--guide"],
                   cwd=str(ROOT), env=env, check=True, capture_output=True)
    return {f: sha256(OUT / f) for f in FILES}


def main():
    first = run_once()
    second = run_once()
    different = sorted(f for f in FILES if first[f] != second[f])
    dump_json(OUT / "determinism.json", {"identical": not different, "different": different, "files": second})
    for f in FILES:
        out("%s  %s  %s" % (second[f][:16], "same" if first[f] == second[f] else "DIFFERS", f))
    out("identical" if not different else "%d files differ" % len(different))
    raise SystemExit(1 if different else 0)


if __name__ == "__main__":
    main()
