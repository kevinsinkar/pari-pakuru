#!/usr/bin/env python3
"""Stage 2: the possession engine, measured as it is and as the app calls it.

    python scripts/engines_review/measure_possession.py

A. The stem. For every noun whose etymology Parks prints in pieces: does the
   engine strip the suffix his analysis shows, and is what is left his stem?
B. Locative and instrumental. The dictionary's own words in + hiriʔ, + kat and
   + ru: (i) the suffix joined to Parks's stem by the engine's own code;
   (ii) the same word asked for the way the app asks: from the headword of the
   plain noun, where the dictionary has one.
C. Parks's examples on p. 30 (Table 4), asked for the way the app asks.
D. Kinship, asked for the way the app asks: every kin noun of the dictionary.
E. The Blue Book's possession forms against what the engine gives.
F. Everything the app serves: /api/possession for every noun row.
G. The locative and instrumental forms Parks prints as examples under noun
   entries (680 one-word forms with his translation), against what the app
   offers for the same noun. UNSEEN: the engine was never run against them.

Nothing is changed. The engine's functions are imported and called.
Writes data/possession_*.jsonl and data/possession_summary.json.
"""
import re
from collections import Counter, defaultdict

from common import (DATA, TESTSETS, classify_one, clean, connect, out, pct, read_jsonl, strip_accents, variants,
                    write_json, write_jsonl)
from common import require_reviewed_state  # noqa: E402

require_reviewed_state(__file__)

import possession_engine as pe  # noqa: E402
import seams  # noqa: E402

NOUN_CLASSES = ("N", "N-DEP", "N-KIN", "NUM")          # the classes /api/possession accepts
PARKS_SUFFIXES = ("uʔ", "kis", "hiriʔ", "kat", "ru")


def first_headword(hw):
    return variants(hw)[0] if variants(hw) else hw


# ---------------------------------------------------------------------------
# A. The stem
# ---------------------------------------------------------------------------

def run_stems():
    rows = []
    for n in read_jsonl(TESTSETS / "noun_etymologies.jsonl"):
        hw = first_headword(n["headword"])
        stem, stripped = pe.extract_noun_stem(hw)
        parks_suffix = n["last_piece"] if n["last_piece"] in PARKS_SUFFIXES and len(n["pieces"]) > 1 else None
        row = {"entry_id": n["entry_id"], "headword": n["headword"], "etymology": n["etymology"],
               "engine_stem": stem, "engine_strips": stripped, "parks_last_piece": n["last_piece"],
               "parks_suffix": parks_suffix}
        eng = (stripped or "").lstrip("-") or None
        if eng == parks_suffix:
            row["suffix"] = "agree: no suffix" if eng is None else "agree: -" + eng
        elif eng and not parks_suffix:
            row["suffix"] = "engine strips -%s; Parks's analysis ends in another piece" % eng
        elif parks_suffix and not eng:
            row["suffix"] = "Parks has -%s; engine strips nothing" % parks_suffix
        else:
            row["suffix"] = "engine strips -%s; Parks has -%s" % (eng, parks_suffix)
        rows.append(row)
    return rows


def run_combining_forms(conn):
    """The stem against the combining forms Parks prints for a noun.

    Chapter 5 says the entry of a noun gives, in curly brackets, the shapes the
    noun takes when it is incorporated. The engine's stem is meant to be exactly
    that shape. The printed combining forms are in lexical_entries.additional_forms.
    """
    import json
    rows = []
    for r in conn.execute("select entry_id, headword, grammatical_class, additional_forms from lexical_entries "
                          "where grammatical_class in ('N','N-DEP','N-KIN','NUM') and additional_forms is not null "
                          "order by entry_id"):
        try:
            forms = json.loads(r["additional_forms"])
        except ValueError:
            continue
        comb = []
        for f in forms or []:
            if "comb" in (f.get("form_type") or ""):
                comb += [c.strip().rstrip("-") for c in re.split(r"[,;]", f.get("form") or "") if c.strip()]
        if not comb:
            continue
        hw = first_headword(r["headword"])
        stem, stripped = pe.extract_noun_stem(hw)
        rows.append({"entry_id": r["entry_id"], "headword": r["headword"], "class": r["grammatical_class"],
                     "printed_combining_forms": comb, "engine_stem": stem, "engine_strips": stripped,
                     "result": "one of the printed combining forms" if stem.lower() in [c.lower() for c in comb]
                     else "not a printed combining form"})
    return rows


