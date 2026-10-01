# Data Construction Audit — Flashcards & Static Site Pipeline

**Date:** 2026-10-01
**Scope:** DB → `web/flashcards.py` → `scripts/build_static_site.py` → published `docs/` site.
Focus: methodology and execution integrity, with emphasis on IPA preservation and cultural
sensitivity. Upstream OCR/normalization was audited separately (2026-09-01).

All counts below were verified by direct queries against `skiri_pawnee.db` (4,343 entries),
the generated flashcard sets (24 weeks / 387 cards), and the built `docs/` output.

---

## Verified sound (no action needed)

- **Pitch survived respelling with zero loss.** 1,542 entries carry pitch accents in
  `phonetic_form`; in **all 1,542**, the respelled `simplified_pronunciation` encodes the
  pitch as uppercase syllables. No entry lost pitch in the respelling step.
- **"(pitch not marked)" labeling is honest.** 156 of 387 flashcards show this label; in
  all 156 the source IPA genuinely carries no accent. The pipeline is not hiding data.
- **Special characters survive export.** `ʔ`, `č/Č`, circumflex vowels, and `'` all round-trip
  through `dictionary.json` (`ensure_ascii=False`) and the UTF-8 HTML pages.
- **Orthography is clean.** Only 4 headwords contain consonants outside the Pawnee
  inventory; 3 are the legitimate `[+ neg.]` notation, 1 is a Blue Book spelling (see C3).
- **Every flashcard carries IPA on its back.** 0 of 387 cards lack `phonetic_form`.

---

## A. High-priority concerns

### A1. The public static site drops the IPA almost entirely
`export_dictionary_data()` omits `phonetic_form` from `dictionary.json`, even though
**4,334 of 4,343** DB entries have it. Static entry-page generation is disabled
(commented out in `main()`), so on the published site the IPA appears **nowhere except
flashcard backs** — search results show only the respelled pronunciation. For a project
whose stated priority is preserving the IPA, the public artifact is the one place it is
missing. **Fix:** add `phonetic_form` to the JSON export and render it in
`search.js` result cards (and/or re-enable entry pages).

### A2. Scholarly provenance is stripped from the public site
`page_number` (present on **4,250** entries) is not exported; neither cards nor search
results cite where in Parks a form comes from. `usage_notes` on **485** glosses are also
dropped. For a culturally significant scholarly source, every published form should be
traceable to its attestation. **Fix:** export `page_number` (+ `source`) and show a
"Parks p. N" citation.

