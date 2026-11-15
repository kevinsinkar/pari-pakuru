# Engines review, Stage 4: what was done

*2026-11-14. The owner answered the decision paper with "1a 2a 3a 4a 5a 6a 7a
8a": the recommended choice for each of the eight decisions. This is the
record of carrying them out, in the order 1, 2 and 3, 5, 4, 7, 6, 8. Nothing
was committed or pushed.*

## In short

| # | Decision | Done | The figure that matters |
|---|---|---|---|
| 1 | The audit's corrections in the lessons' text | yes | 214 places in 17 lessons and 12 titles; 196 places left where only an accent differs |
| 2 | Conjugation engine and accent rules | withdrawn to `archived/scripts/` | nothing called them |
| 3 | The guide's "Parks's own tables" | printed from the tables as read from the page; the two engine tables dropped | 412 cells, each checked against the file |
| 4 | Sound changes | kept as reference; the self-test replaced by the honest measure | 8 of Parks's 39 examples |
| 5 | Form 2 prediction | kept as a checker; badge removed, 2,239 scores emptied | 87.2%, on seen forms only |
| 6 | Person derivation | repaired narrowly and tested on a sealed half | **97.3%** of 816 forms on 1,059 unseen verbs; bar 97% |
| 7 | Noun possession | replaced by a lookup of printed forms | 734 of 1,706 nouns have something printed; nothing is computed |
| 8 | Sentence templates | rebuilt on printed rows, with the check | 38 tests; the check passes at zero exceptions |

The public site changes in one respect only: the 20 lesson pages. It changes
for readers when this is committed and pushed.

## Where the paper was wrong, found while doing the work

1. **The paper counted 65 OCR slips in the lessons. There were 214.** The
   audit filed its corrections under four labels and the paper counted one
   ("OCR slip corrected"). Old readings with wrong letters also stood under
   the others (*Nawa niru!* for *Nawa rúru!*, *to taxis* for *tá taris*). A
   leftover *kti* on the rebuilt page of lesson 7 gave it away. The script now
   takes every correction of the audit.
2. **The lesson titles held the same errors**, and worse: an earlier script
   had "repaired" *KIRIKJ* to *KIRIKI* by rule, where the scan reads
   *KIRIKÉ*, and *TAR1* to *TARI*, where it reads *TAKÉ*.
3. **`function_words` holds more than four non-words.** The four named in
   the paper were removed. Nine more of its Blue Book rows are found nowhere
   in the scan's readings (*pihkawf*, *rd*, *wfs*, *sihukstarti*, *niru*,
   *hti*, *cararat*, *ʔhr*, *rahesa*), and 18 are parts of words. Left as
   they are: not among the decisions.
4. **On the open half, two rules the paper kept did not reach 97% by
   themselves** (*tu-* → *ru-* 94.6%, *tiʔ-* → *raʔ-* 86.2%). Section 6
   below says what was done about that before the sealed half was opened.

## 1. The lessons' text

`scripts/fix_lesson_text_ocr.py` (lists by default; `--apply` backs up, writes,
appends to `reports/lesson_text_ocr_report.txt`, writes the dump; `--check`).

- **Running text:** every correction of the audit's report, the latest reading
  of a form winning, where the old reading stands in a lesson's text on a page
  the audit read it on and differs from the reading inside the form in
  letters, spacing, a bullet or punctuation. Three runs: 65 places, then 145,
  then 4 that stood at the very end of a text and that a fault in the script's
  own guard had skipped (found by scanning the built pages). **214 places in
  17 lessons.**
- **Titles:** 12 set to the Blue Book table's reading of the title line.
- `extracted_data/lessons.json` is now a true copy of the table (before the
  first run it differed in 23 values, seven of them titles).
- `docs/` rebuilt; `check_static_site.js` 13 of 13; no reading the audit
  corrected in its letters is left on a public lesson page.

**Left, on purpose:**

- 196 places where the audit's reading differs only by an accent or a capital.
  The OCR dropped every accent; the audit read a form at one place; the same
  letters may be printed elsewhere on the page without the accent. Changing
  them all would be a guess. The page settles it.
- Two old readings on a page the audit did not read them on (*hitu '* in
  lesson 4, *ti .ra* in lesson 13).
- Seven titles the table has no reading of: lessons 6 (none stored), 8
  (*KI Rid RA. KU?*), 9, 10, 12, 17, 18. Lessons 10 and 18 show *KIRIKI*.
- OCR damage that matches no reading of the audit exactly: lesson 20
  *tatitska ratkti u•ta*, lesson 13 *kit-kaharu '*, lesson 2 *tskau*.
- The title of lesson 16 is now *KITSKÉ WE RU'*, as the table reads the
  title line, without the question mark the contents page of the OCR text
  has.

## 2. Conjugation engine and accent rules

