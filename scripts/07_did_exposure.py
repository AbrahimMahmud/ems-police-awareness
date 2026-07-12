"""Exposure-intensity DID (Justin's design; REWORK_PLAN §5.2).

Specification (math):
    y_it = alpha_i + lambda_e(t) + beta * (Treated_i x Post_t) + eps_it
within +/-7-day windows around each high-awareness episode start, where
  Treated_i = 1 for districts in the top quartile of pct_black (ACS 2015-19)
  Control   = (a) Q2 districts [Justin]; (b) most demographically even
              districts (lowest quartile of Herfindahl over race shares)
  Post_t    = 1 for event days +1..+7 (0 for -7..-1; day 0 excluded)
  lambda_e  = episode fixed effects; alpha_i = district fixed effects
Estimands: (i) week-after vs week-before (primary, per meeting notes);
(ii) day +7 vs day -1. SEs clustered by date. Windows truncated at the
next episode's start (no overlap).

Outputs: outputs/tables/did_exposure_results.csv, did_event_path.csv
"""

import numpy as np
import pandas as pd
import pyfixest as pf

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
)

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
panel = panel[panel["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
panel["date_id"] = panel["incident_date"].dt.strftime("%Y%m%d").astype(int)

acs = pd.read_csv(DATA_REFERENCE / "acs_2019_cd_demographics.csv")
shares = acs[["pct_white_acs", "pct_black_acs", "pct_hispanic_acs", "pct_asian_acs"]] / 100
acs["herfindahl"] = (shares ** 2).sum(axis=1)
acs["q_black"] = pd.qcut(acs["pct_black_acs"], 4, labels=False)
acs["q_herf"] = pd.qcut(acs["herfindahl"], 4, labels=False)

treated_cds = set(acs.loc[acs["q_black"] == 3, "communitydistrict"])
controls = {
    "Q2_black": set(acs.loc[acs["q_black"] == 1, "communitydistrict"]),
    "even_mix": set(acs.loc[acs["q_herf"] == 0, "communitydistrict"]),
}

ep = pd.read_csv(OUTPUTS_TABLES / "awareness_episodes.csv", parse_dates=["start", "end"])
starts = ep["start"].tolist()

frames = []
for i, s in enumerate(starts):
    lo, hi = s - pd.Timedelta(days=7), s + pd.Timedelta(days=7)
    if i + 1 < len(starts):  # truncate at next episode
        hi = min(hi, starts[i + 1] - pd.Timedelta(days=1))
    w = panel[panel["incident_date"].between(lo, hi)].copy()
    w["episode"] = i + 1
    w["rel_day"] = (w["incident_date"] - s).dt.days
    frames.append(w)
win = pd.concat(frames, ignore_index=True)
win = win[win["rel_day"] != 0]
win["post"] = (win["rel_day"] > 0).astype(int)

rows, path_rows = [], []
for ctrl_name, ctrl_cds in controls.items():
    sub = win[win["communitydistrict"].isin(treated_cds | ctrl_cds)].copy()
    sub["treated"] = sub["communitydistrict"].isin(treated_cds).astype(int)
    sub["tp"] = sub["treated"] * sub["post"]
    for outcome in ["edp_share", "mh_narrow_share", "injury_share"]:
        d = sub.dropna(subset=[outcome])
        m = pf.feols(f"{outcome} ~ tp + post | communitydistrict + episode", d, vcov={"CRV1": "date_id"})
        rows.append({"estimand": "week_after_vs_before", "control": ctrl_name,
                     "outcome": outcome, "coef": m.coef()["tp"], "se": m.se()["tp"],
                     "p": m.pvalue()["tp"], "n_obs": len(d),
                     "n_treated_cds": len(treated_cds), "n_control_cds": len(ctrl_cds)})
        d7 = d[d["rel_day"].isin([-1, 7])]
        m7 = pf.feols(f"{outcome} ~ tp + post | communitydistrict + episode", d7, vcov={"CRV1": "date_id"})
        rows.append({"estimand": "day7_vs_daym1", "control": ctrl_name,
                     "outcome": outcome, "coef": m7.coef()["tp"], "se": m7.se()["tp"],
                     "p": m7.pvalue()["tp"], "n_obs": len(d7),
                     "n_treated_cds": len(treated_cds), "n_control_cds": len(ctrl_cds)})
    # event path: treated-minus-control mean by rel_day (for the figure)
    for rd in range(-7, 8):
        dd = sub[sub["rel_day"] == rd]
        if len(dd):
            t = dd.loc[dd["treated"] == 1, "edp_share"].mean()
            c = dd.loc[dd["treated"] == 0, "edp_share"].mean()
            path_rows.append({"control": ctrl_name, "rel_day": rd, "t_minus_c": t - c})

res = pd.DataFrame(rows)
res.to_csv(OUTPUTS_TABLES / "did_exposure_results.csv", index=False)
pd.DataFrame(path_rows).to_csv(OUTPUTS_TABLES / "did_event_path.csv", index=False)
pd.set_option("display.width", 180)
print(res.round(6).to_string(index=False))
