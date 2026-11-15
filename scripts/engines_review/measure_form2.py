#!/usr/bin/env python3
"""Stage 2: the form 2 predictor (stem_extractor.py), measured as it is.

    python scripts/engines_review/measure_form2.py

It predicts one form: form 2 (third person, indicative, perfective) from the
headword, the verb class and the preverb. Its rules were worked out from the
form 2 of every dictionary verb, so the dictionary cannot give it an unseen
test. Two things are reported apart:

  SEEN     the 2,197 verbs its own --validate scores (one printed form 2)
  NOT SCORED BEFORE   the verbs whose form 2 is printed in two versions with a
           comma. The engine's validation leaves them out, so its rules were
           never adjusted on them. They are few and not typical (a verb with
           two printed forms is irregular by nature); they are the only form
           2s the rules have not been fitted to.

Also: what the stored "confidence" is worth as a sign that the prediction is right.

Nothing is changed. Writes data/form2.jsonl and data/form2_summary.json.
"""
from collections import Counter, defaultdict

from common import (CAUSES, DATA, TESTSETS, classify, connect, group_of, out, pct, read_jsonl, write_json,
                    write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

import stem_extractor as se  # noqa: E402


def class_group(gc):
    first = (gc or "").replace(" ", "").split(",")[0].split("(")[0]
    return {"VI": "VI active intransitive", "VT": "VT active transitive", "VD": "VD descriptive",
            "VL": "VL locative", "VP": "VP passive", "VR": "VR reflexive"}.get(first, "other")


def run():
    conn = connect()
    conf = {r[0]: r[1] for r in conn.execute("select entry_id, form2_confidence from lexical_entries")}
    conn.close()
    rows = []
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        if f["form_number"] != 2:
            continue
        predicted, debug = se.predict_form_2(f["headword"], f["verb_class"] or "", f["stem_preverb"] or "",
                                             f["grammatical_class"] or "")
        cause, compared = classify(predicted, f["variants"])
        c = conf.get(f["entry_id"])
        rows.append({
            "entry_id": f["entry_id"], "headword": f["headword"], "grammatical_class": f["grammatical_class"],
            "class_group": class_group(f["grammatical_class"]), "verb_class": f["verb_class"],
            "stem_preverb": f["stem_preverb"], "printed": f["printed"], "predicted": predicted,
            "compared_with": compared, "cause": cause,
            "scored_by_the_engines_own_validation": "," not in f["printed"],
            "headword_has_notation": any(ch in f["headword"] for ch in "/()[] ,-"),
            "stored_confidence": c,
            "stored_band": None if c is None else ("high" if c >= 0.75 else "medium" if c >= 0.5 else "low"),
        })
    return rows


def block(sel):
    c = Counter(r["cause"] for r in sel)
    g = Counter(group_of(r["cause"]) for r in sel)
    return {"verbs": len(sel), "exact": c["exact"], "by_cause": {k: c[k] for k in CAUSES if c[k]}, "groups": dict(g)}


def main():
    rows = run()
    write_jsonl(DATA / "form2.jsonl", rows)
    seen = [r for r in rows if r["scored_by_the_engines_own_validation"]]
    not_scored = [r for r in rows if not r["scored_by_the_engines_own_validation"]]
    s = {"all": block(rows), "seen": block(seen), "not_scored_before": block(not_scored)}
    s["by_class_group"] = {g: block([r for r in rows if r["class_group"] == g]) for g in sorted({r["class_group"] for r in rows})}
    s["by_verb_class"] = {str(v): block([r for r in rows if r["verb_class"] == v])
                          for v in sorted({r["verb_class"] for r in rows}, key=str)}
    s["by_preverb"] = {str(pv): block([r for r in rows if r["stem_preverb"] == pv])
                       for pv, n in Counter(r["stem_preverb"] for r in rows).most_common(8)}
    s["plain_headwords"] = block([r for r in rows if not r["headword_has_notation"]])
    s["headwords_with_notation"] = block([r for r in rows if r["headword_has_notation"]])
    by_band = defaultdict(list)
    for r in rows:
        by_band[r["stored_band"]].append(r)
    s["stored_confidence_band"] = {str(b): {"verbs": len(v), "exact": sum(x["cause"] == "exact" for x in v)}
                                   for b, v in by_band.items()}
    write_json(DATA / "form2_summary.json", s)
    for name in ("all", "seen", "not_scored_before"):
        b = s[name]
        out("%-18s %4d of %4d exact (%s)  %s" % (name, b["exact"], b["verbs"], pct(b["exact"], b["verbs"]), b["by_cause"]))
    for g, b in s["by_class_group"].items():
        out("   %-24s %4d of %4d exact (%s)" % (g, b["exact"], b["verbs"], pct(b["exact"], b["verbs"])))
    for g, b in s["by_preverb"].items():
        out("   preverb %-22s %4d of %4d exact (%s)" % (g, b["exact"], b["verbs"], pct(b["exact"], b["verbs"])))
    out("   plain headwords %(exact)d of %(verbs)d" % s["plain_headwords"]
        + "; with notation %(exact)d of %(verbs)d" % s["headwords_with_notation"])
    out("   stored confidence band: %s" % s["stored_confidence_band"])


if __name__ == "__main__":
    main()
