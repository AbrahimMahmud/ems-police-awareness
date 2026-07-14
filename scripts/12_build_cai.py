"""Build the Composite Awareness Index and run the validation battery
(AWARENESS_INDEX_DESIGN.md §3-§4; construction rules frozen before any
extension-period outcome contact).

CAI-D (demand/attention, THE awareness measure): wiki_ext, trends_us, trends_nyc
CAI-S (supply/delivery, diagnostics only):       gdelt_news, gdelt_tv
Rules: log(1+x) -> standardize on 2017-2019 -> unweighted mean of available
components. Legacy Twitter (2017-2020) is the validation benchmark only.

Outputs:
  data/processed/cai_daily.parquet         date, components (std), cai_d, cai_s
  outputs/tables/cai_validation.csv        the full validation battery
  outputs/tables/cai_top_days.csv          top-20 CAI-D days with attribution
  outputs/tables/cai_divergence_days.csv   high-supply/low-demand days
"""

import numpy as np
import pandas as pd

from config import DATA_PROCESSED, DATA_REFERENCE, OUTPUTS_TABLES

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

D_COMPONENTS = ["wiki_ext", "trends_us", "trends_nyc", "trends_victims"]
S_COMPONENTS = ["gdelt_news", "gdelt_tv"]
STD_WINDOW = ("2017-01-01", "2019-12-31")   # never a window containing Floyd
FLOYD = ("2020-05-26", "2020-07-10")

parts = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"])]
anchored = DATA_REFERENCE / "cai_trends_anchored.csv"
if anchored.exists():
    parts.append(pd.read_csv(anchored, parse_dates=["date"]))  # anchored US/NYC + victim terms
else:
    parts.append(pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"]))
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
std["cai_d"] = std[avail_d].mean(axis=1)
std["cai_s"] = std[avail_s].mean(axis=1)
std["n_d_components"] = std[avail_d].notna().sum(axis=1)

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

# benchmark vs legacy Twitter
aw = pd.read_parquet(DATA_PROCESSED / "awareness_daily.parquet")[["date", "aware_log"]]
m = std.reset_index().merge(aw, on="date", how="inner")
val.append({"check": "BENCHMARK_corr_caiD_vs_twitter_1720", "value": round(m["cai_d"].corr(m["aware_log"]), 3)})
mx = m[~m["date"].between(*FLOYD)]
val.append({"check": "BENCHMARK_corr_caiD_vs_twitter_exFloyd", "value": round(mx["cai_d"].corr(mx["aware_log"]), 3)})

# lead-lag: does supply lead demand by 0-1 days?
for k in (-2, -1, 0, 1, 2):
    val.append({"check": f"xcorr_caiS(t)_caiD(t+{k})",
                "value": round(std["cai_s"].corr(std["cai_d"].shift(-k)), 3)})

pd.DataFrame(val).to_csv(OUTPUTS_TABLES / "cai_validation.csv", index=False)

# top-20 CAI-D days with registry attribution
reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
top = std.nlargest(20, "cai_d").reset_index()[["date", "cai_d", "cai_s"]]
attr = []
for d in top["date"]:
    near = reg[(reg["date"] >= d - pd.Timedelta(days=14)) & (reg["date"] <= d)]
    vol = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
    volmap = vol.set_index(vol["name"].str.lower())["tweet_volume"]
    near = near.assign(prom=near["name"].str.lower().map(volmap).fillna(0))
    near = near.sort_values("prom", ascending=False)
    attr.append("; ".join(near["name"].head(2)) if len(near) else "")
top["candidate_events"] = attr
top.to_csv(OUTPUTS_TABLES / "cai_top_days.csv", index=False)

# divergence days: supply-heavy, demand-light (the falsification-test sample)
z = std.dropna(subset=["cai_d", "cai_s"])
div = z[(z["cai_s"] > z["cai_s"].quantile(0.95)) & (z["cai_d"] < z["cai_d"].median())]
div.reset_index()[["date", "cai_d", "cai_s"]].to_csv(OUTPUTS_TABLES / "cai_divergence_days.csv", index=False)

print(f"CAI built: {std['cai_d'].notna().sum():,} days with CAI-D "
      f"({avail_d}), {std['cai_s'].notna().sum():,} with CAI-S ({avail_s})")
print(pd.DataFrame(val).to_string(index=False))
print(f"\nDivergence days (S>p95, D<median): {len(div)}")
print("\nTop CAI-D days:")
print(top.head(10).to_string(index=False))
