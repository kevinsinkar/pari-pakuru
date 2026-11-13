#!/usr/bin/env python3
"""Blue Book seam evidence (channel E5, gold set G3).

The Blue Book writes a raised dot between pieces of a word (tat•kikat).  That
segmentation was made by different authors than Parks's dictionary, so where a
seamed Blue Book word can be matched to a Parks form with certainty, the seam
positions are independent evidence about where morphemes meet.

A match is *certain* only when
  1. the Blue Book token (seams removed) has the same length-/ʔ-/h-insensitive
     skeleton as exactly one distinct Parks form (headword, paradigm form or
     Appendix 1 cell), with a skeleton of at least MIN_SKELETON letters, and
  2. the Blue Book English shares a content word with the entry's gloss.
Links stored in blue_book_attestations (match_type) are NOT used: the 'prefix'
links there are known to be unreliable.
"""
import re
from collections import defaultdict

from common import norm, strip_accents

MIN_SKELETON = 4

IRREGULAR = {
    "went": "go", "gone": "go", "goes": "go", "came": "come", "ate": "eat", "eaten": "eat",
    "said": "say", "saw": "see", "seen": "see", "did": "do", "done": "do", "gave": "give",
    "given": "give", "took": "take", "taken": "take", "bought": "buy", "found": "find",
    "sat": "sit", "made": "make", "got": "get", "drank": "drink", "drunk": "drink",
    "slept": "sleep", "told": "tell", "heard": "hear", "knew": "know", "known": "know",
    "ran": "run", "sang": "sing", "sung": "sing", "stood": "stand", "lay": "lie", "lying": "lie",
    "brought": "bring", "thought": "think", "left": "leave", "died": "die", "dead": "die",
    "had": "have", "has": "have", "was": "be", "were": "be", "is": "be", "are": "be", "am": "be",
    "been": "be", "feet": "foot", "teeth": "tooth", "men": "man", "women": "woman",
    "children": "child", "sold": "sell", "spoke": "speak", "spoken": "speak", "wrote": "write",
    "written": "write", "fell": "fall", "felt": "feel", "kept": "keep", "met": "meet",
    "paid": "pay", "sent": "send", "stole": "steal", "swam": "swim", "threw": "throw",
    "woke": "wake", "wore": "wear", "won": "win", "hurting": "hurt", "hungry": "hunger",
    "working": "work", "dying": "die", "tying": "tie",
    # adjectives in -y / -ed that are the same word as their noun
    "bony": "bone", "watery": "water", "grassy": "grass", "hairy": "hair", "muddy": "mud", "sandy": "sand",
    "rocky": "rock", "dusty": "dust", "smoky": "smoke", "bloody": "blood", "windy": "wind", "cloudy": "cloud",
    "stony": "stone", "woody": "wood", "salty": "salt", "greasy": "grease", "eyed": "eye", "nicely": "nice",
}
STOP = set("""a an the of to in on at for and or it its he she him her his they them their we us our
you your i me my is be not no yes do does did have this that these those there here with as by
one ones some any all very just so if when what who where how up down out off now then will
shall would should can could may might must let s t 3 2 1 pl du sg someone something
ref esp e g i.e etc also used being""".split())


def content_stems(text):
    """Crude English content-word stems, for a gloss-overlap check."""
    stems = set()
    for w in re.findall(r"[a-z]+", (text or "").lower()):
        w = IRREGULAR.get(w, w)
        if w in STOP or len(w) < 3:
            continue
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        if len(w) > 3 and w[-1] == w[-2]:        # sitt(ing) -> sit, runn(ing) -> run
            w = w[:-1]
        if w.endswith("e") and len(w) > 3:
            w = w[:-1]
        stems.add(IRREGULAR.get(w, w))
    return stems


def _letters(s):
    return re.sub(r"[^a-zʔ]", "", s)


def bb_norm_part(part):
    """One seam-delimited piece of a Blue Book word -> Parks-like letters."""
    # the Blue Book prints an accent on the stressed vowel (restored in the data on 2026-11-13);
    # it is not a letter, and must not make the vowel under it disappear below
    t = strip_accents(norm(part)).lower()
    t = t.replace("ts", "c")
    t = t.replace("e", "i").replace("o", "u")
    return _letters(t)


