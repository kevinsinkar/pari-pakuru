#!/usr/bin/env python3
"""
The English index rebuilt from the printed page (2026-11-14)
============================================================

The English-to-Skiri section of the dictionary (book pages 63 to 346) lists
the Skiri entries again under English headwords and adds cross-references
("abate (of a fever)  see cool off (non-liquid) {kikarik}"). Two copies of it
are kept: the file Dictionary Data/english_to_skiri_linked.json, read from the
pages by an AI model in February 2026, and the database tables english_index
and cross_references, loaded from an earlier state of that file and never
loaded again.

The section has a text layer, and it is typeset with one font for each kind
of thing: the English headword, the Skiri term, the phonetic form, the class,
the cross-reference. This script reads the entries from the text layer by
those fonts and makes both copies say what the page says:

    python scripts/repair_english_index.py            # what would change; changes nothing
    python scripts/repair_english_index.py --apply    # backs up, writes the file, reloads the two tables, appends the report
    python scripts/repair_english_index.py --show stop   # one printed entry as the script reads it
    python scripts/repair_english_index.py --check    # exit 1 unless the file and the tables say what the page says

What is taken from the page, for every printed entry:

    the English headword
    the page of the book (the file number plus 60, checked against the page
        number printed on every page)
    each Skiri term under it, in order, with its preverb, its phonetic form in
        Parks's symbols, its class and verb class
    the cross-references: each English term referred to, and the Skiri forms
        printed in braces after it

What is kept from the file: the rest of a subentry (glosses, etymology, verb
forms, examples), for every subentry that is paired with a printed one. That
rest has not been compared with the page field by field; the entry a row
links to holds the verified text.

What is removed: placeholder values the first reading wrote where the page
has nothing ("(see cross-reference)", "N/A", ""), and subentries no printed
term accounts for. Printed terms and headwords the file lacks are added with
what the page prints.

Links. Every Skiri term is linked again to its dictionary entry: by headword
and preverb; among several entries with the same headword, by phonetic form,
then class, then by which entry's glosses are printed under the term. A term
that fits no entry, or fits several equally, is left unlinked and listed.

A hyphen at the end of a printed line may belong to the word or not; the
place itself cannot say. Such a form is read the way the same form is printed
without a break: as a dictionary headword, or as a term of the English entry
the cross-reference points to. Where neither settles it, the hyphen is
dropped and the form is listed in the report.

After --apply run:
    python scripts/source_audit/e2s_compare.py --source json --out reports/source_audit_2026-11/after_fixes
    python scripts/source_audit/e2s_compare.py --source db   --out reports/source_audit_2026-11/after_fixes
    python scripts/db_dump.py --write
"""
import argparse
import collections
import copy
import datetime as dt
import difflib
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import compare_core as cc  # noqa: E402
import e2s_compare  # noqa: E402
import s2e_compare  # noqa: E402
import state  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
E2S_JSON = ROOT / "Dictionary Data" / "english_to_skiri_linked.json"
REPORT = ROOT / "reports" / "english_index_repair_report.txt"
OFFSET = 60                        # book page = file number + 60, checked below on every page
BODY_TOP, BODY_BOTTOM = 56.0, 652.0
TODAY = "2026-11-14"
PLACEHOLDER = re.compile(r"^\W*$|^n/?a$|^null$|^none$|see\s*cross-?\s*reference", re.I)
PREVERB = re.compile(r"^(?P<term>.+?)\s+(?P<pre>(?:\((?:[^()\s]*\.\.\.)+\)|\[\+?[^\]]*\])(?:\s*(?:\((?:[^()\s]*\.\.\.)+\)|\[[^\]]*\]))*)$")
PREVERB_BROKEN = re.compile(r"\.\.\.[ ]*\n[ ]*(?=[a-z]+\.\.)")
BOUND_BEFORE_BRACKET = re.compile(r"-[ ]*\n[ ]*(?=[(\[])")
# Forms broken at a line end that nothing else in the section settles, decided one by one: {printed, "|" at the line end: (reading, why)}
SETTLED = {
    "kskiitikstaaruʔ-ruksiriʔ, kskiitikstaaruʔ-a- | ruksiriʔ, kskiitiks-ruksiriʔ, kskiitiks-a-ruksiriʔ": (
        "kskiitikstaaruʔ-ruksiriʔ, kskiitikstaaruʔ-a-ruksiriʔ, kskiitiks-ruksiriʔ, kskiitiks-a-ruksiriʔ",
        "the same head prints kskiitiks-a-ruksiriʔ on one line: the hyphen after a belongs to the word"),
}
VCLASS = re.compile(r"^\s*(\([^)]{1,12}\))")
CLASS_PUNCT = re.compile(r"^\s*(\([^)]{1,12}\))?\s*([,\-])?\s*$")


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.flush()


# ----------------------------------------------------------------------------- the printed page

def clean_breaks(piece):
    """Line ends that are not in doubt: the hyphen of a bound form before its preverb (irikata- | (ut...)),
    and a preverb broken inside its parentheses ((ir...ri... | ut...))."""
    piece = BOUND_BEFORE_BRACKET.sub("- ", piece)
    return PREVERB_BROKEN.sub("...", piece)


