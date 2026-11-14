#!/usr/bin/env python3
"""
The grammar chapter read a second time, blind (2026-11-14)
==========================================================

Chapter 4 (Grammatical Overview, book pages 29 to 51) has no text layer. The
stored copy, extracted_data/grammatical_overview.json, is one AI reading of
the page images (March 2026, prose paraphrased). The audit had the Skiri forms
read once more by a reader who saw only the page (blind_readings/
chapter4_part*.json). Where the two differ, one reading stands against one,
and that settles nothing.

This script sets up and grades a second blind reading, by readers who see
neither the stored copy nor the first reading:

    python scripts/source_audit/chapter4_second_reading.py --sheets   # cut the pages into tiles, one folder per reader
    python scripts/source_audit/chapter4_second_reading.py --zoom p10-b2 0 0.5 0.6 1
                                                                      # for a reader: part of a tile, drawn twice as large
    (the readers write blind2.json in their folder; copy each to
     reports/source_audit_2026-11/blind_readings/chapter4_second_part<N>.json)
    python scripts/source_audit/chapter4_second_reading.py            # grade; writes chapter4_second_reading.json
    python scripts/source_audit/chapter4_second_reading.py --apply    # correct the stored chapter where both blind readings agree

The tiles are cut differently from the first reading's (one band per image, a
little larger, the bands placed by where the print is on each page), so a line
that fell on a cut the first time does not fall on one again.

Grading. Every Skiri word of the stored chapter is looked for in both blind
readings of its page (and the page before and after, as the audit did):

    three readings agree            the word is in both blind readings
    second reading has the stored word   the first reader read something else there; two against one,
                                    the stored word stands
    second reader differs           the first reader has the stored word, the second read something
                                    else or did not list it; two against one, the stored word stands
    both blind readings agree       neither reader has the stored word, and both read the same other
                                    word at that place: the stored word is corrected (--apply)
    place not certain               both read the same other word, but nothing ties it to the place of
                                    the stored word (no gloss, no neighbouring word, or the stored page
                                    has that word as well): left for a person
    three different readings        left for a person
    not a Skiri word                English or a label that only looks like Skiri (listed in NOT_SKIRI)
    in neither reading              nothing close in either reading: prose the stored copy paraphrased

"At that place" means: the blind reader's word has the same English gloss
after it as the stored word, or the same Skiri word before or after it, or the
same grammatical label where only one word like it carries that label. A long
word (eight letters or more) that is the only one like it on the page is also
taken as placed. A correction takes the letters both readers saw; no word of
fewer than four letters is corrected, and none a reader marked as unclear.

Each row also says whether the stored word and the readers' word are forms the
dictionary itself prints (they are checked against the PDF's text). Where the
chapter and the dictionary print a word differently, the chapter's own
printing is what its stored copy should hold; the row keeps the conflict
visible.

Two further passes look at what a comparison of words cannot see.

Breakdown lines. The analysis after "<" (ti- IND + Ø- 3.A + kikak 'cry' + -Ø
PERF) is cut into its pieces. A stored line is laid beside the first reader's
line; where one piece has another form (a hyphen, the length mark of -:hus, a
zero), the stored piece is corrected if the second reader has the first
reader's piece with the same label or gloss and neither reader has the stored
one. Differences of spacing, an apostrophe printed for the glottal stop and a
stray semicolon in the print are not differences.

Places named one by one (BY_HAND). Table 17 and four other places where the
stored copy had merged or changed cells; each is applied only while both
blind readings hold the text named as its evidence.
"""
import argparse
import collections
import datetime as dt
import difflib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appendix_tiles  # noqa: E402
import chapter4_third_witness as third  # noqa: E402
import chapters_compare as cc4  # noqa: E402
import state  # noqa: E402

WORK = state.WORK / "chapter4_second"
CHAPTER = state.ROOT / "extracted_data" / "grammatical_overview.json"
READINGS = state.OUT / "blind_readings"
RECORD = state.OUT / "chapter4_second_reading.json"
LABEL = re.compile(r"^[A-Z0-9Ø][A-Z0-9./ ]*$")      # a grammatical label in small capitals: PL, IND.1/2.A
UNSURE = "ZQZ"                                     # stands for the reader's [?] while a form is cut into words
GLOSS = re.compile(r"[‘'\"“](.{1,140}?)[’'\"”](?![A-Za-z])")     # the closing mark is not the apostrophe of don't
# Stored "words" that are English or labels; the audit's word test took them for Skiri. Checked by eye in the stored text.
NOT_SKIRI = {"st", "an", "has", "INCH", "Input"}
PARTS = [(1, 1, 8), (2, 9, 16), (3, 17, 23)]       # reader, first page, last page (pages of the PDF)
BANDS, ZOOM, OVERLAP = 4, 3.0, 20.0


def ink_box(page):
    """The box that holds the print of a page, found on a coarse rendering."""
    scale = 0.5
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
    w, h, data = pix.width, pix.height, pix.samples
    rows = [y for y in range(h) if min(data[y * w:(y + 1) * w]) < 128]
    cols = [x for x in range(w) if min(data[x::w]) < 128]
    return fitz.Rect(cols[0] / scale, rows[0] / scale, (cols[-1] + 1) / scale, (rows[-1] + 1) / scale)


