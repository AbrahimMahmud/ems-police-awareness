"""
Step 17: Compare trend-based (distributed lag) vs threshold-based (DID) approaches.

Creates side-by-side comparison of results and visualizations.
"""

import pandas as pd
import numpy as np
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
print("TREND VS THRESHOLD COMPARISON")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

# Filter to analysis period
df_analysis = df[df["incident_date"].between("2017-01-01", "2020-12-31")].copy()
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

# Approach 1: Distributed Lag (Trend-based)
print("\n" + "=" * 80)
print("APPROACH 1: DISTRIBUTED LAG (TREND-BASED)")
print("=" * 80)

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use if f"awarez_lag{k}" in df_analysis.columns]

df_dl = df_analysis[(df_analysis["total_calls"] >= 5) & df_analysis["mh_share"].notna()].copy()
df_dl = df_dl.loc[df_dl[lag_cols].notna().any(axis=1)].copy()

formula_dl = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
mod_dl = run_model(formula_dl, df_dl, "Distributed Lag")

print(f"Observations: {int(mod_dl.nobs):,}")
print(f"R-squared: {mod_dl.rsquared:.4f}")

# Extract lag coefficients
dl_results = []
for lag in lag_use:
    lag_col = f"awarez_lag{lag}"
    if lag_col in mod_dl.params.index:
        coef = mod_dl.params[lag_col]
        se = mod_dl.bse[lag_col]
        dl_results.append({
            "approach": "Distributed Lag",
            "lag": lag,
            "coefficient": coef,
            "se": se,
            "ci_low": coef - 1.96 * se,
            "ci_hi": coef + 1.96 * se,
        })

df_dl_results = pd.DataFrame(dl_results)

# Approach 2: Threshold-based (DID)
print("\n" + "=" * 80)
print("APPROACH 2: THRESHOLD-BASED (DID)")
print("=" * 80)

threshold = 1.5
df_analysis["treated"] = (df_analysis["awareness_z"] > threshold).astype(int)

# Create event time windows
df_analysis = df_analysis.sort_values(["communitydistrict", "incident_date"])
df_analysis["event_time"] = np.nan

treated_dates = df_analysis[df_analysis["treated"] == 1]["incident_date"].drop_duplicates().sort_values()

for event_date in treated_dates:
    window_start = event_date - pd.Timedelta(days=14)
    window_end = event_date + pd.Timedelta(days=14)
    mask = (df_analysis["incident_date"] >= window_start) & (df_analysis["incident_date"] <= window_end)
    df_analysis.loc[mask, "event_time"] = (df_analysis.loc[mask, "incident_date"] - event_date).dt.days

df_did = df_analysis[df_analysis["event_time"].notna()].copy()
df_did = df_did[(df_did["total_calls"] >= 5) & df_did["mh_share"].notna()].copy()

# Create event time dummies
event_times = sorted([t for t in df_did["event_time"].dropna().unique() if -14 <= t <= 14])
event_time_dummies = []

for t in event_times:
    if t != -1:
        # Use 'm' for minus/negative to avoid patsy parsing issues
        dummy_name = f"event_time_m{abs(int(t))}" if t < 0 else f"event_time_{int(t)}"
        df_did[dummy_name] = ((df_did["event_time"] == t) & (df_did["treated"] == 1)).astype(int)
        event_time_dummies.append(dummy_name)

if event_time_dummies:
    formula_did = "mh_share ~ " + " + ".join(event_time_dummies) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    mod_did = run_model(formula_did, df_did, "DID")
    
    print(f"Observations: {int(mod_did.nobs):,}")
    print(f"R-squared: {mod_did.rsquared:.4f}")
    
    # Extract event time coefficients
    did_results = []
    for dummy in event_time_dummies:
        if dummy in mod_did.params.index:
            # Parse event time from column name (handles both m# and # formats)
            time_str = dummy.split("_")[-1]
            if time_str.startswith("m"):
                t = -int(time_str[1:])
            else:
                t = int(time_str)
            coef = mod_did.params[dummy]
            se = mod_did.bse[dummy]
            did_results.append({
                "approach": "Threshold (DID)",
                "lag": t,  # Using "lag" for consistency, but this is event time
                "coefficient": coef,
                "se": se,
                "ci_low": coef - 1.96 * se,
                "ci_hi": coef + 1.96 * se,
            })
    
    df_did_results = pd.DataFrame(did_results)
