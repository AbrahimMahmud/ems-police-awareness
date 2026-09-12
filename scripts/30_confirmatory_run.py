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

  * **Where the calibrated scheme is feasible** (one contiguous block, slack >= 0)
    it is used, by calling `event_study.placebo_starts` itself. C2 and any
    discovery replication take this path. Nothing is re-implemented.
  * **Otherwise** placebo starts are drawn by CIRCULAR SHIFT over the stratum's
    *admissible* days: the days whose reference day (-1) and whole first week
    (0..+7) lie inside the stratum's covered dates, which is precisely the
    coverage `event_study.first_week_effect` requires of a design before it will
    return a statistic. Shifting the whole real sequence by a constant number of
    admissible-day positions preserves the episodes' spacing in observed-day
    units, always fits, and always yields exactly as many episodes as the real
    design. Note that admissibility asks for day -1 and the first week, NOT the
    full 14-day pre-window: the real C1 episode of 2021-01-05 does not have a
    full pre-window either (the stratum starts 2021-01-01), and a placebo bar
    stricter than the observed design would compare unlike things.
  * When the number of admissible shifts is at or below `--draws`, EVERY shift is
    enumerated and the test is exact rather than sampled. C1 has 685 admissible
    days and pooled has 1,995, so both are exact at the pre-specified 2,000
    draws; the identity shift is excluded because it is the observed design.

**Stated as a limitation, not buried:** the circular-shift null is not the null
the 200-sim calibration certifies. It is the same estimator and the same test
statistic under a different randomization scheme, adopted because the calibrated
scheme is arithmetically impossible on a gapped stratum. Re-running
`18_null_calibration.py` against a gapped synthetic sample before the freeze
lifts would close that gap; until it is done, C1's and pooled's p-values carry
this caveat and `docs/PRE_ANALYSIS_NOTE.md` §8 says so in plain language.

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
Sequential on purpose. The pre-specified 2,000 draws over ~50 estimated cells is
hours of compute, and a process pool would make the result depend on scheduling
order unless seeded exactly as `18_null_calibration.py` seeds its workers. This
script runs once, in a run whose reproducibility matters more than its wall
clock, so determinism wins and every cell prints as it completes.

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

