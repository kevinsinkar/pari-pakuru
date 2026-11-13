# archived/

A record of finished work: one-off scripts and reports from stages that are
done. **No live code reads anything in this folder.** It is kept because it
shows how a step was carried out, which matters if the step ever has to be
repeated or questioned.

## scripts/

Each of these produced data that is still in the database or in
`extracted_data/`. They were written to run from `scripts/`; to run one again,
copy it back there first.

| Script | Stage | What it did |
|---|---|---|
| `verify_with_gemini.py`, `verify_with_claude.py` | parsing | A second AI pass that checked every parsed entry against its page PDF and corrected it |
| `merge_json_files.py`, `merge_skiri_files_v1.py` | parsing | Merged the pages that were missed and parsed again into the main JSON |
| `generate_review_list.py` | 1.1d | Turned the audit's flags into a prioritised review list |
| `verify_glottal_from_phonetic.py`, `verify_noun_glottal.py` | 1.1d | Checked 260 nouns that end in a vowel with no glottal stop: 257 correct as printed, 3 could not be checked |
| `audit_semantic_tags.py` | 2.1 | AI audit of topic tags; removed 1,248 false matches |
| `bb_pronunciation_compare.py` | 2.2 | Compared the Blue Book's pronunciation guides with Parks's IPA |
| `analyze_dual_plural.py` | 3.1 | AI breakdown of the dual and plural forms in Appendix 1 |
| `conjugation_gemini_collab.py` | 3.1 | Three rounds of AI diagnosis of conjugation mismatches |
| `retry_failed_grammar.py`, `merge_grammar_retries.py` | 3.1 | Recovered four pages of the grammar chapter that the first extraction lost |
| `add_feedback_table.py` | 4.4 | Created the `community_feedback` table |

## reports/

| Report | What it records |
|---|---|
| `phase_1_1b_link_report.md` | Linking the two dictionary sections: 5,132 subentries linked, 362 unmatched |
| `phase_1_1c_report.txt` | The respelling and learner-spelling run |
| `fix_priority_changelog.txt` | What `fix_priority_issues.py` changed |
| `phase_1_1d_final.txt`, `review_final.txt`, `flags_final.json` | The final 1.1d audit: 640 flags, what each kind means, and the flags themselves |
| `glottal_phonetic_verification.txt`, `noun_glottal_verification.txt` | The noun glottal-stop check |
| `grammar_retry_comparison.txt` | Which engine recovered which lost grammar page |
| `conjugation_gemini_collab.txt` | The AI-assisted conjugation diagnosis. Read this before trying to improve the conjugation engine |
| `phase_3_1_5_round2_report.md` | How the possession engine was joined to the sound-change rules |

## What was removed on 2026-11-13

The folder used to hold much more. The following were deleted from the working
tree and remain in git history at commit `2e77095`
(`git show 2e77095:archived/<path>` or `git checkout 2e77095 -- archived/<path>`):

| Removed | What it was |
|---|---|
| `dictionary_intermediates/*.json` (139 MB) | Every earlier stage of the two JSON dictionaries (raw parse, verified, normalised, linked), their backups and change logs |
| `logs_and_analysis/` | Run logs and scratch analysis of mismatches |
| `docs/DIRECTORY_LAYOUT.md`, `claude-todo.md`, `README_phonetic_audit.md`, `skiri_pawnee_db_SCHEMA.txt` | Out-of-date layout, plan and schema notes; the READMEs in each folder replace them |
| earlier drafts of the reports above, and their machine-readable dumps | Superseded by the final versions kept here |
| nine debugging scripts (`check_overlap*.py`, `check_skiri_overlap*.py`, `deep_overlap_check.py`, `deep_skiri_analysis.py`, `deepest_overlap_check.py`, `final_skiri_scan.py`, `find_skiri_anchor.py`), run logs, two compiled `.pyc` files, an older copy of `accent_rules.py`, `integration_guide.py` | Not part of any result |

Ten checkpoint files of finished AI runs (topic tags and their audit, Blue Book
gap triage, appendix extraction, function words, the sound-change audit, the
conjugation and dual/plural analyses) were never in git. They were
**moved, not deleted**, to `OneDrive/pari_pakuru_backups/repo_cleanup_2026-11-13/`.
They are the only saved copies of those AI answers outside the database.

Design documents and parsing instructions that used to be here are now in
[../prompts/](../prompts/).