def sheets():
    src = fitz.open(str(appendix_tiles.find_pdf("Grammatical_Overview")))
    made, key = 0, {}
    for part, first, last in PARTS:
        folder = WORK / ("part%d" % part)
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        names = []
        for pno in range(first - 1, last):
            box = ink_box(src[pno])
            left, right = max(0.0, box.x0 - 10), min(src[pno].rect.width, box.x1 + 10)
            top, bottom = max(0.0, box.y0 - 8), min(src[pno].rect.height, box.y1 + 8)
            step = (bottom - top) / BANDS
            for b in range(BANDS):
                y0 = top + step * b - (OVERLAP / 2 if b else 0)
                y1 = top + step * (b + 1) + (OVERLAP / 2 if b < BANDS - 1 else 0)
                label = "p%d-b%d" % (pno + 1, b + 1)
                path = folder / ("ch4_p%02d_b%d.png" % (pno + 1, b + 1))
                size = appendix_tiles.sheet([(label, pno, fitz.Rect(left, y0, right, y1))], src, path, ZOOM, 1)
                key[label] = {"part": part, "page": pno, "clip": [left, y0, right, y1]}
                names.append(path.name)
                made += 1
        state.out("reader %d: pages %d-%d, %d tiles in %s (last %dx%d)" % (
            part, first, last, len(names), folder.relative_to(state.ROOT).as_posix(), size[0], size[1]))
    (WORK / "tiles.json").write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("%d tiles" % made)


def zoom(label, x0, y0, x1, y1):
    """Part of a tile drawn from the PDF at twice the tile's size. The corners are fractions of the tile, 0 to 1."""
    key = json.loads((WORK / "tiles.json").read_text(encoding="utf-8"))
    if label not in key:
        sys.exit("no tile %r" % label)
    t = key[label]
    cx0, cy0, cx1, cy1 = t["clip"]
    x0, x1 = sorted((min(1.0, max(0.0, x0)), min(1.0, max(0.0, x1))))
    y0, y1 = sorted((min(1.0, max(0.0, y0)), min(1.0, max(0.0, y1))))
    clip = fitz.Rect(cx0 + (cx1 - cx0) * x0, cy0 + (cy1 - cy0) * y0, cx0 + (cx1 - cx0) * x1, cy0 + (cy1 - cy0) * y1)
    if clip.width < 5 or clip.height < 5:
        sys.exit("the part asked for is empty")
    factor = min(2 * ZOOM, 1500.0 / clip.width, 1500.0 / clip.height)
    src = fitz.open(str(appendix_tiles.find_pdf("Grammatical_Overview")))
    folder = WORK / ("part%d" % t["part"]) / "crops"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("%s_%03d-%03d_%03d-%03d.png" % (label, round(x0 * 100), round(x1 * 100), round(y0 * 100), round(y1 * 100)))
    src[t["page"]].get_pixmap(matrix=fitz.Matrix(factor, factor), clip=clip, alpha=False).save(str(path))
    print(path)


Occ = collections.namedtuple("Occ", "page tile key raw gloss prev next label unsure text")


def bare(word):
    """A word without its accent marks."""
    return unicodedata.normalize("NFC", "".join(ch for ch in unicodedata.normalize("NFD", word) if ch != "\u0301"))


