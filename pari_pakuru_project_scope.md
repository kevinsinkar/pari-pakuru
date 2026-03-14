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

### ✅ Phase 1.2 — Database Schema
**Script:** `scripts/import_to_db.py` (implied by DB existence)
**What it does:** SQLite database (`skiri_pawnee.db`) unifying S2E and E2S data.

**Tables:** `lexical_entries` (4,273 entries), `glosses`, `paradigmatic_forms`, `examples`, `etymology`, `cognates`, `derived_stems`, `english_index`, `cross_references`, `semantic_tags`, `blue_book_attestations`, `import_metadata` + FTS tables for glosses, examples, english_index.

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

**Current validation (latest pass — 2026-03-12):**
- Appendix 1: **76.2% exact (587/770)**, 19.9% close (153), 3.9% miss (30)
- Per verb: to go 94%, to drink it 89%, to be sick 88%, to have it 85%, to be good 79%, to do it 67%, to come 31%
- Dictionary: 14.8% exact (1,420/9,583), 44.2% close

**Major improvements since first pass (12.7% → 76.2%):**
- Gemini-collaborative 3-round diagnosis with 10 morphophonological fixes (+25%)
- Rule 24 glottal stop deletion, siʔV epenthesis, r→h before high vowels
- uur preverb ih removal, acir+V r-loss, ʔ deletion after consonant
- Potential shortening conditioned on agent presence
- "to go" suppletive 3pl stems with PREV_3A label (avoids Rule 2R)
- "to drink it" sub_stem shortening, 3pl raak prefix, pl_agent_fusions
- Descriptive-ku verb system overhaul: DESC_KU_MODE_OVERRIDES, raktah plural, 3pl prefix markers, ku→kuu lengthening, aca→acu u-raising (+8%)
- "to come" structural fixes: negative kaakaa, 3.A stem, subjunctive shortening, gerundial/potential/infinitive preverb handling (+4%)

Tasks remaining (priority order):
- [x] ~~"to be sick" descriptive verb fixes~~ — **done**: 37→97/110 exact (88%)
- [x] ~~"to come" structural fixes~~ — **done**: 21→34/110 exact (31%), 70 close (accent-only), 6 remaining MISS
- [ ] **Accent mark generation** — 70 "to come" close matches + ~15 other verbs differ only by accent marks (á, í, ú); implementing stress assignment would boost ~85 forms to exact (~9% overall gain)
- [ ] **"to come" remaining 6 MISS** — assertive/absolutive 3du (3.A stem used instead of du stem), gerundial 2sg (GER shortening fires on PREV label), 3pl sub suffix contraction (stem deleted); also 3pl sub `verb_class='1'` string adds SUB suffix incorrectly
- [ ] **"to do it" investigation** (74/110, 12 MISS) — largest remaining mismatch gap after "to come"
- [ ] VD(u) descriptive verb stem extraction (1% exact in dict validation)
- [ ] VT(3) Class 3 ut- fusion logic (0% exact in dict validation)
- [ ] Dictionary stem extraction improvements (main gap for dict-wide accuracy)

### 🔲 Phase 3.2 — Sentence Construction Framework
**Priority:** Low (depends on 3.1 accuracy improvements)
**Depends on:** Phase 3.1 (morpheme slot system at 60%+ accuracy — **now at 76.2%**)
**Effort:** Very Large

Given English input, construct Skiri output.

Sources:
- `extracted_data/appendix3_kinship.json` — 23 kinship terms with possessive paradigms (already extracted)
- `extracted_data/grammatical_overview.json` — 23 pages of grammar (clause structure, word order)
- Blue Book lesson dialogues as test cases

Tasks:
- [ ] Map English sentence patterns to Skiri clause structure (SOV word order)
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
- [x] Fuzzy matching: LIKE pattern matching + Levenshtein distance (edit distance 1-2) on normalized forms for learner misspellings
- [x] Filter sidebar: semantic category tags, grammatical class (on search results page)
- [x] Blue Book attestation badge on entries and search result cards
- [x] Mobile-responsive design (Pico CSS framework, responsive grid, touch-friendly flashcards)
- [x] Mark generated vs. attested forms: "Attested (Parks Dictionary)" / "Attested (Appendix 1)" labels on paradigm tables
- [x] Browse by semantic tag and grammatical class with paginated results
- [x] Weekly flashcard study system: 19 categories, ~300 curated beginner words, flip-card UI with keyboard nav and shuffle
- [x] Word-of-the-day on homepage with dictionary stats
- [x] Deployment: `requirements.txt` provided; run with `python -m web.app`

**Routes:**
- `/` — Homepage with stats and random word
- `/search?q=...` — Full search with filters
- `/search/partial?q=...` — HTMX live search endpoint
- `/entry/<entry_id>` — Full entry detail
- `/browse` — Browse by tag/class
- `/browse/tag/<tag>` — Entries by semantic tag
- `/browse/class/<class>` — Entries by grammatical class
- `/flashcards` — Weekly flashcard overview
- `/flashcards/<week>` — Interactive flashcard study session
- `/about` — About page with data source info

### 🔲 Phase 4.2 — Sentence Builder UI
**Priority:** Low (depends on Phase 3.2)
**Effort:** Large

Guided interface: select person/action/object/tense → assembled Skiri sentence with morpheme breakdown. Shows derivation steps so learners understand *why* the form looks the way it does.

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
**Priority:** Medium (low effort, high impact for self-directed learners)
**Depends on:** Phase 1.2 (dictionary data)
**Effort:** Small

Generate exportable study materials from the dictionary.

Tasks:
- [x] In-browser flashcard study system (weekly sets, flip cards, keyboard nav, shuffle) — built in Phase 4.1 (`web/flashcards.py`)
- [x] Semantic category decks (19 categories: kinship, animals, body, food, etc.)
- [x] Include pronunciation (IPA + simplified respelling) on every card
- [x] Blue Book-attested entries prioritized in card selection
- [ ] Anki deck export: Skiri → English and English → Skiri cards
- [ ] Blue Book lesson-aligned decks (vocabulary per lesson)
- [ ] Printable PDF wordlists and paradigm tables for offline use
- [ ] Audio placeholder fields (for future recordings)

### 🔲 Ongoing — Data Quality & Maintenance

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
3. **Export everything** — PDF wordlists, Anki decks, printable paradigm tables. Digital tools disappear; offline materials persist
4. **Record uncertainty** — mark generated (unattested) forms distinctly from documented ones. Learners must know what's verified vs. computed
5. **Privilege primary sources** — Parks Dictionary and Blue Book are the authorities; computed forms are supplements, never replacements

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
