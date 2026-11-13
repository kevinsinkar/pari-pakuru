#!/usr/bin/env python3
"""
Stage 3b: grade the Skiri-to-English differences from the blind readings
========================================================================

Joins the blind readings of the crops (work/crops_s2e/readings_part*.json)
with the key, and decides for each crop whether the page shows what the text
layer says or what the database says.

    python scripts/source_audit/grade.py            # writes s2e_graded.jsonl and prints the tally

How a reading is judged. The reader transcribed the whole underlined stretch,
which is usually longer than the part in dispute, and a reader can slip
elsewhere in it. So only the places where stored and printed differ are
looked at: for each such place, the printed version with a few characters of
context, and the stored version with the same context, are searched for in the
reading. The page "says printed" if every disputed place is found in its
printed version and none in its stored version; "says stored" the other way
round; anything else is left for a second look.

Grades (see the prompt):
    confirmed      the page image was read and shows the text-layer reading, not the stored one
    text-layer     not read; belongs to a family whose read members all came out "confirmed"
    stored-is-right  the page image shows the stored reading: the text layer misled
    unresolved     the reading settles nothing
    printed-oddity the stored value matches the page, and the page itself looks wrong
"""
import collections
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_core as cc  # noqa: E402
import crops  # noqa: E402
import state  # noqa: E402

FOLDER = state.WORK / "crops_s2e"
MIN_FAMILY_READ = 30


def canon(s):
    """For comparing a reading with a candidate: no spaces, hyphens, syllable dots or edge dashes; lax i folded."""
    s = cc.nfc(s or "").replace("[?]", "")
    for ch in ("•", cc.SYLLABLE_DOT, cc.EDGE_DASH, "—", "−", "‑", "­", ".", "ˀ", "ʼ"):
        s = s.replace(ch, "" if ch != "ˀ" else "ʔ")
    s = s.replace("’", "'").replace("‘", "'")
    return cc.fold_lax_i(cc.skeleton(s))


def spaced(s):
    s = cc.tidy(cc.nfc(s or "").replace("[?]", "").replace("•", cc.SYLLABLE_DOT))
    return re.sub(r"\s+", " ", s)


def vote(stored, printed, reading):
    """Which version of each disputed place the reading contains: ('printed' | 'stored' | 'neither' | 'both', detail)."""
    cs, cp, ct = canon(stored), canon(printed), canon(reading)
    if cs == cp:
        return "same", []
    votes, detail = [], []
    m = difflib.SequenceMatcher(None, cs, cp, autojunk=False)
    for op, i1, i2, j1, j2 in m.get_opcodes():
        if op == "equal":
            continue
        for width in (5, 3, 2):
            ctx_s = cs[max(0, i1 - width):i2 + width]
            ctx_p = cp[max(0, j1 - width):j2 + width]
            in_s, in_p = ctx_s in ct, ctx_p in ct
            if ctx_s == ctx_p:
                continue
            # one context containing the other proves nothing about the shorter one
            if in_s and in_p and (ctx_s in ctx_p or ctx_p in ctx_s):
                in_s, in_p = (len(ctx_s) > len(ctx_p)), (len(ctx_p) > len(ctx_s))
            if in_s != in_p:
                votes.append("printed" if in_p else "stored")
                detail.append([cs[i1:i2], cp[j1:j2], "printed" if in_p else "stored"])
                break
        else:
            votes.append("neither")
            detail.append([cs[i1:i2], cp[j1:j2], "neither"])
    if votes and all(v == "printed" for v in votes):
        return "printed", detail
    if votes and all(v == "stored" for v in votes):
        return "stored", detail
    return "mixed", detail


def judge(item, reading):
    fam, kind, field = item["family"], item["kind"], crops.base_field(item["field"])
    stored, printed = item["stored"], item["printed"]
    if field == "phonetic_form":
        stored = cc.stored_phonetic_as_printed(stored)
    ct = canon(reading)
    if fam == "agreement-sample":
        return ("agrees" if canon(stored) in ct else "reader-differs"), []
    if fam == "printed-not-stored":
        return ("confirmed" if canon(printed) in ct else "unresolved"), []
    if fam == "entry":
        return ("confirmed" if canon(item["headword"]) in ct else "unresolved"), []
    if fam == "bracket-note":
        note = "".join(re.findall(r"\[[^\]]*\]", printed))
        return ("confirmed" if note and canon(note) in ct else "unresolved"), []
    if fam == "class":
        import s2e_compare
        read_tokens = s2e_compare.class_tokens(reading)
        names = lambda toks: sorted(t for t in toks if not t.startswith("("))
        numbers = lambda toks: sorted(set(t for t in toks if t.startswith("(")))
        p, s = s2e_compare.class_tokens(printed), s2e_compare.class_tokens(stored)
        same_p = names(read_tokens) == names(p) and numbers(read_tokens) == numbers(p)
        same_s = names(read_tokens) == names(s) and numbers(read_tokens) == numbers(s)
        return ("confirmed" if same_p and not same_s else "stored-is-right" if same_s and not same_p else "unresolved"), []
    if fam in ("spacing-or-line-break", "phonetic-word-space"):
        t, p, s = spaced(reading), spaced(printed), spaced(stored)
        if field == "phonetic_form":
            sq = lambda x: re.sub(r"[\[\]]", "", x.replace(cc.EDGE_DASH, "").replace("-", ""))
            t, p, s = sq(t), sq(p), sq(s)
        if kind == "stored-keeps-line-break":
            # the image can only show that the hyphen stands at a line end; the reader was told to keep it there
            joined = canon(printed) in ct
            return ("confirmed" if joined and re.search(r"-\s", cc.nfc(reading)) else "unresolved"), []
        in_p, in_s = p in t, s in t
        if in_p and not in_s:
            return "confirmed", []
        if in_s and not in_p:
            return "stored-is-right", []
        # fall back on the forms with spaces removed, to see at least that the letters are these
        return "unresolved", []
    v, detail = vote(stored, printed, reading)
    return {"printed": "confirmed", "stored": "stored-is-right", "same": "unresolved"}.get(v, "unresolved"), detail


