"""
Step 4: Create visualizations of regression results.

This script:
- Creates impulse response function plot from CD fixed effects model
- Saves plot and data to outputs/figures/
"""

import re
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"

# Create output directory if it doesn't exist
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

# Load model results from previous step
# We need to re-run the model or load parameters
PANEL_PATH = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
PARAMS_PATH = OUTPUTS_TABLES / "dl_model_params_with_cdfe.csv"

if not PANEL_PATH.exists():
    raise FileNotFoundError(
        f"Panel file not found: {PANEL_PATH}. Run 02_merge_awareness.py first."
    )

# Re-run the CD fixed effects model to get full model object
print("Re-running CD fixed effects model for visualization...")
import patsy
import statsmodels.api as sm

df_panel = pd.read_parquet(PANEL_PATH)
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()

df_fe["cd_int"] = df_fe["communitydistrict"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

formula_fe = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
)

y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")

groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")
mod_fe = sm.OLS(y_fe, X_fe, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups_fe}
)

# Extract lag betas and confidence intervals
print("Extracting impulse response function...")
lag_re = re.compile(r"^awarez_lag(\d+)$")
rows = []
for name, coef in mod_fe.params.items():
    m = lag_re.match(name)
    if m:
        k = int(m.group(1))
        # Handle missing standard errors gracefully
        try:
            se = mod_fe.bse.get(name, np.nan)
            if pd.isna(se) or se == 0:
                se = np.nan
        except (KeyError, AttributeError):
            se = np.nan
        
        # Calculate confidence intervals if SE is available
        if not pd.isna(se) and se > 0:
            ci_lo = coef - 1.96 * se
            ci_hi = coef + 1.96 * se
        else:
            ci_lo = np.nan
            ci_hi = np.nan
        
        rows.append((k, coef, se, ci_lo, ci_hi))

ir = pd.DataFrame(rows, columns=["lag", "coef", "se", "ci_lo", "ci_hi"]).sort_values("lag")

print("\nImpulse response function:")
print(ir.to_string(index=False))

# Check for missing standard errors
missing_se = ir["se"].isna().sum()
if missing_se > 0:
    print(f"\n⚠️  WARNING: {missing_se} out of {len(ir)} lag coefficients have missing standard errors")
    print("  This may indicate model specification issues or numerical problems")

# Plot impulse response
print("\nCreating impulse response plot...")
plt.figure(figsize=(10, 6))
plt.axhline(0, lw=1, ls="--", color="gray", alpha=0.5)

# Plot coefficients
plt.plot(ir["lag"], ir["coef"], marker="o", markersize=8, linewidth=2, label="Coefficient")

# Plot confidence intervals only where available
has_ci = ir["ci_lo"].notna() & ir["ci_hi"].notna()
if has_ci.any():
    plt.fill_between(
        ir.loc[has_ci, "lag"], 
        ir.loc[has_ci, "ci_lo"], 
        ir.loc[has_ci, "ci_hi"], 
        alpha=0.2, 
        label="95% Confidence Interval"
    )
    # Also plot points without CIs in a different style
    no_ci = ~has_ci
    if no_ci.any():
        plt.plot(
            ir.loc[no_ci, "lag"], 
            ir.loc[no_ci, "coef"], 
            marker="x", 
            markersize=10, 
            linestyle="None",
            color="red",
            label="No SE available"
        )
else:
    print("  ⚠️  No confidence intervals available for plotting")

# Set appropriate y-axis scale
coef_range = ir["coef"].max() - ir["coef"].min()
if coef_range < 0.01:
    # If coefficients are very small, use a tighter scale
    y_margin = max(0.001, abs(ir["coef"]).max() * 0.2)
    plt.ylim(ir["coef"].min() - y_margin, ir["coef"].max() + y_margin)
    print(f"  Using tight y-axis scale (range: {coef_range:.6f})")

plt.title("Impulse Response of MH Share to Awareness (CD Fixed Effects)", fontsize=14, fontweight="bold")
plt.xlabel("Lag (days)", fontsize=12)
plt.ylabel("Δ mh_share (per 1σ awareness)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

# Save plot
ir_png_path = OUTPUTS_FIGURES / "ir_mhshare_cdfe.png"
plt.savefig(ir_png_path, dpi=180, bbox_inches="tight")
print(f"Saved plot to: {ir_png_path}")

# Save data
ir_csv_path = OUTPUTS_TABLES / "ir_mhshare_cdfe.csv"
ir.to_csv(ir_csv_path, index=False)
print(f"Saved IRF data to: {ir_csv_path}")

# Also create a more detailed plot with all lags if we have them
# Check if we have intermediate lags (4, 5, 6, etc.)
all_lags = sorted([int(m.group(1)) for name in mod_fe.params.index if (m := lag_re.match(name))])
if len(all_lags) > len(lag_use):
    print("\nCreating detailed IRF plot with all available lags...")
    rows_all = []
    for name, coef in mod_fe.params.items():
        m = lag_re.match(name)
        if m:
            k = int(m.group(1))
            se = mod_fe.bse[name]
            ci_lo, ci_hi = mod_fe.conf_int().loc[name].tolist()
            rows_all.append((k, coef, se, ci_lo, ci_hi))
    
    ir_all = pd.DataFrame(rows_all, columns=["lag", "coef", "se", "ci_lo", "ci_hi"]).sort_values("lag")
    
    plt.figure(figsize=(12, 6))
    plt.axhline(0, lw=1, ls="--", color="gray", alpha=0.5)
    plt.plot(ir_all["lag"], ir_all["coef"], marker="o", markersize=6, linewidth=1.5, label="Coefficient")
    plt.fill_between(
        ir_all["lag"], ir_all["ci_lo"], ir_all["ci_hi"], alpha=0.2, label="95% Confidence Interval"
    )
    plt.title("Impulse Response of MH Share to Awareness (All Lags, CD Fixed Effects)", fontsize=14, fontweight="bold")
    plt.xlabel("Lag (days)", fontsize=12)
    plt.ylabel("Δ mh_share (per 1σ awareness)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    ir_all_png_path = OUTPUTS_FIGURES / "ir_mhshare_cdfe_all_lags.png"
    plt.savefig(ir_all_png_path, dpi=180, bbox_inches="tight")
    print(f"Saved detailed plot to: {ir_all_png_path}")

print("\n" + "=" * 80)
print("Visualizations complete!")
print("=" * 80)

