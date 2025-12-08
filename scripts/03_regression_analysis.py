"""
Step 3: Run distributed lag regression models.

This script:
- Runs distributed lag models with and without community district fixed effects
- Estimates effects on mh_share, mh_calls, and total_calls (placebo)
- Calculates cumulative effects
- Saves regression results to outputs/tables/
"""

import os
import re
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"

# Create output directory if it doesn't exist
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DATA_PROCESSED / "panel_cd_day_awareness.parquet"

if not PANEL_PATH.exists():
    raise FileNotFoundError(
        f"Panel file not found: {PANEL_PATH}. Run 02_merge_awareness.py first."
    )

print(f"Loading panel from: {PANEL_PATH}")
df_panel = pd.read_parquet(PANEL_PATH)
print(f"Panel shape: {df_panel.shape}")

# Lag set for analysis
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

# Helper function for distributed lag model with CD fixed effects
def run_dl_cdfe(df, dv):
    """Run distributed lag model with community district fixed effects."""
    d = df.copy()

    # Filter to usable rows
    d = d[(d["total_calls"] >= 5) & d[dv].notna()]
    d = d.loc[d[lag_cols].notna().any(axis=1)]

    # Ensure communitydistrict is clean int for clustering
    d["cd_int"] = pd.to_numeric(d["communitydistrict"], errors="coerce")
    d = d.dropna(subset=["cd_int"])  # drop rows with missing CD
    d["cd_int"] = d["cd_int"].astype("int64")
    d["cd_str"] = d["cd_int"].astype(str)  # string for C() fixed effects

    # Stabilize scale for counts (cosmetic; doesn't affect inference)
    if dv in ("mh_calls", "total_calls"):
        d[dv] = pd.to_numeric(d[dv], errors="coerce").astype(float) / 100.0

    formula = (
        f"{dv} ~ "
        + " + ".join(lag_cols)
        + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    )
    y, X = patsy.dmatrices(formula, data=d, return_type="dataframe")

    groups = d.loc[y.index, "cd_int"].to_numpy(dtype="int64")
    m = sm.OLS(y, X, missing="drop").fit(
        cov_type="cluster", cov_kwds={"groups": groups}
    )

    # Safety check
    assert len(groups) == int(m.nobs), "Cluster groups length mismatch."
    return m

# ---- Model 1: mh_share without CD fixed effects ----
print("\n" + "=" * 80)
print("Model 1: mh_share without CD fixed effects")
print("=" * 80)

df_model = df_panel[df_panel["total_calls"] >= 5].copy()
df_model = df_model.dropna(subset=["mh_share"])
df_model = df_model.loc[df_model[lag_cols].notna().any(axis=1)].copy()

formula = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday"
)
y, X = patsy.dmatrices(formula, data=df_model, return_type="dataframe")

groups = df_model.loc[y.index, "communitydistrict"].astype("int64")
model = sm.OLS(y, X, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups}
)

assert len(groups) == int(model.nobs), "Cluster groups length mismatch."

print(model.summary())

# Save parameters
params_out = OUTPUTS_TABLES / "dl_model_params.csv"
(
    model.params.rename("coef")
    .to_frame()
    .join(model.bse.rename("se"))
    .to_csv(params_out)
)
print(f"\nSaved parameters to: {params_out}")

# ---- Model 2: mh_share with CD fixed effects ----
print("\n" + "=" * 80)
print("Model 2: mh_share with CD fixed effects")
print("=" * 80)

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()

df_fe["cd_int"] = df_fe["communitydistrict"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

formula_fe = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
)

y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")

groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")
mod_fe = sm.OLS(y_fe, X_fe, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups_fe}
)

assert len(groups_fe) == int(mod_fe.nobs), "Cluster groups length mismatch."

print(mod_fe.summary())

# Save parameters
params_fe_out = OUTPUTS_TABLES / "dl_model_params_with_cdfe.csv"
(
    mod_fe.params.rename("coef")
    .to_frame()
    .join(mod_fe.bse.rename("se"))
    .to_csv(params_fe_out)
)
print(f"\nSaved parameters to: {params_fe_out}")

# Note: mod_fe is available in this script's scope but not shared across scripts
# The visualization script will re-run the model or load from saved files

# ---- Model 3: mh_calls (levels) with CD fixed effects ----
print("\n" + "=" * 80)
print("Model 3: mh_calls (levels) with CD fixed effects")
print("=" * 80)

mod_mh = run_dl_cdfe(df_panel, "mh_calls")
print(mod_mh.summary())

# ---- Model 4: total_calls (placebo) with CD fixed effects ----
print("\n" + "=" * 80)
print("Model 4: total_calls (placebo) with CD fixed effects")
print("=" * 80)

mod_tot = run_dl_cdfe(df_panel, "total_calls")
print(mod_tot.summary())

# Save level model parameters
params_levels_out = OUTPUTS_TABLES / "dl_params_levels.csv"
pd.concat(
    {
        "mh_calls": mod_mh.params.rename("coef")
        .to_frame()
        .join(mod_mh.bse.rename("se")),
        "total": mod_tot.params.rename("coef")
        .to_frame()
        .join(mod_tot.bse.rename("se")),
    },
    axis=0,
).to_csv(params_levels_out)
print(f"\nSaved level model parameters to: {params_levels_out}")

# ---- Cumulative effects ----
print("\n" + "=" * 80)
print("Cumulative Effects")
print("=" * 80)


def cumulative_effect(model, lags=(0, 1, 2, 3, 4, 5, 6, 7)):
    """Calculate cumulative effect over specified lags."""
    names = [
        f"awarez_lag{k}"
        for k in lags
        if f"awarez_lag{k}" in model.params.index
    ]
    S = model.params.loc[names].sum()
    VC = model.cov_params().loc[names, names].to_numpy()
    se = float(np.sqrt(VC.sum()))  # variance of sum = 1' V 1
    return S, se


cum_b, cum_se = cumulative_effect(mod_fe, lags=(0, 1, 2, 3, 4, 5, 6, 7))
print(f"Cumulative β (0–7 days) on mh_share: {cum_b:.6f} ± {1.96*cum_se:.6f}")

# Convert cumulative effect on mh_share to calls per 1σ awareness
city_mean_total = df_panel["total_calls"].mean()


def calls_from_share(beta, se, total):
    """Convert share effect to call count effect."""
    point = beta * total
    se_calls = se * total
    return point, 1.96 * se_calls


pt, ci = calls_from_share(cum_b, cum_se, city_mean_total)
print(f"\nCitywide: +{pt:.2f} MH calls over 0–7 days per 1σ awareness (±{ci:.2f})")

# By CD
cd_means = (
    df_panel.groupby("communitydistrict", as_index=False)
    .agg(total_mean=("total_calls", "mean"))
)
cd_means["delta_calls_pt"] = cum_b * cd_means["total_mean"]
cd_means["delta_calls_ci"] = 1.96 * cum_se * cd_means["total_mean"]
cd_means = cd_means.sort_values("delta_calls_pt", ascending=False)

delta_calls_out = OUTPUTS_TABLES / "delta_calls_by_cd.csv"
cd_means.to_csv(delta_calls_out, index=False)
print(f"Saved delta calls by CD to: {delta_calls_out}")

# Note: Cumulative effects are printed above and saved in delta_calls_by_cd.csv
# The visualization script can access these from the saved files if needed

print("\n" + "=" * 80)
print("Regression analysis complete!")
print("=" * 80)

