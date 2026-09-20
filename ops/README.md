# ops — restart-tolerant runners for the long jobs

This environment is a managed container that is **suspended or reset whenever
the session is idle** and restarts with a fresh process table (uptime resets,
every background job dies, the filesystem survives). Measured on 2026-09-13: a
usage-limit pause of four hours advanced the calibration ledger by zero rows;
the container came back with `up 1 min` and no processes. So compute here
advances only while a session is active, and anything long must be (a)
checkpointed — every long script in this project is — and (b) driven by a
runner that can be relaunched blind and will skip what is already done.

The runners here are those. They used to live in a scratchpad directory that
does not survive the container, which is how the previous handoff pointed at
resume scripts that no longer existed.

    bash ops/rebuild.sh      # download → panel → 200-sim calibrations → discovery
                             # estimator at 500 draws → secondary models → power
    bash ops/calib1000.sh    # after rebuild: 1000-sim calibrations, all strata
    bash ops/coldrun.sh      # after rebuild: run_all twice from cold (definition in
                             # the script header) and compare the two manifests
    bash ops/phase_i.sh      # after the lift commit only: the sealed one-shot run
                             # (30, resumable per cell) then its mechanical reading
                             # (34 -> data/reference/confirmatory_reading.csv)

Each writes a PID file, a state file of completed steps, and a log under
`ops/state/` (gitignored). Poll them by PID file or sentinel — never `pgrep -f`,
which matches the shell whose command line contains the pattern.

## Memory and query tooling (2026-09-20)

    context-capsule load                       # decision ledger (docs/CONTEXT_CAPSULE.md) + the plan's Status block
    graph-memory search "<term>" --min-trust 0 # typed, cited memory nodes; sqlite at ~/.local/share/ems-graph/
    graph-memory export docs/graph/graph_memory.jsonl   # the git-tracked record; import on another machine
    python3 ops/ems_duckdb.py "SELECT ..."     # read-only, aggregate-only SQL over the sources (freeze-aware)
    python3 ops/paper_table1.py                # Table 1 (docs/tables/TABLE1_episodes.md), held by V.table1_regenerates
    python3 ops/phase_i_tables.py --out DIR [--docs docs/PAPER_MASTER.md docs/PAPER.md]
                                               # after Phase I: tables.md (the 8b tables, one claim per cell),
                                               # prose.md (the reader's sentences quoted verbatim, one claim per
                                               # sentence, anchored on its own prefix) and claims.csv; --synthetic
                                               # renders the dry run and its reading, and must not be pasted

`ops/graph_memory/seed.py` seeds the graph with the project's standing knowledge; `docs/LOCAL_SETUP.md`
describes the setup and how to mirror it on the Mac.
