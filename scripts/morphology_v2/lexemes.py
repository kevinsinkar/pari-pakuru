#!/usr/bin/env python3
"""Load dictionary rows and resolve duplicate rows into lexemes.

The database has 4,343 rows but some lexemes appear twice (the page-2 / page-71
parser duplicates, split entries).  Counting rows would inflate every frequency,
so rows are grouped into lexemes here.  Rows that share a headword are NOT
merged just for that: they are merged only when class, verb class, preverb and
paradigm (or, without a paradigm, etymology and gloss) show they are the same
record.  Every decision is returned as data.
"""
import json
import re
from collections import defaultdict

from bluebook import content_stems
from common import (headword_alternates, load_page_index, norm, pdf_file_for, strip_accents)

PREVERB_NOTE = re.compile(r"\(\s*([a-z]+(?:\s*\.\s*\.\s*\.\s*[a-z]+)*)\s*\.\s*\.\s*\.\s*\)")


def parse_preverbs(stem_preverb, headword=""):
    pvs = []
    for src in (stem_preverb or "", headword or ""):
        for mt in PREVERB_NOTE.finditer(norm(src)):
            for p in mt.group(1).replace(" ", "").split("..."):
                if p and p not in pvs:
                    pvs.append(p)
    return pvs


def clean_form(s):
    return re.sub(r"[^a-zʔØ]", "", strip_accents(norm(s)).lower().replace("ø", "Ø"))


def load_rows(conn):
    """Every lexical_entries row with the fields the pipeline needs."""
    idx = load_page_index()
    gloss = defaultdict(list)
    for r in conn.execute("select entry_id, sense_number, definition, usage_notes from glosses order by entry_id, sense_number, id"):
        gloss[r[0]].append({"n": r[1], "definition": r[2] or "", "usage": r[3]})
    forms = defaultdict(dict)
    for r in conn.execute("select entry_id, form_number, skiri_form from paradigmatic_forms order by entry_id, form_number, id"):
        forms[r[0]].setdefault(str(r[1]), norm(r[2]))
    tags = defaultdict(list)
    for r in conn.execute("select entry_id, tag from semantic_tags order by entry_id, tag"):
        if r[1] not in tags[r[0]]:
            tags[r[0]].append(r[1])
    cogs = defaultdict(list)
    for r in conn.execute("select entry_id, language, form from cognates order by entry_id, id"):
        cogs[r[0]].append({"language": (r[1] or "").strip("."), "form": norm(r[2])})
    rows = []
    for r in conn.execute("""
            select l.entry_id, l.headword, l.normalized_form, l.phonetic_form, l.simplified_pronunciation,
                   l.stem_preverb, l.grammatical_class, l.verb_class, l.additional_forms, l.page_number,
                   l.source, l.blue_book_attested, e.raw_etymology, e.constituent_elements, e.literal_translation
            from lexical_entries l left join etymology e using(entry_id) order by l.entry_id"""):
        f, book_page, verified = pdf_file_for(r["page_number"], r["headword"], idx)
        if not verified and r["page_number"] is not None:
            # the stored page is wrong (e.g. the kaa- entries labelled page 2):
            # accept a relocation only if exactly one page starts a line with the headword
            hw0 = norm(r["headword"]).split(",")[0].split("[")[0].split("(")[0].strip()
            hits = [fn for fn, v in sorted(idx["_by_file"].items())
                    if hw0 and re.search(r"(?m)^\s*" + re.escape(hw0) + r"[ ,\[(]", norm(v["text"]))]
            if len(hits) == 1:
                f, book_page, verified = hits[0], idx["_by_file"][hits[0]]["book_page"], True
        try:
            add = json.loads(r["additional_forms"]) if r["additional_forms"] else []
        except Exception:
            add = []
        alts = headword_alternates(r["headword"])
        rows.append({
            "entry_id": r["entry_id"], "headword": norm(r["headword"]), "alternates": alts,
            "hw_key": alts[0] if alts else "", "normalized_form": r["normalized_form"],
            "phonetic_form": r["phonetic_form"], "simplified_pronunciation": r["simplified_pronunciation"],
            "stem_preverb": r["stem_preverb"], "preverbs": parse_preverbs(r["stem_preverb"], r["headword"]),
            "class": r["grammatical_class"], "verb_class": r["verb_class"],
            "additional_forms": add or [], "page_number": r["page_number"], "pdf_file": f,
            "book_page": book_page, "page_verified": verified, "source": r["source"] or "parks",
            "bb_attested": bool(r["blue_book_attested"]), "raw_etymology": r["raw_etymology"],
            "constituent_elements": r["constituent_elements"],
            "glosses": gloss.get(r["entry_id"], []), "forms": forms.get(r["entry_id"], {}),
            "tags": tags.get(r["entry_id"], []), "cognates": cogs.get(r["entry_id"], []),
        })
    return rows


