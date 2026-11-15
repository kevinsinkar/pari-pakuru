CREATE TABLE lexical_entries (
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
, blue_book_attested INTEGER DEFAULT 0, form2_confidence REAL, source TEXT, bb_variant_of TEXT);

CREATE INDEX idx_lexical_headword ON lexical_entries(headword);

CREATE INDEX idx_lexical_normalized ON lexical_entries(normalized_form);

CREATE INDEX idx_lexical_class ON lexical_entries(grammatical_class);

CREATE INDEX idx_lexical_verb_class ON lexical_entries(verb_class);

CREATE INDEX idx_lexical_page ON lexical_entries(page_number);

CREATE TABLE paradigmatic_forms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    form_number     INTEGER NOT NULL CHECK(form_number BETWEEN 1 AND 5),
    skiri_form      TEXT NOT NULL,
    UNIQUE(entry_id, form_number)
);

CREATE INDEX idx_paradigm_entry ON paradigmatic_forms(entry_id);

CREATE TABLE examples (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id            TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    skiri_text          TEXT NOT NULL,
    english_translation TEXT,
    usage_context       TEXT,                         -- source info (e.g. "Blue Book Lesson 5")
    source              TEXT DEFAULT 'parks_dictionary' -- 'parks_dictionary', 'blue_book', etc.
);

CREATE INDEX idx_examples_entry ON examples(entry_id);

CREATE TABLE etymology (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id                TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    raw_etymology           TEXT,                    -- full raw etymology string from Parks
    literal_translation     TEXT,                    -- English literal meaning
    constituent_elements    TEXT,                    -- JSON array of morpheme breakdowns
    UNIQUE(entry_id)
);

CREATE INDEX idx_etymology_entry ON etymology(entry_id);

CREATE TABLE cognates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    language        TEXT NOT NULL,                    -- "Ar." (Arikara), "Ki." (Kitsai), etc.
    form            TEXT NOT NULL
);

CREATE INDEX idx_cognates_entry ON cognates(entry_id);

CREATE INDEX idx_cognates_language ON cognates(language);

CREATE TABLE derived_stems (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
    stem_form       TEXT NOT NULL,
    phonetic_form   TEXT,
    definition      TEXT,
    raw_json        TEXT                             -- full derived stem object
);

CREATE INDEX idx_derived_entry ON derived_stems(entry_id);

CREATE TABLE english_index (
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

CREATE TABLE cross_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    from_english_word   TEXT NOT NULL,                -- source English entry
    to_english_term     TEXT NOT NULL,                -- referenced English term
    skiri_equivalents   TEXT,                          -- JSON array of Skiri forms mentioned
    source_page         INTEGER
);

CREATE INDEX idx_xref_from ON cross_references(from_english_word);

CREATE INDEX idx_xref_to ON cross_references(to_english_term);

CREATE VIRTUAL TABLE fts_glosses USING fts5(
    entry_id,
    definition,
    content='glosses',
    content_rowid='id'
);

CREATE VIRTUAL TABLE fts_examples USING fts5(
    entry_id,
    skiri_text,
    english_translation,
    content='examples',
    content_rowid='id'
);

CREATE VIRTUAL TABLE fts_english_index USING fts5(
    english_word,
    entry_id,
    content='english_index',
    content_rowid='id'
);

CREATE TRIGGER examples_ai AFTER INSERT ON examples BEGIN
    INSERT INTO fts_examples(rowid, entry_id, skiri_text, english_translation)
    VALUES (new.id, new.entry_id, new.skiri_text, new.english_translation);
END;

CREATE TRIGGER examples_ad AFTER DELETE ON examples BEGIN
    INSERT INTO fts_examples(fts_examples, rowid, entry_id, skiri_text, english_translation)
    VALUES ('delete', old.id, old.entry_id, old.skiri_text, old.english_translation);
END;

