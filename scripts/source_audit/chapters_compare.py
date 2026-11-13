#!/usr/bin/env python3
"""
Stage 4d: the grammar chapter and the sound-change rules against the blind readings
===================================================================================

Chapter 4 (Grammatical Overview) is stored as extracted_data/grammatical_overview.json,
an AI model's reading of the page images from March 2026 with the prose
paraphrased. Chapter 3 (Major Sound Changes) is stored as the 24 rows of the
sound_change_rules table, each with its examples.

A second reader transcribed every Skiri form on those pages from tiles without
seeing the stored copy (work/appendix/chapter4/blind_part*.json,
work/appendix/chapter3/blind.json). Because the stored text is a paraphrase,
the two cannot be lined up sentence by sentence. Instead every Skiri-looking
word in the stored copy of a page is looked for among the words the blind
reader found on that page (or the page before or after):

    same          the word is there, letter for letter (hyphens aside)
    b-for-h       the stored word has a b where the blind reading has an h. Skiri has no b; in
                  the book's italic type the h has a curled foot and looks like one
    differs       a blind word is close to it but not the same
    not-found     nothing close on the page: a paraphrase, an English word that looks Skiri, or a
                  form the blind reader did not list

    python scripts/source_audit/chapters_compare.py     # writes chapter4_differences.json and chapter3_differences.json
"""
import collections
import difflib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

APP = state.WORK / "appendix"
TOKEN = re.compile(r"[A-Za-zʔíáúÍÁÚ́'’\-]+")
SKIRI_ONLY = re.compile(r"^[aiuptkcswrhʔbníáú́\-]+$", re.I)
ENGLISH_LOOKALIKES = set("""a i it is its this that what which who us as at up in but put sit sat hit bit tub rub cub habit rabbit
 start stick trick thick thin think ship ships trip trips tip tips strip skip pick picks kick wish with wit cut cuts shut hut
 burst bust bus rib ribs pair par part parts bar bars barn burn turn turns urn sun sub run runs trust rust crust thrust
 irish artist tiptip brain bran train rain air hair chair chairs stair stairs chain war wars saw paws straw raw rat rats cat cats
 hat hats bat bats path paths bath baths arch art arts arc tax taxi ask asks task tasks bask can cans tan pan pins pin spin tin win
 wins twin twins skin skins kin nut nuts bun nun inn sin sink pink ink tank bank stab cab scab tab crab pub subs bib crib bid nib
 than thank thanks banks print prints paint paints saint saints paris burnt hurt hurts shirt shirts skirt skirts birth tribute
 nabisco a's i's cis sic etc""".split())


def key(tok):
    t = unicodedata.normalize("NFC", tok).replace("’", "ʔ").replace("'", "ʔ")
    return t.replace("-", "").strip()


def looks_skiri(tok):
    return "ʔ" in tok or re.search(r"aa|ii|uu", tok) is not None


def tokens(text, strict):
    """Skiri-looking words in a string. strict: the string is a form field, so every word of Skiri letters counts."""
    out = []
    for m in TOKEN.finditer(unicodedata.normalize("NFC", text or "")):
        tok = m.group(0).strip("'’")
        k = key(tok)
        if len(k) < 2 or not SKIRI_ONLY.match(tok.replace("’", "ʔ").replace("'", "ʔ")):
            continue
        if looks_skiri(tok) or (strict and k.lower() not in ENGLISH_LOOKALIKES) or ("b" in k.lower() and looks_skiri(tok)):
            out.append(tok)
    return out


def walk(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], out)
    elif isinstance(node, list):
        for v in node:
            walk(v, path, out)
    elif isinstance(node, str):
        strict = any(p in ("morphemes_mentioned", "tables") or "form" in p or "skiri" in p or "morpheme" in p or "example" in p
                     for p in path) and not any(p in ("content", "heading", "description", "gloss", "english", "meaning", "label") for p in path[-1:])
        for tok in tokens(node, strict):
            out.append((tok, "/".join(path[-3:])))


def nearest(k, pool):
    best, best_r = None, 0.0
    for cand in pool:
        if abs(len(cand) - len(k)) > 3:
            continue
        r = difflib.SequenceMatcher(None, k, cand, autojunk=False).ratio()
        if r > best_r:
            best, best_r = cand, r
    return best, best_r


