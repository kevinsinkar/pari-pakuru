#!/usr/bin/env python3
"""
Phase 3.1.6 — Function Word Classification
=============================================

Adds position_rule and refined subclass to the function_words table,
based on analysis of Parks Grammatical Overview (Ch. 4) and Blue Book
dialogue patterns.

LINGUISTIC ANALYSIS (from Parks Ch. 4 + Blue Book dialogues):

1. CLAUSE STRUCTURE
   Skiri is polysynthetic — most grammatical content is packed into the
   verb complex. "Sentences" are typically one or two verb complexes plus
   optional free-standing nouns. Word order for free elements is flexible
   but defaults to SOV (Subject Object Verb) or NP + VP.

2. DEMONSTRATIVE SYSTEM (Parks p. 42)
   5 deictics that combine spatial and temporal reference:
   
   | Deictic | Meaning | Position |
   |---------|---------|----------|
   | ti-/tii- | "this, here" (proximal) | PROCLITIC on verb |
   | it-/i- | "that, there" (distal) | PROCLITIC on verb |
   | iri- | "that (generalized)" (neutral distance) | PROCLITIC on verb |
   | irii- | "what, where" (interrogative) | PROCLITIC on verb |
   | riku- | "the one that/who" (relative) | PROCLITIC on verb |
   | hii- | "other" | PROCLITIC on verb |
   
   Free-standing demonstratives (from dictionary DEM class):
   | Form | Meaning | Position |
   |------|---------|----------|
   | tiʔ | "this is, it is" | CLAUSE-INITIAL or standalone |
   | tiku | "that" | PRECEDES-NOUN |
   | tireku | "here is" | CLAUSE-INITIAL (presentational) |
   | tihe | "those" | PRECEDES-NOUN |
   | hirihe | "this/that/here" | CLAUSE-INITIAL or PRECEDES-NOUN |
   | cararat | "other, those" | PRECEDES-NOUN |
   | irihii | "that other" | PRECEDES-NOUN |
   | raahku | "the one over there" | PRECEDES-NOUN (far distal) |

3. INTERROGATIVE SYSTEM (Parks Table 14, p. 41)
   Proclitic interrogatives (bound to verb):
   | Form | Meaning | Co-occurrence |
   |------|---------|---------------|
   | ka- | yes/no question | Any mode |
   | ka-...i- | negative yes/no | Any mode |
   
   Free interrogative pronouns:
   | Form | Meaning | Position | Mode |
   |------|---------|----------|------|
   | taki | "who" | CLAUSE-INITIAL | Absolutive |
   | kirike/kiki | "what, why, how" | CLAUSE-INITIAL | Any |
   | kickii | "how many" | CLAUSE-INITIAL | Any |
   | kiruu/kiru | "where" | CLAUSE-INITIAL | Any |
   | niru | "where" (BB form) | CLAUSE-INITIAL | Any |
   | pirau | "when" | CLAUSE-INITIAL | Any |

4. ADVERBIAL PROCLITICS (Parks p. 41-42)
   These are BOUND to the verb complex, not free-standing:
   | Form | Meaning | Position |
   |------|---------|----------|
   | wii- | "now; when" | PROCLITIC slot 1 |
   | ruu- | "then; there" | PROCLITIC slot 1 |
   | raa- | "just" | PROCLITIC slot 1 |
   | iriruu- | "thereupon" | PROCLITIC slot 1 |

5. FREE ADVERBS (standalone words)
   Position: typically PRECEDES-VERB or CLAUSE-INITIAL
   | Form | Meaning | Position |
   |------|---------|----------|
   | hiras | "at night" | PRECEDES-VERB |
   | rahesa | "tomorrow" | CLAUSE-INITIAL |
   | kira | "perhaps, maybe" | CLAUSE-INITIAL |
   | ku/kuh | "perhaps" | CLAUSE-INITIAL |
   | resaru | "perhaps" | CLAUSE-INITIAL |
   | rariksisu | "very, hard" | PRECEDES-VERB |

6. CONJUNCTIONS
   | Form | Meaning | Position |
   |------|---------|----------|
   | a/aa | "and" | BETWEEN-CLAUSES |
   | ci | "but" | BETWEEN-CLAUSES |
   | hici | "but, and" | BETWEEN-CLAUSES |
   | hii | "and" | BETWEEN-CLAUSES |
   | aku | "or, maybe" | BETWEEN-CLAUSES |

7. INTERJECTIONS / DISCOURSE MARKERS
   Position: CLAUSE-INITIAL (standalone, precedes everything)
   | Form | Meaning |
   |------|---------|
   | nawa | "hello, now, okay" (greeting/transition) |
   | haʔaʔ/hau | "yes" |
   | ariʔ | "oh!" (surprise) |
   | aari | "well" (discourse) |
   | wi | "it is said" (quotative) |

8. POSITION RULES SUMMARY
   | Position | Description | Examples |
   |----------|-------------|---------|
   | CLAUSE-INITIAL | First element in clause, before all else | nawa, kirike, taki, rahesa |
   | PRECEDES-VERB | Before the verb complex | hiras, rariksisu |
   | PRECEDES-NOUN | Before a noun phrase | tiku, tihe, cararat |
   | BETWEEN-CLAUSES | Joins two clauses | ci, hici, a |
   | PROCLITIC | Bound to verb complex (not free) | wii-, ruu-, ka-, ti- |
   | CLAUSE-FINAL | After verb complex | (rare in Skiri) |
   | STANDALONE | Independent utterance | haʔaʔ, nawa, ariʔ |

Usage:
    python scripts/classify_function_words.py --db skiri_pawnee.db --dry-run
    python scripts/classify_function_words.py --db skiri_pawnee.db
"""

