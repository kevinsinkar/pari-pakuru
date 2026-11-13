#!/usr/bin/env python3
"""Phase 3 and 4: the morpheme inventory, its decisions, and the frequency measures.

A lexical morpheme is a *sense*: a form together with one cluster of Parks's
glosses for it.  Two shapes are never merged because they look alike; every
split, merge and variant candidate is written to decisions.json with evidence.
"""
import re
from collections import Counter, defaultdict

from analysis import COMMUTATION_MIN, SENSE_EVIDENCED, _class_group, gloss_stems, is_word_like
from bluebook import content_stems, skel
from common import segments
from tiers import LEARNER_TIERS
import seams

REVIEW_WORDS = re.compile(
    r"\b(sacred|bundle|ceremon\w*|ritual\w*|doctor'?s? (dance|lodge|society)|medicine (man|lodge|society|bundle)|"
    r"priest\w*|shaman\w*|offering|sacrific\w*|pipe (dance|ceremony|stick)|pipestem|ghost dance|spirit\w*|"
    r"tirawaahat|heaven\w*|holy|religio\w*|deity|god\b|prayer|pray\b|society|war dance|scalp dance|"
    r"morning star|evening star|vision\w*|supernatural)", re.I)


def needs_community_review(lex):
    """Vocabulary that is, or may be, ceremonial or sacred: listed apart, never in early lessons."""
    text = " ; ".join(g["definition"] + " " + (g.get("usage") or "") for g in lex["glosses"])
    tags = {t.lower() for t in lex["tags"]}
    return bool(REVIEW_WORDS.search(text)) or bool(tags & {"ceremony", "ceremonial", "religion", "sacred", "ritual"})


def _wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    import math
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 5), round(min(1.0, c + h), 5)]


def morpheme_key(piece):
    """The inventory key of one analysed piece, or None when it has no identity yet."""
    if piece["role"] == "lexical":
        return piece["sense_id"] if piece.get("sense_evidence") in SENSE_EVIDENCED else None
    if piece["role"] == "preverb":
        return "%s=PREV" % piece["form"]
    return "%s=%s" % (piece["form"], piece["label"])


def lexeme_keys(rec):
    """(keys, complete): the morpheme keys of a record; complete is False if any piece lacks one."""
    keys, complete = [], bool(rec["pieces"]) or rec["e1"] == "citation"
    if rec["e1"] == "citation":
        return [rec["citation"][0]["sense_id"]], True
    for p in rec["pieces"]:
        k = morpheme_key(p)
        if k is None:
            complete = False
        else:
            keys.append(k)
    return keys, complete


