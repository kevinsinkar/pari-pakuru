#!/usr/bin/env python3
"""Per-lexeme evidence (channels E1-E7), sense assignment and tiers.

`analyse(conn)` returns everything later stages need; nothing here writes files.
See PLAN.md / METHOD.md for the reasoning behind each channel.
"""
import difflib
import itertools
import math
import re
from collections import Counter, defaultdict

from bluebook import IRREGULAR, match_seams, parks_clean, skel
from common import DB_PATH, load_json, norm, segments, strip_accents
from etymology import LABEL_CHUNK, MIN_LABEL_COUNT, PREVERBS, align_all, json_pieces, parse_etymology
from lexemes import clean_form, load_rows, resolve_duplicates
from tiers import assign_tier

# v1 helpers that were read and audited before reuse: the rule-by-rule engine
# trace, V+V glottal epenthesis, and single-rule piece location.
from root_extraction import glottal_join, locate_pieces, trace_engine  # noqa: E402
import stem_extractor  # noqa: E402
import seams  # noqa: E402
from proposals import propose_all  # noqa: E402

from pathlib import Path

MANUAL_DECISIONS = Path(__file__).resolve().parent / "decisions_manual.json"

ANALYSIS_KINDS = ("analysis", "identity", "underlying")
SENSE_EVIDENCED = ("aligned", "literal", "entry_gloss", "inherited")
MIN_SUPPORT = 2          # other lexemes that must share a sense for E4
MAX_OPTIONAL_RULES = 2   # an "exact" reproduction may lean on at most this many optional rules

GLOSS_STOP = set("""a an the to be of as or and i.e e.g ref esp etc one ones someone something
somebody s which that this it its is are was by for with usu also said used when where
pl sg du subj obj an inan""".split())


# words that, alone, do not show which piece a gloss belongs to
WEAK_WORDS = {"in", "on", "at", "of", "to", "up", "down", "out", "off", "into", "by", "for", "one", "have", "get"}

LABEL_FUNCTION_WORDS = {"in", "on", "at", "of", "to", "up", "down", "out", "off", "into", "by",
                        "for", "one", "have", "caus", "mak", "get"}

# words too general to show that two glosses mean the same thing
LINK_STOP = {"have", "get", "here", "there", "thing", "not", "can", "with", "from", "into", "when",
             "who", "what"}

# ---------------------------------------------------------------------------
# Gloss handling
# ---------------------------------------------------------------------------

def gloss_stems(text):
    """Content stems of an English gloss (prepositions are kept: they carry locative senses)."""
    stems = set()
    text = re.sub(r"\(.*?\)", " ", (text or "").lower())
    for w in re.findall(r"[a-z]+", text):
        w = IRREGULAR.get(w, w)
        if w in GLOSS_STOP or len(w) < 2:
            continue
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss"):
                w = w[: -len(suf)]
                break
        if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "els":
            w = w[:-1]
        if w.endswith("e") and len(w) > 3:
            w = w[:-1]
        stems.add(IRREGULAR.get(w, w))
    return stems


TAIL = re.compile(r",?\s+(as|said|usu|esp|ref|i\.e|e\.g|when|where|such as|by means)\b.*$")


def first_clauses(glosses):
    """The heads of a definition's clauses, with commentary removed.

    'come; (idiom) be here, said when someone has arrived' -> ['come', 'be here'].
    Parentheses and tails such as ', as a hide being tanned' carry incidental
    words that would chain unrelated senses together.
    """
    outp = []
    for g in glosses:
        d = re.sub(r"\(.*?\)", " ", g["definition"] if isinstance(g, dict) else g)
        for clause in re.split(r"[;.]", d):
            head = TAIL.sub("", clause.strip()).strip(" ,")
            if head:
                outp.append(head)
    return outp


def gloss_label(text):
    """A short normalised label for a gloss: 'to go' / 'going' / 'go.' -> 'go'."""
    g = re.sub(r"\(.*?\)", "", (text or "").lower()).strip(" .;,")
    g = re.split(r"[;,]", g)[0].strip()
    g = re.sub(r"^(to be|to|be|the|a|an)\s+", "", g)
    g = re.sub(r"[^a-z/ \-]", "", g).strip()
    return g


# ---------------------------------------------------------------------------
# E2: sound-change round trip
# ---------------------------------------------------------------------------

def _targets(lex):
    """Headword alternates as plain strings (multiword and hyphenated forms joined)."""
    outp = []
    for alt in lex["alternates"]:
        alt = alt.split("/")[0]
        t = re.sub(r"[^a-zʔØ]", "", alt)
        if t and t not in outp:
            outp.append(t)
    return outp


def _is_preverb_piece(pieces, i):
    p = pieces[i]
    if p["form"] not in PREVERBS or p.get("gloss_kind") == "aligned":
        return False
    same_word = [q for q in pieces if q["word"] == p["word"]]
    return p is not same_word[-1]


def _surface_variants(pieces):
    """Lists of (piece_index, form) to try: with/without preverbs, full/min optional forms."""
    idx_all = list(range(len(pieces)))
    idx_nopv = [i for i in idx_all if not _is_preverb_piece(pieces, i)]
    index_sets = [("preverbs_outside_stem", idx_nopv)]
    if idx_nopv != idx_all:
        index_sets.append(("preverbs_in_stem", idx_all))
    seen = []
    for name, idxs in index_sets:
        opt = [i for i in idxs if pieces[i]["form"] != pieces[i]["form_min"]]
        choices = [(True,) * len(opt), (False,) * len(opt)]
        if 1 < len(opt) <= 3:
            choices = list(itertools.product((True, False), repeat=len(opt)))
        for ch in choices:
            use_full = dict(zip(opt, ch))
            forms = [(i, pieces[i]["form"] if use_full.get(i, True) else pieces[i]["form_min"]) for i in idxs]
            key = tuple(forms)
            if key not in seen:
                seen.append(key)
                yield name, forms


def _by_word(pieces, forms):
    words = defaultdict(list)
    for i, f in forms:
        words[pieces[i]["word"]].append(f)
    return [words[w] for w in sorted(words)]


def _boundaries(forms, target):
    """Offsets in `target` where consecutive pieces meet, each as [lo, hi]."""
    concat = "".join(f for _, f in forms)
    cuts, acc = [], 0
    for _, f in forms[:-1]:
        acc += len(f)
        cuts.append(acc)
    if concat == target:
        return [[c, c] for c in cuts]
    sm = difflib.SequenceMatcher(None, concat, target, autojunk=False)
    ops = sm.get_opcodes()
    outp = []
    for c in cuts:
        lo = hi = None
        for tag, i1, i2, j1, j2 in ops:
            if tag == "equal" and i1 <= c <= i2:
                lo = hi = j1 + (c - i1)
                break
            if tag != "equal" and i1 <= c <= i2:
                lo, hi = j1, j2
                break
        if lo is None:
            lo, hi = 0, len(target)
        outp.append([lo, hi])
    return outp