import argparse
import os
import re
import sqlite3
import sys

# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

# Demonstrative spatial system
DEMONSTRATIVE_SPATIAL = {
    'tiʔ': ('proximal', 'CLAUSE-INITIAL', 'presentational "this is"'),
    'tiku': ('distal', 'PRECEDES-NOUN', '"that" (specific referent)'),
    'tireku': ('proximal', 'CLAUSE-INITIAL', 'presentational "here is"'),
    'tihe': ('distal-plural', 'PRECEDES-NOUN', '"those"'),
    'hirihe': ('proximal-neutral', 'CLAUSE-INITIAL', '"this/that/here"'),
    'cararat': ('distal-plural', 'PRECEDES-NOUN', '"other, those"'),
    'irihii': ('distal-other', 'PRECEDES-NOUN', '"that other"'),
    'iriraaku': ('distal-specific', 'PRECEDES-NOUN', '"that one"'),
    'iriwiruu': ('distal-temporal', 'CLAUSE-INITIAL', '"there, thereupon; at that time"'),
    'raahku': ('far-distal', 'PRECEDES-NOUN', '"the one over there"'),
    'tiheruks': ('distal-past', 'PRECEDES-NOUN', '"that other one, past"'),
}

# Interrogative classification
INTERROGATIVE_RULES = {
    'kirike': ('content-question', 'CLAUSE-INITIAL', '"what, why, how" — general interrogative'),
    'kirikuʔ': ('indefinite', 'PRECEDES-VERB', '"anything" — indefinite pronoun from interrogative'),
    'kiru': ('location-question', 'CLAUSE-INITIAL', '"where" — Parks kiruu'),
    'kiruu': ('location-question', 'CLAUSE-INITIAL', '"where"'),
    'niru': ('location-question', 'CLAUSE-INITIAL', '"where" — BB variant'),
    'kirti': ('location-question', 'CLAUSE-INITIAL', '"where" — BB variant'),
    'taku': ('content-question', 'CLAUSE-INITIAL', '"what, anyone"'),
    'ka?': ('yes-no-question', 'PROCLITIC', '"yes/no question marker"'),
    'kickii': ('quantity-question', 'CLAUSE-INITIAL', '"how many"'),
    'pirau': ('temporal-question', 'CLAUSE-INITIAL', '"when"'),
}

