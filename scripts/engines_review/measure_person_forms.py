#!/usr/bin/env python3
"""Stage 2: person and mode derivation (person_forms.py), measured as it is.

    python scripts/engines_review/measure_person_forms.py

A. Appendix 1 (SEEN). The cells the engine derives for the seven verbs: the
   second person indicative and the three absolutive singulars. The rules were
   read off these verbs.

B. The third person absolutive against the dictionary's form 4 (UNSEEN).
   Form 4 is the gerundial: irii- before the absolutive, with a subordinate
   ending. So after irii- is taken off, form 4 begins the way the third person
   absolutive begins. The engine makes its absolutive by changing the start of
   form 2; this test asks whether form 4 starts the same way, over as many
   letters as the engine changed plus the next two. It tests the left edge,
   which is all the engine claims to know, on verbs it was never fitted to.
   How good a witness form 4 is, is measured first on Appendix 1 itself, where
   both the absolutive and the gerundial are printed.

C. "I" for descriptive verbs (UNSEEN). Where a descriptive verb has no form 1
   the engine makes one: tiku + stem. For the descriptive verbs that do have a
   printed form 1, the same rule is applied and compared with it.

D. How many of the forms it derives are printed anywhere. Each derived form is
   looked for, as a whole word, in the dictionary's own example sentences.
   A hit shows the form exists; no hit shows nothing.

E. How often it gives a form at all (coverage), per kind of form.

Nothing is changed. Writes data/person_forms_*.jsonl and data/person_forms_summary.json.
"""
import re
from collections import Counter, defaultdict

