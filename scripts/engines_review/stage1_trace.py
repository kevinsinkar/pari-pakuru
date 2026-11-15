#!/usr/bin/env python3
"""Stage 1 of the engines review: where do the engines' test forms and stored values come from?

    python scripts/engines_review/stage1_trace.py

Three questions, answered from the corrected sources and written to
reports/engines_review/data/stage1_trace.json:

1. Every expected form in an engine's own test: is it printed in a source
   (the Blue Book as read from the scan, Appendix 3, chapters 3 and 4, the
   dictionary), or is it something the engine itself produced, written down as
   the expectation?
2. The values the engines stored in the database: do they still equal what
   the code computes, and do they hold forms that were corrected elsewhere?
3. The copy of Appendix 1 the rules were fitted to (taken from git, the commit
   before the corrections of 2026-11-13) against the corrected appendix:
   which accents and which cells the rules were built on are not on the page.

Reads only. Changes nothing but its own output file.
"""
import json
import re
import subprocess
from collections import Counter

from common import (DATA, EXTRACTED, ROOT, connect, has_accent, load_json, out, strip_accents, write_json)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

COMMIT_BEFORE_FIXES = "ae99693^"   # the parent of "Apply the reviewed fixes from the source-fidelity audit"


def loose(s):
    """Letters only: accents, case, punctuation, spaces and raised dots set aside."""
    s = strip_accents(s).lower()
    for g in "ʔ’‘":
        s = s.replace(g, "'")
    return re.sub(r"[^a-z']", "", s)


def tight(s):
    """As printed, apart from case, outer punctuation and doubled spaces."""
    return re.sub(r"\s+", " ", s.strip().strip(".?!,").lower())


class BlueBook:
    """The Blue Book forms as corrected from the scan (table blue_book_attestations)."""

    def __init__(self, conn):
        self.tight, self.loose, self.words = {}, {}, {}
        for r in conn.execute("select bb_skiri_form, full_sentence_pawnee, lesson_number, page_number "
                              "from blue_book_attestations order by id"):
            for col in ("bb_skiri_form", "full_sentence_pawnee"):
                v = r[col]
                if not v:
                    continue
                hit = {"printed": v, "lesson": r["lesson_number"], "pdf_page": r["page_number"]}
                self.tight.setdefault(tight(v), hit)
                self.loose.setdefault(loose(v), hit)
                for w in re.split(r"[\s,.?!;:]+", v):
                    if w:
                        self.words.setdefault(loose(w), dict(hit, word=w))

    def find(self, form, allow_word=False):
        t, lo = tight(form), loose(form)
        if t in self.tight:
            return "as printed", self.tight[t]
        if lo in self.loose:
            return "the same letters; the printed accents, dots or spaces differ", self.loose[lo]
        if allow_word and lo in self.words:
            return "a word of a printed sentence (letters only)", self.words[lo]
        if len(lo) >= 4:
            for key in sorted(self.loose):
                if lo in key:
                    return "part of a printed sentence (letters only)", self.loose[key]
        if allow_word:
            for key in sorted(self.words):
                if key.startswith(lo) and len(key) > len(lo):
                    return "the start of a printed word (letters only)", self.words[key]
        return "not in the Blue Book", None


