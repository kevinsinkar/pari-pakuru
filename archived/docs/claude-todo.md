This is a beautiful and meaningful project. After reviewing your JSON structures, parsing instructions, the Sound Key, the full morpheme/abbreviation system, and the dictionary organization diagrams, I can see you've already laid serious groundwork. Let me lay out a roadmap that builds logically from foundation to full tool.

---

**Phase 1 — Foundation: Data Extraction & Core Schema**

This is the bedrock everything else depends on. Nothing works without clean, structured data.

**Milestone 1.1 — Pronunciation Respelling Key** *(your task A)*
Map each Skiri orthographic letter to a plain-English pronunciation hint using the Sound Key you already have. For example, `"aa"` → `"ah (as in father)"`, `"r"` → `"r (tapped, as in Spanish pero)"`, `"®"` → `"glottal stop (as in uh-uh)"`. This becomes a lookup table that auto-generates the `simplified_pronunciation` field in your Skiri-to-English JSON. The tricky part will be handling accent/tone marks and vowel length distinctions in a way that's intuitive for English-only readers without losing accuracy.

**Milestone 1.2 — Unified Database Schema** *(your task B)*
Your two JSON structures (English-to-Skiri and Skiri-to-English) are mirrors with different entry points but shared internal data. Rather than storing them as two separate flat collections, the schema should normalize into a relational structure: a core `lexical_entries` table (headword, phonetic form, preverb, etymology, verb class, grammatical class), linked to a `glosses` table (English meanings with sense numbers), a `paradigmatic_forms` table (the five standard inflected forms per entry), an `examples` table, and a `cross_references` junction table that links English terms to Skiri equivalents bidirectionally. This way, an English-to-Skiri lookup and a Skiri-to-English lookup hit the same underlying records — no duplication, no drift.

**Milestone 1.3 — Dictionary Page Extraction Pipeline**
Build the parser based on your Parsing and Extraction Instructions: identify boldfaced headwords as entry boundaries, extract `[phonetic form]` from brackets, pull grammatical class from small caps, verb class from parentheses, irregular forms from curly brackets, glosses from numbered definitions, etymology from angle brackets, and paradigmatic forms from the numbered 1–5 list. This is the heavy labor phase. Each extracted entry gets validated against the JSON schema before insertion.

---

**Phase 2 — Enrichment: Tags, Cross-References & Verification**

Once the raw data is in, you layer meaning and reliability on top of it.

**Milestone 2.1 — Semantic Category Tagging** *(your task C)*
Build a tagging system for domains like animals, plants, kinship, housing, celestial/weather, body parts, tools/weapons, ceremony/ritual, food, colors, numbers, and so on. Some of this can be partially automated by scanning English glosses for keyword patterns (any gloss mentioning "uncle," "aunt," "mother" → `kin`; "eagle," "beaver," "buffalo" → `animal`), but the richest tagging will come from manual review and from the etymologies, which often reveal that a word compositionally belongs to a domain even if the gloss alone doesn't make it obvious.

**Milestone 2.2 — Blue Book (Pari Pakuru) Cross-Verification** *(your task E)*
The Blue Book texts serve two purposes: first, as a verification corpus — every Skiri word that appears in a connected text can be checked against the dictionary to confirm the headword exists, the inflected form matches expected paradigms, and the gloss makes sense in context. Second, as an example corpus — sentences from the Blue Book can populate the `examples` array in your schema with real, attested usage rather than just the paradigmatic forms. This phase also surfaces gaps: words in the Blue Book that aren't in the dictionary, or forms that don't match any known paradigm, which flags either extraction errors or undocumented irregularities.

**Milestone 2.3 — Sound Change Rule Engine**
Your Major Sound Changes document (PDF 03) describes the phonological rules that transform stems when affixes attach. These need to be formalized as ordered rules — things like vowel coalescence, consonant cluster simplification, and accent shift. Encoding these as programmatic transformations is essential for Phase 3, because you can't construct inflected forms without knowing how sounds change at morpheme boundaries.

---

**Phase 3 — Grammar Engine: Morphological Construction** *(your task D)*

This is the most ambitious phase and depends on everything before it.

**Milestone 3.1 — Morpheme Inventory & Slot System**
Skiri verbs are built from a prefix-stem-suffix template with fixed ordering. Using the morpheme abbreviations you already have (the 60+ items like `IND.3.A`, `BEN`, `PERF`, `PREV`, etc.), build an ordered slot system that defines which morphemes can occupy which positions. The grammatical overview (PDF 04) and the paradigmatic forms in the dictionary are your guide — the five standard forms for each verb effectively demonstrate how the slot system works for indicative perfective, imperfective, absolutive subordinate, and intentive modes.

**Milestone 3.2 — Verb Conjugation Engine**
Given a verb stem, its class (1, 1-a, 1-i, 2, 3, 4, etc.), and a target person/number/mode/aspect combination, the engine should assemble the correct prefixes and suffixes, apply the sound change rules from 2.3, and output the inflected form. Validate every output against the paradigmatic forms already in the dictionary — if the engine produces `tatpiitit` for form 1 of a given verb, and the dictionary says `tatpiitit`, you know it's working.

**Milestone 3.3 — Sentence Construction Framework**
Move from word-level to clause-level: given an English sentence like "I saw the man," identify the verb ("see"), look up the Skiri equivalent, determine it's transitive, slot in the 1st person agentive prefix, the 3rd person animate patient, indicative mode, perfective aspect, and assemble. This is where the preverb system (`ut-`, `ir-`, `uur-`) becomes critical, and where you'll lean heavily on the cross-references and the Blue Book examples for validation.

---

**Phase 4 — Interface & Usability**

**Milestone 4.1 — Bidirectional Search Interface**
A front-end where a user types English and gets Skiri results (with pronunciation, paradigms, examples, category tags) or types Skiri and gets English results. Fuzzy matching is important here since learners will misspell.

**Milestone 4.2 — Audio Pronunciation Layer**
If any recorded audio exists for Skiri words, linking it to entries. If not, the respelling key from 1.1 at least gives learners a starting point, and you could build a text-to-approximate-speech system using the phonetic rules.

**Milestone 4.3 — Sentence Builder UI**
A guided interface where a user selects "I / you / he/she," an action, an object, a tense/aspect, and the engine from Phase 3 assembles the Skiri sentence with a morpheme-by-morpheme breakdown showing how it was built.

---

**Additional tasks I'd add that you didn't mention:**

One is **cognate and etymology linking** — your JSON structures already have cognate fields for Arikara, Kitsai, Wichita, and South Band Pawnee. Building these out creates a comparative Caddoan resource, not just a Skiri one.

Another is **a validation/QA layer** — automated checks that every phonetic form uses only characters from the Sound Key, that every grammatical class abbreviation matches the known set, that every verb has the expected number of paradigmatic forms for its class, and that cross-references actually point to entries that exist.

A third is **versioning and contributor tracking** — as this tool grows and entries get corrected or enriched, you'll want to know what changed, when, and why. This is especially important for a language preservation project where decisions about spelling, glossing, and categorization carry cultural weight.

Finally, **an export pipeline** — the ability to generate a printable dictionary (PDF), flashcard decks (Anki), or structured data files (for other researchers) from the same underlying database.
