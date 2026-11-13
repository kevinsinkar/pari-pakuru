"""Construction guide sections and manual review-log sections."""
from collections import Counter, defaultdict

IND, NEG, CONT, ABS, GER, POT, SUBJ, INF, CONTSUB = (
    "indicative_perfective", "negative_indicative_perfective", "contingent_perfective", "absolutive_perfective",
    "gerundial_perfective_subordinate", "potential_perfective", "subjunctive_perfective_subordinate",
    "infinitive_perfective_subordinate", "contingent_perfective_subordinate")

AT, KAAQAT, KUS, SA, ARIK, WIITIK, KIKAK, RAQUK, KIIKAA, RAAH, AAR_BECOME, AAR_DO, IIRIK, PAHAAT, KAA, IKSKAA, KUUT, ACIKSTAQUK, WARII = (
    "SK-at-p18-0220", "SK-kaaqat-p2-0010", "SK-kus-p102-1993", "SK-sa-p150-2933", "SK-arik-p13-0145", "SK-wiitik-p179-3555",
    "SK-kikak-p93-1767", "SK-raquk-p114-2221", "SK-kiikaa-p90-1694", "SK-raah-p116-2264", "SK-aar-p351-3596", "SK-aar-p351-3598",
    "SK-iirik-p408-3912", "SK-pahaat-p107-2050", "SK-kaa-p418-3942", "SK-ikskaa-p63-1087", "SK-kuut-p452-4017", "SK-acikstaquk-p7-0049",
    "SK-warii-p177-3506")


def _md(headers, rows):
    from build_root_curriculum import md_table
    return md_table(headers, rows)


def _rule_examples(d):
    """Best attested before/after example per rule, from the segmentation log."""
    by = defaultdict(list)
    for eid, rec in d.seg.items():
        if rec["method"] in ("engine", "glottal_epenthesis", "glottal_epenthesis+engine", "located") and rec["confidence"] != "low":
            for rid in set(rec["rules"]):
                by[rid].append(rec)
    outp = {}
    for rid, lst in by.items():
        lst.sort(key=lambda r: (r["confidence"] != "high", len(r["hw_key"])))
        outp[rid] = (len(lst), lst[:3])
    return outp


RULE_NAMES = {
    "21": "r → t after an obstruent (Parks Rule 21; BB L2 p.35, L3 p.41 rule 1)",
    "23": "word-final r lost (Rule 23)",
    "16": "h lost after a consonant or before a cluster (Rule 16)",
    "20": "rr, kk → r, k (Rule 20, degemination)",
    "9R": "word-final s lost (Rule 9R)",
    "13": "t + r → hr (Rule 13)", "14": "r + h → hr (Rule 14)", "15": "hr → h (Rule 15)",
    "17": "s → c after a consonant (Rule 17)", "19": "t + t → ct (Rule 19)", "5": "identical vowels contract to one long vowel (Rule 5)",
    "6": "any vowel + u → uu (Rule 6, u-domination)", "7": "i + a → ii (Rule 7; BB L3 p.42 writes the result as e)",
    "3R": "Vk + -his → -ks (Rule 3R)", "8R": "raar- + t → raac- (Rule 8R)", "1R": "i + u → ii in prefix sequences (Rule 1R)",
    "ʔ-epenthesis (V+V)": "ʔ inserted between two vowels at a stem seam (not a numbered Parks rule; stem_extractor.py convention) ⚠",
    "w>p": "w → p after an obstruent (BB L3 p.41 rule 2; Parks has no numbered rule — attested in stem_extractor ut+w junctions) ⚠",
    "k>t": "stem-final k → t word-finally (Parks GO p.46 kikak → tikikat; BB L15 p.97; not in the 24-rule engine) ⚠",
    "V-length": "vowel-length alternation between the same root in different words (no rule in either source) ⚠",
    "r>h": "r → h before a high vowel (morpheme_inventory.py; Parks Rule 12R covers prefixes only) ⚠",
    "24": "c written ts in BB (Rule 24, variants of c)",
}


