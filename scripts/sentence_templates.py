#!/usr/bin/env python3
"""
Phase 3.2a — Template-Based Sentence Assembly Engine
=====================================================

Assembles Skiri Pawnee sentences from fixed templates extracted from
Blue Book (Pari Pakuru) dialogues. Not free-form translation — guided
construction from attested sentence patterns.

ARCHITECTURE:
  - 10 templates covering 73% of Blue Book sentences (113/155)
  - Each template defines: slot types, word order, morphological constraints
  - Templates 6 (negation) and 7 (affirmation) are wrappers that nest others
  - Assembly pipeline: validate → look up forms → order → output + breakdown

INTEGRATION:
  - Reads: skiri_pawnee.db (lexical_entries, paradigmatic_forms, function_words,
    blue_book_attestations, kinship_paradigms)
  - Optional: morpheme_inventory.py (conjugation engine, if available)
  - Optional: possession_engine.py (noun possession, if available)

Usage:
    # CLI test mode — run all 27 validation tests
    python sentence_templates.py --test

    # Assemble a sentence
    python sentence_templates.py --template T1 --noun "hitu'"
    python sentence_templates.py --template T2 --noun rakis --vd pahaat
    python sentence_templates.py --template T8 --verb_form "tatuks•at" --locative Pari

    # List templates
    python sentence_templates.py --list

    # As a library
    from sentence_templates import assemble, list_templates, TemplateResult
    result = assemble("T2", noun="rakis", vd="pahaat")
    print(result.skiri_sentence)  # "Rakis ti pahaat"
"""

import json
import os
import re
import sqlite3
import sys
import argparse
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get(
    "SKIRI_DB_PATH",
    str(Path(__file__).resolve().parent / "skiri_pawnee.db"),
)

# Fallback: check common locations
_FALLBACK_PATHS = [
    Path(__file__).resolve().parent / "skiri_pawnee.db",
    Path(__file__).resolve().parent.parent / "skiri_pawnee.db",
    Path(__file__).resolve().parent.parent / "data" / "skiri_pawnee.db",
    Path.home() / "skiri_pawnee.db",
]


def _find_db() -> str:
    if os.path.exists(DB_PATH):
        return DB_PATH
    for p in _FALLBACK_PATHS:
        if p.exists():
            return str(p)
    raise FileNotFoundError(
        f"Cannot find skiri_pawnee.db. Set SKIRI_DB_PATH env variable. "
        f"Checked: {DB_PATH}, {[str(p) for p in _FALLBACK_PATHS]}"
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class MorphemeChip:
    """One piece of the morpheme breakdown display."""
    form: str
    gloss: str
    role: str  # SUBJECT, VERB, OBJECT, PARTICLE, ADVERB, LOCATIVE, etc.
    entry_id: Optional[str] = None


@dataclass
class TemplateResult:
    """Output of sentence assembly."""
    skiri_sentence: str
    english_gloss: str
    template_id: str
    template_name: str
    confidence: str  # HIGH, MEDIUM, LOW
    morpheme_breakdown: List[MorphemeChip] = field(default_factory=list)
    bb_attestation: Optional[str] = None  # e.g., "L01, L02"
    word_order_note: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skiri_sentence": self.skiri_sentence,
            "english_gloss": self.english_gloss,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "confidence": self.confidence,
            "morpheme_breakdown": [
                {"form": m.form, "gloss": m.gloss, "role": m.role, "entry_id": m.entry_id}
                for m in self.morpheme_breakdown
            ],
            "bb_attestation": self.bb_attestation,
            "word_order_note": self.word_order_note,
            "error": self.error,
        }


