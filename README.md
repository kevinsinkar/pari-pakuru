# Pari Pakuru' — Skiri Pawnee dictionary and learning tools

A searchable dictionary, a set of lessons and flashcards, and a word-building
guide for Skiri (Skidi) Pawnee. Everything is built from two printed sources,
and every Pawnee form can be traced back to the page it came from.

Skiri Pawnee is critically endangered. The aim is to make the published record
of the language usable by learners, teachers and community members, without
adding anything the sources do not say.

*Last checked against the data: 2026-11-14.*

## The two sources

| Source | What it is | Where |
|---|---|---|
| Parks & Pratt, *A Dictionary of Skiri Pawnee* (2008) | The scholarly record: headwords, IPA pronunciation, grammar class, meanings, etymologies, five standard verb forms, examples | [Dictionary Data/](Dictionary%20Data/) |
| *Pari Pakuru'* ("the Blue Book", 1979) | The Pawnee Cultural Retention Committee's 20-lesson textbook: dialogues, vocabulary, grammar notes | [pari pakuru/](pari%20pakuru/) |

No other source is used. Where the two disagree, both readings are shown.

## What has been built

| | State on 2026-11-14 |
|---|---|
| **Dictionary database** | 4,337 entries (4,244 from Parks, 93 made from words of the Blue Book, of which 37 are words Parks has too, in the textbook's spelling), 5,504 senses, 9,559 attested verb forms for 2,239 verbs, 2,607 example sentences, 21 derived stems. Compared with the printed pages in full on 2026-11-13 and corrected, then completed from the print on 2026-11-14: 99.94% of the dictionary fields are identical to print, and every entry cites the page of the book it stands on |
| **Pronunciation** | Parks's IPA for all 4,244 of his entries, stored in his own symbols, 2,218 of them with the accented syllable marked; a learner respelling for 4,332. IPA is never generated, only copied from Parks; the Blue Book-only words have none |
| **Public site** | A learner's site, built into [docs/](docs/) and served by GitHub Pages: the search, a "Start here" path, pages on the sounds, on how words are built and on how verbs change, practice games, words by topic, the lessons and the flashcards. The learning pages show only what the books print (a phonetic form cut at its syllables, a derivation cut into its pieces, the seven verbs of Appendix 1) and make no form. A search result opens the whole entry (examples, verb forms, Parks's analysis, the forms he cites from related languages) and has a link for sending a correction. This is the only place the project is published |
| **Local web app** | Flask app that runs on your own machine: full entry pages, the printed forms of a noun, a sentence builder, spaced-repetition study, feedback queue, dashboard. Not hosted anywhere since 2026-11-13; the public site is built from its templates |
| **Blue Book lessons** | All 20 lessons with dialogues, vocabulary and grammar notes. Every Pawnee word in them is as read from the scan: the vocabulary by the audit of 2026-11-13, the titles, dialogues and notes line by line on 2026-11-14 (911 lines). Each dialogue line stands with its English, paired by the row of the page it is printed on. The English prose of the notes is OCR text |
| **English index** | Parks's English-to-Skiri section, rebuilt from the printed page on 2026-11-14: 6,431 English headwords, 5,165 Skiri terms under them (5,162 linked to their entry), 4,578 cross-references. Used by the local app's search; the public search does not use it yet |
| **Flashcards** | 24 weekly sets, 387 words, frozen on 2026-10-12; 23 sets (372 words) are shown and one is held for community review; printable sheets for writing cards by hand |
| **Word-building guide** | 549 roots and 30 affixes that let a learner take apart 1,794 of the dictionary's words completely (41%); 15 lessons. See [curriculum/roots_v2/](curriculum/roots_v2/) |
| **Printables** | A word list of the 372 flashcard words and Parks's seven verbs in full (Appendix 1), as PDFs: [curriculum/printables/](curriculum/printables/) |
| **Review packet** | What the project asks the Pawnee Nation's language and culture people to look at, as one 41-page document with an answer sheet: [community_review/](community_review/). Ready; not sent |
| **Grammar tools** | What the app shows of grammar is copied, with two narrow exceptions that are labelled. Copied: Parks's 24 sound changes with his examples; his tables of the verb, printed in the word-building guide; for a noun, the forms he and the Blue Book print. Labelled as made here, and in the local app only: "you" and question forms of a verb ("derived; not checked against a printed form") and sentences put together from printed words ("put together here; not printed"). The conjugation engine, the accent rules and the possession engine were withdrawn on 2026-11-14 after being measured on forms they had not been fitted to: [reports/engines_review/](reports/engines_review/) |

