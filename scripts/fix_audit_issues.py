#!/usr/bin/env python3
"""
fix_audit_issues.py — Apply fixes for the 2026-09-01 extraction audit findings
==============================================================================
Report: reports/extraction_audit_2026-09-01.md

Fixes applied (in dependency order):
  7a. JSON phonetic_form bracket drift        (JSON := DB's bracketed value, 44 entries)
  7b. Backport DB N-KIN reclassifications     (DB -> JSON, 9 entries)
  3.  Recover missing phonetic_forms          (from PDF page index, skeleton-validated)
  4.  OCR artifacts in E2S JSON + S2E etym    (÷->ː etc.; ÷ only after a vowel outside
                                               phonetic fields; the rest are logged)
  6.  Line-break hyphens + ’->ʔ + leading •   (paradigmatic forms, example skiri_text)
  1.  c->č under-conversion                   (recompute normalized_form + simplified
                                               with the fixed ts-aware disambiguator)
  DB. Push all field changes to skiri_pawnee.db
  5.  Dedup doubled examples in DB            (post ’->ʔ normalization)
  2.  Gloss table migration + reinsert        (drop UNIQUE(entry_id, sense_number),
                                               allow NULL sense_number, restore lost senses)

Usage:
  python scripts/fix_audit_issues.py             # dry-run (default): report only
  python scripts/fix_audit_issues.py --apply     # write JSON + DB (backs up both first)

Dependencies: stdlib only.
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from respell_and_normalize import (
    generate_normalized_form,
    generate_simplified_pronunciation,
)

ROOT = Path(__file__).resolve().parent.parent
S2E_PATH = ROOT / 'Dictionary Data' / 'skiri_to_english_respelled.json'
E2S_PATH = ROOT / 'Dictionary Data' / 'english_to_skiri_linked.json'
DB_PATH = ROOT / 'skiri_pawnee.db'
PAGE_INDEX = ROOT / 'reports' / '_s2e_page_index.json'
BACKUP_DIR = Path(os.environ.get('OneDrive', str(Path.home()))) / 'pari_pakuru_backups'  # synced, not single-disk
REPORT_PATH = ROOT / 'reports' / 'fix_audit_issues_report.txt'

OCR_MAP = {'÷': 'ː', 'ˆ': 'ɪ', '‹': 'ʊ', 'Ò': 'a', 'ç': 'ʔ', 'ø': 'ː'}
VOWELS = set('aiuáíúàìùɪʊəeo')

LOG = []


def log(s):
    LOG.append(s)
    sys.stdout.buffer.write((s + '\n').encode('utf-8', errors='replace'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACC = {'á': 'a', 'í': 'i', 'ú': 'u', 'à': 'a', 'ì': 'i', 'ù': 'u'}


def skeleton(s, phonetic=False):
    """Consonant skeleton for headword<->phonetic validation."""
    if not s:
        return ''
    s = ''.join(ACC.get(ch, ch) for ch in s).lower()
    s = re.sub(r'\(\w+\.\.\.\)', '', s)
    s = re.sub(r'\[\+.*?\]', '', s)
    s = re.sub(r'\{([^}/]+)/[^}]*\}', r'\1', s)   # {k/t} -> k
    if phonetic:
        s = s.replace('ts', 'c')
    for ch in '[]•–—()-.,+ /':
        s = s.replace(ch, '')
    s = (s.replace('ɪ', 'i').replace('ʊ', 'u').replace('ə', 'a')
          .replace('ː', '').replace('č', 'c'))
    s = re.sub(r'[aiu]', '', s)
    return s.replace('ʔ', '')


def fix_skiri_text(s, join_hyphens=False):
    """Normalize curly apostrophe, strip leading bullet; optionally join
    line-break hyphens.  Hyphen joining is ONLY safe for verb paradigm forms
    (single inflected words) — example sentences legitimately contain
    compound-numeral hyphens (tawiraaruʔ-ruksiriʔ-asku 'seventy-one')."""
    if not s:
        return s
    orig = s
    s = s.replace('’', 'ʔ')                     # ’ -> ʔ
    s = re.sub(r'^[•]\s*', '', s)                    # leading bullet
    if join_hyphens:
        s = re.sub(r'(?<=[a-zA-Zʔáíúàìù])- ?(?=[a-zA-Zʔáíúàìù])', '', s)
    return s if s != orig else orig


def walk_strings(obj, fn, path=''):
    """Recursively apply fn(path, string) -> new_string to every str in obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                nv = fn(path + '.' + k, v)
                if nv != v:
                    obj[k] = nv
            else:
                walk_strings(v, fn, path + '.' + k)
    elif isinstance(obj, list):
        for item in obj:
            walk_strings(item, fn, path + '[]')


