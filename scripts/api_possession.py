"""
Phase 3.1.5 — Possession API Route
====================================

Flask blueprint serving /api/possession/<headword> for the
_possession_widget.html frontend.

Wire into your app:

    from api_possession import possession_bp
    app.register_blueprint(possession_bp)

Expects possession_engine.py to be importable (same directory or on PYTHONPATH).
"""

from flask import Blueprint, jsonify, request
from possession_engine import (
    generate_possessive,
    generate_paradigm_table,
    generate_locative,
    generate_instrumental,
    _load_kinship,
    _person_label,
    KNOWN_BODY_PART_STEMS,
    KNOWN_RELATIONAL_STEMS,
)

possession_bp = Blueprint('possession', __name__)


# ---------------------------------------------------------------------------
# Noun class lookup — stub.  Replace with your actual DB lookup.
# ---------------------------------------------------------------------------
# In production this should query your lexical_entries table:
#     SELECT grammatical_class FROM lexical_entries WHERE headword = ?
# For now, accepts noun_class from query param or guesses from engine data.

def _lookup_noun_class(headword: str) -> str:
    """
    Look up the grammatical class for a headword.
    Replace this stub with a real DB query.
    """
    # Check if it's a kinship term
    kin = _load_kinship()
    if headword in kin or headword.rstrip("ʔ") in kin:
        return "N-KIN"
    # Check if it's a known body part or relational stem
    from possession_engine import extract_noun_stem
    stem, _ = extract_noun_stem(headword)
    if stem in KNOWN_BODY_PART_STEMS:
        return "N-DEP"
    if stem in KNOWN_RELATIONAL_STEMS:
        return "N-DEP"
    # Default
    return "N"


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@possession_bp.route('/api/possession/<path:headword>')
def get_possession(headword: str):
    """
    Return the full possessive paradigm for a noun.

    Query params:
        noun_class  — override grammatical class (N, N-DEP, N-KIN)
        type        — override possession system (kinship, body_part, agent, patient)

    Response JSON shape (consumed by _possession_widget.html):
    {
        "headword": "paksuʔ",
        "system": "body_part",
        "system_label": "Body Part Possession (ri- PHY.POSS in verb)",
        "construction_note": "MODE + ri(PHY.POSS) + AGENT + NOUN_STEM + ...",
        "persons": [
            {
                "person": "1sg",
                "label": "my",
                "form": "tiritpaksku",
                "morphemes": "ti(IND.3) + ri(PHY.POSS) + t(1SG.A) + ...",
                "morpheme_chips": [
                    {"m": "ti", "l": "IND.3", "role": "mode"},
                    {"m": "ri", "l": "PHY.POSS", "role": "poss"},
                    ...
                ],
                "gloss": "here is my head (sitting)",
                "confidence": "medium",
                "is_attested": false
            },
            ...
        ],
        "locative_forms": [
            {"type": "locative", "form": "paksbiriʔ", "morphemes": "...", "gloss": "..."},
            ...
        ]
    }
    """
    try:
        noun_class = request.args.get('noun_class') or _lookup_noun_class(headword)
        poss_type = request.args.get('type') or None

        data = generate_paradigm_table(
            headword,
            noun_class=noun_class,
            possession_type=poss_type,
        )

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Single-form endpoint (optional — for HTMX partial updates)
# ---------------------------------------------------------------------------

@possession_bp.route('/api/possession/<path:headword>/<person>')
def get_possession_single(headword: str, person: str):
    """Return a single possessive form (e.g. /api/possession/paksuʔ/1sg)."""
    try:
        noun_class = request.args.get('noun_class') or _lookup_noun_class(headword)
        poss_type = request.args.get('type') or None

        result = generate_possessive(
            headword,
            person=person,
            noun_class=noun_class,
            possession_type=poss_type,
        )

        return jsonify({
            "person": result.person,
            "label": _person_label(result.person),
            "form": result.surface_form,
            "system": result.system,
            "morphemes": " + ".join(
                f"{m}({l})" for m, l in
                zip(result.morpheme_sequence, result.morpheme_labels)
            ),
            "gloss": result.gloss,
            "confidence": result.confidence,
            "is_attested": result.is_attested,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Locative endpoint (optional — standalone case-form lookup)
# ---------------------------------------------------------------------------

@possession_bp.route('/api/locative/<path:headword>')
def get_locative(headword: str):
    """Return locative and instrumental forms for a noun."""
    try:
        noun_class = request.args.get('noun_class')
        is_tribal = request.args.get('tribal', '').lower() in ('1', 'true', 'yes')
        plural = request.args.get('plural', '').lower() in ('1', 'true', 'yes')

        loc = generate_locative(headword, noun_class=noun_class,
                                is_tribal=is_tribal, plural=plural)
        inst = generate_instrumental(headword, noun_class=noun_class)

        return jsonify({
            "headword": headword,
            "locative": {
                "form": loc.surface_form,
                "type": loc.form_type,
                "noun_class": loc.noun_class,
                "morphemes": " + ".join(
                    f"{m}({l})" for m, l in
                    zip(loc.morpheme_sequence, loc.morpheme_labels)
                ),
                "gloss": loc.gloss,
            },
            "instrumental": {
                "form": inst.surface_form,
                "morphemes": " + ".join(
                    f"{m}({l})" for m, l in
                    zip(inst.morpheme_sequence, inst.morpheme_labels)
                ),
                "gloss": inst.gloss,
            },
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
