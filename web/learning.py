"""What the learning pages show: word building, verbs, practice, topics.

Used by the local app (web/app.py, routes /words, /verbs, /practice, /data/...)
and by scripts/build_static_site.py, which writes the same data to docs/data/.

The rule of the public site holds here: nothing in this file makes a form.
Every Skiri form it returns is copied from a printed source:

    wordbuilding   Parks's derivation of an entry (the angled brackets of the
                   dictionary), cut at the plus signs he prints; his tables 4
                   and 5; his abbreviations
    verbs          Appendix 1 (seven verbs in full), Appendix 2, the tables of
                   chapter 4, and the five numbered forms of a verb entry
    practice       the flashcard weeks, as the flashcard pages show them
    lessons        the Blue Book lessons as the tables hold them (lesson_context)
    phrases        the lessons' Useful Phrases and the two conversations of
                   lesson 20, listed by situation in
                   curriculum/everyday_phrases.json; every line must stand in
                   the lessons' text or the page is not built (phrases_data)

What the pages add is arrangement: words that share a printed piece are listed
together, a phonetic form is cut at its syllable dots. The project's own
word-construction analysis (curriculum/roots_v2) is not used: it waits for
review by a person who knows the language (project log, open item 1).

Entries tagged "ceremony" are left out of the word-building data, as their
derivations are left out of the search results (open item 50).
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = PROJECT_ROOT / "extracted_data"

# ---------------------------------------------------------------------------
# Parks's derivations
# ---------------------------------------------------------------------------
# The dictionary prints a derivation in angled brackets:  <kaaʔas+as+uʔ, automobile foot + NOM>
# A plus sign stands between major constituents, a dot joins the parts of a compound stem, a hyphen marks a
# bound form, parentheses an optional sound or a preverb note, and a literal translation follows the comma
# (chapter 5, pp. 55-56; summary in extracted_data/organization_of_the_dictionary.json).
#
# split_derivation() cuts the printed string at its plus signs and does nothing else. It does not say which
# word of the literal translation belongs to which piece: the translation is not in the order of the pieces
# (<waa+waapic, flash + DIST>), and pairing them is the analysis that waits for review.

_NOTE_START = re.compile(r"^(i\.q\.|cf\.|onom\.|var\. of\b)", re.I)
_LOAN_START = re.compile(
    r"^(Engl?\.|Sp\.|Fr\.|Wi\.|Sioux\b|from\b|prob\. from\b|borrow|ultimately\b|of unknown origin)", re.I)
_HEDGE = re.compile(r"^(prob\.|perh\.|perhaps|apparently|possibly|poss\.)\s+", re.I)
_PREVERB_NOTE = re.compile(r"\(\s*[a-z]+(?:\s*\.\s*\.\s*\.\s*[a-z]+)*\s*\.\s*\.\s*\.\s*\)")
_MORPH_OK = re.compile(r"^[a-zʔØ()\-./+ ]+$")
_LABEL_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]+(?:[./][A-Z0-9]+)*\b")


def _plain(text: str) -> str:
    """Without accent marks."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def split_derivation(raw: str | None) -> dict | None:
    """The pieces of one printed derivation, or None when it is not an analysis into two or more pieces.

    Returns {"units": [...], "keys": [...], "literal": str | None} and, when they apply,
    "unsure": True (Parks hedges: "prob.", "?") and "words": [...] (the derivation is a phrase of several words).

    units   each piece exactly as printed between the plus signs, preverb note included
    keys    the same piece in plain letters (no hyphen, no parentheses, no note), for listing together the
            words in which Parks prints the same piece
    """
    if not raw or not raw.strip():
        return None
    s = re.sub(r"\s+", " ", unicodedata.normalize("NFC", raw)).strip()
    if s.startswith("<"):
        s = s[1:]
    if s.endswith(">"):
        s = s[:-1]
    s = s.strip()
    if not s or _NOTE_START.match(s) or _LOAN_START.match(s):
        return None                                   # a cognate note or a loan: no analysis
    unsure = False
    hedge = _HEDGE.match(s)
    if hedge:
        unsure = True
        s = s[hedge.end():]
    morph, _, literal = s.split(";")[0].partition(",")
    morph = re.sub(r"\[[^\]]*\]", " ", morph)
    morph = re.sub(r"\(([a-z .]+)\)", lambda m: "(" + m.group(1).replace(" ", "") + ")", morph)   # ( u t . . . )
    if "?" in morph:
        unsure = True
        morph = morph.replace("?", " ")
    morph = re.sub(r"\s*\+\s*", "+", morph)
    morph = re.sub(r"-\s+(?=[a-zʔ])", "", morph)        # a hyphen at the end of a printed line
    morph = re.sub(r"\s*\.\s*(?=[a-zʔ(])", ".", morph).strip()
    literal = literal.strip()
    if _LOAN_START.match(literal) or re.search(r"\bfrom [A-Z]", literal):
        return None
    literal = re.split(r"\b(?:cf\.|i\.q\.|lit\.|ref\. to|originally ref)", literal)[0].strip(" ,")
    if not morph or not _MORPH_OK.match(_plain(morph)):
        return None

    units, keys, words = [], [], []
    word_index = -1
    for word in (w for w in re.split(r"\s+(?![^()]*\))", morph) if w):
        if _PREVERB_NOTE.fullmatch(word):               # a note written after a space belongs to the piece before it
            if units:
                units[-1] += " " + word
            continue
        word_index += 1
        for unit in word.split("+"):
            unit = unit.strip()
            key = re.sub(r"[()\-\s]", "", _plain(_PREVERB_NOTE.sub("", unit)).lower()).replace("ø", "Ø")
            key = ".".join(part for part in key.split(".") if part)
            if not key:
                if unit and units:
                    units[-1] += " " + unit
                continue
            units.append(unit)
            keys.append(key)
            words.append(word_index)
    if len(keys) < 2 or sum(1 for k in keys if len(k) == 1) >= 4:    # one piece, or letter-spaced debris
        return None
    if any(u.count("(") != u.count(")") for u in units):             # a parenthesis that spans a plus sign
        return None
    result = {"units": units, "keys": keys, "literal": literal or None}
    if unsure:
        result["unsure"] = True
    if words and words[-1] > 0:
        result["words"] = words
    return result