CREATE TRIGGER examples_au AFTER UPDATE ON examples BEGIN
    INSERT INTO fts_examples(fts_examples, rowid, entry_id, skiri_text, english_translation)
    VALUES ('delete', old.id, old.entry_id, old.skiri_text, old.english_translation);
    INSERT INTO fts_examples(rowid, entry_id, skiri_text, english_translation)
    VALUES (new.id, new.entry_id, new.skiri_text, new.english_translation);
END;

CREATE TRIGGER english_ai AFTER INSERT ON english_index BEGIN
    INSERT INTO fts_english_index(rowid, english_word, entry_id)
    VALUES (new.id, new.english_word, new.entry_id);
END;

CREATE TRIGGER english_ad AFTER DELETE ON english_index BEGIN
    INSERT INTO fts_english_index(fts_english_index, rowid, english_word, entry_id)
    VALUES ('delete', old.id, old.english_word, old.entry_id);
END;

CREATE TRIGGER english_au AFTER UPDATE ON english_index BEGIN
    INSERT INTO fts_english_index(fts_english_index, rowid, english_word, entry_id)
    VALUES ('delete', old.id, old.english_word, old.entry_id);
    INSERT INTO fts_english_index(rowid, english_word, entry_id)
    VALUES (new.id, new.english_word, new.entry_id);
END;

CREATE TABLE import_metadata (
    key     TEXT PRIMARY KEY,
    value   TEXT
);

CREATE TABLE semantic_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id    TEXT NOT NULL REFERENCES lexical_entries(entry_id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'keyword',
    confidence  TEXT NOT NULL DEFAULT 'medium',
    UNIQUE(entry_id, tag)
);

CREATE INDEX idx_semantic_tag ON semantic_tags(tag);

CREATE INDEX idx_semantic_entry ON semantic_tags(entry_id);

CREATE TABLE blue_book_attestations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bb_skiri_form TEXT NOT NULL,
            bb_pronunciation TEXT,
            bb_english TEXT,
            context_type TEXT,
            dialect_note TEXT,
            lesson_number INTEGER,
            page_number INTEGER,
            full_sentence_pawnee TEXT,
            full_sentence_english TEXT,
            entry_id TEXT REFERENCES lexical_entries(entry_id),
            match_type TEXT,
            match_confidence REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

CREATE INDEX idx_bba_entry_id
            ON blue_book_attestations(entry_id);

CREATE INDEX idx_bba_lesson
            ON blue_book_attestations(lesson_number);

CREATE INDEX idx_bba_match_type
            ON blue_book_attestations(match_type);

CREATE TABLE sound_change_rules (
            rule_id       TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            type          TEXT NOT NULL CHECK(type IN ('restricted', 'unrestricted')),
            domain        TEXT NOT NULL CHECK(domain IN ('vowel', 'consonant')),
            formal        TEXT NOT NULL,
            description   TEXT,
            ordering      INTEGER NOT NULL,
            examples      TEXT  -- JSON array
        );

CREATE TABLE verb_paradigms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verb_heading TEXT NOT NULL,
            verb_class TEXT,
            dictionary_form TEXT,
            english_gloss TEXT,
            mode TEXT NOT NULL,
            person_number TEXT NOT NULL,
            skiri_form TEXT NOT NULL,
            english_form TEXT,
            source_page INTEGER,
            UNIQUE(verb_heading, mode, person_number)
        );

CREATE TABLE irregular_verb_roots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headword TEXT NOT NULL,
            english_gloss TEXT,
            singular_stem TEXT,
            dual_stem TEXT,
            plural_stem TEXT,
            distributive_prefix INTEGER DEFAULT 0,
            notes TEXT,
            UNIQUE(headword)
        );

CREATE TABLE morpheme_abbreviations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abbreviation TEXT NOT NULL UNIQUE,
            meaning TEXT NOT NULL,
            morpheme_form TEXT,
            notes TEXT
        );

