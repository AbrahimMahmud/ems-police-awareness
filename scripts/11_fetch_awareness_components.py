"""Fetch CAI components, 2015-2024 (AWARENESS_INDEX_DESIGN.md §2).

Components fetched here:
  gdelt_news : GDELT DOC 2.0 timelinevol, frozen query, US sources (CAI-S)
  gdelt_tv   : GDELT TV 2.0 timelinevol, CNN+MSNBC+FOXNEWS airtime share (CAI-S)
  wiki_ext   : Wikimedia pageviews for all resolved victim articles,
               2015-07-01..2024-12-31 (pageviews API begins 2015-07) (CAI-D)
Google Trends (CAI-D) is fetched by 11b (separate: different client/rate limits).

Output: data/reference/cai_components_daily.csv (long: date, component, value)
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_REFERENCE

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}
FROZEN_QUERY = '("police shooting" OR "police killing" OR "killed by police" OR "police brutality")'
START, END = "2015-01-01", "2024-12-31"

# --only lets one component be refetched without re-hitting the others. The
# whole-file overwrite below means a partial GDELT failure would otherwise
# truncate components that were fine, and GDELT is persistently rate-limited
# from this egress IP. Components not selected are carried over from the
# existing file rather than being dropped.
_ap = argparse.ArgumentParser()
_ap.add_argument("--only", default=None,
                 choices=["wiki_ext", "gdelt_tv", "gdelt_news"],
                 help="refetch just this component, preserving the others")
ARGS = _ap.parse_args()


class NotFound(RuntimeError):
    """The resource does not exist. Permanent — never worth retrying."""


def get_json(url, tries=6):
    """Fetch JSON, distinguishing permanent failures from transient ones.

    The previous version caught every exception identically and slept
    15/30/45/60/75s before giving up, so ONE nonexistent article cost 225
    seconds of doing nothing. A 121-article basket containing two dead titles
    spends most of an hour asleep, and the run looks hung rather than busy —
    which is exactly how it looked.

    A 404 is a fact about the world, not a temporary condition, so it is raised
    at once and the caller records the article as missing. 429 and 503 are
    transient and honour Retry-After when the server sends one.

    GDELT is a separate case: its rate limiter returns HTTP 200 with a
    plain-text body rather than a status code, so it can only be detected by
    reading the body.
    """
    for a in range(tries):
        try:
            body = urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=90).read()
            text = body[:200].decode("utf-8", "ignore")
            if "limit requests" in text or "Invalid" in text:
                time.sleep(60 + 30 * a)
                continue
            return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound(url[:120]) from None
            if e.code in (429, 503):
                time.sleep(int(e.headers.get("Retry-After") or 0) or min(60, 5 * 2 ** a))
                continue
            time.sleep(5 * (a + 1))
        except Exception:
            time.sleep(5 * (a + 1))
    raise RuntimeError(f"failed after {tries} tries: {url[:120]}")


rows = []

# --- Wikipedia pageviews, extended window, all resolved articles ---
if ARGS.only in (None, "wiki_ext"):
 res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
 articles = res.dropna(subset=["article"]).drop_duplicates("article")["article"].tolist()
 # Record which articles were ACTUALLY summed, and whether each returned data.
 # Without this, wiki_ext can be built from a stale basket while the basket file
 # on disk says something else — the index and its documented inputs drift apart
 # silently, and every check that reads the basket file reports a property the
 # index does not have. Articles that error out are recorded too, so a basket of
 # 121 that silently became 60 is visible instead of merely smaller.
 used = []
 per_article = []
 wiki_daily = {}
 print(f"  wiki_ext: fetching {len(articles)} basket articles", flush=True)
 for i, art in enumerate(articles, 1):
     if i % 20 == 0:
         print(f"    {i}/{len(articles)}", flush=True)
     u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
          f"en.wikipedia/all-access/user/{urllib.parse.quote(art)}/daily/20150701/20241231")
     try:
         items = get_json(u)["items"]
         for it in items:
             d = it["timestamp"][:8]
             wiki_daily[d] = wiki_daily.get(d, 0) + it["views"]
         used.append({"article": art, "days": len(items),
                      "views": sum(it["views"] for it in items), "ok": True,
                      "reason": ""})
         # Keep the per-article series, not just the sum. Episode labelling
         # needs to know WHICH victim drew attention in a given window, and
         # the summed wiki_ext cannot answer that — which is why labelling
         # fell back to the retired Twitter volume (finding E5/L6/R2).
         for it in items:
             per_article.append({"article": art, "date": it["timestamp"][:8],
                                 "views": it["views"]})
     except NotFound:
         print(f"  wiki skip (no such article): {art}", flush=True)
         used.append({"article": art, "days": 0, "views": 0, "ok": False,
                      "reason": "404"})
     except RuntimeError as e:
         print(f"  wiki skip (fetch failed): {art} — {e}", flush=True)
         used.append({"article": art, "days": 0, "views": 0, "ok": False,
                      "reason": "fetch failed"})
     time.sleep(0.4)

 pd.DataFrame(used).to_csv(DATA_REFERENCE / "wiki_ext_basket_used.csv", index=False)
 pa = pd.DataFrame(per_article)
 pa["date"] = pd.to_datetime(pa["date"])
 pa.to_csv(DATA_REFERENCE / "wiki_pageviews_by_article.csv", index=False)
 print(f"  per-article daily series: {len(pa):,} rows over "
       f"{pa['article'].nunique()} articles", flush=True)
 print(f"  wiki_ext: summed {sum(u['ok'] for u in used)} of {len(used)} basket articles")
 for d, v in wiki_daily.items():
     rows.append({"date": d, "component": "wiki_ext", "value": v})

# --- GDELT TV (cable airtime share), chunked by 2 years ---
for y0 in (range(2015, 2025, 1) if ARGS.only in (None, 'gdelt_tv') else []):
    q = urllib.parse.quote(FROZEN_QUERY + " (station:CNN OR station:MSNBC OR station:FOXNEWS)")
    u = (f"https://api.gdeltproject.org/api/v2/tv/tv?query={q}"
         f"&mode=timelinevol&format=json&datanorm=perc"
         f"&startdatetime={y0}0101000000&enddatetime={y0}1231235959")
    js = get_json(u)
    series = js.get("timeline", [{}])[0].get("data", [])
    for pt in series:
        rows.append({"date": pt["date"][:8], "component": "gdelt_tv", "value": pt["value"]})
    time.sleep(15)

# GDELT DOC: persistently rate-limited from this egress IP; tolerate failure
# per AWARENESS_INDEX_DESIGN (missing-component rule) and mark pending.
try:
    # --- GDELT DOC (news volume), chunked by 2 years ---
    # GDELT DOC fulltext begins 2017-01-01; 2015-16 news tier unavailable (documented)
    for y0 in (range(2017, 2025, 1) if ARGS.only in (None, 'gdelt_news') else []):
        q = urllib.parse.quote(FROZEN_QUERY + " sourcecountry:US")
        u = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}"
             f"&mode=timelinevol&format=json"
             f"&startdatetime={y0}0101000000&enddatetime={y0}1231235959")
        js = get_json(u)
        for pt in js["timeline"][0]["data"]:
            rows.append({"date": pt["date"][:8], "component": "gdelt_news", "value": pt["value"]})
        time.sleep(15)
except RuntimeError as e:
    print(f"gdelt_news UNAVAILABLE (rate-limited): {e}")

out = pd.DataFrame(rows)
out["date"] = pd.to_datetime(out["date"])
path = DATA_REFERENCE / "cai_components_daily.csv"
if ARGS.only and path.exists():
    prev = pd.read_csv(path, parse_dates=["date"])
    kept = prev[prev["component"] != ARGS.only]
    print(f"  carrying over {len(kept):,} rows for "
          f"{sorted(kept['component'].unique())} unchanged")
    out = pd.concat([kept, out], ignore_index=True)
out = out.sort_values(["component", "date"])
out.to_csv(path, index=False)
print("  component row counts: "
      + str(out.groupby("component").size().to_dict()))

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
