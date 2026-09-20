# Status — 2026-09-20 ~06:00Z

- **Gate**: 90 checks, 90 PASS twice at 05:52Z, baseline refreshed; 206 of 206 claims verify. Every new check defeat-tested
  (ALPHA, the asthma override, a missing placebo p, the dose sign, the unfiltered panel, the path columns, row 3, "No COVID",
  19's docstring — each mutation fails its check; restored).
- **Third specification audit remediated** (P27–P58, addendum §30, rules 23.1c/d/e): 57 raw findings → 5 confirmed, 5 killed,
  6 critic items; everything surviving fixed in code or record before the lift. See [[Decisions]].
- **Freeze**: ACTIVE. No confirmation outcome has entered a model or test; declared accesses F1–F4 in `PAPER_MASTER.md` §5.3.
- **Calibration**: discovery certified at 1,000 sims (05:10Z: rejection 0.045, KS p 0.2944); C1 at 1,000 (0.049, 0.9930);
  C2's 1,000-sim run started 05:15Z (~3 h; 200-sim certificate CALIBRATED meanwhile); pooled at 200 (descriptive).
- **Panel**: rebuilt with eight new columns (EDPM, EDP-ex-EDPM, cancelled-inclusive totals/counts/shares); every existing
  column byte-identical. Coverage-break table unchanged under the inclusive boundary rule.
- **Cold runs**: relaunched 05:58Z (two passes from cold; the manifest and registers are committed when they agree).
- **Dry run**: 166 cells at 20 draws on the final code, sidecar hashes match every source; the reader reads it (175 rows).
- **Next**: [[Next actions]]. Plan of record: `docs/EXECUTION_PLAN.md` (Status block at the top).

Environment note: compute advances only while a session is active; runners in `ops/` are relaunched blind after a restart.
