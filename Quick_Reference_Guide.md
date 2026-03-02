# QUICK REFERENCE GUIDE: Skiri Pawnee Dictionary Parsing

## Priority Hierarchy
1. **CRITICAL:** Phonetic form `[...]` - 100% accuracy required
2. **Required:** Headword (boldface)
3. **Required:** Grammatical class (SMALL CAPS)
4. **Important:** Etymology `<...>` (when present)
5. **Important:** Paradigmatic forms 1-5 (for verbs)
6. **Optional:** All other fields

## Visual Recognition Patterns

### Delimiters
| Pattern | Meaning | Example |
|---------|---------|---------|
| **Boldface** | Entry headword | **kawPuktawuh** |
| `[...]` | Phonetic form | `[-wii•-t,u®(h)]` |
| `(...)` | Preverb or verb class | `(uur...)` or `(4)` |
| `{...}` | Additional grammatical forms | `{pl. obj., raawi-}` |
| `<...>` | Etymology | `<uur+awi+uusik>` |
| SMALL CAPS | Grammatical class | VI, VT, N |
| `•` | Bullet for examples/forms | • example sentence |
| *Italics* | Usage notes | *as before completion* |

### Entry Structure

```
HEADWORD (preverb) [phonetic] CLASS (verb_class) {forms}
1. definition one, usage notes. 2. definition two.
<etymology breakdown, literal meaning>
1. form1 2. form2 3. form3 4. form4 5. form5
• example sentence
```

## Common Patterns

### Skiri-to-English
- Single entry per headword
- Two parts (I: basic info, II: forms/examples)
- No cross-references

### English-to-Skiri
- Multiple subentries possible
- Three parts (I: basic info, II: forms/examples, III: cross-refs)
- Cross-references: `see WORD {skiri}; WORD {skiri, skiri}`

## Special Characters in Phonetics

| Character | Name | Example |
|-----------|------|---------|
| ® | Glottal stop | `paátu®` |
| • | Syllable break | `ka•wi•®úk` |
| : | Vowel length | `aa:` |
| ´ | Accent/stress | `úk` |
| ˘ | Short vowel | (breve) |
| ¯ | Long vowel | (macron) |

## Grammatical Classes Cheat Sheet

**Verbs:**
- VI = intransitive verb
- VT = transitive verb
- VD = descriptive verb
- VL = locative verb
- VP = patientive/passive verb
- VR = reflexive verb

**Verb Classes:**
- (1), (1-a), (1-i) = Class 1 variants
- (2), (2-i) = Class 2 variants
- (3) = Class 3
- (4), (4-i) = Class 4 variants
- (u) = Descriptive-like
- (wi) = Locative-like

**Other:**
- N = noun
- ADJ = adjective
- ADV = adverb
- PRON = pronoun
- NUM = numeral

## Five Standard Paradigmatic Forms (Verbs)

1. **Form 1:** 1st person singular, indicative, perfective
2. **Form 2:** 3rd person singular, indicative, perfective
3. **Form 3:** 3rd person singular, indicative, imperfective
4. **Form 4:** 3rd person singular, absolutive, subordinate perfective
5. **Form 5:** 3rd person singular, indicative, perfective intentive

*Note:* Some verb classes lack certain forms - extract what's present.

## Parsing Checklist

### Before Processing
- [ ] Identify section (Skiri→English or English→Skiri)
- [ ] Check for page continuations
- [ ] Note column layout (left/right)

### For Each Entry
- [ ] Extract headword (boldface)
- [ ] Extract phonetic form `[...]` **WITH 100% ACCURACY**
- [ ] Extract grammatical class (SMALL CAPS)
- [ ] Extract verb class if present `(...)`
- [ ] Extract additional forms `{...}`
- [ ] Parse numbered glosses
- [ ] Extract etymology `<...>` if present
- [ ] Extract 5 paradigmatic forms (numbered 1-5)
- [ ] Extract bulleted examples/forms

### Validation
- [ ] Phonetic form matches exactly (all diacritics preserved)
- [ ] Required fields present
- [ ] Structure matches schema
- [ ] Cross-page entries merged correctly

## Common Errors to Avoid

❌ **DON'T:**
- Guess or approximate phonetic forms
- Skip diacritical marks
- Merge different entries
- Ignore special characters (®, •, etc.)
- Skip preverb notation

✅ **DO:**
- Extract phonetic forms character-for-character
- Preserve all special formatting
- Track entry boundaries carefully
- Note uncertainties in metadata
- Validate against schema

## Quick Decision Tree

```
Entry found?
├─ Is headword in boldface? → YES: Start new entry
├─ Phonetic in [...]? → CRITICAL: Extract exactly
├─ SMALL CAPS present? → Grammatical class
├─ (...) after class? → Verb class
├─ (...) after headword? → Preverb
├─ {...}? → Additional forms
├─ <...>? → Etymology
├─ Numbered 1-5? → Paradigmatic forms
├─ Bullet •? → Example or additional form
└─ "see" followed by word? → Cross-reference (English-to-Skiri only)
```

## Example Minimum Valid Entry

**Skiri-to-English:**
```json
{
  "headword": "wiiłik",
  "part_I": {
    "phonetic_form": "[-wii•-t,u®(h)]",
    "grammatical_info": {
      "grammatical_class": "VI"
    },
    "glosses": [
      {"definition": "sit down"}
    ]
  }
}
```

**English-to-Skiri:**
```json
{
  "english_entry_word": "stop",
  "subentries": [
    {
      "part_I": {
        "skiri_term": "awPuusik",
        "phonetic_form": "[=a•wi•®uu•s,u®(h)=]",
        "grammatical_classification": {
          "class_abbr": "VI"
        },
        "english_glosses": [
          {"definition": "quiet down"}
        ]
      }
    }
  ]
}
```

## File Output Locations

When complete, move parsed JSON files to:
- `/mnt/user-data/outputs/parsed_entries.json`

Include in filename:
- Page range processed
- Section (Skiri-to-English or English-to-Skiri)
- Example: `skiri_to_english_p100-101.json`