def sec_orthography(d):
    return "\n".join([
        "Parks's dictionary and the Blue Book spell the same sounds differently. All forms in this guide and in the lessons keep the "
        "spelling of the source they are quoted from.", "",
        _md(["Sound", "Parks dictionary", "Blue Book", "Example (same word)"], [
            ["glottal stop", "ʔ", "' (often dropped)", f"Parks *{d.W('SK-hiituq-p390-3856')}* — BB *hitu'* (L1 p.29)"],
            ["affricate", "c", "ts", f"Parks *{d.W('SK-cuuraki-p32-0536')}* — BB *tsuraki* (L6 p.56)"],
            ["long vowel", "aa ii uu", "usually single letter; BB p.35 asks learners to underline long syllables", f"Parks *{d.W('SK-piita-p113-2176')}* — BB *pita* (L4 p.44)"],
            ["i + a contraction", "ii (Rule 7)", "e", f"Parks *{d.F(ARIK, 2)}* — BB *t'erit* (L8 p.66) ⚠"],
            ["morpheme seam", "not marked (etymology uses +)", "• between pieces", "BB *tat•kikat* = Parks *" + d.F(KIKAK, 1) + "*"],
            ["dialect", "Skiri (SK) only", "Skiri (SK) and South Band (SB) marked", "BB L1 p.29 *had'* (SK) / *ahu'* (SB) 'yes'"],
        ]), "",
        f"BB's own statement of long vowels: {d.bbq(35, 'rakis + rahkata')} shows a seam written with •; "
        "Parks writes the result as one word."])


def sec_stem(d):
    return "\n".join([
        "**Nouns.** Parks GO p.29: an independent stem stands freely 'with or without the nominal absolutive suffix -uʔ'; a dependent stem "
        f"(N-DEP) needs a suffix or a compound — *asaa-* 'horse; dog' → *{d.W('SK-asaaki-p362-3736')}* 'dog'. Five derivational affixes only (Table 5, GO p.31): "
        f"NOM *-uʔ* (*{d.W('SK-iksuq-p64-1111')}*), DIM *-kis* (*{d.W('SK-asaaki-p362-3736')}*), AUG *-kusuʔ* (Parks's *wiitakusuʔ* 'large man'; no dictionary etymology carries the label ⚠), "
        f"'covering' *-kuukuʔuʔ* (*{d.W('SK-pakskuukuquq-p109-2106')}* 'hat'), FEM *c-* (Parks's *ckuraaʔuʔ* 'female doctor').", "",
        "**Verb roots and stems.** Parks GO p.31: 'the basic component of active verb stems is the root ... approximately one hundred such roots', so most stems are "
        f"derived. The two most productive are *hak* 'pass' and *at* 'go'. In the extraction, *at* builds {d.roots['at']['frequency']} dictionary words and *hak* "
        f"{d.roots['hak']['frequency']} (see `roots_ranked.json`). Three preverbs — *ir-/a-*, *uur-*, *ut-* — form discontinuous stems and 'do not have any tangible meaning' "
        f"when part of a stem (GO p.31): *{d.W(AAR_BECOME)}* 'become' 3sg *{d.F(AAR_BECOME, 2)}* vs *{d.W(AAR_DO)}* (ut...) 'do' 3sg *{d.F(AAR_DO, 2)}*.", "",
        "**The stem template** (Parks Table 15, GO p.44), illustrated with dictionary words:", "",
        _md(["Slot", "Element", "Attested word", "Analysis (Parks)", "Source"], [
            ["1 Iterative", "raar-, ka-", f"*{d.W('SK-raarapitaarahak-p122-2379')}* 'wind, as a clock'; *{d.W('SK-kacak-p75-1352')}* 'prick, stab'", "raar + apitaarahak; ka + cak", f"Parks p.{d.P('SK-raarapitaarahak-p122-2379')}, p.{d.P('SK-kacak-p75-1352')}"],
            ["2 Noun", "awi- 'image', wak- 'sound'", f"*{d.W('SK-awiqat-p21-0283')}* 'jump'", "awi + at", f"Parks p.{d.P('SK-awiqat-p21-0283')}"],
            ["3 Descriptive stem", "kasis 'hard'", f"*{d.W('SK-asaakasis-p362-3735')}* 'pony'", "asaa + kasis", f"Parks p.{d.P('SK-asaakasis-p362-3735')}"],
            ["4 Portative / comitative", "ri-, ra-, ruu- PORT; cir-, ciras- COM", f"*{d.W('SK-cirasat-p29-0451')}* 'take, lead'", "ciras + at", f"Parks p.{d.P('SK-cirasat-p29-0451')}"],
            ["5 Locative", "ka- 'on', kaa- 'inside'", f"*{d.W(KAAQAT)}* 'go inside'", "kaa + at", f"Parks p.{d.P(KAAQAT)}"],
            ["7 Verb root", "at 'go'", f"*{d.W(AT)}*", "at", f"Parks p.{d.P(AT)}"],
            ["8 Causative", "-rik-, -raʔuk", f"*{d.W('SK-katiihaquk-p82-1530')}* 'blacken'", "katiit + raʔuk", f"Parks p.{d.P('SK-katiihaquk-p82-1530')}"],
        ])])


