#!/usr/bin/env python3
"""
The lessons' text against the scan, line by line (2026-11-14)
=============================================================

The `lessons` table holds a title, the dialogues and the grammar notes of each
of the twenty Blue Book lessons. All of it came from the OCR text of the scan.
The audit of 2026-11-13 read the Blue Book's *listed forms* from the scan (the
table blue_book_attestations); in the lessons it corrected a line only where
the whole line was one of those forms, and scripts/fix_lesson_text_ocr.py
later carried the same readings into running text where the old reading was
plain OCR damage. What no reading covered was left: accents inside running
text, the pieces of the breakdown lines (ti + ku + iks), seven titles.

This tool is for that rest. Every line of a lesson's stored text that is not
plain English is cut from the scan and read.

    python scripts/source_audit/lesson_text_reading.py --plan      # how many lines, by lesson; cuts nothing
    python scripts/source_audit/lesson_text_reading.py --sheets    # cut the lines: work/lesson_text/
    python scripts/source_audit/lesson_text_reading.py --grade     # compare the readings with the stored text
    python scripts/source_audit/lesson_text_reading.py --grade --show   # ... and list every difference
    python scripts/source_audit/lesson_text_reading.py --open      # what one reading does not settle, with the stored words
    python scripts/source_audit/lesson_text_reading.py --second    # cut again, wider and larger, what is open
    python scripts/source_audit/lesson_text_reading.py --second --only 75.8.5,89.1.0+   # chosen lines; + with the lines around
    python scripts/source_audit/lesson_text_reading.py --where ID  # what the stored text has at a strip

How a line is found
-------------------
The scan has a text layer: the OCR the stored text was made from, with the
place of every word on the page. The stored text of a lesson is lined up with
the words of the lesson's pages, word for word (accents, capitals and the
OCR's known confusions set aside); the dialogues by themselves and the notes
by themselves, because a sentence may be stored in both. A stored word that
the OCR split in two or ran together finds its line by its letters. A line of
the page that takes part in this and holds a '+' or '=' or a word that is not
English is cut out with its number, page.block.line. The vocabulary lists and
the glossary are not in the stored text and are not cut: they are the Blue
Book table, which the audit read. The titles are not lined up: the top of
each lesson's first page is cut for every lesson (T1 ... T20).

The text layer makes two "lines" of a form and the English beside it. A
second look is therefore cut from the left margin of the page.

How it is read
--------------
The reader sees the sheets only, and writes for each strip what it shows of
Pawnee: words, and breakdown lines piece by piece, with accents, raised dots
(written •) and apostrophes; English words are left out. The readings go to
reports/source_audit_2026-11/lesson_text_reading/part_NN.json as
{"read": {strip: text}}; "" means the strip shows no Pawnee; [?] marks what
the reader cannot make out. A second reading of a strip goes to
second_NN.json and is the one that counts.

The reading of 2026-11-14 was made in the main session, not by a separate
reader: the stored text was not beside the sheets, but the session had seen
parts of it earlier. It is one reading.

How it is graded
----------------
--grade names every difference by kind and says whether one reading is enough
to take it. It is enough, as it was for the audit's reading of the Blue Book
table, where the OCR is known to fail: an accent the page has and the stored
text lacks; a raised dot, an apostrophe or a space; d, f, j, ti, ii for an
accented vowel. It is never enough to take a mark away, to change a letter,
or to touch a word marked by hand with square brackets. The punctuation of
the sentence is not compared and never changed; plus signs and their spacing
are not differences.

For every difference it also says what the audit's readers read AT THE SAME
PLACE ON THE PAGE (the audit kept the box of every crop): the same, something
else, or nothing because no crop was cut there. That is how two crops of the
audit were found to have been cut at a line above the row they were meant
for (reports/source_audit_2026-11/bluebook_crops_at_another_line.json).

What one reading does not settle is decided by hand after a second look and
written down in lesson_text_reading/decisions.json: changes, a line placed
by hand, differences left as they are, each with its reason.

--grade writes reports/source_audit_2026-11/lesson_text_graded.json;
scripts/apply_lesson_page_reading.py makes the changes and checks them.
"""
import argparse
import collections
import difflib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state  # noqa: E402
from apply_bluebook_scan_fixes import clean, decide, ocr_fold, plain  # noqa: E402
from bluebook_check import PDF  # noqa: E402

FOLDER = state.WORK / "lesson_text"
READINGS = state.OUT / "lesson_text_reading"
GRADED = state.OUT / "lesson_text_graded.json"
DB = state.ROOT / "skiri_pawnee.db"

PAWNEE_LETTERS = set("aeiukptschwr")       # the Blue Book's alphabet
OCR_LETTERS = set("dfj")                   # what the OCR made of accented vowels
EDGE = ".,;:!?()\"“”"

