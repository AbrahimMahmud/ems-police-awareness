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

import inspect
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import (
    CONFIRMATION_WINDOWS,
    DATA_REFERENCE,
    DISCOVERY_END,
    DISCOVERY_START,
    FREEZE_ACCESS_LOG,
    FREEZE_ACTIVE,
    FREEZE_EXEMPTIONS,
)


class FreezeViolation(RuntimeError):
    """Raised when outcome data outside the permitted sample reaches a model."""


def active_windows(window=None):
    """The (start, end) intervals this run is permitted to touch.

    `window=None` derives the sample from the flag: discovery while frozen, the
    confirmation windows once lifted. That is the SEALED script's mode, and it
    was every script's mode until 2026-09-13 (finding D8, addendum 26): lifting
    the freeze would have switched the discovery estimators, figures, power and
    calibration onto the confirmation sample — turning `python3
    17_stacked_event_study.py` into an unsealed confirmatory run, and making the
    discovery results irreproducible after the lift. So:

      window="discovery"     the discovery window whatever the flag says. Every
                             exploratory script asks for this by name.
      window="confirmation"  the confirmation windows; REFUSED while the freeze
                             is active, whoever asks.
      window=None            derived from the flag (30_confirmatory_run only).

    There is deliberately no value that returns both, because pooling them is
    the failure this guards against.
    """
    disc = [(pd.Timestamp(DISCOVERY_START), pd.Timestamp(DISCOVERY_END))]
    conf = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in CONFIRMATION_WINDOWS]
    if window == "discovery":
        return disc
    if window == "confirmation":
        if FREEZE_ACTIVE:
            raise FreezeViolation("the confirmation sample was requested while the freeze "
                                  "is ACTIVE; only the lift (config.FREEZE_ACTIVE = False) opens it")
        return conf
    if window is not None:
        raise ValueError(f"window must be None, 'discovery' or 'confirmation', not {window!r}")
    return disc if FREEZE_ACTIVE else conf


def _in_windows(dates, windows):
    m = pd.Series(False, index=dates.index)
    for lo, hi in windows:
        m |= dates.between(lo, hi)
    return m


def select_sample(df, date_col="incident_date", where="", window=None):
    """Filter to the permitted sample AND prove the filter did what it claims.

    This replaces `df[df[date].between(ANALYSIS_START, ANALYSIS_END)]` followed
    by a separate assertion. Callers must not do their own window filtering:
    that is what made the old guard tautological.

    `window` is passed to `active_windows`: exploratory scripts say
    window="discovery" so the lift cannot move them; the sealed script leaves it
    derived. Returns the permitted rows. Raises if the frame is empty afterwards,
    since a silently empty sample is the failure mode that looks like a clean run.
    """
    if date_col not in df.columns:
        raise FreezeViolation(
            f"{where or 'caller'}: no '{date_col}' column, so the sample cannot be "
            "verified. Pass the correct date column rather than skipping the check.")
    d = pd.to_datetime(df[date_col])
    win = active_windows(window)
    keep = _in_windows(d, win)
    out = df[keep].copy()

    if out.empty:
        raise FreezeViolation(
            f"{where or 'caller'}: no rows fall inside the permitted sample "
            f"{[(str(a.date()), str(b.date())) for a, b in win]} "
            f"(frame spans {d.min().date()}..{d.max().date()}).")

    # Disjointness, checked on the DATA rather than asserted in a comment.
    if window == "confirmation" or (window is None and not FREEZE_ACTIVE):
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


# ---------------------------------------------------------------------------
# Declared accesses (config.FREEZE_EXEMPTIONS)
# ---------------------------------------------------------------------------
def _calling_script():
    """The .py file that called into this module, so the exemption can be
    checked against the script it was declared for rather than trusted."""
    for fr in inspect.stack()[1:]:
        q = Path(fr.filename)
        if q.suffix == ".py" and q.name != "freeze_guard.py" and q.exists():
            return q.name
    return None


def _git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=20, cwd=Path(__file__).parent)
        return r.stdout.strip()[:12]
    except Exception:
        return ""