def build_inventory(res, conn):
    records = res["records"]
    lex_by_id = {lex["lexeme_id"]: lex for lex in res["lexemes"]}
    rec_by_id = {r["lexeme_id"]: r for r in records}
    sense_by_id = res["sense_by_id"]

    # ---- reliable Blue Book links: lesson of first attestation per lexeme
    member_to_lex = {m: r["lexeme_id"] for r in records for m in r["member_ids"]}
    bb_first, bb_forms = {}, defaultdict(list)
    for row in conn.execute("""select entry_id, lesson_number, page_number, bb_skiri_form, bb_english, match_type
                               from blue_book_attestations where entry_id is not null
                               and match_type in ('exact_normalized', 'orthographic', 'propagated')
                               order by lesson_number, id"""):
        lid = member_to_lex.get(row[0])
        if lid is None or row[1] is None:
            continue
        bb_forms[lid].append({"form": row[3], "english": row[4], "lesson": row[1], "page": row[2], "link": row[5]})
        if lid not in bb_first or row[1] < bb_first[lid]:
            bb_first[lid] = row[1]
    for r in records:
        for att in ((r.get("e5_detail") or {}).get("attestations") or []):
            if att.get("lesson") is not None:
                lid = r["lexeme_id"]
                if lid not in bb_first or att["lesson"] < bb_first[lid]:
                    bb_first[lid] = att["lesson"]
    # ---- example sentences per lexeme
    n_examples = Counter()
    total_examples = 0
    for row in conn.execute("select entry_id, count(*) from examples group by entry_id"):
        total_examples += row[1]
        lid = member_to_lex.get(row[0])
        if lid:
            n_examples[lid] += row[1]

    # ---- occurrences
    occ = defaultdict(list)
    form_occ = defaultdict(set)              # form -> lexemes (A/B) containing the form in any sense
    for r in records:
        if r["e1"] == "citation":
            sid = r["citation"][0]["sense_id"]
            occ[sid].append({"lexeme_id": r["lexeme_id"], "tier": r["tier"], "evidence": "standalone",
                             "nested": False, "position": "whole word", "rules": [], "partners": []})
            continue
        if r["e1"] != "printed":
            continue
        pieces = r["pieces"]
        surface_idx = set(r["e2"].get("piece_index") or range(len(pieces)))
        keys = [morpheme_key(p) for p in pieces]
        lexical_idx = [i for i, p in enumerate(pieces) if p["role"] == "lexical"]
        for i, p in enumerate(pieces):
            if r["tier"] in LEARNER_TIERS:
                form_occ[p["form"]].add(r["lexeme_id"])
            k = keys[i]
            if k is None:
                continue
            if p["role"] == "lexical":
                pos = "only root" if len(lexical_idx) == 1 else (
                    "first" if i == lexical_idx[0] else "last" if i == lexical_idx[-1] else "middle")
            else:
                pos = "prefix" if i == 0 else "suffix" if i == len(pieces) - 1 else "inner"
            occ[k].append({"lexeme_id": r["lexeme_id"], "tier": r["tier"], "evidence": p.get("sense_evidence")
                           or ("label printed" if not p.get("label_inferred") else "label by default"),
                           "nested": bool(p.get("stem_ref")), "position": pos,
                           "rules": r["e2"].get("rules") or [], "exact": r["e2"]["status"] == "exact",
                           "partners": [x for j, x in enumerate(keys) if j != i and x]})

    def tier_counts(items):
        seen = {}
        for o in items:
            seen.setdefault(o["lexeme_id"], o["tier"])
        c = Counter(seen.values())
        return {"A": c["A"], "A+B": c["A"] + c["B"], "A+B+C": c["A"] + c["B"] + c["C"]}

    def measures(key, items):
        ab = [o for o in items if o["tier"] in LEARNER_TIERS]
        lex_ab = sorted({o["lexeme_id"] for o in ab})
        partners = Counter()
        for o in ab:
            for x in set(o["partners"]):
                partners[x] += 1
        once = sum(1 for o in ab if o["partners"] and all(partners[x] == 1 for x in set(o["partners"])))
        exact = [o for o in ab if o.get("exact")]
        plain = sum(1 for o in exact if not o["rules"])
        rule_use = Counter(x for o in exact for x in set(o["rules"]))
        ex_n = sum(n_examples.get(l, 0) for l in lex_ab)
        lessons = sorted(bb_first[l] for l in lex_ab if l in bb_first)
        return {
            "type_frequency": tier_counts(items),
            "direct_vs_nested": {"direct": len({o["lexeme_id"] for o in ab if not o["nested"]}),
                                 "inside_a_compound_stem": len({o["lexeme_id"] for o in ab if o["nested"]})},
            "productivity": {"distinct_partners": len(partners),
                             "formations_seen_once": once, "formations": len(ab),
                             "share_seen_once": round(once / len(ab), 3) if ab else None},
            "token_frequency": {"example_sentences": ex_n, "of_total": total_examples,
                                "share": round(ex_n / total_examples, 5) if total_examples else 0,
                                "ci95": _wilson(ex_n, total_examples),
                                "note": "example sentences attached to tier A/B words built with this morpheme; "
                                        "the corpus has %d sentences, so treat as a secondary signal" % total_examples},
            "blue_book": {"first_lesson": lessons[0] if lessons else None, "words_attested": len(lessons)},
            "transparency": {"words_reproduced_exactly": len(exact), "by_plain_concatenation": plain,
                             "share_plain": round(plain / len(exact), 3) if exact else None,
                             "rules_at_work": dict(sorted(rule_use.items(), key=lambda kv: (-kv[1], kv[0])))},
            "positions": dict(Counter(o["position"] for o in ab)),
            "sense_evidence": dict(Counter(o["evidence"] for o in ab)),
        }

    def examples_for(items, n=8):
        """Attested example words, best-corroborated first; each fully traceable."""
        seen, outp = set(), []
        order = {"A": 0, "B": 1, "C": 2, None: 3}
        for o in sorted(items, key=lambda o: (order.get(o["tier"], 3), o["nested"],
                                              o["lexeme_id"] not in bb_first, len(rec_by_id[o["lexeme_id"]]["pieces"]),
                                              o["lexeme_id"])):
            if o["lexeme_id"] in seen or o["tier"] not in LEARNER_TIERS:
                continue
            seen.add(o["lexeme_id"])
            r, lx = rec_by_id[o["lexeme_id"]], lex_by_id[o["lexeme_id"]]
            outp.append({"lexeme_id": r["lexeme_id"], "headword": r["headword"], "class": r["class"],
                         "verb_class": r["verb_class"], "gloss": r["gloss"], "book_page": r["book_page"],
                         "phonetic_form": lx["phonetic_form"], "tier": r["tier"],
                         "pieces": [p["form"] for p in r["pieces"]] or [r["headword"]],
                         "literal": r["literal"], "rules": r["e2"].get("rules") or [],
                         "needs_community_review": needs_community_review(lx)})
            if len(outp) >= n:
                break
        return outp

    # ---- lexical morphemes
    roots = []
    for sid in sorted(sense_by_id):
        c = sense_by_id[sid]
        items = occ.get(sid, [])
        standalone = sorted({a["lexeme_id"] for a in c["anchors"] if a["kind"] == "standalone"})
        aligned = Counter(a["text"].strip() for a in c["anchors"] if a["kind"] == "aligned")
        classes = Counter()
        label_stems = gloss_stems(c["label"])
        own = [a for a in c["anchors"] if a["kind"] == "standalone"]
        matching = [a for a in own if a["stems"] & label_stems] or own
        for a in matching:
            classes[(lex_by_id[a["lexeme_id"]]["class"] or "").split(",")[0].strip()] += 1
        ab_lex = {o["lexeme_id"] for o in items if o["tier"] in LEARNER_TIERS}
        a_lex = {o["lexeme_id"] for o in items if o["tier"] == "A"}
        host_groups = Counter(_class_group(rec_by_id[l]["class"]) for l in ab_lex)
        positions = Counter(o["position"] for o in items if o["tier"] in LEARNER_TIERS)
        if c.get("gram_label"):
            cls, basis = "derivational affix", "manual decision: " + (c.get("manual_evidence") or "")
        elif classes:
            top = classes.most_common(1)[0][0]
            cls = ("noun root" if top.startswith("N") else "descriptive stem" if top == "VD" else
                   "locative" if top in ("VL", "LOC") else "verb root" if top.startswith("V") else
                   "particle or adverb")
            basis = "its own dictionary entry is class %s (%s)" % (top, ", ".join(standalone[:3]))
        else:
            lastish = positions["last"] + positions["only root"]
            if host_groups["V"] > host_groups["N"] and lastish >= positions["first"] + positions["middle"]:
                cls = "verb root (bound, inferred)"
            elif host_groups["N"] >= host_groups["V"]:
                cls = "noun root (bound, inferred)"
            else:
                cls = "incorporated element (bound, inferred)"
            basis = "no dictionary entry of its own; inferred from the %d words it builds" % len(ab_lex)
        n_comm = len({a["lexeme_id"] for a in c["anchors"] if a["kind"] == "commutation"})
        by_commutation = n_comm >= COMMUTATION_MIN
        printed_meaning = (bool(aligned) or bool(standalone) or bool(c.get("n_derived")) or bool(c.get("gram_label"))
                           or by_commutation)
        how_known = ("meaning printed by Parks" if (aligned or standalone or c.get("n_derived") or c.get("gram_label"))
                     else "meaning shown by commutation in %d words" % n_comm)
        if c.get("stored_parse_only") or not printed_meaning:
            tier, why = "C", ("the meaning is not printed by Parks for this piece alone, and fewer than %d words "
                              "establish it by commutation" % COMMUTATION_MIN)
        elif len(ab_lex) >= 3 and a_lex:
            tier, why = "A", "%s; builds %d tier A/B words, %d of them tier A" % (how_known, len(ab_lex), len(a_lex))
        elif len(ab_lex) >= 2:
            tier, why = "B", "%s; builds %d tier A/B words" % (how_known, len(ab_lex))
        else:
            tier, why = "C", "%s, but found in fewer than two tier A/B words" % how_known
        segs = segments(c["form"])
        rec = {"id": sid, "form": c["form"], "meaning": c["label"],
               "gloss_variants": [{"gloss": g, "n": n} for g, n in sorted(aligned.items(), key=lambda kv: (-kv[1], kv[0]))[:8]],
               "class": cls, "class_basis": basis, "grammatical_label": c.get("gram_label"),
               "tier": tier, "tier_reason": why,
               "evidence": {"E1_glossed_by_parks_in": sum(aligned.values()),
                            "own_dictionary_entries": standalone,
                            "root_plus_NOM_nouns": c.get("n_derived", 0),
                            "E4_commutation_words": n_comm,
                            "E3_words_with_paradigm_confirmation": len({o["lexeme_id"] for o in items
                                                                        if rec_by_id[o["lexeme_id"]]["e3"] == "confirm"}),
                            "E5_words_with_blue_book_seam": len({o["lexeme_id"] for o in items
                                                                 if rec_by_id[o["lexeme_id"]]["e5"] == "confirm"}),
                            "E7_words_with_cognate": len({o["lexeme_id"] for o in items
                                                          if (rec_by_id[o["lexeme_id"]].get("e7") or {}).get("shows_a_root")})},
               "segments": len(segs), "examples": examples_for(items)}
        rec.update(measures(sid, items))
        if len(segs) <= 2:
            inside = sum(1 for lex in res["lexemes"] if any(c["form"] in t for t in lex["alternates"]))
            placed = len({o["lexeme_id"] for o in items})
            rec["chance_baseline"] = {"headwords_containing_the_string": inside, "words_where_an_analysis_places_it": placed,
                                      "note": "a short string occurs by chance: only analysed occurrences are counted"}
        own = [lex_by_id[l] for l in standalone]
        comb = sorted({f["form"] for lx in own for f in lx["additional_forms"] if "comb" in (f.get("form_type") or "")})
        if comb:
            rec["combining_forms_printed_by_parks"] = comb
        roots.append(rec)
    roots.sort(key=lambda r: (-r["type_frequency"]["A+B"], -r["type_frequency"]["A+B+C"], r["id"]))
    for i, r in enumerate(roots, 1):
        r["rank"] = i

    # ---- grammatical affixes found in the dictionary's own etymologies
    slot_of = {}
    for row in conn.execute("select morpheme_form, label, slot_number, slot_name from morpheme_inventory"):
        slot_of[(re.sub(r"[^a-zʔ]", "", (row[0] or "").lower()), (row[1] or "").upper())] = (row[2], row[3])
    abbr = {}
    for row in conn.execute("select abbreviation, meaning from morpheme_abbreviations"):
        abbr[(row[0] or "").strip(".").upper()] = row[1]
    affixes = []
    for key in sorted(k for k in occ if "=" in k):
        form, label = key.split("=", 1)
        items = occ[key]
        printed = sum(1 for o in items if o["evidence"] == "label printed")
        d = res["role_defaults"].get(form)
        slot = None
        for lab in re.split(r"[/ ]", label):
            if (form, lab.upper()) in slot_of:
                slot = slot_of[(form, lab.upper())]
        ab = {o["lexeme_id"] for o in items if o["tier"] in LEARNER_TIERS}
        if label == "PREV":
            tier, why = "A", "preverb: Parks GO p.31 names ir-/a-, uur- and ut- as the three preverbs"
        elif printed >= 3 and len(ab) >= 3:
            tier, why = "A", "label printed by Parks %d times; in %d tier A/B words" % (printed, len(ab))
        elif (printed >= 1 or (d and d["basis"] == "manual")) and len(ab) >= 2:
            tier, why = "B", "label printed %d times%s; in %d tier A/B words" % (
                printed, " and fixed by a cited decision" if d and d["basis"] == "manual" else "", len(ab))
        else:
            tier, why = "C", "label printed %d times; in %d tier A/B words" % (printed, len(ab))
        positions = Counter(o["position"] for o in items)
        kind = "preverb" if label == "PREV" else positions.most_common(1)[0][0]
        rec = {"id": key, "form": form, "label": label, "meaning": abbr.get(label.split("/")[0].upper()) or label,
               "kind": kind, "category": "derivational or stem-forming affix (found in dictionary etymologies)",
               "slot": {"number": slot[0], "name": slot[1]} if slot else None,
               "tier": tier, "tier_reason": why,
               "evidence": {"E1_label_printed_by_parks_in": printed,
                            "label_supplied_by_default_in": len(items) - printed,
                            "default_basis": (d or {}).get("basis"), "default_evidence": (d or {}).get("evidence")},
               "examples": examples_for(items)}
        rec.update(measures(key, items))
        affixes.append(rec)
    affixes.sort(key=lambda r: (-r["type_frequency"]["A+B"], r["id"]))
    for i, a in enumerate(affixes, 1):
        a["rank"] = i

    # ---- inflectional affixes: Parks's own tables and worked examples (no segmentation of ours)
    from common import GOLD, load_json
    g1 = load_json(GOLD / "g1_go_examples.json")["examples"]
    g1_count, g1_ex = Counter(), {}
    for e in g1:
        if "ocr_b" in e["flags"] or "surface_suspect" in e["flags"]:
            pass
        for pc in e["pieces"]:
            if pc.get("label"):
                k = (re.sub(r"[^a-zʔØ:]", "", pc["form"]), pc["label"])
                g1_count[k] += 1
                if not e["flags"]:
                    g1_ex.setdefault(k, {"form": e["surface"], "translation": e["translation"], "go_page": e["go_page"]})
    inflection = []
    for row in conn.execute("""select slot_number, slot_name, morpheme_form, label, person_constraint,
                                      mode_constraint, verb_class_constraint, notes
                               from morpheme_inventory order by slot_number, id"""):
        f = re.sub(r"[^a-zʔØ:]", "", row[2] or "")
        n = sum(v for (ff, lab), v in g1_count.items() if ff == f and (row[3] or "").split(".")[0] in lab)
        exm = next((g1_ex[k] for k in sorted(g1_ex) if k[0] == f and (row[3] or "").split(".")[0] in k[1]), None)
        inflection.append({"form": row[2], "label": row[3], "slot": {"number": row[0], "name": row[1]},
                           "constraints": {"person": row[4], "mode": row[5], "verb_class": row[6]}, "notes": row[7],
                           "category": "inflectional affix (Parks, Grammatical Overview tables)",
                           "worked_examples_in_grammatical_overview": n, "example": exm,
                           "source": "morpheme_inventory table (Parks GO Tables 7-17); Appendix 1 paradigms"})
    in_table = {re.sub(r"[^a-zʔØ:]", "", a["form"] or "") for a in inflection}
    extra = defaultdict(lambda: {"n": 0, "pages": set(), "example": None})
    for e in g1:
        if {"ocr_b", "surface_suspect"} & set(e["flags"]):
            continue
        for pc in e["pieces"]:
            f = re.sub(r"[^a-zʔØ:]", "", pc["form"])
            if pc.get("label") and f and f not in in_table and f.replace(":", "") not in in_table:
                d = extra[(pc["form"], pc["label"])]
                d["n"] += 1
                d["pages"].add(e["go_page"])
                d["example"] = d["example"] or {"form": e["surface"], "translation": e["translation"],
                                                "go_page": e["go_page"]}
    for (form, label), d in sorted(extra.items(), key=lambda kv: (-kv[1]["n"], kv[0])):
        inflection.append({"form": form, "label": label, "slot": {"number": None, "name": "not in the slot table"},
                           "constraints": {}, "notes": None,
                           "category": "inflectional affix (labelled in Parks's worked examples)",
                           "worked_examples_in_grammatical_overview": d["n"], "example": d["example"],
                           "source": "Parks, Grammatical Overview, worked examples on p. %s" % ", ".join(
                               str(x) for x in sorted(x for x in d["pages"] if x))})

    # ---- decisions
    decisions = list(res["dup_decisions"])
    for form, d in sorted(res["role_defaults"].items()):
        decisions.append({"type": "role_default", "form": form, "role": d["role"], "label": d.get("label"),
                          "label_by_class": d.get("label_by_class"), "applies_to_classes": d.get("classes"),
                          "position": d.get("position"), "basis": d["basis"], "occurrences": d["occurrences"],
                          "labels_printed_by_parks": d["labelled"], "evidence": d.get("evidence")})
    for form in sorted(res["senses"].clusters):
        clusters = res["senses"].clusters[form]
        if len(clusters) < 2:
            continue
        decisions.append({
            "type": "homonym_split", "form": form, "verdict": "kept_apart",
            "reason": "Parks's glosses for this shape fall into groups that share no content word",
            "senses": [{"id": c["sense_id"], "meaning": c["label"], "aligned_glosses": c["n_aligned"],
                        "own_entries": sorted({a["lexeme_id"] for a in c["anchors"] if a["kind"] == "standalone"}),
                        "sample_glosses": sorted({a["text"].strip()[:70] for a in c["anchors"]})[:4],
                        "words_AB": len({o["lexeme_id"] for o in occ.get(c["sense_id"], []) if o["tier"] in LEARNER_TIERS})}
                       for c in clusters]})
    for d in res["manual"]:
        if d.get("type") in ("sense_merge", "sense_anchor"):
            decisions.append(dict(d, basis="manual", verdict="merged" if d["type"] == "sense_merge" else "anchored"))
    # variant candidates: same skeleton and a shared content word, never merged automatically
    by_skel = defaultdict(list)
    for r in roots:
        by_skel[skel(r["form"])].append(r)
    for sk in sorted(by_skel):
        group = by_skel[sk]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a["form"] == b["form"]:
                    continue
                shared = sense_by_id[a["id"]]["stems"] & sense_by_id[b["id"]]["stems"]
                if not shared:
                    continue
                decisions.append({
                    "type": "variant_candidate", "verdict": "not_merged",
                    "a": a["id"], "b": b["id"], "forms": [a["form"], b["form"]],
                    "difference": "vowel length, ʔ or h only (no rule derives one shape from the other)",
                    "shared_meaning_words": sorted(shared)[:5],
                    "words_AB": {a["form"]: a["type_frequency"]["A+B"], b["form"]: b["type_frequency"]["A+B"],
                                 "combined": a["type_frequency"]["A+B"] + b["type_frequency"]["A+B"]},
                    "question": "Is %s the same morpheme as %s, and if so what conditions the difference?" % (
                        a["form"], b["form"])})
    return {"roots": roots, "affixes": affixes, "inflection": inflection, "decisions": decisions,
            "occurrences": occ, "bb_first": bb_first, "bb_forms": bb_forms, "n_examples": n_examples,
            "total_examples": total_examples, "form_occ": form_occ}


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def decodability(res, inv):
    """For each lexeme: the set of morpheme keys a learner needs, or None if it cannot be decoded."""
    need = {}
    for r in res["records"]:
        if r["tier"] not in LEARNER_TIERS:
            continue
        keys, complete = lexeme_keys(r)
        if complete and keys:
            need[r["lexeme_id"]] = set(keys)
    return need


