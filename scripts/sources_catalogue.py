#!/usr/bin/env python3
"""The register of sources: what else there is on Pawnee, and how this project may use each (2026-11-15).

The project copies forms from two books. On 2026-11-15 the owner brought a
catalogue of 59 further resources ("Skiri Pawnee Language Sources.xlsx", kept
in the root and out of git): for each a credibility score, the dialect, what
it holds, why it is rated so, a note on rights and a link. This script turns
the catalogue into sources/catalogue.json and keeps it honest.

A record has two halves. The spreadsheet's columns are copied (an e-mail
address is cut out; nothing else is changed). Under "project" stand this
project's own decisions, which the spreadsheet never overwrites:

    link       may the site link to it
    url        its address, where the spreadsheet's no longer answers (the
               spreadsheet's own stays in the record beside it)
    section    where the learner page "Learn with others" lists it, or null
    title, says   the name and the sentence the learner page shows for it,
               written from what its page was seen to say
    check      what the project uses it to check, or null
    copy       "source" (the two books forms are copied from), "ask" (its
               content is wanted and needs permission first), or "no"
    sensitive  ceremonial material: never on a learner page, never copied
    checked    when its link was last tried, what came back, and what the
               page was SEEN to say by a person or a session that opened it

A source enters by one of three doors: link, check, copy. Until the rights
are clear in writing, only the first two are open.

Usage:
    python scripts/sources_catalogue.py                  # what an import would change; changes nothing
    python scripts/sources_catalogue.py --apply          # write sources/catalogue.json and rating_key.json
    python scripts/sources_catalogue.py --check-links    # try every link once and record the result
    python scripts/sources_catalogue.py --load-db        # what the table `sources` would hold; changes nothing
    python scripts/sources_catalogue.py --load-db --apply    # back up, load the table, report, write the dump
    python scripts/sources_catalogue.py --check          # exit 0 if the register is sound
    python scripts/sources_catalogue.py --list           # the learner page's sources, by section
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "Skiri Pawnee Language Sources.xlsx"
FOLDER = ROOT / "sources"
CATALOGUE = FOLDER / "catalogue.json"
RATING_KEY = FOLDER / "rating_key.json"
DB = ROOT / "skiri_pawnee.db"
REPORT = ROOT / "reports" / "sources_register_report.txt"

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
COLUMNS = [("A", "title"), ("B", "credibility"), ("C", "dialect"), ("D", "type"), ("E", "access"), ("F", "best_for"),
           ("G", "creator"), ("H", "publisher"), ("I", "year"), ("J", "contains"), ("K", "why_rating"), ("L", "rights"),
           ("M", "url")]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SECTIONS = [("nation", "Learn with the Pawnee Nation"), ("hear", "Hear the language"), ("read", "Read")]

# Short names for the records the code or the pages name; every other record is named from its title.
KEYS = [
    ("Pawnee Nation Language Program", "nation_program"),
    ("Pâripakûru' — Pawnee Language Department Facebook", "nation_facebook"),
    ("Pawnee Nation YouTube", "nation_youtube"),
    ("Pawnee Nation Mukurtu Portal", "nation_mukurtu"),
    ("Pawnee Nation language lessons 1–3", "nation_lessons"),
    ("Pari Pakuru': Introduction to Spoken Pawnee", "blue_book"),
    ("Chaticks si Chaticks", "nation_newspaper"),
    ("Pawnee Nation College", "nation_college"),
    ("Pawnee Language Learning (podcast", "podcast_language_learning"),
    ("“Pâripakûru' with Zach Rice and Taylor Moore”", "podcast_life_in_ruins_89"),
    ("IIK Dictionary Database", "iik_dictionary"),
    ("IIK Northern Caddoan Linguistic Text Corpora", "iik_corpora"),
    ("Pawnee Language Program curriculum", "skiri_course_1997"),
    ("Pawnee Alphabet Book", "alphabet_book"),
    ("A Dictionary of Skiri Pawnee — Parks & Pratt", "parks"),
    ("A Grammar of Pawnee — Parks", "parks_grammar_1976"),
]
# What marks a record as ceremonial when it is first imported. A person goes over the result: the flag is
# the project's, kept in the file, and an import never changes it afterwards.
SENSITIVE = re.compile(r"ceremon|culturally sensitive|sacred|bundle|ghost dance|star lore|cosmolog|song", re.I)


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def slug(title):
    plain = "".join(c for c in unicodedata.normalize("NFD", title) if unicodedata.category(c) != "Mn")
    words = re.findall(r"[a-z0-9]+", plain.lower())
    key = ""
    for w in words:
        if len(key) + len(w) + 1 > 44:
            break
        key = (key + "_" + w) if key else w
    return key


def key_for(title):
    for prefix, key in KEYS:
        if title.startswith(prefix):
            return key
    return slug(title)


def without_address(text):
    """The text without an e-mail address and the sentence that gives it; and whether one was cut."""
    cut = False
    while True:
        m = EMAIL.search(text)
        if not m:
            return text, cut
        start = text.rfind(". ", 0, m.start())
        start = start + 2 if start >= 0 else 0
        end = m.end() + (1 if text[m.end():m.end() + 1] == "." else 0)
        text = (text[:start] + text[end:]).strip()
        cut = True


def read_xlsx(path):
    """(records, notes) of the spreadsheet: the rows of sheet 1 by column, the two columns of sheet 2."""
    z = zipfile.ZipFile(path)
    shared = []
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("{%s}si" % M):
        shared.append("".join(t.text or "" for t in si.iter("{%s}t" % M)))

    def rows(n):
        sheet = ET.fromstring(z.read("xl/worksheets/sheet%d.xml" % n))
        links = {}
        try:
            rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/worksheets/_rels/sheet%d.xml.rels" % n))}
            for h in sheet.iter("{%s}hyperlink" % M):
                links[h.get("ref")] = rels.get(h.get("{%s}id" % R))
        except KeyError:
            pass
        for row in sheet.iter("{%s}row" % M):
            cells = {}
            for c in row.findall("{%s}c" % M):
                v = c.find("{%s}v" % M)
                if c.get("t") == "s" and v is not None:
                    value = shared[int(v.text)]
                elif c.get("t") == "inlineStr":
                    value = "".join(x.text or "" for x in c.iter("{%s}t" % M))
                else:
                    value = v.text if v is not None else ""
                ref = c.get("r")
                cells[re.sub(r"\d+", "", ref)] = (" ".join((value or "").split()), links.get(ref))
            yield cells

    records = []
    for i, cells in enumerate(rows(1)):
        if i == 0 or not cells.get("A", ("",))[0]:
            continue
        rec, cut = {}, False
        for col, name in COLUMNS:
            value = cells.get(col, ("", None))[0]
            value, was_cut = without_address(value)
            cut = cut or was_cut
            rec[name] = value
        if rec["url"] in ("", "—", "-"):
            rec["url"] = cells.get("A", ("", None))[1] or ""
        try:
            rec["credibility"] = int(float(rec["credibility"]))
        except ValueError:
            rec["credibility"] = None
        rec = dict(key=key_for(rec["title"]), **rec)
        if cut:
            rec["cut_from_the_spreadsheet"] = "a sentence that gave an e-mail address"
        records.append(rec)
    notes = [{"topic": c.get("A", ("",))[0], "note": without_address(c.get("B", ("",))[0])[0]}
             for i, c in enumerate(rows(2)) if i > 0 and c.get("A", ("",))[0]]
    return records, notes


def first_project_fields(rec):
    """The project's half of a record that is new. Cautious: nothing is on a learner page until someone says so."""
    text = " ".join([rec["title"], rec["contains"], rec["rights"], rec["type"]])
    sensitive = bool(SENSITIVE.search(text))
    return {"link": not sensitive, "section": None, "check": None,
            "copy": "source" if rec["key"] in ("parks", "blue_book") else "no",
            "sensitive": sensitive, "note": None,
            "checked": {"on": None, "status": None, "final_url": None, "seen": None}}


