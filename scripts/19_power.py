"""Simulation-based power for the stacked episode event study (Phase H, E1).

WHAT THIS ANSWERS
-----------------
Two questions, per stratum, and the second is the one that decides whether the
confirmatory run happens at all:

  1. What is the smallest first-week effect this design can detect at 80% power
     and alpha = 0.05 -- the MDE -- computed on the EFFECTIVE episode count
     rather than the nominal one?
  2. Roth's (2022) pre-trend diagnostic: how big a linear pre-trend would
     contaminate the first-week test by as much as an MDE-sized real effect, and
     what is the probability the pre-period test would catch a trend that size?

If the answer to (1) is that the MDE sits far above any effect this project has
ever measured, then the confirmatory run cannot deliver a confirmation, and
SAYING SO IS THE DELIVERABLE. REBUILD_PLAN.md:495 and EXECUTION_PLAN.md Phase H
both pre-commit to that reading: "If the power analysis says the confirmatory run
cannot deliver, that is the conclusion, and the paper becomes a measurement-and-
design contribution with a precisely bounded null. A real ending, not a failure
mode." A stratum verdict of UNDERPOWERED here is a result, not an error, and this
script exits 0 when it produces one.

WHY THIS FILE IS A REWRITE AND NOT A REVISION
---------------------------------------------
Two previous designs for 19_power.py were returned `needs_revision` by every
reviewer, with measured critiques (EXECUTION_PLAN.md E1). Each defect below is
named with what the old design did, what it should do, and where the fix lives in
this file, because "we fixed the review comments" is not checkable and this
project has been burned by exactly that.

  E1.1  THE ROTH DIAGNOSTIC WAS OPTIMISTIC BY 1.66x, MEASURED.
        The old design computed LEVER = mean(d - EVENT_REFERENCE_DAY) = 4.5 over
        d in 0..7 and declared `meaningful_trend = mde / LEVER`. That divides a
        JOINT WALD MDE by a scalar, and the two are not in the same units: the
        Wald statistic weights directions of the coefficient vector by their
        INFORMATION, and converting a trend to "an equivalent level shift of
        mean lever size" silently reroutes it through the level direction --
        which under this design's strongly equicorrelated Sigma is the LOWEST-
        information direction there is. That flatters the diagnostic: it makes
        the trend needed to matter look larger than it is.
        The correct statement is a noncentrality match. A linear pre-trend of
        slope b per day, anchored at the reference day, contaminates the day
        0..7 coefficients by b*u with u = [1..8], carrying noncentrality
        b^2 * u' Sigma^-1 u; an effect of size delta in profile p carries
        delta^2 * p' Sigma^-1 p. Setting them equal gives the reportable slope.
        Because the MDE is DEFINED by a fixed target power, lambda at the MDE is
        the same number for every profile, so the lambda-matched slope
            b* = sqrt(lambda_target / (u' Sigma^-1 u))
        is profile-free and is the headline. What IS profile-dependent is the
        RATIO b*/MDE, and it is reported for every profile precisely so nobody
        can quote the flattering one alone.
        Measured here on discovery-geometry draws while writing this file: the
        mean off-diagonal correlation of the day 0..7 coefficient vector runs
        0.44 to 0.54 depending on the draw, against the reviewers' 0.515 -- the
        stable fact is that the shared day -1 reference makes Sigma strongly
        equicorrelated, not any one of those numbers, and the file recomputes it
        per run and writes it to `sigma.mean_offdiag_corr`. On one such draw,
        lambda per unit 1.97e5 for the level direction against 1.34e7 for the
        trend direction, a factor of 68. b*/MDE(level) = 0.121, i.e. delta/8.25,
        against the old rule's delta/4.5 -- the old rule overstated the tolerable
        trend by 1.83x on this draw. The reviewers measured 1.66x on theirs and
        quoted delta/8.2; both reproduce the same defect, and neither number is
        hard-coded here. `_roth_diagnostic` recomputes all of it.
        Against the dip-then-rebound profile -- this project's OWN hypothesised
        mechanism (PAPER_MASTER 7.3, finding S3/R7) -- the ratio moves to 0.386
        on that draw. Reporting only the level profile would have been the same
        class of error as the LEVER shortcut.

  E1.2  THE RI BRACKET WOULD NOT CLOSE, AND THE RUN DIED UNDETERMINED.
        The old design bracketed the randomization-inference MDE at
        [0.8, 1.25] x the screen MDE and returned NaN when the true value fell
        outside, after spending its entire budget getting there. It always would
        have. Measured here on the real discovery geometry over 2000 accepted
        `placebo_starts` draws, at the seed this file uses: 32.3% of placebo
        episode starts (p10 24.1%, p90 41.4%) land within 7 days of a REAL
        episode start, because the 29 discovery episodes span 1240 days inside a
        window that leaves the whole shifted sequence only 190 free days to sit
        in. On C2 it is worse: 35.1% contaminated (p10 26.7%, p90 46.7%), and 53
        free days for a 1226-day sequence. The reviewers measured 30.8% on
        discovery; nothing here is hard-coded from that. Under a
        planted effect at the real dates, a third of every placebo design
        absorbs genuine signal, the RI null shifts up, and the RI MDE lands far
        outside any fixed multiple of the screen MDE.
        C1 fails earlier and for a different reason, and this file reports that
        instead of producing a number: 40.9% of its placebo starts land outside
        C1's own windows, because `placebo_starts` anchors a gap-permuted
        sequence inside one contiguous [lo, hi] and C1 is two windows either side
        of the entire discovery period. The project's PRIMARY p-value is not
        defined on C1 as the estimator currently draws placebos. That is a
        finding about the design, not a budget problem, and `ri_status` carries
        it into the CSV.
        So the RI bracket here is ADAPTIVE AND SEEDED BY A PILOT, both, as the
        reviewers asked: `_bracket_power` steps out geometrically from a cheap
        low-sim pilot until it actually brackets the target, refines inside the
        bracket, and -- if the cap is reached -- reports a one-sided BOUND with
        the cap named, never NaN. `ri_contaminated_share` is written to the CSV
        so the reason is in the artifact and not only in this docstring.

  E1.3  THE REFACTOR RECIPE BROKE 18.
        The old design said "delete lines 82-142 of 18_null_calibration.py" and
        claimed `starts` was untouched. `starts` is defined at 18:109-111, inside
        that range, and 18 would have died with NameError on the next line. This
        file DOES NOT TOUCH 18. It cannot import it either: 18 runs argparse and
        its entire 200-sim calibration at module scope, so importing it would
        execute the calibration. The generator is therefore COPIED, with the
        provenance recorded at `synthetic_panel`, and pinned by
        `_check_generator_fingerprint` -- one panel at a fixed seed with fixed
        parameters, hashed on the outcome column and compared to a recorded
        digest. That is a numeric property test: it fails if the arithmetic
        drifts, including drift that leaves the source looking right. It is
        deliberately NOT an `inspect.signature` or source-text guard, because
        "the code SAYS the right thing" is the exact defect class this project
        hunts (PAPER_MASTER 7.5). What it does NOT prove is stated at its
        docstring: it pins THIS file's generator, not equality with 18's.

  E1.4  A CROSS-ROUTE GATE THAT COULD NOT FIRE.
        The old gate compared an RI bracket of +/-25% against a 30% disagreement
        threshold. |log(1.25)| = 0.223 < 0.262 = |log(1.30)|: arithmetically
        unreachable. A gate that cannot fail is not a gate -- the same finding
        that rewrote 18's verdict (S4/X3/R3).
        The gate here compares two routes to the SAME MDE that can genuinely
        disagree:
          route MC -- simulate, plant, count rejections of the joint Wald test;
          route AN -- solve the noncentral chi-square for the delta that hits
                      target power, using Sigma taken from the ESTIMATOR'S OWN
                      clustered vcov.
        They part company exactly when the clustered vcov misstates sampling
        variability, which on this data is a live risk and not a hypothetical:
        p = 0.019 clustered against 0.26 permutation is why RI is the primary
        p-value at all (PAPER_MASTER 7.2). GATE_TOL_LOG = 0.15 is roughly twice
        the MC sampling noise at MIN_SIMS (see `_gate_headroom`, which prints the
        headroom so a reader can see the gate is not vacuous), so it fires on a
        real discrepancy and not on Monte Carlo scatter. `vcov_inflation` is
        reported beside it as the underlying quantity.

  E1.5  --day-shock=0.35 WAS AN UNESTIMATED ASSUMPTION EVERY MDE SCALED WITH.
        The old design took the citywide day-shock SD as a command-line default
        while VERDICT COMPLETE stayed reachable, so the headline number rested
        linearly on a number nobody had measured. THERE IS NO SUCH FLAG HERE.
        Every noise component is estimated from the discovery panel by the same
        peel-then-estimate procedure 18 adopted for finding S8 -- district, then
        day-of-week, then citywide day shock, then the AR(1) residual -- and if
        the panel is absent the run is UNDETERMINED and exits 2. It never
        substitutes an assumption for a measurement.
        S8's measured values, for orientation: rho = 0.0482, sigma = 0.0390,
        component scales district 0.335, dow 0.130, day_shock 0.284 (x sigma),
        implied total SD 0.0429 against the panel's 0.0428. This file re-measures
        them and writes what it measured; it does not trust those numbers.

  E1.6  NO MIN_SIMS FLOOR, SO `--scan-sims 20` PRINTED COMPLETE AND EXITED 0.
        MIN_SIMS = 200 here, applied to COMPLETED sims in both the null leg and
        the scan leg. Below it the verdict is UNDETERMINED and the exit code is
        2, exactly as 18 does -- a small run is a diagnostic, never a pass.

THE EFFECTIVE EPISODE COUNT
---------------------------
"MDE on the effective episode count, not the nominal" is the other standing
requirement, and the mechanism is real: 36 of the 74 rebuilt episodes have a
neighbour within +/-28 days, so event windows collide and `build_stack` assigns
each contested district-day to the NEARER episode -- the day survives, but the
farther episode loses it.

Where that bites is not where it is usually assumed, and this file measures it
rather than asserting it. Measured on the real geometry (`_geometry`):

  stratum     nominal  identifying  first-week depth  pre-period depth  rows kept
  discovery      29         29         29.00 / 29       26.38 / 29        92.2%
  C1             15         15         15.00 / 15       13.15 / 15        90.1%
  C2             30         30         29.75 / 30       25.62 / 30        87.7%

Nearest-assignment protects the FIRST WEEK almost completely -- day 0..7 of a
later episode is nearer to that episode than to an earlier one's day +20 -- so
first-week depth is essentially nominal. The loss lands in the PRE-PERIOD, 9-15%
of it, which is where the Roth pre-test draws its power. So the naive worry is
misdirected and the real cost is to the pre-trend diagnostic, not to the main
test. That is reported, not smoothed over.

The count that actually governs power is neither of those. It is INFORMATION, so
`n_effective` here is defined by information and measured:

    n_effective = n_nominal * lambda_real / lambda_spaced

where lambda is the noncentrality per unit effect and `spaced` is the same number
of episodes in the same calendar span placed far enough apart that no two windows
touch. Both are measured with the real estimator; the ratio absorbs window
truncation AND what happens when one episode's planted effect lands on a day the
stack has labelled with a different episode's relative day. Every MDE in the
output CSV is reported beside the n_effective it was achieved at.

AND THE FIRST WEEK LOSES ALMOST NOTHING, for a reason that is exact rather than
empirical. `build_stack` gives a contested district-day to the NEARER episode.
Day d of episode A sits on date A+d, whose distance to a later episode B is
|d - (B-A)|, and that beats d exactly when 0 < B-A < 2d. So a first-week day is
lost only to a LATER neighbour starting within 14 days -- an earlier one is always
further away and can never take one -- and a 10-day gap costs days 6 and 7 and
nothing else. `_geometry` computes the loss from that rule and the run ABORTS if
build_stack disagrees with it, because if the assignment rule is not what this
file assumes then nothing here about effective N is supported.

Measured, and matching the rule exactly on all three strata:

  stratum  min gap  pairs < 14d  first-week days lost  max |g - profile|
  ---------------------------------------------------------------------
  discovery   15d        0            0 of 232              0.000000
  C1          16d        0            0 of 120              0.000000
  C2          10d        1            2 of 240              0.002866

where g is the day 0..7 coefficient vector the estimator returns for a unit
planted effect: on discovery and C1 it is the planted profile to machine
precision, and on C2 it is off by 0.29% of a unit effect. Written per run to
`geometry.first_week_days_lost_predicted` and
`first_week_attenuation_max_abs_dev`, so a rebuilt episode list that crowds two
starts closer shows up as a number rather than as a surprise.

So the standing worry -- neighbouring episodes truncate windows and reduce
informative N -- is right about the mechanism and wrong about where it lands. On
this episode list it costs 9-15% of the PRE-PERIOD and 0.8% of one stratum's
first week. The Roth pre-test is the diagnostic that pays for it, and it is
computed on the truncated pre-period Sigma for exactly that reason.

`n_effective` is still reported, and still worth reading, but it must be read for
what it is: a ratio of TWO ESTIMATED covariance matrices, the real geometry's and
the spaced reference's. It is not deterministic like the two measurements above,
and at small `--null-sims`/`--ref-sims` it is dominated by estimation noise -- a
2-sim diagnostic run put it at 44 of 29, which is a statement about two noisy
matrices and not about the design. Quote it only from a run at MIN_SIMS or above.

One assumption is buried in all of this and is therefore made explicit and given
a conservative counterpart: where first weeks DO overlap -- they do not on this
list, but a rebuilt list could change that -- `plant` must decide whether two
episodes covering a day produce twice the response. Whether two simultaneous
attention shocks double the behavioural response is not known, so the CSV carries
both conventions: `n_effective` / `mde_*` under additive overlap, and
`n_effective_saturating` / `mde_analytic_saturating_overlap` under the
conservative one where the day takes the single largest contribution instead of
the sum. On the current list the two are identical, which is itself the check
that no first week overlaps.

THE FREEZE
----------
FREEZE_ACTIVE is True and this script must not weaken it. Exactly one real
outcome read happens, in `_variance_components`, through
`freeze_guard.select_sample`, and its return is re-asserted to end at
DISCOVERY_END. The confirmation strata get their power from the DISCOVERY
variance structure plus the confirmation episode GEOMETRY -- episode dates are
treatment-side and were never frozen -- so no confirmation-window outcome value
is read, or needed, to compute an MDE for C1 or C2. That is not a workaround; it
is the only correct way to do this before the freeze lifts, and it is why the
answer is available now, when it can still change the plan.

STRATA
------
Derived from config, never retyped: C1 is the confirmation windows before
BHEARD_LAUNCH, C2 from BHEARD_LAUNCH on. PAPER_MASTER 6 writes Confirmation A as
2015-07-01..2016-12-31 while config.CONFIRMATION_WINDOWS opens it at 2015-01-01.
`_check_strata_agree_with_paper` asserts the disagreement is immaterial to the
episode geometry -- no episode starts in the disputed gap, the earliest is
2015-07-23 -- and FAILS if one ever does, rather than letting two definitions of
a stratum coexist unremarked.

Usage:
    python 19_power.py                          # full run, both profiles, RI on
    python 19_power.py --scan-sims 6 --no-ri    # smoke: prints UNDETERMINED, exit 2
"""

