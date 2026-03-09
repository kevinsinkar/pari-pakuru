#!/usr/bin/env python3
"""Merge recovered grammar pages into grammatical_overview.json."""

import json
import sys
from pathlib import Path

OUTPUT = Path("extracted_data/grammatical_overview.json")

with open(OUTPUT, "r", encoding="utf-8") as f:
    grammar = json.load(f)

# Page 1 (p.29): Introduction + Nouns
page_1 = {
    "page_number": 29,
    "sections": [
        {
            "heading": "Grammatical Overview",
            "content": (
                "Skiri is polysynthetic in its structure in that words -- primarily verbs -- "
                "are composed of an unusually large number of meaningful elements (morphemes) "
                "that generally in other, non-polysynthetic languages are separate, or independent, "
                "words. Most of the categories marked on the Skiri verb are grammatical in nature "
                "and include mode, aspect, person, tense, possession, benefaction, and other such "
                "categories. Also generally incorporated into the verb is the noun patient of a "
                "transitive verb or the noun agent of an intransitive one. Thus in Skiri the verb "
                "is the most elaborate, as well as prevalent, word class, and verbs translate into "
                "English as either a clause or a sentence. Nouns constitute the only other word "
                "class that allows inflection, but in a very limited manner.\n\n"
                "Generally a freely occurring verb has at least five morphemes comprising it, but "
                "often as many as ten or more morphemes. Those morphemes are tightly bound together "
                "by a complex set of phonological rules (presented in chapter 3) that change their "
                "forms and thereby 'disguise' their underlying forms or identities. Languages of "
                "this type, in which morphemes fuse or change their forms to one extent or another "
                "when coming together in word building, are often designated as fusional."
            ),
            "morphemes_mentioned": [],
            "tables": [],
        },
        {
            "heading": "Nouns",
            "content": (
                "In Skiri there are two types of noun stems, independent and dependent. The "
                "independent stem is a noun that stands freely, with or without the nominal "
                "absolutive suffix -u\u0294 (see below). A dependent stem, in contrast, is one "
                "that cannot by itself stand independently as a word. To become a free form it "
                "must have a suffix, although generally it occurs only in compounds.\n\n"
                "Examples of dependent nouns (cited as N-DEP herein) are:\n"
                "siis- 'sharp, pointed object': siiski 'awl' (< siis- + -kis DIM); "
                "siistacara\u0294 'fork' (< siis- + -taar PL + taraa 'be side by side')\n"
                "asaa- 'horse; dog': asaaki 'dog' (< asaa- + -kis DIM); asiicapaat 'mare' "
                "(< asaa- + icapaak 'woman; female'). The independent form of 'horse' is "
                "aruusa\u0294."
            ),
            "morphemes_mentioned": [
                {"form": "-u\u0294", "label": "nominal absolutive suffix", "meaning": "forms independent nouns", "notes": "NOM"},
                {"form": "-kis", "label": "diminutive", "meaning": "small N", "notes": "DIM"},
                {"form": "-taar", "label": "plural", "meaning": "plural marker for nouns", "notes": "PL"},
            ],
            "tables": [],
        },
    ],
    "_source": "gemini_plaintext_400dpi_retry",
}

