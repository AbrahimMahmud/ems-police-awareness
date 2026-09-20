"""Core of the stacked episode event study, shared by 17 and 18.

Kept in an importable (non-numeric) module so the synthetic-null calibration in
18 exercises exactly the estimator that 17 runs on real data. Calibrating a
re-implementation would prove nothing.

2026-09-09 REWRITE — five blocking defects, all introduced by the previous
version of this file, all found by the audit and each independently fatal:

  S2/D1  Day -1 was DELETED from the sample rather than made the reference, so
         formulaic omitted the lowest surviving level and every coefficient was
         measured against day -14. EVENT_REFERENCE_DAY was inert.
  S1/E1/L1/X4/D2  placebo_starts walked forward from a uniform anchor and broke
         when a start passed the end date, so only ~11% of draws carried all 30
         episodes and the mean draw carried 16. The null was built from
         half-size designs, inflating its spread and gutting the primary
         p-value. Five of seven auditors found this independently.
  S3/R7  first_week_effect averaged the day 0-7 coefficients: a 1-df linear
         contrast, not the pre-registered joint test. A dip-then-rebound — the
         project's own hypothesised mechanism — averages to zero, so the
         statistic had almost no power against the thing it was written to find.
  S6     vcov="hetero" assumes independence across districts within a day, but
         treatment is citywide and assigned at the date level. This is
         REWORK_PLAN I1 relearned; error bars were roughly 3x too narrow.
  S5/E4  build_stack truncated forward only and then deleted BOTH copies of any
         contested district-day, losing 28% of window district-days and the
         entire first week of 5 of 30 episodes.
"""

from functools import lru_cache
from pathlib import Path

import warnings

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats

from config import EVENT_REFERENCE_DAY, OUTPUTS_TABLES

# A district-day claimed by two episode windows is assigned to the NEARER
# episode rather than deleted. Deleting both copies (the old rule) removed the
# pre-periods of exactly the closest-spaced, highest-attention episodes — the
# ones carrying the most identifying variation — while nearest-assignment keeps
# every day, uses each exactly once, and biases toward no episode.
CLUSTER_VAR = "incident_date"

# An episode contributes only if it retains the reference day and at least one
# post day; otherwise its fixed effect absorbs everything it has.
MIN_POST_DAYS = 1


def build_stack(panel, starts, pre, post, date_col="incident_date"):
    """Stack clean event windows: one row per (episode, district, rel_day).

    Every district-day is used at most once. Contested days go to the episode
    whose start is nearest in absolute event time, so no observation is a
    control for one event while being treated in another (REWORK_PLAN I4)
    without discarding the observation entirely (S5).
    """
    starts = sorted(pd.to_datetime(pd.Series(list(starts))).tolist())
    if not starts:
        return pd.DataFrame()

    frames = []
    for i, s in enumerate(starts):
        lo, hi = s - pd.Timedelta(days=pre), s + pd.Timedelta(days=post)
        w = panel[panel[date_col].between(lo, hi)]
        if w.empty:
            continue
        w = w.copy()
        w["episode"] = i + 1
        w["rel_day"] = (w[date_col] - s).dt.days
        frames.append(w)
    if not frames:
        return pd.DataFrame()

    stack = pd.concat(frames, ignore_index=True)

    # Nearest-episode assignment. Ties (a day exactly between two starts) break
    # on the earlier episode, which is arbitrary but deterministic.
    stack["_d"] = stack["rel_day"].abs()
    stack = (stack.sort_values(["_d", "episode"])
                  .drop_duplicates(["communitydistrict", date_col], keep="first")
                  .drop(columns="_d"))

    # Drop episodes that cannot identify anything: no reference day, or no post
    # period. Keeping them adds fixed effects that absorb their own rows.
    keep = []
    for ep, g in stack.groupby("episode"):
        days = set(g["rel_day"])
        if EVENT_REFERENCE_DAY in days and sum(d >= 0 for d in days) >= MIN_POST_DAYS:
            keep.append(ep)
    stack = stack[stack["episode"].isin(keep)].copy()
    if stack.empty:
        return stack

    stack["ep_cd"] = stack["episode"].astype(str) + "_" + stack["communitydistrict"].astype(str)
    return stack.sort_values(["episode", "communitydistrict", "rel_day"]).reset_index(drop=True)


def episode_day_counts(stack):
    """Episodes contributing at each relative day — report this, don't assume it."""
    return stack.groupby("rel_day")["episode"].nunique()


def _rel_day_coefs(model):
    """Map event-time coefficient names back to integer relative days."""
    out = {}
    for n in model._coefnames:
        n = str(n)
        if "rel_day" not in n:
            continue
        try:
            out[int(float(n.split("::")[1]))] = n
        except (IndexError, ValueError):
            continue
    return out


def fit_event_study(stack, outcome, fe="ep_cd + dow", counts=False,
                    cluster=CLUSTER_VAR, extra=(), offset=True):
    """Fit the event-time model. Returns the pyfixest model, or None.

    Day EVENT_REFERENCE_DAY stays IN the estimation sample and is named as the
    omitted level via `i(rel_day, ref=...)`, so every coefficient reads as the
    change relative to the day before attention rose (S2/D1).

    Standard errors are clustered on the date, because treatment is citywide and
    assigned at the date level (S6).

    `extra` names covariates added to the right-hand side - the B-HEARD exposure
    control (X6) is the one that exists. It is HERE, in the one estimator, rather
    than in a second copy of the formula in the confirmatory script: 30 carried
    its own `fit()` with the control while this function had no way to take one,
    so "17 has B-HEARD in the model" was true of the panel it attached the column
    to and false of the formula it estimated. A covariate that is identically
    zero (B-HEARD on discovery) is dropped by pyfixest as collinear, which is
    what keeps the discovery numbers bit-identical and what
    X.bheard_wired asserts.
    """
    d = stack.dropna(subset=[outcome])
    if d.empty or d["episode"].nunique() < 2 or len(d) < 200:
        return None
    if EVENT_REFERENCE_DAY not in set(d["rel_day"]):
        return None
    missing = [x for x in extra if x not in d.columns]
    if missing:
        raise ValueError(f"fit_event_study: covariate(s) {missing} are not in the "
                         "stack; attach them before estimating rather than dropping "
                         "them silently")
    vcov = {"CRV1": cluster} if cluster and cluster in d.columns else "hetero"
    rhs = f"i(rel_day, ref={EVENT_REFERENCE_DAY})" + "".join(f" + {x}" for x in extra)
    fml = f"{outcome} ~ {rhs} | {fe}"
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = _fit(fml, d, counts, vcov, outcome, offset=offset)
        for w in caught:
            _note_warning(w)
        return model
    except Exception as e:
        _note_fit_failure(outcome, counts, e)
        return None


