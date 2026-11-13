#!/usr/bin/env python3
"""Tier assignment.  Pure functions: the tier follows mechanically from the evidence record.

Never set a tier by hand.  If a tier looks wrong, the evidence or these rules
are wrong, and that is what has to change.

Evidence values
    e1   'printed'   Parks prints an analysis of this word
         'citation'  Parks prints none, but cites this headword as a single piece,
                     with a compatible gloss, in other words' etymologies
         'proposed'  no Parks analysis; the segmentation was proposed from E3/E4/E5
         None        no analysis and no proposal: no segmentation claim is made
    e2   'exact' | 'partial' | 'fail' | None
    e3   'confirm' | 'contradict' | None      (paradigm evidence)
    e5   'confirm' | 'contradict' | None      (Blue Book seam evidence)
    e4   True | False                         (every piece recurs with the same meaning)
"""

TIERS = ("A", "B", "C", "D")
LEARNER_TIERS = ("A", "B")


def assign_tier(e1, e2, e3, e5, e4):
    """Return (tier or None, [reasons])."""
    if e1 is None:
        return None, ["no analysis in Parks and none proposed: no segmentation claim"]
    contradictions = [name for name, v in (("E3", e3), ("E5", e5)) if v == "contradict"]
    independent = [name for name, v in (("E3", e3), ("E5", e5)) if v == "confirm"]
    if e1 == "proposed":
        if contradictions:
            return "D", ["proposed analysis contradicted by " + " and ".join(contradictions)]
        if e3 == "confirm" and e5 == "confirm":
            return "B", ["analysis not in Parks; E3 and E5 independently agree"]
        if independent or e4:
            return "C", ["analysis not in Parks; supported by " +
                         ", ".join(independent + (["E4"] if e4 else [])) + " only"]
        return "D", ["analysis not in Parks; hypothesis only"]
    src = "Parks's printed analysis" if e1 == "printed" else "Parks's citation of the headword as one piece"
    if contradictions:
        return "C", [src + " contradicted by " + " and ".join(contradictions)]
    if e2 == "exact" and independent:
        return "A", [src + " reproduces the headword exactly and is confirmed by " + " and ".join(independent)]
    if e2 == "exact" and e4:
        return "B", [src + " reproduces the headword exactly; every piece recurs with the same meaning (E4)"]
    if e2 == "partial" and independent:
        return "B", [src + " reproduces the headword only partially but is confirmed by " + " and ".join(independent)]
    why = []
    if e2 == "exact":
        why.append("exact reproduction but no independent confirmation and not every piece recurs")
    elif e2 == "partial":
        why.append("partial reproduction and no independent confirmation")
    else:
        why.append("the pieces do not reproduce the headword")
    return "C", [src + ": " + "; ".join(why)]


def is_learner_facing(tier):
    return tier in LEARNER_TIERS
