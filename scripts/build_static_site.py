#!/usr/bin/env python3
"""
Build static HTML site from Flask app for GitHub Pages deployment.

Usage:
    python scripts/build_static_site.py                    # default: docs/
    python scripts/build_static_site.py --output my_site/  # custom output
    python scripts/build_static_site.py --dry-run           # preview changes

This script:
1. Exports dictionary data to JSON
2. Generates all entry pages
3. Generates browse/category pages
4. Generates lesson pages
5. Copies static assets
6. Updates templates for client-side compatibility
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

        # Flatten to JSON-serializable format
        entry_dict = {
            "entry_id": entry.entry_id,
            "headword": entry.headword,
            "normalized_form": entry.normalized_form,
            "simplified_pronunciation": entry.simplified_pronunciation,
            "grammatical_class": entry.grammatical_class,
            "verb_class": entry.verb_class,
            "blue_book_attested": entry.blue_book_attested,
            "glosses": [
                {
                    "sense_number": g.sense_number,
                    "definition": g.definition,
                    "grammatical_notes": g.grammatical_notes,
                }
                for g in (entry.glosses or [])
            ],
            "examples": [
                {
                    "skiri_text": e.skiri_text,
                    "english_gloss": e.english_gloss,
                }
                for e in (entry.examples or [])
            ],
        }
        entries.append(entry_dict)

    # Write JSON
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    with open(data_dir / "dictionary.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"[OK] Exported {len(entries)} entries to data/dictionary.json")
    db.close()
    return {"entries": len(entries)}


def generate_entry_pages(db_path: str, output_dir: Path) -> dict:
    """Generate individual entry pages."""
    print("[*] Generating entry pages...")
    from jinja2 import Environment, FileSystemLoader

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("entry.html")

    db = SkiriWebDictionary(db_path)

    # Get all entries
    cur = db.conn.cursor()
    cur.execute("SELECT entry_id FROM lexical_entries ORDER BY entry_id")
    entry_ids = [row[0] for row in cur.fetchall()]

    entries_dir = output_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for entry_id in entry_ids:
        entry = db._build_entry(entry_id)
        if not entry:
            continue

        html = template.render(entry=entry)

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

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("browse.html")

    db = SkiriWebDictionary(db_path)

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
            total=len(summaries)
        )

        page_file = browse_dir / f"{slug}.html"
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1

    print(f"[OK] Generated {count} browse pages")
    db.close()
    return {"pages": count}


def copy_static_assets(output_dir: Path) -> dict:
    """Copy CSS, JS, and other static assets."""
    print("[*] Copying static assets...")

    static_src = PROJECT_ROOT / "web" / "static"
    static_dst = output_dir / "static"

    if static_dst.exists():
        shutil.rmtree(static_dst)

    shutil.copytree(static_src, static_dst)

    # Count files
    count = sum(1 for _ in static_dst.rglob("*") if _.is_file())
    print(f"[OK] Copied {count} static files")

    return {"files": count}


def generate_static_pages(db_path: str, output_dir: Path) -> dict:
    """Generate static versions of main pages (index, about, guide, etc.)."""
    print("[*] Generating static pages...")
    from jinja2 import Environment, FileSystemLoader
    from datetime import date

    template_dir = PROJECT_ROOT / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    db = SkiriWebDictionary(db_path)
    stats = db.get_stats()

    pages_to_generate = [
        ("index.html", "index.html", {}),
        ("about.html", "about.html", {}),
        ("guide.html", "guide.html", {}),
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
                    {"skiri": "raawi", "en": "sun"},
                    {"skiri": "aatius", "en": "father"},
                    {"skiri": "piita", "en": "man"},
                    {"skiri": "capaat", "en": "woman"},
                ],
            }
            context.update(extra_context)

            html = template.render(**context)

            output_file = output_dir / output_name
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)

            count += 1
        except Exception as e:
            print(f"  [!]  Skipped {template_name}: {e}")

    print(f"[OK] Generated {count} static pages")
    db.close()
    return {"pages": count}


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
        results["entries"] = generate_entry_pages(str(db_path), output_dir)
        results["browse"] = generate_browse_pages(str(db_path), output_dir)
        results["static"] = copy_static_assets(output_dir)
        results["pages"] = generate_static_pages(str(db_path), output_dir)
    except Exception as e:
        print(f"\n[ERR] Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print(f"\n[*] Build complete!")
    print(f"  Entries: {results['entries']['entries']}")
    print(f"  Browse pages: {results['browse']['pages']}")
    print(f"  Static pages: {results['pages']['pages']}")
    print(f"  Static files: {results['static']['files']}")
    print(f"\n[DIR] Output: {output_dir}/")
    print(f"[WEB] Ready for GitHub Pages!")


if __name__ == "__main__":
    main()

