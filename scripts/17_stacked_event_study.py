"""Stacked episode event study — the ratified primary confirmatory estimator.

ROADMAP U1 and GATE_C_MEMO.md §3/§6.3 made this the primary estimator and the
continuous distributed lag secondary. It did not exist: EVENT_WINDOW_PRE/POST,
EVENT_REFERENCE_DAY and RANDOMIZATION_DRAWS were constants with no consumer, and
H1_TEST was a string label rather than code. This is that estimator.

Design
------
Each frozen episode is an event. Around each, a window of EVENT_WINDOW_PRE days
before to EVENT_WINDOW_POST days after the episode start is stacked into one
dataset carrying an `episode` identifier, so district and calendar effects are
absorbed WITHIN episode rather than across them. Day EVENT_REFERENCE_DAY (-1) is
the omitted category, so every coefficient reads as the change relative to the
day before attention rose.

No observation is a control for one event while being treated in another — the
failure mode that made the original "difference-in-differences" uninterpretable
(REWORK_PLAN I4). A district-day contested by two episode windows is assigned to
the episode whose start is NEAREST in absolute event time, and appears exactly
once in the stack.

This paragraph used to say windows were truncated at the next episode's start and
contested days were DROPPED. Both halves were false: `event_study.build_stack`
builds the full [start-pre, start+post] window unconditionally and deduplicates
by nearest episode, which keeps the observation instead of discarding it (finding
S5). The change was made in the code and not here, so the file described a
sample-construction rule the project had already rejected — and a Methods section
written from this docstring would have misreported how the estimator is built.

Inference
---------
Episode-level randomization inference is the PRIMARY p-value, not a robustness
column. Clustered standard errors have already proved anti-conservative on this
data (p = 0.019 clustered against 0.26 permutation). Under the null the estimator
is re-run on RANDOMIZATION_DRAWS re-draws of placebo episode dates that preserve
the real episodes' spacing, and the reported p is the share of placebo statistics
at least as extreme as the observed one.

The test statistic is the JOINT Wald chi-square on the day 0..7 coefficients,
two-sided in the effect, per the H1 reframe ratified at Gate C §6.1. The mean of
those coefficients is reported beside it as the effect size, but it is not the
test: a dip-then-rebound, the mechanism this project hypothesises, averages to
roughly zero (finding S3/R7).

Standard errors are clustered on the date. Treatment is citywide and assigned at
the date level, so independence across districts within a day is not available
(finding S6).

Outcomes are estimated on shares (OLS) and on counts (PPML with a log
total-calls offset), because the finding is compositional and counts have stayed
non-significant; both are reported rather than the more favourable one.

Usage:
    python 17_stacked_event_study.py [--outcome edp_share] [--draws 2000]
"""

# One BLAS thread per process, set BEFORE numpy loads (see 30_confirmatory_run.py
# for the measurement: forked workers deadlock on an inherited OpenBLAS pool, and
# multi-threaded BLAS under several workers oversubscribes a 4-core box).
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse

import numpy as np
import pandas as pd

from config import (
    EPISODE_LIST_PRIMARY,
    ANALYSIS_END,
    ANALYSIS_START,
    DISCOVERY_END,
    DISCOVERY_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_POST_SENSITIVITY,
    EVENT_WINDOW_PRE,
    FREEZE_ACTIVE,
    H1_OUTCOMES,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    RANDOMIZATION_DRAWS,
    BHEARD_BOUND_PRIMARY,
)
from event_study import (
    _rel_day_coefs,
    build_stack,
    count_outcome,
    fit_dose_response,
    episode_day_counts,
    first_week_effect,
    first_week_mean,
    fit_event_study,
    joint_p,
    randomization_p,
    require_calibrated,
)
from bheard import attach as attach_bheard
from freeze_guard import freeze_banner, select_sample

parser = argparse.ArgumentParser()
parser.add_argument("--outcome", default=None, help="default: every H1 outcome")
parser.add_argument("--draws", type=int, default=RANDOMIZATION_DRAWS)
parser.add_argument("--post", type=int, default=EVENT_WINDOW_POST)
args = parser.parse_args()

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
freeze_banner("17_stacked_event_study")
rng = np.random.default_rng(20260908)


# RANDOMIZATION INFERENCE IS CHECKPOINTED (finding N6). This environment restarts
# every 30-70 minutes and this script writes only at the end, so a 1000-draw run
# never finished: one died at 33 minutes having saved nothing. Each (outcome,
# window, arm) keeps its own ledger of completed draws and its own fixed seed
# root, so a restart costs at most one draw and a resumed run reproduces the run
# it resumed exactly rather than approximately.
#
# The seed is derived from the cell's identity rather than drawn, so re-running
# one cell does not perturb any other, and the ledger is keyed the same way for
# the same reason a calibration ledger is keyed by stratum: statistics from
# different cells are different quantities and pooling them would be a second
# source of truth.
def _ri_cell(outcome, post, arm):
    return f"{outcome}_{post}_{arm}"