def trace_tests(conn):
    import possession_engine as pe
    import sentence_templates as st
    import sound_changes as sc
    import template_slot_fillers as tsf

    bb = BlueBook(conn)
    headwords = {r[0] for r in conn.execute("select headword from lexical_entries")}
    parks_headwords = {r[0] for r in conn.execute("select headword from lexical_entries where source is null or source != 'blue_book'")}
    chapter4 = (EXTRACTED / "grammatical_overview.json").read_text(encoding="utf-8")
    examples = " ".join(r[0] or "" for r in conn.execute("select skiri_text from examples"))
    kin_words = set(re.split(r"[\s,;/\"]+", (EXTRACTED / "appendix3_kinship.json").read_text(encoding="utf-8")))
    record = {}

    def row_for(form, **extra):
        how, hit = bb.find(form, allow_word=extra.pop("allow_word", False))
        row = dict(extra, form=form, blue_book=how)
        if hit:
            row.update(printed=hit["printed"], lesson=hit["lesson"], pdf_page=hit["pdf_page"])
        return row

    # --- sentence templates
    record["sentence_tests"] = [
        row_for(expected, template=tid, description=desc, uses_person_derivation="verb" in slots)
        for tid, slots, expected, desc in st.VALIDATION_TESTS]
    record["template_examples"] = [row_for(t.skiri_example, template=tid, english=t.english_example)
                                   for tid, t in st.TEMPLATES.items()]
    fillers = []
    for cat, items in tsf.SLOT_FILLERS.items():
        for f in items:
            row = row_for(f.skiri_form, category=cat, english=f.english, allow_word=True)
            if f.bb_example_skiri:
                how, hit = bb.find(f.bb_example_skiri)
                row["its_example"] = f.bb_example_skiri
                row["its_example_blue_book"] = how
                row["its_example_printed"] = hit["printed"] if hit else None
            fillers.append(row)
    record["slot_fillers"] = fillers
    record["yes_words"] = [row_for(k, gloss=v, allow_word=True) for k, v in st.YES_WORDS.items()]
    record["imperative_particles"] = [row_for(k, gloss=v, allow_word=True) for k, v in st.IMP_PARTICLES.items()]

    # --- possession engine
    rows = []
    for headword, person, noun_class, poss_type, expected in pe.BB_TESTS:
        row = row_for(expected, input=headword, person=person, system=poss_type,
                      input_is_a_parks_headword=headword in parks_headwords,
                      input_is_any_headword=headword in headwords)
        if poss_type == "kinship":
            row["in_appendix_3"] = expected in kin_words
        rows.append(row)
    record["possession_tests"] = rows
    record["locative_tests"] = [
        {"input": headword, "input_is_a_parks_headword": headword in parks_headwords,
         "test_passes_is_tribal": bool(is_tribal), "plural": bool(plural), "expected": expected,
         "expected_is_a_headword": expected in headwords,
         "expected_in_chapter_4": expected in chapter4,
         "expected_in_a_dictionary_example": expected in examples}
        for headword, noun_class, is_tribal, plural, expected in pe.LOCATIVE_TESTS]
    record["hiri_tests"] = [
        {"stem": stem, "expected": attested, "expected_is_a_headword": attested in headwords,
         "expected_in_chapter_4": attested in chapter4}
        for stem, attested, source in pe.HIRI_SEAM_TESTS]

    # --- sound changes
    printed_surface = {}
    for rule in sc.RULES:
        for ex in rule["examples"]:
            if ex.get("surface"):
                printed_surface[ex["surface"]] = {"rule": rule["rule_id"], "underlying": ex["underlying"]}
    record["sound_change_tests"] = [
        {"input": " + ".join(morphemes), "expected": expected, "description": description,
         "expected_is_a_surface_form_printed_in_chapter_3": expected in printed_surface,
         "printed_example": printed_surface.get(expected),
         "expected_is_a_headword": expected in headwords}
        for morphemes, expected, description, final_s in sc.TEST_CASES]
    record["chapter_3_examples_with_a_printed_surface_form"] = len(printed_surface)
    return record


