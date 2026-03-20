-- =============================================================================
-- Pari Pakuru — Skiri Pawnee Dictionary Database
-- Phase 1.2: Relational Schema (SQLite)
-- =============================================================================
-- Unifies S2E (primary linguistic record) and E2S (English index layer)
-- into a single normalized relational database.
--
-- Design principles:
--   - S2E entries are the authoritative source (lexical_entries + child tables)
--   - E2S entries are the English lookup layer (english_index + cross_references)
--   - All IDs preserved from linked JSON for traceability
--   - JSON stored only for complex/variable-structure fields (etymology constituents)
--   - FTS5 virtual tables for full-text search on glosses and examples
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Core lexical entries (from S2E — one row per dictionary headword)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lexical_entries (
    entry_id                TEXT PRIMARY KEY,       -- e.g. "SK-paaqatuq-p100-1234"
    headword                TEXT NOT NULL,           -- original Parks orthography
    normalized_form         TEXT,                    -- learner orthography (â, î, û, č, ')
    phonetic_form           TEXT,                    -- IPA in square brackets: [•paa-ʔə-tʊʔ•]
    simplified_pronunciation TEXT,                   -- English respelling: "pah-'uh-too'"
    stem_preverb            TEXT,                    -- e.g. "(ut...)", "(ir...)"
    grammatical_class       TEXT,                    -- N, VI, VT, VD, VL, VP, VR, ADJ, ADV, etc.
    verb_class              TEXT,                    -- (1), (1-a), (2), (2-i), (3), (4), etc.
    additional_forms        TEXT,                    -- JSON array of additional grammatical forms
    page_number             INTEGER,                 -- source page in Parks dictionary
    column_position         TEXT,                    -- "left" or "right"
    compound_structure      TEXT,                    -- JSON if compound entry, else NULL
    raw_entry_json          TEXT                     -- full original S2E JSON for reference
);

CREATE INDEX idx_lexical_headword ON lexical_entries(headword);
CREATE INDEX idx_lexical_normalized ON lexical_entries(normalized_form);
CREATE INDEX idx_lexical_class ON lexical_entries(grammatical_class);
CREATE INDEX idx_lexical_verb_class ON lexical_entries(verb_class);
CREATE INDEX idx_lexical_page ON lexical_entries(page_number);

-- -----------------------------------------------------------------------------
-- Glosses / sense definitions (one entry can have multiple numbered senses)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS glosses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    sense_number    INTEGER NOT NULL,                -- 1, 2, 3...
    definition      TEXT NOT NULL,                    -- English gloss text
    usage_notes     TEXT,                             -- optional usage/context notes
    UNIQUE(entry_id, sense_number)
);

CREATE INDEX idx_glosses_entry ON glosses(entry_id);
CREATE INDEX idx_glosses_definition ON glosses(definition);

-- -----------------------------------------------------------------------------
-- Paradigmatic verb forms (up to 5 standard forms per entry)
-- -----------------------------------------------------------------------------
-- Form key:
--   1 = 1st person sg subject, indicative, perfective
--   2 = 3rd person sg subject, indicative, perfective
--   3 = 3rd person sg subject, indicative, imperfective
--   4 = 3rd person sg subject, absolutive, subordinate perfective
--   5 = 3rd person sg subject, indicative, perfective intentive
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS paradigmatic_forms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    form_number     INTEGER NOT NULL CHECK(form_number BETWEEN 1 AND 5),
    skiri_form      TEXT NOT NULL,
    UNIQUE(entry_id, form_number)
);

CREATE INDEX idx_paradigm_entry ON paradigmatic_forms(entry_id);

-- -----------------------------------------------------------------------------
-- Example sentences / usages
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS examples (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id            TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    skiri_text          TEXT NOT NULL,
    english_translation TEXT,
    usage_context       TEXT,                         -- source info (e.g. "Blue Book Lesson 5")
    source              TEXT DEFAULT 'parks_dictionary' -- 'parks_dictionary', 'blue_book', etc.
);

CREATE INDEX idx_examples_entry ON examples(entry_id);

-- -----------------------------------------------------------------------------
-- Etymology
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etymology (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id                TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    raw_etymology           TEXT,                    -- full raw etymology string from Parks
    literal_translation     TEXT,                    -- English literal meaning
    constituent_elements    TEXT,                    -- JSON array of morpheme breakdowns
    UNIQUE(entry_id)
);

CREATE INDEX idx_etymology_entry ON etymology(entry_id);

-- -----------------------------------------------------------------------------
-- Cognates (related forms in sister languages)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cognates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    language        TEXT NOT NULL,                    -- "Ar." (Arikara), "Ki." (Kitsai), etc.
    form            TEXT NOT NULL
);

CREATE INDEX idx_cognates_entry ON cognates(entry_id);
CREATE INDEX idx_cognates_language ON cognates(language);

-- -----------------------------------------------------------------------------
-- Derived stems (sub-entries within an S2E entry)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS derived_stems (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    stem_form       TEXT NOT NULL,
    phonetic_form   TEXT,
    definition      TEXT,
    raw_json        TEXT                             -- full derived stem object
);

CREATE INDEX idx_derived_entry ON derived_stems(entry_id);

