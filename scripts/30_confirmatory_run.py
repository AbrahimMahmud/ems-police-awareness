"""The sealed one-shot confirmatory run (EXECUTION_PLAN.md Phase I).

WHY THIS FILE EXISTS AND WHY IT IS WRITTEN NOW
----------------------------------------------
Everything this project has built is an attempt to make one moment honest: the
moment the confirmation windows are opened. That moment is a `git` diff of one
line — `config.FREEZE_ACTIVE = True` becomes `False` — and then somebody has to
decide what to run. If that decision is taken *after* the flag flips, it is taken
by a person who is one command away from seeing the answer, and every choice made
there is a choice a reader is entitled to discount. **After is when improvisation
becomes p-hacking.**

So the run is written, reviewed and committed BEFORE the flip. Lifting the freeze
then means flipping one flag and executing one script with no arguments. There is
nothing left to decide, and the diff that opens the sample contains no analysis.

This script is deliberately not importable as a library and not parameterised in
any way that changes the specification. `--draws` lowers the number of
randomization draws (for the synthetic dry run only; the pre-specified value is
`config.RANDOMIZATION_DRAWS`), `--dry-run-synthetic` exercises the machinery on
fabricated data, and that is the whole of the surface area. There is no
`--outcome`, no `--window`, no `--stratum`: a flag that lets the operator run one
cell is a flag that lets the operator run the cell that worked.

WHAT IT REFUSES TO DO
---------------------
1. **It refuses to run at all while `FREEZE_ACTIVE` is True**, except under
   `--dry-run-synthetic`. The freeze is the design; a script that could be run
   "just to see" while it holds would be a fourth freeze incident waiting to be
   written up next to F1 and F2 (`PAPER_MASTER.md` §5.3).
2. **It refuses to run unless `outputs/tables/null_calibration.csv` reads
   `VERDICT,CALIBRATED`** at or above its own `min_sims_required`. An
   uncalibrated randomization p-value is not a weak p-value, it is not a
   p-value: if the estimator over-rejects on data built to contain no effect,
   the number this script writes has no interpretation at all. Gate C §6.3
   ratified this ordering and the current artifact records 200 sims, rejection
   rate 0.050 against a nominal 0.05 inside a [0.0198, 0.0802] band, KS
   uniformity p = 0.562.
3. **It refuses to overwrite a sealed result.** Phase I says "freeze results the
   moment they exist", and this project has already destroyed one gating artifact
   by re-running a script with smaller settings (finding D1: an 8-sim smoke test
   silently clobbered the 200-sim calibration, and `outputs/tables/` is
   gitignored so it was not recoverable). `confirmatory_results.csv` is therefore
   written once; a second run must pass `--overwrite-sealed-result` *with a
   reason*, and the reason is written into the file.
4. **In synthetic mode it never writes `confirmatory_results.csv`** and never
   reads a single row of the real panel. Fabricated numbers landing in the
   sealed result file would be the D1 clobber with worse consequences.

THE TWO STRATA (EXECUTION_PLAN.md Phase I)
------------------------------------------
    C1 "clean"    2015-07-01..2016-12-31 and 2021-01-01..2021-05-31
    C2 "exposed"  2021-06-01..2024-12-31
    pooled        C1 + C2

C1 starts 2015-07-01 and not 2015-01-01, which is where `CONFIRMATION_WINDOWS`
starts, because the Wikimedia daily-pageviews API begins 2015-07-01
(`DATA_AUDIT.md`, `PAPER_MASTER.md` §3.1). Before that date the treatment is not
merely noisy, it does not exist, so those 181 days carry no episode and cannot
contribute a comparison. They are dropped explicitly, counted in the log, and
asserted to be the *only* permitted days not assigned to a stratum — rather than
disappearing into a date filter nobody reads.

C1 is clean of both confounds: COVID is outside it and B-HEARD had not launched.
C2 carries B-HEARD (below) and the degraded Google Trends precision documented in
`config.CAI_D_COMPONENTS` — Trends censors NYC region-days below an undisclosed
volume floor on 26% of days in 2020 rising to 71% in 2024, which is why the
national-only index is used and why C2's treatment is measured worse than C1's.
The two strata are reported separately and pooled, and the pre-committed rule for
what to conclude when they disagree is in `docs/PRE_ANALYSIS_NOTE.md` §9.

Running all strata in one execution is not multiple-shot analysis. The one-shot
constraint is about not changing the specification after seeing a result; every
cell below is fixed in this file before any of them has a value.

B-HEARD IS IDENTIFICATION IN C2, NOT ONLY NUISANCE
--------------------------------------------------
From 2021-06-01 New York routes some mental-health 911 calls to a health-led
rather than police-led response, precinct by precinct, and it pushes the outcome
in the SAME direction as H1 (`PAPER_MASTER.md` §5.5). Every specification here
therefore carries `bheard_exposure` as a covariate. Two consequences, both
deliberate:

  * In C1 the column is identically zero, pyfixest drops it as collinear, and the
    estimate is NUMERICALLY IDENTICAL to the pre-registered estimator of
    `17_stacked_event_study.py`. The run asserts this rather than asserting it in
    a comment, the same way `X.bheard_inert_on_discovery` does for discovery.
  * In C2 the roll-out is staggered across districts and exposure spans
    **4e-06 to 1.0** over the 30 of 59 community districts that ever receive any
    (`data/reference/bheard_cd_exposure.csv`, `early` bound). That cross-district
    spread is a second source of identifying variation, not just a nuisance to
    absorb: it says what an attention shock does where the police have *already*
    been partly removed from the mental-health response. The interaction arm
    below estimates exactly that, and `docs/PRE_ANALYSIS_NOTE.md` §7 states the
    direction the mechanism implies before anyone can see the sign.

17 of the 31 precinct adoption dates are low confidence, so `16_bheard_exposure.py`
emits `early` and `late` bounds instead of pretending to a date it does not have.
`early` is primary because it is the CONSERVATIVE choice for this hypothesis, and
`late` is a pre-specified sensitivity: a result that flips between the bounds is a
result that depends on data we do not have, and must be reported as such.

RANDOMIZATION INFERENCE ACROSS A GAPPED SAMPLE — A REAL PROBLEM, PRE-SOLVED
---------------------------------------------------------------------------
`event_study.placebo_starts` draws one anchor uniformly and lays the real
episodes' gaps down from it, rejecting any draw whose whole sequence does not fit.
That is correct on a contiguous window, and it is the scheme the 200-sim null
calibration certifies. It cannot be used everywhere here, and the arithmetic says
so before any outcome is touched:

    stratum          blocks  episodes  anchor slack (days)
    discovery             1        29   190      (calibrated on this)
    C2                    1        30    53
    C1 block 2015-07..2016-12   10        23
    C1 block 2021-01..2021-05    5       -19     <- INFEASIBLE
    pooled block 2021-01..2024-12  35     33

C1's 2021 block holds 5 episodes spanning 139 days inside a 151-day window; once
14 days of pre-period and 14 of post are reserved there are 120 usable days and
the sequence does not fit. Every draw would be rejected, `randomization_p` would
return an empty null, and the primary p-value for the cleanest stratum in the
design would come back NaN — discovered at the one moment the specification may
not be changed.

Worse, the naive fix (draw across the union of covered days) puts placebo
episodes inside the 2017-2020 hole, where the confirmation panel has no rows at
all, so those episodes silently vanish from the stack and the null is built from
half-size designs. That is finding S1/E1/L1/X4/D2 — the defect five auditors
found independently in the previous `placebo_starts` — re-created by a sample
shape rather than by a loop.

Pre-specified resolution, fixed here and recorded per cell in the `ri_scheme`
column so no reader has to infer which null produced which p:

  * There is ONE implementation of the placebo draw and of the p-value, in
    `event_study.randomization_p`, and this script calls it with the stratum's
    calendar windows. `event_study.draw_scheme_for` picks the scheme from the
    geometry: a single contiguous window with room takes the calibrated
    anchor shift (C2); a stratum made of disjoint windows, or one whose
    sequence does not fit, takes the CIRCULAR SHIFT WITHIN EACH BLOCK (C1,
    pooled) - one uniformly drawn shift per window, wrapping inside it, so the
    number of episodes in each window is preserved on every draw (finding RI3:
    a shift across the concatenated blocks reproduced C1's real 10/5 split on
    12.4% of draws, and the calibration certifies the within-block null, not
    that one). This script used to carry its OWN copy of the seam-crossing
    shift, so the certificate it gated on described a null it did not draw
    (CP1 audit, 2026-09-13). The copy is gone.
  * The within-block scheme has 62,920 distinct designs on C1 against the 2,000
    pre-specified draws, so the test is SAMPLED, not exact; `ri_exact` is 0.
  * Every cell's draws are seeded from the cell's own identity and banked in a
    per-cell ledger with a design fingerprint (`event_study.open_ledger`), so a
    run killed by a container restart resumes exactly, a ledger from a
    different panel or episode list is quarantined rather than pooled, and no
    cell's draws depend on which cells ran before it.

**The null each stratum's p-values rest on is the one its own calibration
certifies**: `check_calibration` requires a CALIBRATED verdict for C1 and C2
separately, and `S.ri_scheme_certified` compares the scheme each stratum
requires against the scheme its certificate records.

WHAT IS ESTIMATED, AND WHY BOTH ARMS ALWAYS
-------------------------------------------
Specification, identical in form to the ratified primary estimator:

    y ~ i(rel_day, ref=-1) + bheard_exposure | ep_cd + dow,  clustered on date

Day -1 stays in the sample as the named omitted level (S2/D1). Episode x district
fixed effects mean no observation is a control for one event while treated in
another (I4), and contested district-days go to the nearer episode rather than
being deleted (S5/E4). Standard errors cluster on `incident_date` because
treatment is citywide and assigned at the date level (S6). The test statistic is
the JOINT Wald chi-square on the day 0..7 coefficients, two-sided in the effect,
per the H1 reframe ratified at Gate C §6.1 — not their mean, because a
dip-then-rebound (this project's own hypothesised mechanism) averages to roughly
zero and was nearly invisible to the retired statistic (S3/R7).

**Every outcome is reported on BOTH arms**: OLS on the share and PPML on the
count with a log-total-calls offset. This is not a robustness column and it is
not optional. The 2020 "signature" in shares does not survive in counts — EDP
counts were flat after Floyd while the denominator rose 6.4% because injury calls
rose ~20% (§5.4) — and a compositional result that lives only in the denominator
is not a result. Publishing one arm is exactly how such a reversal goes
unnoticed, and the counts arm has already been dead code once in this project
(X5/R8).

Placebo outcomes (cardiac, injury, asthma) run on both arms in every stratum.
They are falsification, not confirmation: they are excluded from the
multiple-testing family and a significant placebo undermines the primary result
rather than adding to it.

PRE-SPECIFIED SENSITIVITIES
---------------------------
  (a) **Drop the July 2016 episode.** It contains Alton Sterling (2016-07-05),
      Philando Castile (2016-07-06) AND the Dallas attack of 2016-07-07/08 in
      which five police officers were killed. Attention to violence *against*
      police plausibly moves EMS demand the other way, so the single largest
      episode in the clean stratum confounds the treatment's own construct. The
      basket already excludes Micah Xavier Johnson's article (deviation 7), but
      excluding an article does not remove a week from the calendar. Identified
      by CONTAINMENT of 2016-07-08 rather than by row number, so it survives the
      episode list being rebuilt.
  (b) **The broad-basket arm** (`config.CAI_D_BASKET`, `data/reference/
      basket_broad.csv`): the 118-article basket that also admits the nine
      killings where nothing establishes that police were the actor, against the
      109-article strict basket that is primary. The broad basket changes the
      index, which changes every episode date, so this arm requires its own
      episode list built upstream while still blind. It is READ, never rebuilt
      here; if it is absent the run records the arm as NOT_RUN with the reason
      instead of skipping it silently.
  (c) **The `late` B-HEARD bound**, for C2 and pooled only, where the column is
      not identically zero.

Sensitivities are reported beside the primary and are never substituted for it.

MULTIPLE TESTING
----------------
The pre-specified primary family is 2 outcomes (`config.H1_OUTCOMES`) x 2 arms
(share, count) x 2 strata (C1, C2) = 8 tests, Benjamini-Hochberg controlled at
q = 0.05. `REWORK_PLAN.md` I3 committed this project to BH; the family definition
is fixed here and is the honest part, because a correction is only as meaningful
as the set it is applied over.

Pooled is NOT a family member: it is a summary of the same eight observations and
including it would make the correction depend on how often the same data is
described. Sensitivities, the dose and B-HEARD interaction arms, and the placebos
are outside the family and report uncorrected p-values labelled as such. A cell's
membership is in the `family` column of the output, so the correction can be
recomputed by a reader who disagrees with the definition. The column takes four
values and only the first is corrected:

    primary_H1    the 8 corrected tests: H1 outcomes x both arms x C1 and C2
    sensitivity   drop-July-2016 and the broad basket
    secondary     everything else reported beside the primary — the pooled
                  summary, the `late` B-HEARD bound, the B-HEARD interaction arm
    placebo       cardiac, injury and asthma; falsification, never confirmation

RUNTIME
-------
Deterministic whatever the parallelism. Every cell seeds its draws from its own
identity (stratum, specification, outcome, arm, bound), so a cell's result does
not depend on which cells ran before it or on how many workers ran them, and
`--jobs N` distributes cells across processes without changing a single number.
The default is one worker. Each cell is checkpointed in its own ledger, so the
multi-hour run survives the container restarts this environment is known for.

OUTPUT
------
`outputs/tables/confirmatory_results.csv` (real) or
`outputs/tables/confirmatory_results_dryrun_synthetic.csv` (dry run). Note that
`outputs/tables/*.csv` is gitignored: the sealed result must be deliberately
preserved once it exists, and Phase I's "freeze results the moment they exist"
means copying it somewhere that git tracks, not trusting the working tree.

Usage:
    python 30_confirmatory_run.py                       # after the freeze lifts
    python 30_confirmatory_run.py --dry-run-synthetic --draws 20
"""

