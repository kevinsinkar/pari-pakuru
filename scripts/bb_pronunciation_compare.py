#!/usr/bin/env python3
"""
Phase 2.2 (Optional Follow-up) -- BB Pronunciation Comparison
=============================================================
Extracts pronunciation guides from the Blue Book raw text, normalizes OCR
artifacts, matches words to Parks dictionary entries, and compares the two
pronunciation systems side-by-side.

Background
----------
The Blue Book uses a learner orthography with parenthetical pronunciation
guides: e.g., "rakis (rd-kis) wood". These guides use hyphens to show
syllable breaks. OCR artifacts: stressed vowels (written with a dot accent)
are captured by OCR as the consonant preceding 'd' (e.g., 'rd' = r + stressed-a,
'pd' = p + stressed-a, 'kd' = k + stressed-a).

The Parks dictionary stores 'simplified_pronunciation' -- an English-phonemic
approximation system (e.g., "DUH-kihs" for 'rakis'). These are different
systems and not trivially comparable, but side-by-side inspection reveals
patterns:
  - Parks 'DUH' ~ BB 'ra' (tapped r + short a)
  - Parks 'dih' ~ BB 'ri'
  - Parks 'kihs' ~ BB 'kis'
  - Parks long vowel: 'ooh' ~ BB 'uu'
  - Parks glottal: "uh-oh" ~ BB apostrophe '

Layout patterns in the Blue Book text
--------------------------------------
Three distinct formats appear:
  1. Inline:   "word (pron) gloss"  -- all on one line
  2. Column:   words in one vertical block, (pron) in matching block below
  3. Preceding: (pron) alone on its own line, word on immediately preceding line

Usage
-----
    python scripts/bb_pronunciation_compare.py \\
        --text "pari pakuru/Blue_Book_Pari_Pakuru.txt" \\
        --db skiri_pawnee.db \\
        --report reports/phase_2_2_pronunciation.txt

Dependencies: Python 3.8+, sqlite3 (stdlib)
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# OCR normalization for BB pronunciation guides
# ---------------------------------------------------------------------------

# In BB pronunciation guides, stress-dotted vowels were OCR'd as consonant+'d'
# because the dot accent on 'a' (a-with-dot-above) looks like 'd' to OCR.
# No Pawnee consonant inventory includes 'd', so any 'd' in a pron guide is
# an OCR artifact for a stress-marked 'a'.
_OCR_D_RE = re.compile(r'(?<=[bcdfghjklmnpqrstvwxyz])d(?=[^a-z]|$|-)', re.IGNORECASE)


def normalize_bb_pron(raw: str) -> str:
    """
    Clean OCR artifacts from a BB pronunciation guide.

    - consonant+'d' -> consonant+'a'  (stress-dotted 'a' OCR artifact)
    - Collapse multiple spaces
    - Strip leading/trailing whitespace and parens
    """
    s = raw.strip().strip('()')
    s = _OCR_D_RE.sub('a', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def bare_form(pron: str) -> str:
    """Strip hyphens, apostrophes, spaces for approximate comparison."""
    return re.sub(r"[-' ]", '', pron.lower())


# ---------------------------------------------------------------------------
# Extract BB pronunciation pairs from raw text
# ---------------------------------------------------------------------------

_ENGLISH_STOPWORDS = {
    'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was',
    'been', 'when', 'they', 'have', 'which', 'what', 'then', 'but',
    'also', 'each', 'some', 'any', 'all', 'you', 'he', 'she', 'it',
    'caddoan', 'south', 'band', 'skidi', 'pawnee', 'english', 'see',
    'note', 'pronunciation', 'vowels', 'short', 'long', 'word', 'words',
    'or', 'not', 'is', 'in', 'of', 'to', 'a', 'an', 'on', 'as', 'at',
    'by', 'be', 'do', 'go', 'up', 'so', 'if',
}

# A bare pronunciation line: just (pron) possibly with trailing space
_PRON_BARE_RE = re.compile(r'^\s*\(([a-zA-Z\'\-\. ]{3,50})\)\s*$')
# Pronunciation followed by a gloss on same line
_PRON_GLOSS_RE = re.compile(r'^\s*\(([a-zA-Z\'\-\. ]{3,50})\)\s+([A-Za-z].{0,60})$')
# Inline: word (pron) [optional gloss]
_INLINE_RE = re.compile(
    r'^([A-Za-z\'\u2022\u2019\u02BC\-]+(?:\s+[A-Za-z\'\u2022\u2019\-]+)?)'
    r'\s+\(([a-zA-Z\'\-\. ]{3,50})\)\s*(.*)$'
)
# A bare Pawnee word line (short, no spaces, has Pawnee characteristics)
_PAWNEE_WORD_RE = re.compile(
    r'^([A-Za-z\'\u2022\u2019\u02BC\-]{2,25})$'
)


def _is_pawnee_word(s: str) -> bool:
    """Heuristic: does this line look like a bare Pawnee word?"""
    s = s.strip()
    if not s or s.lower() in _ENGLISH_STOPWORDS:
        return False
    if not _PAWNEE_WORD_RE.match(s):
        return False
    sl = s.lower()
    # Must contain a Pawnee-characteristic sequence (most English words won't)
    pawnee_signal = (
        "'" in s or '\u2022' in s
        or any(sub in sl for sub in [
            'ts', 'ks', 'ra', 'ri', 'ru', 'ta', 'ti', 'tu',
            'ka', 'ki', 'ku', 'su', 'sa', 'si', 'ha', 'hi', 'hu',
            'wa', 'wi', 'wu', 'rr',
        ])
    )
    return pawnee_signal


def extract_pron_pairs(text: str, lesson_pages_only: bool = True) -> list[dict]:
    """
    Scan BB text and return list of {word, raw_pron, clean_pron, gloss, page, source}.

    Handles three layout patterns:
      1. Inline:   "word (pron) gloss"  -- all on one line
      2. Column:   block of Pawnee words then matching block of (pron) lines
      3. Preceding: (pron) on its own line, word on the immediately preceding line
    """
    page_blocks = re.split(r'={10,}\s*\nPAGE (\d+)\s*\n={10,}', text)
    pages = {}
    for i in range(1, len(page_blocks), 2):
        pages[int(page_blocks[i])] = page_blocks[i + 1] if i + 1 < len(page_blocks) else ""

    pairs = []
    seen = set()

    # English phoneme sequences that would never appear in a Pawnee pronunciation guide
    _ENGLISH_PRON_SIGNALS = ('ing', 'ight', 'tion', 'ness', 'ment', 'ful', 'less',
                              'ough', 'tion', 'ight', 'atch', 'atch')

    def _add(word, raw_pron, gloss, page, source):
        if '-' not in raw_pron:
            return
        # Reject obvious English compound expressions (e.g., "sight-seeing")
        rp_lower = raw_pron.lower()
        if any(sig in rp_lower for sig in _ENGLISH_PRON_SIGNALS):
            return
        clean_word = (word or '').strip()
        clean_pron = normalize_bb_pron(raw_pron)
        key = (clean_word.lower(), clean_pron)
        if key in seen:
            return
        seen.add(key)
        pairs.append({
            'word': clean_word or None,
            'raw_pron': '(' + raw_pron + ')',
            'clean_pron': clean_pron,
            'gloss': gloss or None,
            'page': page,
            'source': source,
        })

    for page_num in sorted(pages.keys()):
        if lesson_pages_only and page_num < 29:
            continue

        lines = pages[page_num].split('\n')
        n = len(lines)

        # Pass 1: Inline patterns on a single line
        for line in lines:
            m = _INLINE_RE.match(line.strip())
            if m:
                word, raw_pron, gloss = m.group(1), m.group(2), m.group(3).strip()
                # Reject if word is English
                if not word.lower().strip() in _ENGLISH_STOPWORDS:
                    _add(word.strip(), raw_pron, gloss or None, page_num, 'inline')

        # Pass 2: Column-block detection
        # Find runs of Pawnee word lines, then look for a matching-size pron block
        # Track which line indices are part of column blocks to avoid re-use in Pass 3
        column_pron_lines = set()  # line indices of pron lines consumed by column blocks
        i = 0
        while i < n:
            line = lines[i].strip()
            if _is_pawnee_word(line):
                # Collect word block
                word_block = []
                word_line_indices = []
                j = i
                while j < n and _is_pawnee_word(lines[j].strip()):
                    word_block.append(lines[j].strip())
                    word_line_indices.append(j)
                    j += 1
                if len(word_block) < 2:
                    i += 1
                    continue
                # Skip blanks
                while j < n and not lines[j].strip():
                    j += 1
                # Collect pron block
                pron_block = []
                pron_line_indices = []
                k = j
                while k < n:
                    l = lines[k].strip()
                    bm = _PRON_BARE_RE.match(l)
                    gm = _PRON_GLOSS_RE.match(l)
                    if bm:
                        pron_block.append((bm.group(1), None))
                        pron_line_indices.append(k)
                        k += 1
                    elif gm:
                        pron_block.append((gm.group(1), gm.group(2).strip()))
                        pron_line_indices.append(k)
                        k += 1
                    elif not l:
                        k += 1
                    else:
                        break
                if len(pron_block) == len(word_block):
                    # Mark these pron lines as consumed
                    column_pron_lines.update(pron_line_indices)
                    # Collect optional gloss block after pron block
                    gloss_block = []
                    g = k
                    while g < n and not lines[g].strip():
                        g += 1
                    for _ in range(len(word_block)):
                        if g < n and lines[g].strip() and not _PRON_BARE_RE.match(lines[g]):
                            gloss_block.append(lines[g].strip())
                            g += 1
                        else:
                            gloss_block.append(None)
                    for idx in range(len(word_block)):
                        pron_raw, pron_gloss = pron_block[idx]
                        gloss = (pron_gloss or
                                 (gloss_block[idx] if idx < len(gloss_block) else None))
                        _add(word_block[idx], pron_raw, gloss, page_num, 'column')
                i = max(i + 1, j)
            else:
                i += 1

        # Pass 3: Preceding-line pattern -- (pron) alone, word on line before
        # Skip lines already consumed by column-block detection
        for idx in range(n):
            if idx in column_pron_lines:
                continue
            pm = _PRON_BARE_RE.match(lines[idx].strip())
            if not pm:
                continue
            raw_pron = pm.group(1)
            # Look back for a Pawnee word on the immediately preceding non-blank line
            word = None
            for back in range(idx - 1, max(idx - 3, -1), -1):
                candidate = lines[back].strip()
                if not candidate:
                    continue
                if _is_pawnee_word(candidate):
                    word = candidate
                break
            # Gloss: next non-blank line that isn't another pron
            gloss = None
            for fwd in range(idx + 1, min(idx + 3, n)):
                candidate = lines[fwd].strip()
                if not candidate:
                    continue
                if not _PRON_BARE_RE.match(candidate) and not candidate.startswith('='):
                    gloss = candidate
                break
            _add(word, raw_pron, gloss, page_num, 'preceding')

    return pairs


# ---------------------------------------------------------------------------
# Match BB pronunciation pairs to dictionary entries
# ---------------------------------------------------------------------------

def normalize_for_lookup(word: str) -> str:
    """Normalize a BB word form for dictionary lookup."""
    if not word:
        return ''
    s = word.lower()
    s = s.replace('\u2022', '').replace("'", '\u0294').replace('ts', 'c')
    s = re.sub(r'[^a-z\u0294\u00e1\u00e0\u00ed\u00ec\u00fa\u00f9\u00e2\u00ee\u00fb\u0101\u012b\u016b]', '', s)
    return s


def _fold_long_vowels(s: str) -> str:
    """Collapse doubled vowels to single for fuzzy matching (aa->a, ii->i, uu->u)."""
    return re.sub(r'([aiu])\1+', r'\1', s)


def build_lookup_index(conn: sqlite3.Connection) -> dict:
    """Build {key: (entry_id, headword, simplified_pronunciation)} lookup map."""
    cur = conn.cursor()
    cur.execute("SELECT entry_id, headword, normalized_form, simplified_pronunciation FROM lexical_entries")
    index = {}
    for eid, hw, nf, sp in cur.fetchall():
        if nf:
            key = nf.lower().strip()
            if key not in index:
                index[key] = (eid, hw, sp)
        hw_key = normalize_for_lookup(hw or '')
        if hw_key and hw_key not in index:
            index[hw_key] = (eid, hw, sp)
    # Also add long-vowel-folded keys for fuzzy matching
    # This lets BB 'hitu' match Parks 'hiitu', BB 'raku' match 'raaku', etc.
    folded = {}
    for key, val in list(index.items()):
        fk = _fold_long_vowels(key)
        if fk and fk not in index and fk not in folded:
            folded[fk] = val
    index.update(folded)
    return index


def build_gloss_index(conn: sqlite3.Connection) -> dict:
    """Build {english_gloss_word: (entry_id, headword, simplified_pronunciation)} from english_index."""
    cur = conn.cursor()
    cur.execute("""
        SELECT ei.english_word, ei.skiri_term, le.entry_id, le.headword, le.simplified_pronunciation
        FROM english_index ei
        LEFT JOIN lexical_entries le ON (
            le.headword = ei.skiri_term OR le.normalized_form = ei.skiri_term
        )
        WHERE ei.skiri_term IS NOT NULL
    """)
    gloss_idx = {}
    for ew, skiri, eid, hw, sp in cur.fetchall():
        if ew and eid:
            key = ew.lower().strip()
            if key not in gloss_idx:
                gloss_idx[key] = (eid, hw, sp)
    return gloss_idx


def match_pair_to_dict(pair: dict, index: dict, gloss_index: dict = None):
    """
    Try to match a BB word to a dictionary entry.
    Returns (entry_id, headword, simplified_pronunciation) or (None, None, None).
    """
    word = pair.get('word', '') or ''

    # 1. Direct normalized lookup
    key = normalize_for_lookup(word)
    if key and key in index:
        return index[key]

    # 2. Bullet-stripped
    cleaned = re.sub(r'\u2022', '', word).strip()
    key2 = normalize_for_lookup(cleaned)
    if key2 and key2 in index:
        return index[key2]

    # 3. Long-vowel-folded (BB shortens long vowels, Parks has full form)
    folded = _fold_long_vowels(key) if key else ''
    if folded and folded != key and folded in index:
        return index[folded]

    # 4. Gloss-based fallback (use single-word gloss to find Parks entry)
    # Skip proper nouns / tribal names that map to multi-word Parks entries
    _SKIP_GLOSSES = {'pawnee', 'skiri', 'english', 'skidi', 'south', 'band'}
    if gloss_index and pair.get('gloss'):
        gloss_word = pair['gloss'].split()[0].lower().rstrip('.,;()')
        if gloss_word not in _SKIP_GLOSSES and gloss_word in gloss_index:
            return gloss_index[gloss_word]

    return None, None, None


# ---------------------------------------------------------------------------
# Compare two pronunciation strings
# ---------------------------------------------------------------------------

def compare_pronunciations(bb_clean: str, parks_sp) -> dict:
    """
    Compare BB cleaned pronunciation with Parks simplified_pronunciation.

    Returns {'agreement': 'exact'|'close'|'different'|'no_parks', 'notes': [...]}
    """
    if not parks_sp:
        return {'agreement': 'no_parks', 'notes': ['No Parks simplified_pronunciation available']}

    bb_bare = bare_form(bb_clean)
    parks_bare = bare_form(parks_sp)

    if bb_bare == parks_bare:
        return {'agreement': 'exact', 'notes': ['Exact match after normalization']}

    notes = []
    bb_sylls = [s for s in bb_clean.split('-') if s]
    parks_sylls = [s for s in parks_sp.split('-') if s]

    if len(bb_sylls) == len(parks_sylls):
        notes.append('Same syllable count (%d)' % len(bb_sylls))
    else:
        notes.append('Syllable count: BB=%d, Parks=%d' % (len(bb_sylls), len(parks_sylls)))

    parks_lower = parks_sp.lower()
    if 'duh' in parks_lower and bb_clean.startswith('r'):
        notes.append("Parks 'DUH' = BB 'ra' (tapped r + short a)")
    if 'dih' in parks_lower and 'ri' in bb_clean:
        notes.append("Parks 'dih' = BB 'ri' (tapped r + i)")
    if 'ooh' in parks_lower and ('uu' in bb_clean or "u'" in bb_clean):
        notes.append("Parks 'ooh' = BB long-u")
    if 'ee' in parks_lower and 'ii' in bb_clean:
        notes.append("Parks 'ee' = BB long-i (ii)")

    # Character-set overlap heuristic
    bb_set = set(bb_bare)
    parks_set = set(parks_bare)
    overlap = len(bb_set & parks_set) / max(len(bb_set | parks_set), 1)
    if overlap < 0.4 and not notes:
        notes.append('Low character overlap (%.0f%%) -- likely different notation conventions' % (overlap * 100))

    agreement = 'close' if overlap > 0.5 or notes else 'different'
    return {'agreement': agreement, 'notes': notes}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(pairs: list, matched_pairs: list) -> str:
    """Build and return pronunciation comparison report text."""
    n_matched = sum(1 for p in matched_pairs if p['entry_id'])
    n_with_parks = sum(1 for p in matched_pairs if p['parks_sp'])
    n_exact = sum(1 for p in matched_pairs if p.get('comparison', {}).get('agreement') == 'exact')
    n_close = sum(1 for p in matched_pairs if p.get('comparison', {}).get('agreement') == 'close')
    n_diff = sum(1 for p in matched_pairs if p.get('comparison', {}).get('agreement') == 'different')
    n_noparks = sum(1 for p in matched_pairs if p.get('comparison', {}).get('agreement') == 'no_parks')

    lines = [
        '=' * 70,
        'PHASE 2.2 -- BLUE BOOK PRONUNCIATION COMPARISON',
        'Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '=' * 70,
        '',
        'BACKGROUND',
        '-' * 40,
        'The Blue Book uses parenthetical pronunciation guides with hyphenated',
        'syllables. OCR captured stress-dotted vowels as consonant+d sequences',
        "  e.g. 'rd' = tapped-r + stressed-a, 'pd' = p + stressed-a.",
        '',
        'Parks dictionary uses an English-phonemic approximation system:',
        '  "DUH-kihs" for rakis (wood). These are different notation systems.',
        '',
        'Known systematic correspondences:',
        '  Parks "DUH"  ~ BB "ra"  (tapped r + short a)',
        '  Parks "dih"  ~ BB "ri"  (tapped r + i)',
        '  Parks "ooh"  ~ BB "uu"  (long u)',
        '  Parks "ee"   ~ BB "ii"  (long i)',
        '  Parks "ih"   ~ BB "i"   (short i)',
        '  Parks "uh"   ~ BB "a"   (short a / schwa)',
        '',
        'SUMMARY',
        '-' * 40,
        'Total BB pronunciation guides found: %d  (lesson pages 29+)' % len(pairs),
        'Guides matched to dictionary entry:  %d' % n_matched,
        'With Parks simplified_pronunciation: %d' % n_with_parks,
        '',
        'Comparison results:',
        '  Exact match (after normalization): %d' % n_exact,
        '  Close / systematic correspondence: %d' % n_close,
        '  Different:                         %d' % n_diff,
        '  No Parks simplified_pron:          %d' % n_noparks,
        '',
        'DETAIL -- ALL PRONUNCIATION PAIRS',
        '-' * 40,
        '',
    ]

    markers = {'exact': '[=]', 'close': '[~]', 'different': '[!]', 'no_parks': '[-]'}

    for p in matched_pairs:
        word = p.get('word') or '(unknown)'
        raw = p.get('raw_pron', '')
        clean = p.get('clean_pron', '')
        gloss = p.get('gloss') or ''
        page = p.get('page', '?')
        hw = p.get('headword') or '(no match)'
        parks_sp = p.get('parks_sp') or '(none)'
        cmp = p.get('comparison', {})
        agreement = cmp.get('agreement', 'no_parks')
        notes = cmp.get('notes', [])
        marker = markers.get(agreement, '[?]')

        lines.append('%s p.%s  BB word: %s' % (marker, page, repr(word)))
        lines.append('         BB raw:   %s' % raw)
        # Only show cleaned form if it differs from raw
        raw_inner = raw.strip('()')
        if clean != raw_inner:
            lines.append('         BB clean: %s' % clean)
        lines.append('         Parks hw: %-25s  simplified: %s' % (hw, parks_sp))
        if gloss:
            lines.append('         Gloss: %s' % gloss)
        if notes:
            lines.append('         Notes: %s' % '; '.join(notes))
        lines.append('')

    unmatched = [p for p in matched_pairs if not p.get('entry_id')]
    lines += [
        '',
        'UNMATCHED BB PRONUNCIATION GUIDES',
        '-' * 40,
        '(BB word could not be matched to a Parks dictionary entry)',
        '',
    ]
    if unmatched:
        for p in unmatched:
            word = p.get('word') or '(word unknown)'
            raw = p.get('raw_pron', '')
            clean = p.get('clean_pron', '')
            gloss = p.get('gloss') or ''
            raw_inner = raw.strip('()')
            lines.append('  p.%3s  %-30s  %s' % (p['page'], repr(word), raw))
            if clean != raw_inner:
                lines.append('         cleaned: %s' % clean)
            if gloss:
                lines.append('         gloss: %s' % gloss)
    else:
        lines.append('  (none -- all guides matched)')

    lines += [
        '',
        'LEGEND',
        '-' * 40,
        '[=] exact match after normalization (strip hyphens/apostrophes/spaces)',
        '[~] close / systematic correspondence (e.g., Parks DUH ~ BB ra)',
        '[!] different -- may indicate dialect variant or orthographic mismatch',
        '[-] no Parks simplified_pronunciation available for this entry',
    ]

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Phase 2.2 -- Blue Book Pronunciation Comparison'
    )
    parser.add_argument('--text', default='pari pakuru/Blue_Book_Pari_Pakuru.txt')
    parser.add_argument('--db', default='skiri_pawnee.db')
    parser.add_argument('--extracted', default='blue_book_extracted.json')
    parser.add_argument('--report', default='reports/phase_2_2_pronunciation.txt')
    parser.add_argument('--all-pages', action='store_true',
                        help='Include front matter pages 1-28')
    args = parser.parse_args()

    text_path = Path(args.text)
    db_path = Path(args.db)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not text_path.exists():
        print('ERROR: Blue Book text not found: %s' % text_path, file=sys.stderr)
        sys.exit(1)

    # Step 1: Extract pronunciation pairs
    bb_text = text_path.read_text(encoding='utf-8')
    lesson_only = not args.all_pages
    pairs = extract_pron_pairs(bb_text, lesson_pages_only=lesson_only)
    print('Found %d pronunciation pairs (lesson pages %s)'
          % (len(pairs), '29+' if lesson_only else '1+'))

    # Step 2: Build DB lookup indexes
    conn = sqlite3.connect(str(db_path))
    lookup_index = build_lookup_index(conn)
    gloss_index = build_gloss_index(conn)

    # Step 3: Match each pair to a dictionary entry
    matched_pairs = []
    for pair in pairs:
        entry_id, headword, parks_sp = match_pair_to_dict(pair, lookup_index, gloss_index)

        # Query parks_sp directly if we have entry_id but no sp yet
        if entry_id and not parks_sp:
            cur = conn.cursor()
            cur.execute(
                'SELECT simplified_pronunciation, headword FROM lexical_entries WHERE entry_id = ?',
                (entry_id,)
            )
            row = cur.fetchone()
            if row:
                parks_sp, headword = row

        comparison = compare_pronunciations(pair['clean_pron'], parks_sp)
        matched_pairs.append({
            **pair,
            'entry_id': entry_id,
            'headword': headword,
            'parks_sp': parks_sp,
            'comparison': comparison,
        })

    conn.close()

    # Step 4: Generate and write report
    report_text = generate_report(pairs, matched_pairs)
    report_path.write_text(report_text, encoding='utf-8')
    print('Report written to: %s' % report_path)
    sys.stdout.buffer.write((report_text + '\n').encode('utf-8', errors='replace'))


if __name__ == '__main__':
    main()
