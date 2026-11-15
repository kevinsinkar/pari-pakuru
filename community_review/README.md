# community_review/

The packet for the Pawnee Nation's language and culture people: what the
project asks them to look at before anything more is published. It is rank 1
of "What's next" in the [project log](../pari_pakuru_project_scope.md).

*Made for the first time on 2026-11-14. It has not been sent to anyone.*

| File | What it is | In git? |
|---|---|---|
| `review_packet.pdf` | The packet, about 40 pages, for printing or sending | No |
| `review_packet.html` | The same, as one web page | No |
| `response_sheet.csv` | One line for each word of Parts 1 and 2, with empty columns for a decision and a note; opens in any spreadsheet | No |
| `README.md` | This file | Yes |

The three built files are not in git ([.gitignore](../.gitignore)). They put
the vocabulary that is held back into one readable place, and the repository
is public; whether that belongs there is not the project's call. Build them
when they are needed:

```bash
python scripts/build_review_packet.py                # today's date on the first page
python scripts/build_review_packet.py --date 2027-01-15
```

Build it again shortly before sending: it is made from the database and the
curriculum files as they are on that day. The PDF needs PyMuPDF and the
DejaVu fonts in `C:/Windows/Fonts`; `--no-pdf` writes the page and the sheet
only, and the page prints well from a browser.

## What the packet asks

| Part | What | Why it is asked |
|---|---|---|
| 1 | Words to do with ceremony: the 15 flashcard words of the set that is held back (Week 20), and 161 more dictionary entries a keyword picked out (143 carry the site's `ceremony` mark, 176 were set aside in the word-building guide, many are on both lists) | Whether they are on a public site at all, how much of each entry is shown, and whether any may be taught, is the community's decision (open items 2 and 50) |
| 2 | The flashcard word list: 372 words in 23 weekly sets | The list was chosen by English keywords and no person has checked it (open item 3) |
| 3 | The word-building guide: what it is, whether it is welcome, and the ten open questions for a speaker or linguist | Open item 1 |
| 4 | The About page of the public site, word for word | Its wording is the project's alone (open item 47) |
| 5 | Three questions about sound and spelling: the two kinds of short i and u; the word "accent"; and *kt* against *tt*, *r* against *n* | Open items 43 and 9. The third was added when chapter 2 of the dictionary was read on 2026-11-14: Parks writes that the dictionary's *kt* follows one speaker and that all other twentieth-century Skiri speakers said *tt* |

## Before it is sent

- **Fill in the contact line** on the first page: it reads `[name], [telephone or e-mail]`.
- **The packet makes one promise:** "Whatever you decide about Part 1 will be
  done: words can be taken off the site, shown in part, or shown in full."
  That is the project's standing rule. Take the sentence out if you would
  rather not put it in writing.
- The lists in Part 1 were made by keyword and are rough both ways. The
  packet says so. If you already know words that should be on it, add them by
  hand; do not let the packet go out looking more complete than it is.
- Nothing in the packet is computed: every Pawnee word, phonetic form and
  meaning is copied from the database, which holds what the two books print.

## When answers come back

Record them where the decisions take effect, and say in the project log who
decided and when:

| Answer about | Where it takes effect |
|---|---|
| Ceremonial entries on the site | `export_dictionary_data` in `scripts/build_static_site.py` (what a `ceremony` entry shows); the `ceremony` tag itself in the `semantic_tags` table |
| Flashcard Week 20 | `curriculum/held_for_review.json` |
| Words of the flashcard list | `curriculum/flashcard_sets.json`, through `scripts/freeze_flashcard_sets.py` |
| The word-building guide | `curriculum/roots_v2/`; the review flag is `needs_community_review` in `scripts/morphology_v2/inventory.py` |
| The About page | `web/templates/about.html`, then rebuild the site |
| "Accent", tense and lax vowels, *kt* and *tt* | `web/templates/` and the pronunciation guide; the respelling rules in `scripts/fix_pronunciations.py` |
