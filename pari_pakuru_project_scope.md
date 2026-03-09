# Pari Pakuru — Skiri Pawnee Language Tool: Project Scope & Todo

## Project Goal

Build a comprehensive Skiri Pawnee language preservation tool: a searchable, linked dictionary with pronunciation guides, semantic tags, morphological grammar engine, and sentence construction — all validated against source materials.

---

## Source Materials

| File | Description | Location |
|------|-------------|----------|
| Parks Dictionary (PDF) | Full Skiri Pawnee dictionary by Douglas Parks. Split into: Abbreviations/Sound Key, Sounds/Alphabet, Major Sound Changes, Grammatical Overview, Organization, English-to-Skiri section, Skiri-to-English section, 3 Appendices | `Dictionary Data/Dictionary PDF Split/` |
| Dictionary page PDFs | Individual pages split for AI processing | `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/` and `split_pdf_pages_ENGLISH_TO_SKIRI/` |
| Blue Book — Pari Pakuru' | 1979 Pawnee Cultural Retention Committee textbook. 21 lessons teaching spoken Pawnee with dialogues, vocabulary, grammar explanations | `pari pakuru/Blue Book - Pari Pakuru.pdf` and `.txt` extraction |
| JSON Schemas | Defined structures for S2E and E2S parsed entries | `Dictionary Data/` |

## Current Data State

| File | Entries | Status |
|------|---------|--------|
| `skiri_to_english_respelled.json` | 4,273 | **CURRENT** — normalized, IPA synced, OCR fixed, `simplified_pronunciation` + `normalized_form` populated |
| `skiri_to_english_fixed.json` | 4,273 | Intermediate — OCR fixes applied, pre-respelling |
| `skiri_to_english_linked.json` | 4,273 | Linked + IPA synced (pre-fix, pre-respelling) |
| `english_to_skiri_linked.json` | 6,414 | **CURRENT** — normalized, s2e_entry_id linked to S2E entries |
| `skiri_to_english_normalized.json` | 4,273 | Normalized OCR artifacts, pre-linking |
| `english_to_skiri_normalized.json` | 6,414 | Normalized OCR artifacts, pre-linking |
| `skiri_to_english_complete.json` | 4,273 | Original parse (has OCR corruptions) |
| `english_to_skiri_complete.json` | 6,414 | Original parse (has OCR corruptions) |

### Relationship Between S2E and E2S

- **S2E is the primary linguistic record** — full entries with headword, phonetic form, etymology, 5 paradigmatic verb forms, examples, derived stems, cognates
- **E2S is an index into S2E** — English words pointing to Skiri equivalents, with cross-references
- **E2S has more accurate phonetic forms** (IPA vowels: ə, ɪ, ʊ, accent marks) because its PDF parsing captured the IPA characters more faithfully
- **Linked by `entry_id`** (on S2E) and `s2e_entry_id` (on E2S subentries). Format: `SK-{slug}-p{page}-{index}`

### S2E Entry Structure
```json
{
  "entry_id": "SK-paaqatuq-p100-1234",
  "headword": "paaʔatuʔ",
  "normalized_form": "pâ'atu'",
  "entry_metadata": { "page_number": 100, "column": "left", ... },
  "part_I": {
    "stem_preverb": "(ut...)",
    "phonetic_form": "[•paa-ʔə-tʊʔ•]",
    "simplified_pronunciation": "pah-'uh-too'",
    "grammatical_info": { "grammatical_class": "N", "verb_class": null, "additional_forms": [] },
    "glosses": [{ "number": 1, "definition": "blood.", "usage_notes": null }],
    "etymology": { "raw_etymology": "<...>", "constituent_elements": [...], "literal_translation": "..." },
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
    "s2e_entry_id": "SK-paaqatuq-p100-1234",
    "s2e_match_type": "exact_unique",
    "part_I": {
      "skiri_term": "paaʔatuʔ",
      "phonetic_form": "[•paa-ʔə-tʊʔ•]",
      "grammatical_classification": { "class_abbr": "N", "verb_class": null },
      "english_glosses": [{ "number": 1, "definition": "blood." }],
      "etymology": { ... }
    },
    "part_II": { "paradigmatic_forms": [{ "form_number": 1, "skiri_form": "..." }], "examples": [...] },
    "part_III": { "cross_references": [{ "english_term": "...", "skiri_equivalents": ["..."] }] }
  }]
}
```

### Phonetic Notation System (Parks Dictionary)

The phonetic forms use IPA in square brackets with syllable dots:
- `•` (U+2022) — syllable separator (PRESERVED, never modified)
- `–` (U+2013) — stem boundary marker at edges
- Consonants: p, t, k, c/č, s, w, r, h, ʔ (glottal stop)
- Vowels: a, aa (long), i, ii (long), u, uu (long)
- IPA vowels: ɪ (near-close front), ʊ (near-close back), ə (schwa)
- Accent: á, í, ú (acute = high pitch), à (grave)
- Example: `[•rə-hʊh-kaa-paa-kɪs•]`

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