def _gloss_text(row):
    return " ; ".join(g["definition"] for g in row["glosses"])


def _same_record(a, b):
    """Are two same-headword, same-class rows one dictionary record?  Returns (bool, reason)."""
    if (a["verb_class"] or "") != (b["verb_class"] or ""):
        return False, "verb class differs (%s vs %s)" % (a["verb_class"], b["verb_class"])
    if sorted(a["preverbs"]) != sorted(b["preverbs"]):
        return False, "preverb differs (%s vs %s)" % (a["preverbs"], b["preverbs"])
    fa = {k: clean_form(v) for k, v in a["forms"].items()}
    fb = {k: clean_form(v) for k, v in b["forms"].items()}
    ga, gb = content_stems(_gloss_text(a)), content_stems(_gloss_text(b))
    union = ga | gb
    jac = len(ga & gb) / len(union) if union else 1.0
    ea = re.sub(r"[\s<>\-]", "", norm(a["raw_etymology"] or ""))
    eb = re.sub(r"[\s<>\-]", "", norm(b["raw_etymology"] or ""))
    if fa and fb:
        shared = set(fa) & set(fb)
        if shared and all(fa[k] == fb[k] for k in shared):
            if jac >= 0.5:
                return True, "identical paradigm forms and matching glosses (overlap %.2f)" % jac
            return False, "identical paradigm forms but glosses differ (overlap %.2f): kept apart" % jac
        return False, "paradigm forms differ"
    if not fa and not fb:
        if ea == eb and jac >= 0.5:
            return True, "no paradigm; identical etymology and matching glosses (overlap %.2f)" % jac
        if ea != eb:
            return False, "etymology differs"
        return False, "glosses differ (overlap %.2f)" % jac
    # one row has the paradigm, the other does not
    if (not ea or not eb or ea == eb) and jac >= 0.6:
        return True, "one row lacks the paradigm; glosses match (overlap %.2f): split record" % jac
    return False, "one row has a paradigm, the other not, and glosses differ (overlap %.2f)" % jac


def resolve_duplicates(rows):
    """Group rows into lexemes.

    Returns (lexemes, decisions).  A lexeme is the canonical row plus a
    `member_ids` list; fields missing on the canonical row are filled from the
    other members.  Every multi-row headword+class group yields a decision.
    """
    groups = defaultdict(list)
    for r in rows:
        groups[(" , ".join(r["alternates"]), r["class"] or "")].append(r)
    parent = {r["entry_id"]: r["entry_id"] for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    decisions = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda r: r["entry_id"])
        if len(members) < 2:
            continue
        pair_notes = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                same, why = _same_record(members[i], members[j])
                pair_notes.append({"a": members[i]["entry_id"], "b": members[j]["entry_id"],
                                   "same_record": same, "reason": why})
                if same:
                    ra, rb = find(members[i]["entry_id"]), find(members[j]["entry_id"])
                    if ra != rb:
                        parent[max(ra, rb)] = min(ra, rb)
        clusters = defaultdict(list)
        for m in members:
            clusters[find(m["entry_id"])].append(m["entry_id"])
        decisions.append({
            "type": "duplicate_rows", "headword": members[0]["headword"], "class": key[1],
            "rows": [m["entry_id"] for m in members],
            "lexemes": sorted(sorted(v) for v in clusters.values()),
            "verdict": "merged" if len(clusters) < len(members) else "kept_apart",
            "evidence": pair_notes,
        })
    by_root = defaultdict(list)
    for r in rows:
        by_root[find(r["entry_id"])].append(r)
    lexemes = []
    for root in sorted(by_root):
        members = by_root[root]
        # canonical row: page confirmed by the text layer, then the fullest record
        def rank(r):
            return (not r["page_verified"], -len(r["forms"]), not r["raw_etymology"],
                    not r["constituent_elements"], r["entry_id"])
        members = sorted(members, key=rank)
        lex = dict(members[0])
        lex["lexeme_id"] = lex["entry_id"]
        lex["member_ids"] = sorted(m["entry_id"] for m in members)
        for other in members[1:]:
            for k in ("raw_etymology", "constituent_elements", "phonetic_form", "simplified_pronunciation",
                      "normalized_form", "verb_class", "stem_preverb"):
                if not lex.get(k) and other.get(k):
                    lex[k] = other[k]
            if not lex["forms"] and other["forms"]:
                lex["forms"] = other["forms"]
            for k in ("glosses", "tags", "cognates", "additional_forms"):
                if not lex[k] and other[k]:
                    lex[k] = other[k]
            lex["bb_attested"] = lex["bb_attested"] or other["bb_attested"]
        lexemes.append(lex)
    return lexemes, decisions
