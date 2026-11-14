# Pari Pakuru — Skiri Pawnee Language Tool: Project Log

*Last updated 2026-11-14. This is the record of what was done in each phase,
with its results, and of what is still open. What to do next, in order, is in
[What's next](#whats-next). For the folder layout see
[README.md](README.md); for the script behind each step see
[scripts/README.md](scripts/README.md).*

## Project Goal

Build a comprehensive Skiri Pawnee language preservation tool: a searchable, linked dictionary with pronunciation guides, semantic tags, morphological grammar engine, and sentence construction — all validated against source materials.

---

## Status at a glance

| When | Phase | What | State |
|---|---|---|---|
| 2026-02 | parse | Both dictionary sections read from page PDFs into JSON by an AI model; a second pass verified every field | done |
| 2026-03-07 | 1.1a–d | Character repair, linking of the two sections, respelling and learner spelling, completeness audit | done |
| 2026-03-08 | 1.2 | SQLite database | done |
| 2026-03-08 | 2.1 | Topic tags | done |
| 2026-03-08 | 2.2 | Blue Book cross-check | done |
| 2026-03-08 | 2.3 | Sound-change rules (24) | done |
| 2026-03-08 → 03-20 | 3.1 | Verb template, conjugation engine (79.4% of Appendix 1 as Parks prints it; the 90.3% reported until 2026-11-13 was measured against a misread copy), form 2 prediction (87.2% of dictionary verbs), accent rules | paused; see open items 25, 39 and 40 |
| 2026-03-18 | 3.1.5 | Noun possession | done; repaired 2026-11-13; see open item 13 |
| 2026-03-20 | 3.1.6 | Function words (418) | done |
| 2026-03-10 → 03-21 | 4.1, 4.3, 4.4 | Web app, confidence scores, community feedback | done |
| 2026-03-20 | 3.2a | Sentence templates (10) | done |
| 2026-03-20 | 5.2 | Flashcards in the app; Anki export (unused) | done |
| 2026-09-01 | audit | Extraction audit and repairs; IPA cross-checked against the PDF text layer | done; short residual list |
| 2026-09-01 | 3.2b | Person and mode derived from attested forms | first slice done |
| 2026-09-01 | 5.1 | Blue Book lessons in the app | done |
| 2026-09-02 | 5.2b | Spaced-repetition study in the app | done |
| 2026-09-12 | 5.3 | Static site on GitHub Pages | done |
| 2026-10-01 | audit | Flashcard and static-site audit; IPA and page references restored on the site | done in part |
| 2026-10-12 | 5.1, 5.2 | Lesson vocabulary linked; lesson titles repaired; flashcard curriculum frozen | done |
| 2026-11-07 → 11-10 | 6.1 | Word-building guide, version 1; weekly paper flashcards and printable sheets; respelling repair | guide superseded by 6.2; flashcards in use |
| 2026-11-12 | 6.2 | Word-construction analysis, version 2: evidence tiers, gold sets, learning path | done; awaiting human review |
| 2026-11-13 | | Repository clean-up; documentation brought up to date | done |
| 2026-11-13 | fixes | Data fixes (accent marks the decoding had dropped, page numbers, duplicates, letter-spaced text); possession suffix *-hiriʔ*; weekly flashcards rebuilt from version 2; flashcard Week 20 held for community review | done |
| 2026-11-13 | audit | Source-fidelity audit: every stored value compared with the printed page; character table verified against the glyphs; database written to git as text | done; 2,250 fixes proposed; applied in the next rows |
| 2026-11-13 | fixes | The audit's fixes reviewed and applied where the evidence is solid: 807 changes (152 forms of Appendix 1; appendices 2 and 3; chapters 3 and 4; 19 dictionary verb forms; 162 citations from other languages; 27 headwords; 393 column labels; one missing entry added, one phantom removed) | done; judgement calls left for a person (open items 41, 45) |
| 2026-11-13 | IPA | Parks's own phonetic symbols stored for all 4,244 of his entries (ə́, ɪ́, the syllable dot, the edge dash); 75 forms corrected in content, 9 added; respelling and learner spelling made again and checked | done |
| 2026-11-13 | Blue Book | The rest of the Blue Book forms read from the scan (843 more crops; with the audit's 153 that is 949 distinct forms, every one that has a page): 715 corrected (565 accents restored, 105 OCR slips, 45 apostrophes, dots and spaces); three entries built on misread forms corrected; made-up phonetic forms removed from the 93 Blue Book-only entries | done; 77 forms left for a person (open item 42) |
| 2026-11-13 | rebuild | Static site, weekly flashcards, printable sheets and word-construction outputs rebuilt from the corrected data; engines measured again | done |
| 2026-11-13 | hosting | The PythonAnywhere hosting of the web app retired; `wsgi.py` removed. GitHub Pages is the only place the project is published; the Flask app is a local tool | done |
| 2026-11-14 | fixes | Page citations: every Parks entry cites the page of the printed book (3,511 held the number of a PDF file, 348 less) | done |
| 2026-11-14 | fixes | What the dictionary prints and the database lacked, set from the PDF's text layer: 1,447 values (684 hyphens the typesetter put at line ends, 21 derived stems, 18 examples, citations, spacing, punctuation); three verb forms that are not printed removed | done; 37 differences left, each explained |
| 2026-11-14 | Blue Book | A second blind reading of the 77 forms left open: 35 settled. Corrected forms carried into three more tables (628 values). Three words of the grammar chapter corrected | done in part; 42 forms and about 40 chapter words left (open items 42, 45) |
| 2026-11-14 | site | The public site shows the whole entry (examples, verb forms, Parks's analysis, cited forms) and says truthfully what it is: About page rewritten, a "Send a correction" link on every result, "accent" in place of "pitch" | done |

The database on 2026-11-14: 4,337 entries (4,244 from Parks, 93 Blue Book
only), 5,504 senses, 9,559 verb forms for 2,239 verbs, 2,652 examples, 21
derived stems, IPA for the 4,244 Parks entries (2,218 with an accent mark)
and for none of the Blue Book-only ones. Compared with the printed page,
50,807 of 50,837 dictionary fields are identical (99.94%). Full table list: [Quick_Reference_Guide.md](Quick_Reference_Guide.md).

---

## What's next

*Ranked again on 2026-11-14. The ranking of 2026-11-13 had eight items; three
were completed the next day (page citations, the public site, what the
dictionary prints and the database lacked) and one in part (the forms that
need a look at the page). They are in the phase log under 2026-11-14. Numbers
in the last column are open items, further down.*

How the ranking is made: first what only people outside the project can
settle and takes longest to arrange; then what is wrong or missing in front
of learners on the public site; then what makes the stored data more
complete; last, what nobody outside this repository can see.

Size: **small** is part of one working session, **medium** one or two
sessions, **large** more.

| Rank | What | Why at this rank | Who | Size | Open items |
|---|---|---|---|---|---|
| 1 | **Ask the Pawnee Nation's language and culture people to review**: the ceremonial vocabulary, the 387-word flashcard list, the word-building guide, and now the About page of the public site | Nothing in code replaces it, and it takes the longest to arrange. It decides whether flashcard Week 20 is ever shown, whether the word-building guide is published, whether the 143 entries tagged as ceremony stay searchable and show their full detail, and what the accent marks are to be called | You make the contact; the review material can be prepared here | Small to prepare; the review itself is theirs to pace | 1, 2, 3, 14, 43, 50, 9 |
| 2 | **Settle the forms that still need a look at the page** | 42 Blue Book forms, about 40 words of the grammar chapter and a handful of dictionary values are known to be doubtful and are listed one by one. What scripts and one more reading could settle has been settled; what is left needs the book in a person's hands, or a full second blind reading of the grammar chapter | A person with the books. Or blind readings: about 700,000 tokens for the grammar chapter (three readers), about 130,000 for another look at the Blue Book forms | Small for a person; medium by readings | 42, 45, 41 |
| 3 | **Decide what becomes of the engines** | The conjugation engine gets 79.4% of Appendix 1 and its accent rules were worked out from misread data. None of it is on the public site, so nothing wrong is in front of learners. Recommended: withdraw the accent rules, leave from-scratch conjugation paused, and extend person derivation from attested forms instead. The sentence templates still write Blue Book forms without their printed accents | Decision yours; then code | Medium to large | 39, 40, 25, 26, 13, 24, 42 |
| 4 | **Repair the English-to-Skiri file and re-import the English index** | The database's English index is an early, uncleaned copy, page numbers included. Only the local app reads it; the public search does not. Worth doing before anything new is built on those tables | Code | Medium | 32, 22 |
| 5 | **Read what has not been read, build what has not been built** | Front-matter chapters 2 and 5; the Blue Book glossary (pages 123 to 130); Blue Book headwords as the book prints them; printable word lists and paradigm tables | Code, with blind readings for the scanned pages | Medium each | 37, 28, 35, 27 |

Small things to do along the way, whenever the file concerned is open: retire
the older respelling function (46); the "word of the day" fixed at build
time and the Blue Book-only entries without a learner spelling (21); the
style names `pitch-high` and `pitch-unmarked`, which no reader sees but which
still say "pitch" (9).

### The first step of each of the top three

1. **Review.** Put together one packet a reviewer can read without the
   repository: the Week 20 cards and the 176 words flagged as ceremonial (by
   keyword only, so the list needs a person in any case); the 387-word list;
   the ten questions at the top of `curriculum/roots_v2/validation_report.md`;
   the About page as it now reads; and the two teaching questions, whether
   learners should see Parks's difference between tense and lax short vowels
   (43) and whether "accent" is the right word for the marks (9). Ask at the
   same time whether the ceremonial entries should be searchable on the
   public site at all, and whether they may show their verb forms and
   analysis like the others (50).
2. **Forms that need the page.** Print or open three lists beside the books:
   the last section of `reports/source_audit_2026-11/bluebook_applied_report.txt`
   (42 forms, with what each of two readers saw), the words marked `open` in
   `chapter4_third_witness.json` (with what the stored text, the blind reader
   and the dictionary each say), and the section "left as they are" of
   `print_completion_report.txt`. Each line is one look at one page.
3. **Engines.** Read open items 39 and 40 and decide: keep, repair or
   withdraw `accent_rules.py`; and whether from-scratch conjugation is taken
   up again or person derivation from attested forms is extended instead.

### What not to do next

- Do not show Week 20, publish the word-building guide, or give the ceremony-tagged entries their full detail before rank 1 has an answer.
- Do not take up from-scratch conjugation again without a decision (rank 3). The standing rule is that derived forms start from attested ones.
- Do not build on `english_index` or `cross_references` before rank 4.

---

## Source Materials

| File | Description | Location |
|------|-------------|----------|
| Parks Dictionary (PDF) | Full Skiri Pawnee dictionary by Douglas Parks. Split into: Abbreviations/Sound Key, Sounds/Alphabet, Major Sound Changes, Grammatical Overview, Organization, English-to-Skiri section, Skiri-to-English section, 3 Appendices (Appendix 1: 7 verb conjugation paradigms ~770 forms; Appendix 2: irregular du/pl verb roots ~9 entries; Appendix 3: kinship terminology ~40 forms) | `Dictionary Data/Dictionary PDF Split/` |
| Dictionary page PDFs | Individual pages split for AI processing | `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/` and `split_pdf_pages_ENGLISH_TO_SKIRI/` |
| Blue Book — Pari Pakuru' | 1979 Pawnee Cultural Retention Committee textbook. 20 lessons teaching spoken Pawnee with dialogues, vocabulary, grammar explanations | `pari pakuru/Blue Book - Pari Pakuru.pdf` and `.txt` extraction |
| JSON Schemas | Defined structures for S2E and E2S parsed entries | `prompts/dictionary_parsing/` |
| Parks Ch. 3 OCR | OCR extraction of Major Sound Changes (24 rules with examples) | `Dictionary Data/Dictionary PDF Split/parks_sound_changes_ocr.txt` |
| Parks Ch. 4 OCR | OCR extraction of Grammatical Overview (23 pages: noun incorporation, verb classes, possession) | `Dictionary Data/Dictionary PDF Split/parks_grammatical_overview_ocr.txt` |

## Current Data State

| File | Entries | Status |
|------|---------|--------|
| `Dictionary Data/skiri_to_english_respelled.json` | 4,273 | **CURRENT** — normalized, OCR fixed, `simplified_pronunciation` + `normalized_form` populated. Since 2026-11-13: audit fixes applied and phonetic forms in Parks's own symbols; headword, phonetic form, respelling and learner spelling identical to the database for all 4,244 entries the two share (the other 29 are the duplicate rows the database dropped). Since 2026-11-14: `entry_metadata.page_number` is the page of the book, and every value `scripts/complete_from_print.py` set in the database is set here too |
| `Dictionary Data/english_to_skiri_linked.json` | 6,414 | **CURRENT** — normalized, `s2e_entry_id` linked to S2E entries. Phonetic forms in Parks's symbols since 2026-11-13, except 295 of 5,399 subentries (197 of them linked to no entry). Its own faults are not repaired (open item 32) |
| `skiri_pawnee.db` | 4,337 | **CURRENT, and the working master copy** — the two files above plus 93 Blue Book-only entries, less 29 duplicate rows, plus everything later phases added. Not in git |

The earlier stages of the two JSON files (`*_complete`, `*_verified`,
`*_normalized`, `*_linked`, `*_fixed`, and their change logs) were removed from
the repository on 2026-11-13. They are in git history at commit `2e77095`
under `archived/dictionary_intermediates/`.

### Relationship Between S2E and E2S

- **S2E is the primary linguistic record** — full entries with headword, phonetic form, etymology, 5 paradigmatic verb forms, examples, derived stems, cognates
- **E2S is an index into S2E** — English words pointing to Skiri equivalents, with cross-references
- **E2S has more accurate phonetic forms** (IPA vowels: ə, ɪ, ʊ, accent marks) because its PDF parsing captured the IPA characters more faithfully
- **Linked by `entry_id`** (on S2E) and `s2e_entry_id` (on E2S subentries). Format: `SK-{slug}-p{page}-{index}`

### S2E Entry Structure
```json
{
  "entry_id": "SK-paatuq-p107-2038",
  "headword": "paatuʔ",
  "normalized_form": "pâtu'",
  "entry_metadata": { "page_number": 107, "column": "left", ... },
  "part_I": {
    "stem_preverb": null,
    "phonetic_form": "[paá-tʊʔ]",
    "simplified_pronunciation": "PAH-too'",
    "grammatical_info": { "grammatical_class": "N", "verb_class": null, "additional_forms": [] },
    "glosses": [{ "number": 1, "definition": "blood; gore.", "usage_notes": null }],
    "etymology": { "raw_etymology": "<paat+uʔ, blood + NOM>", "constituent_elements": [...], "literal_translation": "..." },
    "cognates": [{ "language": "Ar.", "form": "..." }]
  },
  "part_II": {
    "paradigmatic_forms": { "form_1": "...", "form_2": "...", "form_3": "...", "form_4": "...", "form_5": "..." },
    "examples": [{ "skiri_text": "...", "english_translation": "...", "usage_context": null }]
  },
  "compound_structure": null,
  "derived_stems": []
}
```

### E2S Entry Structure
```json
{
  "english_entry_word": "blood",
  "entry_metadata": { "page_number": 1, ... },
  "subentries": [{
    "subentry_number": 1,
    "s2e_entry_id": "SK-paatuq-p107-2038",
    "s2e_match_type": "exact_unique",
    "part_I": {
      "skiri_term": "paatuʔ",
      "phonetic_form": "[paá-tʊʔ]",
      "grammatical_classification": { "class_abbr": "N", "verb_class": null },
      "english_glosses": [{ "number": 1, "definition": "blood; gore." }],
      "etymology": { ... }
    },
    "part_II": { "paradigmatic_forms": [{ "form_number": 1, "skiri_form": "..." }], "examples": [...] },
    "part_III": { "cross_references": [{ "english_term": "...", "skiri_equivalents": ["..."] }] }
  }]
}
```

### Phonetic Notation System (Parks Dictionary)

Stored exactly as Parks prints it since 2026-11-13. Before that the database
used a working notation: a hyphen for the syllable dot, a bullet for the edge
dash, à for ə́ and í for ɪ́. Reports and frozen files older than that date
still show it.

- `·` (U+00B7) — syllable boundary
- `–` (U+2013) — at the edge of a bound form: something must come before or after
- Consonants: p, t, k, c/č, s, w, r, h, ʔ (glottal stop)
- Long vowels: aa, ii, uu
- Short vowels: ə, ɪ, ʊ (lax, the usual quality); a single i or u is a short vowel with tense quality
- Accent: an acute on the accented syllable: ə́ ɪ́ ʊ́ on a short vowel, on the second half of a long one (aá, ií, uú). A grave occurs in ten entries and is not explained
- `{k/t}` — the final consonant alternates; `(r)` — an optional sound
- Example: `[–rə·hʊh·kaa·paa·kɪs–]`

The PDF's text layer encodes these with stand-in characters that depend on
the font. The verified table is `scripts/source_audit/chartable.py`.
`scripts/ipa_notation.py` converts the stored notation to the old working one
for the respelling code, and nowhere else.

### Sound Key (PDF 01 p. xvii)
```
CONSONANTS: p (spot), t (stop), k (skate), c (patch/cents), s (sit),
            w (wall), r (Spanish tapped pero), h (hit), ʔ (uh-uh)
VOWELS:     a/ah (putt), aa (father), i/ih (pit), ii (weed),
            u (boot), uu (rude)
```

### Grammatical Classes
```
N (noun), N-DEP (dependent noun), N-KIN (kinship term)
VI (intransitive verb), VT (transitive verb), VD (descriptive verb)
VL (locative verb), VP (patientive/passive verb), VR (reflexive verb)
ADJ, ADV, NUM, PRON, DEM, QUAN, CONJ, INTERJ, LOC, COLL
Verb classes: (1), (1-a), (1-i), (2), (2-i), (3), (4), (4-i), (u), (wi)
```

### Paradigmatic Forms Key (5 standard verb forms)
```
1. First Person Singular Subject, Indicative Mode, Perfective
2. Third Person Singular Subject, Indicative Mode, Perfective
3. Third Person Singular Subject, Indicative Mode, Imperfective
4. Third Person Singular Subject, Absolutive Mode, Subordinate Perfective
5. Third Person Singular Subject, Indicative Mode, Perfective Intentive
```

---

## Phase log: 1.1 (cleaning the parsed dictionary)

### ✅ Phase 1.1a — OCR Normalization
**Script:** `scripts/normalize_phonetic.py`
**What it does:** Recursively walks every string in every entry across both S2E and E2S, fixing OCR/encoding corruptions from PDF parsing. Logs every replacement per-entry.

**Character corrections applied:**
| Corrupted | Corrected | Description |
|-----------|-----------|-------------|
| ™ (U+2122) | ʔ (U+0294) | IPA glottal stop |
| ® (U+00AE) | ʔ (U+0294) | Parks glottal stop → IPA |
| ? (phonetic only) | ʔ (U+0294) | OCR misread |
| Ù (U+00D9) | č (U+010D) | c-hacek |
| ‡ (U+2021) | í (U+00ED) | i-acute |
| Ñ (U+00D1) | á (U+00E1) | a-acute |
| ‰ (U+2030) | ʊ (U+028A) | IPA near-close back rounded |
| † (U+2020) | ɪ (U+026A) | IPA near-close near-front |
| æ (U+00E6) | í (U+00ED) | i-acute |
| ß (U+00DF) | ə (U+0259) | IPA schwa |
| Š (U+0160) | ʊ (U+028A) | IPA near-close back rounded |

Also strips whitespace from `phonetic_form` fields. Preserves `•` syllable dots.

**Correction (2026-11-13).** The "corrupted" characters are not OCR errors. The
PDF's text layer does not contain Parks's IPA letters; its font has them at the
positions of other characters, so the text layer is full of stand-ins. The table
above, and the six additions listed under Phase 1.1c, were worked out without
looking at the page, and six rows were wrong. Read against page images:

| Stand-in | Was decoded as | The page prints | Entries |
|---|---|---|---|
| `÷` | ː (a length mark) | **ú**, as in *huú* | 141 |
| `Š` | ʊ | **ʊ́** (accented) | 125 |
| `ˆ`, `ç` | ɪ, ʔ | **ì** | 3 |
| `ø` | ː | **ù** | 1 |
| `Ò` | a | **à** | 1 |
| `à` (itself) | à | **ə́** | 545, not yet changed |
| `‡` | í | what looks like **ɪ́** | 371, not yet changed |

Parks prints no length mark anywhere: long vowels are doubled. The first five
rows had removed the accent from 269 entries, and in two of them a vowel from
the respelling as well. `scripts/fix_data_2026_11.py` restored them from the
text layer, position by position (report:
`reports/fix_data_2026-11-13_report.txt`). The last two rows keep the accent but
not Parks's symbol; they are open item 6. The 2026-09-01 cross-check against the
text layer could not see any of this, because it decoded the text layer with the
same table.

**Results:** 50,699 character replacements across 8,820 entries. Zero corruptions remaining.

### ✅ Phase 1.1b — Dictionary Linking + Phonetic Sync
**Script:** `scripts/link_dictionaries.py`
**What it does:**
1. Assigns unique `entry_id` to every S2E entry
2. Matches E2S subentries to S2E via headword with gloss disambiguation for homonyms
3. Writes `s2e_entry_id` + `s2e_match_type` into E2S subentries
4. Updates S2E phonetic forms with E2S's more accurate IPA transcriptions

**Matching results:**
- 5,132 E2S subentries linked (4,726 exact, 398 gloss-disambiguated, 8 fallback)
- 2,579 cross-reference-only (no data to link)
- 362 unmatched (mostly parsing artifacts like "(see cross-reference)")
- 3,925 S2E phonetic forms updated with IPA

### ✅ Phase 1.1c — Pronunciation Respelling + Orthographic Normalization
**Scripts:** `scripts/respell_and_normalize.py`, `scripts/fix_priority_issues.py`
**What it does:**
1. Generates `simplified_pronunciation` field: IPA `phonetic_form` → learner-friendly English respelling
2. Generates `normalized_form` field: headword → learner orthography with circumflex long vowels, č, '

**Vowel mapping (source: Parks Sound Key p. xvii + Blue Book pp. xvii–xxi):**

| Pawnee | English Comparison | Respelling |
|--------|-------------------|------------|
| `a` (short) | "putt" / "above" | `uh` |
| `aa` (long) | "father" | `ah` |
| `i` (short) | "pit" | `ih` |
| `ii` (long) | "weed" / "machine" | `ee` |
| `u` (short) | "push" | `oo` |
| `uu` (long) | "rude" | `oo` |
| `ɪ`, `ʊ`, `ə` | IPA reduced vowels | `ih`, `oo`, `uh` |

**Consonant mapping:** `r` → `d` (BB: "a very soft d"), `c` → `ts`, `č` → `ch`, `ʔ` → `'`, all others pass through.

**Normalization rules (Skiri words only):** `aa` → `â`, `ii` → `î`, `uu` → `û`, `c` → `č` (when phonetic form confirms /tʃ/), `ʔ` → `'`.

**Edge cases handled:** comma-separated variants, preverb notation `(ʊt...)`, optional sounds `(h)`/`(r)`, IPA length mark `ː`, null morpheme `Ø`, prefix notation `[+raar-]`, alternation markers `{k/t}`.

**Results:**
- 4,272/4,273 entries with `simplified_pronunciation` (1 entry has no phonetic form)
- 4,273/4,273 entries with `normalized_form`
- 53 `c`/`č` disambiguation mismatches flagged for review (count mismatch between headword and phonetic)

**Also applied (`fix_priority_issues.py`):** 6 additional OCR corrections missed by Phase 1.1a (`÷`→`ː`, `ˆ`→`ɪ`, `‹`→`ʊ`, `Ò`→`a`, `ç`→`ʔ`, `ø`→`ː`), plus ~111 non-IPA phonetic form stubs nulled (`[cross-referenceonly]`, `NOT_PROVIDED`, `N/A`, `Seeentryfor'...'`, `[notprovided]`).

### ✅ Phase 1.1d — Parsing Completeness Audit
**Scripts:** `scripts/audit_entries.py`; `generate_review_list.py` and `verify_glottal_from_phonetic.py` (now in `archived/scripts/`)
**What it does:** Validates every S2E entry (and optionally E2S) for data quality. Local rule-based checks + optional Gemini AI batch validation.

**Local checks performed:**
- Field presence: headword, phonetic_form, grammatical_class, glosses
- Phonetic character validation: flag non-IPA characters post-normalization
- Noun glottal stop check: nouns ending in vowel without `ʔ`, triaged by N/N-KIN/N-DEP/proper noun
- Consonant skeleton consistency: headword ↔ phonetic_form, with c↔ts normalization, optional sound inclusion, alternation marker resolution, glottal absorption handling
- Verb class presence (suppressed for VD descriptive verbs — by design in Parks)
- Multi-class grammatical entries validated per-component (e.g., `VT, VR`)

**Gemini AI validation:** Batch validation (20 entries/batch) with checkpointing for resume. System prompt is Pawnee-linguistics-aware (knows Parks notation, c↔ts equivalence, noun suffix patterns).

**Noun glottal stop resolution:** Cross-referenced phonetic_form endings against headword endings for 260 common noun candidates. Result: 0 OCR misses, 257 confirmed correct (phonetic form also lacks final ʔ), 3 unverifiable (no phonetic form). The headwords are correct as-is.

**Final audit numbers (post all fixes):**
- 640 total flags (down from 2,005 initial)
- 81 by-design (proper noun/kinship glottal, VD verb class)
- 12 skeleton mismatches remaining (headword notation edge cases: prefix markers, null preverbs)
- 260 noun glottal candidates: all verified correct via phonetic cross-reference
- 2 residual INVALID_PHONETIC_CHAR (minor stragglers)

---

## Phase log: 1.2 onward

### Priority Roadmap *(added 2026-03-15; statuses brought up to date 2026-11-13)*

High-impact items ordered by learner value, not technical dependency:

| Priority | Phase | What | Why |
|----------|-------|------|-----|
| ✅ ~~1~~ | 3.1.5 | ~~Noun possession morphology~~ | **DONE (2026-03-18)** — 4 possession systems + locative suffixes + web widget + example filter. 40/40 tests. |
| 🟡 2 | 3.1 (stem extraction) | Dictionary-wide stem extraction | **PAUSED at 86.7%** (re-measured 2026-11-12: 1,908 of 2,201) — third pass: 83.5% → **86.6%** (1,914/2,211), 88.4% w/ close. Up from 14.8% → 62.0% → 83.5% → 86.6%. |
| ✅ ~~3~~ | 4.3 | ~~Confidence scoring on computed forms~~ | **DONE (2026-03-19)** — 4-factor weighted scoring (0.0-1.0), DB column, web badges, dashboard widget. 88.7% avg, 2,202 high / 30 med / 22 low. |
| 🟡 4 | 3.1 (accent) | Accent mark generation | **PAUSED** — 78/85 (91.8%) accented forms correct. 4 rules: Agent-boundary í, Mode-prefix í/rí, Infinitive kú, Dual sí. Appendix 1: 76.2% → **86.4%**. 7 remaining failures are verb-specific stem accents. |
| ✅ ~~5~~ | 4.4 | ~~Community feedback mechanism~~ | **DONE (2026-03-19)** — Flag/confirm buttons, admin review queue, writable DB, dashboard widget. Design Principle #6 enforced. |
| 🟡 6 | 5.2 (exports) | Printable PDFs + Anki export | **Anki DONE (2026-03-20)** but unused. **Printable flashcard sheets DONE (2026-11-10)**, `curriculum/flashcard_pdfs/`. Printable word lists and paradigm tables remaining. |
| ✅ ~~7~~ | Ongoing | ~~Blue Book 518-gap triage~~ | **DONE (2026-03-19)** — 516 gaps classified: 38% phrases, 27% inflected verbs, 18% unlisted nouns, 8% descriptors, 3% possessed, 2% function words, 2% loanwords, 2% OCR artifacts. 65% are morphological (roots exist in Parks). 115 high-value items flagged for DB addition. |
| ✅ ~~8~~ | 3.1.6 | ~~Function word inventory~~ | **CLASSIFIED (2026-03-20)** — 418 function words with `position_rule` + `refined_subclass`. 149 PROCLITIC, 135 PRECEDES-VERB, 51 PRECEDES-NOUN, 44 CLAUSE-INITIAL, 28 STANDALONE, 11 BETWEEN-CLAUSES. Demonstratives + interrogatives mapped. |
| ✅ ~~9~~ | 3.2a | ~~Template-based sentence assembly~~ | **DONE (2026-03-20)** — 10 templates, `/sentence-builder`. Person and mode derivation added 2026-09-01 (3.2b). |
| ✅ ~~10~~ | 5.1 | ~~Structured lesson content~~ | **DONE (2026-09-01)** — all 20 Blue Book lessons in the app and on the static site. |

### 🟡 Phase 3.1 — Dictionary-Wide Stem Extraction *(paused after the third pass)*

**Re-measured 2026-11-12:** 1,908 of 2,201 exact (86.7%), 40 close, 253 missed. The word-construction analysis (Phase 6.2) uses this predictor as one of its evidence channels and treats a miss as "no confirmation", never as a contradiction.

**Status (2026-03-19):** Third pass complete — **83.5% → 86.6% exact** (1,914/2,211 verbs), 88.4% with close matches. Up from 14.8% → 62.0% → 83.5% → 86.6%.

**Script:** `scripts/stem_extractor.py`
**Reference files:** `parks_sound_changes_ocr.txt` (OCR of Parks Ch. 3), `parks_grammatical_overview_ocr.txt` (OCR of Parks Ch. 4), both in `Dictionary Data/Dictionary PDF Split/`

This is the wall between "a conjugation engine that works on 7 test verbs" (76.2% on Appendix 1) and "a tool that can inflect any verb a learner looks up." The first pass proved the approach works — headword IS the stem, and form_2 is predictable from `headword + verb_class + stem_preverb` with systematic sound change rules.

**What `stem_extractor.py` does (current pipeline):**
1. Parse `stem_preverb` field → preverb morphemes (ut, uur, ir, ir+ut, etc.)
2. Infer verb class for untagged entries (VD→(u), VL→(wi), VP→(4))
3. Build prefix+stem with preverb junction rules (ut+r→tuuh, ut+h→tut, uur+C→tuuh+C, etc.)
4. Apply vowel coalescence at prefix+stem boundary (Parks Rules 5-7)
5. Apply internal sound changes (Rule 8R: r→t after obstruent, Rule 12R: r→h before C)
6. Apply perfective finals (k→t, hk→t, r→Ø, h→Ø, V→Vʔ, kus→ku)
7. Special class rules: (3) -aʔuk→-uʔ contraction, (wi) no final ʔ
8. Compare predicted form_2 to attested paradigmatic_form in DB

**Accuracy by category (third pass — 2026-03-19):**

| Category | Total | Exact | Rate | Notes |
|---|---|---|---|---|
| (4)\|(uur...) | 28 | 28 | 100.0% | Ceiling! |
| (3)\|(uur...) | 16 | 16 | 100.0% | Ceiling! |
| (3)\|(ut...) | 9 | 9 | 100.0% | Ceiling! |
| (3)\|(ir...ut...) | 13 | 13 | 100.0% | 3rd pass: ir+ut junction fix |
| (wi)\|(ir...ut...) | 10 | 10 | 100.0% | 3rd pass: ir+ut junction fix |
| (wi)\|(ir...) | 7 | 7 | 100.0% | 3rd pass: a+i coalescence |
| (2-i)\|(uur...) | 6 | 6 | 100.0% | — |
| (2)\|(ut...) | 5 | 5 | 100.0% | — |
| (2-i)\|none | 44 | 43 | 97.7% | Near-ceiling |
| (1-a)\|(uur...) | 32 | 31 | 96.9% | — |
| (1-i)\|none | 54 | 52 | 96.3% | — |
| (1)\|(uur...) | 47 | 45 | 95.7% | — |
| (1)\|(ut...) | 101 | 92 | 91.1% | — |
| (3)\|none | 120 | 109 | 90.8% | — |
| (wi)\|none | 80 | 72 | 90.0% | — |
| (1)\|none | 434 | 388 | 89.4% | 3rd pass: -wiir/-uuh shortening |
| (4)\|(ut...) | 81 | 71 | 87.7% | — |
| (3)\|(ir...) | 94 | 82 | 87.2% | 3rd pass: a+u coalescence, aaʔa fix |
| (4)\|none | 414 | 355 | 85.7% | — |
| (wi)\|(ut...) | 27 | 23 | 85.2% | — |
| (u)\|none | 385 | 320 | 83.1% | 3rd pass: VD echo fixes, -wii shortening |
| (u)\|(ir...) | 12 | 10 | 83.3% | — |
| (2)\|none | 42 | 33 | 78.6% | — |
| (u)\|(ut...) | 24 | 18 | 75.0% | 3rd pass: VD echo -Vht fix |

**Remaining gaps (257 miss, 40 close):**

| Pattern | Current | Remaining issue | Count |
|---|---|---|---|
| (4)\|none | 85.7% | Multi-word headwords; `ruuti-`/`si-` prefix entries; internal shortening | 50 miss |
| (u)\|none VD | 83.1% | Internal long-vowel shortening (aah→ah); prothetic vowel; prefix mismatches | 49 miss |
| (1)\|none | 89.4% | `ruuti-`/`si-` prefix entries; `aw-` absorption; internal vowel changes | 43 miss |
| (3)\|(ir...) | 87.2% | Remaining class 3 stem allomorphy; prefix mismatches | 12 miss |
| (3)\|none | 90.8% | Internal contraction edge cases | 11 miss |
| Other categories | — | `si-` prefix (16 total), `ruuti-` prefix (19 total), bracket notation (~10) | ~45 miss |

**Key data sources:**
- `lexical_entries.verb_class` — populated for 1,698/2,254 verbs (75%); 556 missing are VD (438) + VL (115)
- `lexical_entries.stem_preverb` — populated for 652 verbs (29%); top patterns: `(ut...)` 294, `(uur...)` 164, `(ir...)` 129
- `paradigmatic_forms.form_2` — ground truth for validation; available for 2,246/2,254 verbs (99.6%)
- `etymology.constituent_elements` — morpheme decomposition for 1,772 verbs (79%); key for noun incorporation stripping
- `parks_sound_changes_ocr.txt` — OCR of Parks Ch. 3 (all 24 rules with examples and exceptions)
- `parks_grammatical_overview_ocr.txt` — OCR of Parks Ch. 4 (23 pages: noun incorporation, compound formation, verb classes)

### ✅ Phase 1.2 — Database Schema
**Script:** `DB/import_to_sqlite.py`
**What it does:** SQLite database (`skiri_pawnee.db`) unifying S2E and E2S data.

**Tables:** `lexical_entries` (4,337 entries on 2026-11-13: 4,273 imported from Parks, + 93 Blue Book-only words, − 23 duplicate rows in March, − 6 more in November), `glosses`, `paradigmatic_forms`, `examples`, `etymology`, `cognates`, `derived_stems`, `english_index`, `cross_references`, `semantic_tags`, `blue_book_attestations`, `import_metadata`, `bb_gap_triage`, `community_feedback`, `function_words` (418), `bb_function_words` (63) + FTS tables for glosses, examples, english_index. Which script created each table, and the row counts, are in `DB/README.md`.

**The database cannot be rebuilt by one command.** The importer creates only the core tables; more than twenty later scripts changed the database in place, some with AI answers that were saved nowhere else. Restore a backup instead (`OneDrive/pari_pakuru_backups/`, `~/.pari_pakuru_backups/`).

### ✅ Phase 2.1 — Semantic Category Tagging
**Script:** `scripts/tag_entries.py`
**What it does:** Auto-tags entries by domain using rule-based keyword matching + Gemini AI for ambiguous cases. 7,097 tags were stored at first. An AI audit on 2026-03-15 (`archived/scripts/audit_semantic_tags.py`, report `reports/audit_semantic_tags.txt`) removed 1,248 false matches caused by English words with several meanings, and 36 wrong kinship tags were removed on 2026-03-21. On 2026-11-13 the table holds **4,500 tags: 19 topics on 3,316 entries**. (The rest of the drop from 7,097 is not documented.)

### ✅ Phase 2.2 — Blue Book Cross-Verification
**Script:** `scripts/blue_book_verify.py`
**What it does:**
1. Parses Blue Book text (`pari pakuru/Blue_Book_Pari_Pakuru.txt`) into 20 lesson chunks
2. Sends each chunk to Gemini API (`gemini-2.5-flash`) to extract structured vocabulary
3. Normalizes BB practical orthography → Parks linguistic orthography (ts→c, '→ʔ, etc.)
4. Matches against dictionary via 3-tier: exact normalized → loose (no glottal/affricate) → prefix
5. Writes results to `blue_book_attestations` table in SQLite
6. Adds BB dialogue sentences as new `examples`
7. Adds `blue_book_attested` column to `lexical_entries`
8. Generates report at `reports/phase_2_2_blue_book.txt`

**Results (final, after follow-up improvements):**
- 984 BB vocabulary items extracted (all 20 lessons, Lesson 20 split into 4 page-chunks)
- 53 exact, 5 loose, 404 prefix, 4 verb-stem matches; 518 gaps
- 88 new dialogue examples added to `examples` table
- 83 dictionary entries attested (`blue_book_attested = 1`)
- Gaps include: multi-word phrases, verb constructions, function words, loanwords (expected)
- Normalization confirmed working: BB `ts`→Parks `c`, BB `'`→Parks `ʔ`

**Extraction output:** `extracted_data/blue_book_extracted.json` (984 items). The extraction checkpoint is in git history only.

**State on 2026-11-13:** `blue_book_attestations` has 1,026 rows, 581 of them linked to a dictionary entry; 181 entries are marked `blue_book_attested`. The `prefix` match type (404 rows) is unreliable and is not used as evidence by the word-construction analysis.

**Script features:**
- `--rerun-failed`: clears empty checkpoint entries so failed lessons get re-extracted
- `--clear-db`: wipes attestations table for clean re-import
- `--match-only`: re-run matching stage only (no Gemini calls)
- `--extract-only`: run Gemini extraction only (no DB import)
- Large lessons (>6 pages) auto-split into page chunks (fixes Lesson 20 / epilogue)
- 4-tier matching: exact normalized → loose → prefix → verb stem strip

**Lesson 20 breakdown (pages 111–130, epilogue + glossary):**
- Split into 4 chunks: p111-116 (35 entries), p117-122 (18 entries), p123-130 (0 — glossary only)
- 58 total items, 33 matched (57%)

**Follow-up: Pronunciation comparison (`archived/scripts/bb_pronunciation_compare.py`):**
- Extracts BB parenthetical pronunciation guides from raw text (12 found in lesson pages 29+)
- OCR normalization: consonant+'d' → consonant+'a' (stress-dotted vowel artifact)
- 3-pass parser: inline `word (pron) gloss`, column-block (table format), preceding-line
- Long-vowel-folded matching + gloss-based fallback via `english_index`
- Comma-separated headword variant indexing (e.g., `rawa, nawa` indexed as both `rawa` and `nawa`)
- Compares BB guides against verified IPA `phonetic_form` (not `simplified_pronunciation`)
- Normalization for comparison: IPA reduced vowels (ɪ→i, ʊ→u, ə→a), accent marks stripped, BB ts→c, BB '→ʔ
- 7 of 12 guides matched to Parks dictionary entries
- Results: 4 exact matches, 3 exact after long-vowel folding, 0 different
- Key finding: BB pronunciation guides map directly to IPA phonetic forms after normalization; the only systematic difference is BB shortening long vowels (BB `hi` = IPA `hii`, BB `ra` = IPA `raa`, BB `ki` = IPA `kii`)
- 5 unmatched guides are verb constructions / multi-word forms without standalone dictionary entries
- Report: `reports/phase_2_2_pronunciation_phonetic.txt`

### ✅ Phase 2.3 — Sound Change Rule Engine
**Script:** `scripts/sound_changes.py`
**What it does:**
1. Catalogs all 24 phonological rules from Parks Ch. 3 (Major Sound Changes)
2. Implements each rule as a Python function (9 restricted + 15 unrestricted)
3. Provides ordered pipeline: morpheme list → surface form
4. Stores rules in `sound_change_rules` DB table
5. Validates against 2,241 paradigmatic form pairs
6. Generates report at `reports/phase_2_3_sound_changes.txt`

**Rule categories (24 total):**
- Vowels Restricted (4): Dominant i (1R), Dominant a (2R), -his reduction (3R), Vocalic reduplication (4R)
- Vowels Unrestricted (3): Same-vowel contraction (5), u-domination (6), i+a contraction (7)
- Consonants Restricted (5): raar- assibilation (8R), final-s loss (9R), prefixal r-loss (10R), ut- affrication (11R), prefixal r-laryngealization (12R)
- Consonants Unrestricted (12): t-laryngealization (13), metathesis (14), sonorant reduction (15), h-loss (16), sibilant hardening (17), sibilant loss (18), alveolar dissimilation (19), degemination (20), r-stopping (21), labial glide loss (22), final r loss (23), c-variants (24)

**Pipeline ordering:**
1. Restricted rules (morpheme-aware): 1R → 2R → 3R → 8R → 10R → 11R → 12R
2. Concatenate morphemes
3. Unrestricted rules (string-level): 5 → 6 → 7 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23
4. Optional: Rule 9R final-s loss (word-level)

**Test results:** 11/11 built-in tests passing (PDF examples)

**Validation results:**
- 82.1% of form_4 entries start with `irii-` prefix (expected)
- 17.2% start with `irir-` (variant for certain verb classes)
- Simple prefix-swap derivation shows 12% close-match rate (edit dist ≤ 2)
- Full derivation requires morpheme decomposition (Phase 3.1 dependency)
- Rule 13 (t→h before r): 689 entries show evidence
- Rule 20 (degemination): all 9 raar-preverb forms confirmed surface without rr
- 268 headwords end in underlying r (notation convention; surface final-r loss confirmed)

**Key finding:** Sound change rules are correctly formalized and tested; the gap for full paradigmatic form derivation is morphological decomposition (prefix/preverb/suffix inventory), which is Phase 3.1's responsibility.

**Gemini audit results (52 entries across 15 verb classes):**
- 14 of 24 rules observed in paradigmatic forms (most frequent: Rule 6 u-domination, Rule 23 final-r loss, Rule 7 i+a contraction)
- 48/52 entries flagged anomalies — mostly expected: they are **unlisted suffixation/perfective patterns** (not sound change rule errors)
- Unlisted patterns identified (important for Phase 3.1):
  - Perfective suffix `-his` lost after stem-final `t` (not just after `k` as in Rule 3R)
  - Stem-final `k → t` in perfective for Class 2-i and some Class 4 verbs
  - Subordinate perfective suffix `-u` for consonant-final stems, `-wi` for `aa`-final stems
  - Glottal stop `ʔ` blocks vowel contraction rules
  - `irii- + ra-` = `iriira-` (r+r NOT degeminated — Rule 20 scope limited to within-morpheme)
- These are **morphological suffixation rules**, not phonological sound changes — correctly out of scope for Ch. 3 rules
- All 24 implemented rules confirmed correct where they apply

**Script features:**
- `--test`: run built-in test suite (PDF examples)
- `--apply "ti + uur + hiir"`: apply pipeline to morpheme sequence
- `--catalog-only`: populate DB table only
- `--validate-only`: run validation without DB writes
- `--final-s-loss`: apply Rule 9R with --apply mode
- `--audit`: Gemini-powered audit against paradigmatic forms (requires GEMINI_API_KEY)

### 🟡 Phase 3.1 — Morpheme Inventory & Slot System
**Scripts:** `scripts/extract_appendices.py`, `scripts/morpheme_inventory.py`
**What it does:**
1. Extracts conjugation paradigms from scanned PDF appendices via Gemini OCR (PyMuPDF→PNG→Gemini)
2. Defines the complete 30-slot verb template (8 proclitic + 18 inner prefix + 4 suffix slots)
3. Maps 164 morpheme abbreviations to their forms and slot positions
4. Implements conjugation engine: (stem, class, person, number, mode, aspect) → inflected form
5. Validates against 770 Appendix 1 paradigm forms

**Extraction results:**
- Appendix 1: 770 forms (7 verbs × 10 modes × 11 person/number) — 100% extracted
- Appendix 2: 9 irregular verb roots (suppletive sg/du/pl stems)
- Abbreviations: 164 entries with morpheme forms
- Grammatical Overview: 23/23 pages extracted (pages 1,3,7,16 recovered via plain-text Gemini at 400 DPI)

**Extraction audit findings:**
- Appendix 1: all 770 forms present, no nulls/errors; verb_class metadata missing on all 7 pages; 2/7 headings null/empty
- Abbreviations: 81/164 have null morpheme_form (expected for non-morpheme abbrevs like "an.", "Ar."); key person prefixes present
- Grammar pages 1,3,7,16: originally failed due to Gemini empty responses on structured JSON; recovered using plain-text prompts at 400 DPI (page 3 required split-page extraction for Table 5)
- Recovered tables: Table 5 (Derivational Affixes), Table 9 (Pronominal Prefixes), Table 15 (Verb Stem Template), Table 16 (Verb Suffix Template)

**Verb template (Parks Tables 6-7):**
- Proclitics: QUOT wi-, DUB kuur-/kuruur-, INFR tiir-, EV ar-, DU si-, INDF ku-, REFL witii-, NEG kara-/ka-/kaaku-
- Inner prefixes (slots 10-26): MODE → AGENT → INCLUSIVE → PL/POSS/PREV → PATIENT → INF.B → PHY.POSS → BEN/PREV → SEQ → AOR → ADV → PL → PL → PL → NOUN → STEM
- Suffixes: ASPECT → SUBORDINATION → INTENTIVE → SUB.INTENTIVE

**Conjugation engine:**
- Assembles morphemes by slot, concatenates, applies unrestricted phonological rules
- Rule 2R (dominant a) applied at mode+preverb boundary via _smart_concatenate
- Preverb alternation: ir- → iir- (1/2.A) / a- (3.A)
- For verbs with ut- preverb: fused into stem (e.g., ut-+aar→ stem "uutaar")

**Validation results (latest — 2026-03-12):**
- 770 forms tested: 587 exact (76.2%), 153 close (19.9%), 30 mismatch (3.9%)
- Per verb: to go 94%, to drink it 89%, to be sick 88%, to have it 85%, to be good 79%, to do it 67%, to come 31%
- "to come" improved from 21→34 exact (70 close = accent-only); 6 remaining MISS are assertive/absolutive 3du stem, gerundial 2sg, 3pl sub suffix
- Remaining gaps: "to do it" (12 MISS), "to be good" (3 MISS), "to be sick" (4 MISS), "to drink it" (3 MISS)

**Known gaps for refinement:**
- "to come" (34/110): 70 close matches are accent-only; 6 remaining MISS: assertive/absolutive 3du uses sg stem instead of du stem, gerundial 2sg GER shortening fires incorrectly, 3pl sub suffix contraction deletes stem
- "to do it" (74/110): 12 MISS — needs investigation (largest remaining gap after "to come")
- "to be sick" remaining 4 mismatches: gerundial du/infinitive structural anomalies (likely OCR artifacts)
- "to be good" remaining 3 mismatches: minor plural/dual edge cases
- Accent mark generation: ~85 forms have accents (mostly "to come"), implementing stress assignment would boost 70+ close→exact (~9%)
- Dictionary-wide stem extraction: main bottleneck for dict validation (14.8% exact)

**DB tables added:** `verb_paradigms`, `irregular_verb_roots`, `morpheme_abbreviations`, `morpheme_inventory`, `verb_template_slots`
**Report:** `reports/phase_3_1_morphemes.txt`

Tasks completed:
- [x] Extract Appendix 1 verb conjugation paradigms via Gemini OCR
- [x] Extract Appendix 2 irregular verb root tables
- [x] Map all 164 morpheme abbreviations to their forms and slot positions
- [x] Define slot ordering: proclitics → mode → person → preverb → stem → aspect → subordinating
- [x] Encode verb class rules: how each class modifies dependent forms
- [x] Build conjugation engine: (stem, class, person, number, mode, aspect) → inflected form
- [x] Validate against Appendix 1 paradigms (first pass: 12.7% exact, singular ~33%)
- [x] Gemini-powered dual/plural morpheme analysis (all 7 verbs → `extracted_data/dual_plural_analysis.json`)
- [x] Suppletive stem system: SUPPLETIVE_STEMS dict with du/pl stem lookup per verb
- [x] Fix si- proclitic (1du_incl excluded), 1pl_incl agent=t, r→h before consonants
- [x] Descriptive verb 3pl suffix (-waa), Class 3 si- for plural, pl_absorbs_raak flag
- [x] Partial descriptive verb person marking (ku- proclitic, h- 3PM)
- [x] Second pass validation: 20.9% exact (161/770), 31.7% close
- [x] Descriptive verb sub-classification: ku-proclitic (class u/wi without preverb) vs uur-preverb (standard agent prefixes)
- [x] Gerundial decomposition: irii(GER) + ra(MODE) replaces monolithic iriira
- [x] Potential mode: kuus-/kaas- with 2sg agent suppression, shortening before POT.i+V
- [x] Assertive mode Rule 2R: rii + a → raa
- [x] "to go" agent+stem fusions: t+war→tpa, s+war→spa via du_agent_fusions dict
- [x] ku- slot ordering: moved from proclitic slot 6 to inner slot 12.5 (after MODE)
- [x] Class 3 1pl_incl: acir- (not a-) for inclusive, agent t- suppressed
- [x] Imperfective aspect: -huʔ (non-subordinate) / -hu (subordinate) suffix
- [x] Dictionary-wide validation: --validate-dict mode (9,583 forms across all dictionary verbs)
- [x] Appendix 3 extraction: 23 kinship terms (consanguineal + affinal + possessive paradigms)
- [x] Gemini-collaborative morphophonological analysis: 3-round diagnosis → 10 rule fixes (35%→51%)
- [x] "to go" suppletive 3pl: pl3_stem with PREV_3A label for correct vowel contraction
- [x] "to drink it" pl_agent_fusions, sub_stem shortening, 3pl raak prefix
- [x] Potential mode shortening conditioned on agent presence
- [x] Sound change VOWELS sets updated to include accented vowels (áíú)
- [x] Descriptive-ku verb overhaul: 4-way person category system (excl/2nd/3rd/incl), DESC_KU_MODE_OVERRIDES table, raktah plural, 3pl prefix markers, ku→kuu lengthening, gerundial mode decomposition, potential mode reordering, aca→acu u-raising — "to be sick" 34%→88%
- [x] "to come" negative mode: kaakaa underlying form with extended shortening rules (+2)
- [x] "to come" 3.A stem ʔaʔ/ʔa: initial glottal surfaces in non-indicative/non-negative modes
- [x] Subjunctive aa shortening: only before u-initial morphemes (not i/r) — "to have it" +6
- [x] "to come" gerundial: ir-preverb sg 1sg/2sg skip MODE ra; 1sg also skips AGENT; GER shortening label-gated
- [x] "to come" potential mode: preverb irii (1/2) / aa (3rd+1pl_incl); no POT.i; TR_MARKER boundary protection; mode shortening only before aa preverb; 1du_incl uses acir+POT.i instead
- [x] "to come" infinitive mode: preverb ih (1/2) / a (3rd) placed BEFORE INF.B ku via INF_PREV label; 3.A stem for all sg; short stem ʔ-deletion threshold tightened

**Validation at the time (latest pass — 2026-03-19).** These figures were measured against the stored copy of Appendix 1, which had 152 misread forms. Against the appendix as corrected from the page on 2026-11-13 the engine gets 611 of 770 exact (79.4%).
- Appendix 1: **90.3% exact (695/770)** — accent rules integrated via `_apply_ir_accents` (inline, morpheme-level) for ir-preverb verbs + `apply_accent_rules()` (surface-form, non-ir-preverb) for potential cí pattern
- Per verb: to go 96%, to come 94%, to drink it 92%, to do it 89%, to be sick 88%, to have it 88%, to be good 85%
- Dictionary: **86.6% exact** (1,914/2,211 form_2 predictions via `stem_extractor.py`), 88.4% with close — up from 14.8% → 62.0% → 83.5% → 86.6%

**Major improvements since first pass (12.7% → 76.2%):**
- Gemini-collaborative 3-round diagnosis with 10 morphophonological fixes (+25%)
- Rule 24 glottal stop deletion, siʔV epenthesis, r→h before high vowels
- uur preverb ih removal, acir+V r-loss, ʔ deletion after consonant
- Potential shortening conditioned on agent presence
- "to go" suppletive 3pl stems with PREV_3A label (avoids Rule 2R)
- "to drink it" sub_stem shortening, 3pl raak prefix, pl_agent_fusions
- Descriptive-ku verb system overhaul: DESC_KU_MODE_OVERRIDES, raktah plural, 3pl prefix markers, ku→kuu lengthening, aca→acu u-raising (+8%)
- "to come" structural fixes: negative kaakaa, 3.A stem, subjunctive shortening, gerundial/potential/infinitive preverb handling (+4%)

Tasks remaining (priority order — revised 2026-03-19):
- [x] ~~"to be sick" descriptive verb fixes~~ — **done**: 37→97/110 exact (88%)
- [x] ~~"to come" structural fixes~~ — **done**: 21→34/110 exact (31%), 70 close (accent-only), 6 remaining MISS
- [x] **Dictionary stem extraction — first pass** — **done (2026-03-19)**: `stem_extractor.py` predicts form_2 for all 2,211 dictionary verbs. 14.8% → 62.0% exact (1,370/2,211), 67.5% with close. Pipeline: preverb parsing → class inference → prefix+stem junction → coalescence → perfective finals. Parks Ch. 3 OCR'd as reference.
- [x] **Dictionary stem extraction — second pass** — **done (2026-03-19)**: 62.0% → **83.5% exact** (1,846/2,211), 86.3% with close. 12 fixes: i+i coalescence bug, aa/ii/uu-initial glottal insertion, VR reflexive witi- prefix, bracket notation ([+ neg.], [+ i-], [+ raar-], [+ ruu-]), r-deletion vowel-specific ʔ rules (-uur→-uuʔ, -aar→-aa, -iir→-ii), VD ʔ-echo insertion before stops, ir+ut/uur preverb chains, class 3 -aʔu/-aʔa contractions, ut+w junction (w→p), uur+h/s junction (h-absorption, s→c), -sk→-s and -hc→-c cluster rules, (4)-sa no ʔ, (wi) k→t, -i notation stripping.
- [x] **Dictionary stem extraction — third pass** — **done (2026-03-19)**: 83.5% → **86.6% exact** (1,914/2,211), 88.4% with close. 12 fixes: a+u/a+i coalescence for ir-preverb, VD echo false-positive prevention, VD echo for -Vht clusters, VD -wii/-wiir shortening, -uuh shortening, ir+ut junction (keep tuut), class 3 aaʔa contraction guard, ir+ri+uur fusion (ri+uur→ruur), ir+uur h-absorption.
- [ ] **Dictionary stem extraction — fourth pass** (optional) — remaining 257 misses: `si-` prefix (16), `ruuti-` prefix (19), prothetic vowel (5), internal long-vowel shortening, multi-word/bracket headwords. Diminishing returns — remaining cases need morphological decomposition or manual analysis.
- [x] **✅ Accent mark generation + integration** — **done (2026-03-20)**: `accent_rules.py` correctly assigns accent marks to 78/85 Appendix 1 accented forms. 4 rules: (A) Agent-boundary í after t/s/c, (B) Mode-prefix accent (assertive rí, contingent í, gerundial írii), (C) Infinitive kú, (D) Dual sí in absolutive/assertive/negative. Remaining 7 failures are verb-specific stem accents (not generalizable without per-verb annotation). **Integrated into `morpheme_inventory.py`**: ir-preverb accents handled by inline `_apply_ir_accents` (morpheme-level, pre-concatenation); non-ir-preverb accents handled by `apply_accent_rules()` (surface-form, post-sound-changes). Gated by preverb type: uur-preverb does not produce accented forms.
- [ ] **"to do it" investigation** (74/110, 12 MISS) — largest remaining mismatch gap after "to come"
- [ ] **"to come" remaining 6 MISS** — assertive/absolutive 3du (3.A stem used instead of du stem), gerundial 2sg (GER shortening fires on PREV label), 3pl sub suffix contraction (stem deleted); also 3pl sub `verb_class='1'` string adds SUB suffix incorrectly
- [x] ~~VD(u) descriptive verb stem extraction~~ **now 78.2%** (was 1% → 44.7% → 78.2%) — remaining: internal long-vowel shortening, aw- absorption
- [x] ~~VT(3) Class 3 ut- fusion logic~~ **now 100% for (3)|(ut...)** (was 0% → 44.4% → 100%) — aʔuk/aʔu/aʔa contractions all handled

### ✅ Phase 3.1.5 — Noun Possession Morphology *(completed 2026-03-18)*
**Priority:** ✅ Complete (#1 on roadmap)
**Scripts:** `scripts/noun_possession.py` (extraction/classification), `scripts/possession_engine.py` (generation engine), `scripts/example_filter.py` (Skiri-aware example matching)
**Web:** `web/templates/_possession_widget.html` (morpheme chip UI), `web/app.py` (possession API + example filter integration)
**Output:** `extracted_data/noun_possession_catalog.json`, `reports/phase_3_1_5_noun_possession.txt`

Skiri has **four distinct possession systems**, not one. Each applies to different noun classes with different morphological mechanisms. The grammar engine now knows which system to use for any given noun, generates the correct form, and displays it in the web UI with morpheme-level breakdown and confidence scoring.

**The four systems (from Parks Grammatical Overview pp. 36–37 + Blue Book Lessons 5, 7):**

| System | Applies to | Mechanism | Example |
|--------|-----------|-----------|---------|
| 1. Kinship | N-KIN (~23 terms) | Suppletive stems — irregular my/your/his forms | "mother": my=atiraʔ, your=asaas, his=isaastiʔ |
| 2. Body part / physical | N-DEP (body parts) | ri- (PHY.POSS) prefix in verb introducer; noun incorporated | ti+ri+t+kirik+ta → "Ti rit•kirik•ta" (Here is my eye) |
| 3. Agent possession | N (general nouns) | ku-(INDF) + gerundial possessive verb + NOUN | kti ratiru pakskuuku' (my hat) |
| 4. Patient possession | Any noun | uur- prefix when non-agent possesses | tatuuhkuutit aruusaʔ (I killed YOUR horse) |

**Validation (2026-03-18):** 40/40 tests passing (33 possessive + 7 locative/instrumental). Covers all 4 possession systems plus case suffixes, validated against Blue Book Lessons 5, 7, 8 and Grammatical Overview Table 4.

**Validation (2026-11-13):** the built-in list now has 49 checks. When first re-run it gave 31 of 49: the engine was looking for `appendix3_kinship.json` under `scripts/`, so no kinship form was found and `/api/possession/<kinship noun>` returned a server error. With the path corrected: 47 of 49, and the API answers for every noun.

**Suffix corrected (2026-11-13).** The engine built its instrumental and body-part locative with *-biriʔ*. Parks's suffix is *-hiriʔ* (Grammatical Overview p. 30, read from the page image); the `b` came from the AI extraction of that page, and the note above about `b` being an allophone was a rationalisation of the misreading. How *-hiriʔ* attaches was measured on the 42 dictionary words whose etymology ends in it: h stays after a vowel (21 of 21), is lost after a consonant (13 of 13), and after r either the h is lost (2) or, in the one element *-haar*, the r is (6). The engine follows that (`hiri_suffix()`), its plural check now expects Parks's attested *ikstaaririʔ*, ten attested words were added as checks, and it no longer tries to call the conjugation engine's assembler (a call that had never worked). **59 of 59**, the same from the command line and inside the web app; no generated form contains a `b`. What is still wrong with its output is open item 13.

Tasks completed:
- [x] Extract & classify all nouns — filter S2E for N/N-DEP/N-KIN; extract stems (strip -uʔ/-kis); classify by possession system
- [x] Build kinship paradigm table — map appendix3 data to structured 1sg/2sg/3sg forms; cross-validated against Blue Book Lesson 7
- [x] Implement body-part possession constructor — MODE+ri+AGENT+STEM+VERB for any body-part noun; position verb selection (ku vs ta); sound change fallback
- [x] Implement agent possession constructor — `kti + GER-POSS-VERB + NOUN` for 1sg/2sg/3sg (ratiru/rasiru/rau); Blue Book p.35 attested
- [x] Document patient possession pattern — uur- prefix construction; slot 18 in morpheme inventory
- [x] Implement locative suffix system — -biriʔ (body part LOC/INST), -kat (general LOC), -ru/-wiru (tribal/geo LOC); body-part plural -raar- before -biriʔ; 3-class noun routing per Table 4
- [x] **Fix -biriʔ allomorphy (2026-03-20):** b → Ø / C_ (any consonant-final stem). Parallel to -wiru/-ru tribal alternation. Vowel-final stems preserve b (kitkahahki+biriʔ), consonant-final delete it (iks+iriʔ). Parks' /b/ is an allophone (not a phoneme) surfacing only after vowels at morpheme boundaries.
- [x] Handle N-DEP relational nouns — `KNOWN_BODY_PART_STEMS` (25 entries) and `KNOWN_RELATIONAL_STEMS` (5 entries) sets; asaa- "horse/dog", siis- "sharp object" route to agent possession instead of body-part incorporation
- [x] Validate against 40 Blue Book + Grammatical Overview examples — all 4 systems + locative/instrumental
- [x] Populate DB tables — `noun_stems`, `kinship_paradigms`, `possession_examples`
- [x] Integrate into web UI — possession widget with My/Your/His card toggle; color-coded morpheme chips by semantic role (mode/poss/agent/noun/verb/kin); ATTESTED/COMPUTED/LOW confidence badges; locative/instrumental case panel; construction formula display
- [x] Morpheme role classification — `_classify_morpheme_role()` maps labels → UI roles; `morpheme_chips` array in API response for structured rendering
- [x] Possession API — `/api/possession/<headword>` route; Flask blueprint; lazy headword set cache; stub `_lookup_noun_class()` for DB query
- [x] Example filter — `example_filter.py` with Skiri-aware word boundary matching; rejects false substring matches (kirike "what?" ≠ kiri "cat"); handles OCR variants (J→E, 1→E), morpheme-boundary compounds (kiri•wusu' ✓), epenthetic-h compounds (kirihkaatit ✓), prefix disambiguation; wired into `entry_detail()` route filtering both dictionary examples and BB attestations; 14/14 tests
- [x] Kinship dispatch fix — dispatcher tries kinship lookup first for any noun regardless of `noun_class`; handles N-KIN entries stored as plain "N" in DB

**Nominal morphophonology fixes (2026-03-20/21):**
- [x] **Nominal sound change pipeline split** — `apply_nominal_sc()` in `sound_changes.py` runs only noun-safe rules (excludes verb Rules 17/18/19). `possession_engine.py` prefers this over the full verb pipeline. Fixes `ikciriʔ` → `iksiriʔ` (attested).
- [x] **raar→taar resolved** — was Rule 8R (r→t after hard C) all along, masked by Rule 17 corruption. `ikstaaririʔ` now matches attested form with nominal pipeline.
- [x] **-sukat allomorph** — stems ending in -ki/-ski get `-sukat` (not `-kat`). `piiraskisukat`, `asaakisukat` now generate correctly.
- [x] **Instrumental animacy filter** — `generate_instrumental()` accepts `semantic_tags`, returns `None` for animate nouns (N-KIN, kinship/social/animal tags). Widget handles None gracefully.
- **Pattern note:** Three suffix alternations (b→Ø, raar→taar, wiru→ru) all conditioned by same post-consonant environment — single underlying consonant-cluster simplification rule at nominal morpheme boundaries.

**Tagging fixes (2026-03-21):**
- [x] **Kinship false positive guard** — `tag_entries.py` skips kinship keyword path if `grammatical_class` doesn't contain N. Prevents 35 verb false positives.
- [x] **Kinship tag cleanup** — 36 erroneous tags removed (35 verbs + 1 Gemini error). 8 age/gender nouns retagged kinship → social. Tahkuki/Coyote flagged for cultural advisor review.
- [x] **Social keyword expansion** — age/gender/social role terms (youth, lad, maiden, elderly, etc.) added to social taxonomy.

**BB/Parks merge (2026-03-21):**
- [x] **5 orthographic variant pairs merged** — `bb_variant_of` column added to `lexical_entries`. BB stub entries retained for search aliasing. Parks entries marked `blue_book_attested=1`.

**Bug fixes applied during deployment:**
- Kinship file path resolution (REPO_ROOT parent vs current dir)
- Locative test inputs (tribal names need base forms, not already-inflected forms)
- N-DEP relational noun routing (asaa- → agent possession, not body-part)
- Example filter compound heuristic (tightened from `remainder[0] in 'hrstpk'` to epenthetic-h only `remainder[0] == 'h' and len(remainder) >= 3`; prevents kirike false positives when kirike isn't in headword set)
- OCR normalization in example filter (`J→E`, `1→E` for Blue Book header artifacts)

**Key architecture decisions:**
- Agent possession uses attested fixed forms (ratiru/rasiru/rau) rather than generating via conjugation engine — safer, since gerundial+A.POSS interaction hasn't been validated
- `kti` = `ku(INDF)` + `ti(IND.3)` contracted; body part is always 3rd person subject of the position verb
- Locative/instrumental are case forms, not possession — but they share stem extraction and are naturally displayed alongside possession paradigms
- Example filter uses a global headword set (lazily cached at first request) for disambiguation; modifies entry data in-place before template rendering

### 🟡 Phase 3.1.6 — Function Word & Particle Inventory *(seeded 2026-03-19)*
**Priority:** Medium (needed for sentence construction; these are the glue words)
**Depends on:** Phase 3.1 (morpheme slot system), Phase 2.1 (semantic tags)
**Effort:** Medium
**Scripts:** `scripts/function_word_inventory.py`, `scripts/extract_function_words.py`
**DB table:** `function_words` (418 rows: 355 Parks dictionary + 2 BB direct + 61 BB phrase-extracted via Gemini)

Dictionary entries classified as CONJ, DEM, PRON, QUAN, LOC, INTERJ, ADV need to be formalized into a structured inventory with usage rules — not just dictionary definitions. For sentence construction (Phase 3.2), these must be queryable: "which demonstrative goes with visible referents?" "where does the question particle go in the clause?"

**Seed data (2026-03-19):**
- 355 function words from Parks dictionary (lexical_entries with class in CONJ/DEM/PRON/QUAN/LOC/INTERJ/ADV/NUM)
- 2 new function words from BB gap triage direct classification
- 61 new function words from BB phrase extraction via Gemini (5 batches → 35 unique words, 147 occurrences; 4 genuinely new after dedup: `rahesa` "tomorrow", `rariksisu` "hard/very", `tiku` "that", `tireku` "here is")
- OCR artifacts pruned from Gemini extraction; `bb_function_words` raw table has 63 rows (23 unique)
- Report: `reports/extract_function_words.txt`

Tasks:
- [x] Inventory all function words from dictionary (~355 entries across classes)
- [x] Seed from BB gap triage function_word category (11 items → 9 new after dedup)
- [x] Gemini-extract function words from 196 BB phrase gaps (57 new items)
- [x] Prune OCR artifacts from Gemini extraction (done — length ≤ 2, dot-prefixed removed)
- [x] Classify demonstratives by spatial/visibility distinction — **done (2026-03-20)**: `classify_function_words.py` assigns demonstrative-spatial subtypes (proximal, distal, distal-plural, far-distal, etc.) from Parks Ch. 4
- [x] Map interrogative particles and their clause-position rules — **done (2026-03-20)**: 10 interrogatives mapped (content-question, location-question, yes-no-question, quantity-question, temporal-question, indefinite)
- [ ] Document discourse/evidential particles (evidentiality is marked by proclitics, but also by standalone particles)
- [x] Add position_rule + refined_subclass columns — **done (2026-03-20)**: `classify_function_words.py` classifies all 418 items. Distribution: 149 PROCLITIC, 135 PRECEDES-VERB, 51 PRECEDES-NOUN, 44 CLAUSE-INITIAL, 28 STANDALONE, 11 BETWEEN-CLAUSES
- [ ] Cross-reference with Blue Book dialogue examples for natural usage patterns
- [ ] Integrate into sentence builder (Phase 3.2) as selectable modifiers

### 🟡 Phase 3.2 — Sentence Construction Framework *(3.2a done; 3.2b first slice done)*
**Priority:** Medium (depends on 3.1 accuracy improvements + 3.1.5 noun morphology)
**Depends on:** Phase 3.1 (morpheme slot system at 60%+ accuracy — **now at 76.2%**), Phase 3.1.5 (noun possession), Phase 3.1.6 (function words)
**Effort:** Very Large — **now broken into 3 sub-phases to make progress incremental**

Given English input, construct Skiri output.

Sources:
- `extracted_data/appendix3_kinship.json` — 23 kinship terms with possessive paradigms (already extracted)
- `extracted_data/grammatical_overview.json` — 23 pages of grammar (clause structure, word order)
- Blue Book lesson dialogues as test cases (88 examples currently in DB)

#### ✅ Phase 3.2a — Template-Based Sentence Assembly
**Scripts:** `scripts/sentence_templates.py`, `scripts/template_slot_fillers.py`
**Design doc:** `prompts/phase_3_2a_sentence_templates.md`

DONE — 10 templates covering 73% of Blue Book sentences, web UI at
`/sentence-builder` (template cards → slot fill → assembled sentence with
morpheme chips, confidence badge, BB attestation). 27 exact-match validation
tests against BB sentences.

#### 🟡 Phase 3.2b — Person/Mode Derivation *(first slice DONE 2026-09-01)*
**Script:** `scripts/person_forms.py` (validated 27/27 vs the stored Appendix 1 at the time; 25/27 vs the appendix as corrected from the page on 2026-11-13, see open item 26)

Key insight: the from-scratch conjugation engine (`morpheme_inventory.conjugate`)
reproduces only 14.8% of attested dictionary forms — but the person/mode
prefixes sit at the LEFT EDGE of forms the dictionary already attests, and
alternate regularly (IND ta-/ti- ↔ ABS ra-/ri-; 1.A t ↔ 2.A s). So derive
unlisted forms FROM attested ones instead of computing from scratch:

- **2sg indicative** from form_1 (agent t→s with junction repair: r-stems
  tah-→tast-, t-stems tac-→tas-, w-stems tatp-→tasp-; junctions learned from
  1,617 attested form_1/form_2 pairs)
- **absolutive mode** (ka/kirike/kiru questions) by mode-prefix swap
  (1st/2nd: t→r; 3rd: ti→ra, tu→ru, tih→riih desc, tiʔ→raʔ)
- **descriptive-ku persons** for VD/VL (3sg ti+STEM → 1sg tiku+STEM,
  2sg ta+STEM, 2sg-abs raa+STEM)
- **present/future for 1sg/2sg** by person-prefix transplant onto attested
  form_3 (IMPF) / form_5 (INT)

Coverage (2,242 paradigm verbs): 2sg 78%, 3sg-absolutive 91%, 1sg/2sg
future 77–78%, present 50–57%. Every derived form is one left-edge prefix
swap away from an attested form.

Integration: T3/T4/T5/T8/T9 accept `verb` + `person` (1sg/2sg/3sg) +
`tense` (past/present/future) slots — auto-conjugated, derived forms capped
at MEDIUM confidence with a derivation note. Web UI: verb search
(`/api/verbs`) + who/when selectors. Validation: 34/34 template tests.

**Modern spelling + pronunciation on sentences (added 2026-09-01):**
`display_utils.modernize_form()` / `respell_form()` — c→č context rule
(c = [č] before vowel, [ts] elsewhere) validated at 98.5% against 1,387
attested phonetic c-positions; end-to-end 99.5% agreement reproducing
attested normalized_forms from headwords. Sentence results now carry
`modern_sentence` + `approx_pronunciation`, and each morpheme chip carries
modern/pron/ipa. **Truth policy: IPA is never generated** — Parks's IPA marks
vowel reduction (ə/ɪ/ʊ) and pitch accent, which are not predictable from
spelling; chips show IPA only when the word is a dictionary headword with an
attested phonetic_form. Spelling-derived pronunciations are labeled ≈.

Remaining 3.2b tasks:
- [ ] Plural persons (3pl raar-insertion; du/pl suppletive stems — hard, many
      verbs use distributive stems not recoverable by prefix swap)
- [ ] Negative mode (kaaka- prefix swap — same left-edge pattern, easy win)
- [ ] Imperfective coverage (only 57% of verbs list form_3)
- [ ] Question particle placement + clause ordering (original 3.2b scope)

#### Phase 3.2b — SOV Word-Order Engine
**Priority:** Medium
**Effort:** Medium
**Depends on:** Phase 3.2a (templates provide test cases)

Takes pre-inflected components and arranges them in correct Skiri clause structure.

Tasks:
- [ ] Map English sentence patterns to Skiri clause structure (SOV word order)
- [ ] Handle question particle placement and clause-final positioning
- [ ] Handle subordinate clause ordering (from grammatical overview)
- [ ] Implement basic coordination (and, but, then) using CONJ inventory from Phase 3.1.6

#### Phase 3.2c — Compositional Sentence Construction
**Priority:** Low (most ambitious sub-phase)
**Effort:** Very Large
**Depends on:** Phases 3.2a, 3.2b, and high-accuracy stem extraction

Full compositional system handling transitivity, evidentials, and complex clauses.

Tasks:
- [ ] Handle transitivity: subject/object marking, preverb system (ut-, ir-, uur-)
- [ ] Implement proclitic system (indefinite ku-, reflexive witi-, dual si-, etc.)
- [ ] Implement evidential system (quotative wi-, dubitative kuur-, etc.)
- [ ] Possessive morphology from kinship data (my/your/his-her paradigms)
- [ ] Blue Book lesson dialogues + kinship constructions as test cases

### ✅ Phase 4.1 — Web Search Interface
**Script:** `web/app.py` (Flask application)
**Depends on:** Phase 1.2 (SQLite DB)

**Stack:** Flask + SQLite (`skiri_pawnee.db`) + Pico CSS + HTMX

**What it does:**
Full-featured web dictionary with bidirectional search, entry detail views, browsing,
flashcards, and live search. Mobile-responsive via Pico CSS framework.

**Features implemented:**
- [x] Backend: Flask app with SQLite read-only connection, HTMX live search
- [x] Bidirectional search: English -> Skiri (FTS on glosses + english_index), Skiri -> English (headword, normalized_form, paradigmatic forms)
- [x] Entry detail view: headword, pronunciation (IPA + simplified), glosses, etymology with morpheme breakdown, paradigmatic forms, full conjugation tables, examples, cognates, cross-references, derived stems, Blue Book attestations, semantic tags
- [x] Morpheme breakdown display: etymology constituent elements shown as morpheme table (prefix/stem/suffix labels from Parks)
- [x] Fuzzy matching: LIKE pattern matching + Levenshtein distance (edit distance 1-2) on normalized forms for learner misspellings; aggressive fuzzy (strip glottals, collapse long vowels, normalize c/ts/ch) for learner-friendly lookups
- [x] Filter sidebar: semantic category tags, grammatical class, verb class (on search results page)
- [x] Blue Book attestation badge on entries and search result cards
- [x] Mobile-responsive design (Pico CSS framework, responsive grid, touch-friendly flashcards)
- [x] Mark generated vs. attested forms: "Attested (Parks Dictionary)" / "Attested (Appendix 1)" labels on paradigm tables
- [x] Browse by semantic tag and grammatical class with paginated results
- [x] Weekly flashcard study system: 21 categories, ~387 curated beginner words, flip-card UI with keyboard nav and shuffle. BB Essentials (Weeks 1-3) + Greetings & Common Words (Week 4) front-loaded; cross-category deduplication via `seen_ids`
- [x] **Pitch accent display** *(2026-03-20)*: `format_pitch` Jinja filter wraps UPPERCASE syllables in `<span class="pitch-high">` (bold + underline). All-lowercase pronunciations show "(pitch not marked)" note. Legend on entry detail, flashcard study, and flashcard guide pages. Applied in: `_entry_card.html`, `entry.html`, `flashcard_study.html`, `flashcards.html`
- [x] Word-of-the-day on homepage with dictionary stats
- [x] Search result re-ranking: exact matches first, BB-attested boosted, data completeness considered; example FTS matches surfaced with snippets
- [x] JSON API endpoint (`/api/search`) for external consumers
- [x] Detected language returned from search for UI display
- [x] Deployment: `requirements.txt` provided; run with `python -m web.app`
- [x] **Noun possession widget** — lazy-loaded via `/api/possession/<headword>` on noun entries; My/Your/His card toggle; color-coded morpheme chips by semantic role (mode/poss/agent/noun/verb/kin); ATTESTED/COMPUTED/LOW confidence badges; locative/instrumental case-form panel; auto-expand for N-DEP/N-KIN, lazy-expand for N
- [x] **Example filter** — Skiri-aware word-boundary matching on entry detail pages; removes false substring matches (kirike "what?" ≠ kiri "cat") from both dictionary examples and Blue Book attestation tables; cached headword set (~4,273 entries) built lazily on first request
- [x] **Data quality dashboard** — `/dashboard` route with corpus stats, field completeness, verb engine coverage, possession engine coverage, E2S linking health
- [x] **UI/UX improvements** *(completed 2026-03-20)*:
  - Spelling preference toggle (Parks vs. Simplified): cookie-persisted, nav toggle, `primary_spelling`/`secondary_spelling` Jinja filters, all templates respect preference, search placeholder updates dynamically
  - Mobile responsive: hamburger nav (<768px), homepage grid stacking, filter sidebar collapse, conjugation table sticky first column, sentence builder bottom-sheet dropdowns, flashcard swipe gestures
  - Accessibility: search direction `role="radiogroup"` with `sr-only` radio inputs, `lang="x-paw"` on all Skiri text elements (entry, cards, flashcards, possession widget, sentence builder, guide), `aria-labelledby` on feedback modal, skip-to-content link, badge contrast WCAG AA compliant, flashcard keyboard nav (arrows, Enter/Space)
  - Learner-friendly: collapsible `<details>` entry sections, learner/expert view toggle (localStorage), pronunciation tooltip `_pronunciation_help.html`, flashcard self-assessment (Got it/Missed with localStorage progress tracking, Review Missed, session summary), "Start Here" beginner card on homepage, learning path timeline on flashcards overview
  - Browse: human-readable grammatical class labels (`GRAM_CLASS_LABELS` dict via context processor, displayed on browse page and as badge `title` attributes)
  - Search: direction toggle on both index and results pages, direction persisted in form params, BB verb form search endpoint (`/api/bb_verb_forms`)

**Routes:**
- `/` — Homepage with stats and random word
- `/search?q=...` — Full search with filters
- `/search/partial?q=...` — HTMX live search endpoint
- `/api/search?q=...` — JSON API endpoint (limit capped at 100)
- `/api/possession/<headword>` — Possession paradigm JSON (morpheme chips + locative forms)
- `/entry/<entry_id>` — Full entry detail (with example filter + possession widget)
- `/browse` — Browse by tag/class
- `/browse/tag/<tag>` — Entries by semantic tag
- `/browse/class/<class>` — Entries by grammatical class
- `/flashcards` — Weekly flashcard overview
- `/flashcards/<week>` — Interactive flashcard study session
- `/dashboard` — Data quality dashboard (corpus stats, completeness, engine coverage, confidence distribution, feedback stats)
- `/about` — About page with data source info
- `/api/feedback` — POST: submit flag/confirm feedback on an entry
- `/admin/feedback` — Review queue for community feedback (accept/reject with notes)
- `/admin/feedback/<id>/review` — POST: accept or reject a feedback item
- `/preferences` — POST: set spelling preference cookie (parks/simplified)
- `/guide` — Syllable pronunciation guide
- `/sentence-builder` — Sentence assembly UI
- `/api/assemble` — POST: assemble sentence from template + slot values
- `/api/slot-options` — Dropdown options for sentence builder slots
- `/api/bb_verb_forms?q=...` — Blue Book verb form search

### ✅ Phase 4.2 — Sentence Builder UI *(delivered with Phase 3.2a, 2026-03-20; person and tense selectors added 2026-09-01)*
**Priority:** Low (depends on Phase 3.2a at minimum)
**Effort:** Large

Guided interface: select person/action/object/tense → assembled Skiri sentence with morpheme breakdown. Shows derivation steps so learners understand *why* the form looks the way it does. Initially uses Phase 3.2a templates; grows with 3.2b/3.2c.

### ✅ Phase 4.3 — Confidence Scoring System *(completed 2026-03-19)*
**Priority:** ✅ Complete (#3 on roadmap)
**Implemented in:** `scripts/stem_extractor.py` (lines 897-1003), `web/templates/_entry_card.html`, `web/templates/entry.html`, `web/templates/dashboard.html`
**Built via:** Claude Code (VS Code) — parallel with stem extraction second pass

The attested/computed binary badge is replaced by a **continuous confidence score** (0.0–1.0) with 3-tier visual indicators, so learners know *how* trustworthy a computed form is.

**Confidence engine (`compute_confidence()`)** — 4-factor weighted score:

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Category accuracy | 50% | Per-`(class)\|(preverb)` exact+close rate from `stem_extractor.py` validation |
| Prediction method | 20% | Boost for explicit `verb_class` and `stem_preverb` fields (vs inferred) |
| Stem complexity | 15% | Penalties for bracket notation `[+ neg.]`, slash alternates, multi-word headwords |
| Sample size | 15% | Bayesian shrinkage — small categories regress toward population mean |

**DB:** New column `lexical_entries.form2_confidence` (REAL, 0.0–1.0). Populated via `python scripts/stem_extractor.py --confidence`.

**Web UI:**
- Search result cards (`_entry_card.html`): green/gold/red badge with tier label
- Entry detail headers (`entry.html`): same badge + score value
- API search results: `form2_confidence` field in JSON
- Dashboard widget (`dashboard.html`): stacked bar chart with high/med/low counts + average

**Results:**

| Tier | Score | Count | Description |
|------|-------|-------|-------------|
| High | ≥ 75% | 2,202 | Reliable predictions |
| Medium | 50–74% | 30 | Minor differences possible |
| Low | < 50% | 22 | Treat with caution |
| **Average** | **88.7%** | 2,254 | |

Tasks completed:
- [x] Define 3-tier confidence model (High ≥75%, Medium 50-74%, Low <50%)
- [x] Compute per-entry confidence scores using 4-factor weighted formula
- [x] Add `form2_confidence` column to `lexical_entries` DB table
- [x] Display confidence as color-coded badges on search cards and entry headers
- [x] Dashboard widget with distribution visualization
- [x] API endpoint returns confidence score
- [ ] *(deferred)* Tooltip/popover explaining what confidence means for that specific form
- [ ] *(deferred)* Log analytics: which confidence tiers are users viewing?

### ✅ Phase 4.4 — Community Feedback Mechanism *(completed 2026-03-19)*
**Priority:** ✅ Complete (#5 on roadmap)
**Implemented in:** `web/app.py`, `web/db.py`, `web/templates/entry.html`, `web/templates/dashboard.html`, `archived/scripts/add_feedback_table.py`
**Built via:** Claude Code (VS Code)

Knowledgeable community members (teachers, elders' family members, students) can now flag errors and confirm forms. All feedback goes through human review — never auto-accepted (Design Principle #6).

**DB:**
- `community_feedback` table: entry_id, feedback_type (flag/confirm), issue_type, suggested_correction, comment, reporter_name (optional), status workflow (pending→accepted/rejected), reviewer_note, timestamps
- Migration script: `archived/scripts/add_feedback_table.py`
- Separate writable DB connection in `db.py` — main dictionary stays read-only

**Entry detail page (`entry.html`):**
- "Flag an issue" button → modal with field selector, issue type, correction field, comment, optional name
- "Confirm this entry" → one-click crowd-sourced verification
- Per-entry feedback counts displayed

**Admin review queue (`/admin/feedback`):**
- Status tabs: Pending / Accepted / Rejected / Reviewed
- Per-item accept/reject with reviewer notes
- Linked to entry detail for context

**Dashboard (`dashboard.html`):**
- Feedback stats widget (total, pending, accepted, rejected) — appears when feedback exists

**API routes:**
- `POST /api/feedback` — submit flag or confirm
- `GET /admin/feedback` — review queue page
- `POST /admin/feedback/<id>/review` — accept/reject

Tasks completed:
- [x] Add "Flag this form" button on entry detail pages
- [x] Create `community_feedback` DB table with full schema
- [x] Simple review queue page (admin-only route) listing pending feedback
- [x] "Confirm this form" button for crowd-sourced verification
- [x] Per-entry feedback counts in entry detail view
- [x] Dashboard widget with feedback stats
- [x] Design principle enforced: never auto-accept corrections — all feedback goes through human review
- [ ] *(deferred)* Track acceptance rate analytics
- [ ] *(deferred)* Email notification to maintainer on new feedback

### ✅ Phase 5.1 — Structured Lesson Content *(v1 DONE 2026-09-01)*
**Script:** `scripts/build_lessons.py` (deterministic — no AI calls)
**Data:** `lessons` DB table + `extracted_data/lessons.json`
**Report:** `reports/phase_5_1_lessons.txt`

All 20 Blue Book lessons parsed straight from `Blue_Book_Pari_Pakuru.txt`:
Skiri + English titles (as printed; Lesson 8 has no English title in the
source and none was invented), page ranges, ordered dialogue exchanges
(Skiri/English line pairs split at sentence punctuation, mid-form syllable
dots preserved), and grammar/culture prose sections (NOUNS, PRONUNCIATION,
COMBINING ROOTS, USEFUL PHRASES...).

Web UI: `/lessons` (progressive lesson cards) + `/lessons/<n>` — vocabulary
tables drawn from `blue_book_attestations` with dictionary-entry links
(normalized form, pronunciation, class badge; "not in Parks dictionary"
label when unlinked), dialogues in BB practical spelling as printed,
collapsible grammar notes, and "Practice these patterns" cards that open
the sentence builder with the lesson's attested template preselected
(`/sentence-builder?template=Tx`).

- [x] Extract lesson dialogue texts with English translations (20 lessons)
- [x] Map lesson vocabulary to dictionary entries (via blue_book_attestations)
- [x] Extract grammar explanations per lesson
- [x] Lesson sequencing (Blue Book's own 1979 order preserved)
- [x] Link lessons to sentence-builder patterns (Phase 3.2a template map)
- [x] Interactive exercises *(2026-09-01)*: matching (click-to-pair vocab),
      fill-in-the-blank (dialogue lines with a lesson word blanked, 4-way
      multiple choice), and "say it in Pawnee" reveal drills. Generated
      deterministically per page load from the lesson's own verbatim
      material (`web/app.py:_build_exercises`) — no generated language.
- [~] Lessons 3–4 vocabulary gap: Gemini re-extraction of pp. 39–49
      (`scripts/extract_lesson_gaps.py`, dry-run/apply; existing rows never
      modified, new items matched via Phase 2.2 machinery)
- [ ] BB glossary pages (123–130, inside Lesson 20's span) not itemized

**Data safety (2026-09-01):** community_feedback now auto-exports to
git-tracked `exports/community_feedback.json` on every submit/review (the
one table not rebuildable from sources); backup scripts write to the
OneDrive-synced `pari_pakuru_backups/` (home-dir fallback), existing
backups copied over.

### ✅ Phase 5.2b — In-App Spaced Repetition *(2026-09-02)*
**Module:** `web/srs.py` (SM-2 scheduler, unit-tested 7/7 transitions)
**Route:** `/study` (+ `?lesson=N` / `?tag=X` scoping), `POST /api/srs/review`

Server-side SM-2 scheduling over dictionary entries (user does not use Anki
— review state lives in the DB: `srs_cards` + append-only `srs_reviews`,
covered by the OneDrive backup regime). Study UI reuses the flashcard
card-flip design with Again/Hard/Good/Easy grading (keyboard: space flip,
1–4 grade); "again" requeues the card within the session and lapses it.
New-card selection prefers BB-attested entries with pronunciations. Every
lesson page has a "Study this lesson's words" button scoped to that
lesson's vocabulary attestations. Nav: Study link.

### 🟡 Phase 5.2 — Spaced Repetition / Flashcard Export
**Priority:** High — **elevated** (low effort, high impact; Design Principle #3 says "export everything" but the export tasks are still unbuilt. A teacher can hand out a printed paradigm table *today*; accuracy improvements help later.)
**Depends on:** Phase 1.2 (dictionary data)
**Effort:** Small

Generate exportable study materials from the dictionary.

Tasks:
- [x] In-browser flashcard study system (weekly sets, flip cards, keyboard nav, shuffle) — built in Phase 4.1 (`web/flashcards.py`)
- [x] Semantic category decks (19 categories: kinship, animals, body, food, etc.)
- [x] Include pronunciation (IPA + simplified respelling) on every card
- [x] Blue Book-attested entries prioritized in card selection
- [x] **Anki deck export** — **DONE (2026-03-20), unused** (in-app study, Phase 5.2b, replaced it; the exported deck was removed from the repository on 2026-11-13). `scripts/anki_export.py`: 4,336 cards across 19 semantic tag decks + "All Words" parent. genanki .apkg output. Stable model/deck/note IDs for safe re-import. CLI flags: `--dry-run`, `--deck TAG`, `--advanced` (per-sense Option B), `--verbs-only`, `--bb-only`, `--min-confidence`.
- [x] **Pre-export data cleanup (2026-03-20):** `scripts/dedup_entries.py` removed 22 p2/p71 duplicate pairs + merged kusisaar parser artifact (4,366 → 4,343 entries). Preserved hiksukac (VD/VP) and racawaktaarik (VI/VT) as legitimate polysemy. `scripts/display_utils.py`: `display_headword()` with 5 rules (bracket, slash, paren onset, suffix paren, bound-morpheme dash), `gram_class_label()`, `morph_class_note()`. Tested against all 281 notation entries — zero problems.
- [x] **Card template spec locked:** Option A multi-sense (primary sense + "+N more" note), form2_confidence >= 0.75 threshold for verb forms, format_pitch_anki() for HTML pitch accent, per-class back notes (N-KIN, N-DEP, LOC, ADV-P), example dedup on english_translation.
- [x] **Printable flashcard sheets** — **DONE (2026-11-10)**: `scripts/build_flashcard_pdfs.py` → `curriculum/flashcard_pdfs/` (24 weekly PDFs, four cards to a sheet, double-sided).
- [ ] **🔴 Printable PDF wordlists and paradigm tables for offline use** — highest-impact remaining export for classroom use; target users may have inconsistent internet access. Same query as Anki, rendered via reportlab/weasyprint.
- [ ] Blue Book lesson-aligned decks (vocabulary per lesson)
- [ ] Audio placeholder fields (for future recordings)

### ✅ Phase 5.3 — Static site on GitHub Pages *(2026-09-12)*
**Script:** `scripts/build_static_site.py` · **Workflow:** `.github/workflows/static.yml` · **How to:** `DEPLOYMENT.md`

The search, flashcard and lesson pages are rendered from the Flask templates
into `docs/` and served by GitHub Pages. Search runs in the browser over
`docs/data/dictionary.json` (Fuse.js); there are no per-entry pages. The
workflow only uploads `docs/`; the site is rebuilt on a developer's machine,
because the database is not in git. Links are relative, so the site works
under the repository's Pages path.

### ✅ Extraction audit *(2026-09-01)*
**Report:** `reports/extraction_audit_2026-09-01.md` · **Repairs:** `scripts/fix_audit_issues.py`, `scripts/upgrade_phonetics_from_textlayer.py`

Question: is the database a faithful copy of the printed dictionary, and is
the learner spelling derived correctly?

- A stratified sample of 50 Skiri-to-English entries was checked field by field against the page: all 47 that could be located matched. English-to-Skiri linking: 5,132 linked subentries, none dangling.
- An independent re-implementation of the spelling rules reproduced the stored learner spelling for all 4,273 entries.
- Seven issues were found and repaired the same day: c/č under-conversion (60 spellings corrected), seven entries that had lost senses on import (the uniqueness rule on the `glosses` table was dropped), 23 of 32 missing IPA forms recovered, 227 leftover OCR characters, doubled examples after de-duplication, 315 verb forms with line-break hyphens, and drift between the JSON and the database.
- **Second-method cross-check.** Every IPA form was compared with the PDF's own text layer (`reports/_s2e_page_index.json`). 130 forms that had lost their special characters were replaced from the text layer; agreement between the two methods is now 99.76% (4,194 of 4,204 compared).

### ✅ Flashcard and static-site audit *(2026-10-01, follow-ups 2026-10-12)*
**Report:** `reports/audit_data_construction_2026-10-01.md`

Question: do the flashcards and the public site carry the data faithfully?

- Sound: pitch survived respelling in all 1,542 entries that have it; every flashcard carries IPA.
- Fixed 2026-10-01: the static site had dropped the IPA and the page references (A1, A2); definitions were being cut at 120 characters, including two band-name explanations (A3); multi-sense words showed one sense with no sign of the others (A4); 68 respellings contained stray `?` marks (B1, `scripts/fix_respelling_artifacts.py`).
- Fixed 2026-10-12: the flashcard curriculum is frozen in `curriculum/flashcard_sets.json` so that week numbers, to which learners' progress is keyed, no longer shift (B4, `scripts/freeze_flashcard_sets.py`). Lesson vocabulary linked to dictionary entries rose from 234 to 339 of 531 (`scripts/link_bb_vocab.py`). Fourteen OCR errors in lesson titles were repaired (`scripts/fix_lesson_titles.py`).
- Open: B2, B3, B5, B6, C1 to C5. See "Open items".

### ✅ Phase 6.1 — Word-building guide, version 1 *(2026-11-07 to 2026-11-10; superseded)*
**Scripts:** `scripts/root_extraction.py`, `scripts/build_root_curriculum.py` (+ `root_curriculum_spec*.py`) · **Output:** `curriculum/roots/`

First attempt to answer "which roots and affixes are used most, and in what
order should they be learned?" Every entry was segmented from the stored
parse of Parks's etymology and checked against the headword; roots were
ranked by the number of headwords containing them; seven units of lessons
were written by hand from a specification in which every Pawnee form is a
database lookup. 1,320 root senses; segmentation confidence 1,085 high,
1,575 medium, 1,683 low.

Done in the same days and **still in use**:

- `curriculum/weekly_flashcards.md` (`scripts/build_weekly_flashcards.py`): the 387 frozen flashcard words as 1,015 paper cards, Week 1 = Sunday 2026-11-08. (Rebuilt from version 2 on 2026-11-13: 372 words shown, 995 cards.)
- `curriculum/flashcard_pdfs/` (`scripts/build_flashcard_pdfs.py`): the same cards as printable double-sided sheets.
- Respelling repair (`scripts/fix_pronunciations.py`, report `reports/fix_pronunciations_report.txt`): optional sounds kept in parentheses, `{k/t}` alternations restored, Blue Book-only entries re-syllabified; 1,273 entries changed in the database, the JSON and the frozen sets; 32 stems left for review.

Version 1's analysis is superseded by Phase 6.2, which found that the stored
parse it relied on puts meanings on the wrong pieces. Its files are kept; see
`curriculum/README.md` for why.

### ✅ Phase 6.2 — Word-construction analysis, version 2 *(2026-11-12)*
**Instruction:** `prompts/skiri_word_construction_v2.md` · **Code:** `scripts/morphology_v2/` · **Output:** `curriculum/roots_v2/` · **Method:** `curriculum/roots_v2/METHOD.md`

A re-analysis built so that every claim can be checked: each Pawnee form is
looked up from a source record, each analysis gets a tier that follows
mechanically from its evidence, the rules were tested on entries not used to
tune them, and one command regenerates everything byte for byte.

**Evidence channels.** E1 Parks's printed etymology (re-parsed from the raw
text); E2 the pieces joined by named sound rules reproduce the headword; E3
the verb's five forms behave as the analysis predicts; E4 each piece recurs
with the same meaning in other words; E5 a Blue Book seam falls on a boundary
of the analysis; E6 Parks's grammar tables; E7 cognates (recorded only).

**Results** (run of 2026-11-13, after that day's data fixes; the first run differed by one root and three words).

| | |
|---|---|
| Words analysed | 4,337 lexemes (on 2026-11-12: 4,343 rows less six groups of true duplicates; those six rows have since been removed from the database) |
| Tiers | A 1,086 · B 1,320 · C 1,569 · D 1 · no claim 361 |
| Headword reproduced from Parks's pieces | exactly 3,103 · nearly 587 · not 286 (version 1 had 1,085 high-confidence segmentations) |
| Inventory | 1,699 lexical morphemes (A 308, B 246, C 1,145); 57 affixes (A 21, B 9, C 27) |
| Teachable building blocks (tier A or B) | 549 roots + 30 affixes |
| Words a learner can take apart completely | 1,791 (41.3%) with all 579 blocks; 480 (11.1%) with the first 100 |
| Held-back test entries | tier A 18 of 18, tier B 18 of 18, tier C 12 of 12 match the printed page; piece meanings 78 of 78 |
| Compound verbs that inflect like their final root | 1,080 of 1,123 (96%) |
| Independent re-derivation of the top 86 shapes | 154 of 180 senses matched; 91.6% of example words under the same sense |

**What it established.**

- The stored `constituent_elements` glosses are unreliable. Parks's printed etymology must be re-parsed, and his literal translation is not in the order of the pieces.
- The Blue Book (Lesson 3, pp. 41–42) states seam rules the sound-change engine lacked: r becomes h before a consonant (195 of 196 cases), w becomes p after a hard consonant (64 of 64), k drops before p (32 of 32).
- "This shape has only one known meaning, so assume it" was wrong every time it could be checked, and is never counted as evidence.
- Shapes that differ only in vowel length are not merged; 85 such pairs are listed for review.
- Parks's dotted compound stems are entries in their own right and must be resolved before their parts are read.
- 74 basic and 15 bound verb roots reach tier A or B, in line with Parks's "approximately one hundred".

**Limits.** The test set is small (18 of 18 leaves a 95% interval down to 82%)
and tests faithfulness to Parks's page, not whether Parks is right. The page
transcribers and independent reviewers were AI models. Affixes that Parks
rarely labels, and the several functions of the three preverb shapes, are the
weakest parts. The held-back half has been scored more than once and is no
longer unseen.

**Not done.** Nothing from it is on the public site. No speaker or linguist
has reviewed `curriculum/roots_v2/review_queue.md`. (The 43 data errors it
found were applied on 2026-11-13; see below.)

**Weekly flashcards rebuilt from it (2026-11-13).** The cards took their
"built from …" notes and their related-word cards from version 1. Checked
against version 2, 12 of 162 notes read differently and 7 printed a piece's own
shape as its meaning. `scripts/build_weekly_flashcards.py` now reads
`curriculum/roots_v2/evidence.jsonl`. A piece gets a meaning only where Parks
glosses that piece by itself, or where the checked meaning and the stored gloss
(or Parks's translation of the word) agree; otherwise it is shown bare. Checking
the two against each other showed that neither is always right: version 1 had
the meanings of *Ickariʔ* on the wrong pieces, and version 2 reads the first
piece of 'eleven' as "added" where Parks's "one" is plainly meant. Both are now
shown bare.

### ✅ Repository clean-up *(2026-11-13)*

- Removed from the working tree, all recoverable from commit `2e77095`: 139 MB of intermediate dictionary JSON, run logs, superseded report drafts, nine debugging scripts, three overlapping GitHub Pages guides, the unused Anki deck, four page images, two dead scripts.
- Ten checkpoint files that were never in git were moved to `OneDrive/pari_pakuru_backups/repo_cleanup_2026-11-13/`.
- Design documents, parsing instructions and schemas gathered in `prompts/`; `blue_book_extracted.json` moved into `extracted_data/`.
- A `README.md` in every folder; `DEPLOYMENT.md` replaces the three Pages guides; the quick reference rewritten from the live database.
- Three faults found while checking the documentation against the code:
  - `scripts/possession_engine.py` looked for the kinship table in a folder that does not exist, so kinship nouns were treated as ordinary nouns and `/api/possession/<kinship noun>` returned a server error. **Fixed**: the engine's own checks went from 31 to 47 of 49, and the API now answers for all 1,708 nouns.
  - `DB/test_schema.py` could not read `schema.sql` on Windows. **Fixed**: 53 of 53.
  - The possession engine builds instrumental forms with *-biriʔ*, a misreading of Parks's *-hiriʔ*. Fixed the same day; see Phase 3.1.5.

### ✅ Data fixes *(2026-11-13)*
**Script:** `scripts/fix_data_2026_11.py` (dry run by default) · **Report:** `reports/fix_data_2026-11-13_report.txt` · **Backups:** `OneDrive/pari_pakuru_backups/*_20261113_*`

The 43 errors proposed by the word-construction analysis were each checked
against the page image or the PDF text layer before anything was applied.
Checking them turned up more of the same kinds, and one new kind.

| Fix | Proposed | Applied | Checked against |
|---|---|---|---|
| Page number 2 where the entry is on book page 419 | 23 | 28 | text layer of both pages |
| Letter-spaced text ("c l o s e  u p") | 12 glosses | 13 glosses, 12 example translations, 14 etymologies | page image (glosses); plain English (the rest) |
| Duplicate rows of *kaa…* entries (`-p2-` and `-p71-`) | 6 | 6 removed; two cleaner fields kept from the copies; 7 English-index links moved or repaired | page image; the pairs are identical in headword, IPA, class, forms and examples |
| *caʔuuhtuʔ*: etymology and cognates | 1 | 1 | page image |
| *ciihtahaahiriʔ*: "(contemp.)" stored as a verb class | 1 | 1; the label put back in front of the gloss | page image |
| Accent marks dropped by the character decoding | not proposed | 269 entries; plus ÷ → ú in 25 etymologies, 27 cognates, 10 English-index forms | page images for each stand-in character; the text layer for each position |

The last row is described under Phase 1.1a. It changes what learners see: 260
of the 269 entries had shown no accented syllable at all, 48 of them flashcard
words (*kuruks* 'bear' is now `KOO-dooks`), and two respellings had lost a
vowel.

The JSON dictionaries and the frozen flashcard file were updated by the same
script (week membership unchanged), the word-construction analysis was run
again, and the static site was rebuilt.

### ✅ Flashcard Week 20 held for community review *(2026-11-13)*

Audit item B6. `curriculum/held_for_review.json` lists the week;
`web/flashcards.py` leaves listed weeks out, so the web app, the static site
and the paper cards no longer show it. Week numbers do not change. Releasing it
is one deleted line and a rebuild, and is the Pawnee Nation's decision.

### ✅ Source-fidelity audit *(2026-11-13)*

**Question:** does every stored value that claims to copy a printed page match
the page? **Instruction:** `prompts/source_fidelity_audit.md`. **Code:**
`scripts/source_audit/`. **Results:** `reports/source_audit_2026-11/`, starting
with `findings.md`. The audit changed no data (649 input hashes identical
before and after). It ends in `proposed_fixes.jsonl`.

Why another audit: the three earlier ones sampled, and where they compared two
readings both used the same unverified character table. This one compared
everything, verified the table first, and let the page image decide.

| Stage | What was done | Result |
|---|---|---|
| 0 | Database written to `DB/dump/` as text; `scripts/db_dump.py --restore` rebuilds it | round trip exact, 46,783 rows |
| 1 | Every (font, character code) pair of the text layer read from glyphs cut out of the pages | 52 pairs, all settled; 16 had been decoded wrongly or never |
| 2 | Skiri-to-English: 4,244 entries, 50,736 fields against the text layer, both directions | 97.45% identical; 894 differences; planted-error test 510 of 510 |
| 3 | 369 crops of differences read blind | all 303 read differences show the text-layer reading; agreement sample 60 of 60 |
| 4 | Appendices 1 to 3, chapters 3 and 4 read blind from tiles; abbreviations against their text layer | Appendix 1: 152 of 770 forms differ; chapter 4: 85 of 797 words; see below |
| 5 | Blue Book: the 93 Blue Book-only entries and a sample of 60 other forms read from the scan | of the sample, 9 match the scan, 41 lack the printed accent, 9 have a wrong letter |
| 6 | English-to-Skiri: 6,431 printed entries against the JSON and against the database tables | JSON 95.9% identical; database tables 77.7% |
| 7 | 2,250 proposed fixes, 827 with a value that can be applied as it stands; review page; `apply_fixes.py` | nothing applied by the audit itself; see the next entry |

What it found, most important first:

1. **The tables an AI model read from page images are the weak part.**
   Appendix 1 as stored has 152 wrong forms in 770 (accents the page does not
   have, vowels dropped or doubled, one block shifted by a row). The
   conjugation engine's 90.3% is measured against that copy. Appendix 2 has
   *burii-waa* and *burii* for printed *hurii-waa* and *hurii*. Appendix 3 has
   *asaas*, *atipaat*, *apaat*, *ataati* for *asas*, *atipat*, *apat*, *ataat*.
   The grammar chapter extraction has 34 more words with `b` for `h`.
2. **The dictionary entries are a good copy with a known list of faults.**
   305 of 4,244 entries have a difference in a Pawnee form or in meaning:
   22 verb forms (*tikituum* for *tikituus*), 39 IPA forms (14 of them not
   Parks's IPA at all but the spelling cut into syllables), 16 combining
   forms, 102 cognates and 146 etymologies (mostly stand-in characters in
   words cited from other languages: stored *sáhnió* is printed *sáhniš*),
   71 stretches of printed text the database lacks (12 IPA forms, about 15
   examples, the derived stems listed under ten bound stems, qualifiers such
   as "(personal name)"). One printed entry is missing (*kusisaar*, the
   imperfective-only verb, book page 451) and one stored entry is not a
   headword in the book (`SK-aakaqa-p351-3592`).
3. **The character table.** The phonetic font has a regular grid of twelve
   accented vowels (tense and lax, acute and grave). ə́ and ɪ́ are confirmed.
   The stored hyphen is the printed syllable dot and the stored bullet is the
   printed dash at the edge of a bound form. In words cited from other
   languages the code `ó` is š, `Ý` is é, `í` is ó.
4. **The database's English index is an old copy.** `english_index` and
   `cross_references` were imported from the file before cleaning: 3,986 IPA
   forms not in Parks's notation, 177 with raw stand-in characters. The
   current JSON is clean and should be re-imported.
5. **The Blue Book data came from the OCR text of the scan.** The book prints
   an accent on the stressed vowel; no stored form has it. About one form in
   seven has a wrong letter, and three dictionary entries are built on misread
   forms (*had'* for printed *haú'* "yes", *tsktis•kakusu'* for
   *tskús•kakusu'* "chair", *ti•kuwtitiku'* for *ti•kuwútiku'*).
6. **`column_position` is wrong for 393 entries**, and nothing uses it.

What the audit cannot show: that a printed form is right, or that anything the
engines generate is right. It does not replace a speaker.

Cost: 12 sub-agents for blind readings, 2.78 million tokens (about 230,000
each); 156 images read in all. The comparisons with the text layer cost nothing and can
be re-run after any change (`scripts/source_audit/README.md`).

### ✅ Audit fixes applied; Parks's IPA symbols; Blue Book forms from the scan *(2026-11-13)*

The decisions taken on the audit's four questions: commit; review and apply;
keep Parks's notation, retain the IPA and make sure the simplified forms
follow from it accurately; read the rest of the Blue Book.

**1. Fixes applied.** `scripts/apply_audit_fixes_2026_11.py`; record in
`reports/source_audit_2026-11/applied_fixes_report.txt`. 807 changes, each
backed by the text layer or by a blind reading confirmed on a third look.

| What | Changes |
|---|---|
| Appendix 1 (`verb_paradigms` and `extracted_data/appendix1_conjugations.json`) | 152 forms |
| Appendix 2: *hurii-waa*, *hurii* | 2 |
| Appendix 3: *asas*, *atipat*, *apat*, *ataat*; five rows of book p. 543 added to the JSON | 10 |
| Abbreviation list | 3 |
| Grammar chapter extraction: `b` read for `h` | 22 strings, 34 words; then, in a later run, the forms the first pass could not reach (*-:hus*, *-hus*, *tihurás*, *ratkuhurasi*, *tuksuhuuhwiitit*) |
| Sound-change rules: example forms | 5; then, in a later run, the two phonetic forms printed with Rule 24, which had been stored in an ASCII stand-in (`[chepaat]` for printed [čəpaat], `[eskuts]` for [əskuts]) |
| Dictionary verb forms | 19 |
| Stand-in characters in words cited from other languages | 162 |
| Combining forms: a space or a line-break hyphen inside the form | 10 |
| Headwords: the 22 bracket notes Parks prints after a headword, and 5 other fixes | 27 |
| `column_position` | 393 |
| Entries: *kusisaar* added (book p. 451); `SK-aakaqa-p351-3592` removed (not a headword in the book) | 2 |

The record has the first run (807 changes) and four later runs (12 more):
one headword the first run did not reach, two learner spellings, and the two
rows marked "later run" above, which were found when the letter check
(`scripts/source_audit/alphabet_check.py`) was run again after the fixes.
`scripts/sound_changes.py`, which can refill the `sound_change_rules` table,
was corrected in the same places, so that refilling it does not bring the
misreadings back; table and script now agree field for field.

Not applied, because each needs a person with the page: open item 45.

**2. Parks's IPA symbols.** `scripts/restore_parks_ipa.py`; record in
`ipa_restored_report.txt`. Every Parks entry's phonetic form was set to the
form printed in its own entry, decoded with the verified table: 4,147 changed
in symbols only, 75 were corrected in content (some had been the spelling cut
into syllables, not his IPA), 9 were added, 13 were already as printed. No
Parks entry is without a phonetic form now. `scripts/ipa_notation.py` is the
one place that knows the old working notation; the respelling code converts
through it. 54 respellings changed, and three learner spellings that had been
made from a wrong phonetic form. Both JSON dictionaries and the frozen
flashcard file were brought in step.

`scripts/check_simplified_forms.py` makes the respelling and the learner
spelling again for every Parks entry and compares them with what is stored:
no difference in 4,244 entries. One known coarseness, which is not a copying
error: Parks writes a short i or u as tense [i], [u] in some places and as lax
[ɪ], [ʊ] in others, and the respelling writes `ih` and `oo` for both. 589
entries have such a vowel (open item 43).

**3. Blue Book.** `scripts/source_audit/bluebook_rest.py` (crops and grading)
and `scripts/apply_bluebook_scan_fixes.py`; record in
`bluebook_applied_report.txt`. Six blind readers read the 843 crops the audit
had not reached. With the audit's 153 crops that makes 949 distinct stored
forms: every one that has a page.

| Result | Forms |
|---|---|
| Same as stored | 157 |
| Accent restored | 565 |
| Apostrophe, dot or space corrected | 45 |
| OCR slip corrected (ú read as *ti* or *ii*, á as *d*, í as *f*, é as *j*) | 105 |
| Left for a person (letters differ 49, capitals 12, reader unsure 8, crop missed the form 8) | 77 |

738 attestation rows, 79 Blue Book examples, 76 dialogue lines in 18 lessons
and 960 strings in `extracted_data/` were corrected. Three entries built on
misread forms have new headwords: *hauʔ* "yes" (was *had*), *ckuskakusuʔ*
"chair", *tikuwutikuʔ*. The 93 Blue Book-only entries no longer have a
phonetic form: the book prints none, and the stored ones had been made from
the spelling.

**4. Rebuilt and measured again.** Static site, weekly flashcards (cards
changed in 16 of the 24 weeks; the Week 1 card "yes" now reads *hauʔ*),
printable sheets, word-construction outputs (still 549 roots and 30 affixes,
1,791 words taken apart completely).

| Check | Before | After |
|---|---|---|
| Dictionary fields identical to print | 49,443 of 50,736 (97.45%) | 50,597 of 50,757 (99.68%) |
| Planted-error test | 510 of 510 | 510 of 510 |
| Conjugation engine, Appendix 1 | 695 of 770 (90.3%), against the misread copy | 611 of 770 (79.4%); 137 within two letters; 22 further off |
| Form 2 prediction | 1,904 of 2,197 (86.7%) | 1,915 of 2,197 (87.2%) |
| Person derivation | 27 of 27 | 25 of 27 |
| Noun possession | 59 of 59 | 59 of 59, after three expected kin forms were corrected |
| Sound changes, sentence templates, schema, respelling tests | pass | pass |

The lower conjugation figure is the true one: the earlier figure counted
forms that agreed with a misreading of the page.

The comparison after the fixes is kept in
`reports/source_audit_2026-11/after_fixes/`; the audit's own record of what
it found is unchanged beside it.

Cost: six more blind readers, 1.31 million tokens. The audit and its
follow-up together: 18 sub-agents, 4.09 million tokens.

### ✅ Page citations; the entries completed from the print; the whole entry on the public site *(2026-11-14)*

Ranks 2, 3 and 5 of the "What's next" list of 2026-11-13, and rank 4 as far
as it could be taken without a person holding the books.

**Page citations (rank 2).** `scripts/fix_page_citations.py` set
`lexical_entries.page_number` to the page of the printed book for the 3,511
Parks entries that held the number of a PDF file. The page is the one on
which the entry's headword stands, from the audit's pairing of every stored
entry with its printed entry. The step from file number to book page (plus
348) was not assumed: the script reads the page number printed at the head of
each of the 181 pages and stops if one disagrees. The JSON dictionary (3,540
entries, 29 of them rows the database does not hold) and the frozen
flashcards (253 cards) follow. Entry ids keep the old number. The comparison
with the page now counts a file number as a difference. Record:
`reports/page_citations_report.txt`.

**What the dictionary prints and the database lacked (rank 5).**
`scripts/complete_from_print.py` takes every new value from the PDF's text
layer and refuses a change it cannot find in the printed entry.

| What | Values |
|---|---|
| Derived stems Parks lists under ten bound stems, into the empty `derived_stems` table | 21 |
| Examples that are printed and were never stored | 18 |
| Forms cited from other languages still in stand-in characters (*iiótir* is *iištir*) | 19 |
| A typographic apostrophe stored where the page prints ʔ | 11 |
| A hyphen the typesetter put at the end of a line and the parse kept (*witii-karaahuraariʔ* is *witiikaraahuraariʔ*; `raah-kuuc+uʔ` is `raahkuuc+uʔ`): 550 etymologies, 67 examples, 39 other forms, 28 cited forms | 684 |
| Letter-spaced and split words ("o n  t h e  p i g .") | 133 |
| The gloss of an etymology as printed, where the parse had paraphrased it ("plural to be strung" for `PL + to be strung`) | 31 |
| Single corrections, each checked against the page (a dropped half of an etymology, a gloss's wording, a qualifier put back where the page has it) | 27 |
| Stored and not printed: three numbered verb forms for the noun *itkaakahaaruʔ*; four labels the parse made up for bracket notes | 7 |
| A space before a full stop, comma, semicolon or bracket | 496 |
| **In all** | **1,447 in 1,178 entries** |

The piece lists the parse had made from the etymologies
(`constituent_elements`) were brought in step: 441 of them held a piece with
a line-end hyphen or an apostrophe. The line-end hyphens explain why the
audit of 2026-09-01 saw "78 example sentences with a possible line-break
hyphen": the comparison accepted either reading of a hyphen at a line end,
so a kept hyphen never counted as a difference. The rule now applied: the
hyphen goes when the next line begins with `+`, or when the word goes on in
the Skiri font; it stays before an English gloss or a punctuation mark
(a bound form such as *wiruu-*), and where the headword has a hyphen of its
own.

The comparison itself was widened: it now looks at the qualifier stored with
an example and at the derived stems (80 more fields), and the planted-error
test measures the printed text left unaccounted for instead of counting
stretches.

| Check | Before | After |
|---|---|---|
| Dictionary fields identical to print | 50,597 of 50,757 (99.68%) | 50,807 of 50,837 (99.94%) |
| Differences left | 218 | 37 |
| Planted-error test | 510 of 510 | 510 of 510 |
| Learner spelling and respelling follow from Parks's forms | no difference | no difference |
| Word-construction analysis, regenerated | tiers A 1,093 / B 1,315 / C 1,568 / D 1 / none 360 | A 1,093 / B 1,316 / C 1,568 / D 1 / none 359 |
| Engines (conjugation 611 of 770, form 2 1,915 of 2,197, person derivation 25 of 27, possession 59 of 59) | | unchanged |

The 37 left, each with its reason in `print_completion_report.txt`: 13
grammatical classes (nine are the project's own N-KIN, two store "(pl.
subj.)" with the class, two are printed twice); seven stretches the
comparison cannot place although the text is stored; six places where the
page breaks a line after a slash or inside a cited word; two headwords and
two bound forms where the page breaks a line at a hyphen; and seven values
where the page itself is in doubt (a stray *a*, an unclosed bracket, an
apostrophe for ʔ, *rihkuupaȞkstarit*) or the stored value rearranges a
qualifier.

**Forms that need a look at the page (rank 4, in part).**

- *Blue Book.* The 77 forms the first reading left open were cut again with
  the whole line and its neighbours (`scripts/source_audit/bluebook_second_look.py`)
  and read by one sub-agent that saw only the ten sheets (128,000 tokens).
  The two readings agree on 55. For 35 of those, what both readers read is
  the stored row's own form, and it was applied (*KIRIK1 RU'?* is *KIRIKÉ
  RU'?*, *atlas* is *atías*, *Nawa niru!* is *Nawa rúru!*). For the other 20
  both readers read a longer or another word at that place (*rakis* under
  *tirakis*) or English text: the red line had been placed by a match inside
  a longer word, so the stored form may be right and stand elsewhere on the
  page. Those, the 13 on which the readings differ and the 9 where a reader
  was unsure make the 42 left.
- *The same forms elsewhere.* 628 values in `bb_gap_triage` (401),
  `blue_book_attestations.full_sentence_pawnee` (136), `bb_function_words`
  (61) and other attestation rows held the old OCR forms and were corrected
  from the same readings. The sentence templates were not touched.
- *Grammar chapter.* No second reading was made (it would take three readers,
  about 700,000 tokens). Instead the dictionary served as a third witness
  (`scripts/source_audit/chapter4_third_witness.py`): where the blind
  reader's form is a form the dictionary prints and the stored one is printed
  nowhere. That holds for eight words; three differ in letters and were
  corrected (*askatahciriʔ*, *iriirapahaatu*, *tuctiraahawista*); five differ
  only in an accent or a final glottal stop and were left, because the
  chapter may print an accent or an underlying form that a headword lacks.
  Two stored words are confirmed by the dictionary. About 40 stay open.
- *From open item 45.* The three "verb forms" of *itkaakahaaruʔ* are not
  printed and were removed; the combining form is *takasistik [+ raar-]*
  (the hyphen was the typesetter's). The empty singular cell of *tir* in
  Appendix 2 and *rihkuupaȞkstarit* are still for a person.

**The public site (rank 3).**

- `docs/data/dictionary.json` now carries everything the dictionary prints
  for an entry: preverb, the numbered verb forms (9,210 for 2,163 verbs),
  the other forms, the etymology (3,689), the forms cited from related
  languages (597), the derived stems, and the qualifier of each example. One
  entry to a line, so a change to an entry is one line of difference.
- A search result shows what it showed before and, behind "More from this
  entry", the rest. Searching a verb form finds its verb. Every value is
  escaped (etymologies are printed in angle brackets).
- **Held:** the 143 entries tagged `ceremony` show senses and examples as
  before and none of the added detail; the result says so (open item 50).
- Every result has "Send a correction", which opens a GitHub issue with the
  entry filled in; the About page links to the same place.
- The About page was written again for the site as it is: the two books, what
  a visitor can do, how a word is written, how far to trust it (compared with
  the print; not reviewed by any speaker or by the Pawnee Nation; ceremony
  words waiting for review), what is not on the site and why.
- "Pitch" is now "accent" everywhere a reader sees it, and the two sentences
  that said pitch changes meaning in Pawnee are gone: Parks writes that his
  phonetic forms mark the accented syllable. The word is Parks's; whether it
  is the right one for learners is still a question for rank 1.
- Two of the four example words under the search box, *raawi* 'sun' and
  *aatius* 'father', were not in the dictionary at all. They are now
  *sakuuruʔ* 'sun' and *rikucki* 'bird'.
- `search.js` was loaded twice by every page, so each search ran twice.
- `scripts/check_static_site.js` runs the page's own code against the built
  data: 13 checks, all 4,337 entries rendered.

Rebuilt from the corrected data: the word-construction analysis, the weekly
paper cards and their printable sheets (446 lines with a page citation), the
static site, the text copy of the database.

Cost: one sub-agent, 128,000 tokens.


### 🔲 Ongoing — Data Quality & Maintenance

- [x] **~~Blue Book gap triage~~** — **DONE (2026-03-19)** via Gemini batch analysis. 516 of 984 BB vocabulary items classified into 8 categories: phrases (196/38%), inflected verbs (141/27%), unlisted nouns (94/18%), descriptors (40/8%), possessed forms (15/3%), function words (11/2%), loanwords (10/2%), OCR artifacts (9/2%). Key finding: 65% are morphological gaps (roots exist in Parks, inflected forms don't match). 115 high-value items flagged for potential DB addition. DB table: `bb_gap_triage`. Report: `reports/bb_gap_triage.txt`. Script: `scripts/bb_gap_triage.py`.

**Follow-up actions completed (2026-03-19):**
- [x] **Import 93 high-value BB items** — `scripts/import_bb_items.py`: 76 nouns, 9 function words, 8 loanwords added to `lexical_entries` (4,273 → 4,366). New `source` column = 'blue_book'. Entry IDs: `BB-{slug}-{seq}`.
- [x] **p2/p71 deduplication (2026-03-20)** — `scripts/dedup_entries.py`: 22 p2/p71 duplicate pairs removed (p2 kept for higher-quality IPA), kusisaar parser artifact merged (4,366 → 4,343). hiksukac (VD/VP) and racawaktaarik (VI/VT) preserved as polysemy. Examples migrated before deletion. Backup: `~/.pari_pakuru_backups/`.
- [x] **Function word inventory seeded** — `scripts/function_word_inventory.py`: 414 items in `function_words` table (355 Parks + 2 BB direct + 57 Gemini-extracted from phrases).
- [x] **Inflected verb reverse-lookup** (Opus analysis): 82% of 141 BB inflected verb gaps trace to existing Parks dictionary roots. Gap is morphological, not lexical. Top roots: `at` 'go', `aar` 'do', `kuutik` 'kill', `irik` 'see', `huras` 'find', `kawaahc` 'eat'. Validates that conjugation engine work is the right investment.
- [ ] Prune ~5-6 OCR artifacts from Gemini function word extraction
- [ ] Review 40 descriptor items for potential DB addition
- [ ] Review 15 possessed forms for integration with possession engine
- [x] **E2S→S2E linking backfill (2026-03-21)** — `english_index.entry_id` populated from `english_to_skiri_linked.json`: 5,129/8,067 linked (63.6%). Match types: 4,723 exact_unique, 398 gloss_disambiguated, 8 first_homonym_fallback. 2,938 unlinked are genuine gaps (multi-word phrases, cross-references, parsing artifacts). 3 orphaned links from dedup (p71 kaaʔa, kusisaar -2018) skipped. Enables SQL joins from English words to full S2E entries for search, export, and AI verification.
- [ ] Resolve remaining 2,938 unlinked E2S entries (most are parsing artifacts, some may be real terms)
- [ ] Review 8 low-confidence homonym matches from linking
- [ ] Version control: track changes to entries over time
- [ ] Document Blue Book orthography differences (practical vs. linguistic spelling conventions)
- [ ] Cognate linking: build out Arikara, Kitsai, Wichita, South Band comparative data
- [ ] Audio pronunciation layer (if recordings become available)

---

## Design Principles for Endangered Language Preservation

These principles guide all user-facing features:

1. **Every attested form is precious** — surface all attestations (dictionary + Blue Book + Parks examples) for any query, not just one "correct" answer
2. **Show morphological breakdowns** — learners can't ask native speakers, so the tool must explain *why* a form looks the way it does (prefix + stem + suffix with labels)
3. **Export everything** — PDF wordlists, Anki decks, printable paradigm tables. Digital tools disappear; offline materials persist. **This is underbuilt relative to its importance** — see Phase 5.2 elevated priority.
4. **Record uncertainty with granularity** — mark generated (unattested) forms distinctly from documented ones. Learners must know what's verified vs. computed. **Go beyond binary**: use confidence tiers (high/medium/low) so learners know *how* uncertain a computed form is (see Phase 4.3).
5. **Privilege primary sources** — Parks Dictionary and Blue Book are the authorities; computed forms are supplements, never replacements
6. **Community governance over correctness** *(NEW)* — the tool should never be the sole authority on what counts as correct Skiri. Provide mechanisms for knowledgeable community members to flag errors, confirm forms, and contribute corrections. Human review gates all feedback before it enters the system (see Phase 4.4).
7. **Accent is not optional** *(NEW)* — pitch/accent placement in Skiri is phonemic (changes meaning). Any generated form without correct accent marks is unreliable for speech. Treat accent assignment as a learner-safety issue, not a cosmetic improvement (see Phase 3.1 accent task). *Correction, 2026-11-13: the claim that accent is phonemic is not supported by the source. Parks writes "Stress is not phonemic in Skiri and hence is not marked on words. (Phonetic forms in entries do, however, have accented syllables marked.)" (Sounds and Alphabet, p. 15). The marks are part of his IPA and must be preserved and shown for that reason; calling them "pitch" that changes meaning is not his description. See open item 9.*
8. **Build for the classroom first** *(NEW)* — the primary users are teachers and students in community language classes. Prioritize features that serve that context: printable materials, lesson-aligned content, Word of the Day, simple UI that works on low-bandwidth connections. Self-directed online learners are an important secondary audience.
9. **Never invent a Pawnee form; never generate IPA** *(2026-09-01, 2026-11-12)* — every form in learner material is looked up from a source record. Parks's IPA marks vowel reduction and pitch that cannot be predicted from spelling, so it is shown only where he prints it for that exact word. A derived form is always labelled as derived.
10. **Ceremonial vocabulary waits for the community** *(2026-10-01)* — words to do with bundles, dances and doctoring are flagged and kept out of new learner material until the Pawnee Nation has reviewed them. That is a decision about protocol, not about data.
11. **Same spelling is not the same word** *(2026-03-20, 2026-11-12)* — two entries, or two word-pieces, with one shape are merged only when meaning, class and forms agree, and the decision is recorded as data so that it can be undone.

---

## Scripts Reference

The list of scripts, in pipeline order and with the status of each, is
[scripts/README.md](scripts/README.md). It replaced the table that used to be
here, so that there is one list to keep current.

## Environment

- Windows 11; the shell is Git Bash or PowerShell. Python virtual environment at `.venv/` (`.venv/Scripts/python`).
- The console uses code page 1252. A script should write Pawnee text through `sys.stdout.buffer`, or be run with `PYTHONIOENCODING=utf-8`, and should open files with `encoding="utf-8"`.
- AI extraction steps use the Gemini API (`GEMINI_API_KEY`, model `gemini-2.5-flash`) through the `google.genai` package. The two original page parsers still use the older `google.generativeai`.
- The database is not in git. Backups: `OneDrive/pari_pakuru_backups/` and `~/.pari_pakuru_backups/`.
- Published: the static site only, on GitHub Pages from `docs/`. The Flask app runs locally. The PythonAnywhere hosting was retired on 2026-11-13 and `wsgi.py` removed. See `DEPLOYMENT.md`.

---

## Open items

*As of 2026-11-14. Within each group, most important first. Items that are done keep their number, so that older notes still point to the right place.*

### Needs a person, not code

1. **Speaker or linguist review of the word-construction analysis.** `curriculum/roots_v2/review_queue.md`; the ten main questions are at the top of `curriculum/roots_v2/validation_report.md` (vowel-length pairs, affixes labelled by default, the three preverb shapes, 274 shapes with several meanings, 192 pieces with no known meaning).
2. **Community review of ceremonial vocabulary.** Flashcard Week 20 is held back until it has been done (`curriculum/held_for_review.json`). In the word-construction analysis 176 words are flagged, by keyword only.
3. **A person has not reviewed the 387-word flashcard list** (audit item B5). Its membership was decided by English keywords.
4. **Lesson vocabulary:** 4 judgement calls and 8 homonym ambiguities were left unlinked (`reports/bb_vocab_linking.txt`).
5. **Feedback queue:** two flags are pending in `/admin/feedback`.

### The IPA

6. *(Done 2026-11-13.)* **The stored IPA uses Parks's own symbols**: ə́ and ɪ́ for the accented short a and i, `·` between syllables, `–` at the edge of a bound form. Set for every entry from the text layer with the verified table (`scripts/restore_parks_ipa.py`).
7. *(Done 2026-11-13.)* Every Parks IPA form has been matched to its printed form and set from it; 75 were corrected in content.
8. **The grave accent.** Parks's phonetic font has a regular system: à ì ù on the second half of a long vowel, ə̀ ɪ̀ ʊ̀ on a short one. Ten entries have one, stored as printed since 2026-11-13. His front matter does not say what it marks.
9. *(Changed 2026-11-14 to "accent", Parks's own word, everywhere a reader sees it; the sentences saying that pitch changes meaning were removed.)* **What to call the marks.** Parks says stress is not phonemic and that phonetic forms mark accented syllables (p. 15). Whether "accent" is the right word for learners is for someone who knows the language; changing it is one pass over `web/templates/` and the two `format_pitch` filters. The style names `pitch-high` and `pitch-unmarked` still say "pitch".
10. *(Done 2026-11-13: 162 stored cognates and etymologies corrected. `ó` is š, `Ý` is é, `í` is ó, `Ó` is ą, `Ô` is ą́, `è` is į, `ü` is ž, `š` is a raised i; the `?` in Kiowa, Ponca and Arapaho words is printed as a question mark.)* About 20 cognate forms still differ from the page in a letter or a hyphen (item 41).
11. *(Done 2026-11-13.)* Every Parks entry has its printed IPA; the nine that had none were added from the page.
12. 32 respellings of *-ʔa* stems where Parks's IPA lacks the glottal stop (`reports/fix_pronunciations_report.txt`). *(The bullet shown in the IPA of bound forms was the working notation for Parks's dash; the dash is stored and shown since 2026-11-13.)*

### Generated forms

13. **The possession engine offers forms it should not.** Through the API it builds an instrumental ("with, using …") for every noun, animals included, because its animacy filter needs topic tags that the API does not pass. Its stem stripper removes `-kis` wherever it finds it, so *rakis* 'wood' becomes the stem *ra*. For stems ending in r the dictionary shows two outcomes with *-hiriʔ* and the engine picks one (marked "medium"). These forms are shown as computed, but several are plainly wrong.
14. **Bare pieces on the weekly flashcards** are places where two readings of Parks's etymology disagree, for example the first piece of *askuhuukita* 'eleven' and both pieces of *Ickariʔ*. Each is a small question for a person.

### Data

15. *(Done 2026-11-14: `scripts/fix_page_citations.py`; every Parks entry cites the page of the book.)* `english_index.page_number` and `cross_references.source_page` belong to the English-to-Skiri section and still hold file numbers (book page = file number + 60); they go with item 32.
16. *(Done 2026-11-14: the 21 derived stems under ten bound stems are in `derived_stems`, each checked against the printed entry; the local entry page and the public site show them.)*
17. *(2026-11 audit: `(1), (1)` is faithful: the page prints* VT(1), VR(1)*. `(pl. subj.)` is printed after the class and was stored in the class column. Nine kin terms are stored as N-KIN where the page prints N: the project's own reclassification, recorded in `fix_audit_issues.py`.)* **Verb-class values that are not verb classes**: `(pl. subj.)` once and doubled values such as `(1), (1)` on four entries; `(3-i)` once, which may be genuine. The grammatical-class column has 41 distinct strings, some of them one class written two ways (`VI, VT` and `VT, VI`).
18. *(Done 2026-11-14 for the Parks entries: 496 values.)* A space before punctuation in glosses and examples ("animals .", "cloth ;"), left by the parse.
19. Letter-spaced text remains in the raw copies of the parsed entries (`raw_entry_json`, `raw_subentry_json`), which are deliberately not edited.
20. *(Done 2026-11-14: the line-break hyphens, in 67 examples and 617 other values; see the phase entry.)* From the 2026-09-01 audit: rare truncated gloss qualifiers (two were found and completed); a few verb forms where the AI reading and the PDF text layer differ (none is left).
21. From the 2026-10-01 audit: the 93 Blue Book-only entries have no learner spelling and are not labelled as Blue Book spelling (B3); "word of the day" fixed at build time (C3); a join on bare headword in the greetings category (C5). *(Done 2026-11-14: a bare `Ø` headword is shown with its preverb in search (C1); `search.js` is loaded once (C4).)*
22. 2,937 of 8,067 English-index rows are not linked to an entry (cross-references, phrases, parsing leftovers).
23. *(Done 2026-11-13: the audit compared all of it, and the Blue Book forms were then read from the scan as well.)* Everything extracted by AI from page images has been compared with the pages: Appendix 1, Appendices 2 and 3, the abbreviation list, the grammar chapter and the Blue Book vocabulary.

### Engines and features

24. Form 2 prediction: 241 of 2,197 verbs missed and 41 more off by a glottal stop (`si-` and `ruuti-` prefixes, internal vowel shortening, multi-word headwords).
25. Conjugation of Appendix 1: 22 mismatches and 137 near misses in 770 forms, against the appendix as corrected from the page (item 39).
26. Person derivation (3.2b): plural persons, negative mode, imperfective coverage, question-particle placement. Two of the 27 checked forms differ from Appendix 1 as corrected: *ruhii* for printed *ruuhii* ('to be good', 3rd singular absolutive) and *riihkiraawaʔ* for *rihkiraawaʔ* ('to be sick').
27. Printable word lists and paradigm tables. (The flashcard sheets exist; these do not.)
28. The Blue Book glossary pages (123–130) are not itemised.
29. *(Done 2026-11-13: `DB/dump/` and `scripts/db_dump.py`.)* **The database is not under version control and cannot be rebuilt by one command.** A text dump in git, or a build script that replays every step, would make each future fix a reviewable difference.

### From the source-fidelity audit (2026-11-13)

30. *(Done 2026-11-13 for the fixes with solid evidence: 807 applied.)* What remains of `proposed_fixes.jsonl`: the 1,090 English-index differences (item 32) and the judgement calls of items 41 and 45.
31. *(Done 2026-11-13; table in the phase entry.)* Conjugation 79.4% (was 90.3%), form 2 prediction 87.2%, person derivation 25 of 27, sound-change tests 11 of 11.
32. **Re-import the English index** from `english_to_skiri_linked.json`, after its own faults are repaired (about 400 placeholder values, 244 cross-reference terms with spaces, 25 missing headwords, 295 subentries still in the working IPA notation). Until then `english_index` and `cross_references` hold the uncleaned early copy.
33. *(Decided and done 2026-11-13: Parks's notation is stored.)* What is left of this is item 43.
34. *(Done 2026-11-14: `scripts/complete_from_print.py`.)* The printed stretches the database lacked: 18 examples, the 21 derived stems, qualifiers, the second half of four etymologies. Seven stretches are still listed by the comparison although their text is stored (item 41).
35. **Blue Book headwords.** The 93 Blue Book-only entries carry headwords respelled into Parks's letters (*paisic* for printed *paisits*); only 5 are identical to a printed form, and 45 have no printed form on record. The audit's ground rule is to quote the Blue Book as printed.
36. *(Done 2026-11-13: 715 forms corrected from the scan, the three entries first.)* 77 forms are left (item 42).
37. **Chapters 2 and 5 of the front matter** have never been extracted or read. Nothing stored comes from them.
38. *(Done 2026-11-13: corrected for the 393 entries from the page geometry.)* Nothing uses `column_position`.

### After the fixes (2026-11-13)

39. **The conjugation engine gets 611 of 770 forms of Appendix 1 (79.4%), not 90.3%.** Its rules were tuned against a copy with 152 misread forms. `scripts/morpheme_inventory.py --validate` lists the 159 that differ. Whether to take this work up again is a decision for the project; until someone makes it, the rule not to retry from-scratch conjugation stands.
40. **`scripts/accent_rules.py` was worked out from the accents of the misread Appendix 1**, many of which the page does not have. Only the conjugation engine uses it. It should be checked against the corrected appendix or withdrawn.
41. **37 differences between the dictionary entries and the page are left** (`reports/source_audit_2026-11/after_fixes/s2e_differences.jsonl`; 218 before 2026-11-14). Each has its reason in `print_completion_report.txt`: 13 grammatical classes, nine of them the project's own N-KIN (item 17); seven stretches the comparison cannot place although the text is stored; ten places where the page breaks a line after a slash, inside a cited word or at a hyphen that belongs to the word; and seven values where the page itself is in doubt or the stored value rearranges a qualifier. None is a phonetic form or a verb form.
42. **42 Blue Book forms that two readings could not settle** (`reports/source_audit_2026-11/bluebook_second_look.json` and the last section of `bluebook_applied_report.txt`; 77 before the second reading of 2026-11-14). For 20 of them both readers read a longer or another word at the place the OCR pointed to, so the stored form may be right and stand elsewhere on the page; on 13 the readings differ; in 9 a reader was unsure. The forms written into the sentence templates (`scripts/sentence_templates.py`) still lack the printed accents; the other tables were corrected on 2026-11-14.
43. **Tense and lax short vowels in the respelling.** Parks writes [i], [u] in some places and [ɪ], [ʊ] in others; the respelling writes `ih` and `oo` for both (589 entries, counted by `scripts/check_simplified_forms.py`). Whether learners should see the difference is a teaching decision for someone who knows the language.
44. *(Closed 2026-11-13: the PythonAnywhere hosting is no longer in use and was taken out of the repository.)* If the account still exists, its web app should be disabled there: unless someone updated it by hand, it holds the data from before the corrections and would still serve flashcard Week 20.
45. **Left for a person with the page:** the singular cell of *tir* 'to be together' in Appendix 2, empty in print and stored as `tir`, which the conjugation engine reads; about 40 words of the grammar chapter (`chapter4_third_witness.json` says for each what the stored text, the blind reader and the dictionary have; five of them differ from a dictionary form only in an accent or a final glottal stop); *rihkuupa´kstarit* in an example of *apak*, a printing oddity; the values listed as left in `print_completion_report.txt`. *(Settled 2026-11-14: the three "verb forms" of* itkaakahaaruʔ *are not printed and were removed; the combining form is* `takasistik [+ raar-]`*; three chapter words corrected.)*
46. **An older respelling function is still in the code.** `generate_simplified_pronunciation` in `scripts/respell_and_normalize.py` returns `? ?` for a phonetic form of several words. Stored respellings are made by `scripts/fix_pronunciations.py`, which handles them; the older function should be retired.

### The public site, now the only publication (2026-11-13)

47. *(Done 2026-11-14: the About page was written again for the site as it is.)* Its wording is the project's and has not been read by anyone from the community (rank 1).
48. *(Done 2026-11-14: the verb forms, other forms, etymology, cited forms and derived stems are in `docs/data/dictionary.json` and behind "More from this entry".)* The topic tags are in the data and not shown; the cross-references wait for item 32.
49. *(Done 2026-11-14: "Send a correction" on every search result and on the About page opens a GitHub issue with the entry filled in.)* It needs a GitHub account; there is no other route.
50. **The 143 entries tagged `ceremony` show less than the others on the public site.** They are searchable and show senses and examples, as before; the verb forms, etymology and cited forms added on 2026-11-14 are held back for them, and the result says so. The tag was given by keyword, so the list is rough both ways. Whether these entries are shown at all, and how fully, belongs to the community review (rank 1). The switch is in `export_dictionary_data`, `scripts/build_static_site.py`.

---

## How to Use This Document

Start a working session by reading "Status at a glance", "What's next" and
"Open items". When an item of "What's next" is done, take it out of the
ranking and re-rank what is left; the ranking is a recommendation made on the
date it carries, not a plan anyone has agreed to.
Refer to a phase by its name ("Phase 6.2") or to an open item by its number.

When a phase is finished or a number changes, update this file in the same
change. It is only useful while it is true. Figures here were read from the
database and from the scripts' own output on the date given beside them; when
you quote one elsewhere, run the command again.

The ground rules for all work here are the Design Principles above, and the
rules section of `prompts/skiri_word_construction_v2.md`.
