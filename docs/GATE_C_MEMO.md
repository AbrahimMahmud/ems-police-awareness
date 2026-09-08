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

---

## 6. Ratification record — 2026-09-08

Ratified in the 2026-09-08 working session. The decisions below are frozen; the
confirmatory run may not proceed until §5 (power) is also closed.

### 6.0 NEW — the legacy Twitter measure is retired as a treatment variable

**Decision.** The Twitter series is removed from every substantive model. It was
never re-fetchable, its collection methodology was never documented by the data's
originator, and it cannot be defended in print. CAI-D — Wikipedia victim
pageviews plus Google Trends (US and NYC) — is now the treatment variable
everywhere (`config.PRIMARY_AWARENESS = "cai_d"`).

**What Twitter is still for.** One thing only: `03b_bridge_legacy.py`, where the
z-scored Twitter series is the *object* of the methods critique (ROADMAP D2) —
the demonstration that z-scoring an attention measure manufactures
outlier-leveraged findings. Using an indefensible measure to show why such
measures fail is a different act from claiming a result with one, and the paper
should make that distinction explicitly. `02_build_awareness.py` now writes
`awareness_legacy_*.parquet` and is labelled accordingly.

**Consequences, stated plainly:**

1. **Everything in `GATE2_PRELIMINARY_RESULTS.md` §2–§4 is superseded.** Those
   estimates were computed on the Twitter measure. §8 of that memo already
   showed the days-3-5 EDP suppression is measure-dependent (−0.00065, p=0.019
   under Twitter; +0.00038, p=0.407 under CAI-D). Retiring Twitter means the
   headline "post-awareness avoidance of police-adjacent care" no longer has a
   surviving estimate behind it. What survives the swap is the weaker,
   two-sided object: a first-week relationship between awareness and call
   composition (joint lags 0–7: p=0.041 EDP, p=0.006 narrow-MH under CAI-D).
   The full discovery pipeline must be re-run under CAI-D before any framing
   claim is made.
2. **The race-matched exposure index had to be rebuilt.** `aware_black_log` was
   Twitter-derived. `12_build_cai.py` now constructs `cai_d_black` /
   `cai_d_nonblack` from per-victim Wikipedia pageviews joined to the victim
   registry (99.99% of victim pageviews classified by race). Two limits, both
   binding on H3:
   - the per-victim pageview file spans **2017–2020 only**, so H3 cannot be
     tested on the extension sample until pageviews are re-fetched over
     2015–2024 (the Wikimedia API is reachable; the fetcher exists in
     `09_fetch_public_data.py` and needs rate-limited re-running);
   - `corr(cai_d, cai_d_black) = 0.834`. The identity-matched contrast is
     therefore weak — the sub-index is close to the composite it sits inside,
     and H3 has less independent variation than the Twitter version implied.

### 6.1 H1 reframe — ratified, and now unavoidable

Ratified as recommended in §1: a two-sided joint test of awareness on first-week
(lags 0–7) EDP and narrow-MH call composition, under CAI-D
(`config.H1_TEST`, `config.H1_OUTCOMES`).

Note this is no longer a judgment call. H1 was frozen as a *directional* claim
stated on the Twitter measure; with that measure retired, the directional
hypothesis has no instrument to be stated on. The two-sided reframe is what
remains, and the loss of power relative to a directional test stands as recorded
in §1.

### 6.2 B-HEARD — ratified as recommended

Exposure control (early/conservative bound) primary, in every extension-sample
specification, with its interaction with time-since-adoption; late bound as
Sensitivity A; pre-2021-06 episode restriction as Sensitivity B; the
discovery-period invariance check as validation. Unchanged from §2.

### 6.3 Estimator — ratified as recommended

Stacked episode event study primary, windows −14..+14 with +28/+60
sensitivities, quasi-Poisson/PPML on counts alongside share OLS, and
**episode-level randomization inference as the primary p-value**. The
synthetic-null calibration in §3 is a precondition, not a robustness column: if
the estimator does not reject at its nominal rate on data with this
serial-correlation structure, the confirmatory p-value is uninterpretable.

### 6.4 DID control group — even-distribution primary

Treated = top-quartile %Black districts. **Primary control = the
"even-distribution" set** (bottom quartile of a Herfindahl index over the four
race shares). Q2 becomes the pre-specified sensitivity
(`config.DID_CONTROL_PRIMARY`, `config.DID_CONTROL_SENSITIVITY`).

Reasoning: both control sets are defined on demographics alone, so neither is
outcome-dependent by construction. But the *choice between them* is now being
made after the discovery run reported that Q2 is the one quartile with no
effect (`GATE2_PRELIMINARY_RESULTS.md` §7.2). Promoting Q2 to control after
learning that would maximise the measured contrast for a reason the data
supplied, and a referee is entitled to say so. The Herfindahl set avoids the
objection at some cost in interpretability. Both are reported; only the primary
is inferential.

### 6.5 Power — still open, still blocking

Unchanged from §5. Must be recomputed for 40 extension episodes under the
two-sided reframe with the B-HEARD control absorbing variation in the most
recent episodes, and now also under CAI-D rather than Twitter. Until this is
done there is no basis for saying the confirmatory run is worth making.

### 6.6 New open items created by 6.0

| # | Item | Blocking? |
|---|---|---|
| A | Re-run the full discovery pipeline under CAI-D; rewrite the Gate 2 memo from the results | Yes — no current framing claim is supported without it |
| B | Re-fetch per-victim Wikipedia pageviews 2015–2024 so H3 is testable on the extension sample | Yes for H3 only |
| C | `PANEL_BUFFER_START/END` and `ANALYSIS_START/END` are still discovery-scoped; widen for the extension run | Yes, before Phase D |
| D | CAI validation numbers below need Justin's eye before the index is written up | No, but do it early |

### 6.7 CAI validation battery — three numbers worth arguing about

From `outputs/tables/cai_validation.csv` (run 2026-09-08):

- **`corr(wiki_ext, trends_us) = 0.211`.** The two demand-tier components are
  only weakly correlated. An unweighted mean of weakly-correlated components is
  defensible as an index, but it means CAI-D is not measuring one clean thing,
  and the paper has to say what it is measuring.
- **`corr(wiki_ext, gdelt_news) = 0.713`.** Wikipedia pageviews correlate more
  strongly with news *supply* than with the other demand component. This is
  awkward for the demand/supply separation in `AWARENESS_INDEX_DESIGN.md` §7 and
  should be addressed head-on rather than left for a referee to find.
- **`corr(CAI-D, CAI-S) = 0.63`** (0.508 excluding Floyd). Below the 0.8
  threshold the design document set, so the two-tier separation is doing real
  work — the divergence-day falsification test has a genuine sample (18 days).

Peak alignment is a point in the index's favour: the top CAI-D days are the
Floyd episode, and the highest non-2020 day is **2016-07-08** (Alton Sterling and
Philando Castile) — an extension-period event the index detects without having
been tuned on it.