def trace_stored_values(conn):
    import sound_changes as sc
    import stem_extractor as se

    rec = {}
    # sound_change_rules against the catalogue in the code
    table = {r["rule_id"]: dict(r) for r in conn.execute("select * from sound_change_rules")}
    diffs = []
    for rule in sc.RULES:
        row = table.get(rule["rule_id"])
        if row is None:
            diffs.append(rule["rule_id"] + ": not in the table")
            continue
        for k in ("name", "type", "domain", "formal", "description", "ordering"):
            if row[k] != rule[k]:
                diffs.append("%s: %s" % (rule["rule_id"], k))
        if json.loads(row["examples"]) != rule["examples"]:
            diffs.append(rule["rule_id"] + ": examples")
    rec["sound_change_rules"] = {"rows": len(table), "differences_from_the_code": diffs}

    # form2_confidence: stored against today's computation
    res = se.validate_all(str(ROOT / "skiri_pawnee.db"))
    rates = {k: {"exact_rate": v["exact"] / v["total"], "close_rate": (v["exact"] + v["close"]) / v["total"],
                 "total": v["total"]} for k, v in res["by_category"].items() if v["total"]}

    def band(x):
        return "high" if x >= 0.75 else ("medium" if x >= 0.5 else "low")

    has_form2 = {r[0] for r in conn.execute("select entry_id from paradigmatic_forms where form_number=2")}
    has_any = {r[0] for r in conn.execute("select entry_id from paradigmatic_forms")}
    rows = conn.execute("select entry_id, headword, verb_class, stem_preverb, grammatical_class, form2_confidence "
                        "from lexical_entries where grammatical_class like 'V%' order by entry_id").fetchall()
    same = differ = unset = band_changes = 0
    largest = 0.0
    bands = Counter()
    with_form2 = without_any = 0
    for r in rows:
        if r["form2_confidence"] is None:
            unset += 1
            continue
        now = se.compute_confidence(r["entry_id"], r["headword"], r["verb_class"] or "", r["stem_preverb"] or "",
                                    r["grammatical_class"] or "", rates)
        bands[band(r["form2_confidence"])] += 1
        with_form2 += r["entry_id"] in has_form2
        without_any += r["entry_id"] not in has_any
        if abs(now - r["form2_confidence"]) < 1e-9:
            same += 1
        else:
            differ += 1
            largest = max(largest, abs(now - r["form2_confidence"]))
            band_changes += band(now) != band(r["form2_confidence"])
    rec["form2_confidence"] = {
        "verb_entries": len(rows), "with_a_stored_value": same + differ, "without": unset,
        "stored_equals_todays_computation": same, "stored_differs": differ,
        "largest_difference": round(largest, 3), "would_change_band": band_changes,
        "stored_bands": dict(bands),
        "entries_with_a_value_whose_form_2_is_attested": with_form2,
        "entries_with_a_value_and_no_attested_form": without_any,
    }

    # morpheme_inventory against Parks's printed tables 8, 9, 10 and 17
    tables = {t["number"]: t for t in load_json(EXTRACTED / "grammatical_overview_tables.json")["tables"]}
    printed = set()          # every piece printed in tables 8, 9, 10 and 17, without its hyphens
    for n in (8, 9, 10, 17):
        for row in tables[n].get("rows", []):
            for cell in row:
                for token in re.split(r"[\s/+→]+", str(cell)):
                    printed.add(token.strip("-.,:"))
    inv = []
    for r in conn.execute("select slot_name, morpheme_form, label from morpheme_inventory order by slot_number, id"):
        form = r["morpheme_form"]
        inv.append({"slot": r["slot_name"], "form": form, "label": r["label"],
                    "form_is_printed_in_tables_8_9_10_17": form.strip("-") in printed})
    rec["morpheme_inventory"] = {
        "rows": len(inv),
        "forms_not_printed_in_parks_tables": sorted({"%s (%s)" % (i["form"], i["label"]) for i in inv
                                                     if not i["form_is_printed_in_tables_8_9_10_17"]}),
    }

    # possession tables
    kin_file = (EXTRACTED / "appendix3_kinship.json").read_text(encoding="utf-8")
    pe_rows = [dict(r) for r in conn.execute("select * from possession_examples order by id")]
    stale = [r for r in pe_rows if r["possession_type"] == "kinship" and r["expected_form"] not in kin_file]
    rec["possession_examples"] = {
        "rows": len(pe_rows),
        "rows_where_expected_equals_generated": sum(1 for r in pe_rows if r["expected_form"] == r["generated_form"]),
        "kinship_rows_whose_form_is_not_in_appendix_3_as_corrected": [
            {"headword": r["headword"], "person": r["person"], "stored": r["expected_form"]} for r in stale],
        "rows_beginning_kti": sum(1 for r in pe_rows if (r["expected_form"] or "").startswith("kti ")),
    }
    headwords = {r[0] for r in conn.execute("select headword from lexical_entries")}
    ns = [dict(r) for r in conn.execute("select * from noun_stems")]
    rec["noun_stems"] = {
        "rows": len(ns), "rows_linked_to_an_entry": sum(1 for r in ns if r["entry_id"]),
        "headwords_that_are_not_dictionary_headwords": sorted(r["headword"] for r in ns if r["headword"] not in headwords),
    }
    kp = [dict(r) for r in conn.execute("select * from kinship_paradigms")]
    rec["kinship_paradigms"] = {
        "rows": len(kp), "by_source": dict(Counter(r["source"] for r in kp)),
        "rows_not_from_appendix_3": [{"english": r["english_term"], "stem": r["stem"], "1sg": r["form_1sg"],
                                      "2sg": r["form_2sg"], "notes": r["notes"]} for r in kp if r["source"] != "appendix3"],
    }
    rec["verb_paradigms"] = {"rows": conn.execute("select count(*) from verb_paradigms").fetchone()[0],
                             "what": "a copy of Appendix 1 (corrected 2026-11-13), not engine output"}
    return rec


