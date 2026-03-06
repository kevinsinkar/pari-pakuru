# Phase 1.1 — Pronunciation Respelling System & Validation Agent

## The Problem

The Parks dictionary provides phonetic forms in square brackets (e.g., `[–wii•tɪ{k/t}–]`) using a linguistic orthography with specialized symbols (®, accented vowels, syllable bullets). A learner who picks up this dictionary cold has no intuitive way to *say* these words. The Blue Book (Pari Pakuru') solved this for its practical alphabet using parenthesized pronunciation with hyphens (e.g., `(rak-ta-rih-ka-ru-kus)`), but that system was designed for a different orthography.

Phase 1.1 bridges both: a deterministic mapping from the Parks phonetic form to a **simplified pronunciation respelling** that any English reader can approximate, stored as the `simplified_pronunciation` field in every Skiri-to-English JSON entry.

---

## Part A: The Pronunciation Respelling Key

### Source of Truth: Parks Dictionary Sound Key (PDF 01, p. xvii)

The respelling system maps each Skiri orthographic symbol to an English-approximation pronunciation hint. The key principle: **use only standard English letter combinations** so no specialized fonts or symbols are needed.

### Consonant Mapping

| Skiri Letter | Parks Description | English Approximation | Respelling Symbol | Example (Skiri → English) |
|---|---|---|---|---|
| **p** | as in English *spot* (unaspirated) | "p" as in "spin" | `p` | piíta → `PEE-tah` ("man") |
| **t** | as in English *stop* (unaspirated) | "t" as in "start" | `t` | taátu® → `TAH-tuh` ("plant") |
| **k** | as in English *skate* (unaspirated) | "k" as in "skip" | `k` | kariíku® → `kah-REE-kuh` ("liver") |
| **c** | as in English *patch* and *cents* | "ts" as in "cats" | `ts` | cíkic → `TSEE-kits` ("itchy") |
| **s** | as in English *sit* | "s" as in "sit" | `s` | sát → `saht` ("walnut") |
| **w** | as in English *wall* | "w" as in "wall" | `w` | áwi®u® → `AH-wih-uh` ("mage") |
| **r** | as in Spanish *pero* (tapped/flapped) | "r" (soft tap, like fast "d") | `r` | rákis → `RAH-kis` ("wood") |
| **h** | as in English *hit* | "h" as in "hit" | `h` | hiítu® → `HEE-tuh` ("feather") |
| **®** (glottal stop) | as in English *uh-uh* | glottal catch (brief pause) | `'` (apostrophe) | paátu® → `PAH-tu'` ("blood") |

### Vowel Mapping

| Skiri Letter | Parks Description | English Approximation | Respelling Symbol | Example |
|---|---|---|---|---|
| **a** (short) | as in English *putt* | "uh" as in "putt" / "above" | `ah` | ásku → `AHS-ku` ("one") |
| **aa** (long) | as in English *father* | "ah" as in "father" (held longer) | `aah` | haátu® → `HAAH-tu'` ("tongue") |
| **i** (short) | as in English *pit* | "ih" as in "pit" | `ih` | pítku → `PIHT-ku` ("two") |
| **ii** (long) | as in English *weed* | "ee" as in "weed" | `ee` | piíta → `PEE-tah` ("man") |
| **u** (short) | as in English *boot* (shorter) | "u" as in "put" | `u` | ut → `ut` ("prairie chicken") |
| **uu** (long) | as in English *rude* | "oo" as in "rude" | `oo` | uukawikis → `OO-kah-wih-kis` ("lance") |

### Suprasegmental & Special Symbols

| Feature | Parks Notation | Respelling Convention | Notes |
|---|---|---|---|
| **Accent (high pitch)** | á, í, ú (acute accent) | CAPS on stressed syllable | e.g., ásku → `AHS-ku` |
| **Syllable boundary** | • (bullet in phonetic form) | `-` (hyphen) | Standard syllable separator |
| **Glottal stop (®)** | ® | `'` | Brief catch in throat |
| **Long vowel** | doubled letter (aa, ii, uu) | doubled respelling (aah, ee, oo) | Hold the sound longer |
| **Whispered vowel** | word-final after consonant | `(h)` or parenthesized vowel | Barely voiced, breathy |
| **Morpheme boundary** | + (in etymologies) | not shown in respelling | Pronunciation is continuous |

### Reconciliation Notes: Parks vs. Blue Book

| Feature | Parks Dictionary | Blue Book (Pari Pakuru') | Unified Respelling |
|---|---|---|---|
| Phonetic notation | Square brackets `[...]` | Parentheses `(...)` | Generates from Parks `[...]` |
| Syllable marker | Bullet `•` | Hyphen `-` | Hyphen `-` |
| Long vowels | Doubled letters (aa, ii) | Underlined vowels | Doubled respelling symbols |
| Glottal stop | `®` | `'` (apostrophe) | `'` (apostrophe) |
| `c` sound | `c` | `ts` | `ts` |
| `r` after `h` (Skiri) | `hr` → silent `r` | `hr` → just `h` | `h` (note Skiri dialect) |
| `e` vowel | Not used (Skiri uses `i`) | Used in South Band | `ih` (mapped to Skiri `i`) |

---

## Part B: The Validation Agent — Word-by-Word Audit

### Purpose

An AI-assisted agent that processes every dictionary entry to:

1. **Verify parsing completeness** — confirm every field in the JSON schema was correctly extracted from the source page
2. **Validate phonetic form transcription** — ensure the `phonetic_form` field accurately captures the `[...]` content from the dictionary, character-for-character
3. **Generate pronunciation respelling** — apply the mapping above to auto-populate the `simplified_pronunciation` field
4. **Flag anomalies** — mark entries where the phonetic form seems inconsistent with the headword, where expected characters are missing, or where the respelling algorithm encounters an unmapped symbol

### Agent Workflow

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: LOAD ENTRY                                     │
│  Read one JSON entry from the parsed dictionary          │
│  Check: all required fields present?                     │
│         headword ≠ empty?                                │
│         phonetic_form ≠ empty?                           │
│         grammatical_class in known set?                  │
│         verb_class in known set (if verb)?               │
│         glosses array ≠ empty?                           │
│                                                         │
│  → If any field missing/empty → FLAG: "incomplete_parse" │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: VALIDATE PHONETIC FORM                         │
│  Check every character in phonetic_form against the      │
│  allowed character set from the Sound Key:               │
│                                                         │
│  Allowed: a á i í u ú p t k c s w r h ® • ( ) { } / –  │
│  Plus: vowel length (aa, ii, uu), accent marks           │
│                                                         │
│  Check: no stray OCR artifacts?                          │
│         brackets stripped (raw content only)?             │
│         syllable bullets (•) present where expected?     │
│                                                         │
│  → If unknown char found → FLAG: "phonetic_char_error"   │
│  → If no bullets found → FLAG: "missing_syllabification" │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: GENERATE PRONUNCIATION RESPELLING              │
│  Apply the mapping rules (Part A above) left-to-right:   │
│                                                         │
│  1. Tokenize phonetic_form into segments:                │
│     - Identify long vowels first (aa → aah, ii → ee)    │
│     - Then short vowels (a → ah, i → ih, u → u)         │
│     - Then consonants (c → ts, ® → ', etc.)             │
│     - Then suprasegmentals (• → -, accent → CAPS)       │
│                                                         │
│  2. Assemble syllables with hyphens                      │
│  3. Capitalize the accented/stressed syllable             │
│  4. Store result in simplified_pronunciation              │
│                                                         │
│  → If algorithm produces empty string → FLAG: "respell_fail" │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 4: CROSS-CHECK WITH BLUE BOOK (where possible)    │
│  If headword appears in Blue Book text:                  │
│     Compare respelling with Blue Book pronunciation      │
│     (the parenthesized forms)                            │
│                                                         │
│  → If mismatch → FLAG: "blue_book_discrepancy"           │
│  → If match → CONFIRM: "blue_book_verified"              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 5: WRITE AUDIT LOG                                │
│  For every entry, record:                                │
│     - entry_id / headword                                │
│     - parsing_status: complete | incomplete              │
│     - phonetic_status: valid | flagged                   │
│     - respelling_status: generated | failed              │
│     - blue_book_status: verified | discrepancy | n/a     │
│     - flags: [list of all flags with details]            │
│     - simplified_pronunciation: "the result"             │
└─────────────────────────────────────────────────────────┘
```

### Flag Categories & Resolution

| Flag | Meaning | Resolution |
|---|---|---|
| `incomplete_parse` | A required JSON field is empty or missing | Re-examine source page; likely OCR or column-split issue |
| `phonetic_char_error` | Unknown character in phonetic form | Likely OCR artifact (e.g., `ñ` instead of `®`); correct manually |
| `missing_syllabification` | No syllable bullets in phonetic form | Some entries may lack them; agent marks for manual review |
| `respell_fail` | Respelling algorithm produced empty or nonsensical output | Edge case in mapping rules; examine and extend rules |
| `blue_book_discrepancy` | Respelling doesn't match Blue Book pronunciation | Could be dialect difference (Skiri vs. South Band) or extraction error |
| `blue_book_verified` | Respelling matches Blue Book | High confidence in accuracy |

### Priority Order for Resolving Flags

1. `phonetic_char_error` — fix these first; they indicate data corruption
2. `incomplete_parse` — fill in missing fields before respelling
3. `respell_fail` — extend the mapping rules to handle edge cases
4. `blue_book_discrepancy` — investigate; may reveal dialect notes worth capturing
5. `missing_syllabification` — lower priority; respelling can still work without bullets

---

## Part C: Implementation Milestones

### Milestone 1.1a — Static Respelling Key (This Session)
**Deliverable:** A machine-readable JSON mapping file containing every Skiri orthographic symbol → respelling symbol pair, plus rules for accent handling, long vowels, and special combinations.
**Validation:** Manually test against 10-20 known words from the Sound Key examples.

### Milestone 1.1b — Respelling Algorithm
**Deliverable:** A function/script that takes a raw `phonetic_form` string and outputs a `simplified_pronunciation` string.
**Validation:** Run against all Sound Key example words; 100% match expected.

### Milestone 1.1c — Parsing Completeness Checker
**Deliverable:** A script that reads the parsed JSON entries and checks every field for presence and valid content.
**Validation:** Produces a report showing % complete, with specific entries flagged.

### Milestone 1.1d — Phonetic Form Validator
**Deliverable:** A script that scans every `phonetic_form` for characters outside the allowed set.
**Validation:** Every flagged character is either a known OCR error or a genuine extension to the Sound Key.

### Milestone 1.1e — Blue Book Cross-Reference Index
**Deliverable:** An index mapping every Skiri word in the Blue Book text to its page number and context, linked to the corresponding dictionary headword (where it exists).
**Validation:** Words found in both sources can be compared; words found only in Blue Book are flagged as "dictionary gap"; words found only in dictionary are noted as "no Blue Book attestation."

### Milestone 1.1f — Full Audit Run
**Deliverable:** Run the complete agent pipeline across the entire parsed dictionary. Produce an audit report with:
- Total entries processed
- % with complete parsing
- % with valid phonetic forms
- % with successful respelling generation
- % cross-verified against Blue Book
- List of all flagged entries, sorted by flag type

---

## Part D: Edge Cases & Design Decisions to Resolve

These are questions that will surface during implementation. Documenting them now so they don't become blockers:

1. **Accent ambiguity:** When a phonetic form has no marked accent, the Blue Book convention says stress falls on the first syllable. Should the respelling CAPITALIZE the first syllable by default, or leave it unmarked?
   - *Recommendation:* Capitalize first syllable as default; only override when accent mark is explicit.

2. **Whispered vowels:** The Blue Book notes that word-final vowels after hard consonants are often whispered. Should the respelling indicate this?
   - *Recommendation:* Use parenthesized vowel, e.g., `PAHT-su(h)` for paksu'. This alerts the learner without overcomplicating.

3. **Dialect splits (Skiri vs. South Band):** Some entries have variant forms. The respelling should be generated for the Skiri form by default (since this is a Skiri dictionary), with South Band variants noted if present.
   - *Recommendation:* Primary respelling = Skiri. Add optional `sb_pronunciation` field for South Band if data exists.

4. **The `c` → `ts` mapping:** Parks uses `c` for the affricate (like English "cats" or "church"). The Blue Book uses `ts`. The respelling should use `ts` since it's more intuitive for English readers.
   - *Recommendation:* Always respell `c` as `ts`.

5. **Compound phonetic forms with morpheme notation:** Some phonetic forms include `{k/t}` alternation markers or `(ut...)` preverb indicators. These are grammatical, not phonetic — they should be stripped before respelling.
   - *Recommendation:* Pre-process phonetic forms to remove `{...}`, `(...)` preverb markers, and `/` alternation markers before applying respelling rules.

6. **The `®` glyph:** OCR often corrupts this. Common misreads include `(R)`, `r`, or missing entirely. The validation agent should be especially attentive to word-final positions where `®` (glottal stop + nominative suffix) is extremely common.
   - *Recommendation:* If a noun headword ends in a vowel and lacks `®` but the grammatical class is N, flag for review.

---

## What This Unlocks

Once Phase 1.1 is complete, every dictionary entry will have:
- A verified, clean `phonetic_form`
- A learner-friendly `simplified_pronunciation`
- An audit trail documenting parsing quality

This directly feeds into:
- **Phase 1.2** (Database Schema) — the validated data is what gets loaded
- **Phase 2.1** (Semantic Tagging) — clean glosses are a prerequisite
- **Phase 2.2** (Blue Book Verification) — the cross-reference index from 1.1e is the starting point
- **Phase 3** (Grammar Engine) — the phonetic validation ensures the morpheme inventory is built on accurate forms
