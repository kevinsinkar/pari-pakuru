# Pari Pakuru — Skiri Pawnee Language Tool: Project Scope & Todo

## Project Goal

Build a comprehensive Skiri Pawnee language preservation tool: a searchable, linked dictionary with pronunciation guides, semantic tags, morphological grammar engine, and sentence construction — all validated against source materials.

---

## Source Materials

| File | Description | Location |
|------|-------------|----------|
| Parks Dictionary (PDF) | Full Skiri Pawnee dictionary by Douglas Parks. Split into: Abbreviations/Sound Key, Sounds/Alphabet, Major Sound Changes, Grammatical Overview, Organization, English-to-Skiri section, Skiri-to-English section, 3 Appendices (Appendix 1: 7 verb conjugation paradigms ~770 forms; Appendix 2: irregular du/pl verb roots ~9 entries; Appendix 3: kinship terminology ~40 forms) | `Dictionary Data/Dictionary PDF Split/` |
| Dictionary page PDFs | Individual pages split for AI processing | `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/` and `split_pdf_pages_ENGLISH_TO_SKIRI/` |
| Blue Book — Pari Pakuru' | 1979 Pawnee Cultural Retention Committee textbook. 21 lessons teaching spoken Pawnee with dialogues, vocabulary, grammar explanations | `pari pakuru/Blue Book - Pari Pakuru.pdf` and `.txt` extraction |
| JSON Schemas | Defined structures for S2E and E2S parsed entries | `Dictionary Data/` |
| Parks Ch. 3 OCR | OCR extraction of Major Sound Changes (24 rules with examples) | `parks_sound_changes_ocr.txt` |
| Parks Ch. 4 OCR | OCR extraction of Grammatical Overview (23 pages: noun incorporation, verb classes, possession) | `parks_grammatical_overview_ocr.txt` |

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

### Priority Roadmap *(added 2026-03-15)*

High-impact items ordered by learner value, not technical dependency:

| Priority | Phase | What | Why |
|----------|-------|------|-----|
| ✅ ~~1~~ | 3.1.5 | ~~Noun possession morphology~~ | **DONE (2026-03-18)** — 4 possession systems + locative suffixes + web widget + example filter. 40/40 tests. |
| 🟡 2 | 3.1 (stem extraction) | Dictionary-wide stem extraction | **IN PROGRESS** — third pass: 83.5% → **86.6%** (1,914/2,211), 88.4% w/ close. Up from 14.8% → 62.0% → 83.5% → 86.6%. |
| ✅ ~~3~~ | 4.3 | ~~Confidence scoring on computed forms~~ | **DONE (2026-03-19)** — 4-factor weighted scoring (0.0-1.0), DB column, web badges, dashboard widget. 88.7% avg, 2,202 high / 30 med / 22 low. |
| 🟡 4 | 3.1 (accent) | Accent mark generation | **IN PROGRESS** — 78/85 (91.8%) accented forms correct. 4 rules: Agent-boundary í, Mode-prefix í/rí, Infinitive kú, Dual sí. Appendix 1: 76.2% → **86.4%**. 7 remaining failures are verb-specific stem accents. |
| ✅ ~~5~~ | 4.4 | ~~Community feedback mechanism~~ | **DONE (2026-03-19)** — Flag/confirm buttons, admin review queue, writable DB, dashboard widget. Design Principle #6 enforced. |
| 🟡 6 | 5.2 (exports) | Printable PDFs + Anki export | **Anki DONE (2026-03-20)** — 4,336 cards, 19 tag decks, dedup + display_headword + confidence gating. PDF export remaining. |
| ✅ ~~7~~ | Ongoing | ~~Blue Book 518-gap triage~~ | **DONE (2026-03-19)** — 516 gaps classified: 38% phrases, 27% inflected verbs, 18% unlisted nouns, 8% descriptors, 3% possessed, 2% function words, 2% loanwords, 2% OCR artifacts. 65% are morphological (roots exist in Parks). 115 high-value items flagged for DB addition. |
| ✅ ~~8~~ | 3.1.6 | ~~Function word inventory~~ | **CLASSIFIED (2026-03-20)** — 418 function words with `position_rule` + `refined_subclass`. 149 PROCLITIC, 135 PRECEDES-VERB, 51 PRECEDES-NOUN, 44 CLAUSE-INITIAL, 28 STANDALONE, 11 BETWEEN-CLAUSES. Demonstratives + interrogatives mapped. |
| 🟡 9 | 3.2a | Template-based sentence assembly | First usable step toward sentence construction |
| 🟡 10 | 5.1 | Structured lesson content | Blue Book curriculum extraction for progressive learning |

