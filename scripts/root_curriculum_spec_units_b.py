"""Units 4–7: one affix or rule at a time, combined only with roots already taught."""

# ids (all resolved against skiri_pawnee.db)
IKSU, ASU, PAKSU, KIISU, KAASU, KARAARU, HURAARU, AKAARU, RAAQU, HIIRU, TAAKAARU, PAHAATU, HAAKAQU, PIIRAUQ, AWIQU, KIRAARU, HAATU = (
    "SK-iksuq-p64-1111", "SK-asuq-p18-0202", "SK-paksuq-p110-2116", "SK-kiisuq-p93-1757", "SK-kaasuq-p74-1322", "SK-karaaruq-p77-1409",
    "SK-huraaruq-p47-0790", "SK-akaaruq-p9-0108", "SK-raaquq-p115-2248", "SK-hiiruq-p390-3845", "SK-taakaaruq-p502-4234",
    "SK-pahaatuq-p107-2052", "SK-haakaquq-p33-0559", "SK-piiraquq-p460-4084", "SK-awiquq-p21-0290", "SK-kiraaruq-p94-1793", "SK-haatuq-p36-0627")
KAAHURAARU, UUSKUUTU, KITAHAARU, HUKAKUSU, ASAAKAARU, KIISKUCUU = (
    "SK-kaahuraaruq-p72-1283", "SK-uuskuutuq-p173-3427", "SK-kitahaaruq-p98-1910", "SK-hukakusuq-p44-0740", "SK-asaakaaruq-p362-3732", "SK-kiiskucuuq-p92-1740")
ASAAKI, RAKIS, KARITKI, TIRAAKIS, KUUCKI, HASKI, CUURAKI, KISAACKI, KACIIKI, PAAKIS, PAKSKUUKU, HAAKARAHKUUKU = (
    "SK-asaaki-p362-3736", "SK-rakis-p135-2644", "SK-karitki-p79-1443", "SK-tiraakis-p166-3268", "SK-kuucki-p452-4007", "SK-haski-p37-0650",
    "SK-cuuraki-p32-0536", "SK-kisaacki-p98-1883", "SK-kaciiki-p75-1358", "SK-paakis-p454-4053", "SK-pakskuukuquq-p109-2106", "SK-haakarahkuukuquq-p34-0572")
IKSKIICU, HASKIICU, PAKSKIRAARU, HAAKAKIRAARU, KICKARAARU, UUSKARAARU, KIRIKTAAKU, KAASTAKIS, KIISAAKAQU, ASAAKIRAAQ, KICTAAKAA, HUKAHAARU = (
    "SK-ikskiicuq-p63-1094", "SK-haskiicuq-p37-0653", "SK-pakskiraaruq-p109-2102", "SK-haakakiraaruq-p34-0567", "SK-kickaraaruq-p86-1618",
    "SK-uuskaraaruq-p173-3423", "SK-kiriktaakuq-p96-1847", "SK-kaastakis-p74-1320", "SK-kiisaakaquq-p91-1724", "SK-asaakiraaq-p362-3738",
    "SK-kictaakaa-p436-3947", "SK-hukahaaruq-p44-0734")
KIIHAAHIRI, KITAHAAHIRI, AWIIRAHIRI, RUKSIRI, ASKUSIRI, PICIKAT, IRITKAT, WARAAKAT, CKARAARU, KICPIIRAARU, RAKTARIIKAQU, CAAHIKSTAHKUCUU, KIRIKUURUKSTU = (
    "SK-kiihaahiriq-p90-1680", "SK-kitahaahiriq-p98-1909", "SK-awiirahiriq-p23-0301", "SK-ruksiriq-p148-2871", "SK-askusiriq-p16-0180",
    "SK-picikat-p111-2162", "SK-iritkat-p67-1190", "SK-waraakat,_paraakat-p177-3504", "SK-ckaraaruq-p30-0467", "SK-kicpiiraaruq-p87-1652",
    "SK-raktariikaquq-p135-2658", "SK-caahikstahkucuuq-p26-0368", "SK-kirikuurukstu-p97-1864")
AT, KUS, SA, ARIK, WIITIK, WARII, KIKAK, RAQUK, KIIKAA, RAAH, RAAH_UUR, KAAQAT, KAAKUS, KAAKUS_UT, KAAKUS_UUR, AAR_BECOME, AAR_DO, IIRIK, HIIR_GOOD, AWUH, AWUH_UUR, KUUT, HURAHAC, A_COME, KAAQA = (
    "SK-at-p18-0220", "SK-kus-p102-1993", "SK-sa-p150-2933", "SK-arik-p13-0145", "SK-wiitik-p179-3555", "SK-warii-p177-3506", "SK-kikak-p93-1767",
    "SK-raquk-p114-2221", "SK-kiikaa-p90-1694", "SK-raah-p116-2264", "SK-raah-p116-2265", "SK-kaaqat-p2-0010", "SK-kaakus-p72-1294",
    "SK-kaakus-p72-1295", "SK-kaakus-p73-1296", "SK-aar-p351-3596", "SK-aar-p351-3598", "SK-iirik-p408-3912", "SK-hiir-p389-3832",
    "SK-awuh-p26-0353", "SK-awuh-p26-0354", "SK-kuut-p452-4017", "SK-hurahac-p47-0798", "SK-a-p349-3577", "SK-kaaqa-p2-0001")
KAAHIKUUT, ACIKSURAHAC, ACIKSTAAHIIS, KISUQAAR, PAHITAAR = (
    "SK-kaahikuut-p2-0025", "SK-aciksurahac-p8-0074", "SK-acikstaahiis-p7-0051", "SK-kisuqaar-p98-1898", "SK-pahitaar-p108-2056")
IKSKAA, ICKAKAA, IKSTA, KIISTA, HAASTA, KIICKAA, ASPIITIK, ASKAWAT, HAAKARIIR, IKSTAAH, KITAKUS, KAASA, HUKAARIK, KAARIK = (
    "SK-ikskaa-p63-1087", "SK-ickakaa-p57-0978", "SK-iksta-p63-1097", "SK-kiista-p93-1754", "SK-haasta-p36-0621", "SK-kiickaa-p89-1663",
    "SK-aspiitik-p17-0186", "SK-askawat-p16-0164", "SK-haakariir-p34-0577", "SK-ikstaah-p63-1099", "SK-kitakus-p98-1912", "SK-kaasa-p73-1312",
    "SK-hukaarik-p44-0728", "SK-kaarik-p73-1306")
ACIKSTAQUK, ACIKSTIIHAC, ASUUKTIK = "SK-acikstaquk-p7-0049", "SK-acikstiihac-p7-0063", "SK-asuuktik-p18-0215"
KAA = "SK-kaa-p418-3942"
KATIIHAQUK, ICKARAQUK, AKARAQUK, KITUHAQUK, KAASIK, HIIRIK, RAAHIIRIK, KIKAARIK, KISAKTIK, KIICKAAWUH = (
    "SK-katiihaquk-p82-1530", "SK-ickaraquk-p57-0981", "SK-akaraquk-p11-0110", "SK-kituhaquk-p99-1931", "SK-kaasik-p73-1315",
    "SK-hiirik-p389-3842", "SK-raahiirik-p117-2273", "SK-kikaarik-p93-1766", "SK-kisaktik-p98-1887", "SK-kiickaawuh-p89-1664")
KICAAR, KIRIKAQAAR, KITUUQAAR, AWIQAAR, RAAHIIRIITIK, PIIRIITIK, IKSIITIK, RAAHIWAAR, UUSPAA, KATAWAARIK = (
    "SK-kicaar-p84-1573", "SK-kirikaqaar-p95-1825", "SK-kituuqaar-p99-1937", "SK-awiqaar-p21-0282", "SK-raahiiriitik-p117-2272",
    "SK-piiriitik-p460-4102", "SK-iksiitik-p63-1085", "SK-raahiwaar-p117-2279", "SK-uuspaa-p173-3428", "SK-katawaarik-p82-1516")
PAHAAT, KAATIIT_VD, TAAKAAR, RAHKATAAR, TARIIQUUS, KIIQAC, KIC_VD, HIIR_GRASS, HURAAR_VD, KIRAAR_VD, HAAS_VD, KATUUS, KIISKAAC, KICKIRAAR, PAHAATKAATIIT, KAAHURAAR, SAKUUR_VD = (
    "SK-pahaat-p107-2050", "SK-kaatiit-p74-1330", "SK-taakaar-p502-4233", "SK-rahkataar-p131-2560", "SK-tariiquus-p161-3146", "SK-kiiqac-p436-3967",
    "SK-kic-p84-1568", "SK-hiir-p389-3831", "SK-huraar-p46-0779", "SK-kiraar-p94-1788", "SK-haas-p36-0613", "SK-katuus-p83-1540", "SK-kiiskaac-p92-1729",
    "SK-kickiraar-p87-1634", "SK-pahaatkaatiit-p107-2051", "SK-kaahuraar-p72-1277", "SK-sakuur-p152-2962")

