#!/usr/bin/env python3
"""
The packet for review by the Pawnee Nation's language and culture people
========================================================================

One document a reviewer can read without the repository, and a sheet to
answer on. It is built from the database and the curriculum files as they
are on the day it is made, so build it again shortly before it is sent.

    python scripts/build_review_packet.py             # writes community_review/review_packet.html, .pdf, response_sheet.csv
    python scripts/build_review_packet.py --date 2027-01-15
    python scripts/build_review_packet.py --no-pdf    # the page and the sheet only (the PDF needs PyMuPDF and the DejaVu fonts)

What is in it (the list comes from "What's next", rank 1, in the project log):

    1  Words to do with ceremony: the flashcard set that is held back, and
       every dictionary entry a keyword picked out (the entries tagged
       `ceremony`, which the public site shows in part, and the words set
       aside in the word-building guide)
    2  The flashcard word list, week by week
    3  The word-building guide: what it is, and ten questions for a speaker
       or a linguist
    4  The About page of the public site, as it now reads
    5  Three questions about sound and spelling (two kinds of short vowel;
       the word "accent"; kt and tt, r and n, which the dictionary's chapter
       on sounds says differed among speakers)
    6  Added 2026-11-15: the textbook's lessons on the site (the Nation's
       book: permission is asked); Skiri and South Band, and how the site now
       marks them; the other places to learn that the site points to; and the
       works on ceremony and song that the project knows of and has not used

Rules it keeps: every Pawnee form is copied from the database, never typed
here; a phonetic form is shown only where Parks prints one; a Blue Book word
is marked as such. The feedback table is not read.

The built files hold the held-back vocabulary in one readable place, so they
are not in git (see .gitignore). This script and community_review/README.md
are.
"""
import argparse
import csv
import datetime as dt
import html
import json
import re
import sqlite3
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "skiri_pawnee.db"
OUT = ROOT / "community_review"
SETS = ROOT / "curriculum" / "flashcard_sets.json"
HELD = ROOT / "curriculum" / "held_for_review.json"
QUEUE = ROOT / "curriculum" / "roots_v2" / "review_queue.md"
REPORT = ROOT / "curriculum" / "roots_v2" / "validation_report.md"
ABOUT = ROOT / "web" / "templates" / "about.html"
STATEMENTS = ROOT / "extracted_data" / "blue_book_dialect_statements.json"
REGISTER = ROOT / "sources" / "catalogue.json"
FONTDIR = Path("C:/Windows/Fonts")
SITE = "https://kevinsinkar.github.io/pari-pakuru/"

CSS = """
@font-face { font-family: dv; src: url(DejaVuSans.ttf); }
@font-face { font-family: dv; font-weight: bold; src: url(DejaVuSans-Bold.ttf); }
@font-face { font-family: dv; font-style: italic; src: url(DejaVuSans-Oblique.ttf); }
@font-face { font-family: dvs; src: url(DejaVuSerif.ttf); }
@font-face { font-family: dvs; font-weight: bold; src: url(DejaVuSerif-Bold.ttf); }
@font-face { font-family: dvs; font-style: italic; src: url(DejaVuSerif-Italic.ttf); }
body { font-family: dvs, "DejaVu Serif", Georgia, serif; font-size: 10.5pt; line-height: 1.4; color: #1c1c1f; }
h1 { font-family: dv, "DejaVu Sans", Arial, sans-serif; font-size: 20pt; margin-bottom: 4pt; }
h2 { font-family: dv, "DejaVu Sans", Arial, sans-serif; font-size: 14pt; margin-top: 18pt; page-break-before: always; }
h3 { font-family: dv, "DejaVu Sans", Arial, sans-serif; font-size: 11.5pt; margin-top: 12pt; }
p { margin-top: 5pt; margin-bottom: 5pt; }
li { margin-bottom: 4pt; }
table { width: 100%; border-collapse: collapse; margin-top: 6pt; }
td, th { border: 0.5pt solid #8a8a90; padding: 3pt; font-size: 9pt; vertical-align: top; text-align: left; }
th { font-family: dv, "DejaVu Sans", Arial, sans-serif; font-weight: bold; border-bottom: 1.2pt solid #55555a; }
.sk { font-weight: bold; }
.small { font-size: 9pt; color: #444448; }
.box { border: 0.75pt solid #55555a; padding: 6pt; margin-top: 8pt; margin-bottom: 8pt; }
.ask { font-family: dv, "DejaVu Sans", Arial, sans-serif; font-weight: bold; }
.line { margin-top: 14pt; border-bottom: 0.5pt solid #8a8a90; }
.quote { margin-left: 14pt; margin-right: 14pt; font-size: 9.5pt; }
"""
SCREEN_CSS = """
body { max-width: 46em; margin: 2em auto; padding: 0 1em; }
@media print { h2 { page-break-before: always; } body { margin: 0; max-width: none; } }
"""
BOX = "\u2610"


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def esc(text):
    return html.escape(text or "", quote=False)


