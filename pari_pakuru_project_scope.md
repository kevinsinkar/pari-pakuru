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
| `skiri_to_english_linked.json` | 4,273 | **CURRENT** — normalized, IPA phonetics synced from E2S, entry_id assigned |
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

---

## Todo: Remaining Work

### 🔲 Phase 1.1c — Pronunciation Respelling + Orthographic Normalization
**Priority:** High
**Depends on:** Phase 1.1a, 1.1b (normalized + IPA-synced phonetic forms)
**Effort:** Medium

Two new fields derived from `phonetic_form` and `headword`:

#### 1. `simplified_pronunciation` — Learner-Friendly English Respelling
**Source:** IPA `phonetic_form` field
**Purpose:** Give English-speaking learners an intuitive pronunciation guide

Build a deterministic converter: IPA `phonetic_form` → hyphenated English respelling.

**Vowel mapping:**

| Pawnee | Parks Sound Key (p. xvii) | Blue Book (p. xvii–xxi) | Respelling |
|--------|--------------------------|-------------------------|------------|
| `a` (short) | "putt" (/ʌ/) | "above" (/ə/); "even though `a` often sounds like the `u` in English *mud*" | `uh` |
| `aa` (long) | "father" (/ɑː/) | "father" | `ah` |
| `i` (short) | "pit" (/ɪ/) | "hit" | `ih` |
| `ii` (long) | "weed" (/iː/) | "machine" | `ee` |
| `u` (short) | "boot" (/uː/) | "push" (/ʊ/); "lips are pursed or rounded as in *prune* or *push*" | `oo` |
| `uu` (long) | "rude" (/uː/) | "ruler" | `oo` |
| `ɪ` (IPA) | — | — (Parks IPA for short i quality) | `ih` |
| `ʊ` (IPA) | — | — (Parks IPA for short u quality) | `oo` |
| `ə` (IPA) | — | — (Parks IPA for schwa/reduced a) | `uh` |

**Note:** Short `u` ("push"/ʊ) vs long `uu` ("rude"/uː) differ in quality, but both map to `oo` in the respelling. Length distinction is not captured in simplified pronunciation — both sound "oo"-like to English ears.

**Consonant mapping:**

| Pawnee | Parks Sound Key | Blue Book | Respelling |
|--------|----------------|-----------|------------|
| `r` | "Spanish *pero*" (tapped r) | "*steady*"; "a very soft d"; "a fast d as in *ready*, but softer" | `d` |
| `c` | "patch and cents" | `ts` = "catsup" | `ts` |
| `č` | (same phoneme as `c` in IPA) | "often pronounced almost like English *ch* in *church*, especially when it begins a syllable which is not the last syllable of a word" | `ch` |
| `ʔ` | "uh-uh" (glottal stop) | "co-operate" (voice stop); "a stopping of the voice in the voice box" | `'` |
| `p` | "spot" (unaspirated) | "spin" | `p` |
| `t` | "stop" (unaspirated) | "start" | `t` |
| `k` | "skate" (unaspirated) | "skin" | `k` |
| `s` | "sit" | "super" | `s` |
| `w` | "wall" | "watch"; "the same as the vowel u" | `w` |
| `h` | "hit" | "harm"; silent in SK after `r` (`hr` → `h`) | `h` |

**Structural rules:**
- Syllable dot `•` → `-` (hyphen) in respelling
- Accented syllables (á, í, ú) → UPPERCASE in respelling
- Strip brackets `[` `]` and stem boundary markers `–`

**Examples:**
- `[•rə-hʊh-kaa-paa-kɪs•]` → `duh-HOOh-kah-pah-kihs`
- `[•paa-ʔə-tʊʔ•]` → `pah-'uh-too'`

**Validation note:** Blue Book parenthesized pronunciations (e.g., `(pa-ri-su')` for `paresu'`) use Pawnee orthographic letters, *not* English approximations. So validation against Blue Book should compare **syllable boundaries** and **vowel length marking**, not letter-for-letter mappings.

#### 2. `normalized_form` — Orthographic Normalization of Skiri Words
**Source:** `headword` field, cross-referenced with `phonetic_form` for č disambiguation
**Purpose:** Produce a standardized, learner-readable Skiri spelling that preserves morphological structure while simplifying diacritics

