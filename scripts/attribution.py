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


def label_drivers(attention, lo, hi, top=3, min_share=0.02):
    """Name the ARTICLES that actually drove attention in a window.

    label_window() answers "which recently-killed person in the registry drew the
    most attention here", and it gates on the registry FIRST: if nobody in the
    registry died within the lookback, it returns an empty label no matter how
    much attention the window contains. That is the right shape for a question
    about victims and the wrong shape for describing an episode, and the cost is
    measurable — 33 of 74 episodes (45%), and 16 of 29 in discovery, carry no
    label at all.

    Among them is the second-largest discovery episode in the study,
    2020-08-24..09-07, peak index 9.01. Nothing in the registry explains it,
    because the two things that drove it are invisible to a registry of
    KILLINGS keyed on DATE OF DEATH: Jacob Blake was shot on 2020-08-23 and
    survived, and Daniel Prude's death became public when the video was released
    on 2020-09-02, five months after he died — and Prude is absent from Mapping
    Police Violence entirely (finding T9). Widening the lookback does not fix
    this and makes labelling worse (finding E7): it lets long-past deaths capture
    episodes driven by something else.

    This labels the window by what the TREATMENT SERIES itself says drove it —
    the basket articles people actually read — which needs no registry, no death
    date, and no assumption that the trigger was a death at all. On the episode
    above it returns Jacob Blake at 62% of basket views, eight times the next
    article. It is reported BESIDE the registry label rather than replacing it:
    the two answer different questions, and where they disagree that is a fact
    about the episode worth seeing.

    Shares are of total basket views in the window, so they say how concentrated
    an episode is — which is the measurable form of "this period cannot separate
    individual killings" (finding E8).
    """
    w = attention[(attention["date"] >= lo) & (attention["date"] <= hi)]
    if w.empty:
        return "", 0.0
    tot = float(w["views"].sum())
    if tot <= 0:
        return "", 0.0
    # BY PERSON, NOT BY ARTICLE. English Wikipedia carries both
    # "Murder_of_George_Floyd" and "George_Floyd", so ranking articles splits one
    # person's attention across two rows and prints "George Floyd (20%); George
    # Floyd (11%)" — which reads as a data error and understates the
    # concentration it is meant to measure. This is the same duplicate-person
    # collapse already fixed for the wiki_ext sum itself (T.no_duplicate_person);
    # it had to be applied here too, because the label is a second consumer of
    # the same per-article series.
    key = "person_key" if "person_key" in w.columns else "article"
    share = w.groupby(key)["views"].sum().sort_values(ascending=False) / tot
    keep = share[share >= min_share].head(top)
    label = "; ".join(f"{_name(k)} ({v:.0%})" for k, v in keep.items())
    return label, float(share.iloc[0])


_PREFIXES = ("Killing_of_", "Shooting_of_", "Death_of_", "Murder_of_",
             "Police_shooting_of_")


def _name(key):
    """Grouping key -> a human-readable name.

    person_key is already a lowercased person name; an article title needs its
    "Killing_of_" style prefix stripped.
    """
    for p in _PREFIXES:
        if key.startswith(p):
            return key[len(p):].replace("_", " ")
    return key.replace("_", " ").title() if key.islower() else key.replace("_", " ")


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