-- -----------------------------------------------------------------------------
-- English index (from E2S — the lookup layer)
-- Each row = one E2S subentry pointing to an S2E lexical entry
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS english_index (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    english_word        TEXT NOT NULL,                -- E2S headword (English)
    subentry_number     INTEGER NOT NULL,             -- position within the E2S entry
    entry_id            TEXT REFERENCES lexical_entries(entry_id),  -- linked S2E entry (nullable for unmatched)
    s2e_match_type      TEXT,                         -- "exact_unique", "gloss_disambiguated", "fallback", etc.
    skiri_term          TEXT,                          -- Skiri form as given in E2S
    phonetic_form       TEXT,                          -- E2S phonetic (may be more accurate IPA)
    grammatical_class   TEXT,
    verb_class          TEXT,
    page_number         INTEGER,                      -- E2S source page
    raw_subentry_json   TEXT                           -- full original E2S subentry JSON
);

CREATE INDEX idx_english_word ON english_index(english_word);
CREATE INDEX idx_english_entry_id ON english_index(entry_id);
CREATE INDEX idx_english_match ON english_index(s2e_match_type);

-- -----------------------------------------------------------------------------
-- Cross-references (from E2S Part III — "see also" links between English terms)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cross_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    from_english_word   TEXT NOT NULL,                -- source English entry
    to_english_term     TEXT NOT NULL,                -- referenced English term
    skiri_equivalents   TEXT,                          -- JSON array of Skiri forms mentioned
    source_page         INTEGER
);

CREATE INDEX idx_xref_from ON cross_references(from_english_word);
CREATE INDEX idx_xref_to ON cross_references(to_english_term);

-- -----------------------------------------------------------------------------
-- Full-text search virtual tables
-- -----------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS fts_glosses USING fts5(
    entry_id,
    definition,
    content='glosses',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_examples USING fts5(
    entry_id,
    skiri_text,
    english_translation,
    content='examples',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_english_index USING fts5(
    english_word,
    entry_id,
    content='english_index',
    content_rowid='id'
);

-- -----------------------------------------------------------------------------
-- FTS triggers to keep virtual tables in sync
-- -----------------------------------------------------------------------------

-- Glosses FTS sync
CREATE TRIGGER IF NOT EXISTS glosses_ai AFTER INSERT ON glosses BEGIN
    INSERT INTO fts_glosses(rowid, entry_id, definition)
    VALUES (new.id, new.entry_id, new.definition);
END;

CREATE TRIGGER IF NOT EXISTS glosses_ad AFTER DELETE ON glosses BEGIN
    INSERT INTO fts_glosses(fts_glosses, rowid, entry_id, definition)
    VALUES ('delete', old.id, old.entry_id, old.definition);
END;

CREATE TRIGGER IF NOT EXISTS glosses_au AFTER UPDATE ON glosses BEGIN
    INSERT INTO fts_glosses(fts_glosses, rowid, entry_id, definition)
    VALUES ('delete', old.id, old.entry_id, old.definition);
    INSERT INTO fts_glosses(rowid, entry_id, definition)
    VALUES (new.id, new.entry_id, new.definition);
END;

-- Examples FTS sync
CREATE TRIGGER IF NOT EXISTS examples_ai AFTER INSERT ON examples BEGIN
    INSERT INTO fts_examples(rowid, entry_id, skiri_text, english_translation)
    VALUES (new.id, new.entry_id, new.skiri_text, new.english_translation);
END;

CREATE TRIGGER IF NOT EXISTS examples_ad AFTER DELETE ON examples BEGIN
    INSERT INTO fts_examples(fts_examples, rowid, entry_id, skiri_text, english_translation)
    VALUES ('delete', old.id, old.entry_id, old.skiri_text, old.english_translation);
END;

CREATE TRIGGER IF NOT EXISTS examples_au AFTER UPDATE ON examples BEGIN
    INSERT INTO fts_examples(fts_examples, rowid, entry_id, skiri_text, english_translation)
    VALUES ('delete', old.id, old.entry_id, old.skiri_text, old.english_translation);
    INSERT INTO fts_examples(rowid, entry_id, skiri_text, english_translation)
    VALUES (new.id, new.entry_id, new.skiri_text, new.english_translation);
END;

-- English index FTS sync
CREATE TRIGGER IF NOT EXISTS english_ai AFTER INSERT ON english_index BEGIN
    INSERT INTO fts_english_index(rowid, english_word, entry_id)
    VALUES (new.id, new.english_word, new.entry_id);
END;

CREATE TRIGGER IF NOT EXISTS english_ad AFTER DELETE ON english_index BEGIN
    INSERT INTO fts_english_index(fts_english_index, rowid, english_word, entry_id)
    VALUES ('delete', old.id, old.english_word, old.entry_id);
END;

CREATE TRIGGER IF NOT EXISTS english_au AFTER UPDATE ON english_index BEGIN
    INSERT INTO fts_english_index(fts_english_index, rowid, english_word, entry_id)
    VALUES ('delete', old.id, old.english_word, old.entry_id);
    INSERT INTO fts_english_index(rowid, english_word, entry_id)
    VALUES (new.id, new.english_word, new.entry_id);
END;

-- -----------------------------------------------------------------------------
-- Semantic tags (Phase 2.1)
-- Each row = one tag assigned to one entry.
-- Multiple tags per entry are allowed (e.g. an entry can be both 'animal' and 'food').
-- source: 'gram_class' | 'keyword' | 'etymology' | 'manual'
-- confidence: 'high' | 'medium' | 'low'
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS semantic_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id    TEXT NOT NULL REFERENCES lexical_entries(entry_id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'keyword',
    confidence  TEXT NOT NULL DEFAULT 'medium',
    UNIQUE(entry_id, tag)
);

CREATE INDEX idx_semantic_tag ON semantic_tags(tag);
CREATE INDEX idx_semantic_entry ON semantic_tags(entry_id);

-- -----------------------------------------------------------------------------
-- Metadata table for tracking import state
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_metadata (
    key     TEXT PRIMARY KEY,
    value   TEXT
);
