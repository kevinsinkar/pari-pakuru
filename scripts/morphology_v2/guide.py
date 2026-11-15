#!/usr/bin/env python3
"""Phase 6: the learner-facing guides, generated from tier A and B data only.

Nothing Pawnee is typed here.  Every Pawnee form in the output is looked up
from a record and written in *italics*; IPA is copied from Parks's
`phonetic_form` and written in [brackets]; the learner respelling is copied
from `simplified_pronunciation` and written in `code`.  check_forms.py verifies
all three against the sources and fails on anything it cannot resolve.
"""
import re
from collections import Counter, defaultdict

from analysis import SENSE_EVIDENCED
import unicodedata

from common import OUT, norm, write_text
from inventory import lexeme_keys, morpheme_key, needs_community_review
from ordering import WEIGHTS
from tiers import LEARNER_TIERS
import seams

LESSON_SIZE = 8
N_LESSONS = 15
LESSONS_PER_UNIT = 3
REVIEW_FREE_UNITS = 3          # no vocabulary flagged for community review in these units


# ---------------------------------------------------------------------------
# Formatting helpers (the only places a Pawnee form is written)
# ---------------------------------------------------------------------------

def it(form):
    """A Pawnee form exactly as stored in its source record (no respelling of any kind)."""
    return "*%s*" % unicodedata.normalize("NFC", form or "").strip().replace("*", "")


def affix_shape(form, kind):
    if kind in ("suffix",):
        return "*-%s*" % form
    if kind in ("prefix", "preverb"):
        return "*%s-*" % form
    return "*-%s-*" % form


def cell(text):
    return (text or "").replace("|", "/").replace("\n", " ").strip()


def printed_table(w, rows):
    """A table of the book, cell for cell as read from the page. The first printed row is the header row."""
    width = max(len(r) for r in rows)
    for i, row in enumerate(rows):
        w("| %s |" % " | ".join(cell(c) for c in list(row) + [""] * (width - len(row))))
        if i == 0:
            w("|%s" % ("---|" * width))
    w("")


def short_gloss(text, n=70):
    # display-only repair of letter-spaced OCR runs in English glosses ('o n  o n e ' s  b a c k');
    # the database text is left as it is and the cases are listed in proposed_data_fixes.json
    t = cell(re.sub(r"(?:[a-zA-Z'] ){3,}[a-zA-Z]", lambda m: m.group(0).replace(" ", ""),
                    re.sub(r"\s{2,}", " § ", text or ""))).replace(" § ", " ")
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


class Book:
    """Lookups shared by the three documents."""

    def __init__(self, bundle):
        res, inv, need, usable, order, curve, sens, stats = bundle
        self.res, self.inv, self.need, self.usable = res, inv, need, usable
        self.order, self.curve, self.sens, self.stats = order, curve, sens, stats
        self.lex = {l["lexeme_id"]: l for l in res["lexemes"]}
        self.rec = {r["lexeme_id"]: r for r in res["records"]}
        self.root = {r["id"]: r for r in inv["roots"]}
        self.affix = {a["id"]: a for a in inv["affixes"]}
        self.keys_of = {}
        for r in res["records"]:
            if r["tier"] in LEARNER_TIERS:
                ks, complete = lexeme_keys(r)
                self.keys_of[r["lexeme_id"]] = (ks, complete)
        self.body_roots = self._body_roots()

    def _body_roots(self):
        outp = set()
        for r in self.inv["roots"]:
            own = r["evidence"]["own_dictionary_entries"]
            tagged = any("body" in self.lex[l]["tags"] for l in own)
            if not tagged:
                for ex in r["examples"][:8]:
                    lx = self.lex[ex["lexeme_id"]]
                    if len(ex["pieces"]) == 2 and ex["pieces"][-1] == "uʔ" and "body" in lx["tags"]:
                        tagged = True
            if tagged and "noun" in r["class"] or tagged and "incorporated" in r["class"]:
                outp.add(r["id"])
        return outp

    # ---- describing things
    def name(self, key):
        """A morpheme as the learner sees it: shape and meaning."""
        if key in self.root:
            r = self.root[key]
            return "%s '%s'" % (it(r["form"]), r["meaning"])
        a = self.affix[key]
        return "%s %s" % (affix_shape(a["form"], a["kind"]), a["label"])

    def shape(self, key):
        if key in self.root:
            return it(self.root[key]["form"])
        a = self.affix[key]
        return affix_shape(a["form"], a["kind"])

    def meaning(self, key):
        if key in self.root:
            return self.root[key]["meaning"]
        a = self.affix[key]
        return "%s (%s)" % (a["label"], a["meaning"]) if a["meaning"] != a["label"] else a["label"]

    def source(self, lid):
        r = self.rec[lid]
        page = "p. %s" % r["book_page"] if r["book_page"] else "Blue Book only"
        return "`%s`, Parks %s" % (lid, page) if r["source"] != "blue_book" else "`%s`, %s" % (lid, page)

    def pieces(self, lid):
        r = self.rec[lid]
        if r["e1"] == "citation" or not r["pieces"]:
            return it(r["headword"].split(",")[0].strip())
        return " + ".join(it(p["form"]) for p in r["pieces"])

    def gloss_pieces(self, lid):
        """pieces with their meanings: *kaa* 'inside' + *at* 'go'."""
        r = self.rec[lid]
        if r["e1"] == "citation" or not r["pieces"]:
            return it(r["headword"].split(",")[0].strip())
        parts = []
        for p in r["pieces"]:
            k = morpheme_key(p)
            if p["role"] == "lexical":
                m = self.root[k]["meaning"] if k in self.root else "?"
                parts.append("%s '%s'" % (it(p["form"]), m))
            else:
                parts.append("%s %s" % (it(p["form"]), p["label"]))
        return " + ".join(parts)

    def bb(self, lid):
        forms = self.inv["bb_forms"].get(lid) or []
        if not forms:
            return ""
        f = forms[0]
        return "%s (L%s%s)" % (it(f["form"].strip(" .")), f["lesson"], ", p. %s" % f["page"] if f["page"] else "")

    def spelling_row(self, lid, with_pieces=True):
        """Blue Book | Parks | learner spelling | say it | IPA | meaning | pieces | source."""
        lx, r = self.lex[lid], self.rec[lid]
        cols = [self.bb(lid) or "—", it(r["headword"]),
                it(lx["normalized_form"]) if lx["normalized_form"] else "—",
                "`%s`" % lx["simplified_pronunciation"] if lx["simplified_pronunciation"] else "—",
                lx["phonetic_form"] or "not recorded", short_gloss(r["gloss"])]
        if with_pieces:
            cols.append(self.gloss_pieces(lid))
        cols.append(self.source(lid))
        return "| " + " | ".join(cell(c) for c in cols) + " |"

    SPELLING_HEAD = ("| Blue Book | Parks | Learner spelling | Say it | IPA (Parks) | Meaning | Built from | Source |\n"
                     "|---|---|---|---|---|---|---|---|")


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

