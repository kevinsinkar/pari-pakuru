import os
import time
import glob
import json
import pathlib
import logging
import google.generativeai as genai
from google.api_core import exceptions
from pypdf import PdfReader

# --- CONFIGURATION ---

# 1. SET YOUR API KEY
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")

# 2. DEFINE FOLDER AND FILE NAMES
INPUT_PDF_FOLDER = "split_pdf_pages_SKIRI_TO_ENGLISH_missed"  # Folder with Skiri-to-English pages
OUTPUT_JSON_FILE = "skiri_to_english_parsed_MISSED.json"

# 3. DEFINE THE MASTER PROMPT FOR SKIRI-TO-ENGLISH PARSING
MASTER_PROMPT_TEXT = """# SKIRI-TO-ENGLISH DICTIONARY PARSING TASK

You are parsing a Skiri Pawnee to English dictionary. Extract ALL entries from the provided pages with 100 percent accuracy.

## CRITICAL PRIORITY
**PHONETIC FORM in square brackets [...] must be extracted with 100 percent accuracy.** This is your highest priority field.

## ENTRY STRUCTURE

Each entry has this structure:
1. **Headword** (boldface Skiri word) - REQUIRED
2. **Stem Preverb** (if present) - in parentheses like (ut...) or (uur...) immediately after headword
3. **Phonetic Form** [...] - REQUIRED, CRITICAL ACCURACY
4. **Grammatical Class** - SMALL CAPS abbreviation (VI, VT, N, VD, etc.)
5. **Verb Class** - Number in parentheses: (1), (1-a), (2), (3), (4), etc.
6. **Additional Forms** - In curly brackets {...}
7. **Glosses** - Numbered English definitions
8. **Etymology** - In angle brackets <...>
9. **Paradigmatic Forms** - Numbered list 1-5 (for verbs)
10. **Examples** - Bulleted sentences with •

## PARSING INSTRUCTIONS

**You will receive TWO pages: Page N and Page N+1.**

1. Parse ALL entries that BEGIN on Page N
2. Use Page N+1 text ONLY to complete entries that continue from Page N
3. Do NOT parse new entries that begin on Page N+1
4. Process left column top-to-bottom, then right column top-to-bottom
5. Entry boundaries: New entry starts with boldface headword, ends where next boldface begins

## SPECIAL CHARACTERS TO PRESERVE EXACTLY
- ® = glottal stop
- • = syllable break
- : = vowel length
- All diacritics (accents, macrons, etc.)

## OUTPUT JSON SCHEMA

Return a JSON array of entries following this exact structure:

```json
[
  {
    "headword": "string (REQUIRED)",
    "entry_metadata": {
      "page_number": integer,
      "column": "left" or "right",
      "continues_from_previous_page": boolean,
      "continues_to_next_page": boolean
    },
    "part_I": {
      "stem_preverb": "string or null (e.g., '(ut...)' or '(uur...)')",
      "phonetic_form": "string (REQUIRED - extract with 100 percent accuracy)",
      "grammatical_info": {
        "grammatical_class": "string (VI, VT, N, VD, etc.)",
        "verb_class": "string or null (e.g., '(1)', '(4)', '(1-a)')",
        "additional_forms": [
          {
            "form_type": "string (e.g., 'pl. obj.', 'du. obj.')",
            "form": "string"
          }
        ]
      },
      "glosses": [
        {
          "number": integer or null,
          "definition": "string",
          "usage_notes": "string or null (italicized clarifications)"
        }
      ],
      "etymology": {
        "raw_etymology": "string (complete <...> contents)",
        "constituent_elements": [
          {
            "morpheme": "string",
            "gloss": "string",
            "morpheme_type": "string (prefix, root, suffix, preverb)"
          }
        ],
        "literal_translation": "string or null"
      },
      "cognates": [
        {
          "language": "string (Ar, Pa, Wi, Ki, SB)",
          "form": "string",
          "gloss": "string or null"
        }
      ]
    },
    "part_II": {
      "paradigmatic_forms": {
        "form_1": "string or null (1st Person Singular, Indicative, Perfective)",
        "form_2": "string or null (3rd Person Singular, Indicative, Perfective)",
        "form_3": "string or null (3rd Person Singular, Indicative, Imperfective)",
        "form_4": "string or null (3rd Person Singular, Absolutive, Subordinate Perfective)",
        "form_5": "string or null (3rd Person Singular, Indicative, Perfective Intentive)",
        "additional_forms": [
          {
            "form": "string",
            "description": "string (for bulleted forms beyond standard 5)"
          }
        ]
      },
      "examples": [
        {
          "skiri_text": "string",
          "english_translation": "string or null",
          "usage_context": "string or null"
        }
      ]
    },
    "compound_structure": {
      "has_null_stem": boolean,
      "preverb": "string or null",
      "verb_stem": "string or null",
      "noun": "string or null"
    },
    "derived_stems": [
      {
        "derived_form": "string",
        "phonetic_form": "string",
        "meaning": "string"
      }
    ]
  }
]
```

## GRAMMATICAL CLASS ABBREVIATIONS
- VI = intransitive verb
- VT = transitive verb
- VD = descriptive verb
- VL = locative verb
- VP = patientive/passive verb
- VR = reflexive verb
- N = noun
- N-DEP = dependent noun stem
- N-KIN = kinship term
- ADJ = adjective
- ADV = adverb
- PRON = pronoun
- DEM = demonstrative
- NUM = numeral

## VERB CLASSES
- (1), (1-a), (1-i) = Class 1 variants
- (2), (2-i) = Class 2 variants
- (3) = Class 3
- (4), (4-i) = Class 4 variants
- (u) = Descriptive-like
- (wi) = Locative-like

## VALIDATION BEFORE OUTPUT
✓ Every entry has headword and phonetic_form
✓ Phonetic forms extracted character-for-character with all special characters
✓ Entries spanning pages are properly merged
✓ Paradigmatic forms numbered correctly (1-5)
✓ Etymology angle brackets matched
✓ All curly brackets {...} and square brackets [...] properly captured

## OUTPUT FORMAT
- Return ONLY valid JSON
- No markdown formatting
- No explanatory text before or after JSON
- Ensure all special characters preserved exactly
"""