`scripts/morpheme_inventory.py` and `scripts/accent_rules.py` moved to
`archived/scripts/`, each with a note at its head. Nothing in `web/` imported
them. The dashboard's block "Grammar Engine" became "Reference Tables" and
counts only what is copied (Appendix 1 forms, sound-change rules, Appendix 3
kin terms).

## 3. The guide's table

The section "The prefixes and endings Parks tabulates" of
`curriculum/roots_v2/construction_guide.md` was built from the table
`morpheme_inventory`: the engine's arrangement, six rows of it pieces Parks
does not print (*kaaka-* for his *kaakaa-*), under a sentence saying these
were his own tables.

- It now prints **Parks's Tables 6 to 17 row by row** from
  `extracted_data/grammatical_overview_tables.json`, with the page and
  whether the two readings agree; Tables 6 and 7 in both readings.
- A second list, "The pieces Parks labels in his worked examples": 69 pieces
  with a count and an example. A piece is not matched to a table row by its
  letters. A worked example whose stored word is not the word its pieces make
  (the gold file has eight such records) still counts, but is not shown as the
  example.
- `scripts/morphology_v2/` no longer reads the database table.
  `check_forms.py` checks every table cell against the file: 412 cells.
  Unit tests 34 of 34, gold sets unchanged, two runs byte-identical.
- Then `morpheme_inventory` (37 rows) and `verb_template_slots` (27) were
  dropped.

## 4. Sound changes

`scripts/sound_changes.py` stays where it is; the word-construction analysis
reads single rules from it. The table `sound_change_rules` is kept and is
identical to the file's catalogue (`--check-table`).

- The file says at its head that it is a reference, not an engine.
- `--test` (11 forms, 7 of them the code's own output) is gone. `--measure`
  compares the code with every example Parks prints in chapter 3: **8 of 39**.
- Run without options, the file used to rewrite the table. It now does
  nothing, and writes the table only with `--write-table`, after a backup.
- No rule function changed (compared function by function).

## 5. Form 2 prediction

- The badge "Prediction: High / Med / Low" is gone from entry pages and
  result cards; the score is no longer read, returned by the search API or
  used to order new study cards.
- `predict_form_2` and `--validate` stay (1,915 of 2,197, on the forms the
  rules were read from). The code that computed and stored the score is
  removed. The file says at its head that it is a checker.
- 2,239 stored scores set to NULL. The column stays, empty.
- `scripts/anki_export.py` (unused) showed a printed form 2 only above a score
  of 0.75; it now shows the printed form wherever one is printed.

## 6. Person derivation

The full record, with the split, the plan and the result:
[person_forms_repair.md](person_forms_repair.md).

- Before the file was touched: the split written down (odd entry numbers
  open, even sealed), with what was already known of the sealed half.
- On the open half the three rules built on misread forms agreed for 14 of
  243 verbs. Removed. No rule for their verbs reached 97% there, so those
  verbs get no form.
- No "I" form is invented for descriptive verbs; no present or future for "I"
  and "you"; `--validate-appendix` fails on any mismatch (26 passed, 0
  failed, 2 declined).
- Because two kept rules were under 97% on the open half, two configurations
  were fixed before the opening, with the rule for which ships. **The sealed
  half, opened once: the repair as the paper lists it gives a form for 816 of
  1,059 verbs, and 794 start as the dictionary's form 4 starts: 97.3%.** It
  ships. The stricter one: 562 of 572.
- **Weak point, yours to decide:** *tiʔ-* → *raʔ-* agreed for 12 of 19 sealed
  verbs (25 of 29 open). One line switches it off.
- The builder passes the entry, not the spelling, and labels every derived
  form (with decision 8).

## 7. Noun possession

- `scripts/printed_noun_forms.py` looks up, for a noun, what is printed: the
  Appendix 3 row of a kin term; the one-word examples of the entry that end in
  *-kat*, *-hiriʔ* or *-ru*, with Parks's translation; the combining forms;
  Blue Book words tied to the entry by the exact form whose English begins
  with "my", "your", "his", "her". Each with its source. Nothing is computed.
- Of 1,706 noun entries, **734 have something printed**: 38 Appendix 3 rows
  on 37 entries, 680 forms with a case ending on 610, 537 combining forms on
  408, 15 Blue Book forms on 13. The other 972 pages say that nothing is
  printed.
- An Appendix 3 row is tied to an entry by the printed form, or, for the
  bound stems (*-saas-* 'mother'), by the relation the row is listed under;
  the page says which, and that the second says nothing of how the forms are
  built.
- Removed: `/api/possession`, the widget and its styles,
  `extracted_data/noun_possession_catalog.json`. `possession_engine.py` and
  `noun_possession.py` moved to `archived/scripts/`.
- **Parks's own examples are no longer filtered on entry pages** (428 of
  2,652 were shown). The Blue Book filter stays; taking the engine's stem out
  of it changes none of 262 rows.
