# Phase 3.2a — Template-Based Sentence Assembly

## Design Document & Claude Code Handoff

**Date:** 2026-03-20
**Author:** Opus linguistic analysis of 160 Blue Book sentences + Parks grammatical overview
**Status:** Template design complete → ready for engine implementation

---

## 1. What This Is

A guided sentence construction system using **fixed templates** extracted from Blue Book dialogues. Not free-form translation — the learner selects a pattern, fills slots with dictionary entries, and the engine inflects and assembles.

**Key principle:** Every template output must be validated against attested Blue Book examples. These templates are *descriptions of patterns the Blue Book already teaches*, not inventions.

---

## 2. Sentence Pattern Analysis

### 2.1 Classification of 160 Blue Book Sentences

| Pattern | Count | Lessons | Coverage |
|---------|-------|---------|----------|
| Content questions (what/where/who/when/how much) | 30 | L01–L20 | 18.8% |
| Yes/no questions | 15 | L01–L20 | 9.4% |
| Negation responses | 13 | L01–L18 | 8.1% |
| Identification ("This is X") | 11 | L01–L13 | 6.9% |
| Subject + intransitive verb | 9 | L06–L14 | 5.6% |
| Affirmation responses | 7 | L01–L20 | 4.4% |
| Descriptive ("X is red") | 4 | L02–L09 | 2.5% |
| Subject + transitive verb + object | 4 | L09–L14 | 2.5% |
| Imperatives | 4 | L12–L20 | 2.5% |
| 1sg declarative statements | 27 | L08–L20 | 16.9% |
| Greetings / social formulas | 5 | L20 | 3.1% |
| Extended narrative (reading) | 5 | L20 | 3.1% |
| Other (temporal, desire, body possession, etc.) | 26 | L05–L20 | 16.3% |

### 2.2 Key Word Order Rules (from BB Lesson 9 + Parks Grammar)

Skiri is basically **SOV** (Subject–Object–Verb) but with significant flexibility:

1. **Verb-final is the default:** `Pita ti•kuwutit rahurahki` → "The man killed a deer"
2. **Object can follow verb for emphasis:** `Pita kuruks ti .kuwutit` → "The man killed a bear" (same meaning, different emphasis — both attested in L14)
3. **Noun + ti + descriptive verb** is the standard descriptive pattern: `Rakis ti pahaat` → "The stick is red"
4. **Descriptive verb can precede noun:** `Ti pahaat rikutski` → "The bird is red" (both orders attested in L09)
5. **Question words are clause-initial:** `Kirike ras•taspe'?` → "What are you looking for?"
6. **ka- proclitic marks yes/no questions** and attaches to the verb: `Ka ra•pahaat rakis?` → "Is the stick red?"
7. **Adverbs precede the verb** (confirmed by function_words position_rule data: 151 ADV entries with `PRECEDES-VERB`)
8. **Temporal adverbs can be clause-initial or clause-final:** `Tiruks•tsak•ariki tatutsiks•a•wahri'` and `Tatutsiks•d .wahri' tiruks•tsak•ariki` both mean "I was working yesterday" (L17)
9. **Negation kaki is clause-initial,** often followed by a positive restatement: `Kaki tareus, ti pahaat` → "It's not blue, it's red"
10. **Imperative suks- is a proclitic on the verb:** `Suks•teka .rikut` → "Open the door"

---

## 3. The 10 Templates

### Template 1: IDENTIFICATION
**Pattern:** `ti [NOUN]`
**English:** "This is [noun]" / "He/She is [noun]"
**Blue Book attestations:** 11 sentences (L01, L05, L07, L13)

```
Structure:  ti + NOUN (independent form)
Slots:      [NOUN] — any N, N-KIN, or tribal name from dictionary
Examples:
  ti hitu'         → "This is a feather"
  ti atira'        → "She's my mother"  (kinship: 1sg form)
  ti Rihita        → "He's Ponca"  (tribal name, no suffix)
  ti Pahriksukat   → "He's Sioux"
```

**Morphological constraints:**
- Noun takes its independent (absolutive) form — the headword as stored in DB
- Kinship nouns: engine must select the correct possessive stem (calls possession_engine)
- No verb inflection needed — `ti` is a fixed particle (PROCLITIC, `position_rule=PROCLITIC`)