def address(rec):
    """Where a source is: the project's own address for it if the spreadsheet's is stale, else the spreadsheet's."""
    return (rec.get("project") or {}).get("url") or rec.get("url") or ""


def load():
    return json.loads(CATALOGUE.read_text(encoding="utf-8")) if CATALOGUE.exists() else {"records": []}


def write_catalogue(data):
    FOLDER.mkdir(exist_ok=True)
    lines = ["{", ' "about": %s,' % json.dumps(data["about"], ensure_ascii=False),
             ' "spreadsheet_compiled": %s,' % json.dumps(data.get("spreadsheet_compiled"), ensure_ascii=False),
             ' "records": [']
    for i, rec in enumerate(data["records"]):
        body = json.dumps(rec, ensure_ascii=False, indent=1).replace("\n", "\n  ")
        lines.append("  " + body + ("," if i < len(data["records"]) - 1 else ""))
    lines += [" ]", "}"]
    CATALOGUE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def plan_import(xlsx):
    records, notes = read_xlsx(xlsx)
    old = {r["key"]: r for r in load().get("records", [])}
    merged, log = [], []
    seen = set()
    for rec in records:
        if rec["key"] in seen:
            raise SystemExit("two records are named %s" % rec["key"])
        seen.add(rec["key"])
        before = old.get(rec["key"])
        if before is None:
            rec["project"] = first_project_fields(rec)
            log.append("new       %s" % rec["key"])
        else:
            rec["project"] = before["project"]
            changed = [k for _, k in COLUMNS if before.get(k) != rec.get(k)]
            if changed:
                log.append("changed   %s: %s" % (rec["key"], ", ".join(changed)))
        merged.append(rec)
    for key, rec in old.items():
        if key not in seen:
            rec.setdefault("project", {})["note"] = ((rec["project"].get("note") or "") + " Not in the spreadsheet any more.").strip()
            merged.append(rec)
            log.append("kept      %s (not in the spreadsheet any more)" % key)
    compiled = next((n["note"] for n in notes if n["topic"].lower().startswith("compiled")), None)
    data = {"about": "Resources on the Pawnee language beyond the two books this project copies forms from. The fields before "
                     "'project' are copied from a catalogue the project's owner brought on 2026-11-15 (a spreadsheet kept out of "
                     "git): its credibility scores and its notes are its compiler's judgement, made from web searches, and most "
                     "archival items are described from their catalogue entries. Under 'project' stand this project's own "
                     "decisions about each source. See sources/README.md and scripts/sources_catalogue.py.",
            "spreadsheet_compiled": compiled, "records": merged}
    return data, notes, log


