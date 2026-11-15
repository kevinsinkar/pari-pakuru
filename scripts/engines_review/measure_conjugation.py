#!/usr/bin/env python3
"""Stage 2: the conjugation engine and the accent rules, measured as they are.

    python scripts/engines_review/measure_conjugation.py

A. Appendix 1 (770 cells). The engine is called with its own settings for the
   seven verbs (morpheme_inventory.APPENDIX1_VERBS). All of this is SEEN: the
   rules were fitted to these cells. Reported verb by verb and mode by mode,
   with the misses sorted by cause.
B. The dictionary's five verb forms (9,559). UNSEEN. The engine is set up for a
   dictionary verb the way its own --validate-dict does it (headword as stem,
   first preverb, the class as printed), so this measures the engine with the
   only adapter its authors wrote.
C. The accents. What the engine marks against what the page marks.

Nothing is changed: the engine's functions are imported and called.
Writes data/conjugation_appendix1.jsonl, data/conjugation_dictionary.jsonl and
data/conjugation_summary.json.
"""
import logging
from collections import Counter, defaultdict

from common import (CAUSES, DATA, TESTSETS, classify, clean, group_of, has_accent, out, pct, read_jsonl,
                    strip_accents, write_json, write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

logging.disable(logging.CRITICAL)          # the engine logs at import and in its validators
import morpheme_inventory as mi  # noqa: E402

VERB_OF_PAGE = {page: info for page, info in mi.APPENDIX1_VERBS.items()}


def count_causes(rows):
    c = Counter(r["cause"] for r in rows)
    return {k: c[k] for k in CAUSES if c[k]}


def groups(rows):
    c = Counter(group_of(r["cause"]) for r in rows)
    return dict(c)


# ---------------------------------------------------------------------------
# A. Appendix 1
# ---------------------------------------------------------------------------

def run_appendix1():
    cells = read_jsonl(TESTSETS / "appendix1.jsonl")
    rows = []
    for cell in cells:
        info = VERB_OF_PAGE[cell["page"]]
        our_mode, is_sub = mi.APPENDIX1_MODE_MAP[cell["mode"]]
        try:
            res = mi.conjugate(stem=info["stem"], verb_class=info["verb_class"], mode=our_mode,
                               person_number=cell["person"], aspect="perfective",
                               preverb=info.get("preverb"), subordinate=is_sub)
            produced, breakdown = res["surface_form"], res["morpheme_breakdown"]
        except Exception as exc:
            produced, breakdown = "", "error: %s" % exc
        cause, compared = classify(produced, cell["variants"])
        first = cell["variants"][0]
        rows.append({"verb": cell["verb"], "mode": cell["mode"], "person": cell["person"],
                     "printed": cell["printed"], "produced": produced, "compared_with": compared,
                     "cause": cause, "exact_against_first_variant": clean(produced) == first,
                     "letters_right": strip_accents(clean(produced)) in [strip_accents(v) for v in cell["variants"]],
                     "printed_has_accent": has_accent(compared), "produced_has_accent": has_accent(produced),
                     "breakdown": breakdown})
    return rows


def summarise_appendix1(rows):
    s = {"cells": len(rows),
         "exact": sum(r["cause"] == "exact" for r in rows),
         "exact_against_the_first_printed_form_only": sum(r["exact_against_first_variant"] for r in rows),
         "letters_right_accents_aside": sum(r["letters_right"] for r in rows),
         "by_cause": count_causes(rows), "groups": groups(rows)}
    by_verb, by_mode, by_person = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in rows:
        by_verb[r["verb"]].append(r)
        by_mode[r["mode"]].append(r)
        by_person[r["person"]].append(r)
    for name, d in (("by_verb", by_verb), ("by_mode", by_mode), ("by_person", by_person)):
        s[name] = {k: {"cells": len(v), "exact": sum(x["cause"] == "exact" for x in v),
                       "letters_right": sum(x["letters_right"] for x in v), "by_cause": count_causes(v)}
                   for k, v in d.items()}
    # singular against dual and plural: the part a learner meets first
    sg = [r for r in rows if r["person"].endswith("sg")]
    s["singular_persons"] = {"cells": len(sg), "exact": sum(r["cause"] == "exact" for r in sg)}
    s["dual_and_plural_persons"] = {"cells": len(rows) - len(sg),
                                    "exact": sum(r["cause"] == "exact" for r in rows) - sum(r["cause"] == "exact" for r in sg)}
    return s


def accents(rows):
    """The engine's accents against the page's, on the cells whose letters are right and on all cells."""
    table = Counter()
    for r in rows:
        p, e = r["printed_has_accent"], r["produced_has_accent"]
        if r["letters_right"]:
            if p and e:
                key = "both marked, same place" if clean(r["produced"]) == r["compared_with"] else "both marked, different place"
            elif p:
                key = "page marked, engine not"
            elif e:
                key = "engine marked, page not"
            else:
                key = "neither marked"
            table["letters right: " + key] += 1
        else:
            table["letters wrong: engine marked" if e else "letters wrong: engine not marked"] += 1
    by_verb = defaultdict(Counter)
    for r in rows:
        by_verb[r["verb"]]["page"] += r["printed_has_accent"]
        by_verb[r["verb"]]["engine"] += r["produced_has_accent"]
        by_verb[r["verb"]]["engine_marks_and_page_does_not"] += (r["produced_has_accent"] and not r["printed_has_accent"])
    # what the score would be if the engine marked no accent at all
    no_accent_exact = sum(1 for r in rows if r["letters_right"] and not r["printed_has_accent"])
    return {"table": dict(table), "by_verb": {k: dict(v) for k, v in by_verb.items()},
            "cells_the_engine_marks": sum(r["produced_has_accent"] for r in rows),
            "cells_the_page_marks": sum(r["printed_has_accent"] for r in rows),
            "exact_now": sum(r["cause"] == "exact" for r in rows),
            "exact_if_the_engine_marked_no_accent": no_accent_exact,
            "engine_marks_where_the_page_has_none": [
                {"verb": r["verb"], "mode": r["mode"], "person": r["person"], "printed": r["printed"],
                 "produced": r["produced"]} for r in rows if r["produced_has_accent"] and not r["printed_has_accent"]]}


# ---------------------------------------------------------------------------
# B. The dictionary's five forms
# ---------------------------------------------------------------------------

FORM_NAMES = {1: "1 (I, perfective)", 2: "2 (he/she, perfective)", 3: "3 (he/she, imperfective)",
              4: "4 (subordinate)", 5: "5 (intentive)"}


def where_it_differs(produced, printed):
    """For a miss in other letters: at the end of the word, at its start, or elsewhere."""
    p, b = strip_accents(clean(produced)), strip_accents(printed)
    lcp = 0
    while lcp < min(len(p), len(b)) and p[lcp] == b[lcp]:
        lcp += 1
    lcs = 0
    while lcs < min(len(p), len(b)) - lcp and p[-1 - lcs] == b[-1 - lcs]:
        lcs += 1
    if lcp >= len(b) - 4 and lcp >= 3:
        return "only in the last letters (ending)"
    if lcs >= len(b) - 5 and lcs >= 3:
        return "only in the first letters (prefix meets stem)"
    return "in several places or in the middle"


def class_group(gc):
    gc = (gc or "").replace(" ", "")
    first = gc.split(",")[0].split("(")[0]
    return {"VI": "VI active intransitive", "VT": "VT active transitive", "VD": "VD descriptive",
            "VL": "VL locative", "VP": "VP passive", "VR": "VR reflexive"}.get(first, "other")


def run_dictionary():
    forms = read_jsonl(TESTSETS / "dictionary_forms.jsonl")
    rows = []
    for f in forms:
        hw, gc = f["headword"], f["grammatical_class"] or ""
        preverb = mi._parse_preverb(f["stem_preverb"])
        vc = mi._parse_verb_class(f["verb_class"])
        row = {"entry_id": f["entry_id"], "headword": hw, "grammatical_class": gc, "class_group": class_group(gc),
               "verb_class": f["verb_class"], "stem_preverb": f["stem_preverb"], "form": f["form_number"],
               "printed": f["printed"],
               "headword_has_notation": any(ch in hw for ch in "/()[] ,-")}
        # --- the engine's own set-up for a dictionary verb (validate_dict) ---
        if not vc:
            if gc in ("VD", "VD, VT"):
                vc = "u"
            elif gc == "VL":
                vc = "wi"
        if not vc or vc not in mi.VERB_CLASSES:
            row.update(cause="no form produced", produced="", why_not="the engine has no class for this verb (%s, %s)" % (gc, f["verb_class"]))
            rows.append(row)
            continue
        stem = hw
        if preverb == "ut":
            stem = "uu" + hw if not hw.startswith("uu") else hw
        params = mi.DICT_FORM_PARAMS[f["form_number"]]
        try:
            res = mi.conjugate(stem=stem, verb_class=vc, mode=params["mode"], person_number=params["person_number"],
                               aspect=params["aspect"], preverb=preverb if preverb != "ut" else None,
                               subordinate=params["subordinate"], intentive=params["intentive"])
            produced = res["surface_form"]
        except Exception as exc:
            produced = ""
            row["why_not"] = "error: %s" % exc
        cause, compared = classify(produced, f["variants"])
        row.update(produced=produced, compared_with=compared, cause=cause)
        if cause.startswith("other letters"):
            row["where"] = where_it_differs(produced, compared)
        rows.append(row)
    return rows


def summarise_dictionary(rows):
    def block(sel):
        return {"forms": len(sel), "exact": sum(r["cause"] == "exact" for r in sel), "groups": groups(sel),
                "by_cause": count_causes(sel)}

    s = {"all": block(rows)}
    s["by_form"] = {FORM_NAMES[n]: block([r for r in rows if r["form"] == n]) for n in range(1, 6)}
    s["by_class_group"] = {g: block([r for r in rows if r["class_group"] == g])
                           for g in sorted({r["class_group"] for r in rows})}
    s["by_form_and_class_group"] = {
        "%s | %s" % (FORM_NAMES[n], g): {"forms": len(sel), "exact": sum(r["cause"] == "exact" for r in sel)}
        for n in range(1, 6) for g in sorted({r["class_group"] for r in rows})
        for sel in [[r for r in rows if r["form"] == n and r["class_group"] == g]] if sel}
    s["by_verb_class"] = {str(vc): block([r for r in rows if r["verb_class"] == vc])
                          for vc in sorted({r["verb_class"] for r in rows}, key=lambda x: str(x))}
    s["by_preverb"] = {str(pv): block([r for r in rows if r["stem_preverb"] == pv])
                       for pv, n in Counter(r["stem_preverb"] for r in rows).most_common(6)}
    s["plain_headwords_only"] = block([r for r in rows if not r["headword_has_notation"]])
    s["headwords_with_notation"] = block([r for r in rows if r["headword_has_notation"]])
    other = [r for r in rows if r["cause"].startswith("other letters")]
    s["other_letters_where"] = {FORM_NAMES[n]: dict(Counter(r["where"] for r in other if r["form"] == n))
                                for n in range(1, 6)}
    s["engine_adds_an_accent"] = sum(1 for r in rows if has_accent(r.get("produced", "")))
    # verbs for which all printed forms come out right
    by_entry = defaultdict(list)
    for r in rows:
        by_entry[r["entry_id"]].append(r)
    s["verbs"] = len(by_entry)
    s["verbs_with_every_printed_form_right"] = sum(1 for v in by_entry.values() if all(r["cause"] == "exact" for r in v))
    s["verbs_with_no_printed_form_right"] = sum(1 for v in by_entry.values() if not any(r["cause"] == "exact" for r in v))
    return s


def engines_own_dictionary_count():
    """The engine's own --validate-dict, for comparison with the 14.8% it recorded on 2026-03-09."""
    from common import DB_PATH
    res = mi.validate_dict(str(DB_PATH))
    return {"forms_tested": res["total"], "skipped": res["skipped"], "exact": res["exact"],
            "exact_once_accents_and_notation_are_set_aside": res["exact_normalized"],
            "within_two_letters": res["close"], "further_off": res["mismatch"],
            "note": "the engine compares with the first printed form only and counts in its own way"}


def main():
    a1 = run_appendix1()
    write_jsonl(DATA / "conjugation_appendix1.jsonl", a1)
    d = run_dictionary()
    write_jsonl(DATA / "conjugation_dictionary.jsonl", d)
    summary = {"appendix1": summarise_appendix1(a1), "accents_on_appendix1": accents(a1),
               "dictionary": summarise_dictionary(d), "engines_own_dictionary_count": engines_own_dictionary_count()}
    write_json(DATA / "conjugation_summary.json", summary)

    s = summary["appendix1"]
    out("A. Appendix 1 (seen): %d of %d exact (%s); against the first printed form only: %d; letters right, accents aside: %d"
        % (s["exact"], s["cells"], pct(s["exact"], s["cells"]), s["exact_against_the_first_printed_form_only"],
           s["letters_right_accents_aside"]))
    out("   by cause: %s" % s["by_cause"])
    for v, b in s["by_verb"].items():
        out("   %-12s %3d of %d exact; letters right %3d" % (v, b["exact"], b["cells"], b["letters_right"]))
    for m, b in s["by_mode"].items():
        out("   %-36s %2d of %d exact" % (m, b["exact"], b["cells"]))
    out("   singular persons: %(exact)d of %(cells)d" % s["singular_persons"]
        + "; dual and plural: %(exact)d of %(cells)d" % s["dual_and_plural_persons"])
    ac = summary["accents_on_appendix1"]
    out("C. Accents: the page marks %d cells, the engine marks %d; %s" % (
        ac["cells_the_page_marks"], ac["cells_the_engine_marks"], ac["table"]))
    out("   exact now %d; exact if the engine marked no accent at all %d" % (
        ac["exact_now"], ac["exact_if_the_engine_marked_no_accent"]))
    s = summary["dictionary"]
    out("B. Dictionary forms (unseen): %d of %d exact (%s)" % (
        s["all"]["exact"], s["all"]["forms"], pct(s["all"]["exact"], s["all"]["forms"])))
    out("   groups: %s" % s["all"]["groups"])
    for k, b in s["by_form"].items():
        out("   form %-28s %4d of %4d exact (%s)  %s" % (k, b["exact"], b["forms"], pct(b["exact"], b["forms"]), b["by_cause"]))
    for k, b in s["by_class_group"].items():
        out("   %-24s %4d of %4d exact (%s)" % (k, b["exact"], b["forms"], pct(b["exact"], b["forms"])))
    out("   verbs: %d; every printed form right: %d; none right: %d" % (
        s["verbs"], s["verbs_with_every_printed_form_right"], s["verbs_with_no_printed_form_right"]))
    out("   the engine's own count: %s" % summary["engines_own_dictionary_count"])


if __name__ == "__main__":
    main()
