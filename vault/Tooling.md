---
tags: [tools]
updated: 2026-09-21
---
# Tooling

Repo-tracked equivalents of the Mac-side setup, so every environment carries the same memory (`docs/LOCAL_SETUP.md`):

- **Context capsule** — `context-capsule load` prints `docs/CONTEXT_CAPSULE.md` (the decision ledger) and the
  current Status block of `docs/EXECUTION_PLAN.md`; `context-capsule add "…"` appends. Script: `ops/context_capsule.py`.
- **Memory graph** — `graph-memory add|link|search|list|export|import` (`ops/graph_memory/`), sqlite at
  `~/.local/share/ems-graph/graph_memory.sqlite`, git-tracked export `docs/graph/graph_memory.jsonl`; seed with
  `python3 -m graph_memory.seed` from `ops/`. Node types: intent, decision, finding, provenance, open_question,
  next_action, rule, status; trust in [0, 1]; citations are `commit:<sha>` or `path[:line]`.
- **SQL over the sources** — `ops/ems_duckdb.py "SELECT …"`: read-only DuckDB views over `data/processed` and
  `data/reference`, aggregates only (the guard refuses `SELECT *`/record-level output and any COPY/INSTALL/LOAD).
  Outcome files are exposed only through the discovery window while the freeze holds.
- **Python** — `pyproject.toml` pins the versions the analysis ran on (pandas 3.0.5, numpy 2.4.6, scipy 1.17.1,
  statsmodels 0.15.0, pyfixest 0.60.0); `uv lock` writes `uv.lock`; `uv run pytest` runs `tests/` (synthetic-data
  tests that wrap the gate's data-free checks). Never re-lock or bump these five without asking.
- **Graph → Obsidian** — `python3 -m graph_memory.obsidian` (from `ops/`; `--export`, `--vault` optional) renders
  every node of `docs/graph/graph_memory.jsonl` as `vault/Graph/<id>.md` with its edges as wikilinks and writes
  the index [[Graph memory]]; result values are replaced by a marker (the vault rule). Re-run after every export.
- **This vault** — conventions in [[AGENTS]]; hub [[00 Project]].

Related: [[00 Project]] · [[Graph memory]] · [[Lessons]]