# English words spelled with the Blue Book's letters only, which the glosses of the database do not happen to hold.
ENGLISH_EXTRA = """a i is it its as at the this these there their here where what which who with was were are has
he she we us use uses used sit sits see sees set sets put puts act acts part parts past phrase phrases that hat
three street eats eat ate heat state states speaker speakers speak speaks cases case pair pairs page pages write
writes wrote practice practices paper spear its's twice text texts test tests title titles appear appears
earth water white wheat street sister sisters parent parents repeat repeats separate hits hit pit kiss shape
shapes takes take taste easier easiest harder skip sure true rise rather per sheet sweet treat ask asks asked
either its repetitive repetitive utterance utterances active passive perfect respect characteristic article
articles tape tapes speech starts start stress stresses week weeks wake eat seat suit were chapter chapters
piece pieces replace replaces separate create creates increase ease erase search arise area areas require
requires express expresses receive receives attach attaches pause pauses script picture pictures purpose
success such etc pp ie eg cf vs succeeded attitude hearers precede succeed tepee ii refer refers aspect aspects hearer research strict carries cats whereas reduced
effect preferred added studied whether desk recited
re- pre pre- paw- adj adjec- dicate spect ited ad- repre- per- phr res ac- ap- pears fect""".split()
# The last line: halves of English words the page breaks at the end of a line.


# ---------------------------------------------------------------- words

def unaccent(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(ch))


def key_of(token):
    """What two spellings of one word on the page have in common: used only to line words up."""
    return ocr_fold(token) or token


def english_lexicon(conn):
    words = set(ENGLISH_EXTRA)
    for sql in ("select definition from glosses", "select bb_english from blue_book_attestations",
                "select english_word from english_index", "select english_translation from examples",
                "select english_title from lessons"):
        for (text,) in conn.execute(sql):
            words.update(w.lower() for w in re.findall(r"[A-Za-z]+", text or ""))
    return words


def is_english(token, lexicon):
    """True if the token cannot be, or need not be, a Pawnee word: a number, punctuation, a word with a letter the
    Blue Book's alphabet lacks, or an English word spelled with the Blue Book's letters."""
    core = token.strip(EDGE + "'")
    if "•" in token or unaccent(core) != core:
        return False
    letters = re.sub(r"[^a-z]", "", core.lower())
    if not letters:
        return True
    if set(letters) - PAWNEE_LETTERS - OCR_LETTERS:
        return True
    if token.rstrip(EDGE).endswith("'") and not token.rstrip(EDGE).lower().endswith("s'"):
        return False                               # a final glottal stop
    low = core.lower()
    return low.replace("'", "") in lexicon or all(part in lexicon for part in low.split("'") if part)


def needs_reading(tokens, lexicon):
    return any(t in ("+", "=") or "+" in t or "=" in t or not is_english(t, lexicon) for t in tokens)


# ---------------------------------------------------------------- the stored text

def strings(node, path=()):
    """Every string of a JSON value, with its path."""
    if isinstance(node, str):
        yield list(path), node
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from strings(item, path + (i,))
    elif isinstance(node, dict):
        for k, item in node.items():
            yield from strings(item, path + (k,))


def load_lessons(conn):
    """The lessons as the table holds them, the two JSON columns unpacked."""
    out = []
    for n, title, english, p0, p1, dialogues, notes in conn.execute(
            "select lesson_number, skiri_title, english_title, page_start, page_end, dialogues, grammar_notes "
            "from lessons order by 1"):
        out.append({"lesson_number": n, "skiri_title": title, "english_title": english, "page_start": p0,
                    "page_end": p1, "dialogues": json.loads(dialogues or "[]"), "grammar_notes": json.loads(notes or "[]")})
    return out


def stored_units(lessons):
    """lesson -> {"pages": (first, last), "units": [{"where": [column, path...], "text": str}]}, in the order the
    page has them: title, dialogues, notes."""
    out = {}
    for lesson in lessons:
        units = [{"where": ["skiri_title"], "text": lesson["skiri_title"] or ""}]
        for path, text in strings(lesson["dialogues"]):
            units.append({"where": ["dialogues"] + path, "text": text})
        for path, text in strings(lesson["grammar_notes"]):
            units.append({"where": ["grammar_notes"] + path, "text": text})
        out[lesson["lesson_number"]] = {"pages": (lesson["page_start"], lesson["page_end"]), "units": units}
    return out


def stored_tokens(lesson, units):
    toks = []
    for u, unit in enumerate(units):
        for m in re.finditer(r"\S+", unit["text"]):
            toks.append({"lesson": lesson, "unit": u, "where": unit["where"], "start": m.start(), "end": m.end(),
                         "token": m.group(0)})
    return toks


# ---------------------------------------------------------------- the page

def page_words(doc, first, last):
    """The words of the text layer of pages first..last in reading order: dicts with page, line id, box, word."""
    words = []
    for pno in range(first, last + 1):
        for x0, y0, x1, y1, word, block, line, _n in doc[pno - 1].get_text("words"):
            words.append({"page": pno, "line": "%d.%d.%d" % (pno, block, line), "box": (x0, y0, x1, y1), "word": word})
    return words


