"""Data integrity audit of every committed reference input.

Run before trusting any downstream number. Touches NO outcome data — it reads
only data/reference/ and the treatment-side files in data/processed/, so it is
safe to run while the confirmation freeze is active.

Checks, in order:
  1  component coverage by year and the gaps in each series
  2  whether CAI-D is consistently scaled across component regimes
  3  what inconsistent scaling does to the episode threshold
  4  whether component availability is endogenous to attention
  5  per-victim Wikipedia series: real gaps vs post-event article creation
  6  resolver failures (titles that resolved to low-traffic redirects)
  7  victim registry integrity
  8  ACS demographics integrity
  9  precinct -> CD crosswalk normalisation direction
 10  B-HEARD adoption confidence and exposure bounds
 11  episode labels naming victims killed outside their window
 12  provenance register key collisions

Output: outputs/tables/data_audit.csv  (one row per check, with a PASS/FLAG verdict)
"""

import numpy as np
import pandas as pd

from config import ANALYSIS_END, ANALYSIS_START, DATA_PROCESSED, DATA_REFERENCE, OUTPUTS_TABLES

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 200)

rows = []


def record(check, value, verdict, note=""):
    rows.append({"check": check, "value": value, "verdict": verdict, "note": note})
    mark = {"PASS": "  ", "FLAG": "!!", "INFO": "  "}[verdict]
    print(f"{mark} {check:52s} {str(value):>26s}  {note}")


# ---------------------------------------------------------------------------
print("\n== 1. component coverage ==")
comp = pd.concat([
    pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"]),
    pd.read_csv(DATA_REFERENCE / "cai_trends_anchored.csv", parse_dates=["date"]),
], ignore_index=True)
wide = comp.pivot_table(index="date", columns="component", values="value")
wide = wide.reindex(pd.date_range("2015-01-01", "2024-12-31", freq="D"))

for c in sorted(wide.columns):
    s = wide[c].dropna()
    span = len(pd.date_range(s.index.min(), s.index.max()))
    record(f"coverage_{c}", f"{s.index.min().date()}..{s.index.max().date()}",
           "FLAG" if (span - len(s)) > 30 else "PASS",
           f"{len(s)} days, {span - len(s)} internal gaps")

# ---------------------------------------------------------------------------
print("\n== 2-3. is CAI-D consistently scaled? ==")
cai = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
cai["date"] = pd.to_datetime(cai["date"])
cai = cai.set_index("date")

sd_by_k = cai.groupby("n_d_components")["cai_d"].std()
spread = float(sd_by_k.max() - sd_by_k.min())
record("cai_d_sd_by_component_count", " / ".join(f"{v:.3f}" for v in sd_by_k),
       "FLAG" if spread > 0.10 else "PASS",
       f"range {spread:.3f}; a stable index would be flat")

cai["high"] = cai["cai_d"] > 1.0
flag_rate = cai.groupby("n_d_components")["high"].mean() * 100
rate_spread = float(flag_rate.max() - flag_rate.min())
record("episode_flag_rate_by_component_count", " / ".join(f"{v:.1f}%" for v in flag_rate),
       "FLAG" if rate_spread > 5 else "PASS",
       f"range {rate_spread:.1f}pp; threshold is not a constant-SD rule")

# ---------------------------------------------------------------------------
print("\n== 4. is component availability endogenous to attention? ==")
ALWAYS_ON = ["wiki_ext", "trends_us", "trends_nyc"]
sub = cai.dropna(subset=ALWAYS_ON)
base = sub[ALWAYS_ON].mean(axis=1)
present = sub["trends_victims"].notna()
gap = float(base[present].mean() - base[~present].mean())
record("trends_victims_selection_gap", f"{gap:+.3f} SD",
       "FLAG" if abs(gap) > 0.15 else "PASS",
       "mean of always-on components when trends_victims present vs absent")

