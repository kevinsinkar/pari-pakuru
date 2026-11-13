# Prompt: Rigorous analysis of Skiri word construction, and a learning guide built on it

Paste everything below the line into a fresh session started at the root of the
`pari-pakuru` repository. It assumes the model can read files (including PDFs),
run Python, and write files.

---

## Why this matters

You are working on Pari Pakuru, a revitalization project for Skiri (Skidi)
Pawnee, a Caddoan language with very few remaining first-language speakers. The
project has turned Douglas Parks's *Dictionary of Skiri Pawnee* and the
community teaching text *Pari Pakuru* (the "Blue Book") into a SQLite database
and tooling. Learners will study from what you produce, and in a language with
this few speakers a mistake that gets taught is hard to take back. Accuracy is
the goal and coverage comes second: a smaller guide in which every claim holds
up is worth more than a complete one with errors in it.

## The task

Using only the evidence in this repository, work out how Skiri words are built:

1. which roots and affixes exist, what each means, and which surface shapes
   belong to the same morpheme;
2. which roots and affixes are used most, measured several independent ways;
3. the recurring construction patterns: how pieces combine and what happens at
   the seams.

Then turn that into a learning guide that teaches the most useful building
blocks first, in an order a learner can follow, with every Pawnee form traceable
to its source.

A first version already exists in `curriculum/roots/`, built on 2026-11-07 by
`scripts/root_extraction.py` and `scripts/build_root_curriculum.py`. Treat it as
a hypothesis to test, not as ground truth. Put your version in
`curriculum/roots_v2/` and leave v1 untouched so the two can be compared.

"Bulletproof" means the following four properties. The work isn't done until
all four hold.

- **Traceable.** Every Pawnee form in every output is looked up from a source
  record: an entry_id plus Parks page, an Appendix cell, a Grammatical Overview
  page, or a Blue Book lesson and page. No form is typed by hand in prose or
  code.
- **Triangulated.** Every root and affix claim records which independent lines
  of evidence support it, and its confidence tier follows mechanically from that
  record.
- **Validated on data you did not tune on.** Lock a gold set before writing
  heuristics, then report accuracy against it per confidence tier.
- **Reproducible.** One command regenerates every output from the DB and
  `extracted_data/`, and two runs produce byte-identical files.

## Ground rules

These come from the project owner and from earlier mistakes on this project.
Each rule gives its reason.

1. **Don't modify `skiri_pawnee.db`, `Dictionary Data/*.json`,
   `extracted_data/`, anything in `curriculum/roots/`, the frozen
   `curriculum/flashcard_sets.json`, or the static site in `docs/`.** The DB
   backs a live site and frozen flashcard sets, so changes there go through
   review. If you find data errors, write them with evidence to
   `curriculum/roots_v2/proposed_data_fixes.json`, plus a fix script that
   defaults to `--dry-run`.
2. **Never fabricate a Pawnee form.** If a lesson needs a word that isn't
   attested, choose an attested one instead. If you must show a constructed
   form, put it in a section labelled "constructed — unverified" and keep it out
   of flashcards and drills. **Never generate IPA.** Parks's `phonetic_form`
   records reduction vowels and pitch accent that spelling can't predict, so
   show IPA only where it is attested for that exact word.
3. **Show conflicts instead of picking a side.** When Parks and the Blue Book
   disagree, or Parks disagrees with itself across the dictionary, Grammatical
   Overview and appendices, show both forms with their sources and mark the
   conflict. Only a speaker or a linguist can settle it, so it goes in the
   review queue.
4. **Same spelling doesn't mean same morpheme.** Never merge entries or roots
   just because they share a shape. A merge needs agreement in meaning,
   grammatical class and paradigm behaviour. Examples: *hiksukac* has separate
   VD and VP entries with different paradigms, and *hiir* means both 'grass'
   and, with *uur-*, 'good'. Record every merge or split as a decision with
   evidence. Store these decisions as data rather than hard-coding them in a
   function, so each one can be reversed.
