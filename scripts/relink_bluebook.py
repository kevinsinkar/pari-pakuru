#!/usr/bin/env python3
"""Tie the rows of the Blue Book table to dictionary entries again, soundly.

What was wrong. In March 2026 `blue_book_verify.py` tied a Blue Book form to
a dictionary entry by four tests. The third, "prefix", accepted any entry
whose headword is the beginning of the form: *asáki* 'dog' and *arúsa*
'horse' were tied to the entry *a* 'be stretched out', 139 forms beginning
with *ta* to the entry *ta* 'hang suspended', every question beginning with
*Kiriké* 'what' to *kiri* 'domestic cat'. 404 of the 1,026 rows were tied
that way. `link_bb_vocab.py` (October) tied rows by the exact form and a
shared meaning, but looked only at rows that had no tie yet. The prefix ties
stayed, and three things rested on them:

  * `lexical_entries.blue_book_attested`, the "Blue Book" badge and a boost
    in the search;
  * the Blue Book sentences stored as examples of an entry (table
    `examples`, 88 rows): "What is it?" stood as an example of 'domestic
    cat', on the public site;
  * the links from the vocabulary of the lesson pages to dictionary entries.

What this script does.

1. A row is tied to an entry only if its form, in the Blue Book's spelling
   set over into Parks's letters and with long vowels written short (the
   Blue Book does not write vowel length), IS a headword, and the English
   beside it shares a word with the entry's glosses. One entry must fit;
   where two do, the row is left without a tie and listed. This is the test
   of `link_bb_vocab.py`, applied to every row whose present tie is not by
   the exact form: "prefix", "stem", and "propagated" from such a tie.
   A row whose form fits one entry but whose English does not is tied if the
   same form is tied soundly elsewhere in the book ("propagated").
   A "stem" tie (a verb form tied to its verb) is kept if the meanings share
   a word.
   The same test is put to the ties that were made by the exact form without
   asking the meaning: 20 of them share no word with their entry. Some are
   homonyms (*hiru'* 'meadow' tied to *hiruʔ* 'go on!', *tát•at* 'I went' to
   *tatat* 'be stuck to'); those are judged again like the others. Four are
   right although no word is shared and are kept by name: REVIEWED, below.
2. Every other such row loses its tie: a sentence is not a form of one entry.
3. A Blue Book sentence is an example of an entry only if it contains, as a
   word, a form that the book lists and that is tied soundly to that entry
   (four letters or more, so that particles are not caught by chance), and
   only if it is a sentence: a reading passage of more than ten words is an
   example of no single word.
4. `blue_book_attested` is set from the ties as they then are: an entry is
   attested if a row is tied to it, if it was made from a Blue Book word, or
   if such an entry is the textbook's spelling of it.

Nothing is read anew and no form is changed: only which entry a row points to.

Usage:
    python scripts/relink_bluebook.py            # lists what it would change; changes nothing
    python scripts/relink_bluebook.py --apply    # backs up, writes, appends to the report, writes the dump
    python scripts/relink_bluebook.py --check    # exit 0 if nothing is left to do
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from link_bb_vocab import bb_normalize, collapse_length, content_words, glosses_overlap, parks_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "bluebook_relink_report.txt"

BY_THE_FORM = ("exact_normalized", "orthographic", "loose", "bb_only_form_and_english")
SOUND = BY_THE_FORM + ("propagated", "stem")
MIN_WORD = 4            # letters a word of a sentence must have to carry the sentence to an entry
MAX_WORDS = 10          # a longer text is a reading passage, not an example of one word
# Ties looked at one by one on 2026-11-14: the English beside the form shares no word with the entry's glosses,
# and the tie is right all the same. row id -> why it is kept.
REVIEWED = {
    2434: "the name of the band; the English beside it explains the name",
    2730: "the Blue Book's name for December is this word, 'in winter'",
    2783: "'pork' beside the entry for the pig, which Parks also glosses 'bacon'",
    2253: "a form of 'go'; 'gone' and 'go' are one word",
}
TODAY = "2026-11-14"


def out(text=""):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def unaccent(text):
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch))


def bb_key(form):
    """A Blue Book form as a key in Parks's letters: no accents, bullets or capitals, long vowels short."""
    return collapse_length(bb_normalize(unaccent(form)))


