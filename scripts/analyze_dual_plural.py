#!/usr/bin/env python3
"""
Phase 3.1 — Dual/Plural Morpheme Analysis
==========================================
Uses Gemini to systematically decompose every dual and plural form
from Appendix 1 into constituent morphemes, identifying:
  - Proclitics (si-, ku-, etc.)
  - Modal prefixes
  - Agent prefixes
  - Inclusive/plural markers
  - Preverb forms (and their alternations)
  - Stems (including suppletive du/pl stems)
  - Suffixes (aspect, subordination, 3pl)

Outputs structured JSON for each verb with morpheme-by-morpheme analysis.

Usage:
    python scripts/analyze_dual_plural.py
    python scripts/analyze_dual_plural.py --resume  # resume from checkpoint
    python scripts/analyze_dual_plural.py --report   # just print summary from saved results
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Paths
A1_PATH = Path("extracted_data/appendix1_conjugations.json")
CHECKPOINT_PATH = Path("dual_plural_analysis_checkpoint.json")
OUTPUT_PATH = Path("extracted_data/dual_plural_analysis.json")

# Known verb info (from morpheme_inventory.py)
VERB_INFO = {
    "page_2": {
        "english": "to come",
        "stem": "aʔ",
        "preverb": "ir- (alternating: iir- for 1/2.A, a- for 3.A)",
        "verb_class": "1",
        "transitivity": "intransitive",
    },
    "page_3": {
        "english": "to do it",
        "stem": "uutaar (ut- fused: underlying ut- + aar)",
        "preverb": "ut- (fused into stem)",
        "verb_class": "1",
        "transitivity": "transitive",
    },
    "page_4": {
        "english": "to go",
        "stem": "ʔat (suppletive: sg ʔat, du war, pl at/wuu)",
        "preverb": "none",
        "verb_class": "1",
        "transitivity": "intransitive",
        "notes": "Irregular suppletive stems in du/pl (Appendix 2)",
    },
    "page_5": {
        "english": "to be good",
        "stem": "hiir",
        "preverb": "uur-",
        "verb_class": "u (descriptive)",
        "transitivity": "intransitive/descriptive",
    },
    "page_6": {
        "english": "to drink it",
        "stem": "kiikaʔ",
        "preverb": "none",
        "verb_class": "1",
        "transitivity": "transitive",
    },
    "page_7": {
        "english": "to be sick",
        "stem": "kiraawaʔ",
        "preverb": "none",
        "verb_class": "u (descriptive)",
        "transitivity": "intransitive/descriptive",
        "notes": "Uses ku- indefinite proclitic in some forms",
    },
    "page_8": {
        "english": "to have it",
        "stem": "raa",
        "preverb": "none",
        "verb_class": "3",
        "transitivity": "transitive",
    },
}

PERSON_NUMBERS = [
    "1sg", "2sg", "3sg",
    "1du_incl", "1du_excl", "2du", "3du",
    "1pl_incl", "1pl_excl", "2pl", "3pl",
]

MODES = [
    "indicative_perfective",
    "negative_indicative_perfective",
    "contingent_perfective",
    "assertive_perfective",
    "absolutive_perfective",
    "potential_perfective",
    "gerundial_perfective_subordinate",
    "contingent_perfective_subordinate",
    "subjunctive_perfective_subordinate",
    "infinitive_perfective_subordinate",
]


def build_prompt(page_key, verb_info, paradigm_data):
    """Build a Gemini prompt for morpheme analysis of one verb."""

    # Collect all forms into a readable table
    form_table = []
    modes_data = paradigm_data.get("modes", {})
    for mode in MODES:
        mode_forms = modes_data.get(mode, {})
        for pn in PERSON_NUMBERS:
            fd = mode_forms.get(pn, {})
            skiri = fd.get("skiri", "") if isinstance(fd, dict) else str(fd)
            if skiri:
                form_table.append(f"  {mode:45s} {pn:12s} {skiri}")

    forms_text = "\n".join(form_table)

    prompt = f"""You are a Skiri Pawnee morphology expert analyzing verb paradigms from the Parks Dictionary.

