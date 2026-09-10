"""Extract the confirmation-sample episode list from CAI-D, 2015-2024.

MUST run and be committed BEFORE any extension-period (2015-16, 2021-24) EMS
outcome data enters the environment (CONFIRMATION_PLAN.md discipline). Episode
rules are the frozen ones from config (threshold 1.0 on the standardized
index, merge gap < 7 days), applied to CAI-D exactly as they were applied to
the legacy measure for the discovery sample.

Output: data/reference/confirmation_episodes.csv (committed)
"""

import pandas as pd

from attribution import label_window, load_attention

from config import (
    ATTRIBUTION_LOOKBACK_DAYS,
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
attention = load_attention()

rows = []
for i, ep in enumerate(episodes, 1):
    peak = cai[cai["date"].between(ep["start"], ep["end"])].nlargest(1, "cai_d").iloc[0]
    label = label_window(reg, attention, ep["start"], ep["end"],
                         ATTRIBUTION_LOOKBACK_DAYS)
    rows.append({
        "episode": i,
        "start": ep["start"].date(), "end": ep["end"].date(),
        "n_high_days": ep["n_high_days"],
        "peak_date": peak["date"].date(), "peak_cai_d": round(peak["cai_d"], 2),
        "candidate_events": label,
        "period": "discovery" if pd.Timestamp("2017-01-01") <= ep["start"] <= pd.Timestamp("2020-12-31")
                  else "extension",
    })

out = pd.DataFrame(rows)
# The frozen list is data/reference/confirmation_episodes.csv and this script
# MUST NOT write it. It is the pre-registered artifact: its value is that it was
# fixed before any outcome was examined, and regenerating it in place destroys
# the only evidence of that ordering. Corrections go to a new file, the diff
# gets published, and the frozen list is replaced only after sign-off.
#
# This is not hypothetical caution. On 2026-09-10 this script overwrote the
# frozen file because its output path was never changed when the rebuild began;
# it was restored from git and verified byte-identical, and the guard below
# plus check E.frozen_list_untouched exist so it cannot happen silently again.
FROZEN = DATA_REFERENCE / "confirmation_episodes.csv"
REBUILT = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
out.to_csv(REBUILT, index=False)
print(f"wrote {REBUILT.name} — the frozen {FROZEN.name} is untouched")

if FROZEN.exists():
    frozen = pd.read_csv(FROZEN, parse_dates=["start", "end"])
    fs = set(frozen["start"].dt.date)
    rs = set(pd.to_datetime(out["start"]).dt.date)
    print(f"  diff vs frozen: {len(frozen)} -> {len(out)} episodes; "
          f"{len(rs - fs)} added, {len(fs - rs)} dropped, {len(fs & rs)} shared starts")
n_ext = (out["period"] == "extension").sum()
print(f"Episodes: {len(out)} total ({n_ext} extension, {len(out) - n_ext} discovery)")
print(out.to_string(index=False))
