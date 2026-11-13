# Prompt: Source-fidelity audit of the Skiri Pawnee database, run in stages

Paste everything below the line into a fresh session started at the root of the
`pari-pakuru` repository. It assumes the model can read files (including PNG
images), run Python, write files, and start sub-agents.

The audit is built to be interrupted. If a session ends part-way (a usage limit,
a closed laptop), start a new session with this same prompt: it reads
`reports/source_audit_2026-11/STATE.json` and carries on from the first
unfinished unit.

---

## Why this matters

Pari Pakuru is a revitalization project for Skiri (Skidi) Pawnee, a Caddoan
language with very few first-language speakers. Its database is a copy of two
printed sources: Parks & Pratt, *A Dictionary of Skiri Pawnee* (2008), and the
community textbook *Pari Pakuru'* (the "Blue Book", 1979). Learners study from
it. A copying error that is taught is hard to take back.

The copy was made by an AI model reading page PDFs in February 2026. It has
been audited three times (2026-03, 2026-09-01, 2026-10-01). On 2026-11-13 two
errors were found that all three audits had missed:

- 269 IPA forms had lost their accent mark, because the table that decodes the
  PDF's stand-in characters read `÷` as a length mark (it is ú) and `Š` as ʊ
  (it is ʊ́).
- Parks's locative suffix *-hiriʔ* was stored as *-biriʔ* in the grammar
  chapter extraction, and an engine had been built on it. No Skiri word
  contains a `b`.

Both were missed for the same two reasons. The audits **sampled**, and where
they compared two readings, **both readings shared one unverified assumption**
(the character table). Both errors were found the moment someone looked at the
page image. This audit is designed around those two lessons.

## The task

Establish, for every stored value that claims to be copied from a printed page,
whether it matches the page. Cover everything, not a sample. Produce a list of
differences, each with the evidence a person needs to approve or reject a fix.
**Apply nothing.**

## What this audit can and cannot show

It shows fidelity to the printed sources. It cannot show that a printed form is
right, that a gloss is how a speaker would put it, or that anything generated
by the project's engines is correct. It does not replace review by a speaker or
a linguist, and its report must say so.

## Design principles

1. **Full coverage.** Every entry, every field, every page. Sampling is used
   only to measure the audit itself (principle 6).
2. **Two independent readings, and the page image decides.** A stored value is
   accepted when a second reading that never saw the database agrees with it.
   When they differ, look at the image.
3. **Verify the shared assumptions first.** The PDF text layer is only an
   independent reading if its characters are decoded correctly. So the
   character table is verified exhaustively, per font and per character,
   against rendered glyphs, before any comparison depends on it.
4. **Cheap readings before expensive ones.** The text layer is free and covers
   465 of the dictionary's pages. Reading images with a model costs tokens.
   Use the model's eyes only where there is no text layer, or where two
   readings disagree, and then on a crop of the entry, not on a whole page.
5. **Nothing is applied.** The output is a list of proposed fixes with page
   evidence. A separate, reviewed step applies them.
6. **The audit is itself tested.** Plant known errors in a copy of the data and
   measure how many the comparison catches (recall). Check a random sample of
   "both readings agree" against images (residual error where they agree).
   Report both figures.

## Ground rules

- **The page is the authority, including when it looks wrong.** If the book has
  what looks like a misprint, the faithful copy has the misprint. List it under
  "printed oddities"; do not correct Parks.
- **Never fabricate a Pawnee form. Never generate IPA.** A reading you are not
  sure of is recorded as `unresolved` with the crop, not guessed.
- **Read before you look.** When you read an image to settle a difference,
  write down what you see before you look at either candidate. A sub-agent
  doing a blind reading gets the images and a transcription format and nothing
  else: not the database, not the JSON, not this repository's extracted files.
- **Same spelling is not the same thing.** Homographs with different
  grammatical classes are different entries. Never merge.
