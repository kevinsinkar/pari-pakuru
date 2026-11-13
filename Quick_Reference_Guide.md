# Quick reference

A cheat sheet for working in this repository. Every example word and every
count below was read from `skiri_pawnee.db` on 2026-11-13.

## How a dictionary entry is laid out

Parks prints each entry in a fixed order. The same fields are in the JSON and
the database.

| Field | How Parks prints it | Example (entry `SK-kuutik-p453-4018`) |
|---|---|---|
| Headword | bold | *kuutik* |
| Phonetic form | `[...]` | [•kuu-tɪ{k/t}•] |
| Preverb | `(ut...)`, `(uur...)`, `(ir...)` before the class | none here; *awiʔuusik* has `(uur...)` |
| Grammatical class | small capitals | VT |
| Verb class | in parentheses after the class | (1) |
| Glosses | numbered | 1. kill, slay. 2. whip, beat, beat up. |
| Etymology | `<...>` | `<kuuʔat+ik, cause to die>` |
| Five verb forms | numbered 1 to 5 | see below |
| Examples | after a bullet | *tikawuutit* 'he killed them.' |

A noun entry, `SK-paatuq-p107-2038`: *paatuʔ* [paá-tʊʔ], N, 'blood; gore.',
etymology `<paat+uʔ, blood + NOM>`.

### The five verb forms

| # | What it is | *kuutik* 'kill' |
|---|---|---|
| 1 | 1st person singular, indicative, perfective | *tatkuutit* |
| 2 | 3rd person singular, indicative, perfective | *tikuutit* |
| 3 | 3rd person singular, indicative, imperfective | *tikuutikuʔ* |
| 4 | 3rd person singular, absolutive, subordinate perfective | *iriirakuutika* |
| 5 | 3rd person singular, indicative, perfective intentive | *tikuutiksta* |

### Reading an etymology

`+` joins pieces. A dot joins the parts of a compound stem that has its own
dictionary entry. A trailing hyphen marks a bound form. Parentheses mark an
optional sound. CAPITALS are grammatical labels (NOM, PREV, PL, CAUS ...). A
piece "glossed" by its own shape is one Parks gives no meaning for. The
literal translation after the comma is **not** in the same order as the pieces.

## Classes

| Class | Meaning | Entries |
|---|---|---|
| N | noun | 1,634 |
| VT | transitive verb | 777 |
| VI | intransitive verb | 711 |
| VD | descriptive verb | 444 |
| LOC | locative | 147 |
| ADV | adverb | 141 |
| VP | patient (passive) verb | 129 |
| VL | locative verb | 116 |
| NUM, INTERJ, N-DEP, N-KIN, VR, ADJ, CONJ, DEM, PRON ... | | under 30 each |

Some entries carry two classes, such as `VT, VR`. Two entries with the same
headword and different classes are two words, not duplicates.

Verb classes, by number of entries: (1) 589, (4) 548, (3) 253, (1-i) 74,
(2-i) 63, (2) 57, (1-a) 50, (u) 23, (wi) 23. Descriptive and locative verbs
usually have no printed class.

## Sounds and spellings

Nine consonants: p, t, k, c, s, h, r, w, ʔ. Three vowels, each short or long:
a/aa, i/ii, u/uu.

Three spellings of the same word are stored side by side:

| | Example | Where it comes from |
|---|---|---|
| Parks's headword | *paatuʔ* | the dictionary, unchanged |
| Parks's phonetic form (IPA) | [paá-tʊʔ] | the dictionary, unchanged. Never generated |
| Learner spelling (`normalized_form`) | `pâtu'` | rule: aa→â, ii→î, uu→û, ʔ→', and c→č where it is said "ch" |
| Respelling (`simplified_pronunciation`) | `PAH-too'` | derived from the IPA; CAPITALS = the syllable Parks marks as accented |

### Respelling key

| Pawnee | Respelled | Example |
|---|---|---|
| a | uh | *rakis* [rà-kɪs] `DUH-kihs` 'wood' |
| aa | ah | *paatuʔ* [paá-tʊʔ] `PAH-too'` 'blood' |
| i | ih | *kiri* [kí-rɪ] `KIH-dih` 'domestic cat' |
| ii | ee | *kariikuʔ* [kə-rií-kʊʔ] `kuh-DEE-koo'` 'liver' |
| u, uu | oo | *kuruks* [kʊ́-rʊks] `KOO-dooks` 'bear' |
| r | d (a light tap) | *kiri* `KIH-dih`, *rakis* `DUH-kihs` |
| c | ch before a vowel, ts elsewhere | *cikic* [čí-kɪts] `CHIH-kihts` 'itch; itchy' |
| ʔ | ' | *awiʔuʔ* [à-wi-ʔuʔ] `UH-wih-'oo'` 'picture, image' |
| optional sound | in parentheses | *kuutik* [•kuu-tɪ{k/t}•] `koo-tih(k/t)` |

A respelling with no capitals means Parks marks no accent on that form (he
cites verb stems without one). It does not mean the word has no accent.

### Accent marks in the IPA

Parks: "Stress is not phonemic in Skiri and hence is not marked on words.
(Phonetic forms in entries do, however, have accented syllables marked.)"
(Sounds and Alphabet, p. 15.) So the marks show the accented syllable; they are
not a pitch that changes meaning.

| On | Parks prints | Stored as | Example |
|---|---|---|---|
| a long vowel | acute on its second half: aá, ií, uú | the same | *paatuʔ* [paá-tʊʔ]; *askuhuukita* [əs-kʊ-huú-kɪ-tə] |
| a short u | ʊ́ | the same | *kuruks* [kʊ́-rʊks] |
| a short a | ə́ | **à** (not his symbol) | *rakis* [rà-kɪs]; he prints [rə́-kɪs] |
| a short i | what looks like ɪ́ (to be confirmed) | **í** | *cikic* [čí-kɪts] |

