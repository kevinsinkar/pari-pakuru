#!/usr/bin/env python3
"""
Stage 2b: the Skiri-to-English section, database against text layer
===================================================================

Every Parks entry in the database is paired with its printed entry, and every
field is looked for in the printed text (stored -> page). What is printed and
no stored field accounts for is listed too (page -> stored).

    python scripts/source_audit/s2e_compare.py                     # the live database
    python scripts/source_audit/s2e_compare.py --db COPY --out DIR # another copy (used by the recall test)

Writes, into reports/source_audit_2026-11/ (or DIR):
    s2e_differences.jsonl   one line per difference, with its kind, class and severity
    s2e_summary.json        counts
and into work/: s2e_pairs.jsonl (which printed entry each database entry was paired with).

Every difference gets a class:
    noise        not a difference in content; each kind of noise is a named rule below, with its count
    convention   the database writes a printed symbol another way, everywhere; reported once with its count
    difference   to be graded (stage 3)

Reads the database read-only. Changes nothing.
"""
import argparse
import collections
import difflib
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_core as cc  # noqa: E402
import state  # noqa: E402

PRINTED = state.WORK / "s2e_printed_entries.jsonl"
BOOK_PAGE_OFFSET = 348

# ---- the noise rules. Each was made after looking at examples of the kind; see findings.md ----
NOISE_RULES = {
    "structural-marks": "printed marks that separate the parts of an entry and are not stored as such: "
                        "the bullets before examples, < > round an etymology, { } round extra forms, sense numbers, commas between "
                        "fields, and the labels that introduce a cognate (i.q. SB, cf. Ar.)",
    "phonetic-spacing-at-punctuation": "the stored phonetic form has no space after the comma between two variants, or before a "
                                       "bracketed preverb; the print has one",
}
CONVENTIONS = {
    "lax-i-symbol": "printed lax i with an accent (ɪ́, ɪ̀) is stored as í, ì",
}
STRUCTURAL = set("•<>{}(),.;:0123456789 ")
# the labels that introduce a cognate ("i.q. SB", "cf. Ar."); the cognate itself is a stored field
LABELS = re.compile(r"\b(cf\.|i\.q\.|SB|Ar\.|Ki\.|Wi\.|Pa\.|Sk\.)")
CONTENT_KINDS_LOW = {"punctuation", "capital"}


def seqno(entry_id):
    m = re.search(r"-(\d+)$", entry_id)
    return int(m.group(1)) if m else 10 ** 9