def is_word_like(lex):
    """Verb stems and bound (hyphenated) entries are not free words: word-edge rules do not apply."""
    if (lex["class"] or "").startswith("V"):
        return False
    hw = lex["headword"].split(",")[0].strip()
    return not (hw.endswith("-") or hw.startswith("-"))


def e2_roundtrip(lex, parsed):
    """Do Parks's pieces, joined by the named seam rules, give the headword?

    exact    the headword is produced by concatenation, by the seam engine (seams.py)
             or by the Parks rule engine; every rule used is recorded
    partial  a produced form matches only when vowel length, ʔ and h are ignored,
             or the pieces can only be located one at a time
    fail     neither
    """
    pieces = parsed["pieces"]
    res = {"status": None, "method": None, "rules": [], "target": None, "surface_pieces": [],
           "boundaries": [], "preverb_handling": None}
    if not pieces:
        return res
    targets = _targets(lex)
    nominal = (lex["class"] or "").startswith("N")
    word_like = is_word_like(lex)
    best_partial = None

    def hit(method, rules, t, forms, name, status="exact"):
        return dict(status=status, method=method, rules=rules, target=t,
                    surface_pieces=[f for _, f in forms], piece_index=[i for i, _ in forms],
                    boundaries=_boundaries(forms, t), preverb_handling=name)

    for name, forms in _surface_variants(pieces):
        words = _by_word(pieces, forms)
        concat = "".join("".join(w) for w in words)
        for t in targets:
            if concat == t:
                res.update(hit("concatenation", [], t, forms, name))
                return res
        seam = seams.derive_words(words, word_like)
        for t in targets:
            if t in seam:
                n_opt = sum(1 for r in set(seam[t]) if seams.RULES[r]["optional"])
                if n_opt <= MAX_OPTIONAL_RULES:
                    res.update(hit("seam rules", seam[t], t, forms, name))
                    return res
                if best_partial is None:
                    best_partial = hit("seam rules (needs %d optional rules)" % n_opt, seam[t], t, forms, name,
                                       status="partial")
        legacy = []
        for flag, label in ((nominal, "Parks rule engine"), (not nominal, "Parks rule engine (other class)")):
            surf, fired = [], []
            for w in words:
                sfc, f = trace_engine(w, nominal=flag)
                surf.append(sfc)
                fired += ["R" + r for r in f if "R" + r not in fired]
            legacy.append((label, "".join(surf), fired))
        for method, surface, rules in legacy:
            for t in targets:
                if surface == t:
                    res.update(hit(method, rules, t, forms, name))
                    return res
        if best_partial is None:
            cands = [("concatenation", concat, [])] + [("seam rules", sfc, rl) for sfc, rl in sorted(seam.items())] + legacy
            for t in targets:
                tsk = skel(t)
                for method, surface, rules in cands:
                    if skel(surface) == tsk:
                        best_partial = hit(method + " (vowel length, ʔ and h ignored)", rules, t, forms, name,
                                           status="partial")
                        break
                if best_partial:
                    break
    if best_partial:
        res.update(best_partial)
        return res
    for name, forms in _surface_variants(pieces):
        flat = [f for _, f in forms]
        for t in targets:
            ok, found, leftover = locate_pieces(t, flat)
            if ok and len(leftover) <= 2:
                res.update(hit("pieces located one at a time", sorted({c for _, _, c, _ in found if c}), t,
                               forms, name, status="partial"))
                return res
    res.update(status="fail", target=targets[0] if targets else None)
    return res


# ---------------------------------------------------------------------------
# E3: paradigm evidence
# ---------------------------------------------------------------------------

def _form_variants(s):
    return [clean_form(v) for v in re.split(r"[;,]", s or "") if clean_form(v)]


def e3a_stem(lex):
    """Does headword + verb class + preverb predict the attested form 2?"""
    f2 = lex["forms"].get("2")
    if not f2 or not (lex["class"] or "").startswith("V"):
        return None
    try:
        pred, _ = stem_extractor.predict_form_2(lex["headword"], lex["verb_class"] or "",
                                                lex["stem_preverb"] or "", lex["class"] or "")
    except Exception:
        return {"status": "error"}
    pred = clean_form(pred)
    att = _form_variants(f2)
    if pred in att:
        return {"status": "exact", "predicted": pred}
    if any(pred.replace("ʔ", "") == a.replace("ʔ", "") for a in att):
        return {"status": "close", "predicted": pred}
    return {"status": "miss", "predicted": pred}


def _first(forms, n):
    v = _form_variants(forms.get(str(n)))
    return v[0] if v else None


def root_tails(simplex):
    """How a verb root is realised at the right edge of each paradigm form.

    Forms 2, 3 and 5 share the prefix ti-; whatever follows the part that form 2
    and form n have in common is the aspect ending.  One more character is kept
    to anchor the ending on the root.  Form 4 carries the subordinate suffix,
    which depends on the verb class, so its last three characters are compared.
    """
    f2 = _first(simplex["forms"], 2)
    tails = {}
    if not f2:
        return tails
    for n in (3, 5):
        fn = _first(simplex["forms"], n)
        if not fn:
            continue
        k = 0
        while k < min(len(f2), len(fn)) and f2[k] == fn[k]:
            k += 1
        want = max(len(fn) - k + 1, 4)
        tails[str(n)] = fn[-min(want, max(2, len(fn) - 2)):]
    f4 = _first(simplex["forms"], 4)
    if f4:
        tails["4"] = f4[-3:]
    tails["2"] = f2[-min(3, max(2, len(f2) - 2)):]
    return tails


