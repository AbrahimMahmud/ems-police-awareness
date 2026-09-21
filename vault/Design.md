---
tags: [design]
updated: 2026-09-21
---
# Design

- **Treatment.** Attention episodes: bursts of the CAI-D index under a shock rule with a within-year quantile
  threshold (`scripts/13_extension_episodes.py`); the adopted list `data/reference/confirmation_episodes_rebuilt.csv`
  (74 episodes) beside the frozen pre-registration list `confirmation_episodes.csv` (70, byte-identical). Table 1 of
  the paper is generated from both: `docs/tables/TABLE1_episodes.md` (`ops/paper_table1.py`).
- **Outcome.** EDP share of dispatches per district-day (and the narrow mental-health share), both as OLS on shares
  and PPML on counts with a log-total offset. Panel: `data/processed/panel_cd_day.parquet` (`01_build_panel.py`).
- **Estimator.** `scripts/event_study.py`: stacked event study, episode×district and day-of-week fixed effects,
  date-clustered SEs; the statistic is the joint Wald test on days 0–7; randomization inference draws placebo
  episode dates (anchor shift with gap permutation on contiguous strata; circular within-block shift, first-week
  admissibility, on gapped strata) — addendum §21, §24, §27.
- **Calibration precondition.** Every stratum's null is certified on synthetic panels built on the measured
  panel noise (`18_null_calibration.py`; `S.ri_scheme_certified`, `S.calibration_noise_measured`,
  `S.lift_requires_1000_sims`).
- **Family and reading.** Eight tests (2 outcomes × 2 arms × 2 strata), Benjamini–Hochberg q = 0.05; reading rules
  in `PRE_ANALYSIS_NOTE.md` §9 as amended by addendum §23 and §25, implemented in `34_confirmatory_reading.py`.
  Outside the family: the pooled estimate (descriptive), the sensitivities (ten specs, both arms), the placebos
  (cardiac, asthma; override on rejections only) and two secondary arms with asymptotic p only — the B-HEARD
  interaction (C2) and the dose-response arm (first-week effect per SD of peak intensity, addendum §9).
- **Power.** `19_power.py` → `data/reference/power_analysis_prefreeze.csv` (EDP share only): the pre-freeze
  minimum detectable effect per stratum for a sustained shift and a dip-and-rebound, read by §19 rule 2;
  addendum 23.11–23.12 state the bound's limitations (asymptotic Wald at nominal α vs BH-adjusted randomization p).
- **Freeze.** `scripts/freeze_guard.py`: exploratory scripts ask for the discovery window by name; only the sealed
  `30_confirmatory_run.py` reads the confirmation sample after `config.FREEZE_ACTIVE = False` (addendum §26).

Related: [[00 Project]] · [[Record]] · [[Phase I]] · [[Decisions]]