VERB: "{verb_info['english']}"
STEM: {verb_info['stem']}
PREVERB: {verb_info['preverb']}
VERB CLASS: {verb_info['verb_class']}
TRANSITIVITY: {verb_info['transitivity']}
{('NOTES: ' + verb_info.get('notes', '')) if verb_info.get('notes') else ''}

KNOWN MORPHEME SYSTEM (Parks Dictionary):
- Proclitics: si- (DU), ku- (INDF), wi- (QUOT), kuur- (DUB), etc.
- Modal prefixes: ta-/ti- (IND), kaaka-/kaaki- (NEG), rii- (ASSR), i-/ri- (CONT), kuus-/kaas- (POT), ra- (ABS), aa-/ii- (SUBJ), ra-..ku- (INF)
  - 1/2 person forms: ta-, kaaka-, rii-, i-, kuus-/kaas-, ra-, aa-, ra-
  - 3rd person forms: ti-, kaaki-, rii-, ri-, kuus-, ra-, ii-, ra-
  - Rule 2R (dominant a): when mode prefix ending in -i (ti-, ri-, kaaki-, ii-) is followed by preverb a-, the -i becomes -a (ti+a->ta, ri+a->ra, kaaki+a->kaaka, ii+a->a)
- Agent prefixes: t- (1.A), s- (2.A), zero (3.A)
- Inclusive: acir- (1.DU.INCL), a- (1.PL.INCL)
- Plural: raak-/rak- (1/2.PL), ir- (3.COLL.PL), raar- (3.INDV.PL)
- Preverb alternation: ir- -> iir- (1/2.A) / a- (3.A); ut- and uur- do not alternate
- Aspect suffixes: -zero (PERF), -hus (IMPF)
- Subordination: -a (class 1), -i (class 2), -u (descriptive), -wi (locative)
- 3pl suffixes: -aahuʔ / -raaraʔ (non-sub), -aahu / -raara (sub)
- Gerundial: irii- + ra- compound prefix (absolutive subordinate)

SOUND CHANGE RULES (apply at morpheme boundaries):
- Rule 5: same vowel contraction (aa+a->aa, ii+i->ii, etc.)
- Rule 6: u-domination (u+i->u, i+u->u, u+a->u, a+u->u)
- Rule 7: i+a contraction -> ii (in certain environments)
- Rule 13: t -> h before r
- Rule 14: r+h -> hr (metathesis)
- Rule 15: hr -> h (sonorant reduction)
- Rule 17: sibilant hardening (s -> st after certain consonants)
- Rule 20: degemination (rr->r, etc.)
- Rule 23: final r loss (word-final r is deleted)

ALL PARADIGM FORMS:
{forms_text}

TASK: For EVERY form in the paradigm above, provide a morpheme-by-morpheme decomposition.

For each form, identify:
1. The exact surface form (as given)
2. Each morpheme in order: its underlying form, its label (e.g., DU, MODE, AGENT, INCL, PL, PREV, STEM, ASPECT, SUB, 3PL), and its slot
3. Any sound changes that occurred at each boundary
4. Whether the stem is the singular stem or a suppletive dual/plural stem (and what that stem is)

Pay special attention to:
- DUAL forms: Does the stem change? Does the preverb change form? When does si- appear vs not?
- PLURAL forms: How does raak- interact with the inclusive marker? What happens to the preverb?
- 3PL forms: What determines -aahuʔ vs -raaraʔ?
- GERUNDIAL: How does the irii-ra- prefix decompose for different persons?

Return your analysis as JSON with this structure:
{{
  "verb": "{verb_info['english']}",
  "singular_stem": "<stem used in singular>",
  "dual_stem": "<stem used in dual, or null if same>",
  "plural_stem": "<stem used in plural, or null if same>",
  "forms": {{
    "<mode>": {{
      "<person_number>": {{
        "surface": "<surface form>",
        "morphemes": [
          {{"underlying": "<morpheme>", "label": "<LABEL>", "slot": "<slot_name>"}},
          ...
        ],
        "sound_changes": ["<description of each change>"],
        "notes": "<any special observations>"
      }}
    }}
  }},
  "patterns": {{
    "dual_si_placement": "<rule for when si- appears>",
    "dual_preverb_form": "<how preverb changes in dual>",
    "dual_stem_form": "<the dual stem and how it relates to singular>",
    "plural_preverb_form": "<how preverb changes in plural>",
    "plural_raak_interaction": "<how raak- combines with inclusive/agent>",
    "three_pl_suffix_rule": "<when -aahuʔ vs -raaraʔ>",
    "gerundial_decomposition": "<how irii-ra- works for different persons>"
  }}
}}

