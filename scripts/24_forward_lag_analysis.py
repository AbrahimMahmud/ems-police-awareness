"""
Step 24: Forward-Looking Lag Analysis

This script examines how awareness on day t affects MH calls on future days
(t+1, t+2, ..., t+7). This helps understand the temporal dynamics of the
relationship and whether effects persist or accumulate over time.

Method:
- Create forward-looking variables: next_1, next_2, ..., next_7 (future days' mh_share)
- Examine how awareness on day t affects MH calls on days t+1, t+2, etc.
- Create scatter plots: awareness vs. future MH calls
- Run regressions: next_k ~ awareness_z + controls
"""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("FORWARD-LOOKING LAG ANALYSIS")
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
print(f"Analysis sample: {len(df_analysis):,} rows")

# Sort by community district and date
df_analysis = df_analysis.sort_values(["communitydistrict", "incident_date"]).reset_index(drop=True)

# ============================================================================
# Step 1: Create forward-looking variables
# ============================================================================

print("\n" + "=" * 80)
print("STEP 1: CREATING FORWARD-LOOKING VARIABLES")
print("=" * 80)

# Create next_1 through next_7 (future days' mh_share)
for i in range(1, 8):
    df_analysis[f'next_{i}'] = df_analysis.groupby('communitydistrict')['mh_share'].shift(-i)
    print(f"  Created next_{i}: {df_analysis[f'next_{i}'].notna().sum():,} non-null values")

# Ensure we have awareness_z
if "awareness_z" not in df_analysis.columns:
    print("⚠️  awareness_z not found, creating from awareness data...")
    if "tweet_count_all" in df_analysis.columns:
        df_analysis["awareness_z"] = (
            (df_analysis["tweet_count_all"] - df_analysis["tweet_count_all"].mean()) / 
            df_analysis["tweet_count_all"].std(ddof=0)
        )

# Filter to rows where we have both current awareness and future outcomes
df_forward = df_analysis[
    df_analysis["awareness_z"].notna() & 
    df_analysis[["next_1", "next_2", "next_3", "next_4", "next_5", "next_6", "next_7"]].notna().any(axis=1)
].copy()

print(f"\nRows with forward-looking data: {len(df_forward):,}")

# ============================================================================
# Step 2: Scatter Plots
# ============================================================================