5. **Preserve the IPA and provenance.** Every learner-facing word shows its
   Parks headword, `phonetic_form` and page number. The learner spellings from
   `scripts/display_utils.py` appear alongside those, never instead of them.
6. **Sacred and ceremonial vocabulary** (bundles, ceremonies, sacred names and
   similar) is flagged `needs_community_review`. Keep it in the analysis, list
   it separately, and leave it out of early lessons. Whether it gets published
   is the Pawnee community's decision, not a technical one.
7. **Don't retry from-scratch conjugation.** `morpheme_inventory.conjugate` is
   only 14.8% exact across the dictionary, and that path has been tried. For
   inflected forms, use attested paradigm forms, Appendix 1, or
   `scripts/person_forms.py`, which swaps prefixes on attested forms and matches
   Appendix 1 27/27. Label any derived form as derived.

**Environment.** Windows 11, bash shell, Python at `.venv/Scripts/python`. The
console uses cp1252, so:

- print Pawnee text with
  `sys.stdout.buffer.write(s.encode('utf-8', errors='replace'))`;
- keep `→` out of log output;
- open every file with `encoding='utf-8'`.

Scripts take argparse flags with sensible defaults.

## What you have to work with

Start by reading `pari_pakuru_project_scope.md`. It covers the data model, the
five paradigm forms, the grammatical classes and the phonetic notation.

### Database (`skiri_pawnee.db`)

The DB holds 4,343 lexical entries. 93 of them come only from the Blue Book
(`source='blue_book'`).

- **`lexical_entries`**: headword, normalized_form, phonetic_form,
  simplified_pronunciation, grammatical_class, verb_class, stem_preverb and
  page_number. 4,334 entries have a phonetic_form. In the IPA, hyphens mark
  syllable breaks, not morpheme boundaries, and `•…•` brackets a bound verb
  stem.
- **`etymology`**: `raw_etymology` (e.g. `<kaa+at, go inside>`),
  `literal_translation` and `constituent_elements` (pieces as JSON). 3,327
  entries have constituent elements and 1,016 have no etymology at all. The
  `morpheme_type` labels on the pieces are unreliable: *kic* is typed both
  preverb and root, and 2,401 pieces have no type. Classify pieces by gloss and
  grammar instead.
- **`paradigmatic_forms`**: up to five inflected forms for 2,243 verbs:
  1. 1sg indicative perfective;
  2. 3sg indicative perfective;
  3. 3sg indicative imperfective;
  4. 3sg absolutive subordinate perfective;
  5. 3sg indicative perfective intentive.
- **`examples`**: 2,637 example sentences, about 3,700 tokens, 88 of them from
  the Blue Book.
- **`blue_book_attestations`**: 1,026 rows, 160 with full sentences. The 404
  rows with `match_type='prefix'` are known to be unreliable (e.g. BB *kisu'*
  'bone' is linked to *kisu* 'be slender'). Don't count them as evidence unless
  you re-verify each one.
- **Other lexical tables**: `glosses`, `cognates` (mostly South Band and
  Arikara), `semantic_tags`, `english_index`, `function_words` (418 rows).
- **Grammar tables**:
  - `verb_paradigms`: Appendix 1, 7 verbs, 770 cells;
  - `irregular_verb_roots`: Appendix 2;
  - `kinship_paradigms`: Appendix 3;
  - `morpheme_abbreviations`: 164 rows;
  - `morpheme_inventory` and `verb_template_slots`: the slot template;
  - `sound_change_rules`: 24 rules.

**Duplicates.** 63 headword + class groups have more than one row (132 rows in
total), and 9 of those groups also share an identical etymology. Some are real
polysemy and some are parser duplicates, such as page 2 / page 71 pairs.

- Count lexemes, not rows.
- Decide each group by comparing class, etymology and paradigm forms.
- Record each decision and report the totals.

### Grammar sources (`extracted_data/`)

- `grammatical_overview.json`: Parks's Grammatical Overview, including worked
  examples with morpheme-by-morpheme analyses;
- `appendix1_conjugations.json`, `appendix2_irregular_roots.json` and
  `appendix3_kinship.json`;
