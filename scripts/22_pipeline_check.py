"""Structural invariants of the built artifacts, checked after every pipeline stage.

WHY THIS EXISTS, AND WHY IT IS NOT THE REGRESSION SUITE
-------------------------------------------------------
23_regression_suite.py asks "is each known defect still fixed?" - one check per
audit finding, keyed to history. This asks a different question: "is what we just
built structurally coherent at all?" It knows nothing about the findings and
everything about shape - row counts, keys, ranges, arithmetic identities between
columns that must hold by construction.

Both are needed because they fail on different things. The suite would not notice
a merge that silently dropped half the panel, and this would not notice a check
that passes for the wrong reason.

WHAT IT IS FOR: it runs between stages of run_all.py, so a stage that corrupts an
artifact is caught immediately rather than four stages later where the cause is no
longer obvious. The EMS extract taught this lesson - a truncated download looked
exactly like a complete one until someone compared row counts against the source.

STATES
  PASS     the invariant holds
  FAIL     it does not
  BLOCKED  the artifact does not exist yet, so the invariant could not be
           evaluated. Deliberately NOT a pass, for the same reason the suite
           makes that distinction: treating "could not check" as "fine" is the
           error that destroyed four dimensions of audit findings on their first
           run.

FREEZE. This reads the panel, which contains outcome data. It routes through
freeze_guard.select_sample() like every other reader, so while the freeze holds it
sees discovery rows only. That is enough: an invariant that holds on discovery and
fails on confirmation would be a genuine finding, but discovering it would require
examining confirmation outcomes, which is exactly what is forbidden. The invariants
are therefore asserted over the permitted sample and RE-ASSERTED automatically when
the freeze lifts, because the same code then sees the confirmation windows.

  python 22_pipeline_check.py                 # all stages
  python 22_pipeline_check.py --stage panel   # one stage
"""

import argparse
import sys

import numpy as np
import pandas as pd

from config import (
    CAI_D_COMPONENTS,
    CAI_S_COMPONENTS,
    DATA_PROCESSED,
    DATA_REFERENCE,
    EPISODE_MAX_DAYS,
    MH_BROAD_GROUPS,
    MH_NARROW_GROUPS,
    OUTPUTS_TABLES,
    VALID_CDS,
)
from freeze_guard import active_windows, freeze_banner, select_sample

results = []


def record(stage, name, state, detail=""):
    results.append({"stage": stage, "check": name, "state": state, "detail": str(detail)[:300]})
    mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "BLOCKED": " ---- "}[state]
    print(f"[{mark}] {stage:<10} {name:<42} {str(detail)[:78]}")


def _load(path, parse_dates=None):
    """Return a frame, or None if absent. Never invents an empty frame."""
    if not path.exists():
        return None
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, parse_dates=parse_dates or [])