import argparse
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
from config import (
    BHEARD_BOUND_PRIMARY,
    BHEARD_BOUND_SENSITIVITY,
    CAI_D_BASKET,
    CONFIRMATION_WINDOWS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EPISODE_LIST_PRIMARY,
    EVENT_REFERENCE_DAY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    FREEZE_ACTIVE,
    H1_OUTCOMES,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    RANDOMIZATION_DRAWS,
    VALID_CDS,
)
from event_study import (
    MIN_FIRST_WEEK_DAYS,
    _joint_stat,
    _rel_day_coefs,
    build_stack,
    count_outcome,
    placebo_starts,
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
C1_WINDOWS = (("2015-07-01", "2016-12-31"), ("2021-01-01", "2021-05-31"))
C2_WINDOWS = (("2021-06-01", "2024-12-31"),)

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
ARGS = parser.parse_args()

SYNTHETIC = bool(ARGS.dry_run_synthetic)


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
    """Refuse to run unless the estimator's null calibration says CALIBRATED.

    This is a precondition, not a robustness column (Gate C §6.3). If the
    estimator over-rejects on data built to contain no effect then the number
    this script writes is not a weak p-value, it is not a p-value. The gate also
    re-checks `n_sims_completed` against the artifact's own
    `min_sims_required`, because the committed CALIBRATED verdict was once
    produced by a 12-sim smoke test and a gate that cannot fail is not a gate
    (findings S4, X3, R3).
    """
    f = OUTPUTS_TABLES / "null_calibration.csv"
    if not f.exists():
        raise SealBroken(
            f"{f} is absent. It is gitignored, so a fresh clone has none — run "
            "18_null_calibration.py --sims 200 --draws 200 before this script.")
    cal = pd.read_csv(f).set_index("metric")["value"]
    verdict = str(cal.get("VERDICT", "MISSING"))
    if verdict != "CALIBRATED":
        raise SealBroken(
            f"null calibration reads VERDICT={verdict!r}. An uncalibrated "
            "randomization p-value is not interpretable, so the confirmatory "
            "run does not happen (GATE_C_MEMO.md §6.3).")
    n_sims = int(float(cal.get("n_sims_completed", 0)))
    min_sims = int(float(cal.get("min_sims_required", 200)))
    if n_sims < min_sims:
        raise SealBroken(
            f"null calibration says CALIBRATED on {n_sims} sims against its own "
            f"minimum of {min_sims}. That combination is how the 12-sim artifact "
            "passed; treat it as a broken artifact and re-run 18.")
    rej = float(cal.get("empirical_rejection_rate", float("nan")))
    ks = float(cal.get("ks_p_uniform", float("nan")))
    print(f"[seal] calibration gate PASSED: {n_sims} sims, rejection rate "
          f"{rej:.4f}, KS uniformity p = {ks:.4f}")
    return {"n_sims": n_sims, "rejection_rate": rej, "ks_p": ks}


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


def episodes_for(ep, stratum_panel):
    """Episodes whose START lies inside the stratum.

    Assignment is on the start date and the window is then truncated to the
    stratum's own rows, which matters for exactly one real episode: the C1
    episode beginning 2021-05-24, whose +14 window runs into the B-HEARD era. Its
    days 0..+7 end on 2021-05-31, the last day of C1, so the first-week statistic
    is fully identified and only the tail is lost. Assigning by start rather than
    by full containment keeps that episode in the clean stratum where it belongs
    instead of discarding a tenth of C1's 2021 evidence.
    """
    lo, hi = stratum_panel["incident_date"].min(), stratum_panel["incident_date"].max()
    inside = _mask(ep["start"], [(lo, hi)])
    keep = ep[inside & _in_panel_dates(ep["start"], stratum_panel)]
    return keep.sort_values("start").reset_index(drop=True)


def _in_panel_dates(starts, stratum_panel):
    have = set(stratum_panel["incident_date"].unique())
    return starts.isin(have)


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------
def _formula(outcome, extra, fe="ep_cd + dow"):
    rhs = f"i(rel_day, ref={EVENT_REFERENCE_DAY})"
    for t in extra:
        rhs += f" + {t}"
    return f"{outcome} ~ {rhs} | {fe}"


def fit(stack, outcome, extra=("bheard_exposure",), counts=False,
        fe="ep_cd + dow", cluster=CLUSTER_VAR):
    """The confirmatory fit: 17's estimator plus the B-HEARD covariate.

    In C1 `bheard_exposure` is identically zero and pyfixest drops it as
    collinear, so the C1 estimate is numerically identical to the pre-registered
    estimator. `assert_bheard_inert` proves that on the data instead of claiming
    it here.

    Failures are returned as None rather than raised because a placebo draw can
    legitimately produce a degenerate design, but each distinct failure prints
    once: a systematic break (a wrong argument type, a missing column) otherwise
    looks exactly like bad luck, which is how the PPML arm stayed broken and
    merely appeared "not estimable" (X5/R8).
    """
    d = stack.dropna(subset=[outcome])
    if d.empty or d["episode"].nunique() < 2 or len(d) < 200:
        return None
    if EVENT_REFERENCE_DAY not in set(d["rel_day"]):
        return None
    extra = [t for t in extra if t in d.columns and d[t].notna().all()]
    vcov = {"CRV1": cluster} if cluster and cluster in d.columns else "hetero"
    fml = _formula(outcome, extra, fe=fe)
    try:
        with collected_warnings():
            if counts:
                d = d[(d["total_calls"] > 0) & d[outcome].notna()].copy()
                if d.empty:
                    return None
                d["log_total"] = np.log(d["total_calls"])
                return pf.fepois(fml, d, vcov=vcov, offset="log_total")
            return pf.feols(fml, d, vcov=vcov)
    except Exception as e:
        _note_failure(fml, counts, e)
        return None


_SEEN = set()


def _note_failure(fml, counts, exc):
    key = (fml, bool(counts), type(exc).__name__, str(exc)[:80])
    if key in _SEEN:
        return
    _SEEN.add(key)
    arm = "PPML counts" if counts else "OLS share"
    print(f"[fit] {arm} failed for `{fml}`: {type(exc).__name__}: {str(exc)[:160]}")


def first_week(stack, outcome, extra=("bheard_exposure",), counts=False,
               days=range(0, 8), min_days=MIN_FIRST_WEEK_DAYS):
    """Joint Wald chi-square on the day 0..7 coefficients, and their mean.

    Returns (statistic, mean coefficient, k coefficients) or (None, None, k).
    The statistic is the test; the mean is the reportable effect size and is
    explicitly not the test, because a dip-then-rebound averages to zero (S3/R7).
    """
    m = fit(stack, outcome, extra=extra, counts=counts)
    if m is None:
        return None, None, 0
    names = _rel_day_coefs(m)
    wanted = [names[k] for k in days if k in names]
    if len(wanted) < min_days:
        return None, None, len(wanted)
    return (_joint_stat(m, wanted),
            float(m.coef().loc[wanted].mean()),
            len(wanted))


def assert_bheard_inert(stack, outcome, label):
    """In a stratum with no B-HEARD exposure, the control must change nothing.

    Arithmetic, not assertion-by-comment. If the estimate moves when an
    identically-zero column is added, the precinct-to-community-district
    crosswalk is wrong — and that error would otherwise surface only in the
    confirmatory run, where it cannot be fixed. This is
    `X.bheard_inert_on_discovery` applied to the clean stratum.
    """
    if "bheard_exposure" not in stack.columns:
        return None
    mx = float(stack["bheard_exposure"].max())
    if mx > 0:
        return None
    with_c, _, _ = first_week(stack, outcome, extra=("bheard_exposure",))
    without, _, _ = first_week(stack, outcome, extra=())
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


# ---------------------------------------------------------------------------
# Randomization inference
# ---------------------------------------------------------------------------
def contiguous_blocks(dates):
    """Maximal runs of consecutive calendar days present in a stratum.

    The day difference is taken in DAY units (`datetime64[D]`) rather than by
    comparing the integer representation against a nanosecond constant. The first
    version of this function did the latter and was wrong: pandas stores this
    project's dates at MICROSECOND resolution, so consecutive days differ by
    86,400,000,000 and not 86,400,000,000,000, every comparison failed, and the
    function reported 701 one-day blocks for C1 instead of 2. The dry run caught
    it because the downstream consequence was visible — no day had a first week
    inside its own "block", so randomization inference reported that all 15
    episodes lacked coverage. A resolution-dependent constant is precisely the
    check that passes for the wrong reason on somebody else's machine.
    """
    d = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(dates)).unique()))
    if len(d) == 0:
        return []
    day = d.values.astype("datetime64[D]").astype("int64")
    cuts = np.where(np.diff(day) != 1)[0]
    blocks, start = [], 0
    for c in cuts:
        blocks.append((d[start], d[c]))
        start = c + 1
    blocks.append((d[start], d[-1]))
    return blocks


