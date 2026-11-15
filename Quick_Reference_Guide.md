# Quick reference

A cheat sheet for working in this repository. Every example word and every
count below was read from `skiri_pawnee.db` on 2026-11-13, after the
source-fidelity audit's fixes were applied.

## How a dictionary entry is laid out

Parks prints each entry in a fixed order. The same fields are in the JSON and
the database.

| Field | How Parks prints it | Example (entry `SK-kuutik-p453-4018`) |
|---|---|---|
| Headword | bold | *kuutik* |
| Phonetic form | `[...]` | [–kuu·tɪ{k/t}–] |
| Preverb | `(ut...)`, `(uur...)`, `(ir...)` before the class | none here; *awiʔuusik* has `(uur...)` |
| Grammatical class | small capitals | VT |
| Verb class | in parentheses after the class | (1) |
| Glosses | numbered | 1. kill, slay. 2. whip, beat, beat up. |
| Etymology | `<...>` | `<kuuʔat+ik, cause to die>` |
| Five verb forms | numbered 1 to 5 | see below |
| Examples | after a bullet | *tikawuutit* 'he killed them.' |

A noun entry, `SK-paatuq-p107-2038`: *paatuʔ* [paá·tʊʔ], N, 'blood; gore.',
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
| VI | intransitive verb | 712 |
| VD | descriptive verb | 444 |
| LOC | locative | 147 |
| ADV | adverb | 141 |
| VP | patient (passive) verb | 129 |
| VL | locative verb | 116 |
| NUM, INTERJ, N-DEP, N-KIN, VR, ADJ, CONJ, DEM, PRON ... | | under 30 each |

Some entries carry two classes, such as `VT, VR`. Two entries with the same
headword and different classes are two words, not duplicates.

Verb classes, by number of entries: (1) 589, (4) 548, (3) 253, (1-i) 75,
(2-i) 63, (2) 57, (1-a) 50, (u) 23, (wi) 23. Descriptive and locative verbs
usually have no printed class.

## Sounds and spellings

Nine consonants: p, t, k, c, s, h, r, w, ʔ. Three vowels, each short or long:
a/aa, i/ii, u/uu.

Three spellings of the same word are stored side by side:

| | Example | Where it comes from |
|---|---|---|
| Parks's headword | *paatuʔ* | the dictionary, unchanged |
| Parks's phonetic form (IPA) | [paá·tʊʔ] | the dictionary, in his own symbols. Never generated |
| Learner spelling (`normalized_form`) | `pâtu'` | rule: aa→â, ii→î, uu→û, ʔ→', and c→č where the phonetic form has [č] |
| Respelling (`simplified_pronunciation`) | `PAH-too'` | derived from the IPA; CAPITALS = the syllable Parks marks as accented |

The 93 Blue Book-only words have no phonetic form: the book gives none, and
the ones the database used to hold had been made from the spelling. Their
respelling is made from the spelling and shown with ≈.

`python scripts/check_simplified_forms.py` makes the learner spelling and the
respelling again for every Parks entry and compares them with what is stored.
On 2026-11-13: no difference in 4,244 entries.

### Respelling key

| Pawnee | Respelled | Example |
|---|---|---|
| a | uh | *rakis* [rə́·kɪs] `DUH-kihs` 'wood' |
| aa | ah | *paatuʔ* [paá·tʊʔ] `PAH-too'` 'blood' |
| i | ih | *kiri* [kɪ́·rɪ] `KIH-dih` 'domestic cat' |
| ii | ee | *kariikuʔ* [kə·rií·kʊʔ] `kuh-DEE-koo'` 'liver' |
| u, uu | oo | *kuruks* [kʊ́·rʊks] `KOO-dooks` 'bear' |
| r | d (a light tap) | *kiri* `KIH-dih`, *rakis* `DUH-kihs` |
| c | ch before a vowel, ts elsewhere | *cikic* [čɪ́·kɪts] `CHIH-kihts` 'itch; itchy' |
| ʔ | ' | *awiʔuʔ* [ə́·wi·ʔuʔ] `UH-wih-'oo'` 'picture, image' |
| optional sound | in parentheses | *kuutik* [–kuu·tɪ{k/t}–] `koo-tih(k/t)` |

A respelling with no capitals means Parks marks no accent on that form (he
cites verb stems without one). It does not mean the word has no accent.

