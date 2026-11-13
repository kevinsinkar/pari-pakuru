#!/usr/bin/env python3
"""
Weekly hand-written flashcard sheets from the frozen curriculum
================================================================

Reads curriculum/flashcard_sets.json (24 frozen weekly sets) and writes
curriculum/weekly_flashcards.md: one section per week, dated to a Sunday,
with every card laid out as Front / Back so it can be copied onto paper.

Where the word-building information comes from
  The line "built from ..." on an A card, and the noun C cards, are read from the
  version 2 word-construction analysis (curriculum/roots_v2/evidence.jsonl and
  roots.json). Until 2026-11-13 they came from version 1, which put some
  meanings on the wrong piece.
    * The pieces are Parks's printed etymology, and are shown only when they
      reproduce the headword (exactly or nearly).
    * A piece gets a meaning only when Parks glosses that piece by itself in
      that word, or when two readings agree: the meaning the analysis checked
      for the piece, and the gloss stored with the piece or Parks's literal
      translation of the word. Where they disagree, or Parks gives the piece
      no meaning, the piece is shown bare. A bare piece is not an error.
    * A C card is offered only when the root has the same checked meaning in
      both words, and never for a word flagged for community review.
  Weeks listed in curriculum/held_for_review.json are left out; the other weeks
  keep their numbers and dates.

Card design (spaced-repetition practice):
  A  recognition  front = Pawnee word + pronunciation      back = meaning, class, source, build
  B  production   front = English meaning + class cue      back = Pawnee word + pronunciation
  C  forms        one card per attested inflected form (verbs) or per related
                  compound built on the same root (nouns) — optional extras

Spelling: learner orthography (â î û, ', č) as in the project's normalized_form;
Parks's dictionary spelling is given on the back for lookup. Pronunciations
without ≈ come from Parks's phonetic transcription (DB column); ≈ marks a
spelling-based respelling of an inflected form (no stress information).

Usage:
    python scripts/build_weekly_flashcards.py                      # Week 1 = next Sunday (or today if Sunday)
    python scripts/build_weekly_flashcards.py --start 2026-11-08   # explicit first Sunday
"""
import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "morphology_v2"))
from build_root_curriculum import modern_spelling, respell_orthography  # noqa: E402
from analysis import gloss_stems  # noqa: E402

SETS = ROOT / "curriculum" / "flashcard_sets.json"
HELD = ROOT / "curriculum" / "held_for_review.json"
EVIDENCE = ROOT / "curriculum" / "roots_v2" / "evidence.jsonl"
ROOTS = ROOT / "curriculum" / "roots_v2" / "roots.json"
OUT = ROOT / "curriculum" / "weekly_flashcards.md"

# what counts as a checked meaning (scripts/morphology_v2/analysis.py, SENSE_EVIDENCED)
CHECKED = ("aligned", "literal", "entry_gloss", "inherited")

CLASS_LABEL = {
    "N": "noun", "N-DEP": "noun (bound stem)", "N-KIN": "kinship noun", "NUM": "number", "INTERJ": "interjection",
    "EXCL": "exclamation", "ADV": "adverb", "ADJ": "adjective", "PRON": "pronoun", "DEM": "demonstrative", "CONJ": "conjunction",
    "PART": "particle", "LOC": "locative", "VI": "intransitive verb", "VT": "transitive verb", "VD": "descriptive verb (be ...)",
    "VP": "passive verb (it happens to someone)", "VL": "locative verb (be in/on/at)", "VR": "reflexive verb",
}
FORM_CUES = {1: "I … (1sg)", 2: "he / she / it … (3sg)", 3: "is …-ing (imperfective)", 5: "is going to … (intentive)"}


def norm(s):
    return unicodedata.normalize("NFC", s or "").replace("’", "ʔ").strip()


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")


def class_label(gc):
    if not gc:
        return ""
    return "; ".join(CLASS_LABEL.get(p.strip(), p.strip()) for p in gc.split(","))


