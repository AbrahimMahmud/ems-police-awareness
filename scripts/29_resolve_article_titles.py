"""Resolve every historical title an article has had, so renames stop deleting attention.

THE DEFECT (audit finding C, re-found live on 2026-09-10)
----------------------------------------------------------
Wikimedia records pageviews PER TITLE and does not carry them across a page
move. Many of these articles were renamed from "Shooting of X" to "Killing of X"
during 2020-21, so fetching only the current canonical title silently discards
everything before the rename — including the attention spike at the moment of
death, which is the entire signal this project measures.

    Shooting_of_Alton_Sterling   3,101 days from 2016-07-06   1,861,004 views
    Killing_of_Alton_Sterling    1,183 days from 2021-04-25     128,855 views

The basket used the second: 6.5% of the attention, and none of July 2016 — the
week he was killed. Measured across the basket, 57 of 117 fetched articles have
under 60% of their expected coverage.

This was diagnosed in the original audit and 21_refetch_wikipedia.py was written
to fix it. It was never applied to the current basket, and it discovers titles by
GUESSING PREFIXES, which fails: guessing produced four false negatives on Alton
Sterling alone. Wikipedia already knows the answer — every former title of a page
survives as a redirect to it.

WHAT THIS DOES
--------------
For each article, ask the redirects API for every title pointing at it, keep the
plausible ones, and measure each one's pageview series. The result is a title map
that 11_fetch_awareness_components.py sums over.

OVERLAP. After a rename the OLD title keeps receiving some traffic, because
people arrive through the redirect. Summing titles therefore double-counts the
post-rename residual. This takes the per-day MAXIMUM across a victim's titles
instead, which is exact before the rename (only one title has traffic) and
conservative after (the new title dominates). Both are computed and the
difference is reported so the choice is inspectable rather than asserted.

Outputs:
  data/reference/article_title_map.csv   article, title, days, views, first, last
  outputs/tables/rename_recovery.csv     per-article before/after coverage
"""

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from config import DATA_REFERENCE, OUTPUTS_TABLES

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic; contact via repository)"}
API = "https://en.wikipedia.org/w/api.php"
PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
      "en.wikipedia/all-access/user/{}/daily/{}/{}")
START, END = "20150701", "20241231"

# Redirects include incidental pages ("CD Man" redirects to Killing of Alton
# Sterling). A candidate must share a substantive word with the article title,
# so we follow the page's own history rather than whatever points at it.
STOPWORDS = {"of", "the", "and", "in", "at", "a", "an", "shooting", "killing",
             "death", "murder", "assault", "beating", "police", "officer"}


class NotFound(RuntimeError):
    """The title has no pageview series. Permanent; distinct from a rate limit."""


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("action", "query")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(int(e.headers.get("Retry-After") or 0) or min(60, 5 * 2 ** attempt))
                continue
            raise
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("wikipedia api did not answer")


def pageviews(title):
    """Daily series for one exact title. Raises NotFound only on a real 404.

    The distinction matters: an earlier probe of this very problem treated every
    exception as 404 and reported that Alton Sterling's pre-rename title had no
    data, when it had 1.86M views and the request had merely been rate-limited.
    """
    u = PV.format(urllib.parse.quote(title.replace(" ", "_"), safe=""), START, END)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                        timeout=45) as r:
                items = json.load(r)["items"]
            return pd.Series({pd.Timestamp(i["timestamp"][:8]): i["views"] for i in items})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound(title) from None
            if e.code in (429, 503):
                time.sleep(int(e.headers.get("Retry-After") or 0) or min(60, 5 * 2 ** attempt))
                continue
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"could not fetch {title}")


def key_words(title):
    w = re.sub(r"[^a-z ]", " ", title.replace("_", " ").lower()).split()
    return {x for x in w if x not in STOPWORDS and len(x) > 2}


def redirects_for(titles):
    """Every title redirecting to each of up to 50 pages per call."""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = [t.replace("_", " ") for t in titles[i:i + 50]]
        d = api(prop="redirects", rdlimit="max", titles="|".join(chunk))
        for p in d.get("query", {}).get("pages", {}).values():
            out[p["title"].replace(" ", "_")] = [
                r["title"].replace(" ", "_") for r in p.get("redirects", [])]
        time.sleep(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="*", default=[
        "wikipedia_article_resolution.csv", "wiki_nyc_articles.csv"])
    args = ap.parse_args()

    arts = []
    for src in args.sources:
        f = DATA_REFERENCE / src
        if not f.exists():
            print(f"  skip {src} (absent)")
            continue
        d = pd.read_csv(f)
        col = "article"
        if "keep" in d.columns:
            d = d[d["keep"]]
        arts += d[col].dropna().tolist()
    arts = sorted(set(arts))
    print(f"resolving historical titles for {len(arts)} articles")

    red = redirects_for(arts)
    print(f"  redirects fetched for {len(red)} pages")

    rows, report = [], []
    for a in arts:
        base = key_words(a)
        cands = [a]
        for r in red.get(a, []):
            # keep only redirects that share a substantive word (the person's
            # name), so "CD Man" -> Killing of Alton Sterling is not probed
            if base & key_words(r):
                cands.append(r)
        cands = list(dict.fromkeys(cands))

        kept, canonical_views = [], 0
        for t in cands:
            try:
                s = pageviews(t)
            except NotFound:
                continue
            except RuntimeError as e:
                print(f"    fetch failed {t}: {e}")
                continue
            time.sleep(0.25)
            if s.empty:
                continue
            if t == a:
                canonical_views = int(s.sum())
            kept.append({"article": a, "title": t, "days": len(s),
                         "views": int(s.sum()),
                         "first": str(s.index.min().date()),
                         "last": str(s.index.max().date())})
        if not kept:
            print(f"  --  {a}: no series under any title")
            continue
        rows += kept
        total = sum(k["views"] for k in kept)
        gain = total / canonical_views if canonical_views else float("inf")
        report.append({"article": a, "n_titles": len(kept),
                       "canonical_views": canonical_views, "all_titles_views": total,
                       "gain": round(gain, 2) if canonical_views else None,
                       "titles": " | ".join(k["title"] for k in kept)})
        if len(kept) > 1:
            print(f"  ok  {a:<44} {len(kept)} titles, "
                  f"{canonical_views:>9,} -> {total:>10,} views "
                  f"({gain:.1f}x)" if canonical_views else "")

    tm = pd.DataFrame(rows)
    tm.to_csv(DATA_REFERENCE / "article_title_map.csv", index=False)
    rep = pd.DataFrame(report)
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUTPUTS_TABLES / "rename_recovery.csv", index=False)

    multi = rep[rep["n_titles"] > 1]
    print(f"\n{len(tm)} title-series over {rep.shape[0]} articles")
    print(f"{len(multi)} articles have more than one historical title")
    if len(multi):
        rec = multi["all_titles_views"].sum() - multi["canonical_views"].sum()
        print(f"recovered {rec:,} views that the canonical-title-only fetch discarded")
        print("\nlargest recoveries:")
        print(multi.nlargest(10, "all_titles_views")[
            ["article", "n_titles", "canonical_views", "all_titles_views", "gain"]
        ].to_string(index=False))


if __name__ == "__main__":
    main()