**Where the respelling is coarser than the IPA.** Parks writes a short i or u
in two ways: lax [ɪ], [ʊ] in most places, tense [i], [u] in others (before a
glottal stop, for one: *awiʔuʔ* [ə́·wi·ʔuʔ]). The respelling writes both as
`ih` and `oo`, as his sound key does for the spelling. 589 entries have such a
vowel. Whether learners should see the difference is a teaching decision that
has not been made; the IPA keeps it either way.

### Parks's phonetic notation

Since 2026-11-13 the database stores the phonetic forms in the symbols Parks
prints, character for character, read from the typesetter's text of the PDF
with a table verified against the printed glyphs
(`scripts/source_audit/chartable.py`).

| Symbol | Meaning | Example |
|---|---|---|
| `·` | syllable boundary | [kʊ́·rʊks] |
| `–` at an edge | the form is bound: something must come before or after | *kuutik* [–kuu·tɪ{k/t}–] |
| ə ɪ ʊ | the short vowels a, i, u in their usual (lax) quality | *rakis* [rə́·kɪs] |
| i u (single) | a short vowel with tense quality | *awiʔuʔ* [ə́·wi·ʔuʔ] |
| aa ii uu | long vowels | *paatuʔ* [paá·tʊʔ] |
| č | the "ch" sound of c | *cikic* [čɪ́·kɪts] |
| `{k/t}` | the final consonant alternates | *kuutik* |

Before that date the database wrote a hyphen for the syllable dot, a bullet
for the edge dash, à for ə́ and í for ɪ́. Older reports and frozen files from
before 2026-11-13 still show that working notation. `scripts/ipa_notation.py`
converts Parks's notation to it for the respelling code, nowhere else.

### Accent marks in the IPA

Parks: "Stress is not phonemic in Skiri and hence is not marked on words.
(Phonetic forms in entries do, however, have accented syllables marked.)"
(Sounds and Alphabet, p. 15.) So the marks show the accented syllable; they are
not a pitch that changes meaning.

| On | Parks prints, and the database stores | Example |
|---|---|---|
| a long vowel | acute on its second half: aá, ií, uú | *paatuʔ* [paá·tʊʔ]; *askuhuukita* [əs·kʊ·huú·kɪ·tə] |
| a short u | ʊ́ | *kuruks* [kʊ́·rʊks] |
| a short a | ə́ | *rakis* [rə́·kɪs] |
| a short i | ɪ́ | *cikic* [čɪ́·kɪts] |

2,218 of the 4,244 Parks entries carry an accent mark. A grave accent (a
second, weaker mark, as in *aacikicii* [aá·čɪ·kɪ·čiì]) occurs in ten entries;
Parks does not explain it.

The Blue Book uses its own practical spelling (ts for c, ' for ʔ, a dot `•`
between the parts of a word) and prints an acute accent on the stressed
vowel. Blue Book forms are quoted as printed; the accents, lost when the book
was read by OCR, were restored from the scan on 2026-11-13.

## Database tables

`skiri_pawnee.db` (SQLite, not in git). Row counts on 2026-11-13.

| Table | Rows | Contents |
|---|---|---|
| `lexical_entries` | 4,337 | one row per headword; 4,244 from Parks, 93 made from Blue Book words (37 of those are words Parks has too: `bb_variant_of`) |
| `glosses` | 5,504 | numbered senses |
| `paradigmatic_forms` | 9,559 | the five forms, for 2,239 verbs |
| `examples` | 2,652 | example sentences (2,564 Parks, 88 Blue Book) |
| `etymology` | 3,825 | Parks's printed etymology; `constituent_elements` is a derived parse whose per-piece glosses are unreliable |
| `cognates` | 609 | related forms in Arikara, Kitsai, Wichita ... |
| `derived_stems` | 21 | the stems Parks lists, with their glosses, under ten bound stems such as *iri-* and *piira-* |
| `english_index` | 7,806 | English-to-Skiri lookup rows, rebuilt from the printed page on 2026-11-14: 5,165 with a Skiri term, 5,162 of them linked to an entry; the other 2,641 are headwords that only refer to another |
| `cross_references` | 4,578 | "see also" links as printed, with the Skiri forms in braces |
| `semantic_tags` | 4,499 | 19 topic tags on 3,315 entries |
| `blue_book_attestations` | 1,026 | Blue Book vocabulary items; 581 linked to an entry |
| `lessons` | 20 | Blue Book lessons |
| `verb_paradigms` | 770 | Parks Appendix 1: 7 verbs × 10 modes × 11 persons; 152 forms corrected from the printed pages on 2026-11-13 |
| `irregular_verb_roots` | 9 | Parks Appendix 2 |
| `morpheme_abbreviations` | 164 | Parks's abbreviation list |
| `sound_change_rules` | 24 | Parks chapter 3: the rules and his examples |
| `kinship_paradigms` | 11 | Parks Appendix 3: kin terms with "my", "your", "his/her" |
| `function_words`, `bb_function_words` | 414, 63 | particles, demonstratives, conjunctions. The rows taken from Blue Book phrases are still OCR text |
| `bb_gap_triage` | 516 | Blue Book items with no dictionary match, classified |
| `community_feedback` | 2 | flags and confirmations from the web app |
| `srs_cards`, `srs_reviews` | 0, 0 | spaced-repetition state |

