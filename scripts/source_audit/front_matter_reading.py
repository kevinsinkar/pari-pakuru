#!/usr/bin/env python3
"""
Front-matter chapters 2 and 5, read twice from the page (2026-11-14)
====================================================================

Chapter 2 (Sounds and Alphabet, book pages 13 to 17) and chapter 5
(Organization of the Dictionary, book pages 53 to 60) have no text layer: the
print is stored as outlines. Until 2026-11-14 nothing in the project came
from them. This script sets up two blind readings of the 13 pages and joins
them into one stored copy of each chapter.

    python scripts/source_audit/front_matter_reading.py --sheets     # cut the pages; one folder per reader
    python scripts/source_audit/front_matter_reading.py --zoom ch2_a p3-b2 0 0.5 0.6 1
                                                                     # for a reader: part of a tile, drawn larger
    (each reader writes reading.json in its folder; copy it to
     reports/source_audit_2026-11/blind_readings/front_matter_<folder>.json)
    python scripts/source_audit/front_matter_reading.py              # compare the two readings; writes the record
    python scripts/source_audit/front_matter_reading.py --write      # also writes the two files in extracted_data/

The two readings see different cuts of the same pages (reading A four bands a
page, reading B three), so a line that falls on a cut in one reading does not
in the other. Each reader gets a folder that holds its images and nothing
else, and is told nothing about the project's data.

What a reader writes, page by page:

    blocks   the whole page in reading order: headings, paragraphs, list
             items, tables (rows of cells), figure captions; italic print
             between asterisks, phonetic forms in their square brackets
    forms    every Skiri form of the page in order, each with the phonetic
             form and the English gloss printed beside it, if any

Joining. A Skiri form, a phonetic form or a table cell is stored as settled
when both readings have it letter for letter, accents included. Where they
differ, both are stored side by side and the place is listed for a person;
nothing is chosen.

What is stored, and what is not. extracted_data/sounds_and_alphabet.json and
organization_of_the_dictionary.json hold every Skiri form of the chapter with
the phonetic form and the gloss printed beside it, the tables, the section
headings and the captions of the figures. They do not hold the chapter's
running text: the book is in copyright, and the project needs what the
chapter establishes, not its sentences. Each section has a summary in the
project's own words (NOTES below) and, where a statement of Parks settles a
question of the project, that sentence quoted with its page. The copies of
the readings kept in reports/.../blind_readings/ are cut down in the same
way; the full readings stay in the work folder, which is not in git. How far
the two readings of the running text agree is counted while the work files
exist and kept in the record.

What happened on 2026-11-14. Four readers were started (two chapters, two
cuts). Three finished; the fourth (chapter 5, cuts A) was stopped by the
service's content filter after six of eight pages, and two readers reported
an automated notice in their tool results about not reproducing sections of
books. Pages 7 and 8 of reading A were then read by a fifth reader that was
asked for the forms and figure labels only (folder ch5_a2). That is why
reading A of chapter 5 has its running text shortened and why the agreement
of running text is counted for chapter 2 only.
"""
import argparse
import collections
import datetime as dt
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appendix_tiles  # noqa: E402
import state  # noqa: E402

WORK = state.WORK / "front_matter"
READINGS = state.OUT / "blind_readings"
RECORD = state.OUT / "front_matter_reading.json"
CHAPTERS = {
    "ch2": {"pdf": "Sounds_and_Alphabet", "title": "Sounds and Alphabet", "chapter": 2, "first_book_page": 13,
            "out": "sounds_and_alphabet.json"},
    "ch5": {"pdf": "Organization_of_the_Dictionary", "title": "Organization of the Dictionary", "chapter": 5,
            "first_book_page": 53, "out": "organization_of_the_dictionary.json"},
}
# reading: bands per page, overlap in points. Other cuts for the second reading.
CUTS = {"a": (4, 20.0), "b": (3, 26.0)}
ZOOM = 3.0


def ink_box(page):
    """The box that holds the print of a page, found on a coarse rendering."""
    scale = 0.5
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
    w, h, data = pix.width, pix.height, pix.samples
    rows = [y for y in range(h) if min(data[y * w:(y + 1) * w]) < 128]
    cols = [x for x in range(w) if min(data[x::w]) < 128]
    return fitz.Rect(cols[0] / scale, rows[0] / scale, (cols[-1] + 1) / scale, (rows[-1] + 1) / scale)


