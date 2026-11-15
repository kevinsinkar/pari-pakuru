# Engines review, Stage 0: the baseline

*Taken on 2026-11-14, between 16:02 and 16:10, before anything else in this
review was done. Every check in the two "Checks" tables of the top-level
[README.md](../../README.md) was run. Nothing was changed.*

## In short

- All 24 checks give the result the README states, with **one stale figure**:
  the README says the text copy of the database has 46,821 rows; it has
  46,553. The reason is found and is harmless (below).
- Two more lines in `scripts/README.md` are out of date, and say so beside
  lines of the same file that are right (below).
- The checks changed no file. The database has the same SHA-256 before and
  after.

## Before starting

| | |
|---|---|
| Database backed up to | `OneDrive/pari_pakuru_backups/skiri_pawnee_backup_20261114_160246_engines_review_stage0.db` |
| SHA-256 of `skiri_pawnee.db` | `4f206feeb5fa01dddb18fe521227b833dea7c567f6c09a9e5239d883512db145` (the backup has the same) |
| Git | branch `main` at `814e8cc`, with 75 files changed or new and not committed (the third part of 2026-11-14) |
| Python | 3.13.14 (`.venv`); Node.js v24.14.0 |

## How "changed nothing" was checked

Every file of the repository outside `.git` and `.venv` was hashed before the
first check and again after the last (3,496 files). Result: no file changed
and none was removed. Two files were added, `skiri_pawnee.db-shm` and
`skiri_pawnee.db-wal`. They are SQLite's own working files for a database in
write-ahead mode; they appear whenever the database is opened, the second is
0 bytes long (nothing was waiting to be written), and both are ignored by
git.

Three checks would by default write into the repository, so they were run in
a way that could not:

- `source_audit/s2e_compare.py` and `source_audit/e2s_compare.py` overwrite
  the audit's own record unless given `--out`. They were given a folder
  outside the repository, and their output was compared with the record in
  `reports/source_audit_2026-11/after_fixes/`: byte for byte the same.
- `morphology_v2/run.py --all` rewrites `curriculum/roots_v2/`. The folder was
  copied first; after the run it was identical to the copy.
- The web app's `/study` page opens the database for writing. The app was
  tested against a copy of the database.

## The checks

"README" is what the README's table says; "now" is what the command printed
today.

| # | Check | Command | README | Now | Same? |
|---|---|---|---|---|---|
| 1 | Sound-change rules | `scripts/sound_changes.py --test` | 11 of 11 | 11 of 11 | yes |
| 2 | Person and mode derivation | `scripts/person_forms.py --validate-appendix` | 25 of 27 | 25 passed, 2 failed, 1 skipped | yes (see note 1) |
| 3 | Sentence templates | `scripts/sentence_templates.py test` | 34 of 34 | 34 of 34 | yes |
| 4 | Respelling and audit code | `scripts/test_phase_1_1.py` | 106 of 106 | 106 of 106 | yes |
| 5 | Database schema and query library | `DB/test_schema.py` | 53 of 53 | 53 passed, 0 failed | yes |
| 6 | Word-construction analysis | `python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"` | 34 of 34 | 34 tests, OK | yes |
| 7 | Its test sets are unchanged | `scripts/morphology_v2/gold_build.py --verify` | 17 files match | 17 ok, 0 changed | yes |
| 8 | Its outputs are reproducible | `scripts/morphology_v2/run.py --all`, hashes compared | byte-identical | 9 output hashes identical before and after; the folder identical to a copy taken before the run | yes |
| 9 | Every Pawnee form in the guide has a source | `scripts/morphology_v2/check_forms.py` | 3,811 forms, 250 IPA, 203 respellings: all resolved | 3,811 forms, 250 IPA, 203 respellings: all resolved | yes |
| 10 | Noun possession and the *-hiriʔ* suffix | `scripts/possession_engine.py --test` | 60 of 60, ten of them attested words in *-hiriʔ* | 60 of 60; *-hiriʔ* seam 10 of 10 | yes |
| 11 | The text copy of the database restores to the same database | `scripts/db_dump.py --verify` | round trip exact: 46,821 rows in 25 tables | round trip exact: **46,553** rows in 25 tables | **no** (see note 2) |
| 12 | Dictionary entries against the printed page | `scripts/source_audit/s2e_compare.py` | 50,807 of 50,837 fields identical (99.94%); 37 differences | 50,807 of 50,837 (99.94%); 37 differences | yes |
| 13 | Every entry cites the page of the book | `scripts/fix_page_citations.py --check` | 4,244 of 4,244; 181 pages | 4,244 of 4,244; file number + 348 on all 181 pages | yes |
| 14 | Learner spelling and respelling follow from Parks's forms | `scripts/check_simplified_forms.py` | no difference in 4,244 entries | 0 and 0 differences in 4,244 entries (589 entries with the known tense/lax coarseness) | yes |
| 15 | That comparison catches errors | `scripts/source_audit/recall_test.py` | 510 of 510 | 510 of 510, 17 kinds | yes |
| 16 | The grammar chapter against two blind readings | `scripts/source_audit/chapter4_second_reading.py` | all 526 Skiri words stand in both readings; nothing left to correct | 538 stored words: 526 where three readings agree, 12 not Skiri words; nothing to change | yes |
| 17 | Blue Book forms against the readings of the scan | `scripts/apply_bluebook_scan_fixes.py` (dry run) | nothing left to apply; 17 forms for a person | 0 rows to correct; 17 left for a person | yes |
| 18 | The English index against the printed page | `scripts/repair_english_index.py --check` | 118,262 letters printed, 118,262 stored | the same; exit 0; "nothing to change" | yes |
| 18b | The audit's own comparison of the index | `scripts/source_audit/e2s_compare.py` (`--source json` and `--source db`) | 32,632 of 32,636 fields equal | 32,632 of 32,636 for both the file and the tables | yes |
| 19 | Chapters 2 and 5 against two readings | `scripts/source_audit/front_matter_reading.py` | all 138 and 57 Skiri forms the same in both | 138 of 138 and 57 of 57 | yes |
| 20 | The grammar chapter's tables in two readings | `scripts/source_audit/chapter4_tables.py` | 14 tables: 6 the same, 6 the same text with rows divided differently, 2 differ | the same | yes |
| 21 | The Blue Book glossary against the pages it points to | `scripts/bluebook_glossary.py` | 589 of 644 page references confirmed | 589 of 644 | yes |
| 22 | The published search page | `node scripts/check_static_site.js` | 13 checks pass; all 4,337 entries render | 13 of 13 "ok"; 4,337 entries | yes |
| 23 | Web app | Flask's test client (no command is recorded; see note 3) | 25 routes; the possession API for all 1,706 nouns; all answer | 26 addresses covering every page and read-only API route: all answer. Possession API: 1,706 of 1,706 answer | yes (see note 3) |

