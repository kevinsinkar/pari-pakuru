#!/usr/bin/env python3
"""Sentences from printed words: what stands behind the sentence builder of the local app.

Rebuilt on 2026-11-14 (engines review, decision 8: "repair by copying").
The earlier engine joined words that were typed into the code from the OCR
text of the Blue Book. Three of them do not exist, none had its printed
accent, and so the engine recognised none of the sentences the book prints
with an accent. It wrote a bare dictionary stem after a particle for "the
stick is red", and put a dictionary verb, in Parks's spelling, into a
sentence in the Blue Book's spelling.

What this file does instead, and the four rules it keeps:

1. EVERY BLUE BOOK FORM COMES FROM A ROW. A pattern starts from a sentence
   the Blue Book prints (a "frame": a row of blue_book_attestations, named in
   template_slot_fillers.py by its number and its text). A word of the frame
   may be swapped only for another printed word: a row, given by its number.
   No Pawnee word is typed in this file.
2. A SENTENCE SAYS WHAT IT IS. It is "printed in the Blue Book, lesson N"
   only when it is, accents included, a sentence the book prints. Anything
   else is "put together here; not printed". A swapped word keeps the accent
   it has where it was copied from, which may not be the accent it would
   carry in the new sentence: one more reason the label matters.
3. "THE STICK IS RED" USES A PRINTED FORM. In the Blue Book's spelling the
   quality is a phrase the book lists; in the dictionary's spelling it is the
   entry's printed form 2, and the sentence is offered only where one is
   printed. No form is made from a stem.
4. ONE SPELLING PER SENTENCE, AND THE ENTRY FOR A VERB. A sentence is either
   all Blue Book rows or all dictionary forms (dictionary_sentence). A
   dictionary verb is given by its entry id, never by its spelling: 211 verbs
   share a spelling with another. A form made by person_forms.py carries that
   file's label, "derived; not checked against a printed form".

Nothing here is shown on the public site.

    python scripts/sentence_templates.py --check     # every form named in the two files is what its row holds
    python scripts/sentence_templates.py --test      # the builder's own tests
    python scripts/sentence_templates.py --list      # the frames

Library (the web app):
    list_templates(), slot_options(...), assemble(template_id, frame=0, noun=ROW, ...),
    verb_forms(entry_id), dictionary_sentence(pattern, verb_entry_id, form_key, noun_entry_id=None)
"""
import argparse
import ast
import io
import os
import re
import sqlite3
import sys
import tokenize
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import person_forms
    from template_slot_fillers import FRAMES, PARKS_QUESTION_WORDS, SLOT_KINDS
except ImportError:  # imported as a package (the web app): scripts.sentence_templates
    from scripts import person_forms
    from scripts.template_slot_fillers import FRAMES, PARKS_QUESTION_WORDS, SLOT_KINDS

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("SKIRI_DB_PATH", str(ROOT / "skiri_pawnee.db"))

PRINTED = "printed in the Blue Book"
NOT_PRINTED = "put together here; not printed"
# Blue Book rows tied to a dictionary entry by the exact form (not by a shared beginning)
SOUND_LINKS = ("exact_normalized", "orthographic", "bb_only_form_and_english")
LISTS = ("BASIC_WORDS", "ADDITIONAL_WORDS", "GRAMMAR_EXAMPLE")
BLUE_BOOK_PAGE_OFFSET = 28          # the table counts pages of the scan; the book's own page is 28 less

# the forms of a dictionary verb the builder may show: (key of person_forms.derive_forms, what it is)
FORM_LABELS = [
    ("1sg_ind", "I: perfective"),
    ("2sg_ind", "you: perfective"),
    ("3sg_ind", "he or she: perfective"),
    ("3sg_ind_impf", "he or she: imperfective"),
    ("3sg_ind_int", "he or she: intentive"),
    ("1sg_abs", "I: question form"),
    ("2sg_abs", "you: question form"),
    ("3sg_abs", "he or she: question form"),
]


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def connect(db_path=None):
    """A read-only connection. Nothing in this file writes to the database."""
    conn = sqlite3.connect("file:%s?mode=ro" % Path(db_path or DB_PATH).resolve().as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Words and sentences as printed
# ---------------------------------------------------------------------------

def fold(text):
    """Without accents and capitals. Used to compare places in a sentence, never to make a form."""
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch)).lower()


def split_token(token):
    """(what stands before the word, the word, the punctuation after it). The apostrophe is a letter."""
    lead = ""
    while token and token[0] in "(\"“":
        lead, token = lead + token[0], token[1:]
    trail = ""
    while token and token[-1] in ".,?!;:)\"”":
        trail, token = token[-1] + trail, token[:-1]
    return lead, token, trail


