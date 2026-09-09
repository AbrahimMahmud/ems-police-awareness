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

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats

from config import EVENT_REFERENCE_DAY

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
                    cluster=CLUSTER_VAR):
    """Fit the event-time model. Returns the pyfixest model, or None.

    Day EVENT_REFERENCE_DAY stays IN the estimation sample and is named as the
    omitted level via `i(rel_day, ref=...)`, so every coefficient reads as the
    change relative to the day before attention rose (S2/D1).

    Standard errors are clustered on the date, because treatment is citywide and
    assigned at the date level (S6).
    """
    d = stack.dropna(subset=[outcome])
    if d.empty or d["episode"].nunique() < 2 or len(d) < 200:
        return None
    if EVENT_REFERENCE_DAY not in set(d["rel_day"]):
        return None
    vcov = {"CRV1": cluster} if cluster and cluster in d.columns else "hetero"
    fml = f"{outcome} ~ i(rel_day, ref={EVENT_REFERENCE_DAY}) | {fe}"
    try:
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
            d = d[(d["total_calls"] > 0) & d[outcome].notna()].copy()
            if d.empty:
                return None
            d["log_total"] = np.log(d["total_calls"])
            return pf.fepois(fml, d, vcov=vcov, offset="log_total")
        return pf.feols(fml, d, vcov=vcov)
    except Exception as e:
        _note_fit_failure(outcome, counts, e)
        return None


def count_outcome(share_outcome):
    """The count column behind a share column: edp_share -> edp."""
    return share_outcome[:-6] if share_outcome.endswith("_share") else share_outcome


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


def _note_fit_failure(outcome, counts, exc):
    key = (outcome, bool(counts), type(exc).__name__, str(exc)[:80])
    if key in _SEEN_FAILURES:
        return
    _SEEN_FAILURES.add(key)
    arm = "PPML counts" if counts else "OLS share"
    print(f"[event_study] {arm} fit failed for {outcome}: "
          f"{type(exc).__name__}: {str(exc)[:160]}")


def first_week_effect(stack, outcome, fe="ep_cd + dow", counts=False, days=range(0, 8),
                      min_days=MIN_FIRST_WEEK_DAYS, return_n=False, cluster=CLUSTER_VAR):
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
    m = fit_event_study(stack, outcome, fe=fe, counts=counts, cluster=cluster)
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
                    cluster=CLUSTER_VAR):
    """Reportable effect size: the mean day 0..7 coefficient. NOT the test statistic."""
    m = fit_event_study(stack, outcome, fe=fe, counts=counts, cluster=cluster)
    if m is None:
        return None
    names = _rel_day_coefs(m)
    wanted = [names[k] for k in days if k in names]
    if not wanted:
        return None
    return float(m.coef().loc[wanted].mean())


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


def randomization_p(panel, real_starts, outcome, pre, post, draws, rng,
                    fe="ep_cd + dow", counts=False, date_col="incident_date",
                    cluster=CLUSTER_VAR):
    """Episode-level randomization inference. Returns (observed, p, null draws).

    The statistic is the joint chi-square, which is non-negative and increasing
    in departure from the null, so p is the share of placebo statistics at least
    as large as the observed one.
    """
    obs_stack = build_stack(panel, real_starts, pre, post, date_col)
    obs = first_week_effect(obs_stack, outcome, fe=fe, counts=counts, cluster=cluster)
    if obs is None:
        return None, np.nan, np.array([])
    lo, hi = panel[date_col].min(), panel[date_col].max()
    stats_ = []
    for _ in range(draws):
        ps = placebo_starts(rng, real_starts, lo, hi, pre, post)
        if len(ps) != len(list(real_starts)):
            continue                              # never let a short draw in
        b = first_week_effect(build_stack(panel, ps, pre, post, date_col),
                              outcome, fe=fe, counts=counts, cluster=cluster)
        if b is not None:
            stats_.append(b)
    stats_ = np.array(stats_)
    p = float((stats_ >= obs).mean()) if len(stats_) else np.nan
    return obs, p, stats_
