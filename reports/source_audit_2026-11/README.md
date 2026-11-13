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
| `bluebook_applied_report.txt` | `scripts/apply_bluebook_scan_fixes.py`: the 715 forms corrected, the three entries built on misread forms, and the 77 forms left for a person |
| `after_fixes/s2e_differences.jsonl`, `after_fixes/s2e_summary.json` | The dictionary entries compared with the page again after all of this: 50,597 of 50,757 fields identical; the 218 differences left |
| `after_fixes/alphabet_check.json` | The letter check run again: no stored Skiri form has a letter Skiri lacks. The 15 hits left are English words and formula symbols ("etc.", "[+ neg.]", "V") |

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
