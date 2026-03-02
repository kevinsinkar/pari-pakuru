# SKIRI PAWNEE DICTIONARY PARSING INSTRUCTIONS

## OVERVIEW
You are parsing a Skiri Pawnee bilingual dictionary with two sections:
1. **Skiri-to-English** entries (Skiri headwords → English definitions)
2. **English-to-Skiri** entries (English headwords → Skiri translations with subentries)

You will receive **TWO consecutive pages** (page N and page N+1) to handle entries that span across page boundaries.

---

## CRITICAL EXTRACTION PRIORITY

**MOST IMPORTANT:** The **phonetic form** in square brackets [...] must be extracted with 100% accuracy. This is the highest priority field in every entry.

---

## DICTIONARY LAYOUT

### Physical Format
- **Two-column layout** per page
- Read **left column top-to-bottom**, then **right column top-to-bottom**
- Alphabetical guide letters at top of each page
- Entries may span columns or pages

### Entry Boundaries
- **New entry begins:** Boldface headword (Skiri or English depending on section)
- **Entry ends:** Where next boldface headword begins
- **Cross-page entries:** Use alphabetical headers to verify correct sequence

---

## PART 1: SKIRI-TO-ENGLISH ENTRIES

### Structure Recognition

#### PART I: Primary Information
Extract in this order:

1. **Headword** (required)
   - Format: **Boldface** Skiri word
   - May be: simple stem, compound, or stem requiring preverb
   
2. **Stem Preverb** (if present)
   - Format: Parentheses immediately after headword: `(ut...)`, `(uur...)`, `(ir...)`
   - These appear BEFORE the headword is used but are noted AFTER it

3. **Phonetic Form** (required - CRITICAL)
   - Format: `[phonetic transcription]` in square brackets
   - Contains syllable breaks marked with small bullets (•)
   - Extract EXACTLY as written, preserving all diacritics and special characters
   - Examples: `[-wii•-t,u®(h)]`, `[ti•k-su®]`, `[a®-wi•-®u®]`

4. **Grammatical Information**
   - **Grammatical Class:** SMALL CAPS abbreviation
     - Common: VI (intransitive verb), VT (transitive verb), N (noun), VD (descriptive verb), ADJ, ADV
     - See full list in abbreviations reference
   
   - **Verb Class:** Number in parentheses (for verbs only)
     - Format: `(1)`, `(1-a)`, `(1-i)`, `(2)`, `(2-i)`, `(3)`, `(4)`, `(4-i)`, `(u)`, `(wi)`
     - Indicates inflectional pattern
   
   - **Additional Forms:** Content in curly brackets `{...}`
     - Irregular/notable grammatical forms
     - Examples: `{pl. obj., raawi-}`, `{du. obj., si-}`

5. **Glosses** (English definitions)
   - Numbered if multiple senses: `1. definition` `2. definition`
   - May include italicized usage notes explaining context
   - Format: "main definition, *as usage clarification*"

6. **Etymology** (if present)
   - Format: `<constituent breakdown, literal meaning>`
   - Enclosed in angle brackets
   - Contains morpheme-by-morpheme analysis
   - Often includes literal translation
   - Example: `<uur+ra+uusik, image to go down, i.e., go down quickly>`

7. **Cognates** (if present)
   - Related forms in sister languages
   - Prefixed with language code: `Ar.` (Arikara), `Pa.` (Pawnee), `Wi.` (Wichita), `Ki.` (Kitsai), `SB` (South Band)
   - Example: `Wi. chaxkiyac 'your skin'`

#### PART II: Illustrative Forms (for verbs)

1. **Standard Paradigmatic Forms** (numbered list 1-5)
   - **Form 1:** 1st Person Singular Subject, Indicative Mode, Perfective
   - **Form 2:** 3rd Person Singular Subject, Indicative Mode, Perfective
   - **Form 3:** 3rd Person Singular Subject, Indicative Mode, Imperfective
   - **Form 4:** 3rd Person Singular Subject, Absolutive Mode, Subordinate Perfective
   - **Form 5:** 3rd Person Singular Subject, Indicative Mode, Perfective Intentive
   
   Note: Some verb classes lack certain forms - extract what is present

