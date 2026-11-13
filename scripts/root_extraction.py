#!/usr/bin/env python3
"""
Root & Affix Extraction — type-frequency ranking of Skiri Pawnee morphemes
==========================================================================

Segments every lexical entry into prefixes / root(s) / suffixes using the
dictionary's own etymology breakdowns (Parks `constituent_elements`), checks
each segmentation against the headword with the Phase 2.3 sound-change engine
(scripts/sound_changes.py), and ranks roots and affixes by the number of
distinct words (types) they build.

Nothing is invented: every root, gloss and example is traced to an entry_id
and Parks page number; Blue Book attestations are attached where linked.

Outputs (default dir curriculum/roots/):
    roots_ranked.json       ranked lexical roots
    affixes_ranked.json     ranked grammatical affixes / stem elements
    segmentation_log.jsonl  one record per entry: pieces, rules, confidence
    variant_merges.json     surface-variant -> underlying root merges, with rule
    review_log_auto.md      machine-generated review items
    stats.json              summary counts

Usage:
    python scripts/root_extraction.py                 # run, write outputs
    python scripts/root_extraction.py --db skiri_pawnee.db --out curriculum/roots
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sound_changes as sc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def out(text):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def norm(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "ʔ").replace("'", "ʔ").replace("‘", "ʔ")
    return s.strip()


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s)
                   if unicodedata.category(ch) != "Mn")


def headword_key(hw):
    """First alternate of a headword, bracket notes removed, accents stripped."""
    hw = norm(hw)
    hw = re.sub(r"\[.*?\]", "", hw).strip()
    hw = hw.split(",")[0].strip()
    return strip_accents(hw)


PREVERB_RE = re.compile(r"\((\s*[a-z]+(?:\s*\.\s*\.\s*\.\s*[a-z]+)*)\s*\.\s*\.\s*\.\s*\)")


def split_preverb_annotation(m):
    """'a (ir...)' -> ('a', ['ir']); '(ut...)' -> ('', ['ut'])."""
    pvs = []
    for mt in PREVERB_RE.finditer(m):
        inner = mt.group(1).replace(" ", "")
        pvs.extend([p for p in inner.split("...") if p])
    base = PREVERB_RE.sub("", m)
    base = re.sub(r"\[.*?\]", "", base)
    return base.strip(), pvs


# ---------------------------------------------------------------------------
# Morpheme classification
# ---------------------------------------------------------------------------

GRAM_LABEL_RE = re.compile(r"^[A-Z0-9][A-Z0-9./+ -]*$")

# Known grammatical morphemes (form -> (category, label)). Used when Parks
# gives no gloss or a grammatical paraphrase for a grammatical element.
KNOWN_GRAMMATICAL = {
    "ut":   ("preverb", "PREV ut-"),
    "uur":  ("preverb", "PREV uur-"),
    "ir":   ("preverb", "PREV ir-"),
    "uks":  ("prefix", "AOR/JUSS uks-"),
    "raar": ("affix", "PL/ITER raar- (ambiguous without gloss)"),
    "ra":   ("stem-element", "PORT ra-"),
    "ri":   ("stem-element", "PORT ri-"),
    "ruu":  ("stem-element", "PORT ruu-"),
    "cir":  ("stem-element", "COM cir-"),
    "ciras": ("stem-element", "COM ciras-"),
    "uʔ":   ("suffix", "NOM -uʔ"),
    "u":    ("suffix", "NOM -u (variant) / SUB.D -u"),
    "kis":  ("suffix", "DIM -kis"),
    "kiʔ":  ("suffix", "DIM -kiʔ (variant of -kis)"),
    "kusuʔ": ("suffix", "AUG -kusuʔ"),
    "hiriʔ": ("suffix", "LOC/INST -hiriʔ"),
    "piriʔ": ("suffix", "LOC/INST -piriʔ"),
    "iriʔ": ("suffix", "LOC/INST -iriʔ"),
    "riʔ":  ("suffix", "LOC/INST -riʔ"),
    "kat":  ("suffix", "LOC -kat"),
    "ru":   ("suffix", "LOC -ru"),
    "wiru": ("suffix", "LOC -wiru"),
    "taku": ("suffix", "LOC.ADV -taku"),
    "his":  ("suffix", "PERF -his"),
    "hus":  ("suffix", "IMPF -hus"),
    "huʔ":  ("suffix", "IMPF -huʔ"),
    "waa":  ("suffix", "DIST -waa"),
    "itik": ("suffix", "INCH -itik"),
    "c":    ("prefix", "FEM c-"),
    "ta":   ("prefix", "GEN.LOC ta-"),
    "witi": ("proclitic", "REFL witi-"),
    "si":   ("proclitic", "DU si-"),
    "ku":   ("proclitic", "INDF ku-"),
    "kara": ("proclitic", "NEG kara-"),
    "ka":   ("affix", "ITER ka- / LOC ka- 'on' (ambiguous without gloss)"),
    "wi":   ("stem-element", "LOC.V -wi (locative/positional formative; Parks 'upright')"),
    "uk":   ("suffix", "EXIST -uk 'be, exist' (descriptive-verb formative)"),
}


def homonym_sense(form, gk, host_class, preverbs):
    """Homonym splits grounded in the data (documented in the review log).

    Returns a sense tag or None. gk = normalised gloss key of this occurrence.
    """
    hc = host_class or ""
    if form == "hiir":
        # Parks: hiir (uur...) 'be good' (App.1 'to be good' tuuhii; p.32) vs hiir- 'grass'
        if "uur" in preverbs or re.search(r"good|nice", gk):
            return "(uur...) be good"
        if re.search(r"grass|hay", gk) or (not gk and hc.startswith("N")):
            return "grass"
        if gk:
            return "other: " + gk
        return "unassigned"
    if form == "arik":
        # Parks: arik 'be standing' (App.2 irregular root) vs arik- 'horn' (nouns)
        if re.search(r"stand", gk) or (not gk and hc.startswith("V")):
            return "be standing"
        if re.search(r"horn|braid|patch|spot", gk) or hc.startswith("N"):
            return "horn"
        return "unassigned"
    if form == "kaa" and re.search(r"grandmother", gk):
        return "grandmother (kinship, atikaʔ)"
    if form == "as" and re.search(r"father", gk):
        return "father (kinship, atiʔas)"
    if form == "raar":
        return gk or "unassigned"
    return None

CAUS_FORMS = {"rik", "raʔuk", "k", "ik", "wuh", "kuk"}
KIN_POSS = {"my": "KIN.POSS 1 ati-/t-", "your": "KIN.POSS 2 a-", "his": "KIN.POSS 3 i-",
            "her": "KIN.POSS 3 i-", "his/her": "KIN.POSS 3 i-", "his or her": "KIN.POSS 3 i-"}

GRAM_PARAPHRASES = {
    "holding", "carrying", "carry", "for", "trans", "prev", "preverb", "upright",
    "become", "get", "small", "little", "with", "using", "in", "on", "at", "among",
    "the one", "that", "there", "here", "pl", "plural", "iter", "iterative",
}


def classify(form, gloss, ptype, position, n_elements):
    """Return (category, label) for one etymology element.

    category in {root, preverb, prefix, suffix, stem-element, proclitic, affix}
    """
    g = (gloss or "").strip()
    f = form
    if not f:
        return None, None
    if f == "i" and position == n_elements - 1 and n_elements > 1 and not g:
        return "suffix", "-i (class 1-i/2-i stem marker in Parks headwords)"
    # 1. Parks grammatical label (uppercase)
    if g and GRAM_LABEL_RE.match(g):
        lab = g
        if position == 0 and ptype != "suffix":
            cat = "prefix"
        elif position == n_elements - 1:
            cat = "suffix"
        else:
            cat = ptype if ptype in ("prefix", "suffix", "preverb") else "affix"
        shape = f"-{f}" if cat == "suffix" else f"{f}-"
        return cat, f"{lab} {shape}"
    # 2. kinship possessive prefixes
    if g.lower() in KIN_POSS and position == 0:
        return "prefix", KIN_POSS[g.lower()]
    # 3. causatives in non-initial position
    if position > 0 and f in CAUS_FORMS and (g.lower().startswith("cause") or g.lower() in ("make", "caus", "trans", "")):
        return "suffix", f"CAUS -{f}"
    # 4. known grammatical forms
    if f in KNOWN_GRAMMATICAL:
        cat, lab = KNOWN_GRAMMATICAL[f]
        lexical_gloss = bool(g) and not GRAM_LABEL_RE.match(g) and g.lower() not in GRAM_PARAPHRASES
        # lexical roots that share a shape with an affix (e.g. 'ta' 'be suspended',
        # 'ra' 'have', 'kis' 'small', 'ka' 'be inside') stay roots when Parks gives
        # a lexical gloss and the element is stem-final or non-initial.
        if lexical_gloss and position == n_elements - 1 and cat != "suffix":
            return "root", None
        if lexical_gloss and f in ("ra", "ri", "ruu", "ka", "ta", "raar", "ir") and position > 0:
            return "root", None
        return cat, lab
    # 5. everything else is lexical
    return "root", None


# ---------------------------------------------------------------------------
# Sound-change tracing
# ---------------------------------------------------------------------------

RESTRICTED = [("1R", sc.apply_rule_1r), ("2R", sc.apply_rule_2r), ("3R", sc.apply_rule_3r),
              ("8R", sc.apply_rule_8r), ("10R", sc.apply_rule_10r), ("11R", sc.apply_rule_11r),
              ("12R", sc.apply_rule_12r)]
UNRESTRICTED = [("5", sc.apply_rule_5_same_vowel_contraction), ("6", sc.apply_rule_6_u_domination),
                ("7", sc.apply_rule_7_i_a_contraction), ("13", sc.apply_rule_13_t_laryngealization),
                ("14", sc.apply_rule_14_metathesis), ("15", sc.apply_rule_15_sonorant_reduction),
                ("16", sc.apply_rule_16_h_loss), ("17", sc.apply_rule_17_sibilant_hardening),
                ("18", sc.apply_rule_18_sibilant_loss), ("19", sc.apply_rule_19_alveolar_dissimilation),
                ("20", sc.apply_rule_20_degemination), ("21", sc.apply_rule_21_r_stopping),
                ("22", sc.apply_rule_22_labial_glide_loss), ("23", sc.apply_rule_23_final_r_loss)]
NOMINAL_SAFE = {"5", "6", "7", "13", "14", "15", "16", "20", "21", "22", "23"}
UNNUMBERED = {"V-length", "k>t", "r>h", "w>p"}


def trace_engine(pieces, nominal=False):
    """Run the engine rule by rule; return (surface, [rule ids that changed something])."""
    fired = []
    m = list(pieces)
    if not nominal:
        for rid, fn in RESTRICTED:
            new = fn(m)
            if new != m:
                fired.append(rid)
            m = new
    s = "".join(m)
    for rid, fn in UNRESTRICTED:
        if nominal and rid not in NOMINAL_SAFE:
            continue
        new = fn(s)
        if new != s:
            fired.append(rid)
        s = new
    s = s.replace(sc.KS_MARKER, "")
    return s, fired


def tol(s):
    """Tolerant normalisation: collapse long vowels, drop ʔ and h."""
    s = re.sub(r"([aiu])\1+", r"\1", s)
    return s.replace("ʔ", "").replace("h", "")


def glottal_join(pieces):
    """Join pieces inserting ʔ at vowel+vowel boundaries (stem_extractor convention)."""
    outp = ""
    for p in pieces:
        if outp and p and sc.is_vowel(outp[-1]) and sc.is_vowel(p[0]):
            outp += "ʔ"
        outp += p
    return outp


def alternants(piece):
    """Yield (variant, rule_id, note) single-rule alternants of one morpheme."""
    p = piece
    if p.endswith("r"):
        yield p[:-1], "23", "final r loss"
    if p.endswith("s"):
        yield p[:-1], "9R", "final s loss"
    if p.endswith("k"):
        yield p[:-1] + "t", "k>t", "stem-final k -> t word-finally (Parks perfective Vk; BB L15 'verb-final k')"
    for i, ch in enumerate(p):
        if ch == "h":
            yield p[:i] + p[i + 1:], "16", "h loss"
    if "tr" in p:
        yield p.replace("tr", "hr"), "13", "t -> h before r"
    if p.startswith("r"):
        yield "t" + p[1:], "21", "r -> t after obstruent"
        yield "h" + p[1:], "r>h", "r -> h (morpheme_inventory r->h before high vowel)"
    if p.startswith("w"):
        yield "p" + p[1:], "w>p", "w -> p after obstruent (stem_extractor ut+w junction)"
    for i in range(1, len(p)):
        if p[i] == "s" and sc.is_consonant(p[i - 1]):
            yield p[:i] + "c" + p[i + 1:], "17", "s -> c after consonant"
    for i, ch in enumerate(p):
        if ch in "aiu":
            if i + 1 < len(p) and p[i + 1] == ch:
                yield p[:i] + p[i + 1:], "V-length", "long vowel shortened (no engine rule)"
            elif not (i > 0 and p[i - 1] == ch):
                yield p[:i] + ch + p[i:], "V-length", "short vowel lengthened (no engine rule)"
    if "c" in p:
        yield p.replace("c", "ts"), "24", "c written ts"


def locate_pieces(headword, pieces):
    """Sequentially locate every morpheme in the headword, allowing one rule per piece."""
    pos = 0
    found = []
    ok = True
    for p in pieces:
        if not p:
            continue
        idx = headword.find(p, pos)
        hit = None
        if idx >= 0 and idx - pos <= 3:
            hit = (p, p, None, None)
            pos = idx + len(p)
        else:
            best = None
            for var, rid, note in alternants(p):
                if not var:
                    continue
                j = headword.find(var, pos)
                if j >= 0 and j - pos <= 3 and (best is None or j < best[0]):
                    best = (j, var, rid, note)
            if best:
                hit = (p, best[1], best[2], best[3])
                pos = best[0] + len(best[1])
        if hit is None:
            ok = False
            found.append((p, None, None, "not located"))
        else:
            found.append(hit)
    return ok, found, headword[pos:]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_entries(conn):
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        select l.entry_id, l.headword, l.normalized_form, l.grammatical_class, l.verb_class,
               l.stem_preverb, l.page_number, l.blue_book_attested, l.source, l.additional_forms,
               e.raw_etymology, e.constituent_elements, e.literal_translation,
               (select definition from glosses g where g.entry_id=l.entry_id order by sense_number limit 1) as gloss
        from lexical_entries l left join etymology e using(entry_id)
        order by l.page_number, l.entry_id""").fetchall()
    tags = defaultdict(list)
    for r in conn.execute("select entry_id, tag from semantic_tags"):
        tags[r[0]].append(r[1])
    bb = defaultdict(list)
    for r in conn.execute("""select entry_id, bb_skiri_form, bb_english, lesson_number, page_number, match_type
                             from blue_book_attestations where entry_id is not null order by lesson_number"""):
        bb[r[0]].append({"bb_form": r[1], "bb_english": r[2], "lesson": r[3], "page": r[4], "match": r[5]})
    pforms = defaultdict(dict)
    for r in conn.execute("select entry_id, form_number, skiri_form from paradigmatic_forms"):
        pforms[r[0]][r[1]] = r[2]
    return rows, tags, bb, pforms


