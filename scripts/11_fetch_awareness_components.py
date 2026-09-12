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
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

import wikimedia as wm
from config import (basket_artifact, basket_articles_file, basket_source_id,
                    DATA_PROCESSED, DATA_REFERENCE)
from provenance import log_source
from wiki_titles import collapse_duplicates, load_title_map

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}
FROZEN_QUERY = '("police shooting" OR "police killing" OR "killed by police" OR "police brutality")'
START, END = "2015-01-01", "2024-12-31"

# --only lets one component be refetched without re-hitting the others. The
# whole-file overwrite below means a partial GDELT failure would otherwise
# truncate components that were fine, and GDELT is persistently rate-limited
# from this egress IP. Components not selected are carried over from the
# existing file rather than being dropped.
_ap = argparse.ArgumentParser()
_ap.add_argument("--basket", default=None,
                 help="which basket to sum wiki_ext over; default config.CAI_D_BASKET. "
                      "Outputs are suffixed so the arms cannot overwrite each other.")
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


# One file per title, keyed on the request (scripts/wikimedia.py).
PV_CACHE = DATA_PROCESSED / "wiki_pageviews_cache"

rows = []

# --- Wikipedia pageviews, extended window, all resolved articles ---
if ARGS.only in (None, "wiki_ext"):
 res = pd.read_csv(DATA_REFERENCE / basket_articles_file(ARGS.basket))
 articles = res.dropna(subset=["article"]).drop_duplicates("article")["article"].tolist()

 # COLLAPSE DUPLICATE PEOPLE before fetching anything. Each article is summed
 # across all of its historical titles below, so an article that is ITSELF a
 # historical title of another kept article enters the basket twice. Nine
 # victims were double-counted this way - Eric_Garner alongside
 # Killing_of_Eric_Garner, Freddie_Gray alongside Killing_of_Freddie_Gray and
 # seven more, 449,549 views - and it corrupted episode attribution as well as
 # the index (finding T17). The rule lives in wiki_titles.py because 28 needs it
 # too, and writing it twice is how this defect came to exist in one and not the
 # other.
 articles, _dropped = collapse_duplicates(articles, load_title_map())

 # Historical titles. Wikimedia records pageviews per TITLE and does not carry
 # them across a page move, so fetching only the current canonical title
 # discards everything before a rename - including the spike at the moment of
 # death. Measured: Killing_of_Alton_Sterling holds 128,855 views from
 # 2021-04-25, while Shooting_of_Alton_Sterling holds 1,861,004 from 2016-07-06.
 # 57 of 117 basket articles showed under 60% of expected coverage.
 #
 # 29_resolve_article_titles.py discovers every former title from the redirects
 # API and writes the map. Refusing to run without it is deliberate: silently
 # falling back to one title per article is how this defect survived being
 # diagnosed and having a fix written for it.
 _tm = DATA_REFERENCE / "article_title_map.csv"
 if not _tm.exists():
     raise SystemExit(
         f"{_tm.name} is missing. Run 29_resolve_article_titles.py first. "
         "Fetching only canonical titles silently discards pre-rename attention "
         "for roughly half the basket.")
 title_map = (pd.read_csv(_tm).groupby("article")["title"]
              .apply(list).to_dict())
 # Record which articles were ACTUALLY summed, and whether each returned data.
 # Without this, wiki_ext can be built from a stale basket while the basket file
 # on disk says something else — the index and its documented inputs drift apart
 # silently, and every check that reads the basket file reports a property the
 # index does not have. Articles that error out are recorded too, so a basket of
 # 121 that silently became 60 is visible instead of merely smaller.
 used = []
 per_article = []
 wiki_daily = {}
 wiki_daily_max = {}
 n_titles_day = {}
 print(f"  wiki_ext: fetching {len(articles)} basket articles", flush=True)
 for i, art in enumerate(articles, 1):
     if i % 20 == 0:
         print(f"    {i}/{len(articles)}", flush=True)
     titles = title_map.get(art, [art])
     # BOTH aggregations are computed, because the right one is not obvious and
     # the wrong one is not visible in any coverage diagnostic.
     #
     # SUM: Wikimedia attributes a pageview to the exact title requested, so a
     # reader arriving via "Death of George Floyd" and one arriving via "Murder
     # of George Floyd" are two distinct views of the same content. The evidence
     # they are distinct: those two titles cover the SAME 1,681 days with
     # different magnitudes (7.59M vs 3.89M). Triple-counted views would be
     # identical, not different. So the sum is the total attention to the topic.
     #
     # MAX: the conservative alternative. Its risk is under-counting whenever
     # readers are split across live redirects, which is the normal case here.
     #
     # The hazard in SUM is a TIME TREND: titles accumulate within an article
     # (George Floyd gained 14 titles in 2020, 5 in 2021, 3 in 2022), so later
     # years can have more contributing titles and drift upward for a reason
     # that has nothing to do with attention. Both series are written and
     # T.title_agg_no_trend decides between them on the data.
     by_day, by_day_max, n_ok, n_fail, n_404 = {}, {}, 0, 0, 0
     for t in titles:
         # Cached per title, on disk. This block asks for ~500 ten-year daily
         # series and had no cache at all, so every run refetched all of them and
         # a rate-limited interruption threw the whole thing away. The limit is a
         # token bucket on the CLIENT IP, shared with every other Wikimedia
         # caller in this project, so a run that has to start over is not merely
         # slow — it spends budget the basket rebuild also needs. wikimedia.py
         # honours Retry-After and paces across processes, and it does NOT cache
         # failures, so a 429 can never harden into "this title has no data".
         try:
             items = wm.pageviews_items(t, "20150701", "20241231", cache_dir=PV_CACHE)
         except wm.NotFound:
             n_404 += 1
             continue
         except wm.FetchFailed as e:
             # Counted into the ARTIFACT, not only printed. A failure that
             # exists solely in a three-hour stdout log is a failure nobody
             # sees: the last run of this script lost one of Daunte Wright's
             # 14 titles and the basket file recorded n_titles=13 with no way
             # to tell that apart from a title that has no data (finding T15).
             n_fail += 1
             print(f"  wiki skip (fetch failed): {t} — {e}", flush=True)
             continue
         n_ok += 1
         for it in items:
             d = it["timestamp"][:8]
             by_day[d] = by_day.get(d, 0) + it["views"]
             by_day_max[d] = max(by_day_max.get(d, 0), it["views"])

     if not by_day:
         print(f"  wiki skip (no series under any title): {art}", flush=True)
         used.append({"article": art, "days": 0, "views": 0, "ok": False,
                      "reason": "all titles failed" if n_fail else "no series",
                      "n_titles": n_ok, "n_titles_offered": len(titles),
                      "n_titles_no_data": n_404, "n_titles_failed": n_fail})
         continue

     for d, v in by_day.items():
         wiki_daily[d] = wiki_daily.get(d, 0) + v
         wiki_daily_max[d] = wiki_daily_max.get(d, 0) + by_day_max.get(d, 0)
         n_titles_day[d] = n_titles_day.get(d, 0) + 1
         # Keep the per-article series, not just the sum. Episode labelling
         # needs to know WHICH victim drew attention in a given window, and
         # the summed wiki_ext cannot answer that (finding E5/L6/R2).
         per_article.append({"article": art, "date": d, "views": v})
     used.append({"article": art, "days": len(by_day),
                  "views": sum(by_day.values()), "ok": True, "reason": "",
                  "n_titles": n_ok, "n_titles_offered": len(titles),
                  "n_titles_no_data": n_404, "n_titles_failed": n_fail})

 pd.DataFrame(used).to_csv(
     DATA_REFERENCE / basket_artifact("wiki_ext_basket_used.csv", ARGS.basket),
     index=False)

 # A RECORDED FAILURE THAT STILL SHIPS IS NOT A FIX (finding T15, extended).
 #
 # A title whose fetch failed was counted into n_titles_failed and the summed
 # series was written anyway. wiki_ext IS the treatment index's main input, so a
 # rate-limited run published a quietly smaller measure of public attention, with
 # the evidence of it sitting in a column nobody reads until the suite next runs
 # — by which time 12_build_cai.py and 13_extension_episodes.py have rebuilt the
 # index and the episode list on top of it.
 #
 # Refuse instead. The per-title cache above makes a re-run cheap: everything
 # already fetched is on disk, so resuming costs only the titles that failed.
 _failed = [u for u in used if u["n_titles_failed"]]
 if _failed:
     raise SystemExit(
         f"{len(_failed)} article(s) lost at least one title to a failed fetch "
         f"({sum(u['n_titles_failed'] for u in _failed)} titles in total, e.g. "
         f"{[u['article'] for u in _failed[:3]]}). REFUSING to write a wiki_ext "
         "built from an incomplete fetch. Re-run this script — the per-title "
         "cache means only the failures are retried.")
 pa = pd.DataFrame(per_article)
 pa["date"] = pd.to_datetime(pa["date"])
 pa.to_csv(DATA_REFERENCE / basket_artifact("wiki_pageviews_by_article.csv",
                                            ARGS.basket), index=False)
 print(f"  per-article daily series: {len(pa):,} rows over "
       f"{pa['article'].nunique()} articles", flush=True)
 print(f"  wiki_ext: summed {sum(u['ok'] for u in used)} of {len(used)} basket articles")
 for d, v in wiki_daily.items():
     rows.append({"date": d, "component": "wiki_ext", "value": v})

 # Diagnostic for the aggregation choice: the same days under both rules, and
 # how many articles contributed. If sum/max drifts over time the sum is picking
 # up title accumulation rather than attention, and the max series is primary.
 agg = pd.DataFrame({
     "date": pd.to_datetime(list(wiki_daily.keys())),
     "sum": list(wiki_daily.values()),
     "max": [wiki_daily_max[d] for d in wiki_daily],
     "n_articles": [n_titles_day[d] for d in wiki_daily],
 }).sort_values("date")
 agg.to_csv(DATA_REFERENCE / basket_artifact("wiki_ext_aggregation_diagnostic.csv",
                                             ARGS.basket), index=False)
 r = (agg["sum"] / agg["max"].replace(0, pd.NA)).dropna()
 by_year = r.groupby(agg.loc[r.index, "date"].dt.year).median()
 print("  sum/max ratio by year (a trend here means SUM is biased):")
 print("    " + "  ".join(f"{y}:{v:.2f}" for y, v in by_year.items()), flush=True)

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