def norm_gloss(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def words_of(text):
    """[(key, raw, start, end)] for every word of a string, in order.

    Quotation marks around a gloss are not part of a word. An apostrophe that closes no gloss is: the
    print sometimes has an apostrophe where the glottal stop belongs (tikiwaaku' beside tikacaakuʔ), and
    both readers copied it."""
    out = []
    glosses = [m.span() for m in GLOSS.finditer(text)]
    for m in cc4.TOKEN.finditer(text):
        a, b = m.start(), m.end()
        in_gloss = any(g0 <= a and b <= g1 for g0, g1 in glosses) or (a > 0 and text[a - 1] in "‘“")
        raw = m.group(0).strip("'’") if in_gloss else m.group(0).lstrip("'’")
        if not in_gloss and raw.endswith(("'", "’")) and not re.search(r"[a-zʔ]{2}['’]$", raw):
            raw = raw.rstrip("'’")
        if cc4.key(raw):
            out.append((cc4.key(raw), raw, a, b))
    return out


def gloss_after(text, end):
    """The gloss in quotation marks that follows a word, if only Skiri words stand between."""
    m = GLOSS.search(text, end)
    if m is None or "\n" in text[end:m.start()]:
        return ""
    between = text[end:m.start()]
    if re.search(r"[<+=;(]|[A-Z]{2}", between):
        return ""
    return norm_gloss(m.group(1))


def same_gloss(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return (len(short) >= 8 and long_.startswith(short)) or difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.88


def label_after(text, end):
    m = re.match(r"\s*([A-Z][A-Z0-9./]+)", text[end:])
    return m.group(1) if m else ""


def reading(pattern):
    """A blind reading as {page: [Occ]}, and the readers' own count of forms."""
    pages, n_forms, n_tiles = collections.defaultdict(list), 0, 0
    for f in sorted(READINGS.glob(pattern)):
        for label, tile in json.loads(f.read_text(encoding="utf-8")).items():
            n_tiles += 1
            page = int(re.match(r"p(\d+)", label).group(1))
            entries = []
            for x in tile.get("forms", []):
                if x:
                    entries.append((str(x[0]), str(x[1]) if len(x) > 1 else ""))
                    n_forms += 1
            for t in tile.get("tables", []):
                if t.get("title"):
                    entries.append((str(t["title"]), ""))
                for row in t.get("rows", []):
                    entries.append(("  |  ".join(str(c) for c in (row if isinstance(row, list) else [row])), ""))
            # A reader may give a whole line as one form, or its pieces one by one with the label of each
            # in the gloss slot. Either way a word's neighbours are the words before and after it in the tile.
            tile_words = []
            for form, gloss in entries:
                text = unicodedata.normalize("NFC", form).replace("[?]", UNSURE)
                gloss = unicodedata.normalize("NFC", gloss).strip()
                is_label = bool(LABEL.match(gloss))
                found = [(k.replace(UNSURE, ""), r.replace(UNSURE, ""), a, b, UNSURE in r) for k, r, a, b in words_of(text)]
                found = [w for w in found if w[0]]
                for i, (k, raw, a, b, unsure) in enumerate(found):
                    last = i + 1 == len(found)
                    tile_words.append([k, raw, gloss_after(text, b) or ("" if is_label or not last else norm_gloss(gloss)),
                                       label_after(text, b) or (gloss if is_label and last else ""), unsure, form])
            for i, (k, raw, g, lab, unsure, form) in enumerate(tile_words):
                pages[page].append(Occ(page, label, k, raw, g, tile_words[i - 1][0] if i else "",
                                       tile_words[i + 1][0] if i + 1 < len(tile_words) else "", lab, unsure, form))
    return pages, n_forms, n_tiles


def stored_words():
    """The stored chapter as {page: [Occ]}: the words the audit counted, each with what stands around it."""
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    pages = collections.defaultdict(list)

    def walk(node, path, page, label=""):
        if isinstance(node, dict):
            own = node.get("label") if isinstance(node.get("label"), str) else ""
            for k, v in node.items():
                walk(v, path + [str(k)], page, own if k == "form" else "")
        elif isinstance(node, list):
            for v in node:
                walk(v, path, page)
        elif isinstance(node, str):
            strict = any(q in ("morphemes_mentioned", "tables") or "form" in q or "skiri" in q or "morpheme" in q or "example" in q
                         for q in path) and not any(q in ("content", "heading", "description", "gloss", "english", "meaning", "label")
                                                    for q in path[-1:])
            text = unicodedata.normalize("NFC", node)
            wanted = collections.Counter(cc4.tokens(text, strict))
            # The audit's word test asks for ʔ or a doubled vowel in running text, and an accent on one of
            # two vowels hides the pair (rakuracakipíitit). A word of Skiri letters with an accent is counted too.
            for m in cc4.TOKEN.finditer(text):
                tok = m.group(0).strip("'’")
                if tok != bare(tok) and cc4.SKIRI_ONLY.match(tok) and len(cc4.key(tok)) >= 4:
                    wanted[tok] += 1
            found = words_of(text)
            counted = [i for i, w in enumerate(found) if wanted.get(w[1]) or wanted.get(w[1].strip("'’"))]
            for n, i in enumerate(counted):
                k, raw, a, b = found[i]
                line_start = text.rfind("\n", 0, a) + 1
                line_end = text.find("\n", b)
                snippet = text[max(line_start, a - 70):min(len(text) if line_end < 0 else line_end, b + 90)]
                pages[page].append(Occ(page, "/".join(path[-3:]), k, raw, gloss_after(text, b),
                                       found[counted[n - 1]][0] if n else "", found[counted[n + 1]][0] if n + 1 < len(counted) else "",
                                       label or label_after(text, b), False, snippet))

    for name, node in data.items():
        walk(node, [], int(name.split("_")[1]))
    return pages


def near(pages, page):
    out = []
    for q in (page, page - 1, page + 1):
        out += pages.get(q, [])
    return out


def best(stored, candidates):
    """The reader's word at the place of a stored word: (Occ, ratio, [what places it]) or (None, 0, [])."""
    top, top_score, close = (None, 0.0, []), 0.0, []
    for c in candidates:
        if abs(len(c.key) - len(stored.key)) > 3:
            continue
        r = 1.0 if c.key == stored.key else difflib.SequenceMatcher(None, stored.key, c.key, autojunk=False).ratio()
        if r < 0.6:
            continue
        close.append(c)
        by = []
        if same_gloss(stored.gloss, c.gloss):
            by.append("gloss")
        if stored.prev and stored.prev == c.prev:
            by.append("word before")
        if stored.next and stored.next == c.next:
            by.append("word after")
        if stored.label and stored.label == c.label:
            by.append("label")
        score = r + 0.6 * ("gloss" in by) + 0.2 * ("word before" in by) + 0.2 * ("word after" in by) + 0.3 * ("label" in by) \
            + (0.01 if c.page == stored.page else 0)
        if score > top_score:
            top, top_score = (c, r, by), score
    c, r, by = top
    if by == ["label"] and len({x.key for x in close if x.label == stored.label}) > 1:
        by = []                      # several words like it carry that label: the label does not say which
    if c is None and stored.gloss:
        # nothing like it in letters: the one word the reader has before the same gloss
        same = [x for x in candidates if same_gloss(stored.gloss, x.gloss) and x.next != stored.key]
        if len({x.key for x in same}) == 1:
            x = same[0]
            return x, difflib.SequenceMatcher(None, stored.key, x.key, autojunk=False).ratio(), ["gloss alone"]
    return c, r, by


def corrected_word(stored_raw, first, second):
    """The stored word with the letters both readers saw. Hyphens as both readers have them, else as stored."""
    if first.raw == second.raw:
        return first.raw
    lead = len(stored_raw) - len(stored_raw.lstrip("-"))
    trail = len(stored_raw) - len(stored_raw.rstrip("-"))
    return "-" * lead + first.raw.strip("-") + "-" * trail


def grade():
    first, forms1, tiles1 = reading("chapter4_part*.json")
    second, forms2, tiles2 = reading("chapter4_second_part*.json")
    if not second:
        sys.exit("no second reading in %s yet" % READINGS.relative_to(state.ROOT).as_posix())
    stored = stored_words()
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    known = third.dictionary_forms(conn)
    conn.close()
    rows, tally = [], collections.Counter()
    for page in sorted(stored):
        near1, near2 = near(first, page), near(second, page)
        pool1, pool2 = {c.key for c in near1}, {c.key for c in near2}
        stored_keys = {o.key for q in (page - 1, page, page + 1) for o in stored.get(q, [])}
        by_key = collections.OrderedDict()
        for o in stored[page]:
            by_key.setdefault(o.key, []).append(o)
        for k, occs in by_key.items():
            tally["words"] += 1
            in1, in2 = k in pool1, k in pool2
            if in1 and in2:
                tally["three readings agree"] += 1
                continue
            # the occurrence that says most about its place
            occs = sorted(occs, key=lambda o: -(bool(o.gloss) + bool(o.prev) + bool(o.next) + bool(o.label)))
            o = occs[0]
            c1, r1, placed1 = (None, 1.0, []) if in1 else best(o, near1)
            c2, r2, placed2 = (None, 1.0, []) if in2 else best(o, near2)
            row = {"page": page, "book_page": 28 + page, "stored": o.raw, "where": o.tile, "stored_text": o.text.strip(),
                   "first_reading": k if in1 else (c1.raw if c1 else ""), "second_reading": k if in2 else (c2.raw if c2 else ""),
                   "stored_is_dictionary_form": k in known}
            for name, c in (("first", c1), ("second", c2)):
                if c is not None and c.key != k:
                    row[name + "_reading_is_dictionary_form"] = c.key in known
            for name, c in (("first", c1), ("second", c2)):
                if c is not None:
                    row[name + "_tile"], row[name + "_text"] = c.tile, c.text
                    if c.unsure:
                        row[name + "_unsure"] = True
            if o.raw in NOT_SKIRI:
                verdict = "not a Skiri word"
            elif in2:
                verdict = "second reading has the stored word"
            elif in1:
                verdict = "second reader differs"
                row["second_reading"] = c2.raw if c2 else ""
            elif c1 is None and c2 is None:
                verdict = "in neither reading"
            elif c1 is not None and c2 is not None and c1.key == c2.key:
                elsewhere = c1.key in stored_keys
                no_accent_seen = (bare(k) == bare(c1.key) and k != c1.key
                                  and not any(c.key != bare(c.key) for c in near1 + near2))
                if len(k) < 4 or c1.unsure or c2.unsure:
                    verdict = "place not certain"
                elif no_accent_seen:
                    # the stored word differs only in an accent, and neither reader saw an accent on any word
                    # of this page or its neighbours: wherever the word stands, it has none
                    verdict = "both blind readings agree"
                    row["correct_to"] = corrected_word(o.raw, c1, c2)
                    row["placed_by"] = "neither reader saw an accent anywhere on these pages"
                elif (placed1 or placed2) or (not elsewhere and len(k) >= 8 and min(r1, r2) >= 0.85):
                    verdict = "both blind readings agree"
                    row["correct_to"] = corrected_word(o.raw, c1, c2)
                    row["placed_by"] = ", ".join(sorted(set(placed1) | set(placed2))) or "the only word like it on the page"
                else:
                    verdict = "place not certain"
            else:
                verdict = "three different readings"
            row["verdict"] = verdict
            tally[verdict] += 1
            rows.append(row)
    # the two blind readings against each other, whatever the stored copy says
    both = only1 = only2 = 0
    for page in sorted(set(first) | set(second)):
        k1 = {c.key for c in near(first, page)}
        k2 = {c.key for c in near(second, page)}
        own1, own2 = {c.key for c in first.get(page, [])}, {c.key for c in second.get(page, [])}
        both += len({k for k in own1 if k in k2} | {k for k in own2 if k in k1})
        only1 += len({k for k in own1 if k not in k2})
        only2 += len({k for k in own2 if k not in k1})
    readers = {"first_reading": {"tiles": tiles1, "forms": forms1}, "second_reading": {"tiles": tiles2, "forms": forms2},
               "distinct_words_per_page_in_both": both, "only_in_first": only1, "only_in_second": only2}
    return rows, tally, readers


def replace_word(node, old, new):
    """Replace old by new where it stands as a whole word, in every string under node."""
    pattern = re.compile(r"(?<![A-Za-zʔíáúÍÁÚ\u0301-])%s(?![A-Za-zʔíáúÍÁÚ\u0301-])" % re.escape(old))
    n = 0
    items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else ()
    for k, v in list(items):
        if isinstance(v, str):
            v2 = unicodedata.normalize("NFC", v)
            if pattern.search(v2):
                node[k] = pattern.sub(new, v2)
                n += 1
        else:
            n += replace_word(v, old, new)
    return n


# ---------------------------------------------------------------------------------------------------------
# Breakdown lines
# ---------------------------------------------------------------------------------------------------------

def norm_line(text):
    """A breakdown line with plain quotation marks and even spacing."""
    t = unicodedata.normalize("NFC", str(text))
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        t = t.replace(a, b)
    t = re.sub(r"\s*\+\s*", " + ", t)
    t = re.sub(r"Ø\s+-\s", "Ø- ", t)                  # the print has "Ø - 3.A" in places; it is Ø- 3.A
    t = re.sub(r"\s+", " ", t).strip().lstrip("<").strip().strip(";.,").strip()
    if t.endswith(")") and t.count(")") > t.count("("):
        t = t[:-1].strip()                           # the bracket that closes "(< ... )" is not part of the last piece
    return t


def pieces(line):
    """[(form, label or gloss)] of a normalised breakdown line."""
    out = []
    for chunk in line.split(" + "):
        form, _, rest = chunk.strip().partition(" ")
        if form:
            out.append((form, rest.strip().strip("'\"").strip()))
    return out


def reading_lines(pattern):
    """A blind reading as ({page: [normalised lines]}, {page: {(form, label or gloss)}})."""
    lines, bits = collections.defaultdict(list), collections.defaultdict(set)
    for f in sorted(READINGS.glob(pattern)):
        for label, tile in json.loads(f.read_text(encoding="utf-8")).items():
            page = int(re.match(r"p(\d+)", label).group(1))
            for x in tile.get("forms", []):
                if not x:
                    continue
                line = norm_line(x[0])
                if " + " in line:
                    lines[page].append(line)
                    bits[page].update(pieces(line))
                else:                                   # one piece, its label or gloss in the second slot
                    gloss = norm_line(x[1]) if len(x) > 1 else ""
                    form, _, rest = line.partition(" ")
                    bits[page].add((form, (rest.strip().strip("'\"") or gloss.strip("'\"")).strip()))
    return lines, bits


def stored_lines(data):
    """Every breakdown of the stored chapter: (page, json path of the string, start, end, normalised line)."""
    out = []

    def walk(node, path, page):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [k], page)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [i], page)
        elif isinstance(node, str) and path and path[-1] == "content":
            text = unicodedata.normalize("NFC", node)
            glosses = [m.span() for m in GLOSS.finditer(text)]
            for m in re.finditer(r"<[^\n<]+", text):
                # cut where another example follows: at "; " outside a gloss, and at "cp."
                cuts = [m.start() + 1]
                for c in re.finditer(r";|\bcp\.", text[m.start():m.end()]):
                    at = m.start() + c.start()
                    if not any(g0 < at < g1 for g0, g1 in glosses):
                        cuts.append(at)
                cuts.append(m.end())
                for a, b in zip(cuts, cuts[1:]):
                    line = norm_line(text[a:b].lstrip(";"))
                    if " + " in line:
                        out.append((page, path, a, b, line))

    for name, node in data.items():
        walk(node, [name], int(name.split("_")[1]))
    return out


