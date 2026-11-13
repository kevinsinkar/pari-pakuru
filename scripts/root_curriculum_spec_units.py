"""Units 1–7 of the root-first curriculum. See root_curriculum_spec_units_b for Units 4–7."""
from root_curriculum_spec_units_b import UNITS_B

# ---------------------------------------------------------------------------
# Entry ids used in Units 1–3 (resolved against skiri_pawnee.db)
# ---------------------------------------------------------------------------
CAAHIKS, PIITA, CAPAAT, PIIRAUQ, PIIRASKI, CUURAKI, CUURAASU, CUUSTIT = (
    "SK-caahiks-p26-0358", "SK-piita-p113-2176", "SK-capaat-p28-0410", "SK-piiraquq-p460-4084",
    "SK-piiraski-p460-4096", "SK-cuuraki-p32-0536", "SK-cuuraasuq-p32-0535", "SK-cuustit-p32-0540")
PIIRIICAAHIKS, ICAAHIKSKITAWI, CIKIRIHPIITA, PIITAKITAWI, HARIWIITA, ICAPAKITAWI, PIIRAKIRIPAHKI = (
    "SK-piiriicaahiks-p460-4099", "SK-icaahikskitawi-p53-0908", "SK-cikirihpiita-p29-0443",
    "SK-piitakitawiquq-p113-2180", "SK-hariwiita-p37-0644", "SK-icapakitawi-p55-0928", "SK-piirakiripahki-p460-4092")
ATIRA, ATIAS, ATIKA, ATIPAT, IRAARI, TIWAAT, TIWACIRIKS, RAKTIIKI, TIKI = (
    "SK-atiraq-p19-0243", "SK-atiqas-p19-0228", "SK-atikaq-p19-0233", "SK-atipat-p19-0241", "SK-iraariq-p64-1121",
    "SK-tiwaat-p166-3278", "SK-tiwaciriks-p166-3279", "SK-raktiiki-p135-2664", "SK-tiki-p165-3261")
AQAS, ASAS, AKAQ, APAT, ARA, ARAAC, PACIRIKS, AWAAT, ARAKIS = (
    "SK-aqas-p349-3581", "SK-asas-p363-3759", "SK-akaq-p9-0103", "SK-apat-p360-3693", "SK-ara-p360-3704",
    "SK-araac-p360-3706", "SK-paciriks-p107-2045", "SK-awaat-p20-0262", "SK-arakis-p13-0132")
HIQAASTI, ISAASTI, IKAARI, IPAAKTI, IWAAHI, IWARIIRIKS, ITAAHI, IRAACTI = (
    "SK-hiqaastiq-p40-0689", "SK-isaastiq-p68-1213", "SK-ikaariq-p61-1056", "SK-ipaaktiq-p64-1116",
    "SK-iwaahiq-p418-3921", "SK-iwariiriks-p418-3922", "SK-itaahiq-p68-1216", "SK-iraactiq-p64-1117")
ASAAKI, ARUUSA, KUHKU, RAKIS, KARITKI, KIRIKS, HIITU, RAAKU, AKAARU, PAAPICISU, RIIKSU, RIKIISU = (
    "SK-asaaki-p362-3736", "SK-aruusaq-p362-3724", "SK-kuhku-p101-1962", "SK-rakis-p135-2644", "SK-karitki-p79-1443",
    "SK-kiriks-p96-1841", "SK-hiituq-p390-3856", "SK-raakuq-p120-2340", "SK-akaaruq-p9-0108",
    "SK-paapicisuq-p454-4063", "SK-riiksuq-p141-2811", "SK-rikiisuq-p492-4194")
ASAAKASIS, ASAAKIRIPAHKI, ASAAKAARU, KIRIKTAAKU, RAAKICKUUSU, ASAAPAHAT, ASAARAHKATA = (
    "SK-asaakasis-p362-3735", "SK-asaakiripahki-p362-3739", "SK-asaakaaruq-p362-3732", "SK-kiriktaakuq-p96-1847",
    "SK-raakickuusuq-p119-2321", "SK-asaapahat-p362-3741", "SK-asaarahkata-p362-3745")
# body
PAKSU, KIRIIKU, HAAKAQU, IKSU, ASU, PAKSKUUKU, IKSKIICU, ASKIIRU, KAAQASASU, PAKSKIRAARU = (
    "SK-paksuq-p110-2116", "SK-kiriikuq-p95-1819", "SK-haakaquq-p33-0559", "SK-iksuq-p64-1111", "SK-asuq-p18-0202",
    "SK-pakskuukuquq-p109-2106", "SK-ikskiicuq-p63-1094", "SK-askiiruq-p16-0165", "SK-kaaqasasuq,_kaasasuq-p2-0005",
    "SK-pakskiraaruq-p109-2102")
KIISU, CKAQU, CUSU, KIICU, UUSU, KAASU, KARAARU, HAATU, PIIRU, CIKSU = (
    "SK-kiisuq-p93-1757", "SK-ckaquq-p30-0460", "SK-cusuq-p32-0528", "SK-kiicuq-p89-1677", "SK-uusuq-p173-3430",
    "SK-kaasuq-p74-1322", "SK-karaaruq-p77-1409", "SK-haatuq-p36-0627", "SK-piiruq-p460-4104", "SK-ciksuq-p29-0448")
HASKIICU, UUSKARAARU, KICKARAARU, KAASTAKIS, HAAKAKIRAARU, KIISKUCUU = (
    "SK-haskiicuq-p37-0653", "SK-uuskaraaruq-p173-3423", "SK-kickaraaruq-p86-1618", "SK-kaastakis-p74-1320",
    "SK-haakakiraaruq-p34-0567", "SK-kiiskucuuq-p92-1740")
