#!/usr/bin/env python3
"""
Phase 3.1 — Accent Mark Assignment Rules
==========================================

Analyzes and validates pitch accent placement rules for Skiri Pawnee
verb forms, targeting the 85 accented Appendix 1 forms.

The accent marks (á í ú) indicate HIGH PITCH in Skiri. Pitch is phonemic
— wrong accent = wrong word. The conjugation engine currently produces
forms without accents ("close" matches). This script validates accent
placement rules that would convert those close matches to exact.

IMPACT: If all 85 accented forms are correctly predicted,
Appendix 1 accuracy jumps from 76.2% → 87.3% (587+85=672/770).

RULES IDENTIFIED (from analysis of 85 attested accented forms):

Rule A — Agent-boundary í:
  After agent consonant (t- 1.A, s- 2.A), the first SHORT i from
  a subsequent morpheme receives high pitch accent.
  Applies to i from: ir(aak) PL, acir- INCL, ih compound, ir- PREV, i- SEQ
  Does NOT apply to long ii (which is from the stem/preverb, not a boundary).
  Examples:
    ta + t + í + raak... → tatíraakaahuʔ (1pl_excl indicative)
    ta + s + í + raak... → tasíraakaahuʔ (2pl indicative)
    ta + c + í + hwa...  → tacíhwaʔaʔ (1du_incl indicative)

Rule B — Mode-prefix accent:
  B1: Assertive rii- → rí (accent on first i, before agent)
  B2: Contingent i- (1/2 person) → í (word-initial accent)
  B3: Gerundial irii-ra- → írii-ra- (word-initial accent)

Rule C — Infinitive kú:
  In infinitive mode, the INF.B marker ku receives accent → kú.
  Applies to ALL person/numbers in infinitive mode.

Rule D — Dual sí:
  The dual proclitic si- receives accent sí- in:
  - Absolutive mode (ra-)
  - Assertive mode (rii-)
  - Negative mode (kaakaa-/kaaki-)
  But NOT in:
  - Indicative mode (ta-/ti-)
  - Contingent mode (i-/ri-)
  - Subjunctive mode (aa-/ii-)

Usage:
    python accent_rules.py --validate    # test against 85 Appendix 1 forms
    python accent_rules.py --analyze     # show accent patterns
"""

import os
import re
import sqlite3
import sys
from collections import defaultdict
from typing import Optional, List, Tuple, Dict

ACCENT_MAP = {'a': 'á', 'i': 'í', 'u': 'ú'}
DEACCENT_MAP = str.maketrans('áíúàìù', 'aiuaiu')

def strip_accents(form: str) -> str:
    """Remove all accent marks from a form."""
    return form.translate(DEACCENT_MAP)


