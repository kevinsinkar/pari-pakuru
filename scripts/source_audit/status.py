#!/usr/bin/env python3
"""Print how far the source-fidelity audit has got, and the last lines of its log.

    python scripts/source_audit/status.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402

if __name__ == "__main__":
    state.out(state.status_text())
    if state.LOG.exists():
        lines = state.LOG.read_text(encoding="utf-8").splitlines()
        state.out("")
        state.out("last log lines (%s):" % state.LOG.relative_to(state.ROOT).as_posix())
        for line in lines[-8:]:
            state.out("  " + line)
