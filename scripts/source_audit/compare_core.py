#!/usr/bin/env python3
"""
Comparing a stored value with the printed text of its entry
===========================================================

Used by the Skiri-to-English comparison (s2e_compare.py) and the
English-to-Skiri one (e2s_compare.py).

A printed entry is a run of spans. A stored value is looked for in it in three
steps, strictest first:

  1. skeleton match. Both sides with white space and hyphens removed. Print
     breaks words at line ends with a hyphen and the stored value has the word
     joined, so the two cannot be compared character for character until it is
     known where the value sits. The skeleton finds the place.
  2. exactness. The printed stretch that was found is put back together, once
     for each way of reading its line-end hyphens (a hyphen at a line end is
     either a break or a real hyphen), and compared with the stored value. If
     none of the readings is equal, the difference is one of spacing or of
     hyphens, and it is reported.
  3. nearest match. A value with no skeleton match is aligned with the most
     similar stretch of the entry, and the differences are listed.

Nothing is ever skipped silently: a value is equal, or it is a difference with
a kind.
"""
import difflib
import itertools
import re
import unicodedata

ACUTE, GRAVE = "́", "̀"
SYLLABLE_DOT, EDGE_DASH = "·", "–"
WS = set(" \t\n\r ")

KIND = {"PlainsArial": "S", "PAdothyphen": "P", "CenturySchoolbookN.Plain": "C", "TruteauGaramond": "E",
        "LucidaSansUnicode": "S", "CSNPdothyphen": "E", "Garamond": "E"}


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def stored_phonetic_as_printed(s):
    """A stored phonetic form in the printed notation.

    Since 2026-11-13 the database stores Parks's own notation, and such a form is returned as it
    is. A form still in the old working notation (hyphen for the syllable dot, bullet for the edge
    dash, à for ə́) is converted, so that files not yet rewritten can still be compared.
    """
    s = nfc(s)
    if SYLLABLE_DOT in s or EDGE_DASH in s or not ("-" in s or "•" in s):
        return s
    s = s.replace("-", SYLLABLE_DOT).replace("•", EDGE_DASH)
    # the stored a-grave is the printed schwa-acute, except directly after a plain a, where it is
    # the second half of a long vowel and a true a-grave (two forms in the dictionary)
    return nfc(re.sub("(?<!a)à", "ə" + ACUTE, s))


LAX_FOLD = [(nfc("ɪ" + ACUTE), "í"), (nfc("ɪ" + GRAVE), "ì")]


def fold_lax_i(s):
    """Printed lax i with an accent -> the i with an accent that the database writes for it."""
    for a, b in LAX_FOLD:
        s = s.replace(a, b)
    return s


def tidy(s):
    s = nfc(s).replace(" ", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r" +([,;.:)!?>\]}])", r"\1", s)
    s = re.sub(r"([(\[{<]) +", r"\1", s)
    return s.strip()


def skeleton(s):
    return "".join(ch for ch in nfc(s) if ch not in WS and ch != "-")


