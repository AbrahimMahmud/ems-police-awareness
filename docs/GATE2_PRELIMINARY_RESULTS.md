# Gate 2 preliminary results memo

First full run of the corrected pipeline on real data (extracts of the NYC EMS
dispatch file, 59 districts, 2017–2020). This memo is the decision-point input
for the paper's framing. Tables referenced are in `outputs/tables/`.

## 1. The legacy result replicates, then fails a specific stress test

Bridge table (`bridge_legacy_to_primary.csv`), changing one element at a time:

| Step | lag-7 coef | p | Joint lags 0–7 p |
|---|---|---|---|
| 1. Legacy replica (mh_broad, z-score, sparse lags, CD cluster) | 0.00147 | 0.0002 | 0.001 |
| 2. + date clustering | 0.00147 | <0.0001 | <0.0001 |
| 3. + all lags & leads | 0.00124 | 0.004 | <0.0001 |
| 4. **+ log transform** | **−0.00029** | **0.59** | **0.29** |
| 5. + narrow MH outcome (= corrected primary) | 0.00041 | 0.27 | 0.028 |

Two surprises relative to expectations:
- **Date clustering did NOT weaken the legacy result** (concern I1 did not bite).
- **The result is destroyed by measuring awareness in logs instead of z-scores**
  (step 4). The z-scored measure gives the Floyd outlier (z = 20.4) ~10x the
  leverage of any other episode; the lag-7 "effect" is fit to that single point.
  corr(aware_log, aware_z) = 0.61.

Conclusion: the original headline — a positive lag-7 effect of awareness on the
broad MH call share — is **not robust**. It is an artifact of outlier leverage
in the awareness transform.

## 2. What the corrected data actually show

Primary spec (mh_narrow share, aware_log, full lags+leads, date-clustered):
- No individual lag significant after BH correction; lag 7 p = 0.27.
- **Joint lags 0–7 test: p = 0.028**, and it **survives excluding the Floyd
  episode (p = 0.068) and excluding 2020 entirely (p = 0.007)**. There is a
  first-week relationship; it is just not a lag-7 spike.
- Pre-trends clean (mean-of-leads p = 0.19; 2/14 leads nominally significant ≈ chance).

Shape of the relationship (binned windows, each window entered alone):
- days 0–2: **−0.00048 (p = 0.047)**
- days 3–5: **−0.00058 (p = 0.030)**
- days 6–8: +0.00043 (p = 0.12) — a partial rebound, significant only conditionally
- days 9–14: ≈ 0

The robust sign is **negative**: higher awareness predicts a *lower* narrow-MH
call share in the following ~5 days.

## 3. Decomposition points at help-seeking, plus a protest-injury channel

Effect of the day-3–5 awareness window by outcome (each alone, date-clustered):

| Outcome | coef | p |
|---|---|---|
| EDP share (police-adjacent) | −0.00051 | 0.037 |
| ALTMEN share | −0.00008 | 0.47 |
| Suicide-related share | +0.00001 | 0.75 |
| OD/poison/drug share | +0.00023 | 0.45 |
| Cardiac share (placebo) | −0.00005 | 0.83 |
| Asthma share (placebo) | −0.00002 | 0.70 |
| **Injury share** | **+0.00098** | **0.062** (days 0–2: +0.00123, p = 0.015) |
| log total calls | ≈ 0 | 0.54 |

- The MH-share decline is concentrated in **EDP** — precisely the call type
  that brings police — while suicide-related and OD calls are flat and the
  pure placebos are null. This is the signature of **help-seeking avoidance**
  (Desmond, Papachristos & Kirk 2016), the mechanism Justin flagged
  ("lower hesitancy to call 911 after event").
- **Injury calls rise** in days 0–2 — consistent with protest-related injuries
  during high-awareness periods. This also means share outcomes are partly
  compositional (injury growth mechanically depresses other shares); EDP
  *counts* are negative but not significant (p = 0.41), so the avoidance
  evidence is suggestive, not conclusive, pending the DID.

## 4. Proposed reframing (for discussion with Justin)

From: "awareness of police killings increases mental-health EMS calls with a
7-day delay" (not supported by corrected analysis).

To: "high-profile police-violence awareness shifts what communities ask EMS
for: police-adjacent mental-health (EDP) call shares fall in the week after
awareness spikes while injury calls rise; we find no robust evidence of an
overall increase in mental-health EMS utilization."

Decisive next test (Phase 4): does the EDP decline concentrate in heavily
Black/Hispanic districts? That is exactly Justin's exposure-intensity DID, and
the race-matched awareness index (aware_black_log) is built and ready.

## 5. Caveats

- Everything beyond the pre-registered primary test (joint lags 0–7) is
  exploratory and must be labeled as such in the paper.
- Window-level results shown "alone" and "jointly" differ because adjacent
  windows correlate at 0.8; both are reported.
- Count models (PPML) and the DID remain to be run before conclusions harden.

## 6. Checkpoint update (2026-07-12): call-type audit, outlier robustness, data augmentation

1. **Call-type audit** (user-requested): EDPC (140k calls, phased in mid-2018 as a
   recode of EDP), EDPM, EDPW, T-EDP added to the EDP family; OD/ODC/POISON/JUMPDC
   confirmed absent from 2016-2021 (legacy codes). With the corrected family the
   days-3-5 EDP suppression strengthens to -0.00065 (p=0.019).
