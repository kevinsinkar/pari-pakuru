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

## What the 2026-11 audit found, and what was done

- **Everything taken from this book was taken from `Blue_Book_Pari_Pakuru.txt`,
  the OCR text, and that text is a poor copy of the scan.** The book prints an
  accent on the stressed vowel of most words (*tí kaats*, *paréku'*); the OCR
  text has none. It also misreads about one form in seven, most often an
  accented vowel as other letters (*ktitasut* for *kútasut*, *pakd* for
  *paká*). The word for "yes" was in the database as *had'*; the scan has
  *haú'*.
- **The stored forms were corrected from the scan on 2026-11-13.** Every
  distinct form that has a page (949: the audit's 153 crops and 843 more) was
  cut out of the scan and read by readers who saw only the image: 157 were
  right, 565 had their accent restored, 45 an apostrophe, dot or space
  corrected, 105 an OCR slip corrected. The corrections went into
  `blue_book_attestations`, the Blue Book examples, the lesson dialogues and
  `extracted_data/`. Record:
  `../reports/source_audit_2026-11/bluebook_applied_report.txt`.
- **77 forms are left for a person** (the same report, last section): the
  reading and the stored form differ in letters (49) or capitals (12), the
  reader was unsure (8), or the crop missed the form (8).
- **Not corrected:** `Blue_Book_Pari_Pakuru.txt` itself, which stays as the
  OCR produced it; the Blue Book forms in the tables `bb_gap_triage`,
  `bb_function_words` and `function_words`; the forms written into the
  sentence templates. These still lack the printed accents.
- The 93 Blue Book-only dictionary entries have no phonetic form. The book
  gives none; the ones the database held until 2026-11-13 had been made from
  the spelling.
- The scan's PDF has the OCR's word positions, so a form can be found on its
  page and cut out for reading: `scripts/source_audit/bluebook_crops.py` and
  `bluebook_rest.py`.
