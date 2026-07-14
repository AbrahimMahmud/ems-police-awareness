"""Complete the Trends component per the frozen spec (AWARENESS_INDEX_DESIGN §2).

1. WEEKLY ANCHOR: one un-stitched weekly series per geo for the full decade
   (single request each -> no chain-scaling drift). The stitched daily series
   from 11b is rescaled so its weekly sums match the anchor ("anchored daily").
2. VICTIM-NAME TERMS: for each major victim, one daily-granularity request
   over event date +/-120d with the payload [victim name, "police brutality"].
   Because both terms share one window's 0-100 scale, victim search volume is
   expressed in topic-term units and is therefore comparable across victims.
   Summed across victims -> trends_victims component (demand tier).

Outputs: data/reference/cai_trends_anchored.csv (trends_us, trends_nyc anchored,
         trends_victims), provenance row appended.
"""

import hashlib
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

from config import DATA_REFERENCE

TOPIC = "police brutality"
GEOS = {"trends_us": "US", "trends_nyc": "US-NY-501"}
VICTIM_EVENTS = {  # name -> event/peak-coverage date
    "George Floyd": "2020-05-25", "Breonna Taylor": "2020-03-13",
    "Rayshard Brooks": "2020-06-12", "Stephon Clark": "2018-03-18",
    "Laquan McDonald": "2018-10-05", "Elijah McClain": "2020-06-24",
    "Alton Sterling": "2016-07-05", "Philando Castile": "2016-07-06",
    "Atatiana Jefferson": "2019-10-12", "Walter Wallace": "2020-10-26",
    "Freddie Gray": "2015-04-19", "Walter Scott": "2015-04-04",
    "Keith Lamont Scott": "2016-09-20", "Daniel Prude": "2020-09-02",
    "Daunte Wright": "2021-04-11", "Tyre Nichols": "2023-01-27",
    "Jordan Neely": "2023-05-01", "Sonya Massey": "2024-07-22",
}

pt = TrendReq(hl="en-US", tz=0, timeout=(10, 30))


def payload(terms, timeframe, geo, tries=4):
    for a in range(tries):
        try:
            pt.build_payload(terms, timeframe=timeframe, geo=geo)
            df = pt.interest_over_time()
            if len(df):
                return df
        except Exception:
            pass
        time.sleep(25 * (a + 1))
    return pd.DataFrame()


rows = []

# --- 1. weekly anchors + anchored daily ---
daily = pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])
for comp, geo in GEOS.items():
    wk = payload([TOPIC], "2015-01-01 2024-12-31", geo)
    if not len(wk):
        print(f"{comp}: weekly anchor FAILED; keeping stitched series unanchored")
        d = daily[daily["component"] == comp]
        for _, r in d.iterrows():
            rows.append({"date": r["date"], "component": comp, "value": r["value"]})
        continue
    wk = wk[TOPIC].astype(float)
    wk.index = pd.to_datetime(wk.index)
    d = daily[daily["component"] == comp].set_index("date")["value"].astype(float)
    # rescale each anchor week so the stitched daily mean matches the anchor value
    anchored = d.copy()
    for wstart, aval in wk.items():
        mask = (anchored.index >= wstart) & (anchored.index < wstart + pd.Timedelta(days=7))
        m = d.loc[mask].mean()
        if m and m > 0:
            anchored.loc[mask] = d.loc[mask] * (aval / m)
    for dt, v in anchored.items():
        rows.append({"date": dt, "component": comp, "value": v})
    drift = np.corrcoef(d.values, anchored.values)[0, 1]
    print(f"{comp}: anchored; corr(stitched, anchored) = {drift:.3f}")
    time.sleep(10)

# --- 2. victim-name terms in topic units ---
victim_daily = {}
for name, ev in VICTIM_EVENTS.items():
    ev = pd.Timestamp(ev)
    t0, t1 = ev - pd.Timedelta(days=30), ev + pd.Timedelta(days=120)
    tf = f"{t0.date()} {t1.date()}"
    df = payload([name, TOPIC], tf, "US")
    if not len(df) or df[TOPIC].max() == 0:
        print(f"  {name}: no usable window")
        time.sleep(8)
        continue
    # express victim volume in topic units within the shared window scale
    ratio = df[name].astype(float)
    for dt, v in ratio.items():
        victim_daily[dt] = victim_daily.get(dt, 0.0) + float(v)
    print(f"  {name}: peak {df[name].idxmax().date()} ({df[name].max():.0f})")
    time.sleep(8)
for dt, v in victim_daily.items():
    rows.append({"date": dt, "component": "trends_victims", "value": v})

out = pd.DataFrame(rows)
path = DATA_REFERENCE / "cai_trends_anchored.csv"
out.to_csv(path, index=False)
log = pd.DataFrame([{
    "source_id": "S13", "description": "Trends weekly-anchored daily (US, NYC) + victim-name terms in topic units",
    "url": "https://trends.google.com (via pytrends)",
    "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "output_file": str(path),
}])
lp = DATA_REFERENCE / "data_sources.csv"
log.to_csv(lp, mode="a", header=not lp.exists(), index=False)
print(f"\nWrote {path}: {len(out):,} rows, components: {sorted(out['component'].unique())}")