### 🟡 Next Up: Phase 3.1 — Dictionary-Wide Stem Extraction *(Priority #2 — IN PROGRESS)*

**Status:** Third pass complete — **83.5% → 86.6% exact** (1,914/2,211 verbs), 88.4% with close matches. Up from 14.8% → 62.0% → 83.5% → 86.6%.

**Script:** `scripts/stem_extractor.py`
**Reference files:** `parks_sound_changes_ocr.txt` (OCR of Parks Ch. 3), `parks_grammatical_overview_ocr.txt` (OCR of Parks Ch. 4)

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
**Script:** `scripts/import_to_db.py` (implied by DB existence)
**What it does:** SQLite database (`skiri_pawnee.db`) unifying S2E and E2S data.

**Tables:** `lexical_entries` (4,366 entries: 4,273 Parks + 93 Blue Book), `glosses`, `paradigmatic_forms`, `examples`, `etymology`, `cognates`, `derived_stems`, `english_index`, `cross_references`, `semantic_tags`, `blue_book_attestations`, `import_metadata`, `bb_gap_triage`, `community_feedback`, `function_words` (418), `bb_function_words` (63) + FTS tables for glosses, examples, english_index.

### ✅ Phase 2.1 — Semantic Category Tagging
**Script:** `scripts/tag_entries.py`
**What it does:** Auto-tags entries by domain using rule-based keyword matching + Gemini AI for ambiguous cases. 7,097 tags stored in `semantic_tags` table.

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

**Follow-up: Pronunciation comparison (`scripts/bb_pronunciation_compare.py`):**
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

**Current validation (latest pass — 2026-03-19):**
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

**Validation:** 40/40 tests passing (33 possessive + 7 locative/instrumental). Covers all 4 possession systems plus case suffixes, validated against Blue Book Lessons 5, 7, 8 and Grammatical Overview Table 4.

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

### 🔲 Phase 3.2 — Sentence Construction Framework
**Priority:** Medium (depends on 3.1 accuracy improvements + 3.1.5 noun morphology)
**Depends on:** Phase 3.1 (morpheme slot system at 60%+ accuracy — **now at 76.2%**), Phase 3.1.5 (noun possession), Phase 3.1.6 (function words)
**Effort:** Very Large — **now broken into 3 sub-phases to make progress incremental**

Given English input, construct Skiri output.

Sources:
- `extracted_data/appendix3_kinship.json` — 23 kinship terms with possessive paradigms (already extracted)
- `extracted_data/grammatical_overview.json` — 23 pages of grammar (clause structure, word order)
- Blue Book lesson dialogues as test cases (88 examples currently in DB)

#### Phase 3.2a — Template-Based Sentence Assembly *(start here)*
**Priority:** Medium-High
**Effort:** Medium

Not free-form translation — guided construction from a fixed set of sentence patterns drawn from Blue Book dialogues. The 88 dialogue examples are the test suite.

Tasks:
- [ ] Extract sentence templates from Blue Book dialogues (e.g., "[person] [descriptive verb]", "I see the [noun]", "[person] is going to [place]")
- [ ] Identify 10–15 high-frequency patterns that cover lessons 1–10
- [ ] Build template engine: user selects pattern → fills slots with dictionary entries → engine inflects and assembles
- [ ] Show full morpheme breakdown of assembled sentence (so learners see *why* it looks that way)
- [ ] Validate each template output against attested Blue Book examples where available
- [ ] Mark template outputs with confidence level (see Phase 4.3)

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

