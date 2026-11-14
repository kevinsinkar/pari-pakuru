# scripts/morphology_v2/

The code behind [curriculum/roots_v2/](../../curriculum/roots_v2/): the
word-construction analysis of 2026-11-12. It opens the database read-only and
writes only into `curriculum/`.

The method is described in
[curriculum/roots_v2/METHOD.md](../../curriculum/roots_v2/METHOD.md). The
instruction it was built from is
[prompts/skiri_word_construction_v2.md](../../prompts/skiri_word_construction_v2.md).

## Commands

```bash
python scripts/morphology_v2/run.py --all            # data, guides, validation report
python scripts/morphology_v2/check_forms.py          # every Pawnee form in the guides resolves to a source
python scripts/morphology_v2/check_determinism.py    # two runs, byte-identical outputs
python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"
python scripts/morphology_v2/gold_build.py --verify  # gold files match their recorded hashes
python scripts/morphology_v2/apply_data_fixes.py     # list proposed data fixes (dry run)
```

## Modules, in the order the pipeline uses them

| Module | What it does |
|---|---|
| `common.py` | Paths, read-only database connection, text normalisation, deterministic JSON output |
| `lexemes.py` | Loads the dictionary rows and groups true duplicate rows into lexemes |
| `etymology.py` | Re-parses Parks's printed etymology and aligns his literal translation with the pieces |
| `bluebook.py` | Finds Blue Book words written with seams and matches them to dictionary forms |
| `seams.py` | The seam engine: the surface forms the named sound rules allow for a list of pieces |
| `analysis.py` | Decides which pieces are grammatical, groups each shape's meanings into senses, runs the evidence channels |
| `proposals.py` | Cautious proposals for words Parks leaves unanalysed |
| `tiers.py` | The tier rules, as one pure function |
| `inventory.py` | Builds the root and affix inventory, the decision records and the frequency measures |
| `ordering.py` | Derives the learning order and tests how sensitive it is to the weights |
| `guide.py` | Writes the three learner documents |
| `validate.py`, `report.py` | Score the gold sets and write the validation report, the change list and the proposed data fixes |
| `run.py` | The entry point |

## Checks and one-off tools

| File | What it does |
|---|---|
| `test_morphology_v2.py` | 34 unit tests: tier rules, duplicate handling, etymology parsing, seam engine, coverage |
| `check_forms.py` | Verifies every italic form, bracketed IPA and respelling in the learner documents |
| `check_determinism.py` | Runs the pipeline twice and compares hashes |
| `gold_sample.py`, `gold_build.py` | Draw the test sample (seeded) and build and lock the gold sets |
| `apply_data_fixes.py` | Lists the proposed data fixes; applies only page-number corrections, and only with `--apply`. The 43 it listed on 2026-11-12 were applied by `scripts/fix_data_2026_11.py`; it now lists none |

## Data files that are edited by hand

| File | What it holds |
|---|---|
| `decisions_manual.json` | The 27 decisions made by hand, each with its source. To change a decision, edit this file and run again; never hard-code one |
| `adversarial_review.json` | The written resolutions of the independent review, the list of changes from version 1, the open questions and the gaps. `report.py` copies them into the validation report |

## Who reads its output

`scripts/build_weekly_flashcards.py` takes the word-building notes on the weekly
flashcards from `evidence.jsonl` and `roots.json`. If you change how a piece's
meaning is recorded, rebuild the flashcards and read the difference.

## Rules this code keeps

- A tier is never set by hand; it follows from the evidence record.
- No Pawnee form is typed into a document; each is looked up.
- IPA is never generated.
- The same spelling is not assumed to be the same morpheme.
- The gold sets are locked; a change to them is visible in `gold/HASHES.json`.
  `--verify` only says that the files are as they were when they were hashed, not that they
  still follow their sources. When Appendix 1, the grammar chapter or the Blue Book forms are
  corrected, run `gold_build.py` and then `gold_build.py --hash` before `run.py --all`. (This
  was missed after the corrections of 2026-11-13 and made good on 2026-11-14.)
- The held-back half of the test set has now been scored several times. Any
  further tuning needs fresh entries.
