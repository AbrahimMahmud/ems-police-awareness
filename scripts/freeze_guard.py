"""Enforcement for the confirmation freeze (docs/CONFIRMATION_PLAN.md).

The pre-registration's entire value rests on the extension-period outcomes not
having been examined before the hypotheses were fixed.

2026-09-09 REWRITE — finding D3. The previous version had three defects, and the
third was dangerous:

  1. TAUTOLOGICAL. Every caller filtered with
     `.between(ANALYSIS_START, ANALYSIS_END)` and then, on the next line, asked
     the guard whether anything fell outside that range. The guard could only
     ever confirm what the filter had just done. It never had the opportunity to
     fire, so its passing told nobody anything.

  2. INCOMPLETE. Four scripts read the panel without calling it at all.

  3. IT POOLED THE SAMPLES. `assert_discovery_only` no-opped entirely when
     FREEZE_ACTIVE was False, and the sample bounds were a single pair of
     constants. Lifting the freeze therefore did not open a *confirmation*
     sample; it opened whatever ANALYSIS_START/END happened to say, and widening
     them silently pooled the already-examined discovery years into the
     "confirmatory" run — a discovery-contaminated estimate reported as 70 unseen
     episodes. Nothing in the code prevented that.

The fix for (1) and (2) is the same idea: **the filter and the guard must be one
operation, owned in one place.** `select_sample()` below both selects the rows a
run may use and proves nothing else got through. A caller cannot filter to the
wrong window and then be asked whether it filtered to the right one, because it
no longer does its own filtering.

The fix for (3) is that the active window is DERIVED from FREEZE_ACTIVE and the
two samples are disjoint by construction. Lifting the freeze switches the sample
to the confirmation windows and EXCLUDES discovery, rather than widening a range.
"""

import pandas as pd

from config import (
    CONFIRMATION_WINDOWS,
    DISCOVERY_END,
    DISCOVERY_START,
    FREEZE_ACTIVE,
)


class FreezeViolation(RuntimeError):
    """Raised when outcome data outside the permitted sample reaches a model."""


def active_windows():
    """The (start, end) intervals this run is permitted to touch.

    Derived, never hand-set. While frozen this is discovery only; once lifted it
    is the confirmation windows only. There is deliberately no state in which
    both are returned, because pooling them is the failure this guards against.
    """
    if FREEZE_ACTIVE:
        return [(pd.Timestamp(DISCOVERY_START), pd.Timestamp(DISCOVERY_END))]
    return [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in CONFIRMATION_WINDOWS]


def _in_windows(dates, windows):
    m = pd.Series(False, index=dates.index)
    for lo, hi in windows:
        m |= dates.between(lo, hi)
    return m


def select_sample(df, date_col="incident_date", where=""):
    """Filter to the permitted sample AND prove the filter did what it claims.

    This replaces `df[df[date].between(ANALYSIS_START, ANALYSIS_END)]` followed
    by a separate assertion. Callers must not do their own window filtering:
    that is what made the old guard tautological.

    Returns the permitted rows. Raises if the frame is empty afterwards, since a
    silently empty sample is the failure mode that looks like a clean run.
    """
    if date_col not in df.columns:
        raise FreezeViolation(
            f"{where or 'caller'}: no '{date_col}' column, so the sample cannot be "
            "verified. Pass the correct date column rather than skipping the check.")
    d = pd.to_datetime(df[date_col])
    win = active_windows()
    keep = _in_windows(d, win)
    out = df[keep].copy()

    if out.empty:
        raise FreezeViolation(
            f"{where or 'caller'}: no rows fall inside the permitted sample "
            f"{[(str(a.date()), str(b.date())) for a, b in win]} "
            f"(frame spans {d.min().date()}..{d.max().date()}).")

    # Disjointness, checked on the DATA rather than asserted in a comment.
    if not FREEZE_ACTIVE:
        disc = pd.to_datetime(out[date_col]).between(
            pd.Timestamp(DISCOVERY_START), pd.Timestamp(DISCOVERY_END))
        if disc.any():
            raise FreezeViolation(
                f"{where or 'caller'}: {int(disc.sum()):,} discovery-period rows "
                "reached the confirmation sample. The two samples must be disjoint; "
                "a confirmatory estimate computed on already-examined data is not "
                "confirmatory.")

    dropped = int((~keep).sum())
    print(f"[freeze] {where or 'sample'}: kept {len(out):,} rows, dropped {dropped:,} "
          f"outside {[(str(a.date()), str(b.date())) for a, b in win]}")
    return out


def assert_no_confirmation_outcomes(df, date_col="incident_date", where=""):
    """Assert a frame contains NO confirmation-period rows, whatever the flag.

    Unlike `select_sample` this does not filter, so it is safe on raw frames and
    it CAN fail — which is the point. Use it where a script legitimately handles
    a wide frame (panel construction, QC) but must not carry extension outcomes
    into anything that gets looked at.
    """
    if date_col not in df.columns:
        raise FreezeViolation(f"{where or 'caller'}: no '{date_col}' column")
    d = pd.to_datetime(df[date_col])
    bad = int(_in_windows(d, [(pd.Timestamp(a), pd.Timestamp(b))
                              for a, b in CONFIRMATION_WINDOWS]).sum())
    if bad and FREEZE_ACTIVE:
        raise FreezeViolation(
            f"{where or 'caller'}: {bad:,} rows fall in a confirmation window "
            f"{list(CONFIRMATION_WINDOWS)} while the freeze is ACTIVE.")
    return df


def assert_discovery_only(df, date_col="incident_date", where=""):
    """Back-compatible wrapper. Prefer `select_sample`.

    Retained so existing callers keep working, but it now delegates to the real
    check instead of re-testing the filter the caller just applied.
    """
    return assert_no_confirmation_outcomes(df, date_col=date_col, where=where)


def freeze_banner(script):
    """One line at the top of a run so every log records the sample state."""
    win = active_windows()
    state = "ACTIVE — discovery only" if FREEZE_ACTIVE else "LIFTED — confirmation sample"
    spans = ", ".join(f"{a.date()}..{b.date()}" for a, b in win)
    print(f"[freeze] {script}: {state} ({spans})")
