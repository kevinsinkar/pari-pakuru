#!/usr/bin/env python3
"""
Build static HTML site from Flask app for GitHub Pages deployment.

Usage:
    python scripts/build_static_site.py                    # default: docs/
    python scripts/build_static_site.py --output my_site/  # custom output
    python scripts/build_static_site.py --dry-run           # preview changes

This script:
1. Exports dictionary data to JSON (data/dictionary.json)
2. Exports the data of the learning pages (data/wordbuilding.json, verbs.json, practice.json)
3. Copies static assets and the two printable documents
4. Generates the main pages, the learning pages, the flashcard pages and the lesson pages
5. Rewrites the app's links so the pages work as plain files

Everything a page shows is copied from the database or from extracted_data/;
no step makes a Skiri form (see web/learning.py for the learning pages).
"""

import argparse
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from web.db import SkiriWebDictionary
from web import learning
from web import spelling

# Import grammatical class labels from Flask app
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


def export_dictionary_data(db_path: str, output_dir: Path) -> dict:
    """Export all dictionary entries to searchable JSON."""
    print("[*] Exporting dictionary data...")
    db = SkiriWebDictionary(db_path)

    # Get all entries
    cur = db.conn.cursor()
    cur.execute("SELECT entry_id FROM lexical_entries ORDER BY entry_id")
    entry_ids = [row[0] for row in cur.fetchall()]

    # Build searchable index
    entries = []
    for entry_id in entry_ids:
        entry = db._build_entry(entry_id)
        if not entry:
            continue

        # Get blue_book_attested + source from database
        cur_bb = db.conn.cursor()
        cur_bb.execute(
            "SELECT blue_book_attested, source FROM lexical_entries WHERE entry_id = ?",
            (entry_id,)
        )
        bb_row = cur_bb.fetchone()
        bb_attested = bool(bb_row["blue_book_attested"]) if bb_row else False
        source = (bb_row["source"] if bb_row else None) or "parks"

        # What the public page shows of an entry. Everything Parks prints for it goes out:
        # the numbered verb forms, the other forms in braces, the etymology, the forms cited
        # from related languages, the stems listed under a bound stem. Entries tagged
        # "ceremony" keep to headword, senses and examples until the community review of
        # ceremonial vocabulary has an answer (project log, "What's next", rank 1).
        tags = [r[0] for r in db.conn.execute(
            "SELECT DISTINCT tag FROM semantic_tags WHERE entry_id = ? ORDER BY tag", (entry_id,))]
        held = "ceremony" in tags
        detail = {}
        if not held:
            raw_forms = db.conn.execute(
                "SELECT additional_forms FROM lexical_entries WHERE entry_id = ?", (entry_id,)).fetchone()[0]
            try:
                other_forms = [f for f in json.loads(raw_forms or "[]") if isinstance(f, dict) and f.get("form")]
            except ValueError:
                other_forms = []
            # the printed derivation cut at its plus signs (web/learning.py); only for a Parks entry whose
            # derivation has two or more pieces
            parts = (learning.split_derivation(entry.etymology.raw_etymology)
                     if entry.etymology and entry.etymology.raw_etymology and source != "blue_book" else None)
            build = None
            if parts:
                build = {"u": parts["units"], "k": parts["keys"], "lit": parts["literal"]}
                if parts.get("unsure"):
                    build["unsure"] = True
                if parts.get("words"):
                    build["words"] = parts["words"]
            detail = {
                "build": build,
                "verb_forms": [{"n": p.form_number, "form": p.skiri_form} for p in (entry.paradigmatic_forms or [])],
                "other_forms": [{"type": f.get("form_type"), "form": f["form"]} for f in other_forms],
                "etymology": ({"raw": entry.etymology.raw_etymology, "literal": entry.etymology.literal_translation}
                              if entry.etymology and entry.etymology.raw_etymology else None),
                "cognates": [{"language": c.language, "form": c.form} for c in (entry.cognates or [])],
                "derived_stems": [{"form": r[0], "definition": r[1]} for r in db.conn.execute(
                    "SELECT stem_form, definition FROM derived_stems WHERE entry_id = ? ORDER BY id", (entry_id,))],
            }
        contexts = dict(db.conn.execute(
            "SELECT skiri_text, usage_context FROM examples WHERE entry_id = ? AND usage_context IS NOT NULL", (entry_id,)).fetchall())

        # Flatten to JSON-serializable format
        entry_dict = {
            "entry_id": entry.entry_id,
            "headword": entry.headword,
            "normalized_form": entry.normalized_form,
            "phonetic_form": entry.phonetic_form,
            "simplified_pronunciation": entry.simplified_pronunciation,
            "stem_preverb": entry.stem_preverb,
            "grammatical_class": entry.grammatical_class,
            "verb_class": entry.verb_class,
            "blue_book_attested": bb_attested,
            "source": source,
            "page_number": entry.page_number,
            "glosses": [
                {
                    "sense_number": g.sense_number,
                    "definition": g.definition,
                    "usage_notes": g.usage_notes,
                }
                for g in (entry.glosses or [])
            ],
            "examples": [
                {
                    "skiri_text": e.skiri_text,
                    "english_translation": e.english_translation,
                    "usage_context": contexts.get(e.skiri_text),
                    "source": e.source,
                }
                for e in (entry.examples or [])
            ],
            "tags": tags,
            "detail_held": held,
        }
        if source == "blue_book":
            # A word taken from the textbook is headed in the dictionary's letters. Show beside it what the book
            # prints (forms read from the scan) and, where it is a word Parks has, the dictionary's own entry
            # (both set by scripts/bluebook_only_entries.py).
            from bluebook_only_entries import letters as bb_letters
            same = db.conn.execute(
                "SELECT p.entry_id, p.headword FROM lexical_entries b JOIN lexical_entries p ON p.entry_id = b.bb_variant_of "
                "WHERE b.entry_id = ?", (entry_id,)).fetchone()
            printed = []
            # the book's form may be filed under the dictionary's entry for the same word: take it from there
            # when it is this entry's headword letter for letter
            for form, page, owner in db.conn.execute(
                    "SELECT bb_skiri_form, page_number, entry_id FROM blue_book_attestations WHERE entry_id IN (?, ?) ORDER BY id",
                    (entry_id, same[0] if same else entry_id)):
                form = (form or "").strip()
                if owner != entry_id and bb_letters(form) != bb_letters(entry.headword):
                    continue
                if form and form not in [p["form"] for p in printed]:
                    printed.append({"form": form, "page": (page - 28) if page else None})   # book page = PDF page - 28
            entry_dict["bb_printed"] = printed
            entry_dict["bb_variant_of"] = {"entry_id": same[0], "headword": same[1]} if same else None
        entry_dict.update(detail)
        entries.append(entry_dict)

    # Write JSON
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # one entry to a line: a change to one entry is one line of difference in git
    with open(data_dir / "dictionary.json", "w", encoding="utf-8", newline="\n") as f:
        f.write("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in entries) + "\n]\n")

    print(f"[OK] Exported {len(entries)} entries to data/dictionary.json")
    db.close()
    return {"entries": len(entries)}


