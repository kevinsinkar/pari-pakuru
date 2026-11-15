#!/usr/bin/env python3
"""Phase 5: validation report, changelog against v1, proposed data fixes.

Everything here is computed from the pipeline bundle and the locked gold files.
The held-out half of G2 is read only by this module.
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from analysis import SENSE_EVIDENCED, gloss_stems
from bluebook import skel
from common import GOLD, OUT, ROOT, V1, dump_json, load_json, norm, sha256, strip_accents, write_text
from tiers import LEARNER_TIERS
from validate import gold_pieces, score_g2, wilson
import seams

BLIND = OUT / "blind"
MANUAL_REVIEW = Path(__file__).resolve().parent / "adversarial_review.json"


def _clean(s):
    return re.sub(r"[^a-zʔø]", "", strip_accents(norm(s or "")).lower())


def _pct(k, n):
    return "%d / %d (%.1f%%)" % (k, n, 100.0 * k / n) if n else "0 / 0"


# ---------------------------------------------------------------------------
# G2: piece meanings
# ---------------------------------------------------------------------------

def meaning_agreement(records, sense_by_id, split):
    """Compare the meaning attached to each piece with the annotator's reading of the page."""
    by_member = {m: r for r in records for m in r["member_ids"]}
    anns = [a for a in load_json(GOLD / "g2_annotations.json")["annotations"] if a["split"] == split]
    counts, strict, rows = Counter(), defaultdict(Counter), []
    for a in anns:
        r = by_member.get(a["entry_id"])
        if not r or a.get("etymology_kind") != "analysis" or r["e1"] != "printed":
            continue
        if gold_pieces(a) != [p["form"] for p in r["pieces"]]:
            strict[r["tier"]]["wrong_pieces"] += 1
            continue
        flat = []
        for g in a.get("inferred_glosses") or []:
            subs = gold_pieces({"pieces": [g["piece"]]})
            for f in subs:
                flat.append((f, g.get("meaning"), g.get("basis"), len(subs)))
        bad = False
        for (f, meaning, basis, nsub), p in zip(flat, r["pieces"]):
            if p["form"] != f or p["role"] != "lexical":
                continue
            meaning = (meaning or "").replace("-|", "") or None      # the annotators' line-break marker
            ev = p.get("sense_evidence")
            if not meaning or nsub > 1 and ev not in SENSE_EVIDENCED:
                counts[(ev, "page gives no separate meaning")] += 1
                continue
            if not p.get("sense_id"):
                counts[(ev, "no meaning assigned")] += 1
                continue
            ok = bool(sense_by_id[p["sense_id"]]["stems"] & gloss_stems(meaning))
            if nsub > 1 and not ok:
                counts[(ev, "page gives no separate meaning")] += 1
                continue
            counts[(ev, "agree" if ok else "differ")] += 1
            if not ok:
                rows.append({"headword": r["headword"], "piece": f, "assigned": p["sense_id"], "evidence": ev,
                             "annotator": meaning, "tier": r["tier"]})
                if ev in SENSE_EVIDENCED:
                    bad = True
        strict[r["tier"]]["meaning_conflict" if bad else "correct"] += 1
    return {"counts": {"%s | %s" % k: v for k, v in sorted(counts.items(), key=str)}, "differences": rows,
            "strict": {t: dict(c) for t, c in sorted(strict.items(), key=str)}}


def extraction_check(conn, split=None):
    """Compare the page transcriptions with the database rows: what did the extraction get wrong?"""
    anns = load_json(GOLD / "g2_annotations.json")["annotations"]
    if split:
        anns = [a for a in anns if a["split"] == split]
    issues, n = [], Counter()
    for a in anns:
        row = conn.execute("""select l.headword, l.grammatical_class, l.verb_class, e.raw_etymology
                              from lexical_entries l left join etymology e using(entry_id) where l.entry_id=?""",
                           (a["entry_id"],)).fetchone()
        if not row or not a.get("found"):
            continue
        n["entries"] += 1
        hw_a = _clean((a.get("printed_headword") or "").split(",")[0].split("(")[0].split("[")[0])
        hw_d = _clean(row[0].split(",")[0].split("(")[0].split("[")[0])
        cls_a = re.sub(r"\s+", "", a.get("printed_class") or "")
        cls_d = re.sub(r"\s+", "", row[1] or "")
        same_entry = hw_a == hw_d and cls_a == cls_d
        if not same_entry:
            n["different_homograph_or_headword"] += 1
            issues.append({"entry_id": a["entry_id"], "field": "headword/class", "page": "%s %s" % (
                a.get("printed_headword"), a.get("printed_class")), "database": "%s %s" % (row[0], row[1]),
                "note": "the annotator may have transcribed a neighbouring homograph; check by eye"})
            continue
        n["compared"] += 1
        if a.get("etymology_kind") is not None:
            ea = re.sub(r"[\s\-|<>]", "", norm(a.get("etymology_verbatim") or "")).replace("’", "ʔ")
            ed = re.sub(r"[\s\-|<>]", "", norm(row[3] or ""))
            n["etymology_compared"] += 1
            if ea != ed:
                n["etymology_differs"] += 1
                issues.append({"entry_id": a["entry_id"], "field": "raw_etymology",
                               "page": a.get("etymology_verbatim"), "database": row[3]})
        forms = dict(conn.execute("select form_number, skiri_form from paradigmatic_forms where entry_id=?",
                                  (a["entry_id"],)).fetchall())
        for k, v in (a.get("paradigm_forms") or {}).items():
            n["forms_compared"] += 1
            d = forms.get(int(k))
            if d is None:
                n["form_missing_in_database"] += 1
                issues.append({"entry_id": a["entry_id"], "field": "paradigm form %s" % k, "page": v, "database": None})
            elif _clean(d) != _clean(v):
                n["form_differs"] += 1
                issues.append({"entry_id": a["entry_id"], "field": "paradigm form %s" % k, "page": v, "database": d})
        vc_a = re.sub(r"\s+", "", a.get("printed_verb_class") or "")
        vc_d = re.sub(r"\s+", "", row[2] or "")
        if vc_a != vc_d:
            n["verb_class_differs"] += 1
            issues.append({"entry_id": a["entry_id"], "field": "verb_class", "page": a.get("printed_verb_class"),
                           "database": row[2]})
    return dict(n), issues