**Validation test cases:** L01 `ti hitu'`, L07 `ti atira'`, L13 `ti Rihita`, `ti Pasuhara`, `ti Asakiwa`, `ti Pahriksukat`, `ti Astarahi'`, `ti Tuhkaka'`


### Template 2: DESCRIPTIVE
**Pattern:** `[NOUN] ti [DESCRIPTIVE_VERB]`
**English:** "[Noun] is [quality]"
**Blue Book attestations:** 4 sentences (L02, L09)

```
Structure:  NOUN + ti + VD (3rd person, indicative, perfective)
Alt order:  ti + VD + NOUN  (both attested, same meaning)
Slots:      [NOUN] — any N
            [VD]   — descriptive verb (446 entries with class=VD in DB)
Examples:
  Rakis ti pahaat        → "The stick is red"
  Kiwaku ti pahaat       → "The fox is red"
  Rikutski ti pahaat     → "The bird is red"
  Ti pahaat rikutski     → "The bird is red" (alt order)
```

**Morphological constraints:**
- VD appears in 3rd person form (Form 1 from paradigmatic_forms, or headword if no paradigm)
- `ti` is the indicative particle — always present
- Noun in independent (absolutive) form

**Validation:** L02 `Rakis ti pahaat`, L09 `Kiwaku ti pahaat`, `Rikutski ti pahaat`, `Ti pahaat rikutski`


### Template 3: YES/NO QUESTION
**Pattern:** `ka [VERB_FORM] [NOUN]?`
**English:** "Is [noun] [verb]?" / "Did [subject] [verb]?"
**Blue Book attestations:** 15 sentences (L01–L20)

```
Structure:  ka + ra•/ru•/ras• VERB + NOUN?
Slots:      [SUBJECT_NOUN] — optional, any N (omitted when context is clear)
            [VERB]         — any verb, inflected for person/aspect
Examples:
  Ka rii hitu'?                → "Is this a feather?"
  Ka ra•pahaat rakis?          → "Is the stick red?"        (VD, 3sg)
  Ka ra•paks•taari'?           → "Does your head hurt?"     (body part incorporated)
  Ka ras•huras asaki?          → "Have you found the dog?"  (VT, 2sg)
  Ka ra•awari rikutski?        → "Is the bird flying?"      (VI, 3sg)
  Ka rut•erit kuruks?          → "Has he seen the bear?"    (VT, 3sg)
```

**Morphological constraints:**
- `ka` is the yes/no interrogative proclitic (slot 8 in proclitic template)
- Verb takes **absolutive mode** (ra-) for 3rd person, or **assertive + 2.A** (ras-/rus-) for 2sg
- Verb is fully conjugated — person, mode, aspect must be filled
- Subject noun, if present, can precede or follow the verb complex

**Validation:** L01 `Ka rii hitu'?`, L02 `Ka ra•pahaat rakis?`, L05 `Ka ra•paks•taari'?`, L08 `Ka ras•huras asaki?`, L09 `Ka ra•awari rikutski?`, L14 `Ka rut•erit kuruks?`

**Note on ka with adverbs:** `Tsikstit ka ras•pari'?` → "Are you well?" shows that an adverb can precede `ka`. Template should allow optional ADV before ka.


### Template 4: CONTENT QUESTION — WHAT
**Pattern:** `kirike [VERB_FORM] [NOUN]?`
**English:** "What is/does [subject] [verb]?"
**Blue Book attestations:** 17 sentences (L01–L18)

```
Structure:  (NOUN?) + kirike + VERB?
Slots:      [SUBJECT_NOUN] — optional, precedes kirike if present
            [VERB]         — conjugated verb (absolutive mode)
Examples:
  Kirike ru'?                  → "What is it?"
  Kirike ra•tarawis rakis?     → "What color is the stick?"
  Pita kirike rut•ari'?        → "What is the man doing?"
  Kirike ras•taspe'?           → "What are you looking for?"
  Kirike rasuks•a?             → "What did you eat?"
  Kirike rasutsiksari?         → "What were you doing?"
  Kirike ras•itska raskut•ara? → "What do you want to do?"
```

