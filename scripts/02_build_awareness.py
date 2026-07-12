"""Build the awareness dataset from the single Twitter source (REWORK_PLAN I5-I9).

Outputs:
  data/processed/awareness_daily.parquet   one row per date 2017-2020: raw counts,
                                           all transform variants, race-specific indices
  data/processed/awareness_lags.parquet    one row per date (buffered range) with
                                           lag 0..28 / lead 1..14 columns per variant,
                                           plus rolling-window means for the primary
  outputs/tables/awareness_episodes.csv    high-awareness episodes with victim attribution
  outputs/tables/qc_awareness.csv          QC metrics
  outputs/tables/qc_awareness_top_days.csv top 15 days with attribution

Key decisions (see REWORK_PLAN.md):
  - Single source: the daily file. The per-victim file is the same data at victim
    granularity (verified here by assertion); it is used only to attribute volume
    to victims and build race-specific indices.
  - Primary transform: log(1 + tweet_count) (I8). z-score kept for comparability
    with the original analysis; rank and tweets+retweets as robustness.
  - Lags/leads are built on the DATE table and merged to the panel by calendar
    date, never by row-shift (I6).
"""

import re

import numpy as np
import pandas as pd

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    AWARENESS_VARIANTS,
    DATA_PROCESSED,
    EPISODE_MERGE_GAP_DAYS,
    EPISODE_Z_THRESHOLD,
    LAGS,
    LEADS,
    OUTPUTS_TABLES,
    PANEL_BUFFER_END,
    PANEL_BUFFER_START,
    PRIMARY_AWARENESS,
    ROLLING_WINDOWS,
    SHOOTINGS_DB_CSV,
    TWEETS_DAILY_CSV,
    TWEETS_PER_VICTIM_CSV,
    VICTIM_CURATION_CSV,
)

DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Load the single daily source and verify the per-victim file matches it
# ---------------------------------------------------------------------------
daily = pd.read_csv(TWEETS_DAILY_CSV, index_col=0)
daily["date"] = pd.to_datetime(daily["date"])
daily = daily[["date", "tweet_count", "retweet_count", "quote_count", "tweets_and_re"]].sort_values("date")

pv = pd.read_csv(TWEETS_PER_VICTIM_CSV)
pv["date"] = pd.to_datetime(pv["date"])

agg = pv.groupby("date", as_index=False)["tweet_count"].sum()
check = daily.merge(agg, on="date", how="left", suffixes=("", "_pv")).fillna({"tweet_count_pv": 0})
mismatch = (check["tweet_count"] - check["tweet_count_pv"]).abs()
n_mismatch = int((mismatch > 0).sum())
assert n_mismatch <= 2, (
    f"Per-victim aggregation deviates from daily file on {n_mismatch} days; "
    "expected at most the 2 known off-by-one days. Investigate before proceeding."
)

