# reports/source_audit_2026-11/

The source-fidelity audit of 2026-11-13: every stored value that claims to
copy a printed page, compared with the page. **Read `findings.md` first.**

The audit itself changed no data. Its instruction is
[../../prompts/source_fidelity_audit.md](../../prompts/source_fidelity_audit.md);
its code is in [../../scripts/source_audit/](../../scripts/source_audit/).

The fixes with solid evidence were applied afterwards, the same day. The files
of the audit are left as they were, as the record of what it found; what was
changed is in the three reports under "What was applied afterwards".

## What was applied afterwards

| File | What it is |
|---|---|
| `applied_fixes_report.txt` | Every change `scripts/apply_audit_fixes_2026_11.py` made: 807 in the first run and 12 in four later runs (a headword, two learner spellings, the last `b`-for-`h` forms of the grammar chapter, the phonetic forms of sound-change Rule 24). Stored value, new value, book page. Ends with what was left for a person |
| `ipa_restored_report.txt` | `scripts/restore_parks_ipa.py`: the phonetic forms set to Parks's own symbols. Lists the 75 corrected in content, the 9 added, the 54 respellings and 3 learner spellings that changed |
| `bluebook_rest_graded.json`, `blind_readings/bluebook_rest_part1.json` to `part6.json` | The 843 Blue Book crops the audit had not reached, read blind from the scan, and each reading compared with the stored form. With the audit's 153 crops they cover 949 distinct stored forms: every one that has a page |
| `bluebook_applied_report.txt` | `scripts/apply_bluebook_scan_fixes.py`: the 715 forms corrected, the three entries built on misread forms, and the forms left for a person: 77 after the first reading, 42 after the second (the run of 2026-11-14 is added below the first) |
| `after_fixes/s2e_differences.jsonl`, `after_fixes/s2e_summary.json` | The dictionary entries compared with the page again, most recently on 2026-11-14 after `complete_from_print.py`: 50,807 of 50,837 fields identical (99.94%), 37 differences left (after the first fixes: 50,597 of 50,757, 218 left; the comparison has since been widened by 80 fields) |
| `after_fixes/alphabet_check.json` | The letter check run again: no stored Skiri form has a letter Skiri lacks. The 15 hits left are English words and formula symbols ("etc.", "[+ neg.]", "V") |
| `print_completion_report.txt` | `scripts/complete_from_print.py` (2026-11-14): every value set from the text layer, old and new, in eleven sections (derived stems, examples, citations, glottal stops, line-end hyphens, spacing, etymology glosses, single values, forms not printed, punctuation, piece lists), and the values left as they are with the reason for each |
| `bluebook_second_look.json`, `blind_readings/bluebook_second_look.json` | The second blind reading of the 77 Blue Book forms the first reading left open, and its grading: two readings agree on 55, of which 35 are the stored row's own form and were applied; 42 forms are still open |
| `chapter4_third_witness.json` | The grammar chapter's doubtful words with what each witness says (stored text, blind reading, dictionary): three corrected, two confirmed as stored. The rest were settled by the second reading, below |
| `chapter4_second_reading.json`, `blind_readings/chapter4_second_part1.json` to `part3.json` | The second blind reading of the whole grammar chapter (2026-11-14; three readers, 613 forms) and its grading against the stored chapter and the first reading: 38 words, 22 pieces of breakdown lines and 22 named places (Table 17) corrected, each with what both readers have and how the word was tied to its place. The two blind readings do not differ on one Skiri word |
| `bluebook_right_place.json`, `blind_readings/bluebook_right_place.json` | 25 of the open Blue Book forms found at their own place on the page and read there (2026-11-14): 18 corrected, 7 confirmed as stored. 17 forms are left; they are the last section of `bluebook_applied_report.txt` |

To compare the live database with the page again without overwriting the
audit's record:

```bash
python scripts/source_audit/s2e_compare.py --out reports/source_audit_2026-11/after_fixes
```

## For a person

| File | What it is |
|---|---|
| `findings.md` | What was checked, what was found, how far to trust it, what to do next |
| `proposed_fixes.jsonl` | One line per proposed change, as the audit left it: where, what was stored, what is printed, the value to store instead where that is unambiguous, the grade of the evidence, a severity. "Stored" means stored on 2026-11-13 before the fixes; most lines outside the English-to-Skiri section have been applied since |
| `work/review.html` | The fixes that touch a Pawnee form or a meaning, each with a crop of the page beside it. Not in git: build it with `python scripts/source_audit/build_report.py --review` and open it in a browser |
| `approved_fixes.txt` | Does not exist until someone approves fixes: one fix id per line. `scripts/source_audit/apply_fixes.py` applies those and nothing else |

