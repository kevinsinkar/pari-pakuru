#!/usr/bin/env python3
"""Build gold sets G1 (Parks's own analyses) and G3 (Blue Book seams), and hash all gold files.

    python scripts/morphology_v2/gold_build.py          # build G1 + G3
    python scripts/morphology_v2/gold_build.py --hash   # (re)write gold/HASHES.json
    python scripts/morphology_v2/gold_build.py --verify # check files against HASHES.json

G2 (the hand-checked sample) is drawn by gold_sample.py and annotated from the
page images; this script only merges and hashes it.
"""
import argparse
import re

from bluebook import match_seams
from common import (EXTRACTED, GOLD, connect, dump_json, load_json, norm, out, sha256)

EXAMPLE_RE = re.compile(
    r"(?P<surface>[^\s'‘’<>()]+)\s+['‘’](?P<trans>[^<\n]*?)['’]\s*<\s*(?P<analysis>[^\n]+)")
LABEL_RE = re.compile(r"^[A-Z0-9][A-Za-z0-9./ ]*$")


def _strings(o):
    if isinstance(o, dict):
        for k in sorted(o):
            yield from _strings(o[k])
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)
    elif isinstance(o, str):
        yield o


def parse_analysis(text):
    """'ti- IND + Ø- 3.A + kikak 'cry' + -Ø PERF' -> list of pieces."""
    text = re.split(r";\s*(?:cp\.|cf\.)|\bcp\.", text)[0]
    pieces = []
    for chunk in re.split(r"\s\+\s", text):
        chunk = chunk.strip().strip(";").strip()
        if not chunk:
            continue
        m = re.match(r"^(?P<form>\S+)\s*(?P<rest>.*)$", chunk)
        form, rest = m.group("form"), m.group("rest").strip()
        gloss, label = None, None
        g = re.search(r"['‘’](.*?)['’]?$", rest)
        if rest and rest[0] in "'‘’" and g:
            gloss = g.group(1).strip("'‘’ ")
        elif rest and LABEL_RE.match(rest):
            label = rest
        elif rest:
            gloss = rest
        pieces.append({"form": norm(form), "label": label, "gloss": gloss})
    return pieces


def build_g1():
    go = load_json(EXTRACTED / "grammatical_overview.json")
    examples, seen = [], set()
    pages = sorted((k for k in go if k.startswith("page_")), key=lambda k: int(k.split("_")[1]))
    for k in pages:
        book_page = go[k].get("page_number")
        for s in _strings(go[k]):
            for m in EXAMPLE_RE.finditer(s):
                key = (m["surface"], m["analysis"][:60])
                if key in seen:
                    continue
                seen.add(key)
                pieces = parse_analysis(m["analysis"])
                flags = []
                if "b" in m["surface"] or any("b" in p["form"] for p in pieces):
                    flags.append("ocr_b")          # b is not a Skiri letter: OCR for h/p
                if not re.match(r"^[a-zʔáíúàìù]+$", norm(m["surface"])):
                    flags.append("surface_suspect")
                examples.append({"go_page": book_page, "surface": norm(m["surface"]),
                                 "translation": m["trans"].strip(), "analysis_text": m["analysis"].strip(),
                                 "pieces": pieces, "flags": flags})
        for sec in go[k].get("sections", []):
            for e in sec.get("examples", []) or []:
                key = (e.get("pawnee_form"), "structured")
                if key in seen or not e.get("pawnee_form"):
                    continue
                seen.add(key)
                pieces = []
                for b in e.get("breakdown", []) or []:
                    lab = (b.get("label") or "").strip()
                    is_gloss = lab[:1] in "'‘’"
                    pieces.append({"form": norm(b.get("morpheme") or ""),
                                   "label": None if is_gloss else lab or None,
                                   "gloss": lab.strip("'‘’ ") if is_gloss else None})
                examples.append({"go_page": book_page, "surface": norm(e["pawnee_form"]),
                                 "translation": e.get("translation"), "analysis_text": None,
                                 "pieces": pieces, "flags": ["structured"]})
    dump_json(GOLD / "g1_go_examples.json", {"source": "extracted_data/grammatical_overview.json",
                                              "n": len(examples), "examples": examples})
    conn = connect()
    cells = [dict(r) for r in conn.execute(
        """select id, verb_heading, verb_class, dictionary_form, english_gloss, mode, person_number,
                  skiri_form, english_form, source_page from verb_paradigms order by id""")]
    dump_json(GOLD / "g1_appendix1.json", {"source": "verb_paradigms table (Parks Appendix 1)",
                                            "n": len(cells), "cells": cells})
    return len(examples), len(cells)


def build_g3():
    conn = connect()
    certain, counts = match_seams(conn)
    dump_json(GOLD / "g3_bb_seams.json", {"source": "blue_book_attestations seamed tokens",
                                           "counts": counts, "n": len(certain), "matches": certain})
    return counts


def merge_g2():
    """Merge annotator batches into one file (only when all batches are present)."""
    sample = load_json(GOLD / "g2_sample.json")
    n_batches = sample["entries"][-1]["batch"]
    merged, missing = [], []
    for b in range(1, n_batches + 1):
        p = GOLD / "g2_raw" / ("batch_%d.json" % b)
        if not p.exists():
            missing.append(b)
            continue
        merged.extend(load_json(p))
    if missing:
        return None, missing
    split = {e["entry_id"]: e["split"] for e in sample["entries"]}
    by_id = {a["entry_id"]: a for a in merged}
    ordered = [dict(by_id[e["entry_id"]], split=split[e["entry_id"]])
               for e in sample["entries"] if e["entry_id"] in by_id]
    dump_json(GOLD / "g2_annotations.json", {"n": len(ordered), "annotations": ordered})
    return len(ordered), []


def gold_files():
    files = sorted(p for p in GOLD.rglob("*.json") if p.name != "HASHES.json")
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--merge-g2", action="store_true")
    args = ap.parse_args()
    if args.verify:
        saved = load_json(GOLD / "HASHES.json")
        bad = [f for f, h in saved.items() if sha256(GOLD / f) != h]
        out("gold files verified: %d ok, %d changed %s" % (len(saved) - len(bad), len(bad), bad))
        raise SystemExit(1 if bad else 0)
    if args.merge_g2:
        n, missing = merge_g2()
        out("g2 merged: %s; missing batches: %s" % (n, missing))
    if args.hash:
        hashes = {str(p.relative_to(GOLD)).replace("\\", "/"): sha256(p) for p in gold_files()}
        dump_json(GOLD / "HASHES.json", hashes)
        for f, h in sorted(hashes.items()):
            out("%s  %s" % (h[:16], f))
        return
    if not args.merge_g2:
        n_ex, n_cells = build_g1()
        out("G1: %d Grammatical Overview worked examples, %d Appendix 1 cells" % (n_ex, n_cells))
        counts = build_g3()
        out("G3: " + ", ".join("%s=%d" % kv for kv in sorted(counts.items())))


if __name__ == "__main__":
    main()
