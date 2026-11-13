#!/usr/bin/env python3
"""
Checkpoint state of the source-fidelity audit
=============================================

One file, reports/source_audit_2026-11/STATE.json, says how far the audit has
got. Every stage script updates it through this module, so that a session that
is cut off can be picked up again from the first unfinished unit.

    python scripts/source_audit/state.py status
    python scripts/source_audit/state.py start 2 --units 181
    python scripts/source_audit/state.py progress 2 --done 50 --note "pages 1-50"
    python scripts/source_audit/state.py done 2 --count differences=412 --output s2e_differences.jsonl
    python scripts/source_audit/state.py cost --images 12 --agents 1
    python scripts/source_audit/state.py log "decided: ..."

The cost counters (images read by a model, sub-agents started) are the only
measure of cost the audit can keep: a session cannot see the account's usage
limit.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "source_audit_2026-11"
WORK = OUT / "work"
STATE = OUT / "STATE.json"
LOG = OUT / "progress.log"

STAGES = [
    ("0", "Baseline: backup, text dump of the database, hashes, test suites"),
    ("1", "Character table, by font, against rendered glyphs"),
    ("2", "Skiri-to-English against the text layer, both directions"),
    ("3", "Settle the Skiri-to-English differences from the page"),
    ("4", "Image-only parts: appendices and front-matter chapters"),
    ("5", "Blue Book"),
    ("6", "English-to-Skiri against the text layer"),
    ("7", "Report and proposed fixes"),
    ("8", "Apply the fixes that were approved"),
    ("9", "Store Parks's own IPA symbols; regenerate and check the simplified forms"),
]


def out(text=""):
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def load():
    if STATE.exists():
        s = json.loads(STATE.read_text(encoding="utf-8"))
        for n, name in STAGES:                     # stages added after the audit began
            s["stages"].setdefault(n, {"name": name, "status": "pending", "units_total": None, "units_done": 0,
                                       "counts": {}, "outputs": [], "started": None, "finished": None, "note": ""})
        return s
    return {
        "audit": "source-fidelity audit 2026-11",
        "prompt": "prompts/source_fidelity_audit.md",
        "created": now(),
        "updated": now(),
        "cost": {"images_read_by_model": 0, "subagents_started": 0},
        "stages": {n: {"name": name, "status": "pending", "units_total": None, "units_done": 0,
                       "counts": {}, "outputs": [], "started": None, "finished": None, "note": ""}
                   for n, name in STAGES},
    }


def save(state):
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    state["updated"] = now()
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(STATE)          # written whole or not at all


def log(message):
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8", newline="\n") as f:
        f.write("%s  %s\n" % (now(), message))


def stage_start(n, units_total=None, note=""):
    s = load()
    st = s["stages"][str(n)]
    if st["status"] != "done":
        st["status"] = "running"
    st["started"] = st["started"] or now()
    if units_total is not None:
        st["units_total"] = units_total
    if note:
        st["note"] = note
    save(s)
    log("stage %s started%s" % (n, (": " + note) if note else ""))


def stage_progress(n, units_done=None, note="", counts=None, units_total=None):
    s = load()
    st = s["stages"][str(n)]
    if units_done is not None:
        st["units_done"] = units_done
    if units_total is not None:
        st["units_total"] = units_total
    if counts:
        st["counts"].update(counts)
    if note:
        st["note"] = note
    save(s)
    log("stage %s: %s of %s units%s" % (n, st["units_done"], st["units_total"], ("; " + note) if note else ""))


def stage_done(n, counts=None, outputs=None, note=""):
    s = load()
    st = s["stages"][str(n)]
    st["status"] = "done"
    st["finished"] = now()
    if st["units_total"] is not None:
        st["units_done"] = st["units_total"]
    if counts:
        st["counts"].update(counts)
    for o in outputs or []:
        if o not in st["outputs"]:
            st["outputs"].append(o)
    if note:
        st["note"] = note
    save(s)
    log("stage %s done%s" % (n, (": " + note) if note else ""))


def add_cost(images=0, agents=0):
    s = load()
    s["cost"]["images_read_by_model"] += images
    s["cost"]["subagents_started"] += agents
    save(s)
    if images or agents:
        log("cost: +%d images read, +%d sub-agents (total %d, %d)" % (
            images, agents, s["cost"]["images_read_by_model"], s["cost"]["subagents_started"]))


def status_text():
    s = load()
    lines = ["Source-fidelity audit 2026-11   (state of %s)" % s["updated"], ""]
    lines.append("%-5s %-8s %-11s %s" % ("stage", "status", "units", "what"))
    for n, name in STAGES:
        st = s["stages"][n]
        units = "" if st["units_total"] is None else "%s/%s" % (st["units_done"], st["units_total"])
        lines.append("%-5s %-8s %-11s %s" % (n, st["status"], units, name))
        if st["counts"]:
            lines.append("%27s%s" % ("", ", ".join("%s %s" % (k, v) for k, v in st["counts"].items())))
        if st["note"]:
            lines.append("%27snote: %s" % ("", st["note"]))
    c = s["cost"]
    lines += ["", "cost so far: %d images read by a model, %d sub-agents started" % (
        c["images_read_by_model"], c["subagents_started"])]
    nxt = next((n for n, _ in STAGES if s["stages"][n]["status"] != "done"), None)
    lines.append("next: " + ("stage %s" % nxt if nxt else "nothing; every stage is done"))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status")
    p = sub.add_parser("start"); p.add_argument("stage"); p.add_argument("--units", type=int); p.add_argument("--note", default="")
    p = sub.add_parser("progress"); p.add_argument("stage"); p.add_argument("--done", type=int); p.add_argument("--units", type=int)
    p.add_argument("--note", default=""); p.add_argument("--count", action="append", default=[])
    p = sub.add_parser("done"); p.add_argument("stage"); p.add_argument("--note", default="")
    p.add_argument("--count", action="append", default=[]); p.add_argument("--output", action="append", default=[])
    p = sub.add_parser("cost"); p.add_argument("--images", type=int, default=0); p.add_argument("--agents", type=int, default=0)
    p = sub.add_parser("log"); p.add_argument("message")
    args = ap.parse_args()

    def counts(pairs):
        d = {}
        for pair in pairs:
            k, _, v = pair.partition("=")
            d[k] = int(v) if v.lstrip("-").isdigit() else v
        return d

    if args.cmd == "start":
        stage_start(args.stage, args.units, args.note)
    elif args.cmd == "progress":
        stage_progress(args.stage, args.done, args.note, counts(args.count), args.units)
    elif args.cmd == "done":
        stage_done(args.stage, counts(args.count), args.output, args.note)
    elif args.cmd == "cost":
        add_cost(args.images, args.agents)
    elif args.cmd == "log":
        log(args.message)
    out(status_text())


if __name__ == "__main__":
    main()
