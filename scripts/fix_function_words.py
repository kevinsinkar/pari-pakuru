#!/usr/bin/env python3
"""The function-word tables against the Blue Book as read from the scan.

Two tables hold words that an AI model took out of Blue Book phrases in March
2026, when the phrases were still OCR text:

  bb_function_words   63 rows: a word, its class and meaning, and the phrase
                      it was taken from
  function_words      418 rows then; 59 of them from the Blue Book (the rest
                      are dictionary entries and are not touched here)

The audit of 2026-11-13 read every Blue Book form from the scan and corrected
the phrases. The words taken out of them were corrected only where the
letters already agreed. This pass sets each word against what the scan reads.
It reads nothing new: a word is corrected only to a form that stands in the
Blue Book table, at the place the word was taken from.

bb_function_words. Each row names its phrase, and every phrase is a row of
the Blue Book table. The word becomes what the phrase prints at its place:

  * the word of the phrase it is (accents aside): written as printed;
  * the word of the phrase it is but for a final glottal stop the phrase does
    not print, or prints: written as printed;
  * a word the OCR had misread: the audit's reading of the same phrase has
    another word at that place, and that is the word;
  * a part of a word of the phrase, set off by the book's own bullet: written
    as printed, with the bullet on the side where the word goes on;
  * neither: the row is deleted. The letters stand in the phrase, but the book
    does not set them off as a word or as a part.

function_words, the rows from the Blue Book. A row stays if its headword is,
in the table's own spelling (small letters, no accent, ʔ for the apostrophe,
c for ts), a word or a bulleted part of a form of the Blue Book table. Forms
that still show OCR damage are not counted as evidence. Otherwise:

  * a leading dot is the OCR's reading of the bullet and is taken off;
  * a headword whose word in bb_function_words was corrected follows it;
  * a headword that the audit's reading of a phrase corrects, where the
    English of that phrase shares a word with the row's meaning, follows it;
  * a row that then repeats another row is deleted;
  * a row with no support is deleted, and so is the English word "or".

The meanings and classes in both tables are the extraction's. They are not
checked here; some are plainly wrong (a word glossed 'when' that is the
book's word for 'child'). No page shows these tables to a learner.

Usage:
    python scripts/fix_function_words.py            # lists what it would change; changes nothing
    python scripts/fix_function_words.py --apply    # backs up, writes, appends to the report, writes the dump
    python scripts/fix_function_words.py --check    # exit 0 if nothing is left to do
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_lesson_text_ocr import audit_pairs  # noqa: E402
from link_bb_vocab import content_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "function_words_pass_report.txt"

BULLET = "•"
OCR_BULLET = re.compile(r"\s\.\s?\w")            # " .x": the OCR's reading of a bullet; such a form is damaged
OCR_SPLIT = re.compile(r"\w\s'\w")                # "t 'ekah": a word the OCR split before its apostrophe
ENGLISH = {"or": "the English word between two forms the book lists (ar or ah; or kuh)"}


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def norm(text):
    """The table's own spelling of a word: small letters, no accent, ʔ for the apostrophe, c for ts, letters only."""
    s = "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch)).lower()
    s = s.replace("'", "ʔ").replace("’", "ʔ").replace("ts", "c")
    return re.sub(r"[^a-zʔ]", "", s)


def tokens(phrase):
    """The words of a phrase, without the punctuation around them."""
    return [t for t in (w.strip(".,?!;:()\"“”") for w in (phrase or "").split()) if t]


def pieces(token):
    """The parts of a word the book sets off: by its bullet, a hyphen, or the plus sign of an analysis line."""
    return [p for p in re.split(r"[%s+\-]" % BULLET, token) if p]


def printed_part(token, index):
    """Part number `index` of a word as printed, with the bullet on the side where the word goes on."""
    parts = re.split(r"([%s+\-])" % BULLET, token)
    names = [p for p in parts[::2]]
    kept = [i for i, p in enumerate(names) if p]
    i = kept[index]
    left = BULLET if i > 0 else ""
    right = BULLET if i < len(names) - 1 else ""
    return left + names[i] + right


