#!/usr/bin/env python3
"""
Stage 7a: one list of proposed fixes, and a page for reviewing them by eye
==========================================================================

Gathers what the stages found into reports/source_audit_2026-11/proposed_fixes.jsonl:
one line per proposed change, with the stored value, what is printed, the
page, the grade of the evidence, a severity, and, where it can be worked out
safely, the value to store instead.

    python scripts/source_audit/build_report.py            # proposed_fixes.jsonl and audit_numbers.json
    python scripts/source_audit/build_report.py --review   # also work/review.html with a crop of the page beside each fix

Nothing here changes the database or the JSON. apply_fixes.py does that, for
the lines a person has approved.

"proposed_value" is filled only where the correction is unambiguous (a letter,
an accent, a missing vowel in a single form). Where a person has to decide
(a hyphen at a line end that may be real, text the database lacks, a class the
project changed on purpose) it is null and "needs" says what is needed.
"""
import argparse
import collections
import html
import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chartable  # noqa: E402
import compare_core as cc  # noqa: E402
import state  # noqa: E402

OUT = state.OUT
LETTER_KINDS = {"letters", "accent", "vowel-length", "glottal-stop", "printed-has-more", "stored-has-more", "length-mark-for-accent",
                "citation-standin", "lax-i-symbol", "capital", "stored-is-part-of-a-printed-word"}
SKIRI = ("headword", "phonetic_form", "additional_form", "form", "example.skiri", "cognate.form", "etymology")


def base_field(field):
    return re.sub(r"\[.*\]", "", field)


def index_of(field):
    m = re.search(r"\[(\d+)\]", field)
    return int(m.group(1)) if m else None


def s2e_target(d):
    f, n = base_field(d["field"]), index_of(d["field"])
    return {
        "headword": ("lexical_entries", "headword / stem_preverb"), "phonetic_form": ("lexical_entries", "phonetic_form"),
        "grammatical_class": ("lexical_entries", "grammatical_class / verb_class"), "page_number": ("lexical_entries", "page_number"),
        "column_position": ("lexical_entries", "column_position"),
        "additional_form": ("lexical_entries", "additional_forms, item %s" % n), "additional_form_type": ("lexical_entries", "additional_forms, item %s" % n),
        "gloss": ("glosses", "definition, sense %s" % n), "gloss_usage": ("glosses", "usage_notes, sense %s" % n),
        "etymology": ("etymology", "raw_etymology"), "etymology_literal": ("etymology", "literal_translation"),
        "cognate.form": ("cognates", "form, cognate %s" % n), "form": ("paradigmatic_forms", "skiri_form, form %s" % n),
        "example.skiri": ("examples", "skiri_text, example %s" % n), "example.english": ("examples", "english_translation, example %s" % n),
        "(printed text)": ("(not stored)", ""), "(entry)": ("lexical_entries", "(whole entry)"),
    }.get(f, ("?", f))


