"""Wikipedia title logic, owned in one place.

Two scripts build a pageview basket — 11_fetch_awareness_components.py for the
national wiki_ext series and 28_build_nyc_attention.py for the NYC validation
exhibit — and both need the same two rules. Writing them twice is how the
Daniel_Prude collapse came to exist in 28 and not in 11, which left NINE victims
double-counted in the treatment index for a day.

RULE 1: SUM ACROSS HISTORICAL TITLES.
Wikimedia attributes a pageview to the exact title requested and does not carry
views across a page move, so a victim's attention is split across every title
their article has ever had. Fetching only the current canonical title discards
everything before the rename, including the spike at the moment of death.

RULE 2: COLLAPSE ARTICLES THAT ARE THE SAME PERSON.
Because of rule 1, an article already includes the views of every title it has
had. If one of those titles is ALSO admitted as an article in its own right, that
person enters the basket twice. Measured in wiki_ext before this was applied:
Eric_Garner (280,937 views) alongside Killing_of_Eric_Garner, Freddie_Gray
(91,238) alongside Killing_of_Freddie_Gray, and seven more — 449,549 views, 0.35%
of the basket, concentrated in exactly the victims whose articles were renamed.
It also corrupted episode attribution, labelling two episodes with the bare-name
title rather than the canonical one.
"""

import pandas as pd

from config import DATA_REFERENCE

TITLE_MAP_CSV = DATA_REFERENCE / "article_title_map.csv"


def load_title_map(path=None):
    """article -> [titles]. Returns {} if the map has not been built.

    Callers decide what an absent map means. 11 and 28 both REFUSE to run
    without it rather than silently falling back to canonical-title-only
    fetching, because that silent fallback is how the rename defect survived
    being diagnosed and having a fix written for it.
    """
    f = path or TITLE_MAP_CSV
    if not f.exists():
        return {}
    d = pd.read_csv(f)
    return d.groupby("article")["title"].apply(list).to_dict()


def alias_index(title_map):
    """title -> [articles that list it as a historical title], excluding self."""
    out = {}
    for article, titles in title_map.items():
        for t in titles:
            if t != article:
                out.setdefault(t, []).append(article)
    return out


def duplicate_articles(articles, title_map):
    """Which of `articles` are a historical title of another one of `articles`.

    Returns {duplicate: [canonical, ...]}. Order-independent: it looks only at
    the title map, so it cannot depend on which article happened to be processed
    first.
    """
    kept = set(articles)
    alias = alias_index(title_map)
    return {a: [o for o in alias[a] if o in kept and o != a]
            for a in sorted(kept)
            if a in alias and any(o in kept and o != a for o in alias[a])}


def collapse_duplicates(articles, title_map, log=print):
    """Drop articles that duplicate a person already in the basket.

    Returns (kept_articles, dropped_map). Every drop is logged with the article
    it duplicates, because a basket that silently shrinks is indistinguishable
    from one that was always that size.
    """
    dupes = duplicate_articles(articles, title_map)
    if not dupes:
        return list(articles), {}
    for a, owners in dupes.items():
        log(f"  --  {a}: dropped, it is a historical title of {owners[0]}, "
            f"which is already in the basket")
    log(f"  collapsed {len(dupes)} duplicate article(s)")
    return [a for a in articles if a not in dupes], dupes