2. **Additional Forms** (if present)
   - Marked with bullet points (•)
   - Plural, distributive, or other special inflections
   - Include description and form

3. **Examples** (if present)
   - Sentences marked with bullet point (•)
   - May include Skiri text and/or English translation
   - Illustrate usage in context

### Special Cases

#### Compound Stems (Preverb + Ø + Noun)
- Structure shown in Figure 6 of documentation
- Preverb noted in parentheses after headword
- May have null verb stem (Ø)
- Example: `Ø (ut...) ciksu® [-Ø- cík•su®] VI(Ø–1-a) {...} VT(4) [1-a] {dist., du., pl. agent, ciks+u®}`

#### Dependent Forms as Entry Heads
- When a dependent/bound form is the headword
- Entry provides examples of derived stems using this element
- Extract all derived forms with their meanings

---

## PART 2: ENGLISH-TO-SKIRI ENTRIES

### Structure Recognition

English-to-Skiri entries have the same internal structure as Skiri-to-English BUT:
- **No subentries** in Skiri-to-English
- **Multiple subentries** in English-to-Skiri (one English word may have multiple Skiri translations)

#### Top Level
1. **English Entry Word** (required)
   - Format: **Boldface** English word at entry start
   - Example: `stop`

2. **Subentries Array**
   - Each different Skiri translation = separate subentry
   - Subentries numbered implicitly by order
   - Each subentry has Parts I, II, and III (as applicable)

#### Each Subentry Contains:

**PART I:** (same structure as Skiri-to-English Part I)
- Skiri term (boldface)
- Stem preverb (if present) - NOTE: appears AFTER stem in citation
- Phonetic form [...]
- Grammatical classification
- Grammatical forms {...}
- English glosses (numbered senses)
- Etymology <...>

**PART II:** (same structure as Skiri-to-English Part II)
- Paradigmatic forms (5 standard forms for verbs)
- Additional forms (with bullets)
- Examples (with bullets)

**PART III:** Cross-references (unique to English-to-Skiri)
- Format: `see ENGLISH_WORD {skiri_form}; ENGLISH_WORD {skiri_form, skiri_form}`
- Multiple cross-references separated by semicolons
- Each reference: English entry head + its Skiri equivalents in curly brackets
- Enables user to consult related English words

### Example Structure from Documentation (Figure 1)
```
stop awPuusik (uur...) [=a•wi•®uu•s,u®(h)=] VI(4) 1.
quiet down, calm down (purposefully). 2. stop,
cease an activity, as before its completion. <uur+ra
wi+uusik, image to go down, i.e., go down quickly>
1. tatuurawiPuusit 2. tuurawiPuusit 3. tuurawi-
PuusIiku® 4. iriruurawiPuusit 5. tuurawiPuusiksta
```

This shows:
- English entry word: **stop**
- Subentry 1 begins with Skiri term: **awPuusik**
- Has preverb: (uur...)
- Phonetic form in brackets
- Grammatical info: VI(4)
- Numbered glosses
- Etymology in angle brackets
- Part II with 5 paradigmatic forms

---

## PARSING WORKFLOW

### Step 1: Identify Section
Determine if parsing **Skiri-to-English** or **English-to-Skiri** section

### Step 2: Locate Entries
- Scan for **boldface headwords**
- Track entry boundaries (next boldface = new entry)
- Handle entries spanning columns/pages

### Step 3: For Each Entry

#### A. Extract Entry Metadata
```json
{
  "page_number": 123,
  "column": "left",
  "continues_from_previous_page": false,
  "continues_to_next_page": true
}
```

#### B. Parse Headword
- Extract boldface term
- Check for parenthetical preverb immediately following

#### C. Extract Phonetic Form (CRITICAL - highest priority)
- Locate square brackets [...]
- Extract complete contents preserving:
  - All diacritical marks (macrons, accents, etc.)
  - Special characters (®, glottal stop markers)
  - Syllable break markers (•)
  - Length markers (:)
