# Source-fidelity audit, November 2026: findings

*Run on 2026-11-13 from `prompts/source_fidelity_audit.md`. The audit changed
no data: the 649 input hashes taken at the start were identical at the end.*

## The short answer

**The dictionary entries are a good copy of the printed dictionary with a
known list of faults; the tables that an AI model read from page images are
not yet a good copy.** Of 4,244 dictionary entries, 305 have a difference from
the page in a Pawnee form or in meaning, and every one is now listed with the
printed value beside it. Of the 770 verb forms of Parks's Appendix 1, the
answer key the conjugation engine is scored against, 152 differ from the page.

Nothing has been fixed. The audit proposes 2,250 changes
(`proposed_fixes.jsonl`); 827 of them carry a value that can be applied as it
stands, and the rest need a person.

## What this audit can and cannot show

It shows whether the stored copy matches the printed sources. It cannot show
that a printed form is right, that a gloss is how a speaker would put it, or
that anything the project's engines generate is correct. It does not replace
review by a speaker or a linguist.

## What was checked, and against what

| Stored data | Second reading | Coverage |
|---|---|---|
| Skiri-to-English entries: headword, IPA, class, senses, etymology, verb forms, examples, cognates (4,244 entries, 50,736 fields) | The PDF's text layer, decoded with a character table verified against the printed glyphs | Every field, and every printed stretch |
| The differences found there (900) | Page images: 369 crops read blind by readers who saw only the images | All differences in Pawnee forms, wording, class and missing text; a sample of 30 from each large mechanical family |
| Appendix 1 (770 verb forms), Appendix 3 (kinship), chapter 4 (grammar), chapter 3 (sound changes) | Page images read blind, tile by tile | Every page |
| Appendix 2 (irregular roots) | The page image, read before the stored copy was opened | The whole page |
| Abbreviation list (164 rows) | Its text layer | Every value |
| English-to-Skiri section (6,431 printed entries) | The PDF's text layer | Every row and cross-reference; no images read |
| Blue Book | The scan, read blind from crops | The 93 Blue Book-only dictionary entries and a random 60 of the other 890 forms |

Not checked: chapters 2 and 5 of the front matter (nothing stored comes from
them), the remaining Blue Book forms and the lesson texts (the `lessons` table), and everything the project generated
itself (respellings, tags, confidence scores, the curriculum).

## How far to trust the audit itself

- **It catches planted errors.** 510 errors of 17 kinds (a changed consonant,
  `b` for `h`, a dropped accent or glottal stop, a shortened vowel, a deleted
  sense, example or entry, a truncated translation, a changed class) were
  planted in a copy of the database. The comparison reported all 510. The
  first run reported 466: it missed word-final glottal stops and truncations,
  and was corrected before any result was used.
- **The page agrees with the text layer.** All 303 differences that were read
  from a crop show on the page what the text layer says, not what the
  database says. Six further "differences" were faults of the comparison (the
  stored value was right) and were dropped.
- **Where database and text layer agree, so does the page.** 60 fields on
  which they agree were read from crops: 60 of 60 agree. That bounds the rate
  at which both are wrong together at about 5% with 95% confidence; the true
  rate is probably far lower.
- **The blind readers were checked.** For Appendix 1, 40 of the 152
  differences were looked at a third time at high zoom: the page showed the
  blind reading 40 times of 40.
- **The text layer is not independent of the database.** The AI parse was made
  from the same PDFs, and its output carried the text layer's stand-in
  characters. So agreement between the two says nothing about how those
  characters are decoded. That is why the character table was verified
  first, on glyphs cut out of the pages, for every character and every font.

## Findings

### 1. The character table (stage 1)

All 52 (font, character code) pairs of the text layer were read from the
printed glyphs. Sixteen had been decoded wrongly, or never.

- **The phonetic font has a regular grid of twelve accented vowels:** tense
  á í ú and à ì ù on the second half of a long vowel, lax ə́ ɪ́ ʊ́ and ə̀ ɪ̀ ʊ̀
  on a short one. The lax i with an accent has the hooked foot of the lax i;
  the tense one does not. The distribution over every occurrence agrees: the
  lax codes never follow a plain vowel letter (0 of 1,257; 0 of 834; 0 of
  313), the tense ones nearly always do.
- **Stored differently, everywhere** (a convention, not an error; a decision
  for the project): `à` for printed ə́ (579 entries), `í` for printed ɪ́ (387
  entries), a hyphen for the printed syllable dot, a bullet for the printed
  dash at the edge of a form that cannot stand alone.
- **Wrongly stored in single forms:** printed ə̀ is stored as `á` in two forms,
  and ʊ̀, ɪ̀, ʊ́ are missing their accent in twelve.
- **In words cited from other languages** the code `ó` is printed š, `Ý` is é,
  `í` is ó, and five rarer codes are ą, ą́, į, ž and a raised i. 162 stored
  cognates and etymologies have the raw code: Arikara *sáhnió* is printed
  *sáhniš*, *sčÝó* is *sčéš*.

