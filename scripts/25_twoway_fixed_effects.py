"""
Step 25: Two-Way Fixed Effects Analysis

This script adds date fixed effects in addition to community district fixed effects.
This controls for time-varying factors that affect all districts equally (e.g., 
citywide events, policy changes, seasonal effects beyond month×year).

Method:
- Add date fixed effects: C(incident_date) or date dummies
- Compare with one-way fixed effects (CD only)
- Note: This may be computationally intensive with daily data
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
print("TWO-WAY FIXED EFFECTS ANALYSIS")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")
print(f"Community districts: {df['communitydistrict'].nunique()}")
print(f"Unique dates: {df['incident_date'].nunique()}")

# Filter to analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
print(f"Analysis sample: {len(df_analysis):,} rows")

# Prepare lag variables
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_analysis = df_analysis.loc[df_analysis[lag_cols].notna().any(axis=1)].copy()
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

# Ensure date variables
if "dow" not in df_analysis.columns:
    df_analysis["dow"] = df_analysis["incident_date"].dt.dayofweek
if "month" not in df_analysis.columns:
    df_analysis["month"] = df_analysis["incident_date"].dt.month
if "year" not in df_analysis.columns:
    df_analysis["year"] = df_analysis["incident_date"].dt.year

# Create date string for fixed effects
df_analysis["date_str"] = df_analysis["incident_date"].dt.strftime("%Y-%m-%d")

print(f"Final regression sample: {len(df_analysis):,} rows")
print(f"Unique dates in sample: {df_analysis['date_str'].nunique()}")

# ============================================================================
# Model 1: One-way Fixed Effects (CD only) - Baseline
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 1: ONE-WAY FIXED EFFECTS (CD ONLY) - BASELINE")
print("=" * 80)

formula_oneway = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y_oneway, X_oneway = patsy.dmatrices(formula_oneway, data=df_analysis, return_type="dataframe")
groups_oneway = df_analysis.loc[y_oneway.index, "cd_int"].to_numpy(dtype="int64")

print(f"Fitting one-way FE model...")
print(f"  Observations: {len(y_oneway):,}")
print(f"  Parameters: {X_oneway.shape[1]}")

mod_oneway = sm.OLS(y_oneway, X_oneway, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_oneway}
)

print(f"  R-squared: {mod_oneway.rsquared:.4f}")

# Extract key coefficients
oneway_results = {}
for lag in [0, 1, 7, 14]:
    lag_col = f"awarez_lag{lag}"
    if lag_col in mod_oneway.params.index:
        coef = mod_oneway.params[lag_col]
        se = mod_oneway.bse[lag_col]
        oneway_results[lag] = {'coef': coef, 'se': se}
        print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")

# Save one-way FE results
params_oneway_out = OUTPUTS_TABLES / "twoway_fe_oneway_params.csv"
mod_oneway.params.rename("coef").to_frame().join(mod_oneway.bse.rename("se")).to_csv(params_oneway_out)
print(f"\n✓ Saved one-way FE parameters to: {params_oneway_out}")

# ============================================================================
# Model 2: Two-way Fixed Effects (CD + Date)
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 2: TWO-WAY FIXED EFFECTS (CD + DATE)")
print("=" * 80)

# Check number of unique dates
unique_dates = df_analysis["date_str"].nunique()
print(f"Unique dates: {unique_dates}")

# If too many dates, we have a few options:
# 1. Sample subset of dates
# 2. Use date bins (e.g., weekly)
# 3. Use only dates with sufficient observations

if unique_dates > 1000:
    print(f"⚠️  {unique_dates} unique dates detected. This may be computationally intensive.")
    print("  Options:")
    print("    1. Sample subset of dates")
    print("    2. Use weekly bins")
    print("    3. Use only dates with sufficient observations")
    
    # Option: Use only dates with sufficient observations
    date_counts = df_analysis["date_str"].value_counts()
    dates_to_keep = date_counts[date_counts >= 20].index  # At least 20 observations per date
    
    if len(dates_to_keep) > 500:
        # Further limit to top 500 dates by observation count
        dates_to_keep = date_counts[date_counts >= 20].head(500).index
    
    df_twfe = df_analysis[df_analysis["date_str"].isin(dates_to_keep)].copy()
    print(f"  Using {len(dates_to_keep)} dates with {len(df_twfe):,} observations")
else:
    df_twfe = df_analysis.copy()

formula_twfe = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str) + C(date_str)"

print(f"Fitting two-way FE model...")
print(f"  Observations: {len(df_twfe):,}")
print(f"  Formula includes date fixed effects")

try:
    y_twfe, X_twfe = patsy.dmatrices(formula_twfe, data=df_twfe, return_type="dataframe")
    groups_twfe = df_twfe.loc[y_twfe.index, "cd_int"].to_numpy(dtype="int64")
    
    print(f"  Parameters: {X_twfe.shape[1]}")
    
    if X_twfe.shape[1] > 50000:
        print(f"  ⚠️  Warning: Very large number of parameters ({X_twfe.shape[1]}).")
        print(f"     This may take a long time or run out of memory.")
        print(f"     Consider using a smaller date subset.")
    
    mod_twfe = sm.OLS(y_twfe, X_twfe, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups_twfe}
    )
    
    print(f"  R-squared: {mod_twfe.rsquared:.4f}")
    
    # Extract key coefficients
    twfe_results = {}
    for lag in [0, 1, 7, 14]:
        lag_col = f"awarez_lag{lag}"
        if lag_col in mod_twfe.params.index:
            coef = mod_twfe.params[lag_col]
            se = mod_twfe.bse[lag_col]
            twfe_results[lag] = {'coef': coef, 'se': se}
            print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")
    
    # Save two-way FE results
    params_twfe_out = OUTPUTS_TABLES / "twoway_fe_twoway_params.csv"
    mod_twfe.params.rename("coef").to_frame().join(mod_twfe.bse.rename("se")).to_csv(params_twfe_out)
    print(f"\n✓ Saved two-way FE parameters to: {params_twfe_out}")
    
except Exception as e:
    print(f"  ⚠️  Error fitting two-way FE model: {e}")
    print(f"     This is likely due to computational limitations.")
    print(f"     Consider using a smaller date subset or alternative approach.")
    mod_twfe = None
    twfe_results = {}

# ============================================================================
# Model 3: Alternative: Weekly Date Bins
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 3: ALTERNATIVE - WEEKLY DATE BINS")
print("=" * 80)

# Create weekly bins to reduce number of date fixed effects
df_analysis["year_week"] = (
    df_analysis["incident_date"].dt.isocalendar().year.astype(str) + "_" +
    df_analysis["incident_date"].dt.isocalendar().week.astype(str).str.zfill(2)
)

unique_weeks = df_analysis["year_week"].nunique()
print(f"Unique weeks: {unique_weeks}")

formula_weekly = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str) + C(year_week)"

y_weekly, X_weekly = patsy.dmatrices(formula_weekly, data=df_analysis, return_type="dataframe")
groups_weekly = df_analysis.loc[y_weekly.index, "cd_int"].to_numpy(dtype="int64")

print(f"Fitting weekly FE model...")
print(f"  Observations: {len(y_weekly):,}")
print(f"  Parameters: {X_weekly.shape[1]}")

mod_weekly = sm.OLS(y_weekly, X_weekly, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_weekly}
)

print(f"  R-squared: {mod_weekly.rsquared:.4f}")

# Extract key coefficients
weekly_results = {}
for lag in [0, 1, 7, 14]:
    lag_col = f"awarez_lag{lag}"
    if lag_col in mod_weekly.params.index:
        coef = mod_weekly.params[lag_col]
        se = mod_weekly.bse[lag_col]
        weekly_results[lag] = {'coef': coef, 'se': se}
        print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")

# Save weekly FE results
params_weekly_out = OUTPUTS_TABLES / "twoway_fe_weekly_params.csv"
mod_weekly.params.rename("coef").to_frame().join(mod_weekly.bse.rename("se")).to_csv(params_weekly_out)
print(f"\n✓ Saved weekly FE parameters to: {params_weekly_out}")

# ============================================================================
# Comparison
# ============================================================================

print("\n" + "=" * 80)
print("COMPARISON OF FIXED EFFECTS MODELS")
print("=" * 80)

comparison_results = []

# One-way FE
for lag in [0, 1, 7, 14]:
    if lag in oneway_results:
        comparison_results.append({
            'model': 'One-way FE (CD only)',
            'lag': lag,
            'coef': oneway_results[lag]['coef'],
            'se': oneway_results[lag]['se'],
            'n_obs': int(mod_oneway.nobs),
            'r_squared': mod_oneway.rsquared
        })

# Weekly FE
for lag in [0, 1, 7, 14]:
    if lag in weekly_results:
        comparison_results.append({
            'model': 'Two-way FE (CD + Week)',
            'lag': lag,
            'coef': weekly_results[lag]['coef'],
            'se': weekly_results[lag]['se'],
            'n_obs': int(mod_weekly.nobs),
            'r_squared': mod_weekly.rsquared
        })

# Two-way FE (if available)
if mod_twfe is not None:
    for lag in [0, 1, 7, 14]:
        if lag in twfe_results:
            comparison_results.append({
                'model': 'Two-way FE (CD + Date)',
                'lag': lag,
                'coef': twfe_results[lag]['coef'],
                'se': twfe_results[lag]['se'],
                'n_obs': int(mod_twfe.nobs),
                'r_squared': mod_twfe.rsquared
            })

if comparison_results:
    df_comparison = pd.DataFrame(comparison_results)
    
    print("\nLag 7 Coefficient Comparison:")
    df_lag7 = df_comparison[df_comparison['lag'] == 7]
    if len(df_lag7) > 0:
        print(df_lag7[['model', 'coef', 'se', 'r_squared']].to_string(index=False))
    
    comparison_out = OUTPUTS_TABLES / "twoway_fe_results.csv"
    df_comparison.to_csv(comparison_out, index=False)
    print(f"\n✓ Saved comparison to: {comparison_out}")

# Cumulative effects comparison
print("\n" + "=" * 80)
print("CUMULATIVE EFFECTS (0-7 DAYS)")
print("=" * 80)

def cumulative_effect(model, lags=(0, 1, 2, 3, 4, 5, 6, 7)):
    """Calculate cumulative effect over specified lags."""
    names = [f"awarez_lag{k}" for k in lags if f"awarez_lag{k}" in model.params.index]
    if not names:
        return np.nan, np.nan
    S = model.params.loc[names].sum()
    VC = model.cov_params().loc[names, names].to_numpy()
    se = float(np.sqrt(VC.sum()))
    return S, se

cum_oneway, cum_se_oneway = cumulative_effect(mod_oneway, lags=(0, 1, 2, 3, 4, 5, 6, 7))
cum_weekly, cum_se_weekly = cumulative_effect(mod_weekly, lags=(0, 1, 2, 3, 4, 5, 6, 7))

print(f"One-way FE cumulative effect (0-7 days): {cum_oneway:.6f} ± {1.96*cum_se_oneway:.6f}")
print(f"Weekly FE cumulative effect (0-7 days): {cum_weekly:.6f} ± {1.96*cum_se_weekly:.6f}")

if mod_twfe is not None:
    cum_twfe, cum_se_twfe = cumulative_effect(mod_twfe, lags=(0, 1, 2, 3, 4, 5, 6, 7))
    print(f"Two-way FE cumulative effect (0-7 days): {cum_twfe:.6f} ± {1.96*cum_se_twfe:.6f}")

# Save cumulative effects
cumulative_out = OUTPUTS_TABLES / "twoway_fe_cumulative_effects.csv"
cumulative_data = {
    'model': ['One-way FE', 'Weekly FE'],
    'cumulative_coef': [cum_oneway, cum_weekly],
    'cumulative_se': [cum_se_oneway, cum_se_weekly],
    'ci_low': [cum_oneway - 1.96*cum_se_oneway, cum_weekly - 1.96*cum_se_weekly],
    'ci_hi': [cum_oneway + 1.96*cum_se_oneway, cum_weekly + 1.96*cum_se_weekly]
}

if mod_twfe is not None:
    cumulative_data['model'].append('Two-way FE')
    cumulative_data['cumulative_coef'].append(cum_twfe)
    cumulative_data['cumulative_se'].append(cum_se_twfe)
    cumulative_data['ci_low'].append(cum_twfe - 1.96*cum_se_twfe)
    cumulative_data['ci_hi'].append(cum_twfe + 1.96*cum_se_twfe)

pd.DataFrame(cumulative_data).to_csv(cumulative_out, index=False)
print(f"\n✓ Saved cumulative effects to: {cumulative_out}")

print("\n" + "=" * 80)
print("TWO-WAY FIXED EFFECTS ANALYSIS COMPLETE")
print("=" * 80)