def load(conn):
    entries = {}
    index = defaultdict(set)
    for r in conn.execute(
            "select le.entry_id, le.headword, le.normalized_form, le.source, le.blue_book_attested, le.bb_variant_of, "
            "  (select group_concat(definition, ' ; ') from glosses g where g.entry_id = le.entry_id) as defs "
            "from lexical_entries le"):
        entries[r["entry_id"]] = r
        for field in (r["headword"], r["normalized_form"]):
            for alt in re.split(r"[,/]\s*", field or ""):
                key = parks_key(alt)
                if key:
                    index[key].add(r["entry_id"])
                    index[key.replace("ʔ", "")].add(r["entry_id"])
    rows = conn.execute(
        "select id, bb_skiri_form, bb_english, context_type, lesson_number, entry_id, match_type, match_confidence, "
        "notes from blue_book_attestations where bb_skiri_form is not null order by id").fetchall()
    return entries, index, rows


def by_the_form(row, entries, index):
    """(entry id or None, why) for a row judged by its form and its English alone."""
    key = bb_key(row["bb_skiri_form"])
    if not key:
        return None, "no letters"
    candidates = index.get(key) or index.get(key.replace("ʔ", "")) or set()
    if not candidates:
        return None, "no headword has this form"
    def parks_first(pool):
        """A Blue Book-only entry beside its Parks twin: the Parks entry is the entry."""
        parks = {c for c in pool if entries[c]["source"] != "blue_book"}
        return parks if len(parks) == 1 else pool

    fitting = parks_first({c for c in candidates if glosses_overlap(row["bb_english"], entries[c]["defs"])})
    if len(fitting) == 1:
        return next(iter(fitting)), "the form is the headword and the meanings share a word"
    if len(fitting) > 1:
        return None, "ambiguous: %s" % ", ".join(sorted(entries[c]["headword"] for c in fitting))
    only = parks_first(candidates)
    if len(only) == 1:
        return None, "form fits %s; meaning does not" % entries[next(iter(only))]["headword"]
    return None, "form fits %d entries; meaning fits none" % len(candidates)


def form_is_headword(row, entries):
    e = entries.get(row["entry_id"])
    if e is None:
        return False
    key = bb_key(row["bb_skiri_form"])
    keys = set()
    for field in (e["headword"], e["normalized_form"]):
        for alt in re.split(r"[,/]\s*", field or ""):
            k = parks_key(alt)
            keys.update({k, k.replace("ʔ", "")})
    return bool(key) and (key in keys or key.replace("ʔ", "") in keys)


