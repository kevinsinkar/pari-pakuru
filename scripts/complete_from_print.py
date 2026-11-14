#!/usr/bin/env python3
"""
Add what the dictionary prints and the database lacks (2026-11-14)
==================================================================

After the audit's fixes, 218 differences were left between the stored
dictionary and the printed page (open items 34 and 41), and many glosses
kept a space before punctuation (item 18). This script closes what the PDF's
text layer can settle without anyone reading an image. The text layer is the
typesetter's own text, decoded with the character table that was verified
against the printed glyphs.

Every new value comes from the printed entry, and the script refuses a change
it cannot find there: a corrected value must be, letter for letter, a reading
of a stretch of the printed entry it belongs to.

What it does
     1  derived stems     the stems Parks lists under ten bound stems, with their glosses,
                          go into the `derived_stems` table (it was empty)
     2  examples          examples that are printed and were never stored
     3  citations         forms cited from other languages that still held stand-in
                          characters (ó for š, Ý for é, í for ó ...)
     4  glottal stop      a typographic apostrophe stored where the page prints ʔ
     5  line breaks       a hyphen the typesetter put at the end of a line and the parse kept:
                          before a `+` in an etymology, and inside a Skiri word
     6  spacing           letter-spaced and split words ("o n  t h e  p i g ."), one word stored as two
     7  literal meaning   where the parse paraphrased the gloss of an etymology ("plural to be
                          strung"), the printed wording ("PL + to be strung")
     8  single values     corrections listed one by one below, each checked against the page
     9  not printed       three numbered verb forms stored for the noun itkaakahaaruʔ, which the
                          page does not print; four labels the parse made up for bracket notes
    10  punctuation       the space the parse left before a full stop, comma, semicolon or bracket
    11  pieces            the list of pieces the parse made from each etymology (`constituent_elements`)
                          follows the etymology: a piece that kept a line-end hyphen, an apostrophe
                          or a stray space is set to the form the etymology now has

What it leaves, and says so in its report
    Anything where the page itself is in doubt (a printing slip, a hyphen at a
    line end that may belong to the word), and the project's own choices (the
    N-KIN class).

    python scripts/complete_from_print.py            # dry run: prints what it would do, writes nothing
    python scripts/complete_from_print.py --apply    # backs up, then writes the database, the JSON and the report

After --apply: `python scripts/source_audit/s2e_compare.py --out reports/source_audit_2026-11/after_fixes`,
`scripts/source_audit/recall_test.py`, `scripts/check_simplified_forms.py`, `scripts/db_dump.py --write`.
"""
import argparse
import datetime as dt
import itertools
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "source_audit"))
import compare_core as cc  # noqa: E402
import s2e_compare  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
REPORT = ROOT / "reports" / "source_audit_2026-11" / "print_completion_report.txt"
LINE_END = re.compile(r"-[ ]*\n[ ]*")

# stored stand-in -> printed character (scripts/source_audit/chartable.py); ":" and "÷" stood for ú in two citations
STAND_IN = {"ó": "š", "Ý": "é", "í": "ó", "Ó": "ą", "Ô": cc.nfc("ą" + cc.ACUTE), "è": "į", "ü": "ž", "š": "ⁱ", ":": "ú", "÷": "ú"}

# ---- 2: examples that are printed and were not stored (entry id, Skiri, English), read off the text layer ----
EXAMPLES = [
    ("SK-haa-p33-0546", "kuratiihaaʔu", "my child."),
    ("SK-haa-p33-0546", "kurasiihaaʔu", "your child."),
    ("SK-haa-p33-0546", "kurahaaʔu", "his child."),
    ("SK-haa-p33-0546", "kuraciihaaʔu", "our (incl. du.) child."),
    ("SK-parihik-p110-2132", "tipariʔit, tiparit", "it is sleek."),
    ("SK-parit-p110-2134", "ruutiiparihit", "it is really smooth."),
    ("SK-raakii-p119-2322", "tiraakiirit", "they (different ones) are strung, braided together."),
    ("SK-rahkarariihuriir-p131-2548", "turahkarariihuriwaa", "they are colorful, have pretty colors."),
    ("SK-rahkasii-p131-2550", "tirarahkasiiʔ", "they are wearing garments."),
    ("SK-raraasitaqu-p136-2680", "iriirararaasituuki", "the ones that are cold."),
    ("SK-takaahak-p157-3058", "tiracakaahat", "they got down."),
    ("SK-takaahak-p157-3059", "tiracakaahaakuʔ", "they are falling off, as leaves."),
    ("SK-takaarahak-p157-3062", "tiiraktacakaarahat", "they dropped them off."),
    ("SK-takacat-p157-3066", "tihtakacat", "they went to get water."),
    ("SK-takaruus-p157-3067", "tiracakaruus", "they are flat."),
    ("SK-takiis-p157-3073", "tiictakiis", "they are stingy."),
    ("SK-takiis/kiqis-p157-3074", "tihtakiisuʔ", "they are cracking them."),
    ("SK-takipiir-p157-3077", "tiracakipiiʔ", "they are wadded up."),
]

