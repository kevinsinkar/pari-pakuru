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
| `appendix3_kinship.json` | Appendix 3: 23 kinship terms with their "my / your / his" forms | `scripts/extract_appendices.py` | `noun_possession.py`, `possession_engine.py` |
| `grammatical_overview.json` | Parks's chapter 4, the grammatical overview, page by page with its tables and worked examples | `scripts/extract_appendices.py` | `morpheme_inventory.py`, `noun_possession.py`, the word-construction analysis |
| `grammar_retry_results.json`, `grammar_failed_pages_transcriptions.json` | Four pages of chapter 4 (1, 3, 7, 16) that the first extraction lost, recovered as plain text | `archived/scripts/retry_failed_grammar.py` | merged into the file above by `archived/scripts/merge_grammar_retries.py` |
| `dual_plural_analysis.json` | An AI analysis of the dual and plural forms in Appendix 1, piece by piece. Working notes for the conjugation engine | `archived/scripts/analyze_dual_plural.py` | nothing |
| `noun_possession_catalog.json` | Nouns sorted by possession system, with suffix tables and the examples used for validation | `scripts/noun_possession.py --extract` | nothing; the database tables are what the app uses |
| `blue_book_extracted.json` | 984 vocabulary items and sentences from the Blue Book, by lesson | `scripts/blue_book_verify.py --extract-only` | `blue_book_verify.py`, `noun_possession.py` |
| `lessons.json` | The 20 Blue Book lessons: titles, pages, dialogues, grammar notes. A copy of the `lessons` table | `scripts/build_lessons.py` | nothing; kept so the lessons are in git |

## Things to know

- **These files were compared with the pages in full on 2026-11-13 and
  corrected the same day.** A second reader transcribed the pages without
  seeing these files
  ([../reports/source_audit_2026-11/findings.md](../reports/source_audit_2026-11/findings.md));
  the changes are listed in `../reports/source_audit_2026-11/applied_fixes_report.txt`.

  | File | What was wrong | Now |
  |---|---|---|
  | `appendix1_conjugations.json` | 152 of 770 forms: accents the page does not have, vowels dropped or doubled, one block shifted by a row | all 152 corrected, each after a third look at the page |
  | `appendix2_irregular_roots.json` | *burii-waa* and *burii* for printed *hurii-waa* and *hurii*; one stem stored where the cell is empty | the two forms corrected. The singular of *tir* 'to be together' is still stored though the cell is empty in print: the conjugation engine reads it, so it was left for a person |
  | `appendix3_kinship.json` | *asaas*, *atipaat*, *apaat* for printed *asas*, *atipat*, *apat*; the five rows of book page 543 missing | corrected; the five rows added |
  | `grammatical_overview.json` | 85 of 797 Skiri words: 34 with a `b` where the page has an `h` (*-busuukuʔ* is *-husuukuʔ*), the rest differing by an accent, a vowel or a glottal stop | the 34 corrected, and after them the forms a second letter check still found (*-:hus*, *-hus*, *tihurás*, *ratkuhurasi*, *tuksuhuuhwiitit*); no `b` is left in a Skiri form. **51 words are not corrected**: they were matched to the second reading by likeness, not by position, and need a person with the page (`../reports/source_audit_2026-11/chapter4_differences.json`). Three of them were corrected on 2026-11-14, where the blind reading is a form the dictionary prints and the stored one is printed nowhere (*askatahciriʔ*, *iriirapahaatu*, *tuctiraahawista*); what each witness says about the others is in `chapter4_third_witness.json` |
  | `abbreviations.json` | 4 of 411 values (*raar-/rab-* is *raar-/rah-*) | three corrected; "verb class 1-a" is printed "verb class 1: -a" and was left |
  | `blue_book_extracted.json`, `lessons.json` | Blue Book forms taken from the OCR text: no accents, about one form in seven misread | 960 strings corrected from the scan, and 51 more on 2026-11-14 after a second reading; 42 forms left for a person |
  | `noun_possession_catalog.json` | carried the misread kin terms and *-biriʔ* | made again from the corrected data |

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