def sec_template(d):
    ex = {w: (pg, gl, an) for pg, w, gl, an in d.grammar_examples()}

    def go(word):
        if word in ex:
            pg, gl, an = ex[word]
            return f"*{word}* '{gl}' < {an} (GO p.{pg})"
        d.missing.append(f"GO example: {word}")
        return f"*{word}* (GO)"
    rows = [
        ["Proclitic 1–8", "wi- QUOT, kuur- DUB, tiir- INFR, ar- EV, si- DU, ku- INDF, witi- REFL, kara-/ka- NEG", go("witiʔitat") + "; " + f"App.1 *{d.A('to go', IND, '1du_excl')}* (si- DU); dictionary *{d.F(ACIKSTAQUK, 2)}* (witi- REFL)", "GO p.40 Table 12–13"],
        ["10 Mode", "ta-/ti- IND, kaakaa-/kaaki- NEG.IND, rii- ASSR, i-/ri- CONT, kuus-/kaas- POT, ra- ABS, aa-/ii- SUBJ, ra...ku INF", f"App.1 'to go' 3sg: {', '.join(f'*{d.A(chr(116)+chr(111)+chr(32)+chr(103)+chr(111), m, chr(51)+chr(115)+chr(103))}*' for m in [IND, NEG, CONT, ABS, POT])}", "GO p.34 Table 8"],
        ["11 Agent", "t- 1.A, s- 2.A, Ø 3.A; ir- OBV", f"*{d.A('to go', IND, '1sg')}* / *{d.A('to go', IND, '2sg')}* / *{d.A('to go', IND, '3sg')}*", "GO p.35 Table 9"],
        ["12 Inclusive", "acir- 1.DU.IN, a- 1.PL.IN", f"*{d.A('to go', IND, '1du_incl')}* / *{d.A('to go', IND, '1pl_incl')}*", "GO p.35"],
        ["13 Agent PL / A.POSS / preverb", "rak- PL; ir- A.POSS; preverb", f"*{d.A('to drink it', IND, '1pl_excl')}*; " + go("kutakawirahuʔ"), "GO p.35–36"],
        ["15 Patient", "ku- 1.P, a- 2.P, Ø 3.P, ak- 3.PL.AN.P", f"*{d.F(KUUT, 1)}* 'I died' (*ku-*); App.1 *{d.A('to be sick', IND, '2sg')}* (*a-*)", "GO p.35 Table 9"],
        ["16 Infinitive ku-", "ra- ... ku-", f"App.1 *{d.A('to go', INF, '3sg')}*", "GO p.34"],
        ["17 Physical possession", "ri-", go("taruuraariit"), "GO p.36"],
        ["18 Benefactive / P.POSS / preverb", "ut- BEN, uur- P.POSS, preverbs ut-/uur-", f"*{d.F(AAR_DO, 2)}* 'he did it' (ut-); *{d.F('SK-hiir-p389-3832', 2)}* 'he is good' (uur-)", "GO p.31, 37"],
        ["19 Sequential", "i-", "*kusaahkikat* 'he might cry' < kuus- POT.1/3.A + Ø- 3.A + i- SEQ + ar- EV + kikak 'cry' + -Ø PERF (GO p.38, quoted as extracted)", "GO p.38"],
        ["20 Aorist / jussive", "uks-", go("taatat") + " vs Parks *tatuksat* 'I went' (GO p.38)", "GO p.38"],
        ["21 Adverbials", "uhuur- 'now, finally', awaahc- 'even'", "Parks *tuksuhuubwíitit* 'let me sit down a while!' (GO p.39, OCR b = h)", "GO p.39"],
        ["22–24 Plurals", "ak-, raar-, ir-", go("tiiraspaatasit") + "; " + go("tiiraaraspaatasit"), "GO p.35–36 Table 10"],
        ["25 Incorporated noun", "body parts, nature, food, cultural products (± raar- PL)", go("ahikiistacakipu") + f"; dictionary *{d.F(IKSKAA, 2)}* 'his hand is in it'", "GO p.43"],
        ["26 Stem", "root ± preverb ± stem elements", f"*{d.W(AT)}*, *{d.W(KAAQAT)}*, *{d.W(RAQUK)}*", "GO p.31, 44"],
        ["27 Aspect", "-Ø/-his PERF, -:hus IMPF, -ta INT, -itik INCH, -uukuʔ HAB", f"*{d.F(KIKAK, 2)}* / *{d.F(KIKAK, 3)}* / *{d.F(KIKAK, 5)}*", "GO p.45–48 Table 17"],
        ["28 Subordination", "class 1 -a, 2 -i, 3 change, 4 Ø, D -u, L -wi", f"*{d.F(AT, 4)}*, *{d.F(ARIK, 4)}*, *{d.F(RAQUK, 4)}*, *{d.F(WIITIK, 4)}*, *{d.F(PAHAAT, 4)}*, *{d.F(KAA, 4)}*", "GO p.46 Table 17"],
        ["29–30 Intentive", "-ta, -rit INT.SUB", go("wiiruuhaasitiiʔ"), "GO p.47–48"],
    ]
    return "\n".join([
        "Parks's Table 6 (GO p.33): **proclitics → inner prefixes → incorporated noun → STEM → suffixes**; Table 7 numbers the inner slots 9–26. "
        "The Blue Book's 'introducer' (L4 p.45–46) = mode + person + number, i.e. Parks's slots 10–24. Each slot below is illustrated by an attested word "
        "with its source.", "", _md(["Slot (Parks)", "Fillers", "Attested example", "Source"], rows), "",
        f"**Blue Book statement of the same structure:** {d.bbq(46, 'introducer')} (BB L4); {d.bbq(102, 'ut becomes uts')} … (BB L17, on *ut* + *uks*)."])