IND, NEG, CONT, ABS, GER, POT = ("indicative_perfective", "negative_indicative_perfective", "contingent_perfective",
                                 "absolutive_perfective", "gerundial_perfective_subordinate", "potential_perfective")
TIKUKS = "Tiku'ks"
PERSONS = ["1sg", "2sg", "3sg", "1du_incl", "1du_excl", "2du", "3du", "1pl_incl", "1pl_excl", "2pl", "3pl"]


def _derive(d, pairs, src_n, tgt_n, label_src, label_tgt):
    """Practice C: given form src_n of each verb, produce form tgt_n (answers attested)."""
    lines = [f"Given the {label_src} of each verb, give the attested {label_tgt}.", ""]
    for i, eid in enumerate(pairs, 1):
        lines.append(f"C{i}. *{d.F(eid, src_n)}* ('{d.G(eid)}', stem *{d.W(eid)}*) → ______")
    lines += ["", "Answers (Parks Part II forms):", ""]
    for i, eid in enumerate(pairs, 1):
        lines.append(f"C{i}. *{d.F(eid, tgt_n)}* (Parks p.{d.P(eid)}, `{eid}`)")
    return "\n".join(lines)


def _stem_to_form(d, eids, n, label):
    lines = [f"Given the dictionary stem, give the attested {label}.", ""]
    for i, eid in enumerate(eids, 1):
        lines.append(f"C{i}. *{d.W(eid)}* ('{d.G(eid)}') → ______")
    lines += ["", "Answers (Parks Part II forms):", ""]
    for i, eid in enumerate(eids, 1):
        lines.append(f"C{i}. *{d.F(eid, n)}* (Parks p.{d.P(eid)}, `{eid}`)")
    return "\n".join(lines)


def _cells(d, verb, mode, persons, given="1sg"):
    lines = [f"Appendix 1, *{verb}*, {mode.replace('_', ' ')}: given {given} *{d.A(verb, mode, given)}*, fill the other cells.", ""]
    for i, p in enumerate(persons, 1):
        lines.append(f"C{i}. {p} → ______")
    lines += ["", "Answers (App.1 p.%s):" % d.A_page(verb), ""]
    for i, p in enumerate(persons, 1):
        lines.append(f"C{i}. {p} *{d.A(verb, mode, p)}* '{d.A_eng(verb, mode, p)}'")
    return "\n".join(lines)


