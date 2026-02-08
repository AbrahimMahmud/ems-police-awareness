"""
Step 21: De-meaning Analysis by Day-of-Week and Community District

This script implements de-meaning by day-of-week and community district to remove
day-of-week patterns that vary by geographic unit. This is a robustness check
that helps control for unobserved day-of-week effects that may differ across
community districts.

Method:
- Calculate mean mh_share for each weekday within each community district
- Create de-meaned variable: dm_mh_share = mh_share - mean(mh_share | cd, weekday)
- Re-run main regression models using de-meaned outcome
- Compare results with/without de-meaning
"""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("DE-MEANING ANALYSIS BY DAY-OF-WEEK AND COMMUNITY DISTRICT")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")
print(f"Community districts: {df['communitydistrict'].nunique()}")

# Filter to analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
print(f"\nAnalysis sample: {len(df_analysis):,} rows")

# Ensure dow is available
if "dow" not in df_analysis.columns:
    df_analysis["dow"] = df_analysis["incident_date"].dt.dayofweek

# ============================================================================
# Step 1: Calculate day-of-week means by community district
# ============================================================================

print("\n" + "=" * 80)
print("STEP 1: CALCULATING DAY-OF-WEEK MEANS BY COMMUNITY DISTRICT")
print("=" * 80)

# Group by CD and weekday, calculate means
cd_weekday_means = df_analysis.groupby(['communitydistrict', 'dow'])['mh_share'].mean().reset_index()
cd_weekday_means.rename(columns={'mh_share': 'mh_share_mean'}, inplace=True)

print(f"Calculated means for {len(cd_weekday_means):,} CD-weekday combinations")
print(f"Mean mh_share by weekday (across all CDs):")
print(df_analysis.groupby('dow')['mh_share'].mean())

# Merge back to main dataframe
df_analysis = df_analysis.merge(
    cd_weekday_means, 
    on=['communitydistrict', 'dow'], 
    how='left',
    suffixes=('', '_mean')
)

# Create de-meaned variable
df_analysis['dm_mh_share'] = df_analysis['mh_share'] - df_analysis['mh_share_mean']

print(f"\nDe-meaned variable created:")
print(f"  Mean of mh_share: {df_analysis['mh_share'].mean():.6f}")
print(f"  Mean of dm_mh_share: {df_analysis['dm_mh_share'].mean():.6f} (should be ~0)")
print(f"  Std of mh_share: {df_analysis['mh_share'].std():.6f}")
print(f"  Std of dm_mh_share: {df_analysis['dm_mh_share'].std():.6f}")

# ============================================================================
# Step 2: Prepare for regression
# ============================================================================

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_analysis = df_analysis.loc[df_analysis[lag_cols].notna().any(axis=1)].copy()
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

print(f"\nFinal regression sample: {len(df_analysis):,} rows")

# ============================================================================
# Step 3: Run regression with original mh_share (baseline)
# ============================================================================

print("\n" + "=" * 80)
print("STEP 3: BASELINE MODEL (ORIGINAL mh_share)")
print("=" * 80)

formula_baseline = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y_baseline, X_baseline = patsy.dmatrices(formula_baseline, data=df_analysis, return_type="dataframe")
groups_baseline = df_analysis.loc[y_baseline.index, "cd_int"].to_numpy(dtype="int64")

mod_baseline = sm.OLS(y_baseline, X_baseline, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_baseline}
)

print(f"Observations: {int(mod_baseline.nobs):,}")
print(f"R-squared: {mod_baseline.rsquared:.4f}")

# Extract key coefficients
baseline_results = {}
for lag in [0, 1, 7, 14]:
    lag_col = f"awarez_lag{lag}"
    if lag_col in mod_baseline.params.index:
        coef = mod_baseline.params[lag_col]
        se = mod_baseline.bse[lag_col]
        baseline_results[lag] = {
            'coef': coef,
            'se': se,
            'ci_low': coef - 1.96 * se,
            'ci_hi': coef + 1.96 * se
        }
        print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")

# ============================================================================
# Step 4: Run regression with de-meaned mh_share
# ============================================================================

print("\n" + "=" * 80)
print("STEP 4: DE-MEANED MODEL (dm_mh_share)")
print("=" * 80)

formula_demeaned = "dm_mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y_demeaned, X_demeaned = patsy.dmatrices(formula_demeaned, data=df_analysis, return_type="dataframe")
groups_demeaned = df_analysis.loc[y_demeaned.index, "cd_int"].to_numpy(dtype="int64")

