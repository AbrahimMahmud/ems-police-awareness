"""Measure the April 2020 Wikipedia agent-class break, and bound what it moves.

WHY THIS EXISTS (finding L7)
-----------------------------
wiki_ext is built from Wikimedia pageviews requested with `agent=user`. Before
late April 2020 that filter had two classes to choose from, "user" and "spider";
in April 2020 Wikimedia added a third, "automated", and DID NOT APPLY IT
RETROACTIVELY. So `user` means "not obviously a spider" before the change and
"not a spider and not automated" after it, and the series measures a
systematically different quantity either side of a date five weeks before the
largest episode in the study.

The standardisation window compounds it: CAI-D is standardised on 2017-2019,
entirely before the break, while the Floyd episode lies entirely after it.

WHY THE OBVIOUS FIX IS BACKWARDS
---------------------------------
The finding proposed refetching under `agent=all-agents`. That is the wrong
direction: all-agents ADDS spider traffic, which is a different and larger
contamination than the one being corrected. The comparable series is
`user + automated` after the break against `user` before it — which is what the
pre-April-2020 `user` class already was.

WHAT THIS SCRIPT ESTABLISHES
-----------------------------
The break's SIZE on the titles the index is actually built from, rather than
WMF's aggregate figure for all of English Wikipedia. Those are different
quantities and the difference is an order of magnitude: the 5-8% bot-spam figure
in the finding is a 2019 desktop-wide aggregate, and these articles are not
typical of English Wikipedia.

Outputs:
  data/reference/wiki_agent_class_break.csv
      per year: user views, automated views, automated share, and the implied
      shift in standard deviations of log1p(wiki_ext)
"""

import argparse

import numpy as np
import pandas as pd

import wikimedia as wm
from config import (basket_articles_file, DATA_PROCESSED, DATA_REFERENCE)
from provenance import log_source

PV_CACHE = DATA_PROCESSED / "wiki_pageviews_cache"
START, END = "20150701", "20241231"

ap = argparse.ArgumentParser()
ap.add_argument("--basket", default=None, help="default: config.CAI_D_BASKET")
ARGS = ap.parse_args()

res = pd.read_csv(DATA_REFERENCE / basket_articles_file(ARGS.basket))
titles = sorted(res["article"].dropna().unique())
print(f"agent-class break: {len(titles)} basket articles")

rows, failed = [], []
for i, t in enumerate(titles, 1):
    try:
        items = wm.pageviews_items(t, START, END, agent="automated", cache_dir=PV_CACHE)
    except wm.NotFound:
        items = []                      # a real 404: no automated traffic recorded
    except Exception as e:
        failed.append((t, f"{type(e).__name__}: {e}"))
        continue
    for d in items:
        rows.append({"article": t, "date": d["timestamp"][:8], "automated": d["views"]})
    if i % 25 == 0:
        print(f"  {i}/{len(titles)}", flush=True)

# REFUSE ON A PARTIAL FETCH. A break measured from a subset of the basket
# understates itself by exactly the articles that failed, and the failure would
# be invisible in the output — the T15 defect, which this project has already
# shipped once.
if failed:
    raise SystemExit(
        f"{len(failed)} article(s) failed and the break cannot be measured from a "
        f"subset: {failed[:3]}. Re-run; the cache makes it resumable.")

auto = pd.DataFrame(rows)
auto["date"] = pd.to_datetime(auto["date"])

user = pd.read_csv(DATA_REFERENCE / "wiki_pageviews_by_article.csv",
                   parse_dates=["date"])
user = user[user["article"].isin(titles)]

u = user.groupby("date")["views"].sum().rename("user")
a = auto.groupby("date")["automated"].sum().rename("automated")
day = pd.concat([u, a], axis=1).fillna(0.0)
day["share"] = day["automated"] / (day["user"] + day["automated"]).replace(0, np.nan)

# The break's effect on the INDEX is a shift in log1p space, because that is
# where wiki_ext is standardised. Adding back the automated views raises
# log1p(user) to log1p(user + automated); the shift is measured in SDs of
# log1p(wiki_ext) over the standardisation window, which is what a z-score moves by.
ref = day.loc["2017-01-01":"2019-12-31", "user"]
sd_ref = float(np.log1p(ref).std())
day["z_shift"] = (np.log1p(day["user"] + day["automated"])
                  - np.log1p(day["user"])) / sd_ref

out = (day.groupby(day.index.year)
          .agg(user=("user", "sum"), automated=("automated", "sum"),
               mean_share=("share", "mean"), max_share=("share", "max"),
               mean_z_shift=("z_shift", "mean"), max_z_shift=("z_shift", "max"))
          .reset_index(names="year"))
out["share_of_total"] = out["automated"] / (out["user"] + out["automated"])
out.to_csv(DATA_REFERENCE / "wiki_agent_class_break.csv", index=False)

first_nonzero = day.index[day["automated"] > 0].min()
print(f"\nSD of log1p(wiki_ext) on the 2017-2019 reference window: {sd_ref:.4f}")
print(f"first day with any automated traffic: {first_nonzero.date()}")
print(out.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

log_source("S19",
           f"Wikipedia agent=automated daily series for the {ARGS.basket or 'strict'} "
           f"basket, {len(titles)} articles, used to size the April 2020 agent-class "
           f"break; first nonzero {first_nonzero.date()}",
           "https://wikimedia.org/api/rest_v1 (agent=automated)",
           out_file=DATA_REFERENCE / "wiki_agent_class_break.csv")