def kind(s):
    f, st, sz = s["f"], s["st"], s["sz"]
    if f == "PAdothyphen":
        return "P"                                   # phonetic form
    if f == "LucidaSansUnicode":
        return "L"                                   # the zero sign, set in another font
    if f == "PlainsArial" and st == "Bold" and sz > 8.5:
        return "T"                                   # a Skiri term
    if f == "TruteauGaramond" and st == "Bold" and sz > 9.6:
        return "H"                                   # English headword
    if f == "TruteauGaramond" and st == "Bold" and sz > 8.5:
        return "X"                                   # English term referred to
    if f == "TruteauGaramond" and st == "Italic" and re.fullmatch(r"\s*see(\s+also)?\s*", s["t"]):
        return "S"
    if f == "TruteauGaramond" and st == "" and abs(sz - 7.0) < 0.3:
        return "C"                                   # class, in small capitals
    return "E"


def raw(spans):
    return "".join(("\n" if s["nl"] and i else "") + s["t"] for i, s in enumerate(spans))


def blank(s):
    return s["t"].strip() == ""


def printed_folios():
    folios = {}
    for f in sorted(e2s_compare.TEXT.glob("e2s_*.json")):
        page = json.loads(f.read_text(encoding="utf-8"))
        folios[page["unit"]] = [int(s["t"].strip()) for s in page["spans"]
                                if not (BODY_TOP < s["b"][1] < BODY_BOTTOM) and s["t"].strip().isdigit()]
    return folios


