"""Download the EMS extract directly from NYC OpenData (replaces the local run
of 00 now that network access allows it). Paged SODA API, 7 columns only.

Produces the same two files as 00_local_ems_extract.py:
  data/processed/ems_cd_day_calltype.parquet   (2014-12-01..2024-12-31)
  data/processed/ems_citywide_day_trends.parquet (2005..latest)
Progress prints per page (observability lesson applied).
"""

import io
import json
import time
import urllib.request

import pandas as pd

from config import DATA_PROCESSED
from provenance import log_source

BASE = "https://data.cityofnewyork.us/resource/76xm-jjuj.csv"
COLS = ("incident_datetime,communitydistrict,final_call_type,"
        "incident_disposition_code,special_event_indicator,standby_indicator,transfer_indicator")
PAGE = 500_000
UA = {"User-Agent": "ems-police-awareness-research/1.0", "Accept": "text/csv"}

# Pages ordered by :id (indexed, fast) and written to disk immediately;
# rerunning resumes from existing page files.
from pathlib import Path
PAGES_DIR = DATA_PROCESSED / "ems_pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)
offset = 0
pages_cached = pages_downloaded = 0
while True:
    pf = PAGES_DIR / f"page_{offset:09d}.parquet"
    if pf.exists():
        n = len(pd.read_parquet(pf, columns=["incident_datetime"]))
        pages_cached += 1
        print(f"offset {offset:,}: cached ({n:,} rows)", flush=True)
        if n < PAGE:
            break
        offset += PAGE
        continue
    url = f"{BASE}?$select={COLS}&$order=:id&$limit={PAGE}&$offset={offset}"
    url = url.replace(" ", "%20")
    for attempt in range(5):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600).read()
            break
        except Exception as e:
            print(f"offset {offset:,}: retry {attempt+1} ({e})", flush=True)
            time.sleep(30 * (attempt + 1))
    else:
        raise RuntimeError(f"page failed at offset {offset}")
    df = pd.read_csv(io.BytesIO(raw), dtype=str, low_memory=False)
    if len(df) == 0:
        break
    df.to_parquet(pf, index=False)
    pages_downloaded += 1
    print(f"offset {offset:,}: {len(df):,} rows", flush=True)
    if len(df) < PAGE:
        break
    offset += PAGE

ems = pd.concat([pd.read_parquet(p) for p in sorted(PAGES_DIR.glob("page_*.parquet"))],
                ignore_index=True)
print(f"Total rows downloaded: {len(ems):,}")

# --- same filters as 00_local_ems_extract.py ---
ems["incident_ts"] = pd.to_datetime(ems["incident_datetime"], errors="coerce")
for c in ["special_event_indicator", "standby_indicator", "transfer_indicator"]:
    ems[c] = ems[c].astype(str).str.strip().str.upper()
ems["disp"] = ems["incident_disposition_code"].astype(str).str.strip().str.upper()
ems["final_call_type"] = ems["final_call_type"].astype(str).str.strip().str.upper()
truthy = {"Y", "YES", "TRUE", "1"}
excl_disp = {"CANCEL", "NOTSNT", "DUP", "87"}
keep = (
    ems["incident_ts"].notna()
    & ~ems["special_event_indicator"].isin(truthy)
    & ~ems["standby_indicator"].isin(truthy)
    & ~ems["transfer_indicator"].isin(truthy)
    & ~ems["disp"].isin(excl_disp)
)
# FINDING O1 — the cancelled dispatches are kept, in their own artifact.
#
# The disposition filter drops CANCEL / NOTSNT / DUP / 87, and it does so
# DIFFERENTIALLY: measured on the discovery window, it removes 7.47% of EDP calls
# against 0.76-0.77% of altmen and asthma — a 9.9x ratio across families with
# more than 10,000 calls — and within EDP it swings from 6.28% (2017) to 8.75%
# (2019).
#
# That matters because of what the outcome MEANS here. A cancelled EDP dispatch
# is still someone calling 911 about a mental-health crisis; the hypothesis is
# about what New Yorkers ASK FOR, not about what EMS ultimately did. Filtering
# them out is defensible as the standard definition of a real dispatch, but it is
# a choice, and it removes the calls most likely to be affected.
#
# Measured effect on the outcome (discovery window, 86,140 district-days): the
# mean mental-health share rises from 0.1083 to 0.1119, +3.3%, and the two series
# correlate 0.9758. Small — but "small" is a finding, not an assumption, and it
# could only be established by keeping the counts.
#
# So the primary extract still applies the filter, and the excluded calls are
# written alongside it so the sensitivity can actually be run rather than merely
# promised in a limitations section.
excluded = ems[~keep].copy()
ems = ems[keep].copy()
ems["incident_date"] = ems["incident_ts"].dt.normalize()
ems["communitydistrict"] = pd.to_numeric(ems["communitydistrict"], errors="coerce")
print(f"After filters: {len(ems):,} rows")

