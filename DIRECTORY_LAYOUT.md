# Pari Pakuru — Directory Layout

```
pari-pakuru/
│
├── README.md                          # Project readme
├── Quick_Reference_Guide.md           # Quick reference guide
├── claude-todo.md                     # Claude task tracking
├── verify_s2e.log                     # Skiri-to-English verification log
│
├── Dictionary Data/                   # Parsed & verified dictionary data
│   ├── AI_Dictionary_Parsing_Instructions.md   # Instructions for AI-assisted parsing
│   │
│   ├── # JSON Schemas
│   ├── English-to-Skiri_JSON_Schema.json       # Schema for E2S entries
│   ├── Skiri-to-English_JSON_Schema.json       # Schema for S2E entries
│   ├── Example_English-to-Skiri_Output.json    # Example E2S output
│   ├── Example_Skiri-to-English_Output.json    # Example S2E output
│   │
│   ├── # English-to-Skiri Data
│   ├── english_to_skiri_complete.json           # Full parsed E2S dictionary
│   ├── english_to_skiri_complete.json.backup    # Backup of E2S dictionary
│   ├── english_to_skiri_complete_missed.json    # Missed entries from E2S parsing
│   ├── english_to_skiri_verified.json           # AI-verified E2S entries
│   ├── english_to_skiri_verified_corrections.json # Corrections from E2S verification
│   ├── verification_progress_e2s.json           # E2S verification progress tracker
│   │
│   ├── # Skiri-to-English Data
│   ├── skiri_to_english_complete.json           # Full parsed S2E dictionary
│   ├── skiri_to_english_parsed.json             # Parsed S2E entries
│   ├── skiri_to_english_parsed_MISSED.json      # Missed entries from S2E parsing
│   ├── skiri_to_english_verified.json           # AI-verified S2E entries
│   ├── skiri_to_english_verified_corrections.json # Corrections from S2E verification
│   ├── verification_progress_s2e.json           # S2E verification progress tracker
│   │
│   ├── Dictionary PDF Split/                    # Source dictionary PDF sections
│   │   ├── 01-Abbreviations_and_Sound_Key.pdf
│   │   ├── 02-Sounds_and_Alphabet.pdf
│   │   ├── 03-Major_Sound_Changes.pdf
│   │   ├── 04-Grammatical_Overview.pdf
│   │   ├── 05-Organization_of_the_Dictionary.pdf
│   │   ├── Appendix 1 - Illustrative Skiri Verb Conjugations.pdf
│   │   ├── Appendix 2 - Verb Roots with Irregular Dual or Plural Agents.pdf
│   │   ├── Appendix 3 - Kinship Terminology - Consanguineal and Affinal.pdf
│   │   ├── English to Skiri.pdf
│   │   └── Skiri to English.pdf
│   │
│   ├── split_pdf_pages_ENGLISH_TO_SKIRI/        # Individual E2S dictionary pages (PDFs)
│   └── split_pdf_pages_SKIRI_TO_ENGLISH/        # Individual S2E dictionary pages (PDFs)
│
├── pari pakuru/                       # Blue Book source material
│   ├── Blue Book - Pari Pakuru.pdf              # Original Blue Book PDF
│   ├── Blue_Book_Pari_Pakuru.txt                # Text extraction of the Blue Book
│   ├── blue_book_split.py                       # Script to split the Blue Book PDF
│   └── Blue Book - Pari Pakuru - split/         # Individual pages (page_1.pdf – page_130.pdf)
│
├── scripts/                           # Parsing, verification & utility scripts
│   ├── README_E2S_Parser.md                     # Documentation for the E2S parser
│   │
│   ├── # Parsers
│   ├── run_parser_e2s.py                        # English-to-Skiri dictionary parser
│   ├── s2e_parser.py                            # Skiri-to-English dictionary parser
│   │
│   ├── # AI Verification
│   ├── verify_with_claude.py                    # Verify parsed entries using Claude
│   ├── verify_with_gemini.py                    # Verify parsed entries using Gemini
│   ├── gemini_model.py                          # Gemini API model wrapper
│   │
│   ├── # Merge & Overlap Analysis
│   ├── merge_json_files.py                      # Merge multiple JSON dictionary files
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
│   │
│   ├── # Logs
│   ├── parser.log                               # Parser execution log
│   ├── parser_s2e.log                           # S2E parser log
│   ├── verify_e2s.log                           # E2S verification log
│   ├── verify_s2e.log                           # S2E verification log
│   │
│   └── __pycache__/                             # Python bytecode cache
│
└── .venv/                             # Python virtual environment
```
