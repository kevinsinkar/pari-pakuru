#!/usr/bin/env python3
"""
Printable flashcard PDFs: 4 landscape cards per sheet, fronts and backs
=======================================================================

Reads curriculum/weekly_flashcards.md (the generated weekly sets) and writes one PDF per
week into curriculum/flashcard_pdfs/, plus all_weeks.pdf. Each landscape US Letter sheet
holds a 2x2 grid of 5.5 x 4.25 in cards, text centred on the card. Pages alternate FRONT
sheet, BACK sheet, with the back columns mirrored so that printing double-sided (flip on
the long edge of the paper) lines every back up behind its front. Cut along the dotted
lines.

Usage:
    python scripts/build_flashcard_pdfs.py                # all weeks + all_weeks.pdf
    python scripts/build_flashcard_pdfs.py --week 3
    python scripts/build_flashcard_pdfs.py --core-only    # A/B cards only, no C form cards
"""
import argparse
import html
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "curriculum" / "weekly_flashcards.md"
OUTDIR = ROOT / "curriculum" / "flashcard_pdfs"
FONTDIR = Path("C:/Windows/Fonts")

PAGE_W, PAGE_H = 792, 612            # US Letter landscape, points
CW, CH = PAGE_W / 2, PAGE_H / 2      # card 5.5 x 4.25 in
PAD = 22                             # inner margin of a card
GREY = (0.55, 0.55, 0.58)
RULE = (0.72, 0.72, 0.75)
ACCENT = {"A": (0.72, 0.33, 0.18), "B": (0.20, 0.42, 0.55), "C": (0.40, 0.48, 0.30)}

CSS = """
@font-face { font-family: dv; src: url(DejaVuSans.ttf); }
@font-face { font-family: dv; font-weight: bold; src: url(DejaVuSans-Bold.ttf); }
@font-face { font-family: dv; font-style: italic; src: url(DejaVuSans-Oblique.ttf); }
@font-face { font-family: dv; font-weight: bold; font-style: italic; src: url(DejaVuSans-BoldOblique.ttf); }
@font-face { font-family: dvs; src: url(DejaVuSerif.ttf); }
@font-face { font-family: dvs; font-weight: bold; src: url(DejaVuSerif-Bold.ttf); }
@font-face { font-family: dvs; font-style: italic; src: url(DejaVuSerif-Italic.ttf); }
body { font-family: dv; color: #222226; text-align: center; line-height: 1.3; margin: 0; }
p { margin: 0; }
.word  { font-family: dvs; font-size: 30pt; font-weight: bold; }
.pron  { font-size: 15pt; color: #55555a; margin-top: 10pt; }
.eng   { font-family: dvs; font-size: 22pt; }
.engsm { font-family: dvs; font-size: 17pt; }
.cue   { font-size: 11pt; color: #6a6a70; font-style: italic; margin-top: 10pt; }
.meta  { font-size: 9.5pt; color: #55555a; margin-top: 14pt; line-height: 1.35; }
"""


def inline(s):
    """Markdown subset (**bold**, *italic*, `code`) -> HTML; <br> kept."""
    out = []
    for p in re.split(r"(<br>)", s.replace("\\|", "|")):
        if p == "<br>":
            out.append("<br>")
            continue
        p = html.escape(p)
        p = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
        p = re.sub(r"(?<![\w*])\*(.+?)\*(?![\w*])", r"<i>\1</i>", p)
        p = re.sub(r"`(.+?)`", r"\1", p)
        out.append(p)
    return "".join(out)