def held_entry_ids(conn: sqlite3.Connection) -> set:
    """Entries tagged "ceremony": headword, senses and examples only, until the community review."""
    return {r[0] for r in conn.execute("SELECT DISTINCT entry_id FROM semantic_tags WHERE tag = 'ceremony'")}


def _tables(*numbers: int) -> dict:
    """Tables of chapter 4 as printed (extracted_data/grammatical_overview_tables.json)."""
    data = json.loads((EXTRACTED / "grammatical_overview_tables.json").read_text(encoding="utf-8"))
    wanted = {}
    for table in data["tables"]:
        if table["number"] not in numbers:
            continue
        rows = table.get("rows") or table.get("rows_second_reading") or []
        wanted[str(table["number"])] = {
            "title": table["title"],
            "pages": table.get("book_pages") or [],
            "rows": rows,
        }
    return wanted


def abbreviations(conn: sqlite3.Connection) -> dict:
    """Parks's abbreviations: label -> what it stands for (and the forms he lists for it)."""
    labels = {}
    for abbr, meaning, form in conn.execute(
            "SELECT abbreviation, meaning, morpheme_form FROM morpheme_abbreviations ORDER BY id"):
        if abbr and meaning and abbr not in labels:
            labels[abbr] = {"meaning": meaning, "forms": form or None}
    return labels


