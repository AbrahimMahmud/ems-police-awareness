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

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    CAI_D_COMPONENTS,
    EPISODE_MAX_DAYS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    OUTPUTS_TABLES,
)

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 200)

rows = []


def record(check, value, verdict, note=""):
    rows.append({"check": check, "value": value, "verdict": verdict, "note": note})
    mark = {"PASS": "  ", "FLAG": "!!", "INFO": "  "}[verdict]
    print(f"{mark} {check:52s} {str(value):>26s}  {note}")


# ---------------------------------------------------------------------------
print("\n== 1. component coverage ==")
# Read exactly the files 12_build_cai.py reads. This audit used to read
# cai_trends_anchored.csv, which was deleted when anchoring was retired
# (f7789d1), so from that commit until 2026-09-10 this script raised
# FileNotFoundError on its first statement and produced no audit at all -
# while "audit flags non-increasing" was being recorded as satisfied. An audit
# that cannot run is not a clean audit, so the anchored file is now an explicit
# refusal (matching 12) rather than a silent dependency.
_stale = DATA_REFERENCE / "cai_trends_anchored.csv"
if _stale.exists():
    raise SystemExit(
        f"{_stale.name} still exists. Anchoring is retired; move it to "
        "data/reference/archive/ and re-run (see 12_build_cai.py).")

