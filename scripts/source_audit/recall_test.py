#!/usr/bin/env python3
"""
Stage 2c: does the comparison catch errors? A test with planted ones
====================================================================

Copies the database, plants known errors of many kinds in the copy, runs the
Skiri-to-English comparison on the copy, and counts how many of the planted
errors it reports. The live database is opened read-only and is not touched;
the copy lives in work/recall/.

    python scripts/source_audit/recall_test.py           # plant, compare, report
    python scripts/source_audit/recall_test.py --per-kind 40

Errors are planted only in fields that the comparison finds clean in the live
database, so that a hit can only come from the plant. An error counts as
caught when the comparison of the copy reports a difference (not noise, not a
convention) in that entry and field that the live comparison does not report;
for a deleted sense or example, when the entry gains a "printed, not stored"
stretch; for a deleted entry, when its headword is reported as printed and not
stored.

Writes reports/source_audit_2026-11/recall_test.json.
"""
import argparse
import collections
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2e_compare  # noqa: E402
import state  # noqa: E402

CONS = "ptkcswrh"


def base_field(field):
    return re.sub(r"\[.*\]", "", field)


def swap_consonant(s, rng):
    idx = [i for i, ch in enumerate(s) if ch in CONS and 0 < i < len(s) - 1]
    if not idx:
        return None
    i = rng.choice(idx)
    new = rng.choice([c for c in CONS if c != s[i]])
    return s[:i] + new + s[i + 1:]


def h_to_b(s, rng):
    idx = [i for i, ch in enumerate(s) if ch == "h"]
    if not idx:
        return None
    i = rng.choice(idx)
    return s[:i] + "b" + s[i + 1:]


def drop_accent(s, rng):
    for a, b in (("á", "a"), ("í", "i"), ("ú", "u"), ("à", "ə"), ("ʊ́", "ʊ")):
        if a in s:
            return s.replace(a, b, 1)
    return None


def drop_glottal(s, rng):
    idx = [i for i, ch in enumerate(s) if ch == "ʔ"]
    if not idx:
        return None
    i = rng.choice(idx)
    return s[:i] + s[i + 1:]


def shorten_vowel(s, rng):
    m = [x.start() for x in re.finditer(r"aa|ii|uu", s)]
    if not m:
        return None
    i = rng.choice(m)
    return s[:i] + s[i + 1:]


def add_space(s, rng):
    idx = [i for i in range(2, len(s) - 2) if s[i].isalpha() and s[i - 1].isalpha()]
    if not idx:
        return None
    i = rng.choice(idx)
    return s[:i] + " " + s[i:]


def english_typo(s, rng):
    idx = [i for i, ch in enumerate(s) if ch.isalpha() and ch.islower()]
    if len(idx) < 4:
        return None
    i = rng.choice(idx)
    new = rng.choice([c for c in "aeiourstn" if c != s[i]])
    return s[:i] + new + s[i + 1:]


def truncate(s, rng):
    words = s.split()
    if len(words) < 4:
        return None
    return " ".join(words[:-2])


def lax_to_tense(s, rng):
    for a, b in (("ɪ", "i"), ("ʊ", "u"), ("ə", "a")):
        if a in s:
            i = rng.choice([x.start() for x in re.finditer(a, s)])
            return s[:i] + b + s[i + 1:]
    return None


