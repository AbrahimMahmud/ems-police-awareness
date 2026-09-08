"""Enforcement for the confirmation freeze (docs/CONFIRMATION_PLAN.md).

The pre-registration's entire value rests on the extension-period outcomes not
having been examined before the hypotheses were fixed. Until now that rule was
enforced by one hard-coded literal in a single script. This module makes it a
property of the pipeline: any modelling script that reads outcome data calls
`assert_discovery_only()` and cannot silently widen its own sample.

Lifting the freeze is therefore a single, greppable, reviewable act — flip
`FREEZE_ACTIVE` in config.py — rather than an edit that could pass unnoticed in a
diff. That audit trail is exactly what a Registered Report reviewer asks for.
"""

import pandas as pd

from config import ANALYSIS_END, ANALYSIS_START, FREEZE_ACTIVE


class FreezeViolation(RuntimeError):
    """Raised when outcome data outside the discovery window reaches a model."""


def assert_discovery_only(df, date_col="incident_date", where=""):
    """Fail loudly if any row falls outside the discovery window.

    No-op once FREEZE_ACTIVE is False, which is the deliberate act of opening the
    confirmation sample. Returns the frame so it can be used inline.
    """
    if not FREEZE_ACTIVE:
        return df
    if date_col not in df.columns:
        raise FreezeViolation(
            f"{where or 'caller'}: no '{date_col}' column, so the freeze cannot be "
            "verified. Pass the correct date column rather than skipping the check."
        )
    d = pd.to_datetime(df[date_col])
    lo, hi = pd.Timestamp(ANALYSIS_START), pd.Timestamp(ANALYSIS_END)
    bad = int(((d < lo) | (d > hi)).sum())
    if bad:
        raise FreezeViolation(
            f"{where or 'caller'}: {bad:,} of {len(df):,} rows fall outside the "
            f"discovery window {ANALYSIS_START}..{ANALYSIS_END} "
            f"(observed {d.min().date()}..{d.max().date()}). The confirmation "
            "freeze is still active; set FREEZE_ACTIVE = False in config.py only "
            "as the deliberate, committed act of opening the confirmation sample."
        )
    return df


def freeze_banner(script):
    """One line at the top of a run so every log records the sample state."""
    state = "ACTIVE — discovery only" if FREEZE_ACTIVE else "LIFTED — confirmation sample open"
    print(f"[freeze] {script}: {state} ({ANALYSIS_START}..{ANALYSIS_END})")
