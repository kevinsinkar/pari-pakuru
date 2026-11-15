# Prompt: What should become of the grammar engines? A fresh review, in stages

Paste everything below the line into a fresh session started at the root of
the `pari-pakuru` repository. It assumes the model can read files, run Python
and write files.

It is written for a session that has **not** worked on this project before.
That is deliberate: the sessions that built and patched the engines have a
stake in them, and three times they trusted a rule because it passed a test
made of the same faulty data. The prompt gives the facts that were learned
and holds back the earlier session's opinion until you have formed your own.

The review is built to be interrupted. If a session ends part-way, start a new
one with this same prompt: it reads `reports/engines_review/STATE.json` and
carries on from the first unfinished stage.

---

## Why this matters

Pari Pakuru is a study aid for Skiri (Skidi) Pawnee, a Caddoan language with
very few first-language speakers. Its data is a copy of two printed sources:
Parks & Pratt, *A Dictionary of Skiri Pawnee* (2008), and the community
textbook *Pari Pakuru'* (the "Blue Book", 1979). Learners study from it, and a
wrong form that is taught is hard to take back.

Beside the copied data, the project has a set of **engines**: programs that
work Pawnee forms out by rule (conjugated verbs, possessed nouns, sentences).
They were written in March 2026, before the copied data had been checked
against the printed pages. In November 2026 the data was checked in full, and
a good part of what the engines had been built on and tested against turned
out to be misread. Nobody has decided since what the engines are for.

Your job is to find out, from the evidence, what each engine is worth now,
and to put a decision in front of the project owner. You are not asked to
make the engines score higher. Read the next section before anything else:
it explains why that difference matters here.

## What went wrong before, and what it means for you

Three times a rule was built on a form an AI model had misread from a page
image, and each time the engine's own tests passed, because the tests held
the same misread form:

- The locative suffix *-hiriʔ* was read as *-biriʔ*, and the possession engine
  was built on it. No Skiri word contains a `b`.
- The possession engine stripped a final *-kiʔ* from nouns, a rule drawn from
  two words of the grammar chapter (*asaakiʔ*, *riicikiʔ*) that the chapter
  does not print. 'Dog' is *asaaki*. The rule was removed on 2026-11-14.
- `scripts/accent_rules.py` was worked out from the accent marks of a copy of
  Appendix 1 in which 152 of the 770 forms were misread, many of them in
  their accents. It has not been checked since.

The conjugation engine was reported at 90.3% of Appendix 1. Against the
appendix as Parks prints it, it gets 79.4%. The rules had been tuned on all
770 forms of the copy, so the 90.3% measured how well they fitted the
copy's errors along with its truths.

Two things follow, and the review is designed around them:

1. **A test proves nothing unless its expected forms are attested, and
   unless the rule was not fitted to them.** Before you trust any number,
   find out where the expected forms came from and whether the code was
   tuned against those same forms.
2. **Do not tune while you measure.** In the stages below you measure first
   and change nothing. If the owner later asks you to repair an engine, you
   will set aside forms the code has never been fitted to and report the
   score on those.

## What is settled, so you can rely on it

All of this was established between 2026-11-13 and 2026-11-14. The records
are in `reports/source_audit_2026-11/` (start with `findings.md`) and in the
project log.

