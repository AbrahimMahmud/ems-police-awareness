"""Central configuration for the analysis pipeline.

All constants live here (REWORK_PLAN.md §7): scripts must not hard-code
sample rules, code lists, lag sets, or dates.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_REFERENCE = PROJECT_ROOT / "data" / "reference"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"

# ---------------------------------------------------------------------------
# Input files
# ---------------------------------------------------------------------------
TWEETS_DAILY_CSV = DATA_RAW / "220126_final_daily_tweet_count.csv"      # single source (I5)
TWEETS_PER_VICTIM_CSV = DATA_RAW / "211118_tweet_count_name_date.csv"   # victim-level detail
SHOOTINGS_DB_CSV = DATA_RAW / "fatalpoliceshootingsCLEANED.csv"         # WaPo Fatal Force (cleaned)
VICTIM_CURATION_CSV = DATA_REFERENCE / "victim_curation_table.csv"      # manual top-100 (I9)
EMS_EXTRACT_CD_DAY = DATA_PROCESSED / "ems_cd_day_calltype.parquet"     # from 00_local_ems_extract.py
EMS_EXTRACT_TRENDS = DATA_PROCESSED / "ems_citywide_day_trends.parquet"

# ---------------------------------------------------------------------------
# Sample definition
# ---------------------------------------------------------------------------
ANALYSIS_START = "2017-01-01"
ANALYSIS_END = "2020-12-31"
PANEL_BUFFER_START = "2016-12-01"   # covers 28-day lags before analysis start
PANEL_BUFFER_END = "2021-01-31"     # covers 14-day leads after analysis end

MIN_TOTAL_CALLS_FOR_SHARE = 5        # primary; sensitivities at 3 and 10 (I17/plan §4.5)
MIN_CALLS_SENSITIVITY = (3, 10)

# 59 valid community districts (I7): borough*100 + district number.
VALID_CDS = (
    [100 + i for i in range(1, 13)]     # Manhattan 101-112
    + [200 + i for i in range(1, 13)]   # Bronx 201-212
    + [300 + i for i in range(1, 19)]   # Brooklyn 301-318
    + [400 + i for i in range(1, 15)]   # Queens 401-414
    + [500 + i for i in range(1, 4)]    # Staten Island 501-503
)
assert len(VALID_CDS) == 59

# ---------------------------------------------------------------------------
# Call type groups (I10, I11). Codes from the official data dictionary sheet
# "Call Type Descriptions" in EMS_incident_dispatch_data_description.xlsx.
# ---------------------------------------------------------------------------
CALL_TYPE_GROUPS = {
    "edp": ["EDP"],
    "altmen": ["ALTMEN", "ALTMFC", "ALTMFT"],
    "suicide_jump": ["JUMPDN", "JUMPUP", "JUMPDC"],
    "od_poison_drug": ["OD", "ODC", "POISON", "DRUG"],
    # placebo outcomes: no plausible awareness channel
    "cardiac": ["ARREST", "ARREFC", "ARREFT", "CARD", "CARDFC", "CARDFT",
                "HEART", "HEARTC", "CVA", "CVAC", "CVACFC", "CVACFT", "CVAFC", "CVAFT"],
    "injury": ["INJURY", "INJMIN", "INJMAJ", "INJALS", "MVAINJ", "TRAUMA"],
    "asthma": ["ASTHMA", "ASTHMB", "ASTHMC", "ASTHMP", "ASTHFC", "ASTHFT"],
}
# Derived outcomes: mh_narrow = edp + altmen + suicide_jump (primary, I10);
# mh_broad = mh_narrow + od_poison_drug (legacy definition).
MH_NARROW_GROUPS = ("edp", "altmen", "suicide_jump")
MH_BROAD_GROUPS = MH_NARROW_GROUPS + ("od_poison_drug",)

# ---------------------------------------------------------------------------
# Awareness (I5, I6, I8, I9)
# ---------------------------------------------------------------------------
PRIMARY_AWARENESS = "aware_log"            # log(1 + tweet_count)
AWARENESS_VARIANTS = ("aware_log", "aware_z", "aware_rank", "aware_re_log",
                      "aware_black_log", "aware_nonblack_log")
LAGS = tuple(range(0, 29))                 # every k, 0..28 (meeting note)
LEADS = tuple(range(1, 15))                # pre-trend checks, 1..14 (meeting note)
ROLLING_WINDOWS = ((0, 2), (3, 5), (6, 8), (9, 11), (12, 14))  # meeting note

# Episode definition (plan §4.1): runs of days with aware_z > EPISODE_Z_THRESHOLD,
# merged when separated by fewer than EPISODE_MERGE_GAP_DAYS days.
EPISODE_Z_THRESHOLD = 1.0
EPISODE_MERGE_GAP_DAYS = 7

# High-visibility days for the DID (plan §5.2): top decile of aware_log in analysis window.
DID_EVENT_QUANTILE = 0.90
