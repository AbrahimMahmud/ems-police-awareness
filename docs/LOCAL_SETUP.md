# Local setup — status, data inventory, install manifest, rollback

*Written 2026-09-20 in the analysis container, as the repository-tracked twin of the setup on the
author's Mac (`docs/LOCAL_SETUP_PROMPT.md` is the plan of record behind it). Anything here that
names a path outside the repository names the container; the Mac equivalents are in the prompt.*

## Status

| item | state |
|---|---|
| Python | 3.11; `pyproject.toml` pins the estimation stack to the versions the analysis ran on (pandas 3.0.5, numpy 2.4.6, scipy 1.17.1, statsmodels 0.15.0, pyfixest 0.60.0); `uv lock` → `uv.lock`; `uv run pytest` runs `tests/` (12 synthetic-data tests wrapping the gate's data-free checks). **Never re-lock or bump the five without asking.** |
| Data | Real inputs live under `data/raw` (tracked), `data/reference` (tracked) and `data/processed` (gitignored, rebuilt by `run_all.py` from the raw page cache). On the Mac they are linked read-only from `~/.local/share/ems-sources`; a data file that git does not track is not missing. Inventory: `vault/Data inventory.md`. |
| Memory | `context-capsule load` (decision ledger `docs/CONTEXT_CAPSULE.md` + the plan's Status block); `graph-memory` (sqlite at `~/.local/share/ems-graph/graph_memory.sqlite`, export `docs/graph/graph_memory.jsonl`). Reconcile by `graph-memory export` here / `graph-memory import` there. |
| SQL | `ops/ems_duckdb.py "SELECT …"` — read-only views over the sources, aggregates only, outcome views filtered to the active sample. The Mac runs the same as an MCP server (`ems-duckdb`). |
| Vault | `vault/` (Obsidian-compatible; conventions in `vault/AGENTS.md`); the Mac vault is `~/Downloads/abrahimm/EMS`. |
| Runners | `ops/*.sh` with state under `ops/state/` (gitignored). |

## Install manifest (container)

```
python3 3.11.15; pip: pandas 3.0.5 numpy 2.4.6 scipy 1.17.1 statsmodels 0.15.0 pyfixest 0.60.0
pyarrow 25.0.1 duckdb 1.5.5 matplotlib 3.11.2 requests 2.33.1 pyyaml 6.0.1 tabulate 0.10.0 tqdm 4.70.1
uv (/root/.local/bin/uv); shims: ~/.local/bin/context-capsule, ~/.local/bin/graph-memory
```

To reproduce on another machine: `uv sync --frozen` (installs from `uv.lock`), then
`printf '#!/bin/bash\nexec python3 <repo>/ops/context_capsule.py "$@"\n' > ~/.local/bin/context-capsule`
and the same for `graph-memory` (`cd <repo>/ops && exec python3 -m graph_memory.cli "$@"`), then
`graph-memory import docs/graph/graph_memory.jsonl`.

## Rollback

- Tooling: delete `~/.local/bin/{context-capsule,graph-memory}`, `~/.local/share/ems-graph/`, `.venv/`; the
  repository files (`ops/graph_memory/`, `ops/context_capsule.py`, `ops/ems_duckdb.py`, `pyproject.toml`,
  `uv.lock`, `tests/`, `vault/`, `docs/CONTEXT_CAPSULE.md`, `docs/graph/`) are removed by reverting the commit
  that added them. Nothing in the analysis pipeline imports any of them.
- Data: `data/processed` is regenerable (`ops/coldrun.sh` defines "cold"); certificates and ledgers under
  `outputs/tables` are hours of compute and are kept across cold runs on purpose.

## Standing don'ts (both machines)

The legacy lag-7 result is superseded and is never restated as established; methods, lags, sample and outcome
definitions are not changed to make something significant; scripts 00/00b (network fetches) are not run
casually — 00b rebuilds from the page cache inside cold runs only; the graph-memory hooks are not installed.