def problems_of(data, conn=None):
    """What is wrong with the register."""
    bad = []
    records = data.get("records", [])
    keys = [r.get("key") for r in records]
    for k in ("parks", "blue_book"):
        if k not in keys:
            bad.append("the record %s is missing: the two books forms are copied from must be in the register" % k)
    if len(set(keys)) != len(keys):
        bad.append("two records share a name")
    text = CATALOGUE.read_text(encoding="utf-8") + (RATING_KEY.read_text(encoding="utf-8") if RATING_KEY.exists() else "")
    if EMAIL.search(text):
        bad.append("an e-mail address stands in the register")
    names = {s for s, _ in SECTIONS}
    for r in records:
        p = r.get("project")
        if not isinstance(p, dict) or not {"link", "section", "check", "copy", "sensitive", "checked"} <= set(p):
            bad.append("%s: the project's fields are not complete" % r.get("key"))
            continue
        if p["copy"] not in ("source", "ask", "no"):
            bad.append("%s: copy is %r" % (r["key"], p["copy"]))
        if p["sensitive"] and (p["section"] or p["copy"] != "no"):
            bad.append("%s: ceremonial material is on a learner page or marked for copying" % r["key"])
        if p["section"]:
            if p["section"] not in names:
                bad.append("%s: unknown section %r" % (r["key"], p["section"]))
            if not p["link"] or not address(r):
                bad.append("%s: listed for learners without a link" % r["key"])
            if not (p["checked"] or {}).get("seen"):
                bad.append("%s: listed for learners, but nobody has recorded what its page says" % r["key"])
            if not p.get("says") or not p.get("title"):
                bad.append("%s: listed for learners without the title and the sentence the page shows" % r["key"])
            # 2xx answers; 403, 418 and 429 are sites that turn automated clients away, and then the note of what
            # the page was seen to say (required above) is the evidence that the link is good
            status = str((p["checked"] or {}).get("status"))
            if not (status.startswith("2") or status in ("not checkable", "403", "418", "429")):
                bad.append("%s: listed for learners, and its link last answered %s" % (r["key"], status))
        if p["copy"] == "source" and r["key"] not in ("parks", "blue_book"):
            bad.append("%s: marked as a source of forms; only the two books are" % r["key"])
    if conn is not None:
        has = conn.execute("select count(*) from sqlite_master where type='table' and name='sources'").fetchone()[0]
        if not has:
            bad.append("the table `sources` is not in the database (--load-db --apply)")
        elif [tuple(r) for r in conn.execute("select * from sources order by key")] != sorted(table_rows(data)):
            bad.append("the table `sources` does not hold what the file holds (--load-db --apply)")
    return bad