def split_top(text, sep=","):
    """Split at separators that are outside every bracket."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def parse_entry(p):
    """One printed entry: its subentries (term, phonetic form, class) and its cross-references."""
    spans, n, i = p["spans"], len(p["spans"]), 0
    while i < n and (e2s_compare.is_head_span(spans[i]) or blank(spans[i])):
        i += 1
    subs, sees, notes = [], [], []
    cur, see, depth = None, None, 0
    while i < n:
        s = spans[i]
        k = kind(s)
        if k == "S":
            see = {"after": len(subs), "parts": []}
            sees.append(see)
            depth = 0
            i += 1
            continue
        if see is not None:
            starts_term = k == "T" and depth == 0 and not s["t"].lstrip().startswith("{") and s["t"].strip()
            if not starts_term:
                if k in ("X", "T", "L"):
                    see["parts"].append(("T" if k == "L" else k, ("\n" if s["nl"] else "") + s["t"]))
                    if k != "X":
                        depth += s["t"].count("{") - s["t"].count("}")
                elif not blank(s):
                    see["parts"].append(("O", ("\n" if s["nl"] else "") + s["t"]))
                    notes.append("other print inside a cross-reference: %r" % s["t"])
                i += 1
                continue
            see = None                                # a Skiri term outside braces: the next subentry begins
        nxt = spans[i + 1] if i + 1 < n else None
        head_start = k == "T" and s["t"].strip() or (k == "L" and s["sz"] > 8.5 and nxt is not None and kind(nxt) in ("T", "P"))
        if head_start:
            j, run = i, []
            while j < n and (kind(spans[j]) == "T" or (kind(spans[j]) == "L" and spans[j]["sz"] > 8.5)):
                run.append(spans[j])
                j += 1
            phon = []
            while j < n and (kind(spans[j]) == "P" or (kind(spans[j]) == "L" and spans[j]["sz"] < 8.5 and phon)):
                phon.append(spans[j])
                j += 1
            # the class: small capitals (VT, N), a verb class in parentheses after it, commas between several,
            # and a hyphen inside N-DEP; the pieces are separate spans and may stand on two lines
            classes, vclasses, rest, glue = [], [], None, False      # glue: "-" or " " joins the next piece to the class before
            while j < n:
                sp, kk = spans[j], kind(spans[j])
                if kk == "C":
                    word = sp["t"].strip()
                    if word:
                        if glue and classes:
                            classes[-1] += glue + word
                        else:
                            classes.append(word)
                        glue = False
                    j += 1
                    continue
                if kk != "E" or abs(sp["sz"] - 9.1) > 0.3 or sp["st"]:
                    break
                text, width = sp["t"], 1
                if re.match(r"^\s*\([^)]*$", text) and j + 1 < n and kind(spans[j + 1]) == "E":
                    text, width = text + spans[j + 1]["t"], 2          # "(1-" at a line end, "a) be drunk" on the next
                if text.strip() == "." and classes:
                    classes[-1] += "."                                 # IRR. VI
                    glue = " "
                    j += 1
                    continue
                m = CLASS_PUNCT.match(text)
                if m and (m.group(1) or m.group(2)):
                    if m.group(1):
                        vclasses.append(m.group(1))
                    glue = "-" if m.group(2) == "-" else False
                    j += width
                    continue
                if classes:
                    m = VCLASS.match(text)
                    if m:
                        vclasses.append(m.group(1))
                        rest = text[m.end():]
                        j += width
                break
            if not phon and not classes:
                # bold Skiri in the running text of an entry, not the head of a subentry
                notes.append("bold Skiri that heads no subentry: %r" % raw(run))
                if cur is not None:
                    cur["body"] += raw(run)
                i = j
                continue
            cur = {"head_raw": raw(run), "phon_raw": raw(phon), "classes": classes, "vclasses": vclasses,
                   "body": rest or "", "box": [run[0]["p"]] + list(run[0]["b"])}
            subs.append(cur)
            i = j
            continue
        if cur is not None:
            cur["body"] += ("\n" if s["nl"] else "") + s["t"]
        elif not blank(s):
            notes.append("print before the first term: %r" % s["t"][:60])
        i += 1
    return subs, sees, notes


def see_items(parts):
    """[(English term as printed, raw), [Skiri forms, raw]] from the pieces of one cross-reference list."""
    items, target, skiri = [], "", ""

    def close():
        nonlocal target, skiri
        if target.strip() or skiri.strip():
            items.append((target, skiri))
        target, skiri = "", ""

    for k, t in parts:
        if k == "X":
            for m, piece in enumerate(t.split(";")):
                if m:
                    close()
                elif skiri.strip() and piece.strip():
                    close()                           # a new English term straight after a brace, with no semicolon
                target += piece
        elif k == "T":
            skiri += t
    close()
    out_items = []
    for target, skiri in items:
        inner = skiri.strip()
        if inner.startswith("{"):
            inner = inner[1:]
        if inner.endswith("}"):
            inner = inner[:-1]
        forms = [f for f in split_top(inner) if f.strip()]
        out_items.append((target, forms))
    return out_items


class Printed:
    """The whole English-to-Skiri section as read from the text layer."""

    def __init__(self, conn):
        folios = printed_folios()
        wrong = {n: d for n, d in folios.items() if d and d != [n + OFFSET]}
        if wrong or not folios:
            raise SystemExit("stop: the printed page number is not the file number plus %d: %s" % (OFFSET, dict(list(wrong.items())[:8])))
        self.pages_with_folio = sum(1 for d in folios.values() if d)
        self.pages = len(folios)
        self.entries = e2s_compare.segment()
        self.lex = [dict(zip(("entry_id", "headword", "stem_preverb", "phonetic_form", "grammatical_class", "verb_class"), r))
                    for r in conn.execute("select entry_id, headword, coalesce(stem_preverb, ''), phonetic_form, grammatical_class, verb_class "
                                          "from lexical_entries where coalesce(source, 'parks') = 'parks'")]
        self.gloss = collections.defaultdict(list)
        for eid, text in conn.execute("select entry_id, definition from glosses"):
            self.gloss[eid].append(text or "")
        self.by_skel, self.by_loose, self.by_head = (collections.defaultdict(list) for _ in range(3))
        self.known = collections.defaultdict(set)          # skeleton -> spellings of that form printed without a line break
        for e in self.lex:
            key = s2e_compare.db_key(e)
            self.by_skel[cc.skeleton(key)].append(e)
            self.by_loose[s2e_compare.loose_key(key)].append(e)
            self.by_head[cc.skeleton(e["headword"])].append(e)
            self.known[cc.skeleton(key)].add(cc.tidy(key))
            self.known[cc.skeleton(e["headword"])].add(cc.tidy(e["headword"]))
            for variant in split_top(e["headword"]):        # "haawaʔ, hawaa": two forms under one head
                v = cc.tidy(variant)
                if v:
                    self.known[cc.skeleton(v)].add(v)
                    if e["stem_preverb"]:
                        self.known[cc.skeleton(v + e["stem_preverb"])].add("%s %s" % (v, e["stem_preverb"]))
        self.heads = collections.defaultdict(set)           # skeleton of an English headword -> its spellings
        for p in self.entries:
            self.heads[cc.skeleton(p["head"]).lower()].add(p["head"])
        self.undecided, self.notes, self.unlinked, self.settled = [], [], [], []
        parsed = [parse_entry(p) for p in self.entries]
        # first the terms: a term printed on one line is evidence for the same form broken elsewhere
        for p, (subs, sees, notes) in zip(self.entries, parsed):
            for s in subs:
                rs = cc.readings(clean_breaks(s["head_raw"]))
                if len(rs) == 1:
                    self.known[cc.skeleton(rs[0])].add(rs[0])
        self.broken = collections.defaultdict(list)        # skeleton -> the readings of each broken occurrence
        for p, (subs, sees, notes) in zip(self.entries, parsed):
            pieces = [s["head_raw"] for s in subs]
            for x in sees:
                for target, forms in see_items(x["parts"]):
                    pieces += forms
            for piece in pieces:
                rs = cc.readings(clean_breaks(piece))
                if len(rs) > 1:
                    self.broken[cc.skeleton(rs[0])].append(rs)
        self.model = []
        for p, (subs, sees, notes) in zip(self.entries, parsed):
            for note in notes:
                self.notes.append("%s (p. %d): %s" % (p["head"], p["page"] + OFFSET, note))
            head = re.sub(r",(?=[^\s,])", ", ", p["head"])
            if head != p["head"]:
                self.notes.append("%s (p. %d): the text layer has no space after the comma; read as %r, as every other "
                                  "headword of this pattern is printed" % (p["head"], p["page"] + OFFSET, head))
            entry = {"seq": p["seq"], "head": head, "file": p["page"], "page": p["page"] + OFFSET,
                     "column": "left" if p["col"] == 0 else "right", "subs": [], "see": []}
            for s in subs:
                entry["subs"].append(self.subentry(p, s))
            if len(sees) > 1 or (sees and sees[0]["after"] != len(subs)):
                self.notes.append("%s (p. %d): %d cross-reference lists, placed after subentries %s of %d" % (
                    p["head"], entry["page"], len(sees), [x["after"] for x in sees], len(subs)))
            for x in sees:
                for target, forms in see_items(x["parts"]):
                    entry["see"].append({"english_term": self.english(p, target),
                                         "skiri_equivalents": [self.skiri(p, f) for f in forms], "after": x["after"]})
            self.model.append(entry)

    def skiri(self, p, piece, prefer=None):
        """A Skiri form as printed; line-end hyphens read as the same form is printed without a break."""
        piece = clean_breaks(piece)
        rs = cc.readings(piece)
        if len(rs) == 1:
            return rs[0]
        if prefer and prefer in rs:
            return prefer
        sk = cc.skeleton(rs[0])
        spellings = self.known.get(sk, set()) & set(rs)
        if len(spellings) == 1:
            return next(iter(spellings))
        # the same form broken at another place elsewhere in the section: only a reading both allow can be right
        common = set(rs)
        for other in self.broken.get(sk, []):
            common &= set(other)
        if len(common) == 1:
            return next(iter(common))
        key = cc.tidy(piece.replace("\n", " | "))
        if key in SETTLED:
            self.settled.append("%s (p. %d): %s  read as %s: %s" % (p["head"], p["page"] + OFFSET, key, SETTLED[key][0], SETTLED[key][1]))
            return SETTLED[key][0]
        self.undecided.append("%s (p. %d): %s" % (p["head"], p["page"] + OFFSET, cc.tidy(piece.replace("\n", " | "))))
        return rs[0]

    def english(self, p, piece):
        rs = cc.readings(piece)
        if len(rs) == 1:
            return rs[0]
        spellings = self.heads.get(cc.skeleton(rs[0]).lower(), set()) & set(rs)
        if len(spellings) == 1:
            return next(iter(spellings))
        self.undecided.append("%s (p. %d): English %s" % (p["head"], p["page"] + OFFSET, cc.tidy(piece.replace("\n", " | "))))
        return rs[0]

    def subentry(self, p, s):
        body = cc.tidy(s["body"].replace("\n", " "))
        rs = cc.readings(s["head_raw"])
        phon_rs = cc.readings(s["phon_raw"]) if s["phon_raw"].strip() else [""]
        entry_id, how = self.link(rs[0], phon_rs, s["classes"], s["vclasses"], s["body"])
        linked = next((e for e in self.lex if e["entry_id"] == entry_id), None) if entry_id else None
        full = self.skiri(p, s["head_raw"], prefer=cc.tidy(s2e_compare.db_key(linked)) if linked else None)
        phon = phon_rs[0]
        if linked and len(phon_rs) > 1:
            same = [r for r in phon_rs if cc.nfc(r) == cc.nfc(linked["phonetic_form"] or "")]
            phon = same[0] if same else phon
        m = PREVERB.match(full)
        term, pre = (m.group("term"), m.group("pre")) if m else (full, None)
        if not entry_id:
            self.unlinked.append("%s (p. %d): %s %s %s  [%s]" % (p["head"], p["page"] + OFFSET, full, phon, " ".join(s["classes"]), how))
        return {"term": term, "preverb": pre, "key": full, "phonetic": phon or None,
                "class": ", ".join(s["classes"]) or None, "verb_class": ", ".join(s["vclasses"]) or None,
                "entry_id": entry_id, "match": how, "text": body}

    def link(self, full, phon_rs, classes, vclasses, body):
        c = self.by_skel.get(cc.skeleton(full)) or self.by_loose.get(s2e_compare.loose_key(full)) or []
        how = "headword"
        if not c:
            m = PREVERB.match(full)
            c = self.by_head.get(cc.skeleton(m.group("term") if m else full)) or []
            how = "headword, another preverb"
            if not c:
                return None, "no dictionary entry with this headword"
        if len(c) > 1:
            ph = {cc.skeleton(r) for r in phon_rs}
            narrowed = [e for e in c if cc.skeleton(e["phonetic_form"] or "") in ph]
            if narrowed:
                c, how = narrowed, how + ", phonetic form"
        if len(c) > 1:
            toks = s2e_compare.class_tokens(" ".join(classes + vclasses))
            narrowed = [e for e in c if set(s2e_compare.class_tokens("%s %s" % (e["grammatical_class"] or "", e["verb_class"] or ""))) == set(toks)]
            if narrowed:
                c, how = narrowed, how + ", class"
        words = set(re.findall(r"[a-z]{4,}", cc.readings(body)[0].lower()))

        def shared(e):
            """The share of the entry's gloss words that are printed under this term."""
            own = set(re.findall(r"[a-z]{4,}", " ".join(self.gloss.get(e["entry_id"], [])).lower()))
            return len(own & words) / float(len(own)) if own else 0.0

        if len(c) > 1:
            scored = sorted(((shared(e), e) for e in c), key=lambda t: -t[0])
            if scored[0][0] >= 0.5 and scored[0][0] - scored[1][0] >= 0.2:
                c, how = [scored[0][1]], how + ", glosses"
        if len(c) > 1:
            return None, "%d dictionary entries fit equally" % len(c)
        e = c[0]
        ph = {letters(r) for r in phon_rs}
        toks = set(s2e_compare.class_tokens(" ".join(classes + vclasses)))
        agrees = (letters(e["phonetic_form"] or "") in ph or shared(e) >= 0.5
                  or (toks and set(s2e_compare.class_tokens("%s %s" % (e["grammatical_class"] or "", e["verb_class"] or ""))) == toks
                      and not (e["phonetic_form"] and phon_rs[0])))
        if not agrees:
            return None, "the dictionary entry with this headword has another phonetic form and other glosses"
        return e["entry_id"], how


