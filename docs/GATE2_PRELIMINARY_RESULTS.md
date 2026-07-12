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
3. **Environment/network change**: the session environment's network policy was
   updated on 2026-07-12 to allow api.census.gov, wikimedia.org,
   data.cityofnewyork.us, and trends.google.com so public augmentation data
   (ACS 2015-19 CD demographics, Wikipedia pageviews, NYC Well/311/NYPD CFS)
   can be fetched directly. Policy applies to sessions started after the change;
   fetches run via scripts/09_fetch_public_data.py.
4. **Single-event view**: raw Floyd-only comparison vs 2017-19 calendar baseline
   shows EDP share breaking ~0.8pp below its own pre-event level in the three
   weeks after May 25, 2020 while injury shares rise 2-3pp -- the regression
   signature, visible without a model.
