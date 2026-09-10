# Rebuild plan

**Status: 29 checks — 8 FAIL, 1 BLOCKED, 20 PASS.** Target: all PASS.

Progress log (each line is one gate that ran clean, no regressions):

| Phase | Fixed | Passing |
|---|---|---|
| mechanism | suite + baseline + register sync | 1 |
| P1.1 | dropped `trends_victims`; corrected two checks that could not fail | 2 |
| P0 + P4 | EMS extract whole; O4; all five estimator defects; calibration gate | 10 |
| P0 | panel built — last BLOCKED cleared | 11 |
| T9 | registry-coverage finding + canary check | 11 |
| P5 | freeze guard: not tautological, full coverage, samples disjoint, proved able to fire | 15 |
| P1.5 | composite standardised after averaging, fixed component set | 17 |
| X5/R8 | PPML counts arm wired and recovering a planted rate change | 18 |
| P1.4 | article basket rebuilt from live sources | 20 |

### Checks that could pass for the wrong reason — five found so far

Every one was caught by the gate flagging an *unintended* flip, including flips
toward PASS. They are listed because the pattern is the point: a check that
reports success without verifying anything is worse than no check, since it
retires a live finding.

1. `T.composite_after_avg` — a non-greedy DOTALL regex matched elsewhere in the
   file after an unrelated edit. Reported PASS while `cai_d` still had SD 0.67.
2. `T.victims_topic_units` — admitted only one of two valid fixes, so dropping
   the component would have left it FAIL forever.
3. `S.no_stale_calibration` — returned PASS when the artifact was **absent**, so
   deleting the stale file "passed" it with no calibration having run.
4. `D.guard_coverage` — grepped for a function name, so renaming the entry point
   (the actual fix) made the fixed scripts read as unguarded.
5. `T.wiki_basket_live` — returned PASS as soon as a column disappeared. Dropping
   a column is not fixing a selection.

All five now assert on data or behaviour. **Prefer a data check to a source
grep**: where the property is arithmetic, test the arithmetic.

---|---|---|---|
| 09-09 | mechanism | suite + baseline + register sync | 1 |
| 09-09 | P1.1 | dropped `trends_victims`; corrected two checks that could not fail | 2 |
| 09-09 | P0 + P4 | EMS extract whole; O4; all five estimator defects; calibration gate | 10 |
| 09-09 | P0 | panel built — last BLOCKED cleared | 11 |

This is the execution plan for the 53 findings in `AUDIT_FINDINGS.csv`. It is
ordered so that each phase's inputs are settled before it runs, and it puts a
verification step between every phase.

---

## 0. The rule this plan is built around

The last round of repairs introduced five new blocking defects. All five were
written carefully. Care was not the missing ingredient — a way to check was.

So:

- **Every finding is a check in `scripts/23_regression_suite.py`**, keyed by its
  ID in `docs/AUDIT_FINDINGS.csv`.
- **A fix is done when its check flips FAIL → PASS and no other check moves.**
- **A check that cannot be evaluated reports BLOCKED, never PASS.** "Couldn't
  check" reading as "fine" is what silently destroyed four dimensions of audit
  findings on the first verification run. It is not allowed to happen again.
- **The suite exits non-zero if any check that was PASS is no longer PASS.**
  That is the whole safety net; it was tested by doctoring the baseline, and it
  fired.

### Why the checks are written to FAIL right now

A test that passes before the fix and after the fix tests nothing. Each check
asserts the *corrected* property, so today it fails. The count of FAILs is the
work remaining, and it should only go down.

### Prefer a data check to a source grep

A check that greps a script for the right-looking code proves the code says the
right thing, not that the output has the right property.

This is not hypothetical. `T.composite_after_avg` originally searched
`12_build_cai.py` with a non-greedy DOTALL regex. When P1.1 edited an unrelated
part of that file, the regex found a match somewhere else and the check flipped
to PASS — while the defect was completely untouched and the composite still had
SD 0.67 on its reference window. **A false PASS is worse than no check**: it
retires a finding that is still live.

It was caught only because the gate flags *any* unintended flip, including a
flip in the direction you were hoping for. Rewritten as an assertion on the
built index, it correctly reports FAIL.

So: where the property is arithmetic, test the arithmetic. 13 checks are still
source greps; each should become a data check when its phase runs and the data
it needs exists.