def _ri_ledger(outcome, post, arm):
    return OUTPUTS_TABLES / f"ri_ledger_{_ri_cell(outcome, post, arm)}.csv"


def _ri_seed(outcome, post, arm):
    import zlib
    return zlib.crc32(_ri_cell(outcome, post, arm).encode()) ^ 20260908


# ---------------------------------------------------------------------------
panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
panel["incident_date"] = pd.to_datetime(panel["incident_date"])
panel = select_sample(panel, where="17_stacked_event_study")
panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
panel["dow"] = panel["incident_date"].dt.dayofweek

# B-HEARD exposure, attached HERE rather than at the point it becomes non-zero
# (finding X6). From 2021-06-01 New York routes some mental-health 911 calls to a
# health-led response instead of police, precinct by precinct - which moves the
# outcome in the SAME DIRECTION as the hypothesis. The control was built, IBO-
# validated and committed, and read by no model at all.
#
# It went unnoticed because it is identically zero throughout discovery, so
# adding it changes nothing anyone has estimated. That is exactly why it has to
# be wired NOW: after the freeze lifts, adding a control is a specification
# change, and doing it before means the confirmatory run inherits it rather than
# acquiring it.
#
# Verified: adding it to the discovery model leaves all 28 event-time
# coefficients bit-identical (max |difference| 0.000e+00) - pyfixest drops the
# all-zero column as collinear. X.bheard_inert_on_discovery asserts it, and a
# non-zero value here while frozen would mean the precinct-to-district crosswalk
# is wrong.
panel = attach_bheard(panel, bound=BHEARD_BOUND_PRIMARY)

ep = pd.read_csv(DATA_REFERENCE / EPISODE_LIST_PRIMARY, parse_dates=["start", "end"])
if FREEZE_ACTIVE:
    ep = ep[ep["period"] == "discovery"]

# THE NULL BEHIND THIS SCRIPT'S p-VALUES MUST BE CERTIFIED BEFORE IT REPORTS ANY.
#
# This script computes randomization-inference p-values — the ratified primary
# inference — and until now read no calibration at all. Gate C ratified the
# ordering "calibrate, then report"; the gate existed only inside the regression
# suite, so the estimator itself would have run and printed p-values regardless.
#
# It was invisible because discovery IS calibrated, so every number it produced
# would have been sound. That is the failure mode, not an excuse for it: a
# guarantee nothing enforces is a guarantee that holds until the day it doesn't,
# and this project has closed the identical pattern three times already (X5
# PPML, X6 B-HEARD, D6 dose response).
#
# The stratum is DERIVED from the episodes actually selected, not asserted. While
# the freeze holds those are discovery's and the answer is "discovery". After it
# lifts, the filter above stops applying and this script would silently pool
# discovery with both confirmation strata — a set no calibration certifies,
# because the three do not even share a draw scheme (discovery and C2 shift an
# anchor, C1 shifts circularly over a gapped window). So a pooled run is refused
# and pointed at the confirmatory path, which certifies each stratum separately.
_periods = sorted(ep["period"].unique())
if _periods != ["discovery"]:
    raise SystemExit(
        f"17_stacked_event_study estimates the discovery stratum; the selected "
        f"episode list spans {_periods}. No calibration certifies a pooled null "
        "over strata that do not share a draw scheme. The confirmatory path is "
        "30_confirmatory_run.py, which certifies C1 and C2 separately.")
require_calibrated("discovery")

ep = ep.sort_values("start").reset_index(drop=True)
real_starts = ep["start"].tolist()
print(f"episodes in scope: {len(ep)}  ({'discovery only' if FREEZE_ACTIVE else 'all'})")

lo_d, hi_d = panel["incident_date"].min(), panel["incident_date"].max()
gaps = np.diff([d.toordinal() for d in real_starts]) if len(real_starts) > 1 else np.array([30])

# THE RANDOMIZATION GEOMETRY IS THE CERTIFIED ONE, NOT THE PANEL'S EXTENT. The
# calibration that licenses these p-values was run on the fixed discovery window
# (18_null_calibration.py, STRATUM_WINDOWS["discovery"]); randomization_p, left
# without `windows=`, takes the panel's own min..max after the MIN_TOTAL_CALLS
# filter, and the two coincide only while the panel has rows on both boundary
# dates. So the window is passed explicitly, and the coincidence is asserted
# rather than relied on: a panel that lost an edge day would otherwise draw its
# null from a geometry the calibration never tested.
RI_WINDOWS = [(pd.Timestamp(DISCOVERY_START), pd.Timestamp(DISCOVERY_END))]
if (lo_d, hi_d) != (RI_WINDOWS[0][0], RI_WINDOWS[0][1]):
    raise SystemExit(
        f"the discovery panel spans {lo_d.date()}..{hi_d.date()} after the sample "
        f"rules, not {DISCOVERY_START}..{DISCOVERY_END}; the certified anchor-shift "
        "geometry would not be the one drawn. Refusing rather than estimating on an "
        "uncertified null.")

