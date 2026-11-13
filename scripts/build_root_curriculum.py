#!/usr/bin/env python3
"""
Root-first curriculum builder
=============================

Renders three Markdown deliverables from the extraction outputs and the DB:

    curriculum/roots/construction_guide.md
    curriculum/roots/lesson_plans.md
    curriculum/roots/review_log.md

Every Pawnee form in the output is produced by a lookup (dictionary entry,
paradigmatic form, Appendix 1 cell, Blue Book attestation, Parks grammar
example). Prose never spells a form by hand; it calls W(), F(), A() or BB().
Anything that is not attested is labelled "constructed — unverified" by the
C() helper, which the current spec does not use.

Usage:
    python scripts/build_root_curriculum.py            # build all three files
    python scripts/build_root_curriculum.py --check    # only verify spec ids exist
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from root_curriculum_spec import UNITS, GUIDE, REVIEW_MANUAL  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "curriculum" / "roots"


def out(text):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def norm(s):
    if s is None:
        return ""
    return unicodedata.normalize("NFC", s).replace("’", "ʔ").strip()


# ---------------------------------------------------------------------------
# Spelling-based respelling (same sound values as scripts/respell_and_normalize.py,
# Parks Sound Key p. xvii / Blue Book pp. xvii–xxi). Used only where no Parks
# phonetic transcription exists (inflected forms); marked ≈ in the output.
# ---------------------------------------------------------------------------
_VOWEL_MAP = {"aa": "ah", "ii": "ee", "uu": "oo", "a": "uh", "i": "ih", "u": "oo", "e": "eh", "ee": "eh"}
_CONS_MAP = {"r": "d", "c": "ts", "ʔ": "'", "č": "ch", "'": "'"}
_ACCENT = {"á": "a", "í": "i", "ú": "u", "à": "a", "ì": "i", "ù": "u"}
_VOWELS = set("aiue")   # e occurs only in Blue Book spellings


def respell_orthography(form):
    """Parks orthography -> English respelling, syllable by syllable.

    Accented syllables (Parks acute = high pitch) are upper-cased, as in the DB column.
    Variants separated by ',' or ';' are respelled separately.
    """
    outv = []
    for variant in re.split(r"[;,]", form):
        v = re.sub(r"\[.*?\]|\(.*?\)", "", variant).strip().strip("-").strip()
        if not v:
            continue
        chars = []
        for ch in v:
            if ch in _ACCENT:
                chars.append((_ACCENT[ch], True))
            elif ch.lower() in _VOWELS or ch.lower() in "ptkcswhrnʔč'":
                chars.append((ch.lower(), False))
            # anything else (spaces, Ø, digits) is dropped
        syllables, i, n = [], 0, len(chars)
        while i < n:
            onset = []
            while i < n and chars[i][0] not in _VOWELS:
                onset.append(chars[i][0]); i += 1
            if i >= n:
                if syllables:
                    syllables[-1][2].extend(onset)
                else:
                    syllables.append([onset, "", []])
                break
            vowel, accented = chars[i][0], chars[i][1]
            i += 1
            if i < n and chars[i][0] == vowel:
                vowel = vowel * 2; accented = accented or chars[i][1]; i += 1
            run = []
            j = i
            while j < n and chars[j][0] not in _VOWELS:
                run.append(chars[j][0]); j += 1
            if j >= n:
                coda = run; i = j
            elif len(run) >= 2:
                coda = run[:-1]; i += len(coda)
            else:
                coda = []
            syllables.append([onset, vowel, coda, accented])
        parts = []
        for syl in syllables:
            onset, vowel, coda = syl[0], syl[1], syl[2]
            accented = syl[3] if len(syl) > 3 else False
            # Parks Rule 24: c is [ch] before a vowel, [ts] before a consonant or word-finally
            onset_s = "".join(("ch" if (c == "c" and k == len(onset) - 1 and vowel) else _CONS_MAP.get(c, c)) for k, c in enumerate(onset))
            s = onset_s + _VOWEL_MAP.get(vowel, vowel) + "".join(_CONS_MAP.get(c, c) for c in coda)
            parts.append(s.upper() if accented else s)
        outv.append("-".join(parts))
    return " / ".join(outv)


_LONG = {"aa": "â", "ii": "î", "uu": "û"}


def modern_spelling(form):
    """Parks orthography -> learner orthography used in normalized_form:
    aa ii uu -> â î û; ʔ -> '; c -> č before a vowel (Parks Rule 24), c elsewhere.
    Accents are kept: short accented vowels stay (á í ú); an accented long vowel is
    written as the caret vowel plus a combining acute."""
    if not form:
        return form
    outp = []
    i, n = 0, len(form)
    vowels = "aiuáíú"
    while i < n:
        ch = form[i]
        base = {"á": "a", "í": "i", "ú": "u"}.get(ch, ch)
        if base in "aiu" and i + 1 < n and {"á": "a", "í": "i", "ú": "u"}.get(form[i + 1], form[i + 1]) == base:
            accented = ch != base or form[i + 1] != {"á": "a", "í": "i", "ú": "u"}.get(form[i + 1], form[i + 1])
            outp.append(_LONG[base * 2] + ("́" if accented else ""))
            i += 2
            continue
        if ch == "ʔ":
            outp.append("'")
        elif ch == "c" and i + 1 < n and form[i + 1] in vowels:
            outp.append("č")
        else:
            outp.append(ch)
        i += 1
    return "".join(outp)


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

class Data:
    def __init__(self, db_path, outdir):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.roots = {r["key"]: r for r in json.loads((outdir / "roots_ranked.json").read_text(encoding="utf-8"))}
        self.roots_by_rank = sorted(self.roots.values(), key=lambda r: r["rank"])
        self.affixes = json.loads((outdir / "affixes_ranked.json").read_text(encoding="utf-8"))
        self.seg = {}
        for line in (outdir / "segmentation_log.jsonl").read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            self.seg[rec["entry_id"]] = rec
        self.stats = json.loads((outdir / "stats.json").read_text(encoding="utf-8"))
        self.auto_review = (outdir / "review_log_auto.md").read_text(encoding="utf-8")
        self.variant_merges = json.loads((outdir / "variant_merges.json").read_text(encoding="utf-8"))
        self.missing = []
        self.used_entries = OrderedDict()
        self.grammar = json.loads((ROOT / "extracted_data" / "grammatical_overview.json").read_text(encoding="utf-8"))
        self.kin = [dict(r) for r in self.conn.execute("select * from kinship_paradigms")]
        self.bb_pages = self._bb_page_index()
        self.pronounce = False
        self.modern = False
        self._pron_db = {}
        for r in self.conn.execute("select entry_id, headword, simplified_pronunciation from lexical_entries where simplified_pronunciation is not null"):
            self._pron_db[r[0]] = (norm(r[1]).split(",")[0].strip(), r[2])

    def spell(self, form):
        """Apply the modern (learner) spelling when --modern is set; otherwise unchanged."""
        return modern_spelling(form) if self.modern and form and not form.startswith("[") else form

    def pron(self, form, eid=None):
        """⟨respelling⟩ for a form: DB value (from Parks's phonetic transcription) when the
        form is the headword of `eid`; otherwise spelling-based, marked ≈."""
        if not self.pronounce or not form or form.startswith("["):
            return ""
        if eid in self._pron_db and self._pron_db[eid][0] == form:
            return f" ⟨{self._pron_db[eid][1]}⟩"
        rs = respell_orthography(form)
        return f" ⟨≈{rs}⟩" if rs else ""

    # -- entries --------------------------------------------------------------
    def entry(self, eid):
        r = self.conn.execute("""select l.*, (select definition from glosses g where g.entry_id=l.entry_id
                                 order by sense_number limit 1) as gloss,
                                 (select raw_etymology from etymology e where e.entry_id=l.entry_id) as etym
                                 from lexical_entries l where entry_id=?""", (eid,)).fetchone()
        if r is None:
            self.missing.append(eid)
            return None
        self.used_entries[eid] = True
        return r

    def W(self, eid):
        """Headword (first alternate) of an entry, Parks orthography (+ pronunciation in pronounce mode)."""
        r = self.entry(eid)
        if not r:
            return f"[MISSING {eid}]"
        hw = norm(r["headword"]).split(",")[0].strip()
        return self.spell(hw) + self.pron(hw, eid)

    def G(self, eid, short=True):
        r = self.entry(eid)
        if not r:
            return ""
        g = r["gloss"] or ""
        if short:
            g = g.split(";")[0].strip().rstrip(".")
        return g

    def P(self, eid):
        r = self.entry(eid)
        return r["page_number"] if r else "?"

    def CL(self, eid):
        r = self.entry(eid)
        if not r:
            return ""
        return (r["grammatical_class"] or "") + (f" {r['verb_class']}" if r["verb_class"] else "")

    def F(self, eid, n):
        """Dictionary paradigmatic form n (1 = 1sg IND, 2 = 3sg IND, 3 = IMPF, 4 = GER, 5 = INT)."""
        r = self.conn.execute("select skiri_form from paradigmatic_forms where entry_id=? and form_number=?", (eid, n)).fetchone()
        if r is None:
            self.missing.append(f"{eid}#form{n}")
            return f"[no form_{n}]"
        self.used_entries[eid] = True
        f = norm(r["skiri_form"])
        return self.spell(f) + self.pron(f)

    def has_F(self, eid, n):
        return self.conn.execute("select 1 from paradigmatic_forms where entry_id=? and form_number=?", (eid, n)).fetchone() is not None

    def pieces(self, eid):
        rec = self.seg.get(eid)
        return rec["pieces"] if rec else []

    def piece_glosses(self, eid):
        """[(form, label-or-gloss)] from Parks's etymology as segmented."""
        rec = self.seg.get(eid)
        if not rec:
            return []
        outp = []
        for x in rec["elements"]:
            lab = x.get("label") or x.get("gloss") or x.get("compound_gloss") or "—"
            outp.append((self.spell(x["form"]), lab, x["category"]))
        return outp

    def seg_conf(self, eid):
        rec = self.seg.get(eid)
        return rec["confidence"] if rec else "n/a"

    def rules(self, eid):
        rec = self.seg.get(eid)
        return rec["rules"] if rec else []

    def BBatt(self, eid):
        rows = self.conn.execute("""select bb_skiri_form, bb_english, lesson_number, page_number, match_type
                                    from blue_book_attestations where entry_id=?
                                    order by case match_type when 'exact_normalized' then 0 when 'orthographic' then 1
                                                             when 'loose' then 2 when 'stem' then 3 else 9 end, lesson_number""", (eid,)).fetchall()
        return [dict(r) for r in rows]

    def BB(self, eid):
        rows = [r for r in self.BBatt(eid) if r["match_type"] in ("exact_normalized", "orthographic", "loose", "stem")]
        if not rows:
            return ""
        b = rows[0]
        pg = f", p.{b['page_number']}" if b["page_number"] else ""
        return f"BB *{b['bb_skiri_form']}* (L{b['lesson_number']}{pg})"

    # -- Appendix 1 -----------------------------------------------------------
    def A(self, verb, mode, person):
        r = self.conn.execute("select skiri_form, english_form, source_page from verb_paradigms where verb_heading=? and mode=? and person_number=?",
                              (verb, mode, person)).fetchone()
        if r is None:
            self.missing.append(f"App1:{verb}/{mode}/{person}")
            return "[no cell]"
        f = norm(r["skiri_form"])
        return self.spell(f) + self.pron(f)

    def A_eng(self, verb, mode, person):
        r = self.conn.execute("select english_form from verb_paradigms where verb_heading=? and mode=? and person_number=?",
                              (verb, mode, person)).fetchone()
        return r["english_form"] if r else ""

    def A_page(self, verb):
        r = self.conn.execute("select source_page from verb_paradigms where verb_heading=? limit 1", (verb,)).fetchone()
        return r["source_page"] if r else "?"

    # -- Blue Book text pages -------------------------------------------------
    def _bb_page_index(self):
        txt = (ROOT / "pari pakuru" / "Blue_Book_Pari_Pakuru.txt").read_text(encoding="utf-8", errors="replace")
        pages = {}
        cur = None
        for line in txt.splitlines():
            m = re.match(r"^PAGE (\d+)$", line.strip())
            if m:
                cur = int(m.group(1))
                pages[cur] = []
            elif cur is not None:
                pages[cur].append(line)
        return pages

    def bb_quote(self, page, needle, span=1):
        """Return the Blue Book line on `page` (or the next `span` pages) containing `needle`."""
        for pg in range(page, page + span + 1):
            for line in self.bb_pages.get(pg, []):
                if needle in line:
                    return line.strip()
        self.missing.append(f"BB p.{page}: {needle}")
        return ""

    def bbq(self, page, needle, span=1):
        """Formatted BB citation: quoted line plus page."""
        q = self.bb_quote(page, needle, span)
        return f"BB p.{page}: “{q}”" if q else f"BB p.{page}"

    # -- Parks grammar examples ----------------------------------------------
    def grammar_examples(self):
        """Parks's own glossed verb examples: (page, word, gloss, analysis)."""
        outp = []
        for k, v in self.grammar.items():
            pg = v.get("page_number")
            for s in v.get("sections", []):
                txt = s.get("content") or ""
                for m in re.finditer(r"([a-zA-Zʔáíúāīū]+)\s+[‘'“]([^’'”]{2,90})[’'”]\s*<\s*(.{10,260}?)(?=\s+(?:[a-zA-Zʔ]+\s+[‘'“][^’'”]+[’'”]\s*<|\n|$))", txt):
                    w, gl, an = m.group(1), m.group(2), m.group(3).strip()
                    if "+" in an:
                        outp.append((pg, w, gl, an.split("; cp.")[0].rstrip(";")))
        return outp

    def grammar_example(self, word):
        for pg, w, gl, an in self.grammar_examples():
            if w == word:
                return pg, w, gl, an
        self.missing.append(f"GO example: {word}")
        return None


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(lines)


def cite(d, eid):
    return f"Parks p.{d.P(eid)}, `{eid}`"


def entry_table(d, eids, with_pieces=True, with_bb=True):
    headers = ["Word", "Class", "Meaning (Parks)", "Parks analysis", "Source"]
    rows = []
    for eid in eids:
        if d.entry(eid) is None:
            rows.append([f"[MISSING {eid}]", "", "", "", ""])
            continue
        pg = d.piece_glosses(eid)
        analysis = " + ".join(f"{f} '{l}'" if l != "—" else f for f, l, c in pg) if with_pieces else ""
        src = cite(d, eid)
        bb = d.BB(eid) if with_bb else ""
        if bb:
            src += "; " + bb
        rows.append([f"**{d.W(eid)}**", d.CL(eid), d.G(eid), analysis, src])
    return md_table(headers, rows)


def root_card(d, key):
    r = d.roots.get(key)
    if r is None:
        d.missing.append(f"root:{key}")
        return f"- [MISSING ROOT {key}]"
    sense = f" ({r['sense']})" if r.get("sense") else ""
    pv = f", with preverb *{r['preverb']}-*" if r.get("preverb") else ""
    conf = r["confidence"]
    reasons = "; ".join(r["confidence_reasons"]) if r["confidence_reasons"] else ""
    ex = "; ".join(f"*{d.spell(e['word'].split(',')[0].strip())}{d.pron(e['word'].split(',')[0].strip(), e['entry_id'])}* '{(e['gloss'] or '')[:40]}' (p.{e['parks_page']})" for e in r["examples"][:3])
    line = (f"- **{d.spell(r['root'])}**{sense} — '{r['gloss']}' — {r['class']}{pv} — builds {r['frequency']} dictionary words "
            f"(rank {r['rank']}) — confidence **{conf}**" + (f" ({reasons})" if reasons else "") + f". Examples: {ex}.")
    return line


def paradigm_table(d, eids):
    headers = ["Stem (entry)", "1sg IND (form 1)", "3sg IND (form 2)", "IMPF (form 3)", "GER (form 4)", "INT (form 5)", "Parks p."]
    rows = []
    for eid in eids:
        if d.entry(eid) is None:
            continue
        rows.append([f"**{d.W(eid)}** '{d.G(eid)}'"] +
                    [d.F(eid, n) if d.has_F(eid, n) else "—" for n in (1, 2, 3, 4, 5)] + [d.P(eid)])
    return md_table(headers, rows)


def app1_table(d, verb, modes, persons):
    headers = ["Person/number"] + [m.replace("_perfective", "").replace("_", " ") for m in modes]
    rows = []
    for p in persons:
        rows.append([p] + [d.A(verb, m, p) for m in modes])
    return md_table(headers, rows) + f"\n\nSource: Parks Appendix 1, *{verb}*, p.{d.A_page(verb)} (verb_paradigms table)."


def exercises(d, build_eids, break_eids, extra=None):
    """Build-the-word and break-down-the-word exercises with answer key."""
    lines = []
    if build_eids:
        lines += ["**Practice A — build the word.** Combine the pieces (Parks's own analysis) into the attested word. "
                  "Watch for the sound changes listed in the walkthrough.", ""]
        for i, eid in enumerate(build_eids, 1):
            pg = d.piece_glosses(eid)
            lines.append(f"{i}. " + " + ".join(f"*{f}* '{l}'" if l != "—" else f"*{f}*" for f, l, c in pg) + f"  → ______ ('{d.G(eid)}')")
    if break_eids:
        lines += ["", "**Practice B — break down the word.** Divide each attested word into its morphemes and gloss each.", ""]
        for i, eid in enumerate(break_eids, 1):
            lines.append(f"{i}. *{d.W(eid)}* '{d.G(eid)}'  → ______")
    if extra:
        if lines:
            lines.append("")
        lines += ["**Practice C — derive the attested form.**", "", extra]
    if not (build_eids or break_eids):
        return "\n".join(lines)
    lines += ["", "**Answer key (A and B)**", ""]
    for i, eid in enumerate(build_eids, 1):
        lines.append(f"A{i}. *{d.W(eid)}* ({cite(d, eid)}" + (f"; {d.BB(eid)}" if d.BB(eid) else "") + ")"
                     + (f" — rules at the seams: {', '.join(d.rules(eid))}" if d.rules(eid) else "")
                     + f" — segmentation confidence {d.seg_conf(eid)}")
    for i, eid in enumerate(break_eids, 1):
        pg = d.piece_glosses(eid)
        lines.append(f"B{i}. " + " + ".join(f"*{f}* '{l}'" if l != "—" else f"*{f}*" for f, l, c in pg)
                     + f" ({cite(d, eid)}) — confidence {d.seg_conf(eid)}")
    return "\n".join(lines)


def taught_review_words(d, taught_forms, limit=12, exclude=()):
    """Attested dictionary words whose every surface piece is already taught."""
    hits = []
    for eid, rec in d.seg.items():
        if not rec["pieces"] or rec["confidence"] == "low" or eid in exclude:
            continue
        pcs = [p for p, x in zip(rec["pieces"], rec["elements"]) if x["category"] != "preverb"]
        if len(pcs) < 2:
            continue
        if all(p in taught_forms for p in pcs):
            hits.append(rec)
    hits.sort(key=lambda r: (r["confidence"] != "high", -len(r["pieces"]), r["page"] or 0))
    seen, picked = set(), []
    for r in hits:
        if r["hw_key"] in seen:
            continue
        seen.add(r["hw_key"])
        picked.append(r["entry_id"])
        if len(picked) >= limit:
            break
    return picked


# ---------------------------------------------------------------------------
# Lesson plans
# ---------------------------------------------------------------------------

def render_lessons(d):
    title = "# Skiri Pawnee root-first curriculum — lesson plans"
    if d.modern:
        title += " (modern spelling, with simplified pronunciation)"
    elif d.pronounce:
        title += " (with simplified pronunciation)"
    L = [title, ""]
    if d.modern:
        L += ["**Spelling note.** Dictionary forms, Appendix 1 forms, root names and Parks's morpheme pieces are written here in the learner "
              "orthography used by the project's `normalized_form` field: long vowels *â î û* (Parks *aa ii uu*), the glottal stop as *'* (Parks *ʔ*), "
              "and *č* for Parks's *c* when a vowel follows (pronounced *ch*, Parks Rule 24), plain *c* before a consonant or at the end of a word "
              "(pronounced *ts*). Parks's accent marks are kept. The conversion is mechanical and reversible; entry ids and page numbers still point to "
              "Parks's spelling. Blue Book forms stay in Blue Book spelling, and bare morphemes quoted in explanatory prose (such as *ti-*, *-uʔ*) keep "
              "Parks's dictionary spelling so that they can be looked up.", ""]
    if d.pronounce:
        L += ["**Pronunciation key.** Each Pawnee form is followed by a respelling in ⟨ ⟩ using the project's English respelling "
              "(Parks Sound Key p. xvii; Blue Book pp. xvii–xxi): *ah ee oo* = long *aa ii uu*; *uh ih oo* = short *a i u*; *d* = Pawnee *r* "
              "(a quick tap, as in English 'ready'); *ts* = *c*; *'* = glottal stop; a syllable in CAPITALS carries Parks's accent mark. "
              "Parks's *c* is written *ch* before a vowel and *ts* elsewhere (Parks Rule 24). Respellings without ≈ come from Parks's own phonetic transcription of that headword (database column `simplified_pronunciation`, Phase 1.1c). "
              "Respellings marked ≈ are derived from the spelling alone, because the dictionary gives no phonetic transcription for inflected forms; they carry no "
              "stress information beyond written accents and are an aid, not an attestation. Blue Book forms are left in Blue Book spelling.", ""]
    L += [
         "Generated by `scripts/build_root_curriculum.py` from `roots_ranked.json`, `affixes_ranked.json`, the project "
         "database (Parks dictionary), Parks Appendix 1, and the Blue Book (BB). Every Pawnee form below is looked up, "
         "not typed; each is followed by its source (Parks page and entry id, Appendix 1 page, or BB lesson and page). "
         "Orthography follows the source exactly: Parks forms use *ʔ*, *c*, long vowels *aa ii uu*; BB forms keep the "
         "BB spelling (*ts*, *'*, *•* between pieces).", "",
         "Confidence labels come from the extraction: **high** = Parks's analysis reproduces the headword exactly or via a "
         "numbered sound rule; **medium** = reproduces it only with vowel-length / glottal tolerance, an unnumbered rule, or "
         "an inherited gloss; **low** = not reproducible, needs speaker/linguist review.", "",
         "## How to read a lesson", "",
         "Each lesson has: objectives; new roots or morphemes (with frequency rank and confidence); a construction "
         "walkthrough; attested example words (5–10); Practice A (build the word) and Practice B (break down the word); an "
         "answer key. Units end with a review built from attested words whose *every* morpheme has been taught.", ""]
    taught = set()           # surface forms taught so far (roots + affixes)
    used_in_lessons = set()
    for unit in UNITS:
        L += [f"# Unit {unit['id']} — {unit['title']}", "", unit["intro"], ""]
        if unit.get("bb_alignment"):
            L += ["**Blue Book alignment.** " + unit["bb_alignment"], ""]
        for les in unit["lessons"]:
            L += [f"## Lesson {les['id']} — {les['title']}", ""]
            L += ["**Objectives**", ""] + [f"- {o}" for o in les["objectives"]] + [""]
            if les.get("roots"):
                L += ["**New roots** (type frequency = number of distinct dictionary words built on the root)", ""]
                for key in les["roots"]:
                    L.append(root_card(d, key))
                    r = d.roots.get(key)
                    if r:
                        taught.add(r["root"])
                        taught.update(r.get("variants", []))
                L.append("")
            if les.get("morphemes"):
                L += ["**New morphemes**", ""]
                for m in les["morphemes"]:
                    L.append(f"- {m['label']} — {m['meaning']} — source: {m['source']}" + (f" — {m['note']}" if m.get("note") else ""))
                    taught.update(m.get("forms", []))
                L.append("")
            L += ["**Construction walkthrough**", "", les["walkthrough"](d), ""]
            if les.get("examples"):
                L += ["**Attested example words**", "", entry_table(d, les["examples"]), ""]
                used_in_lessons.update(les["examples"])
            if les.get("paradigms"):
                L += ["**Dictionary paradigm forms** (Parks Part II of each entry)", "", paradigm_table(d, les["paradigms"]), ""]
            if les.get("app1"):
                for verb, modes, persons in les["app1"]:
                    L += [f"**Appendix 1 — *{verb}***", "", app1_table(d, verb, modes, persons), ""]
            if les.get("bb_notes"):
                L += ["**Blue Book cross-reference**", "", les["bb_notes"](d), ""]
            if les.get("exercises") or les.get("extra_practice"):
                b, br = les.get("exercises", ([], []))
                extra = les["extra_practice"](d) if les.get("extra_practice") else None
                L += ["**Practice and answer key**", "", exercises(d, b, br, extra), ""]
            if les.get("deviation"):
                L += ["**Where this deviates from the Blue Book, and why.** " + les["deviation"], ""]
        # unit review
        review = taught_review_words(d, taught, limit=unit.get("review_size", 12), exclude=used_in_lessons)
        used_in_lessons.update(review)
        L += [f"## Unit {unit['id']} review", "",
              f"Everything below is an attested dictionary word made only of morphemes taught so far (Units 1–{unit['id']}). "
              "Break each down, gloss the pieces, and name any sound change at the seams; then rebuild it from the pieces.", ""]
        if review:
            L += [entry_table(d, review), ""]
            L += ["Answer key (Parks's analysis, sound rules fired, confidence):", ""]
            for eid in review:
                pg = d.piece_glosses(eid)
                L.append(f"- *{d.W(eid)}* = " + " + ".join(f"{f} '{l}'" if l != "—" else f for f, l, c in pg)
                         + (f" — rules: {', '.join(d.rules(eid))}" if d.rules(eid) else " — no change at the seams")
                         + f" — {d.seg_conf(eid)} ({cite(d, eid)})")
            L.append("")
        else:
            L += ["No further attested words are built solely from the morphemes taught so far.", ""]
        if unit.get("review_extra"):
            L += [unit["review_extra"](d), ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Construction guide
# ---------------------------------------------------------------------------

def render_guide(d):
    G = ["# How Skiri Pawnee words are built — a construction guide", "",
         "Generated by `scripts/build_root_curriculum.py`. Sources: Parks, *A Dictionary of Skiri Pawnee* — Grammatical "
         "Overview (cited as **GO p.N**, book pages 29–51 as extracted in `grammatical_overview.json`), Chapter 3 sound "
         "rules (as formalised in `scripts/sound_changes.py`), Appendix 1 paradigms (**App.1 p.N**), Appendix 3 kinship "
         "(**App.3**), dictionary entries (**Parks p.N**, entry id); and the Blue Book *Pari Pakuru* (**BB L#, p.N**). "
         "Where the two sources disagree both are shown and the disagreement is flagged ⚠.", ""]
    for section in GUIDE:
        G += [f"## {section['title']}", "", section["body"](d), ""]
    return "\n".join(G)


# ---------------------------------------------------------------------------
# Review log
# ---------------------------------------------------------------------------

def render_review(d):
    R = ["# Review log — uncertain segmentations, source conflicts, data gaps", "",
         "Part 1 is written by hand from the comparison of sources during curriculum design. Part 2 is the machine-generated "
         "log from `scripts/root_extraction.py` (every low/medium segmentation, every variant merge, every homonym split).", "",
         "# Part 1 — Source conflicts, decisions and gaps (manual)", ""]
    for section in REVIEW_MANUAL:
        R += [f"## {section['title']}", "", section["body"](d), ""]
    R += ["", "# Part 2 — Machine-generated log", "", d.auto_review.replace("# Review log (auto-generated by scripts/root_extraction.py)", "").strip(), ""]
    return "\n".join(R)


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(ROOT / "skiri_pawnee.db"))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true", help="only verify that every id in the spec resolves")
    ap.add_argument("--pronounce", action="store_true",
                    help="write lesson_plans_pronounced.md (forms followed by simplified pronunciation) and nothing else")
    ap.add_argument("--modern", action="store_true",
                    help="like --pronounce, but forms in the learner orthography (â î û, ', č); writes lesson_plans_pronounced_modern.md")
    args = ap.parse_args()
    outdir = Path(args.out)
    d = Data(args.db, outdir)

    if args.pronounce or args.modern:
        d.pronounce = True
        d.modern = bool(args.modern)
        name = "lesson_plans_pronounced_modern.md" if args.modern else "lesson_plans_pronounced.md"
        lessons = render_lessons(d)
        (outdir / name).write_text(lessons, encoding="utf-8")
        out(f"wrote {name} ({len(lessons):,} chars); unresolved references: {len(set(d.missing))}")
        return

    lessons = render_lessons(d)
    guide = render_guide(d)
    review = render_review(d)
    if d.missing:
        out("UNRESOLVED REFERENCES (fix the spec):")
        for m in sorted(set(d.missing)):
            out("  - " + m)
    if args.check:
        out(f"spec check done; {len(set(d.missing))} unresolved")
        return
    (outdir / "lesson_plans.md").write_text(lessons, encoding="utf-8")
    (outdir / "construction_guide.md").write_text(guide, encoding="utf-8")
    (outdir / "review_log.md").write_text(review, encoding="utf-8")
    out(f"wrote lesson_plans.md ({len(lessons):,} chars), construction_guide.md ({len(guide):,}), review_log.md ({len(review):,})")
    out(f"entries cited: {len(d.used_entries)}; unresolved references: {len(set(d.missing))}")


if __name__ == "__main__":
    main()
