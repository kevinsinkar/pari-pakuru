# DB/

The database layer: the schema, the importer that builds the database from the
two JSON dictionaries, and the query library the web app uses.

The database file itself, `skiri_pawnee.db`, sits in the repository root and is
**not in git**.

| File | Purpose |
|---|---|
| `schema.sql` | Creates the core tables, indexes, full-text search tables and the triggers that keep them in step |
| `import_to_sqlite.py` | Reads the two JSON dictionaries and fills the core tables (phase 1.2) |
| `query_api.py` | Lookup library and command-line tool: English → Skiri, Skiri → English, full-text and fuzzy search. `web/db.py` builds on it |
| `test_schema.py` | 53 checks of the schema and the query library against a small made-up database. Passes (2026-11-13) |

## Where each table comes from

`schema.sql` and the importer create only the core tables. The rest were added
later by the script named. Row counts on 2026-11-13.

| Table | Rows | Created by |
|---|---|---|
| `lexical_entries` | 4,337 | importer (4,273), then `scripts/import_bb_items.py` (+93), `scripts/dedup_entries.py` (−23) and `scripts/fix_data_2026_11.py` (−6) |
| `glosses` | 5,504 | importer |
| `paradigmatic_forms` | 9,562 | importer; 19 forms corrected from the page on 2026-11-13 |
| `examples` | 2,634 | importer; `scripts/blue_book_verify.py` added 88 Blue Book sentences |
| `etymology` | 3,825 | importer |
| `cognates` | 608 | importer |
| `derived_stems` | 0 | importer. **Empty**, although the JSON holds 21 derived stems in 10 entries: an open item |
| `english_index` | 8,067 | importer, **from an earlier file than the current JSON** (`import_metadata` names `english_to_skiri_verified.json`). Its Skiri terms and IPA were never cleaned: 3,986 IPA forms are not in Parks's notation and 177 still hold raw stand-in characters. The current `english_to_skiri_linked.json` is clean. Re-import from it; see the 2026-11 audit |
| `cross_references` | 4,585 | importer |
| `fts_glosses`, `fts_examples`, `fts_english_index` | | full-text indexes, kept current by triggers |
| `import_metadata` | 6 | importer |
| `semantic_tags` | 4,499 | `scripts/tag_entries.py` |
| `blue_book_attestations` | 1,026 | `scripts/blue_book_verify.py` |
| `bb_gap_triage` | 516 | `scripts/bb_gap_triage.py` |
| `sound_change_rules` | 24 | `scripts/sound_changes.py` |
| `verb_paradigms`, `irregular_verb_roots`, `morpheme_abbreviations` | 770, 9, 164 | `scripts/extract_appendices.py` |
| `morpheme_inventory`, `verb_template_slots` | 37, 27 | `scripts/morpheme_inventory.py` |
| `noun_stems`, `kinship_paradigms`, `possession_examples` | 49, 14, 20 | `scripts/noun_possession.py` |
| `function_words` | 418 | `scripts/function_word_inventory.py` |
| `bb_function_words` | 63 | `scripts/extract_function_words.py` |
| `lessons` | 20 | `scripts/build_lessons.py` |
| `community_feedback` | 2 | `archived/scripts/add_feedback_table.py`; written by the web app |
| `srs_cards`, `srs_reviews` | 0, 0 | `web/srs.py` |

Columns added to `lexical_entries` after the import: `blue_book_attested`,
`form2_confidence`, `source`, `bb_variant_of`.

## Rebuilding

The importer alone gives you only the core tables as they were on 2026-03-08.
Everything after that (tags, Blue Book links, the 93 Blue Book words, the
de-duplication, the audit repairs, lessons, grammar tables) was applied to the
database by later scripts, in the order given in
[../scripts/README.md](../scripts/README.md). Some of those steps called an AI
service. In practice, **restore; do not rebuild.** Since 2026-11-13 the whole
database is in git as text, in [dump/](dump/):

```bash
python scripts/db_dump.py --restore skiri_pawnee.db   # build the database from DB/dump/ (refuses to overwrite a file)
python scripts/db_dump.py --write                     # after changing the database: bring DB/dump/ up to date, then commit it
python scripts/db_dump.py                             # is DB/dump/ in step with the database?
```

A restored database has everything except the community feedback and study
progress, which are private and are not written to the dump. Binary backups
are still made by every script that changes the database, in
`OneDrive/pari_pakuru_backups/` and `~/.pari_pakuru_backups/`.

```bash
# core tables only, into a new file
python DB/import_to_sqlite.py \
    --s2e "Dictionary Data/skiri_to_english_respelled.json" \
    --e2s "Dictionary Data/english_to_skiri_linked.json" \
    --db  new.db --schema DB/schema.sql
```

## Looking things up

```bash
python DB/query_api.py --db skiri_pawnee.db --english "bear"
python DB/query_api.py --db skiri_pawnee.db --skiri "kuruks"
python DB/query_api.py --db skiri_pawnee.db --search "to run"      # full text
python DB/query_api.py --db skiri_pawnee.db --fuzzy "kuruk"        # misspellings
python DB/query_api.py --db skiri_pawnee.db --english "stop" --class VT
python DB/query_api.py --db skiri_pawnee.db --browse N --brief
python DB/query_api.py --db skiri_pawnee.db --stats
python DB/query_api.py --db skiri_pawnee.db --english "bear" --json
```

```python
from query_api import SkiriDictionary

with SkiriDictionary("skiri_pawnee.db") as db:
    for entry in db.lookup_english("bear"):
        print(entry.full_display())
```

## Design decisions

- **The Skiri-to-English section is the record.** `lexical_entries` holds it; `english_index` points into it.
- **`entry_id` is stable**: `SK-{slug}-p{page}-{index}` for Parks entries, `BB-{slug}-{n}` for Blue Book-only words. The page in the id is whatever the parser saw and is sometimes wrong (the `kaa…` entries with `-p2-` ids are on book page 419); an id is a name, not a page reference.
- **`raw_entry_json`** keeps the parsed entry whole, so nothing is lost by the table layout.
- **Senses can share a number.** Parks's sub-senses 2a and 2b are both stored as sense 2. The `glosses` table has no uniqueness rule on `(entry_id, sense_number)`; an earlier rule silently dropped seven entries' senses.
- **`etymology.constituent_elements`** is JSON made by an automatic parse. Its per-piece glosses are often attached to the wrong piece. Use `raw_etymology`, and see `scripts/morphology_v2/etymology.py` for a parser that reads it correctly.
- **Two entries with one headword are usually two words.** Parks lists, for example, a descriptive and a passive verb of the same shape separately. Never merge on the headword alone.
- **`phonetic_form` holds Parks's own symbols**, since 2026-11-13: `·` between syllables, `–` at the edge of a bound form, ə́ and ɪ́ for the accented short vowels. The PDF's text layer does not hold his IPA letters but other characters in their place (`ß` for ə, `÷` for ú, `Š` for ʊ́ ...), and which character stands for what depends on the font; the verified table is `scripts/source_audit/chartable.py`. Code written for the older notation (hyphen, bullet, à, í) must convert with `scripts/ipa_notation.py`. The 93 Blue Book-only entries have no phonetic form.
- **Reading connections open the file read-only.** Only the feedback and study tables are written by the web app, through a separate connection.
