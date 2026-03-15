pari-pakuru/
│
├── README.md                              # Project overview and instructions
├── Quick_Reference_Guide.md               # Skiri dictionary parsing cheat sheet
├── Phase_1_1_Pronunciation_Respelling_Roadmap.md  # Respelling methodology doc
├── README_phonetic_audit.md               # Phonetic audit documentation
├── pari_pakuru_project_scope.md           # Full project scope and phase descriptions
├── claude-todo.md                         # Task tracking for Claude agent
├── requirements.txt                       # Python dependencies
├── .gitignore                             # Git ignore rules
│
├── skiri_pawnee.db                        # SQLite database (4273 entries, all tables)
├── skiri_pawnee.db-shm                    # SQLite shared memory file
├── skiri_pawnee.db-wal                    # SQLite write-ahead log
│
├── blue_book_extracted.json               # Gemini-extracted BB vocabulary (931 entries)
├── bb_extraction_checkpoint.json          # Gemini BB extraction checkpoint (20 lessons)
├── appendix_extraction_checkpoint.json    # Appendix extraction checkpoint
├── audit_sound_changes_checkpoint.json    # Sound change audit checkpoint
├── conjugation_collab_checkpoint.json     # Conjugation collaboration checkpoint
├── dual_plural_analysis_checkpoint.json   # Dual/plural analysis checkpoint
├── tag_checkpoint.json                    # Semantic tagging checkpoint
├── tag_review_queue.json                  # Semantic tag review queue
├── verify_s2e.log                         # S2E verification log
├── conjugation_collab.log                 # Conjugation collaboration log
│
├── validate_output.txt                    # Morpheme validation output
├── validate_output2.txt                   # Morpheme validation output (run 2)
├── validate_sick.txt                      # "to be sick" validation output
├── close_analysis.txt                     # Close-match analysis
├── come_close.txt                         # "to come" close-match analysis
├── mismatch_analysis.txt                  # Mismatch analysis
├── mismatch2.txt                          # Mismatch analysis (run 2)
├── mismatch3.txt                          # Mismatch analysis (run 3)
├── mismatch4.txt                          # Mismatch analysis (run 4)
├── paripakuru_pythonanywhere_ERROR_LOG.txt # PythonAnywhere error log
├── paripakuru_pythonanywhere_SERVER_LOG.txt # PythonAnywhere server log
│
├── Dictionary Data/                       # All parsed, verified, and output dictionary data
│   ├── AI_Dictionary_Parsing_Instructions.md       # Parsing instructions for AI agents
│   ├── English-to-Skiri_JSON_Schema.json           # JSON schema for E2S entries
│   ├── Skiri-to-English_JSON_Schema.json           # JSON schema for S2E entries
│   ├── Example_English-to-Skiri_Output.json        # Example E2S output format
│   ├── Example_Skiri-to-English_Output.json        # Example S2E output format
│   │
│   ├── english_to_skiri_complete.json              # Full parsed E2S dictionary
│   ├── english_to_skiri_complete.json.backup       # Backup of E2S dictionary
│   ├── english_to_skiri_complete.pre_ocr_fix_*.json # Pre-OCR-fix snapshot
│   ├── english_to_skiri_complete_missed.json       # Missed E2S entries
│   ├── english_to_skiri_linked.json                # E2S entries with cross-links (6414 entries)
│   ├── english_to_skiri_normalized.json            # E2S entries after normalization
│   ├── english_to_skiri_verified.json              # AI-verified E2S entries
│   ├── english_to_skiri_verified_corrections.json  # Corrections from E2S verification
│   ├── verification_progress_e2s.json              # E2S verification progress tracker
│   │
│   ├── skiri_to_english_complete.json              # Full parsed S2E dictionary
│   ├── skiri_to_english_complete.pre_ocr_fix_*.json # Pre-OCR-fix snapshot
│   ├── skiri_to_english_fixed.json                 # S2E entries after fixes
│   ├── skiri_to_english_linked.json                # S2E entries with cross-links
│   ├── skiri_to_english_normalized.json            # S2E entries after normalization
│   ├── skiri_to_english_parsed.json                # Parsed S2E entries
│   ├── skiri_to_english_parsed_MISSED.json         # Missed S2E entries
│   ├── skiri_to_english_respelled.json             # S2E entries with respelling (4273, CURRENT)
│   ├── skiri_to_english_verified.json              # AI-verified S2E entries
│   ├── skiri_to_english_verified_corrections.json  # Corrections from S2E verification
│   ├── verification_progress_s2e.json              # S2E verification progress tracker
│   │
│   ├── link_changelog.json                         # Linking phase changelog
│   ├── link_report.md                              # Linking phase report
│   ├── normalization_changelog.json                # Normalization changelog
│   │
│   └── Dictionary PDF Split/                       # Source dictionary PDFs by section
│       ├── 01-Abbreviations_and_Sound_Key.pdf
│       ├── 02-Sounds_and_Alphabet.pdf
│       ├── 03-Major_Sound_Changes.pdf
│       ├── 04-Grammatical_Overview.pdf
│       ├── 05-Organization_of_the_Dictionary.pdf
│       ├── Appendix 1 - Illustrative Skiri Verb Conjugations.pdf
│       ├── Appendix 2 - Verb Roots with Irregular Dual or Plural Agents.pdf
│       ├── Appendix 3 - Kinship Terminology - Consanguineal and Affinal.pdf
│       ├── English to Skiri.pdf
│       └── Skiri to English.pdf
│
├── pari pakuru/                           # Blue Book source and scripts
│   ├── Blue Book - Pari Pakuru.pdf                 # Original Blue Book PDF
│   ├── Blue_Book_Pari_Pakuru.txt                   # Text extraction of Blue Book
│   ├── blue_book_split.py                          # Script to split Blue Book PDF
│   └── Blue Book - Pari Pakuru - split/            # 130 individual Blue Book pages (PDFs)
│
├── extracted_data/                        # Gemini-extracted structured data from PDFs
│   ├── abbreviations.json                          # 164 morpheme abbreviations with forms
│   ├── appendix1_conjugations.json                 # 770 verb paradigm forms (7 verbs × 10 modes × 11 pn)
│   ├── appendix2_irregular_roots.json              # 9 suppletive verb roots
│   ├── appendix3_kinship.json                      # 23 kinship terms with possessive paradigms
│   ├── grammatical_overview.json                   # 23 pages of grammar (19 OCR + 4 text recovery)
│   ├── grammar_failed_pages_transcriptions.json    # Fallback transcriptions for failed pages
│   ├── grammar_retry_results.json                  # Grammar retry outputs
│   ├── dual_plural_analysis.json                   # Gemini morpheme breakdowns for all 7 verbs
│   ├── noun_possession_catalog.json                # Noun catalog by possession system
│   ├── grammar_page_1.png                          # High-DPI renders for OCR recovery
│   ├── grammar_page_3.png
│   ├── grammar_page_7.png
│   └── grammar_page_16.png
│
├── reports/                               # Phase reports and analysis outputs
│   ├── phase_1_1c_report.txt                       # Phase 1.1c respelling report
│   ├── phase_1_1c_report_final.txt                 # Phase 1.1c final report
│   ├── phase_1_1c_report_post_fix.txt              # Phase 1.1c post-fix report
│   ├── phase_1_1d_audit.txt                        # Phase 1.1d audit report
│   ├── phase_1_1d_audit_final.txt                  # Phase 1.1d final audit
│   ├── phase_1_1d_audit_gemini.txt                 # Phase 1.1d Gemini audit
│   ├── phase_1_1d_audit_local.txt                  # Phase 1.1d local audit
│   ├── phase_1_1d_audit_post_fix.txt               # Phase 1.1d post-fix audit
│   ├── phase_1_1d_final.txt                        # Phase 1.1d final summary
│   ├── phase_1_1d_flags.json                       # Audit flags (JSON)
│   ├── phase_1_1d_flags_final.json                 # Audit flags final (JSON)
│   ├── phase_2_2_blue_book.txt                     # Phase 2.2 Blue Book cross-verification
│   ├── phase_2_2_pronunciation.txt                 # Phase 2.2 pronunciation comparison
│   ├── phase_2_2_pronunciation_phonetic.txt        # Phase 2.2 phonetic comparison
│   ├── phase_2_3_sound_changes.txt                 # Phase 2.3 sound change rules report
│   ├── phase_3_1_morphemes.txt                     # Phase 3.1 morpheme inventory report
│   ├── phase_3_1_5_noun_possession.txt             # Phase 3.1.5 noun possession report
│   ├── conjugation_gemini_collab.txt               # Gemini conjugation collaboration log
│   ├── conjugation_gemini_collab.json              # Gemini collab structured output
│   ├── fix_priority_changelog.txt                  # Priority fix changelog
│   ├── flags_final.json                            # Final audit flags
│   ├── gemini_checkpoint.json                      # Gemini analysis checkpoint
│   ├── glottal_checkpoint.json                     # Glottal verification checkpoint
│   ├── glottal_confirmed_fixes.json                # Confirmed glottal stop fixes
│   ├── glottal_phonetic_verification.txt           # Glottal verification report
│   ├── grammar_retry_comparison.txt                # Grammar retry comparison
│   ├── manual_review_list.txt                      # Manual review list
│   ├── noun_glottal_fixes.json                     # Noun glottal fixes
│   ├── noun_glottal_verification.txt               # Noun glottal verification report
│   └── review_final.txt                            # Final review report
│
├── scripts/                               # All parsing, verification, and utility scripts
│   │
│   │  # --- Parsing ---
│   ├── run_parser_e2s.py                           # Main E2S parser script
│   ├── s2e_parser.py                               # Main S2E parser script
│   ├── README_E2S_Parser.md                        # E2S parser documentation
│   │
│   │  # --- Normalization & Linking (Phase 1.1) ---
│   ├── normalize_phonetic.py                       # OCR phonetic normalization
│   ├── link_dictionaries.py                        # Cross-link S2E ↔ E2S entries
│   ├── respell_and_normalize.py                    # IPA respelling and normalization
│   ├── test_phase_1_1.py                           # Phase 1.1 unit tests
│   ├── fix_priority_issues.py                      # Priority issue fixer
│   │
│   │  # --- Verification (Phase 1.1d) ---
│   ├── audit_entries.py                            # Gemini-powered entry audit
│   ├── verify_with_claude.py                       # Claude-based verification
│   ├── verify_with_gemini.py                       # Gemini-based verification
│   ├── verify_glottal_from_phonetic.py             # Glottal stop verification from phonetic
│   ├── verify_noun_glottal.py                      # Noun glottal stop verification
│   ├── generate_review_list.py                     # Generate manual review list
│   ├── gemini_model.py                             # Gemini API wrapper
│   │
│   │  # --- Semantic Tagging (Phase 2.1) ---
│   ├── tag_entries.py                              # Semantic category tagging
│   │
│   │  # --- Blue Book Cross-Reference (Phase 2.2) ---
│   ├── blue_book_verify.py                         # BB cross-verification
│   ├── bb_pronunciation_compare.py                 # BB pronunciation comparison
│   │
│   │  # --- Sound Changes (Phase 2.3) ---
│   ├── sound_changes.py                            # 24-rule sound change engine
│   │
│   │  # --- Morpheme Inventory (Phase 3.1) ---
│   ├── extract_appendices.py                       # PyMuPDF→Gemini PDF extraction
│   ├── morpheme_inventory.py                       # Verb conjugation engine (90.3% accuracy)
│   ├── analyze_dual_plural.py                      # Gemini dual/plural morpheme analysis
│   ├── conjugation_gemini_collab.py                # Gemini conjugation collaboration
│   ├── merge_grammar_retries.py                    # Merge grammar retry results
│   ├── retry_failed_grammar.py                     # Retry failed grammar pages
│   │
│   │  # --- Noun Possession (Phase 3.1.5) ---
│   ├── noun_possession.py                          # Noun classification & possession catalog
│   │
│   │  # --- Overlap & Dedup Utilities ---
│   ├── check_overlap.py                            # Check for duplicate/overlapping entries
│   ├── check_overlap_v2.py                         # Overlap check (v2)
│   ├── check_skiri_overlap.py                      # Skiri-specific overlap check
│   ├── check_skiri_overlap_v2.py                   # Skiri overlap check (v2)
│   ├── deep_overlap_check.py                       # Deep overlap analysis
│   ├── deepest_overlap_check.py                    # Most thorough overlap analysis
│   ├── deep_skiri_analysis.py                      # Deep Skiri entry analysis
│   ├── final_skiri_scan.py                         # Final scan for Skiri entries
│   ├── find_skiri_anchor.py                        # Find anchor points in Skiri data
│   ├── merge_json_files.py                         # Merge JSON dictionary files
│   ├── merge_skiri_files_v1.py                     # Merge Skiri dictionary files (v1)
│   │
│   │  # --- Logs ---
│   ├── parser.log                                  # E2S parser execution log
│   ├── parser_s2e.log                              # S2E parser log
│   ├── verify_e2s.log                              # E2S verification log
│   ├── verify_s2e.log                              # S2E verification log
│   ├── link_dictionaries.log                       # Linking log
│   ├── normalize_phonetic.log                      # Normalization log
│   └── __pycache__/                                # Python bytecode cache
│
├── web/                                   # Flask web search interface (Phase 4.1)
│   ├── __init__.py                                 # Package init
│   ├── app.py                                      # Flask application (routes, HTMX endpoints)
│   ├── db.py                                       # Database access layer
│   ├── search.py                                   # Search logic (fuzzy matching, FTS)
│   ├── flashcards.py                               # Flashcard study mode
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css                           # Main stylesheet
│   │   │   └── pawnee-theme.css                    # Pawnee-themed styling
│   │   └── js/
│   │       └── search.js                           # Client-side search (HTMX integration)
│   │
│   ├── templates/
│   │   ├── base.html                               # Base template (Pico CSS + HTMX)
│   │   ├── index.html                              # Home page
│   │   ├── results.html                            # Search results page
│   │   ├── entry.html                              # Single entry detail page
│   │   ├── browse.html                             # Browse by letter
│   │   ├── browse_list.html                        # Browse list partial
│   │   ├── about.html                              # About page
│   │   ├── guide.html                              # Syllable/pronunciation guide
│   │   ├── flashcards.html                         # Flashcard deck selection
│   │   ├── flashcard_study.html                    # Flashcard study view
│   │   ├── _entry_card.html                        # Entry card partial (HTMX)
│   │   ├── _results_body.html                      # Results body partial (HTMX)
│   │   ├── _category_cloud.html                    # Category cloud partial
│   │   ├── _stats_bar.html                         # Stats bar partial
│   │   └── _word_of_day.html                       # Word of the day partial
│   │
│   └── __pycache__/                                # Python bytecode cache
│
└── .venv/                                 # Python virtual environment
