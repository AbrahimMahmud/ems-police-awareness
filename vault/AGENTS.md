---
tags: [conventions]
updated: 2026-09-21
---
# Conventions for this vault

This folder is the project's Obsidian vault (open `vault/` as a vault, or copy its notes into the
Mac vault at `~/Downloads/abrahimm/EMS`). Notes are Markdown with wikilinks (double square brackets); one idea per note;
every factual statement names the repository file (and, where it matters, the line or commit) it comes
from, so the note is a pointer and the repository is the record. Start at [[00 Project]].

**Structure**
- Hand-written topic notes at the top level, each with YAML frontmatter (`tags`, `updated`) and a
  "Related" footer, so nothing is an orphan in the graph view.
- `Graph/` holds one generated note per memory-graph node (`python3 -m graph_memory.obsidian`, run from
  `ops/`); do not edit them by hand — add or link nodes with `graph-memory`, export, re-render. The index
  is [[Graph memory]].

**What may appear here**
- Paths, schemas, column names, row counts and other aggregate counts.
- Decisions with their reasons and where they are recorded.
- The pipeline, the checks, the runners, the current status.

**What may not**
- Any record-level row of any data file.
- Any unpublished result: no coefficients, p-values or effect sizes from `PAPER_MASTER.md` §8 or §8b or from
  the confirmatory run. Point at the section instead. The graph renderer enforces this for `Graph/` by
  replacing such values with a marker.
- Any value from the confirmation windows (2015-07→2016-12, 2021→2024) beyond what the sealed result table
  and the paper carry (the freeze was lifted 2026-09-20; the rule about values stands).

**Updating.** When a decision lands in `docs/CONTEXT_CAPSULE.md` or the graph
(`docs/graph/graph_memory.jsonl`), mirror it in [[Decisions]], refresh [[Status]] and [[Next actions]], and
re-render `Graph/`. Dates are UTC.

Related: [[00 Project]] · [[Tooling]]
