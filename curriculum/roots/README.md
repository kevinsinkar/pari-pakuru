# curriculum/roots/ — version 1 (superseded)

**Do not learn from, or build on, the files in this folder.** They are the
first attempt at a word-building guide, made on 2026-11-07 and 2026-11-08. The
current guide is [../roots_v2/](../roots_v2/).

## Why it was superseded

Version 2 tested version 1 and found:

- **Meanings on the wrong piece.** Version 1 took each piece's meaning from a
  stored parse of Parks's etymologies. That parse often attaches a meaning to
  the wrong piece (`as+hur+uʔ` 'foot place + NOM' is stored with *as* meaning
  "foot place").
- **Counts too high.** A root was counted in every headword whose stored parse
  contained its shape. Checked properly, 'go' falls from 156 words to 120 and
  'liquid' from 114 to 60.
- **Shapes merged that may be different roots.** Version 1 merged shapes that
  differ only in vowel length; its single root 'wood' (80 words) is three
  shapes.
- **Compound stems read as their first part.** The stem that means 'run' was
  read as 'foot'.
- **Nothing held back for testing.**

The full list is in [../roots_v2/changelog_vs_v1.md](../roots_v2/changelog_vs_v1.md).

## Why it is still here

| File | Still used by |
|---|---|
| `segmentation_log.jsonl` | `scripts/morphology_v2/gold_sample.py` (to stratify the test sample). The weekly flashcards read it until 2026-11-13; they now read version 2 |
| `roots_ranked.json` | `scripts/morphology_v2/report.py` (to write the list of changes) |
| the rest | nothing. Kept so that the list of changes can be checked against what version 1 actually said |

One thing was changed after the files were set aside. They quote ten words
from Parks's grammar chapter as the stored chapter then had them, and the
second blind reading of 2026-11-14 showed those ten to be misreadings
(*asaakiʔ* for *asaaki*, *taruuraariit* for *taruuraarit*, *tikíkat* for
*tikikat*). The quotations were corrected in the four guide and lesson files,
in `review_log.md` and in the two spec files they are made from
(`scripts/root_curriculum_spec_guide.py`, `root_curriculum_spec_units_b.py`),
41 places in all. Nothing else was touched.

## What the files are

| File | Contents |
|---|---|
| `roots_ranked.json`, `affixes_ranked.json` | Version 1's roots (1,320 senses) and affixes, ranked by count |
| `segmentation_log.jsonl` | One record per dictionary entry: pieces, method, confidence (1,085 high, 1,575 medium, 1,683 low) |
| `variant_merges.json` | The 21 merges of shapes differing in vowel length. Version 2 undoes them |
| `stats.json` | Totals |
| `construction_guide.md`, `lesson_plans.md` | The version 1 guide and its 7 units |
| `lesson_plans_pronounced.md`, `lesson_plans_pronounced_modern.md` | The same lessons with respelling, and with learner spelling |
| `review_log.md`, `review_log_auto.md` | What version 1 flagged for review |

Made by `scripts/root_extraction.py` and then
`scripts/build_root_curriculum.py` (with the `root_curriculum_spec*.py` files).
