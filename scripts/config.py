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
# Discovery and confirmation are named SEPARATELY and explicitly (finding D3).
#
# Previously only ANALYSIS_START/END existed, scoped to discovery, and the guard
# no-opped when FREEZE_ACTIVE was False. Lifting the freeze therefore did NOT
# open a confirmation sample — it opened whatever ANALYSIS_START/END happened to
# say, and widening them pooled the already-examined discovery years into the
# "confirmatory" run. That would have produced a discovery-contaminated estimate
# reported as 70 unseen episodes, which is the single worst thing that could
# happen to this design, and no code prevented it.
#
# Now the two samples are disjoint by construction and the active one is derived,
# never hand-set. See freeze_guard.select_sample().
DISCOVERY_START = "2017-01-01"
DISCOVERY_END = "2020-12-31"

# Never examined. Kept as explicit intervals so "the confirmation sample" is a
# value in the code rather than a claim in a document.
CONFIRM_START = "2015-01-01"
CONFIRMATION_WINDOWS = (
    ("2015-01-01", "2016-12-31"),   # pre-discovery: no COVID, no B-HEARD
    ("2021-01-01", "2024-12-31"),   # post-discovery: B-HEARD control required
)

# Back-compatible aliases. While the freeze holds these ARE the discovery window;
# they are what existing scripts filter on.
ANALYSIS_START = DISCOVERY_START
ANALYSIS_END = DISCOVERY_END
PANEL_BUFFER_START = "2016-12-01"   # covers 28-day lags before analysis start
PANEL_BUFFER_END = "2021-01-31"     # covers 14-day leads after analysis end

# The OUTCOME SOURCE itself, not just the files derived from it. Freeze coverage
# was a list of artifacts, so querying this dataset directly bypassed every guard
# in the project - which is exactly how incident F2 happened (see PAPER_MASTER
# 5.3). D.soda_guarded keys on this constant.
EMS_DATASET_ID = "76xm-jjuj"

