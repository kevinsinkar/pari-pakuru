# Method: how the v2 word-construction analysis was made

This file says what was done, how to run it again, and what the tiers mean.
`PLAN.md` records what was planned and locked in advance. Numbers are in
`stats.json`, `coverage.json` and `validation_report.md`.

## Reproduce everything

From the repository root, with `.venv/Scripts/python`:

```
python scripts/morphology_v2/run.py --all            # data, guides, validation report
python scripts/morphology_v2/check_forms.py          # every Pawnee form resolves to a source
python scripts/morphology_v2/check_determinism.py    # two runs, byte-identical outputs
python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"
python scripts/morphology_v2/gold_build.py --verify  # gold files match their recorded hashes
python scripts/morphology_v2/apply_data_fixes.py     # list proposed data fixes (dry run)
```

The database is opened read-only. Nothing outside `curriculum/roots_v2/` is
written. The gold sample can be redrawn with
`python scripts/morphology_v2/gold_sample.py --check`; the page transcriptions
in `gold/g2_raw/` were made by hand from the page images and are not
regenerated.

## What the pipeline does, in order

| Step | Module | What it does |
|---|---|---|
| 1 | `lexemes.py` | Loads every dictionary row and groups duplicate rows into lexemes. Rows that share a headword are merged only when class, verb class, preverb and paradigm (or, without a paradigm, etymology and gloss) show they are one record. |
| 2 | `etymology.py` | Re-parses Parks's printed etymology into pieces and aligns his literal translation with them. Grammatical labels are anchored on the piece that carries that label most often across the dictionary, not on position. |
| 3 | `analysis.py` | Decides which pieces are grammatical, clusters each form's glosses into senses, resolves dotted compound stems to their own entries, and runs the evidence channels. |
| 4 | `seams.py` | The seam engine: every surface form the named rules allow for a list of pieces. |
| 5 | `tiers.py` | Assigns the tier from the evidence record. |
| 6 | `inventory.py` | Builds the morpheme inventory, the decision records and the frequency measures. |
| 7 | `ordering.py` | Derives the learning order and tests its sensitivity to the weights. |
| 8 | `guide.py` | Writes the three learner documents from tier A/B data. |
| 9 | `report.py`, `validate.py` | Scores the gold sets and writes the validation report, the changelog and the proposed data fixes. |

## The evidence channels

**E1, Parks's printed analysis.** Read from `etymology.raw_etymology`. The
stored `constituent_elements` are used only to cross-check the piece forms:
their per-piece glosses come from an earlier automatic parse and mis-align
(`as+hur+uʔ` 'foot place + NOM' is stored as *as* = "foot place").

A word with no printed analysis still counts as analysed when Parks cites its
headword as a single piece, with a compatible gloss, in other words'
etymologies (**E1 by citation**). That is how basic roots such as 'go' enter:
Parks prints no etymology for them because they are unanalysable.

**E2, round trip.** The pieces are joined by the seam engine and compared with
the headword.

- *Exact*: the headword is produced by plain concatenation or by named rules,
  using at most two optional rules. Every rule used is recorded.
- *Partial*: a produced form matches only when vowel length, ʔ and h are
  ignored, or needs three or more optional rules, or the pieces can only be
  located one at a time.
- *Fail*: neither.

The rules are Parks's numbered rules, the five rules the Blue Book states in
Lesson 3 ("Combining roots", pp. 41-42), and six regularities measured in the
data and marked as such (`affixes.json`, key `seam_rules`). Rules apply only at
morpheme boundaries and word edges, never inside a piece. Word-edge rules apply
only to free words, not to verb stems or bound forms. No rule changes vowel
length except shortening before h + consonant.

**E3, paradigms.** Two checks on verbs that have the five dictionary forms:

- *E3a*: the existing stem extractor predicts form 2 from headword, verb class
  and preverb, and the prediction equals the attested form.
- *E3b*: a compound ends each of its forms the way its final root's own
  dictionary entry does (aspect endings of forms 3 and 5, subordinate ending of
  form 4), allowing for the junction sound at the start of the root. The check
  is made only when the two share an inflection class.

E3 confirms a single-piece analysis by E3a, and a multi-piece analysis by E3a
and E3b together. An outright difference in an aspect ending contradicts.

**E4, recurrence.** Every lexical piece has a meaning that was checked in this
word (see "Meanings" below) and that meaning is found, checked, in at least two
other words whose analyses reproduce exactly, or the piece has its own
dictionary entry. Every grammatical piece carries a label Parks prints at
least three times for that form, or a label fixed by a cited decision.

**E5, Blue Book seams.** A Blue Book word written with seams (`•`) is matched to
a Parks form only when its skeleton equals exactly one Parks form and the
English agrees. A seam on a boundary of the analysis confirms; seams that never
fall on a boundary contradict. The stored `blue_book_attestations.match_type`
links are not used for this.

**E6, grammar.** The affix is in Parks's tables or worked examples, or Parks
labels the piece in his etymologies. Used inside E4.

**E7, cognates.** Recorded per word, never used for a tier.

## Tiers

| Tier | Rule |
|---|---|
| **A** | Parks's analysis (printed or by citation), exact round trip, confirmed by E3 or E5, nothing contradicting |
| **B** | Nothing contradicting, and either an exact round trip with E4, or a partial round trip confirmed by E3 or E5 |
| **C** | Parks's analysis alone; conflicting channels; an analysis not in Parks that has some support |
| **D** | Hypothesis only |
| none | No printed analysis, no citation, no proposal: no claim is made |

The rules are in `tiers.py` and are unit-tested. A tier is never set by hand.
Learner documents use tiers A and B only.