else:
    df_did_results = pd.DataFrame()

# Combine results
comparison_results = []

# Add distributed lag results
for _, row in df_dl_results.iterrows():
    comparison_results.append({
        "approach": "Distributed Lag",
        "time_period": row["lag"],
        "coefficient": row["coefficient"],
        "se": row["se"],
        "ci_low": row["ci_low"],
        "ci_hi": row["ci_hi"],
    })

# Add DID results
for _, row in df_did_results.iterrows():
    comparison_results.append({
        "approach": "Threshold (DID)",
        "time_period": row["lag"],
        "coefficient": row["coefficient"],
        "se": row["se"],
        "ci_low": row["ci_low"],
        "ci_hi": row["ci_hi"],
    })

df_comparison = pd.DataFrame(comparison_results)

# Save comparison
comparison_out = OUTPUTS_TABLES / "trend_vs_threshold_comparison.csv"
df_comparison.to_csv(comparison_out, index=False)
print(f"\n✓ Saved comparison to: {comparison_out}")

# Create visualization
if len(df_dl_results) > 0 and len(df_did_results) > 0:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Distributed Lag
    ax1.plot(df_dl_results["lag"], df_dl_results["coefficient"], 
            marker="o", linewidth=2, markersize=6, label="Coefficient")
    ax1.fill_between(df_dl_results["lag"], 
                    df_dl_results["ci_low"], 
                    df_dl_results["ci_hi"],
                    alpha=0.3, label="95% CI")
    ax1.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax1.set_xlabel("Lag (days)", fontsize=12)
    ax1.set_ylabel("Effect on mh_share", fontsize=12)
    ax1.set_title("Distributed Lag Approach", fontsize=14, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # DID
    ax2.plot(df_did_results["lag"], df_did_results["coefficient"], 
            marker="o", linewidth=2, markersize=6, label="Coefficient", color="orange")
    ax2.fill_between(df_did_results["lag"], 
                    df_did_results["ci_low"], 
                    df_did_results["ci_hi"],
                    alpha=0.3, label="95% CI")
    ax2.axvline(0, color="red", linestyle="--", linewidth=1, label="Treatment")
    ax2.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax2.set_xlabel("Days from Treatment", fontsize=12)
    ax2.set_ylabel("Effect on mh_share", fontsize=12)
    ax2.set_title("Threshold (DID) Approach", fontsize=14, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.suptitle("Comparison: Distributed Lag vs Threshold (DID) Approaches", 
                fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    
    output_path = OUTPUTS_FIGURES / "trend_vs_threshold_comparison.png"
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()
    
    print(f"✓ Saved comparison visualization to: {output_path}")

# Summary statistics
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

print("\nDistributed Lag Approach:")
print(f"  Observations: {int(mod_dl.nobs):,}")
print(f"  R-squared: {mod_dl.rsquared:.4f}")
if len(df_dl_results) > 0:
    print(f"  Key lags:")
    key_lags = [0, 1, 2, 3, 7, 14]
    for lag in key_lags:
        row = df_dl_results[df_dl_results["lag"] == lag]
        if len(row) > 0:
            print(f"    Lag {lag}: {row.iloc[0]['coefficient']:.6f} (SE: {row.iloc[0]['se']:.6f})")

if len(df_did_results) > 0:
    print("\nThreshold (DID) Approach:")
    print(f"  Observations: {int(mod_did.nobs):,}")
    print(f"  R-squared: {mod_did.rsquared:.4f}")
    print(f"  Treatment threshold: {threshold} SD")
    print(f"  Key periods:")
    key_periods = [-7, -3, 0, 3, 7, 14]
    for period in key_periods:
        row = df_did_results[df_did_results["lag"] == period]
        if len(row) > 0:
            print(f"    Day {period}: {row.iloc[0]['coefficient']:.6f} (SE: {row.iloc[0]['se']:.6f})")

print("\n" + "=" * 80)
print("TREND VS THRESHOLD COMPARISON COMPLETE")
print("=" * 80)

