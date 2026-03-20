#!/usr/bin/env python3
"""
Phase 3.1 — Gemini-Collaborative Conjugation Analysis
======================================================
Runs the conjugation engine against Appendix 1, then sends mismatched forms
to Gemini in multi-round dialogue for morpheme-by-morpheme diagnosis.

Round 1: "Here are our mismatches grouped by pattern. What morphological
          rules are we getting wrong?"
Round 2: "Here is our engine's logic for [specific area]. What would you
          change?" (informed by Round 1 findings)
Round 3: "Here are proposed fixes. Validate against these test cases."

The script is designed to run unattended overnight. All Gemini exchanges
are saved to a JSON report with full prompts and responses.

Usage:
    python scripts/conjugation_gemini_collab.py
    python scripts/conjugation_gemini_collab.py --resume         # resume from checkpoint
    python scripts/conjugation_gemini_collab.py --report         # print summary only
    python scripts/conjugation_gemini_collab.py --rounds 2       # limit rounds
    python scripts/conjugation_gemini_collab.py --verbs "to come,to go"  # specific verbs

Requires: GEMINI_API_KEY environment variable
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from morpheme_inventory import (
    conjugate, validate_appendix1, APPENDIX1_VERBS, APPENDIX1_MODE_MAP,
    SUPPLETIVE_STEMS, MODAL_PREFIXES, PERSON_NUMBER_PREFIXES, VERB_CLASSES,
    _edit_distance,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(stream=open(os.devnull, 'w')),  # suppress console
        logging.FileHandler("conjugation_collab.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# Also print to stdout for monitoring
def printlog(msg):
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.flush()
    log.info(msg)

CHECKPOINT_PATH = Path("conjugation_collab_checkpoint.json")
OUTPUT_PATH = Path("reports/conjugation_gemini_collab.json")
REPORT_PATH = Path("reports/conjugation_gemini_collab.txt")

A1_PATH = Path("extracted_data/appendix1_conjugations.json")


# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------

def call_gemini(prompt, system_prompt=None, expect_json=True, max_retries=3):
    """Call Gemini with retry logic and partial JSON recovery."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    contents = prompt
    config_kwargs = {
        "max_output_tokens": 65536,
        "temperature": 0.2,
    }
    if expect_json:
        config_kwargs["response_mime_type"] = "application/json"
    if system_prompt:
        config_kwargs["system_instruction"] = system_prompt

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = response.text.strip()
            if not text:
                printlog(f"  [Gemini] Empty response, attempt {attempt + 1}")
                time.sleep(5)
                continue

            if expect_json:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Try to salvage partial JSON
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
                    printlog(f"  [Gemini] JSON parse failed, attempt {attempt + 1}")
            else:
                return text

        except Exception as e:
            printlog(f"  [Gemini] Error attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None


# ---------------------------------------------------------------------------
# Mismatch Analysis
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert in Skiri Pawnee morphophonology, specifically the verb conjugation system documented in Douglas R. Parks' Dictionary of Skiri Pawnee.

You understand:
- The 26-slot verb template (proclitics -> inner prefixes -> stem -> suffixes)
- Modal prefixes: ta-/ti- (IND), kaaka-/kaaki- (NEG), rii- (ASSR), i-/ri- (CONT), kuus-/kaas- (POT), ra- (ABS), aa-/ii- (SUBJ), ra-..ku- (INF)
- Agent prefixes: t- (1.A), s- (2.A), zero (3.A)
- Number markers: si- (DU proclitic), acir- (1.DU.INCL), a- (1.PL.INCL), raak-/iraak- (PL)
- Preverb alternation: ir- -> iir- (1/2.A) / a- (3.A); uur- and ut- don't alternate
- Sound change rules (24 rules from Parks Ch. 3): vowel contraction, u-domination, metathesis, degemination, r->h before C, final r loss, etc.
- Subordination suffixes by verb class
- Suppletive stems in dual/plural
- Descriptive verb ku- marking pattern
- Gerundial irii- + ra- decomposition

Your role: analyze mismatches between a conjugation engine's output and the attested Parks forms, identify the morphological rule or pattern error, and propose specific fixes. Be precise about which morpheme boundary or rule is incorrect."""


def gather_mismatches():
    """Run validation and collect all mismatches grouped by pattern."""
    results = validate_appendix1()
    if not results:
        return None

    mismatches = []
    for d in results["details"]:
        if d["match"] != "EXACT":
            mismatches.append(d)

    return mismatches, results


def group_mismatches(mismatches):
    """Group mismatches by likely error pattern for efficient Gemini analysis."""
    groups = {
        "by_verb": defaultdict(list),
        "by_mode": defaultdict(list),
        "by_person": defaultdict(list),
        "by_error_type": defaultdict(list),
    }

    for m in mismatches:
        groups["by_verb"][m["verb"]].append(m)
        groups["by_mode"][m["mode"]].append(m)
        groups["by_person"][m["person"]].append(m)

        # Classify error type
        pred = m["predicted"]
        exp = m["expected"]
        if pred.startswith(exp[:3]) and len(pred) != len(exp):
            groups["by_error_type"]["length_mismatch"].append(m)
        elif exp.startswith(pred[:3]):
            groups["by_error_type"]["prefix_correct_suffix_wrong"].append(m)
        elif _edit_distance(pred, exp) <= 2:
            groups["by_error_type"]["close_single_edit"].append(m)
        else:
            groups["by_error_type"]["major_divergence"].append(m)

    return groups


# ---------------------------------------------------------------------------
# Round 1: Pattern Diagnosis
# ---------------------------------------------------------------------------

def build_round1_prompt(verb_key, verb_info, verb_mismatches):
    """Build Round 1 prompt: diagnose error patterns for one verb."""

    # Format mismatches as a table
    table_lines = []
    for m in verb_mismatches:
        mode_short = m["mode"].replace("_perfective", "").replace("_subordinate", ".sub")
        table_lines.append(
            f"  {mode_short:40s} {m['person']:12s} "
            f"expected={m['expected']:25s} got={m['predicted']:25s} "
            f"({m['match']})"
        )
    table = "\n".join(table_lines)

    # Get engine's morpheme breakdown for a few representative mismatches
    breakdown_lines = []
    for m in verb_mismatches[:10]:
        breakdown_lines.append(f"  {m['person']:12s} {m['mode'][:30]:30s}: {m.get('breakdown', 'N/A')}")
    breakdowns = "\n".join(breakdown_lines)

    prompt = f"""VERB: "{verb_info['english']}"
STEM: {verb_info['stem']}
PREVERB: {verb_info.get('preverb', 'none')}
CLASS: {verb_info['verb_class']}
{verb_info.get('notes', '')}

Our conjugation engine produces {len(verb_mismatches)} incorrect forms for this verb.

MISMATCHED FORMS (mode, person, expected vs. our output):
{table}

OUR ENGINE'S MORPHEME BREAKDOWNS (for first 10 mismatches):
{breakdowns}

SUPPLETIVE STEM INFO:
{json.dumps(SUPPLETIVE_STEMS.get(verb_info['stem'], {}), ensure_ascii=False, indent=2)}

TASK: Analyze these mismatches and identify the systematic patterns. For each pattern:
1. What morphological rule or combination is our engine getting wrong?
2. What is the correct morpheme sequence for a representative example?
3. What specific change to the engine would fix this pattern?

Return JSON:
{{
  "verb": "{verb_info['english']}",
  "total_mismatches": {len(verb_mismatches)},
  "patterns": [
    {{
      "pattern_id": "<short_id>",
      "description": "<what's going wrong>",
      "affected_forms": ["<mode/person pairs>"],
      "count": <number of forms affected>,
      "example": {{
        "mode": "<mode>",
        "person": "<person>",
        "expected": "<correct form>",
        "engine_output": "<wrong form>",
        "correct_morphemes": "<morpheme + morpheme + ...>",
        "engine_morphemes": "<what engine builds>",
        "root_cause": "<specific rule/logic error>"
      }},
      "proposed_fix": "<concrete description of code change needed>"
    }}
  ],
  "priority_order": ["<pattern_ids ordered by impact>"]
}}

Focus on patterns that affect MULTIPLE forms, not one-off issues."""

    return prompt


# ---------------------------------------------------------------------------
# Round 2: Deep Dive on Top Patterns
# ---------------------------------------------------------------------------

def build_round2_prompt(verb_info, round1_result, appendix1_forms):
    """Build Round 2: deep dive on the top patterns identified in Round 1."""

    patterns = round1_result.get("patterns", [])
    priority = round1_result.get("priority_order", [p["pattern_id"] for p in patterns])

    # Take top 3 patterns
    top_patterns = []
    for pid in priority[:3]:
        for p in patterns:
            if p.get("pattern_id") == pid:
                top_patterns.append(p)
                break

    if not top_patterns:
        top_patterns = patterns[:3]

    patterns_text = json.dumps(top_patterns, ensure_ascii=False, indent=2)

    # Gather ALL forms for the affected mode/person combos
    affected_forms = []
    for p in top_patterns:
        for af in p.get("affected_forms", []):
            # Parse "mode/person" format
            parts = af.split("/")
            if len(parts) == 2:
                mode_key, pn = parts
                form_data = appendix1_forms.get(mode_key, {}).get(pn, {})
                if isinstance(form_data, dict) and form_data.get("skiri"):
                    affected_forms.append(f"  {mode_key:40s} {pn:12s} = {form_data['skiri']}")

    # Also include the correct forms for the full paradigm of affected modes
    all_correct = []
    for p in top_patterns:
        example = p.get("example", {})
        mode = example.get("mode", "")
        if mode and mode in appendix1_forms:
            mode_forms = appendix1_forms[mode]
            for pn in ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du",
                        "1pl_incl", "1pl_excl", "2pl", "3pl"]:
                fd = mode_forms.get(pn, {})
                skiri = fd.get("skiri", "") if isinstance(fd, dict) else str(fd)
                if skiri:
                    all_correct.append(f"  {mode:40s} {pn:12s} = {skiri}")

    correct_text = "\n".join(all_correct[:50]) if all_correct else "(no forms available)"

    prompt = f"""VERB: "{verb_info['english']}" (stem: {verb_info['stem']}, preverb: {verb_info.get('preverb', 'none')}, class: {verb_info['verb_class']})

In Round 1, you identified these top error patterns:
{patterns_text}

COMPLETE CORRECT PARADIGM for affected modes (from Parks Appendix 1):
{correct_text}

TASK: For each of the top patterns above, provide:
1. The EXACT morpheme-by-morpheme breakdown of 3 representative correct forms
2. The EXACT sequence of sound changes that derive the surface form
3. A comparison showing where our engine diverges
4. A minimal, precise rule statement that could be implemented in Python

Return JSON:
{{
  "verb": "{verb_info['english']}",
  "deep_dives": [
    {{
      "pattern_id": "<from round 1>",
      "representative_forms": [
        {{
          "mode": "<mode>",
          "person": "<person>",
          "surface": "<correct surface form>",
          "underlying": "<slot-by-slot morpheme sequence>",
          "derivation_steps": [
            "<step 1: concatenate X + Y>",
            "<step 2: Rule N applies: X -> Y>",
            "<step 3: ...>"
          ]
        }}
      ],
      "engine_error_point": "<exact step where engine diverges>",
      "rule_statement": "<implementable rule: IF context THEN action>",
      "test_cases": [
        {{"input_morphemes": ["m1", "m2", ...], "expected_output": "<surface>"}},
      ]
    }}
  ]
}}

Be extremely precise about the derivation steps. Show every sound change rule application."""

    return prompt