def _edit1(a, b):
    """True when a and b differ by at most one substitution, insertion or deletion."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b):
        a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def _tail_agrees(form, tail):
    """'yes', 'near' or 'no': does `form` end the way the root's own form does?

    The first segment of the tail sits at the junction with whatever precedes
    the root, where sound changes apply (ʔ-epenthesis after a vowel, w > p and
    h-loss after a consonant), so the tail may match without it.
    """
    if form.endswith(tail):
        return "yes"
    seg = 2 if tail[:2] in ("aa", "ii", "uu") else 1
    short = tail[seg:]
    if len(short) >= 2 and form.endswith(short):
        return "yes"
    for t in (tail, short) if len(short) >= 3 else (tail,):
        for d in (-1, 0, 1):
            if len(t) + d >= 2 and _edit1(form[-(len(t) + d):], t):
                return "near"
    return "no"


def _class_family(lex):
    """Descriptive, locative and active verbs take different endings (Parks Table 17)."""
    gc = (lex["class"] or "").split(",")[0].strip()
    fam = "D" if gc == "VD" else "L" if gc == "VL" else "A"
    return fam, (lex["verb_class"] or "").split(",")[0].strip()


def paradigm_signature(lex):
    return root_tails(lex)


def e3b_final_root(lex, final_form, simplex_by_form):
    """Does a compound inflect at its right edge like its final root does alone?

    status
        'confirm'       every compared form ends like the root's own form, same verb class
        'class_differs' Parks gives the two a different verb class, so endings are not comparable
        'near'          an ending differs by one letter: recorded, counts neither way
        'mismatch'      an aspect ending (form 3 or 5) differs outright
    """
    sims = [s for s in simplex_by_form.get(final_form, []) if s["lexeme_id"] != lex["lexeme_id"]]
    if not sims:
        return None
    results = []
    for s in sims:
        tails = root_tails(s)
        compared, verdicts = [], {}
        for n in ("2", "3", "4", "5"):
            mine = _first(lex["forms"], n)
            if mine and n in tails:
                compared.append(n)
                verdicts[n] = _tail_agrees(mine, tails[n])
        if len(compared) < 2 or not ({"3", "5"} & set(compared)):
            continue
        same_class = _class_family(lex) == _class_family(s)
        if not same_class:
            status = "class_differs"      # a different inflection class: endings are not comparable
        elif all(v == "yes" for v in verdicts.values()):
            status = "confirm"
        elif any(verdicts.get(n) == "no" for n in ("3", "5")):
            status = "mismatch"
        else:
            status = "near"
        results.append({"simplex": s["lexeme_id"], "compared": compared, "verdicts": verdicts,
                        "root_tails": tails, "same_verb_class": same_class, "status": status})
    if not results:
        return None
    order = {"confirm": 0, "class_differs": 1, "near": 2, "mismatch": 3}
    results.sort(key=lambda r: (order[r["status"]], r["simplex"]))
    return results[0]


# ---------------------------------------------------------------------------
# E5: Blue Book seams
# ---------------------------------------------------------------------------

def _stem_start(form, stem):
    """Offset range in `form` where the stem begins, or None."""
    st = skel(stem)
    if not st:
        return None
    need = max(1, len(st) - 1)
    best = None
    for i in range(len(form)):
        s = skel(form[i:])
        k = 0
        while k < min(len(s), len(st)) and s[k] == st[k]:
            k += 1
        if k >= need and (len(st) > 2 or k == len(st)):
            best = i                      # keep the rightmost start
    if best is None:
        return None
    lo = best
    while lo > 0 and form[lo - 1] in "ʔh":
        lo -= 1
    return [lo, best]


def _overlap(a, b, tol=0):
    return a[0] - tol <= b[1] and b[0] - tol <= a[1]


def e5_seams(lex, e2, seam_matches):
    """Compare Blue Book seams with the boundaries of the analysis."""
    if not seam_matches:
        return None
    n_pieces = len(e2.get("surface_pieces") or [])
    internal = e2.get("boundaries") or []
    notes, hits, misses, edge = [], 0, 0, False
    for m in seam_matches:
        for t in m["targets"]:
            if t.get("entry_id") not in lex["member_ids"]:
                continue
            if t["type"] == "headword":
                if e2.get("target") != m["target"]:
                    continue
                for b in m["boundaries"]:
                    if any(_overlap(b, ib) for ib in internal):
                        hits += 1
                    else:
                        misses += 1
                notes.append({"bb": m["bb_token"], "lesson": m["lesson"], "page": m["page"],
                              "on": "headword", "seams": m["boundaries"]})
            elif t["type"] == "form":
                start = _stem_start(m["target"], e2.get("target") or lex["hw_key"])
                if start is None:
                    continue
                for b in m["boundaries"]:
                    if _overlap(b, start):
                        edge = True
                    elif b[0] > start[1]:
                        shifted = [[ib[0] + start[0] - 1, ib[1] + start[1] + 1] for ib in internal]
                        if any(_overlap(b, sb) for sb in shifted):
                            hits += 1
                        else:
                            misses += 1
                notes.append({"bb": m["bb_token"], "lesson": m["lesson"], "page": m["page"],
                              "on": "form %s" % t.get("form_number"), "seams": m["boundaries"],
                              "stem_starts_at": start})
    if not notes:
        return None
    if n_pieces <= 1:
        status = "confirm" if edge and not misses else None
        flags = ["bb_finer_than_parks"] if (hits + misses) else []
    else:
        status = "confirm" if hits else ("contradict" if misses else None)
        flags = ["bb_finer_than_parks"] if (hits and misses) else []
    return {"status": status, "seams_on_boundaries": hits, "seams_elsewhere": misses,
            "stem_edge_seam": edge, "flags": flags, "attestations": notes}


# ---------------------------------------------------------------------------
# Roles and senses
# ---------------------------------------------------------------------------

def load_manual_decisions():
    if MANUAL_DECISIONS.exists():
        return load_json(MANUAL_DECISIONS)
    return []


def role_statistics(parsed_by_lex):
    """For every piece form: how often it occurs, and how often under each label."""
    total, labelled, final_share = Counter(), defaultdict(Counter), defaultdict(Counter)
    for parsed in parsed_by_lex.values():
        pieces = parsed["pieces"]
        for i, p in enumerate(pieces):
            total[p["form"]] += 1
            last = p is [q for q in pieces if q["word"] == p["word"]][-1]
            if p["gloss_kind"] == "label":
                labelled[p["form"]][p["gloss"]] += 1
                final_share[(p["form"], p["gloss"])]["final" if last else "nonfinal"] += 1
    return total, labelled, final_share


def _class_group(gc):
    gc = (gc or "").split(",")[0].strip()
    return "V" if gc.startswith("V") else "N" if gc.startswith("N") else "other"


def assign_roles(parsed_by_lex, manual, lex_by_id):
    """Mark every piece as grammatical, preverb or lexical.  Returns the role defaults used.

    A piece is grammatical when Parks prints a grammatical label for it.  A piece
    he leaves unlabelled is grammatical only by a recorded default: either the
    form carries a label in at least half of its occurrences (label statistics),
    or a manual decision with a source citation says so (decisions_manual.json).
    A piece with its own lexical gloss in the literal translation is always lexical.
    """
    total, labelled, final_share = role_statistics(parsed_by_lex)
    manual_role = {d["form"]: d for d in manual if d.get("type") == "role_default"}
    defaults = {}
    for form in sorted(total):
        n_lab = sum(labelled[form].values())
        if form in manual_role:
            d = manual_role[form]
            defaults[form] = {"role": d["role"], "label": d.get("label"), "basis": "manual",
                              "label_by_class": d.get("label_by_class"), "classes": d.get("classes"),
                              "unless_literal_has": d.get("unless_literal_has"),
                              "position": d.get("position", "any"), "evidence": d.get("evidence"),
                              "occurrences": total[form], "labelled": dict(labelled[form])}
        elif n_lab >= MIN_LABEL_COUNT and n_lab / total[form] >= 0.5:
            lab = labelled[form].most_common(1)[0][0]
            pos = final_share[(form, lab)]
            where = "final" if pos["final"] >= 0.8 * sum(pos.values()) else (
                "nonfinal" if pos["nonfinal"] >= 0.8 * sum(pos.values()) else "any")
            defaults[form] = {"role": "grammatical", "label": lab, "basis": "label_statistics",
                              "position": where, "occurrences": total[form], "labelled": dict(labelled[form]),
                              "evidence": "Parks prints the label %s for this form in %d of its %d occurrences"
                                          % (lab, labelled[form][lab], total[form])}
    for lid, parsed in parsed_by_lex.items():
        pieces = parsed["pieces"]
        group = _class_group(lex_by_id[lid]["class"])
        for i, p in enumerate(pieces):
            last = p is [q for q in pieces if q["word"] == p["word"]][-1]
            p["label_inferred"] = False
            if p["gloss_kind"] == "label":
                p["role"], p["label"] = "grammatical", p["gloss"]
            elif _is_preverb_piece(pieces, i):
                p["role"], p["label"] = "preverb", "PREV"
            elif p["gloss_kind"] == "aligned":
                p["role"], p["label"] = "lexical", None
            elif p["form"] in defaults and defaults[p["form"]]["role"] == "grammatical":
                d = defaults[p["form"]]
                where = d.get("position", "any")
                ok_pos = where == "any" or (where == "final") == last
                ok_cls = not d.get("classes") or group in d["classes"]
                lexical_words = set().union(*(gloss_stems(x) for x in d.get("unless_literal_has") or []))                     if d.get("unless_literal_has") else set()
                says_lexical = bool(lexical_words & gloss_stems(p.get("phrase") or parsed.get("literal") or ""))
                if ok_pos and ok_cls and not says_lexical:
                    lab = (d.get("label_by_class") or {}).get(group) or d["label"]
                    p["role"], p["label"], p["label_inferred"] = "grammatical", lab, True
                else:
                    p["role"], p["label"] = "lexical", None
            else:
                p["role"], p["label"] = "lexical", None
    # a word cannot consist of grammatical pieces only: if every piece ended up grammatical and
    # the last one got its label by default, that piece is the root after all (raar+raar)
    for parsed in parsed_by_lex.values():
        pieces = parsed["pieces"]
        if pieces and not any(p["role"] == "lexical" for p in pieces):
            inferred = [p for p in pieces if p.get("label_inferred")]
            if inferred:
                inferred[-1]["role"], inferred[-1]["label"], inferred[-1]["label_inferred"] = "lexical", None, False
    merges = {}
    for d in manual:
        if d.get("type") == "label_merge":
            for lab in d["labels"]:
                merges[(d["form"], lab)] = d["as"]
    for parsed in parsed_by_lex.values():
        for p in parsed["pieces"]:
            if p["role"] == "grammatical" and (p["form"], p["label"]) in merges:
                p["label_printed"] = p["label"]
                p["label"] = merges[(p["form"], p["label"])]
    return defaults


class SenseInventory:
    """Senses of every lexical piece form, clustered from Parks's own glosses."""

    def __init__(self):
        self.anchors = defaultdict(list)      # form -> [anchor]
        self.clusters = {}                    # form -> [cluster]
        self.df = Counter()                   # stem -> number of forms whose senses use it

    def add_anchor(self, form, kind, text, lexeme_id, extra=None):
        st = gloss_stems(text)
        if not st:
            return
        a = {"kind": kind, "text": text, "stems": st, "lexeme_id": lexeme_id}
        a.update(extra or {})
        self.anchors[form].append(a)

    def build(self, manual):
        self.clusters, self.df = {}, Counter()
        merges = defaultdict(list)
        blocked = defaultdict(set)
        for d in manual:
            if d.get("type") == "sense_merge":
                merges[d["form"]].append(d)
            elif d.get("type") == "link_block":
                blocked[d["form"]] |= set(d["stems"]) | set().union(*(gloss_stems(x) for x in d["stems"]))
        for form in sorted(self.anchors):
            anchors = self.anchors[form]
            # stored-parse glosses seed senses only when Parks's own glosses give none
            strong = [a for a in anchors if a["kind"] != "stored_parse"]
            use = strong if strong else anchors
            parent = list(range(len(use)))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            for i in range(len(use)):
                for j in range(i + 1, len(use)):
                    shared = (use[i]["stems"] & use[j]["stems"]) - LINK_STOP - blocked[form]
                    if shared and not (shared - WEAK_WORDS):
                        if (use[i]["stems"] - WEAK_WORDS) and (use[j]["stems"] - WEAK_WORDS):
                            shared = set()      # 'liquid in a container' ~ 'light in color': no
                    same_entry = (use[i].get("lexeme_id") and use[i]["lexeme_id"] == use[j].get("lexeme_id")
                                  and {use[i]["kind"], use[j]["kind"]} == {"standalone", "aligned"}
                                  and (use[i].get("identity") or use[j].get("identity")))
                    if shared or same_entry:
                        ri, rj = find(i), find(j)
                        if ri != rj:
                            parent[max(ri, rj)] = min(ri, rj)
            for d in merges[form]:
                want = [gloss_stems(s) for s in d["senses"]]
                idxs = [i for i, a in enumerate(use) if any(a["stems"] & w for w in want)]
                for i in idxs[1:]:
                    ri, rj = find(idxs[0]), find(i)
                    if ri != rj:
                        parent[max(ri, rj)] = min(ri, rj)
            groups = defaultdict(list)
            for i, a in enumerate(use):
                groups[find(i)].append(a)
            clusters = []
            for g in groups.values():
                stems = set().union(*(a["stems"] for a in g))
                # name the sense after the morpheme's own dictionary entry when it has one,
                # else after the gloss Parks gives it most often
                # name the sense after the gloss Parks gives the piece in compounds when he
                # gives it at least twice; otherwise after the morpheme's own dictionary entry
                al = Counter(gloss_label(a["text"]) for a in g if a["kind"] == "aligned")
                if al and max(al.values()) >= 2:
                    labels = al
                else:
                    labels = Counter(gloss_label(a["text"]) for a in g if a["kind"] == "standalone") or al
                if not labels:
                    labels = Counter(gloss_label(a["text"]) for a in g if a["kind"] == "derived")
                if not labels:
                    labels = Counter(gloss_label(a["text"]) for a in g if a["kind"] == "commutation")
                if not labels:
                    labels = Counter(gloss_label(a["text"]) for a in g)
                label = sorted(labels.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))[0][0] or "?"
                kinds = Counter(a["kind"] for a in g)
                gram = [a for a in g if a.get("gram_label")]
                if gram:
                    label = gloss_label(gram[0]["text"])
                # Parks glosses some pieces with nothing but 'in/on': for those, such a word is the evidence
                weak_ok = any(st and not (st - WEAK_WORDS)
                              for a in g if a["kind"] in ("aligned", "standalone", "derived", "manual")
                              for st in [gloss_stems(cl) for cl in a["text"].split(" ; ")])
                clusters.append({"form": form, "label": label, "stems": stems, "anchors": g, "weak_ok": weak_ok,
                                 "gram_label": gram[0]["gram_label"] if gram else None,
                                 "manual_evidence": gram[0].get("evidence") if gram else None,
                                 "n_aligned": kinds["aligned"], "n_standalone": kinds["standalone"],
                                 "n_derived": kinds["derived"], "n_commutation": kinds["commutation"],
                                 "stored_parse_only": not strong,
                                 "gloss_variants": Counter(a["text"].strip() for a in g if a["kind"] == "aligned")})
            clusters.sort(key=lambda c: (-(c["n_aligned"] + c["n_standalone"]), c["label"]))
            used = Counter()
            for c in clusters:
                used[c["label"]] += 1
                c["sense_id"] = "%s#%s" % (form, c["label"]) + ("" if used[c["label"]] == 1 else "~%d" % used[c["label"]])
            self.clusters[form] = clusters
        for form, clusters in self.clusters.items():
            for st in set().union(*(c["stems"] for c in clusters)) if clusters else ():
                self.df[st] += 1

    def weight(self, stem):
        return 1.0 / math.log(2 + self.df.get(stem, 0))

    def best(self, form, text, min_weight=0.0):
        """The cluster of `form` that best matches the English text, or (None, reason)."""
        clusters = self.clusters.get(form, [])
        if not clusters:
            return None, "no_sense_known"
        st = gloss_stems(text)
        scored = []
        for c in clusters:
            shared = c["stems"] & st
            if shared and not (shared - WEAK_WORDS) and (c["stems"] - WEAK_WORDS) and not c.get("weak_ok"):
                continue                        # 'on' alone does not pick out 'stretched out on a frame'
            if shared:
                scored.append((sum(self.weight(s) for s in shared), c))
        if not scored:
            return None, "no_overlap"
        scored.sort(key=lambda sc: (-sc[0], sc[1]["sense_id"]))
        if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 1e-9:
            return None, "ambiguous"
        if scored[0][0] < min_weight:
            return None, "weak_overlap"
        return scored[0][1], "ok"