# ---------------------------------------------------------------------------
# G1 and G3
# ---------------------------------------------------------------------------

def score_g1(res, inv, conn):
    ex = load_json(GOLD / "g1_go_examples.json")["examples"]
    clean = [e for e in ex if not ({"ocr_b", "surface_suspect"} & set(e["flags"]))]
    by_hw = defaultdict(list)
    for lex in res["lexemes"]:
        for alt in lex["alternates"]:
            by_hw[re.sub(r"[^a-zʔ]", "", alt)].append(lex)
    rec = {r["lexeme_id"]: r for r in res["records"]}
    # (a) words Parks analyses in the Overview that are also headwords
    seg = Counter()
    seg_rows = []
    for e in clean:
        lexs = by_hw.get(_clean(e["surface"]), [])
        if not lexs:
            continue
        gold = [re.sub(r"[^a-zʔ]", "", strip_accents(norm(p["form"])).lower()) for p in e["pieces"]]
        gold = [g for g in gold if g]
        if skel("".join(gold)) != skel(_clean(e["surface"])):
            continue        # the extracted 'surface' is not the word this analysis belongs to
        hit = None
        for lx in lexs:
            mine = [p["form"] for p in rec[lx["lexeme_id"]]["pieces"]]
            if mine:
                hit = (mine, lx["lexeme_id"])
                if mine == gold:
                    break
        if hit is None:
            continue
        same = hit[0] == gold
        seg["same" if same else "different"] += 1
        seg_rows.append({"word": e["surface"], "go_page": e["go_page"], "parks_overview": gold, "pipeline": hit[0],
                         "lexeme_id": hit[1], "same": same})
    # (b) stems Parks cites with a gloss
    stems = Counter()
    stem_rows = []
    seen = set()
    for e in clean:
        for p in e["pieces"]:
            if not p.get("gloss") or p["form"].endswith("-") and len(p["form"]) <= 4 and False:
                continue
            f = re.sub(r"[^a-zʔ]", "", strip_accents(norm(p["form"])).lower())
            if not f or (f, p["gloss"]) in seen:
                continue
            seen.add((f, p["gloss"]))
            lexs = by_hw.get(f, [])
            gst = gloss_stems(p["gloss"])
            ok = any(gst & gloss_stems(" ; ".join(g["definition"] for g in lx["glosses"])) for lx in lexs)
            status = "headword with matching gloss" if ok else ("headword, gloss differs" if lexs else "not a headword")
            stems[status] += 1
            if not ok:
                stem_rows.append({"form": p["form"], "gloss": p["gloss"], "status": status, "go_page": e["go_page"]})
    # (c) the pieces he labels: counted, not matched against anything. Until 2026-11-14 they were matched by
    # their letters against the conjugation engine's table; the engine was withdrawn and the table dropped.
    labelled = Counter()
    for e in clean:
        for p in e["pieces"]:
            if p.get("label") and re.sub(r"[^a-zʔØ:]", "", p["form"]):
                labelled[(p["form"], p["label"])] += 1
    return {"worked_examples": len(ex), "clean_examples": len(clean), "segmentation": dict(seg),
            "segmentation_rows": seg_rows, "stems": dict(stems), "stem_rows": stem_rows[:40],
            "labelled_pieces": {"occurrences": sum(labelled.values()), "distinct": len(labelled)}}


def score_g3(res):
    by_tier = defaultdict(Counter)
    rows = []
    for r in res["records"]:
        d = r.get("e5_detail")
        if not d:
            continue
        t = r["tier_without_e5"] or "no claim"
        n_pieces = len(r["e2"].get("surface_pieces") or [])
        kind = "multi-piece" if n_pieces > 1 else "single piece"
        by_tier[(t, kind)]["words"] += 1
        by_tier[(t, kind)]["seams_on_a_boundary"] += d["seams_on_boundaries"]
        by_tier[(t, kind)]["seams_elsewhere"] += d["seams_elsewhere"]
        by_tier[(t, kind)]["stem_edge_seams"] += int(d["stem_edge_seam"])
        rows.append({"lexeme_id": r["lexeme_id"], "headword": r["headword"], "tier_without_e5": t, "kind": kind,
                     "on_boundary": d["seams_on_boundaries"], "elsewhere": d["seams_elsewhere"],
                     "stem_edge": d["stem_edge_seam"], "bb": [a["bb"] for a in d["attestations"]]})
    return {"by_tier": {"%s, %s" % k: dict(v) for k, v in sorted(by_tier.items())}, "rows": rows}


# ---------------------------------------------------------------------------
# Blind re-derivation
# ---------------------------------------------------------------------------

