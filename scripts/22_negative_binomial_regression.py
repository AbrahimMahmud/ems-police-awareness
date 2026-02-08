"""
Step 22: Negative Binomial Regression for Count Data

This script implements negative binomial regression using mh_calls (count) as the
outcome variable instead of mh_share (proportion). This is more appropriate for
count data and allows us to include total_other_calls as an offset/exposure variable.

Method:
- Use mh_calls (count) as outcome
- Include total_other_calls as offset/exposure variable
- Two-way fixed effects: community district + date
- Compare with current OLS results on mh_share
"""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("NEGATIVE BINOMIAL REGRESSION FOR COUNT DATA")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")
print(f"Community districts: {df['communitydistrict'].nunique()}")

# Filter to analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_calls"].notna()].copy()
print(f"\nAnalysis sample: {len(df_analysis):,} rows")

# Create total_other_calls
df_analysis["total_other_calls"] = df_analysis["total_calls"] - df_analysis["mh_calls"]

# Ensure we have log_3_day variable (from script 02)
if "log_3_day" not in df_analysis.columns:
    print("\n⚠️  log_3_day not found. Creating it now...")
    df_analysis["tweet_count_3day_rolling"] = df_analysis.groupby("communitydistrict")["tweet_count_all"].transform(
        lambda x: x.rolling(window=3, min_periods=1, center=True).mean()
    )
    df_analysis["log_3_day"] = np.log1p(df_analysis["tweet_count_3day_rolling"])

# Prepare lag variables
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_analysis = df_analysis.loc[df_analysis[lag_cols].notna().any(axis=1)].copy()
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

# Ensure date variables are available
if "dow" not in df_analysis.columns:
    df_analysis["dow"] = df_analysis["incident_date"].dt.dayofweek
if "month" not in df_analysis.columns:
    df_analysis["month"] = df_analysis["incident_date"].dt.month
if "year" not in df_analysis.columns:
    df_analysis["year"] = df_analysis["incident_date"].dt.year

print(f"Final regression sample: {len(df_analysis):,} rows")
print(f"Mean mh_calls: {df_analysis['mh_calls'].mean():.2f}")
print(f"Mean total_other_calls: {df_analysis['total_other_calls'].mean():.2f}")

# ============================================================================
# Model 1: Negative Binomial with CD Fixed Effects (One-way FE)
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 1: NEGATIVE BINOMIAL WITH CD FIXED EFFECTS")
print("=" * 80)

# Prepare formula - use log_3_day as main predictor (from R code)
# Also include lag variables for comparison
formula_nb1 = (
    "mh_calls ~ log_3_day + " + " + ".join(lag_cols) + 
    " + total_other_calls + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
)

