#!/usr/bin/env python3
"""
Printable word list and paradigm tables (2026-11-14)
====================================================

Two documents for use away from a screen, each as a PDF and as a web page
that prints well. Nothing in them is computed: every Pawnee form is copied
from the database or from the stored copy of Parks's Appendix 1.

    python scripts/build_printables.py            # writes curriculum/printables/
    python scripts/build_printables.py --no-pdf   # the web pages only (the PDFs need PyMuPDF and the DejaVu fonts)

word_list            The flashcard words week by week, as a list: the word as
                     the dictionary spells it, the learner spelling, a rough
                     guide to saying it, the meaning, and where it stands in
                     the book. Weeks held for community review
                     (curriculum/held_for_review.json) are left out.

paradigm_tables      Parks's Appendix 1, "Illustrative Skiri Verb
                     Conjugations": seven verbs, ten modes, eleven persons,
                     770 forms, as corrected from the printed page in
                     November 2026 (extracted_data/appendix1_conjugations.json).
                     The stored file also has an English line for every form;
                     those were written by the extraction, not by Parks, and
                     are not printed here.

Build them again after the flashcard list, the database or Appendix 1 changes.
"""
import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_review_packet as packet  # noqa: E402

ROOT = packet.ROOT
OUT = ROOT / "curriculum" / "printables"
APPENDIX = ROOT / "extracted_data" / "appendix1_conjugations.json"
PERSONS = [("1sg", "I"), ("2sg", "you (one)"), ("3sg", "he, she, it"), ("1du_incl", "we two (you and I)"), ("1du_excl", "we two (not you)"),
           ("2du", "you two"), ("3du", "they two"), ("1pl_incl", "we all (with you)"), ("1pl_excl", "we all (not you)"),
           ("2pl", "you all"), ("3pl", "they all")]
TABLE_CSS = packet.CSS + """
td, th { font-size: 7.6pt; padding: 2pt; }
h2 { font-size: 13pt; page-break-before: auto; }
h2.next { page-break-before: always; }
"""
esc = packet.esc


def word_list(date):
    conn = sqlite3.connect("file:%s?mode=ro" % packet.DB.resolve().as_posix(), uri=True)
    E = packet.entries(conn)
    conn.close()
    sets = json.loads(packet.SETS.read_text(encoding="utf-8"))["weeks"]
    held = {w["week"] for w in json.loads(packet.HELD.read_text(encoding="utf-8"))["weeks"]}
    H, n = [], 0
    H.append("<h1>Pâri Pakûru' — word list</h1>")
    H.append("<p class='small'>The flashcard words of the study site, week by week. Made %s from two books: Parks and Pratt, "
             "<i>A Dictionary of Skiri Pawnee</i> (2008), and <i>Pari Pakuru'</i> (1979). “p.” is a page of the dictionary; "
             "“textbook” marks a word taken from <i>Pari Pakuru'</i>.</p>" % esc(packet.long_date(date)))
    H.append("<p class='small'>The learner spelling writes a long vowel with a circumflex and the glottal stop with an apostrophe. "
             "The guide to saying a word is rough, made from Parks's phonetic form by fixed rules; capitals mark the accented syllable. "
             "No speaker has reviewed this list yet.</p>")
    for w in sets:
        if w["week"] in held:
            continue
        cards = [E[c["entry_id"]] for c in w["cards"] if c["entry_id"] in E]
        n += len(cards)
        H.append("<h3>Week %d. %s</h3>" % (w["week"], esc(w["category_label"])))
        rows = "".join("<tr><td class='sk'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc((e["headword"] + " " + e["preverb"]).strip()), esc(e["learner"]), esc(e["say"]), esc(packet.meaning(e)), esc(packet.where(e)))
            for e in cards)
        H.append("<table><tr><th width='20%%'>Pawnee word</th><th width='17%%'>Learner spelling</th><th width='19%%'>Saying it</th>"
                 "<th>Meaning</th><th width='10%%'>Where</th></tr>%s</table>" % rows)
    return "\n".join(H), n


def paradigm_tables(date):
    data = json.loads(APPENDIX.read_text(encoding="utf-8"))
    H, forms = [], 0
    H.append("<h1>Seven Skiri verbs in full</h1>")
    H.append("<p class='small'>Parks and Pratt, <i>A Dictionary of Skiri Pawnee</i> (2008), Appendix 1, “Illustrative Skiri Verb "
             "Conjugations”: seven verbs, each in ten modes and eleven persons. The forms are as the appendix prints them; "
             "they were read again from the printed page in November 2026. Made %s. An empty cell is empty in the stored copy.</p>" % esc(packet.long_date(date)))
    for page in sorted(data, key=lambda k: int(k.split("_")[1])):
        verb = data[page]
        gloss = verb.get("english_gloss") or ""
        modes = list(verb["modes"])
        H.append("<h2%s>%s</h2>" % (" class='next'" if forms else "", esc(gloss[:1].upper() + gloss[1:])))
        for part in (modes[:5], modes[5:]):
            head = "<tr><th width='15%%'>Who</th>%s</tr>" % "".join("<th>%s</th>" % esc(m.replace("_", " ").capitalize()) for m in part)
            body = []
            for key, label in PERSONS:
                cells = []
                for m in part:
                    form = ((verb["modes"][m].get(key) or {}).get("skiri") or "").strip()
                    forms += bool(form)
                    cells.append("<td class='sk'>%s</td>" % esc(form))
                body.append("<tr><td>%s</td>%s</tr>" % (esc(label), "".join(cells)))
            H.append("<table>%s%s</table>" % (head, "".join(body)))
    return "\n".join(H), forms


def page_of(title, body, css):
    return ("<!doctype html>\n<html lang='en'><head><meta charset='utf-8'><title>%s</title><style>%s%s</style></head><body>\n%s\n</body></html>\n"
            % (esc(title), css, packet.SCREEN_CSS, body))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="the date printed on the first page (default: today)")
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    words, n_words = word_list(args.date)
    tables, n_forms = paradigm_tables(args.date)
    (OUT / "word_list.html").write_text(page_of("Pâri Pakûru' — word list", words, packet.CSS), encoding="utf-8", newline="\n")
    (OUT / "paradigm_tables.html").write_text(page_of("Seven Skiri verbs in full", tables, TABLE_CSS), encoding="utf-8", newline="\n")
    packet.out("word_list.html: %d words; paradigm_tables.html: %d forms" % (n_words, n_forms))
    if not args.no_pdf:
        a = packet.write_pdf(words, OUT / "word_list.pdf", footer="Pari Pakuru' word list")
        b = packet.write_pdf(tables, OUT / "paradigm_tables.pdf", footer="Seven Skiri verbs in full (Parks, Appendix 1)", landscape=True, css=TABLE_CSS)
        packet.out("word_list.pdf: %d pages; paradigm_tables.pdf: %d pages" % (a, b))


if __name__ == "__main__":
    main()
