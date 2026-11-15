#!/usr/bin/env python3
"""Stage 2 of the engines review: the test sets, made from attested forms only.

    python scripts/engines_review/build_test_sets.py            # build, write the manifest
    python scripts/engines_review/build_test_sets.py --verify   # build again in memory, compare hashes

Every set is a plain copy of forms that a source prints. Nothing here is
produced by an engine, and no set is chosen by looking at what an engine gets
right. The sets go to reports/engines_review/data/testsets/ with a manifest
that records, for each, where it comes from, how many items it has and the
SHA-256 of the file.

The sets

  appendix1            Parks, Appendix 1: 7 verbs x 10 modes x 11 persons (770 cells),
                       from extracted_data/appendix1_conjugations.json as corrected 2026-11-13.
                       SEEN: the conjugation engine and the person rules were fitted to these.
  dictionary_forms     The five verb forms Parks prints in the dictionary entries
                       (table paradigmatic_forms). UNSEEN by the conjugation engine and by
                       the person rules; SEEN by the form 2 predictor (form 2 only).
  chapter3_examples    The examples Parks gives with his 24 sound changes (underlying pieces
                       and the surface form), from the catalogue that is also in the table
                       sound_change_rules. Partly SEEN by the sound-change engine (its 11 tests).
  chapter4_examples    Parks's worked examples in chapter 4, each a word with his own division
                       into pieces. Taken from the locked gold file of the word-construction
                       analysis (curriculum/roots_v2/gold/g1_go_examples.json), which was made
                       again from the corrected chapter on 2026-11-14. UNSEEN by every engine.
  noun_suffix_words    Dictionary words whose printed etymology ends in + hiriʔ, + kat or + ru:
                       the stem as Parks writes it, and the word it gives.
  noun_etymologies     Every noun with a printed etymology: its last piece, to compare with the
                       suffix the possession engine strips.
  noun_case_examples   The locative and instrumental forms Parks prints as examples under noun
                       entries ("siiskat  on the awl", "tahuuhiriʔ  with the flint"): one-word
                       examples ending in -kat, -(h)iriʔ or -ru, with his translation.
                       UNSEEN by the possession engine.
  kinship_appendix3    The kin terms of Appendix 3 with "my / your / his".
  blue_book_possession The possession forms the Blue Book prints (lessons 5 and 7), from
                       blue_book_attestations as read from the scan.
  blue_book_sentences  Every Blue Book dialogue line, phrase and grammar example, as printed.

Reads only.
"""
import argparse
import re

from common import (DATA, EXTRACTED, GOLD, ROOT, TESTSETS, clean, connect, load_json, out, variants, write_json,
                    write_jsonl)

APPENDIX1_VERBS = {  # the engine's own setting for each verb (scripts/morpheme_inventory.py, APPENDIX1_VERBS)
    "page_2": "to come", "page_3": "to do it", "page_4": "to go", "page_5": "to be good",
    "page_6": "to drink it", "page_7": "to be sick", "page_8": "to have it",
}
PERSONS = ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du", "1pl_incl", "1pl_excl", "2pl", "3pl"]


def appendix1():
    data = load_json(EXTRACTED / "appendix1_conjugations.json")
    rows = []
    for page, verb in APPENDIX1_VERBS.items():
        for mode, cells in data[page]["modes"].items():
            for pn in PERSONS:
                printed = cells[pn]["skiri"]
                rows.append({"page": page, "verb": verb, "mode": mode, "person": pn,
                             "printed": printed, "variants": variants(printed)})
    return rows


def dictionary_forms(conn):
    rows = []
    for r in conn.execute("""
            select pf.entry_id, le.headword, le.grammatical_class, le.verb_class, le.stem_preverb,
                   pf.form_number, pf.skiri_form
            from paradigmatic_forms pf join lexical_entries le using(entry_id)
            where pf.skiri_form is not null and pf.skiri_form != ''
            order by pf.entry_id, pf.form_number"""):
        rows.append({"entry_id": r["entry_id"], "headword": r["headword"],
                     "grammatical_class": r["grammatical_class"], "verb_class": r["verb_class"],
                     "stem_preverb": r["stem_preverb"], "form_number": r["form_number"],
                     "printed": r["skiri_form"], "variants": variants(r["skiri_form"])})
    return rows


