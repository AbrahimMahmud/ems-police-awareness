"""Core of the stacked episode event study, shared by 17 and 18.

Kept in an importable (non-numeric) module so the synthetic-null calibration in
18 exercises exactly the estimator that 17 runs on real data. Calibrating a
re-implementation would prove nothing.
"""

import numpy as np
import pandas as pd
import pyfixest as pf

from config import EVENT_REFERENCE_DAY


def build_stack(panel, starts, pre, post, date_col="incident_date"):
    """Stack clean event windows: one row per (episode, district, rel_day).

    Windows are truncated at the next episode's start, and any district-day
    claimed by more than one window is dropped, so no observation is a control
    for one event while being treated in another (REWORK_PLAN I4).
    """
    starts = sorted(pd.to_datetime(pd.Series(list(starts))).tolist())
    frames = []
    for i, s in enumerate(starts):
        lo, hi = s - pd.Timedelta(days=pre), s + pd.Timedelta(days=post)
        if i + 1 < len(starts):
            hi = min(hi, starts[i + 1] - pd.Timedelta(days=1))
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
    dup = stack.duplicated(["communitydistrict", date_col], keep=False)
    stack = stack[~dup].copy()
    stack["ep_cd"] = stack["episode"].astype(str) + "_" + stack["communitydistrict"].astype(str)
    return stack


def _rel_day_coefs(model):
    """Map event-time coefficient names back to integer relative days."""
    out = {}
    for n in model._coefnames:
        if "rel_day" not in n or "[T." not in n:
            continue
        try:
            out[int(float(n.split("[T.")[1].rstrip("]")))] = n
        except ValueError:
            continue
    return out


def fit_event_study(stack, outcome, fe="ep_cd + dow", counts=False):
    """Fit the event-time model. Returns the pyfixest model, or None."""
    d = stack[stack["rel_day"] != EVENT_REFERENCE_DAY].dropna(subset=[outcome])
    if d.empty or d["episode"].nunique() < 2 or len(d) < 200:
        return None
    try:
        if counts:
            d = d[d["total_calls"] > 0]
            return pf.fepois(f"{outcome} ~ C(rel_day) | {fe}", d, vcov="hetero")
        return pf.feols(f"{outcome} ~ C(rel_day) | {fe}", d, vcov="hetero")
    except Exception:
        return None


# Collinear event-time dummies get dropped when windows are truncated by an
# adjacent episode. If the statistic silently averaged whatever survived, its
# composition would vary across randomization draws and the null distribution
# would not correspond to the observed statistic. So require most of the week.
MIN_FIRST_WEEK_DAYS = 6


def first_week_effect(stack, outcome, fe="ep_cd + dow", counts=False, days=range(0, 8),
                      min_days=MIN_FIRST_WEEK_DAYS, return_n=False):
    """Test statistic for H1: mean of the day 0..7 event-time coefficients.

    Two-sided by construction — the directional days-3-5 hypothesis was retired
    with the Twitter measure it was stated on (GATE_C_MEMO.md §6.1).

    Returns None when fewer than `min_days` of the window are identified, so a
    draw with a degenerate design is discarded rather than contributing a
    statistic built from a different set of days than the observed one.
    """
    m = fit_event_study(stack, outcome, fe=fe, counts=counts)
    if m is None:
        return (None, 0) if return_n else None
    names = _rel_day_coefs(m)
    wanted = [names[k] for k in days if k in names]
    if len(wanted) < min_days:
        return (None, len(wanted)) if return_n else None
    val = float(m.coef().loc[wanted].mean())
    return (val, len(wanted)) if return_n else val


def placebo_starts(rng, real_starts, lo, hi, pre, post):
    """Draw placebo episode dates that preserve the real episodes' spacing.

    Preserving spacing matters: attention episodes cluster, and a null built from
    uniformly scattered dates would understate how often clustered draws produce
    a large statistic by chance.
    """
    real = sorted(pd.to_datetime(pd.Series(list(real_starts))).tolist())
    if len(real) < 2:
        return []
    gaps = np.diff([d.toordinal() for d in real])
    earliest = lo + pd.Timedelta(days=pre + 1)
    latest = hi - pd.Timedelta(days=post + 1)
    if latest <= earliest:
        return []
    anchor = earliest + pd.Timedelta(days=int(rng.integers(0, max(1, (latest - earliest).days))))
    out = [anchor]
    for g in rng.permutation(gaps):
        nxt = out[-1] + pd.Timedelta(days=int(g))
        if nxt > latest:
            break
        out.append(nxt)
    return out


def randomization_p(panel, real_starts, outcome, pre, post, draws, rng,
                    fe="ep_cd + dow", counts=False, date_col="incident_date"):
    """Episode-level randomization inference. Returns (observed, p, null draws)."""
    obs = first_week_effect(build_stack(panel, real_starts, pre, post, date_col),
                            outcome, fe=fe, counts=counts)
    if obs is None:
        return None, np.nan, np.array([])
    lo, hi = panel[date_col].min(), panel[date_col].max()
    stats = []
    for _ in range(draws):
        ps = placebo_starts(rng, real_starts, lo, hi, pre, post)
        if len(ps) < 2:
            continue
        b = first_week_effect(build_stack(panel, ps, pre, post, date_col),
                              outcome, fe=fe, counts=counts)
        if b is not None:
            stats.append(b)
    stats = np.array(stats)
    p = float((np.abs(stats) >= abs(obs)).mean()) if len(stats) else np.nan
    return obs, p, stats
