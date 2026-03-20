# Phase 1.2 — Database Schema

Relational database (SQLite) unifying the S2E and E2S linked dictionary data.

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | DDL — creates all tables, indexes, FTS5 virtual tables, sync triggers |
| `import_to_sqlite.py` | Reads linked JSON → populates SQLite |
| `query_api.py` | Bidirectional lookup API (library + CLI) |
| `test_schema.py` | Validation suite (53 tests, synthetic data matching real structure) |

## Tables

| Table | Source | Description |
|-------|--------|-------------|
| `lexical_entries` | S2E | Core: one row per dictionary headword (4,273 expected) |
| `glosses` | S2E | Numbered sense definitions |
| `paradigmatic_forms` | S2E | 5 standard verb forms per entry |
| `examples` | S2E | Skiri + English example sentences |
| `etymology` | S2E | Raw etymology, literal translation, constituents (JSON) |
| `cognates` | S2E | Related forms in Arikara, Kitsai, Wichita, etc. |
| `derived_stems` | S2E | Sub-stems within an entry |
| `english_index` | E2S | English lookup layer → linked to `lexical_entries` |
| `cross_references` | E2S | "See also" links between English terms |
| `import_metadata` | — | Tracks import source files and timestamps |

FTS5 virtual tables: `fts_glosses`, `fts_examples`, `fts_english_index` — kept in sync via triggers.

## Usage

### Import

```bash
python import_to_sqlite.py \
    --s2e path/to/skiri_to_english_respelled.json \
    --e2s path/to/english_to_skiri_linked.json \
    --db  skiri_pawnee.db \
    --schema schema.sql
```

### Query (CLI)

```bash
# English → Skiri
python query_api.py --db skiri_pawnee.db --english "bear"

# Skiri → English
python query_api.py --db skiri_pawnee.db --skiri "kuruks"

# Full-text search across glosses
python query_api.py --db skiri_pawnee.db --search "to run"

# Fuzzy match (learner misspellings)
python query_api.py --db skiri_pawnee.db --fuzzy "kuruk"

# Filter by grammatical class
python query_api.py --db skiri_pawnee.db --english "stop" --class VT

# Browse all nouns
python query_api.py --db skiri_pawnee.db --browse N --brief

# Database stats
python query_api.py --db skiri_pawnee.db --stats

# JSON output
python query_api.py --db skiri_pawnee.db --english "bear" --json
```

### Query (Python library)

```python
from query_api import SkiriDictionary

with SkiriDictionary("skiri_pawnee.db") as db:
    # English → Skiri
    for entry in db.lookup_english("bear"):
        print(entry.full_display())

    # Skiri → English
    for entry in db.lookup_skiri("kuruks"):
        print(entry.summary())

    # Full-text search
    for entry in db.search("running"):
        print(entry.summary())

    # Stats
    print(db.stats())
```

### Run tests

```bash
python test_schema.py
```

## Design Decisions

- **S2E is authoritative**: `lexical_entries` is the core table; `english_index` points into it.
- **`raw_entry_json`** preserved on both `lexical_entries` and `english_index` for lossless round-tripping.
- **FTS5** for relevance-ranked full-text search on glosses and examples.
- **Triggers** keep FTS tables in sync automatically on INSERT/UPDATE/DELETE.
- **`entry_id` format preserved**: `SK-{slug}-p{page}-{index}` from Phase 1.1b linking.
- **`constituent_elements` as JSON**: variable-length morpheme arrays don't normalize well; stored as JSON in the `etymology` table.
- **Nullable `entry_id` in `english_index`**: handles the ~362 unmatched E2S entries and cross-reference-only subentries.

## Phase 1.2 Checklist

- [x] Core `lexical_entries` table
- [x] `glosses` table
- [x] `paradigmatic_forms` table
- [x] `examples` table
- [x] `etymology` table
- [x] `cognates` table
- [x] `english_index` table (E2S lookup layer)
- [x] `cross_references` junction table
- [x] Import script: linked JSON → SQLite
- [x] Query API: bidirectional lookup by English or Skiri
- [x] Full-text search (FTS5)
- [x] Fuzzy search for learner misspellings
- [x] Grammatical class filtering
- [x] Test suite (53 tests, all passing)