def _fit(fml, d, counts, vcov, outcome, offset=True):
    try:
        if counts and not offset:
            # RAW count, no offset: the denominator diagnostic of addendum 23.
            # A rate model (offset) shares the share arm's denominator; this one
            # does not, so it can tell a change in demand from a change in the
            # denominator.
            d = d[d[outcome].notna()].copy()
            return pf.fepois(fml, d, vcov=vcov) if not d.empty else None
        if counts:
            # PPML on the count with a log total-calls OFFSET, so a coefficient
            # reads as a proportional change in the rate — the same quantity the
            # share regression targets, without the denominator moving the
            # answer. The offset was documented in 17's header and never
            # existed: counts=True was passed by no caller and fepois was called
            # with no offset at all (findings X5, R8).
            #
            # pyfixest takes the offset as a COLUMN NAME, not an array, so the
            # column has to exist. Passing a Series raises TypeError, which the
            # except below then turned into a silent "not estimable" — the arm
            # would have looked merely unlucky rather than broken.
            #
            # `offset` may name the denominator column (the cancelled-inclusive
            # count arm offsets on the cancelled-inclusive total, addendum 30);
            # True means the primary denominator, total_calls.
            total_col = offset if isinstance(offset, str) else "total_calls"
            d = d[(d[total_col] > 0) & d[outcome].notna()].copy()
            if d.empty:
                return None
            d["log_total"] = np.log(d[total_col])
            return pf.fepois(fml, d, vcov=vcov, offset="log_total")
        return pf.feols(fml, d, vcov=vcov)
    except Exception:
        raise


def fit_dose_response(stack, outcome, intensity, fe="ep_cd + dow", counts=False,
                      cluster=CLUSTER_VAR, days=range(0, 8)):
    """Event-time effect scaled by EPISODE INTENSITY, not a binary dummy.

    FINDING D6. The binary design treats every episode identically, and they are
    not identical: peak CAI-D runs 1.40 to 12.67 across the 28 discovery episodes
    (a 9x range) and 0.57 to 12.69 across all 75 (22x), with quartiles at 1.86,
    2.86 and 3.42. A handful of enormous episodes sit beside many marginal ones
    and every one contributes the same indicator. That is information the design
    throws away, and it is exactly the information a dose-response reading needs.

    It also bears on T6. Treatment precision is worse in quiet stretches - the two
    attention indicators correlate 0.90 in 2020 against 0.14 in 2024 - so quiet
    episodes carry a noisier treatment. Averaging them in with a binary dummy
    hides that; scaling by intensity makes it visible.

    Specification: the day 0..7 indicators are interacted with the episode's
    standardised peak intensity, so the coefficient reads as the effect per
    standard deviation of episode size. `intensity` maps episode id -> peak, and
    is standardised HERE rather than upstream, so the scale is a property of the
    episodes actually in this stack rather than of whatever list produced them.

    SECONDARY, and pre-specified as such. The binary arm remains primary because
    it was pre-registered; this is disclosed as an addition made while still
    blind to every confirmation outcome.
    """
    d = stack.dropna(subset=[outcome]).copy()
    if d.empty or d["episode"].nunique() < 3:
        return None
    if EVENT_REFERENCE_DAY not in set(d["rel_day"]):
        return None
    # Intensity is keyed on the episode's START DATE, derived from the stack
    # itself, NOT on the episode number. build_stack numbers episodes before it
    # drops the ones that cannot identify anything, so a caller mapping by
    # position gets a silent off-by-n the moment any episode is dropped. The
    # start date is recoverable from the stack (incident_date - rel_day) and
    # cannot drift.
    d["_start"] = d["incident_date"] - pd.to_timedelta(d["rel_day"], unit="D")
    key = {pd.Timestamp(k).normalize(): v for k, v in intensity.items()}
    d["_dose"] = d["_start"].dt.normalize().map(key)
    if d["_dose"].isna().any():
        missing = sorted(d.loc[d["_dose"].isna(), "_start"].dt.date.unique())[:3]
        raise ValueError(f"no intensity for episode start(s) {missing}; refusing "
                         "to estimate a dose model on a partial mapping")
    sd = d["_dose"].std(ddof=0)
    if not sd or not np.isfinite(sd):
        return None
    d["_dose"] = (d["_dose"] - d["_dose"].mean()) / sd
    d["_post"] = d["rel_day"].isin(list(days)).astype(float)
    d["_post_dose"] = d["_post"] * d["_dose"]

    vcov = {"CRV1": cluster} if cluster and cluster in d.columns else "hetero"
    # _dose alone is absorbed by the episode x district fixed effect, so only the
    # interaction and the post indicator are identified.
    fml = f"{outcome} ~ _post + _post_dose | {fe}"
    try:
        if counts:
            d = d[(d["total_calls"] > 0) & d[outcome].notna()].copy()
            if d.empty:
                return None
            d["log_total"] = np.log(d["total_calls"])
            return pf.fepois(fml, d, vcov=vcov, offset="log_total")
        return pf.feols(fml, d, vcov=vcov)
    except Exception as e:
        _note_fit_failure(f"{outcome}:dose", counts, e)
        return None


def count_outcome(share_outcome):
    """The count column behind a share column: edp_share -> edp,
    edp_share_incl_cancelled -> edp_incl_cancelled, edp_ex_edpm_share -> edp_ex_edpm."""
    return share_outcome.replace("_share", "", 1) if "_share" in share_outcome else share_outcome


# Collinear event-time dummies get dropped when windows are truncated by an
# adjacent episode. If the statistic silently used whatever survived, its
# composition would vary across randomization draws and the null distribution
# would not correspond to the observed statistic. So require most of the week.
MIN_FIRST_WEEK_DAYS = 6

# Fit failures are EXPECTED during randomization inference — a placebo draw can
# produce a degenerate design — so they cannot raise. But a systematic failure
# (a bad formula, a wrong argument type) then looks identical to bad luck, which
# is how the counts arm could be broken and merely appear "not estimable". So
# each distinct failure is reported once, and never silently.
_SEEN_FAILURES = set()


_SEEN_WARNINGS = set()