def _keys(rec):
    return [morpheme_key(p) for p in rec["pieces"]]


def recipes(book):
    root = book.root

    def cls(k):
        return root[k]["class"] if k in root else ""

    def is_v(r):
        return (r["class"] or "").startswith("V")

    def is_n(r):
        return (r["class"] or "").startswith("N")

    def lexical(r):
        return [k for k, p in zip(_keys(r), r["pieces"]) if p["role"] == "lexical"]

    def gram(r):
        return [k for k, p in zip(_keys(r), r["pieces"]) if p["role"] != "lexical"]

    def sid(form, word):
        """The inventory id of the sense of `form` whose meaning has `word` (ids follow the labels)."""
        from analysis import gloss_stems
        want = gloss_stems(word)
        best = None
        for r in book.inv["roots"]:
            if r["form"] == form and (want & book.res["sense_by_id"][r["id"]]["stems"]):
                if best is None or r["type_frequency"]["A+B"] > best["type_frequency"]["A+B"]:
                    best = r
        return best["id"] if best else "%s#%s" % (form, word)

    MAKE, BECOME = sid("raʔuk", "make"), sid("aar", "become")
    R = []

    def add(rid, title, formula, applies, pred, needs_any=(), note=""):
        R.append({"id": rid, "title": title, "formula": formula, "applies": applies, "pred": pred,
                  "needs_any": list(needs_any), "note": note})

    add("nom", "A noun from a root: root + {uʔ=NOM}", "root + {uʔ=NOM}",
        "Nouns. The suffix adds no meaning of its own; it lets a bound root stand as a word "
        "(Parks, Grammatical Overview p. 31, Table 5).",
        lambda r: len(r["pieces"]) == 2 and _keys(r)[1] == "uʔ=NOM" and r["pieces"][0]["role"] == "lexical",
        ["uʔ=NOM"])
    add("compound", "Two roots make one noun", "root + root (+ {uʔ=NOM})",
        "Nouns. The second root is the head; the first narrows it.",
        lambda r: is_n(r) and len(lexical(r)) == 2 and set(gram(r)) <= {"uʔ=NOM"})
    add("locverb", "Where + what happens: a locative before a verb root", "locative + verb root",
        "Verbs. Parks's stem template puts the locative (slot 5) before the verb root (slot 7) "
        "(Grammatical Overview p. 44, Table 15).",
        lambda r: is_v(r) and len(r["pieces"]) == 2 and len(lexical(r)) == 2
        and cls(lexical(r)[0]) == "locative" and cls(lexical(r)[1]).startswith("verb root"))
    add("incorporation", "A body part inside the verb", "body-part root + verb stem",
        "Verbs. The noun comes first, in the noun slot of the stem (Grammatical Overview p. 43; p. 44, Table 15 slot 2).",
        lambda r: is_v(r) and len(lexical(r)) >= 2 and lexical(r)[0] in book.body_roots)
    add("wi", "Position words in {wi=LOC}", "locative + {wi=LOC}",
        "Locative stems and the verbs built on them (Grammatical Overview p. 44: locative verbs take {wi=LOC}).",
        lambda r: "wi=LOC" in _keys(r), ["wi=LOC"])
    add("portative", "Carrying: {ra=PORT} and {ri=PORT} before a motion root", "{ra=PORT} / {ri=PORT} + verb root",
        "Verbs. With 'go' and 'come' the result is 'take' and 'bring' (Grammatical Overview p. 44, Table 15 slot 4).",
        lambda r: is_v(r) and ({"ra=PORT", "ri=PORT"} & set(_keys(r))), ["ra=PORT", "ri=PORT"])
    add("causative", "Making it happen: the causatives",
        "stem + {%s} / {rik=CAUS} / {ik=CAUS} / {wuh=CAUS} / {k=TRANS}" % MAKE,
        "Verbs. The causative is the last element of the stem (Grammatical Overview p. 44, Table 15 slot 8).",
        lambda r: is_v(r) and len(r["pieces"]) >= 2 and _keys(r)[-1] in (
            MAKE, "rik=CAUS", "ik=CAUS", "wuh=CAUS", "k=TRANS"),
        [MAKE, "rik=CAUS", "ik=CAUS", "wuh=CAUS", "k=TRANS"])
    add("become", "Becoming: a stem + 'become'", "stem + {%s}" % BECOME,
        "Verbs built on a descriptive or noun stem.",
        lambda r: is_v(r) and len(r["pieces"]) >= 2 and _keys(r)[-1] == BECOME, [BECOME])
    add("pliter", "Many, or again and again: {raar=PL/ITER}", "{raar=PL/ITER} + stem",
        "On nouns inside a verb it marks plural; on verbs it marks repeated action "
        "(Grammatical Overview p. 44, Table 15 slot 1; p. 30, Table 4).",
        lambda r: "raar=PL/ITER" in _keys(r), ["raar=PL/ITER"])
    add("dist", "Here and there: the distributive {waa=DIST}", "{waa=DIST} with a stem",
        "Verbs. Parks lists the distributive form of a verb in braces after its class.",
        lambda r: "waa=DIST" in _keys(r), ["waa=DIST"])
    add("dim", "Small: {kis=DIM}", "root + {kis=DIM}",
        "Nouns (Grammatical Overview p. 31, Table 5).",
        lambda r: "kis=DIM" in _keys(r), ["kis=DIM"])
    add("locnoun", "Where: locative endings on nouns", "noun stem + {hiriʔ=LOC} / {kat=LOC} / {t=LOC} / {taku=LOC.ADV}",
        "Nouns and the adverbs made from them (Grammatical Overview p. 30, Table 4).",
        lambda r: {"hiriʔ=LOC", "kat=LOC", "t=LOC", "taku=LOC.ADV"} & set(_keys(r)),
        ["hiriʔ=LOC", "kat=LOC", "t=LOC", "taku=LOC.ADV"])
    add("preverb", "Stems in two parts: the preverbs", "{ut=PREV} / {uur=PREV} / {ir=PREV} … stem",
        "Verbs. The preverb is part of the stem but stands earlier in the word, among the prefixes, and has "
        "no meaning of its own (Grammatical Overview p. 31). Parks writes it in parentheses after the headword. "
        "The same three shapes also serve as benefactive, possessor and transitivising prefixes; this inventory "
        "does not separate those uses and labels them all PREV.",
        lambda r: is_v(r) and {"ut=PREV", "uur=PREV", "ir=PREV"} & set(_keys(r)),
        ["ut=PREV", "uur=PREV", "ir=PREV"])
    add("agentnoun", "The one that …: a verb turned into a noun", "{ra=ABS} + verb stem + {hus=IMPF}",
        "Nouns naming a thing by what it does.",
        lambda r: is_n(r) and "ra=ABS" in _keys(r) and "hus=IMPF" in _keys(r), ["ra=ABS", "hus=IMPF"])
    return R


