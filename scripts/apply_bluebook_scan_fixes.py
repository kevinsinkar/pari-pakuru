#!/usr/bin/env python3
"""
Blue Book forms corrected from the scan (2026-11-13)
====================================================

Every Blue Book form in the database was taken from the OCR text of the scan
(pari pakuru/Blue_Book_Pari_Pakuru.txt). That text has none of the accent
marks the book prints and misreads about one form in six. In the audit of
2026-11-13 each stored form with a page was cut out of the scan and read by a
reader who saw only the image (reports/source_audit_2026-11/: bluebook_graded.json
for the first 153 crops, bluebook_rest_graded.json for the other 843).

This script puts the readings into the database:

  1. blue_book_attestations.bb_skiri_form, the record of the form "as printed":
       accent only        the letters agree; the scan has an accent, an apostrophe or a raised dot
                          that the stored form lacks: the reading replaces the stored form
       OCR slip           the letters differ in a way the OCR is known to misread accented vowels
                          (ú read as ti or ii, á as d or i, í as f, É as J): the reading replaces it
       left for a person  anything else (other letters, a reader's doubt, a crop that missed the form)
  2. the copies of those forms: Blue Book rows of `examples`, the dialogue lines in `lessons`, and
     extracted_data/blue_book_extracted.json and lessons.json, wherever a copy is identical to the old form
  3. three dictionary entries whose headword was made from a misread form
       had'  -> haú'  "yes";  tsktis•kakusu' -> tskús•kakusu' "chair";  ti•kuwtitiku' -> ti•kuwútiku'
  4. the "phonetic form" of the 93 Blue Book-only entries, which is removed: the book gives none, and
     what was stored had been made up from the spelling. The spelling-based pronunciation stays.

    python scripts/apply_bluebook_scan_fixes.py            # dry run: prints what it would do, writes nothing
    python scripts/apply_bluebook_scan_fixes.py --apply    # backs up, writes, adds to the report

Blue Book spelling is kept as printed (ts, ', the raised dot •). Nothing is respelled into Parks's letters
except the three headwords, which follow the convention the 93 entries already use.
"""
import argparse
import datetime as dt
import difflib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
AUDIT = ROOT / "reports" / "source_audit_2026-11"
DB = ROOT / "skiri_pawnee.db"
REPORT = AUDIT / "bluebook_applied_report.txt"
FROZEN = ROOT / "curriculum" / "flashcard_sets.json"
EXTRACTED = [ROOT / "extracted_data" / "blue_book_extracted.json", ROOT / "extracted_data" / "lessons.json"]

MISREAD_ENTRIES = {          # entry: (form stored, form on the scan, headword now, headword in the entries' convention)
    "BB-had-0010": ("had'", "haú'", "hadʔ", "hauʔ"),
    "BB-cktiskakusu-0003": ("tsktis•kakusu'", "tskús•kakusu'", "cktiskakusuʔ", "ckuskakusuʔ"),
    "BB-tikuwtitiku-0083": ("ti•kuwtitiku'", "ti•kuwútiku'", "tikuwtitikuʔ", "tikuwutikuʔ"),
}


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def clean(reading):
    """A reader's transcription in the database's Blue Book conventions: • for the raised dot, ' for the glottal stop."""
    s = unicodedata.normalize("NFC", reading or "").replace("·", "•").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


def plain(s):
    s = "".join(ch for ch in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9?]", "", s)


def ocr_fold(s):
    """Letters with the OCR's known misreadings of accented vowels folded together."""
    s = plain(s).replace("f", "i").replace("d", "a").replace("j", "e")
    return s.replace("ti", "u").replace("ii", "u")


def decide(stored, reading):
    """(new form or None, kind)."""
    read = clean(reading)
    if "[?]" in read:
        return None, "reader unsure"
    if read == clean(stored):
        return None, "same"
    ps, pr = plain(stored), plain(read)
    if difflib.SequenceMatcher(None, ps, pr, autojunk=False).ratio() < 0.6:
        return None, "crop shows something else"
    if ps == pr:
        if any(a.isupper() != b.isupper() for a, b in zip(re.sub(r"[^A-Za-z]", "", unicodedata.normalize("NFD", stored)),
                                                          re.sub(r"[^A-Za-z]", "", unicodedata.normalize("NFD", read)))):
            return None, "capitals differ"
        has_mark = any(unicodedata.combining(ch) for ch in unicodedata.normalize("NFD", read))
        return read, "accent restored" if has_mark else "apostrophe, dot or space"
    if ocr_fold(stored) == ocr_fold(read) and any(unicodedata.combining(ch) for ch in unicodedata.normalize("NFD", read)):
        return read, "OCR slip corrected"
    return None, "letters differ"


