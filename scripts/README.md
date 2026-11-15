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
| `sound_changes.py` | 2.3 | **live**, as a reference | Parks's 24 sound changes with his examples (the table `sound_change_rules`), and the code for each. **Not an engine**: `--measure` compares the code with the 39 examples Parks prints and gets 8. `--check-table`: the table is the catalogue of the file. It writes the table only with `--write-table`. The word-construction analysis reads single rules from it |
| `extract_appendices.py` | 3.1 | pipeline, **AI** | Reads Parks's appendices, abbreviation list and grammar chapter from scanned pages into [../extracted_data/](../extracted_data/) |
| `stem_extractor.py` | 3.1 | **live**, as a checker | Predicts form 2 from headword, class and preverb. Used by the word-construction analysis to test whether a headword and its printed form 2 agree; never to show a form. `--validate`: 1,915 of 2,197 exact (87.2%), on the forms its rules were read from; there is no unseen figure. The confidence score it used to store is gone |
| `printed_noun_forms.py` | 3.1.5 | **live** | For a noun, what Parks and the Blue Book print: the Appendix 3 row of a kin term, the one-word examples of the entry that end in *-kat*, *-hiriʔ* or *-ru*, the combining forms, Blue Book words with "my", "your", "his". Computes nothing. Behind the box "Printed forms of this noun" on entry pages. `--check`: 734 of 1,706 nouns have something printed; every form shown is a stored value of that entry. It replaced the possession engine on 2026-11-14 |
| `example_filter.py` | 3.1.5 | **live** | Decides whether a Blue Book sentence tied to an entry really contains the headword. No longer applied to Parks's own examples, which it hid (2,224 of 2,652) |
| `function_word_inventory.py` | 3.1.6 | applied | Seeded the `function_words` table |
| `extract_function_words.py` | 3.1.6 | pipeline, **AI** | Pulled function words out of Blue Book phrases |
| `fix_function_words.py` | 3.1.6 | applied | The pass over the two function-word tables against the scan's readings (2026-11-14): in `bb_function_words` 22 words corrected and 1 row deleted; in the Blue Book rows of `function_words` 10 corrected and 8 deleted. Meanings and word classes were not checked. `--check` |
| `classify_function_words.py` | 3.1.6 | applied | Added position rules and subclasses to all 418 function words |

Archived: `analyze_dual_plural.py`, `conjugation_gemini_collab.py` (AI-assisted
diagnosis of conjugation mismatches), `retry_failed_grammar.py`,
`merge_grammar_retries.py` (recovered four grammar pages the first extraction lost).

**Withdrawn on 2026-11-14, now in [../archived/scripts/](../archived/scripts/)**, each
with a note at its head saying why: `morpheme_inventory.py` (the conjugation
engine: 15.0% of the dictionary's verb forms), `accent_rules.py` (marked an
accent in 81 cells of Appendix 1 where the page marks 26), `possession_engine.py`
and `noun_possession.py` (answered 1,671 of 1,706 nouns with a phrase beginning
with an OCR slip). Nothing imports them. The tables they wrote are dropped.

**Do not try again to conjugate every dictionary verb from scratch.** The
withdrawn engine reproduced 79.4% of the seven Appendix 1 verbs, which it was
fitted to, and 15.0% of the forms across the whole dictionary. `person_forms.py`
(below) gets a few unlisted forms by changing the start of a form the
dictionary does print, and labels them.

**The rule for everything in this section and the next**, since the engines
review of 2026-11-14 (section 9): a form the code makes is *computed*, is
marked so wherever it is shown, and is never stored beside copied forms. A
test proves nothing unless its expected forms are printed in a source and the
rule was not fitted to them. Before repairing or adding a rule, split the
printed forms into a part you may look at and a part you do not open until the
end, write the split down first, and report the result on the second part:
[engines_review/person_forms_repair.py](engines_review/person_forms_repair.py)
is the pattern.