def wordbuilding_data(conn: sqlite3.Connection) -> dict:
    """Every entry whose printed derivation has two or more pieces, with the pieces."""
    held = held_entry_ids(conn)
    entries = []
    seen = set()
    for entry_id, headword, preverb, cls, raw, gloss in conn.execute("""
            SELECT l.entry_id, l.headword, l.stem_preverb, l.grammatical_class, e.raw_etymology,
                   (SELECT definition FROM glosses g WHERE g.entry_id = l.entry_id ORDER BY sense_number LIMIT 1)
            FROM lexical_entries l JOIN etymology e ON e.entry_id = l.entry_id
            WHERE coalesce(l.source, 'parks') <> 'blue_book'
            ORDER BY l.headword COLLATE NOCASE, l.entry_id, e.id"""):
        if entry_id in held or entry_id in seen:
            continue
        parts = split_derivation(raw)
        if not parts:
            continue
        seen.add(entry_id)
        row = {
            "id": entry_id,
            "w": (headword + (" " + preverb if preverb else "")).strip(),
            "cls": cls or "",
            "g": (gloss or "").strip(),
            "u": parts["units"],
            "k": parts["keys"],
            "lit": parts["literal"],
        }
        if parts.get("unsure"):
            row["unsure"] = True
        if parts.get("words"):
            row["words"] = parts["words"]
        entries.append(row)

    all_labels = abbreviations(conn)
    used = set()
    for row in entries:
        for token in _LABEL_TOKEN.findall(row["lit"] or ""):
            used.add(token)
            used.update(re.split(r"[./]", token))

    # Dictionary entries spelled like a piece. Parks does not say which entry a piece is, and several entries
    # often share a spelling, so the page lists them all and says so.
    piece_keys = {k.replace(".", "") for row in entries for k in row["k"]}
    heads = {}
    for entry_id, headword, preverb, cls, gloss in conn.execute("""
            SELECT l.entry_id, l.headword, l.stem_preverb, l.grammatical_class,
                   (SELECT definition FROM glosses g WHERE g.entry_id = l.entry_id ORDER BY sense_number LIMIT 1)
            FROM lexical_entries l WHERE coalesce(l.source, 'parks') <> 'blue_book'
            ORDER BY l.headword COLLATE NOCASE, l.entry_id"""):
        key = re.sub(r"[\s\-.()]", "", _plain(headword or "").lower()).replace("ø", "Ø")
        if key in piece_keys:
            heads.setdefault(key, []).append({
                "id": entry_id, "w": (headword + (" " + preverb if preverb else "")).strip(),
                "cls": cls or "", "g": (gloss or "").strip()})

    by_headword = {row["w"]: row["id"] for row in entries}
    examples = [by_headword[w] for w in EXAMPLE_WORDS if w in by_headword]
    return {
        "about": "Parks and Pratt, A Dictionary of Skiri Pawnee (2008): the derivation printed in angled brackets "
                 "in each entry, cut at its plus signs. Nothing here was worked out by a program.",
        "entries": entries,
        "heads": heads,
        "examples": examples,
        "labels": {k: v for k, v in all_labels.items() if k in used},
        "tables": _tables(4, 5),
    }


# Entries the word-building page opens with: short words whose printed derivation is easy to follow.
EXAMPLE_WORDS = ["iksuʔ", "asaaki", "pakskuukuʔuʔ", "asuuruʔ", "kaaʔat", "atiktaka"]


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
PERSONS = [
    ("1sg", "I"), ("2sg", "you (one)"), ("3sg", "he, she, it"),
    ("1du_incl", "we two (you and I)"), ("1du_excl", "we two (not you)"), ("2du", "you two"), ("3du", "they two"),
    ("1pl_incl", "we all (with you)"), ("1pl_excl", "we all (not you)"), ("2pl", "you all"), ("3pl", "they all"),
]

# The ten modes of Appendix 1, and the row of Table 8 (mode, subordinate or not) that describes each.
MODES = [
    ("indicative_perfective", "Indicative", False, "Indicative"),
    ("negative_indicative_perfective", "Negative indicative", False, "Negative Indicative"),
    ("contingent_perfective", "Contingent", False, "Contingent"),
    ("assertive_perfective", "Assertive", False, "Assertive"),
    ("absolutive_perfective", "Absolutive", False, "Absolutive"),
    ("potential_perfective", "Potential", False, "Potential"),
    ("gerundial_perfective_subordinate", "Gerundial", True, "Absolutive"),
    ("contingent_perfective_subordinate", "Contingent (conditional)", True, "Contingent"),
    ("subjunctive_perfective_subordinate", "Subjunctive", True, "Subjunctive"),
    ("infinitive_perfective_subordinate", "Infinitive", True, "Infinitive"),
]

# What the five numbered forms of a verb entry are (chapter 5, p. 56). The same labels as search.js.
FORM_LABELS = {
    1: "1st person singular, indicative, perfective",
    2: "3rd person singular, indicative, perfective",
    3: "3rd person singular, indicative, imperfective",
    4: "3rd person singular, absolutive, subordinate perfective",
    5: "3rd person singular, indicative, perfective intentive",
}
# Rough plain-English lines for the same five forms. They are the site's, not the dictionary's.
FORM_PLAIN = {
    1: "“I …”: a plain statement about myself",
    2: "“he …” or “she …”: the same statement about someone else",
    3: "“he is …ing”: the action going on, not finished",
    4: "the form used inside a longer sentence: “when he …”, “that he …”",
    5: "“he is going to …”: what someone is about to do",
}