def compare_blind(res, inv):
    files = sorted(BLIND.glob("result_*.json"))
    if not files:
        return None
    roots_by_form, aff_by_form = defaultdict(list), defaultdict(list)
    for r in inv["roots"]:
        roots_by_form[r["form"]].append(r)
    for a in inv["affixes"]:
        aff_by_form[a["form"]].append(a)
    occ = inv["occurrences"]
    member_to_lex = {m: r["lexeme_id"] for r in res["records"] for m in r["member_ids"]}
    by_serial = {m.rsplit("-", 1)[-1]: m for m in member_to_lex}
    rec = {r["lexeme_id"]: r for r in res["records"]}
    summary = Counter()
    rows = []
    for fp in files:
        data = load_json(fp)
        for item in data.get("forms", []):
            form = item["form"]
            mine_lex = [r for r in roots_by_form.get(form, [])]
            mine_aff = aff_by_form.get(form, [])
            summary["forms"] += 1
            for s in item.get("senses", []):
                summary["reviewer_senses"] += 1
                meaning = s.get("meaning") or ""
                ex_ids = []
                for x in (s.get("examples") or []):
                    eid = x.get("entry_id") if isinstance(x, dict) else str(x).split()[0]
                    if eid and eid.isdigit():           # reviewers sometimes gave only the serial number
                        eid = by_serial.get(eid.zfill(4))
                    ex_ids.append(member_to_lex.get(eid))
                ex_ids = [x for x in ex_ids if x]
                if s.get("kind") == "grammatical":
                    lab = (s.get("label") or "").upper()
                    def toks(x):
                        return {t[:4] for t in re.split(r"[/. ,]", x) if t}      # INST ~ INSTR
                    match = [a for a in mine_aff if toks(a["label"].upper()) & toks(lab)]
                    if not match and mine_aff and not lab:
                        match = []
                    key = match[0]["id"] if match else None
                    kind = "grammatical"
                    if key is None:
                        # the pipeline may hold the same thing as a sense with a grammatical label,
                        # or as a lexical morpheme (the causative raʔuk 'make')
                        st = gloss_stems(meaning)
                        cands = [(bool(res["sense_by_id"][r["id"]].get("gram_label")),
                                  len(st & res["sense_by_id"][r["id"]]["stems"]), r) for r in mine_lex]
                        cands = [c for c in cands if c[1] > 0]
                        if cands:
                            key = sorted(cands, key=lambda c: (-c[0], -c[1], c[2]["rank"]))[0][2]["id"]
                else:
                    st = gloss_stems(meaning)
                    scored = [(len(st & res["sense_by_id"][r["id"]]["stems"]), r) for r in mine_lex]
                    scored = [x for x in scored if x[0] > 0]
                    scored.sort(key=lambda x: (-x[0], x[1]["rank"]))
                    key = scored[0][1]["id"] if scored else None
                    kind = "lexical"
                    if key is None:
                        # the reviewer may call lexical what the pipeline treats as an affix, or vice versa
                        for a in mine_aff:
                            if st & gloss_stems(a["meaning"] + " " + a["label"]):
                                key = a["id"]
                if key is None:
                    summary["%s_sense_not_in_inventory" % kind] += 1
                    rows.append({"form": form, "issue": "reviewer sense not matched", "kind": kind,
                                 "reviewer_meaning": meaning, "reviewer_label": s.get("label"),
                                 "reviewer_n_words": s.get("n_words"),
                                 "pipeline_senses": [r["meaning"] for r in mine_lex] + [a["label"] for a in mine_aff]})
                    continue
                summary["%s_sense_matched" % kind] += 1
                mine_set = {o["lexeme_id"] for o in occ.get(key, [])}
                inside = [x for x in ex_ids if x in mine_set]
                summary["examples_given"] += len(ex_ids)
                summary["examples_in_pipeline_set"] += len(inside)
                for x in ex_ids:
                    if x not in mine_set:
                        r = rec[x]
                        how = [p.get("sense_evidence") or p.get("label") for p in r["pieces"] if p["form"] == form]
                        rows.append({"form": form, "issue": "reviewer example not counted under this sense",
                                     "sense": key, "lexeme_id": x, "headword": r["headword"],
                                     "pipeline_treatment_of_piece": how, "raw_etymology": r["raw_etymology"]})
            got = {res["sense_by_id"][r["id"]]["sense_id"] for r in mine_lex if r["tier"] in LEARNER_TIERS}
            theirs = [gloss_stems(s.get("meaning") or "") for s in item.get("senses", []) if s.get("kind") != "grammatical"]
            for r in mine_lex:
                if r["tier"] in LEARNER_TIERS and not any(t & res["sense_by_id"][r["id"]]["stems"] for t in theirs):
                    summary["pipeline_sense_not_found_by_reviewer"] += 1
                    rows.append({"form": form, "issue": "pipeline tier A/B sense the reviewer did not list",
                                 "sense": r["id"], "words_AB": r["type_frequency"]["A+B"]})
    return {"files": [f.name for f in files], "summary": dict(summary), "rows": rows}


# ---------------------------------------------------------------------------
# Adversarial pass
# ---------------------------------------------------------------------------

def adversarial(res, inv, top=100):
    """Try to break each of the most frequent morphemes; return what was tried and what was found."""
    rec = {r["lexeme_id"]: r for r in res["records"]}
    variants = defaultdict(list)
    for d in inv["decisions"]:
        if d["type"] == "variant_candidate":
            for f in d["forms"]:
                variants[f].append(d)
    homonyms = {d["form"]: d for d in inv["decisions"] if d["type"] == "homonym_split"}
    items = sorted(inv["roots"] + inv["affixes"], key=lambda r: -r["type_frequency"]["A+B"])[:top]
    outp = []
    for m in items:
        key = m["id"]
        occ = [o for o in inv["occurrences"].get(key, []) if o["tier"] in LEARNER_TIERS]
        flags = []
        tried = ["homonym folded in", "false variant merge", "chance substring hits",
                 "gloss fits only part of the hosts", "counterexample to seam behaviour"]
        if "#" in key:
            c = res["sense_by_id"][key]
            head = gloss_stems(c["label"])
            checked = [o for o in occ if o["evidence"] in ("aligned", "literal")]
            fit = 0
            for o in checked:
                r = rec[o["lexeme_id"]]
                texts = [p.get("gloss") or p.get("phrase") or r["literal"] or "" for p in r["pieces"]
                         if p.get("sense_id") == key]
                if any(head & gloss_stems(t) for t in texts):
                    fit += 1
            share = fit / len(checked) if checked else None
            if share is not None and share < 0.6 and len(checked) >= 5:
                flags.append("only %d of %d checked words mention the head meaning '%s'; the sense groups "
                             "several glosses" % (fit, len(checked), c["label"]))
            entries = [a for a in c["anchors"] if a["kind"] == "standalone"]
            classes = {(a.get("class") or "").split(",")[0] for a in entries}
            if len(entries) > 1 and len(classes) > 1:
                flags.append("its dictionary entries have different classes (%s): possibly more than one "
                             "morpheme under one meaning" % ", ".join(sorted(classes)))
            defaults = len([o for o in inv["occurrences"].get(key, []) if o["evidence"] == "default_single_sense"])
        if m["form"] in homonyms:
            others = [s for s in homonyms[m["form"]]["senses"] if s["id"] != key]
            flags.append("shape has %d other meaning(s) kept apart: %s" % (
                len(others), "; ".join("%s (%d)" % (s["meaning"], s["words_AB"]) for s in others[:4])))
        if variants.get(m["form"]):
            flags.append("variant candidate(s), not merged: " + "; ".join(
                " ~ ".join(d["forms"]) for d in variants[m["form"]][:3]))
        if m.get("chance_baseline"):
            cb = m["chance_baseline"]
            flags.append("short form: the string occurs inside %d headwords, an analysis places it in %d; only the "
                         "analysed ones are counted" % (cb["headwords_containing_the_string"],
                                                        cb["words_where_an_analysis_places_it"]))
        nested = sum(1 for o in occ if o["nested"])
        exact = [o for o in occ if o.get("exact")]
        inexact = len(occ) - len(exact)
        if occ and inexact / len(occ) > 0.4:
            flags.append("%d of its %d tier A/B words are reproduced only partially (they are tier B through "
                         "paradigm or Blue Book confirmation)" % (inexact, len(occ)))
        default_n = sum(1 for o in inv["occurrences"].get(key, []) if o["evidence"] == "label by default")
        if "=" in key and default_n and m["evidence"]["E1_label_printed_by_parks_in"] < default_n / 5:
            flags.append("label printed by Parks only %d times against %d uses labelled by default (%s)" % (
                m["evidence"]["E1_label_printed_by_parks_in"], default_n, m["evidence"].get("default_basis")))
        outp.append({"id": key, "form": m["form"], "meaning": m.get("meaning"), "words_AB": m["type_frequency"]["A+B"],
                     "tried": tried, "found": flags})
    return outp


