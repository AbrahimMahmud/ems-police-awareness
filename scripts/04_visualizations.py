"""Create impulse response function visualization from regression results."""

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import patsy
import statsmodels.api as sm
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(PANEL_PATH)

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_fe = df_panel[df_panel["total_calls"] >= 5].copy()
df_fe = df_fe.dropna(subset=["mh_share", "communitydistrict"])
df_fe = df_fe.loc[df_fe[lag_cols].notna().any(axis=1)].copy()
df_fe["cd_int"] = df_fe["communitydistrict"].astype("int64")
df_fe["cd_str"] = df_fe["cd_int"].astype(str)

formula_fe = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y_fe, X_fe = patsy.dmatrices(formula_fe, data=df_fe, return_type="dataframe")
groups_fe = df_fe.loc[y_fe.index, "cd_int"].to_numpy(dtype="int64")
mod_fe = sm.OLS(y_fe, X_fe, missing="drop").fit(cov_type="cluster", cov_kwds={"groups": groups_fe})

lag_re = re.compile(r"^awarez_lag(\d+)$")
rows = []
for name, coef in mod_fe.params.items():
    m = lag_re.match(name)
    if m:
        k = int(m.group(1))
        se = mod_fe.bse.get(name, np.nan)
        if pd.isna(se) or se == 0:
            se = np.nan
        if not pd.isna(se) and se > 0:
            ci_lo = coef - 1.96 * se
            ci_hi = coef + 1.96 * se
        else:
            ci_lo = ci_hi = np.nan
        rows.append((k, coef, se, ci_lo, ci_hi))

ir = pd.DataFrame(rows, columns=["lag", "coef", "se", "ci_lo", "ci_hi"]).sort_values("lag")

plt.figure(figsize=(10, 6))
plt.axhline(0, lw=1, ls="--", color="gray", alpha=0.5)

# Plot confidence intervals first (so they appear behind the line)
has_ci = ir["ci_lo"].notna() & ir["ci_hi"].notna()
if has_ci.any():
    # Use a more visible color and higher alpha for the confidence interval
    plt.fill_between(ir.loc[has_ci, "lag"], ir.loc[has_ci, "ci_lo"], ir.loc[has_ci, "ci_hi"], 
                     alpha=0.3, color="steelblue", label="95% Confidence Interval", zorder=1)
    
    # Also plot error bars for better visibility
    ci_data = ir.loc[has_ci]
    errors_low = ci_data["coef"] - ci_data["ci_lo"]
    errors_hi = ci_data["ci_hi"] - ci_data["coef"]
    plt.errorbar(ci_data["lag"], ci_data["coef"], 
                yerr=[errors_low, errors_hi],
                fmt='none', color='darkblue', alpha=0.5, capsize=4, capthick=1.5, zorder=2)

# Plot the coefficient line and points
plt.plot(ir["lag"], ir["coef"], marker="o", markersize=8, linewidth=2, 
         color="steelblue", label="Coefficient", zorder=3)

# Mark points without SE
no_ci = ~has_ci
if no_ci.any():
    plt.plot(ir.loc[no_ci, "lag"], ir.loc[no_ci, "coef"], marker="x", markersize=10,
            linestyle="None", color="red", label="No SE available (clustering issue)", zorder=4)

plt.title("Impulse Response of MH Share to Awareness (CD Fixed Effects)", fontsize=14, fontweight="bold")
plt.xlabel("Lag (days)", fontsize=12)
plt.ylabel("Δ mh_share (per 1σ awareness)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

ir_png_path = OUTPUTS_FIGURES / "ir_mhshare_cdfe_fixed.png"
plt.savefig(ir_png_path, dpi=180, bbox_inches="tight")
ir.to_csv(OUTPUTS_TABLES / "ir_mhshare_cdfe.csv", index=False)

print(f"Saved IRF plot: {ir_png_path}")
print(f"Saved IRF data: {OUTPUTS_TABLES / 'ir_mhshare_cdfe.csv'}")