def build_senses(lexemes, parsed_by_lex, manual):
    inv = SenseInventory()
    ignored = {(d["form"], gloss_label(d["gloss"])) for d in manual if d.get("type") == "ignore_anchor"}
    by_alt = defaultdict(list)
    for lex in lexemes:
        for alt in _targets(lex):
            by_alt[alt].append(lex)
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        stored = json_pieces(lex["constituent_elements"])
        mine = [p["form"] for p in parsed["pieces"]]
        aligned_stored = stored["glosses"] if stored and stored["forms"] == mine else None
        for i, p in enumerate(parsed["pieces"]):
            p["stored_gloss"] = None
            if aligned_stored and aligned_stored[i] and not LABEL_CHUNK.match(aligned_stored[i].strip()):
                p["stored_gloss"] = aligned_stored[i]
            if p["role"] != "lexical":
                continue
            if p["gloss_kind"] == "aligned":
                if (p["form"], gloss_label(p["gloss"])) in ignored:
                    continue
                inv.add_anchor(p["form"], "aligned", p["gloss"], lex["lexeme_id"],
                               {"identity": parsed["kind"] == "identity"})
            elif p["stored_gloss"]:
                inv.add_anchor(p["form"], "stored_parse", p["stored_gloss"], lex["lexeme_id"])
    # standalone dictionary entries: the piece is itself a headword
    forms_used = {p["form"] for parsed in parsed_by_lex.values() for p in parsed["pieces"] if p["role"] == "lexical"}
    forms_used |= {p["form_min"] for parsed in parsed_by_lex.values() for p in parsed["pieces"] if p["role"] == "lexical"}
    for form in sorted(forms_used):
        for lex in by_alt.get(form, []):
            text = " ; ".join(first_clauses(lex["glosses"]))
            inv.add_anchor(form, "standalone", text, lex["lexeme_id"],
                           {"class": lex["class"], "verb_class": lex["verb_class"], "preverbs": lex["preverbs"]})
    # a noun that is only root + NOM (or a single underlying form) shows the root's meaning
    # in its own first gloss: Parks, GO p.31, says -uʔ adds no meaning of its own
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        lexical = [p for p in parsed["pieces"] if p["role"] == "lexical"]
        others = [p for p in parsed["pieces"] if p["role"] != "lexical"]
        if len(lexical) == 1 and lex["glosses"] and all(p.get("label") == "NOM" for p in others) and (
                others or parsed["kind"] == "underlying"):
            inv.add_anchor(lexical[0]["form"], "derived", " ; ".join(first_clauses(lex["glosses"][:1])),
                           lex["lexeme_id"])
    for d in manual:
        if d.get("type") == "sense_anchor":
            inv.add_anchor(d["form"], "manual", d["gloss"], None,
                           {"gram_label": d.get("label"), "evidence": d.get("evidence")})
    inv.build(manual)
    return inv, by_alt


