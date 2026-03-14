"""
Phase 4.1 — Flask web application for the Skiri Pawnee dictionary.

Usage:
    python web/app.py                    # default: localhost:5000
    python web/app.py --port 8080        # custom port
"""

import argparse
import math
import os
import sys

from flask import Flask, g, render_template, request, abort

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
    word_of_day = db.get_random_entry()
    return render_template("index.html", stats=stats, word_of_day=word_of_day)


@app.route("/search")
def search_page():
    db = get_db()
    query = request.args.get("q", "").strip()
    lang = request.args.get("lang", "auto")
    gram_class = request.args.get("class", None)
    tag = request.args.get("tag", None)
    page = request.args.get("page", 1, type=int)
    per_page = 20

    if not query:
        return render_template("results.html", query="", results=[], total=0,
                               page=1, total_pages=0, lang=lang,
                               gram_class=gram_class, tag=tag,
                               all_tags=db.get_all_tags(),
                               all_classes=db.get_all_classes())

    results, total = search_combined(
        db, query, lang=lang, gram_class=gram_class, tag=tag,
        page=page, per_page=per_page,
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
        gram_class=gram_class,
        tag=tag,
        all_tags=db.get_all_tags(),
        all_classes=db.get_all_classes(),
    )


@app.route("/search/partial")
def search_partial():
    """HTMX endpoint: returns just result cards."""
    db = get_db()
    query = request.args.get("q", "").strip()
    lang = request.args.get("lang", "auto")
    gram_class = request.args.get("class", None)
    tag = request.args.get("tag", None)
    page = request.args.get("page", 1, type=int)

    if not query:
        return ""

    results, total = search_combined(
        db, query, lang=lang, gram_class=gram_class, tag=tag,
        page=page, per_page=20,
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
        gram_class=gram_class,
        tag=tag,
    )


@app.route("/entry/<path:entry_id>")
def entry_detail(entry_id):
    db = get_db()
    data = db.build_full_entry(entry_id)
    if not data:
        abort(404)
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


@app.route("/about")
def about():
    return render_template("about.html")


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
