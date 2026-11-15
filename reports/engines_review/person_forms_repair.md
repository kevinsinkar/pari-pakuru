# The repair of person derivation, and its test on a sealed half

Decision 6 of the engines review, carried out on 2026-11-14. The owner chose
"the narrow repair of section 5, measured on a sealed half"
([decision.md](decision.md)). This is the record: what was fixed beforehand,
what was done, and what the one opening of the sealed half showed.

**Result in one line.** On 1,059 verbs the repair never saw, the question form
it gives for "he/she" starts as the dictionary's own form 4 starts for 794 of
the 816 verbs it gives a form for: **97.3%**. The bar was 97%. It gives no
form for 243 verbs (23%). Before the repair, over all verbs: 76%.

## What the test is

The same test as in Stage 2. The engine makes the question form for "he/she"
(the absolutive) from the printed form 2. The dictionary prints, as form 4, a
form that begins with *irii-* followed by the same prefix. For every verb that
prints one form 2 and one form 4 of that shape (2,124 verbs), the start of
what the engine gives is compared with the start of form 4: the letters the
engine changed and the two after them. "Agrees" means the same letters; a
difference in vowel length or a glottal stop counts as a miss.

## What was fixed before anything was changed

| When | What | Where |
|---|---|---|
| before `person_forms.py` was touched | The split: the last digit of the number that ends the entry's id. Odd, the open half (1,065 verbs); even, the sealed half (1,059). With it, the hash of the engine file as it then was, and what was already known of the sealed half | `data/person_forms_split.json` |
| before the sealed half was opened | The two configurations to be measured, what each scored on the open half, the bar, and the rule for which one ships | `data/person_forms_plan.json` |

**What was already known of the sealed half, said plainly.** Stage 2 had
measured the old engine on all 2,124 verbs before there was a split, so its
counts by rule over both halves were known; the decision to take out three
rules rests on them. Rows of single verbs had been printed as examples. The
record of the working session was searched: 39 sealed verbs (and 40 open
ones) occur in it by entry id or by form 4. They are counted in the result
and also reported apart. Between the split and the opening no row of the
sealed half was looked at, and no rule was read from it.

## What the open half showed

The old engine, on the open half: a form for 995 of 1,065 verbs, 746 agree
(75.0%).

