"""Extract the confirmation-sample episode list from CAI-D, 2015-2024.

MUST run and be committed BEFORE any extension-period (2015-16, 2021-24) EMS
outcome data enters the environment (CONFIRMATION_PLAN.md discipline). Episode
rules are the frozen ones from config (threshold 1.0 on the standardized
index, merge gap < 7 days), applied to CAI-D exactly as they were applied to
the legacy measure for the discovery sample.

Output: data/reference/confirmation_episodes.csv (committed)
"""

import pandas as pd

from config import (
    DATA_PROCESSED,
    DATA_REFERENCE,
    EPISODE_MERGE_GAP_DAYS,
    EPISODE_Z_THRESHOLD,
)

cai = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
cai = cai.dropna(subset=["cai_d"]).sort_values("date")
high = cai[cai["cai_d"] > EPISODE_Z_THRESHOLD]["date"].tolist()

episodes = []
for d in high:
    if episodes and (d - episodes[-1]["end"]).days < EPISODE_MERGE_GAP_DAYS:
        episodes[-1]["end"] = d
        episodes[-1]["n_high_days"] += 1
    else:
        episodes.append({"start": d, "end": d, "n_high_days": 1})

reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
vol = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
prom = vol.set_index(vol["name"].str.lower())["tweet_volume"]

rows = []
for i, ep in enumerate(episodes, 1):
    peak = cai[cai["date"].between(ep["start"], ep["end"])].nlargest(1, "cai_d").iloc[0]
    near = reg[(reg["date"] >= ep["start"] - pd.Timedelta(days=14)) & (reg["date"] <= ep["end"])]
    near = near.assign(p=near["name"].str.lower().map(prom).fillna(0)).sort_values("p", ascending=False)
    rows.append({
        "episode": i,
        "start": ep["start"].date(), "end": ep["end"].date(),
        "n_high_days": ep["n_high_days"],
        "peak_date": peak["date"].date(), "peak_cai_d": round(peak["cai_d"], 2),
        "candidate_events": "; ".join(near["name"].head(2)),
        "period": "discovery" if pd.Timestamp("2017-01-01") <= ep["start"] <= pd.Timestamp("2020-12-31")
                  else "extension",
    })

out = pd.DataFrame(rows)
out.to_csv(DATA_REFERENCE / "confirmation_episodes.csv", index=False)
n_ext = (out["period"] == "extension").sum()
print(f"Episodes: {len(out)} total ({n_ext} extension, {len(out) - n_ext} discovery)")
print(out.to_string(index=False))
