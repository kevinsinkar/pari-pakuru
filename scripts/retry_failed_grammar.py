#!/usr/bin/env python3
"""
Retry failed grammar page extractions using multiple AI engines.

The 4 failed pages (1, 3, 7, 16) from the Grammatical Overview contain
critical tables (Table 5, 9, 15, 16) that Gemini couldn't extract with
JSON response constraint. This script tries:
  1. Gemini WITHOUT JSON constraint (plain text response, then parse)
  2. Claude API as alternative engine

Usage:
    python scripts/retry_failed_grammar.py
    python scripts/retry_failed_grammar.py --engine gemini
    python scripts/retry_failed_grammar.py --engine claude
    python scripts/retry_failed_grammar.py --engine both
    python scripts/retry_failed_grammar.py --pages 1,3   # specific pages only
"""

import argparse
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

PDF_PATH = Path("Dictionary Data/Dictionary PDF Split/04-Grammatical_Overview.pdf")
OUTPUT_DIR = Path("extracted_data")
FAILED_PAGES = [1, 3, 7, 16]  # 1-indexed page numbers

# Page content descriptions for context
PAGE_DESCRIPTIONS = {
    1: "Opening page of Grammatical Overview (p.29): Introduction, polysynthetic language description, Nouns section, independent vs dependent noun stems, nominal absolutive suffix -u'",
    3: "Table 5 (Nominal Derivational Affixes), Verbs section intro, verb root definition, discontinuous stems, preverbs (ir-/a-, uur-, at-), morpheme breakdown example",
    7: "Table 9 (Pronominal Prefixes): Agent/Patient columns for 1st/2nd/Obviative/Dual/Plural, si- DU prefix, collective vs individuative plural, morpheme breakdowns",
    16: "Table 15 (Verb Stem Template, 8 slots), Suffixes section (aspect/subordination), Table 16 (Verb Suffix Template, slots 25-28), verb class definition by subordinate suffix",
}

SYSTEM_PROMPT = """You are an expert linguistic OCR assistant specializing in Skiri Pawnee.
You are reading the "Grammatical Overview" section from the Parks Skiri Pawnee dictionary.

Extract ALL content from this page as structured JSON. This section describes the
grammatical structure of Skiri Pawnee including word classes, verb morphology,
slot ordering, person/number marking, modal categories, aspect markers, and proclitics.

CRITICAL: Preserve all linguistic notation exactly:
- Use ʔ (U+0294) for glottal stops (looks like superscript ? or apostrophe in the scan)
- Long vowels: aa, ii, uu (doubled letters)
- c represents /ts/ (NOT English "c")
- Accent marks: á, í, ú (acute = high pitch)
- Preserve morpheme boundaries shown with hyphens

Return JSON with this exact structure:
{
  "page_number": N,
  "sections": [
    {
      "heading": "section heading or null",
      "content": "full text content of this section, preserving all examples and morpheme forms",
      "morphemes_mentioned": [
        {"form": "wi-", "label": "quotative", "meaning": "...", "notes": "..."}
      ],
      "tables": [
        {"caption": "Table N -- Title", "headers": ["col1", "col2"], "rows": [["val1", "val2"], ...]}
      ]
    }
  ]
}"""

USER_PROMPT = """Extract ALL grammatical information from this page of the Parks Skiri Pawnee dictionary.

Focus especially on:
1. ALL text content, preserving exact Pawnee forms and linguistic terminology
2. ALL tables with their full content (headers + every row)
3. ALL morpheme forms mentioned with their labels, meanings, and slot positions
4. ALL example words with morpheme breakdowns
5. Footnotes if present

Be thorough — every morpheme form and table cell matters for building the grammar engine."""


def pdf_page_to_png(page_num_0indexed, dpi=300):
    """Render a PDF page to PNG bytes."""
    doc = fitz.open(str(PDF_PATH))
    page = doc[page_num_0indexed]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


