# scripts/

One script per processing step. This file lists them in the order the work was
done, so that the next person can see how the data came to be and what to run
again.

The folder is flat on purpose: the scripts import one another by name, and the
web app imports several of them. Do not move a script into a sub-folder without
changing those imports.

## Status words used below

| Status | Meaning |
|---|---|
| **live** | Imported by the web app, the site build or the word-construction analysis. Changing it changes what users see |
| **pipeline** | Builds or rebuilds data. Run it only when you mean to rebuild that data |
| **applied** | A one-time repair that has been applied to the database and the JSON. Kept as the record of exactly what was changed. Do not run it again without reading it |
| **test** | Checks other code; changes nothing |

Rules that every script here follows, or should:

- A script that changes the database or the JSON has a preview mode. Newer scripts change nothing unless `--apply` is given. Scripts from March 2026 apply by default and take `--dry-run` to preview. Check `--help` before running one.
- It backs the file up first to `OneDrive/pari_pakuru_backups/` (or `~/.pari_pakuru_backups/`).
- It writes a report to [../reports/](../reports/).
- Steps marked **AI** call the Gemini API and need `GEMINI_API_KEY`. Their answers were saved in checkpoint files; the checkpoints of finished runs are in the backup folder under `repo_cleanup_2026-11-13/`, not in the repository.

## 1. From the printed dictionary to JSON (February to March 2026)

| Script | Phase | Status | What it does |
|---|---|---|---|
| `s2e_parser.py` | parse | pipeline, **AI** | Reads Skiri-to-English page PDFs into JSON entries. Left as it was for its last run (the pages missed the first time) |
| `run_parser_e2s.py` | parse | pipeline, **AI** | The same for the English-to-Skiri section. Uses the prompt and schema in [../prompts/dictionary_parsing/](../prompts/dictionary_parsing/) |
| `normalize_phonetic.py` | 1.1a | applied | Repairs characters the PDF text layer corrupted (™ for ʔ, Ù for č, and so on) in every field. 50,699 replacements |
| `link_dictionaries.py` | 1.1b | applied | Gives every Skiri entry an `entry_id`, links English-to-Skiri subentries to it, and copies the better IPA across |
| `respell_and_normalize.py` | 1.1c | **live** (imported by the repair scripts) | Makes the learner respelling from the IPA, and the learner spelling from the headword |
| `fix_priority_issues.py` | 1.1c | applied | Six more character repairs and removal of non-IPA placeholder text |
| `audit_entries.py` | 1.1d | pipeline, optional **AI** | Checks every entry for missing fields, bad characters and headword/IPA mismatches |
| `test_phase_1_1.py` | 1.1 | test | 106 tests of the respelling and audit code |

Also from this stage, in [../archived/scripts/](../archived/scripts/):
`verify_with_gemini.py` and `verify_with_claude.py` (a second AI pass that
checked each parsed page against the PDF), `merge_json_files.py` and
`merge_skiri_files_v1.py` (merged the re-parsed missed pages),
`generate_review_list.py`, `verify_glottal_from_phonetic.py`,
`verify_noun_glottal.py` (follow-ups to the 1.1d audit).

## 2. Database (March 2026)

The importer, schema and query library are in [../DB/](../DB/).

| Script | Phase | Status | What it does |
|---|---|---|---|
| `tag_entries.py` | 2.1 | pipeline, optional **AI** | Gives entries topic tags (animal, body, kinship ...) from keywords, with AI for unclear cases |
| `blue_book_verify.py` | 2.2 | pipeline, **AI** for extraction | Extracts Blue Book vocabulary lesson by lesson, matches it to dictionary entries, fills `blue_book_attestations` |
| `bb_gap_triage.py` | 2.2 | pipeline, **AI** | Sorts the 516 Blue Book items with no dictionary match into eight kinds |
| `import_bb_items.py` | 2.2 | applied | Added 93 Blue Book-only words as entries (`source = 'blue_book'`, ids `BB-…`) |
| `populate_bb_pronunciation.py` | 2.2 | applied | Respelling and tags for those 93 entries |
| `dedup_entries.py` | cleanup | applied | Removed 22 duplicate entry pairs (pages 2 and 71) and merged one split entry: 4,366 → 4,343 |