def _note_warning(w):
    """Print each distinct fit warning ONCE per process.

    pyfixest warns on every fit that drops a collinear column, and the B-HEARD
    control is identically zero on discovery, so a 500-draw run would print the
    same four lines a thousand times and bury anything that mattered. Shown
    once, never suppressed: a collinearity message that stopped appearing would
    hide a genuinely degenerate specification.
    """
    text = " ".join(str(w.message).split())
    key = (w.category.__name__, text[:120])
    if key in _SEEN_WARNINGS:
        return
    _SEEN_WARNINGS.add(key)
    print(f"[event_study] {w.category.__name__} (shown once): {text[:200]}")


def _note_fit_failure(outcome, counts, exc):
    key = (outcome, bool(counts), type(exc).__name__, str(exc)[:80])
    if key in _SEEN_FAILURES:
        return
    _SEEN_FAILURES.add(key)
    arm = "PPML counts" if counts else "OLS share"
    print(f"[event_study] {arm} fit failed for {outcome}: "
          f"{type(exc).__name__}: {str(exc)[:160]}")


def first_week_effect(stack, outcome, fe="ep_cd + dow", counts=False, days=range(0, 8),
                      min_days=MIN_FIRST_WEEK_DAYS, return_n=False, cluster=CLUSTER_VAR,
                      extra=(), offset=True):
    """Test statistic for H1: the JOINT Wald statistic on the day 0..7 coefficients.

    H1 is that attention changes first-week demand — a joint claim that the
    eight coefficients are not all zero, two-sided, per the reframe ratified at
    Gate C 6.1. The previous implementation returned their MEAN, which is a
    single linear contrast: a dip followed by a rebound, which is precisely the
    mechanism this project hypothesises, averages to approximately zero and was
    therefore nearly invisible to the old statistic (S3/R7).

    Returns the chi-square statistic, which is non-negative, so randomization
    inference compares it one-sided in the statistic while remaining two-sided
    in the effect. Use `first_week_mean` for the reportable effect size.

    Returns None when fewer than `min_days` of the window are identified, so a
    draw with a degenerate design is discarded rather than contributing a
    statistic built from a different set of days than the observed one.
    """
    m = fit_event_study(stack, outcome, fe=fe, counts=counts, cluster=cluster, extra=extra,
                        offset=offset)
    if m is None:
        return (None, 0) if return_n else None
    names = _rel_day_coefs(m)
    wanted = [names[k] for k in days if k in names]
    if len(wanted) < min_days:
        return (None, len(wanted)) if return_n else None
    stat = _joint_stat(m, wanted)
    return (stat, len(wanted)) if return_n else stat


def _joint_stat(model, wanted):
    """Wald chi-square that every coefficient in `wanted` is zero."""
    names = [str(n) for n in model._coefnames]
    b = np.asarray(model.coef().values, dtype=float)
    V = np.asarray(model._vcov, dtype=float)
    idx = [names.index(str(w)) for w in wanted]
    R = np.zeros((len(idx), len(names)))
    for r, j in enumerate(idx):
        R[r, j] = 1.0
    Rb, M = R @ b, R @ V @ R.T
    try:
        return float(Rb @ np.linalg.solve(M, Rb))
    except np.linalg.LinAlgError:
        return float(Rb @ np.linalg.pinv(M) @ Rb)


def joint_p(model, wanted):
    """Asymptotic p-value for the joint test. Reported beside the RI p, never instead."""
    stat = _joint_stat(model, wanted)
    return stat, float(stats.chi2.sf(stat, len(wanted)))


def first_week_mean(stack, outcome, fe="ep_cd + dow", counts=False, days=range(0, 8),
                    cluster=CLUSTER_VAR, extra=(), offset=True, return_se=False,
                    return_path=False):
    """Reportable effect size: the mean day 0..7 coefficient. NOT the test statistic.

    With `return_se=True` returns `(mean, se)`, where `se` is the asymptotic
    date-clustered standard error of that mean — sqrt(a'Va) with a = 1/k on the
    k first-week coefficients. Addendum 23.2 reads a rejection's direction off
    the sign of this mean and calls it inconsistent when the mean is within one
    standard error of zero in either arm, so the sealed script writes both.
    With `return_path=True` (implies the SE) returns `(mean, se, path)` where
    `path` is `{day: (coef, se)}` for every requested day the fit identified —
    the day-by-day path 23.2 requires a direction-less rejection to be reported
    with, written into the sealed table so no second read is needed (addendum 30).
    """
    m = fit_event_study(stack, outcome, fe=fe, counts=counts, cluster=cluster, extra=extra,
                        offset=offset)
    none = (None, None, None) if return_path else (None, None) if return_se else None
    if m is None:
        return none
    names = _rel_day_coefs(m)
    wanted = [names[k] for k in days if k in names]
    if not wanted:
        return none
    mean = float(m.coef().loc[wanted].mean())
    if not return_se and not return_path:
        return mean
    allnames = [str(n) for n in m._coefnames]
    V = np.asarray(m._vcov, dtype=float)
    a = np.zeros(len(allnames))
    for w in wanted:
        a[allnames.index(str(w))] = 1.0 / len(wanted)
    se = float(np.sqrt(max(float(a @ V @ a), 0.0)))
    if not return_path:
        return mean, se
    coefs, ses = m.coef(), m.se()
    path = {int(k): (float(coefs.loc[names[k]]), float(ses.loc[names[k]])) for k in days if k in names}
    return mean, se, path


def placebo_starts(rng, real_starts, lo, hi, pre, post):
    """Draw placebo episode dates that preserve the real episodes' spacing.

    Preserving spacing matters: attention episodes cluster, and a null built from
    uniformly scattered dates would understate how often clustered draws produce
    a large statistic by chance.

    The anchor is drawn so that the WHOLE shifted sequence fits inside the
    window, and the draw is rejected outright if it does not. The previous
    version walked forward and stopped early when a start passed the end date,
    so the null carried about half the real episode count (S1/E1/L1/X4/D2).
    """
    real = sorted(pd.to_datetime(pd.Series(list(real_starts))).tolist())
    if len(real) < 2:
        return []
    gaps = np.diff([d.toordinal() for d in real])
    span = int(gaps.sum())                       # first start to last start
    earliest = lo + pd.Timedelta(days=pre + 1)
    latest = hi - pd.Timedelta(days=post + 1)
    room = (latest - earliest).days - span       # slack for the whole sequence
    if room < 0:
        return []                                # sequence cannot fit; caller discards

    anchor = earliest + pd.Timedelta(days=int(rng.integers(0, room + 1)))
    out = [anchor]
    for g in rng.permutation(gaps):
        out.append(out[-1] + pd.Timedelta(days=int(g)))

    # Permuting gaps cannot change the total span, so this always holds; assert
    # rather than trust, because a silent short draw is the defect being fixed.
    if out[-1] > latest or len(out) != len(real):
        return []
    return out