def sheets():
    key = {}
    for ch, info in CHAPTERS.items():
        src = fitz.open(str(appendix_tiles.find_pdf(info["pdf"])))
        for reading, (bands, overlap) in CUTS.items():
            name = "%s_%s" % (ch, reading)
            folder = WORK / name
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.glob("*.png"):
                old.unlink()
            made = 0
            for pno in range(len(src)):
                box = ink_box(src[pno])
                left, right = max(0.0, box.x0 - 10), min(src[pno].rect.width, box.x1 + 10)
                top, bottom = max(0.0, box.y0 - 8), min(src[pno].rect.height, box.y1 + 8)
                step = (bottom - top) / bands
                for b in range(bands):
                    y0 = top + step * b - (overlap / 2 if b else 0)
                    y1 = top + step * (b + 1) + (overlap / 2 if b < bands - 1 else 0)
                    label = "p%d-b%d" % (pno + 1, b + 1)
                    path = folder / ("%s_p%d_b%d.png" % (ch, pno + 1, b + 1))
                    size = appendix_tiles.sheet([(label, pno, fitz.Rect(left, y0, right, y1))], src, path, ZOOM, 1)
                    key["%s/%s" % (name, label)] = {"chapter": ch, "page": pno, "clip": [left, y0, right, y1]}
                    made += 1
            state.out("%s: %d pages, %d tiles in %s (last %dx%d)" % (
                name, len(src), made, folder.relative_to(state.ROOT).as_posix(), size[0], size[1]))
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "tiles.json").write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8", newline="\n")


def zoom(folder, label, x0, y0, x1, y1):
    """Part of a tile drawn from the PDF at up to twice the tile's size. The corners are fractions of the tile, 0 to 1."""
    key = json.loads((WORK / "tiles.json").read_text(encoding="utf-8"))
    t = key.get("%s/%s" % (folder, label))
    if not t:
        sys.exit("no tile %r in %r" % (label, folder))
    cx0, cy0, cx1, cy1 = t["clip"]
    x0, x1 = sorted((min(1.0, max(0.0, x0)), min(1.0, max(0.0, x1))))
    y0, y1 = sorted((min(1.0, max(0.0, y0)), min(1.0, max(0.0, y1))))
    clip = fitz.Rect(cx0 + (cx1 - cx0) * x0, cy0 + (cy1 - cy0) * y0, cx0 + (cx1 - cx0) * x1, cy0 + (cy1 - cy0) * y1)
    if clip.width < 5 or clip.height < 5:
        sys.exit("the part asked for is empty")
    factor = min(2 * ZOOM, 1500.0 / clip.width, 1500.0 / clip.height)
    src = fitz.open(str(appendix_tiles.find_pdf(CHAPTERS[t["chapter"]]["pdf"])))
    out = WORK / folder / "crops"
    out.mkdir(parents=True, exist_ok=True)
    path = out / ("%s_%03d-%03d_%03d-%03d.png" % (label, round(x0 * 100), round(x1 * 100), round(y0 * 100), round(y1 * 100)))
    src[t["page"]].get_pixmap(matrix=fitz.Matrix(factor, factor), clip=clip, alpha=False).save(str(path))
    print(path)


