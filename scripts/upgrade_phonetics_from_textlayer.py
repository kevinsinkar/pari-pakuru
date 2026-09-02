#!/usr/bin/env python3
"""
Upgrade degraded phonetic_forms from the PDF text layer (cross-validation).
=============================================================================

Method: the dictionary was extracted twice by independent paths — an AI
vision model (the production JSON/DB) and pdftotext (the PDF's embedded text
layer, saved in reports/_s2e_page_index.json). Cross-validating all 4,273
entries (2026-09-01) found 96.7% exact agreement and 123 entries where the
AI extraction kept plain ASCII (a/i/u/c) while the text layer preserves the
true printed IPA (ə/ɪ/ʊ/č + pitch accents).

This script adopts the text-layer phonetic ONLY when it is provably safe:
  A. plain-ASCII skeletons are identical and the text layer is strictly
     richer (adds ə/ɪ/ʊ/č or accents) — no information is contradicted;
  B. the forms differ only in accent marks and the text layer has more
     (accents were the most OCR-damaged characters);
  C. four manually reviewed d=1 conflicts where the HEADWORD corroborates
     the text layer (a dropped long-vowel letter in the AI transcription).

After upgrading, normalized_form and simplified_pronunciation are
regenerated for the affected entries and pushed to the DB.

Usage:
  python scripts/upgrade_phonetics_from_textlayer.py            # dry-run
  python scripts/upgrade_phonetics_from_textlayer.py --apply
"""

import argparse
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from respell_and_normalize import (
    generate_normalized_form,
    generate_simplified_pronunciation,
)

ROOT = Path(__file__).resolve().parent.parent
S2E_PATH = ROOT / 'Dictionary Data' / 'skiri_to_english_respelled.json'
DB_PATH = ROOT / 'skiri_pawnee.db'
PAGE_INDEX = ROOT / 'reports' / '_s2e_page_index.json'
BACKUP_DIR = Path.home() / '.pari_pakuru_backups'
REPORT_PATH = ROOT / 'reports' / 'phonetic_textlayer_upgrade.txt'

# Manually reviewed conflicts (case C): headword corroborates the text layer.
CONFLICT_WHITELIST = {
    'SK-haakaawatatuuk-p33-0562',
    'SK-kisaactacapahtuq-p98-1884',
    'SK-raarakaahki-p122-2378',
    'SK-taakaar-p502-4233',
}

ACC = {'á': 'a', 'í': 'i', 'ú': 'u', 'à': 'a', 'ì': 'i', 'ù': 'u'}
OCR = {'÷': 'ː', 'ˆ': 'ɪ', '‹': 'ʊ', 'Ò': 'a', 'ç': 'ʔ', 'ø': 'ː'}
RICH = set('əɪʊč')

LOG = []


def log(s):
    LOG.append(s)
    sys.stdout.buffer.write((s + '\n').encode('utf-8', errors='replace'))


def strip_acc(s):
    return ''.join(ACC.get(ch, ch) for ch in s)


def fix_ocr(s):
    return ''.join(OCR.get(ch, ch) for ch in s)


def plainify(s):
    s = strip_acc(s)
    return (s.replace('ə', 'a').replace('ɪ', 'i').replace('ʊ', 'u')
             .replace('č', 'c').replace('ː', ''))


def norm_pf(s):
    if not s:
        return ''
    s = re.sub(r'\s+', '', s)
    return s.replace('[', '').replace(']', '')