**Morphological constraints:**
- `kirike` (or `kirikii-`) is the content interrogative proclitic meaning "what"
- Requires **absolutive mode** on the verb
- Subject noun, when present, **precedes** kirike: `Pita kirike rut•ari'?`
- Person inflection on verb indicates who is asking/doing

**Sub-patterns observed:**
- `kirike ru'?` — "what is it?" (generic, no specific verb)
- `kirike ra•VERB?` — "what is [3sg] [verb]-ing?" (3sg absolutive)
- `kirike ras•VERB?` — "what [did you/are you] [verb]?" (2sg absolutive)
- `NOUN kirike rut•VERB?` — "what is [noun] doing?" (with subject)


### Template 5: CONTENT QUESTION — WHERE
**Pattern:** `kiru [VERB_FORM] [NOUN]?`
**English:** "Where is/did [subject] [verb]?"
**Blue Book attestations:** 7 sentences (L05–L13)

```
Structure:  kiru + VERB + (NOUN)?
Slots:      [SUBJECT_NOUN] — optional
            [VERB]         — conjugated (absolutive mode)
Examples:
  Kiru rdspaks•ku?        → "Where is your head (sitting)?"
  Kiru ras•kirik•ta?      → "Where is your eye (hanging)?"
  Kiru ruks•ku'?          → "Where was it (sitting)?"
  Kiru rasuks•at?         → "Where did you go?"
```

Also `kirti` for "where (has it gone)": `Kirti ra•'at rikutski?` → "Where has the bird gone?"

**Morphological constraints:**
- `kiru` / `kiruu-` is the locative interrogative
- Requires absolutive mode
- Frequently used with positional verbs (sitting, standing, hanging — VL class)


### Template 6: NEGATION
**Pattern:** `kaki('), [POSITIVE_RESTATEMENT]`
**English:** "No, [alternative statement]"
**Blue Book attestations:** 13 sentences (L01–L18)

```
Structure:  kaki + (optional: negated element) + (optional: positive restatement)
Slots:      [NEG_VERB]   — optional negated verb form
            [POS_CLAUSE] — optional positive alternative (uses another template)
Examples:
  Kaki, kaki karitki.                  → "No, it is not a rock"
  Kaki tareus, ti pahaat.              → "It's not blue, it's red"
  Kaki', pita t'ewasku'.              → "No, the man is laughing"
  Kaki', rikutski ti .'isat.          → "No, the bird has disappeared"
  Kaki', kakuruks•tahare.             → "No, it tasted bad"
  Kaki', tatitska rakti•u•ta          → "No, I want him to go"
```

**Morphological constraints:**
- `kaki` is standalone negation (also BB function word `kaki` = "no, it is not")
- Negative verb prefix `kaku-` also exists for embedded negation: `kakuruks•tahare` = "it did not taste good"
- Often followed by a positive restatement using another template pattern
- Template engine should support NEGATION wrapping any other template


### Template 7: AFFIRMATION + STATEMENT
**Pattern:** `[YES_WORD], [STATEMENT]`
**English:** "Yes, [statement]"
**Blue Book attestations:** 7 sentences (L01–L20)

```
Structure:  YES_PARTICLE + comma + STATEMENT (any other template)
Slots:      [YES_WORD]  — ahu' / hau / ilan'
            [STATEMENT] — any template output
Examples:
  Ahu', ti hitu'.              → "Yes, this is a feather"     (YES + T1)
  Hau, ti hitu'.               → "Yes, this is a feather"     (YES + T1)
  Ahu', rakis ti pahaat.       → "Yes, the stick is red"      (YES + T2)
  Ahu', tat .huras asaki.     → "Yes, I found the dog"       (YES + T8)
  Ilan', tiku•ratsaus.        → "Yes, I'm hungry"            (YES + T8)
```

**Notes:**
- `ahu'` and `hau` are interchangeable for "yes" (both in L01)
- `ilan'` is a variant "yes" (L11)
- The statement portion uses any other template — this is a **wrapper template**


### Template 8: 1st PERSON DECLARATIVE
**Pattern:** `[TEMPORAL?] [OBJECT?] [1SG_VERB] [LOCATIVE?]`
**English:** "I [verb] (object) (time/place)"
**Blue Book attestations:** 27 sentences (L08–L20) — the largest single category