# ---------------------------------------------------------------------------
# B. The dictionary's own words in + hiriʔ, + kat, + ru
# ---------------------------------------------------------------------------

def engine_join(stem, suffix):
    """Join a stem and a case suffix with the engine's own code."""
    if suffix == "hiriʔ":
        previous, suf, _ = pe.hiri_suffix(stem)
        return pe.apply_nominal_sc(pe.concatenate([previous, suf]))
    return pe.apply_nominal_sc(pe.concatenate([stem, suffix]))


def run_suffix_words(conn):
    by_stem = defaultdict(list)            # engine stem -> noun headwords of the dictionary
    for r in conn.execute("select headword, grammatical_class from lexical_entries "
                          "where grammatical_class in ('N','N-DEP','N-KIN','NUM')"):
        hw = first_headword(r["headword"])
        by_stem[pe.extract_noun_stem(hw.rstrip("-"))[0]].append((r["headword"], r["grammatical_class"]))
        by_stem[hw.rstrip("-")].append((r["headword"], r["grammatical_class"]))
    rows = []
    for w in read_jsonl(TESTSETS / "noun_suffix_words.jsonl"):
        stem_pieces = [p for part in w["stem_pieces"] for p in part.split(".")]
        # (i) Parks's stem, joined piece by piece with the engine's assembler
        stem_joined = pe.apply_nominal_sc(pe.concatenate(stem_pieces)) if len(stem_pieces) > 1 else stem_pieces[0]
        made = engine_join("".join(stem_pieces) if len(stem_pieces) == 1 else pe.concatenate(stem_pieces), w["suffix"])
        cause = min((classify_one(made.lower(), v.lower()) for v in w["words"]), key=lambda c: (c != "exact", c))
        row = {"headword": w["headword"], "grammatical_class": w["grammatical_class"], "etymology": w["etymology"],
               "suffix": w["suffix"], "from_parks_stem": made, "from_parks_stem_cause": cause,
               "stem_has_several_pieces": len(stem_pieces) > 1}
        # (ii) the way the app asks: from the plain noun's headword
        bases = []
        if len(stem_pieces) == 1:
            seen = set()
            for hw, gc in by_stem.get(stem_pieces[0], []):
                if hw not in seen and first_headword(hw) not in w["words"]:
                    seen.add(hw)
                    bases.append((hw, gc))
        row["plain_nouns_with_this_stem"] = [b[0] for b in bases]
        via = []
        for hw, gc in bases:
            table = pe.generate_paradigm_table(hw, noun_class=gc)      # the stored headword, as the app passes it
            offered = {f["type"]: f["form"] for f in table.get("locative_forms", [])}
            want = {"hiriʔ": ("instrumental", "locative"), "kat": ("locative",), "ru": ("locative",)}[w["suffix"]]
            got = [offered[t] for t in want if t in offered]
            ok = any(clean(g).lower() in [x.lower() for x in w["words"]] for g in got)
            via.append({"asked_for": hw, "class": gc, "system": table.get("system"), "offered": offered, "matches": ok})
        row["through_the_app"] = via
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# C. Parks's examples on p. 30, asked the way the app asks
# ---------------------------------------------------------------------------

# (what Parks prints, his gloss, the dictionary headword of the noun, which form the app offers for it)
PAGE_30 = [
    ("iksiriʔ", "by hand; on the hand", "iksuʔ", "locative"),
    ("ikstaaririʔ", "with the hands; on the hands", "iksuʔ", "locative (pl)"),
    ("sahiiru", "in Cheyenne country", "Sahi", "locative"),
    ("uukaahpaawiru", "among the Quapaw", "Ukaahpaa", "locative"),
    ("riihitawiru", "among the Ponca", "Riihita", "locative"),
    ("akahkat", "on the dwelling", "akaaruʔ", "locative"),
    ("asaakat", "among the horses", "asaa-", "locative"),
]


