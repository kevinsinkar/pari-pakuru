# Skiri Pawnee Dictionary Digitization Project

**Transforming a printed Skiri Pawnee dictionary into a structured, searchable digital database for language preservation and revitalization.**

---

## About

This project digitizes and structures the contents of *A Dictionary of Skiri Pawnee* (Parks & Pratt, 2008) — one of the most comprehensive linguistic references for the Skiri dialect of the Pawnee language (Caddoan family). The goal is to convert the dictionary's ~4,200 Skiri-to-English entries into a clean, normalized JSON database suitable for building flashcard apps, search tools, and language learning resources.

Skiri Pawnee is critically endangered. Making this dictionary data machine-readable and accessible is a step toward supporting learners, educators, and community members working to keep the language alive.

## What's in the Database

Each dictionary entry is structured with:

| Field | Description |
|-------|-------------|
| **Headword** | The Skiri Pawnee lemma in standard orthography |
| **Preverb** | Required prefix notation (e.g., `uur...`, `ut...`) |
| **Phonetic Form** | Dictionary's bracketed pronunciation with syllable breaks |
| **Simplified Pronunciation** | Learner-friendly English approximation |
| **Grammatical Class** | Part of speech (VI, VT, N, VD, VP, ADV, etc.) |
| **Verb Class** | Inflectional class for verbs (1, 1-a, 2, 3, 4, etc.) |
| **Additional Forms** | Plural, distributive, combining forms |
| **Glosses** | English definitions (numbered for multiple senses) |
| **Etymology** | Morpheme breakdown + literal translation |
| **Paradigmatic Forms** | Up to 5 standard inflected forms per verb |
| **Examples** | Illustrative phrases and sentences with translations |

## Project Pipeline

```
PDF Scans ──► Initial Extraction ──► Verification ──► Normalized Database ──► Applications
 (source)      (Gemini API)        (Claude API)       (JSON/SQLite)       (flashcards, etc.)
```

### 1. Source Material
The printed dictionary was split into individual page PDFs for manageable processing. Supporting sections (abbreviations, sound key, grammatical overview, dictionary organization) serve as reference material for extraction accuracy.

### 2. Initial Extraction
Entries were extracted using the Gemini API, processing pages in overlapping pairs (page N + N+1) to handle entries that span page boundaries.

### 3. Verification & Normalization
A Claude API pipeline verifies every extracted field against the source PDFs, correcting errors and normalizing inconsistencies from the initial extraction:
- Standardizing grammatical class abbreviations
- Normalizing etymology field structures
- Unifying example sentence formats
- Fixing glottal stop encoding (`ʔ` vs `?` vs `™`)
- Mapping PDF font-specific characters to proper linguistic symbols

### 4. Target Applications
- **Flashcard decks** (Anki-compatible CSV export)
- **Searchable dictionary app**
- **Language learning tools** with pronunciation guides
- **Linguistic research database**

## Skiri Pawnee Sound System

The language has a small phonemic inventory — 9 consonants and 3 vowels (each with short/long variants):

**Consonants:** p, t, k, c, s, h, r, w, ʔ

| Letter | Sound | Example |
|--------|-------|---------|
| p | as in English *spot* | **piíta** 'man' |
| t | as in English *stop* | **taátuʔ** 'plant' |
| k | as in English *skate* | **kariíkuʔ** 'liver' |
| c | *ts* (before consonants) / *ch* (before vowels) | **cíkic** 'itchy' |
| s | as in English *sit* | **sát** 'walnut' |
| r | tap, as in Spanish *pero* | **rákis** 'wood' |
| h | as in English *hit* | **hiítuʔ** 'feather' |
| w | as in English *wall* | **áwiʔuʔ** 'mage' |
| ʔ | glottal stop, as in *uh-oh* | **paátuʔ** 'blood' |

**Vowels:** a/aa, i/ii, u/uu (short a ≈ English *putt*, long aa ≈ *father*)

## Repository Structure [subject to change]

```
skiri-dictionary/
├── README.md
├── data/
│   ├── skiri_dictionary.json          # Full extracted database (4,242 entries)
│   ├── verified/                      # Page-by-page verification results
│   └── exports/                       # CSV, SQLite, Anki deck exports
├── reference/
│   ├── 01-Abbreviations_and_Sound_Key.pdf
│   ├── 02-Sounds_and_Alphabet.pdf
│   ├── 03-Major_Sound_Changes.pdf
│   ├── 04-Grammatical_Overview.pdf
│   ├── 05-Organization_of_the_Dictionary.pdf
│   ├── Skiri-to-English_JSON_Structure.txt
│   ├── English-to-Skiri_JSON_Structure.txt
│   └── Parsing_and_Extraction_Instructions.txt
├── scripts/
│   ├── verify_skiri.py                # Claude API verification pipeline
│   └── export_flashcards.py           # Export to Anki/CSV formats
├── prompts/
│   └── skiri_verification_prompt.md   # Verification prompt for Claude
└── pages/                             # Individual page PDFs (not tracked in git)
    ├── page_001.pdf
    ├── page_002.pdf
    └── ...
```

## Contributing

This is a language preservation effort. Contributions are welcome, especially from:
- **Pawnee community members and language learners** — your knowledge is invaluable for catching errors
- **Linguists** — help improve phonetic transcriptions and grammatical annotations
- **Developers** — build tools that make this data useful (apps, flashcards, search interfaces)

If you find errors in the data, please open an issue with the headword and page number.

## References

- Parks, Douglas R., and Lula Nora Pratt. *A Dictionary of Skiri Pawnee.* Lincoln: University of Nebraska Press, 2008.

## License

The structured data in this repository is intended for educational and language revitalization purposes. The original dictionary content is the intellectual property of its authors and publisher. Please respect the cultural significance of this language to the Pawnee Nation.
