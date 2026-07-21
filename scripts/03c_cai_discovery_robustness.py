"""Does the composite awareness index (CAI-D) change the discovery-period result?
(Justin's Q3, 2026-07-18.)

Re-runs the discovery-period (2017-2020 ONLY) EDP-share and mh_narrow-share
effects using CAI-D as the treatment in place of the legacy Twitter measure,
alongside the legacy result for direct comparison. This is a robustness check
on the DISCOVERY sample and does NOT touch extension-period outcomes, so it
does not engage the confirmation freeze (CONFIRMATION_PLAN.md).

Output: outputs/tables/cai_discovery_robustness.csv
"""

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats

from config import DATA_PROCESSED, MIN_TOTAL_CALLS_FOR_SHARE, OUTPUTS_TABLES

DISC_START, DISC_END = "2017-01-01", "2020-12-31"   # hard discovery-only guard

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
panel = panel[panel["incident_date"].between(DISC_START, DISC_END)]
panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
panel["month_year"] = panel["year"] * 100 + panel["month"]
panel["date_id"] = panel["incident_date"].dt.strftime("%Y%m%d").astype(int)


def windows_from(series_df, col):
    s = series_df.sort_values("date").reset_index(drop=True)
    out = pd.DataFrame({"date": s["date"]})
    out["w35"] = s[col].shift(3).add(s[col].shift(4)).add(s[col].shift(5)).div(3)
    for k in range(0, 8):
        out[f"lag{k}"] = s[col].shift(k)
    return out


# CAI-D (composite index)
cai = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")[["date", "cai_d"]]
caiw = windows_from(cai, "cai_d")

# Legacy Twitter (log)
tw = pd.read_parquet(DATA_PROCESSED / "awareness_daily.parquet")[["date", "aware_log"]]
tww = windows_from(tw, "aware_log")

FE = "communitydistrict + dow + month_year"
VC = {"CRV1": "date_id"}
rows = []


def joint07(m, aware, G):
    names = [f"lag{k}" for k in range(0, 8) if f"lag{k}" in m._coefnames]
    V = pd.DataFrame(m._vcov, index=m._coefnames, columns=m._coefnames).loc[names, names].to_numpy()
    b = m.coef().loc[names].to_numpy()
    V = (V + V.T) / 2
    ev, evec = np.linalg.eigh(V)
    keep = ev > 1e-9 * ev.max()
    q = int(keep.sum())
    W = float(((evec.T @ b)[keep] ** 2 / ev[keep]).sum())
    return 1 - stats.f.cdf(W / q, q, G - 1)


for label, w in [("legacy_twitter", tww), ("CAI_D", caiw)]:
    d = panel.merge(w, left_on="incident_date", right_on="date", how="left")
    G = d["date_id"].nunique()
    for outcome in ["edp_share", "mh_narrow_share"]:
        dd = d.dropna(subset=[outcome, "w35"])
        m = pf.feols(f"{outcome} ~ w35 | {FE}", dd, vcov=VC)
        dj = d.dropna(subset=[outcome] + [f"lag{k}" for k in range(8)])
        mj = pf.feols(f"{outcome} ~ " + " + ".join(f"lag{k}" for k in range(8)) + f" | {FE}", dj, vcov=VC)
        rows.append({
            "measure": label, "outcome": outcome,
            "w35_coef": m.coef()["w35"], "w35_se": m.se()["w35"], "w35_p": m.pvalue()["w35"],
            "joint_lags07_p": joint07(mj, label, G), "n_obs": len(dd),
        })

res = pd.DataFrame(rows)
res.to_csv(OUTPUTS_TABLES / "cai_discovery_robustness.csv", index=False)
pd.set_option("display.width", 160)
print(res.round(6).to_string(index=False))