class Block:
    """The printed text of one entry, with a map from its skeleton back to the page."""

    def __init__(self, spans):
        text, kinds, span_of = [], [], []
        for i, s in enumerate(spans):
            if s.get("nl") and i > 0:
                text.append("\n"); kinds.append("N"); span_of.append(i)
            k = KIND.get(s["f"], "E")
            for ch in s["t"]:
                text.append(ch); kinds.append(k); span_of.append(i)
        self.orig = "".join(text)
        self.kinds = kinds
        self.span_of = span_of
        self.spans = spans
        sk, idx = [], []
        for i, ch in enumerate(self.orig):
            if ch in WS or ch == "-":
                continue
            sk.append(ch); idx.append(i)
        self.sk = "".join(sk)
        self.idx = idx
        self.covered = bytearray(len(self.sk))
        self.sk_folded = fold_lax_i(self.sk) if ("ɪ" + ACUTE in self.sk or "ɪ" + GRAVE in self.sk) else None

    def kind_at(self, sk_pos):
        return self.kinds[self.idx[sk_pos]] if 0 <= sk_pos < len(self.idx) else "E"

    def find(self, sk_value, prefer_kind=None, value=""):
        """Every skeleton position where the value occurs; uncovered ones first, then the wanted font kind."""
        hits, start = [], 0
        while True:
            p = self.sk.find(sk_value, start)
            if p < 0:
                break
            hits.append(p)
            start = p + 1
        if not hits:
            return None
        def rank(p):
            free = not any(self.covered[p:p + len(sk_value)])
            kind_ok = prefer_kind is None or self.kind_at(p) == prefer_kind
            whole = self.whole_words(p, p + len(sk_value), value)
            return (0 if whole else 1, 0 if free else 1, 0 if kind_ok else 1, p)
        return min(hits, key=rank)

    @staticmethod
    def _word_char(ch):
        return ch.isalpha() or ch == "ʔ" or unicodedata.combining(ch) != 0

    def stretch(self, a, b):
        return self.idx[a], self.idx[b - 1] + 1

    def whole_words(self, a, b, value=""):
        """False when the stretch begins or ends in the middle of a printed word."""
        o0, o1 = self.stretch(a, b)
        text = self.orig
        if self._word_char(text[o0]) and o0 > 0 and not value.strip().startswith("-"):
            if self._word_char(text[o0 - 1]):
                return False
            if LINE_END_HYPHEN_BEFORE.search(text[:o0]):          # the word began on the line above
                return False
        if self._word_char(text[o1 - 1]) and o1 < len(text) and not value.strip().endswith("-"):
            if self._word_char(text[o1]):
                return False
            m = LINE_END_HYPHEN.match(text, o1)
            if m and m.end() < len(text) and self._word_char(text[m.end()]):   # the word goes on, on the next line
                return False
        return True

    def whole_word_text(self, a, b):
        """The stretch widened to the ends of the printed words it cuts into."""
        o0, o1 = self.stretch(a, b)
        text = self.orig
        while o0 > 0:
            if self._word_char(text[o0 - 1]):
                o0 -= 1
                continue
            m = LINE_END_HYPHEN_BEFORE.search(text[:o0])
            if m and self._word_char(text[o0]):
                o0 = m.start()
                continue
            break
        while o1 < len(text):
            if self._word_char(text[o1]):
                o1 += 1
                continue
            m = LINE_END_HYPHEN.match(text, o1)
            if m and m.end() < len(text) and self._word_char(text[m.end()]) and self._word_char(text[o1 - 1]):
                o1 = m.end()
                continue
            break
        return text[o0:o1]

    def cover(self, a, b):
        for i in range(a, b):
            self.covered[i] = 1

    def printed(self, a, b, value=""):
        """The printed stretch for skeleton positions a..b, with hyphens at its ends if the value has them."""
        o0, o1 = self.idx[a], self.idx[b - 1] + 1
        v = nfc(value).strip()
        lead = len(v) - len(v.lstrip("-"))
        trail = len(v) - len(v.rstrip("-"))
        while lead and o0 > 0 and self.orig[o0 - 1] == "-":
            o0 -= 1; lead -= 1
        while trail and o1 < len(self.orig) and self.orig[o1] == "-":
            o1 += 1; trail -= 1
        return self.orig[o0:o1]

    def boxes(self, a=None, b=None):
        """Where a stretch is on the page: one [page, x0, y0, x1, y1] per printed line. No range: the headword line."""
        if a is None or b is None or b <= a or not self.idx:
            spans = []
            for i, s in enumerate(self.spans):
                if i > 0 and s.get("nl"):
                    break
                spans.append(i)
        else:
            o0, o1 = self.idx[a], self.idx[min(b, len(self.idx)) - 1] + 1
            spans = sorted(set(self.span_of[o0:o1]))
        lines = {}
        for i in spans:
            s = self.spans[i]
            if not s["t"].strip():
                continue
            key = (s["p"], round(s["b"][3] / 4.0))
            x0, y0, x1, y1 = s["b"]
            if key in lines:
                q = lines[key]
                lines[key] = [s["p"], min(q[1], x0), min(q[2], y0), max(q[3], x1), max(q[4], y1)]
            else:
                lines[key] = [s["p"], x0, y0, x1, y1]
        return [[v[0]] + [round(x, 1) for x in v[1:]] for v in lines.values()]

    def residue(self):
        """Stretches of the entry that no stored value accounts for: (skeleton start, text, kinds)."""
        runs, i = [], 0
        n = len(self.sk)
        while i < n:
            if self.covered[i]:
                i += 1
                continue
            j = i
            while j < n and not self.covered[j]:
                j += 1
            o0, o1 = self.idx[i], self.idx[j - 1] + 1
            kinds = "".join(sorted(set(self.kinds[o0:o1]) - {"N"}))
            runs.append((i, self.orig[o0:o1], kinds, self.boxes(i, j)))
            i = j
        return runs


LINE_END_HYPHEN = re.compile(r"-[ ]*\n[ ]*")
DOT_AT_LINE_END = re.compile(SYLLABLE_DOT + r"[ ]*\n[ ]*")
LINE_END_HYPHEN_BEFORE = re.compile(r"-[ ]*\n[ ]*$")


def readings(printed_raw, limit=64):
    """Every way of reading the line-end hyphens of a printed stretch."""
    # a phonetic form broken after a syllable dot continues on the next line with no space
    printed_raw = DOT_AT_LINE_END.sub(SYLLABLE_DOT, printed_raw)
    pieces = LINE_END_HYPHEN.split(printed_raw)
    pieces = [p.replace("\n", " ") for p in pieces]
    if len(pieces) == 1:
        return [tidy(pieces[0])]
    out = []
    for joins in itertools.islice(itertools.product(("", "-"), repeat=len(pieces) - 1), limit):
        s = pieces[0]
        for j, p in zip(joins, pieces[1:]):
            s += j + p
        out.append(tidy(s))
    return out