# ---------------------------------------------------------------------------
# Fix functions (each returns a summary dict; mutates in-memory data only)
# ---------------------------------------------------------------------------

def fix_7a_brackets(s2e, dbcur):
    dbcur.execute("SELECT entry_id, phonetic_form FROM lexical_entries")
    dbpf = dict(dbcur.fetchall())
    n = 0
    for e in s2e:
        pI = e.get('part_I') or {}
        jpf = pI.get('phonetic_form')
        dpf = dbpf.get(e['entry_id'])
        if jpf and dpf and jpf != dpf and dpf == '[' + jpf + ']':
            pI['phonetic_form'] = dpf
            n += 1
    log(f"[7a] bracket drift fixed in JSON: {n} entries")
    return n


def fix_7b_nkin(s2e, dbcur):
    dbcur.execute("SELECT entry_id, grammatical_class FROM lexical_entries")
    dbgc = dict(dbcur.fetchall())
    n = 0
    for e in s2e:
        gi = (e.get('part_I') or {}).get('grammatical_info') or {}
        jgc = gi.get('grammatical_class')
        dgc = dbgc.get(e['entry_id'])
        if jgc and dgc and jgc != dgc:
            log(f"  [7b] {e['entry_id']}: JSON class {jgc!r} := DB {dgc!r}")
            gi['grammatical_class'] = dgc
            n += 1
    log(f"[7b] grammatical_class backported DB->JSON: {n} entries")
    return n


def fix_3_missing_phonetics(s2e):
    index = json.load(open(PAGE_INDEX, encoding='utf-8'))
    alltext = '\n'.join(v['text'] for v in index.values())
    applied, review = [], []
    for e in s2e:
        pI = e.get('part_I') or {}
        if (pI.get('phonetic_form') or '').strip():
            continue
        hw = (e.get('headword') or '').split(',')[0].strip()
        if not hw:
            continue
        # bracketed phonetic within ~40 chars of the headword; may span lines
        m = re.search(re.escape(hw) + r'[^\[\]]{0,40}?\[([^\]]{2,90})\]',
                      alltext, re.DOTALL)
        if not m:
            review.append((e['entry_id'], hw, 'no bracketed form found'))
            continue
        cand = re.sub(r'\s+', '', m.group(1))
        if not re.search(r'[əɪʊaiuáíúàìù]', cand):
            review.append((e['entry_id'], hw, f'not IPA-like: {cand[:40]}'))
            continue
        if skeleton(hw) != skeleton(cand, phonetic=True):
            review.append((e['entry_id'], hw, f'skeleton mismatch: [{cand[:50]}]'))
            continue
        pf = '[' + cand + ']'
        pI['phonetic_form'] = pf
        applied.append((e['entry_id'], hw, pf))
    log(f"[3] missing phonetic_form recovered: {len(applied)} "
        f"(needs manual review: {len(review)})")
    for eid, hw, pf in applied:
        log(f"  [3] RECOVERED {eid} {hw!r} -> {pf}")
    for eid, hw, why in review:
        log(f"  [3] REVIEW    {eid} {hw!r}: {why}")
    return applied, review