- Verify extraction accuracy

#### D. Parse Grammatical Information
- Extract SMALL CAPS class abbreviation
- Extract parenthesized verb class (if present)
- Extract curly bracket forms {...}

#### E. Parse Glosses
- Identify numbered definitions
- Separate main definitions from italicized usage notes
- Preserve numbering

#### F. Parse Etymology (if present)
- Extract complete angle bracket contents <...>
- Parse constituent elements and literal translation

#### G. Parse Part II (if present)
- Extract numbered paradigmatic forms (1-5)
- Extract any additional bulleted forms
- Extract example sentences

#### H. For English-to-Skiri: Parse Part III (if present)
- Extract cross-reference structure
- Identify English terms and their Skiri equivalents

### Step 4: Validate Extraction
- **Required fields present:** headword, phonetic_form
- **Phonetic form accuracy:** Double-check this field
- **Proper nesting:** Part I, II, III in correct structure
- **Cross-page continuity:** Entries spanning pages are complete

---

## SOUND KEY REFERENCE

### Consonants
- **p** - as in "spot" (never aspirated)
- **t** - as in "stop" (never aspirated)
- **k** - as in "skate" (never aspirated)
- **c** - as in "patch" and "cents"
- **s** - as in "sit"
- **w** - as in "wall"
- **r** - as in Spanish "pero" (flap/tap)
- **h** - as in "hit"
- **®** - glottal stop, as in "uh-oh"

### Vowels
- **i** - as in "pit" (short)
- **ii** - as in "weed" (long)
- **u** - as in "boot" (short)
- **uu** - as in "rude" (long)
- **a** - as in "putt" (short)
- **aa** - as in "father" (long)

---

## COMMON ABBREVIATIONS

### Grammatical Classes
- **VI** - intransitive verb
- **VT** - transitive verb
- **VD** - descriptive verb
- **VL** - locative verb
- **VP** - patientive/passive verb
- **VR** - reflexive verb
- **N** - noun
- **N-DEP** - dependent noun stem
- **N-KIN** - inalienably possessed kinship term
- **ADJ** - adjective
- **ADV** - adverb(ial)
- **PRON** - pronoun
- **DEM** - demonstrative
- **NUM** - numeral

### Verb Classes
- **(1)** - Class 1: -a suffixed to dependent forms
- **(1-a)** - Class 1-a: -a suffix, intentive perfective in -asta
- **(1-i)** - Class 1-i: -i suffix, imperfective in -i
- **(2)** - Class 2: -i suffixed to dependent forms
- **(2-i)** - Class 2-i: -i suffix, imperfective in -i
- **(3)** - Class 3: various stem-specific changes
- **(4)** - Class 4: no stem change in dependent forms
- **(4-i)** - Class 4-i: no change, imperfective in -i
- **(u)** - Inflected like descriptive verbs, -u suffix
- **(wi)** - Inflected like locative verbs, -wi suffix

### Language Codes (for cognates)
- **Ar.** - Arikara
- **Pa.** - Pawnee (general)
- **Sk.** - Skiri Pawnee
- **Wi.** - Wichita
- **Ki.** - Kitsai
- **SB** - South Band Pawnee

---

## OUTPUT FORMAT

Return a JSON array following the appropriate schema:
- **Skiri-to-English:** Use Skiri-to-English JSON Schema
- **English-to-Skiri:** Use English-to-Skiri JSON Schema

### Quality Checks Before Output:
1. ✓ Phonetic forms extracted with 100% accuracy
2. ✓ All required fields present
3. ✓ Entries spanning pages are merged correctly
4. ✓ Grammatical information properly parsed
5. ✓ Etymology brackets matched correctly
6. ✓ Paradigmatic forms numbered 1-5 correctly
7. ✓ Cross-references (Part III) properly structured

---

## SPECIAL FORMATTING MARKERS

### Recognizing Delimiters
- **[...]** - Phonetic form
- **{...}** - Additional grammatical forms
- **<...>** - Etymology
- **(...)** - Preverb notation or verb class
- **•** - Bullet point for examples/additional forms
- **SMALL CAPS** - Grammatical class abbreviation
- ***Italics*** - Usage notes in glosses
- **1. 2. 3.** - Numbered glosses or paradigmatic forms

