#!/usr/bin/env python3
"""
Stage 6: the English-to-Skiri section, database against text layer
==================================================================

The English-to-Skiri section repeats the Skiri entries under English
headwords, and adds cross-references ("comfort  see hug {rikatiri}"). The
database keeps it in two tables: english_index (one row per subentry) and
cross_references.

Every row is paired with its printed English entry by headword, and its Skiri
term, phonetic form and class are looked for in that entry; every
cross-reference likewise. Printed English headwords and printed Skiri terms
that no row accounts for are listed too.

    python scripts/source_audit/e2s_compare.py     # writes e2s_differences.jsonl and e2s_summary.json

Reads the database read-only. Changes nothing.
"""
import argparse
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_core as cc  # noqa: E402
import s2e_compare  # noqa: E402
import s2e_segment  # noqa: E402
import state  # noqa: E402

TEXT = state.WORK / "textlayer"
HEAD_SIZE = 10.1
RAW_STANDINS = set("ß†‰™ÙÑæ‡Š÷")
AI_STYLE = re.compile(r"[éèëêɛ²³ıˈˌ]|\.[a-zəɪʊ]")


def is_head_span(s):
    return s["f"] == "TruteauGaramond" and s["st"] == "Bold" and abs(s["sz"] - HEAD_SIZE) < 0.3


def segment():
    entries, current = [], None
    for f in sorted(TEXT.glob("e2s_*.json")):
        page = json.loads(f.read_text(encoding="utf-8"))
        ordered, left = s2e_segment.page_lines(page)
        for col, bottom, x0, line in ordered:
            first = next((s for s in line if s["t"].strip()), None)
            margin = left if col == 0 else left + 207.0
            if first is not None and is_head_span(first) and abs(first["b"][0] - margin) < 3.0:
                current = {"seq": len(entries) + 1, "page": page["unit"], "col": col, "spans": []}
                entries.append(current)
            if current is None:
                continue
            for i, s in enumerate(line):
                current["spans"].append({"f": s["f"], "st": s["st"], "sz": s["sz"], "t": s["t"], "p": page["unit"], "b": s["b"],
                                         "nl": 1 if i == 0 else 0})
    for e in entries:
        head = []
        for s in e["spans"]:
            if is_head_span(s):
                head.append(("\n" if s["nl"] and head else "") + s["t"])
            elif s["t"].strip() == "":
                continue
            else:
                break
        e["head"] = cc.readings("".join(head))[0]
    return entries


def phonetic_state(value):
    v = value or ""
    if any(ch in RAW_STANDINS for ch in v):
        return "raw-stand-in-characters"
    if re.search(r"\[( \S){4,}", v):
        return "letter-spaced"
    if AI_STYLE.search(v):
        return "not-parks-notation"
    return None