def sec_modes(d):
    rows = []
    for m, lab, fn in [(IND, "Indicative", "statements"), (NEG, "Negative indicative", "negative statements"), (ABS, "Absolutive", "questions, narration"),
                       (CONT, "Contingent", "future, mild imperative"), (POT, "Potential", "'might, will'"), (SUBJ, "Subjunctive (sub.)", "wish, unreal"),
                       (INF, "Infinitive (sub.)", "'for X to ...'"), (GER, "Gerundial (sub.)", "'the one who; when'"), (CONTSUB, "Conditional (sub.)", "'if, when'")]:
        rows.append([lab, fn] + [f"*{d.A('to go', m, p)}*" for p in ("1sg", "2sg", "3sg")] + [f"*{d.A('to drink it', m, '3sg')}*"])
    return "\n".join([
        "Every verb carries a modal prefix (GO p.33–34, Table 8). Appendix 1 shows the same two verbs in every mode:", "",
        _md(["Mode (Parks)", "Function", "'go' 1sg", "'go' 2sg", "'go' 3sg", "'drink it' 3sg"], rows), "",
        f"Sources: App.1 *to go* p.{d.A_page('to go')}, *to drink it* p.{d.A_page('to drink it')}. The Blue Book covers the indicative (*ta-/ti-*), negative (*kaki*, L1 p.32), "
        "absolutive (*ra-* in *Kirike ras•ta?*, L4), the command built on *uks-* (L5 p.53) and the 'indicators of certainty and doubt' *wi, ar/ah, tir, kur/kuh* (L20 p.117), "
        "which are Parks's evidential proclitics *wi-* QUOT, *ar-* EV, *tiir-* INFR, *kuur-* DUB (GO p.37, Table 11)."])


def sec_person(d):
    rows = []
    for p in ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du", "1pl_incl", "1pl_excl", "2pl", "3pl"]:
        rows.append([p, f"*{d.A('to go', IND, p)}*", f"*{d.A('to drink it', IND, p)}*", f"*{d.A('to be good', IND, p)}*", f"*{d.A('to be sick', IND, p)}*"])
    return "\n".join([
        "Agent prefixes *t-* 'I', *s-* 'you', Ø 'he/she/it'; patient prefixes *ku-* 'me', *a-* 'you' (GO p.35, Table 9). Dual *si-* precedes the mode prefix; "
        "plural is marked by *rak-* (1st/2nd), *ir-* COLL or *raar-* INDV (3rd), *ak-* (animate patients) (GO p.35–36, Table 10). Appendix 1, indicative:", "",
        _md(["Person", "'go' (irregular)", "'drink it'", "'be good' (uur-)", "'be sick' (patient-marked)"], rows), "",
        f"Sources: App.1 p.{d.A_page('to go')}, {d.A_page('to drink it')}, {d.A_page('to be good')}, {d.A_page('to be sick')}. "
        f"Blue Book: {d.bbq(58, '+ ku first person')} (L6 p.58); {d.bbq(47, 'Plurality is usually')} (L4 p.47). ⚠ BB writes the inclusive dual as *atsir* and 'they' as *it*; "
        "Parks: *acir-*, *ir-*."])