def tokens(text):
    return [split_token(t) for t in unicodedata.normalize("NFC", text or "").split()]


def words(text):
    return [core for _, core, _ in tokens(text) if core]


def same_sentence_key(text):
    """Two sentences are the same sentence if they agree in every letter, accent and bullet; the capital at
    the start and the full stop, question or exclamation mark at the end are not counted."""
    t = " ".join(unicodedata.normalize("NFC", text or "").split()).rstrip(".?!").strip()
    return t[:1].lower() + t[1:]


def book_page(page_number):
    return page_number - BLUE_BOOK_PAGE_OFFSET if page_number else None


def bb_row(conn, row):
    try:
        row = int(row)
    except (TypeError, ValueError):
        return None
    return conn.execute(
        "select a.id, a.bb_skiri_form, a.bb_english, a.context_type, a.lesson_number, a.page_number, "
        "       a.entry_id, a.match_type "
        "from blue_book_attestations a where a.id = ? and a.bb_skiri_form is not null", (row,)).fetchone()


# ---------------------------------------------------------------------------
# Frames
# ---------------------------------------------------------------------------

def load_frame(conn, template_id, number=0):
    """A frame with its printed text, or a ValueError if the row no longer holds that text."""
    if template_id not in FRAMES:
        raise ValueError("Unknown template: %s. Use T1 to T10." % template_id)
    specs = FRAMES[template_id]["frames"]
    try:
        spec = specs[int(number)]
    except (IndexError, TypeError, ValueError):
        raise ValueError("%s has %d frames; there is no frame %r." % (template_id, len(specs), number))
    row = bb_row(conn, spec["frame"]["row"])
    if row is None or row["bb_skiri_form"] != spec["frame"]["text"]:
        raise ValueError("%s, frame %s: row %s of the Blue Book table does not hold the text the frame names. "
                         "Run sentence_templates.py --check." % (template_id, number, spec["frame"]["row"]))
    return {"template_id": template_id, "number": int(number), "row": row["id"], "text": row["bb_skiri_form"],
            "english": row["bb_english"], "lesson": row["lesson_number"], "book_page": book_page(row["page_number"]),
            "tokens": tokens(row["bb_skiri_form"]), "slots": spec["slots"]}


def list_templates(conn=None):
    """The templates with their frames, for the page."""
    own = conn is None
    conn = conn or connect()
    try:
        result = []
        for template_id, spec in FRAMES.items():
            frames = []
            for number in range(len(spec["frames"])):
                f = load_frame(conn, template_id, number)
                slot_at = {p: name for name, places in f["slots"].items() for p in places}
                frames.append({
                    "number": number, "row": f["row"], "text": f["text"], "english": f["english"],
                    "lesson": f["lesson"], "book_page": f["book_page"],
                    "slots": {name: {"places": places, "kind": SLOT_KINDS[name]} for name, places in f["slots"].items()},
                    "words": [{"text": lead + core + trail, "slot": slot_at.get(i)}
                              for i, (lead, core, trail) in enumerate(f["tokens"])]})
            result.append({"template_id": template_id, "name": spec["name"],
                           "english_pattern": spec["english_pattern"], "frames": frames,
                           # the first frame, for pages that show one example per template
                           "skiri_example": frames[0]["text"], "english_example": frames[0]["english"],
                           "example_lesson": frames[0]["lesson"]})
        return result
    finally:
        if own:
            conn.close()


def printed_sentences(conn):
    """Every form of the Blue Book table, by its sentence key."""
    index = {}
    for r in conn.execute("select id, bb_skiri_form, bb_english, lesson_number, page_number from blue_book_attestations "
                          "where bb_skiri_form is not null order by id"):
        index.setdefault(same_sentence_key(r["bb_skiri_form"]), []).append(r)
    return index


# ---------------------------------------------------------------------------
# What may stand in a slot
# ---------------------------------------------------------------------------

def _option(row, here):
    return {"row": row["id"], "form": " ".join(words(row["bb_skiri_form"])), "english": row["bb_english"] or "",
            "lesson": row["lesson_number"], "here": here}