def recipe_members(book, rc, tiers=LEARNER_TIERS):
    outp = []
    for r in book.res["records"]:
        if r["e1"] != "printed" or r["tier"] not in tiers:
            continue
        if None in [k for k, p in zip(_keys(r), r["pieces"]) if p["role"] != "lexical"]:
            continue
        try:
            if rc["pred"](r):
                outp.append(r)
        except Exception:
            continue
    return outp


def expand_formula(book, formula):
    def rep(m):
        k = m.group(1)
        rec = book.root.get(k) or book.affix.get(k)
        if rec and rec["tier"] in LEARNER_TIERS:
            return book.shape(k)
        return "(a piece below tier B, not shown)"
    return re.sub(r"\{([^}]+)\}", rep, formula)


# ---------------------------------------------------------------------------
# Seam statistics
# ---------------------------------------------------------------------------

def _is_c(ch):
    return ch not in "aiu"


ENVIRONMENTS = {
    "r>h/_C": lambda ps, wl: any(a.endswith("r") and _is_c(b[0]) and b[0] not in "rh" and not (a == "raar" and b[0] == "t")
                                 for a, b in zip(ps, ps[1:])),
    "R21": lambda ps, wl: any(a[-1] in "pkcs" and b[0] == "r" for a, b in zip(ps, ps[1:])),
    "w>p/C_": lambda ps, wl: any(a[-1] in "ptkcs" and b[0] == "w" for a, b in zip(ps, ps[1:])),
    "k>0/_p": lambda ps, wl: any(a[-1] == "k" and b[0] == "w" for a, b in zip(ps, ps[1:])),
    "R16": lambda ps, wl: any(_is_c(a[-1]) and a[-1] != "r" and b[0] == "h" and not (a[-1] == "k" and b == "his")
                              for a, b in zip(ps, ps[1:])),
    "R14-15": lambda ps, wl: any(a[-1] == "r" and b[0] == "h" for a, b in zip(ps, ps[1:])),
    "R20": lambda ps, wl: any(a[-1] == b[0] and a[-1] in "rk" for a, b in zip(ps, ps[1:])),
    "V+V ʔ": lambda ps, wl: any(not _is_c(a[-1]) and not _is_c(b[0]) for a, b in zip(ps, ps[1:])),
    "R9": lambda ps, wl: wl and ps[-1].endswith("s") and len(ps) > 1,
    "k>t/_#": lambda ps, wl: wl and ps[-1].endswith("k"),
    "V>Vʔ/_#": lambda ps, wl: wl and (not _is_c(ps[-1][-1]) or ps[-1].endswith("r")),
    "#V>0/_C": lambda ps, wl: wl and len(ps[0]) > 2 and ps[0][0] in "ia" and _is_c(ps[0][1]),
    "#w>p": lambda ps, wl: wl and ps[0].startswith("w"),
    "R23": lambda ps, wl: wl and ps[-1].endswith("r"),
}


