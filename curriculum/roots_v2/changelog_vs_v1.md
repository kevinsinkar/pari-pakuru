# What changed from version 1

Version 1 is `curriculum/roots/roots_ranked.json` (1,320 root senses, ranked by the number of headwords whose stored piece list contains the root). Version 2 counts differently, so most numbers move. The general reasons come first; the table then gives every root that was added, removed, split or merged, or whose rank moved by more than 10 places or whose count changed by more than 25%.

## Why the numbers differ in general

1. **Tier A/B only.** A v2 count is the number of words whose analysis is tier A or B *and* in which the meaning of the piece was checked. v1 counted every headword whose stored piece list contained the form.
2. **Lexemes, not rows.** 4337 rows are 4337 lexemes after duplicate resolution.
3. **Meaning comes from the printed etymology.** v1 took each piece's gloss from a stored parse that mis-aligns glosses; v2 re-reads Parks's printed string.
4. **Senses are split systematically.** v1 split five shapes by hand. v2 keeps apart every group of glosses that shares no content word (273 shapes).
5. **No merges on vowel length.** v1 merged 21 variant pairs; v2 merges none and lists 85 candidates for review.
6. **Stem formatives are affixes.** Unlabelled raar, ra, ri, waa, wi, hus, his and the causatives are classed as affixes by cited decisions (`decisions.json`), so they leave the root list.
7. **Compound stems are resolved.** A dotted unit in Parks's etymology is matched to its own dictionary entry, and its inner pieces take their meaning from there.

## Root by root

