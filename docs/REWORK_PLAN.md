# Analysis Rework Plan

This document is the complete specification for reworking the analysis pipeline.
It maps every identified issue to a concrete change in code, data, or documentation,
defines the new repository structure, and sets the order of work with review gates.

Issues are tracked with IDs (I1–I19) so commits and review comments can reference them.

---

## 0. Issue register

### A. Inference and identification (highest stakes)

| ID | Issue | Fix |
|----|-------|-----|
| I1 | Awareness varies only by day; district-clustered SEs ignore the common daily shock and overstate precision (effective N ≈ 1,461 days, not 85k district-days) | Primary inference: cluster by **date**. Also report: district-clustered (legacy), two-way CD×date, Driscoll–Kraay. One table, four columns. |
| I2 | Identification likely dominated by one 20.4σ outlier (Floyd episode) coinciding with COVID, curfews, protests, overdose surge | Leave-one-episode-out; drop May–Aug 2020; drop 2020 entirely; winsorized/log/rank awareness transforms |
| I3 | Lag-7 selected post hoc from many specifications; negative lag-1 undiscussed; no multiple-testing control | Pre-analysis note declaring primary spec + primary test (joint F on lags 0–7) before rerunning; BH correction across lags; full IRF reported regardless of significance |
| I4 | "DID" has no cross-sectional control group (treatment is a citywide day); overlapping event windows overwrite each other; event-study cells with zero SEs | Replace with exposure-intensity DID (Justin's design, §5.3); non-overlapping event window rules; drop cells with <k treated observations |

### B. Data construction

| ID | Issue | Fix |
|----|-------|-----|
| I5 | The two Twitter files are the same data at two granularities; pipeline sums them → every tweet counted twice | Use the daily file as the single source (verified: 1,459/1,461 days identical to per-victim aggregation); document as ONE dataset |
| I6 | Lags built with row-shift within district → misaligned wherever a district-day is missing | Build lags on a **date-level awareness table**, then merge to panel by calendar date |
| I7 | Panel contains 71 "districts"; NYC has 59. Codes like 164 (Central Park), 2xx/3xx/4xx park & airport joint-interest areas inflate the count | Whitelist: Manhattan 101–112, Bronx 201–212, Brooklyn 301–318, Queens 401–414, Staten Island 501–503 (=59). Reference file `data/reference/nyc_cd_valid.csv` |
| I8 | Z-score of a heavy-tailed count series; scale dominated by one outlier | Primary transform: log(1+tweets). Variants: z-score (comparability with old results), within-sample percentile rank, log(1+tweets+retweets) using `tweets_and_re` |
| I9 | Awareness ignores victim identity; race-specific salience untested | Victim-level indices: join per-victim counts to shootings db (exact → normalized name match → curated table `data/reference/victim_curation_table.csv`); produces `aware_black_victim`, `aware_other_victim`, coverage 99.2% of volume |
| I10 | MH definition mixes overdose/poison/drug with psychiatric calls; 2020 overdose surge confounds | Keep call types disaggregated in the panel; define `mh_broad` (current 11 codes), `mh_narrow` (EDP+ALTMEN family+suicide codes), and separate `edp`, `altmen`, `suicide_jump`, `od_poison_drug` outcomes |
| I11 | `total_calls` used as placebo but it is the outcome's denominator | Placebo outcomes with no plausible awareness channel: `cardiac` (ARREST/ARREFC/ARREFT/CARD/CARDFC/CARDFT/HEART/HEARTC/CVA*), `injury` (INJURY/INJMIN/INJMAJ/INJALS/MVAINJ/TRAUMA), `asthma` (ASTH*). Total calls promoted to a real outcome (see I13) |
| I12 | 2010 Census demographics for 2017–20 | Keep (time-invariant exposure), state limitation; optional later: ACS 2015–19 CD-approximation swap as robustness |

### C. Interpretation

| ID | Issue | Fix |
|----|-------|-----|
| I13 | EMS calls measure willingness-to-call, not distress. Negative effects in high-%Black districts are consistent with post-event 911 avoidance (Desmond, Papachristos & Kirk 2016), not lower distress. Current docs recommend shifting resources toward White/Asian districts — unsupported and potentially harmful | Help-seeking decomposition: EDP (police-adjacent) vs OD vs suicide vs placebo outcomes, by district demographic quartile. Total call volume as outcome with pre-trend checks (per Justin: "placebo no, pre-trends"). All policy text rewritten after results |
| I14 | Interaction model produced near-identical negative coefficients for all four race groups (they sum to ~100% — mechanical collinearity), contradicting the stratified results | Interactions estimated one demographic at a time, share centered per Justin's baseline convention (§5.4); never all four simultaneously |

### D. Integrity/consistency (all in one cleanup commit)

| ID | Issue | Fix |
|----|-------|-----|
| I15 | `16_difference_in_differences.py` fabricates SEs (`SE = 0.3×coef`) and hard-codes `is_sig=True` for the figure | Delete the block; the whole script is superseded by the new DID (I4) |
| I16 | Non-significant cumulative effect (0.00078 ± 0.00094) presented as key finding; "~33 calls/week" and "~4.7/day" derived from it; paper says "0.04 citywide/week" (mislabeled per-district-per-day) | Remove from README/docs (also per meeting note "3.1 take out per week 33"); recompute magnitudes only from estimates that survive corrected inference |
| I17 | N inconsistencies (84,547 vs 85,139), 59 vs 71 districts, paper date vs doc date | Single source of truth: `outputs/tables/sample_definition.csv` generated by the pipeline; all docs cite it |
| I18 | Scratch meeting notes embedded in RESULTS_INTERPRETATION.md (lines 167–172) | Remove; content lives in this plan (§5.3) |
| I19 | EMS_IMPLICATIONS_SUMMARY.md overclaims ("not spurious", staffing percentages) | Rewritten from scratch after Phase 3 results exist |

---

## 1. Target repository structure

```
ems-police-awareness/
├── data/
│   ├── raw/                          # gitignored inputs (documented in DATA_PROVENANCE.md)
│   ├── reference/                    # committed, small, hand-checked
│   │   ├── nyc_cd_valid.csv          # 59 valid CD codes + borough names
│   │   ├── victim_curation_table.csv # top-100 manual victim classifications [VERIFY: Abrahim]
│   │   └── call_type_groups.csv      # call code -> outcome group mapping (from data dictionary)
│   └── processed/                    # gitignored derived files
├── scripts/
│   ├── 00_local_ems_extract.py       # run locally against the 6.5GB raw CSV (done)
│   ├── 01_build_panel.py             # extracts -> CD-day panel with all outcome groups
│   ├── 02_build_awareness.py         # single-source awareness, variants, victim indices, calendar lags
│   ├── 03_main_model.py              # primary spec + full IRF + 4-way SE table + joint tests
│   ├── 04_robustness.py              # sample windows, leave-one-out, transforms, PPML, thresholds
│   ├── 05_placebo_and_calls.py       # placebo outcomes; total-calls-as-outcome with pre-trends
│   ├── 06_heterogeneity.py           # one-at-a-time interactions, quartiles, Black+Hispanic split
│   ├── 07_did_exposure.py            # Justin's exposure-intensity DID, with math in module docstring
│   ├── 08_figures.py                 # every publication figure regenerated from saved tables only
│   └── run_all.py                    # orchestrates 01-08, writes run manifest with data hashes
├── outputs/                          # gitignored; every table written as CSV with a generation stamp
└── docs/
    ├── REWORK_PLAN.md                # this file
    ├── PRE_ANALYSIS_NOTE.md          # written BEFORE Phase 2 estimation (I3)
    ├── DATA_PROVENANCE.md            # sources, versions, hashes, Twitter collection description [NEED: Justin]
    ├── METHODS.md                    # replaces METHODOLOGY.md after Phase 4
    └── RESULTS.md                    # replaces RESULTS_INTERPRETATION.md after Phase 4
```

Deleted after their replacements exist: scripts 01–26 (old numbering), METHODOLOGY.md,
RESULTS_INTERPRETATION.md, EMS_IMPLICATIONS_SUMMARY.md, NEW_METHODS_*.md,
HIGH_AWARENESS_*.md, AWARENESS_EVENT_DEFINITION.md, HETEROGENEOUS_EFFECTS_RESULTS.md,
FIGURES_TO_INCLUDE.md. Old research paper PDFs move to `docs/archive/`.

---

## 2. Phase 1 — data layer

### 2.1 `01_build_panel.py`
- Inputs: `ems_cd_day_calltype.parquet` (2016–2021), `ems_citywide_day_trends.parquet` (2005–2025).
- Filter to the 59 whitelisted CDs (I7); log dropped codes and their call volumes to the QC report.
- Pivot to CD × day with columns: `total_calls`, `mh_broad`, `mh_narrow`, `edp`, `altmen`,
  `suicide_jump`, `od_poison_drug`, `cardiac`, `injury`, `asthma` (mapping in
  `data/reference/call_type_groups.csv`, sourced from the official data dictionary sheet).
- **Balanced panel**: reindex to full CD × date grid; days with no calls get explicit zeros
  (needed for PPML and to make the ≥5-call share filter a modeled choice, not silent).
- Shares computed for each MH outcome; share set to NA where `total_calls < 5` (sensitivity
  at <3 and <10 in Phase 3).
- QC report `outputs/tables/qc_panel.csv`: old-vs-new row counts, per-CD call totals,
  reconciliation of every N that appears in any doc (I17).

### 2.2 `02_build_awareness.py`
- Single source: `220126_final_daily_tweet_count.csv` (I5), with an assertion that
  aggregating the per-victim file reproduces it (tolerance: the 2 known off-by-one days).
- Transforms (I8): `aware_log` = log(1+tweet_count) [PRIMARY]; `aware_z`; `aware_rank`;
  `aware_re_log` = log(1+tweets_and_re).
- Victim-race indices (I9): match per-victim file to shootings db — exact name →
  normalized name (strip suffixes/middle names) → curated table. Output daily
  `aware_black_log`, `aware_nonblack_log`, `aware_unclassified_share` (must stay ≤1%).
- **Calendar-date lag table** (I6): one row per date 2016-12-01..2021-01-31 with lags
  k = 0..28 and leads j = 1..14 for every variant; merged to the panel **by date**.
- Rolling-window means per Justin: `aware_w02` (days 0–2), `aware_w35`, `aware_w68`,
  `aware_w911`, `aware_w1214`.
- QC: correlation of new vs old awareness_z (expect ≈1 by construction), top-15 days
  table with victim attribution.

**Gate 1 review artifact:** `docs/DATA_PROVENANCE.md` + QC tables. Nothing in Phase 2
starts until Abrahim signs off (and Justin sees the provenance doc).

---

## 3. Phase 2 — pre-analysis note + core estimation

### 3.1 `docs/PRE_ANALYSIS_NOTE.md` (written first — I3)
Declares, before any corrected-data regression is run:
- **Primary outcome**: `mh_narrow` share (EDP + ALTMEN family + suicide codes; overdose
  excluded so the 2020 surge cannot drive it — I10).
- **Primary treatment**: `aware_log`, citywide.
- **Primary specification**: outcome ~ lags 0..28 + leads 1..14 + C(dow) + C(month):C(year)
  + CD FE; sample 2017-01-01..2020-12-31; 59 CDs; ≥5 calls.
  (Holiday indicator dropped from primary per meeting note "remove holiday fixed effect";
  reinstated as a Phase 3 sensitivity to show it does not matter.)
- **Primary test**: joint F-test that lag coefficients 0–7 are all zero, date-clustered.
- **Primary inference**: date-clustered SEs.
- Everything else in Phases 3–4 is labeled exploratory/robustness.

### 3.2 `03_main_model.py`
- Full IRF: all 29 lags + 14 leads plotted with date-clustered 95% CIs (meeting notes:
  "every k variable", "-14, -7, 0, 7, 14", "look at negative days" → leads are the
  pre-trend check: they should be ≈0).
- Rolling-window version (5 window coefficients) as the smoothed IRF.
- SE table (I1): identical point estimates under CD-cluster / date-cluster / two-way /
  Driscoll–Kraay(auto lag), so the paper can show exactly how inference assumptions
  change conclusions. Implementation: pyfixest (`feols`, vcov options) with a
  statsmodels cross-check on one spec.
- Progressive-controls table regenerated (meeting note: "do awareness only, see individual
  fixed effect, then all together") with date-clustered SEs throughout.
- All lag p-values reported raw AND Benjamini–Hochberg adjusted (I3).

**Gate 2 (decision point):** results memo to Abrahim + Justin. Framing of the paper is
decided here based on what survives.

---

## 4. Phase 3 — robustness (`04_robustness.py`, `05_placebo_and_calls.py`)

1. **Episode robustness (I2):** define awareness episodes as maximal runs of consecutive
   days with `aware_z > 1` merged if gaps < 7 days (expected: Stephon Clark 2018,
   Ferguson anniversary spikes, Floyd/Brooks May–Jun 2020, etc. — table of episodes with
   dates and attributed victims). Re-estimate primary spec dropping one episode at a time;
   plot coefficient stability. Plus: drop May–Aug 2020; drop all 2020; 2017–2019 only.
2. **Transform robustness (I8):** primary spec under aware_z / aware_rank / aware_re_log.
3. **Model robustness:** PPML count model, `mh_narrow` counts with log(total_calls)
   offset, CD FE + calendar controls, date-clustered (pyfixest `fepois`). NB2 as
   secondary. OLS-share vs PPML comparison table.
4. **Definition robustness (I10):** primary spec on mh_broad, edp-only, od_poison_drug-only.
5. **Sample robustness:** ≥3/≥5/≥10 call thresholds; balanced-panel zeros vs observed-only.
6. **Placebos (I11):** cardiac, injury, asthma shares under the primary spec — expected ≈0.
   COVID-marker call variants (FC/FT suffixes) tabulated separately as a COVID-disruption
   diagnostic, not pooled with placebos.
7. **Total calls as outcome (I13):** log(total_calls) and PPML around high-awareness
   episodes with leads (pre-trends) — testing Justin's hesitancy hypothesis directly.

---

## 5. Phase 4 — heterogeneity and DID

### 5.1 `06_heterogeneity.py` (I14)
- Interactions **one demographic at a time**: aware_log(lags) × pct_black, share centered
  at 50 (Justin: "our assumption is that 50% is baseline") so main effects read as the
  effect at a 50/50 district and the interaction as change per percentage point.
- Quartile-stratified analysis (as before, corrected inference).
- Binary split per meeting note: (pct_black + pct_hispanic) above/below median.
- Race-matched exposure: `aware_black_log` × pct_black — the identity-salience test (I9).

### 5.2 `07_did_exposure.py` — Justin's design (I4)
Treatment intensity is cross-sectional (district composition), event timing is temporal:

- **Treated**: districts in top quartile of pct_black ("heavily Black").
- **Control** (both variants reported): (a) Q2 districts per Justin; (b) "even-distribution"
  districts — bottom quartile of a demographic concentration index
  (Herfindahl over the four race shares).
- **Events**: high-visibility days = top decile of aware_log within 2017–2020, collapsed
  into episodes (§4.1); event day = first day of episode.
- **Windows** per meeting notes, two estimands:
  (i) day +7 vs day −1; (ii) mean of days +1..+7 vs mean of days −7..−1.
- **Specification** (math to be written out in the module docstring and METHODS.md):
  y_it = α_i + λ_t + β·(Treated_i × Post_t) + ε_it, within event windows,
  date-clustered SEs; event-time plot from −14..+14 with day −1 reference.
- Windows that overlap a subsequent episode are truncated at the new episode start
  (fixes the overwrite bug).
- Outcomes: mh_narrow share, edp share, od share, log total calls — the four together
  distinguish distress from help-seeking avoidance (I13).

### 5.3 Meeting-note traceability
Every note from the advisor meeting maps to: all-lags IRF (§3.2), leads (§3.2), rolling
windows (§2.2/§3.2), "take out 33/week" (I16), total-calls hesitancy (§4.7), disposition
87 = "cancelled" (documented in DATA_PROVENANCE.md), z-score wording + single-dataset
description (I5, DATA_PROVENANCE.md), holiday FE removal (§3.1), progressive FE table
(§3.2), Black/Hispanic split (§5.1), DID design + math + 50% baseline (§5.2).
Paper-formatting notes (Table 1 p-values, bring Table 1 up, §4.5 syntax) are parked
until the paper rewrite.

---

## 6. Phase 5 — documentation and cleanup

1. One commit deleting superseded scripts/docs (list in §1) — after replacements merged.
2. `METHODS.md` and `RESULTS.md` written fresh from Phase 2–4 outputs.
3. README rewritten: single Twitter source, 59 districts, corrected magnitudes, no claims
   from non-significant estimates (I15–I19 verified against a checklist in the PR).
4. `DATA_PROVENANCE.md` finalized — **needs from Justin: who collected the Twitter data,
   query/keyword definition, platform API used, any filtering.**

---

## 7. Reproducibility standards (apply to every new script)

- All constants (CD whitelist, code groups, thresholds, lag sets, dates) in one
  `scripts/config.py`; no magic numbers in analysis scripts.
- Every output table carries: script name, git commit hash, input-file SHA256, timestamp.
- `run_all.py` executes 01→08 and writes `outputs/run_manifest.json`.
- Figures only ever read from saved tables (no estimation inside plotting code — I15
  becomes structurally impossible).
- `requirements.txt` pinned exact versions; add `pyfixest`.

---

## 8. Sequencing and review gates

| Step | Owner | Blocked by |
|------|-------|-----------|
| Run 00 extract locally, upload 2 parquets | Abrahim | — |
| Verify curated victim rows (flagged low-confidence) | Abrahim | — |
| Twitter provenance from Justin | Abrahim | — |
| Phase 1 (01, 02, QC, provenance doc) | assisted | parquets |
| **Gate 1: data sign-off** | Abrahim (+Justin) | Phase 1 |
| PRE_ANALYSIS_NOTE.md | drafted for Abrahim's approval | Gate 1 |
| Phase 2 (03) | assisted | pre-analysis note approved |
| **Gate 2: results decision point** | Abrahim + Justin | Phase 2 |
| Phase 3 (04, 05) | assisted | Gate 2 |
| Phase 4 (06, 07) | assisted | Gate 2 |
| **Gate 3: full results review** | Abrahim + Justin | Phases 3–4 |
| Phase 5 (docs, cleanup, 08 figures) | assisted | Gate 3 |
| Paper rewrite | Abrahim | Gate 3 |

---

## 9. Open questions

1. Control-group choice for the DID: Q2 (Justin's suggestion) vs even-distribution
   districts — we implement both; which is *primary* should be Justin's call.
2. Primary outcome mh_narrow (proposed here) vs mh_broad (original): mh_narrow is the
   conservative choice given the overdose confound; confirm at Gate 1.
3. Whether to also swap 2010 Census for ACS 2015–19 (I12) — defer unless a reviewer asks.
4. Paper venue norms (affects how the pre-analysis note is framed) — decide at Gate 2.