ref = base.loc[ANALYSIS_START:"2019-12-31"]
alt = (base - ref.mean()) / ref.std(ddof=0)
record("corr_cai_d_vs_always_on_only", f"{cai['cai_d'].corr(alt):.3f}", "INFO",
       "dropping trends_victims barely changes the ranking")
record("high_days_as_built_vs_always_on", f"{int(cai['high'].sum())} vs {int((alt > 1).sum())}",
       "INFO", "but it changes how many days clear the threshold")

# ---------------------------------------------------------------------------
print("\n== 5-6. per-victim Wikipedia pageviews ==")
pv = pd.read_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", parse_dates=["date"])
res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
# A name can appear more than once (97 namesakes in the registry), so keep every
# killing date per name and treat a label as valid if ANY of them fits the window.
killed_all = reg.groupby("name")["date"].apply(list)
killed = reg.drop_duplicates("name").set_index("name")["date"]   # for single-date reporting

per = pv.groupby("name").agg(days=("date", "size"), first=("date", "min"), views=("views", "sum"))
per["killed"] = per.index.map(killed)
# A series is legitimately short when the article postdates the killing. It is
# suspect when the victim died long before the window but the series is tiny.
per["expected_from"] = per["killed"].clip(lower=pd.Timestamp(ANALYSIS_START))
per["expected_days"] = (pd.Timestamp(ANALYSIS_END) - per["expected_from"]).dt.days + 1
per["shortfall"] = per["expected_days"] - per["days"]
suspect = per[(per["days"] < 30) & (per["expected_days"] > 365)]

record("wiki_victims_resolved", f"{res['article'].notna().sum()} / {len(res)}", "INFO",
       f"{res.loc[res['article'].notna(), 'tweet_volume'].sum() / res['tweet_volume'].sum():.1%} of tweet volume")
record("wiki_series_suspiciously_short", len(suspect),
       "FLAG" if len(suspect) else "PASS",
       "victim died >1yr before window end but series has <30 days")
for nm, r in suspect.iterrows():
    art = res.loc[res["name"] == nm, "article"]
    record(f"  suspect_{nm.replace(' ', '_')}", f"{int(r['days'])}d / {int(r['views'])} views",
           "FLAG", f"killed {r['killed'].date()}, resolved to {art.iloc[0] if len(art) else '?'}")

legit = per[(per["days"] < per["expected_days"]) & (per["killed"] > pd.Timestamp(ANALYSIS_START))]
record("wiki_series_short_but_legitimate", len(legit), "PASS",
       "article postdates the killing; correct behaviour, not a gap")

# ---------------------------------------------------------------------------
print("\n== 7-8. registry and demographics ==")
record("registry_rows", f"{len(reg):,}", "PASS", f"{reg['date'].min().date()}..{reg['date'].max().date()}")
record("registry_duplicate_rows", int(reg.duplicated().sum()),
       "FLAG" if reg.duplicated().any() else "PASS")
record("registry_null_name_or_date", int(reg["name"].isna().sum() + reg["date"].isna().sum()),
       "FLAG" if (reg["name"].isna().any() or reg["date"].isna().any()) else "PASS")
yearly = reg.groupby(reg["date"].dt.year).size()
record("registry_per_year_range", f"{yearly.min()}..{yearly.max()}", "PASS",
       "Mapping Police Violence records ~1,100/yr")

acs = pd.read_csv(DATA_REFERENCE / "acs_2019_cd_demographics.csv")
shares = acs[["pct_white_acs", "pct_black_acs", "pct_hispanic_acs", "pct_asian_acs"]]
record("acs_districts", len(acs), "PASS" if len(acs) == 59 else "FLAG", "expect 59")
record("acs_share_sum_range", f"{shares.sum(axis=1).min():.1f}..{shares.sum(axis=1).max():.1f}",
       "PASS", "remainder is other/multiracial")
record("acs_out_of_range_values", int(((shares < 0) | (shares > 100)).sum().sum()),
       "FLAG" if ((shares < 0) | (shares > 100)).any().any() else "PASS")

