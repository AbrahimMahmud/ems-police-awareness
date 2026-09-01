# Gate C memo — decisions needed before the confirmatory run

Four items need ratification before any extension-period outcome data is touched.
Three were already open (§1, §3, §4); §2 is new and is the reason this memo exists
now rather than after the estimator was built.

Standing constraint: the confirmation package's value comes entirely from the
hypotheses being fixed before the data is seen. Every decision below has to be
made on the reasoning presented here, not on results.

---

## 1. Reframe H1 from a directional days-3-5 decline to a two-sided first-week test

**What was frozen.** H1 (primary): *EDP call share declines in days 0-5 after
high-awareness episodes* — directional, and specified on the legacy Twitter measure.

**What changed.** Re-running the discovery period with the composite index CAI-D in
place of legacy Twitter (`03c_cai_discovery_robustness.py`, discovery data only,
extension freeze intact):

| Measure | outcome | days 3-5 | p | joint lags 0-7 p |
|---|---|---|---|---|
| Twitter | edp_share | −0.00065 | 0.019 | 0.156 |
| Twitter | mh_narrow | −0.00072 | 0.016 | 0.057 |
| CAI-D | edp_share | +0.00038 | 0.407 | 0.041 |
| CAI-D | mh_narrow | +0.00051 | 0.293 | **0.006** |

The first-week *relationship* survives the measure swap and is stronger under
CAI-D. The specific *days-3-5 decline* does not: it is a feature of the legacy
Twitter series, and the two measures load on different individual lags (Twitter
negative on lag 5, CAI-D positive on lags 1 and 6).

This is the same fragility permutation inference already flagged (p = 0.26 against
a date-clustered p of 0.019). With 30 discovery episodes, the first-week signal is
present but its daily shape and sign are not pinned down, and two defensible
awareness measures pick different noisy lags.

**Recommendation.** Reframe H1 to a **two-sided joint test of awareness on
first-week (lags 0-7) EDP and narrow-MH call composition**, under CAI-D. Rationale:
it is the object that survives the measure swap, it is what the discovery data
actually supports, and a directional test we already know one defensible measure
contradicts is not a real pre-registration.

**Supporting evidence from the literature** (`RELATED_WORK.md`): the closest
published benchmark for acute help-seeking after a collective-trauma event —
Crisis Text Line volume after the Uvalde shooting (Weitzel et al. 2023, SARIMA
counterfactual) — peaks at day +1 and is back inside the forecast interval by day
+4. The first week is where the literature says the action is; no published study
supports singling out days 3-5.

**Cost of the reframe, stated plainly.** A two-sided test is weaker than a
directional one, and this is a genuine loss. It is the honest position given that
the direction reverses across measures.

---

## 2. NEW: B-HEARD contaminates 45% of the confirmation episodes

**The problem.** B-HEARD (Behavioral Health Emergency Assistance Response
Division) routes nonviolent mental-health 911 calls to EMS-led rather than
police-led response. It launched June 2021 in three Harlem precincts and reached
31 of ~78 NYPD precincts by 2025 on a staggered schedule. A quasi-experimental
evaluation using the **same EMS Incident Dispatch Data file we use as our outcome**
(*Psychiatric Services*, doi:10.1176/appi.ps.20250528; staggered-adoption DID, 76
precincts, 2019-2024) finds adoption **reduces** mental-health EMS call rates in
adopting precincts, emerging roughly a year after implementation.

So B-HEARD is a geographically staggered, time-varying intervention acting
directly on our outcome, entirely inside the confirmation window — **and it biases
in the same direction as the hypothesis under test.** Uncontrolled, the
confirmatory run could confirm suppression for the wrong reason.

The discovery period is untouched: B-HEARD did not exist before June 2021.

**Exposure measured** (`scripts/16_bheard_exposure.py`). The dispatch file carries
both `policeprecinct` and `communitydistrict` on every incident, so the
precinct→CD crosswalk is built by server-side cross-tabulation over 14.9M
incidents (2015-2024) — exact and weighted by actual call volume rather than by
land area, which is the right weight for a share outcome.

| | |
|---|---|
| Frozen episodes | 70 (30 discovery, 40 extension) |
| Extension episodes wholly before the B-HEARD launch | 22 |
| **Extension episodes overlapping the B-HEARD period** | **18 (45%)** |
| CDs with any exposure by end-2024 | 30 of 59 |
| CDs fully covered | 25 |
| Mean CD exposure at the last affected episode | 0.451 |