def apply_accent_rules(
    form: str,
    mode: str,
    person_number: str,
    morpheme_labels: List[str] = None,
) -> str:
    """
    Apply pitch accent rules to a generated verb form.
    
    Rules derived from analysis of 85 Appendix 1 accented forms:
    
    Rule A — AGENT_BOUNDARY í (63 cases):
      The first SHORT i after an agent consonant (t/s/c) gets high pitch.
      "Short i" = not followed by another i (which would be long ii from stem).
      Agent consonants: t (1.A), s (2.A), c (from acir- INCL or ut+i affrication).
      Applies in ALL modes.
    
    Rule B — MODE PREFIX accent (21 cases):
      B1: Assertive rii- → rí at word-start (or sirí after dual si-).
          Applies when agent is present (not 3sg/3pl/3du without dual).
      B2: Contingent i- → í (1sg/2sg only — singular forms).
      B3: Gerundial irii- → írii- (ALL person/numbers).
    
    Rule C — INFINITIVE kú (12 cases):
      The INF.B marker ku always gets accent → kú in infinitive mode.
    
    Rule D — DUAL sí (subset of forms):
      Dual proclitic si- → sí in absolutive, assertive, and negative modes.
      NOT in indicative, contingent, subjunctive, potential, gerundial, infinitive.
    """
    if not form:
        return form
    
    result = list(form)
    is_dual = 'du' in person_number
    agent = _get_agent_consonant(person_number)
    
    # ── Rule C: Infinitive kú (highest priority — always applies) ──
    if 'infinitive' in mode:
        for i in range(1, len(result) - 1):
            if result[i] == 'k' and result[i+1] == 'u':
                result[i+1] = 'ú'
                break  # only first ku
        return ''.join(result)  # infinitive forms ONLY have kú accent
    
    # ── Rule B3: Gerundial írii- (word-initial) ──────────────────
    if 'gerundial' in mode:
        if result[0] == 'i':
            result[0] = 'í'
    
    # ── Rule B1: Assertive rí ────────────────────────────────────
    if 'assertive' in mode:
        if is_dual:
            # Dual: si + rii → look for ri after si
            for i in range(1, min(5, len(result))):
                if result[i] == 'r' and i + 1 < len(result) and result[i+1] == 'i':
                    # Check it's the assertive prefix r+i, not stem r+i
                    # In dual assertive, rii appears at position 2-4 (after si)
                    result[i+1] = 'í'
                    break
        elif agent is not None:
            # Non-dual with agent: rii → rí at word start
            if result[0] == 'r' and len(result) > 1 and result[1] == 'i':
                result[1] = 'í'
    
    # ── Rule B2: Contingent í (1sg/2sg only) ─────────────────────
    if 'contingent' in mode and person_number in ('1sg', '2sg'):
        if result[0] == 'i':
            result[0] = 'í'
    
    # ── Rule D: Dual sí in absolutive/negative (NOT assertive 1/2 person) ──
    if is_dual and form.startswith('si'):
        apply_si = False
        if 'absolutive' in mode:
            apply_si = True
        elif 'negative' in mode:
            apply_si = True
        elif 'assertive' in mode and person_number == '3du':
            # Assertive: only 3du gets sí (1du/2du get assertive rí instead)
            apply_si = True
        
        if apply_si:
            result[1] = 'í'
    
    # ── Rule A: Agent-boundary í (most broadly applicable) ───────
    # The first SHORT i after agent consonant t/s/c gets accent.
    # "Short" = the i comes from a PREFIX (ir-, acir-, ih-), not from the stem.
    # Heuristic: skip if the i is followed by another i AND the person is
    # singular AND the mode is not gerundial (gerundial 2sg has s+ír from PREV).
    is_singular = person_number in ('1sg', '2sg', '3sg')
    is_gerundial = 'gerundial' in mode
    
    if agent in ('t', 's'):
        for i in range(1, len(result)):
            if result[i] == agent:
                if i + 1 < len(result) and result[i+1] in ('i', 'í'):
                    is_long = (i + 2 < len(result) and result[i+2] in ('i', 'í'))
                    if is_long and is_singular and not is_gerundial:
                        continue  # skip — this is stem long ii
                    result[i+1] = 'í'
                    break
    
    # 1du_incl: acir- → c is the agent-like consonant
    if person_number == '1du_incl':
        for i in range(len(result)):
            if result[i] == 'c' and i + 1 < len(result) and result[i+1] in ('i', 'í'):
                is_long = (i + 2 < len(result) and result[i+2] in ('i', 'í'))
                if not is_long:
                    result[i+1] = 'í'
                    break
    
    # ── Rule A2: ut-affrication cí (for "to do it" type) ────────
    # When ut- + i-SEQ → uc + i, the i after uc gets accent.
    # This is NOT the agent — it's the sequential marker after affrication.
    # Detect: any 'c' followed by short 'i' followed by 'ʔ' (characteristic
    # of this pattern in potential mode forms).
    if 'potential' in mode:
        for i in range(2, len(result)):
            if result[i] == 'c' and i + 1 < len(result) and result[i+1] in ('i', 'í'):
                is_long = (i + 2 < len(result) and result[i+2] in ('i', 'í'))
                if not is_long:
                    result[i+1] = 'í'
                    # Don't break — only set last c+i (the one closest to stem)
    
    # ── Comma-separated forms: apply rules to each variant ───────
    # Some forms are "form1, form2" — handle by splitting, applying, rejoining
    # (already handled by splitting in validation, not needed here)
    
    # ── Stem accents (verb-specific, 4 forms) ────────────────────
    # "to be good" negative 2sg/2du: ...uuhíi (accent on stem hiir surface)
    # "to have it" assertive 1du_excl/1pl_excl: siriiháa (accent on stem haa)
    # These are rare and verb-specific; not handled by general rules.
    
    return ''.join(result)


def _get_agent_consonant(person_number: str) -> Optional[str]:
    """Return the agent consonant prefix for a person/number."""
    AGENTS = {
        '1sg': 't', '2sg': 's',
        '1du_incl': None,  # uses acir- inclusive
        '1du_excl': 't', '2du': 's', '3du': None,
        '1pl_incl': 't', '1pl_excl': 't', '2pl': 's', '3pl': None,
        '3sg': None,
    }
    return AGENTS.get(person_number)


def _find_agent_position(form: str, mode: str, person_number: str, agent: str) -> Optional[int]:
    """
    Find the position of the agent consonant in the surface form.
    
    The agent consonant position depends on the mode prefix length.
    """
    # Determine mode prefix length in the surface form
    if 'indicative' in mode and 'negative' not in mode:
        prefix_len = 2  # ta- or ti-
    elif 'negative' in mode:
        prefix_len = 6  # kaakaa- or kaaki-
        if person_number.startswith('3'):
            prefix_len = 6  # kaaki- has 5 but contracts
    elif 'assertive' in mode:
        prefix_len = 2  # rii- → rí or ri (contracted)
    elif 'contingent' in mode:
        prefix_len = 1  # i- or ri- (for 3rd person)
        if person_number.startswith('3'):
            return None  # ri- for contingent 3rd has no agent
    elif 'absolutive' in mode:
        prefix_len = 2  # ra-
    elif 'potential' in mode:
        if person_number.startswith('1') or person_number.startswith('3'):
            prefix_len = 4  # kuus-
        else:
            prefix_len = 4  # kaas-
    elif 'subjunctive' in mode:
        prefix_len = 2  # aa- or ii-
    elif 'gerundial' in mode:
        prefix_len = 4  # irii- + ra- = iriira, but varies
        # Gerundial has complex prefix; skip for now
        return None
    elif 'infinitive' in mode:
        prefix_len = 2  # ra-
    else:
        return None
    
    # The agent should be at prefix_len (the character right after the mode prefix)
    # But this is approximate — sound changes may shift positions
    for i in range(max(0, prefix_len - 1), min(len(form), prefix_len + 3)):
        if i < len(form) and form[i] == agent:
            return i
    
    return None