# ---- 8: single values. (entry id, table, column, selector, old, new, why). The selector picks the row:
#         a sense number for glosses, the old value itself elsewhere. `None` as new value stores NULL.
SINGLE = [
    ("SK-hukawarik-p45-0747", "additional_forms", "form", None, "hukawawarik", "hukawaawarik", "the page has huka-|waawarik; its example is tihukawaawarit"),
    ("SK-raararaquk-p122-2380", "additional_forms", "form", None, "raahkaraʔuk", "raarahkaraʔuk", "the page has raarah-|karaʔuk; its example is tiraarahkaruʔ"),
    ("SK-hiirarahuuruq-p389-3840", "additional_forms", "form", None, "hiirararur-, hiirarahuh-", "hiirarahur-, hiirarahuh-", "a letter"),
    ("SK-raahkuucuq-p117-2285", "examples", "skiri_text", None, "tatuuu-haahkuucirahkatakuus", "tatuuhaahkuucirahkatakuus", "the page has tatuu-|haahkuucirahkatakuus: a line break, and one u too many was stored"),
    ("SK-itkaakahaaruq-p69-1225", "examples", "skiri_text", None, "iriiraatkaaka- hahaaruhat", "iriiraatkaakahaaruhat", "the page has iriiraatkaaka-|haaruhat"),
    ("SK-raaqiiwaat-p115-2245", "examples", "skiri_text", None, "tiirikstaaraaʔiiwaawatuuhuʔ", "tiirikstaaʔiiwaawatuuhuʔ", "the page has tiirikstaa-|ʔiiwaawatuuhuʔ"),
    ("SK-kactahaaruq-p75-1364", "examples", "english_translation", None, "where the buffalo grass is (i.e., ex- tends).", "where the buffalo grass is (i.e., extends).", "a line break in an English word"),
    ("SK-paawariihusuq-p107-2041", "glosses", "definition", 1, "traveller; drifter.", "traveler; drifter.", "the page's spelling"),
    ("SK-iksas-p62-1081", "glosses", "definition", 1, "toothed-edge scraper of bison leg bone, used as a flesher.", "tooth-edged scraper of bison leg bone, used as a flesher.", "the page's wording"),
    ("SK-haaktaquk-p35-0594", "glosses", "definition", 1, "make a pipestem, as for a Pipe Dance.", "make pipestem, as for a Pipe Dance.", "the page's wording"),
    ("SK-rikiisastarahi-p492-4178", "glosses", "definition", 1, "Arikara corn, a short variety obtained by the Skiris from the Arikara.", "Arikara corn, a short variety obtained by the Skiris from the Arikaras.", "the page's wording"),
    ("SK-rahkacak-p478-4125", "glosses", "definition", 2, "hack, chop", "hack, chop, as weeds.", "the end of the gloss was not stored"),
    ("SK-ruusikiirus-p150-2919", "glosses", "definition", 1, None, "(formerly) wiping material, as used after defecating; (contemp.) toilet paper.", "the page puts each qualifier before the part it belongs to"),
    ("SK-ruusikiirus-p150-2919", "glosses", "usage_notes", 1, "formerly; contemp.", None, "now in the gloss, where the page has them"),
    ("SK-tiirawaahat-p165-3250", "glosses", "definition", 1, None, "(formerly) The Heavens, the all-pervasive power of the universe, referred to as Atiʔas Tiitaku Ahakitaku; (contemp.) God.", "the page puts each qualifier before the part it belongs to"),
    ("SK-tiirawaahat-p165-3250", "glosses", "usage_notes", 1, "(formerly), (contemp.)", None, "now in the gloss, where the page has them"),
    ("SK-raawiirakuuruq-p127-2502", "glosses", "definition", 1, None, "warrior; war party; (contemp.) soldier.", "the page puts the qualifier before the part it belongs to"),
    ("SK-raawiirakuuruq-p127-2502", "glosses", "usage_notes", 1, "(contemp.)", None, "now in the gloss, where the page has it"),
    ("SK-kawitaat-p84-1566", "glosses", "usage_notes", 1, "with prefixes [+ ruu-, i-]", None, "not printed words; the bracket note is stored with the preverb"),
    ("SK-kitahiis-p98-1911", "etymology", "raw_etymology", None, "kita+hiis, rough on top", "kita+hiis, rough on top; i.q. katahiis, SB katahiis, ickatahiis, Ar. iskačitahiiš", "the second half of the etymology was not stored"),
    ("SK-riicis-p140-2783", "etymology", "raw_etymology", None, "raa+icis (ut...), learn about a way", "raa+icis (ut...), learn about a way; i.q. SB reecis (ut...), Ar. reesiš (ut...)", "the second half of the etymology was not stored"),
    ("SK-war-p177-3501", "etymology", "raw_etymology", None, "<ut+war>", "<ut+war, cf. Ar. wahuun (ut...)>", "the second half of the etymology was not stored"),
    ("SK-warii-p177-3506", "etymology", "raw_etymology", None, "<warii, DIST of at to go>", "<warii, DIST of at to go; cf. Ar. wanuu>", "the second half of the etymology was not stored"),
    ("SK-ituhwiitik-p69-1246", "etymology", "raw_etymology", None, "<itur+wiitik, vil- lage to sit down>", "<itur+wiitik, village to sit down>", "a line break in an English word"),
    ("SK-takaruus-p157-3067", "etymology", "raw_etymology", None, "ta+karuus, GEN.LOC +  b e  d e - flated", "ta+karuus, GEN.LOC + be deflated", "letter-spaced, and a line break in an English word"),
    ("SK-piiracaahuuruq-p460-4086", "etymology", "raw_etymology", None, "piira+caahur+uʔ, child + caa- hur + NOM", "piira+caahur+uʔ, child + caahur + NOM", "a line break in a Skiri word quoted in the gloss"),
]
NEW_COGNATES = [("SK-kitahiis-p98-1911", "SB", "ickatahiis", "printed beside katahiis and not stored")]
# ---- 9: stored and not printed ----
FORMS_NOT_PRINTED = ["SK-itkaakahaaruq-p69-1225"]          # a noun; the page prints no numbered forms for it
MADE_UP_FORM_TYPES = {"usage", "prefix", "prefixes"}        # labels the parse gave a bracket note that is stored with the preverb
# ---- left as they are, with the reason (shown in the report) ----
LEFT = [   # (entry id, table, column, what the page has and why the stored value stays)
    ("SK-cararaat-p28-0416", "etymology", "raw_etymology", "(i)sananaapi- at a line end is followed by its English gloss: a bound form, the hyphen is printed"),
    ("SK-pira--p113-2186", "etymology", "raw_etymology", "wiruu- at a line end is followed by its English gloss: a bound form, the hyphen is printed"),
    ("SK-itkatapiirahc/raqac-p69-1242", "etymology", "raw_etymology", "katapi-|ra- across a line end: one form katapira- or two bound forms; the page cannot say"),
    ("SK-haapuh-p35-0604", "glosses", "definition", "the page prints \"into a the ground\"; the stored gloss leaves out the stray a"),
    ("SK-awuh-p26-0353", "examples", "skiri_text", "the page prints taatawuhu’ with an apostrophe where the letter is ʔ; stored with ʔ"),
    ("SK-apak-p360-3687", "examples", "skiri_text", "rihkuupaȞkstarit on the page: a printing oddity, for a person (open item 45)"),
    ("SK-haakarata-p34-0574", "glosses", "definition", "the page's bracket is never closed; the stored gloss and note rearrange it"),
    ("SK-kicawihuukaaraqa-p85-1593", "etymology", "literal_translation", "the page's bracket is never closed; the stored literal meaning closes it"),
    ("SK-tuuwirik-p167-3292", "glosses", "definition", "the qualifier (pl. subj.) and the reference are stored as a note beside the gloss"),
    ("SK-icataarikiisuq-p55-0947", "etymology", "literal_translation", "corn-|bread across a line end: cornbread or corn bread; the page cannot say"),
]


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.flush()


