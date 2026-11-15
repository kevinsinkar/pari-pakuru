# docs/ — the public static site (generated)

**Do not edit these files by hand.** This folder is written by
`scripts/build_static_site.py` from the database and the templates in `web/`,
and GitHub Pages serves it as it is on every push to `main`.

To change the site, change the data or the templates, rebuild, and commit the
result. See [../DEPLOYMENT.md](../DEPLOYMENT.md).

| Item | What it is |
|---|---|
| `index.html`, `about.html` | Home with search and the ways to learn; about |
| `learn.html` | "Start here": seven steps for a new learner |
| `guide.html` | "Sounds": the letters, what the dictionary says of them, and any flashcard word taken syllable by syllable |
| `words.html` | "Word building": the pieces the dictionary prints for a word, and the words that share a piece |
| `verbs.html` | "Verbs": the five forms of a verb entry, the seven verbs of Appendix 1 in full, Parks's tables |
| `practice.html` | Six practice games over printed forms, and "Today": the flashcard words that are due again (kept in the visitor's browser) |
| `topics.html` | The dictionary's words by topic |
| `flashcards.html`, `flashcard-N.html` | The weekly flashcard sets. A week held for review (now week 20) has no page |
| `lessons.html`, `lesson-1.html` … `lesson-20.html` | The Blue Book lessons, each in the book's order: basic words, dialogues, more words, useful phrases, notes, exercises |
| `phrases.html` | The lessons' Useful Phrases gathered by situation, and the two conversations of lesson 20 |
| `data/dictionary.json` | Every dictionary entry, searched in the browser |
| `data/wordbuilding.json`, `data/verbs.json`, `data/practice.json` | What the word-building, verbs, practice and sounds pages read (`web/learning.py`) |
| `printables/` | Two documents for paper, copied from `curriculum/printables/`: the word list and the seven verbs |
| `static/` | CSS and the scripts of the pages |
| `.nojekyll` | Tells GitHub Pages to serve the files untouched |

The folder is called `docs` because GitHub Pages expects that name. Project
documentation is in the repository root and in each folder's `README.md`.