Measurements, not pass or fail:

| # | What | Command | README | Now | Same? |
|---|---|---|---|---|---|
| 24 | Conjugation engine against Appendix 1 | `scripts/morpheme_inventory.py --validate` | 611 of 770 exact (79.4%), 137 within two letters, 22 further off | 611 exact (79.4%), 137 close, 22 mismatch | yes |
| 25 | Form 2 predicted from headword, class and preverb | `scripts/stem_extractor.py --validate` | 1,915 of 2,197 exact (87.2%) | 1,915 exact, 41 "close (glottal)", 241 missed | yes |

## Notes

**1. Person derivation: 28 cases, not 27.** The script checks four forms for
each of Parks's seven verbs. One of the 28 is skipped, not failed: the third
person absolutive of 'to come', printed *raʔaʔ*, which the script itself
marks "underivable". So the result is 25 right and 2 wrong out of 27 that it
attempts, and one printed form it does not attempt. The README's "25 of 27"
is correct but leaves the skipped form out of view.

**2. The row count in the README is stale; the database is fine.** The
README was written when the text copy held 46,821 rows. After that, on the
same day, the English index was rebuilt from the printed page, and that
changed two tables: `english_index` went from 8,067 rows to 7,806 and
`cross_references` from 4,585 to 4,578. That is 268 rows fewer, which is
exactly the difference (46,821 − 268 = 46,553). I compared the row counts of
the committed text copy with today's, table by table: no other table
changed. The round trip itself is exact, and `DB/dump/` is in step with the
database. The README's figure should read 46,553; I correct it when the
review's documentation is written at the end of Stage 3, not now.

**3. The web app check has no recorded command.** The README says "25 routes
requested" without saying which. I requested every page and every read-only
API route at least once (26 addresses, 21 distinct routes), plus one request
to the sentence assembler: all answer. The four routes that write (spelling
preference, study grading, feedback, feedback review) were not posted to.

The possession API answers for all 1,706 noun rows, but for seven of them the
answer is `{"error": "not a noun"}`: *huuwiʔ*, *iituʔ*, *pic*,
*raruukaʔaatuʔ*, *iit-*, *iriwis-*, *raa-*. Each of these spellings is two
dictionary entries, a noun and something else, and the API looks an entry up
by its spelling and takes whichever it finds first. This is a fault of the
route, not a difference from the README, and it is taken up in Stage 2
(145 spellings in the dictionary are more than one entry).

**4. Two stale lines in `scripts/README.md`.** Line 95 gives the person
derivation as "27 of 27" (the top-level README and the same file's "Known
problems" say 25 of 27, which is what the command prints). The paragraph
under section 3 says the conjugation engine "reproduces 90% of the seven
Appendix 1 verbs" (the table above it in the same file says 79.4%). Both are
corrected with the rest of the documentation at the end of Stage 3.

## Where the output is

The full output of each command was saved outside the repository while the
baseline was taken, and is not kept: every command above can be run again in
seconds, and the two tables above record what each printed.