def same_but_for_print(a, b):
    """Differences that are the printer's or the copyist's, not the word's: spacing, ' for ʔ, a stray semicolon."""
    fold = lambda t: re.sub(r"\s+", "", t).replace("'", "ʔ").replace(";", "")
    return fold(a) == fold(b)


def grade_lines(data):
    """Pieces of stored breakdown lines that both readers have otherwise: [{..., "stored_piece", "piece"}], and what is left."""
    lines1, bits1 = reading_lines("chapter4_part*.json")
    lines2, bits2 = reading_lines("chapter4_second_part*.json")
    fixes, left, tally = [], [], collections.Counter()
    for page, path, a, b, line in stored_lines(data):
        tally["breakdown lines"] += 1
        pool = [x for q in (page, page - 1, page + 1) for x in lines1.get(q, [])]
        near2 = set().union(*[bits2.get(q, set()) for q in (page, page - 1, page + 1)])
        near1 = set().union(*[bits1.get(q, set()) for q in (page, page - 1, page + 1)])
        scored = [(difflib.SequenceMatcher(None, line, x, autojunk=False).ratio(), x) for x in pool]
        ratio, other = max(scored, default=(0.0, ""))
        if line == other:
            tally["as the first reader has it"] += 1
            continue
        if ratio < 0.8:
            tally["no such line in the first reading"] += 1
            continue
        mine, theirs = pieces(line), pieces(other)
        sm = difflib.SequenceMatcher(None, ["%s %s" % x for x in mine], ["%s %s" % x for x in theirs], autojunk=False)
        for op, i0, i1, j0, j1 in sm.get_opcodes():
            if op == "equal":
                continue
            if op != "replace" or i1 - i0 != j1 - j0:
                left.append({"page": page, "book_page": 28 + page, "stored": " + ".join("%s %s" % x for x in mine[i0:i1]).strip(),
                             "first_reading": " + ".join("%s %s" % x for x in theirs[j0:j1]).strip(), "line": line,
                             "why": "pieces added or missing: not judged"})
                continue
            for (sf, st), (rf, rt) in zip(mine[i0:i1], theirs[j0:j1]):
                if same_but_for_print("%s %s" % (sf, st), "%s %s" % (rf, rt)):
                    continue
                row = {"page": page, "book_page": 28 + page, "stored": ("%s %s" % (sf, st)).strip(),
                       "first_reading": ("%s %s" % (rf, rt)).strip(), "line": line}
                if not same_but_for_print(st, rt):
                    left.append(dict(row, why="the label or gloss differs: not judged"))
                elif (rf, rt) in near2 and (sf, st) not in near2 and (sf, st) not in near1:
                    fixes.append(dict(row, path=path, span=[a, b], stored_form=sf, form=rf, tag=st))
                else:
                    left.append(dict(row, why="the second reader does not have the first reader's piece" if (rf, rt) not in near2
                                     else "a reader has the stored piece as well"))
    tally["pieces both readers have otherwise"] = len(fixes)
    tally["left"] = len(left)
    return fixes, left, tally