# ---------------------------------------------------------------------------
def check_panel():
    stage = "panel"
    f = DATA_PROCESSED / "panel_cd_day.parquet"
    p = _load(f)
    if p is None:
        record(stage, "exists", "BLOCKED", f"{f.name} not built")
        return
    record(stage, "exists", "PASS", f"{len(p):,} rows, {len(p.columns)} columns")

    # The guard, not a hand-written filter. Two things at once: it proves the
    # panel can be sampled legally, and everything below is asserted on exactly
    # the rows a model would see.
    n_all = len(p)
    p = select_sample(p, where="22_pipeline_check")
    lo_hi = active_windows()
    record(stage, "sample_window", "PASS",
           f"{len(p):,} rows in {[(str(a.date()), str(b.date())) for a, b in lo_hi]}")

    # WHAT THIS CANNOT SEE, SAID OUT LOUD. The invariants below are structural
    # properties of the ARTIFACT - key uniqueness, arithmetic identities, ranges -
    # but they can only be evaluated on rows the freeze permits. Corruption in the
    # buffer or the confirmation windows is invisible here.
    #
    # This is not hypothetical. The first defeat attempt on this script corrupted
    # five things at once - a broken identity, a violated ordering, a NaN count,
    # an out-of-range share and a duplicate key - and ALL ELEVEN INVARIANTS
    # PASSED, because the corrupted rows sat in the lag/lead buffer that
    # select_sample drops. Reporting "11 pass" without this line would have read
    # as "the artifact is sound".
    unchecked = n_all - len(p)
    if unchecked:
        record(stage, "rows_outside_the_permitted_sample", "BLOCKED",
               f"{unchecked:,} of {n_all:,} rows ({unchecked / n_all:.1%}) are outside "
               f"the freeze window and are NOT covered by any invariant below")

    n_cd = p["communitydistrict"].nunique()
    bad_cd = sorted(set(p["communitydistrict"]) - set(VALID_CDS))
    record(stage, "districts_exactly_59",
           "PASS" if n_cd == 59 and not bad_cd else "FAIL",
           f"{n_cd} distinct districts" + (f", invalid: {bad_cd[:5]}" if bad_cd else ""))

    dup = int(p.duplicated(["communitydistrict", "incident_date"]).sum())
    record(stage, "key_unique", "PASS" if dup == 0 else "FAIL",
           f"{dup} duplicate (district, date) rows")

    # A district-day present for some districts and absent for others is a
    # balance problem that every fixed-effect estimator will silently absorb.
    # Expected rows use the REQUIRED district count (59), not the observed one.
    # With the observed count this passed after an entire district was deleted -
    # 58 districts x 1461 days is perfectly "balanced" - which is a check passing
    # for the wrong reason, caught by deliberately deleting district 101.
    span = pd.date_range(p["incident_date"].min(), p["incident_date"].max(), freq="D")
    expected = len(span) * len(VALID_CDS)
    record(stage, "panel_balanced", "PASS" if len(p) == expected else "FAIL",
           f"{len(p):,} rows against {expected:,} = {len(span)} days x "
           f"{len(VALID_CDS)} districts ({expected - len(p):,} missing)")

    # Arithmetic identities that hold BY CONSTRUCTION. If these fail, a merge or
    # a groupby changed the meaning of a column.
    narrow = p[list(MH_NARROW_GROUPS)].sum(axis=1)
    broad = p[list(MH_BROAD_GROUPS)].sum(axis=1)
    record(stage, "mh_narrow_is_its_parts",
           "PASS" if (p["mh_narrow"] == narrow).all() else "FAIL",
           f"mh_narrow != sum{MH_NARROW_GROUPS} on "
           f"{int((p['mh_narrow'] != narrow).sum())} rows")
    record(stage, "mh_broad_is_its_parts",
           "PASS" if (p["mh_broad"] == broad).all() else "FAIL",
           f"mh_broad != sum{MH_BROAD_GROUPS} on {int((p['mh_broad'] != broad).sum())} rows")
    ordered = (p["mh_narrow"] <= p["mh_broad"]) & (p["mh_broad"] <= p["total_calls"])
    record(stage, "mh_narrow_le_broad_le_total",
           "PASS" if ordered.all() else "FAIL",
           f"{int((~ordered).sum())} rows violate the ordering")

    share_cols = [c for c in p.columns if c.endswith("_share")]
    bad = {c: int(((p[c] < 0) | (p[c] > 1)).sum()) for c in share_cols}
    bad = {c: n for c, n in bad.items() if n}
    record(stage, "shares_in_unit_interval", "PASS" if not bad else "FAIL",
           f"out-of-range: {bad}" if bad else f"{len(share_cols)} share columns in [0,1]")

    # NaN in a count column means a merge introduced rows that do not exist.
    counts = [c for c in ("edp", "altmen", "suicide_jump", "od_poison_drug",
                          "cardiac", "injury", "asthma", "other", "total_calls")
              if c in p.columns]
    nan_counts = {c: int(p[c].isna().sum()) for c in counts}
    nan_counts = {c: n for c, n in nan_counts.items() if n}
    record(stage, "no_nan_in_counts", "PASS" if not nan_counts else "FAIL",
           f"{nan_counts}" if nan_counts else f"{len(counts)} count columns complete")

    neg = {c: int((p[c] < 0).sum()) for c in counts}
    neg = {c: n for c, n in neg.items() if n}
    record(stage, "counts_non_negative", "PASS" if not neg else "FAIL", f"{neg}" if neg else "")


