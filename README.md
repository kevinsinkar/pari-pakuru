# Pari Pakuru' — Skiri Pawnee dictionary and learning tools

A searchable dictionary, a set of lessons and flashcards, and a word-building
guide for Skiri (Skidi) Pawnee. Everything is built from two printed sources,
and every Pawnee form can be traced back to the page it came from.

Skiri Pawnee is critically endangered. The aim is to make the published record
of the language usable by learners, teachers and community members, without
adding anything the sources do not say.

*Last checked against the data: 2026-11-13.*

## The two sources

| Source | What it is | Where |
|---|---|---|
| Parks & Pratt, *A Dictionary of Skiri Pawnee* (2008) | The scholarly record: headwords, IPA pronunciation, grammar class, meanings, etymologies, five standard verb forms, examples | [Dictionary Data/](Dictionary%20Data/) |
| *Pari Pakuru'* ("the Blue Book", 1979) | The Pawnee Cultural Retention Committee's 20-lesson textbook: dialogues, vocabulary, grammar notes | [pari pakuru/](pari%20pakuru/) |

No other source is used. Where the two disagree, both readings are shown.

## What has been built

| | State on 2026-11-13 |
|---|---|
| **Dictionary database** | 4,337 entries (4,244 from Parks, 93 words found only in the Blue Book), 5,504 senses, 9,559 attested verb forms for 2,250 verbs, 2,635 example sentences |
| **Pronunciation** | Parks's IPA for 4,328 entries, 1,800 of them with the accented syllable marked; a learner respelling for 4,324. IPA is never generated, only copied from Parks |
| **Web app** | Flask app: two-way search, entry pages, Blue Book lessons, weekly flashcards, spaced-repetition study, sentence builder, community feedback |
| **Public static site** | The search, flashcard and lesson pages, built into [docs/](docs/) and served by GitHub Pages |
| **Blue Book lessons** | All 20 lessons with dialogues, vocabulary and grammar notes |
| **Flashcards** | 24 weekly sets, 387 words, frozen on 2026-10-12; 23 sets (372 words) are shown and one is held for community review; printable sheets for writing cards by hand |
| **Word-building guide** | 549 roots and 30 affixes that let a learner take apart 1,791 of the dictionary's words completely (41%); 15 lessons. See [curriculum/roots_v2/](curriculum/roots_v2/) |
| **Grammar tools** | 24 sound-change rules; verb form prediction; noun possession; ten sentence templates from Blue Book dialogues |

## Folder map

| Folder | What it holds | Edit by hand? |
|---|---|---|
| [Dictionary Data/](Dictionary%20Data/) | **Source.** The Parks dictionary PDFs, and the two JSON dictionaries parsed from them | The JSON only through scripts |
| [pari pakuru/](pari%20pakuru/) | **Source.** The Blue Book PDF and its text | No |
| [extracted_data/](extracted_data/) | Structured data pulled out of the sources: Parks's appendices and grammar chapter, Blue Book vocabulary and lessons | No, regenerate |
| [DB/](DB/) | Database schema, the importer that builds the database from the JSON, and the query library. [DB/dump/](DB/dump/) is the database itself, written out as text so that it is in git | Yes; `dump/` only through `scripts/db_dump.py` |
| [scripts/](scripts/) | Every processing step, one script per step. [scripts/README.md](scripts/README.md) lists them in order | Yes |
| [scripts/morphology_v2/](scripts/morphology_v2/) | The word-construction analysis (2026-11) | Yes |
| [curriculum/](curriculum/) | Learner material built from the database: flashcard sets and the word-building guides | Only `flashcard_sets.json`, deliberately |
| [web/](web/) | The Flask web app | Yes |
| [docs/](docs/) | **Generated.** The static site that GitHub Pages serves | No, rebuild |
| [reports/](reports/) | What each step found: validation results, audits, change logs | No |
| [prompts/](prompts/) | The written instructions each stage was built from: AI prompts, design specs, JSON schemas | Yes |
| [exports/](exports/) | The community-feedback table, exported so that it is in git | No, written by the app |
| [archived/](archived/) | One-off scripts and reports from finished stages, kept as a record. No live code reads them | No |

Files in the root:

