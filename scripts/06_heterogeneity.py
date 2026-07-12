"""Heterogeneity of the awareness effect by district demographics (REWORK_PLAN §5.1).

Tests whether the days-3-5 suppression of police-adjacent (EDP) call shares
concentrates in heavily Black/Hispanic districts -- the decisive test of the
help-seeking-avoidance interpretation. Uses BOTH demographic vintages:
ACS 2015-2019 (primary, period-matched) and Census 2010 (legacy comparison).

Models (outcome = edp_share and mh_narrow_share; W = aware_log_w35, each
window alone; date-clustered SEs):
  1. Interaction: y ~ W + W x (pct_black - 50)/10   [Justin's 50% baseline;
     coefficient = change in effect per +10pp Black share]
  2. Quartile stratification (Q1..Q4 by pct_black, pct_black+hispanic)
  3. Binary split: (pct_black + pct_hispanic) above/below median
  4. Race-matched exposure: W_black x pct_black (Black-victim awareness)

Outputs: outputs/tables/heterogeneity_results.csv, heterogeneity_quartiles.csv
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

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
lags = pd.read_parquet(DATA_PROCESSED / "awareness_lags.parquet")

# race-matched awareness window (mean of black-victim lags 3-5)
lags["aware_black_w35"] = lags[[f"aware_black_log_lag{k}" for k in (3, 4, 5)]].mean(axis=1)

df = panel.merge(lags[["date", "aware_log_w35", "aware_log_w02", "aware_black_w35"]],
                 left_on="incident_date", right_on="date", how="left")
df = df[df["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
df = df[df["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]
df["month_year"] = df["year"] * 100 + df["month"]
df["date_id"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)

# --- demographics, both vintages ---
acs = pd.read_csv(DATA_REFERENCE / "acs_2019_cd_demographics.csv")
d2010 = pd.read_parquet(DATA_PROCESSED / "cd_demographics_clean.parquet")
keep10 = ["communitydistrict", "pct_black", "pct_hispanic", "pct_white", "pct_asian"]
demo = acs.merge(d2010[keep10], on="communitydistrict", how="left", suffixes=("", "_2010"))

# vintage drift diagnostics
demo["q_black_acs"] = pd.qcut(demo["pct_black_acs"], 4, labels=False)
demo["q_black_2010"] = pd.qcut(demo["pct_black"], 4, labels=False)
n_switch = int((demo["q_black_acs"] != demo["q_black_2010"]).sum())
r_vint = demo["pct_black_acs"].corr(demo["pct_black"])
print(f"Vintage drift: corr(pct_black ACS, 2010) = {r_vint:.3f}; "
      f"{n_switch}/59 CDs change %Black quartile")

df = df.merge(demo, on="communitydistrict", how="left")
df["bh_acs"] = df["pct_black_acs"] + df["pct_hispanic_acs"]
df["bh_2010"] = df["pct_black"] + df["pct_hispanic"]

FE = "communitydistrict + dow + month_year"
VC = {"CRV1": "date_id"}
rows = []


def interaction(outcome, wvar, share_col, vintage, label):
    d = df.dropna(subset=[outcome, wvar, share_col]).copy()
    d["ctr"] = (d[share_col] - 50) / 10  # Justin's 50% baseline, per 10pp
    d["inter"] = d[wvar] * d["ctr"]
    m = pf.feols(f"{outcome} ~ {wvar} + inter | {FE}", d, vcov=VC)
    rows.append({"model": f"interaction_{label}", "vintage": vintage, "outcome": outcome,
                 "term": "effect_at_50pct", "coef": m.coef()[wvar],
                 "se": m.se()[wvar], "p": m.pvalue()[wvar]})
    rows.append({"model": f"interaction_{label}", "vintage": vintage, "outcome": outcome,
                 "term": "change_per_10pp", "coef": m.coef()["inter"],
                 "se": m.se()["inter"], "p": m.pvalue()["inter"]})


qrows = []


def quartiles(outcome, wvar, share_col, vintage, label):
    d = df.dropna(subset=[outcome, wvar, share_col]).copy()
    d["q"] = pd.qcut(d[share_col].rank(method="first"), 4, labels=False)
    # rank-based qcut over CD-days ~ CD-level quartiles since shares are CD-constant
    for q in range(4):
        s = d[d["q"] == q]
        m = pf.feols(f"{outcome} ~ {wvar} | {FE}", s, vcov=VC)
        qrows.append({"split": label, "vintage": vintage, "outcome": outcome,
                      "quartile": f"Q{q+1}", "n_cds": s["communitydistrict"].nunique(),
                      "coef": m.coef()[wvar], "se": m.se()[wvar], "p": m.pvalue()[wvar]})


for outcome in ["edp_share", "mh_narrow_share"]:
    for share_col, vintage in [("pct_black_acs", "acs1519"), ("pct_black", "census2010")]:
        interaction(outcome, "aware_log_w35", share_col, vintage, "black")
        quartiles(outcome, "aware_log_w35", share_col, vintage, "pct_black")
    interaction(outcome, "aware_log_w35", "bh_acs", "acs1519", "black_hispanic")
    quartiles(outcome, "aware_log_w35", "bh_acs", "acs1519", "black_hispanic")
    # binary split (meeting note)
    d = df.dropna(subset=[outcome, "aware_log_w35", "bh_acs"]).copy()
    med = demo["pct_black_acs"].add(demo["pct_hispanic_acs"]).median()
    for grp, lab in [(d[d["bh_acs"] > med], "above_median_BH"),
                     (d[d["bh_acs"] <= med], "below_median_BH")]:
        m = pf.feols(f"{outcome} ~ aware_log_w35 | {FE}", grp, vcov=VC)
        rows.append({"model": "binary_split", "vintage": "acs1519", "outcome": outcome,
                     "term": lab, "coef": m.coef()["aware_log_w35"],
                     "se": m.se()["aware_log_w35"], "p": m.pvalue()["aware_log_w35"]})
    # race-matched exposure
    interaction(outcome, "aware_black_w35", "pct_black_acs", "acs1519", "blackvictim_x_black")

res = pd.DataFrame(rows)
res.to_csv(OUTPUTS_TABLES / "heterogeneity_results.csv", index=False)
qt = pd.DataFrame(qrows)
qt.to_csv(OUTPUTS_TABLES / "heterogeneity_quartiles.csv", index=False)

pd.set_option("display.width", 200)
print("\n=== Interactions and splits (edp_share) ===")
print(res[res["outcome"] == "edp_share"].round(6).to_string(index=False))
print("\n=== Quartiles: edp_share x pct_black (ACS) ===")
print(qt[(qt["outcome"] == "edp_share") & (qt["vintage"] == "acs1519")
         & (qt["split"] == "pct_black")].round(6).to_string(index=False))