def _pieces(underlying):
    """'ti- + uur- + hiir' -> ['ti', 'uur', 'hiir']; zero morphemes are left out."""
    out_ = []
    for part in underlying.split("+"):
        p = part.strip().strip("-").strip()
        if not p or p in ("NULL", "Ø"):
            continue
        out_.append(p)
    return out_


# The four of Parks's examples that were also among the 11 forms of the sound-change file's own test, as that
# test stood when the review measured it (commit 814e8cc). The test was removed on 2026-11-14 (decision 4),
# so the four are written down here; the test set stays what it was.
OWN_TESTS_AT_REVIEW = {("hak + his", "haks"), ("kuhkus", "kuhku"),
                       ("pahaat + raʔuk", "pahaahaʔuk"), ("ta + t + taʔuut", "tactaʔuut")}


def chapter3_examples():
    import sound_changes as sc
    tested = OWN_TESTS_AT_REVIEW
    rows = []
    for rule in sc.RULES:
        for ex in rule["examples"]:
            if not ex.get("surface"):
                continue          # rule 24 gives a pronunciation, not a spelling
            pieces = _pieces(ex["underlying"])
            rows.append({"rule": rule["rule_id"], "rule_name": rule["name"], "underlying": ex["underlying"],
                         "pieces": pieces, "surface": ex["surface"], "gloss": ex.get("gloss"),
                         "has_length_mark": any(":" in p for p in pieces),
                         "is_one_of_the_engines_own_tests": (" + ".join(pieces), ex["surface"]) in tested})
    return rows


def chapter4_examples():
    gold = load_json(GOLD / "g1_go_examples.json")
    rows = []
    for e in gold["examples"]:
        pieces = []
        for pc in e["pieces"]:
            f = pc["form"].strip()
            if f.strip("-") in ("Ø", ""):
                continue
            pieces.append(f.strip("-"))
        rows.append({"page": e["go_page"], "surface": e["surface"], "translation": e["translation"],
                     "analysis": e["analysis_text"], "pieces": pieces,
                     "labels": [pc.get("label") for pc in e["pieces"]],
                     "flags": e["flags"],
                     "has_length_mark": any(":" in p for p in pieces),
                     "plain_pieces": all(re.fullmatch(r"[a-zʔ:]+", p) for p in pieces)})
    return rows


def _etymology_pieces(raw):
    """'<ari.kiis+hiriʔ, ari + bone + LOC>' -> ['ari.kiis', 'hiriʔ']"""
    raw = (raw or "").strip().lstrip("<").rstrip(">").strip()
    first = raw.split(",")[0]
    return [p.strip().lstrip("-") for p in first.split("+") if p.strip()]


def noun_suffix_words(conn):
    rows = []
    for r in conn.execute("""select le.entry_id, le.headword, le.grammatical_class, e.raw_etymology
                             from lexical_entries le join etymology e using(entry_id) order by le.entry_id"""):
        pieces = _etymology_pieces(r["raw_etymology"])
        if len(pieces) < 2 or pieces[-1] not in ("hiriʔ", "kat", "ru"):
            continue
        if not all(re.fullmatch(r"[a-zʔ.]+", p) for p in pieces):
            continue
        rows.append({"entry_id": r["entry_id"], "headword": r["headword"], "words": variants(r["headword"]),
                     "grammatical_class": r["grammatical_class"], "etymology": r["raw_etymology"],
                     "stem_pieces": [p for p in pieces[:-1]], "suffix": pieces[-1]})
    return rows


