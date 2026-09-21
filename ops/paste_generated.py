#!/usr/bin/env python3
"""Refresh the generated regions of a document from the generators' output files.

    python3 ops/paste_generated.py docs/SUPPLEMENT.md docs/PAPER.md

A region is delimited by `<!-- BEGIN:<name> -->` and `<!-- END:<name> -->` on their own lines; the text
between them is replaced by the named source. Sources:

    phase_i_prose     ops/state/phase_i_tables_supp/prose.md      (the reader's transcript)
    phase_i_tables    ops/state/phase_i_tables_supp/tables.md     (Tables 8b.1–8b.5 renamed S1–S5 for the supplement)
    supp_tables       ops/state/supplement_tables/tables.md       (Tables S7–S10)
    paper_tables      ops/state/paper_tables/tables.md            (Tables 1 and 2 of the paper)
    episode_table     docs/tables/TABLE1_episodes.md              (the episode list, as Table S6 of the supplement;
                                                                   held byte-identical to its inputs by V.table1_regenerates)

Run the generators first (phase_i_tables.py --docs docs/PAPER_MASTER.md docs/SUPPLEMENT.md --out ops/state/phase_i_tables_supp;
supplement_tables.py; paper_confirmatory_tables.py). The claims for every generated number are the generators' claims.csv
files; ops/refresh_generated_claims.py replaces them in the register.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "phase_i_prose": ROOT / "ops/state/phase_i_tables_supp/prose.md",
    "phase_i_tables": ROOT / "ops/state/phase_i_tables_supp/tables.md",
    "supp_tables": ROOT / "ops/state/supplement_tables/tables.md",
    "paper_tables": ROOT / "ops/state/paper_tables/tables.md",
    "episode_table": ROOT / "docs/tables/TABLE1_episodes.md",
}
EPISODE_HEADING = "# Table 1 — Attention episodes under the adopted shock rule, with the frozen list beside them"
RENAME = {"phase_i_tables": [(f"**Table 8b.{i} —", f"**Table S{i} —") for i in range(1, 6)],
          "episode_table": [(EPISODE_HEADING, "**Table S6 — Attention episodes under the adopted shock rule, with the frozen list beside them.**")]}


def episode_table_body() -> str:
    """The supplement's Table S6 exactly as paste_generated renders it (the regeneration check compares against this)."""
    body = SOURCES["episode_table"].read_text(encoding="utf-8").rstrip() + "\n"
    for a, b in RENAME["episode_table"]:
        assert a in body, "the episode table's heading changed; update EPISODE_HEADING"
        body = body.replace(a, b)
    return body


def refresh(doc: Path) -> int:
    text = doc.read_text(encoding="utf-8")
    n = 0
    for name, src in SOURCES.items():
        pat = re.compile(rf"(<!-- BEGIN:{name} -->\n)(.*?)(<!-- END:{name} -->)", re.S)
        if not pat.search(text):
            continue
        body = src.read_text(encoding="utf-8").rstrip() + "\n"
        for a, b in RENAME.get(name, []):
            body = body.replace(a, b)
        assert "SYNTHETIC" not in body, f"{src} is a synthetic dry run; never pasted"
        text, k = pat.subn(lambda m: m.group(1) + body + m.group(3), text)
        n += k
    doc.write_text(text, encoding="utf-8")
    return n


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"{arg}: {refresh(ROOT / arg)} region(s) refreshed")