def run_page30(conn):
    rows = []
    for printed, gloss, headword, kind in PAGE_30:
        r = conn.execute("select grammatical_class from lexical_entries where headword=? "
                         "and grammatical_class in ('N','N-DEP','N-KIN','NUM')", (headword,)).fetchone()
        if not r:
            rows.append({"printed": printed, "gloss": gloss, "headword": headword, "result": "no such noun headword"})
            continue
        table = pe.generate_paradigm_table(headword, noun_class=r["grammatical_class"])
        offered = {f["type"]: f["form"] for f in table.get("locative_forms", [])}
        got = offered.get(kind)
        rows.append({"printed": printed, "gloss": gloss, "headword": headword, "class": r["grammatical_class"],
                     "system": table.get("system"), "offered": offered, "engine_gives": got,
                     "result": "no such form offered" if got is None else classify_one(got.lower(), printed.lower())})
    return rows


# ---------------------------------------------------------------------------
# D. Kinship through the app's path
# ---------------------------------------------------------------------------

def run_kinship(conn):
    kin = read_jsonl(TESTSETS / "kinship_appendix3.jsonl")
    by_form = {}
    for k in kin:
        for key in ("stem", "my", "your", "his_her"):
            for v in variants(k.get(key) or ""):
                by_form.setdefault(v.strip("-"), k)
    rows = []
    for r in conn.execute("select headword, grammatical_class, entry_id from lexical_entries "
                          "where grammatical_class='N-KIN' order by headword"):
        hw = first_headword(r["headword"])
        table = pe.generate_paradigm_table(hw, noun_class="N-KIN")
        forms = {p["person"]: p["form"] for p in table["persons"]}
        k = by_form.get(hw.strip("-"))
        row = {"headword": r["headword"], "system_used": table["system"], "engine": forms,
               "in_appendix_3": bool(k)}
        if k:
            want = {"1sg": k["my"], "2sg": k["your"], "3sg": k["his_her"]}
            row["appendix_3"] = want
            row["agrees"] = all((forms.get(p) or "—") == (want[p] or "—") for p in want)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# E. The Blue Book's possession forms
# ---------------------------------------------------------------------------

def letters(s):
    s = strip_accents(s).lower().replace("ʔ", "'")
    return re.sub(r"[^a-z']", "", s)


def run_blue_book():
    rows = []
    printed = read_jsonl(TESTSETS / "blue_book_possession.jsonl")
    engine = {
        "Here is my head.": pe.generate_possessive("paksuʔ", "1sg", noun_class="N-DEP").surface_form,
        "Here is my eye.": pe.generate_possessive("kirikuʔ", "1sg", noun_class="N-DEP").surface_form,
        "my hat": pe.generate_possessive("pakskuukuʔuʔ", "1sg", noun_class="N").surface_form,
        "your hat": pe.generate_possessive("pakskuukuʔuʔ", "2sg", noun_class="N").surface_form,
        "his hat": pe.generate_possessive("pakskuukuʔuʔ", "3sg", noun_class="N").surface_form,
    }
    seen = set()
    for p in printed:
        if p["english"] in engine and p["english"] not in seen:
            seen.add(p["english"])
            e = engine[p["english"]]
            pl, el = letters(p["printed"]), letters(e)
            # the Blue Book writes long vowels short and ' for the glottal stop: compare on that footing too
            el_bb = re.sub(r"([aiu])\1", r"\1", el)
            rows.append({"english": p["english"], "blue_book_prints": p["printed"], "book_page": p["book_page"],
                         "engine_gives": e,
                         "same_letters": pl == el,
                         "same_letters_once_long_vowels_are_written_short": re.sub(r"([aiu])\1", r"\1", pl) == el_bb,
                         "first_word_blue_book": p["printed"].split()[0], "first_word_engine": e.split()[0]})
    return rows


