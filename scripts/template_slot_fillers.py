"""The printed sentences and words the sentence builder starts from.

Rewritten on 2026-11-14 (engines review, decision 8). Until then this file
held forty words typed from the OCR text of the Blue Book: three of them do
not exist (OCR slips for an accented vowel), none carried the printed accent,
and six were dictionary spellings offered as Blue Book words.

Now nothing here is typed from memory or from the OCR text. Every Pawnee form
in this file is named by the place it is copied from:

    bb(row, text)             a row of the table blue_book_attestations: the
                              Blue Book form as read from the scan
    entry(entry_id, headword) an entry of the dictionary (Parks)

and `python scripts/sentence_templates.py --check` fails if the text is not,
letter for letter and accent for accent, what that row or entry holds. A form
may not appear in this file, or in sentence_templates.py, in any other way.

A FRAME is a sentence the Blue Book prints. Some of its words may be swapped
for another printed word of the same kind; "slots" says which, by the place
of the word in the sentence (0 is the first word). The other words of the
frame stay as printed, accents included.
"""


def bb(row, text):
    """A Blue Book form: the row of blue_book_attestations it is copied from, and its text there."""
    return {"row": row, "text": text}


def entry(entry_id, headword):
    """A dictionary entry: its id and its headword as stored."""
    return {"entry_id": entry_id, "headword": headword}


# template id -> its name, what it says in English, and the printed sentences it starts from
FRAMES = {
    "T1": {
        "name": "Identification",
        "english_pattern": "This is [thing]",
        "frames": [
            {"frame": bb(1903, "Tí hitu'."), "slots": {"noun": [1]}},
        ],
    },
    "T2": {
        "name": "Descriptive",
        "english_pattern": "[Thing] is [quality]",
        "frames": [
            {"frame": bb(1947, "Rakis tí pahaat."), "slots": {"noun": [0], "quality": [1, 2]}},
        ],
    },
    "T3": {
        "name": "Yes/No Question",
        "english_pattern": "Is [thing] [quality or action]?",
        "frames": [
            {"frame": bb(1948, "Ka rá•pahaat rakis?"), "slots": {"verb_form": [1], "noun": [2]}},
        ],
    },
    "T4": {
        "name": "What Question",
        "english_pattern": "What is it? What is [subject] doing?",
        "frames": [
            {"frame": bb(1902, "Kiriké ru'?"), "slots": {"verb_form": [1]}},
            {"frame": bb(2072, "Pita kiriké rut•ari'?"), "slots": {"subject": [0], "verb_form": [2]}},
        ],
    },
    "T5": {
        "name": "Where Question",
        "english_pattern": "Where did you go? Where has [subject] gone?",
        "frames": [
            {"frame": bb(2404, "Kiru rásuks•at?"), "slots": {"verb_form": [1]}},
            {"frame": bb(2262, "Kirú ra•'at rikutski?"), "slots": {"verb_form": [1], "noun": [2]}},
        ],
    },
    "T6": {
        "name": "Negation",
        "english_pattern": "No, it is not [thing]",
        "frames": [
            {"frame": bb(1908, "Kakí, kakí karitki."), "slots": {"noun": [2]}},
        ],
    },
    "T7": {
        "name": "Affirmation",
        "english_pattern": "Yes, this is [thing]",
        "frames": [
            {"frame": bb(1905, "Ahu', tí hitu'."), "slots": {"noun": [2]}},
        ],
    },
    "T8": {
        "name": "I did",
        "english_pattern": "I [did] ([place])",
        "frames": [
            {"frame": bb(2405, "Tatuks•at Pári."), "slots": {"verb_form": [0], "place": [1]}},
        ],
    },
    "T9": {
        "name": "He or she does",
        "english_pattern": "[Subject] [does] ([object])",
        "frames": [
            {"frame": bb(2521, "Rikutski ti•wáktahu'."), "slots": {"subject": [0], "verb_form": [1]}},
            {"frame": bb(2504, "Pitá ti•kuwutit kuruks."), "slots": {"subject": [0], "verb_form": [1], "object": [2]}},
        ],
    },
    "T10": {
        "name": "Command",
        "english_pattern": "[Do it]!",
        "frames": [
            {"frame": bb(2566, "Suks•teká•rikut."), "slots": {"command": [0]}},
        ],
    },
}

# What kind of printed word may stand in a slot:
#   "noun"    a single word the Blue Book lists and that is tied, by its exact form, to a noun of the dictionary
#   "phrase"  a listed phrase with as many words as the frame has in that place, beginning with the same word
#   "start"   a single word that begins as the frame's word begins, up to its first bullet
#   "word"    any single listed word, found by its English
SLOT_KINDS = {
    "noun": "noun", "subject": "noun", "object": "noun", "place": "noun",
    "quality": "phrase",
    "command": "start",
    "verb_form": "word",
}

# The question words of the dictionary, for sentences in the dictionary's spelling. Parks, Table 14, says that
# they take the absolutive mode. The yes/no question is a prefix in his spelling, not a word, so there is none.
PARKS_QUESTION_WORDS = {
    "where": entry("SK-kiruu-p97-1878", "kiruu"),
    "who": entry("SK-takii-p157-3072", "takii"),
    "what": entry("SK-kirikii,_kikii-p96-1834", "kirikii, kikii"),
}