def fix_4_ocr_artifacts(s2e, e2s):
    counts = Counter()
    unresolved = []

    def fix_field(path, s):
        field = path.rsplit('.', 1)[-1]
        if field.endswith('_id') or field == 'entry_id':
            return s  # never touch identifiers (the Ø entry's slug contains ø)
        if not any(ch in s for ch in OCR_MAP):
            return s
        if field in ('phonetic_form', 'skiri_form'):
            for bad, good in OCR_MAP.items():
                if bad in s:
                    counts[f'{bad}->{good} ({field})'] += s.count(bad)
                    s = s.replace(bad, good)
            return s
        # elsewhere (etymology, cognates, glosses): ÷ -> ː only after a vowel;
        # leave every other artifact character alone outside phonetic fields
        out_chars = []
        for i, ch in enumerate(s):
            if ch == '÷':
                if i > 0 and s[i - 1] in VOWELS:
                    out_chars.append('ː')
                    counts[f'÷->ː ({field}, vowel-context)'] += 1
                else:
                    out_chars.append(ch)
                    unresolved.append((path, s[max(0, i - 12):i + 8]))
            else:
                out_chars.append(ch)
        return ''.join(out_chars)

    walk_strings(e2s, fix_field)
    walk_strings(s2e, fix_field)
    log(f"[4] OCR artifact replacements: {sum(counts.values())}")
    for k, v in counts.most_common():
        log(f"  [4] {k}: {v}")
    log(f"  [4] unresolved ÷ (non-vowel context, left for manual review): "
        f"{len(unresolved)}")
    for p, ctx in unresolved[:20]:
        log(f"      {p}: ...{ctx}...")
    return counts, unresolved


def fix_6_skiri_text(s2e):
    n_para = n_ex = 0
    ex_hyphens = []
    for e in s2e:
        pII = e.get('part_II') or {}
        pf = pII.get('paradigmatic_forms') or {}
        for k, v in list(pf.items()):
            if isinstance(v, str):
                nv = fix_skiri_text(v, join_hyphens=True)
                if nv != v:
                    pf[k] = nv
                    n_para += 1
            elif isinstance(v, list):  # additional_forms
                for af in v:
                    if isinstance(af, dict) and isinstance(af.get('form'), str):
                        nv = fix_skiri_text(af['form'], join_hyphens=True)
                        if nv != af['form']:
                            af['form'] = nv
                            n_para += 1
        for ex in pII.get('examples') or []:
            st = ex.get('skiri_text')
            if isinstance(st, str):
                nv = fix_skiri_text(st)  # no hyphen join in examples
                if nv != st:
                    ex['skiri_text'] = nv
                    n_ex += 1
                if '-' in (nv or ''):
                    ex_hyphens.append((e['entry_id'], nv))
    log(f"[6] JSON skiri-text cleanups: {n_para} paradigm forms, {n_ex} examples")
    log(f"  [6] example texts containing hyphens (compound numerals are "
        f"legitimate; review for line-break leaks): {len(ex_hyphens)}")
    for eid, st in ex_hyphens[:20]:
        log(f"      {eid}: {st[:70]!r}")
    return n_para, n_ex


def fix_1_recompute(s2e):
    changed_norm, changed_pron = [], []
    for e in s2e:
        hw = e.get('headword') or ''
        pI = e.get('part_I') or {}
        pf = pI.get('phonetic_form') or ''
        if hw.strip():
            norm, _ = generate_normalized_form(hw, pf)
            old = e.get('normalized_form')
            if norm and norm != old:
                changed_norm.append((e['entry_id'], hw, old, norm))
                e['normalized_form'] = norm
        if pf.strip():
            pron, _ = generate_simplified_pronunciation(pf)
            old = pI.get('simplified_pronunciation')
            if pron and pron != old:
                changed_pron.append((e['entry_id'], old, pron))
                pI['simplified_pronunciation'] = pron
    log(f"[1] normalized_form changed: {len(changed_norm)} | "
        f"simplified_pronunciation changed: {len(changed_pron)}")
    for eid, hw, old, new in changed_norm:
        log(f"  [1] {eid}: {old!r} -> {new!r}")
    for eid, old, new in changed_pron[:15]:
        log(f"  [1-pron] {eid}: {old!r} -> {new!r}")
    if len(changed_pron) > 15:
        log(f"  [1-pron] ... and {len(changed_pron) - 15} more")
    return changed_norm, changed_pron


# ---------------------------------------------------------------------------
# DB push
# ---------------------------------------------------------------------------

