#!/usr/bin/env python3
"""
The PDF text layer, read with its fonts and positions
=====================================================

The dictionary page PDFs carry their own text. That text is a second reading
of every page that no AI model produced, which is what makes it worth
comparing with the database. Two things have to be handled:

  - Characters outside plain ASCII are stand-ins: the fonts are custom, and a
    code such as U+00F7 (the division sign) is drawn as u-acute in the Skiri
    font. What a code stands for depends on the font it is set in.
  - The page is two columns, and PyMuPDF returns blocks in file order.

This module only reads. Decoding is in chartable.py.
"""
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
S2E_DIR = ROOT / "Dictionary Data" / "split_pdf_pages_SKIRI_TO_ENGLISH"
E2S_DIR = ROOT / "Dictionary Data" / "split_pdf_pages_ENGLISH_TO_SKIRI"
PARTS_DIR = ROOT / "Dictionary Data" / "Dictionary PDF Split"
ABBREV_PDF = PARTS_DIR / "01-Abbreviations_and_Sound_Key.pdf"


def sources():
    """Every text-layer source as (source, unit, pdf path, page index inside the file)."""
    units = []
    for p in sorted(S2E_DIR.glob("page_*.pdf")):
        units.append(("s2e", int(p.stem.split("_")[1]), p, 0))
    for p in sorted(E2S_DIR.glob("*_English to Skiri.pdf")):
        units.append(("e2s", int(p.name.split("_")[0]), p, 0))
    with fitz.open(str(ABBREV_PDF)) as d:
        for i in range(len(d)):
            units.append(("abbrev", i + 1, ABBREV_PDF, i))
    return units


def family(font):
    """PlainsArial,Bold -> ('PlainsArial', 'Bold'). The stand-in table is per family."""
    name = font.replace("-", ",")
    base, _, style = name.partition(",")
    for suffix in ("BoldItalic", "Bold", "Italic"):
        if base.endswith(suffix) and len(base) > len(suffix):
            base, style = base[:-len(suffix)], suffix
            break
    return base, style


def page_chars(pdf_path, page_index=0):
    """Yield (font, size, flags, char, bbox, block_no, line_no, span_no) for every character."""
    with fitz.open(str(pdf_path)) as d:
        page = d[page_index]
        raw = page.get_text("rawdict")
        for b_no, block in enumerate(raw["blocks"]):
            for l_no, line in enumerate(block.get("lines", [])):
                for s_no, span in enumerate(line["spans"]):
                    for ch in span["chars"]:
                        yield span["font"], round(span["size"], 1), span["flags"], ch["c"], ch["bbox"], b_no, l_no, s_no


def page_spans(pdf_path, page_index=0):
    """The page as a list of spans: dicts with font, size, flags, bbox, text, origin, block, line."""
    spans = []
    with fitz.open(str(pdf_path)) as d:
        page = d[page_index]
        width, height = page.rect.width, page.rect.height
        raw = page.get_text("dict")
        for b_no, block in enumerate(raw["blocks"]):
            for l_no, line in enumerate(block.get("lines", [])):
                for s_no, span in enumerate(line["spans"]):
                    spans.append({"font": span["font"], "size": round(span["size"], 1), "flags": span["flags"],
                                  "bbox": [round(v, 2) for v in span["bbox"]], "text": span["text"],
                                  "block": b_no, "line": l_no, "span": s_no})
    return spans, (width, height)


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