def sec_aspect(d):
    rows = []
    for eid, cls in [(KIKAK, "4"), (KIIKAA, "4"), (WIITIK, "4"), (RAAH, "1"), (KAAQAT, "1"), (ARIK, "2-i"), (AAR_BECOME, "1-i"), (RAQUK, "3"), (PAHAAT, "VD"), (KAA, "VL"), (WARII, "4")]:
        rows.append([f"*{d.W(eid)}* '{d.G(eid)}'", cls, f"*{d.F(eid, 2)}*", f"*{d.F(eid, 3)}*" if d.has_F(eid, 3) else "—", f"*{d.F(eid, 5)}*", f"*{d.F(eid, 4)}*", f"p.{d.P(eid)}"])
    return "\n".join([
        "Parks GO p.44–48 (Tables 16–17): perfective is unmarked word-finally (*-his* surfaces only before *-ta*), imperfective is *-:hus* (final *s* dropped → *-huʔ*), "
        "intentive *-ta*, habitual *-uukuʔ*, inchoative *-itik*. Subordinate perfectives take a class-specific ending, which is why Parks assigns each verb a class.", "",
        _md(["Stem", "Class", "3sg PERF (form 2)", "IMPF (form 3)", "INT (form 5)", "GER (form 4)", "Parks"], rows), "",
        "Parks's own illustrations: *tikacat* 'he cut it' / *tikacaakuʔ* 'he is cutting it' (GO p.47); *tikíkat* / *tikikakísta* 'he is going to cry' (GO p.46); "
        f"descriptive *tipahaaʔat* 'it is red' / *tipahaatuksta* / *iriirapahaattu* (GO p.49). Blue Book: {d.bbq(97, 'drop off')} (L15); "
        f"{d.bbq(108, 'suffix +ta')} (L19)."])


def sec_nouns(d):
    kin_rows = []
    for k in d.kin:
        if k["source"] == "appendix3":
            kin_rows.append([k["english_term"], k["form_1sg"] or "—", k["form_2sg"] or "—", k["form_3sg"] or "—"])
    return "\n".join([
        "**Formation.** Root + *-uʔ* (*" + d.W('SK-iksuq-p64-1111') + "*), root + *-kis* (*" + d.W('SK-asaaki-p362-3736') + "*), root + root + *-uʔ* "
        f"(*{d.W('SK-ikskiicuq-p63-1094')}* 'finger' = hand + neck). Case and number (GO p.30, Table 4): body-part nouns take PL *-raar-* and INST/LOC *-hiriʔ* "
        f"(Parks's *ikstaaririʔ* 'with the hands'); other nouns LOC *-kat* (*{d.W('SK-picikat-p111-2162')}* 'in cold weather') and INST *-hiriʔ*; names LOC *-ru* "
        f"(*{d.W('SK-kirikuurukstu-p97-1864')}* 'Anadarko').", "",
        f"**Incorporation** (GO p.43): body parts, natural phenomena, foods and cultural products go before the stem and drop *-uʔ*: *{d.W(IKSKAA)}* "
        f"'{d.G(IKSKAA)}' (3sg *{d.F(IKSKAA, 2)}*); Parks's *ahikiistacakipu* 'he gathered the bones' (*kiis-* + *raar-* PL + *takipuh*). Nouns that do not incorporate: personal names, "
        "place names, kinship terms, 'man/woman', animal names — with exceptions such as *tuuricaahiksii* 'he is a good-looking person' (GO p.43). "
        f"Blue Book: {d.bbq(68, 'r becomes h before k')} (L8 p.68, *hatur* + *ka* + *arit* → *ti•hatuh•kaarit* 'he's standing in the road').", "",
        "**Possession.** Verbal: *ir...uk* (+ *ku-*) agent possessor, *ir...ri...uur-* physical possessor, *uur-* patient possession, *ut-* benefactive (GO p.36–37); "
        f"Blue Book frame {d.bbq(51, 'mode + phys. poss.')} (L5). Kinship (Appendix 3) is the only inflected noun class:", "",
        _md(["Term", "my", "your", "his/her"], kin_rows), "",
        "⚠ Cross-check against the dictionary and the Blue Book: App.3 *iʔaastiʔ* 'his father' vs dictionary *" + d.W('SK-hiqaastiq-p40-0689') + "* (p.40) vs BB *hiasti'* (L7 p.62); "
        "App.3 *atipaat* vs dictionary *" + d.W('SK-atipat-p19-0241') + "* (p.19) and BB *atipat*; App.3 *awaat* 'your niece/nephew' vs BB *swat* (L7 p.61). "
        "The kinship_paradigms table also holds three BB-only supplements (*tikiʔ*, *tsuwat*, *swat*) that Appendix 3 lacks."])