# One BLAS thread per process, set BEFORE numpy loads. Two reasons, both measured
# on 2026-09-13: OpenBLAS starts a thread pool on first use and a process that
# forks after that (ProcessPoolExecutor) inherits a locked pool - the workers
# sat in futex_wait at 0% CPU for good - and three workers each running an
# 8-thread BLAS on a 4-core box gave a load average of 14, which is slower than
# one thread each. The estimator's fits are small; parallelism belongs at the
# cell or sim level, not inside the matrix library.
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
from pathlib import Path
import sys
import warnings
from contextlib import contextmanager

import numpy as np
import pandas as pd
import pyfixest as pf

# pyfixest warns once per fit that it dropped a collinear column. In C1 that is
# the EXPECTED and asserted behaviour of the B-HEARD control (`assert_bheard_inert`
# checks it arithmetically), and at the pre-specified 2,000 draws it would emit
# thousands of identical lines and bury everything that matters in the log.
# Shown once, never suppressed outright: a collinearity message that stopped
# appearing entirely would hide a genuinely degenerate specification.
#
# Two `warnings.filterwarnings` attempts were tried and BOTH silently did
# nothing: `module=r"pyfixest\..*"` (which matches where a warning is issued, not
# where it is raised) and then `action="once"` on the message, which still
# printed one four-line block per fit — pyfixest re-enters `catch_warnings`
# internally, so the global once-registry never suppresses anything. Each looked
# correct and neither was, which is this project's own recurring failure mode in
# miniature. The working version therefore does not configure the warnings
# module at all: `fit()` captures warnings per call and `_note_warning` prints
# each distinct one exactly once. Verified by counting the blocks, not by
# reading the filter.
_SEEN_WARNINGS = set()


