"""Coverage breaks inside the confirmation window (finding O2) - a DECLARED access.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
Two structural breaks are known to sit inside the 2015-2016 confirmation window:
the share of dispatches with no community district falls sharply at 2016-01-01,
and the INJALS call code is retired inside the window (finding O2). A confirmatory
estimate run across a discontinuity nobody has mapped is not a confirmatory
estimate, so the map has to exist before CP2 - and drawing it means reading
confirmation-window rows of the outcome extract, which the freeze protects.

This script is the one place that read is allowed to happen, and it is allowed
because its scope was written down first: CONFIRMATION_PLAN.md addendum 18,
committed before this file existed, says what may be emitted -

    (a) per final_call_type, the first and last incident_date it appears on;
    (b) per calendar year, the share of dispatched calls with no district

- and nothing else. No count by period, no outcome mean or share of any call
group, no district-level value, nothing crossed with the attention index or the
episode list. The access goes through freeze_guard.declared_access(), which
refuses any exemption not declared in config.FREEZE_EXEMPTIONS, refuses any
caller but this script, and logs every run to data/reference/freeze_access_log.csv.
The outputs go through declared_output(), which refuses any column the
declaration does not name. D.declared_access_scoped checks all of it.

"It is only metadata" is the reasoning that produced incidents F1 and F2. The
difference here is not the reasoning; it is that the scope was fixed in advance
and a check holds it there afterwards.

WHAT IS DECIDED FROM IT (pre-specified in addendum 18, applied here to the two
outputs only, never to an outcome value):
  1. A call code whose first or last date lies strictly inside a confirmation
     ANALYSIS window is a within-window break for every outcome group containing
     it. The primary estimates are unchanged; the affected group/stratum gets a
     pre-specified sensitivity dropping episodes whose +/-14-day window contains
     the break date, reported beside the primary.
  2. If the missing-district share moves by more than a factor of two between
     adjacent years and the year boundary lies inside a confirmation analysis
     window, that boundary is a geocoding break; same treatment. Finding O2's
     corrected claim measured the induced artifact at ~0.0002 on the share, so
     this is expected to be a demonstration rather than a correction.

Output: data/reference/ems_call_code_span.csv
        data/reference/ems_missing_district_rate_by_year.csv
        data/reference/ems_coverage_breaks.csv   (the two rules, evaluated on the above)
        data/reference/freeze_access_log.csv (appended)
"""

import pandas as pd

from config import (
    CALL_TYPE_GROUPS,
    CONFIRMATION_ANALYSIS_WINDOWS,
    EMS_EXTRACT_CD_DAY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
)
from freeze_guard import declared_access, declared_output, freeze_banner
from provenance import log_source

EXEMPTION = "O2_coverage_breaks"
freeze_banner("35_coverage_breaks")

# Columns are named explicitly so a widened extract cannot widen this read.
ext = pd.read_parquet(EMS_EXTRACT_CD_DAY,
                      columns=["incident_date", "communitydistrict", "final_call_type", "n_calls"])
ext["incident_date"] = pd.to_datetime(ext["incident_date"])
ext = declared_access(ext, EXEMPTION, where="35_coverage_breaks")

# (a) per call code: first and last date observed. Dates, not volumes.
span = (ext.groupby("final_call_type")["incident_date"]
           .agg(first_date="min", last_date="max").reset_index())
span["first_date"] = span["first_date"].dt.strftime("%Y-%m-%d")
span["last_date"] = span["last_date"].dt.strftime("%Y-%m-%d")
span = span.sort_values("final_call_type").reset_index(drop=True)
span_path = declared_output(span[["final_call_type", "first_date", "last_date"]],
                            EXEMPTION, "ems_call_code_span.csv")

# (b) per year: share of dispatched calls with no community district. A ratio,
# rounded, with neither numerator nor denominator written.
year = ext["incident_date"].dt.year
tot = ext.groupby(year)["n_calls"].sum()
miss = ext[ext["communitydistrict"].isna()].groupby(year[ext["communitydistrict"].isna()])["n_calls"].sum()
rate = (miss.reindex(tot.index).fillna(0) / tot).round(6)
rate = rate.rename("missing_district_rate").reset_index().rename(columns={"incident_date": "year"})
rate["year"] = rate["year"].astype(int)
rate_path = declared_output(rate[["year", "missing_district_rate"]],
                            EXEMPTION, "ems_missing_district_rate_by_year.csv")