def load(conn):
    forms = conn.execute("select id, bb_skiri_form, bb_english from blue_book_attestations "
                         "where bb_skiri_form is not null order by id").fetchall()
    words, parts = {}, {}
    for r in forms:
        if OCR_BULLET.search(r["bb_skiri_form"]) or OCR_SPLIT.search(r["bb_skiri_form"]):
            continue                            # still damaged: no evidence
        for tok in tokens(r["bb_skiri_form"]):
            words.setdefault(norm(tok), (tok, r["id"], r["bb_skiri_form"]))
            ps = pieces(tok)
            if len(ps) > 1 or tok != ps[0] if ps else False:
                for p in ps:
                    parts.setdefault(norm(p), (p, r["id"], r["bb_skiri_form"]))
    by_form = {}
    for r in forms:
        by_form.setdefault(r["bb_skiri_form"], r)
    return forms, words, parts, by_form


def place_in(word, phrase):
    """Where a word stands in a phrase: ("word", i, printed), ("glottal", i, printed), ("part", (i, j), printed) or None."""
    w = norm(word)
    toks = tokens(phrase)
    for i, t in enumerate(toks):
        if norm(t) == w:
            return "word", i, t
    for i, t in enumerate(toks):
        if norm(t).rstrip("ʔ") == w.rstrip("ʔ"):
            return "glottal", i, t
    for i, t in enumerate(toks):
        ps = pieces(t)
        if len(ps) < 2:
            continue
        for j, part in enumerate(ps):
            if norm(part) == w or norm(part).rstrip("ʔ") == w.rstrip("ʔ"):
                return "part", (i, j), printed_part(t, j)
    return None


def plan_bb(conn, pairs):
    """bb_function_words: (id, old word, new word or None, new normalized word, why)."""
    older = {}                                   # the audit's reading -> the OCR readings it replaced
    for old, (new, _pages) in pairs.items():
        older.setdefault(new, []).append(old)
    changes = []
    for r in conn.execute("select id, word, normalized_word, source_phrase from bb_function_words order by id"):
        phrase = r["source_phrase"] or ""
        found = place_in(r["word"], phrase)
        new, why = None, None
        if found:
            kind, _where, printed = found
            new = printed
            why = {"word": "the word of its phrase, as printed",
                   "glottal": "the word of its phrase; the phrase prints it %s the glottal stop" % (
                       "with" if norm(printed).endswith("ʔ") else "without"),
                   "part": "a part of a word of its phrase, as the book sets it off"}[kind]
        else:
            for old_phrase in older.get(phrase, []):
                # the OCR wrote the bullet as " ." and so split a word in two: put it together before counting
                old_toks = tokens(OCR_BULLET.sub(lambda m: BULLET + m.group(0)[-1], old_phrase))
                new_toks = tokens(phrase)
                hits = [i for i, t in enumerate(old_toks) if norm(t) == norm(r["word"])]
                if len(old_toks) == len(new_toks) and len(hits) == 1:
                    new = new_toks[hits[0]]
                    why = "the OCR read %s here; the audit reads %s (%s -> %s)" % (
                        old_toks[hits[0]], new, old_phrase, phrase)
                    break
        if new is None:
            changes.append((r["id"], r["word"], None, None,
                            "its letters stand in %s, but not as a word or a part the book sets off" % phrase))
        elif new != r["word"] or norm(new) != (r["normalized_word"] or ""):
            changes.append((r["id"], r["word"], new, norm(new), why))
    return changes


