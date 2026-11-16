# extracted_data/

Structured data taken from the two sources by a script, saved as JSON so that
the step does not have to be repeated. Most of these came from an AI reading of
scanned pages. Treat them as generated: to change one, change and re-run its
script.

| File | Contents | Made by | Read by |
|---|---|---|---|
| `abbreviations.json` | Parks's 164 abbreviations and the sound key | `scripts/extract_appendices.py` | `morpheme_inventory.py` |
| `appendix1_conjugations.json` | Appendix 1: seven verbs conjugated in full (770 forms) | `scripts/extract_appendices.py` | `morpheme_inventory.py`, `person_forms.py` |
| `appendix2_irregular_roots.json` | Appendix 2: nine verb roots with irregular dual or plural stems | `scripts/extract_appendices.py` | `morpheme_inventory.py` |
| `appendix3_kinship.json` | Appendix 3: 23 kinship terms with their "my / your / his" forms | `scripts/extract_appendices.py` | the table `kinship_paradigms` was filled from it; `scripts/printed_noun_forms.py` shows that table on entry pages |
| `grammatical_overview.json` | Parks's chapter 4, the grammatical overview, page by page with its tables and worked examples | `scripts/extract_appendices.py` | `morpheme_inventory.py`, `noun_possession.py`, the word-construction analysis |
| `grammatical_overview_tables.json` | The 14 tables of chapter 4 as printed, row by row, put together from the two blind readings of the chapter. Twelve read the same in both; tables 6 and 7 are given in both readings. **Use this file for a table** | `scripts/source_audit/chapter4_tables.py --write` | nothing yet |
| `sounds_and_alphabet.json` | Parks's chapter 2 (pp. 13-17): its 138 Skiri forms with the phonetic form and gloss printed beside them, tables 2 and 3, and a summary of each section in the project's words. Not the chapter's running text | `scripts/source_audit/front_matter_reading.py --write` | nothing yet; cited by the review packet and the engines prompt |
| `organization_of_the_dictionary.json` | Parks's chapter 5 (pp. 53-60): its 57 Skiri forms, the figure captions, and a summary of each section, among them his definition of the five verb forms | the same script | nothing yet |
| `grammar_retry_results.json`, `grammar_failed_pages_transcriptions.json` | Four pages of chapter 4 (1, 3, 7, 16) that the first extraction lost, recovered as plain text | `archived/scripts/retry_failed_grammar.py` | merged into the file above by `archived/scripts/merge_grammar_retries.py` |
| `dual_plural_analysis.json` | An AI analysis of the dual and plural forms in Appendix 1, piece by piece. Working notes for the conjugation engine | `archived/scripts/analyze_dual_plural.py` | nothing |
| `blue_book_dialect_statements.json` | What the textbook says of its own two dialects: the contents page and the chapter "The Pawnee Alphabet" (pp. xviii-xxiv): 12 statements with their pages and the book's own examples, and the six things a Skiri reader is told (*e* is said *i*, *hr* is said *h*, the accent marks are South Band) | read from the scan on 2026-11-15, one reading (the front matter was not part of the lessons' reading) | `web/learning.py` (the dialect line of the lesson pages), `scripts/label_bluebook_dialect.py`, `scripts/build_review_packet.py` |
| `blue_book_extracted.json` | 985 vocabulary items and sentences from the Blue Book, by lesson (984 from the extraction; one line it left out was added on 2026-11-15, when 16 items also got the English of their own row of the page) | `scripts/blue_book_verify.py --extract-only` | `blue_book_verify.py`, `noun_possession.py` |
| `blue_book_glossary.json` | The Blue Book's glossary (book pages 95-102) item by item: 573 English terms with the pages they point to, each reference checked against that page, and the Pawnee forms the database holds for it. The glossary itself prints no Pawnee | `scripts/bluebook_glossary.py --write` | nothing yet |
| `lessons.json` | The 20 Blue Book lessons: titles, pages, dialogues, grammar notes. A copy of the `lessons` table; `scripts/fix_lesson_text_ocr.py --check` and `scripts/apply_lesson_page_reading.py --check` fail if it is not. Since 2026-11-14 the Pawnee of titles, dialogues and notes is as read from the scan line by line; the notes of lesson 20 no longer end in the glossary | `scripts/build_lessons.py`, then `scripts/fix_lesson_text_ocr.py`, then `scripts/apply_lesson_page_reading.py` | nothing; kept so the lessons are in git |

## Things to know