---

## 1. The gate between every phase

Run this after every phase, and after any single change big enough to worry
about. It takes about a minute.

```
cd scripts
../.venv/bin/python 23_regression_suite.py          # 1. did I fix it, did I break anything
../.venv/bin/python 20_data_audit.py                # 2. data-level integrity (flag count must not rise)
../.venv/bin/python -c "import ast,pathlib,sys; [ast.parse(p.read_text()) for p in pathlib.Path('.').glob('*.py')]"
```

**Pass conditions, all three required:**

1. The checks this phase targeted are PASS.
2. Exit code 0 — no check that was PASS has stopped passing.
3. `data_audit.csv` flag count is the same or lower than the previous run.

**If a check flips in a direction you did not intend, stop and understand it
before continuing.** An unexplained flip is information, not noise: it is the
fix touching something you did not know it touched. That is precisely the event
this whole mechanism exists to surface, and walking past it wastes it.

Then accept the new state as the baseline, so the next phase is measured
against it:

```
../.venv/bin/python 23_regression_suite.py --baseline
git add -A docs scripts && git commit
```

Commit the baseline **with** the fix, in the same commit. A baseline updated
separately can quietly launder a regression into the accepted state.

---

## 2. Phase order, and why it is this order

Each phase's output is the next phase's input, so they cannot be reordered or
usefully parallelised — except P0, which is pure wall-clock and runs alongside
everything.

```
P0  outcome data        (running now, detached — the long pole)
P1  treatment index     → blocks P2, because episodes are defined on the index
P2  episode definition  → blocks P4, because the event study takes episodes as given
P3  outcome panel       → needs P0
P4  estimator           → needs P1, P2, P3
P5  gates               → must be REPAIRED before being re-run, or they pass vacuously
P6  documentation and replication package
```

---

## P0 — Restore the outcome data

**Checks:** `O.ems_complete`, `O.panel_exists`, `O.dropna_groupby`

The single fact that reorders everything: the outcome data does not exist. The
extract held 14.5M of 29,978,154 source rows and stopped at 2016-06-10. The last
cached page was *full*, so the `if len(df) < PAGE: break` terminator never fired
— the loop was killed, not completed. `panel_cd_day.parquet` has never existed,
which means no estimate in the repo is reproducible.

- [x] Restart `00b_download_ems_extract.py` on the harness-tracked background
      runner. `nohup` dies at turn boundaries; this does not.
- [x] **Done: 29,978,154 rows, matching the source count exactly**, aggregated to
      4,876,509 district-day-call-type rows over 2014-12-01..2024-12-31.
- [ ] Fix the terminator: stop relying on a short final page. Record realised
      min/max date and row count, and exit non-zero if coverage falls short of
      the source count.
- [x] Fix `00b`'s silent `dropna` on missing community district (**O4**).
      It found what it was meant to find: **167,446 calls (1.14%)** had no
      district and were vanishing before any QC metric saw them — and the
      by-year rate is **2.97% in 2015 against ~0.90% from 2016 on**, which is
      finding O2's geocoding regime change, now measured instead of hidden.
- [ ] Reconcile `00b`'s mental-health code map against `config.CALL_TYPE_GROUPS`.
      The two "equivalent" extract scripts are not equivalent.
- [x] `01_build_panel.py`: 89,857 rows, 59 districts, 2016-12-01..2021-01-31
      (still buffered-discovery-scoped, correctly — widening `ANALYSIS_START/END`
      is the act that ends the freeze and waits on ratification).
- [ ] `10d_parse_cd_demographics.py`.

**Gate P0:** `O.ems_complete` PASS; `O.panel_exists` moves BLOCKED → PASS;
`O.dropna_groupby` PASS. Panel is 59 districts exactly, no duplicate
(district, date), `mh_narrow <= mh_broad <= total_calls` on every row.

*Note: `O.panel_exists` going BLOCKED → PASS is the one case where a BLOCKED
check clearing is real progress rather than a masked failure. Every other
BLOCKED in this plan is a "cannot check yet" and must not be read as good news.*

---

## P1 — Rebuild the treatment index

**Checks:** `T.anchor_monthly`, `T.nyc_break`, `T.nyc_censoring`,
`T.victims_topic_units`, `T.composite_after_avg`, `T.fixed_component_set`,
`T.wiki_basket_live`