2. **Outlier sensitivity resolved**: Floyd episode = 3.2% of days, 28.9% of
   regressor variance (log scale), but the suppression estimate is invariant:
   drop-Floyd -0.00063 (p=0.031), drop-2020 -0.00115 (p<0.001), winsorized
   unchanged. Unlike the legacy lag-7 result, current findings are not
   outlier-driven.
3. **Environment/network change**: the analysis environment's network policy was
   updated on 2026-07-12 to allow api.census.gov, wikimedia.org,
   data.cityofnewyork.us, and trends.google.com so public augmentation data
   (ACS 2015-19 CD demographics, Wikipedia pageviews, NYC Well/311/NYPD CFS)
   can be fetched directly. Policy applies to runs started after the change;
   fetches run via scripts/09_fetch_public_data.py.
4. **Single-event view**: raw Floyd-only comparison vs 2017-19 calendar baseline
   shows EDP share breaking ~0.8pp below its own pre-event level in the three
   weeks after May 25, 2020 while injury shares rise 2-3pp -- the regression
   signature, visible without a model.

## 7. Checkpoint update: Phase 3-4 complete (heterogeneity, DID, counts, permutation)

1. **Vintage question resolved**: ACS 2015-19 vs Census 2010 demographics are
   nearly interchangeable at the CD level (corr 0.993 on %Black; 6/59 quartile
   switches; results identical to 3 decimals). ACS is primary; 2010 is the
   robustness appendix.
2. **Heterogeneity is non-monotonic**: the EDP suppression appears in the
   whitest quartile (Q1: -0.00108, p=0.02) and the two Blackest (Q3/Q4:
   ~-0.00074, p~0.09) but not Q2. Continuous interactions slope negative
   (Black+Hispanic x awareness: -0.00015 per 10pp, p=0.005; race-matched
   Black-victim awareness x %Black: p=0.06), but the clean "avoidance
   concentrates in Black districts" prediction is NOT confirmed as stated --
   suppression looks broad-based with at most a modest gradient.
3. **DID (Justin's design) is directionally consistent but underpowered**:
   heavily-Black vs Q2, week-after vs week-before: EDP -0.0017 (p=0.49),
   mh_narrow -0.0026 (p=0.32). With 15v15 districts and 12 episodes the
   minimum detectable effect is several times the plausible effect size.
4. **Counts stay non-significant** (PPML: EDP -0.4%/log-point, p=0.21) -- the
   suppression claim remains compositional (shares), not levels.
5. **Permutation inference is the decisive caveat**: 200 circular shifts of
   the awareness series yield p=0.26 for the edp_share days-3-5 effect whose
   date-clustered p was 0.019. With both series persistent and only 12 real
   episodes, clustered SEs understate uncertainty; the suppression pattern is
   internally coherent (right call type, null placebos, visible in raw
   single-event data, sign-consistent everywhere) but is NOT statistically
   distinguishable from chance at conventional thresholds on this sample.
6. **Implication for the paper**: honest framing is now "suggestive evidence
   of post-awareness avoidance of police-adjacent emergency care" with the
   permutation result reported prominently, OR the sample must be extended
   (more episodes: 2015-16 and 2021-23 via the validated Wikipedia/Trends
   instrument) to gain the power a confirmatory claim needs. Extension is the
   scientifically stronger path and is feasible with sources already in hand.

## 8. Checkpoint (2026-07-18): CAI robustness on discovery period (Justin's Q3)

Re-ran the discovery-period (2017-2020 ONLY; extension freeze intact) EDP and
narrow-MH effects with the composite index CAI-D in place of legacy Twitter.
Key result -- the specific "days 3-5 suppression" is measure-dependent:

| Measure | outcome | days3-5 coef | p | joint lags0-7 p |
|---|---|---|---|---|
| Twitter | edp_share | -0.00065 | 0.019 | 0.156 |
| Twitter | mh_narrow | -0.00072 | 0.016 | 0.057 |
| CAI-D   | edp_share | +0.00038 | 0.407 | 0.041 |
| CAI-D   | mh_narrow | +0.00051 | 0.293 | 0.006 |

Reading (honest):
1. A first-week relationship between awareness and MH-call composition is
   present under both measures and is if anything STRONGER under CAI-D
   (joint lags 0-7: mh_narrow p=0.006 vs 0.057). So "awareness moves call
   composition in the first week" survives the measure swap.
2. BUT the specific feature we highlighted -- a decline concentrated at
   days 3-5 -- is specific to the legacy Twitter measure. Under CAI-D the
   individual-lag structure differs (Twitter loads negative on lag 5; CAI-D
   loads positive on lags 1 and 6), and the days-3-5 window is not negative.
3. Implication: with only 12 discovery episodes the first-week signal is
   real-ish but its precise temporal shape and daily-level sign are NOT
   pinned down; different (both defensible) awareness measures pick different
   noisy lags. This is the same fragility permutation inference flagged
   (p=0.26) and is a strong argument for the extension sample.
4. Consequence for the frozen plan: H1 was frozen as DIRECTIONAL ("EDP share
   declines days 0-5") based on the Twitter measure. The composite index does
   not reproduce that direction at that window. Recommend the confirmation
   test be reframed to the robust object -- a two-sided first-week joint test
   of awareness on EDP/narrow-MH composition -- rather than a directional
   days-3-5 decline. TO BE RATIFIED WITH JUSTIN AT GATE C before the
   confirmatory run.