# ---------------------------------------------------------------------------
# F. Everything the app serves
# ---------------------------------------------------------------------------

def run_api(conn):
    tags = defaultdict(set)
    for r in conn.execute("select entry_id, tag from semantic_tags"):
        tags[r["entry_id"]].add(r["tag"])
    gloss = {r["entry_id"]: r["definition"] for r in conn.execute(
        "select entry_id, definition from glosses where sense_number=1 or sense_number is null")}
    rows = []
    all_rows = conn.execute("select entry_id, headword, grammatical_class, source from lexical_entries "
                            "where grammatical_class in ('N','N-DEP','N-KIN','NUM') order by entry_id").fetchall()
    for r in all_rows:
        hw = r["headword"]
        # the route looks the entry up by its spelling and takes the first row it finds
        first = conn.execute("select grammatical_class, entry_id from lexical_entries where headword = ?", (hw,)).fetchone()
        row = {"entry_id": r["entry_id"], "headword": hw, "class": r["grammatical_class"],
               "gloss": (gloss.get(r["entry_id"]) or "")[:60], "tags": sorted(tags.get(r["entry_id"], ())),
               "blue_book_only": r["source"] == "blue_book"}
        if first["grammatical_class"] not in NOUN_CLASSES:
            row["answer"] = "not a noun (the route found another entry with this spelling first)"
            rows.append(row)
            continue
        row["answered_for_another_entry"] = first["entry_id"] != r["entry_id"]
        table = pe.generate_paradigm_table(hw, noun_class=first["grammatical_class"])
        row["answer"] = table["system"]
        row["forms"] = {p["person"]: p["form"] for p in table["persons"]}
        row["marked_attested"] = any(p["is_attested"] for p in table["persons"])
        row["confidence"] = sorted({p["confidence"] for p in table["persons"]})
        row["case_forms"] = {f["type"]: f["form"] for f in table.get("locative_forms", [])}
        stem, stripped = pe.extract_noun_stem(hw)
        row["stem"], row["stripped"] = stem, stripped
        loc = pe.generate_locative(hw, noun_class=first["grammatical_class"]) if table["system"] != "kinship" else None
        row["locative_class"] = loc.noun_class if loc else None
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# G. The locative and instrumental forms Parks prints as examples under nouns
# ---------------------------------------------------------------------------

def run_case_examples(conn):
    """Each printed form against what /api/possession offers for the same noun."""
    tags = defaultdict(set)
    for r in conn.execute("select entry_id, tag from semantic_tags"):
        tags[r["entry_id"]].add(r["tag"])
    rows = []
    for ex in read_jsonl(TESTSETS / "noun_case_examples.jsonl"):
        row = {"entry_id": ex["entry_id"], "headword": ex["headword"], "printed": ex["printed"],
               "translation": ex["translation"], "suffix": ex["suffix"],
               "parks_meaning": "instrument (with, by)" if ex["translation_begins"] in ("with", "by") else "place (in, on, among)",
               "tagged_animal": "animal" in tags.get(ex["entry_id"], ())}
        if ex["suffix"] == "ru" and not re.search(r"among|country", ex["translation"], re.I):
            row["result"] = "left out: not a locative of the noun (a name or a verb form)"
            rows.append(row)
            continue
        # the route: the first entry with this spelling decides the class; the stored headword is passed as it is
        first = conn.execute("select grammatical_class from lexical_entries where headword = ?", (ex["headword"],)).fetchone()
        if first["grammatical_class"] not in NOUN_CLASSES:
            row["result"] = "the app answers 'not a noun'"
            rows.append(row)
            continue
        table = pe.generate_paradigm_table(ex["headword"], noun_class=first["grammatical_class"])
        offered = {f["type"]: f["form"] for f in table.get("locative_forms", [])}
        row["system"] = table["system"]
        row["offered"] = offered
        target = ex["printed"].lower()
        hits = [t for t, form in offered.items() if clean(form).lower() == target]
        row["offered_as"] = hits
        if hits:
            row["result"] = "exact"
        else:
            if ex["suffix"] == "hiriʔ":
                nearest = offered.get("instrumental") or offered.get("locative")
            else:
                nearest = offered.get("locative")
            row["nearest"] = nearest
            row["result"] = "no form produced" if not nearest else classify_one(nearest.lower(), target)
            if nearest:
                m = re.search(r"(sukat|kat|iriʔ|wiru|ru)$", nearest)
                row["engine_suffix"] = m.group(1) if m else None
        rows.append(row)
    return rows


