# scripts/engines_review/

The review of the grammar engines, November 2026: what is each engine worth
now that the data it was built on has been corrected? Written from
[../../prompts/engines_review.md](../../prompts/engines_review.md). The
results, and the decision paper, are in
[../../reports/engines_review/](../../reports/engines_review/).

**These scripts change no engine, no data file and not the database.** They
write only into `reports/engines_review/data/`. The database is opened
read-only; where the app's own code is called, it is given a temporary copy.

**The Stage 1 and 2 scripts measured the engines as they stood in commit
`814e8cc`, and now refuse to run.** Stage 4 carried out the owner's decisions:
four engine files were withdrawn to `archived/scripts/` and five were
repaired or rebuilt. Run on today's files the scripts would measure other
code and write over the record, so each stops with an explanation
(`common.require_reviewed_state`) and writes nothing.

```bash
python scripts/engines_review/run_all.py --check            # are the test sets still what the manifest says? works today
python scripts/engines_review/person_forms_repair.py --open # the repaired person derivation on the open half of its test
python scripts/engines_review/run_all.py                    # Stages 1 and 2 again: only where the reviewed files are in place
```

If `--check` reports a difference, a source was changed after the review:
the test sets no longer describe it.

The per-form records the measurements wrote (`data/*.jsonl`) are ignored by
git on purpose: they hold the engines' computed forms.

### Making the Stage 2 figures again

They can be made again only on the code and the data they were made on:

1. Check out commit `814e8cc` into a separate folder
   (`git worktree add ../pari-pakuru-review 814e8cc`).
2. Copy this folder into it as it was at the end of Stage 3: take it from the
   commit that first contains it and remove `person_forms_repair.py`, the
   guard at the end of `common.py`, and the three lines that call the guard
   in each script.
3. Put the database of the review beside it: the backup named in
   `reports/engines_review/STATE.json` (`database_backup`; its SHA-256 is
   there too). It is not in git. `DB/dump/` of commit `814e8cc` is close but
   older: it lacks the rebuild of the English index made earlier that day.
4. `python scripts/engines_review/run_all.py`. A second run gives the same
   bytes.

## The scripts

| Script | Stage | What it does |
|---|---|---|
| `common.py` | | Paths, the read-only connection, and the one comparison used everywhere: a produced form against the printed one, sorted into exact, accent, vowel length, glottal stop, other letters |
| `stage1_trace.py` | 1 | For every expected form in an engine's own test: is it printed in a source, or is it the engine's own output? Which stored values an engine computed, and whether they are still what the code gives. The copy of Appendix 1 the rules were fitted to (from git) against the corrected one |
| `build_test_sets.py` | 2 | Writes the ten test sets from attested forms, with a manifest of counts and hashes. `--verify` builds them again and compares |
| `measure_conjugation.py` | 2 | The conjugation engine on Appendix 1 (seen) and on the dictionary's 9,559 verb forms (unseen); the accents it marks against the page |
| `measure_sound_changes.py` | 2 | The sound-change engine on Parks's own examples in chapters 3 and 4, beside the seam engine of the word-construction analysis |
| `measure_form2.py` | 2 | The form 2 predictor on every dictionary verb; what the stored confidence score is worth |
| `measure_person_forms.py` | 2 | Person derivation on Appendix 1 (seen); its question form for "he/she" against the dictionary's form 4 (unseen); the "I" form it makes for descriptive verbs |
| `measure_possession.py` | 2 | The possession engine against Parks's etymologies and printed combining forms, his 680 printed locative and instrumental examples (unseen), Appendix 3, the Blue Book, and everything `/api/possession` serves |
| `measure_use.py` | 2 | The sentence templates; what the entry pages and the sentence builder actually show; OCR slips left in the lessons' running text |
| `run_all.py` | | `--check` verifies the test sets; without it, runs the above in order where the reviewed files are in place |
| `person_forms_repair.py` | 4 | The repair of person derivation: `--write-split` (once, before the engine was touched), `--open` and `--explore` (the open half only), `--sealed` (once; it refuses a second run). Record: `reports/engines_review/person_forms_repair.md` |

## The test sets

All in `reports/engines_review/data/testsets/`, listed with source and hash in
`MANIFEST.json`. "Seen" means the engine's rules were fitted to those very
forms, so a good result on them proves little.

| Set | Items | From | Seen? |
|---|---|---|---|
| `appendix1` | 770 | Appendix 1 as corrected | seen by conjugation, accents, person rules |
| `dictionary_forms` | 9,559 | the five verb forms of the entries | unseen by conjugation and person rules; form 2 seen by the form 2 predictor |
| `chapter3_examples` | 39 | Parks's examples to his 24 sound changes | 4 are the sound-change engine's own tests |
| `chapter4_examples` | 93 | Parks's worked examples (the locked gold file of the word-construction analysis) | unseen |
| `noun_suffix_words` | 57 | headwords whose etymology ends in + *hiriʔ*, + *kat*, + *ru* | the 40 in *-hiriʔ* seen by the possession engine |
| `noun_etymologies` | 1,350 | nouns with an etymology in pieces | unseen |
| `noun_case_examples` | 680 | locative and instrumental forms printed as examples under nouns | unseen |
| `kinship_appendix3` | 11 | Appendix 3 | looked up by the possession engine |
| `blue_book_possession` | 37 | Blue Book lessons 5 and 7, from the scan | the engine was built on the OCR text of these |
| `blue_book_sentences` | 454 | every Blue Book dialogue line, phrase and grammar example | the templates were built on the OCR text of these |

## Things to know

- **Eight of the 93 chapter 4 examples are mis-paired in the gold file** and
  are left out for every engine alike (`measure_sound_changes.py` names
  them): in six the word listed is another word of the same example
  (*aruusaʔ* 'horse' beside the pieces of a verb), in two a line with two
  analyses had the pieces of both joined. Eleven more carry the gold file's
  own flags or a piece that is not a plain form. 74 are used.
- **"The way the app asks"** means: the headword exactly as stored (two
  spellings and a comma, or a trailing dash, included), the class of the
  first entry found with that spelling, no topic tags. That is what
  `/api/possession` does.
- **If an engine is repaired or a rule added**, do not fit it to these sets
  and then quote the result on them. Split the printed forms first, write the
  split down with what you already know of the part you will not look at, fix
  beforehand what will be measured and what result means what, and open that
  part once. `person_forms_repair.py` and its three files in `data/` are the
  pattern. Its sealed half is spent: a further change to person derivation
  needs forms that have not been looked at, and the dictionary has no more
  verbs with a form 4.
- The four of Parks's chapter 3 examples that were also in the sound-change
  file's old self-test are written into `build_test_sets.py`, since that
  self-test no longer exists.