# The project's own summary of each section, and the sentences of Parks that settle something the project asks.
# Written after the readings, from them; a summary is not Parks's text. Keys are the printed headings.
NOTES = {
    "ch2": [
        {"heading": "Sounds and Alphabet", "pages": [13],
         "summary": "Skiri has nine consonants and three vowels, each vowel short and long: fifteen phonemes (tables 2 and 3)."},
        {"heading": "Consonants", "pages": [13, 14],
         "summary": "p, t, k and c are always voiceless and unaspirated, like English stops after s. c has two regular variants: "
                    "[ts] before a consonant and at the end of a word, [č] before a vowel. s is as in English for most speakers, "
                    "further back (like sh) for some. h is as in English, breathier before a consonant. w is as in English. r is "
                    "usually a tap; at the start of a word many speakers often say it as [n], and some occasionally as [l]."},
        {"heading": "Vowels", "pages": [14, 15],
         "summary": "i and ii are front, u and uu back and rounded, a and aa central. The short vowels have tense and lax variants: "
                    "for i the chapter gives lax [ɪ]; u varies between tense [u] and lax [ʊ]; a between lower [a] and higher [ə]. "
                    "Long vowels are always tense. Length is usually clear, but before h or a syllable-final consonant measured "
                    "length varies widely, and some prefixes and stems alternate between a long and a short vowel (raar-/rar-, "
                    "-taakaa/-taka, asaa-/asa-). Stress is not phonemic and is not written on words; the phonetic forms of entries "
                    "mark accented syllables. Some accent patterns recur (the first syllable, or the second when the first is short "
                    "and the second long; the third from the end, less often the second from the end), but the chapter calls most "
                    "patterns variable in the end.",
         "quoted": [(14, "This alternation occurs frequently, but the difference in vowel length is not predictable."),
                    (15, "Stress is not phonemic in Skiri and hence is not marked on words. (Phonetic forms in entries do, however, "
                         "have accented syllables marked.)")],
         "bears_on": "open items 9 (the word for the marks), 40 (accent rules), 43 (tense and lax short vowels), and questions 1, 2 "
                     "and 7 of the word-construction analysis (vowel length)"},
        {"heading": "Skiri Alphabet", "pages": [15],
         "summary": "The alphabet is the fifteen phonemic symbols. Because only two consonants and the three vowels have variants it "
                    "is close to phonetic; every entry still gives a phonetic form. Alphabetical order in the Skiri-to-English "
                    "section: a, aa, c, h, i, ii, k, p, r, s, t, u, uu, w. The glottal stop occurs only between vowels and at the "
                    "end of a word after a vowel, where it mainly sets non-subordinate imperfective verb forms (with it) apart "
                    "from subordinate ones (without); it is passed over in alphabetical order."},
        {"heading": "Speaker Variation", "pages": [15, 16],
         "summary": "The Skiri and South Band speakers Parks worked with from 1965 on kept their dialects apart; Weltfish's forecast "
                    "of 1937 that the differences would level did not come true for them. One Skiri speaker, Harry Mad Bear, "
                    "sometimes used the South Band vowel e in texts (reesaaruʔ for riisaaruʔ 'chief', he for hi 'and'). "
                    "Late-twentieth-century Skiri speech was uniform and close to that of Roaming Scout a century earlier."},
        {"heading": "The Cluster kt", "pages": [16],
         "summary": "In Skiri k became t before t (kt to tt). Roaming Scout's texts have tt in nearly 70 percent of the cases; Murie, "
                    "the speakers Lesser and Weltfish worked with, and all speakers Parks worked with in the 1960s and 1970s had tt "
                    "throughout, except Mrs. Pratt, who consistently said kt. The dictionary writes kt, following her.",
         "quoted": [(16, "In this dictionary forms are written with kt rather than tt in conformance with Mrs. Pratt’s usage throughout "
                         "our collaboration, but users should realize that all other twentieth-century Skiri speakers replaced kt "
                         "clusters with tt.")],
         "bears_on": "the pronunciation guide and the respelling: every kt of the dictionary was tt for the other speakers"},
        {"heading": "Other Sound Differences", "pages": [16, 17],
         "summary": "Three more differences between Roaming Scout and twentieth-century speakers: kirikii 'what' is now usually "
                    "kikii; the imperfective distributive of aar 'to become' is waahi where Roaming Scout often said waari (South "
                    "Band waahri, Arikara waahnu); ut- + uks- is ucuks- today and icuks in Roaming Scout's speech, as in South "
                    "Band; si- + ar- (siʔah-) is now usually contracted to siih-, which Roaming Scout did not do."},
    ],
    "ch5": [
        {"heading": "Organization of the Dictionary", "pages": [53],
         "summary": "Two sections, English-to-Skiri first because most users will not be speakers; entries in both hold the same "
                    "information."},
        {"heading": "General Conventions for Citing Skiri Forms", "pages": [53, 54],
         "summary": "Verbs are cited as uninflected stems, which never occur as words. A stem that needs a preverb (ir-/a-, ut-, "
                    "uur-) has it in parentheses after the stem, as in tii (ut...); in a word the preverb comes before the stem. A "
                    "few stems have a zero base, Ø (ut...) 'to be (in a condition)' and Ø (ir...) 'to be one's'; in their "
                    "non-subordinate forms the vowel of the preverb, or of a subject plural prefix after it, is reduplicated. "
                    "Nouns are cited in their independent form, with the nominal suffix they need (-uʔ NOM, -hiriʔ INST/LOC, -kat "
                    "LOC, -ru LOC); the suffix is absent when the noun is incorporated or stands first in a compound. Dependent "
                    "noun roots (N-DEP), which occur only before another stem, are cited with a final dash (asaa- 'horse; dog', "
                    "as in asaaki 'dog'). Locatives that occur only in derived forms are also cited with a final dash (iis- 'out "
                    "of sight'). Other classes are cited in their independent forms.",
         "bears_on": "open item 13 (noun possession: the suffix -hiriʔ, and asaaki 'dog' printed here a third time without a final "
                     "glottal stop)"},
        {"heading": "English-to-Skiri Entries", "pages": [55, 56, 57, 58],
         "summary": "An entry begins with the English word in bold; each Skiri translation begins a subentry of up to three parts. "
                    "Part I: the Skiri word or stem in bold; its phonetic form in square brackets, with small bullets between "
                    "syllables; the class in small capitals, followed by a dash for dependent elements or by the verb class, which "
                    "rests on the verb's subordinate form; grammatical forms in curly brackets where they are irregular (usually "
                    "for a dual or plural agent, or the distributive); the English glosses, numbered when there are several, with "
                    "clarifying phrases in italics; the derivation in angled brackets, with a hyphen between morphemes inside a "
                    "stem and a plus sign between major constituents, then a literal translation, sometimes with cognates from "
                    "South Band, Arikara, Kitsai or Wichita. Part II: for verbs the five standard forms; for a dependent form, "
                    "derived stems that contain it. Part III: cross-references, beginning with 'see', each an English entry head "
                    "followed by its Skiri equivalent in curly brackets.",
         "quoted": [(56, "(1) first person agent (for active, descriptive, and locative verbs) or first person patient (for passive "
                         "verbs), in the indicative mode, perfective aspect; (2) third person agent or patient, indicative mode, "
                         "perfective aspect; (3) third person agent, indicative mode, imperfective aspect; (4) third person agent, "
                         "gerundial mode (i.e., subordinate absolutive mode), usually perfective aspect; and (5) third person "
                         "agent, indicative mode, intentive aspect."),
                    (57, "Certain verb classes do not allow some of these forms and thus are lacking here.")],
         "bears_on": "the five verb forms of every entry (form 1 of a passive verb is a first person patient; form 4 is 'usually' "
                     "perfective); the English index (scripts/repair_english_index.py reads the entries by this structure)"},
        {"heading": "Skiri-to-English Entries", "pages": [58, 59, 60],
         "summary": "The same structure without subentries. The head is a stem or root for verbs and the independent form for "
                    "nouns, with a final dash for dependent nouns and locatives. After it come the phonetic form, the class, "
                    "entry-specific information in curly brackets (grammatical forms for verbs; for most nouns the variant shapes "
                    "the noun takes when it is incorporated), the glosses and the derivation. Part II holds the same five forms, "
                    "or derived forms, as in the English section. Figure 6 shows a compound of the zero verb stem with a noun, "
                    "Ø (ut...) ciksuʔ; such collocations are cited with the verb base first, though the noun may come first in "
                    "speech."},
    ],
}
READERS = {"ch2": (["ch2_a"], ["ch2_b"]), "ch5": (["ch5_a", "ch5_a2"], ["ch5_b"])}