# GDELT DOC: persistently rate-limited from this egress IP; tolerate failure per
# AWARENESS_INDEX_DESIGN (missing-component rule) and mark pending.
#
# FINDING T7. The whole year loop used to sit inside ONE try/except, so the
# first RuntimeError abandoned every remaining year while the years already
# fetched were still written below - one warning, exit 0, and a register that
# recorded the span REQUESTED. That is how gdelt_news came to end at 2022-12-31
# while the provenance row said 2024-12-31.
#
# Per-year now: one year failing costs that year, not the rest, and every
# failure is named and counted rather than summarised as "unavailable".
gdelt_failed = []
for y0 in (range(2017, 2025, 1) if ARGS.only in (None, 'gdelt_news') else []):
    q = urllib.parse.quote(FROZEN_QUERY + " sourcecountry:US")
    u = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}"
         f"&mode=timelinevol&format=json"
         f"&startdatetime={y0}0101000000&enddatetime={y0}1231235959")
    try:
        js = get_json(u)
    except (RuntimeError, NotFound) as e:
        gdelt_failed.append(y0)
        print(f"  gdelt_news {y0} FAILED: {type(e).__name__}: {str(e)[:90]}", flush=True)
        time.sleep(15)
        continue
    n0 = len(rows)
    for pt in js["timeline"][0]["data"]:
        rows.append({"date": pt["date"][:8], "component": "gdelt_news", "value": pt["value"]})
    print(f"  gdelt_news {y0}: {len(rows) - n0} days", flush=True)
    time.sleep(15)