- `abbreviations.json`, `noun_possession_catalog.json` and `lessons.json`.

### Source PDFs, for checking by eye

- `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/page_NNN.pdf`: the
  dictionary, 181 pages;
- `Dictionary Data/Dictionary PDF Split/`: sound changes, grammar and
  appendices;
- `pari pakuru/Blue Book - Pari Pakuru - split/`: the Blue Book.

Before relying on page numbers, check on a few known entries how a DB
`page_number` maps to a split-file number.

### Blue Book text (`pari pakuru/Blue_Book_Pari_Pakuru.txt`)

The Blue Book marks morpheme seams with `•`, as in *tat•kikat* and *Tuks•at*,
and has about 760 such seamed tokens. These seams are a segmentation by a
different author than Parks, which makes them your best independent check on
Parks's analyses.

### Reusable code (audit before you rely on it)

- `scripts/sound_changes.py`: Parks's 24 rules as ordered transformations
  (`--test`, `--apply "ti + uur + hiir"`).
- `scripts/stem_extractor.py`: handles stem, class and preverb, and predicts
  form 2 (`--validate`).
- `scripts/person_forms.py`: derives person and mode forms from attested forms
  (`--validate-appendix`).
- `scripts/display_utils.py`: `display_headword()`, `modernize_form()`,
  `respell_form()`, `gram_class_label()`.
- `scripts/root_extraction.py`: the v1 segmenter (normalisation, alternant
  generation, piece location, rule tracing).

### What v1 produced, and where it is weak

Read `curriculum/roots/stats.json` and `review_log.md` before you start.

- **Scope.** 1,320 root senses and 127 affixes, ranked only by how many
  headwords each builds.
- **Confidence.** 1,085 entries were segmented with high confidence, 1,575
  medium and 1,683 low.
  - 1,016 entries had no etymology and were never segmented.
  - 647 could not be reproduced from Parks's analysis.
  - 610 matched only after ignoring vowel length, ʔ and h.
- **Circular validation.** v1 used Parks's etymology both to produce each
  segmentation and to check it. Paradigm forms, Blue Book seams and cognates
  were barely used as independent checks.
- **Unsupported variant merges.** v1 made 21 variant merges, most of them on
  vowel length with no rule behind them (*paks/paaks*, *kirik/kiriik*,
  *rak/raak*), plus r~h (*haak/raak*), also without a rule.
- **Homonyms.** `homonym_sense()` hard-codes splits for a handful of roots, and
  no one searched systematically for other homonyms.
- **Short roots.** *a*, *at*, *as*, *ka*, *ri* and *ku* are the riskiest
  because they turn up by chance inside unrelated words.
- **Parks's root count was never checked.** Parks says (GO p.31) that there are
  about a hundred basic verb roots. v1's 1,320 root senses mix nouns,
  descriptive stems and verb roots, so the claim was never tested.
- **Lesson order** was set by hand.

## Method

Work in phases. Write each phase's output to disk before starting the next, so
the run can resume and every step can be inspected.

### Phase 0: Orient and baseline

1. Read the scope doc and v1's `review_log.md`, `construction_guide.md` and
   `stats.json`, and skim `lesson_plans.md`.
2. Run the existing checks and record the results in
   `curriculum/roots_v2/baseline.md`:
   - `sound_changes.py --test`
   - `person_forms.py --validate-appendix`
   - `stem_extractor.py --validate`
   - `build_root_curriculum.py --check`

   If any of them fails, stop and report before you build on these tools.
3. Write a short `curriculum/roots_v2/PLAN.md` covering your plan, the evidence
   channels, how you will draw the gold set, and the tier rules.

### Phase 1: Lock a gold set before writing any heuristics

Build `gold/` from sources that don't depend on the heuristics you are about to
tune. Fix it before Phase 2: use seeded sampling, save the ids, and record the
file hashes in PLAN.md.

- **G1, Parks's own analyses.** Every Grammatical Overview worked example that
  has a morpheme-by-morpheme breakdown, plus the Appendix 1 paradigms (for the
  affix and mode inventory).