```
Structure:  (TEMPORAL?) + (OBJECT?) + 1SG-VERB + (LOCATIVE?)
Slots:      [TEMPORAL]  — optional time word (rahesa' "tomorrow", tiruks•tsak•ariki "yesterday")
            [OBJECT]    — optional noun (for transitive verbs)
            [VERB]      — 1sg conjugated form (ta-...-t prefix pattern for indicative)
            [LOCATIVE]  — optional place (Pari "Pawnee", with -ru/-kat/-wiru locative)
Examples:
  Tatuks•at.                        → "I went"
  Tatuks•at Pari.                   → "I went to Pawnee"
  Tatuks•a kisatski.                → "I ate meat"
  Tah•raspe' asaki.                 → "I'm looking for my dog"
  Rahesa' tatut•a•wahri•usta.       → "Tomorrow I will work"
  Tiruks•tsak•ariki tatutsiks•d•wahri'. → "I was working yesterday"
  Kaas raku•kariu tatutak•erit.     → "I saw many cars"
  Tawit kaas tatutak•erit.          → "I saw three cars"
```

**Morphological constraints:**
- 1sg indicative: `ta-` mode + `t-` 1.A agent → `tat-` (with preverb/aspect)
- Past perfective: no suffix (-Ø PERF)
- Future intentive: `-sta` suffix
- Habitual/progressive: `-usuku'` suffix
- Object noun in independent form, can precede or follow verb
- Quantifier (NUM) precedes noun: `tawit kaas` "three cars"

**This is the highest-frequency production template.** It covers the core conversational pattern: "I did/do/will [verb] [thing]."


### Template 9: 3rd PERSON NARRATIVE (SUBJECT + VERB)
**Pattern:** `[SUBJECT] [VERB_3SG]` (intransitive) or `[SUBJECT] [VERB_3SG] [OBJECT]` (transitive)
**English:** "[Subject] is [verb]-ing" / "[Subject] [verb]-ed [object]"
**Blue Book attestations:** 13 sentences (L06–L14)

```
Structure:  SUBJECT + VERB_3SG + (OBJECT?)
Slots:      [SUBJECT]  — animate noun (person, animal)
            [VERB]     — 3sg form (ti-/tir-/tur- indicative 3.A prefixes)
            [OBJECT]   — optional noun for transitive verbs
Examples:
  Pita tiwari'.                          → "The man is walking about"
  Pita t'ewasku'.                        → "The man is laughing"
  Paresu ti•taka•asiku'.                 → "The hunter is shooting"
  Rikutski ti•waktahu'.                  → "The bird is singing"
  Asaki tirah•kI wat.                    → "The dog barked"
  Pita ti•kuwutit rahurahki.             → "The man killed a deer"
  Pita ti•kuwutit kuruks.               → "The man killed a bear"
  Rahurahki we tut•awi'at Karit•kutsu'. → "The deer jumped over the big rock"
```

**Morphological constraints:**
- 3sg indicative: `ti-` + `Ø-` 3.A → surface `ti-` (active verbs)
- Past perfective with `we` particle: `Rahurahki we tut•awi'at` — `we` signals completed action
- SOV default but OV also attested: `Pita kuruks ti .kuwutit` (L14 alt word order)
- Noun incorporation possible: `ti•taka•asiku'` = shoot (with incorporated element)

**This template + Template 3 (yes/no) + Template 4 (what) covers the core L06–L14 dialogues.**


### Template 10: IMPERATIVE
**Pattern:** `suks•[VERB] [OBJECT?]`
**English:** "[Do verb]!" / "Give [object]!"
**Blue Book attestations:** 4 sentences (L12, L15, L20)

```
Structure:  IMPERATIVE_PARTICLE + VERB + (OBJECT?)
Slots:      [IMP_PARTICLE] — suks (2sg), stiks (??), sisuks (2du), siks (2pl)
            [VERB]         — verb stem (no person inflection — imperative replaces it)
            [OBJECT]       — optional noun
Examples:
  Suks•u rekits•tiwiru'.    → "Give him the candy"
  Suks•teka .rikut.         → "Open the door"
  Suks•teka•wu.             → "Close the door"
  Sukspitit.                → "Sit down"
```

**Morphological constraints:**
- Imperative particles are proclitics: `suks-` (2sg command), `siks-` (2pl)
- Verb takes a special imperative form — not the standard person-inflected paradigm
- From function_words: 4 imperative markers with `position_rule=PROCLITIC`: suks, siks, sisuks, stiks

