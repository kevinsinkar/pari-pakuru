# scripts/source_audit/

The source-fidelity audit of November 2026: does every stored value that claims
to copy a printed page match the page? Written from
[../../prompts/source_fidelity_audit.md](../../prompts/source_fidelity_audit.md).
Results: [../../reports/source_audit_2026-11/](../../reports/source_audit_2026-11/).

Every script here reads the database read-only, except `apply_fixes.py`, which
changes nothing without `--apply` and a file of approved fix ids.

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
| 2 | `compare_core.py`, `s2e_compare.py` | Every stored field looked for in its printed entry, and every printed stretch looked for among the stored fields. Noise rules and conventions are named in `s2e_compare.py` |
| 2 | `recall_test.py` | Plants 510 known errors in a copy and counts how many the comparison reports |
| 2, 6 | `show.py` | Lists differences by field and kind |
| 3 | `crops.py`, `grade.py` | Cuts differences out of the page onto sheets for a blind reading; grades them from the readings |
| 4 | `appendix_tiles.py` | Tiles of the pages that have no text layer |
| 4 | `appendix1_compare.py`, `chapters_compare.py`, `abbrev_compare.py`, `alphabet_check.py` | Appendix 1, chapters 3 and 4 and the abbreviation list against their second readings; the check that every stored Skiri form uses only Skiri letters |
| 5 | `bluebook_check.py`, `bluebook_crops.py` | Blue Book forms against the scan |
| 6 | `e2s_compare.py` | The English-to-Skiri section against its text layer; `--source db` for the database tables, `--source json` for the current JSON |
| 7 | `build_report.py`, `apply_fixes.py` | The list of proposed fixes and the review page; the script that applies approved fixes |

## To run it again

The comparisons with the text layer take seconds and need no AI:

```bash
python scripts/source_audit/decode_pages.py       # once; a minute
python scripts/source_audit/s2e_segment.py
python scripts/source_audit/s2e_compare.py        # the live database against the page
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
  disagree, not as a first pass.
- `work/` in the reports folder holds rendered crops and per-page files. It is
  not in git and can be rebuilt.