def apply_lines(data, fixes):
    """Put the readers' form into the stored line. Returns the fixes that were made."""
    done = []
    by_string = collections.defaultdict(list)
    for f in fixes:
        by_string[tuple(f["path"])].append(f)
    for path, group in by_string.items():
        node = data
        for k in path[:-1]:
            node = node[k]
        text = unicodedata.normalize("NFC", node[path[-1]])
        # the same piece may stand twice in a line (two words, each with -Ø PERF): all of them, or none
        same = collections.defaultdict(list)
        for f in group:
            same[(f["span"][0], f["span"][1], f["stored_form"], f["tag"], f["form"])].append(f)
        for (a, b, old, tag, new), fs in sorted(same.items(), key=lambda kv: -kv[0][0]):   # from the end: earlier spans stay valid
            tag_rx = re.escape(tag).replace("'", "['‘’]")
            after = (r"\s+['‘’\"]?" + tag_rx) if tag else r"\s*(?:\+|;|\)|$)"
            pattern = re.compile(r"(?<![\wʔ:\-])" + re.escape(old) + "(?=" + after + ")")
            hits = list(pattern.finditer(text, a, b))
            if len(hits) != len(fs):
                for f in fs:
                    f["not_applied"] = "%d places in the line for %d corrections" % (len(hits), len(fs))
                continue
            for m in reversed(hits):
                text = text[:m.start()] + new + text[m.end():]
            done += fs
        node[path[-1]] = text
    return done