def same_place(stored, read):
    """Two readers agree on what stands over the red line. Is that the stored row's own form?

    The line was placed where the OCR text matched the stored form. A short stored form can match
    inside a longer printed word ("rakis" inside "tirakis"), and then the readers read a neighbour,
    not the row's form. So the reading is taken only when it is no longer or shorter than the stored
    form by more than two letters, neither contains the other, and both begin and end alike (capital
    or small letter; the same final stop). Anything else stays open.
    """
    a, b = ocr_fold(stored), ocr_fold(read)
    if not a or not b or abs(len(plain(stored)) - len(plain(read))) > 2:
        return False
    if a != b and (a in b or b in a):
        return False
    first = lambda s: next((ch for ch in s if ch.isalpha()), "")
    if first(stored).isupper() != first(read).isupper():
        return False
    last = lambda s: s.strip()[-1] if s.strip() and s.strip()[-1] in ".?!" else ""
    return last(stored) == last(read)


def replace_strings(node, mapping):
    """Replace string values that are exactly a key of mapping; returns the number replaced."""
    n = 0
    items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else ()
    for k, v in list(items):
        if isinstance(v, str):
            if v in mapping:
                node[k] = mapping[v]
                n += 1
        else:
            n += replace_strings(v, mapping)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = ap.parse_args()
    conn = sqlite3.connect("file:%s?mode=ro" % DB.resolve().as_posix(), uri=True)
    log, kinds, left, confirmed = [], Counter(), [], []
    updates = []                                    # (attestation id, old, new)

    # ---- 1. the readings ----
    groups = []
    rest = json.loads((AUDIT / "bluebook_rest_graded.json").read_text(encoding="utf-8"))["rows"]
    for r in rest:
        groups.append((r["attestation_ids"], r["stored_form"], r["read"], r["page"], r["crop"]))
    first = json.loads((AUDIT / "bluebook_graded.json").read_text(encoding="utf-8"))["rows"]
    for r in first:
        if r.get("stored_form_is", "").startswith("the headword"):
            continue                                 # a respelled headword, not a stored form
        if r.get("attestation_id"):
            ids = [r["attestation_id"]]
        else:
            ids = [x[0] for x in conn.execute("select id from blue_book_attestations where entry_id=? and bb_skiri_form=?",
                                              (r.get("entry_id"), r["stored_form"]))]
        groups.append((ids, r["stored_form"], r["read"], r["page"], r["crop"]))
    # the second reading of the forms the first one left open (scripts/source_audit/bluebook_second_look.py --grade)
    second = {}
    second_file = AUDIT / "bluebook_second_look.json"
    if second_file.exists():
        for r in json.loads(second_file.read_text(encoding="utf-8"))["rows"]:
            second[(r["page"], r["first_crop"])] = r
    for ids, stored, reading, page, crop in groups:
        new, kind = decide(stored, reading)
        if new is None and kind != "same":
            two = second.get((page, crop))
            if two and two["verdict"] == "two readings agree" and two.get("pawnee", True) and same_place(stored, two["second_reading"]):
                new, kind = clean(two["second_reading"]), "two readings agree"
            elif two and two["verdict"] == "two readings agree":
                kind += "; both readers read %s, which is %s" % (
                    clean(two["second_reading"]), "English" if not two.get("pawnee", True) else "a longer or another word at that place")
            elif two and two["verdict"] == "second reading agrees with the stored form":
                kind = "same"                         # the first reader slipped; the stored form stands
                confirmed.append("p. %-4s %-5s stored %r; the first reader saw %r, the second read the stored form" % (
                    page, crop, stored, clean(reading)))
            elif two:
                kind += "; second reading: %s" % clean(two["second_reading"])
        kinds[kind.split(";")[0]] += 1
        if new is None:
            if kind not in ("same",):
                left.append("p. %-4s %-5s %-26s stored %r; the reader saw %r" % (page, crop, kind, stored, clean(reading)))
            continue
        for rid in ids:
            row = conn.execute("select bb_skiri_form from blue_book_attestations where id=?", (rid,)).fetchone()
            # every row of the group holds the same letters; rows may differ from one another in spacing
            if row and plain(row[0]) == plain(stored) and row[0] != new:
                updates.append((rid, row[0], new))
        if not ids and kind == "two readings agree":
            for rid, form in conn.execute("select id, bb_skiri_form from blue_book_attestations where page_number=? and bb_skiri_form=?", (page, stored)):
                updates.append((rid, form, new))
        log.append("  p. %-4s %-22s %s -> %s" % (page, kind, stored, new))
    mapping = {}
    for rid, old, new in updates:
        mapping.setdefault(old, new)

    # Every stored form with its corrected reading, including those corrected by an earlier run: the
    # attestation rows no longer hold the old form, but copies of it elsewhere may.
    for ids, stored, reading, page, crop in groups:
        new, kind = decide(stored, reading)
        if new is None:
            two = second.get((page, crop))
            if two and two["verdict"] == "two readings agree" and two.get("pawnee", True) and same_place(stored, two["second_reading"]):
                new = clean(two["second_reading"])
        if new and new != stored:
            mapping.setdefault(stored, new)
    for r in rest:
        new = mapping.get(r["stored_form"])
        for alt in r.get("stored_forms_all", []):
            if new and alt != new:
                mapping.setdefault(alt, new)

    # ---- 5. the same forms held in other tables (they were filled from the same OCR text) ----
    other = []                                      # (table, column, key column, key, old, new)
    for table, column, key, where in (("bb_gap_triage", "bb_skiri_form", "id", ""),
                                      ("blue_book_attestations", "bb_skiri_form", "id", ""),
                                      ("blue_book_attestations", "full_sentence_pawnee", "id", ""),
                                      ("bb_function_words", "source_phrase", "id", ""),
                                      ("function_words", "headword", "id", " where source in ('blue_book', 'blue_book_phrase')")):
        for k, v in conn.execute("select %s, %s from %s%s" % (key, column, table, where)).fetchall():
            if v in mapping and mapping[v] != v:
                other.append((table, column, key, k, v, mapping[v]))
    done = {u[0] for u in updates}
    other = [o for o in other if not (o[0] == "blue_book_attestations" and o[1] == "bb_skiri_form" and o[3] in done)]
    # one word taken out of a phrase: it follows the word at the same place in the corrected phrase
    phrase_now = {k: new for table, column, key, k, old, new in other if table == "bb_function_words"}
    for k, word, phrase in conn.execute("select id, word, source_phrase from bb_function_words").fetchall():
        old_phrase = phrase
        new_phrase = phrase_now.get(k) or mapping.get(phrase)
        if not new_phrase or not word:
            continue
        a, b = old_phrase.split(), new_phrase.split()
        if len(a) != len(b):
            continue
        strip = lambda t: t.strip(".,?!")
        for x, y in zip(a, b):
            if strip(x) == word and strip(y) != word and plain(strip(y)) == plain(word):
                other.append(("bb_function_words", "word", "id", k, word, strip(y)))
                break

    ex_rows = [(i, t) for i, t in conn.execute("select id, skiri_text from examples where source='blue_book'") if t in mapping]
    lessons = []
    for num, dialogues, notes in conn.execute("select lesson_number, dialogues, grammar_notes from lessons"):
        d = json.loads(dialogues) if dialogues else None
        n = replace_strings(d, mapping) if d is not None else 0
        if n:
            lessons.append((num, json.dumps(d, ensure_ascii=False), n))

    # ---- 3 and 4. the Blue Book-only entries ----
    entry_changes = []
    from build_root_curriculum import respell_orthography
    for entry_id, (old_form, new_form, old_head, new_head) in MISREAD_ENTRIES.items():
        row = conn.execute("select headword from lexical_entries where entry_id=?", (entry_id,)).fetchone()
        if row and row[0] == old_head:
            resp = respell_orthography(re.sub(r"[?!+]", "", new_head).replace(".", "-")).replace("--", "-")
            entry_changes.append((entry_id, old_head, new_head, resp, old_form, new_form))
    synthetic = conn.execute("select count(*) from lexical_entries where source='blue_book' and phonetic_form is not null").fetchone()[0]

    header = ["apply_bluebook_scan_fixes — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "distinct forms read from the scan: %d   %s" % (len(groups), dict(kinds)),
              "attestation rows to correct: %d; Blue Book example rows: %d; lessons with corrected dialogue lines: %d (%d lines)" % (
                  len(updates), len(ex_rows), len(lessons), sum(l[2] for l in lessons)),
              "entries whose headword was made from a misread form: %d; made-up phonetic forms to remove from Blue Book-only entries: %d" % (
                  len(entry_changes), synthetic),
              "the same forms in other tables: %d values; stored forms confirmed by the second reading: %d; left for a person: %d" % (
                  len(other), len(confirmed), len(left))]
    body = ["", "== 1. Forms corrected (%d distinct)" % len(log)] + sorted(log)
    body += ["", "== 3. Entries"] + ["  %s: headword %s -> %s; pronunciation from the spelling %s; printed form %s -> %s" % c for c in entry_changes]
    body += ["", "== 5. The same forms in other tables (%d values)" % len(other)]
    body += ["  %-34s %d" % ("%s.%s" % k, n) for k, n in sorted(Counter((o[0], o[1]) for o in other).items())]
    body += ["  %s.%s  %s -> %s" % (o[0], o[1], o[4], o[5]) for o in other]
    body += ["", "== Stored form confirmed by the second reading (%d)" % len(confirmed)] + ["  " + x for x in sorted(confirmed)]
    body += ["", "== Left for a person (%d)" % len(left)] + ["  " + x for x in sorted(left)]
    if not args.apply:
        out("\n".join(header))
        out("\n".join(body[:24]))
        out("  ...")
        at = next(i for i, line in enumerate(body) if line.startswith("== 5."))
        out("\n".join(body[at:at + 22]))
        out("  ...")
        out("\n".join(body[-34:]))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return
    conn.close()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s.db" % stamp))
    conn = sqlite3.connect(str(DB))
    conn.executemany("update blue_book_attestations set bb_skiri_form=? where id=?", [(new, rid) for rid, old, new in updates])
    conn.executemany("update examples set skiri_text=? where id=?", [(mapping[t], i) for i, t in ex_rows])
    for table, column, key, k, old, new in other:
        conn.execute("update %s set %s=? where %s=? and %s=?" % (table, column, key, column), (new, k, old))
    conn.executemany("update lessons set dialogues=? where lesson_number=?", [(d, num) for num, d, n in lessons])
    for entry_id, old_head, new_head, resp, old_form, new_form in entry_changes:
        conn.execute("update lexical_entries set headword=?, simplified_pronunciation=? where entry_id=?", (new_head, resp, entry_id))
        conn.execute("update blue_book_attestations set bb_skiri_form=? where entry_id=? and bb_skiri_form=?", (new_form, entry_id, old_form))
    conn.execute("update lexical_entries set phonetic_form=NULL where source='blue_book'")
    conn.commit()
    conn.close()
    n_json = 0
    for path in EXTRACTED:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        n = replace_strings(data, mapping)
        if n:
            indent = 2 if raw.startswith(("{\n  ", "[\n  ")) else 1 if raw.startswith(("{\n ", "[\n ")) else None
            path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
            n_json += n
    sets = json.loads(FROZEN.read_text(encoding="utf-8"))
    heads = {c[0]: c for c in entry_changes}
    n_cards = 0
    for wk in sets["weeks"]:
        for card in wk["cards"]:
            if card.get("source") == "blue_book" or str(card["entry_id"]).startswith("BB-"):
                if card.get("phonetic_form") is not None:
                    card["phonetic_form"] = None
                    n_cards += 1
                if card["entry_id"] in heads:
                    card["headword"] = heads[card["entry_id"]][2]
                    card["simplified_pronunciation"] = heads[card["entry_id"]][3]
    FROZEN.write_text(json.dumps(sets, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False, stdout=subprocess.DEVNULL)
    header += ["", "written: %d attestation rows, %d example rows, %d lessons, %d strings in extracted_data, %d flashcards cleared of a made-up phonetic form"
               % (len(updates), len(ex_rows), len(lessons), n_json, n_cards), "backups: OneDrive/pari_pakuru_backups (stamp %s)" % stamp]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
