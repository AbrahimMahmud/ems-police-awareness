"""
Diagnostic script to identify issues with the analysis.

This script checks:
1. Awareness data variation
2. Lag variable creation
3. Model specification issues
4. Data quality problems
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

print("=" * 80)
print("DIAGNOSTIC ANALYSIS")
print("=" * 80)

# Load the merged panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
if not panel_path.exists():
    print(f"ERROR: Panel not found: {panel_path}")
    print("Run scripts 01 and 02 first.")
    exit(1)

df = pd.read_parquet(panel_path)
print(f"\nPanel shape: {df.shape}")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Check awareness data
print("\n" + "=" * 80)
print("1. AWARENESS DATA CHECK")
print("=" * 80)

print(f"\nAwareness_z statistics:")
print(f"  Non-null values: {df['awareness_z'].notna().sum():,} / {len(df):,}")
print(f"  Mean: {df['awareness_z'].mean():.6f}")
print(f"  Std: {df['awareness_z'].std():.6f}")
print(f"  Min: {df['awareness_z'].min():.6f}")
print(f"  Max: {df['awareness_z'].max():.6f}")

# Check for variation
if df['awareness_z'].std() < 0.01:
    print("  ⚠️  WARNING: Very low variation in awareness_z!")
else:
    print("  ✓ Awareness has sufficient variation")

# Check lag variables
print("\n" + "=" * 80)
print("2. LAG VARIABLES CHECK")
print("=" * 80)

lag_cols = [f"awarez_lag{k}" for k in [0, 1, 2, 3, 7, 14, 21, 28]]
for lag_col in lag_cols:
    if lag_col in df.columns:
        non_null = df[lag_col].notna().sum()
        mean_val = df[lag_col].mean()
        std_val = df[lag_col].std()
        print(f"\n{lag_col}:")
        print(f"  Non-null: {non_null:,} ({100*non_null/len(df):.1f}%)")
        print(f"  Mean: {mean_val:.6f}")
        print(f"  Std: {std_val:.6f}")
        if std_val < 0.01:
            print(f"  ⚠️  WARNING: Very low variation!")
    else:
        print(f"\n{lag_col}: MISSING")

# Check for perfect correlation between lags
print("\n" + "=" * 80)
print("3. MULTICOLLINEARITY CHECK")
print("=" * 80)

lag_data = df[lag_cols].dropna()
if len(lag_data) > 0:
    corr_matrix = lag_data.corr()
    print("\nCorrelation matrix for lag variables:")
    print(corr_matrix.round(3))
    
    # Check for perfect correlation
    high_corr = (corr_matrix.abs() > 0.99) & (corr_matrix != 1.0)
    if high_corr.any().any():
        print("\n⚠️  WARNING: Very high correlations detected (potential multicollinearity):")
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                if abs(corr_matrix.iloc[i, j]) > 0.99:
                    print(f"  {corr_matrix.index[i]} <-> {corr_matrix.columns[j]}: {corr_matrix.iloc[i, j]:.3f}")
    else:
        print("\n✓ No perfect correlations detected")
else:
    print("⚠️  No data available for correlation check (all missing)")

# Check model sample
print("\n" + "=" * 80)
print("4. MODEL SAMPLE CHECK")
print("=" * 80)

df_model = df[df["total_calls"] >= 5].copy()
df_model = df_model.dropna(subset=["mh_share", "communitydistrict"])
df_model = df_model.loc[df_model[lag_cols].notna().any(axis=1)].copy()

print(f"\nSample for regression:")
print(f"  Total rows: {len(df_model):,}")
print(f"  Community districts: {df_model['communitydistrict'].nunique()}")
print(f"  Date range: {df_model['incident_date'].min()} to {df_model['incident_date'].max()}")

# Check how many rows have each lag
print(f"\nRows with each lag variable:")
for lag_col in lag_cols:
    if lag_col in df_model.columns:
        count = df_model[lag_col].notna().sum()
        print(f"  {lag_col}: {count:,} ({100*count/len(df_model):.1f}%)")

# Check COVID phase
print("\n" + "=" * 80)
print("5. COVID PHASE CHECK")
print("=" * 80)

print(f"\nCOVID phase distribution:")
print(df_model['covid_phase'].value_counts().sort_index())

# Check if COVID phase is causing issues
covid_phase_counts = df_model['covid_phase'].value_counts()
if (covid_phase_counts < 100).any():
    print("\n⚠️  WARNING: Some COVID phases have very few observations")
    print("  This could cause numerical issues in regression")

# Check outcome variable
print("\n" + "=" * 80)
print("6. OUTCOME VARIABLE CHECK")
print("=" * 80)

print(f"\nmh_share statistics:")
print(f"  Mean: {df_model['mh_share'].mean():.6f}")
print(f"  Std: {df_model['mh_share'].std():.6f}")
print(f"  Min: {df_model['mh_share'].min():.6f}")
print(f"  Max: {df_model['mh_share'].max():.6f}")

# Check for variation in outcomes
if df_model['mh_share'].std() < 0.01:
    print("  ⚠️  WARNING: Very low variation in mh_share!")
else:
    print("  ✓ Outcome has sufficient variation")

# Check awareness spikes
print("\n" + "=" * 80)
print("7. AWARENESS SPIKES CHECK")
print("=" * 80)

# Find days with high awareness
high_awareness = df[df['awareness_z'] > 2].copy()  # > 2 standard deviations
print(f"\nDays with awareness_z > 2 SD: {len(high_awareness):,}")
if len(high_awareness) > 0:
    print(f"  Date range: {high_awareness['incident_date'].min()} to {high_awareness['incident_date'].max()}")
    print(f"  Max awareness_z: {high_awareness['awareness_z'].max():.2f}")
    print(f"\nTop 10 awareness spikes:")
    top_spikes = df.nlargest(10, 'awareness_z')[['incident_date', 'awareness_z', 'tweet_count_all']]
    print(top_spikes.to_string(index=False))
else:
    print("  ⚠️  WARNING: No high awareness days found!")
    print("  This could explain why effects are small/flat")

# Summary
print("\n" + "=" * 80)
print("SUMMARY OF POTENTIAL ISSUES")
print("=" * 80)

issues = []

if df['awareness_z'].std() < 0.1:
    issues.append("Low variation in awareness measure")
    
if df_model['mh_share'].std() < 0.01:
    issues.append("Low variation in outcome variable")

if len(high_awareness) < 10:
    issues.append("Very few high-awareness days (spikes)")

if (covid_phase_counts < 100).any():
    issues.append("Some COVID phases have very few observations")

if len(lag_data) == 0:
    issues.append("All lag variables are missing")

if len(issues) == 0:
    print("\n✓ No obvious data quality issues detected")
    print("\nPossible reasons for flat IRF:")
    print("  1. True effect is very small (coefficients are ~0.0005-0.001)")
    print("  2. Standard errors not calculated properly (model specification issue)")
    print("  3. Need to check if model is converging properly")
else:
    print("\n⚠️  Issues detected:")
    for issue in issues:
        print(f"  - {issue}")

print("\n" + "=" * 80)

