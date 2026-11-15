#!/usr/bin/env python3
"""
The 93 "Blue Book-only" entries: their printed forms, and which of them Parks has (2026-11-14)
==============================================================================================

93 entries of the database come from the Blue Book and not from Parks's
dictionary. Their headwords were respelled into Parks's letters when they
were made (*paisic* for the book's *paisits*), and for 45 of them no printed
form was on record (open item 35). The project's rule is to quote the Blue
Book as it prints.

    python scripts/bluebook_only_entries.py            # what is found; changes nothing
    python scripts/bluebook_only_entries.py --apply    # backs up, sets the two things below, appends the report

For each of the 93 the script looks in the table of Blue Book forms
(blue_book_attestations, read from the scan in November 2026) for:

1. **Its printed form.** A row already linked to the entry, or a row whose
   form is the entry's headword letter for letter once both are written the
   same way (ts as c, the apostrophe as ʔ, accents, raised dots and capitals
   aside) and whose English is the entry's gloss. Rows found the second way
   that are linked to no entry are linked to this one (--apply).

2. **Its entry in Parks, if it has one.** The Blue Book does not write vowel
   length, so *tsuraki* 'girl' and Parks's *cuuraki* 'girl' are one word in
   two spellings. A Parks entry is taken as the same word when its headword
   has the same letters as the Blue Book form with long vowels written short
   and a final ʔ aside, and the two share a word of their English meaning.
   --apply writes that entry into the column bb_variant_of, which five of
   the 93 already carried. Nothing is merged and no entry is removed: the
   flashcard list is frozen on entry ids.

What this changes for a reader: nothing by itself. The public site reads the
two facts from the database when it is built (scripts/build_static_site.py)
and shows a Blue Book-only entry with the form the book prints, and with the
dictionary's entry for the same word where there is one.

Entries for which neither is found are listed. They are for a person with
the book.
"""
import argparse
import collections
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "bluebook_only_entries_report.txt"


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def letters(form):
    """A form in one spelling: ts as c, apostrophe and ? as ʔ; accents, dots, capitals and punctuation aside."""
    f = unicodedata.normalize("NFD", form or "").lower()
    f = "".join(ch for ch in f if not unicodedata.combining(ch))
    f = f.replace("ts", "c").replace("'", "ʔ").replace("’", "ʔ").replace("?", "ʔ")
    return re.sub(r"[^a-zʔ]", "", f)


def short(key):
    """Long vowels written short, a final glottal stop aside: what the Blue Book's spelling keeps of a Parks headword."""
    return re.sub(r"([aiu])\1", r"\1", key).rstrip("ʔ")


def words(text):
    return {w for w in re.findall(r"[a-z]{3,}", (text or "").lower()) if w not in {"the", "and", "for", "with", "one"}}


