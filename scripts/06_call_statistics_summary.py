"""
Step 6: Create summary statistics for EMS calls.

This script creates comprehensive summary tables showing:
- Total number of calls (by CD, by date, overall)
- Share that are mental health calls
- Trends over time
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CALL STATISTICS SUMMARY")
print("=" * 80)

# Load panel data
panel_path = DATA_PROCESSED / "panel_cd_day.parquet"
if not panel_path.exists():
    raise FileNotFoundError(f"Panel data not found: {panel_path}")

df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")
print(f"Community districts: {df['communitydistrict'].nunique()}")

# Overall statistics
overall_stats = {
    "total_observations": len(df),
    "total_calls_sum": int(df["total_calls"].sum()),
    "total_mh_calls_sum": int(df["mh_calls"].sum()),
    "overall_mh_share": df["mh_calls"].sum() / df["total_calls"].sum() if df["total_calls"].sum() > 0 else np.nan,
    "mean_total_calls_per_day": df["total_calls"].mean(),
    "mean_mh_calls_per_day": df["mh_calls"].mean(),
    "mean_mh_share": df["mh_share"].mean(),
    "median_total_calls_per_day": df["total_calls"].median(),
    "median_mh_calls_per_day": df["mh_calls"].median(),
    "median_mh_share": df["mh_share"].median(),
}

# By community district
cd_stats = df.groupby("communitydistrict").agg({
    "total_calls": ["sum", "mean", "median", "std"],
    "mh_calls": ["sum", "mean", "median", "std"],
    "mh_share": ["mean", "median", "std"],
    "incident_date": ["min", "max", "count"]
}).reset_index()

cd_stats.columns = ["communitydistrict", 
                   "total_calls_sum", "total_calls_mean", "total_calls_median", "total_calls_std",
                   "mh_calls_sum", "mh_calls_mean", "mh_calls_median", "mh_calls_std",
                   "mh_share_mean", "mh_share_median", "mh_share_std",
                   "date_min", "date_max", "n_days"]

cd_stats["mh_share_overall"] = cd_stats["mh_calls_sum"] / cd_stats["total_calls_sum"]

# By date (citywide)
date_stats = df.groupby("incident_date").agg({
    "total_calls": "sum",
    "mh_calls": "sum",
    "communitydistrict": "nunique"
}).reset_index()

date_stats["mh_share"] = date_stats["mh_calls"] / date_stats["total_calls"]
date_stats["year"] = date_stats["incident_date"].dt.year
date_stats["month"] = date_stats["incident_date"].dt.month

# By year
year_stats = date_stats.groupby("year").agg({
    "total_calls": ["sum", "mean", "median"],
    "mh_calls": ["sum", "mean", "median"],
    "mh_share": ["mean", "median"],
    "incident_date": "count"
}).reset_index()

year_stats.columns = ["year", "total_calls_sum", "total_calls_mean", "total_calls_median",
                     "mh_calls_sum", "mh_calls_mean", "mh_calls_median",
                     "mh_share_mean", "mh_share_median", "n_days"]

year_stats["mh_share_overall"] = year_stats["mh_calls_sum"] / year_stats["total_calls_sum"]

# Save results
output_path = OUTPUTS_TABLES / "call_statistics_summary.csv"

# Combine all statistics into a structured format
summary_data = []

# Overall
summary_data.append({
    "level": "overall",
    "group": "all",
    "total_calls": overall_stats["total_calls_sum"],
    "mh_calls": overall_stats["total_mh_calls_sum"],
    "mh_share": overall_stats["overall_mh_share"],
    "mean_total_calls": overall_stats["mean_total_calls_per_day"],
    "mean_mh_calls": overall_stats["mean_mh_calls_per_day"],
    "mean_mh_share": overall_stats["mean_mh_share"],
})

# By year
for _, row in year_stats.iterrows():
    summary_data.append({
        "level": "year",
        "group": str(int(row["year"])),
        "total_calls": int(row["total_calls_sum"]),
        "mh_calls": int(row["mh_calls_sum"]),
        "mh_share": row["mh_share_overall"],
        "mean_total_calls": row["total_calls_mean"],
        "mean_mh_calls": row["mh_calls_mean"],
        "mean_mh_share": row["mh_share_mean"],
    })

df_summary = pd.DataFrame(summary_data)

# Save main summary
df_summary.to_csv(output_path, index=False)
print(f"\n✓ Saved summary to: {output_path}")

# Save detailed by-CD statistics
cd_output_path = OUTPUTS_TABLES / "call_statistics_by_cd.csv"
cd_stats.to_csv(cd_output_path, index=False)
print(f"✓ Saved by-CD statistics to: {cd_output_path}")

# Save by-date statistics
date_output_path = OUTPUTS_TABLES / "call_statistics_by_date.csv"
date_stats.to_csv(date_output_path, index=False)
print(f"✓ Saved by-date statistics to: {date_output_path}")

# Save by-year statistics
year_output_path = OUTPUTS_TABLES / "call_statistics_by_year.csv"
year_stats.to_csv(year_output_path, index=False)
print(f"✓ Saved by-year statistics to: {year_output_path}")

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"\nOverall:")
print(f"  Total calls: {overall_stats['total_calls_sum']:,}")
print(f"  Mental health calls: {overall_stats['total_mh_calls_sum']:,}")
print(f"  MH share: {overall_stats['overall_mh_share']:.4f} ({overall_stats['overall_mh_share']*100:.2f}%)")
print(f"  Mean calls per day: {overall_stats['mean_total_calls_per_day']:.1f}")
print(f"  Mean MH calls per day: {overall_stats['mean_mh_calls_per_day']:.1f}")

print("\nBy Year:")
print(year_stats[["year", "total_calls_sum", "mh_calls_sum", "mh_share_overall"]].to_string(index=False))

print("\n" + "=" * 80)
print("CALL STATISTICS SUMMARY COMPLETE")
print("=" * 80)

