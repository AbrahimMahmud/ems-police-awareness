"""Fetch Google Trends daily series 2015-2024, US and NYC metro (CAI-D tier).

Trends returns daily granularity only for windows <= ~9 months, and each window
is internally rescaled 0-100, so a decade has to be fetched in chunks and
chain-stitched.

2026-09-10 REWRITE — two defects, findings T1 and T3/L3.

T3/L3 — THE SERIES WAS A CENSORED INDICATOR, NOT A LEVEL.
The query was the single literal term "police brutality". In the NYC DMA that
sits at Google's low-volume reporting floor: 79% of days exactly zero overall,
rising from 55% censored in 2020 to 98% in 2024. trends_nyc is the ONLY
nominally city-local component of CAI-D, so the paper's locality claim rested
entirely on a series that is mostly zeros.

Measured alternatives (NYC DMA, share of days exactly zero):

    query                          quiet 2023   loud 2020   distinct (quiet)
    term "police brutality"            84.4%       44.8%           14
    topic /m/016497                    73.3%       35.9%           17
    topic /m/0bwkkxd (US-specific)     99.4%       99.4%            2
    topic + 2 phrases  <- CHOSEN       40.6%       22.1%           39
    topic + 4 phrases                  40.0%       21.0%           40

So the topic entity ALONE does not fix it — that is worth stating plainly,
because "use the topic" was the obvious repair and it buys 84% -> 73%. The
basket is what works. The 4th and 5th terms buy essentially nothing (40.6 ->
40.0) while costing payload slots, so the basket stops at three.

HONEST LIMIT: 40% of quiet-period days are STILL censored. This is a large
improvement, not a solved problem, and the paper must not claim otherwise. The
residual censoring is why trends_nyc should also be reported as a censored
indicator in sensitivity (finding T3's option b), not treated as a clean level.

Terms are fetched in ONE payload so Trends normalises them against a common
maximum; only then is summing them meaningful. Terms fetched in separate
payloads are on different scales and must never be summed.

Deliberately excluded from the basket: bare "police" (recruitment, precinct
hours, scanner traffic), "BLM" (a movement, not an incident), and victim names —
the last is the endogeneity that retired trends_victims, since a victim series
only exists once volume clears the floor, i.e. on high-attention days.

T1 — THE STITCHER SILENTLY RESET THE SCALE.
The old link was `scale = prev_mean / new_mean` with a fallback to 1.0 when the
new mean was zero. The 2021-05-29..09-25 NYC chunk was all zeros, so the chain
reset and trends_nyc gained a ~4.5x artificial level break at 2021-09-26 — half
of 2022's threshold crossings were that artifact.

A silent fallback is the wrong response to "I cannot compute the link": it
produces a number that looks like a measurement. This now fits the link through
the origin on JOINTLY POSITIVE overlap days, requires a minimum number of them
spread over a minimum span, and ABORTS with the diagnostics rather than guessing.

Output: data/reference/cai_trends_daily.csv (date, component, value)
"""

import time

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

from config import DATA_REFERENCE
from provenance import log_source

# One payload, common normalisation. See the docstring for what is excluded.
TOPIC = "/m/016497"                      # Google Trends topic entity "Police brutality"
TERMS = [TOPIC, "police shooting", "police killed"]
TERM_LABELS = {TOPIC: "topic:Police brutality"}

GEOS = {"trends_us": "US", "trends_nyc": "US-NY-501"}
START, END = pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31")
CHUNK, OVERLAP = 180, 60

# Stitching gates. A link estimated from three positive days that happen to sit
# in one week is not a link; it is a coincidence with a slope.
MIN_OVERLAP_POSITIVE = 10        # jointly-positive days required
MIN_OVERLAP_SPAN_DAYS = 21       # those days must span at least this many days


class StitchFailure(RuntimeError):
    """The chunk link cannot be estimated. Never fall back to a guess."""


def fetch(pt, terms, timeframe, geo, tries=4):
    """One payload, summed across terms on their common scale."""
    for attempt in range(tries):
        try:
            pt.build_payload(terms, timeframe=timeframe, geo=geo)
            df = pt.interest_over_time()
            break
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(20 * (attempt + 1))
    if df is None or df.empty:
        raise StitchFailure(f"empty response for {geo} {timeframe}")
    cols = [c for c in df.columns if c != "isPartial"]
    s = df[cols].astype(float).sum(axis=1)
    s.index = pd.to_datetime(s.index)
    return s