# Conjunction position rules
CONJUNCTION_RULES = {
    'a, aa': 'BETWEEN-CLAUSES',
    'ci': 'BETWEEN-CLAUSES',
    'hici': 'BETWEEN-CLAUSES',
    'hii': 'BETWEEN-CLAUSES',
    'aku': 'BETWEEN-CLAUSES',
    'ar': 'BETWEEN-CLAUSES',
    'or': 'BETWEEN-CLAUSES',
    'wa': 'BETWEEN-CLAUSES',
    'hiruu': 'CLAUSE-INITIAL',
    'hiiriruu': 'CLAUSE-INITIAL',
    'iihii': 'BETWEEN-CLAUSES',
}

# Interjection/discourse marker rules
INTERJECTION_RULES = {
    'nawa': 'STANDALONE',
    'nawa!': 'STANDALONE',
    'hau': 'STANDALONE',
    'hadʔ': 'STANDALONE',
    'haʔaʔ': 'STANDALONE',
    'haaʔaʔ': 'STANDALONE',
    'ilanʔ': 'STANDALONE',
    'ariʔ': 'STANDALONE',
    'aari': 'CLAUSE-INITIAL',
    'wi': 'CLAUSE-INITIAL',
    'aki': 'CLAUSE-INITIAL',
    'ah': 'STANDALONE',
    'hiruʔ': 'STANDALONE',
    'ut': 'STANDALONE',
    'wfs': 'STANDALONE',
}

# Adverb position rules (by keyword in gloss)
def classify_adverb_position(headword, gloss):
    """Infer position rule for adverbs from gloss content."""
    g = (gloss or '').lower()
    
    # Temporal adverbs → CLAUSE-INITIAL
    if any(w in g for w in ['tomorrow', 'yesterday', 'today', 'morning', 'evening',
                             'always', 'never', 'sometimes', 'perhaps', 'maybe']):
        return 'CLAUSE-INITIAL'
    
    # Manner adverbs → PRECEDES-VERB
    if any(w in g for w in ['quickly', 'slowly', 'hard', 'very', 'really',
                             'well', 'badly', 'carefully', 'a lot']):
        return 'PRECEDES-VERB'
    
    # Locative adverbs → CLAUSE-INITIAL or PRECEDES-VERB
    if any(w in g for w in ['here', 'there', 'inside', 'outside', 'above',
                             'below', 'nearby', 'far', 'across']):
        return 'PRECEDES-VERB'
    
    # Temporal setting → CLAUSE-INITIAL
    if any(w in g for w in ['at night', 'in winter', 'in summer', 'nighttime',
                             'daytime', 'long ago', 'formerly']):
        return 'CLAUSE-INITIAL'
    
    return 'PRECEDES-VERB'  # default for adverbs


def classify_locative_position(headword, gloss):
    """Classify locative words."""
    g = (gloss or '').lower()
    # Locative preverbs (end in -) are PROCLITIC
    if headword.endswith('-'):
        return 'PROCLITIC'
    # Free-standing locatives
    return 'PRECEDES-VERB'


def classify_numeral_position(headword, gloss):
    """Numerals typically precede the noun they modify."""
    return 'PRECEDES-NOUN'


# ---------------------------------------------------------------------------
# Main classification engine
# ---------------------------------------------------------------------------

