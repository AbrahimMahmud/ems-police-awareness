"""Rebuild the CAI-D Wikipedia article basket from a LIVE source.

WHY THIS EXISTS (finding X2)
----------------------------
The basket `wiki_ext` is summed over was selected using the retired Twitter
volume series, and it contains ZERO victims killed after 2020. A treatment index
whose article list stops in 2020 cannot measure attention in 2021-2024, so every
extension-period episode defined on it is defined on a partly-dead measure.

The basket also cannot be re-derived from Twitter, because that measure was
retired precisely for being undocumented and unre-fetchable. It needs a
selection rule that is live, public, and reproducible by a referee.

WHAT THIS DOES
--------------
Enumerates the English Wikipedia category tree for people killed by US law
enforcement, which IS the live public record of "this killing has an article",
and intersects it with the victim registry (Mapping Police Violence).

Selection is therefore:
  - live      — re-runnable today and next year, no private data
  - blind     — nothing about EMS outcomes enters it
  - auditable — every article traces to a named category

Two things it deliberately does NOT do:
  - rank victims (ranking by attention is what the index is FOR; ranking the
    basket by attention would make the index partly select its own inputs)
  - filter by date, race, or prominence

Resumable: every API response is cached under data/processed/wiki_cat_cache/.
Rate-limited to stay inside Wikimedia's limits; a 429 backs off rather than
being retried in a tight loop.

Outputs:
  data/reference/wiki_basket.csv        name, article, category, in_registry
  outputs/tables/wiki_basket_report.csv coverage by year of death
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from config import DATA_PROCESSED, DATA_REFERENCE, OUTPUTS_TABLES

UA = "ems-police-awareness-research/1.0 (academic; contact via repository)"
CACHE = DATA_PROCESSED / "wiki_cat_cache"
SLEEP = 3.0          # Wikimedia asks for serial, unhurried access
MAX_DEPTH = 3

# Roots of the category tree. Chosen to cover killings by any means and in
# custody, not only shootings, because the outcome hypothesis is about attention
# to police violence rather than about firearms specifically.
ROOTS = [
    "Category:People shot dead by law enforcement officers in the United States",
    "Category:Deaths in police custody in the United States",
    "Category:People killed by law enforcement officers in the United States",
    "Category:Black Lives Matter",
]

# Category branches to refuse. Each would import articles that are not a single
# identifiable killing, which would put non-victim traffic into wiki_ext.
DENY = (
    "by state or territory",   # container categories, re-listing the same people
    "songs", "albums", "films", "documentaries", "books", "television",
    "organizations", "protests", "riots", "murals", "monuments",
)


def _get(params):
    """One cached, rate-limited API call."""
    params = {**params, "format": "json", "action": "query"}
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:24]
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.load(r)
            path.write_text(json.dumps(data))
            time.sleep(SLEEP)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = 5 * (2 ** attempt)
                print(f"    {e.code}; backing off {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if attempt == 5:
                raise
            print(f"    {type(e).__name__}; retrying")
            time.sleep(5 * (2 ** attempt))
    raise RuntimeError(f"gave up on {params}")


def members(cat):
    """All pages and subcategories of one category, following continuations."""
    out, cont = [], {}
    while True:
        d = _get({"list": "categorymembers", "cmtitle": cat, "cmlimit": 500,
                  "cmtype": "page|subcat", **cont})
        out.extend(d.get("query", {}).get("categorymembers", []))
        if "continue" not in d:
            return out
        cont = d["continue"]


def walk(roots, max_depth=MAX_DEPTH):
    """Depth-limited traversal. Returns {article_title: source_category}."""
    seen_cat, articles = set(), {}
    frontier = [(c, 0) for c in roots]
    while frontier:
        cat, depth = frontier.pop(0)
        if cat in seen_cat or depth > max_depth:
            continue
        seen_cat.add(cat)
        low = cat.lower()
        if any(d in low for d in DENY):
            print(f"  skip (denied) {cat}")
            continue
        try:
            ms = members(cat)
        except Exception as e:
            print(f"  ERROR {cat}: {e}")
            continue
        pages = [m["title"] for m in ms if m["ns"] == 0]
        subs = [m["title"] for m in ms if m["ns"] == 14]
        for t in pages:
            articles.setdefault(t, cat)
        print(f"  [{depth}] {cat.replace('Category:', '')[:70]:<70} "
              f"+{len(pages)} pages, {len(subs)} subcats")
        frontier.extend((s, depth + 1) for s in subs)
    return articles, seen_cat


def resolve_redirects(titles, batch=50):
    """Map every redirect in `titles` to the page it points at.

    WHY (findings T13/T17/T18). Category membership is a property of a PAGE, and
    a redirect is a page. The walk therefore collects redirects as if they were
    articles, and two separate defects follow:

      DUPLICATES. When both a redirect and its target survive into the basket,
      the same person is counted twice. Eight did: Eric_Garner alongside
      Killing_of_Eric_Garner, Freddie_Gray alongside Killing_of_Freddie_Gray,
      and six more.

      LOSSES. When only the redirect is collected, the candidacy rule in 26 -
      article starts with a person prefix OR the name matched the registry -
      tests the REDIRECT's title, which usually has neither. The article is then
      never considered at all. Walter_Lamar_Scott is a redirect to
      Killing_of_Walter_Scott, so Walter Scott - whose summed titles are
      2,228,711 views, which would rank 15th of 121 basket articles - was
      missing from the treatment index entirely. Jordan_Edwards_(shooting_victim)
      -> Murder_of_Jordan_Edwards was lost the same way, killed 2017-04-29,
      inside the discovery window.

    Measured on the committed candidate list: 39 of 482 candidates (8%) are
    redirects.

    Resolving here, at the point of collection, fixes both at the source. It is
    strictly better than repairing them downstream, because a redirect that
    reaches the basket has already lost the information needed to repair it.
    """
    out = {}
    titles = list(titles)
    for i in range(0, len(titles), batch):
        chunk = [t.replace("_", " ") for t in titles[i:i + batch]]
        d = _get({"titles": "|".join(chunk), "redirects": 1})
        for r in d.get("query", {}).get("redirects", []):
            out[r["from"].replace(" ", "_")] = r["to"].replace(" ", "_")
        time.sleep(0.5)
    return out


def victim_name(title):
    """Strip the article-title framing to get the person's name."""
    t = title
    for pre in ("Killing of ", "Shooting of ", "Death of ", "Murder of ",
                "Kidnapping and murder of ", "Police shooting of "):
        if t.startswith(pre):
            t = t[len(pre):]
            break
    return t.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=MAX_DEPTH)
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

    print(f"walking {len(ROOTS)} category roots to depth {args.max_depth}\n")
    articles, cats = walk(ROOTS, args.max_depth)
    print(f"\n{len(articles)} distinct articles from {len(cats)} categories")

    reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv")
    date_col = "date" if "date" in reg.columns else reg.columns[
        [c.lower().startswith("date") for c in reg.columns].index(True)]
    reg[date_col] = pd.to_datetime(reg[date_col], errors="coerce")
    by_name = reg.dropna(subset=[date_col]).groupby("name")[date_col].min()

    # Resolve redirects BEFORE anything is decided about a candidate, and keep
    # the target's category attribution. If a redirect and its target are both
    # present, they merge into one entry rather than two.
    raw_articles = dict(articles)
    red = resolve_redirects(sorted(articles))
    if red:
        merged = {}
        for title, cat in sorted(articles.items()):
            tgt = red.get(title.replace(" ", "_"), title).replace("_", " ")
            merged.setdefault(tgt, cat)
        n_lost = sum(1 for f, t in red.items()
                     if t.replace("_", " ") not in articles)
        print(f"resolved {len(red)} redirect(s); {len(articles)} -> {len(merged)} "
              f"distinct articles ({n_lost} target(s) the walk had not collected "
              "directly)")
        articles = merged
    # Commit the resolution itself, not just its effect. Without this the fix is
    # unverifiable offline: a check would have to re-query the API to know whether
    # any candidate is still a redirect, and a check that needs the network is a
    # check that gets skipped. T.no_redirect_candidates reads this.
    pd.DataFrame(
        [{"redirect": f, "target": t,
          "target_was_collected_directly": t.replace("_", " ") in raw_articles}
         for f, t in sorted(red.items())]
    ).to_csv(DATA_REFERENCE / "redirect_resolution.csv", index=False)

    rows = []
    for title, cat in sorted(articles.items()):
        nm = victim_name(title)
        rows.append({"name": nm, "article": title.replace(" ", "_"),
                     "category": cat.replace("Category:", ""),
                     "in_registry": nm in by_name.index,
                     "death_date": by_name.get(nm, pd.NaT)})
    b = pd.DataFrame(rows)
    b.to_csv(DATA_REFERENCE / "wiki_basket.csv", index=False)

    # ---- the metric finding X2 is about ----
    matched = b[b["in_registry"]].copy()
    matched["year"] = pd.to_datetime(matched["death_date"]).dt.year
    yr = matched.groupby("year").size().rename("victims").reset_index()
    yr.to_csv(OUTPUTS_TABLES / "wiki_basket_report.csv", index=False)

    post2020 = int((matched["year"] > 2020).sum())
    print(f"\n{len(b)} articles; {len(matched)} matched to the registry by name")
    print(f"victims killed after 2020: {post2020}   (the old basket had 0)")
    print(yr.to_string(index=False))
    if post2020 == 0:
        print("\nWARNING: still zero post-2020 victims — finding X2 is NOT discharged.")


if __name__ == "__main__":
    main()