import argparse
import hashlib
import os

# BLAS THREADS OFF, BEFORE numpy IS IMPORTED. Two reasons, and the first is a
# hang this file actually produced rather than a precaution.
#
#  1. DEADLOCK. The workers are forked (see `_pmap`), and this script fits models
#     in the PARENT before the first fork -- the plant-equivalence check and the
#     unit-response measurement. A fork of a process that has already started
#     OpenMP/BLAS worker threads gives the child an inherited, already-held
#     mutex, and the child then blocks forever on it. Observed exactly that: the
#     parent at futex_do_wait, the child at futex_do_wait with 0 seconds of CPU
#     consumed, no error, no timeout -- an error path indistinguishable from a
#     slow run, which is the failure shape this project keeps finding. Setting
#     these before numpy loads means the thread pools are never created, so there
#     is nothing to inherit.
#  2. OVERSUBSCRIPTION. With JOBS processes each running an N-thread BLAS on a
#     4-core box, the run is slower than the serial version and starves whatever
#     else is on the machine. One thread per worker process is the right setting
#     for a process-parallel job regardless of the deadlock.
#
# setdefault, so an operator who deliberately exports a different value keeps it.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

from config import (
    BHEARD_LAUNCH,
    CONFIRMATION_WINDOWS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    DISCOVERY_END,
    DISCOVERY_START,
    EPISODE_LIST_PRIMARY,
    EVENT_REFERENCE_DAY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    FREEZE_ACTIVE,
    H1_OUTCOMES,
    OUTPUTS_TABLES,
    VALID_CDS,
)
from event_study import (
    _joint_stat,
    _rel_day_coefs,
    build_stack,
    fit_event_study,
    placebo_starts,
    randomization_p,
)
from freeze_guard import freeze_banner, select_sample

# ---------------------------------------------------------------------------
# Constants. None of these is a command-line flag, and that is deliberate: a
# tunable gate threshold or a tunable minimum sim count is a gate that the next
# person under time pressure turns off (findings S4, X3, R3).
# ---------------------------------------------------------------------------
MIN_SIMS = 200              # completed sims below which no verdict is issued
TARGET_POWER = 0.80
ALPHA = 0.05
FIRST_WEEK = tuple(range(0, 8))
GATE_TOL_LOG = 0.15         # |log(mde_mc / mde_analytic)| the two routes may differ by

# Effect profiles over days 0..7, each at unit root-mean-square so that `delta`
# reads in the same units across profiles: for `level` it is the size of the
# level shift, for `dip_rebound` the depth of the dip and the height of the
# rebound. dip_rebound is the square wave PAPER_MASTER 7.3 uses to demonstrate
# S3/R7 -- the mechanism this project hypothesises, and the one whose mean is
# approximately zero.
PROFILES = {
    "level": np.ones(8),
    "dip_rebound": np.array([-1.0] * 4 + [1.0] * 4),
}

# Reference effect sizes the verdict is read against. There are only two numbers
# this project has ever named, they are NOT the same estimand, and neither is an
# elicited minimum effect of interest -- so both are reported and the MDE itself
# stays the primary number.
#   planted:   PAPER_MASTER 7.1, the -0.010 first-week effect the estimator was
#              verified to recover (as -0.01043). A verification convenience.
#   discovery: GATE2_PRELIMINARY_RESULTS 2, the largest discovery-period EDP
#              coefficient, -0.00108 in the whitest quartile at p = 0.02. That is
#              a continuous-awareness heterogeneity coefficient, NOT a stacked
#              first-week level shift, so comparing an MDE to it is indicative of
#              magnitude only. Said here so nobody reads the ratio as exact.
REFERENCE_EFFECTS = {"planted_verification": 0.010, "discovery_gate2": 0.00108}
REFERENCE_PRIMARY = "discovery_gate2"

# Randomization-inference bracket search. RI_MAX_STEPOUTS x log(RI_STEP) is the
# reach: 1.6^6 = 16.8x the screen MDE. Beyond it the answer is reported as a
# bound, because spending the rest of the budget to bracket a number that is
# already an order of magnitude past anything this project can detect buys
# nothing (E1.2).
RI_STEP = 1.6
RI_MAX_STEPOUTS = 6
RI_MAX_STEPINS = 3
RI_REFINE_ROUNDS = 4
RI_MIN_ACCEPT = 0.02        # placebo draws landing wholly inside the stratum

# Fingerprint of `synthetic_panel` under FINGERPRINT_PARAMS. See
# `_check_generator_fingerprint` for what this does and does not prove.
FINGERPRINT_PARAMS = dict(rho=0.05, sigma=0.04, mu=0.10,
                          cd_scale=0.33, dow_scale=0.13, day_scale=0.28)
GENERATOR_FINGERPRINT = "9c05c9183349afbb1b487e10b8f3998633a6f210df4e251637518fec656554cc"

parser = argparse.ArgumentParser()
parser.add_argument("--outcome", default=H1_OUTCOMES[0],
                    help=f"H1 outcome to power; one of {H1_OUTCOMES}")
parser.add_argument("--null-sims", type=int, default=MIN_SIMS,
                    help="null panels per stratum; sets Sigma and the MC size")
parser.add_argument("--scan-sims", type=int, default=MIN_SIMS,
                    help="sims per delta in the Monte Carlo power scan")
parser.add_argument("--ref-sims", type=int, default=40,
                    help="null panels for the SPACED reference design (Sigma only)")
parser.add_argument("--ri-sims", type=int, default=40)
parser.add_argument("--ri-draws", type=int, default=60)
parser.add_argument("--ri-pilot-sims", type=int, default=10)
parser.add_argument("--ri-pilot-draws", type=int, default=30)
parser.add_argument("--no-ri", action="store_true",
                    help="skip the randomization-inference leg; verdict records it")
parser.add_argument("--strata", default="discovery,C1,C2")
parser.add_argument("--jobs", type=int, default=0, help="0 = cpu_count()-1")
args = parser.parse_args()

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
JOBS = args.jobs or max(1, (os.cpu_count() or 2) - 1)
freeze_banner("19_power")


