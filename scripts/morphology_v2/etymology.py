#!/usr/bin/env python3
"""Channel E1: parse Parks's printed etymology (`raw_etymology`) into pieces.

The database also stores `constituent_elements`, a piece list produced by an
earlier AI parse.  Its per-piece glosses and `morpheme_type` labels are not
reliable (e.g. `<as+hur+uʔ, foot place + NOM>` is stored as as='foot place',
hur=None), so this module re-derives everything from the printed string and
uses `constituent_elements` only as a cross-check on the piece forms.

Parks's conventions, as observed in the data:
    <kaa+at, go inside>              pieces joined by +, then a literal translation
    <as+uʔ, foot + NOM>              literal split by + when it aligns with the pieces
    <waa+waapic, flash + DIST>       ...but the literal need not follow morpheme order
    <ut+as+ukaa.at, ...>             '.' joins the elements of a compound stem
    <as (ut...)+ri.wiitik, ...>      a preverb note attached to a piece
    <haak-+kata.wuh, ...>            a trailing hyphen marks a bound (combining) form
    <kaas-+(h)aahka.wi+uʔ, ...>      parentheses mark an optional segment
    <kic+tuuks+uʔ, water + tuuks + NOM>   a piece glossed by its own form has no known meaning
    <rut.kis ra+haa+warii, ...>      a space separates the words of a phrase
    <i.q. SB kee, Ar. čee>           cognate note only: no analysis
    <Engl. biscuit>                  loan

Alignment of the literal translation with the pieces is done in two passes over
the whole dictionary (see `align_all`): grammatical labels are anchored to the
piece that carries that label most often elsewhere, not to the piece that
happens to sit in the same position.
"""
import json
import re
from collections import Counter, defaultdict

from common import norm, strip_accents

PREVERB_NOTE = re.compile(r"\(\s*([a-z]+(?:\s*\.\s*\.\s*\.\s*[a-z]+)*)\s*\.\s*\.\s*\.\s*\)")
LABEL_CHUNK = re.compile(r"^[A-Z0-9][A-Z0-9./ ]*$")
PREVERBS = ("ut", "uur", "ir")
NOTE_START = re.compile(r"^(i\.q\.|cf\.|onom\.|var\. of\b)", re.I)
LOAN_START = re.compile(r"^(Engl?\.|Sp\.|Fr\.|Wi\.|Sioux\b|from\b|prob\. from\b|borrow|ultimately\b|of unknown origin)", re.I)
HEDGE = re.compile(r"^(prob\.|perh\.|perhaps|apparently|possibly|poss\.)\s+", re.I)
MORPH_OK = re.compile(r"^[a-zʔØ()\-./+ ]+$")
MIN_LABEL_COUNT = 3      # a form must carry a label this often before it can anchor it


def clean_form(s):
    """A piece as a plain comparable string: accents stripped, hyphens removed."""
    s = strip_accents(norm(s)).lower()
    s = s.replace("ø", "Ø")
    return re.sub(r"[\s\-]", "", s)


def optional_variants(form):
    """'(h)aahka' -> ('haahka', 'aahka');  'asku(s)' -> ('askus', 'asku')."""
    full = re.sub(r"[()]", "", form)
    minimal = re.sub(r"\([^)]*\)", "", form)
    minimal = re.sub(r"[()]", "", minimal)
    return full, (minimal or full)


def _strip_wrapper(raw):
    s = norm(raw)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("<"):
        s = s[1:]
    if s.endswith(">"):
        s = s[:-1]
    return s.strip()


def _despace(text):
    """Repair letter-spaced OCR runs: 'e x i s t ;  r e f .' -> 'exist; ref.'"""
    return re.sub(r"(?:\b[a-zA-Z] ){3,}[a-zA-Z]\b", lambda m: m.group(0).replace(" ", ""), text)


