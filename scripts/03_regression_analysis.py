"""Run distributed lag regression models with community district fixed effects."""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(PANEL_PATH)

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

def run_dl_cdfe(df, dv):
    """Run distributed lag model with community district fixed effects."""
    d = df[(df["total_calls"] >= 5) & df[dv].notna()].copy()
    d = d.loc[d[lag_cols].notna().any(axis=1)]
    d["cd_int"] = pd.to_numeric(d["communitydistrict"], errors="coerce")
    d = d.dropna(subset=["cd_int"])
    d["cd_int"] = d["cd_int"].astype("int64")
    d["cd_str"] = d["cd_int"].astype(str)
    
    if dv in ("mh_calls", "total_calls"):
        d[dv] = pd.to_numeric(d[dv], errors="coerce").astype(float) / 100.0
    
    formula = f"{dv} ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y, X = patsy.dmatrices(formula, data=d, return_type="dataframe")
    groups = d.loc[y.index, "cd_int"].to_numpy(dtype="int64")
    m = sm.OLS(y, X, missing="drop").fit(cov_type="cluster", cov_kwds={"groups": groups})
    return m

print("=" * 80)
print("Model: mh_share with CD fixed effects")
print("=" * 80)

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()
df_fe["cd_int"] = df_fe["communitydistrict"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

formula_fe = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")
groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")
mod_fe = sm.OLS(y_fe, X_fe, missing="drop").fit(cov_type="cluster", cov_kwds={"groups": groups_fe})

print(f"Observations: {int(mod_fe.nobs):,}")
print(f"R-squared: {mod_fe.rsquared:.4f}")

params_fe_out = OUTPUTS_TABLES / "dl_model_params_with_cdfe.csv"
mod_fe.params.rename("coef").to_frame().join(mod_fe.bse.rename("se")).to_csv(params_fe_out)
print(f"Saved to: {params_fe_out}")

print("\n" + "=" * 80)
print("Placebo test: total_calls")
print("=" * 80)
mod_tot = run_dl_cdfe(df_panel, "total_calls")
print(f"Observations: {int(mod_tot.nobs):,}")
print(f"R-squared: {mod_tot.rsquared:.4f}")

def cumulative_effect(model, lags=(0, 1, 2, 3, 4, 5, 6, 7)):
    """Calculate cumulative effect over specified lags."""
    names = [f"awarez_lag{k}" for k in lags if f"awarez_lag{k}" in model.params.index]
    S = model.params.loc[names].sum()
    VC = model.cov_params().loc[names, names].to_numpy()
    se = float(np.sqrt(VC.sum()))
    return S, se

cum_b, cum_se = cumulative_effect(mod_fe, lags=(0, 1, 2, 3, 4, 5, 6, 7))
print(f"\nCumulative effect (0-7 days): {cum_b:.6f} ± {1.96*cum_se:.6f}")

city_mean_total = df_panel["total_calls"].mean()
pt = cum_b * city_mean_total
ci = 1.96 * cum_se * city_mean_total
print(f"Citywide: +{pt:.2f} MH calls per 1σ awareness (±{ci:.2f})")

print("\n" + "=" * 80)
print("Regression analysis complete")
print("=" * 80)