@lru_cache(maxsize=64)
def _admissible_days_cached(windows, pre, post, first_week=None):
    days = pd.DatetimeIndex([])
    for lo, hi in windows:
        lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)
        if first_week is None:
            a = lo + pd.Timedelta(days=pre + 1)
            b = hi - pd.Timedelta(days=post + 1)
        else:
            # FIRST-WEEK containment (addendum 17, 24): a start is admissible when
            # day -1 and days 0..first_week lie inside the window, exactly the rule
            # that decides which REAL episodes a stratum keeps. Tails may truncate.
            a = lo + pd.Timedelta(days=1)
            b = hi - pd.Timedelta(days=first_week)
        if b >= a:
            days = days.union(pd.date_range(a, b, freq="D"))
    return days.sort_values()


def admissible_days(windows, pre, post, first_week=None):
    """Every day a placebo episode may start on, across one or more windows.

    With `first_week` given, admissibility is first-week containment (day -1
    through day +first_week inside the window) rather than the full pre/post
    window; see placebo_starts_circular and addendum 24.

    A start needs `pre` days before it and `post` after, so each window
    contributes only its interior. Returned sorted, as a DatetimeIndex, so a
    position in it is a well-defined index.

    CACHED, because the within-block shift (N3) calls this once PER WINDOW PER
    DRAW rather than once per run, and rebuilding a 520-day DatetimeIndex 200
    times a simulation made the calibration 3.6x slower — 1 sim/minute against
    3.6, which is 16 hours for one stratum instead of 4.6. The windows are a
    property of the stratum and never change inside a run, so the recomputation
    bought nothing. Keyed on a tuple so the arguments are hashable; callers
    passing a list still work.
    """
    key = tuple((str(lo), str(hi)) for lo, hi in windows)
    return _admissible_days_cached(key, pre, post, first_week)


def placebo_starts_circular(rng, real_starts, windows, pre, post):
    """Placebo dates by circular shift over admissible days (finding P1).

    WHY A SECOND SCHEME EXISTS. `placebo_starts` draws one anchor and slides the
    whole real sequence inside a single contiguous window, rejecting the draw if
    the sequence does not fit. On the clean confirmation stratum that is not
    merely tight, it is UNDEFINED: C1 is two windows sitting either side of the
    entire discovery period, so there is no single span to slide within, and
    40.9% of anchor draws land outside C1's own windows. Its 2021 block alone
    holds 5 episodes spanning 139 days in a 151-day window — 120 usable days
    against 139 required, slack of minus 19. Every draw is rejected and the
    p-value returns NaN after the whole budget is spent.

    HOW THIS ONE WORKS. Take the admissible days across ALL windows, in order,
    as one sequence. Each real start occupies a position in that sequence. A
    single shift is drawn uniformly and every position moves by it, wrapping at
    the end. Every draw is admissible by construction, so nothing is rejected and
    the null has the full episode count on every draw.

    WHAT IT PRESERVES, AND WHAT IT DOES NOT. It preserves each episode's position
    RELATIVE TO THE OTHERS measured in admissible days — clustering survives,
    which is the property that matters, because a null of uniformly scattered
    dates would understate how often clustered draws produce a large statistic by
    chance. It does NOT preserve calendar gaps across a window boundary: two
    episodes either side of the seam are adjacent in index space while being
    years apart in calendar time. That is a real difference from the anchor-shift
    null and it is why this is a DIFFERENT NULL, not a patch to the same one. A
    verdict calibrated under one does not transfer to the other, which is what
    S.ri_scheme_certified exists to enforce.

    A real start that is not itself admissible — too close to a window edge — is
    snapped to the nearest admissible day and the count of snaps is returned, so
    a caller can refuse rather than quietly estimate on a shifted design.
    """
    days = admissible_days(windows, pre, post)
    real = sorted(pd.to_datetime(pd.Series(list(real_starts))).tolist())
    if len(days) == 0 or len(real) < 2:
        return [], 0
    # WITHIN EACH WINDOW, NOT ACROSS ALL OF THEM (finding N3).
    #
    # The first version of this concatenated every window's admissible days into
    # one sequence and slid through it, which let a shift carry episodes across
    # the seam between windows. That sounds like a detail about calendar gaps —
    # the docstring above said so — and it is not: it changes HOW MANY EPISODES
    # LAND IN EACH WINDOW, and the placebo design stops resembling the real one.
    #
    # Measured on C1, which really has 10 episodes in 2015-16 and 5 in 2021:
    # block 1 is 520 of the 641 admissible days, so a uniform shift through the
    # concatenation put a MEAN OF 12.1 episodes there, its modal draw was 13,
    # and it reproduced the real 10/5 split on 12.4% OF DRAWS. Different
    # episodes per window means a different effective sample and a different
    # fixed-effect structure, so the null was not a null of this design, and
    # C1's p-values were correspondingly non-uniform — the one stratum of three
    # that could not pass its own uniformity test comfortably.
    #
    # Shifting inside each window fixes it by construction: the count per window
    # is preserved on EVERY draw, clustering within a window survives, and there
    # is no seam to cross. Under first-week containment (CIRCULAR_FIRST_WEEK,
    # addendum 24) C1 has 542 and 143 admissible days, so 542 x 143 = 77,506
    # distinct placebo designs remain against the 2,000 draws the design calls
    # for (the 520 x 121 = 62,920 quoted before 2026-09-20 counted full-post
    # containment). On a single-window stratum the block shift and the anchor
    # shift are different draws (addendum 27): discovery and C2 keep the latter.
    # Membership is decided by the WINDOW'S CALENDAR BOUNDS, not by its
    # admissible days. The two differ by `pre` at the start and `post` at the
    # end, and finding P2 is precisely that two of C1's fifteen episodes sit in
    # that margin: 2021-01-05, whose pre-period reaches into discovery, and
    # 2021-05-24, whose post-period crosses the B-HEARD launch. Keying on
    # admissible days leaves those two belonging to no block, which sent them to
    # a fallback that scattered them across the whole stratum and made the split
    # WORSE than the seam-crossing version it replaced — 3.9% of draws against
    # 12.4%. Measured, not reasoned about; the first version of this fix was
    # wrong and the test said so.
    # ADMISSIBILITY IS FIRST-WEEK CONTAINMENT, the same rule that keeps a real
    # episode in the stratum (addendum 17). Keyed on the full +/-14 window, the two
    # C1 episodes whose tails leave the 2021 block were snapped to the block's
    # first and last admissible day, and a circular shift of positions 0 and
    # N-1 puts them on CONSECUTIVE days: measured 2026-09-13, 397 of 400 C1
    # placebo draws carried two episodes one day apart against a real minimum
    # gap of 16, and build_stack then hands nearly all of one to the other. The
    # null was drawing designs unlike the real one (CP2 audit; addendum 24).
    # Under first-week admissibility every kept episode is on an admissible day
    # and nothing snaps; the snapping branch below stays as a guard and its
    # count is returned so a caller can refuse a draw that used it.
    blocks = []
    for w in windows:
        adm = admissible_days([w], pre, post, first_week=CIRCULAR_FIRST_WEEK)
        if len(adm):
            blocks.append((pd.Timestamp(w[0]), pd.Timestamp(w[1]), adm))
    if not blocks:
        return [], 0

    out, snapped = [], 0
    for lo_w, hi_w, b in blocks:
        mine = [d for d in real if lo_w <= d <= hi_w]
        # An episode inside the window's calendar span but not on an admissible
        # day is snapped to the nearest one, and counted, exactly as before.
        pos = []
        for d in mine:
            i = b.searchsorted(d)
            if i >= len(b) or b[i] != d:
                cands = [j for j in (i - 1, i) if 0 <= j < len(b)]
                i = min(cands, key=lambda j: (abs((b[j] - d).days), j))
                snapped += 1
            pos.append(int(i))
        if not pos:
            continue
        shift = int(rng.integers(0, len(b)))
        out.extend(b[(i + shift) % len(b)] for i in pos)

    # Every episode a stratum contains lies inside one of its windows by
    # construction — that is what stratum_episodes selected on — so this should
    # place all of them. If it ever does not, the draw is SHORT, and a draw
    # carrying fewer episodes than the real design is the exact defect
    # placebo_starts rejects draws to avoid. Refuse rather than return it.
    if len(out) != len(real):
        raise ValueError(
            f"within-block shift placed {len(out)} of {len(real)} episodes; an "
            "episode lies outside every window of its own stratum, which means "
            "the stratum and the episode list disagree")
    return sorted(out), snapped