def _same_place(conn, frame, places):
    """Rows of the book that are the frame with other words in these places: what the book itself puts there."""
    n = len(frame["tokens"])
    fixed = {i: fold(core) for i, (_, core, _) in enumerate(frame["tokens"]) if i not in places}
    if not fixed:
        return []                      # a frame of one word has no pattern to share
    found = []
    for r in conn.execute("select id, bb_skiri_form, bb_english, lesson_number from blue_book_attestations "
                          "where bb_skiri_form is not null order by id"):
        toks = tokens(r["bb_skiri_form"])
        if len(toks) != n or any(fold(toks[i][1]) != f for i, f in fixed.items()):
            continue
        if r["bb_skiri_form"] == r["bb_skiri_form"].upper():
            continue                   # a title line in capitals: the same words stand below it in ordinary letters
        found.append({"row": r["id"], "form": " ".join(toks[i][1] for i in places), "english": r["bb_english"] or "",
                      "lesson": r["lesson_number"], "here": True, "whole_sentence": True, "places": list(places)})
    return found


def slot_options(template_id, frame=0, slot="", q="", limit=60, conn=None):
    """Printed words that may stand in a slot of a frame, the ones the book itself puts there first.

    An option names a row. For an option marked "whole_sentence" the row is a sentence of the same shape and
    the word is taken from the same place in it.
    """
    own = conn is None
    conn = conn or connect()
    try:
        f = load_frame(conn, template_id, frame)
        if slot not in f["slots"]:
            return []
        places = f["slots"][slot]
        kind = SLOT_KINDS[slot]
        options = _same_place(conn, f, places)
        needle = fold(q.strip())
        if kind == "noun":
            sql = ("select a.id, a.bb_skiri_form, a.bb_english, a.lesson_number from blue_book_attestations a "
                   "join lexical_entries le on le.entry_id = a.entry_id "
                   "where a.bb_skiri_form is not null and a.match_type in (%s) "
                   "  and (le.grammatical_class = 'N' or le.grammatical_class like 'N,%%' or le.grammatical_class like 'N-%%') "
                   "order by a.lesson_number, a.id" % ",".join("?" * len(SOUND_LINKS)))
            rows = conn.execute(sql, SOUND_LINKS).fetchall()
            options += [_option(r, False) for r in rows if len(words(r["bb_skiri_form"])) == len(places)]
            if needle:
                # Asked for by its English, any word of the book's word lists may be taken. Many common nouns
                # (dog, man, woman, horse) are not tied to their dictionary entry in the table, so the tie
                # cannot be the test of what is a noun; the English beside each word says what it is.
                rows = conn.execute(
                    "select id, bb_skiri_form, bb_english, lesson_number from blue_book_attestations "
                    "where bb_skiri_form is not null and context_type in ('BASIC_WORDS', 'ADDITIONAL_WORDS') "
                    "order by lesson_number, id").fetchall()
                options += [_option(r, False) for r in rows if len(words(r["bb_skiri_form"])) == len(places)]
        else:
            rows = conn.execute(
                "select id, bb_skiri_form, bb_english, lesson_number, context_type from blue_book_attestations "
                "where bb_skiri_form is not null and context_type in (%s) order by lesson_number, id"
                % ",".join("?" * len(LISTS)), LISTS).fetchall()
            first = fold(f["tokens"][places[0]][1])
            for r in rows:
                ws = words(r["bb_skiri_form"])
                if len(ws) != len(places):
                    continue
                if kind == "phrase" and (fold(ws[0]) != first or r["context_type"] == "GRAMMAR_EXAMPLE"):
                    continue               # a phrase from the word lists, not a whole example sentence
                if kind == "start" and not fold(ws[0]).startswith(first.split("•")[0] + "•"):
                    continue
                if kind == "word" and not needle:
                    continue               # too many to list: these are found by their English
                options.append(_option(r, False))
        seen, result = set(), []
        asked = re.compile(chr(92) + "b" + re.escape(needle)) if needle else None   # at the start of a word
        for o in options:
            key = o["form"][:1].lower() + o["form"][1:]          # the same word with and without a capital is one
            if key in seen:
                continue
            if asked and not asked.search(fold(o["english"])) and needle not in fold(o["form"]):
                continue
            seen.add(key)
            result.append(o)
        return result[:limit]
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------------------
# Putting a sentence together
# ---------------------------------------------------------------------------

@dataclass
class TemplateResult:
    """A sentence and what it is."""
    skiri_sentence: str = ""
    spelling: str = "Blue Book"                 # or "Parks"
    status: str = NOT_PRINTED                   # PRINTED or NOT_PRINTED
    printed_in: List[Dict[str, Any]] = field(default_factory=list)   # the rows that print it
    english: Optional[str] = None               # the book's own translation, when the sentence is printed
    frame: Optional[Dict[str, Any]] = None      # the printed sentence it started from
    template_id: str = ""
    template_name: str = ""
    words: List[Dict[str, Any]] = field(default_factory=list)
    derived: bool = False                       # True if a word was made by person_forms.py
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self):
        return {"skiri_sentence": self.skiri_sentence, "spelling": self.spelling, "status": self.status,
                "printed": self.status == PRINTED, "printed_in": self.printed_in, "english": self.english,
                "frame": self.frame, "template_id": self.template_id, "template_name": self.template_name,
                "words": self.words, "derived": self.derived, "notes": self.notes, "error": self.error}


