"""
Step 26: Synthesize All Results for Research Paper

This script loads all result tables, verifies completeness, and creates
comprehensive summary statistics for inclusion in the research paper.
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("SYNTHESIZING ALL RESULTS FOR RESEARCH PAPER")
print("=" * 80)

# Load panel for summary statistics
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel = pd.read_parquet(panel_path)
df_panel["incident_date"] = pd.to_datetime(df_panel["incident_date"])

print(f"\nPanel data: {len(df_panel):,} rows")
print(f"Date range: {df_panel['incident_date'].min()} to {df_panel['incident_date'].max()}")
print(f"Community districts: {df_panel['communitydistrict'].nunique()}")

# Filter to analysis sample
df_analysis = df_panel[(df_panel["total_calls"] >= 5) & df_panel["mh_share"].notna()].copy()
print(f"Analysis sample: {len(df_analysis):,} rows")

# ============================================================================
# 1. Main Regression Results
# ============================================================================

print("\n" + "=" * 80)
print("1. MAIN REGRESSION RESULTS")
print("=" * 80)

main_results = {}

# Load main distributed lag model
dl_params_path = OUTPUTS_TABLES / "dl_model_params_with_cdfe.csv"
if dl_params_path.exists():
    dl_params = pd.read_csv(dl_params_path, index_col=0)
    
    # Extract key lags
    for lag in [0, 1, 2, 3, 7, 14, 21, 28]:
        lag_col = f"awarez_lag{lag}"
        if lag_col in dl_params.index:
            coef = dl_params.loc[lag_col, "coef"]
            se = dl_params.loc[lag_col, "se"]
            main_results[lag] = {
                "coefficient": coef,
                "se": se,
                "ci_low": coef - 1.96 * se,
                "ci_hi": coef + 1.96 * se
            }
            print(f"  Lag {lag}: {coef:.6f} (SE: {se:.6f})")
    
    print(f"✓ Main regression results loaded")

# ============================================================================
# 2. Progressive Regression Comparison
# ============================================================================

print("\n" + "=" * 80)
print("2. PROGRESSIVE REGRESSION COMPARISON")
print("=" * 80)

progressive_path = OUTPUTS_TABLES / "regression_progressive_lag7_comparison.csv"
if progressive_path.exists():
    progressive = pd.read_csv(progressive_path)
    print(progressive.to_string(index=False))
    print(f"✓ Progressive regression results loaded")
else:
    print("⚠️  Progressive regression file not found")

# ============================================================================
# 3. Heterogeneous Effects
# ============================================================================

print("\n" + "=" * 80)
print("3. HETEROGENEOUS EFFECTS")
print("=" * 80)

hetero_strat_path = OUTPUTS_TABLES / "heterogeneous_effects_stratified.csv"
if hetero_strat_path.exists():
    hetero_strat = pd.read_csv(hetero_strat_path)
    print("\nStratified analysis by demographics:")
    print(hetero_strat.to_string(index=False))
    print(f"✓ Heterogeneous effects loaded")
else:
    print("⚠️  Heterogeneous effects file not found")

# ============================================================================
# 4. DID Results
# ============================================================================

print("\n" + "=" * 80)
print("4. DIFFERENCE-IN-DIFFERENCES RESULTS")
print("=" * 80)

did_path = OUTPUTS_TABLES / "did_results.csv"
if did_path.exists():
    did_results = pd.read_csv(did_path)
    print("\nDID models:")
    print(did_results.to_string(index=False))
    print(f"✓ DID results loaded ({len(did_results)} models)")
else:
    print("⚠️  DID results file not found")

# ============================================================================
# 5. De-meaning Analysis
# ============================================================================

print("\n" + "=" * 80)
print("5. DE-MEANING ANALYSIS")
print("=" * 80)

demeaned_path = OUTPUTS_TABLES / "demeaned_regression_comparison.csv"
if demeaned_path.exists():
    demeaned = pd.read_csv(demeaned_path)
    print("\nBaseline vs. De-meaned comparison:")
    print(demeaned.to_string(index=False))
    print(f"✓ De-meaning results loaded")
else:
    print("⚠️  De-meaning results file not found")

# ============================================================================
# 6. Quantile Analysis
# ============================================================================

print("\n" + "=" * 80)
print("6. QUANTILE ANALYSIS")
print("=" * 80)

quantile_path = OUTPUTS_TABLES / "quantile_analysis_regression_results.csv"
if quantile_path.exists():
    quantile = pd.read_csv(quantile_path)
    print("\nQuantile-specific lag 7 coefficients:")
    print(quantile[["quantile", "lag7_coef", "lag7_se", "n_obs"]].to_string(index=False))
    print(f"✓ Quantile analysis loaded")
else:
    print("⚠️  Quantile analysis file not found")

# ============================================================================
# 7. Forward Lag Analysis
# ============================================================================

print("\n" + "=" * 80)
print("7. FORWARD LAG ANALYSIS")
print("=" * 80)

forward_path = OUTPUTS_TABLES / "forward_lag_results.csv"
if forward_path.exists():
    forward = pd.read_csv(forward_path)
    print("\nForward lag coefficients:")
    print(forward[["forward_lag", "awareness_coef", "awareness_se", "n_obs"]].to_string(index=False))
    print(f"✓ Forward lag results loaded")
else:
    print("⚠️  Forward lag results file not found")

# ============================================================================
# 8. Two-Way Fixed Effects
# ============================================================================

print("\n" + "=" * 80)
print("8. TWO-WAY FIXED EFFECTS")
print("=" * 80)

twoway_path = OUTPUTS_TABLES / "twoway_fe_results.csv"
if twoway_path.exists():
    twoway = pd.read_csv(twoway_path)
    print("\nTwo-way FE comparison:")
    print(twoway[twoway["lag"] == 7][["model", "coef", "se", "r_squared"]].to_string(index=False))
    print(f"✓ Two-way FE results loaded")
else:
    print("⚠️  Two-way FE results file not found")

# ============================================================================
# 9. Summary Statistics
# ============================================================================

print("\n" + "=" * 80)
print("9. SUMMARY STATISTICS")
print("=" * 80)

summary_stats = {
    "Variable": [],
    "Mean": [],
    "Std": [],
    "Min": [],
    "Max": [],
    "N": []
}

# Key variables
for var in ["mh_share", "mh_calls", "total_calls", "awareness_z"]:
    if var in df_analysis.columns:
        data = df_analysis[var].dropna()
        summary_stats["Variable"].append(var)
        summary_stats["Mean"].append(data.mean())
        summary_stats["Std"].append(data.std())
        summary_stats["Min"].append(data.min())
        summary_stats["Max"].append(data.max())
        summary_stats["N"].append(len(data))

df_summary = pd.DataFrame(summary_stats)
print("\nSummary statistics:")
print(df_summary.to_string(index=False))

# Save summary
summary_out = OUTPUTS_TABLES / "research_paper_summary_statistics.csv"
df_summary.to_csv(summary_out, index=False)
print(f"\n✓ Saved summary statistics to: {summary_out}")

# ============================================================================
# 10. Key Findings Summary
# ============================================================================

print("\n" + "=" * 80)
print("10. KEY FINDINGS SUMMARY")
print("=" * 80)

key_findings = []

# Main finding
if 7 in main_results:
    kf = main_results[7]
    key_findings.append({
        "Finding": "Main Effect: Lag 7",
        "Coefficient": kf["coefficient"],
        "SE": kf["se"],
        "CI_Low": kf["ci_low"],
        "CI_Hi": kf["ci_hi"],
        "Significant": "Yes" if abs(kf["coefficient"] / kf["se"]) > 1.96 else "No"
    })

# Cumulative effect
cumulative_path = OUTPUTS_TABLES / "demeaned_cumulative_effects.csv"
if cumulative_path.exists():
    cum_effects = pd.read_csv(cumulative_path)
    baseline_cum = cum_effects[cum_effects["model"] == "baseline"]
    if len(baseline_cum) > 0:
        cum_coef = baseline_cum.iloc[0]["cumulative_coef"]
        cum_se = baseline_cum.iloc[0]["cumulative_se"]
        key_findings.append({
            "Finding": "Cumulative Effect (0-7 days)",
            "Coefficient": cum_coef,
            "SE": cum_se,
            "CI_Low": cum_coef - 1.96 * cum_se,
            "CI_Hi": cum_coef + 1.96 * cum_se,
            "Significant": "Yes" if abs(cum_coef / cum_se) > 1.96 else "No"
        })

# Heterogeneous effects
if hetero_strat_path.exists():
    hetero_strat = pd.read_csv(hetero_strat_path)
    # Get strongest effects
    for demo in ["pct_black", "pct_white"]:
        demo_data = hetero_strat[hetero_strat["demographic"] == demo]
        if len(demo_data) > 0:
            # Q1 for black, Q4 for white
            quartile = "Q1" if demo == "pct_black" else "Q4"
            q_data = demo_data[demo_data["quartile"] == quartile]
            if len(q_data) > 0:
                key_findings.append({
                    "Finding": f"Heterogeneous: {demo} {quartile}",
                    "Coefficient": q_data.iloc[0]["lag7_coef"],
                    "SE": q_data.iloc[0]["lag7_se"],
                    "CI_Low": q_data.iloc[0]["lag7_ci_low"],
                    "CI_Hi": q_data.iloc[0]["lag7_ci_hi"],
                    "Significant": "Yes" if abs(q_data.iloc[0]["lag7_coef"] / q_data.iloc[0]["lag7_se"]) > 1.96 else "No"
                })

# DID
if did_path.exists():
    did_results = pd.read_csv(did_path)
    simple_did = did_results[did_results["model"] == "Simple 2x2 DID"]
    if len(simple_did) > 0:
        key_findings.append({
            "Finding": "DID: Simple 2x2",
            "Coefficient": simple_did.iloc[0]["coefficient"],
            "SE": simple_did.iloc[0].get("se", np.nan),
            "CI_Low": simple_did.iloc[0].get("ci_low", np.nan),
            "CI_Hi": simple_did.iloc[0].get("ci_hi", np.nan),
            "Significant": "Yes" if not pd.isna(simple_did.iloc[0].get("se", np.nan)) and abs(simple_did.iloc[0]["coefficient"] / simple_did.iloc[0]["se"]) > 1.96 else "No"
        })

if key_findings:
    df_key_findings = pd.DataFrame(key_findings)
    print("\nKey findings summary:")
    print(df_key_findings.to_string(index=False))
    
    key_findings_out = OUTPUTS_TABLES / "research_paper_key_findings.csv"
    df_key_findings.to_csv(key_findings_out, index=False)
    print(f"\n✓ Saved key findings to: {key_findings_out}")

# ============================================================================
# 11. Data Completeness Check
# ============================================================================

print("\n" + "=" * 80)
print("11. DATA COMPLETENESS CHECK")
print("=" * 80)

required_files = [
    "dl_model_params_with_cdfe.csv",
    "regression_progressive_lag7_comparison.csv",
    "heterogeneous_effects_stratified.csv",
    "did_results.csv",
    "demeaned_regression_comparison.csv",
    "quantile_analysis_regression_results.csv",
    "forward_lag_results.csv",
    "twoway_fe_results.csv"
]

missing_files = []
for file in required_files:
    if not (OUTPUTS_TABLES / file).exists():
        missing_files.append(file)

if missing_files:
    print(f"⚠️  Missing files: {missing_files}")
else:
    print("✓ All required result files present")

# Check for figures
required_figures = [
    "ir_mhshare_cdfe_fixed.png",
    "progressive_regression_robustness.png",
    "heterogeneous_effects_pct_black.png",
    "heterogeneous_effects_pct_hispanic.png",
    "heterogeneous_effects_pct_white.png",
    "heterogeneous_effects_pct_asian.png",
    "did_trends.png",
    "forward_lag_coefficients.png",
    "quantile_boxplots.png"
]

OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
missing_figures = []
for fig in required_figures:
    if not (OUTPUTS_FIGURES / fig).exists():
        missing_figures.append(fig)

if missing_figures:
    print(f"⚠️  Missing figures: {missing_figures}")
else:
    print("✓ All required figures present")

print("\n" + "=" * 80)
print("SYNTHESIS COMPLETE")
print("=" * 80)