# ---------------------------------------------------------------------------
# Segmentation of one entry
# ---------------------------------------------------------------------------

def segment_entry(row):
    hw = headword_key(row["headword"])
    rec = {"entry_id": row["entry_id"], "headword": norm(row["headword"]), "hw_key": hw,
           "class": row["grammatical_class"], "verb_class": row["verb_class"],
           "stem_preverb": row["stem_preverb"], "page": row["page_number"], "gloss": row["gloss"],
           "raw_etymology": row["raw_etymology"], "elements": [], "pieces": [], "preverbs": [],
           "rules": [], "method": None, "confidence": None, "reasons": []}
    if row["stem_preverb"]:
        _, pvs = split_preverb_annotation(norm(row["stem_preverb"]))
        rec["preverbs"] = pvs
    ce = row["constituent_elements"]
    if not ce or ce == "[]":
        rec["method"] = "no_etymology"
        rec["confidence"] = "low"
        rec["reasons"].append("Parks gives no etymology; segmentation not attempted (needs linguist review)")
        return rec
    try:
        els = json.loads(ce)
    except Exception:
        rec["method"] = "bad_json"
        rec["confidence"] = "low"
        rec["reasons"].append("etymology JSON unreadable")
        return rec
    expanded = []
    for e in els:
        m = norm(e.get("morpheme") or "")
        if not m:
            continue
        base, pvs = split_preverb_annotation(m)
        for pv in pvs:
            if pv not in rec["preverbs"]:
                rec["preverbs"].append(pv)
        base = base.replace("+", ".")
        if re.search(r"-i$", base):
            base = base[:-2] + ".i"
        parts = [p for p in re.split(r"[.]", base)]
        parts = [re.sub(r"^[-\s]+|[-\s]+$", "", p) for p in parts]
        parts = [p for p in parts if p]
        if not parts:
            continue
        for p in parts:
            raw = p
            hyph = "-" in p
            p = p.replace("-", "")
            paren = "(" in p or ")" in p
            p_full = re.sub(r"[()]", "", p)            # optional segment kept
            p_min = re.sub(r"\(.*?\)", "", p)          # optional segment dropped
            p_min = re.sub(r"[()]", "", p_min)
            if not p_full or GRAM_LABEL_RE.match(p_full):
                continue  # empty after cleaning, or a gloss label leaked into the morpheme field
            expanded.append({"form": p_full, "form_min": p_min if p_min else p_full, "raw": raw,
                             "gloss": e.get("gloss") if len(parts) == 1 else None,
                             "compound_gloss": e.get("gloss") if len(parts) > 1 else None,
                             "ptype": e.get("morpheme_type"), "from_dotted": len(parts) > 1,
                             "slash": "/" in p, "internal_hyphen": hyph, "paren": paren})
    n = len(expanded)
    for pos, x in enumerate(expanded):
        cat, lab = classify(x["form"], x.get("gloss"), x.get("ptype"), pos, n)
        x["category"] = cat
        x["label"] = lab
    # kinship: a final -riʔ after a KIN.POSS prefix is the third-person kin suffix, not the locative
    if expanded and (expanded[0].get("label") or "").startswith("KIN.POSS") and expanded[-1]["form"] in ("riʔ", "tiʔ"):
        expanded[-1]["category"] = "suffix"
        expanded[-1]["label"] = "KIN.3 -riʔ (third-person kinship suffix)"
    rec["elements"] = expanded
    pieces = [x["form"] for x in expanded]
    rec["pieces"] = pieces
    alternates = [strip_accents(a.strip()).lower() for a in
                  re.sub(r"\[.*?\]", "", norm(row["headword"])).split(",") if a.strip()]
    is_noun = (row["grammatical_class"] or "").startswith("N")
    # preverbs sit outside the stem, so they are not expected in the headword
    surf_elems = [x for x in expanded if x["category"] != "preverb"]
    variants_sets = [[x["form"] for x in surf_elems], [x["form_min"] for x in surf_elems]]
    matched = False
    for hw_cmp in alternates:
        for pieces in variants_sets:
            if "".join(pieces) == hw_cmp:
                rec.update(method="concatenation", rules=[], confidence="high"); matched = True; break
            surf, fired = trace_engine(pieces, nominal=is_noun)
            if surf == hw_cmp:
                rec.update(method="engine", rules=fired, confidence="high"); matched = True; break
            gj = glottal_join(pieces)
            if gj == hw_cmp:
                rec.update(method="glottal_epenthesis", rules=["ʔ-epenthesis (V+V)"], confidence="high"); matched = True; break
            surf2, fired2 = trace_engine([gj], nominal=is_noun)
            if surf2 == hw_cmp:
                rec.update(method="glottal_epenthesis+engine", rules=["ʔ-epenthesis (V+V)"] + fired2, confidence="high"); matched = True; break
        if matched:
            break
    if not matched:
        for hw_cmp in alternates:
            for pieces in variants_sets:
                surf, fired = trace_engine(pieces, nominal=is_noun)
                gj = glottal_join(pieces)
                if tol(surf) == tol(hw_cmp) or tol(gj) == tol(hw_cmp):
                    rec.update(method="engine_tolerant", rules=fired + ["tolerance: vowel length/ʔ/h"], confidence="medium")
                    rec["reasons"].append("engine output matches headword only after ignoring vowel length, ʔ and h")
                    matched = True; break
            if matched:
                break
    if not matched:
        best = None
        for hw_cmp in alternates:
            for pieces in variants_sets:
                ok, found, leftover = locate_pieces(hw_cmp, pieces)
                score = (ok, -len(leftover), -sum(1 for f in found if f[2]))
                if best is None or score > best[0]:
                    best = (score, ok, found, leftover, hw_cmp)
        _, ok, found, leftover, hw_cmp = best
        rec["located"] = [{"piece": a, "found_as": b, "rule": c, "note": d} for a, b, c, d in found]
        rules = [c for _, _, c, _ in found if c]
        rec["rules"] = rules
        if ok and len(leftover) <= 2:
            rec["method"] = "located"
            unnum = sorted(set(r for r in rules if r in UNNUMBERED))
            if unnum:
                rec["confidence"] = "medium"
                rec["reasons"].append("alternation explained only by an unnumbered rule: " + ", ".join(unnum))
            elif leftover:
                rec["confidence"] = "medium"
                rec["reasons"].append(f"unexplained residue after last morpheme: '{leftover}'")
            else:
                rec["confidence"] = "high"
        else:
            okt, foundt, leftt = locate_pieces(tol(hw_cmp), [tol(p) for p in variants_sets[1]])
            if okt and len(leftt) <= 2:
                rec["method"] = "located_tolerant"
                rec["confidence"] = "medium"
                rec["reasons"].append("morphemes located only after ignoring vowel length, ʔ and h")
            else:
                rec["method"] = "unlocated"
                rec["confidence"] = "low"
                missing = [a for a, b, _, _ in found if b is None]
                if missing:
                    rec["reasons"].append("morpheme(s) not recoverable from headword by any single rule: " + ", ".join(missing))
                else:
                    rec["reasons"].append(f"residue '{leftover}' too long after locating all morphemes")
    if any(x.get("from_dotted") for x in expanded):
        rec["reasons"].append("compound stem split at Parks's '.' boundary; sub-element glosses inherited")
        if rec["confidence"] == "high":
            rec["confidence"] = "medium"
    if any(x.get("slash") for x in expanded):
        rec["reasons"].append("etymology contains alternation '/' (Parks gives two shapes)")
        rec["confidence"] = "low"
    if any(x.get("internal_hyphen") for x in expanded):
        rec["reasons"].append("Parks hyphenated form (e.g. hu-raar) kept as one morpheme")
        if rec["confidence"] == "high":
            rec["confidence"] = "medium"
    if any(x.get("paren") for x in expanded):
        rec["reasons"].append("Parks marks an optional segment with ( ); both shapes tried")
        if rec["confidence"] == "high":
            rec["confidence"] = "medium"
    roots = [x for x in expanded if x["category"] == "root"]
    if not roots:
        rec["reasons"].append("no lexical root identified among elements")
        rec["confidence"] = "low"
    unglossed = [x["form"] for x in roots if not x.get("gloss") and not x.get("compound_gloss")]
    if unglossed:
        rec["reasons"].append("root(s) without Parks gloss: " + ", ".join(unglossed))
        if rec["confidence"] == "high":
            rec["confidence"] = "medium"
    return rec