## The record

| File | Stage | What it is |
|---|---|---|
| `STATE.json`, `progress.log` | all | How far the audit got, stage by stage, and when. `python scripts/source_audit/status.py` prints them |
| `baseline.json` | 0 | The hash of every input at the start, and the result of each existing test suite. `baseline.py --check` showed the same 649 hashes at the end |
| `character_table.json` | 1 | Every (font, character code) pair of the text layer and what is printed for it |
| `character_readings.json` | 1 | What was read off the contact sheets, row by row, before the key was opened |
| `s2e_differences.jsonl`, `s2e_summary.json` | 2 | Every difference between the database and the Skiri-to-English text layer, with its kind, class (noise, convention, difference) and severity; the counts, with the noise rules spelled out |
| `recall_test.json` | 2 | The 510 errors planted in a copy of the database and whether each was reported |
| `s2e_graded.jsonl` | 3 | The 900 differences with a grade each, and for those read from a crop, the blind reading |
| `appendix1_differences.json`, `appendix1_third_look.json` | 4 | Appendix 1: the 152 forms on which the stored copy and the blind reading differed; the third look at them (40 during the audit, all 152 before the fixes were applied) |
| `appendix2_reading.json`, `appendix3_findings.json` | 4 | Appendix 2 as read from the page; Appendix 3's differences |
| `chapter4_differences.json`, `chapter3_differences.json` | 4 | The grammar chapter and the sound-change rules against their blind readings |
| `abbreviations_differences.json`, `alphabet_check.json` | 4 | The abbreviation list against its text layer; stored forms with a letter Skiri does not have |
| `bluebook_check.json`, `bluebook_readings.json`, `bluebook_graded.json` | 5 | Blue Book forms against the scan's OCR layer (which proved to be their source); the blind reading of 153 crops of the scan; the comparison |
| `blind_readings/` | 3, 4 | What the blind readers wrote down, as they wrote it: the 369 dictionary crops (with the stored value and the text-layer value beside each reading), Appendix 1, Appendix 3, chapters 3 and 4 |
| `e2s_differences.jsonl`, `e2s_summary.json` | 6 | The current English-to-Skiri JSON against the text layer |
| `e2s_db_tables_summary.json` | 6 | The same comparison for the database tables `english_index` and `cross_references`, which are an older copy; counts only, because the remedy is to re-import them |
| `audit_numbers.json` | 7 | Counts of the proposed fixes by source, severity, kind and grade |

## Added on 2026-11-14, after the audit (third part of that day)

| File | What it is |
|---|---|
| `front_matter_reading.json` | Chapters 2 and 5 of the dictionary's front matter in two readings: how many forms and tables, and where the readings differ (nowhere, for the 195 Skiri forms) |
| `blind_readings/front_matter_ch2_a.json`, `..._ch2_b.json`, `..._ch5_a.json`, `..._ch5_a2.json`, `..._ch5_b.json` | The five readings, cut down to forms, tables, headings and figure labels. The running text the readers wrote is not kept here: it is in `work/front_matter/`, which is not in git (project log, open item 54). Reading A of chapter 5 is in two files because its first reader was stopped after six pages |
| `after_fixes/e2s_summary.json`, `e2s_differences.jsonl`, `e2s_db_tables_summary.json`, `e2s_db_tables_differences.jsonl` | The English-to-Skiri comparison run again after the index was rebuilt from the page: 32,632 of 32,636 fields equal for the file and for the tables. The files of the same name one folder up are the audit's own record (95.90% and 77.69%) and are not overwritten |

The tables of chapter 4 as printed are in `extracted_data/grammatical_overview_tables.json`;
they were put together from `blind_readings/chapter4_part*.json` and
`chapter4_second_part*.json` by `scripts/source_audit/chapter4_tables.py`.

## Grades and severities

| Grade | Meaning |
|---|---|
| `confirmed` | The page image was read and shows the printed value given, not the stored one |
| `text-layer` | The text layer differs from the stored value; not read from an image, but it belongs to a family of differences whose read members (at least 30) were all confirmed, or follows from the page's geometry |
| `blind-reading` | A blind reading of the page differs from the stored value; not looked at a third time. Every third look that was taken agreed with the blind reading |
| `unresolved` | Not settled |

Severity: **1** a Pawnee form or its IPA; **2** meaning (a gloss, a
translation, a missing sense, example or entry); **3** class, cross-reference,
page; **4** formatting.

## Not in git

`work/`: the decoded text layer page by page, the contact sheets, crops and
tiles, the blind readers' raw files, the review page. All of it is rebuilt by
the scripts, except the blind readers' raw files, whose content is carried
into the files above.
