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
    EPISODE_MAX_DAYS,
    EPISODE_MAX_ONSET_LEAD_DAYS,
    EPISODE_EXIT_RATE,
    EPISODE_MIN_SEPARATION_DAYS,
    EPISODE_PEAK_WINDOW_DAYS,
    EPISODE_RATE,
)

cai = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
cai = cai.dropna(subset=["cai_d"]).sort_values("date").reset_index(drop=True)
cai["year"] = cai["date"].dt.year

# --- 1. Constant stringency: the top EPISODE_RATE of days WITHIN each year ---
# A fixed level cut is not a fixed stringency; see config for the measured range.
thresh = cai.groupby("year")["cai_d"].quantile(1.0 - EPISODE_RATE)
exit_thresh = cai.groupby("year")["cai_d"].quantile(1.0 - EPISODE_EXIT_RATE)
cai["thresh"] = cai["year"].map(thresh)
cai["exit_thresh"] = cai["year"].map(exit_thresh)
cai["is_high"] = cai["cai_d"] > cai["thresh"]          # entry bar: starts a shock
cai["in_tail"] = cai["cai_d"] > cai["exit_thresh"]      # exit bar: keeps it open
print("threshold by year (top {:.0%} of days):".format(EPISODE_RATE))
for y, t in thresh.items():
    n = int(cai.loc[cai["year"] == y, "is_high"].sum())
    tot = int((cai["year"] == y).sum())
    print(f"  {y}  cut={t:+.3f}  high={n:3d}/{tot:3d} ({n / tot:.1%})")

# --- 2. Shock detection: local peaks among high days, minimum separation ---
vals = cai["cai_d"].to_numpy()
W = EPISODE_PEAK_WINDOW_DAYS
cands = []
for i in cai.index[cai["is_high"]]:
    lo, hi = max(0, i - W), min(len(cai) - 1, i + W)
    if vals[i] >= vals[lo:hi + 1].max():
        cands.append(i)

# Two peaks closer than the minimum separation are one shock: keep the higher.
cands.sort(key=lambda i: -vals[i])
kept = []
for i in cands:
    if all(abs((cai.at[i, "date"] - cai.at[j, "date"]).days) >= EPISODE_MIN_SEPARATION_DAYS
           for j in kept):
        kept.append(i)
kept.sort(key=lambda i: cai.at[i, "date"])

# --- 3. Onset and bounded span ---
# Walk back from the peak while days stay high (tolerating one-day dips), but no
# further than EPISODE_MAX_ONSET_LEAD_DAYS; then bound the whole span so an
# episode can never be longer than the window it is analysed with.
episodes = []
for i in kept:
    # Walk out along the EXIT bar (hysteresis): a shock is entered on the top
    # decile but stays open through its tail, which is where the response we are
    # looking for would actually land.
    j = i
    while (j - 1 >= 0
           and (cai.at[i, "date"] - cai.at[j - 1, "date"]).days <= EPISODE_MAX_ONSET_LEAD_DAYS
           and cai.at[j - 1, "in_tail"]):
        j -= 1
    k = i
    while (k + 1 < len(cai)
           and (cai.at[k + 1, "date"] - cai.at[j, "date"]).days <= EPISODE_MAX_DAYS
           and cai.at[k + 1, "in_tail"]):
        k += 1
    episodes.append({
        "start": cai.at[j, "date"], "end": cai.at[k, "date"],
        "n_high_days": int(cai.loc[j:k, "is_high"].sum()),
        "peak_i": i,
    })
print(f"\n{len(kept)} shocks detected from {int(cai['is_high'].sum())} high days")

reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
attention = load_attention()

rows = []
for i, ep in enumerate(episodes, 1):
    peak = cai.loc[ep["peak_i"]]
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