Do these in order — the last two depend on the first four being settled.

### P1.1 Drop `trends_victims` (**T2, L2**)
- The code never divides by the topic term (`ratio = df[name]`, `11c:96`), so
  every sizeable victim saturates at exactly 100. The component counts open
  windows, not attention.
- Its availability is *caused by the treatment*: Trends only returns a
  victim-name series once volume clears a reporting floor, so its presence is
  itself an attention signal and the index partly measures itself.
- Drop rather than repair. The three always-on components correlate 0.985 with
  the index as built, so this costs almost nothing.
- **Flips:** `T.victims_topic_units`. Also removes **T8** (calibration constants
  estimated on a treatment-selected 39% subsample) as a side effect.

### P1.2 Decide `trends_nyc` (**T1, T3, L3**)
- It has a ~4.5x artificial level break at 2021-09-26: `11b:53` falls back to
  `scale = 1.0` when an overlap mean is zero, and the 2021-05-29..09-25 NYC
  chunk is all zeros, so the chain reset.
- It is 79% exactly-zero, with censoring rising 55% (2020) → 98% (2024). That is
  Google's low-volume floor, not a level.
- It is the *only* nominally NYC-local component, so the "city-local treatment"
  claim rests entirely on it. Say so either way.
- Fix the stitching first (regress new-on-previous through the origin, require a
  minimum count of jointly-positive days, **abort loudly instead of falling
  back**). Then decide: broader term basket so it clears the floor, or model it
  as censored, or drop it and demote to a validation exhibit.
- **Flips:** `T.nyc_break`, `T.nyc_censoring`.

### P1.3 Fix the Trends anchor (**X1, T4, T5, L4**)
- The "weekly anchor" is monthly: `11c:61` requests a 10-year window, Trends
  returns monthly granularity, and the 7-day mask at `11c:74` then rescales only
  days 1–7 — leaving a permanent within-month step of −0.408 SD.
- Fetch the anchor in <5-year blocks so Trends returns weekly, or mask
  `wstart` → next `wstart`, or drop anchoring and keep the stitched series.
- **Flips:** `T.anchor_monthly`.

### P1.4 Rebuild the Wikipedia basket (**X2**)
- The basket is selected by the retired Twitter data and contains **zero victims
  killed after 2020**. A treatment index whose article list ends in 2020 cannot
  measure attention in 2021–2024.
- Re-select from a live source, then finish `21_refetch_wikipedia.py`, which sums
  pageviews across each article's *historical titles*. Wikimedia records views
  per title and does not carry them across a page move, so resolving to the
  current canonical title discards the spike at the killing — the exact signal
  being measured. 15 of 45 articles show this.
- Also bound **L7**: `agent=user` changed meaning in April 2020,
  non-retroactively, splitting the sample at the largest treatment episode.
- **Flips:** `T.wiki_basket_live`.

### P1.5 Standardise the composite after averaging (**D5**)
- Today each component is standardised separately and the index is the mean of
  whatever exists that day, so its SD moves with how many components exist
  (0.693 on 3-component days, 1.034 on 4-component days).
- The `cai_d > 1.0` episode rule is therefore not a 1-SD rule: it selects the
  62nd percentile of days in 2020 and the 99.7th in 2024.
- Hold the component set fixed, average, then standardise the composite on the
  reference window.
- **Flips:** `T.composite_after_avg`, `T.fixed_component_set`.
- **Must run last in P1** — it consumes whatever component set P1.1–P1.4 leave.

**Gate P1:** all seven `T.*` checks PASS. Then, before P2, confirm the property
the index is supposed to have: **SD stable across years and across component
regimes**, and the share of days above threshold no longer varying with
component count. If `T.*` passes but that property does not hold, the checks are
too weak and need tightening — not the fix declaring victory.

Honest consequence to state in the paper: after P1.1 and possibly P1.2, CAI-D is
a **two-component national attention index**. Write it that way.

---

## P2 — Redefine episodes

**Checks:** `E.threshold_stringency`, `E.no_mega_episode`,
`E.labels_live_source`, `E.attribution_lookback`

Blocked by P1 — episodes are thresholds on the index, so redefining them before
the index is settled means doing it twice.

