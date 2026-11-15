# reports/

What each step found. Reports are written by scripts and are not edited by
hand; to bring one up to date, run its script again.

## Audits

Read these first. They say how far the data can be trusted.

| Report | Date | What it covers |
|---|---|---|
| `extraction_audit_2026-09-01.md` | 2026-09-01 | Is the database a faithful copy of the printed dictionary? A stratified sample was checked against the page, and every IPA form against the PDF's own text layer. Verdict: sound. Seven issues were found and repaired the same day; a short list is still open |
| `fix_audit_issues_report.txt` | 2026-09-01 | Exactly what those repairs changed |
| `phonetic_textlayer_upgrade.txt` | 2026-09-01 | The 130 IPA forms replaced from the PDF text layer, old and new |
| `audit_data_construction_2026-10-01.md` | 2026-10-01 | Are the flashcards and the public site built correctly? IPA preservation, provenance, truncation, cultural review. Items A1 to A4, B1 and B4 are done; B2, B3, B5, B6 and C1 to C5 are open |
| `fix_pronunciations_report.txt` | 2026-11-08 | The respelling repair: 1,273 entries, with the 32 left for review |
| `fix_data_2026-11-13_report.txt` | 2026-11-13 | Every change made by `scripts/fix_data_2026_11.py`, old value and new: 269 accent marks restored, 28 page numbers, letter-spaced text, six duplicate rows, two single entries |
| `page_citations_report.txt` | 2026-11-14 | `scripts/fix_page_citations.py`: the 3,511 entries whose page citation was the number of a PDF file, each with the old value and the page of the book |
| `english_index_repair_report.txt` | 2026-11-14 | `scripts/repair_english_index.py`: the English index rebuilt from the printed page. Counts, and in full: what was removed from the file and why, what was added, the links that changed, the three terms left without a link |
| `lesson_text_ocr_report.txt` | 2026-11-14 | The lessons' text. First `scripts/fix_lesson_text_ocr.py`: the audit's readings put into the running text and titles, three runs; every place changed, and the 196 places left where only an accent differed. Then, as the last run in the file, `scripts/apply_lesson_page_reading.py`: every line read from the scan; each change with its strip, its kind and what the audit's reader read at that place; what was cut from the end of the notes; 13 rows of the Blue Book table; the 20 differences left by decision |
| `learner_site_feedback_2026-11-14.md` | 2026-11-14 | One session's feedback on the learner pages, asked for by the owner: what follows good practice for learning a language, five things to change first (lead with the dialogue, phrases to use today, spaced practice, one spelling to write, no stem's pronunciation beside an inflected word), and what not to do. An opinion to weigh, not a plan |
| `lesson_dialogues_pairing_report.txt` | 2026-11-14 | `scripts/pair_lesson_dialogues.py`: which English went to which Pawnee line and why (taken from the row of the page, cut out of a merged line, joined from a continuation line), the two Pawnee lines joined, the section moved to lesson 2's notes, and the three lines printed without English |
| `bluebook_relink_report.txt` | 2026-11-14 | `scripts/relink_bluebook.py`: every tie of a Blue Book word to an entry that was not made by the form, judged again: 65 re-tied, 349 untied, each with the reason; the 45 Blue Book sentences that stopped being examples, and where the other 43 stand |
| `function_words_pass_report.txt` | 2026-11-14 | `scripts/fix_function_words.py`: the 32 rows corrected and the 9 deleted in the two function-word tables, each with the form of the scan it was set to |
| `bluebook_only_entries_report.txt` | 2026-11-14 | `scripts/bluebook_only_entries.py`: for each of the 93 Blue Book-only entries the form the book prints, and for 37 the dictionary entry it is the textbook's spelling of |
| `bb_vocab_linking.txt` | 2026-10-12 | Lesson vocabulary linked to dictionary entries, and the cases left for a person to decide |

