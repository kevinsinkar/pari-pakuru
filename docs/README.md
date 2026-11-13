# docs/ — the public static site (generated)

**Do not edit these files by hand.** This folder is written by
`scripts/build_static_site.py` from the database and the templates in `web/`,
and GitHub Pages serves it as it is on every push to `main`.

To change the site, change the data or the templates, rebuild, and commit the
result. See [../DEPLOYMENT.md](../DEPLOYMENT.md).

| Item | What it is |
|---|---|
| `index.html`, `about.html`, `guide.html` | Home with search, about, pronunciation guide |
| `flashcards.html`, `flashcard-N.html` | The weekly flashcard sets. A week held for review (now week 20) has no page |
| `lessons.html`, `lesson-1.html` … `lesson-20.html` | The Blue Book lessons |
| `data/dictionary.json` | Every dictionary entry, searched in the browser |
| `static/` | CSS and the search script |
| `.nojekyll` | Tells GitHub Pages to serve the files untouched |

The folder is called `docs` because GitHub Pages expects that name. Project
documentation is in the repository root and in each folder's `README.md`.