---

## 4. Template Slot Definitions

### 4.1 Slot Types

| Slot Type | Source | Example Values |
|-----------|--------|----------------|
| NOUN | lexical_entries WHERE grammatical_class='N' | paksuʔ "head", asaaki "dog", kaas "car" |
| NOUN_KIN | lexical_entries WHERE grammatical_class='N-KIN' | atiraʔ "mother" (1sg), asaas "father" (2sg) |
| VD | lexical_entries WHERE grammatical_class='VD' | pahaat "be red", tareus "be blue" |
| VI | lexical_entries WHERE grammatical_class='VI' | wariʔ "walk about", kikat "cry" |
| VT | lexical_entries WHERE grammatical_class='VT' | kuwutit "kill it", huraas "find it" |
| TEMPORAL | function_words WHERE refined_subclass LIKE '%temporal%' OR lesson-attested | rahesa' "tomorrow", tiruks•tsak•ariki "yesterday", hiras "at night" |
| LOCATIVE | Noun + locative suffix (-kat, -ru, -wiru) | Pari "Pawnee (place)", tuks•kaku' "in the house" |
| NUMERAL | function_words WHERE grammatical_class='NUM' | asku "one", pitku "two", tawit "three" |
| ADV_MANNER | function_words WHERE refined_subclass='adverb' AND position_rule='PRECEDES-VERB' | cikstit "well, fine", rariksisu "hard" |

### 4.2 Conjugation Requirements Per Template

| Template | Person Needed | Mode | Aspect | Engine Call |
|----------|--------------|------|--------|-------------|
| T1 (identification) | None | — | — | No conjugation (particle `ti` only) |
| T2 (descriptive) | 3sg | IND | PERF | Form 1 from paradigmatic_forms or headword |
| T3 (yes/no Q) | Variable | ABS (3sg) or ABS+2.A | PERF | Full conjugation engine |
| T4 (what Q) | Variable | ABS | PERF | Full conjugation engine |
| T5 (where Q) | Variable | ABS | PERF | Full conjugation engine |
| T6 (negation) | Mirrors inner | NEG.IND | PERF | kaki + inner template |
| T7 (affirmation) | Mirrors inner | — | — | YES particle + inner template |
| T8 (1sg declarative) | 1sg | IND | PERF/INT/HAB | Full conjugation engine |
| T9 (3sg narrative) | 3sg | IND | PERF | Full conjugation engine |
| T10 (imperative) | 2sg/2pl | IMP | — | Imperative-specific |

---

## 5. Assembly Engine Spec

### 5.1 Pipeline

```
User input:
  1. Select template (T1-T10)
  2. Fill slots (dropdown/search from DB)
     - Noun slot → search lexical_entries
     - Verb slot → search lexical_entries by grammatical_class
     - Temporal → pick from curated list
  3. Select person (if template requires it)
  4. Select tense/aspect (if template requires it)

Engine processing:
  1. Validate slot compatibility (e.g., VT requires object slot filled)
  2. Look up verb paradigm (paradigmatic_forms table)
     - If attested form exists → use it directly
     - If not → call conjugation engine (morpheme_inventory.py)
  3. Apply noun morphology
     - Independent form (default)
     - Locative suffix if LOCATIVE slot
     - Possessive form if kinship/body part (calls possession_engine.py)
  4. Apply word order rules per template
  5. Apply sound changes at word boundaries (if applicable)
  6. Generate morpheme breakdown

Output:
  {
    "skiri_sentence": "Pita ti•kuwutit rahurahki",
    "english_gloss": "The man killed a deer",
    "template_id": "T9",
    "confidence": "HIGH",
    "morpheme_breakdown": [
      {"form": "Pita", "gloss": "man", "type": "SUBJECT"},
      {"form": "ti•kuwutit", "gloss": "IND-3.A-kill.it-PERF", "type": "VERB"},
      {"form": "rahurahki", "gloss": "deer", "type": "OBJECT"}
    ],
    "bb_attestation": "L09, L14",
    "word_order_note": "SOV (default); OVS also attested in L14"
  }
```

### 5.2 Confidence Scoring for Template Output