def summarise_case_examples(rows):
    used = [r for r in rows if not r["result"].startswith("left out")]
    by_suffix = {}
    for suf in ("kat", "hiriʔ", "ru"):
        sel = [r for r in used if r["suffix"] == suf]
        by_suffix[suf] = {"forms": len(sel), "exact": sum(r["result"] == "exact" for r in sel),
                          "by_result": dict(Counter(r["result"] for r in sel))}
    hiri = [r for r in used if r["suffix"] == "hiriʔ"]
    s = {
        "forms": len(rows), "used": len(used), "nouns": len({r["entry_id"] for r in used}),
        "exact": sum(r["result"] == "exact" for r in used),
        "by_suffix": by_suffix,
        "by_result": dict(Counter(r["result"] for r in used)),
        "kat_words_for_which_the_engine_offers_another_suffix": dict(Counter(
            r.get("engine_suffix") for r in used if r["suffix"] == "kat" and r["result"] != "exact" and r.get("engine_suffix")
            and not r["engine_suffix"].endswith("kat"))),
        "hiri_forms_by_parks_meaning": dict(Counter(r["parks_meaning"] for r in hiri)),
        "hiri_forms_right_and_offered_as": dict(Counter(
            "%s -> offered as %s" % (r["parks_meaning"], "/".join(sorted(r["offered_as"])))
            for r in hiri if r["result"] == "exact")),
        "printed_instrument_forms_under_a_noun_tagged_animal": sum(
            1 for r in hiri if r["tagged_animal"] and r["parks_meaning"].startswith("instrument")),
        "printed_hiri_forms_under_a_noun_tagged_animal": sum(1 for r in hiri if r["tagged_animal"]),
        "headword_is_two_spellings_or_has_a_dash": sum(1 for r in used if re.search(r"[,/-]", r["headword"])),
        "of_those_exact": sum(1 for r in used if re.search(r"[,/-]", r["headword"]) and r["result"] == "exact"),
    }
    return s


def summarise_api(rows):
    answered = [r for r in rows if "forms" in r]
    animate = {"animal", "kinship", "social"}
    s = {
        "noun_rows": len(rows),
        "answer": dict(Counter(r["answer"] for r in rows)),
        "answered_for_another_entry_of_the_same_spelling": sum(1 for r in answered if r.get("answered_for_another_entry")),
        "marked_attested": sum(1 for r in answered if r["marked_attested"]),
        "marked_attested_by_system": dict(Counter(r["answer"] for r in answered if r["marked_attested"])),
        "my_form_begins_kti": sum(1 for r in answered if r["forms"].get("1sg", "").startswith("kti ")),
        "with_an_instrumental": sum(1 for r in answered if "instrumental" in r["case_forms"]),
        "with_an_instrumental_and_tagged_animal_kin_or_person": sum(
            1 for r in answered if "instrumental" in r["case_forms"] and animate & set(r["tags"])),
        "with_an_instrumental_tagged_animal": sum(
            1 for r in answered if "instrumental" in r["case_forms"] and "animal" in r["tags"]),
        "nouns_tagged_animal_kin_or_person_served": sum(1 for r in answered if animate & set(r["tags"])),
        "treated_as_a_tribe_or_place": sum(1 for r in answered if r["locative_class"] == "tribal"),
        "treated_as_a_tribe_and_gloss_names_a_tribe_or_people": sum(
            1 for r in answered if r["locative_class"] == "tribal"
            and re.search(r"tribe|band|people|indian|nation|country|pawnee|sioux", r["gloss"], re.I)),
        "stripped": dict(Counter(r["stripped"] or "nothing" for r in answered)),
        "body_part_forms_with_the_default_verb_hanging": sum(
            1 for r in answered if r["answer"] == "body_part"),
    }
    s["treated_as_a_tribe_examples_that_are_not"] = [
        {"headword": r["headword"], "gloss": r["gloss"], "locative": r["case_forms"].get("locative")}
        for r in answered if r["locative_class"] == "tribal"
        and not re.search(r"tribe|band|people|indian|nation|country|pawnee|sioux", r["gloss"], re.I)][:25]
    return s