| Source | State | Where |
|---|---|---|
| Dictionary entries (4,244) | Compared field by field with the PDF's text layer; 99.94% identical; the 37 differences left are each explained and none is a verb form or a phonetic form | `skiri_pawnee.db`, `Dictionary Data/skiri_to_english_respelled.json` |
| The five verb forms of each verb | 9,559 attested forms for 2,239 verbs, part of the entries above | table `paradigmatic_forms` |
| Appendix 1 (seven verbs, ten modes, eleven persons: 770 forms) | Read blind from the page images and corrected; 152 forms had been wrong | `extracted_data/appendix1_conjugations.json` |
| Appendices 2 and 3 | Corrected from blind readings; one cell of Appendix 2 (*tir*) is empty in print and stored as `tir` | `extracted_data/` |
| Chapter 3, the 24 sound changes | Corrected from a blind reading | `extracted_data/`, table `sound_change_rules` |
| Chapter 4, the grammatical overview | Two blind readings agree on every Skiri word; the stored chapter was corrected to them, breakdown lines and Table 17 included. The chapter's other tables are stored as an earlier extraction rebuilt them (open item 51) | `extracted_data/grammatical_overview.json` |
| Chapters 2 and 5 | Read for the first time on 2026-11-14, twice; forms, tables and a summary of each section | `extracted_data/sounds_and_alphabet.json`, `organization_of_the_dictionary.json` |
| Blue Book forms | Read from the scan, accents restored; 17 forms left that the scan cannot settle | table `blue_book_attestations` |
| English index | Rebuilt from the printed page on 2026-11-14 | tables `english_index`, `cross_references` |

Phonetic forms are stored in Parks's own symbols. They are copied, never
generated.

## What Parks says that bears on the engines

Chapters 2 and 5 had never been read when the engines were written. Read both
stored files in full; they are short. The statements that matter most here:

- On accent (p. 15): "Stress is not phonemic in Skiri and hence is not marked
  on words. (Phonetic forms in entries do, however, have accented syllables
  marked.)" He names tendencies (the first syllable, or the second when the
  first is short and the second long; the third or second from the end) and
  says that most patterns are variable in the end.
