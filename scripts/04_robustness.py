"""Count models, permutation inference, and the deferral test (REWORK_PLAN §4).

1. PPML: edp (count) ~ aware_log_w35 + log(other calls) | CD + dow + month-year.
   Resolves the shares-vs-counts question (share effects can be compositional).
2. Permutation inference: circularly shift the awareness date-series by random
   offsets >= 60 days (preserving its autocorrelation), re-estimate the w35
   share effect N_PERM times; permutation p = share of |shifted| >= |actual|.
   Complements clustered SEs given only 12 awareness episodes.
3. Deferral test: if early suppression is deferred help-seeking, the cumulative
   window (days 0-8, spanning dip and rebound) should be ~0.

Output: outputs/tables/robustness_counts_permutation.csv
"""

import numpy as np
import pandas as pd
import pyfixest as pf

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
)

N_PERM = 200
rng = np.random.default_rng(20260712)

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
aware = pd.read_parquet(DATA_PROCESSED / "awareness_daily.parquet")[["date", "aware_log"]]

df = panel[panel["incident_date"].between(ANALYSIS_START, ANALYSIS_END)].copy()
df = df[df["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]
df["month_year"] = df["year"] * 100 + df["month"]
df["date_id"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)
df["log_other"] = np.log(np.maximum(df["total_calls"] - df["edp"], 1))

FE = "communitydistrict + dow + month_year"
VC = {"CRV1": "date_id"}
results = []


def w35_from(series_df, col):
    """Build the days-3-5 window from a date-level awareness series."""
    s = series_df.sort_values("date").reset_index(drop=True)
    w = s[col].shift(3).add(s[col].shift(4)).add(s[col].shift(5)).div(3)
    return pd.DataFrame({"date": s["date"], "w35": w})


base_w = w35_from(aware, "aware_log")
d = df.merge(base_w, left_on="incident_date", right_on="date", how="left").dropna(subset=["w35"])

# 1. PPML count model
m_ppml = pf.fepois(f"edp ~ w35 + log_other | {FE}", d, vcov=VC)
results.append({"test": "ppml_edp_count", "coef": m_ppml.coef()["w35"],
                "se": m_ppml.se()["w35"], "p": m_ppml.pvalue()["w35"],
                "note": "semi-elasticity of EDP count per log-point awareness"})
m_ppml_mh = pf.fepois(f"mh_narrow ~ w35 + log_other | {FE}",
                      d.assign(log_other=np.log(np.maximum(d["total_calls"] - d["mh_narrow"], 1))),
                      vcov=VC)
results.append({"test": "ppml_mh_narrow_count", "coef": m_ppml_mh.coef()["w35"],
                "se": m_ppml_mh.se()["w35"], "p": m_ppml_mh.pvalue()["w35"], "note": ""})

# 2. Permutation inference on the share effect
m_actual = pf.feols(f"edp_share ~ w35 | {FE}", d, vcov=VC)
b_actual = m_actual.coef()["w35"]
n_days = len(aware)
perm_bs = []
for i in range(N_PERM):
    shift = int(rng.integers(60, n_days - 60))
    sh = aware.copy()
    sh["aware_perm"] = np.roll(sh["aware_log"].to_numpy(), shift)
    pw = w35_from(sh, "aware_perm")
    dp = df.merge(pw, left_on="incident_date", right_on="date", how="left").dropna(subset=["w35"])
    mp = pf.feols(f"edp_share ~ w35 | {FE}", dp, vcov="iid")  # only coef needed
    perm_bs.append(mp.coef()["w35"])
perm_bs = np.array(perm_bs)
p_perm = float((np.abs(perm_bs) >= abs(b_actual)).mean())
results.append({"test": "permutation_edp_share_w35", "coef": b_actual,
                "se": float(perm_bs.std()), "p": p_perm,
                "note": f"{N_PERM} circular shifts >=60 days; p = share |b_perm| >= |b_actual|"})

# 3. Deferral test: cumulative days 0-8
s = aware.sort_values("date").reset_index(drop=True)
cum = s["aware_log"].rolling(9).mean().shift(0)
cum_df = pd.DataFrame({"date": s["date"], "w08": s["aware_log"].shift(0).rolling(9).mean()})
# rolling(9) at t averages t-8..t which equals lags 0..8
d2 = df.merge(cum_df, left_on="incident_date", right_on="date", how="left").dropna(subset=["w08"])
for y in ["edp_share", "mh_narrow_share"]:
    m = pf.feols(f"{y} ~ w08 | {FE}", d2, vcov=VC)
    results.append({"test": f"deferral_cum08_{y}", "coef": m.coef()["w08"],
                    "se": m.se()["w08"], "p": m.pvalue()["w08"],
                    "note": "days 0-8 cumulative; ~0 supports deferral, <0 supports net loss"})

res = pd.DataFrame(results)
res.to_csv(OUTPUTS_TABLES / "robustness_counts_permutation.csv", index=False)
print(res.round(6).to_string(index=False))