# The B-HEARD control is IN THE FORMULA, not merely attached to the panel. It was
# attached above and estimated by nothing: event_study's estimator had no way to
# take a covariate, so the control lived in a column no model read while 30 kept
# its own formula with it. Identically zero on discovery, pyfixest drops it as
# collinear and every coefficient is unchanged - which X.bheard_wired asserts.
COVARIATES = ("bheard_exposure",)

outcomes = [args.outcome] if args.outcome else list(H1_OUTCOMES)
rows, path_rows = [], []

for outcome in outcomes:
    for post in dict.fromkeys([args.post, *EVENT_WINDOW_POST_SENSITIVITY]):
        stack = build_stack(panel, real_starts, EVENT_WINDOW_PRE, post)
        if stack.empty:
            continue
        obs = first_week_effect(stack, outcome, extra=COVARIATES)
        if obs is None:
            print(f"  {outcome} post={post}: not estimable")
            continue

        # -- event-time path (only for the primary window) --
        if post == args.post:
            m = fit_event_study(stack, outcome, extra=COVARIATES)
            if m is not None:
                names = _rel_day_coefs(m)
                epc = episode_day_counts(stack)
                for rd, n in sorted(names.items()):
                    path_rows.append({"outcome": outcome, "rel_day": rd,
                                      "coef": float(m.coef()[n]), "se": float(m.se()[n]),
                                      "n_episodes": int(epc.get(rd, 0))})
                w = [names[k] for k in range(0, 8) if k in names]
                if w:
                    chi2, p_asy = joint_p(m, w)
                    print(f"    joint chi2({len(w)}) = {chi2:.2f}   asymptotic p = {p_asy:.4f}"
                          "   (reported beside the RI p, never instead of it)")

        # -- randomization inference (primary p-value) --
        obs, p_ri, draws = randomization_p(
            panel, real_starts, outcome, EVENT_WINDOW_PRE, post, args.draws, rng,
            windows=RI_WINDOWS, extra=COVARIATES,
            ledger=_ri_ledger(outcome, post, "ols"),
            seed=_ri_seed(outcome, post, "ols"))

        # -- counts arm: PPML on the count with a log total-calls offset --
        # Reported BESIDE the share result, never instead of it. The 2020
        # "signature" is known to reverse in counts: EDP counts were flat after
        # Floyd while the denominator rose 6.4% because injury calls rose ~20%,
        # so a compositional finding that exists only in the denominator is not
        # a finding. Publishing one arm and not the other is how that goes
        # unnoticed (finding T3.1; the arm itself was dead code, X5/R8).
        cnt = count_outcome(outcome)
        if cnt in stack.columns:
            c_obs, c_p, c_draws = randomization_p(
                panel, real_starts, cnt, EVENT_WINDOW_PRE, post, args.draws, rng,
                counts=True, windows=RI_WINDOWS, extra=COVARIATES,
                ledger=_ri_ledger(cnt, post, "ppml"),
                seed=_ri_seed(cnt, post, "ppml"))
            if c_obs is not None:
                rows.append({"outcome": cnt, "post_window": post,
                             "estimator": "PPML_count_offset",
                             "first_week_chi2": c_obs,
                             "first_week_mean_coef": first_week_mean(stack, cnt,
                                                                     counts=True,
                                                                     extra=COVARIATES),
                             "p_randomization": c_p, "n_draws": len(c_draws),
                             "null_sd": float(c_draws.std()) if len(c_draws) else np.nan,
                             "n_episodes": len(real_starts), "n_obs": len(stack)})
                print(f"  {cnt:18s} post={post:>3}  chi2={c_obs:8.2f}  "
                      f"p_RI={c_p:.3f}  [PPML counts]")
            else:
                print(f"  {cnt} post={post}: counts arm not estimable")

        # -- dose-response arm: the effect per SD of episode intensity (D6) --
        #
        # SECONDARY and pre-specified as such; the binary arm stays primary
        # because it is what was pre-registered. It is here because the binary
        # design treats a 12.67-peak episode and a 1.40-peak one identically, and
        # peak CAI-D spans 9x across the discovery episodes.
        #
        # It is here at all because it was DEAD CODE: fit_dose_response was
        # written, documented, committed, and called by nothing — a repo-wide
        # grep returned only its own def. That is the third time in this rebuild
        # a documented arm turned out to be wired into nothing, after the PPML
        # counts arm (X5/R8) and the B-HEARD control (X6). A function nobody
        # calls is a claim nobody tested.
        if post == args.post:
            dose = fit_dose_response(stack, outcome,
                                     dict(zip(ep["start"], ep["peak_cai_d"])))
            if dose is None:
                print(f"  {outcome} post={post}: dose arm not estimable")
            else:
                k = "_post_dose"
                rows.append({"outcome": outcome, "post_window": post,
                             "estimator": "OLS_share_dose_per_sd",
                             "first_week_chi2": np.nan,
                             "first_week_mean_coef": float(dose.coef()[k]),
                             # No RI here: the permutation would have to redraw
                             # intensities as well as dates, which is a different
                             # null from the one the primary arm tests. The
                             # asymptotic p is reported and labelled as such
                             # rather than a randomization p left blank.
                             "p_randomization": np.nan,
                             "p_asymptotic": float(dose.pvalue()[k]),
                             "se": float(dose.se()[k]),
                             "n_draws": 0, "null_sd": np.nan,
                             "n_episodes": len(real_starts), "n_obs": len(stack)})
                print(f"  {outcome:18s} post={post:>3}  "
                      f"coef/SD-intensity={dose.coef()[k]:+.5f}  "
                      f"p_asy={dose.pvalue()[k]:.3f}  [dose, secondary]")

        rows.append({"outcome": outcome, "post_window": post, "estimator": "OLS_share",
                     "first_week_chi2": obs,
                     "first_week_mean_coef": first_week_mean(stack, outcome, extra=COVARIATES),
                     "p_randomization": p_ri,
                     "n_draws": len(draws), "null_sd": float(draws.std()) if len(draws) else np.nan,
                     "n_episodes": len(real_starts), "n_obs": len(stack)})
        print(f"  {outcome:18s} post={post:>3}  chi2={obs:8.2f}  p_RI={p_ri:.3f}  ({len(draws)} draws)")

        if post == args.post:
            pd.DataFrame({"draw": np.arange(1, len(draws) + 1), "stat": draws}).assign(
                observed=obs, outcome=outcome).to_csv(
                OUTPUTS_TABLES / f"event_study_ri_draws_{outcome}.csv", index=False)