def admissible_starts(blocks, first_week_days=7):
    """Days whose reference day and whole first week lie inside the sample.

    That is exactly what `first_week_effect` requires before it will return a
    statistic, so a placebo drawn here is estimable on the same days as the
    observed design. It deliberately does NOT require the full 14-day
    pre-window: the real C1 episode of 2021-01-05 does not have one either, and
    a bar the observed design would fail is not a null, it is a different design.
    """
    out = []
    for lo, hi in blocks:
        a = lo + pd.Timedelta(days=1)                      # day -1 must exist
        b = hi - pd.Timedelta(days=first_week_days)        # day +7 must exist
        if b >= a:
            out.extend(pd.date_range(a, b, freq="D"))
    return pd.DatetimeIndex(sorted(out))


def calibrated_scheme_feasible(blocks, starts, pre, post):
    """Whether `event_study.placebo_starts` can produce any draw at all.

    Reproduces its own arithmetic rather than calling it and hoping: the anchor
    must leave room for the entire gap sequence inside one contiguous block. A
    negative result here is why C1 needs the fallback, and the number is printed
    so the reason is in the log rather than in a reviewer's head.
    """
    if len(blocks) != 1 or len(starts) < 2:
        return False, None
    lo, hi = blocks[0]
    gaps = np.diff([pd.Timestamp(s).toordinal() for s in sorted(starts)])
    span = int(gaps.sum())
    earliest = lo + pd.Timedelta(days=pre + 1)
    latest = hi - pd.Timedelta(days=post + 1)
    room = (latest - earliest).days - span
    return room >= 0, room


def circular_shift_starts(real_starts, adm, shift):
    """Shift the whole episode sequence by `shift` admissible-day positions.

    Spacing is preserved in observed-day units and the sequence wraps, so every
    shift yields a design with exactly as many episodes as the real one, each
    with the coverage the statistic needs. On a single contiguous block this is
    an ordinary circular time shift; on a gapped stratum it is the same operation
    performed in the sample's own day index, which is the only place the two
    blocks are adjacent.
    """
    pos = {d: i for i, d in enumerate(adm)}
    n = len(adm)
    idx = [pos[pd.Timestamp(s)] for s in real_starts]
    return [adm[(i + shift) % n] for i in idx]