@contextmanager
def collected_warnings():
    """Capture warnings from one fit and report each distinct one once."""
    with warnings.catch_warnings(record=True) as got:
        warnings.simplefilter("always")
        try:
            yield
        finally:
            for w in got:
                _note_warning(w)


def _note_warning(w):
    text = " ".join(str(w.message).split())
    key = (w.category.__name__, text[:120])
    if key in _SEEN_WARNINGS:
        return
    _SEEN_WARNINGS.add(key)
    print(f"[warn] {w.category.__name__}: {text[:200]}")

import freeze_guard
from bheard import attach as attach_bheard
import zlib
from concurrent.futures import ProcessPoolExecutor

from config import (
    BHEARD_BOUND_PRIMARY,
    BHEARD_BOUND_SENSITIVITY,
    CAI_D_BASKET,
    CONFIRMATION_ANALYSIS_WINDOWS,
    CONFIRMATION_WINDOWS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EPISODE_LIST_PRIMARY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    FREEZE_ACTIVE,
    H1_OUTCOMES,
    MH_NARROW_GROUPS,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    RANDOMIZATION_DRAWS,
    VALID_CDS,
)
from event_study import (
    admissible_days,
    build_stack,
    count_outcome,
    draw_scheme_for,
    first_week_effect,
    first_week_mean,
    randomization_p,
    require_calibrated,
    stratum_episodes,
    Uncalibrated,
)
from freeze_guard import freeze_banner, select_sample

# ---------------------------------------------------------------------------
# Pre-specified constants that have no home in config.py yet.
#
# They are HERE and not inlined at their use sites, and they are CHECKED against
# config rather than merely written down, because config.py's own opening rule is
# that a sample rule used in two places belongs in exactly one. The strata are a
# partition of `CONFIRMATION_WINDOWS` and the assertion below proves it, so these
# cannot drift away from the constants they refine. When the freeze-lift commit is
# made they should move into config.py verbatim.
# ---------------------------------------------------------------------------
# Derived from the one definition in config rather than spelled out again: the
# CP1 audit found the stratum calendar written three different ways across 18,
# 19 and this file. The partition check below still proves they refine
# CONFIRMATION_WINDOWS and leave only the treatment-free 2015 half-year unused.
C1_WINDOWS = tuple(CONFIRMATION_ANALYSIS_WINDOWS[:2])
C2_WINDOWS = tuple(CONFIRMATION_ANALYSIS_WINDOWS[2:])
assert C1_WINDOWS == (("2015-07-01", "2016-12-31"), ("2021-01-01", "2021-05-31"))
assert C2_WINDOWS == (("2021-06-01", "2024-12-31"),)
STRATUM_WINDOWS = {"C1_clean": C1_WINDOWS, "C2_exposed": C2_WINDOWS,
                   "pooled": C1_WINDOWS + C2_WINDOWS}
# Which calibration certificate each stratum's p-values rest on.
STRATUM_CALIBRATION = {"C1_clean": ("C1",), "C2_exposed": ("C2",), "pooled": ("C1", "C2")}

# The 181 days of 2015 that are inside the freeze window but carry no treatment,
# because Wikimedia daily pageviews begin 2015-07-01. Named so the log can assert
# that these and only these permitted days go unused.
NO_TREATMENT_WINDOW = ("2015-01-01", "2015-06-30")

# The Dallas attack. Used to FIND the July 2016 episode by containment rather
# than by index, so sensitivity (a) still points at the right week if the episode
# list is rebuilt and the row numbers move.
DALLAS_ATTACK_DATE = "2016-07-08"

PLACEBO_OUTCOMES = ("cardiac_share", "injury_share", "asthma_share")
BH_Q = 0.05

# The broad-basket episode list, derived from the primary list's name rather than
# spelled out, so the two cannot drift apart if EPISODE_LIST_PRIMARY changes.
EPISODE_LIST_BROAD = EPISODE_LIST_PRIMARY.replace(".csv", "_broad.csv")
# The spliced `user + automated` Wikipedia arm (CONFIRMATION_PLAN addendum 20).
EPISODE_LIST_SPLICED = EPISODE_LIST_PRIMARY.replace(".csv", "_spliced.csv")
# The coverage-break table from the declared O2 access (addendum 18), read for
# the coverage-clean sensitivity. Dates only; it carries no outcome value.
COVERAGE_BREAKS = DATA_REFERENCE / "ems_coverage_breaks.csv"
# Which outcome groups each reported outcome sums, for the coverage-clean rule.
OUTCOME_GROUPS = {
    "edp_share": {"edp"},
    "mh_narrow_share": set(MH_NARROW_GROUPS),
    "cardiac_share": {"cardiac"}, "injury_share": {"injury"}, "asthma_share": {"asthma"},
}
# Which rows of the break table belong to which stratum.
STRATUM_BREAK_LABELS = {"C1_clean": {"C1a", "C1b"}, "C2_exposed": {"C2"},
                        "pooled": {"C1a", "C1b", "C2"}}

CLUSTER_VAR = "incident_date"
SEED = 30_20260912

OUT_REAL = OUTPUTS_TABLES / "confirmatory_results.csv"
OUT_SYNTHETIC = OUTPUTS_TABLES / "confirmatory_results_dryrun_synthetic.csv"


class SealBroken(RuntimeError):
    """Raised when a precondition of the sealed run is not met."""


# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run-synthetic", action="store_true",
                    help="fabricate confirmation-period outcomes with the real "
                         "panel's shape and no real values; proves the machinery "
                         "and the guard switch without touching a real number")
parser.add_argument("--draws", type=int, default=RANDOMIZATION_DRAWS,
                    help=f"randomization draws; pre-specified value is "
                         f"{RANDOMIZATION_DRAWS} and lowering it is for the dry "
                         f"run only")
parser.add_argument("--overwrite-sealed-result", default=None, metavar="REASON",
                    help="permit overwriting an existing confirmatory_results.csv; "
                         "the reason is written into the file")
parser.add_argument("--jobs", type=int, default=1,
                    help="worker processes over cells. Every cell seeds its own draws "
                         "and keeps its own ledger, so the numbers do not depend on "
                         "this; only the wall clock does.")
ARGS = parser.parse_args()

SYNTHETIC = bool(ARGS.dry_run_synthetic)
# Ledgers are named for the data they were drawn on, so a synthetic dry run can
# never be resumed by the real run (their design fingerprints differ too).
DATA_TAG = "SYNTHETIC" if SYNTHETIC else "REAL"


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------
def check_strata_partition():
    """The strata must be a partition of the frozen confirmation windows.

    Checked on DAYS, not on endpoints. An endpoint comparison would pass for a
    stratum definition that left a hole in the middle, and this project's own
    history is a sequence of guarantees that were asserted in prose and provided
    by nothing (D3, X11, O1). The only permitted days a stratum may not claim are
    the pre-2015-07 days where the treatment index does not exist.
    """
    def days(windows):
        out = set()
        for a, b in windows:
            out |= set(pd.date_range(a, b, freq="D"))
        return out

    permitted = days(CONFIRMATION_WINDOWS)
    c1, c2 = days(C1_WINDOWS), days(C2_WINDOWS)
    if c1 & c2:
        raise SealBroken(f"C1 and C2 overlap on {len(c1 & c2):,} days")
    outside = (c1 | c2) - permitted
    if outside:
        raise SealBroken(
            f"{len(outside):,} stratum day(s) fall outside CONFIRMATION_WINDOWS, "
            f"e.g. {sorted(outside)[0].date()} — the strata may only refine the "
            "frozen windows, never widen them")
    unassigned = permitted - c1 - c2
    expected = days([NO_TREATMENT_WINDOW])
    if unassigned != expected:
        raise SealBroken(
            f"{len(unassigned):,} permitted day(s) belong to no stratum but "
            f"{len(expected):,} were expected ({NO_TREATMENT_WINDOW[0]}.."
            f"{NO_TREATMENT_WINDOW[1]}, where Wikimedia pageviews do not exist). "
            "A silently unused stretch of the confirmation sample is how a "
            "sample rule stops meaning what it says.")
    print(f"[seal] strata partition confirmed: C1 {len(c1):,} days, "
          f"C2 {len(c2):,} days, {len(unassigned):,} days dropped for want of "
          f"treatment ({NO_TREATMENT_WINDOW[0]}..{NO_TREATMENT_WINDOW[1]})")