def db_push_lexical(s2e, cur):
    cur.execute("SELECT entry_id, headword, normalized_form, phonetic_form, "
                "simplified_pronunciation FROM lexical_entries")
    dbrows = {r[0]: r for r in cur.fetchall()}
    n = 0
    for e in s2e:
        r = dbrows.get(e['entry_id'])
        if not r:
            continue
        pI = e.get('part_I') or {}
        vals = (e.get('normalized_form'), pI.get('phonetic_form'),
                pI.get('simplified_pronunciation'))
        if (r[2], r[3], r[4]) != vals:
            cur.execute(
                "UPDATE lexical_entries SET normalized_form=?, phonetic_form=?, "
                "simplified_pronunciation=? WHERE entry_id=?",
                (*vals, e['entry_id']))
            n += 1
    log(f"[DB] lexical_entries rows updated: {n}")
    return n


def db_fix_text_tables(cur):
    n_para = n_ex = 0
    cur.execute("SELECT id, skiri_form FROM paradigmatic_forms")
    for rid, v in cur.fetchall():
        nv = fix_skiri_text(v, join_hyphens=True)
        if nv != v:
            cur.execute("UPDATE paradigmatic_forms SET skiri_form=? WHERE id=?",
                        (nv, rid))
            n_para += 1
    cur.execute("SELECT id, skiri_text FROM examples")
    for rid, v in cur.fetchall():
        nv = fix_skiri_text(v)
        if nv != v:
            cur.execute("UPDATE examples SET skiri_text=? WHERE id=?", (nv, rid))
            n_ex += 1
    log(f"[DB] text cleanups: {n_para} paradigmatic_forms, {n_ex} examples")
    return n_para, n_ex


def fix_5_dedup_examples(cur):
    """After ’->ʔ normalization, doubled dedup-merge examples are near-exact.
    Keep the row whose english_translation has no line-break hyphen."""
    cur.execute("SELECT id, entry_id, skiri_text, english_translation FROM examples")
    groups = {}
    for rid, eid, st, tr in cur.fetchall():
        key = (eid, re.sub(r'\s+', ' ', (st or '').strip()))
        groups.setdefault(key, []).append((rid, tr or ''))
    deleted = 0
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        # prefer translation without mid-word hyphenation, then longest
        rows.sort(key=lambda r: (1 if re.search(r'\w-\s*\w', r[1]) else 0,
                                 -len(r[1])))
        keep = rows[0][0]
        for rid, _ in rows[1:]:
            cur.execute("DELETE FROM examples WHERE id=?", (rid,))
            deleted += 1
        log(f"  [5] {key[0]}: kept #{keep}, deleted "
            f"{[r[0] for r in rows[1:]]} for {key[1][:40]!r}")
    log(f"[5] duplicate example rows deleted: {deleted}")
    return deleted


def fix_2_glosses(cur, s2e, affected_ids):
    """Migrate glosses table: drop UNIQUE(entry_id, sense_number), allow NULL
    sense_number; reinsert full gloss sets for entries that lost senses."""
    # 1. capture trigger SQL so we can recreate them
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' "
                "AND name LIKE 'glosses_%'")
    triggers = cur.fetchall()
    # 2. rebuild table without UNIQUE and with nullable sense_number
    cur.execute("""
        CREATE TABLE glosses_new (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id        TEXT NOT NULL REFERENCES lexical_entries(entry_id),
            sense_number    INTEGER,
            definition      TEXT NOT NULL,
            usage_notes     TEXT
        )""")
    cur.execute("INSERT INTO glosses_new SELECT id, entry_id, sense_number, "
                "definition, usage_notes FROM glosses")
    for name, _ in triggers:
        cur.execute(f"DROP TRIGGER {name}")
    cur.execute("DROP TABLE glosses")
    cur.execute("ALTER TABLE glosses_new RENAME TO glosses")
    for _, sql in triggers:
        cur.execute(sql)
    # 3. reinsert lost senses for affected entries (delete + full reinsert)
    by_id = {e['entry_id']: e for e in s2e}
    n_re = 0
    for eid in affected_ids:
        e = by_id.get(eid)
        if not e:
            continue
        glosses = (e.get('part_I') or {}).get('glosses') or []
        cur.execute("DELETE FROM glosses WHERE entry_id=?", (eid,))
        last_num = 0
        for g in glosses:
            num = g.get('number')
            if num is None:
                # derive: leading "2a."-style digit in the definition, else
                # continue from the previous sense (NULL would sort first in
                # the ORDER BY sense_number LIMIT 1 queries used everywhere)
                m = re.match(r'\s*(\d+)[a-z]?\.', g.get('definition') or '')
                num = int(m.group(1)) if m else last_num + 1
            last_num = max(last_num, num)
            cur.execute(
                "INSERT INTO glosses (entry_id, sense_number, definition, "
                "usage_notes) VALUES (?,?,?,?)",
                (eid, num, g.get('definition'), g.get('usage_notes')))
            n_re += 1
        log(f"  [2] {eid}: reinserted {len(glosses)} glosses")
    # 4. rebuild FTS to be safe (rowids for reinserted rows changed)
    cur.execute("INSERT INTO fts_glosses(fts_glosses) VALUES('rebuild')")
    log(f"[2] glosses table migrated (UNIQUE dropped, NULL allowed); "
        f"{n_re} gloss rows reinserted for {len(affected_ids)} entries")
    return n_re