UNITS_B = [
    # =====================================================================
    {
        "id": 4, "title": "Making nouns",
        "intro": ("One affix at a time, applied only to roots from Units 1–3. Parks's nominal affixes are few (GO p.30–31, Tables 4–5): "
                  "the absolutive *-uʔ*, the diminutive *-kis*, the augmentative *-kusuʔ*, the 'covering' *-kuukuʔuʔ*, the feminine *c-*, "
                  "two cases (instrumental/locative *-hiriʔ*, locative *-kat*, *-ru*) and the body-part plural *-raar-*."),
        "bb_alignment": "BB L1 p.31 introduces *-u'*; BB L2 p.35 and L3 p.41–42 give the spelling rules that operate when roots are joined; BB L4 p.47 discusses plurality.",
        "lessons": [
            {
                "id": "4.1", "title": "the noun suffix -uʔ",
                "objectives": ["Form free nouns from known roots with *-uʔ* (NOM).", "Recognise ʔ-insertion when the root ends in a vowel."],
                "morphemes": [{"label": "NOM *-uʔ*", "meaning": "nominal absolutive: makes a free noun from a stem (no added meaning)", "forms": ["uʔ"],
                               "source": "Parks GO p.31 Table 5 (iksuʔ < iks- + -uʔ); 677 dictionary etymologies name it; BB L1 p.31"}],
                "walkthrough": lambda d: (
                    f"Parks: 'independent nouns are usually derived with the nominal absolutive suffix *-uʔ*' (GO p.30); the Blue Book says the same "
                    f"({d.bbq(31, 'suffix -u')}). Consonant-final roots simply add it: *{d.W(IKSU)}*, *{d.W(ASU)}*, *{d.W(KIISU)}*, *{d.W(KAASU)}*, *{d.W(HURAARU)}*, "
                    f"*{d.W(AKAARU)}*, *{d.W(TAAKAARU)}* '{d.G(TAAKAARU)}', *{d.W(PAHAATU)}* '{d.G(PAHAATU)}'. Vowel-final roots take a glottal stop before *-uʔ*: "
                    f"*{d.W(HAAKAQU)}*, *{d.W(PIIRAUQ)}*, *{d.W(AWIQU)}*, *{d.W(RAAQU)}* '{d.G(RAAQU)}'. Short roots may lengthen: *{d.W(HAATU)}* 'tongue' from *hat*."),
                "examples": [IKSU, ASU, PAKSU, KIISU, KAASU, KARAARU, HURAARU, AKAARU, RAAQU, HIIRU, TAAKAARU, PAHAATU],
                "exercises": ([TAAKAARU, PAHAATU, AWIQU, KIRAARU, HAATU], [KAAHURAARU, UUSKUUTU, KITAHAARU, HUKAKUSU, ASAAKAARU]),
            },
            {
                "id": "4.2", "title": "small and large: -kis, -kusuʔ, -kuukuʔuʔ",
                "objectives": ["Form diminutives with *-kis* and see its two surface shapes (*-kis*, *-ki*).", "Know the augmentative and 'covering' suffixes from Parks Table 5."],
                "morphemes": [
                    {"label": "DIM *-kis*", "meaning": "diminutive; also simply forms free nouns", "forms": ["kis"],
                     "source": "Parks GO p.31 Table 5 (asaaki 'dog', riiciki 'knife'); 58 etymologies", "note": "word-final *s* is often dropped (Parks Rule 9R): *-ki*"},
                    {"label": "AUG *-kusuʔ*", "meaning": "augmentative 'large, big'", "forms": ["kusuʔ"],
                     "source": "Parks GO p.31 Table 5 (wiitakusuʔ 'large man')", "note": "⚠ no dictionary etymology labels AUG; the only analysed example is Parks's own (data gap)"},
                    {"label": "*-kuukuʔuʔ* 'covering'", "meaning": "covering of N", "forms": ["kuuku"],
                     "source": "Parks GO p.31 Table 5 (pakskuukuʔuʔ 'hat'); dictionary *kuuku* 'covering' root, 22 words"},
                ],
                "walkthrough": lambda d: (
                    f"*{d.W(ASAAKI)}* 'dog' = *asaa* + *kis* with the final *s* lost (Rule 9R). "
                    f"*{d.W(RAKIS)}* = *rak* + *kis* with *kk* → *k* (Rule 20, degemination); *{d.W(TIRAAKIS)}* 'bow' likewise. *{d.W(KARITKI)}* '{d.G(KARITKI)}' and "
                    f"*{d.W(HASKI)}* '{d.G(HASKI)}' show *-ki*. The 'covering' suffix: *{d.W(PAKSKUUKU)}* 'hat' (head-covering) and *{d.W(HAAKARAHKUUKU)}* "
                    f"'{d.G(HAAKARAHKUUKU)}' (mouth + PL + covering + NOM)."),
                "examples": [ASAAKI, RAKIS, KARITKI, TIRAAKIS, KUUCKI, HASKI, CUURAKI, KISAACKI, KACIIKI, PAAKIS, PAKSKUUKU, HAAKARAHKUUKU],
                "exercises": ([ASAAKI, RAKIS, KARITKI, HASKI, TIRAAKIS], [KUUCKI, CUURAKI, KACIIKI, KISAACKI, PAKSKUUKU]),
            },
            {
                "id": "4.3", "title": "noun + noun compounds and what happens at the seam",
                "objectives": ["Build compound nouns from two known roots plus *-uʔ*.",
                               "Apply the boundary rules that appear most often in the data: *r* → *t* after an obstruent (Rule 21), *h*-loss (16), final *r*-loss (23), *t*+*r* → *h* (13–15), same-vowel contraction (5), ʔ-insertion."],
                "morphemes": [{"label": "Rule 21 (*r* → *t* / obstruent _)", "meaning": "Parks Ch. 3 Rule 21; BB L2 p.35 and L3 p.41 rule 1", "forms": [],
                               "source": "sound_changes.py; 139 dictionary headwords explained by it"},
                              {"label": "Rule 16 (*h*-loss), Rule 23 (final *r*-loss), Rules 13–15 (*tr* → *hr* → *h*), Rule 5 (same-vowel contraction), ʔ-epenthesis",
                               "meaning": "boundary adjustments", "forms": [], "source": "Parks Ch. 3; counts in review log"}],
                "walkthrough": lambda d: (
                    f"*{d.W(IKSKIICU)}* 'finger' = hand + neck + NOM with no change. *{d.W(KIRIKTAAKU)}* '{d.G(KIRIKTAAKU)}' = *kirik* + *raak* + *uʔ*: after *k* the "
                    f"*r* of *raak* becomes *t* (Rule 21) — the rule the Blue Book states as {d.bbq(35, 'rakis + rahkata')}. *{d.W(KAASTAKIS)}* = *kaas* + *rakis*, "
                    f"same rule after *s*. *{d.W(ASAAKAARU)}* 'barn' = *asaa* + *akaar* + *uʔ*: *aa* + *a* contract to *aa* (Rule 5). *{d.W(KIISAAKAQU)}* "
                    f"'{d.G(KIISAAKAQU)}' = *kiis* + *haaka* + *uʔ*: the *h* of *haaka* is lost after *s* (Rule 16) and ʔ separates *a* from *uʔ*. "
                    f"*{d.W(KICTAAKAA)}* 'gasoline' = *kic* + *taakaar*: word-final *r* is dropped (Rule 23). *{d.W(ASAAKIRAAQ)}* '{d.G(ASAAKIRAAQ)}' = *asaa* + *kiraar*: "
                    f"final *r* lost and a glottal stop closes the word."),
                "examples": [IKSKIICU, HASKIICU, PAKSKIRAARU, HAAKAKIRAARU, KICKARAARU, UUSKARAARU, KIRIKTAAKU, KAASTAKIS, ASAAKAARU, KIISAAKAQU, KICTAAKAA, ASAAKIRAAQ],
                "bb_notes": lambda d: (f"BB L3 p.41–42 spelling rules: {d.bbq(41, 'r changes to t')}; {d.bbq(41, 'w changes to p')}; {d.bbq(41, 'k drops off before p')}; "
                                       f"{d.bbq(42, 'r changes to h')}; {d.bbq(42, 'combine to make e')}. Parks equivalents: rule 1 = Rule 21; rule 2 (*w* → *p*) is not among "
                                       "Parks's 24 numbered rules but is attested in 115 dictionary headwords (flagged as unnumbered); rule 3 (*k* drops before *p*) has no Parks "
                                       "counterpart in the engine ⚠; rule 4 corresponds to Rules 13–15 only before *r*/*h* (Parks has *r* → *h* in prefixes, Rule 12R) ⚠; "
                                       "rule 5 (*i* + *a* → *e*) corresponds to Parks Rule 7 (*i* + *a* → *ii*) — the two sources write the result differently ⚠."),
                "exercises": ([KIRIKTAAKU, KAASTAKIS, ASAAKAARU, KIISAAKAQU, KICTAAKAA], [PAKSKIRAARU, HAAKAKIRAARU, UUSKARAARU, ASAAKIRAAQ, HUKAHAARU]),
            },
            {
                "id": "4.4", "title": "case and number on nouns: -hiriʔ, -kat, -ru, -raar-",
                "objectives": ["Recognise the instrumental/locative *-hiriʔ*, the locatives *-kat* and *-ru*, and the plural *-raar-*."],
                "morphemes": [
                    {"label": "LOC/INST *-hiriʔ* (Parks Table 4 writes *-biriʔ*, an OCR shape for *-hiriʔ/-piriʔ*)", "meaning": "'with, using; in, on, at'", "forms": ["hiriʔ", "piriʔ", "iriʔ"],
                     "source": "Parks GO p.30 Table 4 (iksiriʔ 'by hand; on the hand'); 36 etymologies"},
                    {"label": "LOC *-kat*", "meaning": "'in, on; among (animates)'", "forms": ["kat"], "source": "Parks GO p.30 (akahkat 'on the dwelling', asaakat 'among the horses')"},
                    {"label": "LOC *-ru* / *-wiru*", "meaning": "'among, in the country of' (tribal and place names)", "forms": ["ru", "wiru"], "source": "Parks GO p.30 (sahiiru 'in Cheyenne country')"},
                    {"label": "PL *-raar-*", "meaning": "plural of body-part and other nouns, before the case suffix", "forms": ["raar"],
                     "source": "Parks GO p.30 (ikstaaririʔ 'with the hands'), p.43 (kiis- + raar- + ... 'bones'); 33 etymologies labelled PL", "note": "same shape as the iterative *raar-* (ITER) and the 3rd-person plural prefixes — Parks's gloss decides (ambiguous cases flagged)"},
                ],
                "walkthrough": lambda d: (
                    f"*{d.W(KIIHAAHIRI)}* '{d.G(KIIHAAHIRI)}' = *kiihaar* 'room' + *hiriʔ* with *r* + *h* → *h* (Rules 14–15); *{d.W(KITAHAAHIRI)}* 'on top' = *kita* + *haar* + *hiriʔ*; "
                    f"*{d.W(RUKSIRI)}* 'ten' = *ruks* + *hiriʔ* (the *h* is lost after *s*, Rule 16); *{d.W(ASKUSIRI)}* 'once'. *{d.W(PICIKAT)}* '{d.G(PICIKAT)}' (BB L15 *pitsikat*). "
                    f"*{d.W(KIRIKUURUKSTU)}* '{d.G(KIRIKUURUKSTU)}' carries *-ru*. The plural: *{d.W(CKARAARU)}* 'clouds' = *icka* + *raar* + *uʔ*; *{d.W(RAKTARIIKAQU)}* "
                    f"'{d.G(RAKTARIIKAQU)}' = *rak* + *raar* + *riika* + *uʔ* with *r* → *t* after *k* (Rule 21); *{d.W(CAAHIKSTAHKUCUU)}* '{d.G(CAAHIKSTAHKUCUU)}' = people + PL + big."),
                "examples": [KIIHAAHIRI, KITAHAAHIRI, AWIIRAHIRI, RUKSIRI, ASKUSIRI, PICIKAT, IRITKAT, WARAAKAT, CKARAARU, KICPIIRAARU, RAKTARIIKAQU, CAAHIKSTAHKUCUU, KIRIKUURUKSTU],
                "bb_notes": lambda d: f"{d.bbq(47, 'Plurality is usually')} — the Blue Book treats plural as a verb-phrase matter (Unit 6), which agrees with Parks: nouns other than body parts have no plural marking (GO p.30).",
                "exercises": ([KITAHAAHIRI, CKARAARU, PICIKAT, RAKTARIIKAQU, KIIHAAHIRI], [AWIIRAHIRI, RUKSIRI, KICPIIRAARU, CAAHIKSTAHKUCUU, IRITKAT]),
            },
        ],
        "review_size": 14,
    },
    # =====================================================================
    {
        "id": 5, "title": "The verb, part 1: mode, person, incorporation",
        "intro": ("Parks: every verb has a modal prefix and a stem; the person prefixes sit between them (GO p.33–35, Tables 7–9). The Blue Book calls "
                  "the prefix block the 'introducer' (L4 p.45–46). This unit adds one prefix at a time to stems from Unit 3, using only the forms Parks cites."),
        "bb_alignment": "BB L4 (verb phrase), L6 (person markers, preverbs), L5 (passive introducers, physical possession) and L8 (nouns in a verb phrase).",
        "lessons": [
            {
                "id": "5.1", "title": "ti- : the third-person indicative frame",
                "objectives": ["Read the dictionary's 3sg indicative (form 2) of known verbs as *ti-* + Ø + stem.", "Recognise the adjustments at the seam."],
                "morphemes": [{"label": "IND *ti-* (3rd person agent, which is unmarked Ø)", "meaning": "indicative mode with a third-person subject: 'he/she/it ...'", "forms": ["ti"],
                               "source": "Parks GO p.34 Table 8; every dictionary form 2 (2186 attested words); BB L4 p.46, L8 p.67 ('Pawnee does not use a letter or root to refer to the third person')"}],
                "walkthrough": lambda d: (
                    f"{d.bbq(46, 'introducer')} (BB). With a consonant-initial stem nothing changes: *{d.F(KIKAK, 2)}* (*ti* + *kikak*; stem-final *k* → *t*, Parks GO p.46), "
                    f"*{d.F(KIIKAA, 2)}*, *{d.F(WIITIK, 2)}*, *{d.F(WARII, 2)}*, *{d.F(RAAH, 2)}*, *{d.F(KAAQAT, 2)}*. With a vowel-initial stem a glottal stop is inserted: "
                    f"*{d.F(AT, 2)}* 'he went'. With *a*-initial stems *i* + *a* contract to *ii* (Rule 7): *{d.F(ARIK, 2)}* 'he is standing' (BB *t'erit*). "
                    f"Short *s*- and *k*-initial position stems lengthen the prefix vowel in Parks's forms: *{d.F(KUS, 2)}* 'he is sitting' (final *s* dropped, Rule 9R), "
                    f"*{d.F(SA, 2)}* 'he is lying'. The 'make' stem *raʔuk* contracts: *{d.F(RAQUK, 2)}* (GO p.46)."),
                "paradigms": [AT, KUS, SA, ARIK, WIITIK, WARII, KIKAK, RAQUK, KIIKAA, RAAH, KAAQAT, KAAKUS],
                "bb_notes": lambda d: f"{d.bbq(67, 'strong vowel')} … (BB L8 p.67, on *ti* with the past marker). BB L6 p.55 *ti•kikat* = Parks *{d.F(KIKAK, 2)}*; BB *ti•ruku'* 'he is making it' = Parks imperfective *{d.F(RAQUK, 3)}* (Lesson 6.1).",
                "extra_practice": lambda d: _stem_to_form(d, [KAAQAT, KAAKUS, KAASA, KAARIK, KITAKUS, HUKAARIK], 2, "3sg indicative (form 2)"),
                "exercises": ([], []),
            },
            {
                "id": "5.2", "title": "ta- + t- 'I', ta- + s- 'you'",
                "objectives": ["Form 1sg and 2sg indicatives from known stems: *ta-* + *t-*/*s-* + stem.", "Learn the junction changes: *t*+*r* → *h*, *t*+*w* → *tp*, *t*+*s* → *c*, *s*+*r* → *st*, *ta*+*t*+*a* → *taat*."],
                "morphemes": [
                    {"label": "IND *ta-* (1st/2nd person)", "meaning": "indicative with a speech-act-participant subject", "forms": ["ta"], "source": "Parks GO p.34 Table 8; 1602 dictionary form-1 words; BB L4 p.46 'ta ... I'm telling you'"},
                    {"label": "1.A *t-* 'I'", "meaning": "first-person agent", "forms": ["t"], "source": "Parks GO p.35 Table 9; BB L6 p.58 '+ t first person'"},
                    {"label": "2.A *s-* 'you'", "meaning": "second-person agent", "forms": ["s"], "source": "Parks GO p.35 Table 9; App.1 2sg cells (69 forms); BB L6 p.58 '+ s second person'"},
                ],
                "walkthrough": lambda d: (
                    f"Parks's own example (GO p.38): *{d.A('to go', IND, '1sg')}* 'I went' < *ta-* + *t-* + *at*: *a* + *a* become long *aa* (Rule 5). The dictionary form 1 of each entry "
                    f"is this 1sg: *{d.F(KIKAK, 1)}* (*tat* + *kikak*), *{d.F(KIIKAA, 1)}*, *{d.F(KAAQAT, 1)}*, *{d.F(KUS, 1)}*. At the seam: *t* + *s* → *c* "
                    f"(*{d.F(SA, 1)}* 'I am lying', Rule 17, *s* → *c* after a consonant); *t* + *w* → *tp* (*{d.F(WIITIK, 1)}*, *{d.F(WARII, 1)}*; the *w* → *p* change BB states on p.41); "
                    f"*t* + *r* → *h* (*{d.F(RAAH, 1)}* 'I have it', *{d.F(RAQUK, 1)}* 'I made it'; Rules 13–15). Second person replaces *t-* with *s-*: App.1 *{d.A('to go', IND, '2sg')}* "
                    f"'you went', *{d.A('to drink it', IND, '2sg')}*, *{d.A('to have it', IND, '2sg')}* (*s* + *r* → *st*, Rule 21), *{d.A('to be good', IND, '2sg')}*."),
                "paradigms": [KIKAK, KIIKAA, KAAQAT, KUS, SA, WIITIK, WARII, RAAH, RAQUK],
                "app1": [("to go", [IND], ["1sg", "2sg", "3sg"]), ("to drink it", [IND], ["1sg", "2sg", "3sg"]), ("to have it", [IND], ["1sg", "2sg", "3sg"])],
                "bb_notes": lambda d: (f"BB L4 p.46: *tah•ra* 'I have it', *tas•ta* 'you have it', *ti ra* 'he has it'. Parks App.1 'to have it': *{d.A('to have it', IND, '1sg')}*, "
                                       f"*{d.A('to have it', IND, '2sg')}*, *{d.A('to have it', IND, '3sg')}*. ⚠ BB keeps *r* after *h* (*tahra*) where Parks writes *tahaa* (the *r* is absorbed, Rule 15); "
                                       f"BB *tas•ta* agrees with Parks *{d.A('to have it', IND, '2sg')}* apart from vowel length. BB L6 p.58 *tat•kikat* 'I am crying' = Parks *{d.F(KIKAK, 1)}*."),
                "extra_practice": lambda d: _derive(d, [KIKAK, WARII, KUS, RAQUK, KAAQAT], 2, 1, "3sg indicative", "1sg indicative"),
                "exercises": ([], []),
            },
            {
                "id": "5.3", "title": "ku- 'me', a- 'you' — the patient prefixes",
                "objectives": ["Recognise verbs whose subject is grammatically a patient (Parks's 'passive' class, VP).", "Read *ti-* + *ku-* 'it ... me' and *ta-* + *a-* 'it ... you'."],
                "morphemes": [{"label": "1.P *ku-* 'me, us'", "meaning": "first-person patient", "forms": ["ku"], "source": "Parks GO p.35 Table 9; dictionary form 1 of VP verbs (e.g. tikuʔaa); BB L5 p.51 'passive introducers', L6 p.58 '+ ku'"},
                              {"label": "2.P *a-* 'you'", "meaning": "second-person patient", "forms": ["a"], "source": "Parks GO p.35 Table 9; App.1 'to be sick' 2sg; BB L6 p.58 '+ a second person to you'"}],
                "walkthrough": lambda d: (
                    f"Parks: passive verbs 'describe actions that befall people ... what is interpretively a subject is grammatically a patient' (GO p.32). So 'I became' is "
                    f"*{d.F(AAR_BECOME, 1)}* = *ti* + *ku* 'me' + *aar*, and 'I died' is *{d.F(KUUT, 1)}*; 'I forgot' *{d.F(ACIKSURAHAC, 1)}*, 'I am thirsty' *{d.F(ACIKSTAAHIIS, 1)}* "
                    f"(*ku* + *aciks*: the *u* dominates the following vowel — Rule 6; BB L5 p.50: {d.bb_quote(50, 'When i follows u')}). App.1 'to be sick': *{d.A('to be sick', IND, '1sg')}* 'I am sick', "
                    f"*{d.A('to be sick', IND, '2sg')}* 'you are sick' (*ta* + *a*), *{d.A('to be sick', IND, '3sg')}*."),
                "paradigms": [AAR_BECOME, KUUT, HURAHAC, KAAHIKUUT, ACIKSURAHAC, ACIKSTAAHIIS, KISUQAAR, PAHITAAR],
                "app1": [("to be sick", [IND], ["1sg", "2sg", "3sg", "1pl_excl", "2pl", "3pl"])],
                "bb_notes": lambda d: f"{d.bbq(51, 'mode + phys. poss.')} (BB L5, the possessive frame); {d.bbq(53, TIKUKS)} ('my hand has been hurt' = *ti* + *ku* + *iks* + ...; the dictionary has no entry for this exact verb — BB-attested only). BB L6 p.58 *tiku'tskipi* 'I am sleepy', *ta'tskipi* 'you are sleepy'.",
                "extra_practice": lambda d: _derive(d, [KUUT, AAR_BECOME, KAAHIKUUT, KISUQAAR, PAHITAAR], 2, 1, "3sg indicative", "1sg (patient-marked)"),
                "exercises": ([], []),
            },
            {
                "id": "5.4", "title": "putting a body part inside the verb; ri- physical possession",
                "objectives": ["Combine the body roots of Unit 2 with the position and locative roots of Unit 3 inside one verb.", "Recognise the possession prefix *ri-* (and *uur-*) in the Blue Book's body dialogues."],
                "morphemes": [{"label": "Incorporated noun (slot 25)", "meaning": "body parts, natural phenomena, foods and cultural products are placed before the stem and drop their *-uʔ*", "forms": [],
                               "source": "Parks GO p.43; Table 7 slot 25; BB L8 p.67–68 'Nouns in a verb phrase'"},
                              {"label": "PHY.POSS *ri-* and P.POSS *uur-*", "meaning": "the subject physically possesses the noun", "forms": ["ri", "uur"],
                               "source": "Parks GO p.36 (taruuraarit 'he has it (standing)'; tatiriiriikstahka); BB L5 p.51"}],
                "walkthrough": lambda d: (
                    f"Parks GO p.43: 'An incorporated noun drops the nominal suffix of its independent form'. So *iks-* 'hand' + *kaa* 'be inside' = *{d.W(IKSKAA)}* "
                    f"'{d.G(IKSKAA)}' (3sg *{d.F(IKSKAA, 2)}*, 1sg *{d.F(IKSKAA, 1)}*); *icka-* + *kaa* = *{d.W(ICKAKAA)}* '{d.G(ICKAKAA)}' (3sg *{d.F(ICKAKAA, 2)}*); *iks* + *ta* 'be hanging' = "
                    f"*{d.W(IKSTA)}* '{d.G(IKSTA)}'; *kiis* + *ta* = *{d.W(KIISTA)}* '{d.G(KIISTA)}'; *haas* + *ta* = *{d.W(HAASTA)}*; *iks* + *raah* = *{d.W(IKSTAAH)}* (Rule 21), 3sg *{d.F(IKSTAAH, 2)}*. "
                    f"*as* + *wiitik* = *{d.W(ASPIITIK)}* '{d.G(ASPIITIK)}' with *w* → *p* after *s*. Possession: Parks's *taruuraarit* 'he has it (something standing)' is "
                    f"*ti-* + *a-* + *ri-* + *uur-* + *arik* (GO p.36); the Blue Book frame is {d.bbq(51, 'mode + phys. poss.')}."),
                "examples": [IKSKAA, ICKAKAA, IKSTA, KIISTA, HAASTA, KIICKAA, ASPIITIK, ASKAWAT, HAAKARIIR, IKSTAAH],
                "paradigms": [IKSKAA, ICKAKAA, IKSTAAH],
                "bb_notes": lambda d: ("BB L5 p.50: *Ti rit•paks•ku* 'Here is my head (sitting)', *Ti rit•kirik•ta* 'Here is my eye (hanging)' — BB analyses these as *ti* + *ri* + *t* + *paks* + *ku*. "
                                       "⚠ The dictionary has no headwords *paksku*/*kirikta*; the pattern is attested in Parks only through the general statement (GO p.43) and in the parallel "
                                       f"dictionary words *{d.W(IKSTA)}*, *{d.W(KIISTA)}*, *{d.W(IKSKAA)}*. Treat the BB sentences as BB-attested, not dictionary-attested."),
                "exercises": ([IKSKAA, ICKAKAA, KIICKAA, ASPIITIK, IKSTAAH], [HAASTA, KIISTA, ASKAWAT, IKSTA, HAAKARIIR]),
            },
            {
                "id": "5.5", "title": "the preverbs ut- and uur-",
                "objectives": ["Recognise discontinuous stems: a preverb among the prefixes plus a stem base (Parks GO p.31).", "Contrast pairs that differ only in the preverb."],
                "morphemes": [{"label": "PREV *ut-*", "meaning": "part of the stem (no meaning of its own); also benefactive 'for, to'", "forms": ["ut"], "source": "Parks GO p.31, p.37; 345 dictionary entries; BB L6 p.56, L10 p.75"},
                              {"label": "PREV *uur-*", "meaning": "part of the stem; also patient possession", "forms": ["uur"], "source": "Parks GO p.31, p.36; 180 dictionary entries; BB L10 p.75 '+ur'"},
                              {"label": "PREV *ir-* / *a-*", "meaning": "part of the stem (e.g. 'come'); first/second person *ir-*, third person *a-*", "forms": ["ir"], "source": "Parks GO p.31–32 (a (ir-...) 'to come'); 200 dictionary entries"}],
                "walkthrough": lambda d: (
                    f"Same base, different stem: *{d.W(AAR_BECOME)}* '{d.G(AAR_BECOME)}' has 3sg *{d.F(AAR_BECOME, 2)}*; *{d.W(AAR_DO)}* '{d.G(AAR_DO)}' with *ut-* has 3sg *{d.F(AAR_DO, 2)}* "
                    f"(*ti* + *ut* → *tuut*: the *u* dominates, Rules 1R/6; BB L10 p.75 '{d.bb_quote(75, 'i +u becomes u')}'). *{d.W(RAAH)}* 'have' 3sg *{d.F(RAAH, 2)}*; *{d.W(RAAH_UUR)}* "
                    f"'{d.G(RAAH_UUR)}' with *uur-* 3sg *{d.F(RAAH_UUR, 2)}*. *{d.W(AWUH)}* '{d.G(AWUH)}' 3sg *{d.F(AWUH, 2)}* versus *{d.W(AWUH_UUR)}* '{d.G(AWUH_UUR)}' 3sg *{d.F(AWUH_UUR, 2)}*. "
                    f"*{d.W(IIRIK)}* 'see' is always with *ut-*: 3sg *{d.F(IIRIK, 2)}*, 1sg *{d.F(IIRIK, 1)}* (BB L14 *Tatut•erit* 'I saw it'). *{d.W(HIIR_GOOD)}* 'be good' is always with *uur-*: "
                    f"3sg *{d.F(HIIR_GOOD, 2)}*, 1sg *{d.F(HIIR_GOOD, 1)}* (App.1). Three homonymous 'kaakus' stems differ only by preverb: *{d.F(KAAKUS, 2)}* '{d.G(KAAKUS)}', "
                    f"*{d.F(KAAKUS_UT, 2)}* '{d.G(KAAKUS_UT)}', *{d.F(KAAKUS_UUR, 2)}* '{d.G(KAAKUS_UUR)}'."),
                "paradigms": [AAR_BECOME, AAR_DO, RAAH, RAAH_UUR, AWUH, AWUH_UUR, IIRIK, HIIR_GOOD, KAAKUS, KAAKUS_UT, KAAKUS_UUR],
                "bb_notes": lambda d: f"{d.bbq(56, 'ti•ari')} vs *tut•ari'* 'he's making it or doing it' (BB L6 p.56) = Parks *{d.F(AAR_BECOME, 2)}* / *{d.F(AAR_DO, 2)}* (⚠ BB writes the imperfective *-i'*; Parks's perfective 3sg is *{d.F(AAR_DO, 2)}*, imperfective *{d.F(AAR_DO, 3)}*). BB L10 p.75 *tuh•ra'* 'he is using it' = Parks *{d.F(RAAH_UUR, 2)}*.",
                "extra_practice": lambda d: _derive(d, [AAR_DO, RAAH_UUR, IIRIK, HIIR_GOOD, KAAKUS_UT], 2, 1, "3sg indicative (with preverb)", "1sg indicative"),
                "exercises": ([], []),
            },
        ],
        "review_size": 12,
        "review_extra": lambda d: ("**Unit 5 cumulative paradigm drill.** Appendix 1 *to drink it*, indicative: " +
                                   ", ".join(f"{p} *{d.A('to drink it', IND, p)}*" for p in ["1sg", "2sg", "3sg"]) +
                                   f" (App.1 p.{d.A_page('to drink it')}). Identify mode prefix, person prefix and stem in each."),
    },
    # =====================================================================
    {
        "id": 6, "title": "The verb, part 2: aspect, number, time, negation",
        "intro": "Suffixes mark aspect and subordination (Parks GO p.44–48, Tables 16–17); number is marked by the proclitic *si-* and the prefixes *rak-*, *raar-*, *ir-*, *ak-* (GO p.35–36); the aorist/jussive *uks-* marks past time and commands (GO p.38).",
        "bb_alignment": "BB L5 (completed/incomplete action, commands, irregular roots), L4 (plurals), L8 (past tense), L15 (verb-final k), L19 (future), L1/L4 (indicators ka/kaki).",
        "lessons": [
            {
                "id": "6.1", "title": "the imperfective -huʔ (-:hus)",
                "objectives": ["Form 'is ...-ing' from known verbs (dictionary form 3).", "See why a stem-final *k* appears only before a suffix."],
                "morphemes": [{"label": "IMPF *-huʔ* / *-:hus*", "meaning": "imperfective 'uncompleted, in progress'; lengthens the stem-final vowel; final *s* dropped word-finally", "forms": ["huʔ", "hus"],
                               "source": "Parks GO p.46–47, Table 17; 1255 dictionary form-3 words; BB L5 p.52–53"}],
                "walkthrough": lambda d: (
                    f"Parks GO p.47: *tikacaakuʔ* 'he is cutting it' vs *tikacat* 'he cut it'. In the dictionary: *{d.F(KIKAK, 2)}* 'he cried' → *{d.F(KIKAK, 3)}* 'he is crying' "
                    f"(the stem-final *k* of *kikak* surfaces before the suffix, and *huʔ* after *k* appears as *-uʔ* with the *h* lost, Rule 16); *{d.F(RAQUK, 2)}* → *{d.F(RAQUK, 3)}*; "
                    f"*{d.F(KIIKAA, 2)}* → *{d.F(KIIKAA, 3)}* (Parks GO p.47 cites this pair); *{d.F(RAAH, 2)}* → *{d.F(RAAH, 3)}*; *{d.F(WARII, 2)}* → *{d.F(WARII, 3)}*; *{d.F(WIITIK, 2)}* → *{d.F(WIITIK, 3)}*; "
                    f"*{d.F(SA, 2)}* → *{d.F(SA, 3)}*. Verbs of class 1-i and 2-i take *-iʔ* instead: *{d.F(ARIK, 2)}* → *{d.F(ARIK, 3)}*, *{d.F(AAR_BECOME, 2)}* → *{d.F(AAR_BECOME, 3)}*. "
                    f"'Go' is suppletive in the imperfective: *{d.F(AT, 2)}* → *{d.F(AT, 3)}*, *{d.F(KAAQAT, 2)}* → *{d.F(KAAQAT, 3)}*."),
                "paradigms": [KIKAK, RAQUK, KIIKAA, RAAH, WARII, WIITIK, SA, ARIK, AAR_BECOME, AT, KAAQAT, KUUT],
                "bb_notes": lambda d: (f"BB L5 p.52–53: {d.bb_quote(53, TIKUKS)} (perfect) vs *Tiku'ks•taari'* 'My hand is hurting' (imperfect). BB L15 p.96–97: "
                                       f"{d.bb_quote(97, 'drop off')} — the same fact Parks states for stem-final *k* (GO p.46). ⚠ BB writes the imperfective as *-u'*/*-us*; Parks as *-huʔ*/*-hus*: the *h* is lost after a consonant (Rule 16)."),
                "extra_practice": lambda d: _derive(d, [KIKAK, KIIKAA, WARII, WIITIK, RAAH], 2, 3, "3sg perfective", "3sg imperfective"),
                "exercises": ([], []),
            },
            {
                "id": "6.2", "title": "the intentive -his + -ta 'is going to'",
                "objectives": ["Form the intentive (dictionary form 5) and recognise its shapes *-ista*, *-sta*, *-ksta*."],
                "morphemes": [{"label": "INT *-ta* after PERF *-his* (→ *-ista*, after *Vk*: *-ksta*; after IMPF *-hus*: *-usta*)", "meaning": "'is going to ...'", "forms": ["his", "ta"],
                               "source": "Parks GO p.46–47, Table 17; Rule 3R (-his reduction); 2142 dictionary form-5 words; BB L19 p.108"}],
                "walkthrough": lambda d: (
                    f"Parks GO p.46: *tikikat* 'he cried' vs *tikikaksta* 'he is going to cry' — the perfective *-his* appears only when *-ta* follows, and after a stem-final *k* it "
                    f"reduces to *-s* (Rule 3R): dictionary *{d.F(KIKAK, 5)}*, *{d.F(WIITIK, 5)}*, *{d.F(RAQUK, 5)}*. After a vowel: *{d.F(SA, 5)}*, *{d.F(KIIKAA, 5)}*, *{d.F(RAAH, 5)}*, "
                    f"*{d.F(ARIK, 5)}*. With the imperfective inside: *{d.F(WARII, 5)}* (= *warii* + *hus* + *ta*). Descriptive verbs add *-uk* first: *{d.F(PAHAAT, 5)}* "
                    f"(Parks GO p.49 cites exactly *tipahaatuksta* 'it is going to be red'). The Blue Book: {d.bbq(108, 'suffix +ta')}."),
                "paradigms": [KIKAK, WIITIK, RAQUK, SA, KIIKAA, RAAH, ARIK, WARII, KUS, AT, PAHAAT, AAR_DO],
                "bb_notes": lambda d: f"BB L19 p.108 *Tatutari'sta* 'I'll do it' = Parks *{d.F(AAR_DO, 5)}*-type build (1sg: *ta* + *t* + *ut* + *aar* + *his* + *ta*); the dictionary gives the 3sg *{d.F(AAR_DO, 5)}*.",
                "extra_practice": lambda d: _derive(d, [KIKAK, SA, KIIKAA, RAAH, WARII], 2, 5, "3sg perfective", "3sg intentive"),
                "exercises": ([], []),
            },
            {
                "id": "6.3", "title": "two and many: si-, rak-, raar-, ir-, and the irregular stems of 'go'",
                "objectives": ["Read the full indicative paradigm of 'to go' and 'to drink it' (Appendix 1).", "Recognise *si-* (dual), *rak-* (1st/2nd plural), *raar-*/*ir-* (3rd plural) and the suppletive stems *at / war / wuu*."],
                "morphemes": [{"label": "DU *si-*", "meaning": "dual, before the mode prefix", "forms": ["si"], "source": "Parks GO p.35; App.1 dual cells (180 forms); BB L4 p.47 'Si tahrarra'"},
                              {"label": "PL *rak-* (1st/2nd agent)", "meaning": "'we (excl.), you (pl.)'", "forms": ["rak", "raak"], "source": "Parks GO p.35 Table 10; App.1; BB L4 p.47 '+ rak +'"},
                              {"label": "1.PL.IN *a-* + *rak-*", "meaning": "'we (inclusive)'", "forms": ["a"], "source": "Parks GO p.35 Table 9; App.1 1pl_incl cells"},
                              {"label": "1.DU.IN *acir-*", "meaning": "'you and I'", "forms": ["acir"], "source": "Parks GO p.35 Table 9; App.1 (BB L4 p.47 writes *+ atsir +*)"},
                              {"label": "3.PL *ir-* (collective) / *raar-* (individuative) / suffix *-aahuʔ*", "meaning": "'they'", "forms": ["ir", "raar"], "source": "Parks GO p.35–36 Table 10 (tiiraspaatasit / tiraaraspaatasit); App.1 3pl cells; BB L4 p.47 '+ it + for they'"}],
                "walkthrough": lambda d: (
                    f"Singular is unmarked (GO p.35). Dual adds *si-* in front of everything: *{d.A('to go', IND, '1sg')}* 'I went' → *{d.A('to go', IND, '1du_excl')}* 'we two went' — and the stem "
                    f"of 'go' changes to *war* (surfacing as *pa* after *t*). Plural first/second person adds *rak-*: *{d.A('to go', IND, '1pl_excl')}*, *{d.A('to go', IND, '2pl')}*, with the plural "
                    f"stem *wuu* (*puuʔ*). Third plural: *{d.A('to go', IND, '3pl')}*. The regular verb 'drink' shows the prefixes without stem change: *{d.A('to drink it', IND, '1du_excl')}*, "
                    f"*{d.A('to drink it', IND, '1pl_excl')}*, *{d.A('to drink it', IND, '2pl')}*, *{d.A('to drink it', IND, '3pl')}*. Appendix 2 lists the suppletive roots "
                    f"(irregular_verb_roots): *at* / *war* / *at~wuu* 'go'; *kus* / *kus* / *wihak* 'be sitting'; *aah* / *aah* / *hurii-waa* 'be around'. BB: {d.bbq(54, 'roots for go')}."),
                "app1": [("to go", [IND], PERSONS), ("to drink it", [IND], PERSONS)],
                "bb_notes": lambda d: (f"BB L4 p.47 verb set 'Who has them?': *Si tahrarra* 'We (2) have them', *Tahraktarra* 'We (3+) have them', *Tihrarra* 'They (3+) have them' (BB analysis *ti + it + rarra*). "
                                       f"Parks App.1 'to have it' (class 3) uses *si-* for all non-singular persons: dual *{d.A('to have it', IND, '1du_excl')}*, plural *{d.A('to have it', IND, '1pl_excl')}* ⚠ — "
                                       f"BB's *Tahraktarra* with *rak-* is not what Appendix 1 shows for this verb; both are given, neither is altered. BB L5 p.54: *Sitat•pa* 'we (2) have gone', *Tahra•pu'* 'we (3+) have gone' = App.1 *{d.A('to go', IND, '1du_excl')}*, *{d.A('to go', IND, '1pl_excl')}*."),
                "extra_practice": lambda d: _cells(d, "to drink it", IND, ["1du_excl", "2du", "3du", "1pl_excl", "2pl", "3pl"]),
                "exercises": ([], []),
            },
            {
                "id": "6.4", "title": "uks-: past time and commands",
                "objectives": ["Recognise the aorist/jussive prefix *uks-* in Parks's examples and the Blue Book's past and command forms."],
                "morphemes": [{"label": "AOR/JUSS *uks-*", "meaning": "optional past tense; with the contingent mode, a command", "forms": ["uks"],
                               "source": "Parks GO p.38 (tatuksat 'I went'; sukskirikaʔaa 'wake up!'); BB L5 p.53, L8 p.66–67, L13 p.89", "note": "⚠ no dictionary paradigm form contains uks-; Appendix 1 has no aorist mode — attested only in Parks's grammar examples and the Blue Book"}],
                "walkthrough": lambda d: (
                    f"Parks GO p.38 contrasts *{d.A('to go', IND, '1sg')}* 'I went' with *tatuksat* 'I went' < *ta-* + *t-* + *uks-* AOR + *at*; the Blue Book builds the same word: "
                    f"BB L13 p.89 *Tatuks•at* 'I went', *Tasu'ks•at* 'You went', *Tuks•at* 'He went'. {d.bbq(66, '+uks, which follows')} … (BB L8). With a third person the mode vowel disappears: "
                    f"{d.bbq(67, 'strong vowel')}, hence BB *Tuks•kaku'* 'He was in the house' (Parks's rule 1R/6: *ti* + *u...* → *tu...*). Commands: contingent *i-* + *s-* + *uks-* + stem (GO p.38, "
                    f"*sukskirikaʔaa* 'wake up!'); BB L5 p.53 *Suks•paku'* 'Say it!', *Sisuks•paku'* (two hearers), *Suksta•paku'* (three or more; *rak-* → *ta* after *s*)."),
                "bb_notes": lambda d: f"{d.bbq(53, 'command marker')} (BB L5). Parks writes the command with the contingent mode prefix *i-* (GO p.38); BB's forms begin directly with *s-* — the *i-* is not written ⚠.",
                "exercises": ([], []),
                "extra_practice": lambda d: ("Break down the Blue Book forms using Parks's slots (mode, person, *uks-*, stem). Answers follow BB's own analyses (L8 p.67; L5 p.53).\n\n"
                                             "C1. *Tasuks•atku* 'You listened' (BB p.66) → ______\nC2. *Tuks•kaku'* 'He was in the house' (BB p.67) → ______\nC3. *Suks•paku'* 'Say it!' (BB p.53) → ______\n\n"
                                             "Answers: C1 *ta* + *s* + *uks* + *atku* (BB p.66–67); C2 *ti* + Ø + *uks* + *ka* + *ku'* (BB p.67: 'mode person past root root'); "
                                             "C3 *s* + *uks* + *wak* + *u'* (BB p.53: 'you + do it + say it + completed'; *w* → *p* after *s*). These three words are BB-attested; the dictionary has no entries for them."),
            },
            {
                "id": "6.5", "title": "saying no and asking: kaaki-/kaakaa- and ra-",
                "objectives": ["Form negative indicatives with *kaakaa-* (1st/2nd) and *kaaki-* (3rd).", "Recognise the absolutive *ra-* used in questions."],
                "morphemes": [{"label": "NEG.IND *kaakaa-* / *kaaki-*", "meaning": "negative statements", "forms": ["kaakaa", "kaaki"], "source": "Parks GO p.34 Table 8; App.1 negative cells (73 forms); BB L1 p.32 'Kaki', L4 p.46 'Kakah•ra'"},
                              {"label": "ABS *ra-*", "meaning": "absolutive: questions, narration", "forms": ["ra"], "source": "Parks GO p.34 Table 8; App.1 absolutive cells; BB L4 p.46 'ra + s + ra (that) you have it', L13 p.89 'Take ra'at?'"}],
                "walkthrough": lambda d: (
                    f"App.1 'to go': *{d.A('to go', IND, '1sg')}* 'I went' → *{d.A('to go', NEG, '1sg')}* 'I did not go'; *{d.A('to go', IND, '3sg')}* → *{d.A('to go', NEG, '3sg')}*. "
                    f"'Drink': *{d.A('to drink it', NEG, '1sg')}*, *{d.A('to drink it', NEG, '2sg')}*, *{d.A('to drink it', NEG, '3sg')}*. Absolutive (questions): *{d.A('to go', ABS, '1sg')}*, "
                    f"*{d.A('to go', ABS, '2sg')}*, *{d.A('to go', ABS, '3sg')}*; 'have': *{d.A('to have it', ABS, '2sg')}* — the Blue Book's *Kirike ras•ta?* 'What do you have?' (L4 title)."),
                "app1": [("to go", [IND, NEG, ABS], ["1sg", "2sg", "3sg", "3pl"]), ("to drink it", [NEG, ABS], ["1sg", "2sg", "3sg"])],
                "bb_notes": lambda d: f"BB L1 p.32 *Kaki kisu'* 'It is not a bone'; BB L4 p.46 *Kakah•ra* 'I don't have it' vs Parks App.1 *{d.A('to have it', NEG, '1sg')}* ⚠ (BB keeps *r*, Parks has *haa*; same difference as *tahra*/*tahaa* in Lesson 5.2).",
                "extra_practice": lambda d: _cells(d, "to go", NEG, ["2sg", "3sg", "1du_excl", "1pl_excl", "3pl"]),
                "exercises": ([], []),
            },
        ],
        "review_size": 10,
    },
    # =====================================================================
    {
        "id": 7, "title": "Subordinate forms, reflexives, derivation, descriptive verbs",
        "intro": "The remaining pieces needed to read any dictionary entry: the gerundial (form 4) with its class-dependent ending, the reflexive proclitic, the causative and inchoative suffixes, and the descriptive-verb existential *-uk*.",
        "bb_alignment": "BB L13 (making verb phrases into nouns), L14 (reflexive marker), L2/L3 (descriptive 'ti pahaat', 'ti rihu').",
        "lessons": [
            {
                "id": "7.1", "title": "irii- ra- ... : the gerundial and the verb classes",
                "objectives": ["Read dictionary form 4 as *irii-* 'the one' + *ra-* ABS + stem + subordinating suffix.", "Use the ending to identify Parks's verb class: class 1 *-a*, class 2 *-i*, class 3 final-syllable change, class 4 Ø, descriptive *-u*, locative *-wi*."],
                "morphemes": [{"label": "ABS/GER *ra-*", "meaning": "subordinate mode: 'the one who..., when...'", "forms": ["ra"], "source": "Parks GO p.34 Table 8; 2190 dictionary form-4 words"},
                              {"label": "*irii-* 'the one; what, where'", "meaning": "deictic proclitic opening the dictionary's gerundial forms", "forms": ["irii"], "source": "Parks GO p.42 (irii- 'what, where'; iriiʔahaarasika 'where he cooked'); BB L13 p.88 'hiri'"},
                              {"label": "SUB suffixes by class: 1 *-a*, 2 *-i*, 3 final-syllable change, 4 Ø, D *-u*, L *-wi*", "meaning": "subordinate perfective marker", "forms": ["a", "i", "u", "wi"], "source": "Parks GO p.46 Table 17; p.50 (-wi); morpheme_inventory slot 28"}],
                "walkthrough": lambda d: (
                    f"Class 1 (*-a*): *{d.W(AT)}* → *{d.F(AT, 4)}*; *{d.W(KAAQAT)}* → *{d.F(KAAQAT, 4)}*; *{d.W(RAAH)}* → *{d.F(RAAH, 4)}*. Class 4 (Ø): *{d.W(WIITIK)}* → *{d.F(WIITIK, 4)}*, "
                    f"*{d.W(KIKAK)}* → *{d.F(KIKAK, 4)}*, *{d.W(KUS)}* → *{d.F(KUS, 4)}*, *{d.W(SA)}* → *{d.F(SA, 4)}*. Class 2-i (*-i*): *{d.W(ARIK)}* → *{d.F(ARIK, 4)}*, *{d.W(KUUT)}* → *{d.F(KUUT, 4)}*. "
                    f"Class 3 (final syllable changes): *{d.W(RAQUK)}* → *{d.F(RAQUK, 4)}*. Class 1-i: *{d.W(AAR_BECOME)}* → *{d.F(AAR_BECOME, 4)}*. Descriptive (*-u*): *{d.W(PAHAAT)}* → *{d.F(PAHAAT, 4)}* "
                    f"(Parks GO p.49 cites *iriirapahaattu* 'the one that is red'). Locative (*-wi*): *{d.W(KAA)}* → *{d.F(KAA, 4)}*, *{d.W(IKSKAA)}* → *{d.F(IKSKAA, 4)}*. App.1 gerundials: "
                    f"*{d.A('to go', GER, '3sg')}*, *{d.A('to drink it', GER, '3sg')}*, *{d.A('to be good', GER, '3sg')}*."),
                "paradigms": [AT, KAAQAT, RAAH, WIITIK, KIKAK, KUS, SA, ARIK, KUUT, RAQUK, AAR_BECOME, PAHAAT, KAA, IKSKAA],
                "bb_notes": lambda d: f"BB L13 p.88–89: {d.bbq(89, 'hiri .ra wa')}; 'hiri ratukstak•kitkeu'' 'where we used to live'. ⚠ BB *hiri* corresponds to Parks *irii-* (GO p.42) — initial *h* and vowel length differ; BB *ra* = Parks *ra-* ABS.",
                "extra_practice": lambda d: _derive(d, [AT, WIITIK, ARIK, RAQUK, PAHAAT], 2, 4, "3sg indicative", "gerundial (form 4), naming the class"),
                "exercises": ([], []),
            },
            {
                "id": "7.2", "title": "witi- : doing it to oneself",
                "objectives": ["Recognise the reflexive/reciprocal proclitic *witi-* in dictionary VR forms and in BB L14."],
                "morphemes": [{"label": "REFL *witi-*", "meaning": "reflexive / reciprocal: subject = object", "forms": ["witi"], "source": "Parks GO p.40 (wititaatacikstariku 'I keep my thoughts to myself'); dictionary VR forms; BB L14 p.93 'Witi tatut•erit' 'I saw myself'"}],
                "walkthrough": lambda d: (
                    f"Reflexive verbs (VR) carry *witi-* before the mode prefix in every dictionary form: *{d.W(ACIKSTAQUK)}* '{d.G(ACIKSTAQUK)}' → 3sg *{d.F(ACIKSTAQUK, 2)}*, 1sg *{d.F(ACIKSTAQUK, 1)}*; "
                    f"*{d.W(ACIKSTIIHAC)}* → *{d.F(ACIKSTIIHAC, 2)}*. Verbs that are both transitive and reflexive list both forms: *{d.W(ASKAWAT)}* '{d.G(ASKAWAT)}' 3sg *{d.F(ASKAWAT, 2)}*; "
                    f"*{d.W(ASUUKTIK)}* '{d.G(ASUUKTIK)}' 3sg *{d.F(ASUUKTIK, 2)}*. {d.bbq(92, 'Witi tatut', span=2)} (BB L14)."),
                "paradigms": [ACIKSTAQUK, ACIKSTIIHAC, ASKAWAT, ASUUKTIK],
                "exercises": ([], []),
                "extra_practice": lambda d: _derive(d, [ACIKSTAQUK, ACIKSTIIHAC, ASUUKTIK], 2, 1, "3sg reflexive", "1sg reflexive"),
            },
            {
                "id": "7.3", "title": "making new verbs: -raʔuk / -ik / -rik / -wuh (cause), -aar / -itik (become), -waa (distributive)",
                "objectives": ["Derive causatives and inchoatives from known roots with Parks's stem-template suffixes (GO p.44 Table 15; p.50)."],
                "morphemes": [{"label": "CAUS *-raʔuk*", "meaning": "'cause to be, make'", "forms": ["raʔuk"], "source": "Parks GO p.44 Table 15 slot 8; 102 etymologies"},
                              {"label": "CAUS *-ik*, *-rik*, *-k*, *-wuh*", "meaning": "'cause to; put'", "forms": ["ik", "rik", "k", "wuh"], "source": "Parks GO p.44 Table 15; 40 / 29 / 28 / 48 etymologies"},
                              {"label": "INCH *-aar* 'become', *-itik*", "meaning": "inchoative 'become, get; begin'", "forms": ["aar", "itik", "iitik"], "source": "Parks GO p.48, p.50 (table of -aar forms); 56 / 29 etymologies"},
                              {"label": "DIST *-waa*", "meaning": "distributive 'here and there, several'", "forms": ["waa"], "source": "Parks abbreviations (dist.); 87 etymologies"}],
                "walkthrough": lambda d: (
                    f"*kaatiit* 'black' + *raʔuk* → *{d.W(KATIIHAQUK)}* '{d.G(KATIIHAQUK)}': *t* + *r* → *hr* → *h* (Rules 13–15), 3sg *{d.F(KATIIHAQUK, 2)}*. *icka* 'face, point' + *raʔuk* → "
                    f"*{d.W(ICKARAQUK)}* '{d.G(ICKARAQUK)}'; *akaar* + *raʔuk* → *{d.W(AKARAQUK)}* '{d.G(AKARAQUK)}' (*rr* → *r*, Rule 20). *kaas* 'leg; break' + *ik* → *{d.W(KAASIK)}* '{d.G(KAASIK)}'; "
                    f"*hiir* (uur...) + *ik* → *{d.W(HIIRIK)}* '{d.G(HIIRIK)}'. *kiikaa* + *rik* → *{d.W(KIKAARIK)}* '{d.G(KIKAARIK)}'. *kiic* + *kaa* + *wuh* → *{d.W(KIICKAAWUH)}* '{d.G(KIICKAAWUH)}'. "
                    f"Inchoatives: *kic* + *aar* → *{d.W(KICAAR)}* '{d.G(KICAAR)}' (3sg *{d.F(KICAAR, 2)}*); *{d.W(KIRIKAQAAR)}* '{d.G(KIRIKAQAAR)}'; *{d.W(KITUUQAAR)}*; *{d.W(RAAHIIRIITIK)}* "
                    f"'{d.G(RAAHIIRIITIK)}'. Distributive: *{d.W(RAAHIWAAR)}* '{d.G(RAAHIWAAR)}' = *raa* + *hiir* + *waa*; *{d.W(UUSPAA)}* = *uus* + *waa* (*w* → *p* after *s*)."),
                "examples": [KATIIHAQUK, ICKARAQUK, AKARAQUK, KITUHAQUK, KAASIK, HIIRIK, RAAHIIRIK, KIKAARIK, KIICKAAWUH, KICAAR, KIRIKAQAAR, KITUUQAAR, AWIQAAR, RAAHIIRIITIK, PIIRIITIK, IKSIITIK, RAAHIWAAR, UUSPAA, KATAWAARIK],
                "paradigms": [KATIIHAQUK, KAASIK, KICAAR, KIRIKAQAAR],
                "exercises": ([KATIIHAQUK, AKARAQUK, KAASIK, KICAAR, UUSPAA], [ICKARAQUK, KIKAARIK, KIICKAAWUH, KIRIKAQAAR, RAAHIWAAR]),
            },
            {
                "id": "7.4", "title": "descriptive verbs: the existential -uk and vowel reduplication",
                "objectives": ["Read the 3sg of colour and quality roots as stem + *-uk* 'be' (null word-finally) with the final-syllable vowel repeated (Parks GO p.49).", "Form their intentive (*-uksta*) and gerundial (*-u*)."],
                "morphemes": [{"label": "EXIST *-uk* 'be, exist' (Ø word-finally; *-u* subordinate; *-uksta* intentive)", "meaning": "turns a descriptive stem into a predicate", "forms": ["uk", "u"], "source": "Parks GO p.49–50 (tipahaaʔat; iriirapahaattu; tipahaatuksta)"},
                              {"label": "Rule 4R (stem-final vocalic reduplication)", "meaning": "V(V) → V(V)ʔV between consonants in non-subordinate descriptive forms", "forms": [], "source": "Parks Ch. 3 Rule 4R; GO p.49 'Class I descriptive verbs'"}],
                "walkthrough": lambda d: (
                    f"Parks GO p.49: *tipahaaʔat* 'it is red' < *ti-* + *pahaat* + *-uk*. Dictionary 3sg forms: *{d.F(PAHAAT, 2)}*, *{d.F(KAATIIT_VD, 2)}*, *{d.F(KIISKAAC, 2)}* '{d.G(KIISKAAC)}', "
                    f"*{d.F(KIC_VD, 2)}* '{d.G(KIC_VD)}', *{d.F(HAAS_VD, 2)}* — Class I, with the reduplicated vowel. Class II (no reduplication): *{d.F(TARIIQUUS, 2)}*, *{d.F(KATUUS, 2)}*, *{d.F(KIIQAC, 2)}*. "
                    f"Stems in *r* lose it: *{d.F(TAAKAAR, 2)}*, *{d.F(HURAAR_VD, 2)}*, *{d.F(KAAHURAAR, 2)}*, *{d.F(HIIR_GRASS, 2)}* 'it is grassy'. Intentive: *{d.F(PAHAAT, 5)}*, *{d.F(TAAKAAR, 5)}*; "
                    f"gerundial: *{d.F(PAHAAT, 4)}*, *{d.F(KAATIIT_VD, 4)}*, *{d.F(KIC_VD, 4)}*."),
                "paradigms": [PAHAAT, KAATIIT_VD, TAAKAAR, RAHKATAAR, TARIIQUUS, KIIQAC, KIC_VD, HIIR_GRASS, HURAAR_VD, KIRAAR_VD, HAAS_VD, KATUUS, KIISKAAC, KICKIRAAR, PAHAATKAATIIT, KAAHURAAR, SAKUUR_VD],
                "bb_notes": lambda d: f"BB L2 p.33 *ti pahaat*, L3 p.41 *ti rihu* 'it's big', *ti ha\"k•tihu* 'it's big wood' (OCR). ⚠ BB writes descriptive 3sg without the reduplicated *-ʔa-*; Parks: *{d.F(PAHAAT, 2)}*. For *rihuur* the dictionary gives no form 2 (gap); compounds show it: *{d.F('SK-haakarihuur-p34-0576', 2)}* '{d.G('SK-haakarihuur-p34-0576')}'.",
                "extra_practice": lambda d: _derive(d, [KAATIIT_VD, TAAKAAR, KIC_VD, HAAS_VD, KATUUS], 2, 5, "3sg existential", "3sg intentive"),
                "exercises": ([], []),
            },
        ],
        "review_size": 16,
        "review_extra": lambda d: ("**Final cumulative review.** Appendix 1 *to be good* (uur- preverb) across modes, 3sg: " +
                                   ", ".join(f"{m.split('_')[0]} *{d.A('to be good', m, '3sg')}*" for m in [IND, NEG, CONT, ABS, GER, POT]) +
                                   f" (App.1 p.{d.A_page('to be good')}). Name each mode prefix (Parks Table 8) and the preverb."),
    },
]
