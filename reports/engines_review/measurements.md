# Engines review, Stage 2: what each engine gets right, measured without tuning

*Measured 2026-11-14. No engine was changed. Every number here comes from
`python scripts/engines_review/run_all.py`, which writes the per-form records
into [data/](data/); a second run gives the same bytes. The test sets and how
each was made are in `data/testsets/MANIFEST.json` and in
[scripts/engines_review/README.md](../../scripts/engines_review/README.md).*

## How to read the tables

- **Seen** forms are forms the engine's rules were fitted to. A good result on
  them shows that the fitting worked, not that the rules are right.
  **Unseen** forms were never used to write or adjust the engine.
- A produced form is compared with the printed one letter for letter. Where
  Parks prints two forms in one place, the nearer one counts.
- A miss is put in one of four groups:

  | Group | Meaning |
  |---|---|
  | accent | the letters are right; an accent mark is added, missing or misplaced |
  | vowel length | the letters are right; a vowel is long where the page has it short, or the reverse |
  | glottal stop | the letters are right; a *ʔ* is added or missing |
  | other letters | a consonant or vowel is wrong, missing or added: a wrong rule, a missing rule, or a stem the engine could not find. "Within two" means at most two letters off |

  The first two are the ones Parks calls unpredictable in part (pp. 14-15).
  They are an upper bound on "no rule could be right": some differences in
  vowel length do follow a rule the engine lacks.

## The results in one table

| Engine | Tested on | Seen? | Forms | Exact | Share |
|---|---|---|---|---|---|
| Conjugation | Appendix 1 | seen | 770 | 611 | 79.4% |
| Conjugation | the dictionary's five verb forms | **unseen** | 9,559 | 1,431 | **15.0%** |
| Accent rules | the 26 cells of Appendix 1 the page marks | seen | 26 | 15 | marks 81 cells; the page marks 26 |
| Sound changes | Parks's examples to his own 24 rules (ch. 3) | 4 of 39 seen | 39 | 8 | 20.5% |
| Sound changes | Parks's worked examples (ch. 4) | **unseen** | 74 | 15 | **20.3%** |
| Form 2 prediction | form 2 of every dictionary verb | seen | 2,197 | 1,915 | 87.2% |
| Form 2 prediction | the verbs its own check leaves out | not scored before | 35 | 28 | 80% |
| Person derivation | Appendix 1, the cells it derives | seen | 27 | 25 | 93% |
| Person derivation | the start of the dictionary's form 4 | **unseen** | 2,124 | 1,503 | **70.8%** |
| Possession: locative, instrumental | the forms Parks prints as examples under nouns | **unseen** | 675 | 300 | **44.4%** |
| Possession: "my X" for a common noun | Blue Book p. 35 | built on its OCR text | 3 | 0 | every form begins with the non-word *kti* |
| Sentence templates: "is this sentence in the Blue Book?" | the 385 sentences the book prints with an accent | | 385 | 0 | never recognised |

The three figures that were quoted until now (79.4%, 87.2%, 25 of 27) are all
on seen forms. On unseen forms the same engines stand at 15%, at an unknown
figure, and at 71%.

---

## 1. Conjugation: `morpheme_inventory.py`

### On Appendix 1 (seen: the rules were fitted to all 770 cells)

611 of 770 exact. The 159 misses:

| Cause | Forms |
|---|---|
| accent only | 50 |
| accent, and vowel length or glottal stop | 13 |
| vowel length only | 56 |
| glottal stop, or glottal stop and vowel length | 2 |
| other letters, within two | 25 |
| other letters, further off | 13 |

So in 121 of the 159 misses (76%) every letter is right. With accents set
aside, 661 forms have the right letters (85.8%).

| Verb | Exact of 110 | Letters right | | Mode | Exact of 77 |
|---|---|---|---|---|---|
| to come | 43 | 86 | | indicative | 77 |
| to be good | 85 | 85 | | contingent | 72 |
| to be sick | 87 | 87 | | absolutive | 65 |
| to do it | 91 | 98 | | assertive | 64 |
| to drink it | 99 | 99 | | contingent, subordinate | 64 |
| to have it | 102 | 102 | | subjunctive, subordinate | 61 |
| to go | 104 | 104 | | negative | 60 |
| | | | | infinitive, subordinate | 58 |
| | | | | potential | 47 |
| | | | | gerundial | 43 |

