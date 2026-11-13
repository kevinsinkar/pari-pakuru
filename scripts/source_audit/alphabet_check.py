#!/usr/bin/env python3
"""
Stage 4b: does every stored Skiri form use only Skiri letters?
==============================================================

Skiri is written with a i u p t k c s w r h ʔ (and č in phonetic forms; n in a
few words). A form with a b, d, f, g, l, m, o ... in it was misread or is not
Skiri. This needs no page image, and it would have caught -biriʔ, the misread
-hiriʔ that an engine was built on.

    python scripts/source_audit/alphabet_check.py     # writes alphabet_check.json

Two kinds of field are scanned:
  form fields   hold nothing but Skiri forms: every word in them is tested
  mixed text    English with Skiri words in it (the grammar chapter as extracted): only words
                that look Skiri (a glottal stop, or a doubled a, i or u) are tested
"""
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

SKIRI = set("aiuptkcswrhʔčn") | set("áíúàìùəɪʊ") | {"́", "̀"}
NOTATION = set("-+/()[]{}.,;:~*=<>→#Ø∅ ?!'’\"_|0123456789")
FOREIGN = re.compile(r"[bdfgjlmoqvxyze]", re.I)
WORD = re.compile(r"[^\s,;()\[\]{}<>/+=→\"“”]+")

# (table, columns that hold only Skiri forms)
FORM_COLUMNS = [
    ("verb_paradigms", ["skiri_form", "dictionary_form"]),
    ("irregular_verb_roots", ["headword", "singular_stem", "dual_stem", "plural_stem"]),
    ("kinship_paradigms", ["stem", "form_1sg", "form_2sg", "form_3sg", "vocative"]),
    ("noun_stems", ["headword", "stem", "suffix"]),
    ("morpheme_inventory", ["morpheme_form"]),
    ("morpheme_abbreviations", ["morpheme_form"]),
    ("possession_examples", ["headword", "expected_form"]),
    ("paradigmatic_forms", ["skiri_form"]),
    ("lexical_entries", ["headword"]),
]
# keys in the JSON extractions whose values are Skiri forms
FORM_KEYS = re.compile(r"(skiri|stem|form|morpheme|root|my$|your$|his_her$|vocative|headword|term$)", re.I)
ENGLISH_KEYS = re.compile(r"(english|gloss|meaning|notes?$|label|description|translation|heading|content|type|class|caption|title)", re.I)


def looks_skiri(word):
    return "ʔ" in word or re.search(r"aa|ii|uu", word) is not None


def bad_letters(word):
    return sorted(set(FOREIGN.findall(word)))


def scan_value(value, strict):
    """Yield (word, letters) for words that hold a letter Skiri does not have."""
    for m in WORD.finditer(str(value)):
        word = m.group(0).strip(".'’-")
        if not word or not any(ch.isalpha() for ch in word):
            continue
        if not strict and not looks_skiri(word):
            continue
        letters = bad_letters(word)
        if letters:
            yield word, letters


def walk(node, path, out, source):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], out, source)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + [str(i)], out, source)
    elif isinstance(node, str):
        key = next((p for p in reversed(path) if not p.isdigit()), "")
        strict = bool(FORM_KEYS.search(key)) and not ENGLISH_KEYS.search(key)
        for word, letters in scan_value(node, strict):
            out.append({"source": source, "where": "/".join(path), "word": word, "letters": letters,
                        "field_kind": "form" if strict else "mixed", "value": node[:160]})


def main():
    findings = []
    conn = sqlite3.connect("file:%s?mode=ro" % (state.ROOT / "skiri_pawnee.db").resolve().as_posix(), uri=True)
    checked = collections.Counter()
    for table, cols in FORM_COLUMNS:
        where = " where coalesce(source,'') != 'blue_book'" if table == "lexical_entries" else ""
        for row in conn.execute('select rowid, %s from "%s"%s' % (", ".join('"%s"' % c for c in cols), table, where)):
            for col, value in zip(cols, row[1:]):
                if value is None:
                    continue
                checked[table] += 1
                for word, letters in scan_value(value, True):
                    findings.append({"source": "db:" + table, "where": "%s rowid %s" % (col, row[0]), "word": word,
                                     "letters": letters, "field_kind": "form", "value": str(value)[:160]})
    for name in ("appendix1_conjugations.json", "appendix2_irregular_roots.json", "appendix3_kinship.json",
                 "abbreviations.json", "grammatical_overview.json"):
        data = json.loads((state.ROOT / "extracted_data" / name).read_text(encoding="utf-8"))
        before = len(findings)
        walk(data, [], findings, "extracted_data/" + name)
        checked[name] = len(findings) - before
    # sound_change_rules keeps its examples as text
    for row in conn.execute("select rule_id, formal, examples from sound_change_rules"):
        for col, value in (("formal", row[1]), ("examples", row[2])):
            for word, letters in scan_value(value or "", False):
                findings.append({"source": "db:sound_change_rules", "where": "%s rule %s" % (col, row[0]), "word": word,
                                 "letters": letters, "field_kind": "mixed", "value": str(value)[:160]})
    by = collections.Counter((f["source"], f["field_kind"]) for f in findings)
    (state.OUT / "alphabet_check.json").write_text(json.dumps(
        {"skiri_letters": "a i u p t k c s w r h ʔ (č ə ɪ ʊ and accents in phonetic forms; n in a few words)",
         "findings": findings}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("values tested in the database: %s" % dict((k, v) for k, v in checked.items() if not k.endswith(".json")))
    state.out("words with a letter Skiri does not have: %d" % len(findings))
    for (source, kind), n in sorted(by.items()):
        state.out("  %-44s %-6s %d" % (source, kind, n))
    seen = collections.Counter((f["source"], f["word"]) for f in findings)
    for (source, word), n in seen.most_common(70):
        state.out("     %-40s %-28s x%d" % (source[-40:], word, n))


if __name__ == "__main__":
    main()
