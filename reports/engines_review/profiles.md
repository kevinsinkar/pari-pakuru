# Engines review, Stage 1: what each engine claims, and on what

*Written 2026-11-14 from a full reading of the eight engine files (11,285
lines), their tests, their commit history and the tables they wrote. Nothing
was changed. The tracing can be run again:
`python scripts/engines_review/stage1_trace.py` writes
[data/stage1_trace.json](data/stage1_trace.json), which holds every form
named below with the place it was looked for.*

## In short

1. **Six more rules or words were built on a misread form**, beside the three
   the brief names. Each passes its own test because the test holds the same
   misreading. All six were corrected in the data tables in November; the
   engines were not touched.

   | In the engine | What it was built on | What the page has |
   |---|---|---|
   | Possession: "my X" is *kti ratiru X*, for every common noun; *kti* analysed as *ku* + *ti* | the OCR text of the Blue Book, *kti•ratiru paks-ktiku'* | *kú•ratir•u paks•kúku'* 'my hat' (Blue Book p. 35). OCR read the accented *ú* as *ti*. There is no *kti* |
   | Sentence builder: *ilan'*, a third word for "yes" | OCR text *Ilan', tiku•ratsaus.* | *Háu', tikú•ratsaus.* |
   | Sentence builder: *kirti* "where (destination), when", beside *kiru* "where" | OCR text *Kirti rira•awi•u …* | *Kirú rira•awi•u …* The same word, with its accent |
   | Sentence builder: *stiks*, a "first person imperative (let me …)" | OCR text *Stiks .atku!* | *Súks•atku!* 'You (1) listen!' |
   | Person derivation: *tuu-* becomes *ru-* with the preverb *uur-*; *tih-* becomes *riih-* | two cells of the old copy of Appendix 1: *ruhii*, *riihkiraawaʔ* | *ruuhii*, *rihkiraawaʔ*. These are exactly the two forms the check now fails |
   | Person derivation: *tii-* becomes *rii-* in a question, "as in the Blue Book's *Ka rii hitu'?*"; the same sentence is a test of the sentence builder | OCR text *Ka rii hitu '?* | *Ka rú hitu'?* 'Is this a feather?' OCR read the *ú* as *ii* |

   A seventh is stored, not coded: the table `kinship_paradigms` has *swat*
   'your niece, nephew' with the note "BB form uses s- agent prefix where
   Parks has a-". The Blue Book prints *awat*; the *s* was an OCR slip, and
   the note explains a form that does not exist.