| File | What it is |
|---|---|
| [pari_pakuru_project_scope.md](pari_pakuru_project_scope.md) | The project log: every phase, what was done, the results, what is still open |
| [Quick_Reference_Guide.md](Quick_Reference_Guide.md) | Cheat sheet: how a dictionary entry is laid out, sound system, database tables, web routes |
| [DEPLOYMENT.md](DEPLOYMENT.md) | How the static site and the hosted web app are published |
| `skiri_pawnee.db` | The database. **Not in git** (see below) |
| `requirements.txt`, `wsgi.py` | What the hosted web app needs |

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
4. **Publish.** The web app reads the database; the static site and the flashcards are built from it.
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

All of these were run on 2026-11-13.

| Check | Command | Result |
|---|---|---|
| Sound-change rules | `scripts/sound_changes.py --test` | 11 of 11 |
| Person and mode derivation | `scripts/person_forms.py --validate-appendix` | 27 of 27 against Parks Appendix 1 |
| Sentence templates | `scripts/sentence_templates.py test` | 34 of 34 |
| Respelling and audit code | `scripts/test_phase_1_1.py` | 106 of 106 |
| Database schema and query library | `DB/test_schema.py` | 53 of 53 |
| Word-construction analysis | `python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"` | 34 of 34 |
| Its test sets are unchanged | `scripts/morphology_v2/gold_build.py --verify` | 17 files match their hashes |
| Its outputs are reproducible | `scripts/morphology_v2/run.py --all`, hashes compared | byte-identical |
| Every Pawnee form in the guide has a source | `scripts/morphology_v2/check_forms.py` | 3,781 forms, 250 IPA, 204 respellings: all resolved |
| Noun possession and the *-hiriʔ* suffix | `scripts/possession_engine.py --test` | 59 of 59, ten of them attested dictionary words |
| The text copy of the database restores to the same database | `scripts/db_dump.py --verify` | round trip exact: 46,783 rows in 25 tables |
| Dictionary entries against the printed page | `scripts/source_audit/s2e_compare.py` | 49,443 of 50,736 fields identical (97.45%); the differences are in `reports/source_audit_2026-11/` |
| That comparison catches errors | `scripts/source_audit/recall_test.py` | 510 of 510 planted errors reported |
| Web app | 25 routes requested through Flask's test client; the possession API for all 1,706 nouns | all answer |

Measurements, not pass or fail:

| What | Command | Result |
|---|---|---|
| Conjugation engine against Parks Appendix 1 | `scripts/morpheme_inventory.py --validate` | 695 of 770 forms exact (90.3%) |
| Form 2 predicted from headword, class and preverb | `scripts/stem_extractor.py --validate` | 1,904 of 2,197 verbs exact (86.7%) |

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
  fixes are not applied yet.** The source-fidelity audit of 2026-11-13
  ([reports/source_audit_2026-11/findings.md](reports/source_audit_2026-11/findings.md))
  found the dictionary entries 97.5% identical to print, field for field, and
  the tables read from page images much worse: 152 of the 770 verb forms of
  Appendix 1 differ from the page. It proposes 2,250 fixes and applies none.
  Until they are reviewed and applied, treat a form from the appendices, the
  grammar chapter or the English index as unchecked.
- **The IPA is close to Parks's, not yet identical.** The PDF encodes his
  symbols with stand-in characters. The table is now verified against the
  printed glyphs for every character (`scripts/source_audit/chartable.py`).
  What the database still writes differently, everywhere: à for his ə́, í for
  his lax ɪ́, a hyphen for his syllable dot and a bullet for his dash at the
  edge of a bound form. Whether to change the stored symbols is an open
  decision.
- **"Accent", not "pitch".** Parks writes that stress is not phonemic in Skiri
  and that his phonetic forms mark the accented syllable. Parts of the app
  still call this "pitch".
- **Generated forms are marked.** Any verb form that was derived, not attested,
  carries a confidence level and a note. Spelling-based pronunciations are
  marked with ≈.
- **Open data questions** are listed at the end of the
  [project log](pari_pakuru_project_scope.md#open-items).

## Contributing

Corrections are welcome, most of all from Pawnee community members, language
learners and linguists. Please open an issue with the headword and the page
number, or use the flag button on an entry page in the web app. Every
correction is reviewed by a person before it is accepted.

## References

- Parks, Douglas R., and Lula Nora Pratt. *A Dictionary of Skiri Pawnee.* Lincoln: University of Nebraska Press, 2008.
- Pawnee Cultural Retention Committee. *Pari Pakuru'.* 1979.

## Licence and respect

The structured data here is for education and language revitalisation. The
dictionary and the textbook remain the property of their authors and
publishers. The language belongs to the Pawnee people; please treat it, and
especially its ceremonial vocabulary, with that in mind.