### Syllable Breaks in Phonetics
- Small bullet (•) marks syllable boundaries
- Hyphens (-) may appear for morpheme boundaries
- Preserve all these markers exactly

---

## ERROR HANDLING

### If Uncertain:
1. **Mark ambiguous fields** with a note in metadata
2. **Include raw text** if parsing is unclear
3. **Never guess** phonetic forms - extract exactly or mark as uncertain
4. **Preserve original** if structure is non-standard

### Common Edge Cases:
- **Missing forms:** Some verb classes lack certain paradigmatic forms - this is expected
- **Multiple preverbs:** Entry may cite multiple preverb options
- **Compound entries:** May have complex internal structure (preverb + Ø + noun)
- **Derived stems:** Entry head may be a bound form with examples of derived forms

---

## EXAMPLE ENTRY WALKTHROUGH

### Input Text (Skiri-to-English):
```
kawPuktawuh (ut...) [+ si=] [=ka•wi•®úk•ta• wu(h)=]
GRAMMATICAL FORM
VT(1) {pl. obj., kawPuktawaawuh [+ raar=]} (du. obj.,
join together, as when sewing two or more pieces
together. <ka.wi.ukta (ut...)+wuh, cause to be joined
together>
1. sitatkawPuktawu 2. situłkawPuktawu 3. si-
tułkawPuktawuhu® 4. iriisirułkawPuktawuha 5.
situłkawPuktawista • tatuuhahkawPuktawaawu
I joined them (pl.) together.
```

### Expected JSON Output:
```json
{
  "headword": "kawPuktawuh",
  "entry_metadata": {
    "page_number": 156,
    "column": "left"
  },
  "part_I": {
    "stem_preverb": "(ut...)",
    "phonetic_form": "[=ka•wi•®úk•ta• wu(h)=]",
    "grammatical_info": {
      "grammatical_class": "VT",
      "verb_class": "(1)",
      "additional_forms": [
        {
          "form_type": "pl. obj.",
          "form": "kawPuktawaawuh [+ raar=]"
        },
        {
          "form_type": "du. obj.",
          "form": "si-"
        }
      ]
    },
    "glosses": [
      {
        "number": null,
        "definition": "join together",
        "usage_notes": "as when sewing two or more pieces together"
      }
    ],
    "etymology": {
      "raw_etymology": "ka.wi.ukta (ut...)+wuh, cause to be joined together",
      "constituent_elements": [
        {"morpheme": "ka.wi.ukta", "gloss": "to join"},
        {"morpheme": "(ut...)", "gloss": "preverb"},
        {"morpheme": "+wuh", "gloss": "causative"}
      ],
      "literal_translation": "cause to be joined together"
    }
  },
  "part_II": {
    "paradigmatic_forms": {
      "form_1": "sitatkawPuktawu",
      "form_2": "situłkawPuktawu",
      "form_3": "situłkawPuktawuhu®",
      "form_4": "iriisirułkawPuktawuha",
      "form_5": "situłkawPuktawista"
    },
    "examples": [
      {
        "skiri_text": "tatuuhahkawPuktawaawu",
        "english_translation": "I joined them (pl.) together."
      }
    ]
  }
}
```

---

## FINAL REMINDERS

1. **PHONETIC FORM IS CRITICAL** - Extract with 100% accuracy
2. Handle entries spanning page boundaries using both pages provided
3. Follow alphabetical headers to verify correct sequence
4. Process left column completely before right column
5. Preserve all special characters, diacritics, and formatting markers
6. When in doubt, include raw text and mark as uncertain
7. Validate output against JSON schema before returning

---

## READY TO PARSE

When you receive dictionary pages, respond with:
1. Section identified (Skiri-to-English OR English-to-Skiri)
2. Number of entries found
3. JSON array of parsed entries following the appropriate schema
4. Any notes about uncertain or unusual structures encountered