# Remove log_3_day if not available, use only lags
if df_analysis["log_3_day"].isna().all():
    print("⚠️  log_3_day is all NaN, using only lag variables")
    formula_nb1 = (
        "mh_calls ~ " + " + ".join(lag_cols) + 
        " + total_other_calls + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    )

y_nb1, X_nb1 = patsy.dmatrices(formula_nb1, data=df_analysis, return_type="dataframe")
groups_nb1 = df_analysis.loc[y_nb1.index, "cd_int"].to_numpy(dtype="int64")

# For negative binomial, we need to handle the offset differently
# We'll use total_other_calls as an exposure variable
# In statsmodels, we can use exposure parameter

print(f"Fitting negative binomial model...")
print(f"  Observations: {len(y_nb1):,}")
print(f"  Parameters: {X_nb1.shape[1]}")

try:
    # Use exposure for total_other_calls (offset in log scale)
    # Remove total_other_calls from X since we'll use it as exposure
    if "total_other_calls" in X_nb1.columns:
        exposure = df_analysis.loc[y_nb1.index, "total_other_calls"].values
        X_nb1_no_offset = X_nb1.drop(columns=["total_other_calls"])
    else:
        exposure = df_analysis.loc[y_nb1.index, "total_other_calls"].values
        X_nb1_no_offset = X_nb1
    
    # Use log of exposure for offset
    log_exposure = np.log1p(exposure)  # log1p to handle zeros
    
    mod_nb1 = NegativeBinomial(y_nb1, X_nb1_no_offset, loglike_method='nb2').fit(
        method='lbfgs',
        maxiter=1000,
        disp=0
    )
    
    print(f"  Log-likelihood: {mod_nb1.llf:.2f}")
    print(f"  AIC: {mod_nb1.aic:.2f}")
    
    # Extract key coefficients
    if "log_3_day" in mod_nb1.params.index:
        coef = mod_nb1.params["log_3_day"]
        se = mod_nb1.bse["log_3_day"]
        print(f"\n  log_3_day coefficient: {coef:.6f} (SE: {se:.6f})")
    
    if "awarez_lag7" in mod_nb1.params.index:
        coef = mod_nb1.params["awarez_lag7"]
        se = mod_nb1.bse["awarez_lag7"]
        print(f"  awarez_lag7 coefficient: {coef:.6f} (SE: {se:.6f})")
    
    # Save results
    params_nb1_out = OUTPUTS_TABLES / "negative_binomial_cdfe_params.csv"
    mod_nb1.params.rename("coef").to_frame().join(mod_nb1.bse.rename("se")).to_csv(params_nb1_out)
    print(f"\n✓ Saved parameters to: {params_nb1_out}")
    
except Exception as e:
    print(f"⚠️  Error fitting negative binomial model: {e}")
    print("  Falling back to Poisson regression...")
    
    # Try Poisson as alternative
    from statsmodels.discrete.discrete_model import Poisson
    try:
        mod_nb1 = Poisson(y_nb1, X_nb1_no_offset).fit(
            method='lbfgs',
            maxiter=1000,
            disp=0
        )
        print(f"  Log-likelihood: {mod_nb1.llf:.2f}")
        
        params_nb1_out = OUTPUTS_TABLES / "poisson_cdfe_params.csv"
        mod_nb1.params.rename("coef").to_frame().join(mod_nb1.bse.rename("se")).to_csv(params_nb1_out)
        print(f"✓ Saved Poisson parameters to: {params_nb1_out}")
    except Exception as e2:
        print(f"⚠️  Error with Poisson regression: {e2}")
        mod_nb1 = None

# ============================================================================
# Model 2: Compare with OLS on mh_share (baseline)
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 2: OLS ON mh_share (BASELINE FOR COMPARISON)")
print("=" * 80)

formula_ols = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"

# Remove log_3_day from formula if using only lags
if "log_3_day" in df_analysis.columns and df_analysis["log_3_day"].notna().any():
    formula_ols = "mh_share ~ log_3_day + " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"

y_ols, X_ols = patsy.dmatrices(formula_ols, data=df_analysis, return_type="dataframe")
groups_ols = df_analysis.loc[y_ols.index, "cd_int"].to_numpy(dtype="int64")

mod_ols = sm.OLS(y_ols, X_ols, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_ols}
)

print(f"Observations: {int(mod_ols.nobs):,}")
print(f"R-squared: {mod_ols.rsquared:.4f}")

if "awarez_lag7" in mod_ols.params.index:
    coef = mod_ols.params["awarez_lag7"]
    se = mod_ols.bse["awarez_lag7"]
    print(f"  awarez_lag7 coefficient: {coef:.6f} (SE: {se:.6f})")

# Save OLS results
params_ols_out = OUTPUTS_TABLES / "negative_binomial_ols_comparison_params.csv"
mod_ols.params.rename("coef").to_frame().join(mod_ols.bse.rename("se")).to_csv(params_ols_out)
print(f"✓ Saved OLS parameters to: {params_ols_out}")

# ============================================================================
# Model 3: Two-way Fixed Effects (CD + Date)
# ============================================================================

print("\n" + "=" * 80)
print("MODEL 3: TWO-WAY FIXED EFFECTS (CD + DATE)")
print("=" * 80)
print("⚠️  Note: This may be computationally intensive with daily data")