Singular persons: 184 of 210 (88%). Dual and plural: 427 of 560 (76%). The
indicative, which a learner meets first, is complete; the gerundial and
potential are worst.

None of this is unseen. And the engine's settings for the seven verbs are not
the dictionary's: for every one of them the stem or the class typed into the
engine differs from the entry Parks prints.

| Verb | Dictionary entry | The engine's setting |
|---|---|---|
| to come | *a*, class 3, preverb *ir-* | stem *aʔ*, class 1, preverb *ir-* |
| to do it | *aar*, class 1-i, preverb *ut-* | stem *uutaar*, class 1, no preverb |
| to go | *at*, class 1 | stem *ʔat*, class 1 |
| to be good | *hiir*, class 1-a, preverb *uur-* | stem *hiir*, class "u", preverb *uur-* |
| to drink it | *kiikaa*, class 4 | stem *kiikaʔ*, class 1 |
| to be sick | *kiraawa/waahc*, **passive**, class 4 | stem *kiraawaʔ*, "descriptive", class "u" |
| to have it | *raah*, class 1 | stem *raa*, class 3 |

That is why the engine cannot start from a dictionary entry: it does not
conjugate Parks's seven verbs from what the dictionary says about them, but
from stems and classes chosen so that the forms come out.

### On the dictionary's five forms (unseen)

The engine was set up for each verb the way its own `--validate-dict` does
it. 1,431 of 9,559 forms exact: **15.0%**.

| | Forms | Exact | Letters right; vowel length or glottal stop differs | Other letters, within two | Further off | No form |
|---|---|---|---|---|---|---|
| All | 9,559 | 1,431 (15.0%) | 739 | 3,276 | 4,072 | 41 |
| Form 1 (I) | 1,615 | 170 (10.5%) | 159 | 595 | 683 | 8 |
| Form 2 (he/she) | 2,232 | 375 (16.8%) | 180 | 1,017 | 651 | 9 |
| Form 3 (imperfective) | 1,274 | 261 (20.5%) | 234 | 389 | 384 | 6 |
| Form 4 (subordinate) | 2,234 | 425 (19.0%) | 114 | 485 | 1,201 | 9 |
| Form 5 (intentive) | 2,204 | 200 (9.1%) | 52 | 790 | 1,153 | 9 |

| Class of verb | Forms | Exact |
|---|---|---|
| active intransitive (VI) | 3,017 | 589 (19.5%) |
| active transitive (VT) | 3,941 | 700 (17.8%) |
| passive (VP) | 620 | 87 (14.0%) |
| locative (VL) | 391 | 33 (8.4%) |
| descriptive (VD) | 1,517 | 22 (1.5%) |
| reflexive (VR) | 73 | 0 |

- Of 2,239 verbs, **41 have every printed form right; 1,484 have none
  right.**
- Verbs with the preverb *ut-*: 0 of 1,219 forms. Class 3 verbs: 20 of 1,206.
- Form 1 of the 123 passive verbs is a patient form (*tiku-* …), as Parks says
  on p. 56. The engine builds an agent form for them: 4 of 123.
- 90% of the misses are in other letters: missing or wrong rules. The two
  simplest single faults account for few of them: the final *k* of a stem not
  becoming *t* (601 forms), and the engine's general rules turning an *s*
  inside a stem into *c*, *kuksat* → *tikukcat* (113 forms). The rest are
  spread over the endings Parks tabulates and the engine does not have
  (*-aʔuk* → *-uʔ*, *-itik* + *-his* + *-ta* → *-itiksta*, the lengthening of
  *-:huʔ*), stems that change in the plural or imperfective, and the meeting
  of preverb and stem.
- The engine puts an accent on 172 dictionary forms. The dictionary's verb
  forms have none.

**The engine's own count is 1,413 of 9,518 forms: 14.8%, the same figure as
on 2026-03-09.** The eleven days of fitting that took Appendix 1 from 35% or
less to 90% moved the dictionary by nothing.

### How much of the error could no rule put right?

On Appendix 1, three quarters of the misses are accent or vowel length. On
the dictionary, under one tenth. The engine is not mostly failing at what
Parks calls unpredictable; it is failing at the regular endings and junctions
of verbs it was not fitted to.

### What it is used for

Nothing. No page of the app calls it.