# A SMALLER RUN MUST NOT REPLACE A LARGER ONE (finding D1, re-found in 17).
#
# 18_null_calibration.py was given this rule after an 8-sim smoke test destroyed
# the 200-sim verdict it was gating on. The rule was never applied here, and
# this script has exactly the same shape: --draws exists so the estimator can be
# exercised cheaply, outputs/tables/ is gitignored so nothing is recoverable
# from git, and the artifact is the one carrying the primary inference.
#
# Found the same way as the original: a 2-draw run launched to prove the new
# calibration gate fires replaced a full result, reporting p_randomization = 1.0
# from two draws. The file is honest about itself — it records n_draws — but
# nothing stopped it and nothing said what it had overwritten, which is the
# error path indistinguishable from success.
_res = pd.DataFrame(rows)
_main = OUTPUTS_TABLES / "event_study_results.csv"
_draws_here = int(_res["n_draws"].max()) if len(_res) else 0
_prior = 0
if _main.exists():
    try:
        _prior = int(pd.read_csv(_main)["n_draws"].max())
    except Exception as e:
        print(f"could not read the existing result ({e}); treating it as absent")

# The sidecar is written unconditionally, before any decision about the main
# artifact, so a run that declines to publish still leaves its evidence.
_res.to_csv(OUTPUTS_TABLES / f"event_study_results_d{_draws_here}.csv", index=False)
pd.DataFrame(path_rows).to_csv(
    OUTPUTS_TABLES / f"event_study_path_d{_draws_here}.csv", index=False)

if _draws_here >= _prior:
    _res.to_csv(_main, index=False)
    pd.DataFrame(path_rows).to_csv(OUTPUTS_TABLES / "event_study_path.csv", index=False)
    if _prior:
        print(f"published: {_draws_here} draws replaces the {_prior}-draw result on disk")
else:
    print("=" * 70)
    print(f"REFUSING TO PUBLISH. This run used {_draws_here} draws; the result on "
          f"disk rests on {_prior}.")
    print(f"Its record is in event_study_results_d{_draws_here}.csv. "
          "event_study_results.csv is unchanged.")
    print("=" * 70)
# The closing line says what HAPPENED, not what was intended: it used to claim
# the main file was written even after the branch above had refused to.
if _draws_here >= _prior:
    print(f"\nwrote event_study_results.csv ({len(rows)} rows) and event_study_path.csv")
else:
    print(f"\nwrote event_study_results_d{_draws_here}.csv only ({len(rows)} rows); "
          "the main artifact was left untouched")
