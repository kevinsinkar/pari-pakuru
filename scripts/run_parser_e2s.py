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
INPUT_PDF_FOLDER = "split_pdf_pages_ENGLISH_TO_SKIRI_missed"  # Folder with the English-to-Skiri pages
OUTPUT_JSON_FILE = "english_to_skiri_complete_missed.json"

SCHEMA_FILE = "English-to-Skiri_JSON_Schema.json"  # Path to the JSON schema file
INSTRUCTIONS_FILE = "AI_Dictionary_Parsing_Instructions.md"  # Path to parsing instructions

# 3. LOAD PARSING INSTRUCTIONS
def load_parsing_instructions():
    """Loads the comprehensive parsing instructions and schema."""
    instructions = ""
    schema = ""
    
    if os.path.exists(INSTRUCTIONS_FILE):
        with open(INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
            instructions = f.read()
    else:
        logging.warning(f"Instructions file '{INSTRUCTIONS_FILE}' not found. Using embedded instructions.")
    
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = f.read()
    else:
        logging.warning(f"Schema file '{SCHEMA_FILE}' not found.")
    
    return instructions, schema

# 4. DEFINE THE MASTER PROMPT FOR THE API
MASTER_PROMPT_TEMPLATE = """
# ENGLISH-TO-SKIRI DICTIONARY PARSING TASK

You are parsing the **English-to-Skiri** section of a Skiri Pawnee bilingual dictionary for language revitalization purposes. **Complete accuracy is essential** - this data will be used to teach and preserve the Skiri language.

## CRITICAL PRIORITY
**PHONETIC FORMS in square brackets [...] must be extracted with 100% ACCURACY.**
- Preserve ALL diacritics, special characters (®, •, accents, macrons)
- Extract character-for-character, including syllable breaks (•)
- This is the HIGHEST PRIORITY field in every entry

## YOUR TASK
You will receive text from **TWO consecutive pages** (Page N and Page N+1):

1. **Parse ALL English entries that BEGIN on Page N**
2. **Use Page N+1 text ONLY** to complete any entry from Page N that spans across pages
3. **DO NOT parse new entries that begin on Page N+1**

## ENGLISH-TO-SKIRI STRUCTURE (Key Differences from Skiri-to-English)

### Top Level: English Entry Word
- Boldface English word starts each entry
- Example: **stop**, **water**, **house**

### SUBENTRIES (Critical Feature)
- **One English word can have MULTIPLE Skiri translations**
- Each Skiri translation = separate subentry
- Each subentry can have Parts I, II, and III

### Each Subentry Contains:

**PART I: Basic Information**
- **Skiri term** (boldface Skiri word)
- **Stem preverb** (if present): appears AFTER stem in parentheses, e.g., (uur...)
- **Phonetic form** [...] - CRITICAL: Extract with 100% accuracy
- **Grammatical classification**: SMALL CAPS abbreviation (VI, VT, N, etc.)
- **Verb class**: Number in parentheses (1), (1-a), (2), (4), etc.
- **Additional grammatical forms**: In curly brackets
- **English glosses**: Numbered definitions with usage notes in italics
- **Etymology**: In angle brackets with constituent breakdown

**PART II: Illustrative Forms** (when present)
- **5 standard paradigmatic forms** (numbered 1-5 for verbs)
  1. 1st Person Singular Subject, Indicative Mode, Perfective
  2. 3rd Person Singular Subject, Indicative Mode, Perfective
  3. 3rd Person Singular Subject, Indicative Mode, Imperfective
  4. 3rd Person Singular Subject, Absolutive Mode, Subordinate Perfective
  5. 3rd Person Singular Subject, Indicative Mode, Perfective Intentive
- **Additional forms**: Marked with bullets (•)
- **Examples**: Sentence examples with Skiri text and English translation

**PART III: Cross-References** (UNIQUE TO ENGLISH-TO-SKIRI)
- Format: "see ENGLISH_WORD" followed by Skiri forms in curly brackets
- Extract the English term and all its Skiri equivalents
- Multiple cross-references separated by semicolons

## JSON OUTPUT SCHEMA

{schema_content}

## EXTRACTION RULES

### Entry Boundaries
- **New entry starts**: Boldface English headword
- **Entry ends**: Where next boldface English headword begins
- **Cross-page entries**: Use alphabetical headers to verify sequence, merge before parsing

### Phonetic Form Extraction (CRITICAL)
- Extract EXACTLY as written between [...] brackets
- Preserve: ®, •, :, all diacritics, all special characters
- Example: [=a•wi•®uu•s,u®(h)=] must be extracted character-for-character

### Subentry Recognition
- Each new boldface Skiri term under an English word = new subentry
- Number subentries sequentially
- Extract complete Part I, II, III for each

### Cross-Reference Parsing (Part III)
- Begins with "see" keyword
- Format: English term followed by Skiri forms in curly brackets
- Extract as structured array with english_term and skiri_equivalents

### Missing Data Handling
- Some verb classes lack certain paradigmatic forms - this is normal
- Use null for missing fields
- Never guess or approximate - extract exactly or mark as null

### Column Layout
- Process left column completely, then right column
- Track page and column in metadata

## VALIDATION CHECKLIST
Before outputting each entry, verify:
- Phonetic form extracted with 100% accuracy
- All subentries captured
- Grammatical class in SMALL CAPS extracted
- Etymology angle brackets matched correctly
- Cross-references (Part III) properly structured
- JSON matches schema exactly

## OUTPUT FORMAT
Return ONLY valid JSON following the schema above. No markdown, no explanatory text, just the JSON array.

---

**REFERENCE MATERIALS:**
The three attached PDFs provide essential context:
- 05-Organization_of_the_Dictionary.pdf: Primary guide for English-to-Skiri structure
- 01-Abbreviations_and_Sound_Key.pdf: Grammatical class abbreviations
- 02-Sounds_and_Alphabet.pdf: Phonetic character reference

**REMEMBER:** This dictionary is for Skiri language revitalization. Accuracy and completeness are essential for preserving this endangered language.
"""

####################
### SCRIPT LOGIC ###
####################

def setup_logging():
    """Configures logging to output to both console and a file."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the lowest level of messages to capture

    # Prevent handlers from being added multiple times if the function is called again
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a formatter to define the log message structure
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Create a handler to write logs to a file
    file_handler = logging.FileHandler('parser.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a handler to stream logs to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def configure_gemini():
    """Configures the Gemini API with optimal settings for linguistic parsing."""
    if API_KEY == "YOUR_API_KEY" or not API_KEY:
        logging.error("Error: API key not configured. Please set it in the script or as an environment variable.")
        return None
    
    genai.configure(api_key=API_KEY)
    
    # Using Gemini 2.5 Pro for highest accuracy on linguistic data with special characters
    # JSON mode ensures valid output every time
    model = genai.GenerativeModel(
        'gemini-2.5-pro',
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1  # Low temperature for consistency and accuracy
        }
    )
    return model

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
    except json.JSONDecodeError:
        logging.warning("Failed to decode JSON from the API response.")
        logging.debug(f"--- API Response Text ---\n{response_text}\n-------------------------")
        return []
    except Exception as e:
        logging.error(f"  - An unexpected error occurred while parsing JSON: {e}")
        return []

def automate_parsing():
    """Main function to automate the English-to-Skiri PDF parsing process."""
    setup_logging()
    model = configure_gemini()
    if not model:
        return
    
    # Load parsing instructions and schema
    logging.info("Loading parsing instructions and JSON schema...")
    instructions, schema = load_parsing_instructions()
    
    # Create the master prompt with schema embedded
    master_prompt = MASTER_PROMPT_TEMPLATE.format(schema_content=schema)


    pdf_files = sorted(glob.glob(os.path.join(INPUT_PDF_FOLDER, "*.pdf")))
    if not pdf_files:
        logging.error(f"Error: No PDF files found in the '{INPUT_PDF_FOLDER}' folder.")
        return

    all_entries = []
    total_pages = len(pdf_files)
    logging.info(f"Found {total_pages} pages to process.")
    logging.info("Starting COMPLETE English-to-Skiri dictionary parsing...")
    logging.info("Extracting: phonetic forms, etymologies, paradigms, cross-references - all data\n")

    for i in range(total_pages):
        page_n_path = pdf_files[i]
        page_n_text = extract_text_from_pdf(page_n_path)
        logging.info(f"Processing Page {i+1}/{total_pages}: {os.path.basename(page_n_path)}")

        page_n1_text = ""
        if i + 1 < total_pages:
            page_n1_path = pdf_files[i+1]
            page_n1_text = extract_text_from_pdf(page_n1_path)
        
        # Build the complete prompt with context and page text
        prompt_content = [
            master_prompt,
            f"\n\n--- TEXT FROM PAGE N (Page {i+1}) ---\n{page_n_text}\n\n--- TEXT FROM PAGE N+1 (Page {i+2 if i+1 < total_pages else 'END'}) ---\n{page_n1_text}"
        ]

        retries = 3
        for attempt in range(retries):
            try:
                response = model.generate_content(prompt_content)
                parsed_entries = parse_json_from_response(response.text)
                
                if parsed_entries:
                    # Track metadata for each entry
                    for entry in parsed_entries:
                        if "entry_metadata" not in entry:
                            entry["entry_metadata"] = {}
                        entry["entry_metadata"]["source_page"] = i + 1
                    
                    all_entries.extend(parsed_entries)
                    logging.info(f"  - Successfully parsed {len(parsed_entries)} English entries with complete data.")
                else:
                    logging.warning(f"  - No entries parsed from page {i+1}")
                break

            except exceptions.ResourceExhausted:
                wait_time = 30 * (attempt + 1)
                logging.warning(f"  - Rate limit hit. Waiting for {wait_time}s to retry... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            except Exception as e:
                logging.error(f"  - An unexpected error occurred for {os.path.basename(page_n_path)}: {e}")
                if attempt == retries - 1:
                    logging.error(f"  - Failed to parse page {i+1} after {retries} attempts. Moving to next page.")
                break

    # Save complete output
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    logging.info(f"\n{'='*60}")
    logging.info(f"PARSING COMPLETE!")
    logging.info(f"{'='*60}")
    logging.info(f"Total English entries parsed: {len(all_entries)}")
    logging.info(f"Output file: '{OUTPUT_JSON_FILE}'")
    logging.info(f"Data includes: phonetic forms, etymologies, paradigms, cross-references")
    logging.info(f"Ready for Skiri language revitalization application!")
    logging.info(f"{'='*60}\n")

if __name__ == "__main__":
    automate_parsing()