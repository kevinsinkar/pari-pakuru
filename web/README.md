# web/

The Flask web app (Flask, SQLite, Pico CSS, HTMX). It reads
`skiri_pawnee.db` from the repository root.

**It runs locally only.** It was hosted on PythonAnywhere until 2026-11-13;
that hosting is retired. What the public sees is the static site in
[../docs/](../docs/), which is built from the templates here.

```bash
.venv/Scripts/python -m web.app            # http://localhost:5000
.venv/Scripts/python -m web.app --port 8080 --debug
```

| File | What it does |
|---|---|
| `app.py` | Routes, template filters (the accented syllable shown in capitals), the lesson exercises, the feedback export |
| `spelling.py` | The two spellings of a dictionary word, written into a page together: the filters `primary_spelling` and `secondary_spelling`, for the app and for the static build alike. It makes no form: the learner spelling is the entry's stored `normalized_form` |
| `db.py` | Database access. Builds on `DB/query_api.py`. The dictionary is opened read-only; a second, writable connection serves feedback and study progress |
| `search.py` | Language detection, full-text search, fuzzy matching for misspellings |
| `search_ranking.py` | Orders results: exact matches first, Blue Book words boosted |
| `flashcards.py` | The weekly flashcard sets. `load_sets()` serves the frozen `curriculum/flashcard_sets.json` and leaves out any week listed in `curriculum/held_for_review.json`; use it, not `generate_all_sets()`, in anything a learner sees |
| `srs.py` | Spaced-repetition scheduling (SM-2) for `/study` |
| `learning.py` | What the learning pages show (word building, verbs, practice, topics, the lesson pages, the phrases), for the app and for the static build alike. It copies printed forms and arranges them: `split_derivation()` cuts a derivation of the dictionary at its plus signs, `verbs_data()` reads Appendix 1 and 2 and the tables of chapter 4, `practice_data()` the flashcard weeks, `lesson_context()` puts one lesson page together, `phrases_data()` reads `curriculum/everyday_phrases.json` and refuses a line that does not stand in the lessons' text, `sources_data()` gives the page "Learn with others" the sources the register marks for learners, and `south_band_spelling()` with `dialect_labels()` give the marks SK, SB and "SB spelling". It makes no form, and leaves out the entries tagged `ceremony` |
| `templates/` | Jinja templates. Files starting with `_` are fragments included by others |
| `static/` | CSS and the scripts. `js/search.js` is the search of the published site: it runs in the visitor's browser over `docs/data/dictionary.json` and shows the whole entry, with a link for sending a correction (the local app searches on the server and does not use it). `js/skiri.js` holds what the learning pages share: a phonetic form cut at its syllable dots with a hint for each symbol, the pieces of a derivation as a row of chips, the box that remembers when a flashcard word is due again (`Skiri.box`, kept in the visitor's browser), the buttons that cover one side of a dialogue or a phrase (`Skiri.coverTools`), and the two spellings (`Skiri.spelling` keeps the visitor's choice in the browser; `Skiri.spell()` and `Skiri.spellOther()` write a word in both). `js/words.js`, `wordweb.js`, `verbs.js`, `practice.js`, `sounds.js` and `topics.js` each drive one page. `wordweb.js` is in two halves: the model and the layout of the picture, which need no page and are run by `scripts/check_static_site.js`, and the drawing |

The routes are listed in the [quick reference](../Quick_Reference_Guide.md#web-app-routes).

## What it imports from `scripts/`

`printed_noun_forms.py` (the box "Printed forms of this noun"),
`example_filter.py` (which Blue Book sentences an entry page shows) and
`sentence_templates.py` (the sentence builder; it brings in `person_forms.py`
and `template_slot_fillers.py`). Changing those changes the app.

## How it reaches the public

Only through the static site: `scripts/build_static_site.py` renders a subset
of these templates into `docs/` and rewrites the links: home, about, the
learning pages (`learn.html` "Start here", `guide.html` "Sounds", `words.html`, `wordweb.html`,
`verbs.html`, `practice.html`, `topics.html`, `phrases.html`, `resources.html`),
flashcards and lessons. See
[../DEPLOYMENT.md](../DEPLOYMENT.md). When you change one of those templates,
rebuild the site, run `node scripts/check_static_site.js` and look at the
result.

The learning pages read their data in the browser from `data/wordbuilding.json`,
`data/verbs.json` and `data/practice.json`. The static build writes those files;
the local app serves the same data at `/data/<name>.json`. Their scripts write
links the way the published site names its files (`words.html?piece=...`,
`index.html?id=...`); in the local app `/<name>.html` leads on to the same page
(`published_name` in `app.py`). `topics.html` exists
only on the published site (it filters `data/dictionary.json`); in the local
app `/topics` leads to `/browse`.

Everything else here (entry pages, browse, sentence builder, study, feedback,
dashboard) is seen only by someone running the app on their own machine.

## Rules the app keeps

- IPA is shown only when Parks prints it for that word.
- **The app computes almost nothing, and says so where it does.** A noun's
  page shows only forms Parks or the Blue Book prints. A Blue Book sentence in
  the builder is made of printed rows and says "printed in the Blue Book,
  lesson N" or "put together here; not printed". A verb form made by rule
  carries "derived; not checked against a printed form". There is no
  confidence level any more: it was a score for the code, not for the word.
- An entry's own examples are shown as Parks prints them, all of them. Only
  Blue Book sentences tied to an entry are filtered.
- **The learning pages arrange printed forms and add none.** The pieces of a
  word are the dictionary's derivation cut at its plus signs; the page does not
  say which word of the literal translation belongs to which piece, because
  that pairing is the project's own analysis (`curriculum/roots_v2`) and waits
  for review. The verb pages show Appendix 1 and the five numbered forms; no
  verb is conjugated. A practice question is made only of forms in those files.
  `node scripts/check_static_site.js` checks that every piece shown stands in
  the printed derivation.
- **A dictionary word stands in a page in both spellings, and the dictionary's is shown first.** The switch at
  the top of every page (`base.html`, "Spelling": Parks / Learner) changes it to the learner spelling. The
  choice is kept in the visitor's browser (localStorage `spelling`) and put on `<html data-spelling>`; a style
  rule hides the other spelling (`.when-parks`, `.when-learner`). The server holds no preference, so the
  app and the published site behave alike. Write a word with the filters of `spelling.py` in a template
  and with `Skiri.spell()` in a script, never by choosing one spelling in code. A word found only in the
  textbook has one spelling. The lessons' dialogues and phrases stay as the textbook prints them, and
  the pages on word building, the word web and verbs stay in the dictionary's spelling and say so.
- **The word web draws what the word-building page lists, and no more.** A box
  is an entry (headword and first meaning, whole or cut short with a mark), an
  oval is a piece of its printed derivation, and a line joins the two only
  where the dictionary prints that piece in that word. Words hang on one oval
  when the piece is printed with the same letters; the page says that the same
  letters are not always the same piece, keeps apart pieces printed with
  different letters, and does not say what a piece means. Where a shape sits
  carries no meaning. The same start always gives the same picture.
- **A lesson page keeps the book's order** (basic words, dialogues, more
  words, useful phrases, notes) and cites the page numbers printed in the
  book. Its "Say it" and phonetic form are the dictionary entry's and stand
  under the heading "In the Skiri dictionary"; a Blue Book word tied to an entry as
  a form of its stem (*ti•'at*, a form of *at*) gets the link and no
  pronunciation. Its Useful Phrases come from `curriculum/everyday_phrases.json`,
  not from the Blue Book table. One visible line on each lesson, flashcard and
  phrases page says which spelling to learn to write
  (`templates/_spelling_line.html`).
- **The textbook's Pawnee carries its dialect.** A form shows the textbook's
  own mark, SK or SB, where the page has one, and "SB spelling" where it is
  written with *e* or *hr* (`_dialect_line.html` says why, in the textbook's
  words). The app does not respell such a form and works out no Skiri form;
  where a word is tied to a dictionary entry, the entry is the Skiri word.
- **Sound is linked, never stored.** "Hear it at Indiana University" opens a
  search for the word in that university's online Skiri dictionary
  (`Skiri.hearUrls` in `static/js/skiri.js`). The search key is the longest
  run of plain letters of the headword; it is never shown as a form. Words
  found only in the textbook have no such link.
- **"Learn with others" lists only what the register allows**
  (`sources/catalogue.json`): a source marked for learners, never one marked
  as ceremonial, and no e-mail address. The catalogue's scores are not shown.
- **Spaced practice is kept in the visitor's browser** (`Skiri.box`,
  localStorage `practice-box`): a right answer on a word that is due moves it
  one of five boxes up (back after 1, 3, 7, 14, 30 days), a miss sends it to
  the first. The Practice page and the flashcards' "Got it" / "Missed" feed
  the same box. Nothing is sent to a server, and the box holds entry ids,
  never forms. The local app's `/study` (`srs.py`) is a separate scheduler.
- The pages are always shown in the light theme (`data-theme="light"` in
  `base.html`). New styles must not switch colours on the visitor's system
  setting: the tokens `--learn-*` in `pawnee-theme.css` are fixed for that reason.
- A dictionary verb is passed by its entry id, never by its spelling.
- A flashcard week that is held for review is not served: `/flashcards/<week>` answers "not found" for it.
- Feedback is never applied automatically. It waits in `/admin/feedback` for
  a person to accept or reject it. With no hosted app, feedback can only be
  entered by someone running the app locally; visitors to the public site
  send corrections as GitHub issues.
- Every feedback submission is also written to `exports/community_feedback.json`
  so that it reaches git.
