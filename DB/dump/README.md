# DB/dump/

**The database as text.** `skiri_pawnee.db` is a binary file and is not in
git. This folder holds its contents as plain text, so that every change to
the database shows up in git as a readable difference, and so that the
database can be rebuilt.

Written by [`scripts/db_dump.py`](../../scripts/db_dump.py). **Do not edit
these files by hand**: each table file is checked against its hash in
`_manifest.json` before a restore.

| File | What it is |
|---|---|
| `<table>.jsonl` | One table: one row per line, as a JSON object, sorted by key |
| `_schema.sql` | Every `CREATE` statement, in the order the objects were made |
| `_sequence.json` | The AUTOINCREMENT counters |
| `_manifest.json` | Rows and SHA-256 of each table file; what was left out |

Left out on purpose: `community_feedback` (people's names and comments),
`srs_cards` and `srs_reviews` (one person's study progress), and the
full-text index tables (SQLite rebuilds them as the rows are restored).

```bash
python scripts/db_dump.py                 # is this folder in step with the database? changes nothing
python scripts/db_dump.py --write         # bring it up to date after a change to the database
python scripts/db_dump.py --restore new.db   # build a database from this folder
python scripts/db_dump.py --verify        # prove that dump and restore give back the same database
```

After any script changes the database, run `--write` and commit the
difference together with the script's report.