- [ ] **Constant stringency (D5, L5).** Replace the fixed 1.0 threshold with a
      trailing-365-day rolling standardisation or a fixed within-year quantile.
      A threshold that means "top 22% of days" in 2015 and "top 0.3%" in 2024 is
      not one rule.
- [ ] **Cap episode length (E3, D7).** No "event" may exceed the window it is
      analysed with. The 129-day mega-episode discards 114 of its own days and
      hides at least eight distinct attention shocks — including **Daniel
      Prude**, a Black man killed during a mental-health crisis, which is the
      single most on-hypothesis event in the dataset and is currently invisible.
- [ ] **Widen the attribution lookback 14 → 60+ days (E2).** Video releases,
      indictments and verdicts spike well after the death, so a 14-day lookback
      attributes the largest non-2020 episode to the wrong person.
- [ ] **Relabel from a live source (E5, L6, R2).** `candidate_events` ranks
      victims by retired Twitter volume; ties break on file order over an
      all-zero column, so **39 of 70 labels are arbitrary** and episode 22 names
      the Newton NH Michael Brown. Rank by post-episode Wikipedia pageviews on
      resolved titles instead.
- [ ] **Audit the registry for omissions.** Daniel Prude and Jordan Neely are
      both missing; Neely is pre-specified in `CONFIRMATION_PLAN.md:23-25`.
- [ ] **Evaluate rules on design quality, not results** — {frozen,
      peak-prominence 14d/28d, hysteresis enter>1.5/exit<1.0, ≥2 consecutive
      days} — while still blind to every outcome. This is the only moment that
      choice is free.
- [ ] **Write to a NEW file.** Leave `confirmation_episodes.csv` untouched as the
      original frozen artifact, and publish the diff: episodes added, dropped,
      boundaries moved, labels changed.
- [ ] **Retract** the "labels are correct / no relabelling needed" lines at
      `docs/DATA_AUDIT.md:159-165` (**R2**).

**Gate P2:** all four `E.*` checks PASS; no `T.*` check has moved; the episode
diff is written and readable. **Justin signs off on the corrected list before any
outcome is touched** — this is the one step in the plan not to take alone,
because it changes a frozen artifact.

Why changing it is defensible *only now*: the freeze exists to prevent
outcome-informed selection. A correction made while still blind to every outcome
cannot be outcome-informed. Made after the confirmatory run, the same correction
is worthless.

---

## P3 — Outcome construction

**Checks:** `O.dropna_groupby` (with P0), plus new checks written in this phase
for O1, O2, O3.

- [ ] **Counts primary, shares secondary (T3.1).** The 2020 "signature" reverses
      in counts: EDP counts were flat after Floyd and the denominator rose 6.4%
      because injury calls rose ~20%. A compositional finding that only exists in
      the denominator is not a finding. Publish the count path beside every share
      path and add `log_total` as its own outcome.
- [ ] **Disposition filter (O1).** It deletes cancelled EDP dispatches — an
      EDP-specific deletion with a 40x differential across call families and 6x
      instability over time. Quantify it and justify it, or drop it.
- [ ] **Call-type births (O3).** EDPM is born on the exact day B-HEARD launches;
      T-EDP is born inside the largest discovery episode. Both are coding changes
      that will read as effects. Fold into the EDP family and test a pre/post
      split.
- [ ] **In-window breaks (O2).** Geocoding completeness triples on 2016-01-01
      (missing-CD 3.12% → 0.63%) and INJALS retires 2015-12-16 — both inside the
      2015–2016 confirmation window. Handle explicitly or move the floor.
- [ ] Rewrite `GATE2_PRELIMINARY_RESULTS.md` §6.4, whose headline visual evidence
      does not survive in counts.

**Gate P3:** panel invariants hold; the count and share paths are both produced;
new checks for O1/O2/O3 exist and pass. Re-run the P1 and P2 gates — this phase
touches the panel those gates read.

---

## P4 — Fix the estimator

**Checks:** `S.reference_day`, `S.placebo_count`, `S.joint_test`,
`S.cluster_by_date`, `S.prewindow_truncation`, `S.ppml_wired`

Five of these six are defects I introduced. Each is independently fatal. The
design is right; the implementation is not.

