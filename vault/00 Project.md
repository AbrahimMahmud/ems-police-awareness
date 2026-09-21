---
tags: [hub]
updated: 2026-09-21
---
# EMS × police-violence attention — project hub

**Question.** Does national public attention to police violence — the CAI-D index (Wikipedia pageviews on a
basket of police-violence victims' articles + Google Trends) — change the share of NYC EMS dispatches that are
mental-health (EDP) calls, across the 59 community districts? Source of record: `docs/PAPER_MASTER.md`;
manuscript: `docs/PAPER.md`.

**Answer (2026-09-21).** The sealed confirmatory run read by the pre-registered rules returns the pre-specified
null in both confirmation strata; the discovery result is a bounded null too. Numbers live in
`docs/PAPER_MASTER.md` §8b and `docs/PAPER.md` (Results), never here. See [[Phase I]].

## Map of content

| Area | Note | What it holds |
|---|---|---|
| Design | [[Design]] | Treatment, outcome, estimator, calibration, family, freeze |
| Data | [[Data inventory]] | Paths, schemas, row counts; the sealed artifacts |
| Pipeline | [[Pipeline]] | `run_all.py` stages, runners, what is not a stage |
| Record | [[Record]] | Pre-registration documents, the addendum, the summary table, the registers |
| Freeze | [[Freeze incidents]] | F1–F5: what was read, where disclosed |
| Result | [[Phase I]] | The sealed run, its seven starts, the reader, where the reading lives |
| Paper | [[Manuscript]] | `docs/PAPER.md` structure, claims, display items, open editorial items |
| Verification | [[Gate and checks]] | The 90-check gate, claims verification, register conventions |
| Audits | [[Audits]] | CP1, CP2 specification audits, CP3 (blind half and full), the findings they filed |
| Memory | [[Graph memory]] | The typed memory graph rendered as notes (`Graph/`) |
| Ledger | [[Decisions]] | Decisions with dates, mirrored from the capsule and the graph |
| Now | [[Status]] · [[Next actions]] | Current state and the ordered to-do |
| History | [[Timeline]] | Dated milestones with commits |
| Craft | [[Lessons]] | What went wrong and the rule each produced |
| Tools | [[Tooling]] | Capsule, graph, DuckDB, Python environment, this vault |
| Rules | [[AGENTS]] | Conventions for this vault |

**Where things are.**
- Pre-registration: `docs/PRE_ANALYSIS_NOTE.md`, `docs/CONFIRMATION_PLAN.md` (frozen text + numbered addendum §1–§30).
- Plan and status: `docs/EXECUTION_PLAN.md` (Status block at the top, session log at the bottom);
  handoffs `docs/HANDOFF_2026-09-13.md`, `_09-20.md`, `_09-21.md`.
- Registers: `docs/AUDIT_FINDINGS.csv` (findings), `docs/CLAIMS_REGISTER.csv` (every result number in the paper),
  `docs/regression_baseline.csv` (the gate), `data/reference/freeze_access_log.csv` (declared accesses).
- Memory: `docs/CONTEXT_CAPSULE.md` (decision ledger), `docs/graph/graph_memory.jsonl` (graph export).