def main():
    key = json.loads((FOLDER / "key.json").read_text(encoding="utf-8"))
    readings = {}
    for f in sorted(FOLDER.glob("readings_part*.json")):
        readings.update(json.loads(f.read_text(encoding="utf-8")))
    second = FOLDER / "second_look.json"          # the unresolved ones, read again at higher zoom
    second_look = json.loads(second.read_text(encoding="utf-8")) if second.exists() else {}
    diffs = [json.loads(line) for line in (state.OUT / "s2e_differences.jsonl").open(encoding="utf-8")]
    missing = sorted(set(key) - set(readings))
    state.out("crops: %d; readings: %d; not read yet: %d" % (len(key), len(readings), len(missing)))

    graded = {}                                   # difference index -> grade record
    tally = collections.defaultdict(collections.Counter)
    agreement = collections.Counter()
    unresolved = []
    for cid, item in sorted(key.items()):
        if cid not in readings:
            continue
        reading = readings[cid]
        verdict, detail = judge(item, reading)
        if cid in second_look:
            verdict = second_look[cid]["grade"]
            reading = "%s || second look: %s" % (reading, second_look[cid].get("reading", ""))
        if item["what"] == "agreement":
            agreement[verdict] += 1
            if verdict != "agrees":
                unresolved.append((cid, item, readings[cid], verdict))
            continue
        tally[item["family"]][verdict] += 1
        graded[item["index"]] = {"grade": verdict, "crop": cid, "sheet": item["sheet"], "reading": reading, "votes": detail}
        if verdict not in ("confirmed",):
            unresolved.append((cid, item, readings[cid], verdict))

    # families that were sampled: extend the grade to the unread members only if every read member is confirmed
    read_by_family = collections.defaultdict(list)
    for i, g in graded.items():
        read_by_family[crops.family(diffs[i])].append(g["grade"])
    out_rows = []
    final = collections.Counter()
    for i, d in enumerate(diffs):
        if d["class"] != "difference":
            continue
        fam = crops.family(d)
        row = dict(d)
        row["family"] = fam
        if i in graded:
            row.update(graded[i])
        elif fam == "column":
            row["grade"], row["basis"] = "text-layer", "geometry: the headword's position on the page"
        elif fam == "entry" and d["kind"] == "stored-entry-not-printed":
            row["grade"], row["basis"] = "text-layer", "no such headword on any of the 181 pages"
        else:
            grades = read_by_family.get(fam, [])
            if len(grades) >= MIN_FAMILY_READ and all(g == "confirmed" for g in grades):
                row["grade"], row["basis"] = "text-layer", "%d read members of this family all confirmed" % len(grades)
            else:
                row["grade"], row["basis"] = "unresolved", "not read, and its family is not uniformly confirmed (%d read)" % len(grades)
        final[(fam, row["grade"])] += 1
        out_rows.append(row)
    with (state.OUT / "s2e_graded.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    state.out("")
    state.out("read crops, by family:")
    for fam, c in sorted(tally.items()):
        state.out("  %-24s %s" % (fam, dict(c)))
    state.out("agreement sample (database and text layer agree; does the page?): %s" % dict(agreement))
    state.out("")
    state.out("all %d differences, by family and grade:" % len(out_rows))
    for (fam, grade), n in sorted(final.items()):
        state.out("  %-24s %-16s %d" % (fam, grade, n))
    (FOLDER / "to_second_look.json").write_text(json.dumps(
        [{"crop": cid, "sheet": item["sheet"], "family": item["family"], "field": item["field"], "kind": item["kind"],
          "verdict": verdict, "boxes": item["boxes"]} for cid, item, reading, verdict in unresolved], ensure_ascii=False, indent=1), encoding="utf-8")
    state.out("")
    state.out("left for a second look: %d (work/crops_s2e/to_second_look.json)" % len(unresolved))
    return unresolved


if __name__ == "__main__":
    main()