def sec_sound(d):
    ex = _rule_examples(d)
    order = sorted(ex, key=lambda r: -ex[r][0])
    rows = []
    for rid in order:
        n, lst = ex[rid]
        samples = "; ".join(f"*{' + '.join(r['pieces'])}* → *{r['hw_key']}* (p.{r['page']})" for r in lst[:2])
        rows.append([RULE_NAMES.get(rid, rid), n, samples])
    return "\n".join([
        "Counts are the number of dictionary headwords whose Parks etymology is reproduced only when the rule applies (segmentation log, high/medium confidence). "
        "Rules marked ⚠ are regularities needed to reproduce the data but absent from Parks's 24 numbered rules as formalised in `sound_changes.py`.", "",
        _md(["Rule", "Headwords", "Before → after (Parks analysis → attested word)"], rows), "",
        "**Blue Book rule statements and their Parks counterparts.**", "",
        _md(["Blue Book", "Where", "Parks"], [
            [d.bb_quote(41, 'r changes to t'), "L3 p.41", "Rule 21"],
            [d.bb_quote(41, 'w changes to p'), "L3 p.41", "not numbered; attested (w>p above) ⚠"],
            [d.bb_quote(41, 'k drops off before p'), "L3 p.41", "no counterpart in the engine ⚠ (BB *ti hak + wa + wi → ti ha•pa•wi*)"],
            [d.bb_quote(42, 'r changes to h'), "L3 p.42", "Rules 13–15 (before r/h) and 12R (prefix r → h); not before every consonant ⚠"],
            [d.bb_quote(42, 'combine to make e'), "L3 p.42", "Rule 7 (i + a → ii); spelling differs ⚠"],
            [d.bb_quote(50, 'When i follows u'), "L5 p.50", "Rule 6 (u-domination) / Rule 1R"],
            [d.bb_quote(67, 'strong vowel'), "L8 p.67", "Rule 1R (ti-/ri- + u → tu-/ru-)"],
            [d.bb_quote(97, 'drop off'), "L15 p.97", "GO p.46 stem-final k (k>t above); Rule 3R before -his"],
            [d.bb_quote(102, 's +s becomes'), "L17 p.102", "no direct counterpart; Parks Rule 17 is s → c after a consonant ⚠"],
            [d.bb_quote(102, 'ut becomes uts'), "L17 p.102", "Rule 11R (ut- → uc- before i-) is the nearest; BB's environment differs ⚠"],
        ])])


def sec_sources(d):
    return "\n".join([
        "- Parks, D. R. *A Dictionary of Skiri Pawnee*: Grammatical Overview pp. 29–51 (`extracted_data/grammatical_overview.json`); Chapter 3 sound rules (`scripts/sound_changes.py`, "
        "`sound_change_rules` table); Appendix 1 paradigms (`verb_paradigms`, 7 verbs × 10 modes × 11 persons); Appendix 2 irregular roots (`irregular_verb_roots`); Appendix 3 kinship "
        "(`kinship_paradigms`, `extracted_data/appendix3_kinship.json`); dictionary entries with Parks's etymologies (`lexical_entries`, `etymology`, `paradigmatic_forms`).",
        "- *Pari Pakuru* (Blue Book), lessons 1–20 (`pari pakuru/Blue_Book_Pari_Pakuru.txt`, page markers as printed; `blue_book_attestations` for linked forms).",
        "- Project scripts: `scripts/morpheme_inventory.py` (30-slot template, `morpheme_inventory` table), `scripts/stem_extractor.py` (stem/preverb junction rules), "
        "`scripts/root_extraction.py` (this analysis), `scripts/build_root_curriculum.py` (this document).",
        f"- Extraction totals: {d.stats['entries']} entries; {d.stats['roots']} root senses; {d.stats['affixes']} affix records; segmentation confidence "
        f"high {d.stats['confidence'].get('high', 0)}, medium {d.stats['confidence'].get('medium', 0)}, low {d.stats['confidence'].get('low', 0)}.",
    ])


GUIDE = [
    {"title": "1. Two spellings of one language", "body": sec_orthography},
    {"title": "2. Word classes and the shape of a stem", "body": sec_stem},
    {"title": "3. The verb template, slot by slot", "body": sec_template},
    {"title": "4. Mode", "body": sec_modes},
    {"title": "5. Person and number", "body": sec_person},
    {"title": "6. Aspect and subordination (and Parks's verb classes)", "body": sec_aspect},
    {"title": "7. Nouns: formation, case, incorporation, possession", "body": sec_nouns},
    {"title": "8. Sound changes at morpheme boundaries", "body": sec_sound},
    {"title": "9. Sources", "body": sec_sources},
]


# ---------------------------------------------------------------------------
# Manual review log
# ---------------------------------------------------------------------------

