#!/usr/bin/env python3
"""
The database as text, so that it can be kept in git
===================================================

`skiri_pawnee.db` is a binary file and is not in git. This script writes its
contents to DB/dump/ as plain text, one file per table and one row per line,
sorted by key. A later fix to the database then shows up in git as a small,
readable difference, and the database can be rebuilt from the dump.

    python scripts/db_dump.py                 # compare DB/dump/ with the database; change nothing
    python scripts/db_dump.py --write         # write DB/dump/ from the database
    python scripts/db_dump.py --restore NEW   # build a new database file NEW from DB/dump/
    python scripts/db_dump.py --verify        # prove the round trip: dump, restore to a temporary
                                              # file, compare every row with the live database

The database itself is never modified by this script.

What is left out, on purpose:
  community_feedback    people's names and comments; private
  srs_cards, srs_reviews  one person's study progress
  fts_* tables          full-text indexes; SQLite rebuilds them as the rows are restored

A restored database has those tables, empty (the full-text ones filled).

Files in DB/dump/:
  _schema.sql      every CREATE statement, in the order the objects were made
  _sequence.json   the AUTOINCREMENT counters
  _manifest.json   rows and SHA-256 per table file
  <table>.jsonl    one JSON object per row
"""
import argparse
import base64
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"
DUMP = ROOT / "DB" / "dump"

PRIVATE = {"community_feedback", "srs_cards", "srs_reviews"}


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def connect_ro(path):
    return sqlite3.connect("file:%s?mode=ro" % Path(path).resolve().as_posix(), uri=True)


def is_fts(name, fts_names):
    return name in fts_names or any(name.startswith(f + "_") for f in fts_names)


def schema_objects(conn):
    """(type, name, tbl_name, sql) in creation order; internal objects left out."""
    rows = conn.execute("select type, name, tbl_name, sql from sqlite_master order by rowid").fetchall()
    fts = {name for typ, name, _, sql in rows if typ == "table" and sql and "USING fts5" in sql}
    keep = []
    for typ, name, tbl, sql in rows:
        if sql is None or name.startswith("sqlite_"):
            continue                      # automatic indexes, sqlite_sequence
        if typ == "table" and name not in fts and is_fts(name, fts):
            continue                      # shadow tables of a full-text index
        keep.append((typ, name, tbl, sql))
    return keep, fts


def data_tables(conn):
    objs, fts = schema_objects(conn)
    return [name for typ, name, _, _ in objs if typ == "table" and name not in fts and name not in PRIVATE]


def key_columns(conn, table):
    info = conn.execute('pragma table_info("%s")' % table).fetchall()
    pk = [r[1] for r in sorted(info, key=lambda r: r[5]) if r[5]]
    return [r[1] for r in info], pk


def encode(value):
    if isinstance(value, bytes):
        return {"$blob": base64.b64encode(value).decode("ascii")}
    return value


def decode(value):
    if isinstance(value, dict) and set(value) == {"$blob"}:
        return base64.b64decode(value["$blob"])
    return value


def table_lines(conn, table):
    cols, pk = key_columns(conn, table)
    order = ", ".join('"%s"' % c for c in pk) if pk else "rowid"
    lines = []
    for row in conn.execute('select * from "%s" order by %s' % (table, order)):
        lines.append(json.dumps({c: encode(v) for c, v in zip(cols, row)}, ensure_ascii=False))
    return lines