def stratum_episodes(episode_starts, windows, pre, post, first_week=7):
    """Which episodes a stratum can actually test, and what each one loses.

    FINDING P2. A stratum is a set of calendar windows, and an episode near a
    window's edge does not fit inside it. Two of C1's fifteen do not, and each
    fails differently:

      2021-01-05 (Dolal Idd) — its pre-period reaches back to 2020-12-22, which
        is INSIDE THE DISCOVERY WINDOW. Its baseline would come from data already
        explored while its post-period is unexamined, mixing the two samples
        inside one event window.

      2021-05-24 (Daunte Wright; Adam Toledo) — its post-period runs to
        2021-06-07, CROSSING THE B-HEARD LAUNCH on 2021-06-01, so 7 of its post
        days are exposed inside the stratum defined as unexposed.

    THE RULE, and why it is not the obvious one. Requiring the full +/-14 window
    to fit would drop both, costing 2 of C1's 15 episodes — 13% of the smallest
    and most valuable stratum — and one of them is Daunte Wright. Measured, that
    is not necessary: the statistic this design reports is the joint test over day
    -1 through day +7, and for BOTH episodes that span lies entirely inside C1.
    Only the tails fall outside, 10 days and 7 days of 29.

    So an episode is kept when its FIRST-WEEK span fits, and the days beyond it
    are truncated and counted. That keeps the primary test exact and confines the
    loss to the longer sensitivity windows, where it is reported rather than
    absorbed. An episode whose first week does not fit is dropped with its reason.

    Returns (kept, dropped) where each is a list of dicts, so the decision is an
    artifact rather than a filter nobody can inspect.
    """
    wins = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in windows]

    def inside(d):
        return any(a <= d <= b for a, b in wins)

    def inside_one(days):
        # The first week must lie inside ONE window. The pooled stratum's C1b
        # and C2 windows are adjacent in the calendar (2021-05-31 | 2021-06-01),
        # so a union test would keep an episode whose first week straddles the
        # seam while the within-block drawer has no block to place it in — the
        # P13 snap re-created at the seam (third CP2 audit pass, 2026-09-20).
        return any(all(a <= d <= b for d in days) for a, b in wins)

    kept, dropped = [], []
    for s0 in sorted(pd.to_datetime(pd.Series(list(episode_starts))).tolist()):
        if not any(a <= s0 <= b for a, b in wins):
            continue
        ref = s0 - pd.Timedelta(days=1)
        fw_end = s0 + pd.Timedelta(days=first_week)
        fw = pd.date_range(ref, fw_end, freq="D")
        full = pd.date_range(s0 - pd.Timedelta(days=pre),
                             s0 + pd.Timedelta(days=post), freq="D")
        lost = int(sum(1 for d in full if not inside(d)))
        if inside_one(fw):
            kept.append({"start": s0, "days_outside_full_window": lost,
                         "full_window_days": len(full)})
        else:
            missing = [d for d in fw if not inside(d)]
            dropped.append({"start": s0, "days_outside_full_window": lost,
                            "reason": ((f"day -1..+{first_week} is not inside the stratum: "
                                        f"{len(missing)} of {len(fw)} first-week days fall "
                                        f"outside, first {missing[0].date()}") if missing else
                                       f"day -1..+{first_week} straddles a seam between two of the "
                                       "stratum's windows; no single block contains it")})
    return kept, dropped


class Uncalibrated(Exception):
    """The null behind a p-value about to be reported is not certified."""


def calibration_file(stratum):
    """Artifact holding the calibration for one stratum.

    Discovery keeps the historical name so every existing reader still finds it.
    """
    return OUTPUTS_TABLES / ("null_calibration.csv" if stratum == "discovery"
                             else f"null_calibration_{stratum}.csv")


