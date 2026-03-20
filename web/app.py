"""
Phase 4.1 — Flask web application for the Skiri Pawnee dictionary.

Usage:
    python web/app.py                    # default: localhost:5000
    python web/app.py --port 8080        # custom port
"""

import argparse
import hashlib
import math
import os
import re
import sys
from datetime import date

from flask import Flask, g, jsonify, render_template, request, abort
from markupsafe import Markup

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from web.db import SkiriWebDictionary
from web.search import search_combined
from web.flashcards import generate_all_sets

DATABASE = os.path.join(PROJECT_ROOT, "skiri_pawnee.db")

app = Flask(__name__)
app.config["DATABASE"] = DATABASE


# ------------------------------------------------------------------
# Jinja template filters
# ------------------------------------------------------------------

_UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")


@app.template_filter("format_pitch")
def format_pitch(pronunciation: str) -> Markup:
    """Wrap UPPERCASE pitch-accent syllables in <span class="pitch-high">.

    If the pronunciation has no uppercase (pitch not marked), append a
    small note so learners know the absence is intentional.
    """
    if not pronunciation:
        return Markup("")
    has_upper = any(c.isupper() for c in pronunciation)
    if has_upper:
        html = _UPPER_RUN_RE.sub(r'<span class="pitch-high">\1</span>', pronunciation)
        return Markup(html)
    # All-lowercase: display as-is with "pitch not marked" note
    return Markup(
        f'{pronunciation}'
        ' <span class="pitch-unmarked">(pitch not marked)</span>'
    )


# ------------------------------------------------------------------
# Headword set cache (for example filtering)
# ------------------------------------------------------------------

_headword_set_cache = None

def _get_headword_set() -> set:
    """Lazily build and cache the normalized headword set for example filtering."""
    global _headword_set_cache
    if _headword_set_cache is not None:
        return _headword_set_cache

    from scripts.example_filter import _normalize_for_match
    db = SkiriWebDictionary(DATABASE)
    try:
        raw_headwords = db.get_all_headwords()
        _headword_set_cache = set()
        for hw in raw_headwords:
            norm = _normalize_for_match(hw)
            _headword_set_cache.add(norm)
            # Also add without trailing glottal for fuzzy matching
            if norm.endswith("'"):
                _headword_set_cache.add(norm[:-1])
    finally:
        db.close()
    return _headword_set_cache


def _filter_entry_examples(entry_data: dict) -> dict:
    """
    Filter examples and BB attestations on an entry to remove
    false substring matches (e.g., 'kirike' pollution on 'kiri').

    Modifies entry_data in place and returns it.
    """
    from scripts.example_filter import matches_headword
    from scripts.possession_engine import extract_noun_stem

    hw_set = _get_headword_set()
    entry = entry_data.get("entry")
    if not entry:
        return entry_data

    headword = entry.headword if hasattr(entry, 'headword') else ""
    if not headword:
        return entry_data

    stem, _ = extract_noun_stem(headword)

    # --- Filter dictionary examples ---
    if hasattr(entry, 'examples') and entry.examples:
        filtered = []
        for ex in entry.examples:
            skiri_text = ex.skiri_text if hasattr(ex, 'skiri_text') else ""
            if not skiri_text:
                filtered.append(ex)  # keep examples with no Skiri text
                continue
            if matches_headword(headword, skiri_text, hw_set, stem=stem):
                filtered.append(ex)
        entry.examples = filtered

    # --- Filter Blue Book attestations ---
    bb_info = entry_data.get("bb_info")
    if bb_info and bb_info.get("attestations"):
        filtered_bb = []
        for att in bb_info["attestations"]:
            bb_form = att.get("bb_skiri_form", "")
            context = att.get("context_type", "")

            # Always keep vocabulary listings (BASIC_WORDS, ADDITIONAL_WORDS)
            # — these are pre-matched by the BB extraction pipeline
            if context in ("BASIC_WORDS", "ADDITIONAL_WORDS"):
                filtered_bb.append(att)
                continue

            # For dialogues, phrases, grammar examples: check the Skiri form
            if bb_form and matches_headword(headword, bb_form, hw_set, stem=stem):
                filtered_bb.append(att)
                continue

            # If bb_form is empty or very short, keep it (metadata row)
            if not bb_form or len(bb_form) < 3:
                filtered_bb.append(att)

        bb_info["attestations"] = filtered_bb

    return entry_data