Archived: `audit_semantic_tags.py` (AI audit that removed 1,248 wrong tags),
`bb_pronunciation_compare.py` (Blue Book pronunciation guides against Parks's IPA),
`add_feedback_table.py` (created the `community_feedback` table).

## 3. Grammar (March 2026)

| Script | Phase | Status | What it does |
|---|---|---|---|
| `sound_changes.py` | 2.3 | **live** | Parks's 24 sound-change rules as code. `--test` runs 11 examples from the book |
| `extract_appendices.py` | 3.1 | pipeline, **AI** | Reads Parks's appendices, abbreviation list and grammar chapter from scanned pages into [../extracted_data/](../extracted_data/) |
| `morpheme_inventory.py` | 3.1 | **live** | The 30-slot verb template and a conjugation engine. `--validate`: 611 of 770 Appendix 1 forms exact (79.4%) against the appendix as corrected from the page on 2026-11-13; the 90.3% reported before was against a copy with 152 misread forms |
| `accent_rules.py` | 3.1 | **live** (used only by `morpheme_inventory.py`) | Four rules for where the accent falls in conjugated forms. Worked out from the misread copy of Appendix 1 and not checked since it was corrected |
| `stem_extractor.py` | 3.1, 4.3 | **live** | Predicts form 2 from headword, class and preverb. `--validate`: 1,915 of 2,197 exact (87.2%). `--confidence` fills `form2_confidence` |
| `noun_possession.py` | 3.1.5 | pipeline | Classifies nouns by possession system; fills `noun_stems`, `kinship_paradigms`, `possession_examples` |
| `possession_engine.py` | 3.1.5 | **live** | Builds "my / your / his" forms and locative forms for a noun; behind `/api/possession/<headword>`. `--test`: 59 of 59, including ten attested *-hiriʔ* words |
| `example_filter.py` | 3.1.5 | **live** | Decides whether an example sentence really contains a headword or only looks as if it does |
| `function_word_inventory.py` | 3.1.6 | applied | Seeded the `function_words` table |
| `extract_function_words.py` | 3.1.6 | pipeline, **AI** | Pulled function words out of Blue Book phrases |
| `classify_function_words.py` | 3.1.6 | applied | Added position rules and subclasses to all 418 function words |

Archived: `analyze_dual_plural.py`, `conjugation_gemini_collab.py` (AI-assisted
diagnosis of conjugation mismatches), `retry_failed_grammar.py`,
`merge_grammar_retries.py` (recovered four grammar pages the first extraction lost).

**Do not try again to conjugate every dictionary verb from scratch.** The
conjugation engine reproduces 90% of the seven Appendix 1 verbs but only about
15% of forms across the whole dictionary. `person_forms.py` (below) gets
unlisted forms by changing the prefix of a form the dictionary does attest.

## 4. Sentences and lessons (March and September 2026)

| Script | Phase | Status | What it does |
|---|---|---|---|
| `sentence_templates.py` | 3.2a | **live** | Ten sentence patterns taken from Blue Book dialogues. `test`: 34 of 34 |
| `template_slot_fillers.py` | 3.2a | **live** | The words offered for each slot, all attested in the Blue Book |
| `person_forms.py` | 3.2b | **live** | Derives 2nd-person and absolutive forms from attested forms. `--validate-appendix`: 27 of 27 |
| `display_utils.py` | 5.2 | **live** | Cleans headword notation for display; learner spelling and respelling of inflected forms |
| `build_lessons.py` | 5.1 | pipeline | Parses the 20 Blue Book lessons from the text file into the `lessons` table and `extracted_data/lessons.json`. No AI |
| `extract_lesson_gaps.py` | 5.1 | applied, **AI** | Re-extracted the vocabulary of Lessons 3 and 4, which the two-column layout had scrambled |
| `link_bb_vocab.py` | 5.1 | applied | Linked more lesson vocabulary to dictionary entries (339 of 531), conservatively |
| `fix_lesson_titles.py` | 5.1 | applied | Repaired 14 OCR errors in lesson titles, each with stated evidence |

## 5. Audits and repairs (September to November 2026)

| Script | Status | What it does |
|---|---|---|
| `_audit_sample.py`, `_audit_sample_e2s.py` | test | Draw the stratified samples that the 2026-09-01 audit checked against the page |
| `fix_audit_issues.py` | applied | The repairs from that audit: c/č spelling, lost senses, missing IPA, leftover OCR characters, doubled examples, line-break hyphens |
| `upgrade_phonetics_from_textlayer.py` | applied | Replaced 130 IPA forms that had lost their special characters, using the PDF's own text layer as a second source |
| `fix_respelling_artifacts.py` | applied | Regenerated 68 respellings that contained stray `?` marks |
| `fix_pronunciations.py` | applied; its respeller is **live** (imported by the script below) | Repaired respellings of optional sounds and `{k/t}` alternations (1,273 entries) |
| `fix_data_2026_11.py` | applied | The fixes of 2026-11-13: accent marks the character decoding had dropped (269 entries), 28 page numbers, letter-spaced text in 39 places, six duplicate rows, two single entries. Its docstring has the character table. Report: `reports/fix_data_2026-11-13_report.txt` |

## 6. Publishing (September to November 2026)

| Script | Status | What it does |
|---|---|---|
| `build_static_site.py` | **live** | Builds [../docs/](../docs/) from the database. See [../DEPLOYMENT.md](../DEPLOYMENT.md) |
| `freeze_flashcard_sets.py` | pipeline | Writes `curriculum/flashcard_sets.json`. Run only for a deliberate change to the curriculum: learners' progress is keyed to its week numbers |
| `build_weekly_flashcards.py` | pipeline | Writes `curriculum/weekly_flashcards.md`: every card as front and back, for copying by hand. Word-building notes come from the version 2 analysis; weeks held for review are left out |
| `build_flashcard_pdfs.py` | pipeline | Turns that file into printable sheets, four cards to a page |
| `anki_export.py` | unused | Exports Anki decks. Works, but nobody uses Anki here; in-app study replaced it |

## 7. Word construction (November 2026)

| Script | Status | What it does |
|---|---|---|
| `root_extraction.py` | **live** (the v2 analysis imports three helpers) | Version 1: segments every entry from the stored etymology parse and ranks roots by frequency |
| `build_root_curriculum.py`, `root_curriculum_spec*.py` | **live** (the flashcard builder and `fix_pronunciations.py` import its spelling helpers) | Version 1: renders the lesson plans in `curriculum/roots/` from a hand-written specification |
| [`morphology_v2/`](morphology_v2/) | current | Version 2: the evidence-tiered analysis. `run.py --all` regenerates `curriculum/roots_v2/` |

Version 1's outputs are superseded by version 2; see
[../curriculum/README.md](../curriculum/README.md) for why both are still here.

## 8. Source-fidelity audit (November 2026)

Does every stored value match the printed page? The instruction is
[../prompts/source_fidelity_audit.md](../prompts/source_fidelity_audit.md); the
results are in [../reports/source_audit_2026-11/](../reports/source_audit_2026-11/).
The audit itself **changed no data**; it ended in a list of proposed fixes.
The fixes with solid evidence were then applied by the three `applied` scripts
below, each of which wrote a record into the same reports folder.

| Script | Status | What it does |
|---|---|---|
| `db_dump.py` | **live** | Writes the database to [../DB/dump/](../DB/dump/) as text, one row per line, so that it is in git; `--restore` builds a database from that text; `--verify` proves the round trip. Run `--write` after any change to the database |
| [`source_audit/`](source_audit/) | test | The audit, stage by stage. `status.py` prints how far it has got. See its README |
| `apply_audit_fixes_2026_11.py` | applied | The reviewed fixes: 807 changes to the database, the JSON dictionary and `extracted_data/` (Appendix 1: 152 forms; appendices 2 and 3; chapters 3 and 4; verb forms; citations; headwords; column labels; one entry added, one removed). Lists what it left for a person. Record: `applied_fixes_report.txt` |
| `restore_parks_ipa.py` | applied | Sets every Parks entry's phonetic form to the form printed in its entry, in Parks's own symbols; makes the respelling again; brings both JSON dictionaries and the frozen flashcards in step. Record: `ipa_restored_report.txt` |
| `apply_bluebook_scan_fixes.py` | applied | Corrects the Blue Book forms from the blind readings of the scan (accents, OCR slips) in attestations, examples, lessons and `extracted_data/`; corrects three entries built on misread forms; removes the made-up phonetic forms of the Blue Book-only entries. Record: `bluebook_applied_report.txt` |
| `ipa_notation.py` | **live** | The one place that knows both notations: Parks's (`·`, `–`, ə́, ɪ́), which is stored, and the older working one (hyphen, bullet, à, í), which the respelling code was written for. `to_working()` converts; the respelling scripts call it on the way in |
| `check_simplified_forms.py` | test | Makes the respelling and the learner spelling again for every Parks entry and compares them with what is stored. Changes nothing. Run it after any change to phonetic forms or headwords |

All three `applied` scripts change nothing without `--apply`, back the files
up first, and add to their record on a later run without overwriting it.

The audit's two findings that matter for every other script:

- **The dictionary PDFs' text layer is the typesetter's own text**, and the AI
  parse was made from it. With the character table in
  `source_audit/chartable.py` (verified against the printed glyphs) it can be
  compared with the database field by field: `source_audit/s2e_compare.py`.
  Run it after any change to dictionary data.
- **Anything read by an AI model from a page image needs a second reading.**
  Appendix 1 as stored had 152 wrong forms in 770.

## Known problems

- **The engines were tuned against answer keys that had errors.** The stored
  copy of Appendix 1 had 152 of 770 forms differing from the page; it was
  corrected on 2026-11-13. Against the corrected appendix
  `morpheme_inventory.py --validate` gives 79.4% (it gave 90.3% against the
  faulty one) and `person_forms.py --validate-appendix` 25 of 27. The rules in
  `accent_rules.py` came from the faulty copy and have not been checked again.
  The verb forms `stem_extractor.py --validate` is scored against, the
  sound-change examples and the kin terms `possession_engine.py` reads were
  corrected the same day.
- **Phonetic forms are stored in Parks's notation since 2026-11-13.** A script
  that splits a phonetic form on a hyphen, or looks for a bullet, à or
  unaccented-looking í, was written for the older working notation. Pass the
  form through `ipa_notation.to_working()` first, as `fix_pronunciations.py`
  and `respell_and_normalize.py` do. `generate_simplified_pronunciation` in
  `respell_and_normalize.py` is the older respelling function and gives `? ?`
  for a phonetic form of several words; stored respellings are made by
  `fix_pronunciations.respell_phonetic`.
- **Blue Book forms outside the corrected tables still lack the printed
  accents**: `bb_gap_triage`, `bb_function_words`, `function_words`, and the
  forms written into `sentence_templates.py` and `template_slot_fillers.py`.
- `possession_engine.py` offers an instrumental form ("with, using ...") for
  every noun the web app asks about, animals included: its animacy filter needs
  topic tags, and the API does not pass them. Its stem stripper also removes
  `-kis` from nouns where that is not the diminutive (*rakis* 'wood' is cut to
  *ra*). Both give forms that look attested and are not.
- **A dry run can overwrite a report.** Some applied scripts (for example
  `build_lessons.py` and `link_bb_vocab.py`) write their report file on a dry
  run too. Run one today and the record of what it changed when it was applied
  is replaced by "nothing to change". Copy the report first, or read the script.
  `fix_pronunciations.py` and `fix_data_2026_11.py` write their report only
  with `--apply`.
- `person_forms.py`, `sentence_templates.py` and a few others print Pawnee
  characters straight to the console and need `PYTHONIOENCODING=utf-8` on
  Windows.
- `s2e_parser.py` and `run_parser_e2s.py` use the old `google.generativeai`
  package. New code should use `google.genai`, as `audit_entries.py` does.