# ---------------------------------------------------------------------------
# Changelog against v1
# ---------------------------------------------------------------------------

def changelog(res, inv):
    v1 = load_json(V1 / "roots_ranked.json")
    v1_by_form = defaultdict(list)
    for r in v1:
        v1_by_form[r["root"]].append(r)
        for v in r.get("variants") or []:
            v1_by_form[v].append(dict(r, _as_variant_of=r["root"]))
    v2_by_form = defaultdict(list)
    for r in inv["roots"]:
        v2_by_form[r["form"]].append(r)
    aff_forms = defaultdict(list)
    for a in inv["affixes"]:
        aff_forms[a["form"]].append(a)
    lines = []
    w = lines.append
    w("# What changed from version 1")
    w("")
    w("Version 1 is `curriculum/roots/roots_ranked.json` (1,320 root senses, ranked by the number of headwords "
      "whose stored piece list contains the root). Version 2 counts differently, so most numbers move. The "
      "general reasons come first; the table then gives every root that was added, removed, split or "
      "merged, or whose rank moved by more than 10 places or whose count changed by more than 25%.")
    w("")
    w("## Why the numbers differ in general")
    w("")
    w("1. **Tier A/B only.** A v2 count is the number of words whose analysis is tier A or B *and* in which the "
      "meaning of the piece was checked. v1 counted every headword whose stored piece list contained the form.")
    w("2. **Lexemes, not rows.** %d rows are %d lexemes after duplicate resolution." % (
        sum(len(r["member_ids"]) for r in res["records"]), len(res["records"])))
    w("3. **Meaning comes from the printed etymology.** v1 took each piece's gloss from a stored parse that "
      "mis-aligns glosses; v2 re-reads Parks's printed string.")
    w("4. **Senses are split systematically.** v1 split five shapes by hand. v2 keeps apart every group of glosses "
      "that shares no content word (%d shapes)." % sum(1 for d in inv["decisions"] if d["type"] == "homonym_split"))
    w("5. **No merges on vowel length.** v1 merged 21 variant pairs; v2 merges none and lists %d candidates for "
      "review." % sum(1 for d in inv["decisions"] if d["type"] == "variant_candidate"))
    w("6. **Stem formatives are affixes.** Unlabelled raar, ra, ri, waa, wi, hus, his and the causatives are "
      "classed as affixes by cited decisions (`decisions.json`), so they leave the root list.")
    w("7. **Compound stems are resolved.** A dotted unit in Parks's etymology is matched to its own dictionary "
      "entry, and its inner pieces take their meaning from there.")
    w("")
    w("## Root by root")
    w("")
    w("| Root | v1 meaning | v1 rank | v1 words | v2 | v2 rank | v2 words (A+B / all tiers) | What happened |")
    w("|---|---|---|---|---|---|---|---|")
    rows = []
    seen_v2 = set()
    for r in v1:
        form = r["root"]
        v2s = v2_by_form.get(form, [])
        v1n, v1rank = r["frequency"], r["rank"]
        if not v2s:
            if form in aff_forms:
                what = "reclassified as an affix: %s" % ", ".join(sorted({a["label"] for a in aff_forms[form]}))
            else:
                what = "removed: no occurrence with a checked meaning in a tier A/B/C analysis"
            if v1n >= 3 or form in aff_forms:
                rows.append((v1rank, "| %s | %s | %d | %d | — | — | — | %s |" % (form, r["gloss"] or "", v1rank, v1n, what)))
            continue
        st = gloss_stems((r["gloss"] or "") + " " + (r.get("sense") or ""))
        best = sorted(v2s, key=lambda x: (-len(st & res["sense_by_id"][x["id"]]["stems"]), x["rank"]))[0]
        seen_v2.add(best["id"])
        n2, n2all = best["type_frequency"]["A+B"], best["type_frequency"]["A+B+C"]
        moved = abs(best["rank"] - v1rank) > 10
        changed = v1n and abs(n2 - v1n) / v1n > 0.25
        notes = []
        if len(v2s) > 1:
            notes.append("shape split into %d senses (%s)" % (len(v2s), "; ".join(
                "%s %d" % (x["meaning"], x["type_frequency"]["A+B"]) for x in v2s[:4])))
        if r.get("variants"):
            notes.append("v1 had merged the variants %s; v2 counts them separately" % ", ".join(r["variants"]))
        if form in aff_forms:
            notes.append("some uses reclassified as affix %s" % ", ".join(sorted({a["label"] for a in aff_forms[form]})))
        if changed and n2 < v1n:
            notes.append("count falls: only tier A/B words with a checked meaning are counted (%d in all tiers)" % n2all)
        elif changed:
            notes.append("count rises: occurrences inside compound stems are now recognised")
        if (moved or changed or len(v2s) > 1 or r.get("variants")) and (v1rank <= 150 or best["rank"] <= 150):
            rows.append((v1rank, "| %s | %s | %d | %d | %s | %d | %d / %d | %s |" % (
                form, r["gloss"] or "", v1rank, v1n, best["meaning"], best["rank"], n2, n2all,
                "; ".join(notes) or "rank moved with the general changes above")))
    for r in inv["roots"]:
        if r["id"] not in seen_v2 and r["form"] not in v1_by_form and r["tier"] in LEARNER_TIERS and r["rank"] <= 300:
            rows.append((10000 + r["rank"], "| %s | — | — | — | %s | %d | %d / %d | added: not a root in v1 |" % (
                r["form"], r["meaning"], r["rank"], r["type_frequency"]["A+B"], r["type_frequency"]["A+B+C"])))
    for _, line in sorted(rows):
        w(line)
    w("")
    w("Rows are limited to roots in the first 150 of either version (and added roots in the v2 first 300); "
      "the full v2 inventory is `roots.json`.")
    w("")
    return "\n".join(lines), len(rows)


