# Plan: Skiri word construction, version 2

Written 2026-11-12, after the baseline checks and before any segmentation
heuristic was run. `METHOD.md` (written at the end) describes what was actually
done; this file records what was planned and what was locked in advance.

## Goal

1. Find which roots and affixes exist, what each means, and which shapes belong
   to one morpheme.
2. Measure which are used most, in several independent ways.
3. Describe the recurring construction patterns.
4. Turn that into a learning guide ordered by usefulness, with every Pawnee
   form traceable to a source record.

Version 1 (`curriculum/roots/`) is treated as a hypothesis and is not modified.
All v2 output goes to `curriculum/roots_v2/`; all v2 code is in
`scripts/morphology_v2/`. The database is opened read-only.

## What v1 left open, and how v2 addresses it

| v1 weakness | v2 response |
|---|---|
| Parks's etymology was used both to segment and to check the segmentation | Independent channels E3 (paradigms) and E5 (Blue Book seams), and a gold set read from the page images |
| Per-piece glosses came from a stored AI parse that mis-aligns them (*as+hur+uʔ* 'foot place + NOM' stored as *as* = "foot place") | The printed etymology is re-parsed; glosses are aligned by how each form is labelled across the whole dictionary |
| 21 variant merges, most on vowel length with no rule | Merges need a named rule and matching meaning; length-only pairs become review candidates |
| Homonym splits hard-coded for five roots | Senses are clustered from Parks's own glosses for every form; every split and merge is a data record |
| Short roots can match by chance | Counted only through tier A/B analyses; a chance baseline is reported for each |
| Rows counted, not lexemes | Duplicate rows are resolved first, each decision recorded |
| Lesson order set by hand | Order derived from coverage gain under a prerequisite graph, with a sensitivity check |

## Evidence channels

| Channel | Source | What it can confirm |
|---|---|---|
| E1 | Parks's printed etymology, re-parsed from `raw_etymology` | The analysis itself |
| E2 | `sound_changes.py` round trip from the pieces to the headword | That the analysis is self-consistent; exact or partial |
| E3 | Paradigm forms 1–5 | E3a: the stem sits in the forms where the class and preverb predict. E3b: a compound inflects at its right edge like its final root does on its own |
| E4 | Other lexemes' analyses | The piece recurs with a compatible meaning in unrelated words |
| E5 | Blue Book seams (`•`) | A second author puts a boundary at the same place |
| E6 | Grammatical Overview, appendices, abbreviations, Parks's own labels | An affix is a documented affix |
| E7 | South Band / Arikara cognates | Weak corroboration, recorded only |

## Tier rules (to be implemented as code and unit-tested)

- **A**: E1 analysis, exact E2, confirmed by E3 or E5, nothing contradicting.
- **B**: nothing contradicting, and either exact E2 with every piece recurring
  with the same meaning elsewhere (E4), or partial E2 confirmed by E3 or E5.
- **C**: E1 alone; any analysis not in Parks that fails B; conflicting channels.
- **D**: hypothesis only.

Two interpretations fixed in advance:

1. **Simplex entries.** Parks prints no etymology for basic roots such as *at*
   'go'. When such a headword is itself cited as a piece, with a compatible
   gloss, in other entries' printed etymologies, that citation counts as Parks's
   analysis of it as a single morpheme (E1 by citation). Its tier then follows
   the same rules.
2. **Entries with no etymology and no citation** make no segmentation claim. A
   segmentation proposed for them from E3/E4/E5 is "analysis not in Parks" and
   reaches tier B only if E3 and E5 independently agree.

## Gold sets (locked)

| Set | Content | Built by |
|---|---|---|
| G1 | 93 worked examples from Parks's Grammatical Overview with morpheme-by-morpheme analyses; 770 Appendix 1 cells | `gold_build.py` |
| G2 | 120 dictionary entries transcribed from the page images by annotators who saw neither the database nor any v2 code; 60 development, 60 held out | `gold_sample.py`, then annotation |
| G3 | 77 Blue Book seamed words matched with certainty to a Parks form | `gold_build.py` via `bluebook.py` |

**G2 sampling.** Seed 20261112. Pool: 4,216 entries whose page was confirmed
from the PDF text layer (Blue-Book-only entries have no Parks page and are
excluded). Five class groups (N, VT, VI, VD, other) by four v1 strata (high 7,
medium 6, low 4, no etymology 3) give 100 entries; 20 more are drawn from
entries of one or two syllables. Half of each cell is held out. The held-out
half is not scored or read until Phase 5.

**Order of events.** The sample ids, G1 and G3 were hashed before any
segmentation code existed. The annotation ran while the etymology parser was
being written; the annotators had no access to it. The annotation hashes were
recorded as soon as the last batch arrived, before the pipeline was first run
against G2. As a check on the annotation itself, all 120 transcribed headwords
and all 103 transcribed etymology strings were compared with the PDF text
layer, a second independent reading, and all agree.

**G3 caveat.** E5 and G3 draw on the same seams. When segmentations are scored
against G3, tiers are recomputed with E5 switched off, so that nothing is
scored against evidence it was promoted on.

### Hashes (SHA-256, first 16 hex digits; full values in `gold/HASHES.json`)

```
9f0abd8b565ff1a9  g1_appendix1.json
00cfa0d01291dfde  g1_go_examples.json
19ae20a23c60ac54  g2_sample.json
913cd7fa05c2c7f0  g2_annotations.json
61f703b35cbb2c20  g2_raw/batch_1.json
bb1abfe3116524c5  g2_raw/batch_2.json
f9f13cd5ba44629a  g2_raw/batch_3.json
65062fd2a895c5ec  g2_raw/batch_4.json
84c756bd38a66967  g2_raw/batch_5.json
0ec45706e5fbc8db  g2_raw/batch_6.json
a32188d917851baa  g3_bb_seams.json
```

Verify at any time with `python scripts/morphology_v2/gold_build.py --verify`.

## Phases

0. Baseline (done: `baseline.md`).
1. Gold sets (done: above).
2. Per-lexeme evidence table: `evidence.jsonl`.
3. Morpheme inventory: `roots.json`, `affixes.json`, `decisions.json`.
4. Frequency, productivity, coverage: `coverage.json`.
5. Verification: `validation_report.md`, `changelog_vs_v1.md`.
6. Learner material: `construction_guide.md`, `learning_path.md`,
   `review_queue.md`.

## Stop conditions

- A baseline test fails (none did).
- A fix needs a change to the database or source JSON: write
  `proposed_data_fixes.json`, do not apply.
- E1 and E3 disagree for more than about 10% of verbs that have both, after the
  E3 extraction itself has been ruled out as the cause.