**The source-fidelity audit of 2026-11-13 has its own folder:
[source_audit_2026-11/](source_audit_2026-11/).** It is the first audit that
compared everything with the page instead of a sample: every dictionary entry
against the PDF's text layer, and every table that an AI model had read from
page images against a second, blind reading. Start with its `findings.md`.
The fixes it led to were applied the same day; the reports of what was
changed (`applied_fixes_report.txt`, `ipa_restored_report.txt`,
`bluebook_applied_report.txt`, and from 2026-11-14 `print_completion_report.txt`)
are in the same folder. It
supersedes the "verdict: sound" of the 2026-09-01 audit for the appendices,
the grammar chapter and the English index, which that audit did not reach.

**The engines review of 2026-11-14 has its own folder:
[engines_review/](engines_review/).** It asks what each grammar engine is
worth now that the data has been corrected: every engine read in full and
its rules traced to their sources (`profiles.md`), each measured on attested
forms it had and had not been fitted to (`measurements.md`), and a paper
that put eight decisions before the owner (`decision.md`). The owner
answered, and the decisions were carried out the same day (`stage4.md`, the
place to start; `person_forms_repair.md` for the one engine that was
repaired and tested on a sealed half). The figures in the phase reports
below for phases 2.3, 3.1 and 3.1.5 are the engines' own, on their own
tests; two of those engines are withdrawn. This folder is where to find what
they got right.

The word-construction analysis of 2026-11-12 has
its own folder: [../curriculum/roots_v2/validation_report.md](../curriculum/roots_v2/validation_report.md).

## Phase reports

| Report | Phase | What it shows |
|---|---|---|
| `audit_semantic_tags.txt` | 2.1 | The AI audit of topic tags that removed false matches |
| `phase_2_2_blue_book.txt` | 2.2 | Blue Book vocabulary matched to the dictionary, lesson by lesson |
| `phase_2_2_pronunciation.txt`, `phase_2_2_pronunciation_phonetic.txt` | 2.2 | Blue Book pronunciation guides compared with Parks's respelling and with his IPA |
| `bb_gap_triage.txt` | 2.2 | The 516 Blue Book items with no dictionary match, sorted into eight kinds |
| `phase_2_3_sound_changes.txt` | 2.3 | The 24 sound-change rules, the file's self-test of March 2026 ("11 of 11", seven of them the code's own output) and an AI audit of the rules. A record: the script no longer writes it, and the self-test is replaced by `sound_changes.py --measure` (8 of Parks's 39 examples) |
| `phase_3_1_morphemes.txt` | 3.1 | The verb template and conjugation results (this copy dates from 2026-03-09; current figures are in the project log) |
| `phase_3_1_5_noun_possession.txt` | 3.1.5 | Nouns by possession system, from the possession engine, withdrawn on 2026-11-14. A record |
| `bb_function_words.txt`, `extract_function_words.txt` | 3.1.6 | Function words found in Blue Book phrases |
| `phase_5_1_lessons.txt` | 5.1 | The 20 lessons as parsed: pages, dialogue lines, vocabulary linked |

## Working data kept here

These are not reports, but scripts read them from this folder, so they stay.

| File | What it is | Read by |
|---|---|---|
| `_s2e_page_index.json` | The text layer of every Skiri-to-English page PDF: a second, independent reading of the dictionary | `scripts/morphology_v2/` (to find an entry's true page), `fix_audit_issues.py`, `upgrade_phonetics_from_textlayer.py` |
| `_e2s_page_index.json` | The same for the English-to-Skiri pages | `scripts/_audit_sample_e2s.py` |
| `_crossval_phonetics.json` | Result of comparing every IPA form with the text layer; the nine remaining conflicts | nothing |
| `_audit_s2e_sample.json`, `_audit_s2e_fields.txt`, `_audit_e2s_sample.json`, `_audit_e2s_fields.txt` | The samples the 2026-09-01 audit checked, with what was found on the page | nothing |

Reports from the first phases (1.1b to 1.1d) and two analysis write-ups are in
[../archived/reports/](../archived/reports/).
