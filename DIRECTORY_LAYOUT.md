pari-pakuru/
│
├── README.md                          # Project overview and instructions
├── Quick_Reference_Guide.md           # Skiri dictionary parsing cheat sheet
├── claude-todo.md                     # Task tracking for Claude agent
├── verify_s2e.log                     # Log of S2E verification results
│
├── Dictionary Data/                   # All parsed, verified, and output dictionary data
│   ├── AI_Dictionary_Parsing_Instructions.md   # Parsing instructions for AI agents
│   ├── English-to-Skiri_JSON_Schema.json       # JSON schema for E2S entries
│   ├── Skiri-to-English_JSON_Schema.json       # JSON schema for S2E entries
│   ├── Example_English-to-Skiri_Output.json    # Example E2S output format
│   ├── Example_Skiri-to-English_Output.json    # Example S2E output format
│   ├── english_to_skiri_complete.json          # Full parsed E2S dictionary
│   ├── english_to_skiri_complete.json.backup   # Backup of E2S dictionary
│   ├── english_to_skiri_complete_missed.json   # Missed E2S entries
│   ├── english_to_skiri_verified.json          # AI-verified E2S entries
│   ├── english_to_skiri_verified_corrections.json # Corrections from E2S verification
│   ├── verification_progress_e2s.json          # E2S verification progress tracker
│   ├── skiri_to_english_complete.json          # Full parsed S2E dictionary
│   ├── skiri_to_english_parsed.json            # Parsed S2E entries
│   ├── skiri_to_english_parsed_MISSED.json     # Missed S2E entries
│   ├── skiri_to_english_verified.json          # AI-verified S2E entries
│   ├── skiri_to_english_verified_corrections.json # Corrections from S2E verification
│   ├── verification_progress_s2e.json          # S2E verification progress tracker
│   ├── blue_book_cross_reference.json          # Blue Book cross-reference data
│   ├── ocr_fix_changelog.json                  # Log of OCR character fixes
│   ├── phonetic_audit_checkpoint.json          # Audit progress checkpoint
│   ├── phonetic_audit_report.md                # Markdown audit report
│   ├── phonetic_validation_results.json        # AI validation results
│   ├── english_to_skiri_respelled.json         # E2S entries with respelling
│   ├── skiri_to_english_respelled.json         # S2E entries with respelling
│   ├── Dictionary PDF Split/                   # Source dictionary PDFs split by section
│   │   ├── split_pdf_pages_ENGLISH_TO_SKIRI/   # Individual E2S dictionary pages (PDFs)
│   │   ├── split_pdf_pages_SKIRI_TO_ENGLISH/   # Individual S2E dictionary pages (PDFs)
│
├── pari pakuru/                       # Blue Book source and scripts
│   ├── Blue Book - Pari Pakuru.pdf              # Original Blue Book PDF
│   ├── Blue_Book_Pari_Pakuru.txt                # Text extraction of Blue Book
│   ├── blue_book_split.py                       # Script to split Blue Book PDF
│   ├── Blue Book - Pari Pakuru - split/         # Individual Blue Book pages (PDFs)
│
├── scripts/                           # All parsing, verification, and utility scripts
│   ├── README_E2S_Parser.md                     # E2S parser documentation
│   ├── run_parser_e2s.py                        # Main E2S parser script
│   ├── s2e_parser.py                            # Main S2E parser script
│   ├── verify_with_claude.py                    # Claude-based verification
│   ├── verify_with_gemini.py                    # Gemini-based verification
│   ├── gemini_model.py                          # Gemini API wrapper
│   ├── merge_json_files.py                      # Merge JSON dictionary files
│   ├── merge_skiri_files_v1.py                  # Merge Skiri dictionary files (v1)
│   ├── check_overlap.py                         # Check for duplicate/overlapping entries
│   ├── check_overlap_v2.py                      # Overlap check (v2)
│   ├── check_skiri_overlap.py                   # Skiri-specific overlap check
│   ├── check_skiri_overlap_v2.py                # Skiri overlap check (v2)
│   ├── deep_overlap_check.py                    # Deep overlap analysis
│   ├── deepest_overlap_check.py                 # Most thorough overlap analysis
│   ├── deep_skiri_analysis.py                   # Deep Skiri entry analysis
│   ├── final_skiri_scan.py                      # Final scan for Skiri entries
│   ├── find_skiri_anchor.py                     # Find anchor points in Skiri data
│   ├── fix_headwords_and_cleanup.py             # Headword and cleanup script
│   ├── fix_ocr_phonetic_chars.py                # Fix OCR phonetic character errors
│   ├── cross_reference_blue_book.py             # Blue Book cross-reference script
│   ├── parser.log                               # Parser execution log
│   ├── parser_s2e.log                           # S2E parser log
│   ├── verify_e2s.log                           # E2S verification log
│   ├── verify_s2e.log                           # S2E verification log
│   ├── phonetic_audit_agent.py                  # Phonetic respelling & validation agent
│   └── __pycache__/                             # Python bytecode cache
│
└── .venv/                             # Python virtual environment