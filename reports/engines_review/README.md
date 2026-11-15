# reports/engines_review/

The review of the grammar engines, 2026-11-14: what is each engine worth now
that the data it was built on has been corrected, and what should become of
it? Run from [../../prompts/engines_review.md](../../prompts/engines_review.md).

**Stages 0 to 3 changed nothing** and ended in a paper for the project owner.
The owner answered it the same day with the recommended choice for all eight
decisions, and **Stage 4 carried them out**. Nothing is committed.

## Read in this order

| File | What it is |
|---|---|
| [stage4.md](stage4.md) | **Start here.** What was done for each of the eight decisions, where the paper turned out wrong, what was removed from the database, and what is still open |
| [person_forms_repair.md](person_forms_repair.md) | The one engine that was repaired: the split written down first, what the open half showed, and the one opening of the sealed half (97.3% against a bar of 97%) |
| [decision.md](decision.md) | The paper the owner answered: the recommendation, the open choices for each engine, the eight decisions |
| [measurements.md](measurements.md) | Stage 2: what each engine got right on attested forms, seen and unseen apart, with the misses sorted by cause |
| [profiles.md](profiles.md) | Stage 1: what each engine took in and gave out, where each of its rules came from, what its own tests really tested, and which stored values it computed |
| [baseline.md](baseline.md) | Stage 0: every check of the top-level README run before the review began |
| `stage4_database_report.txt` | What `scripts/remove_engine_output.py` removed from the database, run by run, with the backup made before each |
| `STATE.json`, `progress.log` | How far the review has got, stage by stage and decision by decision |

## The short version

| Engine | Measured (Stage 2) | Decided and done (Stage 4) |
|---|---|---|
| Conjugation | 79.4% of Appendix 1, which it was fitted to; **15.0%** of the dictionary's 9,559 verb forms, which it was not. Called by nothing | withdrawn to `archived/scripts/`; its two tables dropped |
| Accent rules | marked 81 cells of Appendix 1; the page marks 26 | withdrawn with it |
| Sound changes | 8 of Parks's 39 examples to his own rules; 15 of 74 of his worked examples | kept as a reference to the rules; its self-test replaced by that measure |
| Form 2 prediction | 87.2% on the forms its rules were read from; no unseen test exists | kept as a checker; the badge and the stored score removed |
| Person derivation | rules read from correct forms: 97% of 1,516 unseen verbs. Three rules built on misread forms: 6% of 465 | repaired narrowly; on a sealed half of 1,059 verbs, 97.3% of the 816 forms it gives |
| Noun possession | "my X" began with the OCR slip *kti* for 1,671 of 1,706 nouns; locatives right for 44% of 675 printed forms | replaced by a lookup of printed forms; 734 nouns have something printed |
| Sentence templates | three of its words did not exist; it recognised none of the 385 Blue Book sentences printed with an accent | rebuilt on printed rows; a sentence says whether the book prints it |

And beside the engines: the lessons' running text and titles were brought in
step with the audit's reading of the scan (214 places, 12 titles).

## data/

Everything behind the figures, written by
[../../scripts/engines_review/](../../scripts/engines_review/). Run
`python scripts/engines_review/run_all.py` to make it all again; a second run
gives the same bytes.

**The per-form records (the `.jsonl` files directly in `data/`) are not in
git.** They list, form by form, what each engine computed beside what is
printed: some twenty thousand computed forms, most of them wrong. The
project's rule is that a computed form is never stored where it could pass
for a copied one, and the repository is public. They are made again in a
minute. The test sets, the summaries and the Stage 1 trace are in git.

| File | What it holds |
|---|---|
| `stage1_trace.json` | Every expected form of every engine test, with where it was looked for and found; the stored values; the copy of Appendix 1 the rules were fitted to against the corrected one |
| `testsets/` | The ten test sets, one form per line, and `MANIFEST.json` with source, count and hash of each |
| `conjugation_appendix1.jsonl`, `conjugation_dictionary.jsonl`, `conjugation_summary.json` | The conjugation engine, cell by cell and form by form |
| `sound_changes.jsonl`, `sound_changes_summary.json` | The sound-change engine and the seam engine on Parks's examples |
| `form2.jsonl`, `form2_summary.json` | The form 2 predictor, verb by verb |
| `person_forms_*.jsonl`, `person_forms_summary.json` | Person derivation: Appendix 1, the test against form 4, descriptive verbs, forms found in examples |
| `possession_*.jsonl`, `possession_summary.json` | The possession engine: stems, combining forms, suffix words, the 675 printed case forms, every answer of the API, the first flashcard nouns |
| `use_*.jsonl`, `use_summary.json` | The sentence templates; examples hidden on entry pages; OCR slips left in the lessons |
| `person_forms_split.json`, `person_forms_plan.json`, `person_forms_sealed_result.json` | Stage 4, the repair of person derivation: the split of the 2,124 verbs with what was already known of the sealed half; the two configurations and the rule for which ships, fixed before the opening; the one opening |

## Things to know

- **The Stage 2 figures are about the engines as they were**: the files of
  commit `814e8cc`, with the database of that hour (its SHA-256 and the name
  of its backup are in `STATE.json`). Four of those files are now in
  `archived/` and five are changed, so the measurement scripts refuse to run
  and write nothing. `python scripts/engines_review/run_all.py --check` still
  says whether the test sets match their sources.
- "Seen" and "unseen" are used throughout. A result on forms an engine was
  fitted to is not evidence that the engine is right.
- The paper's count of OCR slips in the lessons (65) was an undercount; the
  true figure is in `stage4.md`.
- What Stage 4 found and left for the owner is at the end of `stage4.md`.
