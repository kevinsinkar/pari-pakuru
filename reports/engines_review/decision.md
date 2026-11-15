# What should become of the grammar engines? A decision paper

*For the project owner. Written 2026-11-14, at the end of Stage 3 of the
engines review. Nothing has been changed: no engine, no data, no page of the
app. The evidence is in [profiles.md](profiles.md) (what each engine is built
on) and [measurements.md](measurements.md) (what each gets right). You do not
need to read those to decide; this paper gives the figures that matter.*

## What I recommend

**Stop computing Pawnee forms, with two narrow exceptions, and show what the
sources print instead.** The sources print far more than the app shows today.
The two exceptions are the "you" and question forms of a verb, made from a
printed form by rules that have passed a test on unseen verbs, and sentences
put together from printed words. Both stay in the local app and are
labelled as made here.

| Engine | Recommendation | In one line |
|---|---|---|
| Conjugation | **Withdraw** | Used by nothing. Right on 15% of the 9,559 verb forms it was not fitted to |
| Accent rules | **Withdraw** | Built on 85 accents of which the page has 26. They make the engine worse |
| Sound changes | **Keep the rules as a reference, retire the engine** | Reproduces a fifth of Parks's own examples of the rules it codes. The word-construction analysis already has a better one |
| Form 2 prediction | **Keep as a checker; remove the badge and the score** | Its one sound use is confirming attested forms. The "Prediction: High" badge is on 98% of verbs and says nothing |
| Person derivation | **Repair, narrowly** | The rules it read from correct forms hold on 97% of unseen verbs. Three rules built on misread forms hold on 6%. Take those out, and stop it inventing forms Parks gives none of |
| Noun possession | **Replace by a lookup of printed forms** | Its "my X" begins with *kti*, an OCR slip, for 98% of nouns, under a badge that says "ATTESTED". Parks prints 675 locative and instrumental forms the app could show instead and currently hides |
| Sentence templates | **Repair by copying** | Three of its words do not exist, and none of its Blue Book sentences has the printed accents. No rule needs changing; its words need to come from the corrected table |

Before any of that, one thing that is not an engine and **is in front of
learners now**: 14 of the 20 lesson pages on the public site still carry OCR
slips that were corrected everywhere else (*Stiks .atku!* for *Súks•atku!*).
I would fix that first. It is section 9.

Everything recommended here can be done without reading a page image and
without sub-agents. Sizes are given per engine: **small** is part of one
working session, **medium** one or two.

## The finding behind the recommendation

The brief named three rules that had been built on a misread form and passed
their own tests. Reading every engine in full, I found six more of the same
kind:

| In the engine | What it was built on | What the page has |
|---|---|---|
| Possession: "my X" is *kti ratiru X* | OCR text *kti•ratiru* | *kú•ratir•u* (Blue Book p. 35). OCR read *ú* as *ti* |
| Sentence builder: *ilan'* "yes" | OCR text *Ilan'* | *Háu'* |
| Sentence builder: *kirti* "where (destination)" | OCR text *Kirti* | *Kirú* |
| Sentence builder: *stiks* "let me …" | OCR text *Stiks* | *Súks* |
| Person derivation: *tuu-* → *ru-*, *tih-* → *riih-* | two misread cells of Appendix 1 | *ruuhii*, *rihkiraawaʔ* |
| Person derivation: *tii-* → *rii-* | OCR text *Ka rii hitu'?* | *Ka rú hitu'?* |

That makes nine. In every case the corrected form is already in the
database: the audit of 2026-11-13 fixed the tables and did not look at the
code. And in every case the engine's own test still passes, because the test
holds the same misreading.

The measurements then showed what that pattern costs, most clearly in person
derivation, where the two kinds of rule sit side by side and can be tested
on 2,124 verbs the code was never fitted to:

| Rules read from | Unseen verbs | Agree with the dictionary's own form 4 |
|---|---|---|
| correctly read forms of Appendix 1 | 1,516 | 1,474 (97%) |
| misread forms | 465 | 29 (6%) |

So the lesson of this review is not that rules cannot work. A rule read from
a correct source and tested on forms it has not seen can be very good. The
lesson is that this project has no way to know which rules those are except
by testing each on unseen printed forms, and that for most of what the
engines produce no printed form exists to test against.

## What this review cannot show

It shows how often an engine reproduces what Parks or the Blue Book printed.
It cannot show that a form they did not print is a form a speaker would say.
Only a speaker can.