def is_word(ch):
    return bool(ch) and (ch.isalpha() or ch == "ʔ")


class Page:
    """The printed entries, and the questions the script asks of them."""

    def __init__(self, db_path):
        self.printed = [json.loads(line) for line in s2e_compare.PRINTED.open(encoding="utf-8")]
        blocks = {p["seq"]: cc.Block(p["spans"]) for p in self.printed}
        self.db = s2e_compare.load_db(db_path)
        self.pairs, how, phantom, missing = s2e_compare.pair_entries(self.db, self.printed, blocks)
        self._blocks = {}
        words = Counter()
        for e in self.db.values():
            for g in e["glosses"]:
                words.update(w.lower() for w in re.findall(r"[A-Za-z]{3,}", g["definition"] or ""))
        self.vocab = words

    def block(self, entry_id):
        if entry_id not in self._blocks:
            self._blocks[entry_id] = cc.Block(self.printed[self.pairs[entry_id] - 1]["spans"])
        return self._blocks[entry_id]

    def hits(self, entry_id, value):
        """Every printed stretch whose letters are the value's: (start in the text, the stretch, whole words?)."""
        b = self.block(entry_id)
        sk = cc.skeleton(value)
        found, start = [], 0
        while sk:
            p = b.sk.find(sk, start)
            if p < 0:
                break
            start = p + 1
            raw = b.printed(p, p + len(sk), value)
            o0 = b.idx[p]
            v = cc.nfc(value).strip()
            lead = len(v) - len(v.lstrip("-"))
            while lead and o0 > 0 and b.orig[o0 - 1] == "-":
                o0 -= 1
                lead -= 1
            found.append((o0, raw, b.whole_words(p, p + len(sk), value)))
        found.sort(key=lambda h: (not h[2], h[0]))
        return found

    def has(self, entry_id, value):
        """Is the value printed in this entry as it stands (any reading of the line ends)?"""
        v = cc.tidy(value)
        if cc.nfc(value.strip()) in self.block(entry_id).orig:
            return True
        return any(whole and v in cc.readings(raw) for o0, raw, whole in self.hits(entry_id, value))

    def canonical(self, entry_id, o0, raw, word_joins=True, stored=""):
        """The printed stretch as one line. A hyphen at a line end is dropped before a `+`, and inside a
        Skiri word that goes on in the Skiri font; in English it is dropped when that makes a word the
        glosses use, or the word the stored value already has. It is kept before a new word or a
        punctuation mark. Returns the text and the number of line ends with a hyphen in the stretch;
        (None, 0) when the page cannot say."""
        b = self.block(entry_id)
        parts, i = [], 0
        line_ends = len(LINE_END.findall(raw))
        stored_words = set(re.findall(r"[a-z]+", stored.lower()))
        for m in LINE_END.finditer(raw):
            parts.append(raw[i:m.start()])
            i = m.end()
            before = raw[m.start() - 1] if m.start() > 0 else ""
            after = raw[m.end()] if m.end() < len(raw) else ""
            k_before = b.kinds[o0 + m.start() - 1] if m.start() > 0 else "E"
            k_after = b.kinds[o0 + m.end()] if o0 + m.end() < len(b.kinds) else "E"
            if after == "+":
                continue
            if is_word(before) and is_word(after) and k_before == "S" and k_after == "S":
                if not word_joins:
                    return None, 0
                continue
            if is_word(before) and is_word(after) and k_before == "E" and k_after == "E":
                left = re.search(r"[A-Za-z]+$", "".join(parts))
                right = re.match(r"[A-Za-z]+", raw[m.end():])
                joined = ((left.group(0) if left else "") + (right.group(0) if right else "")).lower()
                if self.vocab.get(joined) or joined in stored_words:
                    continue
                if left and right and left.group(0).lower() in stored_words and right.group(0).lower() in stored_words:
                    parts.append("-")           # stored as a hyphenated compound; the page does not contradict it
                    continue
                return None, 0
            if k_before == "S" and k_after == "E" and is_word(after):
                parts.append("- ")              # a bound form, then its English gloss
            else:
                parts.append("-")
        parts.append(raw[i:])
        text = "".join(parts)
        text = re.sub(r"/[ ]*\n[ ]*", "/", text)
        return cc.tidy(text.replace("\n", " ")), line_ends


