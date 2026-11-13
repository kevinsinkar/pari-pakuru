# web/

The Flask web app (Flask, SQLite, Pico CSS, HTMX). It reads
`skiri_pawnee.db` from the repository root.

```bash
.venv/Scripts/python -m web.app            # http://localhost:5000
.venv/Scripts/python -m web.app --port 8080 --debug
```

| File | What it does |
|---|---|
| `app.py` | Routes, template filters (pitch display, spelling preference), the lesson exercises, the feedback export |
| `db.py` | Database access. Builds on `DB/query_api.py`. The dictionary is opened read-only; a second, writable connection serves feedback and study progress |
| `search.py` | Language detection, full-text search, fuzzy matching for misspellings |
| `search_ranking.py` | Orders results: exact matches first, Blue Book words boosted |
| `flashcards.py` | The weekly flashcard sets. `load_sets()` serves the frozen `curriculum/flashcard_sets.json` and leaves out any week listed in `curriculum/held_for_review.json`; use it, not `generate_all_sets()`, in anything a learner sees |
| `srs.py` | Spaced-repetition scheduling (SM-2) for `/study` |
| `templates/` | Jinja templates. Files starting with `_` are fragments included by others |
| `static/` | CSS and `js/search.js` (the in-browser search the static site uses) |

The routes are listed in the [quick reference](../Quick_Reference_Guide.md#web-app-routes).

## What it imports from `scripts/`

`possession_engine.py`, `example_filter.py`, `sentence_templates.py` (which
brings in `person_forms.py`, `template_slot_fillers.py`, `display_utils.py`).
Changing those changes the app.

## Two ways it is published

The same templates serve both the hosted app and the static site:
`scripts/build_static_site.py` renders a subset of them into `docs/` and
rewrites the links. See [../DEPLOYMENT.md](../DEPLOYMENT.md). When you change a
template, check both.

## Rules the app keeps

- IPA is shown only when Parks prints it for that word.
- A generated form is always marked as generated, with a confidence level.
- A flashcard week that is held for review is not served: `/flashcards/<week>` answers "not found" for it.
- Feedback from visitors is never applied automatically. It waits in
  `/admin/feedback` for a person to accept or reject it.
- Every feedback submission is also written to `exports/community_feedback.json`
  so that it reaches git.