Be precise. Every morpheme must be accounted for. If you are uncertain about a decomposition, note it."""

    return prompt


def call_gemini(prompt, max_retries=3):
    """Call Gemini API with retry logic."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65536,
                    temperature=0.1,
                ),
            )
            text = response.text.strip()
            if not text:
                log.warning(f"Empty response on attempt {attempt + 1}")
                time.sleep(5)
                continue
            return json.loads(text)
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
            # Try to salvage partial JSON
            if text:
                try:
                    # Find the last complete object
                    depth = 0
                    last_valid = 0
                    for i, ch in enumerate(text):
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                last_valid = i + 1
                    if last_valid > 0:
                        return json.loads(text[:last_valid])
                except Exception:
                    pass
            if attempt < max_retries - 1:
                time.sleep(5)
        except Exception as e:
            log.error(f"API error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None


def load_checkpoint():
    """Load checkpoint if it exists."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(data):
    """Save checkpoint."""
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze_all_verbs(resume=False):
    """Analyze all 7 Appendix 1 verbs."""
    with open(A1_PATH, "r", encoding="utf-8") as f:
        a1_data = json.load(f)

    checkpoint = load_checkpoint() if resume else {}
    results = checkpoint.get("results", {})

    pages = sorted(VERB_INFO.keys())

    for page_key in pages:
        if page_key in results and results[page_key]:
            log.info(f"Skipping {page_key} ({VERB_INFO[page_key]['english']}) - already done")
            continue

        verb_info = VERB_INFO[page_key]
        paradigm = a1_data.get(page_key, {})

        log.info(f"Analyzing {page_key}: {verb_info['english']}...")

        prompt = build_prompt(page_key, verb_info, paradigm)
        result = call_gemini(prompt)

        if result:
            results[page_key] = result
            log.info(f"  -> Got analysis for {verb_info['english']}")

            # Count forms analyzed
            forms = result.get("forms", {})
            total = sum(len(pns) for pns in forms.values())
            log.info(f"  -> {total} forms decomposed")
        else:
            log.error(f"  -> FAILED for {verb_info['english']}")
            results[page_key] = None

        # Save checkpoint after each verb
        save_checkpoint({"results": results, "timestamp": datetime.now().isoformat()})
        time.sleep(2)  # Rate limiting

    # Save final output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"Analysis saved to {OUTPUT_PATH}")

    return results


def print_summary(results):
    """Print a summary of the analysis."""
    lines = []
    lines.append("=" * 70)
    lines.append("Dual/Plural Morpheme Analysis Summary")
    lines.append("=" * 70)

    for page_key in sorted(VERB_INFO.keys()):
        verb_info = VERB_INFO[page_key]
        result = results.get(page_key)
        if not result:
            lines.append(f"\n{verb_info['english']}: NO DATA")
            continue

        lines.append(f"\n--- {verb_info['english']} ({page_key}) ---")
        lines.append(f"  Singular stem: {result.get('singular_stem', '?')}")
        lines.append(f"  Dual stem:     {result.get('dual_stem', '?')}")
        lines.append(f"  Plural stem:   {result.get('plural_stem', '?')}")

        patterns = result.get("patterns", {})
        if patterns:
            lines.append("  Patterns:")
            for key, val in patterns.items():
                lines.append(f"    {key}: {val}")

    lines.append("\n" + "=" * 70)
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8", errors="replace"))


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.1: Analyze dual/plural morpheme patterns via Gemini"
    )
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint")
    parser.add_argument("--report", action="store_true",
                        help="Print summary from saved results")
    args = parser.parse_args()

    if args.report:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                results = json.load(f)
            print_summary(results)
        else:
            log.error(f"No results file found at {OUTPUT_PATH}")
        return

    results = analyze_all_verbs(resume=args.resume)
    print_summary(results)


if __name__ == "__main__":
    main()