def skel_chars(s):
    """Skeleton of a Parks-like string with the source span of every kept char.

    Returns a list of (char, start, end) where [start, end) is the span in s.
    Long vowels collapse to one char; ʔ and h are dropped.
    """
    outp = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "ʔh":
            i += 1
            continue
        if ch in "aiu":
            j = i
            while j < len(s) and s[j] == ch:
                j += 1
            outp.append((ch, i, j))
            i = j
            continue
        outp.append((ch, i, i + 1))
        i += 1
    return outp


def skel(s):
    return "".join(c for c, _, _ in skel_chars(s))


def parks_clean(form):
    """A Parks form as a plain lower-case letter string (accents stripped)."""
    return _letters(strip_accents(norm(form)).lower())


def bb_token_parts(token):
    """Split a Blue Book token at its seams -> list of normalised parts (may be empty)."""
    token = token.strip(" .,;:!?\"“”()[]")
    return [bb_norm_part(p) for p in token.split("•")]


def seam_boundaries(parts, target):
    """Map Blue Book seams onto offsets in the Parks string `target`.

    Returns (boundaries, ok).  Each boundary is [lo, hi]: the seam lies at some
    offset lo <= k <= hi in target (segments dropped by the skeleton leave the
    exact spot undetermined).  ok is False when the skeletons do not line up.
    """
    tchars = skel_chars(target)
    tskel = "".join(c for c, _, _ in tchars)
    pieces = [skel(p) for p in parts]
    joined = "".join(pieces)
    # a seam inside t•s corresponds to Parks c: retry with the pair merged
    merged_at = None
    if joined != tskel:
        acc = 0
        for i in range(len(pieces) - 1):
            acc += len(pieces[i])
            if pieces[i].endswith("t") and pieces[i + 1].startswith("s"):
                cand = joined[: acc - 1] + "c" + joined[acc + 1:]
                if cand == tskel:
                    merged_at = (i, acc - 1)
                    break
        if merged_at is None:
            return [], False
    bounds = []
    acc = 0
    shift = 0
    for i in range(len(pieces) - 1):
        acc += len(pieces[i])
        k = acc - shift                     # skeleton offset of this seam
        if merged_at and merged_at[0] == i:
            # the seam fell inside a Parks 'c': it may sit on either side of it
            cpos = merged_at[1]
            lo = tchars[cpos][1]
            hi = tchars[cpos][2]
            bounds.append([lo, hi])
            shift = 1
            continue
        lo = tchars[k - 1][2] if k - 1 >= 0 and k - 1 < len(tchars) else 0
        hi = tchars[k][1] if k < len(tchars) else len(target)
        if k <= 0:
            lo, hi = 0, tchars[0][1] if tchars else 0
        bounds.append([lo, hi])
    return bounds, True


def split_variants(form):
    """A paradigm cell may hold variants: 'taatasuuktit; wititaatasuuktit'."""
    return [v.strip() for v in re.split(r"[;,]", form or "") if v.strip()]


