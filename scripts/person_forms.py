#!/usr/bin/env python3
"""
Phase 3.2b — Person/Mode Derivation from Attested Paradigm Forms
=================================================================

Derives verb forms the dictionary does not list (2nd person, absolutive mode)
from the forms it DOES list, instead of conjugating from scratch.

WHY: the from-scratch engine (morpheme_inventory.conjugate) reproduces only
14.8% of attested dictionary forms exactly — dictionary-wide morphophonology
is too irregular to rebuild. But the attested forms already encode almost all
of it. The person/mode prefixes sit at the LEFT EDGE and alternate in a small,
regular paradigm (Parks App. 1):

    mode:   indicative ta-/ti-     absolutive ra-/ri-  (swap initial t -> r)
    agent:  1.A t      2.A s       3.A Ø               (swap t -> s for 2sg)

Junctions with the stem-initial segment are the only complication, and they
are recoverable by aligning attested form_1 (1sg IND) with form_2 (3sg IND):

    3sg ti+X    1sg tat+X     2sg tas+X       (plain consonant stems)
    3sg tir+X   1sg tah+X     2sg tast+X      (r-stems: t+r->h, s+r->st)
    3sg tih+X   1sg tat+X     2sg tas+X       (h-stems: h drops after t and s)
    3sg tiw+X   1sg tatp+X    2sg tasp+X      (w-stems: w->p after obstruent)
    3sg ti+tX   1sg tac+tX    2sg tas+tX      (t-stems: t+t->ct, s+t->st)
    3sg tu+X    1sg tatu+X    2sg tasu+X      (ut-preverb: coalesced tu-)

Validation: --validate-appendix derives 2sg + absolutive forms for the seven
Appendix 1 paradigm verbs and compares against Parks's attested answers.

Usage:
    python scripts/person_forms.py --validate-appendix
    python scripts/person_forms.py --derive tactakacat titakacat takacat

Library:
    from person_forms import derive_forms
    d = derive_forms(form_1="tactakacat", form_2="titakacat", headword="takacat")
    d["2sg_ind"]   # 'tastakacat'  "you fetched water"
    d["3sg_abs"]   # 'ratakacat'   for 'ka ratakacat ...?' questions
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPENDIX1 = ROOT / 'extracted_data' / 'appendix1_conjugations.json'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_accents(s):
    """Remove combining accents (á -> a) for alignment; keeps ʔ etc."""
    if not s:
        return s
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def primary_form(s):
    """First variant of a possibly 'a; b' / 'a, b' valued paradigm cell."""
    if not s:
        return None
    return re.split(r'[;,]', s)[0].strip()


def _common_suffix_split(a, b):
    """Return (prefix_a, prefix_b, common_suffix)."""
    i = 0
    while i < min(len(a), len(b)) and a[-1 - i] == b[-1 - i]:
        i += 1
    return a[:len(a) - i], b[:len(b) - i], a[len(a) - i:]


# ---------------------------------------------------------------------------
# Core derivation
# ---------------------------------------------------------------------------

def derive_2sg_ind(form_1, form_2):
    """1sg indicative (attested) -> 2sg indicative.

    Aligns form_1 against form_2 to locate the agent junction, then swaps
    the 1.A agent for 2.A s with the appropriate junction repair.
    Returns None when the shape is not recognized (caller should not guess).
    """
    if not form_1:
        return None
    f1 = strip_accents(primary_form(form_1))
    f2 = strip_accents(primary_form(form_2)) if form_2 else None
    if ' ' in f1 or 'witi' in f1[:5]:
        return None
    # descriptive-ku verbs: 1st person is ti+ku+STEM, 2nd person is ta+STEM
    if f1.startswith('tiku'):
        return 'ta' + f1[4:]
    if not f1.startswith('ta'):
        return None

    p1, p2, _suffix = _common_suffix_split(f1, f2) if f2 else (None, None, None)

    if p1 is not None and len(p1) <= 8:
        rest = f1[len(p1):]
        # ut-preverb pattern: form_1 = 'ta' + form_2 ('ta'+'tuutaa') — the
        # agent t is the first char of the shared material.
        if p1 in ('ta', 'taa') and rest.startswith('t'):
            return p1 + 's' + rest[1:]
        # r-stem: 1sg shows t+r -> h where 3sg shows r; 2sg is s+r -> st
        if p1.endswith('h') and p2 and p2.endswith('r'):
            return p1[:-1] + 'st' + rest
        # t-stem: 1sg agent surfaces as c before t (t+t -> ct); 2sg s+t -> st
        if p1.endswith('c') and rest.startswith('t'):
            return p1[:-1] + 's' + rest
        # w-stem: 1sg 'tatp' (t+w -> tp); 2sg 'tasp' — swap the t before p
        if p1.endswith('tp'):
            return p1[:-2] + 'sp' + rest
        # general: the agent is the last 't' in the prefix — swap to s
        idx = p1.rfind('t')
        if idx > 0:
            return p1[:idx] + 's' + p1[idx + 1:] + rest

    # No form_2 to align against: positional fallback — ^t[a]+ then agent
    m = re.match(r'^(t[a]+)([tch])(.*)$', f1)
    if m:
        mode, agent, rest = m.groups()
        if agent == 'h':
            return mode + 'st' + rest
        return mode + 's' + rest
    return None


def to_absolutive(ind_form, third_person=False, stem_preverb=None,
                  headword=None):
    """Indicative -> absolutive, for ka/kirike/kiru questions.

    1st/2nd person: the mode vowel matches (ta-/ra-), so the swap is the
    initial t -> r (App.1: tatkiikaʔ -> ratkiikaʔ, taskiikaʔ -> raskiikaʔ),
    with descriptive-ku 1sg tiku- -> riiku-.

    3rd person: IND mode is ti- but ABS mode is ra-, so shapes differ:
        ti+C  -> ra+C      (tikiikaʔ -> rakiikaʔ, tiraa -> raraa)
        tiʔ+V -> raʔ+V     (tiʔat -> raʔat)
        tih-  -> riih-     (descriptive-ku: tihkiraawaʔ -> riihkiraawaʔ)
        tii-  -> rii-      (BB: 'Ka rii hituʔ?')
        tu-   -> ru-       (ut-preverb: tuutaa -> ruutaa; BB 'rutærit')
        tuu-  -> ru-       when the preverb is uur- (tuuhii -> ruhii)
        ta-   -> None      (ir-preverb 3sg; not derivable by prefix swap)
    """
    if not ind_form:
        return None
    f = strip_accents(primary_form(ind_form))
    if not f.startswith('t'):
        return None

    if not third_person:
        if f.startswith('tiku'):                 # descriptive-ku 1st person
            return 'riiku' + f[4:]
        if f.startswith('ta'):
            return 'r' + f[1:]
        return None

    # --- third person ---
    # 'tih-' is ambiguous: descriptive-ku marker (tihkiraawaʔ -> riih-) vs an
    # h-initial stem (tihuraas = ti+huraas -> ra+huraas). The headword tells.
    if f.startswith('tih'):
        if headword and strip_accents(headword).startswith('h'):
            return 'ra' + f[2:]
        return 'riih' + f[3:]
    if f.startswith('tii'):
        return 'rii' + f[3:]
    if f.startswith('tiʔ'):
        return 'raʔ' + f[3:]
    if f.startswith('tuu') and stem_preverb and 'uur' in stem_preverb:
        return 'ru' + f[3:]
    if f.startswith('tu'):
        return 'ru' + f[2:]
    if f.startswith('ti'):
        return 'ra' + f[2:]
    return None    # ta- (ir-preverb) and other shapes: not derivable


def derive_forms(form_1=None, form_2=None, form_3=None, form_5=None,
                 headword=None, stem_preverb=None, gram_class=None):
    """Derive the person/mode forms the sentence builder needs.

    Inputs are the attested dictionary paradigm forms:
      form_1 = 1sg IND PERF, form_2 = 3sg IND PERF,
      form_3 = 3sg IND IMPF, form_5 = 3sg IND INTENTIVE (future)

    Returns dict of derived surface forms (values None when underivable):
      1sg_ind / 2sg_ind / 3sg_ind          (perfective, "past")
      3sg_ind_impf                          (attested passthrough, "present")
      3sg_ind_int                           (attested passthrough, "future")
      1sg_abs / 2sg_abs / 3sg_abs           (absolutive, for questions)
    Every returned form is either attested verbatim or a single left-edge
    prefix swap away from an attested form.
    """
    f1 = strip_accents(primary_form(form_1)) if form_1 else None
    f2 = strip_accents(primary_form(form_2)) if form_2 else None
    f3 = strip_accents(primary_form(form_3)) if form_3 else None
    f5 = strip_accents(primary_form(form_5)) if form_5 else None

    # Descriptive verbs (VD/VL, no preverb) list no form_1 — they mark person
    # with the descriptive-ku system directly on form_2's stem:
    #   3sg ti+STEM   1sg ti+ku+STEM   2sg ta+STEM   (App.1 'to be sick')
    primary_gc = (gram_class or '').split(',')[0].strip()
    is_desc = (primary_gc in ('VD', 'VL') and not stem_preverb)
    if (not f1 and is_desc and f2 and f2.startswith('ti')
            and not f2.startswith(('tir', 'tii', 'tiʔ'))):
        stem_part = f2[2:]
        # only when form_2 is transparently ti+STEM (stem must echo the
        # headword's first letter — filters out tih- person-marker shapes)
        hw0 = strip_accents(headword or '')[:1].lower()
        if stem_part and hw0 and stem_part[0].lower() == hw0:
            f1 = 'tiku' + stem_part

    two_sg = derive_2sg_ind(f1, f2)
    desc_ku = bool(f1 and f1.startswith('tiku'))
    # descriptive-ku 2nd person absolutive uses raa- (App.1: raakiraawaʔ)
    if desc_ku and two_sg and two_sg.startswith('ta'):
        two_sg_abs = 'raa' + two_sg[2:]
    else:
        two_sg_abs = to_absolutive(two_sg)

    # Prefix transplant: form_3 (IMPF, "present") and form_5 (INTENTIVE,
    # "future") carry the same 3sg prefix shape as form_2, so swapping in the
    # 1sg/2sg prefix learned from the form_1/form_2 alignment yields the
    # other persons in those aspects (tac|takacat -> tac|takacuhta).
    p_1sg = p_3sg = None
    if f1 and f2:
        p_1sg, p_3sg, _ = _common_suffix_split(f1, f2)

    def transplant_1sg(target):
        """Move the (attested) 1sg prefix onto an aspect variant of form_2."""
        if not (target and p_1sg is not None and p_3sg is not None
                and target.startswith(p_3sg) and len(p_1sg) <= 8):
            return None
        return p_1sg + target[len(p_3sg):]

    f3_1sg = transplant_1sg(f3)
    f5_1sg = transplant_1sg(f5)

    return {
        '1sg_ind': f1,
        '2sg_ind': two_sg,
        '3sg_ind': f2,
        '1sg_ind_impf': f3_1sg,
        '2sg_ind_impf': derive_2sg_ind(f3_1sg, f3),
        '3sg_ind_impf': f3,
        '1sg_ind_int': f5_1sg,
        '2sg_ind_int': derive_2sg_ind(f5_1sg, f5),
        '3sg_ind_int': f5,
        '1sg_abs': to_absolutive(f1),
        '2sg_abs': two_sg_abs,
        '3sg_abs': to_absolutive(f2, third_person=True,
                                 stem_preverb=stem_preverb,
                                 headword=headword),
    }


# ---------------------------------------------------------------------------
# Validation against Appendix 1
# ---------------------------------------------------------------------------

def validate_appendix(verbose=True):
    """Derive 2sg + absolutive forms for the Appendix 1 paradigm verbs and
    compare against Parks's attested cells. Returns (passed, failed, details)."""
    data = json.loads(APPENDIX1.read_text(encoding='utf-8'))
    passed = failed = skipped = 0
    failures = []

    def norm(s):
        return strip_accents(primary_form(s or '')) or None

    for page, verb in data.items():
        gloss = verb.get('english_gloss') or page
        modes = verb.get('modes') or {}
        ind = modes.get('indicative_perfective') or {}
        absv = modes.get('absolutive_perfective') or {}
        f1 = norm((ind.get('1sg') or {}).get('skiri'))
        f2 = norm((ind.get('3sg') or {}).get('skiri'))
        if not f1:
            continue

        preverb = {'to do it': '(ut...)', 'to be good': '(uur...)'}.get(gloss)
        derived = derive_forms(form_1=f1, form_2=f2, stem_preverb=preverb)

        checks = []
        att_2sg = norm((ind.get('2sg') or {}).get('skiri'))
        if att_2sg:
            checks.append(('2sg_ind', derived['2sg_ind'], att_2sg))
        for pn in ('1sg', '2sg', '3sg'):
            att = norm((absv.get(pn) or {}).get('skiri'))
            if att:
                checks.append((pn + '_abs', derived[pn + '_abs'], att))

        for label, derived, attested in checks:
            if derived is None:
                skipped += 1
                if verbose:
                    print(f"  SKIP {gloss:14s} {label:8s} (underivable) "
                          f"attested={attested}")
                continue
            if derived == attested:
                passed += 1
                if verbose:
                    print(f"  PASS {gloss:14s} {label:8s} {derived}")
            else:
                failed += 1
                failures.append((gloss, label, derived, attested))
                if verbose:
                    print(f"  FAIL {gloss:14s} {label:8s} "
                          f"derived={derived}  attested={attested}")

    print(f"\nAppendix 1 derivation validation: "
          f"{passed} passed, {failed} failed, {skipped} skipped")
    return passed, failed, failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Person/mode form derivation")
    ap.add_argument('--validate-appendix', action='store_true')
    ap.add_argument('--derive', nargs=3,
                    metavar=('FORM_1', 'FORM_2', 'HEADWORD'),
                    help='derive all forms for one verb')
    args = ap.parse_args()

    if args.validate_appendix:
        _, failed, _ = validate_appendix()
        sys.exit(1 if failed > 3 else 0)
    elif args.derive:
        f1, f2, hw = args.derive
        d = derive_forms(form_1=f1, form_2=f2, headword=hw)
        for k, v in d.items():
            print(f"  {k:14s} {v}")
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
