# prompts/

The written instructions each stage was built from: the prompts given to AI
models, the design documents, and the JSON schemas. Read these to see what a
stage was *asked* to do; read the project log and `reports/` to see what it did.

| File | Date | What it drove |
|---|---|---|
| `dictionary_parsing/AI_Dictionary_Parsing_Instructions.md` | 2026-02 | The instructions the AI parser followed for every dictionary page |
| `dictionary_parsing/Skiri-to-English_JSON_Schema.json`, `English-to-Skiri_JSON_Schema.json` | 2026-02 | The shape of a parsed entry in each section |
| `dictionary_parsing/Example_Skiri-to-English_Output.json`, `Example_English-to-Skiri_Output.json` | 2026-02 | Worked examples given to the parser |
| `dictionary_parsing/README_E2S_Parser.md` | 2026-02 | How the English-to-Skiri parser works |
| `Phase_1_1_Pronunciation_Respelling_Roadmap.md` | 2026-03 | The design of the learner respelling: which English letters stand for which sound, and why |
| `phase_3_2a_sentence_templates.md` | 2026-03-20 | The design of the sentence builder: the ten templates and the Blue Book sentences each comes from |
| `skiri_word_construction_v2.md` | 2026-11-12 | The instruction for the word-construction analysis in `curriculum/roots_v2/`: what "bulletproof" means, the evidence channels, the ground rules |
| `source_fidelity_audit.md` | 2026-11-13 | The instruction for the source-fidelity audit in `reports/source_audit_2026-11/`: full coverage, two readings with the page image deciding, the stages, the checkpoint file that lets an interrupted run be picked up, the grades of evidence. Nothing is applied by the audit |

## Things to know

- These are records. Changing one does not change any output; it only makes
  the record wrong. To change behaviour, change the script.
- `scripts/run_parser_e2s.py` reads the parsing instructions and schema from
  `dictionary_parsing/` when it runs.
- The example words in `Phase_1_1_Pronunciation_Respelling_Roadmap.md` and in
  the parsing instructions were written before the data was cleaned, and some
  show the corrupted characters the parser first produced (such as `®` for the
  glottal stop). Take examples from the database, not from these files.
- The ground rules in `skiri_word_construction_v2.md` (never invent a Pawnee
  form, never generate IPA, show conflicts between the sources, keep ceremonial
  vocabulary for community review) apply to any later work on learner material.
