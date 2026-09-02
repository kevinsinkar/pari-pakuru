#!/usr/bin/env python3
"""
Phase 5.1 — Structured Lesson Content from the Blue Book
=========================================================

Deterministically parses `pari pakuru/Blue_Book_Pari_Pakuru.txt` (the 1979
Pawnee Cultural Retention Committee textbook) into a structured `lessons`
table: titles, page ranges, ordered dialogue exchanges, and grammar/culture
prose sections. No AI calls — everything comes straight from the text.

Lesson VOCABULARY is not duplicated here: the web layer reads it from
`blue_book_attestations` (Phase 2.2), which already links items to dictionary
entries. Known gap: lessons 3–4 vocabulary was garbled by column reflow in
the source text (8 + 5 attestation items only); their dialogues parse fine.

Sentence-builder template links per lesson come from the Phase 3.2a design
doc's attestation table (phase_3_2a_sentence_templates.md, Appendix A).

Usage:
  python scripts/build_lessons.py            # dry-run: parse + report
  python scripts/build_lessons.py --apply    # write lessons table to DB
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BB_TEXT = ROOT / 'pari pakuru' / 'Blue_Book_Pari_Pakuru.txt'
DB_PATH = ROOT / 'skiri_pawnee.db'
OUT_JSON = ROOT / 'extracted_data' / 'lessons.json'
REPORT = ROOT / 'reports' / 'phase_5_1_lessons.txt'

LOG = []


def log(s):
    LOG.append(s)
    sys.stdout.buffer.write((s + '\n').encode('utf-8', errors='replace'))


# Templates attested per lesson — from phase_3_2a_sentence_templates.md
# Appendix A (sentence-to-template mapping) plus template `lessons` metadata.
LESSON_TEMPLATES = {
    1: ['T1', 'T3', 'T4', 'T6', 'T7'],
    2: ['T2', 'T3', 'T4', 'T6', 'T7'],
    3: ['T3', 'T4', 'T6', 'T7'],
    4: ['T4'],
    5: ['T3', 'T5'],
    6: ['T3', 'T4', 'T6', 'T9'],
    7: ['T1'],
    8: ['T3', 'T4', 'T7', 'T8'],
    9: ['T2', 'T3', 'T9'],
    10: ['T4'],
    11: ['T7', 'T8'],
    12: ['T10'],
    13: ['T1', 'T5', 'T8'],
    14: ['T3', 'T9'],
    15: ['T10'],
    16: ['T8'],
    17: ['T8'],
    18: ['T3', 'T6', 'T8'],
    19: ['T8'],
    20: ['T7', 'T10'],
}

# Section headers that hold ITEM LISTS (rendered from attestations, not prose)
ITEM_SECTIONS = {'BASIC WORDS', 'ADDITIONAL WORDS', 'DIALOGUES', 'DIALOGUE'}

PAGE_RE = re.compile(r'^=+\s*$')
PAGE_NUM_RE = re.compile(r'^PAGE (\d+)\s*$')
# a section header: short mostly-caps line (allows digits: 'DIALOGUE 1')
HEADER_RE = re.compile(r"^[A-Z][A-Z0-9 '•&,-]{2,40}:?$")
# page-marker fragments broken across lines ('P' / 'AGE 60')
BROKEN_PAGE_RE = re.compile(r'^(P|AGE \d+)$')
LESSON_RE = re.compile(r'^(.*?)\s*LESSON\s*(\d+)?\s*$')
# post-scan English title: standalone Title-Case line, 2+ words
TITLE_SCAN_RE = re.compile(
    r"^[A-Z][a-z'•]+(?: [A-Za-z'•]+){1,7}[?.!]$")


def looks_skiri_title(s):
    """Mostly-uppercase line with Skiri markers (•, ?, ') — OCR noise ok."""
    if not s or len(s) > 45:
        return False
    letters = [ch for ch in s if ch.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
    return upper_ratio >= 0.6 and any(ch in s for ch in "•?'")


def parse_dialogue_line(line):
    """Split 'N. Skiri sentence? English translation.' into parts.

    Returns (num_or_None, skiri, english) or None if not a dialogue line.
    The split point is the first . ? ! that is followed by whitespace and an
    uppercase letter or '(' — this keeps mid-form syllable dots (' .rihu')
    and Skiri-final apostrophes attached to the Skiri side.
    """
    line = line.strip()
    if not line:
        return None
    m = re.match(r'^(\d+)[.)]\s+(.*)$', line)
    num = None
    if m:
        num = int(m.group(1))
        line = m.group(2)
    for i, ch in enumerate(line):
        if ch in '.?!':
            rest = line[i + 1:]
            # allow a trailing apostrophe glued to the punctuation
            rest2 = rest.lstrip("'’ ")
            if rest and rest[0] in ' \t' and rest2 and rest2[0].isupper():
                skiri = line[:i + 1].strip()
                english = rest.strip()
                return (num, skiri, english)
    # no split found: whole line is Skiri (or continuation)
    return (num, line, '')


def clean_prose(lines):
    """Join prose lines: drop page separators/numbers, fix hyphen breaks."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or PAGE_RE.match(s) or PAGE_NUM_RE.match(s):
            continue
        if re.match(r'^\d{1,3}[,.]?$', s):   # bare printed page number
            continue
        out.append(s)
    text = ' '.join(out)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)   # line-break hyphens
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def parse_lessons(text):
    lines = text.splitlines()
    lessons = {}
    cur = None            # current lesson dict
    cur_section = None    # current section header
    section_lines = []
    page = None
    last_nonempty = ''
    prev_lesson_num = 0

    def flush_section():
        nonlocal section_lines, cur_section
        if cur is None or cur_section is None:
            section_lines = []
            return
        if cur_section in ITEM_SECTIONS or cur_section.startswith('DIALOGUE'):
            # reflow-displaced English title inside a vocab block (L04)
            if not cur_section.startswith('DIALOGUE') and \
                    cur['english_title'] is None:
                for ln in section_lines:
                    if TITLE_SCAN_RE.match(ln.strip()):
                        cur['english_title'] = ln.strip()
                        break
            if cur_section.startswith('DIALOGUE'):
                exchanges = []
                current_ex = None
                for ln in section_lines:
                    s = ln.strip()
                    if not s or PAGE_RE.match(s) or PAGE_NUM_RE.match(s):
                        continue
                    if re.match(r'^\d{1,3}[,.]?$', s):
                        continue
                    parsed = parse_dialogue_line(s)
                    if not parsed:
                        continue
                    num, skiri, english = parsed
                    if not skiri:
                        continue
                    if num is not None or current_ex is None:
                        current_ex = {'lines': []}
                        exchanges.append(current_ex)
                    if english or skiri:
                        current_ex['lines'].append(
                            {'skiri': skiri, 'english': english})
                # drop empty exchanges
                exchanges = [e for e in exchanges if e['lines']]
                cur['dialogues'].extend(exchanges)
        else:
            prose = clean_prose(section_lines)
            if prose and len(prose) > 40:
                cur['grammar_notes'].append(
                    {'heading': cur_section.rstrip(':').title(),
                     'text': prose})
        section_lines = []
        cur_section = None

    title_window = 0   # lines remaining in which to look for the English title

    for raw in lines:
        s = raw.strip()
        m = PAGE_NUM_RE.match(s)
        if m:
            page = int(m.group(1))
            continue
        if PAGE_RE.match(s) or BROKEN_PAGE_RE.match(s):
            continue

        lm = LESSON_RE.match(s)
        if lm and 'LESSON' in s and len(s) < 60:
            flush_section()
            num = int(lm.group(2)) if lm.group(2) else prev_lesson_num + 1
            skiri_title = lm.group(1).strip() or None
            # a Skiri title may also sit on the previous line
            if not skiri_title and looks_skiri_title(last_nonempty):
                skiri_title = last_nonempty.strip()
            if cur:
                cur['page_end'] = page
            cur = {
                'lesson_number': num,
                'skiri_title': skiri_title,
                'english_title': None,
                'page_start': page,
                'page_end': None,
                'dialogues': [],
                'grammar_notes': [],
                'templates': LESSON_TEMPLATES.get(num, []),
            }
            lessons[num] = cur
            prev_lesson_num = num
            cur_section = None
            section_lines = []
            title_window = 4
            last_nonempty = s
            continue

        # English title: within a few lines of the header, a line that has
        # lowercase letters and starts uppercase (not a vocab item, not a
        # section header). Page reflow can push it later — the post-scan
        # below catches those.
        if cur and cur['english_title'] is None and title_window > 0 and s:
            title_window -= 1
            if (not HEADER_RE.match(s) and s[0].isupper()
                    and any(ch.islower() for ch in s)
                    and len(s.split()) >= 2 and 6 <= len(s) < 50):
                cur['english_title'] = s
                last_nonempty = s
                continue

        if cur and HEADER_RE.match(s) and not re.match(r'^\d', s):
            flush_section()
            cur_section = s.rstrip(':')
            last_nonempty = s
            continue

        if cur_section is not None:
            section_lines.append(raw)
        elif cur and cur['english_title'] is None and TITLE_SCAN_RE.match(s):
            # reflow-displaced title (e.g. L04 'What Do You Have?')
            cur['english_title'] = s
        if s:
            last_nonempty = s

    if cur:
        cur['page_end'] = page
        flush_section()

    # post-scan: reflow can bury a title INSIDE an item section (L04's sits
    # at the end of BASIC WORDS) — recover from section text if still missing
    return lessons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true',
                    help='write lessons table to DB (default: dry-run)')
    args = ap.parse_args()
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    log(f"=== Phase 5.1 lesson build — {mode} — {datetime.now().isoformat()} ===")

    text = BB_TEXT.read_text(encoding='utf-8')
    lessons = parse_lessons(text)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT lesson_number, "
                "sum(context_type IN ('BASIC_WORDS','ADDITIONAL_WORDS')), "
                "sum(context_type IN ('BASIC_WORDS','ADDITIONAL_WORDS') "
                "    AND entry_id IS NOT NULL) "
                "FROM blue_book_attestations GROUP BY lesson_number")
    vocab_counts = {r[0]: (r[1] or 0, r[2] or 0) for r in cur.fetchall()}

    log(f"lessons parsed: {len(lessons)}")
    for n in sorted(lessons):
        L = lessons[n]
        nvocab, nlinked = vocab_counts.get(n, (0, 0))
        n_dlg_lines = sum(len(e['lines']) for e in L['dialogues'])
        log(f"  L{n:02d} p{L['page_start']}-{L['page_end']} "
            f"{(L['english_title'] or '?')[:38]!r:40s} "
            f"skiri={(L['skiri_title'] or '')[:28]!r:30s} "
            f"dlg={len(L['dialogues'])}ex/{n_dlg_lines}ln "
            f"notes={len(L['grammar_notes'])} vocab={nvocab}({nlinked} linked) "
            f"tmpl={','.join(L['templates'])}")

    # sample dialogue + note for eyeballing
    if 1 in lessons and lessons[1]['dialogues']:
        log("\nsample L1 dialogue exchange:")
        for line in lessons[1]['dialogues'][0]['lines']:
            log(f"    {line['skiri']!r}  =  {line['english']!r}")
    if 1 in lessons and lessons[1]['grammar_notes']:
        gn = lessons[1]['grammar_notes'][0]
        log(f"\nsample L1 note [{gn['heading']}]: {gn['text'][:180]}...")

    OUT_JSON.parent.mkdir(exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump([lessons[n] for n in sorted(lessons)], f,
                  ensure_ascii=False, indent=1)
    log(f"\n[write] {OUT_JSON}")

    if args.apply:
        cur.execute("DROP TABLE IF EXISTS lessons")
        cur.execute("""
            CREATE TABLE lessons (
                lesson_number  INTEGER PRIMARY KEY,
                skiri_title    TEXT,
                english_title  TEXT,
                page_start     INTEGER,
                page_end       INTEGER,
                dialogues      TEXT,   -- JSON: [{lines:[{skiri,english}]}]
                grammar_notes  TEXT,   -- JSON: [{heading,text}]
                template_ids   TEXT    -- JSON: ["T1","T3"]
            )""")
        for n in sorted(lessons):
            L = lessons[n]
            cur.execute(
                "INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?)",
                (n, L['skiri_title'], L['english_title'],
                 L['page_start'], L['page_end'],
                 json.dumps(L['dialogues'], ensure_ascii=False),
                 json.dumps(L['grammar_notes'], ensure_ascii=False),
                 json.dumps(L['templates'])))
        con.commit()
        log(f"[DB] lessons table written: {len(lessons)} rows")
    else:
        log("DRY-RUN: DB not modified. Re-run with --apply.")
    con.close()

    REPORT.write_text('\n'.join(LOG), encoding='utf-8')
    log(f"[report] {REPORT}")


if __name__ == '__main__':
    main()