def assign_senses(lexemes, parsed_by_lex, inv):
    """Give every lexical piece occurrence a sense and say what the assignment rests on."""
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        entry_gloss = " ; ".join(g["definition"] for g in lex["glosses"])
        for p in parsed["pieces"]:
            p["sense_id"], p["sense_evidence"] = None, None
            if p["role"] != "lexical":
                continue
            form = p["form"]
            clusters = inv.clusters.get(form, [])
            if p["gloss_kind"] == "self":
                p["sense_evidence"] = "meaning_unknown_to_parks"
                continue
            if p["gloss_kind"] == "aligned":
                c, why = inv.best(form, p["gloss"])
                if c:
                    p["sense_id"], p["sense_evidence"] = c["sense_id"], "aligned"
                    continue
            phrase = p.get("phrase") or parsed.get("literal") or ""
            c, why = inv.best(form, phrase)
            if c:
                p["sense_id"], p["sense_evidence"] = c["sense_id"], "literal"
                p["_words"] = c["stems"] & gloss_stems(phrase)
                p["_by_commutation_only"] = not (c["n_aligned"] or c["n_standalone"] or c.get("n_derived")
                                                 or c.get("gram_label"))
                continue
            c, why2 = inv.best(form, entry_gloss)
            if c:
                p["sense_id"], p["sense_evidence"] = c["sense_id"], "entry_gloss"
                continue
            if p.get("stored_gloss"):
                c, _ = inv.best(form, p["stored_gloss"])
                if c:
                    p["sense_id"], p["sense_evidence"] = c["sense_id"], "stored_parse"
                    continue
            if len(clusters) == 1:
                p["sense_id"], p["sense_evidence"] = clusters[0]["sense_id"], "default_single_sense"
            elif not clusters:
                p["sense_evidence"] = "no_sense_known"
            else:
                p["sense_evidence"] = "unassigned_homonym"
        # one word of the literal translation cannot vouch for two pieces: a sense known only by
        # commutation loses the claim to a piece whose meaning Parks prints
        claimed = [p for p in parsed["pieces"] if p.get("sense_evidence") in ("aligned", "literal")]
        for p in claimed:
            if p.get("sense_evidence") != "literal" or not p.get("_by_commutation_only"):
                continue
            for q in claimed:
                if q is p or q.get("_by_commutation_only"):
                    continue
                q_words = q.get("_words") or gloss_stems(q.get("gloss") or "")
                if p.get("_words") and p["_words"] <= q_words:
                    p["sense_id"], p["sense_evidence"] = None, "word_claimed_by_another_piece"
                    break
        for p in parsed["pieces"]:
            p.pop("_words", None)
            p.pop("_by_commutation_only", None)