Useful columns on `lexical_entries`: `blue_book_attested` (181 entries),
`source` (`blue_book` for the 93 Blue Book-only words), `bb_variant_of`,
`page_number`. (`form2_confidence` is empty since 2026-11-14.)

No table holds a form that a script made. Four that did, written by the
conjugation and possession engines, were dropped on 2026-11-14
(`morpheme_inventory`, `verb_template_slots`, `noun_stems`,
`possession_examples`).

**`page_number` is the page of the printed book** (349 to 529) for every Parks
entry since 2026-11-14 (`scripts/fix_page_citations.py`). Until then most
values were the number of the split PDF file, which is 348 less. The `-pNNN-`
inside an entry id still holds the old number and is not a page reference:
ids are kept stable, and the 28 `kaa…` entries with `-p2-` ids are on book
page 419. `english_index.page_number` belongs to the English-to-Skiri section
and still holds file numbers (there the book page is the file number plus 60).

## Verb template

Parks's own tables of the verb are printed in the
[word-building guide](curriculum/roots_v2/construction_guide.md) and stored,
as read twice from the page, in
`extracted_data/grammatical_overview_tables.json`. In brief, as he prints
them:

| Table | What it lays out |
|---|---|
| 6 | The major positions: proclitics (outer prefixes), prefixes and preverbs (inner prefixes), incorporated noun, stem, suffixes |
| 12 | The proclitics, positions 1 to 8: adverbials, indefinite, demonstratives, dual, reflexive, negatives and the yes/no question |
| 7 | The inner prefixes, positions 9 to 26: evidentials, modals, agent, inclusive, agent plural and preverb, patient, infinitive modal, possession, benefactive, aorist, adverbials, plurals, then noun and stem |
| 16 | The suffixes, positions 25 to 28: verb stem, perfective and imperfective, intentive and habitual and inchoative, intentive subordinate |
| 8 to 11, 13, 14, 17 | The prefixes and suffixes themselves |

The 30-slot template that used to stand here was the numbering of the
conjugation engine, which was withdrawn on 2026-11-14.

## Web app routes

The Flask app runs locally only (`python -m web.app`). The public site on
GitHub Pages has the search, flashcard, lesson and guide pages and none of
the others.

| Route | Page |
|---|---|
| `/` | home, word of the day |
| `/search`, `/search/partial`, `/api/search` | search (page, live results, JSON) |
| `/entry/<id>` | full entry |
| `/browse`, `/browse/tag/<tag>`, `/browse/class/<class>` | browse |
| `/lessons`, `/lessons/<n>` | Blue Book lessons |
| `/flashcards`, `/flashcards/<week>` | weekly flashcards |
| `/study`, `/api/srs/review` | spaced-repetition study |
| `/sentence-builder`, `/api/assemble`, `/api/slot-options` | sentence builder: a printed Blue Book sentence with words swapped for other printed words |
| `/api/verbs`, `/api/verb-forms`, `/api/dictionary-sentence` | a dictionary verb by its entry: printed and derived forms, and a sentence in Parks's spelling |
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
.venv/Scripts/python scripts/sound_changes.py --measure       # the sound-change code against Parks's own examples
.venv/Scripts/python scripts/sentence_templates.py --check    # every form in the sentence builder is copied from a row
.venv/Scripts/python scripts/printed_noun_forms.py --check    # the printed forms of nouns
.venv/Scripts/python scripts/check_simplified_forms.py        # learner forms follow from Parks's forms
.venv/Scripts/python scripts/source_audit/s2e_compare.py      # dictionary entries against the printed page
.venv/Scripts/python scripts/db_dump.py --write               # refresh DB/dump/ after any database change
.venv/Scripts/python DB/query_api.py --db skiri_pawnee.db --english "bear"
```

The full list, in pipeline order, is in [scripts/README.md](scripts/README.md).