def coverage_curve(order, need, res, inv):
    """Cumulative share decodable after each morpheme in `order` is taught."""
    n_lex = len(res["records"])
    bb_lex = set(inv["bb_first"])
    total_ex = inv["total_examples"]
    taught = set()
    remaining = {l: set(k) for l, k in need.items()}
    by_key = defaultdict(set)
    for l, ks in need.items():
        for k in ks:
            by_key[k].add(l)
    done = set()
    curve = []
    ex_done = 0
    touched = set()
    for step, key in enumerate(order, 1):
        taught.add(key)
        for l in by_key.get(key, ()):
            touched.add(l)
            remaining[l].discard(key)
            if not remaining[l] and l not in done:
                done.add(l)
                ex_done += inv["n_examples"].get(l, 0)
        curve.append({"step": step, "morpheme": key, "words_decodable": len(done),
                      "words_with_a_known_piece": len(touched),
                      "share_of_dictionary": round(len(done) / n_lex, 4),
                      "share_of_analysable_words": round(len(done) / len(need), 4) if need else 0,
                      "blue_book_words_decodable": len(done & bb_lex),
                      "share_of_blue_book_words": round(len(done & bb_lex) / len(bb_lex), 4) if bb_lex else 0,
                      "share_of_example_sentences": round(ex_done / total_ex, 4) if total_ex else 0})
    return curve