def generate_entry_pages(db_path: str, output_dir: Path) -> dict:
    """Generate individual entry pages."""
    print("[*] Generating entry pages...")
    from jinja2 import Environment, FileSystemLoader

    # Register custom filters for static rendering
    def format_pitch_filter(pronunciation: str):
        """Format pitch accent (uppercase syllables)."""
        if not pronunciation:
            return ""
        import re
        _UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")
        has_upper = any(c.isupper() for c in pronunciation)
        if has_upper:
            return _UPPER_RUN_RE.sub(r'<span class="pitch-high">\1</span>', pronunciation)
        return pronunciation + ' <span class="pitch-unmarked">(accent not marked)</span>'

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    spelling.register(env)          # both spellings of a word; the switch at the top shows one (web/spelling.py)
    env.filters['format_pitch'] = format_pitch_filter

    template = env.get_template("entry.html")

    db = SkiriWebDictionary(db_path)

    # Get all entries
    cur = db.conn.cursor()
    cur.execute("SELECT entry_id FROM lexical_entries ORDER BY entry_id")
    entry_ids = [row[0] for row in cur.fetchall()]

    entries_dir = output_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)

    # Mock request object for static rendering
    class MockRequest:
        class Args:
            def get(self, key, default=""):
                return default
        args = Args()

    count = 0
    for entry_id in entry_ids:
        entry = db._build_entry(entry_id)
        if not entry:
            continue

        html = template.render(
            entry=entry,
            request=MockRequest(),
            gram_class_labels=GRAM_CLASS_LABELS
        )

        page_file = entries_dir / f"{entry_id}.html"
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1
        if count % 500 == 0:
            print(f"  {count}/{len(entry_ids)}...")

    print(f"[OK] Generated {count} entry pages")
    db.close()
    return {"entries": count}