# --- the pre-specified rules, evaluated on the two outputs only ---------------
extract_lo, extract_hi = span["first_date"].min(), span["last_date"].max()
windows = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in CONFIRMATION_ANALYSIS_WINDOWS]


def inside(day):
    d = pd.Timestamp(day)
    return any(lo < d < hi for lo, hi in windows)


code_to_group = {c: g for g, codes in CALL_TYPE_GROUPS.items() for c in codes}
print("\n== rule 1: call codes in an outcome group born or retired inside a confirmation analysis window ==")
breaks = []
for _, r in span[span["final_call_type"].isin(code_to_group)].iterrows():
    c = r["final_call_type"]
    if r["first_date"] != extract_lo and inside(r["first_date"]):
        breaks.append((code_to_group[c], c, "first", r["first_date"]))
    if r["last_date"] != extract_hi and inside(r["last_date"]):
        breaks.append((code_to_group[c], c, "last", r["last_date"]))
for g, c, kind, d in sorted(breaks):
    print(f"  {g:14s} {c:8s} {kind}-date {d}  -> sensitivity: drop episodes whose "
          f"[-{EVENT_WINDOW_PRE},+{EVENT_WINDOW_POST}] window contains it")
if not breaks:
    print("  none")

print("\n== rule 2: missing-district share, adjacent-year ratio (break if >2x or <0.5x inside a window) ==")
r = rate.set_index("year")["missing_district_rate"]
geo_breaks = []
for y0, y1 in zip(r.index[:-1], r.index[1:]):
    ratio = (r[y1] / r[y0]) if r[y0] > 0 else float("inf")
    boundary = pd.Timestamp(f"{y1}-01-01")
    flag = (ratio > 2 or ratio < 0.5) and inside(boundary)
    print(f"  {y0}->{y1}: {r[y0]:.4%} -> {r[y1]:.4%}  ratio {ratio:6.3f}"
          + ("   <- GEOCODING BREAK inside a confirmation analysis window" if flag else ""))
    if flag:
        geo_breaks.append(str(boundary.date()))

# (c) The rule evaluations as a table, so the paper's counts can be claims over
# an artifact rather than a reading of a log. Every value here is copied from
# (a) or (b) or from config; nothing new is read.
def window_of(day):
    d = pd.Timestamp(day)
    for (lo, hi), label in zip(windows, ("C1a", "C1b", "C2")):
        if lo < d < hi:
            return label
    return ""


table = [{"window": window_of(d), "group": g, "final_call_type": c, "kind": f"{kind}_date", "date": d}
         for g, c, kind, d in sorted(breaks)]
table += [{"window": window_of(b), "group": "(geocoding)", "final_call_type": "",
           "kind": "missing_district_step", "date": b} for b in geo_breaks]
breaks_df = pd.DataFrame(table, columns=["window", "group", "final_call_type", "kind", "date"])
breaks_path = declared_output(breaks_df, EXEMPTION, "ems_coverage_breaks.csv")

# Provenance: three derived artifacts of S1b, each with its own id (a source id
# belongs to one artifact - finding P3).
log_source("D4", f"Per call code, first and last incident_date in the EMS extract "
                 f"({len(span)} codes); declared access {EXEMPTION}, addendum 18",
           "derived from data/processed/ems_cd_day_calltype.parquet", out_file=span_path)
log_source("D5", f"Per year, share of dispatched calls with no community district "
                 f"({rate['year'].min()}-{rate['year'].max()}); declared access {EXEMPTION}, addendum 18",
           "derived from data/processed/ems_cd_day_calltype.parquet", out_file=rate_path)
log_source("D6", f"Pre-specified coverage-break rules (addendum 18) evaluated on D4 and D5: "
                 f"{len(breaks)} within-window code break(s), {len(geo_breaks)} geocoding break(s)",
           "derived from ems_call_code_span.csv and ems_missing_district_rate_by_year.csv",
           out_file=breaks_path)
print(f"\nwithin-window code breaks: {len(breaks)}; geocoding breaks: {geo_breaks or 'none'}")
