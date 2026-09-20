# EMS × police-violence attention — project note

**Question.** Does public attention to police violence — measured by the CAI-D index (Wikipedia pageviews on a
basket of police-violence victims' articles + Google Trends) — change the share of NYC EMS dispatches that are
mental-health (EDP) calls, across the 59 community districts? Source of record: `docs/PAPER_MASTER.md`.

**Design.** Stacked episode event study with day −1 as reference; episode-level randomization inference as the
primary p-value; a discovery sample (2017–2020, explored) and a sealed confirmation sample (2015-07→2016-12 as C1
with 2021-01→05, and 2021-06→2024 as C2 under B-HEARD). See [[Design]].

**Where things are.**
- Pre-registration: `docs/PRE_ANALYSIS_NOTE.md`, `docs/CONFIRMATION_PLAN.md` (frozen text + numbered addendum).
- Master document: `docs/PAPER_MASTER.md`; manuscript: `docs/PAPER.md`; plan and status: `docs/EXECUTION_PLAN.md`.
- Registers: `docs/AUDIT_FINDINGS.csv` (findings), `docs/CLAIMS_REGISTER.csv` (every number in the paper),
  `docs/regression_baseline.csv` (the gate).
- Memory: `docs/CONTEXT_CAPSULE.md` (decision ledger), `docs/graph/graph_memory.jsonl` (graph export). See [[Tooling]].

Related: [[Decisions]] · [[Data inventory]] · [[Pipeline]] · [[Status]] · [[Next actions]]
