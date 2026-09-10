"""Build the Composite Awareness Index and run the validation battery
(AWARENESS_INDEX_DESIGN.md §3-§4; construction rules frozen before any
extension-period outcome contact).

CAI-D (demand/attention, THE awareness measure): wiki_ext, trends_us, trends_nyc
CAI-S (supply/delivery, diagnostics only):       gdelt_news, gdelt_tv
Rules: log(1+x) -> standardize on 2017-2019 -> unweighted mean of available
components.

Race-matched sub-indices (H3, identity-matched exposure): cai_d_black and
cai_d_nonblack are built here from per-victim Wikipedia pageviews joined to the
victim registry. They replace the Twitter-derived aware_black_log /
aware_nonblack_log, which were retired with the rest of the Twitter measure
(GATE_C_MEMO.md §6). NOTE the coverage limit reported by this script: the
per-victim pageview file currently spans the DISCOVERY window only, so the
race-matched sub-indices are not yet available for the extension sample.

The legacy Twitter benchmark correlation is computed only if the legacy file
happens to be present; it is a diagnostic, and nothing depends on it.

Outputs:
  data/processed/cai_daily.parquet         date, components (std), cai_d, cai_s,
                                           cai_d_black, cai_d_nonblack
  outputs/tables/cai_validation.csv        the full validation battery
  outputs/tables/cai_top_days.csv          top-20 CAI-D days with attribution
  outputs/tables/cai_divergence_days.csv   high-supply/low-demand days
"""

import numpy as np
import pandas as pd

from config import (
    ATTRIBUTION_LOOKBACK_DAYS,
    CAI_D_COMPONENTS,
    CAI_S_COMPONENTS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    OUTPUTS_TABLES,
)

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

D_COMPONENTS = list(CAI_D_COMPONENTS)
S_COMPONENTS = list(CAI_S_COMPONENTS)
RACE_COMPONENTS = {"cai_d_black": "wiki_black", "cai_d_nonblack": "wiki_nonblack"}
STD_WINDOW = ("2017-01-01", "2019-12-31")   # never a window containing Floyd
FLOYD = ("2020-05-26", "2020-07-10")

parts = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"])]
anchored = DATA_REFERENCE / "cai_trends_anchored.csv"
if anchored.exists():
    parts.append(pd.read_csv(anchored, parse_dates=["date"]))  # anchored US/NYC + victim terms