# Page 3 (p.31): Table 5 + Verbs intro
page_3 = {
    "page_number": 31,
    "sections": [
        {
            "heading": "Noun Derivation",
            "content": (
                "There are five derivational affixes in Skiri, two of which do not add new "
                "semantic content to noun stems, but serve only to form independent nouns. The "
                "other three, one a suffix and two prefixes, do add content. These affixes are "
                "given in table 5."
            ),
            "morphemes_mentioned": [
                {"form": "-u\u0294", "label": "Nominal Absolutive (NOM)", "meaning": "forms independent nouns",
                 "notes": "iksu\u0294 'hand' < iks- 'hand' + -u\u0294"},
                {"form": "-kis", "label": "Diminutive (DIM)", "meaning": "small N; no translation",
                 "notes": "asaaki\u0294 'dog' < asaa- 'dog; horse' + -kis DIM; riiciki\u0294 'knife' < riici- 'knife' + kis DIM"},
                {"form": "-kusu\u0294", "label": "Augmentative (AUG)", "meaning": "large, big",
                 "notes": "wiitakusu\u0294 'large man' < wiita 'man' + kusu\u0294 'big'"},
                {"form": "-kuuku\u0294u\u0294", "label": "covering", "meaning": "covering",
                 "notes": "pakskuuku\u0294u\u0294 'hat; headwear' < paks- 'head' + -kuuku- 'covering' + -u\u0294 NOM"},
                {"form": "c-", "label": "Feminine (FEM)", "meaning": "female",
                 "notes": "ckuraa\u0294u\u0294 < c- FEM + kuraa- 'doctor' + -u\u0294 NOM"},
            ],
            "tables": [
                {
                    "caption": "Table 5. Nominal Derivational Affixes",
                    "headers": ["Category", "Skiri", "Translation", "Example"],
                    "rows": [
                        ["Nominal Absolutive (NOM)", "-u\u0294", "(no translation)", "iksu\u0294 'hand' < iks- + -u\u0294"],
                        ["Diminutive (DIM)", "-kis", "small N; no trans.", "asaaki\u0294 'dog'; riiciki\u0294 'knife'"],
                        ["Augmentative (AUG)", "-kusu\u0294", "large, big", "wiitakusu\u0294 'large man'"],
                        ["Covering", "-kuuku\u0294u\u0294", "covering", "pakskuuku\u0294u\u0294 'hat; headwear'"],
                        ["Feminine (FEM)", "c-", "female", "ckuraa\u0294u\u0294 'female doctor'"],
                    ],
                },
            ],
        },
        {
            "heading": "Verbs",
            "content": (
                "The basic component of active verb stems is the root, usually a monosyllabic "
                "but sometimes a di- or tri-syllabic morpheme. In Skiri there are approximately "
                "one hundred such roots, and consequently the vast majority of active verb stems "
                "are derived forms. Stems are formed by the addition of verbal prefixes; by "
                "compounding locative, descriptive, or noun stems, and combinations of those "
                "elements to verb roots; and by combining preverbs with roots and stems. The root "
                "hak 'to pass, go by', for example, has hundreds of different stems based on it, "
                "and the root at 'to go' has even more.\n\n"
                "Many active and passive verb stems in Skiri are discontinuous stems, in which "
                "the stem base is preceded by a preverb, a monosyllabic morpheme that occurs "
                "among the inner prefixes preceding the stem base but is usually not contiguous "
                "with it. There are three preverbs in Skiri: ir-/a-, uur- and ut-. Each of them "
                "is identical in form to grammatical prefixes that have other functions (see below), "
                "but when they occur as parts of stems they do not have any tangible meaning.\n\n"
                "Example: wiitatiiksa\u0294 'I have come' < wii- 'now' + ta- IND.1/2.A + t- 1.A "
                "+ ir- PREV + uks- AOR + a 'come' + -\u00d8 PERF"
            ),
            "morphemes_mentioned": [
                {"form": "ir-/a-", "label": "preverb", "meaning": "part of discontinuous verb stems",
                 "notes": "ir- alternates with a- for 3rd person agent"},
                {"form": "uur-", "label": "preverb", "meaning": "part of discontinuous verb stems", "notes": None},
                {"form": "ut-", "label": "preverb", "meaning": "part of discontinuous verb stems", "notes": None},
                {"form": "wii-", "label": "now", "meaning": "temporal proclitic", "notes": None},
                {"form": "ta-", "label": "IND.1/2.A", "meaning": "indicative mode for 1st/2nd person agent", "notes": "Modal prefix"},
                {"form": "t-", "label": "1.A", "meaning": "first person agent", "notes": None},
                {"form": "uks-", "label": "AOR", "meaning": "aorist", "notes": None},
            ],
            "tables": [],
        },
    ],
    "_source": "gemini_plaintext_400dpi_retry_split",
}

# Page 7 (p.35): from earlier successful retry
with open("extracted_data/grammar_retry_results.json", "r", encoding="utf-8") as f:
    retry_data = json.load(f)
page_7 = retry_data["page_7"]["gemini"]["data"]
page_7["_source"] = "gemini_plaintext_retry"