def classify_function_word(hw, gram_class, subclass, gloss):
    """
    Assign position_rule and refined subclass to a function word.
    Returns (position_rule, refined_subclass, notes).
    """
    # Demonstratives
    if hw in DEMONSTRATIVE_SPATIAL:
        spatial, pos, note = DEMONSTRATIVE_SPATIAL[hw]
        return pos, f'demonstrative-{spatial}', note
    
    # Interrogatives
    if hw in INTERROGATIVE_RULES:
        qtype, pos, note = INTERROGATIVE_RULES[hw]
        return pos, f'interrogative-{qtype}', note
    
    # Conjunctions
    if gram_class == 'CONJ':
        pos = CONJUNCTION_RULES.get(hw, 'BETWEEN-CLAUSES')
        return pos, subclass or 'conjunction', ''
    
    # Interjections
    if gram_class == 'INTERJ':
        pos = INTERJECTION_RULES.get(hw, 'STANDALONE')
        return pos, subclass or 'interjection', ''
    
    # Adverbs
    if gram_class == 'ADV':
        pos = classify_adverb_position(hw, gloss)
        return pos, subclass or 'adverb', ''
    
    # Locatives
    if gram_class == 'LOC':
        pos = classify_locative_position(hw, gloss)
        return pos, subclass or 'locative', ''
    
    # Numerals
    if gram_class == 'NUM':
        return 'PRECEDES-NOUN', subclass or 'numeral', ''
    
    # Pronouns
    if gram_class == 'PRON':
        return 'CLAUSE-INITIAL', subclass or 'pronoun', ''
    
    # Quantifiers
    if gram_class == 'QUAN':
        return 'PRECEDES-NOUN', subclass or 'quantifier', ''
    
    # Particles (BB-extracted)
    if gram_class == 'PART':
        g = (gloss or '').lower()
        if 'imperative' in g:
            return 'PROCLITIC', 'imperative-marker', ''
        if 'future' in g:
            return 'PROCLITIC', 'tense-marker', ''
        if 'definite' in g or 'article' in g:
            return 'PRECEDES-NOUN', 'determiner', ''
        if 'copula' in g or 'is' in g.split():
            return 'CLAUSE-INITIAL', 'copula', ''
        return 'PROCLITIC', 'particle', ''
    
    return 'UNKNOWN', subclass or 'other', ''


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

def run_classification(db_path, dry_run=False):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Add position_rule column if not exists
    cols = {r[1] for r in conn.execute("PRAGMA table_info(function_words)")}
    if 'position_rule' not in cols:
        if not dry_run:
            conn.execute("ALTER TABLE function_words ADD COLUMN position_rule TEXT")
            conn.commit()
        print("Added position_rule column to function_words")
    
    if 'refined_subclass' not in cols:
        if not dry_run:
            conn.execute("ALTER TABLE function_words ADD COLUMN refined_subclass TEXT")
            conn.commit()
        print("Added refined_subclass column to function_words")
    
    # Fetch all function words
    rows = conn.execute("""
        SELECT id, headword, grammatical_class, subclass, usage_notes
        FROM function_words ORDER BY grammatical_class, headword
    """).fetchall()
    
    # Classify
    updates = []
    by_position = {}
    
    for r in rows:
        pos, refined, notes = classify_function_word(
            r['headword'], r['grammatical_class'], r['subclass'], r['usage_notes']
        )
        updates.append((pos, refined, r['id']))
        by_position.setdefault(pos, []).append(r['headword'])
    
    # Report
    out = sys.stdout.buffer
    out.write(f"\n{'='*70}\n".encode("utf-8"))
    out.write(f"FUNCTION WORD CLASSIFICATION -- {len(rows)} items\n".encode("utf-8"))
    out.write(f"{'='*70}\n".encode("utf-8"))

    for pos in ['CLAUSE-INITIAL', 'PRECEDES-VERB', 'PRECEDES-NOUN',
                 'BETWEEN-CLAUSES', 'PROCLITIC', 'STANDALONE', 'UNKNOWN']:
        items = by_position.get(pos, [])
        if items:
            out.write(f"\n{pos} ({len(items)}):\n".encode("utf-8"))
            for hw in items[:10]:
                out.write(f"  {hw}\n".encode("utf-8"))
            if len(items) > 10:
                out.write(f"  ... and {len(items)-10} more\n".encode("utf-8"))

    if dry_run:
        out.write(f"\n[DRY RUN] Would update {len(updates)} rows\n".encode("utf-8"))
    else:
        for pos, refined, row_id in updates:
            conn.execute(
                "UPDATE function_words SET position_rule = ?, refined_subclass = ? WHERE id = ?",
                (pos, refined, row_id)
            )
        conn.commit()
        out.write(f"\nUpdated {len(updates)} rows with position_rule + refined_subclass\n".encode("utf-8"))
    
    conn.close()
    return by_position


def main():
    parser = argparse.ArgumentParser(description="Classify function words with position rules")
    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skiri_pawnee.db")
    parser.add_argument("--db", default=default_db, help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Show classification without modifying DB")
    args = parser.parse_args()
    
    run_classification(args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