## Folder map

| Folder | What it holds | Edit by hand? |
|---|---|---|
| [Dictionary Data/](Dictionary%20Data/) | **Source.** The Parks dictionary PDFs, and the two JSON dictionaries parsed from them | The JSON only through scripts |
| [pari pakuru/](pari%20pakuru/) | **Source.** The Blue Book PDF and its text | No |
| [extracted_data/](extracted_data/) | Structured data pulled out of the sources: Parks's appendices and grammar chapter, Blue Book vocabulary and lessons | No, regenerate |
| [DB/](DB/) | Database schema, the importer that builds the database from the JSON, and the query library. [DB/dump/](DB/dump/) is the database itself, written out as text so that it is in git | Yes; `dump/` only through `scripts/db_dump.py` |
| [scripts/](scripts/) | Every processing step, one script per step. [scripts/README.md](scripts/README.md) lists them in order | Yes |
| [scripts/morphology_v2/](scripts/morphology_v2/) | The word-construction analysis (2026-11) | Yes |
| [scripts/engines_review/](scripts/engines_review/) | The review of the grammar engines (2026-11): test sets made from attested forms, the measurements of the engines as they were, and the sealed test of the one that was repaired. Changes nothing | Yes |
| [curriculum/](curriculum/) | Learner material built from the database: flashcard sets and the word-building guides | Only `flashcard_sets.json`, deliberately |
| [community_review/](community_review/) | The packet for community review. The built files are not in git; the README and the script are | No, rebuild |
| [web/](web/) | The Flask web app, run locally; its templates are what the static site is built from | Yes |
| [docs/](docs/) | **Generated.** The static site that GitHub Pages serves | No, rebuild |
| [reports/](reports/) | What each step found: validation results, audits, change logs | No |
| [prompts/](prompts/) | The written instructions each stage was built from: AI prompts, design specs, JSON schemas | Yes |
| [exports/](exports/) | The community-feedback table, exported so that it is in git | No, written by the app |
| [archived/](archived/) | One-off scripts and reports from finished stages, and the engines withdrawn on 2026-11-14, kept as a record. No live code reads them | No |

Files in the root:

| File | What it is |
|---|---|
| [pari_pakuru_project_scope.md](pari_pakuru_project_scope.md) | The project log: every phase, what was done, the results, what is still open |
| [Quick_Reference_Guide.md](Quick_Reference_Guide.md) | Cheat sheet: how a dictionary entry is laid out, sound system, database tables, web routes |
| [DEPLOYMENT.md](DEPLOYMENT.md) | How the static site is published, and how to run the web app locally |
| `skiri_pawnee.db` | The database. **Not in git** (see below) |
| `requirements.txt` | What the web app and the site build need (Flask) |

## How the data flows

```
Parks dictionary PDFs ─┐
                       ├─ parse ─► JSON dictionaries ─ import ─► skiri_pawnee.db ─┬─► web app
Blue Book text ────────┘           (Dictionary Data/)            (database)       ├─► static site (docs/)
                                                                      ▲           ├─► flashcards, lessons
              extracted_data/ (appendices, grammar, lessons) ─────────┘           └─► word-building guide
```

1. **Parse.** Each dictionary page was read by an AI model into JSON, then verified, normalised and linked (phases 1.1a to 1.1d).
2. **Import.** The JSON was loaded into SQLite (phase 1.2).
3. **Enrich.** Later steps added semantic tags, Blue Book attestations, lessons, grammar tables and repairs straight into the database.
4. **Publish.** The static site and the flashcards are built from the database and pushed to GitHub Pages. The web app reads the database directly and runs only on your own machine.
5. **Analyse.** The word-construction analysis reads the database and writes its own outputs; it never changes the database.