def parse_etymology(raw, headword_alternates=()):
    """Parse the structure of one printed etymology (no gloss alignment yet).

    Returns a dict:
        kind       'analysis' | 'identity' | 'underlying' | 'cognate_only' | 'loan' | 'none' | 'unparsed'
        pieces     list of piece dicts, in order
        chunks     the literal translation split at ' + '
        literal    Parks's literal translation or None
        preverbs   preverbs named in notes such as (ut...)
        flags      list of strings describing anything irregular
    A piece dict has:
        form, form_min   full form and form without optional segments
        group            index of the '+'-delimited unit the piece belongs to
        word             index of the space-delimited word the piece belongs to
        dotted           True when the unit was a compound stem split at '.'
        bound            True when Parks wrote a hyphen on the piece
    `align_all` later adds gloss, gloss_kind and phrase.
    """
    res = {"kind": "none", "pieces": [], "chunks": [], "literal": None, "preverbs": [], "flags": []}
    if not raw or not raw.strip():
        return res
    s = _despace(_strip_wrapper(raw))
    if not s:
        return res
    if NOTE_START.match(s):
        res["kind"] = "cognate_only"
        return res
    if LOAN_START.match(s):
        res["kind"] = "loan"
        return res
    m = HEDGE.match(s)
    if m:
        res["flags"].append("hedged")
        s = s[m.end():]
    if re.search(r"\[[^\]]*\]", s.split(",")[0]):
        res["flags"].append("bracket_note")
    body = s.split(";")[0]
    morph, _, literal = body.partition(",")
    morph = re.sub(r"\[[^\]]*\]", " ", morph)
    # '( u t . . . )' -> '(ut...)'
    morph = re.sub(r"\(([a-z .]+)\)", lambda mt: "(" + mt.group(1).replace(" ", "") + ")", morph)
    if "?" in morph:
        res["flags"].append("hedged")
        morph = morph.replace("?", " ")
    morph = re.sub(r"\s*\+\s*", "+", morph)
    morph = re.sub(r"-\s+(?=[a-zʔ])", "", morph)        # line-break hyphen: 'pii- ra' -> 'piira'
    morph = re.sub(r"\s*\.\s*(?=[a-zʔ(])", ".", morph)
    morph = morph.strip()
    literal = literal.strip()
    if LOAN_START.match(literal) or re.search(r"\bfrom [A-Z]", literal):
        res["kind"] = "loan"
        return res
    literal = re.split(r"\b(?:cf\.|i\.q\.|lit\.|ref\. to|originally ref)", literal)[0].strip(" ,")
    if not morph or not MORPH_OK.match(strip_accents(morph)):
        # an upper-case label written in the morpheme string (NEG+kaapaakis) is tolerated
        if morph and MORPH_OK.match(strip_accents(re.sub(r"\b[A-Z]{2,}\b", "", morph))):
            res["flags"].append("label_in_morpheme_string")
            morph = re.sub(r"\b[A-Z]{2,}\b\+?", "", morph)
        else:
            res["kind"] = "unparsed"
            res["flags"].append("unexpected_characters")
            return res
    res["literal"] = literal or None
    res["chunks"] = [c.strip() for c in re.split(r"\s\+\s|\s\+$|^\+\s", literal) if c.strip()] if literal else []
    # 'INCH, i.e., become knowledgeable': the chunk is the label, the rest is commentary
    res["chunks"] = [re.match(r"^[A-Z]{2,}[A-Z./]*", c).group(0) if re.match(r"^[A-Z]{2,}[A-Z./]*,", c) else c
                     for c in res["chunks"]]

    preverbs, pieces = [], []
    gi = 0
    for wi, word in enumerate(w for w in re.split(r"\s+(?![^()]*\))", morph) if w):
        # a preverb note written after a space belongs to the preceding word
        if PREVERB_NOTE.fullmatch(word):
            for p in PREVERB_NOTE.fullmatch(word).group(1).replace(" ", "").split("..."):
                if p and p not in preverbs:
                    preverbs.append(p)
            continue
        for unit in word.split("+"):
            unit_pvs = []

            def take(mt, acc=unit_pvs):
                acc.extend(p for p in mt.group(1).replace(" ", "").split("...") if p)
                return ""
            unit = PREVERB_NOTE.sub(take, unit).strip()
            for p in unit_pvs:
                if p not in preverbs:
                    preverbs.append(p)
            if not unit:
                continue
            if "/" in unit:
                res["flags"].append("slash_alternation")
            bound = unit.endswith("-") or unit.startswith("-")
            if re.search(r"[a-zʔ)]-[a-zʔ(]", unit):
                res["flags"].append("internal_hyphen")
            subs = [x for x in unit.split(".") if x.strip("-")]
            for sub in subs:
                sub = sub.replace("-", "")
                if not sub:
                    continue
                if "(" in sub:
                    res["flags"].append("optional_segment")
                full, minimal = optional_variants(sub)
                pieces.append({"form": clean_form(full), "form_min": clean_form(minimal), "group": gi,
                               "word": wi, "dotted": len(subs) > 1, "bound": bound,
                               "gloss": None, "gloss_kind": None, "phrase": None})
            gi += 1
    if not pieces or sum(1 for p in pieces if len(p["form"]) == 1) >= 4:
        res["kind"] = "unparsed"                          # empty, or letter-spaced OCR debris
        res["flags"].append("unparsed_pieces")
        return res
    # renumber words densely (preverb-note words were skipped)
    remap = {w: i for i, w in enumerate(sorted({p["word"] for p in pieces}))}
    for p in pieces:
        p["word"] = remap[p["word"]]
    if len(remap) > 1:
        res["flags"].append("multiword")
    res["preverbs"] = preverbs
    res["flags"] = sorted(set(res["flags"]))
    alts = set(headword_alternates)
    if len(pieces) > 1:
        res["kind"] = "analysis"
    else:
        only = pieces[0]
        res["kind"] = "identity" if (only["form"] in alts or only["form_min"] in alts) else "underlying"
    res["pieces"] = pieces
    return res


# ---------------------------------------------------------------------------
# Literal-translation alignment (two passes over the whole dictionary)
# ---------------------------------------------------------------------------

