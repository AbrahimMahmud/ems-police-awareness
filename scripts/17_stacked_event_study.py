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

Windows are truncated at the next episode's start, and any day belonging to more
than one episode window is dropped, so no observation is a control for one event
while being treated in another — the failure mode that made the original
"difference-in-differences" uninterpretable (REWORK_PLAN I4).

Inference
---------
Episode-level randomization inference is the PRIMARY p-value, not a robustness
column. Clustered standard errors have already proved anti-conservative on this
data (p = 0.019 clustered against 0.26 permutation). Under the null the estimator
is re-run on RANDOMIZATION_DRAWS re-draws of placebo episode dates that preserve
the real episodes' spacing, and the reported p is the share of placebo statistics
at least as extreme as the observed one.

The test statistic is the first-week effect: the mean of the day 0..7
coefficients, two-sided, per the H1 reframe ratified at Gate C §6.1.

Outcomes are estimated on shares (OLS) and on counts (PPML with a log
total-calls offset), because the finding is compositional and counts have stayed
non-significant; both are reported rather than the more favourable one.

Usage:
    python 17_stacked_event_study.py [--outcome edp_share] [--draws 2000]
"""

import argparse

import numpy as np
import pandas as pd
import pyfixest as pf

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EVENT_REFERENCE_DAY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_POST_SENSITIVITY,
    EVENT_WINDOW_PRE,
    FREEZE_ACTIVE,
    H1_OUTCOMES,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    RANDOMIZATION_DRAWS,
)
from event_study import build_stack, first_week_effect, randomization_p
from freeze_guard import assert_discovery_only, freeze_banner

parser = argparse.ArgumentParser()
parser.add_argument("--outcome", default=None, help="default: every H1 outcome")
parser.add_argument("--draws", type=int, default=RANDOMIZATION_DRAWS)
parser.add_argument("--post", type=int, default=EVENT_WINDOW_POST)
args = parser.parse_args()

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
freeze_banner("17_stacked_event_study")
rng = np.random.default_rng(20260908)


# ---------------------------------------------------------------------------
panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
panel["incident_date"] = pd.to_datetime(panel["incident_date"])
panel = panel[panel["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
assert_discovery_only(panel, where="17_stacked_event_study")
panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
panel["dow"] = panel["incident_date"].dt.dayofweek

ep = pd.read_csv(DATA_REFERENCE / "confirmation_episodes.csv", parse_dates=["start", "end"])
if FREEZE_ACTIVE:
    ep = ep[ep["period"] == "discovery"]
ep = ep.sort_values("start").reset_index(drop=True)
real_starts = ep["start"].tolist()
print(f"episodes in scope: {len(ep)}  ({'discovery only' if FREEZE_ACTIVE else 'all'})")

lo_d, hi_d = panel["incident_date"].min(), panel["incident_date"].max()
gaps = np.diff([d.toordinal() for d in real_starts]) if len(real_starts) > 1 else np.array([30])

outcomes = [args.outcome] if args.outcome else list(H1_OUTCOMES)
rows, path_rows = [], []

for outcome in outcomes:
    for post in dict.fromkeys([args.post, *EVENT_WINDOW_POST_SENSITIVITY]):
        stack = build_stack(panel, real_starts, EVENT_WINDOW_PRE, post)
        if stack.empty:
            continue
        obs = first_week_effect(stack, outcome)
        if obs is None:
            print(f"  {outcome} post={post}: not estimable")
            continue

        # -- event-time path (only for the primary window) --
        if post == args.post:
            d = stack[stack["rel_day"] != EVENT_REFERENCE_DAY].dropna(subset=[outcome])
            m = pf.feols(f"{outcome} ~ C(rel_day) | ep_cd + dow", d, vcov="hetero")
            for n in m._coefnames:
                if "rel_day" not in n:
                    continue
                rd = int(float(n.split("[T.")[1].rstrip("]")))
                path_rows.append({"outcome": outcome, "rel_day": rd,
                                  "coef": float(m.coef()[n]), "se": float(m.se()[n])})

        # -- randomization inference (primary p-value) --
        obs, p_ri, draws = randomization_p(panel, real_starts, outcome,
                                           EVENT_WINDOW_PRE, post, args.draws, rng)

        rows.append({"outcome": outcome, "post_window": post, "estimator": "OLS_share",
                     "first_week_effect": obs, "p_randomization": p_ri,
                     "n_draws": len(draws), "null_sd": float(draws.std()) if len(draws) else np.nan,
                     "n_episodes": len(real_starts), "n_obs": len(stack)})
        print(f"  {outcome:18s} post={post:>3}  effect={obs:+.6f}  p_RI={p_ri:.3f}  ({len(draws)} draws)")

        if post == args.post:
            pd.DataFrame({"draw": np.arange(1, len(draws) + 1), "stat": draws}).assign(
                observed=obs, outcome=outcome).to_csv(
                OUTPUTS_TABLES / f"event_study_ri_draws_{outcome}.csv", index=False)

pd.DataFrame(rows).to_csv(OUTPUTS_TABLES / "event_study_results.csv", index=False)
pd.DataFrame(path_rows).to_csv(OUTPUTS_TABLES / "event_study_path.csv", index=False)
print(f"\nwrote event_study_results.csv ({len(rows)} rows) and event_study_path.csv")
