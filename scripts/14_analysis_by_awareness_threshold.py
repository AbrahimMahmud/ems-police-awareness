"""
Step 14: Alternative analysis using awareness thresholds.

This script creates binary indicators for high awareness days and runs
analysis using threshold-based approach instead of continuous awareness measure.
Compares results with date-of-killing approach (current method).
"""

import pandas as pd
import numpy as np
import patsy
import statsmodels.api as sm
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("ANALYSIS BY AWARENESS THRESHOLD")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Create threshold indicators
thresholds = [1.0, 1.5, 2.0]  # Standard deviations

print("\n" + "=" * 80)
print("AWARENESS DISTRIBUTION")
print("=" * 80)
if "awareness_z" in df.columns:
    awareness_data = df["awareness_z"].dropna()
    print(f"\nAwareness z-score statistics:")
    print(f"  Mean: {awareness_data.mean():.3f}")
    print(f"  Std: {awareness_data.std():.3f}")
    print(f"  Min: {awareness_data.min():.3f}")
    print(f"  Max: {awareness_data.max():.3f}")
    print(f"  Median: {awareness_data.median():.3f}")
    
    for threshold in thresholds:
        n_above = (awareness_data > threshold).sum()
        pct_above = n_above / len(awareness_data) * 100
        print(f"\n  Threshold: {threshold} SD")
        print(f"    Days above threshold: {n_above} ({pct_above:.2f}%)")
        if n_above > 0:
            print(f"    Mean awareness on high days: {awareness_data[awareness_data > threshold].mean():.3f}")
            print(f"    Dates above threshold (sample):")
            high_days = df[df["awareness_z"] > threshold]["incident_date"].drop_duplicates().head(10)
            for date in high_days:
                print(f"      {date.date()}")

# Create threshold indicators (use underscore instead of period in column names)
for threshold in thresholds:
    threshold_str = str(threshold).replace('.', '_')
    df[f"high_awareness_{threshold_str}sd"] = (df["awareness_z"] > threshold).astype(int)

# Prepare analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

print(f"\nAnalysis sample: {len(df_analysis):,} rows")

def run_model(formula, data, model_name):
    """Run OLS model with clustered standard errors."""
    y, X = patsy.dmatrices(formula, data=data, return_type="dataframe")
    groups = data.loc[y.index, "cd_int"].to_numpy(dtype="int64")
    
    model = sm.OLS(y, X, missing="drop").fit(
        cov_type="cluster", 
        cov_kwds={"groups": groups}
    )
    
    return model

# Run analysis for each threshold
results = []

for threshold in thresholds:
    threshold_str = str(threshold).replace('.', '_')
    threshold_col = f"high_awareness_{threshold_str}sd"
    
    if threshold_col not in df_analysis.columns:
        continue
    
    print("\n" + "=" * 80)
    print(f"THRESHOLD ANALYSIS: {threshold} SD")
    print("=" * 80)
    
    # Create lagged indicators
    for lag in [0, 1, 2, 3, 7, 14]:
        lag_col = f"{threshold_col}_lag{lag}"
        df_analysis[lag_col] = df_analysis.groupby("communitydistrict")[threshold_col].shift(lag)
    
    # Model with threshold indicators
    lag_cols_threshold = [f"{threshold_col}_lag{lag}" for lag in [0, 1, 2, 3, 7, 14]]
    
    # Filter to rows with valid data
    df_threshold = df_analysis[(df_analysis["total_calls"] >= 5) & df_analysis["mh_share"].notna()].copy()
    df_threshold = df_threshold.loc[df_threshold[lag_cols_threshold].notna().any(axis=1)].copy()
    
    if len(df_threshold) < 100:
        print(f"    ⚠️  Insufficient data after filtering ({len(df_threshold)} rows), skipping")
        continue
    
    formula = "mh_share ~ " + " + ".join(lag_cols_threshold) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    
    mod = run_model(formula, df_threshold, f"Threshold {threshold}SD")
    
    print(f"\nObservations: {int(mod.nobs):,}")
    print(f"R-squared: {mod.rsquared:.4f}")
    
    # Extract key coefficients
    for lag in [0, 1, 2, 3, 7, 14]:
        lag_col = f"{threshold_col}_lag{lag}"
        if lag_col in mod.params.index:
            coef = mod.params[lag_col]
            se = mod.bse[lag_col]
            results.append({
                "threshold": threshold,
                "lag": lag,
                "coefficient": coef,
                "se": se,
                "ci_low": coef - 1.96 * se,
                "ci_hi": coef + 1.96 * se,
                "t_stat": coef / se if se > 0 else np.nan,
            })
            print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")
    
    # Save model results
    params_out = OUTPUTS_TABLES / f"awareness_threshold_{threshold}sd_params.csv"
    mod.params.rename("coef").to_frame().join(mod.bse.rename("se")).to_csv(params_out)
    print(f"\n✓ Saved to: {params_out}")

# Save comparison
if results:
    df_results = pd.DataFrame(results)
    comparison_out = OUTPUTS_TABLES / "awareness_threshold_analysis.csv"
    df_results.to_csv(comparison_out, index=False)
    print(f"\n✓ Saved threshold comparison to: {comparison_out}")
    
    print("\n" + "=" * 80)
    print("THRESHOLD COMPARISON")
    print("=" * 80)
    print("\nKey lags by threshold:")
    for threshold in thresholds:
        df_thresh = df_results[df_results["threshold"] == threshold]
        if len(df_thresh) > 0:
            print(f"\nThreshold: {threshold} SD")
            print(df_thresh[["lag", "coefficient", "se", "ci_low", "ci_hi"]].to_string(index=False))

# Compare with continuous awareness (current method)
print("\n" + "=" * 80)
print("COMPARISON: Threshold vs Continuous Awareness")
print("=" * 80)

# Run continuous model for comparison
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols_continuous = [f"awarez_lag{k}" for k in lag_use if f"awarez_lag{k}" in df_analysis.columns]

if lag_cols_continuous:
    formula_continuous = "mh_share ~ " + " + ".join(lag_cols_continuous) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    mod_continuous = run_model(formula_continuous, df_analysis, "Continuous")
    
    print(f"\nContinuous awareness model:")
    print(f"  Observations: {int(mod_continuous.nobs):,}")
    print(f"  R-squared: {mod_continuous.rsquared:.4f}")
    
    if "awarez_lag7" in mod_continuous.params.index:
        coef_cont = mod_continuous.params["awarez_lag7"]
        se_cont = mod_continuous.bse["awarez_lag7"]
        print(f"  Lag 7 coefficient: {coef_cont:.6f} (SE: {se_cont:.6f})")
        
        # Compare with threshold models
        print("\n  Comparison at lag 7:")
        for threshold in thresholds:
            df_thresh_lag7 = df_results[(df_results["threshold"] == threshold) & (df_results["lag"] == 7)]
            if len(df_thresh_lag7) > 0:
                coef_thresh = df_thresh_lag7.iloc[0]["coefficient"]
                print(f"    {threshold} SD threshold: {coef_thresh:.6f}")

print("\n" + "=" * 80)
print("AWARENESS THRESHOLD ANALYSIS COMPLETE")
print("=" * 80)