def rev_conflicts(d):
    items = [
        f"'his father': App.3 *iʔaastiʔ*; dictionary *{d.W('SK-hiqaastiq-p40-0689')}* (p.40, etymology hi-+aas+riʔ); BB *hiasti'* (L7 p.62, OCR *hidsti'*). Two Parks sources disagree on the initial *h*.",
        f"'my grandfather': App.3 *atipaat*; dictionary *{d.W('SK-atipat-p19-0241')}* (p.19); BB *atipat* (L7 p.60). Vowel length.",
        f"'your niece/nephew': Parks *{d.W('SK-awaat-p20-0262')}* (p.20) and App.3 *awaat*; BB *swat* (L7 p.61). Different prefix (BB s- vs Parks a-).",
        "'my daughter' BB *tsuwat*, 'my son' BB *tiki'* (L7 p.61): no Parks kinship paradigm; dictionary has *tiki* 'son, sonny' only (p.165).",
        f"'I have it': BB *tah•ra* (L4 p.46) vs App.1 *{d.A('to have it', IND, '1sg')}*; 'I don't have it' BB *Kakah•ra* vs App.1 *{d.A('to have it', NEG, '1sg')}*. BB keeps the *r* that Parks's Rules 13–15 absorb.",
        f"'We (3+) have them': BB *Tahraktarra* with *rak-* (L4 p.47) vs App.1 'to have it' plural with *si-* (*{d.A('to have it', IND, '1pl_excl')}*). Different plural strategy for this class-3 verb.",
        f"'it is red': BB *ti pahaat* (L2 p.33) vs Parks *{d.F(PAHAAT, 2)}* (p.107; GO p.49). BB omits the reduplicated *-ʔa-* of Class I descriptives.",
        f"'he is doing it': BB *tut•ari'* (L6 p.56) vs Parks 3sg perfective *{d.F(AAR_DO, 2)}*, imperfective *{d.F(AAR_DO, 3)}*. BB glosses an imperfective form as the citation form.",
        "nominaliser: BB *hiri* (L13 p.88–89) vs Parks *irii-* (GO p.42). Initial *h* and vowel length.",
        "commands: BB *Suks•paku'* (L5 p.53) vs Parks *i-* CONT + *s-* + *uks-* (GO p.38, *sukskirikaʔaaʔ*). BB does not write the contingent *i-*.",
        "spelling rules: BB 'k drops off before p' (L3 p.41) and 's + s → s•ts' (L17 p.102) have no counterpart among Parks's 24 rules; BB 'i + a → e' corresponds to Parks Rule 7 (→ ii); BB 'w → p' is attested in 115 headwords but unnumbered in Parks.",
        "BB *tsau* 'face' (L2 p.36 *tskau*) vs Parks *" + d.W('SK-ckaquq-p30-0460') + "*; BB *kskitsu'* 'finger' (L5 p.52) vs Parks *" + d.W('SK-ikskiicuq-p63-1094') + "*: BB drops the initial *i-* of *icka-*/*iks-* in these words; Parks does so only in *ckaʔuʔ*, *cusuʔ*, *caahiks*.",
        "Parks Table 4 (GO p.30) prints the instrumental/locative suffix as *-biriʔ* (OCR); dictionary etymologies have *-hiriʔ*, *-piriʔ*, *-iriʔ*.",
        "Parks GO examples containing *b* (*wiitahurabwiicaʔ*, *tuksuhuubwíitit*, *siwituksaakitaabku*, *riibiikakuspihat*) are OCR errors for *h*/*p*; cited as printed in the extraction, flagged here.",
    ]
    return "\n".join(f"- ⚠ {x}" for x in items)


def rev_homonyms(d):
    lines = ["Decisions encoded in `homonym_sense()` of `scripts/root_extraction.py`; each is reversible.", ""]
    for key, why in [
        ("hiir #(uur...) be good", "split from *hiir* 'grass' by the presence of the preverb *uur-* or a 'good/nice' gloss (Parks App.1 'to be good' *tuuhii*; GO p.32 'hiir (uur...)')."),
        ("hiir #grass", "grass/hay glosses or unglossed nouns."),
        ("arik #be standing", "verb hosts; App.2 irregular root *arik*."),
        ("arik #horn", "noun hosts glossed horn/braid/patch."),
        ("as #father (kinship, atiʔas)", "kinship gloss 'father' vs the body root *as* 'foot'."),
        ("kaa #grandmother (kinship, atikaʔ)", "kinship gloss vs *kaa* 'inside'."),
        ("raar #samesex sibling", "*raar* occurrences with a lexical gloss are kept apart by gloss (sibling, fringe, under, ...); unglossed *raar* is counted as the PL/ITER affix (ambiguous)."),
    ]:
        r = d.roots.get(key)
        lines.append(f"- **{key}** — {why}" + (f" Result: {r['frequency']} words, confidence {r['confidence']}." if r else " (not present after rerun)"))
    lines += ["", "Variant merges (surface shapes folded into one root by a single rule plus a shared gloss):", ""]
    for v in d.variant_merges:
        lines.append(f"- *{v['variant']}* → **{v['underlying']}** by {v['rule']} ({v['note']}); shared gloss {v['shared_gloss']}; confidence {v['confidence']}.")
    return "\n".join(lines)