def nfc(text):
    return unicodedata.normalize("NFC", text or "")


# ----------------------------------------------------------------------------- data

def entries(conn):
    """Every entry with what a reader of the site sees of it."""
    rows = {}
    for r in conn.execute("select entry_id, headword, coalesce(stem_preverb, ''), normalized_form, simplified_pronunciation, phonetic_form, "
                          "grammatical_class, page_number, coalesce(source, 'parks') from lexical_entries"):
        rows[r[0]] = {"entry_id": r[0], "headword": nfc(r[1]), "preverb": nfc(r[2]), "learner": nfc(r[3]), "say": nfc(r[4]),
                      "phonetic": nfc(r[5]), "class": r[6] or "", "page": r[7], "source": r[8], "glosses": [], "tags": set()}
    for eid, n, text, usage in conn.execute("select entry_id, sense_number, definition, usage_notes from glosses order by entry_id, sense_number, id"):
        if eid in rows and text:
            rows[eid]["glosses"].append(nfc(text).strip())
    for eid, tag in conn.execute("select entry_id, tag from semantic_tags"):
        if eid in rows:
            rows[eid]["tags"].add(tag)
    return rows


def meaning(e):
    g = e["glosses"]
    if len(g) <= 1:
        return "".join(g)
    return " ".join("%d. %s" % (n, t) for n, t in enumerate(g, 1))


def where(e):
    if e["source"] != "parks":
        return "textbook"
    return "p. %s" % e["page"] if e["page"] else ""