@dataclass
class TemplateInfo:
    """Metadata about a template for the UI."""
    template_id: str
    name: str
    english_pattern: str
    skiri_example: str
    english_example: str
    slots: List[Dict[str, str]]  # [{"name": "noun", "type": "N", "required": True}, ...]
    lessons: str  # "L01–L13"
    bb_count: int  # Number of BB attestations


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------
TEMPLATES: Dict[str, TemplateInfo] = {
    "T1": TemplateInfo(
        template_id="T1",
        name="Identification",
        english_pattern="This is [thing] / He/She is [noun]",
        skiri_example="Ti hitu'",
        english_example="This is a feather",
        slots=[
            {"name": "noun", "type": "N,N-KIN,TRIBAL", "required": True,
             "description": "The thing or person being identified"},
        ],
        lessons="L01, L05, L07, L13",
        bb_count=11,
    ),
    "T2": TemplateInfo(
        template_id="T2",
        name="Descriptive",
        english_pattern="[Thing] is [quality]",
        skiri_example="Rakis ti pahaat",
        english_example="The stick is red",
        slots=[
            {"name": "noun", "type": "N", "required": True,
             "description": "The thing being described"},
            {"name": "vd", "type": "VD", "required": True,
             "description": "Descriptive verb (quality: color, size, etc.)"},
        ],
        lessons="L02, L09",
        bb_count=4,
    ),
    "T3": TemplateInfo(
        template_id="T3",
        name="Yes/No Question",
        english_pattern="Is [thing] [quality/action]?",
        skiri_example="Ka ra•pahaat rakis?",
        english_example="Is the stick red?",
        slots=[
            {"name": "noun", "type": "N", "required": False,
             "description": "The subject (optional if clear from context)"},
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "Pre-conjugated verb form (absolutive mode)"},
        ],
        lessons="L01–L20",
        bb_count=15,
    ),
    "T4": TemplateInfo(
        template_id="T4",
        name="What Question",
        english_pattern="What is/does [subject] [verb]?",
        skiri_example="Kirike ru'?",
        english_example="What is it?",
        slots=[
            {"name": "subject", "type": "N", "required": False,
             "description": "The subject (precedes kirike if present)"},
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "Pre-conjugated verb form (absolutive mode)"},
        ],
        lessons="L01–L18",
        bb_count=17,
    ),
    "T5": TemplateInfo(
        template_id="T5",
        name="Where Question",
        english_pattern="Where is/did [subject] [verb]?",
        skiri_example="Kiru rasuks•at?",
        english_example="Where did you go?",
        slots=[
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "Pre-conjugated verb form (absolutive mode)"},
            {"name": "noun", "type": "N", "required": False,
             "description": "Subject noun (optional)"},
        ],
        lessons="L05–L13",
        bb_count=7,
    ),
    "T6": TemplateInfo(
        template_id="T6",
        name="Negation",
        english_pattern="No, [it is not X] / [alternative]",
        skiri_example="Kaki, kaki karitki.",
        english_example="No, it is not a rock.",
        slots=[
            {"name": "inner", "type": "TEXT", "required": True,
             "description": "The negated or alternative clause"},
        ],
        lessons="L01–L18",
        bb_count=13,
    ),
    "T7": TemplateInfo(
        template_id="T7",
        name="Affirmation",
        english_pattern="Yes, [statement]",
        skiri_example="Ahu', ti hitu'.",
        english_example="Yes, this is a feather.",
        slots=[
            {"name": "yes_word", "type": "YES", "required": False,
             "description": "Affirmation particle (ahu', hau, ilan')"},
            {"name": "inner", "type": "TEXT", "required": True,
             "description": "The affirmed statement"},
        ],
        lessons="L01–L20",
        bb_count=7,
    ),
    "T8": TemplateInfo(
        template_id="T8",
        name="I did/do/will [verb]",
        english_pattern="I [verb] ([object]) ([time/place])",
        skiri_example="Tatuks•at Pari.",
        english_example="I went to Pawnee.",
        slots=[
            {"name": "temporal", "type": "TEMPORAL", "required": False,
             "description": "Time word (rahesa' 'tomorrow', hiras 'at night', etc.)"},
            {"name": "adv_manner", "type": "ADV_MANNER", "required": False,
             "description": "Manner adverb (rariksisu 'hard', cikstit 'well')"},
            {"name": "object", "type": "N", "required": False,
             "description": "Object noun (for transitive verbs)"},
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "1sg conjugated verb form"},
            {"name": "locative", "type": "LOCATIVE", "required": False,
             "description": "Place (Pari, tuks•kaku', etc.)"},
        ],
        lessons="L08–L20",
        bb_count=27,
    ),
    "T9": TemplateInfo(
        template_id="T9",
        name="He/She [verb]s",
        english_pattern="[Subject] [verb]s ([object])",
        skiri_example="Pita ti•kuwutit rahurahki.",
        english_example="The man killed a deer.",
        slots=[
            {"name": "subject", "type": "N", "required": True,
             "description": "The subject (animate noun)"},
            {"name": "we_particle", "type": "BOOL", "required": False,
             "description": "Add 'we' particle (past/completed action)"},
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "3sg conjugated verb form"},
            {"name": "object", "type": "N", "required": False,
             "description": "Object noun (for transitive verbs)"},
            {"name": "temporal", "type": "TEMPORAL", "required": False,
             "description": "Time/season (pitsikat 'in winter', etc.)"},
        ],
        lessons="L06–L14",
        bb_count=13,
    ),
    "T10": TemplateInfo(
        template_id="T10",
        name="Imperative (Command)",
        english_pattern="[Do verb]! [Object]",
        skiri_example="Suks•teka .rikut.",
        english_example="Open the door.",
        slots=[
            {"name": "imp_particle", "type": "IMP", "required": False,
             "description": "Imperative particle (suks=2sg, siks=2pl)"},
            {"name": "verb_form", "type": "VERB_FORM", "required": True,
             "description": "Verb stem (imperative form)"},
            {"name": "object", "type": "N", "required": False,
             "description": "Object noun (optional)"},
        ],
        lessons="L12, L15, L20",
        bb_count=4,
    ),
}

# Yes-word options for T7
YES_WORDS = {
    "ahu'": "yes (standard)",
    "hau": "yes (variant)",
    "ilan'": "yes (variant, L11)",
}

