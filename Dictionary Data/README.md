# Dictionary Data/

**Source material.** Parks & Pratt, *A Dictionary of Skiri Pawnee* (2008), as
PDF, and the two JSON dictionaries that were parsed from it.

The folder name has a space in it and is hard-coded in many scripts. Do not
rename it.

| Item | What it is |
|---|---|
| `skiri_to_english_respelled.json` | **Current.** The Skiri-to-English section: 4,273 entries with headword, IPA, class, senses, etymology, verb forms, examples, plus the derived `normalized_form` and `simplified_pronunciation`. Corrected from the printed page on 2026-11-13; phonetic forms in Parks's own symbols. For the 4,244 entries it shares with the database, headword, phonetic form, respelling and learner spelling are identical to the database's |
| `english_to_skiri_linked.json` | **Current.** The English-to-Skiri section: 6,414 English headwords, each subentry linked to a Skiri entry by `s2e_entry_id`. Phonetic forms were brought to Parks's symbols with the entries they link to; 295 of 5,399 still show the older notation |
| `Dictionary PDF Split/` | The book cut into its parts: front matter (abbreviations and sound key, sounds and alphabet, major sound changes, grammatical overview, organisation of the dictionary), the two dictionary sections, and the three appendices. Also two text files, `parks_sound_changes_ocr.txt` and `parks_grammatical_overview_ocr.txt`, with the text of chapters 3 and 4 |
| `split_pdf_pages_SKIRI_TO_ENGLISH/` | The Skiri-to-English section, one PDF per page: `page_001.pdf` to `page_181.pdf` |
| `split_pdf_pages_ENGLISH_TO_SKIRI/` | The English-to-Skiri section, one PDF per page |

## Things to know

- **The JSON files are changed only by scripts**, each with a preview mode and a
  backup. They are kept in step with the database for the dictionary's own
  fields. They do not contain what was added to the database later (the 93
  Blue Book-only words, tags, lessons).
- **Page numbers.** A Skiri-to-English page file `page_NNN.pdf` is printed book
  page NNN + 348. Since 2026-11-14 the `page_number` stored with a
  Skiri-to-English entry is the book page (`scripts/fix_page_citations.py`);
  the number inside an entry id is the old one and may be a file number.
- **The page PDFs have a text layer.** `reports/_s2e_page_index.json` holds that
  text by page. It is the typesetter's own text, and the best check there is
  on the parse. Two cautions, both learned in the 2026-11 audit:
  it is **not independent** of the parse (the AI model was given these PDFs
  and its output carried the text layer's stand-in characters, so an error in
  decoding those characters is shared by both); and what a character code
  stands for **depends on its font**. The verified table is
  `scripts/source_audit/chartable.py`; the decoded pages, with fonts and
  positions, are rebuilt by `scripts/source_audit/decode_pages.py`.
- **`english_to_skiri_linked.json` is cleaner than the database's copy of it.**
  The database tables `english_index` and `cross_references` were loaded from
  an earlier file. The JSON itself still has about 400 placeholder values
  ("N/A", "[cross-reference]") stored as Skiri terms, 244 cross-reference
  terms with spaces inside the word, and lacks 25 printed English headwords
  (twelve of them in a row on page file 278).
- **Earlier versions of the JSON** (the raw parse, the verified, normalised and
  linked stages, and their change logs) were removed from the repository on
  2026-11-13. They are in git history at commit `2e77095`, under
  `archived/dictionary_intermediates/`.

## How the JSON was made

1. Each page PDF was read by an AI model into JSON (`scripts/s2e_parser.py`,
   `scripts/run_parser_e2s.py`; the prompt and schemas are in
   [../prompts/dictionary_parsing/](../prompts/dictionary_parsing/)).
2. A second AI pass verified every field against the page.
3. Corrupted characters were repaired, the two sections were linked, and the
   learner spelling and respelling were generated (phases 1.1a to 1.1c).
4. Two audits (2026-03 and 2026-09) checked the result against the pages; see
   [../reports/](../reports/).