class Plan:
    def __init__(self, page, conn):
        self.page, self.conn = page, conn
        self.ops = []          # (section, sql, params, entry_id, line for the report)
        self.notes = []        # things not done, with the reason
        self.touched = set()
        self.count = Counter()

    def op(self, section, sql, params, entry_id, line):
        self.ops.append((section, sql, params, entry_id, line))
        self.touched.add(entry_id)
        self.count[section] += 1

    def skip(self, section, entry_id, line):
        self.notes.append((section, entry_id, line))

    # ---------------------------------------------------------------- 1
    def derived_stems(self):
        data = json.loads(S2E_JSON.read_text(encoding="utf-8"))
        have = {(r[0], r[1]) for r in self.conn.execute("select entry_id, stem_form from derived_stems")}
        for e in data:
            eid = e.get("entry_id")
            for d in e.get("derived_stems") or []:
                form, meaning = d.get("derived_form"), d.get("meaning")
                if eid not in self.page.pairs or not form or (eid, form) in have:
                    continue
                if not (self.page.has(eid, form) and self.page.has(eid, meaning or "")):
                    self.skip("1 derived stems", eid, "%s: not found on the page as stored in the JSON; not added" % form)
                    continue
                self.op("1 derived stems", "insert into derived_stems (entry_id, stem_form, phonetic_form, definition, raw_json) values (?,?,?,?,?)",
                        (eid, form, None, meaning, json.dumps(d, ensure_ascii=False)), eid, "%s: %s  %s" % (eid, form, meaning))

    # ---------------------------------------------------------------- 2
    def examples(self):
        for eid, skiri, english in EXAMPLES:
            if self.conn.execute("select 1 from examples where entry_id=? and skiri_text=?", (eid, skiri)).fetchone():
                continue
            if not (self.page.has(eid, skiri) and self.page.has(eid, english)):
                self.skip("2 examples", eid, "%s = %s: not found on the page; not added" % (skiri, english))
                continue
            self.op("2 examples", "insert into examples (entry_id, skiri_text, english_translation, usage_context, source) values (?,?,?,?,?)",
                    (eid, skiri, english, None, "parks_dictionary"), eid, "%s: %s  %s" % (eid, skiri, english))

    # ---------------------------------------------------------------- 3 to 7
    def fields(self, e):
        """(table, row id, column, value, Skiri-bearing?, key inside additional_forms)."""
        eid = e["entry_id"]
        if e["additional_forms"]:
            try:
                forms = json.loads(e["additional_forms"])
            except ValueError:
                forms = []
            for n, f in enumerate(forms if isinstance(forms, list) else []):
                if isinstance(f, dict) and f.get("form"):
                    yield ("lexical_entries", eid, "additional_forms", f["form"], True, n)
        for g in e["glosses"]:
            yield ("glosses", g["id"], "definition", g["definition"], False, None)
        for x in e["etymology"]:
            yield ("etymology", x["id"], "raw_etymology", x["raw_etymology"], True, None)
            yield ("etymology", x["id"], "literal_translation", x["literal_translation"], False, None)
        for x in e["cognates"]:
            yield ("cognates", x["id"], "form", x["form"], True, None)
        for x in e["forms"]:
            yield ("paradigmatic_forms", x["id"], "skiri_form", x["skiri_form"], True, None)
        for x in e["examples"]:
            yield ("examples", x["id"], "skiri_text", x["skiri_text"], True, None)
            yield ("examples", x["id"], "english_translation", x["english_translation"], False, None)

    def set_value(self, section, e, table, row, column, old, new, key, why=""):
        eid = e["entry_id"]
        line = "%s  %s.%s: %s  ->  %s%s" % (eid, table, column, old, new, ("   (" + why + ")") if why else "")
        if table == "lexical_entries":            # one form inside the additional_forms list
            forms = json.loads(e["additional_forms"])
            forms[key]["form"] = new
            e["additional_forms"] = json.dumps(forms, ensure_ascii=False)
            self.op(section, "update lexical_entries set additional_forms=? where entry_id=?", (e["additional_forms"], eid), eid, line)
        else:
            self.op(section, 'update "%s" set %s=? where id=? and %s is ?' % (table, column, column), (new, row, old), eid, line)

    def from_the_page(self):
        single = {(s[0], s[1], s[4]) for s in SINGLE}
        left = {(s[0], s[1], s[2]) for s in LEFT}
        for eid in sorted(self.page.pairs, key=lambda i: self.page.pairs[i]):
            e = self.page.db[eid]
            compound = bool(re.search(r"\w-\w", e["headword"]))
            for table, row, column, value, skiri, key in self.fields(e):
                if not value or not cc.skeleton(value):
                    continue
                if (eid, "additional_forms" if table == "lexical_entries" else table, value) in single:
                    continue
                hits = self.page.hits(eid, value)
                if hits:
                    if column == "literal_translation" and not any(w for o, r, w in hits):
                        pass                                    # inside a longer word: see section 7
                    else:
                        self.respace(e, table, row, column, value, skiri, key, hits, compound, (eid, table, column) in left)
                        continue
                if column == "literal_translation":
                    if (eid, table, column) not in left:
                        self.literal(e, row, value)
                elif skiri:
                    self.letters(e, table, row, column, value, key)

    def respace(self, e, table, row, column, value, skiri, key, hits, compound, left):
        """Sections 5 and 6: same letters as the page, other hyphens or spaces."""
        eid = e["entry_id"]
        v = cc.tidy(value)
        chosen = [h for h in hits if h[2]] or hits
        cands = [self.page.canonical(eid, o0, raw, word_joins=not compound, stored=value) for o0, raw, whole in chosen]
        if any(c is not None and c == value for c, n in cands):
            return
        if not skiri and any(v in cc.readings(raw) for o0, raw, whole in hits):
            return                                              # English, and one reading of the page is what is stored
        # a hyphen may go only where this stretch of the page ends a line with one
        fits = [c for c, n in cands if c is not None and 0 <= value.count("-") - c.count("-") <= n]
        new = fits[0] if fits else None
        if new is None:
            if "- " in value and not left:
                self.skip("5 line breaks", eid, "%s.%s: %s  left: the page cannot say whether the hyphen belongs to the word" % (table, column, value))
            return
        if " < " in value:
            new = re.sub(r" <(?=\S)", " < ", new)               # "X < Y", derived from: not a bracket
        if new == value or cc.skeleton(new) != cc.skeleton(value):
            return
        if new == v and not skiri:
            return                                              # only a space before punctuation: section 10
        hyphen = new.count("-") != value.count("-")
        if new.count(" ") > v.count(" "):
            return                                              # the page breaks a line there; no space is meant
        if left:
            self.skip("5 line breaks", eid, "%s.%s: %s  (page: %s)  left: see the list of values left as they are" % (table, column, value, new))
            return
        self.set_value("5 line breaks" if hyphen else "6 spacing", e, table, row, column, value, new, key)

    def letters(self, e, table, row, column, value, key):
        """Sections 3 and 4: a stand-in character or an apostrophe where the page has another letter."""
        eid = e["entry_id"]
        if self.page.has(eid, value):
            return
        if "’" in value and self.page.has(eid, value.replace("’", "ʔ")):
            self.set_value("4 glottal stop", e, table, row, column, value, value.replace("’", "ʔ"), key)
            return
        spots = [i for i, ch in enumerate(value) if ch in STAND_IN or ch == "’"]
        if not spots or len(spots) > 10:
            return
        best = None
        for n in range(len(spots), 0, -1):
            for chosen in itertools.combinations(spots, n):
                cand = "".join((STAND_IN.get(ch, "ʔ") if i in chosen else ch) for i, ch in enumerate(value))
                if self.page.has(eid, cand):
                    best = cand
                    break
            if best:
                break
        if best:
            self.set_value("3 citations", e, table, row, column, value, best, key)

    def literal(self, e, row, value):
        """Section 7: the gloss of the etymology as printed, where the stored paraphrase is not on the page."""
        eid = e["entry_id"]
        if self.page.has(eid, value):
            return
        raw = next((x["raw_etymology"] for x in e["etymology"] if x["id"] == row), None) or ""
        m = re.match(r"^<?[^,]*,\s*(.*?)>?$", raw.strip())
        if not m:
            return
        gloss = cc.tidy(re.split(r";\s*(?:i\.q\.|cf\.)", m.group(1))[0])
        if gloss and gloss != value and self.page.has(eid, gloss):
            self.op("7 literal meaning", "update etymology set literal_translation=? where id=? and literal_translation is ?",
                    (gloss, row, value), eid, "%s  %s  ->  %s" % (eid, value, gloss))

    # ---------------------------------------------------------------- 8
    def single(self):
        for eid, table, column, sel, old, new, why in SINGLE:
            e = self.page.db.get(eid)
            if e is None:
                self.skip("8 single values", eid, "entry not found")
                continue
            if new is not None and not self.page.has(eid, new):
                self.skip("8 single values", eid, "%s: the new value is not on the page; not changed" % new)
                continue
            if table == "additional_forms":
                forms = json.loads(e["additional_forms"] or "[]")
                idx = [n for n, f in enumerate(forms) if isinstance(f, dict) and f.get("form") == old]
                if idx:
                    self.set_value("8 single values", e, "lexical_entries", eid, "additional_forms", old, new, idx[0], why)
                elif not any(isinstance(f, dict) and f.get("form") == new for f in forms):
                    self.skip("8 single values", eid, "additional form %s not found" % old)
                continue
            if table == "glosses":
                rows = [g for g in e["glosses"] if g["sense_number"] == sel]
                key = "id"
            else:
                rows = [x for x in e[{"examples": "examples", "etymology": "etymology"}[table]] if x[column] == old]
                key = "id"
            if not rows:
                if not self.conn.execute('select 1 from "%s" where entry_id=? and %s is ?' % (table, column), (eid, new)).fetchone():
                    self.skip("8 single values", eid, "%s.%s: %s not found" % (table, column, old))
                continue
            r = rows[0]
            if r[column] == new or (old is not None and r[column] != old):
                continue
            if table == "etymology" and column == "raw_etymology" and r[column].startswith("<") and not str(new).startswith("<"):
                new = "<%s>" % new
            self.op("8 single values", 'update "%s" set %s=? where id=?' % (table, column), (new, r[key]), eid,
                    "%s  %s.%s: %s  ->  %s   (%s)" % (eid, table, column, r[column], new, why))
            r[column] = new
        for eid, language, form, why in NEW_COGNATES:
            if self.conn.execute("select 1 from cognates where entry_id=? and form=?", (eid, form)).fetchone():
                continue
            if not self.page.has(eid, form):
                self.skip("8 single values", eid, "cognate %s not on the page" % form)
                continue
            self.op("8 single values", "insert into cognates (entry_id, language, form) values (?,?,?)", (eid, language, form), eid,
                    "%s  cognate added: %s %s   (%s)" % (eid, language, form, why))

    # ---------------------------------------------------------------- 9
    def not_printed(self):
        for eid in FORMS_NOT_PRINTED:
            for f in self.page.db[eid]["forms"]:
                numbered = "%s. %s" % (f["form_number"], f["skiri_form"])
                if self.page.has(eid, numbered):
                    continue
                self.op("9 not printed", "delete from paradigmatic_forms where id=?", (f["id"],), eid,
                        "%s  form %s removed: %s   (the page prints no numbered forms for this noun)" % (eid, f["form_number"], f["skiri_form"]))
        for eid, e in self.page.db.items():
            if not e["additional_forms"] or eid not in self.page.pairs:
                continue
            forms = json.loads(e["additional_forms"])
            keep = []
            for f in forms:
                note = cc.skeleton((f.get("form") or "").strip("[]")) if isinstance(f, dict) else ""
                if isinstance(f, dict) and f.get("form_type") in MADE_UP_FORM_TYPES and note and note in cc.skeleton(e["stem_preverb"] or ""):
                    continue
                keep.append(f)
            if len(keep) != len(forms):
                new = json.dumps(keep, ensure_ascii=False) if keep else None
                self.op("9 not printed", "update lexical_entries set additional_forms=? where entry_id=?", (new, eid), eid,
                        "%s  additional form removed: %s   (the bracket note is stored with the preverb: %s)" % (
                            eid, e["additional_forms"], e["stem_preverb"]))
                e["additional_forms"] = new

    # ---------------------------------------------------------------- 10
    def punctuation(self):
        def despace(s):
            s = re.sub(r"[ \t]+", " ", s)
            s = re.sub(r" +(?!\.\.\.)([,;:.!?)\]}])", r"\1", s)
            s = re.sub(r"([(\[{]) +", r"\1", s)
            return s.strip()
        pending = {}
        for section, sql, params, eid, line in self.ops:      # values this run already rewrites
            m = re.match(r'update "?(\w+)"? set (\w+)=\? where id=\?', sql)
            if m:
                pending[(m.group(1), m.group(2), params[1])] = params[0]
        for table, columns in (("glosses", ("definition", "usage_notes")), ("examples", ("english_translation", "usage_context")),
                               ("etymology", ("literal_translation",))):
            where = " and coalesce(source, 'parks_dictionary') = 'parks_dictionary'" if table == "examples" else ""
            for column in columns:
                for row, eid, value in self.conn.execute('select id, entry_id, %s from "%s" where %s is not null%s' % (column, table, column, where)).fetchall():
                    if eid not in self.page.pairs:
                        continue
                    value = pending.get((table, column, row), value)
                    if value is None:
                        continue
                    new = despace(value)
                    if new == value or cc.skeleton(new) != cc.skeleton(value):
                        continue
                    self.op("10 punctuation", 'update "%s" set %s=? where id=?' % (table, column), (new, row), eid,
                            "%s  %s.%s: %s  ->  %s" % (eid, table, column, value, new))