def _table8_row(rows: list, mode_name: str, subordinate: bool) -> dict | None:
    want = "Subordinate" if subordinate else "Non-subordinate"
    for row in rows[1:]:
        if len(row) >= 4 and row[0].startswith(mode_name + " ") and row[1].strip() == want:
            # "Negative Indicative NEG.IND" also starts with nothing else; "Indicative IND" must not match it
            return {"mode": row[0], "forms": row[2],
                    "functions": [f.strip() for f in row[3].split("•") if f.strip()]}
    return None


def _entry_with_forms(conn: sqlite3.Connection, first: str, third: str) -> dict | None:
    """The dictionary entry whose printed forms 1 and 2 are these two printed forms of Appendix 1.

    A tie by two printed forms, not by meaning; None unless exactly one entry fits."""
    rows = conn.execute("""
        SELECT l.entry_id, l.headword, l.stem_preverb, l.grammatical_class, l.verb_class
        FROM lexical_entries l
        JOIN paradigmatic_forms a ON a.entry_id = l.entry_id AND a.form_number = 1 AND a.skiri_form = ?
        JOIN paradigmatic_forms b ON b.entry_id = l.entry_id AND b.form_number = 2 AND b.skiri_form = ?""",
                        (first, third)).fetchall()
    if len(rows) != 1:
        return None
    entry_id, headword, preverb, cls, verb_class = rows[0]
    forms = [{"n": n, "form": f} for n, f in conn.execute(
        "SELECT form_number, skiri_form FROM paradigmatic_forms WHERE entry_id = ? ORDER BY form_number", (entry_id,))]
    gloss = conn.execute(
        "SELECT definition FROM glosses WHERE entry_id = ? ORDER BY sense_number LIMIT 1", (entry_id,)).fetchone()
    return {"id": entry_id, "w": (headword + (" " + preverb if preverb else "")).strip(),
            "cls": " ".join(x for x in (cls, verb_class) if x), "g": gloss[0] if gloss else "", "forms": forms}


def verbs_data(conn: sqlite3.Connection) -> dict:
    """Appendix 1 and Appendix 2 as printed, the tables of chapter 4, and the five forms of an entry."""
    appendix = json.loads((EXTRACTED / "appendix1_conjugations.json").read_text(encoding="utf-8"))
    tables = _tables(6, 8, 9, 10, 13, 15, 16, 17)
    held = held_entry_ids(conn)
    verbs = []
    for page in sorted(appendix, key=lambda k: int(k.split("_")[1])):
        verb = appendix[page]
        modes = {}
        for key, _label, _sub, _name in MODES:
            cells = verb["modes"].get(key) or {}
            # the English line stored beside each form was written by the extraction, not by Parks: left out
            modes[key] = {person: ((cells.get(person) or {}).get("skiri") or "").strip() for person, _ in PERSONS}
        indicative = modes["indicative_perfective"]
        entry = _entry_with_forms(conn, indicative["1sg"], indicative["3sg"])
        if entry and entry["id"] in held:
            entry = None
        verbs.append({"gloss": verb.get("english_gloss") or "", "modes": modes, "entry": entry})

    rows8 = tables["8"]["rows"]
    modes = []
    for key, label, subordinate, name in MODES:
        modes.append({"key": key, "label": label, "subordinate": subordinate,
                      "table8": _table8_row(rows8, name, subordinate)})

    irregular = json.loads((EXTRACTED / "appendix2_irregular_roots.json").read_text(encoding="utf-8"))
    roots = []
    for root in irregular:
        singular = root.get("singular_stem") or ""
        if root.get("headword") == "tir":
            singular = ""        # the cell is empty on the printed page (project log, open item 45)
        roots.append({"w": root.get("headword") or "", "g": root.get("english_gloss") or "", "sg": singular,
                      "du": root.get("dual_stem") or "", "pl": root.get("plural_stem") or "",
                      "note": root.get("notes") or ""})

    return {
        "about": "Parks and Pratt, A Dictionary of Skiri Pawnee (2008): Appendix 1 (seven verbs in full), "
                 "Appendix 2, and tables 6 to 17 of chapter 4, as printed.",
        "persons": [{"key": k, "label": label} for k, label in PERSONS],
        "modes": modes,
        "verbs": verbs,
        "form_labels": {str(k): v for k, v in FORM_LABELS.items()},
        "form_plain": {str(k): v for k, v in FORM_PLAIN.items()},
        "tables": tables,
        "irregular_roots": roots,
    }


