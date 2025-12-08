"""
Diagnostic and fix script for IRF issues.

This script:
1. Checks why standard errors are missing
2. Verifies awareness data variation
3. Checks for multicollinearity
4. Re-runs model with better diagnostics
5. Creates corrected IRF plot
"""

import pandas as pd
import numpy as np
import patsy
import statsmodels.api as sm
import re
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"

print("=" * 80)
print("IRF ISSUE DIAGNOSTICS AND FIX")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(panel_path)

print(f"\nPanel shape: {df_panel.shape}")
print(f"Date range: {df_panel['incident_date'].min()} to {df_panel['incident_date'].max()}")

# Check awareness variation
print("\n" + "=" * 80)
print("1. AWARENESS DATA VARIATION")
print("=" * 80)
print(f"Awareness_z stats:")
print(f"  Mean: {df_panel['awareness_z'].mean():.6f}")
print(f"  Std: {df_panel['awareness_z'].std():.6f}")
print(f"  Min: {df_panel['awareness_z'].min():.6f}")
print(f"  Max: {df_panel['awareness_z'].max():.6f}")
print(f"  Non-null: {df_panel['awareness_z'].notna().sum():,} / {len(df_panel):,}")

# Check lag variables
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

print("\n" + "=" * 80)
print("2. LAG VARIABLES CHECK")
print("=" * 80)
for lag_col in lag_cols:
    if lag_col in df_panel.columns:
        non_null = df_panel[lag_col].notna().sum()
        mean_val = df_panel[lag_col].mean()
        std_val = df_panel[lag_col].std()
        print(f"{lag_col}:")
        print(f"  Non-null: {non_null:,} ({100*non_null/len(df_panel):.1f}%)")
        print(f"  Mean: {mean_val:.6f}, Std: {std_val:.6f}")

# Prepare model data
print("\n" + "=" * 80)
print("3. PREPARING MODEL DATA")
print("=" * 80)

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()

print(f"Model sample size: {len(df_fe):,}")
print(f"Community districts: {df_fe['communitydistrict'].nunique()}")

# Check for rows with all lags
rows_with_all_lags = df_fe[lag_cols].notna().all(axis=1).sum()
print(f"Rows with all lags: {rows_with_all_lags:,} ({100*rows_with_all_lags/len(df_fe):.1f}%)")

