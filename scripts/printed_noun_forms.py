#!/usr/bin/env python3
"""What Parks and the Blue Book print of a noun. Nothing here is computed.

This replaces the possession engine, withdrawn on 2026-11-14 (engines review,
decision 7). The engine computed "my / your / his" and case forms for every
noun; for 1,671 of 1,706 nouns its answer began with *kti*, an OCR slip, and
its locatives agreed with 44% of the forms Parks prints. The printed forms
were in the database all along. For a noun entry, lookup() returns:

  kin        the row or rows of Parks's Appendix 3 (table kinship_paradigms)
             for this kin term: "my", "your", "his/her" as printed
  case       the one-word examples printed in the entry that end in -kat,
             -hiriʔ or -ru, each with Parks's translation (Table 4 of the
             Grammatical Overview: -kat and -ru mark a place, -hiriʔ a place
             or a means)
  combining  the combining forms printed in the entry
  blue_book  Blue Book words linked to the entry whose English begins with
             my, your, his or her, as read from the scan

Every form returned is a value of a table that holds copied forms, and each
comes with its source. Where nothing is printed, nothing is returned: no form
is made up to fill the gap.

How an Appendix 3 row is tied to an entry (the tie is stated with the row):
  "form"      the entry's headword is one of the forms, or the stem, printed
              in the row;
  "relation"  the entry is a kin term (class N-KIN) and its first gloss
              names the relation the row is listed under (the bound stem
              -saas- 'mother' gets the row for 'mother'). This says only that
              Appendix 3 lists these forms for that relation; it does not say
              that the stem is in each of them.

Usage:
    python scripts/printed_noun_forms.py --entry SK-paksuq-p110-2116
    python scripts/printed_noun_forms.py --check
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"

NOUN_CLASSES = ("N", "N-DEP", "N-KIN", "NUM")
CASE_ENDING = re.compile(r"(sukat|kat|hiriʔ|iriʔ|wiru|ru)$")
POSSESSOR = re.compile(r"(my|your|his|her) ", re.I)
# Blue Book links made by the exact form; links by a shared beginning ("prefix", "loose") are not shown here
SOUND_LINKS = ("exact_normalized", "orthographic", "bb_only_form_and_english")
KIN_WORDS = ("grandmother", "grandfather", "grandchild", "mother", "father", "nephew", "niece", "brother",
             "sister", "sibling")


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def connect(db=DB):
    conn = sqlite3.connect("file:%s?mode=ro" % Path(db).resolve().as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _kin_words(text):
    """The kin words in an English term, longest first so that 'grandmother' is not also 'mother'."""
    found, rest = set(), (text or "").lower()
    for word in KIN_WORDS:
        if re.search(r"\b%s" % word, rest):
            found.add(word)
            rest = re.sub(r"\b%s\w*" % word, " ", rest)
    return found


def kin_rows(conn, entry):
    """Rows of Appendix 3 for this entry, each with the reason it is shown."""
    alternates = {a.strip() for a in re.split(r",\s*", entry["headword"] or "") if a.strip()}
    first_gloss = conn.execute("select definition from glosses where entry_id = ? order by sense_number limit 1",
                               (entry["entry_id"],)).fetchone()
    relation = _kin_words(re.split(r"[;(]", first_gloss[0])[0]) if first_gloss and first_gloss[0] else set()
    relation_whole = _kin_words(first_gloss[0]) if first_gloss and first_gloss[0] else set()
    by_form, by_relation = [], []
    for r in conn.execute("select english_term, stem, form_1sg, form_2sg, form_3sg, vocative, notes "
                          "from kinship_paradigms where source = 'appendix3' order by rowid"):
        forms = {f for f in (r["form_1sg"], r["form_2sg"], r["form_3sg"], r["vocative"]) if f}
        stems = {s.strip().strip("-") for s in re.split(r",\s*", r["stem"] or "") if s.strip()}
        row = {"relation": r["english_term"], "stem": r["stem"], "my": r["form_1sg"], "your": r["form_2sg"],
               "his_her": r["form_3sg"], "notes": r["notes"], "source": "Parks, Appendix 3"}
        if alternates & forms or {a.strip("-") for a in alternates} & stems:
            by_form.append(dict(row, tie="form"))
        elif entry["grammatical_class"] == "N-KIN":
            wanted = _kin_words(r["english_term"])
            if wanted and wanted in (relation, relation_whole):
                by_relation.append(dict(row, tie="relation"))
    # a headword that Appendix 3 itself prints needs no second tie; the tie by relation is for the bound stems
    return by_form or by_relation


def case_forms(conn, entry_id):
    """One-word examples of the entry that end in a case suffix, as printed, with Parks's translation.

    The same definition as the engines review's test set noun_case_examples.
    """
    rows = []
    for r in conn.execute("select id, skiri_text, english_translation from examples "
                          "where entry_id = ? and source = 'parks_dictionary' and skiri_text is not null order by id",
                          (entry_id,)):
        words = [w.strip().rstrip(".") for w in re.split(r"[,;]\s*", r["skiri_text"].strip()) if w.strip()]
        for w in words:
            if " " in w or len(w) < 5:
                continue
            m = CASE_ENDING.search(w)
            if not m:
                continue
            ending = m.group(1)
            rows.append({"form": w, "translation": (r["english_translation"] or "").strip(),
                         "ending": "-kat" if ending.endswith("kat") else ("-ru" if ending.endswith("ru") else "-hiriʔ"),
                         "example_id": r["id"], "source": "Parks, example in this entry"})
    return rows


def combining_forms(entry):
    try:
        forms = json.loads(entry["additional_forms"]) if entry["additional_forms"] else []
    except (TypeError, ValueError):
        return []
    return [{"form": f.get("form"), "source": "Parks, combining form printed in this entry"}
            for f in forms if isinstance(f, dict) and f.get("form") and "comb" in (f.get("form_type") or "")]


def blue_book_lines(conn, entry_id):
    rows = []
    marks = ",".join("?" * len(SOUND_LINKS))
    for r in conn.execute("select id, bb_skiri_form, bb_english, lesson_number, page_number from blue_book_attestations "
                          "where entry_id = ? and match_type in (%s) and bb_skiri_form is not null order by id" % marks,
                          (entry_id,) + SOUND_LINKS):
        english = (r["bb_english"] or "").strip()
        if POSSESSOR.match(english):
            rows.append({"form": r["bb_skiri_form"], "english": english, "lesson": r["lesson_number"],
                         "book_page": (r["page_number"] - 28) if r["page_number"] else None, "row": r["id"],
                         "source": "Blue Book, lesson %s" % r["lesson_number"]})
    return rows


def lookup(conn, entry_id):
    """Everything printed of this noun, or None if the entry is not a noun."""
    entry = conn.execute("select entry_id, headword, grammatical_class, additional_forms from lexical_entries "
                         "where entry_id = ?", (entry_id,)).fetchone()
    if entry is None or entry["grammatical_class"] not in NOUN_CLASSES:
        return None
    found = {"kin": kin_rows(conn, entry), "case": case_forms(conn, entry_id),
             "combining": combining_forms(entry), "blue_book": blue_book_lines(conn, entry_id)}
    found["anything"] = any(found[k] for k in ("kin", "case", "combining", "blue_book"))
    return found


def check(conn):
    """Counts, and the properties the box rests on. Returns the number of problems."""
    problems = []
    nouns = conn.execute("select entry_id, headword, grammatical_class from lexical_entries "
                         "where grammatical_class in (%s)" % ",".join("?" * len(NOUN_CLASSES)), NOUN_CLASSES).fetchall()
    with_ = {"kin": 0, "case": 0, "combining": 0, "blue_book": 0, "anything": 0}
    totals = {"kin": 0, "case": 0, "combining": 0, "blue_book": 0}
    kin_without = []
    rows_used = set()
    for n in nouns:
        found = lookup(conn, n["entry_id"])
        for k in totals:
            totals[k] += len(found[k])
            with_[k] += bool(found[k])
        with_["anything"] += found["anything"]
        if n["grammatical_class"] == "N-KIN" and not found["kin"]:
            kin_without.append(n["headword"])
        rows_used.update(r["relation"] for r in found["kin"])
        for c in found["case"]:        # a case form must be a word of an example printed in that very entry
            hit = conn.execute("select 1 from examples where id = ? and entry_id = ? and instr(skiri_text, ?) > 0",
                               (c["example_id"], n["entry_id"], c["form"])).fetchone()
            if not hit:
                problems.append("case form %s of %s is not in its example" % (c["form"], n["headword"]))
        for b in found["blue_book"]:   # a Blue Book line must be a row linked to that very entry
            hit = conn.execute("select 1 from blue_book_attestations where id = ? and entry_id = ? and bb_skiri_form = ?",
                               (b["row"], n["entry_id"], b["form"])).fetchone()
            if not hit:
                problems.append("Blue Book form %s of %s is not a row of that entry" % (b["form"], n["headword"]))
    other = conn.execute("select count(*) from kinship_paradigms where source != 'appendix3'").fetchone()[0]
    if other:
        problems.append("%d rows of kinship_paradigms are not from Appendix 3" % other)
    all_rows = {r[0] for r in conn.execute("select english_term from kinship_paradigms where source = 'appendix3'")}
    if all_rows - rows_used:
        problems.append("Appendix 3 rows shown on no entry: %s" % sorted(all_rows - rows_used))
    if kin_without:
        problems.append("kin terms (N-KIN) with no Appendix 3 row: %s" % kin_without)
    testset = ROOT / "reports" / "engines_review" / "data" / "testsets" / "noun_case_examples.jsonl"
    if testset.exists():
        recorded = sum(1 for line in testset.read_text(encoding="utf-8").splitlines() if line.strip())
        if recorded != totals["case"]:
            problems.append("case forms found: %d; the review's test set has %d" % (totals["case"], recorded))
    out("noun entries: %d; with something printed: %d" % (len(nouns), with_["anything"]))
    out("  Appendix 3 rows shown:        %4d on %4d entries (all %d rows of the table are shown somewhere)" % (
        totals["kin"], with_["kin"], len(all_rows)))
    out("  case forms printed in entry:  %4d on %4d entries" % (totals["case"], with_["case"]))
    out("  combining forms:              %4d on %4d entries" % (totals["combining"], with_["combining"]))
    out("  Blue Book possessed forms:    %4d on %4d entries" % (totals["blue_book"], with_["blue_book"]))
    for line in problems:
        out("PROBLEM: " + line)
    if not problems:
        out("every form shown is a value of a table of copied forms, in the entry it is shown on; nothing is computed")
    return len(problems)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entry", help="print what is printed of this noun entry")
    ap.add_argument("--check", action="store_true", help="counts and checks; exit 1 on a problem")
    args = ap.parse_args()
    conn = connect()
    if args.entry:
        found = lookup(conn, args.entry)
        out(json.dumps(found, ensure_ascii=False, indent=2) if found is not None else "not a noun entry")
        return 0
    if args.check:
        return 1 if check(conn) else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