def require_calibrated(stratum):
    """Return the calibration for `stratum`, or refuse.

    ONE implementation, because there were nearly three. A calibration certifies
    one sample geometry and one draw scheme, so "is the null certified" is a
    question about a STRATUM and cannot be answered by a filename fixed at
    import time — and both existing answers got that wrong in different ways:

      17_stacked_event_study.py, the primary estimator, never read a calibration
      at all. It would have reported randomization p-values with nothing
      checking that the null producing them had passed its own test. Discovery
      happens to be CALIBRATED, so the numbers would have been sound and the
      absence invisible — which is precisely the pattern already closed for
      PPML (X5), B-HEARD (X6) and the dose arm (D6).

      30_confirmatory_run.py did gate, but on `null_calibration.csv` — DISCOVERY's
      artifact — while writing p-values for C1 and C2. A gate that reads the
      wrong stratum's verdict is not a weaker gate; it is a gate that answers a
      question nobody asked. C1 is the stratum whose scheme is new and whose
      uniformity is marginal, so it is the one a discovery-keyed check could
      never have protected.

    The sim-count re-check is kept from 30: a CALIBRATED verdict below the
    artifact's own `min_sims_required` is how the 12-sim artifact once passed,
    and a gate that cannot fail is not a gate.
    """
    f = calibration_file(stratum)
    if not f.exists():
        raise Uncalibrated(
            f"{f.name} is absent, so the null for stratum {stratum!r} is not "
            f"certified. outputs/tables/ is gitignored, so a fresh clone has "
            f"none — run 18_null_calibration.py --stratum {stratum} "
            "--sims 200 --draws 200 first.")
    cal = pd.read_csv(f).set_index("metric")["value"]
    verdict = str(cal.get("VERDICT", "MISSING"))
    if verdict != "CALIBRATED":
        raise Uncalibrated(
            f"{f.name} reads VERDICT={verdict!r} for stratum {stratum!r}. An "
            "uncalibrated randomization p-value is not a weak p-value — it has "
            "no interpretation at all (GATE_C_MEMO.md 6.3).")
    n = int(float(cal.get("n_sims_completed", 0)))
    need = int(float(cal.get("min_sims_required", 200)))
    if n < need:
        raise Uncalibrated(
            f"{f.name} says CALIBRATED on {n} sims against its own minimum of "
            f"{need}. That combination is how the 12-sim artifact passed; treat "
            "it as broken and re-run 18.")
    # The scheme the artifact certifies must be the scheme that will be drawn.
    # Recorded here so the caller's log carries it and a reader can see which
    # null the p-values below rest on.
    print(f"[calibration] {stratum}: CALIBRATED on {n} sims, scheme "
          f"{cal.get('draw_scheme', 'unrecorded')}, geometry "
          f"{cal.get('sample_geometry', 'unrecorded')}, rejection "
          f"{cal.get('empirical_rejection_rate', '?')}, KS p "
          f"{cal.get('ks_p_uniform', '?')}")
    return cal


def design_fingerprint(design):
    """sha256 of a JSON-serialised design dict, sorted keys, so two runs agree
    on identity iff they agree on every field."""
    import hashlib
    import json
    return hashlib.sha256(json.dumps(design, sort_keys=True, default=str).encode()).hexdigest()


def frame_hash(frame, columns):
    """Order-independent 64-bit hash of the named columns' VALUES.

    Summing per-row hashes is commutative, so the same rows in any order give
    the same number; a rebuilt panel with one value changed gives a different
    one. It says nothing about what the values are, which is why it can be
    written into a sidecar beside a confirmation-window ledger.
    """
    cols = [c for c in columns if c in frame.columns]
    h = pd.util.hash_pandas_object(frame[cols], index=False).to_numpy(dtype="uint64")
    return int(h.sum(dtype="uint64"))


def open_ledger(path, design, header):
    """Open a checkpoint ledger whose IDENTITY is verified, not assumed.

    A ledger banks results keyed by index so a run can resume. That is only
    correct if the banked results were produced by the SAME design: the same
    panel values, episode dates, windows, scheme, estimator and seed root. The
    first versions of both ledgers in this project (finding N4 for the
    calibration, N6 for randomization inference) keyed the file on a name alone
    - stratum and draw count, or outcome and window - so a ledger left behind by
    an earlier panel or episode list would be resumed as if nothing had changed,
    pairing an observed statistic from the new design with null draws from the
    old one. Nothing would have said so; the p-value would simply have been
    wrong.

    So every ledger carries a sidecar `<name>.meta.json` holding a fingerprint
    of the design that produced it, written when the ledger is created. On
    resume the fingerprint must match. If it does not - or the ledger has no
    sidecar, or cannot be parsed - the file is QUARANTINED under a name that
    says why (`.stale-<fp8>`, `.unverified`, `.corrupt`) and a fresh ledger is
    started. Compute is lost; a pooled null is never produced. Adopting a
    sidecar-less ledger is a deliberate act done by the owning script, never a
    default here.

    Returns (banked_rows, meta_path). `banked_rows` is the parsed DataFrame of
    an identity-verified ledger, or an empty frame.
    """
    import json
    from datetime import datetime, timezone
    path = Path(path)
    meta = path.with_suffix(".meta.json")
    fp = design_fingerprint(design)
    banked = pd.DataFrame(columns=header)

    def quarantine(reason):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = path.with_name(f"{path.stem}.{reason}-{stamp}{path.suffix}")
        path.rename(dest)
        if meta.exists():
            meta.rename(meta.with_name(f"{meta.stem}.{reason}-{stamp}{meta.suffix}"))
        print(f"[ledger] {path.name}: {reason.upper()} - moved aside to {dest.name}; "
              "starting a fresh ledger. Nothing from it is pooled with this run.")

    if path.exists():
        reason = None
        if not meta.exists():
            reason = "unverified"
        else:
            try:
                recorded = json.loads(meta.read_text()).get("fingerprint")
            except Exception:
                recorded = None
            if recorded != fp:
                reason = f"stale-{str(recorded or 'none')[:8]}"
        if reason is None:
            try:
                # Field counts are checked line by line BEFORE pandas sees the
                # file: given a header of two names and a row of three fields,
                # read_csv quietly promotes the extra field to an index and
                # returns a well-formed frame - the partial-write corruption a
                # killed run leaves behind, parsed as if it were data.
                lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
                if not lines or lines[0].split(",") != list(header):
                    raise ValueError(f"header {lines[:1]} != {list(header)}")
                bad = [i for i, ln in enumerate(lines[1:], 2)
                       if len(ln.split(",")) != len(header)]
                if bad:
                    raise ValueError(f"{len(bad)} row(s) with the wrong field count, "
                                     f"first at line {bad[0]}")
                banked = pd.read_csv(path)
                if list(banked.columns) != list(header):
                    raise ValueError(f"columns {list(banked.columns)} != {list(header)}")
                for c in header[1:]:
                    pd.to_numeric(banked[c], errors="raise")
            except Exception as e:
                print(f"[ledger] {path.name} unreadable ({type(e).__name__}: {e})")
                reason = "corrupt"
                banked = pd.DataFrame(columns=header)
        if reason is not None:
            quarantine(reason)

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(",".join(header) + "\n")
        meta.write_text(json.dumps({
            "fingerprint": fp,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "design": design,
        }, indent=1, sort_keys=True, default=str))
    return banked, meta