2. **Most engine tests do not test against a printed form.** Counting every
   expected form in the engines' own tests:

   | Engine | Expected forms | Printed in a source as given | The same letters, printed marks missing | Engine's own output, or a fragment |
   |---|---|---|---|---|
   | Sound changes | 11 | 4 | 0 | 7 |
   | Person derivation | 27 | 27 (Appendix 1) | 0 | 0, but all seven verbs are the ones the rules were read from |
   | Possession | 60 | 35 | 2 | 23 (16 the engine's own output, 1 returns its input, 6 compare nothing) |
   | Sentence templates | 34 | 2 | 22 | 10 |
   | Conjugation, form 2 | 770 and 2,197 | all (Appendix 1, dictionary) | | 0, but the rules were fitted to these same forms |

3. **The accent rules rest on 85 accented forms; the page has 26.** Of the 85
   forms that carried an accent in the old copy of Appendix 1, 15 carry the
   same accent on the page. In live use only one branch of
   `accent_rules.py` can run at all, and the forms it was written for have no
   accent on the page.

4. **The "14.8% across the whole dictionary" was measured on 2026-03-09**,
   when the conjugation engine reached 35% of Appendix 1 or less. The engine was
   then tuned to 90.3% in eleven days and the dictionary was never measured
   again. Stage 2 measured it: the present engine gets 14.8% by its own count
   and 15.0% by this review's. The fitting moved Appendix 1 by 55 points or
   more and the dictionary by none.

5. **Stored engine output is presented as source in two places.** The app
   shows the possession engine's *kti ratiru …* phrases under a badge that
   reads "ATTESTED" for every common noun. And the word-building guide prints
   the conjugation engine's own table of prefixes under the words "These are
   Parks's own tables"; six of its 37 rows are not in Parks's tables.

6. **Three engines reach a person; four do not.** The possession engine and
   the sentence templates (with person derivation behind them) are in the
   app. The conjugation engine, the accent rules and the full sound-change
   pipeline are called by nothing a person uses. Form 2 prediction is not
   shown, but a score it produced is shown on every verb page.

## How to read "where it comes from"

| Mark | Meaning |
|---|---|
| **Parks** | A statement or table of Parks, with its place |
| **Blue Book** | A form or statement printed in the Blue Book |
| **pattern** | A regularity read off attested forms; the number of forms is given |
| **fit** | Written to make a particular test form come out; no statement behind it |
| **misread** | Built on a form that the corrections of November 2026 changed |
| **not found** | The code names a source and the source does not have it, or names none |

---

## 1. Sound changes: `scripts/sound_changes.py`

**Takes** a list of word-pieces (`ti`, `uur`, `hiir`). **Gives** one surface
form. It first applies the rules Parks limits to particular pieces, joins the
pieces, then applies the general rules to the joined word.

**Who calls it.** No page of the app calls it directly.

- The conjugation engine uses only the second half (`apply_unrestricted_rules`):
  it has its own code for the first half.
- The possession engine imports six single rules (5, 6, 7, 13, 20, 23).
- The version 1 root extraction (`root_extraction.py`, superseded) imports
  the rule functions.
- The word-construction analysis does **not** use it. Its own
  `morphology_v2/seams.py` says why: this engine "cannot tell a boundary
  cluster from a cluster inside a root, e.g. it turns iks- into ikc-".

So the full pipeline, restricted rules first, is used by nothing except its
own tests and its command line.

**Rules.** All 24 are Parks's, from chapter 3. What differs is how they are
coded:

| Rules | Coded how | Comes from |
|---|---|---|
| 1R, 2R, 3R, 8R, 10R, 11R, 12R | on the named pieces Parks lists | Parks, ch. 3 |
| 4R (the echo vowel of descriptive verbs, *pahaat* → *tipahaaʔat*) | not coded: "complex and verb-specific; handled separately" | |
| 9R (final *s* lost in certain nouns and suffixes) | only when the caller asks for it; the engine does not know which words | Parks, ch. 3 |
| 5, 6, 7 (vowels meeting) | on every pair of vowels anywhere in the joined word. Parks's conditions (before one or two consonants; not at the end of a word) are not coded | Parks, ch. 3, in part |
| 13 to 23 (consonants) | as replacements over the whole joined word, so they also fire inside a root | Parks, ch. 3, wider than he states |
| 24 (*c* said as [ts] or [č]) | nothing to code: it is about pronunciation, not spelling | |
| a hidden marker that shields the *s* of rule 3R from rule 17 | so that *hak* + *-his* gives *haks* and not *hakc* | fit |
| "Noun-safe" subset: rules 17, 18, 19 left out for nouns (`apply_nominal_sc`) | added 2026-03-20 after rule 17 turned a noun's *ks* into *kc* | fit; the comment calls the rules "verb-specific", Parks calls them unrestricted. The real fault is the row above |

**Tests** (`--test`, 11 of 11). The file calls them "examples from Parks
Ch. 3". Four expected forms are printed there: *pahaahaʔuk*, *tactaʔuut*,
*haks*, *kuhku*. The other seven are fragments or cut-down versions whose
expected value is what the engine gives: *aa*, *raaraahu*, *raaciis*, *uci*,
*ikca*, *ikta*, *tactak*. Three of the seven stand at a place where the
engine does **not** reach the form Parks prints:

| Parks prints | The test asks instead for |
|---|---|
| *ti-* + *raar-* + *raahur* → *tiraraahuʔ* | *raar* + *raahur* → *raaraahu* |
| *ti-* + *raar-* + *takasis* → *tiracakasis* | *raar* + *tiis* → *raaciis*. A comment says the full example gives *tiraacakasis* and that the printed form has a "vowel shortening not covered by the 24 listed rules" |
| *ta-* + *t-* + *cak* → *tactat* | … → *tactak* |

The catalogue in the same file holds 39 of Parks's examples with a printed
result. The test uses four of them. Stage 2 runs all 39, and the 93 worked
examples of chapter 4, which this engine has never been run against.

**Stored values.** Table `sound_change_rules` (24 rows) is the catalogue:
Parks's rules and his examples as corrected from the page, with the
project's own wording of each description. **Copied**, and identical to the
code today. One warning: run with `--db`, the script empties and rewrites
this table unless `--validate-only` is given.

---

## 2. Verb template and conjugation: `scripts/morpheme_inventory.py`

**Takes** a stem, a verb class, a mode, a person and number, an aspect, a
preverb. **Gives** one form and the list of pieces it joined.

**Who calls it.** Nothing in the app. Since September 2026 the sentence
builder uses person derivation instead. The possession engine was once meant
to call its assembler; the call never worked and was removed on 2026-11-13.
Only its own command line runs it.

**Rules.**

| What | Comes from |
|---|---|
| The modal prefixes *ta-/ti-*, *kaakaa-*, *rii-*, *i-/ri-*, *kuus…i-/kaas…i-*, *ra-*, *aa-/ii-*, *ra…ku-* | Parks, Table 8 |
| Third person negative *kaakii-* | fit: Table 8 prints *kaaki-*. The code lengthens it and then has four branches that shorten it again |
| Agent *t-*, *s-*; inclusive *acir-*, *a-* | Parks, Table 9 |
| Subordinate suffix *-a* (class 1), *-i* (class 2), none (class 4); intentive *-his* + *-ta* (+ *-rit*) | Parks, Table 17 |
| Class 3 subordinate suffix *-aha* | not found: Table 17 says "final syllable change" |
| Classes "u" and "wi" given the suffix *-a* | fit to 'to be good', the one descriptive verb with a preverb in Appendix 1. Table 17 has no such row; the table the engine itself wrote earlier has *-u* and *-wi* |
| Imperfective *-huʔ* | Parks, Table 17, without its length mark: he prints *-:huʔ*. The stored chapter had lost the mark until 2026-11-14 |
| Plural *raak-*, *iraak-* | fit: Table 10 prints *rak-* |
| Perfective, non-subordinate: nothing added | Table 17 prints "-Ø / -ʔ"; only the first is coded. No final *k* → *t*, which the dictionary's forms show throughout |
| The order of the slots | Parks, Tables 6 and 7, as the March extraction stored them. These are the two tables on which the blind readings of 2026-11-14 differ |
| `SUPPLETIVE_STEMS`: a block for six of the seven verbs, 47 values typed in, three of them stems with an accent typed in (*ucíʔaar*) | fit to Appendix 1 |
| `DESC_KU_MODE_OVERRIDES`: 25 prefix exceptions, all for 'to be sick' | fit to Appendix 1 |
| The assembly code: 258 conditions, of which 41 name a person, 27 a mode, 18 a preverb. 43 comments quote the Appendix 1 form the condition was written to produce | fit to Appendix 1 |
| "Parks' Rule 12" (glottal stop lost after a consonant, with lengthening), "Parks' Rule 24" (final glottal stop lost before a vowel), "Parks Ch 3.3.11" (*r* → *h* before *i*, *u*) | not found. Chapter 3 as stored has no such rules under these numbers: its rule 12R is about two evidential prefixes, its rule 24 about the pronunciation of *c*. The three came from an AI-assisted analysis of the mismatches on 2026-03-10 |
| Accents | see the next profile |

The commit history shows the fitting: 12.7% of Appendix 1 exact on 2026-03-08,
35.2% and then 50.8% on 03-10 ("52 patterns across 7 verbs"), 76.2% by 03-19,
90.3% on 03-20 with the accents. Every step was scored on all 770 forms.

**Tests.** `--validate` compares with Appendix 1 as corrected: attested, but
nothing in it is unseen. Where Parks prints two forms in one cell (13 cells)
only the first is compared. `--validate-dict` compares with the dictionary's
five forms; its one recorded run is the 14.8% of 2026-03-09.

**Stored values.**

- `morpheme_inventory` (37 rows) and `verb_template_slots` (27 rows) were
  written by `--import-db` from the engine's own constants, at an earlier
  state of the code. They are **computed** (the engine's arrangement), not a
  copy of a table. Labels such as `AGENT.1du_excl` are the engine's. Six rows
  are not in Parks's tables: *kaaka-* (he prints *kaakaa-*), *raak-*,
  *iraak-* twice (he prints *rak-*), and the suffixes *-u* and *-wi*.
  `morphology_v2/inventory.py` reads the table, and
  `curriculum/roots_v2/construction_guide.md` prints all 37 rows under the
  sentence "These are Parks's own tables (Grammatical Overview, Tables 7 to
  17), not a segmentation made here." The check that every form in the guide
  has a source passes because it accepts this table as a source.
- `verb_paradigms` (770 rows) is **copied**: Appendix 1, corrected. The entry
  page has a place for it, headed "Attested (Appendix 1)", but finds the
  table by a column that is filled for two of the seven verbs only, with
  *tuuhii* and *kiraawaʔ*, neither of which is a headword. So no entry page
  shows it.
- Nothing reads Appendix 2. `extracted_data/README.md` says the conjugation
  engine reads the cell of *tir* that is empty in print; it does not. The
  engine only counts the rows of that file in a report.

---

## 3. Accent rules: `scripts/accent_rules.py`

**Takes** a generated verb form with its mode and person. **Gives** the form
with accent marks.

**Who calls it.** The conjugation engine, and only for verbs without the
preverb *ir-*. For those, only one branch of the file can run: in the
potential mode, *c* + *i* + *ʔ* becomes *cí*. Rules A to D, which fill the
file, are skipped. The verb 'to come', which has all the printed accents, is
handled by a second copy of the same rules inside `morpheme_inventory.py`
(`_apply_ir_accents`).

**Rules.** The file says where they come from: "Rules derived from analysis
of 85 Appendix 1 accented forms."

| | In the old copy | On the page |
|---|---|---|
| Forms with an accent mark | 85 | 26 |
| 'to come' | 74 | 26 |
| 'to do it' | 7 | 0 |
| 'to be good' | 2 | 0 |
| 'to have it' | 2 | 0 |
| The same form, accent and all, in both | | 15 |

So 70 of the 85 forms the rules were fitted to are not as printed: **misread**.
The one branch that runs in live use was written for the seven 'to do it'
forms, none of which has an accent on the page.

The file opens: "The accent marks indicate HIGH PITCH in Skiri. Pitch is
phonemic — wrong accent = wrong word." Parks says the opposite (p. 15):
stress is not phonemic and is not marked on words; some patterns recur, and
most are variable in the end. What the 26 marks in the first verb of
Appendix 1 stand for, he does not say in the chapters that have been read.

**Tests.** `--validate` takes each printed form that has an accent, removes
it, and checks whether the rules put it back. It looks only at forms that
have an accent, so it cannot see an accent the rules add to a form that has
none.

**Stored values.** None.

---

## 4. Form 2 prediction: `scripts/stem_extractor.py`

**Takes** a headword, its verb class, its preverb and its grammatical class.
**Gives** a predicted form 2 (third person, indicative, perfective). It
predicts no other form.

**Who calls it.**

- The word-construction analysis (`morphology_v2/analysis.py`), as one of its
  evidence checks: does the prediction equal the form 2 Parks prints? There
  it is used to check, never to show a form.
- `--confidence`, which wrote `form2_confidence`.
- No page of the app calls the predictor.

**Rules.**

| What | Comes from |
|---|---|
| Prefix *ti-*; preverbs *ut-*, *uur-*; *ir-* appearing as *a-* in the third person | Parks, chs. 4 and 5 |
| Vowels meeting at the prefix (rules 5, 6, 7), final *r* lost (23), *r* → *t* after a hard consonant (21) | Parks, ch. 3. The code calls rule 21 "Rule 8R", calls its own *r* → *h* "Rule 12R" and its final *k* → *t* "Rule 3R"; those numbers are other rules in Parks |
| The table of what happens where a preverb meets a stem (*tuut* + *k* → *tutk*, *tuut* + *c* → *tuc*, *tuur* + *r* → *tur* …), several of which shorten a vowel | pattern: the code says "from empirical analysis of 2,211 attested forms" |
| Perfective endings (*k* → *t*, *hk* → *t*, *uuh* → *uʔ*, *wiir* → *wiʔ*, *ʔ* after a final vowel …) | pattern, same forms |
| Class 3 contractions; the echo vowel of descriptive verbs and when it is not used | pattern, same forms; the echo vowel is Parks's rule 4R |
| No final *ʔ* for class 4 stems in *-sa*; the *-wii* shortening for descriptive verbs | pattern on a few forms each |

"The same forms" is the point. The rules were worked out, in three passes on
2026-03-19 (62.0%, 83.5%, 86.6% exact), from the form 2 of every dictionary
verb, and `--validate` scores them on the form 2 of every dictionary verb.

**Tests.** `--validate`: 2,197 verbs. Expected forms are the dictionary's
own, attested and corrected. Nothing was held out, so the 87.2% is a measure
of fit, not of prediction. 35 verbs whose form 2 has a comma are left out.

**Stored values.** `lexical_entries.form2_confidence`, on 2,239 verb entries:
**computed**. It is not a property of the word. The formula is 50% how often
the predictor is right for verbs of the same class and preverb, 20% whether
class and preverb are given, 15% whether the headword is a plain single word,
15% how many verbs are in that group.

- 1,863 of the 2,239 stored values differ from what the code gives today
  (the largest by 0.55; 21 would change band). They were written in March
  and not made again after the corrections.
- The app shows it on every verb page and search card as "Prediction: High",
  "Med" or "Low" (2,187 are "High"). For 2,232 of the 2,239 the form the
  score is about is printed by Parks and shown on the same page under
  "Attested". The badge says nothing about the word and suggests that
  something on the page is predicted.
- `web/srs.py` uses it as the third key when it orders new study cards.

---

## 5. Person and mode derivation: `scripts/person_forms.py`

**Takes** the attested forms 1, 2, 3 and 5 of a verb. **Gives** twelve forms:
first, second and third person in the past, the present and the future, and
the three persons of the absolutive (question) mode. It changes only the left
edge of an attested form.

**Who calls it.** The sentence builder: `sentence_templates.resolve_verb_form`
behind `/api/assemble`, when the learner picks a dictionary verb and "who"
and "when".

**Rules.**

| What | Comes from |
|---|---|
| Second person: the agent *t* becomes *s*, with repairs where it meets *r*, *h*, *w*, *t* (six shapes) | pattern, read off the seven verbs of Appendix 1 |
| Absolutive, first and second person: initial *t* → *r* | pattern, Appendix 1; agrees with Parks's Table 8 (*ta-* against *ra-*) |
| Absolutive, third person: *ti* + consonant → *ra*; *tiʔ* → *raʔ*; *tu-* → *ru-* | pattern, Appendix 1 and one Blue Book word |
| *tuu-* → *ru-* when the preverb is *uur-* (*tuuhii* → *ruhii*) | misread: the page has *ruuhii* |
| *tih-* → *riih-* (*tihkiraawaʔ* → *riihkiraawaʔ*) | misread: the page has *rihkiraawaʔ* |
| *tii-* → *rii-*, citing the Blue Book's "Ka rii hitu'?" | misread: the book has *Ka rú hitu'?*. In Appendix 1 itself *tiiwuuʔ* 'they went' has the absolutive *raawuuʔ*, not *rii-* |
| Descriptive verbs without a preverb: *ti* + stem, first person *tiku* + stem, second person *ta* + stem | pattern on one verb, 'to be sick' |
| Present and future for "I" and "you": the first-person prefix is moved onto forms 3 and 5 | not found. Appendix 1 gives only perfective forms, so no first or second person present or future is printed there to learn from or check against |

**Tests.** `--validate-appendix`: 28 cells of Appendix 1, attested. All seven
verbs are the ones the rules were read from. 25 right, 2 wrong, 1 not
attempted. Accents are removed before comparing. The command reports failure
only if more than three forms are wrong, so today's two do not make it fail.

**Stored values.** None.

---

## 6. Noun possession: `scripts/possession_engine.py`, `scripts/noun_possession.py`

**Takes** a noun's headword and class. **Gives** "my / your / his" forms, a
locative and an instrumental.

**Who calls it.** The app, in two places:

- `/api/possession/<headword>`, behind the "Possession" box on every noun's
  page (1,706 noun rows).
- `extract_noun_stem`, for **every** entry page, nouns and verbs alike: the
  app uses it to decide which example sentences belong to an entry.

`noun_possession.py` is a one-time script that filled three tables; nothing
calls it.

**Rules, by the four "systems".**

| What | Comes from |
|---|---|
| Kinship: the three forms are looked up | Parks, Appendix 3, copied and corrected |
| Body parts: *ti* + *ri* + agent + noun stem + a verb of position | Blue Book p. 22: *Ti rit•páks•ku*, *Ti rit•kírik•ta*, two sentences; Parks ch. 4 for *ri-* |
| Which position verb goes with which body part: a table of 13, headed "Source: Blue Book Lesson 5 dialogues" | 2 of the 13 are in the Blue Book (head sits, eye hangs). The other 11, all "hangs", are **not found**; "hangs" is also the default for any other noun. The stems in the table are in Blue Book spelling (*tsusu*, *kskitsu*) and cannot match a dictionary stem |
| Which dependent nouns are body parts: a list of 24 stems | typed in; "arrow" is among them |
| Any other noun: *kti ratiru X*, *kti rasiru X*, *kti rau X*, with *kti* = *ku* + *ti* | **misread**, see "In short". The engine marks all three "attested", confidence "high", for every noun |
| Locative *-hiriʔ*, *-ru*, *-kat*; instrumental *-hiriʔ* "where it is semantically appropriate" | Parks, Table 4 and p. 30 |
| A noun is a tribe if its headword ends in *ii*, *ita* or *aasi* | not found. *piita* 'man' ends in *ita* |
| *-wiru* after *a* | pattern on two words, p. 30 |
| *-sukat* after *ki* or *ski* | pattern on two dictionary examples |
| How *-hiriʔ* attaches (h stays after a vowel, is lost after a consonant; *-haar* special) | pattern, measured 2026-11-13 on 42 dictionary words |
| No instrumental for an animate noun | Parks's "semantically appropriate", applied through the topic tags; the route does not pass the tags, so the filter never acts |
| Stem: drop *-uʔ*, *-kis*, *-kusuʔ* from the end | Parks names *-uʔ*, *-hiriʔ*, *-kat*, *-ru* as the suffixes a noun drops (p. 54). *-kis* and *-kusuʔ* are derivational; the code drops *-kis* wherever the letters stand |
| Its own small set of sound rules, with numbers 2R, 4R, 8R, 12R | not found under those numbers: "Rule 4R: i + u → u" and "Rule 8R: r → t after a hard consonant" are other rules in Parks |

**Tests** (`--test`, 60 of 60).

| Group | Tests | Expected form printed in a source | Not |
|---|---|---|---|
| Body parts | 10 | 2 (*Ti rit•páks•ku*, *Ti rit•kírik•ta*, without the printed accent) | 8 are the engine's own output. Three of the inputs (*tsusuuʔ*, *kararuuʔ*, *usuuʔ*) are not words of the dictionary: they were made so that the stem comes out in Blue Book spelling |
| Kinship | 16 | 16, Appendix 3 | They check that a lookup returns what the table holds |
| Any other noun | 7 | 0 | All seven begin with *kti*. *akaruʔ* 'house', used in three, is not a dictionary headword (Parks has *akaaruʔ*) |
| Locative | 11 | 9 (seven in chapter 4, two in dictionary examples) | *caahikskat* is the engine's output; one test returns its input. Six inputs are not headwords as given, and the three tribal tests tell the engine by hand that the noun is a tribe, which the app never does |
| Instrumental | 6 | none compared | They check only that a form, or nothing, comes back, and pass topic tags that the app never passes |
| *-hiriʔ* | 10 | 10 dictionary words | The rule was measured on 42 words; these are ten of the same 42. The test starts from Parks's stem, not from a headword as the app does |

**Stored values.**

| Table | Rows | What it is |
|---|---|---|
| `kinship_paradigms` | 14 | 11 **copied** from Appendix 3 (corrected). 3 typed from the Blue Book's OCR text: *tikiʔ*, *tsuwat*, and *swat* for printed *awat* |
| `noun_stems` | 49 | **Computed.** No row is linked to an entry. 20 of the 49 "headwords" are not in the dictionary (*tsusuuʔ*, *paauʔ* …) |
| `possession_examples` | 20 | **Computed**: the engine's output stored twice, as "expected" and "generated", all marked "exact", source "BB". It still holds the misread *asaas*, *atipaat*, *apaat* that were corrected everywhere else, and three *kti* phrases |
| `extracted_data/noun_possession_catalog.json` | | Computed by `noun_possession.py`; the README says nothing reads it |

The script that made the three tables is not in the repository: their columns
do not match what `noun_possession.py` creates. The dashboard counts their
rows and shows "20 of 20 exact".

---

## 7. Sentence templates: `scripts/sentence_templates.py`, `scripts/template_slot_fillers.py`

**Takes** a template (T1 to T10) and words for its slots. **Gives** a sentence,
an English line, a confidence and a breakdown.

**Who calls it.** The app: `/sentence-builder`, `/api/assemble`,
`/api/slot-options`. Each lesson page also lists its templates with their
example sentence.

**Rules.**

| What | Comes from |
|---|---|
| The ten frames and their word order | Blue Book dialogues: between 4 and 27 sentences each, by the file's own count |
| The example sentence of each template | Blue Book, typed from the OCR text. All ten have the letters of a printed sentence; none has its printed accents. One keeps an OCR artefact: *Suks•teka .rikut.* for *Suks•teká•rikut.* |
| 40 words offered for the slots, "every entry here has at least one Blue Book attestation" | 13 are as printed. 4 lack the printed accent or dot. 14 are a word inside a printed sentence. 9 are **not in the Blue Book** as given: six are dictionary spellings (*cikstit* for the book's *Tsikstit*, *ctuu*, *awiit*, *istuʔ*, *kskiitiʔiks*, *suhuks*) and three are the non-words *ilan'*, *kirti*, *stiks* |
| T2, "the stick is red": noun + *ti* + the dictionary stem of a descriptive verb | Blue Book *Rakis tí pahaat*. For this verb Parks prints form 2 as one word, *tipahaaʔat*. For other verbs the frame writes a bare stem, which Parks says never occurs as a word (p. 53) |
| A verb chosen from the dictionary is put in as Parks spells it, inside a sentence spelled as the Blue Book spells | fit: two spellings in one sentence |
| Confidence "HIGH" when the sentence is found in the Blue Book | The comparison ignores dots, spaces and capitals but not accents. Since the Blue Book forms carry their printed accents, a sentence the book prints is found only if it has no accent: 2 of the 27 Blue Book sentences in the engine's own test |

**Tests** (`test`, 34 of 34). They check that the frame puts the words it is
given in order. For the 27 that take a ready-made verb form, the "expected"
sentence is the input words in that order.

- 2 are as the Blue Book prints them.
- 22 have the right letters without the printed accents or dots.
- 3 are not in the book as given: *ka rii hitu'?* (the book has *Ka rú
  hitu'?*), *kaki', kaki karitki* (the engine adds an apostrophe to the
  first word), *kiwaku we tu'h•kuksas* (the apostrophe is OCR's reading of
  the accent in *túh•kuksas*).
- 7 test the person derivation. Their expected values are what the
  derivation gives; two of them are also attested dictionary forms.

**Stored values.** None of its own. It reads `function_words`, which has four
non-words from the same OCR slips, each marked as attested in the Blue Book:
*ilanʔ*, *kirti*, *stiks* and *kti* (glossed "your").

---

## What is stored: copied or computed

| Table or column | Rows | Copied from a source | Computed by an engine | Note |
|---|---|---|---|---|
| `verb_paradigms` | 770 | Appendix 1 | | corrected 2026-11-13 |
| `sound_change_rules` | 24 | chapter 3 | | descriptions are the project's wording |
| `kinship_paradigms` | 14 | 11 from Appendix 3 | | 3 rows from OCR text, one a non-form |
| `irregular_verb_roots` | 9 | Appendix 2 | | no engine reads it |
| `morpheme_inventory` | 37 | | conjugation engine's constants, March 2026 | 6 rows not in Parks's tables; printed in the word-building guide as Parks's |
| `verb_template_slots` | 27 | | conjugation engine | slot names and groups |
| `lexical_entries.form2_confidence` | 2,239 | | form 2 predictor | stale; shown on verb pages |
| `noun_stems` | 49 | | an earlier possession script | linked to no entry |
| `possession_examples` | 20 | | possession engine output | holds three misread kin forms |
| `function_words` | 418 | | not an engine's (phase 3.1.6) | 4 non-words from OCR slips; outside this review, noted because the sentence builder reads it |

## Found on the way, outside the engines

The grammar notes of the lesson pages on the **public site** are raw OCR
text and still carry the same slips: *Stiks•at.* for *Súks•at.* (lessons 5
and 12), *Stiks•kika'.* for *Súks•kika'.* (lesson 11), and in the `lessons`
table *kti•ratiru paks-ktiku'* (lesson 7). The corrections of 2026-11-13
replaced a lesson line only where it was identical to a corrected form;
running text was left. Stage 2 counts these. It is not an engine matter, but
it is in front of learners now, which nothing an engine produces is.
