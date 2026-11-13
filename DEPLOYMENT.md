# Deployment

The project is published in two ways. Both read the same database.

| | Static site | Hosted web app |
|---|---|---|
| Where | GitHub Pages, from the [docs/](docs/) folder | PythonAnywhere, running [web/](web/) through [wsgi.py](wsgi.py) |
| What it offers | Search, Blue Book lessons, weekly flashcards, pronunciation guide | Everything: entry pages, sentence builder, spaced-repetition study, feedback, dashboard |
| Needs a server | No | Yes |
| Updated by | Rebuilding `docs/` on your machine and pushing | Pulling the code and uploading the database |

## Static site (GitHub Pages)

### How it works

1. `scripts/build_static_site.py` reads `skiri_pawnee.db` and writes the site into `docs/`:
   - `data/dictionary.json`: all 4,337 entries with headword, learner spelling, IPA, respelling, class, page number, senses and examples;
   - `index.html`, `about.html`, `guide.html`;
   - `flashcards.html` and one `flashcard-N.html` for each weekly set in the frozen `curriculum/flashcard_sets.json` that is not held for review (23 of 24);
   - `lessons.html` and `lesson-1.html` to `lesson-20.html`;
   - `static/` (CSS and `search.js`).
2. Search runs in the browser: `search.js` loads `dictionary.json` once and searches it with Fuse.js. There are no per-entry pages; a search result shows the entry.
3. `.github/workflows/static.yml` runs on every push to `main`. It uploads `docs/` as it is and deploys it. **It does not build anything**, because the database is not in git.

So the site changes only when you rebuild `docs/` locally and push the result.

### Update the site

```bash
.venv/Scripts/python scripts/build_static_site.py --dry-run   # show what would be built
.venv/Scripts/python scripts/build_static_site.py             # write docs/
cd docs && python -m http.server 8000                         # look at it: http://localhost:8000/
git add docs && git commit -m "Rebuild static site" && git push
```

The site uses relative links, so it works from the repository's Pages address
(`https://<user>.github.io/pari-pakuru/`) without any base-path setting.
`docs/.nojekyll` stops GitHub from running Jekyll over the files.

### First-time setup on GitHub

Repository **Settings → Pages → Source: GitHub Actions**. Nothing else is needed.

### What the static site cannot do

- No feedback form, no study progress on a server, no sentence builder, no dashboard. Those need the hosted app.
- Flashcard progress is kept in the visitor's browser, keyed to week numbers. That is why the flashcard sets are frozen: see [curriculum/README.md](curriculum/README.md).
- The "word of the day" is whatever word was chosen when the site was last built.

### Before you publish

- Do not publish ceremonial vocabulary that the community has not reviewed. Flashcard Week 20 ("Ceremony & Sacred") is held back: it is listed in `curriculum/held_for_review.json`, so the app returns "not found" for it and the build writes no page for it (and removes an old one). To release a week, delete its entry from that file and rebuild. Week numbers never change, so learners' saved progress is not disturbed either way ([reports/audit_data_construction_2026-10-01.md](reports/audit_data_construction_2026-10-01.md), item B6).
- The word-building guide in `curriculum/roots_v2/` is **not** on the site. Putting it there is a publishing decision, not a build step.

## Hosted web app (PythonAnywhere)

`wsgi.py` is the entry point. In PythonAnywhere's **Web** tab:

| Setting | Value |
|---|---|
| WSGI file | `/home/<username>/pari-pakuru/wsgi.py` |
| Source code and working directory | `/home/<username>/pari-pakuru` |
| Static files | URL `/static/` → `/home/<username>/pari-pakuru/web/static` |

`requirements.txt` lists what the app needs (Flask).

The database is not in git, so upload `skiri_pawnee.db` to the project root
separately. `wsgi.py` points the app at it through the `SKIRI_DB_PATH`
environment variable.

### Update the hosted app

1. Back up the database on the server if it holds feedback or study progress that your local copy does not.
2. `git pull` on the server.
3. Upload the new `skiri_pawnee.db` if the data changed.
4. Press **Reload** in the Web tab.

Feedback that visitors submit is written to the server's database and exported
to `exports/community_feedback.json` after each submission, so that it can be
committed. It is the one table that cannot be rebuilt from the sources.

## Run locally

```bash
.venv/Scripts/python -m web.app          # http://localhost:5000
```
