---
tags: [result, phase-i]
updated: 2026-09-21
---
# Phase I — the sealed confirmatory run

**What it is.** `scripts/30_confirmatory_run.py` run once after the lift (`4e3dce1`, 2026-09-20), through the
certified machinery in `scripts/event_study.py`, at 2,000 randomization draws per cell, and read once by
`scripts/34_confirmatory_reading.py` (the pre-registered rules as code; see [[Record]] §23). The reading is the
paper's confirmatory Results, quoted verbatim; nothing here restates a number.

**The result, in words.** The pre-specified null in both confirmation strata (PRE_ANALYSIS_NOTE 9.4 row 5, read
by addendum §19 rule 2): no primary cell rejects after the family correction; the falsification outcomes are
quiet; a sustained shift at or above the pre-freeze minimum detectable effect is disfavoured at 80% power, the
minimum effect of interest is not excluded, a transient dip-and-rebound of that size is disfavoured. Reported and
not read as evidence: C1's sensitivity pattern and its positive dose-response arm. Where the numbers are:
`docs/PAPER_MASTER.md` §8b, `docs/PAPER.md` Results (Tables 2–6), `data/reference/confirmatory_reading.csv`.

**Artifacts (tracked, `data/reference/`).**

| file | rows | columns |
|---|---|---|
| `confirmatory_results.csv` | 166 cells (157 estimated, 9 `IDENTICAL_TO_PRIMARY`) | 36: stratum, outcome, estimator, spec, family, bheard_bound, episode_set, n_episodes, n_districts, post_window, draw_post_window, first_week_chi2, first_week_mean_coef, first_week_mean_se, path_coefs, path_ses, …, p_randomization, p_asymptotic, p_bh_adjusted, ri_scheme, n_draws, status, note, null_certified, calibration_sims, overwrite_reason |
| `confirmatory_results.meta.json` | sidecar | script/estimator code hashes, `source_sha256` (30, event_study, freeze_guard, config, bheard), `inputs_sha256` (panel, three episode lists, coverage breaks, B-HEARD exposure, the three calibration certificates), git commit, hash seed, draws, jobs, written_utc |
| `confirmatory_run_log.csv` | 8 (7 `start`, 1 `sealed`) | utc, event, git_commit, source hashes, panel hash, draws, jobs, pythonhashseed, overwrite_reason, output_sha256, rows |
| `confirmatory_reading.csv` (+ `.meta.json`) | 175 | stratum, item, value, rule, detail, data_source |
| `power_analysis_prefreeze.csv` | 276 | metric, value (the pre-freeze MDE table, EDP share only) |

Cells by stratum and family: C1 — 4 primary, 36 sensitivity, 6 placebo, 3 diagnostic, 2 secondary; C2 — 4, 37,
6, 3, 6; pooled (descriptive) — 4, 44, 6, 3, 2.

**The seven starts** (2026-09-20 09:29Z → 2026-09-21 03:24Z, wall clock 17 h 55 min): the original start; a resume
after the container suspended five minutes into the session's idle time; the runner's automatic retry after the
first out-of-memory kill (four workers) and the hand relaunch with two; a relaunch with three workers for speed;
the automatic retry after the second kill (three workers on the pooled 60-day cells) and the hand relaunch with
two. The hand relaunches carry their reasons in the run log; the automatic retries repeat the preceding reason;
the first start carries none; the sealed table's `overwrite_reason` carries the last. Source hashes are identical
across all seven; every cell resumed from its identity-keyed ledger, so no number depends on the restarts.

**Run it again?** Never by hand: a second real start needs `--overwrite-sealed-result REASON` (runner variable
`PHASE_I_RESUME_REASON`) and the reason is recorded. Tables and prose regenerate from the sealed files with
`ops/phase_i_tables.py` (see [[Manuscript]]).

Related: [[00 Project]] · [[Design]] · [[Manuscript]] · [[Timeline]] · [[Lessons]]