def find_gloss_loss(cur, s2e):
    """Entries whose JSON gloss count exceeds the DB's (the UNIQUE-victims)."""
    cur.execute("SELECT entry_id, count(*) FROM glosses GROUP BY entry_id")
    dbc = dict(cur.fetchall())
    out = []
    for e in s2e:
        jn = len((e.get('part_I') or {}).get('glosses') or [])
        if jn and jn > dbc.get(e['entry_id'], 0) and e['entry_id'] in dbc:
            out.append(e['entry_id'])
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--apply', action='store_true',
                    help='write changes (default is dry-run)')
    args = ap.parse_args()
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    log(f"=== fix_audit_issues.py — {mode} — {datetime.now().isoformat()} ===")

    s2e = json.load(open(S2E_PATH, encoding='utf-8'))
    e2s = json.load(open(E2S_PATH, encoding='utf-8'))
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # identify gloss-loss victims BEFORE any changes
    gloss_victims = find_gloss_loss(cur, s2e)
    log(f"[2] entries with gloss loss to restore: {len(gloss_victims)} "
        f"{gloss_victims}")

    # in-memory JSON fixes
    fix_7a_brackets(s2e, cur)
    fix_7b_nkin(s2e, cur)
    fix_3_missing_phonetics(s2e)
    fix_4_ocr_artifacts(s2e, e2s)
    fix_6_skiri_text(s2e)
    fix_1_recompute(s2e)

    if not args.apply:
        log("\nDRY-RUN complete — no files or DB modified. "
            "Re-run with --apply to write.")
        REPORT_PATH.write_text('\n'.join(LOG), encoding='utf-8')
        log(f"Report written to {REPORT_PATH}")
        return

    # ---- APPLY ----
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for src in (DB_PATH, S2E_PATH, E2S_PATH):
        dst = BACKUP_DIR / f"{src.stem}_backup_{stamp}{src.suffix}"
        shutil.copy2(src, dst)
        log(f"[backup] {dst}")

    with open(S2E_PATH, 'w', encoding='utf-8') as f:
        json.dump(s2e, f, ensure_ascii=False, indent=2)
    log(f"[write] {S2E_PATH}")
    with open(E2S_PATH, 'w', encoding='utf-8') as f:
        json.dump(e2s, f, ensure_ascii=False, indent=2)
    log(f"[write] {E2S_PATH}")

    db_push_lexical(s2e, cur)
    db_fix_text_tables(cur)
    fix_5_dedup_examples(cur)
    fix_2_glosses(cur, s2e, gloss_victims)
    cur.execute("INSERT INTO fts_examples(fts_examples) VALUES('rebuild')")
    con.commit()
    con.close()
    log("[DB] committed")

    REPORT_PATH.write_text('\n'.join(LOG), encoding='utf-8')
    log(f"Report written to {REPORT_PATH}")


if __name__ == '__main__':
    main()