print("\n" + "=" * 80)
print("STEP 2: CREATING SCATTER PLOTS")
print("=" * 80)

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, ax in enumerate(axes[:7], start=1):
    next_col = f'next_{i}'
    
    # Remove outliers for better visualization (top/bottom 1%)
    df_plot = df_forward[[next_col, 'awareness_z']].dropna()
    if len(df_plot) > 0:
        q_low = df_plot[next_col].quantile(0.01)
        q_hi = df_plot[next_col].quantile(0.99)
        df_plot = df_plot[(df_plot[next_col] >= q_low) & (df_plot[next_col] <= q_hi)]
        
        ax.scatter(df_plot['awareness_z'], df_plot[next_col], alpha=0.3, s=10)
        ax.set_xlabel('Awareness (z-score)', fontsize=10)
        ax.set_ylabel(f'mh_share on day t+{i}', fontsize=10)
        ax.set_title(f'Day t+{i}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
        ax.axvline(0, color='gray', linestyle='--', linewidth=0.5)

# Remove unused subplot
axes[7].axis('off')

plt.suptitle('Awareness on Day t vs. mh_share on Future Days', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()

scatter_out = OUTPUTS_FIGURES / "forward_lag_scatter.png"
plt.savefig(scatter_out, dpi=180, bbox_inches='tight')
plt.close()

print(f"✓ Saved scatter plots to: {scatter_out}")

# ============================================================================
# Step 3: Regressions for each forward lag
# ============================================================================

print("\n" + "=" * 80)
print("STEP 3: REGRESSIONS FOR EACH FORWARD LAG")
print("=" * 80)

# Prepare CD fixed effects
df_forward["cd_int"] = pd.to_numeric(df_forward["communitydistrict"], errors="coerce")
df_forward = df_forward.dropna(subset=["cd_int"])
df_forward["cd_int"] = df_forward["cd_int"].astype("int64")
df_forward["cd_str"] = df_forward["cd_int"].astype(str)

# Ensure date variables
if "dow" not in df_forward.columns:
    df_forward["dow"] = df_forward["incident_date"].dt.dayofweek
if "month" not in df_forward.columns:
    df_forward["month"] = df_forward["incident_date"].dt.month
if "year" not in df_forward.columns:
    df_forward["year"] = df_forward["incident_date"].dt.year

forward_regression_results = []

for i in range(1, 8):
    next_col = f'next_{i}'
    
    # Filter to rows with non-null next_i
    df_reg = df_forward[df_forward[next_col].notna()].copy()
    
    if len(df_reg) < 100:
        print(f"\n⚠️  next_{i}: Insufficient data ({len(df_reg)} rows), skipping")
        continue
    
    print(f"\nRegression for next_{i}: {len(df_reg):,} observations")
    
    # Simple model: next_i ~ awareness_z + controls
    formula_forward = (
        f"{next_col} ~ awareness_z + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    )
    
    y_forward, X_forward = patsy.dmatrices(formula_forward, data=df_reg, return_type="dataframe")
    groups_forward = df_reg.loc[y_forward.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_forward = sm.OLS(y_forward, X_forward, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups_forward}
    )
    
    print(f"  R-squared: {mod_forward.rsquared:.4f}")
    
    # Extract awareness_z coefficient
    if "awareness_z" in mod_forward.params.index:
        coef = mod_forward.params["awareness_z"]
        se = mod_forward.bse["awareness_z"]
        print(f"  awareness_z coefficient: {coef:.6f} (SE: {se:.6f})")
        
        forward_regression_results.append({
            'forward_lag': i,
            'n_obs': int(mod_forward.nobs),
            'r_squared': mod_forward.rsquared,
            'awareness_coef': coef,
            'awareness_se': se,
            'ci_low': coef - 1.96 * se,
            'ci_hi': coef + 1.96 * se
        })

if forward_regression_results:
    df_forward_reg = pd.DataFrame(forward_regression_results)
    forward_reg_out = OUTPUTS_TABLES / "forward_lag_results.csv"
    df_forward_reg.to_csv(forward_reg_out, index=False)
    print(f"\n✓ Saved regression results to: {forward_reg_out}")
    
    print("\nAwareness Coefficients by Forward Lag:")
    print(df_forward_reg[['forward_lag', 'awareness_coef', 'awareness_se', 'n_obs']].to_string(index=False))

# ============================================================================
# Step 4: Visualization of forward lag coefficients
# ============================================================================

print("\n" + "=" * 80)
print("STEP 4: VISUALIZING FORWARD LAG COEFFICIENTS")
print("=" * 80)

if forward_regression_results:
    df_plot = pd.DataFrame(forward_regression_results)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df_plot['forward_lag'], df_plot['awareness_coef'], 
           marker='o', linewidth=2, markersize=8, label='Coefficient')
    
    ax.fill_between(df_plot['forward_lag'], 
                   df_plot['ci_low'], 
                   df_plot['ci_hi'],
                   alpha=0.3, label='95% Confidence Interval')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_xlabel('Days Forward (t+k)', fontsize=12)
    ax.set_ylabel('Effect of Awareness on mh_share', fontsize=12)
    ax.set_title('Forward-Looking Effects: Awareness on Day t → mh_share on Day t+k', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xticks(df_plot['forward_lag'])
    
    plt.tight_layout()
    
    forward_plot_out = OUTPUTS_FIGURES / "forward_lag_coefficients.png"
    plt.savefig(forward_plot_out, dpi=180, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved coefficient plot to: {forward_plot_out}")

# ============================================================================
# Step 5: Compare with backward lags
# ============================================================================

print("\n" + "=" * 80)
print("STEP 5: COMPARISON WITH BACKWARD LAGS")
print("=" * 80)

# Use lag variables if available
lag_use = [0, 1, 2, 3, 7]
lag_cols = [f"awarez_lag{k}" for k in lag_use if f"awarez_lag{k}" in df_forward.columns]

if lag_cols:
    # Run regression with backward lags
    formula_backward = (
        "mh_share ~ " + " + ".join(lag_cols) + 
        " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    )
    
    df_backward = df_forward[df_forward["mh_share"].notna()].copy()
    df_backward = df_backward.loc[df_backward[lag_cols].notna().any(axis=1)].copy()
    
    if len(df_backward) > 100:
        y_backward, X_backward = patsy.dmatrices(formula_backward, data=df_backward, return_type="dataframe")
        groups_backward = df_backward.loc[y_backward.index, "cd_int"].to_numpy(dtype="int64")
        
        mod_backward = sm.OLS(y_backward, X_backward, missing="drop").fit(
            cov_type="cluster",
            cov_kwds={"groups": groups_backward}
        )
        
        print(f"Backward lag model:")
        print(f"  Observations: {int(mod_backward.nobs):,}")
        print(f"  R-squared: {mod_backward.rsquared:.4f}")
        
        if "awarez_lag7" in mod_backward.params.index:
            coef = mod_backward.params["awarez_lag7"]
            se = mod_backward.bse["awarez_lag7"]
            print(f"  Lag 7 coefficient: {coef:.6f} (SE: {se:.6f})")
        
        # Compare with forward lag 7
        if forward_regression_results and any(r['forward_lag'] == 7 for r in forward_regression_results):
            forward_7 = next(r for r in forward_regression_results if r['forward_lag'] == 7)
            print(f"\nComparison:")
            print(f"  Backward lag 7 (awareness t-7 → mh_share t): {coef:.6f} (SE: {se:.6f})")
            print(f"  Forward lag 7 (awareness t → mh_share t+7): {forward_7['awareness_coef']:.6f} (SE: {forward_7['awareness_se']:.6f})")

print("\n" + "=" * 80)
print("FORWARD-LOOKING LAG ANALYSIS COMPLETE")
print("=" * 80)
