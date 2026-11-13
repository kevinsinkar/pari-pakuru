#!/usr/bin/env python3
"""
Stage 0 of the source-fidelity audit: the baseline
==================================================

Records what the audit started from, so that at the end it can be shown that
the audit changed none of it:

  - a SHA-256 of every input: each table of the database (through the text
    dump in DB/dump/), the two dictionary JSON files, every file in
    extracted_data/, every source PDF and the Blue Book text;
  - the result of each existing test suite.

    python scripts/source_audit/baseline.py            # write baseline.json (hashes + test suites)
    python scripts/source_audit/baseline.py --check    # compare today's inputs with baseline.json
    python scripts/source_audit/baseline.py --no-tests # hashes only
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state  # noqa: E402
import db_dump  # noqa: E402

ROOT = state.ROOT
BASELINE = state.OUT / "baseline.json"
PY = sys.executable

SUITES = [
    ("sound-change rules", ["scripts/sound_changes.py", "--test"]),
    ("person and mode derivation", ["scripts/person_forms.py", "--validate-appendix"]),
    ("sentence templates", ["scripts/sentence_templates.py", "test"]),
    ("respelling and audit code", ["scripts/test_phase_1_1.py"]),
    ("database schema and query library", ["DB/test_schema.py"]),
    ("word-construction unit tests", ["-m", "unittest", "discover", "-s", "scripts/morphology_v2", "-p", "test_*.py"]),
    ("word-construction gold sets unchanged", ["scripts/morphology_v2/gold_build.py", "--verify"]),
    ("every Pawnee form in the guide has a source", ["scripts/morphology_v2/check_forms.py"]),
    ("noun possession", ["scripts/possession_engine.py", "--test"]),
    ("conjugation engine against Appendix 1 (a measurement)", ["scripts/morpheme_inventory.py", "--validate"]),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_hashes():
    hashes = {}
    conn = db_dump.connect_ro(db_dump.DB)
    files = db_dump.render(conn)
    conn.close()
    for table, meta in json.loads(files["_manifest.json"])["tables"].items():
        hashes["db:" + table] = "%s rows %d" % (meta["sha256"], meta["rows"])
    hashes["db:_schema"] = hashlib.sha256(files["_schema.sql"].encode("utf-8")).hexdigest()
    groups = [
        ("Dictionary Data", "*.json"),
        ("Dictionary Data/Dictionary PDF Split", "*"),
        ("Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH", "*.pdf"),
        ("Dictionary Data/split_pdf_pages_ENGLISH_TO_SKIRI", "*.pdf"),
        ("extracted_data", "*.json"),
        ("pari pakuru", "*.pdf"),
        ("pari pakuru", "*.txt"),
        ("pari pakuru/Blue Book - Pari Pakuru - split", "*.pdf"),
        ("curriculum", "flashcard_sets.json"),
    ]
    for folder, pattern in groups:
        for p in sorted((ROOT / folder).glob(pattern)):
            if p.is_file():
                hashes[p.relative_to(ROOT).as_posix()] = sha(p)
    return hashes


def run_suites():
    results = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for name, cmd in SUITES:
        try:
            r = subprocess.run([PY] + cmd, cwd=str(ROOT), env=env, capture_output=True, timeout=1200)
            text = (r.stdout + b"\n" + r.stderr).decode("utf-8", errors="replace")
            tail = [line.strip() for line in text.splitlines() if line.strip()][-4:]
            results.append({"check": name, "command": " ".join(cmd), "exit_code": r.returncode, "last_lines": tail})
        except subprocess.TimeoutExpired:
            results.append({"check": name, "command": " ".join(cmd), "exit_code": None, "last_lines": ["timed out"]})
        state.out("  %-52s exit %s   %s" % (name, results[-1]["exit_code"], results[-1]["last_lines"][-1][:90] if results[-1]["last_lines"] else ""))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="compare today's inputs with baseline.json; write nothing")
    ap.add_argument("--no-tests", action="store_true")
    args = ap.parse_args()

    hashes = input_hashes()
    if args.check:
        base = json.loads(BASELINE.read_text(encoding="utf-8"))["inputs"]
        changed = sorted(k for k in base if hashes.get(k) != base[k])
        new = sorted(k for k in hashes if k not in base)
        state.out("inputs in baseline: %d; today: %d" % (len(base), len(hashes)))
        for k in changed:
            state.out("  CHANGED or missing: " + k)
        for k in new:
            state.out("  new: " + k)
        state.out("unchanged since the baseline" if not (changed or new) else "inputs have changed since the baseline")
        sys.exit(1 if (changed or new) else 0)

    data = {"written": state.now(), "inputs": hashes}
    state.out("inputs hashed: %d (database tables %d, files %d)" % (
        len(hashes), sum(k.startswith("db:") for k in hashes), sum(not k.startswith("db:") for k in hashes)))
    if not args.no_tests:
        data["test_suites"] = run_suites()
    state.OUT.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("written: " + BASELINE.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