ACIKS, ACIKSTAQUK, ACIKSTIIHUUR, ACIKCAK, ACIKSICAAHIKS, WAKURAAH, WAKUHKA, AWIQU, AWIQAT, WAKUHKIISIK, ACIKSTAAHIIS = (
    "SK-aciks-p352-3614", "SK-acikstaquk-p7-0049", "SK-acikstiihuur-p7-0064", "SK-acikcak-p351-3613",
    "SK-aciksicaahiks-p352-3624", "SK-wakuraah-p176-3488", "SK-wakuhka-p176-3480", "SK-awiquq-p21-0290",
    "SK-awiqat-p21-0283", "SK-wakuhkiisik-p176-3482", "SK-acikstaahiis-p7-0051")
# movement / position
AT, A_COME, WICAT, WICA, WARII, KAAQAT, KAAQA, ICKAQAT, KATAHAK, KAAHAK, UQAT, HAAQAT, CIRASAT, AWARII, ICKAHAK, KITAQAT, HUUKITAHAAWARII = (
    "SK-at-p18-0220", "SK-a-p349-3577", "SK-wicat-p178-3529", "SK-wica-p178-3526", "SK-warii-p177-3506",
    "SK-kaaqat-p2-0010", "SK-kaaqa-p2-0001", "SK-ickaqat-p56-0971", "SK-katahak-p80-1480", "SK-kaahak-p2-0023",
    "SK-uqat-p167-3296", "SK-haaqat-p33-0548", "SK-cirasat-p29-0451", "SK-awarii-p21-0272", "SK-ickahak-p57-0975",
    "SK-kitaqat-p98-1907", "SK-huukitahaawarii-p398-3883")
KUS, SA, ARIK, WIITIK, KAAKUS, KAASA, KAARIK, KITAKUS, HUKAKUS, HUKASA, HUKAARIK, KATAKUS, KATASA = (
    "SK-kus-p102-1993", "SK-sa-p150-2933", "SK-arik-p13-0145", "SK-wiitik-p179-3555", "SK-kaakus-p72-1294",
    "SK-kaasa-p73-1312", "SK-kaarik-p73-1306", "SK-kitakus-p98-1912", "SK-hukakus-p44-0739", "SK-hukasa-p44-0741",
    "SK-hukaarik-p44-0728", "SK-katakus-p81-1493", "SK-katasa-p82-1509")
HUUKITAKUS, HUUKITASA, HUUKITAWIITIK, KAAWIITIK, KATAWIITIK, HUKAWIITIK, AWIIRAKUS, KAA, HUKA, KITA = (
    "SK-huukitakus-p398-3884", "SK-huukitasa-p398-3886", "SK-huukitawiitik-p398-3888", "SK-kaawiitik-p74-1339",
    "SK-katawiitik-p82-1527", "SK-hukawiitik-p45-0749", "SK-awiirakus-p23-0303", "SK-kaa-p418-3942",
    "SK-huka-p43-0721", "SK-kita-p98-1905")
# actions
RAQUK, RAAH, RAAH_UUR, WARIK, AWARIK, AWUH, KITAWUH, HUUKITAWUH, CAK, PAKCAK, AAR_BECOME, AAR_DO, KUUT, KICKUUT, IIRIK, KIIKAA, KIKAK, IKSTAAH, KAAWARIK, ICKARAQUK, KAASIK, RIWARIK, ICAKAWARIK = (
    "SK-raquk-p114-2221", "SK-raah-p116-2264", "SK-raah-p116-2265", "SK-warik-p177-3511", "SK-awarik-p21-0273",
    "SK-awuh-p26-0353", "SK-kitawuh-p99-1919", "SK-huukitawuh-p398-3889", "SK-cak,_icak-p27-0402", "SK-pakcak-p108-2076",
    "SK-aar-p351-3596", "SK-aar-p351-3598", "SK-kuut-p452-4017", "SK-kickuut-p87-1642", "SK-iirik-p408-3912",
    "SK-kiikaa-p90-1694", "SK-kikak-p93-1767", "SK-ikstaah-p63-1099", "SK-kaawarik-p74-1336", "SK-ickaraquk-p57-0981",
    "SK-kaasik-p73-1315", "SK-riwarik-p147-2854", "SK-icakawarik-p54-0919")
# qualities / nature
PAHAAT, KAATIIT_VD, TAAKAAR, RAHKATAAR, TARIIQUUS, RIHUUR, KIIQAC, KIC_VD, KIICU_WATER, HURAARU, SAKUURU, RAAQU, KIRAARU, HAASU, HIIRU, HIIR_GOOD = (
    "SK-pahaat-p107-2050", "SK-kaatiit-p74-1330", "SK-taakaar-p502-4233", "SK-rahkataar-p131-2560", "SK-tariiquus-p161-3146",
    "SK-rihuur-p139-2764", "SK-kiiqac-p436-3967", "SK-kic-p84-1568", "SK-kiicuq-p89-1678", "SK-huraaruq-p47-0790",
    "SK-sakuuruq-p152-2965", "SK-raaquq-p115-2248", "SK-kiraaruq-p94-1793", "SK-haasuq-p36-0625", "SK-hiiruq-p390-3845",
    "SK-hiir-p389-3832")
PAHAATKAATIIT, KICTAAKAA, KICKAATIIT, HAAKARIHUUR, KATARIHUUR, KAAHURAARU, KITAHAARU, HUKAHAARU, KICPAHAT = (
    "SK-pahaatkaatiit-p107-2051", "SK-kictaakaa-p436-3947", "SK-kickaatiit-p86-1612", "SK-haakarihuur-p34-0576",
    "SK-katarihuur-p81-1502", "SK-kaahuraaruq-p72-1283", "SK-kitahaaruq-p98-1910", "SK-hukahaaruq-p44-0734",
    "SK-kicpahat-p87-1644")


def _kin_table(d):
    rows = []
    for k in d.kin:
        if k["source"] != "appendix3":
            continue
        rows.append([k["english_term"], k["stem"], k["form_1sg"] or "—", k["form_2sg"] or "—", k["form_3sg"] or "—"])
    from build_root_curriculum import md_table
    return md_table(["Term (App.3)", "Stem", "my", "your", "his/her"], rows)


