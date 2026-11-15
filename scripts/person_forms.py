#!/usr/bin/env python3
"""
Phase 3.2b — Person/Mode Derivation from Attested Paradigm Forms
=================================================================

Makes a few verb forms the dictionary does not print ("you", and the question
forms) by changing the start of a form it does print. Used by the sentence
builder of the local app, nowhere else.

EVERY FORM THIS FILE MAKES IS DERIVED, NOT ATTESTED. Show it only with the
words of DERIVED_LABEL beside it, never store it in a table or file of copied
forms, and never put it on the public site. No accent is given: the rules work
on forms without their accents.

Repaired on 2026-11-14 (engines review, decision 6). What changed, and why:

  * Three rules for the "he/she" question form were built on misread forms
    and are gone: tii- to rii- (from the OCR slip "Ka rii hitu'?"; the scan
    reads "Ka rú hitu'?"), tuu- to ru- for uur- verbs and tih- to riih- (both
    from misread cells of Appendix 1). On verbs the rules never saw they
    agreed with the dictionary's own form 4 for 29 of 465.
  * The "I" form it used to invent for descriptive verbs that print none
    (tiku + stem, for 184 verbs) is gone. Parks says some classes lack some
    forms. Where no form 1 is printed, no first or second person is given.
  * The present and future of "I" and "you" are gone. No source prints such
    a paradigm: Appendix 1 has only perfective forms.
  * A rule for the "he/she" question form is in force only if it earned its
    place: see THIRD_PERSON_RULES, where each rule carries what it scored on
    the open half of the test (reports/engines_review/person_forms_repair.md).
  * --validate-appendix fails on any mismatch.

It is NOT to be extended to plurals, the negative or other modes until
someone who knows the language has looked at what it gives now.

The rules that remain. The person and mode prefixes sit at the left edge
(Parks, Appendix 1):

    mode:   indicative ta-/ti-     absolutive ra-/ri-  (swap initial t -> r)
    agent:  1.A t      2.A s       3.A Ø               (swap t -> s for 2sg)

Junctions with the stem-initial segment are recovered by aligning the printed
form 1 (1sg IND) with the printed form 2 (3sg IND):

    3sg ti+X    1sg tat+X     2sg tas+X       (plain consonant stems)
    3sg tir+X   1sg tah+X     2sg tast+X      (r-stems: t+r->h, s+r->st)
    3sg tih+X   1sg tat+X     2sg tas+X       (h-stems: h drops after t and s)
    3sg tiw+X   1sg tatp+X    2sg tasp+X      (w-stems: w->p after obstruent)
    3sg ti+tX   1sg tac+tX    2sg tas+tX      (t-stems: t+t->ct, s+t->st)
    3sg tu+X    1sg tatu+X    2sg tasu+X      (ut-preverb: coalesced tu-)

For the "you" forms there is no test on unseen verbs: only Appendix 1 prints
a second person, and the rules were read from it.

Usage:
    python scripts/person_forms.py --validate-appendix
    python scripts/person_forms.py --derive tactakacat titakacat takacat

Library:
    from person_forms import derive_forms, PRINTED, DERIVED_LABEL
    d = derive_forms(form_1="tactakacat", form_2="titakacat", headword="takacat")
    d["2sg_ind"]   # 'tastakacat'  derived
    d["3sg_abs"]   # 'ratakacat'   derived, for 'ka ratakacat ...?' questions
    "2sg_ind" in PRINTED      # False: show DERIVED_LABEL beside it
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPENDIX1 = ROOT / 'extracted_data' / 'appendix1_conjugations.json'

# What must stand beside every form this file makes, wherever it is shown.
DERIVED_LABEL = "derived; not checked against a printed form"

# The keys of derive_forms() whose value is a printed form of the dictionary (the number of the form), given
# back without its accent. Show the printed form itself, from the table paradigmatic_forms. Every other key
# is derived.
PRINTED = {'1sg_ind': 1, '3sg_ind': 2, '3sg_ind_impf': 3, '3sg_ind_int': 5}

# ---------------------------------------------------------------------------
# The question form for "he/she": which start of form 2 becomes which start
# ---------------------------------------------------------------------------
# Each rule: (name, how the open half of the test judged it, in force?). The open half is the 1,065 verbs
# with an odd entry number; a rule is tested against the start of the dictionary's printed form 4.
#
# Two sets were fixed before the sealed half was opened (reports/engines_review/data/person_forms_plan.json):
#   "narrow"  the repair as the decision paper lists it: the three misread rules out, the others kept;
#   "strict"  only the rules that hold for 97% of the open verbs they cover, with twenty or more of them.
# POLICY says which is in force. It was set by the rule written in the plan, after the one opening of the
# sealed half; the result is in reports/engines_review/person_forms_repair.md.
THIRD_PERSON_RULES = [
    # name                                         open half                      narrow  strict
    ("tih- with a headword in h-: ti- to ra-",     "86 of 87 (98.9%)",            True,   True),
    ("tih-, other headwords: no rule",             "2 verbs; none can be read",   False,  False),
    ("tii-: no rule",                              "best guess 137 of 184 (74.5%)", False, False),
    ("tiʔ- to raʔ-",                               "25 of 29 (86.2%)",            True,   False),
    ("tu- to ru-",                                 "211 of 223 (94.6%)",          True,   False),
    ("ti- to ra-",                                 "464 of 470 (98.7%)",          True,   True),
]
POLICY = "narrow"


def third_person_question_form(form_2, stem_preverb=None, headword=None, policy=None):
    """(name of the rule, the question form for "he/she" or None) from the printed form 2.

    None when no rule in force covers the verb: the caller must then show no form, not a guess.
    stem_preverb is taken for the sake of the callers; no rule in force reads it.
    """
    column = 3 if (policy or POLICY) == "strict" else 2
    in_force = {rule[0] for rule in THIRD_PERSON_RULES if rule[column]}
    if not form_2:
        return "no form 2", None
    f = strip_accents(primary_form(form_2))
    if f.startswith('tih'):
        if headword and strip_accents(headword).startswith('h'):
            name, form = "tih- with a headword in h-: ti- to ra-", 'ra' + f[2:]
        else:
            name, form = "tih-, other headwords: no rule", None
    elif f.startswith('tii'):
        name, form = "tii-: no rule", None
    elif f.startswith('tiʔ'):
        name, form = "tiʔ- to raʔ-", 'raʔ' + f[3:]
    elif f.startswith('tu'):
        name, form = "tu- to ru-", 'ru' + f[2:]
    elif f.startswith('ti'):
        name, form = "ti- to ra-", 'ra' + f[2:]
    else:
        return "form 2 begins %s-: no rule" % f[:2], None
    return name, (form if name in in_force else None)


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
    """Indicative -> absolutive, for ka/kirike/kiru questions. A derived form, or None.

    1st/2nd person: the mode vowel matches (ta-/ra-), so the swap is the
    initial t -> r (App.1: tatkiikaʔ -> ratkiikaʔ, taskiikaʔ -> raskiikaʔ),
    with descriptive-ku 1sg tiku- -> riiku- (App.1: riikukiraawaʔ).

    3rd person: IND mode is ti- but ABS mode is ra-, so the shapes differ and
    each has its own rule: see THIRD_PERSON_RULES. Where no rule is in force
    the answer is None.
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

    return third_person_question_form(f, stem_preverb=stem_preverb, headword=headword)[1]