def line_up(stored, words):
    """Which word of the page is each stored word? Returns {index in stored: index in words}.

    The table holds the page twice over in places: the dialogues in one column, the notes in another, and a
    sentence may stand in both. So the dialogues are lined up with the page by themselves and the title and
    notes by themselves; within each, a word of the page takes one stored word. Several passes of difflib over
    what is still unpaired, because the page may have the texts in another order than the table. A single word
    is paired on its own only if it is long; short ones ('+', 'ti') are paired as part of a run or not at all,
    and get their line from their neighbours."""
    pairs = {}
    groups = collections.defaultdict(list)
    for i, t in enumerate(stored):
        groups["dialogues" if t["where"][0] == "dialogues" else "notes"].append(i)
    # A line in capitals is a title or a heading. A dialogue line is never one, though it may be the same sentence.
    letters_of = collections.defaultdict(str)
    for w in words:
        letters_of[w["line"]] += "".join(ch for ch in w["word"] if ch.isalpha())
    capitals = {lid for lid, text in letters_of.items()
                if len(text) >= 3 and sum(ch.isupper() for ch in text) >= 0.7 * len(text)}
    for name in ("notes", "dialogues"):
        members = groups.get(name, [])
        mine = {}
        for _ in range(6):
            left_s = [i for i in members if i not in mine]
            taken = set(mine.values())
            left_w = [j for j in range(len(words)) if j not in taken
                      and not (name == "dialogues" and words[j]["line"] in capitals)]
            if not left_s or not left_w:
                break
            a = [key_of(stored[i]["token"]) for i in left_s]
            b = [key_of(words[j]["word"]) for j in left_w]
            found = 0
            for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
                if block.size >= 2 or (block.size == 1 and len(a[block.a]) >= 6):
                    for k in range(block.size):
                        i, j = left_s[block.a + k], left_w[block.b + k]
                        # A word must fall between the words of its own text that already have a place: the
                        # same word in a vocabulary list elsewhere in the lesson is not its place.
                        unit = stored[i]["unit"]
                        before = next((mine[x] for x in range(i - 1, -1, -1) if x in mine and stored[x]["unit"] == unit), None)
                        after = next((mine[x] for x in range(i + 1, len(stored)) if x in mine and stored[x]["unit"] == unit), None)
                        if (before is not None and j < before) or (after is not None and j > after):
                            continue
                        mine[i] = j
                        found += 1
            if not found:
                break
        if name == "dialogues":
            # One word of a dialogue line paired by itself on another line than the rest of its line (the same
            # word in the vocabulary list of the page before) is not its place: it goes with the rest.
            per_unit = collections.defaultdict(lambda: collections.defaultdict(list))
            for i, j in mine.items():
                per_unit[stored[i]["unit"]][words[j]["line"]].append(i)
            for per_line in per_unit.values():
                if len(per_line) > 1 and max(len(v) for v in per_line.values()) >= 2:
                    for alone in [v[0] for v in per_line.values() if len(v) == 1]:
                        del mine[alone]
        pairs.update(mine)
    return pairs


def lines_of(lessons, doc):
    """Every line of the page that holds stored text: id -> {"page", "box", "layer", "stored": [stored tokens]},
    and the stored tokens that found no line."""
    lines, lost = collections.OrderedDict(), []
    for lesson, data in stored_units(lessons).items():
        # the title is not lined up: it is read from its own strip, the top of the lesson's first page
        stored = [t for t in stored_tokens(lesson, data["units"]) if t["where"] != ["skiri_title"]]
        words = page_words(doc, data["pages"][0], data["pages"][1])
        pairs = line_up(stored, words)
        by_line = collections.defaultdict(list)
        for j, w in enumerate(words):
            by_line[w["line"]].append(j)
        # a stored word without a partner takes the line of its neighbour in the same unit: the one before, or after
        place = {}
        for i in range(len(stored)):
            if i in pairs:
                place[i] = words[pairs[i]]["line"]
        # A stored word that pairs with no single word of the page may be one the OCR split in two, or two that it
        # ran together (the stored text has since been corrected, the text layer has not). Between its paired
        # neighbours, look for up to three words of one line that have the same letters as up to three stored words.
        pos = dict(pairs)                      # stored word -> word of the page, paired or found by its letters
        i = 0
        while i < len(stored):
            if i in place:
                i += 1
                continue
            j = i
            while j < len(stored) and j not in place:
                j += 1
            left = next((x for x in range(i - 1, -1, -1) if x in pos), None)
            right = next((x for x in range(j, len(stored)) if x in pos), None)
            lo = pos[left] + 1 if left is not None else 0
            hi = pos[right] if right is not None else len(words)
            k, w = i, lo
            while k < j:
                hit = None
                for ns in (1, 2, 3):
                    if k + ns > j or hit:
                        break
                    key = ocr_fold("".join(stored[x]["token"] for x in range(k, k + ns)))
                    if len(key) < 2:
                        continue
                    for start in range(w, hi):
                        for nw in (1, 2, 3):
                            if start + nw > hi or words[start + nw - 1]["line"] != words[start]["line"]:
                                break
                            if ocr_fold("".join(words[x]["word"] for x in range(start, start + nw))) == key:
                                hit = (ns, start, nw)
                                break
                        if hit:
                            break
                if hit:
                    for x in range(k, k + hit[0]):
                        place[x] = words[hit[1]]["line"]
                        pos[x] = hit[1]
                    k, w = k + hit[0], hit[1] + hit[2]
                else:
                    k += 1
            i = j
        by_letters = {i for i in place if i not in pairs}
        for i in range(len(stored)):
            if i in place:
                continue
            before = next((k for k in range(i - 1, -1, -1) if k in pos and stored[k]["unit"] == stored[i]["unit"]), None)
            after = next((k for k in range(i + 1, len(stored)) if k in pos and stored[k]["unit"] == stored[i]["unit"]), None)
            if before is not None and after is not None and place[before] != place[after]:
                # between two lines: the words of the page between its neighbours that have no partner show where
                gap = list(range(pos[before] + 1, pos[after]))
                rank = sum(1 for k in range(before + 1, i) if k not in pos)
                place[i] = words[gap[min(rank, len(gap) - 1)]]["line"] if gap else place[before]
            elif before is not None:
                place[i] = place[before]
            elif after is not None:
                place[i] = place[after]
            else:
                lost.append(stored[i])
        for forced in decisions().get("place", []):
            for i, tok in enumerate(stored):
                if forced["lesson"] == lesson and tok["where"] == forced["where"]:
                    place[i] = forced["strip"]
        for i, tok in enumerate(stored):
            if i not in place:
                continue
            lid = place[i]
            if lid not in lines and lid not in by_line:
                continue
            if lid not in lines:
                js = by_line[lid]
                xs0, ys0 = min(words[j]["box"][0] for j in js), min(words[j]["box"][1] for j in js)
                xs1, ys1 = max(words[j]["box"][2] for j in js), max(words[j]["box"][3] for j in js)
                lines[lid] = {"page": words[js[0]]["page"], "box": [xs0, ys0, xs1, ys1],
                              "layer": " ".join(words[j]["word"] for j in js), "stored": []}
            lines[lid]["stored"].append(dict(tok, paired=i in pairs or i in by_letters))
    return lines, lost