**Morpheme tiers** follow the same idea one level up. A lexical morpheme is
tier A when Parks prints its meaning (in an aligned gloss or as a dictionary
entry) and it builds at least three tier A/B words, one of them tier A; tier B
when it builds at least two; tier C otherwise. An affix is tier A when Parks
prints its label at least three times and it is in at least three tier A/B
words; tier B when the label is printed at least once or fixed by a cited
decision and it is in at least two.

## Meanings: how a piece gets one

Parks's literal translation rarely glosses each piece separately: `<kaa+at, go
inside>` does not say which word goes with which piece. So:

1. **Senses.** For each form, the glosses Parks does attach to it are
   collected: glosses aligned with the piece alone, the definitions of the
   form's own dictionary entries, and the gloss of a noun that is just the root
   plus the noun suffix. Glosses that share a content word are one sense;
   groups that share none are separate senses. That is how homonyms are found,
   for every form, not for a hand-picked few.
2. **Assignment.** A piece in a given word is assigned to a sense when Parks
   glosses it there (*aligned*), or when the literal translation of the word
   shares a content word with exactly one sense of the form (*literal*), or, for
   a piece inside a dotted compound stem, when the stem's own dictionary entry
   assigns it (*inherited*).
3. **What does not count.** If the form has only one known sense and the
   literal translation does not mention it, the assignment is recorded as
   `default_single_sense` and is **not** evidence. On the gold set this
   fallback was wrong every time the page allowed a check, which is why it is
   excluded. Two further guards: a function word such as "on" or "in" is
   evidence only when Parks's own gloss for the piece is just that word; and one
   word of a literal translation cannot vouch for two pieces of the same word.
4. **Commutation.** Some pieces are never glossed alone: Parks writes "big
   buck", "large tooth", never "big" by itself. Where a word has two roots and
   one already has an established meaning that accounts for part of the literal
   translation, the remainder is what the other root contributes. A sense is
   accepted on this basis only when at least three words agree.
5. **Naming.** A sense is named after the gloss that fits the largest number of
   the words it was assigned in. The other glosses Parks uses are kept with it.

**Dotted compound stems.** In `<pirus+as.i, ...>` the unit `as.i` is a stem with
its own dictionary entry ('run'), not 'foot' plus something. Each dotted unit
is matched to a headword; its inner pieces take role and sense from that
entry's analysis.

## Decisions are data

`scripts/morphology_v2/decisions_manual.json` holds every decision made by
hand, each with its source. There are six kinds:

- `role_default`: an unlabelled stem element is an affix (plural/iterative,
  portative, distributive, locative formative, aspect suffixes, causatives);
- `sense_anchor`: the three kinship possessive prefixes;
- `sense_merge`: two glosses are one sense, where Parks uses both for the same
  thing;
- `label_merge`: two of Parks's labels name one affix;
- `label_anchor`: a form carries a label that position alone would misplace;
- `ignore_anchor`: one gloss that would wrongly join two separate entries.

Several of these were added after the adversarial pass and the blind
re-derivation; each says so in its evidence. `decisions.json` (output) holds
those plus every automatic
decision: duplicate rows, role defaults from label statistics, every homonym
split with its glosses, and every variant candidate. Changing a decision means
editing the manual file and re-running.

**Variants are not merged.** Two shapes that differ only in vowel length, ʔ or
h and share a meaning word are listed as candidates with their counts shown
separately and combined. The only variants treated as one morpheme are those
Parks writes himself with an optional segment in parentheses.

## Frequency measures

All in `roots.json` and `affixes.json`, per morpheme:

- `type_frequency`: distinct lexemes, for tier A, A+B and A+B+C.
- `direct_vs_nested`: words built directly, and words where the morpheme sits
  inside a compound stem.
- `productivity`: distinct partner morphemes, and the share of formations whose
  partners occur with it only once.
- `token_frequency`: example sentences attached to its tier A/B words, with a
  95% interval. The corpus is small.
- `blue_book`: first lesson in which one of its words is reliably attested.
- `transparency`: share of its exactly reproduced words that join with no
  rule, and which rules apply in the rest.
- `chance_baseline` (forms of one or two segments): how many headwords contain
  the string against how many analyses place it.

## Coverage and learning order

A word can be taken apart completely when its analysis is tier A or B and every
piece has an inventory key: a sense assigned on evidence, or a labelled affix.
`coverage.json` gives, after each morpheme in the order, the share of
dictionary lexemes, of reliably linked Blue Book words and of example sentences
that can be taken apart completely, and the number of words with at least one
known piece. The order itself, the weights and the sensitivity test are
described at the top of `learning_path.md` and implemented in `ordering.py`.

## Limits to keep in mind

- **Precision on the gold set is high but the gold set is small.** The interval
  for tier A on the held-out half has a lower bound well below the point
  estimate. See `validation_report.md`.
- **The gold set checks the analysis against the printed page.** It shows that
  the extraction and this pipeline report Parks faithfully. It cannot show that
  Parks's analysis is right; the paradigm and Blue Book channels speak to that.
- **Nouns can reach tier A only through the Blue Book**, because they have no
  paradigms. Most analysed nouns are tier B or C.
- **Vowel length.** Many printed analyses differ from the headword in vowel
  length where no rule applies. They are kept out of the learner documents
  unless independently confirmed, and listed for review.
- **Affix defaults.** Several stem formatives are labelled by a cited decision
  where Parks prints no label on the word. The adversarial section of the
  validation report gives the printed-against-default counts for each.
- **The community-review flag is a keyword match** on glosses and semantic
  tags. It will miss some words and flag others needlessly.
- **Token frequency is weak.** It counts example sentences attached to an
  entry, not occurrences in running text.