# ===========================================================================
# The synthetic panel generator -- COPIED from 18_null_calibration.py
# ===========================================================================
def synthetic_panel(rng, dates, cds, rho, sigma, mu,
                    cd_effect, dow_effect, day_scale):
    """A panel with the real serial structure and NO episode effect.

    PROVENANCE. This is 18_null_calibration.py's `synthetic_panel`, copied, not
    imported. 18 cannot be imported: it parses arguments and runs its entire
    calibration at module scope, so `import` would execute a 200-sim job. It is
    also not edited, and nothing here reads its source (E1.3).

    The draw ORDER is preserved exactly -- innovations, then the initial state,
    then the AR(1) recursion, then the citywide day shock -- because the order is
    what makes a seed reproducible, and `_check_generator_fingerprint` pins it.

    Differences from 18, all of them parameterisation rather than behaviour:
      - `dates`, `cds`, and the noise parameters are arguments instead of module
        globals, because this file generates panels for three different calendars
        and 18 generates one;
      - `cd_effect` and `dow_effect` are passed in rather than drawn here. 18
        draws them once at module scope so they are constant across its sims;
        passing them keeps that property while letting the fingerprint be a
        function of its inputs alone;
      - `dates` may be NON-CONTIGUOUS. Stratum C1 is two disjoint windows, and a
        date index with a hole is the honest representation of a sample that has
        one. The AR(1) is recursed over the index in order, which means the
        district series is treated as continuing across the gap. That overstates
        persistence across one boundary out of 731 days and is recorded here
        rather than hidden; at rho = 0.048 the effect is not measurable.

    The citywide day shock is in here because treatment is citywide (finding S6).
    Without it every district is an independent draw, the effective sample is
    ~59x the truth, and a power analysis would inherit an MDE that is far too
    small -- the mirror image of the pessimism S8 found in the old calibration.
    """
    T, N = len(dates), len(cds)
    dow = np.asarray([d.dayofweek for d in dates])
    innov = rng.normal(0, sigma * np.sqrt(1 - rho ** 2), (N, T))
    y = np.empty((N, T))
    y[:, 0] = rng.normal(0, sigma, N)
    for t in range(1, T):
        y[:, t] = rho * y[:, t - 1] + innov[:, t]
    day_shock = rng.normal(0, sigma * day_scale, T)
    y = y + cd_effect[:, None] + dow_effect[dow][None, :] + day_shock[None, :] + mu
    return pd.DataFrame({
        "communitydistrict": np.repeat(cds, T),
        "incident_date": np.tile(np.asarray(dates), N),
        args.outcome: y.reshape(-1),
        "total_calls": 50,
        "dow": np.tile(dow, N),
    })


def _check_generator_fingerprint():
    """Pin the copied generator's arithmetic to a recorded digest.

    WHAT IT PROVES: that `synthetic_panel` still produces bit-identical output
    for a fixed seed and fixed parameters. It catches a reordered draw, a changed
    recursion, a dropped component, a transposed broadcast -- including changes
    that leave the source reading correctly, which a source grep cannot (the
    class PAPER_MASTER 7.5 calls the most transferable lesson in the project).

    WHAT IT DOES NOT PROVE: that this copy still matches 18's. Nothing here can
    prove that, because 18 is not importable without running its calibration, and
    a source-text comparison would be a check on what the code SAYS. If 18's
    generator is deliberately changed, this fingerprint will keep passing and the
    two files will have diverged -- so the divergence risk is named in the S8
    comment block of `_variance_components` where a reader will meet it.

    The parameters are FIXED CONSTANTS, not the panel-calibrated ones, so a
    rebuild of the EMS panel does not false-fail this check.
    """
    p = FINGERPRINT_PARAMS
    rng = np.random.default_rng(19_20260912)
    dates = pd.date_range("2017-01-01", "2017-03-31", freq="D")
    cds = list(VALID_CDS)[:8]
    cd_effect = np.linspace(-1, 1, len(cds)) * p["sigma"] * p["cd_scale"]
    dow_effect = np.linspace(-1, 1, 7) * p["sigma"] * p["dow_scale"]
    df = synthetic_panel(rng, dates, cds, p["rho"], p["sigma"], p["mu"],
                         cd_effect, dow_effect, p["day_scale"])
    digest = hashlib.sha256(
        np.ascontiguousarray(df[args.outcome].to_numpy(dtype=np.float64)).tobytes()
    ).hexdigest()
    if GENERATOR_FINGERPRINT == "PLACEHOLDER":
        raise SystemExit(f"generator fingerprint not recorded; measured {digest}")
    if digest != GENERATOR_FINGERPRINT:
        raise SystemExit(
            "GENERATOR DRIFT. synthetic_panel no longer reproduces its recorded "
            f"fingerprint:\n  recorded {GENERATOR_FINGERPRINT}\n  measured {digest}\n"
            "Every MDE in this file is a function of this generator, so a changed "
            "generator invalidates the artifact. If the change is intended, record "
            "the new digest in the same commit as the change and say why.")
    return digest


# ===========================================================================
# Noise structure -- MEASURED from the discovery panel, never assumed (E1.5)
# ===========================================================================
def _variance_components(outcome):
    """Peel district, day-of-week and citywide day shock, then fit the AR(1).

    This is finding S8's procedure. Before S8, 18 estimated rho as the pooled
    lag-1 correlation of the LEVEL series and sigma as its total SD, so both
    already contained the district effect, the day-of-week effect and the day
    shock -- and the generator then added all three again. rho came out 0.1851
    against a true residual 0.0482, nearly four times too persistent, and total
    synthetic variance ran 1.40x the panel's. S8 was found BY REVIEWING A POWER
    DESIGN, because a power analysis built on that generator inherits a
    pessimistic MDE; this is that power design, so it estimates the same way.

    Each component is removed before the next is estimated, so the pieces sum to
    the panel's variance instead of stacking on it. The implied total SD is
    checked against the panel's own SD and reported, which is the only thing that
    makes "calibrated" mean anything.

    DIVERGENCE RISK: 18 owns the same procedure and this file owns a copy of it.
    They are not wired together and cannot be: 18 is a script, not a module
    (E1.3). If S8's procedure changes in one file and not the other, the null
    calibration and the power analysis will describe different designs. The
    implied-vs-actual SD line printed by both is the cheapest way to notice.

    THE ONLY REAL OUTCOME READ IN THIS FILE, and it goes through select_sample.
    """
    path = DATA_PROCESSED / "panel_cd_day.parquet"
    if not path.exists():
        return None
    real = pd.read_parquet(path)
    real["incident_date"] = pd.to_datetime(real["incident_date"])
    real = select_sample(real, where="19_power")

    # select_sample is the guard, but assert its postcondition anyway: this file
    # computes numbers FOR the confirmation strata and a reader is entitled to
    # see, at the point of the read, that no confirmation row reached it.
    if real["incident_date"].max() > pd.Timestamp(DISCOVERY_END):
        raise RuntimeError(
            "19_power read outcome rows past DISCOVERY_END. The confirmation "
            "strata are powered from discovery variance plus confirmation "
            "GEOMETRY; reading their outcomes is the thing this design exists "
            "to avoid.")
    if outcome not in real.columns or not real[outcome].notna().any():
        return None

    s = real.dropna(subset=[outcome]).sort_values(["communitydistrict", "incident_date"])
    mu = float(s[outcome].mean())
    total_sd = float(s[outcome].std())

    r = s[outcome] - s.groupby("communitydistrict")[outcome].transform("mean")
    cd_sd = float(s.groupby("communitydistrict")[outcome].mean().std())
    dow_means = r.groupby(s["incident_date"].dt.dayofweek).transform("mean")
    r = r - dow_means
    dow_sd = float(dow_means.groupby(s["incident_date"].dt.dayofweek).first().std())
    day_means = r.groupby(s["incident_date"]).transform("mean")
    r = r - day_means
    day_sd = float(day_means.groupby(s["incident_date"]).first().std())

    sigma = float(r.std())
    lag = r.groupby(s["communitydistrict"]).shift(1)
    ok = lag.notna() & r.notna()
    rho = float(np.corrcoef(r[ok], lag[ok])[0, 1])
    scales = (cd_sd / sigma, dow_sd / sigma, day_sd / sigma)
    implied = float(np.sqrt(sigma ** 2 * (1 + sum(x ** 2 for x in scales))))
    return dict(mu=mu, sigma=sigma, rho=rho, cd_scale=scales[0],
                dow_scale=scales[1], day_scale=scales[2],
                implied_total_sd=implied, panel_total_sd=total_sd,
                n_rows=int(len(s)))


# ===========================================================================
# Strata -- derived from config, and checked against PAPER_MASTER 6
# ===========================================================================
def _stratum_windows(name):
    """The (start, end) intervals a stratum covers. DERIVED, never hand-set."""
    if name == "discovery":
        return [(pd.Timestamp(DISCOVERY_START), pd.Timestamp(DISCOVERY_END))]
    launch = pd.Timestamp(BHEARD_LAUNCH)
    out = []
    for a, b in CONFIRMATION_WINDOWS:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        if name == "C1":
            hi = min(b, launch - pd.Timedelta(days=1))
            if a <= hi:
                out.append((a, hi))
        elif name == "C2":
            lo = max(a, launch)
            if lo <= b:
                out.append((lo, b))
        else:
            raise ValueError(f"unknown stratum {name}")
    return out


def _check_strata_agree_with_paper(episodes):
    """PAPER_MASTER 6 opens Confirmation A at 2015-07-01; config opens it at
    2015-01-01. Two definitions of a stratum is a second source of truth, so the
    disagreement is either immaterial or it is a defect, and this decides which.

    It is immaterial iff no episode starts in the disputed gap, because the
    stratum's POWER is a function of its episode geometry and its calendar
    length, and six extra months of control days with no episode in them change
    the geometry not at all. The earliest episode on the rebuilt list starts
    2015-07-23. This FAILS if a rebuild ever puts one earlier, instead of letting
    the two definitions drift apart unremarked.
    """
    gap_lo, gap_hi = pd.Timestamp("2015-01-01"), pd.Timestamp("2015-06-30")
    n = int(episodes["start"].between(gap_lo, gap_hi).sum())
    if n:
        raise RuntimeError(
            f"{n} episode(s) start between {gap_lo.date()} and {gap_hi.date()}, "
            "where config.CONFIRMATION_WINDOWS and PAPER_MASTER 6 disagree about "
            "whether stratum C1 has begun. The two definitions now give different "
            "episode sets and one of them has to be corrected before a power "
            "number for C1 means anything.")
    return int(episodes["start"].min() > gap_hi)


def _stratum_starts(episodes, name):
    wins = _stratum_windows(name)
    m = pd.Series(False, index=episodes.index)
    for a, b in wins:
        m |= episodes["start"].between(a, b)
    return sorted(episodes.loc[m, "start"].tolist())


def _stratum_dates(name):
    wins = _stratum_windows(name)
    return pd.DatetimeIndex(np.concatenate(
        [pd.date_range(a, b, freq="D").to_numpy() for a, b in wins]))


def _spaced_starts(name, n):
    """The same n episodes, placed so no two event windows touch.

    The reference design for `n_effective`. Episodes are allocated to the
    stratum's windows in proportion to window length and spread evenly inside
    each, keeping the pre/post margins `placebo_starts` uses. Returns None if the
    stratum cannot hold n isolated windows, in which case n_effective is reported
    as not measurable rather than as 1.0 by default.
    """
    wins = _stratum_windows(name)
    span = int(EVENT_WINDOW_PRE + EVENT_WINDOW_POST + 1)
    lens = [max(0, (b - a).days - span) for a, b in wins]
    total = sum(lens)
    if total <= 0:
        return None
    alloc = [max(1, int(round(n * L / total))) for L in lens]
    while sum(alloc) > n:
        alloc[int(np.argmax(alloc))] -= 1
    while sum(alloc) < n:
        alloc[int(np.argmax(lens))] += 1
    out = []
    for (a, b), k in zip(wins, alloc):
        if k <= 0:
            continue
        lo = a + pd.Timedelta(days=EVENT_WINDOW_PRE + 1)
        hi = b - pd.Timedelta(days=EVENT_WINDOW_POST + 1)
        room = (hi - lo).days
        if room < 0 or (k > 1 and room / (k - 1) < span):
            return None                    # cannot isolate them; say so
        step = room / max(k - 1, 1)
        out += [lo + pd.Timedelta(days=int(round(i * step))) for i in range(k)]
    return sorted(out) if len(out) == n else None