COMMUTATION_MIN = 3      # words that must agree before a commutation gloss counts as printed meaning


def add_commutation_anchors(lexemes, parsed_by_lex, inv):
    """Meanings shown by commutation, for pieces Parks never glosses on their own.

    In <icaahiks+kucuu, large person> the literal translation covers two pieces.
    If one piece's meaning is already established ('person') and its words
    account for part of the literal, the remainder ('large') is what the other
    piece contributes.  One such word proves little; the remainder becomes an
    anchor, and the inventory treats a sense as established this way only when
    at least COMMUTATION_MIN words agree.  Returns the number of anchors added.
    """
    added = 0
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        lexical = [p for p in parsed["pieces"] if p["role"] == "lexical"]
        if len(lexical) != 2 or any(p["dotted"] for p in lexical):
            continue
        a, b = lexical
        if a["gloss_kind"] != "phrase" or b["gloss_kind"] != "phrase" or a["phrase"] != b["phrase"]:
            continue
        def cluster_of(pc):
            return next((c for c in inv.clusters.get(pc["form"], []) if c["sense_id"] == pc.get("sense_id")), None)
        for known, other in ((a, b), (b, a)):
            if known.get("sense_evidence") != "literal":
                continue
            oc = cluster_of(other)
            if other.get("sense_evidence") in ("aligned", "literal") and oc and not oc.get("stored_parse_only"):
                continue                    # the other piece already has a meaning Parks prints
            cluster = cluster_of(known)
            if cluster is None or cluster.get("stored_parse_only"):
                continue
            rest = gloss_stems(known["phrase"]) - cluster["stems"] - LABEL_FUNCTION_WORDS
            if 1 <= len(rest) <= 2:
                words = []
                for word in re.findall(r"[a-z]+", re.sub(r"\(.*?\)", " ", known["phrase"].lower())):
                    if gloss_stems(word) and gloss_stems(word) <= rest and word not in words:
                        words.append(word)
                inv.add_anchor(other["form"], "commutation", " ".join(words), lex["lexeme_id"],
                               {"with": known["sense_id"], "literal": known["phrase"]})
                added += 1
    return added


def relabel_senses(lexemes, parsed_by_lex, inv):
    """Name each sense after the gloss that fits most of the words it is found in.

    A sense groups several of Parks's glosses (mind, feelings, thoughts).  Its
    label is the candidate gloss that shares a content word with the literal
    translation of the largest number of words where the sense was assigned on
    evidence.  Sense ids are rebuilt from the new labels.
    """
    texts = defaultdict(list)
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        for p in parsed["pieces"]:
            if p.get("sense_id") and p.get("sense_evidence") in ("aligned", "literal", "entry_gloss"):
                texts[p["sense_id"]].append(gloss_stems(p.get("gloss") or p.get("phrase") or parsed.get("literal") or ""))
    mapping = {}
    for form in sorted(inv.clusters):
        used = Counter()
        for c in inv.clusters[form]:
            cands = []
            for a in c["anchors"]:
                if a["kind"] == "aligned":
                    cands.append((0, gloss_label(a["text"])))
                elif a["kind"] in ("standalone", "derived"):
                    for clause in a["text"].split(" ; "):
                        cands.append((1, gloss_label(clause)))
                elif a["kind"] == "manual":
                    cands.append((-1, gloss_label(a["text"])))
                elif a["kind"] == "commutation":
                    for word in a["text"].split():
                        cands.append((2, word))
            cands = sorted({x for x in cands if x[1]})
            host = texts.get(c["sense_id"], [])
            best, best_key = c["label"], None
            for pri, lab in cands:
                # a candidate fits a word only if all its content words are in that word's literal
                # translation; otherwise a long gloss would win just by containing common words
                st = (gloss_stems(lab) - LABEL_FUNCTION_WORDS) or gloss_stems(lab)
                if not st:
                    continue                # 'be', or OCR debris: says nothing
                score = sum(1 for t in host if st <= t)
                key = (-1 if pri == -1 else 0, -score, pri, len(lab), lab)
                if best_key is None or key < best_key:
                    best, best_key = lab, key
            if host or c.get("gram_label"):
                c["label"] = best
            used[c["label"]] += 1
            new_id = "%s#%s" % (form, c["label"]) + ("" if used[c["label"]] == 1 else "~%d" % used[c["label"]])
            mapping[c["sense_id"]] = new_id
            c["sense_id"] = new_id
    for parsed in parsed_by_lex.values():
        for p in parsed["pieces"]:
            if p.get("sense_id"):
                p["sense_id"] = mapping.get(p["sense_id"], p["sense_id"])


