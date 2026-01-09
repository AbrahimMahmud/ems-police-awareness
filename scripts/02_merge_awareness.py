"""Merge Twitter awareness data with EMS panel and create lagged variables."""

import pandas as pd
import numpy as np
from pathlib import Path
from pandas.tseries.holiday import USFederalHolidayCalendar

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

TW1_PATH = DATA_RAW / "211118_tweet_count_name_date.csv"
TW2_PATH = DATA_RAW / "220126_final_daily_tweet_count.csv"
PANEL_PATH = DATA_PROCESSED / "panel_cd_day.parquet"

def load_twitter_csv(path):
    """Load Twitter CSV and aggregate to daily counts."""
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    
    date_col = next((c for c in ("date", "day", "created_at") if c in df.columns), df.columns[0])
    df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    
    cnt_col = next((c for c in ("count", "tweet_count", "tweets", "n", "value", "total") if c in df.columns), "count")
    if cnt_col not in df.columns:
        df[cnt_col] = 1
    df[cnt_col] = pd.to_numeric(df[cnt_col], errors="coerce")
    
    return df.groupby("date", as_index=False)[cnt_col].sum().rename(columns={cnt_col: "tweet_count"}).sort_values("date")

aware1 = load_twitter_csv(TW1_PATH)
aware2 = load_twitter_csv(TW2_PATH)

awareness = aware1.merge(aware2, on="date", how="outer", suffixes=("", "_2"))
tweet_cols = [c for c in awareness.columns if c.startswith("tweet_count")]
awareness["tweet_count_all"] = awareness[tweet_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
awareness = awareness[["date", "tweet_count_all"]].sort_values("date").reset_index(drop=True)

awareness["awareness_z"] = (awareness["tweet_count_all"] - awareness["tweet_count_all"].mean()) / awareness["tweet_count_all"].std(ddof=0)

panel = pd.read_parquet(PANEL_PATH)
panel["incident_date"] = pd.to_datetime(panel["incident_date"])
awareness["date"] = pd.to_datetime(awareness["date"])

df_panel = panel.merge(awareness, left_on="incident_date", right_on="date", how="left").drop(columns=["date"])
df_panel = df_panel.sort_values(["communitydistrict", "incident_date"]).reset_index(drop=True)

for k in range(0, 29):
    df_panel[f"awarez_lag{k}"] = df_panel.groupby("communitydistrict")["awareness_z"].shift(k)

# Calculate 3-day rolling average of MH calls (by CD) and log transform
df_panel = df_panel.sort_values(["communitydistrict", "incident_date"])
df_panel["mh_calls_3day_rolling"] = df_panel.groupby("communitydistrict")["mh_calls"].transform(
    lambda x: x.rolling(window=3, min_periods=1, center=True).mean()
)
df_panel["log_mh_calls_3day_rolling"] = np.log1p(df_panel["mh_calls_3day_rolling"])

df_panel["dow"] = df_panel["incident_date"].dt.dayofweek
df_panel["month"] = df_panel["incident_date"].dt.month
df_panel["year"] = df_panel["incident_date"].dt.year

cal = USFederalHolidayCalendar()
holidays = cal.holidays(start=str(df_panel["incident_date"].min()), end=str(df_panel["incident_date"].max()))
df_panel["is_holiday"] = df_panel["incident_date"].isin(holidays).astype(int)

d = df_panel["incident_date"]
df_panel["covid_phase"] = np.select(
    [(d >= pd.to_datetime("2020-03-01")) & (d <= pd.to_datetime("2020-06-30")), (d >= pd.to_datetime("2020-07-01"))],
    [1, 2], default=0
)

panel_out = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df_panel.to_parquet(panel_out, index=False)

print(f"Merged panel: {df_panel.shape[0]:,} rows, {df_panel['communitydistrict'].nunique()} districts")
print(f"Date range: {df_panel['incident_date'].min()} to {df_panel['incident_date'].max()}")
print(f"Saved to: {panel_out}")