from common import (DATA, EXTRACTED, TESTSETS, classify_one, clean, connect, load_json, no_glottal, out, pct,
                    read_jsonl, short_vowels, strip_accents, variants, write_json, write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

import person_forms as pf  # noqa: E402

PREVERB_OF = {"to do it": "(ut...)", "to be good": "(uur...)"}     # as the engine's own check sets them


# ---------------------------------------------------------------------------
# A. Appendix 1
# ---------------------------------------------------------------------------

def run_appendix():
    data = load_json(EXTRACTED / "appendix1_conjugations.json")
    rows = []
    for page, verb in data.items():
        gloss = verb["english_gloss"]
        ind = verb["modes"]["indicative_perfective"]
        absv = verb["modes"]["absolutive_perfective"]
        f1 = strip_accents(variants(ind["1sg"]["skiri"])[0])
        f2 = strip_accents(variants(ind["3sg"]["skiri"])[0])
        d = pf.derive_forms(form_1=f1, form_2=f2, stem_preverb=PREVERB_OF.get(gloss))
        for label, printed in (("2sg_ind", ind["2sg"]["skiri"]), ("1sg_abs", absv["1sg"]["skiri"]),
                               ("2sg_abs", absv["2sg"]["skiri"]), ("3sg_abs", absv["3sg"]["skiri"])):
            derived = d[label]
            printed_v = [strip_accents(v) for v in variants(printed)]
            if derived is None:
                cause = "no form produced"
            else:
                cause = min((classify_one(derived, v) for v in printed_v),
                            key=lambda c: (c != "exact", c))
            rows.append({"verb": gloss, "cell": label, "printed": printed, "derived": derived, "cause": cause})
    return rows


# ---------------------------------------------------------------------------
# B. Third person absolutive against form 4
# ---------------------------------------------------------------------------

def gerundial_body(form4):
    """Form 4 without its irii-: what is left begins with the absolutive prefix."""
    f = clean(form4)
    if not f.startswith("iri"):
        return None
    rest = f[3:]
    if rest.startswith("i"):
        rest = rest[1:]
    return rest if rest.startswith("r") else None       # iriis-, iriiw-, iriik- are dual, reflexive or indefinite forms


def compare_edge(derived, form2, body):
    """Does the body of form 4 start as the derived absolutive starts?

    The zone compared is what the engine changed at the start of form 2, and
    the two letters after it.
    """
    d, f2 = clean(derived), clean(form2)
    i = 0
    while i < min(len(d), len(f2)) and d[-1 - i] == f2[-1 - i]:
        i += 1
    changed = d[:len(d) - i]                 # the new left edge
    replaced = f2[:len(f2) - i]
    zone = d[:len(changed) + 2]
    result = "other letters"
    for label, fn in (("the same", lambda x: x), ("vowel length", short_vowels), ("glottal stop", no_glottal),
                      ("vowel length and glottal stop", lambda x: short_vowels(no_glottal(x)))):
        z, b = fn(zone), fn(body)
        if b.startswith(z):
            result = label
            break
    return {"rule": "%s- to %s-" % (replaced or "(nothing)", changed or "(nothing)"), "zone": zone,
            "form4_starts": body[:len(zone) + 1], "result": result}


def branch_of(form2, stem_preverb, headword):
    """Which line of person_forms.to_absolutive (third person) applies. The conditions are copied from it, in its order."""
    f = strip_accents(form2)
    if f.startswith("tih"):
        if headword and strip_accents(headword).startswith("h"):
            return "tih- with a stem in h-: ti- to ra-"
        return "tih- to riih-"
    if f.startswith("tii"):
        return "tii- to rii-"
    if f.startswith("tiʔ"):
        return "tiʔ- to raʔ-"
    if f.startswith("tuu") and stem_preverb and "uur" in stem_preverb:
        return "tuu- to ru- (preverb uur-)"
    if f.startswith("tu"):
        return "tu- to ru-"
    if f.startswith("ti"):
        return "ti- to ra-"
    return "none: form 2 begins %s-" % f[:2]


def witness_on_appendix1():
    """How often does the gerundial start like the absolutive, where Parks prints both?"""
    data = load_json(EXTRACTED / "appendix1_conjugations.json")
    rows = []
    for page, verb in data.items():
        m = verb["modes"]
        for pn in ("1sg", "2sg", "3sg"):
            ab = strip_accents(variants(m["absolutive_perfective"][pn]["skiri"])[0])
            ge = strip_accents(variants(m["gerundial_perfective_subordinate"][pn]["skiri"])[0])
            ind = strip_accents(variants(m["indicative_perfective"][pn]["skiri"])[0])
            body = gerundial_body(ge)
            if body is None:
                rows.append({"verb": verb["english_gloss"], "person": pn, "absolutive": ab, "gerundial": ge,
                             "result": "gerundial does not have the shape irii- + r…"})
                continue
            cmp_ = compare_edge(ab, ind, body)
            rows.append({"verb": verb["english_gloss"], "person": pn, "absolutive": ab, "gerundial": ge,
                         "result": cmp_["result"], "zone": cmp_["zone"]})
    return rows


def run_form4():
    by_entry = defaultdict(dict)
    meta = {}
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        by_entry[f["entry_id"]][f["form_number"]] = f
        meta[f["entry_id"]] = f
    rows = []
    for eid, forms in sorted(by_entry.items()):
        if 2 not in forms or 4 not in forms:
            continue
        m = meta[eid]
        f2v, f4v = forms[2]["variants"], forms[4]["variants"]
        row = {"entry_id": eid, "headword": m["headword"], "grammatical_class": m["grammatical_class"],
               "stem_preverb": m["stem_preverb"], "form_2": forms[2]["printed"], "form_4": forms[4]["printed"]}
        if len(f2v) != 1 or len(f4v) != 1:
            row["result"] = "left out: two printed forms"
            rows.append(row)
            continue
        body = gerundial_body(f4v[0])
        if body is None:
            row["result"] = "left out: form 4 is not irii- + r…"
            rows.append(row)
            continue
        derived = pf.to_absolutive(f2v[0], third_person=True, stem_preverb=m["stem_preverb"], headword=m["headword"])
        row["derived"] = derived
        row["rule"] = branch_of(f2v[0], m["stem_preverb"], m["headword"])
        if derived is None:
            row["result"] = "no form produced"
            rows.append(row)
            continue
        cmp_ = compare_edge(derived, f2v[0], body)
        cmp_.pop("rule")
        row.update(cmp_)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# C. "I" for descriptive verbs
# ---------------------------------------------------------------------------

def run_descriptive_first_person():
    by_entry = defaultdict(dict)
    meta = {}
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        by_entry[f["entry_id"]][f["form_number"]] = f
        meta[f["entry_id"]] = f
    rows = []
    for eid, forms in sorted(by_entry.items()):
        m = meta[eid]
        gc = (m["grammatical_class"] or "").split(",")[0].strip()
        if gc not in ("VD", "VL") or m["stem_preverb"] or 1 not in forms or 2 not in forms:
            continue
        d = pf.derive_forms(form_1=None, form_2=forms[2]["variants"][0], headword=m["headword"],
                            stem_preverb=m["stem_preverb"], gram_class=m["grammatical_class"])
        made = d["1sg_ind"]
        printed = forms[1]["variants"]
        cause = "no form produced" if not made else min((classify_one(made, v) for v in printed),
                                                        key=lambda c: (c != "exact", c))
        rows.append({"entry_id": eid, "headword": m["headword"], "grammatical_class": m["grammatical_class"],
                     "form_2": forms[2]["printed"], "printed_form_1": forms[1]["printed"], "made": made, "cause": cause})
    return rows


# ---------------------------------------------------------------------------
# D and E. Coverage, and derived forms found in the dictionary's examples
# ---------------------------------------------------------------------------

DERIVED_KEYS = ["2sg_ind", "1sg_ind_impf", "2sg_ind_impf", "1sg_ind_int", "2sg_ind_int", "1sg_abs", "2sg_abs", "3sg_abs"]
LABEL = {"2sg_ind": "you, past", "1sg_ind_impf": "I, present", "2sg_ind_impf": "you, present",
         "1sg_ind_int": "I, future", "2sg_ind_int": "you, future", "1sg_abs": "I, question form",
         "2sg_abs": "you, question form", "3sg_abs": "he/she, question form"}


def run_coverage_and_examples():
    conn = connect()
    words = Counter()
    words_by_entry = defaultdict(set)
    for r in conn.execute("select entry_id, skiri_text from examples where skiri_text is not null"):
        for w in re.split(r"[^a-zʔáíúàìù']+", strip_accents(r["skiri_text"].lower()).replace("'", "ʔ")):
            if w:
                words[w] += 1
                words_by_entry[r["entry_id"]].add(w)
    conn.close()
    by_entry = defaultdict(dict)
    meta = {}
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        by_entry[f["entry_id"]][f["form_number"]] = f["variants"][0]
        meta[f["entry_id"]] = f
    made = Counter()
    found_anywhere = Counter()
    found_in_own_entry = Counter()
    hits = []
    for eid, forms in sorted(by_entry.items()):
        m = meta[eid]
        d = pf.derive_forms(form_1=forms.get(1), form_2=forms.get(2), form_3=forms.get(3), form_5=forms.get(5),
                            headword=m["headword"], stem_preverb=m["stem_preverb"], gram_class=m["grammatical_class"])
        for k in DERIVED_KEYS:
            v = d.get(k)
            if not v:
                continue
            made[k] += 1
            if v in words:
                found_anywhere[k] += 1
            if v in words_by_entry.get(eid, ()):
                found_in_own_entry[k] += 1
                hits.append({"entry_id": eid, "headword": m["headword"], "form": k, "derived": v})
    table = {LABEL[k]: {"verbs_with_a_derived_form": made[k], "of_verbs": len(by_entry),
                        "found_as_a_word_in_some_dictionary_example": found_anywhere[k],
                        "found_in_an_example_of_the_same_entry": found_in_own_entry[k]} for k in DERIVED_KEYS}
    return table, hits


def main():
    a = run_appendix()
    write_jsonl(DATA / "person_forms_appendix1.jsonl", a)
    w = witness_on_appendix1()
    b = run_form4()
    write_jsonl(DATA / "person_forms_form4.jsonl", b)
    c = run_descriptive_first_person()
    write_jsonl(DATA / "person_forms_descriptive.jsonl", c)
    table, hits = run_coverage_and_examples()
    write_jsonl(DATA / "person_forms_found_in_examples.jsonl", hits)

    tested = [r for r in b if r["result"] not in ("left out: two printed forms", "left out: form 4 is not irii- + r…")]
    by_rule = defaultdict(Counter)
    for r in tested:
        by_rule[r.get("rule", "?")][r["result"]] += 1
    summary = {
        "A_appendix1": {"cells": len(a), "by_cause": dict(Counter(r["cause"] for r in a)),
                        "misses": [r for r in a if r["cause"] not in ("exact",)]},
        "B_witness_on_appendix1": {
            "third_person": dict(Counter(r["result"] for r in w if r["person"] == "3sg")),
            "first_and_second_person": dict(Counter(r["result"] for r in w if r["person"] != "3sg")),
            "rows": w},
        "B_form4": {"verbs_with_forms_2_and_4": len(b), "left_out": dict(Counter(r["result"] for r in b if r["result"].startswith("left out"))),
                    "tested": len(tested), "result": dict(Counter(r["result"] for r in tested)),
                    "by_rule": {k: dict(v) for k, v in sorted(by_rule.items(), key=lambda kv: -sum(kv[1].values()))}},
        "C_descriptive_first_person": {"verbs": len(c), "by_cause": dict(Counter(r["cause"] for r in c))},
        "D_E_coverage_and_examples": table,
    }
    write_json(DATA / "person_forms_summary.json", summary)

    out("A. Appendix 1 (seen): %s" % summary["A_appendix1"]["by_cause"])
    out("B. witness check on Appendix 1: third person %s; first and second %s" % (
        summary["B_witness_on_appendix1"]["third_person"], summary["B_witness_on_appendix1"]["first_and_second_person"]))
    s = summary["B_form4"]
    out("B. he/she question form against form 4 (unseen): %d verbs tested (%s left out): %s" % (
        s["tested"], s["left_out"], s["result"]))
    for rule, c_ in s["by_rule"].items():
        n = sum(c_.values())
        if n >= 5:
            out("   %-28s %4d verbs: %s" % (rule, n, dict(c_)))
    s = summary["C_descriptive_first_person"]
    out("C. tiku + stem for descriptive verbs with a printed form 1: %d verbs: %s" % (s["verbs"], s["by_cause"]))
    out("D/E. coverage and examples:")
    for k, v in table.items():
        out("   %-24s made for %4d of %d verbs (%s); found in a dictionary example: %d (same entry %d)" % (
            k, v["verbs_with_a_derived_form"], v["of_verbs"], pct(v["verbs_with_a_derived_form"], v["of_verbs"]),
            v["found_as_a_word_in_some_dictionary_example"], v["found_in_an_example_of_the_same_entry"]))


if __name__ == "__main__":
    main()