# ------------------------------------------------------------------
# DB lifecycle
# ------------------------------------------------------------------

def get_db() -> SkiriWebDictionary:
    if "db" not in g:
        g.db = SkiriWebDictionary(app.config["DATABASE"])
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()


# ------------------------------------------------------------------
# Ensure UTF-8 responses
# ------------------------------------------------------------------

@app.after_request
def set_charset(response):
    if "text/html" in response.content_type:
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


# ------------------------------------------------------------------
# Template helpers
# ------------------------------------------------------------------

@app.context_processor
def inject_helpers():
    return {
        "abs": abs,
        "min": min,
        "max": max,
    }


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/")
def index():
    db = get_db()
    stats = db.get_stats()
    word_of_day = db.get_word_of_day()
    tags = db.get_all_tags()
    wotd_date = date.today().strftime("%b %d")

    # Quick-access hint chips for the search bar
    quick_words = [
        {"skiri": "raawi", "en": "sun"},
        {"skiri": "aatius", "en": "father"},
        {"skiri": "piita", "en": "man"},
        {"skiri": "capaat", "en": "woman"},
    ]

    return render_template(
        "index.html",
        stats=stats,
        word_of_day=word_of_day,
        wotd_date=wotd_date,
        tags=tags,
        quick_words=quick_words,
    )


@app.route("/search")
def search_page():
    db = get_db()
    query = request.args.get("q", "").strip()
    lang = request.args.get("lang", "auto")
    gram_class = request.args.get("class", None)
    tag = request.args.get("tag", None)
    verb_class = request.args.get("verb_class", None)
    page = request.args.get("page", 1, type=int)
    per_page = 20

    if not query:
        return render_template("results.html", query="", results=[], total=0,
                               page=1, total_pages=0, lang=lang,
                               detected_lang="auto",
                               gram_class=gram_class, tag=tag,
                               verb_class=verb_class,
                               all_tags=db.get_all_tags(),
                               all_classes=db.get_all_classes(),
                               all_verb_classes=db.get_all_verb_classes())

    results, total, detected_lang = search_combined(
        db, query, lang=lang, gram_class=gram_class, tag=tag,
        verb_class=verb_class, page=page, per_page=per_page,
    )
    total_pages = math.ceil(total / per_page) if total else 0

    return render_template(
        "results.html",
        query=query,
        results=results,
        total=total,
        page=page,
        total_pages=total_pages,
        lang=lang,
        detected_lang=detected_lang,
        gram_class=gram_class,
        tag=tag,
        verb_class=verb_class,
        all_tags=db.get_all_tags(),
        all_classes=db.get_all_classes(),
        all_verb_classes=db.get_all_verb_classes(),
    )


@app.route("/search/partial")
def search_partial():
    """HTMX endpoint: returns just result cards."""
    db = get_db()
    query = request.args.get("q", "").strip()
    lang = request.args.get("lang", "auto")
    gram_class = request.args.get("class", None)
    tag = request.args.get("tag", None)
    verb_class = request.args.get("verb_class", None)
    page = request.args.get("page", 1, type=int)

    # Support direction param from the index page toggle
    direction = request.args.get("direction", "")
    if direction == "skiri-en":
        lang = "skiri"
    elif direction == "en-skiri":
        lang = "english"

    if not query:
        return ""

    results, total, detected_lang = search_combined(
        db, query, lang=lang, gram_class=gram_class, tag=tag,
        verb_class=verb_class, page=page, per_page=20,
    )
    total_pages = math.ceil(total / 20) if total else 0

    return render_template(
        "_results_body.html",
        query=query,
        results=results,
        total=total,
        page=page,
        total_pages=total_pages,
        lang=lang,
        detected_lang=detected_lang,
        gram_class=gram_class,
        tag=tag,
        verb_class=verb_class,
    )


