"""
Step 2: Merge Twitter awareness data with EMS panel.

This script:
- Loads and combines two Twitter awareness datasets
- Creates z-scored awareness measure
- Merges awareness data with EMS panel
- Creates lagged awareness variables (0-28 days)
- Adds control variables (day of week, month, year, holidays, COVID phases)
- Saves merged panel to data/processed/panel_cd_day_awareness.parquet
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from pandas.tseries.holiday import USFederalHolidayCalendar

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Twitter file names (without _drive suffix)
TW1_BASENAME = "211118_tweet_count_name_date.csv"
TW2_BASENAME = "220126_final_daily_tweet_count.csv"

TW1_PATH = DATA_RAW / TW1_BASENAME
TW2_PATH = DATA_RAW / TW2_BASENAME
PANEL_PATH = DATA_PROCESSED / "panel_cd_day.parquet"

# Check if files exist
if not TW1_PATH.exists():
    raise FileNotFoundError(f"Twitter file 1 not found: {TW1_PATH}")
if not TW2_PATH.exists():
    raise FileNotFoundError(f"Twitter file 2 not found: {TW2_PATH}")
if not PANEL_PATH.exists():
    raise FileNotFoundError(f"Panel file not found: {PANEL_PATH}. Run 01_data_cleaning.py first.")

print(f"Using panel: {PANEL_PATH}")
print(f"Twitter file 1: {TW1_PATH}")
print(f"Twitter file 2: {TW2_PATH}")

# ---- Load & combine Twitter daily awareness ----
def load_twitter_csv(path):
    """Load Twitter CSV and aggregate to daily counts."""
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Pick date-like column
    for cand in ("date", "day", "created_at"):
        if cand in df.columns:
            date_col = cand
            break
    else:
        date_col = df.columns[0]
    
    df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date

    # Pick count column (or create one)
    for cand in ("count", "tweet_count", "tweets", "n", "value", "total"):
        if cand in df.columns:
            cnt_col = cand
            break
    else:
        cnt_col = "count"
        df[cnt_col] = 1

    df[cnt_col] = pd.to_numeric(df[cnt_col], errors="coerce")
    out = (
        df.groupby("date", as_index=False)[cnt_col]
        .sum()
        .rename(columns={cnt_col: "tweet_count"})
    )
    return out.sort_values("date")

print("\nLoading Twitter data...")
aware1 = load_twitter_csv(TW1_PATH)
aware2 = load_twitter_csv(TW2_PATH)

print(f"Awareness 1 date range: {aware1['date'].min()} to {aware1['date'].max()}")
print(f"Awareness 2 date range: {aware2['date'].min()} to {aware2['date'].max()}")

# Combine the two awareness datasets
awareness = aware1.merge(aware2, on="date", how="outer", suffixes=("", "_2"))
tweet_cols = [c for c in awareness.columns if c.startswith("tweet_count")]
awareness["tweet_count_all"] = (
    awareness[tweet_cols]
    .apply(pd.to_numeric, errors="coerce")
    .fillna(0)
    .sum(axis=1)
)
awareness = awareness[["date", "tweet_count_all"]].sort_values("date").reset_index(drop=True)

# Z-score the awareness measure
awareness["awareness_z"] = (
    (awareness["tweet_count_all"] - awareness["tweet_count_all"].mean())
    / awareness["tweet_count_all"].std(ddof=0)
)

print("\nAwareness preview:")
print(awareness.head(10))
print(f"\nAwareness statistics:")
print(f"  Mean tweet count: {awareness['tweet_count_all'].mean():.2f}")
print(f"  Std tweet count: {awareness['tweet_count_all'].std():.2f}")
print(f"  Mean awareness_z: {awareness['awareness_z'].mean():.6f}")
print(f"  Std awareness_z: {awareness['awareness_z'].std():.6f}")

# ---- Merge awareness to panel & build lags ----
print("\nLoading panel and merging awareness...")
panel = pd.read_parquet(PANEL_PATH)
panel["incident_date"] = pd.to_datetime(panel["incident_date"])
awareness["date"] = pd.to_datetime(awareness["date"])

df_panel = panel.merge(
    awareness, left_on="incident_date", right_on="date", how="left"
).drop(columns=["date"])

df_panel = df_panel.sort_values(["communitydistrict", "incident_date"]).reset_index(drop=True)

# Create lagged awareness variables (0-28 days)
print("Creating lagged awareness variables...")
max_lag = 28
for k in range(0, max_lag + 1):
    df_panel[f"awarez_lag{k}"] = df_panel.groupby("communitydistrict")["awareness_z"].shift(k)

# Controls
df_panel["dow"] = df_panel["incident_date"].dt.dayofweek
df_panel["month"] = df_panel["incident_date"].dt.month
df_panel["year"] = df_panel["incident_date"].dt.year

# Federal holidays
cal = USFederalHolidayCalendar()
holidays = cal.holidays(
    start=str(df_panel["incident_date"].min()),
    end=str(df_panel["incident_date"].max())
)
df_panel["is_holiday"] = df_panel["incident_date"].isin(holidays).astype(int)

# COVID phases
d = df_panel["incident_date"]
df_panel["covid_phase"] = np.select(
    [
        (d >= pd.to_datetime("2020-03-01")) & (d <= pd.to_datetime("2020-06-30")),
        (d >= pd.to_datetime("2020-07-01"))
    ],
    [1, 2],
    default=0
)

print("\nMerged panel sample:")
print(df_panel.head(10))
print(f"\nMerged panel shape: {df_panel.shape}")
print(f"Date range: {df_panel['incident_date'].min()} to {df_panel['incident_date'].max()}")
print(f"Number of community districts: {df_panel['communitydistrict'].nunique()}")
print(f"Rows with awareness data: {df_panel['awareness_z'].notna().sum()}")

# Save merged panel
panel_out = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel.to_parquet(panel_out, index=False)
print(f"\nSaved merged panel to: {panel_out}")