- On vowel length (p. 14): some prefixes and stems have a long vowel in some
  words and a short one in others (*raar-*/*rar-*, *-taakaa*/*-taka*,
  *asaa-*/*asa-*). "This alternation occurs frequently, but the difference in
  vowel length is not predictable."
- On the five verb forms (pp. 56-57): form 1 is a first person **agent** for
  active, descriptive and locative verbs and a first person **patient** for
  passive verbs; form 4 is the gerundial (subordinate absolutive) mode,
  "usually" perfective; form 5 is the intentive aspect. "Certain verb classes
  do not allow some of these forms and thus are lacking here."
- On verb classes (p. 56): the class rests on the verb's subordinate form.
- On citation (pp. 53-54): a preverb is printed after the stem and stands
  before it in a word; nouns are cited with their nominal suffix (*-uʔ*,
  *-hiriʔ*, *-kat*, *-ru*), which is absent in compounds and incorporation.
- On *kt* (p. 16): the dictionary writes *kt* after one speaker; all other
  twentieth-century Skiri speakers said *tt*.

Weigh the first two against any rule that predicts an accent or a vowel
length. Parks, who had the recordings, calls both unpredictable in part.

## The engines

Line counts and results as measured on 2026-11-14. Run each command yourself
in Stage 0; do not quote these.

| Engine | File | What it does | Its own check |
|---|---|---|---|
| Sound changes | `scripts/sound_changes.py` (1,884 lines) | Applies Parks's 24 rules at morpheme boundaries | `--test`: 11 of 11 |
| Verb template and conjugation | `scripts/morpheme_inventory.py` (2,629) | Builds a verb form from slots (mode, person, preverb, stem, aspect) | `--validate`: 611 of 770 forms of Appendix 1 exact, 137 within two letters, 22 further off |
| Accent rules | `scripts/accent_rules.py` (429) | Places the accent on a generated form. Only the conjugation engine calls it | none of its own |
| Form 2 prediction | `scripts/stem_extractor.py` (1,102) | Predicts dictionary form 2 from headword, class and preverb; wrote `lexical_entries.form2_confidence` | `--validate`: 1,915 of 2,197 verbs exact |
| Person and mode derivation | `scripts/person_forms.py` (348) | Derives an unlisted person or mode from an attested form by changing its left edge | `--validate-appendix`: 25 of 27 |
| Noun possession | `scripts/possession_engine.py` (1,811), `scripts/noun_possession.py` (1,466) | Possessed and locative forms of nouns | `--test`: 60 of 60 |
| Sentence templates | `scripts/sentence_templates.py` (1,616) | Ten sentence frames from Blue Book dialogues, filled with words | `test`: 34 of 34 |

Known faults, as far as they have been seen (open items 13, 24, 25, 26, 39, 40
and 42 in the project log give the detail):

- The possession engine offers an instrumental form ("with, using ...") for
  every noun through the web API, animals included; it removes `-kis` wherever
  it finds it, so *rakis* 'wood' becomes the stem *ra*; for stems ending in *r*
  the dictionary shows two outcomes with *-hiriʔ* and the engine picks one.
- Person derivation gives *ruhii* and *riihkiraawaʔ* where Appendix 1 prints
  *ruuhii* and *rihkiraawaʔ*. Both are vowel-length differences.
- Conjugation from scratch was measured once across the whole dictionary, in
  September 2026 before the corrections: 14.8% exact. The project's standing
  rule since then is that derived forms start from attested ones and that
  from-scratch conjugation is not taken up again without the owner's decision.
- The sentence templates carry Blue Book forms typed in before the scan was
  read; they lack the printed accents that `blue_book_attestations` now has.

Where the engines reach a person: only in the local Flask app (`web/app.py`:
the entry pages and `/api/possession/...`, `/sentence-builder` and its API).
The public site in `docs/` publishes nothing computed, and that is a rule,
not an accident. Some engine output is also stored in the database
(`form2_confidence`, and tables such as `noun_stems`, `possession_examples`,
`verb_paradigms`, `morpheme_inventory`, `verb_template_slots`): find out in
Stage 1 which stored values are copied from a source and which were computed.

The word-construction analysis of November 2026 (`scripts/morphology_v2/`,
outputs in `curriculum/roots_v2/`) is not one of the engines under review,
but look at how it works: it grades every claim by the evidence behind it
(tiers A to D), keeps test sets it never tunes on, and has its own code for
what happens where two pieces meet (`seams.py`). It may be the better
foundation for whatever is kept, or it may show that part of an engine is
already done better elsewhere.

## Ground rules of the project

These hold for everything you do. The fuller statement is in the Design
Principles of `pari_pakuru_project_scope.md` and in the rules section of
`prompts/skiri_word_construction_v2.md`.

- Never invent a Pawnee form. A form the code produces is "computed", is
  marked as such wherever it is shown, and is never written into a table or
  file that holds copied forms.
- Never generate a phonetic form. Show one only where Parks prints it.
- Where two sources disagree, show both. Do not pick.
- Same spelling does not mean same morpheme.
- Ceremonial vocabulary is kept out of examples and teaching material until
  the Pawnee community has reviewed it.
- A script that changes the database or a data file changes nothing by
  default, backs up before it applies, and appends to its report. After any
  change to the database run `python scripts/db_dump.py --write`.
- Update the project log and the README of each folder you touch in the same
  change. Commit and push only when the owner asks.
- The owner watches token usage. This review should need no sub-agents and
  no reading of page images: the sources are settled. If you come to think
  one is needed, say what it would cost in tokens and wait for an answer.

## The stages

Keep `reports/engines_review/STATE.json` (stage, status, what was written)
and a `progress.log`, and write a line at the start and end of each stage.

### Stage 0: read, and take the baseline

Read `README.md`, then "Status at a glance", "What's next" and "Open items"
in `pari_pakuru_project_scope.md`, then `scripts/README.md`. Rank 2 of
"What's next" carries a recommendation written by the session that made the
corrections. Treat it as one person's opinion and set it aside until Stage 3.

Back up the database. Run every check in the "Checks" tables of `README.md`
and record the results in `reports/engines_review/baseline.md`. Change
nothing. If a result differs from the README, say so and find out why before
going on.

### Stage 1: what each engine claims, and on what

For each engine write a short profile in `reports/engines_review/`:

- what it takes in and what it puts out, and who calls it;
- every rule in it, with where the rule comes from: a statement of Parks
  (chapter and page), a pattern in attested forms (how many), a fit made to
  pass a test, or data that has since been corrected. Be plain about rules
  whose origin you cannot find;
- its tests: for each expected form, is it attested (where?), or is it the
  engine's own earlier output written down as an expectation?
- which stored values in the database it produced.

This stage is reading and tracing. It is the one most likely to be skimped,
and the one the decision most depends on.

### Stage 2: measure, without tuning

Build test sets from attested forms only, and keep a record of how each was
made so it can be made again. The material:

- Appendix 1: 770 forms. The code was tuned on all seven verbs, so report
  the result verb by verb and mode by mode, and say that none of it is
  unseen.
- The dictionary's five forms: 9,559 forms for 2,239 verbs. The conjugation
  engine was not tuned on most of these, which makes them the nearest thing
  to an unseen test. Measure forms 1 to 5 separately and by verb class, and
  remember form 1 of a passive verb is a patient form.
- The breakdown lines of the grammar chapter: each is Parks's own analysis of
  a word into pieces, so it tests the sound changes directly.
- For possession: the dictionary's own possessed and locative forms (the ten
  words in *-hiriʔ* are a start) and the chapter's examples.
- For person derivation: the persons of Appendix 1 that it derives, against
  the printed ones.

For every engine report exact matches, near misses, and misses, and then sort
the misses by cause. Separate at least: vowel length, accent, glottal stop,
a wrong or missing rule, and a stem the engine could not find. Given what
Parks says, a miss in vowel length or accent may be a place where no rule
could be right. Say how much of each engine's error is of that kind.

Also measure what each engine is actually used for. An engine that is right
on 80% of forms nobody asks for and wrong on the ten forms a learner sees
first is not an 80% engine.

Write `reports/engines_review/measurements.md`. Change no engine.

### Stage 3: the decision paper, then stop

Write `reports/engines_review/decision.md` for the project owner, who is not
a linguist and wrote none of this code. Lead with what you recommend. For
each engine set out the choices that are really open, among them:

- keep it as a local tool, as it is, with its limits stated;
- repair it, saying what would be repaired, against which unseen forms it
  would be measured, and what result would count as good enough to keep;
- rebuild it on another foundation (attested forms only; the
  word-construction analysis);
- withdraw it: take it out of the app and move the code to `archived/`.

For each choice give the evidence from Stages 1 and 2, the work it would
take, and what a learner could be shown wrong if it is chosen. Say what you
would do with the stored values an engine computed.

Then read rank 2 of "What's next" and the phase entries for 3.1 and 3.2 in
the project log, and add a section: where your conclusions differ from the
earlier session's, and why. If you agree, say what in your measurements
supports it, not only that you agree.

**Stop here.** Tell the owner the paper is ready. Do not change an engine
before they answer.

### Stage 4: only what the owner chose

Carry out the decision. If an engine is repaired: split its attested forms
into a part you may fit rules to and a part you never look at until the end,
write the split down before you start, and report the result on the unseen
part. Do not add a rule to pass a single form. If an engine is withdrawn:
remove its routes and templates from the app, move the code, and remove or
mark the values it stored. Update the project log, the READMEs, and the
"Checks" tables.

## What this review cannot show

It can show how often an engine reproduces what Parks printed. It cannot show
that a form Parks did not print is one a speaker would say. Only a speaker
can. Say so in the decision paper, and keep the two questions apart: whether
an engine is good enough to help the owner study the grammar on their own
machine, and whether anything it produces could ever be shown to learners.
The second is for the Pawnee community, and the packet in
`community_review/` is how the project means to ask them.