def derive_forms(form_1=None, form_2=None, form_3=None, form_5=None,
                 headword=None, stem_preverb=None, gram_class=None):
    """The person and mode forms the sentence builder may show for one verb.

    Inputs are the printed forms of the dictionary entry:
      form_1 = 1sg IND PERF, form_2 = 3sg IND PERF,
      form_3 = 3sg IND IMPF, form_5 = 3sg IND INTENTIVE (future)

    Returns a dict; a value is None where no form can be given:
      1sg_ind, 3sg_ind, 3sg_ind_impf, 3sg_ind_int   printed forms, given back without their accent (PRINTED)
      2sg_ind                                       derived from the printed form 1
      1sg_abs, 2sg_abs, 3sg_abs                     derived question forms
    Where the entry prints no form 1, no first or second person is given: none is made up.
    gram_class is taken for the sake of the callers; nothing reads it any more.
    """
    f1 = strip_accents(primary_form(form_1)) if form_1 else None
    f2 = strip_accents(primary_form(form_2)) if form_2 else None
    f3 = strip_accents(primary_form(form_3)) if form_3 else None
    f5 = strip_accents(primary_form(form_5)) if form_5 else None

    two_sg = derive_2sg_ind(f1, f2)
    desc_ku = bool(f1 and f1.startswith('tiku'))
    # descriptive-ku 2nd person absolutive uses raa- (App.1: raakiraawaʔ)
    if desc_ku and two_sg and two_sg.startswith('ta'):
        two_sg_abs = 'raa' + two_sg[2:]
    else:
        two_sg_abs = to_absolutive(two_sg)

    return {
        '1sg_ind': f1,
        '2sg_ind': two_sg,
        '3sg_ind': f2,
        '3sg_ind_impf': f3,
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
        sys.exit(1 if failed else 0)
    elif args.derive:
        f1, f2, hw = args.derive
        d = derive_forms(form_1=f1, form_2=f2, headword=hw)
        for k, v in d.items():
            print(f"  {k:14s} {v}")
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