def stems(text):
    """Content stems of an English gloss; the bare words when it has no content word ('one')."""
    return set(gloss_stems(text)) or set(re.findall(r"[a-z]+", (text or "").lower()))


def clean_gloss(text):
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", " ", text or "")).strip(" ,;")


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", help="date of the first Sunday (YYYY-MM-DD)")
    ap.add_argument("--db", default=str(ROOT / "skiri_pawnee.db"))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    if args.start:
        start = dt.date.fromisoformat(args.start)
    else:
        today = dt.date.today()
        start = today + dt.timedelta(days=(6 - today.weekday()) % 7)
    if start.weekday() != 6:
        sys.exit(f"{start} is not a Sunday")

    sets = json.loads(SETS.read_text(encoding="utf-8"))
    held = {h["week"]: h for h in json.loads(HELD.read_text(encoding="utf-8")).get("weeks", [])} if HELD.exists() else {}
    ev = {}          # entry id -> evidence record of its word
    records = []
    for line in EVIDENCE.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        records.append(rec)
        for member in rec["member_ids"]:
            ev[member] = rec
    senses = {}      # sense id -> (meaning, stems of every gloss Parks uses for it, those glosses)
    for r in json.loads(ROOTS.read_text(encoding="utf-8"))["roots"]:
        variants = [g["gloss"] for g in r.get("gloss_variants") or []]
        st = stems(r["meaning"])
        for g in variants:
            st |= stems(g)
        senses[r["id"]] = (r["meaning"], st, variants)
    conn = sqlite3.connect(args.db)
    labels_used = set()

    def forms(eid):
        return {n: norm(f) for n, f in conn.execute("select form_number, skiri_form from paradigmatic_forms where entry_id=?", (eid,))}

    def bb(eid):
        r = conn.execute("""select bb_skiri_form, lesson_number, page_number from blue_book_attestations where entry_id=?
                            and match_type in ('exact_normalized','orthographic','loose') order by lesson_number limit 1""", (eid,)).fetchone()
        return f"Blue Book *{r[0]}* (L{r[1]}{', p.' + str(r[2]) if r[2] else ''})" if r else ""

    def usable(rec):
        """Parks prints an analysis of two or more pieces, and the pieces reproduce the headword."""
        return bool(rec) and rec.get("e1") == "printed" and len(rec.get("pieces") or []) >= 2 \
            and (rec.get("e2") or {}).get("status") in ("exact", "partial")

    def looks_like_the_word(gloss, rec):
        """Parks sometimes 'glosses' a piece with its own shape: that is not a meaning."""
        g = re.sub(r"[^a-zʔ]", "", norm(gloss).lower())
        shapes = re.sub(r"[^a-zʔ]", "", norm((rec.get("raw_etymology") or "").split(",")[0]).lower())
        return len(g) >= 3 and g in shapes

    def best(candidates, allowed):
        """The gloss that says most while saying nothing outside `allowed`."""
        ok = [c for c in candidates if c and stems(c) and stems(c) <= allowed]
        return max(ok, key=lambda c: (len(stems(c)), -candidates.index(c))) if ok else None

    def piece_gloss(piece, rec):
        """The meaning to print beside a piece, or None when no two readings agree on one."""
        if piece["role"] == "grammatical":
            return piece.get("label")
        if piece.get("gloss_kind") == "self" or piece.get("sense_evidence") == "meaning_unknown_to_parks":
            return None                      # Parks gives the piece no meaning
        if piece.get("gloss_kind") == "aligned" and piece.get("gloss"):
            g = clean_gloss(piece["gloss"])  # Parks glosses this piece by itself in this word
            return None if (not g or looks_like_the_word(g, rec)) else g
        sid = piece.get("sense_id")
        if not sid or piece.get("sense_evidence") not in CHECKED or sid not in senses:
            return None
        meaning, sense_stems, variants = senses[sid]
        if looks_like_the_word(meaning, rec):
            return None
        stored = clean_gloss(piece.get("stored_gloss"))
        if stored and stored != piece["form"] and not looks_like_the_word(stored, rec):
            if stems(stored) <= sense_stems:
                return stored                # the stored gloss says nothing beyond the checked meaning
            return best([meaning] + variants, stems(stored))     # the checked meaning, if the stored gloss contains it
        # no gloss stored with the piece: the checked meaning must be in Parks's literal translation
        return best([meaning] + variants, stems(clean_gloss(piece.get("phrase") or rec.get("literal"))))

    def build_note(eid):
        rec = ev.get(eid)
        if not usable(rec):
            return ""
        glosses = [piece_gloss(piece, rec) for piece in rec["pieces"]]
        # one word of the translation cannot stand beside two pieces: keep it on the piece it fits most closely
        for i, gi in enumerate(glosses):
            for j, gj in enumerate(glosses):
                if i >= j or not gi or not gj:
                    continue
                if rec["pieces"][i]["role"] != "lexical" or rec["pieces"][j]["role"] != "lexical":
                    continue
                if stems(gi) & stems(gj):
                    if len(stems(gi)) == len(stems(gj)):
                        glosses[i] = glosses[j] = None
                    elif len(stems(gi)) > len(stems(gj)):
                        glosses[i] = None
                    else:
                        glosses[j] = None
        parts = []
        for piece, lab in zip(rec["pieces"], glosses):
            if lab and piece["role"] == "grammatical":
                labels_used.add(lab)
            parts.append(f"{modern_spelling(piece['form'])}" + (f" '{lab}'" if lab else ""))
        return "built from " + " + ".join(parts)

    KIN_POSSESSORS = {"a#your", "ati#my", "i#his her"}

    def root_sense(rec):
        """(form, sense id) of the word's one root, when its meaning was checked there."""
        lexical = [p for p in (rec or {}).get("pieces") or [] if p["role"] == "lexical" and p.get("sense_id") not in KIN_POSSESSORS]
        if len(lexical) != 1:
            return None
        p = lexical[0]
        if not p.get("sense_id") or p.get("sense_evidence") not in CHECKED:
            return None
        return p["form"], p["sense_id"]

    by_sense = {}
    for rec in records:
        if not usable(rec) or rec.get("needs_community_review"):
            continue
        for p in rec["pieces"]:
            if p["role"] == "lexical" and p.get("sense_id") and p.get("sense_evidence") in CHECKED:
                by_sense.setdefault(p["sense_id"], []).append(rec)

    def related(eid, hw_key, limit=2):
        """Attested compounds built on the headword's root, with the same checked meaning (nouns)."""
        rec = ev.get(eid)
        rs = root_sense(rec) if usable(rec) else None
        if not rs:
            return []
        seen, hits = set(), []
        for other in by_sense.get(rs[1], []):
            key = strip_accents(norm(other["headword"]).split(",")[0].strip())
            if other["lexeme_id"] == rec["lexeme_id"] or key == hw_key or other["lexeme_id"] in seen:
                continue
            seen.add(other["lexeme_id"])
            hits.append(other)
        # compounds that begin with the root first (the root is easiest to see there), then nouns,
        # then confirmed analyses, then short words
        hits.sort(key=lambda r: (r["pieces"][0]["form"] != rs[0], not (r.get("class") or "").startswith("N"),
                                 r.get("tier") not in ("A", "B"), len(norm(r["headword"])), r.get("book_page") or 0, r["lexeme_id"]))
        return hits[:limit]

    pron_db = {r[0]: r[1] for r in conn.execute("select entry_id, simplified_pronunciation from lexical_entries where simplified_pronunciation is not null")}

    L = ["# Weekly flashcards — Skiri Pawnee (hand-written sets)", "",
         f"Generated by `scripts/build_weekly_flashcards.py` from the frozen curriculum `curriculum/flashcard_sets.json` "
         f"(version {sets['version']}, frozen {sets['frozen_date']}). Week 1 is Sunday {start.isoformat()}; each later week is the next Sunday. "
         "Write the week's cards on Sunday, then review them during the week (see the schedule below).", "",
         "How a word is built, and which compounds are offered on C cards, comes from the word-construction analysis in "
         "`curriculum/roots_v2/`. A meaning is printed beside a piece only where Parks glosses that piece by itself in the word, or "
         "where the analysis and Parks's translation of the word agree on it. Otherwise the piece is shown bare: that means "
         "\"no meaning confirmed\", not \"no meaning\".", "",
         "## How the cards are designed", "",
         "- **One fact per card.** A word gets two core cards: **A** (see Pawnee → recall meaning) and **B** (see English → produce Pawnee). "
         "Testing both directions is what makes a word usable, not just recognisable.",
         "- **Pronunciation sits with the Pawnee word**, never alone on the front: on card A it is part of the cue (read it aloud before flipping), "
         "on card B it is part of the answer (say it, then check).",
         "- **Backs are short.** Meaning, word class, a source reference, and, when Parks gives one, how the word is built from its pieces. "
         "The source lets you check the dictionary later instead of trusting the card.",
         "- **Forms go on their own cards (C).** For verbs, each attested dictionary form is a separate card cued by its meaning "
         "('he/she …', 'I …', 'is …-ing', 'is going to …'). For nouns, up to two attested compounds built on the same root are extra cards. "
         "Treat C cards as optional: add them in a later week if the A/B cards are already solid.",
         "- **Spelling.** Cards use the learner spelling (*â î û* long vowels, *'* glottal stop, *č* = ch, *c* = ts). The back of card A gives "
         "Parks's dictionary spelling and page for lookup. Pronunciations without ≈ come from Parks's phonetic transcription; "
         "≈ marks a spelling-based respelling of an inflected form (no stress shown). CAPITALS mark Parks's accented syllable.",
         "- **Review schedule.** Sunday: write and read through once. Monday: all cards. Tuesday: misses only. Thursday: all cards. "
         "Saturday: all cards plus a shuffled handful from every earlier week. A card answered correctly three reviews in a row moves to a "
         "monthly pile.", ""]

    total_cards = 0
    total_words = 0
    for w in sets["weeks"]:
        wk = w["week"]
        sunday = start + dt.timedelta(weeks=wk - 1)
        if wk in held:
            L += [f"## Week {wk} — Sunday {sunday.isoformat()} — {w['category_label']}", "",
                  "*Held back.* This week's words are waiting for review by the Pawnee community "
                  "(`curriculum/held_for_review.json`). Use the week to review earlier sets.", ""]
            continue
        total_words += len(w["cards"])
        rows = []
        n_cards = 0
        for i, k in enumerate(w["cards"], 1):
            eid = k["entry_id"]
            hw = norm(k["headword"]).split(",")[0].strip()
            hw_key = strip_accents(hw)
            modern = k.get("normalized_form") or modern_spelling(hw)
            modern = modern.split(",")[0].strip()
            pron = k.get("simplified_pronunciation") or pron_db.get(eid) or f"≈{respell_orthography(hw)}"
            definition = (k["definition"] or "").strip().rstrip(".")
            short_def = definition.split(";")[0].strip()
            gc = k.get("grammatical_class") or ""
            label = class_label(gc)
            more = f" (+{k['sense_count'] - 1} more sense{'s' if k['sense_count'] > 2 else ''} in the dictionary)" if (k.get("sense_count") or 1) > 1 else ""
            src = (f"Parks p.{k['page_number']}, `{eid}`" if k.get("page_number") else f"`{eid}`")
            if k.get("source") == "blue_book":
                src = "Blue Book only (no Parks entry); " + src
            b = bb(eid)
            build = build_note(eid)
            back_a = f"**{short_def}**" + (f" — {definition}" if definition != short_def else "") + more + \
                     f"<br>{label}" + (f"<br>{build}" if build else "") + \
                     f"<br>dictionary spelling *{hw}*; {src}" + (f"; {b}" if b else "")
            rows.append([f"{wk}.{i}A", f"**{modern}** ⟨{pron}⟩", back_a])
            cue = label
            if gc.startswith("V") and not gc.startswith("VD"):
                cue = label + " — dictionary stem"
            rows.append([f"{wk}.{i}B", f"{short_def}<br>*({cue})*", f"**{modern}** ⟨{pron}⟩"])
            n_cards += 2
            # C cards
            if gc.startswith("V"):
                fs = forms(eid)
                j = 0
                for n in (2, 1, 3, 5):
                    if n in fs:
                        f = fs[n].split(",")[0].strip()
                        j += 1
                        rows.append([f"{wk}.{i}C{j}", f"'{short_def}': {FORM_CUES[n]}<br>*(stem {modern})*",
                                     f"**{modern_spelling(f)}** ⟨≈{respell_orthography(f)}⟩<br>dictionary form {n} of *{hw}*, Parks p.{k.get('page_number')}"])
                        n_cards += 1
            elif gc.startswith("N"):
                for j, other in enumerate(related(eid, hw_key), 1):
                    ohw = norm(other["headword"]).split(",")[0].strip()
                    oid = other["lexeme_id"]
                    opron = pron_db.get(oid) or f"≈{respell_orthography(ohw)}"
                    pieces = " + ".join(modern_spelling(p["form"]) for p in other["pieces"])
                    rows.append([f"{wk}.{i}C{j}", f"**{modern_spelling(ohw)}** ⟨{opron}⟩<br>*(built on {modern_spelling(hw_key)})*",
                                 f"**{(other['gloss'] or '').split(';')[0].strip().rstrip('.')}**<br>{pieces}<br>Parks p.{other['page_number']}, `{oid}`"])
                    n_cards += 1
        total_cards += n_cards
        L += [f"## Week {wk} — Sunday {sunday.isoformat()} — {w['category_label']}", "",
              f"{len(w['cards'])} words → {n_cards} cards ({2 * len(w['cards'])} core A/B cards, {n_cards - 2 * len(w['cards'])} optional C cards).", "",
              "| Card | Front | Back |", "|---|---|---|"]
        for r in rows:
            L.append("| " + " | ".join(cell(x) for x in r) + " |")
        L.append("")
    aff = json.loads((ROOT / "curriculum" / "roots_v2" / "affixes.json").read_text(encoding="utf-8"))
    meaning_of = {}
    for a in aff["affixes"] + list(aff.get("inflectional") or []):
        if isinstance(a, dict) and a.get("label") and a.get("meaning"):
            meaning_of.setdefault(a["label"], a["meaning"])
    legend = "; ".join(f"{lab} = {meaning_of[lab]}" for lab in sorted(labels_used) if lab in meaning_of)
    plain = sorted(lab for lab in labels_used if lab not in meaning_of)
    at = L.index("## How the cards are designed") + 2
    L.insert(at, "- **Labels in capitals** are Parks's grammatical labels for pieces that have a job, not a dictionary meaning: "
             + legend + ("; also " + ", ".join(plain) if plain else "") + ".")
    L.insert(2, f"**Total: {total_words} words, {total_cards} cards over {len(sets['weeks'])} weeks "
                f"({start.isoformat()} to {(start + dt.timedelta(weeks=len(sets['weeks']) - 1)).isoformat()}).**")
    L.insert(3, "")
    Path(args.out).write_text("\n".join(L), encoding="utf-8")
    sys.stdout.buffer.write(f"wrote {args.out}: {total_cards} cards\n".encode("utf-8"))


if __name__ == "__main__":
    main()