### A3. Definitions are silently truncated at 120 characters
`web/flashcards.py` cuts definitions to 117 chars + `"..."`. Six cards are affected, and
they are disproportionately the culturally weighty ones — the **Pitahawirata band name**
explanation and the **Kitkahahki village name** etymology are both cut mid-sentence.
Truncating band-name etymologies on a heritage learning deck is a meaning-distortion
risk, not a cosmetic one. (The code comment says "skip entries with very long
definitions" but the code truncates instead — comment and behavior disagree.)
**Fix:** show full definitions (cards scroll fine) or at minimum never truncate
proper-name/etymology entries.

### A4. Polysemy flattened to sense 1
**56 of 387 cards** belong to entries with multiple senses in `glosses`, but only
sense 1 is shown with no indication others exist. The static search UI likewise renders
only `glosses[0]` although all senses are exported. This repeats the polysemy risk
already flagged in the dedup work. **Fix:** add a "+N more senses" marker or render all
senses.

---

## B. Medium-priority concerns

### B1. Respelling generation bug: stray `?` around variant slashes — 69 entries
Entries with slash variants have corrupted respellings, e.g.
`acikstarahkiis/kis` → `uh-chihks-tuh-duhh-kees?/?kihs` (should be `kees / kihs`).
69 DB entries affected; 1 reaches the flashcards (`rawa, nawa` → `DUH-wuh / ?N?UH-wuh`),
where the stray `?` additionally breaks the pitch-highlight regex (`[A-Z][A-Z']+` cannot
match the interrupted uppercase run, so its pitch styling is lost on display — the only
such case in the DB). This is a bug in the respelling generator's variant handling.
**Fix:** regenerate these 69 respellings; add a validation rule rejecting `?` in
`simplified_pronunciation`.

### B2. Two IPA conventions coexist; bullet artifacts shown to learners
2,526 entries (58%) have bullet-wrapped IPA (`[•kaa-ʔə•]`), 1,808 have plain accented
IPA (`[kaá-ʔə-…]`). The split is almost perfectly grammatical: bullets = verbs
(2,234 of 2,526, plus LOC), accents = nouns/adverbs. This strongly suggests Parks's
citation convention — verb *roots* are cited without pitch because pitch surfaces on
inflected forms — rather than OCR diacritic loss. But the `•` characters themselves are
print/OCR artifacts, and **105 of 387 flashcards display them verbatim**. Learners see
two unexplained transcription styles. **Fix:** verify the convention against the print
source, then strip the bullets at display time (keep them in the DB field or
`raw_entry_json` for fidelity) and add a note to the flashcard guide explaining why verb
roots show no pitch.

### B3. Blue Book entries bypass orthographic normalization
All **93** `source='blue_book'` entries have `normalized_form = NULL`, so BB spellings
appear as-is beside Parks-respelled forms — e.g. Week 1 shows `hadʔ` ("yes"), which uses
the Blue Book's `d` for the r-flap where Parks writes `r` (its own IPA is `[•hərʔ•]`).
Nothing on the card tells the learner which orthography they are looking at, in a deck
that teaches spelling. **Fix:** either derive Parks-convention normalized forms for the
93 BB entries or badge BB-orthography cards explicitly.

### B4. Learner progress is keyed to unstable week numbers
`generate_all_sets()` recomputes the curriculum from the live DB on every build. Week
numbers and set membership shift whenever entries, tags, or BB attestations change —
but learner progress lives in `localStorage` under `fc-progress-week-N` with entry-id
lists. After any DB change, progress silently misattaches to different weeks, and
`known/missed` lists can reference entries no longer in the set (counts can exceed the
new total). For a static site rebuilt on every deploy, this *will* happen. **Fix:**
freeze the curriculum as a versioned data file (e.g. `data/flashcard_sets.json`
committed once and only changed deliberately), and key progress by category+entry-id
rather than week number.

### B5. Cultural categories are curated through an English lexical lens
Category membership is decided by English keyword matching on definitions, patched with
hand-tuned reject lists ("jesus", "baloney", "wolves (standing)" …). This is pragmatic,
but it classifies *Pawnee* cultural domains by their *English* gloss vocabulary, and the
reject lists are unreviewable ad-hoc accretions. Misfiled or wrongly excluded entries are
likely and invisible. **Fix (methodological):** treat the current filters as a bootstrap;
have the resulting 387-card curriculum reviewed as a flat list by a speaker/
community reviewer, then freeze it (which B4 requires anyway) so curation becomes an
editorial act rather than a regex side-effect.

### B6. "Ceremony & Sacred" week needs community sign-off
Week 20 puts sacred-bundle terms (`taahaaruʔ`, `taaraaruʔ`, `raaʔiksuʔ`), Deer Dance,
War Dance, and doctor/healer vocabulary into a public, gamified beginner deck. All are
published in Parks, so this is not a data problem — but whether ceremonial vocabulary
belongs in casual flashcard drilling is a cultural-protocol decision that belongs to the
Pawnee Nation, not to a selection heuristic. **Recommendation:** hold Week 20 out of the
public static build until it has been explicitly reviewed and approved.

---

## C. Low-priority notes

- **C1.** Nine `Ø` (null verb root) entries render a bare `Ø` headword in search results
  with no explanation. Legitimate Parks notation, but confusing learner-facing; worth a
  tooltip or exclusion from search.
- **C2.** Nine entries have no `phonetic_form` at all (list in audit queries; includes
  `kiraar`, `pahuks`, `wakta/taa`). Worth back-filling from the print source.
- **C3.** "Word of the Day" is frozen at build time (currently shows "Sep 12") — on a
  static site this mislabels stale content as daily. Either compute it client-side from
  the date, or relabel ("Featured word").
- **C4.** `base.html` loads `search.js` twice (head + body).
- **C5.** `_fetch_greetings` joins `function_words` to `lexical_entries` on bare
  `headword` equality — homonyms would attach the wrong entry row. No bad case observed
  in the current 387 cards, but the join is unsound in principle.

---

## Suggested order of work

1. ✅ **DONE 2026-10-01** — A1 + A2: `phonetic_form`, `page_number`, `source`, and gloss
   `usage_notes` now exported to `dictionary.json`; `search.js` renders IPA, all senses,
   and a Parks/textbook citation; flashcard backs carry the citation.
2. ✅ **DONE 2026-10-01** — B1: 68 corrupted respellings regenerated from IPA in both the
   DB and the source JSON (`scripts/fix_respelling_artifacts.py`; DB backup taken).
   Generator patched: `n` added to the consonant map, Parks stem-alternation `/` passes
   through verbatim. Note: the 69th hit, `BB-ka-0021` ("ka?"), is the Blue Book yes/no
   question particle — its `?` is part of the form, not corruption. Left as-is.
3. ✅ **DONE 2026-10-01** — A3 + A4: definition truncation removed (card faces scroll);
   previously-cut Pitahawirata/Kitkahahki definitions verified complete; 56 multi-sense
   cards now show "sense 1 of N".
4. B4 + B5 — freeze the curriculum to a reviewed, versioned file.
5. B2 + B3 — display-layer IPA cleanup + BB orthography labeling (after print-source check).
6. B6 — community review of Week 20 before (re)publishing it.
