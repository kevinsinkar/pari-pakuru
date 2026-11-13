#!/usr/bin/env python3
"""
Stage 1c: join the sheet readings with the key
==============================================

Puts what was read off the contact sheets (character_readings.json) beside the
code each row stands for (work/char_sheets/key.json) and beside what the
project's decoding steps have assumed until now.

    python scripts/source_audit/char_join.py

Prints the table and writes work/char_sheets/joined.json. The verified table
itself, character_table.json, is written by hand from this and from the
distribution checks (char_distribution.py): it is a judgement, not a join.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

# What earlier steps decoded each stand-in as. PHON: the table in fix_data_2026_11.py (after its
# 2026-11-13 correction), which is what the stored phonetic forms follow.
ASSUMED = {
    "PAdothyphen": {"ß": "ə", "†": "ɪ", "‰": "ʊ", "™": "ʔ", "Ù": "č", "à": "à", "‡": "í", "Ñ": "á", "æ": "í",
                    "÷": "ú", "Š": "ʊ́", "ˆ": "ì", "ç": "ì", "ø": "ù", "Ò": "à", "á": "á", "•": "•", "-": "-"},
    "PlainsArial": {"™": "ʔ", "Ù": "č", "Ñ": "á", "æ": "í", "÷": "ú"},
    "TruteauGaramond": {"®": "ʔ"},
}


def main():
    key = json.loads((state.WORK / "char_sheets" / "key.json").read_text(encoding="utf-8"))
    readings = json.loads((state.OUT / "character_readings.json").read_text(encoding="utf-8"))
    rows = []
    for kid, k in sorted(key.items(), key=lambda kv: (kv[1]["family"], -kv[1]["count"])):
        r = readings[kid]
        assumed = ASSUMED.get(k["family"], {}).get(k["char"])
        rows.append({"id": kid, "family": k["family"], "char": k["char"], "code": k["code"], "count": k["count"],
                     "pages": k["pages"], "looked_at": k["looked_at"], "printed": r["printed"], "seen": r["seen"],
                     "assumed_until_now": assumed, "note": r["note"]})
    (state.WORK / "char_sheets" / "joined.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    state.out("%-4s %-17s %-4s %-7s %6s %5s  %-8s %-8s %s" % ("id", "font family", "char", "code", "count", "pages", "printed", "assumed", ""))
    for r in rows:
        flag = ""
        if r["assumed_until_now"] is None:
            flag = "same glyph" if r["printed"] == r["char"] else "NOT IN ANY TABLE"
        elif r["assumed_until_now"] != r["printed"]:
            flag = "DIFFERS"
        state.out("%-4s %-17s %-4s %-7s %6d %5d  %-8s %-8s %s" % (
            r["id"], r["family"], r["char"], r["code"], r["count"], r["pages"], r["printed"], r["assumed_until_now"] or "", flag))


if __name__ == "__main__":
    main()