# Imperative particles for T10
IMP_PARTICLES = {
    "suks": "2sg imperative (you, do it!)",
    "siks": "2pl imperative (you all, do it!)",
    "sisuks": "2du imperative (you two, do it!)",
    "stiks": "1sg imperative (let me...)",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the Skiri Pawnee database."""
    db_path = _find_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def lookup_entry(conn: sqlite3.Connection, headword: str) -> Optional[Dict]:
    """Look up a lexical entry by headword, with fuzzy fallbacks."""
    cur = conn.cursor()

    # 1. Exact match on headword or normalized_form
    cur.execute(
        "SELECT entry_id, headword, grammatical_class, verb_class, "
        "phonetic_form, simplified_pronunciation "
        "FROM lexical_entries WHERE headword = ? OR normalized_form = ?",
        (headword, headword),
    )
    row = cur.fetchone()
    if row:
        return dict(row)

    # 2. Try with/without final glottal stop (ʔ / ')
    variants = []
    if headword.endswith("ʔ"):
        variants.append(headword[:-1])
    elif headword.endswith("'"):
        variants.append(headword[:-1])
    else:
        variants.extend([headword + "ʔ", headword + "'"])

    for v in variants:
        cur.execute(
            "SELECT entry_id, headword, grammatical_class, verb_class, "
            "phonetic_form, simplified_pronunciation "
            "FROM lexical_entries WHERE headword = ? OR normalized_form = ?",
            (v, v),
        )
        row = cur.fetchone()
        if row:
            return dict(row)

    # 3. Check Blue Book attestations (BB forms may differ from dictionary)
    cur.execute(
        "SELECT entry_id FROM blue_book_attestations "
        "WHERE bb_skiri_form LIKE ? AND entry_id IS NOT NULL LIMIT 1",
        (f"%{headword}%",),
    )
    row = cur.fetchone()
    if row and row["entry_id"]:
        cur.execute(
            "SELECT entry_id, headword, grammatical_class, verb_class, "
            "phonetic_form, simplified_pronunciation "
            "FROM lexical_entries WHERE entry_id = ?",
            (row["entry_id"],),
        )
        row2 = cur.fetchone()
        if row2:
            return dict(row2)

    # 4. Prefix match (e.g., "pita" matches "pitaruʔ")
    cur.execute(
        "SELECT entry_id, headword, grammatical_class, verb_class, "
        "phonetic_form, simplified_pronunciation "
        "FROM lexical_entries WHERE headword LIKE ? "
        "AND grammatical_class IN ('N', 'N-KIN', 'N-DEP') "
        "ORDER BY length(headword) LIMIT 1",
        (headword + "%",),
    )
    row = cur.fetchone()
    if row:
        return dict(row)

    return None


def lookup_gloss(conn: sqlite3.Connection, entry_id: str) -> Optional[str]:
    """Get the primary English gloss for an entry."""
    cur = conn.cursor()
    cur.execute(
        "SELECT definition FROM glosses WHERE entry_id = ? ORDER BY sense_number LIMIT 1",
        (entry_id,),
    )
    row = cur.fetchone()
    return row["definition"] if row else None


def find_bb_attestation(
    conn: sqlite3.Connection, skiri_text: str
) -> Optional[str]:
    """Check if a sentence (or close variant) appears in Blue Book attestations."""
    cur = conn.cursor()
    # Normalize: strip punctuation, collapse whitespace, lowercase
    normalized = re.sub(r'[.,!?;:\'\"]', '', skiri_text).strip().lower()
    normalized = re.sub(r'\s+', ' ', normalized)

    cur.execute(
        "SELECT lesson_number, full_sentence_pawnee "
        "FROM blue_book_attestations "
        "WHERE full_sentence_pawnee IS NOT NULL AND full_sentence_pawnee != ''"
    )
    matches = []
    for row in cur.fetchall():
        bb_norm = re.sub(r'[.,!?;:\'\"]', '', row["full_sentence_pawnee"]).strip().lower()
        bb_norm = re.sub(r'\s+', ' ', bb_norm)
        # Exact or close match (ignore BB OCR artifacts like •, spaces)
        bb_clean = bb_norm.replace('•', '').replace(' ', '')
        query_clean = normalized.replace('•', '').replace(' ', '')
        if bb_clean == query_clean or bb_norm == normalized:
            matches.append(f"L{row['lesson_number']:02d}")

    if matches:
        return ", ".join(sorted(set(matches)))
    return None


# ---------------------------------------------------------------------------
# Assembly functions — one per template
# ---------------------------------------------------------------------------
def _assemble_t1(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T1: Identification — 'ti [NOUN]'"""
    noun = slots.get("noun", "").strip()
    if not noun:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T1",
            template_name="Identification", confidence="LOW",
            error="Noun slot is required",
        )

    entry = lookup_entry(conn, noun)
    gloss = ""
    entry_id = None
    if entry:
        entry_id = entry["entry_id"]
        gloss = lookup_gloss(conn, entry_id) or noun

    sentence = f"ti {noun}"
    english = f"This is {gloss}" if gloss else f"This is {noun}"

    breakdown = [
        MorphemeChip(form="ti", gloss="this is / it is", role="PARTICLE"),
        MorphemeChip(form=noun, gloss=gloss or noun, role="NOUN", entry_id=entry_id),
    ]

    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else ("MEDIUM" if entry else "LOW")

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T1",
        template_name="Identification",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
    )


