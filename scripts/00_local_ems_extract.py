"""Create compact analysis extracts from the raw NYC EMS dispatch CSV.

Run this LOCALLY on the machine that has the full EMS_Incident_Dispatch_Data*.csv
(~6.5 GB). It produces two small parquet files (tens of MB) that contain
everything the corrected analysis pipeline needs, so the raw file never has to
be moved:

  1. data/processed/ems_cd_day_calltype.parquet
     District x day x final_call_type call counts for 2014-12-01..2024-12-31
     (confirmation-plan window plus lag/lead buffer). Call types kept verbatim so mental
     health definitions can be changed without re-reading the raw file.

  2. data/processed/ems_citywide_day_trends.parquet
     Citywide daily totals and mental-health-group counts for the full
     2005-2025 period (for long-run descriptive trends only).

Filters applied (documented for the paper):
  - Drop special event / standby / transfer indicator = Y
  - Drop dispositions: CANCEL, 87 (="cancelled" per NYC data dictionary),
    DUP (duplicate incident), NOTSNT (unit not sent)
  - Drop rows with unparseable incident_datetime

Rows are NOT restricted to valid community districts here; that filter is
applied (and documented) at the analysis stage.

Usage:
    python scripts/00_local_ems_extract.py [path/to/EMS_Incident_Dispatch_Data.csv]
"""

import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

if len(sys.argv) > 1:
    EMS_PATH = Path(sys.argv[1])
else:
    ems_files = sorted(DATA_RAW.glob("EMS_Incident_Dispatch_Data*.csv"), key=lambda p: p.stat().st_size)
    if not ems_files:
        raise FileNotFoundError(
            f"No EMS_Incident_Dispatch_Data*.csv found in {DATA_RAW}. "
            "Pass the path explicitly: python scripts/00_local_ems_extract.py /path/to/file.csv"
        )
    EMS_PATH = ems_files[-1]

print(f"Reading: {EMS_PATH} ({EMS_PATH.stat().st_size / 1e9:.2f} GB)")

# Mental health groups used only for the citywide trends file; the district-day
# extract keeps final_call_type verbatim.
MH_GROUPS_SQL = """
  CASE
    WHEN final_call_type = 'EDP' THEN 'edp'
    WHEN final_call_type IN ('ALTMEN','ALTMFC','ALTMFT') THEN 'altmen'
    WHEN final_call_type IN ('JUMPDN','JUMPUP','JUMPDC') THEN 'suicide_jump'
    WHEN final_call_type IN ('OD','ODC','POISON','DRUG') THEN 'od_poison_drug'
    ELSE 'other'
  END
"""

TRUTHY_SQL = "('Y','YES','TRUE','1')"
EXCLUDED_DISP_SQL = "('CANCEL','NOTSNT','DUP','87')"

BASE_CTE = f"""
WITH ems_raw AS (
  SELECT incident_datetime, communitydistrict, final_call_type, incident_disposition_code,
         special_event_indicator, standby_indicator, transfer_indicator
  FROM read_csv_auto('{EMS_PATH}', all_varchar=true, sample_size=-1, ignore_errors=true)
),
ems AS (
  SELECT
    COALESCE(
      try_strptime(incident_datetime, '%Y-%m-%d %H:%M:%S'),
      try_strptime(incident_datetime, '%Y-%m-%dT%H:%M:%S'),
      try_strptime(incident_datetime, '%m/%d/%Y %H:%M:%S'),
      try_strptime(incident_datetime, '%m/%d/%Y %I:%M:%S %p')
    ) AS incident_ts,
    try_cast(communitydistrict AS INTEGER) AS communitydistrict,
    upper(trim(final_call_type)) AS final_call_type,
    upper(trim(incident_disposition_code)) AS disp,
    upper(nullif(trim(special_event_indicator), '')) AS special_event_indicator,
    upper(nullif(trim(standby_indicator), '')) AS standby_indicator,
    upper(nullif(trim(transfer_indicator), '')) AS transfer_indicator
  FROM ems_raw
),
ems_filtered AS (
  SELECT CAST(date_trunc('day', incident_ts) AS DATE) AS incident_date,
         communitydistrict, final_call_type
  FROM ems
  WHERE incident_ts IS NOT NULL
    AND (special_event_indicator NOT IN {TRUTHY_SQL} OR special_event_indicator IS NULL)
    AND (standby_indicator NOT IN {TRUTHY_SQL} OR standby_indicator IS NULL)
    AND (transfer_indicator NOT IN {TRUTHY_SQL} OR transfer_indicator IS NULL)
    AND (disp NOT IN {EXCLUDED_DISP_SQL} OR disp IS NULL)
)
"""

con = duckdb.connect()
con.execute("PRAGMA threads=4;")

# --- Extract 1: district x day x call type, 2016-2021 ---
out1 = DATA_PROCESSED / "ems_cd_day_calltype.parquet"
sql1 = BASE_CTE + f"""
SELECT incident_date, communitydistrict, final_call_type, COUNT(*) AS n_calls
FROM ems_filtered
WHERE incident_date BETWEEN DATE '2014-12-01' AND DATE '2024-12-31'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
"""
df1 = con.execute(sql1).fetch_df()
df1.to_parquet(out1, index=False)
print(f"Wrote {out1}: {len(df1):,} rows, {df1['communitydistrict'].nunique()} district codes, "
      f"{df1['final_call_type'].nunique()} call types, "
      f"{df1['incident_date'].min()} -> {df1['incident_date'].max()}")

# --- Extract 2: citywide daily trends, full period ---
out2 = DATA_PROCESSED / "ems_citywide_day_trends.parquet"
sql2 = BASE_CTE + f"""
SELECT incident_date, {MH_GROUPS_SQL} AS call_group, COUNT(*) AS n_calls
FROM ems_filtered
GROUP BY 1, 2
ORDER BY 1, 2
"""
df2 = con.execute(sql2).fetch_df()
df2.to_parquet(out2, index=False)
print(f"Wrote {out2}: {len(df2):,} rows, {df2['incident_date'].min()} -> {df2['incident_date'].max()}")

con.close()

size1 = out1.stat().st_size / 1e6
size2 = out2.stat().st_size / 1e6
print(f"\nAnalysis extract files ready (total {size1 + size2:.1f} MB):")
print(f"  {out1}  ({size1:.1f} MB)")
print(f"  {out2}  ({size2:.1f} MB)")
