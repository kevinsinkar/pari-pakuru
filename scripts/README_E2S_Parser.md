# English-to-Skiri Dictionary Parser

## Overview
This parser extracts **complete, detailed entries** from the English-to-Skiri section of the Skiri Pawnee bilingual dictionary for language revitalization purposes. It captures all linguistic data including phonetic forms, etymologies, paradigmatic forms, examples, and cross-references.

## Purpose
This tool supports **Skiri language revitalization** by creating a comprehensive digital dataset that can be used for:
- Language learning applications
- Digital dictionaries
- Linguistic analysis
- Educational materials
- Preservation of endangered language data

---

## Key Features

### Complete Data Extraction
- ✅ **Phonetic forms** with 100% accuracy (highest priority)
- ✅ **Multiple subentries** per English word (one English word → multiple Skiri translations)
- ✅ **Etymology** with morpheme breakdown
- ✅ **Grammatical classifications** (VI, VT, N, etc.)
- ✅ **5 paradigmatic forms** for verbs
- ✅ **Part III cross-references** (unique to English-to-Skiri)
- ✅ **Examples and usage notes**

### Advanced Processing
- **Two-page parsing**: Handles entries that span across pages
- **Subentry recognition**: Automatically detects multiple Skiri translations
- **Special character preservation**: Maintains diacritics (®, •, accents, macrons)
- **Cross-reference extraction**: Structured parsing of "see X {skiri}" references
- **JSON schema validation**: Output matches comprehensive schema

---

## Requirements

### Python Dependencies
```bash
pip install google-generativeai pypdf
```

### Required Files
1. **Context PDFs** (for AI understanding):
   - `01-Abbreviations_and_Sound_Key.pdf`
   - `02-Sounds_and_Alphabet.pdf`
   - `05-Organization_of_the_Dictionary.pdf`

2. **Schema and Instructions**:
   - `English-to-Skiri_JSON_Schema.json`
   - `AI_Dictionary_Parsing_Instructions.md` (optional but recommended)

3. **Input PDFs**:
   - Folder containing split PDF pages: `split_pdf_pages_ENGLISH_TO_SKIRI/`
   - Each PDF should be a single page from the dictionary

### API Configuration
- **Gemini API Key** required
- Model used: **gemini-2.5-pro** (highest accuracy for linguistic data)
- Set key as environment variable: `export GEMINI_API_KEY="your_key_here"`

---

## Configuration

Edit these variables in `run_parser_e2s.py`:

```python
# API Key
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")

# Input/Output
INPUT_PDF_FOLDER = "split_pdf_pages_ENGLISH_TO_SKIRI"
OUTPUT_JSON_FILE = "english_to_skiri_complete.json"

# Context files
CONTEXT_PDFS = [
    "01-Abbreviations_and_Sound_Key.pdf",
    "02-Sounds_and_Alphabet.pdf",
    "05-Organization_of_the_Dictionary.pdf"
]

# Schema files
SCHEMA_FILE = "English-to-Skiri_JSON_Schema.json"
INSTRUCTIONS_FILE = "AI_Dictionary_Parsing_Instructions.md"
```

---

## Usage

### Basic Usage
```bash
python run_parser_e2s.py
```

### With Environment Variable
```bash
export GEMINI_API_KEY="your_api_key_here"
python run_parser_e2s.py
```

### What Happens
1. Script loads parsing instructions and JSON schema
2. Uploads context PDFs to Gemini API
3. Processes pages sequentially (Page N + Page N+1 for cross-page entries)
4. Parses all English entries that BEGIN on Page N
5. Uses Page N+1 only to complete split entries
6. Saves complete JSON output

### Output
- **File**: `english_to_skiri_complete.json`
- **Format**: JSON array of complete dictionary entries
- **Encoding**: UTF-8 with preserved special characters
- **Log**: `parser.log` (detailed processing log)

---

## Output Structure

### Top Level Entry
```json
{
  "english_entry_word": "stop",
  "entry_metadata": {
    "page_number": 455,
    "column": "right",
    "source_page": 455
  },
  "subentries": [...]
}
```

### Each Subentry Contains

#### Part I: Basic Information
```json
{
  "part_I": {
    "skiri_term": "awPuusik",
    "stem_preverb": "(uur...)",
    "phonetic_form": "[=a•wi•®uu•s,u®(h)=]",
    "grammatical_classification": {
      "class_abbr": "VI",
      "verb_class": "(4)"
    },
    "english_glosses": [
      {
        "number": 1,
        "definition": "quiet down, calm down",
        "usage_notes": "purposefully"
      }
    ],
    "etymology": {
      "raw_etymology": "<uur+ra wi+uusik, image to go down>",
      "constituent_elements": [...],
      "literal_translation": "image to go down, i.e., go down quickly"
    }
  }
}
```