- **Blue Book forms are quoted as printed** (`ts`, `'`, the dot `•`; `?` is a
  letter in `ka?`). Never respell them into Parks's system.
- **Sacred and ceremonial vocabulary** stays flagged `needs_community_review`.
  The audit checks its fidelity like any other entry and publishes nothing new.
- **Privacy.** Send no dictionary content, names or paths to outside services.
  The `community_feedback` table holds people's names and comments: never dump
  it, quote it or commit it.
- **Scripts that could change data** default to a dry run, back up first, and
  write their report only when applied. Run nothing from `scripts/` marked
  "applied" in `scripts/README.md`.
- **Do not commit or push** unless the user asks.

## What you have to work with

Read `README.md`, the "Status at a glance" and "Open items" sections of
`pari_pakuru_project_scope.md`, and `scripts/README.md` first.

### The stored copy

| Where | What |
|---|---|
| `skiri_pawnee.db` | The working master copy. Not in git. 44 tables |
| `Dictionary Data/skiri_to_english_respelled.json`, `english_to_skiri_linked.json` | The parsed dictionary; kept in step with the database |
| `extracted_data/*.json` | Appendices, abbreviations, grammar chapter, Blue Book vocabulary and lessons, as read by an AI model from page images |

In scope are the values that claim to copy a page:

