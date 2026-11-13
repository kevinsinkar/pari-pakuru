#!/usr/bin/env python3
"""
Parks's phonetic notation, as stored since 2026-11-13
=====================================================

The database stores a phonetic form exactly as Parks prints it:

    [huu·kɪ·wɪ́h·kə·haa·rʊʔ]        a raised dot between syllables
    [–huuk·tɪ{k/t}–]               a dash at each edge of a form that cannot stand alone
    ə́ ɪ́ ʊ́   ə̀ ɪ̀ ʊ̀                 a short (lax) vowel with an acute or a grave accent
    á í ú   à ì ù                  the second half of a long (tense) vowel with an accent
    (h)  {k/t}                     an optional sound; a final consonant that alternates

Until that date it stored the same forms in a working notation that came from
how the PDF's text layer encodes them: a hyphen for the syllable dot, a bullet
for the edge dash, à for ə́ and í for ɪ́ (which lost the difference between the
lax and the tense i).

The respelling code was written for the working notation. to_working() gives
it what it expects, so that the stored form can be Parks's own and the
respelling rules stay as they were. Nothing stored is ever converted back.
"""
import unicodedata

ACUTE, GRAVE = "́", "̀"
SYLLABLE_DOT = "·"
EDGE_DASH = "–"


def is_parks_notation(pf):
    """True when a stored form uses the printed syllable dot or edge dash (and so is not in the old working notation)."""
    return SYLLABLE_DOT in (pf or "") or EDGE_DASH in (pf or "")


def to_working(pf, old_vowels=False):
    """Parks's printed notation -> the notation the respelling code reads.

    old_vowels: also write the accented lax vowels with the letters the 2026-03 code knows
    (à í ì ú ù), for scripts/respell_and_normalize.py.
    """
    if not pf:
        return pf
    s = unicodedata.normalize("NFC", pf).replace(SYLLABLE_DOT, "-").replace(EDGE_DASH, "•")
    if old_vowels:
        for a, b in (("ə" + ACUTE, "à"), ("ə" + GRAVE, "à"), ("ɪ" + ACUTE, "í"), ("ɪ" + GRAVE, "ì"), ("ʊ" + ACUTE, "ú"), ("ʊ" + GRAVE, "ù")):
            s = s.replace(unicodedata.normalize("NFC", a), b)
    return s