## Completed Work

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
**Scripts:** `scripts/audit_entries.py`, `scripts/generate_review_list.py`, `scripts/verify_glottal_from_phonetic.py`
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

## Todo: Remaining Work

### 🔲 Phase 1.2 — Database Schema
**Priority:** Medium
**Depends on:** Phase 1.1b (linked data)
**Effort:** Large

Design a relational database schema (SQLite) that unifies S2E and E2S.

Tasks:
- [ ] Core `lexical_entries` table (entry_id, headword, normalized_form, phonetic_form, simplified_pronunciation, preverb, grammatical_class, verb_class)
- [ ] `glosses` table (entry_id, sense_number, definition, usage_notes)
- [ ] `paradigmatic_forms` table (entry_id, form_number 1-5, skiri_form)
- [ ] `examples` table (entry_id, skiri_text, english_translation, usage_context)
- [ ] `etymology` table (entry_id, raw_etymology, literal_translation, constituent_elements as JSON)
- [ ] `cognates` table (entry_id, language, form)
- [ ] `english_index` table (english_word, entry_id, subentry_number) — the E2S lookup layer
- [ ] `cross_references` junction table (from_english, to_english, skiri_equivalents)
- [ ] Import script: linked JSON → SQLite
- [ ] Query API: bidirectional lookup by English or Skiri

### 🔲 Phase 2.1 — Semantic Category Tagging
**Priority:** Medium
**Depends on:** Phase 1.1a (clean glosses)
**Effort:** Medium

Auto-tag entries by domain: animals, plants, kinship, housing, celestial/weather, body parts, tools/weapons, ceremony/ritual, food, colors, numbers, etc.

Tasks:
- [ ] Define tag taxonomy (finite list of categories)
- [ ] Keyword scan: gloss text → category assignment (e.g., "eagle"/"beaver" → `animal`)
- [ ] Etymology scan: constituent elements revealing domain membership
- [ ] Grammatical class hints: N-KIN → `kinship` automatically
- [ ] Manual review queue for ambiguous entries
- [ ] Store tags on entries (new `semantic_tags` array field)
- [ ] Blue Book lessons as category source (Lesson 8 = animals/housing, Lesson 5 = body parts, etc.)

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

**Checkpoint files:** `bb_extraction_checkpoint.json`, `blue_book_extracted.json`

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

**Optional follow-up: Pronunciation comparison (`scripts/bb_pronunciation_compare.py`):**
- Extracts BB parenthetical pronunciation guides from raw text (12 found in lesson pages 29+)
- OCR normalization: consonant+'d' → consonant+'a' (stress-dotted vowel artifact)
- 3-pass parser: inline `word (pron) gloss`, column-block (table format), preceding-line
- Long-vowel-folded matching + gloss-based fallback via `english_index`
- 7 of 12 guides matched to Parks dictionary entries; all show "close/systematic" correspondence
- Key finding: Parks `DUH` = BB `ra` (tapped r + short a); BB shortens long vowels (BB `hitu'` = Parks `hiituʔ`)
- Report: `reports/phase_2_2_pronunciation.txt`

### 🔲 Phase 2.3 — Sound Change Rule Engine
**Priority:** Medium-High
**Depends on:** Phase 1.1a (clean data), PDF 03 (Major Sound Changes)
**Effort:** Large

Formalize phonological rules as ordered transformations for the grammar engine.

Source: `Dictionary Data/Dictionary PDF Split/03-Major_Sound_Changes.pdf`

Tasks:
- [ ] Extract and catalog all sound change rules from PDF 03
- [ ] Encode as ordered rules (vowel coalescence, consonant cluster simplification, accent shift)
- [ ] Implement as functions: (stem, affix) → surface form
- [ ] Validate against paradigmatic forms in dictionary (form 1-5 for every verb)
- [ ] Handle verb class-specific changes (Class 1: -a suffix, Class 2: -i suffix, etc.)

### 🔲 Phase 3.1 — Morpheme Inventory & Slot System
**Priority:** Low (depends on 2.3)
**Depends on:** Phase 2.3 (sound changes), PDF 04 (Grammatical Overview)
**Effort:** Very Large

Build the verb template: which morphemes occupy which slots in what order.

Source: `Dictionary Data/Dictionary PDF Split/04-Grammatical_Overview.pdf`, Abbreviations (60+ morpheme labels in PDFs 01)