def noun_etymologies(conn):
    rows = []
    for r in conn.execute("""select le.entry_id, le.headword, le.grammatical_class, e.raw_etymology
                             from lexical_entries le join etymology e using(entry_id)
                             where le.grammatical_class in ('N','N-DEP','N-KIN','NUM') order by le.entry_id"""):
        pieces = _etymology_pieces(r["raw_etymology"])
        if not pieces or not all(re.fullmatch(r"[a-zʔ.]+", p) for p in pieces):
            continue                      # a cognate note, a loan, or no analysis into pieces
        rows.append({"entry_id": r["entry_id"], "headword": r["headword"],
                     "grammatical_class": r["grammatical_class"], "etymology": r["raw_etymology"],
                     "pieces": pieces, "last_piece": pieces[-1]})
    return rows


def noun_case_examples(conn):
    rows = []
    for r in conn.execute("""select e.id, e.entry_id, le.headword, le.grammatical_class, e.skiri_text, e.english_translation
                             from examples e join lexical_entries le using(entry_id)
                             where le.grammatical_class in ('N','N-DEP','N-KIN','NUM')
                               and e.source = 'parks_dictionary' and e.skiri_text is not null
                             order by e.id"""):
        words = [w.strip().rstrip(".") for w in re.split(r"[,;]\s*", r["skiri_text"].strip()) if w.strip()]
        for w in words:
            if " " in w:
                continue
            m = re.search(r"(sukat|kat|hiriʔ|iriʔ|wiru|ru)$", w)
            if not m or len(w) < 5:
                continue
            ending = m.group(1)
            english = (r["english_translation"] or "").strip()
            first = english.lower().split(" ")[0].strip("(") if english else ""
            rows.append({"example_id": r["id"], "entry_id": r["entry_id"], "headword": r["headword"],
                         "grammatical_class": r["grammatical_class"], "printed": w, "ending": ending,
                         "translation": english,
                         "suffix": "kat" if ending.endswith("kat") else ("ru" if ending.endswith("ru") else "hiriʔ"),
                         "translation_begins": first,
                         "several_forms_in_the_example": len(words) > 1})
    return rows


def kinship_appendix3():
    data = load_json(EXTRACTED / "appendix3_kinship.json")
    rows = []

    def add(term, category=None):
        pf = term.get("possessive_forms")
        if not pf:
            return
        rows.append({"english": term.get("english_term"), "stem": term.get("skiri_term"), "category": category,
                     "my": pf.get("my"), "your": pf.get("your"), "his_her": pf.get("his_her")})

    for item in data.get("terms", []):
        if "category" in item and "terms" in item:
            for sub in item["terms"]:
                add(sub, item["category"])
        else:
            add(item)
    return rows


def blue_book_possession(conn):
    rows = []
    for r in conn.execute("""select id, bb_skiri_form, bb_english, context_type, lesson_number, page_number
                             from blue_book_attestations
                             where lesson_number in (5, 7) and bb_skiri_form is not null order by id"""):
        eng = (r["bb_english"] or "").lower()
        kind = None
        if re.search(r"\b(my|your|his|her)\b", eng) and "hat" in eng:
            kind = "any other noun"
        elif eng.startswith("here is") or eng.startswith("where is your"):
            kind = "body part"
        elif r["context_type"] in ("BASIC_WORDS", "ADDITIONAL_WORDS") and re.match(r"(my|your|his|her) ", eng):
            kind = "kinship"
        if kind:
            rows.append({"id": r["id"], "kind": kind, "printed": r["bb_skiri_form"], "english": r["bb_english"],
                         "lesson": r["lesson_number"], "pdf_page": r["page_number"],
                         "book_page": (r["page_number"] - 28) if r["page_number"] else None})
    return rows


def blue_book_sentences(conn):
    rows = []
    seen = set()
    for r in conn.execute("""select id, bb_skiri_form, bb_english, context_type, lesson_number, page_number
                             from blue_book_attestations
                             where context_type in ('DIALOGUE','PHRASE','GRAMMAR_EXAMPLE')
                               and bb_skiri_form is not null and bb_skiri_form != '' order by id"""):
        key = r["bb_skiri_form"]
        if key in seen:
            continue
        seen.add(key)
        rows.append({"id": r["id"], "printed": key, "english": r["bb_english"], "context": r["context_type"],
                     "lesson": r["lesson_number"], "pdf_page": r["page_number"]})
    return rows