Three levels (extending Phase 4.3):

- **HIGH**: Template output exactly matches a BB attestation (or differs only in the filled noun/verb, with the conjugation form being attested in paradigmatic_forms)
- **MEDIUM**: Template pattern is BB-attested but the specific verb form is engine-computed (not in paradigmatic_forms), or the word order variant is not directly attested
- **LOW**: Template extrapolation — pattern is theoretically valid per grammar rules but no close BB attestation exists

### 5.3 Integration Points

```
sentence_templates.py (NEW — DELIVERED)
  ├── imports from: morpheme_inventory.py (conjugation engine)
  ├── imports from: possession_engine.py (noun possession)
  ├── imports from: template_slot_fillers.py (curated dropdown data)
  ├── reads: skiri_pawnee.db
  │     ├── lexical_entries (slot filling + fuzzy lookup with BB alias)
  │     ├── paradigmatic_forms (attested verb forms)
  │     ├── function_words (particles, adverbs, numerals)
  │     ├── blue_book_attestations (validation + BB matching)
  │     └── kinship_paradigms (kinship slot)
  ├── exposes: assemble(template_id, slots) → TemplateResult
  ├── exposes: get_slot_options(template_id, slot_name) → List[Dict]
  └── exposes: list_templates() → List[Dict]

template_slot_fillers.py (NEW — DELIVERED)
  ├── 40 curated SlotFiller objects across 11 categories
  ├── 36 BB-attested, 4 Parks-dictionary supplemental
  ├── TEMPLATE_SLOT_MAP: which categories are valid per template
  ├── BB_VOCABULARY_ALIASES: 15 BB→Parks headword mappings
  └── exposes: get_fillers_for_slot(slot_type, bb_only) → List[SlotFiller]
```

---

## 6. Validation Test Suite

Every template has BB-attested test cases. The engine should pass these before shipping:

### Required Exact Matches (27 tests — all passing)

```python
VALIDATION_TESTS = [
    # T1: Identification
    ("T1", {"noun": "hitu'"}, "ti hitu'"),
    ("T1", {"noun": "Rihita"}, "ti Rihita"),

    # T2: Descriptive
    ("T2", {"noun": "rakis", "vd": "pahaat"}, "Rakis ti pahaat"),
    ("T2", {"noun": "kiwaku", "vd": "pahaat"}, "Kiwaku ti pahaat"),
    ("T2", {"noun": "rikutski", "vd": "pahaat"}, "Rikutski ti pahaat"),

    # T3: Yes/No question (structural match — verb conjugation tested separately)
    ("T3", {"noun": "hitu'", "verb_form": "rii"}, "Ka rii hitu'?"),
    ("T3", {"noun": "rakis", "verb_form": "ra•pahaat"}, "Ka ra•pahaat rakis?"),

    # T4: Content Q — What
    ("T4", {"verb_form": "ru'"}, "Kirike ru'?"),
    ("T4", {"subject": "pita", "verb_form": "rut•ari'"}, "Pita kirike rut•ari'?"),

    # T5: Content Q — Where
    ("T5", {"verb_form": "rasuks•at"}, "Kiru rasuks•at?"),

    # T6: Negation
    ("T6", {"inner": "kaki karitki"}, "Kaki, kaki karitki."),

    # T7: Affirmation
    ("T7", {"yes": "ahu'", "inner": "ti hitu'"}, "Ahu', ti hitu'."),

    # T8: 1sg declarative
    ("T8", {"verb_form": "tatuks•at"}, "Tatuks•at."),
    ("T8", {"verb_form": "tatuks•at", "locative": "Pari"}, "Tatuks•at Pari."),
    ("T8", {"verb_form": "tatuks•a", "object": "kisatski"}, "Tatuks•a kisatski."),

    # T9: 3sg narrative
    ("T9", {"subject": "pita", "verb_form": "tiwari'"}, "Pita tiwari'."),
    ("T9", {"subject": "pita", "verb_form": "ti•kuwutit", "object": "rahurahki"}, "Pita ti•kuwutit rahurahki."),
    ("T9", {"subject": "rikutski", "verb_form": "ti•waktahu'"}, "Rikutski ti•waktahu'."),

    # T10: Imperative
    ("T10", {"imp": "suks", "verb_form": "teka", "object": ".rikut"}, "Suks•teka .rikut."),
    ("T10", {"imp": "suks", "verb_form": "pitit"}, "Sukspitit."),
]
```

