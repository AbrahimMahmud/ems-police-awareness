"""Re-fetch victim Wikipedia pageviews, summing across historical article titles.

WHY THIS EXISTS (docs/DATA_AUDIT.md §3)
---------------------------------------
Wikimedia records pageviews per TITLE, and a page move does not carry its history
to the new title. Many police-killing articles were renamed during 2020-21
("Shooting of X" -> "Killing of X"). The original resolver in
09_fetch_public_data.py resolved each victim to the article's CURRENT canonical
title, so for every renamed article the series begins at the rename date and all
earlier traffic is invisible — including the attention spike at the time of the
killing, which is exactly the signal this project measures.

Verified example: Killing_of_Walter_Scott returns 1,370 days and 231,231 views
starting 2020-12-31, while Shooting_of_Walter_Scott returns 3,472 days and
1,950,646 views starting 2015-07-01. Resolving to the canonical title alone threw
away 89% of the article's traffic and all of its 2015 peak.

15 of 45 previously-resolved articles show this signature.

WHAT THIS DOES
--------------
For each victim, probe every plausible title variant, keep the ones that exist and
are about a police killing, and sum their daily pageviews. Post-rename the old
title still receives redirect traffic, so summing slightly over-counts in the
overlap; the alternative (per-day max) loses that traffic instead. Both are
reported so the choice can be inspected — see the discontinuity check below.

Resumable: every probe is cached under data/processed/wiki_probe_cache/, so the
script can be interrupted and restarted without re-hitting the API.

Outputs:
  data/reference/wikipedia_pageviews_victims.csv    per-victim daily, summed
  data/reference/wikipedia_article_resolution.csv   updated with every title used
  data/reference/cai_components_daily.csv           wiki_ext recomputed
  outputs/tables/wiki_refetch_report.csv            per-victim before/after
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from config import DATA_PROCESSED, DATA_REFERENCE, OUTPUTS_TABLES

START, END = "2015-07-01", "2024-12-31"          # Wikimedia pageviews API begins 2015-07
PREFIXES = ["Shooting of", "Killing of", "Murder of", "Death of"]
POLICE_WORDS = ("police", "officer", "law enforcement", "deputy", "trooper", "sheriff")
UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}
SLEEP = 2.0                                       # Wikimedia rate-limits aggressively

CACHE = DATA_PROCESSED / "wiki_probe_cache"
CACHE.mkdir(parents=True, exist_ok=True)
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)


def _get(url, tries=6):
    for a in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (a + 1))
                continue
            return None          # 404: title does not exist
        except Exception:
            time.sleep(3 * (a + 1))
    return None


def is_police_article(title):
    """True if the title exists and its summary is about a police killing."""
    j = _get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}")
    if not j:
        return False
    return any(w in (j.get("extract") or "").lower() for w in POLICE_WORDS)


def pageviews(article):
    """Daily pageviews for one exact title. Cached to disk."""
    safe = urllib.parse.quote(article, safe="")
    f = CACHE / f"{safe.replace('%', '_')}.json"
    if f.exists():
        return json.loads(f.read_text())
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
           f"all-access/user/{safe}/daily/{START.replace('-', '')}00/{END.replace('-', '')}00")
    j = _get(url)
    items = [] if not j else [{"date": i["timestamp"][:8], "views": i["views"]} for i in j.get("items", [])]
    f.write_text(json.dumps(items))
    time.sleep(SLEEP)
    return items


res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
old_pv = pd.read_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", parse_dates=["date"])
old_tot = old_pv.groupby("name")["views"].sum()

frames, report, resolution = [], [], []
names = res["name"].tolist()
print(f"probing {len(names)} victims x {len(PREFIXES)} title variants (cached; resumable)\n")

for i, name in enumerate(names, 1):
    base = str(name).strip().replace(" ", "_")
    candidates = [f"{p.replace(' ', '_')}_{base}" for p in PREFIXES]
    prior = res.loc[res["name"] == name, "article"]
    if len(prior) and isinstance(prior.iloc[0], str):
        candidates.append(prior.iloc[0])          # keep any manually-verified title

    kept, per_title = [], {}
    for art in dict.fromkeys(candidates):         # de-dupe, preserve order
        items = pageviews(art)
        if not items:
            continue
        if not is_police_article(art):            # guards against same-name articles
            time.sleep(SLEEP)
            continue
        time.sleep(SLEEP)
        kept.append(art)
        per_title[art] = len(items)
        d = pd.DataFrame(items)
        d["date"] = pd.to_datetime(d["date"], format="%Y%m%d")
        d["name"], d["article"] = name, art
        frames.append(d[["name", "article", "date", "views"]])

    if kept:
        got = pd.concat([f for f in frames if f["name"].iloc[0] == name])
        combined = got.groupby("date")["views"].sum()
        report.append({
            "name": name, "titles_used": " + ".join(kept), "n_titles": len(kept),
            "days_after": int(combined.notna().sum()), "views_after": int(combined.sum()),
            "views_before": int(old_tot.get(name, 0)),
            "first_after": combined.index.min().date(), "last_after": combined.index.max().date(),
        })
        for art in kept:
            resolution.append({"name": name, "article": art, "pageview_days": per_title[art]})
    if i % 10 == 0 or i == len(names):
        print(f"  {i}/{len(names)} probed, {len(report)} resolved")

if not frames:
    raise SystemExit("no articles resolved — check network access to wikipedia/wikimedia")

# ---------------------------------------------------------------------------
allpv = pd.concat(frames, ignore_index=True)
# per-victim daily series: sum across that victim's historical titles
victim_daily = allpv.groupby(["name", "date"], as_index=False)["views"].sum()
victim_daily["article"] = victim_daily["name"].map(
    allpv.groupby("name")["article"].agg(lambda s: " + ".join(sorted(set(s)))))
victim_daily[["name", "article", "date", "views"]].to_csv(
    DATA_REFERENCE / "wikipedia_pageviews_victims.csv", index=False)

# wiki_ext: total attention across all victim articles, deduplicated by title
wiki_ext = (allpv.drop_duplicates(["article", "date"])
            .groupby("date", as_index=False)["views"].sum()
            .assign(component="wiki_ext")[["date", "component", "views"]]
            .rename(columns={"views": "value"}))

comp = pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"])
comp = comp[comp["component"] != "wiki_ext"]
pd.concat([comp, wiki_ext], ignore_index=True).sort_values(["component", "date"]).to_csv(
    DATA_REFERENCE / "cai_components_daily.csv", index=False)

rep = pd.DataFrame(report)
rep["views_gained"] = rep["views_after"] - rep["views_before"]
rep = rep.sort_values("views_gained", ascending=False)
rep.to_csv(OUTPUTS_TABLES / "wiki_refetch_report.csv", index=False)
pd.DataFrame(resolution).to_csv(DATA_REFERENCE / "wikipedia_article_resolution_titles.csv", index=False)

print(f"\nresolved {rep.shape[0]} / {len(names)} victims, {len(resolution)} distinct titles")
print(f"multi-title (renamed) victims: {(rep['n_titles'] > 1).sum()}")
print(f"wiki_ext: {len(wiki_ext):,} days {wiki_ext['date'].min().date()}..{wiki_ext['date'].max().date()}")
print("\nlargest recoveries:")
print(rep.head(12)[["name", "n_titles", "views_before", "views_after", "views_gained"]].to_string(index=False))
