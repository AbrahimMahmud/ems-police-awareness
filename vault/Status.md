# Status — 2026-09-20 ~04:20Z

- **Gate**: 88 checks (X20 added), 87/87 PASS twice before it, baseline refreshed; 206 of 206 claims verify (commit `bbd146a`).
- **Freeze**: ACTIVE. No confirmation outcome has entered a model or test; declared accesses are listed in
  `docs/PAPER_MASTER.md` §5.3 (F1–F4).
- **Calibration**: C1 certified at 1,000 sims; discovery being extended from 719 to 1,000 (resumed 03:43Z after the
  week-long suspension); C2 follows from 200; pooled at 200 (descriptive).
- **Cold runs**: both passes clean; build/model outputs differed only at the byte level (hash randomization, finding X20); relaunched under a fixed seed so the manifests match to the byte.
- **Next**: [[Next actions]]. Plan of record: `docs/EXECUTION_PLAN.md` (Status block at the top).

Environment note: the container was suspended 2026-09-13 22:40Z → 2026-09-20 03:42Z (usage limit); the filesystem
survived, processes did not; runners were relaunched from `ops/`.