- **G2, a hand-checked sample** of about 120 entries.
  - Stratify the sample by grammatical class, by v1 confidence, and by whether
    the entry has an etymology.
  - Include about 20 entries of one or two syllables, where chance matches are
    most likely.
  - For each entry, read the dictionary page image yourself and record the
    correct segmentation, the glosses, and any extraction errors. If the page
    doesn't settle the segmentation, record "undetermined" instead of guessing.
- **G3, Blue Book seams.** Blue Book tokens with `•` seams that can be matched
  to a dictionary entry with certainty. Don't use `prefix` links for this.

Hold back half of G2 and don't look at how you score on it until Phase 5.

### Phase 2: A per-lexeme evidence table

After resolving duplicates, write one record per lexeme to `evidence.jsonl`.
Each record lists the candidate segmentations and, for each candidate, which
evidence channels support or contradict it.

| Channel | What it checks | Notes |
|---|---|---|
| E1 Parks etymology | `constituent_elements` / `raw_etymology` | Main source for most entries. Ignore `morpheme_type`. |
| E2 Sound-change round trip | Running the pieces through `sound_changes.py` reproduces the headword exactly. | Record every rule applied. A match that ignores length/ʔ/h is *partial*, never exact. |
| E3 Paradigm consistency | The proposed stem appears in forms 1–5 once the known mode/person prefixes, aspect suffixes and sound changes are accounted for. | Independent of E1, so disagreement here is a strong signal. |
| E4 Recurrence | The same form with a compatible meaning builds other, unrelated lexemes, and swapping the piece changes the meaning predictably. | Counts only through other lexemes' E1/E3-supported analyses, never raw substring hits. |
| E5 Blue Book | A BB `•` seam falls at the same place and the BB gloss agrees. | Different author: the strongest independent check. |
| E6 Grammar | The piece appears in GO tables, Appendices 1–3 or `morpheme_abbreviations`. | Mainly for affixes. |
| E7 Cognates | A South Band or Arikara cognate shows the same root. | Weak corroboration. Never the only support. |

For the 1,016 entries with no etymology, try E3, E4 and E5 to propose a
segmentation and mark it "analysis not in Parks". Such an analysis can reach
tier B only if E3 and E5 independently agree. Otherwise it stays at tier C or
below, which keeps it out of learner material.

Tiers follow mechanically from the record:

- **A**: the E1 analysis is reproduced exactly by E2 and confirmed by an
  independent source (E3 or E5), and nothing contradicts it.
- **B**: nothing contradicts the analysis, and either:
  - the E1 analysis is reproduced exactly by E2 and each piece recurs with the
    same meaning elsewhere (E4), or
  - the E1 analysis is reproduced only partially by E2 and is confirmed by E3
    or E5.
- **C**: E1 alone, any analysis not in Parks that doesn't meet B, or channels
  that conflict.
- **D**: hypothesis only. These appear in analysis files only, never in learner
  material.

Implement the tier rules as code and unit-test them. Never assign a tier by
hand.

### Phase 3: The morpheme inventory

Turn the segmentations into `roots.json`, `affixes.json` and `decisions.json`.

- **Identity is form plus meaning.** Cluster each shape's glosses into senses:
  normalise variants such as "go / to go / going", but keep 'grass' and 'good'
  apart. Then search systematically for homonyms: a shape is a homonym
  candidate if its glosses fall into unrelated clusters or its host words split
  by grammatical class. Every split and merge goes into `decisions.json` with
  its evidence, and the pipeline reads its decisions from that file.
- **Allomorphy.** Merge two shapes into one morpheme only when both conditions
  hold:
  - A named rule derives one shape from the other in that environment. The rule
    is one of Parks's 24 or a documented regularity with its own attestation
    count, such as w>p after an obstruent.
  - The meanings agree.

  Record pairs that differ only in vowel length (*paks/paaks*) and r~h pairs as
  *candidate variants*. Show their counts separately and combined, and send
  them to the review queue instead of merging them silently.
- **Short morphemes** (two segments or fewer) are counted only through tier A
  or B analyses. Report a chance baseline for each: how often the string occurs
  inside headwords where no analysis places it.