def load_db(path):
    conn = sqlite3.connect("file:%s?mode=ro" % Path(path).resolve().as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    entries = {}
    for r in conn.execute("select * from lexical_entries where coalesce(source, '') != 'blue_book'"):
        e = dict(r)
        e.pop("raw_entry_json", None)
        e.update(glosses=[], etymology=[], forms=[], examples=[], cognates=[], derived=[])
        entries[e["entry_id"]] = e
    for table, key, order in (("glosses", "glosses", "id"), ("etymology", "etymology", "id"),
                              ("paradigmatic_forms", "forms", "form_number, id"), ("examples", "examples", "id"),
                              ("cognates", "cognates", "id"), ("derived_stems", "derived", "id")):
        for r in conn.execute('select * from "%s" order by %s' % (table, order)):
            if r["entry_id"] in entries:
                if table == "examples" and (r["source"] or "parks_dictionary") != "parks_dictionary":
                    continue
                entries[r["entry_id"]][key].append(dict(r))
    conn.close()
    return entries


def db_key(e):
    return cc.tidy(e["headword"] + (" " + e["stem_preverb"] if e["stem_preverb"] else ""))


def loose_key(key):
    key = re.sub(r"\[[^\]]*\]", " ", key)
    return "".join(sorted(cc.skeleton(key)))


def class_tokens(text):
    return sorted(re.findall(r"\([^)]*\)|[A-Za-z][A-Za-z.\-]*", (text or "").replace(" ", "")))


def quick_score(e, block):
    """Share of an entry's main fields that occur in a printed entry. Used only to pair homographs."""
    values = []
    if e["phonetic_form"]:
        values.append(cc.fold_lax_i(cc.skeleton(cc.stored_phonetic_as_printed(e["phonetic_form"]))))
    if e["grammatical_class"]:
        values.append(cc.skeleton(e["grammatical_class"]))
    values += [cc.skeleton(g["definition"] or "") for g in e["glosses"]]
    values += [cc.skeleton(f["skiri_form"] or "") for f in e["forms"]]
    values = [v for v in values if v]
    if not values:
        return 0.0
    hay = block.sk_folded or block.sk
    return sum(v in hay for v in values) / float(len(values))


def pair_entries(db, printed, blocks):
    by_key_db, by_key_pr = collections.defaultdict(list), collections.defaultdict(list)
    for e in sorted(db.values(), key=lambda e: seqno(e["entry_id"])):
        by_key_db[db_key(e)].append(e["entry_id"])
    for p in printed:
        by_key_pr[cc.tidy(p["head"])].append(p["seq"])
    pairs, how = {}, {}
    left_db, left_pr = [], []

    def assign(ids, seqs, label):
        scored = sorted(((quick_score(db[i], blocks[s]), i, s) for i in ids for s in seqs), key=lambda t: (-t[0], t[1], t[2]))
        used_i, used_s = set(), set()
        for sc, i, s in scored:
            if i in used_i or s in used_s:
                continue
            pairs[i] = s; how[i] = label
            used_i.add(i); used_s.add(s)
        return [i for i in ids if i not in used_i], [s for s in seqs if s not in used_s]

    for key in sorted(set(by_key_db) | set(by_key_pr)):
        ids, seqs = by_key_db.get(key, []), by_key_pr.get(key, [])
        if ids and seqs:
            ids, seqs = assign(ids, seqs, "headword" if len(by_key_db[key]) == 1 and len(by_key_pr[key]) == 1 else "homograph")
        left_db += ids
        left_pr += seqs
    # same letters, different spacing, order or bracket note
    loose_db, loose_pr = collections.defaultdict(list), collections.defaultdict(list)
    for i in left_db:
        loose_db[loose_key(db_key(db[i]))].append(i)
    for s in left_pr:
        loose_pr[loose_key(printed[s - 1]["head"])].append(s)
    left_db, left_pr = [], []
    for key in sorted(set(loose_db) | set(loose_pr)):
        ids, seqs = loose_db.get(key, []), loose_pr.get(key, [])
        if ids and seqs:
            ids, seqs = assign(ids, seqs, "headword-loose")
        left_db += ids
        left_pr += seqs
    # what is left: pair only if the headwords are close and the content agrees
    cands = []
    for i in left_db:
        for s in left_pr:
            r = difflib.SequenceMatcher(None, cc.skeleton(db_key(db[i])), cc.skeleton(printed[s - 1]["head"]), autojunk=False).ratio()
            sc = quick_score(db[i], blocks[s])
            if r >= 0.8 and sc >= 0.5:
                cands.append((r + sc, i, s))
    used_i, used_s = set(), set()
    for _, i, s in sorted(cands, key=lambda t: (-t[0], t[1], t[2])):
        if i in used_i or s in used_s:
            continue
        pairs[i] = s; how[i] = "headword-near"
        used_i.add(i); used_s.add(s)
    phantom = [i for i in left_db if i not in used_i]
    missing = [s for s in left_pr if s not in used_s]
    return pairs, how, phantom, missing


def is_skiri_field(field):
    f = re.sub(r"\[.*\]", "", field)
    return f in ("headword", "phonetic_form", "additional_form", "form", "example.skiri", "cognate.form", "etymology", "derived.form")


def classify(d):
    """Sets class (noise / convention / difference) and severity (1 Pawnee form, 2 meaning, 3 class or page, 4 formatting)."""
    field = re.sub(r"\[.*\]", "", d["field"])
    kind = d["kind"]
    kinds = set(kind.split("+"))
    if kind in NOISE_RULES:
        d["class"], d["severity"] = "noise", 4
        return d
    # Until 2026-11-13 the database wrote í for Parks's lax ɪ́ everywhere, and that was counted once as a
    # convention. It now stores his symbols, so an í where he prints ɪ́ is a difference like any other.
    d["class"] = "difference"
    if field in ("(entry)",):
        sev = 2
    elif field == "(printed text)":
        sev = 1 if "S" in d.get("fonts", "") or "P" in d.get("fonts", "") else 2
    elif field in ("grammatical_class", "verb_class", "page_number", "additional_form_type"):
        sev = 3
    elif field == "column_position":
        sev = 4
    elif is_skiri_field(field):
        sev = 4 if kinds <= CONTENT_KINDS_LOW or kind == "phonetic-word-space-lost" else 1
    else:
        sev = 4 if kinds <= (CONTENT_KINDS_LOW | {"spacing", "hyphen", "stored-keeps-line-break"}) else 2
    d["severity"] = sev
    return d


class Finder:
    """Compares the fields of one database entry with one printed entry and collects the differences."""

    def __init__(self, e, p, block, neighbours):
        self.e, self.p, self.block, self.neighbours = e, p, block, neighbours
        self.diffs = []
        self.checked = 0
        self.equal = 0
        self.page_convention = None

    def add(self, field, kind, stored, printed="", at=None, **extra):
        d = {"entry_id": self.e["entry_id"], "headword": self.e["headword"], "page_file": self.p["page"],
             "book_page": self.p["page"] + BOOK_PAGE_OFFSET, "seq": self.p["seq"], "field": field, "kind": kind,
             "stored": stored, "printed": printed}
        d.update(extra)
        d["boxes"] = self.block.boxes(*at) if at else self.block.boxes()
        self.diffs.append(d)

    def spacing_kind(self, value, rs, phonetic):
        v = cc.tidy(value)
        if "- " in v and (v.replace("- ", "-") in rs or v.replace("- ", "") in rs):
            return "stored-keeps-line-break"
        if phonetic:
            squeeze = lambda s: re.sub(r" *([,(–]) *", r"\1", s)
            if any(squeeze(r) == squeeze(v) for r in rs):
                return "phonetic-spacing-at-punctuation"
            return "phonetic-word-space-lost"
        if any(r.replace(" ", "") == v.replace(" ", "") for r in rs):
            return "spacing"
        return "hyphen"

    def look(self, field, value, prefer=None, phonetic=False):
        if value is None or cc.skeleton(str(value)) == "":
            return
        self.checked += 1
        value = str(value)
        shown = value
        if phonetic:
            value = cc.stored_phonetic_as_printed(value)
        sk = cc.skeleton(value)
        b = self.block
        pos = b.find(sk, prefer, value)
        if pos is not None:
            b.cover(pos, pos + len(sk))
            if not b.whole_words(pos, pos + len(sk), value):
                # the stored value is there, but as part of a longer printed word: something was cut off
                whole = b.whole_word_text(pos, pos + len(sk))
                self.add(field, "stored-is-part-of-a-printed-word", shown, cc.best_reading(value, whole), at=(pos, pos + len(sk)))
                return
            raw = b.printed(pos, pos + len(sk), value)
            rs = cc.readings(raw)
            if cc.tidy(value) in rs or (not phonetic and cc.nfc(value.strip()) in b.orig):
                self.equal += 1
                return
            extra = {}
            if len(rs) > 1:
                extra["printed_if_line_breaks_are_joined"] = rs[0]
            self.add(field, self.spacing_kind(value, rs, phonetic), shown, cc.best_reading(value, raw), at=(pos, pos + len(sk)), **extra)
            return
        if prefer == "E" and self.in_pieces(sk):
            self.equal += 1
            return
        ratio, a, z = cc.nearest(b, sk)
        if ratio >= 0.55:
            printed_sk = b.sk[a:z]
            ed = cc.edits(sk, printed_sk)
            kinds = sorted({cc.edit_kind(x, y) for x, y, _ in ed}) or ["none"]
            b.cover(a, z)
            raw = b.printed(a, z, value) if z > a else ""
            self.add(field, "+".join(kinds), shown, cc.best_reading(value, raw) if raw else "",
                     at=(a, z), edits=[[x, y] for x, y, _ in ed][:12], ratio=round(ratio, 3))
            return
        # not in its own entry: is it printed in a neighbouring one?
        for label, nb in self.neighbours:
            if nb is not None and sk in nb.sk:
                self.add(field, "printed-in-%s-entry" % label, shown, "")
                return
        self.add(field, "not-printed-in-entry", shown, "", ratio=round(ratio, 3))

    def in_pieces(self, sk, min_piece=4, max_pieces=8):
        """An English value that is printed in order but not in one stretch.

        The parse took the italic qualifiers out of a gloss ("bald eagle (Haliaeetus leucocephalus)." is
        stored as the gloss "bald eagle." and the note "(Haliaeetus leucocephalus)"), so a stored gloss is
        often the printed gloss with pieces missing from its middle. Every character of the stored value
        must be found, in order, in at most a few pieces; the printed text between the pieces is left
        uncovered, so that if no other field accounts for it, it is reported as printed and not stored.
        """
        b = self.block
        budget = [400]                                        # steps; keeps the search small

        def longest(rest, pos):
            lo, hi, best = 1, len(rest), 0
            while lo <= hi:                                   # longest prefix of the rest printed after pos
                mid = (lo + hi) // 2
                if b.sk.find(rest[:mid], pos) >= 0:
                    best, lo = mid, mid + 1
                else:
                    hi = mid - 1
            return best

        def search(rest, pos, used):
            if not rest:
                return []
            budget[0] -= 1
            if used >= max_pieces or budget[0] < 0:
                return None
            best = longest(rest, pos)
            seen = set()
            # the longest piece first; if that leads nowhere, a shorter piece that sits earlier on the page
            for n in range(best, 0, -1):
                if n < min_piece and n != len(rest):
                    break
                at = b.sk.find(rest[:n], pos)
                if at in seen:
                    continue
                seen.add(at)
                tail = search(rest[n:], at + n, used + 1)
                if tail is not None:
                    return [(at, at + n)] + tail
                if len(seen) >= 3:
                    break
            return None

        pieces = search(sk, 0, 0)
        if not pieces or pieces[-1][1] - pieces[0][0] > len(sk) + 400:
            return False
        for a, z in pieces:
            b.cover(a, z)
        return True

    def headword(self):
        e, p, b = self.e, self.p, self.block
        self.checked += 1
        key, head = db_key(e), cc.tidy(p["head"])
        if key == head:
            self.equal += 1
        elif cc.skeleton(key) == cc.skeleton(head):
            self.add("headword", "spacing" if key.replace(" ", "") == head.replace(" ", "") else "hyphen", key, head)
        elif loose_key(key) == loose_key(head):
            note = re.findall(r"\[[^\]]*\]", head)
            if note and not re.findall(r"\[[^\]]*\]", key):
                self.add("headword", "bracket-note-not-stored", key, head)
            elif sorted(key.split()) == sorted(head.split()):
                # a preverb printed between two words of the headword; the database keeps it in its own column
                self.equal += 1
            else:
                self.add("headword", "spacing", key, head)
        else:
            ed = cc.edits(cc.skeleton(key), cc.skeleton(head))
            self.add("headword", "+".join(sorted({cc.edit_kind(x, y) for x, y, _ in ed})) or "differs", key, head,
                     edits=[[x, y] for x, y, _ in ed][:12])
        b.cover(0, min(len(b.sk), len(cc.skeleton(p["head"]))))

    def classes(self):
        """Class and verb class are printed interleaved (VT(1), VR(1)); the database keeps them in two columns."""
        e, b = self.e, self.block
        stored = class_tokens(e["grammatical_class"]) + class_tokens(e["verb_class"])
        printed_text = "".join(ch for ch, k in zip(b.orig, b.kinds) if k == "C")
        printed = class_tokens(printed_text)
        self.checked += 1
        names = lambda toks: sorted(t for t in toks if not t.startswith("("))
        numbers = lambda toks: sorted(set(t for t in toks if t.startswith("(")))
        # print repeats the verb class after each class (VT(1), VR(1)); the database stores it once when both are the same
        if names(stored) == names(printed) and numbers(stored) == numbers(printed):
            self.equal += 1
        else:
            self.add("grammatical_class", "class-differs",
                     "%s %s" % (e["grammatical_class"] or "", e["verb_class"] or ""), cc.tidy(printed_text))
        for i, pos in enumerate(b.idx):
            if b.kinds[pos] == "C":
                b.covered[i] = 1

    def run(self):
        e, p = self.e, self.p
        self.headword()
        self.look("phonetic_form", e["phonetic_form"], prefer="P", phonetic=True)
        self.classes()
        if e["additional_forms"]:
            try:
                forms = json.loads(e["additional_forms"])
            except ValueError:
                forms = []
                self.add("additional_forms", "not-json", e["additional_forms"])
            for n, f in enumerate(forms if isinstance(forms, list) else [], 1):
                if isinstance(f, dict):
                    self.look("additional_form[%d]" % n, f.get("form"), prefer="S")
                    self.look("additional_form_type[%d]" % n, f.get("form_type"), prefer="E")
                else:
                    self.look("additional_form[%d]" % n, f, prefer="S")
        for g in e["glosses"]:
            self.look("gloss[%s]" % g["sense_number"], g["definition"], prefer="E")
            self.look("gloss_usage[%s]" % g["sense_number"], g["usage_notes"], prefer="E")
        for n, et in enumerate(e["etymology"], 1):
            self.look("etymology[%d]" % n, et["raw_etymology"])
            self.look("etymology_literal[%d]" % n, et["literal_translation"], prefer="E")
        for n, c in enumerate(e["cognates"], 1):
            self.look("cognate.form[%d]" % n, c["form"], prefer="S")
        for f in e["forms"]:
            self.look("form[%s]" % f["form_number"], "%s. %s" % (f["form_number"], f["skiri_form"]), prefer="S")
        for n, x in enumerate(e["examples"], 1):
            self.look("example.skiri[%d]" % n, x["skiri_text"], prefer="S")
            self.look("example.english[%d]" % n, x["english_translation"], prefer="E")
            self.look("example.context[%d]" % n, x["usage_context"], prefer="E")
        for n, x in enumerate(e["derived"], 1):
            self.look("derived.form[%d]" % n, x["stem_form"], prefer="S")
            self.look("derived.definition[%d]" % n, x["definition"], prefer="E")
        # page and column
        self.checked += 1
        if e["page_number"] == p["page"] + BOOK_PAGE_OFFSET:
            self.equal += 1
            self.page_convention = "book-page"
        elif e["page_number"] == p["page"]:
            # until 2026-11-14 most entries held the number of the PDF file; scripts/fix_page_citations.py set the book page
            self.page_convention = "file-number"
            self.add("page_number", "file-number-not-book-page", e["page_number"], "book page %d" % (p["page"] + BOOK_PAGE_OFFSET))
        else:
            self.page_convention = "wrong"
            self.add("page_number", "wrong-page", e["page_number"], "file %d = book page %d" % (p["page"], p["page"] + BOOK_PAGE_OFFSET))
        col = {"left": 0, "right": 1}.get((e.get("column_position") or "").lower())
        if col is not None:
            self.checked += 1
            if col == p["col"]:
                self.equal += 1
            else:
                self.add("column_position", "wrong-column", e["column_position"], "left" if p["col"] == 0 else "right")
        return self


def compare(db_path):
    printed = [json.loads(line) for line in PRINTED.open(encoding="utf-8")]
    blocks = {p["seq"]: cc.Block(p["spans"]) for p in printed}
    db = load_db(db_path)
    pairs, how, phantom, missing = pair_entries(db, printed, blocks)
    diffs, pair_rows = [], []
    totals = collections.Counter()
    page_conv = collections.Counter()
    for entry_id, seq in sorted(pairs.items(), key=lambda kv: kv[1]):
        e, p = db[entry_id], printed[seq - 1]
        nbs = [("previous", blocks.get(seq - 1)), ("next", blocks.get(seq + 1))]
        f = Finder(e, p, blocks[seq], nbs).run()
        diffs += f.diffs
        totals["fields_checked"] += f.checked
        totals["fields_equal"] += f.equal
        page_conv[f.page_convention] += 1
        for start, text, kinds, boxes in blocks[seq].residue():
            shown = cc.tidy(text.replace("\n", " "))
            structural = set(shown) <= STRUCTURAL or set(LABELS.sub("", shown)) <= STRUCTURAL
            diffs.append({"entry_id": entry_id, "headword": e["headword"], "page_file": p["page"],
                          "book_page": p["page"] + BOOK_PAGE_OFFSET, "seq": seq, "field": "(printed text)",
                          "kind": "structural-marks" if structural else "printed-not-stored", "stored": "", "printed": shown, "fonts": kinds, "boxes": boxes})
        pair_rows.append({"entry_id": entry_id, "seq": seq, "page_file": p["page"], "paired_by": how[entry_id],
                          "checked": f.checked, "equal": f.equal})
    for entry_id in phantom:
        e = db[entry_id]
        diffs.append({"entry_id": entry_id, "headword": e["headword"], "page_file": None, "book_page": None, "seq": None,
                      "field": "(entry)", "kind": "stored-entry-not-printed", "stored": db_key(e), "printed": ""})
    for seq in missing:
        p = printed[seq - 1]
        diffs.append({"entry_id": None, "headword": p["head"], "page_file": p["page"], "book_page": p["page"] + BOOK_PAGE_OFFSET,
                      "seq": seq, "field": "(entry)", "kind": "printed-entry-not-stored", "stored": "",
                      "printed": cc.tidy("".join(s["t"] for s in p["spans"]))[:600],
                      "boxes": blocks[seq].boxes(0, len(blocks[seq].sk))})
    diffs = [classify(d) for d in diffs]
    by_kind = collections.Counter((d["class"], re.sub(r"\[.*\]", "", d["field"]), d["kind"]) for d in diffs)
    summary = {"printed_entries": len(printed), "stored_entries": len(db), "paired": len(pairs),
               "paired_by": dict(collections.Counter(how.values())),
               "stored_entry_not_printed": len(phantom), "printed_entry_not_stored": len(missing),
               "fields_checked": totals["fields_checked"], "fields_equal": totals["fields_equal"],
               "page_number_convention": dict(page_conv),
               "by_class": dict(collections.Counter(d["class"] for d in diffs)),
               "differences_by_severity": dict(collections.Counter(str(d["severity"]) for d in diffs if d["class"] == "difference")),
               "noise_rules": {k: {"rule": v, "count": sum(1 for d in diffs if d["kind"] == k)} for k, v in NOISE_RULES.items()},
               "conventions": {k: {"what": v, "count": sum(1 for d in diffs if d["class"] == "convention" and k in d["kind"])}
                               for k, v in CONVENTIONS.items()},
               "by_class_field_kind": {"%s | %s | %s" % k: n for k, n in by_kind.most_common()}}
    return diffs, pair_rows, summary, by_kind


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(state.ROOT / "skiri_pawnee.db"))
    ap.add_argument("--out", default=str(state.OUT))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    diffs, pair_rows, summary, by_kind = compare(args.db)
    with (out_dir / "s2e_differences.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for d in diffs:
            if d["class"] == "noise":       # 9,700 rows of marks: keep the row, not its position
                d = {k: v for k, v in d.items() if k != "boxes"}
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    if out_dir.resolve() == state.OUT.resolve():
        with (state.WORK / "s2e_pairs.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
            for r in pair_rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out_dir / "s2e_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    if not args.quiet:
        state.out("printed entries %d, stored %d, paired %d %s" % (
            summary["printed_entries"], summary["stored_entries"], summary["paired"], summary["paired_by"]))
        state.out("stored entry not printed: %d; printed entry not stored: %d" % (
            summary["stored_entry_not_printed"], summary["printed_entry_not_stored"]))
        state.out("fields checked %d, equal %d (%.2f%%)" % (summary["fields_checked"], summary["fields_equal"],
                                                           100.0 * summary["fields_equal"] / max(1, summary["fields_checked"])))
        state.out("page number convention: %s" % summary["page_number_convention"])
        state.out("by class: %s   differences by severity: %s" % (summary["by_class"], summary["differences_by_severity"]))
        for (cls, field, kind), n in by_kind.most_common(90):
            if cls == "difference":
                state.out("  %-26s %-44s %d" % (field, kind, n))


if __name__ == "__main__":
    main()
