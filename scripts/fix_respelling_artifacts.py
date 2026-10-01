#!/usr/bin/env python3
"""
Fix respelling artifacts: stray '?' markers in simplified_pronunciation.

The respelling generator emitted '?X?' for characters missing from its
inventory: the Parks stem-alternation slash (68 entries, e.g.
'kees?/?kihs') and the marginal consonant n (1 entry, 'rawa, nawa').
The generator has been patched (see respell_and_normalize.py); this
script regenerates the affected values from phonetic_form in both the
SQLite DB and the source respelled JSON.

Safety: a regenerated value is only applied when it equals the old
value with the '?' markers removed — i.e. the fix changes nothing but
the artifact. Anything else is reported and skipped.

Usage:
    python scripts/fix_respelling_artifacts.py            # dry run (default)
    python scripts/fix_respelling_artifacts.py --apply    # write changes
"""

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from respell_and_normalize import generate_simplified_pronunciation

BACKUP_DIR = Path.home() / ".pari_pakuru_backups"


def out(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def regenerate(old: str, phonetic_form: str, label: str, changes: list) -> str | None:
    """Return the regenerated value if it safely fixes `old`, else None."""
    if not phonetic_form:
        out(f"  [SKIP] {label}: no phonetic_form to regenerate from")
        return None
    new, warnings = generate_simplified_pronunciation(phonetic_form)
    if not new:
        out(f"  [SKIP] {label}: regeneration failed ({warnings})")
        return None
    if "?" in new:
        out(f"  [SKIP] {label}: still contains '?' after regeneration: {new!r}")
        return None
    if old.replace("?", "") != new:
        out(f"  [SKIP] {label}: regenerated value differs beyond artifact removal")
        out(f"         old={old!r}  new={new!r}")
        return None
    changes.append((label, old, new))
    return new


def fix_db(db_path: Path, apply: bool) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT entry_id, phonetic_form, simplified_pronunciation "
        "FROM lexical_entries WHERE simplified_pronunciation LIKE '%?%'"
    )
    rows = cur.fetchall()
    out(f"\n[DB] {len(rows)} entries with '?' in simplified_pronunciation")

    changes: list = []
    for r in rows:
        new = regenerate(r["simplified_pronunciation"], r["phonetic_form"],
                         r["entry_id"], changes)
        if new and apply:
            cur.execute(
                "UPDATE lexical_entries SET simplified_pronunciation = ? "
                "WHERE entry_id = ?",
                (new, r["entry_id"]),
            )
    if apply:
        conn.commit()
    conn.close()

    for label, old, new in changes[:10]:
        out(f"  {label}: {old!r} -> {new!r}")
    if len(changes) > 10:
        out(f"  ... and {len(changes) - 10} more")
    out(f"[DB] {'applied' if apply else 'would fix'}: {len(changes)}/{len(rows)}")
    return len(changes)


def fix_json(json_path: Path, apply: bool) -> int:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    changes: list = []

    def walk(obj, entry_id):
        if isinstance(obj, dict):
            simp = obj.get("simplified_pronunciation")
            if isinstance(simp, str) and "?" in simp:
                new = regenerate(simp, obj.get("phonetic_form"), entry_id, changes)
                if new:
                    obj["simplified_pronunciation"] = new
            for v in obj.values():
                walk(v, entry_id)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, entry_id)

    for entry in data:
        walk(entry, entry.get("entry_id", "?"))

    if apply and changes:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    out(f"[JSON] {'applied' if apply else 'would fix'}: {len(changes)}")
    return len(changes)


def main():
    parser = argparse.ArgumentParser(description="Fix '?' artifacts in respellings")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "skiri_pawnee.db"))
    parser.add_argument(
        "--json",
        default=str(PROJECT_ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"),
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write changes (default: dry run)")
    args = parser.parse_args()

    db_path = Path(args.db)
    json_path = Path(args.json)

    out(f"{'[APPLY]' if args.apply else '[DRY RUN]'} fixing respelling artifacts")

    if args.apply:
        BACKUP_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUP_DIR / f"skiri_pawnee_backup_{stamp}.db"
        shutil.copy2(db_path, backup)
        out(f"[*] DB backed up to {backup}")

    n_db = fix_db(db_path, args.apply)
    n_json = fix_json(json_path, args.apply)

    out(f"\nDone. DB: {n_db} fixed, JSON: {n_json} fixed"
        + ("" if args.apply else " (dry run — re-run with --apply)"))


if __name__ == "__main__":
    main()