def title_strips(lessons, doc):
    """The top of each lesson's first page, where the title stands: T<lesson> -> {"page", "box"}."""
    out = {}
    for lesson in lessons:
        n, p0 = lesson["lesson_number"], lesson["page_start"]
        page = doc[p0 - 1]
        out["T%d" % n] = {"page": p0, "box": [14, 12, min(page.rect.width - 20, 300), 78], "lesson": n, "title": True,
                          "zoom": 1.05}           # the titles are in large capitals
    return out


def to_read(conn, doc, lessons=None):
    """The strips: the lines that need reading, and the title strips."""
    lexicon = english_lexicon(conn)
    lessons = lessons or load_lessons(conn)
    lines, lost = lines_of(lessons, doc)
    chosen = collections.OrderedDict()
    for lid, line in lines.items():
        tokens = [t["token"] for t in line["stored"]] + line["layer"].split()
        if needs_reading(tokens, lexicon):
            chosen[lid] = line
    chosen.update(title_strips(lessons, doc))
    lost = [t for t in lost if not is_english(t["token"], lexicon)]
    return chosen, lines, lost, lexicon


# ---------------------------------------------------------------- sheets

SHEET_W, SHEET_H = 552.0, 470.0        # points of the sheet; at 150 dpi 1150 x 979 pixels
LABEL_W = 40.0
ZOOM = 1.5                             # the scan is 150 dpi; the strips are drawn one and a half times that


def order_key(item):
    lid = item[0]
    if lid.startswith("T"):
        return (9999, int(lid[1:]), 0, 0) if len(item) == 1 else (0, int(lid[1:]), 0, 0)
    p, b, ln = (int(x) for x in lid.split("."))
    return (1, p, b, ln)


def draw(strips, folder, prefix, zoom=ZOOM, pad=(8, 3, 10, 2)):
    """Sheets of strips, packed in rows. strips: [(id, {"page", "box"})]. Returns {sheet file: [ids]}."""
    doc = fitz.open(str(PDF))
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("%s_*.png" % prefix):
        old.unlink()
    sheets, current, sheet, x, y, row_h = collections.OrderedDict(), [], None, 0.0, 4.0, 0.0

    def close():
        nonlocal sheet, current
        if sheet is not None and current:
            name = "%s_%02d.png" % (prefix, len(sheets) + 1)
            sheet[0].get_pixmap(matrix=fitz.Matrix(150 / 72.0, 150 / 72.0), alpha=False).save(str(folder / name))
            sheets[name] = current
        if sheet is not None:
            sheet.close()
        sheet, current = None, []

    for sid, s in strips:
        src = doc[s["page"] - 1]
        x0, y0, x1, y1 = s["box"]
        clip = fitz.Rect(max(0, x0 - pad[0]), max(0, y0 - pad[1]), min(src.rect.width, x1 + pad[2]),
                         min(src.rect.height, y1 + pad[3]))
        scale = min(s.get("zoom", zoom), (SHEET_W - LABEL_W - 4) / clip.width)
        w, h = clip.width * scale, clip.height * scale
        if sheet is not None and x + LABEL_W + w > SHEET_W - 2:
            x, y, row_h = 0.0, y + row_h + 5, 0.0
        if sheet is not None and y + h > SHEET_H - 2:
            close()
        if sheet is None:
            sheet = fitz.open()
            sheet.new_page(width=SHEET_W, height=SHEET_H)
            x, y, row_h = 0.0, 4.0, 0.0
        pg = sheet[0]
        pg.insert_text((x + 2, y + h / 2 + 3), sid, fontsize=6.5, color=(0, 0, 0.75))
        pg.show_pdf_page(fitz.Rect(x + LABEL_W, y, x + LABEL_W + w, y + h), doc, s["page"] - 1, clip=clip)
        pg.draw_rect(fitz.Rect(x + LABEL_W, y, x + LABEL_W + w, y + h), color=(0.8, 0.8, 0.8), width=0.3)
        current.append(sid)
        x += LABEL_W + w + 8
        row_h = max(row_h, h)
    close()
    return sheets