def _assemble_t2(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T2: Descriptive — '[NOUN] ti [VD]'"""
    noun = slots.get("noun", "").strip()
    vd = slots.get("vd", "").strip()

    if not noun or not vd:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T2",
            template_name="Descriptive", confidence="LOW",
            error="Both noun and descriptive verb (vd) slots are required",
        )

    noun_entry = lookup_entry(conn, noun)
    vd_entry = lookup_entry(conn, vd)

    noun_gloss = ""
    vd_gloss = ""
    noun_eid = None
    vd_eid = None

    if noun_entry:
        noun_eid = noun_entry["entry_id"]
        noun_gloss = lookup_gloss(conn, noun_eid) or noun
    if vd_entry:
        vd_eid = vd_entry["entry_id"]
        vd_gloss = lookup_gloss(conn, vd_eid) or vd

    # Default word order: NOUN ti VD
    sentence = f"{noun} ti {vd}"
    english = f"The {noun_gloss or noun} is {vd_gloss or vd}"

    breakdown = [
        MorphemeChip(form=noun, gloss=noun_gloss or noun, role="SUBJECT", entry_id=noun_eid),
        MorphemeChip(form="ti", gloss="is (indicative)", role="PARTICLE"),
        MorphemeChip(form=vd, gloss=vd_gloss or vd, role="VERB", entry_id=vd_eid),
    ]

    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else ("MEDIUM" if noun_entry and vd_entry else "LOW")

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T2",
        template_name="Descriptive",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Both 'NOUN ti VD' and 'ti VD NOUN' are attested (L09)",
    )


def _assemble_t3(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T3: Yes/No Question — 'ka [VERB_FORM] [NOUN]?'"""
    verb_form = slots.get("verb_form", "").strip()
    noun = slots.get("noun", "").strip()

    if not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T3",
            template_name="Yes/No Question", confidence="LOW",
            error="Verb form slot is required",
        )

    parts = ["ka", verb_form]
    if noun:
        parts.append(noun)
    sentence = " ".join(parts) + "?"

    # Build breakdown
    breakdown = [
        MorphemeChip(form="ka", gloss="(yes/no question)", role="PARTICLE"),
        MorphemeChip(form=verb_form, gloss="verb (absolutive)", role="VERB"),
    ]
    if noun:
        noun_entry = lookup_entry(conn, noun)
        noun_gloss = ""
        if noun_entry:
            noun_gloss = lookup_gloss(conn, noun_entry["entry_id"]) or noun
        breakdown.append(
            MorphemeChip(
                form=noun, gloss=noun_gloss or noun, role="SUBJECT",
                entry_id=noun_entry["entry_id"] if noun_entry else None,
            )
        )

    english = f"Is {noun or 'it'} {verb_form}?"
    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T3",
        template_name="Yes/No Question",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Adverb (e.g., cikstit) can precede ka",
    )


def _assemble_t4(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T4: What Question — '(SUBJECT) kirike [VERB_FORM]?'"""
    subject = slots.get("subject", "").strip()
    verb_form = slots.get("verb_form", "").strip()

    if not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T4",
            template_name="What Question", confidence="LOW",
            error="Verb form slot is required",
        )

    parts = []
    if subject:
        parts.append(subject)
    parts.extend(["kirike", verb_form])
    sentence = " ".join(parts) + "?"

    breakdown = []
    if subject:
        subj_entry = lookup_entry(conn, subject)
        subj_gloss = ""
        if subj_entry:
            subj_gloss = lookup_gloss(conn, subj_entry["entry_id"]) or subject
        breakdown.append(
            MorphemeChip(
                form=subject, gloss=subj_gloss or subject, role="SUBJECT",
                entry_id=subj_entry["entry_id"] if subj_entry else None,
            )
        )
    breakdown.append(MorphemeChip(form="kirike", gloss="what", role="PARTICLE"))
    breakdown.append(MorphemeChip(form=verb_form, gloss="verb (absolutive)", role="VERB"))

    subj_str = f"the {subject}" if subject else "it"
    english = f"What is {subj_str} doing?"
    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T4",
        template_name="What Question",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Subject precedes kirike when present",
    )


def _assemble_t5(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T5: Where Question — 'kiru [VERB_FORM] [NOUN]?'"""
    verb_form = slots.get("verb_form", "").strip()
    noun = slots.get("noun", "").strip()

    if not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T5",
            template_name="Where Question", confidence="LOW",
            error="Verb form slot is required",
        )

    parts = ["kiru", verb_form]
    if noun:
        parts.append(noun)
    sentence = " ".join(parts) + "?"

    breakdown = [
        MorphemeChip(form="kiru", gloss="where", role="PARTICLE"),
        MorphemeChip(form=verb_form, gloss="verb (absolutive)", role="VERB"),
    ]
    if noun:
        noun_entry = lookup_entry(conn, noun)
        noun_gloss = ""
        if noun_entry:
            noun_gloss = lookup_gloss(conn, noun_entry["entry_id"]) or noun
        breakdown.append(
            MorphemeChip(
                form=noun, gloss=noun_gloss or noun, role="SUBJECT",
                entry_id=noun_entry["entry_id"] if noun_entry else None,
            )
        )

    english = f"Where did {noun or 'it'} go/is?"
    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T5",
        template_name="Where Question",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Also 'kirti' for 'where (destination)'",
    )