# ---------------------------------------------------------------------------
# Practice: the flashcard weeks
# ---------------------------------------------------------------------------
def practice_data(db_path: str) -> dict:
    """The flashcard words week by week, as the flashcard pages show them. Weeks held for review are left out."""
    from web.flashcards import load_sets

    weeks = []
    for fset in load_sets(db_path):
        cards = []
        for card in fset.cards:
            parks = card.headword or ""
            learner = card.normalized_form if card.normalized_form and card.normalized_form != parks else parks
            if not learner or not card.definition:
                continue
            cards.append({
                "id": card.entry_id,
                "w": learner,
                "p": parks if parks != learner else "",
                "say": card.simplified_pronunciation or "",
                "ipa": card.phonetic_form or "",
                "def": card.definition,
                "cls": card.grammatical_class or "",
                "bb": card.source == "blue_book",
            })
        weeks.append({"week": fset.week, "label": fset.category_label, "cards": cards})
    return {"weeks": weeks}


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------
# The topic tags were given by English keywords (phase 2.1). "ceremony" is not offered as a topic.
# The labels are those of the flashcard weeks (curriculum/flashcard_sets.json).
TOPIC_LABELS = {
    "kinship": "Family & Kinship", "number": "Numbers & Counting", "animal": "Animals", "body": "Body & Health",
    "food": "Food & Cooking", "clothing": "Clothing & Adornment", "housing": "Home & Shelter",
    "color": "Colors & Appearance", "celestial": "Sky, Stars & Weather", "water": "Water & Rivers",
    "plant": "Plants & Trees", "tool": "Tools & Objects", "land": "Land & Earth", "emotion": "Feelings & Emotions",
    "social": "People & Society", "speech": "Language & Communication", "motion": "Movement & Travel",
    "location": "Places & Directions",
}


def topics_data(conn: sqlite3.Connection) -> list:
    counts = dict(conn.execute("SELECT tag, count(DISTINCT entry_id) FROM semantic_tags GROUP BY tag"))
    return [{"tag": tag, "label": label, "count": counts.get(tag, 0)}
            for tag, label in TOPIC_LABELS.items() if counts.get(tag)]


# ---------------------------------------------------------------------------
# The Blue Book: the lesson pages and the phrases
# ---------------------------------------------------------------------------
# The scan of Pari Pakuru' has 28 pages before the page the book numbers 1. The tables store pages of the scan;
# a reader holding the book needs the number printed on the page.
BLUE_BOOK_PAGE_OFFSET = 28
PHRASES_FILE = PROJECT_ROOT / "curriculum" / "everyday_phrases.json"
DIALECT_NAMES = {"SK": "Skiri", "SB": "South Band"}       # the book writes (SK) and (SB) after a form
DIALECT_FILE = EXTRACTED / "blue_book_dialect_statements.json"
SOURCES_FILE = PROJECT_ROOT / "sources" / "catalogue.json"


def south_band_spelling(form: str | None) -> list:
    """Why a printed Blue Book form is written the South Band way, by the book's own alphabet chapter:
    ["e"], ["hr"], both, or [] (extracted_data/blue_book_dialect_statements.json has the statements).

    It looks at the printed letters and nothing else. It does not say how a Skiri speaker says the word, and no
    form is made from it."""
    plain = _plain(form or "").lower()
    return [mark for mark in ("e", "hr") if mark in plain]


def _sb_spelling_mark(text: str | None) -> bool:
    """A line gets the mark "SB spelling" when it is written with e or hr and the book puts no mark of its own on it."""
    text = text or ""
    return bool(south_band_spelling(text)) and "(SK)" not in text and "(SB)" not in text


def dialect_statements() -> dict:
    """What Pari Pakuru' says of its two dialects, as read from the scan."""
    return json.loads(DIALECT_FILE.read_text(encoding="utf-8"))


def dialect_labels(conn: sqlite3.Connection) -> dict:
    """Blue Book row id or Blue Book-only entry id -> {"label", "basis", "skiri_entry_id"}, from the table
    bb_dialect_labels (scripts/label_bluebook_dialect.py). {} if the table has not been made."""
    try:
        rows = conn.execute("SELECT attestation_id, entry_id, label, basis, skiri_entry_id FROM bb_dialect_labels").fetchall()
    except sqlite3.OperationalError:
        return {}
    return {(r[0] if r[0] is not None else r[1]): {"label": r[2], "basis": r[3], "skiri_entry_id": r[4]} for r in rows}


