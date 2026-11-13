#!/usr/bin/env python3
"""
The verified character table of the dictionary's text layer
===========================================================

The dictionary PDFs were typeset with custom fonts. Many character codes in
the text layer are stand-ins: the code says one thing and the font draws
another. What a code is drawn as depends on the font.

This table was verified on 2026-11-13 against the printed glyphs: for every
(font family, code) pair in all 471 text-layer pages, occurrences were cut out
of the pages onto contact sheets and read (reports/source_audit_2026-11/
character_readings.json; the sheets are rebuilt by char_sheets.py). For the
accent codes the reading was checked against where each code stands in every
one of its occurrences (char_distribution.py).

The phonetic font has a regular grid of twelve accented vowels:

                      acute              grave
    tense a  (long)   Ñ  á               Ò  à
    lax   a  (short)  à  ə́               á  ə̀
    tense i           æ  í               ç  ì
    lax   i           ‡  ɪ́               ˆ  ɪ̀
    tense u           ÷  ú               ø  ù
    lax   u           Š  ʊ́               ‹  ʊ̀

Two more things in that font are not what they seem:
    -   is printed as a raised dot between syllables
    •   is printed as a dash at the edge of a form that cannot stand alone

    python scripts/source_audit/chartable.py      # writes reports/source_audit_2026-11/character_table.json
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

ACUTE, GRAVE = "́", "̀"
SYLLABLE_DOT = "·"      # · the raised dot between syllables, as printed
EDGE_DASH = "–"         # – the dash at the edge of a bound form, as printed

# family -> code -> what is printed
PRINTED = {
    # phonetic forms, in square brackets
    "PAdothyphen": {
        "-": SYLLABLE_DOT, "•": EDGE_DASH,
        "ß": "ə", "†": "ɪ", "‰": "ʊ", "™": "ʔ", "Ù": "č",
        "Ñ": "á", "Ò": "à", "à": "ə" + ACUTE, "á": "ə" + GRAVE,
        "æ": "í", "ç": "ì", "‡": "ɪ" + ACUTE, "ˆ": "ɪ" + GRAVE,
        "÷": "ú", "ø": "ù", "Š": "ʊ" + ACUTE, "‹": "ʊ" + GRAVE,
    },
    # Skiri in the practical orthography, and words cited from other languages
    "PlainsArial": {
        "™": "ʔ", "Ù": "č", "Ñ": "á", "æ": "í", "÷": "ú",
        "ó": "š", "Ý": "é", "í": "ó", "Ó": "ą", "Ô": "ą" + ACUTE, "è": "į", "ü": "ž", "š": "ⁱ",
        "´": "Ȟ",              # printed as a capital-height H with a caron; occurs once, inside a Skiri word
        "’": "’",
    },
    # English text, and Skiri words quoted in the front matter
    "TruteauGaramond": {"®": "ʔ", "•": "•", "í": "í", "á": "á", "Ø": "Ø", "‘": "‘", "’": "’"},
    "LucidaSansUnicode": {"Ø": "Ø"},
    "CenturySchoolbookN.Plain": {},
    "CSNPdothyphen": {},
    "Garamond": {},
}

# What the stored data writes for the same printed thing. These are conventions of the earlier
# decoding steps; each is reported once, with its count, as a decision for the user, and is not
# counted as a difference entry by entry.
STORED_CONVENTION = {
    SYLLABLE_DOT: "-",                 # stored hyphen = printed syllable dot
    EDGE_DASH: "•",               # stored bullet = printed edge dash
    "ə" + ACUTE: "à",                  # stored a-grave = printed schwa-acute
    "ɪ" + ACUTE: "í",                  # stored i-acute = printed lax-i-acute (and also printed tense i-acute)
    "ɪ" + GRAVE: "ì",                  # stored i-grave = printed lax-i-grave (and also printed tense i-grave)
}


def family(font):
    name = font.replace("-", ",")
    base = name.partition(",")[0]
    for suffix in ("BoldItalic", "Bold", "Italic"):
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[:-len(suffix)]
            break
    return base


def decode(text, font):
    """Text of one span, as printed. A non-ASCII code with no entry for its font is kept, marked ⟦…⟧."""
    table = PRINTED.get(family(font), {})
    out = []
    for ch in text:
        if ch in table:
            out.append(table[ch])
        elif ord(ch) < 128 or ch in " ":
            out.append(" " if ch == " " else ch)
        else:
            out.append("⟦%s⟧" % ch)
    return unicodedata.normalize("NFC", "".join(out))


def to_stored(printed):
    """A printed phonetic form in the convention the database uses today."""
    s = unicodedata.normalize("NFC", printed)
    for a, b in STORED_CONVENTION.items():
        s = s.replace(unicodedata.normalize("NFC", a), b)
    return s


def main():
    joined = json.loads((state.WORK / "char_sheets" / "joined.json").read_text(encoding="utf-8"))
    dist = json.loads((state.WORK / "char_distribution.json").read_text(encoding="utf-8"))
    table = {"_about": ("Every (font family, character code) pair of the dictionary's text layer that is not a plain letter, "
                        "digit or common punctuation mark, with what is printed. Verified 2026-11-13 against glyphs cut from "
                        "the pages; see scripts/source_audit/chartable.py."),
             "_pages": 471, "pairs": []}
    notes = {r["id"]: r for r in joined}
    for r in joined:
        fam, ch = r["family"], r["char"]
        printed = PRINTED.get(fam, {}).get(ch, ch)
        row = {"family": fam, "code": r["code"], "char": ch, "printed": unicodedata.normalize("NFC", printed),
               "occurrences": r["count"], "pages": r["pages"], "looked_at": r["looked_at"], "seen": r["seen"],
               "status": "verified", "assumed_until_now": r["assumed_until_now"], "note": r["note"]}
        if fam == "PAdothyphen" and ch in dist:
            d = dist[ch]
            after_same = sum(v for k, v in d["before"].items() if k in "aiu")
            row["position"] = "%d of %d occurrences directly follow a plain vowel letter" % (after_same, d["occurrences"])
        if r["assumed_until_now"] is None and printed != ch:
            row["finding"] = "was in no table"
        elif r["assumed_until_now"] is not None and unicodedata.normalize("NFC", r["assumed_until_now"]) != row["printed"]:
            row["finding"] = "decoded until now as %s" % r["assumed_until_now"]
        table["pairs"].append(row)
    path = state.OUT / "character_table.json"
    path.write_text(json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("written: %s (%d pairs, %d with a finding)" % (
        path.relative_to(state.ROOT).as_posix(), len(table["pairs"]), sum("finding" in r for r in table["pairs"])))
    for r in table["pairs"]:
        if "finding" in r:
            state.out("  %-17s %s %s  printed %-3s x%-6d %s" % (r["family"], r["char"], r["code"], r["printed"], r["occurrences"], r["finding"]))


if __name__ == "__main__":
    main()