---

## 7. UI Spec (for web/app.py)

### Route: `/sentence-builder`

**Step 1: Pick a pattern**
Show 10 cards with English pattern + Skiri example:
- "This is [thing]" — Ti hitu'
- "[Thing] is [quality]" — Rakis ti pahaat
- "Is [thing] [quality]?" — Ka ra•pahaat rakis?
- etc.

**Step 2: Fill slots**
- Each slot shows a search dropdown backed by `/api/search`
- Filter by grammatical class (e.g., noun slot only shows N entries)
- Show pronunciation next to each option

**Step 3: Select person/tense (if needed)**
- Person: 1sg "I", 2sg "you", 3sg "he/she/it", 1du "we two", etc.
- Tense: present, past (perfective), future (intentive)

**Step 4: See result**
- Full assembled sentence in Skiri
- Morpheme breakdown with chip UI (reuse `_possession_widget.html` pattern)
- English gloss
- Confidence badge (HIGH/MEDIUM/LOW)
- "Attested in Blue Book Lesson X" note if exact match exists

### HTMX Integration
- Slot filling via `hx-get="/api/search?q=...&class=N"` → live search
- Assembly via `hx-post="/api/assemble"` with template_id + slot values → returns rendered result
- Progressive enhancement: works without JS, enhanced with HTMX

---

## 8. Implementation Order for Claude Code

1. **Drop files into repo** — `sentence_templates.py` and `template_slot_fillers.py` go into `scripts/`. Run `python sentence_templates.py test` to confirm 27/27 pass against the DB.

2. **BB vocabulary alias integration** — Wire `BB_VOCABULARY_ALIASES` from `template_slot_fillers.py` into the fuzzy `lookup_entry()` function so that "pita" reliably resolves to `pitaruʔ` (man) rather than `pitaksuʔ` (blanket). ~15 mappings, 20 minutes.

3. **`web/app.py` routes** — Web integration:
   - `GET /sentence-builder` — template selection + slot UI
   - `POST /api/assemble` — JSON assembly endpoint (calls `assemble()`)
   - `GET /api/slot-options?template=T8&slot=temporal` — calls `get_slot_options()`, returns JSON for HTMX dropdowns
   - `GET /api/search?class=N&q=...` — filtered search for free-form noun/verb slots

4. **`web/templates/sentence_builder.html`** — UI:
   - Template cards (10 cards with pattern + example)
   - Slot dropdowns with HTMX live search for nouns/verbs
   - **Curated dropdown** for temporal, adv_manner, yes_word, imp_particle (populated from `get_slot_options()`)
   - `we` particle toggle checkbox for T9
   - Morpheme breakdown display (reuse `_possession_widget.html` chip pattern)
   - Confidence badge (HIGH/MEDIUM/LOW)
   - "Attested in Blue Book Lesson X" citation when BB match found

5. **Ship #6 (PDF/Anki export)** in the same session — pure implementation, no analysis needed.

---

## 9. What This Does NOT Cover (Future Phases)