| Source | Tables and files |
|---|---|
| Skiri-to-English section | `lexical_entries` (headword, phonetic_form, grammatical_class, verb_class, stem_preverb, additional_forms, page_number), `glosses`, `paradigmatic_forms`, `examples` (Parks's), `etymology`, `cognates`, `derived_stems` |
| English-to-Skiri section | `english_index`, `cross_references` |
| Appendix 1 | `verb_paradigms` (770 forms; the conjugation engine is scored against these), `appendix1_conjugations.json` |
| Appendices 2, 3 | `irregular_verb_roots`, `kinship_paradigms`, `appendix2_irregular_roots.json`, `appendix3_kinship.json` |
| Front matter | `morpheme_abbreviations`, `abbreviations.json`, `sound_change_rules`, `grammatical_overview.json` (its Skiri forms, affixes, glosses and table cells; its prose paraphrase is not data) |
| Blue Book | `blue_book_attestations`, the 93 entries with `source = 'blue_book'`, `lessons`, `blue_book_extracted.json`, the Blue Book rows of `examples` |

Out of scope, because the project generated them: `normalized_form`,
`simplified_pronunciation`, `semantic_tags`, `form2_confidence`,
`function_words`, `morpheme_inventory`, `noun_stems`, the curriculum. Check
only that each is still in step with the value it was generated from.

### The printed sources, and the second reading each one allows

| Source | Files | Pages | Second reading available |
|---|---|---|---|
| Skiri-to-English | `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/page_NNN.pdf` | 181 | **Text layer with fonts.** Skiri is set in `PlainsArial` (headwords bold), phonetic forms in `PAdothyphen` and small `PlainsArial`, English in `TruteauGaramond` |
| English-to-Skiri | `Dictionary Data/split_pdf_pages_ENGLISH_TO_SKIRI/NNN_English to Skiri.pdf` | 284 | Text layer with fonts |
| Abbreviations and sound key | `Dictionary PDF Split/01-…pdf` | 6 | Text layer |
| Sounds and alphabet; major sound changes; grammatical overview; organization | `Dictionary PDF Split/02-…` to `05-…pdf` | 5, 9, 23, 8 | **Image only.** Chapters 3 and 4 also have an OCR text file in the same folder |
| Appendices 1, 2, 3 | `Dictionary PDF Split/Appendix N ….pdf` | 8, 1, 6 | **Image only** |
| Blue Book | `pari pakuru/Blue Book - Pari Pakuru - split/`, `Blue_Book_Pari_Pakuru.txt` | 130 | Scan with OCR text. The OCR misreads often |

Things that will trip you:

- **The text layer uses stand-in characters**, and what a character stands for
  depends on its font. `÷` in a `PlainsArial` span is ú. The table verified so
  far is in the docstring of `scripts/fix_data_2026_11.py`. It was verified on
  one image per character. Treat it as a hypothesis.
- **Parks prints no length mark.** A long vowel is two vowel letters, tense,
  with any accent on the second (aá, ií, uú); short vowels are lax (ə, ɪ, ʊ).
- **`page_number` mixes two conventions**: values up to 181 are the page file
  number, larger values are the printed book page (book page = file number +
  348). Find an entry's page by its headword, not by trusting the column.
- **Console encoding on Windows is cp1252.** Write output with
  `sys.stdout.buffer.write(text.encode("utf-8"))` or set `PYTHONIOENCODING=utf-8`.
  Do not put code with quotes or backslashes in a shell heredoc; write a file.
- PyMuPDF (`fitz`) is installed in `.venv`. Pillow and fontTools are not.
  Contact sheets can be composed with PyMuPDF alone (`show_pdf_page` with a
  clip rectangle keeps the crop as vector, sharp at any zoom).

## Checkpoints and progress reports

Everything the audit writes goes in two places:

- code: `scripts/source_audit/`
- outputs: `reports/source_audit_2026-11/`, with bulky working files (rendered
  crops, per-page intermediate files) in its `work/` sub-folder, which is not
  for git.

**State.** `reports/source_audit_2026-11/STATE.json` records, per stage:
status (`pending`, `running`, `done`), units total and done, counts of
findings by grade, the files written, and start and finish times; and, for the
whole audit, the number of images read by a model and of sub-agents started
(the only measure of cost available: a session cannot see the account's usage
limit; the user can, with `/usage`).

**Units.** Each stage works through units (a page, a table, a batch of crops)
and writes one result file per unit as it finishes. A unit whose result file
exists is skipped on a re-run. A stage is `done` only when every unit is.

**Progress log.** `progress.log` is append-only: one line per finished unit
batch, with the time.

**Heartbeat.** Tell the user where things stand at the start and end of every
stage, and inside a stage at least once per 25 units or per long-running
command: stage, units done of total, findings so far, images read so far, what
comes next. One or two lines. If a step fails, say so in the same message, with
the error.

**Status command.** `python scripts/source_audit/status.py` prints the state
table, so the user can check without asking.

**Resuming.** At the start of a session, if `STATE.json` exists, print the
status table and continue at the first stage that is not `done`. Do not redo a
finished unit unless the file it was computed from has changed.

**Before an expensive stage** (more than about 100 images to be read by a
model), state the estimate in the heartbeat before starting it.

## Grades of evidence

Every difference between the stored value and the page gets one grade:

| Grade | Meaning |
|---|---|
| `confirmed` | The page image was read, the reading is recorded, and it differs from the stored value. A crop is kept as evidence |
| `text-layer` | The text layer differs from the stored value, every character involved is `verified` in the Stage 1 table, and the difference is of a kind whose image checks have all come out the same way. Image not read for this item |
| `unresolved` | The image is unclear, or readings disagree and cannot be settled |
| `printed-oddity` | The stored value matches the page, and the page itself looks wrong |
| `noise` | Not a difference in content: line-break hyphens, spacing, a formatting convention of the parse. Each kind of noise is a named rule in code, with its count, never a silent skip |

And a severity: **1** a Pawnee form or its IPA; **2** meaning (a gloss, a
translation, a missing or extra sense, example or entry); **3** grammatical
class, verb class, cross-reference, page; **4** formatting.

## Stages

### Stage 0. Baseline

- Back up the database (`OneDrive/pari_pakuru_backups/`).
- **Put the database under version control as text.** Write
  `scripts/db_dump.py`: one file per table in `DB/dump/`, one row per line,
  sorted by primary key, UTF-8, stable formatting, so that a later fix shows as
  a small difference. Leave out `community_feedback`, the `srs_*` tables and
  the full-text index tables (rebuilt from their sources). Give it a
  `--restore` mode that builds a database from the dump and `DB/schema.sql`,
  and a `--verify` mode that proves the round trip (dump, restore, compare
  every row).
- Record the hashes of every input (database dump, both JSON files, every
  source PDF) in `baseline.json`.
- Run the existing test suites listed in `README.md` and record their results,
  so that any later change in them is visible.
- Create `STATE.json` and `status.py`.

Done when: the round trip is exact, and the baseline is written.

### Stage 1. The character table, by font

For every font in the text layer of both dictionary sections and the
abbreviations chapter, list every character outside plain ASCII letters,
digits and common punctuation, with its count. For each (font, character) pair
build a contact sheet: several occurrences from different pages, each a crop of
the printed word with the character's box marked, labelled with an id only.
Read the sheets. Record in `character_table.json`, per pair: what is printed,
how many occurrences were looked at, and `verified` or `uncertain`.

Settle in particular, with enough occurrences to be sure:

- `à` in Skiri fonts: is the printed glyph ə́?
- `‡`: is it ɪ́, and how does it differ in print from `æ`?
- `ˆ`, `ç`, `ø`, `Ò`: the grave accents. Are they grave in print?
- every character in cognate citations (Arikara, Kitsai, Wichita, Kiowa …)
  that the current table leaves undecoded (`ó`, `Ý`, `?`).

Then decode the whole text layer with the verified table into
`work/textlayer/`, one file per page, keeping for every span its font, size,
position and decoded text.

Done when: every pair that occurs in a Skiri or phonetic span is `verified` or
listed as `uncertain` with its count, and the user has been told which stored
symbols are affected. Whether to change stored symbols (the ə́/ɪ́ question) is
the user's decision; the audit records what is printed and how many entries a
change would touch.

### Stage 2. Skiri-to-English against the text layer, both directions

Segment each page of the text layer into entries by its bold headwords,
respecting the two columns and entries that run over a column or page break.
Then:

- **Stored → page.** For each database entry, find its entry block by
  headword. For each field (IPA, class, verb class, each sense, the etymology,
  each paradigm form, each example and its translation, each cognate), test
  that it is printed in that block. Record every field that is not.
- **Page → stored.** For each entry block, remove everything the database
  accounts for. What is left, beyond labels and punctuation, is text the
  database lacks. Every token in a Skiri font must be accounted for by a Skiri
  field.
- **Entries.** A bold headword with no database entry is a missing entry. A
  database entry with no headword on any page is a phantom. Check homographs
  one for one.

Classify differences by kind. Turn a kind into a `noise` rule only after
looking at examples of it, and log the rule and its count.

Then test the comparison itself: plant at least 300 known errors of at least
eight kinds in a copy of the stored values (a changed consonant, `h` for `b`,
a dropped accent, a dropped glottal stop, a shortened vowel, a deleted sense, a
truncated example, a deleted entry, a swapped class) and report recall by
kind. If any kind is below 95%, fix the comparison and run again.

Done when: all 181 pages and every Parks entry are processed, the recall test
passes, and `s2e_differences.jsonl` is written with a count per kind.

### Stage 3. Settle the Skiri-to-English differences from the page

For each difference that is not `noise`, render a crop of the entry from the
page PDF. Read crops in batches on contact sheets labelled by id only; write
the readings to a file; let a script compare the reading with the two
candidates. Grade each difference.

Where a kind of difference has come out the same way on every one of at least
30 crops, the rest of that kind may be graded `text-layer` without reading
them. Say so, with the count.

Also read crops for a random sample of 60 fields on which the database and the
text layer agree, to estimate how often both are wrong together.

Done when: every non-noise difference has a grade.

### Stage 4. The image-only parts

Appendices 1 to 3 and front-matter chapters 2 to 5: 60 pages with no text
layer. The stored extraction is one reading (an AI model, March 2026). Get a
second, **blind** reading: render each page as overlapping tiles at a zoom
where the smallest diacritic is clear, and give a sub-agent the tiles and a
transcription format, and nothing else. One sub-agent per few pages, a few at
a time. Each writes its transcription to `work/blind/`.

Compare the blind reading with the stored extraction, form by form and cell by
cell. Settle every difference from a zoomed crop, reading before looking.

Order by what depends on the data: Appendix 1 (the conjugation engine's answer
key), Appendix 3 and Appendix 2 (kinship and irregular roots, used by the
possession and conjugation engines), the grammatical overview (every Skiri
form, affix and table), major sound changes (the 24 rules and their examples),
sounds and alphabet, organization. The abbreviations chapter has a text layer
and is compared by script.

Add one check that needs no image: every Skiri form in these files uses only
letters of the Skiri alphabet. This would have caught *-biriʔ*.

Done when: every page has a blind reading, and every difference has a grade.

### Stage 5. The Blue Book

In this order:

1. The 93 Blue Book-only entries: headword and gloss of each against a crop of
   the page it came from. These are dictionary entries learners see.
2. `blue_book_attestations` and the Blue Book examples: each Pawnee form and
   its English against the OCR text of its page; what the OCR does not confirm
   goes to a crop.
3. `lessons`: titles and dialogue lines the same way.

Blue Book spelling is kept as printed. A stored form that was "normalized"
toward Parks's spelling is a finding.

Done when: every item is graded.

### Stage 6. English-to-Skiri against the text layer

As Stage 2, for the 284 pages: each `english_index` row's English headword,
Skiri term, IPA, class and cross-reference against its page, and each printed
subentry against the table. Where a row is linked to a Skiri-to-English entry,
check that the two sections print the same form; where they differ, that is a
`printed-oddity` or a parsing error, and the image says which.

Done when: all 284 pages are processed and differences graded.

### Stage 7. Report and proposed fixes

- `findings.md`: for a person. What was checked, how, the two self-test
  figures, counts by source, grade and severity, the ten findings that matter
  most, what the audit could not settle, and what it cannot show at all.
- `proposed_fixes.jsonl`: one line per proposed change: table, key, field,
  stored value, printed value, source file and page, grade, severity, evidence
  crop. Only `confirmed` and `text-layer` grades.
- `review.html`: the proposed fixes of severity 1 and 2 with their crops, so a
  person can approve them by eye.
- `scripts/source_audit/apply_fixes.py`: reads an approved subset of the
  proposals; dry run by default; backs up; writes its report only when
  applied; updates database, JSON and `DB/dump/` together.
- Bring the documents up to date in the same change: the project log (a phase
  entry, and the open items this closes or opens), `reports/README.md`,
  `scripts/README.md`, `prompts/README.md`, `DB/README.md`.

## Definition of done

1. Every in-scope table and file has been compared in full with a second
   reading, and the report says which reading that was.
2. Every character of the text-layer table that occurs in Skiri or phonetic
   text is verified against glyphs, or listed as uncertain.
3. The recall test and the agreement sample have been run and their figures
   are in the report.
4. Every difference has a grade; none is silently dropped; every noise rule is
   named and counted.
5. Nothing in the database, the JSON files or `extracted_data/` has been
   changed by the audit.
6. `STATE.json` shows every stage `done`, and the documents are up to date.

## When to stop and ask

- A decision about what the database should hold, as opposed to what the page
  shows: the ə́/ɪ́ symbols, "pitch" or "stress", normalizing `page_number`.
  Record what is printed and what a change would touch, and go on.
- Anything touching ceremonial content beyond checking its fidelity.
- A stage whose image reading would be far above the estimate given.

For everything else, decide, write the decision in `progress.log`, and go on.

## Final report to the user

Lead with whether the database can be trusted and to what degree, in two
sentences. Then: counts of differences by severity; the ones that would change
what a learner sees; what was not settled; the cost (images read, sub-agents
started); and the decisions that are the user's to make. Say plainly what was
not checked.
