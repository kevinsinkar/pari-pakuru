#!/usr/bin/env python3
"""Verify that every Pawnee form in the learner documents resolves to a source record.

Conventions of the generated Markdown (see guide.py):
    *italics*   a Pawnee form, exactly as stored in a source record
    [brackets]  Parks's IPA for a headword (lexical_entries.phonetic_form)
    `code`      the learner respelling (lexical_entries.simplified_pronunciation),
                unless it is a file name or command

The valid forms are collected here directly from the database, the gold files
and Parks's printed etymologies, independently of the code that wrote the
documents.  Exit status 1 if anything is unresolved.

    python scripts/morphology_v2/check_forms.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import GOLD, OUT, connect, load_json, out  # noqa: E402

DOCS = ["construction_guide.md", "learning_path.md", "review_queue.md"]
ITALIC = re.compile(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)")
BRACKET = re.compile(r"\[[^\]\n]+\]")
CODE = re.compile(r"`([^`\n]+)`")
NOT_PAWNEE_CODE = re.compile(r"^(SK|BB)-|[/=]|\.(md|py|json|jsonl|db)\b|^--|^e2\b")


def nfc(s):
    return unicodedata.normalize("NFC", s or "").strip()


def valid_forms(conn):
    forms, ipa, say = set(), set(), set()

    def add(s):
        s = nfc(s)
        if not s:
            return
        forms.add(s)
        forms.add(s.strip(" .,;:!?\"“”"))
        for part in re.split(r"[;,]", s):
            part = part.strip()
            if part:
                forms.add(part)
                forms.add(part.strip(" .,;:!?\"“”"))

    for r in conn.execute("select headword, normalized_form, phonetic_form, simplified_pronunciation, "
                          "additional_forms from lexical_entries"):
        add(r[0])
        add(r[1])
        if r[2]:
            ipa.add(nfc(r[2]))
        if r[3]:
            say.add(nfc(r[3]))
        try:
            for f in json.loads(r[4]) if r[4] else []:
                add(f.get("form"))
        except Exception:
            pass
    for r in conn.execute("select phonetic_form from english_index where phonetic_form is not null"):
        ipa.add(nfc(r[0]))
    for (f,) in conn.execute("select skiri_form from paradigmatic_forms"):
        add(f)
    for (f,) in conn.execute("select skiri_form from verb_paradigms"):
        add(f)
    for (f,) in conn.execute("select skiri_text from examples"):
        add(f)
        for tok in nfc(f).split():
            add(tok)
    for (f,) in conn.execute("select bb_skiri_form from blue_book_attestations"):
        add(f)
        for tok in nfc(f).split():
            add(tok)
    for (f,) in conn.execute("select morpheme_form from morpheme_inventory"):
        add(f)
        add(re.sub(r"[^a-zʔØ:]", "", f or ""))
    # the pieces of Parks's printed etymologies
    for (raw,) in conn.execute("select raw_etymology from etymology where raw_etymology is not null"):
        body = nfc(raw).strip("<>").split(";")[0].split(",")[0]
        body = re.sub(r"\([a-z .]*\.\.\.\s*\)", " ", body)
        body = re.sub(r"-\s+(?=[a-zʔ])", "", body)
        for tok in re.split(r"[+.\s]+", body):
            tok = tok.replace("-", "")
            if tok:
                add(tok.replace("’", "ʔ").replace("'", "ʔ"))
                add(re.sub(r"[()]", "", tok).replace("’", "ʔ").replace("'", "ʔ"))
                add(re.sub(r"\([^)]*\)", "", tok).replace("’", "ʔ").replace("'", "ʔ"))
    for e in load_json(GOLD / "g1_go_examples.json")["examples"]:
        add(e["surface"])
        for p in e["pieces"]:
            add(p["form"])
            add(p["form"].strip("-"))
    return forms, ipa, say


def check(conn=None):
    conn = conn or connect()
    forms, ipa, say = valid_forms(conn)
    problems = []
    counts = {"italic": 0, "ipa": 0, "say": 0}
    for name in DOCS:
        path = OUT / name
        if not path.exists():
            problems.append((name, 0, "file", "missing"))
            continue
        for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in ITALIC.finditer(line):
                counts["italic"] += 1
                tok = nfc(m.group(1))
                cands = {tok, tok.strip("-"), tok.strip("-").strip(), tok.strip(" .,;:!?")}
                if not (cands & forms):
                    problems.append((name, ln, "form", tok))
            rest = ITALIC.sub(" ", line)
            for m in CODE.finditer(rest):
                tok = nfc(m.group(1))
                if NOT_PAWNEE_CODE.search(tok):
                    continue
                counts["say"] += 1
                if tok not in say:
                    problems.append((name, ln, "respelling", tok))
            rest = CODE.sub(" ", rest)
            for m in BRACKET.finditer(rest):
                counts["ipa"] += 1
                if nfc(m.group(0)) not in ipa:
                    problems.append((name, ln, "IPA", m.group(0)))
    return counts, problems


def main():
    counts, problems = check()
    out("checked %d Pawnee forms, %d IPA transcriptions, %d respellings in %s" % (
        counts["italic"], counts["ipa"], counts["say"], ", ".join(DOCS)))
    for name, ln, kind, tok in problems[:60]:
        out("UNRESOLVED %s in %s line %d: %s" % (kind, name, ln, tok))
    if problems:
        out("%d unresolved" % len(problems))
        raise SystemExit(1)
    out("all resolved")


if __name__ == "__main__":
    main()