def generate_browse_pages(db_path: str, output_dir: Path) -> dict:
    """Generate browse pages for grammatical classes."""
    print("[*] Generating browse pages...")
    from jinja2 import Environment, FileSystemLoader

    # Register custom filters for static rendering
    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    spelling.register(env)          # both spellings of a word; the switch at the top shows one (web/spelling.py)

    template = env.get_template("browse.html")

    db = SkiriWebDictionary(db_path)

    # Mock request object for static rendering
    class MockRequest:
        class Args:
            def get(self, key, default=""):
                return default
        args = Args()

    classes = db.get_all_classes()
    browse_dir = output_dir / "browse"
    browse_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for gram_class, _ in classes:
        cur = db.conn.cursor()
        cur.execute(
            "SELECT entry_id FROM lexical_entries WHERE grammatical_class = ? "
            "ORDER BY headword",
            (gram_class,)
        )
        entry_ids = [row[0] for row in cur.fetchall()]

        summaries = db.build_entry_summaries(entry_ids)

        slug = gram_class.lower().replace(" ", "-")
        html = template.render(
            gram_class=gram_class,
            entries=summaries,
            total=len(summaries),
            request=MockRequest(),
            gram_class_labels=GRAM_CLASS_LABELS
        )

        page_file = browse_dir / f"{slug}.html"
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1

    print(f"[OK] Generated {count} browse pages")
    db.close()
    return {"pages": count}


