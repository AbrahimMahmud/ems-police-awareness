# Police-Violence Awareness and Emergency Help-Seeking in NYC

MIT UROP research project (Prof. Justin Steil, Department of Urban Studies and
Planning; student: Abrahim Mahmud) studying how public awareness of police
killings relates to mental-health-related EMS utilization across New York City's
59 community districts, 2017–2020.

**Status: under active rework.** The original analysis and its conclusions were
superseded in July 2026 after a full methodological audit; see
`docs/REWORK_PLAN.md` (issue register and design) and
`docs/GATE2_PRELIMINARY_RESULTS.md` (current findings and their limits).
Old scripts and documentation live in git history; old paper drafts in `docs/archive/`.

## Current state of findings (summary; see the memo for full detail)

- The original headline (a positive lag-7 effect of awareness on mental-health
  call share) **replicates but is not robust**: it depends on outlier leverage
  in a z-scored awareness measure and disappears under a log transform.
- The corrected analysis shows a **suggestive decline in police-adjacent (EDP)
  mental-health call shares in the ~5 days after awareness spikes**, with
  placebo call types null and injury calls rising — a pattern consistent with
  help-seeking avoidance (Desmond et al. 2016). It survives outlier and
  2020-exclusion stress tests, but **permutation inference (p≈0.26) indicates
  it cannot currently be distinguished from chance at conventional thresholds**
  given only 12 awareness episodes. Heterogeneity across districts is
  non-monotonic; the exposure-intensity DID is directionally consistent but
  underpowered.

## Pipeline

```
scripts/
  config.py                   all constants (CD whitelist, call groups, lags, episodes)
  00_local_ems_extract.py     run locally against the raw 6.5GB EMS CSV
  01_build_panel.py           59-CD balanced panel, disaggregated call groups
  02_build_awareness.py       single-source Twitter measure, victim-race indices,
                              calendar-date lags/leads, episode table
  03_main_model.py            full IRF, four-way SE table, calibrated joint tests
  03b_bridge_legacy.py        step-by-step attribution: original result -> corrected
  04_robustness.py            PPML counts, permutation inference, deferral test
  05_placebo_and_calls.py     outcome decomposition and placebo call types
  06_heterogeneity.py         demographics interactions/quartiles (ACS + 2010 vintages)
  07_did_exposure.py          exposure-intensity DID (heavily-Black vs Q2/even districts)
  08_figures.py               publication figures (read saved tables only)
  09_fetch_public_data.py     ACS 2015-19 demographics, Wikipedia pageviews (+ hash log)
  10d_parse_cd_demographics.py  legacy 2010 Census parser (kept for vintage comparison)
```

Run order: 00 (locally) → 01 → 02 → 03/03b/04/05/06/07 → 08.

## Data

All sources, access dates, hashes, and citation lines: `docs/DATA_PROVENANCE.md`
and `data/reference/data_sources.csv`. Raw inputs are gitignored; small
reference files (ACS demographics, Wikipedia pageviews, victim curation table,
CD whitelist) are committed. Twitter collection methodology is an open item
pending documentation from the data's originator.

## Documentation

- `docs/REWORK_PLAN.md` — issue register (I1–I19), design, review gates
- `docs/GATE2_PRELIMINARY_RESULTS.md` — findings memo, updated at each checkpoint
- `docs/DATA_PROVENANCE.md` — source registry