def _assemble_t6(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T6: Negation — 'kaki, [INNER]'"""
    inner = slots.get("inner", "").strip()
    if not inner:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T6",
            template_name="Negation", confidence="LOW",
            error="Inner clause is required",
        )

    sentence = f"kaki', {inner}"

    breakdown = [
        MorphemeChip(form="kaki'", gloss="no / not", role="PARTICLE"),
        MorphemeChip(form=inner, gloss="(clause)", role="CLAUSE"),
    ]

    english = f"No, {inner}"
    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T6",
        template_name="Negation",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Often followed by a positive restatement",
    )


def _assemble_t7(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T7: Affirmation — '[YES], [INNER]'"""
    yes_word = slots.get("yes_word", "ahu'").strip()
    inner = slots.get("inner", "").strip()

    if not inner:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T7",
            template_name="Affirmation", confidence="LOW",
            error="Inner statement is required",
        )

    if yes_word not in YES_WORDS:
        yes_word = "ahu'"

    sentence = f"{yes_word}, {inner}"

    breakdown = [
        MorphemeChip(form=yes_word, gloss="yes", role="PARTICLE"),
        MorphemeChip(form=inner, gloss="(statement)", role="CLAUSE"),
    ]

    english = f"Yes, {inner}"
    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T7",
        template_name="Affirmation",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
    )


def _assemble_t8(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T8: 1sg Declarative — '(TEMPORAL) (ADV_MANNER) [1SG_VERB] (OBJECT) (LOCATIVE)'"""
    temporal = slots.get("temporal", "").strip()
    adv_manner = slots.get("adv_manner", "").strip()
    obj = slots.get("object", "").strip()
    verb_form = slots.get("verb_form", "").strip()
    locative = slots.get("locative", "").strip()

    if not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T8",
            template_name="I did/do/will [verb]", confidence="LOW",
            error="Verb form slot is required",
        )

    parts = []
    breakdown = []

    # CLAUSE-INITIAL temporals come first
    if temporal:
        parts.append(temporal)
        breakdown.append(MorphemeChip(form=temporal, gloss="(time)", role="ADVERB"))

    # PRECEDES-VERB manner adverbs come before the verb
    # BB evidence: "Rariksisu tatutsiks•a•wahri'." (L18)
    if adv_manner:
        parts.append(adv_manner)
        breakdown.append(MorphemeChip(form=adv_manner, gloss="(manner)", role="ADVERB"))

    # Verb
    # In BB 1sg declaratives, verb typically precedes object:
    #   Tatuks•a kisatski  "I ate meat" (L11)
    #   Tah•raspe' asaki   "I'm looking for my dog" (L08)
    # But quantified objects precede: Tawit kaas tatutak•erit (L13)
    parts.append(verb_form)
    breakdown.append(MorphemeChip(form=verb_form, gloss="I (verb)", role="VERB"))

    if obj:
        parts.append(obj)
        obj_entry = lookup_entry(conn, obj)
        obj_gloss = ""
        if obj_entry:
            obj_gloss = lookup_gloss(conn, obj_entry["entry_id"]) or obj
        breakdown.append(
            MorphemeChip(
                form=obj, gloss=obj_gloss or obj, role="OBJECT",
                entry_id=obj_entry["entry_id"] if obj_entry else None,
            )
        )

    if locative:
        parts.append(locative)
        breakdown.append(MorphemeChip(form=locative, gloss="(place)", role="LOCATIVE"))

    sentence = " ".join(parts)

    # Build English gloss
    eng_parts = ["I"]
    eng_parts.append(verb_form)  # placeholder
    if adv_manner:
        eng_parts.append(f"({adv_manner})")
    if obj:
        eng_parts.append(obj)
    if locative:
        eng_parts.append(f"to {locative}")
    english = " ".join(eng_parts)

    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T8",
        template_name="I did/do/will [verb]",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="Temporal can be clause-initial or clause-final (both attested L17). "
                        "Manner adverbs precede verb (L18: rariksisu tatutsiks•a•wahri').",
    )


def _assemble_t9(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T9: 3sg Narrative — '[SUBJECT] (we) [3SG_VERB] [OBJECT] (TEMPORAL)'"""
    subject = slots.get("subject", "").strip()
    verb_form = slots.get("verb_form", "").strip()
    obj = slots.get("object", "").strip()
    we_particle = slots.get("we_particle", "").strip().lower() in ("true", "1", "yes")
    temporal = slots.get("temporal", "").strip()

    if not subject or not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T9",
            template_name="He/She [verb]s", confidence="LOW",
            error="Subject and verb form are required",
        )

    parts = [subject]
    breakdown = []

    subj_entry = lookup_entry(conn, subject)
    subj_gloss = ""
    if subj_entry:
        subj_gloss = lookup_gloss(conn, subj_entry["entry_id"]) or subject
    breakdown.append(
        MorphemeChip(
            form=subject, gloss=subj_gloss or subject, role="SUBJECT",
            entry_id=subj_entry["entry_id"] if subj_entry else None,
        )
    )

    # 'we' particle marks completed/past action
    # BB: "Rahurahki we tut•awi'at" (L09), "Kiwaku we tu'h•kuksas" (L09)
    # Position: between subject and verb
    if we_particle:
        parts.append("we")
        breakdown.append(MorphemeChip(form="we", gloss="(completed action)", role="PARTICLE"))

    parts.append(verb_form)
    breakdown.append(MorphemeChip(form=verb_form, gloss="he/she (verb)", role="VERB"))

    if obj:
        parts.append(obj)
        obj_entry = lookup_entry(conn, obj)
        obj_gloss = ""
        if obj_entry:
            obj_gloss = lookup_gloss(conn, obj_entry["entry_id"]) or obj
        breakdown.append(
            MorphemeChip(
                form=obj, gloss=obj_gloss or obj, role="OBJECT",
                entry_id=obj_entry["entry_id"] if obj_entry else None,
            )
        )

    # Temporal goes clause-final in T9
    # BB: "Pita ti•kuwutit rahurahki pitsikat" (L09)
    if temporal:
        parts.append(temporal)
        breakdown.append(MorphemeChip(form=temporal, gloss="(time)", role="ADVERB"))

    sentence = " ".join(parts)

    eng_parts = [f"The {subj_gloss or subject}"]
    eng_parts.append(verb_form)
    if obj:
        eng_parts.append(f"the {obj}")
    if temporal:
        eng_parts.append(f"({temporal})")
    english = " ".join(eng_parts)

    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T9",
        template_name="He/She [verb]s",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
        word_order_note="SOV default; object can follow verb (L14). "
                        "'we' particle marks completed action (L09). "
                        "Temporal clause-final (L09: pitsikat).",
    )