def cmd_plan(conn, doc, cut):
    chosen, lines, lost, _ = to_read(conn, doc)
    by_lesson = collections.Counter()
    for lid, line in chosen.items():
        by_lesson[line["lesson"] if "title" in line else line["stored"][0]["lesson"]] += 1
    stored_all = sum(len(l["stored"]) for l in lines.values())
    paired = sum(1 for l in lines.values() for t in l["stored"] if t["paired"])
    state.out("lines of the pages that hold stored text: %d (stored words %d, of them lined up word for word %d)" % (
        len(lines), stored_all, paired))
    state.out("strips to read: %d (of them %d title strips)" % (len(chosen), sum(1 for l in chosen.values() if "title" in l)))
    state.out("by lesson: " + ", ".join("L%d %d" % (n, by_lesson[n]) for n in sorted(by_lesson)))
    state.out("stored words that are not English and found no line: %d" % len(lost))
    for t in lost[:40]:
        state.out("   L%d %s %r" % (t["lesson"], "/".join(str(p) for p in t["where"]), t["token"]))
    if cut:
        items = sorted(chosen.items(), key=order_key)
        sheets = draw(items, FOLDER, "lt")
        key = {"sheets": sheets, "strips": {lid: {"page": l["page"], "box": l["box"]} for lid, l in chosen.items()}}
        (FOLDER / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
        state.out("sheets: %d in %s" % (len(sheets), FOLDER.relative_to(state.ROOT).as_posix()))


# ---------------------------------------------------------------- grading

def readings():
    """strip -> reading, and the strips read a second time (the second reading is the one that counts)."""
    read, twice = {}, set()
    for part in sorted(READINGS.glob("part_*.json")):
        read.update(json.loads(part.read_text(encoding="utf-8"))["read"])
    for part in sorted(READINGS.glob("second_*.json")):
        again = json.loads(part.read_text(encoding="utf-8"))["read"]
        read.update(again)
        twice.update(again)
    return read, twice


DECISIONS = READINGS / "decisions.json"


def decisions():
    """What was decided by hand after the second look: changes that the comparison of words cannot make (a word
    the OCR split over two lines, a piece of a breakdown line read as an English word), and differences that are
    left as they are, each with its reason."""
    if not DECISIONS.exists():
        return {}
    return json.loads(DECISIONS.read_text(encoding="utf-8"))


def audit_words(conn):
    """lesson -> the words of the audit's readings of that lesson's Blue Book forms, punctuation at the edge off."""
    out = collections.defaultdict(set)
    for n, form in conn.execute("select lesson_number, bb_skiri_form from blue_book_attestations where bb_skiri_form is not null"):
        for w in clean(form).split():
            out[n].add(w.strip(EDGE))
    return out


def audit_crops():
    """What the audit's readers read, and where on the page: page -> [(box, [readings])].

    The audit kept the place of every crop it cut. A row of the Blue Book table was cut where its stored
    letters were found in the text layer; for a short form that could be another line than the row's own
    (bluebook_right_place.py found this for the forms that were left open, not for those graded "same").
    Comparing by place, not by row, says whether a second reader has in fact read the line in question."""
    out = collections.defaultdict(list)

    def add(page, box, *reads):
        reads = [clean(r) for r in reads if r]
        if box and reads:
            out[page].append((box, reads))

    def rows(name):
        return json.loads((state.OUT / name).read_text(encoding="utf-8"))["rows"]

    for r in rows("bluebook_rest_graded.json"):
        add(r["page"], r["box"], r["read"])
    for r in rows("bluebook_graded.json"):
        add(r["page"], r.get("box"), r["read"])
    for r in rows("bluebook_second_look.json"):
        add(r["page"], r["box"], r["second_reading"])
    for r in rows("bluebook_right_place.json"):
        add(r["page"], r.get("box"), r.get("reading"))
    return out


def same_place(a, b):
    """Two boxes on one line of the page: they overlap sideways, and by half a line or more in height."""
    high = min(a[3], b[3]) - max(a[1], b[1])
    wide = min(a[2], b[2]) - max(a[0], b[0])
    return wide > 0 and high >= 0.5 * min(a[3] - a[1], b[3] - b[1])


def audit_here(item, line, crops):
    """What the audit's readers read at this place, set beside one difference:
    'the same', 'otherwise: <their word>', 'another word', or 'no reading'."""
    here = [r for box, reads in crops.get(line["page"], []) if same_place(line["box"], box) for r in reads]
    if not here:
        return "no reading"
    theirs = {w.strip(EDGE) for r in here for w in r.split() if "[?]" not in w}
    mine = [w.strip(EDGE) for w in (item.get("read") or "").split() if w.strip(EDGE)]
    if mine and all(w in theirs for w in mine):
        return "the same"
    letters = plain(item.get("read") or item.get("stored") or "")
    close = sorted(w for w in theirs if plain(w) == letters or (letters and plain(w) in [plain(m) for m in mine]))
    return "otherwise: " + ", ".join(close) if close else "another word"


def glue(tokens):
    """Stored tokens as units for comparing: a token without a letter that holds an apostrophe or a dot belongs to
    the word before it ("hitu '" is one damaged word, not a word and a stray mark)."""
    units = []
    for t in tokens:
        bare = re.sub(r"[^A-Za-z]", "", unaccent(t["token"]))
        if units and not bare and re.search(r"['•]", t["token"]):
            units[-1].append(t)
        else:
            units.append([t])
    return units


def span_text(unit_tokens, texts):
    first, last = unit_tokens[0], unit_tokens[-1]
    return texts[(first["lesson"], tuple(first["where"]))][first["start"]:last["end"]]


def accents(text):
    """The places of the accents: the numbers of the letters that carry one."""
    at, n = set(), -1
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.combining(ch):
            at.add(n)
        elif ch.isalpha():
            n += 1
    return at


def bare(text):
    """A piece of a breakdown line without its plus signs, equals signs, blanks for a dropped sound and numbers."""
    return " ".join(re.sub(r"[+=_0-9]", " ", unaccent(clean(text))).split())


ONE_READING = ("page has an accent the stored text lacks", "dot, apostrophe or space", "OCR slip")


def kind_of(stored, read):
    """What kind of difference: (kind, True if one reading is enough to take it).

    One reading is enough, as it was for the audit's reading of the Blue Book table, where the OCR is known to
    fail: it dropped every accent, misread the raised dot and the apostrophe, and made 'ti', 'ii', 'f', 'd', 'j'
    of accented vowels. Anything else (other letters, an accent the stored text has and the page lacks, a
    capital) needs a second look."""
    if "[?]" in read:
        return "reader unsure", False
    s, r = clean(stored), clean(read)
    if s == r:
        return "same", True
    if plain(s) != plain(r):
        if ocr_fold(s) == ocr_fold(r) and accents(r):
            return "OCR slip", True
        return "letters differ", False
    if accents(s) == accents(r) and bare(s) == bare(r):
        return "plus sign or spacing only", True          # not a difference in a word; never changed
    kinds = []
    if accents(s) != accents(r):
        kinds.append("page has an accent the stored text lacks" if accents(s) < accents(r) else
                     "stored text has an accent the page lacks" if accents(r) < accents(s) else "accent at another place")
    us, ur = unaccent(s), unaccent(r)
    if us != ur:
        # The OCR wrote an accented vowel as the vowel and an apostrophe (ha'k for hák): that many apostrophes
        # more in the stored text are the accents. Any other dot or apostrophe that the stored text has and the
        # reading lacks may be the reader's slip, and is not taken from one reading.
        spare = len(accents(r) - accents(s))
        if us.lower() == ur.lower():
            kinds.append("capitals differ")
        elif us.count("•") > ur.count("•") or us.count("'") > ur.count("'") + spare:
            kinds.append("stored text has a dot or apostrophe the page lacks")
        else:
            kinds.append("dot, apostrophe or space")
    return "; ".join(kinds), all(k in ONE_READING for k in kinds)


def core(text):
    """A word without the punctuation of the sentence around it: (characters cut in front, behind, the rest)."""
    lead = len(text) - len(text.lstrip(EDGE))
    trail = len(text) - len(text.rstrip(EDGE)) if text.strip(EDGE) else 0
    return lead, trail, text.strip(EDGE)


def grade_line(lid, line, read_text, lexicon, texts):
    """The differences between one strip's reading and the stored words of its line. The punctuation of the
    sentence (. , ; : ! ? brackets, quotation marks) is not compared and is never changed."""
    diffs = []
    units = glue(line["stored"])
    stored_text = [span_text(u, texts) for u in units]
    read = clean(read_text).split()
    a = [key_of(s) for s in stored_text]
    b = [key_of(r) for r in read]
    for op, a0, a1, b0, b1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(a1 - a0):
                diffs.append((units[a0 + k], stored_text[a0 + k], read[b0 + k]))
        elif op == "replace":
            # English beside the Pawnee is not part of the difference
            while a0 < a1 and is_english(stored_text[a0], lexicon):
                a0 += 1
            while a0 < a1 and is_english(stored_text[a1 - 1], lexicon):
                a1 -= 1
            while b0 < b1 and is_english(read[b0], lexicon):
                b0 += 1
            while b0 < b1 and is_english(read[b1 - 1], lexicon):
                b1 -= 1
            if a0 == a1:
                diffs += [(None, None, r) for r in read[b0:b1] if not is_english(r, lexicon)]
            elif b0 == b1:
                diffs += [(units[k], stored_text[k], None) for k in range(a0, a1) if not is_english(stored_text[k], lexicon)]
            else:
                both = [units[a0][0], units[a1 - 1][-1]]
                diffs.append((both, span_text(both, texts), " ".join(read[b0:b1])))
        elif op == "delete":
            for k in range(a0, a1):
                if not is_english(stored_text[k], lexicon):
                    diffs.append((units[k], stored_text[k], None))
        elif op == "insert":
            for k in range(b0, b1):
                if not is_english(read[k], lexicon):
                    diffs.append((None, None, read[k]))
    out = []
    for unit, s, r in diffs:
        item = {"strip": lid, "page": line["page"], "lesson": line["stored"][0]["lesson"]}
        if s is None:
            item.update(stored=None, read=core(r)[2], kind="on the page, not in the stored text", one_reading=False)
        elif r is None:
            if not core(s)[2]:
                continue
            item.update(stored=core(s)[2], read=None, kind="stored, not in the reading", one_reading=False)
        else:
            lead, trail, cs = core(s)
            cr = core(r)[2]
            # The OCR wrote the raised dot as a full stop. A stop that touches the stored word at an end where
            # the reading has a raised dot is that dot, not the punctuation of the sentence.
            if cr.endswith("•") and trail and s[len(s) - trail] == ".":
                trail -= 1
            if cr.startswith("•") and lead and s[lead - 1] == ".":
                lead -= 1
            cs = s[lead:len(s) - trail]
            kind, enough = kind_of(cs, cr)
            if kind == "same":
                continue
            if "[" in cs:              # letters under a flaw in the scan, marked by hand: never changed from here
                enough = False
            item.update(stored=cs, read=cr, kind=kind, one_reading=enough)
            item.update(lesson=unit[0]["lesson"], where=unit[0]["where"], start=unit[0]["start"] + lead,
                        end=unit[-1]["end"] - trail)
        if unit is not None and "start" not in item:
            lead, trail, _ = core(s)
            item.update(lesson=unit[0]["lesson"], where=unit[0]["where"], start=unit[0]["start"] + lead,
                        end=unit[-1]["end"] - trail)
        out.append(item)
    return out


def grade(conn, doc, lessons=None):
    """Everything --grade knows, as a dict. lessons: the lessons to grade, if not those of the table (a plan)."""
    lessons = lessons or load_lessons(conn)
    chosen, lines, lost, lexicon = to_read(conn, doc, lessons)
    read, twice = readings()
    decided = decisions()
    left = {(d["strip"], d.get("stored"), d.get("read")): d["why"] for d in decided.get("leave", [])}
    texts = {}
    for lesson, data in stored_units(lessons).items():
        for unit in data["units"]:
            texts[(lesson, tuple(unit["where"]))] = unit["text"]
    audit = audit_words(conn)
    crops = audit_crops()
    rows, tally, not_read, titles = [], collections.Counter(), [], {}
    for lid, line in chosen.items():
        if lid not in read:
            not_read.append(lid)
            continue
        if "title" in line:
            titles[line["lesson"]] = (lid, clean(read[lid]))
            continue
        # A line of the page may hold words of two stored texts (a dialogue line and its English; the title of
        # the next lesson, which the extraction also left at the end of a lesson's notes). The reading is put
        # beside each; a word of the reading is "not in the stored text" only if none of them has it.
        groups = collections.OrderedDict()
        for t in line["stored"]:
            if t["where"] != ["skiri_title"]:              # a title is graded by its own strip, T1 ... T20
                groups.setdefault((t["lesson"], tuple(t["where"])), []).append(t)
        per_group = [grade_line(lid, dict(line, stored=toks), read[lid], lexicon, texts) for toks in groups.values()]
        extra = [set(i["read"] for i in items if i["stored"] is None) for items in per_group]
        nowhere = set.intersection(*extra) if extra else set()
        items = []
        for group in per_group:
            for item in group:
                if item["stored"] is None:
                    if item["read"] not in nowhere:
                        continue
                    nowhere.discard(item["read"])
                items.append(item)
        for item in items:
            item["read_twice"] = lid in twice
            if item.get("read"):
                item["audit_has_the_reading"] = item["read"] in audit[item["lesson"]] or all(
                    w.strip(EDGE) in audit[item["lesson"]] for w in item["read"].split())
            if item.get("stored"):
                item["audit_has_the_stored"] = item["stored"] in audit[item["lesson"]]
            item["audit_here"] = audit_here(item, line, crops)
            why = left.get((lid, item.get("stored"), item.get("read")))
            if why:
                item.update(left=why, one_reading=False)
            if item["kind"] == "plus sign or spacing only":
                continue
            tally[item["kind"]] += 1
            rows.append(item)
    title_rows = []
    for n, title in ((x["lesson_number"], x["skiri_title"]) for x in lessons):
        if n in titles:
            lid, shown = titles[n]
            kind = kind_of(title or "", shown)[0] if title else "no title stored"
            title_rows.append({"lesson": n, "strip": lid, "stored": title, "read": shown, "kind": kind,
                               "read_twice": lid in twice})
            tally["title: " + kind] += 1
    covered = sum(1 for lid, l in chosen.items() if lid in read and "title" not in l
                  for t in l["stored"] if not is_english(t["token"], lexicon))
    return {"strips": len(chosen), "read": len(chosen) - len(not_read), "read_twice": len(twice & set(chosen)),
            "not_read": not_read, "stored_words_not_english_in_strips_read": covered, "tally": dict(tally),
            "titles": title_rows, "differences": rows,
            "no_line": [{"lesson": t["lesson"], "where": t["where"], "token": t["token"]} for t in lost]}


def cmd_grade(conn, doc, show):
    result = grade(conn, doc)
    GRADED.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("strips %d, read %d (twice %d); stored words that are not English in the strips read: %d" % (
        result["strips"], result["read"], result["read_twice"], result["stored_words_not_english_in_strips_read"]))
    state.out("differences: %s" % result["tally"])
    if show:
        for item in result["differences"]:
            state.out("  %-10s L%-2s %-42s %s | %s   [audit here: %s]" % (
                item["strip"], item.get("lesson"), item["kind"], item["stored"], item["read"], item["audit_here"]))
        for t in result["titles"]:
            if t["kind"] != "same":
                state.out("  title L%-2d %-30s %s | %s" % (t["lesson"], t["kind"], t["stored"], t["read"]))


def cmd_open(conn, doc):
    """What one reading does not settle, strip by strip, with the reading and the stored words of the line."""
    result = grade(conn, doc)
    chosen, lines, _, _ = to_read(conn, doc)
    read, _ = readings()
    seen = []
    for item in result["differences"]:
        if not item["one_reading"] and not item.get("left") and item["strip"] not in seen:
            seen.append(item["strip"])
    for lid in seen:
        line = chosen[lid]
        state.out("%s  p.%d  read: %s" % (lid, line["page"], read[lid]))
        for item in result["differences"]:
            if item["strip"] == lid and not item["one_reading"] and not item.get("left"):
                state.out("     %s: %s | %s" % (item["kind"], item["stored"], item["read"]))
        groups = collections.OrderedDict()
        for t in line["stored"]:
            groups.setdefault((t["lesson"], "/".join(str(p) for p in t["where"])), []).append(t)
        for (lesson, where), toks in groups.items():
            state.out("     L%d %s [%d:%d]: %s" % (lesson, where, toks[0]["start"], toks[-1]["end"],
                                                  " ".join(t["token"] for t in toks)))
    state.out("%d strips" % len(seen))


def layer_line(doc, lid):
    """Any line of the text layer by its number page.block.line: {"page", "box"}."""
    page, block, line = (int(x) for x in lid.split("."))
    words = [w for w in doc[page - 1].get_text("words") if (w[5], w[6]) == (block, line)]
    if not words:
        return None
    return {"page": page, "box": [min(w[0] for w in words), min(w[1] for w in words),
                                  max(w[2] for w in words), max(w[3] for w in words)]}


def cmd_second(conn, doc, only):
    """Cut again what one reading does not settle: from the left margin of the page (a form may stand in the
    column to the left of the line that was cut), and larger. Without --only: every strip with a difference
    that one reading does not settle. With --only: those lines (page.block.line or T<lesson>); an id ending
    in '+' is cut with the line above and the line below."""
    graded = json.loads(GRADED.read_text(encoding="utf-8"))
    chosen, _, _, _ = to_read(conn, doc)
    want = list(only)
    if not want:
        for item in graded["differences"]:
            if not item["one_reading"] and item["strip"] not in want:
                want.append(item["strip"])
        want += [t["strip"] for t in graded["titles"] if t["kind"] != "same"]
    strips = []
    for spec in sorted(want, key=lambda x: order_key((x.rstrip("+"),))):
        lid, tall = spec.rstrip("+"), spec.endswith("+")
        line = chosen.get(lid) or layer_line(doc, lid)
        if not line:
            state.out("no such line: %s" % lid)
            continue
        if "title" in line:
            strips.append((lid, {"page": line["page"], "box": [6, 10, 330, 84], "zoom": 1.3}))
            continue
        x0, y0, x1, y1 = line["box"]
        around = 14 if tall else 5
        strips.append((lid, {"page": line["page"], "box": [22, y0 - around, max(x1, 200), y1 + around], "zoom": 1.9}))
    sheets = draw(strips, FOLDER, "second", zoom=1.9, pad=(8, 3, 14, 3))
    state.out("strips for a second look: %d on %d sheets (%s)" % (len(strips), len(sheets), FOLDER.relative_to(state.ROOT).as_posix()))
    for name, ids in sheets.items():
        state.out("  %s: %s" % (name, " ".join(ids)))


def cmd_where(conn, doc, lid):
    chosen, lines, _, _ = to_read(conn, doc)
    line = chosen.get(lid) or lines.get(lid)
    if not line:
        state.out("no such strip")
        return
    state.out("page %s, text layer: %s" % (line["page"], line.get("layer")))
    for t in line.get("stored", []):
        state.out("  L%d %s [%d:%d] %s%s" % (t["lesson"], "/".join(str(p) for p in t["where"]), t["start"], t["end"],
                                            t["token"], "" if t["paired"] else "   (placed by its neighbours)"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="count the strips; cut nothing")
    ap.add_argument("--sheets", action="store_true", help="cut the strips onto sheets")
    ap.add_argument("--grade", action="store_true", help="compare the readings with the stored text")
    ap.add_argument("--show", action="store_true", help="with --grade: list every difference")
    ap.add_argument("--second", action="store_true", help="cut again what the grading left open")
    ap.add_argument("--open", action="store_true", help="what one reading does not settle, with the stored words")
    ap.add_argument("--only", metavar="IDS", help="with --second: the lines to cut, comma-separated; 'ID+' with the lines around")
    ap.add_argument("--where", metavar="ID", help="what the stored text has at a strip")
    args = ap.parse_args()
    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    doc = fitz.open(str(PDF))
    if args.grade:
        cmd_grade(conn, doc, args.show)
    elif args.open:
        cmd_open(conn, doc)
    elif args.second:
        cmd_second(conn, doc, [x for x in (args.only or "").split(",") if x])
    elif args.where:
        cmd_where(conn, doc, args.where)
    else:
        cmd_plan(conn, doc, cut=args.sheets)


if __name__ == "__main__":
    main()