def seam_statistics(book):
    """For each rule: in how many exactly reproduced tier A/B words its environment occurs, and how often it applies."""
    from analysis import is_word_like
    stats = {}
    for rid in seams.RULES:
        stats[rid] = {"applied": 0, "environment": 0, "examples": []}
    for r in book.res["records"]:
        if r["e1"] != "printed" or r["tier"] not in LEARNER_TIERS or r["e2"]["status"] != "exact":
            continue
        ps = [p for p in r["e2"]["surface_pieces"] if p]
        if len(ps) < 1:
            continue
        wl = is_word_like(book.lex[r["lexeme_id"]])
        used = set(r["e2"]["rules"])
        for rid in seams.RULES:
            env = ENVIRONMENTS.get(rid)
            in_env = bool(env and len(ps) >= 1 and env(ps, wl))
            if rid in used:
                stats[rid]["applied"] += 1
                if len(stats[rid]["examples"]) < 3 and len(ps) <= 3 and not r["needs_community_review"]:
                    stats[rid]["examples"].append(r["lexeme_id"])
                in_env = True
            if in_env:
                stats[rid]["environment"] += 1
    return stats


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def construction_guide(book):
    S = book.stats
    L = []
    w = L.append
    w("# How Skiri Pawnee words are built")
    w("")
    w("Generated by `scripts/morphology_v2/run.py --guide`. Do not edit by hand: every Pawnee form "
      "below is looked up from a source record, and `scripts/morphology_v2/check_forms.py` verifies that.")
    w("")
    w("## How to read this guide")
    w("")
    w("- **Sources.** Parks, A Dictionary of Skiri Pawnee (cited by entry id and printed page), his "
      "Grammatical Overview (GO) and appendices, and the Blue Book, Pari Pakuru (BB, cited by lesson and page).")
    w("- **What is shown.** Only analyses in tier A or B. Tier A: Parks prints the analysis, the pieces reproduce "
      "the headword exactly by named rules, and an independent source (the word's paradigm, or a Blue Book "
      "seam) confirms it. Tier B: Parks prints it, it reproduces exactly, and every piece recurs with the same "
      "meaning in other words. `METHOD.md` gives the rules in full.")
    w("- **Spelling.** Pawnee forms are in italics, each in the spelling of the source it is quoted from. "
      "The \"Say it\" column is the project's learner respelling. IPA is Parks's own phonetic form, shown only "
      "where he prints one for that exact word; it is never generated.")
    w("- **Pieces.** A hyphen after a piece marks a prefix or preverb; a hyphen before it marks a suffix. "
      "Upper-case labels (NOM, DIM, PL …) are Parks's.")
    w("")
    n_ab = S["lexeme_tiers"].get("A", 0) + S["lexeme_tiers"].get("B", 0)
    w("**Scale.** The dictionary has %d words after duplicate rows are resolved. Parks prints an analysis for "
      "%d of them. %d analyses reach tier A and %d tier B; this guide draws on those %d words." % (
          S["lexemes"], S["e1"].get("printed", 0), S["lexeme_tiers"].get("A", 0), S["lexeme_tiers"].get("B", 0), n_ab))
    w("")

    # ---- seams
    w("## 1. What happens where two pieces meet")
    w("")
    w("These are all the rules the pipeline needed to turn Parks's pieces into his headwords. "
      "\"Words\" counts tier A/B words whose exact reproduction uses the rule. Where a rule is marked "
      "optional, the second number shows how often it applies when it could: the outcome is not predictable "
      "from the sounds alone, so learn those words as they come.")
    w("")
    w("| Rule | Source | Words using it | Applies in | Examples (pieces → word) |")
    w("|---|---|---|---|---|")
    st = seam_statistics(book)
    for rid, n in sorted(((rid, st[rid]["applied"]) for rid in seams.RULES), key=lambda t: (-t[1], t[0])):
        if n == 0:
            continue
        info = seams.RULES[rid]
        exs = []
        for lid in st[rid]["examples"]:
            r = book.rec[lid]
            exs.append("%s → %s" % (" + ".join(it(p) for p in r["e2"]["surface_pieces"]), it(r["e2"]["target"])))
        env = st[rid]["environment"]
        share = "%d of %d (%d%%)" % (n, env, round(100 * n / env)) if env and rid in ENVIRONMENTS else "—"
        w("| %s%s | %s | %d | %s | %s |" % (info["name"], " (optional)" if info["optional"] else "",
                                         cell(info["source"]), n, share, "; ".join(exs)))
    w("")
    w("Not covered by any rule: changes of vowel length elsewhere in a word. %d printed analyses match their "
      "headword only when vowel length, ʔ and h are ignored. Those words are tier B only if a paradigm or the "
      "Blue Book confirms them, and are otherwise left out of this guide; they are listed in `review_queue.md`."
      % S["e2"].get("partial", 0))
    w("")

    # ---- recipes
    w("## 2. Construction recipes")
    w("")
    for rc in recipes(book):
        mem = recipe_members(book, rc)
        if len(mem) < 3:
            continue
        allm = recipe_members(book, rc, tiers=("A", "B", "C"))
        n_a = sum(1 for r in mem if r["tier"] == "A")
        tier = "A" if n_a >= 3 and len(mem) >= 10 else "B"
        w("### %s" % expand_formula(book, rc["title"]))
        w("")
        w("**Formula.** %s" % expand_formula(book, rc["formula"]))
        w("")
        w("**Where it applies.** %s" % expand_formula(book, rc["applies"]))
        w("")
        w("**Tier %s.** %d tier A/B words follow this recipe (%d tier A, %d tier B); %d more match the pattern but "
          "are tier C and are not shown." % (tier, len(mem), n_a, len(mem) - n_a, len(allm) - len(mem)))
        w("")
        rule_use = Counter(x for r in mem if r["e2"]["status"] == "exact" for x in set(r["e2"]["rules"]))
        plain = sum(1 for r in mem if r["e2"]["status"] == "exact" and not r["e2"]["rules"])
        if rule_use:
            w("**At the seam.** %d of these words join with no change. In the rest: %s." % (
                plain, "; ".join("%s (%d)" % (seams.RULES[k]["name"], n) if k in seams.RULES else "%s (%d)" % (k, n)
                                 for k, n in sorted(rule_use.items(), key=lambda kv: (-kv[1], kv[0]))[:5])))
        else:
            w("**At the seam.** All of these words join with no change.")
        w("")
        w("**Attested examples.**")
        w("")
        w(Book.SPELLING_HEAD)
        shown = 0
        order = sorted(mem, key=lambda r: (r["needs_community_review"], r["lexeme_id"] not in book.inv["bb_first"],
                                           r["tier"] != "A", len(r["pieces"]), r["lexeme_id"]))
        for r in order:
            if r["needs_community_review"]:
                continue
            w(book.spelling_row(r["lexeme_id"]))
            shown += 1
            if shown >= 5:
                break
        w("")
        odd = [r for r in allm if r["tier"] == "C" and r["e2"]["status"] != "exact"
               and not r["needs_community_review"]][:3]
        if odd:
            w("**Exceptions found.** These words match the pattern, but their pieces do not reproduce the headword "
              "exactly by the rules above, so they are not taught here: %s." % "; ".join(
                  "%s from %s (%s)" % (it(r["headword"]), " + ".join(it(p["form"]) for p in r["pieces"]),
                                       book.source(r["lexeme_id"])) for r in odd))
            w("")
        conflicts = [r for r in mem if ("bb_finer_than_parks" in r["flags"] or r["e5"] == "contradict")
                     and not r["needs_community_review"]]
        if conflicts:
            w("**Parks and the Blue Book.** %s" % "; ".join(
                "%s: the Blue Book writes %s, with a seam Parks's analysis does not have" % (
                    it(r["headword"]), it(r["e5_detail"]["attestations"][0]["bb"])) for r in conflicts[:3]))
            w("")

    # ---- inflection: read off the paradigms
    w("## 3. What the five dictionary forms show")
    w("")
    w("Parks gives up to five inflected forms for a verb: (1) I …ed, (2) he/she …ed, (3) he/she is …ing, "
      "(4) the one who …ed / where he …ed, (5) he/she is going to …. They show how the stem takes the "
      "mode-and-person prefixes and the aspect endings. The forms below are his, copied from the entries.")
    w("")
    w("| Verb | Meaning | 1 | 2 | 3 | 4 | 5 | Source |")
    w("|---|---|---|---|---|---|---|---|")
    shown = 0
    for r in book.inv["roots"]:
        if shown >= 8:
            break
        if not r["class"].startswith("verb root") or r["tier"] != "A":
            continue
        for lid in r["evidence"]["own_dictionary_entries"]:
            lx = book.lex[lid]
            if len(lx["forms"]) == 5 and not needs_community_review(lx):
                w("| %s | %s | %s | %s |" % (it(lx["headword"]), short_gloss(lx["glosses"][0]["definition"], 40),
                                            " | ".join(it(lx["forms"][str(n)]) for n in range(1, 6)), book.source(lid)))
                shown += 1
                break
    w("")
    w("**The subordinate ending depends on the verb class.** Counted over every verb that has both form 2 and "
      "form 4: the last sound of form 4, by the class Parks prints in parentheses.")
    w("")
    w("| Class | Verbs | Form 4 most often ends in | Share | Example: headword, form 2, form 4 | Source |")
    w("|---|---|---|---|---|---|")
    by_class = defaultdict(list)
    for lx in book.res["lexemes"]:
        if (lx["class"] or "").startswith("V") and "2" in lx["forms"] and "4" in lx["forms"]:
            vc = (lx["verb_class"] or ("descriptive" if lx["class"].startswith("VD") else
                                       "locative" if lx["class"].startswith("VL") else "unmarked")).split(",")[0].strip()
            by_class[vc].append(lx)
    for vc in sorted(by_class, key=lambda k: (-len(by_class[k]), k)):
        items = by_class[vc]
        if len(items) < 15:
            continue
        ends = Counter(re.sub(r"[^a-zʔ]", "", norm(lx["forms"]["4"]).split(";")[0].split(",")[0].lower())[-1:] for lx in items)
        top, n = ends.most_common(1)[0]
        ex = next((lx for lx in sorted(items, key=lambda l: (len(l["headword"]), l["lexeme_id"]))
                   if norm(lx["forms"]["4"]).lower().rstrip().endswith(top) and not needs_community_review(lx)
                   and book.rec[lx["lexeme_id"]]["tier"] in LEARNER_TIERS
                   and ";" not in lx["forms"]["4"] and len(lx["headword"]) > 2), None)
        if ex is None:
            continue
        w("| %s | %d | the sound written %s | %d%% | %s, %s, %s | %s |" % (
            vc, len(items), '"%s"' % top, round(100 * n / len(items)), it(ex["headword"]), it(ex["forms"]["2"]),
            it(ex["forms"]["4"]), book.source(ex["lexeme_id"])))
    w("")
    w("**A compound inflects like its last root.** Of %d compound verbs that share an inflection class with the "
      "dictionary entry of their final root, %d (%d%%) end every form exactly as that root does on its own. "
      "Learn a root's five forms once and they carry over to the words built on it." % (
          S["e3b"].get("confirm", 0) + S["e3b"].get("near", 0) + S["e3b"].get("mismatch", 0), S["e3b"].get("confirm", 0),
          round(100 * S["e3b"].get("confirm", 0) / max(1, S["e3b"].get("confirm", 0) + S["e3b"].get("near", 0)
                                                        + S["e3b"].get("mismatch", 0)))))
    w("")
    w("### The prefixes and endings Parks tabulates")
    w("")
    w("These are Parks's own tables of the verb (Grammatical Overview, Tables 6 to 17), row by row as printed. "
      "They are taken from `extracted_data/grammatical_overview_tables.json`: each table was read from the page "
      "twice, by readers who did not see each other's reading. Where the two wrote the same text but divided "
      "the rows differently, one division is shown and the other is in the file. Where the readings differ, "
      "both are shown and neither is chosen. Nothing in these tables is a segmentation made here, and no piece "
      "is put into a position of the verb that Parks does not put it in.")
    w("")
    for t in book.inv["parks_tables"]:
        w("**%s** (p. %s; %s)" % (cell(t["title"]), ", ".join(str(p) for p in t["book_pages"]), t["status"]))
        w("")
        if "rows" in t:
            printed_table(w, t["rows"])
        else:
            w("First reading:")
            w("")
            printed_table(w, t["rows_first_reading"])
            w("Second reading:")
            w("")
            printed_table(w, t["rows_second_reading"])
    w("### The pieces Parks labels in his worked examples")
    w("")
    w("Counted from his worked examples in the same chapter; examples marked doubtful in the project's copy are "
      "left out. The piece and the label are his, as printed in the analysis line of the example. The same "
      "letters under two labels are two rows: the same spelling is not the same morpheme.")
    w("")
    w("| Piece | Label | Worked examples | One of them |")
    w("|---|---|---|---|")
    for a in book.inv["inflection"]:
        ex = a["example"]
        w("| %s | %s | %d | %s |" % (it(a["form"]), cell(a["label"]), a["worked_examples_in_grammatical_overview"],
                                     "%s '%s' (GO p. %s)" % (it(ex["form"]), cell(ex["translation"]), ex["go_page"])
                                     if ex else "—"))
    w("")
    return "\n".join(L)