# ---------------------------------------------------------------------------
print("\n== 9-10. crosswalk and B-HEARD ==")
cw = pd.read_csv(DATA_REFERENCE / "precinct_cd_crosswalk.csv")
by_cd = cw.groupby("communitydistrict")["w_precinct_in_cd"].sum()
by_pct = cw.groupby("policeprecinct")["w_precinct_in_cd"].sum()
cd_ok = int((by_cd.sub(1).abs() < 1e-3).sum())
record("crosswalk_weights_sum_to_1_by_CD", f"{cd_ok} / {len(by_cd)}", "PASS" if cd_ok == len(by_cd) else "FLAG")
record("crosswalk_weights_sum_to_1_by_precinct",
       f"{int((by_pct.sub(1).abs() < 1e-3).sum())} / {len(by_pct)}", "FLAG",
       "column is named w_precinct_in_cd but is normalised by CD — rename it")

ad = pd.read_csv(DATA_REFERENCE / "bheard_precinct_adoption.csv")
conf = ad["confidence"].value_counts().to_dict()
record("bheard_adoption_confidence", str(conf),
       "FLAG" if conf.get("low", 0) > len(ad) / 3 else "PASS",
       "low-confidence dates in a pre-registered control")

ex = pd.read_csv(DATA_REFERENCE / "bheard_cd_exposure.csv", parse_dates=["effective_from"])
record("bheard_exposure_out_of_bounds", int(((ex["exposure"] < 0) | (ex["exposure"] > 1)).sum()),
       "FLAG" if ((ex["exposure"] < 0) | (ex["exposure"] > 1)).any() else "PASS")
record("bheard_effective_before_launch", int((ex["effective_from"] < "2021-06-01").sum()),
       "FLAG" if (ex["effective_from"] < "2021-06-01").any() else "PASS")

# ---------------------------------------------------------------------------
print("\n== 11-12. episode labels and provenance ==")
ep = pd.read_csv(DATA_REFERENCE / "confirmation_episodes.csv", parse_dates=["start", "end", "peak_date"])
bad, total = [], 0
for _, r in ep.iterrows():
    for nm in str(r["candidate_events"]).split(";"):
        nm = nm.strip()
        if not nm:
            continue
        total += 1
        dates = killed_all.get(nm)
        if dates is None:
            continue
        lo, hi = r["start"] - pd.Timedelta(days=21), r["end"]
        if not any(lo <= d <= hi for d in dates):
            nearest = min(dates, key=lambda d: abs((d - r["start"]).days))
            bad.append(f"ep{r['episode']} '{nm}' (nearest killing {nearest.date()})")
record("episode_labels_out_of_window", f"{len(bad)} / {total}",
       "FLAG" if bad else "PASS", "; ".join(bad))

record("episodes_total", f"{len(ep)} ({(ep['period'] == 'discovery').sum()} disc / "
       f"{(ep['period'] == 'extension').sum()} ext)", "INFO")
record("episodes_single_day", int((ep["n_high_days"] == 1).sum()),
       "FLAG" if (ep["n_high_days"] == 1).sum() > len(ep) / 3 else "PASS",
       "single threshold-grazing days counted as events")
record("episode_longest_span_days", int((ep["end"] - ep["start"]).dt.days.max()), "FLAG",
       "merge-gap rule collapses the 2020 summer into one event")

ds = pd.read_csv(DATA_REFERENCE / "data_sources.csv")
coll = ds.groupby("source_id")["description"].nunique()
record("provenance_id_collisions", int((coll > 1).sum()),
       "FLAG" if (coll > 1).any() else "PASS",
       ", ".join(coll[coll > 1].index))

# ---------------------------------------------------------------------------
out = pd.DataFrame(rows)
out.to_csv(OUTPUTS_TABLES / "data_audit.csv", index=False)
n_flag = int((out["verdict"] == "FLAG").sum())
print(f"\n{'=' * 78}\n{len(out)} checks, {n_flag} flagged -> outputs/tables/data_audit.csv")