def render(conn):
    """Every dump file as {name: text}. The same database always gives the same bytes."""
    files = {}
    objs, _ = schema_objects(conn)
    files["_schema.sql"] = "".join(sql.strip() + ";\n\n" for _, _, _, sql in objs)
    tables = data_tables(conn)
    manifest = {"tables": {}, "left_out": sorted(PRIVATE) + ["fts_* (rebuilt on restore)"],
                "journal_mode": conn.execute("pragma journal_mode").fetchone()[0],
                "user_version": conn.execute("pragma user_version").fetchone()[0]}
    for t in tables:
        lines = table_lines(conn, t)
        text = "".join(line + "\n" for line in lines)
        files[t + ".jsonl"] = text
        manifest["tables"][t] = {"rows": len(lines), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    seq = {name: n for name, n in conn.execute("select name, seq from sqlite_sequence order by name") if name not in PRIVATE}
    files["_sequence.json"] = json.dumps(seq, ensure_ascii=False, indent=1) + "\n"
    files["_manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=1) + "\n"
    return files


def compare_with_disk(files):
    changed, missing, extra = [], [], []
    for name, text in files.items():
        p = DUMP / name
        if not p.exists():
            missing.append(name)
        elif p.read_bytes() != text.encode("utf-8"):
            changed.append(name)
    if DUMP.exists():
        extra = sorted(p.name for p in DUMP.iterdir() if p.is_file() and p.name not in files and p.name != "README.md")
    return changed, missing, extra


def write_dump(files):
    DUMP.mkdir(parents=True, exist_ok=True)
    changed, missing, extra = compare_with_disk(files)
    for name in changed + missing:
        (DUMP / name).write_bytes(files[name].encode("utf-8"))
    for name in extra:
        (DUMP / name).unlink()
    return changed, missing, extra


def restore(target, dump_dir=DUMP):
    target = Path(target)
    if target.exists():
        sys.exit("refusing to overwrite %s: give the name of a file that does not exist" % target)
    manifest = json.loads((dump_dir / "_manifest.json").read_text(encoding="utf-8"))
    conn = sqlite3.connect(str(target))
    conn.executescript((dump_dir / "_schema.sql").read_text(encoding="utf-8"))
    for table, meta in manifest["tables"].items():
        text = (dump_dir / (table + ".jsonl")).read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != meta["sha256"]:
            sys.exit("%s.jsonl does not match its hash in _manifest.json: the dump was edited or is incomplete" % table)
        rows = [json.loads(line) for line in text.splitlines() if line]
        if not rows:
            continue
        cols = list(rows[0])
        sql = 'insert into "%s" (%s) values (%s)' % (table, ", ".join('"%s"' % c for c in cols), ", ".join("?" * len(cols)))
        conn.executemany(sql, [[decode(r[c]) for c in cols] for r in rows])
    for name, n in json.loads((dump_dir / "_sequence.json").read_text(encoding="utf-8")).items():
        if conn.execute("select 1 from sqlite_sequence where name=?", (name,)).fetchone():
            conn.execute("update sqlite_sequence set seq=? where name=?", (n, name))
        else:
            conn.execute("insert into sqlite_sequence(name, seq) values (?, ?)", (name, n))
    conn.commit()
    conn.execute("pragma user_version = %d" % int(manifest.get("user_version", 0)))
    conn.execute("pragma journal_mode = %s" % manifest.get("journal_mode", "delete"))
    conn.commit()
    conn.close()
    return manifest


def verify(db_path):
    """Dump the live database to a temporary folder, restore it, and compare the two databases."""
    live = connect_ro(db_path)
    files = render(live)
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        d = tmp / "dump"
        d.mkdir()
        for name, text in files.items():
            (d / name).write_bytes(text.encode("utf-8"))
        copy_path = tmp / "restored.db"
        restore(copy_path, d)
        copy = sqlite3.connect(str(copy_path))
        # 1. the schema
        a = [(t, n, s.strip()) for t, n, _, s in schema_objects(live)[0]]
        b = [(t, n, s.strip()) for t, n, _, s in schema_objects(copy)[0]]
        if a != b:
            problems.append("schema differs")
        out("schema: %d objects, identical: %s" % (len(a), a == b))
        # 2. every row of every dumped table
        total = 0
        for t in data_tables(live):
            cols, pk = key_columns(live, t)
            order = ", ".join('"%s"' % c for c in pk) if pk else "rowid"
            ra = live.execute('select * from "%s" order by %s' % (t, order)).fetchall()
            rb = copy.execute('select * from "%s" order by %s' % (t, order)).fetchall()
            total += len(ra)
            if ra != rb:
                problems.append("rows differ in %s" % t)
                out("  %-26s DIFFERENT (%d rows live, %d restored)" % (t, len(ra), len(rb)))
        out("rows: %d in %d tables compared" % (total, len(data_tables(live))))
        # 3. the counters
        sa = {n: s for n, s in live.execute("select name, seq from sqlite_sequence") if n not in PRIVATE}
        sb = {n: s for n, s in copy.execute("select name, seq from sqlite_sequence") if n not in PRIVATE}
        if sa != sb:
            problems.append("AUTOINCREMENT counters differ")
        out("counters: identical: %s" % (sa == sb))
        # 4. the full-text indexes answer the same
        _, fts = schema_objects(live)
        probes = ["bear", "water", "house", "go", "eat", "sing", "chief", "night"]
        for f in sorted(fts):
            copy.execute('insert into "%s"("%s") values (\'integrity-check\')' % (f, f))
            same = True
            for word in probes:
                q = 'select rowid from "%s" where "%s" match ? order by rowid' % (f, f)
                if live.execute(q, (word,)).fetchall() != copy.execute(q, (word,)).fetchall():
                    same = False
            if not same:
                problems.append("full-text index %s answers differently" % f)
            out("full-text %-20s integrity ok, %d probe searches identical: %s" % (f, len(probes), same))
        # 5. the private tables exist and are empty
        for t in sorted(PRIVATE):
            n = copy.execute('select count(*) from "%s"' % t).fetchone()[0]
            if n:
                problems.append("%s is not empty in the restored copy" % t)
        ok = copy.execute("pragma integrity_check").fetchone()[0]
        if ok != "ok":
            problems.append("integrity_check: %s" % ok)
        out("restored copy: integrity_check %s; private tables empty" % ok)
        copy.close()
    live.close()
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true", help="write DB/dump/ from the database")
    g.add_argument("--restore", metavar="NEW", help="build a new database file from DB/dump/")
    g.add_argument("--verify", action="store_true", help="prove that dump and restore give back the same database")
    args = ap.parse_args()

    if args.restore:
        manifest = restore(args.restore)
        out("built %s from DB/dump/: %d tables, %d rows" % (
            args.restore, len(manifest["tables"]), sum(t["rows"] for t in manifest["tables"].values())))
        out("left empty: %s" % ", ".join(sorted(PRIVATE)))
        return
    if args.verify:
        problems = verify(args.db)
        if problems:
            for p in problems:
                out("PROBLEM: " + p)
            sys.exit(1)
        out("round trip exact")
        return

    conn = connect_ro(args.db)
    files = render(conn)
    conn.close()
    rows = sum(json.loads(files["_manifest.json"])["tables"][t]["rows"] for t in json.loads(files["_manifest.json"])["tables"])
    size = sum(len(t.encode("utf-8")) for t in files.values())
    if args.write:
        changed, missing, extra = write_dump(files)
        out("DB/dump/: %d files, %d rows, %.1f MB" % (len(files), rows, size / 1e6))
        out("written: %d changed, %d new, %d removed" % (len(changed), len(missing), len(extra)))
        for name in changed + missing:
            out("  " + name)
        return
    changed, missing, extra = compare_with_disk(files)
    if not (changed or missing or extra):
        out("DB/dump/ is in step with the database (%d files, %d rows)" % (len(files), rows))
        return
    out("DB/dump/ is NOT in step with the database:")
    for label, names in (("changed", changed), ("not yet written", missing), ("no longer a table", extra)):
        for name in names:
            out("  %-16s %s" % (label, name))
    out("run with --write to bring it up to date")
    sys.exit(1)


if __name__ == "__main__":
    main()