# ===========================================================================
# Planting, and the equivalence it rests on
# ===========================================================================
def plant(frame, starts, profile, delta, outcome, overlap="add"):
    """Add `delta * profile[d]` to every district on date start+d, d in 0..7.

    Citywide, because treatment is citywide.

    WHAT HAPPENS WHERE TWO EPISODES OVERLAP IS AN ASSUMPTION, NOT A FACT, and it
    changes the answer, so both conventions are available and both are reported:

      "add"      two episodes covering the same day produce twice the response.
                 This is the default because it is what an additive linear model
                 means, and it is the convention the RI leg and the MC scan use
                 throughout.
      "saturate" the day takes the single largest contribution instead. Nobody
                 knows whether two simultaneous attention shocks double the
                 behavioural response, and if they do not, "add" credits the
                 design with information it does not have.

    This matters more than it looks. Under "add", crowding does not cost the
    first-week test information -- it ADDS it, and the measured effective episode
    count comes out ABOVE the nominal one. Reporting that number alone, with no
    conservative counterpart, would be assuming the favourable answer to an open
    question, which is the shape of defect this project keeps finding. So
    `n_effective` and the analytic MDE are both reported under each convention
    and the saturating one is the conservative bound.
    """
    contrib = {}
    for s in starts:
        for d, w in enumerate(profile):
            key = pd.Timestamp(s) + pd.Timedelta(days=d)
            contrib.setdefault(key, []).append(float(delta) * float(w))
    if overlap == "add":
        off = {k: float(np.sum(v)) for k, v in contrib.items()}
    elif overlap == "saturate":
        off = {k: float(v[int(np.argmax(np.abs(v)))]) for k, v in contrib.items()}
    else:
        raise ValueError(f"unknown overlap convention {overlap!r}")
    out = frame.copy()
    out[outcome] = out[outcome] + out["incident_date"].map(off).fillna(0.0).to_numpy()
    return out