def lesson_plan(book):
    """The first N_LESSONS lessons: which morphemes, which words, which recipes."""
    usable = book.usable
    order = book.order
    lessons, taught, shown = [], set(), set()
    rcs = recipes(book)
    recipe_done = set()
    members = {rc["id"]: {r["lexeme_id"] for r in recipe_members(book, rc)} for rc in rcs}
    for n in range(N_LESSONS):
        new = order[n * LESSON_SIZE:(n + 1) * LESSON_SIZE]
        if not new:
            break
        taught |= set(new)
        unit = n // LESSONS_PER_UNIT + 1
        dec = [l for l, ks in usable.items() if ks <= taught and l not in shown]
        allow_review = unit > REVIEW_FREE_UNITS
        dec = [l for l in dec if not book.rec[l]["needs_community_review"]]
        fresh = [l for l in dec if usable[l] & set(new)]
        older = [l for l in dec if not (usable[l] & set(new))]

        def rank(l):
            r = book.rec[l]
            return (l not in book.inv["bb_first"], r["tier"] != "A", len(r["pieces"]) > 3,
                    r["e1"] == "citation", len(r["pieces"]), l)
        pool, seen_hw = [], set()
        for l in sorted(fresh, key=rank) + sorted(older, key=rank):
            hk = re.sub(r"[^a-zʔ]", "", book.rec[l]["headword"].split(",")[0].lower())
            if hk not in seen_hw:           # one entry per spelling in a lesson
                seen_hw.add(hk)
                pool.append(l)
        words, decode, build = pool[:12], [], []
        rest = [l for l in pool[12:]]
        decode = [l for l in rest if len(book.rec[l]["pieces"]) >= 2][:4]
        rest = [l for l in rest if l not in decode]
        build = [l for l in rest if len(book.rec[l]["pieces"]) >= 2 and book.rec[l]["e2"]["status"] == "exact"][:3]
        shown |= set(words) | set(decode) | set(build)
        intro = []
        for rc in rcs:
            if rc["id"] in recipe_done or len(intro) >= 2:
                continue
            if rc["needs_any"] and not (set(rc["needs_any"]) & taught):
                continue
            ready = [l for l in members[rc["id"]] if l in usable and usable[l] <= taught
                     and not book.rec[l]["needs_community_review"]]
            if len(ready) >= 3:
                intro.append((rc, sorted(ready, key=rank)[:3]))
                recipe_done.add(rc["id"])
        step = min(len(book.curve), (n + 1) * LESSON_SIZE)
        lessons.append({"n": n + 1, "unit": unit, "new": new, "words": words, "decode": decode, "build": build,
                        "recipes": intro, "coverage": book.curve[step - 1], "allow_review": allow_review})
    return lessons