def adopt_ledger(path, design):
    """Write the identity sidecar for a ledger that predates sidecars.

    DELIBERATE, and only for a ledger the caller knows was produced by exactly
    this design. The alternative - silently trusting any sidecar-less ledger -
    is the defect open_ledger exists to remove, so this is a separate call that
    a script exposes behind an explicit flag and prints when it runs.
    """
    import json
    from datetime import datetime, timezone
    path = Path(path)
    meta = path.with_suffix(".meta.json")
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist; nothing to adopt")
    if meta.exists():
        raise FileExistsError(f"{meta} already exists; refusing to overwrite an identity")
    pd.read_csv(path)                       # must at least parse
    meta.write_text(json.dumps({
        "fingerprint": design_fingerprint(design),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adopted": True,
        "design": design,
    }, indent=1, sort_keys=True, default=str))
    print(f"[ledger] ADOPTED {path.name}: identity written to {meta.name} from the "
          "current design, on the caller's assertion that this ledger was produced by it")
    return meta


# The scheme NAME is the certificate's subject (finding N3), so it changes when
# the null changes. "_fw7": admissible days by first-week containment (addendum
# 24) rather than by the full window, which snapped edge episodes.
CIRCULAR_FIRST_WEEK = 7
CIRCULAR_SCHEME = f"circular_within_block_fw{CIRCULAR_FIRST_WEEK}"


def draw_scheme_for(windows, real_starts, pre, post):
    """Which draw scheme a stratum requires, and why. Never guessed at runtime.

    Returns (scheme, reason). `anchor_shift` only when there is ONE window and
    the real sequence actually fits inside it; `circular` otherwise. The reason
    is carried into the artifact so a reader can see what was used and a check
    can compare it against what the calibration certified.
    """
    windows = list(windows)
    real = sorted(pd.to_datetime(pd.Series(list(real_starts))).tolist())
    if len(real) < 2:
        return "none", f"{len(real)} episode(s): no permutation null is defined"
    if len(windows) > 1:
        # NAMED "circular_within_block", not "circular". The scheme changed in a
        # way that changes the null (finding N3), so the name has to change too
        # — otherwise a calibration certifying the seam-crossing version would
        # go on satisfying S.ri_scheme_certified for a different null. The name
        # IS the certificate's subject.
        return CIRCULAR_SCHEME, (
            f"{len(windows)} disjoint windows: an anchor shift has no single span "
            "to slide within, and a shift across the concatenation would not "
            "preserve how many episodes fall in each window")
    lo, hi = (pd.Timestamp(x) for x in windows[0])
    span = (real[-1] - real[0]).days
    room = ((hi - pd.Timedelta(days=post + 1))
            - (lo + pd.Timedelta(days=pre + 1))).days - span
    if room < 0:
        # One window, so within-block and across-block are the same operation;
        # the name still records which implementation drew the placebos.
        return CIRCULAR_SCHEME, (
            f"one window, but the sequence spans {span}d against "
            f"{span + room}d usable: slack {room}")
    return "anchor_shift", f"one window with {room}d of slack for a {span}d sequence"


