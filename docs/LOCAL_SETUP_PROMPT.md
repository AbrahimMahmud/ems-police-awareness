# Local setup — the plan of record

The author works in two places: an ephemeral analysis container (this repository checked out, runners in
`ops/`, compute that advances only while a session is active) and a Mac with the same repository plus
local conveniences — a context capsule, a memory graph (MCP server + CLI), a read-only DuckDB MCP server over
the sources, an Obsidian vault, and a uv-managed Python. The plan is that **the repository carries the memory,
and each machine carries only a thin shell around it**:

1. Decisions are written once, in `docs/CONTEXT_CAPSULE.md` (dated, with reason and citation) and as
   `decision` nodes of the graph; the vault's [[Decisions]] mirrors them.
2. The graph's sqlite is machine-local; its export `docs/graph/graph_memory.jsonl` is the record and is
   committed with the decisions it describes. Import it on the other machine before working.
3. The vault holds pointers, schemas and aggregate counts — never records, never unpublished results
   (`vault/AGENTS.md`).
4. SQL over the sources is read-only and aggregate-only; outcome views obey the freeze through the same
   constants the guard uses.
5. Python versions are pinned in `pyproject.toml`/`uv.lock` to what the analysis ran on; the twelve
   synthetic-data tests in `tests/` run anywhere, data or not.
6. The analysis pipeline itself (`run_all.py`, the runners, the gate) does not depend on any of this; the
   tooling can be removed by reverting its commit (`docs/LOCAL_SETUP.md`, Rollback).

Built in the container 2026-09-20 at the author's request ("make sure you are updating the graph and
obsidian, set up the stuff here"); the Mac copies pre-date it and are reconciled by export/import.
