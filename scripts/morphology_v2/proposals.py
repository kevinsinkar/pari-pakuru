#!/usr/bin/env python3
"""Proposed segmentations for words Parks leaves unanalysed ("analysis not in Parks").

These are hypotheses.  The tier rules keep them out of learner material unless
paradigm evidence (E3) and a Blue Book seam (E5) independently agree, which is
rare.  They exist so that a speaker or linguist can be asked about them.

A proposal is made only when
  - the headword is produced exactly by the seam engine from one or two
    well-established pieces (optionally plus the noun suffix -uʔ), and
  - each lexical piece has at least three segments, exactly one known sense, and
    builds at least MIN_WORDS other words, and
  - the word's own gloss shares a content word with the sense of at least one piece.
"""
from collections import defaultdict

from bluebook import skel
from common import segments
import seams

MIN_WORDS = 5


def strong_forms(inv, support):
    """form -> its single sense, for forms safe enough to propose with."""
    outp = {}
    for form, clusters in inv.clusters.items():
        if len(clusters) != 1 or len(segments(form)) < 3:
            continue
        c = clusters[0]
        if c.get("stored_parse_only") or len(support.get(c["sense_id"], ())) < MIN_WORDS:
            continue
        outp[form] = c
    return outp


def propose_all(lexemes, has_claim, inv, support, gloss_stems, targets_of, is_word_like):
    strong = strong_forms(inv, support)
    by_first = defaultdict(list)
    for f in sorted(strong):
        by_first[skel(f)[:2]].append(f)
    proposals = {}
    for lex in lexemes:
        lid = lex["lexeme_id"]
        if has_claim(lid):
            continue
        targets = targets_of(lex)
        if not targets or " " in lex["headword"].strip():
            continue
        t = targets[0]
        word_like = is_word_like(lex)
        gst = gloss_stems(" ; ".join(g["definition"] for g in lex["glosses"]))
        tsk = skel(t)
        best = None
        for x in by_first.get(tsk[:2], []):
            if x == t or len(x) >= len(t):
                continue
            # x + uʔ
            tails = [["uʔ"]]
            # x + y (+ uʔ)
            rest_sk = tsk[max(1, len(skel(x)) - 1):]
            for y in strong:
                ysk = skel(y)
                if y != x and ysk and (ysk[1:] in rest_sk):
                    tails.append([y])
                    tails.append([y, "uʔ"])
            for tail in tails:
                pieces = [x] + tail
                if t not in seams.derive(pieces, word_like):
                    continue
                lexical = [p for p in pieces if p != "uʔ"]
                shared = [p for p in lexical if strong[p]["stems"] & gst]
                if not shared:
                    continue
                score = (len(shared) == len(lexical), -len(pieces), sum(len(p) for p in lexical))
                if best is None or score > best[0]:
                    best = (score, pieces, seams.derive(pieces, word_like)[t], shared)
        if best:
            _, pieces, rules, shared = best
            proposals[lid] = {
                "pieces": [{"form": p, "role": "grammatical" if p == "uʔ" else "lexical",
                            "label": "NOM" if p == "uʔ" else None,
                            "sense_id": None if p == "uʔ" else strong[p]["sense_id"],
                            "sense_evidence": None if p == "uʔ" else (
                                "entry_gloss" if p in shared else "default_single_sense")} for p in pieces],
                "rules": rules, "target": t,
                "all_pieces_match_gloss": len(shared) == len([p for p in pieces if p != "uʔ"])}
    return proposals