| Rule (start of form 2 → start of the question form) | Open verbs | Agree |
|---|---|---|
| *ti-* → *ra-* | 470 | 464 (98.7%) |
| *tih-*, headword in *h-*: *ti-* → *ra-* | 87 | 86 (98.9%) |
| *tu-* → *ru-* | 166 | 157 (94.6%) |
| *tiʔ-* → *raʔ-* | 29 | 25 (86.2%) |
| *tii-* → *rii-* (built on the OCR slip *Ka rii hitu'?*) | 184 | 14 |
| *tuu-* → *ru-* for *uur-* verbs (built on a misread cell) | 57 | 0 |
| *tih-* → *riih-* (built on a misread cell) | 2 | 0 |

**Rules looked for.** The paper allowed a new rule for the verbs of the three
removed rules if it held for 97% of the open verbs it covers. For each start
of form 2 and each of five features fixed beforehand (all verbs; first letter
of the headword; preverb; class; next letter of form 2), the substitution
that agrees with form 4 most often was computed.

- ***tii-* (184 open verbs): no rule.** The best substitution, *tii-* →
  *raa-*, holds for 137 (74.5%); split by the first letter of the headword,
  88.8% (*a*), 77.8% (*i*) and 88.9% (*u*). These verbs get no form.
- ***tih-* with a headword not in *h-*: no rule.** Two open verbs, both with
  *rih-* in form 4. Two verbs are not a rule.
- ***uur-* verbs** fall under *tu-* → *ru-* once their own rule is gone, and
  agree with it: that rule then covers 223 open verbs, 211 agree (94.6%).
- Two single slices reached 97% (*tuu-* with a headword in *i-*, 24 of 24;
  *tu-* before a consonant in class VI, 25 of 25). They are two of some sixty
  slices looked at and were **not** taken as rules.

## The two configurations

*tu-* → *ru-* and *tiʔ-* → *raʔ-* were not on the paper's list of rules to
remove, yet on the open half neither reached 97% by itself. So two
configurations were written down before the opening, to be measured in the
same run:

- **narrow**: the repair as the paper lists it. The three misread rules out,
  their verbs without a form; the four other rules kept.
- **strict**: only the rules that reach 97% on the open half with twenty or
  more verbs: *ti-* → *ra-* and its *h-* variant.

The rule for which ships, also written beforehand: narrow, if it reaches the
bar on the sealed half, because it is what was chosen and gives more forms;
otherwise strict. Nothing else to be changed after the opening.

## The sealed half, opened once

| | narrow | strict |
|---|---|---|
| Verbs | 1,059 | 1,059 |
| A form is given for | 816 (77%) | 572 (54%) |
| No form | 243 (23%) | 487 (46%) |
| Starts as form 4 starts | **794 (97.3%)** | 562 (98.3%) |
| The same, without the 39 verbs displayed before the split | 773 of 784 (98.6%) | 554 of 560 (98.9%) |
| Open half, for comparison | 786 of 809 (97.2%) | 550 of 557 (98.7%) |
| Bar of 97% | reached | reached |

By rule, narrow, sealed half:

| Rule | Verbs | Agree |
|---|---|---|
| *ti-* → *ra-* | 469 | 461 (98.3%) |
| *tu-* → *ru-* | 225 | 220 (97.8%) |
| *tih-*, headword in *h-* | 103 | 101 (98.1%) |
| *tiʔ-* → *raʔ-* | 19 | **12 (63.2%)** |
| no rule (*tii-* 168, *ta-* 65, *ru-* 7, *tih-* other 2, *ku-* 1) | 243 | no form |

**Narrow ships**, by the rule written beforehand. `POLICY = "narrow"` in
`scripts/person_forms.py`.

## What you should know before trusting it

1. **It passed narrowly.** 97.3% against a bar of 97%, on 816 forms: 22
   misses. Two more misses would have put it under.
2. **One rule is weak, and it is your call.** *tiʔ-* → *raʔ-* agreed for 25
   of 29 open verbs and 12 of 19 sealed ones: 37 of 48 together. I did not
   switch it off after the opening, because the plan said nothing would be
   changed then, and a rule dropped because of the sealed half is no longer
   tested by it. Part of its misses may be the test's: Appendix 1 prints the
   question form *raʔat* beside a form 4 with *raa-* for 'to go', the same
   kind of verb. To switch it off, set its "narrow" column to `False` in
   `THIRD_PERSON_RULES`; 48 verbs would then get no form.
3. **The test covers one form.** Only the "he/she" question form has an
   unseen witness. The "you" forms and the question forms for "I" and "you"
   follow Appendix 1's seven verbs (26 of 26 cells the engine answers, two it
   declines) and can be checked against nothing else in the sources. They are
   labelled "derived; not checked against a printed form".
4. **Agreement with form 4 is not a speaker's judgement.** Form 4 is the
   gerundial, not the question form itself. Where Appendix 1 prints both, they
   start alike for five verbs of seven and differ by a glottal stop for two.
5. **No accent.** The rules work on forms without their accents, so a derived
   form never carries one.

## What else the repair changed

- No "I" form is made up for descriptive verbs that print none (it was *tiku*
  + stem, for 184 verbs). Where an entry prints no form 1, no first or second
  person is given.
- The present and future of "I" and "you" are no longer made. No source
  prints such a paradigm.
- `--validate-appendix` now fails on any mismatch: 26 passed, 0 failed, 2
  declined (*raʔaʔ* 'he came', *rihkiraawaʔ* 'he is sick').
- The sentence builder passes the entry, not the spelling, and shows the
  label beside every derived form (done with decision 8).

## To check this record

```bash
python scripts/person_forms.py --validate-appendix                  # 26 passed, 0 failed, 2 skipped
python scripts/engines_review/person_forms_repair.py --open         # the open half, both configurations
```

`--sealed` refuses to run again: the result is
`data/person_forms_sealed_result.json`, with the hash of the engine file as it
was when the half was opened.