def rev_gaps(d):
    noetym = d.stats["methods"].get("no_etymology", 0)
    return "\n".join([
        f"- {noetym} of {d.stats['entries']} entries have no Parks etymology; they were not segmented and count toward a root only when the headword itself is the root.",
        "- No dictionary paradigm form and no Appendix 1 cell contains the aorist/jussive *uks-*; it is attested only in Parks's grammar examples (GO p.38) and the Blue Book (L5, L8, L13). Lesson 6.4 therefore uses BB-attested words labelled as such.",
        "- No dictionary etymology carries the label AUG *-kusuʔ*; Parks's single example (*wiitakusuʔ*, GO p.31) is not a dictionary headword.",
        "- The Blue Book body dialogues (*paks•ku*, *kirik•ta*, *tiku•paks•taari'*) have no dictionary headwords; parallel dictionary words (*iksta*, *kiista*, *ikskaa*) are used instead.",
        f"- The dictionary gives no form 2 for *rihuur* 'be big' and no form 3 for *{d.W(KUS)}*; compounds supply the pattern.",
        "- Appendix 1 covers seven verbs only; mode paradigms for all other verbs are inferred, never shown, in this curriculum.",
        "- Blue Book auto-links of type 'prefix' (404 rows in blue_book_attestations) are unreliable: e.g. BB *kisu'* 'bone' → *kisu* 'be slender' (should be *" + d.W('SK-kiisuq-p93-1757') + "*), BB *kaki'* 'no' → *ka* 'be outstanding', BB *tirakis* 'bow' → *tir* 'be together', BB *kararu'* 'stomach' → *ka*, BB *kasu'* 'leg' → *ka*, BB *atlas* 'my father' → *at* 'go'. These should be re-linked before BB forms are shown as dictionary-confirmed.",
        "- 93 database entries come only from the Blue Book (source = blue_book) and have no Parks confirmation.",
    ])


def rev_engine(d):
    c = Counter()
    for rec in d.seg.values():
        for r in rec["rules"]:
            c[r] += 1
    unnum = {k: v for k, v in c.items() if k in ("ʔ-epenthesis (V+V)", "w>p", "k>t", "V-length", "r>h", "tolerance: vowel length/ʔ/h")}
    return "\n".join([
        f"- Methods: {', '.join(f'{k} {v}' for k, v in sorted(d.stats['methods'].items(), key=lambda kv: -kv[1]))}.",
        f"- {d.stats['methods'].get('engine_tolerant', 0) + d.stats['methods'].get('located_tolerant', 0)} headwords match Parks's analysis only after ignoring vowel length, ʔ and h (medium confidence).",
        "- Regularities required by the data but not among Parks's 24 numbered rules (counts = headwords explained): " + ", ".join(f"{k} {v}" for k, v in sorted(unnum.items(), key=lambda kv: -kv[1])) + ".",
        f"- {d.stats['methods'].get('unlocated', 0)} headwords could not be reproduced from Parks's analysis by any single rule per morpheme (low confidence; listed in Part 2).",
        "- Root frequency is type frequency over distinct headwords (first alternate), including the 93 Blue-Book-only entries where Parks's analysis names the root.",
    ])


def rev_speaker(d):
    return "\n".join([
        "Items that no written source settles and that need a speaker or linguist:",
        "- Whether the reduplicated *-ʔa-* of Class I descriptives (Parks *tipahaaʔat*) is heard in contemporary speech where the Blue Book writes *ti pahaat*.",
        "- Vowel length in roots that Parks writes both long and short (*paaks/paks*, *kiriik/kirik*, *haas/has*, *kaatiit/katiit*, *raak/rak*): lexical or conditioned?",
        "- The *r ~ h* alternation in 'wood' (*raak/haak*) and *w ~ p* word-initially (*wiita/piita*, *wiir/piir*): Parks records both shapes without a rule.",
        "- The initial *h* of 'his father' (*hiʔaastiʔ* vs *iʔaastiʔ*) and of the nominaliser (BB *hiri* vs Parks *irii-*).",
        "- BB *swat* 'your niece/nephew' against Parks *awaat*.",
        "- Every root whose Parks glosses disagree across entries (listed in Part 2 under 'Roots flagged medium/low').",
    ])


REVIEW_MANUAL = [
    {"title": "A. Blue Book vs Parks (and Parks vs Parks): conflicts shown, not resolved", "body": rev_conflicts},
    {"title": "B. Homonym splits and variant merges", "body": rev_homonyms},
    {"title": "C. Gaps in the data", "body": rev_gaps},
    {"title": "D. Limits of the sound-change engine as applied here", "body": rev_engine},
    {"title": "E. Needs speaker / linguist review", "body": rev_speaker},
]