# ---------------------------------------------------------------------------
# Round 3: Cross-Verb Synthesis
# ---------------------------------------------------------------------------

def build_round3_prompt(all_round2_results):
    """Build Round 3: synthesize findings across all verbs into unified fixes."""

    summaries = []
    for verb, r2 in all_round2_results.items():
        if not r2:
            continue
        dives = r2.get("deep_dives", [])
        for d in dives:
            summaries.append({
                "verb": verb,
                "pattern": d.get("pattern_id", "?"),
                "rule": d.get("rule_statement", "?"),
                "error_point": d.get("engine_error_point", "?"),
            })

    summaries_text = json.dumps(summaries, ensure_ascii=False, indent=2)

    prompt = f"""You have analyzed conjugation errors across 7 Skiri Pawnee verbs.

Here are ALL the error patterns and proposed fixes from the per-verb analysis:
{summaries_text}

TASK: Synthesize these into a unified improvement plan:

1. SHARED PATTERNS: Which errors appear across multiple verbs? Group them.
2. VERB-SPECIFIC: Which errors are unique to one verb's irregularity?
3. PRIORITY ORDER: Rank fixes by number of forms they would correct.
4. IMPLEMENTATION PLAN: For the top 5 fixes, describe the exact code change needed
   in the conjugation engine (which function, what condition, what output).
5. RISK ASSESSMENT: Which fixes might break currently-correct forms?
6. ACCENT PATTERNS: Are there any systematic accent (pitch/stress) patterns visible
   in the data that we should eventually handle?

Return JSON:
{{
  "shared_patterns": [
    {{
      "pattern": "<description>",
      "affects_verbs": ["<verb1>", "<verb2>"],
      "estimated_forms_fixed": <number>,
      "fix_description": "<precise code change>"
    }}
  ],
  "verb_specific_patterns": [
    {{
      "verb": "<verb>",
      "pattern": "<description>",
      "estimated_forms_fixed": <number>,
      "fix_description": "<precise code change>"
    }}
  ],
  "priority_ranking": [
    {{
      "rank": 1,
      "pattern": "<description>",
      "forms_fixed": <number>,
      "implementation": "<step-by-step code change>",
      "risk": "<what could break>"
    }}
  ],
  "accent_observations": "<any patterns noted>",
  "expected_accuracy_after_fixes": "<estimated % exact match>"
}}"""

    return prompt


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"round1": {}, "round2": {}, "round3": None, "timestamp": None}