# ---------------------------------------------------------------------------------------------------------
# Places named one by one
# ---------------------------------------------------------------------------------------------------------

TABLE_17 = [
    ["Perfective/Imperfective", "Non-Intentive/Intentive/Habitual/Inchoative", "Non-Subordinate/Subordinate", "Suffixes"],
    ["Perfective", "Non-intentive", "Non-subordinate", "-Ø / -ʔ"],
    ["Perfective", "Non-intentive", "Non-subordinate", "-his (when incorporated)"],
    ["Perfective", "Non-intentive", "Subordinate", "Class I: -a"],
    ["Perfective", "Non-intentive", "Subordinate", "Class II: -i"],
    ["Perfective", "Non-intentive", "Subordinate", "Class III: final syllable change"],
    ["Perfective", "Non-intentive", "Subordinate", "Class IV: -Ø"],
    ["Perfective", "Intentive", "Non-subordinate", "-his + -ta"],
    ["Perfective", "Intentive", "Subordinate", "-his + -ta + -rit"],
    ["Imperfective", "Non-intentive", "Non-subordinate", "-:huʔ"],
    ["Imperfective", "Non-intentive", "Non-subordinate", "-:hus (when incorporated)"],
    ["Imperfective", "Non-intentive", "Subordinate", "-hu"],
    ["Imperfective", "Intentive", "Non-subordinate", "-:hus + -ta → -:husta"],
    ["Imperfective", "Intentive", "Subordinate", "-hus + -ta + -rit → -hustarit"],
    ["Imperfective", "Inchoative", "Non-subordinate", "-:hus + -itik → -:husitit"],
    ["Imperfective", "Inchoative", "Subordinate", "-hus + -itik → -husitit"],
    ["Imperfective", "Habitual", "Non-subordinate", "-:hus + -uukuʔ → -:husuukuʔ"],
    ["Imperfective", "Habitual", "Subordinate", "-hus + -uku → -husuku"],
]
T17 = ["page_17", "sections", 0]
# (what, json path, stored value, value as printed, [texts both readers must have on that page; spaces are ignored])
# A sixth member PART means the stored and the printed value are a part of the string at that path.
PART = "part of the string"
BY_HAND = [
    ("the breakdown of wiiraraʔu ends in the label alone; the stored copy had put a zero before it",
     ["page_18", "sections", 1, "content"], "raʔuk ‘make’ + Ø SUB.3", "raʔuk ‘make’ + SUB.3", ["raʔuk‘make’+SUB.3"], PART),
    ("Table 17 as both readers have it: the stored copy had merged the cells of -ʔ and -his and of -:huʔ and -:hus, had given "
     "the perfective a combined form -hustarit that the table does not print, and had lost the length mark of -:hus",
     T17 + ["tables", 0, "rows"], None, TABLE_17,
     ["Non-subordinate|-Ø/-ʔ", "-his(whenincorporated)", "Subordinate|-his+-ta+-rit", "Non-subordinate|-:huʔ", "-:hus(whenincorporated)",
      "-:hus+-ta|→|-:husta", "-hus+-ta+-rit|→|-hustarit", "-:hus+-itik|→|-:husitit", "-hus+-itik|→|-husitit",
      "-:hus+-uukuʔ|→|-:husuukuʔ", "-hus+-uku|→|-husuku"]),
    ("the summary of Table 17 made by the March 2026 extraction, brought in line with the table",
     T17 + ["morphemes_mentioned", 1, "notes"], "Occurs when incorporated in perfective, non-intentive, non-subordinate contexts.",
     "Beside -Ø in perfective, non-intentive, non-subordinate contexts. The form given for incorporation is -his.",
     ["Non-subordinate|-Ø/-ʔ", "-his(whenincorporated)"]),
    ("the same", T17 + ["morphemes_mentioned", 8, "notes"],
     "Combines with -his + -ta for perfective, intentive, subordinate forms, resulting in -hustarit. Combines with -hus + -ta for "
     "imperfective, intentive, subordinate forms, resulting in -hustarit.",
     "Combines with -his + -ta for perfective, intentive, subordinate forms. Combines with -hus + -ta for imperfective, intentive, "
     "subordinate forms, resulting in -hustarit.", ["Subordinate|-his+-ta+-rit", "-hus+-ta+-rit|→|-hustarit"]),
    ("the same", T17 + ["morphemes_mentioned", 9, "label"], "perfective/imperfective, intentive, subordinate",
     "imperfective, intentive, subordinate", ["-hus+-ta+-rit|→|-hustarit"]),
    ("the same", T17 + ["morphemes_mentioned", 9, "notes"],
     "Combined form of -his + -ta + -rit (perfective) or -hus + -ta + -rit (imperfective).", "Combined form of -hus + -ta + -rit.",
     ["-hus+-ta+-rit|→|-hustarit"]),
    ("the same", T17 + ["morphemes_mentioned", 10, "form"], "-huʔ", "-:huʔ", ["Non-subordinate|-:huʔ"]),
    ("the same", T17 + ["morphemes_mentioned", 10, "notes"],
     "Occurs when incorporated in imperfective, non-intentive, non-subordinate contexts.",
     "Occurs in imperfective, non-intentive, non-subordinate contexts. The form given for incorporation is -:hus. The colon "
     "stands for lengthening of the vowel before it.", ["Non-subordinate|-:huʔ", "-:hus(whenincorporated)"]),
    ("the same", T17 + ["morphemes_mentioned", 12, "notes"], "Combines with -ta, -itik, -uukuʔ, -uku for various imperfective categories.",
     "Combines with -ta, -itik, -uukuʔ, -uku for various imperfective categories. Table 17 gives it as -:hus in non-subordinate "
     "forms and as -hus in subordinate forms.", ["-:hus+-ta|→|-:husta", "-hus+-uku|→|-husuku"]),
    ("the same", T17 + ["morphemes_mentioned", 13, "form"], "-husta", "-:husta", ["-:hus+-ta|→|-:husta"]),
    ("the same", T17 + ["morphemes_mentioned", 13, "notes"], "Combined form of -hus + -ta.", "Combined form of -:hus + -ta.",
     ["-:hus+-ta|→|-:husta"]),
    ("the same", T17 + ["morphemes_mentioned", 14, "notes"],
     "Combines with -hus for imperfective, inchoative forms, resulting in -husitit.",
     "Combines with the imperfective suffix for inchoative forms: -:husitit non-subordinate, -husitit subordinate.",
     ["-:hus+-itik|→|-:husitit", "-hus+-itik|→|-husitit"]),
    ("the same", T17 + ["morphemes_mentioned", 15, "form"], "-husitit", "-:husitit / -husitit",
     ["-:hus+-itik|→|-:husitit", "-hus+-itik|→|-husitit"]),
    ("the same", T17 + ["morphemes_mentioned", 15, "notes"], "Combined form of -hus + -itik.",
     "Combined form of -:hus + -itik (non-subordinate) and of -hus + -itik (subordinate).",
     ["-:hus+-itik|→|-:husitit", "-hus+-itik|→|-husitit"]),
    ("the same", T17 + ["morphemes_mentioned", 16, "notes"],
     "Combines with -hus for imperfective, habitual, non-subordinate forms, resulting in -husuukuʔ.",
     "Combines with -:hus for imperfective, habitual, non-subordinate forms, resulting in -:husuukuʔ.", ["-:hus+-uukuʔ|→|-:husuukuʔ"]),
    ("the same", T17 + ["morphemes_mentioned", 17, "form"], "-husuukuʔ", "-:husuukuʔ", ["-:hus+-uukuʔ|→|-:husuukuʔ"]),
    ("the same", T17 + ["morphemes_mentioned", 17, "notes"], "Combined form of -hus + -uukuʔ.", "Combined form of -:hus + -uukuʔ.",
     ["-:hus+-uukuʔ|→|-:husuukuʔ"]),
    ("the non-subordinate imperfective is printed -:hus on this page, once, and nowhere as -hus",
     ["page_18", "sections", 2, "heading"], "Imperfective aspect (IMPF), non-subordinate: -hus",
     "Imperfective aspect (IMPF), non-subordinate: -:hus", ["-:hus"]),
    ("the same", ["page_18", "sections", 2, "morphemes_mentioned", 0, "form"], "-hus", "-:hus", ["-:hus"]),
    ("the breakdown of tiwaawaktiikusitit has -:hus",
     ["page_20", "sections", 1, "examples", 0, "breakdown", 3, "morpheme"], "-hus", "-:hus", ["waawaktik‘talk’-:husIMPF+-itikINCH"]),
    ("the imperfective row of the list of inchoative forms: -itik + -:hus gives -itiikuʔ",
     ["page_23", "sections", 0, "tables", 0, "rows", 4, 0], "-itik + -hus", "-itik + -:hus", ["-itik+-:hus|IMPF|→|-itiikuʔ"]),
    ("the same; the stored copy had a raised u for the last two letters",
     ["page_23", "sections", 0, "tables", 0, "rows", 4, 2], "-itiikᵘ", "-itiikuʔ", ["-itik+-:hus|IMPF|→|-itiikuʔ"]),
]