def check_calibration():
    """Refuse to run unless EVERY stratum this script estimates is CALIBRATED.

    This is a precondition, not a robustness column (Gate C §6.3). If the
    estimator over-rejects on data built to contain no effect then the number
    this script writes is not a weak p-value, it is not a p-value. The gate also
    re-checks `n_sims_completed` against the artifact's own
    `min_sims_required`, because the committed CALIBRATED verdict was once
    produced by a 12-sim smoke test and a gate that cannot fail is not a gate
    (findings S4, X3, R3).
    """
    # PER STRATUM. This gate used to read null_calibration.csv — DISCOVERY's
    # artifact — while this script writes p-values for C1 and C2. A calibration
    # certifies one geometry and one draw scheme, and these strata share
    # neither: discovery and C2 shift an anchor within a contiguous span, C1
    # shifts circularly over a gapped one. So the old gate passed on a verdict
    # about a sample this script never estimates, and C1 — the stratum whose
    # scheme is new and whose uniformity is marginal — was the one it could
    # never have protected.
    out = {}
    for stratum in ("C1", "C2"):
        try:
            out[stratum] = require_calibrated(stratum)
        except Uncalibrated as e:
            if SYNTHETIC:
                # The dry run proves the MACHINERY, on fabricated outcomes, and
                # has to be runnable on a fresh clone before any certificate
                # exists. It writes no real number, so an absent certificate is
                # reported rather than fatal here - and fatal in real mode.
                print(f"[dry-run] {stratum}: NOT CERTIFIED ({str(e)[:90]}...) — the "
                      "synthetic run proceeds; the real run would refuse here")
                out[stratum] = pd.Series({"n_sims_completed": np.nan, "draw_scheme": "uncertified"})
                continue
            raise SealBroken(str(e)) from e
    return out


def check_freeze_state():
    """The flag decides which of the two modes is legal. Never both.

    Real mode requires the freeze LIFTED, because reading confirmation outcomes
    under an active freeze is the incident this whole apparatus exists to
    prevent. Synthetic mode requires the freeze ACTIVE, because fabricated
    numbers produced after the lift could be mistaken for the sealed result, and
    that is the D1 clobber with worse consequences.
    """
    if SYNTHETIC and not FREEZE_ACTIVE:
        raise SealBroken(
            "--dry-run-synthetic requires FREEZE_ACTIVE=True. The freeze is "
            "lifted, so the dry run has no purpose and fabricated numbers beside "
            "a real result are a hazard, not a check.")
    if not SYNTHETIC and FREEZE_ACTIVE:
        raise SealBroken(
            "FREEZE_ACTIVE is True. This script reads confirmation-window "
            "outcomes and MUST NOT run while the freeze holds. Two freeze "
            "incidents are already on the record (PAPER_MASTER.md §5.3); a third "
            "would end the pre-registration's value.\n"
            "  To exercise the machinery now:  --dry-run-synthetic\n"
            "  To run for real: lift the freeze in its own commit, after CP2, "
            "then re-run with no arguments.")


# ---------------------------------------------------------------------------
# Synthetic dry run
# ---------------------------------------------------------------------------
@contextmanager
def simulated_freeze_lift():
    """Patch the guard's own flag so the synthetic run can exercise the switch.

    This is the only place in the project that touches `FREEZE_ACTIVE` at
    runtime, and it is dangerous by nature, so it is fenced three ways:

      * it raises unless SYNTHETIC is set, so it cannot be reached in a real run;
      * `load_real_panel()` raises whenever SYNTHETIC is set, so no code path can
        read the real panel while the patch is in effect — the patch cannot open
        anything, because the only door it could open is bolted from the other
        side;
      * `config.FREEZE_ACTIVE` itself is never written, only the name the guard
        module resolved at import, and the original is restored in a finally.

    What it proves is the thing that cannot otherwise be proved before the lift:
    that `freeze_guard.select_sample` SWITCHES sample rather than widening one.
    That distinction is finding D3 and it is the difference between a
    confirmatory estimate and a discovery-contaminated one reported as
    confirmatory.
    """
    if not SYNTHETIC:
        raise SealBroken("the freeze flag may only be simulated in synthetic mode")
    original = freeze_guard.FREEZE_ACTIVE
    freeze_guard.FREEZE_ACTIVE = False
    try:
        yield
    finally:
        freeze_guard.FREEZE_ACTIVE = original
        assert freeze_guard.FREEZE_ACTIVE is original
        from config import FREEZE_ACTIVE as still
        if still is not True:
            raise SealBroken("config.FREEZE_ACTIVE was mutated; refusing to continue")


def prove_guard_switches():
    """Show the guard keeps discovery while frozen and confirmation once lifted.

    Run on a two-column probe frame that carries dates and a marker and NOTHING
    else — no outcome column exists for it to leak. The assertion is arithmetic
    (row counts by window), not a grep for a function name: a source grep proves
    the code SAYS the right thing, and at least fifteen checks in this project
    have passed for the wrong reason (`PAPER_MASTER.md` §7.5).
    """
    probe = pd.DataFrame({
        "incident_date": pd.date_range("2015-01-01", "2024-12-31", freq="D"),
    })
    probe["_synthetic_probe"] = 1
    assert list(probe.columns) == ["incident_date", "_synthetic_probe"]

    frozen = select_sample(probe, where="30:probe(frozen)")
    d = frozen["incident_date"]
    if not (d.min() == pd.Timestamp("2017-01-01") and d.max() == pd.Timestamp("2020-12-31")):
        raise SealBroken(f"frozen guard returned {d.min().date()}..{d.max().date()}, "
                         "expected the discovery window")

    with simulated_freeze_lift():
        lifted = select_sample(probe, where="30:probe(lifted)")
    d2 = lifted["incident_date"]
    disc = d2.between(pd.Timestamp("2017-01-01"), pd.Timestamp("2020-12-31"))
    if disc.any():
        raise SealBroken(f"{int(disc.sum()):,} discovery days survived the lifted "
                         "guard; the samples are not disjoint")
    expected = sum((pd.Timestamp(b) - pd.Timestamp(a)).days + 1
                   for a, b in CONFIRMATION_WINDOWS)
    if len(d2) != expected:
        raise SealBroken(f"lifted guard returned {len(d2):,} days, expected {expected:,}")

    print(f"[dry-run] guard switch proven on a {len(probe):,}-day probe: frozen "
          f"-> {len(frozen):,} discovery days; lifted -> {len(d2):,} confirmation "
          f"days, 0 of them discovery")