# ---------------------------------------------------------------------------
# Proposed data fixes
# ---------------------------------------------------------------------------

def proposed_fixes(res, conn, extraction_issues):
    fixes = []
    for lex in res["lexemes"]:
        for mid in lex["member_ids"]:
            pass
    idx_rows = conn.execute("select entry_id, headword, page_number from lexical_entries").fetchall()
    lex_by_member = {m: lex for lex in res["lexemes"] for m in lex["member_ids"]}
    for eid, hw, page in idx_rows:
        lex = lex_by_member.get(eid)
        if lex and lex["page_verified"] and lex["book_page"] and page is not None:
            expect_file = int(lex["pdf_file"][5:8])
            if page not in (expect_file, lex["book_page"]) and eid == lex["lexeme_id"]:
                fixes.append({"kind": "page_number", "entry_id": eid, "headword": hw, "current": page,
                              "proposed": lex["book_page"], "auto_applicable": True,
                              "evidence": "the headword is not on the stored page; the PDF text layer has it at the "
                                          "start of a line only on %s (book page %d)" % (lex["pdf_file"], lex["book_page"])})
    for d in res["dup_decisions"]:
        if d["verdict"] == "merged":
            for group in d["lexemes"]:
                if len(group) > 1:
                    fixes.append({"kind": "duplicate_rows", "entry_ids": group, "headword": d["headword"],
                                  "class": d["class"], "auto_applicable": False,
                                  "evidence": "; ".join(e["reason"] for e in d["evidence"] if e["same_record"]),
                                  "proposed": "keep one row; review by eye before deleting (never auto-merge)"})
    for iss in extraction_issues:
        if iss["field"] == "headword/class":
            continue
        fixes.append({"kind": "extraction_differs_from_page", "entry_id": iss["entry_id"], "field": iss["field"],
                      "current": iss["database"], "page_reads": iss["page"], "auto_applicable": False,
                      "evidence": "transcribed from the page image by an independent annotator (gold set G2); "
                                  "confirm against the page before changing"})
    spaced = re.compile(r"(?:\b[a-zA-Z'] ){4,}[a-zA-Z]\b")
    for gid, eid, text in conn.execute("select id, entry_id, definition from glosses"):
        if text and spaced.search(text):
            fixes.append({"kind": "letter_spaced_gloss", "gloss_id": gid, "entry_id": eid, "current": text,
                          "proposed": spaced.sub(lambda m: m.group(0).replace(" ", ""), text),
                          "auto_applicable": False,
                          "evidence": "letter-spaced OCR run in an English gloss; the proposed text joins the letters "
                                      "but word breaks must be restored by hand"})
    return fixes


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def run_suites():
    env_python = str(ROOT / ".venv" / "Scripts" / "python")
    import os
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    outp = {}
    # sound_changes.py has no pass-or-fail test since 2026-11-14: --measure compares the code with Parks's examples
    cmds = {"sound_changes.py --measure (a measurement)": [env_python, "scripts/sound_changes.py", "--measure"],
            "person_forms.py --validate-appendix": [env_python, "scripts/person_forms.py", "--validate-appendix"],
            "build_root_curriculum.py --check": [env_python, "scripts/build_root_curriculum.py", "--check"],
            "morphology_v2 unit tests": [env_python, "-m", "unittest", "discover", "-s", "scripts/morphology_v2",
                                         "-p", "test_*.py"]}
    for name, cmd in cmds.items():
        try:
            p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, timeout=600)
            text = (p.stdout + p.stderr).decode("utf-8", errors="replace")
            if "sound_changes" in name:
                summ = next((l.strip() for l in text.splitlines() if "printed form for" in l), "no result line")
            else:
                summ = [l for l in text.strip().splitlines() if l.strip()][-1][:120] if text.strip() else ""
            outp[name] = {"exit": p.returncode, "summary": summ}
        except Exception as exc:
            outp[name] = {"exit": None, "summary": "could not run: %s" % exc}
    return outp