else:
    parts.append(pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"]))

# --- race-split victim attention from per-victim Wikipedia pageviews ---
# Only the wiki component is available at victim granularity: trends_victims is
# already aggregated across victim terms and cannot be split.
pv = pd.read_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", parse_dates=["date"])
reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv")
race = reg.drop_duplicates("name").set_index("name")["race_code"]
pv["race_code"] = pv["name"].map(race)
pv["race_group"] = np.where(pv["race_code"] == "B", "wiki_black",
                            np.where(pv["race_code"].notna(), "wiki_nonblack", "wiki_unclassified"))
race_daily = (pv.groupby(["date", "race_group"])["views"].sum()
                .unstack(fill_value=0)
                .reindex(columns=["wiki_black", "wiki_nonblack", "wiki_unclassified"], fill_value=0)
                .reset_index()
                .melt(id_vars="date", var_name="component", value_name="value"))
parts.append(race_daily[race_daily["component"] != "wiki_unclassified"])

pv_span = (pv["date"].min(), pv["date"].max())
unclassified_share = (pv.loc[pv["race_group"] == "wiki_unclassified", "views"].sum()
                      / max(pv["views"].sum(), 1))

comp = pd.concat(parts, ignore_index=True)
wide = comp.pivot_table(index="date", columns="component", values="value").sort_index()
wide = wide.reindex(pd.date_range("2015-01-01", "2024-12-31", freq="D"))
wide.index.name = "date"

std = pd.DataFrame(index=wide.index)
for c in wide.columns:
    x = np.log1p(wide[c])
    ref = x.loc[STD_WINDOW[0]:STD_WINDOW[1]]
    std[c] = (x - ref.mean()) / ref.std(ddof=0)

avail_d = [c for c in D_COMPONENTS if c in std.columns]
avail_s = [c for c in S_COMPONENTS if c in std.columns]
std["n_d_components"] = std[avail_d].notna().sum(axis=1)
std["n_s_components"] = std[avail_s].notna().sum(axis=1)


def composite(cols, name):
    """Fixed component set, then standardise the COMPOSITE (finding D5).

    Two defects, one fix.

    The index used to be the mean of whatever components existed that day. How
    many existed swung from 2 to 4 across the decade, and the spread of a mean
    moves with the number of terms averaged, so the index's SD moved with data
    availability rather than with attention: 0.770 on 2-component days, 0.693 on
    3, 1.034 on 4. A day became an episode partly because of which sources
    happened to be reporting.

    And averaging k separately standardised series does not give something with
    unit variance — it gives roughly 1/sqrt(k) of it, times the correlation
    structure. Measured here: SD 0.6699 on the reference window. So the frozen
    rule `cai_d > EPISODE_Z_THRESHOLD` with the threshold at 1.0 was never the
    documented "1 SD" rule; it was about 1.5 SD, and it selected the 62nd
    percentile of days in 2020 and the 99.7th in 2024.

    So: score a day only when EVERY component is present, then re-standardise
    the composite on the reference window. Days that lack a component are NaN
    rather than being scored on a different measure under the same name. That is
    a real cost in coverage, and it is reported below rather than absorbed.
    """
    have_all = std[cols].notna().all(axis=1)
    raw = std[cols].mean(axis=1).where(have_all)
    ref = raw.loc[STD_WINDOW[0]:STD_WINDOW[1]]
    if not ref.notna().any():
        raise SystemExit(f"{name}: no complete-component days in the reference window")
    out = (raw - ref.mean()) / ref.std(ddof=0)
    lost = int((~have_all).sum())
    print(f"{name}: {int(have_all.sum()):,} scored days, {lost:,} dropped for an "
          f"incomplete component set ({lost / len(have_all):.1%})")
    return out


std["cai_d"] = composite(avail_d, "cai_d")
std["cai_s"] = composite(avail_s, "cai_s")

# The property the fix exists to create, asserted rather than assumed.
_ref = std["cai_d"].loc[STD_WINDOW[0]:STD_WINDOW[1]]
assert abs(_ref.std(ddof=0) - 1.0) < 1e-9 and abs(_ref.mean()) < 1e-9, (
    f"cai_d is not standardised on the reference window "
    f"(mean={_ref.mean():.4f}, sd={_ref.std(ddof=0):.4f})")
print(f"cai_d reference window: mean={_ref.mean():+.6f} sd={_ref.std(ddof=0):.6f}")
for out_name, src in RACE_COMPONENTS.items():
    # single-component sub-indices: standardised on the same window as CAI-D,
    # but built from wiki alone, so weaker than the full composite by design.
    std[out_name] = std[src] if src in std.columns else np.nan

out = std.reset_index()
out.to_parquet(DATA_PROCESSED / "cai_daily.parquet", index=False)

# ---------------- validation battery ----------------
val = []
cols = avail_d + avail_s
cm = std[cols].corr()
for i, a in enumerate(cols):
    for b in cols[i + 1:]:
        val.append({"check": f"corr_{a}_vs_{b}", "value": round(cm.loc[a, b], 3)})
nofloyd = std[~std.index.to_series().between(*FLOYD)]
cmn = nofloyd[cols].corr()
val.append({"check": "corr_caiD_vs_caiS", "value": round(std["cai_d"].corr(std["cai_s"]), 3)})
val.append({"check": "corr_caiD_vs_caiS_exFloyd", "value": round(nofloyd["cai_d"].corr(nofloyd["cai_s"]), 3)})
if "trends_nyc" in std.columns and "trends_us" in std.columns:
    val.append({"check": "corr_nyc_vs_us_trends", "value": round(std["trends_nyc"].corr(std["trends_us"]), 3)})

# Optional diagnostic: correlation with the retired Twitter series, if it has
# been built. Nothing depends on this; the index does not need Twitter to stand.
legacy_path = DATA_PROCESSED / "awareness_legacy_daily.parquet"
if legacy_path.exists():
    aw = pd.read_parquet(legacy_path)[["date", "aware_log"]]
    m = std.reset_index().merge(aw, on="date", how="inner")
    val.append({"check": "DIAGNOSTIC_corr_caiD_vs_retired_twitter_1720",
                "value": round(m["cai_d"].corr(m["aware_log"]), 3)})
    mx = m[~m["date"].between(*FLOYD)]
    val.append({"check": "DIAGNOSTIC_corr_caiD_vs_retired_twitter_exFloyd",
                "value": round(mx["cai_d"].corr(mx["aware_log"]), 3)})

# race sub-index coverage: the binding limit on H3
val.append({"check": "race_subindex_first_date", "value": str(pv_span[0].date())})
val.append({"check": "race_subindex_last_date", "value": str(pv_span[1].date())})
val.append({"check": "race_subindex_unclassified_view_share", "value": round(unclassified_share, 4)})
val.append({"check": "corr_caiD_vs_caiD_black", "value": round(std["cai_d"].corr(std["cai_d_black"]), 3)})

# lead-lag: does supply lead demand by 0-1 days?
for k in (-2, -1, 0, 1, 2):
    val.append({"check": f"xcorr_caiS(t)_caiD(t+{k})",
                "value": round(std["cai_s"].corr(std["cai_d"].shift(-k)), 3)})

pd.DataFrame(val).to_csv(OUTPUTS_TABLES / "cai_validation.csv", index=False)

# top-20 CAI-D days with registry attribution
reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
top = std.nlargest(20, "cai_d").reset_index()[["date", "cai_d", "cai_s"]]
# Prominence comes from Wikipedia pageviews IN THE WINDOW, keyed on the
# resolved article title (findings E5, L6, R2). It used to come from
# `tweet_volume` in the resolution file — the retired Twitter measure — keyed on
# lowercase name. That had two failure modes. Coverage stopped at death-year
# 2020 and only 150 names carried any value, so for most windows every
# candidate tied at 0.0 and a stable sort returned the registry's own
# date-descending file order: 39 of 70 episode labels were file-order
# artifacts, not attention rankings. And keying on lowercase name gave all four
# "Michael Brown" registry rows Ferguson's volume, which is how episode 22 came
# to be labelled with the Newton NH Michael Brown.
#
# An article title is one person, so the namesake collapse cannot happen. The
# lookback is ATTRIBUTION_LOOKBACK_DAYS rather than 14 because video releases,
# indictments and verdicts spike well after the death (finding E2).
pv_path = DATA_REFERENCE / "wiki_pageviews_by_article.csv"
dec_path = DATA_REFERENCE / "basket_decisions.csv"
if not (pv_path.exists() and dec_path.exists()):
    raise SystemExit(
        "episode attribution needs wiki_pageviews_by_article.csv and "
        "basket_decisions.csv — run 11_fetch_awareness_components.py --only "
        "wiki_ext and 27_finalise_basket.py --apply first. Refusing to fall "
        "back to the retired Twitter ranking (findings E5, L6, R2).")

pv_art = pd.read_csv(pv_path, parse_dates=["date"])
dec = pd.read_csv(dec_path)
art2person = dec.set_index("article")["person"].to_dict()
pv_art["person_key"] = pv_art["article"].map(art2person).str.lower()

attr = []
for d in top["date"]:
    lo = d - pd.Timedelta(days=ATTRIBUTION_LOOKBACK_DAYS)
    near = reg[(reg["date"] >= lo) & (reg["date"] <= d)]
    # Attention to each candidate over the window, summed across that person's
    # article titles (a page move splits the series across titles).
    w = pv_art[(pv_art["date"] >= lo) & (pv_art["date"] <= d)]
    prom = w.groupby("person_key")["views"].sum()
    near = near.assign(prom=near["name"].str.lower().map(prom).fillna(0.0))
    # Only name a candidate that actually drew attention. An all-zero window
    # gets an empty label rather than whatever the file order happens to be.
    near = near[near["prom"] > 0].sort_values("prom", ascending=False)
    attr.append("; ".join(near["name"].head(2)) if len(near) else "")
top["candidate_events"] = attr
top.to_csv(OUTPUTS_TABLES / "cai_top_days.csv", index=False)

# divergence days: supply-heavy, demand-light (the falsification-test sample)
z = std.dropna(subset=["cai_d", "cai_s"])
div = z[(z["cai_s"] > z["cai_s"].quantile(0.95)) & (z["cai_d"] < z["cai_d"].median())]
div.reset_index()[["date", "cai_d", "cai_s"]].to_csv(OUTPUTS_TABLES / "cai_divergence_days.csv", index=False)

print(f"CAI built: {std['cai_d'].notna().sum():,} days with CAI-D "
      f"({avail_d}), {std['cai_s'].notna().sum():,} with CAI-S ({avail_s})")
print(f"Race sub-indices: {std['cai_d_black'].notna().sum():,} days "
      f"({pv_span[0].date()} -> {pv_span[1].date()}); "
      f"{unclassified_share:.1%} of victim pageviews unclassified by race")
if std["cai_d_black"].notna().sum() and pv_span[1] < pd.Timestamp("2024-12-31"):
    print("  WARNING: race sub-indices do not cover the extension window. H3 "
          "cannot be tested on the extension sample until per-victim pageviews "
          "are re-fetched over 2015-2024 (scripts/09_fetch_public_data.py).")
print(pd.DataFrame(val).to_string(index=False))
print(f"\nDivergence days (S>p95, D<median): {len(div)}")
print("\nTop CAI-D days:")
print(top.head(10).to_string(index=False))