def _assemble_t10(conn: sqlite3.Connection, **slots) -> TemplateResult:
    """T10: Imperative — '[IMP]•[VERB] [OBJECT]'"""
    imp = slots.get("imp_particle", "suks").strip()
    verb_form = slots.get("verb_form", "").strip()
    obj = slots.get("object", "").strip()

    if not verb_form:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id="T10",
            template_name="Imperative (Command)", confidence="LOW",
            error="Verb form slot is required",
        )

    if imp not in IMP_PARTICLES:
        imp = "suks"

    # Imperative particle is a proclitic — joins to verb
    verb_with_imp = f"{imp}•{verb_form}"

    parts = [verb_with_imp]
    breakdown = [
        MorphemeChip(form=imp, gloss="(imperative)", role="PARTICLE"),
        MorphemeChip(form=verb_form, gloss="(verb stem)", role="VERB"),
    ]

    if obj:
        parts.append(obj)
        obj_entry = lookup_entry(conn, obj)
        obj_gloss = ""
        if obj_entry:
            obj_gloss = lookup_gloss(conn, obj_entry["entry_id"]) or obj
        breakdown.append(
            MorphemeChip(
                form=obj, gloss=obj_gloss or obj, role="OBJECT",
                entry_id=obj_entry["entry_id"] if obj_entry else None,
            )
        )

    sentence = " ".join(parts)
    english = f"(Do) {verb_form}" + (f" {obj}" if obj else "") + "!"

    bb = find_bb_attestation(conn, sentence)
    confidence = "HIGH" if bb else "MEDIUM"

    return TemplateResult(
        skiri_sentence=sentence,
        english_gloss=english,
        template_id="T10",
        template_name="Imperative (Command)",
        confidence=confidence,
        morpheme_breakdown=breakdown,
        bb_attestation=bb,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
_ASSEMBLERS = {
    "T1": _assemble_t1,
    "T2": _assemble_t2,
    "T3": _assemble_t3,
    "T4": _assemble_t4,
    "T5": _assemble_t5,
    "T6": _assemble_t6,
    "T7": _assemble_t7,
    "T8": _assemble_t8,
    "T9": _assemble_t9,
    "T10": _assemble_t10,
}


def assemble(template_id: str, **slots) -> TemplateResult:
    """
    Assemble a sentence from a template and slot values.

    Args:
        template_id: One of T1–T10
        **slots: Named slot values (varies by template)

    Returns:
        TemplateResult with assembled sentence, breakdown, and confidence
    """
    if template_id not in _ASSEMBLERS:
        return TemplateResult(
            skiri_sentence="", english_gloss="", template_id=template_id,
            template_name="Unknown", confidence="LOW",
            error=f"Unknown template: {template_id}. Use T1–T10.",
        )

    conn = get_db_connection()
    try:
        return _ASSEMBLERS[template_id](conn, **slots)
    finally:
        conn.close()


def list_templates() -> List[Dict[str, Any]]:
    """Return metadata for all templates (for UI display)."""
    return [
        {
            "template_id": t.template_id,
            "name": t.name,
            "english_pattern": t.english_pattern,
            "skiri_example": t.skiri_example,
            "english_example": t.english_example,
            "slots": t.slots,
            "lessons": t.lessons,
            "bb_count": t.bb_count,
        }
        for t in TEMPLATES.values()
    ]


def get_slot_options(template_id: str, slot_name: str, bb_only: bool = True) -> List[Dict]:
    """
    Get curated dropdown options for a template slot.

    Args:
        template_id: T1–T10
        slot_name: The slot name (e.g., "temporal", "adv_manner", "yes_word")
        bb_only: If True, only return BB-attested options

    Returns:
        List of dicts with keys: skiri_form, english, position_rule, bb_lessons
    """
    try:
        from template_slot_fillers import (
            SLOT_FILLERS, TEMPLATE_SLOT_MAP, BB_VOCABULARY_ALIASES,
        )
    except ImportError:
        try:
            from scripts.template_slot_fillers import (
                SLOT_FILLERS, TEMPLATE_SLOT_MAP, BB_VOCABULARY_ALIASES,
            )
        except ImportError:
            return []

    # Map slot names to filler categories
    SLOT_NAME_TO_CATEGORY = {
        "temporal": "TEMPORAL",
        "adv_manner": "ADV_MANNER",
        "yes_word": "YES",
        "imp_particle": "IMPERATIVE",
        "numeral": "NUMERAL",
    }

    category = SLOT_NAME_TO_CATEGORY.get(slot_name)
    if not category:
        return []

    # Check this category is valid for this template
    valid_cats = TEMPLATE_SLOT_MAP.get(template_id, [])
    if category not in valid_cats:
        return []

    fillers = SLOT_FILLERS.get(category, [])
    if bb_only:
        fillers = [f for f in fillers if f.bb_lessons]

    return [
        {
            "skiri_form": f.skiri_form,
            "english": f.english,
            "position_rule": f.position_rule,
            "bb_lessons": f.bb_lessons,
            "bb_example": f.bb_example_skiri,
        }
        for f in fillers
    ]


# ---------------------------------------------------------------------------
# Validation test suite — 27 BB-attested test cases
# ---------------------------------------------------------------------------
VALIDATION_TESTS = [
    # (template_id, slots_dict, expected_skiri_output, description)

    # T1: Identification
    ("T1", {"noun": "hitu'"}, "ti hitu'", "This is a feather (L01)"),
    ("T1", {"noun": "Rihita"}, "ti Rihita", "He's Ponca (L13)"),
    ("T1", {"noun": "Pasuhara"}, "ti Pasuhara", "He's Oto (L13)"),

    # T2: Descriptive
    ("T2", {"noun": "rakis", "vd": "pahaat"}, "rakis ti pahaat",
     "The stick is red (L02)"),
    ("T2", {"noun": "kiwaku", "vd": "pahaat"}, "kiwaku ti pahaat",
     "The fox is red (L09)"),
    ("T2", {"noun": "rikutski", "vd": "pahaat"}, "rikutski ti pahaat",
     "The bird is red (L09)"),

    # T3: Yes/No question
    ("T3", {"verb_form": "rii", "noun": "hitu'"}, "ka rii hitu'?",
     "Is this a feather? (L01)"),
    ("T3", {"verb_form": "ra•pahaat", "noun": "rakis"},
     "ka ra•pahaat rakis?", "Is the stick red? (L02)"),
    ("T3", {"verb_form": "ru", "noun": "karitki"}, "ka ru karitki?",
     "Is this a rock? (L01)"),

    # T4: What question
    ("T4", {"verb_form": "ru'"}, "kirike ru'?", "What is it? (L01)"),
    ("T4", {"subject": "pita", "verb_form": "rut•ari'"},
     "pita kirike rut•ari'?", "What is the man doing? (L06)"),
    ("T4", {"verb_form": "ras•taspe'"}, "kirike ras•taspe'?",
     "What are you looking for? (L08)"),

    # T5: Where question
    ("T5", {"verb_form": "rasuks•at"}, "kiru rasuks•at?",
     "Where did you go? (L13)"),
    ("T5", {"verb_form": "ruks•ku'"}, "kiru ruks•ku'?",
     "Where was it? (L08)"),

    # T6: Negation
    ("T6", {"inner": "kaki karitki"}, "kaki', kaki karitki",
     "No, it is not a rock (L01)"),

    # T7: Affirmation
    ("T7", {"yes_word": "ahu'", "inner": "ti hitu'"},
     "ahu', ti hitu'", "Yes, this is a feather (L01)"),
    ("T7", {"yes_word": "ahu'", "inner": "rakis ti pahaat"},
     "ahu', rakis ti pahaat", "Yes, the stick is red (L02)"),

    # T8: 1sg declarative
    ("T8", {"verb_form": "tatuks•at"}, "tatuks•at",
     "I went (L13)"),
    ("T8", {"verb_form": "tatuks•at", "locative": "Pari"},
     "tatuks•at Pari", "I went to Pawnee (L13)"),
    ("T8", {"verb_form": "tatuks•a", "object": "kisatski"},
     "tatuks•a kisatski", "I ate meat (L11)"),

    # T9: 3sg narrative
    ("T9", {"subject": "pita", "verb_form": "tiwari'"},
     "pita tiwari'", "The man is walking (L06)"),
    ("T9", {"subject": "rikutski", "verb_form": "ti•waktahu'"},
     "rikutski ti•waktahu'", "The bird is singing (L14)"),
    ("T9", {"subject": "asaki", "verb_form": "tirah•kI wat"},
     "asaki tirah•kI wat", "The dog barked (L14)"),

    # T10: Imperative
    ("T10", {"imp_particle": "suks", "verb_form": "pitit"},
     "suks•pitit", "Sit down (L20)"),

    # === New tests for slot filler integration ===

    # T8 with manner adverb (L18: Rariksisu tatutsiks•a•wahri')
    ("T8", {"adv_manner": "rariksisu", "verb_form": "tatutsiks•a•wahri'"},
     "rariksisu tatutsiks•a•wahri'",
     "I've been working hard (L18 — ADV_MANNER slot)"),

    # T9 with 'we' particle (L09: Rahurahki we tut•awi'at Karit•kutsu')
    ("T9", {"subject": "kiwaku", "we_particle": "true", "verb_form": "tu'h•kuksas"},
     "kiwaku we tu'h•kuksas",
     "The fox ran away (L09 — we particle)"),

    # T9 with temporal (L09: Pita ti•kuwutit rahurahki pitsikat)
    ("T9", {"subject": "pita", "verb_form": "ti•kuwutit", "object": "rahurahki",
            "temporal": "pitsikat"},
     "pita ti•kuwutit rahurahki pitsikat",
     "The man killed a deer, in the winter (L09 — temporal slot)"),
]


def run_validation(verbose: bool = True) -> Tuple[int, int, List[str]]:
    """
    Run all validation tests and report results.

    Returns:
        (passed, total, failure_messages)
    """
    conn = get_db_connection()
    passed = 0
    total = len(VALIDATION_TESTS)
    failures = []

    for template_id, slots, expected, desc in VALIDATION_TESTS:
        result = _ASSEMBLERS[template_id](conn, **slots)
        actual = result.skiri_sentence.strip()
        expected_clean = expected.strip()

        # Normalize for comparison: lowercase, collapse spaces
        actual_norm = re.sub(r'\s+', ' ', actual.lower().strip(' .'))
        expected_norm = re.sub(r'\s+', ' ', expected_clean.lower().strip(' .'))

        if actual_norm == expected_norm:
            passed += 1
            if verbose:
                bb_tag = f" [BB: {result.bb_attestation}]" if result.bb_attestation else ""
                print(f"  ✅ {template_id} {desc}{bb_tag}")
        else:
            msg = f"  ❌ {template_id} {desc}: expected '{expected_clean}', got '{actual}'"
            failures.append(msg)
            if verbose:
                print(msg)

    conn.close()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Results: {passed}/{total} passed ({100*passed/total:.0f}%)")
        if failures:
            print(f"\nFailures ({len(failures)}):")
            for f in failures:
                print(f)

    return passed, total, failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Skiri Pawnee sentence template assembly engine"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Test command
    subparsers.add_parser("test", help="Run validation test suite")

    # List command
    subparsers.add_parser("list", help="List all templates")

    # Assemble command
    asm = subparsers.add_parser("assemble", help="Assemble a sentence")
    asm.add_argument("--template", "-t", required=True, help="Template ID (T1–T10)")
    asm.add_argument("--noun", help="Noun slot")
    asm.add_argument("--vd", help="Descriptive verb slot")
    asm.add_argument("--verb_form", help="Pre-conjugated verb form")
    asm.add_argument("--subject", help="Subject noun")
    asm.add_argument("--object", help="Object noun")
    asm.add_argument("--temporal", help="Time word")
    asm.add_argument("--locative", help="Place word")
    asm.add_argument("--inner", help="Inner clause (for T6/T7 wrappers)")
    asm.add_argument("--yes_word", help="Affirmation word (for T7)")
    asm.add_argument("--imp_particle", help="Imperative particle (for T10)")
    asm.add_argument("--adv_manner", help="Manner adverb (rariksisu, cikstit)")
    asm.add_argument("--we_particle", help="Add 'we' particle for T9 (true/false)")
    asm.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "test" or (not args.command and "--test" in sys.argv):
        print("Phase 3.2a — Sentence Template Validation")
        print("=" * 60)
        run_validation(verbose=True)

    elif args.command == "list":
        templates = list_templates()
        for t in templates:
            print(f"\n{t['template_id']}: {t['name']}")
            print(f"  Pattern: {t['english_pattern']}")
            print(f"  Example: {t['skiri_example']} = {t['english_example']}")
            print(f"  Lessons: {t['lessons']} ({t['bb_count']} attestations)")
            print(f"  Slots: {', '.join(s['name'] for s in t['slots'])}")

    elif args.command == "assemble":
        # Gather slots from CLI args
        slot_names = [
            "noun", "vd", "verb_form", "subject", "object",
            "temporal", "locative", "inner", "yes_word", "imp_particle",
            "adv_manner", "we_particle",
        ]
        slots = {}
        for name in slot_names:
            val = getattr(args, name, None)
            if val:
                slots[name] = val

        result = assemble(args.template, **slots)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            if result.error:
                print(f"Error: {result.error}")
            else:
                print(f"\n  Skiri:  {result.skiri_sentence}")
                print(f"  English: {result.english_gloss}")
                print(f"  Confidence: {result.confidence}")
                if result.bb_attestation:
                    print(f"  Blue Book: {result.bb_attestation}")
                if result.word_order_note:
                    print(f"  Note: {result.word_order_note}")
                print(f"\n  Morpheme breakdown:")
                for m in result.morpheme_breakdown:
                    print(f"    [{m.role:10s}] {m.form:25s} = {m.gloss}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