[scripts/README.md](scripts/README.md) gives the script for each step. The project log gives the results.

### The database is the working master copy

`skiri_pawnee.db` is not in git, and it cannot be rebuilt from the sources with
one command. After the first import, more than twenty scripts changed it in
place, and several of those used an AI service whose answers went straight
into the database. So:

- **The database is in git as text**, in [DB/dump/](DB/dump/) (since
  2026-11-13). `python scripts/db_dump.py --restore new.db` builds a database
  from it; `--write` brings the text up to date after a change, so that the
  change can be read as a difference in git. The feedback table and study
  progress are left out of the text.
- Keep backups. Scripts that change the database back it up first to
  `OneDrive/pari_pakuru_backups/` (or `~/.pari_pakuru_backups/`).
- The JSON files in `Dictionary Data/` hold the dictionary text itself and are
  kept in step with the database for the fields the audits checked. They do not
  hold the tags, Blue Book links, lessons or grammar tables.
- Every script that changes the database or the JSON has a preview mode
  (`--dry-run`, or no change without `--apply`). Use it first.

## Run it

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Flask is all the web app needs

.venv/Scripts/python -m web.app                            # web app at http://localhost:5000
.venv/Scripts/python scripts/build_static_site.py          # rebuild docs/ from the database
.venv/Scripts/python scripts/morphology_v2/run.py --all    # regenerate the word-construction analysis
```

On Windows the console uses code page 1252. A few older scripts print Pawnee
characters directly and need `PYTHONIOENCODING=utf-8` set first.

Some pipeline scripts need more packages: `google-genai` (AI extraction steps,
with `GEMINI_API_KEY` set), `PyMuPDF` (PDF rendering, printable flashcards),
`pypdf` (the original page parsers), `genanki` (Anki export). None of them is
needed to run the app, the site build or the analysis.

## Checks

All of these were run on 2026-11-14.

| Check | Command | Result |
|---|---|---|
| The sound-change table is the catalogue of Parks's 24 rules | `scripts/sound_changes.py --check-table` | 24 rules, identical (what the code makes of them is a measurement, below) |
| Person and mode derivation | `scripts/person_forms.py --validate-appendix` | 26 passed, 0 failed, 2 declined, against Parks Appendix 1 as corrected from the page. It fails on any mismatch |
| Sentence builder | `scripts/sentence_templates.py --test` | 38 of 38; every expected form is read from a row of the Blue Book table |
| Every Pawnee form in the builder's two files is copied | `scripts/sentence_templates.py --check` | 13 printed sentences and 3 question words, each what its row or entry holds; no form stands anywhere else in the files: zero exceptions |
| Respelling and audit code | `scripts/test_phase_1_1.py` | 106 of 106 |
| Database schema and query library | `DB/test_schema.py` | 53 of 53 |
| Word-construction analysis | `python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"` | 34 of 34 |
| Its test sets are unchanged | `scripts/morphology_v2/gold_build.py --verify` | 17 files match their hashes. Three of them (Parks's worked examples, the Appendix 1 cells, the Blue Book seams) were made again from the corrected data on 2026-11-14 |
| Its outputs are reproducible | `scripts/morphology_v2/run.py --all`, hashes compared | byte-identical |
| Every Pawnee form in the guide has a source | `scripts/morphology_v2/check_forms.py` | 3,833 forms, 250 IPA, 202 respellings, 412 cells of Parks's tables: all resolved |
| The printed forms of a noun | `scripts/printed_noun_forms.py --check` | 734 of 1,706 nouns have something printed (38 Appendix 3 rows, 680 forms with a case ending, 537 combining forms, 18 Blue Book forms); every form shown is a stored value of the entry it is shown on |
| No engine output is left in the database | `scripts/remove_engine_output.py --check` | the four engine tables are gone, the form 2 score is empty, the kin table holds Appendix 3 only |
| The lessons' text is what the page prints | `scripts/apply_lesson_page_reading.py --check` | every line of the twenty lessons that is not plain English was cut from the scan and read: 910 lines of the text as it now stands (79 read a second time), 1,368 Pawnee words. No difference is open; 21 are left by decision, each with its reason; the 20 titles are the title lines of the page |
| Every dialogue line is a Pawnee line with its English | `scripts/pair_lesson_dialogues.py --check` | 105 lines in 46 dialogues; 102 have their English beside them, 3 are printed without one (a second dialect's form, an alternative in brackets, a breakdown line) |
| The lessons are in step with the audit's reading of the scan | `scripts/fix_lesson_text_ocr.py --check` | none of the 380 readings the audit corrected in letters, spacing or punctuation stands in the text; 13 titles hold the table's reading of the title line (the table has none for the other 7) |
| Blue Book words are tied to the entry they are a form of | `scripts/relink_bluebook.py --check` | 257 of 1,026 rows are tied, every one by its form and a shared meaning; 43 Blue Book sentences stand as examples, each under an entry one of its words is tied to |
| The function-word tables against the scan's readings | `scripts/fix_function_words.py --check` | all 62 rows of `bb_function_words` hold the word their phrase prints; all 51 Blue Book rows of `function_words` are a word or a bulleted part of a form of the Blue Book table |
| The text copy of the database restores to the same database | `scripts/db_dump.py --verify` | round trip exact: 46,359 rows in 21 tables |
| Dictionary entries against the printed page | `scripts/source_audit/s2e_compare.py` | 50,807 of 50,837 fields identical (99.94%; 97.45% before the first fixes, 99.68% after them). The 37 differences left are each explained in `reports/source_audit_2026-11/print_completion_report.txt` |
| Every entry cites the page of the book | `scripts/fix_page_citations.py --check` | 4,244 of 4,244 Parks entries; the printed page number was read from all 181 pages |
| Learner spelling and respelling follow from Parks's forms | `scripts/check_simplified_forms.py` | no difference in 4,244 entries |
| That comparison catches errors | `scripts/source_audit/recall_test.py` | 510 of 510 planted errors reported |
| The grammar chapter against two blind readings of the page | `scripts/source_audit/chapter4_second_reading.py` | all 526 Skiri words of the stored chapter stand in both readings; nothing left to correct |
| Blue Book forms against the readings of the scan | `scripts/apply_bluebook_scan_fixes.py` (a dry run) | nothing left to apply; 17 forms listed for a person; 2 crops passed over because they were cut at another line than the row's own |
| The English index against the printed page | `scripts/repair_english_index.py --check` | the file and both tables say what the page says; 118,262 letters printed in the type of Skiri terms, 118,262 stored. The audit's own comparison (`source_audit/e2s_compare.py`): 32,632 of 32,636 fields equal |
| Chapters 2 and 5 against two readings of the page | `scripts/source_audit/front_matter_reading.py` | all 138 and 57 Skiri forms the same in both readings |
| The grammar chapter's tables in two readings | `scripts/source_audit/chapter4_tables.py` | 14 tables: 6 the same, 6 the same text with rows divided differently, 2 differ |
| The Blue Book glossary against the pages it points to | `scripts/bluebook_glossary.py` | 589 of 644 page references confirmed |
| The published site | `node scripts/check_static_site.js` (needs Node.js) | 28 checks pass (2026-11-14): all 4,337 entries render, every value escaped; each of the 3,319 word derivations shown piece by piece stands in the printed derivation; 770 forms of Appendix 1; no link between the 53 pages is broken |
| Web app | 49 addresses requested through Flask's test client, on a copy of the database | every page and read-only route answers; the two withdrawn routes (`/api/possession`, `/api/bb_verb_forms`) answer 404 |
| The engines review's test sets still match their sources | `scripts/engines_review/run_all.py --check` | 10 sets as recorded (the Blue Book sentences once the 13 rows corrected from the page since the review are put back) |

Measurements, not pass or fail. "Seen" means the rules were read from those
very forms, so the figure proves little; "unseen" is the kind to go by.

| What | Command | Result |
|---|---|---|
| The sound-change rules as coded, on the 39 examples Parks prints with them | `scripts/sound_changes.py --measure` | 8 of 39. The file is a reference to the rules, not an engine |
| Form 2 predicted from headword, class and preverb (seen) | `scripts/stem_extractor.py --validate` | 1,915 of 2,197 verbs exact (87.2%). No source prints a form 2 the rules did not see; the predictor is used as a checker only |
| Person derivation: the question form for "he/she" against the start of the dictionary's form 4 (unseen: the sealed half, opened once) | `scripts/engines_review/person_forms_repair.py` | 794 of the 816 forms it gives (97.3%); no form for 243 of 1,059 verbs. On the open half: 786 of 809 (`--open`). Record: [reports/engines_review/person_forms_repair.md](reports/engines_review/person_forms_repair.md) |

The engines that were withdrawn, as measured before (the record is
[reports/engines_review/measurements.md](reports/engines_review/measurements.md);
the scripts that made it refuse to run on today's files): the conjugation
engine, 611 of 770 Appendix 1 forms (seen) and 1,431 of 9,559 dictionary forms
(unseen, 15.0%); the possession engine, 300 of 675 printed locative and
instrumental forms (unseen, 44.4%).

## What to be careful about

- **Nothing here is a substitute for a speaker.** The transcribers and reviewers
  in the pipeline were AI models checked against the printed page. No speaker or
  linguist has reviewed the output yet. [curriculum/roots_v2/review_queue.md](curriculum/roots_v2/review_queue.md)
  lists what most needs one.
- **Ceremonial vocabulary.** Words to do with bundles, dances and doctoring are
  flagged for community review and kept out of the word-building lessons.
  Flashcard Week 20 ("Ceremony & Sacred") is held back from the web app, the
  static site and the printable cards (`curriculum/held_for_review.json`).
  Whether it is shown is the Pawnee Nation's decision, and it has not been
  asked yet.
- **The database has been compared with the printed pages in full, and the
  fixes with solid evidence are applied.** The source-fidelity audit of
  2026-11-13 ([reports/source_audit_2026-11/findings.md](reports/source_audit_2026-11/findings.md))
  found the dictionary entries 97.5% identical to print, field for field, and
  the tables read from page images much worse: 152 of the 770 verb forms of
  Appendix 1 differed from the page. 807 fixes were applied the same day. On
  2026-11-14 everything else the PDF's text layer can settle was set from it
  (1,447 values, most of them hyphens the typesetter put at line ends and the
  parse kept); the dictionary entries are now 99.94% identical. The grammar
  chapter, which exists only as page images, was read a second time by
  readers who saw nothing but the page: both blind readings agree on every
  Skiri word, and the stored chapter was corrected to them (38 words, Table
  17). What is left is for a person with the books: 37 small differences in
  the dictionary and 17 Blue Book forms that three readings could not settle.
  The English index was rebuilt from the printed page on 2026-11-14.
  Chapters 2 and 5 of the dictionary's front matter were read the same day,
  twice; they are stored as forms, tables and summaries, not as running text.
- **The IPA is Parks's, in his own symbols.** The PDF encodes his symbols with
  stand-in characters; the table is verified against the printed glyphs for
  every character (`scripts/source_audit/chartable.py`), and every phonetic
  form was set from it on 2026-11-13: ə́ and ɪ́ for the accented short vowels,
  `·` between syllables, `–` at the edge of a bound form. The learner
  respelling is coarser in one known way: it does not show his difference
  between tense and lax short i and u (589 entries). See the
  [quick reference](Quick_Reference_Guide.md#sounds-and-spellings).
- **Almost nothing in the app is computed any more, and what is says so.**
  The engines review of 2026-11-14 measured each grammar engine on printed
  forms it had not been fitted to. The conjugation engine got 15.0% of the
  dictionary's verb forms; the possession box answered 1,671 of 1,706 nouns
  with a phrase beginning with *kti*, an OCR slip, under the word "attested";
  the sentence builder offered three words that do not exist. The owner
  decided, and the same day: those engines were withdrawn or rebuilt on
  copied forms, and their stored output removed from the database. Two kinds
  of made forms remain, in the local app only, each with its label: "derived;
  not checked against a printed form" (a verb's "you" and question forms) and
  "put together here; not printed" (a sentence made of printed words). The
  derived "he/she" question form agreed with the dictionary's own form 4 for
  97.3% of the verbs it gives a form for, on verbs set aside before the
  repair; the "you" forms can be checked against nothing but Appendix 1's
  seven verbs. None of it is a speaker's judgement. What was done, decision
  by decision: [reports/engines_review/stage4.md](reports/engines_review/stage4.md).
- **The Pawnee of the lessons was read from the page, line by line; their
  English and their layout were not.** On 2026-11-14 every line of the twenty
  lessons' titles, dialogues and notes that is not plain English was cut from
  the scan and read (911 lines, 79 of them a second time at a larger cut):
  328 places were corrected (42 by hand after a second look, 286 where one
  reading settles it: an accent, a raised dot, an apostrophe), 8 titles set,
  and the title of the next lesson and the Blue Book's glossary cut from the
  end of the notes where the extraction had left them. At 164 of the 286
  places the audit's reader had read the same; the others rest on one
  reading, made in the main session, of a line no reader had looked at. Three places lie under a
  flaw in the scan and carry square brackets (*Kitské [w]e ru'?*,
  *We ti p[it]ku.*, *Ka res•[..]sí•urúkat!*); they need the book. The
  dialogues were then paired: in 83 of 156 stored lines the English had stood
  in the place of a Pawnee line or was missing, and each Pawnee line now has
  the English the page prints on its row (105 lines). Still as the extraction
  left it: the English prose of the notes. Records:
  [reports/lesson_text_ocr_report.txt](reports/lesson_text_ocr_report.txt),
  [reports/lesson_dialogues_pairing_report.txt](reports/lesson_dialogues_pairing_report.txt).
- **The Blue Book forms now carry the printed accents.** The stored forms came
  from OCR, which dropped or garbled the accented vowels. 949 forms were read
  again from the scan and 715 corrected. One of them is on a flashcard a
  learner meets in Week 1: "yes" was stored as *had'* and is *haú'* in the
  book.
- **"Accent", not "pitch".** Parks writes that stress is not phonemic in Skiri
  and that his phonetic forms mark the accented syllable (p. 15). Only two
  style names in the code still say "pitch".
- **The dictionary's *kt* was *tt* for most speakers.** Parks writes forms with
  *kt* after one speaker and says that all other twentieth-century Skiri
  speakers said *tt* (p. 16). The site does not tell learners yet; the review
  packet asks which to teach.
- **"Blue Book-only" is not quite true.** 37 of the 93 entries made from
  Blue Book words are words Parks has: the textbook does not write long
  vowels. The site names the dictionary's entry beside them. They are still
  separate entries, and some are in the first flashcard weeks.
- **Made forms are marked.** A verb form that was derived carries the words
  "derived; not checked against a printed form"; a sentence the book does not
  print carries "put together here; not printed"; spelling-based
  pronunciations are marked with ≈. The sentence builder no longer adds a
  spelling-based pronunciation to a sentence.
- **Open data questions** are listed at the end of the
  [project log](pari_pakuru_project_scope.md#open-items).

## Contributing

Corrections are welcome, most of all from Pawnee community members, language
learners and linguists. Please open an issue with the headword and the page
number. (The flag button on entry pages exists only in the local web app,
which is not hosted.) Every correction is reviewed by a person before it is
accepted.

## References

- Parks, Douglas R., and Lula Nora Pratt. *A Dictionary of Skiri Pawnee.* Lincoln: University of Nebraska Press, 2008.
- Pawnee Cultural Retention Committee. *Pari Pakuru'.* 1979.

## Licence and respect

The structured data here is for education and language revitalisation. The
dictionary and the textbook remain the property of their authors and
publishers. The language belongs to the Pawnee people; please treat it, and
especially its ceremonial vocabulary, with that in mind.