def norm(text):
    text = unicodedata.normalize("NFC", text or "").replace("…", "...")
    return re.sub(r"\s+", " ", text).strip()


def plain(text):
    """For comparing: quotation marks and italic asterisks aside."""
    return norm(text).replace("’", "'").replace("‘", "'").replace("*", "")


def cut_down(reading):
    """A reading without its running text: forms, tables, headings, example lines and figure labels."""
    kept = {}
    for page, v in reading.items():
        blocks = v.get("blocks") or []
        kept[page] = {
            "book_page": v.get("book_page", ""),
            "forms": v.get("forms") or [],
            "headings": [norm(b.get("text")) for b in blocks if b.get("type") == "heading"],
            "tables": [{"title": norm(b.get("title")), "rows": b.get("rows") or []} for b in blocks if b.get("type") == "table"],
            "examples": [norm(b.get("text")) for b in blocks if b.get("type") == "example"],
            "figures": [{"caption": norm(b.get("caption")), "labels": b.get("labels") or []} for b in blocks if b.get("type") == "figure"]
                       + [{"caption": norm(f.get("caption")), "labels": f.get("labels") or [], "forms": f.get("forms") or [],
                           "phonetic": f.get("phonetic") or []} for f in v.get("figures") or []],
        }
    return kept


def running_text(page):
    return plain(" ".join(b.get("text") or "" for b in page.get("blocks") or [] if b.get("type") in ("para", "item"))).split()


