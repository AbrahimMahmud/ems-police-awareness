"""Download the EMS extract directly from NYC OpenData (replaces the local run
of 00 now that network access allows it). Paged SODA API, 7 columns only.

Produces the same two files as 00_local_ems_extract.py:
  data/processed/ems_cd_day_calltype.parquet   (2014-12-01..2024-12-31)
  data/processed/ems_citywide_day_trends.parquet (2005..latest)
Progress prints per page (observability lesson applied).
"""

import hashlib
import io
import json
import time
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_PROCESSED, DATA_REFERENCE

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
while True:
    pf = PAGES_DIR / f"page_{offset:09d}.parquet"
    if pf.exists():
        n = len(pd.read_parquet(pf, columns=["incident_datetime"]))
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
ems = ems[keep].copy()
ems["incident_date"] = ems["incident_ts"].dt.normalize()
ems["communitydistrict"] = pd.to_numeric(ems["communitydistrict"], errors="coerce")
print(f"After filters: {len(ems):,} rows")

# Extract 1: CD x day x call type, 2014-12..2024-12
win = ems[ems["incident_date"].between("2014-12-01", "2024-12-31")]
g1 = (win.groupby(["incident_date", "communitydistrict", "final_call_type"])
      .size().rename("n_calls").reset_index())
out1 = DATA_PROCESSED / "ems_cd_day_calltype.parquet"
g1.to_parquet(out1, index=False)
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

row = pd.DataFrame([{
    "source_id": "S1b", "description": "EMS Incident Dispatch Data via SODA API (7 columns, paged), replaces user-local export",
    "url": BASE, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sha256": hashlib.sha256(out1.read_bytes()).hexdigest(), "output_file": str(out1),
}])
lp = DATA_REFERENCE / "data_sources.csv"
row.to_csv(lp, mode="a", header=not lp.exists(), index=False)
print("provenance logged")