@app.route("/api/search")
def api_search():
    """JSON API endpoint for search. Powers future AJAX and external consumers."""
    db = get_db()
    query = request.args.get("q", "").strip()
    lang = request.args.get("lang", "auto")
    gram_class = request.args.get("class", None)
    tag = request.args.get("tag", None)
    verb_class = request.args.get("verb_class", None)
    limit = request.args.get("limit", 25, type=int)
    limit = min(limit, 100)  # cap at 100
    page = request.args.get("page", 1, type=int)

    if not query:
        return jsonify({"query": "", "results": [], "total": 0,
                        "detected_lang": "auto"})

    results, total, detected_lang = search_combined(
        db, query, lang=lang, gram_class=gram_class, tag=tag,
        verb_class=verb_class, page=page, per_page=limit,
    )

    return jsonify({
        "query": query,
        "detected_lang": detected_lang,
        "total": total,
        "page": page,
        "per_page": limit,
        "results": [
            {
                "entry_id": r.entry_id,
                "headword": r.headword,
                "normalized_form": r.normalized_form,
                "simplified_pronunciation": r.simplified_pronunciation,
                "grammatical_class": r.grammatical_class,
                "verb_class": r.verb_class,
                "first_gloss": r.first_gloss,
                "blue_book_attested": r.blue_book_attested,
                "tags": r.tags,
                "example_snippet": r.example_snippet,
                "form2_confidence": r.form2_confidence,
                "url": f"/entry/{r.entry_id}",
            }
            for r in results
        ],
    })


@app.route("/entry/<path:entry_id>")
def entry_detail(entry_id):
    db = get_db()
    data = db.build_full_entry(entry_id)
    if not data:
        abort(404)

    # Filter out false-positive examples and BB refs (e.g., kirike ≠ kiri)
    _filter_entry_examples(data)

    # Community feedback counts for this entry
    feedback_counts = db.get_entry_feedback_count(entry_id)
    data["feedback_counts"] = feedback_counts

    return render_template("entry.html", **data)


@app.route("/browse")
def browse():
    db = get_db()
    tags = db.get_all_tags()
    classes = db.get_all_classes()
    return render_template("browse.html", tags=tags, classes=classes)


@app.route("/browse/tag/<tag>")
def browse_tag(tag):
    db = get_db()
    page = request.args.get("page", 1, type=int)
    per_page = 40

    cur = db.conn.cursor()
    cur.execute(
        "SELECT entry_id FROM semantic_tags WHERE tag = ? ORDER BY entry_id",
        (tag,),
    )
    entry_ids = [r["entry_id"] for r in cur.fetchall()]
    total = len(entry_ids)
    total_pages = math.ceil(total / per_page) if total else 0
    page_ids = entry_ids[(page - 1) * per_page : page * per_page]
    results = db.build_entry_summaries(page_ids)

    return render_template(
        "browse_list.html",
        title=f"Tag: {tag}",
        results=results,
        total=total,
        page=page,
        total_pages=total_pages,
        base_url=f"/browse/tag/{tag}",
    )


@app.route("/browse/class/<path:cls>")
def browse_class(cls):
    db = get_db()
    page = request.args.get("page", 1, type=int)
    per_page = 40

    cur = db.conn.cursor()
    cur.execute(
        "SELECT entry_id FROM lexical_entries "
        "WHERE UPPER(grammatical_class) = UPPER(?) ORDER BY headword",
        (cls,),
    )
    entry_ids = [r["entry_id"] for r in cur.fetchall()]
    total = len(entry_ids)
    total_pages = math.ceil(total / per_page) if total else 0
    page_ids = entry_ids[(page - 1) * per_page : page * per_page]
    results = db.build_entry_summaries(page_ids)

    return render_template(
        "browse_list.html",
        title=f"Class: {cls}",
        results=results,
        total=total,
        page=page,
        total_pages=total_pages,
        base_url=f"/browse/class/{cls}",
    )


@app.route("/flashcards")
def flashcards_index():
    """Overview of all weekly flashcard sets."""
    sets = generate_all_sets(app.config["DATABASE"])
    # Group by category for display
    by_cat = {}
    for s in sets:
        by_cat.setdefault(s.category, []).append(s)
    return render_template("flashcards.html", sets=sets, by_category=by_cat)


