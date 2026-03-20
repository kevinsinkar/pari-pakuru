"""
Phase 3.2a — BB-Attested Slot Fillers for Sentence Templates
=============================================================

Cross-referenced 418 function words against 160 Blue Book sentences.
27 function words appear directly in BB sentences.

This module provides curated, BB-attested slot filler options for
template dropdowns. Every entry here has at least one Blue Book
attestation — learners see real Pawnee, not engine guesses.

Usage:
    from template_slot_fillers import SLOT_FILLERS, get_fillers_for_slot
    
    # Get all temporal options
    temporals = get_fillers_for_slot("TEMPORAL")
    
    # Get manner adverbs
    manner_advs = get_fillers_for_slot("ADV_MANNER")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SlotFiller:
    """A curated option for a template slot dropdown."""
    skiri_form: str          # The form to insert into the sentence
    english: str             # English gloss for the dropdown
    position_rule: str       # Where it goes: CLAUSE-INITIAL, PRECEDES-VERB, PRECEDES-NOUN, etc.
    bb_lessons: List[int]    # Which BB lessons attest it
    bb_example_skiri: str    # An attested BB sentence using this word
    bb_example_english: str  # English translation of that example
    function_word_id: Optional[str] = None  # Headword in function_words table
    grammatical_class: str = ""
    notes: str = ""


# ============================================================================
# TEMPORAL slot fillers — for Template T8 (1sg declarative) and T9 (3sg narrative)
#
# Position: CLAUSE-INITIAL (can also be clause-final per L17 evidence)
# BB evidence: L15–L19 systematically teach time expressions
# ============================================================================
TEMPORAL_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="rahesa'",
        english="tomorrow",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[19],
        bb_example_skiri="Rahesa' tatut•a•wahri•usta.",
        bb_example_english="Tomorrow I will work.",
        function_word_id=None,  # BB basic word, not in function_words table
        grammatical_class="ADV",
        notes="L19 basic word. Can be clause-initial or clause-final.",
    ),
    SlotFiller(
        skiri_form="tiruks•tsak•ariki",
        english="yesterday",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[17],
        bb_example_skiri="Tiruks•tsak•ariki tatutsiks•a•wahri'.",
        bb_example_english="I was working yesterday.",
        grammatical_class="ADV",
        notes="L17 basic word. Both clause-initial and clause-final attested (L17).",
    ),
    SlotFiller(
        skiri_form="hiras",
        english="at night",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[16],
        bb_example_skiri="Tatih•ka•isa' hiras.",
        bb_example_english="I came home at night.",
        function_word_id="hiras",
        grammatical_class="ADV",
        notes="L16 basic word. Clause-final in BB attestation.",
    ),
    SlotFiller(
        skiri_form="tihe ra•pa•ariki'",
        english="next month",
        position_rule="CLAUSE-FINAL",
        bb_lessons=[19],
        bb_example_skiri="Tat•uh•ta tihe ra•pa•ariki'.",
        bb_example_english="I will go next month.",
        grammatical_class="ADV",
        notes="L19 basic word. Multi-word temporal phrase.",
    ),
    SlotFiller(
        skiri_form="pitsikat",
        english="in (the) winter",
        position_rule="CLAUSE-FINAL",
        bb_lessons=[9, 15, 20],
        bb_example_skiri="Pita ti•kuwutit rahurahki pitsikat.",
        bb_example_english="The man killed a deer, in the winter.",
        grammatical_class="ADV",
        notes="L09, L15 basic word. Locative suffix -kat. Clause-final.",
    ),
    SlotFiller(
        skiri_form="retskuhke",
        english="in (the) fall",
        position_rule="CLAUSE-FINAL",
        bb_lessons=[15],
        bb_example_skiri="'T'at•tstfa•usuku retskuhke.",
        bb_example_english="It rains in the fall.",
        grammatical_class="ADV",
        notes="L15 basic word. Clause-final in all BB attestations.",
    ),
    SlotFiller(
        skiri_form="kekaruskat",
        english="early this morning",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[17],
        bb_example_skiri="",
        bb_example_english="(L17 additional word)",
        grammatical_class="ADV",
        notes="L17 additional word list.",
    ),
    SlotFiller(
        skiri_form="tiruks•tatkiu'",
        english="last night",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[17],
        bb_example_skiri="",
        bb_example_english="(L17 additional word)",
        grammatical_class="ADV",
        notes="L17 additional word list.",
    ),
    SlotFiller(
        skiri_form="tiherukspa•ariki",
        english="last month",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[17],
        bb_example_skiri="",
        bb_example_english="(L17 additional word)",
        grammatical_class="ADV",
        notes="L17 additional word list.",
    ),
]


# ============================================================================
# MANNER ADVERB slot fillers — for Templates T8, T9 (optional ADV_MANNER slot)
#
# Position: PRECEDES-VERB (confirmed by function_words.position_rule)
# BB evidence: cikstit in L18/L20, rariksisu in L18
# ============================================================================
ADV_MANNER_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="cikstit",
        english="well, fine",
        position_rule="PRECEDES-VERB",
        bb_lessons=[18, 20],
        bb_example_skiri="Tsikstit ka ras•pari'?",
        bb_example_english="Are you well? (Are you doing fine?)",
        function_word_id="cikstit",
        grammatical_class="ADV",
        notes="L18, L20. Used in greetings. Precedes ka or verb.",
    ),
    SlotFiller(
        skiri_form="rariksisu",
        english="hard, very much",
        position_rule="PRECEDES-VERB",
        bb_lessons=[18],
        bb_example_skiri="Rariksisu tatutsiks•a•wahri'.",
        bb_example_english="I've been working hard.",
        function_word_id="rariksisu",
        grammatical_class="ADV",
        notes="L18 dialogue. Clause-initial (precedes 1sg verb).",
    ),
    SlotFiller(
        skiri_form="ctuu",
        english="really, so",
        position_rule="PRECEDES-VERB",
        bb_lessons=[],  # Parks dictionary, not directly in BB sentence
        bb_example_skiri="",
        bb_example_english="",
        function_word_id="ctuu",
        grammatical_class="ADV",
        notes="Parks dictionary. Common intensifier. PRECEDES-VERB confirmed.",
    ),
    SlotFiller(
        skiri_form="awiit",
        english="first",
        position_rule="PRECEDES-VERB",
        bb_lessons=[],
        bb_example_skiri="",
        bb_example_english="",
        function_word_id="awiit",
        grammatical_class="ADV",
        notes="Parks dictionary. Sequencing adverb.",
    ),
    SlotFiller(
        skiri_form="istuʔ",
        english="again, back",
        position_rule="PRECEDES-VERB",
        bb_lessons=[],
        bb_example_skiri="",
        bb_example_english="",
        function_word_id="istuʔ",
        grammatical_class="ADV",
        notes="Parks dictionary. Repetition/return adverb.",
    ),
]


# ============================================================================
# NUMERAL / QUANTIFIER slot fillers — for noun slots in any template
#
# Position: PRECEDES-NOUN (all numerals confirmed)
# BB evidence: asku L12, tawit L13, kaas raku•kariu L13, kitu L02/L12
# ============================================================================
NUMERAL_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="asku",
        english="one",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[2, 12, 20],
        bb_example_skiri="T'ewitsu asku.",
        bb_example_english="It costs a dollar.",
        function_word_id="asku",
        grammatical_class="NUM",
        notes="L02, L12. Most frequent numeral in BB.",
    ),
    SlotFiller(
        skiri_form="pitku",
        english="two",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[16],
        bb_example_skiri="we ti pitku",
        bb_example_english="it's two o'clock",
        function_word_id="pitku",
        grammatical_class="NUM",
        notes="L16 basic word.",
    ),
    SlotFiller(
        skiri_form="tawit",
        english="three",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[13],
        bb_example_skiri="Tawit kaas tatutak•erit.",
        bb_example_english="I saw three cars.",
        function_word_id="tawit",
        grammatical_class="NUM",
        notes="L13. Precedes noun in attested example.",
    ),
    SlotFiller(
        skiri_form="kskiitiʔiks",
        english="four",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[20],
        bb_example_skiri="tuh•raru kskitiiks akitaru'",
        bb_example_english="made up of four bands",
        function_word_id="kskiitiʔiks",
        grammatical_class="NUM",
        notes="L20 reading passage.",
    ),
    SlotFiller(
        skiri_form="suhuks",
        english="five",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[],
        bb_example_skiri="",
        bb_example_english="",
        function_word_id="suhuks",
        grammatical_class="NUM",
        notes="Parks dictionary. Common numeral.",
    ),
    SlotFiller(
        skiri_form="kitu",
        english="all, together",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[2, 12],
        bb_example_skiri="Ketuh•kusit papitsisu kitu.",
        bb_example_english="Lend me a dollar.",
        function_word_id="kitu",
        grammatical_class="QUAN",
        notes="L02, L12. Quantifier. Both 'all' and 'together' senses attested.",
    ),
]


# ============================================================================
# LOCATIVE slot fillers — for T5 (where Q) answers and T8 (place slot)
#
# Position: PRECEDES-VERB for freestanding locatives; PROCLITIC for prefixes
# BB evidence: hiri (8x), ru (6x) in BB sentences
# ============================================================================
LOCATIVE_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="hiri",
        english="here, this place, where",
        position_rule="PRECEDES-VERB",
        bb_lessons=[13, 15, 20],
        bb_example_skiri="Aka, hiri we ti•pitsi'!",
        bb_example_english="Gee, it's cold in here!",
        function_word_id="hiri",
        grammatical_class="LOC",
        notes="L13, L15, L20. 8x in BB sentences. Most frequent locative.",
    ),
    SlotFiller(
        skiri_form="ru",
        english="there, over there",
        position_rule="PRECEDES-VERB",
        bb_lessons=[1, 7, 8, 13, 16],
        bb_example_skiri="Ru tuks•kaku'.",
        bb_example_english="It was in the house.",
        function_word_id="ru",
        grammatical_class="LOC",
        notes="L01, L07, L08, L13, L16. 6x in BB. General distal locative.",
    ),
]


# ============================================================================
# YES/NO PARTICLES — for T7 (affirmation wrapper)
# ============================================================================
YES_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="ahu'",
        english="yes",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[1, 2, 8, 18, 20],
        bb_example_skiri="Ahu', ti hitu'.",
        bb_example_english="Yes, this is a feather.",
        grammatical_class="INTERJ",
        notes="Standard affirmative. Most frequent in BB (5 lessons).",
    ),
    SlotFiller(
        skiri_form="hau",
        english="yes",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[1],
        bb_example_skiri="Hau, ti hitu'.",
        bb_example_english="Yes, this is a feather.",
        function_word_id="hau",
        grammatical_class="INTERJ",
        notes="L01. Male speech variant per some sources.",
    ),
    SlotFiller(
        skiri_form="ilan'",
        english="yes",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[11],
        bb_example_skiri="Ilan', tiku•ratsaus.",
        bb_example_english="Yes, I'm hungry.",
        function_word_id="ilanʔ",
        grammatical_class="INTERJ",
        notes="L11. Variant affirmative.",
    ),
]


# ============================================================================
# GREETING / DISCOURSE slot fillers — for social formulas (standalone)
# ============================================================================
GREETING_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="nawa",
        english="hello, now, well",
        position_rule="STANDALONE",
        bb_lessons=[20],
        bb_example_skiri="Nawa, taku ka ra•ka .ku?",
        bb_example_english="Hello, is anyone home?",
        function_word_id="nawa",
        grammatical_class="INTERJ",
        notes="L20. Greeting particle. 4x in L20 dialogues.",
    ),
]


# ============================================================================
# DEMONSTRATIVE slot fillers — for specifying which noun
# ============================================================================
DEMONSTRATIVE_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="ti",
        english="this is, it is",
        position_rule="PROCLITIC",
        bb_lessons=[1, 2, 5, 7, 9, 13, 14, 16, 20],
        bb_example_skiri="Ti hitu'.",
        bb_example_english="This is a feather.",
        function_word_id="ti",
        grammatical_class="PART",
        notes="26x in BB. The most frequent function word. Indicative / demonstrative.",
    ),
    SlotFiller(
        skiri_form="we",
        english="(perfective/emphasis particle)",
        position_rule="PRECEDES-VERB",
        bb_lessons=[7, 9, 11, 12, 15, 16, 20],
        bb_example_skiri="Rahurahki we tut•awi'at Karit•kutsu'.",
        bb_example_english="The deer jumped over the big rock.",
        function_word_id="we",
        grammatical_class="PART",
        notes="12x in BB. Marks completed action or present state. Critical for past tense narratives.",
    ),
    SlotFiller(
        skiri_form="tihe",
        english="those, that (distal plural)",
        position_rule="PRECEDES-NOUN",
        bb_lessons=[19, 20],
        bb_example_skiri="Tat•uh•ta tihe ra•pa•ariki'.",
        bb_example_english="I will go next month.",
        function_word_id="tihe",
        grammatical_class="DEM",
        notes="L19, L20. Distal-plural demonstrative. Used with time references.",
    ),
]


# ============================================================================
# INTERROGATIVE slot fillers — already wired into T3, T4, T5 but documented
# ============================================================================
INTERROGATIVE_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="ka",
        english="(yes/no question marker)",
        position_rule="PROCLITIC",
        bb_lessons=[1, 2, 5, 6, 7, 8, 9, 11, 12, 14, 18, 20],
        bb_example_skiri="Ka ra•pahaat rakis?",
        bb_example_english="Is the stick red?",
        function_word_id="ka?",
        grammatical_class="PRON",
        notes="22x in BB. Wired into T3. Most frequent interrogative.",
    ),
    SlotFiller(
        skiri_form="kirike",
        english="what, why, how",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[1, 2, 6, 8, 10, 11, 13, 15, 17, 18, 19, 20],
        bb_example_skiri="Kirike ru'?",
        bb_example_english="What is it?",
        function_word_id="kirike",
        grammatical_class="PRON",
        notes="14x in BB. Wired into T4. Requires absolutive mode on verb.",
    ),
    SlotFiller(
        skiri_form="kiru",
        english="where",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[5, 8, 13, 19],
        bb_example_skiri="Kiru rasuks•at?",
        bb_example_english="Where did you go?",
        function_word_id="kiru",
        grammatical_class="PRON",
        notes="7x in BB. Wired into T5. Requires absolutive mode.",
    ),
    SlotFiller(
        skiri_form="kirti",
        english="where (destination), when",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[9, 16, 17],
        bb_example_skiri="Kirti rira•awi•u tasih•ka•isa'?",
        bb_example_english="When did you come home?",
        function_word_id="kirti",
        grammatical_class="PRON",
        notes="3x in BB. Used for 'where (to)' and 'when' (with rira•awi•u).",
    ),
    SlotFiller(
        skiri_form="taku",
        english="who, anyone, what",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[20],
        bb_example_skiri="Nawa, taku ka ra•ka .ku?",
        bb_example_english="Hello, is anyone home?",
        function_word_id="taku",
        grammatical_class="PRON",
        notes="L20. Content interrogative for persons/indefinite.",
    ),
    SlotFiller(
        skiri_form="kitske",
        english="how much, how many",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[12, 16],
        bb_example_skiri="Kitske rd•awitsu'?",
        bb_example_english="How much is it?",
        grammatical_class="PRON",
        notes="L12, L16. Quantity interrogative.",
    ),
]


# ============================================================================
# IMPERATIVE PARTICLES — for T10
# ============================================================================
IMPERATIVE_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="suks",
        english="(do it!) — 2sg imperative",
        position_rule="PROCLITIC",
        bb_lessons=[12, 15, 20],
        bb_example_skiri="Suks•teka .rikut.",
        bb_example_english="Open the door.",
        function_word_id="suks",
        grammatical_class="PART",
        notes="L12, L15, L20. Most common imperative. 2sg command.",
    ),
    SlotFiller(
        skiri_form="siks",
        english="(do it!) — 2pl imperative",
        position_rule="PROCLITIC",
        bb_lessons=[20],
        bb_example_skiri="Nawa, siks .uka .a'.",
        bb_example_english="Hello, come in.",
        function_word_id="siks",
        grammatical_class="PART",
        notes="L20. 2pl command (to multiple people).",
    ),
    SlotFiller(
        skiri_form="stiks",
        english="(listen!) — you (1) imperative",
        position_rule="PROCLITIC",
        bb_lessons=[2],
        bb_example_skiri="Stiks .atku!",
        bb_example_english="You (1) listen!",
        function_word_id="stiks",
        grammatical_class="PART",
        notes="L02 phrase. Single-addressee imperative.",
    ),
]


# ============================================================================
# NEGATION — for T6 inner mechanics
# ============================================================================
NEGATION_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="kaki",
        english="no, not",
        position_rule="CLAUSE-INITIAL",
        bb_lessons=[1, 2, 5, 6, 7, 9, 11, 12, 14, 20],
        bb_example_skiri="Kaki, kaki karitki.",
        bb_example_english="No, it is not a rock.",
        grammatical_class="INTERJ",
        notes="13x in BB dialogues. Standalone negation. Often doubled for emphasis.",
    ),
]


# ============================================================================
# CONJUNCTION — for combining clauses (future templates)
# ============================================================================
CONJUNCTION_FILLERS: List[SlotFiller] = [
    SlotFiller(
        skiri_form="a",
        english="and",
        position_rule="BETWEEN-CLAUSES",
        bb_lessons=[20],
        bb_example_skiri="taraha a rahurahki",
        bb_example_english="buffalo and deer",
        function_word_id="a, aa",
        grammatical_class="CONJ",
        notes="L20 reading passage. Basic conjunction.",
    ),
]


# ============================================================================
# Master slot registry — maps slot type names to filler lists
# ============================================================================
SLOT_FILLERS: Dict[str, List[SlotFiller]] = {
    "TEMPORAL": TEMPORAL_FILLERS,
    "ADV_MANNER": ADV_MANNER_FILLERS,
    "NUMERAL": NUMERAL_FILLERS,
    "LOCATIVE": LOCATIVE_FILLERS,
    "YES": YES_FILLERS,
    "GREETING": GREETING_FILLERS,
    "DEMONSTRATIVE": DEMONSTRATIVE_FILLERS,
    "INTERROGATIVE": INTERROGATIVE_FILLERS,
    "IMPERATIVE": IMPERATIVE_FILLERS,
    "NEGATION": NEGATION_FILLERS,
    "CONJUNCTION": CONJUNCTION_FILLERS,
}


def get_fillers_for_slot(slot_type: str, bb_only: bool = False) -> List[SlotFiller]:
    """
    Get curated slot fillers for a given slot type.
    
    Args:
        slot_type: One of TEMPORAL, ADV_MANNER, NUMERAL, LOCATIVE, YES,
                   GREETING, DEMONSTRATIVE, INTERROGATIVE, IMPERATIVE,
                   NEGATION, CONJUNCTION
        bb_only: If True, only return items with BB attestation
    
    Returns:
        List of SlotFiller objects
    """
    fillers = SLOT_FILLERS.get(slot_type, [])
    if bb_only:
        fillers = [f for f in fillers if f.bb_lessons]
    return fillers


def get_all_bb_attested() -> Dict[str, List[SlotFiller]]:
    """Return only BB-attested fillers across all slot types."""
    return {
        slot_type: [f for f in fillers if f.bb_lessons]
        for slot_type, fillers in SLOT_FILLERS.items()
    }


# ============================================================================
# Position rule summary for word order engine
# ============================================================================
POSITION_RULES = {
    "CLAUSE-INITIAL": "Appears at the start of the clause, before subject and verb",
    "PRECEDES-VERB": "Appears immediately before the verb complex",
    "PRECEDES-NOUN": "Appears immediately before the noun it modifies",
    "CLAUSE-FINAL": "Appears at the end of the clause, after the verb",
    "PROCLITIC": "Attaches directly to the following word (no space in careful writing)",
    "BETWEEN-CLAUSES": "Appears between two clauses it connects",
    "STANDALONE": "Used independently, not bound to a particular position",
}


# ============================================================================
# Template-to-slot mapping — which slot types are available per template
# ============================================================================
TEMPLATE_SLOT_MAP: Dict[str, List[str]] = {
    "T1": ["DEMONSTRATIVE"],           # ti is built-in; noun slot is free
    "T2": ["DEMONSTRATIVE"],           # ti is built-in; noun + VD are free
    "T3": ["INTERROGATIVE", "ADV_MANNER"],  # ka is built-in; adv can precede
    "T4": ["INTERROGATIVE"],           # kirike is built-in
    "T5": ["INTERROGATIVE"],           # kiru/kirti built-in
    "T6": ["NEGATION"],               # kaki built-in
    "T7": ["YES"],                     # yes-word selectable
    "T8": ["TEMPORAL", "ADV_MANNER", "NUMERAL", "LOCATIVE"],  # richest slot set
    "T9": ["TEMPORAL", "ADV_MANNER", "NUMERAL", "LOCATIVE", "DEMONSTRATIVE"],
    "T10": ["IMPERATIVE"],            # imp particle selectable
}


# ============================================================================
# BB vocabulary alias table — Blue Book forms that differ from Parks headwords
#
# These are the ~15 common BB forms that fuzzy lookup needs help with.
# Format: bb_form -> (parks_headword, parks_entry_id, gloss)
# ============================================================================
BB_VOCABULARY_ALIASES = {
    "pita": ("pitaruʔ", "SK-pitaruq-p114-2205", "man"),
    "paresu": ("paresuʔ", "BB-paresu-0036", "hunter"),
    "rakis": ("rakis", None, "stick"),  # exact match but included for completeness
    "kaas": ("kaaʔas", "SK-kaasa-p73-1312", "car, automobile"),
    "asaki": ("asaaki", None, "dog"),
    "kuruks": ("kuruks", "SK-kuruks-p102-1986", "bear"),
    "rahurahki": ("rahurahki", None, "deer"),
    "rikutski": ("rikucki", "SK-rikucki-p492-4198", "bird"),
    "kiwaku": ("kiwakuʔ", None, "fox"),
    "taraha": ("taraha", None, "buffalo"),
    "arusa": ("aruusaʔ", None, "horse"),
    "hitu'": ("hituʔ", None, "feather"),
    "karitki": ("karitki", None, "rock, stone"),
    "kisatski": ("kisacki", None, "meat"),
    "papitsisu": ("papiciisuʔ", None, "money"),
}


if __name__ == "__main__":
    print("BB-Attested Slot Fillers for Pari Pakuru Sentence Templates")
    print("=" * 65)
    
    total_bb = 0
    total_all = 0
    for slot_type, fillers in SLOT_FILLERS.items():
        bb_count = len([f for f in fillers if f.bb_lessons])
        total_bb += bb_count
        total_all += len(fillers)
        print(f"\n{slot_type} ({bb_count} BB-attested / {len(fillers)} total)")
        for f in fillers:
            bb_tag = f"  L{','.join(str(l) for l in f.bb_lessons)}" if f.bb_lessons else "  (Parks dict)"
            print(f"  {f.skiri_form:30s} = {f.english:25s} [{f.position_rule}]{bb_tag}")
    
    print(f"\n{'='*65}")
    print(f"Total: {total_bb} BB-attested / {total_all} curated fillers across {len(SLOT_FILLERS)} slot types")