def best_reading(value, printed_raw):
    """The reading of the printed stretch closest to the value (for showing to a person)."""
    v = tidy(value)
    rs = readings(printed_raw)
    return min(rs, key=lambda r: (r != v, -difflib.SequenceMatcher(None, r, v, autojunk=False).ratio()))


def nearest(block, sk_value):
    """Best approximate place for a value in the block: (ratio, a, b) in skeleton positions."""
    if not block.sk or not sk_value:
        return 0.0, 0, 0
    m = difflib.SequenceMatcher(None, block.sk, sk_value, autojunk=False)
    blocks = [b for b in m.get_matching_blocks() if b.size]
    if not blocks:
        return 0.0, 0, 0
    # the offset (position in block minus position in value) that most matched characters agree on
    votes = {}
    for b in blocks:
        votes[b.a - b.b] = votes.get(b.a - b.b, 0) + b.size
    best = None
    for off in sorted(votes, key=votes.get, reverse=True)[:4]:
        near = [b for b in blocks if abs((b.a - b.b) - off) <= max(6, len(sk_value) // 6)]
        a = max(0, min(b.a - b.b for b in near))
        z = min(len(block.sk), max(b.a + (len(sk_value) - b.b) for b in near))
        a = max(0, min(a, min(b.a for b in near)))
        window = block.sk[a:z]
        r = difflib.SequenceMatcher(None, window, sk_value, autojunk=False).ratio()
        if best is None or r > best[0]:
            best = (r, a, z)
    r, a, z = best
    # trim the window to the first and last matched characters
    ops = difflib.SequenceMatcher(None, block.sk[a:z], sk_value, autojunk=False).get_opcodes()
    if ops and ops[0][0] == "delete":
        a += ops[0][2] - ops[0][1]
    if ops and ops[-1][0] == "delete":
        z -= ops[-1][2] - ops[-1][1]
    return r, a, max(a, z)


def edits(stored_sk, printed_sk):
    """Character differences, each widened to whole letters: [(stored bit, printed bit, context)]."""
    out = []
    m = difflib.SequenceMatcher(None, stored_sk, printed_sk, autojunk=False)
    for op, i1, i2, j1, j2 in m.get_opcodes():
        if op == "equal":
            continue
        # keep combining marks with their base letter
        while i1 > 0 and i1 < len(stored_sk) and unicodedata.combining(stored_sk[i1]):
            i1 -= 1; j1 = max(0, j1 - 1)
        while j1 > 0 and j1 < len(printed_sk) and unicodedata.combining(printed_sk[j1]):
            j1 -= 1; i1 = max(0, i1 - 1)
        while i2 < len(stored_sk) and unicodedata.combining(stored_sk[i2]):
            i2 += 1
        while j2 < len(printed_sk) and unicodedata.combining(printed_sk[j2]):
            j2 += 1
        out.append((stored_sk[i1:i2], printed_sk[j1:j2], printed_sk[max(0, j1 - 6):j2 + 6]))
    return out


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))


# printed letter -> what the earlier decoding steps stored for it (citations from other languages)
STANDIN_STORED = {"š": "ó", "é": "Ý", "ó": "í", "ą": "Ó", nfc("ą" + ACUTE): "Ô", "į": "è", "ž": "ü", "ⁱ": "š", "Ȟ": "´"}
VOWELS = set("aiuəɪʊeo")
PUNCT = set(".,;:!?()[]{}<>/+•'\"’‘=*…") | {SYLLABLE_DOT, EDGE_DASH}


def edit_kind(a, b):
    """Kind of one difference: a is stored, b is printed."""
    if fold_lax_i(b) == a or fold_lax_i(a) == fold_lax_i(b):
        return "lax-i-symbol"
    if "".join(STANDIN_STORED.get(ch, ch) for ch in b) == a:
        return "citation-standin"
    if a.replace("ː", "") == strip_accents(b) and "ː" in a:
        return "length-mark-for-accent"
    if strip_accents(a) == strip_accents(b):
        return "accent"
    ga, gb = a.replace("ʔ", "").replace("'", "").replace("’", ""), b.replace("ʔ", "").replace("'", "").replace("’", "")
    if ga == gb:
        return "glottal-stop"
    if all(ch in PUNCT for ch in a + b):
        return "punctuation"
    if a.lower() == b.lower():
        return "capital"
    if set(a) <= VOWELS and set(b) <= VOWELS and (a.startswith(b) or b.startswith(a)) and len(set(a + b)) == 1:
        return "vowel-length"
    if not a:
        return "printed-has-more"
    if not b:
        return "stored-has-more"
    return "letters"