def check_treatment():
    stage = "treatment"
    comp = _load(DATA_REFERENCE / "cai_components_daily.csv", ["date"])
    tr = _load(DATA_REFERENCE / "cai_trends_daily.csv", ["date"])
    if comp is None or tr is None:
        record(stage, "components_exist", "BLOCKED", "component files not built")
        return
    w = pd.concat([comp, tr]).pivot_table(index="date", columns="component", values="value")
    record(stage, "components_exist", "PASS", f"{len(w.columns)} series, {len(w):,} dates")

    missing = [c for c in CAI_D_COMPONENTS + CAI_S_COMPONENTS if c not in w.columns]
    record(stage, "every_configured_component_present",
           "PASS" if not missing else "FAIL",
           f"absent from the component files: {missing}" if missing
           else f"{list(CAI_D_COMPONENTS)} + {list(CAI_S_COMPONENTS)}")

    dup = int(pd.concat([comp, tr]).duplicated(["date", "component"]).sum())
    record(stage, "one_value_per_date_component", "PASS" if dup == 0 else "FAIL",
           f"{dup} duplicated (date, component) rows")

    # An internal gap means the index is undefined on days inside a component's
    # own span - different from a component that simply starts later.
    gaps = {}
    for c in CAI_D_COMPONENTS:
        if c not in w.columns:
            continue
        s = w[c].dropna()
        if s.empty:
            continue
        inside = pd.date_range(s.index.min(), s.index.max(), freq="D")
        n = len(inside) - len(s)
        if n:
            gaps[c] = n
    record(stage, "no_internal_gaps_in_index_components",
           "PASS" if not gaps else "FAIL", f"{gaps}" if gaps else "")

    cai = _load(DATA_PROCESSED / "cai_daily.parquet")
    if cai is None:
        record(stage, "cai_built", "BLOCKED", "cai_daily.parquet not built")
        return
    cai["date"] = pd.to_datetime(cai["date"])
    record(stage, "cai_built", "PASS", f"{len(cai):,} days")

    scored = cai["cai_d"].notna()
    full = len(CAI_D_COMPONENTS)
    wrong = int((scored & (cai["n_d_components"] < full)).sum())
    unscored = int((~scored & (cai["n_d_components"] >= full)).sum())
    record(stage, "scored_iff_complete", "PASS" if not (wrong or unscored) else "FAIL",
           f"{wrong} scored with <{full} components, {unscored} complete but unscored")

    dup = int(cai["date"].duplicated().sum())
    record(stage, "cai_one_row_per_day", "PASS" if dup == 0 else "FAIL", f"{dup} duplicate dates")


def check_episodes():
    stage = "episodes"
    f = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
    ep = _load(f, ["start", "end", "peak_date"])
    if ep is None:
        record(stage, "exists", "BLOCKED", f"{f.name} not built")
        return
    record(stage, "exists", "PASS", f"{len(ep)} episodes")

    span = (ep["end"] - ep["start"]).dt.days
    record(stage, "span_within_cap", "PASS" if span.max() <= EPISODE_MAX_DAYS else "FAIL",
           f"longest {int(span.max())}d against cap {EPISODE_MAX_DAYS}")
    record(stage, "start_le_end", "PASS" if (span >= 0).all() else "FAIL",
           f"{int((span < 0).sum())} episodes end before they start")

    s = ep.sort_values("start")
    overlap = int((s["start"].shift(-1) <= s["end"]).sum())
    record(stage, "episodes_disjoint", "PASS" if overlap == 0 else "FAIL",
           f"{overlap} episodes overlap the next")

    p = _load(DATA_PROCESSED / "panel_cd_day.parquet")
    if p is None:
        record(stage, "starts_inside_panel", "BLOCKED", "panel not built")
        return
    lo, hi = p["incident_date"].min(), p["incident_date"].max()
    windows = active_windows()
    in_scope = ep[[any(a <= t <= b for a, b in windows) for t in ep["start"]]]
    outside = in_scope[(in_scope["start"] < lo) | (in_scope["start"] > hi)]
    record(stage, "starts_inside_panel", "PASS" if outside.empty else "FAIL",
           f"{len(in_scope)} in-scope episode starts, {len(outside)} outside the panel "
           f"{lo.date()}..{hi.date()}")