CREATE TABLE kinship_paradigms (
            english_term TEXT NOT NULL,
            stem TEXT NOT NULL,
            form_1sg TEXT,
            form_2sg TEXT,
            form_3sg TEXT,
            vocative TEXT,
            source TEXT DEFAULT 'appendix3',
            notes TEXT,
            UNIQUE(english_term, stem)
        );

CREATE TABLE community_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            form_field TEXT,
            feedback_type TEXT NOT NULL CHECK (feedback_type IN ('flag', 'confirm')),
            issue_type TEXT,
            suggested_correction TEXT,
            comment TEXT,
            reporter_name TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'reviewed', 'accepted', 'rejected')),
            reviewer_note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            reviewed_at TEXT,
            FOREIGN KEY (entry_id) REFERENCES lexical_entries(entry_id)
        );

CREATE INDEX idx_feedback_status
        ON community_feedback(status);

CREATE INDEX idx_feedback_entry
        ON community_feedback(entry_id);

CREATE TABLE bb_gap_triage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bb_skiri_form TEXT NOT NULL,
            bb_english TEXT,
            context_type TEXT,
            lesson_number INTEGER,
            category TEXT NOT NULL,
            confidence REAL,
            notes TEXT,
            triaged_at TEXT NOT NULL
        );

CREATE INDEX idx_gap_triage_cat ON bb_gap_triage(category);

CREATE TABLE function_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headword TEXT NOT NULL UNIQUE,
            grammatical_class TEXT NOT NULL,
            subclass TEXT,
            usage_notes TEXT,
            bb_attested INTEGER DEFAULT 0,
            source TEXT
        , position_rule TEXT, refined_subclass TEXT);

CREATE INDEX idx_fw_class ON function_words(grammatical_class);

CREATE TABLE bb_function_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            grammatical_class TEXT,
            meaning TEXT,
            source_phrase TEXT,
            lesson TEXT,
            normalized_word TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE "glosses" (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
            sense_number    INTEGER,
            definition      TEXT NOT NULL,
            usage_notes     TEXT
        );

CREATE TRIGGER glosses_ai AFTER INSERT ON glosses BEGIN
    INSERT INTO fts_glosses(rowid, entry_id, definition)
    VALUES (new.id, new.entry_id, new.definition);
END;

CREATE TRIGGER glosses_ad AFTER DELETE ON glosses BEGIN
    INSERT INTO fts_glosses(fts_glosses, rowid, entry_id, definition)
    VALUES ('delete', old.id, old.entry_id, old.definition);
END;

CREATE TRIGGER glosses_au AFTER UPDATE ON glosses BEGIN
    INSERT INTO fts_glosses(fts_glosses, rowid, entry_id, definition)
    VALUES ('delete', old.id, old.entry_id, old.definition);
    INSERT INTO fts_glosses(rowid, entry_id, definition)
    VALUES (new.id, new.entry_id, new.definition);
END;

CREATE TABLE lessons (
                lesson_number  INTEGER PRIMARY KEY,
                skiri_title    TEXT,
                english_title  TEXT,
                page_start     INTEGER,
                page_end       INTEGER,
                dialogues      TEXT,   -- JSON: [{lines:[{skiri,english}]}]
                grammar_notes  TEXT,   -- JSON: [{heading,text}]
                template_ids   TEXT    -- JSON: ["T1","T3"]
            );

CREATE TABLE srs_cards (
            entry_id      TEXT PRIMARY KEY REFERENCES lexical_entries(entry_id),
            ease          REAL NOT NULL DEFAULT 2.5,
            interval_days REAL NOT NULL DEFAULT 0,
            reps          INTEGER NOT NULL DEFAULT 0,
            lapses        INTEGER NOT NULL DEFAULT 0,
            due           TEXT,                -- ISO date
            last_review   TEXT
        );

CREATE TABLE srs_reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id        TEXT NOT NULL,
            grade           TEXT NOT NULL,
            interval_before REAL,
            interval_after  REAL,
            reviewed_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );

CREATE INDEX idx_srs_due ON srs_cards(due);

