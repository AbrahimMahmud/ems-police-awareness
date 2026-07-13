"""Fetch Google Trends daily series 2015-2024, US and NYC metro (CAI-D tier).

Trends returns daily granularity only for windows <= ~9 months, and each
window is internally rescaled 0-100. We therefore fetch 180-day chunks with
60-day overlaps and chain-scale successive chunks by the ratio of means over
the overlap (standard stitching). Term: "police brutality" (search term;
robust across the decade). Geos: US (national) and US-NY-501 (NYC DMA).

Output: data/reference/cai_trends_daily.csv (date, component, value)
"""

import hashlib
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

from config import DATA_REFERENCE

TERM = "police brutality"
GEOS = {"trends_us": "US", "trends_nyc": "US-NY-501"}
START, END = pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31")
CHUNK, OVERLAP = 180, 60

pt = TrendReq(hl="en-US", tz=0, timeout=(10, 30), retries=3, backoff_factor=2)
rows = []
for comp, geo in GEOS.items():
    stitched = None
    t0 = START
    while t0 <= END:
        t1 = min(t0 + pd.Timedelta(days=CHUNK - 1), END)
        tf = f"{t0.date()} {t1.date()}"
        for attempt in range(4):
            try:
                pt.build_payload([TERM], timeframe=tf, geo=geo)
                df = pt.interest_over_time()
                break
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(20 * (attempt + 1))
        s = df[TERM].astype(float)
        s.index = pd.to_datetime(s.index)
        if stitched is None:
            stitched = s
        else:
            ov = stitched.index.intersection(s.index)
            prev_m, new_m = stitched.loc[ov].mean(), s.loc[ov].mean()
            scale = (prev_m / new_m) if new_m > 0 else 1.0
            s = s * scale
            stitched = pd.concat([stitched, s[~s.index.isin(stitched.index)]])
        t0 = t1 - pd.Timedelta(days=OVERLAP - 1)
        if t1 == END:
            break
        time.sleep(8)
    stitched = stitched.sort_index()
    for d, v in stitched.items():
        rows.append({"date": d, "component": comp, "value": v})
    print(f"{comp}: {len(stitched):,} days, peak {stitched.idxmax().date()} ({stitched.max():.1f})")

out = pd.DataFrame(rows)
path = DATA_REFERENCE / "cai_trends_daily.csv"
out.to_csv(path, index=False)
log = pd.DataFrame([{
    "source_id": "S12", "description": f"Google Trends daily '{TERM}', US + NYC DMA 501, stitched 180d/60d",
    "url": "https://trends.google.com (via pytrends)",
    "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "output_file": str(path),
}])
lp = DATA_REFERENCE / "data_sources.csv"
log.to_csv(lp, mode="a", header=not lp.exists(), index=False)
