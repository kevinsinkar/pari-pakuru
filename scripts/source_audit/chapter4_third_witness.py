#!/usr/bin/env python3
"""
The grammar chapter's doubtful words, weighed against the dictionary (2026-11-14)
================================================================================

The audit left 51 words of the stored grammar chapter (Chapter 4) that differ
from what the blind reader saw on the page. Stored text and blind reading are
one reading each, so neither settles the other. The dictionary can act as a
third witness for some of them: its forms are checked against the PDF's text
layer, letter for letter, and many words the chapter cites are dictionary
forms.

    python scripts/source_audit/chapter4_third_witness.py           # the verdicts; writes chapter4_third_witness.json
    python scripts/source_audit/chapter4_third_witness.py --apply   # also corrects the words listed in SETTLED

Verdicts
    reader and dictionary agree     the reader's form is a form the dictionary prints, the stored form is
                                    printed nowhere in the dictionary, and the chapter does not hold the
                                    reader's form as another word on that page
    stored form is a dictionary form   and the reader's is not: the reader slipped, the stored word stands
    open                            everything else: for a person with the page, or a second blind reading

Only differences in letters are corrected from the first verdict. Where the
stored word differs from the dictionary form in an accent mark or a final
glottal stop it is left open: the chapter may print an accent or an
underlying form that the dictionary's headword does not have.
"""
import argparse
import collections
import datetime as dt
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chapters_compare as cc4  # noqa: E402
import state  # noqa: E402

CHAPTER = state.ROOT / "extracted_data" / "grammatical_overview.json"
TOKEN = re.compile(r"[^\s,;:.!?()\[\]{}<>/+•\"=]+")
# (page of the chapter's JSON, stored word, word on the page) -- reader and dictionary agree, letters only
SETTLED = [
    (2, "askatahciruʔ", "askatahciriʔ"),
    (21, "iriirapahaattu", "iriirapahaatu"),
    (22, "tuciraahawista", "tuctiraahawista"),
]


def dictionary_forms(conn):
    forms = set()

    def add(text):
        for m in TOKEN.finditer(unicodedata.normalize("NFC", text or "")):
            forms.add(cc4.key(m.group(0).strip("'’")))
    for (v,) in conn.execute("select headword from lexical_entries where coalesce(source, '') != 'blue_book'"):
        add(v)
    for (v,) in conn.execute("select skiri_form from paradigmatic_forms"):
        add(v)
    for (v,) in conn.execute("select skiri_text from examples where coalesce(source, 'parks_dictionary') = 'parks_dictionary'"):
        add(v)
    for (v,) in conn.execute("select stem_form from derived_stems"):
        add(v)
    for (v,) in conn.execute("select additional_forms from lexical_entries where additional_forms is not null"):
        for f in json.loads(v):
            if isinstance(f, dict):
                add(f.get("form"))
    return forms


def verdicts():
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    known = dictionary_forms(conn)
    stored = json.loads(CHAPTER.read_text(encoding="utf-8"))
    pages = {}
    for name, page in stored.items():
        found = []
        cc4.walk(page, [], found)
        pages[int(name.split("_")[1])] = {cc4.key(t) for t, where in found}
    rows = json.loads((state.OUT / "chapter4_differences.json").read_text(encoding="utf-8"))["differences"]
    out, seen = [], set()
    for r in rows:
        if r["kind"] not in ("differs", "not-found", "b-for-h and more"):
            continue
        s, b, page = cc4.key(r["stored"]), r["blind_reading"], r["page"]
        if (s, b, page) in seen:
            continue
        seen.add((s, b, page))
        near = set()
        for p in (page - 1, page, page + 1):
            near |= pages.get(p, set())
        if s not in near:
            verdict = "corrected since the audit"
        elif len(s) < 4 or not b:
            verdict = "open"
        elif b in known and s not in known and b not in near:
            verdict = "reader and dictionary agree"
        elif s in known and b not in known:
            verdict = "stored form is a dictionary form"
        else:
            verdict = "open"
        out.append({"page": page, "book_page": 28 + page, "stored": r["stored"], "blind_reading": b, "kind": r["kind"],
                    "stored_is_dictionary_form": s in known, "reading_is_dictionary_form": bool(b) and b in known,
                    "reading_is_another_word_of_the_page": bool(b) and b in near, "verdict": verdict})
    return out


def replace_word(node, old, new):
    """Replace old by new where it stands as a whole word, in every string under node."""
    pattern = re.compile(r"(?<![A-Za-zʔ])%s(?![A-Za-zʔ])" % re.escape(old))
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="correct the words listed in SETTLED in the stored chapter")
    args = ap.parse_args()
    rows = verdicts()
    tally = collections.Counter(r["verdict"] for r in rows)
    agree = {(r["page"], r["stored"], r["blind_reading"]) for r in rows if r["verdict"] == "reader and dictionary agree"}
    applied = []
    if args.apply:
        raw = CHAPTER.read_text(encoding="utf-8")
        data = json.loads(raw)
        for page, old, new in SETTLED:
            if (page, old, new) not in agree:
                state.out("not applied (the verdict no longer holds): page %d %s -> %s" % (page, old, new))
                continue
            n = sum(replace_word(data[name], old, new) for name in data if int(name.split("_")[1]) == page)
            if n:
                applied.append({"page": page, "stored": old, "now": new, "strings_changed": n})
        if applied:
            indent = 2 if raw.startswith("{\n  ") else 1 if raw.startswith("{\n ") else None
            CHAPTER.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
            rows = verdicts()
            tally = collections.Counter(r["verdict"] for r in rows)
    path = state.OUT / "chapter4_third_witness.json"
    previous = json.loads(path.read_text(encoding="utf-8")).get("applied", []) if path.exists() else []
    record = {"made": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "tally": dict(tally),
              "applied": previous + [dict(a, when=dt.datetime.now().strftime("%Y-%m-%d %H:%M")) for a in applied], "words": rows}
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("doubtful words of the chapter: %d; %s" % (len(rows), dict(tally)))
    for r in rows:
        if r["verdict"] != "open":
            state.out("  p. %-3s %-26s reader: %-26s %s" % (r["book_page"], r["stored"], r["blind_reading"], r["verdict"]))
    if args.apply:
        state.out("corrected in %s: %s" % (CHAPTER.name, applied or "nothing"))
    else:
        state.out("nothing was changed in the chapter (use --apply for the words listed in SETTLED)")


if __name__ == "__main__":
    main()
