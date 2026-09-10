"""Which victim drew attention in a window — one implementation, two callers.

WHY THIS MODULE EXISTS (findings E5, L6, R2, and the duplication noted in the
audit's X-series)
------------------------------------------------------------------------------
Episode labelling used to rank candidate victims by `tweet_volume` from
wikipedia_article_resolution.csv — the retired Twitter measure — keyed on
lowercase name. The same logic was written twice, in 12_build_cai.py and
13_extension_episodes.py, so a fix to one left the other wrong. Two failure
modes, both live:

  COVERAGE. Twitter volume stops at death-year 2020 and only the top 150 of
  13,241 registry names carried any value. For most windows every candidate tied
  at 0.0, and `sort_values(ascending=False)` is a stable sort, so the "ranking"
  returned the registry's own date-descending file order. 39 of 70 episode
  labels were file-order artifacts. Every episode starting 2021 or later was one.

  IDENTITY. Keying on lowercase name collapsed namesakes. All four "Michael
  Brown" registry rows (Ferguson 2014, Fort Worth 2016, Newton NH 2017, Milford
  CT 2024) inherited Ferguson's 10,037 tweets, so discovery episode 22
  (2017-06-17) was labelled with the Newton NH Michael Brown and demoted
  Charleena Lyles — Seattle, killed during a mental-health crisis, the most
  on-hypothesis victim in that window — to second place.

WHAT REPLACES IT
----------------
Wikipedia pageviews accumulated IN THE WINDOW, keyed on the resolved article
title. An article is one person, so the namesake collapse cannot happen, and
pageviews exist for the whole 2015-2024 span rather than stopping in 2020.

Two deliberate properties:

  - A candidate with no attention is not named. An empty label is the honest
    answer for a window where nothing was read; a file-order default is not.
  - Views are summed across all of a person's article titles, because Wikimedia
    records pageviews per title and a page move does not carry history across
    it (the rename defect, docs/DATA_AUDIT.md 3).

This module never ranks the article BASKET — only which victim explains a
window. Ranking the basket by attention would let the index select its own
inputs, which is the defect that retired trends_victims.
"""

import pandas as pd

from config import DATA_REFERENCE


def load_attention():
    """Per-person daily Wikipedia attention. Raises if the inputs are absent.

    Refuses to run rather than falling back to the retired ranking. A silent
    fallback is how the Twitter dependency survived being 'removed'.
    """
    pv_path = DATA_REFERENCE / "wiki_pageviews_by_article.csv"
    dec_path = DATA_REFERENCE / "basket_decisions.csv"
    missing = [p.name for p in (pv_path, dec_path) if not p.exists()]
    if missing:
        raise SystemExit(
            f"episode attribution needs {missing}. Run "
            "11_fetch_awareness_components.py --only wiki_ext and "
            "27_finalise_basket.py --apply first. Refusing to fall back to the "
            "retired Twitter ranking (findings E5, L6, R2).")

    pv = pd.read_csv(pv_path, parse_dates=["date"])
    dec = pd.read_csv(dec_path)
    pv["person_key"] = pv["article"].map(
        dec.set_index("article")["person"].to_dict()).str.lower()
    return pv.dropna(subset=["person_key"])


def label_window(reg, attention, lo, hi, lookback_days, top=2):
    """Name the victims who actually drew attention between lo and hi.

    `reg` is the victim registry, `attention` the frame from load_attention().
    Returns a "; "-joined label, empty when no candidate has any pageviews.
    """
    start = lo - pd.Timedelta(days=lookback_days)
    near = reg[(reg["date"] >= start) & (reg["date"] <= hi)]
    if near.empty:
        return ""
    w = attention[(attention["date"] >= start) & (attention["date"] <= hi)]
    prom = w.groupby("person_key")["views"].sum()
    near = near.assign(prom=near["name"].str.lower().map(prom).fillna(0.0))
    named = near[near["prom"] > 0].sort_values("prom", ascending=False)
    return "; ".join(named["name"].head(top))