def randomization(panel, real_starts, outcome, pre, post, draws, rng,
                  extra=("bheard_exposure",), counts=False, label=""):
    """Episode-level randomization inference, one scheme or the other.

    Returns a dict carrying the observed statistic, the p-value, and — the part
    that must never be dropped from the output — WHICH null produced it.
    """
    obs_stack = build_stack(panel, real_starts, pre, post)
    obs, mean_coef, k = first_week(obs_stack, outcome, extra=extra, counts=counts)
    res = {"first_week_chi2": obs, "first_week_mean_coef": mean_coef,
           "n_first_week_coefs": k, "n_obs": len(obs_stack),
           "p_randomization": np.nan, "n_draws": 0, "null_sd": np.nan,
           "ri_scheme": None, "ri_exact": 0, "n_admissible_starts": np.nan}
    if obs is None:
        res["status"] = "NOT_ESTIMABLE: the observed design yields no first-week statistic"
        return res

    blocks = contiguous_blocks(panel["incident_date"])
    feasible, room = calibrated_scheme_feasible(blocks, real_starts, pre, post)
    adm = admissible_starts(blocks)
    res["n_admissible_starts"] = len(adm)

    stats_ = []
    if feasible:
        res["ri_scheme"] = "calibrated_anchor_gap_permutation"
        lo, hi = panel["incident_date"].min(), panel["incident_date"].max()
        print(f"  [RI] {label}: calibrated scheme, anchor slack {room} day(s), "
              f"{draws} draws")
        for _ in range(draws):
            ps = placebo_starts(rng, real_starts, lo, hi, pre, post)
            if len(ps) != len(real_starts):
                continue
            b, _, _ = first_week(build_stack(panel, ps, pre, post), outcome,
                                 extra=extra, counts=counts)
            if b is not None:
                stats_.append(b)
    else:
        res["ri_scheme"] = "circular_shift_admissible_days"
        missing = [s for s in real_starts if pd.Timestamp(s) not in set(adm)]
        if len(adm) < 2 or missing:
            res["status"] = (f"RI_NOT_RUN: {len(missing)} real episode start(s) lack "
                             f"the coverage the statistic requires, so no shift "
                             f"preserves the observed design")
            return res
        shifts = np.arange(1, len(adm))          # shift 0 is the observed design
        if len(shifts) <= draws:
            res["ri_exact"] = 1
            chosen = shifts
            print(f"  [RI] {label}: circular shift over {len(adm)} admissible days "
                  f"({len(blocks)} block(s)) — EXACT, all {len(shifts)} shifts")
        else:
            chosen = rng.choice(shifts, size=draws, replace=False)
            print(f"  [RI] {label}: circular shift over {len(adm)} admissible days "
                  f"({len(blocks)} block(s)) — {draws} of {len(shifts)} shifts sampled")
        for s in chosen:
            ps = circular_shift_starts(real_starts, adm, int(s))
            b, _, _ = first_week(build_stack(panel, ps, pre, post), outcome,
                                 extra=extra, counts=counts)
            if b is not None:
                stats_.append(b)

    stats_ = np.array(stats_)
    if len(stats_) == 0:
        res["status"] = "RI_NOT_RUN: every placebo draw was discarded"
        return res
    res["p_randomization"] = float((stats_ >= obs).mean())
    res["n_draws"] = len(stats_)
    res["null_sd"] = float(stats_.std())
    res["status"] = "OK"
    return res