---

## 2. Accent rules: `accent_rules.py` and the copy inside the conjugation engine

Appendix 1 as printed marks an accent in 26 cells, all in 'to come'. The
engine marks 81.

| | Cells of 770 |
|---|---|
| Neither marks an accent | 687 |
| Both mark, and the form is exact | 15 |
| Both mark, on different vowels | 7 |
| Both mark, and the letters are wrong as well | 2 |
| The page marks, the engine does not | 2 |
| **The engine marks, the page does not** | **57** (50 in 'to come', 7 in 'to do it') |

- If the engine marked no accent at all, it would have 637 of the 770 forms
  exact instead of 611. The accent rules cost 26 forms against the page.
  Against the misread copy they had gained 85.
- `accent_rules.py --validate`, the file's own check: **0 of 26** today. It
  read 78 of 85 against the old copy.
- The one branch of `accent_rules.py` that runs in live use writes *cí* in
  the potential of 'to do it'. The page has no accent in any of those seven
  forms.

Every accent miss is of the kind Parks describes as variable. The dictionary
itself answers whether accents in verb forms can be predicted from the
sources the project has: its 9,559 verb forms are printed without any.

**What it is used for:** only the conjugation engine calls it.

---

## 3. Sound changes: `sound_changes.py`

Both test sets are Parks's own: a word divided into pieces by him, and the
word. The pieces go in; the word should come out.

| | Chapter 3: the examples to his 24 rules | Chapter 4: worked examples |
|---|---|---|
| Examples | 39 | 93, of which 74 usable (see the note) |
| Full engine, exact | 8 (20.5%) | 15 (20.3%) |
| … also right if told to drop a final *s* | 9 | 17 |
| The half the conjugation engine uses | 6 | 12 |
| The pieces simply written together, no rules | 1 | 11 |
| **Seam engine of the word-construction analysis:** the printed word is among the forms it allows | 15 (38.5%) | 36 (48.6%) |
| … and is its first choice | 6 | 14 |

Chapter 3 without the four examples the engine's own test holds: 5 of 35.

The misses of the full engine:

| Cause | Chapter 3 (31 misses) | Chapter 4 (59 misses) |
|---|---|---|
| vowel length only | 2 | 6 |
| glottal stop, or both | 4 | 7 |
| other letters, within two | 13 | 27 |
| other letters, further off | 12 | 19 |

- For 16 of the 23 rules that have a printed example, the engine reproduces
  **none** of Parks's examples of that rule. It reproduces at least one for
  rules 3R, 5, 6, 13, 14, 15 and 19.
- In chapter 4 the rules add four right forms to the eleven that come out
  right by writing the pieces together.
- Named faults in chapter 4: an *s* inside a piece made into *c*, as in
  *iks* + *uʔ* → *ikcuʔ* for *iksuʔ* 'hand' (5); the final *k* of a perfective
  not made into *t* (4); a final *s* not dropped (3); a length mark in his
  pieces that the engine cannot read (1). The other 46 are several things at
  once: the restricted rules not firing on the pieces as
  Parks writes them, vowels contracted where he keeps them apart, and
  word-level changes that are not among the 24 rules.
- About a fifth of the misses are vowel length or glottal stop.

The seam engine does better because it applies a rule only where two pieces
meet. It is a checker, not a generator: it returns every form its rules
allow (three or four on average), and the printed word is the first of them
in only 14 of 74. Neither engine can be trusted to produce an inflected verb
from its pieces.

**Note on the test set.** Eight of the 93 chapter 4 examples are mis-paired in
the gold file of the word-construction analysis and were left out for both
engines: in six the "word" is another word of the same example (*aruusaʔ*
'horse' three times, listed beside the pieces of a verb), and in two a line
holding two analyses had the pieces of both joined. Eleven more carry the
gold file's own flags. That gold file should be made again; it does not
change the picture here.

**What it is used for.** The full pipeline: nothing. Single rules are
borrowed by the conjugation engine and the possession engine.

---

## 4. Form 2 prediction: `stem_extractor.py`

| | Verbs | Exact | Vowel length | Glottal stop | Both | Other letters, within two | Further off |
|---|---|---|---|---|---|---|---|
| All verbs with a form 2 | 2,232 | 1,943 (87.1%) | 53 | 42 | 40 | 88 | 66 |
| Seen: what its own check scores | 2,197 | 1,915 (87.2%) | 51 | 41 | 40 | 85 | 65 |
| Not scored before: form 2 printed in two versions | 35 | 28 (80%) | 2 | 1 | 0 | 3 | 1 |

