# pari pakuru/

**Source material.** *Pari Pakuru'*, the "Blue Book": the textbook of spoken
Pawnee published by the Pawnee Cultural Retention Committee in 1979. Twenty
lessons of dialogues, vocabulary and grammar notes, 130 pages.

The folder name has a space in it and is hard-coded in many scripts. Do not
rename it.

| Item | What it is |
|---|---|
| `Blue Book - Pari Pakuru.pdf` | The scanned book |
| `Blue_Book_Pari_Pakuru.txt` | Its text, 130 pages. **This is the file the scripts read** |
| `Blue Book - Pari Pakuru - split/` | The book as 130 single-page PDFs |
| `blue_book_split.py` | The small script that cut the PDF into pages |

## Things to know

- **The text file is a scan read by OCR.** It has errors, most often `1` or `J`
  for `I` in capitals, and two-column vocabulary lists whose columns ran
  together (Lessons 3 and 4). Scripts that read it are conservative, and a
  doubtful reading is left as printed.
- **The Blue Book has its own spelling**: `ts` where Parks writes `c`, `'` for
  the glottal stop, and a dot `•` between the parts of a long word. Blue Book
  forms are always quoted as printed and never respelled into Parks's system.
- **`?` is a letter here.** `ka?` is the yes/no question word. Do not "repair" it.
- **The dots mark word-building seams**, and Lesson 3 (pages 41 to 42,
  "Combining roots") states the sound rules that apply at those seams. The
  word-construction analysis uses both as evidence.

## What was taken from it

| Into | By |
|---|---|
| `blue_book_attestations` (vocabulary by lesson, linked to dictionary entries where a match is certain) | `scripts/blue_book_verify.py`, `scripts/link_bb_vocab.py` |
| `lessons` and `extracted_data/lessons.json` | `scripts/build_lessons.py` |
| 93 words found only here, added as entries with ids `BB-…` | `scripts/import_bb_items.py` |
| 88 dialogue sentences added to `examples` | `scripts/blue_book_verify.py` |
| Ten sentence templates | `scripts/sentence_templates.py` |
