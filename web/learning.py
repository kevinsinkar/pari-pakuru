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
