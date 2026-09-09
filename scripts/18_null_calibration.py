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

import numpy as np
import pandas as pd
from scipy import stats

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    OUTPUTS_TABLES,
    VALID_CDS,
)
from event_study import randomization_p
from freeze_guard import select_sample

parser = argparse.ArgumentParser()
parser.add_argument("--sims", type=int, default=200, help="synthetic panels to test")
parser.add_argument("--draws", type=int, default=200, help="RI draws within each sim")
parser.add_argument("--rho", type=float, default=0.6, help="AR(1) used if no real panel")
parser.add_argument("--alpha", type=float, default=0.05)
parser.add_argument("--day-shock", type=float, default=0.35,
                    help="citywide day shock SD, as a fraction of sigma (finding S6)")
args = parser.parse_args()

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(18_20260908)

dates = pd.date_range(ANALYSIS_START, ANALYSIS_END, freq="D")
cds = list(VALID_CDS)

# ---------------------------------------------------------------------------
# Calibrate the noise structure to the real panel when it is available, so the
# null being tested is the null of THIS design, not a generic one.
# ---------------------------------------------------------------------------
rho, sigma, mu = args.rho, 0.03, 0.10
panel_path = DATA_PROCESSED / "panel_cd_day.parquet"
if panel_path.exists():
    real = pd.read_parquet(panel_path)
    real["incident_date"] = pd.to_datetime(real["incident_date"])
    real = select_sample(real, where="18_null_calibration")
    if "edp_share" in real.columns and real["edp_share"].notna().any():
        s = real.dropna(subset=["edp_share"]).sort_values(["communitydistrict", "incident_date"])
        d = s.groupby("communitydistrict")["edp_share"]
        lag = d.shift(1)
        ok = lag.notna() & s["edp_share"].notna()
        rho = float(np.corrcoef(s.loc[ok, "edp_share"], lag[ok])[0, 1])
        sigma = float(s["edp_share"].std())
        mu = float(s["edp_share"].mean())
        print(f"calibrated to the real panel: rho={rho:.3f} sigma={sigma:.4f} mean={mu:.4f}")
else:
    print(f"real panel not built yet — using assumed rho={rho}, sigma={sigma}")

ep = pd.read_csv(DATA_REFERENCE / "confirmation_episodes.csv", parse_dates=["start"])
starts = ep.loc[ep["period"] == "discovery", "start"].sort_values().tolist()
print(f"episode dates applied to synthetic outcomes: {len(starts)}")

MIN_SIMS = 200          # below this the verdict is "UNDETERMINED", never a pass

dow = np.array([d.dayofweek for d in dates])
dow_effect = rng.normal(0, sigma * 0.15, 7)
cd_effect = rng.normal(0, sigma * 0.5, len(cds))
T, N = len(dates), len(cds)


def synthetic_panel():
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
    day_shock = rng.normal(0, sigma * args.day_shock, T)
    y = y + cd_effect[:, None] + dow_effect[dow][None, :] + day_shock[None, :] + mu
    return pd.DataFrame({
        "communitydistrict": np.repeat(cds, T),
        "incident_date": np.tile(dates, N),
        "edp_share": y.reshape(-1),
        "total_calls": 50,
        "dow": np.tile(dow, N),
    })


# ---------------------------------------------------------------------------
pvals, effects = [], []
for i in range(1, args.sims + 1):
    obs, p, _ = randomization_p(synthetic_panel(), starts, "edp_share",
                                EVENT_WINDOW_PRE, EVENT_WINDOW_POST, args.draws, rng)
    if obs is None or np.isnan(p):
        continue
    pvals.append(p)
    effects.append(obs)
    if i % 25 == 0:
        cur = np.mean(np.array(pvals) < args.alpha)
        print(f"  {i}/{args.sims} sims — rejection rate so far {cur:.3f}")

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
out.to_csv(OUTPUTS_TABLES / "null_calibration.csv", index=False)
pd.DataFrame({"sim": np.arange(1, len(pvals) + 1), "p": pvals, "effect": effects}).to_csv(
    OUTPUTS_TABLES / "null_calibration_pvalues.csv", index=False)

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
