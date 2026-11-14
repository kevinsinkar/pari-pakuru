# scripts/source_audit/

The source-fidelity audit of November 2026: does every stored value that claims
to copy a printed page match the page? Written from
[../../prompts/source_fidelity_audit.md](../../prompts/source_fidelity_audit.md).
Results: [../../reports/source_audit_2026-11/](../../reports/source_audit_2026-11/).

Every script here reads the database read-only, except `apply_fixes.py`, which
changes nothing without `--apply` and a file of approved fix ids.

The fixes were applied on 2026-11-13 by three scripts one folder up, which
build on this code: `../apply_audit_fixes_2026_11.py`,
`../restore_parks_ipa.py` and `../apply_bluebook_scan_fixes.py`. Since then
the database stores phonetic forms in Parks's own symbols, and the comparison
treats any other symbol as a difference (it used to fold í into his ɪ́ as a
known convention).

```bash
python scripts/source_audit/status.py        # how far the audit has got
```

## By stage

| Stage | Script | What it does |
|---|---|---|
| all | `state.py`, `status.py` | The checkpoint file `STATE.json` and the progress log; `status.py` prints them |
| 0 | `baseline.py` | Hashes every input and runs the existing test suites. `--check` shows whether anything has changed since |
| 1 | `textlayer.py` | Reads the PDF text layer with fonts and positions |
| 1 | `char_inventory.py`, `char_sheets.py`, `char_join.py`, `char_distribution.py` | Every stand-in character by font; contact sheets of each, cut from the pages; the join of the readings with the key; where each accent code stands in all of its occurrences |
| 1 | `chartable.py` | **The verified character table**, as code. `decode()` turns text-layer text into what is printed |
| 1 | `decode_pages.py` | The whole text layer decoded, one file per page |
| 2 | `s2e_segment.py` | Cuts the Skiri-to-English text layer into its 4,244 entries |
| 2 | `compare_core.py`, `s2e_compare.py` | Every stored field looked for in its printed entry, and every printed stretch looked for among the stored fields. Noise rules and conventions are named in `s2e_compare.py`. Since 2026-11-14 it also looks at the qualifier stored with an example and at the derived stems, and a page number that is a file number counts as a difference |
| 2 | `recall_test.py` | Plants 510 known errors in a copy and counts how many the comparison reports. A deleted sense is caught by the amount of printed text left unaccounted for, so that it is seen even beside a stretch that is already listed |
| 2, 6 | `show.py` | Lists differences by field and kind |
| 3 | `crops.py`, `grade.py` | Cuts differences out of the page onto sheets for a blind reading; grades them from the readings |
| 4 | `appendix_tiles.py` | Tiles of the pages that have no text layer |
| 4 | `appendix1_compare.py`, `chapters_compare.py`, `abbrev_compare.py`, `alphabet_check.py` | Appendix 1, chapters 3 and 4 and the abbreviation list against their second readings; the check that every stored Skiri form uses only Skiri letters |
| 5 | `bluebook_check.py`, `bluebook_crops.py` | Blue Book forms against the scan: the Blue Book-only entries and a sample of 60 |
| 5 | `bluebook_rest.py` | The 843 Blue Book forms the audit had not reached, cut from the scan for reading (after the audit); `--grade` compares the readings with the stored forms |
| 5 | `bluebook_second_look.py` | The 77 forms the first reading left open, cut again with the whole line and its neighbours, for a second reader who sees only the images (2026-11-14); `--grade` says where the two readings agree. `scripts/apply_bluebook_scan_fixes.py` takes the agreed ones |
| 5 | `bluebook_right_place.py` | The Blue Book forms two readings left open because the crop had shown a longer or another word: finds the row's own place on the page (where the stored letters stand directly before the English stored with the row, or once as a word by itself), cuts it, and `--grade` judges the reading as the first reading was judged (2026-11-14: 25 found, 18 corrected, 7 confirmed) |
| 4 | `chapter4_third_witness.py` | The grammar chapter's doubtful words weighed against the dictionary's printed forms: where the blind reader's form is a dictionary form and the stored one is printed nowhere, both witnesses agree. Corrects only the three words where they differ in letters (`--apply`); records a verdict for all of them |
| 4 | `chapter4_second_reading.py` | **The grammar chapter against two blind readings** (2026-11-14). `--sheets` cuts the pages for the second readers, one folder each; `--zoom` draws part of a tile larger for a reader. Without options it grades: every stored Skiri word against both readings, the breakdown lines piece by piece, and the places named one by one in `BY_HAND` (Table 17). `--apply` corrects what both blind readings agree on. Run it after any change to `extracted_data/grammatical_overview.json`: it should report nothing to correct |
| 6 | `e2s_compare.py` | The English-to-Skiri section against its text layer; `--source db` for the database tables, `--source json` for the current JSON |
| 7 | `build_report.py`, `apply_fixes.py` | The list of proposed fixes and the review page; the script that applies approved fixes |

## To run it again

The comparisons with the text layer take seconds and need no AI:

```bash
python scripts/source_audit/decode_pages.py       # once; a minute
python scripts/source_audit/s2e_segment.py
python scripts/source_audit/s2e_compare.py --out reports/source_audit_2026-11/after_fixes
                                                  # the live database against the page; without --out it
                                                  # overwrites the audit's own record of what it found
python scripts/source_audit/recall_test.py        # does the comparison still catch planted errors?
python scripts/source_audit/e2s_compare.py --source json
python scripts/source_audit/alphabet_check.py
```

Run these after any change to dictionary data. The stages that read page
images (1, 3, 4, 5) were done by a model reading crops and tiles; their
readings are kept in the reports folder, so the grading can be re-run without
reading anything again.

## Things to know

- **A sub-agent doing a blind reading must not see stored data.** It gets
  image paths and a transcription format, nothing else. The briefs used are in
  the session that ran the audit; the pattern is in the prompt.
- **Blind readings are expensive.** Each reader used about 230,000 tokens for
  eight to ten sheets, because it enlarges each image several times to be sure
  of accents. Use them where there is no text layer or where two readings
  disagree, not as a first pass. The second reading of the grammar chapter
  took 535,000 tokens for 23 pages (three readers); a reader for 25 small
  crops took 58,000.
- **Give the second reader other cuts than the first,** and a folder that
  holds nothing but its images: the first reading's files lie in the work
  folder beside the first tiles.
- **A comparison of words does not see everything.** In the grammar chapter
  the stored copy had lost the length mark of *-:hus* and merged cells of a
  table, and every word in it was still a word of the page. Compare the
  breakdown lines piece by piece and the tables row by row as well.
- **A crop drawn where the OCR text matches can be the wrong place** when the
  stored form is short. The English stored with the row says which place is
  meant (`bluebook_right_place.py`).
- `work/` in the reports folder holds rendered crops and per-page files. It is
  not in git and can be rebuilt.
