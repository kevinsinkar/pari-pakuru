# G2 gold annotation: transcribe dictionary entries from the page image

You are building an independent gold record for a Skiri Pawnee morphology
project. For each entry in your batch you read the printed page of Parks's
*Dictionary of Skiri Pawnee* and transcribe what is printed. Your record is
later compared with a database extraction, so accuracy matters more than speed
and you must not look at the database, the JSON dictionary files or any other
extraction. The printed page is the only source.

## Where things are

- Your work list: `curriculum/roots_v2/gold/g2_batches/batch_N.json` (N is given
  in your task). Each item has `entry_id`, `headword`, `grammatical_class`,
  `pdf_file`, `book_page` and `column`.
- Page images: `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/<pdf_file>`
  under the repository root (`pari-pakuru`).
  Read each PDF with the Read tool. Several entries may share a page, so read a
  page once and do all of its entries.
- Write your output to `curriculum/roots_v2/gold/g2_raw/batch_N.json`.

## Reading the page

The PDF gives you a page image and a text layer. The text layer is damaged for
special characters (it shows `™` for the glottal stop and odd letters inside the
phonetic brackets). Trust the image. Use the text layer only to find your place.

How an entry is laid out, in order:

1. **Headword** in bold, possibly with alternates separated by commas, a preverb
   note such as `(ut...)` or `(ir...)`, and a bracket note such as `[+ raar-]`.
2. **Phonetic form** in square brackets. Do not transcribe it.
3. **Class** in italics, e.g. `VT(4)`, `N`, `VD(u)`, `VI(1)`.
4. Optional **braces** with other forms, e.g. `{dist., astaarawarii}` or
   `{comb., asuur-, asuh-}`.
5. **Glosses**, numbered when there are several.
6. Optional **etymology** in angle brackets, e.g. `<as+uʔ, foot + NOM>`.
7. Optional **numbered paradigm forms** `1. … 2. … 3. … 4. … 5. …` (verbs).
8. Optional **examples**, each introduced by a bullet `•`.

Homographs are common: several entries on a page can share a headword. Use the
class, the column and the order on the page to pick the one that matches your
item. If you cannot tell which one is meant, transcribe the best match and say
so in `notes`.

## Transcription rules

- Glottal stop: write `ʔ` (it is printed as a small raised hook).
- Long vowels are printed doubled (`aa`, `ii`, `uu`). Copy them exactly. Vowel
  length errors are the most likely mistake, so look twice.
- Copy `c`, `k`, `s`, `h`, `r`, `w`, `p`, `t` exactly. Do not "correct" anything.
- Inside the etymology keep every `+`, `.`, `-`, parenthesis and preverb note
  exactly as printed.
- When a word is broken across two lines with a hyphen, join it and drop the
  hyphen, **except** inside the etymology: there, write the line-end hyphen as
  `-|` (hyphen followed by a pipe) so the reader can tell it sat at a line break.
- If something is illegible or you are unsure, say so in `notes`. Never guess
  silently.

## What to record for each entry

Write one JSON object per entry with exactly these keys:

```json
{
  "entry_id": "SK-asuqat-p18-0203",
  "found": true,
  "printed_headword": "asuʔat",
  "printed_class": "VI",
  "printed_verb_class": "(1)",
  "printed_braces": "{dist., astaarawarii}",
  "first_gloss": "point one's foot; extend one's leg up or outward (horizontally).",
  "etymology_verbatim": "as+u.at, foot to extend (in a line)",
  "etymology_kind": "analysis",
  "pieces": ["as", "u.at"],
  "literal": "foot to extend (in a line)",
  "aligned_glosses": null,
  "inferred_glosses": [
    {"piece": "as", "meaning": "foot", "basis": "literal"},
    {"piece": "u.at", "meaning": "to extend (in a line)", "basis": "literal"}
  ],
  "paradigm_forms": {"1": "taatasuʔat", "2": "tiisuʔat", "3": "tiisawuuʔ", "4": "iriiraasuʔata", "5": "tiisuhuhta"},
  "notes": ""
}
```

Field by field:

- `found`: `false` if the entry is not on the page. Then fill only `entry_id`,
  `found` and `notes`.
- `printed_headword`: the whole bold headword line as printed, including
  alternates, preverb note and bracket note.
- `printed_class`, `printed_verb_class`: e.g. `"VT"` and `"(4)"`. Use `null`
  for the verb class when none is printed. If two classes are printed
  (`VT(1), VR(1)`), write `"VT, VR"` and `"(1), (1)"`.
- `printed_braces`: the braces verbatim, or `null`.
- `first_gloss`: the first numbered gloss, or the whole gloss if unnumbered.
- `etymology_verbatim`: everything inside the angle brackets, without the
  brackets. `null` if the entry has none.
- `etymology_kind`: one of
  - `"analysis"`: Parks breaks the word into pieces (there is a `+` or `.`) or
    names an underlying form;
  - `"cognate_only"`: only `i.q.` / `cf.` references to other languages or
    words;
  - `"loan"`: a borrowing note (`Engl.`, `from …`);
  - `"none"`: no etymology printed.
- `pieces`: the morpheme string (the part before the first comma) split at
  every `+`, keeping dots, hyphens, parentheses and preverb notes inside each
  piece exactly as printed. `[]` when `etymology_kind` is not `"analysis"`.
- `literal`: Parks's literal translation, i.e. the text after the first comma
  up to any `;`, `cf.` or `i.q.`. `null` if there is none.
- `aligned_glosses`: fill this **only** when the literal translation is itself
  split by `+` into the same number of parts as `pieces` (e.g. `foot + NOM` for
  `as+uʔ`). Then give a list of `{"piece": …, "gloss": …}` in order. Otherwise
  `null`.
- `inferred_glosses`: your own reading of which meaning goes with which piece,
  one object per piece. `basis` is `"aligned"` (copied from `aligned_glosses`),
  `"literal"` (you matched words of the literal translation to the piece) or
  `"unknown"` (the page does not let you tell; then `meaning` is `null`). Do
  not use outside knowledge of Pawnee to fill these: only what this page prints.
- `paradigm_forms`: the numbered forms as printed, as strings keyed `"1"`–`"5"`.
  When a form has two variants separated by `;` or `,`, keep them in one string
  as printed. `{}` if the entry has none. Parks sometimes omits a number; record
  only the numbers printed.
- `notes`: anything unclear, any doubt about which homograph you transcribed,
  anything on the page that looks like a printing oddity.

The output file is a JSON array of these objects, in the order of your work
list, saved as UTF-8.

## When you finish

Reply with one short paragraph: how many entries you transcribed, how many were
not found, and anything a reviewer should know. Do not paste the JSON back.
