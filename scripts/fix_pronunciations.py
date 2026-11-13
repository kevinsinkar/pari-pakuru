#!/usr/bin/env python3
"""
Repair systematic defects in `simplified_pronunciation`
======================================================

The Phase 1.1c respelling (scripts/respell_and_normalize.py) mis-rendered three
things in Parks's phonetic transcriptions:

  1. optional sounds written in parentheses, e.g. [•kaa-ʔaa(h)•], were respelled
     as obligatory ("kah-'ahh") instead of "kah-'ah(h)";
  2. stem-final alternations {k/t} were dropped ("wee-tih" for wiitik) instead of
     "wee-tih(k/t)";
  3. mixed-quality vowel runs (uʊ) doubled the vowel ("'ooooh").

Blue-Book-only entries (source = 'blue_book') carry a synthetic, unsyllabified
phonetic form, so their respelling is a single unreadable blob; they are
re-respelled from the headword spelling with syllable breaks.

Nothing else is changed. Entries whose phonetic form simply differs from the
headword (e.g. kataʔa transcribed [kə-taa]) are Parks's own data and are only
listed for review.

Usage:
    python scripts/fix_pronunciations.py             # dry run: report only
    python scripts/fix_pronunciations.py --apply     # back up DB, update DB + JSON files
"""
import argparse
import datetime as dt
import json
import re
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_root_curriculum import respell_orthography  # noqa: E402
from ipa_notation import to_working  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
RESPELLED_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
FROZEN_SETS = ROOT / "curriculum" / "flashcard_sets.json"
REPORT = ROOT / "reports" / "fix_pronunciations_report.txt"
BACKUP_DIR = Path.home() / ".pari_pakuru_backups"

CONS = {"r": "d", "c": "ts", "č": "ch", "ʔ": "'", "p": "p", "t": "t", "k": "k", "s": "s", "w": "w", "h": "h", "n": "n"}
VQ = {"a": "a", "á": "a", "à": "a", "ə": "a", "i": "i", "í": "i", "ì": "i", "ɪ": "i", "u": "u", "ú": "u", "ù": "u", "ʊ": "u", "e": "e"}
VOUT = {("a", False): "uh", ("a", True): "ah", ("i", False): "ih", ("i", True): "ee", ("u", False): "oo", ("u", True): "oo", ("e", False): "eh", ("e", True): "eh"}
ACCENTED = set("áíúàìù")


def out(t):
    sys.stdout.buffer.write((t + "\n").encode("utf-8", errors="replace"))


def respell_syllable(syl):
    """Respell one IPA syllable; returns (text, accented)."""
    text, i, acc = [], 0, False
    while i < len(syl):
        ch = syl[i]
        if ch in VQ:
            q = VQ[ch]
            acc = acc or ch in ACCENTED
            j = i + 1
            long_ = False
            # extend the run only over the same vowel quality (ɪ/i, ʊ/u, ə/a) or a length mark;
            # a different quality (e.g. ʊɪ across a missing word break) starts a new vowel
            while j < len(syl) and (syl[j] in "ː́̀" or VQ.get(syl[j]) == q):
                if syl[j] in "́̀":
                    acc = True      # a combining accent on the vowel just read, as in Parks's ʊ́
                else:
                    long_ = True
                    acc = acc or syl[j] in ACCENTED
                j += 1
            text.append(VOUT[(q, long_)])
            i = j
        elif ch == "{":
            j = syl.index("}", i)
            alts = syl[i + 1:j].split("/")
            text.append("(" + "/".join(CONS.get(a, a) for a in alts) + ")")
            i = j + 1
        elif ch == "(":
            j = syl.index(")", i)
            inner = syl[i + 1:j]
            inner_text, _ = respell_syllable(inner)
            text.append(("-" if any(c in VQ for c in inner) else "") + "(" + inner_text + ")")
            i = j + 1
        elif ch in CONS:
            text.append(CONS[ch]); i += 1
        elif ch == "/":
            text.append("/"); i += 1   # Parks stem alternation kiis/kis, kept verbatim as before
        else:
            i += 1  # ː handled above; Ø + ? ! and anything else dropped
    s = "".join(text)
    return s, acc