def plan(conn):
    entries, index, rows = load(conn)
    new_tie = {}          # row id -> (entry id or None, match type, note)
    kept, changes = [], []
    for r in rows:
        if r["entry_id"] is None:
            continue
        shares_a_word = glosses_overlap(r["bb_english"], entries[r["entry_id"]]["defs"])
        if r["match_type"] == "propagated" and form_is_headword(r, entries):
            kept.append(r)             # the same word listed twice in the book, once with another English
            continue
        if r["match_type"] in BY_THE_FORM + ("stem",) and (shares_a_word or r["id"] in REVIEWED):
            kept.append(r)
            continue
        old = entries[r["entry_id"]]["headword"] if r["entry_id"] in entries else r["entry_id"]
        entry_id, why = by_the_form(r, entries, index)
        if entry_id == r["entry_id"]:
            kept.append(r)
            continue
        new_tie[r["id"]] = (entry_id, "orthographic" if entry_id else "none", why, old)
    # a form that fits one entry but whose English does not: tied if the same form is tied soundly elsewhere
    sound_key = defaultdict(set)
    for r in rows:
        tied = new_tie[r["id"]][0] if r["id"] in new_tie else r["entry_id"]
        mtype = new_tie[r["id"]][1] if r["id"] in new_tie else r["match_type"]
        if tied and mtype in BY_THE_FORM:
            sound_key[bb_key(r["bb_skiri_form"])].add(tied)
    for r in rows:
        if r["id"] in new_tie and new_tie[r["id"]][0] is None:
            targets = sound_key.get(bb_key(r["bb_skiri_form"]), set())
            if len(targets) == 1:
                new_tie[r["id"]] = (next(iter(targets)), "propagated", "the same form is tied by its meaning elsewhere",
                                    new_tie[r["id"]][3])
    for r in rows:
        if r["id"] in new_tie:
            entry_id, mtype, why, old = new_tie[r["id"]]
            changes.append({"id": r["id"], "form": r["bb_skiri_form"], "english": r["bb_english"] or "",
                            "lesson": r["lesson_number"], "context": r["context_type"], "was": old,
                            "was_type": r["match_type"], "entry_id": entry_id, "match_type": mtype, "why": why,
                            "now": entries[entry_id]["headword"] if entry_id else None})
    # the ties as they will be
    tie_after = {r["id"]: (new_tie[r["id"]][0] if r["id"] in new_tie else r["entry_id"]) for r in rows}
    type_after = {r["id"]: (new_tie[r["id"]][1] if r["id"] in new_tie else r["match_type"]) for r in rows}

    # ---- Blue Book sentences as examples of an entry
    word_entry = defaultdict(set)
    for r in rows:
        if (tie_after[r["id"]] and type_after[r["id"]] in BY_THE_FORM + ("propagated",)
                and len(r["bb_skiri_form"].split()) == 1):
            word_entry[bb_key(r["bb_skiri_form"])].add(tie_after[r["id"]])
    examples = conn.execute("select id, entry_id, skiri_text, english_translation, usage_context from examples "
                            "where source = 'blue_book' order by id").fetchall()
    wanted = []           # (entry_id, text, english, context) in a fixed order
    seen = set()
    for text, english, context in sorted({(e["skiri_text"], e["english_translation"], e["usage_context"]) for e in examples}):
        if len(text.split()) > MAX_WORDS or re.search(r"[.?!]\s+\S", text):
            continue                   # a passage, or more than one sentence
        for word in text.split():
            key = bb_key(word)
            targets = word_entry.get(key, set())
            if len(key) >= MIN_WORD and len(targets) == 1:
                target = next(iter(targets))
                if (target, text) not in seen:
                    seen.add((target, text))
                    wanted.append((target, text, english, context))
    have = {(e["entry_id"], e["skiri_text"]) for e in examples}
    example_plan = {
        "remove": [e for e in examples if (e["entry_id"], e["skiri_text"]) not in seen],
        "add": [w for w in wanted if (w[0], w[1]) not in have],
        "stay": [e for e in examples if (e["entry_id"], e["skiri_text"]) in seen],
        "sentences": len({e["skiri_text"] for e in examples}),
        "sentences_without_a_tied_word": sorted({e["skiri_text"] for e in examples} - {w[1] for w in wanted}),
    }

    # ---- the flag
    # An entry is attested in the Blue Book if a row is tied to it, if it was made from a Blue Book word, or if
    # such an entry is the textbook's spelling of it (bb_variant_of).
    tied_entries = {e for e in tie_after.values() if e}
    tied_entries |= {e["bb_variant_of"] for e in entries.values() if e["source"] == "blue_book" and e["bb_variant_of"]}
    flags = []
    for entry_id, e in entries.items():
        should = 1 if (entry_id in tied_entries or e["source"] == "blue_book") else 0
        if (e["blue_book_attested"] or 0) != should:
            flags.append((entry_id, e["headword"], e["blue_book_attested"] or 0, should))
    return entries, rows, kept, changes, example_plan, flags


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: list them only)")
    ap.add_argument("--check", action="store_true", help="exit 0 if nothing is left to do")
    args = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    entries, rows, kept, changes, ex, flags = plan(conn)
    by_type = Counter(r["match_type"] for r in rows)
    conn.close()

    retied = [c for c in changes if c["entry_id"]]
    untied = [c for c in changes if not c["entry_id"]]
    if args.check:
        problems = []
        if changes:
            problems.append("%d rows are tied to an entry otherwise than by their form" % len(changes))
        if ex["remove"] or ex["add"]:
            problems.append("%d Blue Book examples stand under an entry none of their words is tied to, %d are missing"
                            % (len(ex["remove"]), len(ex["add"])))
        if flags:
            problems.append("blue_book_attested does not follow the ties for %d entries" % len(flags))
        if problems:
            out("NOT in order: " + "; ".join(problems))
            return 1
        tied = sum(1 for r in rows if r["entry_id"])
        out("Blue Book ties in order: %d of %d rows are tied to an entry, every one by its form (%s); %d Blue Book "
            "sentences stand as examples, each under an entry one of its words is tied to; blue_book_attested "
            "follows the ties" % (tied, len(rows), ", ".join("%s %d" % (k, v) for k, v in sorted(
                (k, v) for k, v in by_type.items() if k and k != "none")), len(ex["stay"])))
        return 0

    header = ["relink_bluebook — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "rows of the Blue Book table: %d; tied to an entry now: %d (%s)" % (
                  len(rows), sum(1 for r in rows if r["entry_id"]),
                  ", ".join("%s %d" % (k, v) for k, v in by_type.most_common() if k and k != "none")),
              "ties kept: %d (by the form and a shared word, the same word listed twice, or one of the %d looked at "
              "one by one)" % (len(kept), len(REVIEWED)),
              "ties judged again: %d; tied to the entry their form is: %d; left without a tie: %d" % (
                  len(changes), len(retied), len(untied)),
              "Blue Book sentences stored as examples: %d sentences in %d rows; rows to remove: %d, to add: %d, "
              "staying: %d; sentences with no listed word tied to an entry: %d" % (
                  ex["sentences"], len(ex["remove"]) + len(ex["stay"]), len(ex["remove"]), len(ex["add"]),
                  len(ex["stay"]), len(ex["sentences_without_a_tied_word"])),
              "blue_book_attested: %d entries lose the flag, %d gain it" % (
                  sum(1 for f in flags if f[3] == 0), sum(1 for f in flags if f[3] == 1))]
    body = ["", "== 1. Rows tied to the entry their form is (row, lesson, form, English: was -> now)"]
    body += ["  %-5d L%-2s %-28s %-34s %s -> %s  [%s]" % (c["id"], c["lesson"], c["form"][:28], c["english"][:34], c["was"],
                                                       c["now"], c["match_type"]) for c in retied]
    body += ["", "== 2. Rows left without a tie (row, lesson, kind, form, English: was; why)"]
    body += ["  %-5d L%-2s %-9s %-30s %-30s was %s; %s" % (c["id"], c["lesson"], (c["context"] or "")[:9], c["form"][:30],
                                                         c["english"][:30], c["was"], c["why"]) for c in untied]
    body += ["", "== 3. Blue Book sentences as examples: removed from (entry: sentence)"]
    body += ["  %-14s %s" % (entries[e["entry_id"]]["headword"], e["skiri_text"]) for e in ex["remove"]] or ["  none"]
    body += ["", "== 3b. ... and placed under (entry: sentence)"]
    body += ["  %-14s %s" % (entries[w[0]]["headword"], w[1]) for w in ex["add"]] or ["  none"]
    body += ["", "== 3c. Sentences that are an example of no entry now (they stay in the lessons)"]
    body += ["  " + t for t in ex["sentences_without_a_tied_word"]] or ["  none"]
    body += ["", "== 4. blue_book_attested (entry: was -> now)"]
    body += ["  %-22s %d -> %d" % (f[1], f[2], f[3]) for f in sorted(flags, key=lambda f: (f[3], f[1]))] or ["  none"]

    if not args.apply:
        out("\n".join(header))
        for title, chunk in (("== 1. first rows", body[2:22]), ("== 2. first rows", [l for l in body if " was " in l][:14])):
            out(title)
            out("\n".join(chunk))
        out("== 3b. placed under")
        out("\n".join(["  %-14s %s" % (entries[w[0]]["headword"], w[1]) for w in ex["add"]][:30]))
        out("== 4. flags")
        out("  lose: " + ", ".join(f[1] for f in flags if f[3] == 0))
        out("  gain: " + ", ".join(f[1] for f in flags if f[3] == 1))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("skiri_pawnee_backup_%s_bluebook_relink.db" % stamp)
    shutil.copy2(DB, backup)
    conn = sqlite3.connect(str(DB))
    for c in changes:
        if c["entry_id"]:
            note = "tied by the form and a shared meaning by relink_bluebook.py %s (was tied to %s: %s)" % (
                TODAY, c["was"], c["was_type"]) if c["match_type"] == "orthographic" else \
                "tied by relink_bluebook.py %s: the same form is tied by its meaning elsewhere (was tied to %s: %s)" % (
                    TODAY, c["was"], c["was_type"])
            conn.execute("update blue_book_attestations set entry_id = ?, match_type = ?, match_confidence = ?, notes = ? "
                         "where id = ?", (c["entry_id"], c["match_type"], 0.85 if c["match_type"] == "orthographic" else 0.8,
                                          note, c["id"]))
        else:
            conn.execute("update blue_book_attestations set entry_id = NULL, match_type = 'none', match_confidence = 0.0, "
                         "notes = ? where id = ?",
                         ("the tie to %s (%s) was removed by relink_bluebook.py %s: %s" % (
                             c["was"], c["was_type"], TODAY, c["why"]), c["id"]))
    conn.executemany("delete from examples where id = ?", [(e["id"],) for e in ex["remove"]])
    conn.executemany("insert into examples (entry_id, skiri_text, english_translation, usage_context, source) "
                     "values (?, ?, ?, ?, 'blue_book')", ex["add"])
    conn.executemany("update lexical_entries set blue_book_attested = ? where entry_id = ?", [(f[3], f[0]) for f in flags])
    conn.commit()
    conn.close()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False,
                   stdout=subprocess.DEVNULL)
    header += ["", "written. backup: OneDrive/pari_pakuru_backups/%s" % backup.name]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