def declared_access(df, exemption, date_col="incident_date", where=""):
    """Return the WHOLE frame - confirmation rows included - under a declared exemption.

    This is the opposite of select_sample: it does not filter. It exists so that
    the one kind of confirmation-window read this project permits - a coverage
    diagnostic that emits dates and missingness rates and no outcome value - is
    a decision on the record rather than a script quietly added to an exemption
    list. Three things make it different from GUARD_EXEMPT:

      1. The exemption must be declared in config.FREEZE_EXEMPTIONS, with the
         script that may use it, what it reads, and exactly which columns it may
         write. An undeclared name raises. A declared name used from any other
         script raises, so the exemption cannot be borrowed.
      2. Every call appends a row to FREEZE_ACCESS_LOG - when, which exemption,
         which script, which commit, how many rows and how many of them fall in a
         confirmation window. The log is committed. Incidents F1 and F2 were
         found weeks late because nothing recorded the read; this records it at
         the moment it happens.
      3. declared_output() below refuses to write anything but the declared
         columns, so the scope written in the addendum is the scope on disk.

    The freeze flag is irrelevant here on purpose: a declared access is allowed
    while the freeze holds (that is the point) and stays logged after it lifts.
    """
    spec = FREEZE_EXEMPTIONS.get(exemption)
    if spec is None:
        raise FreezeViolation(
            f"{where or 'caller'}: exemption {exemption!r} is not declared in "
            f"config.FREEZE_EXEMPTIONS ({sorted(FREEZE_EXEMPTIONS)}). A read of "
            "confirmation-window outcomes must be declared and disclosed first.")
    caller = _calling_script()
    if caller != spec["script"]:
        raise FreezeViolation(
            f"{where or 'caller'}: exemption {exemption!r} is declared for "
            f"{spec['script']} and was invoked from {caller!r}. An exemption "
            "belongs to one script and cannot be borrowed.")
    if date_col not in df.columns:
        raise FreezeViolation(
            f"{where or 'caller'}: no '{date_col}' column, so the access cannot be "
            "described in the log.")
    d = pd.to_datetime(df[date_col])
    conf = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in CONFIRMATION_WINDOWS]
    n_conf = int(_in_windows(d, conf).sum())
    row = {
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exemption": exemption,
        "script": caller,
        "git_commit": _git_commit(),
        "rows_total": int(len(df)),
        "rows_confirmation_window": n_conf,
        "date_min": str(d.min().date()),
        "date_max": str(d.max().date()),
        "disclosure": spec["disclosure"],
    }
    FREEZE_ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not FREEZE_ACCESS_LOG.exists()
    pd.DataFrame([row]).to_csv(FREEZE_ACCESS_LOG, mode="a", header=new, index=False)
    print(f"[freeze] DECLARED ACCESS {exemption!r} by {caller}: {len(df):,} rows, "
          f"{n_conf:,} in a confirmation window ({row['date_min']}..{row['date_max']}); "
          f"logged to {FREEZE_ACCESS_LOG.name}; scope: {spec['disclosure']}")
    return df


def declared_output(frame, exemption, name):
    """Write one of an exemption's declared outputs, refusing anything else.

    The columns must equal the declared tuple exactly - not a superset, not a
    reordering. A column that is not in the declaration is, by definition,
    something the disclosure did not promise, and it does not get written.
    """
    spec = FREEZE_EXEMPTIONS.get(exemption)
    if spec is None:
        raise FreezeViolation(f"exemption {exemption!r} is not declared")
    if name not in spec["writes"]:
        raise FreezeViolation(
            f"{name!r} is not a declared output of {exemption!r} "
            f"(declared: {sorted(spec['writes'])})")
    want = tuple(spec["writes"][name])
    got = tuple(str(c) for c in frame.columns)
    if got != want:
        raise FreezeViolation(
            f"{name}: columns {list(got)} differ from the declared {list(want)}. "
            "The disclosure fixed the scope; the output does not get to widen it.")
    out = DATA_REFERENCE / name
    frame.to_csv(out, index=False)
    print(f"[freeze] declared output {name}: {len(frame):,} rows, columns {list(want)}")
    return out
