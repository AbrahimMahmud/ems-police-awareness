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

Both write a PID file, a state file of completed steps, and a log under
`ops/state/` (gitignored). Poll them by PID file or sentinel — never `pgrep -f`,
which matches the shell whose command line contains the pattern.
