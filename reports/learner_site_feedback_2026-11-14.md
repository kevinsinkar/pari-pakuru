# The learner pages: feedback from the session that read the lessons

2026-11-14. Written at the owner's request by the session that corrected the
lessons from the scan, for the session that built the learner pages and for
the owner. It is one reader's opinion, to be weighed, not a list of tasks.
I read the pages as built in `docs/` that evening (Start here, Sounds, Word
building, Verbs, Practice, Topics, a lesson page, a search result) and the
practice code. I did not click through every game.

Every suggestion below keeps the site's rule: nothing computed is shown, no
form is made, ceremony-tagged material stays held.

**Added on 2026-11-15.** The owner asked for the first five points and they
were carried out that day (project log, "The five changes to the learner
pages"). One of them rested on a mistake of mine, which is corrected where
it stands: point 1 says the Blue Book opens every lesson with a dialogue.
It does not. Every lesson opens with its Basic Words, then the dialogues,
then Additional Words, and the lesson page already followed that order. The
order was kept. The same day's work also found that the English beside
some Blue Book words was the English of the row above (the Useful Phrases
of lesson 18 among them), which matters for point 2: the phrases are
gathered from the lessons' text and each is proved against its row of the
page.

## What already follows good practice

- **It says what it is.** "No speaker of Pawnee and no one from the Pawnee
  Nation has reviewed it yet … trust them before this site" stands on the
  first page a learner opens, and each page ends with what it is not. For a
  heritage language that is the most important sentence on the site.
- **A path, with one small task per step.** "Do: one round a day, ten
  questions" is the right size. Short and daily beats long and weekly, and
  the page says so.
- **Recognition before recall.** The games go from choosing a meaning, to
  choosing the word, to typing it. That is the order that works.
- **Comparison instead of rules.** "Compare the seven verbs" and "words that
  share a piece" let a learner notice a pattern in printed forms. Given that
  the site may not explain what it has not been told, this is the best
  available way to teach grammar, and a good one in any case.
- **Paper.** The printable word list and verb tables matter for learners who
  study away from a screen, and for classes.

## What I would change first

1. **Lead with the dialogue.** *(Wrong about the book: see the note of
   2026-11-15 above. The book opens a lesson with 6 to 20 basic words and
   then the dialogue; only lesson 19 has a list of forty, because the months
   and weekdays are stored there as basic words. What was done instead: the
   order kept, links to each part at the top of a lesson, one side of a
   dialogue can be covered, and the lessons moved up to step 2 of "Start
   here".)* The Blue Book opens every lesson with a short
   exchange; the lesson page opens with a table of up to forty words and the
   dialogue comes after it. Connected language that means something ("What is
   it? It is a feather.") is what a beginner remembers and can use the same
   day; a word list is support for it. I would put the dialogue first on each
   lesson page, then the words, then the notes. The same goes for the path:
   lesson 1's dialogue could be step 2, before the first flashcard set.
   Since tonight every dialogue line stands with its English (105 pairs; 83
   of the 156 stored lines had been unpaired), so the dialogues can carry
   more: cover the English and recall it, cover the Pawnee and say it, take
   both parts aloud.
2. **Give the learner phrases to use today.** Each lesson has a "Useful
   Phrases" section (*Síks•a'* "come here", *Wis* "hurry", *Tsíru'* "wait",
   and lines such as "sit down" and "I'm hungry" elsewhere in the lessons). They are printed, short, and exactly what a family
   can use at home. A page that gathers them by situation, each linked to its
   lesson, would be the most used page on the site. No new forms are needed.
3. **Space the practice.** The games remember missed words, which is good,
   but nothing brings a word back after a day, then three days, then a week.
   A Leitner box in the browser's storage (five boxes; a right answer moves a
   word up, a miss sends it back to the first; "12 words due today" on the
   Practice page) is a small piece of code and is the best-supported
   technique there is for vocabulary. The local app already has such a
   scheduler (`web/srs.py`).
4. **One spelling to learn to write, said where the learner reads.** A lesson
   page shows a word up to four ways: the Blue Book's spelling, the
   dictionary entry in learner spelling, the "Say it" respelling and Parks's
   phonetic form. The explanation is there but folded away. One visible line
   on every lesson and flashcard page would settle it: which spelling Pawnee
   people write today (the owner says the learner spelling), that the Blue
   Book column is how the 1979 textbook writes the same word, and that "Say
   it" is only a hint for English speakers. The first three flashcard weeks
   are Blue Book-only entries in the textbook's spelling, so a beginner's
   first words are in the spelling they will not go on to use; that makes
   open item 52 (what the 93 entries are) worth settling early.
5. **Do not show a stem's pronunciation beside an inflected word.** On lesson
   9 the row *ti•'at* "it has gone" shows "uht" under "Say it" and `[–ət–]`
   under IPA: those belong to the dictionary entry *at*, the stem, not to the
   word in the first column. A learner will read "uht" as how to say
   *ti•'at*. Three vocabulary rows are tied to an entry as a form of its stem
   (`match_type` "stem": *ti•'at*, *ti•ta•'at*, *we tí•hura•hats*). For those
   I would show the link and leave "Say it" and IPA empty, or head the two
   columns "the dictionary entry". The same table calls an inflected verb
   form "not in Parks dictionary"; the verb usually is in Parks, under its
   stem. "No dictionary entry linked" would be true in both cases. (The
   wording is in `web/templates/lesson_detail.html`, older than both of us.)

## Worth doing, less urgent

6. **Sound.** A learner cannot hear a word, and no amount of respelling
   replaces that; the site says so honestly. This is the largest gap and it
   is not one code can close (open item 67). Two things could be checked: the
   American Indian Studies Research Institute at Indiana University, which
   published Parks's dictionary, has had online Pawnee dictionaries with
   recordings; and the Pawnee Nation runs its own language programme. I have
   not verified either tonight. If one exists and the Nation is content with
   it, a link to it from "Start here" would do more for pronunciation than
   anything on the Sounds page. It belongs in the review packet as a
   question.
7. **A plan for today.** The ticks on "Start here" record what was done once.
   A learner comes back asking "what do I do now?". A small box on the first
   page ("Today: 8 words due, then the dialogue of lesson 3") turns six steps
   into a habit. It needs item 3.
8. **After a miss, show why.** When a learner picks the wrong word, show the
   right one with its printed pieces and its syllables, since both are
   already on the site, and ask it again before the round ends. Feedback at
   the moment of the mistake is worth more than a list at the end.
9. **Keep the reference tables one step back.** The Verbs page teaches well
   as far as "to go, eleven words" and then meets a beginner with Tables 6 to
   17. They are already called reference; folding them shut by default would
   keep the page from frightening the people it is for.
10. **Point outward.** For a language learned in a community, the best
    practice is people. A short "Learn with others" block (the Nation's
    language programme, classes, how to ask a speaker) should come before any
    game, once the owner knows what may be linked.

## Small things

- The language tag is written `lang="x-paw"` (156 places). The code for
  Pawnee is `paw` (ISO 639-3), and `paw-fonipa` for the phonetic forms. It
  changes nothing a sighted reader sees, but it is the correct label for
  screen readers, fonts and search engines.
- At a width of about 1,000 pixels the tenth menu item, "About", wraps to a
  line of its own. Ten items is many; "Flashcards", "Practice" and "Topics"
  could sit under one "Practise" heading.
- "Six steps, in an order that works for most beginners" is a claim nobody
  has tested. "In an order we suggest" promises less.
- Topics lists 392 words for "Body & Health" and 320 for "Animals". For a
  beginner a topic is twenty words. A "start with these" set per topic, taken
  from the flashcard words, would make the page a study tool as well as an
  index.
- The lesson pages now show three lines in square brackets where the scan is
  damaged (*Kitské [w]e ru'?*, *We ti p[it]ku.*, *Ka res•[..]sí•urúkat!*).
  A learner needs one line saying what the brackets mean. That decision was
  mine and the owner has been told; it may change.

## What I would not do

- Not add machine-made audio or pronunciation by a speech synthesiser. It
  would be a computed form of the worst kind: confident and unreviewed.
- Not turn Blue Book spelling into learner spelling by a rule, or the other
  way. Where the two differ, show both as printed and say which is which.
- Not add streaks, points or leaderboards. The learners here are few and
  come for reasons that a score does not serve; a plain "due today" is
  enough.

## What changed under the pages tonight

For whoever reads this later: on the evening of 2026-11-14 the Pawnee of all
twenty lessons was corrected from the scan (328 places, 8 titles; the
glossary no longer hangs on lesson 20's notes), the dialogues were paired
with their English, the Blue Book words were tied to dictionary entries by
their form only (the lesson vocabulary no longer links *asáki* "dog" to the
entry *a*), and Blue Book example sentences stand only under an entry one of
their words belongs to (43 instead of 88). The scope document's "seventh
part" has the detail.