1,800 entries carry an accent mark. The last two rows are an open item: the
accent is stored, but the vowel symbol under it is not the one Parks prints
(certain for a; for i the print has still to be compared closely). A
grave accent (ì, ù, à as its own mark) occurs in five forms; Parks does not
explain it.

The Blue Book uses its own practical spelling (ts for c, ' for ʔ, a dot `•`
between the parts of a word). Blue Book forms are quoted as printed.

## Database tables

`skiri_pawnee.db` (SQLite, not in git). Row counts on 2026-11-13.

| Table | Rows | Contents |
|---|---|---|
| `lexical_entries` | 4,337 | one row per headword; 4,244 from Parks, 93 Blue Book only |
| `glosses` | 5,504 | numbered senses |
| `paradigmatic_forms` | 9,559 | the five forms, for 2,239 verbs |
| `examples` | 2,635 | example sentences (2,547 Parks, 88 Blue Book) |
| `etymology` | 3,825 | Parks's printed etymology; `constituent_elements` is a derived parse whose per-piece glosses are unreliable |
| `cognates` | 608 | related forms in Arikara, Kitsai, Wichita ... |
| `english_index` | 8,067 | English-to-Skiri lookup rows; 5,130 linked to an entry |
| `cross_references` | 4,585 | "see also" links |
| `semantic_tags` | 4,500 | 19 topic tags on 3,316 entries |
| `blue_book_attestations` | 1,026 | Blue Book vocabulary items; 581 linked to an entry |
| `lessons` | 20 | Blue Book lessons |
| `verb_paradigms` | 770 | Parks Appendix 1: 7 verbs × 10 modes × 11 persons |
| `irregular_verb_roots` | 9 | Parks Appendix 2 |
| `morpheme_abbreviations` | 164 | Parks's abbreviation list |
| `morpheme_inventory` | 37 | inflectional prefixes and suffixes with slot numbers |
| `verb_template_slots` | 27 | the verb template |
| `sound_change_rules` | 24 | Parks chapter 3 |
| `noun_stems`, `kinship_paradigms`, `possession_examples` | 49, 14, 20 | noun possession |
| `function_words`, `bb_function_words` | 418, 63 | particles, demonstratives, conjunctions |
| `bb_gap_triage` | 516 | Blue Book items with no dictionary match, classified |
| `community_feedback` | 2 | flags and confirmations from the web app |
| `srs_cards`, `srs_reviews` | 0, 0 | spaced-repetition state |

Useful columns on `lexical_entries`: `blue_book_attested` (181 entries),
`source` (`blue_book` for the 93 Blue Book-only words), `form2_confidence`,
`bb_variant_of`, `page_number`.

**`page_number` mixes two conventions.** Values up to 181 are the number of the
split PDF file; larger values are the printed book page (book page = file
number + 348). The `page_NNN` in an entry id is not a reliable page either:
the 28 `kaa…` entries with `-p2-` ids are on book page 419.

### Confidence on predicted verb forms

`form2_confidence` (0 to 1) says how far to trust a *predicted* form 2. It
weighs how accurate the predictor is for that verb class and preverb (50%),
whether class and preverb are printed or inferred (20%), how complex the
headword notation is (15%) and how many verbs the class has (15%).
High (0.75 and up): 2,187 verbs. Medium: 30. Low: 22.

## Verb template

```
proclitics (slots 1-8) → inner prefixes (10-26) → STEM → suffixes (27-30)
```

| Slots | Positions |
|---|---|
| 1-8 | quotative, dubitative, inferential, evidential, dual, indefinite, reflexive, negative |
| 10-13 | mode, agent, inclusive, agent plural / possessor / preverb |
| 15-20 | patient, infinitive mode, physical possession, benefactive / preverb, resultative, aorist |
| 22-26 | plural markers, incorporated noun, stem |
| 27-30 | aspect, subordination, intentive, subordinate intentive |

## Web app routes

| Route | Page |
|---|---|
| `/` | home, word of the day |
| `/search`, `/search/partial`, `/api/search` | search (page, live results, JSON) |
| `/entry/<id>` | full entry |
| `/browse`, `/browse/tag/<tag>`, `/browse/class/<class>` | browse |
| `/lessons`, `/lessons/<n>` | Blue Book lessons |
| `/flashcards`, `/flashcards/<week>` | weekly flashcards |
| `/study`, `/api/srs/review` | spaced-repetition study |
| `/sentence-builder`, `/api/assemble`, `/api/slot-options`, `/api/verbs`, `/api/bb_verb_forms` | sentence builder |
| `/api/possession/<headword>` | possession forms for a noun |
| `/guide` | pronunciation guide |
| `/dashboard` | data-quality dashboard |
| `/about` | about |
| `/api/feedback`, `/admin/feedback`, `/admin/feedback/<id>/review` | community feedback and its review queue |
| `/preferences` | spelling preference |

## Commands used most

```bash
.venv/Scripts/python -m web.app                               # run the web app
.venv/Scripts/python scripts/build_static_site.py             # rebuild docs/
.venv/Scripts/python scripts/morphology_v2/run.py --all       # word-construction analysis
.venv/Scripts/python scripts/sound_changes.py --test          # sound-change rules
.venv/Scripts/python scripts/stem_extractor.py --validate     # form 2 prediction
.venv/Scripts/python DB/query_api.py --db skiri_pawnee.db --english "bear"
```

The full list, in pipeline order, is in [scripts/README.md](scripts/README.md).