def export_learning_data(db_path: str, output_dir: Path) -> dict:
    """Write the files the learning pages read: data/wordbuilding.json, verbs.json, practice.json."""
    print("[*] Exporting the data of the learning pages...")
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    files = learning.data_files(db_path)

    # wordbuilding: one entry to a line, so that a changed derivation is one line of difference in git
    wb = files["wordbuilding"]
    head = {k: v for k, v in wb.items() if k != "entries"}
    with open(data_dir / "wordbuilding.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1] + ',"entries":[\n')
        f.write(",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in wb["entries"]))
        f.write("\n]}\n")
    for name in ("verbs", "practice"):
        with open(data_dir / f"{name}.json", "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(files[name], ensure_ascii=False, indent=1) + "\n")

    forms = sum(1 for v in files["verbs"]["verbs"] for m in v["modes"].values() for form in m.values() if form)
    cards = sum(len(w["cards"]) for w in files["practice"]["weeks"])
    print(f"[OK] Word building: {len(wb['entries'])} entries with a printed derivation of two or more pieces")
    print(f"[OK] Verbs: {len(files['verbs']['verbs'])} verbs of Appendix 1, {forms} forms; practice: {cards} words")
    return {"wordbuilding": len(wb["entries"]), "verb_forms": forms, "practice_words": cards}


def copy_printables(output_dir: Path) -> dict:
    """Copy the two documents for paper (curriculum/printables/*.pdf) to printables/."""
    src = PROJECT_ROOT / "curriculum" / "printables"
    dst = output_dir / "printables"
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in ("word_list.pdf", "paradigm_tables.pdf"):
        if (src / name).exists():
            shutil.copyfile(src / name, dst / name)
            count += 1
        else:
            print(f"  [!] {name} is missing: run scripts/build_printables.py")
    print(f"[OK] Copied {count} printable documents")
    return {"files": count}


def copy_static_assets(output_dir: Path) -> dict:
    """Copy CSS, JS, and other static assets."""
    print("[*] Copying static assets...")

    static_src = PROJECT_ROOT / "web" / "static"
    static_dst = output_dir / "static"

    # Overwrite in place (rmtree fights OneDrive file locks on Windows)
    shutil.copytree(static_src, static_dst, dirs_exist_ok=True)

    # Count files
    count = sum(1 for _ in static_dst.rglob("*") if _.is_file())
    print(f"[OK] Copied {count} static files")

    return {"files": count}


def _postprocess_for_static(html: str) -> str:
    """Rewrite Flask-app URLs so pages work as plain files under any base path
    (GitHub Pages serves this site at /pari-pakuru/, so absolute paths break)."""
    import re

    # Drop nav links to Flask-only routes that have no static equivalent
    # (flashcards and lessons HAVE static equivalents now — keep those links)
    html = re.sub(
        r'<li><a href="/(search|browse|study|sentence-builder|dashboard)"[^>]*>[^<]*</a></li>',
        "", html)

    # Drop the spaced-repetition study button (server-side SRS only)
    html = re.sub(
        r'<p><a href="/study\?[^"]*"[^>]*>.*?</a></p>',
        "", html, flags=re.DOTALL)

    # Strip HTMX live-search attributes (their endpoints don't exist statically;
    # search.js handles live search instead)
    html = re.sub(r'\s+hx-[a-z-]+="[^"]*"', "", html)

    # Absolute → relative paths (all generated pages sit at the site root)
    html = html.replace('href="/static/', 'href="static/')
    html = html.replace('src="/static/', 'src="static/')
    html = html.replace('action="/search"', 'action="index.html"')
    html = html.replace('href="/search?', 'href="index.html?')
    html = html.replace('href="/about"', 'href="about.html"')
    html = html.replace('href="/guide"', 'href="guide.html"')
    html = re.sub(r'href="/"', 'href="index.html"', html)

    # The learning pages sit at the site root; a query string or an anchor is kept
    html = re.sub(r'href="/(learn|words|wordweb|verbs|practice|topics|phrases|resources)((?:\?|#)[^"]*)?"',
                  lambda m: 'href="%s.html%s"' % (m.group(1), m.group(2) or ""), html)

    # A category link opens that topic's word list (topics.html). A tag that is not offered as a topic
    # ("ceremony") stays a search on the tag word, as before.
    html = re.sub(r'href="/browse/tag/([^"]+)"',
                  lambda m: 'href="topics.html?tag=%s"' % m.group(1) if m.group(1) in learning.TOPIC_LABELS
                  else 'href="index.html?q=%s"' % m.group(1), html)
    html = html.replace('href="/browse"', 'href="topics.html"')

    # Flashcard pages are generated statically at the site root
    html = re.sub(r'href="/flashcards/(\d+)"', r'href="flashcard-\1.html"', html)
    html = html.replace('href="/flashcards"', 'href="flashcards.html"')

    # Blue Book lesson pages are generated statically at the site root; an anchor is kept
    html = re.sub(r'href="/lessons/(\d+)(#[^"]*)?"', lambda m: 'href="lesson-%s.html%s"' % (m.group(1), m.group(2) or ""), html)
    html = html.replace('href="/lessons"', 'href="lessons.html"')

    # A link to an entry page opens that one entry on the home page (search.js, ?id=)
    from urllib.parse import quote
    html = re.sub(r'href="/entry/([^"]*)"',
                  lambda m: 'href="index.html?id=%s"' % quote(m.group(1), safe=""), html)

    # Any remaining Flask-route link (entry pages, flashcards, browse) has no
    # static equivalent yet — fall back to the home page rather than a 404
    html = re.sub(r'href="/[^"]*"', 'href="index.html"', html)

    return html


def generate_static_pages(db_path: str, output_dir: Path) -> dict:
    """Generate static versions of main pages (index, about, guide, etc.)."""
    print("[*] Generating static pages...")
    from jinja2 import Environment, FileSystemLoader
    from datetime import date
    import re

    # Register custom filters for static rendering
    def format_pitch_filter(pronunciation: str):
        """Format pitch accent (uppercase syllables)."""
        if not pronunciation:
            return ""
        _UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")
        has_upper = any(c.isupper() for c in pronunciation)
        if has_upper:
            return _UPPER_RUN_RE.sub(r'<span class="pitch-high">\1</span>', pronunciation)
        return pronunciation + ' <span class="pitch-unmarked">(accent not marked)</span>'

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    spelling.register(env)          # both spellings of a word; the switch at the top shows one (web/spelling.py)
    env.filters['format_pitch'] = format_pitch_filter

    db = SkiriWebDictionary(db_path)
    stats = db.get_stats()

    # Mock request object for static rendering
    class MockRequest:
        class Args:
            def get(self, key, default=""):
                return default
        args = Args()

    pages_to_generate = [
        ("index.html", "index.html", {}),
        ("about.html", "about.html", {}),
        ("guide.html", "guide.html", {}),
        # the learning pages; what they show is read in the browser from data/*.json
        ("learn.html", "learn.html", {}),
        ("words.html", "words.html", {}),
        # the same data as a picture: words joined to the pieces printed in their derivations (wordweb.js)
        ("wordweb.html", "wordweb.html", {}),
        ("verbs.html", "verbs.html", {}),
        ("practice.html", "practice.html", {}),
        ("topics.html", "topics.html", {"topics": learning.topics_data(db.conn)}),
        # the lessons' Useful Phrases by situation, written into the page (curriculum/everyday_phrases.json)
        ("phrases.html", "phrases.html", {"phrases": learning.phrases_data(db.conn),
                                          "dialect_statements": learning.dialect_statements()["statements"]}),
        # other places to learn: the part of the register of sources marked for learners (sources/catalogue.json)
        ("resources.html", "resources.html", {"sections": learning.sources_data()}),
    ]

    count = 0
    for template_name, output_name, extra_context in pages_to_generate:
        try:
            template = env.get_template(template_name)
            context = {
                "stats": stats,
                "word_of_day": db.get_word_of_day(),
                "wotd_date": date.today().strftime("%b %d"),
                "tags": db.get_all_tags(),
                "quick_words": [
                    {"skiri": "sakuuruʔ", "en": "sun"},
                    {"skiri": "rikucki", "en": "bird"},
                    {"skiri": "piita", "en": "man"},
                    {"skiri": "capaat", "en": "woman"},
                ],
                "request": MockRequest(),
                "gram_class_labels": GRAM_CLASS_LABELS,
            }
            context.update(extra_context)

            html = template.render(**context)
            html = _postprocess_for_static(html)

            output_file = output_dir / output_name
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)

            count += 1
        except Exception as e:
            # a page that cannot be built is an error, not something to pass over: the navigation links to it
            raise RuntimeError(f"{template_name}: {e}") from e

    print(f"[OK] Generated {count} static pages")
    db.close()
    return {"pages": count}


def generate_flashcard_pages(db_path: str, output_dir: Path) -> dict:
    """Generate the flashcards overview page and one study page per week.

    All pages are written at the site root (flashcards.html, flashcard-N.html)
    so the relative static/ asset paths work without a base-path rewrite.
    Progress tracking already runs on localStorage, so the Flask templates
    work statically as-is.
    """
    print("[*] Generating flashcard pages...")
    import re
    from jinja2 import Environment, FileSystemLoader
    from web.flashcards import held_weeks, load_sets

    # Register custom filters for static rendering
    def format_pitch_filter(pronunciation: str):
        """Format pitch accent (uppercase syllables)."""
        if not pronunciation:
            return ""
        _UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")
        has_upper = any(c.isupper() for c in pronunciation)
        if has_upper:
            return _UPPER_RUN_RE.sub(r'<span class="pitch-high">\1</span>', pronunciation)
        return pronunciation + ' <span class="pitch-unmarked">(accent not marked)</span>'

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    spelling.register(env)          # both spellings of a word; the switch at the top shows one (web/spelling.py)
    env.filters['format_pitch'] = format_pitch_filter

    # Mock request object for static rendering
    class MockRequest:
        class Args:
            def get(self, key, default=""):
                return default
        args = Args()

    base_context = {
        "request": MockRequest(),
        "gram_class_labels": GRAM_CLASS_LABELS,
    }

    sets = load_sets(db_path)          # weeks held for review are left out
    held = held_weeks()
    by_cat = {}
    for s in sets:
        by_cat.setdefault(s.category, []).append(s)

    # a page built before a week was held must not stay on the site
    for h in held:
        stale = output_dir / f"flashcard-{h['week']}.html"
        if stale.exists():
            stale.unlink()
            print(f"  removed {stale.name} (week {h['week']} is held for review)")

    # Overview page
    template = env.get_template("flashcards.html")
    html = template.render(sets=sets, by_category=by_cat, held=held, **base_context)
    html = _postprocess_for_static(html)
    with open(output_dir / "flashcards.html", "w", encoding="utf-8") as f:
        f.write(html)

    # One study page per week
    template = env.get_template("flashcard_study.html")
    weeks = [s.week for s in sets]
    count = 0
    for idx, fset in enumerate(sets):
        prev_week = weeks[idx - 1] if idx > 0 else None
        next_week = weeks[idx + 1] if idx < len(weeks) - 1 else None
        html = template.render(
            fset=fset,
            prev_week=prev_week,
            next_week=next_week,
            **base_context,
        )
        html = _postprocess_for_static(html)
        with open(output_dir / f"flashcard-{fset.week}.html", "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    total_cards = sum(s.card_count for s in sets)
    print(f"[OK] Generated flashcards.html + {count} weekly pages ({total_cards} cards)")
    return {"weeks": count, "cards": total_cards}


def generate_lesson_pages(db_path: str, output_dir: Path) -> dict:
    """Generate the Blue Book lessons index and one page per lesson.

    Pages are written at the site root (lessons.html, lesson-N.html) so the
    relative static/ asset paths work. Exercises are rendered by the same
    client-side JS the Flask app uses; the server-only features (spaced
    repetition, sentence-builder practice links) are omitted.
    """
    print("[*] Generating Blue Book lesson pages...")
    import json as _json
    import re
    from jinja2 import Environment, FileSystemLoader
    from web.app import _build_exercises

    def format_pitch_filter(pronunciation: str):
        """Format pitch accent (uppercase syllables)."""
        if not pronunciation:
            return ""
        _UPPER_RUN_RE = re.compile(r"([A-Z][A-Z']+)")
        has_upper = any(c.isupper() for c in pronunciation)
        if has_upper:
            return _UPPER_RUN_RE.sub(r'<span class="pitch-high">\1</span>', pronunciation)
        return pronunciation + ' <span class="pitch-unmarked">(accent not marked)</span>'

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    spelling.register(env)          # both spellings of a word; the switch at the top shows one (web/spelling.py)
    env.filters['format_pitch'] = format_pitch_filter

    class MockRequest:
        class Args:
            def get(self, key, default=""):
                return default
        args = Args()

    base_context = {
        "request": MockRequest(),
        "gram_class_labels": GRAM_CLASS_LABELS,
    }

    db = SkiriWebDictionary(db_path)
    cur = db.conn.cursor()

    # ---- Lessons index ----
    cur.execute("SELECT lesson_number, skiri_title, english_title, "
                "page_start, page_end, dialogues, template_ids "
                "FROM lessons ORDER BY lesson_number")
    lesson_rows = cur.fetchall()
    lessons = []
    for r in lesson_rows:
        cur.execute(
            "SELECT count(*) FROM blue_book_attestations "
            "WHERE lesson_number = ? "
            "AND context_type IN ('BASIC_WORDS','ADDITIONAL_WORDS')",
            (r["lesson_number"],))
        vocab_count = cur.fetchone()[0]
        dialogues = _json.loads(r["dialogues"] or "[]")
        lessons.append({
            "number": r["lesson_number"],
            "skiri_title": r["skiri_title"],
            "english_title": r["english_title"],
            "pages": f"{r['page_start']}–{r['page_end']}",
            "vocab_count": vocab_count,
            "dialogue_count": sum(len(d.get("lines", [])) for d in dialogues),
            "templates": _json.loads(r["template_ids"] or "[]"),
        })

    template = env.get_template("lessons.html")
    html = template.render(lessons=lessons, **base_context)
    html = _postprocess_for_static(html)
    with open(output_dir / "lessons.html", "w", encoding="utf-8") as f:
        f.write(html)

    # ---- One page per lesson ----
    template = env.get_template("lesson_detail.html")
    count = 0
    max_lesson = max(l["number"] for l in lessons) if lessons else 0
    for r in lesson_rows:
        number = r["lesson_number"]
        # the same data as the local app shows (web/learning.py): word lists, dialogues, the book's phrases
        ctx = learning.lesson_context(db.conn, number)
        lesson = ctx["lesson"]
        exercises = _build_exercises(ctx["vocab"], lesson["dialogues"], ctx["phrase_pairs"])
        prev_n = number - 1 if number > 1 else None
        next_n = number + 1 if number < max_lesson else None

        html = template.render(
            lesson=lesson, basic=ctx["basic"], additional=ctx["additional"],
            phrases=ctx["phrases"], conversations=ctx["conversations"],
            conversation_note=ctx["conversation_note"],
            dialect_statements=ctx["dialect_statements"],
            practice=[],  # sentence builder is Flask-only
            exercises=exercises, prev_n=prev_n, next_n=next_n,
            **base_context,
        )
        html = _postprocess_for_static(html)
        with open(output_dir / f"lesson-{number}.html", "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    print(f"[OK] Generated lessons.html + {count} lesson pages")
    db.close()
    return {"lessons": count}


def main():
    parser = argparse.ArgumentParser(description="Build static GitHub Pages site")
    parser.add_argument(
        "--output",
        default="docs",
        help="Output directory (default: docs/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files"
    )

    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output
    db_path = PROJECT_ROOT / "skiri_pawnee.db"

    if not db_path.exists():
        print(f"[ERR] Database not found: {db_path}")
        sys.exit(1)

    if args.dry_run:
        print(f"[?] DRY RUN: Would build to {output_dir}/")
        print("  (no files will be written)")
        return

    print(f"[>>] Building static site to {output_dir}/\n")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Run build steps
    results = {}
    try:
        results["data"] = export_dictionary_data(str(db_path), output_dir)
        results["learning"] = export_learning_data(str(db_path), output_dir)
        # Skip individual entry page generation - use client-side JS instead
        # results["entries"] = generate_entry_pages(str(db_path), output_dir)
        # results["browse"] = generate_browse_pages(str(db_path), output_dir)
        results["static"] = copy_static_assets(output_dir)
        results["printables"] = copy_printables(output_dir)
        results["pages"] = generate_static_pages(str(db_path), output_dir)
        results["flashcards"] = generate_flashcard_pages(str(db_path), output_dir)
        results["lessons"] = generate_lesson_pages(str(db_path), output_dir)
    except Exception as e:
        print(f"\n[ERR] Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print(f"\n[*] Build complete!")
    print(f"  Dictionary data: {results['data']['entries']} entries exported")
    print(f"  Learning data: {results['learning']['wordbuilding']} word derivations, "
          f"{results['learning']['verb_forms']} verb forms, {results['learning']['practice_words']} practice words")
    print(f"  Static pages: {results['pages']['pages']}")
    print(f"  Flashcard pages: {results['flashcards']['weeks']} weeks ({results['flashcards']['cards']} cards)")
    print(f"  Blue Book lessons: {results['lessons']['lessons']} pages")
    print(f"  Static files: {results['static']['files']}")
    print(f"\n[DIR] Output: {output_dir}/")
    print(f"[WEB] Ready for GitHub Pages!")
    print(f"\nNote: Entry pages generated dynamically via client-side search.js")


if __name__ == "__main__":
    main()