# ---------------------------------------------------------------------------
# Multiple testing
# ---------------------------------------------------------------------------
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
             extra, draws, rng, bound, episode_set, note=""):
    """One reported number, with everything needed to read it beside it."""
    col = count_outcome(outcome) if arm_counts else outcome
    label = f"{stratum}/{spec}/{col}/{'PPML' if arm_counts else 'OLS'}"
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
                        draws, rng, extra=extra, counts=arm_counts, label=label)
    rows.append(_row(stratum, col, arm_counts, spec, family, bound, episode_set,
                     len(ep), note=note,
                     n_districts=panel["communitydistrict"].nunique(), **res))
    chi = res.get("first_week_chi2")
    p = res.get("p_randomization")
    print(f"  {label:58s} chi2={chi if chi is None else round(chi, 2)!s:>10} "
          f"p_RI={p if p is None or np.isnan(p) else round(p, 4)!s:>8}  "
          f"[{res.get('status')}]")


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
    jul = july_2016_episode(ep_primary)
    print(f"[seal] episode lists: primary {EPISODE_LIST_PRIMARY} "
          f"({len(ep_primary)} extension episodes); broad "
          f"{EPISODE_LIST_BROAD} ({'absent' if ep_broad is None else len(ep_broad)})")
    print(f"[seal] July 2016 sensitivity targets {len(jul)} episode(s) containing "
          f"{DALLAS_ATTACK_DATE}"
          + (f": {jul['start'].dt.date.tolist()}" if len(jul) else ""))

    rows = []
    for stratum, spanel in strata.items():
        if spanel.empty:
            rows.append(_row(stratum, "-", False, "primary", "primary_H1",
                             BHEARD_BOUND_PRIMARY, "primary", 0,
                             status="NOT_RUN: stratum is empty"))
            continue
        print("\n" + "-" * 78)
        print(f"STRATUM {stratum}: {len(spanel):,} district-days, "
              f"{spanel['incident_date'].min().date()}.."
              f"{spanel['incident_date'].max().date()}, "
              f"{spanel['communitydistrict'].nunique()} districts")
        blocks = contiguous_blocks(spanel["incident_date"])
        shown = [(str(a.date()), str(b.date())) for a, b in blocks[:4]]
        print(f"  {len(blocks)} contiguous block(s): {shown}"
              + (" ..." if len(blocks) > 4 else ""))
        print(f"  {len(admissible_starts(blocks)):,} admissible placebo start(s) "
              "(day -1 and days 0..+7 inside the sample)")

        for bound in (BHEARD_BOUND_PRIMARY, BHEARD_BOUND_SENSITIVITY):
            sp = attach_bheard(spanel, bound=bound)
            mx = float(sp["bheard_exposure"].max())
            is_primary_bound = bound == BHEARD_BOUND_PRIMARY
            if not is_primary_bound and mx <= 0:
                print(f"  [{bound} bound] exposure is 0 throughout; the bound "
                      "sensitivity is identical to the primary and is not re-run")
                continue
            print(f"  [{bound} bound] max exposure {mx:.6g}")

            ep_here = episodes_for(ep_primary, sp)
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
                    run_cell(rows, sp, ep_here, stratum, outcome, counts, spec,
                             fam, ("bheard_exposure",), ARGS.draws, rng, bound,
                             "primary")
            if is_primary_bound:
                for outcome in PLACEBO_OUTCOMES:
                    for counts in (False, True):
                        run_cell(rows, sp, ep_here, stratum, outcome, counts,
                                 "placebo", "placebo", ("bheard_exposure",),
                                 ARGS.draws, rng, bound, "primary",
                                 note="falsification, not confirmation")

                # (a) drop the July 2016 episode
                drop = ep_here[~ep_here["start"].isin(jul["start"])]
                if len(drop) == len(ep_here):
                    print("  [sens] no July 2016 episode in this stratum; the "
                          "drop-July-2016 arm would be identical to the primary "
                          "and is not re-run")
                else:
                    for outcome in list(H1_OUTCOMES):
                        for counts in (False, True):
                            run_cell(rows, sp, drop, stratum, outcome, counts,
                                     "sens_drop_jul2016", "sensitivity",
                                     ("bheard_exposure",), ARGS.draws, rng, bound,
                                     "primary_minus_jul2016",
                                     note="Sterling + Castile + the Dallas attack")

                # (b) the broad basket
                if ep_broad is None:
                    for outcome in list(H1_OUTCOMES):
                        rows.append(_row(
                            stratum, outcome, False, "sens_broad_basket",
                            "sensitivity", bound, EPISODE_LIST_BROAD, 0,
                            status="NOT_RUN: broad-basket episode list absent",
                            note=("build it upstream with CAI_D_BASKET='broad' "
                                  "BEFORE the freeze lifts; rebuilding the "
                                  "treatment index after the lift is not blind")))
                else:
                    ep_b = episodes_for(ep_broad, sp)
                    for outcome in list(H1_OUTCOMES):
                        for counts in (False, True):
                            run_cell(rows, sp, ep_b, stratum, outcome, counts,
                                     "sens_broad_basket", "sensitivity",
                                     ("bheard_exposure",), ARGS.draws, rng, bound,
                                     EPISODE_LIST_BROAD,
                                     note="broad basket: +9 civilian-actor articles")

                # B-HEARD as identification
                if mx > 0:
                    for outcome in list(H1_OUTCOMES):
                        for counts in (False, True):
                            bheard_identification(rows, sp, ep_here, stratum,
                                                  outcome, counts, bound)

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
    res["calibration_sims"] = cal["n_sims"]
    res["freeze_active_at_run"] = int(FREEZE_ACTIVE)
    res["overwrite_reason"] = ARGS.overwrite_sealed_result or ""
    res.to_csv(out_path, index=False)

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