def rows_from_json():
    """The current English-to-Skiri JSON as index rows and cross-references (same shape as the database tables)."""
    data = json.loads((state.ROOT / "Dictionary Data" / "english_to_skiri_linked.json").read_text(encoding="utf-8"))
    rows, xrefs = [], []
    for n, e in enumerate(data, 1):
        word = e.get("english_entry_word")
        page = (e.get("entry_metadata") or {}).get("page_number")
        for s in e.get("subentries") or []:
            p1 = s.get("part_I") or {}
            gc = p1.get("grammatical_classification") or {}
            term = p1.get("skiri_term")
            if term and p1.get("stem_preverb") and p1["stem_preverb"] not in term:
                term = "%s %s" % (term, p1["stem_preverb"])
            rows.append({"id": "%d.%s" % (n, s.get("subentry_number")), "english_word": word, "subentry_number": s.get("subentry_number"),
                         "entry_id": s.get("s2e_entry_id"), "skiri_term": term, "phonetic_form": p1.get("phonetic_form"),
                         "grammatical_class": gc.get("class_abbr"), "verb_class": gc.get("verb_class"), "page_number": page})
            for x in (s.get("part_III") or {}).get("cross_references") or []:
                xrefs.append({"id": "%d.%s.%d" % (n, s.get("subentry_number"), len(xrefs)), "from_english_word": word,
                              "to_english_term": x.get("english_term"),
                              "skiri_equivalents": json.dumps(x.get("skiri_equivalents") or [], ensure_ascii=False), "source_page": page})
    return rows, xrefs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["json", "db"], default="json",
                    help="json: Dictionary Data/english_to_skiri_linked.json (the current copy). db: the english_index and "
                         "cross_references tables, which were loaded from an earlier file")
    args = ap.parse_args()
    source = args.source
    tag = "e2s" if source == "json" else "e2s_db_tables"
    printed = segment()
    blocks = {p["seq"]: cc.Block(p["spans"]) for p in printed}
    by_head = collections.defaultdict(list)
    for p in printed:
        by_head[cc.tidy(p["head"]).lower()].append(p["seq"])
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    if source == "db":
        rows = [dict(r) for r in conn.execute("select id, english_word, subentry_number, entry_id, skiri_term, phonetic_form, "
                                              "grammatical_class, verb_class, page_number from english_index order by id")]
        xrefs = [dict(r) for r in conn.execute("select id, from_english_word, to_english_term, skiri_equivalents, source_page from cross_references order by id")]
    else:
        rows, xrefs = rows_from_json()
    keys = {r["entry_id"]: s2e_compare.db_key(dict(r)) for r in conn.execute("select entry_id, headword, stem_preverb from lexical_entries")}
    diffs = []
    totals = collections.Counter()
    used_heads = set()
    phon_states = collections.Counter()

    def find_block(word, prefer_page=None):
        seqs = by_head.get(cc.tidy(word or "").lower(), [])
        if not seqs:
            return None
        used_heads.update(seqs)
        return seqs

    def finder(row_id, word, seq):
        p = printed[seq - 1]
        return s2e_compare.Finder({"entry_id": row_id, "headword": word}, p, blocks[seq], [])

    for r in rows:
        totals["index_rows"] += 1
        seqs = find_block(r["english_word"])
        if not seqs:
            diffs.append({"entry_id": "%s:%s" % ("english_index" if source == "db" else "e2s_json", r["id"]), "headword": r["english_word"], "page_file": r["page_number"],
                          "seq": None, "field": "(english headword)", "kind": "stored-headword-not-printed", "stored": r["english_word"], "printed": ""})
            continue
        if not r["skiri_term"]:
            totals["rows_without_term"] += 1
            continue
        # a headword can be printed more than once; take the printed entry that holds this row's term
        sk = cc.skeleton(r["skiri_term"])
        seq = next((s for s in seqs if sk in blocks[s].sk), seqs[0])
        f = finder("%s:%s" % ("english_index" if source == "db" else "e2s_json", r["id"]), r["english_word"], seq)
        f.look("skiri_term", r["skiri_term"], prefer="S")
        state_ = phonetic_state(r["phonetic_form"])
        if r["phonetic_form"]:
            if state_:
                phon_states[state_] += 1
                f.checked += 1
                f.add("phonetic_form", state_, r["phonetic_form"], "")
            else:
                f.look("phonetic_form", r["phonetic_form"], prefer="P", phonetic=True)
        for col in ("grammatical_class", "verb_class"):
            if r[col]:
                f.checked += 1
                toks = s2e_compare.class_tokens(r[col])
                block_text = blocks[seq].sk
                if all(cc.skeleton(t) in block_text for t in toks):
                    f.equal += 1
                else:
                    f.add(col, "class-differs", r[col], "")
        if r["entry_id"] and r["entry_id"] in keys:
            f.checked += 1
            if cc.skeleton(keys[r["entry_id"]]) == cc.skeleton(r["skiri_term"]) or s2e_compare.loose_key(keys[r["entry_id"]]) == s2e_compare.loose_key(r["skiri_term"]):
                f.equal += 1
            else:
                f.add("entry_link", "linked-entry-has-another-headword", r["skiri_term"], keys[r["entry_id"]])
        totals["fields_checked"] += f.checked
        totals["fields_equal"] += f.equal
        diffs += f.diffs
    for x in xrefs:
        totals["cross_references"] += 1
        seqs = find_block(x["from_english_word"])
        if not seqs:
            diffs.append({"entry_id": "%s:%s" % ("cross_references" if source == "db" else "e2s_json_xref", x["id"]), "headword": x["from_english_word"], "page_file": x["source_page"],
                          "seq": None, "field": "(english headword)", "kind": "stored-headword-not-printed",
                          "stored": x["from_english_word"], "printed": ""})
            continue
        target = cc.skeleton(x["to_english_term"] or "")
        seq = next((s for s in seqs if target and target in blocks[s].sk), seqs[0])
        f = finder("%s:%s" % ("cross_references" if source == "db" else "e2s_json_xref", x["id"]), x["from_english_word"], seq)
        f.look("xref.target", x["to_english_term"], prefer="E")
        try:
            terms = json.loads(x["skiri_equivalents"] or "[]")
        except ValueError:
            terms = [x["skiri_equivalents"]]
        for n, t in enumerate(terms, 1):
            f.look("xref.skiri[%d]" % n, t, prefer="S")
        totals["fields_checked"] += f.checked
        totals["fields_equal"] += f.equal
        diffs += f.diffs
    # page -> stored: English headwords and bold Skiri terms that nothing accounts for
    for p in printed:
        if p["seq"] not in used_heads:
            diffs.append({"entry_id": None, "headword": p["head"], "page_file": p["page"], "seq": p["seq"], "field": "(english headword)",
                          "kind": "printed-headword-not-stored", "stored": "", "printed": cc.tidy("".join(s["t"] for s in p["spans"]))[:300],
                          "boxes": blocks[p["seq"]].boxes()})
            continue
        b = blocks[p["seq"]]
        pos = 0
        for i, s in enumerate(p["spans"]):
            n = len(cc.skeleton(s["t"]))
            if s["f"] == "PlainsArial" and s["st"] == "Bold" and s["sz"] > 8.5 and n >= 2 and not any(b.covered[pos:pos + n]):
                diffs.append({"entry_id": None, "headword": p["head"], "page_file": p["page"], "seq": p["seq"], "field": "(printed skiri term)",
                              "kind": "printed-term-not-stored", "stored": "", "printed": cc.tidy(s["t"]), "boxes": b.boxes(pos, pos + n)})
            pos += n
    for d in diffs:
        d.setdefault("book_page", None)
        kind = d["kind"]
        field = re.sub(r"\[.*\]", "", d["field"])
        if kind in s2e_compare.NOISE_RULES:
            d["class"], d["severity"] = "noise", 4
        elif set(kind.split("+")) == {"lax-i-symbol"}:
            d["class"], d["severity"] = "convention", 4
        else:
            d["class"] = "difference"
            if field in ("skiri_term", "phonetic_form", "xref.skiri", "(printed skiri term)"):
                d["severity"] = 4 if kind in ("phonetic-word-space-lost",) else 1
            elif field in ("grammatical_class", "verb_class", "entry_link"):
                d["severity"] = 3
            else:
                d["severity"] = 4 if kind in ("spacing", "hyphen", "stored-keeps-line-break", "punctuation", "capital") else 2
    if source == "json":       # for the database tables the counts are enough: the remedy is to re-import them
        with (state.OUT / ("%s_differences.jsonl" % tag)).open("w", encoding="utf-8", newline="\n") as fh:
            for d in diffs:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    by_kind = collections.Counter((d["class"], re.sub(r"\[.*\]", "", d["field"]), d["kind"]) for d in diffs)
    summary = {"printed_english_entries": len(printed), "index_rows": totals["index_rows"], "rows_without_a_skiri_term": totals["rows_without_term"],
               "cross_references": totals["cross_references"], "fields_checked": totals["fields_checked"], "fields_equal": totals["fields_equal"],
               "phonetic_forms_not_in_parks_notation": dict(phon_states),
               "by_class": dict(collections.Counter(d["class"] for d in diffs)),
               "differences_by_severity": dict(collections.Counter(str(d["severity"]) for d in diffs if d["class"] == "difference")),
               "by_class_field_kind": {"%s | %s | %s" % k: n for k, n in by_kind.most_common()}}
    (state.OUT / ("%s_summary.json" % tag)).write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("printed English entries %d; index rows %d (%d without a Skiri term); cross-references %d" % (
        len(printed), totals["index_rows"], totals["rows_without_term"], totals["cross_references"]))
    state.out("fields checked %d, equal %d (%.2f%%)" % (totals["fields_checked"], totals["fields_equal"],
                                                       100.0 * totals["fields_equal"] / max(1, totals["fields_checked"])))
    state.out("by class: %s; differences by severity: %s" % (summary["by_class"], summary["differences_by_severity"]))
    for (cls, field, kind), n in by_kind.most_common(45):
        if cls == "difference":
            state.out("  %-24s %-44s %d" % (field, kind, n))


if __name__ == "__main__":
    main()