def learning_path(book):
    S, C = book.stats, book.curve
    L = []
    w = L.append
    lessons = lesson_plan(book)
    w("# Learning path: the building blocks of Skiri Pawnee, most useful first")
    w("")
    w("Generated by `scripts/morphology_v2/run.py --guide`. Every Pawnee form is looked up from a source "
      "record (see `construction_guide.md` for how to read sources, tiers and spellings).")
    w("")
    w("## How the order was worked out")
    w("")
    w("1. **What counts.** Only morphemes of tier A or B, and only words whose analysis is tier A or B and whose "
      "every piece has a meaning that was checked in that word. That leaves %d teachable building blocks and "
      "%d words that can be taken apart completely." % (len(book.order), len(book.usable)))
    w("2. **Prerequisites.** A word is shown only after every one of its pieces has been taught, and a recipe "
      "only after the pieces it needs.")
    w("3. **Which block next.** Each block is credited, for every word it helps build, with that word's weight "
      "divided by the number of its pieces still untaught. A word the Blue Book teaches weighs %.1f, any other "
      "word 1.0. The credit is multiplied by 1 + %.1f × the share of the block's words that join with no sound "
      "change. The block with the highest credit is taught next." % (1 + WEIGHTS["blue_book"], WEIGHTS["transparency"]))
    w("4. **Sensitivity.** Each weight was shifted by ±25%%, alone and together. The first 50 blocks keep a rank "
      "correlation of %.3f or better with this order, and at least %d%% of them stay in the first 50. The "
      "order does not hinge on the weights." % (
          min(r["spearman_top_50"] for r in book.sens), round(100 * min(r["overlap_top_50"] for r in book.sens))))
    w("5. **Community review.** Words whose meaning is ceremonial or sacred are not used as teaching words in "
      "this path. They are listed in `review_queue.md` for the Pawnee community to decide on.")
    w("")
    w("## What the order buys")
    w("")
    w("\"Taken apart completely\" means every piece of the word has been taught. \"With a known piece\" means at "
      "least one has. The dictionary has %d words; %d Blue Book words are reliably linked to it; "
      "it has %d example sentences." % (S["lexemes"], len(book.inv["bb_first"]), book.inv["total_examples"]))
    w("")
    w("| Blocks taught | Words taken apart completely | Share of dictionary | Words with a known piece | "
      "Blue Book words taken apart | Example sentences covered |")
    w("|---|---|---|---|---|---|")
    for m in (8, 24, 48, 72, 96, 120, 200, 300, 400, len(C)):
        if m <= len(C):
            c = C[m - 1]
            w("| %d | %d | %.1f%% | %d | %d (%.1f%%) | %.1f%% |" % (
                m, c["words_decodable"], 100 * c["share_of_dictionary"], c["words_with_a_known_piece"],
                c["blue_book_words_decodable"], 100 * c["share_of_blue_book_words"],
                100 * c["share_of_example_sentences"]))
    w("")
    w("The lessons below cover the first %d blocks. The rest of the order is in the table at the end." % (
        len(lessons) * LESSON_SIZE))
    w("")
    answers = []
    for ls in lessons:
        if (ls["n"] - 1) % LESSONS_PER_UNIT == 0:
            w("# Unit %d" % ls["unit"])
            w("")
        w("## Lesson %d" % ls["n"])
        w("")
        w("### New building blocks")
        w("")
        w("| Piece | Meaning | Kind | Tier | Tier A/B words it builds | First Blue Book lesson |")
        w("|---|---|---|---|---|---|")
        for k in ls["new"]:
            rec = book.root.get(k) or book.affix[k]
            kind = rec.get("class") or rec.get("kind")
            w("| %s | %s | %s | %s | %d | %s |" % (book.shape(k), cell(book.meaning(k)), cell(kind), rec["tier"],
                                                 rec["type_frequency"]["A+B"],
                                                 rec["blue_book"]["first_lesson"] or "—"))
        w("")
        if ls["recipes"]:
            w("### Recipes you can now use")
            w("")
            for rc, exs in ls["recipes"]:
                w("- **%s.** %s. For example: %s. Full details in `construction_guide.md`." % (
                    expand_formula(book, rc["title"]), expand_formula(book, rc["formula"]),
                    "; ".join("%s = %s" % (it(book.rec[l]["headword"]), book.gloss_pieces(l)) for l in exs[:2])))
            w("")
        if ls["words"]:
            w("### Words you can now take apart")
            w("")
            w(Book.SPELLING_HEAD)
            for l in ls["words"]:
                w(book.spelling_row(l))
            w("")
        if ls["decode"]:
            w("### Practice: take these apart")
            w("")
            w("Each is a real dictionary word built only from pieces you know. Find the pieces and work out the "
              "meaning, then check the answers at the end of this document.")
            w("")
            for i, l in enumerate(ls["decode"], 1):
                w("%d. %s" % (i, it(book.rec[l]["headword"])))
                answers.append((ls["n"], "take apart", i, l))
            w("")
        if ls["build"]:
            w("### Practice: build these")
            w("")
            w("Put the pieces together, applying the seam rules, and check your result against the attested word "
              "in the answers. Every target is a real dictionary word.")
            w("")
            for i, l in enumerate(ls["build"], 1):
                w("%d. %s — meaning: %s" % (i, book.gloss_pieces(l), short_gloss(book.rec[l]["gloss"], 60)))
                answers.append((ls["n"], "build", i, l))
            w("")
        c = ls["coverage"]
        w("**After this lesson:** %d blocks taught; %d dictionary words can be taken apart completely (%.1f%%), "
          "%d contain a piece you know, and %d of the %d linked Blue Book words are covered." % (
              c["step"], c["words_decodable"], 100 * c["share_of_dictionary"], c["words_with_a_known_piece"],
              c["blue_book_words_decodable"], len(book.inv["bb_first"])))
        w("")
    w("# Answers")
    w("")
    w("| Lesson | Exercise | Word | Pieces | Meaning | Seam rules | Source |")
    w("|---|---|---|---|---|---|---|")
    for n, kind, i, l in answers:
        r = book.rec[l]
        rules = "; ".join(seams.RULES[x]["name"] for x in r["e2"]["rules"] if x in seams.RULES) or "none"
        w("| %d | %s %d | %s | %s | %s | %s | %s |" % (n, kind, i, it(r["headword"]), book.gloss_pieces(l),
                                                     short_gloss(r["gloss"], 60), rules, book.source(l)))
    w("")
    w("# The rest of the order")
    w("")
    w("Blocks %d to %d, in the order the method gives. \"Words\" is the number of tier A/B words the block builds."
      % (len(lessons) * LESSON_SIZE + 1, len(book.order)))
    w("")
    w("| # | Piece | Meaning | Words | # | Piece | Meaning | Words |")
    w("|---|---|---|---|---|---|---|---|")
    rest = book.order[len(lessons) * LESSON_SIZE:]
    half = (len(rest) + 1) // 2
    base = len(lessons) * LESSON_SIZE

    def col(i):
        if i >= len(rest):
            return "| | | | "
        k = rest[i]
        rec = book.root.get(k) or book.affix[k]
        return "| %d | %s | %s | %d " % (base + i + 1, book.shape(k), cell(book.meaning(k))[:40], rec["type_frequency"]["A+B"])
    for i in range(half):
        w(col(i) + col(i + half) + "|")
    w("")
    return "\n".join(L), lessons