def extract_with_gemini(png_bytes, page_num):
    """Try Gemini extraction — first with JSON, then plain text."""
    import google.genai as genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set")
        return None

    client = genai.Client(api_key=api_key)
    image_part = types.Part.from_bytes(data=png_bytes, mime_type="image/png")

    # Strategy 1: Plain text (no JSON constraint) — less likely to return empty
    log.info(f"  Gemini strategy 1: plain text response...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image_part, USER_PROMPT + "\n\nReturn the result as valid JSON."],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,
                max_output_tokens=16384,
                # NO response_mime_type — let it respond freely
            ),
        )
        text = response.text.strip() if response.text else ""
        if text:
            # Try to extract JSON from the response
            parsed = _extract_json_from_text(text)
            if parsed:
                log.info(f"  Gemini plain-text: SUCCESS")
                return {"engine": "gemini_plaintext", "data": parsed}
            else:
                log.info(f"  Gemini plain-text: got text but couldn't parse JSON, saving raw")
                return {"engine": "gemini_plaintext_raw", "data": {"_raw_text": text}}
        else:
            log.warning(f"  Gemini plain-text: empty response")
    except Exception as e:
        log.error(f"  Gemini plain-text error: {e}")

    # Strategy 2: JSON constraint but with higher temperature
    log.info(f"  Gemini strategy 2: JSON mode with temp=0.2...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image_part, USER_PROMPT],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=16384,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip() if response.text else ""
        if text:
            try:
                parsed = json.loads(text)
                log.info(f"  Gemini JSON mode: SUCCESS")
                return {"engine": "gemini_json", "data": parsed}
            except json.JSONDecodeError:
                log.warning(f"  Gemini JSON mode: invalid JSON")
        else:
            log.warning(f"  Gemini JSON mode: empty response")
    except Exception as e:
        log.error(f"  Gemini JSON mode error: {e}")

    return None


def extract_with_claude(png_bytes, page_num):
    """Try Claude API extraction."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    b64_image = base64.b64encode(png_bytes).decode("utf-8")

    log.info(f"  Claude: sending page {page_num}...")
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": USER_PROMPT,
                    },
                ],
            }],
        )

        text = response.content[0].text.strip()
        if text:
            parsed = _extract_json_from_text(text)
            if parsed:
                log.info(f"  Claude: SUCCESS (parsed JSON)")
                return {"engine": "claude", "data": parsed}
            else:
                log.info(f"  Claude: got text but couldn't parse JSON, saving raw")
                return {"engine": "claude_raw", "data": {"_raw_text": text}}
        else:
            log.warning(f"  Claude: empty response")
    except Exception as e:
        log.error(f"  Claude error: {e}")

    return None


def _extract_json_from_text(text):
    """Extract JSON from text that may contain markdown fences or preamble."""
    import re

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None


def main():
    parser = argparse.ArgumentParser(description="Retry failed grammar page extractions")
    parser.add_argument("--engine", choices=["gemini", "claude", "both"], default="both",
                        help="Which AI engine to use (default: both)")
    parser.add_argument("--pages", type=str, default=None,
                        help="Comma-separated page numbers to retry (default: all failed)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI for page rendering (default: 300)")
    args = parser.parse_args()

    pages = [int(p) for p in args.pages.split(",")] if args.pages else FAILED_PAGES
    OUTPUT_DIR.mkdir(exist_ok=True)

    results = {}

    for page_num in pages:
        page_idx = page_num - 1  # 0-indexed
        log.info(f"=== Page {page_num} (0-idx: {page_idx}) ===")
        log.info(f"  Content: {PAGE_DESCRIPTIONS.get(page_num, 'Unknown')}")

        png_bytes = pdf_page_to_png(page_idx, dpi=args.dpi)
        log.info(f"  Rendered {len(png_bytes)} bytes at {args.dpi} DPI")

        page_results = {}

        if args.engine in ("gemini", "both"):
            gemini_result = extract_with_gemini(png_bytes, page_num)
            if gemini_result:
                page_results["gemini"] = gemini_result
            time.sleep(2)

        if args.engine in ("claude", "both"):
            claude_result = extract_with_claude(png_bytes, page_num)
            if claude_result:
                page_results["claude"] = claude_result
            time.sleep(1)

        results[f"page_{page_num}"] = page_results

        # Report what we got
        for engine, result in page_results.items():
            data = result["data"]
            if isinstance(data, dict) and "_raw_text" in data:
                log.info(f"  {engine}: raw text ({len(data['_raw_text'])} chars)")
            elif isinstance(data, dict) and "sections" in data:
                n_sections = len(data["sections"])
                n_morphemes = sum(len(s.get("morphemes_mentioned", [])) for s in data["sections"])
                n_tables = sum(len(s.get("tables", [])) for s in data["sections"])
                log.info(f"  {engine}: {n_sections} sections, {n_morphemes} morphemes, {n_tables} tables")
            else:
                log.info(f"  {engine}: data structure: {type(data)}")

    # Save results
    out_path = OUTPUT_DIR / "grammar_retry_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"\nSaved all results to {out_path}")

    # Generate comparison report
    report_lines = [
        "=" * 70,
        "Grammar Page Retry — Comparison Report",
        "=" * 70,
        "",
    ]

    for page_num in pages:
        page_key = f"page_{page_num}"
        page_data = results.get(page_key, {})
        report_lines.append(f"--- Page {page_num}: {PAGE_DESCRIPTIONS.get(page_num, '')} ---")

        if not page_data:
            report_lines.append("  NO RESULTS from any engine")
            report_lines.append("")
            continue

        for engine_name, result in page_data.items():
            engine_tag = result["engine"]
            data = result["data"]

            if isinstance(data, dict) and "_raw_text" in data:
                report_lines.append(f"  [{engine_tag}] Raw text ({len(data['_raw_text'])} chars)")
                # Show first 200 chars
                preview = data["_raw_text"][:200].replace("\n", " ")
                report_lines.append(f"    Preview: {preview}...")
            elif isinstance(data, dict) and "sections" in data:
                sections = data["sections"]
                report_lines.append(f"  [{engine_tag}] {len(sections)} sections:")
                for i, sec in enumerate(sections):
                    heading = sec.get("heading", "(no heading)")
                    n_morph = len(sec.get("morphemes_mentioned", []))
                    n_tables = len(sec.get("tables", []))
                    content_len = len(sec.get("content", ""))
                    report_lines.append(f"    {i+1}. {heading} ({content_len} chars, {n_morph} morphemes, {n_tables} tables)")

                    # List tables
                    for tbl in sec.get("tables", []):
                        caption = tbl.get("caption", "(no caption)")
                        n_rows = len(tbl.get("rows", []))
                        report_lines.append(f"       Table: {caption} ({n_rows} rows)")
            else:
                report_lines.append(f"  [{engine_tag}] Other data: {str(data)[:200]}")

        report_lines.append("")

    report_text = "\n".join(report_lines)
    report_path = Path("reports/grammar_retry_comparison.txt")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Print report to stdout safely
    sys.stdout.buffer.write(report_text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
    log.info(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