- **There is no unseen test for it in the project's sources.** Its rules were
  read off the form 2 of every dictionary verb, and no other source prints a
  form 2. The 35 verbs its check leaves out are the only ones its rules were
  not adjusted on; they are too few, and too unusual, to carry a figure.
- Of its 289 misses, 135 (47%) are vowel length or glottal stop: for example
  *kiikaa* → *tikiikaaʔ* where Parks prints *tikiikaʔ*. Several of its rules
  shorten or keep a vowel by rule. Parks calls that alternation
  unpredictable, and these misses agree with him.
- By class: transitive 90.0%, locative 89.7%, intransitive 87.6%, passive
  83.1%, descriptive 81.9%, reflexive 67%.

**The stored score.** `form2_confidence` puts 2,181 of the 2,232 verbs in the
band "High". Of those, 1,928 are predicted right (88%). So "High" is on 253
verbs whose prediction is wrong, and the badge separates almost nothing: 98%
of verbs carry it.

**What it is used for.**

- The prediction is used in one place, the word-construction analysis, as a
  check on an attested form. It never shows a form to anyone. In that use an
  87% fit is useful: it can only confirm, and a miss costs nothing.
- The score is shown on every verb page as "Prediction: High / Med / Low",
  beside forms that are attested, not predicted.

---

## 5. Person and mode derivation: `person_forms.py`

### On Appendix 1 (seen)

25 of 27 right, one not attempted. The two misses are vowel length: *ruhii*
for *ruuhii*, *riihkiraawaʔ* for *rihkiraawaʔ*.

### The question form for "he/she", against the dictionary's form 4 (unseen)

The engine makes the question form by changing the start of form 2. Form 4,
the gerundial, is *irii-* before that same mode with a subordinate ending;
so with *irii-* taken off, form 4 must start as the question form starts.
The test compares the start only: the letters the engine changed and the two
after them.

How good a witness form 4 is, measured where Parks prints both forms
(Appendix 1): in the third person the starts agree for 5 of the 7 verbs, and
for all 7 once a glottal stop is set aside. So the witness is sound for
letters and vowel length, and not for the glottal stop.

2,124 verbs tested:

| The engine's rule | Read from | Verbs | Form 4 starts the same | |
|---|---|---|---|---|
| *ti-* → *ra-* | Appendix 1 | 939 | 925 | 98.5% |
| *ti-* → *ra-* before a stem in *h* | Appendix 1 | 190 | 187 | 98.4% |
| *tu-* → *ru-* | Appendix 1 | 339 | 325 | 95.9% |
| *tiʔ-* → *raʔ-* | Appendix 1 | 48 | 37 (4 more but for a glottal stop) | 77% |
| *tii-* → *rii-* | the OCR slip "Ka rii hitu'?" | 352 | 29 | **8.2%** |
| *tuu-* → *ru-* with *uur-* | the misread cell *ruhii* | 109 | 0 (105 differ in vowel length) | **0%** |
| *tih-* → *riih-* | the misread cell *riihkiraawaʔ* | 4 | 0 | **0%** |
| no rule (form 2 begins *ta-*, *ru-* or otherwise) | | 143 | no form given | |
| **All** | | **2,124** | **1,503** | **70.8%** |

**The rules read from correctly read forms hold on 1,474 of 1,516 unseen
verbs (97%). The three built on misread forms hold on 29 of 465 (6%).**

For the *tii-* verbs form 4 shows *raa-* (*tiirit*, *iriiraariki*): the
question form of *ti* + *a…* is *ra* + *a…*. For the *uur-* verbs it shows
*ruu-*, as Appendix 1 does once corrected.

Sorted by cause, the 478 disagreements are 353 in other letters (322 of them
that one *tii-* rule), 121 in vowel length (105 of them that one *uur-*
rule) and 4 in the glottal stop. Almost all of the error is three rules.

### "I" for descriptive verbs (unseen)

For a descriptive or locative verb with no printed form 1 the engine makes
one: *tiku* + stem, after 'to be sick'.

