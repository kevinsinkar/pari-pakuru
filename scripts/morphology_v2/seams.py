#!/usr/bin/env python3
"""Seam engine: what happens where two pieces meet.

`derive(pieces, word_like)` builds every surface form that the named rules
allow from a list of underlying pieces and returns each with the rules used.
Channel E2 calls a reproduction *exact* only when the headword is one of these
forms, so every difference between Parks's pieces and the headword is accounted
for by a rule that is named here and has a source.

Rules are applied only at morpheme boundaries and at word edges, never inside a
piece (the string-level engine in sound_changes.py cannot tell a boundary
cluster from a cluster inside a root, e.g. it turns iks- into ikc-).

Sources
    Parks N    numbered rule N in Parks, "Major Sound Changes" (scripts/sound_changes.py)
    BB L3      Blue Book Lesson 3, "Combining roots", pp. 41-42
    data       a regularity not stated in either source; its attestation count and
               consistency are measured over the dictionary and reported in METHOD.md
"""
import itertools

VOWELS = "aiu"
OBSTRUENTS = "ptkcs"

RULES = {
    "V+V ʔ": {"name": "ʔ between two vowels that do not contract", "source": "data; consistent with the "
              "conditions under which Parks says vowels do not contract (Major Sound Changes, Vowels: "
              "Unrestricted Rules)", "optional": False},
    "R5": {"name": "same-vowel contraction (V + V > VV)", "source": "Parks 5", "optional": False},
    "R6": {"name": "u-domination (V + u, u + V > uu)", "source": "Parks 6", "optional": False},
    "R7": {"name": "i + a, a + i > ii", "source": "Parks 7; BB L3 rule 5 (i + a > e)", "optional": False},
    "r>h/_C": {"name": "r > h before a consonant", "source": "BB L3 rule 4", "optional": False},
    "V:>V/_hC": {"name": "a long vowel shortens before h + consonant", "source": "data", "optional": True},
    "R20": {"name": "degemination (r + r > r, k + k > k)", "source": "Parks 20", "optional": False},
    "R14-15": {"name": "r + h > h", "source": "Parks 14, 15", "optional": False},
    "R13": {"name": "t + r > h", "source": "Parks 13, 15", "optional": False},
    "R21": {"name": "r > t after an obstruent", "source": "Parks 21; BB L3 rule 1", "optional": False},
    "R16": {"name": "h is lost after a consonant", "source": "Parks 16", "optional": False},
    "R16b": {"name": "h is lost before two consonants or a single word-final consonant",
             "source": "Parks 16", "optional": False},
    "R17": {"name": "s > c after a consonant", "source": "Parks 17", "optional": False},
    "R19": {"name": "t + t > ct", "source": "Parks 19", "optional": False},
    "w>p/C_": {"name": "w > p after a hard consonant", "source": "BB L3 rule 2", "optional": False},
    "k>0/_p": {"name": "k drops before p", "source": "BB L3 rule 3", "optional": False},
    "R3": {"name": "k + -his > ks", "source": "Parks 3R", "optional": False},
    "R8": {"name": "raar- + t > c", "source": "Parks 8R", "optional": False},
    "R23": {"name": "word-final r is lost", "source": "Parks 23", "optional": False},
    "R9": {"name": "word-final s is lost in certain nouns and suffixes", "source": "Parks 9R (lexically restricted)",
           "optional": True},
    "k>t/_#": {"name": "word-final k > t", "source": "data; BB L15 (verb-final k)", "optional": True},
    "V>Vʔ/_#": {"name": "ʔ after a word-final vowel", "source": "data", "optional": True},
    "#V>0/_C": {"name": "word-initial i or a is lost before a consonant", "source": "data (lexically restricted)",
                "optional": True},
    "#w>p": {"name": "word-initial w > p", "source": "data; extends BB L3 rule 2 to the start of a word",
             "optional": True},
}

MAX_STATES = 96


def _is_v(ch):
    return ch in VOWELS


def _trailing_vowel(s):
    """Length of the vowel (1 or 2 letters) that ends s, or 0."""
    if not s or s[-1] not in VOWELS:
        return 0
    return 2 if len(s) >= 2 and s[-2] == s[-1] else 1


def _leading_vowel(s):
    if not s or s[0] not in VOWELS:
        return 0
    return 2 if len(s) >= 2 and s[1] == s[0] else 1