# ---------------------------------------------------------------------------
# Gloss clustering / variant relation
# ---------------------------------------------------------------------------

def gloss_key(g):
    g = (g or "").lower().strip()
    g = re.sub(r"\(.*?\)", "", g)
    g = re.sub(r"^(to|be|the|a|an)\s+", "", g)
    g = re.sub(r"^(to|be)\s+", "", g)
    g = g.split(";")[0].split(",")[0].strip()
    g = re.sub(r"[^a-z/ ]", "", g).strip()
    if g.endswith("s") and len(g) > 3 and not g.endswith("ss"):
        g = g[:-1]
    return g


def relate_forms(a, b):
    for var, rid, note in alternants(a):
        if var == b:
            return rid, note
    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(ROOT / "skiri_pawnee.db"))
    ap.add_argument("--out", default=str(ROOT / "curriculum" / "roots"))
    ap.add_argument("--min-words", type=int, default=1)
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    rows, tags, bb, pforms = load_entries(conn)
    out(f"entries: {len(rows)}")

    records = []
    for r in rows:
        rec = segment_entry(r)
        rec["tags"] = tags.get(r["entry_id"], [])
        rec["bb"] = bb.get(r["entry_id"], [])
        rec["pforms"] = pforms.get(r["entry_id"], {})
        records.append(rec)

    stats = Counter()
    for rec in records:
        stats[("method", rec["method"])] += 1
        stats[("confidence", rec["confidence"])] += 1
        for rid in rec["rules"]:
            stats[("rule", rid)] += 1
    out("methods: " + json.dumps({k[1]: v for k, v in stats.items() if k[0] == "method"}))
    out("confidence: " + json.dumps({k[1]: v for k, v in stats.items() if k[0] == "confidence"}))
    out("rules fired: " + json.dumps({k[1]: v for k, v in sorted(stats.items()) if k[0] == "rule"}, ensure_ascii=False))

    # ---- root aggregation by surface root form
    root_hosts = defaultdict(dict)
    root_glosses = defaultdict(Counter)
    root_gloss_raw = defaultdict(Counter)
    root_conf = defaultdict(Counter)
    root_pos = defaultdict(Counter)
    root_pv = defaultdict(Counter)
    root_inherited = Counter()
    root_display = {}
    # pass 1: glosses Parks gives to a form when it stands as its own element
    single_gloss = defaultdict(Counter)   # keyed by sense key, not bare form
    for rec in records:
        for x in rec["elements"]:
            if x["category"] == "root" and x.get("gloss") and not x.get("from_dotted"):
                form = strip_accents(x["form"])
                sense = homonym_sense(form, gloss_key(x["gloss"]), rec["class"], rec["preverbs"])
                key = form if sense is None else f"{form} #{sense}"
                single_gloss[key][x["gloss"]] += 1
    # pass 2: aggregate
    for rec in records:
        for i, x in enumerate(rec["elements"]):
            if x["category"] != "root":
                continue
            form = strip_accents(x["form"])
            g = x.get("gloss")
            inherited = False
            if g:
                sense = homonym_sense(form, gloss_key(g), rec["class"], rec["preverbs"])
                f = form if sense is None else f"{form} #{sense}"
            else:
                # no own gloss: decide the sense from class/preverb first, then inherit
                sense = homonym_sense(form, "", rec["class"], rec["preverbs"])
                f = form if sense is None else f"{form} #{sense}"
                if x.get("from_dotted") and single_gloss.get(f):
                    g = single_gloss[f].most_common(1)[0][0]
                    inherited = True
            root_display[f] = form
            root_hosts[f].setdefault(rec["hw_key"], rec)
            if g:
                root_glosses[f][gloss_key(g)] += 1
                root_gloss_raw[f][g] += 1
                if inherited:
                    root_inherited[f] += 1
            root_conf[f][rec["confidence"]] += 1
            lex_after = any(y["category"] == "root" for y in rec["elements"][i + 1:])
            root_pos[f]["final" if not lex_after else "nonfinal"] += 1
            for pv in rec["preverbs"]:
                root_pv[f][pv] += 1

    # ---- merge surface variants via single rules + shared gloss
    forms = sorted(root_hosts, key=lambda f: (-len(root_hosts[f]), f))
    canonical = {f: f for f in forms}
    variant_log = []
    for a in forms:
        for b in forms:
            if a == b or canonical[b] != b or canonical[a] != a:
                continue
            if "#" in a or "#" in b:
                continue
            rid, note = relate_forms(a, b)
            if not rid:
                continue
            ga, gb = root_glosses[a], root_glosses[b]
            shared = set(ga) & set(gb)
            if not shared or not gb:
                continue
            # the variant's dominant gloss must be one of the shared glosses
            if gb.most_common(1)[0][0] not in shared:
                continue
            if ga and ga.most_common(1)[0][0] not in shared and ga[gb.most_common(1)[0][0]] < 2:
                continue
            under, var = a, b
            if rid == "V-length" and len(b) > len(a):
                under, var = b, a
            canonical[var] = under
            variant_log.append({"underlying": under, "variant": var, "rule": rid, "note": note,
                                "shared_gloss": sorted(shared)[:3],
                                "variant_words": sorted(root_hosts[var])[:5],
                                "confidence": "medium" if rid in UNNUMBERED else "high"})

    def canon(f):
        seen = set()
        while canonical[f] != f and f not in seen:
            seen.add(f)
            f = canonical[f]
        return f

    merged_hosts = defaultdict(dict)
    merged_variants = defaultdict(set)
    for f in forms:
        c = canon(f)
        merged_hosts[c].update(root_hosts[f])
        if c != f:
            merged_variants[c].add(f)

    standalone = {}
    for rec in records:
        standalone.setdefault(rec["hw_key"], rec)

    roots_out = []
    for f, hosts in merged_hosts.items():
        allf = [f] + sorted(merged_variants[f])
        gl, glraw, conf, posc, pvc = Counter(), Counter(), Counter(), Counter(), Counter()
        for ff in allf:
            gl.update(root_glosses[ff]); glraw.update(root_gloss_raw[ff])
            conf.update(root_conf[ff]); posc.update(root_pos[ff]); pvc.update(root_pv[ff])
        nglossed = sum(gl.values())
        top_gloss, top_n = (gl.most_common(1)[0] if gl else (None, 0))
        share = top_n / nglossed if nglossed else 0
        host_recs = list(hosts.values())
        classes = Counter(h["class"] for h in host_recs)
        vclasses = Counter(h["verb_class"] for h in host_recs if h["verb_class"])
        tagc = Counter(t for h in host_recs for t in h["tags"])
        own = None
        base_form = root_display.get(f, f)
        top_words = set(w for w in (top_gloss or "").split() if len(w) > 2)
        for cand in (base_form, base_form + "uʔ", base_form + "ʔ", base_form + "u"):
            if cand in standalone:
                s = standalone[cand]
                sg = set(re.findall(r"[a-z]+", (s["gloss"] or "").lower()))
                if top_words and not (top_words & sg):
                    continue  # standalone word is a different sense; do not borrow its class
                own = {"headword": s["headword"], "entry_id": s["entry_id"], "class": s["class"],
                       "verb_class": s["verb_class"], "gloss": s["gloss"], "page": s["page"]}
                break
        final_share = posc["final"] / max(1, sum(posc.values()))
        if own and own["class"]:
            cls = own["class"] + (f" {own['verb_class']}" if own.get("verb_class") else "")
            cls_src = f"standalone entry {own['headword']} ({own['entry_id']}, p.{own['page']})"
        else:
            maj = classes.most_common(1)[0][0] if classes else None
            if maj and maj.startswith("N"):
                cls = "noun root (bound)"
            elif maj and maj.startswith("VD"):
                cls = "descriptive root (bound)"
            elif maj and maj.startswith("V"):
                cls = "verb root (bound)" if final_share >= 0.5 else "incorporated element in verbs"
            else:
                cls = f"bound root (hosts: {maj})"
            cls_src = "inferred from host-word classes"
        reasons = []
        hi = conf["high"] / max(1, sum(conf.values()))
        own_glossed = nglossed - root_inherited[f]
        if nglossed == 0:
            rconf = "low"; reasons.append("no Parks gloss on any occurrence — needs speaker/linguist review")
        elif nglossed >= 2 and share < 0.6:
            rconf = "medium"; reasons.append(f"gloss disagreement across entries (top gloss share {share:.0%}) — possible homonymy/polysemy; needs linguist review")
        elif own_glossed >= 3 and hi >= 0.3:
            rconf = "high"
        elif own_glossed >= 3:
            rconf = "medium"; reasons.append(f"root glossed consistently by Parks but only {hi:.0%} of host words segment cleanly")
        elif hi < 0.5:
            rconf = "medium"; reasons.append(f"fewer than 3 direct Parks glosses and only {hi:.0%} of host segmentations are high-confidence")
        else:
            rconf = "high"
        if len(hosts) == 1:
            reasons.append("attested in a single word only")
            if rconf == "high":
                rconf = "medium"
        if merged_variants[f]:
            reasons.append("surface variants merged: " + ", ".join(sorted(merged_variants[f])))
        if root_inherited[f]:
            reasons.append(f"{root_inherited[f]} occurrence(s) inside Parks compound stems glossed by inheritance from the form's own entries")
        if "#" in f:
            reasons.append("homonym split applied (see homonym_sense in root_extraction.py)")
        ex_sorted = sorted(host_recs, key=lambda h: (h["confidence"] != "high", not h["bb"], h["page"] or 0))
        examples = []
        for h in ex_sorted[:5]:
            ex = {"word": h["headword"], "entry_id": h["entry_id"], "parks_page": h["page"],
                  "class": (h["class"] or "") + (f" {h['verb_class']}" if h.get("verb_class") else ""),
                  "gloss": h["gloss"], "segmentation": " + ".join(h["pieces"]),
                  "rules": h["rules"], "segmentation_confidence": h["confidence"]}
            if h["bb"]:
                b = h["bb"][0]
                ex["blue_book"] = {"form": b["bb_form"], "lesson": b["lesson"], "page": b["page"], "match": b["match"]}
            examples.append(ex)
        roots_out.append({
            "root": base_form,
            "sense": f.split("#", 1)[1].strip() if "#" in f else None,
            "key": f,
            "variants": sorted(merged_variants[f]),
            "preverb": pvc.most_common(1)[0][0] if pvc and pvc.most_common(1)[0][1] >= 0.5 * len(hosts) else None,
            "gloss": top_gloss,
            "gloss_variants": [{"gloss": g, "n": n} for g, n in glraw.most_common(6)],
            "class": cls, "class_source": cls_src,
            "host_classes": dict(classes.most_common()),
            "host_verb_classes": dict(vclasses.most_common()),
            "semantic_domains": [t for t, _ in tagc.most_common(3)],
            "frequency": len(hosts),
            "position": "stem-final" if final_share >= 0.5 else "non-final (incorporated / compound-initial)",
            "examples": examples,
            "sources": sorted({f"Parks p.{h['page']}" for h in host_recs if h["page"]})[:8] +
                       sorted({f"BB L{b['lesson']} p.{b['page']}" for h in host_recs for b in h["bb"] if b["lesson"]})[:6],
            "confidence": rconf,
            "confidence_reasons": reasons,
        })
    roots_out.sort(key=lambda r: (-r["frequency"], r["root"]))
    roots_out = [r for r in roots_out if r["frequency"] >= args.min_words]
    for i, r in enumerate(roots_out, 1):
        r["rank"] = i

    # ---- affixes from etymology
    aff_hosts = defaultdict(dict)
    aff_meta = defaultdict(Counter)
    for rec in records:
        for x in rec["elements"]:
            if x["category"] == "root":
                continue
            key = x["label"] or f"{x['category']} {x['form']}"
            aff_hosts[key].setdefault(rec["hw_key"], rec)
            aff_meta[key]["cat:" + x["category"]] += 1
            if x.get("gloss"):
                aff_meta[key]["gloss:" + x["gloss"]] += 1
        for pv in rec["preverbs"]:
            key = f"PREV {pv}-"
            aff_hosts[key].setdefault(rec["hw_key"], rec)
            aff_meta[key]["cat:preverb"] += 1

    def affix_record(label, hosts, category, slot, meaning, source_note, conf, reasons):
        host_recs = list(hosts.values())
        ex_sorted = sorted(host_recs, key=lambda h: (h["confidence"] != "high", not h["bb"], h["page"] or 0))
        examples = []
        for h in ex_sorted[:5]:
            ex = {"word": h["headword"], "entry_id": h["entry_id"], "parks_page": h["page"],
                  "class": h["class"], "gloss": h["gloss"], "segmentation": " + ".join(h.get("pieces", []))}
            if h["bb"]:
                b = h["bb"][0]
                ex["blue_book"] = {"form": b["bb_form"], "lesson": b["lesson"], "page": b["page"]}
            examples.append(ex)
        return {"affix": label, "category": category, "slot": slot, "meaning": meaning,
                "frequency": len(hosts), "examples": examples,
                "sources": [source_note] + sorted({f"Parks p.{h['page']}" for h in host_recs if h["page"]})[:6],
                "confidence": conf, "confidence_reasons": reasons}

    affixes_out = []
    for key, hosts in aff_hosts.items():
        cats = [k[4:] for k in aff_meta[key] if k.startswith("cat:")]
        glosses = Counter({k[6:]: v for k, v in aff_meta[key].items() if k.startswith("gloss:")})
        meaning = glosses.most_common(1)[0][0] if glosses else key.split(" ")[0]
        conf, reasons = "high", []
        if "ambiguous" in key:
            conf = "medium"; reasons.append("Parks gives no gloss; form is shared by two morphemes")
        if len(hosts) < 3:
            conf = "medium" if conf == "high" else conf; reasons.append("fewer than 3 attesting words")
        affixes_out.append(affix_record(key, hosts, cats[0] if cats else "affix",
                                        "stem / derivation (Parks Tables 5, 15; p.31, 44)",
                                        meaning, "Parks etymology (constituent_elements)", conf, reasons))

    # ---- inflectional affixes from paradigmatic forms (by form number)
    def pf_words(n):
        d = {}
        for rec in records:
            f = rec["pforms"].get(n)
            if f:
                d[strip_accents(norm(f)).split(",")[0].strip()] = rec
        return d

    def pf_examples(n, hosts):
        ex = []
        for rec in sorted(hosts.values(), key=lambda h: (not h["bb"], h["page"] or 0))[:5]:
            ex.append({"word": strip_accents(norm(rec["pforms"][n])).split(",")[0].strip(), "entry_id": rec["entry_id"],
                       "parks_page": rec["page"], "class": rec["class"], "gloss": rec["gloss"],
                       "note": f"dictionary form_{n} of {rec['headword']}"})
        return ex

    infl = [
        (1, "IND ta- (1/2 agent) + 1.A t-", "mode + agent prefix", "slots 10-11", "indicative mode, first/second-person agent; t- 'I'",
         "every dictionary form_1 is 1sg indicative (Parks Tables 8-9, p.34-35)"),
        (2, "IND ti- (3 agent)", "mode prefix", "slot 10", "indicative mode, third-person agent (Ø-)",
         "every dictionary form_2 is 3sg indicative (Parks Table 8, p.34)"),
        (3, "IMPF -huʔ / -:hus", "aspect suffix", "slot 27", "imperfective aspect 'is ...-ing'",
         "every dictionary form_3 is imperfective (Parks Table 17, p.45-47)"),
        (4, "GER irii- + ra- ... + SUB (-a/-i/-Ø/-u/-wi)", "proclitic + mode + subordination suffix", "slots 4, 10, 28",
         "gerundial/absolutive subordinate 'the one who / when ...'", "every dictionary form_4 is gerundial (Parks Tables 8, 17)"),
        (5, "INT -his + -ta (-ista/-sta/-ksta)", "aspect suffix", "slots 27, 29", "intentive 'is going to ...'",
         "every dictionary form_5 is intentive (Parks Table 17, p.47)"),
    ]
    for n, label, cat, slot, meaning, src in infl:
        hosts = pf_words(n)
        affixes_out.append({"affix": label, "category": cat, "slot": slot, "meaning": meaning,
                            "frequency": len(hosts), "examples": pf_examples(n, hosts),
                            "sources": [src, "paradigmatic_forms table"], "confidence": "high",
                            "confidence_reasons": ["structural: identified by paradigm position, not by string match"]})

    # ---- Appendix 1 modes / persons
    app = defaultdict(dict)
    for r in conn.execute("select verb_heading, mode, person_number, skiri_form, english_form, source_page from verb_paradigms"):
        app[(r[1], r[2])][strip_accents(norm(r[3])).split(",")[0].strip()] = {"verb": r[0], "english": r[4], "page": r[5]}
    mode_labels = {
        "negative_indicative_perfective": ("NEG.IND kaakaa-/kaaki-", "mode prefix", "slot 10", "negative indicative"),
        "assertive_perfective": ("ASSR rii-", "mode prefix", "slot 10", "assertive / emphatic"),
        "contingent_perfective": ("CONT i-/ri-", "mode prefix", "slot 10", "contingent (future, mild imperative)"),
        "potential_perfective": ("POT kuus-/kaas- ... i-", "mode prefix (discontinuous)", "slot 10 + 19", "potential 'might, will'"),
        "absolutive_perfective": ("ABS ra-", "mode prefix", "slot 10", "absolutive (questions, narration)"),
        "subjunctive_perfective_subordinate": ("SUBJ aa-/ii-", "mode prefix", "slot 10", "subjunctive (wish, unreal)"),
        "infinitive_perfective_subordinate": ("INF ra- ... ku-", "mode prefix (discontinuous)", "slot 10 + 16", "infinitive 'for X to ...'"),
        "contingent_perfective_subordinate": ("CONT.SUB i-/ri- + SUB", "mode prefix", "slot 10", "conditional 'if/when'"),
    }
    for mode, (label, cat, slot, meaning) in mode_labels.items():
        words = {}
        for (m, p), d in app.items():
            if m == mode:
                words.update(d)
        ex = [{"word": w, "appendix1_verb": d["verb"], "gloss": d["english"], "parks_page": d["page"]} for w, d in list(words.items())[:5]]
        affixes_out.append({"affix": label, "category": cat, "slot": slot, "meaning": meaning, "frequency": len(words),
                            "examples": ex, "sources": ["Parks Appendix 1 paradigms (verb_paradigms table)", "Parks Table 8, p.34"],
                            "confidence": "high", "confidence_reasons": ["structural: identified by paradigm cell"]})
    person_labels = {
        "2sg": ("2.A s-", "agent prefix", "slot 11", "second-person agent 'you'"),
        "1du_incl": ("1.DU.IN.A acir-", "agent prefix", "slot 12", "you-and-I agent"),
        "1pl_incl": ("1.PL.IN a- + rak-", "agent + plural prefix", "slots 12-13", "we (inclusive) agent"),
        "1pl_excl": ("PL rak- (with 1.A t-)", "plural prefix", "slot 13", "we (exclusive) agent"),
        "2pl": ("PL rak- (with 2.A s-)", "plural prefix", "slot 13", "you (plural) agent"),
        "3pl": ("3.PL -aahuʔ / raar- / ir-", "plural marking", "slots 13, 23 / suffix", "they (plural) agent"),
    }
    for pn, (label, cat, slot, meaning) in person_labels.items():
        words = {}
        for (m, p), d in app.items():
            if p == pn:
                words.update(d)
        ex = [{"word": w, "appendix1_verb": d["verb"], "gloss": d["english"], "parks_page": d["page"]} for w, d in list(words.items())[:5]]
        affixes_out.append({"affix": label, "category": cat, "slot": slot, "meaning": meaning, "frequency": len(words),
                            "examples": ex, "sources": ["Parks Appendix 1 paradigms", "Parks Tables 9-10, p.35-36"],
                            "confidence": "high", "confidence_reasons": ["structural: identified by paradigm cell"]})
    words = {}
    for (m, p), d in app.items():
        if p in ("1du_excl", "2du", "3du"):
            words.update({w: v for w, v in d.items() if w.startswith("si")})
    affixes_out.append({"affix": "DU si-", "category": "proclitic", "slot": "slot 5 (Table 12:6)", "meaning": "dual number",
                        "frequency": len(words),
                        "examples": [{"word": w, "appendix1_verb": d["verb"], "gloss": d["english"], "parks_page": d["page"]} for w, d in list(words.items())[:5]],
                        "sources": ["Parks Appendix 1", "Parks p.35"], "confidence": "high",
                        "confidence_reasons": ["counted only dual cells whose form begins with si-"]})

    # ---- noun suffix ending-matches for nouns WITHOUT etymology (medium)
    endings = [("uʔ", "NOM -uʔ"), ("kis", "DIM -kis"), ("kusuʔ", "AUG -kusuʔ"), ("hiriʔ", "LOC/INST -hiriʔ"),
               ("piriʔ", "LOC/INST -piriʔ"), ("kat", "LOC -kat")]
    for end, label in endings:
        hosts = {}
        for rec in records:
            if rec["method"] == "no_etymology" and (rec["class"] or "").startswith("N") and rec["hw_key"].endswith(end) and len(rec["hw_key"]) - len(end) >= 2:
                hosts[rec["hw_key"]] = rec
        if hosts:
            affixes_out.append(affix_record(label + " (ending match, no etymology)", hosts, "suffix",
                                            "noun derivation (Parks Table 5, p.31)", label,
                                            "headword ending only; Parks gives no etymology", "medium",
                                            ["segmentation by ending match, not confirmed by Parks etymology"]))

    affixes_out.sort(key=lambda a: -a["frequency"])
    for i, a in enumerate(affixes_out, 1):
        a["rank"] = i

    # ---- write outputs
    (outdir / "roots_ranked.json").write_text(json.dumps(roots_out, ensure_ascii=False, indent=1), encoding="utf-8")
    (outdir / "affixes_ranked.json").write_text(json.dumps(affixes_out, ensure_ascii=False, indent=1), encoding="utf-8")
    with (outdir / "segmentation_log.jsonl").open("w", encoding="utf-8") as fh:
        for rec in records:
            slim = {k: v for k, v in rec.items() if k not in ("pforms", "tags")}
            fh.write(json.dumps(slim, ensure_ascii=False) + "\n")
    (outdir / "variant_merges.json").write_text(json.dumps(variant_log, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["# Review log (auto-generated by scripts/root_extraction.py)", "",
             f"Entries processed: {len(records)}", "", "## Segmentation confidence", ""]
    for k in ("high", "medium", "low"):
        lines.append(f"- {k}: {stats[('confidence', k)]}")
    lines += ["", "## Segmentation method", ""]
    for k, v in sorted(((k[1], v) for k, v in stats.items() if k[0] == "method"), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Sound-change rules that explained headword surface forms", ""]
    for k, v in sorted(((k[1], v) for k, v in stats.items() if k[0] == "rule"), key=lambda x: -x[1]):
        lines.append(f"- Rule {k}: {v} words")
    lines += ["", "## Root surface variants merged under one underlying form", ""]
    for v in variant_log:
        lines.append(f"- **{v['underlying']}** ~ {v['variant']} — Rule {v['rule']} ({v['note']}); shared gloss {v['shared_gloss']}; "
                     f"variant words: {', '.join(v['variant_words'])} — confidence {v['confidence']}")
    lines += ["", "## Roots flagged medium/low (top 150 by frequency)", ""]
    for r in [r for r in roots_out if r["confidence"] != "high"][:150]:
        lines.append(f"- #{r['rank']} **{r['root']}** '{r['gloss']}' ({r['frequency']} words) — {r['confidence']}: "
                     + "; ".join(r["confidence_reasons"]) + "; gloss variants: "
                     + ", ".join(f"{g['gloss']}({g['n']})" for g in r["gloss_variants"][:5]))
    lines += ["", "## Entries whose segmentation is LOW confidence (needs speaker/linguist review)", ""]
    for rec in [rec for rec in records if rec["confidence"] == "low" and rec["method"] != "no_etymology"]:
        lines.append(f"- {rec['headword']} ({rec['entry_id']}, p.{rec['page']}) — pieces: {' + '.join(rec.get('pieces', []))} — "
                     + "; ".join(rec["reasons"]))
    lines += ["", f"## Entries with no Parks etymology: {stats[('method', 'no_etymology')]}", "",
              "Segmentation was not attempted for these; they count toward a root only when their own headword is the root.", ""]
    byc = Counter(rec["class"] for rec in records if rec["method"] == "no_etymology")
    for k, v in byc.most_common(12):
        lines.append(f"- {k}: {v}")
    (outdir / "review_log_auto.md").write_text("\n".join(lines), encoding="utf-8")

    summary = {"entries": len(records), "roots": len(roots_out), "affixes": len(affixes_out),
               "variant_merges": len(variant_log),
               "confidence": {k[1]: v for k, v in stats.items() if k[0] == "confidence"},
               "methods": {k[1]: v for k, v in stats.items() if k[0] == "method"}}
    (outdir / "stats.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    out(json.dumps(summary, indent=1))
    out("TOP 40 ROOTS:")
    for r in roots_out[:40]:
        out(f"  {r['rank']:3} {r['root']:14} {r['frequency']:4}  {str(r['gloss']):22} {r['class']:28} {r['confidence']:6} {r['semantic_domains']}")


if __name__ == "__main__":
    main()