- [ ] **Reference day (S2, D1).** `event_study.py:59` *deletes* day −1 instead of
      making it the reference, so the omitted category is day −14 and
      `EVENT_REFERENCE_DAY = -1` is inert. Every coefficient and every caption
      currently states the wrong baseline. Keep day −1 in the frame and use
      `C(rel_day, Treatment(reference=-1))`; then assert the estimated rel_days
      equal the window minus {−1}.
- [ ] **Placebo draws (S1, E1, L1, X4, D2 — found independently by five of seven
      auditors).** `placebo_starts` walks forward from a uniform anchor and
      breaks when a start would exceed `latest`, so only ~11% of draws admit all
      30 episodes and the mean draw carries 16.2. The null is built from
      half-size designs, which inflates its SD and guts the primary p-value. Draw
      the anchor from `[earliest, latest − sum(gaps)]` so all N always fit, and
      reject any draw where `n != len(real_starts)`.
- [ ] **Joint test (S3, R7).** `first_week_effect` averages the day 0–7
      coefficients — a 1-df linear contrast. H1 is a joint test that all eight
      are zero. A dip-then-rebound, which is the project's *own* hypothesised
      mechanism, averages to zero: the statistic has almost no power against the
      thing it was written to detect. Use the 8-df Wald; keep the mean only as a
      reported effect size.
- [ ] **Clustering (S6).** Treatment is citywide and assigned at the date level,
      but `vcov="hetero"` assumes independence across districts within a day.
      This is `REWORK_PLAN` I1 relearned in new code; error bars are roughly 3x
      too narrow. Cluster by date, or two-way district × date.
- [ ] **Stack construction (S5, E4).** `build_stack` truncates forward only, then
      `duplicated(..., keep=False)` deletes *both* copies of a contested
      district-day. 28% of window district-days are lost and 5 of 30 episodes
      lose their entire first week. Set `lo = max(s − pre, prev_end + 1)`, drop
      any episode that cannot retain day −1 plus one post day, and report
      per-rel_day episode counts.
- [ ] **Counts arm (X5, R8).** PPML with a log total-calls offset is documented
      but `counts=True` is never passed and no offset term exists. Wire it or
      delete the claim.
- [ ] **`07_did_exposure` (S7)** still contains the exact I4 double-counting
      defect `build_stack` was written to eliminate: 12% of rows are the same
      outcome counted with opposite treatment status.

**Gate P4:** all six `S.*` checks PASS. Then two things the checks alone do not
prove:

- Fit on **synthetic data with a known planted effect** and confirm the estimator
  recovers it. A green suite proves the defects are gone, not that the estimator
  is correct.
- Confirm the reported first-week statistic is invariant to episode ordering.

---

## P5 — Repair the gates, then re-run them

**Checks:** `S.calibration_can_fail`, `S.no_stale_calibration`,
`D.freeze_not_tautological`, `D.freeze_disjoint`, `D.guard_coverage`

**All three ratified validation gates are constructed so that they cannot fail
(D4).** Re-running them before repairing them produces three more passes that
mean nothing — which is how they came to be treated as discharged in the first
place.

- [ ] **Null calibration (S4, X3, R3).** The binomial acceptance band is wide
      enough to contain any estimate, and the committed `null_calibration.csv`
      is a 12-sim / 25-draw smoke test with no real panel that reads PASS. At the
      documented 200 sims the same code prints NOT CALIBRATED. Require p-value
      **uniformity (KS test)**, not a rejection rate inside a wide band; delete
      the stale artifact; re-run at ≥1000 sims *after* P4.
- [ ] **Citywide day shocks (S6).** The synthetic panel has no common day shock,
      so the null it generates is easier than reality. Add one, or the
      calibration validates the estimator against a world that does not exist.
- [ ] **Freeze guard (D3, X9).** `assert_discovery_only` is tautological wherever
      it is called — always immediately after the same `.between()` filter — is
      absent from four scripts that read the panel, and no-ops when
      `FREEZE_ACTIVE=False`. Worst: **flipping that flag pools discovery into the
      confirmatory sample**, producing a discovery-only estimate labelled "70
      episodes". Guard on the *raw* frame before filtering; add it to every panel
      reader; make `FREEZE_ACTIVE=False` widen the sample window and *exclude*
      discovery rather than pooling them.
