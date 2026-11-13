#!/usr/bin/env python3
"""
Store Parks's phonetic forms exactly as he prints them (2026-11-13)
===================================================================

Until now the database held each phonetic form in a working notation: a
hyphen for Parks's syllable dot, a bullet for his dash at the edge of a bound
form, à for his ə́ and í for his ɪ́. The user's decision of 2026-11-13 is to
keep Parks's own notation.

This script sets the phonetic form of every Parks entry to what is printed in
that entry, taken from the PDF text layer and decoded with the character
table that was verified against the printed glyphs
(scripts/source_audit/chartable.py). It then regenerates the simplified
pronunciation from the new form and checks that nothing else moved.

    python scripts/restore_parks_ipa.py            # dry run: prints what it would do, writes nothing
    python scripts/restore_parks_ipa.py --apply    # backs up, then writes the database, the JSON files, the frozen flashcards, the report

For every entry it says which of these holds:
    symbols only      the printed form is the stored form in Parks's symbols; nothing else differs
    content corrected the stored form also differed in a letter, an accent or a word space
                      (the differences the audit found, all confirmed on the page)
    added             the page has a phonetic form and the database had none
and for the simplified pronunciation: unchanged, or changed (listed, with the reason).

Blue Book-only entries are not touched: the book gives no phonetic forms, and
what those entries hold is a spelling-based stand-in, not IPA.

Needs reports/source_audit_2026-11/work/s2e_printed_entries.jsonl; if it is
missing, run scripts/source_audit/decode_pages.py and s2e_segment.py first.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import compare_core as cc  # noqa: E402
import s2e_compare  # noqa: E402
from fix_pronunciations import respell_phonetic  # noqa: E402
from respell_and_normalize import generate_normalized_form  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
E2S_JSON = ROOT / "Dictionary Data" / "english_to_skiri_linked.json"
FROZEN = ROOT / "curriculum" / "flashcard_sets.json"
REPORT = ROOT / "reports" / "source_audit_2026-11" / "ipa_restored_report.txt"


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def printed_ipa(block):
    """The bracketed phonetic form of a printed entry, as printed, or None."""
    o, k = block.orig, block.kinds
    start = next((i for i, ch in enumerate(o) if ch == "[" and k[i] == "P"), None)
    if start is None:
        return None
    end = next((i for i in range(start, len(o)) if o[i] == "]" and k[i] == "P"), None)
    if end is None:
        return None
    return cc.nfc(cc.readings(o[start:end + 1])[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = ap.parse_args()
    printed = [json.loads(line) for line in s2e_compare.PRINTED.open(encoding="utf-8")]
    blocks = {p["seq"]: cc.Block(p["spans"]) for p in printed}
    db = s2e_compare.load_db(DB)
    pairs, how, phantom, missing = s2e_compare.pair_entries(db, printed, blocks)

    changes, kinds = [], Counter()
    lines = {"content corrected": [], "added": [], "printed form not found": [], "respelling changed": [],
             "learner spelling corrected": [], "learner spelling differs from the rule": []}
    for entry_id, seq in sorted(pairs.items(), key=lambda kv: kv[1]):
        e = db[entry_id]
        new = printed_ipa(blocks[seq])
        old = e["phonetic_form"]
        if new is None:
            if old:
                kinds["printed form not found"] += 1
                lines["printed form not found"].append("%-26s stored %s" % (e["headword"], old))
            else:
                kinds["no phonetic form in print or in the database"] += 1
            continue
        if old == new:
            kinds["already as printed"] += 1
            continue
        if not old:
            kind = "added"
            lines[kind].append("%-26s %s   [book p. %d]" % (e["headword"], new, printed[seq - 1]["page"] + 348))
        else:
            as_printed = cc.stored_phonetic_as_printed(old)
            # a space after a comma or before a bracketed preverb is how the page is set;
            # a space between two words of the form is content
            squeeze = lambda s: re.sub(r" *([,(]) *", r"\1", cc.tidy(s))
            letters_same = cc.fold_lax_i(cc.skeleton(as_printed)) == cc.fold_lax_i(cc.skeleton(new))
            spaces_same = squeeze(as_printed).count(" ") == squeeze(new).count(" ")
            kind = "symbols only" if letters_same and spaces_same else "content corrected"
            if kind == "content corrected":
                lines[kind].append("%-26s %s -> %s   [book p. %d]" % (e["headword"], old, new, printed[seq - 1]["page"] + 348))
        kinds[kind] += 1
        old_resp = e["simplified_pronunciation"]
        new_resp = respell_phonetic(new) or old_resp
        if new_resp != old_resp:
            lines["respelling changed"].append("%-26s %s -> %s   (%s)" % (e["headword"], old_resp, new_resp, kind))
        # the learner spelling is made from the headword; the phonetic form tells c (ts) from č in it
        new_norm = e["normalized_form"]
        try:
            norm = generate_normalized_form(e["headword"], new)[0]
        except Exception:                                   # the 2026-03 function was not written for every form
            norm = None
        if norm and norm != e["normalized_form"]:
            try:
                from_old = generate_normalized_form(e["headword"], old)[0] if old else None
            except Exception:
                from_old = None
            if from_old == norm:
                # the stored spelling differs from what the rule gives for a reason other than the phonetic form: listed, not changed
                lines["learner spelling differs from the rule"].append("%-26s stored %s; the rule gives %s" % (e["headword"], e["normalized_form"], norm))
            else:
                lines["learner spelling corrected"].append("%-26s %s -> %s" % (e["headword"], e["normalized_form"], norm))
                new_norm = norm
        changes.append((entry_id, old, new, old_resp, new_resp, new_norm))

    header = ["restore_parks_ipa — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "Parks entries paired with their printed entry: %d of %d" % (len(pairs), len(db)),
              "phonetic forms set to the printed form: %d   %s" % (len(changes), dict(kinds)),
              "simplified pronunciations that change: %d" % len(lines["respelling changed"]),
              "learner spellings corrected because the phonetic form they were made from was wrong: %d" % len(lines["learner spelling corrected"]),
              "learner spellings that differ from the rule for another reason (listed, not changed): %d" % len(lines["learner spelling differs from the rule"])]
    body = []
    for title in ("content corrected", "added", "printed form not found", "respelling changed", "learner spelling corrected",
                  "learner spelling differs from the rule"):
        body += ["", "== %s (%d)" % (title, len(lines[title]))] + ["  " + x for x in lines[title]]
    if not args.apply:
        out("\n".join(header))
        out("\n".join(body[:150]))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s.db" % stamp))
    for f in (S2E_JSON, E2S_JSON, FROZEN):
        shutil.copy2(f, backups / ("%s_backup_%s%s" % (f.stem, stamp, f.suffix)))
    conn = sqlite3.connect(str(DB))
    conn.executemany("update lexical_entries set phonetic_form=?, simplified_pronunciation=?, normalized_form=? where entry_id=?",
                     [(new, resp, norm, eid) for eid, old, new, old_resp, resp, norm in changes])
    conn.commit()
    conn.close()
    new_of = {eid: (new, resp, old, norm) for eid, old, new, old_resp, resp, norm in changes}
    data = json.loads(S2E_JSON.read_text(encoding="utf-8"))
    n_s2e = 0
    for e in data:
        hit = new_of.get(e.get("entry_id"))
        if hit:
            e.setdefault("part_I", {})["phonetic_form"] = hit[0]
            e["part_I"]["simplified_pronunciation"] = hit[1]
            if hit[3]:
                e["normalized_form"] = hit[3]
            n_s2e += 1
    S2E_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # the English-to-Skiri file repeats the phonetic form of the entry each subentry is linked to
    raw = E2S_JSON.read_text(encoding="utf-8")
    e2s = json.loads(raw)
    n_e2s = n_e2s_other = 0
    for entry in e2s:
        for sub in entry.get("subentries") or []:
            hit = new_of.get(sub.get("s2e_entry_id"))
            p1 = sub.get("part_I") or {}
            if hit and p1.get("phonetic_form"):
                if p1["phonetic_form"] == hit[2] or cc.skeleton(cc.stored_phonetic_as_printed(p1["phonetic_form"])) == cc.skeleton(cc.stored_phonetic_as_printed(hit[2] or "")):
                    p1["phonetic_form"] = hit[0]
                    n_e2s += 1
                else:
                    n_e2s_other += 1
    indent = 2 if raw.startswith("[\n  ") else 1 if raw.startswith("[\n ") else None
    E2S_JSON.write_text(json.dumps(e2s, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
    sets = json.loads(FROZEN.read_text(encoding="utf-8"))
    n_cards = 0
    for wk in sets["weeks"]:
        for card in wk["cards"]:
            hit = new_of.get(card["entry_id"])
            if hit:
                card["phonetic_form"] = hit[0]
                card["simplified_pronunciation"] = hit[1]
                if hit[3]:
                    card["normalized_form"] = hit[3]
                n_cards += 1
    FROZEN.write_text(json.dumps(sets, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False, stdout=subprocess.DEVNULL)
    header += ["", "written: database %d entries; %s %d entries; %s %d subentries (%d left: their form differed from the entry they are linked to); "
               "frozen flashcards %d cards (membership unchanged)" % (len(changes), S2E_JSON.name, n_s2e, E2S_JSON.name, n_e2s, n_e2s_other, n_cards),
               "backups: OneDrive/pari_pakuru_backups (stamp %s)" % stamp]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
