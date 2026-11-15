#!/usr/bin/env python3
"""Shared helpers for the engines review of November 2026.

Nothing here changes an engine, the database or a data file. The database is
opened read-only; results are written only into reports/engines_review/.

The engines are imported from scripts/ exactly as they are and called as the
web app and their own tests call them.
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
EXTRACTED = ROOT / "extracted_data"
OUT = ROOT / "reports" / "engines_review"
DATA = OUT / "data"
TESTSETS = DATA / "testsets"
GOLD = ROOT / "curriculum" / "roots_v2" / "gold"

# the engines import one another by bare name
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "morphology_v2"))


def out(text=""):
    """Console-safe print (the Windows console is cp1252)."""
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))


def connect(db=DB_PATH):
    """Read-only connection."""
    conn = sqlite3.connect("file:" + Path(db).as_posix() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    """Deterministic JSON, so that a second run gives the same bytes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    return hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            f.write(line)
            h.update(line.encode("utf-8"))
    return h.hexdigest()


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Comparing a produced form with a printed one
# ---------------------------------------------------------------------------

GLOTTALS = "ʔ'’‘"


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def strip_accents(s):
    """Remove accent marks, keep every letter (ʔ included)."""
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")


def has_accent(s):
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", s or ""))


def clean(s):
    """A printed form as a plain word: no hyphen of notation, one glottal sign."""
    s = nfc(s).strip()
    for g in "'’‘":
        s = s.replace(g, "ʔ")
    return s.replace("-", "").replace(" ", "")


def variants(printed):
    """The forms printed in one cell (Parks separates alternatives with a comma or semicolon)."""
    return [clean(v) for v in re.split(r"[;,]", printed or "") if clean(v)]


def short_vowels(s):
    """Every long vowel written short: what is left when vowel length is ignored."""
    return re.sub(r"([aiu])\1+", r"\1", s)


def no_glottal(s):
    return s.replace("ʔ", "")


def edit_distance(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]


# What a produced form can differ in without any other letter being wrong.
# Applied in this order, so that aʔa, aa and a count as the same once both the
# glottal stop and vowel length are set aside.
_IGNORABLE = [("accent", strip_accents), ("glottal stop", no_glottal), ("vowel length", short_vowels)]

CAUSES = [
    "exact",
    "accent only",
    "vowel length only",
    "glottal stop only",
    "vowel length and glottal stop",
    "accent and vowel length",
    "accent and glottal stop",
    "accent, vowel length and glottal stop",
    "other letters, within two",
    "other letters, further off",
    "no form produced",
]

_LABEL = {
    (): "exact",
    ("accent",): "accent only",
    ("vowel length",): "vowel length only",
    ("glottal stop",): "glottal stop only",
    ("glottal stop", "vowel length"): "vowel length and glottal stop",
    ("accent", "vowel length"): "accent and vowel length",
    ("accent", "glottal stop"): "accent and glottal stop",
    ("accent", "glottal stop", "vowel length"): "accent, vowel length and glottal stop",
}


def _smallest_set(p, b):
    """The fewest things to set aside for p to equal b, or None when another letter differs."""
    import itertools
    for n in range(len(_IGNORABLE) + 1):
        for combo in itertools.combinations(range(len(_IGNORABLE)), n):
            x, y = p, b
            for i in combo:
                x, y = _IGNORABLE[i][1](x), _IGNORABLE[i][1](y)
            if x == y:
                return tuple(_IGNORABLE[i][0] for i in combo)
    return None


def classify_one(produced, printed):
    p, b = clean(produced), clean(printed)
    found = _smallest_set(p, b)
    if found is not None:
        return _LABEL[found]
    d = edit_distance(strip_accents(p), strip_accents(b))
    return "other letters, within two" if d <= 2 else "other letters, further off"


def classify(produced, printed_variants):
    """How does a produced form differ from what is printed?

    Returns (cause, the printed variant it was compared with). Where Parks
    prints two forms in one cell the produced form is compared with each and
    the nearer one counts, so an engine is not blamed for giving his second
    alternative.
    """
    if not printed_variants:
        raise ValueError("no printed form")
    if not produced:
        return "no form produced", printed_variants[0]
    scored = []
    for v in printed_variants:
        cause = classify_one(produced, v)
        scored.append((CAUSES.index(cause), edit_distance(strip_accents(clean(produced)), strip_accents(v)), v, cause))
    scored.sort()
    return scored[0][3], scored[0][2]


# Coarser groups used in the summaries
def group_of(cause):
    if cause == "exact":
        return "exact"
    if cause in ("other letters, within two", "other letters, further off", "no form produced"):
        return cause
    return "letters right; accent, vowel length or glottal stop differ"


def tally(rows, key="cause"):
    counts = {c: 0 for c in CAUSES}
    for r in rows:
        counts[r[key]] = counts.get(r[key], 0) + 1
    return counts


def pct(n, d):
    return "%.1f%%" % (100.0 * n / d) if d else "n/a"


def md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The engines as reviewed
# ---------------------------------------------------------------------------
# Stages 1 and 2 measured nine engine files as they stood in commit 814e8cc. Stage 4 carried out the owner's
# decisions: four files were withdrawn to archived/scripts/, the others repaired or rebuilt, tables dropped.
# A measurement script run on today's files would measure something else and write over the record.
REVIEWED_COMMIT = "814e8cc"
REVIEWED_FILES = {
    "scripts/morpheme_inventory.py": "f223a23448d21b02d5ee7fe074db83295b1092d6",
    "scripts/accent_rules.py": "3c9cd5d225e413853ac1a4f311fd7213e311e1e1",
    "scripts/sound_changes.py": "0309d3a13f0130809363bac288a2033af43581b9",
    "scripts/stem_extractor.py": "d78cc86bfaac1eac57eb38b0bb809880119db9ca",
    "scripts/person_forms.py": "fb52c1ade6062339dae63326e10894c3e716bd72",
    "scripts/possession_engine.py": "a4c0f17b33614a1ac16d75669f6b3a88bc18d45f",
    "scripts/noun_possession.py": "fbc3614df2f0336790551de3075afad10d758d35",
    "scripts/sentence_templates.py": "79511de28742873f56aa13aa332723d97eed4716",
    "scripts/template_slot_fillers.py": "64cb4c782511aa9a74acf329aee8c1a819617f9f",
}


def git_blob_id(path):
    """The id git gives a file's content (line endings as git stores them)."""
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def engines_changed_since_review():
    """The engine files that are not where and what they were when the review measured them."""
    changed = []
    for rel, blob in REVIEWED_FILES.items():
        path = ROOT / rel
        if not path.exists():
            changed.append(rel + " (moved or removed)")
        elif git_blob_id(path) != blob:
            changed.append(rel + " (changed)")
    return changed


def require_reviewed_state(script):
    """Stop a Stage 1 or 2 script unless the engines are the files the review measured."""
    changed = engines_changed_since_review()
    if not changed:
        return
    out("%s measures the grammar engines as they were reviewed on 2026-11-14: the files of commit %s."
        % (Path(script).name, REVIEWED_COMMIT))
    out("Since then the owner's decisions were carried out (Stage 4), and %d of the nine engine files are no "
        "longer those files:" % len(changed))
    for line in changed:
        out("  " + line)
    out("Nothing was run and nothing was written: the record of the review stays as it is, in "
        "reports/engines_review/data/.")
    out("To make that record again, see \"Making the Stage 2 figures again\" in scripts/engines_review/README.md.")
    raise SystemExit(2)