def pieces_follow(plan, pending_raw):
    """Section 11. `pending_raw` maps an etymology row to the raw etymology this run is about to store."""
    for row, eid, raw, const in plan.conn.execute("select id, entry_id, raw_etymology, constituent_elements from etymology "
                                                  "where constituent_elements is not null and constituent_elements not in ('', '[]')").fetchall():
        if eid not in plan.page.pairs:
            continue
        raw = pending_raw.get(row, raw) or ""
        try:
            els = json.loads(const)
        except ValueError:
            continue
        changed = []
        for el in els if isinstance(els, list) else []:
            m = el.get("morpheme") if isinstance(el, dict) else None
            if not m or m in raw:
                continue
            a = m.replace("’", "ʔ")
            for v in (a, a.rstrip("-"), a.replace("- ", ""), a.replace("-", ""), re.sub(r"\s+", "", a), re.sub(r"\s+", "", a).replace("-", "")):
                if v and v != m and v in raw:
                    changed.append("%s -> %s" % (m, v))
                    el["morpheme"] = v
                    break
        if changed:
            plan.op("11 pieces", "update etymology set constituent_elements=? where id=?", (json.dumps(els, ensure_ascii=False), row), eid,
                    "%s  %s" % (eid, "; ".join(changed)))


def sync_json(data, conn, touched):
    """Rewrite, in the JSON file, the parts of each touched entry that this script can change."""
    by_id = {e.get("entry_id"): e for e in data}
    n = 0
    for eid in sorted(touched):
        e = by_id.get(eid)
        if e is None:
            continue
        n += 1
        p1, p2 = e.setdefault("part_I", {}), e.setdefault("part_II", {})
        row = conn.execute("select additional_forms from lexical_entries where entry_id=?", (eid,)).fetchone()
        p1.setdefault("grammatical_info", {})["additional_forms"] = json.loads(row[0]) if row and row[0] else []
        glosses = conn.execute("select sense_number, definition, usage_notes from glosses where entry_id=? order by id", (eid,)).fetchall()
        for g, (number, definition, notes) in zip(p1.get("glosses") or [], glosses):
            g["definition"], g["usage_notes"] = definition, notes
        ety = conn.execute("select raw_etymology, literal_translation, constituent_elements from etymology where entry_id=? order by id", (eid,)).fetchone()
        if ety and isinstance(p1.get("etymology"), dict):
            p1["etymology"]["raw_etymology"], p1["etymology"]["literal_translation"] = ety[0], ety[1]
            if ety[2]:
                p1["etymology"]["constituent_elements"] = json.loads(ety[2])
        cogs = conn.execute("select language, form from cognates where entry_id=? order by id", (eid,)).fetchall()
        old = p1.get("cognates") or []
        p1["cognates"] = [dict(old[i] if i < len(old) and isinstance(old[i], dict) else {"gloss": None}, language=lang, form=form)
                          for i, (lang, form) in enumerate(cogs)]
        forms = dict(conn.execute("select form_number, skiri_form from paradigmatic_forms where entry_id=?", (eid,)).fetchall())
        if isinstance(p2.get("paradigmatic_forms"), dict):
            for k in range(1, 6):
                if "form_%d" % k in p2["paradigmatic_forms"] or k in forms:
                    p2["paradigmatic_forms"]["form_%d" % k] = forms.get(k)
        exs = conn.execute("select skiri_text, english_translation, usage_context from examples where entry_id=? "
                           "and coalesce(source, 'parks_dictionary') = 'parks_dictionary' order by id", (eid,)).fetchall()
        p2["examples"] = [{"skiri_text": s, "english_translation": t, "usage_context": c} for s, t, c in exs]
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the database, the JSON and the report")
    ap.add_argument("--show", type=int, default=6, help="lines to show per section in a dry run")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB))
    page = Page(DB)
    plan = Plan(page, conn)
    plan.derived_stems()
    plan.examples()
    plan.single()
    plan.from_the_page()
    plan.not_printed()
    plan.punctuation()
    pending_raw = {params[1]: params[0] for section, sql, params, eid, line in plan.ops
                   if sql.startswith('update "etymology" set raw_etymology')}
    pieces_follow(plan, pending_raw)

    header = ["What the dictionary prints and the database lacked: set from the PDF text layer",
              "run: %s%s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "" if args.apply else " (dry run)"), ""]
    sections = sorted(plan.count, key=lambda s: int(s.split()[0]))
    header += ["%6d  %s" % (plan.count[s], s) for s in sections]
    header += ["%6d  changes in all, in %d entries" % (sum(plan.count.values()), len(plan.touched)), ""]
    body = []
    for s in sections:
        body += ["", "== %s (%d) ==" % (s, plan.count[s])] + ["   " + line for sec, sql, params, eid, line in plan.ops if sec == s]
    body += ["", "== not done, with the reason (%d) ==" % len(plan.notes)] + ["   %s  %s  %s" % n for n in plan.notes]
    body += ["", "== left as they are (%d) ==" % len(LEFT)] + ["   %s  %s.%s: %s" % l for l in LEFT]

    if not args.apply:
        out("\n".join(header))
        for s in sections:
            lines = [line for sec, sql, params, eid, line in plan.ops if sec == s]
            out("== %s (%d) ==" % (s, len(lines)))
            for line in lines[:args.show]:
                out("   " + line[:230])
        out("== not done (%d) ==" % len(plan.notes))
        for n in plan.notes[:40]:
            out(("   %s  %s  %s" % n)[:260])
        out("")
        out("dry run: nothing was changed and no report was written (use --apply)")
        return
    if not plan.ops:
        out("\n".join(header))
        out("nothing to change; nothing written")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
    backups.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB, backups / ("skiri_pawnee_backup_%s_print.db" % stamp))
    shutil.copy2(S2E_JSON, backups / ("%s_backup_%s%s" % (S2E_JSON.stem, stamp, S2E_JSON.suffix)))
    for section, sql, params, eid, line in plan.ops:
        conn.execute(sql, params)
    conn.commit()
    data = json.loads(S2E_JSON.read_text(encoding="utf-8"))
    n_json = sync_json(data, conn, plan.touched)
    S2E_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    conn.close()
    header += ["%s: %d entries brought in step" % (S2E_JSON.name, n_json), "backups: OneDrive/pari_pakuru_backups (stamp %s)" % stamp]
    text = "\n".join(header + body) + "\n"
    if REPORT.exists():            # the record of an earlier run is kept; this run is added below it
        text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    out("\n".join(header))
    out("report: %s" % REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