def link(prev, new):
    """Scale factor putting `new` on `prev`'s scale, or raise.

    Through-origin least squares on jointly-positive days: b = sum(pq)/sum(qq).
    A ratio of means (the old rule) is dominated by whichever days happen to be
    large and is undefined when the new chunk is all zeros — which is exactly
    the case that produced the 4.5x break.
    """
    ov = prev.index.intersection(new.index)
    if len(ov) == 0:
        raise StitchFailure("chunks do not overlap at all")
    p = prev.loc[ov].to_numpy(float)
    q = new.loc[ov].to_numpy(float)
    j = (p > 0) & (q > 0)
    n_pos = int(j.sum())
    span = 0
    if n_pos:
        days = ov[j]
        span = int((days.max() - days.min()).days) + 1
    if n_pos < MIN_OVERLAP_POSITIVE or span < MIN_OVERLAP_SPAN_DAYS:
        raise StitchFailure(
            f"overlap too thin to estimate a link: {n_pos} jointly-positive days "
            f"(need {MIN_OVERLAP_POSITIVE}) spanning {span} days "
            f"(need {MIN_OVERLAP_SPAN_DAYS}). Overlap {ov.min().date()}..{ov.max().date()}, "
            f"prev>0 on {int((p > 0).sum())}, new>0 on {int((q > 0).sum())}. "
            "Refusing to fall back to scale=1.0 — that is what produced the "
            "4.5x break at 2021-09-26 (finding T1).")
    b = float((p[j] * q[j]).sum() / (q[j] * q[j]).sum())
    resid = p[j] - b * q[j]
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((p[j] - p[j].mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return b, n_pos, span, r2


pt = TrendReq(hl="en-US", tz=0, timeout=(10, 30))  # no retries kwarg: pytrends
# passes the removed urllib3 'method_whitelist' argument; fetch() retries instead.

rows, diagnostics = [], []
for comp, geo in GEOS.items():
    stitched, t0, n_chunks = None, START, 0
    while t0 <= END:
        t1 = min(t0 + pd.Timedelta(days=CHUNK - 1), END)
        s = fetch(pt, TERMS, f"{t0.date()} {t1.date()}", geo)
        n_chunks += 1
        if stitched is None:
            stitched = s
        else:
            b, n_pos, span, r2 = link(stitched, s)
            diagnostics.append({"component": comp, "boundary": str(t0.date()),
                                "scale": round(b, 4), "n_positive": n_pos,
                                "span_days": span, "r2": round(r2, 4)})
            s = s * b
            stitched = pd.concat([stitched, s[~s.index.isin(stitched.index)]])
        t0 = t1 - pd.Timedelta(days=OVERLAP - 1)
        if t1 == END:
            break
        time.sleep(8)
    stitched = stitched.sort_index()
    for d, v in stitched.items():
        rows.append({"date": d, "component": comp, "value": v})
    zero = float((stitched == 0).mean())
    print(f"{comp}: {len(stitched):,} days over {n_chunks} chunks, "
          f"peak {stitched.idxmax().date()} ({stitched.max():.1f}), "
          f"{zero:.1%} exactly zero, {stitched.nunique()} distinct values")

out = pd.DataFrame(rows)
path = DATA_REFERENCE / "cai_trends_daily.csv"
out.to_csv(path, index=False)

# Stitch diagnostics are committed, not printed and lost: every scale factor the
# chain applied is inspectable, so a future break can be traced to its boundary.
diag = pd.DataFrame(diagnostics)
diag.to_csv(DATA_REFERENCE / "cai_trends_stitch_diagnostics.csv", index=False)
print(f"\nstitch links: {len(diag)} boundaries, "
      f"scale range {diag['scale'].min():.3f}-{diag['scale'].max():.3f}, "
      f"min r2 {diag['r2'].min():.3f}")

# Provenance records REALISED coverage, not the intended span (finding T7).
realised = out.groupby("component")["date"].agg(["min", "max", "count"])
log_source(
    "S12",
    (f"Google Trends daily, basket {TERMS} summed on one payload scale, "
                    f"US + NYC DMA 501, stitched {CHUNK}d/{OVERLAP}d through-origin; "
                    f"realised " + "; ".join(
                        f"{c}={r['min'].date()}..{r['max'].date()} n={r['count']}"
                        for c, r in realised.iterrows())),
    "https://trends.google.com (via pytrends)",
    out_file=path)