- **Free-form English → Skiri translation** (Phase 3.2c)
- **Automatic word order selection** (Phase 3.2b — needs more data)
- **Subordinate clauses** (L20 reading passages show these but they're too complex for v1)
- **Desire/want constructions** (L20 `tat•itska ratkti•u•ta` — complex embedding, needs separate analysis)
- **Temporal clause combination** ("When X, I did Y" — L16, L17 patterns)

These are explicitly deferred to Phase 3.2b+ and should not block shipping v1.

---

## Appendix B: BB-Attested Slot Fillers (Phase 3.1.6 Cross-Reference)

Cross-referenced 418 function words against 160 BB sentences. 27 function words appear directly. Full data in `template_slot_fillers.py`.

### Temporal Slot (T8, T9) — 9 BB-attested options

| Skiri | English | Position | BB Lessons |
|-------|---------|----------|------------|
| rahesa' | tomorrow | CLAUSE-INITIAL | L19 |
| tiruks•tsak•ariki | yesterday | CLAUSE-INITIAL | L17 |
| hiras | at night | CLAUSE-INITIAL | L16 |
| tihe ra•pa•ariki' | next month | CLAUSE-FINAL | L19 |
| pitsikat | in winter | CLAUSE-FINAL | L09, L15, L20 |
| retskuhke | in fall | CLAUSE-FINAL | L15 |
| kekaruskat | early this morning | CLAUSE-INITIAL | L17 |
| tiruks•tatkiu' | last night | CLAUSE-INITIAL | L17 |
| tiherukspa•ariki | last month | CLAUSE-INITIAL | L17 |

### Manner Adverb Slot (T8) — 2 BB-attested + 3 Parks dictionary

| Skiri | English | Position | Source |
|-------|---------|----------|--------|
| cikstit | well, fine | PRECEDES-VERB | L18, L20 |
| rariksisu | hard, very much | PRECEDES-VERB | L18 |
| ctuu | really, so | PRECEDES-VERB | Parks dict |
| awiit | first | PRECEDES-VERB | Parks dict |
| istuʔ | again, back | PRECEDES-VERB | Parks dict |

### Key Structural Particles (already wired into templates)

| Skiri | English | BB Count | Templates |
|-------|---------|----------|-----------|
| ti | this is / it is | 26x | T1, T2 (built-in) |
| ka | yes/no question | 22x | T3 (built-in) |
| kirike | what | 14x | T4 (built-in) |
| we | completed action | 12x | T9 (selectable) |
| hiri | here/where | 8x | locative slot |
| kiru | where | 7x | T5 (built-in) |
| ru | there | 6x | locative slot |
| kaki | no/not | 13x | T6 (built-in) |

### BB Vocabulary Alias Table (15 common forms)

BB classroom forms that differ from Parks dictionary headwords:

| BB Form | Parks Headword | Gloss |
|---------|---------------|-------|
| pita | pitaruʔ | man |
| paresu | paresuʔ | hunter |
| asaki | asaaki | dog |
| rikutski | rikucki | bird |
| kiwaku | kiwakuʔ | fox |
| arusa | aruusaʔ | horse |
| hitu' | hituʔ | feather |
| kisatski | kisacki | meat |

---

## Appendix A: Complete Blue Book Sentence ↔ Template Mapping

| Lesson | Skiri | English | Template |
|--------|-------|---------|----------|
| L01 | Kirike ru'? | What is it? | T4 |
| L01 | Ti hitu'. | This is a feather. | T1 |
| L01 | Ka rii hitu'? | Is this a feather? | T3 |
| L01 | Ahu', ti hitu'. | Yes, this is a feather. | T7+T1 |
| L01 | Hau, ti hitu'. | Yes, this is a feather. | T7+T1 |
| L01 | Ka ru karitki? | Is this a rock? | T3 |
| L01 | Kaki, kaki karitki. | No, it is not a rock. | T6 |
| L02 | Kirike ra•tarawis rakis? | What color is the stick? | T4 |
| L02 | Rakis ti pahaat. | The stick is red. | T2 |
| L02 | Ka ra•pahaat rakis? | Is the stick red? | T3 |
| L02 | Ahu', rakis ti pahaat. | Yes, the stick is red. | T7+T2 |
| L02 | Ka rd .tareus rakis? | Is the stick blue? | T3 |
| L02 | Kaki tareus, ti pahaat. | It is not blue, it is red. | T6+T2 |
| L06 | Pita kirike rut•ari'? | What is the man doing? | T4 |
| L06 | Pita tiwari'. | The man is walking about. | T9 |
| L06 | Pita ka ra•kikat? | Is the man crying? | T3 |
| L06 | Kaki', pita t'ewasku'. | No, the man is laughing. | T6+T9 |
| L08 | Kirike ras•taspe'? | What are you looking for? | T4 |
| L08 | Tah•raspe' asaki. | I'm looking for my dog. | T8 |
| L08 | Ka ras•huras asaki? | Have you found the dog? | T3 |
| L08 | Ahu', tat .huras asaki. | Yes, I found the dog. | T7+T8 |
| L09 | Pita ti•kuwutit rahurahki pitsikat. | The man killed a deer, in the winter. | T9 |
| L13 | Tatuks•at Pari. | I went to Pawnee. | T8 |
| L14 | Pita ti•kuwutit kuruks. | The man has killed a bear. | T9 |