@app.route("/flashcards/<int:week>")
def flashcard_study(week):
    """Interactive flip-card study session for a specific week."""
    sets = generate_all_sets(app.config["DATABASE"])
    current = None
    for s in sets:
        if s.week == week:
            current = s
            break
    if not current:
        abort(404)

    # Find prev/next weeks
    weeks = [s.week for s in sets]
    idx = weeks.index(week)
    prev_week = weeks[idx - 1] if idx > 0 else None
    next_week = weeks[idx + 1] if idx < len(weeks) - 1 else None

    return render_template(
        "flashcard_study.html",
        fset=current,
        prev_week=prev_week,
        next_week=next_week,
    )


@app.route("/guide")
def syllable_guide():
    return render_template("guide.html")


@app.route("/api/possession/<path:headword>")
def possession_api(headword):
    """Return possessive paradigm data for a noun."""
    db = get_db()
    cur = db.conn.cursor()
    cur.execute(
        "SELECT grammatical_class FROM lexical_entries WHERE headword = ?",
        (headword,),
    )
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "entry not found"}), 404

    noun_class = row["grammatical_class"] if row else None

    # Only generate for noun classes
    noun_classes = {"N", "N-DEP", "N-KIN", "NUM"}
    if not noun_class or noun_class not in noun_classes:
        return jsonify({"error": "not a noun"}), 200

    # Import possession engine (lives in scripts/)
    from scripts.possession_engine import generate_paradigm_table
    table = generate_paradigm_table(headword, noun_class=noun_class)
    return jsonify(table)