if gdelt_failed:
    print(f"gdelt_news INCOMPLETE: {len(gdelt_failed)} year(s) missing: {gdelt_failed}")

out = pd.DataFrame(rows)
out["date"] = pd.to_datetime(out["date"])
path = DATA_REFERENCE / basket_artifact("cai_components_daily.csv", ARGS.basket)
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

# REALISED coverage, not the requested span (finding T7). A register that states
# the span we asked for answers the question wrongly, which is worse than not
# answering it.
_realised = out.groupby("component")["date"].agg(["min", "max", "count"])
log_source(
    # Suffixed with the basket: the broad arm writes a DIFFERENT components file
    # and must not overwrite the primary arm's row (see config.basket_source_id).
    basket_source_id("S11", ARGS.basket),
    ("CAI components from GDELT DOC/TV and Wikimedia pageviews; "
     f"query={FROZEN_QUERY}; realised "
     + "; ".join(f"{c}={r['min'].date()}..{r['max'].date()} n={r['count']}"
                 for c, r in _realised.iterrows())),
    "https://api.gdeltproject.org/api/v2 + https://wikimedia.org/api/rest_v1",
    out_file=path)

for c in out["component"].unique():
    s = out[out["component"] == c]
    print(f"{c}: {len(s):,} days, {s['date'].min().date()} -> {s['date'].max().date()}, "
          f"peak {s.loc[s['value'].idxmax(), 'date'].date()}")