def resolve_groups(lexemes, parsed_by_lex, inv, by_alt):
    """Resolve Parks's dotted compound stems to their own dictionary entries.

    In `<pirus+as.i, ...>` the dotted unit `as.i` is a stem that Parks lists as a
    headword of its own (as-i 'run').  The inner pieces of such a unit must not
    be read against the literal translation one by one: `as` here is not 'foot'.
    Each dotted unit is therefore matched to a headword; its inner pieces then
    take role and sense from that headword's own analysis.

    Adds to every piece of a resolved unit:
        stem_ref            lexeme id of the stem's entry
        stem_ref_evidence   'literal' when the literal translation shares a content word
                            with the stem's gloss, else 'form_only'
    """
    lex_by_id = {lex["lexeme_id"]: lex for lex in lexemes}
    stats = Counter()
    for lex in lexemes:
        parsed = parsed_by_lex[lex["lexeme_id"]]
        units = defaultdict(list)
        for pc in parsed["pieces"]:
            pc["stem_ref"], pc["stem_ref_evidence"] = None, None
            if pc["dotted"]:
                units[pc["group"]].append(pc)
        for g in sorted(units):
            members = units[g]
            cands = set()
            for forms in ([m["form"] for m in members], [m["form_min"] for m in members]):
                cands.add("".join(forms))
                cands.update(seams.derive(forms, False).keys())
                cands.update(seams.derive(forms, True).keys())
            matches = []
            for c in sorted(cands):
                for x in by_alt.get(c, []):
                    if x["lexeme_id"] != lex["lexeme_id"] and x not in matches:
                        matches.append(x)
            if not matches:
                stats["unit_not_a_headword"] += 1
                continue
            phrase = members[0].get("phrase") or parsed.get("literal") or ""
            pst = gloss_stems(phrase)
            scored = []
            for x in matches:
                xst = gloss_stems(" ; ".join(gl["definition"] for gl in x["glosses"]))
                shared = pst & xst
                same_group = _class_group(x["class"]) == _class_group(lex["class"])
                scored.append((sum(inv.weight(t) for t in shared), same_group, x))
            scored.sort(key=lambda t: (-t[0], not t[1], t[2]["lexeme_id"]))
            best = scored[0]
            if best[0] > 0:
                if len(scored) > 1 and abs(scored[1][0] - best[0]) < 1e-9 and scored[1][1] == best[1]:
                    stats["unit_ambiguous"] += 1
                    continue
                ref, ev = best[2], "literal"
            elif len(matches) == 1:
                ref, ev = matches[0], "form_only"
            else:
                stats["unit_ambiguous"] += 1
                continue
            stats["unit_resolved_" + ev] += 1
            for m in members:
                m["stem_ref"], m["stem_ref_evidence"] = ref["lexeme_id"], ev
    # inheritance: inner pieces take role and sense from the stem's own analysis
    for _ in range(4):
        changed = 0
        for lex in lexemes:
            parsed = parsed_by_lex[lex["lexeme_id"]]
            units = defaultdict(list)
            for pc in parsed["pieces"]:
                if pc.get("stem_ref"):
                    units[(pc["group"], pc["stem_ref"])].append(pc)
            for (g, ref), members in units.items():
                src = [q for q in parsed_by_lex[ref]["pieces"] if q["role"] != "preverb"]
                if [q["form"] for q in src] != [m["form"] for m in members]:
                    continue
                for m, q in zip(members, src):
                    if q["role"] != "lexical":
                        if m["role"] != q["role"] or m.get("label") != q.get("label"):
                            m["role"], m["label"], m["label_inferred"] = q["role"], q.get("label"), True
                            m["sense_id"], m["sense_evidence"] = None, None
                            changed += 1
                        continue
                    if q.get("sense_id") and q.get("sense_evidence") in SENSE_EVIDENCED and (
                            m.get("sense_id") != q["sense_id"] or m.get("sense_evidence") != "inherited"):
                        if m.get("sense_evidence") == "aligned":
                            continue            # Parks glosses the piece here: keep that
                        m["role"], m["label"] = "lexical", None
                        m["sense_id"], m["sense_evidence"] = q["sense_id"], "inherited"
                        m["inherited_from"] = ref
                        changed += 1
        if not changed:
            break
    # inner pieces of a resolved unit that could not inherit keep no unverified default
    for parsed in parsed_by_lex.values():
        for pc in parsed["pieces"]:
            if pc.get("stem_ref") and pc["role"] == "lexical" and pc.get("sense_evidence") in (
                    "default_single_sense", "entry_gloss", "stored_parse"):
                pc["sense_id"], pc["sense_evidence"] = None, "inside_stem_unanalysed"
    return dict(stats)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyse(conn):
    rows = load_rows(conn)
    lexemes, dup_decisions = resolve_duplicates(rows)
    manual = load_manual_decisions()

    parsed_by_lex = {}
    for lex in lexemes:
        parsed_by_lex[lex["lexeme_id"]] = parse_etymology(lex["raw_etymology"], _targets(lex))
    label_stats = align_all(list(parsed_by_lex.values()),
                            [(d["label"], d["form"]) for d in manual if d.get("type") == "label_anchor"])
    lex_by_id = {lex["lexeme_id"]: lex for lex in lexemes}
    role_defaults = assign_roles(parsed_by_lex, manual, lex_by_id)
    inv, by_alt = build_senses(lexemes, parsed_by_lex, manual)
    assign_senses(lexemes, parsed_by_lex, inv)
    n_commutation = add_commutation_anchors(lexemes, parsed_by_lex, inv)
    if n_commutation:
        inv.build(manual)                       # second pass, now with the commutation glosses
        assign_senses(lexemes, parsed_by_lex, inv)
    group_stats = resolve_groups(lexemes, parsed_by_lex, inv, by_alt)
    group_stats["commutation_anchors"] = n_commutation
    relabel_senses(lexemes, parsed_by_lex, inv)

    # ---- E2
    e2 = {lex["lexeme_id"]: e2_roundtrip(lex, parsed_by_lex[lex["lexeme_id"]]) for lex in lexemes}

    # ---- sense support: evidenced occurrences in lexemes whose analysis reproduces exactly
    support = defaultdict(set)
    for lex in lexemes:
        lid = lex["lexeme_id"]
        if e2[lid]["status"] != "exact":
            continue
        for p in parsed_by_lex[lid]["pieces"]:
            if p["role"] == "lexical" and p["sense_id"] and p["sense_evidence"] in SENSE_EVIDENCED:
                support[p["sense_id"]].add(lid)
    standalone_of = defaultdict(set)          # sense_id -> lexemes that are that piece as a headword
    sense_by_id = {}
    for form, clusters in inv.clusters.items():
        for c in clusters:
            sense_by_id[c["sense_id"]] = c
            for a in c["anchors"]:
                if a["kind"] == "standalone":
                    standalone_of[c["sense_id"]].add(a["lexeme_id"])

    # ---- E1 by citation: a headword with no printed analysis that Parks cites as a piece
    citation = {}
    for lex in lexemes:
        lid = lex["lexeme_id"]
        if parsed_by_lex[lid]["kind"] in ANALYSIS_KINDS:
            continue
        cites = []
        for sid, owners in standalone_of.items():
            if lid in owners:
                others = support[sid] - {lid}
                if others:
                    cites.append({"sense_id": sid, "cited_in": len(others), "examples": sorted(others)[:5]})
        if cites:
            cites.sort(key=lambda c: (-c["cited_in"], c["sense_id"]))
            citation[lid] = cites

    proposals = propose_all(
        lexemes, lambda x: parsed_by_lex[x]["kind"] in ANALYSIS_KINDS or x in citation,
        inv, support, gloss_stems, _targets, is_word_like)

    simplex_by_form = defaultdict(list)
    for lex in lexemes:
        if (lex["class"] or "").startswith("V") and lex["forms"]:
            for alt in _targets(lex):
                simplex_by_form[alt].append(lex)

    seam_matches, seam_counts = match_seams(conn)
    seams_by_entry = defaultdict(list)
    for m in seam_matches:
        for t in m["targets"]:
            if t.get("entry_id"):
                seams_by_entry[t["entry_id"]].append(m)

    records = []
    for lex in lexemes:
        lid = lex["lexeme_id"]
        parsed = parsed_by_lex[lid]
        r2 = e2[lid]
        pieces = parsed["pieces"]
        if parsed["kind"] in ANALYSIS_KINDS:
            e1 = "printed"
        elif lid in citation:
            e1 = "citation"
            r2 = {"status": "exact", "method": "the headword is the piece", "rules": [],
                  "target": _targets(lex)[0], "surface_pieces": [_targets(lex)[0]], "boundaries": [],
                  "preverb_handling": None}
        elif lid in proposals:
            e1 = "proposed"
            pr = proposals[lid]
            pieces = [dict(q, form_min=q["form"], word=0, group=i, dotted=False, bound=False,
                           label_inferred=False, gloss=None, gloss_kind=None, phrase=None)
                      for i, q in enumerate(pr["pieces"])]
            forms = list(enumerate(q["form"] for q in pieces))
            r2 = {"status": "exact", "method": "seam rules (proposed pieces)", "rules": pr["rules"],
                  "target": pr["target"], "surface_pieces": [q["form"] for q in pieces],
                  "piece_index": list(range(len(pieces))), "boundaries": _boundaries(forms, pr["target"]),
                  "preverb_handling": None}
        else:
            e1 = None
        # ---- E3
        e3a = e3a_stem(lex)
        e3b = None
        lexical = [p for p in pieces if p["role"] == "lexical"]
        n_surface = len(r2.get("surface_pieces") or [])
        if e1 in ("printed", "proposed") and n_surface > 1 and lexical:
            final = pieces[-1]
            if final["role"] == "lexical":
                e3b = e3b_final_root(lex, final["form"], simplex_by_form)
                if e3b is None and final["form_min"] != final["form"]:
                    e3b = e3b_final_root(lex, final["form_min"], simplex_by_form)
        e3 = None
        if e1 and e3a and e3a["status"] == "exact":
            if n_surface <= 1:
                e3 = "confirm"
            elif e3b and e3b["status"] == "confirm":
                e3 = "confirm"
        if e3b and e3b["status"] == "mismatch":
            e3 = "contradict"
        # ---- E5
        matches = []
        for mid in lex["member_ids"]:
            for m in seams_by_entry.get(mid, []):
                if m not in matches:
                    matches.append(m)
        r5 = e5_seams(lex, r2, matches) if e1 else None
        e5 = r5["status"] if r5 else None
        # ---- E4 / E6
        e4_detail = []
        e4 = bool(e1)
        if e1 == "printed":
            for p in pieces:
                if p["role"] == "lexical":
                    others = support.get(p["sense_id"], set()) - {lid} if p["sense_id"] else set()
                    owners = standalone_of.get(p["sense_id"], set()) - {lid} if p["sense_id"] else set()
                    ok = bool(p["sense_id"]) and p["sense_evidence"] in SENSE_EVIDENCED and (
                        len(others) >= MIN_SUPPORT or bool(owners))
                    basis = "meaning checked in this word" if ok else None
                    if p.get("stem_ref") and p.get("stem_ref_evidence") == "literal":
                        # the piece sits inside a compound stem that is its own dictionary entry,
                        # and the literal translation agrees with that entry's gloss
                        ok, basis = True, "inside the stem %s, whose gloss matches the literal" % p["stem_ref"]
                    elif p["sense_evidence"] == "inherited" and p["sense_id"]:
                        ok = len(others) >= MIN_SUPPORT or bool(owners)
                        basis = "meaning taken from the stem's own entry" if ok else None
                    e4_detail.append({"piece": p["form"], "sense_id": p["sense_id"], "basis": basis,
                                      "sense_evidence": p["sense_evidence"], "other_lexemes": len(others),
                                      "standalone_entries": sorted(owners)[:3], "ok": ok})
                    e4 = e4 and ok
                elif p["role"] == "grammatical":
                    n = label_stats.get(p["label"], {}).get(p["form"], 0)
                    known = n >= MIN_LABEL_COUNT or p["form"] in role_defaults
                    e4_detail.append({"piece": p["form"], "label": p["label"], "label_printed_elsewhere": n,
                                      "label_inferred": p["label_inferred"], "ok": known})
                    e4 = e4 and known
            if len(lexical) == 0 and len(pieces) > 0:
                e4 = e4 and True
        elif e1 == "proposed":
            e4 = proposals[lid]["all_pieces_match_gloss"]
            e4_detail.append({"note": "proposal: every lexical piece shares a content word with the gloss"
                              if e4 else "proposal: only some pieces share a content word with the gloss",
                              "ok": e4})
        elif e1 == "citation":
            e4 = citation[lid][0]["cited_in"] >= MIN_SUPPORT
            e4_detail.append({"piece": _targets(lex)[0], "sense_id": citation[lid][0]["sense_id"],
                              "cited_in": citation[lid][0]["cited_in"], "ok": e4})
        # ---- E7 (recorded only)
        e7 = None
        cog = [c for c in lex["cognates"] if c["language"] in ("SB", "Ar")]
        if cog and lexical:
            shared = [c for c in cog if any(len(skel(p["form"])) >= 3 and
                                            skel(p["form"])[:3] in skel(parks_clean(c["form"])) for p in lexical)]
            e7 = {"cognates": cog[:3], "shows_a_root": bool(shared)}
        tier, reasons = assign_tier(e1, r2["status"] if e1 else None, e3, e5, e4)
        # the same tier with E5 switched off, for scoring against the Blue Book gold set
        tier_no_e5, _ = assign_tier(e1, r2["status"] if e1 else None, e3, None, e4)
        flags = list(parsed["flags"])
        if r5:
            flags += r5["flags"]
        if e1 == "printed" and parsed["preverbs"] and sorted(parsed["preverbs"]) != sorted(lex["preverbs"]):
            flags.append("preverb_note_differs_from_headword")
        records.append({
            "lexeme_id": lid, "member_ids": lex["member_ids"], "headword": lex["headword"],
            "class": lex["class"], "verb_class": lex["verb_class"], "preverbs": lex["preverbs"],
            "page_number": lex["page_number"], "book_page": lex["book_page"], "pdf_file": lex["pdf_file"],
            "source": lex["source"], "gloss": lex["glosses"][0]["definition"] if lex["glosses"] else None,
            "raw_etymology": lex["raw_etymology"], "e1": e1, "e1_kind": parsed["kind"],
            "literal": parsed["literal"], "etymology_preverbs": parsed["preverbs"],
            "pieces": [{k: p.get(k) for k in ("form", "form_min", "word", "group", "dotted", "bound", "role",
                                               "label", "label_inferred", "gloss", "gloss_kind", "phrase",
                                               "sense_id", "sense_evidence", "stored_gloss", "stem_ref",
                                               "stem_ref_evidence", "inherited_from")} for p in pieces],
            "citation": citation.get(lid), "e2": r2, "e3": e3, "e3a": e3a, "e3b": e3b,
            "e4": e4 if e1 else None, "e4_detail": e4_detail, "e5": e5, "e5_detail": r5, "e7": e7,
            "tier": tier, "tier_without_e5": tier_no_e5, "tier_reasons": reasons, "flags": sorted(set(flags)),
        })
    return {"lexemes": lexemes, "records": records, "dup_decisions": dup_decisions,
            "label_stats": label_stats, "role_defaults": role_defaults, "senses": inv,
            "sense_by_id": sense_by_id, "support": support, "standalone_of": standalone_of,
            "seam_counts": seam_counts, "manual": manual, "by_alt": by_alt, "group_stats": group_stats}
