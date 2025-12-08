"""
Step 1: Clean EMS data and create daily panel by community district.

This script:
- Loads raw EMS incident dispatch data
- Filters out special events, standby calls, transfers, cancellations
- Creates daily panel with total calls, MH calls, and MH share by community district
- Saves panel to data/processed/panel_cd_day.parquet
"""

import duckdb
import os
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Create output directory if it doesn't exist
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Find EMS data file (handle date suffix)
EMS_BASENAME_PATTERN = "EMS_Incident_Dispatch_Data"
ems_files = [f for f in DATA_RAW.glob(f"{EMS_BASENAME_PATTERN}*.csv")]
if not ems_files:
    raise FileNotFoundError(
        f"EMS data file not found in {DATA_RAW}. "
        f"Expected file matching pattern: {EMS_BASENAME_PATTERN}*.csv"
    )
# Use the largest file if multiple exist
EMS_PATH = max(ems_files, key=lambda p: p.stat().st_size)
print(f"Using EMS file: {EMS_PATH}")

# Mental health call codes
MH_CODES = ("EDP", "ALTMEN", "ALTMFC", "ALTMFT", "JUMPDN", "JUMPUP", "JUMPDC", "OD", "ODC", "POISON", "DRUG")

# Truthy values for filtering
TRUTHY = ("Y", "YES", "TRUE", "1")

# Format tuples for SQL IN clause
MH_CODES_SQL = "(" + ",".join(f"'{code}'" for code in MH_CODES) + ")"
TRUTHY_SQL = "(" + ",".join(f"'{val}'" for val in TRUTHY) + ")"

# Robust parse: try multiple datetime formats
sql = f"""
PRAGMA threads=4;

WITH ems_raw AS (
  SELECT
    incident_datetime,
    communitydistrict,
    final_call_type,
    incident_disposition_code,
    special_event_indicator,
    standby_indicator,
    transfer_indicator
  FROM read_csv_auto('{EMS_PATH}', all_varchar=true, sample_size=-1, ignore_errors=true)
),
ems AS (
  SELECT
    /* Try common formats: 'YYYY-MM-DD HH:MM:SS' and ISO 'YYYY-MM-DDTHH:MM:SS' */
    COALESCE(
      try_strptime(incident_datetime, '%Y-%m-%d %H:%M:%S'),
      try_strptime(incident_datetime, '%Y-%m-%dT%H:%M:%S'),
      try_strptime(incident_datetime, '%m/%d/%Y %H:%M:%S'),
      try_strptime(incident_datetime, '%m/%d/%Y %I:%M:%S %p')
    ) AS incident_ts,
    try_cast(communitydistrict AS INTEGER)                       AS communitydistrict,
    upper(trim(final_call_type))                                 AS final_call_type,
    upper(trim(incident_disposition_code))                       AS disp_str,
    try_cast(incident_disposition_code AS INTEGER)               AS disp_int,
    upper(nullif(trim(special_event_indicator),''))              AS special_event_indicator,
    upper(nullif(trim(standby_indicator),''))                    AS standby_indicator,
    upper(nullif(trim(transfer_indicator),''))                   AS transfer_indicator
  FROM ems_raw
),
ems_filtered AS (
  SELECT *
  FROM ems
  WHERE (special_event_indicator NOT IN {TRUTHY_SQL} OR special_event_indicator IS NULL)
    AND (standby_indicator       NOT IN {TRUTHY_SQL} OR standby_indicator IS NULL)
    AND (transfer_indicator      NOT IN {TRUTHY_SQL} OR transfer_indicator IS NULL)
    AND (disp_str NOT IN ('CANCEL','NOTSNT','DUP') OR disp_str IS NULL)
    AND (disp_int IS NULL OR disp_int <> 87)
    AND incident_ts IS NOT NULL
),
panel AS (
  SELECT
    CAST(date_trunc('day', incident_ts) AS DATE)         AS incident_date,
    communitydistrict,
    COUNT(*)                                             AS total_calls,
    SUM(CASE WHEN final_call_type IN {MH_CODES_SQL} THEN 1 ELSE 0 END) AS mh_calls
  FROM ems_filtered
  GROUP BY 1,2
)
SELECT
  incident_date,
  communitydistrict,
  total_calls,
  mh_calls,
  CASE WHEN total_calls>0 THEN mh_calls::DOUBLE/total_calls::DOUBLE ELSE NULL END AS mh_share
FROM panel
ORDER BY incident_date, communitydistrict;
"""

print("Connecting to DuckDB and executing query...")
con = duckdb.connect()
panel_df = con.execute(sql).fetch_df()
con.close()

print(f"Panel shape: {panel_df.shape}")
print("\nPanel preview:")
print(panel_df.head(10))

# Validate panel
assert len(panel_df) > 0, "Panel is empty!"
assert "incident_date" in panel_df.columns, "Missing incident_date column"
assert "communitydistrict" in panel_df.columns, "Missing communitydistrict column"
assert "total_calls" in panel_df.columns, "Missing total_calls column"
assert "mh_calls" in panel_df.columns, "Missing mh_calls column"
assert "mh_share" in panel_df.columns, "Missing mh_share column"

# Save panel
panel_parquet = DATA_PROCESSED / "panel_cd_day.parquet"
panel_df.to_parquet(panel_parquet, index=False)
print(f"\nSaved panel to: {panel_parquet}")
print(f"Panel date range: {panel_df['incident_date'].min()} to {panel_df['incident_date'].max()}")
print(f"Number of community districts: {panel_df['communitydistrict'].nunique()}")