def save_checkpoint(data):
    data["timestamp"] = datetime.now().isoformat()
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_analysis(max_rounds=3, verb_filter=None):
    """Run the full multi-round Gemini collaborative analysis."""

    printlog("=" * 70)
    printlog("Phase 3.1: Gemini-Collaborative Conjugation Analysis")
    printlog("=" * 70)

    # Load Appendix 1 data
    with open(A1_PATH, "r", encoding="utf-8") as f:
        a1_data = json.load(f)

    # Step 0: Gather mismatches
    printlog("\n[Step 0] Running conjugation engine validation...")
    mismatches, validation = gather_mismatches()
    if not mismatches:
        printlog("No mismatches found! Engine is perfect.")
        return

    total = validation["total"]
    exact = validation["exact_match"]
    close = validation["close_match"]
    printlog(f"  {total} forms tested: {exact} exact ({100*exact/total:.1f}%), "
             f"{close} close, {len(mismatches)} mismatched")

    groups = group_mismatches(mismatches)
    printlog(f"  Mismatches by verb: {', '.join(f'{v}: {len(ms)}' for v, ms in sorted(groups['by_verb'].items()))}")

    checkpoint = load_checkpoint()

    # Step 1: Round 1 — Per-verb pattern diagnosis
    if max_rounds >= 1:
        printlog("\n[Round 1] Per-verb pattern diagnosis...")

        for page_key, verb_info in sorted(APPENDIX1_VERBS.items()):
            eng = verb_info["english"]

            if verb_filter and eng not in verb_filter:
                continue

            if eng in checkpoint["round1"] and checkpoint["round1"][eng]:
                printlog(f"  {eng}: cached from checkpoint")
                continue

            verb_mismatches = groups["by_verb"].get(eng, [])
            if not verb_mismatches:
                printlog(f"  {eng}: no mismatches, skipping")
                checkpoint["round1"][eng] = {"patterns": [], "total_mismatches": 0}
                save_checkpoint(checkpoint)
                continue

            printlog(f"  {eng}: {len(verb_mismatches)} mismatches, sending to Gemini...")
            prompt = build_round1_prompt(page_key, verb_info, verb_mismatches)
            result = call_gemini(prompt, system_prompt=SYSTEM_PROMPT)

            if result:
                checkpoint["round1"][eng] = result
                n_patterns = len(result.get("patterns", []))
                printlog(f"  {eng}: {n_patterns} patterns identified")
            else:
                printlog(f"  {eng}: FAILED")
                checkpoint["round1"][eng] = None

            save_checkpoint(checkpoint)
            time.sleep(3)  # rate limit

    # Step 2: Round 2 — Deep dive on top patterns
    if max_rounds >= 2:
        printlog("\n[Round 2] Deep dive on top patterns...")

        for page_key, verb_info in sorted(APPENDIX1_VERBS.items()):
            eng = verb_info["english"]

            if verb_filter and eng not in verb_filter:
                continue

            r1 = checkpoint["round1"].get(eng)
            if not r1 or not r1.get("patterns"):
                continue

            if eng in checkpoint["round2"] and checkpoint["round2"][eng]:
                printlog(f"  {eng}: cached from checkpoint")
                continue

            # Get this verb's appendix 1 forms
            page_data = a1_data.get(page_key, {})
            a1_forms = page_data.get("modes", {})

            printlog(f"  {eng}: deep dive on {len(r1.get('patterns', []))} patterns...")
            prompt = build_round2_prompt(verb_info, r1, a1_forms)
            result = call_gemini(prompt, system_prompt=SYSTEM_PROMPT)

            if result:
                checkpoint["round2"][eng] = result
                n_dives = len(result.get("deep_dives", []))
                printlog(f"  {eng}: {n_dives} deep dives completed")
            else:
                printlog(f"  {eng}: FAILED")
                checkpoint["round2"][eng] = None

            save_checkpoint(checkpoint)
            time.sleep(3)

    # Step 3: Round 3 — Cross-verb synthesis
    if max_rounds >= 3:
        printlog("\n[Round 3] Cross-verb synthesis...")

        if checkpoint["round3"]:
            printlog("  Cached from checkpoint")
        else:
            r2_results = checkpoint["round2"]
            if any(v for v in r2_results.values() if v):
                prompt = build_round3_prompt(r2_results)
                result = call_gemini(prompt, system_prompt=SYSTEM_PROMPT)

                if result:
                    checkpoint["round3"] = result
                    n_shared = len(result.get("shared_patterns", []))
                    n_specific = len(result.get("verb_specific_patterns", []))
                    printlog(f"  Synthesis: {n_shared} shared patterns, {n_specific} verb-specific")
                else:
                    printlog("  Synthesis FAILED")

                save_checkpoint(checkpoint)
            else:
                printlog("  No Round 2 data available for synthesis")

    # Save final report
    save_report(checkpoint, validation)
    printlog(f"\nDone. Report saved to {REPORT_PATH}")
    printlog(f"Full JSON data at {OUTPUT_PATH}")