def _failed(template_id, message):
    name = FRAMES.get(template_id, {}).get("name", "")
    return TemplateResult(template_id=template_id, template_name=name, error=message)


def assemble(template_id, frame=0, conn=None, **slots):
    """A frame with some of its words swapped for other printed words.

    Each slot is given as the number of a row of the Blue Book table. Given as {"row": N, "places": [..]} the
    words are taken from those places of row N (a sentence of the same shape); otherwise row N must be the
    word or phrase itself.
    """
    own = conn is None
    conn = conn or connect()
    try:
        try:
            f = load_frame(conn, template_id, frame)
        except ValueError as exc:
            return _failed(template_id, str(exc))
        toks = [list(t) for t in f["tokens"]]
        source = [{"from": "the frame", "row": f["row"], "english": None, "lesson": f["lesson"], "slot": None,
                   "entry_id": None} for _ in toks]
        for name, value in slots.items():
            if value in (None, "", []):
                continue
            if name not in f["slots"]:
                return _failed(template_id, "This frame has no place called %r. It has: %s." % (
                    name, ", ".join(sorted(f["slots"]))))
            places = f["slots"][name]
            take = None
            if isinstance(value, dict):
                take, value = value.get("places"), value.get("row")
            row = bb_row(conn, value)
            if row is None:
                return _failed(template_id, "%s: there is no row %r in the Blue Book table. A word can only be "
                                            "taken from a row." % (name, value))
            ws = words(row["bb_skiri_form"])
            if take:
                if max(take) >= len(ws):
                    return _failed(template_id, "%s: row %s has no word at place %s." % (name, row["id"], max(take)))
                ws = [ws[i] for i in take]
            if len(ws) != len(places):
                return _failed(template_id, "%s: %d word(s) are needed here and row %s has %d." % (
                    name, len(places), row["id"], len(ws)))
            tied = row["entry_id"] if row["match_type"] in SOUND_LINKS and not take else None
            for place, word in zip(places, ws):
                toks[place][1] = word
                source[place] = {"from": "row %d" % row["id"], "row": row["id"],
                                 "english": ("in the sentence: %s" % row["bb_english"]) if take else row["bb_english"],
                                 "lesson": row["lesson_number"],
                                 "slot": name, "entry_id": tied}
        if f["tokens"][0][1][:1].isupper():          # the sentence begins with a capital, as the frame does
            toks[0][1] = toks[0][1][:1].upper() + toks[0][1][1:]
        sentence = " ".join(lead + core + trail for lead, core, trail in toks)
        result = TemplateResult(
            skiri_sentence=sentence, template_id=template_id, template_name=FRAMES[template_id]["name"],
            frame={"row": f["row"], "text": f["text"], "english": f["english"], "lesson": f["lesson"],
                   "book_page": f["book_page"]},
            words=[dict(s, form=t[1]) for t, s in zip(toks, source)])
        rows = printed_sentences(conn).get(same_sentence_key(sentence), [])
        if rows:
            result.status = PRINTED
            result.english = rows[0]["bb_english"]
            result.printed_in = [{"row": r["id"], "lesson": r["lesson_number"], "book_page": book_page(r["page_number"]),
                                  "text": r["bb_skiri_form"], "english": r["bb_english"]} for r in rows]
        else:
            result.notes.append("The Blue Book does not print this sentence. Each word is copied from the book, "
                                "and a swapped word keeps the accent it has where it was copied from.")
        return result
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------------------
# A dictionary verb: its printed forms, and the forms derived from them
# ---------------------------------------------------------------------------

def _entry(conn, entry_id):
    return conn.execute(
        "select le.entry_id, le.headword, le.grammatical_class, le.stem_preverb, "
        "  (select definition from glosses g where g.entry_id = le.entry_id order by sense_number limit 1) as gloss "
        "from lexical_entries le where le.entry_id = ?", (entry_id,)).fetchone()


