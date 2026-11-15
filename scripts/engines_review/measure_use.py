#!/usr/bin/env python3
"""Stage 2: the sentence templates, and what each engine is actually used for.

    python scripts/engines_review/measure_use.py

1. Sentence templates
   a. Does the engine recognise a sentence the Blue Book prints? Every printed
      dialogue line, phrase and grammar example is handed to the engine's own
      find_bb_attestation, once as printed and once without its accent marks
      (which is how the engine's own words are typed).
   b. The frame "noun + ti + descriptive verb": the verb the frame writes
      against the form 2 Parks prints for the same verb.
   c. A verb chosen in the sentence builder: the seven verbs of Appendix 1,
      asked for through their dictionary entries as the page does, against the
      printed cells (I / you / he-she, statement and question form).
   d. A verb is passed to the engine by its spelling alone: how many verbs
      share their spelling with another verb.
2. The entry pages: Parks's own example sentences that the app hides, because
   it keeps an example only when the headword, or the stem the possession
   engine cuts from it, begins a word of the sentence.
3. The lesson pages of the public site: forms that the audit corrected as OCR
   slips in the Blue Book table and that still stand in the lessons' running text.

Reads only. The app's own functions are called on a temporary copy of the
database. Writes data/use_*.jsonl and data/use_summary.json.
"""
import logging
import os
import re
import shutil
import sqlite3
import tempfile
from collections import Counter, defaultdict