- **Chapters 2 and 5 are stored without their running text, on purpose** (2026-11-14). The book is in copyright, and the
  project needs what the chapters establish, not their sentences. Each section has a summary in the project's own
  words; it is not Parks's text. The sentences under `quoted` are his, and carry their page. Every Skiri form was read
  twice from the page images and stands letter for letter in both readings.
- **`appendix1_conjugations.json` has an English line for every form** ("he have it"). Those lines were written by the
  extraction, not by Parks. Do not print them as his; `scripts/build_printables.py` leaves them out.

- **These files were compared with the pages in full on 2026-11-13 and
  corrected the same day.** A second reader transcribed the pages without
  seeing these files
  ([../reports/source_audit_2026-11/findings.md](../reports/source_audit_2026-11/findings.md));
  the changes are listed in `../reports/source_audit_2026-11/applied_fixes_report.txt`.

  | File | What was wrong | Now |
  |---|---|---|
  | `appendix1_conjugations.json` | 152 of 770 forms: accents the page does not have, vowels dropped or doubled, one block shifted by a row | all 152 corrected, each after a third look at the page |
  | `appendix2_irregular_roots.json` | *burii-waa* and *burii* for printed *hurii-waa* and *hurii*; one stem stored where the cell is empty | the two forms corrected. The singular of *tir* 'to be together' is still stored though the cell is empty in print; it was left for a person. (It was left because the conjugation engine was thought to read it. It does not: no engine reads this file, as the engines review of 2026-11-14 found) |
  | `appendix3_kinship.json` | *asaas*, *atipaat*, *apaat* for printed *asas*, *atipat*, *apat*; the five rows of book page 543 missing | corrected; the five rows added |
  | `grammatical_overview.json` | 85 of 797 Skiri words: 34 with a `b` where the page has an `h` (*-busuukuʔ* is *-husuukuʔ*), the rest differing by an accent, a vowel or a glottal stop | the 34 corrected, and after them the forms a second letter check still found (*-:hus*, *-hus*, *tihurás*, *ratkuhurasi*, *tuksuhuuhwiitit*); no `b` is left in a Skiri form. **51 words are not corrected**: they were matched to the second reading by likeness, not by position, and need a person with the page (`../reports/source_audit_2026-11/chapter4_differences.json`). Three of them were corrected on 2026-11-14, where the blind reading is a form the dictionary prints and the stored one is printed nowhere (*askatahciriʔ*, *iriirapahaatu*, *tuctiraahawista*); what each witness says about the others is in `chapter4_third_witness.json`). **Settled on 2026-11-14 by a second blind reading of the whole chapter:** 38 words, 22 pieces of breakdown lines and Table 17 corrected to what both blind readings have; every Skiri word of the file now stands in both (`../reports/source_audit_2026-11/chapter4_second_reading.json`). The English prose is still a paraphrase, the `morphemes_mentioned` lists are the extraction's own summaries, and the tables other than Table 17 are as the extraction rebuilt them |
  | `abbreviations.json` | 4 of 411 values (*raar-/rab-* is *raar-/rah-*) | three corrected; "verb class 1-a" is printed "verb class 1: -a" and was left |
  | `blue_book_extracted.json`, `lessons.json` | Blue Book forms taken from the OCR text: no accents, about one form in seven misread | 960 strings corrected from the scan, 51 more on 2026-11-14 after a second reading, and 14 after the forms were read at their own place; 17 forms left for a person. On the evening of 2026-11-14 the lessons were read line by line: 38 values of `lessons.json`, and 19 strings of `blue_book_extracted.json` in the 13 rows that are lines of a lesson |
  | `noun_possession_catalog.json` | carried the misread kin terms and *-biriʔ* | made again from the corrected data; **removed on 2026-11-14** with the possession engine that wrote it: computed, and read by nothing |

- **`grammatical_overview.json` was read from page images by an AI model, and
  it can misread.** Until 2026-11-13 it gave Parks's locative/instrumental
  suffix as *-biriʔ* in eight places. The page has *-hiriʔ* (Grammatical
  Overview p. 30), 65 dictionary etymologies have it, and no Skiri word
  contains a `b`. Those places, and 34 more words with the same misreading,
  are corrected. For the 51 words still listed as differing, check the form
  against the PDF in `Dictionary Data/Dictionary PDF Split/` before relying on
  it.
- `blue_book_extracted.json` was moved here from the repository root on
  2026-11-13.
- The page images that were used to recover the four lost grammar pages were
  removed on 2026-11-13; they can be rendered again from the PDF, and are in
  git history at commit `2e77095`.