def verb_forms(entry_id, conn=None):
    """The forms of one dictionary verb the builder may show, each marked "printed" or "derived"."""
    own = conn is None
    conn = conn or connect()
    try:
        e = _entry(conn, entry_id)
        if e is None or not (e["grammatical_class"] or "").startswith("V"):
            return {"error": "There is no verb entry %r. A verb is chosen by its entry, not by its spelling." % (entry_id,)}
        printed = {r["form_number"]: r["skiri_form"] for r in conn.execute(
            "select form_number, skiri_form from paradigmatic_forms where entry_id = ? and skiri_form is not null "
            "and skiri_form != ''", (entry_id,))}
        derived = person_forms.derive_forms(form_1=printed.get(1), form_2=printed.get(2), form_3=printed.get(3),
                                            form_5=printed.get(5), headword=e["headword"],
                                            stem_preverb=e["stem_preverb"], gram_class=e["grammatical_class"])
        forms = []
        for key, label in FORM_LABELS:
            number = person_forms.PRINTED.get(key)
            if number:
                if printed.get(number):
                    forms.append({"key": key, "label": label, "form": printed[number], "status": "printed",
                                  "source": "Parks, form %d of the entry" % number})
            elif derived.get(key):
                forms.append({"key": key, "label": label, "form": derived[key], "status": "derived",
                              "source": person_forms.DERIVED_LABEL})
        return {"entry_id": e["entry_id"], "headword": e["headword"], "grammatical_class": e["grammatical_class"],
                "gloss": e["gloss"], "forms": forms,
                "note": "A derived form has no accent mark: the rules work on forms without their accents. "
                        "Where no form is listed, none is printed and none can be derived."}
    finally:
        if own:
            conn.close()


def dictionary_sentence(pattern, verb_entry_id, form_key, noun_entry_id=None, conn=None):
    """A sentence in the dictionary's spelling: a noun, a verb form, and for a question Parks's question word.

    pattern: "statement" (noun, then verb), or "where", "who", "what" (question word, verb, then noun).
    The words are dictionary forms; the order is the Blue Book's. Never printed anywhere.
    """
    own = conn is None
    conn = conn or connect()
    try:
        failed = lambda message: TemplateResult(spelling="Parks", template_name="Dictionary spelling", error=message)
        info = verb_forms(verb_entry_id, conn)
        if "error" in info:
            return failed(info["error"])
        form = next((f for f in info["forms"] if f["key"] == form_key), None)
        if form is None:
            return failed("%s has no such form: none is printed and none can be derived. It has: %s." % (
                info["headword"], ", ".join(f["label"] for f in info["forms"]) or "no form at all"))
        notes = []
        text = person_forms.primary_form(form["form"])
        if text != form["form"]:
            notes.append("Parks prints two forms here (%s); the first is used." % form["form"])
        parts = [{"form": text, "from": form["source"], "english": info["gloss"], "entry_id": info["entry_id"],
                  "slot": "verb", "derived": form["status"] == "derived", "label": form["label"]}]
        if pattern == "statement":
            if form_key.endswith("_abs"):
                return failed("A question form does not stand in a statement.")
        elif pattern in PARKS_QUESTION_WORDS:
            if not form_key.endswith("_abs"):
                return failed("After a question word the verb stands in its question form (Parks, Table 14).")
            q = PARKS_QUESTION_WORDS[pattern]
            qe = _entry(conn, q["entry_id"])
            if qe is None or qe["headword"] != q["headword"]:
                return failed("The entry of the question word is not what template_slot_fillers.py names.")
            qword = person_forms.primary_form(qe["headword"])
            if qword != qe["headword"]:
                notes.append("Parks prints the question word in two forms (%s); the first is used." % qe["headword"])
            parts.insert(0, {"form": qword, "from": "Parks, headword", "english": qe["gloss"],
                             "entry_id": qe["entry_id"], "slot": "question word", "derived": False, "label": None})
            notes.append("Parks says that the question words take this mode (Grammatical Overview, Table 14).")
        else:
            return failed("Unknown pattern %r. Use statement, %s." % (pattern, ", ".join(PARKS_QUESTION_WORDS)))
        if noun_entry_id:
            n = _entry(conn, noun_entry_id)
            if n is None or not (n["grammatical_class"] or "").startswith("N"):
                return failed("There is no noun entry %r." % (noun_entry_id,))
            if re.search(r"[\s,/()\[\]]|^-|-$", n["headword"]):
                return failed("The headword %s is not one free word, so it cannot stand in a sentence as it is." % n["headword"])
            noun = {"form": n["headword"], "from": "Parks, headword", "english": n["gloss"], "entry_id": n["entry_id"],
                    "slot": "noun", "derived": False, "label": None}
            if pattern == "statement":
                parts.insert(0, noun)
            else:
                parts.append(noun)
        sentence = " ".join(p["form"] for p in parts) + ("?" if pattern != "statement" else ".")
        derived = any(p["derived"] for p in parts)
        if derived:
            notes.insert(0, "The verb form is %s." % person_forms.DERIVED_LABEL)
        notes.append("The words are dictionary forms in Parks's spelling. Their order follows the Blue Book's "
                     "sentences; no source prints this sentence.")
        return TemplateResult(skiri_sentence=sentence, spelling="Parks", status=NOT_PRINTED,
                              template_name="Dictionary spelling: %s" % pattern, words=parts, derived=derived,
                              notes=notes)
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------------------
# The check: every form named in the two files is what its row or entry holds
# ---------------------------------------------------------------------------

