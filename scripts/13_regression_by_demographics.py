"""
Step 13: Separate regression analyses with demographic variables.

This script runs:
1. Regression with pct_white as independent variable (controlling for awareness)
2. Regression with mh_share as outcome, pct_white as control variable
"""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("REGRESSION ANALYSES BY DEMOGRAPHICS")
print("=" * 80)

# Load panel with demographics
panel_path = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
if not panel_path.exists():
    # Try without demographics
    panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
    if not panel_path.exists():
        raise FileNotFoundError(f"Panel data not found")

df = pd.read_parquet(panel_path)
print(f"\nLoaded panel: {len(df):,} rows")

# Check for demographics
has_pct_white = "pct_white" in df.columns
if not has_pct_white:
    print("⚠️  pct_white not found. Demographics may not be merged.")
    print("   Run: python scripts/11_merge_demographics.py")

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

# Prepare analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
df_analysis = df_analysis.loc[df_analysis[lag_cols].notna().any(axis=1)].copy()
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

print(f"Analysis sample: {len(df_analysis):,} rows")
print(f"Community districts: {df_analysis['cd_int'].nunique()}")

def run_model(formula, data, model_name):
    """Run OLS model with clustered standard errors."""
    y, X = patsy.dmatrices(formula, data=data, return_type="dataframe")
    groups = data.loc[y.index, "cd_int"].to_numpy(dtype="int64")
    
    model = sm.OLS(y, X, missing="drop").fit(
        cov_type="cluster", 
        cov_kwds={"groups": groups}
    )
    
    return model

# Analysis 1: pct_white as independent variable (controlling for awareness)
if has_pct_white and df_analysis["pct_white"].notna().sum() > 100:
    print("\n" + "=" * 80)
    print("ANALYSIS 1: pct_white as independent variable")
    print("=" * 80)
    print("Outcome: mh_share")
    print("Independent: pct_white (controlling for awareness lags)")
    
    formula1 = "mh_share ~ pct_white + " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    mod1 = run_model(formula1, df_analysis, "Model 1")
    
    print(f"\nObservations: {int(mod1.nobs):,}")
    print(f"R-squared: {mod1.rsquared:.4f}")
    
    if "pct_white" in mod1.params.index:
        coef = mod1.params["pct_white"]
        se = mod1.bse["pct_white"]
        print(f"\npct_white coefficient: {coef:.6f} (SE: {se:.6f})")
        print(f"95% CI: [{coef - 1.96*se:.6f}, {coef + 1.96*se:.6f}]")
        print(f"t-statistic: {coef/se:.3f}")
        from scipy import stats
        print(f"p-value: {2 * (1 - stats.norm.cdf(abs(coef/se))):.4f}")
    
    # Save results
    params_out = OUTPUTS_TABLES / "regression_by_pct_white_independent.csv"
    mod1.params.rename("coef").to_frame().join(mod1.bse.rename("se")).to_csv(params_out)
    print(f"\n✓ Saved to: {params_out}")
else:
    print("\n⚠️  Cannot run Analysis 1: pct_white not available or insufficient data")

# Analysis 2: pct_white as control variable (with mh_share as outcome)
if has_pct_white and df_analysis["pct_white"].notna().sum() > 100:
    print("\n" + "=" * 80)
    print("ANALYSIS 2: pct_white as control variable")
    print("=" * 80)
    print("Outcome: mh_share")
    print("Independent: awareness lags")
    print("Control: pct_white")
    
    formula2 = "mh_share ~ " + " + ".join(lag_cols) + " + pct_white + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    mod2 = run_model(formula2, df_analysis, "Model 2")
    
    print(f"\nObservations: {int(mod2.nobs):,}")
    print(f"R-squared: {mod2.rsquared:.4f}")
    
    # Compare key lag coefficients with and without pct_white
    if "awarez_lag7" in mod2.params.index:
        coef_lag7 = mod2.params["awarez_lag7"]
        se_lag7 = mod2.bse["awarez_lag7"]
        print(f"\nawarez_lag7 coefficient: {coef_lag7:.6f} (SE: {se_lag7:.6f})")
        print(f"95% CI: [{coef_lag7 - 1.96*se_lag7:.6f}, {coef_lag7 + 1.96*se_lag7:.6f}]")
    
    if "pct_white" in mod2.params.index:
        coef = mod2.params["pct_white"]
        se = mod2.bse["pct_white"]
        print(f"\npct_white coefficient (control): {coef:.6f} (SE: {se:.6f})")
    
    # Save results
    params_out = OUTPUTS_TABLES / "regression_by_pct_white_control.csv"
    mod2.params.rename("coef").to_frame().join(mod2.bse.rename("se")).to_csv(params_out)
    print(f"\n✓ Saved to: {params_out}")

# Analysis 3: Regression of mh_share on pct_white only (no awareness controls)
if has_pct_white and df_analysis["pct_white"].notna().sum() > 100:
    print("\n" + "=" * 80)
    print("ANALYSIS 3: mh_share ~ pct_white (simple relationship)")
    print("=" * 80)
    
    formula3 = "mh_share ~ pct_white + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    mod3 = run_model(formula3, df_analysis, "Model 3")
    
    print(f"\nObservations: {int(mod3.nobs):,}")
    print(f"R-squared: {mod3.rsquared:.4f}")
    
    if "pct_white" in mod3.params.index:
        coef = mod3.params["pct_white"]
        se = mod3.bse["pct_white"]
        print(f"\npct_white coefficient: {coef:.6f} (SE: {se:.6f})")
    
    # Save results
    params_out = OUTPUTS_TABLES / "regression_mhshare_pctwhite_simple.csv"
    mod3.params.rename("coef").to_frame().join(mod3.bse.rename("se")).to_csv(params_out)
    print(f"\n✓ Saved to: {params_out}")

print("\n" + "=" * 80)
print("REGRESSION BY DEMOGRAPHICS COMPLETE")
print("=" * 80)