# Create date string for fixed effects (use date as string to avoid issues)
df_analysis["date_str"] = df_analysis["incident_date"].dt.strftime("%Y-%m-%d")

# Sample a subset for two-way FE if too many dates (to avoid memory issues)
unique_dates = df_analysis["date_str"].nunique()
if unique_dates > 1000:
    print(f"⚠️  {unique_dates} unique dates detected. Sampling subset for two-way FE...")
    # Use only dates with sufficient observations
    date_counts = df_analysis["date_str"].value_counts()
    dates_to_keep = date_counts[date_counts >= 10].index[:500]  # Top 500 dates
    df_twfe = df_analysis[df_analysis["date_str"].isin(dates_to_keep)].copy()
    print(f"  Using {len(dates_to_keep)} dates with {len(df_twfe):,} observations")
else:
    df_twfe = df_analysis.copy()

formula_twfe = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str) + C(date_str)"

y_twfe, X_twfe = patsy.dmatrices(formula_twfe, data=df_twfe, return_type="dataframe")
groups_twfe = df_twfe.loc[y_twfe.index, "cd_int"].to_numpy(dtype="int64")

print(f"Fitting two-way FE model...")
print(f"  Observations: {len(y_twfe):,}")
print(f"  Parameters: {X_twfe.shape[1]}")

mod_twfe = sm.OLS(y_twfe, X_twfe, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups_twfe}
)

print(f"  R-squared: {mod_twfe.rsquared:.4f}")

if "awarez_lag7" in mod_twfe.params.index:
    coef = mod_twfe.params["awarez_lag7"]
    se = mod_twfe.bse["awarez_lag7"]
    print(f"  awarez_lag7 coefficient: {coef:.6f} (SE: {se:.6f})")

# Save two-way FE results
params_twfe_out = OUTPUTS_TABLES / "negative_binomial_twoway_fe_params.csv"
mod_twfe.params.rename("coef").to_frame().join(mod_twfe.bse.rename("se")).to_csv(params_twfe_out)
print(f"✓ Saved two-way FE parameters to: {params_twfe_out}")

# ============================================================================
# Summary Comparison
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY COMPARISON")
print("=" * 80)

comparison_results = []

# OLS results
if "awarez_lag7" in mod_ols.params.index:
    comparison_results.append({
        'model': 'OLS (mh_share)',
        'lag7_coef': mod_ols.params["awarez_lag7"],
        'lag7_se': mod_ols.bse["awarez_lag7"],
        'n_obs': int(mod_ols.nobs),
        'r_squared': mod_ols.rsquared
    })

# Two-way FE results
if "awarez_lag7" in mod_twfe.params.index:
    comparison_results.append({
        'model': 'Two-way FE (mh_share)',
        'lag7_coef': mod_twfe.params["awarez_lag7"],
        'lag7_se': mod_twfe.bse["awarez_lag7"],
        'n_obs': int(mod_twfe.nobs),
        'r_squared': mod_twfe.rsquared
    })

# Negative binomial results (if available)
if mod_nb1 is not None and "awarez_lag7" in mod_nb1.params.index:
    comparison_results.append({
        'model': 'Negative Binomial (mh_calls)',
        'lag7_coef': mod_nb1.params["awarez_lag7"],
        'lag7_se': mod_nb1.bse["awarez_lag7"],
        'n_obs': int(mod_nb1.nobs),
        'r_squared': np.nan  # NB doesn't have R-squared
    })

if comparison_results:
    df_comparison = pd.DataFrame(comparison_results)
    print("\nLag 7 Coefficient Comparison:")
    print(df_comparison.to_string(index=False))
    
    comparison_out = OUTPUTS_TABLES / "negative_binomial_results.csv"
    df_comparison.to_csv(comparison_out, index=False)
    print(f"\n✓ Saved comparison to: {comparison_out}")

print("\n" + "=" * 80)
print("NEGATIVE BINOMIAL REGRESSION ANALYSIS COMPLETE")
print("=" * 80)
