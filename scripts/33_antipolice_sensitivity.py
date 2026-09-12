"""What excluding attention to violence AGAINST police does to the index.

WHY THIS EXISTS
---------------
32_validate_basket_construct.py drops two articles from every basket because
they measure the opposite construct: Micah Xavier Johnson, who shot five Dallas
police officers on 2016-07-07, and Gonzalo Lopez, a fugitive who murdered six
people. Attention to an attack ON police is not attention to police violence, and
summing it into CAI-D would put the two in the same direction.

That exclusion is easy to justify and easy to under-state, because it lands on
the most load-bearing day in the whole project. 2016-07-08 — the Alton Sterling
and Philando Castile week — is the index's highest day and its strongest content
validation, and it is also the day after the Dallas attack. A reader is entitled
to ask whether the peak was ever about Sterling and Castile at all.

So the difference is MEASURED rather than asserted. This rebuilds the index with
the two articles added back, through the same log1p -> standardise -> average ->
re-standardise pipeline 12_build_cai.py uses, and reports both.

It is a SENSITIVITY EXHIBIT, not an alternative index. Nothing downstream reads
its output.

Outputs:
  outputs/tables/antipolice_sensitivity.csv   both series on the top days, plus
      the summary rows the paper quotes
"""

import numpy as np
import pandas as pd

import wikimedia as wm
from config import CAI_D_COMPONENTS, DATA_PROCESSED, DATA_REFERENCE, OUTPUTS_TABLES

PV_CACHE = DATA_PROCESSED / "wiki_pageviews_cache"
STD_WINDOW = ("2017-01-01", "2019-12-31")   # must match 12_build_cai.py:48

# Titles are listed explicitly rather than resolved, because these articles are
# deliberately NOT in the basket and so have no entry in the title map.
ANTI_POLICE = {
    "Micah_Xavier_Johnson": ["Micah Xavier Johnson",
                             "2016 shooting of Dallas police officers"],
    "Gonzalo_Lopez": ["Gonzalo Lopez"],
}
PEAK = pd.Timestamp("2016-07-08")


def build_index(wide):
    """12_build_cai.py's construction, applied to whatever components are given."""
    std = pd.DataFrame(index=wide.index)
    for c in CAI_D_COMPONENTS:
        x = np.log1p(wide[c])
        ref = x.loc[STD_WINDOW[0]:STD_WINDOW[1]]
        std[c] = (x - ref.mean()) / ref.std(ddof=0)
    ok = std[list(CAI_D_COMPONENTS)].notna().all(axis=1)
    raw = std.loc[ok, list(CAI_D_COMPONENTS)].mean(axis=1)
    ref = raw.loc[STD_WINDOW[0]:STD_WINDOW[1]]
    return (raw - ref.mean()) / ref.std(ddof=0)


def main():
    extra, per_article = {}, []
    for art, titles in ANTI_POLICE.items():
        tot = {}
        for t in titles:
            try:
                for it in wm.pageviews_items(t, "20150701", "20241231", cache_dir=PV_CACHE):
                    tot[it["timestamp"][:8]] = tot.get(it["timestamp"][:8], 0) + it["views"]
            except wm.NotFound:
                print(f"  no series for title: {t}")
        per_article.append({"article": art, "days": len(tot),
                            "views": int(sum(tot.values()))})
        print(f"{art}: {len(tot)} days, {sum(tot.values()):,} views")
        for d, v in tot.items():
            extra[d] = extra.get(d, 0) + v

    parts = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"]),
             pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])]
    wide = (pd.concat(parts, ignore_index=True)
            .pivot_table(index="date", columns="component", values="value", aggfunc="sum"))

    base = build_index(wide)
    w2 = wide.copy()
    add = pd.Series({pd.Timestamp(d): v for d, v in extra.items()}).reindex(w2.index).fillna(0)
    w2["wiki_ext"] = w2["wiki_ext"] + add
    alt = build_index(w2)

    diff = (alt - base).dropna()
    peak_base, peak_alt = float(base.get(PEAK)), float(alt.get(PEAK))
    rank_base = base.sort_values(ascending=False).index.get_loc(PEAK) + 1
    rank_alt = alt.sort_values(ascending=False).index.get_loc(PEAK) + 1

    print(f"\nindex days {len(base)}; the excluded articles have traffic on "
          f"{int((add > 0).sum())} of them")
    print(f"largest change anywhere: {diff.abs().max():.4f} SD on "
          f"{diff.abs().idxmax().date()}")
    print(f"\n2016-07-08  published {peak_base:.4f} (rank {rank_base})"
          f"   counterfactual {peak_alt:.4f} (rank {rank_alt})")
    print(f"  views the excluded articles add that day: {extra.get('20160708', 0):,}")

    rows = [{"metric": "excluded_articles", "value": len(ANTI_POLICE)},
            {"metric": "excluded_views_total", "value": sum(a["views"] for a in per_article)},
            {"metric": "index_days", "value": len(base)},
            {"metric": "days_touched_by_excluded", "value": int((add > 0).sum())},
            {"metric": "max_abs_change_sd", "value": round(float(diff.abs().max()), 4)},
            {"metric": "max_abs_change_date", "value": str(diff.abs().idxmax().date())},
            {"metric": "peak_2016_07_08_published", "value": round(peak_base, 4)},
            {"metric": "peak_2016_07_08_counterfactual", "value": round(peak_alt, 4)},
            {"metric": "peak_2016_07_08_rank_published", "value": int(rank_base)},
            {"metric": "peak_2016_07_08_rank_counterfactual", "value": int(rank_alt)},
            {"metric": "views_added_on_2016_07_08", "value": int(extra.get("20160708", 0))}]
    top = base.sort_values(ascending=False).head(10)
    for dt, v in top.items():
        rows.append({"metric": f"top_day_{dt.date()}_published", "value": round(float(v), 4)})
        rows.append({"metric": f"top_day_{dt.date()}_counterfactual",
                     "value": round(float(alt.get(dt)), 4)})
    out = OUTPUTS_TABLES / "antipolice_sensitivity.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nwrote {out.name}")


if __name__ == "__main__":
    main()
