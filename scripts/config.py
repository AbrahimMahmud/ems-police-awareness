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
# Legacy Twitter files. RETIRED as a treatment variable (GATE_C_MEMO.md §6):
# the collection methodology was never documented by the data's originator and
# cannot be defended in print. They are retained for ONE purpose only -- the
# bridge/methods result (ROADMAP D2), where the z-scored Twitter series is the
# OBJECT OF CRITIQUE, not a measure anything is claimed from.
TWEETS_DAILY_CSV = DATA_RAW / "220126_final_daily_tweet_count.csv"      # legacy/bridge only
TWEETS_PER_VICTIM_CSV = DATA_RAW / "211118_tweet_count_name_date.csv"   # legacy/bridge only
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
    # EDP family: EDPC appears mid-2018 as a progressive recode of EDP (family
    # total stable ~125k/yr while EDP alone falls); EDPM appears 2021; omitting
    # them (as the original analysis did) creates a time-trending undercount.
    "edp": ["EDP", "EDPC", "EDPM", "EDPW", "T-EDP"],
    "altmen": ["ALTMEN", "ALTMFC", "ALTMFT"],
    # JUMPDC, OD, ODC, POISON never occur in 2016-2021 (legacy codes); kept out.
    "suicide_jump": ["JUMPDN", "JUMPUP"],
    "od_poison_drug": ["DRUG", "DRUGFC"],
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
# Treatment variable: the composite index CAI-D (demand/attention tier), built
# from Wikipedia victim pageviews + Google Trends by 12_build_cai.py. Every
# component is public and re-fetchable, which is the whole point of the swap.
PRIMARY_AWARENESS = "cai_d"
AWARENESS_VARIANTS = ("cai_d", "cai_d_black", "cai_d_nonblack", "cai_s")

# Legacy Twitter variants, available only via 02_build_awareness.py and used
# only by 03b_bridge_legacy.py. Never a treatment in a reported result.
LEGACY_AWARENESS = "aware_log"
LEGACY_AWARENESS_VARIANTS = ("aware_log", "aware_z", "aware_rank", "aware_re_log",
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

# ---------------------------------------------------------------------------
# B-HEARD confound control (GATE_C_MEMO.md §2)
# ---------------------------------------------------------------------------
# B-HEARD routes nonviolent mental-health 911 calls to EMS-led rather than
# police-led response. It launched June 2021 and reduces mental-health EMS call
# rates in adopting precincts, so it confounds the 2021-2024 confirmation
# sample in the same direction as the hypothesis under test.
BHEARD_LAUNCH = "2021-06-01"
BHEARD_ADOPTION_CSV = DATA_REFERENCE / "bheard_precinct_adoption.csv"
BHEARD_EXPOSURE_CSV = DATA_REFERENCE / "bheard_cd_exposure.csv"
PRECINCT_CD_CROSSWALK_CSV = DATA_REFERENCE / "precinct_cd_crosswalk.csv"
# Primary control uses the conservative (maximal-exposure) bound; "late" is the
# pre-specified sensitivity. See the module docstring of 16_bheard_exposure.py.
BHEARD_PRIMARY_BOUND = "early"

# ---------------------------------------------------------------------------
# Stacked episode event study (ROADMAP U1; GATE_C_MEMO.md §3)
# ---------------------------------------------------------------------------
EVENT_WINDOW_PRE = 14                  # days before the episode start
EVENT_WINDOW_POST = 14                 # primary post-window
EVENT_WINDOW_POST_SENSITIVITY = (28, 60)   # U2: Desmond et al. find year-long effects
EVENT_REFERENCE_DAY = -1               # omitted category in event-time dummies
RANDOMIZATION_DRAWS = 2000             # episode-level RI; primary p-value

# ---------------------------------------------------------------------------
# Gate C ratified decisions (GATE_C_MEMO.md §6, 2026-09-08)
# ---------------------------------------------------------------------------
# H1 is a TWO-SIDED joint test of awareness on first-week (lags 0-7) EDP and
# narrow-MH call composition under CAI-D. The directional days-3-5 decline is
# retired: it was a feature of the legacy Twitter series, which is no longer a
# treatment variable.
H1_TEST = "two_sided_joint_lags_0_7"
H1_OUTCOMES = ("edp_share", "mh_narrow_share")

# DID control group (GATE_C_MEMO.md §4). Treated = top-quartile %Black CDs.
# Primary control is the "even-distribution" set (bottom quartile of a
# Herfindahl index over the four race shares) rather than Q2: Q2 is the one
# quartile the discovery run found to have no effect, so promoting it to
# control after seeing that would be selecting the comparison on the outcome.
DID_CONTROL_PRIMARY = "even_distribution"
DID_CONTROL_SENSITIVITY = "q2_black"