def plan(conn):
    bb = conn.execute("select entry_id, headword, bb_variant_of from lexical_entries where source = 'blue_book' order by entry_id").fetchall()
    gloss = collections.defaultdict(list)
    for eid, text in conn.execute("select entry_id, definition from glosses"):
        gloss[eid].append(text or "")
    parks = conn.execute("select entry_id, headword from lexical_entries where coalesce(source, 'parks') = 'parks'").fetchall()
    by_short = collections.defaultdict(list)
    for eid, hw in parks:
        if hw.strip().endswith("-") or hw.strip().startswith("-"):
            continue                               # a bound form is not the word the Blue Book prints as a word
        for variant in hw.split(","):
            by_short[short(letters(variant))].append(eid)
    head = dict(parks)
    atts = conn.execute("select id, bb_skiri_form, bb_english, page_number, entry_id from blue_book_attestations order by id").fetchall()
    rows = []
    for eid, hw, variant_of in bb:
        key, mine = letters(hw), words(" ".join(gloss[eid]))
        linked = [a for a in atts if a[4] == eid]
        matched = [a for a in atts if a[4] != eid and letters(a[1]) == key and key
                   and (words(a[2]) & mine or re.sub(r"[^a-z]", "", (a[2] or "").lower()) in {re.sub(r"[^a-z]", "", g.lower()) for g in gloss[eid]})]
        printed = []
        for a in linked + matched:
            form = a[1].strip()
            if form not in [p[0] for p in printed]:
                printed.append((form, a[3]))
        # the same word in Parks: by the link of a matched row, or by its letters, and in either case by a shared English word
        same = []
        for cand in dict.fromkeys(by_short.get(short(key), [])):
            if words(" ".join(gloss[cand])) & (mine | set().union(*[words(a[2]) for a in linked + matched] or [set()])):
                same.append(cand)
        rows.append({"entry_id": eid, "headword": hw, "gloss": "; ".join(gloss[eid]), "printed": printed, "variant_of": variant_of,
                     "to_link": [a[0] for a in matched if a[4] is None], "parks": same})
    return rows, head, gloss


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write bb_variant_of and the links (the default changes nothing)")
    ap.add_argument("--list", action="store_true", help="print every entry")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB))
    rows, head, gloss = plan(conn)
    with_printed = [r for r in rows if r["printed"]]
    one_parks = [r for r in rows if len(r["parks"]) == 1]
    several = [r for r in rows if len(r["parks"]) > 1]
    to_set = [r for r in one_parks if r["variant_of"] != r["parks"][0]]
    conflict = [r for r in rows if r["variant_of"] and r["parks"] and r["variant_of"] not in r["parks"]]
    links = sum(len(r["to_link"]) for r in rows)
    lines = ["The Blue Book-only entries: %s, %s" % ("applied" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")), ""]
    lines.append("%d entries. A printed form is on record or found for %d; for %d none is found." % (len(rows), len(with_printed), len(rows) - len(with_printed)))
    stored_only = [r for r in rows if r["variant_of"] and not r["parks"]]
    lines.append("%d are a word Parks has, in the Blue Book's spelling: for %d one dictionary entry fits by letters and meaning, and %d more "
                 "carry a dictionary entry from an earlier decision. %d fit several dictionary entries and are left. For %d no dictionary "
                 "entry fits by this rule; the Blue Book often writes e where Parks writes ii (resáru' beside riisaaruʔ 'chief'), "
                 "which this rule does not follow, so some of those are in the dictionary too." % (
                     len(one_parks) + len(stored_only), len(one_parks), len(stored_only), len(several),
                     len(rows) - len(one_parks) - len(several) - len(stored_only)))
    lines.append("To write: bb_variant_of for %d entries (%d already carry it); %d rows of Blue Book forms to link to their entry." % (
        len([r for r in to_set if not r["variant_of"]]), len([r for r in rows if r["variant_of"]]), links))
    if conflict:
        lines.append("Stored bb_variant_of that this rule does not find (left as stored): %s" % ", ".join("%s -> %s" % (r["entry_id"], r["variant_of"]) for r in conflict))
    detail = ["", "A word Parks has (%d):" % len(one_parks)]
    detail += ["  %-16s %-20s = %-22s %s  | printed %s" % (r["headword"], "(" + r["gloss"][:18] + ")", head[r["parks"][0]], r["parks"][0],
                                                          ", ".join("%s p.%s" % (f, p - 28 if p else "?") for f, p in r["printed"]) or "none on record") for r in one_parks]
    detail += ["", "Several dictionary entries fit, left for a person (%d):" % len(several)]
    detail += ["  %-16s (%s): %s" % (r["headword"], r["gloss"][:40], ", ".join("%s %s" % (head[p], p) for p in r["parks"])) for r in several]
    rest = [r for r in rows if not r["parks"] and not r["variant_of"]]
    detail += ["", "No dictionary entry fits: in the Blue Book only, as far as this rule can tell (%d):" % len(rest)]
    detail += ["  %-16s (%s)  printed %s" % (r["headword"], r["gloss"][:40], ", ".join("%s p.%s" % (f, p - 28 if p else "?") for f, p in r["printed"]) or "NONE FOUND")
               for r in rest]
    for line in lines + (detail if args.list or args.apply else []):
        out(line)
    if not args.apply:
        out("")
        out("Run again with --apply to write. --list shows every entry.")
        return
    if not to_set and not links:
        out("")
        out("Nothing to write.")
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    conn.close()
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_bb_only.db" % stamp))
    conn = sqlite3.connect(str(DB))
    with conn:
        for r in to_set:
            if not r["variant_of"]:
                conn.execute("update lexical_entries set bb_variant_of = ? where entry_id = ?", (r["parks"][0], r["entry_id"]))
        for r in rows:
            for att_id in r["to_link"]:
                conn.execute("update blue_book_attestations set entry_id = ?, match_type = 'bb_only_form_and_english', match_confidence = 1.0, "
                             "notes = coalesce(notes || '; ', '') || 'linked by bluebook_only_entries.py 2026-11-14' where id = ? and entry_id is null",
                             (r["entry_id"], att_id))
    conn.close()
    with REPORT.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines + ["backup: OneDrive/pari_pakuru_backups (stamp %s)" % stamp] + detail) + "\n\n" + "=" * 100 + "\n\n")
    out("")
    out("written; report appended to %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
