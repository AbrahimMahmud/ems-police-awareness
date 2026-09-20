# Context capsule — the decision ledger

*Load with `context-capsule load` (ops/context_capsule.py); append with `context-capsule add "…"`.
Each entry is a decision with its reason and where it is recorded. The current state lives in the
Status block of `docs/EXECUTION_PLAN.md`, which `load` prints after this ledger. The memory graph
(`graph-memory search <term> --min-trust 0`; export in `docs/graph/graph_memory.jsonl`) holds the same
decisions as typed, cited nodes.*

## Standing (from the pre-registration and the plan)

- **The freeze.** No script reads confirmation-window outcomes (2015-07→2016-12, 2021→2024) except the
  declared accesses in `config.FREEZE_EXEMPTIONS` (logged) and the sealed `30_confirmatory_run.py` after
  `config.FREEZE_ACTIVE = False`. `confirmation_episodes.csv` stays byte-identical. — `freeze_guard.py`,
  PAPER_MASTER §5.2–5.3.
- **The gate.** Every change passes `23_regression_suite.py` (twice) before the next; a new check gets a
  defeat attempt; the baseline is refreshed in the same commit; artifact-pending failures are written into
  EXECUTION_PLAN rather than waved through. — EXECUTION_PLAN "Standing rules".
- **Numbers.** No number reaches the paper without a `CLAIMS_REGISTER.csv` entry that reproduces it;
  generated tables are held by re-rendering. — `31_verify_sources.py`, `V.*` checks.
- **Reading rules are fixed before results exist**, and since 2026-09-13 they are code
  (`34_confirmatory_reading.py`). — CONFIRMATION_PLAN addendum §19, §23, §25.
- **Superseded results stay superseded.** The legacy lag-7 result is never restated as established; no
  specification, lag, sample or outcome change is made to recover a result.

## Ledger

- **2026-09-13 (user)** — Continue to Phase I as pre-registered, the reading of a non-rejection fixed in
  advance against the measured power. Reason: the design is powered for the transient shape the mechanism
  work predicts; a one-shot test whose reading is fixed cannot be made worse by being run. — addendum §19.
- **2026-09-13 (user)** — Work on `analysis-rework`, commits authored Abrahim Mahmud, no AI attribution;
  deliverable a Markdown manuscript in the repo (`docs/PAPER.md`) with the repo at CP3.
- **2026-09-13 (user)** — O2 coverage diagnostic: disclose first (addendum §18), then run as a declared access.
- **2026-09-13** — Addendum §25: pre-registered fallback if a stratum's null fails at 1,000 sims. Written at
  18:00Z after C1 failed at 200 under the corrected drawer, before the 1,000-sim verdict; C1 then calibrated
  (0.049 / KS p 0.993), so §25 is not invoked.
- **2026-09-13** — The reading is code (34) held to planted tables; the placebo override is cardiac and
  asthma (injury reported, not overriding); the sealed script estimates the 28/60-day windows and the dose
  arm it had promised (addendum §29). — findings P14, P19–P26.
- **2026-09-13** — After the lift only the sealed script reads the confirmation sample; exploratory scripts
  pin the discovery window by name (addendum §26, finding D8).
- **2026-09-13** — 18 refuses to calibrate on assumed noise (finding N11) after a near-miss caught by the
  ledger identity check.
- **2026-09-20** — Discovery p-values reported at the pre-specified 2,000 draws (updater-moved; prose
  amended). Gate 87/87 clean, 206/206 claims; baseline refreshed. — commit bbd146a.
- **2026-09-20** — Repo-tracked equivalents of the Mac-side tooling built here (`ops/graph_memory`,
  `ops/context_capsule.py`, `vault/`, `pyproject.toml` + `uv.lock`, `tests/`, `docs/LOCAL_SETUP.md`), so
  every environment carries the same memory; the Mac copies are to be reconciled by import/export.

## Open

- The Registered Report route (PAPER_MASTER §10) is foreclosed by Phase I — the supervisor's call, stated.
- The specification audit's refutation phase has not completed on any run (usage limits); the eight
  findings of the one completed finder were acted on; a run on the Opus model is in flight (2026-09-20).

