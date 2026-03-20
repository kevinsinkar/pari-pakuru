# Quick Reference Guide: Pari Pakuru'

## Dictionary Entry Structure

Each Skiri Pawnee dictionary entry contains:

| Field | Format | Example |
|-------|--------|---------|
| **Headword** | Boldface lemma | **kawPuktawuh** |
| **Phonetic form** | `[...]` brackets | `[-wii•-t,u®(h)]` |
| **Preverb** | `(prefix...)` | `(uur...)` |
| **Grammatical class** | Small caps | VI, VT, N |
| **Verb class** | `(N)` after class | `(4)` |
| **Additional forms** | `{...}` braces | `{pl. obj., raawi-}` |
| **Glosses** | Numbered definitions | 1. sit down 2. rest |
| **Etymology** | `<...>` angle brackets | `<uur+awi+uusik>` |
| **Paradigmatic forms** | Numbered 1-5 | Standard verb inflections |
| **Examples** | Bulleted `•` | Example sentences with translations |

## Grammatical Classes

**Verbs:**
- VI = intransitive, VT = transitive, VD = descriptive
- VL = locative, VP = patientive/passive, VR = reflexive

**Verb Classes:** (1), (1-a), (1-i), (2), (2-i), (3), (4), (4-i), (u), (wi)

**Other:** N = noun, ADJ = adjective, ADV = adverb, PRON = pronoun, NUM = numeral

## Five Standard Paradigmatic Forms (Verbs)

1. **Form 1:** 1st person singular, indicative, perfective
2. **Form 2:** 3rd person singular, indicative, perfective
3. **Form 3:** 3rd person singular, indicative, imperfective
4. **Form 4:** 3rd person singular, absolutive, subordinate perfective
5. **Form 5:** 3rd person singular, indicative, perfective intentive

## Sound System

**Consonants:** p, t, k, c, s, h, r, w, ʔ

| Letter | Sound |
|--------|-------|
| c | *ts* before consonants, *ch* before vowels |
| r | tap, as in Spanish *pero* |
| ʔ | glottal stop, as in *uh-oh* |

**Vowels:** a/aa, i/ii, u/uu (short/long pairs)

## Simplified Pronunciation Key

| Symbol | Sounds like | Parks IPA |
|--------|-------------|-----------|
| ah | "u" in *putt* | a |
| ee | "ee" in *see* | i, ii |
| oo | "oo" in *boot* | u, uu |
| ch | "ch" in *church* | c (before vowels) |
| ts | "ts" in *cats* | c (before consonants) |
| ' | catch in *uh-oh* | ʔ |

**Pitch accent:** UPPERCASE syllables = high pitch (e.g., **KAH**-'uhs). Not all entries have pitch marked.

## Confidence Scoring

Entries carry a weighted confidence score based on four factors:
- Attestation (Parks Dictionary, Blue Book, or both)
- Data completeness (pronunciation, etymology, examples present)
- Source agreement (Parks and Blue Book forms align)
- Community verification (flags and confirmations)

Badges: high confidence, medium, low, unscored.

## Database Tables

| Table | Contents |
|-------|----------|
| `lexical_entries` | 4,273 headwords with all core fields |
| `glosses` | English definitions linked to entries |
| `paradigmatic_forms` | Verb inflection forms (1-5) |
| `examples` | Example sentences and translations |
| `etymology` | Morpheme breakdowns |
| `semantic_tags` | 7,097 categorization tags |
| `sound_change_rules` | 24 phonological rules |
| `verb_paradigms` | 770 conjugation forms (7 verbs × 10 modes × 11 persons) |
| `morpheme_inventory` | 37 morphemes with slot positions |
| `noun_stems` | 1,633 noun possession forms |
| `kinship_paradigms` | 11 kinship term paradigms |
| `community_feedback` | User flags and confirmations |
| `blue_book_attestations` | Blue Book cross-verification data |

## Web App Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage with word-of-the-day and stats |
| `/search` | Dictionary search (bidirectional) |
| `/entry/<id>` | Full entry detail with pronunciation, etymology |
| `/flashcards` | Weekly flashcard categories |
| `/flashcards/study/<cat>` | Flashcard study session |
| `/guide` | Pronunciation and syllable guide |
| `/dashboard` | Study overview and dictionary statistics |
| `/sentences` | Sentence builder |
| `/about` | About page |
| `/api/search` | JSON API for external consumers |

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/sound_changes.py` | 24 sound change rules engine (Parks Ch. 3) |
| `scripts/morpheme_inventory.py` | Verb conjugation with `--validate` flag |
| `scripts/stem_extractor.py` | Extract stems from dictionary headwords |
| `scripts/tag_entries.py` | Semantic tagging via Gemini API |
| `scripts/blue_book_verify.py` | Cross-verify against Blue Book |
| `scripts/noun_possession.py` | Catalog noun possession types |
| `scripts/sentence_templates.py` | Generate sentence builder templates |
| `scripts/audit_entries.py` | Gemini-powered data audit |
| `scripts/bb_gap_triage.py` | Classify Blue Book gaps |

## Verb Template Slot Structure

```
Proclitics (slots 1-8) → Inner Prefixes (slots 9-26) → Noun → STEM → Suffixes (slots 27-30)
```

Key slots:
- **Slot 10:** Modal prefix (IND ta-/ti-, NEG kaaka-, ASSR rii-, CONT i-/ri-, POT kuus-..i-, ABS ra-, SUBJ aa-/ii-, INF ra-..ku-)
- **Slot 11:** Agent prefix (1.A t-, 2.A s-, 3.A Ø)
- **Suffixes:** Subordinate class markers, imperfective -huʔ/-hu