# ----------------------------------------------------------------------------- the file

def is_placeholder(value):
    return value is None or bool(PLACEHOLDER.search(str(value).strip()))


def stored_key(sub):
    p1 = sub.get("part_I") or {}
    term = p1.get("skiri_term")
    if is_placeholder(term):
        return None
    pre = p1.get("stem_preverb")
    if pre and not is_placeholder(pre) and cc.skeleton(pre) not in cc.skeleton(term):
        term = "%s %s" % (term, pre)
    return term


def letters(phonetic):
    """A phonetic form without its brackets, spaces and edge dashes, and with the old spelling of the accented lax i."""
    return cc.fold_lax_i("".join(ch for ch in cc.skeleton(phonetic) if ch not in "[]" + cc.EDGE_DASH))


def similar(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def pair_lists(old_keys, new_keys, threshold=0.6):
    """Pairs of positions (old, new) of two lists in the same order; a position without a partner is left out."""
    pairs = []
    sm = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == "equal":
            pairs += list(zip(range(i0, i1), range(j0, j1)))
        elif tag == "replace":
            used = set()
            for i in range(i0, i1):
                best = max(((similar(old_keys[i], new_keys[j]), j) for j in range(j0, j1) if j not in used), default=(0, None))
                if best[1] is not None and best[0] >= threshold:
                    pairs.append((i, best[1]))
                    used.add(best[1])
    return pairs


def rebuild(data, printed):
    """The file as it should be, and a record of what differs from the file as it is."""
    tally = collections.Counter()
    lists = collections.defaultdict(list)
    old_heads = [cc.skeleton(e.get("english_entry_word") or "").lower() for e in data]
    new_heads = [cc.skeleton(m["head"]).lower() for m in printed.model]
    partner = {j: i for i, j in pair_lists(old_heads, new_heads, threshold=0.75)}
    kept = set(partner.values())
    merged = collections.defaultdict(list)                  # kept entry -> the entries with the same headword beside it
    orphans, orphan_at = [], {}
    for i, e in enumerate(data):
        if i not in kept:
            near = [k for k in range(max(0, i - 4), min(len(data), i + 5)) if k in kept and old_heads[k] == old_heads[i]]
            if near:
                k = min(near, key=lambda k: abs(k - i))
                merged[k].append(i)
                tally["entries the first reading had split in two (put together)"] += 1
                continue
            tally["entries of the file no printed headword accounts for (removed)"] += 1
            orphans.append(i)
    # first pass: pair the subentries of each entry, and collect what is left over on either side
    plan, pool, wanted = {}, collections.defaultdict(list), []
    for j, m in enumerate(printed.model):
        old_subs = []
        if j in partner:
            parts = sorted([partner[j]] + merged.get(partner[j], []))
            old_subs = [copy.deepcopy(s) for k in parts for s in data[k].get("subentries") or []]
        with_term = [(n, s) for n, s in enumerate(old_subs) if stored_key(s)]
        pairs = dict((b, a) for a, b in pair_lists([cc.skeleton(stored_key(s)) for _, s in with_term],
                                                   [cc.skeleton(x["key"]) for x in m["subs"]]))
        used = set(pairs.values())
        if len(with_term) == len(m["subs"]):                 # same number, same order: pair what is left by position,
            for b in range(len(m["subs"])):                   # if the phonetic forms show it is the same term
                if b not in pairs and b not in used:
                    stored_ph = letters(cc.stored_phonetic_as_printed(((with_term[b][1].get("part_I") or {}).get("phonetic_form")) or ""))
                    if stored_ph and similar(stored_ph, letters(m["subs"][b]["phonetic"] or "")) >= 0.8:
                        pairs[b] = b
                        used.add(b)
        plan[j] = (old_subs, with_term, pairs, used)
        for a, (n, s) in enumerate(with_term):
            if a not in used:
                pool[cc.skeleton(stored_key(s))].append((j, a))
        wanted += [(j, b) for b in range(len(m["subs"])) if b not in pairs]
    where = {i: j for j, i in partner.items()}
    for i in orphans:                                        # an entry no printed headword accounts for
        near = min(where, key=lambda k: abs(k - i))
        subs = [(n, s) for n, s in enumerate(data[i].get("subentries") or []) if stored_key(s)]
        plan[("orphan", i)] = (data[i].get("subentries") or [], subs, {}, set())
        for a, (n, s) in enumerate(subs):
            pool[cc.skeleton(stored_key(s))].append((("orphan", i), a))
            orphan_at[("orphan", i)] = where[near]
    moved_to, moved_from = {}, set()

    def position(k):
        return orphan_at[k] if isinstance(k, tuple) else k

    for j, b in wanted:
        near = [(abs(position(k) - j), str(k), k, a) for k, a in pool.get(cc.skeleton(printed.model[j]["subs"][b]["key"]), [])
                if abs(position(k) - j) <= 60 and (k, a) not in moved_from]
        if near:
            _, _, k, a = min(near)
            moved_to[(j, b)] = plan[k][1][a][1]
            moved_from.add((k, a))

    def printed_near(j, key):
        """Where a stored term that goes is printed: the headwords near by that have it as a term."""
        sk = cc.skeleton(key)
        heads = [printed.model[k]["head"] for k in range(max(0, j - 60), min(len(printed.model), j + 61))
                 if any(cc.skeleton(x["key"]) == sk for x in printed.model[k]["subs"])]
        return ("; printed, and kept, under %s" % ", ".join(repr(h) for h in heads[:3])) if heads else "; printed under no headword near by"

    for i in orphans:
        k = ("orphan", i)
        e = data[i]
        left = [stored_key(s) for a, (n, s) in enumerate(plan[k][1]) if (k, a) not in moved_from]
        lists["removed entries"].append("%s (file page %s); its terms: %s" % (
            e.get("english_entry_word"), (e.get("entry_metadata") or {}).get("page_number"),
            ", ".join("%s%s" % (t, printed_near(orphan_at[k], t)) for t in left) or "none left, all moved"))
    result = []
    for j, m in enumerate(printed.model):
        old = data[partner[j]] if j in partner else None
        entry = copy.deepcopy(old) if old else {"english_entry_word": None, "entry_metadata": {}, "subentries": []}
        if old is None:
            tally["printed headwords the file lacked (added)"] += 1
            lists["added entries"].append("%s (p. %d)" % (m["head"], m["page"]))
            entry["added_from_print"] = TODAY
        elif old.get("english_entry_word") != m["head"]:
            tally["English headwords corrected"] += 1
            lists["headwords"].append("%r -> %r (p. %d)" % (old.get("english_entry_word"), m["head"], m["page"]))
        entry["english_entry_word"] = m["head"]
        meta = entry.setdefault("entry_metadata", {})
        if meta.get("page_number") != m["page"]:
            tally["page numbers set to the page of the book"] += 1
        meta["page_number"], meta["source_page"], meta["column"] = m["page"], m["file"], m["column"]
        old_subs, with_term, pairs, used = plan[j]
        braces = {cc.skeleton(t) for x in m["see"] for t in x["skiri_equivalents"]}
        targets = {cc.skeleton(x["english_term"]).lower() for x in m["see"]}
        for a, (n, s) in enumerate(with_term):
            if a not in used and (j, a) in moved_from:
                tally["subentries stored under a neighbouring headword (moved to the one they are printed under)"] += 1
            elif a not in used:
                key = stored_key(s)
                ksk = cc.skeleton(key)
                if ksk in braces or any(ksk and (ksk in b or b in ksk) for b in braces):
                    tally["cross-reference forms the first reading had stored as terms (removed; they are in the cross-references)"] += 1
                elif any(t and t in ksk.lower() for t in targets) or "cross-reference" in key.lower():
                    tally["placeholder subentries (no term on the page) removed"] += 1
                else:
                    tally["subentries of the file no printed term accounts for (removed)"] += 1
                    lists["removed subentries"].append("%s (p. %d): %s%s" % (m["head"], m["page"], key, printed_near(j, key)))
        for n, s in enumerate(old_subs):
            p1 = s.get("part_I")
            if p1 and not stored_key(s):
                tally["placeholder subentries (no term on the page) removed"] += 1
        subs = []
        for b, x in enumerate(m["subs"]):
            paired = b in pairs or (j, b) in moved_to
            if b in pairs:
                sub = copy.deepcopy(with_term[pairs[b]][1])
            elif (j, b) in moved_to:
                sub = copy.deepcopy(moved_to[(j, b)])
            else:
                sub = {"part_I": {"grammatical_forms": [], "english_glosses": [], "etymology": None, "printed_text": x["text"]},
                       "part_II": None, "added_from_print": TODAY}
                tally["printed terms the file lacked (added)"] += 1
                lists["added subentries"].append("%s (p. %d): %s %s" % (m["head"], m["page"], x["key"], x["phonetic"] or ""))
            p1 = sub["part_I"]
            gc = p1.get("grammatical_classification")
            if not isinstance(gc, dict):
                gc = p1["grammatical_classification"] = {"class_abbr": None, "class_full_description": None, "verb_class": None}
            if paired:
                if cc.nfc(p1.get("skiri_term") or "") != x["term"] or (p1.get("stem_preverb") or None) != x["preverb"]:
                    tally["Skiri terms corrected (term or preverb)"] += 1
                    lists["terms"].append("%s (p. %d): %r %r -> %r %r" % (m["head"], m["page"], p1.get("skiri_term"), p1.get("stem_preverb"), x["term"], x["preverb"]))
                if cc.nfc(p1.get("phonetic_form") or "") != (x["phonetic"] or ""):
                    old_ph = cc.stored_phonetic_as_printed(p1.get("phonetic_form") or "")
                    what = "phonetic forms: notation only" if letters(old_ph) == letters(x["phonetic"] or "") \
                        else "phonetic forms: content corrected"
                    tally[what] += 1
                    if what.endswith("corrected"):
                        lists["phonetic"].append("%s (p. %d) %s: %r -> %r" % (m["head"], m["page"], x["key"], p1.get("phonetic_form"), x["phonetic"]))
            p1["skiri_term"], p1["stem_preverb"], p1["phonetic_form"] = x["term"], x["preverb"], x["phonetic"]
            stored_cls = "%s %s" % (gc.get("class_abbr") or "", gc.get("verb_class") or "")
            if set(s2e_compare.class_tokens(stored_cls)) != set(s2e_compare.class_tokens("%s %s" % (x["class"] or "", x["verb_class"] or ""))):
                if paired:
                    tally["classes corrected"] += 1
                    lists["classes"].append("%s (p. %d) %s: %r %r -> %r %r" % (m["head"], m["page"], x["key"], gc.get("class_abbr"), gc.get("verb_class"), x["class"], x["verb_class"]))
                gc["class_abbr"], gc["verb_class"] = x["class"], x["verb_class"]
            if paired and (sub.get("s2e_entry_id") or None) != x["entry_id"]:
                tally["links to a dictionary entry set or changed"] += 1
                if sub.get("s2e_entry_id") and x["entry_id"]:
                    lists["links"].append("%s (p. %d) %s: %s -> %s  [%s]" % (m["head"], m["page"], x["key"], sub.get("s2e_entry_id"), x["entry_id"], x["match"]))
                elif sub.get("s2e_entry_id"):
                    lists["links"].append("%s (p. %d) %s: %s -> none  [%s]" % (m["head"], m["page"], x["key"], sub.get("s2e_entry_id"), x["match"]))
            sub["subentry_number"] = b + 1
            sub["s2e_entry_id"], sub["s2e_match_type"] = x["entry_id"], x["match"]
            sub["part_III"] = {"cross_references": []}
            subs.append(sub)
        if not subs:
            subs.append({"subentry_number": 1, "part_I": None, "part_II": None, "part_III": {"cross_references": []},
                         "s2e_entry_id": None, "s2e_match_type": "cross-reference only"})
        for x in m["see"]:
            holder = subs[max(0, min(len(subs), x["after"]) - 1)]
            holder["part_III"]["cross_references"].append({"english_term": x["english_term"], "skiri_equivalents": x["skiri_equivalents"]})
        old_x = [(cc.tidy(r.get("english_term") or ""), [cc.tidy(t) for t in r.get("skiri_equivalents") or []])
                 for s in old_subs for r in (s.get("part_III") or {}).get("cross_references") or []]
        new_x = [(r["english_term"], r["skiri_equivalents"]) for r in m["see"]]
        if old is not None and old_x != new_x:
            tally["entries whose cross-references changed"] += 1
        entry["subentries"] = subs
        if old is not None and entry != old:
            tally["entries changed in all"] += 1
        result.append(entry)
    return result, tally, lists


# ----------------------------------------------------------------------------- the two tables

def table_rows(data):
    index, xrefs = [], []
    for e in data:
        word, page = e["english_entry_word"], e["entry_metadata"]["page_number"]
        for s in e["subentries"]:
            p1 = s.get("part_I") or {}
            gc = p1.get("grammatical_classification") or {}
            index.append((word, s.get("subentry_number") or 1, s.get("s2e_entry_id"), s.get("s2e_match_type"), p1.get("skiri_term"),
                          p1.get("phonetic_form"), gc.get("class_abbr"), gc.get("verb_class"), page, json.dumps(s, ensure_ascii=False)))
            for x in (s.get("part_III") or {}).get("cross_references") or []:
                if x.get("english_term"):
                    xrefs.append((word, x["english_term"], json.dumps(x.get("skiri_equivalents") or [], ensure_ascii=False), page))
    return index, xrefs


def stored_rows(conn):
    index = conn.execute("select english_word, subentry_number, entry_id, s2e_match_type, skiri_term, phonetic_form, grammatical_class, "
                         "verb_class, page_number, raw_subentry_json from english_index order by id").fetchall()
    xrefs = conn.execute("select from_english_word, to_english_term, skiri_equivalents, source_page from cross_references order by id").fetchall()
    return [tuple(r) for r in index], [tuple(r) for r in xrefs]


def reload_tables(conn, index, xrefs):
    conn.execute("delete from cross_references")
    conn.execute("delete from english_index")
    conn.execute("delete from sqlite_sequence where name in ('english_index', 'cross_references')")
    conn.executemany("insert into english_index (english_word, subentry_number, entry_id, s2e_match_type, skiri_term, phonetic_form, "
                     "grammatical_class, verb_class, page_number, raw_subentry_json) values (?,?,?,?,?,?,?,?,?,?)", index)
    conn.executemany("insert into cross_references (from_english_word, to_english_term, skiri_equivalents, source_page) values (?,?,?,?)", xrefs)
    conn.execute("insert into fts_english_index(fts_english_index) values ('rebuild')")


def bold_check(data, entries):
    """Every bold Skiri letter of the section against what is stored for the entry it is printed in.

    This does not go through the reading above: it takes all print in the font and size of Skiri terms, entry by
    entry, and the stored terms, preverbs and forms in braces, and counts letters. Returns (printed, stored, [entries
    where the two differ]).
    """
    def letters_of(text):
        return "".join(ch for ch in cc.skeleton(text) if ch not in "{},")

    n_printed = n_stored = 0
    bad = []
    if len(data) != len(entries):
        return 0, 0, ["the file has %d entries, the page %d" % (len(data), len(entries))]
    for e, p in zip(data, entries):
        a = letters_of("".join(s["t"] for s in p["spans"] if kind(s) == "T" or (kind(s) == "L" and s["sz"] > 8.5)))
        stored = ""
        for s in e["subentries"]:
            p1 = s.get("part_I") or {}
            if p1.get("skiri_term"):
                stored += p1["skiri_term"] + (p1.get("stem_preverb") or "")
            for x in (s.get("part_III") or {}).get("cross_references") or []:
                stored += "".join(x["skiri_equivalents"])
        b = letters_of(stored)
        n_printed += len(a)
        n_stored += len(b)
        if collections.Counter(a) != collections.Counter(b):
            bad.append("%s (p. %s)" % (e["english_entry_word"], e["entry_metadata"].get("page_number")))
    return n_printed, n_stored, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the file and the two tables (the default changes nothing)")
    ap.add_argument("--check", action="store_true", help="exit with 1 unless the file and the tables say what the page says")
    ap.add_argument("--show", metavar="HEADWORD", help="print one printed entry as the script reads it, and stop")
    ap.add_argument("--list", action="store_true", help="print the full lists (removed, added, unlinked, undecided)")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB))
    printed = Printed(conn)
    if args.show:
        for m in printed.model:
            if m["head"].lower() == args.show.lower():
                out(json.dumps(m, ensure_ascii=False, indent=1))
        return
    data = json.loads(E2S_JSON.read_text(encoding="utf-8"))
    result, tally, lists = rebuild(data, printed)
    index, xrefs = table_rows(result)
    old_index, old_xrefs = stored_rows(conn)
    with_term = [r for r in index if r[4]]
    linked = sum(1 for r in with_term if r[2])
    how = collections.Counter(r[3] for r in with_term)
    equivalents = [t for r in xrefs for t in json.loads(r[2])]
    eq_known = sum(1 for t in equivalents if cc.tidy(t) in printed.known.get(cc.skeleton(t), ()))
    targets_known = sum(1 for r in xrefs if r[1] in printed.heads.get(cc.skeleton(r[1]).lower(), ()))

    lines = ["The English index rebuilt from the printed page: %s, %s" % (
        "applied" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")), ""]
    lines.append("The page: %d printed English entries on %d pages; the page number printed on %d of them is the file number plus %d (the others print none)" % (
        len(printed.model), printed.pages, printed.pages_with_folio, OFFSET))
    lines.append("  %d Skiri terms under them; %d entries are cross-references only; %d cross-references with %d Skiri forms in braces" % (
        len(with_term), sum(1 for m in printed.model if not m["subs"]), len(xrefs), len(equivalents)))
    lines.append("  terms linked to a dictionary entry: %d of %d" % (linked, len(with_term)))
    for k, v in how.most_common():
        lines.append("      %-52s %d" % (k, v))
    lines.append("  cross-references: %d of %d point to a printed English headword; %d of %d Skiri forms in braces are a dictionary headword or a term of this section" % (
        targets_known, len(xrefs), eq_known, len(equivalents)))
    lines.append("")
    lines.append("The file %s: %d entries, %d subentries before; %d entries, %d subentries after" % (
        E2S_JSON.name, len(data), sum(len(e.get("subentries") or []) for e in data), len(result), sum(len(e["subentries"]) for e in result)))
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        lines.append("  %-66s %d" % (k, v))
    lines.append("")
    lines.append("The tables: english_index %d rows before, %d after (%d already as they will be); cross_references %d before, %d after (%d already)" % (
        len(old_index), len(index), len(set(old_index) & set(index)), len(old_xrefs), len(xrefs), len(set(old_xrefs) & set(xrefs))))
    lines.append("")
    lines.append("Left for a person: %d terms without a link, %d forms where a hyphen at a line end could not be settled, %d notes on the print" % (
        len(printed.unlinked), len(printed.undecided), len(printed.notes)))
    nothing = result == data and old_index == index and old_xrefs == xrefs
    n_printed, n_stored, bad = bold_check(result, printed.entries)
    lines.append("")
    lines.append("Letter count: %d letters are printed in the section in the type of Skiri terms; %d are stored as terms, preverbs "
                 "and forms in braces of the entries they stand in; entries where the two differ: %d" % (n_printed, n_stored, len(bad)))
    lines += ["    " + b for b in bad[:20]]
    lines.append("")
    lines.append("Nothing to change: the file and the two tables say what the page says." if nothing else
                 ("Applied." if args.apply else "Run again with --apply to write the file and the tables."))
    detail = []
    for title, items in [("Terms without a link", printed.unlinked), ("Line-end hyphens not settled (the hyphen is dropped)", printed.undecided),
                         ("Line-end hyphens settled one by one", printed.settled),
                         ("Links changed from one dictionary entry to another, or taken away", lists["links"]),
                         ("Notes on the print", printed.notes), ("Entries removed from the file", lists["removed entries"]),
                         ("Entries added from the page", lists["added entries"]), ("English headwords corrected", lists["headwords"]),
                         ("Subentries removed from the file", lists["removed subentries"]),
                         ("Subentries added from the page", lists["added subentries"]), ("Skiri terms corrected", lists["terms"]),
                         ("Phonetic forms corrected in content", lists["phonetic"]), ("Classes corrected", lists["classes"])]:
        detail += ["", "%s (%d)" % (title, len(items))] + ["  " + t for t in items]
    for line in lines:
        out(line)
    if args.list:
        for line in detail:
            out(line)
    if args.check:
        conn.close()
        sys.exit(0 if nothing and not bad else 1)
    if not args.apply or nothing:
        conn.close()
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    conn.close()
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_english_index.db" % stamp))
    shutil.copy2(E2S_JSON, backups / ("%s_backup_%s%s" % (E2S_JSON.stem, stamp, E2S_JSON.suffix)))
    tmp = E2S_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(E2S_JSON)
    conn = sqlite3.connect(str(DB))
    with conn:
        reload_tables(conn, index, xrefs)
    check = conn.execute("pragma integrity_check").fetchone()[0]
    conn.close()
    with REPORT.open("a", encoding="utf-8", newline="\n") as fh:       # appended: a later run must not wipe this record
        fh.write("\n".join(lines + ["backups: OneDrive/pari_pakuru_backups (stamp %s); integrity check: %s" % (stamp, check)] + detail) + "\n\n" + "=" * 100 + "\n\n")
    out("")
    out("written: %s, the two tables (integrity check: %s), %s" % (E2S_JSON.name, check, REPORT.relative_to(ROOT).as_posix()))


if __name__ == "__main__":
    main()