#### Part II: Paradigmatic Forms
```json
{
  "part_II": {
    "paradigmatic_forms": [
      {
        "form_number": 1,
        "description": "1st Person Singular Subject, Indicative Mode, Perfective",
        "skiri_form": "tatuurawiPuusit"
      },
      // ... forms 2-5
    ],
    "examples": [
      {
        "skiri_text": "example sentence",
        "english_translation": "translation"
      }
    ]
  }
}
```

#### Part III: Cross-References (unique to English-to-Skiri)
```json
{
  "part_III": {
    "cross_references": [
      {
        "english_term": "come to a stop",
        "skiri_equivalents": ["iriitik", "raar-"]
      }
    ]
  }
}
```

---

## Key Differences: English-to-Skiri vs. Skiri-to-English

| Feature | English-to-Skiri | Skiri-to-English |
|---------|------------------|------------------|
| **Subentries** | ✅ Multiple (one English → many Skiri) | ❌ Single entry only |
| **Part III** | ✅ Cross-references included | ❌ Not present |
| **Preverb position** | After stem in citation: `awPuusik (uur...)` | After stem: `word (ut...)` |
| **Structure** | Parts I, II, III | Parts I, II only |

---

## Logging

The script provides detailed logging to both console and `parser.log`:

```
2024-02-15 10:30:15 - INFO - Loading parsing instructions and JSON schema...
2024-02-15 10:30:16 - INFO - Uploading essential context PDFs...
2024-02-15 10:30:20 - INFO - Found 247 pages to process.
2024-02-15 10:30:20 - INFO - Processing Page 1/247: page_001.pdf
2024-02-15 10:30:35 - INFO -   - Successfully parsed 8 English entries with complete data.
```

---

## Error Handling

### Rate Limiting
- Automatic retry with exponential backoff (30s, 60s, 90s)
- Logged warnings when rate limits hit

### Missing Context Files
- Warning logged if schema/instructions files not found
- Falls back to embedded instructions

### Malformed JSON
- Warning logged with response text for debugging
- Returns empty array, continues processing

### Page Processing Failures
- Logs error but continues to next page
- Final summary shows total successful parses

---

## Quality Validation

### Before Each Entry Output, AI Validates:
- ✓ Phonetic form extracted with 100% accuracy
- ✓ All subentries captured
- ✓ Grammatical class in SMALL CAPS extracted
- ✓ Etymology angle brackets matched correctly
- ✓ Cross-references (Part III) properly structured
- ✓ JSON matches schema exactly

### Manual Validation Recommended:
1. **Phonetic forms**: Spot-check random entries for diacritics
2. **Subentries**: Verify multiple Skiri translations captured
3. **Cross-references**: Check Part III structure
4. **Cross-page entries**: Verify continuity for split entries

---

## Troubleshooting

### "No entries parsed"
- Check PDF text extraction quality
- Verify PDFs contain actual text (not scanned images)
- Review `parser.log` for API response details

### "Rate limit hit"
- Normal for large batches
- Script automatically retries
- Consider reducing batch size or adding delays

### Missing phonetic characters
- Verify PDF encoding
- Check if Gemini 2.5 Pro is being used (best for special chars)
- Review raw PDF text extraction

### Schema validation errors
- Ensure schema file is valid JSON
- Check schema matches latest version
- Review parsed output structure

---

## Performance

### Expected Processing Time
- **~15-30 seconds per page** (with Gemini 2.5 Pro)
- **247 pages ≈ 1.5-2.5 hours total**
- Rate limiting may extend this time

### API Costs (Approximate)
- Gemini 2.5 Pro: ~$0.001-0.003 per page
- Total for 247 pages: ~$0.25-$0.75

---

## Next Steps After Parsing

1. **Validation**: Run quality checks on output
2. **Post-processing**: Clean any encoding issues
3. **Database import**: Load into application database
4. **Application integration**: Build learning tools with data
5. **Community review**: Have Skiri speakers verify entries

---

## Files Included

- `run_parser_e2s.py` - Main parsing script
- `English-to-Skiri_JSON_Schema.json` - Complete output schema
- `AI_Dictionary_Parsing_Instructions.md` - Comprehensive parsing guide
- `Quick_Reference_Guide.md` - Quick lookup reference
- `Example_English-to-Skiri_Output.json` - Example output
- `README_E2S_Parser.md` - This file

---

## Support for Language Revitalization

This parser is designed specifically to support Skiri Pawnee language revitalization efforts by:

1. **Preserving accuracy**: 100% fidelity to phonetic forms and linguistic details
2. **Enabling accessibility**: Structured data for digital learning tools
3. **Supporting research**: Complete etymological and grammatical information
4. **Facilitating teaching**: Example sentences and usage notes preserved
5. **Building connections**: Cross-references help learners discover related words

---

## License & Attribution

This tool processes the Skiri Pawnee Dictionary. Please ensure appropriate attribution and respect for the Skiri language and culture in any applications built with this data.

---

## Contact & Contributions

For issues, improvements, or questions about using this parser for language revitalization projects, please reach out to the project maintainers.

**Remember**: This is not just data extraction - this is language preservation for future generations of Skiri speakers.