def compare_pages(stored_pages, blind_pages, label):
    """stored_pages / blind_pages: {page number: [(token, where)]} / {page number: set of keys}."""
    rows, tally = [], collections.Counter()
    for page in sorted(stored_pages):
        pool = set()
        for p in (page - 1, page, page + 1):
            pool |= blind_pages.get(p, set())
        seen = set()
        for tok, where in stored_pages[page]:
            k = key(tok)
            if (k, where) in seen:
                continue
            seen.add((k, where))
            tally["words"] += 1
            if k in pool:
                tally["same"] += 1
                continue
            if "b" in k.lower() and (k.replace("b", "h").replace("B", "H") in pool):
                tally["b-for-h"] += 1
                rows.append({"page": page, "stored": tok, "blind_reading": k.replace("b", "h").replace("B", "H"), "kind": "b-for-h",
                             "where": where, "grade": "blind-reading", "severity": 1})
                continue
            cand, r = nearest(k, pool)
            if cand is not None and r >= 0.74:
                kind = "b-for-h and more" if "b" in k.lower() and "b" not in cand.lower() else "differs"
                tally[kind] += 1
                rows.append({"page": page, "stored": tok, "blind_reading": cand, "kind": kind, "ratio": round(r, 3), "where": where,
                             "grade": "blind-reading", "severity": 1})
            else:
                kind = "not-found (has a b)" if "b" in k.lower() and looks_skiri(k) else "not-found"
                tally[kind] += 1
                rows.append({"page": page, "stored": tok, "blind_reading": cand or "", "kind": kind, "ratio": round(r, 3), "where": where,
                             "grade": "unresolved", "severity": 1 if "b" in kind else 3})
    return rows, tally


def chapter4():
    stored = json.loads((state.ROOT / "extracted_data" / "grammatical_overview.json").read_text(encoding="utf-8"))
    stored_pages = {}
    for name, page in stored.items():
        out = []
        walk(page, [], out)
        stored_pages[int(name.split("_")[1])] = out
    blind_pages = collections.defaultdict(set)
    n_tiles = 0
    for f in sorted((APP / "chapter4").glob("blind_part*.json")):
        for label, tile in json.loads(f.read_text(encoding="utf-8")).items():
            n_tiles += 1
            page = int(re.match(r"p(\d+)", label).group(1))
            texts = [x[0] for x in tile.get("forms", []) if x] + [x[1] for x in tile.get("forms", []) if len(x) > 1]
            for t in tile.get("tables", []):
                texts.append(t.get("title") or "")
                for row in t.get("rows", []):
                    texts += [str(c) for c in (row if isinstance(row, list) else [row])]
            for text in texts:
                for m in TOKEN.finditer(unicodedata.normalize("NFC", text or "")):
                    blind_pages[page].add(key(m.group(0).strip("'’")))
    rows, tally = compare_pages(stored_pages, blind_pages, "chapter4")
    return n_tiles, rows, tally


def chapter3():
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    path = APP / "chapter3" / "blind.json"
    if not path.exists():
        return None
    blind = json.loads(path.read_text(encoding="utf-8"))
    pool = set()
    for tile in blind.values():
        texts = []
        for ex in tile.get("examples", []):
            texts += [ex.get("underlying") or "", ex.get("surface") or ""]
        for r in tile.get("rules", []):
            texts += [r.get("formal") or "", r.get("name") or ""]
        texts += [x[0] for x in tile.get("other_forms", []) if x]
        for text in texts:
            for m in TOKEN.finditer(unicodedata.normalize("NFC", text)):
                pool.add(key(m.group(0).strip("'’")))
    stored_pages = {1: []}
    for rule_id, name, formal, examples in conn.execute("select rule_id, name, formal, examples from sound_change_rules order by ordering, rule_id"):
        try:
            exs = json.loads(examples or "[]")
        except ValueError:
            exs = []
        for ex in exs if isinstance(exs, list) else []:
            if isinstance(ex, dict):
                for field in ("underlying", "surface"):
                    for tok in tokens(ex.get(field) or "", True):
                        stored_pages[1].append((tok, "rule %s %s" % (rule_id, field)))
    rows, tally = compare_pages(stored_pages, {1: pool}, "chapter3")
    for r in rows:
        r.pop("page", None)
    return len(blind), rows, tally


def report(name, result):
    if result is None:
        state.out("%s: no blind reading yet" % name)
        return
    tiles, rows, tally = result
    (state.OUT / ("%s_differences.json" % name)).write_text(json.dumps(
        {"tiles_read": tiles, "tally": dict(tally), "differences": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("%s: %d tiles; %s" % (name, tiles, dict(tally)))
    for kind in ("b-for-h", "b-for-h and more", "not-found (has a b)", "differs"):
        sel = [r for r in rows if r["kind"] == kind]
        if sel:
            state.out("  %s (%d): %s" % (kind, len(sel), "; ".join("%s -> %s" % (r["stored"], r["blind_reading"]) for r in sel[:60])))


def main():
    report("chapter4", chapter4())
    report("chapter3", chapter3())


if __name__ == "__main__":
    main()
