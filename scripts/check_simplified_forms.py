#!/usr/bin/env python3
"""
Are the simplified forms what the rules give from Parks's forms?
================================================================

Each dictionary entry carries two forms made for learners:

  simplified_pronunciation   made from Parks's phonetic form:  [kʊ́·rʊks] -> KOO-dooks
  normalized_form            the learner spelling, made from the headword, with the phonetic form
                             telling c (ts) from č:  huukiwihkahaaruʔ -> hûkiwihkahâru'

This check changes nothing. For every Parks entry it makes both again from
what is stored now and compares them with what is stored:

    python scripts/check_simplified_forms.py            # counts, and the entries that differ
    python scripts/check_simplified_forms.py --all      # list every difference, not the first 40

It also counts the one place where the respelling is known to be coarser than
Parks's transcription: he writes a short i and u as tense [i], [u] before a
glottal stop and in a few other places; the respelling writes every short i as
"ih" and every u as "oo", as his sound key does for the spelling. Whether to
show that difference is a teaching decision, not a copying error.

Blue Book-only entries are left out: the book gives no phonetic forms, and
their pronunciation is made from the spelling.
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fix_pronunciations import respell_phonetic  # noqa: E402
from ipa_notation import is_parks_notation  # noqa: E402
from respell_and_normalize import generate_normalized_form  # noqa: E402

SHORT_TENSE = re.compile(r"(?<![iíì])[iíì](?![iíì])|(?<![uúù])[uúù](?![uúù])")


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--db", default=str(ROOT / "skiri_pawnee.db"))
    args = ap.parse_args()
    conn = sqlite3.connect("file:%s?mode=ro" % Path(args.db).resolve().as_posix(), uri=True)
    rows = conn.execute("select entry_id, headword, phonetic_form, simplified_pronunciation, normalized_form from lexical_entries "
                        "where coalesce(source, '') != 'blue_book' order by entry_id").fetchall()
    no_ipa, old_notation, resp_diff, norm_diff, norm_error, tense = [], [], [], [], 0, 0
    for entry_id, headword, ipa, resp, norm in rows:
        if not ipa:
            no_ipa.append(headword)
            continue
        if ("-" in ipa or "•" in ipa) and not is_parks_notation(ipa):
            old_notation.append((headword, ipa))
        made = respell_phonetic(ipa)
        if made and made != resp:
            resp_diff.append((headword, ipa, resp, made))
        try:
            made_norm = generate_normalized_form(headword, ipa)[0]
            if made_norm and norm and made_norm != norm:
                norm_diff.append((headword, norm, made_norm))
        except Exception:
            norm_error += 1
        if SHORT_TENSE.search(ipa):
            tense += 1
    limit = None if args.all else 40
    out("Parks entries: %d" % len(rows))
    out("without a phonetic form: %d %s" % (len(no_ipa), no_ipa[:10]))
    out("phonetic form still in the old working notation (hyphen or bullet): %d" % len(old_notation))
    out("simplified pronunciation differs from what the rules give: %d" % len(resp_diff))
    for h, ipa, stored, made in resp_diff[:limit]:
        out("   %-26s %-34s stored %s; the rules give %s" % (h, ipa, stored, made))
    out("learner spelling differs from what the rule gives: %d   (rule could not be applied to %d entries)" % (len(norm_diff), norm_error))
    for h, stored, made in norm_diff[:limit]:
        out("   %-26s stored %s; the rule gives %s" % (h, stored, made))
    out("entries whose phonetic form has a short tense i or u that the respelling writes like the lax one: %d" % tense)
    ok = not (old_notation or resp_diff)
    out("")
    out("simplified pronunciations follow from the stored phonetic forms" if ok else "DIFFERENCES FOUND")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