# The page "Learn with others": the sections, and what stands over each.
SOURCE_SECTIONS = [
    ("nation", "Learn with the Pawnee Nation",
     "The language is the Pawnee people's, and the Nation teaches it. Begin there, and trust what you learn there before this site."),
    ("hear", "Hear the language", "This site cannot let you hear a word. These can."),
    ("read", "Read", "From the Pawnee Nation's own language project."),
]


def sources_data() -> list:
    """The sources the page "Learn with others" lists, by section (sources/catalogue.json).

    Only records the register marks for learners are returned; a record marked as ceremonial never is. The
    sentence shown for a source is the project's, written from what the source's page was seen to say; the
    catalogue's own credibility scores are not shown."""
    data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    sections = []
    for key, label, about in SOURCE_SECTIONS:
        items = []
        for r in data["records"]:
            p = r["project"]
            if p.get("section") != key or p.get("sensitive") or not p.get("link"):
                continue
            dialect = r.get("dialect") or ""
            items.append({"key": r["key"], "title": p.get("title") or r["title"], "says": p.get("says") or "",
                          "url": p.get("url") or r["url"], "dialect": "" if dialect.lower().startswith("not ") else dialect,
                          "access": r.get("access") or "", "seen": (p.get("checked") or {}).get("on") or ""})
        sections.append({"key": key, "label": label, "about": about, "items": items})
    return sections


def _stands(text: str, piece: str) -> bool:
    """A piece stands in a text as whole words."""
    return bool(re.search(r"(?<!\S)" + re.escape(piece) + r"(?!\S)", text or ""))


def _lesson_notes(conn: sqlite3.Connection) -> dict:
    return {n: json.loads(raw or "[]") for n, raw in conn.execute("SELECT lesson_number, grammar_notes FROM lessons")}


def phrase_problems(conn: sqlite3.Connection, data: dict | None = None) -> list:
    """What in curriculum/everyday_phrases.json does not stand, letter for letter, in the lessons' text.

    The file holds copied forms. Every Pawnee line, its dialect label and its English must stand in a note of its
    lesson headed "Useful Phrases" or "Useful Conversations" (the page reading of the lessons). Whether a line
    and its English also share a row of the printed page is checked by scripts/everyday_phrases.py, which needs
    the scan."""
    data = data or json.loads(PHRASES_FILE.read_text(encoding="utf-8"))
    notes = _lesson_notes(conn)
    known = {s["key"] for s in data["situations"]}
    problems = []

    def texts(lesson, heading):
        return [n.get("text") or "" for n in notes.get(lesson, []) if n.get("heading") == heading]

    for p in data["phrases"]:
        where = texts(p["lesson"], "Useful Phrases")
        form = p["skiri"] + (" (%s)" % p["dialect"] if p.get("dialect") else "")
        if not any(_stands(t, form) for t in where):
            problems.append("lesson %d: %r is not in the Useful Phrases" % (p["lesson"], form))
        for piece in filter(None, [p.get("english"), p.get("also_printed")]):
            if not any(_stands(t, piece) for t in where):
                problems.append("lesson %d: the English %r is not in the Useful Phrases" % (p["lesson"], piece))
        if not p.get("english") and not (p.get("same_meaning_as_line_above") or p.get("printed_after_or")):
            problems.append("lesson %d: %r has no English and no reason" % (p["lesson"], p["skiri"]))
        if p.get("printed_after_or") and not any(("or " + p["skiri"]) in t for t in where):
            problems.append("lesson %d: %r is not printed after 'or'" % (p["lesson"], p["skiri"]))
        if p.get("situation") not in known:
            problems.append("lesson %d: %r has the unknown situation %r" % (p["lesson"], p["skiri"], p.get("situation")))
        if p.get("dialect") and p["dialect"] not in DIALECT_NAMES:
            problems.append("lesson %d: unknown dialect label %r" % (p["lesson"], p["dialect"]))
    for conv in data["conversations"]:
        where = texts(conv["lesson"], "Useful Conversations")
        for line in conv["lines"]:
            for piece in (line["skiri"], line["english"]):
                if not any(_stands(t, piece) for t in where):
                    problems.append("lesson %d, conversation %d: %r is not in the Useful Conversations" % (conv["lesson"], conv["number"], piece))
    for note in data.get("notes_of_the_book", []):
        if not any(note["text"] in (n.get("text") or "") for n in notes.get(note["lesson"], [])):
            problems.append("lesson %d: the book's note %r is not in the lesson" % (note["lesson"], note["text"][:40]))
    return problems


