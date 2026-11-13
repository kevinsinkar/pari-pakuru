#!/usr/bin/env python3
"""
Stage 7b: apply the fixes a person has approved
===============================================

The audit proposes; this applies, and only what has been approved.

Approval is a text file, reports/source_audit_2026-11/approved_fixes.txt, with
one fix id per line (P00453, P00454 ...; anything after # is a comment). The
ids are those in proposed_fixes.jsonl and on the review page.

    python scripts/source_audit/apply_fixes.py            # dry run: says what each approved fix would do
    python scripts/source_audit/apply_fixes.py --apply    # backs up, changes the database and the JSON, rewrites DB/dump/, writes the report

What it can apply (a fix needs a "proposed_value"):
    paradigmatic_forms.skiri_form        a verb form of a dictionary entry
    lexical_entries.phonetic_form        the IPA of an entry (the respelling is regenerated from it)
    lexical_entries.column_position      left or right
    cognates.form                        a form cited from another language
    verb_paradigms.skiri_form            a form of Appendix 1
    irregular_verb_roots.plural_stem     Appendix 2
Each change is made only if the stored value is still the one the audit saw.
The Skiri-to-English JSON is changed in step for the first, second and fourth.

What it does not apply, and says so: anything without a proposed value, fixes
to extracted_data/ files and to the English-to-Skiri JSON, and text the
database lacks. Those are for a person, or for a re-run of the step that made
the file.

Dry run is the default. The report is written only with --apply.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
FIXES = state.OUT / "proposed_fixes.jsonl"
APPROVED = state.OUT / "approved_fixes.txt"
REPORT = state.OUT / "apply_fixes_report.txt"


def number_in(column):
    m = re.search(r"(\d+)\s*$", column or "")
    return int(m.group(1)) if m else None


def replace_in_json(node, old, new):
    """Replace string values equal to `old` under `node`; returns how many were replaced."""
    n = 0
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str) and v == old:
                node[k] = new
                n += 1
            else:
                n += replace_in_json(v, old, new)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str) and v == old:
                node[i] = new
                n += 1
            else:
                n += replace_in_json(v, old, new)
    return n


def plan(fix, conn):
    """(sql, params, json change or None, description) or (None, None, None, reason it cannot be applied)."""
    value = fix.get("proposed_value")
    if value is None:
        return None, None, None, "no proposed value: %s" % (fix.get("needs") or "needs a person")
    table, column = fix["table"].split(" ")[0], fix["column"] or ""
    stored = fix["stored"]
    if table == "paradigmatic_forms":
        n = number_in(column)
        old = re.sub(r"^\s*\d+\.\s*", "", stored)
        row = conn.execute("select id, skiri_form from paradigmatic_forms where entry_id=? and form_number=?", (fix["key"], n)).fetchone()
        if not row or row[1] != old:
            return None, None, None, "the stored form is no longer %r" % old
        return ("update paradigmatic_forms set skiri_form=? where id=?", (value, row[0]), (fix["key"], old, value),
                "form %s of %s: %s -> %s" % (n, fix["headword"], old, value))
    if table == "lexical_entries" and column == "phonetic_form":
        row = conn.execute("select phonetic_form from lexical_entries where entry_id=?", (fix["key"],)).fetchone()
        if not row or row[0] != stored:
            return None, None, None, "the stored IPA is no longer %r" % stored
        return ("update lexical_entries set phonetic_form=? where entry_id=?", (value, fix["key"]), (fix["key"], stored, value),
                "IPA of %s: %s -> %s" % (fix["headword"], stored, value))
    if table == "lexical_entries" and column == "column_position":
        return ("update lexical_entries set column_position=? where entry_id=? and column_position=?", (value, fix["key"], stored), None,
                "column of %s: %s -> %s" % (fix["headword"], stored, value))
    if table == "cognates":
        n = number_in(column)
        rows = conn.execute("select id, form from cognates where entry_id=? order by id", (fix["key"],)).fetchall()
        if not n or n > len(rows) or rows[n - 1][1] != stored:
            return None, None, None, "the stored cognate is no longer %r" % stored
        return ("update cognates set form=? where id=?", (value, rows[n - 1][0]), (fix["key"], stored, value),
                "cognate %s of %s: %s -> %s" % (n, fix["headword"], stored, value))
    if table == "verb_paradigms":
        row = conn.execute("select skiri_form from verb_paradigms where id=?", (fix["key"],)).fetchone()
        if not row or row[0] != stored:
            return None, None, None, "the stored form is no longer %r" % stored
        return ("update verb_paradigms set skiri_form=? where id=?", (value, fix["key"]), None,
                "Appendix 1, %s: %s -> %s" % (fix["headword"], stored, value))
    if table == "irregular_verb_roots" and column == "plural_stem":
        return ("update irregular_verb_roots set plural_stem=? where headword=? and plural_stem=?", (value, fix["key"], stored), None,
                "Appendix 2, %s: %s -> %s" % (fix["headword"], stored, value))
    return None, None, None, "this kind of fix is applied by hand (%s, %s)" % (fix["table"], column)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    ap.add_argument("--approved", default=str(APPROVED), help="file with the approved fix ids")
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()
    approved_path = Path(args.approved)
    if not approved_path.exists():
        state.out("no approvals yet: %s does not exist." % approved_path)
        state.out("Write the ids of the fixes to apply into it, one per line, and run again.")
        return
    ids = []
    for line in approved_path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            ids.append(line)
    fixes = {}
    for line in FIXES.open(encoding="utf-8"):
        f = json.loads(line)
        fixes[f["id"]] = f
    conn = sqlite3.connect(args.db) if args.apply else sqlite3.connect("file:%s?mode=ro" % Path(args.db).resolve().as_posix(), uri=True)
    log = ["apply_fixes %s %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
           "approved ids: %d" % len(ids), ""]
    todo, skipped = [], 0
    for fid in ids:
        f = fixes.get(fid)
        if f is None:
            log.append("%s  UNKNOWN id" % fid)
            skipped += 1
            continue
        sql, params, json_change, text = plan(f, conn)
        if sql is None:
            log.append("%s  not applied: %s" % (fid, text))
            skipped += 1
        else:
            log.append("%s  %s" % (fid, text))
            todo.append((fid, f, sql, params, json_change))
    log.append("")
    log.append("%d to apply, %d not applied" % (len(todo), skipped))
    state.out("\n".join(log))
    if not args.apply:
        state.out("")
        state.out("dry run: nothing was changed and no report was written (use --apply)")
        return
    if not todo:
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.db, backups / ("skiri_pawnee_backup_%s.db" % stamp))
    shutil.copy2(S2E_JSON, backups / ("skiri_to_english_respelled_backup_%s.json" % stamp))
    from fix_pronunciations import respell_phonetic
    data = json.loads(S2E_JSON.read_text(encoding="utf-8"))
    by_id = {e.get("entry_id"): e for e in data}
    json_notes = []
    for fid, f, sql, params, json_change in todo:
        conn.execute(sql, params)
        if f["table"].startswith("lexical_entries") and f["column"] == "phonetic_form":
            new_respelling = respell_phonetic(f["proposed_value"])
            conn.execute("update lexical_entries set simplified_pronunciation=? where entry_id=?", (new_respelling, f["key"]))
        if json_change:
            entry_id, old, new = json_change
            entry = by_id.get(entry_id)
            n = replace_in_json(entry, old, new) if entry is not None else 0
            if n != 1:
                json_notes.append("%s  JSON: %d places held %r in entry %s (expected 1); check by hand" % (fid, n, old, entry_id))
            if entry is not None and f["column"] == "phonetic_form":
                entry.setdefault("part_I", {})["simplified_pronunciation"] = respell_phonetic(new)
    conn.commit()
    conn.close()
    S2E_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False)
    log += ["", "backups: %s (stamp %s)" % (backups, stamp)] + json_notes
    REPORT.write_text("\n".join(log) + "\n", encoding="utf-8", newline="\n")
    state.out("applied %d fixes; report: %s" % (len(todo), REPORT))
    for note in json_notes:
        state.out(note)


if __name__ == "__main__":
    main()
