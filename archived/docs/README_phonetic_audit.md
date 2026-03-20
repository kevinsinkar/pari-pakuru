# Phonetic Audit Agent — Setup & Usage

**Script:** `phonetic_audit_agent.py`  
**Location:** `pari-pakuru/scripts/`  
**Phase:** 1.1 — Pronunciation Respelling & Validation

---

## Quick Start

```bash
cd pari-pakuru/scripts/

# 1. Install dependency (only needed for validate/audit)
pip install google-generativeai

# 2. Run respelling FIRST (no API key needed, fast)
python phonetic_audit_agent.py respell

# 3. Then validate with Gemini (needs API key)
export GEMINI_API_KEY=your_key_here
python phonetic_audit_agent.py validate

# 4. Or run the full pipeline at once
python phonetic_audit_agent.py audit
```

---

## Commands

| Command | What It Does | Uses Gemini? | Cost |
|---------|-------------|--------------|------|
| `respell` | Generates `simplified_pronunciation` for every entry | No | Free |
| `validate` | AI-checks phonetic forms for OCR errors & consistency | Yes | ~tokens |
| `audit` | Runs respell → validate → report in sequence | Yes | ~tokens |
| `report` | Generates markdown summary from existing logs | No | Free |

---

## How It Works

### The Respelling Engine (Local, Deterministic)

The engine converts Parks dictionary phonetic forms into learner-friendly pronunciation:

```
Input:  [pii•ta]        →  Output: "PEE-tah"     (man)
Input:  [haa•tu®]       →  Output: "HAAH-tu'"     (tongue)
Input:  [ka•rii•ku®]    →  Output: "kah-REE-ku'"  (liver)
Input:  [cí•kic]        →  Output: "TSIH-kihts"   (itchy)
```

Rules applied:
- `aa` → `aah`, `ii` → `ee`, `uu` → `oo` (long vowels)
- `a` → `ah`, `i` → `ih`, `u` → `u` (short vowels)
- `c` → `ts`, `®` → `'` (consonant mappings)
- `•` → `-` (syllable breaks)
- Accented vowels → CAPITALIZED syllables

### The Validation Agent (Gemini)

Sends batches of 20 entries to Gemini for judgment calls:
- Does the phonetic form match the headword?
- Any OCR artifacts (garbled characters)?
- Missing glottal stops on nouns?
- Truncated or malformed entries?

Batching keeps token usage efficient. Checkpointing lets you resume if interrupted.

---

## Options

```bash
# Smaller batches (if hitting token limits)
python phonetic_audit_agent.py validate --batch-size 10

# Longer delay between API calls (if rate limited)
python phonetic_audit_agent.py validate --delay 5

# Resume after interruption
python phonetic_audit_agent.py validate --resume
```

---

## Output Files

All outputs land in `Dictionary Data/`:

| File | Description |
|------|-------------|
| `skiri_to_english_respelled.json` | S2E entries with `simplified_pronunciation` added |
| `english_to_skiri_respelled.json` | E2S entries with `simplified_pronunciation` added |
| `phonetic_validation_results.json` | Full validation log (local + AI results) |
| `phonetic_audit_report.md` | Human-readable summary report |
| `phonetic_audit_checkpoint.json` | Resume checkpoint (safe to delete to restart) |

---

## Flag Types & Priority

| Flag | Meaning | Fix How |
|------|---------|---------|
| `phonetic_char_error` | Unknown character in phonetic form | Check source PDF — likely OCR corruption |
| `incomplete_parse` | Required field is empty | Re-parse from source page |
| `possible_ocr_glottal` | Noun missing terminal ® | Very common OCR miss — check manually |
| `missing_syllabification` | No syllable bullets (•) | Some entries lack them; low priority |
| `respell_fail` | Respelling produced empty output | Examine phonetic form for unusual patterns |

---

## Adjusting the Respelling Key

The mapping lives inside the `RespellingEngine` class at the top of the script. To modify:

1. Edit `VOWEL_MAP` or `CONSONANT_MAP` tuples
2. Order matters — longer patterns must come before shorter ones
3. Run `python phonetic_audit_agent.py respell` to regenerate all pronunciations
4. Check the report for entries with `?x?` markers (unmapped characters)