def synthetic_panel(rng):
    """A confirmation-window panel with the real panel's SHAPE and no real values.

    SHAPE means: the real panel's column names and dtypes, read from the parquet
    FOOTER via pyarrow's schema reader, which decodes no row group and therefore
    no outcome value; the 59 community districts from `config.VALID_CDS`; and the
    calendar of the confirmation windows. Every number is drawn from this
    function's own generator.

    It is deliberately NOT calibrated to the discovery panel's moments. Discovery
    moments would be legal — that sample has been explored freely — but the point
    of this run is to prove the machinery is well formed, and a well-formed
    pipeline is well formed on any plausible numbers. Using none at all makes the
    claim "no real value entered this" checkable rather than argued.

    A `_synthetic` marker column rides along so a fabricated frame is
    identifiable anywhere downstream, and every output row is stamped
    `data_source=SYNTHETIC`.
    """
    import pyarrow.parquet as pq

    src = DATA_PROCESSED / "panel_cd_day.parquet"
    if src.exists():
        schema = pq.read_schema(src)          # footer only; no row group is read
        cols = list(schema.names)
        print(f"[dry-run] shape taken from {src.name}: {len(cols)} columns, "
              "schema footer only, zero rows read")
    else:
        cols = ["incident_date", "communitydistrict", "total_calls", "dow",
                "edp", "mh_narrow", "cardiac", "injury", "asthma",
                "edp_share", "mh_narrow_share", "cardiac_share",
                "injury_share", "asthma_share"]
        print(f"[dry-run] {src.name} absent; using the documented column set")

    dates = pd.DatetimeIndex([])
    for a, b in CONFIRMATION_WINDOWS:
        dates = dates.union(pd.date_range(a, b, freq="D"))
    cds = list(VALID_CDS)
    n = len(dates) * len(cds)

    out = pd.DataFrame({
        "incident_date": np.tile(dates, len(cds)),
        "communitydistrict": np.repeat(cds, len(dates)),
    })
    out["total_calls"] = rng.integers(20, 140, n)
    for grp, base in (("edp", 0.06), ("altmen", 0.02), ("suicide_jump", 0.004),
                      ("od_poison_drug", 0.01), ("cardiac", 0.11),
                      ("injury", 0.19), ("asthma", 0.05)):
        out[grp] = rng.binomial(out["total_calls"].to_numpy(), base)
    out["mh_narrow"] = out[["edp", "altmen", "suicide_jump"]].sum(axis=1)
    out["mh_broad"] = out["mh_narrow"] + out["od_poison_drug"]
    out["other"] = (out["total_calls"]
                    - out[["mh_broad", "cardiac", "injury", "asthma"]].sum(axis=1)).clip(lower=0)
    for c in ("edp", "altmen", "suicide_jump", "od_poison_drug", "mh_narrow",
              "mh_broad", "cardiac", "injury", "asthma"):
        out[f"{c}_share"] = out[c] / out["total_calls"]
    out["dow"] = out["incident_date"].dt.dayofweek
    out["month"] = out["incident_date"].dt.month
    out["year"] = out["incident_date"].dt.year
    out["_synthetic"] = 1

    missing = [c for c in cols if c not in out.columns]
    if missing:
        print(f"[dry-run] columns present in the real schema but not fabricated: "
              f"{missing} — not used by this estimator")
    print(f"[dry-run] fabricated {len(out):,} rows x {len(out.columns)} columns "
          f"over {len(dates):,} days and {len(cds)} districts, "
          f"{out['incident_date'].min().date()}..{out['incident_date'].max().date()}")
    return out


# ---------------------------------------------------------------------------
# Real panel
# ---------------------------------------------------------------------------
def load_real_panel():
    """The confirmation panel, through the guard, never around it.

    Raises in synthetic mode. That is what makes `simulated_freeze_lift()` safe:
    while the guard's flag is patched, the only function that can open the real
    panel refuses, so the patch cannot be used to read anything.
    """
    if SYNTHETIC:
        raise SealBroken("refusing to read the real panel in synthetic dry-run mode")
    panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
    panel["incident_date"] = pd.to_datetime(panel["incident_date"])
    panel = select_sample(panel, where="30_confirmatory_run")
    return panel


def prepare(panel):
    """Sample rules and the B-HEARD control, applied once for every stratum."""
    panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
    panel["dow"] = panel["incident_date"].dt.dayofweek
    return panel


# ---------------------------------------------------------------------------
# Strata
# ---------------------------------------------------------------------------
def _mask(dates, windows):
    m = pd.Series(False, index=dates.index)
    for a, b in windows:
        m |= dates.between(pd.Timestamp(a), pd.Timestamp(b))
    return m


def split_strata(panel):
    """Partition the permitted sample into C1, C2 and pooled.

    The unassigned days are COUNTED and reported rather than filtered away, and
    the count is checked against the treatment-free stretch the partition check
    already established. A stratum definition that quietly dropped a year would
    look exactly like one that did not.
    """
    d = panel["incident_date"]
    c1, c2 = _mask(d, C1_WINDOWS), _mask(d, C2_WINDOWS)
    dropped = int((~(c1 | c2)).sum())
    if dropped:
        lost = d[~(c1 | c2)]
        print(f"[strata] {dropped:,} permitted row(s) belong to no stratum "
              f"({lost.min().date()}..{lost.max().date()}): before 2015-07-01 the "
              "Wikimedia pageviews API has no data, so the treatment does not exist")
    return {
        "C1_clean": panel[c1].copy(),
        "C2_exposed": panel[c2].copy(),
        "pooled": panel[c1 | c2].copy(),
    }


