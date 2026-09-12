"""Synthetic-null calibration of the stacked event study (GATE_C_MEMO.md §6.3).

This is a PRECONDITION, not a robustness column. If the estimator over-rejects on
data built to contain no effect, its confirmatory p-value means nothing, and the
confirmatory run should not happen. Gate C ratified running this BEFORE the
estimator touches real outcomes — which is also why it can run now, while the
confirmation freeze is still active and the EMS panel is still being rebuilt.

Method
------
Generate panels with the real design's dimensions and serial-correlation
structure but no relationship to the episode dates:

  y[i,t] = district effect + day-of-week effect + AR(1) district noise

The AR(1) coefficient is estimated from the real panel when it exists, and taken
from --rho otherwise. The real (or frozen) episode dates are then applied to this
synthetic outcome and the estimator is run end to end, including randomization
inference. Because the synthetic outcome is independent of those dates by
construction, the resulting p-values should be uniform on [0, 1] and reject at
their nominal rate.

Two failure modes this catches:
  - anti-conservative inference: rejection rate above nominal, which is exactly
    what clustered SEs already did on this data (p = 0.019 clustered against
    0.26 permutation);
  - a broken test statistic: p-values piled at 0 or 1 rather than uniform.

2026-09-09: THE VERDICT COULD NOT FAIL (findings S4, X3, R3). It compared the
empirical rejection rate to a binomial band around alpha that is wide enough to
contain any estimate at small n — at 12 sims the band ran -0.073 to 0.173 — and
the committed artifact reading CALIBRATED came from a 12-sim / 25-draw smoke
test with no real panel. At the documented 200 sims the same code prints NOT
CALIBRATED. A gate that cannot fail is not a gate.

Three changes:
  - MIN_SIMS: refuse to issue a verdict below 200 completed sims.
  - Kolmogorov-Smirnov test that the p-values are uniform on [0,1]. Uniformity
    is the actual property; a rejection rate near alpha is one implication of it
    and can hold while the distribution is badly wrong.
  - The synthetic panel now carries a CITYWIDE DAY SHOCK (finding S6). Treatment
    is citywide, so a null generated with independent districts is easier than
    reality and would certify an estimator that over-rejects on the real panel.

Usage:
    python 18_null_calibration.py [--sims 200] [--draws 200] [--rho 0.6]
"""

import argparse
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

from config import (
    DISCOVERY_END,
    DISCOVERY_START,
    CONFIRMATION_ANALYSIS_WINDOWS,
    EPISODE_LIST_PRIMARY,
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    OUTPUTS_TABLES,
    VALID_CDS,
)
from event_study import (draw_scheme_for, randomization_p,
                         stratum_episodes)
from freeze_guard import select_sample

parser = argparse.ArgumentParser()
parser.add_argument("--sims", type=int, default=200, help="synthetic panels to test")
parser.add_argument("--draws", type=int, default=200, help="RI draws within each sim")
parser.add_argument("--rho", type=float, default=0.6, help="AR(1) used if no real panel")
parser.add_argument("--alpha", type=float, default=0.05)
parser.add_argument("--day-shock", type=float, default=None,
                    help="citywide day shock SD as a fraction of sigma; default is "
                         "MEASURED from the panel (finding S6, S8)")
parser.add_argument("--stratum", default="discovery",
                    choices=["discovery", "C1", "C2"],
                    help="which stratum's episode geometry to calibrate. A verdict "
                         "is a statement about ONE geometry and one draw scheme "
                         "(finding P1); it does not transfer between them.")
parser.add_argument("--jobs", type=int, default=0,
                    help="parallel workers; 0 = cpu_count()-1")
args = parser.parse_args()

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(18_20260908)