# ---------------------------------------------------------------------------
# 2. Victim race classification: exact match -> normalized match -> curated table
# ---------------------------------------------------------------------------
def norm_name(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\.?$", "", s).strip()
    s = re.sub(r"[^a-z ]", "", s)
    parts = s.split()
    return (parts[0] + " " + parts[-1]) if len(parts) >= 2 else s


shoot = pd.read_csv(SHOOTINGS_DB_CSV)
shoot["key_exact"] = shoot["cleaned_name"].astype(str).str.strip().str.lower()
shoot["key_norm"] = shoot["cleaned_name"].astype(str).map(norm_name)
shoot_exact = shoot.drop_duplicates("key_exact").set_index("key_exact")["race"]
shoot_norm = shoot.drop_duplicates("key_norm").set_index("key_norm")["race"]

cur = pd.read_csv(VICTIM_CURATION_CSV)
cur["key_exact"] = cur["name"].astype(str).str.strip().str.lower()
cur_race = cur.drop_duplicates("key_exact").set_index("key_exact")["race"]

pv["key_exact"] = pv["name"].astype(str).str.strip().str.lower()
pv["key_norm"] = pv["name"].astype(str).map(norm_name)

pv["race"] = pv["key_exact"].map(shoot_exact)
pv["match_source"] = np.where(pv["race"].notna(), "exact", None)
m = pv["race"].isna()
pv.loc[m, "race"] = pv.loc[m, "key_norm"].map(shoot_norm)
pv.loc[m & pv["race"].notna(), "match_source"] = "normalized"
m = pv["race"].isna()
pv.loc[m, "race"] = pv.loc[m, "key_exact"].map(cur_race)
pv.loc[m & pv["race"].notna(), "match_source"] = "curated"

total_volume = pv["tweet_count"].sum()
classified_volume = pv.loc[pv["race"].notna(), "tweet_count"].sum()
coverage = classified_volume / total_volume

race_daily = (
    pv.assign(race_group=np.select(
        [pv["race"] == "B", pv["race"].notna()],
        ["black_victim", "nonblack_victim"],
        default="unclassified",
    ))
    .groupby(["date", "race_group"])["tweet_count"].sum()
    .unstack(fill_value=0)
    .reindex(columns=["black_victim", "nonblack_victim", "unclassified"], fill_value=0)
    .reset_index()
)

# ---------------------------------------------------------------------------
# 3. Transforms (I8) on the daily table
# ---------------------------------------------------------------------------
aware = daily.merge(race_daily, on="date", how="left").fillna(
    {"black_victim": 0, "nonblack_victim": 0, "unclassified": 0}
)

aware["aware_log"] = np.log1p(aware["tweet_count"])
mu, sd = aware["tweet_count"].mean(), aware["tweet_count"].std(ddof=0)
aware["aware_z"] = (aware["tweet_count"] - mu) / sd
aware["aware_rank"] = aware["tweet_count"].rank(pct=True)
aware["aware_re_log"] = np.log1p(aware["tweets_and_re"])
aware["aware_black_log"] = np.log1p(aware["black_victim"])
aware["aware_nonblack_log"] = np.log1p(aware["nonblack_victim"])

out_daily = DATA_PROCESSED / "awareness_daily.parquet"
aware.to_parquet(out_daily, index=False)

# ---------------------------------------------------------------------------
# 4. Calendar-date lag/lead table (I6)
# ---------------------------------------------------------------------------
full_dates = pd.DataFrame({"date": pd.date_range(PANEL_BUFFER_START, PANEL_BUFFER_END, freq="D")})
grid = full_dates.merge(aware, on="date", how="left").sort_values("date").reset_index(drop=True)
# Awareness data exists only for 2017-2020; outside that range values stay NaN
# and downstream models drop those rows explicitly.

lag_cols = {}
for var in AWARENESS_VARIANTS:
    for k in LAGS:
        lag_cols[f"{var}_lag{k}"] = grid[var].shift(k)
    for j in LEADS:
        lag_cols[f"{var}_lead{j}"] = grid[var].shift(-j)
lag_tbl = pd.concat([grid[["date"]], pd.DataFrame(lag_cols)], axis=1)

win_cols = {}
for lo, hi in ROLLING_WINDOWS:
    cols = [f"{PRIMARY_AWARENESS}_lag{k}" for k in range(lo, hi + 1)]
    win_cols[f"{PRIMARY_AWARENESS}_w{lo}{hi}"] = lag_tbl[cols].mean(axis=1)
lag_tbl = pd.concat([lag_tbl, pd.DataFrame(win_cols)], axis=1)

out_lags = DATA_PROCESSED / "awareness_lags.parquet"
lag_tbl.to_parquet(out_lags, index=False)

# ---------------------------------------------------------------------------
# 5. Episodes (plan §4.1) with victim attribution
# ---------------------------------------------------------------------------
a = aware[aware["date"].between(ANALYSIS_START, ANALYSIS_END)].copy()
a["is_high"] = a["aware_z"] > EPISODE_Z_THRESHOLD
high_dates = a.loc[a["is_high"], "date"].sort_values().tolist()

episodes = []
for d in high_dates:
    if episodes and (d - episodes[-1]["end"]).days < EPISODE_MERGE_GAP_DAYS:
        episodes[-1]["end"] = d
        episodes[-1]["n_high_days"] += 1
    else:
        episodes.append({"start": d, "end": d, "n_high_days": 1})

ep_rows = []
for i, ep in enumerate(episodes, 1):
    span = pv[pv["date"].between(ep["start"], ep["end"])]
    vol = span.groupby("name")["tweet_count"].sum().sort_values(ascending=False)
    top = vol.index[0] if len(vol) else ""
    top_share = vol.iloc[0] / vol.sum() if len(vol) else np.nan
    peak = a[a["date"].between(ep["start"], ep["end"])].nlargest(1, "aware_z").iloc[0]
    ep_rows.append({
        "episode": i,
        "start": ep["start"].date(),
        "end": ep["end"].date(),
        "n_high_days": ep["n_high_days"],
        "peak_date": peak["date"].date(),
        "peak_z": round(peak["aware_z"], 2),
        "peak_tweets": int(peak["tweet_count"]),
        "top_victim": top,
        "top_victim_share": round(top_share, 3) if top else np.nan,
    })
ep_df = pd.DataFrame(ep_rows)
ep_df.to_csv(OUTPUTS_TABLES / "awareness_episodes.csv", index=False)

# ---------------------------------------------------------------------------
# 6. QC outputs
# ---------------------------------------------------------------------------
variant_corr = aware[list(AWARENESS_VARIANTS)].corr().round(3)

qc = pd.DataFrame([
    {"metric": "daily_rows", "value": len(aware)},
    {"metric": "date_min", "value": str(aware["date"].min().date())},
    {"metric": "date_max", "value": str(aware["date"].max().date())},
    {"metric": "per_victim_daily_mismatch_days", "value": n_mismatch},
    {"metric": "race_classified_volume_share", "value": round(coverage, 4)},
    {"metric": "unclassified_volume_share", "value": round(1 - coverage, 4)},
    {"metric": "curated_rows_used", "value": int((pv["match_source"] == "curated").sum())},
    {"metric": "n_episodes", "value": len(ep_df)},
    {"metric": "n_high_days_z_gt_1", "value": int(a["is_high"].sum())},
    {"metric": "max_aware_z", "value": round(a["aware_z"].max(), 2)},
    {"metric": "corr_log_vs_z", "value": variant_corr.loc["aware_log", "aware_z"]},
    {"metric": "corr_log_vs_rank", "value": variant_corr.loc["aware_log", "aware_rank"]},
    {"metric": "corr_log_vs_re_log", "value": variant_corr.loc["aware_log", "aware_re_log"]},
    {"metric": "corr_black_vs_total_log", "value": variant_corr.loc["aware_black_log", "aware_log"]},
])
qc.to_csv(OUTPUTS_TABLES / "qc_awareness.csv", index=False)

top_days = aware.nlargest(15, "tweet_count").copy()
attribution = []
for d in top_days["date"]:
    day_pv = pv[pv["date"] == d].nlargest(1, "tweet_count")
    attribution.append(day_pv["name"].iloc[0] if len(day_pv) else "")
top_days["top_victim"] = attribution
top_days[["date", "tweet_count", "tweets_and_re", "aware_log", "aware_z",
          "black_victim", "nonblack_victim", "unclassified", "top_victim"]].to_csv(
    OUTPUTS_TABLES / "qc_awareness_top_days.csv", index=False)

print(f"awareness_daily.parquet: {len(aware):,} rows "
      f"({aware['date'].min().date()} -> {aware['date'].max().date()})")
print(f"awareness_lags.parquet:  {len(lag_tbl):,} rows x {lag_tbl.shape[1]} cols")
print(f"Race classification coverage: {coverage:.1%} of tweet volume "
      f"({int((pv['match_source'] == 'curated').sum()):,} rows via curated table)")
print(f"Episodes (z>{EPISODE_Z_THRESHOLD}, merge<{EPISODE_MERGE_GAP_DAYS}d): {len(ep_df)}")
print(ep_df.to_string(index=False))