def build_targets(conn):
    """skeleton -> {parks_string: [target records]} over headwords, paradigm forms, App.1."""
    targets = defaultdict(lambda: defaultdict(list))
    gloss = defaultdict(list)
    for r in conn.execute("select entry_id, definition from glosses order by entry_id, sense_number, id"):
        gloss[r[0]].append(r[1] or "")
    # Blue-Book-only entries are excluded: their headwords were derived from the
    # Blue Book itself, so matching them would be circular.
    for r in conn.execute("""select entry_id, headword from lexical_entries
                             where coalesce(source, '') <> 'blue_book' order by entry_id"""):
        hw = re.sub(r"\[.*?\]|\(.*?\)", "", norm(r[1]))
        for alt in hw.split(","):
            t = parks_clean(alt)
            if t:
                targets[skel(t)][t].append({"type": "headword", "entry_id": r[0],
                                            "english": " ; ".join(gloss[r[0]])})
    for r in conn.execute("select entry_id, form_number, skiri_form from paradigmatic_forms order by entry_id, form_number"):
        for v in split_variants(r[2]):
            t = parks_clean(v)
            if t:
                targets[skel(t)][t].append({"type": "form", "form_number": r[1], "entry_id": r[0],
                                            "english": " ; ".join(gloss[r[0]])})
    for r in conn.execute("""select id, verb_heading, mode, person_number, skiri_form, english_form
                             from verb_paradigms order by id"""):
        for v in split_variants(r[4]):
            t = parks_clean(v)
            if t:
                targets[skel(t)][t].append({"type": "app1", "app1_id": r[0], "verb": r[1],
                                            "mode": r[2], "person": r[3],
                                            "english": (r[5] or "") + " ; " + (r[1] or "")})
    return targets


def bb_seam_tokens(conn):
    """Every seamed word token in blue_book_attestations, with its row context."""
    toks = []
    seen = set()
    for r in conn.execute("""select id, bb_skiri_form, bb_english, context_type, lesson_number, page_number
                             from blue_book_attestations order by id"""):
        form = norm(r[1] or "").replace("ʔ", "'")
        if "•" not in form:
            continue
        repaired = bool(re.search(r"\s\.(?=\w)|•\s|\s•", form))
        for tok in form.split():
            if "•" not in tok:
                continue
            clean = tok.strip(" .,;:!?\"“”()[]")
            key = (clean.lower(), (r[2] or "").lower())
            if key in seen:
                continue
            seen.add(key)
            toks.append({"bb_row": r[0], "bb_token": clean, "bb_phrase": r[1], "bb_english": r[2],
                         "context": r[3], "lesson": r[4], "page": r[5], "ocr_spacing": repaired})
    return toks


def match_seams(conn):
    """Certain and uncertain seam matches.  Returns (certain, rejected_counts)."""
    targets = build_targets(conn)
    certain = []
    counts = defaultdict(int)
    for t in bb_seam_tokens(conn):
        counts["seamed_tokens"] += 1
        if t["ocr_spacing"]:
            counts["skipped_ocr_spacing"] += 1
            continue
        parts = bb_token_parts(t["bb_token"])
        if any(not p for p in parts):
            counts["skipped_empty_part"] += 1
            continue
        sk = skel("".join(parts))
        alt = None
        if sk not in targets:
            # t•s across a seam is Parks c
            j = "".join(skel(p) for p in parts)
            acc = 0
            for i in range(len(parts) - 1):
                acc += len(skel(parts[i]))
                if j[acc - 1: acc + 1] == "ts":
                    cand = j[: acc - 1] + "c" + j[acc + 1:]
                    if cand in targets:
                        alt = cand
                        break
            if alt is None:
                counts["no_target"] += 1
                continue
            sk = alt
        if len(sk) < MIN_SKELETON:
            counts["too_short"] += 1
            continue
        cands = targets[sk]
        if len(cands) != 1:
            counts["ambiguous_target"] += 1
            continue
        (target, recs), = cands.items()
        bb_stems = content_stems(t["bb_english"])
        ok_recs = [r for r in recs if bb_stems & content_stems(r["english"])]
        if not ok_recs:
            counts["english_mismatch"] += 1
            continue
        bounds, ok = seam_boundaries(parts, target)
        if not ok:
            counts["alignment_failed"] += 1
            continue
        counts["certain"] += 1
        certain.append({
            "bb_token": t["bb_token"], "bb_parts": parts, "bb_english": t["bb_english"],
            "lesson": t["lesson"], "page": t["page"], "bb_row": t["bb_row"],
            "target": target, "boundaries": bounds,
            "targets": sorted(ok_recs, key=lambda r: (r["type"], r.get("entry_id") or "", r.get("form_number") or 0,
                                                      r.get("app1_id") or 0)),
        })
    certain.sort(key=lambda m: (m["target"], m["bb_token"], m["bb_row"]))
    return certain, dict(counts)