## 4. Sentences and lessons (March and September 2026)

| Script | Phase | Status | What it does |
|---|---|---|---|
| `sentence_templates.py` | 3.2a | **live** | The sentence builder, rebuilt on 2026-11-14. A pattern starts from a sentence the Blue Book prints; a word may be swapped only for another printed word, given by its row. The result says "printed in the Blue Book, lesson N" or "put together here; not printed". Dictionary verbs are a separate part in Parks's spelling, chosen by entry. `--test`: 38 of 38, every expected form read from a row. `--check`: every form named in the two files is what its row or entry holds, zero exceptions |
| `template_slot_fillers.py` | 3.2a | **live** | The 13 printed sentences the builder starts from, each named by the number and the text of its row, and Parks's three question words by entry. No form is typed here in any other way; `sentence_templates.py --check` enforces it |
| `person_forms.py` | 3.2b | **live** | Makes "you" forms and question forms from a printed form, each to be shown with the label "derived; not checked against a printed form". Repaired on 2026-11-14: three rules built on misread forms removed, no first person invented, no present or future for "I" and "you". `--validate-appendix`: 26 passed, 0 failed, 2 declined; it fails on any mismatch. On 1,059 verbs it never saw, its "he/she" question form starts as the dictionary's form 4 starts for 794 of 816 (97.3%); it gives no form for 243 |
| `display_utils.py` | 5.2 | **live** | Cleans headword notation for display; learner spelling and respelling of inflected forms |
| `build_lessons.py` | 5.1 | applied; do not run again | Parsed the 20 Blue Book lessons from the OCR text file into the `lessons` table and `extracted_data/lessons.json`. No AI. The table has since been corrected from the scan and its dialogues paired; `--apply` now refuses to write over it unless `--from-scratch` is given, and a dry run no longer writes the JSON file |
| `extract_lesson_gaps.py` | 5.1 | applied, **AI** | Re-extracted the vocabulary of Lessons 3 and 4, which the two-column layout had scrambled |
| `link_bb_vocab.py` | 5.1 | applied | Linked more lesson vocabulary to dictionary entries (339 of 531), conservatively |
| `fix_lesson_titles.py` | 5.1 | applied, superseded | Repaired OCR errors in lesson titles by rule (*KIRIKJ* to *KIRIKI*). The scan reads *KIRIKÉ*: 12 titles were set from the Blue Book table on 2026-11-14 by `fix_lesson_text_ocr.py`. Do not run again |
| `fix_lesson_text_ocr.py` | 5.1 | applied | Brought the lessons' running text and titles in step with the audit's reading of the scan: 214 places in 17 lessons, 12 titles; `extracted_data/lessons.json` made a copy of the table. It left 196 places where only an accent differed, for the page; they were settled by `apply_lesson_page_reading.py`. `--check` |
| `apply_lesson_page_reading.py` | 5.1 | applied | **The lessons' text as the page prints it** (2026-11-14). Puts into the `lessons` table what `source_audit/lesson_text_reading.py` read from the scan, line by line: 42 changes by hand after a second look, 8 titles, 286 words where one reading settles it (an accent, a raised dot, an apostrophe, the OCR's known slips), the next lesson's title and the glossary cut from the end of the notes; 13 rows of the Blue Book table that are lines of the lessons and had never been read at their own line. Never takes away an accent, dot or apostrophe on one reading. `--check` |
| `pair_lesson_dialogues.py` | 5.1 | applied | **Each dialogue line with its English** (2026-11-14). The parser had stored the two columns of a dialogue as separate lines: in 83 of 156 lines the English stood in the Pawnee field or was missing. A Pawnee line now takes the English the page prints to its right on the same row (from the scan's text layer); merged lines are cut, continuation lines joined, and the section of notes that sat inside lesson 2's third dialogue is the first of that lesson's notes. 105 lines. Changes no Pawnee word. `--check` |
| `relink_bluebook.py` | 5.1 | applied | Judged again every tie of a Blue Book word to a dictionary entry that was not made by the form: 65 re-tied, 349 untied (257 of 1,026 rows are tied now). A Blue Book sentence is an example of an entry only if one of its words is tied to it: 43 of 88 kept. Sets `blue_book_attested` from the ties. `--check` |

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
| `build_static_site.py` | **live** | Builds [../docs/](../docs/) from the database: the dictionary file, the data of the learning pages (`web/learning.py`), the pages, the two printable documents. See [../DEPLOYMENT.md](../DEPLOYMENT.md) |
| `freeze_flashcard_sets.py` | pipeline | Writes `curriculum/flashcard_sets.json`. Run only for a deliberate change to the curriculum: learners' progress is keyed to its week numbers |
| `build_weekly_flashcards.py` | pipeline | Writes `curriculum/weekly_flashcards.md`: every card as front and back, for copying by hand. Word-building notes come from the version 2 analysis; weeks held for review are left out |
| `build_flashcard_pdfs.py` | pipeline | Turns that file into printable sheets, four cards to a page |
| `build_printables.py` | pipeline | Writes `curriculum/printables/`: the flashcard words as a printable list and Parks's Appendix 1 in full |
| `build_review_packet.py` | pipeline | Writes `community_review/`: the packet for the Pawnee Nation's language and culture people (PDF, web page, answer sheet). The built files are not in git. Build it again on the day it is sent |
| `anki_export.py` | unused | Exports Anki decks. Works, but nobody uses Anki here; in-app study replaced it. Shows the printed form 2 wherever one is printed (it used to ask the form 2 score, removed on 2026-11-14) |

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
The fixes with solid evidence were then applied by the `applied` scripts
below, each of which wrote a record into the same reports folder. On
2026-11-14 two more followed: the page citations, and everything else the
text layer could settle.

| Script | Status | What it does |
|---|---|---|
| `db_dump.py` | **live** | Writes the database to [../DB/dump/](../DB/dump/) as text, one row per line, so that it is in git; `--restore` builds a database from that text; `--verify` proves the round trip. Run `--write` after any change to the database |
| [`source_audit/`](source_audit/) | test | The audit, stage by stage. `status.py` prints how far it has got. See its README |
| `apply_audit_fixes_2026_11.py` | applied | The reviewed fixes: 807 changes to the database, the JSON dictionary and `extracted_data/` (Appendix 1: 152 forms; appendices 2 and 3; chapters 3 and 4; verb forms; citations; headwords; column labels; one entry added, one removed). Lists what it left for a person. Record: `applied_fixes_report.txt` |
| `restore_parks_ipa.py` | applied | Sets every Parks entry's phonetic form to the form printed in its entry, in Parks's own symbols; makes the respelling again; brings both JSON dictionaries and the frozen flashcards in step. Record: `ipa_restored_report.txt` |
| `apply_bluebook_scan_fixes.py` | applied | Corrects the Blue Book forms from the blind readings of the scan (accents, OCR slips) in attestations, examples, lessons and `extracted_data/`; corrects three entries built on misread forms; removes the made-up phonetic forms of the Blue Book-only entries. Since 2026-11-14 it also takes a form on which two independent readings agree (35 of the 77 the first reading left open) and carries the corrected forms into `bb_gap_triage`, `bb_function_words` and the attestations' full sentences (628 values), and a form read at its own place on the page (`source_audit/bluebook_right_place.py`: 18 more). 17 forms are left. Record: `bluebook_applied_report.txt` |
| `fix_page_citations.py` | applied | Sets `page_number` to the page of the printed book for every Parks entry (3,511 held the number of a PDF file, 348 less). The page comes from the audit's pairing of each entry with its printed entry; the step from file number to book page is read off the page number printed on all 181 pages. Follows through to the JSON dictionary and the frozen flashcards; entry ids are left alone. `--check` exits 0 when every citation is a book page. Record: `reports/page_citations_report.txt` |
| `complete_from_print.py` | applied | Adds what the dictionary prints and the database lacked, from the text layer alone: 21 derived stems, 18 examples, citations still in stand-in characters, hyphens the typesetter put at line ends (684 values), letter-spaced words, the printed wording of 31 etymology glosses, spaces before punctuation, and removes three verb forms that are not printed. Refuses any new value it cannot find in the printed entry. 1,447 values in 1,178 entries, and 441 piece lists brought in step. Record: `print_completion_report.txt`, which also lists what was left and why |
| `repair_english_index.py` | applied | **The English index rebuilt from the printed page** (2026-11-14). Reads the English-to-Skiri section from the PDF's text layer by its fonts and makes `english_to_skiri_linked.json` and the tables `english_index` and `cross_references` say what the page says: headwords, Skiri terms with preverb, phonetic form and class, links to dictionary entries, cross-references, book pages. `--check` exits 0 while they do; `--show WORD` prints one printed entry as it is read |
| `bluebook_only_entries.py` | applied | For the 93 Blue Book-only entries: finds the form the book prints (87 found) and, where the entry is a word Parks has in the textbook's spelling, the dictionary entry (37; written to `bb_variant_of`). Merges nothing |
| `bluebook_glossary.py` | pipeline | Itemises the Blue Book's glossary from the scan's text layer, checks every page reference against the page it points to, and writes `extracted_data/blue_book_glossary.json` |
| `ipa_notation.py` | **live** | The one place that knows both notations: Parks's (`·`, `–`, ə́, ɪ́), which is stored, and the older working one (hyphen, bullet, à, í), which the respelling code was written for. `to_working()` converts; the respelling scripts call it on the way in |
| `check_simplified_forms.py` | test | Makes the respelling and the learner spelling again for every Parks entry and compares them with what is stored. Changes nothing. Run it after any change to phonetic forms or headwords |
| `check_static_site.js` | test | Runs the published search page's own code (`docs/static/js/skiri.js`, `search.js`) against the published data with a stand-in for the browser: a headword and a verb form are found, citations are book pages, etymologies are escaped, held entries carry no added detail, all entries render. Then the learning pages: every piece shown for a word stands in the derivation the dictionary prints, the seven verbs agree with forms 1 and 2 of their entries, no held entry and no held flashcard week is in the data files, and every link between the pages leads to a file. 28 checks. Needs Node.js. Run it after `build_static_site.py` |

All the `applied` scripts change nothing without `--apply`, back the files
up first, and add to their record on a later run without overwriting it. A
second run of any of them finds nothing to change.

The audit's two findings that matter for every other script:

- **The dictionary PDFs' text layer is the typesetter's own text**, and the AI
  parse was made from it. With the character table in
  `source_audit/chartable.py` (verified against the printed glyphs) it can be
  compared with the database field by field: `source_audit/s2e_compare.py`.
  Run it after any change to dictionary data.
- **Anything read by an AI model from a page image needs a second reading.**
  Appendix 1 as stored had 152 wrong forms in 770.

## 9. Engines review (November 2026)

What is each grammar engine worth, now that the data it was built on has
been corrected? The instruction is
[../prompts/engines_review.md](../prompts/engines_review.md); the results, the
decision paper and the record of what was then done are in
[../reports/engines_review/](../reports/engines_review/). Stages 0 to 3
changed nothing; the owner answered the paper, and Stage 4 carried out the
eight decisions the same day.

| Script | Status | What it does |
|---|---|---|
| [`engines_review/`](engines_review/) | test | The review's own code: `stage1_trace.py`, `build_test_sets.py` (ten test sets from attested forms, with a manifest), `measure_*.py` (one per engine). They measured the engines as they stood in commit `814e8cc` and now refuse to run, so as not to write over that record. `run_all.py --check` still compares the test sets with their sources. `person_forms_repair.py`: the split, the open half and the one opening of the sealed half for the repair of person derivation. See its README |
| `remove_engine_output.py` | applied | Removed from the database what the withdrawn engines had stored: the tables `morpheme_inventory`, `verb_template_slots`, `possession_examples`, `noun_stems`; the form 2 score; three kin rows not from Appendix 3; four OCR slips in `function_words`. `--check`: nothing of it is left |

## Known problems

- **The engines were tuned against answer keys that had errors**, and their
  own tests passed because the tests held the same errors. The engines review
  of 2026-11-14 measured each on printed forms it had not been fitted to and
  the owner decided what became of each: two withdrawn, one replaced by a
  lookup, one rebuilt, one repaired, two kept as reference and checker
  ([../reports/engines_review/stage4.md](../reports/engines_review/stage4.md)).
  The figures in the tables above are the ones to quote; where a figure is on
  forms the rules were read from, the table says so.
- **Phonetic forms are stored in Parks's notation since 2026-11-13.** A script
  that splits a phonetic form on a hyphen, or looks for a bullet, à or
  unaccented-looking í, was written for the older working notation. Pass the
  form through `ipa_notation.to_working()` first, as `fix_pronunciations.py`
  and `respell_and_normalize.py` do. `generate_simplified_pronunciation` in
  `respell_and_normalize.py` is the older respelling function and gives `? ?`
  for a phonetic form of several words; stored respellings are made by
  `fix_pronunciations.respell_phonetic`.
- **The function-word tables hold the scan's readings since 2026-11-14, but
  their meanings were never checked.** `fix_function_words.py` corrected or
  deleted every Blue Book row that was an OCR slip. The English and the word
  class of a row are still what the extraction gave (*pirau* is glossed
  'when'). `bb_gap_triage` is corrected only where a row is a line of a
  lesson (13 rows).
- **A Blue Book word is tied to a dictionary entry only by its form.** Until
  2026-11-14 the table tied *asáki* 'dog' and *arúsa* 'horse' to the entry
  *a* by a shared beginning; `relink_bluebook.py` judged those 414 ties again
  (65 re-tied, 349 untied). A row with two forms (*kiri, pus* 'cat') stays
  untied. The Blue Book examples cite the page of the scan, which is the
  book's page plus 28.
- **The Pawnee of the lessons is as read from the page; the rest of their
  text is not.** `apply_lesson_page_reading.py` holds every Pawnee word of
  the titles, dialogues and notes to what its line of the scan shows. The
  English prose of the notes is OCR text nobody has proofread. The dialogue
  lines are pairs since `pair_lesson_dialogues.py` (the parser had not paired
  the two columns of the page). `build_lessons.py` would write the OCR text
  back over all of it, which is why it now asks for `--from-scratch`. Three
  places lie under a flaw in the scan and are marked with square brackets.
- **A crop cut where the stored letters match can be another line.** Two
  corrections of the audit's first Blue Book reading had been read from a
  line above the row's own (`bluebook_crops_at_another_line.json`);
  `source_audit/lesson_text_reading.py` compares readings by their place on
  the page, which is how they were found.
- **A dry run can overwrite a report.** Some applied scripts (for example
  `build_lessons.py` and `link_bb_vocab.py`) write their report file on a dry
  run too. Run one today and the record of what it changed when it was applied
  is replaced by "nothing to change". Copy the report first, or read the script.
  `fix_pronunciations.py` and `fix_data_2026_11.py` write their report only
  with `--apply`.
- `person_forms.py` and a few others print Pawnee characters straight to the
  console and need `PYTHONIOENCODING=utf-8` on Windows.
- **Some audit scripts write their record when run.**
  `source_audit/alphabet_check.py` rewrites
  `reports/source_audit_2026-11/alphabet_check.json`, the record of the day of
  the audit, with today's findings. Copy the record first.
- `s2e_parser.py` and `run_parser_e2s.py` use the old `google.generativeai`
  package. New code should use `google.genai`, as `audit_entries.py` does.
