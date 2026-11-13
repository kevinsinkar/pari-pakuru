# Blind re-derivation of Skiri Pawnee morphemes

You are an independent reviewer on a Skiri Pawnee language-revitalization
project. Another analyst has built an inventory of roots and affixes from
Parks's *Dictionary of Skiri Pawnee*. Your job is to work out the same facts
again, from the raw sources only, so the two results can be compared. The
comparison is only worth something if you have not seen the other analysis, so
the rules about which files you may open matter.

## What you are given

A JSON file with a list of **forms** (bare morpheme shapes such as `at` or
`uʔ`) and a `kind`: `"root"` or `"affix"`. You are told nothing about what they
mean. Some forms are homonyms: one shape, several unrelated morphemes.

## Sources you may use

Repository root: the folder that holds this repository (`pari-pakuru`)

- The SQLite database `skiri_pawnee.db`, **read-only**, and only these tables:
  - `lexical_entries` (entry_id, headword, grammatical_class, verb_class,
    stem_preverb, page_number, additional_forms)
  - `glosses` (entry_id, sense_number, definition)
  - `etymology` (entry_id, `raw_etymology`): Parks's printed etymology, e.g.
    `<kaa+at, go inside>`. Pieces are joined by `+`; a `.` joins the parts of a
    compound stem; the text after the first comma is Parks's literal
    translation; UPPERCASE words in it are grammatical labels (NOM, DIM, PL …).
    **Do not use the `constituent_elements` or `literal_translation` columns:**
    they come from an earlier automatic parse whose glosses are unreliable.
  - `paradigmatic_forms` (entry_id, form_number, skiri_form)
  - `examples`
- `extracted_data/grammatical_overview.json` (Parks's Grammatical Overview) and
  `extracted_data/abbreviations.json`.
- The dictionary page PDFs in
  `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/` if you want to check a
  reading.

Use Python at `.venv/Scripts/python` in the repository root.
Open the database with `sqlite3.connect("file:skiri_pawnee.db?mode=ro", uri=True)`.
The console is cp1252: print with
`sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))`, or set
`PYTHONIOENCODING=utf-8`.

## Files you must not open

- anything under `curriculum/` except this instruction file, your forms file and
  your own output file;
- anything under `scripts/` (in particular `scripts/morphology_v2/` and
  `scripts/root_extraction.py`);
- anything under `reports/`.

Do not modify anything except your output file. Put temporary scripts in a
subfolder of your own in the scratchpad directory, named after your batch.

## What to work out for each form

Search Parks's printed etymologies for the form used as a piece (between `+`,
`.` or the ends of the morpheme string; mind optional segments in parentheses,
bound-form hyphens and preverb notes like `(ut...)`). Do **not** count places
where the letters merely occur inside a longer piece or inside a headword. Also
look for dictionary entries whose headword is the form itself.

Then record, per form, one or more **senses**. Two uses belong to the same
sense only if the evidence shows the same meaning; if the glosses fall into
unrelated groups (for example 'grass' and 'good'), record separate senses.

For each sense give:

- `meaning`: a short English meaning, in Parks's own words where possible.
- `kind`: `"lexical"` or `"grammatical"`. For a grammatical sense also give
  `label` (Parks's label such as NOM, DIM, PL, ITER, PREV, LOC, CAUS, DIST,
  PERF) and `position` (`"prefix"`, `"suffix"`, `"inner"`).
- `class`: for lexical senses, your best judgement of one of `"noun root"`,
  `"verb root"`, `"descriptive stem"`, `"locative"`, `"other"`, with the entry
  or evidence it rests on.
- `evidence`: how you know the meaning. Quote up to three printed etymologies
  (with entry_id) where the literal translation makes the meaning clear, and
  name the form's own dictionary entry if it has one.
- `n_words`: how many dictionary entries you found whose printed etymology uses
  the form in this sense (a count from your search; say how you counted).
- `examples`: five entries that use the form in this sense, each as
  `{"entry_id": …, "headword": …, "raw_etymology": …}`. Prefer words where the
  literal translation shows the meaning.
- `shapes`: other shapes you believe are the same morpheme (for example a form
  Parks writes with an optional segment), each with the evidence. Leave empty
  if none.
- `doubts`: anything uncertain: a meaning you could not pin down, uses you could
  not assign to a sense, possible homonyms.

## Output

Write a UTF-8 JSON file (path given in your task) with this shape:

```json
{
  "batch": "roots_1",
  "forms": [
    {
      "form": "at",
      "senses": [
        {
          "meaning": "…", "kind": "lexical", "label": null, "position": null,
          "class": "…", "evidence": "…", "n_words": 0,
          "examples": [{"entry_id": "…", "headword": "…", "raw_etymology": "…"}],
          "shapes": [], "doubts": ""
        }
      ],
      "unassigned_uses": 0,
      "notes": ""
    }
  ]
}
```

`unassigned_uses` is the number of etymologies that use the form as a piece but
that you could not assign to any sense.

Write the file with the Write tool so that `ʔ` is saved correctly, then check
that it parses as JSON.

## When you finish

Reply with one short paragraph: how many forms you covered, which forms you
found to be homonyms, and anything a reviewer should know. Do not paste the
JSON back.
