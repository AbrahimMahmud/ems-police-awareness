---
tags: [verification, gate]
updated: 2026-09-21
---
# The gate and the registers

**`scripts/23_regression_suite.py`** — 90 checks, baseline `docs/regression_baseline.csv` (states only; `--baseline`
rewrites it from a clean run; unbaselined or retired checks fail the run). Families by prefix: T treatment (26),
S specification and sealed run (24), D design and freeze (11), V verification and claims (9), E episodes (8),
X infrastructure (6), O outcome (3), M meta (3). Run from `scripts/` with `PYTHONHASHSEED=0` and one BLAS thread;
run twice after every change; every new check or token gets a defeat attempt (plant the defect, the check must
fail, restore).

**Checks worth knowing by name.**
- `V.claims_reproduce` — every row of `docs/CLAIMS_REGISTER.csv` renders its template in its document and the
  expression over the artifact reproduces the number (`scripts/31_verify_sources.py`; `--update-claims` rewrites
  the document from the artifact).
- `V.claims_cover_exhibits` — every numeral-leading cell of every markdown table in PAPER_MASTER and PAPER sits
  inside some claim's captured group; ISO dates and year spans are labels; numeral-leading labels are values.
- `S.third_pass_record_consistency` — text tokens holding the record's corrected wording (P46–P58 from the third
  specification audit; P59–P63 from CP3: the incident nouns, what was kept, "before any outcome was seen", the
  bias direction, the note's §4 table, the master's §5.3 heading).
- `S.confirmatory_spec_audit`, `S.confirmatory_reading_rules` — exact-line tokens in 30 and 34 and 32 planted
  reading tables (P14–P58).
- `D.discovery_scripts_pinned` (D8, F5) — every exploratory reader, the suite included, selects the discovery
  window by name; `D.incident_disclosed` — F1–F5 named in PAPER_MASTER §5.3; `D.addendum_complete` — the frozen
  text untouched and every finding whose fix says "addendum" discussed there.
- `M.register_sync` — the register's `checks` column equals the suite's tags; `M.status_honest` — no finding is
  `fixed` while its check fails.
- `V.table1_regenerates`, `V.paper_figures_current`, `X.run_all_deterministic_env`, `V.artifacts_current`,
  `V.sources_verified`.

**Register conventions.** CSVs are CRLF and written through the csv module (templates may wrap across a newline
inside the quoted field); never edited while a cold pass runs; findings carry id, dimension, severity, status,
checks, title, votes, fix, claim, corrected_claim; a fix that mentions "addendum" must be named in
CONFIRMATION_PLAN §30. Generated claims (note names `ops/phase_i_tables.py`) are replaced wholesale.

**Counts (2026-09-21).** 90/90 checks; 1,354/1,354 claims; 164/164 findings fixed.

Related: [[00 Project]] · [[Pipeline]] · [[Manuscript]] · [[Audits]] · [[Lessons]]
