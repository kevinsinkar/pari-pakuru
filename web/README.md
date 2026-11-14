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
| `templates/` | Jinja templates. Files starting with `_` are fragments included by others |
| `static/` | CSS and `js/search.js`: the search of the published site, which runs in the visitor's browser over `docs/data/dictionary.json` and shows the whole entry, with a link for sending a correction. The local app searches on the server and does not use it |

The routes are listed in the [quick reference](../Quick_Reference_Guide.md#web-app-routes).

## What it imports from `scripts/`

`possession_engine.py`, `example_filter.py`, `sentence_templates.py` (which
brings in `person_forms.py`, `template_slot_fillers.py`, `display_utils.py`).
Changing those changes the app.

## How it reaches the public

Only through the static site: `scripts/build_static_site.py` renders a subset
of these templates (home, about, guide, flashcards, lessons) into `docs/` and
rewrites the links. See [../DEPLOYMENT.md](../DEPLOYMENT.md). When you change
one of those templates, rebuild the site and look at the result.

Everything else here (entry pages, browse, sentence builder, study, feedback,
dashboard) is seen only by someone running the app on their own machine.

## Rules the app keeps

- IPA is shown only when Parks prints it for that word.
- A generated form is always marked as generated, with a confidence level.
- A flashcard week that is held for review is not served: `/flashcards/<week>` answers "not found" for it.
- Feedback is never applied automatically. It waits in `/admin/feedback` for
  a person to accept or reject it. With no hosted app, feedback can only be
  entered by someone running the app locally; visitors to the public site
  send corrections as GitHub issues.
- Every feedback submission is also written to `exports/community_feedback.json`
  so that it reaches git.
