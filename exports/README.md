# exports/

Data written out of the database so that it is kept in git.

| File | What it is |
|---|---|
| `community_feedback.json` | A copy of the `community_feedback` table: the flags and confirmations people have submitted through the web app. The app rewrites this file after every submission and every review |

This is the one table that cannot be rebuilt from the two sources, because it
is knowledge that people contributed. The database is not in git, so this file
is how that knowledge is kept safe. Commit it when it changes.

Do not edit it by hand; the app will overwrite it.

The Anki deck that used to be here was removed on 2026-11-13 (nobody uses Anki
on this project). `scripts/anki_export.py` can make it again.