- It does so for 184 verbs (*tikuhaahka* …). Parks prints no first person
  for any of them, and says some verb classes lack some of the five forms
  (p. 57).
- Of the 184 descriptive verbs that **do** have a printed form 1, none
  begins *tiku-*: 181 begin with *ta-* and the agent prefix (*tatkitiiʔ*,
  *tatpariiʔit*). Where the engine's rule can be applied to them it gives the
  printed form 0 times in 81.
- 'To be sick' is a passive verb in the dictionary, and 122 of the 123
  printed first persons of passive verbs begin *tiku-*. The pattern was read
  off a passive verb and applied to descriptive ones.

### The forms nobody can check

| Form it makes | Verbs (of 2,239) | Found as a word in the dictionary's 2,652 examples |
|---|---|---|
| you, past | 1,757 (78%) | 1 |
| I, present | 1,149 (51%) | 4 |
| you, present | 1,134 (51%) | 0 |
| I, future | 1,751 (78%) | 0 |
| you, future | 1,727 (77%) | 0 |
| I, question form | 1,757 (78%) | 1 |
| you, question form | 1,757 (78%) | 3 |
| he/she, question form | 2,046 (91%) | 7 |

About 13,000 forms, of which 16 occur in a printed example. The present and
future of "I" and "you" rest on no printed paradigm at all: Appendix 1 is
perfective only.

### What it is used for

The sentence builder. Asked for the seven verbs of Appendix 1 through their
dictionary entries, as the page asks, it gives 33 of the 42 printed cells.
Two misses are the vowel-length rules above, one form is not attempted, and
**six are another verb**: the page passes a verb by its spelling, *aar*
'do' and *aar* 'become' are spelled alike, and the builder conjugates
'become'. 101 spellings are shared by several verbs (211 of the 2,239).

---

## 6. Noun possession: `possession_engine.py`

### What the app serves, for all 1,706 nouns

| | Nouns |
|---|---|
| Answered with *kti ratiru X*, *kti rasiru X*, *kti rau X* | 1,671 |
| … and marked "attested" | 1,671 |
| Answered from Appendix 3 (kin terms) | 9 |
| Answered with the body-part pattern | 19 |
| "Not a noun": the route found another entry with the same spelling first | 7 |
| Answered for a different entry of the same spelling | 12 |
| Given an instrumental ("with, using …") | 1,678 |
| … of which tagged animal, kin or person | 475 (283 animals) |
| Treated as a tribe or place | 31, of which 3 are |

- ***kti* does not exist.** The Blue Book prints *kú•ratir•u paks•kúku'* 'my
  hat'. So the first word of the answer for 98% of nouns is an OCR slip, and
  the app labels it "ATTESTED".
- **The 28 false tribes** include four numbers, 'male horse', 'rooster',
  'carpenter', 'biscuit' and 'airplane': *piiskitawiru*, "among the biscuit;
  in biscuit country". The real tribes are missed: for *Paari* 'Pawnee' the
  app gives *Paarikat* where Parks prints *Paariru*.
- **The 19 body-part answers** are all dependent nouns, whose headword ends
  in a dash or is two spellings. The engine pastes the headword in whole:
  *tirithaak-, rak-ta*, "here is my wood (hanging)"; *tirittut-ta*, "here is
  my snake (hanging)".
- **Kin terms.** Of the 21 kin nouns in the dictionary, 9 are answered from
  Appendix 3 and agree with it. The other 12 get *kti ratiru* + stem, among
  them four that are in Appendix 3: for the stem *-taat-* 'sister' the app
  gives *kti ratiru taat* where Parks prints *itaahiʔ*.
- **The first nouns a learner meets.** Of the 36 nouns in flashcard weeks 1
  to 4, 34 are answered with *kti …*, all 36 are marked attested.

### Locative and instrumental, against the forms Parks prints (unseen)

Under 609 noun entries Parks prints the noun's own locative or instrumental
as an example: *siiskat* 'on the awl', *tahuuhiriʔ* 'with the flint',
*Paariru* 'among the Pawnee'. 675 such forms, never used to build or test
the engine. Each was compared with what the app offers for that noun.

