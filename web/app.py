"""
Phase 4.1 — Flask web application for the Skiri Pawnee dictionary.

Usage:
    python web/app.py                    # default: localhost:5000
    python web/app.py --port 8080        # custom port
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import date

from flask import Flask, g, jsonify, redirect, render_template, request, abort, make_response
from markupsafe import Markup

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from web.db import SkiriWebDictionary
from web.search import search_combined
from web.search_ranking import rank_results
from web.flashcards import held_weeks, load_sets

DATABASE = os.path.join(PROJECT_ROOT, "skiri_pawnee.db")

app = Flask(__name__)
app.config["DATABASE"] = DATABASE


def _rerank(db, results, query):
    """Re-rank EntrySummary results using search_ranking.rank_results()."""
    if not results or not query:
        return results
    as_dicts = [
        {
            "entry_id": r.entry_id,
            "headword": r.headword,
            "grammatical_class": r.grammatical_class,
            "blue_book_attested": r.blue_book_attested,
        }
        for r in results
    ]
    ranked = rank_results(db.conn, as_dicts, query)
    by_id = {r.entry_id: r for r in results}
    return [by_id[d["entry_id"]] for d in ranked if d["entry_id"] in by_id]


# ------------------------------------------------------------------
# Jinja template filters
# ------------------------------------------------------------------

_UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")


@app.template_filter("format_pitch")
def format_pitch(pronunciation: str) -> Markup:
    """Wrap UPPERCASE pitch-accent syllables in <span class="pitch-high">.

    If the pronunciation has no uppercase (accent not marked), append a
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
        ' <span class="pitch-unmarked">(accent not marked)</span>'
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
    Filter the Blue Book attestations on an entry to remove false substring
    matches (e.g., 'kirike' pollution on 'kiri').

    The entry's own examples are NOT filtered: Parks printed them in this
    entry. Until 2026-11-14 they went through the same filter, which is made
    for Blue Book sentences and hid 2,224 of his 2,652 examples (engines
    review, section 9 of the decision paper).

    Modifies entry_data in place and returns it.
    """
    from scripts.example_filter import matches_headword

    hw_set = _get_headword_set()
    entry = entry_data.get("entry")
    if not entry:
        return entry_data

    headword = entry.headword if hasattr(entry, 'headword') else ""
    if not headword:
        return entry_data

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
            if bb_form and matches_headword(headword, bb_form, hw_set):
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
    spelling_pref = request.cookies.get("spelling", "simplified")
    return {
        "abs": abs,
        "min": min,
        "max": max,
        "spelling_pref": spelling_pref,
        "gram_class_labels": GRAM_CLASS_LABELS,
    }


@app.template_filter("primary_spelling")
def primary_spelling(entry):
    """Return the preferred primary spelling for an entry."""
    pref = request.cookies.get("spelling", "simplified")
    if pref == "parks":
        return entry.headword if hasattr(entry, "headword") else entry.get("headword", "")
    # simplified
    nf = entry.normalized_form if hasattr(entry, "normalized_form") else entry.get("normalized_form")
    hw = entry.headword if hasattr(entry, "headword") else entry.get("headword", "")
    return nf if nf and nf != hw else hw


@app.template_filter("secondary_spelling")
def secondary_spelling(entry):
    """Return the secondary (non-preferred) spelling for an entry."""
    pref = request.cookies.get("spelling", "simplified")
    hw = entry.headword if hasattr(entry, "headword") else entry.get("headword", "")
    nf = entry.normalized_form if hasattr(entry, "normalized_form") else entry.get("normalized_form")
    if pref == "parks":
        return nf if nf and nf != hw else None
    # simplified: secondary is Parks
    return hw if nf and nf != hw else None


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/preferences", methods=["POST"])
def set_preferences():
    """Set user preferences (spelling toggle) via cookie and redirect back."""
    spelling = request.form.get("spelling", "simplified")
    if spelling not in ("parks", "simplified"):
        spelling = "simplified"
    referrer = request.referrer or "/"
    resp = make_response(redirect(referrer))
    resp.set_cookie("spelling", spelling, max_age=365 * 24 * 3600, samesite="Lax")
    return resp


@app.route("/")
def index():
    db = get_db()
    stats = db.get_stats()
    word_of_day = db.get_word_of_day()
    tags = db.get_all_tags()
    wotd_date = date.today().strftime("%b %d")

    # Quick-access hint chips for the search bar
    quick_words = [
        {"skiri": "sakuuruʔ", "en": "sun"},
        {"skiri": "rikucki", "en": "bird"},
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
    results = _rerank(db, results, query)
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
    results = _rerank(db, results, query)
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
    results = _rerank(db, results, query)

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

    # Filter out false-positive Blue Book refs (e.g., kirike ≠ kiri)
    _filter_entry_examples(data)

    # For a noun: what Parks and the Blue Book print of it (nothing computed)
    from scripts.printed_noun_forms import lookup as printed_noun_forms
    data["printed_forms"] = printed_noun_forms(db.conn, entry_id)

    # Community feedback counts for this entry
    feedback_counts = db.get_entry_feedback_count(entry_id)
    data["feedback_counts"] = feedback_counts

    return render_template("entry.html", **data)


GRAM_CLASS_LABELS = {
    "VI-S": "Intransitive verb (stative)",
    "VI": "Intransitive verb",
    "VT": "Transitive verb",
    "VD": "Descriptive verb (qualities)",
    "VR": "Reflexive verb",
    "N": "Noun",
    "N-DEP": "Noun (always possessed)",
    "N-KIN": "Kinship noun",
    "ADV": "Adverb",
    "CONJ": "Conjunction",
    "INTERJ": "Interjection",
    "NUM": "Number",
    "PART": "Particle",
    "PRON": "Pronoun",
    "QUANT": "Quantifier",
    "VI-R": "Intransitive verb (reciprocal)",
    "VT-R": "Transitive verb (reciprocal)",
}


@app.route("/browse")
def browse():
    db = get_db()
    tags = db.get_all_tags()
    classes = db.get_all_classes()
    return render_template("browse.html", tags=tags, classes=classes,
                           gram_class_labels=GRAM_CLASS_LABELS)


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
    sets = load_sets(app.config["DATABASE"])
    # Group by category for display
    by_cat = {}
    for s in sets:
        by_cat.setdefault(s.category, []).append(s)
    return render_template("flashcards.html", sets=sets, by_category=by_cat, held=held_weeks())


@app.route("/flashcards/<int:week>")
def flashcard_study(week):
    """Interactive flip-card study session for a specific week."""
    sets = load_sets(app.config["DATABASE"])
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

    # --- Reference tables copied from the sources (counts only; nothing here is computed) ---
    reference = {}
    for key, sql in [
        ("paradigm_forms", "SELECT COUNT(*) FROM verb_paradigms"),
        ("distinct_verbs", "SELECT COUNT(DISTINCT verb_heading) FROM verb_paradigms"),
        ("sound_rules", "SELECT COUNT(*) FROM sound_change_rules"),
        ("kinship", "SELECT COUNT(*) FROM kinship_paradigms"),
    ]:
        try:
            reference[key] = cur.execute(sql).fetchone()[0]
        except Exception:
            reference[key] = None
    data["reference"] = reference

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

# ------------------------------------------------------------------
# Spaced repetition study (Phase 5.2b)
# ------------------------------------------------------------------

@app.route("/study")
def study():
    """Spaced-repetition review session (optionally scoped to a lesson/tag)."""
    from web import srs
    db = get_db()
    conn = db._get_write_conn()   # SRS schedules live in the DB
    lesson = request.args.get("lesson", type=int)
    tag = request.args.get("tag", "").strip() or None
    queue = srs.get_queue(conn, lesson=lesson, tag=tag)
    stats = srs.get_stats(conn, lesson=lesson, tag=tag)
    scope_label = (f"Lesson {lesson}" if lesson
                   else tag.replace("_", " ").title() if tag else "All words")
    return render_template("study.html", queue=queue, stats=stats,
                           lesson=lesson, tag=tag, scope_label=scope_label)


@app.route("/api/srs/review", methods=["POST"])
def srs_review():
    """Grade one card: {entry_id, grade: again|hard|good|easy}."""
    from web import srs
    db = get_db()
    data = request.get_json(silent=True) or {}
    entry_id = (data.get("entry_id") or "").strip()
    grade = (data.get("grade") or "").strip()
    if not entry_id or grade not in srs.GRADES:
        return jsonify({"error": "entry_id and grade (again/hard/good/easy) "
                                 "required"}), 400
    conn = db._get_write_conn()
    srs.ensure_tables(conn)
    due = srs.grade_card(conn, entry_id, grade)
    return jsonify({"ok": True, "due": due})


# ------------------------------------------------------------------
# Blue Book Lessons (Phase 5.1)
# ------------------------------------------------------------------

@app.route("/lessons")
def lessons_index():
    """Progressive Blue Book lesson list."""
    db = get_db()
    cur = db.conn.cursor()
    cur.execute("SELECT lesson_number, skiri_title, english_title, "
                "page_start, page_end, dialogues, template_ids "
                "FROM lessons ORDER BY lesson_number")
    lessons = []
    for r in cur.fetchall():
        cur.execute(
            "SELECT count(*) FROM blue_book_attestations "
            "WHERE lesson_number = ? "
            "AND context_type IN ('BASIC_WORDS','ADDITIONAL_WORDS')",
            (r["lesson_number"],))
        vocab_count = cur.fetchone()[0]
        dialogues = json.loads(r["dialogues"] or "[]")
        lessons.append({
            "number": r["lesson_number"],
            "skiri_title": r["skiri_title"],
            "english_title": r["english_title"],
            "pages": f"{r['page_start']}–{r['page_end']}",
            "vocab_count": vocab_count,
            "dialogue_count": sum(len(d.get("lines", [])) for d in dialogues),
            "templates": json.loads(r["template_ids"] or "[]"),
        })
    return render_template("lessons.html", lessons=lessons)


@app.route("/lessons/<int:number>")
def lesson_detail(number):
    """One Blue Book lesson: vocabulary, dialogues, grammar notes."""
    db = get_db()
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE lesson_number = ?", (number,))
    row = cur.fetchone()
    if not row:
        abort(404)

    # vocabulary from attestations, joined to dictionary entries where linked
    cur.execute("""
        SELECT a.bb_skiri_form, a.bb_english, a.context_type, a.entry_id,
               a.match_type, le.headword, le.normalized_form,
               le.simplified_pronunciation, le.phonetic_form,
               le.grammatical_class
        FROM blue_book_attestations a
        LEFT JOIN lexical_entries le ON le.entry_id = a.entry_id
        WHERE a.lesson_number = ?
          AND a.context_type IN ('BASIC_WORDS', 'ADDITIONAL_WORDS')
        ORDER BY a.context_type, a.id
    """, (number,))
    vocab = [dict(r) for r in cur.fetchall()]
    basic = [v for v in vocab if v["context_type"] == "BASIC_WORDS"]
    additional = [v for v in vocab if v["context_type"] == "ADDITIONAL_WORDS"]

    # useful phrases + grammar examples from attestations
    cur.execute("""
        SELECT bb_skiri_form, bb_english FROM blue_book_attestations
        WHERE lesson_number = ? AND context_type = 'PHRASE'
        ORDER BY id
    """, (number,))
    phrases = [dict(r) for r in cur.fetchall()]

    lesson = {
        "number": row["lesson_number"],
        "skiri_title": row["skiri_title"],
        "english_title": row["english_title"],
        "page_start": row["page_start"],
        "page_end": row["page_end"],
        "dialogues": json.loads(row["dialogues"] or "[]"),
        "grammar_notes": json.loads(row["grammar_notes"] or "[]"),
        "templates": json.loads(row["template_ids"] or "[]"),
    }
    # the patterns practised in this lesson: each with a sentence the Blue Book prints, read from its row
    from scripts.sentence_templates import list_templates
    patterns = {t["template_id"]: t for t in list_templates(db.conn)}
    practice = [
        {"id": t, "name": patterns[t]["name"],
         "example": patterns[t]["skiri_example"],
         "english": patterns[t]["english_example"]}
        for t in lesson["templates"] if t in patterns
    ]
    exercises = _build_exercises(vocab, lesson["dialogues"], phrases)
    prev_n = number - 1 if number > 1 else None
    next_n = number + 1 if number < 20 else None
    return render_template("lesson_detail.html", lesson=lesson,
                           basic=basic, additional=additional,
                           phrases=phrases, practice=practice,
                           exercises=exercises,
                           prev_n=prev_n, next_n=next_n)


def _build_exercises(vocab, dialogues, phrases):
    """Deterministically generate lesson exercises from Blue Book content.

    Everything shown is verbatim lesson material — vocabulary pairs and
    dialogue lines as printed; nothing is machine-generated language.
    """
    import random as _random
    rng = _random.Random()   # fresh shuffle each page load

    pairs = [(v["bb_skiri_form"].strip(), (v["bb_english"] or "").strip())
             for v in vocab
             if v["bb_skiri_form"] and (v["bb_english"] or "").strip()
             and len((v["bb_english"] or "")) < 40]
    # de-dup on the Skiri side
    seen = set()
    uniq = []
    for s, e in pairs:
        if s.lower() not in seen:
            seen.add(s.lower())
            uniq.append((s, e))

    matching = rng.sample(uniq, min(8, len(uniq))) if len(uniq) >= 4 else []

    # fill-in-the-blank: blank a lesson vocab word inside a dialogue line
    def first_token(form):
        t = re.split(r'[\s,(]', form.strip())[0]
        return t if len(t) >= 3 else None

    blanks = []
    used_lines = set()
    vocab_tokens = [(first_token(s), s, e) for s, e in uniq]
    vocab_tokens = [(t, s, e) for t, s, e in vocab_tokens if t]
    all_lines = [ln for d in dialogues for ln in d.get("lines", [])]
    for ln in all_lines:
        skiri, english = ln.get("skiri", ""), ln.get("english", "")
        if not skiri or not english or skiri in used_lines:
            continue
        for tok, form, gloss in vocab_tokens:
            m = re.search(r'(?<![\w•])' + re.escape(tok) + r'(?![\w•])',
                          skiri, re.IGNORECASE)
            if m:
                blanked = (skiri[:m.start()] + "_____" + skiri[m.end():])
                distractors = [t for t, s, e in vocab_tokens if t != tok]
                if len(distractors) < 3:
                    break
                options = rng.sample(distractors, 3) + [tok]
                rng.shuffle(options)
                blanks.append({
                    "blanked": blanked, "english": english,
                    "answer": tok, "options": options,
                })
                used_lines.add(skiri)
                break
        if len(blanks) >= 6:
            break

    # "say it in Pawnee": English prompt -> reveal the printed Skiri line
    say_pool = ([(p["bb_skiri_form"], p["bb_english"]) for p in phrases
                 if p.get("bb_english")] +
                [(ln["skiri"], ln["english"]) for ln in all_lines
                 if ln.get("english")])
    say_pool = [(s, e) for s, e in say_pool if 3 < len(e) < 60]
    say = [{"skiri": s, "english": e}
           for s, e in rng.sample(say_pool, min(5, len(say_pool)))]

    return {"matching": [{"skiri": s, "english": e} for s, e in matching],
            "blanks": blanks, "say": say}


@app.route("/sentence-builder")
def sentence_builder():
    """Sentences from printed words (scripts/sentence_templates.py). Local app only."""
    from scripts.sentence_templates import list_templates
    return render_template("sentence_builder.html", templates=list_templates(get_db().conn))


@app.route("/api/assemble", methods=["POST"])
def api_assemble():
    """A printed sentence of the Blue Book with some words swapped for other printed words.

    Body: {"template_id": "T2", "frame": 0, "slots": {"noun": ROW, ...}}; a slot is the number of a row of
    blue_book_attestations, or {"row": N, "places": [...]} for a word taken from a sentence of the same shape.
    """
    from scripts.sentence_templates import assemble
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid request"}), 400
    template_id = str(data.get("template_id", "")).strip()
    if not template_id:
        return jsonify({"error": "template_id required"}), 400
    slots = data.get("slots")
    if not isinstance(slots, dict):
        slots = {k: v for k, v in data.items() if k not in ("template_id", "frame", "slots")}
    slots = {str(k): v for k, v in slots.items() if str(k) not in ("conn", "frame", "template_id")}
    result = assemble(template_id, data.get("frame", 0), conn=get_db().conn, **slots)
    return jsonify(result.to_dict())


@app.route("/api/slot-options")
def api_slot_options():
    """Printed words that may stand in one place of a frame; those the book itself puts there come first."""
    from scripts.sentence_templates import slot_options
    template_id = request.args.get("template", "").strip()
    slot = request.args.get("slot", "").strip()
    if not template_id or not slot:
        return jsonify([])
    try:
        options = slot_options(template_id, request.args.get("frame", 0, type=int), slot,
                               q=request.args.get("q", ""), conn=get_db().conn)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(options)


@app.route("/api/verbs")
def api_verbs():
    """Search dictionary verbs. Each hit carries its entry id: the same spelling can be two verbs.

    Matches English glosses or Skiri headwords; says whether "I" and "you" forms can be shown
    (the entry prints a form 1) or only "he/she" forms."""
    db = get_db()
    q = request.args.get("q", "").strip()
    limit = min(request.args.get("limit", 8, type=int), 20)
    if not q or len(q) < 2:
        return jsonify([])

    cur = db.conn.cursor()
    # rank word-boundary gloss matches ("be red", "red, reddish") above
    # substring hits ("scared", "interred"), then shorter headwords
    cur.execute("""
        SELECT le.entry_id, le.headword, le.normalized_form,
               le.grammatical_class, le.verb_class,
               le.simplified_pronunciation,
               (SELECT definition FROM glosses g WHERE g.entry_id = le.entry_id
                ORDER BY sense_number LIMIT 1) AS gloss,
               max(CASE WHEN pf.form_number = 1 THEN 1 ELSE 0 END) AS has_f1,
               max(CASE WHEN pf.form_number = 2 THEN 1 ELSE 0 END) AS has_f2,
               (le.headword LIKE :pfx OR le.normalized_form LIKE :pfx) AS hw_hit,
               EXISTS (SELECT 1 FROM glosses g2 WHERE g2.entry_id = le.entry_id
                       AND (g2.definition LIKE :w1 OR g2.definition LIKE :w2
                            OR g2.definition LIKE :w3 OR g2.definition = :q))
                   AS word_hit
        FROM lexical_entries le
        JOIN paradigmatic_forms pf ON pf.entry_id = le.entry_id
        WHERE le.grammatical_class LIKE 'V%'
          AND (le.headword LIKE :pfx OR le.normalized_form LIKE :pfx
               OR le.entry_id IN (
                   SELECT entry_id FROM glosses WHERE definition LIKE :sub))
        GROUP BY le.entry_id
        ORDER BY hw_hit DESC, word_hit DESC, length(le.headword)
        LIMIT :lim
    """, {"pfx": q + "%", "sub": "%" + q + "%", "q": q,
          "w1": q + " %", "w2": "% " + q + "%", "w3": "% " + q,
          "lim": limit})
    results = []
    for r in cur.fetchall():
        results.append({
            "entry_id": r["entry_id"],
            "headword": r["headword"],
            "normalized_form": r["normalized_form"],
            "gram_class": r["grammatical_class"],
            "verb_class": r["verb_class"],
            "pronunciation": r["simplified_pronunciation"],
            "gloss": (r["gloss"] or "").split(";")[0].strip(),
            # "I" and "you" only where the entry prints a form 1: none is made up
            "persons": "I / you / he-she" if r["has_f1"] else "he-she only",
        })
    return jsonify(results)


@app.route("/api/verb-forms")
def api_verb_forms():
    """The forms of one dictionary verb, by its entry id: printed ones, and derived ones with their label."""
    from scripts.sentence_templates import verb_forms
    entry_id = request.args.get("entry_id", "").strip()
    if not entry_id:
        return jsonify({"error": "entry_id required"}), 400
    return jsonify(verb_forms(entry_id, get_db().conn))


@app.route("/api/dictionary-sentence", methods=["POST"])
def api_dictionary_sentence():
    """A sentence in the dictionary's spelling: a noun, a verb form of one entry, and for a question Parks's
    question word. Never printed anywhere, and marked so."""
    from scripts.sentence_templates import dictionary_sentence
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid request"}), 400
    result = dictionary_sentence(str(data.get("pattern", "statement")), str(data.get("verb_entry_id", "")),
                                 str(data.get("form_key", "")), data.get("noun_entry_id") or None,
                                 conn=get_db().conn)
    return jsonify(result.to_dict())


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
    _export_feedback(db)
    return jsonify({"ok": True, "id": row_id})


def _export_feedback(db):
    """Mirror community_feedback to a git-tracked JSON file.

    Community feedback is the one table that cannot be rebuilt from the
    source PDFs — it is knowledge contributed by people. The DB itself is
    gitignored, so every write also lands in exports/ for versioned,
    off-machine safekeeping.
    """
    try:
        cur = db.conn.cursor()
        cur.execute("SELECT * FROM community_feedback ORDER BY id")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        out_path = os.path.join(PROJECT_ROOT, "exports",
                                "community_feedback.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
    except Exception:
        # export is belt-and-braces; never let it break a submission
        app.logger.exception("community feedback export failed")


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
    _export_feedback(db)
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
