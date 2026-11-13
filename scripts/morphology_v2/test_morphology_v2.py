#!/usr/bin/env python3
"""Unit tests for the v2 morphology pipeline.

    python -m unittest discover -s scripts/morphology_v2 -p "test_*.py"

Covered: tier assignment, duplicate resolution, etymology parsing and gloss
alignment, the seam engine, variant handling (nothing merges on vowel length)
and the coverage computation.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etymology import align_all, parse_etymology  # noqa: E402
from inventory import coverage_curve  # noqa: E402
from lexemes import _same_record, resolve_duplicates  # noqa: E402
from tiers import assign_tier, is_learner_facing  # noqa: E402
import seams  # noqa: E402


class TierRules(unittest.TestCase):
    def test_a_needs_exact_and_independent_confirmation(self):
        self.assertEqual(assign_tier("printed", "exact", "confirm", None, False)[0], "A")
        self.assertEqual(assign_tier("printed", "exact", None, "confirm", False)[0], "A")

    def test_exact_without_confirmation_is_b_only_with_recurrence(self):
        self.assertEqual(assign_tier("printed", "exact", None, None, True)[0], "B")
        self.assertEqual(assign_tier("printed", "exact", None, None, False)[0], "C")

    def test_partial_needs_independent_confirmation(self):
        self.assertEqual(assign_tier("printed", "partial", "confirm", None, False)[0], "B")
        self.assertEqual(assign_tier("printed", "partial", None, None, True)[0], "C")

    def test_failed_reproduction_is_c(self):
        self.assertEqual(assign_tier("printed", "fail", "confirm", None, True)[0], "C")

    def test_contradiction_caps_at_c(self):
        self.assertEqual(assign_tier("printed", "exact", "contradict", "confirm", True)[0], "C")
        self.assertEqual(assign_tier("printed", "exact", "confirm", "contradict", True)[0], "C")

    def test_no_claim(self):
        tier, why = assign_tier(None, None, None, None, False)
        self.assertIsNone(tier)
        self.assertTrue(why)

    def test_citation_follows_the_same_rules(self):
        self.assertEqual(assign_tier("citation", "exact", "confirm", None, False)[0], "A")
        self.assertEqual(assign_tier("citation", "exact", None, None, True)[0], "B")
        self.assertEqual(assign_tier("citation", "exact", None, None, False)[0], "C")

    def test_analysis_not_in_parks(self):
        self.assertEqual(assign_tier("proposed", "exact", "confirm", "confirm", True)[0], "B")
        self.assertEqual(assign_tier("proposed", "exact", "confirm", None, True)[0], "C")
        self.assertEqual(assign_tier("proposed", "exact", None, None, True)[0], "C")
        self.assertEqual(assign_tier("proposed", "exact", None, None, False)[0], "D")
        self.assertEqual(assign_tier("proposed", "exact", "contradict", None, True)[0], "D")

    def test_only_a_and_b_reach_learners(self):
        self.assertTrue(is_learner_facing("A"))
        self.assertTrue(is_learner_facing("B"))
        for t in ("C", "D", None):
            self.assertFalse(is_learner_facing(t))


def _row(eid, **kw):
    base = {"entry_id": eid, "headword": "x", "alternates": ["x"], "class": "VI", "verb_class": "(1)",
            "preverbs": [], "forms": {}, "glosses": [{"definition": "go inside"}], "raw_etymology": "<kaa+at, go inside>",
            "constituent_elements": None, "page_verified": True, "phonetic_form": None,
            "simplified_pronunciation": None, "normalized_form": None, "stem_preverb": None, "tags": [],
            "cognates": [], "additional_forms": [], "bb_attested": False}
    base.update(kw)
    return base


class DuplicateResolution(unittest.TestCase):
    def test_identical_records_merge(self):
        a = _row("A", forms={"1": "tatkaaʔat", "2": "tikaaʔat"})
        b = _row("B", forms={"1": "tatkaaʔat", "2": "tikaaʔat"})
        self.assertTrue(_same_record(a, b)[0])
        lex, dec = resolve_duplicates([a, b])
        self.assertEqual(len(lex), 1)
        self.assertEqual(lex[0]["member_ids"], ["A", "B"])
        self.assertEqual(dec[0]["verdict"], "merged")

    def test_same_spelling_different_verb_class_stays_apart(self):
        a = _row("A", verb_class="(1)", glosses=[{"definition": "say"}])
        b = _row("B", verb_class="(3)", glosses=[{"definition": "speak, as a language"}])
        self.assertFalse(_same_record(a, b)[0])
        self.assertEqual(len(resolve_duplicates([a, b])[0]), 2)

    def test_same_paradigm_different_meaning_stays_apart(self):
        a = _row("A", forms={"2": "tikicaa"}, glosses=[{"definition": "become watery"}])
        b = _row("B", forms={"2": "tikicaa"}, glosses=[{"definition": "act silly; clown"}])
        self.assertFalse(_same_record(a, b)[0])

    def test_different_preverb_stays_apart(self):
        a = _row("A", preverbs=["ut"])
        b = _row("B", preverbs=[])
        self.assertFalse(_same_record(a, b)[0])

    def test_different_etymology_stays_apart(self):
        a = _row("A", **{"class": "N", "verb_class": None, "raw_etymology": "<kiic+uʔ, neck + NOM>",
                         "glosses": [{"definition": "neck"}]})
        b = _row("B", **{"class": "N", "verb_class": None, "raw_etymology": "<kic+uʔ, water + NOM>",
                         "glosses": [{"definition": "water; liquid"}]})
        self.assertFalse(_same_record(a, b)[0])


class EtymologyParsing(unittest.TestCase):
    def parse(self, raws):
        parsed = [parse_etymology(r, ()) for r in raws]
        align_all(parsed)
        return parsed

    def test_pieces_and_literal(self):
        p = parse_etymology("<kaa+at, go inside>")
        self.assertEqual([x["form"] for x in p["pieces"]], ["kaa", "at"])
        self.assertEqual(p["literal"], "go inside")
        self.assertEqual(p["kind"], "analysis")

    def test_dotted_stem_and_preverb_note(self):
        p = parse_etymology("<as (ut...)+ri.wiitik, take hold of someone in dismay>")
        self.assertEqual([x["form"] for x in p["pieces"]], ["as", "ri", "wiitik"])
        self.assertEqual(p["preverbs"], ["ut"])
        self.assertTrue(p["pieces"][1]["dotted"] and p["pieces"][2]["dotted"])
        self.assertFalse(p["pieces"][0]["dotted"])

    def test_optional_segment_and_bound_hyphen(self):
        p = parse_etymology("<kaas-+(h)aahka.wi+uʔ, leg bank + NOM>")
        self.assertEqual(p["pieces"][1]["form"], "haahka")
        self.assertEqual(p["pieces"][1]["form_min"], "aahka")
        self.assertTrue(p["pieces"][0]["bound"])

    def test_line_break_hyphen_is_joined(self):
        p = parse_etymology("pii- ra+icaraks, crazy child")
        self.assertEqual([x["form"] for x in p["pieces"]], ["piira", "icaraks"])

    def test_cognate_note_is_not_an_analysis(self):
        self.assertEqual(parse_etymology("<i.q. SB kee, Ar. čee>")["kind"], "cognate_only")
        self.assertEqual(parse_etymology("<Engl. biscuit>")["kind"], "loan")
        self.assertEqual(parse_etymology(None)["kind"], "none")

    def test_label_is_anchored_by_statistics_not_position(self):
        raws = ["<%s+waa, thing + DIST>" % x for x in ("kus", "sa", "kaa", "at")] + ["<waa+waapic, flash + DIST>"]
        parsed = self.parse(raws)
        last = parsed[-1]["pieces"]
        self.assertEqual((last[0]["form"], last[0]["gloss"], last[0]["gloss_kind"]), ("waa", "DIST", "label"))
        self.assertEqual((last[1]["form"], last[1]["gloss"], last[1]["gloss_kind"]), ("waapic", "flash", "aligned"))

    def test_shared_phrase_is_not_split_between_pieces(self):
        raws = ["<%s+uʔ, thing + NOM>" % x for x in ("iks", "paks", "kiis", "icka")] + ["<as+hur+uʔ, foot place + NOM>"]
        parsed = self.parse(raws)
        pcs = parsed[-1]["pieces"]
        self.assertEqual(pcs[2]["gloss"], "NOM")
        self.assertEqual(pcs[0]["gloss_kind"], "phrase")
        self.assertIsNone(pcs[0]["gloss"])
        self.assertEqual(pcs[0]["phrase"], "foot place")

    def test_piece_glossed_by_its_own_form_has_no_meaning(self):
        raws = ["<%s+uʔ, thing + NOM>" % x for x in ("iks", "paks", "kiis", "icka")] + ["<kic+tuuks+uʔ, water + tuuks + NOM>"]
        pcs = self.parse(raws)[-1]["pieces"]
        self.assertEqual(pcs[1]["gloss_kind"], "self")
        self.assertEqual(pcs[0]["gloss_kind"], "aligned")


class SeamEngine(unittest.TestCase):
    def has(self, pieces, word_like, surface, *rules):
        d = seams.derive(pieces, word_like)
        self.assertIn(surface, d, "%s not in %s" % (surface, sorted(d)[:8]))
        for r in rules:
            self.assertIn(r, d[surface])

    def test_plain_concatenation(self):
        self.assertEqual(seams.derive(["tuks", "at"], False)["tuksat"], [])

    def test_glottal_stop_between_vowels(self):
        self.has(["kaa", "at"], False, "kaaʔat", "V+V ʔ")

    def test_r_becomes_h_before_consonant(self):
        self.has(["sakuur", "kiwatak"], False, "sakuhkiwatak", "r>h/_C", "V:>V/_hC")
        self.has(["aar", "wiriik"], False, "aahwiriik", "r>h/_C")

    def test_w_becomes_p_and_k_drops(self):
        self.has(["haak", "wuh"], False, "haapuh", "w>p/C_", "k>0/_p")
        self.has(["as", "wiitik"], False, "aspiitik", "w>p/C_")

    def test_r_becomes_t_after_obstruent(self):
        self.has(["aciks", "raʔaar"], False, "acikstaʔaar", "R21")

    def test_h_lost_after_consonant(self):
        self.has(["aciks", "hiir"], False, "aciksiir", "R16")

    def test_word_edge_rules_apply_only_to_words(self):
        self.has(["asaa", "kis"], True, "asaaki", "R9")
        self.assertNotIn("asaaki", seams.derive(["asaa", "kis"], False))
        self.has(["aar", "kucuu"], True, "aahkucuuʔ", "V>Vʔ/_#")
        self.assertNotIn("aahkucuuʔ", seams.derive(["aar", "kucuu"], False))

    def test_no_rule_changes_a_cluster_inside_a_piece(self):
        # iks- must not become ikc-: Parks 17 applies at boundaries only
        self.assertIn("iksuʔ", seams.derive(["iks", "uʔ"], True))
        self.assertNotIn("ikcuʔ", seams.derive(["iks", "uʔ"], True))

    def test_vowel_length_is_never_free(self):
        # paks cannot give paaks: there is no rule that lengthens a vowel
        self.assertNotIn("haspaaksuʔ", seams.derive(["has", "paks", "uʔ"], True))

    def test_every_rule_has_a_name_and_a_source(self):
        for rid, info in seams.RULES.items():
            self.assertTrue(info["name"] and info["source"], rid)
            self.assertIn("optional", info)


class Coverage(unittest.TestCase):
    def test_a_word_counts_only_when_every_piece_is_taught(self):
        need = {"w1": {"a", "b"}, "w2": {"a"}, "w3": {"b", "c"}}
        res = {"records": [1, 2, 3, 4]}                       # four words in the dictionary
        inv = {"bb_first": {"w2": 1}, "total_examples": 10, "n_examples": {"w1": 2, "w2": 3}}
        curve = coverage_curve(["a", "b", "c"], need, res, inv)
        self.assertEqual([c["words_decodable"] for c in curve], [1, 2, 3])
        self.assertEqual([c["words_with_a_known_piece"] for c in curve], [2, 3, 3])
        self.assertEqual(curve[0]["share_of_dictionary"], 0.25)
        self.assertEqual(curve[0]["blue_book_words_decodable"], 1)
        self.assertEqual(curve[1]["share_of_example_sentences"], 0.5)

    def test_order_matters(self):
        need = {"w1": {"a", "b"}}
        res, inv = {"records": [1]}, {"bb_first": {}, "total_examples": 0, "n_examples": {}}
        self.assertEqual([c["words_decodable"] for c in coverage_curve(["a", "b"], need, res, inv)], [0, 1])


if __name__ == "__main__":
    unittest.main()