def squeezed(pattern):
    """Each page of a reading as one string without spaces: forms, then table rows with | between cells."""
    pages = collections.defaultdict(str)
    for f in sorted(READINGS.glob(pattern)):
        for label, tile in json.loads(f.read_text(encoding="utf-8")).items():
            page = int(re.match(r"p(\d+)", label).group(1))
            parts = [str(x[0]) for x in tile.get("forms", []) if x]
            for t in tile.get("tables", []):
                parts += ["|".join(str(c) for c in (row if isinstance(row, list) else [row])) for row in t.get("rows", [])]
            pages[page] += "\n" + "\n".join(re.sub(r"\s+", "", unicodedata.normalize("NFC", x)) for x in parts)
    return pages


def grade_by_hand(data):
    """BY_HAND against the stored chapter and both readings: [(entry, state)], state 'to do', 'done' or why not."""
    one, two = squeezed("chapter4_part*.json"), squeezed("chapter4_second_part*.json")
    out = []
    for entry in BY_HAND:
        what, path, old, new, evidence = entry[:5]
        part = len(entry) > 5 and entry[5] == PART
        page = int(path[0].split("_")[1])
        node = data
        try:
            for k in path:
                node = node[k]
        except (KeyError, IndexError, TypeError):
            out.append(((what, path, old, new, part), "the place is not in the stored chapter"))
            continue
        missing = [e for e in evidence if re.sub(r"\s+", "", e) not in one.get(page, "") or re.sub(r"\s+", "", e) not in two.get(page, "")]
        if part:
            done, there = (new in node and old not in node), node.count(old) == 1
        else:
            done, there = node == new, old is None or node == old
        if done:
            state = "done"
        elif missing:
            state = "not in both readings: %s" % missing
        elif not there:
            state = "the stored value is neither the old nor the new one"
        else:
            state = "to do"
        out.append(((what, path, old, new, part), state))
    return out


