#!/usr/bin/env python3
"""Shared helpers for the morphology_v2 pipeline (paths, normalisation, IO).

Nothing here writes to the database: every connection is opened read-only.
"""
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "skiri_pawnee.db"
OUT = ROOT / "curriculum" / "roots_v2"
GOLD = OUT / "gold"
V1 = ROOT / "curriculum" / "roots"
EXTRACTED = ROOT / "extracted_data"
BB_TEXT = ROOT / "pari pakuru" / "Blue_Book_Pari_Pakuru.txt"
S2E_PAGES = ROOT / "Dictionary Data" / "split_pdf_pages_SKIRI_TO_ENGLISH"
PAGE_INDEX = ROOT / "reports" / "_s2e_page_index.json"

sys.path.insert(0, str(ROOT / "scripts"))

SEED = 20261112


def out(text=""):
    """Console-safe print (the Windows console is cp1252)."""
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def connect(db=DB_PATH):
    """Read-only connection: the pipeline must never modify the database."""
    uri = "file:" + Path(db).as_posix() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def norm(s):
    """NFC, unify glottal-stop spellings, strip."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", s)
    # '?' is NOT mapped: it is the Blue Book question particle and Parks's doubt mark
    for ch in ("’", "'", "‘", "ˀ"):
        s = s.replace(ch, "ʔ")
    return s.strip()


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s)
                   if unicodedata.category(ch) != "Mn")


def headword_alternates(hw):
    """All alternate spellings of a headword, accents stripped, lower-cased.

    'caas, icaas' -> ['caas', 'icaas'];  'rirahak [+ raar-]' -> ['rirahak'];
    'itkatapiirahc/raʔac' is kept whole (Parks's slash alternation is resolved
    by the caller);  bound-form hyphens are removed.
    """
    hw = norm(hw)
    hw = re.sub(r"\[.*?\]", "", hw)
    hw = re.sub(r"\(\s*[a-z]+\s*\.\s*\.\s*\.\s*\)", "", hw)   # (ut...) preverb note
    alts = []
    for a in hw.split(","):
        a = strip_accents(a.strip()).lower()
        a = a.strip("-").strip()
        if a:
            alts.append(a)
    return alts


def headword_key(hw):
    alts = headword_alternates(hw)
    return alts[0] if alts else ""


VOWELS = "aiu"


def syllable_count(s):
    """Number of vowel nuclei (a long vowel is one nucleus)."""
    return len(re.findall(r"a+|i+|u+", strip_accents(norm(s)).lower()))


def segments(s):
    """Phoneme-ish segments: long vowels are one segment."""
    return re.findall(r"aa|ii|uu|.", s)


def skeleton(s):
    """Length-, glottal- and h-insensitive comparison key (a *tolerance*, not a match)."""
    s = strip_accents(norm(s)).lower()
    s = re.sub(r"([aiu])\1+", r"\1", s)
    return s.replace("ʔ", "").replace("h", "")


def dump_json(path, obj):
    """Deterministic JSON writer (sorted keys, LF newlines)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")


def dump_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path):
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_file_for(page_number, headword, page_index):
    """Resolve a DB page_number to a split-PDF file name.

    The DB mixes two conventions: values <= 181 are split-file numbers, larger
    values are printed book pages (349-529, book page = file number + 348).
    The text layer is used to confirm that the headword really is on the page.
    Returns (file_name, book_page, verified) or (None, None, False).
    """
    if page_number is None:
        return None, None, False
    by_file = page_index["_by_file"]
    cands = []
    if page_number <= 181:
        cands.append("page_%03d.pdf" % page_number)
    if str(page_number) in page_index:
        cands.append(page_index[str(page_number)]["file"])
    hw0 = norm(headword).split(",")[0].split("[")[0].split("(")[0].strip()
    for f in cands:
        if f in by_file and hw0 and hw0 in norm(by_file[f]["text"]):
            return f, by_file[f]["book_page"], True
    if cands and cands[0] in by_file:
        return cands[0], by_file[cands[0]]["book_page"], False
    return None, None, False


def load_page_index():
    idx = load_json(PAGE_INDEX)
    by_file = {}
    for book_page, v in idx.items():
        by_file[v["file"]] = {"book_page": int(book_page), "text": v["text"]}
    idx["_by_file"] = by_file
    return idx