| Ending | Forms | The app offers the printed form | Vowel length | Glottal stop | Both | Other letters, within two | Further off |
|---|---|---|---|---|---|---|---|
| *-kat* | 489 | 215 (44.0%) | 87 | 61 | 8 | 53 | 64 |
| *-hiriʔ* | 171 | 84 (49.1%) | 17 | 0 | 1 | 40 | 28 |
| *-ru* | 15 | 1 | 0 | 0 | 0 | 1 | 13 |
| **All** | **675** | **300 (44.4%)** | 104 | 61 | 9 | 94 | 105 |

(Two more forms belong to nouns the app answers with "not a noun".)

- **Vowel length, 104 forms.** Parks shortens the vowel before the suffix in
  many nouns (*taatuʔ* 'stalk', *tatkat*) and not in others. This is the
  alternation he calls unpredictable.
- **Glottal stop, 61 forms.** The engine keeps the *ʔ* that stands before
  *-uʔ* (*ksawiʔkat* for *ksawikat*). A missing rule.
- **Other letters, 199 forms.** The tribe test (14 of the 15 printed *-ru*
  forms missed); *-sukat* put after every stem in *-ki*, where Parks prints
  *-kat* or *-kiskat* (*cuurakisukat* for *cuurakiskat* 'among the girls'):
  the rule was read from two words and fails on 20; nouns in *…kusuʔ* cut as
  if *-kusuʔ* were a suffix; the *h* of *-hiriʔ*; plurals in *-raar-*.
- **Meaning.** Of the 84 forms in *-hiriʔ* that come out right, 63 are forms
  Parks translates as a place ("on the tail", "in the field"). The app
  labels every one "instrumental: with/using …".
- So about 46% of the misses are vowel length or glottal stop, and about 53%
  are rules.

Parks's own seven examples on p. 30, asked for through the app: one comes
out as printed (*riihitawiru*), one differs in vowel length (*akaahkat* for
*akahkat*), five are wrong or not offered (*ikskat* for *iksiriʔ*, *Sahikat*
for *sahiiru*).

### The stem

- Against Parks's etymologies (1,350 nouns whose etymology he prints in
  pieces): the engine strips the suffix his analysis shows, or rightly none,
  for 1,217 (90%). It is wrong for 133: it strips *-uʔ* where the word ends
  in another piece (55, *aahkucuuʔ* cut to *aahkucu*); it misses the
  diminutive, which usually surfaces as *-ki* (37, *asaaki* among them); it
  strips *-kusuʔ* from 27 nouns, and for all 22 of them whose etymology he
  prints in pieces his analysis is *…kus* + *-uʔ*.
- Against the combining forms Parks prints (408 nouns): the engine's stem is
  one of them for 152 (37%). For *akaaruʔ* 'house' he prints *akaar-*,
  *akah-*; for *ahitki* he prints *ahiht-*, *ahit-*, *ahic-*, *ahih-* and the
  engine keeps *ahitki*.

### The stem on every entry page

The app calls the stem function for every entry to decide which example
sentences to show. The stem makes **no difference**: not one example is
shown because of it. But the filter it serves hides most of what Parks
prints:

| | Examples Parks prints | Shown on the entry page |
|---|---|---|
| Under verbs | 661 | 18 |
| Under nouns | 1,518 | 316 |
| Under other words | 473 | 94 |
| **All** | **2,652** | **428 (16%)** |

1,340 of the 1,658 entries that have examples show none of them. The filter
was written to keep *kirike* 'what?' off the page of *kiri* 'cat' among Blue
Book sentences, and is applied to the dictionary's own examples too. Among
the hidden ones are the very locatives the engine tries to compute: the page
of *sakuuruʔ* 'sun' hides Parks's *sakuhkat* and offers a computed form
instead.

(The public site is not affected: it shows all 2,652.)

---

## 7. Sentence templates: `sentence_templates.py`

There is little to compute here: a frame puts given words in a given order.
What can be measured is the words it holds and the claims it makes.

**Its words** (from Stage 1). Of the 40 words it offers for its slots, 13 are
as the Blue Book prints them, 18 lack the printed accent or are a word inside
a printed sentence, and 9 are not in the book: six dictionary spellings and
the three non-words *ilan'*, *kirti*, *stiks*. Its ten example sentences all
lack the printed accents.

**"Attested in the Blue Book."** The engine gives a sentence its highest
confidence when it finds it in the Blue Book.

| | Sentences |
|---|---|
| Blue Book dialogue lines, phrases and grammar examples | 454 |
| … printed with at least one accent | 385 |
| Found when typed as the engine types, without accents | 19 |
| … among the 385 with an accent | **0** |

