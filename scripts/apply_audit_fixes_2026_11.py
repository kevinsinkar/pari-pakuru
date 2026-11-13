#!/usr/bin/env python3
"""
Fixes from the source-fidelity audit, applied 2026-11-13
========================================================

The audit (reports/source_audit_2026-11/) proposed 2,250 fixes and applied
none. On 2026-11-13 the user asked for them to be reviewed and applied. This
script applies the ones that passed review: those where the page evidence is a
confirmed reading or follows mechanically from the verified text layer, and
where the value to store is not in doubt. The report lists every change, old
value and new, and what was left for a person.

    python scripts/apply_audit_fixes_2026_11.py            # dry run: prints what it would do, writes nothing
    python scripts/apply_audit_fixes_2026_11.py --apply    # backs up, then writes database, JSON, extracted_data and the report

Sections:
   1. Appendix 1: 152 verb forms (each confirmed by a third look at the page)
   2. Appendix 2: burii-waa, burii -> hurii-waa, hurii
   3. Appendix 3: four kin term forms; the five rows missing from the JSON
   4. Abbreviations: three values
   5. Grammar chapter extraction: 34 words with b for h
   6. Sound-change rules: six example forms
   7. Dictionary verb forms
   8. Stand-in characters in words cited from other languages (cognates, etymologies)
   9. Combining forms with a space or a line-break hyphen in them
  10. Headwords: letter-spaced preverbs, a space inside a word, bracket notes
  11. The column an entry is printed in
  12. The printed entry the database lacked; the stored entry that is not in the book

NOT done here: the phonetic forms (scripts/restore_parks_ipa.py does all of
them from the text layer), English wording, printed examples and derived stems
the database lacks, the English-to-Skiri section, the Blue Book.

Every change is guarded: it is made only if the stored value is still the one
the audit saw. Run again after --apply, the script finds nothing left to do.
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
AUDIT = ROOT / "reports" / "source_audit_2026-11"
DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
EXTRACTED = ROOT / "extracted_data"
REPORT = AUDIT / "applied_fixes_report.txt"

PHANTOM = "SK-aakaqa-p351-3592"
# stand-in codes in citations whose printed value does not depend on context
CERTAIN_STANDINS = [("š", "ⁱ"), ("ó", "š"), ("Ý", "é"), ("Ó", "ą"), ("Ô", "ą́"), ("è", "į"), ("ü", "ž")]


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def base_field(field):
    return re.sub(r"\[.*\]", "", field)


def index_of(field):
    m = re.search(r"\[(\d+)\]", field)
    return int(m.group(1)) if m else None


class Fixer:
    def __init__(self, conn, apply):
        self.conn, self.apply = conn, apply
        self.log, self.counts, self.left = [], Counter(), []
        self.s2e = json.loads(S2E_JSON.read_text(encoding="utf-8"))
        self.by_id = {e.get("entry_id"): e for e in self.s2e}
        self.json_files = {}

    def say(self, section, text):
        self.counts[section] += 1
        self.log.append("  " + text)

    def head(self, title):
        self.log.append("")
        self.log.append("== " + title)

    def run(self, sql, params=()):
        if self.apply:
            self.conn.execute(sql, params)

    def extracted(self, name):
        if name not in self.json_files:
            self.json_files[name] = json.loads((EXTRACTED / name).read_text(encoding="utf-8"))
        return self.json_files[name]

    # ---- 1 ----
    def appendix1(self):
        self.head("1. Appendix 1: stored verb forms that differ from the page (each confirmed by a third look)")
        diffs = json.loads((AUDIT / "appendix1_differences.json").read_text(encoding="utf-8"))["differences"]
        data = self.extracted("appendix1_conjugations.json")
        for d in diffs:
            if d.get("grade") != "confirmed":
                self.left.append("Appendix 1 %s: not confirmed by a third look" % d["id"])
                continue
            row = self.conn.execute("select skiri_form, mode, person_number, source_page from verb_paradigms where id=?", (d["verb_paradigms_id"],)).fetchone()
            if not row or row[0] != d["stored"]:
                continue
            new = d["printed"]
            self.run("update verb_paradigms set skiri_form=? where id=?", (new, d["verb_paradigms_id"]))
            cell = data.get("page_%d" % row[3], {}).get("modes", {}).get(row[1], {}).get(row[2])
            note = ""
            if isinstance(cell, dict) and cell.get("skiri") == d["stored"]:
                cell["skiri"] = new
            else:
                note = "   (JSON cell not found or already different)"
            self.say("appendix 1", "book p. %s  %-36s %-9s %s -> %s%s" % (d["book_page"], d["mode"], d["person"], d["stored"], new, note))

    # ---- 2 ----
    def appendix2(self):
        self.head("2. Appendix 2: b read for h")
        data = self.extracted("appendix2_irregular_roots.json")
        for headword, old, new in (("aah", "burii-waa", "hurii-waa"), ("tir", "burii", "hurii")):
            if self.conn.execute("select 1 from irregular_verb_roots where headword=? and plural_stem=?", (headword, old)).fetchone():
                self.run("update irregular_verb_roots set plural_stem=? where headword=? and plural_stem=?", (new, headword, old))
                for row in data:
                    if row.get("headword") == headword and row.get("plural_stem") == old:
                        row["plural_stem"] = new
                self.say("appendix 2", "%s, plural stem: %s -> %s" % (headword, old, new))
        self.left.append("Appendix 2, tir 'to be together': the singular cell is empty in print; 'tir' is stored. Left as it is: the conjugation engine reads this value")

    # ---- 3 ----
    def appendix3(self):
        self.head("3. Appendix 3: kin term forms")
        data = self.extracted("appendix3_kinship.json")
        changes = [("mother", "form_2sg", "asaas", "asas"), ("grandfather", "stem", "atipaat", "atipat"),
                   ("grandfather", "form_1sg", "atipaat", "atipat"), ("grandfather", "form_2sg", "apaat", "apat"),
                   ("sister (of male)", "form_2sg", "ataati", "ataat")]
        for term, col, old, new in changes:
            if self.conn.execute('select 1 from kinship_paradigms where english_term=? and "%s"=?' % col, (term, old)).fetchone():
                self.run('update kinship_paradigms set "%s"=? where english_term=? and "%s"=?' % (col, col), (new, term, old))
                self.say("appendix 3", "kinship_paradigms, %s, %s: %s -> %s" % (term, col, old, new))
        for t in data.get("terms", []):
            for where in (t, t.get("possessive_forms") or {}):
                for k, v in list(where.items()):
                    for old, new in (("asaas", "asas"), ("atipaat", "atipat"), ("apaat", "apat")):
                        if v == old:
                            where[k] = new
                            self.say("appendix 3", "appendix3_kinship.json, %s, %s: %s -> %s" % (t.get("english_term"), k, old, new))
        # the five rows of book page 543, which the JSON lacks (two empty terms stand in their place)
        empty = [i for i, t in enumerate(data.get("terms", [])) if not t.get("english_term") and not t.get("skiri_term")]
        if empty:
            rows = self.conn.execute("select english_term, stem, form_1sg, form_2sg, form_3sg from kinship_paradigms "
                                     "where source='appendix3' and stem like '-%' order by rowid").fetchall()
            fixed = {("sister (of male)", "ataati"): "ataat"}
            new_terms = [{"english_term": r[0], "skiri_term": r[1], "grammatical_class": "N-KIN",
                          "possessive_forms": {"my": r[2], "your": fixed.get((r[0], r[3]), r[3]), "his_her": r[4], "vocative": None},
                          "verb_construction": None,
                          "notes": "Row of book page 543. Missing from the first extraction; added 2026-11-13 from the database table after a blind reading and a third look at the page."}
                         for r in rows]
            if len(new_terms) == 5:
                terms = data["terms"]
                data["terms"] = terms[:empty[0]] + new_terms + [t for i, t in enumerate(terms[empty[0]:], empty[0]) if i not in empty]
                data["total_terms"] = str(len(data["terms"]))
                self.say("appendix 3", "appendix3_kinship.json: %d empty terms replaced by the five rows of book page 543 (%s)" % (
                    len(empty), ", ".join(t["english_term"] for t in new_terms)))

    # ---- 4 ----
    def abbreviations(self):
        self.head("4. Abbreviations")
        data = self.extracted("abbreviations.json")
        for abbr, col, key, old, new in (("ABS", "meaning", "meaning", "absolutative mode prefix", "absolutive mode prefix"),
                                         ("PL", "morpheme_form", "morpheme_form", "ak-, ir-, raak-, raar-/rab-", "ak-, ir-, raak-, raar-/rah-"),
                                         ("REFL", "morpheme_form", "morpheme_form", "witii-", "witi-")):
            if self.conn.execute('select 1 from morpheme_abbreviations where abbreviation=? and "%s"=?' % col, (abbr, old)).fetchone():
                self.run('update morpheme_abbreviations set "%s"=? where abbreviation=? and "%s"=?' % (col, col), (new, abbr, old))
                self.say("abbreviations", "%s, %s: %s -> %s" % (abbr, col, old, new))
            for row in data.get("abbreviations", []):
                if row.get("abbrev") == abbr and row.get(key) == old:
                    row[key] = new

    # ---- 5 ----
    def chapter4(self):
        self.head("5. Grammar chapter extraction: b read for h")
        data = self.extracted("grammatical_overview.json")
        diffs = json.loads((AUDIT / "chapter4_differences.json").read_text(encoding="utf-8"))["differences"]

        def walk(node, fn):
            """Apply fn to every string in the structure, in place; returns how many strings changed."""
            n = 0
            items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else ()
            for k, v in list(items):
                if isinstance(v, str):
                    new = fn(v)
                    if new != v:
                        node[k] = new
                        n += 1
                else:
                    n += walk(v, fn)
            return n
        pairs = {}
        for d in diffs:
            if d["kind"] == "b-for-h":
                pairs[d["stored"].strip("-:")] = d["stored"].strip("-:").replace("b", "h").replace("B", "H")
            elif d["kind"] == "b-for-h and more":
                pairs[d["stored"].strip("-:")] = d["blind_reading"]
        for old, new in sorted(pairs.items(), key=lambda kv: -len(kv[0])):
            pattern = re.compile(r"(?<![A-Za-zʔ])" + re.escape(old) + r"(?![A-Za-zʔ])")
            n = walk(data, lambda s: pattern.sub(new, s))
            if n:
                self.say("chapter 4", "%s -> %s  (in %d string%s)" % (old, new, n, "" if n == 1 else "s"))
        rest = sum(1 for d in diffs if d["kind"] == "differs")
        self.left.append("Grammar chapter: %d stored words differ from the blind reading in an accent, a vowel or a glottal stop. They were matched "
                         "by likeness, not by position, and need a person with the page (chapter4_differences.json)" % rest)

    # ---- 6 ----
    def sound_changes(self):
        self.head("6. Sound-change rules: example forms")
        fixes = [("kusaakiraawa", "kusaakiraawaʔ"), ("tikiikaahu", "tikiikaahuʔ"), ("ahibt", "ahiht"), ("tiraraahu", "tiraraahuʔ"),
                 ("katawiwari", "katawiwarik")]
        for rule_id, examples in self.conn.execute("select rule_id, examples from sound_change_rules").fetchall():
            new = examples or ""
            for old, good in fixes:
                pattern = re.compile(r"(?<![A-Za-zʔ])" + re.escape(old) + r"(?![A-Za-zʔ])")
                if pattern.search(new):
                    new = pattern.sub(good, new)
                    self.say("sound changes", "rule %s: %s -> %s" % (rule_id, old, good))
            if new != (examples or ""):
                self.run("update sound_change_rules set examples=? where rule_id=?", (new, rule_id))

    # ---- 7 to 11: the dictionary, from the graded differences ----
    def dictionary(self):
        graded = [json.loads(line) for line in (AUDIT / "s2e_graded.jsonl").open(encoding="utf-8")]
        graded = [d for d in graded if d["grade"] in ("confirmed", "text-layer")]

        self.head("7. Dictionary verb forms")
        for d in graded:
            if base_field(d["field"]) != "form":
                continue
            kinds = set(d["kind"].split("+"))
            old = re.sub(r"^\s*\d+\.\s*", "", d["stored"])
            new = re.sub(r"^\s*\d+\.\s*", "", d["printed"])
            n = index_of(d["field"])
            if "punctuation" in kinds or d.get("ratio", 1.0) < 0.8 or abs(len(old) - len(new)) > 4:
                self.left.append("verb form %s of %s (%s): stored %r, printed stretch %r: the match is not clean" % (n, d["headword"], d["entry_id"], old, d["printed"]))
                continue
            row = self.conn.execute("select id, skiri_form from paradigmatic_forms where entry_id=? and form_number=?", (d["entry_id"], n)).fetchone()
            if not row or row[1] != old:
                continue
            self.run("update paradigmatic_forms set skiri_form=? where id=?", (new, row[0]))
            forms = ((self.by_id.get(d["entry_id"]) or {}).get("part_II") or {}).get("paradigmatic_forms") or {}
            if forms.get("form_%d" % n) == old:
                forms["form_%d" % n] = new
            self.say("verb forms", "%-22s form %s: %s -> %s   [%s, book p. %s]" % (d["headword"], n, old, new, d["grade"], d["book_page"]))

        self.head("8. Stand-in characters in words cited from other languages")
        def apply_edits(stored, edits):
            pos, s = 0, stored
            for a, b in edits:
                if not a:
                    return None
                i = s.find(a, pos)
                if i < 0:
                    return None
                s = s[:i] + b + s[i + len(a):]
                pos = i + len(b)
            return s
        for d in graded:
            if d["kind"] != "citation-standin":
                continue
            f, n = base_field(d["field"]), index_of(d["field"])
            new = apply_edits(d["stored"], d.get("edits") or [])
            if new is None:
                self.left.append("%s of %s: could not place the printed characters in the stored value" % (d["field"], d["headword"]))
                continue
            entry = self.by_id.get(d["entry_id"]) or {}
            if f == "cognate.form":
                rows = self.conn.execute("select id, form from cognates where entry_id=? order by id", (d["entry_id"],)).fetchall()
                if n and n <= len(rows) and rows[n - 1][1] == d["stored"]:
                    self.run("update cognates set form=? where id=?", (new, rows[n - 1][0]))
                    cogs = (entry.get("part_I") or {}).get("cognates") or []
                    for c in cogs:
                        if c.get("form") == d["stored"]:
                            c["form"] = new
                    self.say("citations", "%-22s cognate: %s -> %s" % (d["headword"], d["stored"], new))
            elif f == "etymology":
                row = self.conn.execute("select id, raw_etymology, constituent_elements from etymology where entry_id=? order by id", (d["entry_id"],)).fetchall()
                if n and n <= len(row) and row[n - 1][1] == d["stored"]:
                    self.run("update etymology set raw_etymology=? where id=?", (new, row[n - 1][0]))
                    ety = (entry.get("part_I") or {}).get("etymology") or {}
                    if ety.get("raw_etymology") == d["stored"]:
                        ety["raw_etymology"] = new
                    self.say("citations", "%-22s etymology: %s" % (d["headword"], "; ".join("%s -> %s" % (a, b) for a, b in d["edits"])))
            elif f == "example.skiri":
                self.left.append("example of %s: stored %r, printed %r (a printing oddity inside a Skiri word; left as stored)" % (d["headword"], d["stored"], d["printed"]))
        # the pieces the parse cut out of etymologies carry the same characters
        n_pieces = 0
        for rid, pieces in self.conn.execute("select id, constituent_elements from etymology where constituent_elements is not null").fetchall():
            new = pieces
            for a, b in CERTAIN_STANDINS:
                new = new.replace(a, b)
            if new != pieces:
                self.run("update etymology set constituent_elements=? where id=?", (new, rid))
                n_pieces += 1
        if n_pieces:
            self.say("citations", "etymology pieces (constituent_elements): the same stand-in characters replaced in %d rows" % n_pieces)
        n_left = self.conn.execute("select count(*) from cognates where form like '%ó%' or form like '%Ý%'").fetchone()[0]
        self.log.append("  (cognate forms still holding ó or Ý before this run: %d)" % n_left)

        self.head("9. Combining forms: a space or a line-break hyphen inside the form")
        for d in graded:
            if base_field(d["field"]) != "additional_form" or d["kind"] not in ("spacing", "stored-keeps-line-break"):
                continue
            n = index_of(d["field"])
            old = d["stored"]
            if d["kind"] == "spacing":
                new = d["printed"]
            else:
                new = d.get("printed_if_line_breaks_are_joined") or ""
                if "[" in old or not new:
                    self.left.append("combining form of %s: %r: a hyphen at a line end that could not be resolved" % (d["headword"], old))
                    continue
            row = self.conn.execute("select additional_forms from lexical_entries where entry_id=?", (d["entry_id"],)).fetchone()
            try:
                forms = json.loads(row[0]) if row and row[0] else []
            except ValueError:
                forms = []
            if not (n and n <= len(forms) and isinstance(forms[n - 1], dict) and forms[n - 1].get("form") == old):
                continue
            forms[n - 1]["form"] = new
            self.run("update lexical_entries set additional_forms=? where entry_id=?", (json.dumps(forms, ensure_ascii=False), d["entry_id"]))
            jforms = (((self.by_id.get(d["entry_id"]) or {}).get("part_I") or {}).get("grammatical_info") or {}).get("additional_forms") or []
            for jf in jforms:
                if isinstance(jf, dict) and jf.get("form") == old:
                    jf["form"] = new
            self.say("combining forms", "%-22s %s -> %s%s" % (d["headword"], old, new,
                                                             "   (hyphen at a line end read as a line break)" if d["kind"] != "spacing" else ""))

        self.head("10. Headwords")
        manual = {
            "SK-ø_(ut...)_pak_siriq-p349-3573": ("headword", "Ø (ut...) pak siriʔ", "Ø (ut...) paksiriʔ"),
            "SK-wiicat_k-p179-3542": ("headword", "wiicat k", "wiicatk"),
            "SK-awacitiksa-p20-0264": ("stem_preverb", "(i r...)", "(ir...)"),
            "SK-hiitka-p390-3849": ("stem_preverb", "(i r...ut...)", "(ir...ut...)"),
            "SK-tahaariwi--p155-3027": ("stem_preverb", "(u t...)", "(ut...)"),
        }
        for entry_id, (col, old, new) in manual.items():
            row = self.conn.execute('select headword, stem_preverb from lexical_entries where entry_id=?', (entry_id,)).fetchone()
            if not row:
                continue
            current = row[0] if col == "headword" else row[1]
            if current is None or cc_tidy(current).replace(" ", "") != cc_tidy(old).replace(" ", "") and current != old:
                continue
            if current == new:
                continue
            self.run('update lexical_entries set "%s"=? where entry_id=?' % col, (new, entry_id))
            e = self.by_id.get(entry_id) or {}
            if col == "headword" and e.get("headword") == current:
                e["headword"] = new
            elif col == "stem_preverb" and (e.get("part_I") or {}).get("stem_preverb") == current:
                e["part_I"]["stem_preverb"] = new
            self.say("headwords", "%s, %s: %r -> %r" % (entry_id, col, current, new))
        row = self.conn.execute("select headword from lexical_entries where entry_id='SK-tawihuhtawii_(ut...)-p163-3207'").fetchone()
        if row and row[0] == "tawihuhtawii (ut...)":
            self.run("update lexical_entries set headword='tawihuhtawii' where entry_id='SK-tawihuhtawii_(ut...)-p163-3207'")
            e = self.by_id.get("SK-tawihuhtawii_(ut...)-p163-3207") or {}
            if e.get("headword") == "tawihuhtawii (ut...)":
                e["headword"] = "tawihuhtawii"
            self.say("headwords", "tawihuhtawii: the preverb (ut...) was stored twice, in the headword and in its own column; removed from the headword")
        for d in graded:
            if d["kind"] != "bracket-note-not-stored":
                continue
            notes = re.findall(r"\[[^\]]*\]", d["printed"])
            if len(notes) != 1:
                self.left.append("headword %s: bracket note not placed (%r)" % (d["headword"], d["printed"]))
                continue
            note = cc_tidy(notes[0])
            row = self.conn.execute("select headword, stem_preverb from lexical_entries where entry_id=?", (d["entry_id"],)).fetchone()
            if not row or "[" in (row[0] or "") or "[" in (row[1] or ""):
                continue
            new = ("%s %s" % (row[1], note)) if row[1] else note
            self.run("update lexical_entries set stem_preverb=? where entry_id=?", (new, d["entry_id"]))
            e = self.by_id.get(d["entry_id"]) or {}
            if "part_I" in e:
                e["part_I"]["stem_preverb"] = new
            self.say("headwords", "%-22s bracket note %s added after the headword (kept with the preverb): %r" % (row[0], note, new))

        self.head("11. The column an entry is printed in")
        n = 0
        for d in graded:
            if base_field(d["field"]) != "column_position":
                continue
            row = self.conn.execute("select column_position from lexical_entries where entry_id=?", (d["entry_id"],)).fetchone()
            if row and row[0] == d["stored"]:
                self.run("update lexical_entries set column_position=? where entry_id=?", (d["printed"], d["entry_id"]))
                meta = (self.by_id.get(d["entry_id"]) or {}).get("entry_metadata") or {}
                if meta.get("column") == d["stored"]:
                    meta["column"] = d["printed"]
                n += 1
        if n:
            self.counts["column"] += n
            self.log.append("  %d entries: left/right corrected from the position of the headword on the page" % n)

    # ---- 12 ----
    def entries(self):
        self.head("12. Entries")
        # the printed entry the database lacked
        if not self.conn.execute("select 1 from lexical_entries where headword='kusisaar' and stem_preverb is null").fetchone():
            template = self.by_id.get("SK-kusisaar-p103-2019")
            seq = max(int(re.search(r"-(\d+)$", e["entry_id"]).group(1)) for e in self.s2e if e.get("entry_id")) + 1
            entry_id = "SK-kusisaar-p103-%04d" % seq
            from respell_and_normalize import generate_normalized_form
            phon = "[•kʊ-sɪ-saa(r)•]"                      # the printed form in the stored convention; restore_parks_ipa.py rewrites it from the page
            norm = (template or {}).get("normalized_form") or generate_normalized_form("kusisaar", phon)
            compound = '{"has_null_stem": false, "preverb": null, "verb_stem": null, "noun": null}'
            pieces = [{"morpheme": "kusis", "gloss": "lively", "morpheme_type": None}, {"morpheme": "aar", "gloss": "become", "morpheme_type": None}]
            self.run("insert into lexical_entries (entry_id, headword, normalized_form, phonetic_form, simplified_pronunciation, stem_preverb, "
                     "grammatical_class, verb_class, additional_forms, page_number, column_position, compound_structure, raw_entry_json, "
                     "blue_book_attested) values (?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                     (entry_id, "kusisaar", norm, phon, (template or {}).get("part_I", {}).get("simplified_pronunciation"), None, "VI", "(1-i)", None, 103,
                      "right", compound, json.dumps({"added": "2026-11-13", "by": "source-fidelity audit", "from": "text layer of page_103.pdf (book page 451), confirmed on a crop"})))
            self.run("insert into glosses (entry_id, sense_number, definition, usage_notes) values (?,?,?,?)", (entry_id, 1, "play.", "(impf. only)"))
            self.run("insert into etymology (entry_id, raw_etymology, literal_translation, constituent_elements) values (?,?,?,?)",
                     (entry_id, "kusis+aar, become lively", "become lively", json.dumps(pieces, ensure_ascii=False)))
            for n, form in ((3, "tikusisaariʔ"), (4, "iriirakusisaari"), (5, "tikusisaarista")):
                self.run("insert into paradigmatic_forms (entry_id, form_number, skiri_form) values (?,?,?)", (entry_id, n, form))
            new = {"headword": "kusisaar",
                   "entry_metadata": {"page_number": 103, "column": "right", "continues_from_previous_page": False, "continues_to_next_page": False},
                   "part_I": {"stem_preverb": None, "phonetic_form": phon,
                              "grammatical_info": {"grammatical_class": "VI", "verb_class": "(1-i)", "additional_forms": []},
                              "glosses": [{"number": None, "definition": "play.", "usage_notes": "(impf. only)"}],
                              "etymology": {"raw_etymology": "kusis+aar, become lively", "constituent_elements": pieces, "literal_translation": "become lively"},
                              "cognates": [], "simplified_pronunciation": (template or {}).get("part_I", {}).get("simplified_pronunciation")},
                   "part_II": {"paradigmatic_forms": {"form_1": None, "form_2": None, "form_3": "tikusisaariʔ", "form_4": "iriirakusisaari",
                                                      "form_5": "tikusisaarista", "additional_forms": []}, "examples": []},
                   "compound_structure": json.loads(compound), "derived_stems": [], "entry_id": entry_id, "normalized_form": norm}
            at = self.s2e.index(template) if template in self.s2e else len(self.s2e)
            self.s2e.insert(at, new)                        # printed just before kusisaar (ir...)
            self.by_id[entry_id] = new
            self.say("entries", "added %s: kusisaar VI(1-i) '(impf. only) play.', forms 3 tikusisaariʔ, 4 iriirakusisaari, 5 tikusisaarista (book p. 451)" % entry_id)
        # the stored entry that is not a headword in the book
        if self.conn.execute("select 1 from lexical_entries where entry_id=?", (PHANTOM,)).fetchone():
            refs = self.conn.execute("select count(*) from english_index where entry_id=?", (PHANTOM,)).fetchone()[0]
            if refs:
                self.left.append("%s is not a headword in the book but %d English-index rows point to it; not removed" % (PHANTOM, refs))
            else:
                for table in ("glosses", "etymology", "paradigmatic_forms", "examples", "cognates", "semantic_tags"):
                    self.run('delete from "%s" where entry_id=?' % table, (PHANTOM,))
                self.run("delete from lexical_entries where entry_id=?", (PHANTOM,))
                self.s2e[:] = [e for e in self.s2e if e.get("entry_id") != PHANTOM]
                self.say("entries", "removed %s 'aakaʔa (ir...)': not a headword in the book; it repeated the third variant of 'aaka, aakaʔ, aakaʔa', "
                                    "whose gloss and example the real entry already has" % PHANTOM)


def cc_tidy(s):
    return re.sub(r"\s+", " ", s or "").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB)) if args.apply else sqlite3.connect("file:%s?mode=ro" % DB.resolve().as_posix(), uri=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.apply:
        backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
        backups.mkdir(parents=True, exist_ok=True)
        conn.close()
        shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s.db" % stamp))
        shutil.copy2(S2E_JSON, backups / ("skiri_to_english_respelled_backup_%s.json" % stamp))
        conn = sqlite3.connect(str(DB))
    fx = Fixer(conn, args.apply)
    fx.appendix1(); fx.appendix2(); fx.appendix3(); fx.abbreviations(); fx.chapter4(); fx.sound_changes(); fx.dictionary(); fx.entries()
    total = sum(fx.counts.values())
    header = ["apply_audit_fixes_2026_11 — %s — %s" % ("APPLY" if args.apply else "dry run", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
              "changes: %d   %s" % (total, dict(fx.counts))]
    tail = ["", "== Left for a person (%d)" % len(fx.left)] + ["  " + t for t in fx.left]
    text = "\n".join(header + fx.log + tail) + "\n"
    if not args.apply:
        out("\n".join(header))
        out("\n".join(fx.log[:60]))
        out("  ... (%d log lines in all)" % len(fx.log))
        out("\n".join(tail[:40]))
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return
    conn.commit()
    conn.close()
    S2E_JSON.write_text(json.dumps(fx.s2e, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, data in fx.json_files.items():
        (EXTRACTED / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], cwd=str(ROOT), check=False, stdout=subprocess.DEVNULL)
    text += "\nbackups: OneDrive/pari_pakuru_backups (stamp %s)\n" % stamp
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("left for a person: %d" % len(fx.left))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
