# Baseline: state of the existing tools before any v2 work

Recorded 2026-11-12, before any v2 code was written. All commands were run from
the repository root with `.venv/Scripts/python`.

| Check | Command | Result |
|---|---|---|
| Sound-change engine | `scripts/sound_changes.py --test` | **11 / 11 pass** |
| Person/mode derivation | `scripts/person_forms.py --validate-appendix` | **27 pass, 0 fail, 1 skipped** |
| Stem extractor | `scripts/stem_extractor.py --validate` | **1,908 / 2,201 exact (86.7%)**, 40 close, 253 miss |
| v1 curriculum spec | `scripts/build_root_curriculum.py --check` | **0 unresolved ids** |

No baseline check fails, so the v2 work builds on these tools.

## One environment note

`person_forms.py --validate-appendix` crashes with `UnicodeEncodeError` when it
prints `ʔ` to a cp1252 console. This is a console-encoding problem, not a logic
failure: with `PYTHONIOENCODING=utf-8` set it runs to completion with the result
above. The script was left unchanged. Every v2 script writes through
`sys.stdout.buffer`, so none of them depends on that variable.

## What the baseline tells v2

- The sound-change engine is tested on 11 textbook cases only. That is thin
  cover for 24 rules, so v2 measures the engine again on Parks's own worked
  examples (gold set G1) before trusting it as evidence channel E2.
- The stem extractor reproduces form 2 for 86.7% of verbs. Its misses are
  mostly engine limits, so a miss is treated as "no confirmation", never as a
  contradiction.
- The database mixes two page conventions in `lexical_entries.page_number`:
  values up to 181 are split-PDF file numbers, larger values are printed book
  pages (book page = file number + 348). 33 entries carry a page number on
  which their headword does not appear; all of them are the `kaa…` entries
  labelled page 2, which are duplicates of entries on page 71. v2 resolves a
  page by checking the PDF text layer and never trusts the number alone.