TABLE = """create table if not exists sources (
    key text primary key, title text not null, creator text, publisher text, year text, type text, dialect text,
    access text, rights text, url text, credibility integer, link integer not null, section text, copy text not null,
    sensitive integer not null, checked_on text, url_status text)"""


def table_rows(data):
    rows = []
    for r in data["records"]:
        p = r["project"]
        c = p.get("checked") or {}
        rows.append((r["key"], r["title"], r["creator"] or None, r["publisher"] or None, r["year"] or None, r["type"] or None,
                     r["dialect"] or None, r["access"] or None, r["rights"] or None, address(r) or None, r["credibility"],
                     int(bool(p["link"])), p["section"], p["copy"], int(bool(p["sensitive"])), c.get("on"),
                     None if c.get("status") is None else str(c.get("status"))))
    return rows


AGENT = "Mozilla/5.0 (compatible; link-check)"       # a plain client name: nothing about the project or its owner


def try_link(url):
    """(status, final address). One request, a plain client name, nothing kept of the page.

    curl is tried first where there is one: on Windows it trusts the system's certificates, which Python's own
    client does not always do (ten sound links failed with it on 2026-11-15). A site that answers 403, 418 or 429
    is there but turns automated clients away; whether its page says what the register says is for a reader."""
    if "facebook.com" in url:
        return "not checkable", url           # Facebook answers automated requests with a login wall
    curl = shutil.which("curl")
    if curl:
        try:
            got = subprocess.run([curl, "-s", "-L", "-o", os.devnull, "--max-time", "30", "-A", AGENT,
                                  "-w", "%{http_code} %{url_effective}", url], capture_output=True, text=True, timeout=45)
            code, _, final = got.stdout.strip().partition(" ")
            if code.isdigit() and code != "000":
                return int(code), final or url
        except (subprocess.TimeoutExpired, OSError):
            pass
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.geturl()
    except urllib.error.HTTPError as error:
        return error.code, url
    except Exception as error:                # a name that does not resolve, a timeout, a certificate
        reason = getattr(error, "reason", None)
        return "no answer (%s)" % (str(reason)[:60] if reason else type(error).__name__), url


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=str(XLSX), help="the spreadsheet (default: the one in the root)")
    ap.add_argument("--apply", action="store_true", help="write (the import, or with --load-db the table)")
    ap.add_argument("--check", action="store_true", help="exit 0 if the register is sound")
    ap.add_argument("--check-links", action="store_true", help="try every link once and record the result")
    ap.add_argument("--only", metavar="KEYS", help="with --check-links: these records only, comma-separated")
    ap.add_argument("--load-db", action="store_true", help="the table `sources` from the file")
    ap.add_argument("--list", action="store_true", help="the learner page's sources by section")
    args = ap.parse_args()

    if args.check:
        data = load()
        conn = sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True) if DB.exists() else None
        bad = problems_of(data, conn)
        for b in bad:
            out("PROBLEM  " + b)
        recs = data["records"]
        if not bad:
            out("the register of sources is sound: %d records (2 the books forms are copied from, %d listed for learners, "
                "%d wanted and to be asked for, %d held as ceremonial); no e-mail address; every source on the learner page "
                "has a link that answers and a note of what its page was seen to say; the table `sources` holds the same" % (
                    len(recs), sum(1 for r in recs if r["project"]["section"]), sum(1 for r in recs if r["project"]["copy"] == "ask"),
                    sum(1 for r in recs if r["project"]["sensitive"])))
        raise SystemExit(1 if bad else 0)

    if args.list:
        data = load()
        for name, label in SECTIONS:
            out("== %s" % label)
            for r in data["records"]:
                if r["project"]["section"] == name:
                    out("   %-28s %-22s %s" % (r["key"], r["dialect"], r["title"][:70]))
        return

    if args.check_links:
        data = load()
        only = set((args.only or "").split(",")) - {""}
        today = dt.date.today().isoformat()
        for r in data["records"]:
            url = address(r)
            if not url or (only and r["key"] not in only):
                continue
            status, final = try_link(url)
            c = r["project"].setdefault("checked", {})
            c.update({"on": today, "status": status, "final_url": final if final != url else None})
            out("%-14s %-30s %s" % (status, r["key"], url[:80]))
        write_catalogue(data)
        counts = {}
        for r in data["records"]:
            s = str((r["project"].get("checked") or {}).get("status"))
            counts[s] = counts.get(s, 0) + 1
        out("links tried: %s" % ", ".join("%s: %d" % kv for kv in sorted(counts.items())))
        return

    if args.load_db:
        data = load()
        rows = sorted(table_rows(data))
        conn = sqlite3.connect(str(DB)) if args.apply else sqlite3.connect("file:%s?mode=ro" % DB.as_posix(), uri=True)
        has = conn.execute("select count(*) from sqlite_master where type='table' and name='sources'").fetchone()[0]
        now = [tuple(r) for r in conn.execute("select * from sources order by key")] if has else []
        out("table `sources`: %d rows now, %d in the file; %s" % (len(now), len(rows), "the same" if now == rows else "to be written"))
        if not args.apply:
            out("dry run: nothing was changed (use --load-db --apply)")
            return
        if now == rows:
            out("nothing to do")
            return
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backups = Path(os.environ.get("OneDrive", str(Path.home()))) / "pari_pakuru_backups"
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups / ("skiri_pawnee_backup_%s_sources.db" % stamp)
        shutil.copy2(DB, backup)
        conn.execute(TABLE)
        conn.execute("delete from sources")
        conn.executemany("insert into sources values (%s)" % ",".join("?" * 17), rows)
        conn.commit()
        text = "sources_catalogue --load-db — %s\ntable `sources`: %d rows before, %d now\nbackup: OneDrive/pari_pakuru_backups/%s\n" % (
            dt.datetime.now().strftime("%Y-%m-%d %H:%M"), len(now), len(rows), backup.name)
        if REPORT.exists():
            text = REPORT.read_text(encoding="utf-8").rstrip("\n") + "\n\n---- a later run ----\n" + text
        REPORT.write_text(text, encoding="utf-8", newline="\n")
        out("written; backup: %s; report: %s" % (backup.name, REPORT.relative_to(ROOT).as_posix()))
        subprocess.run([sys.executable, str(ROOT / "scripts" / "db_dump.py"), "--write"], check=True)
        return

    # the import
    xlsx = Path(args.xlsx)
    if not xlsx.exists():
        raise SystemExit("no spreadsheet at %s" % xlsx)
    data, notes, log = plan_import(xlsx)
    out("spreadsheet: %d records, %d notes; in the file now: %d records" % (len(read_xlsx(xlsx)[0]), len(notes), len(load().get("records", []))))
    for line in log:
        out("  " + line)
    cut = [r["key"] for r in data["records"] if r.get("cut_from_the_spreadsheet")]
    out("an e-mail address cut from: %s" % (", ".join(cut) or "none"))
    out("marked ceremonial at first import: %s" % ", ".join(r["key"] for r in data["records"] if r["project"]["sensitive"]))
    if not args.apply:
        out("dry run: nothing was written (use --apply)")
        return
    write_catalogue(data)
    RATING_KEY.write_text(json.dumps({"about": "The second sheet of the catalogue: its rating scale and its compiler's notes.",
                                      "notes": notes}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    out("written: %s, %s" % (CATALOGUE.relative_to(ROOT).as_posix(), RATING_KEY.relative_to(ROOT).as_posix()))


if __name__ == "__main__":
    main()
