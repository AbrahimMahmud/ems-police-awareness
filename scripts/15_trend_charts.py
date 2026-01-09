"""
Step 15: Create trend charts showing 20 days before/after events.

Two versions:
1. By date of police killing (identified from Twitter spikes or external data)
2. By high awareness days (awareness_z > threshold)

Shows: log of 3-day rolling average of MH calls
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("TREND CHARTS: 20 DAYS BEFORE/AFTER EVENTS")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Ensure we have log rolling average
if "log_mh_calls_3day_rolling" not in df.columns:
    print("⚠️  log_mh_calls_3day_rolling not found. Calculating...")
    df = df.sort_values(["communitydistrict", "incident_date"])
    df["mh_calls_3day_rolling"] = df.groupby("communitydistrict")["mh_calls"].transform(
        lambda x: x.rolling(window=3, min_periods=1, center=True).mean()
    )
    df["log_mh_calls_3day_rolling"] = np.log1p(df["mh_calls_3day_rolling"])

# Filter to analysis period (2017-2020 for Twitter data)
df_analysis = df[df["incident_date"].between("2017-01-01", "2020-12-31")].copy()
print(f"Analysis period (2017-2020): {len(df_analysis):,} rows")

# Version 1: By high awareness days (awareness_z > threshold)
print("\n" + "=" * 80)
print("VERSION 1: BY HIGH AWARENESS DAYS")
print("=" * 80)

threshold = 1.5  # Standard deviations
df_analysis["high_awareness"] = (df_analysis["awareness_z"] > threshold).astype(int)

# Find high awareness days
high_awareness_dates = df_analysis[df_analysis["high_awareness"] == 1]["incident_date"].drop_duplicates().sort_values()
print(f"\nHigh awareness days (>{threshold} SD): {len(high_awareness_dates)}")

if len(high_awareness_dates) > 0:
    # Create event windows: 20 days before and after
    event_data = []
    
    for event_date in high_awareness_dates:
        window_start = event_date - pd.Timedelta(days=20)
        window_end = event_date + pd.Timedelta(days=20)
        
        window_data = df_analysis[
            (df_analysis["incident_date"] >= window_start) & 
            (df_analysis["incident_date"] <= window_end)
        ].copy()
        
        if len(window_data) > 0:
            window_data["days_from_event"] = (window_data["incident_date"] - event_date).dt.days
            window_data["event_date"] = event_date
            event_data.append(window_data)
    
    if event_data:
        df_events = pd.concat(event_data, ignore_index=True)
        
        # Aggregate across events by days from event
        trend_data = df_events.groupby("days_from_event").agg({
            "log_mh_calls_3day_rolling": ["mean", "std", "count"],
            "mh_share": ["mean", "std"],
        }).reset_index()
        
        trend_data.columns = ["days_from_event", "log_mh_mean", "log_mh_std", "n_obs", 
                             "mh_share_mean", "mh_share_std"]
        
        # Calculate confidence intervals
        trend_data["log_mh_se"] = trend_data["log_mh_std"] / np.sqrt(trend_data["n_obs"])
        trend_data["log_mh_ci_low"] = trend_data["log_mh_mean"] - 1.96 * trend_data["log_mh_se"]
        trend_data["log_mh_ci_hi"] = trend_data["log_mh_mean"] + 1.96 * trend_data["log_mh_se"]
        
        # Filter to -20 to +20 days
        trend_data = trend_data[(trend_data["days_from_event"] >= -20) & 
                               (trend_data["days_from_event"] <= 20)]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(trend_data["days_from_event"], trend_data["log_mh_mean"], 
               marker="o", linewidth=2, markersize=4, label="Mean log(MH calls, 3-day avg)")
        
        ax.fill_between(trend_data["days_from_event"], 
                       trend_data["log_mh_ci_low"], 
                       trend_data["log_mh_ci_hi"],
                       alpha=0.3, label="95% Confidence Interval")
        
        ax.axvline(0, color="red", linestyle="--", linewidth=1, label="Event day")
        ax.axhline(trend_data[trend_data["days_from_event"] < 0]["log_mh_mean"].mean(),
                  color="gray", linestyle=":", linewidth=1, label="Pre-event mean")
        
        ax.set_xlabel("Days from High Awareness Event", fontsize=12)
        ax.set_ylabel("Log(3-day Rolling Avg MH Calls)", fontsize=12)
        ax.set_title(f"Trend in Mental Health Calls Around High Awareness Events\n(Threshold: {threshold} SD, N={len(high_awareness_dates)} events)", 
                    fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        output_path = OUTPUTS_FIGURES / "trend_chart_awareness_threshold.png"
        plt.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close()
        
        print(f"✓ Saved trend chart to: {output_path}")
        
        # Save data
        data_out = OUTPUTS_TABLES / "trend_chart_awareness_threshold_data.csv"
        trend_data.to_csv(data_out, index=False)
        print(f"✓ Saved trend data to: {data_out}")

# Version 2: By date of police killing (using Twitter spikes as proxy)
print("\n" + "=" * 80)
print("VERSION 2: BY POLICE KILLING DATES (Twitter Spikes)")
print("=" * 80)

# Identify potential killing dates from very high Twitter spikes
# Use a higher threshold to identify major events
high_threshold = 2.0  # 2 standard deviations

df_analysis["very_high_awareness"] = (df_analysis["awareness_z"] > high_threshold).astype(int)
killing_dates = df_analysis[df_analysis["very_high_awareness"] == 1]["incident_date"].drop_duplicates().sort_values()

print(f"\nPotential killing dates (>{high_threshold} SD): {len(killing_dates)}")
if len(killing_dates) > 0:
    print("Sample dates:")
    for date in killing_dates.head(10):
        awareness_val = df_analysis[df_analysis["incident_date"] == date]["awareness_z"].iloc[0] if len(df_analysis[df_analysis["incident_date"] == date]) > 0 else np.nan
        print(f"  {date.date()}: awareness_z = {awareness_val:.2f}")

if len(killing_dates) > 0:
    # Create event windows
    event_data = []
    
    for event_date in killing_dates:
        window_start = event_date - pd.Timedelta(days=20)
        window_end = event_date + pd.Timedelta(days=20)
        
        window_data = df_analysis[
            (df_analysis["incident_date"] >= window_start) & 
            (df_analysis["incident_date"] <= window_end)
        ].copy()
        
        if len(window_data) > 0:
            window_data["days_from_event"] = (window_data["incident_date"] - event_date).dt.days
            window_data["event_date"] = event_date
            event_data.append(window_data)
    
    if event_data:
        df_events = pd.concat(event_data, ignore_index=True)
        
        # Aggregate across events
        trend_data = df_events.groupby("days_from_event").agg({
            "log_mh_calls_3day_rolling": ["mean", "std", "count"],
            "mh_share": ["mean", "std"],
        }).reset_index()
        
        trend_data.columns = ["days_from_event", "log_mh_mean", "log_mh_std", "n_obs",
                             "mh_share_mean", "mh_share_std"]
        
        # Calculate confidence intervals
        trend_data["log_mh_se"] = trend_data["log_mh_std"] / np.sqrt(trend_data["n_obs"])
        trend_data["log_mh_ci_low"] = trend_data["log_mh_mean"] - 1.96 * trend_data["log_mh_se"]
        trend_data["log_mh_ci_hi"] = trend_data["log_mh_mean"] + 1.96 * trend_data["log_mh_se"]
        
        # Filter to -20 to +20 days
        trend_data = trend_data[(trend_data["days_from_event"] >= -20) & 
                               (trend_data["days_from_event"] <= 20)]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(trend_data["days_from_event"], trend_data["log_mh_mean"], 
               marker="o", linewidth=2, markersize=4, label="Mean log(MH calls, 3-day avg)")
        
        ax.fill_between(trend_data["days_from_event"], 
                       trend_data["log_mh_ci_low"], 
                       trend_data["log_mh_ci_hi"],
                       alpha=0.3, label="95% Confidence Interval")
        
        ax.axvline(0, color="red", linestyle="--", linewidth=1, label="Event day")
        ax.axhline(trend_data[trend_data["days_from_event"] < 0]["log_mh_mean"].mean(),
                  color="gray", linestyle=":", linewidth=1, label="Pre-event mean")
        
        ax.set_xlabel("Days from Police Killing Event", fontsize=12)
        ax.set_ylabel("Log(3-day Rolling Avg MH Calls)", fontsize=12)
        ax.set_title(f"Trend in Mental Health Calls Around Police Killing Events\n(Identified from Twitter spikes >{high_threshold} SD, N={len(killing_dates)} events)", 
                    fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        output_path = OUTPUTS_FIGURES / "trend_chart_killing_dates.png"
        plt.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close()
        
        print(f"✓ Saved trend chart to: {output_path}")
        
        # Save data
        data_out = OUTPUTS_TABLES / "trend_chart_killing_dates_data.csv"
        trend_data.to_csv(data_out, index=False)
        print(f"✓ Saved trend data to: {data_out}")

print("\n" + "=" * 80)
print("TREND CHARTS COMPLETE")
print("=" * 80)