def join(left, right, left_piece=None):
    """All ways the surface so far (`left`) joins the next underlying piece (`right`).

    Returns a list of (joined, [rule ids]).
    """
    if not left:
        return [(right, [])]
    if not right:
        return [(left, [])]
    a, b = left[-1], right[0]
    # ---- vowel hiatus
    if _is_v(a) and _is_v(b):
        n1, n2 = _trailing_vowel(left), _leading_vowel(right)
        v1, v2 = left[-1], right[0]
        if "u" in (v1, v2):
            res, rid = "uu", "R6"
        elif v1 == v2:
            res, rid = v1 * 2, "R5"
        else:
            res, rid = "ii", "R7"
        return [(left + "ʔ" + right, ["V+V ʔ"]),
                (left[:-n1] + res + right[n2:], [rid])]
    if _is_v(b) or _is_v(a):
        # a consonant meets a vowel, or a vowel meets a consonant: plain concatenation,
        # except the consonant-initial rules below that need a consonant on the left
        if _is_v(a):
            return [(left + right, [])]
    # from here on `a` is a consonant
    if a == "r" and not _is_v(b):
        if b == "r":
            return [(left[:-1] + right, ["R20"])]
        if b == "h":
            return [(left[:-1] + right, ["R14-15"])]
        if left_piece == "raar" and b == "t":
            outs = [(left[:-1] + "c" + right[1:], ["R8"])]
            if len(left) >= 3 and left[-3:-1] in ("aa", "ii", "uu"):
                outs.append((left[:-3] + left[-2] + "c" + right[1:], ["R8", "V:>V/_hC"]))
            return outs
        outs = [(left[:-1] + "h" + right, ["r>h/_C"])]
        if len(left) >= 3 and left[-3:-1] in ("aa", "ii", "uu"):
            outs.append((left[:-3] + left[-2] + "h" + right, ["r>h/_C", "V:>V/_hC"]))
        return outs
    if _is_v(b):
        return [(left + right, [])]
    if a == "t" and b == "r":
        return [(left[:-1] + "h" + right[1:], ["R13"])]
    if a == "t" and b in "tc":
        return [(left[:-1] + "ct" + right[1:], ["R19"])]
    if a == "k" and right == "his":
        return [(left + "s", ["R3"])]
    if a in OBSTRUENTS and b == "r":
        return [(left + "t" + right[1:], ["R21"])]
    if b == "h":
        return [(left + right[1:], ["R16"])]
    if a in OBSTRUENTS and b == "w":
        if a == "k":
            return [(left[:-1] + "p" + right[1:], ["w>p/C_", "k>0/_p"])]
        return [(left + "p" + right[1:], ["w>p/C_"])]
    if a == "k" and b == "k":
        return [(left + right[1:], ["R20"])]
    if a in OBSTRUENTS and b == "s":
        return [(left + "c" + right[1:], ["R17"])]
    return [(left + right, [])]


def _h_before_clusters(s, word_like):
    """Parks 16b: h is lost before two consonants, and before a single word-final consonant."""
    outp, fired = [], False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "h" and i > 0:
            nxt = s[i + 1:i + 3]
            two = len(nxt) == 2 and not _is_v(nxt[0]) and not _is_v(nxt[1])
            final = word_like and len(s) - i == 2 and not _is_v(s[i + 1])
            if two or final:
                fired = True
                i += 1
                continue
        outp.append(ch)
        i += 1
    return "".join(outp), fired


def _word_edges(surface, rules, word_like):
    """Word-level rules.  Stems (verbs, bound forms) are not words: none of these apply to them."""
    s, fired = _h_before_clusters(surface, word_like)
    base_rules = rules + (["R16b"] if fired else [])
    if not word_like:
        return [(s, base_rules)]
    if s.endswith("r"):
        s = s[:-1]
        base_rules = base_rules + ["R23"]
    states = [(s, base_rules)]
    # optional word-edge rules; each doubles the states only where it can apply
    nxt = []
    for st, rl in states:
        nxt.append((st, rl))
        if st.endswith("s") and len(st) > 2:
            nxt.append((st[:-1], rl + ["R9"]))
    states, nxt = nxt, []
    for st, rl in states:
        nxt.append((st, rl))
        if st.endswith("k"):
            nxt.append((st[:-1] + "t", rl + ["k>t/_#"]))
    states, nxt = nxt, []
    for st, rl in states:
        nxt.append((st, rl))
        if st and st[-1] in VOWELS:
            nxt.append((st + "ʔ", rl + ["V>Vʔ/_#"]))
    states, nxt = nxt, []
    for st, rl in states:
        nxt.append((st, rl))
        if len(st) > 2 and st[0] in "ia" and st[1] not in VOWELS:
            nxt.append((st[1:], rl + ["#V>0/_C"]))
        if st.startswith("w"):
            nxt.append(("p" + st[1:], rl + ["#w>p"]))
    return nxt


def derive(pieces, word_like):
    """Every surface the rules allow for one word.  Returns {surface: [rule ids]} (fewest optional rules kept)."""
    pieces = [p for p in pieces if p]
    if not pieces:
        return {}
    states = [(pieces[0], [])]
    for idx in range(1, len(pieces)):
        nxt = []
        for surf, rules in states:
            for joined, fired in join(surf, pieces[idx], pieces[idx - 1]):
                nxt.append((joined, rules + fired))
        states = nxt[:MAX_STATES]
    outp = {}
    for surf, rules in states:
        for s, rl in _word_edges(surf, rules, word_like):
            cost = (sum(1 for r in rl if RULES[r]["optional"]), len(rl))
            if s not in outp or cost < outp[s][0]:
                outp[s] = (cost, rl)
    return {s: rl for s, (cost, rl) in outp.items()}


def derive_words(words, word_like):
    """Multi-word headwords: derive each word, then join the results."""
    per_word = [derive(w, word_like) for w in words]
    if any(not d for d in per_word):
        return {}
    outp = {}
    combos = itertools.islice(itertools.product(*[sorted(d.items()) for d in per_word]), 4096)
    for combo in combos:
        s = "".join(x for x, _ in combo)
        rl = [r for _, rules in combo for r in rules]
        cost = (sum(1 for r in rl if RULES[r]["optional"]), len(rl))
        if s not in outp or cost < outp[s][0]:
            outp[s] = (cost, rl)
    return {s: rl for s, (cost, rl) in outp.items()}