def _phrase_key(skiri: str) -> str:
    return skiri.rstrip(".!?,").strip()


def phrases_data(conn: sqlite3.Connection) -> dict:
    """The lessons' Useful Phrases, by lesson and by situation, and the two conversations of lesson 20.

    {"by_lesson": {lesson: [row]}, "situations": [{key, label, about, rows: [row]}], "conversations": [...],
     "notes": {...}, "count": phrases, "lessons": lessons with phrases}

    A row is one numbered item of the book: {"forms": [{skiri, dialect, dialect_name, after_or}],
    "printings": [{lesson, english}], "also": [str]}. A second dialect's form, or a form printed after "or",
    belongs to the row of the item it stands under. In a situation, the same phrase printed in two lessons is
    one row with both printings: where the book gives it two English renderings, both are shown.
    Raises ValueError if a line of the file does not stand in the lessons' text."""
    data = json.loads(PHRASES_FILE.read_text(encoding="utf-8"))
    problems = phrase_problems(conn, data)
    if problems:
        raise ValueError("curriculum/everyday_phrases.json: " + "; ".join(problems[:5]))

    rows, last = [], None
    for p in data["phrases"]:
        form = {"skiri": p["skiri"], "dialect": p.get("dialect") or "", "dialect_name": DIALECT_NAMES.get(p.get("dialect"), ""),
                "after_or": bool(p.get("printed_after_or")),
                # no mark of the book's own, and written with e or hr: the South Band spelling by the book's rule
                "sb_spelling": not p.get("dialect") and bool(south_band_spelling(p["skiri"]))}
        same_item = (last is not None and last["lesson"] == p["lesson"] and p.get("number") is not None
                     and last["number"] == p.get("number")
                     and (not p.get("english") or p["english"] == last["printings"][0]["english"]))
        if same_item:
            last["forms"].append(form)
            continue
        last = {"lesson": p["lesson"], "number": p.get("number"), "situation": p["situation"], "forms": [form],
                "printings": [{"lesson": p["lesson"], "english": p.get("english") or ""}],
                "also": [p["also_printed"]] if p.get("also_printed") else []}
        rows.append(last)

    by_lesson = {}
    for row in rows:
        by_lesson.setdefault(row["lesson"], []).append(row)

    situations = []
    for s in data["situations"]:
        merged, index = [], {}
        for row in rows:
            if row["situation"] != s["key"]:
                continue
            key = (_phrase_key(row["forms"][0]["skiri"]), row["forms"][0]["dialect"]) if len(row["forms"]) == 1 else None
            if key is not None and key in index:
                index[key]["printings"].extend(row["printings"])
                continue
            copy = {"forms": row["forms"], "printings": list(row["printings"]), "also": row["also"]}
            merged.append(copy)
            if key is not None:
                index[key] = copy
        for row in merged:
            # one English with the lessons that print it, in the order they print it
            glosses = []
            for printing in row["printings"]:
                found = next((g for g in glosses if g["english"] == printing["english"]), None)
                if found:
                    found["lessons"].append(printing["lesson"])
                else:
                    glosses.append({"english": printing["english"], "lessons": [printing["lesson"]]})
            row["glosses"] = glosses
        situations.append({"key": s["key"], "label": s["label"], "about": s["about"], "rows": merged})

    for conv in data["conversations"]:
        for line in conv["lines"]:
            line["sb_spelling"] = _sb_spelling_mark(line["skiri"])
    return {
        "by_lesson": by_lesson,
        "situations": situations,
        "conversations": data["conversations"],
        "notes": {n["about"]: n for n in data.get("notes_of_the_book", [])},
        "count": len(data["phrases"]),
        "lessons": sorted(by_lesson),
    }


