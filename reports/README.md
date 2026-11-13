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
| `bb_vocab_linking.txt` | 2026-10-12 | Lesson vocabulary linked to dictionary entries, and the cases left for a person to decide |

**The source-fidelity audit of 2026-11-13 has its own folder:
[source_audit_2026-11/](source_audit_2026-11/).** It is the first audit that
compared everything with the page instead of a sample: every dictionary entry
against the PDF's text layer, and every table that an AI model had read from
page images against a second, blind reading. Start with its `findings.md`.
The fixes it led to were applied the same day; the three reports of what was
changed (`applied_fixes_report.txt`, `ipa_restored_report.txt`,
`bluebook_applied_report.txt`) are in the same folder. It
supersedes the "verdict: sound" of the 2026-09-01 audit for the appendices,
the grammar chapter and the English index, which that audit did not reach.

The word-construction analysis of 2026-11-12 has
its own folder: [../curriculum/roots_v2/validation_report.md](../curriculum/roots_v2/validation_report.md).

## Phase reports

| Report | Phase | What it shows |
|---|---|---|
| `audit_semantic_tags.txt` | 2.1 | The AI audit of topic tags that removed false matches |
| `phase_2_2_blue_book.txt` | 2.2 | Blue Book vocabulary matched to the dictionary, lesson by lesson |
| `phase_2_2_pronunciation.txt`, `phase_2_2_pronunciation_phonetic.txt` | 2.2 | Blue Book pronunciation guides compared with Parks's respelling and with his IPA |
| `bb_gap_triage.txt` | 2.2 | The 516 Blue Book items with no dictionary match, sorted into eight kinds |
| `phase_2_3_sound_changes.txt` | 2.3 | The 24 sound-change rules and how they test |
| `phase_3_1_morphemes.txt` | 3.1 | The verb template and conjugation results (this copy dates from 2026-03-09; current figures are in the project log) |
| `phase_3_1_5_noun_possession.txt` | 3.1.5 | Nouns by possession system |
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
