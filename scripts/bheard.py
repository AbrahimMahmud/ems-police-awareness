"""B-HEARD exposure as a model-ready control, in one place.

WHY THIS EXISTS (finding X6)
----------------------------
16_bheard_exposure.py builds data/reference/bheard_cd_exposure.csv, and until now
NOTHING read it. Not one model. The ratified control for this project's most
serious confound was computed, validated against the NYC IBO's own precinct
counts, committed — and wired into nothing.

It went unnoticed for a simple reason: B-HEARD begins 2021-06-01 and the freeze
restricts every model to 2017-2020, so the control is identically zero in every
sample anyone has estimated on. Adding it changes no discovery number, which is
precisely why nobody noticed it was missing, and precisely why it MUST be added
before the freeze lifts rather than after.

WHAT B-HEARD IS. From June 2021 New York began routing some mental-health 911
calls to a health-led response rather than police, precinct by precinct. It
pushes the outcome in the SAME DIRECTION as the hypothesis: fewer police-attended
mental-health calls. An uncontrolled 2021-2024 estimate would confuse the two.

BOUNDS, NOT A POINT DATE. 17 of 31 precinct adoption dates are low confidence, so
16 emits an `early` and a `late` bound rather than pretending to a date it does
not have. Both are carried through here; a result that depends on which bound is
used is a result that depends on data we do not have.

THE CHECK THIS MAKES POSSIBLE. Because exposure is zero throughout discovery,
adding it must leave every discovery estimate NUMERICALLY UNCHANGED. If it moves
them, the precinct-to-community-district crosswalk is wrong — and that error
would otherwise surface only in the confirmatory run, where it could not be
fixed. X.bheard_inert_on_discovery asserts it.
"""

import pandas as pd

from config import BHEARD_EXPOSURE_CSV, BHEARD_LAUNCH

BOUNDS = ("early", "late")


def exposure_panel(dates, districts, bound="early", path=None):
    """Exposure for every (district, date), forward-filled from its step table.

    The table is a STEP function: one row per (bound, district, effective_from),
    giving the share of that district's EMS volume covered from that date. A
    district with no row was never covered, and is zero throughout — absent is
    not missing here, it is a real zero, and filling it with NaN would silently
    drop those districts from any model that used the control.
    """
    f = path or BHEARD_EXPOSURE_CSV
    if not f.exists():
        raise FileNotFoundError(f"{f} not built — run 16_bheard_exposure.py")
    if bound not in BOUNDS:
        raise ValueError(f"bound must be one of {BOUNDS}, got {bound!r}")
    steps = pd.read_csv(f, parse_dates=["effective_from"])
    steps = steps[steps["bound"] == bound]

    dates = pd.DatetimeIndex(pd.to_datetime(pd.Series(list(dates))).unique()).sort_values()
    districts = sorted(set(districts))
    out = pd.DataFrame(0.0, index=dates, columns=districts)
    for cd, g in steps.groupby("communitydistrict"):
        if cd not in out.columns:
            continue
        s = (g.sort_values("effective_from")
              .set_index("effective_from")["exposure"]
              .reindex(dates.union(g["effective_from"]))
              .ffill()
              .reindex(dates)
              .fillna(0.0))
        out[cd] = s.to_numpy()
    long = out.stack().rename("bheard_exposure").reset_index()
    long.columns = ["incident_date", "communitydistrict", "bheard_exposure"]
    return long


def attach(panel, bound="early", date_col="incident_date", path=None):
    """Add a bheard_exposure column to a panel. Never drops a row.

    A merge that loses rows would change the sample as a side effect of adding a
    control, which is the kind of silent change this project has been bitten by
    repeatedly, so the row count is asserted rather than assumed.
    """
    n_before = len(panel)
    ex = exposure_panel(panel[date_col].unique(), panel["communitydistrict"].unique(),
                        bound=bound, path=path)
    merged = panel.merge(ex, on=[date_col, "communitydistrict"], how="left")
    merged["bheard_exposure"] = merged["bheard_exposure"].fillna(0.0)
    if len(merged) != n_before:
        raise ValueError(f"attaching B-HEARD changed the row count "
                         f"{n_before} -> {len(merged)}; the exposure table has "
                         "duplicate (district, date) keys")
    return merged


def is_inert(panel, date_col="incident_date"):
    """True when exposure is zero everywhere in this sample.

    Expected for any discovery-only sample, since B-HEARD starts 2021-06-01.
    """
    if "bheard_exposure" not in panel.columns:
        return None
    return bool((panel["bheard_exposure"] == 0).all()), float(panel["bheard_exposure"].max())
