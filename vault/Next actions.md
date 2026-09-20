# Next actions

1. Cold passes match (COLD IDENTITY OK) → commit `outputs/run_manifest.json` and the registers the cold run rewrites.
2. C2's 1,000-sim certificate lands → `S.lift_requires_1000_sims` satisfied → PAPER_MASTER §7.4 (all four rows, the
   "discharged at" sentence) and PAPER.md's calibration prose updated through the claims → gate clean → baseline.
3. The lift: `config.FREEZE_ACTIVE = False` in one greppable commit (`data/reference/power_analysis_prefreeze.csv` is
   already tracked); `ops/phase_i.sh` (PYTHONHASHSEED=0; 30 at 2,000 draws, run log; then 34 once).
4. `ops/phase_i_tables.py` → PAPER_MASTER §8b and PAPER.md Results/Discussion/Abstract with claims; CP3 audit;
   EXECUTION_PLAN session log; HANDOFF; reconcile this vault and graph with the Mac copies.

Closed this session: the third specification audit's refutation phase completed (wf_f524dc75, 39 agents) and its
findings are remediated (P27–P58). The Registered Report route is foreclosed by the lift; PAPER_MASTER §5.3 records
that proceeding is the author's decision (P58).

See [[Status]] · [[Decisions]]