def s2e_proposed(d):
    """(proposed value or None, what is needed if None)."""
    f, kind = base_field(d["field"]), d["kind"]
    kinds = set(kind.split("+"))
    printed = d.get("printed") or ""
    if d["grade"] == "stored-is-right":
        return None, "nothing: the stored value is right"
    if f == "column_position":
        return printed, ""
    if kind == "printed-not-stored":
        return None, "a person to add the printed text to the right field"
    if kind in ("printed-entry-not-stored", "stored-entry-not-printed"):
        return None, "a person to add or remove the entry"
    if kind == "class-differs":
        return None, "a decision: the project changed this class on purpose (N to N-KIN)"
    if kind == "bracket-note-not-stored":
        return None, "a decision on where the bracket note is to be stored"
    if kind == "stored-keeps-line-break":
        return None, "a person to say whether the hyphen at the line end is a line-break hyphen (usual) or part of the form"
    if kind == "phonetic-word-space-lost":
        return chartable.to_stored(printed), ""
    if f in SKIRI or f in ("gloss", "example.english", "etymology_literal", "gloss_usage"):
        ratio = d.get("ratio", 1.0)
        if kinds <= (LETTER_KINDS | {"spacing"}) and ratio >= 0.8 and "punctuation" not in kinds:
            value = printed
            if f == "form":
                value = re.sub(r"^\s*\d+\.\s*", "", value)
            if f == "phonetic_form":
                if not (value.startswith("[") and value.endswith("]")):
                    return None, "a person to copy the form from the crop (the comparison did not isolate it cleanly)"
                value = chartable.to_stored(value)
            if f in ("gloss", "example.english", "etymology_literal", "gloss_usage", "etymology") and kinds != {"citation-standin"}:
                return None, "a person to copy the wording from the crop"
            if abs(len(cc.skeleton(value)) - len(cc.skeleton(re.sub(r"^\s*\d+\.\s*", "", d["stored"]) if f == "form" else d["stored"]))) > 4:
                return None, "a person to copy the form from the crop (the lengths differ too much to trust the match)"
            return value, ""
    return None, "a person to look at the crop"