def trace_appendix_before_fixes():
    """The copy of Appendix 1 the rules were fitted to, against the corrected one."""
    try:
        old_text = subprocess.run(["git", "show", COMMIT_BEFORE_FIXES + ":extracted_data/appendix1_conjugations.json"],
                                  cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:   # no git history at hand
        return {"error": "could not read the earlier copy from git: %s" % exc}
    old, new = json.loads(old_text), load_json(EXTRACTED / "appendix1_conjugations.json")
    cells = []
    for page in new:
        gloss = new[page]["english_gloss"]
        for mode, forms in new[page]["modes"].items():
            for pn, cell in forms.items():
                cells.append((gloss, mode, pn, old[page]["modes"][mode][pn]["skiri"], cell["skiri"]))
    by_verb = {}
    for gloss, mode, pn, o, n in cells:
        b = by_verb.setdefault(gloss, {"accented_in_the_old_copy": 0, "accented_on_the_page": 0,
                                       "old_accent_not_on_the_page": 0})
        b["accented_in_the_old_copy"] += has_accent(o)
        b["accented_on_the_page"] += has_accent(n)
        b["old_accent_not_on_the_page"] += has_accent(o) and (not has_accent(n) or o != n)
    return {
        "commit_of_the_old_copy": COMMIT_BEFORE_FIXES,
        "cells": len(cells),
        "cells_that_differ": sum(1 for c in cells if c[3] != c[4]),
        "differ_in_letters": sum(1 for c in cells if strip_accents(c[3]) != strip_accents(c[4])),
        "differ_only_in_accent_marks": sum(1 for c in cells if c[3] != c[4] and strip_accents(c[3]) == strip_accents(c[4])),
        "accented_in_the_old_copy": sum(has_accent(c[3]) for c in cells),
        "accented_on_the_page": sum(has_accent(c[4]) for c in cells),
        "accented_the_same_in_both": sum(1 for c in cells if has_accent(c[3]) and c[3] == c[4]),
        "by_verb": by_verb,
        "cells_with_two_printed_forms": sum(1 for c in cells if "," in c[4]),
        "the_two_cells_person_derivation_misses": [
            {"verb": c[0], "cell": c[1] + " " + c[2], "old_copy": c[3], "page": c[4]} for c in cells
            if (c[0], c[1], c[2]) in (("to be good", "absolutive_perfective", "3sg"),
                                      ("to be sick", "absolutive_perfective", "3sg"))],
    }


def main():
    conn = connect()
    record = {"tests": trace_tests(conn), "stored_values": trace_stored_values(conn),
              "appendix_1_before_the_corrections": trace_appendix_before_fixes()}
    digest = write_json(DATA / "stage1_trace.json", record)
    t = record["tests"]
    for key in ("sentence_tests", "template_examples", "slot_fillers", "yes_words", "imperative_particles",
                "possession_tests"):
        out("%-22s %s" % (key, dict(Counter(r["blue_book"] for r in t[key]))))
    out("sound-change tests whose expected form is printed in chapter 3: %d of %d" % (
        sum(r["expected_is_a_surface_form_printed_in_chapter_3"] for r in t["sound_change_tests"]),
        len(t["sound_change_tests"])))
    out("stored values: %s" % json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, (list, dict))}
                                          for k, v in record["stored_values"].items()}, ensure_ascii=False))
    a = record["appendix_1_before_the_corrections"]
    out("appendix 1: %s" % json.dumps({k: v for k, v in a.items() if not isinstance(v, (list, dict))}, ensure_ascii=False))
    out("written: reports/engines_review/data/stage1_trace.json  sha256 %s" % digest[:16])


if __name__ == "__main__":
    main()