def respell_phonetic(pf):
    """IPA phonetic form -> simplified pronunciation (variants joined by ' / ')."""
    # the database stores Parks's printed notation (syllable dot, edge dash); the rules below read the working one
    pf = to_working(pf)
    pf = unicodedata.normalize("NFC", pf).strip().strip("[]")
    pf = re.sub(r"^\+[a-zʔ]+-\]?\[?", "", pf)
    pf = re.sub(r"•?\((ʊt|ut|ir|uur|ɪr)\.\.\.\)", "", pf)
    outv = []
    for variant in pf.split(","):
        v = variant.strip().strip("•–— ").replace("•", "-").replace(".", "-")
        if not v:
            continue
        words = []
        for word in v.split():         # a phonetic form of two words is printed with a space between them
            sylls = []
            for syl in [s for s in word.split("-") if s.strip()]:
                s, acc = respell_syllable(syl.strip())
                if not s:
                    continue
                if s.startswith("-"):      # optional syllable wrapped by respell_syllable
                    s = s[1:]
                sylls.append(s.upper() if acc else s)
            if sylls:
                words.append("-".join(sylls).replace("-(-", "-(").replace("--", "-"))
        if words:
            outv.append(" ".join(words))
    return " / ".join(outv)


def classify(old, new, pf, source):
    if source == "blue_book":
        return "bb_resyllabified"
    if "(" in pf and "(" not in old and "(" in new:
        return "optional_sound_marked"
    if "{" in pf and "(" in new and "/" in new.split("(")[-1]:
        return "alternation_restored"
    if re.search(r"(oo){2,}|(ee){2,}|(ah){2,}|(uh){2,}|(ih){2,}", old):
        return "vowel_run_fixed"
    return "other"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    rows = conn.execute("""select entry_id, headword, phonetic_form, simplified_pronunciation, source
                           from lexical_entries where simplified_pronunciation is not null""").fetchall()
    changes, cats, samples = {}, Counter(), defaultdict(list)
    review = []
    for eid, hw, pf, old, source in rows:
        hw0 = unicodedata.normalize("NFC", hw).split(",")[0].strip()
        if source == "blue_book":
            new = respell_orthography(re.sub(r"[?!+]", "", hw0).replace(".", "-")).replace("--", "-")
        else:
            if not pf:
                continue
            new = respell_phonetic(pf)
        if not new:
            continue
        if new != old:
            cat = classify(old, new, pf or "", source)
            changes[eid] = new
            cats[cat] += 1
            if len(samples[cat]) < 12:
                samples[cat].append((hw0, pf, old, new))
        # Parks transcription drops a headword glottal stop: list for review only
        if source != "blue_book" and hw0.endswith("ʔa") and pf and "ʔ" not in pf.split("-")[-1]:
            review.append((hw0, pf, old))

    lines = [f"fix_pronunciations report — {dt.datetime.now():%Y-%m-%d %H:%M}", f"entries checked: {len(rows)}; entries to change: {len(changes)}", ""]
    for cat, n in cats.most_common():
        lines.append(f"== {cat}: {n}")
        for hw0, pf, old, new in samples[cat]:
            lines.append(f"   {hw0:28} {str(pf):40} {old!r:34} -> {new!r}")
        lines.append("")
    lines += [f"== for review, not changed: headword ends in -ʔa but Parks's phonetic form has no glottal stop ({len(review)})"]
    lines += [f"   {h:28} {p:34} {o}" for h, p, o in review]
    out("\n".join(lines[:60]))

    if not args.apply:
        # the report file is the record of the applied run (2026-11-08): a dry run never rewrites it
        out("dry run — nothing written, report left as it is (use --apply)")
        return
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    out(f"... full report: {REPORT}")
    if cats["other"]:
        out("refusing to apply: 'other' category is non-empty; inspect the report first")
        return
    BACKUP_DIR.mkdir(exist_ok=True)
    backup = BACKUP_DIR / f"skiri_pawnee_backup_{dt.datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(args.db, backup)
    out(f"backup: {backup}")
    conn.executemany("update lexical_entries set simplified_pronunciation=? where entry_id=?", [(v, k) for k, v in changes.items()])
    conn.commit()
    out(f"DB rows updated: {len(changes)}")
    # keep the JSON sources in step
    if RESPELLED_JSON.exists():
        data = json.loads(RESPELLED_JSON.read_text(encoding="utf-8"))
        n = 0
        for e in data:
            if e.get("entry_id") in changes:
                e.setdefault("part_I", {})["simplified_pronunciation"] = changes[e["entry_id"]]
                n += 1
        RESPELLED_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        out(f"{RESPELLED_JSON.name}: {n} entries updated")
    if FROZEN_SETS.exists():
        sets = json.loads(FROZEN_SETS.read_text(encoding="utf-8"))
        n = 0
        for w in sets["weeks"]:
            for card in w["cards"]:
                if card["entry_id"] in changes:
                    card["simplified_pronunciation"] = changes[card["entry_id"]]
                    n += 1
        # the freeze script's own format (indent 1), so that a repair shows as a small difference
        FROZEN_SETS.write_text(json.dumps(sets, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        out(f"{FROZEN_SETS.name}: {n} card pronunciations updated (week membership unchanged)")


if __name__ == "__main__":
    main()