def check_bheard():
    stage = "bheard"
    f = DATA_REFERENCE / "bheard_cd_exposure.csv"
    ex = _load(f, ["effective_from"])
    if ex is None:
        record(stage, "exists", "BLOCKED", f"{f.name} not built")
        return
    record(stage, "exists", "PASS", f"{len(ex)} rows, "
           f"{ex['communitydistrict'].nunique()} districts")

    col = [c for c in ex.columns if "expos" in c or c in ("lo", "hi", "share")]
    bad = {c: int(((ex[c] < 0) | (ex[c] > 1)).sum()) for c in col
           if pd.api.types.is_numeric_dtype(ex[c])}
    bad = {c: n for c, n in bad.items() if n}
    record(stage, "exposure_in_unit_interval", "PASS" if not bad else "FAIL", f"{bad}" if bad else "")

    # THE CHECK THAT MATTERS while the freeze holds: B-HEARD launched 2021-06-01,
    # so within the discovery sample exposure must be identically zero. If it is
    # not, the precinct -> community-district crosswalk is wrong, and that would
    # contaminate the confirmatory control rather than the discovery estimate -
    # which is exactly the kind of error that is invisible until too late.
    from config import BHEARD_LAUNCH
    early = ex[ex["effective_from"] < pd.Timestamp(BHEARD_LAUNCH)]
    record(stage, "no_exposure_before_launch", "PASS" if early.empty else "FAIL",
           f"{len(early)} rows effective before {BHEARD_LAUNCH}")


def check_outputs():
    stage = "outputs"
    f = OUTPUTS_TABLES / "regression_suite.csv"
    d = _load(f)
    if d is None:
        record(stage, "suite_ran", "BLOCKED", "no regression_suite.csv")
        return
    record(stage, "suite_ran", "PASS", f"{len(d)} checks")
    # BLOCKED is propagated as BLOCKED, not folded into FAIL. The suite draws
    # that distinction deliberately - "could not evaluate" is not "broken" - and
    # flattening it here would re-introduce the conflation one layer up.
    failing = d[d["state"].isin(["FAIL", "ERROR"])]
    blocked = d[d["state"] == "BLOCKED"]
    if len(failing):
        state, detail = "FAIL", f"{len(failing)} failing: " + ", ".join(
            f"{r['check']}={r['state']}" for _, r in failing.head(4).iterrows())
    elif len(blocked):
        state, detail = "BLOCKED", f"{len(blocked)} blocked: " + ", ".join(
            r["check"] for _, r in blocked.head(4).iterrows())
    else:
        state, detail = "PASS", f"all {len(d)} checks pass"
    record(stage, "suite_all_pass", state, detail)


STAGES = {
    "panel": check_panel,
    "treatment": check_treatment,
    "episodes": check_episodes,
    "bheard": check_bheard,
    "outputs": check_outputs,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=sorted(STAGES), action="append",
                    help="run only these stages (repeatable); default all")
    args = ap.parse_args()

    freeze_banner("22_pipeline_check")
    for name in (args.stage or list(STAGES)):
        STAGES[name]()

    df = pd.DataFrame(results)
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUTS_TABLES / "pipeline_check.csv", index=False)

    counts = df["state"].value_counts().to_dict()
    print("-" * 110)
    print(f"{len(df)} invariants: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    failed = df[df["state"] == "FAIL"]
    blocked = df[df["state"] == "BLOCKED"]
    for _, r in failed.iterrows():
        print(f"  FAIL    {r['stage']}/{r['check']}: {r['detail']}")
    for _, r in blocked.iterrows():
        print(f"  BLOCKED {r['stage']}/{r['check']}: {r['detail']}")
    # BLOCKED does not fail the run - an artifact may legitimately not be built
    # yet mid-pipeline - but it is never silent.
    return 1 if len(failed) else 0


if __name__ == "__main__":
    sys.exit(main())