def edist(a, b):
    if abs(len(a) - len(b)) > 6:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def n_accents(s):
    return sum(1 for ch in s if ch in ACC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true',
                    help='write changes (default: dry-run)')
    args = ap.parse_args()
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    log(f"=== phonetic text-layer upgrade — {mode} — "
        f"{datetime.now().isoformat()} ===")

    s2e = json.load(open(S2E_PATH, encoding='utf-8'))
    index = json.load(open(PAGE_INDEX, encoding='utf-8'))
    fulltext = '\n'.join(index[p]['text']
                         for p in sorted(index, key=lambda x: int(x)))

    upgrades = []   # (entry, old_pf, new_pf, reason)
    for e in s2e:
        hw = (e.get('headword') or '').strip()
        pI = e.get('part_I') or {}
        pf = pI.get('phonetic_form') or ''
        if not hw or not pf.startswith('['):
            continue
        hw_key = hw.split(',')[0].strip()
        pat = re.compile(re.escape(hw_key) + r'[^\[\]]{0,40}?\[([^\]]{2,120})\]',
                         re.DOTALL)
        cands = [fix_ocr(norm_pf(m)) for m in pat.findall(fulltext)]
        if not cands:
            continue
        stored = norm_pf(pf)
        best = min(cands, key=lambda c: edist(c, stored))
        d = edist(best, stored)
        if d == 0:
            continue

        reason = None
        if plainify(best) == plainify(stored):
            pdf_rich = sum(1 for c in best if c in RICH) + n_accents(best)
            db_rich = sum(1 for c in stored if c in RICH) + n_accents(stored)
            if pdf_rich > db_rich:
                reason = 'A: text layer strictly richer IPA'
        if reason is None and strip_acc(best) == strip_acc(stored):
            if n_accents(best) > n_accents(stored):
                reason = 'B: text layer has attested accents'
        if reason is None and e['entry_id'] in CONFLICT_WHITELIST:
            reason = 'C: reviewed conflict, headword corroborates text layer'
        if reason is None:
            continue
        upgrades.append((e, pf, '[' + best + ']', reason))

    log(f"upgrades identified: {len(upgrades)}")
    for e, old, new, reason in upgrades:
        log(f"  {e['entry_id']} ({reason})")
        log(f"     old: {old}")
        log(f"     new: {new}")

    # regenerate derived fields for upgraded entries
    changed_norm = changed_pron = 0
    for e, old, new, reason in upgrades:
        pI = e['part_I']
        pI['phonetic_form'] = new
        norm, _ = generate_normalized_form(e.get('headword') or '', new)
        if norm and norm != e.get('normalized_form'):
            log(f"     normalized_form: {e.get('normalized_form')!r} -> {norm!r}")
            e['normalized_form'] = norm
            changed_norm += 1
        pron, _ = generate_simplified_pronunciation(new)
        if pron and pron != pI.get('simplified_pronunciation'):
            pI['simplified_pronunciation'] = pron
            changed_pron += 1
    log(f"derived fields regenerated: {changed_norm} normalized_form, "
        f"{changed_pron} simplified_pronunciation")

    if not args.apply:
        log("\nDRY-RUN complete — nothing written. Re-run with --apply.")
        REPORT_PATH.write_text('\n'.join(LOG), encoding='utf-8')
        return

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for src in (DB_PATH, S2E_PATH):
        dst = BACKUP_DIR / f"{src.stem}_backup_{stamp}{src.suffix}"
        shutil.copy2(src, dst)
        log(f"[backup] {dst}")

    with open(S2E_PATH, 'w', encoding='utf-8') as f:
        json.dump(s2e, f, ensure_ascii=False, indent=2)
    log(f"[write] {S2E_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    n = 0
    for e, old, new, reason in upgrades:
        pI = e['part_I']
        cur.execute(
            "UPDATE lexical_entries SET phonetic_form=?, normalized_form=?, "
            "simplified_pronunciation=? WHERE entry_id=?",
            (new, e.get('normalized_form'),
             pI.get('simplified_pronunciation'), e['entry_id']))
        n += cur.rowcount
    con.commit()
    con.close()
    log(f"[DB] rows updated: {n}")
    REPORT_PATH.write_text('\n'.join(LOG), encoding='utf-8')
    log(f"Report: {REPORT_PATH}")


if __name__ == '__main__':
    main()