@app.route("/dashboard")
def dashboard():
    db = get_db()
    cur = db.conn.cursor()
    data = {}

    # --- Corpus Overview (hero stats) ---
    hero = {}
    for key, sql in [
        ("s2e", "SELECT COUNT(*) FROM lexical_entries"),
        ("e2s", "SELECT COUNT(*) FROM english_index"),
        ("glosses", "SELECT COUNT(*) FROM glosses"),
        ("examples", "SELECT COUNT(*) FROM examples"),
        ("sem_tags", "SELECT COUNT(*) FROM semantic_tags"),
        ("bb_entries", "SELECT COUNT(DISTINCT entry_id) FROM blue_book_attestations"),
    ]:
        try:
            hero[key] = cur.execute(sql).fetchone()[0]
        except Exception:
            hero[key] = 0
    data["hero"] = hero

    # --- Grammatical Class Distribution ---
    try:
        cur.execute(
            "SELECT grammatical_class, COUNT(*) as ct "
            "FROM lexical_entries GROUP BY grammatical_class ORDER BY ct DESC"
        )
        data["gram_classes"] = [(r[0] or "(none)", r[1]) for r in cur.fetchall()]
    except Exception:
        data["gram_classes"] = []

    # --- Field Completeness ---
    try:
        cur.execute("""
            SELECT
              COUNT(*) as total,
              SUM(CASE WHEN phonetic_form IS NOT NULL AND phonetic_form != '' THEN 1 ELSE 0 END),
              SUM(CASE WHEN simplified_pronunciation IS NOT NULL AND simplified_pronunciation != '' THEN 1 ELSE 0 END),
              SUM(CASE WHEN normalized_form IS NOT NULL AND normalized_form != '' THEN 1 ELSE 0 END),
              SUM(CASE WHEN compound_structure IS NOT NULL AND compound_structure != '' AND compound_structure != 'null' THEN 1 ELSE 0 END)
            FROM lexical_entries
        """)
        row = cur.fetchone()
        total = row[0] or 1
        data["completeness"] = {
            "total": total,
            "phonetic_form": row[1] or 0,
            "simplified_pronunciation": row[2] or 0,
            "normalized_form": row[3] or 0,
            "compound_structure": row[4] or 0,
        }
        # Also count entries with at least one gloss
        has_glosses = cur.execute(
            "SELECT COUNT(DISTINCT entry_id) FROM glosses"
        ).fetchone()[0]
        data["completeness"]["has_glosses"] = has_glosses
        # BB attested count
        bb_attested = cur.execute(
            "SELECT COUNT(*) FROM lexical_entries WHERE blue_book_attested = 1"
        ).fetchone()[0]
        data["completeness"]["bb_attested"] = bb_attested
    except Exception:
        data["completeness"] = {"total": 1}

    # --- Paradigmatic Form Coverage ---
    try:
        cur.execute(
            "SELECT form_number, COUNT(DISTINCT entry_id) as ct "
            "FROM paradigmatic_forms "
            "WHERE skiri_form IS NOT NULL AND skiri_form != '' "
            "GROUP BY form_number"
        )
        data["form_coverage"] = {r[0]: r[1] for r in cur.fetchall()}
    except Exception:
        data["form_coverage"] = {}

    # --- Semantic Tag Distribution (top 15) ---
    try:
        cur.execute(
            "SELECT tag, COUNT(*) as ct FROM semantic_tags "
            "GROUP BY tag ORDER BY ct DESC LIMIT 15"
        )
        data["top_tags"] = [(r[0], r[1]) for r in cur.fetchall()]
    except Exception:
        data["top_tags"] = []

    # --- Verb Engine Coverage ---
    verb = {}
    for key, sql in [
        ("paradigm_forms", "SELECT COUNT(*) FROM verb_paradigms"),
        ("distinct_verbs", "SELECT COUNT(DISTINCT stem) FROM verb_paradigms"),
        ("sound_rules", "SELECT COUNT(*) FROM sound_change_rules"),
        ("morphemes", "SELECT COUNT(*) FROM morpheme_inventory"),
    ]:
        try:
            verb[key] = cur.execute(sql).fetchone()[0]
        except Exception:
            verb[key] = None

    # --- Stem Extraction Accuracy (from pre-computed confidence scores) ---
    try:
        row = cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN form2_confidence >= 0.75 THEN 1 ELSE 0 END) as high_conf
            FROM lexical_entries
            WHERE grammatical_class LIKE 'V%'
        """).fetchone()
        verb["stem_total"] = row[0] or 0
        verb["stem_exact"] = row[1] or 0
    except Exception:
        verb["stem_total"] = 0
        verb["stem_exact"] = 0

    # --- Confidence Score Distribution ---
    confidence_dist = None
    try:
        cur.execute("""
            SELECT
              COUNT(*) as total,
              SUM(CASE WHEN form2_confidence >= 0.75 THEN 1 ELSE 0 END) as high,
              SUM(CASE WHEN form2_confidence >= 0.50 AND form2_confidence < 0.75 THEN 1 ELSE 0 END) as medium,
              SUM(CASE WHEN form2_confidence < 0.50 THEN 1 ELSE 0 END) as low,
              ROUND(AVG(form2_confidence), 3) as avg_conf
            FROM lexical_entries
            WHERE form2_confidence IS NOT NULL
        """)
        crow = cur.fetchone()
        if crow and crow[0] > 0:
            confidence_dist = {
                "total": crow[0],
                "high": crow[1] or 0,
                "medium": crow[2] or 0,
                "low": crow[3] or 0,
                "avg": crow[4] or 0,
            }
    except Exception:
        pass  # column doesn't exist yet
    verb["confidence_dist"] = confidence_dist

    data["verb"] = verb

    # --- Possession Engine Coverage ---
    poss = {}
    for key, sql in [
        ("body_part", "SELECT COUNT(*) FROM noun_stems WHERE possession_type = 'body_part'"),
        ("locative", "SELECT COUNT(*) FROM noun_stems WHERE possession_type = 'locative'"),
        ("kinship", "SELECT COUNT(*) FROM kinship_paradigms"),
    ]:
        try:
            poss[key] = cur.execute(sql).fetchone()[0]
        except Exception:
            poss[key] = None
    # BB test accuracy
    try:
        cur.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN match_status = 'exact' THEN 1 ELSE 0 END) as exact "
            "FROM possession_examples"
        )
        row = cur.fetchone()
        poss["bb_total"] = row[0] or 0
        poss["bb_exact"] = row[1] or 0
    except Exception:
        poss["bb_total"] = None
        poss["bb_exact"] = None
    data["poss"] = poss

    # --- E2S Linking Health ---
    try:
        linked = cur.execute(
            "SELECT COUNT(*) FROM english_index WHERE entry_id IS NOT NULL AND entry_id != ''"
        ).fetchone()[0]
        unlinked = cur.execute(
            "SELECT COUNT(*) FROM english_index WHERE entry_id IS NULL OR entry_id = ''"
        ).fetchone()[0]
        data["linking"] = {"linked": linked, "unlinked": unlinked, "total": linked + unlinked}
    except Exception:
        data["linking"] = {"linked": 0, "unlinked": 0, "total": 0}

    # --- Community Feedback Stats ---
    try:
        feedback_counts = db.get_feedback_counts()
    except Exception:
        feedback_counts = {"total": 0}
    data["feedback"] = feedback_counts

    return render_template("dashboard.html", **data)


@app.route("/about")
def about():
    return render_template("about.html")


# ------------------------------------------------------------------
# Phase 3.2a — Sentence Builder
# ------------------------------------------------------------------

@app.route("/sentence-builder")
def sentence_builder():
    """Template selection + sentence assembly UI."""
    from scripts.sentence_templates import list_templates
    templates = list_templates()
    return render_template("sentence_builder.html", templates=templates)


@app.route("/api/assemble", methods=["POST"])
def api_assemble():
    """Assemble a sentence from a template + slot values."""
    from scripts.sentence_templates import assemble
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid request"}), 400

    template_id = data.get("template_id", "").strip()
    if not template_id:
        return jsonify({"error": "template_id required"}), 400

    slots = {k: v for k, v in data.items() if k != "template_id"}
    result = assemble(template_id, **slots)
    return jsonify(result.to_dict())


@app.route("/api/slot-options")
def api_slot_options():
    """Return curated dropdown options for a template slot."""
    from scripts.sentence_templates import get_slot_options
    template_id = request.args.get("template", "").strip()
    slot = request.args.get("slot", "").strip()
    bb_only = request.args.get("bb_only", "true").lower() != "false"

    if not template_id or not slot:
        return jsonify([])

    options = get_slot_options(template_id, slot, bb_only=bb_only)
    return jsonify(options)


# ------------------------------------------------------------------
# Community Feedback (Phase 4.4)
# ------------------------------------------------------------------

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Submit community feedback for an entry."""
    db = get_db()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid request"}), 400

    entry_id = data.get("entry_id", "").strip()
    feedback_type = data.get("feedback_type", "").strip()

    if not entry_id or feedback_type not in ("flag", "confirm"):
        return jsonify({"error": "entry_id and valid feedback_type required"}), 400

    row_id = db.submit_feedback(
        entry_id=entry_id,
        feedback_type=feedback_type,
        form_field=data.get("form_field", "").strip() or None,
        issue_type=data.get("issue_type", "").strip() or None,
        suggested_correction=data.get("suggested_correction", "").strip() or None,
        comment=data.get("comment", "").strip() or None,
        reporter_name=data.get("reporter_name", "").strip() or None,
    )
    return jsonify({"ok": True, "id": row_id})


@app.route("/admin/feedback")
def feedback_admin():
    """Admin review queue for community feedback."""
    db = get_db()
    status_filter = request.args.get("status", "pending")
    items = db.get_feedback_queue(status=status_filter)
    counts = db.get_feedback_counts()
    return render_template(
        "feedback_admin.html",
        items=items,
        counts=counts,
        status_filter=status_filter,
    )


@app.route("/admin/feedback/<int:feedback_id>/review", methods=["POST"])
def review_feedback(feedback_id):
    """Accept or reject a feedback item."""
    db = get_db()
    data = request.get_json(silent=True) or {}
    status = data.get("status", "").strip()
    if status not in ("accepted", "rejected", "reviewed"):
        return jsonify({"error": "invalid status"}), 400

    reviewer_note = data.get("reviewer_note", "").strip() or None
    db.review_feedback(feedback_id, status, reviewer_note)
    return jsonify({"ok": True})


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pari Pakuru web server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    print(f"Starting Pari Pakuru on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