# Clean community district
df_fe["cd_int"] = pd.to_numeric(df_fe["communitydistrict"], errors="coerce")
df_fe = df_fe.dropna(subset=["cd_int"])
df_fe["cd_int"] = df_fe["cd_int"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

# Check COVID phase distribution
print("\nCOVID phase distribution:")
print(df_fe['covid_phase'].value_counts().sort_index())

# Check for potential multicollinearity
print("\n" + "=" * 80)
print("4. CHECKING MULTICOLLINEARITY")
print("=" * 80)

# Check correlation between lags
lag_data = df_fe[lag_cols].dropna()
if len(lag_data) > 100:
    corr_matrix = lag_data.corr()
    print("\nLag correlation matrix:")
    print(corr_matrix.round(3))
    
    # Check for very high correlations
    high_corr_pairs = []
    for i in range(len(corr_matrix)):
        for j in range(i+1, len(corr_matrix)):
            if abs(corr_matrix.iloc[i, j]) > 0.95:
                high_corr_pairs.append((corr_matrix.index[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    
    if high_corr_pairs:
        print("\n⚠️  Very high correlations (>0.95):")
        for pair in high_corr_pairs:
            print(f"  {pair[0]} <-> {pair[1]}: {pair[2]:.3f}")
    else:
        print("\n✓ No extreme multicollinearity detected")

# Run model with diagnostics
print("\n" + "=" * 80)
print("5. RUNNING MODEL WITH DIAGNOSTICS")
print("=" * 80)

formula_fe = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
)

print(f"\nFormula: {formula_fe[:100]}...")

y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")

print(f"\nDesign matrix shape: {X_fe.shape}")
print(f"Number of parameters: {X_fe.shape[1]}")

# Check for perfect multicollinearity
if X_fe.shape[1] > X_fe.shape[0]:
    print("⚠️  WARNING: More parameters than observations!")
else:
    rank = np.linalg.matrix_rank(X_fe.values)
    print(f"Matrix rank: {rank} (out of {X_fe.shape[1]} columns)")
    if rank < X_fe.shape[1]:
        print(f"⚠️  WARNING: Rank deficiency! {X_fe.shape[1] - rank} columns are linearly dependent")

groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")

print("\nFitting model...")
mod_fe = sm.OLS(y_fe, X_fe, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups_fe}
)

print(f"\nModel fitted:")
print(f"  Observations: {mod_fe.nobs:,}")
print(f"  R-squared: {mod_fe.rsquared:.4f}")

# Check which parameters have standard errors
print("\n" + "=" * 80)
print("6. CHECKING STANDARD ERRORS")
print("=" * 80)

aware_params = [name for name in mod_fe.params.index if name.startswith("awarez_lag")]
print(f"\nAwareness lag parameters found: {len(aware_params)}")
print(f"Expected: {len(lag_cols)}")

for param in aware_params:
    try:
        se = mod_fe.bse[param]
        if pd.isna(se) or se == 0:
            print(f"  {param}: coef={mod_fe.params[param]:.6f}, se=NaN or 0")
        else:
            print(f"  {param}: coef={mod_fe.params[param]:.6f}, se={se:.6f}")
    except KeyError:
        print(f"  {param}: coef={mod_fe.params[param]:.6f}, se=KEY ERROR")

# Extract IRF with better error handling
print("\n" + "=" * 80)
print("7. EXTRACTING IRF")
print("=" * 80)

lag_re = re.compile(r"^awarez_lag(\d+)$")
rows = []

for name, coef in mod_fe.params.items():
    m = lag_re.match(name)
    if m:
        k = int(m.group(1))
        try:
            se = mod_fe.bse[name]
            if pd.isna(se) or se == 0 or np.isinf(se):
                se = np.nan
        except (KeyError, IndexError):
            se = np.nan
        
        if not pd.isna(se) and se > 0:
            ci_lo = coef - 1.96 * se
            ci_hi = coef + 1.96 * se
        else:
            ci_lo = np.nan
            ci_hi = np.nan
        
        rows.append((k, coef, se, ci_lo, ci_hi))

ir = pd.DataFrame(rows, columns=["lag", "coef", "se", "ci_lo", "ci_hi"]).sort_values("lag")

print("\nImpulse Response Function:")
print(ir.to_string(index=False))

# Check if we have enough SEs
has_se = ir["se"].notna().sum()
print(f"\nLags with standard errors: {has_se} / {len(ir)}")

if has_se < len(ir):
    print("\n⚠️  WARNING: Some lags are missing standard errors!")
    print("This may indicate:")
    print("  - Perfect multicollinearity")
    print("  - Insufficient variation in that lag")
    print("  - Numerical issues in the model")

# Create improved plot
print("\n" + "=" * 80)
print("8. CREATING IMPROVED IRF PLOT")
print("=" * 80)

plt.figure(figsize=(12, 6))
plt.axhline(0, lw=1, ls="--", color="gray", alpha=0.5)

# Plot coefficients
plt.plot(ir["lag"], ir["coef"], marker="o", markersize=10, linewidth=2, 
         label="Coefficient", color="steelblue", zorder=3)

# Plot confidence intervals where available
has_ci = ir["ci_lo"].notna() & ir["ci_hi"].notna()
if has_ci.any():
    plt.fill_between(
        ir.loc[has_ci, "lag"], 
        ir.loc[has_ci, "ci_lo"], 
        ir.loc[has_ci, "ci_hi"], 
        alpha=0.3, 
        label="95% Confidence Interval",
        color="steelblue"
    )

# Mark points without CIs
no_ci = ~has_ci
if no_ci.any():
    plt.scatter(
        ir.loc[no_ci, "lag"], 
        ir.loc[no_ci, "coef"], 
        marker="x", 
        s=150,
        color="red",
        label="No SE available",
        zorder=4,
        linewidths=2
    )

# Set appropriate y-axis scale
coef_range = ir["coef"].max() - ir["coef"].min()
if coef_range < 0.01:
    y_margin = max(0.001, abs(ir["coef"]).max() * 0.3)
    plt.ylim(ir["coef"].min() - y_margin, ir["coef"].max() + y_margin)
    print(f"Using tight y-axis scale (range: {coef_range:.6f})")

plt.title("Impulse Response of MH Share to Awareness (CD Fixed Effects)", 
          fontsize=14, fontweight="bold")
plt.xlabel("Lag (days)", fontsize=12)
plt.ylabel("Δ mh_share (per 1σ awareness)", fontsize=12)
plt.grid(True, alpha=0.3, linestyle="--")
plt.legend(loc="best")
plt.tight_layout()

# Save
ir_png_path = OUTPUTS_FIGURES / "ir_mhshare_cdfe_fixed.png"
ir_csv_path = OUTPUTS_TABLES / "ir_mhshare_cdfe_fixed.csv"

plt.savefig(ir_png_path, dpi=180, bbox_inches="tight")
ir.to_csv(ir_csv_path, index=False)

print(f"\nSaved:")
print(f"  Plot: {ir_png_path}")
print(f"  Data: {ir_csv_path}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if has_se == len(ir):
    print("✓ All lags have standard errors")
elif has_se > 0:
    print(f"⚠️  Only {has_se}/{len(ir)} lags have standard errors")
    print("   This may indicate model specification issues")
else:
    print("✗ No lags have standard errors - serious model issue!")

if abs(ir["coef"]).max() < 0.01:
    print("⚠️  Coefficients are very small (<0.01)")
    print("   This may explain why the plot appears flat")
    print("   The effect may genuinely be small, or there may be data issues")

print("\n" + "=" * 80)