def load(name):
    """(the reading cut down, the full reading or None). The full one exists only while the work folder does."""
    work = WORK / name / "reading.json"
    kept = READINGS / ("front_matter_%s.json" % name)
    if work.exists():
        full = json.loads(work.read_text(encoding="utf-8"))
        return cut_down(full), full
    if kept.exists():
        return json.loads(kept.read_text(encoding="utf-8")), None
    sys.exit("no reading for %s: neither %s nor %s" % (name, work, kept))


def grade(write):
    old = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {}
    record = {"made": dt.date.today().isoformat(), "chapters": {}}
    stored = {}
    for ch, info in CHAPTERS.items():
        a_names, b_names = READERS[ch]
        A, B, full_a, full_b = {}, {}, {}, {}
        for names, target, full in ((a_names, A, full_a), (b_names, B, full_b)):
            for name in names:
                cut, whole = load(name)
                target.update(cut)
                if whole is not None:
                    full.update(whole)
                    path = READINGS / ("front_matter_%s.json" % name)
                    path.write_text(json.dumps(cut, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        pages = sorted(B, key=lambda k: int(k[1:]))
        forms, differ, tables, figures = [], [], [], []
        text_words = text_differ = 0
        for page in pages:
            book = info["first_book_page"] + int(page[1:]) - 1
            for side in (A, B):
                printed = side.get(page, {}).get("book_page")
                if printed and int(printed) != book:
                    sys.exit("%s %s: the page prints %s, expected %d" % (ch, page, printed, book))
            fa = [[norm(x) for x in f] + [""] * (3 - len(f)) for f in A.get(page, {}).get("forms", [])]
            fb = [[norm(x) for x in f] + [""] * (3 - len(f)) for f in B[page].get("forms", [])]
            sm = difflib.SequenceMatcher(None, [f[0] for f in fa], [f[0] for f in fb], autojunk=False)
            for tag, i0, i1, j0, j1 in sm.get_opcodes():
                if tag == "equal":
                    for i, j in zip(range(i0, i1), range(j0, j1)):
                        row = {"page": book, "form": fb[j][0], "phonetic": "", "gloss": "", "readings": 2}
                        for n, field in ((1, "phonetic"), (2, "gloss")):
                            x, y = fa[i][n], fb[j][n]
                            if plain(x).lower() == plain(y).lower():
                                row[field] = y
                            elif x and y:
                                row[field + "_reading_a"], row[field + "_reading_b"] = x, y
                                differ.append({"page": book, "form": fb[j][0], "what": field, "reading_a": x, "reading_b": y})
                            else:                     # one reader put it in this column, the other left the column empty
                                row[field + "_one_reader"] = x or y
                        forms.append(row)
                else:
                    for f in fa[i0:i1]:
                        forms.append({"page": book, "form": f[0], "phonetic": f[1], "gloss": f[2], "readings": 1, "reader": "A"})
                        differ.append({"page": book, "form": f[0], "what": "listed by reader A only"})
                    for f in fb[j0:j1]:
                        forms.append({"page": book, "form": f[0], "phonetic": f[1], "gloss": f[2], "readings": 1, "reader": "B"})
                        differ.append({"page": book, "form": f[0], "what": "listed by reader B only"})
            ta, tb = A.get(page, {}).get("tables", []), B[page].get("tables", [])
            for n, t in enumerate(tb):
                rows_b = [[plain(c) for c in r] for r in t["rows"]]
                rows_a = [[plain(c) for c in r] for r in ta[n]["rows"]] if n < len(ta) else None
                tables.append({"title": t["title"], "page": book, "rows": rows_b, "readings": 2 if rows_a == rows_b else 1})
                if rows_a != rows_b:
                    differ.append({"page": book, "form": t["title"], "what": "table cells", "reading_a": rows_a, "reading_b": rows_b})
            fig_a = A.get(page, {}).get("figures", [])
            for n, f in enumerate(B[page].get("figures", [])):
                same = n < len(fig_a) and plain(fig_a[n]["caption"]) == plain(f["caption"])
                figures.append({"page": book, "caption": plain(f["caption"]), "labels": f["labels"], "caption_in_both_readings": same})
            if ch == "ch2" and page in full_a and page in full_b:
                wa, wb = running_text(full_a[page]), running_text(full_b[page])
                text_words += len(wb)
                text_differ += sum(1 for tag, *_ in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes() if tag != "equal")
        both = sum(1 for f in forms if f["readings"] == 2)
        entry = {"pages": "%d-%d" % (info["first_book_page"], info["first_book_page"] + len(pages) - 1),
                 "forms": len(forms), "forms_in_both_readings": both, "tables": len(tables),
                 "tables_in_both_readings": sum(1 for t in tables if t["readings"] == 2), "figures": len(figures),
                 "places_where_the_readings_differ": differ}
        if ch == "ch2":
            entry["running_text"] = ({"words": text_words, "places_that_differ": text_differ} if text_words
                                     else (old.get("chapters", {}).get(ch, {}).get("running_text") or "not counted: the full readings are gone"))
        else:
            entry["running_text"] = "not compared: reading A was stopped by the content filter and has its text shortened"
        record["chapters"][ch] = entry
        state.out("%s (pp. %s): %d forms, %d in both readings letter for letter; %d tables, %d the same in both; %d places differ%s" % (
            info["title"], entry["pages"], len(forms), both, len(tables), entry["tables_in_both_readings"], len(differ),
            ("; running text %(words)d words, %(places_that_differ)d places differ" % entry["running_text"]) if isinstance(entry["running_text"], dict) else ""))
        for d in differ:
            state.out("    p. %s %s: %s  A %s | B %s" % (d["page"], d["form"], d["what"], d.get("reading_a", ""), d.get("reading_b", "")))
        headings = [h for page in pages for h in B[page].get("headings", [])]
        for note in NOTES[ch]:
            if not any(plain(note["heading"]) == plain(h) for h in headings):
                sys.exit("%s: the heading %r of NOTES is not a heading of reading B: %s" % (ch, note["heading"], headings))
        stored[ch] = {
            "_about": {
                "source": "Parks and Pratt, A Dictionary of Skiri Pawnee (2008), chapter %d, \"%s\", pp. %s" % (info["chapter"], info["title"], entry["pages"]),
                "read": "2026-11-14, twice, from the page images, by readers who saw nothing but the page (scripts/source_audit/front_matter_reading.py)",
                "what_is_here": "Every Skiri form of the chapter with the phonetic form and the gloss printed beside it, the tables, the "
                                "section headings and the figure captions, as printed. A form marked \"readings\": 2 stands letter for "
                                "letter in both readings.",
                "what_is_not_here": "The chapter's running text. Each section has a summary in the project's own words; it is not "
                                    "Parks's text. The sentences under \"quoted\" are his.",
                "notation": "The lax short vowels are printed with a letter like a small iota and one like an upsilon; they are "
                            "stored as ɪ and ʊ, the symbols the dictionary's phonetic forms are stored in. No accent mark is printed "
                            "in either chapter outside figure 6.",
                "agreement": {k: v for k, v in entry.items() if k != "places_where_the_readings_differ"},
            },
            "sections": [{"heading": n["heading"], "pages": n["pages"], "summary": n["summary"],
                          "quoted": [{"page": pg, "text": t} for pg, t in n.get("quoted", [])],
                          **({"bears_on": n["bears_on"]} if n.get("bears_on") else {})} for n in NOTES[ch]],
            "tables": tables, "figures": figures, "forms": forms,
        }
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.out("record: %s" % RECORD.relative_to(state.ROOT).as_posix())
    if write:
        for ch, info in CHAPTERS.items():
            path = state.ROOT / "extracted_data" / info["out"]
            path.write_text(json.dumps(stored[ch], ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            state.out("written: %s" % path.relative_to(state.ROOT).as_posix())
    else:
        state.out("run again with --write to write the two files in extracted_data/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheets", action="store_true", help="cut the pages into tiles, one folder per reader")
    ap.add_argument("--zoom", nargs=6, metavar=("FOLDER", "TILE", "X0", "Y0", "X1", "Y1"),
                    help="draw part of a tile larger; corners as fractions of the tile")
    ap.add_argument("--write", action="store_true", help="write the joined chapters to extracted_data/")
    args = ap.parse_args()
    if args.sheets:
        sheets()
    elif args.zoom:
        zoom(args.zoom[0], args.zoom[1], *[float(v) for v in args.zoom[2:]])
    else:
        grade(args.write)


if __name__ == "__main__":
    main()