Keep two questions apart when you decide:

1. **Is an engine good enough to help you study the grammar on your own
   machine?** That is yours to answer, and this paper is for that.
2. **Could anything an engine produces ever be shown to learners?** That is
   for the Pawnee community. The packet in `community_review/` is how the
   project means to ask. Nothing in this paper moves anything computed onto
   the public site, and I recommend that rule stays whatever you choose.

A figure like "97%" answers only the first question, and only for the kind
of form that was tested.

---

## 1. Conjugation engine (`scripts/morpheme_inventory.py`)

**What it is.** Builds a verb form from a stem, a class, a mode and a person.

**Evidence.**

- On Appendix 1, which its rules were fitted to: 611 of 770 (79.4%).
- On the dictionary's five verb forms, which it was not fitted to:
  **1,431 of 9,559 (15.0%)**. Of 2,239 verbs, 41 have every printed form
  right and 1,484 have none.
- Its own count on the dictionary is 14.8% today. It was 14.8% on
  2026-03-09, before eleven days of work took Appendix 1 from 35% or less
  to 90%. That work moved the dictionary by nothing.
- Nine tenths of its misses on the dictionary are wrong or missing rules,
  not vowel length or accent.
- It does not conjugate Parks's seven verbs from their dictionary entries:
  for all seven, the stem or class typed into the engine differs from what
  the entry prints. 'To be sick' is a passive verb in the dictionary and a
  "descriptive" one in the engine.
- **No page of the app calls it.**

| Choice | Work | What you could be shown wrong |
|---|---|---|
| **Withdraw** (recommended): move it and `accent_rules.py` to `archived/`, remove its block from the dashboard | small | nothing |
| Keep as a local tool | none | whatever you ask it for: about five verb forms in six are wrong outside Appendix 1 |
| Repair | not a repair but a new engine. It would have to start from the dictionary's own stems and classes and Parks's Table 17 as printed. Large, and it needs a linguist | unknown until built |

If you ever want this taken up again, the test is ready: the 9,559
dictionary forms, of which half should be sealed before a line is written.

**What replaces it.** Appendix 1 as Parks prints it (the table
`verb_paradigms` and the printable in `curriculum/printables/`), and the
five forms printed in each entry.

**Stored values.**

- `verb_paradigms`: keep. It is a copy of Appendix 1.
- `morpheme_inventory` (37 rows) and `verb_template_slots` (27 rows): these
  are the engine's own arrangement, written in March. Six of the 37 rows are
  not in Parks's tables (*kaaka-* for his *kaakaa-*, *raak-* and *iraak-*
  for his *rak-*, the suffixes *-u* and *-wi*). **The word-building guide
  prints all 37 under the words "These are Parks's own tables."** I
  recommend the guide take that section from
  `extracted_data/grammatical_overview_tables.json`, which holds the tables
  as printed and which nothing reads yet, and that the two tables then be
  dropped. This changes the guide (not published; awaiting review) and its
  check, so it is a **small to medium** change in `scripts/morphology_v2/`.

## 2. Accent rules (`scripts/accent_rules.py`, and a copy inside the conjugation engine)

**Evidence.**

- The rules were "derived from analysis of 85 Appendix 1 accented forms".
  The page has 26 accented forms, all in one verb. 15 of the 85 are the same
  on the page.
- The engine marks an accent in 81 cells. In **57** the page has none.
- With no accent rules at all the conjugation engine would have 637 forms
  right instead of 611.
- The file's own check gives **0 of 26** today.
- Parks (p. 15): stress is not phonemic and is not marked on words; most
  patterns are variable. The dictionary's 9,559 verb forms carry no accent,
  so the sources offer no second place to learn or test where one falls.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| **Withdraw** with the conjugation engine (recommended) | none extra | nothing |
| Keep | none | an accent on forms where the page has none |
| Repair | there is nothing to fit rules to but 26 forms of one verb | |

**Stored values.** None.

## 3. Sound changes (`scripts/sound_changes.py`)

**Evidence.**

- Its own test passes 11 of 11. Seven of the eleven expected values are
  fragments the engine itself produced; three of them stand in for an example
  of Parks that the engine does **not** reproduce.
- Parks prints 39 examples with his 24 rules. The engine reproduces **8**.
  For 16 of the 23 rules that have an example, it reproduces none.
- Parks's worked examples in chapter 4, never tried before: **15 of 74**.
  Writing the pieces together with no rules at all gives 11.
