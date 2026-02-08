"""
Step 16: Difference-in-Differences analysis with Twitter awareness data.

Treatment: High awareness days (threshold-based)
Control: Low awareness days
Shows difference in trends
Compares with distributed lag approach
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
print("DIFFERENCE-IN-DIFFERENCES ANALYSIS")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Filter to analysis period
df_analysis = df[df["incident_date"].between("2017-01-01", "2020-12-31")].copy()
print(f"Analysis period (2017-2020): {len(df_analysis):,} rows")

# ============================================================================
# Create de-meaned outcome variable
# ============================================================================
print("\n" + "=" * 80)
print("CREATING DE-MEANED OUTCOME VARIABLE")
print("=" * 80)

# Ensure dow is available
if "dow" not in df_analysis.columns:
    df_analysis["dow"] = df_analysis["incident_date"].dt.dayofweek

# Calculate mean mh_share for each weekday within each community district
cd_weekday_means = df_analysis.groupby(['communitydistrict', 'dow'])['mh_share'].mean().reset_index()
cd_weekday_means.rename(columns={'mh_share': 'mh_share_mean'}, inplace=True)

# Merge back and create de-meaned variable
df_analysis = df_analysis.merge(
    cd_weekday_means, 
    on=['communitydistrict', 'dow'], 
    how='left',
    suffixes=('', '_mean')
)
df_analysis['dm_mh_share'] = df_analysis['mh_share'] - df_analysis['mh_share_mean']

print(f"De-meaned variable created: {df_analysis['dm_mh_share'].notna().sum():,} non-null values")

# ============================================================================
# Create treatment indicators
# ============================================================================

# Treatment 1: Threshold-based (original)
threshold = 1.5  # Standard deviations
df_analysis["treated"] = (df_analysis["awareness_z"] > threshold).astype(int)

# Treatment 2: Quantile-based (top quintile)
df_analysis = df_analysis[df_analysis["awareness_z"].notna()].copy()
df_analysis['awareness_quantile'] = pd.qcut(
    df_analysis['awareness_z'], 
    q=5, 
    labels=['0-20', '20-40', '40-60', '60-80', '80-100'],
    retbins=False,
    duplicates='drop'
)
df_analysis["treated_quantile"] = (df_analysis['awareness_quantile'] == '80-100').astype(int)

print(f"\nTreatment definitions:")
print(f"  Threshold-based (>1.5 SD): {df_analysis['treated'].sum():,} treated days")
print(f"  Quantile-based (top quintile): {df_analysis['treated_quantile'].sum():,} treated days")

# Create time periods relative to treatment
# For DID, we need to identify treatment periods and pre/post periods
df_analysis = df_analysis.sort_values(["communitydistrict", "incident_date"])

# Create event time (days from treatment)
# For each treated day, mark surrounding days
df_analysis["event_time"] = np.nan

treated_dates = df_analysis[df_analysis["treated"] == 1]["incident_date"].drop_duplicates().sort_values()
print(f"\nTreatment days (>{threshold} SD): {len(treated_dates)}")

# Create windows around treatment events
for event_date in treated_dates:
    window_start = event_date - pd.Timedelta(days=14)
    window_end = event_date + pd.Timedelta(days=14)
    
    mask = (df_analysis["incident_date"] >= window_start) & (df_analysis["incident_date"] <= window_end)
    df_analysis.loc[mask, "event_time"] = (df_analysis.loc[mask, "incident_date"] - event_date).dt.days

# Prepare for regression
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

# Create pre/post indicators
df_analysis["post"] = (df_analysis["event_time"] >= 0).astype(int)
df_analysis["post"] = df_analysis["post"].fillna(0)

# Restrict to event windows
df_did = df_analysis[df_analysis["event_time"].notna()].copy()
print(f"Observations in event windows: {len(df_did):,}")

# DID Model 1: Simple 2x2 DID
print("\n" + "=" * 80)
print("DID MODEL 1: Simple 2x2 Difference-in-Differences")
print("=" * 80)

formula_did1 = "mh_share ~ treated * post + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
y, X = patsy.dmatrices(formula_did1, data=df_did, return_type="dataframe")
groups = df_did.loc[y.index, "cd_int"].to_numpy(dtype="int64")

mod_did1 = sm.OLS(y, X, missing="drop").fit(
    cov_type="cluster",
    cov_kwds={"groups": groups}
)

print(f"Observations: {int(mod_did1.nobs):,}")
print(f"R-squared: {mod_did1.rsquared:.4f}")

if "treated:post" in mod_did1.params.index:
    did_coef = mod_did1.params["treated:post"]
    did_se = mod_did1.bse["treated:post"]
    print(f"\nDID coefficient (treated × post): {did_coef:.6f} (SE: {did_se:.6f})")
    print(f"95% CI: [{did_coef - 1.96*did_se:.6f}, {did_coef + 1.96*did_se:.6f}]")

# DID Model 2: Event study (allowing for dynamic effects)
print("\n" + "=" * 80)
print("DID MODEL 2: Event Study (Dynamic Effects)")
print("=" * 80)

# Create event time dummies
event_times = sorted([t for t in df_did["event_time"].dropna().unique() if -14 <= t <= 14])
event_time_dummies = []

for t in event_times:
    if t != -1:  # Use -1 as reference period
        # Use 'm' for minus/negative to avoid patsy parsing issues
        dummy_name = f"event_time_m{abs(int(t))}" if t < 0 else f"event_time_{int(t)}"
        df_did[dummy_name] = ((df_did["event_time"] == t) & (df_did["treated"] == 1)).astype(int)
        event_time_dummies.append(dummy_name)

if event_time_dummies:
    formula_did2 = "mh_share ~ " + " + ".join(event_time_dummies) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y2, X2 = patsy.dmatrices(formula_did2, data=df_did, return_type="dataframe")
    groups2 = df_did.loc[y2.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_did2 = sm.OLS(y2, X2, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups2}
    )
    
    print(f"Observations: {int(mod_did2.nobs):,}")
    print(f"R-squared: {mod_did2.rsquared:.4f}")
    
    # Extract event time coefficients
    event_coefs = []
    for dummy in event_time_dummies:
        if dummy in mod_did2.params.index:
            # Parse event time from column name (handles both m# and # formats)
            time_str = dummy.split("_")[-1]
            if time_str.startswith("m"):
                t = -int(time_str[1:])
            else:
                t = int(time_str)
            coef = mod_did2.params[dummy]
            se = mod_did2.bse[dummy]
            event_coefs.append({
                "event_time": t,
                "coefficient": coef,
                "se": se,
                "ci_low": coef - 1.96 * se,
                "ci_hi": coef + 1.96 * se,
            })
    
    if event_coefs:
        df_event_coefs = pd.DataFrame(event_coefs).sort_values("event_time")
        print("\nEvent time coefficients:")
        print(df_event_coefs[["event_time", "coefficient", "se"]].to_string(index=False))
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(df_event_coefs["event_time"], df_event_coefs["coefficient"], 
               marker="o", linewidth=2, markersize=6, label="DID Coefficient")
        
        ax.fill_between(df_event_coefs["event_time"], 
                       df_event_coefs["ci_low"], 
                       df_event_coefs["ci_hi"],
                       alpha=0.3, label="95% Confidence Interval")
        
        ax.axvline(0, color="red", linestyle="--", linewidth=1, label="Treatment")
        ax.axhline(0, color="gray", linestyle=":", linewidth=1)
        
        ax.set_xlabel("Days from Treatment", fontsize=12)
        ax.set_ylabel("Effect on mh_share", fontsize=12)
        ax.set_title("Difference-in-Differences: Dynamic Effects of High Awareness", 
                    fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        output_path = OUTPUTS_FIGURES / "did_trends.png"
        plt.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close()
        
        print(f"\n✓ Saved DID visualization to: {output_path}")
        
        # Save event study results
        event_study_out = OUTPUTS_TABLES / "did_event_study_coefficients.csv"
        df_event_coefs.to_csv(event_study_out, index=False)
        print(f"✓ Saved event study coefficients to: {event_study_out}")

# Save DID results
did_results = []
if "treated:post" in mod_did1.params.index:
    did_results.append({
        "model": "Simple 2x2 DID",
        "coefficient": mod_did1.params["treated:post"],
        "se": mod_did1.bse["treated:post"],
        "ci_low": mod_did1.params["treated:post"] - 1.96 * mod_did1.bse["treated:post"],
        "ci_hi": mod_did1.params["treated:post"] + 1.96 * mod_did1.bse["treated:post"],
        "n_obs": int(mod_did1.nobs),
        "r_squared": mod_did1.rsquared,
    })

if did_results:
    df_did_results = pd.DataFrame(did_results)
    did_out = OUTPUTS_TABLES / "did_results.csv"
    df_did_results.to_csv(did_out, index=False)
    print(f"\n✓ Saved DID results to: {did_out}")

# ============================================================================
# DID Model 3: De-meaned outcome (threshold-based treatment)
# ============================================================================

print("\n" + "=" * 80)
print("DID MODEL 3: DE-MEANED OUTCOME (THRESHOLD-BASED TREATMENT)")
print("=" * 80)

df_did_demeaned = df_did[df_did["dm_mh_share"].notna()].copy()

if len(df_did_demeaned) > 100:
    formula_did3 = "dm_mh_share ~ treated * post + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y3, X3 = patsy.dmatrices(formula_did3, data=df_did_demeaned, return_type="dataframe")
    groups3 = df_did_demeaned.loc[y3.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_did3 = sm.OLS(y3, X3, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups3}
    )
    
    print(f"Observations: {int(mod_did3.nobs):,}")
    print(f"R-squared: {mod_did3.rsquared:.4f}")
    
    if "treated:post" in mod_did3.params.index:
        did_coef = mod_did3.params["treated:post"]
        did_se = mod_did3.bse["treated:post"]
        print(f"\nDID coefficient (treated × post): {did_coef:.6f} (SE: {did_se:.6f})")
        print(f"95% CI: [{did_coef - 1.96*did_se:.6f}, {did_coef + 1.96*did_se:.6f}]")
        
        did_results.append({
            "model": "DID with de-meaned outcome (threshold)",
            "coefficient": did_coef,
            "se": did_se,
            "ci_low": did_coef - 1.96 * did_se,
            "ci_hi": did_coef + 1.96 * did_se,
            "n_obs": int(mod_did3.nobs),
            "r_squared": mod_did3.rsquared,
        })
else:
    print("⚠️  Insufficient data for de-meaned DID analysis")

# ============================================================================
# DID Model 4: Quantile-based treatment (original outcome)
# ============================================================================

print("\n" + "=" * 80)
print("DID MODEL 4: QUANTILE-BASED TREATMENT (ORIGINAL OUTCOME)")
print("=" * 80)

# Recreate event windows for quantile-based treatment
df_analysis_quant = df_analysis.copy()
df_analysis_quant = df_analysis_quant.sort_values(["communitydistrict", "incident_date"])
df_analysis_quant["event_time_quant"] = np.nan

treated_dates_quant = df_analysis_quant[df_analysis_quant["treated_quantile"] == 1]["incident_date"].drop_duplicates().sort_values()
print(f"Treatment days (top quintile): {len(treated_dates_quant)}")

# Create windows around treatment events
for event_date in treated_dates_quant:
    window_start = event_date - pd.Timedelta(days=14)
    window_end = event_date + pd.Timedelta(days=14)
    
    mask = (df_analysis_quant["incident_date"] >= window_start) & (df_analysis_quant["incident_date"] <= window_end)
    df_analysis_quant.loc[mask, "event_time_quant"] = (df_analysis_quant.loc[mask, "incident_date"] - event_date).dt.days

df_analysis_quant["post_quant"] = (df_analysis_quant["event_time_quant"] >= 0).astype(int)
df_analysis_quant["post_quant"] = df_analysis_quant["post_quant"].fillna(0)

df_did_quant = df_analysis_quant[df_analysis_quant["event_time_quant"].notna()].copy()
print(f"Observations in event windows: {len(df_did_quant):,}")

if len(df_did_quant) > 100:
    formula_did4 = "mh_share ~ treated_quantile * post_quant + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y4, X4 = patsy.dmatrices(formula_did4, data=df_did_quant, return_type="dataframe")
    groups4 = df_did_quant.loc[y4.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_did4 = sm.OLS(y4, X4, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups4}
    )
    
    print(f"Observations: {int(mod_did4.nobs):,}")
    print(f"R-squared: {mod_did4.rsquared:.4f}")
    
    if "treated_quantile:post_quant" in mod_did4.params.index:
        did_coef = mod_did4.params["treated_quantile:post_quant"]
        did_se = mod_did4.bse["treated_quantile:post_quant"]
        print(f"\nDID coefficient (treated_quantile × post_quant): {did_coef:.6f} (SE: {did_se:.6f})")
        print(f"95% CI: [{did_coef - 1.96*did_se:.6f}, {did_coef + 1.96*did_se:.6f}]")
        
        did_results.append({
            "model": "DID with quantile-based treatment",
            "coefficient": did_coef,
            "se": did_se,
            "ci_low": did_coef - 1.96 * did_se,
            "ci_hi": did_coef + 1.96 * did_se,
            "n_obs": int(mod_did4.nobs),
            "r_squared": mod_did4.rsquared,
        })
else:
    print("⚠️  Insufficient data for quantile-based DID analysis")

# ============================================================================
# DID Model 5: De-meaned outcome + Quantile-based treatment
# ============================================================================

print("\n" + "=" * 80)
print("DID MODEL 5: DE-MEANED OUTCOME + QUANTILE-BASED TREATMENT")
print("=" * 80)

df_did_quant_demeaned = df_did_quant[df_did_quant["dm_mh_share"].notna()].copy()

if len(df_did_quant_demeaned) > 100:
    formula_did5 = "dm_mh_share ~ treated_quantile * post_quant + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y5, X5 = patsy.dmatrices(formula_did5, data=df_did_quant_demeaned, return_type="dataframe")
    groups5 = df_did_quant_demeaned.loc[y5.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_did5 = sm.OLS(y5, X5, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups5}
    )
    
    print(f"Observations: {int(mod_did5.nobs):,}")
    print(f"R-squared: {mod_did5.rsquared:.4f}")
    
    if "treated_quantile:post_quant" in mod_did5.params.index:
        did_coef = mod_did5.params["treated_quantile:post_quant"]
        did_se = mod_did5.bse["treated_quantile:post_quant"]
        print(f"\nDID coefficient (treated_quantile × post_quant): {did_coef:.6f} (SE: {did_se:.6f})")
        print(f"95% CI: [{did_coef - 1.96*did_se:.6f}, {did_coef + 1.96*did_se:.6f}]")
        
        did_results.append({
            "model": "DID with de-meaned outcome + quantile treatment",
            "coefficient": did_coef,
            "se": did_se,
            "ci_low": did_coef - 1.96 * did_se,
            "ci_hi": did_coef + 1.96 * did_se,
            "n_obs": int(mod_did5.nobs),
            "r_squared": mod_did5.rsquared,
        })
else:
    print("⚠️  Insufficient data for combined analysis")

# ============================================================================
# Save updated DID results
# ============================================================================

if did_results:
    df_did_results = pd.DataFrame(did_results)
    did_out = OUTPUTS_TABLES / "did_results.csv"
    df_did_results.to_csv(did_out, index=False)
    print(f"\n✓ Saved updated DID results to: {did_out}")
    
    print("\n" + "=" * 80)
    print("DID RESULTS COMPARISON")
    print("=" * 80)
    print(df_did_results[["model", "coefficient", "se", "n_obs", "r_squared"]].to_string(index=False))

# Compare with distributed lag approach
print("\n" + "=" * 80)
print("COMPARISON: DID vs Distributed Lag")
print("=" * 80)

# Run distributed lag model for comparison
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use if f"awarez_lag{k}" in df_analysis.columns]

if lag_cols:
    formula_dl = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y_dl, X_dl = patsy.dmatrices(formula_dl, data=df_analysis, return_type="dataframe")
    groups_dl = df_analysis.loc[y_dl.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_dl = sm.OLS(y_dl, X_dl, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups_dl}
    )
    
    print(f"\nDistributed Lag Model:")
    print(f"  Observations: {int(mod_dl.nobs):,}")
    print(f"  R-squared: {mod_dl.rsquared:.4f}")
    
    if "awarez_lag7" in mod_dl.params.index:
        dl_coef = mod_dl.params["awarez_lag7"]
        dl_se = mod_dl.bse["awarez_lag7"]
        print(f"  Lag 7 coefficient: {dl_coef:.6f} (SE: {dl_se:.6f})")
    
    print(f"\nDID Model:")
    if did_results:
        print(f"  DID coefficient: {did_results[0]['coefficient']:.6f} (SE: {did_results[0]['se']:.6f})")
        print(f"  Observations: {did_results[0]['n_obs']:,}")
        print(f"  R-squared: {did_results[0]['r_squared']:.4f}")

print("\n" + "=" * 80)
print("DIFFERENCE-IN-DIFFERENCES ANALYSIS COMPLETE")
print("=" * 80)