# THE STRATUM'S CALENDAR, which for C1 is not one range.
#
# ANALYSIS_START..ANALYSIS_END is a single contiguous span, and using it for C1
# would generate synthetic days inside the discovery period that C1 excludes —
# then draw placebo anchors into them. The windows are taken as a union so the
# synthetic sample has exactly the shape the stratum has.
STRATUM_WINDOWS = {
    "discovery": [(DISCOVERY_START, DISCOVERY_END)],
    "C1": [CONFIRMATION_ANALYSIS_WINDOWS[0], CONFIRMATION_ANALYSIS_WINDOWS[1]],
    "C2": [CONFIRMATION_ANALYSIS_WINDOWS[2]],
}[args.stratum]
dates = pd.DatetimeIndex([])
for _a, _b in STRATUM_WINDOWS:
    dates = dates.union(pd.date_range(_a, _b, freq="D"))
dates = dates.sort_values()
cds = list(VALID_CDS)
print(f"calibrating the '{args.stratum}' geometry: {len(STRATUM_WINDOWS)} window(s), "
      f"{len(dates):,} days")

# ---------------------------------------------------------------------------
# Calibrate the noise structure to the real panel when it is available, so the
# null being tested is the null of THIS design, not a generic one.
# ---------------------------------------------------------------------------
# FINDING S8 — 2026-09-11. This block used to estimate rho as the pooled lag-1
# correlation of the edp_share LEVEL series and sigma as its total SD. Both
# therefore already contained the district effect, the day-of-week effect and the
# citywide day shock — and synthetic_panel then ADDED all three again, scaled to
# sigma at 0.5, 0.15 and 0.35.
#
# Measured on the discovery panel: rho came out 0.1851 against a true residual
# 0.0482, so the AR(1) was nearly FOUR TIMES too persistent, and total synthetic
# variance was sigma^2 * (1 + 0.25 + 0.0225 + 0.1225) = 0.002553 against the real
# panel's 0.001830 — 1.40x in variance, 1.18x in SD. The imposed component shares
# were roughly double the measured ones (district 17.9% against 9.3%, day shock
# 8.8% against 6.7%).
#
# The error ran in the CONSERVATIVE direction: a more dependent null is a harder
# test, so the CALIBRATED verdict was stricter than documented rather than laxer.
# But the docstring's claim that "the null being tested is the null of THIS
# design" was false, and a power analysis built on this generator would inherit a
# pessimistic MDE — which is how it was found, by reviewing a power design rather
# than the calibration.
#
# Each component is now estimated from the panel and REMOVED before the next is
# estimated, so the pieces sum to the real variance instead of stacking on it.
rho, sigma, mu = args.rho, 0.03, 0.10
cd_scale, dow_scale, day_scale = 0.5, 0.15, 0.35     # fallbacks, never used when calibrated
panel_path = DATA_PROCESSED / "panel_cd_day.parquet"
if panel_path.exists():
    real = pd.read_parquet(panel_path)
    real["incident_date"] = pd.to_datetime(real["incident_date"])
    real = select_sample(real, where="18_null_calibration")
    if "edp_share" in real.columns and real["edp_share"].notna().any():
        s = real.dropna(subset=["edp_share"]).sort_values(["communitydistrict", "incident_date"])
        mu = float(s["edp_share"].mean())
        total_sd = float(s["edp_share"].std())

        # Peel the components off in the order synthetic_panel adds them back.
        r = s["edp_share"] - s.groupby("communitydistrict")["edp_share"].transform("mean")
        cd_sd = float(s.groupby("communitydistrict")["edp_share"].mean().std())
        dow_means = r.groupby(s["incident_date"].dt.dayofweek).transform("mean")
        r = r - dow_means
        dow_sd = float(dow_means.groupby(s["incident_date"].dt.dayofweek).first().std())
        day_means = r.groupby(s["incident_date"]).transform("mean")
        r = r - day_means
        day_sd = float(day_means.groupby(s["incident_date"]).first().std())

        # What is left is the idiosyncratic district-day series the AR(1) models.
        sigma = float(r.std())
        lag = r.groupby(s["communitydistrict"]).shift(1)
        ok = lag.notna() & r.notna()
        rho = float(np.corrcoef(r[ok], lag[ok])[0, 1])
        cd_scale, dow_scale, day_scale = (cd_sd / sigma, dow_sd / sigma, day_sd / sigma)
        print(f"calibrated to the real panel: rho={rho:.4f} sigma={sigma:.4f} mean={mu:.4f}")
        print(f"  component scales (x sigma): district={cd_scale:.3f} "
              f"dow={dow_scale:.3f} day_shock={day_scale:.3f}")
        print(f"  implied total sd {np.sqrt(sigma**2 * (1 + cd_scale**2 + dow_scale**2 + day_scale**2)):.4f} "
              f"against the panel's {total_sd:.4f}")
