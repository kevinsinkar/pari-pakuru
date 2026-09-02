# Extraction & Modern-Spelling Audit — 2026-09-01

> **STATUS UPDATE (same day):** Issues 1–5 and 7 below have been **FIXED** via
> `scripts/fix_audit_issues.py --apply` (changelog: `reports/fix_audit_issues_report.txt`;
> backups in `~/.pari_pakuru_backups/*_20260901_173320.*`). Summary of what was applied:
> - **#1 c→č:** ts-aware disambiguator in `respell_and_normalize.py` (+ capital Č support);
>   60 `normalized_form` values corrected in JSON + DB, incl. repair of previously
>   *misplaced* č (e.g. `Cawîrikiripački` → `Čawîrikiripacki`). 0 under-conversions remain.
> - **#2 glosses:** table migrated (UNIQUE dropped, sense_number nullable); 23 gloss rows
>   reinserted for the 7 victims, sub-senses share their parent number (2a/2b → 2).
>   `DB/schema.sql` updated. FTS rebuilt.
> - **#3 phonetics:** 23 of 32 recovered from the PDF page index (skeleton-validated) with
>   pronunciations generated; 9 remain for manual review (list in changelog — the Ø entry
>   plus 8 whose nearby bracketed form belongs to a neighboring entry).
> - **#4 OCR artifacts:** 227 replacements across E2S + S2E (blanket in phonetic fields,
>   vowel-context-only `÷`→`ː` in etymology/cognates). 47 non-vowel-context `÷` left
>   deliberately (Arikara cognate citations where `÷` may not be a length mark).
> - **#5 examples:** `’`→`ʔ` normalized, leading `•` stripped, 14 doubled dedup rows
>   deleted; 88 Blue Book dialogue examples relabeled `source='blue_book'`.
> - **#6 hyphens:** joined in 315 paradigm forms (JSON + DB). Example-text hyphens left
>   alone (compound numerals are legitimate); 78 flagged in changelog for later review.
> - **#7 drift:** 44 phonetic brackets restored in JSON; 9 N-KIN classes backported to
>   JSON; scope doc script name corrected. JSON↔DB now diff-clean on all audited fields.
>
> Still open: the AI-vs-print paradigm-form doubt, gloss-qualifier truncations, the 47
> unresolved cognate `÷`, 78 example-hyphen candidates, and the 9 unrecovered phonetics.
>
> **SECOND-METHOD CROSS-VALIDATION (same day, later):** all 4,273 phonetic forms were
> cross-checked against an independent extraction path — the PDF's embedded text layer
> (pdftotext, `reports/_s2e_page_index.json`), which preserves IPA and pitch accents.
> Initial agreement 96.7% exact. The disagreements decomposed into: 123 entries where
> the AI extraction had degraded to plain ASCII while the text layer preserved the true
> printed IPA (ə/ɪ/ʊ/č/accents), 3 accent-only gaps, 4 reviewed d=1 slips (dropped
> long-vowel letters, headword-corroborated), 9 alignment-noise conflicts, and 1 case
> where the DB was richer. `scripts/upgrade_phonetics_from_textlayer.py --apply`
> adopted the 130 safe upgrades (plain-skeleton-identical, strictly richer only) and
> regenerated 15 normalized_forms + 36 pronunciations — the 15 spelling corrections
> were exactly the earlier c-context-rule "exceptions" (paca→pača, icis→ičis...),
> confirming those were extraction artifacts. **Post-upgrade: 99.76% exact agreement**
> between the two independent methods (4,194/4,204 compared; 9 residual conflicts are
> regex alignment noise, listed in `reports/_crossval_phonetics.json`), and the
> rule-based modernizer now reproduces attested normalized_forms at 99.84%.
> Accent-mark confidence, previously the weakest link, is now second-source-verified.

Scope: targeted (not full-scale) audit of (1) PDF → JSON → SQLite extraction fidelity and
(2) the old-spelling → modern-spelling (`normalized_form`) conversion. Method: 50-entry
stratified S2E sample verified line-by-line against PDF page text, 33-entry E2S sample
(11 spot-verified against PDF), plus deterministic full-corpus re-derivation and
JSON↔DB diff checks. Read-only — no production data was modified.

---

## Verdict

**The extraction is in very good shape.** Every one of the 47 sample entries whose PDF
chunk could be located matched the source on headword, phonetic form, grammatical
class, verb class, glosses, etymology, paradigmatic forms, and examples — including
correct separation of homonyms (e.g. the two `iripiitik` entries VP(4) vs VT(4), and
`tiirahk` VL vs VT(wi)). E2S→S2E linking is fully sound: 5,132 linked subentries,
0 dangling IDs, 100% headword-consistent. E2S spot checks against the PDF all matched.