- Its general rules fire inside a root as well as between pieces: *iks* +
  *uʔ* comes out *ikcuʔ* for *iksuʔ* 'hand'. A later patch hid this for
  nouns by switching three rules off, on the grounds that they were
  "verb-specific"; Parks calls them unrestricted.
- The seam engine of the word-construction analysis
  (`scripts/morphology_v2/seams.py`) applies rules only where pieces meet and
  names the source of each. On the same examples the printed word is among
  the forms it allows for 15 of 39 and 36 of 74. It is a checker: it returns
  several candidates and does not pick.
- Nothing in the app calls the engine. Other code borrows single rules.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| **Keep the 24 rules as a reference table; stop calling the code an engine** (recommended): the table `sound_change_rules` stays; the file stays where it is because other code imports from it; its `--test` is replaced by the honest measure on Parks's 39 examples; the README says it must not be used to produce a form | small | nothing |
| Repair it to apply rules only between pieces | that is `seams.py`, which exists | |
| Withdraw the file | not possible yet: the word-construction analysis imports it by way of `root_extraction.py` | |

Neither engine can be trusted to build an inflected verb from its pieces.
That is a finding about the 24 rules as much as about the code: Parks's
examples involve changes at the end of the word and in vowel length that are
not among the 24.

**Stored values.** `sound_change_rules`: keep. It is Parks's rules and
examples, corrected from the page.

## 4. Form 2 prediction (`scripts/stem_extractor.py`)

**Evidence.**

- 1,915 of 2,197 (87.2%), on the same forms its rules were read from. **No
  unseen test exists**: no other source prints a form 2.
- Nearly half of its misses are vowel length or the glottal stop, which is
  where Parks says prediction stops.
- The predictor shows no form to anyone. The word-construction analysis uses
  it to confirm attested forms, where a miss costs nothing.
- The stored score `form2_confidence` is shown on every verb page as
  "Prediction: High / Med / Low". It is "High" for 98% of verbs, including
  253 whose prediction is wrong. It is shown beside forms that are attested,
  so it suggests something on the page is predicted when nothing is. 1,863
  of the 2,239 stored scores no longer equal what the code computes.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| **Keep the predictor as a checker; remove the badge, the score and its use in ordering study cards** (recommended) | small | nothing |
| Keep everything, compute the score again | small | a badge that looks like a judgement on the word and is not |
| Withdraw the predictor | small, but the word-construction analysis loses one of its checks and its outputs change | nothing |

**Stored values.** `lexical_entries.form2_confidence`: set to empty for all
entries (the column can stay), or dropped. I recommend emptying it and
removing the badge from `entry.html` and `_entry_card.html`.

## 5. Person and mode derivation (`scripts/person_forms.py`)

**What it is.** Makes "you" forms, question forms and present and future
forms by changing the start of an attested form. Behind the sentence builder.

**Evidence.**

- On Appendix 1, which its rules were read from: 25 of 27.
- Its question form for "he/she", tested on 2,124 unseen verbs against the
  start of the dictionary's form 4:

  | Rule | Verbs | Agree |
  |---|---|---|
  | *ti-* → *ra-* (two variants) | 1,129 | 1,112 (98.5%) |
  | *tu-* → *ru-* | 339 | 325 (95.9%) |
  | *tiʔ-* → *raʔ-* | 48 | 37 |
  | *tii-* → *rii-* (from the OCR slip) | 352 | 29 (8%) |
  | *tuu-* → *ru-* (from a misread cell) | 109 | 0 |
  | *tih-* → *riih-* (from a misread cell) | 4 | 0 |

- For descriptive verbs with no printed first person it makes one, *tiku* +
  stem, for 184 verbs. The pattern was read from 'to be sick', which is a
  passive verb. None of the 184 descriptive verbs that do print a first
  person forms it that way, and Parks says some verb classes lack some forms
  (p. 57).
- It makes about 13,000 forms in all. Sixteen occur in a printed example.
  The present and future of "I" and "you" rest on no printed paradigm:
  Appendix 1 has only perfective forms.
- The sentence builder passes a verb by its spelling. *aar* 'do' and *aar*
  'become' are spelled alike, and the builder conjugates the wrong one. 211
  verbs share a spelling with another.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| Keep as it is | none | a question form that disagrees with the dictionary's own form 4 for 478 of 2,124 verbs; a first person for 184 verbs that may have none; the wrong verb for up to 211; forms nothing can check |
