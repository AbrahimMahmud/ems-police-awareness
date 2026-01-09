"""
Step 5: Create comprehensive descriptive statistics table.

This script creates descriptive statistics for all variables used in regression:
- Outcome variables: mh_share, mh_calls, total_calls, log_mh_calls_3day_rolling
- Independent variables: awarez_lag* (all lags)
- Controls: dow, month, year, is_holiday
- Demographics: pct_white, pct_black, pct_hispanic, pct_asian, median_income, etc.
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("DESCRIPTIVE STATISTICS FOR ALL REGRESSION VARIABLES")
print("=" * 80)

# Load merged panel directly (more memory efficient)
panel_path = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
if not panel_path.exists():
    # Fallback to panel without demographics
    panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
    if not panel_path.exists():
        raise FileNotFoundError(f"Panel not found: {panel_path}")

print(f"\nLoading panel from: {panel_path.name}")
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"Loaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Filter to analysis sample (same as regression)
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
print(f"Analysis sample: {len(df_analysis):,} rows")

# For memory efficiency, work with a sample if dataset is very large
if len(df_analysis) > 300000:
    print(f"  Large dataset detected, using sample for efficiency...")
    df_analysis = df_analysis.sample(n=min(300000, len(df_analysis)), random_state=42)
    print(f"  Working with sample of {len(df_analysis):,} rows")

# Define variables for descriptive statistics
outcome_vars = ["mh_share", "mh_calls", "total_calls"]
if "log_mh_calls_3day_rolling" in df_analysis.columns:
    outcome_vars.append("log_mh_calls_3day_rolling")

lag_vars = [f"awarez_lag{k}" for k in range(0, 29) if f"awarez_lag{k}" in df_analysis.columns]

control_vars = ["dow", "month", "year", "is_holiday"]
if "covid_phase" in df_analysis.columns:
    control_vars.append("covid_phase")

# Demographic variables (check what's available)
demo_vars = []
potential_demo_vars = [
    "pct_white", "pct_black", "pct_hispanic", "pct_asian",
    "median_income", "pct_college", "pct_poverty", "pct_owner_occupied",
    "pct_over_65", "pct_health_insurance", "median_age"
]
for var in potential_demo_vars:
    if var in df_analysis.columns:
        demo_vars.append(var)

all_vars = outcome_vars + lag_vars + control_vars + demo_vars

# Compute descriptive statistics
descriptive_stats = []

for var in all_vars:
    if var not in df_analysis.columns:
        continue
    
    data = df_analysis[var].dropna()
    
    if len(data) == 0:
        continue
    
    stats = {
        "variable": var,
        "variable_type": "outcome" if var in outcome_vars else 
                        "independent" if var in lag_vars else
                        "control" if var in control_vars else
                        "demographic",
        "n": len(data),
        "n_missing": len(df_analysis) - len(data),
        "pct_missing": (len(df_analysis) - len(data)) / len(df_analysis) * 100,
    }
    
    if pd.api.types.is_numeric_dtype(data):
        stats.update({
            "mean": float(data.mean()),
            "std": float(data.std()),
            "min": float(data.min()),
            "p25": float(data.quantile(0.25)),
            "median": float(data.median()),
            "p75": float(data.quantile(0.75)),
            "max": float(data.max()),
        })
    else:
        # For categorical variables, show unique values and counts
        unique_vals = data.value_counts()
        stats.update({
            "n_unique": len(unique_vals),
            "most_common": str(unique_vals.index[0]) if len(unique_vals) > 0 else None,
            "most_common_count": int(unique_vals.iloc[0]) if len(unique_vals) > 0 else None,
        })
    
    descriptive_stats.append(stats)

df_desc = pd.DataFrame(descriptive_stats)

# Save results
output_path = OUTPUTS_TABLES / "descriptive_stats_all_variables.csv"
df_desc.to_csv(output_path, index=False)
print(f"\n✓ Saved descriptive statistics to: {output_path}")

# Print summary
print("\n" + "=" * 80)
print("DESCRIPTIVE STATISTICS SUMMARY")
print("=" * 80)

print(f"\nOutcome Variables ({len([v for v in outcome_vars if v in df_analysis.columns])}):")
outcome_df = df_desc[df_desc["variable_type"] == "outcome"]
if len(outcome_df) > 0:
    print(outcome_df[["variable", "n", "mean", "std", "min", "median", "max"]].to_string(index=False))

print(f"\nIndependent Variables - Awareness Lags ({len(lag_vars)}):")
lag_df = df_desc[df_desc["variable_type"] == "independent"]
if len(lag_df) > 0:
    print(lag_df[["variable", "n", "mean", "std", "min", "median", "max"]].head(10).to_string(index=False))
    if len(lag_df) > 10:
        print(f"... and {len(lag_df) - 10} more lag variables")

print(f"\nControl Variables ({len([v for v in control_vars if v in df_analysis.columns])}):")
control_df = df_desc[df_desc["variable_type"] == "control"]
if len(control_df) > 0:
    print(control_df[["variable", "n", "n_unique" if "n_unique" in control_df.columns else "mean", 
                      "most_common" if "most_common" in control_df.columns else "std"]].to_string(index=False))

print(f"\nDemographic Variables ({len(demo_vars)}):")
demo_df = df_desc[df_desc["variable_type"] == "demographic"]
if len(demo_df) > 0:
    print(demo_df[["variable", "n", "mean", "std", "min", "median", "max"]].to_string(index=False))
else:
    print("  (No demographic variables found - run demographics merge script first)")

print("\n" + "=" * 80)
print("DESCRIPTIVE STATISTICS COMPLETE")
print("=" * 80)

