"""Build wiki_nyc: a NYC-local police-violence attention series with no censoring.

WHY THIS EXISTS
---------------
CAI-D's only nominally city-local component was `trends_nyc`, and it is not a
level. Google Trends is a SAMPLE of searches rescaled to integers 0-100 against
the maximum day in the requested window, and Google suppresses region-days below
a minimum volume. For a niche topic over a 7M-person DMA that bites hard: 79% of
days exactly zero on the original single-term query, and still 42.6% after the
query was broadened to a three-term basket (71% in 2024).

That censoring is NOT recoverable by fetching differently. Measured: the same
quiet stretch returns 26.7% / 33.3% / 33.3% / 33.3% zeros at 30 / 45 / 60 / 180
day windows. Window length does nothing, because the floor is Google's, not our
quantization. Adding "NYPD" to the basket does clear it (0.0% zeros) but drops
the correlation with the police-violence concept to 0.25 in quiet periods, since
"NYPD" carries institutional baseline traffic — recruitment, precinct lookups,
department news. It clears the floor by measuring something else.

WHAT THIS DOES INSTEAD
----------------------
Wikipedia pageviews are COUNTS, not a sampled index. No reporting floor, no
0-100 rescaling, no window normalisation, no stitching — the three mechanisms
that produced the censoring do not exist here. Measured on a hand-checked NYC
article set: 0% zero days in EVERY year 2015-2024, 1,842 distinct values against
885 for trends_nyc.

The honest trade, which must be stated in the paper: Wikipedia pageviews are not
geo-split, so this is TOPICAL locality (attention to NYC cases) rather than
GEOGRAPHIC locality (attention among New Yorkers). That is arguably the better
construct — what makes a killing salient to New Yorkers is largely that it
happened here — but it is a different claim and must not be described as a
measure of New Yorkers' attention.

SELECTION, and why it is not a hand list
----------------------------------------
Seeded from live Wikipedia categories, not from titles I guessed. Guessing
titles is how the first pass missed Amadou Diallo, Ramarley Graham and Deborah
Danner, all of which are real articles the category tree already knew about.

Each candidate's OWN categories are then fetched and used to filter, because the
seed category mixes incidents with things that are not incidents: it contains
Occupy Wall Street, the Stonewall riots, a museum, a documentary and an officer
alongside the killings. An article is kept only if it is about a specific
person's death or assault — by title form or by a "Deaths by person in New York
City" style category.

Outputs:
  data/reference/wiki_nyc_articles.csv   the basket, with the reason each was kept
  data/reference/wiki_nyc_daily.csv      date, component=wiki_nyc, value
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from config import DATA_REFERENCE
from provenance import log_source

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic; contact via repository)"}
API = "https://en.wikipedia.org/w/api.php"
PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
      "en.wikipedia/all-access/user/{}/daily/{}/{}")
START, END = "20150701", "20241231"

# Historical titles, shared with wiki_ext. Absent map = refuse, do not silently
# fall back to canonical-only fetching (that is how the defect survived once).
_TM = DATA_REFERENCE / "article_title_map.csv"
TITLE_MAP = ({} if not _TM.exists()
             else pd.read_csv(_TM).groupby("article")["title"].apply(list).to_dict())

# SEEDS MUST BE POLICE-SPECIFIC.
#
# The first version of this script also seeded from "Deaths by person in New
# York City" on the reasoning that it would catch NYC cases the brutality
# category missed. It caught Babe Ruth, Richard Nixon, Herbert Hoover, the
# murder of John Lennon and the UnitedHealthcare CEO shooting, and produced a
# series that peaked on 2024-12-10 — the Mangione arrest. The result looked
# excellent on every diagnostic that was being checked (0% zero days, 2,449
# distinct values) while measuring "attention to notable NYC deaths", which is
# not the construct.
#
# That is the failure this whole audit keeps finding, in a new place: a metric
# that passes its checks because the checks test the wrong property. Coverage
# was measured; CONTENT was not. Hence the police marker requirement below.
SEED_CATEGORIES = [
    "Category:Police brutality by the New York City Police Department",
    "Category:People shot dead by law enforcement officers in New York (state)",
    "Category:Asian people shot dead by law enforcement officers in New York (state)",
    "Category:Deaths in police custody in the United States",
]

# An article is an INCIDENT if its title takes one of these forms...
INCIDENT_PREFIXES = ("Killing of ", "Death of ", "Murder of ", "Shooting of ",
                     "Assault of ", "Beating of ", "Police shooting of ")
# ...or one of its own categories marks it as a person's death.
INCIDENT_CATEGORY_MARKERS = ("Deaths by person in New York City",
                             "People killed by law enforcement",
                             "Deaths in police custody")
# Never an incident, however it is categorised: protests, venues, media, officers.
DENY_MARKERS = ("riots", "Occupy", "Museum", "documentary", "films", "Albums",
                "Songs", "Police officers", "Organizations")

# TWO localities, kept distinct because they are different claims. The strict
# set is New York CITY; the wider set is New York STATE, which additionally
# admits Rochester (Daniel Prude) and White Plains (Kenneth Chamberlain Sr.).
# An earlier version lumped them and labelled all of it "NYC", which was wrong
# for 3 of 11 articles — Prude and Chamberlain carry no New York City category
# at all. Rochester is five hours from the outcome being measured; calling that
# NYC-local would be a false claim about the treatment.
NYC_MARKERS = ("New York City", "NYPD", "New York City Police Department")
NYS_MARKERS = NYC_MARKERS + ("New York (state)", "New York state")

# A NYC death is not enough: the incident must involve law enforcement. Without
# this the seed sweeps in every notable death that happened in the city.
POLICE_MARKERS = ("law enforcement", "police", "NYPD", "Police Department",
                  "police custody", "police brutality")


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("action", "query")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=45) as r:
                d = json.load(r)
            # The API answers HTTP 200 with an {"error": ...} body for a bad
            # parameter mix, so returning it makes a rejected query
            # indistinguishable from a page that genuinely has no data.
            if "error" in d:
                raise RuntimeError(f"wikipedia api error: {d['error'].get('code')}: "
                                   f"{d['error'].get('info')}")
            return d
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = int(e.headers.get("Retry-After") or 0) or min(60, 5 * 2 ** attempt)
                print(f"    HTTP {e.code}; waiting {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("wikipedia api did not answer")


def category_members(cat):
    out, cont = [], {}
    while True:
        d = api(list="categorymembers", cmtitle=cat, cmlimit=500, cmtype="page", **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d:
            return out
        cont = d["continue"]
        time.sleep(1)


def categories_for(titles):
    """Own categories for up to 50 titles per call, FOLLOWING CONTINUATION.

    cllimit="max" is a cap per RESPONSE, not per page. When a 50-title batch has
    more categories than one response holds, the API returns a `continue` cursor
    and the rest are simply absent. The first version of this function ignored
    that cursor, so an article could silently arrive with a truncated category
    list - and this basket is selected BY category ("no New York marker in its
    categories").

    It is not a stable error either: which titles get truncated depends on how
    the API packs the batch, so consecutive runs disagreed. Two runs an hour
    apart produced different baskets - one kept Kenneth Chamberlain and dropped
    Sean Bell, the other the reverse, and the second found Ramarley Graham and
    Randolph Evans that the first had missed. A basket that changes between runs
    cannot support any claim about the series built from it.
    """
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        cont, seen = {}, {}
        while True:
            d = api(prop="categories", clshow="!hidden", cllimit="max",
                    titles="|".join(chunk), **cont)
            for pg in d.get("query", {}).get("pages", {}).values():
                seen.setdefault(pg["title"], [])
                seen[pg["title"]] += [c["title"].replace("Category:", "")
                                      for c in pg.get("categories", [])]
            if "continue" not in d:
                break
            cont = d["continue"]
            time.sleep(1)
        for k, v in seen.items():
            out[k] = sorted(set(v))
        time.sleep(1)
    return out


class TitleFetchFailed(RuntimeError):
    """The request did not succeed. NOT the same as the title having no views."""


def _one_title(title):
    """Daily views for one exact title. Raises on failure; None means a real 404.

    THE DEFECT THIS REPLACES (T15). The body was one try/except returning None
    on ANY exception, so a rate-limited request was indistinguishable from a
    title with no data, and the caller treated None as "contributes nothing".

    Under rate limiting that silently shrinks the series. One run hit three 429s
    and produced a basket in which Killing_of_Eric_Garner, the largest NYC case,
    had VANISHED entirely, Amadou Diallo fell from 2,772,084 views to 633,194
    and Sean Bell from 1,292,831 to 3,220. Nothing in the output said anything
    had failed: the run printed its usual summary and exited 0, and an article
    that lost every title was dropped with the reason "no series" - which reads
    exactly like a correct decision.

    A failure must stop the run, not quietly shrink the data.
    """
    u = PV.format(urllib.parse.quote(title.replace(" ", "_"), safe=""), START, END)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                        timeout=45) as r:
                items = json.load(r)["items"]
            return pd.Series({pd.Timestamp(i["timestamp"][:8]): i["views"]
                              for i in items})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None          # genuinely no series for this exact title
            if e.code in (429, 503):
                wait = int(e.headers.get("Retry-After") or 0) or min(60, 5 * 2 ** attempt)
                print(f"    pageviews HTTP {e.code} on {title}; waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise TitleFetchFailed(title)


def pageviews(article):
    """Sum across every historical title, as wiki_ext does.

    The rename defect applies here identically: fetching only the current
    canonical title discards everything before a page move, including the spike
    at the moment of death. Eric Garner alone gains 4.5x from this
    (1,383,319 -> 6,227,155 views).
    """
    titles = TITLE_MAP.get(article, [article])
    total = None
    for t in titles:
        s = _one_title(t)
        time.sleep(0.25)
        if s is None or s.empty:
            continue
        total = s if total is None else total.add(s, fill_value=0)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-views", type=int, default=2000,
                    help="drop articles that never drew meaningful traffic")
    args = ap.parse_args()

    seen = []
    for cat in SEED_CATEGORIES:
        try:
            m = category_members(cat)
        except Exception as e:
            print(f"  seed failed {cat}: {e}")
            continue
        print(f"  seed {cat.replace('Category:', '')}: {len(m)} articles")
        seen += m

    # Also consider everything the NATIONAL basket's category walk already found.
    # The police-specific NYC categories are narrow and miss cases that are
    # categorised elsewhere: Akai Gurley, Deborah Danner and Ramarley Graham all
    # sit under Black Lives Matter rather than under an NYPD category. Those 482
    # articles are already on disk, so this costs nothing and the same police +
    # NYC filter decides them.
    walked = DATA_REFERENCE / "wiki_basket.csv"
    if walked.exists():
        extra = pd.read_csv(walked)["article"].dropna().str.replace("_", " ").tolist()
        print(f"  seed national category walk: {len(extra)} articles")
        seen += extra

    seen = sorted(set(seen))
    print(f"\n{len(seen)} distinct candidates; fetching their own categories")

    cats = categories_for(seen)

    rows = []
    for t in seen:
        own = cats.get(t, [])
        blob = " | ".join(own)
        is_incident = (t.startswith(INCIDENT_PREFIXES)
                       or any(m in blob for m in INCIDENT_CATEGORY_MARKERS))
        denied = [m for m in DENY_MARKERS if m.lower() in blob.lower()]
        is_nyc = any(m in blob for m in NYC_MARKERS) or any(m in t for m in NYC_MARKERS)
        is_police = any(m.lower() in blob.lower() for m in POLICE_MARKERS)
        is_nyc = any(m in blob for m in NYC_MARKERS) or any(m in t for m in NYC_MARKERS)
        is_nys = any(m in blob for m in NYS_MARKERS) or any(m in t for m in NYS_MARKERS)
        locality = "nyc" if is_nyc else ("nys" if is_nys else "")
        if denied and not t.startswith(INCIDENT_PREFIXES):
            keep, why = False, f"not an incident ({denied[0]})"
        elif not is_incident:
            keep, why = False, "not a specific person's death or assault"
        elif not is_police:
            keep, why = False, "no law-enforcement involvement in its categories"
        elif not locality:
            keep, why = False, "no New York marker in its categories"
        else:
            keep, why = True, ("New York City police-violence incident" if is_nyc
                               else "New York State (not NYC) police-violence incident")
        rows.append({"article": t.replace(" ", "_"), "keep": keep, "reason": why,
                     "locality": locality, "n_categories": len(own)})

    b = pd.DataFrame(rows)
    cand = b[b["keep"]]["article"].tolist()
    print(f"{len(cand)} pass the incident + NYC filter; fetching pageviews")

    series, kept = {}, []
    for a in cand:
        s = pageviews(a)
        time.sleep(0.3)
        if s is None or s.empty or int(s.sum()) < args.min_views:
            b.loc[b["article"] == a, "keep"] = False
            b.loc[b["article"] == a, "reason"] = (
                "no pageview series" if s is None or s.empty
                else f"below the traffic floor ({int(s.sum()):,} views)")
            continue
        series[a] = s
        kept.append(a)
        print(f"  ok  {a:<46} days={len(s):5d} views={int(s.sum()):>9,}")

    # COLLAPSE ARTICLES THAT ARE THE SAME PERSON. pageviews() already sums each
    # article across its historical titles, so an article that is ITSELF a
    # historical title of another kept article would be counted twice - once
    # inside the canonical article's sum, and again as its own basket entry.
    # "Daniel_Prude" and "Killing_of_Daniel_Prude" were exactly this: the title
    # map lists Daniel_Prude as a title of Killing_of_Daniel_Prude, and both
    # were in the basket, so Prude entered wiki_nys twice.
    alias_of = {}
    for canonical, titles in TITLE_MAP.items():
        for t in titles:
            if t != canonical:
                alias_of[t] = canonical
    dropped = [a for a in list(series) if alias_of.get(a) in series]
    for a in dropped:
        print(f"  --  {a}: dropped, it is a historical title of "
              f"{alias_of[a]}, which is already in the basket")
        del series[a]
        kept.remove(a)
        b.loc[b["article"] == a, "keep"] = False
        b.loc[b["article"] == a, "reason"] = f"duplicate: historical title of {alias_of[a]}"
    if dropped:
        print(f"  collapsed {len(dropped)} duplicate article(s)")

    b.to_csv(DATA_REFERENCE / "wiki_nyc_articles.csv", index=False)
    if not series:
        raise SystemExit("no NYC articles survived — refusing to write an empty component")

    idx = pd.date_range("2015-07-01", "2024-12-31", freq="D")
    df = pd.DataFrame(series).reindex(idx).fillna(0.0)
    loc = b.set_index("article")["locality"].to_dict()

    # wiki_nyc  = New York CITY only (the strict local claim)
    # wiki_nys  = New York STATE, a superset (city + Rochester, White Plains, ...)
    nyc_cols = [c for c in df.columns if loc.get(c) == "nyc"]
    frames = []
    for comp, cols in (("wiki_nyc", nyc_cols), ("wiki_nys", list(df.columns))):
        if not cols:
            continue
        tot = df[cols].sum(axis=1)
        frames.append(pd.DataFrame({"date": tot.index, "component": comp,
                                    "value": tot.to_numpy()}))
        print(f"\n{comp}: {len(cols)} articles, {len(tot):,} days, "
              f"{float((tot == 0).mean()):.1%} exactly zero, {tot.nunique():,} distinct, "
              f"median {tot.median():.0f}/day, peak {tot.idxmax().date()} ({tot.max():,.0f})")
        by = tot.groupby(tot.index.year).apply(lambda x: float((x == 0).mean()))
        print("  zero share by year: " + " ".join(f"{y}:{p:.0%}" for y, p in by.items()))
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(DATA_REFERENCE / "wiki_nyc_daily.csv", index=False)
    log_source(
        "S18",
        f"NYC/NYS police-incident Wikipedia attention; {len(nyc_cols)} NYC articles, "
        f"{len(df.columns)} NYS; category walk + pageviews summed across historical titles",
        "https://en.wikipedia.org/w/api.php",
        out_file=DATA_REFERENCE / "wiki_nyc_daily.csv")

    # Per-article series, so the index's CONTENT can be validated and not just
    # its coverage. Without this a viral day on one article is invisible to
    # every diagnostic (finding T11).
    long = (df.stack().rename("views").reset_index()
              .rename(columns={"level_0": "date", "level_1": "article"}))
    long.to_csv(DATA_REFERENCE / "wiki_nyc_per_article.csv", index=False)
    total = df[nyc_cols].sum(axis=1) if nyc_cols else df.sum(axis=1)

    print(f"\nrejected {int((~b['keep']).sum())} candidates; reasons in "
          "wiki_nyc_articles.csv")


if __name__ == "__main__":
    main()