def plan_fw(conn, pairs, words, parts, by_form, bb_changes):
    """function_words rows from the Blue Book: (id, headword, new headword or None, why)."""
    rows = conn.execute("select id, headword, usage_notes from function_words where source like 'blue_book%' "
                        "order by id").fetchall()
    others = {r[0] for r in conn.execute("select headword from function_words where source not like 'blue_book%'")}
    follows = {}                                 # stored word (normalised) -> the corrected word (normalised)
    for _id, old, new, new_norm, _why in bb_changes:
        if new and norm(old) != new_norm:
            follows[norm(old)] = new_norm
    result, taken = [], set()
    for r in rows:
        head = r["headword"]
        key = norm(head)
        new, why = head, None
        if head in ENGLISH:
            result.append((r["id"], head, None, ENGLISH[head]))
            continue
        if head.startswith("."):
            new, why = head.lstrip("."), "the leading dot was the OCR's reading of the bullet"
        if key in words or key in parts:
            pass                                 # supported as it is
        elif key in follows:
            new, why = follows[key], "its word in bb_function_words was corrected from the scan"
        else:
            traced = set()
            for old_phrase, (new_phrase, _pages) in pairs.items():
                old_ps = [p for t in tokens(OCR_BULLET.sub(lambda m: BULLET + m.group(0)[-1], old_phrase)) for p in pieces(t)]
                new_ps = [p for t in tokens(new_phrase) for p in pieces(t)]
                if len(old_ps) != len(new_ps):
                    continue
                english = (by_form.get(new_phrase) or {"bb_english": ""})["bb_english"]
                for a, b in zip(old_ps, new_ps):
                    if norm(a) == key and content_words(english) & content_words(r["usage_notes"]):
                        traced.add((norm(b), old_phrase, new_phrase))
            if len({t[0] for t in traced}) == 1:
                t = sorted(traced)[0]
                new, why = t[0], "the OCR's reading in %s; the audit reads %s" % (t[1], t[2])
            else:
                result.append((r["id"], head, None, "no form of the Blue Book table has it as a word or a part"))
                continue
        new_key = norm(new)
        if new_key not in words and new_key not in parts:
            result.append((r["id"], head, None, "no form of the Blue Book table has %s as a word or a part" % new))
            continue
        if new in taken or new in others or (new != head and any(x["headword"] == new for x in rows)):
            result.append((r["id"], head, None, "the same as the row %s once corrected" % new))
            continue
        taken.add(new)
        if new != head:
            result.append((r["id"], head, new, why))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: list them only)")
    ap.add_argument("--check", action="store_true", help="exit 0 if nothing is left to do")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    pairs = audit_pairs()
    _forms, words, parts, by_form = load(conn)
    bb = plan_bb(conn, pairs)
    fw = plan_fw(conn, pairs, words, parts, by_form, bb)
    n_bb = conn.execute("select count(*) from bb_function_words").fetchone()[0]
    n_fw = conn.execute("select count(*) from function_words where source like 'blue_book%'").fetchone()[0]
    conn.close()

    if args.check:
        if bb or fw:
            out("NOT in step: %d rows of bb_function_words and %d Blue Book rows of function_words do not follow "
                "the scan's readings" % (len(bb), len(fw)))
            return 1
        out("function words in step with the scan: all %d rows of bb_function_words hold the word their phrase "
            "prints; all %d Blue Book rows of function_words are a word or a bulleted part of a form of the Blue "
            "Book table" % (n_bb, n_fw))
        return 0

    header = ["fix_function_words — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "bb_function_words: %d rows; to correct %d, to delete %d" % (
                  n_bb, sum(1 for c in bb if c[2]), sum(1 for c in bb if not c[2])),
              "function_words, rows from the Blue Book: %d; to correct %d, to delete %d" % (
                  n_fw, sum(1 for c in fw if c[2]), sum(1 for c in fw if not c[2]))]
    body = ["", "== bb_function_words (row: word -> word as the phrase prints it; why)"]
    body += ["  %-4d %-12s -> %-14s %s" % (c[0], c[1], c[2] if c[2] else "(deleted)", c[4]) for c in bb]
    body += ["", "== function_words, rows from the Blue Book (row: headword -> headword; why)"]
    body += ["  %-4d %-12s -> %-12s %s" % (c[0], c[1], c[2] if c[2] else "(deleted)", c[3]) for c in fw]
    if not args.apply:
        out("\n".join(header + body))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("skiri_pawnee_backup_%s_function_words.db" % stamp)
    shutil.copy2(DB, backup)
    conn = sqlite3.connect(str(DB))
    for rid, old, new, new_norm, _why in bb:
        if new:
            conn.execute("update bb_function_words set word = ?, normalized_word = ? where id = ? and word = ?",
                         (new, new_norm, rid, old))
        else:
            conn.execute("delete from bb_function_words where id = ? and word = ?", (rid, old))
    for rid, old, new, _why in fw:
        if new:
            conn.execute("update function_words set headword = ? where id = ? and headword = ?", (new, rid, old))
        else:
            conn.execute("delete from function_words where id = ? and headword = ?", (rid, old))
    conn.commit()
    conn.close()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    header += ["", "written. backup: OneDrive/pari_pakuru_backups/%s" % backup.name]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