# kind -> (table, value column, field name in the comparison, changer, extra where)
FIELD_PLANTS = {
    "a consonant changed in a verb form": ("paradigmatic_forms", "skiri_form", "form", swap_consonant, ""),
    "h written as b in a verb form": ("paradigmatic_forms", "skiri_form", "form", h_to_b, ""),
    "a glottal stop dropped from an example": ("examples", "skiri_text", "example.skiri", drop_glottal, "and coalesce(source,'parks_dictionary')='parks_dictionary'"),
    "a long vowel shortened in a verb form": ("paradigmatic_forms", "skiri_form", "form", shorten_vowel, ""),
    "a space put inside an example word": ("examples", "skiri_text", "example.skiri", add_space, "and coalesce(source,'parks_dictionary')='parks_dictionary'"),
    "an accent dropped from the IPA": ("lexical_entries", "phonetic_form", "phonetic_form", drop_accent, ""),
    "a lax vowel made tense in the IPA": ("lexical_entries", "phonetic_form", "phonetic_form", lax_to_tense, ""),
    "a consonant changed in the IPA": ("lexical_entries", "phonetic_form", "phonetic_form", swap_consonant, ""),
    "a letter changed in a gloss": ("glosses", "definition", "gloss", english_typo, ""),
    "an example translation cut short": ("examples", "english_translation", "example.english", truncate, "and coalesce(source,'parks_dictionary')='parks_dictionary'"),
    "a consonant changed in an etymology": ("etymology", "raw_etymology", "etymology", swap_consonant, ""),
    "a letter changed in a cognate": ("cognates", "form", "cognate.form", swap_consonant, ""),
}
CLASS_SWAP = {"N": "VI", "VI": "VT", "VT": "VI", "VD": "N", "ADV": "N", "LOC": "N", "VP": "VT"}
VERB_CLASS_SWAP = {"(1)": "(3)", "(3)": "(1)", "(4)": "(1)", "(2)": "(4)", "(1-a)": "(1-i)", "(1-i)": "(1-a)"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-kind", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261113)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    live = state.ROOT / "skiri_pawnee.db"
    folder = state.WORK / "recall"
    folder.mkdir(parents=True, exist_ok=True)
    copy_path = folder / "copy.db"
    if copy_path.exists():
        copy_path.unlink()
    src = sqlite3.connect("file:%s?mode=ro" % live.resolve().as_posix(), uri=True)
    dst = sqlite3.connect(str(copy_path))
    src.backup(dst)
    src.close()

    base_diffs, base_pairs, _, _ = s2e_compare.compare(str(live))
    dirty = {(d["entry_id"], base_field(d["field"])) for d in base_diffs if d["class"] == "difference"}
    base_residue = collections.Counter(d["entry_id"] for d in base_diffs if d["kind"] == "printed-not-stored")
    paired = {r["entry_id"] for r in base_pairs}
    touched = set()                                   # one plant per entry, so that hits cannot be confused
    plants = []

    def usable(entry_id, field):
        return entry_id in paired and entry_id not in touched and (entry_id, field) not in dirty

    for kind, (table, col, field, change, where) in FIELD_PLANTS.items():
        key = "entry_id" if table == "lexical_entries" else "id"
        rows = dst.execute('select %s, entry_id, "%s" from "%s" where "%s" is not null %s' % (key, col, table, col, where)).fetchall()
        rng.shuffle(rows)
        n = 0
        for rid, entry_id, value in rows:
            if n >= args.per_kind:
                break
            if not usable(entry_id, field):
                continue
            new = change(value, rng)
            if not new or new == value:
                continue
            dst.execute('update "%s" set "%s"=? where %s=?' % (table, col, key), (new, rid))
            touched.add(entry_id)
            plants.append({"kind": kind, "entry_id": entry_id, "field": field, "was": value, "now": new, "how": "field"})
            n += 1
    # class and verb class
    for kind, col, table_map in (("the grammatical class changed", "grammatical_class", CLASS_SWAP),
                                 ("the verb class changed", "verb_class", VERB_CLASS_SWAP)):
        rows = dst.execute('select entry_id, "%s" from lexical_entries where "%s" is not null' % (col, col)).fetchall()
        rng.shuffle(rows)
        n = 0
        for entry_id, value in rows:
            if n >= args.per_kind:
                break
            if value not in table_map or not usable(entry_id, "grammatical_class"):
                continue
            dst.execute('update lexical_entries set "%s"=? where entry_id=?' % col, (table_map[value], entry_id))
            touched.add(entry_id)
            plants.append({"kind": kind, "entry_id": entry_id, "field": "grammatical_class", "was": value, "now": table_map[value], "how": "field"})
            n += 1
    # a sense deleted, an example deleted
    for kind, table, where in (("a sense deleted", "glosses", "entry_id in (select entry_id from glosses group by entry_id having count(*) > 1)"),
                               ("an example deleted", "examples", "coalesce(source,'parks_dictionary')='parks_dictionary'")):
        rows = dst.execute('select id, entry_id from "%s" where %s' % (table, where)).fetchall()
        rng.shuffle(rows)
        n = 0
        for rid, entry_id in rows:
            if n >= args.per_kind:
                break
            if entry_id not in paired or entry_id in touched:
                continue
            dst.execute('delete from "%s" where id=?' % table, (rid,))
            touched.add(entry_id)
            plants.append({"kind": kind, "entry_id": entry_id, "field": "(printed text)", "was": "row %s" % rid, "now": "", "how": "residue"})
            n += 1
    # an entry deleted
    rows = dst.execute("select entry_id, headword from lexical_entries where coalesce(source,'') != 'blue_book'").fetchall()
    rng.shuffle(rows)
    n = 0
    for entry_id, headword in rows:
        if n >= args.per_kind:
            break
        if entry_id not in paired or entry_id in touched:
            continue
        for table in ("glosses", "etymology", "paradigmatic_forms", "examples", "cognates"):
            dst.execute('delete from "%s" where entry_id=?' % table, (entry_id,))
        dst.execute("delete from lexical_entries where entry_id=?", (entry_id,))
        touched.add(entry_id)
        plants.append({"kind": "an entry deleted", "entry_id": entry_id, "field": "(entry)", "was": headword, "now": "", "how": "entry"})
        n += 1
    dst.commit()
    dst.close()

    test_diffs, _, _, _ = s2e_compare.compare(str(copy_path))
    found = collections.defaultdict(set)
    residue = collections.Counter()
    missing_heads = collections.Counter()
    for d in test_diffs:
        if d["class"] != "difference":
            continue
        if d["kind"] == "printed-not-stored":
            residue[d["entry_id"]] += 1
        elif d["kind"] == "printed-entry-not-stored":
            missing_heads[d["headword"].split(" (")[0].split(" [")[0]] += 1
        else:
            found[d["entry_id"]].add(base_field(d["field"]))
    by_kind = collections.defaultdict(lambda: [0, 0])
    misses = []
    for p in plants:
        if p["how"] == "field":
            hit = p["field"] in found.get(p["entry_id"], set())
            if not hit and p["kind"] == "an example translation cut short":
                # cut at a word boundary, the rest of the sentence is reported as printed and not stored
                hit = residue[p["entry_id"]] > base_residue[p["entry_id"]]
        elif p["how"] == "residue":
            hit = residue[p["entry_id"]] > base_residue[p["entry_id"]]
        else:
            hit = missing_heads[p["was"].split(" (")[0].split(" [")[0]] > 0 or any(
                d["kind"] == "printed-entry-not-stored" and d["headword"].startswith(p["was"]) for d in test_diffs)
        by_kind[p["kind"]][0] += 1
        by_kind[p["kind"]][1] += int(hit)
        if not hit:
            misses.append(p)
    total = sum(v[0] for v in by_kind.values())
    caught = sum(v[1] for v in by_kind.values())
    result = {"seed": args.seed, "planted": total, "caught": caught, "recall": round(caught / float(total), 4),
              "by_kind": {k: {"planted": v[0], "caught": v[1], "recall": round(v[1] / float(v[0]), 4) if v[0] else None}
                          for k, v in by_kind.items()},
              "missed": misses}
    (state.OUT / "recall_test.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("planted %d errors of %d kinds; caught %d (%.1f%%)" % (total, len(by_kind), caught, 100.0 * caught / total))
    for k, v in by_kind.items():
        state.out("  %-44s %3d of %3d" % (k, v[1], v[0]))
    for p in misses[:25]:
        state.out("  MISSED %s | %s | %s -> %s" % (p["kind"], p["entry_id"], p["was"], p["now"]))
    copy_path.unlink()


if __name__ == "__main__":
    main()