def gather():
    fixes = []

    def add(**kw):
        kw["id"] = "P%05d" % (len(fixes) + 1)
        fixes.append(kw)

    # ---- Skiri-to-English ----
    for line in (OUT / "s2e_graded.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["grade"] == "stored-is-right":
            continue
        table, column = s2e_target(d)
        value, needs = s2e_proposed(d)
        add(source="Skiri-to-English section", table=table, column=column, key=d.get("entry_id"), headword=d.get("headword"),
            book_page=d.get("book_page"), page_file=d.get("page_file"), field=d["field"], kind=d["kind"], family=d.get("family"),
            stored=d["stored"], printed=d["printed"], proposed_value=value, needs=needs, grade=d["grade"], severity=d["severity"],
            basis=d.get("basis") or ("crop %s read blind" % d["crop"] if d.get("crop") else ""), boxes=d.get("boxes"))
    # ---- Appendix 1 ----
    a1 = json.loads((OUT / "appendix1_differences.json").read_text(encoding="utf-8"))
    for d in a1["differences"]:
        add(source="Appendix 1", table="verb_paradigms (and extracted_data/appendix1_conjugations.json)", column="skiri_form",
            key=d["verb_paradigms_id"], headword="%s, %s, %s" % (d["verb"], d["mode"], d["person"]), book_page=d["book_page"], page_file=d["page"],
            field="skiri_form", kind="letters", family="appendix-1", stored=d["stored"], printed=d["printed"], proposed_value=d["printed"], needs="",
            grade=d["grade"], severity=1, basis="blind reading of the page" + ("; third look agrees" if d["grade"] == "confirmed" else ""),
            tile=d["id"])
    # ---- Appendix 2 ----
    add(source="Appendix 2", table="irregular_verb_roots (and extracted_data/appendix2_irregular_roots.json)", column="plural_stem", key="aah",
        headword="aah 'to be around'", book_page=539, field="plural_stem", kind="b-for-h", family="appendix-2", stored="burii-waa",
        printed="hurii-waa", proposed_value="hurii-waa", needs="", grade="confirmed", severity=1, basis="read from the page image at 2.7x")
    add(source="Appendix 2", table="irregular_verb_roots (and extracted_data/appendix2_irregular_roots.json)", column="plural_stem", key="tir",
        headword="tir 'to be together'", book_page=539, field="plural_stem", kind="b-for-h", family="appendix-2", stored="burii",
        printed="hurii", proposed_value="hurii", needs="", grade="confirmed", severity=1, basis="read from the page image at 2.7x")
    add(source="Appendix 2", table="irregular_verb_roots (and extracted_data/appendix2_irregular_roots.json)", column="singular_stem", key="tir",
        headword="tir 'to be together'", book_page=539, field="singular_stem", kind="stored-has-more", family="appendix-2", stored="tir",
        printed="(the cell is empty)", proposed_value=None, needs="a decision: store an empty singular stem, as printed", grade="confirmed",
        severity=1, basis="read from the page image at 2.7x")
    # ---- Appendix 3 ----
    for d in json.loads((OUT / "appendix3_findings.json").read_text(encoding="utf-8"))["differences"]:
        simple = len(d["printed"]) < 12
        add(source="Appendix 3", table="kinship_paradigms (and extracted_data/appendix3_kinship.json)", column=d["where"], key=d["where"],
            headword=d["where"], book_page=d["book_page"], field="kin term form", kind="letters" if simple else "printed-not-stored",
            family="appendix-3", stored=d["stored"], printed=d["printed"], proposed_value=d["printed"] if simple else None,
            needs="" if simple else "a person to add the five rows to the JSON file", grade=d["grade"], severity=d["severity"],
            basis="blind reading of the page; third look at 4x agrees")
    # ---- chapters 4 and 3 ----
    for name, source, target in (("chapter4", "Grammatical Overview (chapter 4)", "extracted_data/grammatical_overview.json"),
                                 ("chapter3", "Major Sound Changes (chapter 3)", "sound_change_rules")):
        path = OUT / ("%s_differences.json" % name)
        if not path.exists():
            continue
        for d in json.loads(path.read_text(encoding="utf-8"))["differences"]:
            if d["kind"].startswith("not-found") and "b" not in d["kind"]:
                continue
            sure = d["kind"] == "b-for-h"
            add(source=source, table=target, column=d.get("where"), key="page %s" % d.get("page", ""), headword=d["stored"],
                book_page=(28 + d["page"]) if d.get("page") else None, field="form in the stored text", kind=d["kind"], family=name,
                stored=d["stored"], printed=d["blind_reading"],
                proposed_value=(d["stored"].replace("b", "h").replace("B", "H") if sure else None),
                needs="" if sure else "a person to compare the stored word with the page (matched by likeness, not by position)",
                grade=d["grade"], severity=d["severity"], basis="blind reading of the page")
    # ---- abbreviations ----
    path = OUT / "abbreviations_differences.json"
    if path.exists():
        for d in json.loads(path.read_text(encoding="utf-8"))["differences"]:
            add(source="Abbreviations", table="morpheme_abbreviations (and extracted_data/abbreviations.json)", column=d["field"], key=d["id"],
                headword=d["abbreviation"], book_page=None, field=d["field"], kind="letters", family="abbreviations", stored=d["stored"],
                printed=d["printed_nearest"], proposed_value=None, needs="a person to copy the value from the text layer (the nearest printed stretch is shown)",
                grade=d["grade"], severity=d["severity"], basis="text layer")
    # ---- Blue Book: forms where the scan shows other letters than the stored form (accents apart) ----
    path = OUT / "bluebook_graded.json"
    if path.exists():
        for r in json.loads(path.read_text(encoding="utf-8"))["rows"]:
            if not r["verdict"].startswith("letters-differ") or "[?]" in r["read"] or r.get("stored_form_is", "").startswith("the headword"):
                continue
            # a reading much longer or shorter than the stored form means the crop was not cut at the form's edges
            if abs(len(r["read"]) - len(r["stored_form"])) > 4:
                continue
            entry = r.get("entry_id")
            add(source="Blue Book", table="blue_book_attestations" + (" and lexical_entries (the headword was made from this form)" if entry else ""),
                column="bb_skiri_form", key=entry or r.get("attestation_id"), headword=r["stored_form"], book_page=r["page"],
                field="bb_skiri_form", kind="letters (the OCR text misread the scan)", family="blue-book", stored=r["stored_form"], printed=r["read"],
                proposed_value=None, needs="a person to correct the form from the scan" + ("; the dictionary headword follows from it" if entry else ""),
                grade="blind-reading", severity=1, basis="blind reading of a crop of the scan (%s)" % r["crop"])
    # ---- English-to-Skiri (the current JSON) ----
    for line in (OUT / "e2s_differences.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["class"] != "difference":
            continue
        placeholder = d["kind"] == "not-printed-in-entry" and re.search(r"cross|n/?a|notprovided|not provided", d["stored"] or "", re.I)
        add(source="English-to-Skiri section", table="Dictionary Data/english_to_skiri_linked.json", column=d["field"], key=d.get("entry_id"),
            headword=d.get("headword"), book_page=None, page_file=d.get("page_file"), field=d["field"],
            kind="placeholder-stored-as-a-value" if placeholder else d["kind"], family="english-to-skiri", stored=d["stored"],
            printed=d.get("printed", ""), proposed_value=None,
            needs=("the placeholder to be replaced by an empty value" if placeholder else "a person, or a re-parse of the entry from the text layer"),
            grade="text-layer", severity=3 if placeholder else d["severity"], basis="text layer; the same kinds of difference were all confirmed on crops in stage 3",
            boxes=d.get("boxes"))
    return fixes


def render_evidence(fixes, folder):
    """A crop of the page for each fix that has a position. Returns {fix id: file name}."""
    import crops
    import appendix_tiles
    from appendix1_compare import row_clip
    folder.mkdir(parents=True, exist_ok=True)
    margins = {"s2e": crops.Margins("s2e"), "e2s": crops.Margins("e2s")}
    docs, files = {}, {}
    a1 = fitz.open(str(appendix_tiles.find_pdf("Appendix 1")))
    for f in fixes:
        try:
            if f["source"] == "Appendix 1":
                m = re.match(r"p(\d+)-([LR])(\d)-r(\d+)$", f["tile"])
                clip = row_clip(int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)))
                pix = a1[int(m.group(1)) - 1].get_pixmap(matrix=fitz.Matrix(3.2, 3.2), clip=clip, alpha=False)
            elif f.get("boxes") and f["source"].startswith("Skiri-to-English"):
                which = "s2e"
                regs = crops.regions(f["boxes"], margins[which])
                page, clip, lines = regs[0]
                path = crops.pdf_for(which, page)
                if path not in docs:
                    docs[path] = fitz.open(str(path))
                pix = docs[path][0].get_pixmap(matrix=fitz.Matrix(3.0, 3.0), clip=clip, alpha=False)
            else:
                continue
            name = f["id"] + ".png"
            pix.save(str(folder / name))
            files[f["id"]] = name
        except Exception as exc:                      # a crop is a convenience; never let one stop the report
            state.out("  no crop for %s: %s" % (f["id"], exc))
    return files


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1c1a;--muted:#6b675f;--line:#dcd8cf;--card:#fff;--bad:#9a2a1c;--good:#1f6a3a;--accent:#2b4f8a}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a09c93;--line:#34332f;--card:#1e1e1b;--bad:#f08a78;--good:#7fd09a;--accent:#9db8e8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:36px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
p.lead{color:var(--muted);margin:0 0 16px;max-width:75ch}.fix{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0}
.meta{color:var(--muted);font-size:13px;display:flex;gap:12px;flex-wrap:wrap}.id{font-weight:600;color:var(--accent)}
.vals{display:grid;grid-template-columns:90px 1fr;gap:2px 10px;margin:8px 0;font-size:17px;word-break:break-word}.vals span{color:var(--muted);font-size:13px;padding-top:4px}
.stored{color:var(--bad)}.printed{color:var(--good)}.needs{font-size:13px;color:var(--muted)}img{max-width:100%;border:1px solid var(--line);border-radius:4px;background:#fff;margin-top:6px}
nav a{color:var(--accent);margin-right:14px}
"""


def write_review(fixes, files, path):
    groups = collections.OrderedDict()
    for f in fixes:
        if f["severity"] > 2 or f["source"].startswith("English-to-Skiri"):
            continue
        groups.setdefault(f["source"], []).append(f)
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>Proposed fixes for review</title><style>%s</style></head><body><main>" % CSS,
             "<h1>Proposed fixes, with the page beside each</h1>",
             "<p class='lead'>Source-fidelity audit, November 2026. Every item is a place where the stored value differs from the printed "
             "page. Red is what is stored now, green is what is printed. Nothing has been changed. To approve an item, add its id to "
             "<code>reports/source_audit_2026-11/approved_fixes.txt</code>, one id per line, and run <code>scripts/source_audit/apply_fixes.py</code>.</p><nav>"]
    for g, items in groups.items():
        parts.append("<a href='#%s'>%s (%d)</a>" % (re.sub(r"\W+", "-", g), html.escape(g), len(items)))
    parts.append("</nav>")
    for g, items in groups.items():
        parts.append("<h2 id='%s'>%s: %d</h2>" % (re.sub(r"\W+", "-", g), html.escape(g), len(items)))
        for f in sorted(items, key=lambda f: (f["severity"], f.get("book_page") or 0, f["id"])):
            parts.append("<div class='fix'><div class='meta'><span class='id'>%s</span><span>%s</span><span>%s</span><span>book page %s</span>"
                         "<span>%s</span><span>severity %s</span><span>%s</span></div>" % (
                             f["id"], html.escape(str(f.get("headword") or "")), html.escape("%s · %s" % (f["table"], f["column"])),
                             f.get("book_page") or "?", html.escape(f["kind"]), f["severity"], html.escape(f["grade"])))
            parts.append("<div class='vals'><span>stored</span><div class='stored'>%s</div><span>printed</span><div class='printed'>%s</div>" % (
                html.escape(str(f["stored"]) or "(nothing)"), html.escape(str(f["printed"]) or "(nothing)")))
            if f.get("proposed_value") is not None:
                parts.append("<span>would store</span><div>%s</div>" % html.escape(str(f["proposed_value"])))
            parts.append("</div>")
            if f.get("needs"):
                parts.append("<div class='needs'>Needs: %s</div>" % html.escape(f["needs"]))
            if f["id"] in files:
                parts.append("<img loading='lazy' src='evidence/%s' alt='crop of the printed page for %s'>" % (files[f["id"]], f["id"]))
            parts.append("</div>")
    parts.append("</main></body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", action="store_true", help="also build work/review.html with a crop beside each fix")
    args = ap.parse_args()
    fixes = gather()
    with (OUT / "proposed_fixes.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for f in fixes:
            row = {k: v for k, v in f.items() if k not in ("boxes", "tile")}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    by = collections.Counter((f["source"], f["severity"]) for f in fixes)
    numbers = {
        "proposed_fixes": len(fixes),
        "with_a_proposed_value": sum(1 for f in fixes if f["proposed_value"] is not None),
        "by_source_and_severity": {"%s | severity %s" % k: v for k, v in sorted(by.items())},
        "by_grade": dict(collections.Counter(f["grade"] for f in fixes)),
        "by_source_and_kind": {"%s | %s" % k: v for k, v in collections.Counter((f["source"], f["kind"])).most_common(0)},
    }
    kinds = collections.Counter((f["source"], f["kind"]) for f in fixes)
    numbers["by_source_and_kind"] = {"%s | %s" % k: v for k, v in kinds.most_common()}
    (OUT / "audit_numbers.json").write_text(json.dumps(numbers, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("proposed fixes: %d (%d with a value that can be applied as it stands)" % (len(fixes), numbers["with_a_proposed_value"]))
    for (source, sev), n in sorted(by.items()):
        state.out("  %-36s severity %s  %d" % (source, sev, n))
    state.out("by grade: %s" % numbers["by_grade"])
    if args.review:
        files = render_evidence(fixes, state.WORK / "evidence")
        write_review(fixes, files, state.WORK / "review.html")
        state.out("review page: %s (%d crops)" % ((state.WORK / "review.html").relative_to(state.ROOT).as_posix(), len(files)))


if __name__ == "__main__":
    main()
