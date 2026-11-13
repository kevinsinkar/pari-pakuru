# curriculum/roots_v2/ — how Skiri words are built (current)

The word-construction analysis of 2026-11-12: which roots and affixes Skiri
words are made of, what each means, how often each is used, and a learning
order built from that. Every claim carries a confidence tier that follows
mechanically from the evidence for it.

Everything here is written by `scripts/morphology_v2/` and can be regenerated
with one command (`python scripts/morphology_v2/run.py --all`). The exceptions
are `PLAN.md`, `baseline.md`, `METHOD.md` and the `gold/` and `blind/` folders,
which were written once.

## Start here

| If you want to | Read |
|---|---|
| Learn | [learning_path.md](learning_path.md): 15 lessons covering the first 120 building blocks, with practice and answers; the remaining 459 as an ordered table |
| See how words are put together | [construction_guide.md](construction_guide.md): 14 construction patterns and the sound rules at the seams, each with counts and attested examples |
| Review it as a speaker or linguist | [review_queue.md](review_queue.md): everything that needs a human decision, most important first |
| Judge how far to trust it | [validation_report.md](validation_report.md): opens with the headline numbers, the top 30 roots and top 20 affixes, the ten main open questions and the known gaps |
| Understand or repeat the method | [METHOD.md](METHOD.md) |

## Headline

549 roots and 30 affixes let a learner take apart 1,791 of the dictionary's
4,337 words completely (41%). The first 100 building blocks cover 480 words
(11%), and 1,378 words (32%) contain at least one of them.

Of the 4,337 words: 1,086 analyses are tier A, 1,320 tier B, 1,569 tier C, and
361 words carry no claim. Only tiers A and B appear in the learner documents.

These figures are from the run of 2026-11-13, after the data fixes of that day.
The first run (2026-11-12) gave 548 roots and 1,788 words.

| Tier | Meaning |
|---|---|
| **A** | Parks's analysis reproduces the headword exactly and a second source (the verb's forms, or a Blue Book seam) confirms it |
| **B** | Reproduces exactly and every piece recurs with the same meaning elsewhere; or reproduces nearly and a second source confirms it |
| **C** | Parks's analysis alone, or the sources conflict |
| **D** | A proposal not in Parks |

## Limits

- The test set is small: 18 of 18 tier A analyses were right on the held-back
  half, which still leaves a 95% interval reaching down to 82%.
- The test shows faithfulness to Parks's printed page, not that Parks is right.
- The page transcribers and the independent reviewers were AI models.
- Affixes that Parks rarely labels are the weakest part.
- 176 words are flagged for community review by a keyword match; none is in the lessons.

## The files

| File | Contents |
|---|---|
| `learning_path.md`, `construction_guide.md`, `review_queue.md` | The three documents for people (see above) |
| `validation_report.md`, `validation_details.json` | Scores against the gold sets, the independent re-derivation, the adversarial review |
| `changelog_vs_v1.md` | What changed from version 1 (`../roots/`) and why |
| `METHOD.md` | The method, the evidence channels, the tier rules, how to reproduce |
| `PLAN.md` | What was planned and fixed before any analysis was run |
| `baseline.md` | The state of the existing tools before the work started |
| `evidence.jsonl` | One record per word: Parks's etymology, the pieces, each evidence channel, the tier and the reason for it. The source of everything else |
| `roots.json`, `affixes.json` | The inventory: each morpheme with meaning, tier, evidence and several frequency measures |
| `decisions.json` | Every judgement call as data: duplicate rows, homonym splits, variant candidates, affix defaults |
| `coverage.json` | The learning order and how much of the dictionary each step unlocks |
| `stats.json` | Totals |
| `proposed_data_fixes.json` | Errors the analysis finds in the database or JSON. The 43 found on 2026-11-12 were applied on 2026-11-13 (`reports/fix_data_2026-11-13_report.txt`); the list is now empty |
| `determinism.json` | Proof that two runs give byte-identical outputs |
| `gold/` | The test sets, locked by hash: Parks's own worked examples, 120 entries transcribed from the page images, Blue Book seams |
| `blind/` | An independent re-derivation of the top 86 shapes, made without sight of the pipeline's output |

## Reading the learner documents

*Italics* are a Pawnee form exactly as stored. `[Brackets]` are Parks's IPA,
shown only where he prints it for that word. `Code font` is a learner
respelling, an entry id or a file name. `check_forms.py` verifies all three
against the sources.
