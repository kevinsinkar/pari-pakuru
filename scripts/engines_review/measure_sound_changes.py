#!/usr/bin/env python3
"""Stage 2: the sound-change engine, measured on Parks's own examples.

    python scripts/engines_review/measure_sound_changes.py

Two sets, both Parks's own division of a word into pieces with the word it
gives:

  chapter 3   the 39 examples he prints with the 24 rules
  chapter 4   his 93 worked examples in the grammatical overview

For each, the pieces are handed to

  a. sound_changes.apply_sound_changes      the full engine (restricted rules, then general ones)
  b. sound_changes.apply_unrestricted_rules the half the conjugation engine uses, on the joined pieces
  c. morphology_v2/seams.derive             the seam engine of the word-construction analysis, which
                                            returns every form its named rules allow

An engine is right when what it gives is the printed word. For (c) two things
are counted: whether the printed word is among the forms it allows, and
whether it is the single form with the fewest optional rules.

Nothing is changed. Writes data/sound_changes.jsonl and data/sound_changes_summary.json.
"""
import logging
from collections import Counter

from common import (CAUSES, DATA, TESTSETS, classify_one, clean, edit_distance, out, pct, read_jsonl, strip_accents,
                    write_json, write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

logging.disable(logging.CRITICAL)
import seams  # noqa: E402   (scripts/morphology_v2)
import sound_changes as sc  # noqa: E402


def undo_rule_17_inside(produced, printed):
    """If the only difference is c where the page has s, the general rule fired inside a piece."""
    if len(produced) != len(printed):
        return False
    diff = [(a, b) for a, b in zip(produced, printed) if a != b]
    return bool(diff) and all(a == "c" and b == "s" for a, b in diff)


def named_fault(produced, printed, pieces):
    """A plain name for the commonest ways the full engine misses. Attribution only: nothing is repaired."""
    p, b = strip_accents(clean(produced)), strip_accents(printed)
    if p == b:
        return None
    if undo_rule_17_inside(p, b):
        return "s made into c inside a piece (rule 17 applied where there is no boundary)"
    if p.endswith("k") and p[:-1] + "t" == b:
        return "final k of the perfective not made into t (not one of the 24 rules)"
    if p + "ʔ" == b:
        return "final ʔ of a non-subordinate form not added (not one of the 24 rules)"
    if p.endswith("s") and p[:-1] == b or p.endswith("s") and p[:-1] + "ʔ" == b:
        return "final s not dropped (rule 9R, which the engine applies only when told)"
    if any(":" in x for x in pieces):
        return "a length mark in Parks's pieces (-:hus) that the engine cannot read"
    return "other"


# Chapter 4 examples whose pieces and word do not belong together in the gold file
# (curriculum/roots_v2/gold/g1_go_examples.json), found by reading all 93 beside Parks's
# analysis. They are left out for every engine alike.
TWO_ANALYSES_RUN_TOGETHER = {
    "asaaki": "the line holds two analyses (asaaki and riiciki); the pieces of both were joined",
    "siwitirakuutiirit": "the line holds two analyses; the pieces of both were joined",
}


def why_left_out(ex, pieces, surface):
    """None when the example can be used. The test is the same for every engine and uses none of them."""
    if ex.get("flags"):
        return "flagged in the gold file: " + ", ".join(ex["flags"])
    if not all(p and all(ch.isalpha() or ch == "ʔ" for ch in p) for p in pieces):
        return "a piece is not a plain form"
    if surface in TWO_ANALYSES_RUN_TOGETHER:
        return TWO_ANALYSES_RUN_TOGETHER[surface]
    joined = "".join(pieces)
    if edit_distance(surface, joined) > 0.6 * len(joined):
        return "the word listed is not the word these pieces make (it is another word of the same example)"
    return None


def run(examples, set_name):
    rows = []
    for ex in examples:
        pieces = [p.replace(":", "") for p in ex["pieces"]]
        surface = clean(ex["surface"].rstrip("."))
        row = {"set": set_name, "pieces": ex["pieces"], "printed": surface,
               "rule": ex.get("rule"), "page": ex.get("page"), "flags": ex.get("flags", []),
               "has_length_mark": ex.get("has_length_mark", False)}
        reason = why_left_out(ex, pieces, surface)
        row["used"] = reason is None
        if reason:
            row["left_out_because"] = reason
            rows.append(row)
            continue
        full = sc.apply_sound_changes(pieces)
        full_s = sc.apply_sound_changes(pieces, final_s_loss=True)
        half = sc.apply_unrestricted_rules("".join(pieces)).replace(sc.KS_MARKER, "")
        plain = "".join(pieces)
        allowed = seams.derive(pieces, word_like=True)
        ranked = sorted(allowed.items(), key=lambda kv: (sum(seams.RULES[r]["optional"] for r in kv[1]), len(kv[1]), kv[0]))
        best_cost = (sum(seams.RULES[r]["optional"] for r in ranked[0][1]), len(ranked[0][1])) if ranked else None
        best = [s for s, rl in ranked if (sum(seams.RULES[r]["optional"] for r in rl), len(rl)) == best_cost]
        row.update({
            "full_engine": full, "full_engine_cause": classify_one(full, surface),
            "full_engine_told_to_drop_final_s": full_s, "full_engine_told_cause": classify_one(full_s, surface),
            "general_rules_only": half, "general_rules_only_cause": classify_one(half, surface),
            "pieces_just_joined": plain, "pieces_just_joined_cause": classify_one(plain, surface),
            "seam_engine_allows": len(allowed), "seam_engine_has_the_printed_form": surface in allowed,
            "seam_engine_first_choice": best, "seam_engine_first_choice_is_the_printed_form": best == [surface],
            "seam_engine_rules_for_it": allowed.get(surface),
        })
        if row["full_engine_cause"] != "exact":
            row["fault"] = named_fault(full, surface, ex["pieces"])
        rows.append(row)
    return rows


def summarise(rows):
    used = [r for r in rows if r["used"]]

    def causes(key):
        c = Counter(r[key] for r in used)
        return {k: c[k] for k in CAUSES if c[k]}

    s = {
        "examples": len(rows), "used": len(used),
        "left_out": len(rows) - len(used),
        "left_out_why": dict(Counter(r["left_out_because"] for r in rows if not r["used"])),
        "full_engine_exact": sum(r["full_engine_cause"] == "exact" for r in used),
        "full_engine_exact_or_exact_when_told_to_drop_final_s": sum(
            r["full_engine_cause"] == "exact" or r["full_engine_told_cause"] == "exact" for r in used),
        "full_engine_by_cause": causes("full_engine_cause"),
        "general_rules_only_exact": sum(r["general_rules_only_cause"] == "exact" for r in used),
        "pieces_just_joined_exact": sum(r["pieces_just_joined_cause"] == "exact" for r in used),
        "full_engine_faults": dict(Counter(r["fault"] for r in used if r.get("fault"))),
        "seam_engine_has_the_printed_form": sum(r["seam_engine_has_the_printed_form"] for r in used),
        "seam_engine_first_choice_is_the_printed_form": sum(r["seam_engine_first_choice_is_the_printed_form"] for r in used),
        "seam_engine_forms_allowed_per_word": {
            "median": sorted(r["seam_engine_allows"] for r in used)[len(used) // 2] if used else 0,
            "largest": max((r["seam_engine_allows"] for r in used), default=0)},
    }
    return s


def main():
    c3 = run(read_jsonl(TESTSETS / "chapter3_examples.jsonl"), "chapter 3")
    c4 = run(read_jsonl(TESTSETS / "chapter4_examples.jsonl"), "chapter 4")
    write_jsonl(DATA / "sound_changes.jsonl", c3 + c4)
    summary = {"chapter3": summarise(c3), "chapter4": summarise(c4)}
    # chapter 3 without the four examples the engine's own test already holds
    tested = {(tuple(r["pieces"]), r["surface"]) for r in read_jsonl(TESTSETS / "chapter3_examples.jsonl")
              if r["is_one_of_the_engines_own_tests"]}
    unseen3 = [r for r in c3 if (tuple(r["pieces"]), r["printed"]) not in tested]
    summary["chapter3_without_the_engines_own_four_tests"] = summarise(unseen3)
    by_rule = {}
    for r in c3:
        if r["used"]:
            b = by_rule.setdefault(r["rule"], {"examples": 0, "full_engine_exact": 0, "seam_engine_has_it": 0})
            b["examples"] += 1
            b["full_engine_exact"] += r["full_engine_cause"] == "exact"
            b["seam_engine_has_it"] += r["seam_engine_has_the_printed_form"]
    summary["chapter3_by_rule"] = by_rule
    write_json(DATA / "sound_changes_summary.json", summary)
    for name in ("chapter3", "chapter3_without_the_engines_own_four_tests", "chapter4"):
        s = summary[name]
        out("%s: %d examples, %d used" % (name, s["examples"], s["used"]))
        out("   full engine exact %d (%s); also when told to drop final s %d; general rules only %d; pieces just joined %d"
            % (s["full_engine_exact"], pct(s["full_engine_exact"], s["used"]),
               s["full_engine_exact_or_exact_when_told_to_drop_final_s"], s["general_rules_only_exact"],
               s["pieces_just_joined_exact"]))
        out("   full engine by cause: %s" % s["full_engine_by_cause"])
        out("   faults: %s" % s["full_engine_faults"])
        out("   seam engine: printed form among those allowed %d (%s); its first choice %d; forms allowed per word: median %d, largest %d"
            % (s["seam_engine_has_the_printed_form"], pct(s["seam_engine_has_the_printed_form"], s["used"]),
               s["seam_engine_first_choice_is_the_printed_form"],
               s["seam_engine_forms_allowed_per_word"]["median"], s["seam_engine_forms_allowed_per_word"]["largest"]))
    out("by rule (chapter 3): %s" % summary["chapter3_by_rule"])


if __name__ == "__main__":
    main()