comp = pd.concat([
    pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"]),
    pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"]),
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

# Finding D5 was that the index averaged whatever components existed that day,
# so its SD tracked DATA AVAILABILITY rather than attention. The repair was to
# score a day only if every component is present, which makes the old
# comparison-across-regimes degenerate - and both checks were reporting on that
# degeneracy rather than on the property:
#
#   n_d_components=2  181 days, cai_d entirely NaN (correctly unscored)
#   n_d_components=3  3,472 days, scored
#
# so the SD check compared NaN against 1.561 and printed "range 0.000, PASS",
# and the flag-rate check compared 0.0% (unscored days can never exceed a
# threshold) against 22.0% and flagged it. One passed and one failed, both for
# reasons that had nothing to do with D5.
#
# What must now hold is the repair itself, so that is what is asserted.
scored = cai["cai_d"].notna()
full = len(CAI_D_COMPONENTS)
bad_scored = int((scored & (cai["n_d_components"] < full)).sum())
bad_unscored = int((~scored & (cai["n_d_components"] >= full)).sum())
record("cai_d_scored_iff_complete", f"{bad_scored} / {bad_unscored}",
       "FLAG" if (bad_scored or bad_unscored) else "PASS",
       f"days scored with <{full} components / days with all {full} left unscored")

sd_by_k = cai.loc[scored].groupby("n_d_components")["cai_d"].std()
if len(sd_by_k) > 1:
    spread = float(sd_by_k.max() - sd_by_k.min())
    record("cai_d_sd_by_component_count", " / ".join(f"{v:.3f}" for v in sd_by_k),
           "FLAG" if spread > 0.10 else "PASS",
           f"range {spread:.3f} among SCORED days; a stable index would be flat")
else:
    record("cai_d_sd_by_component_count", f"{float(sd_by_k.iloc[0]):.3f}", "PASS",
           f"one regime only: every scored day has all {full} components, "
           "so there is no availability regime for the SD to track")

cai["high"] = cai["cai_d"] > 1.0
flag_rate = cai.loc[scored].groupby("n_d_components")["high"].mean() * 100
if len(flag_rate) > 1:
    rate_spread = float(flag_rate.max() - flag_rate.min())
    record("episode_flag_rate_by_component_count",
           " / ".join(f"{v:.1f}%" for v in flag_rate),
           "FLAG" if rate_spread > 5 else "PASS",
           f"range {rate_spread:.1f}pp; threshold is not a constant stringency")
else:
    record("episode_flag_rate_by_component_count", f"{float(flag_rate.iloc[0]):.1f}%",
           "PASS", "one regime only; stringency across YEARS is checked by "
                   "E.threshold_stringency in the regression suite")

# ---------------------------------------------------------------------------
print("\n== 4. is component availability endogenous to attention? ==")
# The component set comes from config, not a second list here. This block used
# to hardcode ["wiki_ext", "trends_us", "trends_nyc"] and then test one named
# component, trends_victims - which was dropped from the index (finding T8), so
# the audit raised KeyError and check 4 onward never ran.
#
# The PROPERTY is what matters and it is not about any one component: if a
# component is missing on days that are systematically quieter or louder than
# average, then "which components exist" is itself a function of attention, and
# the index changes meaning across regimes rather than only changing precision.
# So it is now asked of every component in the index that has any missing day.
present_cols = [c for c in CAI_D_COMPONENTS if c in cai.columns]
missing_cols = [c for c in CAI_D_COMPONENTS if c not in cai.columns]
record("cai_d_components_present", f"{len(present_cols)}/{len(CAI_D_COMPONENTS)}",
       "FLAG" if missing_cols else "PASS",
       f"absent from the component files: {missing_cols}" if missing_cols
       else f"{present_cols}")

# INTERNAL gaps only. A component that simply starts later than another is not
# evidence of endogenous availability - wiki_ext begins 2015-07-01 because that
# is where Wikimedia's daily pageviews begin, while the Trends series begin
# 2015-01-01, and comparing those six months against the rest of the decade
# produced a -0.819 SD "selection gap" that is a level difference between eras,
# not a fact about when data exists.
def _internal_gaps(col):
    s = cai[col]
    obs = s.dropna().index
    if not len(obs):
        return pd.Series(False, index=cai.index)
    inside = (cai.index >= obs.min()) & (cai.index <= obs.max())
    return pd.Series(inside & s.isna().values, index=cai.index)

always_on = [c for c in present_cols if not _internal_gaps(c).any()]
intermittent = [c for c in present_cols if _internal_gaps(c).any()]
for c in present_cols:
    lead = int(((cai.index < cai[c].dropna().index.min()) if cai[c].notna().any()
                else cai.index == cai.index).sum())
    if lead:
        record(f"  span_start_{c}", str(cai[c].dropna().index.min().date()), "INFO",
               f"{lead} days before this component exists at all; "
               "excluded from the selection test as a span difference, not a gap")
if not always_on:
    record("component_selection_gap", "n/a", "FLAG",
           "no component is complete, so there is no stable base to compare against")
for c in intermittent:
    base = cai[always_on].mean(axis=1)
    have = ~_internal_gaps(c)
    gap = float(base[have].mean() - base[~have].mean())
    record(f"selection_gap_{c}", f"{gap:+.3f} SD",
           "FLAG" if abs(gap) > 0.15 else "PASS",
           f"mean of the always-on components on days {c} exists vs does not")
if not intermittent:
    record("component_selection_gap", "none", "PASS",
           f"no component has an internal gap: {present_cols}")

if intermittent:
    base = cai[always_on].mean(axis=1)
    ref = base.loc[ANALYSIS_START:"2019-12-31"]
    alt = (base - ref.mean()) / ref.std(ddof=0)
    record("corr_cai_d_vs_always_on_only", f"{cai['cai_d'].corr(alt):.3f}", "INFO",
           "index vs the gap-free-components-only alternative: ranking")
    record("high_days_as_built_vs_always_on",
           f"{int(cai['high'].sum())} vs {int((alt > 1).sum())}",
           "INFO", "index vs that alternative: days clearing the threshold")
else:
    # With no intermittent component the "alternative" IS the index, so this
    # comparison returns r = 1.000 and a spurious difference in threshold
    # crossings that comes only from re-standardising. Reporting it would be
    # reporting on the arithmetic, not on the data.
    record("corr_cai_d_vs_always_on_only", "n/a", "INFO",
           "no component has an internal gap, so there is no alternative index "
           "to compare against")

# ---------------------------------------------------------------------------
print("\n== 5-6. Wikipedia basket coverage ==")
# This block used to audit wikipedia_pageviews_victims.csv (the LEGACY top-150
# basket, selected by Twitter volume and spanning only 2017-2020) and to read a
# tweet_volume column that no longer exists, so it raised KeyError and checks
# 5-12 never ran. Worse than the crash: even working, it audited a retired
# artifact, so the live wiki_ext basket could have been broken - as it was, by
# the rename defect (T12) - with this reporting nothing.
#
# It now audits the basket the index is actually built from.
reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
killed_all = reg.groupby("name")["date"].apply(list)
killed = reg.drop_duplicates("name").set_index("name")["date"]

used = pd.read_csv(DATA_REFERENCE / "wiki_ext_basket_used.csv")
# Death dates come from basket_decisions.csv, the FINALISED basket, where every
# article carries a date from Wikidata or the registry. wiki_basket.csv is the
# raw candidate list and leaves 39 of these 121 blank, because its date comes
# from an exact-string registry match that middle names and suffixes defeat
# ("Tamir Rice" vs the registry's "Tamir E. Rice") - finding T13. Reading the
# candidate list here produced five coverage flags that were purely an artifact
# of the missing dates.
dec = pd.read_csv(DATA_REFERENCE / "basket_decisions.csv", parse_dates=["death_date"])
death_by_article = dec.dropna(subset=["death_date"]).set_index("article")["death_date"]

# Article CREATION dates, from the earliest first revision across a victim's
# titles (29_resolve_article_titles.py). Without them, "the series starts late"
# is ambiguous between the two things that matter most here:
#   the article did not exist yet   -> correct; no attention existed to record
#   a rename is still eating history -> the defect T12 was supposed to close
tmap = pd.read_csv(DATA_REFERENCE / "article_title_map.csv",
                   parse_dates=["first", "created"])
created_by_article = tmap.groupby("article")["created"].min()
first_by_article = tmap.groupby("article")["first"].min()

# The denominator is the span wiki_ext ACTUALLY covers, read from the component
# file, not a window literal. Wikimedia's per-article daily pageviews begin
# 2015-07-01, so an earlier expectation would flag every article at once; and
# comparing a full-span day count against a discovery-window expectation, as an
# earlier version of this check did, is wrong in both directions.
_wx = comp[comp["component"] == "wiki_ext"]["date"]
WIKI_FROM, WIKI_TO = _wx.min(), _wx.max()

per = used.set_index("article").copy()
per["killed"] = per.index.map(death_by_article)
per["created"] = per.index.map(created_by_article)
per["first"] = per.index.map(first_by_article)
per["expected_from"] = per[["killed", "created"]].max(axis=1).clip(lower=WIKI_FROM)
per["expected_days"] = (WIKI_TO - per["expected_from"]).dt.days + 1
per["coverage"] = per["days"] / per["expected_days"]

record("wiki_basket_span", f"{WIKI_FROM.date()}..{WIKI_TO.date()}", "INFO",
       "realised wiki_ext span; the denominator for coverage below")
no_date = int(per["killed"].isna().sum())
record("wiki_articles_without_death_date", no_date,
       "FLAG" if no_date else "PASS",
       "coverage cannot be assessed without one; not assumed to be fine")

record("wiki_basket_articles", f"{int(per['ok'].sum())} / {len(per)}", "INFO",
       "articles with a usable series / articles attempted")
record("wiki_basket_titles_per_article",
       f"{per['n_titles'].mean():.2f} mean, {int(per['n_titles'].max())} max", "INFO",
       "historical titles summed per article (rename recovery, T12)")

# THE PROPERTY THE RENAME DEFECT VIOLATED is a series that STARTS LATE, not one
# with few days. Killing_of_Alton_Sterling began 2021-04-25 for a man killed in
# 2016; that is lost history. A low-traffic article with scattered missing days
# is not - Wikimedia omits days with no recorded views, so a quiet article is
# legitimately sparse. Day count cannot tell those apart and start lag can.
lagged = per[per["ok"] & per["first"].notna()].copy()
lagged["lag"] = (lagged["first"] - lagged["expected_from"]).dt.days
late = lagged[lagged["lag"] > 7]
record("wiki_series_start_lag_max", f"{int(lagged['lag'].max())}d",
       "FLAG" if len(late) else "PASS",
       f"median {int(lagged['lag'].median())}d; days between max(death, article "
       "creation) and the first observed view — a rename shows up here")
record("wiki_articles_with_lost_history", len(late),
       "FLAG" if len(late) else "PASS",
       "series starting >7d after the article existed")
for art, r in late.nlargest(10, "lag").iterrows():
    record(f"  lost_history_{art}", f"{int(r['lag'])}d late", "FLAG",
           f"created {pd.Timestamp(r['created']).date()}, "
           f"first view {pd.Timestamp(r['first']).date()}")

# Coverage is reported but NOT flagged: after the start-lag test above, a low
# figure means a quiet article, which is information rather than a defect.
low = per[(per["coverage"] < 0.60) & (per["expected_days"] > 365) & per["ok"]
          & per["killed"].notna()]
record("wiki_articles_below_60pct_coverage", len(low), "INFO",
       "sparse days on low-traffic articles; not a defect once start lag is 0")
for art, r in low.nlargest(5, "expected_days").iterrows():
    record(f"  low_cov_{art}", f"{r['coverage']:.0%} ({int(r['days'])}d)", "INFO",
           f"expected {int(r['expected_days'])}d from "
           f"{pd.Timestamp(r['expected_from']).date()} (died "
           f"{pd.Timestamp(r['killed']).date()}, article created "
           f"{pd.Timestamp(r['created']).date()})")

nots = per[~per["ok"]]
record("wiki_basket_unusable", len(nots), "INFO" if len(nots) else "PASS",
       "reasons: " + str(nots["reason"].value_counts().to_dict()) if len(nots) else "")

# The legacy per-victim file is still live for ONE thing: the race-split
# components in 12_build_cai.py. Audit it as that input and nothing more.
pv = pd.read_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", parse_dates=["date"])
pv_named = pv["name"].map(lambda n: n in killed_all.index)
record("racesplit_input_span", f"{pv['date'].min().date()}..{pv['date'].max().date()}",
       "FLAG" if pd.Timestamp(pv["date"].min()) > pd.Timestamp(ANALYSIS_START)
       else "PASS",
       f"legacy top-150 file; {pv['name'].nunique()} victims, "
       f"{pv_named.mean():.0%} matched to the registry")

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
by_cd = cw.groupby("communitydistrict")["w_cd_calls_from_precinct"].sum()
by_pct = cw.groupby("policeprecinct")["w_cd_calls_from_precinct"].sum()
cd_ok = int((by_cd.sub(1).abs() < 1e-3).sum())
record("crosswalk_weights_sum_to_1_by_CD", f"{cd_ok} / {len(by_cd)}", "PASS" if cd_ok == len(by_cd) else "FLAG")
record("crosswalk_weights_sum_to_1_by_precinct",
       f"{int((by_pct.sub(1).abs() < 1e-3).sum())} / {len(by_pct)}", "INFO",
       "normalised by CD, which is the direction B-HEARD exposure needs")

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
# BOTH lists are audited. confirmation_episodes.csv is the FROZEN artifact and
# must stay byte-identical, so its properties are recorded as history, not as
# things to fix; confirmation_episodes_rebuilt.csv is what the current shock
# rule produces and is the one that has to hold. Auditing only the frozen file
# reported a 128-day episode and 34 single-day events as live defects, when the
# construct change had already bounded both.
EPISODE_LISTS = [
    ("frozen", DATA_REFERENCE / "confirmation_episodes.csv", False),
    ("rebuilt", DATA_REFERENCE / "confirmation_episodes_rebuilt.csv", True),
]
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

for label, path, live in EPISODE_LISTS:
    if not path.exists():
        record(f"episodes_{label}", "absent", "FLAG" if live else "INFO",
               f"{path.name} is not on disk")
        continue
    e = pd.read_csv(path, parse_dates=["start", "end", "peak_date"])
    span = int((e["end"] - e["start"]).dt.days.max())
    single = int((e["n_high_days"] == 1).sum())
    record(f"episodes_{label}_total",
           f"{len(e)} ({(e['period'] == 'discovery').sum()} disc / "
           f"{(e['period'] == 'extension').sum()} ext)", "INFO",
           "the live list" if live else "the frozen artifact, kept byte-identical")
    record(f"episodes_{label}_single_day", single,
           ("FLAG" if single > len(e) / 3 else "PASS") if live else "INFO",
           "single threshold-grazing days counted as events")
    record(f"episodes_{label}_longest_span_days", span,
           ("FLAG" if span > EPISODE_MAX_DAYS else "PASS") if live else "INFO",
           f"cap is {EPISODE_MAX_DAYS} days under the shock rule"
           if live else "regime rule: the 2020 summer collapses into one event")

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