def _units(pieces, level):
    """Group pieces into alignment units: each piece ('piece') or each '+'-unit ('group')."""
    if level == "piece":
        return [[p] for p in pieces]
    by = defaultdict(list)
    for p in pieces:
        by[p["group"]].append(p)
    return [by[g] for g in sorted(by)]


def _positional(res):
    """Units and chunks when their counts are equal, else (None, None)."""
    chunks, pieces = res["chunks"], res["pieces"]
    if not chunks:
        return None, None
    for level in ("piece", "group"):
        units = _units(pieces, level)
        if len(units) == len(chunks):
            return units, level
    return None, None


def label_statistics(parsed):
    """Count how often each form sits opposite each grammatical label (pass 1)."""
    stats = defaultdict(Counter)
    for res in parsed:
        units, _ = _positional(res)
        if not units:
            continue
        for unit, chunk in zip(units, res["chunks"]):
            if LABEL_CHUNK.match(chunk) and len(unit) == 1:
                stats[chunk][unit[0]["form"]] += 1
    return stats


def align(res, stats):
    """Attach glosses to the pieces of one parsed etymology (pass 2).

    gloss_kind values:
        'label'    a grammatical label Parks printed (NOM, DIM, PL, DIST, PREV ...)
        'aligned'  a lexical gloss that the literal translation gives to this piece alone
        'self'     Parks glosses the piece with its own form: meaning unknown to him
        'phrase'   the piece shares a literal phrase with its neighbours (see `phrase`)
        None       no literal translation printed
    """
    chunks, pieces = list(res["chunks"]), res["pieces"]
    for p in pieces:
        p["gloss"], p["gloss_kind"], p["phrase"] = None, None, None
    if not chunks or not pieces:
        return res
    free = list(pieces)                         # pieces not yet claimed by a label
    lexical = []
    how = set()
    for ci, chunk in enumerate(chunks):
        if not LABEL_CHUNK.match(chunk):
            lexical.append(chunk)
            continue
        # anchor the label on the free piece that carries it most often elsewhere
        best, best_n = None, 0
        for p in free:
            n = stats.get(chunk, {}).get(p["form"], 0)
            if n > best_n:
                best, best_n = p, n
        if best is not None and best_n >= MIN_LABEL_COUNT:
            best["gloss"], best["gloss_kind"] = chunk, "label"
            free.remove(best)
            how.add("label_by_statistics")
        else:
            lexical.append(chunk)               # unknown label: leave it in the phrase
            how.add("label_unanchored")
    if not free or not lexical:
        res["alignment"] = sorted(how)
        return res
    # the remaining lexical chunks against the remaining pieces
    for level in ("piece", "group"):
        units = _units(free, level)
        if len(units) == len(lexical) and not (len(units) == 1 and len(units[0]) > 1):
            for unit, chunk in zip(units, lexical):
                if len(unit) == 1:
                    p = unit[0]
                    if LABEL_CHUNK.match(chunk):
                        p["gloss"], p["gloss_kind"] = chunk, "label"
                    elif clean_form(chunk) in (p["form"], p["form_min"]) or (
                            clean_form(optional_variants(chunk)[0]) in (p["form"], p["form_min"])):
                        p["gloss"], p["gloss_kind"] = chunk, "self"
                    else:
                        p["gloss"], p["gloss_kind"] = chunk, "aligned"
                else:
                    for p in unit:
                        p["phrase"], p["gloss_kind"] = chunk, "phrase"
            how.add("aligned_by_" + level)
            res["alignment"] = sorted(how)
            return res
    phrase = " + ".join(lexical)
    for p in free:
        p["phrase"], p["gloss_kind"] = phrase, "phrase"
    how.add("shared_phrase")
    res["alignment"] = sorted(how)
    return res


def align_all(parsed, extra_anchors=()):
    """Two-pass alignment over every parsed etymology.  Returns the label statistics.

    `extra_anchors` is a list of (label, form) pairs from cited manual decisions: forms that
    carry a label too rarely in matching position for the statistics to find them.
    """
    stats = label_statistics(parsed)
    for label, form in extra_anchors:
        stats[label][form] = max(stats[label][form], MIN_LABEL_COUNT)
    for res in parsed:
        align(res, stats)
    return stats


def json_pieces(constituent_elements):
    """Piece forms from the stored AI parse, cleaned the same way (cross-check only)."""
    if not constituent_elements:
        return None
    try:
        els = json.loads(constituent_elements)
    except Exception:
        return None
    forms, glosses = [], []
    for e in els or []:
        m = norm(e.get("morpheme") or "")
        m = PREVERB_NOTE.sub("", m)
        m = re.sub(r"\[.*?\]", "", m)
        for unit in re.split(r"[+\s]+", m):
            for sub in unit.split("."):
                sub = sub.strip().replace("-", "")
                if not sub:
                    continue
                full, _ = optional_variants(sub)
                f = clean_form(full)
                if f and not LABEL_CHUNK.match(sub):
                    forms.append(f)
                    glosses.append(e.get("gloss"))
    return {"forms": forms, "glosses": glosses}