- **2026-09-20 04:18Z** — X20: cold passes differed at the byte level (1e-16 coefficients, 1e-11 SEs) from Python hash randomization; run_all and the runners now fix PYTHONHASHSEED=0 and one BLAS thread; the cold comparison requires identity for build/model outputs and lists the check stages' timestamped reports separately. No reported number changed.

- **2026-09-20 04:39Z** — X21: the manuscript's figures are tracked copies in docs/figures held byte-for-byte to the pipeline output (V.paper_figures_current). Cold identity confirmed at 04:36Z: every build and model output byte-identical across two passes under the fixed seed; the check stages' reports differ only by timestamp.

- **2026-09-20 05:54Z** — 2026-09-20 (assistant, under the user's standing mandate) — Third CP2 specification audit remediated in full before the lift: findings P27–P58 (addendum §30; rules 23.1c/d/e). Sealed run: tracked run log + PYTHONHASHSEED=0 required, certificate-vs-design gate, 14-day draw geometry for the 28/60-day cells, unfiltered diagnostics, cross-window coverage-clean + geocoding-only cell, cancelled-inclusive and no-EDPM cells on both arms, day-by-day path columns, pinned sidecars. Reader: sealed with a sidecar, tracked pre-freeze power table, enumerated sensitivity set, pooled and secondary readings, placebo check cannot fail open. Reason: every item was blind and either closes a way the seal could be defeated or a rule the reading could not follow from the table alone; no specification, lag, sample or outcome definition changed. — AUDIT_FINDINGS P27–P58, CONFIRMATION_PLAN §30.

- **2026-09-20 05:54Z** — 2026-09-20 (assistant) — Record corrections from the same pass: summary row 3 marked non-blind (§14); C1 described as clean of B-HEARD with its 2021 block inside COVID; PAPER_MASTER §6 states the strata the code estimates; B-HEARD covariate numbered as row 30; §18, F4 and §20 wording; 62,920 → 77,506 (542 × 143 under first-week containment); 19/18/event_study docstrings; PAPER_MASTER §5.3 says the external pre-registration remedy is foreclosed by the lift and that proceeding is the author's 2026-09-19 decision. Held by S.third_pass_record_consistency. — CONFIRMATION_PLAN §30 P46–P53, P58.

- **2026-09-20 05:54Z** — 2026-09-20 (assistant) — Discovery certified at 1,000 sims (05:10Z: rejection 0.045, KS p 0.2944); §7.4 and the claims updated (C70/C121 re-anchored at three decimals). Gate 90/90 twice (05:52Z), baseline refreshed, 206/206 claims; every new check defeat-tested. C2's 1,000-sim run started 05:15Z; cold passes relaunched 05:58Z after the panel gained eight columns (existing columns byte-identical). — EXECUTION_PLAN Status.

- **2026-09-20 09:26Z** — 2026-09-20 (assistant) — Incident F5 at the lift: the first gate run with FREEZE_ACTIVE = False (made to verify the lifted state before committing it) selected the confirmation sample in three suite checks that derived their sample from the flag (S7, S8, X6; the suite had been exempt from D8's scan). Printed: 0 shared district-days, residual AR(1) 0.0622 vs 0.0482, max |coef difference| 6.117e-05, exposure max 1 — nothing of H1. Disclosed in addendum §15 and PAPER_MASTER §5.3; the checks pinned by name; the suite now scanned by D8; the flag committed only after a clean lifted gate. — AUDIT_FINDINGS F5.

- **2026-09-20 10:43Z** — 2026-09-20 (assistant) — Phase I babysitting rule: the container suspended the sealed run five minutes after the session went idle (09:36:54Z); relaunched 10:34:50Z with PHASE_I_RESUME_REASON, which 30 records as the second start's reason in the run log and in every row of the sealed table; ledgers resumed (no number depends on the restart). Long runs are watched from an active session. — EXECUTION_PLAN session log; ops/README.
