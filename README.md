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
- **The legacy Twitter awareness measure was retired on 2026-09-08**
  (`docs/GATE_C_MEMO.md` §6.0): it is not re-fetchable, its collection
  methodology was never documented, and it is not defensible in print. The
  treatment variable is now CAI-D, built from Wikipedia victim pageviews and
  Google Trends. Twitter survives in one place only — the bridge result, where
  it is the object of the methods critique rather than a source of claims.
- **Consequence: the previously reported findings are superseded pending a
  re-run.** The suggestive decline in police-adjacent (EDP) call shares after
  awareness spikes was estimated on Twitter, and it does not reproduce under
  CAI-D at the same window (+0.00038, p=0.407 vs −0.00065, p=0.019). What
  survives the measure swap is weaker and two-sided: a first-week relationship
  between awareness and call composition (joint lags 0–7: p=0.041 EDP, p=0.006
  narrow-MH). Permutation inference on the discovery sample (p≈0.26 for the
  Twitter-era estimate) already indicated the sample cannot support a
  confirmatory claim; heterogeneity is non-monotonic and the exposure-intensity
  DID is underpowered. **Do not cite the earlier numbers as current.**

## Pipeline

```
scripts/
  config.py                   all constants (CD whitelist, call groups, lags, episodes)
  00_local_ems_extract.py     run locally against the raw 6.5GB EMS CSV
  01_build_panel.py           59-CD balanced panel, disaggregated call groups
  02_build_awareness.py       RETIRED Twitter measure — bridge/methods critique only
  02b_build_cai_lags.py       calendar-date lags/leads/windows for the CAI treatment
                              variables (the file every outcome model reads)
  03_main_model.py            full IRF, four-way SE table, calibrated joint tests
  03b_bridge_legacy.py        step-by-step attribution: original result -> corrected
  04_robustness.py            PPML counts, permutation inference, deferral test
  05_placebo_and_calls.py     outcome decomposition and placebo call types
  06_heterogeneity.py         demographics interactions/quartiles (ACS + 2010 vintages)
  07_did_exposure.py          exposure-intensity DID (heavily-Black vs even-distribution
                              districts primary, Q2 sensitivity — GATE_C_MEMO §6.4)
  08_figures.py               publication figures (read saved tables only)
  09_fetch_public_data.py     ACS 2015-19 demographics, Wikipedia pageviews (+ hash log)
  10_build_victim_registry.py victim/event registry (MPV + WaPo + curation reconcile)
  10d_parse_cd_demographics.py  legacy 2010 Census parser (kept for vintage comparison)
  11_fetch_awareness_components.py  wiki / GDELT news / GDELT TV daily series
  11b_fetch_trends.py         Google Trends daily series, US and NYC metro
  11c_trends_anchor_and_victims.py  weekly-anchored Trends + victim-name terms
  12_build_cai.py             CAI-D (treatment) and CAI-S (diagnostics), race-matched
                              sub-indices, and the validation battery
  16_bheard_exposure.py       B-HEARD confound control: precinct x CD crosswalk built
                              from the dispatch file itself, CD exposure step table
```

Run order: 00 (locally) → 01 → 09/10/11/12 (build CAI) → 02b → 03/04/05/06/07 → 08.
02 and 03b are the legacy/bridge track and are run only for the methods result.

## Data

All sources, access dates, hashes, and citation lines: `docs/DATA_PROVENANCE.md`
and `data/reference/data_sources.csv`. Raw inputs are gitignored; small
reference files (ACS demographics, Wikipedia pageviews, victim curation table,
CD whitelist) are committed. Twitter collection methodology is an open item
pending documentation from the data's originator.

## Documentation

- `docs/REWORK_PLAN.md` — issue register (I1–I19), design, review gates
- `docs/GATE2_PRELIMINARY_RESULTS.md` — findings memo, updated at each checkpoint
- `docs/GATE_C_MEMO.md` — decisions needed before the confirmatory run
- `docs/RELATED_WORK.md` — comparable studies, positioning, and what to borrow
- `docs/DATA_PROVENANCE.md` — source registry