UNITS_A = [
    # =====================================================================
    {
        "id": 1, "title": "People, kin and the creatures around us (roots as vocabulary)",
        "intro": ("Units 1–3 teach the highest-frequency roots as vocabulary. A root is shown with the simplest attested "
                  "word that contains it, so learners hear a real word while meeting the piece that recurs in dozens of "
                  "others. Suffixes that appear in these words (-uʔ, -kis) are only previewed here; they are taught in Unit 4."),
        "bb_alignment": ("The Blue Book opens with short nouns (L1 p.29) and reaches people-words in L6 (p.55–56) and kinship "
                         "in L7 (p.60–62). This unit pulls the person and kinship roots forward because they are the most "
                         "frequent human-reference roots in the dictionary and because kinship words are the clearest case "
                         "of roots that never stand alone."),
        "lessons": [
            {
                "id": "1.1", "title": "person, man, woman, child",
                "objectives": ["Recognise the roots *icaahiks*, *wiita*, *icapaak*, *piira* inside attested words.",
                               "Hear that a stem (the dictionary form) and the free noun can differ at the edges.",
                               "Match each root to its Blue Book spelling."],
                "roots": ["icaahiks", "wiita", "icapaak", "piira"],
                "walkthrough": lambda d: (
                    f"Parks lists the stem *{d.W(CAAHIKS)}* under the root **icaahiks** (GO p.32 shows it incorporated in "
                    f"*tuuricaahiksii* 'he is a good-looking person'). The free noun *{d.W(CAAHIKS)}* ({d.G(CAAHIKS)}; Parks p.{d.P(CAAHIKS)}) "
                    f"lacks the initial *i-* of the stem; the sound-change engine does not model that loss, so the standalone word is "
                    f"flagged for review while compounds such as *{d.W(PIIRIICAAHIKS)}* ({d.G(PIIRIICAAHIKS)}) keep the full stem. "
                    f"**wiita** 'man, male' surfaces as *{d.W(PIITA)}* ({d.BB(PIITA)}): *w* becomes *p* at the start of a word "
                    f"after the way Parks writes the stem — a *w ~ p* alternation the engine records as an unnumbered rule (medium). "
                    f"**icapaak** 'woman' gives *{d.W(CAPAAT)}* (final *k* → *t* word-finally, as Parks notes for stem-final *k*, GO p.46) "
                    f"and **piira** 'child' gives *{d.W(PIIRAUQ)}* with the noun suffix *-uʔ* (Unit 4). Compare the Blue Book list of "
                    f"people-words ({d.bbq(55, 'pita')}; {d.bbq(56, 'tsuraki')})."),
                "examples": [CAAHIKS, PIITA, CAPAAT, PIIRAUQ, PIIRASKI, CUURAKI, CUURAASU, CUUSTIT, PIIRIICAAHIKS, ICAAHIKSKITAWI],
                "bb_notes": lambda d: (
                    f"BB L6 p.55–56 lists *pita*, *tsapat*, *pirau'*, *piraski*, *tsuraki*, *tsurasu'*, *tsustit*. Parks spellings: "
                    f"*{d.W(PIITA)}*, *{d.W(CAPAAT)}*, *{d.W(PIIRAUQ)}*, *{d.W(PIIRASKI)}*, *{d.W(CUURAKI)}*, *{d.W(CUURAASU)}*, *{d.W(CUUSTIT)}*. "
                    "BB *ts* = Parks *c*; BB does not mark vowel length consistently (BB *pita* vs Parks *piita*). ⚠ BB *pirau'* has no "
                    "dictionary entry with that shape; the database holds it only as a Blue-Book-sourced entry (BB-pirau-0046)."),
                "exercises": ([PIIRAUQ, PIIRIICAAHIKS, CUURAKI, ICAAHIKSKITAWI, CIKIRIHPIITA],
                              [PIITAKITAWI, HARIWIITA, ICAPAKITAWI, PIIRAKIRIPAHKI, CUURAASU]),
                "deviation": "BB introduces these words in L6 after verbs; here they come first so that every later verb lesson can incorporate roots the learner already knows.",
            },
            {
                "id": "1.2", "title": "kinship: stems that never stand alone",
                "objectives": ["Learn the kinship stems (-aas- 'father', -saas-/-raa 'mother', -kaa- 'grandmother', -paak- 'grandfather', -raar- 'same-sex sibling', -waat- 'niece/nephew').",
                               "Recognise the three possessor prefixes *ati-/t-* 'my', *a-* 'your', *i-* 'his/her' and the third-person ending *-riʔ/-tiʔ*.",
                               "Compare Appendix 3, the dictionary entries and Blue Book L7 for the same terms."],
                "roots": ["as #father (kinship, atiʔas)", "kaa #grandmother (kinship, atikaʔ)", "raar #samesex sibling"],
                "morphemes": [
                    {"label": "KIN.POSS 1 *ati-* / *t-* 'my, our'", "meaning": "first-person possessor on kinship stems", "forms": ["ati", "ti"],
                     "source": "Parks App.3; dictionary etymologies (e.g. ati+as, ati+kaa, (a)ti+waat); GO p.30 'kinship terms are uniquely inflected for inalienable possession'"},
                    {"label": "KIN.POSS 2 *a-* 'your'", "meaning": "second-person possessor", "forms": ["a"], "source": "Parks App.3; etymologies a+as, a+kaa, a+raar"},
                    {"label": "KIN.POSS 3 *i-* (dictionary also *hi-*) 'his, her, their' + *-riʔ*", "meaning": "third-person possessor with a closing suffix", "forms": ["i", "hi", "riʔ"],
                     "source": "Parks App.3; etymologies i+raar+riʔ, i+saas+riʔ, hi-+aas+riʔ", "note": "⚠ App.3 writes the father form with *i-*; the dictionary entry writes *hi-* (see review log)."},
                ],
                "walkthrough": lambda d: (
                    f"Parks (GO p.30) says kinship terms are the one noun class inflected for inalienable possession. The dictionary "
                    f"etymologies show the pattern: *{d.W(ATIAS)}* = *ati* 'my' + *as* 'father' (p.{d.P(ATIAS)}); *{d.W(AQAS)}* = *a* 'your' + *as* "
                    f"(p.{d.P(AQAS)}, with ʔ inserted between the two vowels); *{d.W(HIQAASTI)}* = *hi-* + *aas* + *-riʔ* (p.{d.P(HIQAASTI)}), where "
                    f"*s* + *r* gives *st* (Parks Rule 21, *r* → *t* after an obstruent). The same three-way pattern recurs: *{d.W(ATIKA)}* / "
                    f"*{d.W(AKAQ)}* / *{d.W(IKAARI)}* 'grandmother'; *{d.W(ATIPAT)}* / *{d.W(APAT)}* / *{d.W(IPAAKTI)}* 'grandfather' (*k* + *r* → *kt*, Rule 21); "
                    f"*{d.W(IRAARI)}* for both 'my' and 'his/her' same-sex sibling, with *{d.W(ARA)}* 'your' (*a* + *raar*, final *r* lost, Rule 23). "
                    f"In *{d.W(ITAAHI)}* 'his sister (of a male)' the stem *taat* meets *-riʔ*: *t* + *r* → *hr* → *h* (Rules 13, 14, 15). "
                    f"Appendix 3 table:\n\n{_kin_table(d)}\n\nSource: Parks Appendix 3 (kinship_paradigms table)."),
                "examples": [ATIRA, ATIAS, ATIKA, ATIPAT, IRAARI, TIWAAT, TIWACIRIKS, RAKTIIKI, TIKI, AQAS, ASAS, AKAQ, APAT, ARA, ARAAC, PACIRIKS, AWAAT, ARAKIS,
                             HIQAASTI, ISAASTI, IKAARI, IPAAKTI, IWAAHI, IWARIIRIKS, ITAAHI, IRAACTI],
                "bb_notes": lambda d: (
                    f"BB L7 p.60–62 lists the same three sets ({d.bbq(60, 'atira')}; {d.bbq(61, 'asas')}; {d.bbq(62, 'hidsti')}). "
                    f"⚠ Conflicts to show learners rather than hide: (1) 'my grandfather' — dictionary *{d.W(ATIPAT)}* (p.{d.P(ATIPAT)}) and BB *atipat*, "
                    f"but App.3 *atipaat*; (2) 'his father' — App.3 *iʔaastiʔ*, dictionary *{d.W(HIQAASTI)}*, BB *hiasti'* (OCR *hidsti'*); "
                    f"(3) 'your niece/nephew' — Parks *{d.W(AWAAT)}* (p.{d.P(AWAAT)}) but BB *swat* (p.61); (4) BB *tsuwat* 'my daughter' and *tiki'* "
                    f"'my son' have no Parks kinship paradigm (*{d.W(TIKI)}* is in the dictionary only as 'son, sonny', p.{d.P(TIKI)})."),
                "exercises": ([AQAS, AKAQ, ARA, IRAARI, ISAASTI], [ATIAS, ATIKA, IPAAKTI, ITAAHI, ARAAC]),
                "deviation": "BB teaches kinship in L7 after the verb phrase. It is moved here because the possessor prefixes are the simplest attested case of a prefix + root + suffix build, and they are needed to read BB dialogues from L6 on.",
            },
            {
                "id": "1.3", "title": "animals, things, and the Blue Book's first nouns",
                "objectives": ["Learn the roots *asaa* 'horse/dog', *raak* (variants *rak*, *haak*) 'wood', *hiit* 'feather', *akaar* 'dwelling', *rikiis* 'corn', *paapicis* 'metal'.",
                               "Read the Blue Book L1 and L8 noun lists in Parks orthography."],
                "roots": ["asaa", "raak", "hiit", "akaar", "rikiis", "paapicis"],
                "walkthrough": lambda d: (
                    f"**asaa** is a dependent stem (Parks GO p.29: *asaa-* 'horse; dog' cannot stand alone). With the diminutive it is "
                    f"*{d.W(ASAAKI)}* 'dog' (p.{d.P(ASAAKI)}); the independent word for 'horse' is the unrelated *{d.W(ARUUSA)}* (p.{d.P(ARUUSA)}). "
                    f"**raak** 'wood' appears as *rak* in *{d.W(RAKIS)}* ({d.G(RAKIS)}; {d.BB(RAKIS)}) and as *raak* in *{d.W(RAAKU)}* ({d.G(RAAKU)}); "
                    f"Parks also writes *haak* for the same root (etymology of *raktiituʔ*: 'rak/haak'), so the extraction merges *rak* and *haak* "
                    f"under *raak* with medium confidence (vowel-length and *r ~ h* alternations are not numbered rules). "
                    f"**hiit** gives *{d.W(HIITU)}* ({d.BB(HIITU)}), **akaar** gives *{d.W(AKAARU)}*, **rikiis** gives *{d.W(RIKIISU)}* ({d.BB(RIKIISU)}), "
                    f"**paapicis** gives *{d.W(PAAPICISU)}* ('{d.G(PAAPICISU)}'; BB L8 p.68 *papitsisu'* 'metal, money')."),
                "examples": [ASAAKI, ARUUSA, KUHKU, RAKIS, KARITKI, KIRIKS, HIITU, RAAKU, AKAARU, PAAPICISU, RIIKSU, RIKIISU],
                "bb_notes": lambda d: (
                    f"BB L1 p.29–30 basic words: *hitu'*, *karitki*, *kisu'*, *kiriks*, *rakis*, *raku'*, *hawiu'*, *tirakis*, *riksu'*. Parks: "
                    f"*{d.W(HIITU)}*, *{d.W(KARITKI)}*, *{d.W(KIISU)}*, *{d.W(KIRIKS)}*, *{d.W(RAKIS)}*, *{d.W(RAAKU)}*, *{d.W(AWIQU)}*, *{d.W('SK-tiraakis-p166-3268')}*, "
                    f"*{d.W(RIIKSU)}*. ⚠ The database auto-link for BB *kisu'* 'bone' points to *kisu* 'be slender' instead of *{d.W(KIISU)}* 'bone' "
                    f"(see review log, BB link errors). BB L8 p.65: *asaki*, *arusa*, *kuhku*, *akaru'* = Parks *{d.W(ASAAKI)}*, *{d.W(ARUUSA)}*, "
                    f"*{d.W(KUHKU)}*, *{d.W(AKAARU)}*."),
                "exercises": ([ASAAKI, RAKIS, RAAKU, HIITU, AKAARU], [ASAAKASIS, ASAAKIRIPAHKI, KIRIKTAAKU, RAAKICKUUSU, ASAAKAARU]),
                "deviation": "Matches BB L1/L8 vocabulary, but presents each word with its root so that *rakis* and *raakuʔ* are seen as one root rather than two unrelated words.",
            },
        ],
        "review_size": 10,
    },
    # =====================================================================
    {
        "id": 2, "title": "The body and the mind",
        "intro": ("Body-part roots are the most productive noun roots in the dictionary and the nouns most often incorporated "
                  "into verbs (Parks GO p.43). Each is shown with its free noun in *-uʔ* and with compounds."),
        "bb_alignment": "Follows the Blue Book's body lesson (L5, p.49–52) closely in vocabulary; the verb constructions of L5 are postponed to Unit 5.",
        "lessons": [
            {
                "id": "2.1", "title": "head, eye, mouth, hand, foot",
                "objectives": ["Learn *paaks*, *kiriik*, *haaka*, *iks*, *as* and their free nouns.",
                               "Notice vowel-length variants (*paaks ~ paks*, *kiriik ~ kirik*) that Parks writes in different words."],
                "roots": ["paaks", "kiriik", "haaka", "iks", "as"],
                "walkthrough": lambda d: (
                    f"Parks's own Table 5 example is *{d.W(IKSU)}* 'hand' < *iks-* + *-uʔ* (GO p.31). The same build gives *{d.W(PAKSU)}*, "
                    f"*{d.W(KIRIIKU)}*, *{d.W(ASU)}* and *{d.W(HAAKAQU)}*; in the last, the stem ends in a vowel, so a glottal stop separates it from *-uʔ* "
                    f"(the engine logs this as ʔ-epenthesis). The root for 'head' is *paaks* in *{d.W(PAKSKIRAARU)}* ('{d.G(PAKSKIRAARU)}') but short "
                    f"*paks* in *{d.W(PAKSU)}* and *{d.W(PAKSKUUKU)}*; 'eye' is *kiriik* in *{d.W(KIRIIKU)}* but *kirik* in *{d.W(KIRIKTAAKU)}*. "
                    f"These length alternations are merged as variants of one root (medium confidence; no numbered rule)."),
                "examples": [PAKSU, KIRIIKU, HAAKAQU, IKSU, ASU, PAKSKUUKU, IKSKIICU, ASKIIRU, KAAQASASU, PAKSKIRAARU],
                "bb_notes": lambda d: (
                    f"BB L5 p.49: *paksu'*, *kiriku'*, *hakau'*, *iksu'*, *asu'*. Parks: *{d.W(PAKSU)}*, *{d.W(KIRIIKU)}*, *{d.W(HAAKAQU)}*, *{d.W(IKSU)}*, *{d.W(ASU)}*. "
                    f"⚠ BB *hakau'* vs Parks *{d.W(HAAKAQU)}*: BB omits the glottal stop and the vowel length; BB L4 p.44 *paks•ku'ku'* 'hat' = Parks *{d.W(PAKSKUUKU)}*."),
                "exercises": ([IKSU, ASU, PAKSU, HAAKAQU, KIRIIKU], [PAKSKUUKU, IKSKIICU, ASKIIRU, KIRIKTAAKU, PAKSKIRAARU]),
            },
            {
                "id": "2.2", "title": "bone, face, nose, neck, hair, leg, belly, tongue, arm",
                "objectives": ["Learn *kiis*, *icka*, *icus*, *kiic*, *uus*, *kaas*, *karaar*, *hat*, *wiir*.",
                               "See a second case of stem-initial *i-* dropping in free nouns (*icka-* → *ckaʔuʔ*, *icus-* → *cusuʔ*)."],
                "roots": ["kiis", "icka", "icus", "kiic", "uus", "kaas", "karaar", "hat", "wiir"],
                "walkthrough": lambda d: (
                    f"*{d.W(KIISU)}*, *{d.W(KIICU)}*, *{d.W(UUSU)}*, *{d.W(KAASU)}*, *{d.W(KARAARU)}* are plain root + *-uʔ*. *{d.W(CKAQU)}* 'face' and "
                    f"*{d.W(CUSU)}* 'nose' drop the *i-* that the stems *icka-* and *icus-* keep inside verbs (*{d.W(ICKAQAT)}*, Unit 3); Parks "
                    f"gives the etymology *icka+uʔ*, so the free noun is flagged medium/low. *{d.W(HAATU)}* 'tongue' lengthens *hat* to *haat* before *-uʔ* "
                    f"(vowel-length alternation, medium). *{d.W(PIIRU)}* 'arm' shows *wiir* → *piir*, the same *w ~ p* alternation as *wiita* → *piita* "
                    f"(BB L3 p.41 states it as 'w changes to p after a hard consonant'; Parks has no numbered rule for the word-initial case — flagged). "
                    f"Compounds: *{d.W(IKSKIICU)}* 'finger' = *iks* + *kiic* + *uʔ* (hand-neck); *{d.W(HASKIICU)}* = *has* 'string' + *kiic* + *uʔ*; "
                    f"*{d.W(KAASTAKIS)}* 'artificial leg' = *kaas* + *rakis* with *r* → *t* after *s* (Rule 21)."),
                "examples": [KIISU, CKAQU, CUSU, KIICU, UUSU, KAASU, KARAARU, HAATU, PIIRU, CIKSU],
                "bb_notes": lambda d: (
                    f"BB L5 p.51–52: *usu'*, *tsusu'*, *kararu'*, *tsiksu'*, *kasu'*, *kskitsu'* 'finger'. Parks: *{d.W(UUSU)}*, *{d.W(CUSU)}*, *{d.W(KARAARU)}*, "
                    f"*{d.W(CIKSU)}*, *{d.W(KAASU)}*, and for 'finger' *{d.W(IKSKIICU)}* (⚠ BB *kskitsu'* drops the initial *i* of *iks-* and the dictionary has "
                    f"no entry spelled that way). ⚠ Database auto-links for BB *kararu'* and *kasu'* point to the wrong entries (review log)."),
                "exercises": ([KIISU, KIICU, KAASU, KARAARU, UUSU], [HASKIICU, UUSKARAARU, KICKARAARU, KAASTAKIS, PIIRU]),
            },
            {
                "id": "2.3", "title": "mind, speech, image: roots for inner life",
                "objectives": ["Learn *aciks* 'thought, mind' (also 'trachea'), *wakur* 'speech, voice', *awi* 'image'.",
                               "See roots that live almost only inside verbs."],
                "roots": ["aciks", "wakur", "awi"],
                "walkthrough": lambda d: (
                    f"**aciks** builds {d.roots['aciks']['frequency']} dictionary words: as a descriptive verb *{d.W(ACIKS)}* '{d.G(ACIKS)}' and as the first "
                    f"element of *{d.W(ACIKSTAQUK)}* '{d.G(ACIKSTAQUK)}', *{d.W(ACIKSTIIHUUR)}* '{d.G(ACIKSTIIHUUR)}', *{d.W(ACIKSICAAHIKS)}* '{d.G(ACIKSICAAHIKS)}' "
                    f"(two roots the learner knows: thought + person). In *{d.W(ACIKCAK)}* '{d.G(ACIKCAK)}' the final *s* of *aciks* drops before *cak* "
                    f"(Rule 9R, final-*s* loss). Parks glosses the same root 'trachea' in *{d.W(ACIKSTAAHIIS)}* and the free noun *{d.W(CIKSU)}* is "
                    f"'{d.G(CIKSU)}' — one root covering the windpipe and the thoughts; the extraction keeps it as one root and flags the gloss spread. "
                    f"**wakur** 'speech' loses its final *r* before a consonant (*{d.W(WAKUHKA)}*, *{d.W(WAKUHKIISIK)}*; Rule 23 as logged) and keeps it before a vowel "
                    f"(*{d.W(WAKURAAH)}*). **awi** 'image' gives *{d.W(AWIQU)}* 'picture' ({d.BB(AWIQU) or 'BB L1 p.29 hawiu'}) and the verb *{d.W(AWIQAT)}* 'jump'."),
                "examples": [ACIKS, CIKSU, ACIKSTAQUK, ACIKSTIIHUUR, ACIKCAK, ACIKSICAAHIKS, WAKURAAH, WAKUHKA, AWIQU, AWIQAT],
                "exercises": ([ACIKCAK, ACIKSICAAHIKS, AWIQU, WAKURAAH, AWIQAT], [ACIKSTIIHUUR, ACIKSTAQUK, WAKUHKA, WAKUHKIISIK, ACIKSTAAHIIS]),
                "deviation": "Not a Blue Book topic; included because *aciks* is the seventh most productive root in the dictionary.",
            },
        ],
        "review_size": 10,
    },
    # =====================================================================
    {
        "id": 3, "title": "Movement, position, everyday actions, and qualities",
        "intro": ("The verb roots that build the most stems: Parks notes that *at* 'go' and *hak* 'pass' each have hundreds of derived "
                  "stems (GO p.31). Position roots (*kus*, *sa*, *arik*) and the locative stem elements *kaa*, *kata*, *kita*, *huka* "
                  "are learned together because they almost always occur together. Verb forms shown here are the dictionary's own "
                  "cited forms; how the prefixes work is the subject of Unit 5."),
        "bb_alignment": "BB meets these verbs in L5–L6 (*ti•wari'*, *ti•kikat*, *tut•ari'*, *ti•ruku'*) and L8 (*t'erit*, *ti•kaku'*). The colour and size roots are BB L2–L3.",
        "lessons": [
            {
                "id": "3.1", "title": "going and coming",
                "objectives": ["Learn *at* 'go' (rank 1), *a (ir...)* 'come', *hak* 'pass', *wic* 'arrive', *warii* 'go about', and the plural/dual stems of 'go'.",
                               "Read the irregular-root table (Parks Appendix 2)."],
                "roots": ["at", "a", "hak", "wic", "warii", "wuu"],
                "walkthrough": lambda d: (
                    f"*at* stands alone as the verb *{d.W(AT)}* '{d.G(AT)}' (3sg *{d.F(AT, 2)}*, p.{d.P(AT)}) and ends hundreds of stems: *{d.W(KAAQAT)}* "
                    f"'{d.G(KAAQAT)}' (*kaa* 'inside' + *at*, with ʔ between the vowels), *{d.W(ICKAQAT)}*, *{d.W(KITAQAT)}*, *{d.W(AWIQAT)}* 'jump', *{d.W(WICAT)}* "
                    f"'{d.G(WICAT)}'. *a* 'come' is a discontinuous stem with the preverb *ir-* (Parks GO p.31–32: 'the root a has no independent meaning of come' "
                    f"outside this stem); its 3sg is *{d.F(A_COME, 2)}* and with *kaa* it is *{d.W(KAAQA)}* '{d.G(KAAQA)}' (3sg *{d.F(KAAQA, 2)}*). "
                    f"*hak* 'pass' gives *{d.W(KAAHAK)}*, *{d.W(KATAHAK)}*, *{d.W(ICKAHAK)}*. 'Go' is irregular in number: singular *at*, dual *war*, plural *wuu* "
                    f"(Appendix 2, irregular_verb_roots), seen in App.1 *{d.A('to go', 'indicative_perfective', '3sg')}* / *{d.A('to go', 'indicative_perfective', '3du')}* / "
                    f"*{d.A('to go', 'indicative_perfective', '3pl')}*; the Blue Book states the same alternation ({d.bbq(54, 'roots for go')})."),
                "examples": [AT, A_COME, WICAT, WICA, WARII, KAAQAT, KAAQA, AWIQAT, ICKAQAT, KATAHAK, KAAHAK, UQAT],
                "paradigms": [AT, KAAQAT, WARII, WICAT],
                "exercises": ([KAAQAT, WICAT, AWARII, ICKAHAK, KITAQAT], [HAAQAT, AWIQAT, CIRASAT, KATAHAK, HUUKITAHAAWARII]),
            },
            {
                "id": "3.2", "title": "sitting, lying, standing — and where",
                "objectives": ["Learn the position roots *kus* 'be sitting', *sa* 'be lying', *arik* 'be standing', *wiitik* 'sit down'.",
                               "Learn the locative stem elements *kaa* 'inside', *kata* 'against a vertical surface', *kita* 'on top', *huka* 'in a shallow space' and combine them with the position roots."],
                "roots": ["kus", "sa", "arik #be standing", "wiitik", "kaa", "kata", "kita", "huka"],
                "walkthrough": lambda d: (
                    f"Position roots stand alone (*{d.W(KUS)}* 3sg *{d.F(KUS, 2)}*; *{d.W(SA)}* 3sg *{d.F(SA, 2)}*; *{d.W(ARIK)}* 3sg *{d.F(ARIK, 2)}*; *{d.W(WIITIK)}* 3sg *{d.F(WIITIK, 2)}*) "
                    f"and take a locative element in front (Parks Table 15, GO p.44: locative slot before the root): *{d.W(KAAKUS)}* '{d.G(KAAKUS)}', *{d.W(KAASA)}* "
                    f"'{d.G(KAASA)}', *{d.W(KAARIK)}* '{d.G(KAARIK)}' (Parks writes short *ka* here), *{d.W(KITAKUS)}* '{d.G(KITAKUS)}', *{d.W(HUKAKUS)}* '{d.G(HUKAKUS)}', "
                    f"*{d.W(KATASA)}* '{d.G(KATASA)}'. The elements are themselves locative verbs: *{d.W(KAA)}* '{d.G(KAA)}' (3sg *{d.F(KAA, 2)}*), *{d.W(HUKA)}* (3sg *{d.F(HUKA, 2)}*). "
                    f"Note the attested shapes: *{d.W(ARIK)}* ends in *k* but its 3sg is *{d.F(ARIK, 2)}* (*k* → *t* word-finally; i + a → ii, Rule 7); "
                    f"*{d.W(WIITIK)}* 3sg *{d.F(WIITIK, 2)}* likewise."),
                "examples": [KUS, SA, ARIK, WIITIK, KAA, HUKA, KITA, KAAKUS, KAASA, KAARIK, KITAKUS, HUKAKUS, HUKASA, HUKAARIK, KATAKUS, KATASA, HUUKITAKUS, KAAWIITIK],
                "paradigms": [KUS, SA, ARIK, WIITIK, KAAKUS, KITAKUS],
                "bb_notes": lambda d: f"BB L8 p.66 *t'erit* 'he is standing', *ti•kaku'* 'he's inside' = Parks *{d.F(ARIK, 2)}*, *{d.F(KAAKUS, 2)}* (p.{d.P(ARIK)}, p.{d.P(KAAKUS)}). ⚠ BB *e* in *t'erit* corresponds to Parks *ii* (i + a contraction, Rule 7) — see guide §1.",
                "exercises": ([KAAKUS, KAASA, HUKAARIK, KITAKUS, HUUKITAWIITIK], [KATAWIITIK, HUKASA, HUUKITASA, KAAWIITIK, AWIIRAKUS]),
            },
            {
                "id": "3.3", "title": "everyday actions",
                "objectives": ["Learn *raʔuk* 'make', *raah* 'have, carry', *warik* 'throw; cause to go', *wuh* 'put', *cak* 'strike', *aar* 'become / do', *kuut* 'die', *iirik* 'see', *kiikaa* 'drink', *kikak* 'cry'.",
                               "Notice that some roots are rare in the dictionary's etymologies but central in speech (*kikak*, *kiikaa*)."],
                "roots": ["raʔuk", "raah", "warik", "wuh", "cak", "aar", "kuut", "iirik", "kiikaa"],
                "walkthrough": lambda d: (
                    f"*{d.W(RAQUK)}* '{d.G(RAQUK)}' has 3sg *{d.F(RAQUK, 2)}* (Parks GO p.46 cites exactly this: *tiruʔ* 'he made it' < ti- + raʔuk); it also serves as "
                    f"the causative suffix *-raʔuk* (Unit 7). *{d.W(RAAH)}* '{d.G(RAAH)}' (3sg *{d.F(RAAH, 2)}*) is the 'have' of BB L4 (*tah•ra*, see Unit 5) and appears in "
                    f"*{d.W(IKSTAAH)}* '{d.G(IKSTAAH)}' with *s* + *r* → *st* (Rule 21). *{d.W(WARIK)}* gives *{d.W(AWARIK)}* 'throw' and *{d.W(KAAWARIK)}* 'put inside'; "
                    f"*wuh* gives *{d.W(AWUH)}*, *{d.W(KITAWUH)}* '{d.G(KITAWUH)}', *{d.W(HUUKITAWUH)}*. *{d.W(CAK)}* 'strike' gives *{d.W(PAKCAK)}* 'shoot' (final *s* of *paks* lost, Rule 9R). "
                    f"*aar* is two dictionary verbs: *{d.W(AAR_BECOME)}* '{d.G(AAR_BECOME)}' (3sg *{d.F(AAR_BECOME, 2)}*) and, with the preverb *ut-*, *{d.W(AAR_DO)}* '{d.G(AAR_DO)}' "
                    f"(3sg *{d.F(AAR_DO, 2)}*; BB L6 p.56 *ti•ari'* vs *tut•ari'*). *{d.W(KUUT)}* '{d.G(KUUT)}' is a passive (patient-marked) verb: 1sg *{d.F(KUUT, 1)}*. "
                    f"*{d.W(KIKAK)}* 'cry' (3sg *{d.F(KIKAK, 2)}*, BB L6 *ti•kikat*) and *{d.W(KIIKAA)}* 'drink' (3sg *{d.F(KIIKAA, 2)}*, App.1 'to drink it') are low in the "
                    f"root ranking because few other dictionary stems are built on them, not because they are rare in use."),
                "examples": [RAQUK, RAAH, RAAH_UUR, WARIK, AWARIK, AWUH, CAK, AAR_BECOME, AAR_DO, KUUT, IIRIK, KIIKAA, KIKAK],
                "paradigms": [RAQUK, RAAH, KIKAK, KIIKAA, AAR_BECOME, AAR_DO, KUUT, IIRIK],
                "exercises": ([AWARIK, PAKCAK, KITAWUH, KICKUUT, IKSTAAH], [HUUKITAWUH, KAAWARIK, ICKARAQUK, KAASIK, RIWARIK]),
            },
            {
                "id": "3.4", "title": "qualities, colours and the natural world",
                "objectives": ["Learn the descriptive roots *pahaat* 'red', *kaatiit* 'black', *taakaar* 'white', *rahkataar* 'yellow', *tariiʔuus* 'blue', *rihuur* 'big', *kiiʔac* 'long', *kucuu* 'big (in nouns)'.",
                               "Learn the nature roots *kic* 'liquid/water', *haar* 'place', *huraar* 'ground', *sakuur* 'sun/day', *raa* 'way', *kiraar* 'liquid', *haas* 'string', *hiir* 'grass' and *hiir (uur...)* 'be good'."],
                "roots": ["pahaat", "kaatiit", "taakaar", "rahkataar", "tariiʔuus", "rihuur", "kiiʔac", "kucuu", "kic", "haar", "huraar", "sakuur", "raa", "kiraar", "haas", "hiir #grass", "hiir #(uur...) be good"],
                "walkthrough": lambda d: (
                    f"Colour roots are descriptive verbs: *{d.W(PAHAAT)}* 3sg *{d.F(PAHAAT, 2)}* (Parks GO p.49: the final-syllable vowel is repeated with ʔ in "
                    f"non-subordinate forms), *{d.W(KAATIIT_VD)}* 3sg *{d.F(KAATIIT_VD, 2)}*, *{d.W(TAAKAAR)}* 3sg *{d.F(TAAKAAR, 2)}* (final *r* lost, Rule 23), "
                    f"*{d.W(TARIIQUUS)}* 3sg *{d.F(TARIIQUUS, 2)}*. The same roots close compound nouns: *{d.W(KICPAHAT)}* '{d.G(KICPAHAT)}', *{d.W(KICKAATIIT)}* '{d.G(KICKAATIIT)}', "
                    f"*{d.W(KICTAAKAA)}* '{d.G(KICTAAKAA)}', *{d.W(ASAAPAHAT)}* '{d.G(ASAAPAHAT)}', *{d.W(ASAARAHKATA)}* '{d.G(ASAARAHKATA)}'. *{d.W(RIHUUR)}* 'be big' is the verbal "
                    f"'big' (*{d.W(HAAKARIHUUR)}*, *{d.W(KATARIHUUR)}* 'be wide'), *kucuu* the nominal one (*{d.W(KIISKUCUU)}* '{d.G(KIISKUCUU)}'). "
                    f"*kic* 'liquid, water' (rank {d.roots['kic']['rank']}) gives *{d.W(KIICU_WATER)}* 'water'; *haar* 'place' closes *{d.W(KITAHAARU)}* 'hilltop' and "
                    f"*{d.W(HUKAHAARU)}*; *huraar* 'ground' gives *{d.W(HURAARU)}* and *{d.W(KAAHURAARU)}* 'world' (*kaa* + *huraar* + *uʔ*). "
                    f"*hiir* is two roots: 'grass' (*{d.W(HIIRU)}*) and, only with the preverb *uur-*, 'be good' (*{d.W(HIIR_GOOD)}* 3sg *{d.F(HIIR_GOOD, 2)}*; App.1 'to be good'); "
                    f"the extraction splits them by the presence of *uur-* and by gloss."),
                "examples": [PAHAAT, KAATIIT_VD, TAAKAAR, RAHKATAAR, TARIIQUUS, RIHUUR, KIIQAC, KIC_VD, KIICU_WATER, HURAARU, SAKUURU, AKAARU, RAAQU, KIRAARU, HAASU, HIIRU, HIIR_GOOD],
                "paradigms": [PAHAAT, KAATIIT_VD, TAAKAAR, TARIIQUUS, RIHUUR, HIIR_GOOD],
                "bb_notes": lambda d: (
                    f"BB L2 p.33 'What colour is it?': *ti pahaat*, *ti tareus*, *ti kirareus*, and p.35 *rakis + rahkata = rakis•tahkata* 'a yellow stick'. "
                    f"⚠ BB *ti pahaat* vs Parks *{d.F(PAHAAT, 2)}*: Parks's 3sg has the reduplicated *-aaʔat* (GO p.49), BB writes the bare stem. "
                    f"⚠ BB *tareus* 'blue' vs Parks *{d.W(TARIIQUUS)}*: BB *e* for Parks *ii* and no ʔ. The sound change BB states on p.35 is Parks Rule 21 "
                    f"(*r* → *t* after an obstruent), seen in *{d.W(ASAARAHKATA)}* only partly (here the *r* follows a vowel and stays)."),
                "exercises": ([PAHAATKAATIIT, KICTAAKAA, ASAAPAHAT, ASAARAHKATA, KICKAATIIT], [HAAKARIHUUR, KATARIHUUR, KAAHURAARU, KITAHAARU, HUKAHAARU]),
                "deviation": "BB L2 teaches colours as the second lesson with the frame *ti ...*. Here they are vocabulary; the *ti-* prefix itself is taught in Lesson 5.1.",
            },
        ],
        "review_size": 14,
    },
]

UNITS = UNITS_A + UNITS_B
