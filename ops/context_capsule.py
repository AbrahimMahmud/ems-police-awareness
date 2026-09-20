#!/usr/bin/env python3
"""context-capsule — load or extend the project's decision ledger.

    context-capsule load            # print docs/CONTEXT_CAPSULE.md (the decision ledger) and the
                                    # current status block of docs/EXECUTION_PLAN.md
    context-capsule add "text"      # append a dated ledger entry (a decision, with its reason)

The ledger is a git-tracked Markdown file, so it needs no service and survives any
container; the graph (ops/graph_memory) holds the same decisions as typed nodes with
citations for search.
"""
import datetime as dt
import re
import signal
import sys

signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "CONTEXT_CAPSULE.md"
PLAN = ROOT / "docs" / "EXECUTION_PLAN.md"


def load():
    print(LEDGER.read_text() if LEDGER.exists() else "(no ledger yet)")
    if PLAN.exists():
        text = PLAN.read_text()
        m = re.search(r"^## Status \(.*?(?=^## |^### What the CP1)", text, re.S | re.M)
        if m:
            print("\n---\n# EXECUTION_PLAN.md — current status block\n")
            print(m.group(0).strip())


def add(text):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    with open(LEDGER, "a") as fh:
        fh.write(f"\n- **{stamp}** — {text}\n")
    print(f"appended to {LEDGER.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "load":
        load()
    elif len(sys.argv) >= 3 and sys.argv[1] == "add":
        add(" ".join(sys.argv[2:]))
    else:
        print(__doc__); sys.exit(2)