### 🔲 Phase 4.2 — Sentence Builder UI
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
**Implemented in:** `web/app.py`, `web/db.py`, `web/templates/entry.html`, `web/templates/dashboard.html`, `scripts/add_feedback_table.py`
**Built via:** Claude Code (VS Code)

Knowledgeable community members (teachers, elders' family members, students) can now flag errors and confirm forms. All feedback goes through human review — never auto-accepted (Design Principle #6).

**DB:**
- `community_feedback` table: entry_id, feedback_type (flag/confirm), issue_type, suggested_correction, comment, reporter_name (optional), status workflow (pending→accepted/rejected), reviewer_note, timestamps
- Migration script: `scripts/add_feedback_table.py`
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

### 🔲 Phase 5.1 — Structured Lesson Content
**Priority:** Medium (can start after Phase 4.1)
**Depends on:** Phase 4.1 (web interface to host lessons)
**Effort:** Medium

Extract lesson structure from Blue Book (not just vocabulary) to provide ready-made curriculum.

Tasks:
- [ ] Extract lesson dialogue texts with English translations (20 lessons)
- [ ] Map lesson vocabulary to dictionary entries (link each lesson word to its full entry)
- [ ] Extract grammar explanations per lesson (progressive skill building)
- [ ] Cultural context notes from Blue Book lesson introductions
- [ ] Lesson sequencing: greetings → basic sentences → question forms → descriptive → narrative
- [ ] Interactive exercises: fill-in-the-blank, matching, translation drills

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
- [x] **Anki deck export** — **DONE (2026-03-20)**. `scripts/anki_export.py`: 4,336 cards across 19 semantic tag decks + "All Words" parent. genanki .apkg output. Stable model/deck/note IDs for safe re-import. CLI flags: `--dry-run`, `--deck TAG`, `--advanced` (per-sense Option B), `--verbs-only`, `--bb-only`, `--min-confidence`.
- [x] **Pre-export data cleanup (2026-03-20):** `scripts/dedup_entries.py` removed 22 p2/p71 duplicate pairs + merged kusisaar parser artifact (4,366 → 4,343 entries). Preserved hiksukac (VD/VP) and racawaktaarik (VI/VT) as legitimate polysemy. `scripts/display_utils.py`: `display_headword()` with 5 rules (bracket, slash, paren onset, suffix paren, bound-morpheme dash), `gram_class_label()`, `morph_class_note()`. Tested against all 281 notation entries — zero problems.
- [x] **Card template spec locked:** Option A multi-sense (primary sense + "+N more" note), form2_confidence >= 0.75 threshold for verb forms, format_pitch_anki() for HTML pitch accent, per-class back notes (N-KIN, N-DEP, LOC, ADV-P), example dedup on english_translation.
- [ ] **🔴 Printable PDF wordlists and paradigm tables for offline use** — highest-impact remaining export for classroom use; target users may have inconsistent internet access. Same query as Anki, rendered via reportlab/weasyprint.
- [ ] Blue Book lesson-aligned decks (vocabulary per lesson)
- [ ] Audio placeholder fields (for future recordings)

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
- [ ] Resolve 362 unmatched E2S entries (most are parsing artifacts, some may be real terms)
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
7. **Accent is not optional** *(NEW)* — pitch/accent placement in Skiri is phonemic (changes meaning). Any generated form without correct accent marks is unreliable for speech. Treat accent assignment as a learner-safety issue, not a cosmetic improvement (see Phase 3.1 accent task).
8. **Build for the classroom first** *(NEW)* — the primary users are teachers and students in community language classes. Prioritize features that serve that context: printable materials, lesson-aligned content, Word of the Day, simple UI that works on low-bandwidth connections. Self-directed online learners are an important secondary audience.

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
| `sound_changes.py` | `scripts/` | Phase 2.3: sound change rule engine — 24 rules cataloged, pipeline, validation against paradigmatic forms | No |
| `extract_appendices.py` | `scripts/` | Phase 3.1: extract appendix/grammar data from scanned PDFs via Gemini OCR (--appendix1, --appendix2, --appendix3) | Yes (GEMINI_API_KEY) |
| `morpheme_inventory.py` | `scripts/` | Phase 3.1: morpheme slot system, conjugation engine, validation (--validate, --validate-dict, --report) | No |
| `analyze_dual_plural.py` | `scripts/` | Phase 3.1: Gemini-powered morpheme breakdown analysis for dual/plural forms | Yes (GEMINI_API_KEY) |
| `retry_failed_grammar.py` | `scripts/` | Phase 3.1: retry failed grammar pages with plain-text Gemini or Claude API | Yes (GEMINI_API_KEY or ANTHROPIC_API_KEY) |
| `merge_grammar_retries.py` | `scripts/` | Phase 3.1: merge recovered grammar page data into grammatical_overview.json | No |
| `noun_possession.py` | `scripts/` | Phase 3.1.5: noun possession morphology — extract nouns, classify possession systems, build kinship paradigms, generate possessive forms, validate against BB (--extract, --report, --validate, --db, --generate HEADWORD) | No |
| `possession_engine.py` | `scripts/` | Phase 3.1.5: possession form generation engine — dispatches to kinship/body_part/agent/locative/patient systems, integrates sound changes, generates morpheme chips for web UI (--test, --paradigm HEADWORD) | No |
| `example_filter.py` | `scripts/` | Phase 3.1.5: Skiri-aware headword matching for examples — rejects false substring matches (kirike≠kiri), handles OCR variants (J→E, 1→E), compound detection via epenthetic-h, prefix disambiguation against headword set; wired into entry_detail route | No |
| `stem_extractor.py` | `scripts/` | Phase 3.1: dictionary-wide form_2 prediction — parses stem_preverb, infers verb class, applies preverb junction rules + coalescence + perfective finals (--validate, --predict HEADWORD, --report, --confidence) | No |
| `add_feedback_table.py` | `scripts/` | Phase 4.4: migration script to create `community_feedback` table in SQLite DB | No |
| `accent_rules.py` | `scripts/` | Phase 3.1: accent mark assignment rules — 4 rules (Agent-boundary í, Mode-prefix accent, Infinitive kú, Dual sí); validates against 85 Appendix 1 accented forms (--validate, --analyze) | No |
| `bb_gap_triage.py` | `scripts/` | Phase 2.2/Ongoing: classify 516 unmatched Blue Book items via Gemini batch analysis into 8 categories (phrase, inflected_verb, noun_unlisted, descriptor, possessed_form, function_word, loanword, ocr_artifact); populates `bb_gap_triage` DB table with checkpointing | Yes (GEMINI_API_KEY) |
| `import_bb_items.py` | `scripts/` | Import 93 high-value BB gap items (nouns, function words, loanwords) into `lexical_entries` + `glosses` tables with `source='blue_book'` flag; normalizes BB→Parks orthography; deduplicates against existing headwords (--dry-run, --db) | No |
| `function_word_inventory.py` | `scripts/` | Phase 3.1.6: seed `function_words` table by merging Parks dictionary function-class entries (355) with BB gap triage function words (11); infers subclass from gloss keywords (--dry-run, --db) | No |
| `extract_function_words.py` | `scripts/` | Phase 3.1.6: extract function words from 196 BB phrase gaps via Gemini batch analysis (5 batches); populates `bb_function_words` table; checkpointed; generates `reports/bb_function_words.txt` (--dry-run, --report-only, --clear) | Yes (GEMINI_API_KEY) |
| `classify_function_words.py` | `scripts/` | Phase 3.1.6: add `position_rule` + `refined_subclass` to all 418 function words; classifies demonstratives (spatial system), interrogatives, conjunctions, adverbs, locatives, numerals, particles by clause position (CLAUSE-INITIAL, PRECEDES-VERB, PRECEDES-NOUN, BETWEEN-CLAUSES, PROCLITIC, STANDALONE) (--dry-run, --db) | No |
| `populate_bb_pronunciation.py` | `scripts/` | Phase 4.1: generate `simplified_pronunciation` for 93 BB-imported entries (headword→English respelling) + assign semantic tags from English glosses; enables BB entries to appear in flashcards (--dry-run, --db) | No |

## Environment

- Python virtual environment at `pari-pakuru/.venv/`
- Gemini API key stored as environment variable `GEMINI_API_KEY`
- Windows environment (paths use `\` in logs)
- Repository: `pari-pakuru/` with structure documented in `DIRECTORY_LAYOUT.md`
- **Production deployment:** PythonAnywhere at `/home/paripakuru/main/` — Flask app in `web/app.py`, SQLite DB at `skiri_pawnee.db`, scripts in `scripts/`. DB is not git-tracked; run `python scripts/dedup_entries.py --apply` on PA after pull to sync dedup (backs up to `~/.pari_pakuru_backups/`).

---

## AI Development Tools & Model Selection

### Three-Tool Workflow

This project benefits from **three AI tools used in parallel**, each with different strengths:

| Tool | Model | Best for | Access |
|------|-------|----------|--------|
| **claude.ai Chat** | Opus 4.6 | Linguistic analysis, architecture, document review, complex debugging | Pro/Max plan, browser |
| **Claude Code (VS Code)** | Sonnet 4.6 (default) | File editing, script writing, running commands, multi-file changes | Pro plan, VS Code extension or CLI |
| **Gemini API** | gemini-2.5-flash | Batch OCR, large-scale pattern analysis, offloading repetitive analytical tasks | Free tier or API key (`GEMINI_API_KEY`) |

### Parallel Processing Strategy

Many tasks in this project can be **split across tools simultaneously**:

**Example: Stem extraction second pass (current priority)**
- **claude.ai (Opus)**: Analyze the 728 remaining mismatches — categorize failure patterns, design rule fixes based on Parks Ch. 3, write the sound change logic
- **Claude Code (Sonnet)**: Implement the fixes in `stem_extractor.py`, run validation, iterate on regex patterns for `[+ neg.]` / `witi-` / initial-ʔ handling
- **Gemini API**: Batch-analyze the 385 VD verb mismatches — send headword+form_2 pairs to Gemini with Parks rule descriptions, get structured morpheme breakdowns for each, identify which internal sound change rules apply

**Example: Phase 3.1 Accent Mark Generation (next deep-analysis priority)**
- **claude.ai (Opus)**: Analyze Parks' pitch/stress rules from the scanned PDFs; design accent assignment algorithm using the ~70 "to come" accent-only close matches as test suite
- **Claude Code (Sonnet)**: Implement accent rules in `stem_extractor.py` or `morpheme_inventory.py`, run validation
- **Gemini API**: Batch-extract accent patterns from the 770 Appendix 1 forms (which ones have accents, where do they fall)

**Example: Future Phase 5.2 (Anki Export)**
- **Claude Code**: Write the export script (SQLite → Anki .apkg format)
- **claude.ai**: Design card templates, select which fields to include, handle IPA rendering

### Gemini API Integration Points

The Gemini API (`GEMINI_API_KEY`) is already used for several tasks and is available for new ones:

| Script | What Gemini does |
|--------|-----------------|
| `extract_appendices.py` | OCR scanned PDF pages → structured JSON (Appendix 1-3, Grammar pages) |
| `tag_entries.py` | Classify ambiguous entries by semantic domain |
| `blue_book_verify.py` | Extract structured vocabulary from Blue Book lesson text |
| `analyze_dual_plural.py` | Morpheme breakdown analysis for dual/plural verb forms |
| `audit_entries.py` | Batch validate parsed entries for data quality |
| **`stem_extractor.py` (planned)** | Batch-analyze mismatch patterns for VD verbs; generate morpheme decompositions for compound headwords |
| `bb_gap_triage.py` | Classify 516 unmatched Blue Book items into 8 categories via 11 Gemini batches (completed) |

**Practical tip:** For analytical tasks with 100+ items (like "analyze why 385 VD verb predictions fail"), Gemini's batch processing is faster and cheaper than running them through claude.ai one by one. Structure the prompt as: "Given this headword and attested form_2, identify which Parks sound change rules explain the difference from this predicted form."

### claude.ai Chat vs. Claude Code in VS Code

**They are NOT the same model by default.** Understanding the difference matters for this project:

| | claude.ai | Claude Code (VS Code extension / CLI) |
|---|---|---|
| **Default model** | Opus 4.6 (on Pro/Max) | **Sonnet 4.6** (on Pro plan, $20/mo) |
| **Best for** | Long-form design discussion, architecture planning, document review, linguistic analysis | File editing, script writing, running commands, multi-file code changes |
| **Context window** | 200K tokens (standard) | 200K standard; 1M beta on Max/Enterprise |
| **Can run code?** | Yes (sandbox) | Yes (your actual local files + terminal) |
| **Sees your codebase?** | Only uploaded files | Full repo access (reads/writes your files directly) |

**Key implication for this project:** Claude Code on a Pro plan runs **Sonnet 4.6**, which is excellent for coding but less strong on the kind of deep linguistic reasoning this project requires (morpheme analysis, sound change rule design, Pawnee grammar interpretation). The intelligence gap matters most for Phases 3.x (morphology engine work).

### Recommended Workflow

**Use claude.ai (Opus) for:**
- Linguistic analysis: morpheme breakdown design, sound change rule debugging, grammar interpretation from Parks
- Architecture decisions: DB schema design, engine design, phase planning
- Document review: reading this scope doc, analyzing Blue Book content, design decisions
- Complex debugging: "why does my conjugation engine produce X instead of Y for this verb class?"

**Use Claude Code (Sonnet) for:**
- Writing and editing Python scripts (morpheme_inventory.py, sound_changes.py, stem_extractor.py, etc.)
- Flask/web UI work (templates, CSS, routes)
- Running validation scripts and interpreting output
- Bulk file operations, refactoring, test writing
- Database migrations and import scripts

**Use Gemini API for:**
- Batch OCR of scanned PDFs (appendices, grammar pages)
- Large-scale pattern analysis (100+ entries needing morpheme breakdown)
- Offloading repetitive analytical tasks that don't require deep reasoning
- Cross-validation of computed forms against attested data

**If you want Opus in Claude Code:**
- **Max plan ($100–200/mo):** Opus 4.6 is available as default. Run `/model opus` in Claude Code.
- **Pro plan ($20/mo):** Opus is available only via `/extra-usage` (pay-per-use on top of subscription). Run `/model opus` after enabling extra usage in settings.
- **Hybrid approach (`opusplan`):** Uses Opus for planning/reasoning, Sonnet for code execution. Run `/model opusplan`. Good middle ground for this project — Opus reasons about the morphology, Sonnet writes the code.

**Practical tip for this project:** Start complex morphology work sessions in claude.ai (Opus) to get the logic right, then move to Claude Code (Sonnet) to implement it. For batch analytical work (VD verb mismatch analysis, etymology parsing), offload to Gemini. Share this scope document at the start of each session so the AI has full context. The `opusplan` mode is worth trying for Phase 3.x work where the reasoning and the implementation are tightly coupled.

### Model Configuration (Claude Code)

```bash
# Check current model
claude /status

# Switch model for current session
claude /model          # interactive picker
claude /model opus     # Opus 4.6 (requires Max or extra-usage)
claude /model sonnet   # Sonnet 4.6 (default on Pro)
claude /model opusplan # Opus plans, Sonnet executes

# Set permanent default (add to shell profile)
export ANTHROPIC_MODEL=claude-sonnet-4-6  # or claude-opus-4-6
```

---

## How to Use This Document

Reference any section by name when starting a new chat. For example:
- "Let's tackle **Phase 3.1 — Accent Mark Generation**"
- "Build the **Anki deck export** from Phase 5.2"
- "Start **Phase 3.1.6 — Function Word Inventory** using the BB gap triage seed data"
- "Continue **Phase 3.1 — stem extraction fourth pass** targeting 90%+"
- "I want to work on **Phase 5.1 — Structured Lesson Content**"

The AI should read this document, understand the current data state, and pick up from the referenced step without needing the full conversation history.

**For Claude Code sessions:** Share this file at session start with `@pari_pakuru_project_scope.md` or include it in your project's `CLAUDE.md` file. See the **AI Development Tools** section for model selection and parallel processing guidance.

**For Gemini-offloaded tasks:** Many batch analytical tasks (VD verb mismatch analysis, etymology parsing, morpheme decomposition) can be offloaded to Gemini API via scripts. Check which scripts support `GEMINI_API_KEY` in the Scripts Reference table.

---

## Next Chat Continuation Prompt

Copy-paste this to start the next session (claude.ai or Claude Code):

> **Pick the next priority from the Pari Pakuru roadmap.**
>
> **What's done (sessions: 2026-03-20 → 2026-03-21):**
> - Phase 5.2 Anki export: ✅ 4,336 cards, 19 semantic tag decks, genanki .apkg with CLI flags
> - DB dedup: ✅ 22 p2/p71 pairs + kusisaar merge (4,366 → 4,343). Polysemy preserved
> - Display utils: ✅ `display_headword()` 5 rules, 281 notation entries zero problems
> - Nominal sound change pipeline: ✅ `apply_nominal_sc()` splits verb/noun rules. Fixes ks→kc regression. `iksiriʔ` and `ikstaaririʔ` now match attested forms
> - -sukat allomorph: ✅ stems ending in -ki/-ski get `-sukat`. `piiraskisukat` correct
> - Instrumental animacy filter: ✅ returns None for animate nouns (N-KIN, kinship/social/animal)
> - BB/Parks merge: ✅ 5 orthographic variant pairs merged, `bb_variant_of` column added, blue_book_attested updated (176→181)
> - Kinship tag cleanup: ✅ 36 erroneous tags removed (35 verbs + 1 Gemini), 8 retagged to social, noun-only guard added. Zero kinship tags on non-nouns
> - Social taxonomy: ✅ age/gender/social role terms expanded
> - raar→taar: ✅ documented as Rule 8R (r→t after hard C), not separate rule
> - Phase 3.1.5 Noun possession: ✅ (4 systems, locative suffixes, web widget, example filter)
> - Phase 3.1 Stem extraction: 🟡 86.6% exact (1,914/2,211 verbs)
> - Phase 3.1.6 Function word inventory: ✅ 418 items classified
> - Phase 4.1–4.4: ✅ Web app, flashcards, confidence scoring, community feedback, UI/UX all complete
>
> **Remaining roadmap priorities:**
> - 🔴 #6 (partial): **Printable PDF export** — same query as Anki, rendered via reportlab/weasyprint. Two-column vocab list + paradigm table appendix. **Claude Code**.
> - 🟡 #9: **Template-based sentence assembly** — function word inventory (with position rules) now supports this. **Opus + Claude Code**.
> - 🟡 Optional: **Stem extraction fourth pass** (86.6%→90%+) — diminishing returns
> - 🟡 Optional: **"to do it" investigation** (74/110, 12 MISS) — largest verb-specific gap
>
> The scope doc (`pari_pakuru_project_scope.md`) has full context. The DB is `skiri_pawnee.db` (4,343 entries, `bb_variant_of` column, 181 BB-attested). Scripts in `scripts/`. Web app on PythonAnywhere.
