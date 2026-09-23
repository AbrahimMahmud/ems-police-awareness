# ops — runners and generators

The long jobs run in a container that may be suspended between sessions, so every long script in this
project checkpoints its work and every runner here can be relaunched and will skip what is already done.

    bash ops/rebuild.sh      # download → panel → 200-simulation calibrations → discovery estimator at 500
                             # draws → secondary models → power
    bash ops/calib1000.sh    # after rebuild: 1,000-simulation calibrations, all strata
    bash ops/coldrun.sh      # after rebuild: run the pipeline twice from cold and compare the two manifests
    bash ops/phase_i.sh      # the sealed one-shot confirmatory run (30, resumable per cell) and its
                             # mechanical reading (34 → data/reference/confirmatory_reading.csv); a relaunch
                             # takes PHASE_I_RESUME_REASON="why", written into the run log and the table

Each writes a PID file, a state file of completed steps and a log under `ops/state/` (not tracked).

## Generators for the manuscript

    python3 ops/paper_table1.py                    # the episode list (docs/tables/TABLE1_episodes.md)
    python3 ops/phase_i_tables.py --docs docs/PAPER_MASTER.md docs/SUPPLEMENT.md --out ops/state/phase_i_tables_supp
                                                   # the sealed run's tables and the reading's transcript
    python3 ops/paper_confirmatory_tables.py --out ops/state/paper_tables   # Tables 1 and 2 of the paper
    python3 ops/supplement_tables.py --out ops/state/supplement_tables     # Tables S7–S10
    python3 ops/refresh_generated_claims.py        # replace the generated rows of docs/CLAIMS_REGISTER.csv
    python3 ops/paste_generated.py docs/SUPPLEMENT.md docs/PAPER.md        # paste the generated regions
    python3 ops/paper_figures.py                   # copy the manuscript's figures into docs/figures

Every generated number carries a claim; the regression suite (`scripts/23_regression_suite.py`) holds the
documents to the generators' output.
