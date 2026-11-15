# Deployment

The project is published in one place: the static site on GitHub Pages, built
into the [docs/](docs/) folder. Nothing else is hosted.

The Flask app in [web/](web/) is a local tool. It runs on your own machine,
and the static site is built from its templates. It was hosted on
PythonAnywhere until that was retired on 2026-11-13; see
[the note at the end](#the-retired-hosted-app).

| | Static site (published) | Flask app (local only) |
|---|---|---|
| Where | GitHub Pages, from [docs/](docs/) | `http://localhost:5000` on your machine |
| What it offers | Search, a "Start here" path, pages on sounds, word building and verbs, practice games with the words due each day, words by topic, Blue Book lessons, the textbook's phrases by situation, weekly flashcards | Everything: entry pages, sentence builder, spaced-repetition study, feedback, dashboard |
| Needs a server | No | No; you start it when you want it |
| Updated by | Rebuilding `docs/` on your machine and pushing | Nothing to do: it reads the database directly |

## Static site (GitHub Pages)

### How it works

1. `scripts/build_static_site.py` reads `skiri_pawnee.db` and writes the site into `docs/`:
   - `data/dictionary.json`: all 4,337 entries, one to a line, with everything the dictionary prints for each: headword and preverb, learner spelling, IPA, respelling, class, page of the book, senses, examples, the numbered verb forms, the other forms, the etymology, the forms cited from related languages, the stems listed under a bound stem. The 143 entries tagged `ceremony` carry senses and examples only (see "Before you publish");
   - `index.html`, `about.html`, and the learning pages `learn.html` ("Start here"), `guide.html` ("Sounds"), `words.html`, `verbs.html`, `practice.html`, `topics.html`, `phrases.html` (the lessons' Useful Phrases, written into the page from `curriculum/everyday_phrases.json`);
   - `data/wordbuilding.json`, `data/verbs.json`, `data/practice.json`, which those pages read in the browser: the derivation the dictionary prints for an entry, cut at its plus signs (entries tagged `ceremony` left out); Appendix 1 and 2 and the tables of chapter 4; the flashcard words. All of it is copied from the database and `extracted_data/` by `web/learning.py`; no form is made;
   - `printables/word_list.pdf` and `printables/paradigm_tables.pdf`, copied from `curriculum/printables/` (build them first with `scripts/build_printables.py` when the data has changed);
   - `flashcards.html` and one `flashcard-N.html` for each weekly set in the frozen `curriculum/flashcard_sets.json` that is not held for review (23 of 24);
   - `lessons.html` and `lesson-1.html` to `lesson-20.html`;
   - `static/` (CSS, `search.js`, and the scripts of the learning pages).
2. Search runs in the browser: `search.js` loads `dictionary.json` once and searches it with Fuse.js, in headwords, senses, example translations and verb forms. There are no per-entry pages; a search result shows the entry, with the rest of it behind "More from this entry", and a "Send a correction" link that opens a GitHub issue with the entry filled in.
3. `.github/workflows/static.yml` runs on every push to `main`. It uploads `docs/` as it is and deploys it. **It does not build anything**, because the database is not in git.

So the site changes only when you rebuild `docs/` locally and push the result.

### Update the site

```bash
.venv/Scripts/python scripts/build_static_site.py --dry-run   # show what would be built
.venv/Scripts/python scripts/build_static_site.py             # write docs/
node scripts/check_static_site.js                             # runs the pages' code against the new data and checks the learning pages and every link (needs Node.js)
cd docs && python -m http.server 8000                         # look at it: http://localhost:8000/
git add docs && git commit -m "Rebuild static site" && git push
```

Every build draws a new random sample of exercise items for each lesson, so
all twenty `lesson-N.html` files show a one-line difference after a rebuild
even when no data changed. That difference is harmless; commit it or restore
those files, as you prefer.

The site uses relative links, so it works from the repository's Pages address
(`https://<user>.github.io/pari-pakuru/`) without any base-path setting.
`docs/.nojekyll` stops GitHub from running Jekyll over the files.

### First-time setup on GitHub

Repository **Settings → Pages → Source: GitHub Actions**. Nothing else is needed.

### What the static site cannot do

- No feedback queue, no study progress on a server, no sentence builder, no
  per-entry pages, no dashboard. Those exist only in the local Flask app, so
  no visitor can reach them. Corrections from visitors come in as GitHub
  issues: every search result and the About page link to a new issue. The
  address of the repository is written in two places, `web/static/js/search.js`
  (`CORRECTIONS_URL`) and `web/templates/about.html`.
- Nothing computed is shown. The forms the engines work out (possession,
  conjugation, sentences) stay in the local app.
- Flashcard progress is kept in the visitor's browser, keyed to week numbers. That is why the flashcard sets are frozen: see [curriculum/README.md](curriculum/README.md).
- The "word of the day" is whatever word was chosen when the site was last built.

### Before you publish

- Do not publish ceremonial vocabulary that the community has not reviewed. Flashcard Week 20 ("Ceremony & Sacred") is held back: it is listed in `curriculum/held_for_review.json`, so the app returns "not found" for it and the build writes no page for it (and removes an old one). To release a week, delete its entry from that file and rebuild. Week numbers never change, so learners' saved progress is not disturbed either way ([reports/audit_data_construction_2026-10-01.md](reports/audit_data_construction_2026-10-01.md), item B6).
- Entries tagged `ceremony` in `semantic_tags` (143, chosen by keyword) show their senses and examples, as they did before, and not the verb forms, etymology or cited forms that were added to the site on 2026-11-14. The build leaves those out of `dictionary.json` and the result says why. To change that, edit `export_dictionary_data` in `scripts/build_static_site.py`; whether these entries are shown at all is a question for the community review.
- The word-building guide in `curriculum/roots_v2/` is **not** on the site. Putting it there is a publishing decision, not a build step.

## Run the Flask app locally

```bash
.venv/Scripts/python -m pip install -r requirements.txt   # Flask
.venv/Scripts/python -m web.app                            # http://localhost:5000
```

Use it to look up full entries, to try the sentence builder, and to check a
template before rebuilding the site. Feedback entered in the local app is
written to your database and exported to `exports/community_feedback.json`.

## The retired hosted app

Until 2026-11-13 the Flask app was also hosted on PythonAnywhere, through a
`wsgi.py` in the repository root. That hosting is no longer in use, and
`wsgi.py` and the instructions for it were removed (they are in git history
before that date).

If the PythonAnywhere account still exists, check that the web app there is
disabled or deleted. Nothing from this repository was uploaded to it on or
after 2026-11-13, so unless someone updated it by hand its copy of the code
and database predates that day's corrections: it would have the uncorrected
forms, and it would still serve flashcard Week 20, which is held for
community review everywhere else. Removing it is done in the PythonAnywhere
dashboard; nothing in this repository can do it.
