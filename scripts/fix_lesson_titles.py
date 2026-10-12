#!/usr/bin/env python3
"""
Fix OCR artifacts in Blue Book lesson titles (lessons table).

Every fix is conservative and evidence-based: digit/letter OCR confusions
(1->I, J->I) justified by the one clean occurrence of the word in the scan
("KIRIKI RASUTSIKS*ARI'?", Lesson 18 header), plus title corrections drawn
from cleaner occurrences elsewhere in the Blue Book text. Where the scan
gives no clean reading (Lesson 8), the title is left exactly as printed.

Usage:
    python scripts/fix_lesson_titles.py            # dry run (default)
    python scripts/fix_lesson_titles.py --apply    # write changes
"""

import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# lesson_number -> {column: (expected_current, corrected, evidence)}
FIXES = {
    1: {"skiri_title": ("KIRIK1 RU'?", "KIRIKI RU'?",
        "OCR 1->I; 'KIRIKI' clean in L18 header; kirikii 'what' in Parks")},
    2: {"skiri_title": ("KIRIKJ RA•TARAWIS?", "KIRIKI RA•TARAWIS?",
        "OCR J->I; 'tarawis' attested in BB text ('tarawis rakis?')")},
    3: {"skiri_title": ("KIRIKJ RUT•U'?", "KIRIKI RUT•U'?",
        "OCR J->I")},
    4: {"skiri_title": ("KIRIKJ RAS•TA?", "KIRIKI RAS•TA?",
        "OCR J->I; ras-ta 'you have' matches L4 vocab tas•ta")},
    6: {"english_title": ("Words to substitute for pita in the dialogues.",
                          "People",
        "BB text prints 'LESSON 6 / People'; stored title was a subheading")},
    7: {"skiri_title": ("TAR1 RU'?", "TARI RU'?",
        "OCR 1->I; 'Tari'' attested as a word in L8 phrases")},
    9: {"skiri_title": ("KIRK RA•'AT", "KIRU RA•'AT",
        "OCR K->U; kiru 'where' attested in L13 title and BB phrases "
        "('KIRU RASUKS•AT?', 'Kiru ras•at')")},
    10: {"skiri_title": ("KIRIK1 RUH•RA'?", "KIRIKI RUH•RA'?",
        "OCR 1->I")},
    11: {"skiri_title": ("KA RIiH•RATSAUS?", "KA RIIH•RATSAUS?",
        "case normalization; L11 vocab tikiih•ratsaus confirms ii")},
    12: {"skiri_title": ("SUKS • U.", "SUKS•U.",
        "spacing normalization around syllable dot")},
    16: {"skiri_title": ("KITSKI WE RU'", "KITSKE WE RU'?",
        "BB text prints 'KITSKE WE RU'?' and 'Kitske'? How much?'")},
    17: {"skiri_title": ("TIRUKS • TSAK • ARIKI", "TIRUKS•TSAKARIKI",
         "L17 vocab prints tiruks•tsakariki as one form"),
         "english_title": ("Verbs to substitute for tatutsiks•a•wahri' "
                           "in the dialogues.", "Yesterday",
         "BB text prints 'LESSON 17 / Yesterday'; stored title was a subheading")},
    20: {"skiri_title": (None, "RATKU•WA•WAKTIT PARI'",
        "missing in DB; BB text prints 'LESSON 20 / RATKU .WA.WAKTIT PARI'' "
        "(dots normalized to the syllable bullet used by other titles)")},
}


def out(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def main():
    parser = argparse.ArgumentParser(description="Fix OCR artifacts in lesson titles")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "skiri_pawnee.db"))
    parser.add_argument("--apply", action="store_true",
                        help="Write changes (default: dry run)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    out(f"{'[APPLY]' if args.apply else '[DRY RUN]'} fixing lesson titles\n")
    applied = skipped = 0
    for number, cols in sorted(FIXES.items()):
        cur.execute("SELECT skiri_title, english_title FROM lessons "
                    "WHERE lesson_number = ?", (number,))
        row = cur.fetchone()
        if not row:
            out(f"L{number}: [SKIP] lesson not found")
            skipped += 1
            continue
        for col, (expected, corrected, evidence) in cols.items():
            current = row[col]
            # Expected-value guard: never overwrite something unanticipated
            if expected is not None and (current or "").strip() != expected:
                if (current or "").strip() == corrected:
                    out(f"L{number}.{col}: already fixed")
                else:
                    out(f"L{number}.{col}: [SKIP] current value "
                        f"{current!r} != expected {expected!r}")
                    skipped += 1
                continue
            if expected is None and (current or "").strip():
                out(f"L{number}.{col}: [SKIP] expected empty, found {current!r}")
                skipped += 1
                continue
            out(f"L{number}.{col}: {current!r} -> {corrected!r}")
            out(f"    evidence: {evidence}")
            if args.apply:
                cur.execute(f"UPDATE lessons SET {col} = ? WHERE lesson_number = ?",
                            (corrected, number))
            applied += 1

    if args.apply:
        conn.commit()
    conn.close()
    out(f"\n{'Applied' if args.apply else 'Would apply'}: {applied}; skipped: {skipped}"
        + ("" if args.apply else "  (re-run with --apply)"))


if __name__ == "__main__":
    main()
