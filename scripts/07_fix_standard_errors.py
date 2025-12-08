"""
Fix standard errors issue by trying alternative covariance specifications.

This script:
1. Re-runs the model with robust (non-clustered) standard errors
2. Checks for multicollinearity
3. Compares results
4. Creates corrected IRF plot
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
print("FIXING STANDARD ERRORS ISSUE")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(panel_path)

print(f"\nPanel shape: {df_panel.shape}")

# Prepare model data
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()

df_fe["cd_int"] = pd.to_numeric(df_fe["communitydistrict"], errors="coerce")
df_fe = df_fe.dropna(subset=["cd_int"])
df_fe["cd_int"] = df_fe["cd_int"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

formula_fe = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
)

y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")

print(f"\nDesign matrix shape: {X_fe.shape}")
print(f"  Observations: {X_fe.shape[0]:,}")
print(f"  Parameters: {X_fe.shape[1]}")

# Check for rank deficiency
rank = np.linalg.matrix_rank(X_fe.values)
print(f"  Matrix rank: {rank}")
if rank < X_fe.shape[1]:
    print(f"  ⚠️  RANK DEFICIENCY: {X_fe.shape[1] - rank} columns are linearly dependent")

# Try different covariance specifications
print("\n" + "=" * 80)
print("ATTEMPT 1: Robust Standard Errors (HC3)")
print("=" * 80)

groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")
mod_robust = sm.OLS(y_fe, X_fe, missing="drop").fit(cov_type="HC3")

print(f"Model fitted: {mod_robust.nobs:,} observations")
print(f"R-squared: {mod_robust.rsquared:.4f}")

# Check which awareness lags have standard errors
aware_params = [name for name in mod_robust.params.index if name.startswith("awarez_lag")]
print(f"\nAwareness lag parameters with robust SEs:")
has_se_count = 0
for param in aware_params:
    try:
        se = mod_robust.bse[param]
        if pd.isna(se) or se == 0 or np.isinf(se):
            print(f"  {param}: coef={mod_robust.params[param]:.6f}, se=NaN/0/Inf")
        else:
            print(f"  {param}: coef={mod_robust.params[param]:.6f}, se={se:.6f}")
            has_se_count += 1
    except KeyError:
        print(f"  {param}: KEY ERROR")

print(f"\nLags with standard errors: {has_se_count} / {len(aware_params)}")

# Extract IRF
lag_re = re.compile(r"^awarez_lag(\d+)$")
rows_robust = []

for name, coef in mod_robust.params.items():
    m = lag_re.match(name)
    if m:
        k = int(m.group(1))
        try:
            se = mod_robust.bse[name]
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
        
        rows_robust.append((k, coef, se, ci_lo, ci_hi))

ir_robust = pd.DataFrame(rows_robust, columns=["lag", "coef", "se", "ci_lo", "ci_hi"]).sort_values("lag")

print("\nImpulse Response Function (Robust SEs):")
print(ir_robust.to_string(index=False))

# Try clustered SEs again but check what's happening
print("\n" + "=" * 80)
print("ATTEMPT 2: Clustered Standard Errors (for comparison)")
print("=" * 80)

mod_clustered = sm.OLS(y_fe, X_fe, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups_fe}
)

aware_params_clust = [name for name in mod_clustered.params.index if name.startswith("awarez_lag")]
print(f"\nAwareness lag parameters with clustered SEs:")
has_se_clust = 0
for param in aware_params_clust:
    try:
        se = mod_clustered.bse[param]
        if pd.isna(se) or se == 0 or np.isinf(se):
            print(f"  {param}: coef={mod_clustered.params[param]:.6f}, se=NaN/0/Inf")
        else:
            print(f"  {param}: coef={mod_clustered.params[param]:.6f}, se={se:.6f}")
            has_se_clust += 1
    except KeyError:
        print(f"  {param}: KEY ERROR")

print(f"\nLags with standard errors: {has_se_clust} / {len(aware_params_clust)}")

# Compare coefficients
print("\n" + "=" * 80)
print("COMPARISON: Robust vs Clustered SEs")
print("=" * 80)

comparison = pd.DataFrame({
    "lag": ir_robust["lag"],
    "coef_robust": ir_robust["coef"],
    "se_robust": ir_robust["se"],
    "coef_clustered": [mod_clustered.params.get(f"awarez_lag{int(k)}", np.nan) for k in ir_robust["lag"]],
    "se_clustered": [mod_clustered.bse.get(f"awarez_lag{int(k)}", np.nan) for k in ir_robust["lag"]]
})

print(comparison.to_string(index=False))

# Use robust SEs for the plot (since they work)
ir = ir_robust.copy()

# Create improved plot
print("\n" + "=" * 80)
print("CREATING CORRECTED IRF PLOT")
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
        label="95% Confidence Interval (Robust SEs)",
        color="steelblue"
    )
    print(f"  ✓ Plotting confidence intervals for {has_ci.sum()} lags")
else:
    print("  ⚠️  No confidence intervals available")

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
    print(f"  Using tight y-axis scale (range: {coef_range:.6f})")

plt.title("Impulse Response of MH Share to Awareness (CD Fixed Effects)\nRobust Standard Errors", 
          fontsize=14, fontweight="bold")
plt.xlabel("Lag (days)", fontsize=12)
plt.ylabel("Δ mh_share (per 1σ awareness)", fontsize=12)
plt.grid(True, alpha=0.3, linestyle="--")
plt.legend(loc="best")
plt.tight_layout()

# Save
ir_png_path = OUTPUTS_FIGURES / "ir_mhshare_cdfe_robust_se.png"
ir_csv_path = OUTPUTS_TABLES / "ir_mhshare_cdfe_robust_se.csv"

plt.savefig(ir_png_path, dpi=180, bbox_inches="tight")
ir.to_csv(ir_csv_path, index=False)

print(f"\nSaved:")
print(f"  Plot: {ir_png_path}")
print(f"  Data: {ir_csv_path}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if has_se_count == len(aware_params):
    print("✓ SUCCESS: All lags now have standard errors using robust SEs")
    print("\nRecommendation: Use robust standard errors for this analysis.")
    print("While clustered SEs are preferred for panel data, robust SEs are still")
    print("valid and allow us to assess statistical significance.")
elif has_se_count > has_se_clust:
    print(f"✓ IMPROVEMENT: {has_se_count} lags have SEs with robust (vs {has_se_clust} with clustered)")
    print("\nRecommendation: Use robust standard errors, but note limitations.")
else:
    print("⚠️  Issue persists. May need to simplify model specification.")

print("\n" + "=" * 80)