- **Classification.** Assign each morpheme to one class using its glosses and
  the grammar, not `morpheme_type`. For inflectional affixes, include the slot
  number from `verb_template_slots`. The classes are:
  - noun root;
  - verb root;
  - descriptive stem;
  - locative or preverb;
  - derivational affix;
  - inflectional affix.

  Compare your count of verb roots with Parks's "about a hundred" and explain
  any gap.

### Phase 4: Frequency and usefulness

Compute these measures separately before combining any of them.

- **Type frequency**: distinct lexemes (not rows) built by the morpheme,
  reported for tier A, tiers A+B and tiers A+B+C.
- **Productivity**: how many distinct partner morphemes it combines with, and
  what share of its formations occur only once.
- **Token frequency**: occurrences in `examples` and in Blue Book sentences.
  The corpus is small (about 4k tokens), so treat this as a secondary signal
  and report confidence intervals.
- **Teaching salience**: whether the morpheme appears in the Blue Book lessons,
  and in which lesson first.
- **Phonological transparency**: how often its formations need a sound change
  at the seam, and which changes. Transparent pieces are easier to teach early.
- **Coverage curves**, the headline metric. Put the morphemes in teaching
  order. For each point in that order, compute the share of each of the
  following whose every piece has already been taught:
  - dictionary lexemes;
  - Blue Book lesson vocabulary;
  - example-sentence tokens.

  These curves support statements like "these 40 roots and 15 affixes let you
  take apart X% of the dictionary". Compute them from tier A and B analyses
  only.

### Phase 5: Verification

- **Gold accuracy.** Score the segmentations against G1, G2 (now including the
  held-back half) and G3, and report precision per tier. If tier A precision on
  the held-back half of G2 is below about 95%, the tier rules are too loose:
  tighten the rules and rerun rather than fixing individual items.
- **Blind re-derivation.** Take the top 60 roots and top 30 affixes. Have a
  reviewer who hasn't seen your segmentations re-derive each one's meaning,
  shapes and five example words from the raw source records. Use a separate
  subagent if you can spawn one, or otherwise a separate pass of your own that
  reads only raw sources. Then compare the results, settle every disagreement on
  the evidence, and log the outcome.
- **Adversarial pass.** For each of the top 100 morphemes, try to break the
  claim. Look for:
  - a homonym that was folded in;
  - a false variant merge;
  - chance substring hits;
  - a gloss that fits only half the host words;
  - a counterexample to the stated seam behaviour.

  Log what you tried and what you found.
- **Sanity checks.** Rerun the Appendix 1 and `sound_changes.py --test` suites.
  Check that every entry_id cited in any output exists and that its form matches
  the DB.
- **Diff against v1.** In `changelog_vs_v1.md`, list every morpheme that was
  added, removed, split or merged, and every morpheme whose rank moved by more
  than 10 places or whose frequency changed by more than 25%, each with the
  reason.
- **Determinism.** Run the pipeline twice and confirm that the output hashes
  match.

### Phase 6: The learning guide

Build all learner-facing material from tier A and B data only.

#### `construction_guide.md`: how words are built

Organise the guide around construction recipes rather than as a list of
morphemes. Candidate recipes include:

- noun + *-uʔ*;
- the diminutive *-kis*;
- noun + noun compounds;
- body-part incorporation;
- locative/preverb + verb root (*kaa* + *at* 'go inside');
- portative and comitative;
- causative *-rik* / *-raʔuk*;
- 'become' *-aar* / *-itik*;
- the mode + person "introducer";
- aspect suffixes, and subordination by verb class.

For each recipe, give:

- the formula, and the class or condition under which it applies;
- what happens at the seam, with rule ids;
- at least three attested examples, each with headword, IPA, gloss,
  segmentation, entry_id and page, plus the Blue Book form where one is linked;
- the exceptions and counterexamples you found;
- any Parks vs Blue Book conflicts;
- the recipe's tier and the number of lexemes it accounts for.

#### `learning_path.md`: sequenced units

