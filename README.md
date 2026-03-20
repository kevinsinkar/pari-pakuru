# Pari Pakuru' — Skiri Pawnee Dictionary & Language Tools

**A digital dictionary, learning platform, and linguistic research tool for the Skiri Pawnee language, built to support language preservation and revitalization.**

---

## About

Pari Pakuru' digitizes and structures the contents of *A Dictionary of Skiri Pawnee* (Parks & Pratt, 2008) — one of the most comprehensive linguistic references for the Skiri dialect of the Pawnee language (Caddoan family). The project has grown from a dictionary digitization effort into a full language learning platform with over 4,200 headwords, a web interface, flashcard study system, sentence builder, and community feedback tools.

Skiri Pawnee is critically endangered. Making this dictionary data machine-readable and accessible is a step toward supporting learners, educators, and community members working to keep the language alive.

## Features

### Search & Dictionary
- Bidirectional search (English → Skiri and Skiri → English) with smart ranking
- Multiple pronunciation displays: IPA phonetic, simplified respelling with pitch accent highlighting
- Spelling preference toggle: Parks linguistic orthography or simplified spelling
- Full verb conjugation tables for documented paradigms
- Semantic categorization and tag browsing
- Blue Book attestation badges and confidence scores for data quality
- Etymology, morpheme breakdowns, and cognate cross-references

### Learning Tools
- Weekly flashcard study system with 21 categories and curated beginner vocabulary
- Template-based sentence builder for practicing Skiri Pawnee word order
- Interactive pronunciation guide with respelling symbols and pitch accent legend
- Suggested learning path for new learners
- Learner / Expert mode toggle to control detail level
- Dashboard with study overview and dictionary statistics

### Community & Data Quality
- Community feedback: flag uncertain entries or confirm correct ones, with admin review
- Confidence scoring: each entry carries a weighted score based on attestation, completeness, and source agreement
- Blue Book cross-verification against teaching materials

### Linguistic Research
- Sound change rule engine (24 rules from Parks Ch. 3)
- Morpheme inventory and verb template slot system
- Noun possession cataloging with kinship paradigms
- Stem extraction and morphophonological analysis

## Data Sources

- **A Dictionary of Skiri Pawnee** by Douglas R. Parks — the primary linguistic reference, containing over 4,200 headwords with phonetic transcriptions, grammatical classifications, etymologies, paradigmatic verb forms, and example sentences.
- **Pari Pakuru' (Blue Book)** — a Skiri Pawnee language textbook used in community language classes, providing attested vocabulary and usage in pedagogical contexts.

## What's in the Database

The SQLite database (`skiri_pawnee.db`) contains 4,273 lexical entries with:

| Field | Description |
|-------|-------------|
| **Headword** | The Skiri Pawnee lemma in standard orthography |
| **Phonetic Form** | Dictionary's bracketed pronunciation |
| **Simplified Pronunciation** | Learner-friendly English respelling with pitch accent |
| **Grammatical Class** | Part of speech (VI, VT, N, VD, VP, ADV, etc.) |
| **Verb Class** | Inflectional class for verbs (1, 1-a, 2, 3, 4, etc.) |
| **Glosses** | English definitions (numbered for multiple senses) |
| **Etymology** | Morpheme breakdown + literal translation |
| **Paradigmatic Forms** | Up to 5 standard inflected forms per verb |
| **Examples** | Illustrative phrases and sentences with translations |
| **Semantic Tags** | 7,097 categorization tags across entries |
| **Confidence Score** | 4-factor weighted quality score |
| **Blue Book Attested** | Whether the term appears in teaching materials |

Additional tables: `sound_change_rules`, `verb_paradigms` (770 forms), `morpheme_inventory`, `community_feedback`, `noun_stems`, `kinship_paradigms`, and full-text search indexes.

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

## Repository Structure

```
pari-pakuru/
├── web/                        # Flask web application
│   ├── app.py                  #   Main app (routes, filters, pitch display)
│   ├── db.py                   #   Database access layer
│   ├── search.py               #   Search logic
│   ├── search_ranking.py       #   Result ranking (exact match, BB boost)
│   ├── flashcards.py           #   Flashcard categories and study system
│   ├── static/                 #   CSS, JS assets
│   └── templates/              #   Jinja2 HTML templates
├── scripts/                    # Data processing and analysis scripts
│   ├── sound_changes.py        #   24 sound change rules engine
│   ├── morpheme_inventory.py   #   Verb conjugation and morpheme system
│   ├── stem_extractor.py       #   Dictionary stem extraction
│   ├── tag_entries.py          #   Semantic tagging
│   ├── blue_book_verify.py     #   Blue Book cross-verification
│   ├── noun_possession.py      #   Noun possession cataloging
│   ├── sentence_templates.py   #   Sentence builder templates
│   └── ...                     #   Additional processing scripts
├── Dictionary Data/            # Source JSON dictionaries
│   ├── skiri_to_english_respelled.json   # 4,273 S2E entries
│   └── english_to_skiri_linked.json      # 6,414 E2S entries
├── extracted_data/             # Structured extractions (appendices, grammar)
├── reports/                    # Phase reports and analysis outputs
├── pari pakuru/                # Blue Book source material
├── skiri_pawnee.db             # SQLite database (production)
├── wsgi.py                     # WSGI entry point for deployment
└── requirements.txt            # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.10+
- Dependencies: `pip install -r requirements.txt`

### Running the Web App
```bash
python -m web.app
```
The app runs at `http://localhost:5000` by default.

### Running Scripts
Scripts use argparse with sensible defaults:
```bash
python -m scripts.sound_changes --help
python -m scripts.morpheme_inventory --validate
```

## Contributing

This is a language preservation effort. Contributions are welcome, especially from:
- **Pawnee community members and language learners** — your knowledge is invaluable for catching errors
- **Linguists** — help improve phonetic transcriptions and grammatical annotations
- **Developers** — build tools that make this data useful

If you find errors in the data, please open an issue with the headword and page number, or use the in-app feedback system to flag entries directly.

## References

- Parks, Douglas R., and Lula Nora Pratt. *A Dictionary of Skiri Pawnee.* Lincoln: University of Nebraska Press, 2008.

## License

The structured data in this repository is intended for educational and language revitalization purposes. The original dictionary content is the intellectual property of its authors and publisher. Please respect the cultural significance of this language to the Pawnee Nation.