Tasks:
- [ ] Map all 60+ morpheme abbreviations to their forms and slot positions
- [ ] Define slot ordering: proclitics → mode → person → preverb → stem → aspect → subordinating
- [ ] Encode verb class rules: how each class modifies dependent forms
- [ ] Build conjugation engine: (stem, class, person, number, mode, aspect) → inflected form
- [ ] Validate against every paradigmatic form in the dictionary

### 🔲 Phase 3.2 — Sentence Construction Framework
**Priority:** Low (depends on 3.1)
**Depends on:** Phase 3.1 (morpheme slot system)
**Effort:** Very Large

Given English input, construct Skiri output.

Tasks:
- [ ] Map English sentence patterns to Skiri clause structure
- [ ] Handle transitivity: subject/object marking, preverb system (ut-, ir-, uur-)
- [ ] Implement proclitic system (indefinite ku-, reflexive witi-, dual si-, etc.)
- [ ] Implement evidential system (quotative wi-, dubitative kuur-, etc.)
- [ ] Blue Book lesson dialogues as test cases

### 🔲 Phase 4.1 — Search Interface
**Priority:** Medium (can start after Phase 1.2)
**Effort:** Medium

Bidirectional search with fuzzy matching.

Tasks:
- [ ] Web UI or CLI: type English → get Skiri results with pronunciation, paradigms, tags
- [ ] Type Skiri → get English results
- [ ] Fuzzy matching for learner misspellings
- [ ] Filter by semantic category, grammatical class, verb class

### 🔲 Phase 4.2 — Sentence Builder UI
**Priority:** Low (depends on Phase 3.2)
**Effort:** Large

Guided interface: select person/action/object/tense → assembled Skiri sentence with morpheme breakdown.

### 🔲 Ongoing — Data Quality & Maintenance

- [ ] Resolve 362 unmatched E2S entries (most are parsing artifacts, some may be real terms)
- [ ] Review 8 low-confidence homonym matches from linking
- [ ] Version control: track changes to entries over time
- [ ] Export pipeline: generate printable dictionary (PDF), flashcard decks (Anki), research data files
- [ ] Cognate linking: build out Arikara, Kitsai, Wichita, South Band comparative data
- [ ] Audio pronunciation layer (if recordings become available)

---

## Scripts Reference

| Script | Location | Purpose | API Required? |
|--------|----------|---------|---------------|
| `normalize_phonetic.py` | `scripts/` | Fix OCR artifacts across all fields | No |
| `link_dictionaries.py` | `scripts/` | Link S2E↔E2S with shared IDs, sync IPA phonetics | No |
| `fix_priority_issues.py` | `scripts/` | Phase 1.1a supplement: fix remaining OCR chars, null non-IPA stubs | No |
| `respell_and_normalize.py` | `scripts/` | Generate `simplified_pronunciation` + `normalized_form` | No |
| `audit_entries.py` | `scripts/` | Full data quality audit (local + optional Gemini) | Optional (GEMINI_API_KEY) |
| `generate_review_list.py` | `scripts/` | Triage audit flags into actionable review list | No |
| `verify_glottal_from_phonetic.py` | `scripts/` | Cross-reference phonetic_form to verify noun glottal stops | Optional (GEMINI_API_KEY) |
| `test_phase_1_1.py` | `scripts/` | Test suite for 1.1c/1.1d engines (106 tests) | No |
| `run_parser_e2s.py` | `scripts/` | Parse E2S dictionary pages | No |
| `s2e_parser.py` | `scripts/` | Parse S2E dictionary pages | No |
| `verify_with_gemini.py` | `scripts/` | Verify parsed entries with Gemini | Yes (GEMINI_API_KEY) |
| `verify_with_claude.py` | `scripts/` | Verify parsed entries with Claude | Yes |
| `tag_entries.py` | `scripts/` | Phase 2.1: semantic tag entries (rule-based + Gemini) | Optional (GEMINI_API_KEY) |
| `blue_book_verify.py` | `scripts/` | Phase 2.2: Blue Book cross-verification — extract vocab, match to dictionary, populate examples | Yes (GEMINI_API_KEY) |
| `bb_pronunciation_compare.py` | `scripts/` | Phase 2.2 follow-up: compare BB pronunciation guides with Parks simplified_pronunciation | No |

## Environment

- Python virtual environment at `pari-pakuru/.venv/`
- Gemini API key stored as environment variable `GEMINI_API_KEY`
- Windows environment (paths use `\` in logs)
- Repository: `pari-pakuru/` with structure documented in `DIRECTORY_LAYOUT.md`

---

## How to Use This Document

Reference any section by name when starting a new chat. For example:
- "I want to work on **Phase 1.1c — Pronunciation Respelling Engine**"
- "Let's tackle **Phase 2.1 — Semantic Category Tagging**"
- "Help me with the **362 unmatched E2S entries** from the linking step"

The AI should read this document, understand the current data state, and pick up from the referenced step without needing the full conversation history.
