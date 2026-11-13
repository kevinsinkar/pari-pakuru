#!/usr/bin/env python3
"""Score the pipeline against the gold sets.

G2 (hand-checked page transcriptions) is the main test.  For each gold entry the
annotator recorded what the page prints; a pipeline analysis is *correct* when
its ordered list of pieces equals the printed etymology's pieces.  The held-out
half is scored only when `split="heldout"` is passed explicitly.
"""
import math
import re
from collections import Counter, defaultdict

from analysis import gloss_stems
from common import GOLD, load_json, norm, strip_accents
from etymology import PREVERB_NOTE, clean_form, optional_variants


def wilson(k, n, z=1.96):
    """Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def gold_pieces(ann):
    """The annotator's piece list as flat comparable forms (dots split, notes removed)."""
    flat = []
    for piece in ann.get("pieces") or []:
        piece = norm(piece).replace("-|", "")
        piece = re.sub(r"\[[^\]]*\]", " ", piece)
        piece = re.sub(r"\(([a-z .]+)\)", lambda m: "(" + m.group(1).replace(" ", "") + ")", piece)
        piece = PREVERB_NOTE.sub("", piece)
        piece = piece.replace("?", " ")
        piece = re.sub(r"-\s+(?=[a-zʔ])", "", piece.strip())
        for word in piece.split():
            for sub in word.split("."):
                sub = sub.replace("-", "").strip()
                if not sub:
                    continue
                full, _ = optional_variants(sub)
                f = clean_form(full)
                if f:
                    flat.append(f)
    return flat


def _class_key(c, vc):
    c = re.sub(r"\s+", "", (c or "")).upper()
    vc = re.sub(r"\s+", "", (vc or ""))
    return c, vc


def _clean_word(s):
    return re.sub(r"[^a-zʔø]", "", strip_accents(norm(s or "")).lower())


def score_g2(records, split):
    """Score one half of G2.  Returns a dict of counts plus per-entry rows."""
    anns = [a for a in load_json(GOLD / "g2_annotations.json")["annotations"] if a["split"] == split]
    by_member = {}
    for r in records:
        for m in r["member_ids"]:
            by_member[m] = r
    rows = []
    for a in anns:
        r = by_member.get(a["entry_id"])
        row = {"entry_id": a["entry_id"], "headword": a.get("printed_headword"), "tier": r["tier"] if r else None,
               "tier_without_e5": r.get("tier_without_e5") if r else None, "kind": a.get("etymology_kind")}
        if r is None or not a.get("found"):
            row["status"] = "not_found"
            rows.append(row)
            continue
        # is the annotator's entry the same homograph as the database row?
        same_class = _class_key(a.get("printed_class"), a.get("printed_verb_class")) == _class_key(r["class"], r["verb_class"])
        hw_a = _clean_word((a.get("printed_headword") or "").split(",")[0].split("(")[0].split("[")[0])
        hw_r = _clean_word(r["headword"].split(",")[0].split("(")[0].split("[")[0])
        row["extraction"] = {"headword_matches": hw_a == hw_r, "class_matches": same_class}
        gold = gold_pieces(a) if a.get("etymology_kind") == "analysis" else []
        mine = [p["form"] for p in r["pieces"]]
        row["gold_pieces"], row["pipeline_pieces"] = gold, mine
        # paradigm forms as a further extraction check
        pf_ok = None
        if a.get("paradigm_forms"):
            pf_ok = True
            for k, v in a["paradigm_forms"].items():
                got = None
                for rec in (r,):
                    got = rec.get("_forms", {}).get(k)
                if got is not None and _clean_word(got) != _clean_word(v):
                    pf_ok = False
        row["extraction"]["paradigm_matches"] = pf_ok
        if a.get("etymology_kind") is None:
            row["status"] = "gold_incomplete"
        elif hw_a != hw_r:
            row["status"] = "different_headword"
        elif a.get("etymology_kind") != "analysis":
            row["status"] = "gold_undetermined" if r["e1"] else "agree_no_claim"
        elif r["e1"] != "printed":
            row["status"] = "missed_analysis"
        elif gold == mine:
            row["status"] = "correct"
        else:
            row["status"] = "wrong"
        # piece meanings, where the page aligns a gloss with a piece
        agree = disagree = 0
        if row["status"] == "correct" and a.get("aligned_glosses"):
            ag = [g for g in a["aligned_glosses"] if g.get("gloss")]
            flat_gold = []
            for g in ag:
                for f in gold_pieces({"pieces": [g["piece"]]}):
                    flat_gold.append((f, g["gloss"]))
            for f, gl in flat_gold:
                for p in r["pieces"]:
                    if p["form"] == f:
                        mine_gl = p.get("gloss") or p.get("label") or ""
                        if gl.strip().upper() == (mine_gl or "").strip().upper() or (
                                gloss_stems(gl) & gloss_stems(mine_gl)):
                            agree += 1
                        else:
                            disagree += 1
                        break
        row["gloss_agree"], row["gloss_disagree"] = agree, disagree
        rows.append(row)
    summary = defaultdict(Counter)
    for row in rows:
        summary[row["tier"] or "none"][row["status"]] += 1
    precision = {}
    for tier in ("A", "B", "C"):
        c = summary[tier]
        n = c["correct"] + c["wrong"]
        lo, hi = wilson(c["correct"], n)
        precision[tier] = {"correct": c["correct"], "scored": n,
                           "precision": round(c["correct"] / n, 4) if n else None,
                           "ci95": [round(lo, 3), round(hi, 3)]}
    ab = summary["A"] + summary["B"]
    n = ab["correct"] + ab["wrong"]
    lo, hi = wilson(ab["correct"], n)
    precision["A+B"] = {"correct": ab["correct"], "scored": n,
                        "precision": round(ab["correct"] / n, 4) if n else None, "ci95": [round(lo, 3), round(hi, 3)]}
    return {"split": split, "n": len(rows), "by_tier": {k: dict(v) for k, v in sorted(summary.items())},
            "precision": precision, "rows": rows,
            "gloss_agree": sum(r.get("gloss_agree", 0) for r in rows),
            "gloss_disagree": sum(r.get("gloss_disagree", 0) for r in rows)}
