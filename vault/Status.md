# Status — 2026-09-21 ~03:50Z

- **Phase I sealed 2026-09-21 03:24:13Z** (`data/reference/confirmatory_results.csv` + `.meta.json`; 166 cells, 157 OK,
  9 IDENTICAL_TO_PRIMARY; 2,000 draws; `git_commit` b046fb6; PYTHONHASHSEED=0). Seven start rows in
  `confirmatory_run_log.csv` (container suspension, two OOM kills of the worker pool, worker-count changes; every row
  carries its reason; the sealed table's `overwrite_reason` carries the last one). Committed `34d4b9e`.
- **Reading** (`34_confirmatory_reading.py`, sealed, 175 rows): **the pre-specified null in both strata** (PAN 9.4 row 5,
  addendum §19 rule 2). C1 and C2 "does not reject"; sustained shift ≥ pre-freeze MDE (0.01156 / 0.00875) disfavoured at
  80% power; MEI −0.005 not excluded; transient dip-and-rebound of the MEI disfavoured (MDEs 0.00382 / 0.00290).
  Placebos quiet in both. Reported, not read as evidence: C1's smallest unadjusted p 0.0115; 14 of 24 C1 sensitivity
  cells at p ≤ 0.05 (0 of 30 in C2); C1 dose-response moves against the predicted direction (asymptotic p 0.03 / 0.02,
  outside the family). Pooled: does not reject on both arms (descriptive).
- **Manuscript**: PAPER_MASTER §8b and PAPER.md's confirmatory Results (reader's sentences quoted verbatim + Tables 2–6),
  Discussion (reading, implications) and Abstract (250 words, plan spec: dataset, place, period, linkage, design,
  three-way question) written from the reading only. 1,269 claims (206 + 1,056 generated + 7 prose) verify; every table
  cell covered. No PHASE I PENDING markers remain.
- **Gate**: 90 checks, 90/90 twice after the paste (a table label that began with a number and one citation-marker
  anchor were the only failures; fixed).
- **Open for the author**: word budget (~6,200 words vs ~4,000; Methods ~3,200 → Supplementary Methods proposal);
  reference 13 title to confirm; RECORD 6.2 validation comparison pending.
- **Next**: [[Next actions]]. Plan of record: `docs/EXECUTION_PLAN.md` (Status block at the top).

Environment note: compute advances only while a session is active; the worker pool fits at two workers (pooled 60-day
cells reach 5 GB each); runners in `ops/` are relaunched blind after a restart.