def lesson_context(conn: sqlite3.Connection, number: int) -> dict | None:
    """What one lesson page shows, for the local app and the published site alike; None if there is no such lesson.

    The word lists are rows of blue_book_attestations with the dictionary entry they are tied to. A row tied to an
    entry as a form of its stem (match_type "stem": ti•'at, a form of the verb at) gets the link but not the
    entry's pronunciation: "uht" is how the dictionary writes the stem, not how the word is said."""
    cur = conn.cursor()
    cur.row_factory = sqlite3.Row
    row = cur.execute("SELECT * FROM lessons WHERE lesson_number = ?", (number,)).fetchone()
    if row is None:
        return None
    vocab = [dict(v) for v in cur.execute("""
        SELECT a.id, a.bb_skiri_form, a.bb_english, a.context_type, a.entry_id, a.match_type, a.dialect_note,
               le.headword, le.normalized_form, le.simplified_pronunciation, le.phonetic_form, le.grammatical_class
        FROM blue_book_attestations a
        LEFT JOIN lexical_entries le ON le.entry_id = a.entry_id
        WHERE a.lesson_number = ? AND a.context_type IN ('BASIC_WORDS', 'ADDITIONAL_WORDS')
        ORDER BY a.context_type, a.id""", (number,))]
    labels = dialect_labels(conn)
    blue_book_only = {r[0] for r in cur.execute("SELECT entry_id FROM lexical_entries WHERE source = 'blue_book'")}
    for v in vocab:
        v["form_of_stem"] = bool(v["entry_id"]) and v["match_type"] == "stem"
        v["entry_sound"] = bool(v["entry_id"]) and not v["form_of_stem"]
        # the dialect the book's own marks or spelling show for the word (scripts/label_bluebook_dialect.py)
        v["dialect"] = labels.get(v["id"])
        # a Skiri dictionary entry can be heard at Indiana University; an entry made from the textbook's word cannot
        v["hear"] = bool(v["entry_id"]) and v["entry_id"] not in blue_book_only and not v["form_of_stem"]
    phrases = phrases_data(conn)
    rows = phrases["by_lesson"].get(number, [])
    dialogues = json.loads(row["dialogues"] or "[]")
    notes = json.loads(row["grammar_notes"] or "[]")
    for d in dialogues:
        for ln in d.get("lines", []):
            ln["sb_spelling"] = _sb_spelling_mark(ln.get("skiri"))
    text = " ".join([ln.get("skiri") or "" for d in dialogues for ln in d.get("lines", [])] + [n.get("text") or "" for n in notes])
    lesson = {
        "number": row["lesson_number"],
        "skiri_title": row["skiri_title"],
        "english_title": row["english_title"],
        "page_start": row["page_start"],
        "page_end": row["page_end"],
        "book_page_start": row["page_start"] - BLUE_BOOK_PAGE_OFFSET,
        "book_page_end": row["page_end"] - BLUE_BOOK_PAGE_OFFSET,
        "dialogues": dialogues,
        "grammar_notes": notes,
        "templates": json.loads(row["template_ids"] or "[]"),
        "has_gap": "[" in text,          # letters under a flaw in the scan stand in square brackets
        "title_sb_spelling": _sb_spelling_mark(row["skiri_title"]),
    }
    return {
        "lesson": lesson,
        "vocab": vocab,
        "basic": [v for v in vocab if v["context_type"] == "BASIC_WORDS"],
        "additional": [v for v in vocab if v["context_type"] == "ADDITIONAL_WORDS"],
        "phrases": rows,
        # the same lines as pairs, for the exercises (one form, its English)
        "phrase_pairs": [{"bb_skiri_form": r["forms"][0]["skiri"], "bb_english": r["printings"][0]["english"]}
                         for r in rows if len(r["forms"]) == 1 and r["printings"][0]["english"]],
        "conversations": [c for c in phrases["conversations"] if c["lesson"] == number],
        "conversation_note": (phrases["notes"].get("the two conversations") or {}).get("text", "") if number == 20 else "",
        # what the book says of its two dialects, for the line every lesson page carries
        "dialect_statements": dialect_statements()["statements"],
    }


def data_files(db_path: str) -> dict:
    """name -> data for the three files the learning pages read (docs/data/<name>.json)."""
    conn = sqlite3.connect("file:%s?mode=ro" % Path(db_path).resolve().as_posix(), uri=True)
    try:
        return {
            "wordbuilding": wordbuilding_data(conn),
            "verbs": verbs_data(conn),
            "practice": practice_data(db_path),
        }
    finally:
        conn.close()