**Normalization rules (Skiri words only — English glosses/definitions unchanged):**
- Convert long vowels to circumflex: `aa` → `â`, `ii` → `î`, `uu` → `û` (and uppercase: `AA` → `Â`, `II` → `Î`, `UU` → `Û`)
- Convert `c` → `č` **only** when the corresponding `phonetic_form` shows /tʃ/ (i.e., the IPA `č`). When the phonetic form shows /ts/ (plain `c`), leave as `c`.
- Convert glottal stop: `ʔ` → `'` (apostrophe)
- All other characters pass through unchanged

**Examples:**
- `kawiirasiira` → `kawîrasîra`
- `karuurasuciraaʔuu` → `karûrasučirâ'û` (the `c` before `i` becomes `č` because phonetic form shows /tʃ/)
- `paaʔatuʔ` → `pâ'atu'`
- `cikic` → `cikic` (stays `c` if phonetic form confirms /ts/ for both)

**Implementation notes:**
- The `c` → `č` decision requires inspecting the IPA `phonetic_form` for each entry. Where the phonetic form contains `č`, the corresponding `c` in the headword maps to `č`. Where it contains plain `c`, it stays `c`.
- For entries without a phonetic_form, flag for manual review rather than guessing.

#### Tasks
- [ ] Build respelling engine (local, no API) for `simplified_pronunciation`
- [ ] Build normalization engine for `normalized_form`
- [ ] Implement `c`/`č` disambiguation by cross-referencing phonetic_form
- [ ] Handle edge cases: alternation markers `{k/t}`, preverb notation `(ut...)`, whispered vowels (Blue Book p. xxi: "pronounced very softly, without using the voice, only the breath" — after hard consonants and accented syllables at word-end)
- [ ] Handle `ts`/`c` → `ch` variant: Blue Book notes `ts` sounds like *ch* "whenever it begins a syllable which is not the last syllable of a word" — decide whether respelling should reflect this allophonic rule or keep `ts` uniformly
- [ ] Run across all S2E entries, populate both new fields
- [ ] Validate `simplified_pronunciation` syllable boundaries against Blue Book parenthesized forms (e.g., `paresu'` → `(pa-ri-su')`)
- [ ] Generate report: entries with unknown characters (`?x?` markers), entries missing phonetic_form, `c`/`č` disambiguation failures

### 🔲 Phase 1.1d — Parsing Completeness Audit
**Priority:** High
**Depends on:** Phase 1.1a
**Effort:** Medium

Use Gemini API (env var `GEMINI_API_KEY`) as an agent to validate entries against source page PDFs.

Tasks:
- [ ] Local field validation: check every entry for empty headwords, phonetic forms, grammatical class, glosses
- [ ] Phonetic character validation: flag any chars not in the valid IPA set post-normalization
- [ ] Noun glottal stop check: nouns ending in vowel without `ʔ` → possible OCR miss
- [ ] AI batch validation (Gemini): send batches of 20 entries, check phonetic↔headword consistency
- [ ] Generate audit report with flag counts and prioritized fix list
- [ ] Checkpointing for resume after interruption

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

### 🔲 Phase 2.2 — Blue Book Cross-Verification
**Priority:** Medium
**Depends on:** Phase 1.1b (linked data)
**Effort:** Large

Use the Blue Book (Pari Pakuru') as a verification corpus and example source.

Blue Book structure: 21 lessons with dialogues, vocabulary, grammar explanations, useful phrases. Pages are split as PDFs in `pari pakuru/Blue Book - Pari Pakuru - split/`. Text extraction in `Blue_Book_Pari_Pakuru.txt`.

Tasks:
- [ ] Extract all Skiri words from Blue Book text with page numbers and English translations
- [ ] Match Blue Book words to dictionary headwords
- [ ] Compare Blue Book pronunciation (parenthesized forms like `(rak-ta-rih-ka-ru-kus)`) against dictionary phonetic forms
- [ ] Populate `examples` array with attested Blue Book usage
- [ ] Flag words in Blue Book not in dictionary (gaps)
- [ ] Flag dictionary words with Blue Book attestation (high confidence)
- [ ] Note Blue Book uses Pari Pakuru practical orthography vs. Parks linguistic orthography — reconciliation needed

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
| `run_parser_e2s.py` | `scripts/` | Parse E2S dictionary pages | No |
| `s2e_parser.py` | `scripts/` | Parse S2E dictionary pages | No |
| `verify_with_gemini.py` | `scripts/` | Verify parsed entries with Gemini | Yes (GEMINI_API_KEY) |
| `verify_with_claude.py` | `scripts/` | Verify parsed entries with Claude | Yes |

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