Exposure at affected episodes rises over time — 4 CDs at the January 2022
episodes, 11 through spring 2022, 16 through early 2023, 24 by March 2023, 30 by
November 2023. The most contaminated episodes are the most recent ones.

**Date uncertainty, handled by bounding not guessing.** OCMH announced expansions
by neighborhood, not by precinct number, and the intermediate tranches cannot be
pinned to specific precincts from public sources.
`data/reference/bheard_precinct_adoption.csv` therefore carries an
earliest/latest window and a confidence flag per precinct (3 high, 11 medium, 17
low). The script validates that the independently published NYC IBO
operational counts fall *inside* the bounds at every checkpoint:

```
2022-01-01: bounds [ 3,  5] vs IBO  3 -- brackets
2023-01-01: bounds [ 9, 14] vs IBO 11 -- brackets
2024-01-01: bounds [21, 31] vs IBO 25 -- brackets
2025-01-01: bounds [31, 31] vs IBO 31 -- brackets
```

**Recommended handling, to be frozen now:**

1. **Primary**: CD-level B-HEARD exposure fraction (early/conservative bound) as a
   control in every extension-sample specification, plus its interaction with
   time-since-adoption, since the published effect emerges with a ~1-year lag.
2. **Sensitivity A**: the late bound, to show the conclusion does not turn on the
   adoption dates.
3. **Sensitivity B**: extension restricted to pre-2021-06 episodes. This drops
   date uncertainty entirely but costs 18 of 40 extension episodes — which is
   why it is a sensitivity and not the primary.
4. **Validation**: adding the control must leave the 2017-2020 discovery results
   numerically unchanged. If they move, the crosswalk is wrong.

**Decision needed:** ratify this handling, or choose a different one. Either way
it must be fixed before the run.

---

## 3. Estimator specification

Per ROADMAP U1, the primary confirmatory estimator becomes a **stacked episode
event study** (the continuous distributed lag becomes secondary):

- Each frozen episode is an event; windows −14..+14, with +28 and +60 as
  sensitivities (Desmond et al. 2016 find call-reporting effects persisting over
  a year, so 14 days may truncate real dynamics).
- Clean control days only; windows truncated at the next episode start.
- Quasi-Poisson/PPML on counts and OLS on shares — the current finding is
  compositional and counts have stayed non-significant, so both are reported.
- **Episode-level randomization inference as the primary p-value.** This is not a
  robustness column. Clustered SEs have already proved anti-conservative on this
  data (p = 0.019 clustered vs 0.26 permutation).
- **Synthetic-null calibration before the estimator touches real data**: confirm
  it rejects at its nominal rate on data with the same serial-correlation
  structure. If it does not, the confirmatory p-value means nothing.

**Decision needed:** ratify, or amend before coding is finalized.

---

## 4. DID control group (carried over from REWORK_PLAN §9.1)

Treated = top-quartile %Black districts. Control, both implemented:
(a) Q2 districts; (b) "even-distribution" districts — bottom quartile of a
Herfindahl index over the four race shares. **Which is primary is Justin's call.**

---

## 5. Power — recompute before ratifying

`CONFIRMATION_PLAN.md` W5 estimated power assuming ~30 episodes and concluded the
extension alone would land H1 near p ≈ 0.08. The frozen list has **70 episodes (40
extension)**, so that figure is stale and almost certainly pessimistic.

This has to be redone before Gate C closes, because it determines whether the
confirmatory run is worth doing at all. Two things make the recomputation
non-trivial and neither should be skipped: the two-sided reframe in §1 costs
power relative to the directional test the W5 note assumed, and the B-HEARD
control in §2 absorbs variation in the most recent episodes. A power calculation
that ignores both would overstate what the run can deliver.

---

## Summary of what is being asked

| # | Decision | Recommendation |
|---|---|---|
| 1 | H1 directional days-3-5 → two-sided first-week joint | Reframe |
| 2 | B-HEARD confound handling | Exposure control primary; two sensitivities |
| 3 | Stacked event study + randomization inference + null calibration | Ratify |
| 4 | DID control group | Justin's call |
| 5 | Power recomputation | Do before closing the gate |

After ratification: one confirmatory run, all hypotheses, no second look.