def flagged_in_guide():
    """Entry ids in section 8 of the word-building review queue (the words set aside there)."""
    text = QUEUE.read_text(encoding="utf-8")
    m = re.search(r"^## 8\. .*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return re.findall(r"`((?:SK|BB)-[^`]+)`", m.group(1)) if m else []


def ten_questions():
    text = REPORT.read_text(encoding="utf-8")
    m = re.search(r"^### The ten most important open questions.*?$(.*?)(?=^### |\Z)", text, re.S | re.M)
    return [re.sub(r"^\d+\.\s*", "", line.strip()) for line in (m.group(1) if m else "").splitlines() if re.match(r"^\d+\.", line.strip())]


class AboutText(HTMLParser):
    """The About page as headings, paragraphs and list items, without the template code."""

    def __init__(self):
        super().__init__()
        self.blocks, self.kind, self.buf = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.flush()
            self.kind = "h" if tag.startswith("h") else tag
        elif tag in ("em", "i", "cite") and self.kind:
            self.buf.append("<i>")
        elif tag in ("strong", "b") and self.kind:
            self.buf.append("<b>")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.flush()
        elif tag in ("em", "i", "cite") and self.kind:
            self.buf.append("</i>")
        elif tag in ("strong", "b") and self.kind:
            self.buf.append("</b>")

    def handle_data(self, data):
        if self.kind:
            self.buf.append(esc(data))

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        if self.kind and text:
            self.blocks.append((self.kind, text))
        self.kind, self.buf = None, []


def about_blocks():
    raw = ABOUT.read_text(encoding="utf-8")
    raw = re.sub(r"\{#.*?#\}", "", raw, flags=re.S)
    raw = re.sub(r"\{%.*?%\}", "", raw, flags=re.S)
    raw = re.sub(r"\{\{.*?\}\}", "", raw, flags=re.S)
    p = AboutText()
    p.feed(raw)
    p.flush()
    return p.blocks


def vowel_examples(conn, flagged):
    """A few plain nouns whose phonetic form has the tense short vowel, and a few with the lax one."""
    tense, lax = [], []
    for eid, hw, ph, say in conn.execute("select entry_id, headword, phonetic_form, simplified_pronunciation from lexical_entries "
                                         "where coalesce(source, 'parks') = 'parks' and grammatical_class = 'N' and phonetic_form is not null "
                                         "and length(headword) between 4 and 7 and headword not like '%,%' and headword not like '%-%' "
                                         "order by length(headword), headword"):
        if eid in flagged or not say or hw[:1].isupper():        # not the names of peoples and places
            continue
        bare = "".join(ch for ch in unicodedata.normalize("NFD", ph) if not unicodedata.combining(ch))
        has_tense = bool(re.search(r"(?<!i)i(?!i)", bare)) or bool(re.search(r"(?<!u)u(?!u)", bare))
        has_lax = "ɪ" in bare or "ʊ" in bare
        if has_tense and not has_lax and len(tense) < 3:
            tense.append(eid)
        elif has_lax and not has_tense and len(lax) < 3:
            lax.append(eid)
        if len(tense) == 3 and len(lax) == 3:
            break
    return tense, lax


def kt_examples(conn, flagged):
    """A few plain nouns the dictionary writes with kt."""
    found = []
    for eid, hw in conn.execute("select entry_id, headword from lexical_entries where coalesce(source, 'parks') = 'parks' "
                                "and grammatical_class = 'N' and headword like '%kt%' and length(headword) between 5 and 9 "
                                "and headword not like '%,%' and headword not like '%-%' order by length(headword), headword"):
        if eid not in flagged and not hw[:1].isupper():
            found.append(eid)
        if len(found) == 3:
            break
    return found


def long_date(iso):
    d = dt.date.fromisoformat(iso)
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


# ----------------------------------------------------------------------------- the document

def word_table(rows, marks, widths=("22%", "17%", "", "9%", "")):
    head = "<tr><th width='%s'>Pawnee word</th><th width='%s'>Learner spelling</th><th>Meaning the book gives</th><th width='%s'>Where</th>%s</tr>" % (
        widths[0], widths[1], widths[3], "".join("<th>%s</th>" % esc(m) for m in marks))
    body = []
    for e in rows:
        word = esc(e["headword"]) + ((" " + esc(e["preverb"])) if e["preverb"] else "")
        body.append("<tr><td class='sk'>%s</td><td>%s</td><td>%s</td><td>%s</td>%s</tr>" % (
            word, esc(e["learner"]), esc(meaning(e)), esc(where(e)), "".join("<td>%s</td>" % BOX for _ in marks)))
    return "<table>%s%s</table>" % (head, "".join(body))


def build(date):
    conn = sqlite3.connect("file:%s?mode=ro" % DB.resolve().as_posix(), uri=True)
    E = entries(conn)
    sets = json.loads(SETS.read_text(encoding="utf-8"))["weeks"]
    held = {w["week"]: w for w in json.loads(HELD.read_text(encoding="utf-8"))["weeks"]}
    tagged = {eid for eid, e in E.items() if "ceremony" in e["tags"]}
    guide = [eid for eid in flagged_in_guide() if eid in E]
    held_cards = [E[c["entry_id"]] for w in sets if w["week"] in held for c in w["cards"] if c["entry_id"] in E]
    held_ids = {e["entry_id"] for e in held_cards}
    flagged = sorted((tagged | set(guide)) - held_ids, key=lambda eid: (E[eid]["headword"].lower().lstrip("-"), eid))
    both = len(tagged & set(guide))
    shown_weeks = [w for w in sets if w["week"] not in held]
    n_cards = sum(len(w["cards"]) for w in sets)
    n_shown = sum(len(w["cards"]) for w in shown_weeks)
    tense, lax = vowel_examples(conn, tagged | set(guide))
    kt = kt_examples(conn, tagged | set(guide))
    counts = {"parks": sum(1 for e in E.values() if e["source"] == "parks"), "bb": sum(1 for e in E.values() if e["source"] != "parks")}
    # part 6: the forms the textbook itself marks (SK) or (SB), and how many it writes the South Band way
    try:
        marked = conn.execute(
            "select d.form, d.label, a.bb_english, a.lesson_number from bb_dialect_labels d "
            "join blue_book_attestations a on a.id = d.attestation_id where d.label in ('SK', 'SB') order by a.lesson_number, a.id").fetchall()
        n_spelling = conn.execute("select count(*) from bb_dialect_labels where label = 'SB spelling' and attestation_id is not null").fetchone()[0]
    except sqlite3.OperationalError:
        marked, n_spelling = [], 0
    n_rows = conn.execute("select count(*) from blue_book_attestations").fetchone()[0]
    conn.close()
    statements = json.loads(STATEMENTS.read_text(encoding="utf-8"))["statements"] if STATEMENTS.exists() else []
    register = json.loads(REGISTER.read_text(encoding="utf-8"))["records"] if REGISTER.exists() else []
    listed = [r for r in register if r["project"].get("section") and not r["project"].get("sensitive")]
    held_works = [r for r in register if r["project"].get("sensitive")]

    H = []
    a = H.append
    a("<h1>P\u00e2ri Pak\u00fbru' \u2014 for review by the Pawnee Nation</h1>")
    a("<p class='small'>A study aid for the Skiri Pawnee language, built from two printed books. Prepared %s. "
      "Public site: %s</p>" % (esc(long_date(date)), esc(SITE)))
    a("<h3>What this is, and why it comes to you</h3>")
    a("<p>This project has put two printed books about the Skiri Pawnee language into a form people can search and study from on a website: "
      "<i>A Dictionary of Skiri Pawnee</i> by Douglas R. Parks and Lula Nora Pratt (2008), and <i>Pari Pakuru'</i>, the textbook of the "
      "Pawnee Cultural Retention Committee (1979). Everything on the site was copied from those two books with computer tools. "
      "Nothing was made up. The person who built it is not a speaker of Pawnee.</p>")
    a("<p>No speaker, and no one from the Pawnee Nation, has looked at it yet. The language belongs to the Pawnee people, and some of what "
      "the books print may not be meant for everyone. Those decisions are yours and not the project's. This packet asks for them.</p>")
    a("<div class='box'><p class='ask'>What we are asking</p>"
      "<p>There are six parts. <b>Parts 1 and 6 matter most</b>; the others can wait or be left out. You do not need to answer every line. "
      "A short answer for a whole list (\u201call of these are fine\u201d, \u201cnone of these\u201d) is as useful as marks beside each word.</p>"
      "<p>1. <b>Words to do with ceremony.</b> Should they be on a public website at all, and how much of each?<br/>"
      "2. <b>The flashcard word list</b> (%d everyday words). Is anything wrong, or wrong for beginners?<br/>"
      "3. <b>The word-building guide.</b> Is this way of teaching welcome? And ten questions for a speaker or a linguist.<br/>"
      "4. <b>The \u201cAbout\u201d page.</b> Does it describe the project, and the Nation, the way you would want?<br/>"
      "5. <b>Three questions</b> about sound and spelling.<br/>"
      "6. <b>The textbook, the two dialects, and other sources.</b> May the lessons of <i>Pari Pakuru'</i> be on the site? "
      "Is the way it now marks Skiri and South Band right?</p>"
      "<p>Whatever you decide about Part 1 will be done: words can be taken off the site, shown in part, or shown in full.</p></div>" % n_shown)
    a("<p><b>How to answer.</b> Any way that suits you: write on these pages, fill in the spreadsheet that comes with them "
      "(<i>response_sheet.csv</i>, one line for each word), or simply tell us. Contact: [name], [telephone or e-mail].</p>")
    a("<p class='small'>Where things stand today: the site shows %s dictionary entries and %d words found only in the textbook. "
      "The entries the computer marked as ceremonial show their meaning and example sentences only. One flashcard set is not shown. "
      "The word-building guide is not published.</p>" % ("{:,}".format(counts["parks"]), counts["bb"]))

    # ---- part 1
    a("<h2>Part 1. Words to do with ceremony</h2>")
    a("<p>The dictionary prints words for sacred bundles, dances, doctors' societies and other ceremonial matters, with the meanings "
      "Parks and his teachers gave. A computer picked the words below by looking for English words such as \u201cceremony\u201d, "
      "\u201cbundle\u201d or \u201cdoctor\u201d in those meanings. It is a rough list: some words on it will be ordinary, and words that should "
      "be on it will be missing. That is one reason it needs you.</p>")
    a("<div class='box'><p class='ask'>Questions for Part 1</p>"
      "<p>A. Should words like these be on a public website at all?<br/>"
      "&nbsp;&nbsp;&nbsp;%s Yes &nbsp;&nbsp; %s Yes, but with the meaning only &nbsp;&nbsp; %s Only the ones marked below &nbsp;&nbsp; %s No, take them all down</p>"
      "<p>B. For words that stay: may the site show the whole dictionary entry (its verb forms, how Parks takes the word apart, "
      "related words in Arikara, Kitsai and Wichita), as it does for other words?&nbsp;&nbsp; %s Yes &nbsp;&nbsp; %s No</p>"
      "<p>C. May any of them be used in teaching material such as flashcards?&nbsp;&nbsp; %s Yes &nbsp;&nbsp; %s No &nbsp;&nbsp; %s Only the ones marked</p>"
      "<p>D. Are there other words, or kinds of words, that should be held back and are not on this list?</p>"
      "<p class='line'>&nbsp;</p><p class='line'>&nbsp;</p></div>" % ((BOX,) * 9))
    a("<h3>1a. The flashcard set that is held back (%d words)</h3>" % len(held_cards))
    a("<p>This set was made for learners under the title \u201c%s\u201d. It has not been shown since %s and will not be unless you say so.</p>" % (
        esc(next(iter(held.values()))["category_label"]) if held else "", esc(long_date(next(iter(held.values()))["held_since"])) if held else ""))
    a(word_table(held_cards, ("Teach", "Show, don't teach", "Take down")))
    a("<h3>1b. Dictionary entries the computer marked (%d more)</h3>" % len(flagged))
    a("<p>%d entries carry the site's \u201cceremony\u201d mark and show only their meaning and examples today; %d words were set aside in the "
      "word-building guide by a wider search; %d are on both lists. Together, without the %d words above, they are the %d below, "
      "in alphabetical order.</p>" % (len(tagged), len(guide), both, len(held_cards), len(flagged)))
    a(word_table([E[eid] for eid in flagged], ("Fine", "Meaning only", "Take down")))

    # ---- part 2
    a("<h2>Part 2. The flashcard word list</h2>")
    a("<p>The site offers %d weekly sets of everyday words for learners, %d words in all (the held-back set of Part 1 is not counted). "
      "A computer chose them by topic from the English meanings; nobody who knows the language has checked the choice.</p>" % (len(shown_weeks), n_shown))
    a("<div class='box'><p class='ask'>Questions for Part 2</p>"
      "<p>Mark any word that is wrong, that people do not say, or that a beginner should not start with. "
      "If everyday words are missing that every learner should know, please name them.</p></div>")
    for w in shown_weeks:
        cards = [E[c["entry_id"]] for c in w["cards"] if c["entry_id"] in E]
        a("<h3>Week %d. %s (%d words)</h3>" % (w["week"], esc(w["category_label"]), len(cards)))
        a(word_table(cards, ("Problem?",), widths=("24%", "19%", "", "10%", "")))

    # ---- part 3
    a("<h2>Part 3. The word-building guide</h2>")
    a("<p>Many Pawnee words are built from smaller pieces, and Parks's dictionary says for most words what the pieces are. "
      "The guide gathers those pieces (about 550 roots and 30 endings and prefixes) so that a learner who knows a piece can recognise it "
      "in a new word. It has fifteen lessons. It uses only what Parks prints; where he says nothing, it says nothing. "
      "It is not published, and words to do with ceremony are kept out of its lessons.</p>")
    a("<div class='box'><p class='ask'>Questions for Part 3</p>"
      "<p>A. Is this a way of teaching the language that you would welcome? &nbsp; %s Yes &nbsp; %s No &nbsp; %s We would need to see it first</p>"
      "<p>B. May it be published once a speaker or a linguist has gone over it? &nbsp; %s Yes &nbsp; %s No</p>"
      "<p>C. Is there someone who works with the language that the project should ask about the ten questions below?</p>"
      "<p class='line'>&nbsp;</p></div>" % ((BOX,) * 5))
    a("<h3>Ten questions for a speaker or a linguist</h3>")
    a("<p class='small'>These are technical. They are the places where the books leave the analysis open. Leave them out if they are not for you.</p>")
    a("<ol>%s</ol>" % "".join("<li>%s</li>" % esc(q) for q in ten_questions()))
    a("<p class='small'>A note on questions 1, 2 and 7. Parks's own chapter on sounds (p. 14) describes pieces that have a long vowel "
      "in some words and a short one in others, and says of them: \u201cThis alternation occurs frequently, but the difference in vowel "
      "length is not predictable.\u201d</p>")

    # ---- part 4
    a("<h2>Part 4. The \u201cAbout\u201d page of the site</h2>")
    a("<p>This is what the site says about itself today, word for word. It was written by the project and has not been read by anyone "
      "from the Nation.</p>")
    a("<div class='box'><p class='ask'>Questions for Part 4</p>"
      "<p>A. Is anything in it wrong, or said in a way that does not sit right?<br/>"
      "B. How should the Pawnee Nation, the Cultural Retention Committee and the speakers who taught Parks be named and thanked?<br/>"
      "C. Is there a statement the Nation would want a visitor to read on this page?</p></div>")
    for kind, text in about_blocks():
        if kind == "h":
            a("<p class='quote'><b>%s</b></p>" % text)
        elif kind == "li":
            a("<p class='quote'>\u2022 %s</p>" % text)
        else:
            a("<p class='quote'>%s</p>" % text)

    # ---- part 5
    a("<h2>Part 5. Three questions about sound and spelling</h2>")
    a("<h3>5a. Two kinds of short i and short u</h3>")
    a("<p>In his phonetic forms Parks writes the short vowels in two ways: [i] and [u] in some words, [\u026a] and [\u028a] in others. "
      "His chapter on sounds (p. 14) describes [\u026a] as the vowel of English <i>mitt</i>, [u] as the vowel of <i>flute</i> and "
      "[\u028a] as the vowel of <i>put</i>. "
      "The site's rough guide to saying a word writes \u201cih\u201d and \u201coo\u201d for both, so a learner cannot see the difference. "
      "Examples from the dictionary:</p>")
    rows = []
    for eid in tense + lax:
        e = E[eid]
        rows.append("<tr><td class='sk'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(e["headword"]), esc(e["phonetic"]), esc(e["say"]), esc(meaning(e)), esc(where(e))))
    a("<table><tr><th>Pawnee word</th><th>Parks's phonetic form</th><th>The site's guide to saying it</th><th>Meaning</th><th>Where</th></tr>%s</table>" % "".join(rows))
    a("<div class='box'><p class='ask'>Question 5a</p><p>Do speakers and teachers hear this difference, and should learners be shown it? "
      "&nbsp; %s Yes, show it &nbsp; %s No, one spelling is enough &nbsp; %s Not sure</p></div>" % ((BOX,) * 3))
    a("<h3>5b. What to call the mark on a syllable</h3>")
    a("<p>Parks writes that stress does not change the meaning of a Skiri word, and that his phonetic forms mark the <i>accented</i> syllable. "
      "The site therefore calls the mark an \u201caccent\u201d and shows the accented syllable in capitals. Earlier it said \u201cpitch\u201d.</p>")
    a("<div class='box'><p class='ask'>Question 5b</p><p>Is \u201caccent\u201d the right word for learners? What do Pawnee teachers call it?</p>"
      "<p class='line'>&nbsp;</p></div>")

    a("<h3>5c. Sounds that differed among speakers</h3>")
    a("<p>The dictionary's chapter on sounds says two things that the site does not yet tell learners.</p>")
    a("<p><b>kt and tt.</b> The dictionary writes <i>kt</i>, following the speech of Mrs. Lula Nora Pratt. Parks adds (p. 16): "
      "\u201cusers should realize that all other twentieth-century Skiri speakers replaced <i>kt</i> clusters with <i>tt</i>.\u201d "
      "Words the dictionary writes with <i>kt</i>:</p>")
    rows = []
    for eid in kt:
        e = E[eid]
        rows.append("<tr><td class='sk'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(e["headword"]), esc(e["phonetic"]), esc(meaning(e)), esc(where(e))))
    a("<table><tr><th>Pawnee word</th><th>Parks's phonetic form</th><th>Meaning</th><th>Where</th></tr>%s</table>" % "".join(rows))
    a("<p><b>r and n.</b> The chapter says (pp. 13\u201314) that <i>r</i> is usually a quick tap, and that at the start of a word many "
      "speakers often say it as <i>n</i>.</p>")
    a("<div class='box'><p class='ask'>Question 5c</p><p>Which should learners be taught to say, <i>kt</i> or <i>tt</i>? "
      "And <i>r</i> or <i>n</i> at the start of a word? Should the site tell learners that speakers differed?</p>"
      "<p class='line'>&nbsp;</p><p class='line'>&nbsp;</p></div>")

    # ---- part 6
    a("<h2>Part 6. The textbook, the two dialects, and other sources</h2>")
    a("<h3>6a. The lessons of <i>Pari Pakuru'</i> on the site</h3>")
    a("<p><i>Pari Pakuru'</i> is the Nation's book. Its copyright page reads: \u201cCopyright \u00a9 1979 by the Pawnee Indian Tribal "
      "Business Council \u2026 No part of this book may be reproduced \u2026 without permission in writing from the Pawnee Tribal "
      "Business Council.\u201d The site shows its twenty lessons: the dialogues, the word lists, the useful phrases and the notes. "
      "Permission was not asked before the site went public. It is asked now, and whatever the answer is will be done.</p>")
    a("<div class='box'><p class='ask'>Question 6a</p><p>May the lessons of <i>Pari Pakuru'</i> be on the site? "
      "&nbsp; %s Yes, as they are &nbsp; %s In part (please say which) &nbsp; %s No, take them down</p>"
      "<p class='line'>&nbsp;</p></div>" % ((BOX,) * 3))

    a("<h3>6b. Skiri and South Band</h3>")
    a("<p>The dictionary is Skiri. The textbook writes for both dialects, and says so in its chapter on the alphabet:</p>")
    for s in statements:
        if s.get("text", "").endswith("."):
            a("<p class='quote'>\u201c%s\u201d <span class='small'>(%s)</span></p>" % (
                esc(s["text"]), esc("p. " + s["book_page"] if s["book_page"] != "contents" else "contents page")))
    a("<p>The site had shown all of it as Skiri. Since November 2026 it marks a form SK or SB where the book does, and marks a form "
      "written with <i>e</i> or <i>hr</i> as \u201cSB spelling\u201d (%d of the %s words, phrases and sentences taken from the "
      "textbook). It does not respell anything and works out no Skiri form from a South Band one. Where a word is tied to a "
      "dictionary entry, the entry is shown beside it as the Skiri word. The forms the book itself marks:</p>" % (
          n_spelling, "{:,}".format(n_rows)))
    rows = ["<tr><td class='sk'>%s</td><td>%s</td><td>%s</td><td>lesson %s</td></tr>" % (
        esc(form), esc(label), esc(english or ""), esc(str(lesson))) for form, label, english, lesson in marked]
    a("<table><tr><th>As the textbook prints it</th><th>Its mark</th><th>Its English</th><th>Where</th></tr>%s</table>" % "".join(rows))
    a("<div class='box'><p class='ask'>Questions for 6b</p>"
      "<p>Is this the right way to show the two dialects to a learner of Skiri? "
      "&nbsp; %s Yes &nbsp; %s No (please say how)</p><p class='line'>&nbsp;</p>"
      "<p>Should a Skiri learner be told to say <i>i</i> wherever the textbook writes <i>e</i>, as the textbook says? "
      "&nbsp; %s Yes &nbsp; %s Not always &nbsp; %s Not sure</p>"
      "<p>How would you want South Band shown on a site whose dictionary is Skiri?</p><p class='line'>&nbsp;</p></div>" % ((BOX,) * 5))

    a("<h3>6c. Other places to learn that the site points to</h3>")
    a("<p>The site links to these and copies nothing from them. Each line is what the site says of the place.</p>")
    for r in listed:
        a("<p><b>%s.</b> %s</p>" % (esc(r["project"].get("title") or r["title"]), esc(r["project"].get("says") or "")))
    a("<div class='box'><p class='ask'>Questions for 6c</p><p>Is anything here wrong, or something the site should not point to? "
      "Is anything missing that learners should be sent to first?</p><p class='line'>&nbsp;</p>"
      "<p>May the Skiri and South Band forms of the Nation's lesson handouts be shown beside the textbook's, with the Nation named? "
      "&nbsp; %s Yes &nbsp; %s No &nbsp; %s Ask us first each time</p></div>" % ((BOX,) * 3))

    a("<h3>6d. Works the project knows of and has not used</h3>")
    a("<p>These are listed in the project's files as existing. None is linked from the site, and nothing has been taken from them. "
      "The project marked them as bound up with ceremony, song or sacred narrative by their titles and catalogue descriptions; "
      "the marking may be too wide or too narrow.</p>")
    a("<p class='small'>%s</p>" % "; ".join(esc("%s (%s)" % (r["title"], r["year"])) for r in held_works))
    a("<div class='box'><p class='ask'>Question 6d</p><p>Should any of these be named to learners? Is there one that should not "
      "be on a public list at all, or one that is missing from the list of what to keep back?</p>"
      "<p class='line'>&nbsp;</p><p class='line'>&nbsp;</p></div>")

    # ---- sources
    a("<h2>Where the words in this packet come from</h2>")
    a("<p>Douglas R. Parks and Lula Nora Pratt, <i>A Dictionary of Skiri Pawnee</i> (Lincoln: University of Nebraska Press, 2008). "
      "A page number beside a word is the page of that book.</p>")
    a("<p>Pawnee Cultural Retention Committee, <i>Pari Pakuru'</i> (1979). \u201cTextbook\u201d beside a word means the word is in the textbook "
      "and not in the dictionary; it is written here in the dictionary's letters.</p>")
    a("<p>The \u201clearner spelling\u201d is the project's own: a circumflex for a long vowel and an apostrophe for the glottal stop. "
      "It is made from the dictionary spelling letter by letter and adds nothing.</p>")
    a("<p class='small'>The dictionary entries were compared with the printed pages value by value in November 2026. "
      "The record of that, and everything else about the project, is in its repository: https://github.com/kevinsinkar/pari-pakuru</p>")

    sheet = [("part", "list", "entry_id", "pawnee_word", "learner_spelling", "meaning", "where", "decision", "note")]
    for e in held_cards:
        sheet.append(("1a", "held flashcard set", e["entry_id"], (e["headword"] + " " + e["preverb"]).strip(), e["learner"], meaning(e), where(e), "", ""))
    for eid in flagged:
        e = E[eid]
        which = "site mark and guide" if eid in tagged and eid in guide else ("site mark" if eid in tagged else "guide")
        sheet.append(("1b", "marked by computer: " + which, eid, (e["headword"] + " " + e["preverb"]).strip(), e["learner"], meaning(e), where(e), "", ""))
    for w in shown_weeks:
        for c in w["cards"]:
            if c["entry_id"] in E:
                e = E[c["entry_id"]]
                sheet.append(("2", "week %d: %s" % (w["week"], w["category_label"]), e["entry_id"], (e["headword"] + " " + e["preverb"]).strip(),
                              e["learner"], meaning(e), where(e), "", ""))
    facts = {"held": len(held_cards), "flagged": len(flagged), "tagged": len(tagged), "guide": len(guide), "weeks": len(shown_weeks),
             "words": n_shown, "all_words": n_cards, "questions": len(ten_questions()), "about_blocks": len(about_blocks()),
             "examples": len(tense) + len(lax) + len(kt), "marked": len(marked), "listed": len(listed), "held_works": len(held_works)}
    return "\n".join(H), sheet, facts


def write_pdf(body, path, footer="Pari Pakuru' review packet", landscape=False, css=None):
    import io

    import fitz
    buf = io.BytesIO()
    story = fitz.Story(html=body, user_css=css or CSS, archive=fitz.Archive(str(FONTDIR)))
    writer = fitz.DocumentWriter(buf)
    w, h = (792, 612) if landscape else (612, 792)
    page, box = fitz.Rect(0, 0, w, h), fitz.Rect(54, 50, w - 54, h - 62)
    more = 1
    while more:
        dev = writer.begin_page(page)
        more, _ = story.place(box)
        story.draw(dev)
        writer.end_page()
    writer.close()
    doc = fitz.open("pdf", buf.getvalue())
    for n, pg in enumerate(doc, 1):
        foot = "%s     page %d of %d" % (footer, n, len(doc))
        pg.insert_text((54, h - 32), foot, fontsize=8, color=(0.4, 0.4, 0.42))
    doc.subset_fonts()
    doc.save(str(path), garbage=3, deflate=True)
    pages = len(doc)
    doc.close()
    return pages


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="the date printed on the first page (default: today)")
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()
    body, sheet, facts = build(args.date)
    OUT.mkdir(exist_ok=True)
    page = ("<!doctype html>\n<html lang='en'><head><meta charset='utf-8'><title>P\u00e2ri Pak\u00fbru' \u2014 review packet</title>"
            "<style>%s%s</style></head><body>\n%s\n</body></html>\n" % (CSS, SCREEN_CSS, body))
    (OUT / "review_packet.html").write_text(page, encoding="utf-8", newline="\n")
    with (OUT / "response_sheet.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(sheet)
    out("review_packet.html written; response_sheet.csv: %d lines" % (len(sheet) - 1))
    if not args.no_pdf:
        out("review_packet.pdf: %d pages" % write_pdf(body, OUT / "review_packet.pdf"))
    out("Part 1: %(held)d held flashcard words and %(flagged)d more entries marked by computer (%(tagged)d with the site's mark, "
        "%(guide)d set aside in the guide). Part 2: %(words)d words in %(weeks)d weekly sets (of %(all_words)d in the frozen list). "
        "Part 3: %(questions)d questions. Part 4: %(about_blocks)d blocks of the About page. Part 5: %(examples)d example words. "
        "Part 6: %(marked)d forms the textbook marks SK or SB, %(listed)d places the site points to, %(held_works)d works held back." % facts)


if __name__ == "__main__":
    main()