# Page 16 (p.44): Verb Stem Template + Suffixes
page_16 = {
    "page_number": 44,
    "sections": [
        {
            "heading": None,
            "content": (
                "iriiruurakuuraaru 'whatever the kind of animal was,' that is, 'all kinds of "
                "animals' < irii- 'the one' + ruu- 'there' + ra- INF.A + \u00d8- 3.A + ku- INF.B "
                "+ i- SEQ + raburaar- 'animal' + -u SUB.D"
            ),
            "morphemes_mentioned": [
                {"form": "irii-", "label": "the one", "meaning": "determiner prefix", "notes": None},
                {"form": "ruu-", "label": "there", "meaning": "locative", "notes": None},
                {"form": "ra-", "label": "INF.A", "meaning": "infinitive agent", "notes": None},
                {"form": "ku-", "label": "INF.B", "meaning": "infinitive benefactive", "notes": None},
                {"form": "i-", "label": "SEQ", "meaning": "sequential", "notes": None},
                {"form": "-u", "label": "SUB.D", "meaning": "subordinate descriptive", "notes": None},
            ],
            "tables": [],
        },
        {
            "heading": "Verb Stems",
            "content": "",
            "morphemes_mentioned": [],
            "tables": [
                {
                    "caption": "Table 15. The Verb Stem Template",
                    "headers": ["Slot", "Category", "Forms"],
                    "rows": [
                        ["1", "Iterative", "raar-, ka- ITER"],
                        ["2", "Noun", "awi- 'image', wak- 'sound'"],
                        ["3", "Descriptive Stem", "kasis 'hard', tarahkis 'strong'"],
                        ["4", "Portative/Comitative", "ri-, ra-, ruu- PORT; cir-, ciras- COM"],
                        ["5", "Locative", "ka- 'on', kaa- 'inside'"],
                        ["6", "Active Verb Complement", "kiikak 'drink' + -his PERF"],
                        ["7", "Verb Root", "at 'go'"],
                        ["8", "Causative", "-rik-, -ra\u0294uk"],
                    ],
                },
            ],
        },
        {
            "heading": "Suffixes",
            "content": (
                "Only two categories are marked by suffixes: aspect and subordination. Active and "
                "stative verbs occur in one of two basic aspects, perfective and imperfective. "
                "There are five other aspects that are built on one or both of these basic aspects: "
                "an intentive, which indicates that something is going to happen; a habitual, which "
                "indicates that something regularly happens; and an inchoative, which indicates that "
                "something is beginning to happen. All verbs occur in both independent and subordinate "
                "forms. Independent forms do not take a suffix, whereas subordinate forms do take one.\n\n"
                "Each of the major classes of verbs is, in part, defined by its distinctive subordinate "
                "suffix, which defines its class. Descriptive stems, for example, take the subordinate "
                "suffix -u, while locative verbs take the suffix -wi. Active and stative verbs, in "
                "contrast, belong to one of four subclasses, of which two are marked by different vowel "
                "suffixes, one by a final-syllable stress change, and one by the lack of a suffix."
            ),
            "morphemes_mentioned": [
                {"form": "-u", "label": "subordinate suffix (descriptive)", "meaning": "marks subordinate form of descriptive verbs", "notes": "SUB.D"},
                {"form": "-wi", "label": "subordinate suffix (locative)", "meaning": "marks subordinate form of locative verbs", "notes": "SUB.LOC"},
            ],
            "tables": [
                {
                    "caption": "Table 16. Verb Suffix Template",
                    "headers": ["Slot 25", "Slot 26", "Slot 27", "Slot 28"],
                    "rows": [
                        ["VERB STEM", "PERFECTIVE / PERFECTIVE SUBORDINATE / IMPERFECTIVE / IMPERFECTIVE SUBORDINATE", "INTENTIVE / HABITUAL / INCHOATIVE", "INTENTIVE SUBORDINATE"],
                    ],
                },
            ],
        },
    ],
    "_source": "gemini_plaintext_400dpi_retry",
}

# Merge
grammar["page_1"] = page_1
grammar["page_3"] = page_3
grammar["page_7"] = page_7
grammar["page_16"] = page_16

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(grammar, f, ensure_ascii=False, indent=2)

# Stats
total = len([k for k in grammar if k.startswith("page_")])
failed = len([k for k in grammar if k.startswith("page_") and isinstance(grammar[k], dict) and "_error" in grammar[k]])
retried = len([k for k in grammar if k.startswith("page_") and isinstance(grammar[k], dict) and "_source" in grammar[k]])

total_morphemes = 0
total_tables = 0
for k, v in grammar.items():
    if not k.startswith("page_"):
        continue
    for sec in v.get("sections", []):
        total_morphemes += len(sec.get("morphemes_mentioned", []))
        total_tables += len(sec.get("tables", []))

msg = (
    f"Updated grammar overview: {total} pages total, {failed} still failed, {retried} from retry\n"
    f"Total morphemes: {total_morphemes}, Total tables: {total_tables}\n"
)
sys.stdout.buffer.write(msg.encode("utf-8"))