- [ ] **Divergence test (T4).** `cai_s` is single-component in 2015, 2016, 2023
      and part of 2024, so its 95th-percentile tail selects *those years* rather
      than divergence days. Of the 18 "divergence days", 17 fall where
      `gdelt_news` is missing; restricting to valid years leaves **one**.
      Restrict to 2017–2022 or standardise after averaging.
- [ ] **B-HEARD invariance (X6, R6).** The control is built and wired into no
      model. Note the discovery-invariance check as designed **cannot fail** —
      exposure is identically zero on every discovery day by construction. Give
      it a version that can: validate the crosswalk on 2021–2024 *treatment-side*
      data, which contains no outcome.

**Gate P5:** all five checks PASS, and each gate has been shown to be *capable*
of failing — feed each one input it should reject and confirm it does. A gate
that has never failed on anything has not been tested.

---

## P6 — Documentation, provenance, replication

- [ ] `docs/PAPER_MASTER.md` — the master document, every method in three layers:
      plain language with an everyday analogy, then why and what the alternatives
      were, then the exact technical statement with the file and function that
      implements it. A reader can stop after layer one and still follow the paper.
- [ ] `scripts/run_all.py` (specified in `REWORK_PLAN` §7, never written; also
      deliverable D3) and `22_pipeline_check.py`. Clean twice from cold.
- [ ] Provenance (**X8**): `data_sources.csv` IDs collide three ways between doc,
      code and register — `S10` is both Mapping Police Violence and the precinct
      crosswalk, `S11` both the CAI components and the B-HEARD schedule. Re-key
      before any source ID is cited in Methods. Move the year-loop try/except
      *inside* the loop (**T7**) so a truncated fetch cannot record its intended
      span.
- [ ] Rename `w_precinct_in_cd`, which is normalised by community district rather
      than by precinct. The arithmetic is right for its use; the name is wrong and
      will mislead a Methods reader.
- [ ] Reconcile the volume-coverage claim: 87.9% in the resolution file, 82.8% in
      the docs. State one number.
- [ ] `CONFIRMATION_PLAN.md` addendum — original text byte-identical, changes
      appended and dated, including the explicit acknowledgement that the H1
      reframe and the DID control-group promotion were both decided **after**
      seeing discovery results. Discovery-informed revision is legitimate;
      concealing it is not.
- [ ] Freeze-disclosure paragraph naming the two post-freeze contacts with
      extension-period data that a reviewer running `git log` will find anyway
      (`4a19d8a`, `9ddede9`), and why neither is fatal.
- [ ] `docs/PRE_ANALYSIS_NOTE.md`, clearly labelled reconstructed rather than
      contemporaneous.
- [ ] Fix the run order (**X10**): four scripts the pipeline depends on are
      omitted, and `08_figures` references a panel column that does not exist.

---

## 3. Final gate, before any confirmatory run

All of these, not a majority:

- [ ] 26 of 26 checks PASS. No BLOCKED, no ERROR.
- [ ] `data_audit.csv` flag count at or below 12 and monotonically decreasing
      across the whole rebuild.
- [ ] Null calibration passes a **KS uniformity** test at ≥1000 sims on a panel
      **with citywide day shocks**.
- [ ] The estimator recovers a **planted effect** on synthetic data.
- [ ] Adding the B-HEARD control leaves discovery estimates numerically unchanged
      (if it moves them, the crosswalk is wrong — `GATE_C_MEMO` §2.4).
- [ ] `run_all.py` + `22_pipeline_check.py` clean **twice from cold**.
- [ ] Power analysis reports a minimum detectable effect, computed on the
      *effective* number of informative episodes rather than the nominal 70 —
      32 of which are single days and several of which graze the threshold.
- [ ] Justin has signed off on the corrected episode list.

**If the power analysis says the confirmatory run cannot deliver, that is a
finding, and it is far better to learn it now than after spending the one shot.**

---

## 4. What is deliberately not in this plan

- **No new branch.** Everything lands on `analysis-rework`.
- **No confirmatory estimate.** Nothing here touches a 2021–2024 outcome. The
  freeze is intact in fact — the panel does not exist and no extension estimate
  has ever been produced — and that is worth more than any single result,
  because it is what keeps the Registered Report route open.
- **No fix without a check.** A finding that is not a test will regress. That is
  not a prediction; it is what already happened, five times.
