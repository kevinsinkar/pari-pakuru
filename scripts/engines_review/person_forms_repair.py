#!/usr/bin/env python3
"""Decision 6 of the engines review: the sealed test of the repaired person derivation.

The owner chose the narrow repair of scripts/person_forms.py, "measured on a
sealed half". The test is the one of Stage 2: the question form the engine
gives for "he/she" (the absolutive, made from the printed form 2) against the
start of the dictionary's printed form 4, for every verb that prints one form
2 and one form 4 of the shape irii- + r… (2,124 verbs).

The verbs are split in two by a rule fixed beforehand: the last digit of the
number that ends the entry's id. Odd: the OPEN half, which may be looked at
and from which rules may be read. Even: the SEALED half, which is not opened
until the code is finished, and then once.

    python scripts/engines_review/person_forms_repair.py --write-split [--seen FILE]
        once, BEFORE person_forms.py is changed: writes data/person_forms_split.json
    python scripts/engines_review/person_forms_repair.py --open [--rows TEXT]
        the engine as it stands, on the open half only: by rule; --rows lists the open verbs whose rule
        name or form 2 begins with TEXT
    python scripts/engines_review/person_forms_repair.py --explore START
        open half only: how form 4 begins for the verbs whose form 2 begins with START, by a few features
    python scripts/engines_review/person_forms_repair.py --sealed
        once, when the code is finished: writes data/person_forms_sealed_result.json

Nothing here changes the engine, the database or a data file.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DATA, ROOT, TESTSETS, clean, no_glottal, out, read_jsonl, short_vowels, strip_accents  # noqa: E402

import person_forms as pf  # noqa: E402

SPLIT = DATA / "person_forms_split.json"
RESULT = DATA / "person_forms_sealed_result.json"
ENGINE = ROOT / "scripts" / "person_forms.py"
BAR = 97.0          # per cent of the verbs a form is given for, fixed in the decision paper


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gerundial_body(form4):
    """Form 4 without its irii-: what is left begins with the absolutive prefix. As in Stage 2."""
    f = clean(form4)
    if not f.startswith("iri"):
        return None
    rest = f[3:]
    if rest.startswith("i"):
        rest = rest[1:]
    return rest if rest.startswith("r") else None


def compare_edge(derived, form2, body):
    """Does the body of form 4 start as the derived form starts? As in Stage 2: the zone compared is what the
    engine changed at the start of form 2, and the two letters after it."""
    d, f2 = clean(derived), clean(form2)
    i = 0
    while i < min(len(d), len(f2)) and d[-1 - i] == f2[-1 - i]:
        i += 1
    zone = d[:len(d) - i + 2]
    for label, fn in (("the same", lambda x: x), ("vowel length", short_vowels), ("glottal stop", no_glottal),
                      ("vowel length and glottal stop", lambda x: short_vowels(no_glottal(x)))):
        if fn(body).startswith(fn(zone)):
            return label
    return "other letters"


def tested_verbs():
    """The verbs of the Stage 2 test, in the order of their entry ids."""
    by_entry = defaultdict(dict)
    for f in read_jsonl(TESTSETS / "dictionary_forms.jsonl"):
        by_entry[f["entry_id"]][f["form_number"]] = f
    rows = []
    for eid, forms in sorted(by_entry.items()):
        if 2 not in forms or 4 not in forms:
            continue
        f2v, f4v = forms[2]["variants"], forms[4]["variants"]
        if len(f2v) != 1 or len(f4v) != 1:
            continue
        body = gerundial_body(f4v[0])
        if body is None:
            continue
        m = forms[2]
        rows.append({"entry_id": eid, "headword": m["headword"], "grammatical_class": m["grammatical_class"],
                     "stem_preverb": m["stem_preverb"], "form_2": f2v[0], "form_4": f4v[0], "body": body,
                     "half": half_of(eid)})
    return rows


def half_of(entry_id):
    number = re.search(r"(\d+)\D*$", entry_id)
    return "open" if int(number.group(1)[-1]) % 2 == 1 else "sealed"


PLAN = DATA / "person_forms_plan.json"
POLICIES = ("narrow", "strict")          # the two configurations fixed in the plan before the sealed half was opened


def judge(row, policy=None):
    """(rule name the engine reports, form given or None, result)."""
    rule, derived = pf.third_person_question_form(row["form_2"], stem_preverb=row["stem_preverb"],
                                                  headword=row["headword"], policy=policy)
    if derived is None:
        return rule, None, "no form given"
    return rule, derived, compare_edge(derived, row["form_2"], row["body"])


def table(rows, policy=None):
    """Counts by rule, and the totals the bar is measured on."""
    by_rule = defaultdict(Counter)
    for r in rows:
        rule, derived, result = judge(r, policy)
        by_rule[rule][result] += 1
    given = sum(n for c in by_rule.values() for k, n in c.items() if k != "no form given")
    same = sum(c["the same"] for c in by_rule.values())
    return by_rule, {"verbs": len(rows), "a_form_is_given_for": given, "declined": len(rows) - given,
                     "starts_as_form_4_starts": same,
                     "per_cent_of_forms_given": round(100.0 * same / given, 2) if given else None}


def show(by_rule, totals, title):
    out(title)
    for rule, c in sorted(by_rule.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        given = n - c["no form given"]
        rate = ("%5.1f%%" % (100.0 * c["the same"] / given)) if given else "   –  "
        out("  %-62s %4d verbs, form for %4d, the same %4d (%s)  %s" % (
            rule[:62], n, given, c["the same"], rate, {k: v for k, v in c.items() if k not in ("the same",)} or ""))
    out("  TOTAL: %(verbs)d verbs; a form is given for %(a_form_is_given_for)d, declined %(declined)d; "
        "starts as form 4 starts: %(starts_as_form_4_starts)d = %(per_cent_of_forms_given)s%% of the forms given" % totals)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write-split", action="store_true")
    ap.add_argument("--seen", help="file with one entry id per line: verbs displayed before the split was written")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--rows", help="with --open: list the open verbs whose rule or form 2 begins with this text")
    ap.add_argument("--explore", help="open half: how form 4 begins where form 2 begins with this text")
    ap.add_argument("--sealed", action="store_true")
    args = ap.parse_args()
    rows = tested_verbs()

    if args.write_split:
        if SPLIT.exists():
            raise SystemExit("the split is already written: %s" % SPLIT.relative_to(ROOT).as_posix())
        seen = set()
        if args.seen:
            seen = {line.strip() for line in Path(args.seen).read_text(encoding="utf-8").splitlines() if line.strip()}
        record = {
            "what": "the split of the verbs of the Stage 2 test into an open and a sealed half, written before "
                    "scripts/person_forms.py was changed",
            "written": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "rule": "the last digit of the number that ends the entry's id: odd = open, even = sealed",
            "person_forms_py_sha256_when_written": sha(ENGINE),
            "verbs": len(rows),
            "open": sorted(r["entry_id"] for r in rows if r["half"] == "open"),
            "sealed": sorted(r["entry_id"] for r in rows if r["half"] == "sealed"),
            "sealed_but_displayed_before_the_split": sorted(r["entry_id"] for r in rows
                                                            if r["half"] == "sealed" and r["entry_id"] in seen),
            "bar": "on the sealed half the form given starts as form 4 starts for at least %s%% of the verbs a "
                   "form is given for; the share declined is reported beside it" % BAR,
            "what_was_already_known_of_the_sealed_half": [
                "Stage 2 of the review measured the engine on all these verbs together, before any split. Its "
                "counts by rule, over both halves, are in person_forms_summary.json and in measurements.md "
                "(ti- to ra- 925 of 939; tih- with a stem in h- 187 of 190; tu- to ru- 325 of 339; tiʔ- to raʔ- "
                "37 of 48; tii- to rii- 29 of 352; tuu- to ru- 0 of 109; tih- to riih- 0 of 4; no form 143). "
                "The decision to take out three rules rests on those counts.",
                "Rows of single verbs were printed during Stage 2 as examples. Every sealed verb whose entry "
                "id or form 4 occurs anywhere in the record of the working session up to the moment of the "
                "split is listed under sealed_but_displayed_before_the_split. They are reported apart.",
                "No rule of the repair is read from the sealed half, and no row of it is looked at between "
                "the split and the one run of --sealed.",
            ],
        }
        with open(SPLIT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(record, f, ensure_ascii=False, indent=1)
            f.write("\n")
        out("split written: %d verbs; open %d, sealed %d (of the sealed, %d were displayed before)" % (
            len(rows), len(record["open"]), len(record["sealed"]), len(record["sealed_but_displayed_before_the_split"])))
        return 0

    if not SPLIT.exists():
        raise SystemExit("write the split first (--write-split)")
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    open_ids, sealed_ids = set(split["open"]), set(split["sealed"])
    if {r["entry_id"] for r in rows} != open_ids | sealed_ids:
        raise SystemExit("the verbs of the test are not those of the split: the test set was changed")

    if args.open or args.explore:
        mine = [r for r in rows if r["entry_id"] in open_ids]
        if args.explore:
            start = args.explore
            group = [r for r in mine if strip_accents(r["form_2"]).startswith(start)]
            out("open half: %d verbs whose form 2 begins %s-" % (len(group), start))
            for name, key in (("form 4 begins (4 letters)", lambda r: r["body"][:4]),
                              ("form 4 begins (3) / headword begins (1)", lambda r: "%s / %s" % (r["body"][:3], strip_accents(r["headword"])[:1])),
                              ("form 4 begins (3) / preverb", lambda r: "%s / %s" % (r["body"][:3], r["stem_preverb"] or "none")),
                              ("form 4 begins (3) / class", lambda r: "%s / %s" % (r["body"][:3], r["grammatical_class"]))):
                out("  by %s:" % name)
                for k, n in Counter(key(r) for r in group).most_common(24):
                    out("     %-28s %d" % (k, n))
            return 0
        for policy in POLICIES:
            by_rule, totals = table(mine, policy)
            show(by_rule, totals, "THE OPEN HALF (%d verbs), configuration '%s', engine file %s" % (
                len(mine), policy, sha(ENGINE)[:12]))
        if args.rows:
            for r in mine:
                rule, derived, result = judge(r)
                if rule.startswith(args.rows) or strip_accents(r["form_2"]).startswith(args.rows):
                    out("    %-22s %-8s %-12s form 2 %-22s form 4 %-28s given %-20s %s" % (
                        r["headword"][:22], r["grammatical_class"], r["stem_preverb"] or "", r["form_2"], r["form_4"],
                        derived, result))
        return 0

    if args.sealed:
        if RESULT.exists():
            raise SystemExit("the sealed half was already opened: %s. It is opened once." % RESULT.relative_to(ROOT).as_posix())
        if not PLAN.exists():
            raise SystemExit("write the plan first: %s" % PLAN.relative_to(ROOT).as_posix())
        mine = [r for r in rows if r["entry_id"] in sealed_ids]
        shown = set(split["sealed_but_displayed_before_the_split"])
        clean_rows = [r for r in mine if r["entry_id"] not in shown]
        record = {
            "what": "the one run of the repaired person derivation on the sealed half, for the two configurations "
                    "fixed in person_forms_plan.json",
            "run": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "person_forms_py_sha256": sha(ENGINE),
            "person_forms_py_sha256_when_the_split_was_written": split["person_forms_py_sha256_when_written"],
            "plan_sha256": sha(PLAN),
            "bar_per_cent": BAR,
            "configurations": {},
        }
        for policy in POLICIES:
            by_rule, totals = table(mine, policy)
            _, totals_clean = table(clean_rows, policy)
            _, totals_open = table([r for r in rows if r["entry_id"] in open_ids], policy)
            passes = totals["per_cent_of_forms_given"] is not None and totals["per_cent_of_forms_given"] >= BAR
            record["configurations"][policy] = {
                "sealed_half": totals,
                "sealed_half_without_the_verbs_displayed_before_the_split": totals_clean,
                "open_half_for_comparison": totals_open,
                "reaches_the_bar": passes,
                "by_rule": {rule: dict(c) for rule, c in sorted(by_rule.items())},
            }
            show(by_rule, totals, "THE SEALED HALF (%d verbs), opened once: configuration '%s'" % (len(mine), policy))
            out("  without the %d verbs displayed before the split: %s" % (len(mine) - len(clean_rows), totals_clean))
            out("  the open half, for comparison: %s" % totals_open)
            out("  bar: %s%% of the forms given. %s" % (BAR, "REACHED" if passes else "NOT reached"))
        record["ships"] = "narrow" if record["configurations"]["narrow"]["reaches_the_bar"] else "strict"
        out("by the rule of the plan, the configuration that ships is: %s" % record["ships"])
        with open(RESULT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(record, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