def save_report(checkpoint, validation):
    """Save human-readable report + full JSON."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save full JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)

    # Build text report
    lines = []
    lines.append("=" * 70)
    lines.append("Phase 3.1: Gemini-Collaborative Conjugation Analysis Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 70)

    total = validation["total"]
    exact = validation["exact_match"]
    close = validation["close_match"]
    lines.append(f"\nCurrent accuracy: {exact}/{total} exact ({100*exact/total:.1f}%), "
                 f"{close} close (d<=2)")

    # Round 1 summary
    lines.append("\n" + "-" * 70)
    lines.append("ROUND 1: Per-Verb Pattern Diagnosis")
    lines.append("-" * 70)

    for eng, r1 in sorted(checkpoint["round1"].items()):
        if not r1:
            lines.append(f"\n{eng}: FAILED")
            continue
        patterns = r1.get("patterns", [])
        lines.append(f"\n{eng} ({r1.get('total_mismatches', '?')} mismatches, {len(patterns)} patterns):")
        for p in patterns:
            lines.append(f"  [{p.get('pattern_id', '?')}] {p.get('description', '?')}")
            lines.append(f"    Affects: {p.get('count', '?')} forms")
            lines.append(f"    Fix: {p.get('proposed_fix', '?')}")
            example = p.get("example", {})
            if example:
                lines.append(f"    Example: {example.get('mode', '?')}/{example.get('person', '?')}")
                lines.append(f"      Expected: {example.get('expected', '?')}")
                lines.append(f"      Got:      {example.get('engine_output', '?')}")
                lines.append(f"      Root cause: {example.get('root_cause', '?')}")

    # Round 2 summary
    lines.append("\n" + "-" * 70)
    lines.append("ROUND 2: Deep Dives")
    lines.append("-" * 70)

    for eng, r2 in sorted(checkpoint["round2"].items()):
        if not r2:
            continue
        dives = r2.get("deep_dives", [])
        lines.append(f"\n{eng}:")
        for d in dives:
            lines.append(f"  Pattern: {d.get('pattern_id', '?')}")
            lines.append(f"  Engine error point: {d.get('engine_error_point', '?')}")
            lines.append(f"  Rule: {d.get('rule_statement', '?')}")
            for form in d.get("representative_forms", [])[:2]:
                lines.append(f"    {form.get('person', '?')} {form.get('mode', '?')[:30]}: {form.get('surface', '?')}")
                lines.append(f"      Underlying: {form.get('underlying', '?')}")
                for step in form.get("derivation_steps", [])[:5]:
                    lines.append(f"        -> {step}")

    # Round 3 summary
    r3 = checkpoint.get("round3")
    if r3:
        lines.append("\n" + "-" * 70)
        lines.append("ROUND 3: Cross-Verb Synthesis")
        lines.append("-" * 70)

        lines.append("\nSHARED PATTERNS (affect multiple verbs):")
        for sp in r3.get("shared_patterns", []):
            lines.append(f"  - {sp.get('pattern', '?')}")
            lines.append(f"    Verbs: {', '.join(sp.get('affects_verbs', []))}")
            lines.append(f"    Est. forms fixed: {sp.get('estimated_forms_fixed', '?')}")
            lines.append(f"    Fix: {sp.get('fix_description', '?')}")

        lines.append("\nPRIORITY RANKING:")
        for pr in r3.get("priority_ranking", []):
            lines.append(f"  #{pr.get('rank', '?')}: {pr.get('pattern', '?')}")
            lines.append(f"    Forms fixed: ~{pr.get('forms_fixed', '?')}")
            lines.append(f"    Implementation: {pr.get('implementation', '?')}")
            lines.append(f"    Risk: {pr.get('risk', '?')}")

        if r3.get("accent_observations"):
            lines.append(f"\nACCENT OBSERVATIONS: {r3['accent_observations']}")
        if r3.get("expected_accuracy_after_fixes"):
            lines.append(f"\nEXPECTED ACCURACY AFTER FIXES: {r3['expected_accuracy_after_fixes']}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def print_report():
    """Print existing report."""
    if REPORT_PATH.exists():
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            sys.stdout.buffer.write(f.read().encode("utf-8", errors="replace"))
    else:
        printlog(f"No report found at {REPORT_PATH}. Run analysis first.")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.1: Gemini-collaborative conjugation analysis"
    )
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint")
    parser.add_argument("--report", action="store_true",
                        help="Print existing report")
    parser.add_argument("--rounds", type=int, default=3,
                        help="Number of rounds to run (1-3)")
    parser.add_argument("--verbs", type=str, default=None,
                        help="Comma-separated verb names to analyze (e.g., 'to come,to go')")
    args = parser.parse_args()

    if args.report:
        print_report()
        return

    if not os.environ.get("GEMINI_API_KEY"):
        printlog("ERROR: Set GEMINI_API_KEY environment variable")
        sys.exit(1)

    verb_filter = None
    if args.verbs:
        verb_filter = [v.strip() for v in args.verbs.split(",")]

    if args.resume:
        printlog("Resuming from checkpoint...")

    run_analysis(max_rounds=args.rounds, verb_filter=verb_filter)


if __name__ == "__main__":
    main()