### 2. The dictionary entries (stages 2 and 3)

4,244 printed entries, 4,244 stored. 49,443 of 50,736 fields are identical to
print (97.45%). 9,759 further mismatches are formatting noise under two named
rules (`s2e_summary.json`). 894 are real differences:

| What | Count | Example |
|---|---|---|
| Verb forms | 22 | *kituus* form 2 stored *tikituum*, printed *tikituus*; *karusik* forms 3 and 5 lack *-ar-* |
| IPA: letters or accent | 39 | 14 are not Parks's IPA but the spelling cut into syllables (`[•a-wi-hu-ra(h)•]` for printed `[–ə·wɪ·hʊ·rə(h)–]`); 12 lack an accent |
| IPA: the space between two words lost | 15 | |
| Headwords | 30 | 22 lack the printed bracket note (`[+ raar-]`, `[+ ruu-, i-]`, `[+ neg.]`); *wiicat k* for *wiicatk* |
| Combining forms | 16 | *huukiwihka haah-* for *huukiwihkahaah-* |
| Example sentences, Skiri | 8 | |
| Cognates | 102 | mostly the stand-in characters above |
| Etymologies | 146 | stand-in characters (82); a hyphen and space kept from a printed line break (34) |
| English wording | 37 | *toothed-edge* for *tooth-edged*; a printed misprint silently corrected |
| Printed text the database lacks | 71 | 12 IPA forms (including all nine entries listed as having none), about 15 examples, the derived stems printed under ten bound stems, qualifiers such as "(personal name)" and "(formerly)" |
| Labels of extra forms (*comb.*, *dist.*) | 4 | |
| Class | 9 | nine kin terms stored N-KIN where the page prints N (the project's own reclassification) |
| Entries | 2 | printed *kusisaar* "(impf. only) play", book page 451, is not stored; stored `SK-aakaqa-p351-3592` is not a headword in the book |
| Left or right column | 393 | the stored label is wrong for 9% of entries; nothing uses it |

305 entries have at least one difference in a Pawnee form or in meaning.

No page number is wrong: 3,510 entries carry the page file number and 733 the
book page (the mixed convention is a known open item).

### 3. The appendices and front-matter chapters (stage 4)

| Source | Compared | Differ | What kind |
|---|---|---|---|
| Appendix 1, verb conjugations | 770 forms | **152** | accents the page does not have (the first verb is stored with about 60), vowels dropped or doubled, a syllable missing, and one block of eleven rows shifted by one |
| Appendix 2, irregular roots | 27 cells | 3 | *burii-waa* and *burii* are printed *hurii-waa* and *hurii*; a singular stem stored where the cell is empty |
| Appendix 3, kinship | 30 possessor forms, 41 verb forms | 4 | *asaas*, *atipaat*, *apaat*, *ataati* are printed *asas*, *atipat*, *apat*, *ataat*. The JSON file also lacks the five rows of book page 543 |
| Chapter 4, grammatical overview | 797 Skiri words | 85 | **34 have a `b` where the page has an `h`** (*-busuukuʔ* is *-husuukuʔ*, *icaabiks* is *icaahiks*); the rest an accent, a vowel or a glottal stop |
| Chapter 3, sound changes (the 24 rules' examples) | 138 words | 6 | three surface forms lack a final glottal stop; *ahibt* is *ahiht* |
| Abbreviations | 411 values | 4 | *raar-/rab-* is *raar-/rah-*; *witii-* is *witi-* |

The `b` for `h` misreading that produced *-biriʔ* was not a single slip. In
the book's italic type the h has a foot that curls inward. It occurs 39 more
times across four of these files. A check that needs no image now finds every
stored Skiri form with a letter the language does not have
(`scripts/source_audit/alphabet_check.py`).

**What rests on these tables.** The conjugation engine's 90.3% (695 of 770)
is agreement with a copy of Appendix 1 that has 152 wrong forms; the figure
has to be measured again after the fixes, and may go up or down. The
possession engine reads the kinship forms. The sound-change tests use the
rule examples.

### 4. The English-to-Skiri section (stage 6)

- **The database's English index is an old copy.** `english_index` and
  `cross_references` were imported from the file as it was before cleaning:
  77.7% of their fields match print, 3,986 IPA forms are not in Parks's
  notation (`[pét.ki]`), 177 hold raw stand-in characters, and 244 Skiri terms
  lack their final glottal stop. The remedy is to re-import them, not to fix
  rows.
- **The current JSON** (`english_to_skiri_linked.json`) matches print in 95.9%
  of 33,231 fields. Its 1,090 differences: about 400 placeholders stored as
  values ("N/A", "[cross-reference]"), 244 cross-reference terms with spaces
  inside the word (*ka ta hurah* for *katahurah*), 161 printed Skiri terms it
  does not account for, and 25 printed English headwords it lacks, twelve of
  them in a row on page file 278 (*weather to change* to *Welsh pony*).

### 5. The Blue Book (stage 5)

**The stored Blue Book forms were taken from the OCR text of the scan, and the
OCR text is a poor copy.** Compared with the scan's OCR layer the stored forms
match 982 times out of 984, which only shows where they came from. Read from
the scan itself:

| | Read | Same as the scan | Accent mark missing | Letters differ | Crop missed the form |
|---|---|---|---|---|---|
| Random sample of the other stored forms | 60 | 9 | 41 | 9 | 1 |
| Blue Book-only entries with a printed form on record | 48 | 20 | 22 | 3 | 3 |
| Blue Book-only entries with no printed form on record (headword compared after undoing the respelling) | 45 | 17 | 20 | 1 that is an apostrophe only | 3, and 4 unclear |

- **The Blue Book prints an accent on the stressed vowel** (*tí kaats*,
  *paréku'*, *rasítu'*). The OCR text has none, so no stored Blue Book form
  has its accent. About two forms in three are affected.
- **About one form in seven has a wrong letter** (9 of 59; with a sample this
  size the true share is between about 7% and 27%). The OCR read accented
  vowels as other letters: *ú* as *ti* (*ktitasut* for *kútasut*, *stiruks* for
  *súruks*), *á* as *d* (*pakd* for *paká*).
- **Three dictionary entries are built on a misread form:** `BB-had-0010`
  "yes", stored from *had'*, printed *haú'*; `BB-cktiskakusu-0003` "chair",
  from *tsktis•kakusu'*, printed *tskús•kakusu'*; `BB-tikuwtitiku-0083`, from
  *ti•kuwtitiku'*, printed *ti•kuwútiku'*.
- **The headwords of the 93 Blue Book-only entries are respelled** into
  Parks's letters (*paisic* for printed *paisits*); 5 are identical to a
  printed form, and 45 have no printed form on record at all.
- About 890 stored Blue Book forms were not read from the scan.

## The ten findings that matter most

1. Appendix 1 as stored has 152 wrong forms in 770, and the engines are scored against it.
2. Twenty-two dictionary verb forms differ from the page by a letter, a vowel or a syllable.
3. Fourteen entries carry an "IPA" that is not Parks's but the spelling cut into syllables, which breaks the rule that IPA is never generated.
4. `b` for `h`: 39 more forms like *-biriʔ*, in Appendix 2, the grammar chapter, the sound-change rules and the abbreviations.
5. The kinship forms the possession engine serves have four errors (*asaas*, *atipaat*, *apaat*, *ataati*).
6. The database's English index is an uncleaned old copy.
7. One printed entry is missing and one stored entry does not exist in the book; twelve IPA forms and about fifteen examples that are printed are not stored.
8. Words cited from other languages are misdecoded in 162 places (*sáhnió* for *sáhniš*).
9. The stored IPA writes four printed symbols another way in every form: ə́, ɪ́, the syllable dot, the edge dash.
10. The Blue Book data came from the OCR text: no stored form has the accent the book prints, about one in seven has a wrong letter, and three dictionary entries are built on misread forms (*had'* for *haú'* "yes").

## Not settled

- **Line-end hyphens.** Where the database kept a hyphen and a space from a
  printed line break (*hurii- waawikaʔuk*), the page cannot say whether the
  hyphen is a line-break hyphen or part of the form: it stands at the end of
  the line either way. 43 such places are listed without a proposed value. In
  nearly all of them the hyphen is a line break.
- **Chapter 4's 51 differing words** were matched to the blind reading by
  likeness, not by position on the page, because the stored chapter is a
  paraphrase. Each needs a person to look at the page. The 34 `b` for `h` are
  certain.
- **112 of Appendix 1's 152** rest on the blind reading alone. Every third
  look taken agreed with it; the review page shows each with its crop.

## Decisions that are the project's to make

1. Store Parks's symbols exactly (ə́, ɪ́, the syllable dot, the edge dash), or keep the present convention and say so where IPA is shown.
2. Whether the nine kin terms stay N-KIN (the project's class) or go back to N (Parks's).
3. Whether the Blue Book-only entries keep their respelled headwords.
4. Where the bracket notes on 22 headwords belong.
5. Whether to keep `column_position` at all.

## What to do next, in order

1. Review the Appendix 1 fixes on the review page and apply them; then measure the conjugation engine again.
2. Apply the single-form fixes to dictionary verb forms and IPA (they carry a proposed value).
3. Fix the 39 `b` for `h` forms and the kinship forms.
4. Repair the English-to-Skiri JSON's placeholders and spaced terms, then re-import the English index.
5. Add what the database lacks (the entry, the IPA forms, the examples).
6. Take the decisions above, then re-decode the IPA in one pass.
7. Correct the three Blue Book entries built on misread forms; then read the rest of the Blue Book against the scan (about 890 forms), restoring the accents.

How to review and apply: `README.md` in this folder.

## Cost

156 images were read by a model. Twelve sub-agents did the blind readings, at
roughly 230,000 tokens each (2.78 million in all). No token estimate was given
before they were started, only a count of crops; that was a mistake, and the
cost per reader is recorded here so that the next run can be planned. The comparisons with the text layer
cost no model time and can be re-run after any change in a few seconds.
