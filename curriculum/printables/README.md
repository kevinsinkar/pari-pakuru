# curriculum/printables/

Two documents for use away from a screen. Both are generated; to change one,
change the data or `scripts/build_printables.py` and build again.

| File | What it is |
|---|---|
| `word_list.pdf`, `word_list.html` | The flashcard words week by week, as a list: the word as the dictionary spells it, the learner spelling, a rough guide to saying it, the meaning, and the page of the dictionary. 372 words in 23 weeks; the week held for community review is left out |
| `paradigm_tables.pdf`, `paradigm_tables.html` | Parks's Appendix 1, "Illustrative Skiri Verb Conjugations": seven verbs (to come, to do it, to go, to be good, to drink it, to be sick, to have it), each in ten modes and eleven persons, 770 forms, as corrected from the printed page in November 2026. Landscape |

```bash
python scripts/build_printables.py            # needs PyMuPDF and the DejaVu fonts for the PDFs
python scripts/build_printables.py --no-pdf   # the web pages only; they print well from a browser
```

## Things to know

- **Nothing here is computed.** The words come from the database, the verb
  forms from `extracted_data/appendix1_conjugations.json`.
- **The word list has not been reviewed by a speaker**, and says so on its
  first page. It is the same list as the flashcards; Part 2 of the review
  packet ([../../community_review/](../../community_review/)) asks about it.
- The first three weeks hold words taken from the Blue Book. 37 of the
  project's Blue Book entries are words the dictionary has with a long vowel
  the textbook does not write (project log, open item 52), so a few words in
  those weeks are shown shorter than the dictionary spells them.
- The appendix's persons are labelled here in plain English ("we two (not
  you)" for the first person dual exclusive). The stored file also has an
  English line for every form; those were written by the extraction, not by
  Parks, and are not printed.
- Neither document is linked from the public site yet.
