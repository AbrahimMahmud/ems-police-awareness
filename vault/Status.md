# Status — 2026-09-20 ~04:40Z

- **Gate**: 89 checks, 89 PASS twice at 04:38Z, baseline refreshed; 206 of 206 claims verify (commit `84411f6`).
- **Freeze**: ACTIVE. No confirmation outcome has entered a model or test; declared accesses are listed in
  `docs/PAPER_MASTER.md` §5.3 (F1–F4).
- **Calibration**: C1 certified at 1,000 sims; discovery being extended from 719 to 1,000 (resumed 03:43Z after the
  week-long suspension); C2 follows from 200; pooled at 200 (descriptive).
- **Cold runs**: under the fixed seed every build and model output is byte-identical across two passes (COLD IDENTITY OK, 04:36Z); a final double pass is running so the committed manifest carries a clean pass 2.
- **Figures**: the manuscript's figures are tracked copies in `docs/figures/` (X21).
- **Next**: [[Next actions]]. Plan of record: `docs/EXECUTION_PLAN.md` (Status block at the top).

Environment note: the container was suspended 2026-09-13 22:40Z → 2026-09-20 03:42Z (usage limit); the filesystem
survived, processes did not; runners were relaunched from `ops/`.
