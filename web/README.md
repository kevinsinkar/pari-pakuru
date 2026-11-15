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
| `app.py` | Routes, template filters (the accented syllable shown in capitals, spelling preference), the lesson exercises, the feedback export |
| `db.py` | Database access. Builds on `DB/query_api.py`. The dictionary is opened read-only; a second, writable connection serves feedback and study progress |
| `search.py` | Language detection, full-text search, fuzzy matching for misspellings |
| `search_ranking.py` | Orders results: exact matches first, Blue Book words boosted |
| `flashcards.py` | The weekly flashcard sets. `load_sets()` serves the frozen `curriculum/flashcard_sets.json` and leaves out any week listed in `curriculum/held_for_review.json`; use it, not `generate_all_sets()`, in anything a learner sees |
| `srs.py` | Spaced-repetition scheduling (SM-2) for `/study` |
| `learning.py` | What the learning pages show (word building, verbs, practice, topics), for the app and for the static build alike. It copies printed forms and arranges them: `split_derivation()` cuts a derivation of the dictionary at its plus signs, `verbs_data()` reads Appendix 1 and 2 and the tables of chapter 4, `practice_data()` the flashcard weeks. It makes no form, and leaves out the entries tagged `ceremony` |
| `templates/` | Jinja templates. Files starting with `_` are fragments included by others |
| `static/` | CSS and the scripts. `js/search.js` is the search of the published site: it runs in the visitor's browser over `docs/data/dictionary.json` and shows the whole entry, with a link for sending a correction (the local app searches on the server and does not use it). `js/skiri.js` holds what the learning pages share: a phonetic form cut at its syllable dots with a hint for each symbol, and the pieces of a derivation as a row of chips. `js/words.js`, `verbs.js`, `practice.js`, `sounds.js` and `topics.js` each drive one page |

The routes are listed in the [quick reference](../Quick_Reference_Guide.md#web-app-routes).

## What it imports from `scripts/`

`printed_noun_forms.py` (the box "Printed forms of this noun"),
`example_filter.py` (which Blue Book sentences an entry page shows) and
`sentence_templates.py` (the sentence builder; it brings in `person_forms.py`
and `template_slot_fillers.py`). Changing those changes the app.

## How it reaches the public

Only through the static site: `scripts/build_static_site.py` renders a subset
of these templates into `docs/` and rewrites the links: home, about, the
learning pages (`learn.html` "Start here", `guide.html` "Sounds", `words.html`,
`verbs.html`, `practice.html`, `topics.html`), flashcards and lessons. See
[../DEPLOYMENT.md](../DEPLOYMENT.md). When you change one of those templates,
rebuild the site, run `node scripts/check_static_site.js` and look at the
result.

The learning pages read their data in the browser from `data/wordbuilding.json`,
`data/verbs.json` and `data/practice.json`. The static build writes those files;
the local app serves the same data at `/data/<name>.json`. `topics.html` exists
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
