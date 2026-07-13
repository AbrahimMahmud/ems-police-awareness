"""Fetch CAI components, 2015-2024 (AWARENESS_INDEX_DESIGN.md §2).

Components fetched here:
  gdelt_news : GDELT DOC 2.0 timelinevol, frozen query, US sources (CAI-S)
  gdelt_tv   : GDELT TV 2.0 timelinevol, CNN+MSNBC+FOXNEWS airtime share (CAI-S)
  wiki_ext   : Wikimedia pageviews for all resolved victim articles,
               2015-07-01..2024-12-31 (pageviews API begins 2015-07) (CAI-D)
Google Trends (CAI-D) is fetched by 11b (separate: different client/rate limits).

Output: data/reference/cai_components_daily.csv (long: date, component, value)
"""

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_REFERENCE

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}
FROZEN_QUERY = '("police shooting" OR "police killing" OR "killed by police" OR "police brutality")'
START, END = "2015-01-01", "2024-12-31"


def get_json(url, tries=4):
    for a in range(tries):
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=90).read())
        except Exception:
            time.sleep(8 * (a + 1))
    raise RuntimeError(f"failed: {url[:120]}")


rows = []

# --- GDELT DOC (news volume), chunked by 2 years ---
# GDELT DOC fulltext begins 2017-01-01; 2015-16 news tier unavailable (documented)
for y0 in range(2017, 2025, 2):
    q = urllib.parse.quote(FROZEN_QUERY + " sourcecountry:US")
    u = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}"
         f"&mode=timelinevol&format=json"
         f"&startdatetime={y0}0101000000&enddatetime={min(y0+1,2024)}1231235959")
    js = get_json(u)
    for pt in js["timeline"][0]["data"]:
        rows.append({"date": pt["date"][:8], "component": "gdelt_news", "value": pt["value"]})
    time.sleep(6)

# --- GDELT TV (cable airtime share), chunked by 2 years ---
for y0 in range(2015, 2025, 2):
    q = urllib.parse.quote(FROZEN_QUERY + " (station:CNN OR station:MSNBC OR station:FOXNEWS)")
    u = (f"https://api.gdeltproject.org/api/v2/tv/tv?query={q}"
         f"&mode=timelinevol&format=json&datanorm=perc"
         f"&startdatetime={y0}0101000000&enddatetime={min(y0+1,2024)}1231235959")
    js = get_json(u)
    series = js.get("timeline", [{}])[0].get("data", [])
    for pt in series:
        rows.append({"date": pt["date"][:8], "component": "gdelt_tv", "value": pt["value"]})
    time.sleep(6)

# --- Wikipedia pageviews, extended window, all resolved articles ---
res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
articles = res.dropna(subset=["article"]).drop_duplicates("article")["article"].tolist()
wiki_daily = {}
for i, art in enumerate(articles):
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
         f"en.wikipedia/all-access/user/{urllib.parse.quote(art)}/daily/20150701/20241231")
    try:
        for it in get_json(u)["items"]:
            d = it["timestamp"][:8]
            wiki_daily[d] = wiki_daily.get(d, 0) + it["views"]
    except RuntimeError:
        print(f"  wiki skip: {art}")
    time.sleep(0.4)
for d, v in wiki_daily.items():
    rows.append({"date": d, "component": "wiki_ext", "value": v})

out = pd.DataFrame(rows)
out["date"] = pd.to_datetime(out["date"])
out = out.sort_values(["component", "date"])
path = DATA_REFERENCE / "cai_components_daily.csv"
out.to_csv(path, index=False)

log = pd.DataFrame([{
    "source_id": "S11", "description": f"CAI components gdelt_news/gdelt_tv/wiki_ext {START}..{END}; query={FROZEN_QUERY}",
    "url": "api.gdeltproject.org/api/v2 + wikimedia.org/api/rest_v1",
    "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "output_file": str(path),
}])
lp = DATA_REFERENCE / "data_sources.csv"
log.to_csv(lp, mode="a", header=not lp.exists(), index=False)

for c in out["component"].unique():
    s = out[out["component"] == c]
    print(f"{c}: {len(s):,} days, {s['date'].min().date()} -> {s['date'].max().date()}, "
          f"peak {s.loc[s['value'].idxmax(), 'date'].date()}")
