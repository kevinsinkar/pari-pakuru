#!/usr/bin/env python3
"""Single entry point: regenerate every data output of the v2 morphology pipeline.

    python scripts/morphology_v2/run.py                # data files (phases 2-4)
    python scripts/morphology_v2/run.py --guide        # ... and the Markdown guides (phase 6)
    python scripts/morphology_v2/run.py --validate     # ... and the validation report (phase 5)
    python scripts/morphology_v2/run.py --all          # everything
    python scripts/morphology_v2/run.py --hashes       # print SHA-256 of every output (determinism check)

Outputs go to curriculum/roots_v2/.  The database is opened read-only.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analysis import analyse  # noqa: E402
from common import OUT, connect, dump_json, dump_jsonl, out, sha256  # noqa: E402
from inventory import build_inventory, coverage_curve, decodability, needs_community_review  # noqa: E402
from ordering import WEIGHTS, learning_order, sensitivity, teachable_keys  # noqa: E402
import seams  # noqa: E402

DATA_FILES = ["evidence.jsonl", "roots.json", "affixes.json", "decisions.json", "coverage.json", "stats.json"]
GUIDE_FILES = ["construction_guide.md", "learning_path.md", "review_queue.md"]


def _slim_record(r):
    keep = dict(r)
    keep.pop("_forms", None)
    return keep


def build(conn):
    res = analyse(conn)
    lex_by_id = {lex["lexeme_id"]: lex for lex in res["lexemes"]}
    for r in res["records"]:
        r["needs_community_review"] = needs_community_review(lex_by_id[r["lexeme_id"]])
    inv = build_inventory(res, conn)
    need = decodability(res, inv)
    order, usable = learning_order(need, inv, res)
    curve = coverage_curve(order, usable, res, inv)
    # a frequency-only order, for comparison
    keys = teachable_keys(inv)
    freq_order = sorted(keys, key=lambda k: (-keys[k]["type_frequency"]["A+B"], k))
    freq_curve = coverage_curve(freq_order, usable, res, inv)
    sens = sensitivity(need, inv, res, order)
    return res, inv, need, usable, order, curve, freq_curve, sens


def write_data(conn):
    res, inv, need, usable, order, curve, freq_curve, sens = build(conn)
    records = res["records"]
    dump_jsonl(OUT / "evidence.jsonl", [_slim_record(r) for r in records])
    dump_json(OUT / "roots.json", {"n": len(inv["roots"]), "roots": inv["roots"]})
    dump_json(OUT / "affixes.json", {"n": len(inv["affixes"]), "affixes": inv["affixes"],
                                     "inflectional": inv["inflection"],
                                     "parks_tables": {
                                         "file": "extracted_data/grammatical_overview_tables.json",
                                         "tables": [t["number"] for t in inv["parks_tables"]],
                                         "note": "Parks's own tables of the verb are not copied here; "
                                                 "the guide prints them from that file"},
                                     "seam_rules": {k: dict(v, id=k) for k, v in sorted(seams.RULES.items())}})
    dump_json(OUT / "decisions.json", {"n": len(inv["decisions"]), "decisions": inv["decisions"]})
    marks = [10, 20, 30, 40, 50, 75, 100, 150, 200, 300, 400, 500, len(curve)]
    dump_json(OUT / "coverage.json", {
        "weights": WEIGHTS, "teachable_morphemes": len(order), "words_analysable": len(usable),
        "words_in_dictionary": len(records),
        "blue_book_words_reliably_linked": len(inv["bb_first"]),
        "example_sentences": inv["total_examples"],
        "order": order, "curve": curve,
        "milestones": [curve[m - 1] for m in marks if 0 < m <= len(curve)],
        "frequency_only_milestones": [freq_curve[m - 1] for m in marks if 0 < m <= len(freq_curve)],
        "sensitivity": sens})
    from collections import Counter
    tiers = Counter(r["tier"] or "no claim" for r in records)
    stats = {
        "rows": sum(len(r["member_ids"]) for r in records), "lexemes": len(records),
        "lexeme_tiers": dict(sorted(tiers.items())),
        "e1": dict(sorted(Counter(r["e1"] or "none" for r in records).items())),
        "e2": dict(sorted(Counter(r["e2"]["status"] or "none" for r in records if r["e1"]).items())),
        "e2_methods": dict(sorted(Counter(r["e2"]["method"] or "none" for r in records if r["e1"] == "printed").items())),
        "e3": dict(sorted(Counter(r["e3"] or "none" for r in records if r["e1"]).items())),
        "e3b": dict(sorted(Counter((r["e3b"] or {}).get("status") or "not tested" for r in records).items())),
        "e5": dict(sorted(Counter(r["e5"] or "none" for r in records if r["e1"]).items())),
        "seam_rule_use": dict(sorted(Counter(x for r in records if r["e1"] == "printed" and r["e2"]["status"] == "exact"
                                             for x in set(r["e2"]["rules"])).items())),
        "blue_book_seams": res["seam_counts"], "compound_stem_units": res["group_stats"],
        "lexical_morphemes": len(inv["roots"]),
        "lexical_morpheme_tiers": dict(sorted(Counter(r["tier"] for r in inv["roots"]).items())),
        "affixes": len(inv["affixes"]),
        "affix_tiers": dict(sorted(Counter(a["tier"] for a in inv["affixes"]).items())),
        "classes_AB": dict(sorted(Counter(r["class"] for r in inv["roots"] if r["tier"] in ("A", "B")).items())),
        "decisions": dict(sorted(Counter(d["type"] for d in inv["decisions"]).items())),
        "words_needing_community_review": sum(1 for r in records if r["needs_community_review"]),
    }
    # Parks says there are "approximately one hundred" basic verb roots (GO p. 31): how many are here?
    rec_by_id = {r["lexeme_id"]: r for r in records}
    vr = Counter()
    for r in inv["roots"]:
        if r["tier"] not in ("A", "B") or not r["class"].startswith("verb root"):
            continue
        own = r["evidence"]["own_dictionary_entries"]
        if not own:
            vr["bound, no entry of its own"] += 1
        elif any(rec_by_id[o]["e1"] == "printed" and len(rec_by_id[o]["pieces"]) > 1 for o in own):
            vr["derived stem (its own entry is analysed by Parks)"] += 1
        else:
            vr["basic root (its own entry is unanalysed)"] += 1
    stats["verb_roots_AB"] = dict(sorted(vr.items()))
    dump_json(OUT / "stats.json", stats)
    return res, inv, need, usable, order, curve, sens, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--guide", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--hashes", action="store_true")
    args = ap.parse_args()
    if args.hashes:
        for f in DATA_FILES + GUIDE_FILES:
            p = OUT / f
            out("%s  %s" % (sha256(p)[:16] if p.exists() else "(missing)       ", f))
        return
    conn = connect()
    bundle = write_data(conn)
    stats = bundle[-1]
    out("lexemes %d  tiers %s" % (stats["lexemes"], stats["lexeme_tiers"]))
    out("lexical morphemes %d %s ; affixes %d %s" % (stats["lexical_morphemes"], stats["lexical_morpheme_tiers"],
                                                    stats["affixes"], stats["affix_tiers"]))
    if args.guide or args.all:
        import guide
        guide.write_guides(conn, bundle)
        out("guides written")
    if args.validate or args.all:
        import report
        report.write_reports(conn, bundle)
        out("validation report written")


if __name__ == "__main__":
    main()
