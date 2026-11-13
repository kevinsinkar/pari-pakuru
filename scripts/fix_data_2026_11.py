#!/usr/bin/env python3
"""
Data fixes of 2026-11-13
========================

Applies the errors found by the word-construction analysis
(curriculum/roots_v2/proposed_data_fixes.json) and the ones found while
checking those against the printed pages. Every change here was checked against
a page image of the dictionary, or follows mechanically from the PDF's own text
layer. The report lists each change with its old and new value.

  1. Page numbers.   28 kaa... entries are labelled page 2 but are printed on
                     book page 419 (page_071.pdf).
  2. Letter-spaced text.  Justified lines came through as "c l o s e  u p":
                     13 glosses, 12 example translations, 14 etymologies.
  3. Duplicate rows. Six kaa... entries exist twice (ids -p2- and -p71-). The
                     -p2- row is kept, as in scripts/dedup_entries.py; the two
                     fields where the -p71- copy is the clean one are taken
                     from it; English-index links are moved; the copy is deleted.
  4. Two single entries.  caʔuuhtuʔ: etymology and cognates as printed.
                     ciihtahaahiriʔ: "(contemp.)" is a usage label, not a verb class.
  5. Accent marks that the character decoding dropped.
                     The PDF text layer encodes Parks's accented u's with the
                     characters ÷ and Š. Earlier steps read ÷ as a length mark
                     (ː) and Š as plain ʊ. On the page ÷ is ú (as in huú) and
                     Š is ʊ́. Parks never prints ː. Four rare characters were
                     also misread: ˆ and ç are ì, ø is ù, Ò is à.
                     Phonetic forms are corrected position by position from the
                     text layer and the respelling is regenerated, so that the
                     accented syllable is shown. ÷ left in etymologies, cognates
                     and the English index becomes ú.
                     (Parks, p. 15: stress is not phonemic in Skiri, but the
                     phonetic forms mark the accented syllable.)

NOT changed here (left for a full audit of the character table): Parks's
accented short a and i are printed ə́ and ɪ́; the database writes them à and í.
The accent is kept, only the symbol differs.

Usage:
    python scripts/fix_data_2026_11.py            # dry run: prints what it would do, writes nothing
    python scripts/fix_data_2026_11.py --apply    # backs up, then writes DB + JSON + frozen flashcards + the report

The fixes were applied on 2026-11-13. Run again, the script finds nothing left to do.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from dedup_entries import CHILD_TABLES  # noqa: E402
from fix_pronunciations import respell_phonetic  # noqa: E402

DB = ROOT / "skiri_pawnee.db"
S2E_JSON = ROOT / "Dictionary Data" / "skiri_to_english_respelled.json"
E2S_JSON = ROOT / "Dictionary Data" / "english_to_skiri_linked.json"
FROZEN_SETS = ROOT / "curriculum" / "flashcard_sets.json"
PAGE_DIR = ROOT / "Dictionary Data" / "split_pdf_pages_SKIRI_TO_ENGLISH"
PAGE_INDEX = ROOT / "reports" / "_s2e_page_index.json"
REPORT = ROOT / "reports" / "fix_data_2026-11-13_report.txt"

ACUTE = "́"

# --------------------------------------------------------------------------- 2. letter-spaced text
# (id, text that must be present now, replacement). Glosses were read from the page image
# (book p. 506); the example translations and etymology glosses are plain English.
GLOSS_FIXES = [
    (3898, "c l o s e  u p ,  c l o s e  t o - gether, shut,", "close up, close together, shut,"),
    (3899, "g a t h e r  t o g e t h e r, as", "gather together, as"),
    (3900, "g a t h e r into", "gather into"),
    (3913, "c a r r y  a  l o a d ,  a  b u n d l e  o n one's back.", "carry a load, a bundle on one's back."),
    (7741, "s h a k e ,  s h i v e r , tremble;", "shake, shiver, tremble;"),
    (7742, "c r i c k e t .", "cricket."),
    (7743, "b u n c h ,  g r o u p, as", "bunch, group, as"),
    (7749, "o n  o n e ' s  b a c k, said", "on one's back, said"),
    (7751, "c a r r y ,  p a c k  o n  o n e ' s back.", "carry, pack on one's back."),
    (7753, "f l o u r ;  p o w d e r ;  m e a l ,  a n y  f i n e l y ground", "flour; powder; meal, any finely ground"),
    (7755, "w h i t e  f l o u r , bleached", "white flour, bleached"),
    (7757, "g r o u n d  c o r n , cornmeal.", "ground corn, cornmeal."),
    (7759, "o f t e n ;  a l l  t h e  t i m e ,  a l w a y s .", "often; all the time, always."),
]
EXAMPLE_FIXES = [
    (1208, "t h e  g l a s s  i s  d e c o r a t e d ,  h a s  a  colored", "the glass is decorated, has a colored"),
    (1211, "p i g l e t ,  s h o a t .", "piglet, shoat."),
    (1460, "C h i e f l y  W a r r i o r", "Chiefly Warrior"),
    (1803, "i t  i s  a  b u n c h .", "it is a bunch."),
    (1806, "i s  i t  s o m e o n e ?", "is it someone?"),
    (2168, "I a m r e a l l y disappointed", "I am really disappointed"),
    (2458, "h e  h a s  h e a r t  d i s - ease.", "he has heart disease."),
    (2463, "I  t h r e w  i t with", "I threw it with"),
    (2464, "b l a c k  g e l d i n g .", "black gelding."),
    (2468, "a m o n g  t h e  c h i l d r e n .", "among the children."),
    (2469, "child  ( c a .  t w o  t o  t h r e e  y e a r s  o f  a g e ).", "child (ca. two to three years of age)."),
    (2472, "a m o n g  t h e  b o y s .", "among the boys."),
]
ETYMOLOGY_FIXES = [
    (1558, "b e  s m o o t h ,  h a i r l e s s ,  A r .  ", "be smooth, hairless, Ar. "),
    (1762, "s n i p e  ( l i t t l e  b i r d ,  l o n g  l e g s ,  l o n g  b e a k ,  along", "snipe (little bird, long legs, long beak, along"),
    (1831, "h u n t i n g party", "hunting party"),
    (1835, "b l o w o n ; neswaanun", "blow on; neswaanun"),
    (1835, "l a r g e i n t e s t i n e c a s - ing", "large intestine casing"),
    (2362, "g o  a  c e r t a i n  d i s- tance", "go a certain distance"),
    (2469, "PL +  b e  m i x e d ;  i . q .  wiriis", "PL + be mixed; i.q. wiriis"),
    (2470, "m y  c h i l d r e n ,  a  prominent", "my children, a prominent"),
    (2554, "riir + o n t o p ; i . q . S B reehkita", "riir + on top; i.q. SB reehkita"),
    (2754, "t a k e  o u t  a n d  o t h e r  e x t r a c -tion", "take out and other extraction"),
    (2800, "DIST +  e x i s t ;  r e f .  t o  fruit", "DIST + exist; ref. to fruit"),
    (3075, "s h a d o w ,  A r .  ookaʔaási b e  shady", "shadow, Ar. ookaʔaási be shady"),
    (3119, "ITER +  v o i c e  t o  travel", "ITER + voice to travel"),
    (3687, "c o c k l e - bur", "cocklebur"),
    (3758, "c o r n  t o  h a v e  k e r n e l s ;  c o r n  t o  r i p e n ,  get", "corn to have kernels; corn to ripen, get"),
]

# --------------------------------------------------------------------------- 3. duplicate rows
# (kept, deleted). The pairs are identical in headword, IPA, class, verb class, forms, examples,
# cognates and tags; they differ only in line-break and spacing artifacts.
DUPLICATES = [
    ("SK-kaackaraaruq-p2-0020", "SK-kaackaraaruq-p71-1267"),
    ("SK-kaahak-p2-0023", "SK-kaahak-p71-1270"),
    ("SK-kaaqaah-p2-0003", "SK-kaaqaah-p71-1250"),
    ("SK-kaaqat-p2-0009", "SK-kaaqat-p71-1256"),
    ("SK-kaaqat-p2-0010", "SK-kaaqat-p71-1257"),
    ("SK-kaaqihwicat-p2-0012", "SK-kaaqihwicat-p71-1259"),
]
MUST_MATCH = ("headword", "phonetic_form", "grammatical_class", "verb_class", "stem_preverb")

# --------------------------------------------------------------------------- 5. character table
# raw text-layer character -> what earlier steps wrote -> what the page prints
OLD_TABLE = {"ß": "ə", "†": "ɪ", "‰": "ʊ", "™": "ʔ", "Ù": "č", "à": "à", "‡": "í", "Ñ": "á", "æ": "í",
             "÷": "ː", "Š": "ʊ", "ˆ": "ɪ", "ç": "ʔ", "ø": "ː", "Ò": "a", "á": "á"}
RESTORE = {"÷": "ú", "Š": "ʊ" + ACUTE, "ˆ": "ì", "ç": "ì", "ø": "ù", "Ò": "à"}
SEPARATORS = set(" \t•-–—.[]")


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def content_key(s):
    return "".join(ch for ch in nfc(s) if ch not in SEPARATORS)


def raw_bracket_forms():
    """Every bracketed form in the text layer of the Skiri-to-English pages, undecoded."""
    import fitz  # PyMuPDF
    forms = []
    for n in range(1, 182):
        text = fitz.open(str(PAGE_DIR / ("page_%03d.pdf" % n)))[0].get_text()
        forms.extend(re.findall(r"\[[^\]\n]{1,70}\]", text))
    return forms


def restore_accents(db_form, raw):
    """Walk the stored form and the raw form together; replace only the misread characters."""
    raw_content = [ch for ch in raw if ch not in SEPARATORS]
    res, i = [], 0
    for ch in nfc(db_form):
        if ch in SEPARATORS:
            res.append(ch)
            continue
        r = raw_content[i]
        i += 1
        res.append(RESTORE.get(r, ch))
    assert i == len(raw_content)
    return "".join(res)


class Fixer:
    def __init__(self, conn):
        self.conn = conn
        self.log = []          # report lines
        self.sql = []          # (statement, params)
        self.counts = Counter()
        # what the JSON and the frozen flashcards need to hear about
        self.entry_updates = {}     # entry_id -> {field: (old, new)}
        self.gloss_updates = []     # (entry_id, old, new)
        self.example_updates = []   # (entry_id, old, new)
        self.etym_updates = []      # (entry_id, old, new)
        self.cognate_updates = []   # (entry_id, language, old, new)
        self.relinks = {}           # deleted id -> kept id

    def say(self, line=""):
        self.log.append(line)

    def entry(self, eid, field, old, new):
        self.entry_updates.setdefault(eid, {})[field] = (old, new)

    # ----------------------------------------------------------------- 1
    def page_numbers(self):
        self.say("== 1. Page numbers (stored 2, printed on book page 419) ==")
        idx = json.loads(PAGE_INDEX.read_text(encoding="utf-8"))
        t350, t419 = idx["350"]["text"], idx["419"]["text"]

        def at_line_start(text, hw):
            return re.search(r"(?m)^\s*(?:• )?%s(?=[\s\[(,])" % re.escape(hw), text) is not None
        doomed = {b for _, b in DUPLICATES}
        for eid, hw in self.conn.execute("select entry_id, headword from lexical_entries where page_number=2 order by entry_id"):
            h = nfc(hw).split(",")[0].strip()
            if at_line_start(t419, h) and not at_line_start(t350, h) and eid not in doomed:
                self.sql.append(("update lexical_entries set page_number=419 where entry_id=? and page_number=2", (eid,)))
                self.entry(eid, "page_number", 2, 419)
                self.say("  %-40s %s: 2 -> 419" % (eid, h))
                self.counts["page numbers"] += 1
        self.say()

    # ----------------------------------------------------------------- 2
    def _substring(self, table, column, label, fixes, sink):
        self.say("== 2. Letter-spaced text: %s ==" % label)
        current = {}
        for row_id, old_part, new_part in fixes:
            if row_id not in current:
                row = self.conn.execute("select entry_id, %s from %s where id=?" % (column, table), (row_id,)).fetchone()
                if row is None:
                    self.say("  SKIPPED %s %s: row not found" % (table, row_id))
                    continue
                current[row_id] = [row[0], row[1], row[1]]
            eid, original, value = current[row_id]
            if value.count(old_part) != 1:
                self.say("  SKIPPED %s %s: expected text not found once: %r" % (table, row_id, old_part))
                continue
            current[row_id][2] = value.replace(old_part, new_part)
        for row_id, (eid, original, value) in current.items():
            if value == original:
                continue
            self.sql.append(("update %s set %s=? where id=? and %s=?" % (table, column, column), (value, row_id, original)))
            sink.append((eid, original, value))
            self.say("  %s %s (%s)\n      old: %s\n      new: %s" % (table, row_id, eid, original, value))
            self.counts["letter-spaced " + label] += 1
        self.say()

    def letter_spacing(self):
        self._substring("glosses", "definition", "glosses", GLOSS_FIXES, self.gloss_updates)
        self._substring("examples", "english_translation", "example translations", EXAMPLE_FIXES, self.example_updates)
        self._substring("etymology", "raw_etymology", "etymologies", ETYMOLOGY_FIXES, self.etym_updates)

    # ----------------------------------------------------------------- 3
    def duplicates(self):
        self.say("== 3. Duplicate rows (kept the -p2- row, deleted the -p71- copy) ==")
        cols = ", ".join(MUST_MATCH)
        for keep, drop in DUPLICATES:
            a = self.conn.execute("select %s from lexical_entries where entry_id=?" % cols, (keep,)).fetchone()
            b = self.conn.execute("select %s from lexical_entries where entry_id=?" % cols, (drop,)).fetchone()
            if a is None or b is None:
                self.say("  SKIPPED %s / %s: a row is missing (already merged?)" % (keep, drop))
                continue
            forms = [self.conn.execute("select form_number, skiri_form from paradigmatic_forms where entry_id=? order by 1, 2", (x,)).fetchall()
                     for x in (keep, drop)]
            exs = [sorted(self.conn.execute("select skiri_text, english_translation from examples where entry_id=?", (x,)).fetchall())
                   for x in (keep, drop)]
            if a != b or forms[0] != forms[1] or exs[0] != exs[1]:
                self.say("  SKIPPED %s / %s: the two rows are not the same word" % (keep, drop))
                continue
            self.say("  %s  <-  %s  (%s)" % (keep, drop, a[0]))
            # the two fields where the copy is the clean one (both read from the page image, book p. 419)
            if keep == "SK-kaackaraaruq-p2-0020":
                old = self.conn.execute("select raw_etymology from etymology where entry_id=?", (keep,)).fetchone()[0]
                new, ce = self.conn.execute("select raw_etymology, constituent_elements from etymology where entry_id=?", (drop,)).fetchone()
                if old != new:
                    self.sql.append(("update etymology set raw_etymology=?, constituent_elements=? where entry_id=?", (new, ce, keep)))
                    self.etym_updates.append((keep, old, new))
                    self.say("      etymology: %s -> %s   (line-break hyphen)" % (old, new))
            if keep == "SK-kaaqat-p2-0009":
                old = self.conn.execute("select definition from glosses where entry_id=?", (keep,)).fetchone()[0]
                new = self.conn.execute("select definition from glosses where entry_id=?", (drop,)).fetchone()[0]
                if old != new:
                    self.sql.append(("update glosses set definition=? where entry_id=? and definition=?", (new, keep, old)))
                    self.gloss_updates.append((keep, old, new))
                    self.say("      gloss: %s -> %s   (line-break hyphen)" % (old, new))
            self.relinks[drop] = keep
            self.counts["duplicate rows removed"] += 1
        # an English-index row still points at a -p71- row that was deleted in March 2026
        for row_id, eid, word in self.conn.execute("select id, entry_id, english_word from english_index where entry_id like '%-p71-%'").fetchall():
            if eid in self.relinks:
                continue
            m = re.match(r"(SK-.+)-p71-(\d+)$", eid)
            twin = "%s-p2-%04d" % (m.group(1), int(m.group(2)) - 1247) if m else None
            if twin and self.conn.execute("select 1 from lexical_entries where entry_id=?", (twin,)).fetchone() \
                    and not self.conn.execute("select 1 from lexical_entries where entry_id=?", (eid,)).fetchone():
                self.relinks[eid] = twin
                self.say("  dangling English-index link (%s): %s -> %s" % (word, eid, twin))
        for drop, keep in self.relinks.items():
            n = self.conn.execute("select count(*) from english_index where entry_id=?", (drop,)).fetchone()[0]
            if n:
                self.sql.append(("update english_index set entry_id=? where entry_id=?", (keep, drop)))
                self.say("      %d English-index link(s) moved: %s -> %s" % (n, drop, keep))
                self.counts["English-index links moved"] += n
            for table in ("blue_book_attestations", "community_feedback", "semantic_tags"):
                # semantic tags are identical on both rows; anything else attached to the copy moves to the kept row
                if table == "semantic_tags":
                    continue
                try:
                    k = self.conn.execute("select count(*) from %s where entry_id=?" % table, (drop,)).fetchone()[0]
                except sqlite3.OperationalError:
                    k = 0
                if k:
                    self.sql.append(("update %s set entry_id=? where entry_id=?" % table, (keep, drop)))
                    self.say("      %d %s row(s) moved" % (k, table))
        for keep, drop in DUPLICATES:
            if drop not in self.relinks:
                continue
            for table in CHILD_TABLES:
                if table in ("english_index", "blue_book_attestations", "community_feedback"):
                    continue
                try:
                    self.conn.execute("select 1 from %s limit 1" % table)
                except sqlite3.OperationalError:
                    continue
                self.sql.append(("delete from %s where entry_id=?" % table, (drop,)))
            self.sql.append(("delete from lexical_entries where entry_id=?", (drop,)))
        self.say()

    # ----------------------------------------------------------------- 4
    def single_entries(self):
        self.say("== 4. Two entries read against the page image ==")
        eid = "SK-caquuhtuq-p26-0357"
        old = self.conn.execute("select raw_etymology from etymology where entry_id=?", (eid,)).fetchone()[0]
        new = old.replace("SB caʔuk-tuʔ", "SB caʔuktuʔ").replace("saʔ÷htuʔ", "saʔúhtuʔ")
        if new != old:
            self.sql.append(("update etymology set raw_etymology=? where entry_id=? and raw_etymology=?", (new, eid, old)))
            self.etym_updates.append((eid, old, new))
            self.say("  %s etymology\n      old: %s\n      new: %s" % (eid, old, new))
            self.counts["single-entry fixes"] += 1
        for lang, o, n in (("SB", "caʔuk-tuʔ", "caʔuktuʔ"), ("Ar", "saʔ÷htuʔ", "saʔúhtuʔ")):
            if self.conn.execute("select 1 from cognates where entry_id=? and language=? and form=?", (eid, lang, o)).fetchone():
                self.sql.append(("update cognates set form=? where entry_id=? and language=? and form=?", (n, eid, lang, o)))
                self.cognate_updates.append((eid, lang, o, n))
                self.say("  %s cognate %s: %s -> %s" % (eid, lang, o, n))
        eid = "SK-ciihtahaahiriq-p29-0435"
        row = self.conn.execute("select verb_class from lexical_entries where entry_id=?", (eid,)).fetchone()
        if row and row[0] == "(contemp.)":
            self.sql.append(("update lexical_entries set verb_class=NULL where entry_id=? and verb_class='(contemp.)'", (eid,)))
            self.entry(eid, "verb_class", "(contemp.)", None)
            gid, definition = self.conn.execute("select id, definition from glosses where entry_id=? order by id limit 1", (eid,)).fetchone()
            if not definition.startswith("(contemp.)"):
                new_def = "(contemp.) " + definition
                self.sql.append(("update glosses set definition=? where id=? and definition=?", (new_def, gid, definition)))
                self.gloss_updates.append((eid, definition, new_def))
            self.say("  %s: verb class '(contemp.)' removed (the entry is an adverb); the label is put back in front of the gloss, where the page has it" % eid)
            self.counts["single-entry fixes"] += 1
        self.say()

    # ----------------------------------------------------------------- 5
    def accents(self):
        self.say("== 5. Accent marks restored (raw ÷ is ú, raw Š is ʊ́; ˆ and ç are ì, ø is ù, Ò is à) ==")
        by_key = {}
        for raw in raw_bracket_forms():
            decoded = "".join(OLD_TABLE.get(ch, ch) for ch in raw)
            by_key.setdefault(content_key(decoded), set()).add(raw)
        rows = self.conn.execute("""select entry_id, headword, phonetic_form, simplified_pronunciation from lexical_entries
                                    where phonetic_form is not null and phonetic_form<>'' and source is null order by entry_id""").fetchall()
        doomed = {b for _, b in DUPLICATES}
        unmatched_with_length = []
        for eid, hw, pf, sp in rows:
            if eid in doomed:
                continue
            raws = by_key.get(content_key(pf))
            if not raws:
                if "ː" in pf:
                    unmatched_with_length.append((eid, hw, pf, sp))
                continue
            candidates = {restore_accents(pf, raw) for raw in raws}
            if len(candidates) != 1:
                self.say("  SKIPPED %s %s: the text layer has two different forms for it" % (eid, pf))
                self.counts["accents skipped (ambiguous)"] += 1
                continue
            new_pf = candidates.pop()
            if new_pf != nfc(pf):
                self._accent_change(eid, hw, pf, new_pf, sp, "text layer")
        for eid, hw, pf, sp in unmatched_with_length:
            # Parks prints no length mark; every ː came from ÷
            self._accent_change(eid, hw, pf, nfc(pf).replace("ː", "ú"), sp, "rule: ː is ú")
        # ÷ left in other fields is the same glyph
        for eid, old in self.conn.execute("select entry_id, raw_etymology from etymology where raw_etymology like '%÷%'").fetchall():
            pending = [n for e, o, n in self.etym_updates if e == eid]
            cur = pending[-1] if pending else old
            if "÷" not in cur or "Kiowa" in cur:      # the one Kiowa citation is left for a look at the page
                continue
            new = cur.replace("÷", "ú")
            if pending:
                self.sql.append(("update etymology set raw_etymology=? where entry_id=?", (new, eid)))
                self.etym_updates = [(e, o, (new if e == eid and n == cur else n)) for e, o, n in self.etym_updates]
            else:
                self.sql.append(("update etymology set raw_etymology=? where entry_id=? and raw_etymology=?", (new, eid, old)))
                self.etym_updates.append((eid, old, new))
            self.say("  etymology %s: %s -> %s" % (eid, cur, new))
            self.counts["÷ -> ú in etymologies"] += 1
        for eid, old in self.conn.execute("select entry_id, constituent_elements from etymology where constituent_elements like '%÷%'").fetchall():
            if "Kiowa" in old:
                continue
            self.sql.append(("update etymology set constituent_elements=? where entry_id=? and constituent_elements=?", (old.replace("÷", "ú"), eid, old)))
            self.counts["÷ -> ú in constituent_elements"] += 1
        for cid, eid, lang, form in self.conn.execute("select id, entry_id, language, form from cognates where form like '%÷%'").fetchall():
            if any(e == eid and o == form for e, _, o, _ in self.cognate_updates):
                continue
            new = form.replace("÷", "ú")
            self.sql.append(("update cognates set form=? where id=? and form=?", (new, cid, form)))
            self.cognate_updates.append((eid, lang, form, new))
            self.say("  cognate %s %s: %s -> %s" % (eid, lang, form, new))
            self.counts["÷ -> ú in cognates"] += 1
        for rid, pf in self.conn.execute("select id, phonetic_form from english_index where phonetic_form like '%÷%' or phonetic_form like '%ː%'").fetchall():
            self.sql.append(("update english_index set phonetic_form=? where id=? and phonetic_form=?", (pf.replace("÷", "ú").replace("ː", "ú"), rid, pf)))
            self.counts["÷ -> ú in English-index IPA"] += 1
        self.say()

    def _accent_change(self, eid, hw, pf, new_pf, sp, basis):
        new_sp = respell_phonetic(new_pf)
        # regenerate only when the present respelling is what the present IPA gives, so nothing unrelated moves
        if sp is not None and respell_phonetic(pf) != sp:
            self.say("  NOTE %s: respelling %r is not what its IPA gives (%r); IPA corrected, respelling left alone" % (eid, sp, respell_phonetic(pf)))
            new_sp = sp
            self.counts["accents: respelling left alone"] += 1
        self.sql.append(("update lexical_entries set phonetic_form=?, simplified_pronunciation=? where entry_id=? and phonetic_form=?",
                         (new_pf, new_sp, eid, pf)))
        self.entry(eid, "phonetic_form", pf, new_pf)
        if new_sp != sp:
            self.entry(eid, "simplified_pronunciation", sp, new_sp)
        self.say("  %-26s %-32s -> %-32s %s -> %s   [%s]" % (nfc(hw)[:26], pf, new_pf, sp, new_sp, basis))
        self.counts["accent marks restored"] += 1
        if not re.search("[áíúàìù]", pf):
            self.counts["  of which had no accent mark at all"] += 1

    # ----------------------------------------------------------------- JSON and frozen flashcards
    def sync_files(self, apply):
        self.say("== Files kept in step ==")
        s2e = json.loads(S2E_JSON.read_text(encoding="utf-8"))
        n = Counter()
        gl = {}
        for eid, old, new in self.gloss_updates:
            gl.setdefault(eid, []).append((old, new))
        et = {eid: (old, new) for eid, old, new in self.etym_updates}
        cg = {}
        for eid, lang, old, new in self.cognate_updates:
            cg.setdefault(eid, []).append((old, new))
        ex = {}
        for eid, old, new in self.example_updates:
            ex.setdefault(eid, []).append((old, new))
        for e in s2e:
            eid = e.get("entry_id")
            p1 = e.get("part_I") or {}
            up = self.entry_updates.get(eid, {})
            if "page_number" in up and (e.get("entry_metadata") or {}).get("page_number") == up["page_number"][0]:
                e["entry_metadata"]["page_number"] = up["page_number"][1]; n["page_number"] += 1
            for field in ("phonetic_form", "simplified_pronunciation"):
                if field in up and p1.get(field) == up[field][0]:
                    p1[field] = up[field][1]; n[field] += 1
            if "verb_class" in up and (p1.get("grammatical_info") or {}).get("verb_class") == up["verb_class"][0]:
                p1["grammatical_info"]["verb_class"] = up["verb_class"][1]; n["verb_class"] += 1
            for old, new in gl.get(eid, []):
                for g in p1.get("glosses") or []:
                    if g.get("definition") == old:
                        g["definition"] = new; n["glosses"] += 1
            if eid in et and (p1.get("etymology") or {}).get("raw_etymology") == et[eid][0]:
                p1["etymology"]["raw_etymology"] = et[eid][1]; n["etymology"] += 1
            for old, new in cg.get(eid, []):
                for cgn in p1.get("cognates") or []:
                    if cgn.get("form") == old:
                        cgn["form"] = new; n["cognates"] += 1
            for old, new in ex.get(eid, []):
                for x in (e.get("part_II") or {}).get("examples") or []:
                    if x.get("english_translation") == old:
                        x["english_translation"] = new; n["examples"] += 1
        # ÷ and the length mark it was turned into are both ú wherever they are left (Parks prints no ː)
        def blanket(obj, counter, skip=("raw_entry_json",)):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        if ("÷" in value or "ː" in value) and "Kiowa" not in value:
                            obj[key] = value.replace("÷", "ú").replace("ː", "ú"); counter["÷ or ː -> ú (%s)" % key] += 1
                    else:
                        blanket(value, counter)
            elif isinstance(obj, list):
                for item in obj:
                    blanket(item, counter)
        blanket(s2e, n)
        self.say("  %s: %s" % (S2E_JSON.name, dict(n) or "nothing to change"))
        e2s = json.loads(E2S_JSON.read_text(encoding="utf-8"))
        m = Counter()
        known = {r[0]: r[1] for r in self.conn.execute("select entry_id, headword from lexical_entries")}
        for e in e2s:
            for sub in e.get("subentries") or []:
                sid = sub.get("s2e_entry_id")
                if sid in self.relinks:
                    sub["s2e_entry_id"] = self.relinks[sid]; m["links moved"] += 1
                elif sid and sid not in known and "-p71-" in sid:
                    # a link that was left pointing at a -p71- row deleted in March 2026
                    mt = re.match(r"(SK-.+)-p71-(\d+)$", sid)
                    twin = "%s-p2-%04d" % (mt.group(1), int(mt.group(2)) - 1247) if mt else None
                    if twin in known and nfc(known[twin]) == nfc((sub.get("part_I") or {}).get("skiri_term")):
                        sub["s2e_entry_id"] = twin; m["dangling links repaired"] += 1
                        self.say("  dangling link repaired: %s (%s) %s -> %s" % (e.get("english_entry_word"), known[twin], sid, twin))
                        if apply:
                            self.conn.execute("""update english_index set entry_id=?, s2e_match_type=? where english_word=? and subentry_number=?
                                                 and entry_id is null and skiri_term=?""",
                                              (twin, sub.get("s2e_match_type"), e.get("english_entry_word"), sub.get("subentry_number"), known[twin]))
                            self.conn.commit()
                p1 = sub.get("part_I") or {}
                pf = p1.get("phonetic_form")
                up = self.entry_updates.get(sub.get("s2e_entry_id"), {})
                if pf and "phonetic_form" in up and nfc(pf) == nfc(up["phonetic_form"][0]):
                    p1["phonetic_form"] = up["phonetic_form"][1]; m["IPA of a linked entry"] += 1
        blanket(e2s, m)
        self.say("  %s: %s" % (E2S_JSON.name, dict(m) or "nothing to change"))
        sets = json.loads(FROZEN_SETS.read_text(encoding="utf-8"))
        k = Counter()
        gloss_by_entry = {}
        for eid, old, new in self.gloss_updates:
            gloss_by_entry.setdefault(eid, []).append((old, new))
        for w in sets["weeks"]:
            for card in w["cards"]:
                up = self.entry_updates.get(card["entry_id"], {})
                for field in ("page_number", "phonetic_form", "simplified_pronunciation"):
                    if field in up and card.get(field) == up[field][0]:
                        card[field] = up[field][1]; k[field] += 1
                for old, new in gloss_by_entry.get(card["entry_id"], []):
                    if card.get("definition") == old:
                        card["definition"] = new; k["definition"] += 1
        self.say("  %s: %s (membership and week numbers unchanged)" % (FROZEN_SETS.name, dict(k) or "nothing to change"))
        self.say()
        if apply:
            S2E_JSON.write_text(json.dumps(s2e, ensure_ascii=False, indent=2), encoding="utf-8")
            E2S_JSON.write_text(json.dumps(e2s, ensure_ascii=False, indent=2), encoding="utf-8")
            # the freeze script's own format (indent 1), so that a repair shows as a small difference
            FROZEN_SETS.write_text(json.dumps(sets, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    before = conn.execute("select count(*) from lexical_entries").fetchone()[0]
    fx = Fixer(conn)
    fx.say("fix_data_2026_11 — %s — %s" % ("APPLY" if args.apply else "DRY RUN", dt.datetime.now().strftime("%Y-%m-%d %H:%M")))
    fx.say()
    fx.page_numbers()
    fx.letter_spacing()
    fx.duplicates()
    fx.single_entries()
    fx.accents()

    if args.apply:
        backup_dir = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        for src in (Path(args.db), S2E_JSON, E2S_JSON, FROZEN_SETS):
            shutil.copy2(src, backup_dir / ("%s_backup_%s%s" % (src.stem, stamp, src.suffix)))
        fx.say("backups written to %s (stamp %s)" % (backup_dir, stamp))
        fx.say()
        with conn:
            for statement, params in fx.sql:
                conn.execute(statement, params)
    fx.sync_files(args.apply)

    after = conn.execute("select count(*) from lexical_entries").fetchone()[0]
    fx.say("== Summary ==")
    for key, value in fx.counts.items():
        fx.say("  %-44s %d" % (key, value))
    fx.say("  %-44s %d -> %d" % ("rows in lexical_entries", before, after if args.apply else before - fx.counts["duplicate rows removed"]))
    out("\n".join(fx.log[-(len(fx.counts) + 12):]))
    if not args.apply:
        # the report file is the record of the applied run: a dry run never writes it
        out("dry run: nothing was changed and no report was written (use --apply)")
        return
    REPORT.write_text("\n".join(fx.log) + "\n", encoding="utf-8", newline="\n")
    out("full report: %s" % REPORT)


if __name__ == "__main__":
    main()