mod_demeaned = sm.OLS(y_demeaned, X_demeaned, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_demeaned}
)

print(f"Observations: {int(mod_demeaned.nobs):,}")
print(f"R-squared: {mod_demeaned.rsquared:.4f}")

# Extract key coefficients
demeaned_results = {}
for lag in [0, 1, 7, 14]:
    lag_col = f"awarez_lag{lag}"
    if lag_col in mod_demeaned.params.index:
        coef = mod_demeaned.params[lag_col]
        se = mod_demeaned.bse[lag_col]
        demeaned_results[lag] = {
            'coef': coef,
            'se': se,
            'ci_low': coef - 1.96 * se,
            'ci_hi': coef + 1.96 * se
        }
        print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")

# ============================================================================
# Step 5: Compare results
# ============================================================================

print("\n" + "=" * 80)
print("STEP 5: COMPARISON OF BASELINE VS DE-MEANED MODELS")
print("=" * 80)

comparison_results = []
for lag in [0, 1, 7, 14]:
    if lag in baseline_results and lag in demeaned_results:
        base = baseline_results[lag]
        dem = demeaned_results[lag]
        
        # Calculate percent change
        pct_change = ((dem['coef'] - base['coef']) / abs(base['coef']) * 100) if base['coef'] != 0 else np.nan
        
        comparison_results.append({
            'lag': lag,
            'baseline_coef': base['coef'],
            'baseline_se': base['se'],
            'demeaned_coef': dem['coef'],
            'demeaned_se': dem['se'],
            'difference': dem['coef'] - base['coef'],
            'pct_change': pct_change
        })
        
        print(f"\nLag {lag}:")
        print(f"  Baseline:  {base['coef']:.6f} (SE: {base['se']:.6f})")
        print(f"  De-meaned: {dem['coef']:.6f} (SE: {dem['se']:.6f})")
        print(f"  Difference: {dem['coef'] - base['coef']:.6f} ({pct_change:.2f}%)")

# Save comparison
if comparison_results:
    df_comparison = pd.DataFrame(comparison_results)
    comparison_out = OUTPUTS_TABLES / "demeaned_regression_comparison.csv"
    df_comparison.to_csv(comparison_out, index=False)
    print(f"\n✓ Saved comparison to: {comparison_out}")

# Save full results
baseline_params_out = OUTPUTS_TABLES / "demeaned_baseline_params.csv"
mod_baseline.params.rename("coef").to_frame().join(mod_baseline.bse.rename("se")).to_csv(baseline_params_out)
print(f"✓ Saved baseline parameters to: {baseline_params_out}")

demeaned_params_out = OUTPUTS_TABLES / "demeaned_demeaned_params.csv"
mod_demeaned.params.rename("coef").to_frame().join(mod_demeaned.bse.rename("se")).to_csv(demeaned_params_out)
print(f"✓ Saved de-meaned parameters to: {demeaned_params_out}")

# ============================================================================
# Step 6: Cumulative effects comparison
# ============================================================================

print("\n" + "=" * 80)
print("STEP 6: CUMULATIVE EFFECTS (0-7 DAYS)")
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

cum_base, cum_se_base = cumulative_effect(mod_baseline, lags=(0, 1, 2, 3, 4, 5, 6, 7))
cum_dem, cum_se_dem = cumulative_effect(mod_demeaned, lags=(0, 1, 2, 3, 4, 5, 6, 7))

print(f"Baseline cumulative effect (0-7 days): {cum_base:.6f} ± {1.96*cum_se_base:.6f}")
print(f"De-meaned cumulative effect (0-7 days): {cum_dem:.6f} ± {1.96*cum_se_dem:.6f}")
print(f"Difference: {cum_dem - cum_base:.6f}")

# Save cumulative effects
cumulative_out = OUTPUTS_TABLES / "demeaned_cumulative_effects.csv"
pd.DataFrame({
    'model': ['baseline', 'demeaned'],
    'cumulative_coef': [cum_base, cum_dem],
    'cumulative_se': [cum_se_base, cum_se_dem],
    'ci_low': [cum_base - 1.96*cum_se_base, cum_dem - 1.96*cum_se_dem],
    'ci_hi': [cum_base + 1.96*cum_se_base, cum_dem + 1.96*cum_se_dem]
}).to_csv(cumulative_out, index=False)
print(f"✓ Saved cumulative effects to: {cumulative_out}")

print("\n" + "=" * 80)
print("DE-MEANING ANALYSIS COMPLETE")
print("=" * 80)