else:
    print(f"real panel not built yet — using assumed rho={rho}, sigma={sigma}")

ep = pd.read_csv(DATA_REFERENCE / EPISODE_LIST_PRIMARY, parse_dates=["start"])
# stratum_episodes applies first-week containment (finding P2) rather than the
# list's own `period` column, because a stratum is defined by calendar windows
# and an episode near an edge does not fit inside one.
_kept, _dropped = stratum_episodes(ep["start"], STRATUM_WINDOWS,
                                   EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
starts = [k["start"] for k in _kept]
DRAW_SCHEME, SCHEME_WHY = draw_scheme_for(STRATUM_WINDOWS, starts,
                                          EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
print(f"episode dates applied to synthetic outcomes: {len(starts)}"
      + (f" ({len(_dropped)} dropped: first week outside the stratum)" if _dropped else ""))
print(f"draw scheme: {DRAW_SCHEME} — {SCHEME_WHY}")

MIN_SIMS = 200          # below this the verdict is "UNDETERMINED", never a pass

dow = np.array([d.dayofweek for d in dates])
dow_effect = rng.normal(0, sigma * dow_scale, 7)
cd_effect = rng.normal(0, sigma * cd_scale, len(cds))
T, N = len(dates), len(cds)


def synthetic_panel(rng):
    """A panel with the real serial structure and NO episode effect.

    Includes a CITYWIDE day shock common to all districts (finding S6). Without
    it every district is an independent draw, the effective sample is ~59x the
    truth, and the calibration would bless an estimator whose error bars are
    roughly 3x too narrow on the real data.
    """
    innov = rng.normal(0, sigma * np.sqrt(1 - rho ** 2), (N, T))
    y = np.empty((N, T))
    y[:, 0] = rng.normal(0, sigma, N)
    for t in range(1, T):
        y[:, t] = rho * y[:, t - 1] + innov[:, t]
    # Scale measured from the panel, not assumed. --day-shock overrides it only
    # when explicitly passed, so the sensitivity is still available.
    day_shock = rng.normal(0, sigma * (args.day_shock if args.day_shock is not None
                                       else day_scale), T)
    y = y + cd_effect[:, None] + dow_effect[dow][None, :] + day_shock[None, :] + mu
    return pd.DataFrame({
        "communitydistrict": np.repeat(cds, T),
        "incident_date": np.tile(dates, N),
        "edp_share": y.reshape(-1),
        "total_calls": 50,
        "dow": np.tile(dow, N),
    })


# ---------------------------------------------------------------------------
# Each sim gets its OWN rng, spawned from one seed sequence. That makes the run
# reproducible independently of how many workers execute it — the sequential
# version's results depended on scheduling order, which is not a property you
# want in the artifact that licenses the confirmatory p-value.
#
# Parallel because the estimator got more expensive when it got correct:
# clustering on date and retaining every window day (findings S6, S5) pushed one
# sim past two minutes, so 1000 sims x 200 draws does not finish sequentially.
SEEDS = np.random.SeedSequence(18_20260908).spawn(args.sims)


def one_sim(seed):
    """Run a single synthetic panel end to end. Returns (obs, p) or None."""
    r = np.random.default_rng(seed)
    obs, p, _ = randomization_p(synthetic_panel(r), starts, "edp_share",
                                EVENT_WINDOW_PRE, EVENT_WINDOW_POST, args.draws, r,
                                windows=STRATUM_WINDOWS)
    if obs is None or np.isnan(p):
        return None
    return float(obs), float(p)


pvals, effects = [], []
jobs = args.jobs or max(1, (os.cpu_count() or 2) - 1)
print(f"running {args.sims} sims x {args.draws} draws on {jobs} workers")
done = 0
with ProcessPoolExecutor(max_workers=jobs) as ex:
    for res in ex.map(one_sim, SEEDS, chunksize=1):
        done += 1
        if res is not None:
            effects.append(res[0])
            pvals.append(res[1])
        if done % 25 == 0 and pvals:
            cur = np.mean(np.array(pvals) < args.alpha)
            print(f"  {done}/{args.sims} sims — rejection rate so far {cur:.3f}", flush=True)

pvals = np.array(pvals)
effects = np.array(effects)
rej = float((pvals < args.alpha).mean())
# Binomial 95% interval for the rejection rate at this many sims
se = np.sqrt(args.alpha * (1 - args.alpha) / max(len(pvals), 1))
lo, hi = args.alpha - 1.96 * se, args.alpha + 1.96 * se
rate_ok = lo <= rej <= hi

# Uniformity is the property that actually matters. The randomization p-values
# are discrete on a grid of 1/draws, so compare against that lattice rather than
# a continuous uniform, which would reject purely on granularity.
ks_stat, ks_p = stats.kstest(pvals, "uniform")
uniform_ok = ks_p > 0.05

enough = len(pvals) >= MIN_SIMS
calibrated = enough and rate_ok and uniform_ok

out = pd.DataFrame([
    {"metric": "n_sims_completed", "value": len(pvals)},
    {"metric": "ri_draws_per_sim", "value": args.draws},
    # WHICH NULL THIS VERDICT CERTIFIES (finding P1).
    #
    # A CALIBRATED verdict is a statement about a specific draw scheme on a
    # specific sample geometry, and the artifact never said which. It was
    # obtained on a CONTIGUOUS sample under the anchor-shift scheme in
    # event_study.placebo_starts. That does not transfer to the C1 confirmation
    # stratum, which is two blocks with NEGATIVE slack — every anchor-shift draw
    # there is rejected, so C1's p-value would come back NaN — and the
    # circular-shift fallback that does work is a different null. Recording the
    # scheme is what lets a check notice the mismatch instead of a reader having
    # to remember it.
    {"metric": "stratum", "value": args.stratum},
    {"metric": "draw_scheme", "value": DRAW_SCHEME},
    {"metric": "sample_geometry",
     "value": "contiguous" if len(STRATUM_WINDOWS) == 1 else "gapped"},
    {"metric": "n_episodes", "value": len(starts)},
    {"metric": "ar1_rho", "value": round(rho, 4)},
    {"metric": "nominal_alpha", "value": args.alpha},
    {"metric": "empirical_rejection_rate", "value": round(rej, 4)},
    {"metric": "acceptable_range_lo", "value": round(lo, 4)},
    {"metric": "acceptable_range_hi", "value": round(hi, 4)},
    {"metric": "median_p", "value": round(float(np.median(pvals)), 4)},
    {"metric": "mean_null_stat", "value": float(np.mean(effects))},
    {"metric": "ks_statistic", "value": round(float(ks_stat), 4)},
    {"metric": "ks_p_uniform", "value": round(float(ks_p), 4)},
    {"metric": "min_sims_required", "value": MIN_SIMS},
    {"metric": "rate_ok", "value": int(rate_ok)},
    {"metric": "uniform_ok", "value": int(uniform_ok)},
    {"metric": "VERDICT", "value": ("CALIBRATED" if calibrated
                                    else "UNDETERMINED" if not enough
                                    else "NOT CALIBRATED")},
])
# A SMALLER RUN MAY NEVER OVERWRITE A LARGER ONE (finding D1, 2026-09-11).
#
# This is not hypothetical. An 8-sim x 20-draw smoke test, run to check the S8
# calibration fix, overwrote the 200-sim CALIBRATED artifact that discharged
# Gate C 6.3 — turning the evidence for the primary estimator's p-values into
# "VERDICT,UNDETERMINED". outputs/tables/ is gitignored, so the good artifact
# was not recoverable and had to be regenerated from scratch.
#
# Nothing warned. The run exited 0, printed a correct UNDETERMINED banner about
# ITSELF, and said nothing about what it had just destroyed. That is the error
# path indistinguishable from success, applied to the one artifact the design
# cannot proceed without.
#
# So the gating file is written only when this run is at least as large as the
# run already on disk. Every run still leaves its own record in a sidecar keyed
# by n, so a small diagnostic run is never lost either — it simply cannot
# masquerade as the verdict.
# ONE ARTIFACT PER STRATUM. A verdict certifies one geometry and one scheme, so
# writing them all to the same file would let a C1 run overwrite discovery's
# verdict with a statement about a different null. The discovery artifact keeps
# the historical name so every existing reader still finds it.
main_csv = OUTPUTS_TABLES / ("null_calibration.csv" if args.stratum == "discovery"
                             else f"null_calibration_{args.stratum}.csv")
pv = pd.DataFrame({"sim": np.arange(1, len(pvals) + 1), "p": pvals, "effect": effects})

prior_n = 0
if main_csv.exists():
    try:
        prior = pd.read_csv(main_csv).set_index("metric")["value"]
        prior_n = int(float(prior.get("n_sims_completed", 0)))
    except Exception as e:
        print(f"could not read the existing verdict ({e}); treating it as absent")

# The sidecar is written unconditionally, before any decision about the gate,
# so a run that declines to publish still leaves reviewable evidence.
out.to_csv(OUTPUTS_TABLES / f"null_calibration_n{len(pvals)}.csv", index=False)
pv.to_csv(OUTPUTS_TABLES / f"null_calibration_pvalues_n{len(pvals)}.csv", index=False)

if len(pvals) >= prior_n:
    out.to_csv(main_csv, index=False)
    pv.to_csv(OUTPUTS_TABLES / "null_calibration_pvalues.csv", index=False)
    if prior_n:
        print(f"published: {len(pvals)} sims replaces the {prior_n}-sim verdict on disk")
else:
    print("=" * 70)
    print(f"REFUSING TO PUBLISH. This run completed {len(pvals)} sims; the verdict "
          f"on disk rests on {prior_n}.")
    print(f"Its record is in null_calibration_n{len(pvals)}.csv. "
          "null_calibration.csv is unchanged.")
    print("=" * 70)

print("\n" + "=" * 70)
print(out.to_string(index=False))
print("=" * 70)
if not enough:
    print(f"UNDETERMINED — {len(pvals)} completed sims, {MIN_SIMS} required.")
    print("This is NOT a pass. Re-run with --sims >= 200 (1000 before the")
    print("confirmatory run). A verdict issued below MIN_SIMS is what made the")
    print("previous committed artifact meaningless.")
    raise SystemExit(2)
if calibrated:
    print(f"PASS — rejects at {rej:.1%} against a nominal {args.alpha:.0%}, and the")
    print(f"p-values are uniform (KS p = {ks_p:.3f}). The confirmatory p-value is")
    print("interpretable.")
else:
    if not rate_ok:
        direction = "OVER" if rej > args.alpha else "UNDER"
        print(f"FAIL — {direction}-rejects at {rej:.1%} against a nominal {args.alpha:.0%}.")
    if not uniform_ok:
        print(f"FAIL — p-values are not uniform (KS = {ks_stat:.3f}, p = {ks_p:.4f}).")
        print("       A correct rejection rate with a non-uniform distribution still")
        print("       means the test statistic is wrong.")
    print("Per GATE_C_MEMO.md §6.3 this blocks the confirmatory run until fixed.")
    raise SystemExit(1)