def _stray_pawnee(path, known):
    """Words of a source file, outside bb(...) and entry(...), that are Pawnee forms. There must be none."""
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    declared = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("bb", "entry"):
            declared.update(id(a) for a in node.args)
    text = [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in declared]
    text += [t.string for t in tokenize.generate_tokens(io.StringIO(source).readline) if t.type == tokenize.COMMENT]
    found = set()
    # the bullet and the glottal stop belong to a word; they are named by number so that this line is not itself a find
    inside_a_word = re.compile("[^\\w'-" + chr(0x2022) + chr(0x0294) + "]+")
    for chunk in text:
        for word in inside_a_word.split(chunk):
            w = word.strip("'-_")
            if len(w) < 3 or not any(ch.isalpha() for ch in w):
                continue
            marked = "•" in w or "ʔ" in w or fold(w) != w.lower()
            if marked or (len(w) >= 5 and w.lower() in known and w.lower() not in ENGLISH_ALSO):
                found.add(w)
    return sorted(found)


# English words of these two files that are also the spelling of a Pawnee form. None is meant as Pawnee here.
ENGLISH_ALSO = set()


def check(conn=None):
    """Returns the list of problems (empty when all is well) and prints a summary."""
    own = conn is None
    conn = conn or connect()
    try:
        problems, frames, slots = [], 0, 0
        for template_id, spec in FRAMES.items():
            for number, fs in enumerate(spec["frames"]):
                frames += 1
                row = bb_row(conn, fs["frame"]["row"])
                if row is None:
                    problems.append("%s frame %d: no row %s" % (template_id, number, fs["frame"]["row"]))
                    continue
                if row["bb_skiri_form"] != fs["frame"]["text"]:
                    problems.append("%s frame %d: row %s holds %r, the file says %r" % (
                        template_id, number, row["id"], row["bb_skiri_form"], fs["frame"]["text"]))
                n = len(tokens(row["bb_skiri_form"]))
                for name, places in fs["slots"].items():
                    slots += 1
                    if name not in SLOT_KINDS:
                        problems.append("%s frame %d: slot %s has no kind" % (template_id, number, name))
                    if not places or max(places) >= n:
                        problems.append("%s frame %d: slot %s names a place the sentence does not have" % (
                            template_id, number, name))
        for name, q in PARKS_QUESTION_WORDS.items():
            e = _entry(conn, q["entry_id"])
            if e is None or e["headword"] != q["headword"]:
                problems.append("question word %s: entry %s does not hold the headword %r" % (name, q["entry_id"], q["headword"]))
        known = {fold(w) for (f,) in conn.execute("select bb_skiri_form from blue_book_attestations where bb_skiri_form is not null")
                 for w in words(f)}
        known |= {fold(h) for (hw,) in conn.execute("select headword from lexical_entries where headword is not null")
                  for h in re.split(r"[,\s]+", hw) if h}
        here = Path(__file__).resolve().parent
        for name in ("sentence_templates.py", "template_slot_fillers.py"):
            for word in _stray_pawnee(here / name, known):
                problems.append("%s: the Pawnee form %r stands outside bb() and entry()" % (name, word))
        out("frames: %d, each the text of its row; places that can be swapped: %d; question words of the dictionary: %d"
            % (frames, slots, len(PARKS_QUESTION_WORDS)))
        for line in problems:
            out("PROBLEM: " + line)
        if not problems:
            out("every Pawnee form in the two files is named by its row or entry and is what that row or entry "
                "holds: zero exceptions")
        return problems
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------------------
# Tests. Every expected form is read from a row; none is typed.
# ---------------------------------------------------------------------------