- Database: `possession_examples` (20 rows) and `noun_stems` (49) dropped;
  three rows of `kinship_paradigms` not from Appendix 3 deleted; four OCR
  slips deleted from `function_words` (*ilanʔ*, *kirti*, *kti*, *stiks*).

## 8. Sentence templates

`scripts/sentence_templates.py` and `scripts/template_slot_fillers.py` are
rebuilt; `web/templates/sentence_builder.html` with them.

1. **Every Blue Book form comes from a row.** A pattern starts from a
   sentence the Blue Book prints: 13 frames for the ten patterns, each named
   by the number and the text of its row. A word may be swapped only for
   another printed word, given by its row. Neither file has a Pawnee word
   typed in it in any other way; the three non-words went with the typed
   lists.
2. **A sentence says what it is:** "printed in the Blue Book, lesson N" only
   when it is, accents included, a form of the table; otherwise "put together
   here; not printed".
3. **"The stick is red"** takes the quality as a phrase the book lists. In
   the dictionary's spelling it is the entry's printed form 2 (*rakis
   tipahaaʔat*), and is offered only where one is printed. The earlier engine
   wrote *ti* and the stem.
4. **One spelling per sentence, and the entry for a verb.** Dictionary verbs
   are a separate part, in Parks's spelling, chosen by entry id. Their forms
   are shown as printed, or as "derived; not checked against a printed form".
   The earlier builder added a spelling-based pronunciation to each sentence;
   it no longer does.

**The check** (`--check`): every form named in the two files is what its row
or entry holds, and no Pawnee form stands outside those declarations: zero
exceptions. **The tests** (`--test`): 38 of 38, every expected form read from
a row.

## What was removed from the database

`scripts/remove_engine_output.py`, one decision at a time; a backup before
each; `reports/engines_review/stage4_database_report.txt`.

| | Before | After |
|---|---|---|
| Tables in the text dump | 25 | 21 |
| Rows | 46,553 | 46,413 |
| `morpheme_inventory`, `verb_template_slots`, `possession_examples`, `noun_stems` | 37, 27, 20, 49 rows | dropped |
| `kinship_paradigms` | 14 | 11, all Appendix 3 |
| `function_words` | 418 | 414 |
| `lexical_entries.form2_confidence` | 2,239 values | empty |
| `lessons` | | text and titles corrected |

Backups, in `OneDrive/pari_pakuru_backups/`: the database as the review found
it (`…_160246_engines_review_stage0.db`), and one before each change
(`…_lesson_text.db` three times, `…_engines_decision3.db`, `…5.db`,
`…7.db`). The removed tables are also in git history: `DB/dump/` at commit
`814e8cc`.

## Checked at the end

Every check of the top-level README was run again: all pass, and the README's
tables give the results. The local app answers on 47 addresses and gives "not
found" for the two withdrawn routes. Every file of the repository was hashed
at the end of Stage 3 and again at the end of Stage 4; the files that differ
are the ones named in this record and the documentation.

One slip of my own, put right: a test run of
`scripts/source_audit/alphabet_check.py` wrote over the audit's record
`alphabet_check.json`. It was restored from git, byte for byte.

## The review's own measurements can no longer be re-run in place

Stages 1 and 2 measured nine engine files as they stood in commit `814e8cc`.
Four are now in `archived/` and five are changed. The measurement scripts
therefore refuse to run and say why, so that the record in `data/` is not
written over with figures about other code.
[../../scripts/engines_review/README.md](../../scripts/engines_review/README.md)
says how to make the record again.

## Still open, and not mine to decide

1. **Commit and push.** The lesson pages are corrected on this machine only.
2. **The 196 accents and seven titles of the lessons** need the page. Reading
   the seven title lines from the scan would take about ten thousand tokens;
   the 196 places, the notes of all twenty lessons, more like a hundred and
   fifty thousand. Say if you want either.
3. **The *tiʔ-* rule** of person derivation: keep, or switch off.
4. **`function_words` and `bb_function_words`** need their own pass against
   `blue_book_attestations`.
5. **The Blue Book table ties common words to the wrong entry.** *asáki*
   'dog' and *arúsa* 'horse' are tied to the entry *a*, *tsapat* 'woman' to
   *ca*, by a shared beginning: 77 single listed words are tied that way to
   a locative verb, and 99 are tied to nothing. The entry page of *a* lists
   them. The lookup and the builder use only ties by the exact form.
6. **The gold file of Parks's worked examples** still has its eight
   mis-paired records.
7. **The Blue Book filter on entry pages** does not set accents aside, so
   since the audit restored them it may hide sentences that do hold the
   headword (it keeps 54 of 262).
8. Whether any made form should ever be shown to learners is for the Pawnee
   community, as before.