# Every artifact that contains OUTCOME data, named here so freeze coverage is a
# property of a list rather than of one hard-coded filename (finding X11, and
# incident F1 which is how it was found).
#
# The guard used to be keyed on the single string "panel_cd_day.parquet", so its
# guarantee was exactly that wide and no wider: ems_citywide_day_trends.parquet
# and ems_cd_day_calltype.parquet were unguarded by construction, and a passing
# D.guard_coverage was read as "outcome data is guarded" when it only ever meant
# "panel readers are guarded". On 2026-09-10 an audit agent took that unguarded
# path and read confirmation-period outcomes.
#
# A NEW OUTCOME ARTIFACT MUST BE ADDED HERE. The check reads this list, so an
# unlisted outcome file is a check failure rather than a silent gap.
OUTCOME_ARTIFACTS = (
    "panel_cd_day.parquet",            # district x day analysis panel
    "ems_cd_day_calltype.parquet",     # district x day x call type extract
    "ems_citywide_day_trends.parquet", # citywide daily call-group counts, 2005+
)

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
# Call type groups (I10, I11).
#
# TWO FALSE COMMENTS WERE REMOVED HERE (finding O3). Both were load-bearing: one
# named the authority for the codes, the other was the stated justification for
# the grouping, and neither was true.
#
#  1. "Codes from the official data dictionary sheet 'Call Type Descriptions'."
#     Verified directly against data/raw/EMS_incident_dispatch_data_description
#     (1).xlsx: that sheet has 271 codes and contains ONLY "EDP = PSYCHIATRIC
#     PATIENT". EDPC, EDPM, EDPW and T-EDP are all UNDOCUMENTED, and edp is the
#     only group here with undocumented members. The real basis for including
#     them is the observed recode pattern, which is weaker and must be stated
#     as such in the paper.
#
#  2. "family total stable ~125k/yr while EDP alone falls." False. Annual family
#     totals run 108,384 (2016) to 141,910 (2024) - a 47% range that matches
#     "~125k" only in 2017-2018. Those figures come from the F2 freeze access
#     and are cited here rather than re-derived, because re-deriving them would
#     be a THIRD confirmation-period read; see PAPER_MASTER.md 5.3.
#
# The grouping itself stands - EDPC really is a progressive recode of EDP, and
# omitting the recode codes creates a time-trending undercount - but it rests on
# a pattern in the data, not on documentation, and the family total is not flat.
# ---------------------------------------------------------------------------
CALL_TYPE_GROUPS = {
    # EDP family. EDPC appears mid-2018 as a progressive recode of EDP; EDPM
    # appears 2021-06-03; T-EDP appears 2020-06-05 and is ~0.2% of the family.
    # See O3 for what each birth date does and does not imply, and 5.3 for the
    # freeze access that established them.
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

# The component baskets are HERE, not in 12_build_cai.py, so that the audit
# suite and the build script cannot disagree about what the index contains.
#
# trends_victims was dropped on 2026-09-09 (findings T2, L2, T8). Two
# independent reasons, either sufficient:
#   1. It was never in the units it claimed. 11c computes `ratio = df[name]`
#      with no denominator, so each victim series is a within-window 0-100
#      rank and every sizeable victim — Walter Scott through George Floyd —
#      saturates at exactly 100. The component counted open windows, not
#      attention.
#   2. Its availability is caused by the treatment. Google Trends only returns
#      a victim-name series once volume clears a reporting floor, so the
#      component is present on high-attention days and missing on quiet ones.
#      In a mean-of-available-components index that pushes the index up
#      precisely when attention is high, partly by construction — the index
#      would partly measure itself.
# Cost of dropping it: near zero. The three always-on components correlate
# 0.985 with the index as previously built.
# CAI-D IS A NATIONAL ATTENTION INDEX. There is no city-local component, and
# that is a measurement decision taken on evidence rather than a gap.
#
# trends_nyc was dropped (2026-09-11). Three independent reasons, any one of
# which would be enough:
#   1. CENSORED. Exactly zero on 42.6% of days - 26% in 2020 rising to 71% in
#      2024 - because Google suppresses region-days below an undisclosed volume
#      floor. On those days it is an indicator of clearing the floor, not a
#      level, and the censoring is worst in the years the exposed confirmation
#      stratum sits in.
#   2. BROKEN BY STITCHING. Two boundaries (2015-12-27, 2022-07-23) drop the
#      level 0.32x and 0.26x with no corroboration in wiki_ext, because a
#      censored overlap window leaves too few positive days to estimate a scale.
#   3. Dropping it costs almost nothing: the national-only index correlates
#      0.9695 with the index as previously built, and keeps the same top days.
#
# wiki_nyc was BUILT as its uncensored replacement and then REJECTED
# (2026-09-11) — not for measuring the wrong thing, but because it cannot be
# both LOCAL and DISJOINT from the national basket:
#   - it has no censored days, and correlates +0.54 with wiki_ext and +0.62 with
#     trends_us, so it is measuring attention to police violence;
#   - but 3 of its 7 NYC articles are already in the national wiki_ext basket
#     (Eric Garner, Akai Gurley, Deborah Danner) and those three are 67% of all
#     its views — Eric Garner alone is 61%. Including it double-counts them;
#   - making it disjoint leaves 4 articles whose most recent killing is from
#     1999, none inside the study window;
#   - the disjoint series' variance beyond the national components (R2 = 0.454)
#     is Amadou Diallo artifacts: all 8 of its largest residuals are a 2022
#     viral spike and anniversary runs, and on 7 actual NYC police-violence
#     events in the window the residual is negative for 3 of them;
#   - substituting it drops 2016-07-08 (Sterling and Castile) out of the index's
#     top five, losing the strongest validation the index has.
# It survives as a validation exhibit, not as treatment.
#
# CORRECTION (T14): the first version of this note rejected wiki_nyc for the
# OPPOSITE reason — a -0.18 correlation with trends_us and Diallo anniversary
# dominance. Those numbers came from a stale artifact: 28_build_nyc_attention.py
# had the historical-title fix but had never been re-run, so the series was
# still canonical-title-only and was missing Eric Garner entirely. The
# conclusion survived the correction; none of the reasons did.
#
# The locality question does not disappear, it moves: whether an episode
# contains an NYC killing is an EPISODE ATTRIBUTE for heterogeneity, not a
# component of the treatment index.
CAI_D_COMPONENTS = ("wiki_ext", "trends_us")
CAI_S_COMPONENTS = ("gdelt_news", "gdelt_tv")
CAI_D_COMPONENTS_RETIRED = ("trends_victims",)

# Legacy Twitter variants, available only via 02_build_awareness.py and used
# only by 03b_bridge_legacy.py. Never a treatment in a reported result.
LEGACY_AWARENESS = "aware_log"
LEGACY_AWARENESS_VARIANTS = ("aware_log", "aware_z", "aware_rank", "aware_re_log",
                             "aware_black_log", "aware_nonblack_log")
LAGS = tuple(range(0, 29))                 # every k, 0..28 (meeting note)
LEADS = tuple(range(1, 15))                # pre-trend checks, 1..14 (meeting note)
ROLLING_WINDOWS = ((0, 2), (3, 5), (6, 8), (9, 11), (12, 14))  # meeting note

# Episode definition — REWRITTEN 2026-09-10. Two changes, both disclosed in the
# CONFIRMATION_PLAN addendum because they alter a pre-registered construct.
#
# 1. THRESHOLD: a fixed level is not a fixed stringency. `cai_d > 1.0` selected
#    between 10.7% and 66.4% of the days in a year depending on the year, because
#    the index is unit-variance on its 2017-2019 reference window but has a strong
#    level shift across years. A within-calendar-year quantile is constant
#    stringency by construction: the top EPISODE_RATE of every year, always.
#
# 2. CONSTRUCT: from REGIME to SHOCK. The old rule merged runs of high days
#    separated by short gaps, which on 2020 produced a single 184-day episode
#    swallowing the whole Floyd summer — one observation in a ±14 day design,
#    hiding at least eight distinct attention shocks including Daniel Prude, a
#    Black man killed during a mental-health crisis and the most on-hypothesis
#    event in the dataset. Verified across four rule variants: no parameter
#    inside the "sustained elevated level" family removes it, because the
#    plateau is a true feature of 2020. So an episode is no longer "attention was
#    high for a stretch" but "attention to a specific killing began on day X" —
#    a local peak, with its onset, bounded so it never exceeds the window it is
#    analysed with.
#
# This is legitimate ONLY because we remain blind to every outcome. The same
# correction made after the confirmatory run would be worthless.
EPISODE_RATE = 0.10               # ENTRY: top 10% of days within each calendar year
# EXIT is deliberately looser than entry (hysteresis). Using the entry bar to end
# an episode as well collapses the rule to points: attention decays below the top
# decile within a day or two of a peak, so 44 of 84 episodes came out as single
# days with a median span of 0. A shock has a sharp onset and a slow tail, and an
# episode that ends the moment it stops being top-decile measures the onset only.
# Entering at p90 and leaving at p75 is the standard hysteresis form and was one
# of the candidate rules evaluated.
EPISODE_EXIT_RATE = 0.25          # EXIT: stay in the episode while in the top 25%
EPISODE_PEAK_WINDOW_DAYS = 7      # a peak is the max over ±this many days
EPISODE_MIN_SEPARATION_DAYS = 14  # two peaks closer than this are one shock
EPISODE_MAX_DAYS = 14             # never longer than the ±14 analysis window
EPISODE_MAX_ONSET_LEAD_DAYS = 7   # how far before the peak an onset may sit

# Retired, kept so the diff from the frozen list is legible.
EPISODE_Z_THRESHOLD = 1.0
EPISODE_MERGE_GAP_DAYS = 7

# How far back from an episode to look for the killing that plausibly caused it.
# Was 14 days, which is shorter than the death-to-attention lag this literature
# documents (finding E2): video releases, indictments, autopsy findings and
# verdicts routinely spike weeks or months after the death. Daniel Prude died
# 2020-03-30 and the bodycam footage was released 2020-09-02 — five months. A
# 14-day window attributes that attention to whoever happened to die in the
# fortnight before the spike, which is how the largest non-2020 episode came to
# be labelled with the wrong person.
ATTRIBUTION_LOOKBACK_DAYS = 60

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
# The confirmation freeze. While True, freeze_guard.assert_discovery_only()
# rejects any outcome row outside ANALYSIS_START..ANALYSIS_END, so no model can
# reach the extension sample. Setting this to False IS the act of opening the
# confirmation sample: do it in its own commit, after Gate C ratification.
FREEZE_ACTIVE = True

H1_TEST = "two_sided_joint_lags_0_7"
H1_OUTCOMES = ("edp_share", "mh_narrow_share")

# DID control group (GATE_C_MEMO.md §4). Treated = top-quartile %Black CDs.
# Primary control is the "even-distribution" set (bottom quartile of a
# Herfindahl index over the four race shares) rather than Q2: Q2 is the one
# quartile the discovery run found to have no effect, so promoting it to
# control after seeing that would be selecting the comparison on the outcome.
DID_CONTROL_PRIMARY = "even_distribution"
DID_CONTROL_SENSITIVITY = "q2_black"