| **Repair, narrowly** (recommended), as set out below | small to medium | "you" forms that follow Appendix 1's pattern and cannot be checked elsewhere, labelled as such |
| Withdraw: the builder offers only the attested forms 1, 2, 3 and 5 | small | nothing; you lose "you" and the question forms |

**The repair I would make, and nothing beyond it:**

1. Take out the three rules built on misread forms.
2. For the 465 verbs those rules covered, give no question form for
   "he/she", unless a rule read from the open half of the test below holds
   there for at least 97% of the verbs it covers. No rule is added for a
   single verb.
3. Give no first person where Parks prints none. Keep the *tiku-* pattern
   only for verbs whose printed form 1 has it.
4. Drop the present and future of "I" and "you", or show them only behind a
   plain warning that no source prints such a form. I would drop them.
5. Pass the entry, not the spelling.

**How it would be measured.** Before any change, the 2,124 verbs with forms 2
and 4 are split in two by a rule written down first (the last digit of the
number that ends the entry's id, odd or even). The open half may be looked
at and rules may be read from it; the sealed half is not opened until the
code is finished. Good enough to keep: on the sealed half, the question form
given for "he/she" starts as the dictionary's form 4 starts for at least 97%
of the verbs it gives a form for, and the share of verbs it declines is
reported beside it. (Today, over all 2,124: it gives a form for 1,981 and
1,503 of those agree, 76%.) For the "you" forms there is no unseen test in the
sources. They would stay marked "derived; not checked against a printed
form", in the local app only.

**Do not extend it** to plurals, the negative or other modes until someone
who knows the language has looked at what it gives now. Each extension adds
thousands of forms that nothing in the sources can check.

**Stored values.** None.

## 6. Noun possession (`scripts/possession_engine.py`, `scripts/noun_possession.py`)

**What it is.** The "Possession" box on every noun's page: "my / your /
his", a locative and an instrumental.

**Evidence.** Asked the way the app asks, for all 1,706 nouns:

- **1,671 nouns (98%) are answered with *kti ratiru X*.** *kti* is an OCR
  slip for *kú*. The Blue Book prints the construction once, with one noun
  (*kú•ratir•u paks•kúku'* 'my hat'). The app labels the answer "ATTESTED"
  for every noun, including 34 of the 36 nouns in the first four flashcard
  weeks.
- 12 of the 21 kin nouns get *kti ratiru* + stem, among them four that
  Appendix 3 lists: *kti ratiru taat* where Parks prints *itaahiʔ* 'my
  sister'.
- 28 common nouns are taken for tribes ("among the biscuit; in biscuit
  country"), and the real ones are missed: *Paarikat* for Parks's *Paariru*
  'among the Pawnee'.
- 283 animals are given a "with, using …" form.
- **Locatives and instrumentals, against the 675 forms Parks prints as
  examples under nouns** (never used to build or test the engine): the app
  offers the printed form for **300 (44%)**. Of the misses, 46% are vowel
  length or a glottal stop and 53% are rules.
- Of the 84 forms in *-hiriʔ* it gets right, 63 are forms Parks translates
  as a place ("on the tail"). The app labels them all "with, using".
- Its tests: 60 of 60, of which 23 compare with no printed form: 16 hold
  the engine's own output (seven beginning with *kti*), one returns its
  input, and 6 check only that something comes back.

**And the attested forms are already there.** Parks prints the locative or
instrumental of 609 nouns as an example in the noun's own entry (*siiskat*
'on the awl'), and combining forms for 408. The app hides the first behind a
filter and computes a replacement that is right less than half the time.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| Keep as it is | none | *kti …* under "ATTESTED" on almost every noun; a wrong locative more often than a right one |
| Repair the generator | medium to large. *kti* → *kú*, the tribe test, the *ʔ* before *-uʔ*, *-sukat*. Vowel length would still leave about one printed locative in six different. And "my X" for every noun from one printed example is invention whatever its spelling | forms no source prints, for most nouns |
| **Replace by a lookup of printed forms** (recommended): the box shows, for this noun, what Parks or the Blue Book prints and nothing else: the kin forms of Appendix 3; the locative and instrumental examples printed in the entry; the combining forms printed in the entry; the Blue Book's own possession lines for the nouns it has. Each with its source. The generator moves to `archived/` | medium | nothing computed. Many nouns will show an empty box, which is the truth |
| Withdraw the box | small | nothing |

The lookup also needs one fix outside the engine: the entry page must stop
filtering Parks's own examples (section 9).

**Stored values.**

- `possession_examples` (20 rows): drop. It is the engine's output stored as
  "expected", and still holds the misread *asaas*, *atipaat*, *apaat* and
  three *kti* phrases.
- `noun_stems` (49 rows): drop. Computed, linked to no entry, 20 of its
  "headwords" are not in the dictionary.
- `kinship_paradigms` (14 rows): keep the 11 from Appendix 3. Drop the three
  typed from OCR text (*swat* is printed *awat*); the Blue Book's forms are
  in `blue_book_attestations` as read from the scan.
- `extracted_data/noun_possession_catalog.json`: remove. Computed; nothing
  reads it.

## 7. Sentence templates (`scripts/sentence_templates.py`, `scripts/template_slot_fillers.py`)

**What it is.** Ten sentence frames from Blue Book dialogues, filled with
words. Behind the sentence builder.

**Evidence.**

- The frames put words in order; there is little to get wrong there. What is
  wrong is the words.
- Of the 40 words it offers, 13 are as the Blue Book prints them. Three do
  not exist (*ilan'*, *kirti*, *stiks*). Six are dictionary spellings
  offered as Blue Book words.
- None of its ten example sentences, and 2 of its 27 Blue Book test
  sentences, are as the book prints them: the rest lack the printed accents,
  and some keep OCR artefacts.
- It gives a sentence its highest confidence when it finds it in the Blue
  Book. Because the table now has the printed accents and the engine's words
  do not, it recognises **none** of the 385 sentences the book prints with
  an accent.
- "The stick is red": the frame writes *ti* and a verb's dictionary stem.
  For 394 descriptive verbs that is Parks's printed form for 92 (23%).
- A dictionary verb is put, in Parks's spelling, into a sentence in the Blue
  Book's spelling.

| Choice | Work | What you could be shown wrong |
|---|---|---|
| Keep as it is | none | three non-words on offer; every Blue Book sentence without its accents; bare stems as verbs |
| **Repair by copying** (recommended), as set out below | medium | a sentence put together here from printed words, in an order the book uses, labelled as not printed anywhere |
| Rebuild as a reader of the book's own sentences: for each frame, show the sentences the Blue Book prints that follow it; no assembly | small to medium | nothing |
| Withdraw | small | nothing |

**The repair:**

1. Every Blue Book form in the two files comes from a row of
   `blue_book_attestations`, by its row, not typed. The three non-words go.
2. A sentence is marked "printed in the Blue Book, lesson N" only when it
   equals a printed sentence, accents included. Anything else is marked "put
   together here; not printed".
3. "The stick is red" uses the form Parks or the Blue Book prints for that
   verb, and is offered only where one is printed.
4. One spelling per sentence, and the entry rather than the spelling for a
   chosen verb.

**How it would be measured.** Not by a score: by a check, like the one the
word-building guide has, that every Pawnee word in the two files is a row of
`blue_book_attestations` or an attested dictionary form. It passes at zero
exceptions.

**Stored values.** None of its own. `function_words` holds four non-words
from the same slips (*ilanʔ*, *kirti*, *stiks*, and *kti* glossed "your"),
each marked as attested in the Blue Book. They should be removed in the same
change; that table belongs to another phase, so I list it in section 9.

---

## 8. Where I differ from the earlier session, and why

The session that made the corrections wrote, in the ranking of 2026-11-14:
*"Recommended: withdraw the accent rules, leave from-scratch conjugation
paused, and extend person derivation from attested forms instead."* The
project log for Phase 3.2b adds: *"Every derived form is one left-edge prefix
swap away from an attested form."*

| Their view | Mine | What in the measurements decides it |
|---|---|---|
| Withdraw the accent rules | **Agree** | 57 accents where the page has none; 637 forms right without the rules against 611 with them; the file's own check at 0 of 26. They said the rules were unchecked; they are now checked, and they do harm |
| Leave from-scratch conjugation paused | **Agree, and go further: withdraw it** | "Paused" keeps 2,600 lines alive that nothing calls. The dictionary figure did not move in eleven days of fitting (14.8% before, 14.8% now), which shows the fitting taught the engine seven verbs and nothing about the language. And its seven verbs are not set up from their dictionary entries, so there is no path from here to "any verb a learner looks up" |
| **Extend** person derivation | **Differ: repair it first, and do not extend it** | Three of its rules are built on misread forms and fail on 94% of the unseen verbs they apply to. Its "I" for descriptive verbs follows a passive verb. About 13,000 of its forms cannot be checked against anything. "One prefix swap away from an attested form" is true of how a form is made and says nothing about whether it is right: *riirit* is one swap from *tiirit*, and the dictionary shows *raa-* |
| The idea behind it, start from attested forms | **Agree, and it is the main result** | The rules of person derivation that were read from correct forms hold on 97% of unseen verbs, where the from-scratch engine holds on 15%. Their approach was right; three of its rules were not |
| "The sentence templates still write Blue Book forms without their printed accents" | **Agree; it is worse than that** | Three of its words are OCR slips given meanings of their own, and it can no longer recognise the book's sentences |
| One rule of the possession engine was built on two misread words, and was removed | **The engine's main output is built on a misread word** | *kti*, on 1,671 of 1,706 nouns, marked attested |
| "None of it is on the public site, so nothing wrong is in front of learners" | **True of the engines; not of the lesson pages** | 65 OCR slips on 14 public lesson pages, from the same OCR text the engines were built on |
| (not raised) | The "Prediction" badge, the stored tables, the guide's table of prefixes | Stage 1 |

Where I agree with them I have tried to say what in the measurements
supports it. One thing they could not have known: the audit corrected the
data and stopped at the edge of the code, so every engine went on running on
the forms the data no longer has.

---

## 9. Found on the way: not engines, but they should not wait

1. **OCR slips on the public lesson pages.** The audit corrected 104
   readings in the Blue Book table as OCR slips. 65 of the old readings still
   stand in the lessons' running text and are on 14 public lesson pages
   (*Stiks .atku!*, *KIRIKJ RA•TARAWIS?*, *kti•ratiru paks-ktiku'*). The
   corrections exist; they were applied only where a whole line matched.
   **I would do this before anything else in this paper.** Small. It changes
   the `lessons` table and `docs/`, so it needs your word and a rebuild of
   the site.
2. **The local app hides 84% of Parks's example sentences.** A filter
   written for Blue Book sentences is applied to the dictionary's own
   examples: 2,652 printed, 428 shown; 1,340 of 1,658 entries show none. The
   public site shows them all. Small to fix: do not filter an entry's own
   examples.
3. **`function_words` holds four non-words** marked as attested (section 7).
4. **The gold file of Parks's worked examples** used by the word-construction
   analysis has eight mis-paired items of 93. It should be made again.
5. **Two statements in the documentation are not so.** Nothing reads
   Appendix 2: the empty cell of *tir* is not "read by the conjugation
   engine". And the Appendix 1 table is shown on no entry page, because the
   column it is found by holds two forms that are not headwords.

---

## What I need from you

Eight decisions. My recommendation is first in each. Answer with the numbers
and letters, for example "1a 2a 3a 4a 5b 6a 7a 8a", or in your own words.

| # | Decision | Choices |
|---|---|---|
| 1 | Public lesson pages: apply the audit's OCR corrections to the lessons' running text and rebuild the site | **a** yes, first · b not now |
| 2 | Conjugation engine and accent rules | **a** withdraw both to `archived/` · b keep as local tools |
| 3 | The guide's table "Parks's own tables", and the two tables behind it | **a** take it from the tables as printed, then drop `morpheme_inventory` and `verb_template_slots` · b leave it, and correct the sentence above it |
| 4 | Sound changes | **a** keep the rules as reference, replace the test by the honest measure, say it is not an engine · b leave as it is |
| 5 | Form 2 prediction | **a** keep as a checker; remove the badge and empty the score · b keep the badge, compute the score again |
| 6 | Person derivation | **a** the narrow repair of section 5, measured on a sealed half · b withdraw it; the builder offers attested forms only · c keep as it is |
| 7 | Noun possession | **a** replace by a lookup of printed forms; drop the two computed tables · b withdraw the box · c repair the generator |
| 8 | Sentence templates | **a** repair by copying, with the check · b rebuild as a reader of the book's own sentences · c withdraw |

In every case the example filter (section 9, item 2) and the four non-words
in `function_words` would be fixed with decision 7 or 8, unless you say
otherwise.

If you choose the recommended line throughout, the order I would work in is
1, then 2 and 3, 5, 4, 7, 6, 8: the withdrawals first, because they are
small and remove the most wrong output; the repairs last, because they need
the sealed test. The whole is two to three working sessions. I will not
start any of it before you answer, and I will not commit or push unless you
ask.
