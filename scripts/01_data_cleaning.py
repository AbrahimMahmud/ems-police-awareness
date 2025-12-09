"""Clean EMS data and create daily panel by community district."""

import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

EMS_BASENAME_PATTERN = "EMS_Incident_Dispatch_Data"
ems_files = [f for f in DATA_RAW.glob(f"{EMS_BASENAME_PATTERN}*.csv")]
if not ems_files:
    raise FileNotFoundError(f"EMS data file not found in {DATA_RAW}")
EMS_PATH = max(ems_files, key=lambda p: p.stat().st_size)

MH_CODES = ("EDP", "ALTMEN", "ALTMFC", "ALTMFT", "JUMPDN", "JUMPUP", "JUMPDC", "OD", "ODC", "POISON", "DRUG")
TRUTHY = ("Y", "YES", "TRUE", "1")
MH_CODES_SQL = "(" + ",".join(f"'{code}'" for code in MH_CODES) + ")"
TRUTHY_SQL = "(" + ",".join(f"'{val}'" for val in TRUTHY) + ")"

sql = f"""
PRAGMA threads=4;

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
    upper(trim(incident_disposition_code)) AS disp_str,
    try_cast(incident_disposition_code AS INTEGER) AS disp_int,
    upper(nullif(trim(special_event_indicator),'')) AS special_event_indicator,
    upper(nullif(trim(standby_indicator),'')) AS standby_indicator,
    upper(nullif(trim(transfer_indicator),'')) AS transfer_indicator
  FROM ems_raw
),
ems_filtered AS (
  SELECT * FROM ems
  WHERE (special_event_indicator NOT IN {TRUTHY_SQL} OR special_event_indicator IS NULL)
    AND (standby_indicator NOT IN {TRUTHY_SQL} OR standby_indicator IS NULL)
    AND (transfer_indicator NOT IN {TRUTHY_SQL} OR transfer_indicator IS NULL)
    AND (disp_str NOT IN ('CANCEL','NOTSNT','DUP') OR disp_str IS NULL)
    AND (disp_int IS NULL OR disp_int <> 87)
    AND incident_ts IS NOT NULL
),
panel AS (
  SELECT
    CAST(date_trunc('day', incident_ts) AS DATE) AS incident_date,
    communitydistrict,
    COUNT(*) AS total_calls,
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

con = duckdb.connect()
panel_df = con.execute(sql).fetch_df()
con.close()

panel_parquet = DATA_PROCESSED / "panel_cd_day.parquet"
panel_df.to_parquet(panel_parquet, index=False)

print(f"Panel created: {panel_df.shape[0]:,} rows, {panel_df['communitydistrict'].nunique()} districts")
print(f"Date range: {panel_df['incident_date'].min()} to {panel_df['incident_date'].max()}")
print(f"Saved to: {panel_parquet}")