Derive the lesson order from the data and explain how you got it.

- **Prerequisites.** Build a prerequisite graph: a word comes after all of its
  pieces, and a recipe comes after all the morphemes it uses.
- **Ordering.** Within those constraints, order greedily by the coverage each
  morpheme adds, weighted by Blue Book salience and phonological transparency.
  State the weights.
- **Sensitivity check.** Shift the weights by ±25% and report how stable the
  top 50 stays, as a rank correlation. Keep only the conclusions that survive.
- **Lesson contents.** Each lesson introduces:
  - its new morphemes;
  - 5–12 attested words built only from material taught so far;
  - one or two recipes;
  - decoding practice: taking apart attested words;
  - building practice, only where the target word is attested, so the
    learner's answer can be checked against a real word.
- **Coverage.** Each lesson ends with the cumulative coverage figure.
- **Spelling.** Show every word the way the static site's four-way spelling
  bridge does: Blue Book spelling, Parks/learner spelling, simplified
  pronunciation and IPA (attested only), side by side with the Parks headword
  and page.

#### `review_queue.md`

List everything that needs a speaker or a linguist, grouped by type:

- variant candidates;
- Blue Book vs Parks conflicts;
- analyses not in Parks;
- homonym decisions;
- vocabulary that needs community review.

For each item, state the question whose answer would settle it.

## Deliverables in `curriculum/roots_v2/`

- **Plans and method**: `PLAN.md`, `baseline.md`, and `METHOD.md` (how to
  reproduce, every command, the tier rules in plain language).
- **Gold set**: `gold/`, containing G1, G2 with its held-back half marked, G3,
  and their hashes.
- **Data**: `evidence.jsonl`, `roots.json`, `affixes.json`, `decisions.json`,
  `coverage.json`.
- **Validation**: `validation_report.md`, with precision per tier per gold set,
  blind re-derivation results, the adversarial log and the determinism hashes.
- **Changes**: `changelog_vs_v1.md`, and `proposed_data_fixes.json` if you
  found any data errors.
- **Learner material**: `construction_guide.md`, `learning_path.md`,
  `review_queue.md`.
- **Code** in `scripts/morphology_v2/`:
  - a single entry point, e.g. `python scripts/morphology_v2/run.py`;
  - tests in `scripts/morphology_v2/test_*.py` covering tier assignment,
    duplicate resolution, variant merging and the coverage computation.

## Definition of done

- [ ] A script confirms that every Pawnee form in every Markdown output
      resolves to a source record, and it fails on any form that doesn't.
- [ ] Tier A precision on the held-back half of G2 is at least 95%, or you
      report the actual number and explain why 95% can't be reached.
- [ ] Learner-facing material contains nothing below tier B and no generated
      IPA, and no `needs_community_review` vocabulary appears in Units 1–3.
- [ ] Every merge and split is recorded in `decisions.json` with its evidence.
- [ ] Two runs produce identical output hashes.
- [ ] `git status` / `git diff` show that the DB, source JSON, v1 files,
      flashcard sets and `docs/` are unchanged.
- [ ] All existing test suites still pass.

## When to stop and ask

- A baseline test fails.
- A fix would require changing the DB or source JSON. Write it up in the
  proposal file and don't apply it.
- Parks's etymologies (E1) and the paradigm forms (E3) disagree for more than
  about 10% of the verbs that have both, after you've ruled out your own E3
  extraction as the cause. That would undermine the whole approach, and the
  project owner should hear about it before you continue.

## Final report

End with a short report in chat, and copy it into `validation_report.md`:

1. **Headline coverage**: "N roots + M affixes → X% of lexemes fully decodable
   at tier A/B".
2. **Top 30 roots and top 20 affixes** in a table with these columns: form(s),
   meaning, class, type frequency, tier, evidence channels, and first Blue Book
   lesson.
3. **Validation**: precision per tier for each gold set.
4. **Changes from v1**: the five most important, each with its reason.
5. **Open questions**: the ten most important questions for a speaker or
   linguist.
6. **Gaps**: anything you couldn't do, and why.