Since the Blue Book forms carry their printed accents, the engine can no
longer recognise 85% of the book's own sentences.

**The frame "the stick is red".** It writes *ti* and the dictionary stem of a
descriptive verb. For 394 descriptive verbs without a preverb, joined to
*ti* this is the form 2 Parks prints for **92 (23%)**; for 129 it differs in
vowel length or the glottal stop, mostly the echo vowel (*ti pahaat* against
*tipahaaʔat*); for 173 in other letters.
Another 49 need a preverb, which the frame has no place for. The frame is
right for the Blue Book's own sentence, in the Blue Book's spelling, and for
little else.

**A verb from the dictionary.** See person derivation above: 33 of 42 cells
for Parks's seven verbs, six of the misses being the wrong verb.

**What it is used for.** The sentence builder page, and the "practice" line
on each lesson page of the local app.

---

## How much of each engine's error could no rule put right?

| Engine, test | Misses | Accent | Vowel length or glottal stop | Other letters |
|---|---|---|---|---|
| Conjugation, Appendix 1 (seen) | 159 | 63 (40%) | 58 (36%) | 38 (24%) |
| Conjugation, dictionary (unseen) | 8,128 | 2 | 737 (9%) | 7,348 (90%), and 41 with no form |
| Sound changes, chapter 4 | 59 | 0 | 13 (22%) | 46 (78%) |
| Form 2 prediction | 289 | 0 | 135 (47%) | 154 (53%) |
| Person derivation, form 4 | 478 | 0 | 125 (26%) | 353 (74%) |
| Possession, printed locatives | 375 | 0 | 174 (46%) | 199 (53%), and 2 not answered |

Two things stand out.

- **Accents.** Every accent the engines produce was fitted to the misread
  copy. Against the page the accent rules do harm. Nothing in the
  dictionary's verb forms gives a second place to learn or test accent
  placement.
- **Vowel length.** Where an engine is otherwise good (form 2, the
  locatives), close to half of what is left is vowel length and the glottal
  stop. That is a ceiling: a careful repair of those two engines could
  remove the rule errors and would still be left with roughly one form in
  sixteen (form 2) or one in four (locatives) differing from print in a
  vowel's length or a *ʔ*.

## What the engines are used for, in one table

| Engine | Reaches a person through | What the person is shown |
|---|---|---|
| Conjugation | nothing | |
| Accent rules | nothing | |
| Sound changes | nothing directly | |
| Form 2 prediction | the badge on verb pages; study-card order | "Prediction: High" on 98% of verbs, beside attested forms |
| Person derivation | the sentence builder | a form for "you", a question form, a present or future; marked "derived" |
| Possession | the box on every noun page | *kti ratiru X* marked "ATTESTED" on 98% of nouns; a locative right 44% of the time; "with, using" for 283 animals |
| Possession (stem) | every entry page | nothing: it changes no page |
| Sentence templates | the sentence builder; lesson pages | sentences in two spellings, without the printed accents; three non-words on offer |

## Found on the way, outside the engines

1. **The public lesson pages still carry OCR slips.** The audit corrected 104
   readings in the Blue Book table as OCR slips. 65 of the old readings still
   stand in the lessons (62 times in the grammar notes, 4 in dialogue
   lines), on 14 of the 20 public lesson pages (lesson 7 has 14): *Stiks .atku!* for *Súks•atku!*, *KIRIKJ RA•TARAWIS?*
   for *KIRIKÉ RA•TARAWIS?*, *kti•ratiru paks-ktiku'* for *kú•ratir•u
   paks•kúku'*. This is in front of learners now. The list is in
   `data/use_summary.json` under `3_lessons`.
2. **The local app hides 84% of Parks's example sentences** (section 6).
3. **`function_words` holds four non-words** marked as attested in the Blue
   Book: *ilanʔ*, *kirti*, *stiks*, and *kti* glossed "your". The
   `bb_function_words` rows for the first two now contradict themselves:
   the word is *Kirti*, the sentence beside it reads *Kirú …*.
4. **The gold file of Parks's worked examples** has eight mis-paired items
   (section 3).
5. **The word-building guide** prints 37 rows of the conjugation engine's
   table as "Parks's own tables" (Stage 1).

None of these was changed.