def apply_by_hand(data, graded):
    done = []
    for (what, path, old, new, part), state in graded:
        if state != "to do":
            continue
        node = data
        for k in path[:-1]:
            node = node[k]
        was = node[path[-1]]
        node[path[-1]] = was.replace(old, new) if part else new
        done.append({"what": what, "where": "/".join(str(k) for k in path),
                     "stored": old if part else was if isinstance(was, str) else "(the table's %d rows)" % len(was),
                     "now": new if isinstance(new, str) else "(the table's %d rows as both readers have them)" % len(new)})
    return done


def run(apply):
    rows, tally, readers = grade()
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    line_fixes, line_left, line_tally = grade_lines(data)
    hand = grade_by_hand(data)
    applied, applied_lines, applied_hand = [], [], []
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if apply:
        raw = CHAPTER.read_text(encoding="utf-8")
        for r in rows:
            if r["verdict"] != "both blind readings agree" or r["correct_to"] == r["stored"]:
                continue
            n = sum(replace_word(data[name], r["stored"], r["correct_to"]) for name in data if int(name.split("_")[1]) == r["page"])
            if n:
                applied.append({"page": r["page"], "book_page": r["book_page"], "stored": r["stored"], "now": r["correct_to"],
                                "placed_by": r["placed_by"], "strings_changed": n, "when": stamp})
        # the lines are judged again on the corrected words, so that a word is not counted twice
        line_fixes, line_left, line_tally = grade_lines(data)
        applied_lines = [{"page": f["page"], "book_page": f["book_page"], "stored": f["stored"], "now": ("%s %s" % (f["form"], f["tag"])).strip(),
                          "line": f["line"], "when": stamp} for f in apply_lines(data, line_fixes)]
        applied_hand = [dict(h, when=stamp) for h in apply_by_hand(data, grade_by_hand(data))]
        if applied or applied_lines or applied_hand:
            indent = 2 if raw.startswith("{\n  ") else 1 if raw.startswith("{\n ") else None
            CHAPTER.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
            before = rows
            rows, tally, readers = grade()
            data = json.loads(CHAPTER.read_text(encoding="utf-8"))
            line_fixes, line_left, line_tally = grade_lines(data)
            hand = grade_by_hand(data)
            done = {(a["page"], a["stored"]) for a in applied}
            rows = [dict(r, verdict="corrected", was=r["stored"]) for r in before if (r["page"], r["stored"]) in done] + rows
    previous = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {}
    if apply or not previous.get("applied"):
        record = {"made": stamp, "readers": readers, "tally": dict(tally), "breakdown_lines": dict(line_tally),
                  "applied": previous.get("applied", []) + applied,
                  "applied_in_breakdown_lines": previous.get("applied_in_breakdown_lines", []) + applied_lines,
                  "applied_by_hand": previous.get("applied_by_hand", []) + applied_hand,
                  "words": rows,
                  "breakdown_pieces_to_correct": [{k: v for k, v in f.items() if k not in ("path", "span")} for f in line_fixes],
                  "breakdown_pieces_left": line_left,
                  "places_named_one_by_one": [{"what": w, "where": "/".join(str(k) for k in pth), "state": st}
                                              for (w, pth, o, n, part), st in hand]}
        RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("stored words of the chapter: %d; %s" % (tally["words"], {k: v for k, v in tally.items() if k != "words"}))
    state.out("the two blind readings: %s" % readers)
    order = ["both blind readings agree", "corrected", "place not certain", "three different readings", "second reading has the stored word",
             "second reader differs", "in neither reading", "not a Skiri word"]
    for verdict in order:
        sel = [r for r in rows if r["verdict"] == verdict]
        if not sel:
            continue
        state.out("")
        state.out("%s (%d)" % (verdict, len(sel)))
        for r in sel:
            state.out("  p. %-3s %-28s first: %-28s second: %-28s%s" % (
                r["book_page"], r["stored"], r["first_reading"], r["second_reading"],
                ("  -> " + r["correct_to"] + "  [" + r["placed_by"] + "]") if r.get("correct_to") else ""))
    state.out("")
    state.out("breakdown lines: %s" % dict(line_tally))
    for f in line_fixes:
        state.out("  p. %-3s %-22s -> %-22s in: %s" % (f["book_page"], f["stored"], ("%s %s" % (f["form"], f["tag"])).strip(), f["line"][:110]))
    if line_left:
        state.out("  left (%d):" % len(line_left))
        for f in line_left:
            state.out("  p. %-3s %-30s first reader: %-30s %s" % (f["book_page"], f["stored"][:30], f["first_reading"][:30], f["why"]))
    state.out("")
    state.out("places named one by one: %s" % dict(collections.Counter(st.split(":")[0] for _, st in hand)))
    for (what, path, old, new, part), st in hand:
        if st not in ("done", "to do"):
            state.out("  %s: %s" % ("/".join(str(k) for k in path), st))
    state.out("")
    if apply:
        state.out("corrected in %s: %d words, %d pieces of breakdown lines, %d places named one by one" % (
            CHAPTER.name, len(applied), len(applied_lines), len(applied_hand)))
    else:
        state.out("nothing was changed in the chapter (use --apply)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheets", action="store_true", help="cut the tiles for the readers")
    ap.add_argument("--apply", action="store_true", help="correct the stored chapter where both blind readings agree")
    ap.add_argument("--zoom", nargs=5, metavar=("TILE", "X0", "Y0", "X1", "Y1"),
                    help="draw part of a tile larger; the corners are fractions of the tile (0 0 1 1 is all of it)")
    args = ap.parse_args()
    if args.zoom:
        zoom(args.zoom[0], *[float(v) for v in args.zoom[1:]])
    elif args.sheets:
        sheets()
    else:
        run(args.apply)


if __name__ == "__main__":
    main()
