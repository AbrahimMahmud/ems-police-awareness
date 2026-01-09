"""
Step 3b: Progressive regression models showing incremental addition of controls.

This script runs multiple regression models, adding controls incrementally:
1. Base model: awareness lags only
2. + Day of week controls
3. + Month×Year interactions
4. + Holiday indicator
5. + Community district fixed effects
6. + Demographic controls (one at a time, then together)
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
print("PROGRESSIVE REGRESSION MODELS")
print("=" * 80)

# Load panel
PANEL_PATH = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(PANEL_PATH)

# Check for demographics
DEMO_PATH = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
has_demographics = DEMO_PATH.exists()
if has_demographics:
    df_demo = pd.read_parquet(DEMO_PATH)
    # Merge demographics (take first row per CD to get time-invariant values)
    demo_cols = [c for c in df_demo.columns 
                 if c not in df_panel.columns or c == "communitydistrict"]
    if demo_cols:
        df_demo_unique = df_demo[["communitydistrict"] + [c for c in demo_cols if c != "communitydistrict"]].drop_duplicates(subset=["communitydistrict"])
        df_panel = df_panel.merge(df_demo_unique, on="communitydistrict", how="left")
        print(f"Merged demographics: {len([c for c in demo_cols if c != 'communitydistrict'])} variables")

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

# Prepare analysis sample
df = df_panel[(df_panel["total_calls"] >= 5) & df_panel["mh_share"].notna()].copy()
df = df.loc[df[lag_cols].notna().any(axis=1)].copy()
df["cd_int"] = pd.to_numeric(df["communitydistrict"], errors="coerce")
df = df.dropna(subset=["cd_int"])
df["cd_int"] = df["cd_int"].astype("int64")
df["cd_str"] = df["cd_int"].astype(str)

print(f"\nAnalysis sample: {len(df):,} rows")
print(f"Community districts: {df['cd_int'].nunique()}")

# Define demographic variables to add progressively
demo_vars_to_add = []
if has_demographics:
    potential_demos = ["pct_white", "pct_black", "pct_hispanic", "pct_asian", 
                      "median_income", "pct_college", "pct_over_65", "pct_health_insurance"]
    demo_vars_to_add = [v for v in potential_demos if v in df.columns]

def run_model(formula, data, model_name):
    """Run OLS model with clustered standard errors."""
    y, X = patsy.dmatrices(formula, data=data, return_type="dataframe")
    groups = data.loc[y.index, "cd_int"].to_numpy(dtype="int64")
    
    model = sm.OLS(y, X, missing="drop").fit(
        cov_type="cluster", 
        cov_kwds={"groups": groups}
    )
    
    return model

# Store results
all_results = []

# Model 1: Awareness lags only
print("\n" + "=" * 80)
print("MODEL 1: Awareness lags only")
print("=" * 80)
formula1 = "mh_share ~ " + " + ".join(lag_cols)
mod1 = run_model(formula1, df, "Model 1")
print(f"Observations: {int(mod1.nobs):,}")
print(f"R-squared: {mod1.rsquared:.4f}")
all_results.append({
    "model": "Model 1: Awareness lags only",
    "n_obs": int(mod1.nobs),
    "r_squared": mod1.rsquared,
    "n_params": len(mod1.params),
})

# Model 2: + Day of week
print("\n" + "=" * 80)
print("MODEL 2: + Day of week controls")
print("=" * 80)
formula2 = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow)"
mod2 = run_model(formula2, df, "Model 2")
print(f"Observations: {int(mod2.nobs):,}")
print(f"R-squared: {mod2.rsquared:.4f}")
all_results.append({
    "model": "Model 2: + Day of week",
    "n_obs": int(mod2.nobs),
    "r_squared": mod2.rsquared,
    "n_params": len(mod2.params),
})

# Model 3: + Month×Year interactions
print("\n" + "=" * 80)
print("MODEL 3: + Month×Year interactions")
print("=" * 80)
formula3 = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year)"
mod3 = run_model(formula3, df, "Model 3")
print(f"Observations: {int(mod3.nobs):,}")
print(f"R-squared: {mod3.rsquared:.4f}")
all_results.append({
    "model": "Model 3: + Month×Year",
    "n_obs": int(mod3.nobs),
    "r_squared": mod3.rsquared,
    "n_params": len(mod3.params),
})

# Model 4: + Holiday indicator
print("\n" + "=" * 80)
print("MODEL 4: + Holiday indicator")
print("=" * 80)
formula4 = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday"
mod4 = run_model(formula4, df, "Model 4")
print(f"Observations: {int(mod4.nobs):,}")
print(f"R-squared: {mod4.rsquared:.4f}")
all_results.append({
    "model": "Model 4: + Holiday",
    "n_obs": int(mod4.nobs),
    "r_squared": mod4.rsquared,
    "n_params": len(mod4.params),
})

# Model 5: + Community district fixed effects
print("\n" + "=" * 80)
print("MODEL 5: + Community district fixed effects")
print("=" * 80)
formula5 = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
mod5 = run_model(formula5, df, "Model 5")
print(f"Observations: {int(mod5.nobs):,}")
print(f"R-squared: {mod5.rsquared:.4f}")
all_results.append({
    "model": "Model 5: + CD fixed effects",
    "n_obs": int(mod5.nobs),
    "r_squared": mod5.rsquared,
    "n_params": len(mod5.params),
})

# Models 6+: Add demographics one at a time
if demo_vars_to_add:
    print("\n" + "=" * 80)
    print("MODELS 6+: Adding demographic controls")
    print("=" * 80)
    
    for i, demo_var in enumerate(demo_vars_to_add, start=6):
        if demo_var not in df.columns or df[demo_var].notna().sum() < 100:
            print(f"\n⚠️  Skipping {demo_var} (not available or insufficient data)")
            continue
        
        print(f"\nMODEL {i}: + {demo_var}")
        formula_demo = formula5 + f" + {demo_var}"
        mod_demo = run_model(formula_demo, df, f"Model {i}")
        print(f"Observations: {int(mod_demo.nobs):,}")
        print(f"R-squared: {mod_demo.rsquared:.4f}")
        all_results.append({
            "model": f"Model {i}: + {demo_var}",
            "n_obs": int(mod_demo.nobs),
            "r_squared": mod_demo.rsquared,
            "n_params": len(mod_demo.params),
        })
        
        # Save individual model
        params_out = OUTPUTS_TABLES / f"regression_progressive_model_{i}_{demo_var}.csv"
        mod_demo.params.rename("coef").to_frame().join(mod_demo.bse.rename("se")).to_csv(params_out)
    
    # Final model: All demographics together
    print("\n" + "=" * 80)
    print(f"MODEL {len(demo_vars_to_add) + 6}: All demographics together")
    print("=" * 80)
    demo_vars_available = [v for v in demo_vars_to_add if v in df.columns and df[v].notna().sum() >= 100]
    if demo_vars_available:
        formula_all_demo = formula5 + " + " + " + ".join(demo_vars_available)
        mod_all_demo = run_model(formula_all_demo, df, f"Model {len(demo_vars_to_add) + 6}")
        print(f"Observations: {int(mod_all_demo.nobs):,}")
        print(f"R-squared: {mod_all_demo.rsquared:.4f}")
        all_results.append({
            "model": f"Model {len(demo_vars_to_add) + 6}: All demographics",
            "n_obs": int(mod_all_demo.nobs),
            "r_squared": mod_all_demo.rsquared,
            "n_params": len(mod_all_demo.params),
        })
        
        params_out = OUTPUTS_TABLES / f"regression_progressive_model_all_demographics.csv"
        mod_all_demo.params.rename("coef").to_frame().join(mod_all_demo.bse.rename("se")).to_csv(params_out)

# Save model comparison
df_results = pd.DataFrame(all_results)
comparison_out = OUTPUTS_TABLES / "regression_progressive_comparison.csv"
df_results.to_csv(comparison_out, index=False)
print(f"\n✓ Saved model comparison to: {comparison_out}")

# Extract key coefficients (lag 7) for comparison
lag7_coefs = []
for i, result in enumerate(all_results, start=1):
    model_file = OUTPUTS_TABLES / f"regression_progressive_model_{i}.csv"
    if i <= 5:
        # Save models 1-5
        if i == 1:
            mod = mod1
        elif i == 2:
            mod = mod2
        elif i == 3:
            mod = mod3
        elif i == 4:
            mod = mod4
        elif i == 5:
            mod = mod5
        
        params_out = OUTPUTS_TABLES / f"regression_progressive_model_{i}.csv"
        mod.params.rename("coef").to_frame().join(mod.bse.rename("se")).to_csv(params_out)
        
        if "awarez_lag7" in mod.params.index:
            lag7_coefs.append({
                "model": result["model"],
                "lag7_coef": mod.params["awarez_lag7"],
                "lag7_se": mod.bse["awarez_lag7"],
                "lag7_ci_low": mod.params["awarez_lag7"] - 1.96 * mod.bse["awarez_lag7"],
                "lag7_ci_hi": mod.params["awarez_lag7"] + 1.96 * mod.bse["awarez_lag7"],
            })

if lag7_coefs:
    df_lag7 = pd.DataFrame(lag7_coefs)
    lag7_out = OUTPUTS_TABLES / "regression_progressive_lag7_comparison.csv"
    df_lag7.to_csv(lag7_out, index=False)
    print(f"✓ Saved lag 7 coefficient comparison to: {lag7_out}")
    print("\nLag 7 Coefficient Across Models:")
    print(df_lag7[["model", "lag7_coef", "lag7_se"]].to_string(index=False))

print("\n" + "=" * 80)
print("PROGRESSIVE REGRESSION ANALYSIS COMPLETE")
print("=" * 80)