def randomization_p(panel, real_starts, outcome, pre, post, draws, rng,
                    fe="ep_cd + dow", counts=False, date_col="incident_date",
                    cluster=CLUSTER_VAR, windows=None, ledger=None, seed=None,
                    extra=(), offset=True, draw_post=None):
    """Episode-level randomization inference. Returns (observed, p, null draws).

    `draw_post` (default: `post`) is the post window the PLACEBO DRAWER uses for
    admissibility and anchor slack, while `post` is the estimation window. The
    sealed run's 28- and 60-day window sensitivities pass draw_post=14 so their
    null is the certified 14-day geometry — the same reference set, the same
    admissible anchors, the observed design inside its own support — and only
    the estimation window lengthens (third CP2 audit pass, 2026-09-20).

    The statistic is the joint chi-square, which is non-negative and increasing
    in departure from the null, so p is the share of placebo statistics at least
    as large as the observed one.

    `windows` names the stratum's calendar windows and selects the draw scheme
    through `draw_scheme_for`. Leave it None and the panel's own date range is
    treated as one window, which is the historical behaviour and is correct for
    discovery. It is NOT correct for a stratum made of disjoint windows: taking
    min..max there spans the gap between them, so an anchor could be drawn inside
    a period the stratum excludes. On C1 that is 40.9% of draws, and each one is
    then rejected for not fitting, which is how a p-value comes back NaN after
    the whole budget is spent (finding P1).
    """
    obs_stack = build_stack(panel, real_starts, pre, post, date_col)
    obs = first_week_effect(obs_stack, outcome, fe=fe, counts=counts, cluster=cluster, offset=offset,
                            extra=extra)
    if obs is None:
        return None, np.nan, np.array([])
    if windows is None:
        windows = [(panel[date_col].min(), panel[date_col].max())]
    dpost = int(post if draw_post is None else draw_post)
    scheme, _why = draw_scheme_for(windows, real_starts, pre, dpost)
    lo, hi = pd.Timestamp(windows[0][0]), pd.Timestamp(windows[-1][1])

    # RESUMABLE, BECAUSE THIS ENVIRONMENT WILL NOT HOLD A LONG JOB (finding N6).
    #
    # Measured three times in one session: the container restarts every 30-70
    # minutes, and a run that writes only at the end loses everything. A 1000-sim
    # calibration died at 45 minutes and the discovery run's primary estimator
    # died at 33, each having saved nothing. 18_null_calibration.py was given a
    # ledger and survived the same restart untouched; this function was not, and
    # it is where every remaining compute-bound deliverable spends its time.
    #
    # Two things are needed and they are the same thing. Draw i must get the same
    # placebo dates however many draws a run asks for — otherwise a resumed run
    # is not the run it resumed — so the draws are seeded per index from one
    # SeedSequence rather than pulled from a single shared rng. That also removes
    # the dependence on completion order, which is why 18 was seeded this way.
    #
    # `seed` is the root. It defaults to the caller's rng so behaviour is
    # unchanged for callers that pass neither, and a caller wanting resumability
    # passes an explicit root and a ledger path.
    root = seed if seed is not None else int(rng.integers(0, 2**31 - 1))
    seeds = np.random.SeedSequence(root).spawn(int(draws))

    # THE LEDGER IS KEYED TO THE DESIGN, NOT TO A FILENAME. Everything that
    # determines a draw's statistic is in the fingerprint: the panel's values on
    # the columns the estimator reads, the episode dates, the windows and hence
    # the scheme, the estimator's own settings, and the seed root. `draws` is
    # deliberately NOT in it - SeedSequence gives draw i the same seed whatever
    # the total, which is what lets a 500-draw ledger be extended to 2,000. A
    # ledger whose design differs is quarantined by open_ledger, never pooled.
    done = {}
    led = Path(ledger) if ledger else None
    if led is not None:
        design = {
            "kind": "randomization_p", "outcome": outcome, "pre": int(pre),
            "post": int(post), "counts": bool(counts), "fe": fe, "cluster": cluster,
            "extra": list(extra), "scheme": scheme,
            # Only written when it departs from the default, so every ledger
            # fingerprinted before the raw-count diagnostic existed still matches.
            **({"offset": offset} if offset is not True else {}),
            # Only when the drawer's window differs from the estimation window
            # (the sealed run's 28/60-day sensitivities draw on the 14-day geometry).
            **({"draw_post": dpost} if dpost != int(post) else {}),
            "windows": [[str(pd.Timestamp(a).date()), str(pd.Timestamp(b).date())]
                        for a, b in windows],
            "starts": sorted(str(pd.Timestamp(s).date()) for s in real_starts),
            "seed_root": int(root), "panel_rows": int(len(panel)),
            "panel_span": [str(panel[date_col].min().date()),
                           str(panel[date_col].max().date())],
            "panel_hash": frame_hash(panel, [date_col, "communitydistrict", outcome,
                                             "total_calls", *extra]),
        }
        banked, _meta = open_ledger(led, design, ["draw_index", "stat"])
        done = {int(r["draw_index"]): float(r["stat"]) for _, r in banked.iterrows()}
        if done:
            print(f"[RI] {led.name}: resuming {len(done)} banked draw(s), identity verified")

    stats_ = []
    # EXHAUSTIVE DISPATCH, AND NO SILENT DEFAULT.
    #
    # This was `if scheme == "circular": ... else: anchor shift`. Renaming the
    # circular scheme to circular_within_block therefore sent C1 — the stratum
    # that CANNOT use an anchor shift, which is the entire reason the second
    # scheme exists — down the else branch, where every draw was rejected and
    # the p-value came back NaN. An `else` that means "the other scheme" turns
    # every unrecognised name into a silent switch to a different null.
    #
    # So the mapping is explicit and an unknown scheme raises. A draw scheme is
    # the subject of a calibration certificate; guessing at one is not a
    # degraded mode, it is an uncertified p-value with no warning attached.
    # Each drawer takes the DRAW'S OWN rng, not the shared one. Closing over the
    # caller's rng would make draw i depend on how many draws ran before it,
    # which is exactly what stops a resumed run from reproducing the run it
    # resumed.
    # Each drawer returns (starts, snapped): the within-block shift relocates a
    # real start that is not itself an admissible day (finding P2's two edge
    # episodes) and COUNTS the relocations; the anchor shift never does. The
    # count used to be discarded with a `[0]` here, against the drawer's own
    # docstring, so no caller could see that every placebo design differed from
    # the observed one in where two episodes sat. It is now summed and reported.
    DRAWERS = {
        CIRCULAR_SCHEME:
            lambda r: placebo_starts_circular(r, real_starts, windows, pre, dpost),
        "anchor_shift":
            lambda r: (placebo_starts(r, real_starts, lo, hi, pre, dpost), 0),
    }
    if scheme not in DRAWERS:
        raise ValueError(
            f"draw_scheme_for returned {scheme!r}, which randomization_p cannot "
            f"draw. Known schemes: {sorted(DRAWERS)}. Refusing to fall back — a "
            "fallback here silently changes which null the p-value comes from.")
    draw_placebo = DRAWERS[scheme]

    n_real = len(list(real_starts))
    fh = led.open("a") if led is not None else None
    n_new, n_short, n_unfit, snapped_total = 0, 0, 0, 0
    try:
        for i in range(int(draws)):
            if i in done:
                continue                          # already banked by an earlier run
            ps, snapped = draw_placebo(np.random.default_rng(seeds[i]))
            if len(ps) != n_real:
                n_short += 1
                continue                          # never let a short draw in
            b = first_week_effect(build_stack(panel, ps, pre, post, date_col),
                                  outcome, fe=fe, counts=counts, cluster=cluster, offset=offset,
                                  extra=extra)
            if b is None:
                n_unfit += 1
                continue
            done[i] = float(b)
            n_new += 1
            snapped_total += int(snapped)
            if fh is not None:
                # Flushed per draw: a kill costs at most one.
                fh.write(f"{i},{b!r}\n")
                fh.flush()
    finally:
        if fh is not None:
            fh.close()
    if n_short or n_unfit or snapped_total:
        print(f"[RI] {outcome}: {n_new} new draw(s); {n_short} short draw(s) and "
              f"{n_unfit} unfit draw(s) discarded; {snapped_total} episode "
              f"relocation(s) onto an admissible day across the new draws"
              + (f" ({snapped_total / max(n_new, 1):.2f} per draw)" if n_new else ""))
    # Ordered by draw index so the result never depends on which draws a
    # particular run happened to compute.
    stats_ = [done[i] for i in sorted(done)]
    stats_ = np.array(stats_)
    # (1 + k) / (1 + n), NOT k / n.
    #
    # The observed assignment is itself one of the assignments the null admits,
    # so it belongs in both the numerator and the denominator. Leaving it out
    # makes the test anti-conservative exactly where rejection decisions are
    # taken, and it can return p = 0 — which is not a p-value, and which the
    # calibration artifacts were carrying: every stratum had one. Phipson &
    # Smyth (2010) is the standard reference; CP2's own checklist has required
    # this form all along and it was never implemented.
    #
    # Measured on the three committed calibrations, correcting the stored
    # placebo counts: KS uniformity p moves 0.6803 -> 0.7718 on discovery,
    # 0.4502 -> 0.4747 on C2, 0.0736 -> 0.0881 on C1. The rejection rates at
    # alpha = 0.05 do not move at 200 draws. So this is a correctness fix rather
    # than a rescue: C1's non-uniformity is a property of its DRAW SCHEME, not
    # of this formula.
    p = (float((1 + (stats_ >= obs).sum()) / (1 + len(stats_)))
         if len(stats_) else np.nan)
    return obs, p, stats_
