#!/usr/bin/env python3
"""The learning order: which building block to teach next, derived from the data.

A word can be taken apart once every one of its pieces has been taught.  Each
morpheme is credited, for every word it helps build, with that word's weight
divided by the number of pieces of the word still untaught, so a piece that
completes many words outranks one that only starts them.  The next morpheme
taught is the one with the highest credit, scaled by how transparently it
joins its neighbours.  The weights are stated here and tested for sensitivity.
"""
from collections import defaultdict

from inventory import REVIEW_WORDS, needs_community_review

WEIGHTS = {
    "blue_book": 1.0,       # extra weight of a word the Blue Book teaches (on top of 1.0)
    "transparency": 0.5,    # bonus for a morpheme whose words join by plain concatenation
}


def teachable_keys(inv):
    keys = {}
    for r in inv["roots"]:
        if r["tier"] in ("A", "B"):
            keys[r["id"]] = r
    for a in inv["affixes"]:
        if a["tier"] in ("A", "B"):
            keys[a["id"]] = a
    return keys


def learning_order(need, inv, res, weights=None):
    """Greedy order over teachable morphemes.  Returns (order, usable_need)."""
    w = dict(WEIGHTS)
    w.update(weights or {})
    keys = teachable_keys(inv)
    lex_by_id = {lex["lexeme_id"]: lex for lex in res["lexemes"]}
    usable = {l: ks for l, ks in need.items() if ks <= set(keys)}
    lex_weight = {l: 1.0 + (w["blue_book"] if l in inv["bb_first"] else 0.0) for l in usable}
    transparency = {k: 1.0 + w["transparency"] * (keys[k]["transparency"]["share_plain"] or 0.0) for k in keys}
    review = {k for k, r in keys.items() if REVIEW_WORDS.search(str(r.get("meaning") or ""))}
    hosts = defaultdict(set)
    for l, ks in usable.items():
        for k in ks:
            hosts[k].add(l)
    remaining = {l: set(ks) for l, ks in usable.items()}

    def credit(k):
        return transparency[k] * sum(lex_weight[l] / len(remaining[l]) for l in hosts[k] if k in remaining[l])

    value = {k: credit(k) for k in keys if hosts[k]}
    order = []
    while value:
        # ceremonial meanings are never placed ahead of ordinary vocabulary
        pool = [k for k in value if k not in review] or list(value)
        best = max(pool, key=lambda k: (round(value[k], 9), -len(k), k))
        order.append(best)
        del value[best]
        touched = set()
        for l in hosts[best]:
            if best in remaining[l]:
                remaining[l].discard(best)
                touched |= remaining[l]
        for k in touched:
            if k in value:
                value[k] = credit(k)
    return order, usable


def spearman_top(base, other, n=50):
    """Spearman rank correlation of the baseline's first n items in another order, and set overlap."""
    top = base[:n]
    pos = {k: i for i, k in enumerate(other)}
    ranks = [pos.get(k, len(other)) for k in top]
    m = len(top)
    if m < 2:
        return 1.0, 1.0
    # rank the ranks (ties cannot occur: positions are distinct or all 'missing')
    order = sorted(range(m), key=lambda i: ranks[i])
    rr = [0] * m
    for r, i in enumerate(order):
        rr[i] = r
    d2 = sum((i - rr[i]) ** 2 for i in range(m))
    rho = 1 - 6 * d2 / (m * (m * m - 1))
    overlap = len(set(top) & set(other[:n])) / m
    return round(rho, 4), round(overlap, 4)


def sensitivity(need, inv, res, base_order, n=50):
    """Shift each weight by +/-25% and report how stable the first n places are."""
    rows = []
    for name in sorted(WEIGHTS):
        for factor in (0.75, 1.25):
            wts = dict(WEIGHTS)
            wts[name] = WEIGHTS[name] * factor
            order, _ = learning_order(need, inv, res, wts)
            rho, overlap = spearman_top(base_order, order, n)
            rows.append({"weight": name, "factor": factor, "value": round(wts[name], 4),
                         "spearman_top_%d" % n: rho, "overlap_top_%d" % n: overlap,
                         "first_10_unchanged": order[:10] == base_order[:10]})
    for fa in (0.75, 1.25):
        for fb in (0.75, 1.25):
            wts = {"blue_book": WEIGHTS["blue_book"] * fa, "transparency": WEIGHTS["transparency"] * fb}
            order, _ = learning_order(need, inv, res, wts)
            rho, overlap = spearman_top(base_order, order, n)
            rows.append({"weight": "both", "factor": [fa, fb], "value": [round(v, 4) for v in wts.values()],
                         "spearman_top_%d" % n: rho, "overlap_top_%d" % n: overlap,
                         "first_10_unchanged": order[:10] == base_order[:10]})
    return rows