def _find_infinitive_ku(form: str, person_number: str) -> Optional[int]:
    """Find the position of the infinitive ku marker in the surface form."""
    # In infinitive forms, ku appears after the mode+agent+preverb complex
    # Look for 'ku' not at the very start
    for i in range(2, len(form) - 1):
        if form[i] == 'k' and form[i+1] == 'u':
            return i
    return None


# ─── Validation ──────────────────────────────────────────────────

def validate_against_appendix1(db_path: str) -> Dict:
    """Validate accent rules against all 85 accented Appendix 1 forms."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    ACCENT_CHARS = set('áíúàìù')
    
    cur = conn.execute("""
        SELECT verb_heading, mode, person_number, skiri_form
        FROM verb_paradigms
        WHERE skiri_form IS NOT NULL
        ORDER BY verb_heading, mode, person_number
    """)
    
    total_accented = 0
    correct = 0
    wrong = 0
    missed = 0
    results = []
    
    for r in cur:
        attested = r['skiri_form']
        has_accent = any(c in ACCENT_CHARS for c in attested)
        
        if not has_accent:
            continue
        
        total_accented += 1
        
        # Handle comma-separated variant forms
        attested_parts = [p.strip() for p in attested.split(',')]
        
        if len(attested_parts) > 1:
            # Apply rules to each variant separately
            predicted_parts = []
            for part in attested_parts:
                unaccented_part = strip_accents(part)
                predicted_part = apply_accent_rules(
                    unaccented_part, mode=r['mode'], person_number=r['person_number'],
                )
                predicted_parts.append(predicted_part)
            predicted = ', '.join(predicted_parts)
            unaccented = ', '.join(strip_accents(p) for p in attested_parts)
        else:
            # Strip accents from attested form → this is what the engine produces
            unaccented = strip_accents(attested)
            predicted = apply_accent_rules(
                unaccented, mode=r['mode'], person_number=r['person_number'],
            )
        
        if predicted == attested:
            status = 'correct'
            correct += 1
        elif strip_accents(predicted) == strip_accents(attested):
            # Accent placement wrong but base form correct
            status = 'wrong_accent'
            wrong += 1
        else:
            status = 'error'
            missed += 1
        
        results.append({
            'verb': r['verb_heading'],
            'mode': r['mode'],
            'pn': r['person_number'],
            'attested': attested,
            'predicted': predicted,
            'unaccented': unaccented,
            'status': status,
        })
    
    conn.close()
    
    return {
        'total': total_accented,
        'correct': correct,
        'wrong': wrong,
        'missed': missed,
        'accuracy': round(100 * correct / total_accented, 1) if total_accented else 0,
        'results': results,
    }


def print_validation_report(results: Dict):
    """Print accent validation report."""
    print("=" * 70)
    print("ACCENT MARK VALIDATION — Appendix 1")
    print("=" * 70)
    print(f"Total accented forms: {results['total']}")
    print(f"Correct:             {results['correct']} ({results['accuracy']}%)")
    print(f"Wrong accent pos:    {results['wrong']}")
    print(f"Errors:              {results['missed']}")
    
    if results['total'] > 0:
        print(f"\nImpact on Appendix 1: 587 + {results['correct']} = "
              f"{587 + results['correct']}/770 = "
              f"{100*(587+results['correct'])/770:.1f}% exact (was 76.2%)")
    
    # Show failures
    failures = [r for r in results['results'] if r['status'] != 'correct']
    if failures:
        print(f"\n{'─'*70}")
        print(f"FAILURES ({len(failures)}):")
        print(f"{'─'*70}")
        for f in failures[:30]:
            print(f"  [{f['status']:>13}] {f['verb']:<12} {f['mode']:<35} {f['pn']:<12}")
            print(f"    attested:  {f['attested']}")
            print(f"    predicted: {f['predicted']}")
            print(f"    unaccent:  {f['unaccented']}")
            print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Accent mark analysis and validation")
    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skiri_pawnee.db")
    parser.add_argument("--db", default=default_db, help="Path to SQLite database")
    parser.add_argument("--validate", action="store_true", help="Validate accent rules")
    parser.add_argument("--analyze", action="store_true", help="Show accent patterns")
    args = parser.parse_args()
    
    if args.validate:
        results = validate_against_appendix1(args.db)
        print_validation_report(results)
    elif args.analyze:
        print("Run --validate to see accent rule accuracy")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