from common import (DATA, DB_PATH, EXTRACTED, ROOT, TESTSETS, classify, classify_one, clean, connect, load_json, out,
                    pct, read_jsonl, strip_accents, variants, write_json, write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

logging.disable(logging.CRITICAL)


def temp_copy():
    folder = tempfile.mkdtemp(prefix="engines_review_")
    path = os.path.join(folder, "skiri_pawnee_copy.db")
    shutil.copyfile(DB_PATH, path)
    return folder, path


# ---------------------------------------------------------------------------
# 1. Sentence templates
# ---------------------------------------------------------------------------

def recognises_printed_sentences(db_copy):
    os.environ["SKIRI_DB_PATH"] = db_copy
    import sentence_templates as st
    st.DB_PATH = db_copy
    conn = sqlite3.connect("file:%s?mode=ro" % db_copy.replace("\\", "/"), uri=True)
    conn.row_factory = sqlite3.Row
    rows = []
    for s in read_jsonl(TESTSETS / "blue_book_sentences.jsonl"):
        printed = s["printed"]
        typed = strip_accents(printed)
        rows.append({"printed": printed, "lesson": s["lesson"],
                     "has_an_accent": typed != printed,
                     "found_as_printed": bool(st.find_bb_attestation(conn, printed)),
                     "found_without_its_accents": bool(st.find_bb_attestation(conn, typed))})
    conn.close()
    return rows


def frame_t2():
    """T2 writes 'ti' and the dictionary stem. Parks prints form 2 for the same verb."""
    rows = []
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        if f["form_number"] != 2 or (f["grammatical_class"] or "").split(",")[0].strip() != "VD":
            continue
        if f["stem_preverb"]:
            continue                      # the frame has no place for a preverb; counted apart below
        stem = variants(f["headword"])[0] if variants(f["headword"]) else f["headword"]
        cause, compared = classify("ti" + stem, f["variants"])
        rows.append({"headword": f["headword"], "frame_writes": "ti " + stem, "parks_form_2": f["printed"], "cause": cause})
    with_preverb = sum(1 for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl")
                       if f["form_number"] == 2 and (f["grammatical_class"] or "").split(",")[0].strip() == "VD"
                       and f["stem_preverb"])
    return rows, with_preverb


APPENDIX_VERBS_IN_THE_DICTIONARY = {   # verb of Appendix 1 -> headword of its dictionary entry (found by its form 2)
    "to come": "a", "to do it": "aar", "to go": "at", "to be good": "hiir",
    "to drink it": "kiikaa", "to be sick": "kiraawa/waahc", "to have it": "raah",
}


def builder_on_appendix_verbs(db_copy):
    import sentence_templates as st
    conn = sqlite3.connect("file:%s?mode=ro" % db_copy.replace("\\", "/"), uri=True)
    conn.row_factory = sqlite3.Row
    data = load_json(EXTRACTED / "appendix1_conjugations.json")
    by_gloss = {v["english_gloss"]: v for v in data.values()}
    rows = []
    for gloss, headword in APPENDIX_VERBS_IN_THE_DICTIONARY.items():
        modes = by_gloss[gloss]["modes"]
        for mode_key, mode, cellname in (("indicative_perfective", "ind", "statement"),
                                         ("absolutive_perfective", "abs", "question form")):
            for person in ("1sg", "2sg", "3sg"):
                printed = modes[mode_key][person]["skiri"]
                res = st.resolve_verb_form(conn, headword, person=person, tense="past", mode=mode)
                got = res.get("form")
                entry = res.get("entry_id")
                if got:
                    cause = min((classify_one(got, strip_accents(v)) for v in variants(printed)),
                                key=lambda c: (c != "exact", c))
                else:
                    cause = "no form produced"
                rows.append({"verb": gloss, "asked_for": headword, "cell": "%s, %s" % (person, cellname),
                             "printed": printed, "builder_gives": got, "entry_used": entry,
                             "marked_derived": res.get("derived"), "error": res.get("error"), "cause": cause})
    conn.close()
    return rows


def verbs_sharing_a_spelling(conn):
    rows = conn.execute("""select le.headword, count(distinct le.entry_id) n
                           from lexical_entries le join paradigmatic_forms pf using(entry_id)
                           where le.grammatical_class like 'V%' group by le.headword having n > 1""").fetchall()
    total = conn.execute("select count(distinct entry_id) from paradigmatic_forms").fetchone()[0]
    return {"verbs_with_forms": total, "spellings_shared_by_several_verbs": len(rows),
            "verb_entries_with_a_shared_spelling": sum(r["n"] for r in rows),
            "examples": [r["headword"] for r in rows[:15]]}


# ---------------------------------------------------------------------------
# 2. Parks's examples hidden on entry pages
# ---------------------------------------------------------------------------

def hidden_examples(db_copy):
    import sys
    sys.path.insert(0, str(ROOT))
    from web import app as webapp
    from web.db import SkiriWebDictionary
    from scripts.example_filter import matches_headword
    webapp.DATABASE = db_copy
    webapp.app.config["DATABASE"] = db_copy
    webapp._headword_set_cache = None
    hw_set = webapp._get_headword_set()
    db = SkiriWebDictionary(db_copy)
    conn = db.conn
    ids = [r[0] for r in conn.execute("select distinct entry_id from examples where skiri_text is not null and skiri_text != ''")]
    rows = []
    for eid in ids:
        data = db.build_full_entry(eid)
        if not data or not data.get("entry"):
            continue
        entry = data["entry"]
        before = list(entry.examples or [])
        texts_before = [getattr(e, "skiri_text", "") for e in before]
        # what the page would show
        webapp._filter_entry_examples(data)
        after = [getattr(e, "skiri_text", "") for e in (entry.examples or [])]
        # the same test without the stem the possession engine cuts: does the stem change anything?
        kept_without_stem = [t for t in texts_before if not t or matches_headword(entry.headword, t, hw_set, stem=None)]
        rows.append({"entry_id": eid, "headword": entry.headword, "class": entry.grammatical_class,
                     "examples_printed": len(texts_before), "examples_shown": len(after),
                     "shown_only_because_of_the_stem": len(after) - len(kept_without_stem)})
    db.close()
    return rows


# ---------------------------------------------------------------------------
# 3. OCR slips left in the lessons' running text
# ---------------------------------------------------------------------------

def lesson_slips(conn):
    """Old -> new pairs the audit recorded as 'OCR slip corrected', still found in the lessons."""
    report = (ROOT / "reports" / "source_audit_2026-11" / "bluebook_applied_report.txt").read_text(encoding="utf-8")
    pairs = {}
    for m in re.finditer(r"^\s*p\. (\d+)\s+OCR slip corrected\s+(.+?) -> (.+?)\s*$", report, flags=re.M):
        old, new = m.group(2).strip(), m.group(3).strip()
        if len(old) >= 6 and old != new:
            pairs[old] = (new, int(m.group(1)))
    lessons = conn.execute("select lesson_number, dialogues, grammar_notes from lessons order by lesson_number").fetchall()
    found = []
    for old, (new, page) in sorted(pairs.items()):
        for row in lessons:
            for col in ("dialogues", "grammar_notes"):
                text = row[col] or ""
                if old in text:
                    found.append({"lesson": row["lesson_number"], "where": col, "stands": old, "the_page_has": new,
                                  "book_page": page})
    site = []
    for row in lessons:
        path = ROOT / "docs" / ("lesson-%d.html" % row["lesson_number"])
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        import html as htmllib
        text = htmllib.unescape(html)
        for old, (new, page) in sorted(pairs.items()):
            if old in text:
                site.append({"page": "docs/lesson-%d.html" % row["lesson_number"], "stands": old, "the_page_has": new})
    return {"ocr_slips_the_audit_corrected": len(pairs), "still_in_the_lessons_table": found,
            "still_on_the_public_lesson_pages": site}


def main():
    folder, db_copy = temp_copy()
    try:
        rec = recognises_printed_sentences(db_copy)
        write_jsonl(DATA / "use_blue_book_sentences_recognised.jsonl", rec)
        t2, t2_preverb = frame_t2()
        write_jsonl(DATA / "use_frame_t2.jsonl", t2)
        builder = builder_on_appendix_verbs(db_copy)
        write_jsonl(DATA / "use_builder_on_appendix_verbs.jsonl", builder)
        hidden = hidden_examples(db_copy)
        write_jsonl(DATA / "use_examples_hidden.jsonl", hidden)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    conn = connect()
    shared = verbs_sharing_a_spelling(conn)
    slips = lesson_slips(conn)
    conn.close()

    accented = [r for r in rec if r["has_an_accent"]]
    by_class = defaultdict(lambda: [0, 0])
    for r in hidden:
        kind = "verbs" if (r["class"] or "").startswith("V") else ("nouns" if (r["class"] or "").startswith("N") else "other")
        by_class[kind][0] += r["examples_printed"]
        by_class[kind][1] += r["examples_shown"]
    summary = {
        "1a_printed_sentences": {
            "sentences": len(rec), "with_an_accent_mark": len(accented),
            "found_as_printed": sum(r["found_as_printed"] for r in rec),
            "found_when_typed_without_accents": sum(r["found_without_its_accents"] for r in rec),
            "found_when_typed_without_accents_among_those_with_an_accent": sum(r["found_without_its_accents"] for r in accented)},
        "1b_frame_t2": {"descriptive_verbs_without_a_preverb": len(t2), "by_cause": dict(Counter(r["cause"] for r in t2)),
                        "descriptive_verbs_with_a_preverb_the_frame_cannot_place": t2_preverb},
        "1c_builder_on_appendix_verbs": {"cells": len(builder), "by_cause": dict(Counter(r["cause"] for r in builder)),
                                         "rows": builder},
        "1d_verbs_sharing_a_spelling": shared,
        "2_examples_on_entry_pages": {
            "entries_with_examples": len(hidden),
            "examples_printed": sum(r["examples_printed"] for r in hidden),
            "examples_shown": sum(r["examples_shown"] for r in hidden),
            "entries_showing_none_of_their_examples": sum(1 for r in hidden if r["examples_printed"] and not r["examples_shown"]),
            "by_kind": {k: {"printed": v[0], "shown": v[1]} for k, v in by_class.items()},
            "examples_shown_only_because_of_the_stem_the_possession_engine_cuts": sum(
                max(0, r["shown_only_because_of_the_stem"]) for r in hidden)},
        "3_lessons": {"ocr_slips_the_audit_corrected": slips["ocr_slips_the_audit_corrected"],
                      "still_in_the_lessons_table": len(slips["still_in_the_lessons_table"]),
                      "still_on_the_public_lesson_pages": len(slips["still_on_the_public_lesson_pages"]),
                      "lessons_table_rows": slips["still_in_the_lessons_table"],
                      "public_pages_rows": slips["still_on_the_public_lesson_pages"]},
    }
    write_json(DATA / "use_summary.json", summary)
    s = summary["1a_printed_sentences"]
    out("1a. Blue Book sentences: %d; with an accent %d; found as printed %d; found when typed without accents %d (of those with an accent: %d)"
        % (s["sentences"], s["with_an_accent_mark"], s["found_as_printed"], s["found_when_typed_without_accents"],
           s["found_when_typed_without_accents_among_those_with_an_accent"]))
    s = summary["1b_frame_t2"]
    out("1b. frame T2 on %d descriptive verbs: %s; %d more have a preverb" % (
        s["descriptive_verbs_without_a_preverb"], s["by_cause"], s["descriptive_verbs_with_a_preverb_the_frame_cannot_place"]))
    s = summary["1c_builder_on_appendix_verbs"]
    out("1c. builder on the seven verbs: %d cells: %s" % (s["cells"], s["by_cause"]))
    for r in builder:
        if r["cause"] != "exact":
            out("     %-12s %-22s printed %-16s builder %-16s [%s] %s" % (r["verb"], r["cell"], r["printed"],
                                                                         r["builder_gives"], r["cause"], r["error"] or ""))
    out("1d. %s" % {k: v for k, v in shared.items() if k != "examples"})
    s = summary["2_examples_on_entry_pages"]
    out("2. examples on entry pages: %d printed, %d shown; %d of %d entries show none; by kind %s; shown only because of the stem: %d"
        % (s["examples_printed"], s["examples_shown"], s["entries_showing_none_of_their_examples"],
           s["entries_with_examples"], s["by_kind"], s["examples_shown_only_because_of_the_stem_the_possession_engine_cuts"]))
    s = summary["3_lessons"]
    out("3. lessons: %d OCR slips corrected in the table; still in the lessons table: %d; on public pages: %d" % (
        s["ocr_slips_the_audit_corrected"], s["still_in_the_lessons_table"], s["still_on_the_public_lesson_pages"]))


if __name__ == "__main__":
    main()