| Root | v1 meaning | v1 rank | v1 words | v2 | v2 rank | v2 words (A+B / all tiers) | What happened |
|---|---|---|---|---|---|---|---|
| raa | way | 2 | 131 | way | 3 | 104 / 149 | shape split into 6 senses (way 104; things 2; mother 0; object 0); some uses reclassified as affix PL |
| kic | liquid | 3 | 114 | liquid | 7 | 60 / 114 | count falls: only tier A/B words with a checked meaning are counted (114 in all tiers) |
| a | come | 4 | 113 | come | 11 | 48 / 66 | shape split into 6 senses (come 48; extending in a line 19; wear 4; your 3); some uses reclassified as affix SUB; count falls: only tier A/B words with a checked meaning are counted (66 in all tiers) |
| awi | image | 6 | 91 | image | 8 | 58 / 75 | shape split into 2 senses (image 58; worn 0); count falls: only tier A/B words with a checked meaning are counted (75 in all tiers) |
| aciks | thought | 7 | 83 | mind | 5 | 63 / 84 | shape split into 2 senses (mind 63; trachea 2) |
| raak | wood | 8 | 80 | wood | 320 | 3 / 5 | shape split into 5 senses (wood 3; a dam 1; box 0; tree 0); v1 had merged the variants haak, rak; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (5 in all tiers) |
| kata | against a vertical surface | 9 | 76 | on a vertical surface | 9 | 56 / 80 | shape split into 2 senses (on a vertical surface 56; throat 2); count falls: only tier A/B words with a checked meaning are counted (80 in all tiers) |
| hak | pass | 10 | 69 | pass | 14 | 38 / 54 | shape split into 4 senses (pass 38; take 7; hold 0; in a circle 0); count falls: only tier A/B words with a checked meaning are counted (54 in all tiers) |
| aar | become | 11 | 56 | become | 12 | 48 / 52 | shape split into 3 senses (become 48; tooth 5; do 3); some uses reclassified as affix INCH |
| haar | place | 12 | 55 | place | 34 | 18 / 32 | shape split into 3 senses (place 18; state 0; interior 0); count falls: only tier A/B words with a checked meaning are counted (32 in all tiers) |
| kaa | inside | 13 | 55 | inside | 13 | 42 / 56 | shape split into 2 senses (inside 42; grandmother 0) |
| as | foot | 14 | 53 | foot | 15 | 33 / 48 | shape split into 3 senses (foot 33; perseverance 1; father 0); count falls: only tier A/B words with a checked meaning are counted (48 in all tiers) |
| iks | hand | 15 | 51 | hand | 17 | 31 / 53 | count falls: only tier A/B words with a checked meaning are counted (53 in all tiers) |
| uhuur | image | 16 | 49 | image | 23 | 25 / 44 | shape split into 2 senses (image 25; behavior 1); count falls: only tier A/B words with a checked meaning are counted (44 in all tiers) |
| kiis | bone | 17 | 48 | bone | 21 | 26 / 42 | shape split into 3 senses (bone 26; vain 5; lively 0); count falls: only tier A/B words with a checked meaning are counted (42 in all tiers) |
| kaatiit | black | 18 | 44 | black | 48 | 14 / 22 | shape split into 2 senses (black 14; dark 3); v1 had merged the variants katiit; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (22 in all tiers) |
| paaks | head | 19 | 42 | head | 1011 | 0 / 2 | v1 had merged the variants paks; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| kiriik | eye | 20 | 40 | eye | 1264 | 0 / 1 | v1 had merged the variants kirik; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (1 in all tiers) |
| warik | cause to | 21 | 40 | cause to go | 18 | 30 / 38 | shape split into 2 senses (cause to go 30; send 2) |
| hiir | good | 22 | 39 | good | 22 | 26 / 41 | shape split into 3 senses (good 26; grass 13; night to elapse 1); count falls: only tier A/B words with a checked meaning are counted (41 in all tiers) |
| haa | in water | 23 | 38 | in water | 174 | 5 / 5 | shape split into 2 senses (in water 5; ones child 4); v1 had merged the variants ha; v2 counts them separately; some uses reclassified as affix LOC.ADV; count falls: only tier A/B words with a checked meaning are counted (5 in all tiers) |
| akaar | dwelling | 24 | 34 | dwelling | 50 | 13 / 27 | shape split into 4 senses (dwelling 13; hide 4; canvas 0; sod 0); count falls: only tier A/B words with a checked meaning are counted (27 in all tiers) |
| haas | string | 25 | 34 | string | 59 | 11 / 13 | v1 had merged the variants has; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| icka | face | 26 | 33 | face | 33 | 19 / 23 | shape split into 5 senses (face 19; cloud 4; end 3; sharp 1); count falls: only tier A/B words with a checked meaning are counted (23 in all tiers) |
| huu | surface | 27 | 31 | surface | 70 | 9 / 13 | shape split into 3 senses (surface 9; mush 7; through water 5); count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| huraar | ground | 28 | 30 | land | 19 | 29 / 44 | shape split into 2 senses (land 29; source 0) |
| pahaat | red | 29 | 29 | red | 68 | 9 / 31 | shape split into 2 senses (red 9; mescal bean 0); count falls: only tier A/B words with a checked meaning are counted (31 in all tiers) |
| huur | image | 31 | 26 | image | 379 | 3 / 3 | shape split into 5 senses (image 3; tracks 3; have the quality of 2; traditional 0); count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| kiraar | liquid | 32 | 26 | liquid | 38 | 17 / 21 | shape split into 5 senses (liquid 17; clear 3; light in color 3; water 0); count falls: only tier A/B words with a checked meaning are counted (21 in all tiers) |
| kita | on top | 33 | 26 | on top | 41 | 16 / 24 | shape split into 2 senses (on top 16; a fork 4); count falls: only tier A/B words with a checked meaning are counted (24 in all tiers) |
| haaka | mouth | 34 | 25 | mouth | 54 | 12 / 20 | shape split into 3 senses (mouth 12; drum 0; skull 0); count falls: only tier A/B words with a checked meaning are counted (20 in all tiers) |
| kiir | water | 35 | 25 | water | 84 | 8 / 12 | shape split into 3 senses (water 8; long 4; tied 0); count falls: only tier A/B words with a checked meaning are counted (12 in all tiers) |
| sa | lying | 36 | 25 | lying | 25 | 25 / 27 | rank moved with the general changes above |
| icaahiks | person | 37 | 24 | person | 36 | 17 / 24 | count falls: only tier A/B words with a checked meaning are counted (24 in all tiers) |
| irii | that | 38 | 24 | there | 979 | 0 / 2 | some uses reclassified as affix REL; count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| sakuur | sun | 39 | 24 | sun | 119 | 6 / 13 | shape split into 2 senses (a day 10; sun 6); count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| arik | standing | 40 | 23 | standing | 31 | 20 / 24 | shape split into 3 senses (standing 20; horn 5; have 3) |
| taakaar | white | 41 | 23 | white | 35 | 17 / 28 | shape split into 2 senses (white 17; on the head 0); count falls: only tier A/B words with a checked meaning are counted (28 in all tiers) |
| icaa | on the end | 42 | 22 | on the end of a pole | 481 | 2 / 3 | v1 had merged the variants ica; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| kuuku | covering | 43 | 22 | covering | 44 | 15 / 20 | shape split into 2 senses (covering 15; money 0); count falls: only tier A/B words with a checked meaning are counted (20 in all tiers) |
| rikiis | corn | 44 | 22 | corn | 58 | 11 / 21 | shape split into 4 senses (corn 11; proud of 1; cooked 0; cut short 0); count falls: only tier A/B words with a checked meaning are counted (21 in all tiers) |
| katuus | flat | 45 | 21 | flat | 45 | 15 / 19 | shape split into 3 senses (flat 15; ravine 3; flatly 1); count falls: only tier A/B words with a checked meaning are counted (19 in all tiers) |
| kiic | neck | 46 | 21 | neck | 47 | 15 / 18 | count falls: only tier A/B words with a checked meaning are counted (18 in all tiers) |
| rihuur | big | 47 | 20 | big | 27 | 22 / 23 | rank moved with the general changes above |
| wakur | speech | 48 | 20 | speech | 56 | 12 / 16 | shape split into 3 senses (speech 12; voice to speak 3; words 1); count falls: only tier A/B words with a checked meaning are counted (16 in all tiers) |
| warii | around in a line | 49 | 20 | go around | 37 | 17 / 24 | rank moved with the general changes above |
| wii | now | 50 | 20 | now | 475 | 2 / 4 | shape split into 4 senses (bent 7; slanting 5; now 2; thick 2); count falls: only tier A/B words with a checked meaning are counted (4 in all tiers) |
| hiir | grass | 51 | 19 | grass | 51 | 13 / 19 | shape split into 3 senses (good 26; grass 13; night to elapse 1); count falls: only tier A/B words with a checked meaning are counted (19 in all tiers) |
| icus | nose | 52 | 19 | nose | 79 | 8 / 20 | count falls: only tier A/B words with a checked meaning are counted (20 in all tiers) |
| kiiʔac | long | 53 | 19 | long | 146 | 5 / 17 | shape split into 3 senses (long 5; length 0; tall 0); count falls: only tier A/B words with a checked meaning are counted (17 in all tiers) |
| huukita | on top | 55 | 18 | on top | 61 | 10 / 19 | count falls: only tier A/B words with a checked meaning are counted (19 in all tiers) |
| raah | have | 56 | 18 | have | 39 | 17 / 17 | rank moved with the general changes above |
| uu | be | 57 | 18 | facing | 726 | 1 / 2 | shape split into 6 senses (facing 1; way 0; favor 0; have 0); count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| wiitik | sit down | 58 | 18 | sit down | 40 | 17 / 17 | shape split into 2 senses (sit down 17; set 1) |
| rahkataar | yellow | 59 | 17 | yellow | 281 | 3 / 18 | count falls: only tier A/B words with a checked meaning are counted (18 in all tiers) |
| wic | arrive | 60 | 16 | at a point | 52 | 13 / 17 | shape split into 2 senses (at a point 13; destination 1) |
| wuu | going in a line | 61 | 16 | going | 198 | 4 / 9 | count falls: only tier A/B words with a checked meaning are counted (9 in all tiers) |
| i | it i | 62 | 15 | his her | 620 | 1 / 9 | count falls: only tier A/B words with a checked meaning are counted (9 in all tiers) |
| iit | in a line | 63 | 15 | in a line | 118 | 6 / 13 | shape split into 3 senses (breast 7; in a line 6; body 1); count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| raawis | smoke | 64 | 15 | smoke | 80 | 8 / 16 | shape split into 2 senses (smoke 8; paint 0); count falls: only tier A/B words with a checked meaning are counted (16 in all tiers) |
| waktaa | sound | 65 | 15 | a sound | 282 | 3 / 16 | count falls: only tier A/B words with a checked meaning are counted (16 in all tiers) |
| wiir | arm | 66 | 15 | arm | 90 | 8 / 10 | shape split into 2 senses (arm 8; leaning 0); v1 had merged the variants piir; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| asaa | horse | 67 | 14 | horse | 43 | 15 / 30 | rank moved with the general changes above |
| iir | put | 68 | 14 | put down | 62 | 10 / 15 | shape split into 2 senses (put down 10; carcass 0); count falls: only tier A/B words with a checked meaning are counted (15 in all tiers) |
| kiihaar | room | 69 | 14 | room | 71 | 9 / 12 | count falls: only tier A/B words with a checked meaning are counted (12 in all tiers) |
| paapicis | metal | 70 | 14 | metal | 82 | 8 / 14 | count falls: only tier A/B words with a checked meaning are counted (14 in all tiers) |
| piira | child | 71 | 14 | child | 99 | 7 / 12 | shape split into 3 senses (child 7; babies 0; bent over 0); count falls: only tier A/B words with a checked meaning are counted (12 in all tiers) |
| tapaht | ground | 72 | 14 | ground | 130 | 6 / 8 | shape split into 3 senses (ground 6; crumbled 5; pulverized 0); count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| tat | stalk | 73 | 14 | stalk | 450 | 2 / 13 | shape split into 2 senses (stalk 2; back 0); count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| wat | acorn | 74 | 14 | acorn | 729 | 1 / 2 | shape split into 2 senses (extract 4; acorn 1); count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| cak | strike | 75 | 13 | strike | 74 | 9 / 11 | shape split into 3 senses (strike 9; pierce 1; stick 1); count falls: only tier A/B words with a checked meaning are counted (11 in all tiers) |
| hata | hole | 76 | 13 | hole | 60 | 11 / 13 | rank moved with the general changes above |
| hur | place | 77 | 13 | place | 911 | 0 / 8 | count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| kuuc | vessel | 78 | 13 | vessel | 1284 | 0 / 1 | v1 had merged the variants kuc; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (1 in all tiers) |
| pira |  | 79 | 13 | scraping | 111 | 7 / 8 | shape split into 3 senses (scraping 7; curved 4; crooked 2); count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| raaruus | hairy | 80 | 13 | hairy | 945 | 0 / 3 | shape split into 3 senses (hairy 0; furry 0; fuzzy 0); v1 had merged the variants raarus, raruus; v2 counts them separately; some uses reclassified as affix DIST; count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| ta | suspended | 81 | 13 | suspended | 6 | 61 / 77 | some uses reclassified as affix GEN.LOC; count rises: occurrences inside compound stems are now recognised |
| tawi | suspended | 82 | 13 | suspended | 1045 | 0 / 2 | shape split into 5 senses (among 5; song 4; lyrics 1; suspended 0); count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| wak | sound | 83 | 13 | sound | 120 | 6 / 13 | shape split into 2 senses (sound 6; verbally 0); count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| atiik | bean | 84 | 12 | bean | 195 | 4 / 12 | count falls: only tier A/B words with a checked meaning are counted (12 in all tiers) |
| icataa | grease bread | 85 | 12 | bread | 117 | 6 / 13 | count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| iri | there | 86 | 12 | there | 486 | 2 / 3 | shape split into 3 senses (in a horizontal position 8; there 2; reclined 1); count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| kahc | herb | 87 | 12 | herb | 98 | 7 / 12 | count falls: only tier A/B words with a checked meaning are counted (12 in all tiers) |
| karuus | shriveled | 88 | 12 | shriveled | 986 | 0 / 2 | shape split into 4 senses (deflated 6; sack 3; shriveled 0; lost 0); count falls: only tier A/B words with a checked meaning are counted (2 in all tiers) |
| kasis | stunted | 89 | 12 | hard | 57 | 12 / 14 | shape split into 2 senses (hard 12; solidly 1) |
| kuuʔat | sore | 90 | 12 | rotten | 148 | 5 / 13 | count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| raʔuk | causative | 91 | 12 | cause | 2 | 109 / 116 | count rises: occurrences inside compound stems are now recognised |
| tariik | wear tied around the belly | 92 | 12 | tied | 149 | 5 / 11 | count falls: only tier A/B words with a checked meaning are counted (11 in all tiers) |
| tariiʔuus | blue | 93 | 12 | blue | 72 | 9 / 12 | shape split into 2 senses (blue 9; green 0) |
| tii | thi | 94 | 12 | border | 322 | 3 / 5 | shape split into 5 senses (border 3; here 3; like 2; tame 1); count falls: only tier A/B words with a checked meaning are counted (5 in all tiers) |
| tiraak | bow/gun | 95 | 12 | gun | 73 | 9 / 12 | rank moved with the general changes above |
| wuh | put | 96 | 12 | cause to be upright | 449 | 3 / 3 | shape split into 2 senses (cause to be upright 3; tied in a bundle 0); some uses reclassified as affix CAUS; count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| araas | cooked | 97 | 11 | cooked | 364 | 3 / 3 | v1 had merged the variants aras; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| iriwis | across | 98 | 11 | across | 122 | 6 / 11 | shape split into 2 senses (across 6; group of warriors 1); count falls: only tier A/B words with a checked meaning are counted (11 in all tiers) |
| itur | village | 99 | 11 | village | 101 | 7 / 11 | count falls: only tier A/B words with a checked meaning are counted (11 in all tiers) |
| kaahuraar | world | 100 | 11 | the world | 95 | 8 / 9 | count falls: only tier A/B words with a checked meaning are counted (9 in all tiers) |
| kaaʔa | come up | 101 | 11 | emerge | 66 | 10 / 10 | shape split into 2 senses (emerge 10; dance 0) |
| kari | many | 102 | 11 | many | 83 | 8 / 13 | count falls: only tier A/B words with a checked meaning are counted (13 in all tiers) |
| kica | liquid | 103 | 11 | liquid | 643 | 1 / 3 | shape split into 4 senses (water 2; liquid 1; cute 1; marshy 0); count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| rahuur |  | 104 | 11 | spoil | 349 | 3 / 4 | shape split into 2 senses (spoil 3; grieve 2); count falls: only tier A/B words with a checked meaning are counted (4 in all tiers) |
| taʔu | an unpleasant surface | 105 | 11 | unpleasant | 191 | 5 / 5 | shape split into 3 senses (unpleasant 5; bitter 2; unpleasantly 2); count falls: only tier A/B words with a checked meaning are counted (5 in all tiers) |
| ak | ak | 106 | 10 | a certain length | 362 | 3 / 3 | shape split into 2 senses (a certain length 3; their 0); some uses reclassified as affix INTR; count falls: only tier A/B words with a checked meaning are counted (3 in all tiers) |
| arik | horn | 107 | 10 | horn | 159 | 5 / 7 | shape split into 3 senses (standing 20; horn 5; have 3); count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| haturaar | road | 108 | 10 | road | 75 | 9 / 9 | shape split into 2 senses (road 9; trail 1) |
| hiit | feather | 109 | 10 | feather | 103 | 7 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| iis | out of sight | 110 | 10 | out of sight | 76 | 9 / 9 | rank moved with the general changes above |
| kaas | leg | 111 | 10 | leg | 132 | 6 / 7 | shape split into 2 senses (leg 6; crack 0); count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| karaar | belly | 112 | 10 | belly | 108 | 7 / 8 | count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| kituu | complete | 113 | 10 | complete | 64 | 10 / 12 | rank moved with the general changes above |
| kuut | die | 114 | 10 | die | 77 | 9 / 9 | rank moved with the general changes above |
| paa | moon | 115 | 10 | moon | 204 | 4 / 7 | shape split into 3 senses (moon 4; knee 3; elk 0); count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| rikuhc | bird | 116 | 10 | bird | 124 | 6 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| ritku | tail | 117 | 10 | tail | 285 | 3 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| taha | taste good | 118 | 10 | taste | 288 | 3 / 8 | shape split into 2 senses (taste 3; flavor 1); count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| tarahkiis | strong | 119 | 10 | strong | 136 | 6 / 7 | shape split into 2 senses (strong 6; strongly 3); count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| uus | hair | 120 | 10 | hair | 88 | 8 / 10 | rank moved with the general changes above |
| waat | your nephew | 121 | 10 | niece | 357 | 3 / 4 | shape split into 3 senses (up 4; niece 3; dove 0); count falls: only tier A/B words with a checked meaning are counted (4 in all tiers) |
| wiita | male | 122 | 10 | man | 286 | 3 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| aah | be | 123 | 9 | walk | 238 | 4 / 4 | shape split into 2 senses (walk 4; exist 3); count falls: only tier A/B words with a checked meaning are counted (4 in all tiers) |
| acaciks | spider | 124 | 9 | spider | 151 | 5 / 9 | count falls: only tier A/B words with a checked meaning are counted (9 in all tiers) |
| caaka | protruding object | 125 | 9 | stick out | 102 | 7 / 10 | rank moved with the general changes above |
| hat | tongue | 126 | 9 | tongue | 297 | 3 / 6 | shape split into 2 senses (tongue 3; hole 0); count falls: only tier A/B words with a checked meaning are counted (6 in all tiers) |
| hii | and | 127 | 9 | other | 451 | 2 / 8 | shape split into 2 senses (other 2; hii 0); v1 had merged the variants hi; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| ickuus | peeling | 128 | 9 | integument | 284 | 3 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| ihtata | close to | 129 | 9 | close to | 123 | 6 / 10 | count falls: only tier A/B words with a checked meaning are counted (10 in all tiers) |
| kaac | gray | 130 | 9 | gray | 86 | 8 / 11 | rank moved with the general changes above |
| katakus | sitting against | 131 | 9 | against | 109 | 7 / 8 | shape split into 2 senses (against 7; on 2) |
| kitawi | leading | 132 | 9 | lead | 105 | 7 / 9 | rank moved with the general changes above |
| rakaraa | dish | 133 | 9 | dish | 158 | 5 / 8 | count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| ruuc | lying | 134 | 9 | lay down | 65 | 10 / 12 | rank moved with the general changes above |
| taa | deer | 135 | 9 | deer | 211 | 4 / 6 | count falls: only tier A/B words with a checked meaning are counted (6 in all tiers) |
| uuc | lay | 136 | 9 | lay | 78 | 9 / 9 | v1 had merged the variants uc; v2 counts them separately |
| waka | voice | 137 | 9 | voice | 137 | 6 / 7 | count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| aruht | soft | 138 | 8 | soft | 202 | 4 / 7 | count falls: only tier A/B words with a checked meaning are counted (7 in all tiers) |
| askus | one | 139 | 8 | added | 745 | 1 / 1 | v1 had merged the variants asku; v2 counts them separately; count falls: only tier A/B words with a checked meaning are counted (1 in all tiers) |
| awiira | behind | 140 | 8 | behind | 92 | 8 / 9 | rank moved with the general changes above |
| ca |  | 141 | 8 | upright | 125 | 6 / 9 | rank moved with the general changes above |
| hihit | spread | 142 | 8 | spread | 154 | 5 / 8 | shape split into 2 senses (spread 5; mat 0); count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| hurahac | disappear | 143 | 8 | disappear | 94 | 8 / 9 | rank moved with the general changes above |
| huuca | along a stream | 144 | 8 | along a stream | 155 | 5 / 8 | count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| ickur | wool | 145 | 8 | wool | 152 | 5 / 9 | count falls: only tier A/B words with a checked meaning are counted (9 in all tiers) |
| ka | outstanding | 146 | 8 | outstanding | 168 | 5 / 6 | shape split into 3 senses (on 53; outstanding 5; what 0); some uses reclassified as affix ITER; count falls: only tier A/B words with a checked meaning are counted (6 in all tiers) |
| kawat | take out | 147 | 8 | take out | 461 | 2 / 5 | shape split into 2 senses (take out 2; from 2); some uses reclassified as affix DIST; count falls: only tier A/B words with a checked meaning are counted (5 in all tiers) |
| kii | kii | 148 | 8 | strung | 115 | 7 / 7 | shape split into 3 senses (strung 7; here 0; strike 0); some uses reclassified as affix TRANS |
| pahuks | squash | 149 | 8 | squash | 157 | 5 / 8 | shape split into 2 senses (squash 5; flying bug 0); count falls: only tier A/B words with a checked meaning are counted (8 in all tiers) |
| piruus | crooked | 150 | 8 | crooked | 129 | 6 / 8 | shape split into 2 senses (crooked 6; nasal mucus 0) |
| riwii | formed into a ball | 154 | 8 | contracted into a ball | 112 | 7 / 8 | shape split into 3 senses (contracted into a ball 7; curled 1; rounded 0) |
| warus | rabbit | 157 | 8 | rabbit | 138 | 6 / 7 | v1 had merged the variants parus; v2 counts them separately |
| haahka | bank | 163 | 7 | a ditch | 131 | 6 / 7 | shape split into 2 senses (a ditch 6; attached to 2) |
| iika | in the middle | 169 | 7 | in the middle | 127 | 6 / 8 | shape split into 2 senses (in the middle 6; oh my 1) |
| kakus | sitting on | 172 | 7 | sitting in | 133 | 6 / 7 | rank moved with the general changes above |
| karit | rock | 175 | 7 | rock | 87 | 8 / 10 | shape split into 2 senses (rock 8; stone 0) |
| kiiriit | nape | 176 | 7 | nape | 116 | 7 / 7 | rank moved with the general changes above |
| riisaar | chief | 181 | 7 | chief | 135 | 6 / 7 | shape split into 2 senses (chief 6; chiefly 0) |
| taahiis | dry | 184 | 7 | dry | 97 | 8 / 9 | rank moved with the general changes above |
| ikskiic | finger | 201 | 6 | finger | 140 | 6 / 6 | rank moved with the general changes above |
| kiciis | bald | 205 | 6 | bare | 110 | 7 / 8 | rank moved with the general changes above |
| kiripahkis | little | 208 | 6 | little | 141 | 6 / 6 | rank moved with the general changes above |
| kiwatak | fade | 209 | 6 | fade | 142 | 6 / 6 | rank moved with the general changes above |
| takaa | pass | 219 | 6 | downward | 144 | 6 / 6 | shape split into 2 senses (downward 6; down 0) |
| ikita |  | 234 | 5 | astride | 128 | 6 / 8 | rank moved with the general changes above |
| kiriks | bead | 239 | 5 | bead | 134 | 6 / 7 | rank moved with the general changes above |
| raawir | cloth | 245 | 5 | cloth | 150 | 5 / 10 | rank moved with the general changes above |
| riici | knife | 248 | 5 | knife | 67 | 10 / 10 | count rises: occurrences inside compound stems are now recognised |
| waarukstii | holy | 263 | 5 | holy | 113 | 7 / 8 | count rises: occurrences inside compound stems are now recognised |
| waawaktiik | talk | 264 | 5 | talk | 145 | 6 / 6 | rank moved with the general changes above |
| paca | lump | 320 | 4 | a bump | 143 | 6 / 6 | count rises: occurrences inside compound stems are now recognised |
| iita | know | 386 | 3 | know | 114 | 7 / 7 | count rises: occurrences inside compound stems are now recognised |
| ratkahaar | night | 446 | 3 | night | 96 | 8 / 9 | count rises: occurrences inside compound stems are now recognised |
| ahiht | fat | 479 | 2 | fat | 81 | 8 / 14 | count rises: occurrences inside compound stems are now recognised |
| awaahaahkiir |  | 491 | 2 | — | — | — | reclassified as an affix: DIST |
| k | set | 547 | 2 | — | — | — | reclassified as an affix: TRANS |
| wi | along | 716 | 2 | upright | 16 | 33 / 43 | some uses reclassified as affix LOC; count rises: occurrences inside compound stems are now recognised |
| hiir | weed | 836 | 1 | good | 22 | 26 / 41 | shape split into 3 senses (good 26; grass 13; night to elapse 1); count rises: occurrences inside compound stems are now recognised |
| hiir |  | 837 | 1 | good | 22 | 26 / 41 | shape split into 3 senses (good 26; grass 13; night to elapse 1); count rises: occurrences inside compound stems are now recognised |
| u | — | — | — | extending in a line | 26 | 22 / 33 | added: not a root in v1 |
| waa | — | — | — | hill | 89 | 8 / 10 | added: not a root in v1 |
| ciras | — | — | — | leading | 93 | 8 / 9 | added: not a root in v1 |
| itik | — | — | — | go | 126 | 6 / 9 | added: not a root in v1 |
| aahkata | — | — | — | on a vertical bank | 139 | 6 / 6 | added: not a root in v1 |

Rows are limited to roots in the first 150 of either version (and added roots in the v2 first 300); the full v2 inventory is `roots.json`.