def parse(md_text):
    weeks, cur = [], None
    for line in md_text.splitlines():
        m = re.match(r"## Week (\d+) — Sunday (\S+) — (.*)", line)
        if m:
            cur = {"week": int(m[1]), "sunday": m[2], "label": m[3], "cards": []}
            weeks.append(cur)
            continue
        if cur and line.startswith("| ") and not line.startswith("| Card") and not line.startswith("|---"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if len(cells) == 3:
                cur["cards"].append(tuple(cells))
    return weeks


WORD_RE = re.compile(r"\*\*(.+?)\*\*\s*(⟨.*?⟩)(.*)", re.S)


def word_block(text, extra_class="cue"):
    """'**word** ⟨pron⟩[<br>extra]' -> word + pronunciation (+ extra line)."""
    m = WORD_RE.match(text)
    if not m:
        return f'<p class="eng">{inline(text)}</p>'
    extra = m[3].strip()
    h = f'<p class="word">{html.escape(m[1])}</p><p class="pron">{html.escape(m[2])}</p>'
    if extra.startswith("<br>"):
        h += f'<p class="{extra_class}">{inline(extra[4:])}</p>'
    return h


def kind_of(cid):
    return cid[-1] if cid[-1] in "AB" else "C"


def front_html(cid, front):
    k = kind_of(cid)
    if k == "A" or WORD_RE.match(front):
        return word_block(front)
    first, *rest = front.split("<br>", 1)
    cls = "eng" if k == "B" else "engsm"
    return f'<p class="{cls}">{inline(first)}</p>' + (f'<p class="cue">{inline(rest[0])}</p>' if rest else "")


def back_html(cid, back):
    if WORD_RE.match(back):
        return word_block(back, extra_class="meta")
    first, *rest = back.split("<br>", 1)
    h = f'<p class="engsm">{inline(first)}</p>'
    if rest:
        h += f'<p class="meta">{inline(rest[0])}</p>'
    return h


def place_centred(page, rect, body, archive):
    """Render HTML centred vertically inside rect (measure with Story, then draw)."""
    story = fitz.Story(html=body, user_css=CSS, archive=archive)
    _, filled = story.place(fitz.Rect(0, 0, rect.width, 10000))
    h = min(filled[3] - filled[1], rect.height)
    top = rect.y0 + (rect.height - h) / 2
    page.insert_htmlbox(fitz.Rect(rect.x0, top, rect.x1, top + h + 2), body, css=CSS, archive=archive, scale_low=0)


def draw_sheet(doc, cards, side, week, archive):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    shape = page.new_shape()
    shape.draw_line((CW, 0), (CW, PAGE_H))
    shape.draw_line((0, CH), (PAGE_W, CH))
    shape.finish(color=RULE, width=0.5, dashes="[3 3] 0")
    shape.commit()
    for idx in range(4):
        row, col = divmod(idx, 2)
        if side == "back":
            col = 1 - col           # mirror so backs sit behind fronts when duplexed
        if idx >= len(cards):
            continue
        cid, front, back = cards[idx]
        x0, y0 = col * CW, row * CH
        s = page.new_shape()
        s.draw_rect(fitz.Rect(x0 + PAD, y0 + PAD - 6, x0 + CW - PAD, y0 + PAD - 4))
        s.finish(color=None, fill=ACCENT[kind_of(cid)])
        s.commit()
        page.insert_text((x0 + PAD, y0 + CH - PAD + 8), cid, fontsize=7.5, color=GREY)
        foot = f"Week {week['week']} - {week['label']} - {side}"
        tw = fitz.get_text_length(foot, fontsize=7.5)
        page.insert_text((x0 + CW - PAD - tw, y0 + CH - PAD + 8), foot, fontsize=7.5, color=GREY)
        rect = fitz.Rect(x0 + PAD, y0 + PAD + 6, x0 + CW - PAD, y0 + CH - PAD - 6)
        body = front_html(cid, front) if side == "front" else back_html(cid, back)
        place_centred(page, rect, body, archive)


def build_pdf(weeks, path, title):
    doc = fitz.open()
    archive = fitz.Archive(str(FONTDIR))
    for w in weeks:
        cards = w["cards"]
        for i in range(0, len(cards), 4):
            chunk = cards[i:i + 4]
            draw_sheet(doc, chunk, "front", w, archive)
            draw_sheet(doc, chunk, "back", w, archive)
    doc.subset_fonts()
    doc.set_metadata({"title": title})
    doc.save(str(path), garbage=3, deflate=True)
    return doc.page_count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--week", type=int)
    ap.add_argument("--core-only", action="store_true", help="only A/B cards, skip C form cards")
    args = ap.parse_args()
    weeks = parse(MD.read_text(encoding="utf-8"))
    if args.core_only:
        for w in weeks:
            w["cards"] = [c for c in w["cards"] if c[0][-1] in "AB"]
    OUTDIR.mkdir(exist_ok=True)
    sel = [w for w in weeks if not args.week or w["week"] == args.week]
    for w in sel:
        p = OUTDIR / f"week_{w['week']:02d}.pdf"
        if not w["cards"]:
            # a week held for review (curriculum/held_for_review.json) has no cards in the Markdown
            if p.exists():
                p.unlink()
            sys.stdout.buffer.write(f"{p.name}: no cards (week held for review), not written\n".encode())
            continue
        n = build_pdf([w], p, f"Skiri Pawnee flashcards, week {w['week']}")
        sys.stdout.buffer.write(f"{p.name}: {len(w['cards'])} cards, {n} pages\n".encode())
    if not args.week:
        p = OUTDIR / "all_weeks.pdf"
        sel = [w for w in sel if w["cards"]]
        n = build_pdf(sel, p, "Skiri Pawnee flashcards, all weeks")
        sys.stdout.buffer.write(f"{p.name}: {sum(len(w['cards']) for w in sel)} cards, {n} pages\n".encode())


if __name__ == "__main__":
    main()
