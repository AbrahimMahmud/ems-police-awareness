"""Outcome decomposition and placebos (REWORK_PLAN I10, I11, I13).

For each outcome (MH components, placebo call types, totals) estimate the effect
of binned awareness windows, both jointly (all windows in one model) and alone
(one window at a time; windows correlate ~0.8 so both views are reported).

Outputs (outputs/tables/):
    decomposition_windows.csv   outcome x window x {joint, alone} coef/se/p (date-clustered)
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
    PRIMARY_AWARENESS,
    ROLLING_WINDOWS,
)

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
lags = pd.read_parquet(DATA_PROCESSED / "awareness_lags.parquet")
df = panel.merge(lags, left_on="incident_date", right_on="date", how="left")
df = df[df["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
df = df[df["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]
df["month_year"] = df["year"] * 100 + df["month"]
df["date_id"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)
df["log_total"] = np.log(df["total_calls"])
for c in ["mh_narrow", "mh_broad", "edp", "altmen", "suicide_jump",
          "od_poison_drug", "cardiac", "injury", "asthma"]:
    df[f"log1p_{c}"] = np.log1p(df[c])

WINDOWS = [f"{PRIMARY_AWARENESS}_w{lo}{hi}" for lo, hi in ROLLING_WINDOWS]
FE = "communitydistrict + dow + month_year"
VCOV = {"CRV1": "date_id"}

OUTCOMES = {
    # (column, family) -- family drives figure grouping
    "mh_narrow_share": "mental health",
    "mh_broad_share": "mental health",
    "edp_share": "mental health",
    "altmen_share": "mental health",
    "suicide_jump_share": "mental health",
    "od_poison_drug_share": "mental health",
    "cardiac_share": "placebo",
    "injury_share": "protest channel",
    "asthma_share": "placebo",
    "log_total": "volume",
    "log1p_mh_narrow": "volume",
    "log1p_edp": "volume",
    "log1p_injury": "volume",
}

rows = []
for y, family in OUTCOMES.items():
    d_joint = df.dropna(subset=[y] + WINDOWS)
    m_joint = pf.feols(f"{y} ~ {' + '.join(WINDOWS)} | {FE}", d_joint, vcov=VCOV)
    for w in WINDOWS:
        d_alone = df.dropna(subset=[y, w])
        m_alone = pf.feols(f"{y} ~ {w} | {FE}", d_alone, vcov=VCOV)
        rows.append({
            "outcome": y, "family": family, "window": w.replace(f"{PRIMARY_AWARENESS}_", ""),
            "coef_joint": m_joint.coef()[w], "se_joint": m_joint.se()[w], "p_joint": m_joint.pvalue()[w],
            "coef_alone": m_alone.coef()[w], "se_alone": m_alone.se()[w], "p_alone": m_alone.pvalue()[w],
            "n_obs": len(d_alone),
        })

out = pd.DataFrame(rows)
out.to_csv(OUTPUTS_TABLES / "decomposition_windows.csv", index=False)
print(out[out["window"].isin(["w02", "w35"])]
      .pivot_table(index=["family", "outcome"], columns="window", values=["coef_alone", "p_alone"])
      .round(5).to_string())