def _check_plant_equivalence(panel, starts, outcome):
    """Planting on the STACK must equal planting on the PANEL and rebuilding.

    The scan plants on the stack, because `build_stack` depends only on dates and
    districts and rebuilding it once per delta would cost ~12% of the run for
    nothing. That is only true if the two routes agree, so this measures it on
    real coefficients rather than arguing it from the source. Four fits.
    """
    prof = PROFILES["dip_rebound"]
    a = fit_event_study(build_stack(plant(panel, starts, prof, 0.01, outcome),
                                    starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST), outcome)
    st = build_stack(panel, starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    b = fit_event_study(plant(st, starts, prof, 0.01, outcome), outcome)
    if a is None or b is None:
        raise RuntimeError("plant-equivalence check could not estimate either model")
    ca, cb = a.coef(), b.coef()
    worst = float(np.max(np.abs(ca.values - cb.reindex(ca.index).values)))
    if worst > 1e-10:
        raise RuntimeError(
            f"planting on the stack and planting on the panel disagree by {worst:.3e}. "
            "The scan's economy is invalid; plant on the panel and rebuild.")
    return worst


# ===========================================================================
# Per-sim work. Module-level so ProcessPoolExecutor can reach it under fork.
# ===========================================================================
def _coef_block(m, days):
    """(coef vector, vcov block, column names) for the requested relative days.

    None when any requested day is missing, which is a real possibility: a
    collinear event-time dummy gets dropped when a window is truncated, and a
    statistic built from a different set of days than the one it is compared
    against is not the same statistic (the reason MIN_FIRST_WEEK_DAYS exists in
    event_study).
    """
    names = _rel_day_coefs(m)
    want = [d for d in days if d in names]
    if len(want) != len(days):
        return None
    cols = [names[d] for d in want]
    allnames = [str(x) for x in m._coefnames]
    idx = [allnames.index(c) for c in cols]
    V = np.asarray(m._vcov, dtype=float)
    return np.asarray(m.coef().loc[cols].values, dtype=float), V[np.ix_(idx, idx)], cols


def _fit_coefs(stack, outcome, days):
    """Fit, then take one block. Use `fit_event_study` + `_coef_block` directly
    when more than one block is wanted: fitting twice for two blocks of the SAME
    model doubled the cost of the null leg for nothing."""
    m = fit_event_study(stack, outcome)
    if m is None:
        return None
    blk = _coef_block(m, days)
    return None if blk is None else (blk[0], blk[1], m, blk[2])


def _null_sim(job):
    """One null panel: first-week and pre-period coefficient vectors and vcovs."""
    c, seed = job
    rng = np.random.default_rng(seed)
    panel = synthetic_panel(rng, c["dates"], c["cds"], c["rho"], c["sigma"], c["mu"],
                            c["cd_effect"], c["dow_effect"], c["day_scale"])
    stack = build_stack(panel, c["starts"], EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    if stack.empty:
        return None
    m = fit_event_study(stack, c["outcome"])
    if m is None:
        return None
    fw = _coef_block(m, list(FIRST_WEEK))
    if fw is None:
        return None
    pre = _coef_block(m, [d for d in range(-EVENT_WINDOW_PRE, EVENT_REFERENCE_DAY)])
    return dict(fw_b=fw[0], fw_V=fw[1],
                pre_b=None if pre is None else pre[0],
                pre_V=None if pre is None else pre[1])


def _scan_sim(job):
    """One panel, one null fit, and one fit per (profile, delta) on top of it.

    Returns the null joint statistic and a rejection flag per cell. The panel and
    the stack are built ONCE and the effect is planted on the stack, which
    `_check_plant_equivalence` has already shown to be exact.
    """
    c, seed, cells = job
    rng = np.random.default_rng(seed)
    panel = synthetic_panel(rng, c["dates"], c["cds"], c["rho"], c["sigma"], c["mu"],
                            c["cd_effect"], c["dow_effect"], c["day_scale"])
    stack = build_stack(panel, c["starts"], EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    if stack.empty:
        return None
    out = {}
    for pname, delta in cells:
        st = plant(stack, c["starts"], PROFILES[pname], delta, c["outcome"])
        got = _fit_coefs(st, c["outcome"], list(FIRST_WEEK))
        if got is None:
            out[(pname, delta)] = None
            continue
        _, _, m, cols = got
        out[(pname, delta)] = float(_joint_stat(m, cols))
    return out


def _ri_sim(job):
    """One randomization-inference replicate at a planted effect size.

    Calls `event_study.randomization_p` -- the estimator 17 runs -- rather than
    reimplementing it, so the RI MDE is the MDE of the committed inference and
    not of a lookalike. Note that that function computes p as k/n; CP2 carries an
    open item to move it to the (1+k)/(1+n) form, which would raise every RI
    p-value by about 1/n and so shift the RI MDE slightly upward. Recorded here
    because the number in the CSV is a property of today's code.
    """
    c, seed, pname, delta, draws = job
    rng = np.random.default_rng(seed)
    panel = synthetic_panel(rng, c["dates"], c["cds"], c["rho"], c["sigma"], c["mu"],
                            c["cd_effect"], c["dow_effect"], c["day_scale"])
    panel = plant(panel, c["starts"], PROFILES[pname], delta, c["outcome"])
    obs, p, null = randomization_p(panel, c["starts"], c["outcome"],
                                   EVENT_WINDOW_PRE, EVENT_WINDOW_POST, draws, rng)
    if obs is None or not np.isfinite(p) or len(null) == 0:
        return None
    return float(p)


EXECUTOR = None


def _start_workers():
    """Fork the worker pool BEFORE this process fits anything. Not optional.

    THIS IS A BUG FIX, NOT A STYLE CHOICE, and it is written down because the
    failure it prevents is silent. `fit_event_study` leaves four native worker
    threads behind in whatever process calls it (measured: 4 OS threads before
    the first fit, 8 after). A pool forked AFTER that inherits a thread's
    already-held lock, and the child then blocks in futex forever: observed here
    as a run that printed "null leg: 2 sims on 1 workers", consumed zero CPU in
    the child, produced no error and never returned. A hang that looks like a
    slow run is the error-path-indistinguishable-from-success class this project
    keeps finding, so it gets a named fix rather than a retry.

    `ProcessPoolExecutor` spawns workers lazily on first submit, so creating it
    early is not enough -- the fork would still happen at the first real job,
    after the parent had fitted. The warm-up map forces every worker to exist
    while the parent is still clean. Measured: with the pool warmed first the
    same child job returns in 1.9s instead of never.

    The consequence for everything else in this file is that workers CANNOT
    inherit per-stratum state through a module global, because they are forked
    before any stratum exists. Each job therefore carries its own context dict.
    """
    global EXECUTOR
    EXECUTOR = ProcessPoolExecutor(max_workers=JOBS)
    want = list(range(max(JOBS * 4, 4)))
    got = list(EXECUTOR.map(int, [str(i) for i in want]))
    if got != want:
        # Raised, not asserted: `python -O` strips asserts, and this one is load
        # bearing -- an unwarmed pool re-creates the deadlock silently.
        raise RuntimeError(f"worker pool did not warm up: {got!r}")
    return EXECUTOR


def _pmap(fn, jobs_iter):
    """Parallel map over the pre-forked pool, keeping failures visible as None."""
    if EXECUTOR is None:
        raise RuntimeError("_start_workers() must run before any fit or any _pmap")
    return [r for r in EXECUTOR.map(fn, jobs_iter, chunksize=1)]


def _seed(*parts):
    """A reproducible integer seed from arbitrary labels.

    NOT `hash()`. Python salts string hashing per process, so `hash(("null",
    name))` gives a different seed on every invocation and the artifact would
    not be reproducible from its own inputs -- the property this project spends
    a register on keeping (PAPER_MASTER 7.6).
    """
    h = hashlib.sha256("|".join(str(x) for x in parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


# ===========================================================================
# The two routes to an MDE, and the bracket that serves both
# ===========================================================================
def _lambda_target(k):
    """Noncentrality a chi-square(k) test needs for TARGET_POWER at ALPHA."""
    crit = stats.chi2.isf(ALPHA, k)
    return float(brentq(lambda L: stats.ncx2.sf(crit, k, L) - TARGET_POWER, 1e-9, 1e4))


def _mde_analytic(g, Sigma, k):
    """delta solving delta^2 * g' Sigma^-1 g = lambda_target.

    `g` is the day 0..7 coefficient vector the estimator returns for a UNIT
    planted effect, so it carries whatever attenuation the geometry imposes --
    window truncation, and the dilution from one episode's effect landing on a
    day the stack has labelled with another episode's relative day. That is what
    makes this an MDE on the effective episode count rather than on the nominal
    one. On the current episode list that attenuation is zero on discovery and C1
    and 0.0029 per unit on C2 (one 10-day gap costs days 6 and 7 of one episode),
    so g is the planted profile or very nearly it;
    `first_week_attenuation_max_abs_dev` is the per-run measurement, not an
    assumption that it stays small.
    """
    # Sigma can be singular or near-singular, and it is NOT a bug when it is:
    # the empirical covariance of an 8-vector estimated from fewer than ~9 null
    # draws has no inverse at all. A small diagnostic run must therefore report
    # "not computable at this size" and let MIN_SIMS decide the verdict, not die
    # with LinAlgError three quarters of the way through -- which is what it did
    # the first time it was run at 2 sims.
    if Sigma is None or not np.all(np.isfinite(Sigma)):
        return np.nan, np.nan
    try:
        if np.linalg.cond(Sigma) > 1e12:
            return np.nan, np.nan
        lam_unit = float(g @ np.linalg.solve(Sigma, g))
    except np.linalg.LinAlgError:
        return np.nan, np.nan
    if not np.isfinite(lam_unit) or lam_unit <= 0:
        return np.nan, np.nan
    return float(np.sqrt(_lambda_target(k) / lam_unit)), lam_unit


def _bracket_power(power_at, start, target=TARGET_POWER, step=RI_STEP,
                   max_out=RI_MAX_STEPOUTS, max_in=RI_MAX_STEPINS,
                   refine=RI_REFINE_ROUNDS, log=print):
    """Find the delta where `power_at` crosses `target`, stepping out to bracket.

    THIS IS THE FIX FOR E1.2. The rejected design fixed the bracket at
    [0.8, 1.25] x a seed value and returned NaN whenever the answer was outside
    -- which, given that a third of every placebo design absorbs planted signal,
    it always was. Here the bracket is discovered: step outward geometrically
    until the target is actually straddled, then bisect inside it.

    Returns (point, lo, hi, closed, trace). When the cap is reached the bracket
    is NOT closed and `point` is the last delta evaluated, reported as a ONE-SIDED
    BOUND with `closed = False`. A bound is an answer. NaN after spending the
    budget is not.
    """
    trace = []
    lo = hi = None
    d = float(start)
    p = power_at(d)
    trace.append((d, p))
    log(f"      pilot delta={d:.6f} power={p:.3f}")
    if p >= target:
        hi = d
        for _ in range(max_in):
            d /= step
            p = power_at(d)
            trace.append((d, p))
            log(f"      step in  delta={d:.6f} power={p:.3f}")
            if p < target:
                lo = d
                break
            hi = d
    else:
        lo = d
        for _ in range(max_out):
            d *= step
            p = power_at(d)
            trace.append((d, p))
            log(f"      step out delta={d:.6f} power={p:.3f}")
            if p >= target:
                hi = d
                break
            lo = d
    if lo is None or hi is None:
        bound = hi if hi is not None else lo
        return float(bound), (np.nan if lo is None else float(lo)), \
            (np.nan if hi is None else float(hi)), False, trace
    for _ in range(refine):
        mid = float(np.sqrt(lo * hi))
        p = power_at(mid)
        trace.append((mid, p))
        log(f"      refine   delta={mid:.6f} power={p:.3f}")
        if p >= target:
            hi = mid
        else:
            lo = mid
    return float(np.sqrt(lo * hi)), float(lo), float(hi), True, trace


def _gate_headroom(n):
    """Print how far GATE_TOL_LOG sits above Monte Carlo noise at n sims.

    A gate whose tolerance is swamped by its own sampling error cannot fire
    (E1.4). The rejection rate at target power has SE sqrt(p(1-p)/n); converting
    that to delta through the local slope of the noncentral chi-square power
    curve gives the noise floor on log(MDE). This prints both so the margin is
    visible in the log rather than asserted in a comment.
    """
    k = len(FIRST_WEEK)
    lam = _lambda_target(k)
    crit = stats.chi2.isf(ALPHA, k)
    h = 0.02
    # d(power)/d(log lambda), then to log delta: lambda scales with delta^2, so
    # d(power)/d(log delta) = 2 * d(power)/d(log lambda).
    d_dloglam = (stats.ncx2.sf(crit, k, lam * np.exp(h))
                 - stats.ncx2.sf(crit, k, lam * np.exp(-h))) / (2 * h)
    slope = 2.0 * d_dloglam
    se_p = np.sqrt(TARGET_POWER * (1 - TARGET_POWER) / max(n, 1))
    noise = float(se_p / abs(slope)) if slope else np.inf
    print(f"  gate: tolerance |log ratio| <= {GATE_TOL_LOG:.3f}; Monte Carlo noise "
          f"floor at {n} sims is {noise:.3f} ({GATE_TOL_LOG / noise:.1f}x headroom)")
    return noise


# ===========================================================================
# Roth (2022) pre-trend diagnostic -- the corrected conversion (E1.1)
# ===========================================================================
def _roth_diagnostic(Sigma_fw, Sigma_pre, pre_days, mdes):
    """The lambda-matched trend slope, and the pre-test's power against it.

    A linear pre-trend of slope b per day, anchored at EVENT_REFERENCE_DAY,
    contributes b*(d - ref) to the day-d coefficient. Over the first week that is
    b*u with u = [1..8]; over the pre-period it is b*v with v = [-13..-1].

    b* solves b^2 * u' Sigma_fw^-1 u = lambda_target, i.e. the slope whose
    contamination of the JOINT WALD statistic equals that of an MDE-sized real
    effect. Because the MDE is defined by a fixed target power, lambda at the MDE
    is the same number whatever the effect profile, so b* is profile-free -- and
    the whole of the old design's LEVER shortcut was an attempt to convert
    between units that do not need converting. What is profile-dependent is the
    ratio b*/MDE, returned for each profile so the flattering one cannot be
    quoted alone.

    `pretest_power` is the actual Roth quantity: the probability the pre-period
    joint test rejects when the true pre-trend is exactly b*. A low number means
    the pre-test is not the protection it looks like. It is computed on the
    PRE-PERIOD Sigma, which is where the window-truncation loss measured in
    `_geometry` lands -- so the diagnostic sees the truncation the first-week test
    mostly escapes.
    """
    k = len(FIRST_WEEK)
    u = np.array([d - EVENT_REFERENCE_DAY for d in FIRST_WEEK], dtype=float)
    lam_t = _lambda_target(k)
    try:
        lam_trend_unit = float(u @ np.linalg.solve(Sigma_fw, u))
    except np.linalg.LinAlgError:
        lam_trend_unit = np.nan
    if not np.isfinite(lam_trend_unit) or lam_trend_unit <= 0:
        return {"trend_lambda_per_unit": np.nan, "lambda_target": lam_t,
                "bias_matched_slope_per_day": np.nan,
                "retired_lever_rule_slope_per_day": np.nan,
                "retired_lever_rule_optimism": np.nan}
    b_star = float(np.sqrt(lam_t / lam_trend_unit))
    out = {"trend_lambda_per_unit": lam_trend_unit,
           "lambda_target": lam_t,
           "bias_matched_slope_per_day": b_star,
           "retired_lever_rule_slope_per_day": np.nan,
           "retired_lever_rule_optimism": np.nan}
    lvl = mdes.get("level")
    if lvl and np.isfinite(lvl):
        # What the rejected design would have reported, recomputed here so the
        # optimism factor is measured on THIS run rather than quoted from a
        # review. LEVER = mean(d - ref) over the first week = 4.5.
        lever = float(np.mean(u))
        out["retired_lever_rule_slope_per_day"] = lvl / lever
        out["retired_lever_rule_optimism"] = (lvl / lever) / b_star
    for name, mde in mdes.items():
        out[f"bias_matched_slope_over_mde_{name}"] = (
            b_star / mde if mde and np.isfinite(mde) else np.nan)
    if Sigma_pre is not None and len(pre_days) and np.all(np.isfinite(Sigma_pre)):
        v = np.array([d - EVENT_REFERENCE_DAY for d in pre_days], dtype=float)
        kp = len(pre_days)
        try:
            lam_pre_unit = float(v @ np.linalg.solve(Sigma_pre, v))
        except np.linalg.LinAlgError:
            return out
        lam_pre = b_star ** 2 * lam_pre_unit
        out["pretest_k"] = kp
        out["pretest_lambda_at_bias_matched_slope"] = lam_pre
        out["pretest_power_at_bias_matched_slope"] = float(
            stats.ncx2.sf(stats.chi2.isf(ALPHA, kp), kp, lam_pre))
    return out


# ===========================================================================
# Geometry: the effective episode count, measured (not assumed)
# ===========================================================================
def _geometry(name, starts, dates, cds, outcome, wins_for_loss):
    """Window collision and depth, measured by running build_stack on the real dates.

    The outcome values are irrelevant to `build_stack` -- it keys on dates and
    districts -- so this uses a constant column and costs no fits.
    """
    idx = pd.DataFrame({
        "communitydistrict": np.repeat(cds, len(dates)),
        "incident_date": np.tile(np.asarray(dates), len(cds)),
        outcome: 0.1, "total_calls": 50,
        "dow": np.tile(np.asarray([d.dayofweek for d in dates]), len(cds)),
    })
    st = build_stack(idx, starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    n = len(starts)
    full_rows = n * len(cds) * (EVENT_WINDOW_PRE + EVENT_WINDOW_POST + 1)
    fw = st[st["rel_day"].between(min(FIRST_WEEK), max(FIRST_WEEK))]
    fw_depth = fw.groupby("episode")["rel_day"].nunique().sum() / len(FIRST_WEEK)
    pre_days = list(range(-EVENT_WINDOW_PRE, EVENT_REFERENCE_DAY))
    pre = st[st["rel_day"].isin(pre_days)]
    pre_depth = pre.groupby("episode")["rel_day"].nunique().sum() / len(pre_days)
    o = np.array([pd.Timestamp(d).toordinal() for d in starts])
    crowded = int(sum(1 for i, x in enumerate(o)
                      if any(abs(x - y) <= 28 for j, y in enumerate(o) if j != i)))
    gaps = np.diff(np.sort(o)) if len(o) > 1 else np.array([np.inf])

    # EXACTLY WHEN A FIRST-WEEK DAY IS LOST, derived rather than feared.
    # `build_stack` gives a contested district-day to the NEARER episode, ties to
    # the earlier one. Day d of episode A (0 <= d <= 7) falls on date A+d, whose
    # distance to a later episode B is |d - (B-A)|. That beats d exactly when
    # 0 < B-A < 2d. So only a LATER neighbour can steal a first-week day -- an
    # earlier one is always further away -- and only if it starts within 14 days.
    # A 10-day gap therefore costs days 6 and 7 and nothing else.
    # The other way to lose a day is the stratum boundary: a window running past
    # the end of the sample has no rows there at all.
    srt = sorted(pd.Timestamp(d) for d in starts)
    predicted = 0
    for i, a in enumerate(srt):
        nxt = (srt[i + 1] - a).days if i + 1 < len(srt) else 10 ** 6
        for d in FIRST_WEEK:
            day = a + pd.Timedelta(days=d)
            stolen = 0 < nxt < 2 * d
            outside = not any(lo_ <= day <= hi_ for lo_, hi_ in wins_for_loss)
            predicted += int(stolen or outside)

    return dict(n_nominal=n,
                min_gap_between_starts=int(gaps.min()),
                pairs_within_14d_steal_range=int((gaps < 2 * max(FIRST_WEEK)).sum()),
                pairs_within_full_window=int((gaps <= EVENT_WINDOW_PRE + EVENT_WINDOW_POST).sum()),
                first_week_days_lost_predicted=int(predicted),
                n_identifying=int(st["episode"].nunique()),
                first_week_depth=float(fw_depth),
                pre_period_depth=float(pre_depth),
                window_rows_kept=float(len(st) / full_rows) if full_rows else np.nan,
                episodes_with_neighbour_28d=crowded,
                pre_days=pre_days)


def _placebo_diagnostics(name, starts, wins, seed=19_20260912):
    """Why the RI bracket behaves the way it does, measured on 2000 draws.

    Two numbers, both from `event_study.placebo_starts` itself:
      contaminated -- share of placebo starts within 7 days of a REAL start. This
        is the mechanism in E1.2: under a planted effect, that share of every
        placebo design absorbs genuine signal and the RI null shifts up.
      outside -- share of placebo starts falling outside the stratum's OWN
        windows. `placebo_starts` anchors a gap-permuted sequence inside
        [panel.min, panel.max] and knows nothing about holes in between, so on a
        stratum made of disjoint windows it draws into the hole. C1 is two
        windows separated by the whole discovery period, so this is not a corner
        case there; it is the normal outcome.
    """
    real = set(pd.Timestamp(d).toordinal() for d in starts)
    lo, hi = wins[0][0], wins[-1][1]
    rng = np.random.default_rng(seed)
    cont, outside, accepted = [], [], 0
    for _ in range(2000):
        ps = placebo_starts(rng, starts, lo, hi, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
        if len(ps) != len(starts):
            continue
        accepted += 1
        cont.append(np.mean([any(abs(p.toordinal() - r) <= 7 for r in real) for p in ps]))
        outside.append(np.mean([not any(a <= p <= b for a, b in wins) for p in ps]))
    span = (max(starts) - min(starts)).days if len(starts) > 1 else 0
    room = ((hi - pd.Timedelta(days=EVENT_WINDOW_POST + 1))
            - (lo + pd.Timedelta(days=EVENT_WINDOW_PRE + 1))).days - span
    if not accepted:
        return dict(accept_rate=0.0, contaminated=np.nan, contaminated_p10=np.nan,
                    contaminated_p90=np.nan, outside_windows=np.nan,
                    sequence_span_days=span, free_days=room)
    cont, outside = np.array(cont), np.array(outside)
    return dict(accept_rate=accepted / 2000.0,
                contaminated=float(cont.mean()),
                contaminated_p10=float(np.percentile(cont, 10)),
                contaminated_p90=float(np.percentile(cont, 90)),
                outside_windows=float(outside.mean()),
                sequence_span_days=span, free_days=room)


# ===========================================================================
# Run
# ===========================================================================
_start_workers()
fingerprint = _check_generator_fingerprint()
print(f"generator fingerprint ok: {fingerprint[:16]}...")

vc = _variance_components(args.outcome)
rows = [{"metric": "outcome", "value": args.outcome},
        {"metric": "episode_list", "value": EPISODE_LIST_PRIMARY},
        {"metric": "freeze_active", "value": int(FREEZE_ACTIVE)},
        {"metric": "generator_fingerprint", "value": fingerprint},
        {"metric": "target_power", "value": TARGET_POWER},
        {"metric": "alpha", "value": ALPHA},
        {"metric": "min_sims_required", "value": MIN_SIMS},
        {"metric": "null_sims_requested", "value": args.null_sims},
        {"metric": "scan_sims_requested", "value": args.scan_sims}]

if vc is None:
    # E1.5: there is no fallback. A power analysis whose noise structure is an
    # assumption reports an MDE that is linear in that assumption.
    rows.append({"metric": "VERDICT", "value": "UNDETERMINED"})
    rows.append({"metric": "undetermined_reason",
                 "value": f"no {args.outcome} in panel_cd_day.parquet; "
                          "every noise component must be MEASURED (E1.5)"})
    pd.DataFrame(rows).to_csv(OUTPUTS_TABLES / "power_analysis.csv", index=False)
    print("UNDETERMINED — the discovery panel is not available, so the noise "
          "structure cannot be measured. This run refuses to assume one.")
    raise SystemExit(2)

print(f"measured from the discovery panel ({vc['n_rows']:,} rows): "
      f"rho={vc['rho']:.4f} sigma={vc['sigma']:.4f} mean={vc['mu']:.4f}")
print(f"  component scales (x sigma): district={vc['cd_scale']:.3f} "
      f"dow={vc['dow_scale']:.3f} day_shock={vc['day_scale']:.3f}")
print(f"  implied total sd {vc['implied_total_sd']:.4f} against the panel's "
      f"{vc['panel_total_sd']:.4f}")
for k in ("rho", "sigma", "mu", "cd_scale", "dow_scale", "day_scale",
          "implied_total_sd", "panel_total_sd"):
    rows.append({"metric": f"noise.{k}", "value": round(float(vc[k]), 6)})

episodes = pd.read_csv(DATA_REFERENCE / EPISODE_LIST_PRIMARY, parse_dates=["start", "end"])
_check_strata_agree_with_paper(episodes)
rows.append({"metric": "episodes_total", "value": int(len(episodes))})

cds = list(VALID_CDS)
noise_rng = np.random.default_rng(19_20260912)
cd_effect = noise_rng.normal(0, vc["sigma"] * vc["cd_scale"], len(cds))
dow_effect = noise_rng.normal(0, vc["sigma"] * vc["dow_scale"], 7)

noise_floor = _gate_headroom(args.scan_sims)
rows.append({"metric": "gate_tolerance_log", "value": GATE_TOL_LOG})
rows.append({"metric": "gate_mc_noise_floor_log", "value": round(noise_floor, 4)})

gate_breaches, stratum_verdicts = [], {}
n_null_done_min, n_scan_done_min = 10 ** 9, 10 ** 9

for name in [s.strip() for s in args.strata.split(",") if s.strip()]:
    print("\n" + "=" * 70)
    wins = _stratum_windows(name)
    starts = _stratum_starts(episodes, name)
    dates = _stratum_dates(name)
    print(f"stratum {name}: {[(str(a.date()), str(b.date())) for a, b in wins]} "
          f"— {len(starts)} episodes, {len(dates)} days")
    P = f"{name}."
    rows.append({"metric": P + "windows",
                 "value": "|".join(f"{a.date()}..{b.date()}" for a, b in wins)})
    rows.append({"metric": P + "calendar_days", "value": int(len(dates))})

    if len(starts) < 2:
        rows.append({"metric": P + "status", "value": "NOT_ESTIMABLE_TOO_FEW_EPISODES"})
        stratum_verdicts[name] = "NOT_ESTIMABLE"
        continue

    geo = _geometry(name, starts, dates, cds, args.outcome, wins)
    pre_days = geo.pop("pre_days")
    # DEFEAT-TESTABLE: the analytic loss rule above is checked against what
    # build_stack actually produced. If they disagree, the reasoning behind
    # `first_week_attenuation_max_abs_dev` and the whole effective-N argument is
    # wrong, and that must stop the run rather than be averaged into an MDE.
    observed_lost = int(round(len(FIRST_WEEK) * (geo["n_identifying"] - geo["first_week_depth"])))
    if observed_lost != geo["first_week_days_lost_predicted"]:
        raise RuntimeError(
            f"{name}: first-week days lost to window collision -- predicted "
            f"{geo['first_week_days_lost_predicted']}, build_stack produced "
            f"{observed_lost}. The nearest-episode assignment rule is not what "
            "this file assumes, so every statement here about effective N is "
            "unsupported until the rule is re-derived.")
    for k, v in geo.items():
        rows.append({"metric": P + "geometry." + k,
                     "value": round(float(v), 4) if isinstance(v, float) else v})
    print(f"  geometry: nominal {geo['n_nominal']}, identifying {geo['n_identifying']}, "
          f"first-week depth {geo['first_week_depth']:.2f}, pre-period depth "
          f"{geo['pre_period_depth']:.2f}, rows kept {geo['window_rows_kept']:.3f}, "
          f"{geo['episodes_with_neighbour_28d']} crowded within 28d")

    # An episode whose window straddles the B-HEARD launch has post-days in a
    # regime its stratum says it is not in. C1 ends the day before the launch and
    # its last episode starts 2021-05-24, so days 0..7 fit and days 8..14 do not.
    # Measured rather than assumed, because if a rebuild moves an episode a week
    # later the first week itself starts crossing and the stratification stops
    # meaning what it says.
    launch = pd.Timestamp(BHEARD_LAUNCH)
    straddle_fw = int(sum(1 for st_ in starts
                          if st_ < launch <= st_ + pd.Timedelta(days=max(FIRST_WEEK))))
    straddle_win = int(sum(1 for st_ in starts
                           if st_ - pd.Timedelta(days=EVENT_WINDOW_PRE) < launch
                           <= st_ + pd.Timedelta(days=EVENT_WINDOW_POST)))
    rows.append({"metric": P + "geometry.episodes_window_straddles_bheard",
                 "value": straddle_win})
    rows.append({"metric": P + "geometry.episodes_first_week_straddles_bheard",
                 "value": straddle_fw})
    if straddle_win:
        print(f"  {straddle_win} episode window(s) straddle the B-HEARD launch "
              f"({BHEARD_LAUNCH}); {straddle_fw} of them in the FIRST WEEK, which "
              "is the part the test uses")

    pdiag = _placebo_diagnostics(name, starts, wins)
    for k, v in pdiag.items():
        rows.append({"metric": P + "placebo." + k,
                     "value": round(float(v), 4) if np.isfinite(v) else "nan"})
    print(f"  placebo geometry: {pdiag['free_days']} free days for a "
          f"{pdiag['sequence_span_days']}-day sequence; "
          f"{pdiag['contaminated']:.1%} of placebo starts within 7d of a real one "
          f"(p10 {pdiag['contaminated_p10']:.1%}, p90 {pdiag['contaminated_p90']:.1%}); "
          f"{pdiag['outside_windows']:.1%} fall outside this stratum's own windows")

    def _ctx(starts_override=None):
        """The picklable bundle a worker needs. Passed with every job, because
        the pool is forked before any stratum is known (see `_start_workers`)."""
        return dict(dates=dates, cds=cds,
                    starts=list(starts_override if starts_override is not None else starts),
                    outcome=args.outcome, rho=vc["rho"], sigma=vc["sigma"],
                    mu=vc["mu"], cd_effect=cd_effect, dow_effect=dow_effect,
                    day_scale=vc["day_scale"])

    CTX = _ctx()

    # ---- one panel, used for the equivalence check and the unit response ----
    base = synthetic_panel(np.random.default_rng(101), dates, cds, vc["rho"],
                           vc["sigma"], vc["mu"], cd_effect, dow_effect, vc["day_scale"])
    worst = _check_plant_equivalence(base, starts, args.outcome)
    rows.append({"metric": P + "plant_equivalence_max_abs_diff", "value": float(worst)})

    # ---- unit response g: exact, and verified to be draw-independent ----
    # b(y) is linear in y, so b(null + z) - b(null) = b(z) whatever the null
    # draw. Measuring it on two different draws and asserting agreement is a
    # check that can fail -- it fails the moment the estimator stops being linear
    # in the outcome, which is exactly when this whole route stops being valid.
    def _unit_response(panel, prof, ep_starts=None, overlap="add"):
        ep_starts = starts if ep_starts is None else ep_starts
        s0 = build_stack(panel, ep_starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
        a = _fit_coefs(s0, args.outcome, list(FIRST_WEEK))
        b = _fit_coefs(plant(s0, ep_starts, prof, 1.0, args.outcome, overlap=overlap),
                       args.outcome, list(FIRST_WEEK))
        return None if (a is None or b is None) else b[0] - a[0]

    alt = synthetic_panel(np.random.default_rng(202), dates, cds, vc["rho"],
                          vc["sigma"], vc["mu"], cd_effect, dow_effect, vc["day_scale"])
    g, g_sat = {}, {}
    for pname, prof in PROFILES.items():
        g1 = _unit_response(base, prof)
        g2 = _unit_response(alt, prof)
        gs = _unit_response(base, prof, overlap="saturate")
        if gs is not None:
            g_sat[pname] = gs
        if g1 is None or g2 is None:
            raise RuntimeError(f"{name}/{pname}: unit response not estimable")
        d = float(np.max(np.abs(g1 - g2)))
        if d > 1e-8:
            raise RuntimeError(
                f"{name}/{pname}: the unit effect response depends on the null draw "
                f"by {d:.3e}. The estimator is not linear in the outcome, so the "
                "analytic route and the stack-planting economy are both invalid.")
        g[pname] = g1
        rows.append({"metric": P + f"unit_response_draw_invariance.{pname}", "value": d})
        # HOW MUCH THE GEOMETRY ATTENUATES THE FIRST WEEK, as a number rather
        # than as a worry. g is the day 0..7 coefficient vector the estimator
        # returns for a unit planted effect; if the geometry cost nothing, g is
        # the planted profile exactly. Measured: 0 on discovery and C1, 0.002866
        # on C2, where one 10-day gap hands days 6 and 7 of one episode to its
        # neighbour. This metric is what makes that checkable per run rather than
        # true only on today's episode list.
        rows.append({"metric": P + f"first_week_attenuation_max_abs_dev.{pname}",
                     "value": float(np.max(np.abs(g1 - np.asarray(prof, dtype=float))))})

    # ---- null sims: Sigma from the estimator's vcov, and empirically ----
    seeds = np.random.SeedSequence(_seed("null", name, args.outcome)).spawn(args.null_sims)
    print(f"  null leg: {args.null_sims} sims on {JOBS} workers", flush=True)
    res = [r for r in _pmap(_null_sim, [(CTX, sd) for sd in seeds]) if r is not None]
    n_null_done_min = min(n_null_done_min, len(res))
    rows.append({"metric": P + "n_null_sims_completed", "value": len(res)})
    if len(res) < 2:
        rows.append({"metric": P + "status", "value": "NOT_ESTIMABLE_NULL_LEG"})
        stratum_verdicts[name] = "NOT_ESTIMABLE"
        continue
    Sigma_model = np.mean([r["fw_V"] for r in res], axis=0)
    B = np.vstack([r["fw_b"] for r in res])
    # The EMPIRICAL covariance needs more draws than the vector is long or it is
    # rank-deficient by construction. Say so rather than inverting it.
    Sigma_emp = np.cov(B, rowvar=False) if len(res) > len(FIRST_WEEK) + 1 else None
    rows.append({"metric": P + "sigma_empirical_available",
                 "value": int(Sigma_emp is not None)})
    pre_ok = [r for r in res if r["pre_V"] is not None]
    Sigma_pre = np.mean([r["pre_V"] for r in pre_ok], axis=0) if pre_ok else None

    corr = Sigma_model / np.sqrt(np.outer(np.diag(Sigma_model), np.diag(Sigma_model)))
    k = len(FIRST_WEEK)
    off = (corr.sum() - k) / (k * (k - 1))
    rows.append({"metric": P + "sigma.mean_offdiag_corr", "value": round(float(off), 4)})
    print(f"  Sigma: mean off-diagonal correlation {off:.3f} "
          "(the shared day -1 reference makes it equicorrelated)")

    # ---- route AN, and the MC scan it seeds ----
    mdes_an, mdes_mc, lam_unit = {}, {}, {}
    lam_unit_sat = {}
    for pname in PROFILES:
        m_an, lu = _mde_analytic(g[pname], Sigma_model, k)
        m_emp, _ = _mde_analytic(g[pname], Sigma_emp, k)
        mdes_an[pname], lam_unit[pname] = m_an, lu
        if pname in g_sat:
            m_sat, lu_sat = _mde_analytic(g_sat[pname], Sigma_model, k)
            lam_unit_sat[pname] = lu_sat
            rows.append({"metric": P + f"mde_analytic_saturating_overlap.{pname}",
                         "value": m_sat})
        rows.append({"metric": P + f"mde_analytic_modelvcov.{pname}", "value": m_an})
        rows.append({"metric": P + f"mde_analytic_empiricalvcov.{pname}", "value": m_emp})
        rows.append({"metric": P + f"lambda_per_unit.{pname}", "value": lu})
        if np.isfinite(m_an) and np.isfinite(m_emp) and m_an > 0:
            rows.append({"metric": P + f"vcov_inflation.{pname}",
                         "value": round(float(m_emp / m_an), 4)})
        print(f"  {pname:12s} analytic MDE {m_an:.6f} (model vcov) / "
              f"{m_emp:.6f} (empirical vcov)")

    crit = stats.chi2.isf(ALPHA, k)
    scan_seeds = np.random.SeedSequence(_seed("scan", name, args.outcome)).spawn(args.scan_sims)
    _scan_cache = {}

    def mc_power(pname, delta):
        key = (pname, round(float(delta), 12))
        if key in _scan_cache:
            return _scan_cache[key]
        jobs = [(CTX, sd, [(pname, float(delta))]) for sd in scan_seeds]
        out = [r for r in _pmap(_scan_sim, jobs) if r is not None]
        vals = [v[(pname, float(delta))] for v in out if v[(pname, float(delta))] is not None]
        p = float(np.mean([x > crit for x in vals])) if vals else np.nan
        _scan_cache[key] = (p, len(vals))
        return _scan_cache[key]

    for pname in PROFILES:
        seed_delta = mdes_an[pname] if np.isfinite(mdes_an[pname]) else 0.01
        print(f"  MC scan [{pname}] seeded at the analytic MDE {seed_delta:.6f}")
        completed = []

        def _pa(d, _p=pname, _c=completed):
            pw, n = mc_power(_p, d)
            _c.append(n)
            return pw if np.isfinite(pw) else 0.0

        point, blo, bhi, closed, trace = _bracket_power(
            _pa, seed_delta, refine=RI_REFINE_ROUNDS,
            log=lambda m: print(m, flush=True))
        mdes_mc[pname] = point if closed else np.nan
        n_scan_done_min = min(n_scan_done_min, min(completed) if completed else 0)
        rows.append({"metric": P + f"mde_mc.{pname}", "value": point})
        rows.append({"metric": P + f"mde_mc_bracket_lo.{pname}", "value": blo})
        rows.append({"metric": P + f"mde_mc_bracket_hi.{pname}", "value": bhi})
        rows.append({"metric": P + f"mde_mc_bracket_closed.{pname}", "value": int(closed)})
        rows.append({"metric": P + f"n_scan_sims_completed.{pname}",
                     "value": int(min(completed)) if completed else 0})

        # ---- the cross-route gate (E1.4) ----
        if closed and np.isfinite(mdes_an[pname]) and mdes_an[pname] > 0 and point > 0:
            ratio = float(np.log(point / mdes_an[pname]))
            ok = abs(ratio) <= GATE_TOL_LOG
            rows.append({"metric": P + f"gate_log_ratio.{pname}", "value": round(ratio, 4)})
            rows.append({"metric": P + f"gate_ok.{pname}", "value": int(ok)})
            if not ok:
                gate_breaches.append(f"{name}/{pname} log ratio {ratio:+.3f}")
            print(f"    gate [{pname}]: MC {point:.6f} vs analytic "
                  f"{mdes_an[pname]:.6f}, log ratio {ratio:+.3f} "
                  f"({'ok' if ok else 'BREACH'})")
        else:
            rows.append({"metric": P + f"gate_ok.{pname}", "value": "not_evaluable"})
            gate_breaches.append(f"{name}/{pname} not evaluable (bracket not closed)")

    # ---- effective episode count, against a spaced reference ----
    spaced = _spaced_starts(name, len(starts))
    for pname in PROFILES:
        rows.append({"metric": P + f"n_effective.{pname}", "value": "not_measurable"})
    if spaced is not None:
        ctx_ref = _ctx(spaced)
        ref_seeds = np.random.SeedSequence(_seed("ref", name, args.outcome)).spawn(args.ref_sims)
        ref = [r for r in _pmap(_null_sim, [(ctx_ref, sd) for sd in ref_seeds])
               if r is not None]
        if len(ref) >= 2:
            Sig_ref = np.mean([r["fw_V"] for r in ref], axis=0)
            base_ref = synthetic_panel(np.random.default_rng(303), dates, cds, vc["rho"],
                                       vc["sigma"], vc["mu"], cd_effect, dow_effect,
                                       vc["day_scale"])
            for pname, prof in PROFILES.items():
                s0 = build_stack(base_ref, spaced, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
                a = _fit_coefs(s0, args.outcome, list(FIRST_WEEK))
                b = _fit_coefs(plant(s0, spaced, prof, 1.0, args.outcome),
                               args.outcome, list(FIRST_WEEK))
                if a is None or b is None:
                    continue
                gr = b[0] - a[0]
                lam_ref = float(gr @ np.linalg.solve(Sig_ref, gr))
                neff = len(starts) * lam_unit[pname] / lam_ref if lam_ref > 0 else np.nan
                rows = [r for r in rows
                        if r["metric"] != P + f"n_effective.{pname}"]
                rows.append({"metric": P + f"n_effective.{pname}",
                             "value": round(float(neff), 3)})
                rows.append({"metric": P + f"lambda_per_unit_spaced.{pname}",
                             "value": lam_ref})
                neff_sat = np.nan
                if pname in lam_unit_sat and lam_ref > 0:
                    neff_sat = len(starts) * lam_unit_sat[pname] / lam_ref
                    rows.append({"metric": P + f"n_effective_saturating.{pname}",
                                 "value": round(float(neff_sat), 3)})
                print(f"  n_effective [{pname}]: {neff:.2f} of {len(starts)} nominal "
                      f"under additive overlap, {neff_sat:.2f} under saturating "
                      f"overlap — a RATIO OF TWO ESTIMATED covariances "
                      f"({len(res)} and {len(ref)} null sims), so it is only "
                      "interpretable at full sim counts")

    # ---- Roth pre-trend diagnostic (E1.1) ----
    headline = {p: (mdes_mc.get(p) if np.isfinite(mdes_mc.get(p, np.nan))
                    else mdes_an.get(p)) for p in PROFILES}
    roth = _roth_diagnostic(Sigma_model, Sigma_pre, pre_days, headline)
    for kk, vv in roth.items():
        rows.append({"metric": P + "roth." + kk,
                     "value": (round(float(vv), 8) if np.isfinite(vv) else "nan")})
    print(f"  Roth: bias-matched trend {roth.get('bias_matched_slope_per_day', float('nan')):.3e} "
          f"per day; the retired LEVER rule would have reported "
          f"{roth.get('retired_lever_rule_slope_per_day', float('nan')):.3e} "
          f"({roth.get('retired_lever_rule_optimism', float('nan')):.2f}x optimistic)")
    for pname in PROFILES:
        print(f"    b*/MDE[{pname}] = "
              f"{roth.get(f'bias_matched_slope_over_mde_{pname}', float('nan')):.4f}")
    if "pretest_power_at_bias_matched_slope" in roth:
        print(f"    pre-test power against that trend: "
              f"{roth['pretest_power_at_bias_matched_slope']:.3f} "
              f"(k={roth['pretest_k']}, on the truncated pre-period)")

    # ---- randomization-inference MDE: pilot, then step out (E1.2) ----
    ri_status, ri_point, ri_lo, ri_hi, ri_closed = "SKIPPED", np.nan, np.nan, np.nan, 0
    rip = "none"
    if args.no_ri:
        ri_status = "SKIPPED_BY_FLAG"
    elif pdiag["outside_windows"] > 0.01 or pdiag["accept_rate"] < RI_MIN_ACCEPT:
        # Not a budget problem and not a bug in this file: `placebo_starts`
        # anchors a gap-permuted sequence inside one contiguous [lo, hi], so on a
        # stratum built from disjoint windows it draws placebo episodes into the
        # gap. For C1 the gap IS the discovery period. Saying so is the finding.
        ri_status = "NOT_DEFINED_DISJOINT_WINDOWS"
        print(f"  RI: NOT DEFINED for {name}. {pdiag['outside_windows']:.1%} of "
              "placebo starts fall outside this stratum's own windows, because "
              "event_study.placebo_starts draws inside one contiguous span and "
              "this stratum is not contiguous. The project's PRIMARY p-value "
              "cannot be computed here as the estimator currently draws placebos.")
    else:
        seed_delta = next((mdes_mc[p] for p in PROFILES
                           if np.isfinite(mdes_mc.get(p, np.nan))), None)
        if seed_delta is None:
            seed_delta = mdes_an["level"]
        rip = "level" if "level" in PROFILES else list(PROFILES)[0]
        print(f"  RI leg [{rip}]: pilot {args.ri_pilot_sims}x{args.ri_pilot_draws}, "
              f"refine {args.ri_sims}x{args.ri_draws}, seeded at {seed_delta:.6f}")
        n_ri = {"sims": args.ri_pilot_sims, "draws": args.ri_pilot_draws}

        def ri_power(delta):
            jobs = [(CTX, _seed("ri", name, rip, round(float(delta), 10), i),
                     rip, float(delta), n_ri["draws"])
                    for i in range(n_ri["sims"])]
            out = [r for r in _pmap(_ri_sim, jobs) if r is not None]
            return float(np.mean([p < ALPHA for p in out])) if out else 0.0

        ri_point, ri_lo, ri_hi, ri_closed_b, _ = _bracket_power(
            ri_power, seed_delta, refine=0, log=lambda m: print(m, flush=True))
        if ri_closed_b:
            n_ri.update(sims=args.ri_sims, draws=args.ri_draws)
            ri_point, ri_lo, ri_hi, ri_closed_b, _ = _bracket_power(
                ri_power, float(np.sqrt(ri_lo * ri_hi)), log=lambda m: print(m, flush=True))
        ri_closed = int(ri_closed_b)
        if ri_closed:
            ri_status = "BRACKETED"
        elif np.isnan(ri_hi):
            # Stepped out to the cap without reaching target power: the RI MDE is
            # ABOVE everything tried. This is the outcome E1.2 predicts, and it is
            # reported as a bound rather than as NaN.
            ri_status = f"BOUND_ABOVE_{RI_STEP ** RI_MAX_STEPOUTS:.1f}x_SEED"
        else:
            # Target power held at every step IN: the RI MDE is below the smallest
            # delta tried. Rarer, and the opposite claim, so it gets its own label.
            ri_status = f"BOUND_BELOW_SEED_OVER_{RI_STEP ** RI_MAX_STEPINS:.1f}"
        print(f"  RI MDE [{rip}]: {ri_point:.6f} "
              f"({'bracketed' if ri_closed else 'one-sided bound'}), "
              f"bracket [{ri_lo:.6f}, {ri_hi:.6f}]")
    rows.append({"metric": P + "ri_profile",
                 "value": rip if ri_status == "BRACKETED" or ri_status.startswith("BOUND_")
                          else "none"})
    rows.append({"metric": P + "ri_status", "value": ri_status})
    rows.append({"metric": P + "mde_ri", "value": ri_point})
    rows.append({"metric": P + "mde_ri_bracket_lo", "value": ri_lo})
    rows.append({"metric": P + "mde_ri_bracket_hi", "value": ri_hi})
    rows.append({"metric": P + "mde_ri_bracket_closed", "value": ri_closed})
    rows.append({"metric": P + "ri_sims", "value": 0 if args.no_ri else args.ri_sims})
    rows.append({"metric": P + "ri_draws", "value": 0 if args.no_ri else args.ri_draws})

    # ---- the stratum's go / no-go, against both named reference effects ----
    best = min([v for v in headline.values() if v and np.isfinite(v)], default=np.nan)
    worst_p = max([v for v in headline.values() if v and np.isfinite(v)], default=np.nan)
    rows.append({"metric": P + "mde_best_profile", "value": best})
    rows.append({"metric": P + "mde_worst_profile", "value": worst_p})
    for rname, rv in REFERENCE_EFFECTS.items():
        rows.append({"metric": P + f"mde_over_reference.{rname}",
                     "value": round(float(worst_p / rv), 3) if np.isfinite(worst_p) else "nan"})
    ref = REFERENCE_EFFECTS[REFERENCE_PRIMARY]
    verdict = ("ADEQUATE" if np.isfinite(worst_p) and worst_p <= ref
               else "UNDERPOWERED" if np.isfinite(worst_p) else "NOT_ESTIMABLE")
    stratum_verdicts[name] = verdict
    rows.append({"metric": P + "POWER_VERDICT", "value": verdict})
    print(f"  {name}: MDE {best:.6f}..{worst_p:.6f} across profiles against the "
          f"{REFERENCE_PRIMARY} reference {ref:.5f} — {verdict}")

# ===========================================================================
# Verdict
# ===========================================================================
# A sentinel that no stratum ever lowered means no leg ran at all, which is the
# opposite of "enough". Collapse it to zero before the floor is applied, or
# `--strata` naming nothing would print COMPLETE on an empty run -- the same
# shape as the defect E1.6 names.
n_null_done_min = 0 if n_null_done_min == 10 ** 9 else n_null_done_min
n_scan_done_min = 0 if n_scan_done_min == 10 ** 9 else n_scan_done_min
enough = (n_null_done_min >= MIN_SIMS and n_scan_done_min >= MIN_SIMS)
rows.append({"metric": "n_null_sims_completed_min", "value": int(n_null_done_min)})
rows.append({"metric": "n_scan_sims_completed_min", "value": int(n_scan_done_min)})
real_breaches = [b for b in gate_breaches if "not evaluable" not in b]
if not enough:
    verdict = "UNDETERMINED"
elif real_breaches:
    verdict = "GATE_FAILED"
else:
    verdict = "COMPLETE"
rows.append({"metric": "gate_breaches", "value": "; ".join(gate_breaches) or "none"})
for s, v in stratum_verdicts.items():
    rows.append({"metric": f"POWER_VERDICT.{s}", "value": v})
rows.append({"metric": "VERDICT", "value": verdict})

out = pd.DataFrame(rows)

# A SMALLER RUN MAY NEVER OVERWRITE A LARGER ONE. This is 18's finding D1,
# applied here for the same reason: outputs/tables/ is gitignored, an 8-sim smoke
# test destroyed the 200-sim calibration that discharged Gate C, the run exited 0
# and said nothing about what it had just overwritten. Every run leaves a sidecar
# keyed by its size, so a diagnostic run is never lost either -- it simply cannot
# masquerade as the answer.
main_csv = OUTPUTS_TABLES / "power_analysis.csv"
tag = int(min(n_scan_done_min, n_null_done_min))
out.to_csv(OUTPUTS_TABLES / f"power_analysis_n{tag}.csv", index=False)
prior_n = 0
if main_csv.exists():
    try:
        prior = pd.read_csv(main_csv).set_index("metric")["value"]
        prior_n = int(float(prior.get("n_scan_sims_completed_min", 0)))
    except Exception as e:
        print(f"could not read the existing power artifact ({e}); treating it as absent")
if tag >= prior_n:
    out.to_csv(main_csv, index=False)
    if prior_n:
        print(f"published: {tag} sims replaces the {prior_n}-sim artifact on disk")
else:
    print("=" * 70)
    print(f"REFUSING TO PUBLISH. This run completed {tag} sims; the artifact on "
          f"disk rests on {prior_n}. Its record is in power_analysis_n{tag}.csv.")
    print("=" * 70)

print("\n" + "=" * 70)
print(out.to_string(index=False))
print("=" * 70)

if verdict == "UNDETERMINED":
    print(f"UNDETERMINED — {n_scan_done_min} scan sims and {n_null_done_min} null "
          f"sims completed, {MIN_SIMS} required (E1.6). This is NOT a pass and "
          "NOT an MDE. Re-run at full size.")
    raise SystemExit(2)
if verdict == "GATE_FAILED":
    print("GATE FAILED — the Monte Carlo and noncentrality routes to the same MDE "
          "disagree by more than the tolerance:")
    for b in real_breaches:
        print(f"  {b}")
    print("The usual cause is the clustered vcov misstating sampling variability, "
          "which is the known risk on this data (p = 0.019 clustered against 0.26 "
          "permutation). Check vcov_inflation before trusting any MDE above.")
    raise SystemExit(1)

print("COMPLETE. Read the MDE against the effective episode count beside it, not "
      "the nominal one, and read the Roth slope as the lambda-matched one.")
for s, v in stratum_verdicts.items():
    print(f"  {s}: {v}")
if all(v == "UNDERPOWERED" for v in stratum_verdicts.values()):
    print("\nEvery stratum is UNDERPOWERED against the largest effect this project "
          "has measured. Per EXECUTION_PLAN.md Phase H and REBUILD_PLAN.md:495 that "
          "is a legitimate and pre-committed conclusion, not a failed run: the "
          "confirmatory design cannot deliver a confirmation, and the paper becomes "
          "a measurement-and-design contribution with a precisely bounded null.")