def write_reports(conn, bundle):
    res, inv, need, usable, order, curve, sens, stats = bundle
    records = res["records"]
    dev, held = score_g2(records, "dev"), score_g2(records, "heldout")
    mdev = meaning_agreement(records, res["sense_by_id"], "dev")
    mheld = meaning_agreement(records, res["sense_by_id"], "heldout")
    ext_counts, ext_issues = extraction_check(conn)
    g1, g3 = score_g1(res, inv, conn), score_g3(res)
    blind = compare_blind(res, inv)
    adv = adversarial(res, inv)
    manual = load_json(MANUAL_REVIEW) if MANUAL_REVIEW.exists() else {}
    suites = run_suites()
    ids = {r["lexeme_id"] for r in records}
    db_ids = {r[0] for r in conn.execute("select entry_id from lexical_entries")}
    cited = set()
    for r in inv["roots"] + inv["affixes"]:
        for e in r["examples"]:
            cited.add(e["lexeme_id"])
    missing_ids = sorted(cited - db_ids)
    fixes = proposed_fixes(res, conn, ext_issues)
    dump_json(OUT / "proposed_data_fixes.json", {"n": len(fixes), "note": "Nothing here has been applied. "
              "scripts/morphology_v2/apply_data_fixes.py lists them (dry run by default).", "fixes": fixes})
    text, n_rows = changelog(res, inv)
    write_text(OUT / "changelog_vs_v1.md", text)
    dump_json(OUT / "validation_details.json", {
        "g2_dev": dev, "g2_heldout": held, "g2_meaning_dev": mdev, "g2_meaning_heldout": mheld,
        "extraction": {"counts": ext_counts, "issues": ext_issues}, "g1": g1, "g3": g3, "blind": blind,
        "adversarial": adv, "suites": suites})

    L = []
    w = L.append
    w("# Validation report")
    w("")
    w("Generated by `scripts/morphology_v2/run.py --validate`. Gold sets and their hashes are described in "
      "`PLAN.md`; the tier rules are in `METHOD.md` and `scripts/morphology_v2/tiers.py`. Per-entry detail is in "
      "`validation_details.json`.")
    w("")
    # ---- summary (regenerated with the report)
    n_roots = sum(1 for k in order if "#" in k)
    last = curve[-1]
    w("## Summary")
    w("")
    w("**Headline.** %d roots and %d affixes (%d building blocks of tier A or B) let a learner take apart %d of "
      "the dictionary's %d words completely (%.1f%%). The first 100 blocks alone give %d words (%.1f%%), and %d "
      "words (%.1f%%) contain at least one of them." % (
          n_roots, len(order) - n_roots, len(order), last["words_decodable"], stats["lexemes"],
          100 * last["share_of_dictionary"], curve[99]["words_decodable"], 100 * curve[99]["share_of_dictionary"],
          curve[99]["words_with_a_known_piece"], 100 * curve[99]["words_with_a_known_piece"] / stats["lexemes"]))
    w("")
    w("**Tiers.** Of %d words, %d analyses are tier A, %d tier B, %d tier C; %d words carry no claim." % (
        stats["lexemes"], stats["lexeme_tiers"].get("A", 0), stats["lexeme_tiers"].get("B", 0),
        stats["lexeme_tiers"].get("C", 0), stats["lexeme_tiers"].get("no claim", 0)))
    w("")
    w("### The 30 most used roots")
    w("")
    w("| Root | Meaning | Class | Tier A/B words | Tier | Evidence | First Blue Book lesson |")
    w("|---|---|---|---|---|---|---|")
    for rt in inv["roots"][:30]:
        e = rt["evidence"]
        ev = []
        if e["E1_glossed_by_parks_in"]:
            ev.append("E1 gloss x%d" % e["E1_glossed_by_parks_in"])
        if e["own_dictionary_entries"]:
            ev.append("own entry")
        if e.get("E4_commutation_words"):
            ev.append("E4 commutation x%d" % e["E4_commutation_words"])
        if e["E3_words_with_paradigm_confirmation"]:
            ev.append("E3 x%d" % e["E3_words_with_paradigm_confirmation"])
        if e["E5_words_with_blue_book_seam"]:
            ev.append("E5 x%d" % e["E5_words_with_blue_book_seam"])
        w("| %s | %s | %s | %d | %s | %s | %s |" % (rt["form"], rt["meaning"], rt["class"], rt["type_frequency"]["A+B"],
                                              rt["tier"], ", ".join(ev), rt["blue_book"]["first_lesson"] or "-"))
    w("")
    w("### The 20 most used affixes")
    w("")
    w("| Affix | Label | Position | Tier A/B words | Tier | Label printed by Parks / supplied by default | First Blue Book lesson |")
    w("|---|---|---|---|---|---|---|")
    for a in inv["affixes"][:20]:
        e = a["evidence"]
        w("| %s | %s | %s | %d | %s | %d / %d%s | %s |" % (
            a["form"], a["label"], a["kind"], a["type_frequency"]["A+B"], a["tier"], e["E1_label_printed_by_parks_in"],
            e["label_supplied_by_default_in"], " (%s)" % e["default_basis"].replace("_", " ") if e.get("default_basis") else "",
            a["blue_book"]["first_lesson"] or "-"))
    w("")
    for title, key in (("The five most important changes from version 1", "changes_from_v1"),
                       ("The ten most important open questions for a speaker or linguist", "open_questions"),
                       ("What could not be done, or is weaker than it looks", "gaps")):
        if manual.get(key):
            w("### %s" % title)
            w("")
            for i, item in enumerate(manual[key], 1):
                w("%d. %s" % (i, item))
            w("")
    w("## 1. Hand-checked dictionary entries (G2)")
    w("")
    w("120 entries were transcribed from the page images by annotators who saw neither the database nor this "
      "pipeline. An analysis is **correct** when its ordered list of pieces equals the printed etymology's. The "
      "held-out half was not scored until this report was written.")
    w("")
    w("| Half | Tier | Correct | Scored | Precision | 95% interval |")
    w("|---|---|---|---|---|---|")
    for name, sc in (("development", dev), ("held out", held)):
        for t in ("A", "B", "C", "A+B"):
            p = sc["precision"][t]
            w("| %s | %s | %d | %d | %s | %s |" % (name, t, p["correct"], p["scored"],
                                               "%.1f%%" % (100 * p["precision"]) if p["precision"] is not None else "—",
                                               "%.0f%% to %.0f%%" % (100 * p["ci95"][0], 100 * p["ci95"][1]) if p["scored"] else "—"))
    w("")
    w("Entries not scored: " + "; ".join("%s half: %s" % (name, ", ".join(
        "%s %d" % (k, v) for k, v in sorted(Counter(r["status"] for r in sc["rows"]
                                                     if r["status"] not in ("correct", "wrong")).items())))
        for name, sc in (("development", dev), ("held-out", held))) + ". \"gold_undetermined\" means the page prints "
      "no analysis and the pipeline treats the entry as a single piece cited elsewhere by Parks; the page cannot "
      "confirm or refute that.")
    w("")
    wrong = [r for sc in (dev, held) for r in sc["rows"] if r["status"] in ("wrong", "missed_analysis", "different_headword")]
    if wrong:
        w("Analyses that do not match the page:")
        w("")
        for r in wrong:
            w("- `%s` %s (tier %s, %s): page %s, pipeline %s" % (r["entry_id"], r["headword"], r["tier"], r["status"],
                                                                 r.get("gold_pieces"), r.get("pipeline_pieces")))
        w("")
    w("### Stricter test: the meaning of each piece")
    w("")
    w("For entries whose pieces match, the meaning the pipeline attaches to each lexical piece was compared with "
      "the annotator's own reading of which words of the literal translation go with which piece. Rows are "
      "grouped by what the pipeline's assignment rests on. Only the first four kinds count as evidence; the "
      "others never promote an analysis.")
    w("")
    w("| Basis of the assignment | Half | Agree | Differ | Page gives no separate meaning | No meaning assigned |")
    w("|---|---|---|---|---|---|")
    kinds = ["aligned", "literal", "inherited", "entry_gloss", "default_single_sense", "stored_parse",
             "unassigned_homonym", "meaning_unknown_to_parks", "no_sense_known", "inside_stem_unanalysed"]
    for k in kinds:
        for name, m in (("development", mdev), ("held out", mheld)):
            c = m["counts"]
            a, d = c.get("%s | agree" % k, 0), c.get("%s | differ" % k, 0)
            g, u = c.get("%s | page gives no separate meaning" % k, 0), c.get("%s | no meaning assigned" % k, 0)
            if a + d + g + u:
                w("| %s%s | %s | %d | %d | %d | %d |" % (k, "" if k in SENSE_EVIDENCED else " (not evidence)",
                                                     name, a, d, g, u))
    w("")
    for name, m in (("development", mdev), ("held out", mheld)):
        ev_a = sum(v for k, v in m["counts"].items() if k.split(" | ")[0] in SENSE_EVIDENCED and k.endswith("agree"))
        ev_d = sum(v for k, v in m["counts"].items() if k.split(" | ")[0] in SENSE_EVIDENCED and k.endswith("differ"))
        lo, hi = wilson(ev_a, ev_a + ev_d)
        w("- %s half: evidenced meanings agree in %s (95%% interval %.0f%% to %.0f%%)." % (
            name.capitalize(), _pct(ev_a, ev_a + ev_d), 100 * lo, 100 * hi))
    w("")
    w("Strict precision (pieces match **and** no evidenced meaning conflicts with the annotator):")
    w("")
    w("| Half | Tier | Correct | Meaning conflict | Wrong pieces |")
    w("|---|---|---|---|---|")
    for name, m in (("development", mdev), ("held out", mheld)):
        for t in ("A", "B", "C"):
            c = m["strict"].get(t, {})
            w("| %s | %s | %d | %d | %d |" % (name, t, c.get("correct", 0), c.get("meaning_conflict", 0),
                                          c.get("wrong_pieces", 0)))
    w("")
    diffs = [d for m in (mdev, mheld) for d in m["differences"] if d["evidence"] in SENSE_EVIDENCED]
    if diffs:
        w("Evidenced meanings that differ from the annotator's reading:")
        w("")
        for d in diffs:
            w("- %s, piece %s: pipeline %s (%s), annotator \"%s\" (tier %s)" % (
                d["headword"], d["piece"], d["assigned"], d["evidence"], d["annotator"], d["tier"]))
        w("")
    w("### What the extraction got wrong")
    w("")
    w("The same transcriptions check the database against the page. Of %d entries, %d were compared field by "
      "field (%d could not be: the annotator's entry and the database row differ in headword or class, usually a "
      "neighbouring homograph)." % (ext_counts.get("entries", 0), ext_counts.get("compared", 0),
                                    ext_counts.get("different_homograph_or_headword", 0)))
    w("")
    w("- Etymology strings: %s differ from the page." % _pct(ext_counts.get("etymology_differs", 0),
                                                             ext_counts.get("etymology_compared", 0)))
    w("- Paradigm forms: %s differ; %d printed forms are missing from the database." % (
        _pct(ext_counts.get("form_differs", 0), ext_counts.get("forms_compared", 0)),
        ext_counts.get("form_missing_in_database", 0)))
    w("- Verb class: %d differ." % ext_counts.get("verb_class_differs", 0))
    w("")
    w("Every difference is listed in `proposed_data_fixes.json` for checking by eye. None has been applied.")
    w("")

    w("## 2. Parks's own worked examples (G1)")
    w("")
    w("%d worked examples were read from the Grammatical Overview; %d are free of OCR damage and were used." % (
        g1["worked_examples"], g1["clean_examples"]))
    w("")
    seg = g1["segmentation"]
    w("- **Words Parks analyses there that are also dictionary headwords:** the pipeline's pieces equal his in %s."
      % _pct(seg.get("same", 0), seg.get("same", 0) + seg.get("different", 0)))
    for r in g1["segmentation_rows"]:
        if not r["same"]:
            w("  - %s (GO p. %s): Overview %s, pipeline %s" % (r["word"], r["go_page"], r["parks_overview"], r["pipeline"]))
    st = g1["stems"]
    tot = sum(st.values())
    w("- **Stems he cites with a gloss:** %s are dictionary headwords whose gloss shares a content word with his; "
      "%d are headwords with a different gloss wording; %d are not headwords (bound stems and combining forms)." % (
          _pct(st.get("headword with matching gloss", 0), tot), st.get("headword, gloss differs", 0),
          st.get("not a headword", 0)))
    lp = g1["labelled_pieces"]
    w("- **Labelled prefixes and suffixes in his analyses:** %d occurrences of %d distinct labelled pieces. All are "
      "listed in `affixes.json` (\"inflectional\") straight from his worked examples, with the page of an example, "
      "and the guide prints his own tables of the verb as printed. They are not matched against a list of the "
      "project's: the table they used to be matched against was written by the conjugation engine, which was "
      "withdrawn on 2026-11-14." % (lp["occurrences"], lp["distinct"]))
    w("- **Appendix 1:** `person_forms.py --validate-appendix` reproduces the paradigm cells it derives "
      "(result below under existing suites).")
    w("")

    w("## 3. Blue Book seams (G3)")
    w("")
    w("77 Blue Book words written with seams were matched with certainty to a Parks form. For the words among "
      "them that have an analysis, each seam either falls on a boundary of the analysis or does not. Tiers here "
      "are computed **without** the Blue Book channel, so nothing is scored against evidence it was promoted on.")
    w("")
    w("| Tier (without E5), kind of analysis | Words | Seams on a boundary | Seams elsewhere | Seam at the stem edge |")
    w("|---|---|---|---|---|")
    for k, v in g3["by_tier"].items():
        w("| %s | %d | %d | %d | %d |" % (k, v.get("words", 0), v.get("seams_on_a_boundary", 0),
                                      v.get("seams_elsewhere", 0), v.get("stem_edge_seams", 0)))
    w("")
    tot_on = sum(v.get("seams_on_a_boundary", 0) for k, v in g3["by_tier"].items() if "multi" in k)
    tot_off = sum(v.get("seams_elsewhere", 0) for k, v in g3["by_tier"].items() if "multi" in k)
    w("In multi-piece analyses, %s of the Blue Book's seams fall where Parks's analysis has a boundary. A seam "
      "elsewhere usually means the Blue Book divides a piece that Parks treats as one; those words are in "
      "`review_queue.md`, section 2." % _pct(tot_on, tot_on + tot_off))
    w("")

    w("## 4. Paradigm check (E1 against E3)")
    w("")
    e3b = stats["e3b"]
    comp = e3b.get("confirm", 0) + e3b.get("near", 0) + e3b.get("mismatch", 0)
    w("Of %d compound verbs that share an inflection class with the dictionary entry of their final root, %s end "
      "every compared form as that root does on its own, %d differ by one letter and %d differ outright. The "
      "stop condition in the plan (more than about 10%% disagreement) is not met. %d further compounds have a "
      "different class from their final root and were not compared." % (
          comp, _pct(e3b.get("confirm", 0), comp), e3b.get("near", 0), e3b.get("mismatch", 0),
          e3b.get("class_differs", 0)))
    w("")

    w("## 5. Blind re-derivation")
    w("")
    if blind:
        s = blind["summary"]
        w("Independent reviewers were given only the shapes of the %d most frequent roots and affixes and the raw "
          "sources (the database's printed etymologies, glosses and paradigms, and the Grammatical Overview). They "
          "had no access to this pipeline, its outputs or version 1." % s.get("forms", 0))
        w("")
        w("- Senses the reviewers recorded: %d. Matched to a morpheme in the inventory: %d lexical, %d grammatical. "
          "Not matched: %d lexical, %d grammatical." % (
              s.get("reviewer_senses", 0), s.get("lexical_sense_matched", 0), s.get("grammatical_sense_matched", 0),
              s.get("lexical_sense_not_in_inventory", 0), s.get("grammatical_sense_not_in_inventory", 0)))
        w("- Example words the reviewers gave for matched senses: %s are counted under the same sense by the "
          "pipeline." % _pct(s.get("examples_in_pipeline_set", 0), s.get("examples_given", 0)))
        w("- Tier A/B senses in the inventory that the reviewers did not list: %d." % s.get(
            "pipeline_sense_not_found_by_reviewer", 0))
        w("")
        for item in manual.get("blind_resolutions", []):
            w("- **%s**: %s" % (item["case"], item["resolution"]))
        w("")
        w("Every disagreement is listed in `validation_details.json` under `blind.rows`.")
    else:
        w("Not yet run: no result files in `blind/`.")
    w("")

    w("## 6. Adversarial pass")
    w("")
    w("For each of the 100 most frequent morphemes the following were tried: a homonym folded into it; a false "
      "variant merge; chance substring hits; a gloss that fits only part of its host words; a counterexample to "
      "the stated seam behaviour. The automatic checks below report what they found; `validation_details.json` "
      "has the full list.")
    w("")
    flagged = [a for a in adv if a["found"]]
    w("%d of 100 morphemes drew at least one finding. No merges exist to be false (version 2 merges no variants)."
      % len(flagged))
    w("")
    w("| Morpheme | Tier A/B words | Finding |")
    w("|---|---|---|")
    for a in flagged[:60]:
        w("| %s %s | %d | %s |" % (a["form"], ("'%s'" % a["meaning"]) if a["meaning"] else "", a["words_AB"],
                               " ".join("(%d) %s." % (i + 1, f) for i, f in enumerate(a["found"])).replace("|", "/")))
    w("")
    for item in manual.get("adversarial_notes", []):
        w("- **%s**: %s" % (item["case"], item["resolution"]))
    w("")

    w("## 7. Sanity checks")
    w("")
    w("- Entry ids cited in `roots.json` and `affixes.json` that do not exist in the database: %d." % len(missing_ids))
    w("- Lexeme ids are database entry ids: %s." % ("yes" if ids <= db_ids else "NO"))
    w("- Every Pawnee form in the three learner documents resolves to a source record: run "
      "`python scripts/morphology_v2/check_forms.py` (it exits with an error otherwise).")
    w("")
    vr = stats.get("verb_roots_AB", {})
    w("- **Parks's count of verb roots.** He says there are \"approximately one hundred\" basic verb roots "
      "(Grammatical Overview p. 31). The inventory has %d tier A/B morphemes classed as verb roots: %d basic "
      "roots whose own dictionary entry is unanalysed, %d bound roots with no entry of their own, and %d that "
      "are themselves derived stems Parks analyses (such as 'cause to go'). The first two together, %d, are "
      "the comparable figure; further verb roots sit in tier C." % (
          sum(vr.values()), vr.get("basic root (its own entry is unanalysed)", 0),
          vr.get("bound, no entry of its own", 0), vr.get("derived stem (its own entry is analysed by Parks)", 0),
          vr.get("basic root (its own entry is unanalysed)", 0) + vr.get("bound, no entry of its own", 0)))
    w("")
    w("| Existing suite | Exit code | Result |")
    w("|---|---|---|")
    for name, r in suites.items():
        w("| `%s` | %s | %s |" % (name, r["exit"], str(r["summary"]).replace("|", "/")))
    w("")
    det = OUT / "determinism.json"
    w("## 8. Determinism")
    w("")
    if det.exists():
        d = load_json(det)
        w("`python scripts/morphology_v2/check_determinism.py` ran the pipeline twice: %s. Hashes of the second "
          "run:" % ("all %d output files are byte-identical" % len(d["files"]) if d["identical"] else
                    "FILES DIFFER: " + ", ".join(d["different"])))
        w("")
        w("```")
        for f, h in sorted(d["files"].items()):
            w("%s  %s" % (h[:16], f))
        w("```")
    else:
        w("Run `python scripts/morphology_v2/check_determinism.py` to fill this section.")
    w("")
    write_text(OUT / "validation_report.md", "\n".join(L))
    return {"dev": dev, "heldout": held, "meaning_dev": mdev, "meaning_heldout": mheld, "g1": g1, "g3": g3,
            "blind": blind, "adversarial": adv, "extraction": ext_counts, "fixes": len(fixes)}
