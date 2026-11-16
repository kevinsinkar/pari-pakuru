# sources/

The register of sources: what else there is on the Pawnee language beyond the
two books this project copies forms from, and how the project may use each.

| File | What it is | Edit by hand? |
|---|---|---|
| `catalogue.json` | 59 records. The fields before `project` are copied from a catalogue the project's owner brought on 2026-11-15; under `project` stand this project's own decisions | Only the `project` part |
| `rating_key.json` | The catalogue's second sheet: its scale of credibility (1 to 5) and its compiler's notes on spelling, dialect, rights and cultural protocol | No |

The catalogue itself is a spreadsheet, `Skiri Pawnee Language Sources.xlsx`,
kept in the root of the working folder and **out of git**: it carries notes
written to the owner and an e-mail address. `scripts/sources_catalogue.py`
reads it and cuts the address out.

## What the catalogue is, and how far to trust it

It says of itself: "Compiled November 15, 2026, from web searches. Ratings are
my judgment against the scale above." Most archival items are described from
their catalogue entries, not from the items. So:

- The scores are one person's judgement. They are kept in the file and are
  not shown on the site. They help decide what a learner page lists.
- **Nothing goes on a public page on the catalogue's word alone.** A source
  is listed for learners only when its link answers and `project.checked.seen`
  records what its page was seen to say, by whom ever opened it, with the date.
  On 2026-11-15 three of the catalogue's links were dead or had moved (the
  Alphabet Book, the page on the 1997 course, the Nation's archive portal).

## The three doors

A source comes into the project by one of three doors. The register records
which, in the `project` part of each record.

| Door | What it means | Field |
|---|---|---|
| **Link** | The site points to it. Nothing of it is copied | `link`, and `section` if a learner page lists it |
| **Check** | It is used to verify or label what the project already holds. What is stored is the project's finding and the citation, not the source's content | `check` |
| **Copy** | Forms, sentences or sound enter the database or the site | `copy`: `source` for the two books; `ask` where the content is wanted and permission has to be asked first; `no` otherwise |

`sensitive` marks ceremonial material and what is bound up with it (song
archives, sacred narrative, doctoring). Such a source is never listed for
learners and never copied; whether it may be named at all is the Pawnee
Nation's to say. The first import marks a record by keywords; seven more were
marked by hand on 2026-11-15. The mark is the project's caution, not a
judgement of the works.

Until permission is given in writing, only the first two doors are open, for
every source. The two books themselves are in copyright: the register's notes
on `parks` and `blue_book` say what was found and what the owner decided.

## Fields of `project`

| Field | Meaning |
|---|---|
| `link` | The site may link to it |
| `section` | Where the page "Learn with others" lists it: `nation`, `hear`, `read`; `null` = not listed |
| `url` | Its address, where the catalogue's no longer answers. The catalogue's own stays in the record |
| `check` | What the project uses it to check |
| `copy` | `source`, `ask` or `no` (see above) |
| `sensitive` | Ceremonial: held |
| `note` | Anything a later reader should know |
| `checked` | `on` (date the link was last tried), `status` (what came back), `final_url` (if it redirects), `seen` (what the page was seen to say) |

## Commands

```bash
python scripts/sources_catalogue.py                 # what an import of the spreadsheet would change
python scripts/sources_catalogue.py --apply         # write catalogue.json; the project's fields are kept
python scripts/sources_catalogue.py --check-links   # try every link once, record the result
python scripts/sources_catalogue.py --load-db --apply   # the table `sources` of the database, from the file
python scripts/sources_catalogue.py --check         # exit 0 if the register is sound
python scripts/sources_catalogue.py --list          # what the learner page lists
```

A link that answers 403, 418 or 429 belongs to a site that turns automated
clients away (the American Philosophical Society, the Smithsonian repository,
WorldCat and others). It is probably sound; only a reader can say.

## State on 2026-11-15

59 records: the 2 books; 8 listed for learners (the Pawnee Nation's language
programme, its Facebook page, the recordings of its classes, its lesson
handouts, the 1997 Skiri course, Indiana University's dictionary with sound, a
podcast with the programme's teachers, the Alphabet Book); 6 whose content is
wanted and has to be asked for; 18 held as ceremonial. Links: 40 answer, 15
turn automated clients away, 1 is Facebook, 2 give no answer (the Nation's
archive portal, the Pawnee Nation College), 1 record has no link.