####################
### SCRIPT LOGIC ###
####################

def setup_logging():
    """Configures logging to output to both console and a file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler('parser_s2e.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def configure_gemini():
    """Configures the Gemini API."""
    if API_KEY == "YOUR_API_KEY" or not API_KEY:
        logging.error("Error: API key not configured. Please set it in the script or as an environment variable.")
        return None
    genai.configure(api_key=API_KEY)
    return genai.GenerativeModel('gemini-2.5-pro')

def extract_text_from_pdf(pdf_path):
    """Extracts all text content from a single-page PDF."""
    try:
        reader = PdfReader(pdf_path)
        if reader.pages:
            return reader.pages[0].extract_text()
        return ""
    except Exception as e:
        logging.warning(f"  - Warning: Could not read {os.path.basename(pdf_path)}. Error: {e}")
        return ""

def parse_json_from_response(response_text):
    """Safely extracts a JSON list from the model's text response."""
    try:
        # Clean up the response in case the model adds markdown
        clean_text = response_text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logging.warning(f"Failed to decode JSON from the API response: {e}")
        logging.debug(f"--- API Response Text ---\n{response_text}\n-------------------------")
        return []
    except Exception as e:
        logging.error(f"  - An unexpected error occurred while parsing JSON: {e}")
        return []

def automate_parsing():
    """Main function to automate the PDF parsing process."""
    setup_logging()
    model = configure_gemini()
    if not model:
        return

    pdf_files = sorted(glob.glob(os.path.join(INPUT_PDF_FOLDER, "*.pdf")))
    if not pdf_files:
        logging.error(f"Error: No PDF files found in the '{INPUT_PDF_FOLDER}' folder.")
        return

    all_entries = []
    total_pages = len(pdf_files)
    logging.info(f"Found {total_pages} pages to process. Starting Skiri-to-English parsing...\n")

    for i in range(total_pages):
        page_n_path = pdf_files[i]
        page_n_text = extract_text_from_pdf(page_n_path)
        page_n_num = i + 1
        logging.info(f"Processing Page {page_n_num}/{total_pages}: {os.path.basename(page_n_path)}")

        page_n1_text = ""
        if i + 1 < total_pages:
            page_n1_path = pdf_files[i + 1]
            page_n1_text = extract_text_from_pdf(page_n1_path)
        
        prompt_content = f"""{MASTER_PROMPT_TEXT}

--- TEXT FROM PAGE {page_n_num} (Page N) ---
{page_n_text}

--- TEXT FROM PAGE {page_n_num + 1} (Page N+1) ---
{page_n1_text}

Extract all entries beginning on Page {page_n_num}. Return valid JSON only.
"""

        retries = 3
        for attempt in range(retries):
            try:
                response = model.generate_content(prompt_content)
                parsed_entries = parse_json_from_response(response.text)
                
                if parsed_entries:
                    all_entries.extend(parsed_entries)
                    logging.info(f"  - Successfully parsed {len(parsed_entries)} entries from page {page_n_num}.")
                else:
                    logging.warning(f"  - No entries parsed from page {page_n_num}.")
                break

            except exceptions.ResourceExhausted:
                wait_time = 30 * (attempt + 1)
                logging.warning(f"  - Rate limit hit. Waiting for {wait_time}s to retry... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            except Exception as e:
                logging.error(f"  - An unexpected error occurred for {os.path.basename(page_n_path)}: {e}")
                break

        # Add small delay between requests to avoid rate limiting
        time.sleep(2)

    # Save all parsed entries to JSON file
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    logging.info(f"\nParsing complete! {len(all_entries)} total entries saved to '{OUTPUT_JSON_FILE}'.")

if __name__ == "__main__":
    automate_parsing()