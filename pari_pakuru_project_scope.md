# Pari Pakuru — Skiri Pawnee Language Tool: Project Log

*Last updated 2026-11-14. This is the record of what was done in each phase,
with its results, and of what is still open. What to do next, in order, is in
[What's next](#whats-next). For the folder layout see
[README.md](README.md); for the script behind each step see
[scripts/README.md](scripts/README.md).*

## Project Goal

Build a comprehensive Skiri Pawnee language preservation tool: a searchable, linked dictionary with pronunciation guides, semantic tags, morphological grammar engine, and sentence construction — all validated against source materials.

---

## Status at a glance

| When | Phase | What | State |
|---|---|---|---|
| 2026-02 | parse | Both dictionary sections read from page PDFs into JSON by an AI model; a second pass verified every field | done |
| 2026-03-07 | 1.1a–d | Character repair, linking of the two sections, respelling and learner spelling, completeness audit | done |
| 2026-03-08 | 1.2 | SQLite database | done |
| 2026-03-08 | 2.1 | Topic tags | done |
| 2026-03-08 | 2.2 | Blue Book cross-check | done |
| 2026-03-08 | 2.3 | Sound-change rules (24) | done |
| 2026-03-08 → 03-20 | 3.1 | Verb template, conjugation engine (79.4% of Appendix 1 as Parks prints it, which it was fitted to; 15.0% of the dictionary's own 9,559 verb forms, which it was not; the 90.3% reported until 2026-11-13 was measured against a misread copy), form 2 prediction (87.2% of dictionary verbs, on the forms its rules were read from), accent rules | **conjugation engine and accent rules withdrawn 2026-11-14**; form 2 prediction kept as a checker, its score removed |
| 2026-03-18 | 3.1.5 | Noun possession | engine **withdrawn 2026-11-14**; noun pages show a lookup of printed forms instead |
| 2026-03-20 | 3.1.6 | Function words (418) | done; four OCR slips removed 2026-11-14 (414); its Blue Book rows set to the scan's readings the same day (406; item 62). Meanings never checked |
| 2026-03-10 → 03-21 | 4.1, 4.3, 4.4 | Web app, confidence scores, community feedback | done; the confidence scores (4.3) removed 2026-11-14 |
| 2026-03-20 | 3.2a | Sentence templates (10) | **rebuilt 2026-11-14** on printed rows of the Blue Book table |
| 2026-03-20 | 5.2 | Flashcards in the app; Anki export (unused) | done |
| 2026-09-01 | audit | Extraction audit and repairs; IPA cross-checked against the PDF text layer | done; short residual list |
| 2026-09-01 | 3.2b | Person and mode derived from attested forms | **repaired 2026-11-14**; 97.3% on verbs set aside beforehand; forms labelled as derived |
| 2026-09-01 | 5.1 | Blue Book lessons in the app | done |
| 2026-09-02 | 5.2b | Spaced-repetition study in the app | done |
| 2026-09-12 | 5.3 | Static site on GitHub Pages | done |
| 2026-10-01 | audit | Flashcard and static-site audit; IPA and page references restored on the site | done in part |
| 2026-10-12 | 5.1, 5.2 | Lesson vocabulary linked; lesson titles repaired; flashcard curriculum frozen | done |
| 2026-11-07 → 11-10 | 6.1 | Word-building guide, version 1; weekly paper flashcards and printable sheets; respelling repair | guide superseded by 6.2; flashcards in use |
| 2026-11-12 | 6.2 | Word-construction analysis, version 2: evidence tiers, gold sets, learning path | done; awaiting human review |
| 2026-11-13 | | Repository clean-up; documentation brought up to date | done |
| 2026-11-13 | fixes | Data fixes (accent marks the decoding had dropped, page numbers, duplicates, letter-spaced text); possession suffix *-hiriʔ*; weekly flashcards rebuilt from version 2; flashcard Week 20 held for community review | done |
| 2026-11-13 | audit | Source-fidelity audit: every stored value compared with the printed page; character table verified against the glyphs; database written to git as text | done; 2,250 fixes proposed; applied in the next rows |
| 2026-11-13 | fixes | The audit's fixes reviewed and applied where the evidence is solid: 807 changes (152 forms of Appendix 1; appendices 2 and 3; chapters 3 and 4; 19 dictionary verb forms; 162 citations from other languages; 27 headwords; 393 column labels; one missing entry added, one phantom removed) | done; judgement calls left for a person (open items 41, 45) |
| 2026-11-13 | IPA | Parks's own phonetic symbols stored for all 4,244 of his entries (ə́, ɪ́, the syllable dot, the edge dash); 75 forms corrected in content, 9 added; respelling and learner spelling made again and checked | done |
| 2026-11-13 | Blue Book | The rest of the Blue Book forms read from the scan (843 more crops; with the audit's 153 that is 949 distinct forms, every one that has a page): 715 corrected (565 accents restored, 105 OCR slips, 45 apostrophes, dots and spaces); three entries built on misread forms corrected; made-up phonetic forms removed from the 93 Blue Book-only entries | done; 77 forms left for a person (open item 42) |
| 2026-11-13 | rebuild | Static site, weekly flashcards, printable sheets and word-construction outputs rebuilt from the corrected data; engines measured again | done |
| 2026-11-13 | hosting | The PythonAnywhere hosting of the web app retired; `wsgi.py` removed. GitHub Pages is the only place the project is published; the Flask app is a local tool | done |
| 2026-11-14 | fixes | Page citations: every Parks entry cites the page of the printed book (3,511 held the number of a PDF file, 348 less) | done |
| 2026-11-14 | fixes | What the dictionary prints and the database lacked, set from the PDF's text layer: 1,447 values (684 hyphens the typesetter put at line ends, 21 derived stems, 18 examples, citations, spacing, punctuation); three verb forms that are not printed removed | done; 37 differences left, each explained |
| 2026-11-14 | Blue Book | A second blind reading of the 77 forms left open: 35 settled. Corrected forms carried into three more tables (628 values). Three words of the grammar chapter corrected | done in part; continued the same day (the three rows below) |
| 2026-11-14 | site | The public site shows the whole entry (examples, verb forms, Parks's analysis, cited forms) and says truthfully what it is: About page rewritten, a "Send a correction" link on every result, "accent" in place of "pitch" | done |
| 2026-11-14 | grammar chapter | A second blind reading of the whole grammar chapter (three readers, 613 forms). The two blind readings do not differ on one Skiri word, and every Skiri word of the stored chapter now stands in both: 38 words corrected (vowel length, glottal stops, and twelve accents the page does not have), 22 pieces of breakdown lines (*-Ø PERF*, *-hus*), Table 17 put back as printed | done |
| 2026-11-14 | Blue Book | 25 of the 42 open forms found at their own place on the page by the English stored with them, and read there: 18 corrected, 7 confirmed as stored | done; 17 left for a person (open item 42) |
| 2026-11-14 | decisions | Confirmed by the project owner: the ceremony-tagged entries show senses and examples only until the community review; "accent" is the word for the marks; the About page as rewritten; corrections come in as GitHub issues | recorded (open items 9, 50) |
| 2026-11-14 | review | The packet for the Pawnee Nation's language and culture people: one 41-page document and an answer sheet, built from the database | ready; not sent (rank 1) |
| 2026-11-14 | engines | A prompt for a fresh session to review the grammar engines and put a decision before the owner | written |
| 2026-11-14 | engines | **The engines review**, run through its third stage: all eight engine files read in full and every rule traced to its source; each engine measured on attested forms, seen and unseen apart, without tuning; a decision paper | paper: [reports/engines_review/decision.md](reports/engines_review/decision.md). Answered by the owner the same day; see the next row |
| 2026-11-14 | engines | **The eight decisions carried out** (Stage 4 of the review). The audit's readings put into the lessons' running text and titles (214 places, 12 titles); conjugation engine and accent rules withdrawn; the guide prints Parks's own tables as read from the page; sound changes kept as a reference with an honest measure (8 of 39); the form 2 score removed; person derivation repaired and tested on a sealed half (97.3% of 816 forms on 1,059 unseen verbs); the possession box replaced by a lookup of printed forms; the sentence builder rebuilt on printed rows. Four engine tables dropped | done; committed and pushed the same day: [reports/engines_review/stage4.md](reports/engines_review/stage4.md) |
| 2026-11-14 | owner | The owner's answer to the five points Stage 4 left open: commit and push; read the notes of all twenty lessons from the page; leave the weak rule of person derivation as it is; correct the Blue Book table's ties; make the pass over the function-word tables | all done the same day (the three rows at the end of this table), committed and pushed (`fad4a3e`) |
| 2026-11-14 | English index | Rebuilt from the printed page: the English-to-Skiri file and the two tables read from the text layer by its fonts. 6,431 English entries, 5,165 Skiri terms (5,162 linked to their entry), 4,578 cross-references; page numbers are book pages | done; 99.99% of fields equal to print by the audit's comparison (the tables were at 77.7%) |
| 2026-11-14 | reading | Front-matter chapters 2 and 5 read for the first time, twice: 195 Skiri forms, every one the same in both readings. Stored as forms, tables and the project's summaries, not as running text | done |
| 2026-11-14 | reading | The tables of the grammar chapter put together as printed from the two existing readings (12 of 14 read the same in both); the Blue Book glossary itemised (573 rows; 589 of 644 page references confirmed by the page they point to) | done; tables 6 and 7 and 55 references left for a person |
| 2026-11-14 | Blue Book | The 93 "Blue Book-only" entries: the printed form found for 87; 37 turn out to be words Parks has, in the textbook's spelling. The site shows both facts; the About page corrected | done; what to do with the 37 is open (item 52) |
| 2026-11-14 | printables | A printable word list (372 words) and Parks's seven verbs in full (Appendix 1, 770 forms) | done |
| 2026-11-14 | site | **The public site rebuilt around the learner**, at the owner's request: a "Start here" path of six steps; the Sounds page with what chapter 2 says of *c* and *r*, and any word taken syllable by syllable; a Word building page (the dictionary's printed derivation of 3,319 entries cut at its plus signs, and the words that share a piece); a Verbs page (the five forms, Appendix 1 in three views with a self-test, Appendix 2, tables 6 to 17); six practice games; words by topic; the two printable documents linked. Every Skiri form shown is printed; nothing is computed | done; committed and pushed the same evening with the owner's word (`cbeb592`, site `12759c6`). The plain-English explanations are the project's and unreviewed (open items 65 to 68); five decisions of that session await the owner (rank 2) |
| 2026-11-14 | Blue Book | **The ties of Blue Book words to dictionary entries made again**: the 414 ties that had been made by a shared beginning (*asáki* 'dog' under the entry *a*) judged by form and meaning; 65 re-tied, 349 untied. A Blue Book sentence is an example of an entry only if one of its words is tied to it: 43 of 88 kept | done (item 61); 257 of 1,026 rows tied |
| 2026-11-14 | function words | The two function-word tables gone over against the scan's readings: 32 rows corrected, 9 deleted | done (item 62); meanings and word classes not checked |
| 2026-11-14 | lessons | **The lessons read from the page, line by line.** Every line of the titles, dialogues and notes that is not plain English cut from the scan and read: 911 lines, 79 a second time. 328 places corrected (at 164 of the 286 that one reading settles, the audit's reader had read the same at that place; none where it had read otherwise), 8 titles set, the next lesson's title and the glossary cut from the end of the notes; 13 rows of the Blue Book table corrected at their own line, two of them because the audit's crop had been cut at a line above. Then **the dialogues paired**: each Pawnee line with the English the page prints on its row (105 lines; in 83 of 156 stored lines the English had stood in the Pawnee field or was missing) | done (items 60, 69); committed and pushed (`fad4a3e`). Three places under a flaw in the scan and three doubts of reading are for a person with the book (item 70) |
| 2026-11-15 | Blue Book | **A Blue Book word given the English of its own row of the page.** The extraction had read the two columns of a word list one after the other, and in three places every word had its neighbour's meaning: the five Useful Phrases of lesson 18, six words of lesson 10 (*asku•ra•wákahu'* stood as 'police man'; it is 'judge'), two lines of lesson 9. Found by reading, from the scan's text layer, what stands to the right of each form on its row; 16 meanings corrected, one printed word that had no row added (*ti•ká•isat* 'he went home'), one Blue Book-only dictionary entry corrected ('judge' for a verb form that means 'he is killing it') | done; committed and pushed the same day (`4c32588`). Ten rows whose form the text layer garbles are unchecked (item 73) |
| 2026-11-15 | site | **The first five points of the feedback on the learner pages carried out**, at the owner's word: the lesson pages keep the book's order (the feedback had said the book begins with the dialogue; it begins with the basic words) and let a learner cover one side of a dialogue; a Phrases page with the 113 Useful Phrases by situation and the two conversations of lesson 20; a practice box in the browser that brings a word back after 1, 3, 7, 14 and 30 days; one visible line on which spelling to learn to write; no pronunciation of a stem beside a Blue Book word that is a form of it. "Start here" has seven steps, the lessons second | done; committed and pushed the same day at the owner's word (`58d6ae9`, site `0168bb1`). Decisions in it await the owner (rank 2) |
| 2026-11-15 | sources | **A register of sources.** The owner brought a catalogue of 59 further sources on Pawnee (programmes, archives, books, recordings), each rated and with a note on rights. It is now `sources/catalogue.json`, without its e-mail address, with the project's own decision beside each record: link to it, check against it, ask before copying, or hold it back as ceremonial (18). Every link was tried: two had moved and were found again, two gave no answer. A page "Learn with others" lists the 8 that are fit for learners, each opened and read first | done; committed and pushed the same evening. Nothing of any source is copied |
| 2026-11-15 | dialect | **The textbook is not a Skiri book, and the site now says so.** *Pari Pakuru'* writes for both dialects in a South Band-based spelling: its alphabet chapter says a Skidi speaker says *i* for its *e* and *h* for its *hr*, and that its accent marks are South Band. The statements were read from the scan. 298 Blue Book rows and 22 Blue Book-only entries carry a mark with its reason: the book's own (SK) or (SB) on 20, "SB spelling" on 300. Lesson, phrases and flashcard pages carry a line on the two dialects | done; committed and pushed the same evening. The Skiri form of a line cannot be had from the books (items 79, 80) |
| 2026-11-15 | sound | **"Hear it at Indiana University"**: every dictionary word links to a search for it in the online Skiri dictionary of the university's Institute for Indigenous Knowledge, where some entries have a recording. A link; no sound is stored | done; committed and pushed the same evening. Of ten words taken at random, eight were found (item 81) |
| 2026-11-15 | permission | Both books are in copyright (the textbook: the Pawnee Indian Tribal Business Council, 1979; the dictionary: University of Nebraska Press, 2008), and the site shows their content. Three letters are drafted for the owner to send; the review packet has a sixth part | **the owner's to send.** Decision of 2026-11-15: ask, and change nothing in the repository or on the site on that account until answers come (item 77) |
| 2026-11-15 | word web | **A picture of how words share their pieces**, asked for by the owner ("word bubbles connected to common descriptors, e.g. bear, black bear, brown bear, white bear"). A new page, `wordweb.html`: each word is a box, each piece of its printed derivation an oval, and a line joins the two. It opens on the words with "bear" in the meaning; choosing the oval of a piece brings in the other words in which the dictionary prints it. Drawn from the same file as the word-building page; no form and no analysis is added | done; committed and pushed the same evening. The page joins words by the letters of a piece and says so (item 85) |
| 2026-11-15 | spelling | **The dictionary's own spelling is shown first, and a switch at the top of every page changes it to the learner spelling**, asked for by the owner ("the default spelling to be Parks, but a toggle button on the top"). Until then the learner spelling stood first everywhere. Every page now carries a dictionary word in both spellings and shows one; the choice is kept in the visitor's browser. The same in the local app, where a cookie on the server did it before | done; committed and pushed the same evening. The line on which spelling to write was reworded (item 89) |

The database on 2026-11-15: 4,337 entries (4,244 from Parks, 93 Blue Book
only), 5,504 senses, 9,559 verb forms for 2,239 verbs, 2,607 examples, 21
derived stems, IPA for the 4,244 Parks entries (2,218 with an accent mark)
and for none of the Blue Book-only ones. Compared with the printed page,
50,807 of 50,837 dictionary fields are identical (99.94%). Two small tables
came with the second part of 2026-11-15 and hold no Pawnee form of their own:
`sources` (59 rows, the register) and `bb_dialect_labels` (320 rows: which
textbook forms carry SK, SB or "SB spelling", and why). The text dump has
46,738 rows in 23 tables. Full table list: [Quick_Reference_Guide.md](Quick_Reference_Guide.md).

---

## What's next

*Ranked again on 2026-11-14, a third time. The second ranking of that day had
four items. Since then the review packet and the engines prompt were written,
the English index was rebuilt from the page, and everything rank 4 listed was
read or built. What is left is mostly not code. Numbers in the last column
are open items, further down. Later the same day the engines review was run,
its paper answered and its eight decisions carried out, and that work was
committed and pushed. The three follow-ups the owner then asked for (the
lessons read from the page, the Blue Book ties, the function-word tables)
were done the same evening, the dialogues were paired, and all of it was
published together with the learner pages. Rank 2 is therefore new again:
the owner has not yet looked at what went public in their name. The other
ranks are as they were. On 2026-11-15 the owner asked for the first five
points of the feedback file; they were done that day and, at the owner's word,
committed and pushed (`4c32588`, `58d6ae9`, `0168bb1`). Rank 2 now also holds
what that work decided. The same day the owner brought a catalogue of 59
further sources and approved a plan for them. Its first stages are done (the
register, the page "Learn with others", the dialect marks, the links to
sound) and were committed and pushed that evening at the owner's word.
Rank 1 has changed with it:
the catalogue names whom to write to, and it showed that permission has to
be asked for the two books themselves. A third request of the same day, a
picture of how words share their pieces, is built as well (the "word web")
and was committed with the rest. The owner looked at it and answered "no
changes". A fourth request of that day followed: the dictionary's own
spelling first, with a switch for the learner spelling. It was built that
evening and pushed with the rest ("commit and push").*

How the ranking is made: first what only people outside the project can
settle and takes longest to arrange; then what is wrong or missing in front
of learners on the public site; then what makes the stored data more
complete; last, what nobody outside this repository can see.

Size: **small** is part of one working session, **medium** one or two
sessions, **large** more.

| Rank | What | Why at this rank | Who | Size | Open items |
|---|---|---|---|---|---|
| 1 | **Send the three letters, and the review packet with the first** | The textbook is the Nation's (its copyright page asks for the written permission of the Pawnee Tribal Business Council) and the dictionary is the University of Nebraska Press's; the site shows the content of both and nobody was asked. The letters are drafted in `community_review/letters/` (not in git): to the Pawnee Nation's language programme and Cultural Resources Division, with the packet; to the Institute for Indigenous Knowledge at Indiana University; to the Press. The packet is ready ([community_review/](community_review/)), now in six parts. The answers decide whether the lessons stay, whether flashcard Week 20 is ever shown, whether the word-building guide is published, how much of the ceremony-tagged entries is shown, how the two dialects are presented, what learners are told about *kt* and *tt*, and whether anything of another source may be copied in | You: read the three drafts, fill in the square brackets, send them. The answers are theirs to pace | Small | 77, 1, 2, 3, 14, 43, 50, 9, 53 |
| 2 | **Look at the published site and settle the decisions made for you** | On the evening of 2026-11-14 the learner pages, the corrected lessons and the paired dialogues went public on the owner's word ("I leave it to your judgement"), with choices in them that two sessions made and the owner has not confirmed. Five on the learner pages: the project's own word-construction analysis stays unpublished; nothing on *kt* and *tt* on the Sounds page; two sentences of the About page; the heading "Learn Skiri Pawnee"; the weekly flashcard PDFs not linked. Three in the lessons: square brackets where the scan is damaged; the glossary and the next lesson's title cut from the end of the notes; 13 rows of the Blue Book table changed on one reading. One session's feedback on the learner pages is in [reports/learner_site_feedback_2026-11-14.md](reports/learner_site_feedback_2026-11-14.md); its first five points were carried out on 2026-11-15 and pushed the same day at the owner's word. That work made choices too: the lesson pages keep the book's order, with the basic words before the dialogue; the phrases are listed under eight situations of the project's choosing; the menu has an eleventh link, "Phrases", and folds below 1,024 pixels; "Start here" has seven steps with the lessons second; the wording of the line on spelling; 16 meanings of Blue Book words changed by the row of the page. The second part of 2026-11-15 (the register, "Learn with others", the dialect marks, "Hear it") and the third (the word web) and the fourth (the spelling switch) were **committed and pushed on the evening of 2026-11-15** at the owner's word. Their choices are listed in their phase entries; the owner answered "no changes" to the third and "commit and push" to the fourth. Say "commit and push" when you have looked, or what to change | You; then code | small | 65 to 68, 70, 73 to 76 |
| 3 | **Decide what the 93 "Blue Book-only" entries are** | 37 of them are words Parks has, written in the textbook's South Band-based spelling and without long vowels; 22 are written with *e* or *hr* and are marked "SB spelling" since 2026-11-15 (the textbook writes *e* where a Skiri speaker says *i*, and Parks writes *ii*). They sit in the first three flashcard weeks as if they were other words, with a learner respelling made from the textbook's spelling. The site now names the dictionary's entry beside them; whether to teach the dictionary's form instead is a decision about the frozen flashcard list | Your decision, with a person who knows the language if one can be asked; then code | Small to medium | 52, 35, 21 |
| 4 | **Use what was rebuilt** | The English index now links 5,162 Skiri terms to their entries and holds Parks's cross-references as printed. The public search does not use either yet; the local search still joins on the spelling of the headword. The pronunciation guide said nothing of what chapter 2 tells learners (*c* as [ts] or [č], *r* often *n* at the start of a word); since the sixth part of 2026-11-14 the Sounds page does, and the topic tags are shown, so what is left of this rank is the index, the cross-references and *kt*/*tt* | Code; the wording about speakers after rank 1 | Medium | 48, 53 |
| – | *For a person with the books, whenever one is at hand* | 17 Blue Book forms the scan cannot settle; in the lessons, three places under a flaw in the scan and four small doubts (70); 37 small differences in the dictionary; the empty cell of *tir* in Appendix 2; tables 6 and 7 of the grammar chapter (two diagrams the readers wrote down differently); 55 glossary references whose English is not on the page they point to; three Skiri terms of the English index that fit two dictionary entries equally; six Blue Book-only entries with no printed form found | A person with the books | Small | 42, 70, 45, 41, 51, 28, 32, 35 |

Small things to do along the way, whenever the file concerned is open: retire
the older respelling function (46); the "word of the day" fixed at build
time (21); the style names `pitch-high` and `pitch-unmarked`, which no reader
sees but which still say "pitch" (9). Each worth a short session of its own:
the gold file of Parks's worked examples (58); the meanings and word classes
of the function-word tables, which nobody has checked (72); the English
prose of the lessons' notes, which is OCR text nobody has proofread (71).
The weak rule of person derivation stays in force: the owner's decision of
2026-11-14 (63).

### The first step of each of the top two

1. **The letters and the packet.** Read the three drafts in
   `community_review/letters/` (on this computer only; the folder is not in
   git). Each has a note at its head on where to send it, and square
   brackets for your name, who you are and how to reach you. The letter to
   the Press has one bracket more: what you have decided about the page
   scans in the public repository. The letters describe the site as it is
   since the push of the evening of 2026-11-15. The first letter also asks
   which spelling a learner should be told to write. Open
   `community_review/review_packet.pdf`,
   read it as the reviewer would, put your name and a way to reach you where
   the first page says `[name], [telephone or e-mail]`, build it again on
   the day it goes out (`python scripts/build_review_packet.py`), and send
   it with the first letter.
   [community_review/README.md](community_review/README.md) says what each
   part asks and where an answer takes effect.
2. **The published site.** Open it and go through "Start here" as a
   beginner would; then open lesson 9 (a dialogue, now with its English
   beside each line) and lesson 16 (the square brackets). The decisions are
   listed in the phase entries "The public site rebuilt around the learner"
   and "The lessons read from the page": say yes to each or change it.
   The five changes of 2026-11-15 are public too: open "Start here",
   lesson 1, "Phrases" and "Practice". Their decisions are in the phase
   entry "The five changes to the learner pages". Public since the evening
   of 2026-11-15 as well: "Learn with others", the marks SK and SB on the
   lessons, "Hear it at Indiana University", the word web, and the switch
   between the two spellings at the top of every page.

For the person with the books: the last section of
`reports/source_audit_2026-11/bluebook_applied_report.txt` (17 forms, with
what each reader saw), the section "left as they are" of
`print_completion_report.txt`, `extracted_data/grammatical_overview_tables.json`
(tables 6 and 7, both readings), `python scripts/bluebook_glossary.py
--list`, and the six places in the lessons of open item 70, with their
pages. Each line is one look at one page.

### What not to do next

- Do not show Week 20, publish the word-building guide, or give the ceremony-tagged entries their full detail before rank 1 has an answer.
- Do not copy a form, a sentence or a recording from any other source of the register (`sources/catalogue.json`) into the database or the site before its owner has said yes in writing. Until then a source is linked to, or used to check what the two books say. A source marked as ceremonial is not copied whatever the answer.
- Do not respell a textbook form into Skiri (an *i* for its *e*, an *h* for its *hr*). The textbook says how a Skidi speaker says those letters; it does not print the Skiri word, and a respelt form is a made form.
- Do not gather Indiana University's entry numbers or sound files in bulk to make the "Hear it" link exact. The link is a search; the exact link waits for their answer (item 81).
- Do not bring back a withdrawn engine from `archived/scripts/` to produce a form. The standing rule is that derived forms start from attested ones, and that a made form is labelled where it is shown and stored nowhere.
- Do not add a rule to an engine, or repair one, by looking at all the printed forms and then quoting the result on them. Split them first and open the second part once (`scripts/engines_review/person_forms_repair.py` is the pattern). For person derivation that second part is spent.
- Do not quote 87.2% (form 2) or "26 of 26" (person derivation on Appendix 1) as how good a tool is: both are on forms the rules were read from. The figure on unseen verbs is 97.3%, for one form only, the "he/she" question form.
- Do not extend person derivation to plurals, the negative or other modes until someone who knows the language has seen what it gives now.
- Do not store a form a script made in the database or in a file of copied forms. `python scripts/remove_engine_output.py --check` and `python scripts/sentence_templates.py --check` guard two places where that happened.
- Do not merge a Blue Book-only entry into the dictionary entry it stands beside, or change the frozen flashcard list, before rank 3 is decided. Learner progress is keyed to the entry ids.
- Do not spend more blind readings on the 17 Blue Book forms: three readings agree that the scan does not show what is there.
- Do not put the running text of the dictionary's chapters into the repository. The chapters are stored as forms, tables and summaries on purpose (open item 54).

---

## Source Materials

| File | Description | Location |
|------|-------------|----------|
| Parks Dictionary (PDF) | Full Skiri Pawnee dictionary by Douglas Parks. Split into: Abbreviations/Sound Key, Sounds/Alphabet, Major Sound Changes, Grammatical Overview, Organization, English-to-Skiri section, Skiri-to-English section, 3 Appendices (Appendix 1: 7 verb conjugation paradigms ~770 forms; Appendix 2: irregular du/pl verb roots ~9 entries; Appendix 3: kinship terminology ~40 forms) | `Dictionary Data/Dictionary PDF Split/` |
| Dictionary page PDFs | Individual pages split for AI processing | `Dictionary Data/split_pdf_pages_SKIRI_TO_ENGLISH/` and `split_pdf_pages_ENGLISH_TO_SKIRI/` |
| Blue Book — Pari Pakuru' | 1979 Pawnee Cultural Retention Committee textbook. 20 lessons teaching spoken Pawnee with dialogues, vocabulary, grammar explanations | `pari pakuru/Blue Book - Pari Pakuru.pdf` and `.txt` extraction |
| JSON Schemas | Defined structures for S2E and E2S parsed entries | `prompts/dictionary_parsing/` |
| Parks Ch. 3 OCR | OCR extraction of Major Sound Changes (24 rules with examples) | `Dictionary Data/Dictionary PDF Split/parks_sound_changes_ocr.txt` |
| Parks Ch. 4 OCR | OCR extraction of Grammatical Overview (23 pages: noun incorporation, verb classes, possession) | `Dictionary Data/Dictionary PDF Split/parks_grammatical_overview_ocr.txt` |

## Current Data State

| File | Entries | Status |
|------|---------|--------|
| `Dictionary Data/skiri_to_english_respelled.json` | 4,273 | **CURRENT** — normalized, OCR fixed, `simplified_pronunciation` + `normalized_form` populated. Since 2026-11-13: audit fixes applied and phonetic forms in Parks's own symbols; headword, phonetic form, respelling and learner spelling identical to the database for all 4,244 entries the two share (the other 29 are the duplicate rows the database dropped). Since 2026-11-14: `entry_metadata.page_number` is the page of the book, and every value `scripts/complete_from_print.py` set in the database is set here too |
| `Dictionary Data/english_to_skiri_linked.json` | 6,431 | **CURRENT** — rebuilt from the printed page on 2026-11-14 (`scripts/repair_english_index.py`): the English headword, each Skiri term with its preverb, phonetic form and class, the links to dictionary entries and the cross-references are what the page prints; `page_number` is the page of the book. The rest of a subentry (glosses, etymology, verb forms, examples) is still the first reading's copy and has not been compared field by field; the entry a subentry links to holds the verified text |
| `skiri_pawnee.db` | 4,337 | **CURRENT, and the working master copy** — the two files above plus 93 Blue Book-only entries, less 29 duplicate rows, plus everything later phases added. Not in git |

The earlier stages of the two JSON files (`*_complete`, `*_verified`,
`*_normalized`, `*_linked`, `*_fixed`, and their change logs) were removed from
the repository on 2026-11-13. They are in git history at commit `2e77095`
under `archived/dictionary_intermediates/`.

### Relationship Between S2E and E2S

- **S2E is the primary linguistic record** — full entries with headword, phonetic form, etymology, 5 paradigmatic verb forms, examples, derived stems, cognates
- **E2S is an index into S2E** — English words pointing to Skiri equivalents, with cross-references
- **E2S has more accurate phonetic forms** (IPA vowels: ə, ɪ, ʊ, accent marks) because its PDF parsing captured the IPA characters more faithfully
- **Linked by `entry_id`** (on S2E) and `s2e_entry_id` (on E2S subentries). Format: `SK-{slug}-p{page}-{index}`

### S2E Entry Structure
```json
{
  "entry_id": "SK-paatuq-p107-2038",
  "headword": "paatuʔ",
  "normalized_form": "pâtu'",
  "entry_metadata": { "page_number": 107, "column": "left", ... },
  "part_I": {
    "stem_preverb": null,
    "phonetic_form": "[paá-tʊʔ]",
    "simplified_pronunciation": "PAH-too'",
    "grammatical_info": { "grammatical_class": "N", "verb_class": null, "additional_forms": [] },
    "glosses": [{ "number": 1, "definition": "blood; gore.", "usage_notes": null }],
    "etymology": { "raw_etymology": "<paat+uʔ, blood + NOM>", "constituent_elements": [...], "literal_translation": "..." },
    "cognates": [{ "language": "Ar.", "form": "..." }]
  },
  "part_II": {
    "paradigmatic_forms": { "form_1": "...", "form_2": "...", "form_3": "...", "form_4": "...", "form_5": "..." },
    "examples": [{ "skiri_text": "...", "english_translation": "...", "usage_context": null }]
  },
  "compound_structure": null,
  "derived_stems": []
}
```

### E2S Entry Structure
```json
{
  "english_entry_word": "blood",
  "entry_metadata": { "page_number": 1, ... },
  "subentries": [{
    "subentry_number": 1,
    "s2e_entry_id": "SK-paatuq-p107-2038",
    "s2e_match_type": "exact_unique",
    "part_I": {
      "skiri_term": "paatuʔ",
      "phonetic_form": "[paá-tʊʔ]",
      "grammatical_classification": { "class_abbr": "N", "verb_class": null },
      "english_glosses": [{ "number": 1, "definition": "blood; gore." }],
      "etymology": { ... }
    },
    "part_II": { "paradigmatic_forms": [{ "form_number": 1, "skiri_form": "..." }], "examples": [...] },
    "part_III": { "cross_references": [{ "english_term": "...", "skiri_equivalents": ["..."] }] }
  }]
}
```

### Phonetic Notation System (Parks Dictionary)

Stored exactly as Parks prints it since 2026-11-13. Before that the database
used a working notation: a hyphen for the syllable dot, a bullet for the edge
dash, à for ə́ and í for ɪ́. Reports and frozen files older than that date
still show it.

- `·` (U+00B7) — syllable boundary
- `–` (U+2013) — at the edge of a bound form: something must come before or after
- Consonants: p, t, k, c/č, s, w, r, h, ʔ (glottal stop)
- Long vowels: aa, ii, uu
- Short vowels: ə, ɪ, ʊ (lax, the usual quality); a single i or u is a short vowel with tense quality
- Accent: an acute on the accented syllable: ə́ ɪ́ ʊ́ on a short vowel, on the second half of a long one (aá, ií, uú). A grave occurs in ten entries and is not explained
- `{k/t}` — the final consonant alternates; `(r)` — an optional sound
- Example: `[–rə·hʊh·kaa·paa·kɪs–]`

The PDF's text layer encodes these with stand-in characters that depend on
the font. The verified table is `scripts/source_audit/chartable.py`.
`scripts/ipa_notation.py` converts the stored notation to the old working one
for the respelling code, and nowhere else.

### Sound Key (PDF 01 p. xvii)
```
CONSONANTS: p (spot), t (stop), k (skate), c (patch/cents), s (sit),
            w (wall), r (Spanish tapped pero), h (hit), ʔ (uh-uh)
VOWELS:     a/ah (putt), aa (father), i/ih (pit), ii (weed),
            u (boot), uu (rude)
```

### Grammatical Classes
```
N (noun), N-DEP (dependent noun), N-KIN (kinship term)
VI (intransitive verb), VT (transitive verb), VD (descriptive verb)
VL (locative verb), VP (patientive/passive verb), VR (reflexive verb)
ADJ, ADV, NUM, PRON, DEM, QUAN, CONJ, INTERJ, LOC, COLL
Verb classes: (1), (1-a), (1-i), (2), (2-i), (3), (4), (4-i), (u), (wi)
```

### Paradigmatic Forms Key (5 standard verb forms)
```
1. First Person Singular Subject, Indicative Mode, Perfective
2. Third Person Singular Subject, Indicative Mode, Perfective
3. Third Person Singular Subject, Indicative Mode, Imperfective
4. Third Person Singular Subject, Absolutive Mode, Subordinate Perfective
5. Third Person Singular Subject, Indicative Mode, Perfective Intentive
```

That key is the project's wording of March 2026. Parks's own definition
(chapter 5, pp. 56-57, read on 2026-11-14) differs in three points: form 1 is
a first person *patient* for passive verbs; form 4 is the gerundial mode
(that is, the subordinate absolutive), "usually" perfective; form 5 is the
intentive aspect. He adds that certain verb classes do not allow some of the
forms. The sentence is quoted in `extracted_data/organization_of_the_dictionary.json`.

---

## Phase log: 1.1 (cleaning the parsed dictionary)

### ✅ Phase 1.1a — OCR Normalization
**Script:** `scripts/normalize_phonetic.py`
**What it does:** Recursively walks every string in every entry across both S2E and E2S, fixing OCR/encoding corruptions from PDF parsing. Logs every replacement per-entry.

**Character corrections applied:**
| Corrupted | Corrected | Description |
|-----------|-----------|-------------|
| ™ (U+2122) | ʔ (U+0294) | IPA glottal stop |
| ® (U+00AE) | ʔ (U+0294) | Parks glottal stop → IPA |
| ? (phonetic only) | ʔ (U+0294) | OCR misread |
| Ù (U+00D9) | č (U+010D) | c-hacek |
| ‡ (U+2021) | í (U+00ED) | i-acute |
| Ñ (U+00D1) | á (U+00E1) | a-acute |
| ‰ (U+2030) | ʊ (U+028A) | IPA near-close back rounded |
| † (U+2020) | ɪ (U+026A) | IPA near-close near-front |
| æ (U+00E6) | í (U+00ED) | i-acute |
| ß (U+00DF) | ə (U+0259) | IPA schwa |
| Š (U+0160) | ʊ (U+028A) | IPA near-close back rounded |

Also strips whitespace from `phonetic_form` fields. Preserves `•` syllable dots.

**Correction (2026-11-13).** The "corrupted" characters are not OCR errors. The
PDF's text layer does not contain Parks's IPA letters; its font has them at the
positions of other characters, so the text layer is full of stand-ins. The table
above, and the six additions listed under Phase 1.1c, were worked out without
looking at the page, and six rows were wrong. Read against page images:

| Stand-in | Was decoded as | The page prints | Entries |
|---|---|---|---|
| `÷` | ː (a length mark) | **ú**, as in *huú* | 141 |
| `Š` | ʊ | **ʊ́** (accented) | 125 |
| `ˆ`, `ç` | ɪ, ʔ | **ì** | 3 |
| `ø` | ː | **ù** | 1 |
| `Ò` | a | **à** | 1 |
| `à` (itself) | à | **ə́** | 545, not yet changed |
| `‡` | í | what looks like **ɪ́** | 371, not yet changed |

Parks prints no length mark anywhere: long vowels are doubled. The first five
rows had removed the accent from 269 entries, and in two of them a vowel from
the respelling as well. `scripts/fix_data_2026_11.py` restored them from the
text layer, position by position (report:
`reports/fix_data_2026-11-13_report.txt`). The last two rows keep the accent but
not Parks's symbol; they are open item 6. The 2026-09-01 cross-check against the
text layer could not see any of this, because it decoded the text layer with the
same table.

**Results:** 50,699 character replacements across 8,820 entries. Zero corruptions remaining.

### ✅ Phase 1.1b — Dictionary Linking + Phonetic Sync
**Script:** `scripts/link_dictionaries.py`
**What it does:**
1. Assigns unique `entry_id` to every S2E entry
2. Matches E2S subentries to S2E via headword with gloss disambiguation for homonyms
3. Writes `s2e_entry_id` + `s2e_match_type` into E2S subentries
4. Updates S2E phonetic forms with E2S's more accurate IPA transcriptions

**Matching results:**
- 5,132 E2S subentries linked (4,726 exact, 398 gloss-disambiguated, 8 fallback)
- 2,579 cross-reference-only (no data to link)
- 362 unmatched (mostly parsing artifacts like "(see cross-reference)")
- 3,925 S2E phonetic forms updated with IPA

### ✅ Phase 1.1c — Pronunciation Respelling + Orthographic Normalization
**Scripts:** `scripts/respell_and_normalize.py`, `scripts/fix_priority_issues.py`
**What it does:**
1. Generates `simplified_pronunciation` field: IPA `phonetic_form` → learner-friendly English respelling
2. Generates `normalized_form` field: headword → learner orthography with circumflex long vowels, č, '

**Vowel mapping (source: Parks Sound Key p. xvii + Blue Book pp. xvii–xxi):**

| Pawnee | English Comparison | Respelling |
|--------|-------------------|------------|
| `a` (short) | "putt" / "above" | `uh` |
| `aa` (long) | "father" | `ah` |
| `i` (short) | "pit" | `ih` |
| `ii` (long) | "weed" / "machine" | `ee` |
| `u` (short) | "push" | `oo` |
| `uu` (long) | "rude" | `oo` |
| `ɪ`, `ʊ`, `ə` | IPA reduced vowels | `ih`, `oo`, `uh` |

**Consonant mapping:** `r` → `d` (BB: "a very soft d"), `c` → `ts`, `č` → `ch`, `ʔ` → `'`, all others pass through.

**Normalization rules (Skiri words only):** `aa` → `â`, `ii` → `î`, `uu` → `û`, `c` → `č` (when phonetic form confirms /tʃ/), `ʔ` → `'`.

**Edge cases handled:** comma-separated variants, preverb notation `(ʊt...)`, optional sounds `(h)`/`(r)`, IPA length mark `ː`, null morpheme `Ø`, prefix notation `[+raar-]`, alternation markers `{k/t}`.

**Results:**
- 4,272/4,273 entries with `simplified_pronunciation` (1 entry has no phonetic form)
- 4,273/4,273 entries with `normalized_form`
- 53 `c`/`č` disambiguation mismatches flagged for review (count mismatch between headword and phonetic)

**Also applied (`fix_priority_issues.py`):** 6 additional OCR corrections missed by Phase 1.1a (`÷`→`ː`, `ˆ`→`ɪ`, `‹`→`ʊ`, `Ò`→`a`, `ç`→`ʔ`, `ø`→`ː`), plus ~111 non-IPA phonetic form stubs nulled (`[cross-referenceonly]`, `NOT_PROVIDED`, `N/A`, `Seeentryfor'...'`, `[notprovided]`).

### ✅ Phase 1.1d — Parsing Completeness Audit
**Scripts:** `scripts/audit_entries.py`; `generate_review_list.py` and `verify_glottal_from_phonetic.py` (now in `archived/scripts/`)
**What it does:** Validates every S2E entry (and optionally E2S) for data quality. Local rule-based checks + optional Gemini AI batch validation.

**Local checks performed:**
- Field presence: headword, phonetic_form, grammatical_class, glosses
- Phonetic character validation: flag non-IPA characters post-normalization
- Noun glottal stop check: nouns ending in vowel without `ʔ`, triaged by N/N-KIN/N-DEP/proper noun
- Consonant skeleton consistency: headword ↔ phonetic_form, with c↔ts normalization, optional sound inclusion, alternation marker resolution, glottal absorption handling
- Verb class presence (suppressed for VD descriptive verbs — by design in Parks)
- Multi-class grammatical entries validated per-component (e.g., `VT, VR`)

**Gemini AI validation:** Batch validation (20 entries/batch) with checkpointing for resume. System prompt is Pawnee-linguistics-aware (knows Parks notation, c↔ts equivalence, noun suffix patterns).

**Noun glottal stop resolution:** Cross-referenced phonetic_form endings against headword endings for 260 common noun candidates. Result: 0 OCR misses, 257 confirmed correct (phonetic form also lacks final ʔ), 3 unverifiable (no phonetic form). The headwords are correct as-is.

**Final audit numbers (post all fixes):**
- 640 total flags (down from 2,005 initial)
- 81 by-design (proper noun/kinship glottal, VD verb class)
- 12 skeleton mismatches remaining (headword notation edge cases: prefix markers, null preverbs)
- 260 noun glottal candidates: all verified correct via phonetic cross-reference
- 2 residual INVALID_PHONETIC_CHAR (minor stragglers)

---

## Phase log: 1.2 onward

### Priority Roadmap *(added 2026-03-15; statuses brought up to date 2026-11-13)*

High-impact items ordered by learner value, not technical dependency:

| Priority | Phase | What | Why |
|----------|-------|------|-----|
| ✅ ~~1~~ | 3.1.5 | ~~Noun possession morphology~~ | **DONE (2026-03-18)** — 4 possession systems + locative suffixes + web widget + example filter. 40/40 tests. |
| 🟡 2 | 3.1 (stem extraction) | Dictionary-wide stem extraction | **PAUSED at 86.7%** (re-measured 2026-11-12: 1,908 of 2,201) — third pass: 83.5% → **86.6%** (1,914/2,211), 88.4% w/ close. Up from 14.8% → 62.0% → 83.5% → 86.6%. |
| ✅ ~~3~~ | 4.3 | ~~Confidence scoring on computed forms~~ | **DONE (2026-03-19)** — 4-factor weighted scoring (0.0-1.0), DB column, web badges, dashboard widget. 88.7% avg, 2,202 high / 30 med / 22 low. |
| 🟡 4 | 3.1 (accent) | Accent mark generation | **PAUSED** — 78/85 (91.8%) accented forms correct. 4 rules: Agent-boundary í, Mode-prefix í/rí, Infinitive kú, Dual sí. Appendix 1: 76.2% → **86.4%**. 7 remaining failures are verb-specific stem accents. |
| ✅ ~~5~~ | 4.4 | ~~Community feedback mechanism~~ | **DONE (2026-03-19)** — Flag/confirm buttons, admin review queue, writable DB, dashboard widget. Design Principle #6 enforced. |
| 🟡 6 | 5.2 (exports) | Printable PDFs + Anki export | **Anki DONE (2026-03-20)** but unused. **Printable flashcard sheets DONE (2026-11-10)**, `curriculum/flashcard_pdfs/`. Printable word lists and paradigm tables remaining. |
| ✅ ~~7~~ | Ongoing | ~~Blue Book 518-gap triage~~ | **DONE (2026-03-19)** — 516 gaps classified: 38% phrases, 27% inflected verbs, 18% unlisted nouns, 8% descriptors, 3% possessed, 2% function words, 2% loanwords, 2% OCR artifacts. 65% are morphological (roots exist in Parks). 115 high-value items flagged for DB addition. |
| ✅ ~~8~~ | 3.1.6 | ~~Function word inventory~~ | **CLASSIFIED (2026-03-20)** — 418 function words with `position_rule` + `refined_subclass`. 149 PROCLITIC, 135 PRECEDES-VERB, 51 PRECEDES-NOUN, 44 CLAUSE-INITIAL, 28 STANDALONE, 11 BETWEEN-CLAUSES. Demonstratives + interrogatives mapped. |
| ✅ ~~9~~ | 3.2a | ~~Template-based sentence assembly~~ | **DONE (2026-03-20)** — 10 templates, `/sentence-builder`. Person and mode derivation added 2026-09-01 (3.2b). |
| ✅ ~~10~~ | 5.1 | ~~Structured lesson content~~ | **DONE (2026-09-01)** — all 20 Blue Book lessons in the app and on the static site. |

### 🟡 Phase 3.1 — Dictionary-Wide Stem Extraction *(paused after the third pass)*

**Re-measured 2026-11-12:** 1,908 of 2,201 exact (86.7%), 40 close, 253 missed. The word-construction analysis (Phase 6.2) uses this predictor as one of its evidence channels and treats a miss as "no confirmation", never as a contradiction.

**Status (2026-03-19):** Third pass complete — **83.5% → 86.6% exact** (1,914/2,211 verbs), 88.4% with close matches. Up from 14.8% → 62.0% → 83.5% → 86.6%.

**Script:** `scripts/stem_extractor.py`
**Reference files:** `parks_sound_changes_ocr.txt` (OCR of Parks Ch. 3), `parks_grammatical_overview_ocr.txt` (OCR of Parks Ch. 4), both in `Dictionary Data/Dictionary PDF Split/`

This is the wall between "a conjugation engine that works on 7 test verbs" (76.2% on Appendix 1) and "a tool that can inflect any verb a learner looks up." The first pass proved the approach works — headword IS the stem, and form_2 is predictable from `headword + verb_class + stem_preverb` with systematic sound change rules.

**What `stem_extractor.py` does (current pipeline):**
1. Parse `stem_preverb` field → preverb morphemes (ut, uur, ir, ir+ut, etc.)
2. Infer verb class for untagged entries (VD→(u), VL→(wi), VP→(4))
3. Build prefix+stem with preverb junction rules (ut+r→tuuh, ut+h→tut, uur+C→tuuh+C, etc.)
4. Apply vowel coalescence at prefix+stem boundary (Parks Rules 5-7)
5. Apply internal sound changes (Rule 8R: r→t after obstruent, Rule 12R: r→h before C)
6. Apply perfective finals (k→t, hk→t, r→Ø, h→Ø, V→Vʔ, kus→ku)
7. Special class rules: (3) -aʔuk→-uʔ contraction, (wi) no final ʔ
8. Compare predicted form_2 to attested paradigmatic_form in DB

**Accuracy by category (third pass — 2026-03-19):**

| Category | Total | Exact | Rate | Notes |
|---|---|---|---|---|
| (4)\|(uur...) | 28 | 28 | 100.0% | Ceiling! |
| (3)\|(uur...) | 16 | 16 | 100.0% | Ceiling! |
| (3)\|(ut...) | 9 | 9 | 100.0% | Ceiling! |
| (3)\|(ir...ut...) | 13 | 13 | 100.0% | 3rd pass: ir+ut junction fix |
| (wi)\|(ir...ut...) | 10 | 10 | 100.0% | 3rd pass: ir+ut junction fix |
| (wi)\|(ir...) | 7 | 7 | 100.0% | 3rd pass: a+i coalescence |
| (2-i)\|(uur...) | 6 | 6 | 100.0% | — |
| (2)\|(ut...) | 5 | 5 | 100.0% | — |
| (2-i)\|none | 44 | 43 | 97.7% | Near-ceiling |
| (1-a)\|(uur...) | 32 | 31 | 96.9% | — |
| (1-i)\|none | 54 | 52 | 96.3% | — |
| (1)\|(uur...) | 47 | 45 | 95.7% | — |
| (1)\|(ut...) | 101 | 92 | 91.1% | — |
| (3)\|none | 120 | 109 | 90.8% | — |
| (wi)\|none | 80 | 72 | 90.0% | — |
| (1)\|none | 434 | 388 | 89.4% | 3rd pass: -wiir/-uuh shortening |
| (4)\|(ut...) | 81 | 71 | 87.7% | — |
| (3)\|(ir...) | 94 | 82 | 87.2% | 3rd pass: a+u coalescence, aaʔa fix |
| (4)\|none | 414 | 355 | 85.7% | — |
| (wi)\|(ut...) | 27 | 23 | 85.2% | — |
| (u)\|none | 385 | 320 | 83.1% | 3rd pass: VD echo fixes, -wii shortening |
| (u)\|(ir...) | 12 | 10 | 83.3% | — |
| (2)\|none | 42 | 33 | 78.6% | — |
| (u)\|(ut...) | 24 | 18 | 75.0% | 3rd pass: VD echo -Vht fix |

**Remaining gaps (257 miss, 40 close):**

| Pattern | Current | Remaining issue | Count |
|---|---|---|---|
| (4)\|none | 85.7% | Multi-word headwords; `ruuti-`/`si-` prefix entries; internal shortening | 50 miss |
| (u)\|none VD | 83.1% | Internal long-vowel shortening (aah→ah); prothetic vowel; prefix mismatches | 49 miss |
| (1)\|none | 89.4% | `ruuti-`/`si-` prefix entries; `aw-` absorption; internal vowel changes | 43 miss |
| (3)\|(ir...) | 87.2% | Remaining class 3 stem allomorphy; prefix mismatches | 12 miss |
| (3)\|none | 90.8% | Internal contraction edge cases | 11 miss |
| Other categories | — | `si-` prefix (16 total), `ruuti-` prefix (19 total), bracket notation (~10) | ~45 miss |

**Key data sources:**
- `lexical_entries.verb_class` — populated for 1,698/2,254 verbs (75%); 556 missing are VD (438) + VL (115)
- `lexical_entries.stem_preverb` — populated for 652 verbs (29%); top patterns: `(ut...)` 294, `(uur...)` 164, `(ir...)` 129
- `paradigmatic_forms.form_2` — ground truth for validation; available for 2,246/2,254 verbs (99.6%)
- `etymology.constituent_elements` — morpheme decomposition for 1,772 verbs (79%); key for noun incorporation stripping
- `parks_sound_changes_ocr.txt` — OCR of Parks Ch. 3 (all 24 rules with examples and exceptions)
- `parks_grammatical_overview_ocr.txt` — OCR of Parks Ch. 4 (23 pages: noun incorporation, compound formation, verb classes)

### ✅ Phase 1.2 — Database Schema
**Script:** `DB/import_to_sqlite.py`
**What it does:** SQLite database (`skiri_pawnee.db`) unifying S2E and E2S data.

**Tables:** `lexical_entries` (4,337 entries on 2026-11-13: 4,273 imported from Parks, + 93 Blue Book-only words, − 23 duplicate rows in March, − 6 more in November), `glosses`, `paradigmatic_forms`, `examples`, `etymology`, `cognates`, `derived_stems`, `english_index`, `cross_references`, `semantic_tags`, `blue_book_attestations`, `import_metadata`, `bb_gap_triage`, `community_feedback`, `function_words` (418), `bb_function_words` (63) + FTS tables for glosses, examples, english_index. Which script created each table, and the row counts, are in `DB/README.md`.

**The database cannot be rebuilt by one command.** The importer creates only the core tables; more than twenty later scripts changed the database in place, some with AI answers that were saved nowhere else. Restore a backup instead (`OneDrive/pari_pakuru_backups/`, `~/.pari_pakuru_backups/`).

### ✅ Phase 2.1 — Semantic Category Tagging
**Script:** `scripts/tag_entries.py`
**What it does:** Auto-tags entries by domain using rule-based keyword matching + Gemini AI for ambiguous cases. 7,097 tags were stored at first. An AI audit on 2026-03-15 (`archived/scripts/audit_semantic_tags.py`, report `reports/audit_semantic_tags.txt`) removed 1,248 false matches caused by English words with several meanings, and 36 wrong kinship tags were removed on 2026-03-21. On 2026-11-13 the table holds **4,500 tags: 19 topics on 3,316 entries**. (The rest of the drop from 7,097 is not documented.)

### ✅ Phase 2.2 — Blue Book Cross-Verification
**Script:** `scripts/blue_book_verify.py`
**What it does:**
1. Parses Blue Book text (`pari pakuru/Blue_Book_Pari_Pakuru.txt`) into 20 lesson chunks
2. Sends each chunk to Gemini API (`gemini-2.5-flash`) to extract structured vocabulary
3. Normalizes BB practical orthography → Parks linguistic orthography (ts→c, '→ʔ, etc.)
4. Matches against dictionary via 3-tier: exact normalized → loose (no glottal/affricate) → prefix
5. Writes results to `blue_book_attestations` table in SQLite
6. Adds BB dialogue sentences as new `examples`
7. Adds `blue_book_attested` column to `lexical_entries`
8. Generates report at `reports/phase_2_2_blue_book.txt`

**Results (final, after follow-up improvements):**
- 984 BB vocabulary items extracted (all 20 lessons, Lesson 20 split into 4 page-chunks)
- 53 exact, 5 loose, 404 prefix, 4 verb-stem matches; 518 gaps
- 88 new dialogue examples added to `examples` table
- 83 dictionary entries attested (`blue_book_attested = 1`)
- Gaps include: multi-word phrases, verb constructions, function words, loanwords (expected)
- Normalization confirmed working: BB `ts`→Parks `c`, BB `'`→Parks `ʔ`

**Extraction output:** `extracted_data/blue_book_extracted.json` (984 items). The extraction checkpoint is in git history only.

**State on 2026-11-13:** `blue_book_attestations` has 1,026 rows, 581 of them linked to a dictionary entry; 181 entries are marked `blue_book_attested`. The `prefix` match type (404 rows) is unreliable and is not used as evidence by the word-construction analysis.

**Script features:**
- `--rerun-failed`: clears empty checkpoint entries so failed lessons get re-extracted
- `--clear-db`: wipes attestations table for clean re-import
- `--match-only`: re-run matching stage only (no Gemini calls)
- `--extract-only`: run Gemini extraction only (no DB import)
- Large lessons (>6 pages) auto-split into page chunks (fixes Lesson 20 / epilogue)
- 4-tier matching: exact normalized → loose → prefix → verb stem strip

**Lesson 20 breakdown (pages 111–130, epilogue + glossary):**
- Split into 4 chunks: p111-116 (35 entries), p117-122 (18 entries), p123-130 (0 — glossary only)
- 58 total items, 33 matched (57%)

**Follow-up: Pronunciation comparison (`archived/scripts/bb_pronunciation_compare.py`):**
- Extracts BB parenthetical pronunciation guides from raw text (12 found in lesson pages 29+)
- OCR normalization: consonant+'d' → consonant+'a' (stress-dotted vowel artifact)
- 3-pass parser: inline `word (pron) gloss`, column-block (table format), preceding-line
- Long-vowel-folded matching + gloss-based fallback via `english_index`
- Comma-separated headword variant indexing (e.g., `rawa, nawa` indexed as both `rawa` and `nawa`)
- Compares BB guides against verified IPA `phonetic_form` (not `simplified_pronunciation`)
- Normalization for comparison: IPA reduced vowels (ɪ→i, ʊ→u, ə→a), accent marks stripped, BB ts→c, BB '→ʔ
- 7 of 12 guides matched to Parks dictionary entries
- Results: 4 exact matches, 3 exact after long-vowel folding, 0 different
- Key finding: BB pronunciation guides map directly to IPA phonetic forms after normalization; the only systematic difference is BB shortening long vowels (BB `hi` = IPA `hii`, BB `ra` = IPA `raa`, BB `ki` = IPA `kii`)
- 5 unmatched guides are verb constructions / multi-word forms without standalone dictionary entries
- Report: `reports/phase_2_2_pronunciation_phonetic.txt`

### ✅ Phase 2.3 — Sound Change Rule Engine
**Script:** `scripts/sound_changes.py`
**What it does:**
1. Catalogs all 24 phonological rules from Parks Ch. 3 (Major Sound Changes)
2. Implements each rule as a Python function (9 restricted + 15 unrestricted)
3. Provides ordered pipeline: morpheme list → surface form
4. Stores rules in `sound_change_rules` DB table
5. Validates against 2,241 paradigmatic form pairs
6. Generates report at `reports/phase_2_3_sound_changes.txt`

**Rule categories (24 total):**
- Vowels Restricted (4): Dominant i (1R), Dominant a (2R), -his reduction (3R), Vocalic reduplication (4R)
- Vowels Unrestricted (3): Same-vowel contraction (5), u-domination (6), i+a contraction (7)
- Consonants Restricted (5): raar- assibilation (8R), final-s loss (9R), prefixal r-loss (10R), ut- affrication (11R), prefixal r-laryngealization (12R)
- Consonants Unrestricted (12): t-laryngealization (13), metathesis (14), sonorant reduction (15), h-loss (16), sibilant hardening (17), sibilant loss (18), alveolar dissimilation (19), degemination (20), r-stopping (21), labial glide loss (22), final r loss (23), c-variants (24)

**Pipeline ordering:**
1. Restricted rules (morpheme-aware): 1R → 2R → 3R → 8R → 10R → 11R → 12R
2. Concatenate morphemes
3. Unrestricted rules (string-level): 5 → 6 → 7 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23
4. Optional: Rule 9R final-s loss (word-level)

**Test results:** 11/11 built-in tests passing (PDF examples)

**Validation results:**
- 82.1% of form_4 entries start with `irii-` prefix (expected)
- 17.2% start with `irir-` (variant for certain verb classes)
- Simple prefix-swap derivation shows 12% close-match rate (edit dist ≤ 2)
- Full derivation requires morpheme decomposition (Phase 3.1 dependency)
- Rule 13 (t→h before r): 689 entries show evidence
- Rule 20 (degemination): all 9 raar-preverb forms confirmed surface without rr
- 268 headwords end in underlying r (notation convention; surface final-r loss confirmed)

**Key finding:** Sound change rules are correctly formalized and tested; the gap for full paradigmatic form derivation is morphological decomposition (prefix/preverb/suffix inventory), which is Phase 3.1's responsibility.

**Gemini audit results (52 entries across 15 verb classes):**
- 14 of 24 rules observed in paradigmatic forms (most frequent: Rule 6 u-domination, Rule 23 final-r loss, Rule 7 i+a contraction)
- 48/52 entries flagged anomalies — mostly expected: they are **unlisted suffixation/perfective patterns** (not sound change rule errors)
- Unlisted patterns identified (important for Phase 3.1):
  - Perfective suffix `-his` lost after stem-final `t` (not just after `k` as in Rule 3R)
  - Stem-final `k → t` in perfective for Class 2-i and some Class 4 verbs
  - Subordinate perfective suffix `-u` for consonant-final stems, `-wi` for `aa`-final stems
  - Glottal stop `ʔ` blocks vowel contraction rules
  - `irii- + ra-` = `iriira-` (r+r NOT degeminated — Rule 20 scope limited to within-morpheme)
- These are **morphological suffixation rules**, not phonological sound changes — correctly out of scope for Ch. 3 rules
- All 24 implemented rules confirmed correct where they apply

**Script features:**
- `--test`: run built-in test suite (PDF examples)
- `--apply "ti + uur + hiir"`: apply pipeline to morpheme sequence
- `--catalog-only`: populate DB table only
- `--validate-only`: run validation without DB writes
- `--final-s-loss`: apply Rule 9R with --apply mode
- `--audit`: Gemini-powered audit against paradigmatic forms (requires GEMINI_API_KEY)

### 🟡 Phase 3.1 — Morpheme Inventory & Slot System
**Scripts:** `scripts/extract_appendices.py`, `scripts/morpheme_inventory.py`
**What it does:**
1. Extracts conjugation paradigms from scanned PDF appendices via Gemini OCR (PyMuPDF→PNG→Gemini)
2. Defines the complete 30-slot verb template (8 proclitic + 18 inner prefix + 4 suffix slots)
3. Maps 164 morpheme abbreviations to their forms and slot positions
4. Implements conjugation engine: (stem, class, person, number, mode, aspect) → inflected form
5. Validates against 770 Appendix 1 paradigm forms

**Extraction results:**
- Appendix 1: 770 forms (7 verbs × 10 modes × 11 person/number) — 100% extracted
- Appendix 2: 9 irregular verb roots (suppletive sg/du/pl stems)
- Abbreviations: 164 entries with morpheme forms
- Grammatical Overview: 23/23 pages extracted (pages 1,3,7,16 recovered via plain-text Gemini at 400 DPI)

**Extraction audit findings:**
- Appendix 1: all 770 forms present, no nulls/errors; verb_class metadata missing on all 7 pages; 2/7 headings null/empty
- Abbreviations: 81/164 have null morpheme_form (expected for non-morpheme abbrevs like "an.", "Ar."); key person prefixes present
- Grammar pages 1,3,7,16: originally failed due to Gemini empty responses on structured JSON; recovered using plain-text prompts at 400 DPI (page 3 required split-page extraction for Table 5)
- Recovered tables: Table 5 (Derivational Affixes), Table 9 (Pronominal Prefixes), Table 15 (Verb Stem Template), Table 16 (Verb Suffix Template)

**Verb template (Parks Tables 6-7):**
- Proclitics: QUOT wi-, DUB kuur-/kuruur-, INFR tiir-, EV ar-, DU si-, INDF ku-, REFL witii-, NEG kara-/ka-/kaaku-
- Inner prefixes (slots 10-26): MODE → AGENT → INCLUSIVE → PL/POSS/PREV → PATIENT → INF.B → PHY.POSS → BEN/PREV → SEQ → AOR → ADV → PL → PL → PL → NOUN → STEM
- Suffixes: ASPECT → SUBORDINATION → INTENTIVE → SUB.INTENTIVE

**Conjugation engine:**
- Assembles morphemes by slot, concatenates, applies unrestricted phonological rules
- Rule 2R (dominant a) applied at mode+preverb boundary via _smart_concatenate
- Preverb alternation: ir- → iir- (1/2.A) / a- (3.A)
- For verbs with ut- preverb: fused into stem (e.g., ut-+aar→ stem "uutaar")

**Validation results (latest — 2026-03-12):**
- 770 forms tested: 587 exact (76.2%), 153 close (19.9%), 30 mismatch (3.9%)
- Per verb: to go 94%, to drink it 89%, to be sick 88%, to have it 85%, to be good 79%, to do it 67%, to come 31%
- "to come" improved from 21→34 exact (70 close = accent-only); 6 remaining MISS are assertive/absolutive 3du stem, gerundial 2sg, 3pl sub suffix
- Remaining gaps: "to do it" (12 MISS), "to be good" (3 MISS), "to be sick" (4 MISS), "to drink it" (3 MISS)

**Known gaps for refinement:**
- "to come" (34/110): 70 close matches are accent-only; 6 remaining MISS: assertive/absolutive 3du uses sg stem instead of du stem, gerundial 2sg GER shortening fires incorrectly, 3pl sub suffix contraction deletes stem
- "to do it" (74/110): 12 MISS — needs investigation (largest remaining gap after "to come")
- "to be sick" remaining 4 mismatches: gerundial du/infinitive structural anomalies (likely OCR artifacts)
- "to be good" remaining 3 mismatches: minor plural/dual edge cases
- Accent mark generation: ~85 forms have accents (mostly "to come"), implementing stress assignment would boost 70+ close→exact (~9%)
- Dictionary-wide stem extraction: main bottleneck for dict validation (14.8% exact)

**DB tables added:** `verb_paradigms`, `irregular_verb_roots`, `morpheme_abbreviations`, `morpheme_inventory`, `verb_template_slots`
**Report:** `reports/phase_3_1_morphemes.txt`

Tasks completed:
- [x] Extract Appendix 1 verb conjugation paradigms via Gemini OCR
- [x] Extract Appendix 2 irregular verb root tables
- [x] Map all 164 morpheme abbreviations to their forms and slot positions
- [x] Define slot ordering: proclitics → mode → person → preverb → stem → aspect → subordinating
- [x] Encode verb class rules: how each class modifies dependent forms
- [x] Build conjugation engine: (stem, class, person, number, mode, aspect) → inflected form
- [x] Validate against Appendix 1 paradigms (first pass: 12.7% exact, singular ~33%)
- [x] Gemini-powered dual/plural morpheme analysis (all 7 verbs → `extracted_data/dual_plural_analysis.json`)
- [x] Suppletive stem system: SUPPLETIVE_STEMS dict with du/pl stem lookup per verb
- [x] Fix si- proclitic (1du_incl excluded), 1pl_incl agent=t, r→h before consonants
- [x] Descriptive verb 3pl suffix (-waa), Class 3 si- for plural, pl_absorbs_raak flag
- [x] Partial descriptive verb person marking (ku- proclitic, h- 3PM)
- [x] Second pass validation: 20.9% exact (161/770), 31.7% close
- [x] Descriptive verb sub-classification: ku-proclitic (class u/wi without preverb) vs uur-preverb (standard agent prefixes)
- [x] Gerundial decomposition: irii(GER) + ra(MODE) replaces monolithic iriira
- [x] Potential mode: kuus-/kaas- with 2sg agent suppression, shortening before POT.i+V
- [x] Assertive mode Rule 2R: rii + a → raa
- [x] "to go" agent+stem fusions: t+war→tpa, s+war→spa via du_agent_fusions dict
- [x] ku- slot ordering: moved from proclitic slot 6 to inner slot 12.5 (after MODE)
- [x] Class 3 1pl_incl: acir- (not a-) for inclusive, agent t- suppressed
- [x] Imperfective aspect: -huʔ (non-subordinate) / -hu (subordinate) suffix
- [x] Dictionary-wide validation: --validate-dict mode (9,583 forms across all dictionary verbs)
- [x] Appendix 3 extraction: 23 kinship terms (consanguineal + affinal + possessive paradigms)
- [x] Gemini-collaborative morphophonological analysis: 3-round diagnosis → 10 rule fixes (35%→51%)
- [x] "to go" suppletive 3pl: pl3_stem with PREV_3A label for correct vowel contraction
- [x] "to drink it" pl_agent_fusions, sub_stem shortening, 3pl raak prefix
- [x] Potential mode shortening conditioned on agent presence
- [x] Sound change VOWELS sets updated to include accented vowels (áíú)
- [x] Descriptive-ku verb overhaul: 4-way person category system (excl/2nd/3rd/incl), DESC_KU_MODE_OVERRIDES table, raktah plural, 3pl prefix markers, ku→kuu lengthening, gerundial mode decomposition, potential mode reordering, aca→acu u-raising — "to be sick" 34%→88%
- [x] "to come" negative mode: kaakaa underlying form with extended shortening rules (+2)
- [x] "to come" 3.A stem ʔaʔ/ʔa: initial glottal surfaces in non-indicative/non-negative modes
- [x] Subjunctive aa shortening: only before u-initial morphemes (not i/r) — "to have it" +6
- [x] "to come" gerundial: ir-preverb sg 1sg/2sg skip MODE ra; 1sg also skips AGENT; GER shortening label-gated
- [x] "to come" potential mode: preverb irii (1/2) / aa (3rd+1pl_incl); no POT.i; TR_MARKER boundary protection; mode shortening only before aa preverb; 1du_incl uses acir+POT.i instead
- [x] "to come" infinitive mode: preverb ih (1/2) / a (3rd) placed BEFORE INF.B ku via INF_PREV label; 3.A stem for all sg; short stem ʔ-deletion threshold tightened

**Validation at the time (latest pass — 2026-03-19).** These figures were measured against the stored copy of Appendix 1, which had 152 misread forms. Against the appendix as corrected from the page on 2026-11-13 the engine gets 611 of 770 exact (79.4%).
- Appendix 1: **90.3% exact (695/770)** — accent rules integrated via `_apply_ir_accents` (inline, morpheme-level) for ir-preverb verbs + `apply_accent_rules()` (surface-form, non-ir-preverb) for potential cí pattern
- Per verb: to go 96%, to come 94%, to drink it 92%, to do it 89%, to be sick 88%, to have it 88%, to be good 85%
- Dictionary: **86.6% exact** (1,914/2,211 form_2 predictions via `stem_extractor.py`), 88.4% with close — up from 14.8% → 62.0% → 83.5% → 86.6%

**Major improvements since first pass (12.7% → 76.2%):**
- Gemini-collaborative 3-round diagnosis with 10 morphophonological fixes (+25%)
- Rule 24 glottal stop deletion, siʔV epenthesis, r→h before high vowels
- uur preverb ih removal, acir+V r-loss, ʔ deletion after consonant
- Potential shortening conditioned on agent presence
- "to go" suppletive 3pl stems with PREV_3A label (avoids Rule 2R)
- "to drink it" sub_stem shortening, 3pl raak prefix, pl_agent_fusions
- Descriptive-ku verb system overhaul: DESC_KU_MODE_OVERRIDES, raktah plural, 3pl prefix markers, ku→kuu lengthening, aca→acu u-raising (+8%)
- "to come" structural fixes: negative kaakaa, 3.A stem, subjunctive shortening, gerundial/potential/infinitive preverb handling (+4%)

Tasks remaining (priority order — revised 2026-03-19):
- [x] ~~"to be sick" descriptive verb fixes~~ — **done**: 37→97/110 exact (88%)
- [x] ~~"to come" structural fixes~~ — **done**: 21→34/110 exact (31%), 70 close (accent-only), 6 remaining MISS
- [x] **Dictionary stem extraction — first pass** — **done (2026-03-19)**: `stem_extractor.py` predicts form_2 for all 2,211 dictionary verbs. 14.8% → 62.0% exact (1,370/2,211), 67.5% with close. Pipeline: preverb parsing → class inference → prefix+stem junction → coalescence → perfective finals. Parks Ch. 3 OCR'd as reference.
- [x] **Dictionary stem extraction — second pass** — **done (2026-03-19)**: 62.0% → **83.5% exact** (1,846/2,211), 86.3% with close. 12 fixes: i+i coalescence bug, aa/ii/uu-initial glottal insertion, VR reflexive witi- prefix, bracket notation ([+ neg.], [+ i-], [+ raar-], [+ ruu-]), r-deletion vowel-specific ʔ rules (-uur→-uuʔ, -aar→-aa, -iir→-ii), VD ʔ-echo insertion before stops, ir+ut/uur preverb chains, class 3 -aʔu/-aʔa contractions, ut+w junction (w→p), uur+h/s junction (h-absorption, s→c), -sk→-s and -hc→-c cluster rules, (4)-sa no ʔ, (wi) k→t, -i notation stripping.
- [x] **Dictionary stem extraction — third pass** — **done (2026-03-19)**: 83.5% → **86.6% exact** (1,914/2,211), 88.4% with close. 12 fixes: a+u/a+i coalescence for ir-preverb, VD echo false-positive prevention, VD echo for -Vht clusters, VD -wii/-wiir shortening, -uuh shortening, ir+ut junction (keep tuut), class 3 aaʔa contraction guard, ir+ri+uur fusion (ri+uur→ruur), ir+uur h-absorption.
- [ ] **Dictionary stem extraction — fourth pass** (optional) — remaining 257 misses: `si-` prefix (16), `ruuti-` prefix (19), prothetic vowel (5), internal long-vowel shortening, multi-word/bracket headwords. Diminishing returns — remaining cases need morphological decomposition or manual analysis.
- [x] **✅ Accent mark generation + integration** — **done (2026-03-20)**: `accent_rules.py` correctly assigns accent marks to 78/85 Appendix 1 accented forms. 4 rules: (A) Agent-boundary í after t/s/c, (B) Mode-prefix accent (assertive rí, contingent í, gerundial írii), (C) Infinitive kú, (D) Dual sí in absolutive/assertive/negative. Remaining 7 failures are verb-specific stem accents (not generalizable without per-verb annotation). **Integrated into `morpheme_inventory.py`**: ir-preverb accents handled by inline `_apply_ir_accents` (morpheme-level, pre-concatenation); non-ir-preverb accents handled by `apply_accent_rules()` (surface-form, post-sound-changes). Gated by preverb type: uur-preverb does not produce accented forms.
- [ ] **"to do it" investigation** (74/110, 12 MISS) — largest remaining mismatch gap after "to come"
- [ ] **"to come" remaining 6 MISS** — assertive/absolutive 3du (3.A stem used instead of du stem), gerundial 2sg (GER shortening fires on PREV label), 3pl sub suffix contraction (stem deleted); also 3pl sub `verb_class='1'` string adds SUB suffix incorrectly
- [x] ~~VD(u) descriptive verb stem extraction~~ **now 78.2%** (was 1% → 44.7% → 78.2%) — remaining: internal long-vowel shortening, aw- absorption
- [x] ~~VT(3) Class 3 ut- fusion logic~~ **now 100% for (3)|(ut...)** (was 0% → 44.4% → 100%) — aʔuk/aʔu/aʔa contractions all handled

### ✅ Phase 3.1.5 — Noun Possession Morphology *(completed 2026-03-18)*
**Priority:** ✅ Complete (#1 on roadmap)
**Scripts:** `scripts/noun_possession.py` (extraction/classification), `scripts/possession_engine.py` (generation engine), `scripts/example_filter.py` (Skiri-aware example matching)
**Web:** `web/templates/_possession_widget.html` (morpheme chip UI), `web/app.py` (possession API + example filter integration)
**Output:** `extracted_data/noun_possession_catalog.json`, `reports/phase_3_1_5_noun_possession.txt`

Skiri has **four distinct possession systems**, not one. Each applies to different noun classes with different morphological mechanisms. The grammar engine now knows which system to use for any given noun, generates the correct form, and displays it in the web UI with morpheme-level breakdown and confidence scoring.

**The four systems (from Parks Grammatical Overview pp. 36–37 + Blue Book Lessons 5, 7):**

| System | Applies to | Mechanism | Example |
|--------|-----------|-----------|---------|
| 1. Kinship | N-KIN (~23 terms) | Suppletive stems — irregular my/your/his forms | "mother": my=atiraʔ, your=asaas, his=isaastiʔ |
| 2. Body part / physical | N-DEP (body parts) | ri- (PHY.POSS) prefix in verb introducer; noun incorporated | ti+ri+t+kirik+ta → "Ti rit•kirik•ta" (Here is my eye) |
| 3. Agent possession | N (general nouns) | ku-(INDF) + gerundial possessive verb + NOUN | kti ratiru pakskuuku' (my hat) |
| 4. Patient possession | Any noun | uur- prefix when non-agent possesses | tatuuhkuutit aruusaʔ (I killed YOUR horse) |

**Validation (2026-03-18):** 40/40 tests passing (33 possessive + 7 locative/instrumental). Covers all 4 possession systems plus case suffixes, validated against Blue Book Lessons 5, 7, 8 and Grammatical Overview Table 4.

**Validation (2026-11-13):** the built-in list now has 49 checks. When first re-run it gave 31 of 49: the engine was looking for `appendix3_kinship.json` under `scripts/`, so no kinship form was found and `/api/possession/<kinship noun>` returned a server error. With the path corrected: 47 of 49, and the API answers for every noun.

**Suffix corrected (2026-11-13).** The engine built its instrumental and body-part locative with *-biriʔ*. Parks's suffix is *-hiriʔ* (Grammatical Overview p. 30, read from the page image); the `b` came from the AI extraction of that page, and the note above about `b` being an allophone was a rationalisation of the misreading. How *-hiriʔ* attaches was measured on the 42 dictionary words whose etymology ends in it: h stays after a vowel (21 of 21), is lost after a consonant (13 of 13), and after r either the h is lost (2) or, in the one element *-haar*, the r is (6). The engine follows that (`hiri_suffix()`), its plural check now expects Parks's attested *ikstaaririʔ*, ten attested words were added as checks, and it no longer tries to call the conjugation engine's assembler (a call that had never worked). **59 of 59**, the same from the command line and inside the web app; no generated form contains a `b`. What is still wrong with its output is open item 13.

Tasks completed:
- [x] Extract & classify all nouns — filter S2E for N/N-DEP/N-KIN; extract stems (strip -uʔ/-kis); classify by possession system
- [x] Build kinship paradigm table — map appendix3 data to structured 1sg/2sg/3sg forms; cross-validated against Blue Book Lesson 7
- [x] Implement body-part possession constructor — MODE+ri+AGENT+STEM+VERB for any body-part noun; position verb selection (ku vs ta); sound change fallback
- [x] Implement agent possession constructor — `kti + GER-POSS-VERB + NOUN` for 1sg/2sg/3sg (ratiru/rasiru/rau); Blue Book p.35 attested
- [x] Document patient possession pattern — uur- prefix construction; slot 18 in morpheme inventory
- [x] Implement locative suffix system — -biriʔ (body part LOC/INST), -kat (general LOC), -ru/-wiru (tribal/geo LOC); body-part plural -raar- before -biriʔ; 3-class noun routing per Table 4
- [x] **Fix -biriʔ allomorphy (2026-03-20):** b → Ø / C_ (any consonant-final stem). Parallel to -wiru/-ru tribal alternation. Vowel-final stems preserve b (kitkahahki+biriʔ), consonant-final delete it (iks+iriʔ). Parks' /b/ is an allophone (not a phoneme) surfacing only after vowels at morpheme boundaries.
- [x] Handle N-DEP relational nouns — `KNOWN_BODY_PART_STEMS` (25 entries) and `KNOWN_RELATIONAL_STEMS` (5 entries) sets; asaa- "horse/dog", siis- "sharp object" route to agent possession instead of body-part incorporation
- [x] Validate against 40 Blue Book + Grammatical Overview examples — all 4 systems + locative/instrumental
- [x] Populate DB tables — `noun_stems`, `kinship_paradigms`, `possession_examples`
- [x] Integrate into web UI — possession widget with My/Your/His card toggle; color-coded morpheme chips by semantic role (mode/poss/agent/noun/verb/kin); ATTESTED/COMPUTED/LOW confidence badges; locative/instrumental case panel; construction formula display
- [x] Morpheme role classification — `_classify_morpheme_role()` maps labels → UI roles; `morpheme_chips` array in API response for structured rendering
- [x] Possession API — `/api/possession/<headword>` route; Flask blueprint; lazy headword set cache; stub `_lookup_noun_class()` for DB query
- [x] Example filter — `example_filter.py` with Skiri-aware word boundary matching; rejects false substring matches (kirike "what?" ≠ kiri "cat"); handles OCR variants (J→E, 1→E), morpheme-boundary compounds (kiri•wusu' ✓), epenthetic-h compounds (kirihkaatit ✓), prefix disambiguation; wired into `entry_detail()` route filtering both dictionary examples and BB attestations; 14/14 tests
- [x] Kinship dispatch fix — dispatcher tries kinship lookup first for any noun regardless of `noun_class`; handles N-KIN entries stored as plain "N" in DB

**Nominal morphophonology fixes (2026-03-20/21):**
- [x] **Nominal sound change pipeline split** — `apply_nominal_sc()` in `sound_changes.py` runs only noun-safe rules (excludes verb Rules 17/18/19). `possession_engine.py` prefers this over the full verb pipeline. Fixes `ikciriʔ` → `iksiriʔ` (attested).
- [x] **raar→taar resolved** — was Rule 8R (r→t after hard C) all along, masked by Rule 17 corruption. `ikstaaririʔ` now matches attested form with nominal pipeline.
- [x] **-sukat allomorph** — stems ending in -ki/-ski get `-sukat` (not `-kat`). `piiraskisukat`, `asaakisukat` now generate correctly.
- [x] **Instrumental animacy filter** — `generate_instrumental()` accepts `semantic_tags`, returns `None` for animate nouns (N-KIN, kinship/social/animal tags). Widget handles None gracefully.
- **Pattern note:** Three suffix alternations (b→Ø, raar→taar, wiru→ru) all conditioned by same post-consonant environment — single underlying consonant-cluster simplification rule at nominal morpheme boundaries.

**Tagging fixes (2026-03-21):**
- [x] **Kinship false positive guard** — `tag_entries.py` skips kinship keyword path if `grammatical_class` doesn't contain N. Prevents 35 verb false positives.
- [x] **Kinship tag cleanup** — 36 erroneous tags removed (35 verbs + 1 Gemini error). 8 age/gender nouns retagged kinship → social. Tahkuki/Coyote flagged for cultural advisor review.
- [x] **Social keyword expansion** — age/gender/social role terms (youth, lad, maiden, elderly, etc.) added to social taxonomy.

**BB/Parks merge (2026-03-21):**
- [x] **5 orthographic variant pairs merged** — `bb_variant_of` column added to `lexical_entries`. BB stub entries retained for search aliasing. Parks entries marked `blue_book_attested=1`.

**Bug fixes applied during deployment:**
- Kinship file path resolution (REPO_ROOT parent vs current dir)
- Locative test inputs (tribal names need base forms, not already-inflected forms)
- N-DEP relational noun routing (asaa- → agent possession, not body-part)
- Example filter compound heuristic (tightened from `remainder[0] in 'hrstpk'` to epenthetic-h only `remainder[0] == 'h' and len(remainder) >= 3`; prevents kirike false positives when kirike isn't in headword set)
- OCR normalization in example filter (`J→E`, `1→E` for Blue Book header artifacts)

**Key architecture decisions:**
- Agent possession uses attested fixed forms (ratiru/rasiru/rau) rather than generating via conjugation engine — safer, since gerundial+A.POSS interaction hasn't been validated
- `kti` = `ku(INDF)` + `ti(IND.3)` contracted; body part is always 3rd person subject of the position verb
- Locative/instrumental are case forms, not possession — but they share stem extraction and are naturally displayed alongside possession paradigms
- Example filter uses a global headword set (lazily cached at first request) for disambiguation; modifies entry data in-place before template rendering

### 🟡 Phase 3.1.6 — Function Word & Particle Inventory *(seeded 2026-03-19)*
**Priority:** Medium (needed for sentence construction; these are the glue words)
**Depends on:** Phase 3.1 (morpheme slot system), Phase 2.1 (semantic tags)
**Effort:** Medium
**Scripts:** `scripts/function_word_inventory.py`, `scripts/extract_function_words.py`
**DB table:** `function_words` (418 rows: 355 Parks dictionary + 2 BB direct + 61 BB phrase-extracted via Gemini)

Dictionary entries classified as CONJ, DEM, PRON, QUAN, LOC, INTERJ, ADV need to be formalized into a structured inventory with usage rules — not just dictionary definitions. For sentence construction (Phase 3.2), these must be queryable: "which demonstrative goes with visible referents?" "where does the question particle go in the clause?"

**Seed data (2026-03-19):**
- 355 function words from Parks dictionary (lexical_entries with class in CONJ/DEM/PRON/QUAN/LOC/INTERJ/ADV/NUM)
- 2 new function words from BB gap triage direct classification
- 61 new function words from BB phrase extraction via Gemini (5 batches → 35 unique words, 147 occurrences; 4 genuinely new after dedup: `rahesa` "tomorrow", `rariksisu` "hard/very", `tiku` "that", `tireku` "here is")
- OCR artifacts pruned from Gemini extraction; `bb_function_words` raw table has 63 rows (23 unique)
- Report: `reports/extract_function_words.txt`

Tasks:
- [x] Inventory all function words from dictionary (~355 entries across classes)
- [x] Seed from BB gap triage function_word category (11 items → 9 new after dedup)
- [x] Gemini-extract function words from 196 BB phrase gaps (57 new items)
- [x] Prune OCR artifacts from Gemini extraction (done — length ≤ 2, dot-prefixed removed)
- [x] Classify demonstratives by spatial/visibility distinction — **done (2026-03-20)**: `classify_function_words.py` assigns demonstrative-spatial subtypes (proximal, distal, distal-plural, far-distal, etc.) from Parks Ch. 4
- [x] Map interrogative particles and their clause-position rules — **done (2026-03-20)**: 10 interrogatives mapped (content-question, location-question, yes-no-question, quantity-question, temporal-question, indefinite)
- [ ] Document discourse/evidential particles (evidentiality is marked by proclitics, but also by standalone particles)
- [x] Add position_rule + refined_subclass columns — **done (2026-03-20)**: `classify_function_words.py` classifies all 418 items. Distribution: 149 PROCLITIC, 135 PRECEDES-VERB, 51 PRECEDES-NOUN, 44 CLAUSE-INITIAL, 28 STANDALONE, 11 BETWEEN-CLAUSES
- [ ] Cross-reference with Blue Book dialogue examples for natural usage patterns
- [ ] Integrate into sentence builder (Phase 3.2) as selectable modifiers

### 🟡 Phase 3.2 — Sentence Construction Framework *(3.2a done; 3.2b first slice done)*
**Priority:** Medium (depends on 3.1 accuracy improvements + 3.1.5 noun morphology)
**Depends on:** Phase 3.1 (morpheme slot system at 60%+ accuracy — **now at 76.2%**), Phase 3.1.5 (noun possession), Phase 3.1.6 (function words)
**Effort:** Very Large — **now broken into 3 sub-phases to make progress incremental**

Given English input, construct Skiri output.

Sources:
- `extracted_data/appendix3_kinship.json` — 23 kinship terms with possessive paradigms (already extracted)
- `extracted_data/grammatical_overview.json` — 23 pages of grammar (clause structure, word order)
- Blue Book lesson dialogues as test cases (88 examples currently in DB)

#### ✅ Phase 3.2a — Template-Based Sentence Assembly
**Scripts:** `scripts/sentence_templates.py`, `scripts/template_slot_fillers.py`
**Design doc:** `prompts/phase_3_2a_sentence_templates.md`

DONE — 10 templates covering 73% of Blue Book sentences, web UI at
`/sentence-builder` (template cards → slot fill → assembled sentence with
morpheme chips, confidence badge, BB attestation). 27 exact-match validation
tests against BB sentences.

#### 🟡 Phase 3.2b — Person/Mode Derivation *(first slice DONE 2026-09-01)*
**Script:** `scripts/person_forms.py` (validated 27/27 vs the stored Appendix 1 at the time; 25/27 vs the appendix as corrected from the page on 2026-11-13, see open item 26)

Key insight: the from-scratch conjugation engine (`morpheme_inventory.conjugate`)
reproduces only 14.8% of attested dictionary forms — but the person/mode
prefixes sit at the LEFT EDGE of forms the dictionary already attests, and
alternate regularly (IND ta-/ti- ↔ ABS ra-/ri-; 1.A t ↔ 2.A s). So derive
unlisted forms FROM attested ones instead of computing from scratch:

- **2sg indicative** from form_1 (agent t→s with junction repair: r-stems
  tah-→tast-, t-stems tac-→tas-, w-stems tatp-→tasp-; junctions learned from
  1,617 attested form_1/form_2 pairs)
- **absolutive mode** (ka/kirike/kiru questions) by mode-prefix swap
  (1st/2nd: t→r; 3rd: ti→ra, tu→ru, tih→riih desc, tiʔ→raʔ)
- **descriptive-ku persons** for VD/VL (3sg ti+STEM → 1sg tiku+STEM,
  2sg ta+STEM, 2sg-abs raa+STEM)
- **present/future for 1sg/2sg** by person-prefix transplant onto attested
  form_3 (IMPF) / form_5 (INT)

Coverage (2,242 paradigm verbs): 2sg 78%, 3sg-absolutive 91%, 1sg/2sg
future 77–78%, present 50–57%. Every derived form is one left-edge prefix
swap away from an attested form.

Integration: T3/T4/T5/T8/T9 accept `verb` + `person` (1sg/2sg/3sg) +
`tense` (past/present/future) slots — auto-conjugated, derived forms capped
at MEDIUM confidence with a derivation note. Web UI: verb search
(`/api/verbs`) + who/when selectors. Validation: 34/34 template tests.

**Modern spelling + pronunciation on sentences (added 2026-09-01):**
`display_utils.modernize_form()` / `respell_form()` — c→č context rule
(c = [č] before vowel, [ts] elsewhere) validated at 98.5% against 1,387
attested phonetic c-positions; end-to-end 99.5% agreement reproducing
attested normalized_forms from headwords. Sentence results now carry
`modern_sentence` + `approx_pronunciation`, and each morpheme chip carries
modern/pron/ipa. **Truth policy: IPA is never generated** — Parks's IPA marks
vowel reduction (ə/ɪ/ʊ) and pitch accent, which are not predictable from
spelling; chips show IPA only when the word is a dictionary headword with an
attested phonetic_form. Spelling-derived pronunciations are labeled ≈.

Remaining 3.2b tasks:
- [ ] Plural persons (3pl raar-insertion; du/pl suppletive stems — hard, many
      verbs use distributive stems not recoverable by prefix swap)
- [ ] Negative mode (kaaka- prefix swap — same left-edge pattern, easy win)
- [ ] Imperfective coverage (only 57% of verbs list form_3)
- [ ] Question particle placement + clause ordering (original 3.2b scope)

#### Phase 3.2b — SOV Word-Order Engine
**Priority:** Medium
**Effort:** Medium
**Depends on:** Phase 3.2a (templates provide test cases)

Takes pre-inflected components and arranges them in correct Skiri clause structure.

Tasks:
- [ ] Map English sentence patterns to Skiri clause structure (SOV word order)
- [ ] Handle question particle placement and clause-final positioning
- [ ] Handle subordinate clause ordering (from grammatical overview)
- [ ] Implement basic coordination (and, but, then) using CONJ inventory from Phase 3.1.6

#### Phase 3.2c — Compositional Sentence Construction
**Priority:** Low (most ambitious sub-phase)
**Effort:** Very Large
**Depends on:** Phases 3.2a, 3.2b, and high-accuracy stem extraction

Full compositional system handling transitivity, evidentials, and complex clauses.

Tasks:
- [ ] Handle transitivity: subject/object marking, preverb system (ut-, ir-, uur-)
- [ ] Implement proclitic system (indefinite ku-, reflexive witi-, dual si-, etc.)
- [ ] Implement evidential system (quotative wi-, dubitative kuur-, etc.)
- [ ] Possessive morphology from kinship data (my/your/his-her paradigms)
- [ ] Blue Book lesson dialogues + kinship constructions as test cases

### ✅ Phase 4.1 — Web Search Interface
**Script:** `web/app.py` (Flask application)
**Depends on:** Phase 1.2 (SQLite DB)

**Stack:** Flask + SQLite (`skiri_pawnee.db`) + Pico CSS + HTMX

**What it does:**
Full-featured web dictionary with bidirectional search, entry detail views, browsing,
flashcards, and live search. Mobile-responsive via Pico CSS framework.

**Features implemented:**
- [x] Backend: Flask app with SQLite read-only connection, HTMX live search
- [x] Bidirectional search: English -> Skiri (FTS on glosses + english_index), Skiri -> English (headword, normalized_form, paradigmatic forms)
- [x] Entry detail view: headword, pronunciation (IPA + simplified), glosses, etymology with morpheme breakdown, paradigmatic forms, full conjugation tables, examples, cognates, cross-references, derived stems, Blue Book attestations, semantic tags
- [x] Morpheme breakdown display: etymology constituent elements shown as morpheme table (prefix/stem/suffix labels from Parks)
- [x] Fuzzy matching: LIKE pattern matching + Levenshtein distance (edit distance 1-2) on normalized forms for learner misspellings; aggressive fuzzy (strip glottals, collapse long vowels, normalize c/ts/ch) for learner-friendly lookups
- [x] Filter sidebar: semantic category tags, grammatical class, verb class (on search results page)
- [x] Blue Book attestation badge on entries and search result cards
- [x] Mobile-responsive design (Pico CSS framework, responsive grid, touch-friendly flashcards)
- [x] Mark generated vs. attested forms: "Attested (Parks Dictionary)" / "Attested (Appendix 1)" labels on paradigm tables
- [x] Browse by semantic tag and grammatical class with paginated results
- [x] Weekly flashcard study system: 21 categories, ~387 curated beginner words, flip-card UI with keyboard nav and shuffle. BB Essentials (Weeks 1-3) + Greetings & Common Words (Week 4) front-loaded; cross-category deduplication via `seen_ids`
- [x] **Pitch accent display** *(2026-03-20)*: `format_pitch` Jinja filter wraps UPPERCASE syllables in `<span class="pitch-high">` (bold + underline). All-lowercase pronunciations show "(pitch not marked)" note. Legend on entry detail, flashcard study, and flashcard guide pages. Applied in: `_entry_card.html`, `entry.html`, `flashcard_study.html`, `flashcards.html`
- [x] Word-of-the-day on homepage with dictionary stats
- [x] Search result re-ranking: exact matches first, BB-attested boosted, data completeness considered; example FTS matches surfaced with snippets
- [x] JSON API endpoint (`/api/search`) for external consumers
- [x] Detected language returned from search for UI display
- [x] Deployment: `requirements.txt` provided; run with `python -m web.app`
- [x] **Noun possession widget** — lazy-loaded via `/api/possession/<headword>` on noun entries; My/Your/His card toggle; color-coded morpheme chips by semantic role (mode/poss/agent/noun/verb/kin); ATTESTED/COMPUTED/LOW confidence badges; locative/instrumental case-form panel; auto-expand for N-DEP/N-KIN, lazy-expand for N
- [x] **Example filter** — Skiri-aware word-boundary matching on entry detail pages; removes false substring matches (kirike "what?" ≠ kiri "cat") from both dictionary examples and Blue Book attestation tables; cached headword set (~4,273 entries) built lazily on first request
- [x] **Data quality dashboard** — `/dashboard` route with corpus stats, field completeness, verb engine coverage, possession engine coverage, E2S linking health
- [x] **UI/UX improvements** *(completed 2026-03-20)*:
  - Spelling preference toggle (Parks vs. Simplified): cookie-persisted, nav toggle, `primary_spelling`/`secondary_spelling` Jinja filters, all templates respect preference, search placeholder updates dynamically
  - Mobile responsive: hamburger nav (<768px), homepage grid stacking, filter sidebar collapse, conjugation table sticky first column, sentence builder bottom-sheet dropdowns, flashcard swipe gestures
  - Accessibility: search direction `role="radiogroup"` with `sr-only` radio inputs, `lang="x-paw"` on all Skiri text elements (entry, cards, flashcards, possession widget, sentence builder, guide), `aria-labelledby` on feedback modal, skip-to-content link, badge contrast WCAG AA compliant, flashcard keyboard nav (arrows, Enter/Space)
  - Learner-friendly: collapsible `<details>` entry sections, learner/expert view toggle (localStorage), pronunciation tooltip `_pronunciation_help.html`, flashcard self-assessment (Got it/Missed with localStorage progress tracking, Review Missed, session summary), "Start Here" beginner card on homepage, learning path timeline on flashcards overview
  - Browse: human-readable grammatical class labels (`GRAM_CLASS_LABELS` dict via context processor, displayed on browse page and as badge `title` attributes)
  - Search: direction toggle on both index and results pages, direction persisted in form params, BB verb form search endpoint (`/api/bb_verb_forms`)

**Routes:**
- `/` — Homepage with stats and random word
- `/search?q=...` — Full search with filters
- `/search/partial?q=...` — HTMX live search endpoint
- `/api/search?q=...` — JSON API endpoint (limit capped at 100)
- `/api/possession/<headword>` — Possession paradigm JSON (morpheme chips + locative forms)
- `/entry/<entry_id>` — Full entry detail (with example filter + possession widget)
- `/browse` — Browse by tag/class
- `/browse/tag/<tag>` — Entries by semantic tag
- `/browse/class/<class>` — Entries by grammatical class
- `/flashcards` — Weekly flashcard overview
- `/flashcards/<week>` — Interactive flashcard study session
- `/dashboard` — Data quality dashboard (corpus stats, completeness, engine coverage, confidence distribution, feedback stats)
- `/about` — About page with data source info
- `/api/feedback` — POST: submit flag/confirm feedback on an entry
- `/admin/feedback` — Review queue for community feedback (accept/reject with notes)
- `/admin/feedback/<id>/review` — POST: accept or reject a feedback item
- `/preferences` — POST: set spelling preference cookie (parks/simplified)
- `/guide` — Syllable pronunciation guide
- `/sentence-builder` — Sentence assembly UI
- `/api/assemble` — POST: assemble sentence from template + slot values
- `/api/slot-options` — Dropdown options for sentence builder slots
- `/api/bb_verb_forms?q=...` — Blue Book verb form search

### ✅ Phase 4.2 — Sentence Builder UI *(delivered with Phase 3.2a, 2026-03-20; person and tense selectors added 2026-09-01)*
**Priority:** Low (depends on Phase 3.2a at minimum)
**Effort:** Large

Guided interface: select person/action/object/tense → assembled Skiri sentence with morpheme breakdown. Shows derivation steps so learners understand *why* the form looks the way it does. Initially uses Phase 3.2a templates; grows with 3.2b/3.2c.

### ✅ Phase 4.3 — Confidence Scoring System *(completed 2026-03-19)*
**Priority:** ✅ Complete (#3 on roadmap)
**Implemented in:** `scripts/stem_extractor.py` (lines 897-1003), `web/templates/_entry_card.html`, `web/templates/entry.html`, `web/templates/dashboard.html`
**Built via:** Claude Code (VS Code) — parallel with stem extraction second pass

The attested/computed binary badge is replaced by a **continuous confidence score** (0.0–1.0) with 3-tier visual indicators, so learners know *how* trustworthy a computed form is.

**Confidence engine (`compute_confidence()`)** — 4-factor weighted score:

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Category accuracy | 50% | Per-`(class)\|(preverb)` exact+close rate from `stem_extractor.py` validation |
| Prediction method | 20% | Boost for explicit `verb_class` and `stem_preverb` fields (vs inferred) |
| Stem complexity | 15% | Penalties for bracket notation `[+ neg.]`, slash alternates, multi-word headwords |
| Sample size | 15% | Bayesian shrinkage — small categories regress toward population mean |

**DB:** New column `lexical_entries.form2_confidence` (REAL, 0.0–1.0). Populated via `python scripts/stem_extractor.py --confidence`.

**Web UI:**
- Search result cards (`_entry_card.html`): green/gold/red badge with tier label
- Entry detail headers (`entry.html`): same badge + score value
- API search results: `form2_confidence` field in JSON
- Dashboard widget (`dashboard.html`): stacked bar chart with high/med/low counts + average

**Results:**

| Tier | Score | Count | Description |
|------|-------|-------|-------------|
| High | ≥ 75% | 2,202 | Reliable predictions |
| Medium | 50–74% | 30 | Minor differences possible |
| Low | < 50% | 22 | Treat with caution |
| **Average** | **88.7%** | 2,254 | |

Tasks completed:
- [x] Define 3-tier confidence model (High ≥75%, Medium 50-74%, Low <50%)
- [x] Compute per-entry confidence scores using 4-factor weighted formula
- [x] Add `form2_confidence` column to `lexical_entries` DB table
- [x] Display confidence as color-coded badges on search cards and entry headers
- [x] Dashboard widget with distribution visualization
- [x] API endpoint returns confidence score
- [ ] *(deferred)* Tooltip/popover explaining what confidence means for that specific form
- [ ] *(deferred)* Log analytics: which confidence tiers are users viewing?

### ✅ Phase 4.4 — Community Feedback Mechanism *(completed 2026-03-19)*
**Priority:** ✅ Complete (#5 on roadmap)
**Implemented in:** `web/app.py`, `web/db.py`, `web/templates/entry.html`, `web/templates/dashboard.html`, `archived/scripts/add_feedback_table.py`
**Built via:** Claude Code (VS Code)

Knowledgeable community members (teachers, elders' family members, students) can now flag errors and confirm forms. All feedback goes through human review — never auto-accepted (Design Principle #6).

**DB:**
- `community_feedback` table: entry_id, feedback_type (flag/confirm), issue_type, suggested_correction, comment, reporter_name (optional), status workflow (pending→accepted/rejected), reviewer_note, timestamps
- Migration script: `archived/scripts/add_feedback_table.py`
- Separate writable DB connection in `db.py` — main dictionary stays read-only

**Entry detail page (`entry.html`):**
- "Flag an issue" button → modal with field selector, issue type, correction field, comment, optional name
- "Confirm this entry" → one-click crowd-sourced verification
- Per-entry feedback counts displayed

**Admin review queue (`/admin/feedback`):**
- Status tabs: Pending / Accepted / Rejected / Reviewed
- Per-item accept/reject with reviewer notes
- Linked to entry detail for context

**Dashboard (`dashboard.html`):**
- Feedback stats widget (total, pending, accepted, rejected) — appears when feedback exists

**API routes:**
- `POST /api/feedback` — submit flag or confirm
- `GET /admin/feedback` — review queue page
- `POST /admin/feedback/<id>/review` — accept/reject

Tasks completed:
- [x] Add "Flag this form" button on entry detail pages
- [x] Create `community_feedback` DB table with full schema
- [x] Simple review queue page (admin-only route) listing pending feedback
- [x] "Confirm this form" button for crowd-sourced verification
- [x] Per-entry feedback counts in entry detail view
- [x] Dashboard widget with feedback stats
- [x] Design principle enforced: never auto-accept corrections — all feedback goes through human review
- [ ] *(deferred)* Track acceptance rate analytics
- [ ] *(deferred)* Email notification to maintainer on new feedback

### ✅ Phase 5.1 — Structured Lesson Content *(v1 DONE 2026-09-01)*
**Script:** `scripts/build_lessons.py` (deterministic — no AI calls)
**Data:** `lessons` DB table + `extracted_data/lessons.json`
**Report:** `reports/phase_5_1_lessons.txt`

All 20 Blue Book lessons parsed straight from `Blue_Book_Pari_Pakuru.txt`:
Skiri + English titles (as printed; Lesson 8 has no English title in the
source and none was invented), page ranges, ordered dialogue exchanges
(Skiri/English line pairs split at sentence punctuation, mid-form syllable
dots preserved), and grammar/culture prose sections (NOUNS, PRONUNCIATION,
COMBINING ROOTS, USEFUL PHRASES...).

Web UI: `/lessons` (progressive lesson cards) + `/lessons/<n>` — vocabulary
tables drawn from `blue_book_attestations` with dictionary-entry links
(normalized form, pronunciation, class badge; "not in Parks dictionary"
label when unlinked), dialogues in BB practical spelling as printed,
collapsible grammar notes, and "Practice these patterns" cards that open
the sentence builder with the lesson's attested template preselected
(`/sentence-builder?template=Tx`).

- [x] Extract lesson dialogue texts with English translations (20 lessons)
- [x] Map lesson vocabulary to dictionary entries (via blue_book_attestations)
- [x] Extract grammar explanations per lesson
- [x] Lesson sequencing (Blue Book's own 1979 order preserved)
- [x] Link lessons to sentence-builder patterns (Phase 3.2a template map)
- [x] Interactive exercises *(2026-09-01)*: matching (click-to-pair vocab),
      fill-in-the-blank (dialogue lines with a lesson word blanked, 4-way
      multiple choice), and "say it in Pawnee" reveal drills. Generated
      deterministically per page load from the lesson's own verbatim
      material (`web/app.py:_build_exercises`) — no generated language.
- [~] Lessons 3–4 vocabulary gap: Gemini re-extraction of pp. 39–49
      (`scripts/extract_lesson_gaps.py`, dry-run/apply; existing rows never
      modified, new items matched via Phase 2.2 machinery)
- [ ] BB glossary pages (123–130, inside Lesson 20's span) not itemized

**Data safety (2026-09-01):** community_feedback now auto-exports to
git-tracked `exports/community_feedback.json` on every submit/review (the
one table not rebuildable from sources); backup scripts write to the
OneDrive-synced `pari_pakuru_backups/` (home-dir fallback), existing
backups copied over.

### ✅ Phase 5.2b — In-App Spaced Repetition *(2026-09-02)*
**Module:** `web/srs.py` (SM-2 scheduler, unit-tested 7/7 transitions)
**Route:** `/study` (+ `?lesson=N` / `?tag=X` scoping), `POST /api/srs/review`

Server-side SM-2 scheduling over dictionary entries (user does not use Anki
— review state lives in the DB: `srs_cards` + append-only `srs_reviews`,
covered by the OneDrive backup regime). Study UI reuses the flashcard
card-flip design with Again/Hard/Good/Easy grading (keyboard: space flip,
1–4 grade); "again" requeues the card within the session and lapses it.
New-card selection prefers BB-attested entries with pronunciations. Every
lesson page has a "Study this lesson's words" button scoped to that
lesson's vocabulary attestations. Nav: Study link.

### 🟡 Phase 5.2 — Spaced Repetition / Flashcard Export
**Priority:** High — **elevated** (low effort, high impact; Design Principle #3 says "export everything" but the export tasks are still unbuilt. A teacher can hand out a printed paradigm table *today*; accuracy improvements help later.)
**Depends on:** Phase 1.2 (dictionary data)
**Effort:** Small

Generate exportable study materials from the dictionary.

Tasks:
- [x] In-browser flashcard study system (weekly sets, flip cards, keyboard nav, shuffle) — built in Phase 4.1 (`web/flashcards.py`)
- [x] Semantic category decks (19 categories: kinship, animals, body, food, etc.)
- [x] Include pronunciation (IPA + simplified respelling) on every card
- [x] Blue Book-attested entries prioritized in card selection
- [x] **Anki deck export** — **DONE (2026-03-20), unused** (in-app study, Phase 5.2b, replaced it; the exported deck was removed from the repository on 2026-11-13). `scripts/anki_export.py`: 4,336 cards across 19 semantic tag decks + "All Words" parent. genanki .apkg output. Stable model/deck/note IDs for safe re-import. CLI flags: `--dry-run`, `--deck TAG`, `--advanced` (per-sense Option B), `--verbs-only`, `--bb-only`, `--min-confidence`.
- [x] **Pre-export data cleanup (2026-03-20):** `scripts/dedup_entries.py` removed 22 p2/p71 duplicate pairs + merged kusisaar parser artifact (4,366 → 4,343 entries). Preserved hiksukac (VD/VP) and racawaktaarik (VI/VT) as legitimate polysemy. `scripts/display_utils.py`: `display_headword()` with 5 rules (bracket, slash, paren onset, suffix paren, bound-morpheme dash), `gram_class_label()`, `morph_class_note()`. Tested against all 281 notation entries — zero problems.
- [x] **Card template spec locked:** Option A multi-sense (primary sense + "+N more" note), form2_confidence >= 0.75 threshold for verb forms, format_pitch_anki() for HTML pitch accent, per-class back notes (N-KIN, N-DEP, LOC, ADV-P), example dedup on english_translation.
- [x] **Printable flashcard sheets** — **DONE (2026-11-10)**: `scripts/build_flashcard_pdfs.py` → `curriculum/flashcard_pdfs/` (24 weekly PDFs, four cards to a sheet, double-sided).
- [ ] **🔴 Printable PDF wordlists and paradigm tables for offline use** — highest-impact remaining export for classroom use; target users may have inconsistent internet access. Same query as Anki, rendered via reportlab/weasyprint.
- [ ] Blue Book lesson-aligned decks (vocabulary per lesson)
- [ ] Audio placeholder fields (for future recordings)

### ✅ Phase 5.3 — Static site on GitHub Pages *(2026-09-12)*
**Script:** `scripts/build_static_site.py` · **Workflow:** `.github/workflows/static.yml` · **How to:** `DEPLOYMENT.md`

The search, flashcard and lesson pages are rendered from the Flask templates
into `docs/` and served by GitHub Pages. Search runs in the browser over
`docs/data/dictionary.json` (Fuse.js); there are no per-entry pages. The
workflow only uploads `docs/`; the site is rebuilt on a developer's machine,
because the database is not in git. Links are relative, so the site works
under the repository's Pages path.

### ✅ Extraction audit *(2026-09-01)*
**Report:** `reports/extraction_audit_2026-09-01.md` · **Repairs:** `scripts/fix_audit_issues.py`, `scripts/upgrade_phonetics_from_textlayer.py`

Question: is the database a faithful copy of the printed dictionary, and is
the learner spelling derived correctly?

- A stratified sample of 50 Skiri-to-English entries was checked field by field against the page: all 47 that could be located matched. English-to-Skiri linking: 5,132 linked subentries, none dangling.
- An independent re-implementation of the spelling rules reproduced the stored learner spelling for all 4,273 entries.
- Seven issues were found and repaired the same day: c/č under-conversion (60 spellings corrected), seven entries that had lost senses on import (the uniqueness rule on the `glosses` table was dropped), 23 of 32 missing IPA forms recovered, 227 leftover OCR characters, doubled examples after de-duplication, 315 verb forms with line-break hyphens, and drift between the JSON and the database.
- **Second-method cross-check.** Every IPA form was compared with the PDF's own text layer (`reports/_s2e_page_index.json`). 130 forms that had lost their special characters were replaced from the text layer; agreement between the two methods is now 99.76% (4,194 of 4,204 compared).

### ✅ Flashcard and static-site audit *(2026-10-01, follow-ups 2026-10-12)*
**Report:** `reports/audit_data_construction_2026-10-01.md`

Question: do the flashcards and the public site carry the data faithfully?

- Sound: pitch survived respelling in all 1,542 entries that have it; every flashcard carries IPA.
- Fixed 2026-10-01: the static site had dropped the IPA and the page references (A1, A2); definitions were being cut at 120 characters, including two band-name explanations (A3); multi-sense words showed one sense with no sign of the others (A4); 68 respellings contained stray `?` marks (B1, `scripts/fix_respelling_artifacts.py`).
- Fixed 2026-10-12: the flashcard curriculum is frozen in `curriculum/flashcard_sets.json` so that week numbers, to which learners' progress is keyed, no longer shift (B4, `scripts/freeze_flashcard_sets.py`). Lesson vocabulary linked to dictionary entries rose from 234 to 339 of 531 (`scripts/link_bb_vocab.py`). Fourteen OCR errors in lesson titles were repaired (`scripts/fix_lesson_titles.py`).
- Open: B2, B3, B5, B6, C1 to C5. See "Open items".

### ✅ Phase 6.1 — Word-building guide, version 1 *(2026-11-07 to 2026-11-10; superseded)*
**Scripts:** `scripts/root_extraction.py`, `scripts/build_root_curriculum.py` (+ `root_curriculum_spec*.py`) · **Output:** `curriculum/roots/`

First attempt to answer "which roots and affixes are used most, and in what
order should they be learned?" Every entry was segmented from the stored
parse of Parks's etymology and checked against the headword; roots were
ranked by the number of headwords containing them; seven units of lessons
were written by hand from a specification in which every Pawnee form is a
database lookup. 1,320 root senses; segmentation confidence 1,085 high,
1,575 medium, 1,683 low.

Done in the same days and **still in use**:

- `curriculum/weekly_flashcards.md` (`scripts/build_weekly_flashcards.py`): the 387 frozen flashcard words as 1,015 paper cards, Week 1 = Sunday 2026-11-08. (Rebuilt from version 2 on 2026-11-13: 372 words shown, 995 cards.)
- `curriculum/flashcard_pdfs/` (`scripts/build_flashcard_pdfs.py`): the same cards as printable double-sided sheets.
- Respelling repair (`scripts/fix_pronunciations.py`, report `reports/fix_pronunciations_report.txt`): optional sounds kept in parentheses, `{k/t}` alternations restored, Blue Book-only entries re-syllabified; 1,273 entries changed in the database, the JSON and the frozen sets; 32 stems left for review.

Version 1's analysis is superseded by Phase 6.2, which found that the stored
parse it relied on puts meanings on the wrong pieces. Its files are kept; see
`curriculum/README.md` for why.

### ✅ Phase 6.2 — Word-construction analysis, version 2 *(2026-11-12)*
**Instruction:** `prompts/skiri_word_construction_v2.md` · **Code:** `scripts/morphology_v2/` · **Output:** `curriculum/roots_v2/` · **Method:** `curriculum/roots_v2/METHOD.md`

A re-analysis built so that every claim can be checked: each Pawnee form is
looked up from a source record, each analysis gets a tier that follows
mechanically from its evidence, the rules were tested on entries not used to
tune them, and one command regenerates everything byte for byte.

**Evidence channels.** E1 Parks's printed etymology (re-parsed from the raw
text); E2 the pieces joined by named sound rules reproduce the headword; E3
the verb's five forms behave as the analysis predicts; E4 each piece recurs
with the same meaning in other words; E5 a Blue Book seam falls on a boundary
of the analysis; E6 Parks's grammar tables; E7 cognates (recorded only).

**Results** (run of 2026-11-13, after that day's data fixes; the first run differed by one root and three words).

| | |
|---|---|
| Words analysed | 4,337 lexemes (on 2026-11-12: 4,343 rows less six groups of true duplicates; those six rows have since been removed from the database) |
| Tiers | A 1,086 · B 1,320 · C 1,569 · D 1 · no claim 361 |
| Headword reproduced from Parks's pieces | exactly 3,103 · nearly 587 · not 286 (version 1 had 1,085 high-confidence segmentations) |
| Inventory | 1,699 lexical morphemes (A 308, B 246, C 1,145); 57 affixes (A 21, B 9, C 27) |
| Teachable building blocks (tier A or B) | 549 roots + 30 affixes |
| Words a learner can take apart completely | 1,791 (41.3%) with all 579 blocks; 480 (11.1%) with the first 100 |
| Held-back test entries | tier A 18 of 18, tier B 18 of 18, tier C 12 of 12 match the printed page; piece meanings 78 of 78 |
| Compound verbs that inflect like their final root | 1,080 of 1,123 (96%) |
| Independent re-derivation of the top 86 shapes | 154 of 180 senses matched; 91.6% of example words under the same sense |

**What it established.**

- The stored `constituent_elements` glosses are unreliable. Parks's printed etymology must be re-parsed, and his literal translation is not in the order of the pieces.
- The Blue Book (Lesson 3, pp. 41–42) states seam rules the sound-change engine lacked: r becomes h before a consonant (195 of 196 cases), w becomes p after a hard consonant (64 of 64), k drops before p (32 of 32).
- "This shape has only one known meaning, so assume it" was wrong every time it could be checked, and is never counted as evidence.
- Shapes that differ only in vowel length are not merged; 85 such pairs are listed for review.
- Parks's dotted compound stems are entries in their own right and must be resolved before their parts are read.
- 74 basic and 15 bound verb roots reach tier A or B, in line with Parks's "approximately one hundred".

**Limits.** The test set is small (18 of 18 leaves a 95% interval down to 82%)
and tests faithfulness to Parks's page, not whether Parks is right. The page
transcribers and independent reviewers were AI models. Affixes that Parks
rarely labels, and the several functions of the three preverb shapes, are the
weakest parts. The held-back half has been scored more than once and is no
longer unseen.

**Not done.** Nothing from it is on the public site. No speaker or linguist
has reviewed `curriculum/roots_v2/review_queue.md`. (The 43 data errors it
found were applied on 2026-11-13; see below.)

**Weekly flashcards rebuilt from it (2026-11-13).** The cards took their
"built from …" notes and their related-word cards from version 1. Checked
against version 2, 12 of 162 notes read differently and 7 printed a piece's own
shape as its meaning. `scripts/build_weekly_flashcards.py` now reads
`curriculum/roots_v2/evidence.jsonl`. A piece gets a meaning only where Parks
glosses that piece by itself, or where the checked meaning and the stored gloss
(or Parks's translation of the word) agree; otherwise it is shown bare. Checking
the two against each other showed that neither is always right: version 1 had
the meanings of *Ickariʔ* on the wrong pieces, and version 2 reads the first
piece of 'eleven' as "added" where Parks's "one" is plainly meant. Both are now
shown bare.

### ✅ Repository clean-up *(2026-11-13)*

- Removed from the working tree, all recoverable from commit `2e77095`: 139 MB of intermediate dictionary JSON, run logs, superseded report drafts, nine debugging scripts, three overlapping GitHub Pages guides, the unused Anki deck, four page images, two dead scripts.
- Ten checkpoint files that were never in git were moved to `OneDrive/pari_pakuru_backups/repo_cleanup_2026-11-13/`.
- Design documents, parsing instructions and schemas gathered in `prompts/`; `blue_book_extracted.json` moved into `extracted_data/`.
- A `README.md` in every folder; `DEPLOYMENT.md` replaces the three Pages guides; the quick reference rewritten from the live database.
- Three faults found while checking the documentation against the code:
  - `scripts/possession_engine.py` looked for the kinship table in a folder that does not exist, so kinship nouns were treated as ordinary nouns and `/api/possession/<kinship noun>` returned a server error. **Fixed**: the engine's own checks went from 31 to 47 of 49, and the API now answers for all 1,708 nouns.
  - `DB/test_schema.py` could not read `schema.sql` on Windows. **Fixed**: 53 of 53.
  - The possession engine builds instrumental forms with *-biriʔ*, a misreading of Parks's *-hiriʔ*. Fixed the same day; see Phase 3.1.5.

### ✅ Data fixes *(2026-11-13)*
**Script:** `scripts/fix_data_2026_11.py` (dry run by default) · **Report:** `reports/fix_data_2026-11-13_report.txt` · **Backups:** `OneDrive/pari_pakuru_backups/*_20261113_*`

The 43 errors proposed by the word-construction analysis were each checked
against the page image or the PDF text layer before anything was applied.
Checking them turned up more of the same kinds, and one new kind.

| Fix | Proposed | Applied | Checked against |
|---|---|---|---|
| Page number 2 where the entry is on book page 419 | 23 | 28 | text layer of both pages |
| Letter-spaced text ("c l o s e  u p") | 12 glosses | 13 glosses, 12 example translations, 14 etymologies | page image (glosses); plain English (the rest) |
| Duplicate rows of *kaa…* entries (`-p2-` and `-p71-`) | 6 | 6 removed; two cleaner fields kept from the copies; 7 English-index links moved or repaired | page image; the pairs are identical in headword, IPA, class, forms and examples |
| *caʔuuhtuʔ*: etymology and cognates | 1 | 1 | page image |
| *ciihtahaahiriʔ*: "(contemp.)" stored as a verb class | 1 | 1; the label put back in front of the gloss | page image |
| Accent marks dropped by the character decoding | not proposed | 269 entries; plus ÷ → ú in 25 etymologies, 27 cognates, 10 English-index forms | page images for each stand-in character; the text layer for each position |

The last row is described under Phase 1.1a. It changes what learners see: 260
of the 269 entries had shown no accented syllable at all, 48 of them flashcard
words (*kuruks* 'bear' is now `KOO-dooks`), and two respellings had lost a
vowel.

The JSON dictionaries and the frozen flashcard file were updated by the same
script (week membership unchanged), the word-construction analysis was run
again, and the static site was rebuilt.

### ✅ Flashcard Week 20 held for community review *(2026-11-13)*

Audit item B6. `curriculum/held_for_review.json` lists the week;
`web/flashcards.py` leaves listed weeks out, so the web app, the static site
and the paper cards no longer show it. Week numbers do not change. Releasing it
is one deleted line and a rebuild, and is the Pawnee Nation's decision.

### ✅ Source-fidelity audit *(2026-11-13)*

**Question:** does every stored value that claims to copy a printed page match
the page? **Instruction:** `prompts/source_fidelity_audit.md`. **Code:**
`scripts/source_audit/`. **Results:** `reports/source_audit_2026-11/`, starting
with `findings.md`. The audit changed no data (649 input hashes identical
before and after). It ends in `proposed_fixes.jsonl`.

Why another audit: the three earlier ones sampled, and where they compared two
readings both used the same unverified character table. This one compared
everything, verified the table first, and let the page image decide.

| Stage | What was done | Result |
|---|---|---|
| 0 | Database written to `DB/dump/` as text; `scripts/db_dump.py --restore` rebuilds it | round trip exact, 46,783 rows |
| 1 | Every (font, character code) pair of the text layer read from glyphs cut out of the pages | 52 pairs, all settled; 16 had been decoded wrongly or never |
| 2 | Skiri-to-English: 4,244 entries, 50,736 fields against the text layer, both directions | 97.45% identical; 894 differences; planted-error test 510 of 510 |
| 3 | 369 crops of differences read blind | all 303 read differences show the text-layer reading; agreement sample 60 of 60 |
| 4 | Appendices 1 to 3, chapters 3 and 4 read blind from tiles; abbreviations against their text layer | Appendix 1: 152 of 770 forms differ; chapter 4: 85 of 797 words; see below |
| 5 | Blue Book: the 93 Blue Book-only entries and a sample of 60 other forms read from the scan | of the sample, 9 match the scan, 41 lack the printed accent, 9 have a wrong letter |
| 6 | English-to-Skiri: 6,431 printed entries against the JSON and against the database tables | JSON 95.9% identical; database tables 77.7% |
| 7 | 2,250 proposed fixes, 827 with a value that can be applied as it stands; review page; `apply_fixes.py` | nothing applied by the audit itself; see the next entry |

What it found, most important first:

1. **The tables an AI model read from page images are the weak part.**
   Appendix 1 as stored has 152 wrong forms in 770 (accents the page does not
   have, vowels dropped or doubled, one block shifted by a row). The
   conjugation engine's 90.3% is measured against that copy. Appendix 2 has
   *burii-waa* and *burii* for printed *hurii-waa* and *hurii*. Appendix 3 has
   *asaas*, *atipaat*, *apaat*, *ataati* for *asas*, *atipat*, *apat*, *ataat*.
   The grammar chapter extraction has 34 more words with `b` for `h`.
2. **The dictionary entries are a good copy with a known list of faults.**
   305 of 4,244 entries have a difference in a Pawnee form or in meaning:
   22 verb forms (*tikituum* for *tikituus*), 39 IPA forms (14 of them not
   Parks's IPA at all but the spelling cut into syllables), 16 combining
   forms, 102 cognates and 146 etymologies (mostly stand-in characters in
   words cited from other languages: stored *sáhnió* is printed *sáhniš*),
   71 stretches of printed text the database lacks (12 IPA forms, about 15
   examples, the derived stems listed under ten bound stems, qualifiers such
   as "(personal name)"). One printed entry is missing (*kusisaar*, the
   imperfective-only verb, book page 451) and one stored entry is not a
   headword in the book (`SK-aakaqa-p351-3592`).
3. **The character table.** The phonetic font has a regular grid of twelve
   accented vowels (tense and lax, acute and grave). ə́ and ɪ́ are confirmed.
   The stored hyphen is the printed syllable dot and the stored bullet is the
   printed dash at the edge of a bound form. In words cited from other
   languages the code `ó` is š, `Ý` is é, `í` is ó.
4. **The database's English index is an old copy.** `english_index` and
   `cross_references` were imported from the file before cleaning: 3,986 IPA
   forms not in Parks's notation, 177 with raw stand-in characters. The
   current JSON is clean and should be re-imported.
5. **The Blue Book data came from the OCR text of the scan.** The book prints
   an accent on the stressed vowel; no stored form has it. About one form in
   seven has a wrong letter, and three dictionary entries are built on misread
   forms (*had'* for printed *haú'* "yes", *tsktis•kakusu'* for
   *tskús•kakusu'* "chair", *ti•kuwtitiku'* for *ti•kuwútiku'*).
6. **`column_position` is wrong for 393 entries**, and nothing uses it.

What the audit cannot show: that a printed form is right, or that anything the
engines generate is right. It does not replace a speaker.

Cost: 12 sub-agents for blind readings, 2.78 million tokens (about 230,000
each); 156 images read in all. The comparisons with the text layer cost nothing and can
be re-run after any change (`scripts/source_audit/README.md`).

### ✅ Audit fixes applied; Parks's IPA symbols; Blue Book forms from the scan *(2026-11-13)*

The decisions taken on the audit's four questions: commit; review and apply;
keep Parks's notation, retain the IPA and make sure the simplified forms
follow from it accurately; read the rest of the Blue Book.

**1. Fixes applied.** `scripts/apply_audit_fixes_2026_11.py`; record in
`reports/source_audit_2026-11/applied_fixes_report.txt`. 807 changes, each
backed by the text layer or by a blind reading confirmed on a third look.

| What | Changes |
|---|---|
| Appendix 1 (`verb_paradigms` and `extracted_data/appendix1_conjugations.json`) | 152 forms |
| Appendix 2: *hurii-waa*, *hurii* | 2 |
| Appendix 3: *asas*, *atipat*, *apat*, *ataat*; five rows of book p. 543 added to the JSON | 10 |
| Abbreviation list | 3 |
| Grammar chapter extraction: `b` read for `h` | 22 strings, 34 words; then, in a later run, the forms the first pass could not reach (*-:hus*, *-hus*, *tihurás*, *ratkuhurasi*, *tuksuhuuhwiitit*) |
| Sound-change rules: example forms | 5; then, in a later run, the two phonetic forms printed with Rule 24, which had been stored in an ASCII stand-in (`[chepaat]` for printed [čəpaat], `[eskuts]` for [əskuts]) |
| Dictionary verb forms | 19 |
| Stand-in characters in words cited from other languages | 162 |
| Combining forms: a space or a line-break hyphen inside the form | 10 |
| Headwords: the 22 bracket notes Parks prints after a headword, and 5 other fixes | 27 |
| `column_position` | 393 |
| Entries: *kusisaar* added (book p. 451); `SK-aakaqa-p351-3592` removed (not a headword in the book) | 2 |

The record has the first run (807 changes) and four later runs (12 more):
one headword the first run did not reach, two learner spellings, and the two
rows marked "later run" above, which were found when the letter check
(`scripts/source_audit/alphabet_check.py`) was run again after the fixes.
`scripts/sound_changes.py`, which can refill the `sound_change_rules` table,
was corrected in the same places, so that refilling it does not bring the
misreadings back; table and script now agree field for field.

Not applied, because each needs a person with the page: open item 45.

**2. Parks's IPA symbols.** `scripts/restore_parks_ipa.py`; record in
`ipa_restored_report.txt`. Every Parks entry's phonetic form was set to the
form printed in its own entry, decoded with the verified table: 4,147 changed
in symbols only, 75 were corrected in content (some had been the spelling cut
into syllables, not his IPA), 9 were added, 13 were already as printed. No
Parks entry is without a phonetic form now. `scripts/ipa_notation.py` is the
one place that knows the old working notation; the respelling code converts
through it. 54 respellings changed, and three learner spellings that had been
made from a wrong phonetic form. Both JSON dictionaries and the frozen
flashcard file were brought in step.

`scripts/check_simplified_forms.py` makes the respelling and the learner
spelling again for every Parks entry and compares them with what is stored:
no difference in 4,244 entries. One known coarseness, which is not a copying
error: Parks writes a short i or u as tense [i], [u] in some places and as lax
[ɪ], [ʊ] in others, and the respelling writes `ih` and `oo` for both. 589
entries have such a vowel (open item 43).

**3. Blue Book.** `scripts/source_audit/bluebook_rest.py` (crops and grading)
and `scripts/apply_bluebook_scan_fixes.py`; record in
`bluebook_applied_report.txt`. Six blind readers read the 843 crops the audit
had not reached. With the audit's 153 crops that makes 949 distinct stored
forms: every one that has a page.

| Result | Forms |
|---|---|
| Same as stored | 157 |
| Accent restored | 565 |
| Apostrophe, dot or space corrected | 45 |
| OCR slip corrected (ú read as *ti* or *ii*, á as *d*, í as *f*, é as *j*) | 105 |
| Left for a person (letters differ 49, capitals 12, reader unsure 8, crop missed the form 8) | 77 |

738 attestation rows, 79 Blue Book examples, 76 dialogue lines in 18 lessons
and 960 strings in `extracted_data/` were corrected. Three entries built on
misread forms have new headwords: *hauʔ* "yes" (was *had*), *ckuskakusuʔ*
"chair", *tikuwutikuʔ*. The 93 Blue Book-only entries no longer have a
phonetic form: the book prints none, and the stored ones had been made from
the spelling.

**4. Rebuilt and measured again.** Static site, weekly flashcards (cards
changed in 16 of the 24 weeks; the Week 1 card "yes" now reads *hauʔ*),
printable sheets, word-construction outputs (still 549 roots and 30 affixes,
1,791 words taken apart completely).

| Check | Before | After |
|---|---|---|
| Dictionary fields identical to print | 49,443 of 50,736 (97.45%) | 50,597 of 50,757 (99.68%) |
| Planted-error test | 510 of 510 | 510 of 510 |
| Conjugation engine, Appendix 1 | 695 of 770 (90.3%), against the misread copy | 611 of 770 (79.4%); 137 within two letters; 22 further off |
| Form 2 prediction | 1,904 of 2,197 (86.7%) | 1,915 of 2,197 (87.2%) |
| Person derivation | 27 of 27 | 25 of 27 |
| Noun possession | 59 of 59 | 59 of 59, after three expected kin forms were corrected |
| Sound changes, sentence templates, schema, respelling tests | pass | pass |

The lower conjugation figure is the true one: the earlier figure counted
forms that agreed with a misreading of the page.

The comparison after the fixes is kept in
`reports/source_audit_2026-11/after_fixes/`; the audit's own record of what
it found is unchanged beside it.

Cost: six more blind readers, 1.31 million tokens. The audit and its
follow-up together: 18 sub-agents, 4.09 million tokens.

### ✅ Page citations; the entries completed from the print; the whole entry on the public site *(2026-11-14)*

Ranks 2, 3 and 5 of the "What's next" list of 2026-11-13, and rank 4 as far
as it could be taken without a person holding the books.

**Page citations (rank 2).** `scripts/fix_page_citations.py` set
`lexical_entries.page_number` to the page of the printed book for the 3,511
Parks entries that held the number of a PDF file. The page is the one on
which the entry's headword stands, from the audit's pairing of every stored
entry with its printed entry. The step from file number to book page (plus
348) was not assumed: the script reads the page number printed at the head of
each of the 181 pages and stops if one disagrees. The JSON dictionary (3,540
entries, 29 of them rows the database does not hold) and the frozen
flashcards (253 cards) follow. Entry ids keep the old number. The comparison
with the page now counts a file number as a difference. Record:
`reports/page_citations_report.txt`.

**What the dictionary prints and the database lacked (rank 5).**
`scripts/complete_from_print.py` takes every new value from the PDF's text
layer and refuses a change it cannot find in the printed entry.

| What | Values |
|---|---|
| Derived stems Parks lists under ten bound stems, into the empty `derived_stems` table | 21 |
| Examples that are printed and were never stored | 18 |
| Forms cited from other languages still in stand-in characters (*iiótir* is *iištir*) | 19 |
| A typographic apostrophe stored where the page prints ʔ | 11 |
| A hyphen the typesetter put at the end of a line and the parse kept (*witii-karaahuraariʔ* is *witiikaraahuraariʔ*; `raah-kuuc+uʔ` is `raahkuuc+uʔ`): 550 etymologies, 67 examples, 39 other forms, 28 cited forms | 684 |
| Letter-spaced and split words ("o n  t h e  p i g .") | 133 |
| The gloss of an etymology as printed, where the parse had paraphrased it ("plural to be strung" for `PL + to be strung`) | 31 |
| Single corrections, each checked against the page (a dropped half of an etymology, a gloss's wording, a qualifier put back where the page has it) | 27 |
| Stored and not printed: three numbered verb forms for the noun *itkaakahaaruʔ*; four labels the parse made up for bracket notes | 7 |
| A space before a full stop, comma, semicolon or bracket | 496 |
| **In all** | **1,447 in 1,178 entries** |

The piece lists the parse had made from the etymologies
(`constituent_elements`) were brought in step: 441 of them held a piece with
a line-end hyphen or an apostrophe. The line-end hyphens explain why the
audit of 2026-09-01 saw "78 example sentences with a possible line-break
hyphen": the comparison accepted either reading of a hyphen at a line end,
so a kept hyphen never counted as a difference. The rule now applied: the
hyphen goes when the next line begins with `+`, or when the word goes on in
the Skiri font; it stays before an English gloss or a punctuation mark
(a bound form such as *wiruu-*), and where the headword has a hyphen of its
own.

The comparison itself was widened: it now looks at the qualifier stored with
an example and at the derived stems (80 more fields), and the planted-error
test measures the printed text left unaccounted for instead of counting
stretches.

| Check | Before | After |
|---|---|---|
| Dictionary fields identical to print | 50,597 of 50,757 (99.68%) | 50,807 of 50,837 (99.94%) |
| Differences left | 218 | 37 |
| Planted-error test | 510 of 510 | 510 of 510 |
| Learner spelling and respelling follow from Parks's forms | no difference | no difference |
| Word-construction analysis, regenerated | tiers A 1,093 / B 1,315 / C 1,568 / D 1 / none 360 | A 1,093 / B 1,316 / C 1,568 / D 1 / none 359 |
| Engines (conjugation 611 of 770, form 2 1,915 of 2,197, person derivation 25 of 27, possession 59 of 59) | | unchanged |

The 37 left, each with its reason in `print_completion_report.txt`: 13
grammatical classes (nine are the project's own N-KIN, two store "(pl.
subj.)" with the class, two are printed twice); seven stretches the
comparison cannot place although the text is stored; six places where the
page breaks a line after a slash or inside a cited word; two headwords and
two bound forms where the page breaks a line at a hyphen; and seven values
where the page itself is in doubt (a stray *a*, an unclosed bracket, an
apostrophe for ʔ, *rihkuupaȞkstarit*) or the stored value rearranges a
qualifier.

**Forms that need a look at the page (rank 4, in part).**

- *Blue Book.* The 77 forms the first reading left open were cut again with
  the whole line and its neighbours (`scripts/source_audit/bluebook_second_look.py`)
  and read by one sub-agent that saw only the ten sheets (128,000 tokens).
  The two readings agree on 55. For 35 of those, what both readers read is
  the stored row's own form, and it was applied (*KIRIK1 RU'?* is *KIRIKÉ
  RU'?*, *atlas* is *atías*, *Nawa niru!* is *Nawa rúru!*). For the other 20
  both readers read a longer or another word at that place (*rakis* under
  *tirakis*) or English text: the red line had been placed by a match inside
  a longer word, so the stored form may be right and stand elsewhere on the
  page. Those, the 13 on which the readings differ and the 9 where a reader
  was unsure make the 42 left.
- *The same forms elsewhere.* 628 values in `bb_gap_triage` (401),
  `blue_book_attestations.full_sentence_pawnee` (136), `bb_function_words`
  (61) and other attestation rows held the old OCR forms and were corrected
  from the same readings. The sentence templates were not touched.
- *Grammar chapter.* No second reading was made (it would take three readers,
  about 700,000 tokens). Instead the dictionary served as a third witness
  (`scripts/source_audit/chapter4_third_witness.py`): where the blind
  reader's form is a form the dictionary prints and the stored one is printed
  nowhere. That holds for eight words; three differ in letters and were
  corrected (*askatahciriʔ*, *iriirapahaatu*, *tuctiraahawista*); five differ
  only in an accent or a final glottal stop and were left, because the
  chapter may print an accent or an underlying form that a headword lacks.
  Two stored words are confirmed by the dictionary. About 40 stay open.
- *From open item 45.* The three "verb forms" of *itkaakahaaruʔ* are not
  printed and were removed; the combining form is *takasistik [+ raar-]*
  (the hyphen was the typesetter's). The empty singular cell of *tir* in
  Appendix 2 and *rihkuupaȞkstarit* are still for a person.

**The public site (rank 3).**

- `docs/data/dictionary.json` now carries everything the dictionary prints
  for an entry: preverb, the numbered verb forms (9,210 for 2,163 verbs),
  the other forms, the etymology (3,689), the forms cited from related
  languages (597), the derived stems, and the qualifier of each example. One
  entry to a line, so a change to an entry is one line of difference.
- A search result shows what it showed before and, behind "More from this
  entry", the rest. Searching a verb form finds its verb. Every value is
  escaped (etymologies are printed in angle brackets).
- **Held:** the 143 entries tagged `ceremony` show senses and examples as
  before and none of the added detail; the result says so (open item 50).
- Every result has "Send a correction", which opens a GitHub issue with the
  entry filled in; the About page links to the same place.
- The About page was written again for the site as it is: the two books, what
  a visitor can do, how a word is written, how far to trust it (compared with
  the print; not reviewed by any speaker or by the Pawnee Nation; ceremony
  words waiting for review), what is not on the site and why.
- "Pitch" is now "accent" everywhere a reader sees it, and the two sentences
  that said pitch changes meaning in Pawnee are gone: Parks writes that his
  phonetic forms mark the accented syllable. The word is Parks's; whether it
  is the right one for learners is still a question for rank 1.
- Two of the four example words under the search box, *raawi* 'sun' and
  *aatius* 'father', were not in the dictionary at all. They are now
  *sakuuruʔ* 'sun' and *rikucki* 'bird'.
- `search.js` was loaded twice by every page, so each search ran twice.
- `scripts/check_static_site.js` runs the page's own code against the built
  data: 13 checks, all 4,337 entries rendered.

Rebuilt from the corrected data: the word-construction analysis, the weekly
paper cards and their printable sheets (446 lines with a page citation), the
static site, the text copy of the database.

Cost: one sub-agent, 128,000 tokens.


### ✅ The grammar chapter read a second time; Blue Book forms read at their own place *(2026-11-14, continued)*

Asked for: "continue rank 4, you can do the second reading of the chapter",
with the decisions of the morning confirmed and leave to push.

**Grammar chapter (Chapter 4, book pages 29 to 51).** The stored copy,
`extracted_data/grammatical_overview.json`, is one AI reading of the page
images from March 2026 with the prose paraphrased. The audit had read every
Skiri form once more, blind. Where the two differed, one reading stood
against one.

- *The second blind reading.* The 23 pages were cut again, differently (92
  tiles, one band to an image, larger; a reader could have any part drawn at
  twice the size from the PDF). Three readers saw only their tiles: not the
  stored text, not the first reading. 613 forms, no letter marked unclear.
  535,000 tokens (the first reading had taken 574,000).
- *The two blind readings agree.* They do not differ on one Skiri-looking
  word in the whole chapter. So wherever the stored word differed from the
  first reading, it differs from the second in the same way; in no case did
  the second reading come out for the stored word.
- *38 words corrected* (`scripts/source_audit/chapter4_second_reading.py`):
  11 in vowel length (*tiiraaraspaatasit* is *tiraaraspaatasit*, *ruukiitaat*
  is *ruukiitat*), 10 where only an accent was wrong, 5 with a glottal stop
  the page does not have (*asaakiʔ* is *asaaki*, *riicikiʔ* is *riiciki*), 1
  with both, and 11 in other letters (*taatakaraspiʔ* is *taataktaraspiʔ*,
  *Takiihaahusaʔ* is *Takiikaahusaʔ*, *iriiruurakuuraaru* is
  *iriiruurakuurahuraaru*, *wiiruuhaasitiiʔ* is *wiiruuhaasitikstarit*). The
  stored copy had twelve words with an accent; neither reader saw an accent
  anywhere in the chapter.
- *One stored word stands.* *tikiwaakuʔ* 'it's barking' had been listed as
  doubtful. Both readers copied an apostrophe where the glottal stop belongs:
  the print has the wrong sign, and the comparison had cut it off as a
  quotation mark.
- *How a correction is tied to its place.* The blind reader's word must have
  the same English gloss after it as the stored word, or the same Skiri word
  before or after it; or the stored word differs only in an accent and
  neither reader saw any; or it is a long word and the only one like it on
  the page. No word of fewer than four letters. Twelve stored "words" that
  are English (*st* from "1st", *an*, *has*) are named in the script and left.
- *Breakdown lines.* The analyses after "<" were compared piece by piece
  with both readings, which a comparison of words cannot do: 22 pieces
  corrected. 15 are *-Ø PERF* stored as *Ø PERF*; 3 are *Ø- 3.A* stored as
  *-Ø- 3.A* or *-Ø 3.A*; 2 are the subordinate *-hus* stored with the length
  mark of the non-subordinate *-:hus*; also *a* 'come' and *-Ø SUB.4*.
- *Table 17 and 21 places beside it* (named one by one in the script, each
  applied only while both readings hold the text given as its evidence). The
  stored Table 17 (suffixes for aspect and subordination) had merged the
  cells of *-ʔ* and *-his* and of *-:huʔ* and *-:hus*, had given the
  perfective a combined form *-hustarit* that the table does not print, and
  had lost the length mark of *-:hus* in every non-subordinate row. It now
  reads as both readers have it. The summary lines the extraction had written
  from the wrong table were corrected with it. Also: *-:hus* in the heading
  of the non-subordinate imperfective (p. 46); the breakdown of
  *tiwaawaktiikusitit* (p. 48); *-itik + -:hus* and *-itiikuʔ* in the list on
  p. 51 (the stored copy had a raised *u* for the last two letters); and a
  zero the stored copy had put before *SUB.3* (p. 46).
- *Where the chapter and the dictionary differ, both are kept.* The chapter
  prints *tiwaarukstiʔ* 'he is holy' where the dictionary's verb form is
  *tiwaarukstiiʔ*; it prints the name *uukahpaa* 'Quapaw' beside
  *uukaahpaawiru* 'among the Quapaw'. The stored chapter now says what the
  chapter prints; the dictionary data is untouched.
- *What this reading did not compare.* The English prose (the stored copy
  paraphrases it); the labels and glosses inside breakdown lines beyond what
  the pieces show; the cells of the other tables, which were compared word
  by word only (open item 51).

**What had been built on the misread words.**

- *The possession engine* took 'dog' to be *asaakiʔ* and, on that word and
  *riicikiʔ*, stripped a final *-kiʔ* from any noun as a "diminutive
  variant". Neither word is printed. With *asaaki* the engine gives
  *asaakisukat* 'among the dogs', which the dictionary attests and which the
  tests had set aside as unexplained. The rule is removed (it would have cut
  *asaawakiʔ* 'pinto' to *asaawa*); the tests use the printed words: 60 of 60.
- *The word-construction analysis* (v2) draws its worked examples from the
  chapter: 90 of 93 are now usable (70 before), and the spurious affixes *Ø
  PERF*, *-Ø- 3.A* and *karíi-* are gone from its list. Rebuilding its test
  sets showed that two of them (the Appendix 1 cells and the Blue Book seams)
  had been made before the audit's corrections and only hash-checked since;
  they are now made from the corrected data. The tiers did not move (A 1,093
  / B 1,316 / C 1,568 / D 1 / none 359).
- *The superseded v1 word-building files* quoted ten of the words; the
  quotations were corrected in the files and in the spec they are made from.

**Blue Book.** Of the 42 forms two readings had left open, 20 were cases
where both readers had read a longer or another word: the red line stood at
the first place where the OCR text holds the stored letters. The English
stored with the row shows which place is meant (the row says "He, she went",
the readers had found "I went" beside *Tatúks•at.*).
`scripts/source_audit/bluebook_right_place.py` finds the place where the
stored letters stand directly before the row's own English, or stand once as
a word by itself, and cuts it. 25 forms were found at another place than the
one read before; one reader read them blind (58,000 tokens). 18 corrected,
by the rule of the first reading (the reader's letters are the stored
letters; the accents, raised dots and apostrophes the OCR cannot see are
taken): *Tuks•at.* is *Túks•at.*, *tirardh•kiwi* is *tiraráh•kiwi*, *patsi*
is *patsí*. 7 read exactly as stored. 17 are left: in eight a reader could
not tell whether a raised dot or a faint mark is there, and the others are
fragments or sentence-initial words the stored row cites in another form.

| Check | Before | After |
|---|---|---|
| Stored Skiri words of the chapter (counted page by page) that stand in both blind readings | 491 of 530 | 526 of 526; twelve more stored "words" are English |
| Stored breakdown lines identical to the first reader's line | 65 of 97 | 91 of 97; the other six differ in an oddity of the print (an apostrophe for ʔ, a stray semicolon, a missing quotation mark) or run across two tiles |
| Blue Book forms left for a person | 42 | 17 |
| Noun possession | 59 of 59 | 60 of 60 |
| Dictionary against the page, planted-error test, learner spelling, page citations, site check, database round trip | pass | unchanged, pass |
| Word-construction analysis | 34 tests, 17 gold files, 3,809 forms resolved | 34 tests, 17 gold files (three rebuilt), 3,811 forms resolved |

Cost: four sub-agents, 593,000 tokens (535,000 for the chapter, 58,000 for
the Blue Book forms).


### ✅ Review packet; engines prompt; the English index from the page; chapters 2 and 5; what rank 4 listed *(2026-11-14, third part)*

The owner asked for the review packet, for a prompt that hands the engines to
a fresh session, and for ranks 3 and 4 of "What's next" to be carried out.

**The review packet.** `scripts/build_review_packet.py` writes
`community_review/review_packet.pdf` (41 pages), the same as a web page, and
`response_sheet.csv`. Five parts: the ceremonial vocabulary (the 15 words of
the held flashcard set and 161 more entries a keyword marked); the 372
flashcard words week by week; the word-building guide with its ten open
questions; the About page word for word; three questions about sound and
spelling. Every Pawnee form in it is read from the database when it is built.
The built files are not in git: they gather the held-back vocabulary in one
readable place, and the repository is public.

**The engines prompt.** `prompts/engines_review.md`. It gives a new session
the facts (what is settled, what Parks says in chapters 2 and 5, what each
engine does and scores) and the two lessons of November (a test proves
nothing if its expected forms are not attested or the rule was fitted to
them; do not tune while measuring). It holds back this session's opinion
until the new one has measured, and it stops with a decision paper before any
engine is changed.

**The English index, from the page.** The English-to-Skiri section has a text
layer set in one font for each kind of thing. `scripts/repair_english_index.py`
reads the 6,431 printed entries by those fonts and makes the file and both
tables say what the page says.

| | Before | After |
|---|---|---|
| English entries in the file | 6,414 | 6,431 |
| Subentries / rows of `english_index` | 8,073 / 8,067 | 7,806 / 7,806 |
| Rows with a Skiri term | | 5,165, of them 5,162 linked to their dictionary entry |
| Cross-references | 4,585 | 4,578, with 5,209 Skiri forms in braces |
| Fields equal to print, the audit's comparison (file / tables) | 95.90% / 77.69% | 99.99% / 99.99% |

What went: 516 placeholder subentries ("(see cross-reference)", "N/A"), 133
cross-reference forms the first reading had stored as terms, 15 subentries
that duplicate one printed under a neighbouring headword. What came: 24
headwords the file lacked, most of them the last column of page 338. Six
entries the first reading had split at a page boundary were put together, and
seven subentries moved to the headword they are printed under. 221 phonetic
forms were still in the old working notation and seven differed in content;
168 terms had the preverb inside the term; 12 classes differed. Page numbers
are the pages of the book (63 to 346; the printed number was read from all
284 pages); `source_page` is the number of the page file.

Two checks that do not share the reading's logic. The audit's own comparison,
which looks for each stored value in the printed entry, finds 32,632 of
32,636 fields equal; what it still lists are a line break inside a preverb,
one headword whose text layer lacks a space, and 152 printed pieces it cannot
place because it searches by substring. A count of letters, entry by entry:
118,262 letters are printed in the type of Skiri terms and 118,262 are
stored. Five cross-references print the figure 1 where an English term should
stand (*braid*, *cherry*, *monster*, *postal carrier*, *water monster*); they
are stored as printed.

**Chapters 2 and 5.** Thirteen pages with no text layer, read twice by
readers who saw nothing but the page, with different cuts
(`scripts/source_audit/front_matter_reading.py`). All 138 Skiri forms of
chapter 2 and all 57 of chapter 5 stand letter for letter in both readings,
and the 1,609 words of running text of chapter 2 are the same in both. The
chapters are stored as forms, tables, headings and a summary of each section
in the project's words (open item 54 says why not as text). What they
establish for the project:

- Stress is not phonemic and is not written on words; the phonetic forms mark
  accented syllables, and Parks calls most accent patterns variable in the
  end (p. 15). "Accent" is his word (item 9); a rule that predicts accents
  has little to stand on (item 40).
- The long and short shapes of the same prefix or stem alternate, and "the
  difference in vowel length is not predictable" (p. 14). That bears on
  questions 1, 2 and 7 of the word-construction analysis and on the two
  vowel-length misses of person derivation (item 26).
- The dictionary writes *kt* after one speaker; all other twentieth-century
  Skiri speakers said *tt* (p. 16). Item 53.
- The five verb forms are defined on pp. 56-57: form 1 is a first person
  patient for passive verbs; form 4 is the gerundial mode, "usually"
  perfective; some classes lack some forms.
- *asaaki* 'dog' is printed a third time without a final glottal stop, and
  the locative suffix as *-hiriʔ* (p. 54).

**The grammar chapter's tables.** `scripts/source_audit/chapter4_tables.py`
puts each table together from the pieces the two readers wrote tile by tile.
Six of 14 are the same row for row; six have the same text in every column
(one reader wrote each printed line as a row); tables 6 and 7 differ and are
stored in both readings.

**The Blue Book glossary.** It is an English index with page numbers and no
Pawnee. `scripts/bluebook_glossary.py` reads it from the scan's text layer
and checks every reference against the page it points to: 589 of 644
confirmed, and for 505 the Pawnee forms stored for that page are listed
beside it.

**The Blue Book-only entries.** `scripts/bluebook_only_entries.py` found the
printed form for 87 of the 93 and, which nobody had looked for, a dictionary
entry for 37 of them (item 52). The public site shows the printed form and
names the dictionary's entry; the About page, which had said these words are
not in the dictionary and are shown in the textbook's spelling, was corrected.

**Printables.** `scripts/build_printables.py`: the word list (372 words, 19
pages) and Parks's seven verbs in full (770 forms, 8 pages), in
`curriculum/printables/`. The English line the stored appendix has for every
form was written by the extraction, not by Parks, and is not printed.

**Cost.** Five readers for chapters 2 and 5: 114,899, 114,174, 141,057 and
60,125 tokens for the four that finished (430,255), and the one that was
stopped, whose count was not reported. The estimate given beforehand was
500,000. Nothing else used a sub-agent.

**Checks afterwards.** Every check of the README's table as before; the site
check 13 of 13; the database text copy restores exactly;
`repair_english_index.py --check` exits 0.

---

### ✅ The engines review: read, measured, and a paper for the owner *(2026-11-14, fourth part)*

The prompt written earlier that day (`prompts/engines_review.md`) was run
through its first three stages. **Nothing was changed**: no engine, no data
file, not the database (its SHA-256 at the end is the one taken at the
start). The review's own files are in `reports/engines_review/` and
`scripts/engines_review/`.

**Stage 0, the baseline.** All 24 checks of the top-level README were run
before anything else. All gave the stated result but one stale figure: the
row count of the text copy (46,821 in the README, 46,553 since the English
index was rebuilt). `reports/engines_review/baseline.md`.

**Stage 1, what each engine is built on.** The eight engine files (11,285
lines) were read in full, every rule traced to a statement of Parks, a
pattern in attested forms, a fit to a test, or a misread form, and every
expected form in the engines' own tests looked for in the corrected sources.
`reports/engines_review/profiles.md`.

- Six more rules or words were built on a misread form, beside the three
  already known, and each still passes its own test: the possession engine's
  *kti* (OCR for *kú*) in "my X" for every common noun; *ilan'*, *kirti* and
  *stiks* in the sentence builder (OCR for *Háu'*, *Kirú*, *Súks*); and three
  rules of person derivation, two from misread cells of Appendix 1 and one
  from the OCR text *Ka rii hitu'?* (*Ka rú hitu'?*). The audit of 2026-11-13
  had corrected all of these in the tables; the code was never looked at.
- Most tests do not compare with a printed form: 7 of the 11 sound-change
  tests, 23 of the 60 possession tests and 10 of the 34 sentence tests hold
  the engine's own output, a fragment, or nothing to compare.
- Stored engine output is presented as source in two places: the app's
  possession box under "ATTESTED", and the word-building guide's table of
  prefixes under "Parks's own tables" (open item 59).

**Stage 2, measured without tuning.** Ten test sets were built from attested
forms only, each recorded with its source and hash, and "seen" forms (those
an engine's rules were fitted to) kept apart from "unseen" ones.
`reports/engines_review/measurements.md`.

| Engine | On forms it was fitted to | On forms it was not |
|---|---|---|
| Conjugation | 611 of 770 (79.4%), Appendix 1 | **1,431 of 9,559 (15.0%)**, the dictionary's five verb forms |
| Accent rules | | marks 81 cells of Appendix 1; the page marks 26; 57 marks where the page has none |
| Sound changes | | 8 of Parks's 39 examples to his own rules; 15 of 74 of his worked examples |
| Form 2 prediction | 1,915 of 2,197 (87.2%) | no unseen form 2 exists in the sources |
| Person derivation | 25 of 27, Appendix 1 | 1,503 of 2,124 verbs against the start of form 4: 97% for the rules read from correct forms, 6% for the three built on misread ones |
| Noun possession | 60 of 60 own tests | *kti* on 1,671 of 1,706 nouns; locatives 300 of 675 printed forms (44.4%) |
| Sentence templates | 34 of 34 own tests | recognises none of the 385 Blue Book sentences printed with an accent |

The conjugation engine's own count on the dictionary is 14.8%, the figure
recorded on 2026-03-09 before it was fitted from 35% or less to 90% of
Appendix 1. Only the possession engine and the sentence templates (with
person derivation behind them) reach a person; the conjugation engine, the
accent rules and the full sound-change pipeline are called by nothing.

**Stage 3, the paper.** `reports/engines_review/decision.md` leads with a
recommendation and asks eight decisions: fix the OCR slips on the public
lesson pages first (open item 55); withdraw the conjugation engine and the
accent rules; keep the 24 sound changes as a reference and not as an engine;
keep the form 2 predictor as a checker and remove its badge; repair person
derivation narrowly, measured on a sealed half of the verbs; replace the
possession box by a lookup of what Parks and the Blue Book print; repair the
sentence templates by copying from the corrected table. It says where it
differs from the recommendation of the earlier session (it agrees on the
accent rules and on conjugation, and differs on extending person derivation)
and what such a review cannot show.

**To run it again:** `python scripts/engines_review/run_all.py` (about a
minute; a second run gives the same bytes). `--check` says whether the test
sets still match their sources.

**Verified at the end:** every file of the repository hashed before the
first check and after the last. Outside `reports/engines_review/` and
`scripts/engines_review/`, the only files changed are documentation (this
log and six READMEs) and one rule added to `.gitignore`: the review's
per-form records, which list what the engines computed beside what is
printed, are not put in git. The engines' own checks give what they gave at
the start.

---

### ✅ The engines review, Stage 4: the eight decisions carried out *(2026-11-14, fifth part)*

The owner answered the decision paper with the recommended choice for each of
the eight decisions ("1a 2a 3a 4a 5a 6a 7a 8a"), and they were carried out
the same day in the order 1, 2 and 3, 5, 4, 7, 6, 8. The full record is
[reports/engines_review/stage4.md](reports/engines_review/stage4.md); the
repair of person derivation has its own,
[person_forms_repair.md](reports/engines_review/person_forms_repair.md).
Committed and pushed the same day, at the owner's word
(commits `5727705`, `dbbb366`, `5389a53` and the documentation commit after them).

| # | Decision | What was done | The figure |
|---|---|---|---|
| 1 | The audit's corrections in the lessons | `scripts/fix_lesson_text_ocr.py`: every reading the audit established put into the running text where the old reading stood on its page and differed in more than an accent; titles set from the Blue Book table; `extracted_data/lessons.json` made a copy of the table; `docs/` rebuilt | 214 places in 17 lessons, 12 titles |
| 2 | Conjugation engine, accent rules | moved to `archived/scripts/` with a note at their head; the dashboard counts only copied tables | nothing called them |
| 3 | The guide's "Parks's own tables" | the guide prints Tables 6 to 17 row by row from `extracted_data/grammatical_overview_tables.json`, and lists the 69 pieces Parks labels in his worked examples; `scripts/morphology_v2/` no longer reads the engine's table; `morpheme_inventory` and `verb_template_slots` dropped | 412 table cells, each checked against the file |
| 4 | Sound changes | the file kept as a reference and says so; `--test` replaced by `--measure`; no database write without `--write-table` | 8 of Parks's 39 examples |
| 5 | Form 2 prediction | kept as a checker; badge, score code and 2,239 stored scores removed | 87.2%, seen forms only |
| 6 | Person derivation | split written down first; three rules built on misread forms removed; no invented first person; no present or future for "I" and "you"; the sealed half opened once | 794 of 816 forms on 1,059 unseen verbs (97.3%; bar 97%); no form for 243 |
| 7 | Noun possession | `scripts/printed_noun_forms.py` and a box "Printed forms of this noun" on entry pages; the engine archived; its two tables dropped, three kin rows and four OCR slips deleted; Parks's examples no longer filtered | 734 of 1,706 nouns have something printed |
| 8 | Sentence templates | rebuilt: a pattern starts from a printed Blue Book sentence and a word is swapped only for another printed row; a sentence says whether the book prints it; dictionary verbs apart, in Parks's spelling, by entry | 38 tests; the check at zero exceptions |

**Where the decision paper was wrong.** It counted 65 OCR slips in the
lessons; there were 214, because the audit filed its corrections under four
labels and the paper counted one. It named four non-words in
`function_words`; nine more of that table's Blue Book rows are found nowhere
in the scan's readings. And two rules of person derivation that the paper
kept did not reach 97% by themselves on the open half; two configurations
were therefore fixed before the sealed half was opened, and the one the
paper describes reached the bar.

**The database** went from 46,553 rows in 25 tables to 46,413 in 21. No table
now holds a form a script made. Backups before each change are in
`OneDrive/pari_pakuru_backups/`; the dropped tables are in git history
(`DB/dump/` at `814e8cc`).

**The review's Stage 2 measurements cannot be re-run in place any more**:
they were about files that are now withdrawn or changed. The scripts refuse
to run, so that the record is not written over;
`scripts/engines_review/README.md` says how to make it again.

**Verified at the end:** every check of the README run again (all pass; the
README's tables give today's results); the local app requested on 49
addresses; every file hashed at the end of Stage 3 and again at the end.

**Open after it** (items 60 to 64, and the end of `stage4.md`): the accents
and seven titles of the lessons, which need the page; the Blue Book table's
ties to the wrong entries; `function_words`; one weak rule; the Blue Book
filter on entry pages.

### ✅ The public site rebuilt around the learner *(2026-11-14, sixth part)*

The owner asked for the GitHub page to serve people who want to learn the
language: how a word breaks down and what its pieces mean, how to say it, how
verbs change, and several ways of taking the material in. Until then the site
was a search box with lessons and flashcards beside it. Done in one session,
while another session worked on rank 2; **nothing was committed or pushed**.

**The rule kept.** Every Skiri word and form on the new pages is copied from
a printed source. The pages arrange: a phonetic form is cut at its syllable
dots, a derivation at its plus signs, words with the same printed piece are
listed together. No form is made, the withdrawn engines are not used, and the
project's own word-construction analysis (`curriculum/roots_v2`) is not
published: it still waits for item 1. So the Word building page shows the
pieces and Parks's literal translation of the whole word, and does not say
which word of the translation belongs to which piece.

**What was built** (all of it in `web/`, rendered into `docs/` by
`scripts/build_static_site.py`; the local app serves the same pages):

| Page | What it shows | Source |
|---|---|---|
| Start here (`learn.html`) | Six steps in order: sounds, first words, how words are built, the verb, the lessons, daily practice. A tick for each, kept in the visitor's browser | the site's own pages |
| Sounds (`guide.html`) | The old pronunciation guide, plus: *c* is [ts] before a consonant and at the end of a word and [č] before a vowel; *r* is a tap, often *n* at the start of a word; the tense and lax short vowels; where the glottal stop stands. "Sound it out" takes a flashcard word syllable by syllable. The old example of a phonetic form, which was in a notation the database no longer stores, is replaced by two printed ones | chapter 2 (`extracted_data/sounds_and_alphabet.json`); the stored phonetic forms |
| Word building (`words.html`) | Parks's five noun-making pieces with his examples (Table 5); how to read a derivation; a finder for the words in which the same piece is printed, by piece or by an English word; the entries spelled like a piece, with the warning that the dictionary does not say which one a piece is; his abbreviations | `etymology.raw_etymology` cut by `web/learning.py:split_derivation`; tables 4 and 5; `morpheme_abbreviations` |
| Verbs (`verbs.html`) | The five numbered forms of an entry, on the seven verbs of Appendix 1; Table 6 as five positions; the modes (Table 8) and the person prefixes (Table 9); Appendix 1 as one verb in one mode, the seven verbs side by side, or the ten modes side by side, with the forms hidden for a self-test; Appendix 2; tables 10, 13, 15, 16, 17 | `extracted_data/appendix1_conjugations.json`, `appendix2_irregular_roots.json`, `grammatical_overview_tables.json`; `paradigmatic_forms` |
| Practice (`practice.html`) | Six games of ten questions: choose the meaning, choose the word, match pairs, type the word (either spelling counts), verb forms, word pieces. Missed words are kept in the browser | the flashcard weeks (week 20 left out); Appendix 1; the printed derivations |
| Topics (`topics.html`) | The dictionary's words by the 18 topic tags, narrowed to nouns or verbs or by a typed word. "ceremony" is not offered as a topic | `semantic_tags`, in `data/dictionary.json` |
| A search result | Two new openings: "Say it, syllable by syllable" and "How the word is built"; the topics as links; a link to the entry itself (`index.html?id=`). Lesson word lists and flashcards now link to the entry, not to a search on its spelling | `data/dictionary.json` |

The home page lists the eight ways in under the search box, and the
navigation follows the learner's order. The two PDFs of
`curriculum/printables/` are copied to `docs/printables/` and linked.

**Figures** (2026-11-14, from the build and `node scripts/check_static_site.js`):
of the entries not tagged `ceremony`, 3,689 carry a printed derivation or a
note on the word's origin, and for 3,319 of them it is a derivation of two
or more pieces. The cutting was compared with the parser of the
word-construction analysis (`scripts/morphology_v2/etymology.py`), which it
does not use: the two give the same pieces for all 3,447 derivations that
both cut, and 22 that the parser cuts are left uncut here (a parenthesis
that spans a plus sign, as in *rak+taakaar(+uʔ)*, or an apostrophe written
for the glottal stop); those entries show the printed line only. Each of the
seven verbs of Appendix 1 is tied to one
dictionary entry by its printed forms 1 and 2, and to no other. 28 checks
pass; among them, every piece shown stands in the derivation as printed, no
held entry is in the data files, and no link between the 53 pages is broken.
The six games, the verb views, the finder, the topics and "Sound it out" were
run in a headless browser at desktop and at phone width, with no script
error.

**Decisions made in the session, for the owner to confirm or change:**

- The project's word-construction analysis stays unpublished (rank 1 decides
  it). The page shows Parks's pieces only.
- *kt* and *tt* are still not mentioned on the Sounds page: which to teach is
  Part 5c of the review packet.
- Two sentences of the About page were changed, because "everything you read
  here comes from those books" was no longer exact: it now says that every
  Skiri word and form does, and that the plain-English explanations are the
  site's own.
- The site's small heading reads "Learn Skiri Pawnee" in place of "Skiri
  Pawnee Dictionary".
- The weekly paper flashcards (`curriculum/flashcard_pdfs/`) are not linked:
  they print pieces from the unpublished analysis.

**Files.** New: `web/learning.py`; templates `learn.html`, `words.html`,
`verbs.html`, `practice.html`, `topics.html`; `web/static/js/skiri.js`,
`words.js`, `verbs.js`, `practice.js`, `sounds.js`, `topics.js`. Changed:
`web/app.py` (routes `/learn`, `/words`, `/verbs`, `/practice`, `/topics`,
`/data/<name>.json`, `/printables/<file>`), `base.html`, `index.html`,
`guide.html`, `about.html`, `search.js`, `pawnee-theme.css`,
`scripts/build_static_site.py`, `scripts/check_static_site.js`.

### ✅ The lessons read from the page; the Blue Book ties; the function-word tables *(2026-11-14, seventh part)*

The owner's answer to the five points Stage 4 left open was: commit and push;
read the notes of all twenty lessons from the page; no action on the weak
rule of person derivation; correct the Blue Book table's ties; make the pass
over the function-word tables. The first was done at once (`bf1f4e0`,
pushed). The other three are below. When they were reported, the owner left
the publishing and the pairing of the dialogues to the session's judgement;
both were done the same evening (`fad4a3e`; the learner pages of the sixth
part in `cbeb592`; the site built from both in `12759c6`).

**The ties (item 61).** `scripts/relink_bluebook.py`. Every tie of a Blue
Book row to a dictionary entry that had not been made by the form was judged
again: a row is a form of an entry if it is the headword with the textbook's
short vowels and the meanings share a word. Of 414 such ties, 65 were made
again to the right entry (*asáki* to *asaaki*, *arúsa* to *aruusaʔ*, *tsapat*
to *capaat*, *pita* to *piita*) and 349 removed. 257 of the 1,026 rows are
tied now. A Blue Book sentence is an example of an entry only if one of its
words is tied to it: of the 88 that stood in `examples`, every one under a
wrong entry, 43 stand under a right one and 45 were removed.
`blue_book_attested` follows the ties (242 entries). Report:
`reports/bluebook_relink_report.txt`.

**The function words (item 62).** `scripts/fix_function_words.py`. Each word
of `bb_function_words` was set to what its phrase prints in the scan's
reading (22; *Kirti* to *Kirú*, *Ilanʔ* to *Háu'*) and one row deleted; in
`function_words`, 10 Blue Book rows were corrected and 8 that are no word of
the readings deleted. 406 and 62 rows. Report:
`reports/function_words_pass_report.txt`.

**The lessons (item 60).** The audit had read the Blue Book's listed forms;
the running text of the lessons it had corrected only where a line was one of
those forms. Now every line of the titles, dialogues and notes that is not
plain English was cut from the scan with its number and read.

- *How.* `scripts/source_audit/lesson_text_reading.py` lines the stored text
  up with the words of the scan's text layer, cuts the lines onto sheets of
  strips (42 sheets, 938 strips), and compares what was read with what is
  stored. The reading was made in the main session, strip by strip, writing
  only the Pawnee; 79 lines were read a second time at a wider and larger
  cut, seven a third time. It is one reading, not a blind one. The script
  therefore takes from one reading only what the OCR is known to get wrong
  (an accent it dropped, a raised dot, an apostrophe, *d* for *á*), never
  takes a mark away, and leaves the rest to a second look and a decision
  written down with its reason
  (`reports/source_audit_2026-11/lesson_text_reading/decisions.json`).
- *The cross-check.* The audit kept the place of every crop it cut. Compared
  by place on the page: at 164 of the 286 places that one reading settles,
  the audit's reader had read the same word at that line; at 119 no reader
  had looked at the line; at none had a reader read otherwise.
- *What changed* (`scripts/apply_lesson_page_reading.py`, report in
  `reports/lesson_text_ocr_report.txt`): 286 words from one reading; 42
  places by hand after a second look (words the OCR had split over two
  lines; *to* for the marker *ta* and *it* for *ir* in breakdown lines;
  *perks* for *paks*; the third and fourth of the four demonstratives of
  lesson 7, which begin with *i*, not *ti*); 8 titles (lesson 6 had none;
  lesson 20's title is two lines, *TAT•ÍTSKA RATKU•WA•WAKTIT PARI'*); the
  English title of lesson 8.
- *What was cut.* The extraction had left the title of the next lesson at
  the end of eleven lessons' notes, and after lesson 20 the whole glossary
  (7,013 characters of "work 29 worry 77 …" on the public page). Both are
  gone; the glossary is in `extracted_data/blue_book_glossary.json`.
- *The Blue Book table.* 13 rows are lines of the lessons and had never been
  read at their own line; they now hold what the line shows. For two of them
  the audit's crop had been cut at a line above with the same letters
  (*kas•i•kika* in the word list has no apostrophe, the lullaby above has
  one; *tuh•rá'*): `bluebook_crops_at_another_line.json`. The audit's
  applying script passes over those crops and leaves the 13 rows alone.
- *What it showed:* the dialogues' English was not paired with the Pawnee
  (item 69; repaired next, below); items 70 and 71 are left.
- *Cost.* 55 images were read (42 sheets, 13 for second and third looks)
  where whole pages would have been about 200. The item as a whole, with the
  tool, the comparison and the corrections around it, took roughly twice
  the 150,000 tokens quoted for it: the estimate covered the reading, not
  the work around it.

**The dialogues (item 69).** `scripts/pair_lesson_dialogues.py`. The parser
of 2026-09 had stored the two columns of a dialogue as separate lines: in 83
of 156 lines the English stood in the field for the Pawnee or was missing,
and the lesson pages showed it so. The page itself decides the pairing: a
Pawnee line takes the English that the scan's text layer has to its right on
the same row (22 lines), a merged line is cut where its English begins (7),
an English line after a Pawnee line without one becomes its English or
continues it (8), and two Pawnee lines the page breaks are joined
(*tatuks•á•ka-* / *wahtsu'.*; *Kaas raku•káriu* / *tatutak•érit.*). The
section "NOUN PHRASE: Noun•Adjective", which sat inside lesson 2's third
dialogue, is the first of that lesson's notes. 105 lines; three are printed
without English of their own. `build_lessons.py`, which would write the OCR
text back over all of this, now refuses `--apply` without `--from-scratch`,
and its dry run no longer overwrites `extracted_data/lessons.json`.

**Decisions made in this part, for the owner to confirm or change:**
- Letters under a flaw in the scan stand in square brackets in the lessons
  and in the Blue Book table, filled in only where the same sentence is
  printed whole a page earlier (item 70).
- The next lesson's title and the glossary were cut from the end of the
  notes, and the section of notes was moved out of lesson 2's dialogue.
- 13 rows of the Blue Book table were corrected at their own line on one
  reading; one correction of the audit (*kas•i•kika'*) was withdrawn because
  its crop had been cut at another line.
- The sign for "no marker" in breakdown lines is written *ø*.
- Everything was published without the owner having seen it first.

**Two sessions in one folder.** The learner pages were built by another
session the same evening, in the same working tree. Nothing was lost, but
only because each wrote different files and both edited the shared documents
by small replacements. The two exchanged messages before the commit, and the
other session confirmed its files were complete. For next time: one session
per working tree (`git worktree add ../pari-pakuru-site <branch>`), one
writer to the database at a time, and whoever finishes a unit commits it;
since GitHub Pages serves `docs/` from `main`, work that is not ready for
learners belongs on a branch.

**Feedback on the learner pages**, asked for by the owner:
[reports/learner_site_feedback_2026-11-14.md](reports/learner_site_feedback_2026-11-14.md).
In short: lead each lesson with its dialogue; gather the lessons' useful
phrases; space the practice; say on the page which spelling to learn to
write; do not show a stem's pronunciation beside an inflected word.

Checks: `apply_lesson_page_reading.py --check`, `pair_lesson_dialogues.py
--check`, `fix_lesson_text_ocr.py --check`, `relink_bluebook.py --check`,
`fix_function_words.py --check`, `apply_bluebook_scan_fixes.py` (dry run:
nothing to apply), and every other check of the README (32 in all, and the
site's 28); the public site was built again from the corrected tables and
the learner pages.

### ✅ The five changes to the learner pages; a Blue Book word with the English of its own row (2026-11-15)

The owner's instruction, after reading the feedback on the learner pages:
"continue with your five changes". The five are the first five points of
[reports/learner_site_feedback_2026-11-14.md](reports/learner_site_feedback_2026-11-14.md).
Everything below was built and checked, and then committed and pushed the
same day when the owner said "commit and push": `4c32588` (the data),
`58d6ae9` (the site's sources), `0168bb1` (the built site).

**What the work found before it changed a page.** The phrases page was to
gather the lessons' Useful Phrases, so each phrase's English had to be
certain. The stored pairs of lesson 18 did not read like pairs
(*Sutsiks•áhut* 'Who's been busy?'). The scan's text layer gives every word
its place on the page, so what stands to the right of a form on its own row
can be read without reading an image (`scripts/fix_bluebook_pairing.py
--survey`: 649 word-list and phrase rows). Three runs were out of step, each
by one row, and all three were on the public lesson pages:

- Lesson 18, Useful Phrases. 'Who's been busy?' is the English of the heading
  of the verb set that follows; the extraction put it first and moved the
  five meanings down. As printed: *Sutsiks•áhut.* 'Hold this.',
  *Keskuruh•ra•wíat.* 'Help me.', *Ketuh•rá•wiat.* 'Let me help.',
  *Tat•atsiks•kápakis.* 'I'm sorry.', *Kesku•rahúrihu'.* 'Forgive me.'
- Lesson 10, Additional Words. The second line of the gloss of *het•katáku*
  ('sheriff, office of the law', then '"(badge) against the breast"') was
  taken for the next word's meaning, and six words each got the meaning of
  the word above: *tsahriks•táhrurikukus* is 'police man, "person catcher"',
  *asku•ra•wákahu'* is 'judge, "says it one time"', *ti•kuwútiku'* is 'he is
  killing it', and so on to *ti•wáktiku'* 'he is telling it', which had been
  lost. A Blue Book-only dictionary entry had been made from the third of
  these: the public search answered 'judge' with a verb form that means 'he
  is killing it'. Its gloss is corrected; its class (N) and its tag
  ('number', from "one time") were worked out from the wrong meaning and are
  removed.
- Lesson 9, Basic Words. *ti•ká•isat* 'he went home' had no row, and its
  English stood beside *ti•hú•isat*, which is 'it has sunk (beneath) a
  surface'. The missing word has a row now (it comes last in the lesson's
  list, because rows are shown in the order of their numbers).

16 meanings corrected, 1 row added, 1 entry corrected, with their copies in
`bb_gap_triage` and `extracted_data/blue_book_extracted.json`. Each
correction is proved again on the text layer whenever the script runs; all
three places were also looked at in a cut of the scan (two sheets, six
places: the only images read in this part, a few thousand tokens, no
sub-agents). The same cut settled four slips of the OCR in the English of
the notes (*Yes, Fm fine* for "Yes, I'm fine"; *hail* for the Skidi word
*haú* inside a sentence of lesson 1) and the form of row 2671. Record:
`reports/source_audit_2026-11/bluebook_pairing_fixes.json`,
`lesson_text_reading/second_02.json` and `decisions.json`,
`reports/bluebook_pairing_report.txt`. The engines review's check puts the
old English back before it compares its test set
(`scripts/engines_review/build_test_sets.py`).

**1. The dialogue. The feedback was wrong about the book.** It said the Blue
Book opens every lesson with a dialogue and the page should too. The book
opens every lesson with its Basic Words (6 to 20 of them; 43 in lesson 19,
where the months and weekdays are stored as basic words), then the
dialogues, then Additional Words. The page already had that order, and it
is kept. What was done for the point behind the advice: links at the top of
a lesson to each of its parts; "Cover the English" and "Cover the Pawnee"
over the dialogues, with a covered line shown again when chosen; and on
"Start here" the lessons are step 2, straight after the sounds, as in the
book, where they were step 5.

**2. Phrases.** [curriculum/everyday_phrases.json](curriculum/everyday_phrases.json)
lists the 113 Useful Phrases of 18 lessons and the 16 lines of the two
Useful Conversations of lesson 20, each with one of eight situations
("Meeting someone", "Around the house", "At the table", "Coming and going",
"Thanks, feelings and helping", "Learning and speaking Pawnee", "Weather",
"Money"). `scripts/everyday_phrases.py --check` proves every line: it stands
letter for letter in the lessons' text, it shares a row of the printed page
with its English or stands over it (127 of 127), and the Blue Book table
agrees (95 rows). The new page `phrases.html` shows them with the lesson
each is from; a phrase the book prints in two lessons with two English
renderings shows both (*Tat•atsíks•tehu'.*: 'Thank you.', lesson 8, and 'I
am happy.', lesson 16). The lesson pages take their Useful Phrases from the
same file, so they no longer list a lesson's title, the pieces of a tongue
twister or the lines of a song under that heading, as the table's PHRASE
rows had made them do. One South Band form is left off the phrases page
because two of its letters lie under a flaw in the scan.

**3. Spaced practice.** A Leitner box in the visitor's browser
(`Skiri.box` in `web/static/js/skiri.js`): five boxes; a right answer on a
word that is due moves it up, and it comes back after 1, 3, 7, 14 or 30
days; a miss sends it to the first box, due the same day; one day cannot
move a word twice. The Practice page opens with "Today" (how many words are
due, the count in each box) and "Today's words" is the first choice of
words: the due ones, then new ones in the order of the flashcard weeks. The
flashcards' "Got it" and "Missed" feed the same box, and "Start here" says
how many words are due. Nothing leaves the browser, and the box holds entry
ids, never forms.

**4. One line on spelling.** `web/templates/_spelling_line.html`, in view on
every lesson page, on the flashcard pages and on the phrases page: the
learner spelling is the one to learn to write; the Blue Book column is the
1979 textbook's spelling; "Say it" is a rough guide, not a spelling;
dialogues and phrases are printed only in the textbook's spelling and stay
in it; where a teacher or a speaker writes a word another way, follow them.

**5. No stem's pronunciation beside a word.** In the word lists of a lesson
the columns "Say it" and "Phonetic form" stand under the heading "In the
dictionary", because they are the entry's. The three rows tied to an entry
as a form of its stem (*ti•'at*, *ti•ta•'at*, *we tí•hura•hats*) keep the
link, marked "a form of", and show no pronunciation. "not in Parks
dictionary" reads "no entry linked".

**Also set right on the way.** The lesson pages cite the page numbers
printed in the book (lesson 1 is pages 1 to 5; the page had said 29 to 33,
the pages of the scan). The lessons' index no longer says that every word
is linked to the dictionary or that titles carry OCR slips. The notes of a
lesson say that their English is unread OCR text. The menu folds below
1,024 pixels, where "About" used to stand alone on a second line.

**Decisions made in this part, for the owner to confirm or change:**
- The lesson pages keep the book's order; the dialogue is not moved above
  the basic words.
- The eight situations and which phrase stands under which; the phrases page
  has a link in the menu, the eleventh.
- "Start here" has seven steps: sounds, lessons, phrases, flashcards, word
  building, verbs, practice. It says "in an order we suggest".
- The spelling line says the learner spelling is the one to write. That
  rests on the owner's report of what Pawnee people write today
  (2026-11-14), not on anything from the Pawnee Nation.
- The gaps of the practice box (1, 3, 7, 14, 30 days) and that a round of
  "Today's words" fills up with new words.
- 16 meanings of Blue Book rows changed, a row added and an entry's class
  emptied, on the evidence of the page's rows and one look at a cut.
- The word-construction outputs were made again (`run.py --all`): one entry
  lost its class and one more Blue Book word has a seam, so three files in
  `curriculum/roots_v2` changed by a line or two.

**Not done.** The book prints, over the Additional Words of 11 lessons, what
they are for ("Nouns to substitute for *rakis* in the dialogues."). Those
lines are not stored, and they are the book's own way of making the dialogue
the centre of a lesson (item 74). The other points of the feedback file
(sound, a plan for today, feedback after a miss, folding the reference
tables, pointing outward, `lang="paw"`) were not asked for.

Checks: every check of the README was run again on 2026-11-15 (two new:
`fix_bluebook_pairing.py --check`, `everyday_phrases.py --check`); the
site's own check has 39 (11 new: the stem row, the order and page numbers
of a lesson, the corrected meanings, every phrase on the page of a lesson
it names, the box's arithmetic on days it is given). The changed pages were
driven in a headless browser at desktop and phone width: covering a side, a
round of today's words, the counts after it and three days later.

### ✅ A register of sources; the two dialects of the textbook; hearing a word (2026-11-15, second part)

The owner's instruction: "commit and push. I have placed a new source into the
root. Come up with a plan on how to incorporate these sources to enhance the
database and learner site." The commit and push is the entry above. The plan
was written, four questions were put to the owner, and the plan was approved
the same day (it is kept with the session's plans, not in the repository).
This entry is its first stages. **Committed on 2026-11-15 at the owner's word
("Commit but don't push yet") and pushed later that evening ("commit and
push").**

**The new source is a catalogue, not language data.** `Skiri Pawnee Language
Sources.xlsx` (in the root, out of git) lists 59 resources: the Pawnee
Nation's language programme, its lesson handouts and recordings of its
classes; Indiana University's online dictionary and text collections; the
1997 Skiri course; books, theses, archives and recordings; reference sites.
Each has a credibility score from 1 to 5, a dialect, what it holds, a note on
rights and a link. It says of itself that it was compiled on 2026-11-15 from
web searches and that the scores are its compiler's judgement.

**The owner's four decisions (2026-11-15):** mark the dialect, Skiri first;
ask for permission and change nothing in the repository or on the site on
that account until answers come; take the catalogue in as cleaned data and do
not show its scores; none of the further materials (the 1997 Skiri course,
the textbook's audio, Parks's 1976 grammar) is in hand.

**Three doors.** A source comes in by one of three: the site *links* to it;
it is used to *check* what the two books say, and what is stored is the
project's finding with the citation; or its content is *copied*. The third
door is shut for every source until permission is given in writing.
Ceremonial material is held whatever the answer. The register records the
door for each source ([sources/README.md](sources/README.md)).

**Stage 1. The register.** `scripts/sources_catalogue.py` reads the
spreadsheet into `sources/catalogue.json` (the e-mail address cut out) and
keeps the project's fields apart from the catalogue's: `link`, `section`,
`check`, `copy`, `sensitive`, and `checked` with what a page was seen to say.
Every link was tried. Two of the catalogue's had moved and were found again
(the Alphabet Book, the page on the 1997 course); two gave no answer and are
not listed (the Nation's archive portal, whose address does not resolve from
this computer, and the Pawnee Nation College). Forty answered. Fifteen sites
answered an automated client with a refusal (twelve with 403, one each with
202, 418 and 429) and need a person to open them; Facebook was not tried, and
one record has no link. 18 records are held as ceremonial: 11 by
keyword at import, 7 more by hand (song archives, sacred narrative,
doctoring). The table `sources` holds the same 59 rows.

**Stage 2. Learn with others; hear a word.** A new page, `resources.html`,
lists the 8 sources fit for learners: the Nation's programme, its Facebook
page, the recordings of its classes, its three lesson handouts, the 1997
Skiri course (not online; copies from the Nation's Education Department),
Indiana University's dictionary with sound, a podcast with two people of the
programme, the Alphabet Book. Each was opened first, and the sentence shown
is written from what was seen. "Start here" now opens with it. Every
dictionary word, on a search result, a flashcard, a practice answer and a
lesson's word list, has a link "Hear it at Indiana University" that opens a
search for the word there. Their search finds a run of plain letters, so the
link searches for the longest run of letters in the headword; of ten words
taken at random eight were found, and three of the ten result pages had a
recording. The pages say "some entries have a recording".

**Stage 3. The two dialects.** The catalogue asked whether the textbook is
Skiri. The textbook answers, in its chapter on the alphabet (pp. xviii to
xxiv, read from the scan and stored in
`extracted_data/blue_book_dialect_statements.json`): "the South Band e is
pronounced by Skidi speakers just as if it were an i"; *hr* "is pronounced
simply as h by Skidi speakers"; South Band speakers "have more long vowels",
"so you should decide which dialect you will concentrate on"; "IMPORTANT.
The accent marked in this book is that of some South Band speakers." Its
contents page prints the title of lesson 3 twice: *KIRIKÉ RUT•U'?* (SB) and
*KÍRIKU RUT•U'?* (SK). The Pawnee Nation's own first lesson says the same of
the vowels ("South Band or SB: 8 & Skiri: 6"). So the first sentence the site
gave a learner of Skiri, *Kiriké ru'?*, is written the South Band way, and
the site had not said so.

`scripts/label_bluebook_dialect.py` gives a form a mark and its reason, in
the table `bb_dialect_labels`, and makes no form: SK or SB where the book
prints that mark on the form's own line (20 rows, found with the text layer;
18 marks the first extraction had given stand on lines the page does not
mark, and are not used); "SB spelling" where the form is written with *e* or
*hr* (278 rows, 22 Blue Book-only entries). Lesson pages, the phrases page
and the flashcard pages carry a line "Skiri or South Band?" with the book's
statements folded under it, and each marked form shows its mark. The word
lists' dictionary columns are headed "In the Skiri dictionary". The About
page no longer says the difference is only one of long vowels.

**Stage 4. Spelling.** The Nation's Lesson 1 lists its alphabet: â ê î û for
long vowels, č as in "catch", c as in "cats", ’ for the catch in "uh-oh".
That is the learner spelling of this site, letter for letter, so the line on
which spelling to learn now names the Nation's handouts, and the Sounds page
has the alphabet with the two ways it differs from the dictionary's letters.
The open check on *c* and *č* is closed.

**Stage 5. Permission.** Found while reading the catalogue against the
books: the textbook's copyright page ("No part of this book may be
reproduced … without permission in writing from the Pawnee Tribal Business
Council"), the catalogue's note that the dictionary's content online needs
the publisher's permission, and that the public repository holds page scans
of both books (634 PDFs). This is not legal advice. The owner's decision is
to ask and to change nothing meanwhile. Three letters are drafted in
`community_review/letters/` (kept out of git), and the review packet has a
sixth part: the lessons on the site, the two dialects, the places the site
points to, the works held back.

**Decisions made in this part, for the owner to confirm or change:**
- Which 8 sources are listed for learners, and the sentence shown for each.
  The independent learner's podcast (scored 3 by the catalogue) is not
  listed; the Nation's archive portal is not, because its address did not
  answer.
- Seven sources were marked ceremonial by hand, on top of the eleven the
  keywords caught. The mark may be too wide.
- "SB spelling" is put on every form written with *e* or *hr*, by the book's
  blanket statement. A form the book marks (SK) is never given it.
- The "Hear it" link is a search, not a link to the entry itself; a link to
  the entry needs the university's word (letter 2 asks).
- The wording of the dialect line, of the page "Learn with others", and of
  the three letters. The letter to the Press mentions the page scans.
- The page "Learn with others" has no menu link of its own: it hangs from
  "Start here", the home page, "About" and the foot of every page.

**Cost.** No sub-agents. Web: one request to each of the 59 links (twice,
after the first client failed on certificates), about 20 pages read once,
and 52 searches of the university's dictionary, one second apart, to learn
how its links work.
Images: four small sheets of the textbook's alphabet chapter.

Checks: every check of the README (28 scripts, two of them new:
`sources_catalogue.py --check`, `label_bluebook_dialect.py --check`); the
site's own check has 45 (6 new); the app's 49 addresses and the 13 changed
ones; the new and changed pages looked at in a headless browser. One bug was
caught there and not by a check: a shell heredoc had eaten the backslashes of
a style rule and left a NUL character in the stylesheet.

### ✅ The word web: words joined to the pieces printed in them (2026-11-15, third part)

The owner's request: "I'd like to have a visual of how these words intertwine,
like word bubbles connected to common descriptors. e.g. - bear, black bear,
brown bear, white bear, etc. to show the building blocks of the language".
**Committed on 2026-11-15 at the owner's word ("Commit but don't push yet")
and pushed later that evening ("commit and push").** The owner looked at the
page and answered "no changes": the choices listed below stand.

**The dictionary already holds the example.** Its derivations print
*kurukskaatiit* "black bear" as *kuruks + kaatiit*, *kurukstaakaa* "white
bear" as *kuruks + taakaar*, and *kurukspahat* "brown bear" as
*kuruks + pahaat*, with the literal translation "red bear". The piece
*kaatiit* is printed in 23 words, *taakaar* in 23, *pahaat* in 28. So the
picture needs nothing that is not printed: it is the word-building page's
data (`data/wordbuilding.json`, 3,319 entries with a derivation of two or more
pieces, 1,780 different pieces) drawn instead of listed.

**What was built.** A page `wordweb.html` ("Word web"; `/wordweb` in the local
app) and its script `web/static/js/wordweb.js`:
- A box is a word: the headword and the first meaning, whole or cut short
  with a mark. An oval is a piece of a printed derivation, with the number of
  words it is printed in. A line joins a word to each piece of its own
  derivation, and to nothing else.
- The page opens on the words with "bear" in the meaning or the literal
  translation (8 words; the piece *kuruks* is printed in 6 of them). Fifteen
  English words are offered to start from, and a box takes any English word
  or any piece. A picture can also start from one word (`?word=`) or one
  piece (`?piece=`).
- Choosing an oval brings in ten more of the words in which that piece is
  printed, so the picture grows from bears to black things to horses. An oval
  with words still to come carries a plus sign, and it grows as its words
  come in. Under the picture the chosen word or piece is shown in full, with
  the literal translations, as on the word-building page.
- Shapes can be dragged, the picture moved and made larger or smaller. On a
  phone the picture is laid out tall instead of wide.
- It hangs from the word-building page, from "Start here" and from every
  search result that has a derivation ("See it in a picture, with the words
  that share its pieces"). It has no menu link.

**How it is laid out.** No library was added. The script holds a small layout
of its own: shapes push one another away, a line pulls its two ends together,
and a last pass moves apart any two shapes that still overlap. The same start
always gives the same picture. Where a shape sits means nothing, and the page
says so.

**The rules it keeps.** No form is made: every label is a printed headword,
meaning or piece. The page does not say what a piece means, and does not pair
the words of a literal translation with the pieces. Words hang on one oval
when the dictionary prints the piece with the same letters, and the page says
that the same letters are not always the same piece (the dictionary has two
entries spelled *kuruks*, "bear" and "boil, carbuncle") and that pieces
printed with different letters are kept apart (*kaatiit* and *katiit* each
stand in words for black things). Entries tagged as ceremony are not in the
data. The project's own word-construction analysis is not used.

**Also changed.** In the local app the names the published site gives its
files (`words.html?piece=...`, `index.html?id=...`), which the pages' scripts
write into their links, now lead on to the same pages; before, such a link
ended on "not found" there.

**Decisions made in this part, for the owner to confirm or change:**
- The picture is a page of its own, without a menu link, and opens on "bear".
- The fifteen English words to start from (bear, black, white, red, yellow,
  horse, bird, snake, hand, foot, bone, water, wood, night, big). Each was
  tried and gives a picture with one clear family in it.
- An English word is matched as a whole word, with its plain plural, in the
  meaning or in the literal translation: "bear" does not find "beard".
- A picture starts with at most 24 words, an oval brings in 10 at a time, and
  a picture stops growing at 150 words.
- The size of an oval follows the number of its words in the picture, not
  the number in the dictionary, so that the piece a family shares stands out.

The owner's answer, 2026-11-15: "no changes".

Checks: the site's own check has 51 (6 new: a line only where the dictionary
prints the piece in the word; every piece of a drawn word drawn; the count on
an oval the dictionary's; no shape on another; the same start the same
picture; a box shows printed text only). The page was driven in a headless
browser through its ovals, buttons, start words and typing box, at desktop,
tablet and phone width; the local app's new address and the links to it were
tried. Every check of the README was run again.

**Cost.** No sub-agents, no web requests. Ten screenshots were looked at.

### ✅ The dictionary's spelling first, and a switch for the learner spelling (2026-11-15, fourth part)

The owner's message: "no changes. pdf books removed from docs/. Commit but
don't push yet. I want another update. I want the default spelling to be
Parks, but a toggle button on the top to switch the spelling to the
learner-friendly spelling with accent marks."

The first half was done at once: the second and third parts of the day were
committed in four commits (`89fc77c` the register and the dialect marks,
`2bd6048` the pages' sources, `763ed84` the built site, `8ba5e82` the
documents) and nothing was pushed. **This part was committed and pushed
later the same evening, when the owner had seen the account of it and wrote
"commit and push"** (three commits after those four: the pages' sources, the
built site, the documents).

**How it was before.** Every page put the learner spelling first (*sakûru'*)
and the dictionary's beside it, small (*sakuuruʔ*). The published site was
fixed that way. The local app had a choice, kept in a cookie on the server.

**What was built.**
- **The switch.** Under the menu of every page: *Spelling*, with two buttons,
  "Parks aa c ʔ" and "Learner â č '". It is in view on a phone without opening
  the menu. A page opens in the dictionary's spelling. The choice is kept in
  the visitor's own browser, is read before the page is drawn, and holds on
  every page and on the next visit.
- **Both spellings are in the page.** Wherever a dictionary word is shown, it
  is written twice and a style rule shows one: search results, entry pages,
  the flashcards (front, back, and the card that explains a flashcard), the
  word of the day, the dictionary column of a lesson, the words by topic, the
  practice games, the Sounds page (whose three tables now stand in the page
  once for each spelling). Nothing is respelt in the browser: the learner
  spelling is the one stored with the entry (`normalized_form`), as before.
- **One way of doing it** for the local app and the published site:
  `web/spelling.py` for the templates, `Skiri.spell()` for the scripts. The
  cookie, the route `/preferences` and the four copies of the old filters in
  the build script are gone, and the build no longer cuts the switch out of
  the published pages.
- **What the switch does not change, and where the page says so.** The 93
  words found only in the textbook have one spelling. The lessons' dialogues
  and phrases stay as the textbook prints them. The pages on word building,
  the word web and verbs stay in the dictionary's spelling, because pieces
  and forms are printed in it; a visitor who chose the learner spelling is
  told so there.
- **The words about spelling.** The line that asked "Which spelling do I
  learn to write?" and answered "the large one, the learner spelling" could
  not stand. It now reads "Two spellings of one word": what the dictionary's
  spelling is, what the learner spelling is, that the learner spelling is the
  alphabet of the Pawnee Nation's own lesson handouts, and where the switch
  is. About, Lessons and Sounds were reworded to match.

**"With accent marks".** The owner's words are the site's own label for the
respelt form on the flashcards page ("Respelled form — learner-friendly
spelling with accent marks"): the circumflex of *â î û* and the hook of *č*.
That is what the switch shows. No mark for the accented syllable is put on a
spelling: the dictionary marks the accent only in its phonetic form, and a
spelling with it would be a made form.

**Found on the way, and corrected.** The card that explains how to read a
flashcard had been written out by hand long ago: the word *akahwi'ûsis* with
the meaning "boy" and a phonetic form in letters Parks does not use. The
dictionary's *akahwiʔuusis* means "restroom; outhouse, privy". This was on the
public flashcards page. The example is now a card taken from the data when
the page is built (*iraariʔ*, a kinship word), so it says what the card says.

**Decisions made in this part, for the owner to confirm or change:**
- The switch's two names, "Parks" and "Learner", each with three of its
  letters; its place under the menu, at the right.
- The line on spelling no longer says which spelling to learn to write. It
  says who writes which, and ends as before: where a teacher or a speaker
  writes a word another way, follow them (item 89).
- Word building, the word web and verbs do not follow the switch.
- In the Sounds page the name "Simplified" became "Learner", to match the
  switch.

The owner's answer, 2026-11-15: "commit and push". None of the four was
spoken to; they stand until the owner says otherwise.

Checks: the site's own check has 58 (7 new: a word is written in both
spellings; the choice is kept and nothing breaks without storage; every page
opens in the dictionary's spelling and has the switch; each of the 242
flashcard words with two spellings stands in both, the dictionary's large;
a search result and a lesson word carry both; the Sounds page holds both
sets of tables; no page still says the learner spelling comes first, and the
example card is a card of the data). The switch was pressed in a headless
browser on the flashcards, a search result, a lesson, the Sounds page, the
topics and the pages that keep their spelling, and the choice held after
loading the page again. The local app's pages were tried, 19 addresses and
14 pages by what they hold. Every check of the README was run again.

**Cost.** No sub-agents, no web requests. Three screenshots were looked at.

### 🔲 Ongoing — Data Quality & Maintenance

- [x] **~~Blue Book gap triage~~** — **DONE (2026-03-19)** via Gemini batch analysis. 516 of 984 BB vocabulary items classified into 8 categories: phrases (196/38%), inflected verbs (141/27%), unlisted nouns (94/18%), descriptors (40/8%), possessed forms (15/3%), function words (11/2%), loanwords (10/2%), OCR artifacts (9/2%). Key finding: 65% are morphological gaps (roots exist in Parks, inflected forms don't match). 115 high-value items flagged for potential DB addition. DB table: `bb_gap_triage`. Report: `reports/bb_gap_triage.txt`. Script: `scripts/bb_gap_triage.py`.

**Follow-up actions completed (2026-03-19):**
- [x] **Import 93 high-value BB items** — `scripts/import_bb_items.py`: 76 nouns, 9 function words, 8 loanwords added to `lexical_entries` (4,273 → 4,366). New `source` column = 'blue_book'. Entry IDs: `BB-{slug}-{seq}`.
- [x] **p2/p71 deduplication (2026-03-20)** — `scripts/dedup_entries.py`: 22 p2/p71 duplicate pairs removed (p2 kept for higher-quality IPA), kusisaar parser artifact merged (4,366 → 4,343). hiksukac (VD/VP) and racawaktaarik (VI/VT) preserved as polysemy. Examples migrated before deletion. Backup: `~/.pari_pakuru_backups/`.
- [x] **Function word inventory seeded** — `scripts/function_word_inventory.py`: 414 items in `function_words` table (355 Parks + 2 BB direct + 57 Gemini-extracted from phrases).
- [x] **Inflected verb reverse-lookup** (Opus analysis): 82% of 141 BB inflected verb gaps trace to existing Parks dictionary roots. Gap is morphological, not lexical. Top roots: `at` 'go', `aar` 'do', `kuutik` 'kill', `irik` 'see', `huras` 'find', `kawaahc` 'eat'. Validates that conjugation engine work is the right investment.
- [ ] Prune ~5-6 OCR artifacts from Gemini function word extraction
- [ ] Review 40 descriptor items for potential DB addition
- [ ] Review 15 possessed forms for integration with possession engine
- [x] **E2S→S2E linking backfill (2026-03-21)** — `english_index.entry_id` populated from `english_to_skiri_linked.json`: 5,129/8,067 linked (63.6%). Match types: 4,723 exact_unique, 398 gloss_disambiguated, 8 first_homonym_fallback. 2,938 unlinked are genuine gaps (multi-word phrases, cross-references, parsing artifacts). 3 orphaned links from dedup (p71 kaaʔa, kusisaar -2018) skipped. Enables SQL joins from English words to full S2E entries for search, export, and AI verification.
- [ ] Resolve remaining 2,938 unlinked E2S entries (most are parsing artifacts, some may be real terms)
- [ ] Review 8 low-confidence homonym matches from linking
- [ ] Version control: track changes to entries over time
- [ ] Document Blue Book orthography differences (practical vs. linguistic spelling conventions)
- [ ] Cognate linking: build out Arikara, Kitsai, Wichita, South Band comparative data
- [ ] Audio pronunciation layer (if recordings become available)

---

## Design Principles for Endangered Language Preservation

These principles guide all user-facing features:

1. **Every attested form is precious** — surface all attestations (dictionary + Blue Book + Parks examples) for any query, not just one "correct" answer
2. **Show morphological breakdowns** — learners can't ask native speakers, so the tool must explain *why* a form looks the way it does (prefix + stem + suffix with labels)
3. **Export everything** — PDF wordlists, Anki decks, printable paradigm tables. Digital tools disappear; offline materials persist. **This is underbuilt relative to its importance** — see Phase 5.2 elevated priority.
4. **Record uncertainty with granularity** — mark generated (unattested) forms distinctly from documented ones. Learners must know what's verified vs. computed. **Go beyond binary**: use confidence tiers (high/medium/low) so learners know *how* uncertain a computed form is (see Phase 4.3).
5. **Privilege primary sources** — Parks Dictionary and Blue Book are the authorities; computed forms are supplements, never replacements
6. **Community governance over correctness** *(NEW)* — the tool should never be the sole authority on what counts as correct Skiri. Provide mechanisms for knowledgeable community members to flag errors, confirm forms, and contribute corrections. Human review gates all feedback before it enters the system (see Phase 4.4).
7. **Accent is not optional** *(NEW)* — pitch/accent placement in Skiri is phonemic (changes meaning). Any generated form without correct accent marks is unreliable for speech. Treat accent assignment as a learner-safety issue, not a cosmetic improvement (see Phase 3.1 accent task). *Correction, 2026-11-13: the claim that accent is phonemic is not supported by the source. Parks writes "Stress is not phonemic in Skiri and hence is not marked on words. (Phonetic forms in entries do, however, have accented syllables marked.)" (Sounds and Alphabet, p. 15). The marks are part of his IPA and must be preserved and shown for that reason; calling them "pitch" that changes meaning is not his description. See open item 9.*
8. **Build for the classroom first** *(NEW)* — the primary users are teachers and students in community language classes. Prioritize features that serve that context: printable materials, lesson-aligned content, Word of the Day, simple UI that works on low-bandwidth connections. Self-directed online learners are an important secondary audience.
9. **Never invent a Pawnee form; never generate IPA** *(2026-09-01, 2026-11-12)* — every form in learner material is looked up from a source record. Parks's IPA marks vowel reduction and pitch that cannot be predicted from spelling, so it is shown only where he prints it for that exact word. A derived form is always labelled as derived.
10. **Ceremonial vocabulary waits for the community** *(2026-10-01)* — words to do with bundles, dances and doctoring are flagged and kept out of new learner material until the Pawnee Nation has reviewed them. That is a decision about protocol, not about data.
11. **Same spelling is not the same word** *(2026-03-20, 2026-11-12)* — two entries, or two word-pieces, with one shape are merged only when meaning, class and forms agree, and the decision is recorded as data so that it can be undone.

---

## Scripts Reference

The list of scripts, in pipeline order and with the status of each, is
[scripts/README.md](scripts/README.md). It replaced the table that used to be
here, so that there is one list to keep current.

## Environment

- Windows 11; the shell is Git Bash or PowerShell. Python virtual environment at `.venv/` (`.venv/Scripts/python`).
- The console uses code page 1252. A script should write Pawnee text through `sys.stdout.buffer`, or be run with `PYTHONIOENCODING=utf-8`, and should open files with `encoding="utf-8"`.
- AI extraction steps use the Gemini API (`GEMINI_API_KEY`, model `gemini-2.5-flash`) through the `google.genai` package. The two original page parsers still use the older `google.generativeai`.
- The database is not in git. Backups: `OneDrive/pari_pakuru_backups/` and `~/.pari_pakuru_backups/`.
- Published: the static site only, on GitHub Pages from `docs/`. The Flask app runs locally. The PythonAnywhere hosting was retired on 2026-11-13 and `wsgi.py` removed. See `DEPLOYMENT.md`.

---

## Open items

*As of 2026-11-14. Within each group, most important first. Items that are done keep their number, so that older notes still point to the right place.*

### Needs a person, not code

1. **Speaker or linguist review of the word-construction analysis.** `curriculum/roots_v2/review_queue.md`; the ten main questions are at the top of `curriculum/roots_v2/validation_report.md` (vowel-length pairs, affixes labelled by default, the three preverb shapes, 274 shapes with several meanings, 192 pieces with no known meaning).
2. **Community review of ceremonial vocabulary.** Flashcard Week 20 is held back until it has been done (`curriculum/held_for_review.json`). In the word-construction analysis 176 words are flagged, by keyword only.
3. **A person has not reviewed the 387-word flashcard list** (audit item B5). Its membership was decided by English keywords.
4. **Lesson vocabulary:** 4 judgement calls and 8 homonym ambiguities were left unlinked (`reports/bb_vocab_linking.txt`).
5. **Feedback queue:** two flags are pending in `/admin/feedback`.

### The IPA

6. *(Done 2026-11-13.)* **The stored IPA uses Parks's own symbols**: ə́ and ɪ́ for the accented short a and i, `·` between syllables, `–` at the edge of a bound form. Set for every entry from the text layer with the verified table (`scripts/restore_parks_ipa.py`).
7. *(Done 2026-11-13.)* Every Parks IPA form has been matched to its printed form and set from it; 75 were corrected in content.
8. **The grave accent.** Parks's phonetic font has a regular system: à ì ù on the second half of a long vowel, ə̀ ɪ̀ ʊ̀ on a short one. Ten entries have one, stored as printed since 2026-11-13. His front matter does not say what it marks. *(Chapters 2 and 5 were read on 2026-11-14: neither mentions it.)*
9. *(Changed 2026-11-14 to "accent", Parks's own word, everywhere a reader sees it; the sentences saying that pitch changes meaning were removed. The project owner confirmed the word the same day.)* **What to call the marks.** Parks says stress is not phonemic and that phonetic forms mark accented syllables (p. 15). Whether "accent" is the right word for learners is for someone who knows the language; changing it is one pass over `web/templates/` and the two `format_pitch` filters. The style names `pitch-high` and `pitch-unmarked` still say "pitch".
10. *(Done 2026-11-13: 162 stored cognates and etymologies corrected. `ó` is š, `Ý` is é, `í` is ó, `Ó` is ą, `Ô` is ą́, `è` is į, `ü` is ž, `š` is a raised i; the `?` in Kiowa, Ponca and Arapaho words is printed as a question mark.)* About 20 cognate forms still differ from the page in a letter or a hyphen (item 41).
11. *(Done 2026-11-13.)* Every Parks entry has its printed IPA; the nine that had none were added from the page.
12. 32 respellings of *-ʔa* stems where Parks's IPA lacks the glottal stop (`reports/fix_pronunciations_report.txt`). *(The bullet shown in the IPA of bound forms was the working notation for Parks's dash; the dash is stored and shown since 2026-11-13.)*

### Generated forms

13. *(Done 2026-11-14, Stage 4, decision 7: the possession engine is withdrawn and noun pages show a lookup of printed forms, `scripts/printed_noun_forms.py`; `possession_examples` and `noun_stems` are dropped. What follows is the measurement that led to it.)* *(Measured 2026-11-14, engines review. Asked the way the app asks, 1,671 of the 1,706 nouns are answered with* kti ratiru X*, marked "attested";* kti *is an OCR slip for the Blue Book's* kú*. Its locatives and instrumentals equal the form Parks prints for 300 of the 675 he prints as examples under nouns (44%). 28 common nouns are taken for tribes and the real tribes are missed. The tables `possession_examples` and `noun_stems` are the engine's own output; the first still holds the misread* asaas*,* atipaat*,* apaat*. Decision 7 of the paper: replace the box by a lookup of printed forms.)* **The possession engine offers forms it should not.** Through the API it builds an instrumental ("with, using …") for every noun, animals included, because its animacy filter needs topic tags that the API does not pass. Its stem stripper removes `-kis` wherever it finds it, so *rakis* 'wood' becomes the stem *ra*. *(It also removed a final* -kiʔ*, a rule built on two words the grammar chapter does not print; that rule was taken out on 2026-11-14.)* For stems ending in r the dictionary shows two outcomes with *-hiriʔ* and the engine picks one (marked "medium"). These forms are shown as computed, but several are plainly wrong.
14. **Bare pieces on the weekly flashcards** are places where two readings of Parks's etymology disagree, for example the first piece of *askuhuukita* 'eleven' and both pieces of *Ickariʔ*. Each is a small question for a person.

### Data

15. *(Done 2026-11-14: `scripts/fix_page_citations.py`; every Parks entry cites the page of the book.)* *(Done 2026-11-14 with item 32: `english_index.page_number` and `cross_references.source_page` are book pages, 63 to 346; the printed page number was read from all 284 pages.)*
16. *(Done 2026-11-14: the 21 derived stems under ten bound stems are in `derived_stems`, each checked against the printed entry; the local entry page and the public site show them.)*
17. *(2026-11 audit: `(1), (1)` is faithful: the page prints* VT(1), VR(1)*. `(pl. subj.)` is printed after the class and was stored in the class column. Nine kin terms are stored as N-KIN where the page prints N: the project's own reclassification, recorded in `fix_audit_issues.py`.)* **Verb-class values that are not verb classes**: `(pl. subj.)` once and doubled values such as `(1), (1)` on four entries; `(3-i)` once, which may be genuine. The grammatical-class column has 41 distinct strings, some of them one class written two ways (`VI, VT` and `VT, VI`).
18. *(Done 2026-11-14 for the Parks entries: 496 values.)* A space before punctuation in glosses and examples ("animals .", "cloth ;"), left by the parse.
19. Letter-spaced text remains in the raw copies of the parsed entries (`raw_entry_json`, `raw_subentry_json`), which are deliberately not edited.
20. *(Done 2026-11-14: the line-break hyphens, in 67 examples and 617 other values; see the phase entry.)* From the 2026-09-01 audit: rare truncated gloss qualifiers (two were found and completed); a few verb forms where the AI reading and the PDF text layer differ (none is left).
21. From the 2026-10-01 audit: the 93 Blue Book-only entries have no learner spelling and are not labelled as Blue Book spelling (B3); "word of the day" fixed at build time (C3); a join on bare headword in the greetings category (C5). *(Done 2026-11-14: a bare `Ø` headword is shown with its preverb in search (C1); `search.js` is loaded once (C4).)*
22. *(Done 2026-11-14.)* Of the 7,806 rows of the English index, 5,165 hold a Skiri term and 5,162 of those are linked to their dictionary entry; the other 2,641 rows are English headwords that only refer to another headword. Three terms fit two dictionary entries equally and are left unlinked: *a* 'and' (p. 67), *ica-* (p. 142), *wakaʔu* (p. 267).
23. *(Done 2026-11-13: the audit compared all of it, and the Blue Book forms were then read from the scan as well.)* Everything extracted by AI from page images has been compared with the pages: Appendix 1, Appendices 2 and 3, the abbreviation list, the grammar chapter and the Blue Book vocabulary.

### Engines and features

24. *(Decided and done 2026-11-14, decision 5: the predictor stays as a checker for the word-construction analysis; the badge and the stored score are removed.)* Form 2 prediction: 241 of 2,197 verbs missed and 41 more off by a glottal stop (`si-` and `ruuti-` prefixes, internal vowel shortening, multi-word headwords). *(Engines review, 2026-11-14: the 87.2% is on the forms the rules were read from, and no other source prints a form 2, so it cannot be tested on unseen forms. 135 of its 289 misses are vowel length or the glottal stop. The stored `form2_confidence` is "High" for 98% of verbs, 253 of them predicted wrongly, and 1,863 of the 2,239 stored values no longer equal what the code gives. Decision 5: keep the predictor as a checker, remove the badge and empty the score.)*
25. *(Closed 2026-11-14, decision 2: the conjugation engine is withdrawn to `archived/scripts/`.)* Conjugation of Appendix 1: 22 mismatches and 137 near misses in 770 forms, against the appendix as corrected from the page (item 39). *(Sorted by cause on 2026-11-14: of the 159 forms that differ, 63 differ in an accent, 58 in vowel length or a glottal stop, 38 in other letters.)*
26. *(Repaired 2026-11-14, decision 6: the three rules are out, no first person is invented, the builder passes the entry and labels derived forms. On 1,059 verbs set aside beforehand the "he/she" question form starts as form 4 starts for 794 of the 816 forms given, 97.3%. See item 63 for the one weak rule left.)* *(Engines review, 2026-11-14. Its question form for "he/she" was tested on 2,124 verbs it was never fitted to, against the start of the dictionary's own form 4: 1,503 agree. The rules read from correctly read forms agree for 1,474 of 1,516 verbs (97%); the three built on misread forms,* tii- → rii-*,* tuu- → ru-*,* tih- → riih-*, for 29 of 465 (6%). It makes a first person in* tiku- *for 184 descriptive verbs that Parks gives none for, after a passive verb. The sentence builder passes a verb by its spelling, and 211 verbs share a spelling. Decision 6: repair narrowly, do not extend.)* Person derivation (3.2b): plural persons, negative mode, imperfective coverage, question-particle placement. Two of the 27 checked forms differ from Appendix 1 as corrected: *ruhii* for printed *ruuhii* ('to be good', 3rd singular absolutive) and *riihkiraawaʔ* for *rihkiraawaʔ* ('to be sick').
27. *(Done 2026-11-14: `scripts/build_printables.py` writes `curriculum/printables/`: the flashcard words as a list, and Parks's Appendix 1 in full.)* *(Linked 2026-11-14, sixth part: both PDFs are copied to `docs/printables/` by the static build and linked from "Start here" and the Verbs page; pushed in `cbeb592`.)*
28. *(Done 2026-11-14: `scripts/bluebook_glossary.py`, `extracted_data/blue_book_glossary.json`.)* The glossary is an English index with page numbers and prints no Pawnee: 573 rows, 644 page references. 589 are confirmed by the page they point to; for 55 the English term is not in the text of that page (another wording in the lesson, or a weak text layer on pages 55, 60 and 92), and one row has no number in the text layer.
29. *(Done 2026-11-13: `DB/dump/` and `scripts/db_dump.py`.)* **The database is not under version control and cannot be rebuilt by one command.** A text dump in git, or a build script that replays every step, would make each future fix a reviewable difference.

### From the source-fidelity audit (2026-11-13)

30. *(Done 2026-11-13 for the fixes with solid evidence: 807 applied; the 1,090 English-index differences were overtaken on 2026-11-14 by rebuilding the index from the page, item 32.)* What remains of `proposed_fixes.jsonl`: the judgement calls of items 41 and 45.
31. *(Done 2026-11-13; table in the phase entry.)* Conjugation 79.4% (was 90.3%), form 2 prediction 87.2%, person derivation 25 of 27, sound-change tests 11 of 11.
32. *(Done 2026-11-14: `scripts/repair_english_index.py`; see the phase entry.)* The file and both tables were rebuilt from the printed page. What is left: three terms without a link (item 22), and the parts of a subentry the rebuild does not touch (glosses, etymology, verb forms and examples inside `english_to_skiri_linked.json` are the first reading's copy). `python scripts/repair_english_index.py --check` exits 0 while the file and the tables say what the page says.
33. *(Decided and done 2026-11-13: Parks's notation is stored.)* What is left of this is item 43.
34. *(Done 2026-11-14: `scripts/complete_from_print.py`.)* The printed stretches the database lacked: 18 examples, the 21 derived stems, qualifiers, the second half of four etymologies. Seven stretches are still listed by the comparison although their text is stored (item 41).
35. *(Done in part 2026-11-14: `scripts/bluebook_only_entries.py`.)* **Blue Book headwords.** The 93 Blue Book-only entries carry headwords respelled into Parks's letters (*paisic* for printed *paisits*). The printed form is now on record for 87 of them and the public site shows it beside the headword; for six none is found (*ic*, *pareʔkuʔ*, *piraski*, *rariksisuʔ*, *rikisuʔ*, *riksuʔ*; four of these are stubs without a gloss). The headwords themselves are unchanged: see item 52.
36. *(Done 2026-11-13: 715 forms corrected from the scan, the three entries first.)* 77 forms are left (item 42).
37. *(Done 2026-11-14: read twice; `extracted_data/sounds_and_alphabet.json` and `organization_of_the_dictionary.json`; see the phase entry.)* **Chapters 2 and 5 of the front matter.**
38. *(Done 2026-11-13: corrected for the 393 entries from the page geometry.)* Nothing uses `column_position`.

### After the fixes (2026-11-13)

39. *(Closed 2026-11-14, decision 2: withdrawn.)* **The conjugation engine gets 611 of 770 forms of Appendix 1 (79.4%), not 90.3%.** Its rules were tuned against a copy with 152 misread forms. `scripts/morpheme_inventory.py --validate` lists the 159 that differ. Whether to take this work up again is a decision for the project; until someone makes it, the rule not to retry from-scratch conjugation stands. *(Engines review, 2026-11-14: on the dictionary's 9,559 verb forms, which it was not fitted to, the engine gets 1,431 (15.0%); 41 of 2,239 verbs have every printed form right. By its own count 14.8%, the figure of 2026-03-09: the fitting that followed moved Appendix 1 and not the dictionary. No page of the app calls the engine. Decision 2: withdraw it.)*
40. *(Closed 2026-11-14, decision 2: withdrawn with the conjugation engine.)* **`scripts/accent_rules.py` was worked out from the accents of the misread Appendix 1**, many of which the page does not have. Only the conjugation engine uses it. It should be checked against the corrected appendix or withdrawn. *(Checked 2026-11-14: the page marks an accent in 26 cells of Appendix 1, the engine in 81, in 57 of them where the page has none. The file's own check gives 0 of 26. Without the rules the engine would have 637 forms right instead of 611. Decision 2: withdraw.)*
41. **37 differences between the dictionary entries and the page are left** (`reports/source_audit_2026-11/after_fixes/s2e_differences.jsonl`; 218 before 2026-11-14). Each has its reason in `print_completion_report.txt`: 13 grammatical classes, nine of them the project's own N-KIN (item 17); seven stretches the comparison cannot place although the text is stored; ten places where the page breaks a line after a slash, inside a cited word or at a hyphen that belongs to the word; and seven values where the page itself is in doubt or the stored value rearranges a qualifier. None is a phonetic form or a verb form.
42. **17 Blue Book forms that three readings could not settle** (the last section of `reports/source_audit_2026-11/bluebook_applied_report.txt`; 77 after the first reading, 42 after the second, 17 after the forms were read at their own place on 2026-11-14). In eight a reader could not tell whether a raised dot or a faint mark is printed (*ti•rá?wa•rar•uhat*, *sakúru'*), or the print is damaged (*Kitské ?e ru'?*); four are words that begin a sentence on the page and are stored in another form (*paresu*, *kitu*, *tatitska*); the rest are fragments (*wa +*, *its*, *ta*) whose place cannot be told. More readings will not help; a person with the book can settle each at a glance. The forms written into the sentence templates (`scripts/sentence_templates.py`) still lack the printed accents; the other tables are corrected. *(Engines review, 2026-11-14: three of the words the templates offer are OCR slips given meanings of their own,* ilan'*,* kirti*,* stiks *for printed* Háu'*,* Kirú*,* Súks*; and since the table has the printed accents the engine recognises none of the 385 Blue Book sentences printed with one. Decision 8.)*
43. **Tense and lax short vowels in the respelling.** Parks writes [i], [u] in some places and [ɪ], [ʊ] in others; the respelling writes `ih` and `oo` for both (589 entries, counted by `scripts/check_simplified_forms.py`). Whether learners should see the difference is a teaching decision for someone who knows the language.
44. *(Closed 2026-11-13: the PythonAnywhere hosting is no longer in use and was taken out of the repository.)* If the account still exists, its web app should be disabled there: unless someone updated it by hand, it holds the data from before the corrections and would still serve flashcard Week 20.
45. **Left for a person with the page:** the singular cell of *tir* 'to be together' in Appendix 2, empty in print and stored as `tir` *(no engine reads Appendix 2; the note that the conjugation engine reads this cell was wrong: engines review, 2026-11-14)*; *rihkuupa´kstarit* in an example of *apak*, a printing oddity; the values listed as left in `print_completion_report.txt`. *(Settled 2026-11-14: the three "verb forms" of* itkaakahaaruʔ *are not printed and were removed; the combining form is* `takasistik [+ raar-]`*; the grammar chapter was read a second time and all its Skiri words are settled, see the phase entry.)*
46. **An older respelling function is still in the code.** `generate_simplified_pronunciation` in `scripts/respell_and_normalize.py` returns `? ?` for a phonetic form of several words. Stored respellings are made by `scripts/fix_pronunciations.py`, which handles them; the older function should be retired.

### The public site, now the only publication (2026-11-13)

47. *(Done 2026-11-14: the About page was written again for the site as it is.)* Its wording is the project's and has not been read by anyone from the community (rank 1).
48. *(Done 2026-11-14: the verb forms, other forms, etymology, cited forms and derived stems are in `docs/data/dictionary.json` and behind "More from this entry".)* *(2026-11-14, sixth part: the topic tags are shown, as links on a search result and as the Topics page; "ceremony" is not offered as a topic.)* The cross-references are as printed since 2026-11-14 (item 32) and could now be shown; they are not yet.
49. *(Done 2026-11-14: "Send a correction" on every search result and on the About page opens a GitHub issue with the entry filled in.)* It needs a GitHub account; there is no other route.
50. *(Confirmed by the project owner on 2026-11-14 as the arrangement until the community review.)* **The 143 entries tagged `ceremony` show less than the others on the public site.** They are searchable and show senses and examples, as before; the verb forms, etymology and cited forms added on 2026-11-14 are held back for them, and the result says so. The tag was given by keyword, so the list is rough both ways. Whether these entries are shown at all, and how fully, belongs to the community review (rank 1). The switch is in `export_dictionary_data`, `scripts/build_static_site.py`.
51. *(Done 2026-11-14 for 12 of 14 tables: `scripts/source_audit/chapter4_tables.py` put them together from the two blind readings into `extracted_data/grammatical_overview_tables.json`. Six read the same in both readings row for row; six have the same text in every column, with rows divided differently by the two readers; tables 6 and 7, two diagrams of positions across the page, are stored in both readings for a person to settle. The older copies inside `grammatical_overview.json` are left as they were.)* **The tables of the grammar chapter are stored as the March 2026 extraction rebuilt them, not as printed.** Table 17 was put back as printed on 2026-11-14 after it turned out to have merged cells and lost the length mark of *-:hus*. The other tables were compared with the two blind readings word by word, which finds a wrong word but not a cell in the wrong row. The `morphemes_mentioned` lists in the same file are summaries the extraction wrote, not Parks's text. The two blind readings (`reports/source_audit_2026-11/blind_readings/chapter4_part*.json` and `chapter4_second_part*.json`) hold every form and table of the chapter twice and agree on every Skiri word, so the tables as printed can be put together from them without another reading. No code reads the stored tables.

52. **37 of the 93 "Blue Book-only" entries are words Parks has.** The textbook does not write vowel length, so its *tsuraki* 'girl' is the dictionary's *cuuraki*, its *pa* 'moon' is *paa*, its *raku'* 'box' is *raakuʔ*. `scripts/bluebook_only_entries.py` finds a dictionary entry when the letters agree with long vowels written short and the meanings share a word (33 entries; four more carried one from March 2026), and writes it into `bb_variant_of`. More are likely: the textbook writes *e* where Parks writes *ii* (*resáru'* beside *riisaaruʔ* 'chief'; chapter 2 calls *e* a South Band sound), and the rule does not follow that. Nothing was merged. These entries are in flashcard weeks 1 to 3 with a respelling made from the textbook's spelling, so a learner is shown a short vowel where the dictionary has a long one. Whether to teach the dictionary's form, and what to call the entries, is a decision about the frozen list (rank 3).
53. **What chapter 2 says and the site does not.** The dictionary writes *kt* after one speaker, and Parks adds that all other twentieth-century Skiri speakers said *tt* (p. 16); *r* is often said as *n* at the start of a word, *c* is [ts] before a consonant and at the end of a word and [č] before a vowel (pp. 13-14). The pronunciation guide mentions none of this. The question which to teach is in the review packet (Part 5c). *(2026-11-14, sixth part: the Sounds page now gives what the chapter says of* c *and* r*, of the tense and lax short vowels and of the glottal stop, with the chapter's own examples. It still says nothing of* kt *and* tt*: that waits for the review.)*
54. **The dictionary's chapters are stored without their running text**, on purpose. When chapters 2 and 5 were read on 2026-11-14, one reader was stopped by the service's content filter while writing the text out in full, and two reported an automated notice about not reproducing sections of books. The book is in copyright and the project needs what the chapters establish, not their sentences: the stored files hold the Skiri forms, the tables, the headings, a summary of each section in the project's own words, and a few sentences of Parks quoted with their page. The full readings are in `reports/source_audit_2026-11/work/front_matter/`, which is not in git. The PDFs of the book are in the repository; whether they should be in a public one is the owner's question, and has been since the project began.

### From the engines review (2026-11-14)

55. *(Done 2026-11-14, decision 1, 214 places and 12 titles; the count of 65 below was an undercount. Pushed the same day (`bf1f4e0`). What is left is item 60.)* **OCR slips on the public lesson pages.** The audit corrected 104 readings in the Blue Book table as OCR slips. 65 of the old readings still stand in the running text of the `lessons` table (62 times in grammar notes, 4 in dialogue lines) and so on 14 of the 20 lesson pages of the public site: *Stiks .atku!* for *Súks•atku!*, *KIRIKJ RA•TARAWIS?* for *KIRIKÉ RA•TARAWIS?*, *kti•ratiru paks-ktiku'* for *kú•ratir•u paks•kúku'*. The corrections were applied only where a whole stored line equalled the old form. The list is in `reports/engines_review/data/use_summary.json` under `3_lessons`. Decision 1 of the paper; it is the only finding of the review that is in front of learners.
56. *(Done 2026-11-14 with decision 7: an entry's own examples are no longer filtered.)* **The local app hides most of Parks's example sentences.** The entry page keeps an example only when the headword begins a word of it, a test written to keep *kirike* off the page of *kiri* among Blue Book sentences. Applied to the dictionary's own examples it shows 428 of 2,652; 1,340 of the 1,658 entries with examples show none. Among the hidden ones are 675 locative and instrumental forms Parks prints under nouns. The public site shows all examples.
57. *(Done 2026-11-14 for the four in `function_words` and for* swat*: deleted. `bb_function_words` and the rest of `function_words` are item 62.)* **Four non-words in `function_words`**, each marked as attested in the Blue Book: *ilanʔ*, *kirti*, *stiks*, and *kti* glossed "your". All four are OCR readings of an accented *ú* or *á*. `bb_function_words` has *Kirti* and *Ilanʔ* beside source phrases that now read *Kirú …* and *Háu' …*. The table `kinship_paradigms` has *swat* 'your niece, nephew' for printed *awat*, with a note explaining the *s*.
58. **The gold file of Parks's worked examples** (`curriculum/roots_v2/gold/g1_go_examples.json`) pairs eight of its 93 examples wrongly: in six the word is another word of the same example (*aruusaʔ* 'horse' beside the pieces of a verb), in two a line with two analyses had the pieces of both joined. It should be made again and its hash recorded again. *(2026-11-14, Stage 4: the guide no longer shows a mis-paired record as an example; the file itself is unchanged.)*
59. *(Done 2026-11-14, decision 3: the guide prints Parks's Tables 6 to 17 from the file; the engine's table is dropped.)* **The word-building guide prints the conjugation engine's table as Parks's.** The section "The prefixes and endings Parks tabulates" of `curriculum/roots_v2/construction_guide.md` takes its first 37 rows from the table `morpheme_inventory`, which `morpheme_inventory.py --import-db` wrote from the engine's own constants in March. Six rows are not in Parks's tables (*kaaka-* for *kaakaa-*, *raak-* and *iraak-* for *rak-*, the suffixes *-u* and *-wi*), and `check_forms.py` accepts the table as a source. `extracted_data/grammatical_overview_tables.json` holds the tables as printed. Decision 3.
60. *(Done 2026-11-14, seventh part: every line of the lessons that holds Pawnee was read from the scan, 911 lines. Of the 196 places, 173 now agree with the audit's reading, at 10 the page has the form without the accent at that place, and 13 differed only in punctuation; all twenty titles are the title lines of the page. What the reading left is items 70 and 71. Committed and pushed, `fad4a3e`.)* **The lessons' running text: what the audit's readings could not settle.** 196 places differ from the audit's reading only by an accent or a capital and were left: the OCR dropped every accent, the audit read a form at one place, and the same letters may be printed elsewhere on the page without it (`python scripts/fix_lesson_text_ocr.py --check` counts them; the report lists them). Seven lesson titles have no reading of the title line in the Blue Book table: lessons 6 (none stored), 8 (*KI Rid RA. KU?*), 9, 10, 12, 17 and 18; 10 and 18 show *KIRIKI* where the four titles read from the scan have *KIRIKÉ*. Some OCR damage matches no reading at all (lesson 20 *tatitska ratkti u•ta*, lesson 13 *kit-kaharu '*). All of it needs the page: the seven title lines are a small reading, the notes of twenty lessons a large one.
61. *(Done 2026-11-14 by `scripts/relink_bluebook.py`, pushed in `fad4a3e`: 414 ties judged again, 65 re-tied, 349 untied; 257 of 1,026 rows are tied, each by its form; 43 of the 88 Blue Book example sentences stand under an entry one of their words is tied to, the other 45 were removed from `examples`. Left: a row with two forms, such as* kiri, pus *'cat', stays untied; the examples cite the page of the scan, not of the book.)* **The Blue Book table ties common words to the wrong dictionary entry.** *asáki* 'dog' and *arúsa* 'horse' are tied to the entry *a*, *tsapat* 'woman' to *ca*, *pita* 'man' to *pitaksuʔ*, by a shared beginning (`match_type` "prefix", from phase 2.2). Of the single words in the lessons' word lists, 77 are tied that way to a locative verb and 99 to nothing. The entry page of *a* lists them as its Blue Book attestations, and `blue_book_attested` is set on that basis. The lookup of printed noun forms and the sentence builder use only ties by the exact form. The ties should be made again from the forms as read from the scan.
62. *(Done 2026-11-14 by `scripts/fix_function_words.py`, pushed in `fad4a3e`: 32 rows corrected and 9 deleted; every Blue Book row of the two tables is now a word, or a bulleted part of a word, of the scan's readings. Their meanings are item 72.)* **`function_words` and `bb_function_words` are still OCR text.** Of the 59 rows of `function_words` that came from Blue Book phrases, 32 are whole words of the scan's readings, 18 are parts of words (*.aʔ*, *suks*, *siks*), and 9 are found neither way (*pihkawf*, *rd*, *wfs*, *sihukstarti*, *niru*, *hti*, *cararat*, *ʔhr*, *rahesa*). `bb_function_words` still has *Kirti* and *Ilanʔ* beside phrases that read *Kirú …* and *Háu' …*. No page shows these rows to a learner. Both tables should be made again from `blue_book_attestations`.
63. *(Decided 2026-11-14 by the owner: no action; the rule stays in force.)* **One weak rule in person derivation.** *tiʔ-* → *raʔ-* agreed with the dictionary's form 4 for 25 of 29 verbs on the open half and 12 of 19 on the sealed half. It was left in force because the configuration to ship was fixed before the sealed half was opened. Part of its misses may be the test's: Appendix 1 prints the question form *raʔat* beside a form 4 in *raa-* for 'to go'. Switching it off is one word in `THIRD_PERSON_RULES` of `scripts/person_forms.py`; 48 verbs would then get no form. The owner's call.
64. **The Blue Book filter on entry pages does not set accents aside.** It keeps 54 of the 262 Blue Book sentences tied to an entry. Since the audit restored the printed accents, a sentence that holds the headword with an accent may be hidden. Not measured further.

### From the learner pages (2026-11-14, sixth part)

65. **The plain English of the learner pages is the project's, and nobody who knows the language has read it.** The comparisons with English sounds under "Say it, syllable by syllable" (`SOUNDS` in `web/static/js/skiri.js`), the one-line meanings of the five verb forms (`FORM_PLAIN` in `web/learning.py`), the names of the eleven persons, the six steps of "Start here" and the sentences that introduce each page. The review packet was built before these pages existed and does not show them; they belong with rank 1.
66. **The Word building page does not say what a piece means.** It shows the pieces Parks prints and his literal translation of the whole word, and lists the dictionary entries spelled like a piece without choosing among them (*raar* is spelled like three entries). Pairing a piece with a meaning is what the project's own analysis does (`curriculum/roots_v2`), and that waits for item 1. If the review releases it, the page is where its reviewed pairings would go.
67. **There is no sound on the site.** A learner cannot hear a word; the Sounds page and every syllable view say so. Recordings would have to come from speakers or from an archive with the right to publish them: a question for the Pawnee Nation, not for code.
68. **22 derivations are shown only as the printed line**, not piece by piece: a parenthesis spans a plus sign (*rak+taakaar(+uʔ)*, "white wood (+ NOM)") or an apostrophe stands for the glottal stop. Showing them as pieces would mean moving a printed sign; left as printed.

### From the reading of the lessons (2026-11-14, seventh part)

69. *(Done 2026-11-14 by `scripts/pair_lesson_dialogues.py`, pushed in `fad4a3e`: each Pawnee line took the English the page prints to its right on the same row, from the scan's text layer; merged lines were cut and continuation lines joined; the section of notes inside lesson 2's third dialogue became the first of that lesson's notes. 105 lines, 102 with their English, 3 printed without one. No page had to be read again and no Pawnee word changed, apart from two lines the page breaks, which were joined.)* **In the dialogues the English is not paired with the Pawnee.** In 83 of the 156 stored dialogue lines the Pawnee field holds an English sentence, or the English field is empty: the extraction took the two columns of the page as separate lines (lessons 9, 10, 11, 13 and 17 throughout; parts of 1, 2, 5, 7, 14, 15, 16, 18 and 20), and in lesson 2 it put a paragraph of the notes into a dialogue. The lesson pages show the lines as stored. The Pawnee lines themselves are right since the reading, so nothing has to be read again; each dialogue has to be looked at on its page to pair the lines: about twenty regions of pages, an estimated 40,000 tokens with the code.
70. **For a person with the Blue Book: six places in the lessons.** Three lie under a flaw in the scan and carry square brackets. Lesson 16, first dialogue (scan page 99, book page 71): *Kitské [w]e ru'?* and *We ti p[it]ku.*; the bracketed letters are those of the same sentences on the page before. Lesson 14, the South Band line under "Don't touch!" (scan page 93, book page 65): *Ka res•[..]sí•urúkat!*; about two letters, not filled in. Three are doubts of reading: whether a raised dot or nothing stands between *rá* and *wa* in *ti•rá wa•rar•uhat* and *hiri•rá wa•rar•uhat* (lesson 13, scan page 89, book page 61; three readers could not tell, and the OCR's space is stored); *tuh•rá'*, the last line of the breakdown on scan page 75 (book page 47), where one reader sees an accent in three looks and the audit had read the dialogue line above instead; and a small stroke over the U of the title *TÍRUKS•TSAK•ARIKI* (lesson 17), which may be a speck. The same six stand in the Blue Book table.
71. **The English of the lessons' notes is OCR text nobody has proofread.** Only the Pawnee was read on 2026-11-14. The prose has the OCR's slips, the hyphens of line breaks and none of the book's italics, and the breakdown lines keep the OCR's spacing around the plus signs.
72. **The function-word tables: meanings and word classes were never checked.** `fix_function_words.py` set the words to the scan's readings; the English and the class of a row are what the extraction gave (*pirau* is glossed 'when'). `bb_gap_triage` is corrected only in the 13 rows that are lines of a lesson.

### From the phrases and the pairing (2026-11-15)

73. **Ten word-list rows could not be checked against their row of the page**, because the scan's text layer garbles the form: *ti'* (lesson 1), *haas* and *awat* (7), *hu'* (11), *kit-kaharu'* (13), *tatut•á•wahri•úsuku'* (15), *we ta sák•ta* (16), *tsiksu tatut•á•wahri'* (18), *tat•katá•hak'sta* (19), and the phrase *Nawa rúru!* (7, which the lessons' text pairs soundly). The rows of grammar examples and dialogues were surveyed once and not corrected: 324 of 376 the same, 23 that differ and looked like layout. One of those is worth a look: *tiraku'* in lesson 10 is stored as 'rifle' and the page has 'gun' beside it. `python scripts/fix_bluebook_pairing.py --survey` lists what differs.
74. **The book's line over a lesson's Additional Words is not stored.** Eleven lessons say what the words are for: "Nouns to substitute for *rakis* in the dialogues." (lesson 2), "Body parts to replace "head" and "eye" in the dialogues." (5), and so on. It is how the book makes the dialogue the centre of a lesson. To show the lines, their Pawnee words have to be read at their own place on the page (about a dozen lines, one small sheet) and the lines need a place in the `lessons` table.
75. **The word added to lesson 9 stands last in its list.** *ti•ká•isat* 'he went home' is printed between *ti•káisat* and *ti•hú•isat*; a lesson's words are shown in the order of their row numbers, and a new row gets the highest. Putting it in its place needs an order column in `blue_book_attestations`.
76. **The Blue Book-only entry *tikuwutikuʔ* 'he is killing it' is a form of a verb Parks has**, with no class since its gloss was corrected. It belongs with the decision about the 93 Blue Book-only entries (item 52). The word the entry was meant to be, 'judge' (*asku•ra•wákahu'*), has no entry.

### From the register of sources and the two dialects (2026-11-15, second part)

77. **Permission for the two books has not been asked.** The textbook: "Copyright © 1979 by the Pawnee Indian Tribal Business Council … No part of this book may be reproduced … without permission in writing from the Pawnee Tribal Business Council." The dictionary: University of Nebraska Press, 2008. The site shows the content of both, and the public repository holds page scans of both (634 PDFs under `Dictionary Data/` and `pari pakuru/`). Three letters are drafted in `community_review/letters/`. The owner's decision of 2026-11-15: ask, and change nothing meanwhile. For the owner; nothing here is legal advice.
78. **Two sources of the register did not answer**: the Pawnee Nation's archive portal (`mukurtu.pawneenation.org` did not resolve from this computer; a search engine lists it) and the Pawnee Nation College. Try again (`python scripts/sources_catalogue.py --check-links --only nation_mukurtu,nation_college`); the portal belongs on "Learn with others" once it answers and has been read. Fifteen more turn automated clients away and were not read.
79. **The Skiri form of a textbook line is not in the two books.** "SB spelling" says how a form is written; the page does not respell it. The Nation's Lesson 1 gives Skiri beside South Band for a few of the same phrases (it writes *Kirikî* or *Kikî* where the textbook's contents page gives *KÍRIKU* as the Skidi form: two sources that differ, to be shown side by side when both may be shown). Copying its forms waits for the Nation's word (letter 1, packet 6c).
80. **Where the textbook gives a word in both dialects, the table often holds only one.** The first extraction marked 12 rows "both" and kept one form: lesson 1 has *haú'* (SK) and not *ahu'* (SB) from the same list; lesson 18 has *tsaskít* (SK) and not the South Band form printed beside it. The partner forms are on the page and can be added, each read at its own line.
81. **"Hear it" is a search.** Eight of ten words taken at random were found; *paktiku* and *haskiicuʔ* were not, under any spelling tried. An exact link needs the university's entry numbers (`key=skiri000837`), and gathering those is bulk use of their site: letter 2 asks. Their dictionary may also differ from the printed one in places; comparing the two is Stage 6 of the plan and waits for the same answer.
82. **The textbook's own chapter on reading and writing is not on the site** ("Reading and Writing Pari Pakuru'", "The Pawnee Alphabet", pp. xi to xxiv). Only its twelve statements on dialect were read. It is the textbook's first lesson in all but name; whether it goes on the site follows the answer to item 77.
83. **Later stages of the plan, each waiting for a written yes:** a link from each entry to its own entry and sound at Indiana University; the Nation's handouts as dialect-marked forms; the 1997 Skiri course, if the Nation's Education Department can supply it; the Skiri text collections (Roaming Scout, Parks) as examples and as forms no rule here was fitted to; the 1966 recordings at the American Philosophical Society.
84. **The twenty lesson pages differ at every build of the site.** The wrong answers offered in a lesson's exercises are drawn at random when the page is made (`web/app.py`, "fresh shuffle each page load": right for the app, where each visit should differ). In the static build it means that two builds of the same data are not the same files, so every commit of `docs/` shows all twenty lesson pages as changed and a real change in one of them is hard to see. Seen on 2026-11-15 by building twice; nothing else differed. A fixed seed for each lesson in `scripts/build_static_site.py` would settle it. Small; code.

### From the word web (2026-11-15, third part)

85. **The word web joins words by the letters of a piece.** That is what the dictionary's derivations give, and the page says so; but a picture claims kinship more loudly than a list does. Short pieces (*a* in 83 words, *ra* in 151, *at* in 104) gather words that may have nothing to do with one another, and one piece may stand under two spellings (*kaatiit* in 23 words, *katiit* in 20, both in words for black things). Telling pieces apart, or putting two spellings together, is analysis: it belongs to the project's word-construction work (`curriculum/roots_v2`), which waits for review (item 1). Until then the picture keeps to the print.
86. **A large picture is crowded.** Past about forty words the lines run under boxes, and on a phone the letters are small until the visitor makes the picture larger. Nothing lies on anything else, and each start is small; but a layout that bundles the lines, or a way to fold a family back into its oval, would help. Code; for later if the page is used.
87. **The word web has no sound and no accent.** A box shows the headword as the dictionary spells it, so that the piece can be seen inside the word; it does not show the learner spelling or the phonetic form. The panel under the picture links to the entry, which has both.
88. **Two books of ceremony lie in `docs/`, the published folder.** Found on 2026-11-15 while checking the working tree: `docs/Hako A Pawnee Ceremony.pdf` (Fletcher, *The Hako: A Pawnee Ceremony*, 388 pages, 35 MB) and `docs/SCtA-0027.1-Hi_res.pdf` (Murie, *Ceremonies of the Pawnee*, part 1, 189 pages, 77 MB), both put there that afternoon and not by this work. Anything committed under `docs/` is public on the site. The register of sources holds both back as ceremonial, and the approved plan lists both under "not brought in". Nothing was moved or deleted; a line in `.gitignore` (`/docs/*.pdf`) keeps them out of a commit. **Settled the same day:** the owner removed both from `docs/` ("pdf books removed from docs/"). The line in `.gitignore` stays, as a guard.

### From the spelling switch (2026-11-15, fourth part)

89. **The site no longer says which spelling to learn to write.** Until 2026-11-15 it said: the learner spelling, the large one. With the dictionary's spelling first, the line now only describes the two and says that the learner spelling is the alphabet of the Pawnee Nation's lesson handouts. A learner still needs an answer, and it is the Nation's teachers' to give. The first letter asks it since 2026-11-15 (its third point); the review packet does not (its part 5 asks about sounds): add the question there when the packet is next built. For the owner, then the reviewers.
90. **The learner spelling is this project's respelling of the dictionary's headword**, made by rule (`scripts/respell_and_normalize.py`; `scripts/check_simplified_forms.py` checks all 4,244). Its alphabet is the Nation's; whether each word comes out as a Pawnee writer would write it has not been checked by anyone. Now that it is the second spelling and not the first, a wrong one does less harm, but the question stands.
91. **A choice of spelling is kept in one browser.** It does not follow a learner to another device, and a browser that keeps nothing (a private window) shows the dictionary's spelling on every page again. That is the price of a site without a server.

---

## How to Use This Document

Start a working session by reading "Status at a glance", "What's next" and
"Open items". When an item of "What's next" is done, take it out of the
ranking and re-rank what is left; the ranking is a recommendation made on the
date it carries, not a plan anyone has agreed to.
Refer to a phase by its name ("Phase 6.2") or to an open item by its number.

When a phase is finished or a number changes, update this file in the same
change. It is only useful while it is true. Figures here were read from the
database and from the scripts' own output on the date given beside them; when
you quote one elsewhere, run the command again.

The ground rules for all work here are the Design Principles above, and the
rules section of `prompts/skiri_word_construction_v2.md`.