SETS = [
    ("appendix1", "Parks, Appendix 1, as corrected from the page: extracted_data/appendix1_conjugations.json",
     "seen: the conjugation engine, the accent rules and the person rules were fitted to these"),
    ("dictionary_forms", "the five verb forms of the dictionary entries: table paradigmatic_forms",
     "unseen by the conjugation engine and the person rules; form 2 seen by the form 2 predictor"),
    ("chapter3_examples", "Parks's examples to his 24 sound changes: the catalogue in scripts/sound_changes.py (= table sound_change_rules)",
     "four are among the sound-change engine's own tests; the rest it was never run on"),
    ("chapter4_examples", "Parks's worked examples in chapter 4: curriculum/roots_v2/gold/g1_go_examples.json (locked by hash)",
     "unseen by every engine"),
    ("noun_suffix_words", "dictionary words whose printed etymology ends in + hiriʔ, + kat or + ru: tables lexical_entries, etymology",
     "the 42 in + hiriʔ were used on 2026-11-13 to set the possession engine's rule for that suffix; the others unseen"),
    ("noun_etymologies", "every noun with a printed etymology made of pieces: tables lexical_entries, etymology",
     "unseen"),
    ("noun_case_examples", "one-word examples in -kat, -(h)iriʔ, -ru printed under noun entries: tables examples, lexical_entries",
     "unseen by the possession engine"),
    ("kinship_appendix3", "Parks, Appendix 3: extracted_data/appendix3_kinship.json",
     "the possession engine looks these up"),
    ("blue_book_possession", "possession forms of Blue Book lessons 5 and 7, as read from the scan: table blue_book_attestations",
     "the engine's constructions were taken from the OCR text of these lines"),
    ("blue_book_sentences", "every Blue Book dialogue line, phrase and grammar example: table blue_book_attestations",
     "the templates were taken from the OCR text of these lines"),
]


def build_all():
    conn = connect()
    made = {
        "appendix1": appendix1(),
        "dictionary_forms": dictionary_forms(conn),
        "chapter3_examples": chapter3_examples(),
        "chapter4_examples": chapter4_examples(),
        "noun_suffix_words": noun_suffix_words(conn),
        "noun_etymologies": noun_etymologies(conn),
        "noun_case_examples": noun_case_examples(conn),
        "kinship_appendix3": kinship_appendix3(),
        "blue_book_possession": blue_book_possession(conn),
        "blue_book_sentences": blue_book_sentences(conn),
    }
    conn.close()
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verify", action="store_true", help="build again and compare with the manifest; write nothing")
    args = ap.parse_args()
    made = build_all()
    if args.verify:
        import hashlib
        import json
        manifest = load_json(TESTSETS / "MANIFEST.json")
        bad = 0
        for name, _, _ in SETS:
            h = hashlib.sha256()
            for row in made[name]:
                h.update((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
            same = h.hexdigest() == manifest["sets"][name]["sha256"]
            bad += not same
            out("%-22s %5d items  %s" % (name, len(made[name]), "as recorded" if same else "DIFFERS from the manifest"))
        out("all test sets are as recorded" if not bad else "%d test set(s) differ: the sources changed since the sets were made" % bad)
        raise SystemExit(1 if bad else 0)
    manifest = {"made_by": "scripts/engines_review/build_test_sets.py", "sets": {}}
    for name, source, seen in SETS:
        digest = write_jsonl(TESTSETS / (name + ".jsonl"), made[name])
        manifest["sets"][name] = {"items": len(made[name]), "source": source, "seen_or_unseen": seen, "sha256": digest}
        out("%-22s %5d items" % (name, len(made[name])))
    write_json(TESTSETS / "MANIFEST.json", manifest)
    out("written: reports/engines_review/data/testsets/ (%d sets and MANIFEST.json)" % len(SETS))


if __name__ == "__main__":
    main()
