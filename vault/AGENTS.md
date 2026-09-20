# Conventions for this vault

This folder is the project's Obsidian vault (open `vault/` as a vault, or copy its notes into the
Mac vault at `~/Downloads/abrahimm/EMS`). Notes are Markdown with `[[wikilinks]]`; one idea per note;
every factual statement names the repository file (and, where it matters, the line or commit) it comes
from, so the note is a pointer and the repository is the record.

**What may appear here**
- Paths, schemas, column names, row counts and other aggregate counts.
- Decisions with their reasons and where they are recorded.
- The pipeline, the checks, the runners, the current status.

**What may not**
- Any record-level row of any data file.
- Any unpublished result: no coefficients, p-values or effect sizes from `PAPER_MASTER.md` §8 or from
  the confirmatory run. Point at the section instead.
- Any value from the confirmation windows (2015-07→2016-12, 2021→2024) while `config.FREEZE_ACTIVE` is
  True — and after the lift, only what the sealed result table and the paper carry.

**Updating.** When a decision lands in `docs/CONTEXT_CAPSULE.md` or the graph
(`docs/graph/graph_memory.jsonl`), mirror it in [[Decisions]] and refresh [[Status]]. Dates are UTC.