def review_queue(book):
    res, inv, S = book.res, book.inv, book.stats
    L = []
    w = L.append
    dec = inv["decisions"]
    w("# Review queue: what a speaker or linguist is needed for")
    w("")
    w("Generated by `scripts/morphology_v2/run.py --guide`. Nothing here is taught as settled. Each group says "
      "what question would settle its items. Full records are in `decisions.json` and `evidence.jsonl`.")
    w("")
    # 1 variants
    var = [d for d in dec if d["type"] == "variant_candidate"]
    w("## 1. Possible variants of one morpheme (%d pairs, none merged)" % len(var))
    w("")
    w("Parks cites these shapes with the same or overlapping meaning, and they differ only in vowel length, ʔ or "
      "h. No rule in Parks or the Blue Book derives one from the other, so they are counted separately.")
    w("")
    w("**Question for each pair:** are these one morpheme, and if so, what decides which shape appears?")
    w("")
    w("| Shape A | Words | Shape B | Words | Shared meaning | Combined |")
    w("|---|---|---|---|---|---|")
    for d in sorted(var, key=lambda d: -d["words_AB"]["combined"])[:60]:
        a, b = d["forms"]
        w("| %s | %d | %s | %d | %s | %d |" % (it(a), d["words_AB"][a], it(b), d["words_AB"][b],
                                            cell(", ".join(d["shared_meaning_words"])), d["words_AB"]["combined"]))
    w("")
    # 2 BB vs Parks
    conf = [r for r in res["records"] if r["e5"] == "contradict" or "bb_finer_than_parks" in r["flags"]]
    w("## 2. Blue Book and Parks divide a word differently (%d words)" % len(conf))
    w("")
    w("**Question:** does the Blue Book's seam mark a real boundary that Parks's analysis leaves out?")
    w("")
    w("| Word | Parks's pieces | Blue Book writes | Blue Book lesson | Source |")
    w("|---|---|---|---|---|")
    for r in sorted(conf, key=lambda r: r["lexeme_id"]):
        att = r["e5_detail"]["attestations"][0]
        w("| %s | %s | %s | L%s%s | %s |" % (it(r["headword"]), book.pieces(r["lexeme_id"]), it(att["bb"]),
                                          att["lesson"], ", p. %s" % att["page"] if att["page"] else "",
                                          book.source(r["lexeme_id"])))
    w("")
    # 3 paradigm disagreements
    mm = [r for r in res["records"] if (r["e3b"] or {}).get("status") in ("mismatch", "near")]
    w("## 3. A compound that does not inflect like its last root (%d words)" % len(mm))
    w("")
    w("Parks's etymology names a final root, but one of the word's paradigm forms ends differently from that "
      "root's own form. \"mismatch\" is an outright difference in an aspect ending; \"near\" is a one-letter one.")
    w("")
    w("**Question:** is the printed form right, and if so, is the last piece really that root?")
    w("")
    w("| Word | Parks's pieces | Kind | Form compared | The word has | The root's own form | Source |")
    w("|---|---|---|---|---|---|---|")
    for r in sorted(mm, key=lambda r: (r["e3b"]["status"] != "mismatch", r["lexeme_id"])):
        lx, sx = book.lex[r["lexeme_id"]], book.lex[r["e3b"]["simplex"]]
        bad = [n for n, v in r["e3b"]["verdicts"].items() if v != "yes"]
        n = bad[0] if bad else r["e3b"]["compared"][0]
        w("| %s | %s | %s | %s | %s | %s | %s |" % (it(r["headword"]), book.pieces(r["lexeme_id"]), r["e3b"]["status"],
                                                  n, it(lx["forms"][n]), it(sx["forms"][n]), book.source(r["lexeme_id"])))
    w("")
    # 4 length-only partials
    part = [r for r in res["records"] if r["e1"] == "printed" and r["e2"]["status"] == "partial"]
    w("## 4. Analyses that match the headword only if vowel length, ʔ or h is ignored (%d words)" % len(part))
    w("")
    w("**Question:** is the difference a real sound change (and what conditions it), a variant spelling of the "
      "piece, or an error in the print or the extraction? The first 40 are shown; all are in `evidence.jsonl` "
      "with `e2.status = partial`.")
    w("")
    w("| Word | Parks's pieces | Source |")
    w("|---|---|---|")
    for r in sorted(part, key=lambda r: r["lexeme_id"])[:40]:
        w("| %s | %s | %s |" % (it(r["headword"]), book.pieces(r["lexeme_id"]), book.source(r["lexeme_id"])))
    w("")
    # 5 homonyms
    hom = [d for d in dec if d["type"] == "homonym_split"]
    w("## 5. One shape, several meanings (%d shapes kept apart)" % len(hom))
    w("")
    w("Parks's glosses for these shapes fall into groups that share no content word, so each group is treated "
      "as a separate morpheme. Some will be true homonyms and some one morpheme with a wide meaning.")
    w("")
    w("**Question for each shape:** are these different morphemes, or one?")
    w("")
    w("| Shape | Meanings kept apart (tier A/B words) |")
    w("|---|---|")
    for d in sorted(hom, key=lambda d: -sum(s["words_AB"] for s in d["senses"]))[:60]:
        w("| %s | %s |" % (it(d["form"]), cell("; ".join("%s (%d)" % (s["meaning"], s["words_AB"]) for s in d["senses"]))))
    w("")
    # 6 unknown pieces
    unk = Counter()
    for r in res["records"]:
        for p in r["pieces"]:
            if p["role"] == "lexical" and p.get("sense_evidence") in ("meaning_unknown_to_parks", "no_sense_known"):
                unk[p["form"]] += 1
    w("## 6. Pieces with no known meaning (%d shapes)" % len(unk))
    w("")
    w("Parks glosses these pieces with their own shape, or gives them no gloss anywhere.")
    w("")
    w("**Question:** what does the piece mean?")
    w("")
    w(", ".join("%s (%d)" % (it(f), n) for f, n in sorted(unk.items(), key=lambda kv: (-kv[1], kv[0]))[:80]))
    w("")
    # 7 not in Parks
    prop = [r for r in res["records"] if r["e1"] == "proposed"]
    none = sum(1 for r in res["records"] if r["e1"] is None)
    w("## 7. Analyses not in Parks (%d proposed)" % len(prop))
    w("")
    w("%d words have no printed analysis and are not cited by Parks as a piece of another word. A segmentation "
      "was proposed only where one or two well-established pieces reproduce the headword exactly and the gloss "
      "agrees. Proposals are hypotheses and are never taught." % (none + len(prop)))
    w("")
    for r in prop:
        w("- %s '%s': proposed %s (tier %s; %s)" % (it(r["headword"]), short_gloss(r["gloss"], 50),
                                                  book.pieces(r["lexeme_id"]), r["tier"], book.source(r["lexeme_id"])))
    w("")
    # 8 community review
    rev = [r for r in res["records"] if r["needs_community_review"]]
    w("## 8. Vocabulary for community review (%d words)" % len(rev))
    w("")
    w("These words were flagged because their gloss or semantic tag refers to ceremony, sacred objects, doctors' "
      "societies and similar matters. They stay in the analysis but are not used as teaching words. Whether and "
      "how they are published is for the Pawnee community to decide. The flag is a keyword match and will have "
      "both false alarms and misses.")
    w("")
    w("| Word | Meaning | Tier | Source |")
    w("|---|---|---|---|")
    for r in sorted(rev, key=lambda r: r["lexeme_id"]):
        w("| %s | %s | %s | %s |" % (it(r["headword"]), short_gloss(r["gloss"], 60), r["tier"] or "—",
                                    book.source(r["lexeme_id"])))
    w("")
    return "\n".join(L)


def write_guides(conn, bundle):
    book = Book(bundle)
    write_text(OUT / "construction_guide.md", construction_guide(book))
    text, lessons = learning_path(book)
    write_text(OUT / "learning_path.md", text)
    write_text(OUT / "review_queue.md", review_queue(book))
    return book, lessons
