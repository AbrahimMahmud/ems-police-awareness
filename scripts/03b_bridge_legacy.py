"""Bridge analysis: attribute the change from the legacy result to each correction.

Starts from a replica of the original specification (mh_broad share, z-scored
awareness, sparse lag set {0,1,2,3,7,14,21,28}, no leads, CD-clustered SEs) and
changes one element at a time toward the corrected primary specification, then
applies the two key sample exclusions. Each row reports the lag-7 coefficient
and the joint lags-0..7 test so the source of any change in conclusions is
transparent (REWORK_PLAN I1-I3, I10).

Output: outputs/tables/bridge_legacy_to_primary.csv
"""

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    LAGS,
    LEADS,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
)

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

SPARSE_LAGS = (0, 1, 2, 3, 7, 14, 21, 28)
FLOYD_EPISODE = ("2020-05-26", "2020-07-03")  # episode 6 in awareness_episodes.csv

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
lags = pd.read_parquet(DATA_PROCESSED / "awareness_lags.parquet")

df = panel.merge(lags, left_on="incident_date", right_on="date", how="left")
df = df[df["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
df = df[df["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]
df["month_year"] = df["year"] * 100 + df["month"]
df["date_id"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)


def joint_lags07(m, aware, n_clusters):
    names = [f"{aware}_lag{k}" for k in range(0, 8) if f"{aware}_lag{k}" in m._coefnames]
    V = pd.DataFrame(m._vcov, index=m._coefnames, columns=m._coefnames)
    b = m.coef().loc[names].to_numpy()
    Vr = V.loc[names, names].to_numpy()
    Vr = (Vr + Vr.T) / 2
    eigval, eigvec = np.linalg.eigh(Vr)
    keep = eigval > 1e-9 * eigval.max()
    q = int(keep.sum())
    b_rot = eigvec.T @ b
    W = float((b_rot[keep] ** 2 / eigval[keep]).sum())
    return 1 - stats.f.cdf(W / q, q, n_clusters - 1)


def run(name, data, outcome, aware, lag_set, with_leads, cluster):
    lag_cols = [f"{aware}_lag{k}" for k in lag_set]
    lead_cols = [f"{aware}_lead{j}" for j in LEADS] if with_leads else []
    d = data.dropna(subset=[outcome] + lag_cols + lead_cols).copy()
    rhs = " + ".join(lag_cols + lead_cols)
    fml = f"{outcome} ~ {rhs} | communitydistrict + dow + month_year"
    vc = {"CRV1": "communitydistrict" if cluster == "cd" else "date_id"}
    m = pf.feols(fml, d, vcov=vc)
    G = d["communitydistrict"].nunique() if cluster == "cd" else d["date_id"].nunique()
    lag7 = f"{aware}_lag7"
    return {
        "step": name,
        "outcome": outcome, "aware": aware,
        "lags": "sparse" if lag_set == SPARSE_LAGS else "all+leads" if with_leads else "all",
        "cluster": cluster,
        "n_obs": len(d), "n_dates": d["date_id"].nunique(),
        "lag7_coef": m.coef()[lag7], "lag7_se": m.se()[lag7], "lag7_p": m.pvalue()[lag7],
        "joint_lags07_p": joint_lags07(m, aware, G),
    }


no_floyd = ~df["incident_date"].between(*FLOYD_EPISODE)
no_2020 = df["year"] < 2020

steps = [
    run("1_legacy_replica", df, "mh_broad_share", "aware_z", SPARSE_LAGS, False, "cd"),
    run("2_+date_cluster", df, "mh_broad_share", "aware_z", SPARSE_LAGS, False, "date"),
    run("3_+all_lags_leads", df, "mh_broad_share", "aware_z", LAGS, True, "date"),
    run("4_+log_transform", df, "mh_broad_share", "aware_log", LAGS, True, "date"),
    run("5_+narrow_outcome(primary)", df, "mh_narrow_share", "aware_log", LAGS, True, "date"),
    run("6_primary_no_floyd_episode", df[no_floyd], "mh_narrow_share", "aware_log", LAGS, True, "date"),
    run("7_primary_2017_2019", df[no_2020], "mh_narrow_share", "aware_log", LAGS, True, "date"),
    run("8_legacy_no_floyd_episode", df[no_floyd], "mh_broad_share", "aware_z", SPARSE_LAGS, False, "cd"),
    run("9_legacy_2017_2019", df[no_2020], "mh_broad_share", "aware_z", SPARSE_LAGS, False, "cd"),
]

out = pd.DataFrame(steps)
out.to_csv(OUTPUTS_TABLES / "bridge_legacy_to_primary.csv", index=False)
pd.set_option("display.width", 200)
print(out.to_string(index=False))