def episodes_for(ep, windows, stratum_panel):
    """Episodes a stratum can test: FIRST-WEEK CONTAINMENT (addendum 17), through
    the one implementation the calibration also uses.

    This used to keep any episode whose START fell inside the stratum panel's
    date range - a second rule, agreeing with the pre-specified one on today's
    list only by measurement (CP1 audit). `event_study.stratum_episodes` keeps an
    episode when day -1 through day +7 lie inside one of the stratum's windows,
    which is what 18 calibrates on, and reports what each dropped episode lost.
    A kept start must also have panel rows; a stratum that lacks them is
    reported rather than estimated on a truncated design.
    """
    kept, dropped = stratum_episodes(ep["start"], windows, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    keep_starts = {pd.Timestamp(k["start"]) for k in kept}
    for d in dropped:
        print(f"  [episodes] dropped {pd.Timestamp(d['start']).date()}: "
              f"{d.get('reason', 'first week not inside the stratum')}")
    out = ep[ep["start"].isin(keep_starts)]
    have = set(stratum_panel["incident_date"].unique())
    missing = out[~out["start"].isin(have)]
    if len(missing):
        raise SealBroken(f"{len(missing)} episode start(s) have no panel rows in this "
                         f"stratum: {missing['start'].dt.date.tolist()}")
    return out.sort_values("start").reset_index(drop=True)


def assert_bheard_inert(stack, outcome, label):
    """In a stratum with no B-HEARD exposure, the control must change nothing.

    Arithmetic, not assertion-by-comment. If the estimate moves when an
    identically-zero column is added, the precinct-to-community-district
    crosswalk is wrong — and that error would otherwise surface only in the
    confirmatory run, where it cannot be fixed. This is X.bheard_wired's inert
    half applied to the clean stratum, on the shared estimator.
    """
    if "bheard_exposure" not in stack.columns:
        return None
    mx = float(stack["bheard_exposure"].max())
    if mx > 0:
        return None
    with_c = first_week_effect(stack, outcome, extra=("bheard_exposure",))
    without = first_week_effect(stack, outcome, extra=())
    if with_c is None or without is None:
        return None
    delta = abs(with_c - without)
    print(f"[check] {label}: B-HEARD exposure is 0 throughout; the control moves "
          f"the {outcome} statistic by {delta:.3e}")
    if delta > 1e-6:
        raise SealBroken(
            f"{label}: adding an identically-zero B-HEARD column moved the "
            f"{outcome} statistic by {delta:.3e}. The exposure table or the "
            "crosswalk is wrong and the confirmatory estimate cannot be trusted.")
    return delta
def randomization(panel, real_starts, outcome, pre, post, draws, windows, cell,
                  extra=("bheard_exposure",), counts=False, label=""):
    """Episode-level randomization inference through event_study.randomization_p.

    Returns a dict carrying the observed statistic, the p-value, and — the part
    that must never be dropped from the output — WHICH null produced it. The
    scheme comes from `draw_scheme_for` on the stratum's own windows, so it is
    the scheme the stratum's calibration certifies; the draws are seeded from
    `cell` and banked in a per-cell ledger whose identity is the design.
    """
    obs_stack = build_stack(panel, real_starts, pre, post)
    with collected_warnings():
        obs, k = first_week_effect(obs_stack, outcome, counts=counts, extra=extra,
                                   return_n=True)
        mean_coef = (first_week_mean(obs_stack, outcome, counts=counts, extra=extra)
                     if obs is not None else None)
    res = {"first_week_chi2": obs, "first_week_mean_coef": mean_coef,
           "n_first_week_coefs": k, "n_obs": len(obs_stack),
           "p_randomization": np.nan, "n_draws": 0, "null_sd": np.nan,
           "ri_scheme": None, "ri_exact": 0,
           "n_admissible_starts": len(admissible_days(windows, pre, post))}
    if obs is None:
        res["status"] = "NOT_ESTIMABLE: the observed design yields no first-week statistic"
        return res
    scheme, why = draw_scheme_for(windows, real_starts, pre, post)
    res["ri_scheme"] = scheme
    if scheme == "none":
        res["status"] = f"RI_NOT_RUN: {why}"
        return res
    ledger = OUTPUTS_TABLES / f"ri_ledger_confirmatory_{DATA_TAG}_{cell}.csv"
    seed = zlib.crc32(cell.encode()) ^ SEED
    print(f"  [RI] {label}: {scheme} — {why}; {draws} draws; ledger {ledger.name}")
    with collected_warnings():
        obs2, p, stats_ = randomization_p(
            panel, real_starts, outcome, pre, post, draws, np.random.default_rng(seed),
            counts=counts, windows=windows, ledger=ledger, seed=seed, extra=extra)
    if obs2 is not None and abs(obs2 - obs) > 1e-9:
        raise SealBroken(f"{label}: the observed statistic differs between the two "
                         f"calls ({obs} vs {obs2}); the estimator is not deterministic")
    if obs2 is None or len(stats_) == 0:
        res["status"] = "RI_NOT_RUN: every placebo draw was discarded"
        return res
    res.update({"p_randomization": float(p), "n_draws": int(len(stats_)),
                "null_sd": float(stats_.std()) if len(stats_) > 1 else np.nan,
                "status": "OK"})
    return res
def benjamini_hochberg(p):
    """Step-up BH adjusted p-values, monotone by construction.

    Applied only to rows whose `family` is the pre-specified primary family. A
    correction is only as meaningful as the set it is applied over, so the set is
    written into the output and a reader who disagrees with it can recompute.
    """
    p = np.asarray(p, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty(n)
    prev = 1.0
    for rank, i in enumerate(order[::-1]):
        k = n - rank
        prev = min(prev, p[i] * n / k)
        adj[i] = prev
    return adj


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def july_2016_episode(ep):
    """The episode containing the Dallas attack, found by containment.

    Sterling (2016-07-05), Castile (2016-07-06) and the Dallas attack
    (2016-07-07/08) fall in one week, and the last of those is attention to
    violence AGAINST police, which plausibly moves EMS demand the other way. The
    basket excludes Micah Xavier Johnson's article, but excluding an article does
    not remove a week from the calendar, so the episode itself is the
    sensitivity. Found by date containment so a rebuilt episode list moves the
    row and not the target.
    """
    day = pd.Timestamp(DALLAS_ATTACK_DATE)
    hit = ep[(ep["start"] <= day) & (ep["end"] >= day)]
    return hit


def load_episodes(filename, require=True):
    f = DATA_REFERENCE / filename
    if not f.exists():
        if require:
            raise SealBroken(f"{f} is absent; the episode list is not optional")
        return None
    ep = pd.read_csv(f, parse_dates=["start", "end"])
    return ep[ep["period"] == "extension"].sort_values("start").reset_index(drop=True)


def run_cell(rows, panel, ep, stratum, outcome, arm_counts, spec, family,
             extra, draws, bound, episode_set, windows, note=""):
    """One reported number, with everything needed to read it beside it."""
    col = count_outcome(outcome) if arm_counts else outcome
    arm = "PPML" if arm_counts else "OLS"
    label = f"{stratum}/{spec}/{col}/{arm}"
    cell = f"{stratum}_{spec}_{col}_{arm.lower()}_{bound}"
    if col not in panel.columns:
        rows.append(_row(stratum, col, arm_counts, spec, family, bound,
                         episode_set, len(ep), note=f"{note} outcome column absent",
                         status="NOT_RUN: outcome column absent"))
        return
    starts = ep["start"].tolist()
    if len(starts) < 2:
        rows.append(_row(stratum, col, arm_counts, spec, family, bound,
                         episode_set, len(ep), note=note,
                         status=f"NOT_RUN: {len(starts)} episode(s) in this stratum"))
        return
    res = randomization(panel, starts, col, EVENT_WINDOW_PRE, EVENT_WINDOW_POST,
                        draws, windows, cell, extra=extra, counts=arm_counts, label=label)
    rows.append(_row(stratum, col, arm_counts, spec, family, bound, episode_set,
                     len(ep), note=note,
                     n_districts=panel["communitydistrict"].nunique(), **res))
    chi = res.get("first_week_chi2")
    p = res.get("p_randomization")
    print(f"  {label:58s} chi2={chi if chi is None else round(chi, 2)!s:>10} "
          f"p_RI={p if p is None or np.isnan(p) else round(p, 4)!s:>8}  "
          f"[{res.get('status')}]")


def execute_job(job):
    """One cell, in whichever process runs it. Returns the single result row."""
    rows = []
    run_cell(rows, job["panel"], job["ep"], job["stratum"], job["outcome"],
             job["counts"], job["spec"], job["family"], ("bheard_exposure",),
             ARGS.draws, job["bound"], job["episode_set"], job["windows"],
             note=job.get("note", ""))
    return rows[0]


def coverage_breaks_for(breaks, stratum, outcome):
    """Break dates (addendum 18) that bear on this outcome in this stratum:
    a code in one of the outcome's groups born or retired inside the stratum,
    or the geocoding step. Dates only."""
    if breaks is None:
        return None
    groups = OUTCOME_GROUPS.get(outcome, set())
    m = (breaks["window"].isin(STRATUM_BREAK_LABELS[stratum])
         & (breaks["group"].isin(groups) | (breaks["group"] == "(geocoding)")))
    return breaks[m]


def drop_break_windows(ep, dates):
    """Episodes whose [-pre, +post] window contains none of `dates`."""
    lo = ep["start"] - pd.Timedelta(days=EVENT_WINDOW_PRE)
    hi = ep["start"] + pd.Timedelta(days=EVENT_WINDOW_POST)
    hit = pd.Series(False, index=ep.index)
    for d in dates:
        d = pd.Timestamp(d)
        hit |= (lo <= d) & (d <= hi)
    return ep[~hit].reset_index(drop=True), int(hit.sum())
def _row(stratum, outcome, arm_counts, spec, family, bound, episode_set,
         n_episodes, note="", status="OK", n_districts=np.nan, **kw):
    row = {
        "stratum": stratum,
        "outcome": outcome,
        "estimator": "PPML_count_offset" if arm_counts else "OLS_share",
        "spec": spec,
        "family": family,
        "bheard_bound": bound,
        "episode_set": episode_set,
        "n_episodes": n_episodes,
        "n_districts": n_districts,
        "post_window": EVENT_WINDOW_POST,
        "first_week_chi2": np.nan,
        "first_week_mean_coef": np.nan,
        "n_first_week_coefs": np.nan,
        "p_randomization": np.nan,
        "p_asymptotic": np.nan,
        "p_bh_adjusted": np.nan,
        "ri_scheme": None,
        "ri_exact": np.nan,
        "n_draws": 0,
        "n_admissible_starts": np.nan,
        "null_sd": np.nan,
        "n_obs": np.nan,
        "status": status,
        "note": note,
        "data_source": "SYNTHETIC" if SYNTHETIC else "REAL",
    }
    row.update({k: v for k, v in kw.items() if k in row})
    return row


def bheard_identification(rows, panel, ep, stratum, outcome, arm_counts, bound):
    """The staggered roll-out as identification: effect per unit of exposure.

    `y ~ _post + _post:bheard_exposure + bheard_exposure | ep_cd + dow`. The
    binary `_post` is the citywide first-week indicator; the interaction is
    identified from the cross-district spread of exposure (4e-06 to 1.0 over 30
    of 59 districts) WITHIN each episode, which the episode x district fixed
    effect makes a clean comparison.

    No randomization p-value, for the same reason the dose-response arm carries
    none (finding D6): permuting episode dates holds exposure fixed, so it tests
    a different null from the one this coefficient speaks to. The asymptotic p is
    reported and LABELLED asymptotic rather than a blank RI column, because an
    empty column reads as an oversight and a mislabelled one reads as a result.
    """
    col = count_outcome(outcome) if arm_counts else outcome
    d = build_stack(panel, ep["start"].tolist(), EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    spec = "bheard_interaction"
    if d.empty or "bheard_exposure" not in d.columns or d["bheard_exposure"].max() <= 0:
        rows.append(_row(stratum, col, arm_counts, spec, "secondary", bound,
                         "primary", len(ep),
                         status="NOT_RUN: no B-HEARD exposure in this stratum"))
        return
    d = d.dropna(subset=[col]).copy()
    d["_post"] = d["rel_day"].isin(range(0, 8)).astype(float)
    d["_post_bheard"] = d["_post"] * d["bheard_exposure"]
    fml = f"{col} ~ _post + _post_bheard + bheard_exposure | ep_cd + dow"
    vcov = {"CRV1": CLUSTER_VAR}
    try:
        if arm_counts:
            d = d[d["total_calls"] > 0].copy()
            d["log_total"] = np.log(d["total_calls"])
            m = pf.fepois(fml, d, vcov=vcov, offset="log_total")
        else:
            m = pf.feols(fml, d, vcov=vcov)
    except Exception as e:
        _note_failure(fml, arm_counts, e)
        rows.append(_row(stratum, col, arm_counts, spec, "secondary", bound,
                         "primary", len(ep),
                         status=f"NOT_ESTIMABLE: {type(e).__name__}"))
        return
    k = "_post_bheard"
    rows.append(_row(stratum, col, arm_counts, spec, "secondary", bound, "primary",
                     len(ep), n_districts=d["communitydistrict"].nunique(),
                     first_week_mean_coef=float(m.coef()[k]),
                     p_asymptotic=float(m.pvalue()[k]),
                     n_obs=len(d),
                     note=(f"effect per unit B-HEARD exposure; exposure range "
                           f"{d['bheard_exposure'].min():.2g}.."
                           f"{d['bheard_exposure'].max():.2g}; asymptotic p only, "
                           f"see the docstring")))
    print(f"  {stratum}/{spec}/{col}: coef/exposure={m.coef()[k]:+.5f} "
          f"p_asy={m.pvalue()[k]:.4f}")


def main():
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("30_confirmatory_run — the sealed one-shot confirmatory analysis")
    print("=" * 78)
    freeze_banner("30_confirmatory_run")

    check_freeze_state()
    check_strata_partition()
    cal = check_calibration()
    if CAI_D_BASKET != "strict":
        raise SealBroken(f"config.CAI_D_BASKET is {CAI_D_BASKET!r}; the primary "
                         "arm is the strict basket and broad is the sensitivity")

    out_path = OUT_SYNTHETIC if SYNTHETIC else OUT_REAL
    if not SYNTHETIC and out_path.exists() and not ARGS.overwrite_sealed_result:
        raise SealBroken(
            f"{out_path} already exists. Phase I freezes results the moment they "
            "exist, and this project has already lost a gating artifact to a "
            "re-run (finding D1). To replace it, pass "
            "--overwrite-sealed-result 'the reason', which is recorded in the file.")
    if ARGS.draws != RANDOMIZATION_DRAWS:
        print(f"[seal] NOTE: --draws {ARGS.draws} overrides the pre-specified "
              f"{RANDOMIZATION_DRAWS}. This is legitimate for the dry run and is "
              f"a disclosed deviation for anything else.")
        if not SYNTHETIC:
            print("[seal] the override is recorded in every output row.")

    rng = np.random.default_rng(SEED)

    # -- panel ------------------------------------------------------------
    if SYNTHETIC:
        prove_guard_switches()
        with simulated_freeze_lift():
            raw = synthetic_panel(rng)
            panel = select_sample(raw, where="30:synthetic")
        panel = prepare(panel)
    else:
        panel = prepare(load_real_panel())

    strata = split_strata(panel)
    ep_primary = load_episodes(EPISODE_LIST_PRIMARY)
    ep_broad = load_episodes(EPISODE_LIST_BROAD, require=False)
    ep_spliced = load_episodes(EPISODE_LIST_SPLICED, require=False)
    breaks = (pd.read_csv(COVERAGE_BREAKS, dtype=str) if COVERAGE_BREAKS.exists() else None)
    jul = july_2016_episode(ep_primary)
    print(f"[seal] episode lists: primary {EPISODE_LIST_PRIMARY} "
          f"({len(ep_primary)} extension episodes); broad "
          f"{EPISODE_LIST_BROAD} ({'absent' if ep_broad is None else len(ep_broad)}); "
          f"spliced {EPISODE_LIST_SPLICED} "
          f"({'absent' if ep_spliced is None else len(ep_spliced)})")
    print(f"[seal] coverage-break table: "
          f"{'absent' if breaks is None else f'{len(breaks)} row(s)'} ({COVERAGE_BREAKS.name})")
    print(f"[seal] July 2016 sensitivity targets {len(jul)} episode(s) containing "
          f"{DALLAS_ATTACK_DATE}"
          + (f": {jul['start'].dt.date.tolist()}" if len(jul) else ""))

    rows, jobs = [], []

    def add(stratum, sp, ep, outcome, counts, spec, family, bound, episode_set, note=""):
        jobs.append(dict(stratum=stratum, panel=sp, ep=ep, outcome=outcome, counts=counts,
                         spec=spec, family=family, bound=bound, episode_set=episode_set,
                         windows=STRATUM_WINDOWS[stratum], note=note))

    for stratum, spanel in strata.items():
        windows = STRATUM_WINDOWS[stratum]
        if spanel.empty:
            rows.append(_row(stratum, "-", False, "primary", "primary_H1",
                             BHEARD_BOUND_PRIMARY, "primary", 0,
                             status="NOT_RUN: stratum is empty"))
            continue
        print("\n" + "-" * 78)
        print(f"STRATUM {stratum}: {len(spanel):,} district-days, "
              f"{spanel['incident_date'].min().date()}.."
              f"{spanel['incident_date'].max().date()}, "
              f"{spanel['communitydistrict'].nunique()} districts; "
              f"{len(windows)} window(s), "
              f"{len(admissible_days(windows, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)):,} "
              "admissible placebo start(s)")

        for bound in (BHEARD_BOUND_PRIMARY, BHEARD_BOUND_SENSITIVITY):
            sp = attach_bheard(spanel, bound=bound)
            mx = float(sp["bheard_exposure"].max())
            is_primary_bound = bound == BHEARD_BOUND_PRIMARY
            if not is_primary_bound and mx <= 0:
                print(f"  [{bound} bound] exposure is 0 throughout; the bound "
                      "sensitivity is identical to the primary and is not re-run")
                continue
            print(f"  [{bound} bound] max exposure {mx:.6g}")

            ep_here = episodes_for(ep_primary, windows, sp)
            if is_primary_bound and mx <= 0 and len(ep_here) >= 2:
                stack = build_stack(sp, ep_here["start"].tolist(),
                                    EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
                if not stack.empty:
                    assert_bheard_inert(stack, H1_OUTCOMES[0], stratum)

            spec = "primary" if is_primary_bound else "sens_bheard_late_bound"
            for outcome in list(H1_OUTCOMES):
                fam = ("primary_H1" if is_primary_bound
                       and stratum in ("C1_clean", "C2_exposed") else "secondary")
                for counts in (False, True):
                    add(stratum, sp, ep_here, outcome, counts, spec, fam, bound, "primary")
            if not is_primary_bound:
                continue

            for outcome in PLACEBO_OUTCOMES:
                for counts in (False, True):
                    add(stratum, sp, ep_here, outcome, counts, "placebo", "placebo", bound,
                        "primary", note="falsification, not confirmation")

            # (a) drop the July 2016 episode
            drop = ep_here[~ep_here["start"].isin(jul["start"])]
            if len(drop) == len(ep_here):
                print("  [sens] no July 2016 episode in this stratum; the "
                      "drop-July-2016 arm would be identical to the primary "
                      "and is not re-run")
            else:
                for outcome in list(H1_OUTCOMES):
                    for counts in (False, True):
                        add(stratum, sp, drop, outcome, counts, "sens_drop_jul2016",
                            "sensitivity", bound, "primary_minus_jul2016",
                            note="Sterling + Castile + the Dallas attack")

            # (b) the broad basket, (d) the spliced Wikipedia series: both are
            # READ, never rebuilt here, and recorded NOT_RUN if absent.
            for spec_name, ep_alt, listname, note in (
                    ("sens_broad_basket", ep_broad, EPISODE_LIST_BROAD,
                     "broad basket: +9 civilian-actor articles"),
                    ("sens_spliced_wiki", ep_spliced, EPISODE_LIST_SPLICED,
                     "user+automated Wikipedia series (addendum 20)")):
                if ep_alt is None:
                    for outcome in list(H1_OUTCOMES):
                        rows.append(_row(
                            stratum, outcome, False, spec_name, "sensitivity", bound,
                            listname, 0,
                            status=f"NOT_RUN: episode list {listname} absent",
                            note="build it upstream BEFORE the freeze lifts; rebuilding "
                                 "the treatment index after the lift is not blind"))
                    continue
                ep_a = episodes_for(ep_alt, windows, sp)
                for outcome in list(H1_OUTCOMES):
                    for counts in (False, True):
                        add(stratum, sp, ep_a, outcome, counts, spec_name, "sensitivity",
                            bound, listname, note=note)

            # (c) coverage-clean (addendum 18): per outcome, drop every episode
            # whose window contains a recording break in that outcome's codes or
            # the geocoding step. One cell per outcome and arm; identical-to-
            # primary when nothing is dropped.
            for outcome in list(H1_OUTCOMES) + list(PLACEBO_OUTCOMES):
                br = coverage_breaks_for(breaks, stratum, outcome)
                if br is None:
                    rows.append(_row(stratum, outcome, False, "sens_coverage_clean",
                                     "sensitivity", bound, "primary", len(ep_here),
                                     status=f"NOT_RUN: {COVERAGE_BREAKS.name} absent"))
                    continue
                if br.empty:
                    continue
                ep_c, n_drop = drop_break_windows(ep_here, br["date"].tolist())
                desc = "; ".join(f"{r.final_call_type or r.group} {r.kind} {r.date}"
                                 for r in br.itertuples())
                if n_drop == 0:
                    rows.append(_row(stratum, outcome, False, "sens_coverage_clean",
                                     "sensitivity", bound, "primary", len(ep_here),
                                     status="IDENTICAL_TO_PRIMARY: no episode window "
                                            "contains a break", note=desc))
                    continue
                for counts in (False, True):
                    add(stratum, sp, ep_c, outcome, counts, "sens_coverage_clean",
                        "sensitivity", bound, f"primary_minus_{n_drop}_break_window(s)",
                        note=desc)

    print(f"\n[seal] {len(jobs)} randomization cell(s) to estimate at {ARGS.draws} draws "
          f"on {max(1, ARGS.jobs)} worker(s); every cell seeds and ledgers itself")
    if ARGS.jobs > 1:
        # SPAWN, not fork. A forked worker inherits every lock the parent's
        # threads held at the fork, and this parent has already fitted models
        # (the B-HEARD inertness assertion) before the pool starts: with fork
        # both workers sat in futex_wait at 0% CPU indefinitely, twice, even
        # with BLAS pinned to one thread (2026-09-13). A spawned worker starts
        # from a clean interpreter, re-imports this module (argparse sees the
        # same argv; main() is guarded), and receives each job by pickle.
        import multiprocessing as mp
        with ProcessPoolExecutor(max_workers=ARGS.jobs,
                                 mp_context=mp.get_context("spawn")) as ex:
            rows.extend(ex.map(execute_job, jobs, chunksize=1))
    else:
        for job in jobs:
            rows.append(execute_job(job))

    # B-HEARD as identification, where there is exposure (fast, single fits).
    for stratum, spanel in strata.items():
        if spanel.empty:
            continue
        sp = attach_bheard(spanel, bound=BHEARD_BOUND_PRIMARY)
        if float(sp["bheard_exposure"].max()) <= 0:
            continue
        ep_here = episodes_for(ep_primary, STRATUM_WINDOWS[stratum], sp)
        for outcome in list(H1_OUTCOMES):
            for counts in (False, True):
                bheard_identification(rows, sp, ep_here, stratum, outcome, counts,
                                      BHEARD_BOUND_PRIMARY)

    res = pd.DataFrame(rows)

    # -- multiple testing across the pre-specified family -------------------
    fam = (res["family"] == "primary_H1") & res["p_randomization"].notna()
    if fam.any():
        res.loc[fam, "p_bh_adjusted"] = benjamini_hochberg(
            res.loc[fam, "p_randomization"].to_numpy())
        print(f"\n[BH] Benjamini-Hochberg at q={BH_Q} over the pre-specified "
              f"family of {int(fam.sum())} test(s) "
              f"(2 outcomes x 2 arms x 2 strata when complete)")
        n_sig = int((res.loc[fam, "p_bh_adjusted"] < BH_Q).sum())
        print(f"[BH] {n_sig} of {int(fam.sum())} survive at q={BH_Q}")
    else:
        print("\n[BH] no family member produced a randomization p-value; "
              "the correction is not applied and the column stays empty")

    res["draws_requested"] = ARGS.draws
    res["draws_prespecified"] = RANDOMIZATION_DRAWS
    # The certificate each row rests on, PER STRATUM: pooled rests on both.
    def _sims(s):
        if s not in STRATUM_CALIBRATION:
            return np.nan
        vals = [float(cal[c]["n_sims_completed"]) for c in STRATUM_CALIBRATION[s]]
        return np.nan if any(np.isnan(v) for v in vals) else int(min(vals))   # NaN: uncertified dry run
    res["calibration_sims"] = res["stratum"].map(_sims)
    res["calibration_scheme"] = res["stratum"].map(
        lambda s: "+".join(str(cal[c].get("draw_scheme", "?")) for c in STRATUM_CALIBRATION[s])
        if s in STRATUM_CALIBRATION else "")
    res["freeze_active_at_run"] = int(FREEZE_ACTIVE)
    res["overwrite_reason"] = ARGS.overwrite_sealed_result or ""
    res.to_csv(out_path, index=False)
    # A sidecar naming the CODE that produced this file, so a check can tell a
    # dry run that proved the current script from one that proved an older one.
    # The CP2 line "30 dry-run on synthetic outcomes" is only evidence while the
    # fingerprints match.
    import json
    from datetime import datetime, timezone
    from provenance import code_fingerprint
    out_path.with_suffix(".meta.json").write_text(json.dumps({
        "script_code_sha256": code_fingerprint(Path(__file__)),
        "event_study_code_sha256": code_fingerprint(Path(__file__).with_name("event_study.py")),
        "rows": int(len(res)), "draws": int(ARGS.draws), "jobs": int(ARGS.jobs),
        "data_source": DATA_TAG,
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=1))

    print("\n" + "=" * 78)
    print(f"wrote {out_path.name}: {len(res)} rows "
          f"({'SYNTHETIC — no real number entered this file' if SYNTHETIC else 'REAL'})")
    if SYNTHETIC:
        print("The dry run proves the machinery is well formed and that the guard")
        print("switches sample. It says NOTHING about any hypothesis.")
    print("=" * 78)
    return res


if __name__ == "__main__":
    try:
        main()
    except SealBroken as e:
        print("\n" + "!" * 78)
        print(f"SEAL REFUSED: {e}")
        print("!" * 78)
        sys.exit(3)