def flashcard_nouns(conn, api_rows):
    """What the Possession box shows for the nouns of the first four flashcard weeks."""
    from common import ROOT, load_json
    sets = load_json(ROOT / "curriculum" / "flashcard_sets.json")
    weeks = sets["weeks"]
    by_id = {r["entry_id"]: r for r in api_rows}
    rows = []
    for wk in weeks:
        number = wk.get("week")
        if number is None or number > 4:
            continue
        for card in wk.get("cards", wk.get("entries", [])):
            eid = card.get("entry_id")
            r = by_id.get(eid)
            if not r:
                continue
            rows.append({"week": number, "headword": r["headword"], "gloss": r["gloss"], "answer": r["answer"],
                         "my": (r.get("forms") or {}).get("1sg"), "marked_attested": r.get("marked_attested"),
                         "case_forms": r.get("case_forms"), "tags": r["tags"]})
    return rows


def main():
    conn = connect()
    a = run_stems()
    write_jsonl(DATA / "possession_stems.jsonl", a)
    a2 = run_combining_forms(conn)
    write_jsonl(DATA / "possession_combining_forms.jsonl", a2)
    b = run_suffix_words(conn)
    write_jsonl(DATA / "possession_suffix_words.jsonl", b)
    c = run_page30(conn)
    d = run_kinship(conn)
    e = run_blue_book()
    g = run_case_examples(conn)
    write_jsonl(DATA / "possession_case_examples.jsonl", g)
    f = run_api(conn)
    write_jsonl(DATA / "possession_api.jsonl", f)
    fc = flashcard_nouns(conn, f)
    write_jsonl(DATA / "possession_first_flashcard_nouns.jsonl", fc)
    conn.close()

    by_suffix = defaultdict(Counter)
    for r in b:
        by_suffix[r["suffix"]][r["from_parks_stem_cause"]] += 1
    app_rows = [(r, v) for r in b for v in r["through_the_app"]]
    summary = {
        "A_stems": {"nouns_with_an_etymology_in_pieces": len(a), "suffix": dict(Counter(r["suffix"] for r in a))},
        "A_combining_forms": {
            "nouns_with_a_printed_combining_form": len(a2),
            "result": dict(Counter(r["result"] for r in a2)),
            "by_what_the_engine_strips": {k: dict(Counter(r["result"] for r in a2 if (r["engine_strips"] or "nothing") == k))
                                          for k in sorted({r["engine_strips"] or "nothing" for r in a2})},
            "examples_not_a_combining_form": [
                {"headword": r["headword"], "engine_stem": r["engine_stem"], "printed": r["printed_combining_forms"]}
                for r in a2 if r["result"].startswith("not")][:30]},
        "B_suffix_words": {
            "words": len(b),
            "from_parks_stem": {k: dict(v) for k, v in by_suffix.items()},
            "words_with_a_plain_noun_in_the_dictionary": sum(1 for r in b if r["through_the_app"]),
            "asked_through_the_app": len(app_rows),
            "app_gives_the_attested_word": sum(1 for r, v in app_rows if v["matches"]),
            "app_rows": [{"attested": r["headword"], "asked_for": v["asked_for"], "offered": v["offered"],
                          "matches": v["matches"]} for r, v in app_rows]},
        "C_page_30": c,
        "D_kinship": {"kin_nouns_in_the_dictionary": len(d), "found_in_appendix_3": sum(r["in_appendix_3"] for r in d),
                      "system_used": dict(Counter(r["system_used"] for r in d)),
                      "agree_with_appendix_3": sum(1 for r in d if r.get("agrees")),
                      "in_appendix_3_and_differ": [r for r in d if r["in_appendix_3"] and not r.get("agrees")],
                      "not_in_appendix_3": [{"headword": r["headword"], "system_used": r["system_used"],
                                             "my": r["engine"].get("1sg")} for r in d if not r["in_appendix_3"]]},
        "E_blue_book": e,
        "G_case_examples": summarise_case_examples(g),
        "F_api": summarise_api(f),
        "F_first_flashcard_weeks": {"nouns": len(fc), "answer": dict(Counter(r["answer"] for r in fc)),
                                    "my_form_begins_kti": sum(1 for r in fc if (r["my"] or "").startswith("kti ")),
                                    "marked_attested": sum(1 for r in fc if r["marked_attested"])},
    }
    write_json(DATA / "possession_summary.json", summary)

    s = summary["A_stems"]
    out("A. suffix against Parks's etymology: %d nouns; %s" % (s["nouns_with_an_etymology_in_pieces"], s["suffix"]))
    s = summary["A_combining_forms"]
    out("A. stem against Parks's printed combining forms: %d nouns; %s; by what is stripped: %s" % (
        s["nouns_with_a_printed_combining_form"], s["result"], s["by_what_the_engine_strips"]))
    s = summary["B_suffix_words"]
    out("B. suffix words: %d; from Parks's stem: %s" % (s["words"], s["from_parks_stem"]))
    out("   through the app: %d words have a plain noun; %d askings; the attested word comes back in %d" % (
        s["words_with_a_plain_noun_in_the_dictionary"], s["asked_through_the_app"], s["app_gives_the_attested_word"]))
    out("C. page 30:")
    for r in c:
        out("   %-16s %-30s asked for %-10s -> %-18s [%s]" % (r["printed"], r["gloss"], r["headword"],
                                                               r.get("engine_gives"), r["result"]))
    s = summary["D_kinship"]
    out("D. kinship: %d kin nouns; in Appendix 3: %d; agree: %d; system used: %s" % (
        s["kin_nouns_in_the_dictionary"], s["found_in_appendix_3"], s["agree_with_appendix_3"], s["system_used"]))
    out("E. Blue Book:")
    for r in e:
        out("   %-18s book %-26s engine %-28s same letters %s (long vowels aside %s)" % (
            r["english"], r["blue_book_prints"], r["engine_gives"], r["same_letters"],
            r["same_letters_once_long_vowels_are_written_short"]))
    s = summary["G_case_examples"]
    out("G. Parks's printed locative and instrumental examples (unseen): %d forms of %d nouns; the app offers the printed form for %d (%s)"
        % (s["used"], s["nouns"], s["exact"], pct(s["exact"], s["used"])))
    for suf, b in s["by_suffix"].items():
        out("   -%-6s %3d forms, %3d exact (%s)  %s" % (suf, b["forms"], b["exact"], pct(b["exact"], b["forms"]), b["by_result"]))
    out("   -kat words where the engine offers another suffix: %s" % s["kat_words_for_which_the_engine_offers_another_suffix"])
    out("   -hiriʔ forms by Parks's meaning: %s; right ones offered as: %s" % (
        s["hiri_forms_by_parks_meaning"], s["hiri_forms_right_and_offered_as"]))
    out("   -hiriʔ forms under a noun tagged animal: %d (instrument meaning: %d)" % (
        s["printed_hiri_forms_under_a_noun_tagged_animal"], s["printed_instrument_forms_under_a_noun_tagged_animal"]))
    out("   headword with two spellings or a dash: %d forms, %d exact" % (
        s["headword_is_two_spellings_or_has_a_dash"], s["of_those_exact"]))
    out("F. the app: %s" % {k: v for k, v in summary["F_api"].items() if not isinstance(v, list)})
    out("   first four flashcard weeks: %s" % summary["F_first_flashcard_weeks"])


if __name__ == "__main__":
    main()