**The modern-spelling conversion is rule-correct.** An independent re-implementation of
the documented rules (aa→â, ii→î, uu→û, c→č via phonetic disambiguation, ʔ→')
reproduced the stored `normalized_form` for **4,273/4,273 entries with zero
mismatches**; no residual `aa/ii/uu` or `ʔ` anywhere. Consonant-skeleton consistency
between headword and phonetic form: only 1 explainable mismatch corpus-wide
(`(r)aapuh` — optional (r) notation). Simplified pronunciations spot-checked correct
against the mapping tables.

---

## Issues found (fix later)

### 1. c→č under-conversion — ~50 entries keep `c` where the word is pronounced č  ⚠ most important
The disambiguator (`respell_and_normalize.py: extract_c_pattern_from_phonetic`) counts
only literal `c`/`č` characters in the phonetic form, but Parks writes the /ts/
pronunciation as **`ts`** in phonetics (e.g. headword `cikic` = [čí-kɪts]). Headword
c-count (2) ≠ phonetic c-count (1) → disambiguation skipped → `normalized_form`
stays `cikic` when it should be `čikic`. **55 DB entries** currently show a č-less
modern spelling despite a č in their phonetic form (e.g. `cikic`, `cuskiic`,
`acikstiihac`, `Caahiksicaahiks`).
**Fix:** when scanning the phonetic form, treat `ts` as one `c` token; counts then
match and the existing positional logic works unchanged. (Caveat: verify no genuine
/t.s/ cross-syllable clusters exist — scan for `t-s` across syllable boundaries first.)

### 2. Gloss loss in DB import — 7 entries silently lose senses
`glosses` has `UNIQUE(entry_id, sense_number)` + `sense_number NOT NULL`. Glosses
parsed with duplicate numbers (Parks "2a./2b." sub-senses) or null numbers are
silently dropped on import. Confirmed content loss, e.g. `akaaruq` (JSON: 3 senses
incl. "tipi cover", "canvas/tarp" → DB: 1), `caahikspahat`, `cahkahaaruq`,
`iriwaawarik` (VP), `pakstariipiiruq`, `raakickuq`, `kictakaahak`.
**Fix:** drop the UNIQUE constraint (or add a sub-sense letter column) and allow
null→auto-numbered senses; re-import glosses for these 7 entries.

### 3. 32 entries missing `phonetic_form`; ~30 recoverable from the PDF
E.g. `piikawaa` — PDF p460 plainly shows `[pii-kà-waa]` but extraction returned null
(so no simplified pronunciation, and c/č + circumflex disambiguation ran without
phonetic support). A grep of the PDF page text finds bracketed phonetics for ~30 of
the 32. **Fix:** one-off recovery script matching headword→bracketed form in the page
index, then regenerate `simplified_pronunciation`/`normalized_form` for them.

### 4. OCR-artifact fixes were applied to S2E only, not E2S
`english_to_skiri_linked.json` still contains **207 `÷`** (should be `ː`) plus
stragglers (`ˆ`×4, `‹`, `Ò`, `ç`, `ø`×9) — the `fix_priority_issues.py` pass never ran
on E2S. Effect: 197/5,016 linked pairs (3.9%) disagree with their S2E phonetic solely
due to `÷`. S2E itself still has 59 `÷` confined to `etymology.raw_etymology` and
`cognates[].form` (phonetic forms are clean). DB phonetics are clean.

### 5. Dedup left doubled near-duplicate examples in 25 entries
The p2/p71 dedup merged examples from both page-copies; they differ only by glottal
character (`’` U+2019 vs `ʔ`) or hyphenation ("grand-mother"/"grandmother"), so they
weren't caught as duplicates. E.g. `SK-kaaqa-p2-0002` has "tarahkaa’aahu’" AND
"tarahkaaʔaahuʔ". 16 example rows in the DB use `’` instead of `ʔ`.
**Fix:** normalize `’`→`ʔ` in examples, then dedup (entry_id, normalized skiri_text).

### 6. Line-break hyphens leak into extracted fields (minor, systematic)
Parks's end-of-line hyphenation occasionally survives joining: paradigmatic forms
(`iriiraripi-haahpiru`, `irii-raacikskaapaakisu`) and etymology (`piira+kiripah- kis`).
Cosmetic in etymology; in paradigm forms it corrupts the inflected string, which
matters if those forms feed the stem extractor. Worth a corpus scan for `\w- \w` and
`\w-\w` where the hyphen sits at a former line break.

### 7. Small stuff
- 44 entries: `phonetic_form` in JSON lost its surrounding `[...]` brackets (DB has
  them) — cosmetic drift between JSON and DB.
- JSON↔DB drift, DB ahead: 9 entries reclassified `N`→`N-KIN` in DB only. The JSON
  is no longer the single source of truth; decide which is canonical.
- Occasional gloss-qualifier truncation: e.g. `uʔat` gloss 1 drops ", as a bird or an
  airplane"; `acikstaraa` drops "as what to do". Content-lossy but rare and mild.
- One E2S gloss OCR artifact: "g o a t ." (letter-spaced).
- A few examples carry a leading "• " in `skiri_text` (e.g. `uʔat`).
- Scope doc names the DB import script `scripts/import_to_db.py`; it's actually
  `DB/import_to_sqlite.py`.

## Doubts noted for later exploration (not verified either way)
- **AI-transcription vs pdftotext divergence:** `asuuktik` form 4 reads
  `iriiriirasuuktika` in JSON but `iririirasuuktika` in the extracted page text. The
  JSON version looks more linguistically regular (irii- prefix), so the AI may have
  "corrected" the source — or read it right where pdftotext dropped a character.
  A handful of paradigm forms may differ from print in this invisible way; only a
  check against the page *images* would settle it.
- **3 sample entries** (`kicka`, `karitihit`, `wiruuhuur`) couldn't be chunk-verified
  because the located page hit was a running header; their data is self-consistent
  but unverified against print.
- The 2 of 32 missing-phonetic entries whose PDF grep hit looks wrong (`kaaks`,
  `kawiʔat` matched neighboring words) need manual PDF inspection.

## What this audit did NOT cover
Appendix extractions (conjugation paradigms, kinship), Blue Book extraction accuracy,
semantic tags, confidence scores, and the derived-stems/cross-references tables.