def run_tests(conn=None, verbose=True):
    own = conn is None
    conn = conn or connect()
    passed, failures = 0, []

    def ok(condition, what):
        nonlocal passed
        if condition:
            passed += 1
            if verbose:
                out("  ok    " + what)
        else:
            failures.append(what)
            out("  FAIL  " + what)

    def text_of(row):
        return bb_row(conn, row)["bb_skiri_form"]

    def is_printed(sentence):       # an independent look: is this, letter for letter, a form of the table?
        key = same_sentence_key(sentence)
        return any(same_sentence_key(f) == key for (f,) in conn.execute(
            "select bb_skiri_form from blue_book_attestations where bb_skiri_form is not null"))

    def option(template_id, frame, slot, like_row, place, q=""):
        want = words(text_of(like_row))[place]
        return next((o for o in slot_options(template_id, frame, slot, q=q, limit=500, conn=conn) if o["form"] == want), None)

    def pick(o):
        return {"row": o["row"], "places": o["places"]} if o.get("whole_sentence") else o["row"]

    try:
        # 1. every frame, untouched, is the printed sentence and says so
        for template_id, spec in FRAMES.items():
            for number, fs in enumerate(spec["frames"]):
                r = assemble(template_id, number, conn=conn)
                row = bb_row(conn, fs["frame"]["row"])
                ok(r.error is None and r.skiri_sentence == row["bb_skiri_form"] and r.status == PRINTED
                   and any(p["row"] == row["id"] for p in r.printed_in) and r.english is not None,
                   "%s frame %d untouched is row %d, printed in lesson %s" % (template_id, number, row["id"], row["lesson_number"]))
        # 2. a swap that gives another printed sentence is recognised as printed, accents included
        for like in (1956, 2282, 2283):          # three sentences the book prints on the pattern of T2
            o = option("T2", 0, "noun", like, 0)
            r = assemble("T2", 0, conn=conn, noun=pick(o)) if o else None
            ok(bool(r) and r.error is None and same_sentence_key(r.skiri_sentence) == same_sentence_key(text_of(like))
               and r.status == PRINTED and any(p["row"] == like for p in r.printed_in),
               "T2 with the noun of row %d gives the sentence of row %d, marked printed" % (like, like))
            ok(bool(o) and o["here"], "T2: the noun of row %d is offered as a word the book itself puts there" % like)
        # 3. a swap the book does not print is marked as put together here
        o = option("T1", 0, "noun", 1908, 2)
        r = assemble("T1", 0, conn=conn, noun=pick(o)) if o else None
        ok(bool(r) and r.error is None and (r.status == PRINTED) == is_printed(r.skiri_sentence),
           "T1 with the noun of row 1908: its status is what an independent look at the table says")
        r = None
        for o in slot_options("T9", 0, "subject", limit=500, conn=conn):     # the first noun that makes a new sentence
            candidate = assemble("T9", 0, conn=conn, subject=pick(o))
            if candidate.error is None and not is_printed(candidate.skiri_sentence):
                r = candidate
                break
        ok(r is not None and r.status == NOT_PRINTED and r.english is None and bool(r.notes)
           and any(w["slot"] == "subject" and w["from"] != "the frame" for w in r.words),
           "T9 with a listed noun as subject is not a sentence of the book and says so")
        # 4. the accent decides: without its accents a printed sentence is no longer recognised as printed
        plain = fold(text_of(1947))
        ok(same_sentence_key(plain) not in printed_sentences(conn) or plain == text_of(1947).lower(),
           "the sentence of row 1947 without its accent is not counted as printed")
        # 5. a word can only come from a row, and must fit the place
        ok(assemble("T1", 0, conn=conn, noun=99999999).error is not None, "a row that does not exist is refused")
        ok(assemble("T1", 0, conn=conn, noun=1947).error is not None, "a row of three words is refused where one is needed")
        ok(assemble("T1", 0, conn=conn, verb=1903).error is not None, "a place the frame does not have is refused")
        ok(assemble("T99", 0, conn=conn).error is not None, "an unknown template is refused")
        # 6. "the stick is red": the quality is a phrase the book lists
        o = next((x for x in slot_options("T2", 0, "quality", limit=500, conn=conn) if not x.get("whole_sentence")), None)
        r = assemble("T2", 0, conn=conn, quality=pick(o)) if o else None
        ok(bool(r) and r.error is None and len(words(o["form"])) == 2 and o["form"] in r.skiri_sentence,
           "T2: the quality is taken whole from a listed row (%s)" % (o["row"] if o else "none found"))
        # 7. nothing is offered that is not a row
        every = [x for t, spec in FRAMES.items() for n, fs in enumerate(spec["frames"]) for s in fs["slots"]
                 for x in slot_options(t, n, s, q="a" if SLOT_KINDS[s] == "word" else "", limit=500, conn=conn)]
        ok(every and all(bb_row(conn, x["row"]) is not None for x in every),
           "all %d words offered across the frames are rows of the Blue Book table" % len(every))
        # 8. a dictionary verb: printed forms are the entry's own, derived ones carry the label
        verb = conn.execute(
            "select p1.entry_id from paradigmatic_forms p1 join paradigmatic_forms p2 on p2.entry_id = p1.entry_id "
            "join lexical_entries le on le.entry_id = p1.entry_id "
            "where p1.form_number = 1 and p2.form_number = 2 and p2.skiri_form like 'tik%' and le.grammatical_class = 'VT' "
            "order by p1.entry_id limit 1").fetchone()[0]
        info = verb_forms(verb, conn)
        stored = {r["form_number"]: r["skiri_form"] for r in conn.execute(
            "select form_number, skiri_form from paradigmatic_forms where entry_id = ?", (verb,))}
        ok(all(f["form"] == stored[person_forms.PRINTED[f["key"]]] for f in info["forms"] if f["status"] == "printed"),
           "a verb's printed forms are shown as the entry prints them, accents included")
        ok(any(f["status"] == "derived" for f in info["forms"])
           and all(f["source"] == person_forms.DERIVED_LABEL for f in info["forms"] if f["status"] == "derived"),
           "every derived form carries the label: %s" % person_forms.DERIVED_LABEL)
        no_first = conn.execute(
            "select le.entry_id from lexical_entries le where le.grammatical_class = 'VD' "
            "and exists (select 1 from paradigmatic_forms p where p.entry_id = le.entry_id and p.form_number = 2) "
            "and not exists (select 1 from paradigmatic_forms p where p.entry_id = le.entry_id and p.form_number = 1) "
            "order by le.entry_id limit 1").fetchone()[0]
        keys = {f["key"] for f in verb_forms(no_first, conn)["forms"]}
        ok(not keys & {"1sg_ind", "2sg_ind", "1sg_abs", "2sg_abs"},
           "a verb that prints no form 1 is given no \"I\" and no \"you\" form")
        ok("error" in verb_forms("no such entry", conn), "a verb is found by its entry id only")
        # 9. sentences in the dictionary's spelling
        noun = conn.execute("select entry_id, headword from lexical_entries where entry_id = 'SK-rakis-p135-2644'").fetchone()
        r = dictionary_sentence("statement", no_first, "3sg_ind", noun["entry_id"], conn=conn)
        form2 = conn.execute("select skiri_form from paradigmatic_forms where entry_id = ? and form_number = 2", (no_first,)).fetchone()[0]
        ok(r.error is None and r.spelling == "Parks" and r.status == NOT_PRINTED and not r.derived
           and r.skiri_sentence == "%s %s." % (noun["headword"], person_forms.primary_form(form2)),
           "\"the stick is ...\" in the dictionary's spelling: the noun's headword and the verb's printed form 2")
        r = dictionary_sentence("where", verb, "3sg_abs", conn=conn)
        ok(r.error is None and r.derived and r.status == NOT_PRINTED and len(r.words) == 2
           and any(person_forms.DERIVED_LABEL in n for n in r.notes),
           "a where-question with a dictionary verb is marked derived and not printed")
        ok(dictionary_sentence("where", verb, "3sg_ind", conn=conn).error is not None,
           "after a question word only a question form is accepted")
        ok(dictionary_sentence("statement", verb, "3sg_abs", conn=conn).error is not None,
           "a question form is refused in a statement")
        ok(dictionary_sentence("statement", no_first, "2sg_ind", conn=conn).error is not None,
           "a form that cannot be given is refused, not made up")
        # 10. the two files hold no form that is not named by its row
        ok(not check(conn), "the check of the two files finds nothing")
    finally:
        if own:
            conn.close()
    out("")
    out("sentence builder: %d passed, %d failed" % (passed, len(failures)))
    return passed, len(failures), failures


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", nargs="?", choices=["test", "check", "list"], help="the same as --test, --check, --list")
    ap.add_argument("--test", action="store_true", help="run the tests; exit 1 if one fails")
    ap.add_argument("--check", action="store_true", help="every form named in the two files against the tables; exit 1 on a problem")
    ap.add_argument("--list", action="store_true", help="the templates and their frames")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.check or args.command == "check":
        return 1 if check() else 0
    if args.test or args.command == "test":
        return 1 if run_tests(verbose=not args.quiet)[1] else 0
    if args.list or args.command == "list":
        for t in list_templates():
            out("%s  %s: %s" % (t["template_id"], t["name"], t["english_pattern"]))
            for f in t["frames"]:
                out("      row %d, lesson %s: %s  '%s'  swap: %s" % (
                    f["row"], f["lesson"], f["text"], f["english"], ", ".join(sorted(f["slots"]))))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