# Extract 1: CD x day x call type, 2014-12..2024-12
win = ems[ems["incident_date"].between("2014-12-01", "2024-12-31")]

# dropna=False is load-bearing (finding O4). communitydistrict is coerced with
# errors="coerce", so every unparseable district becomes NaN, and pandas drops
# NaN group keys by DEFAULT — silently, and before any QC metric is computed.
# The excluded-volume number therefore understated the true loss, and the
# geocoding regime change at 2015-12-31 (missing-CD 3.12% -> 0.63%, finding O2)
# was invisible in it. Keep the NaN group, count it, then let the downstream
# panel filter to VALID_CDS knowingly rather than by accident.
g1 = (win.groupby(["incident_date", "communitydistrict", "final_call_type"], dropna=False)
      .size().rename("n_calls").reset_index())

miss = g1["communitydistrict"].isna()
miss_share = float(g1.loc[miss, "n_calls"].sum() / max(g1["n_calls"].sum(), 1))
print(f"  missing community district: {int(g1.loc[miss, 'n_calls'].sum()):,} calls "
      f"({miss_share:.2%} of in-window volume) — retained as NaN, not dropped")
by_year = (g1.assign(year=g1["incident_date"].dt.year)
             .groupby(["year", g1["communitydistrict"].isna()])["n_calls"].sum()
             .unstack(fill_value=0))
if True in by_year.columns:
    rate = (by_year[True] / by_year.sum(axis=1)).round(4)
    print("  missing-CD share by year:")
    print(rate.to_string())
out1 = DATA_PROCESSED / "ems_cd_day_calltype.parquet"
g1.to_parquet(out1, index=False)

# The excluded calls, same grain, so mh_share_incl_cancelled is a join away.
excluded["incident_date"] = excluded["incident_ts"].dt.normalize()
excluded["communitydistrict"] = pd.to_numeric(excluded["communitydistrict"], errors="coerce")
ex_win = excluded[excluded["incident_date"].between("2014-12-01", "2024-12-31")]
gx = (ex_win.groupby(["incident_date", "communitydistrict", "final_call_type",
                      "disp"], dropna=False)
      .size().rename("n_calls").reset_index())
outx = DATA_PROCESSED / "ems_cd_day_calltype_excluded.parquet"
gx.to_parquet(outx, index=False)
print(f"Wrote {outx}: {len(gx):,} rows, "
      f"{int(gx['n_calls'].sum()):,} excluded calls "
      f"({gx['n_calls'].sum() / (g1['n_calls'].sum() + gx['n_calls'].sum()):.2%} of in-window volume)")
print(f"Wrote {out1}: {len(g1):,} rows, {g1['incident_date'].min()} -> {g1['incident_date'].max()}")

# Extract 2: citywide daily trends, full period
MH = {"EDP": "edp", "EDPC": "edp", "EDPM": "edp", "EDPW": "edp", "T-EDP": "edp",
      "ALTMEN": "altmen", "ALTMFC": "altmen", "ALTMFT": "altmen",
      "JUMPDN": "suicide_jump", "JUMPUP": "suicide_jump",
      "DRUG": "od_poison_drug", "DRUGFC": "od_poison_drug"}
ems["call_group"] = ems["final_call_type"].map(MH).fillna("other")
g2 = ems.groupby(["incident_date", "call_group"]).size().rename("n_calls").reset_index()
out2 = DATA_PROCESSED / "ems_citywide_day_trends.parquet"
g2.to_parquet(out2, index=False)
print(f"Wrote {out2}: {len(g2):,} rows")

# Say whether this run actually fetched anything. accessed_utc otherwise claims a
# download that did not happen: re-running on cached pages rewrites the artifact
# from bytes fetched days earlier, and a register that cannot tell those apart
# slowly stops meaning anything.
_src = (f"{pages_downloaded} page(s) downloaded, {pages_cached} read from cache"
        if pages_downloaded else
        f"NO NETWORK FETCH — rebuilt from {pages_cached} cached page(s)")
log_source(
    "S1b",
    "EMS Incident Dispatch Data via SODA API (7 columns, paged), replaces "
    f"user-local export; {_src}",
    BASE, out_file=out1)
