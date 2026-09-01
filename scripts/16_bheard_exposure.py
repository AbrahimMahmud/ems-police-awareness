"""Build community-district B-HEARD exposure, 2021-2024 (confound control).

Why this exists
---------------
B-HEARD (Behavioral Health Emergency Assistance Response Division) is an
EMS-based alternative to police response for nonviolent mental-health 911 calls.
It launched June 2021 in three Harlem precincts and reached 31 of NYC's ~78
precincts by 2025 on a staggered schedule. A quasi-experimental evaluation using
the *same* EMS Incident Dispatch Data file we use as our outcome
(Psychiatric Services, doi:10.1176/appi.ps.20250528) finds that adoption REDUCES
mental-health EMS call rates in adopting precincts, with effects emerging roughly
a year after implementation.

That makes B-HEARD a geographically staggered, time-varying intervention acting
directly on our outcome variable, entirely inside the confirmation sample
(2021-2024). It biases in the SAME DIRECTION as the hypothesis under test, so an
uncontrolled confirmatory run could confirm H1 for the wrong reason. Per
CONFIRMATION_PLAN discipline the handling is specified here, before the run.

The discovery sample (2017-2020) predates B-HEARD entirely; exposure is zero
throughout it by construction, which is the primary validation check below.

Crosswalk method
----------------
Precincts and community districts are not nested, so precinct-level adoption has
to be mapped onto our CD-level panel. Rather than area-weight two shapefiles, we
weight by actual EMS call volume: the dispatch file carries BOTH `policeprecinct`
and `communitydistrict` on every incident, so a server-side cross-tabulation
gives an exact, outcome-weighted crosswalk. Call volume is the correct weight
here because the quantity being apportioned is a share of calls, not of land.

Date uncertainty
----------------
OCMH published expansions by neighborhood, not by precinct number, and the
intermediate tranches cannot be pinned to specific precincts from public
sources. `bheard_precinct_adoption.csv` therefore carries an earliest/latest
window and a confidence flag per precinct rather than invented precision. This
script emits both bounds:

  bheard_exposure_early  - every precinct adopts at its earliest plausible date
                           (CONSERVATIVE: maximal exposure, primary control)
  bheard_exposure_late   - every precinct adopts at its latest plausible date

Specifications should use `_early` as the primary control and report `_late` as a
sensitivity. Neither bound affects the discovery period, and the pre-registered
"restrict to pre-2021-06" sensitivity sidesteps the date uncertainty entirely.

Outputs (committed, small):
  data/reference/precinct_cd_crosswalk.csv
  data/reference/bheard_cd_exposure.csv
"""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_REFERENCE, VALID_CDS

SOURCES_LOG = DATA_REFERENCE / "data_sources.csv"
ADOPTION_CSV = DATA_REFERENCE / "bheard_precinct_adoption.csv"
CROSSWALK_CSV = DATA_REFERENCE / "precinct_cd_crosswalk.csv"
EXPOSURE_CSV = DATA_REFERENCE / "bheard_cd_exposure.csv"

EMS_SODA = "https://data.cityofnewyork.us/resource/76xm-jjuj.json"
CROSSWALK_START = "2015-01-01"
CROSSWALK_END = "2025-01-01"

# B-HEARD launched June 2021; nothing before this can be exposed.
BHEARD_LAUNCH = pd.Timestamp("2021-06-01")

# Independent validation constraints: NYC Independent Budget Office,
# "B-HEARD: A Look at Precinct Level Data" (January 2026) reports the number of
# precincts operational in the first quarter of each year.
IBO_OPERATIONAL_COUNTS = {"2022-01-01": 3, "2023-01-01": 11,
                          "2024-01-01": 25, "2025-01-01": 31}

UA = {"User-Agent": "ems-police-awareness-research/1.0"}


def log_source(source_id, description, url, payload_bytes=None, out_file=None):
    """Append a provenance row (see docs/DATA_PROVENANCE.md) with content hash."""
    if payload_bytes is None and out_file is not None:
        payload_bytes = open(out_file, "rb").read()
    row = pd.DataFrame([{
        "source_id": source_id,
        "description": description,
        "url": url,
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(payload_bytes).hexdigest() if payload_bytes else "",
        "output_file": str(out_file) if out_file else "",
    }])
    header = not SOURCES_LOG.exists()
    row.to_csv(SOURCES_LOG, mode="a", header=header, index=False)


def fetch_crosswalk():
    """Precinct x CD incident counts, aggregated server-side by SODA."""
    params = urllib.parse.urlencode({
        "$select": "policeprecinct,communitydistrict,count(1) as n",
        "$where": (f'incident_datetime >= "{CROSSWALK_START}T00:00:00"'
                   f' AND incident_datetime < "{CROSSWALK_END}T00:00:00"'),
        "$group": "policeprecinct,communitydistrict",
        "$limit": 5000,
    })
    url = f"{EMS_SODA}?{params}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        payload = r.read()
    rows = json.loads(payload)

    df = pd.DataFrame(rows)
    df["policeprecinct"] = pd.to_numeric(df["policeprecinct"], errors="coerce")
    df["communitydistrict"] = pd.to_numeric(df["communitydistrict"], errors="coerce")
    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df = df.dropna(subset=["policeprecinct", "communitydistrict", "n"])
    df = df.astype({"policeprecinct": int, "communitydistrict": int, "n": int})

    # Restrict to the 59 analysis CDs (I7); park/airport joint-interest areas out.
    df = df[df["communitydistrict"].isin(VALID_CDS)].copy()

    # w_precinct_in_cd: of this CD's calls, what fraction sits in this precinct.
    # This is the weight used to convert precinct-level adoption into CD exposure.
    df["w_precinct_in_cd"] = df["n"] / df.groupby("communitydistrict")["n"].transform("sum")
    return df.sort_values(["communitydistrict", "policeprecinct"]).reset_index(drop=True)


def build_exposure(xwalk, adoption):
    """CD exposure as a STEP FUNCTION: one row per (bound, CD, change date).

    Exposure is the call-weighted share of a CD's EMS volume sitting in precincts
    that have adopted B-HEARD as of `effective_from`. It is piecewise constant --
    it only moves when a precinct adopts -- so storing steps rather than a daily
    grid keeps the committed reference file small and hand-checkable. Use
    `expand_daily()` to get a CD x date panel.
    """
    out = []
    for bound, col in (("early", "adoption_earliest"), ("late", "adoption_latest")):
        merged = xwalk.copy()
        adopt = dict(zip(adoption["precinct"], pd.to_datetime(adoption[col])))
        merged["adopt_date"] = merged["policeprecinct"].map(adopt)
        covered = merged.dropna(subset=["adopt_date"])
        for cd, g in covered.groupby("communitydistrict"):
            cum = 0.0
            for d, step in g.groupby("adopt_date")["w_precinct_in_cd"].sum().items():
                cum += float(step)
                out.append({"bound": bound, "communitydistrict": int(cd),
                            "effective_from": d.date().isoformat(),
                            "exposure": round(min(cum, 1.0), 6)})
    return pd.DataFrame(out).sort_values(
        ["bound", "communitydistrict", "effective_from"]).reset_index(drop=True)


def expand_daily(steps, bound=None, start=None, end="2024-12-31"):
    """Expand the step table to a CD x date panel; exposure is 0 before launch."""
    if bound is not None:
        steps = steps[steps["bound"] == bound]
    dates = pd.date_range(start or BHEARD_LAUNCH, end, freq="D")
    frames = []
    for cd, g in steps.groupby("communitydistrict"):
        g = g.assign(effective_from=pd.to_datetime(g["effective_from"]))
        s = (pd.Series(index=dates, dtype=float)
             .combine_first(pd.Series(g["exposure"].values,
                                      index=g["effective_from"].values))
             .reindex(dates).ffill().fillna(0.0))
        frames.append(pd.DataFrame({"communitydistrict": cd, "date": dates,
                                    "exposure": s.values}))
    return pd.concat(frames, ignore_index=True)


def main():
    print("Fetching precinct x CD crosswalk from the EMS dispatch file...")
    xwalk = fetch_crosswalk()
    xwalk.to_csv(CROSSWALK_CSV, index=False)
    print(f"  {len(xwalk)} precinct-CD pairs over {xwalk['n'].sum():,} incidents")
    print(f"  {xwalk['communitydistrict'].nunique()} CDs, "
          f"{xwalk['policeprecinct'].nunique()} precincts")
    log_source("S10", "NYC EMS dispatch precinct x community district crosswalk "
                      "(server-side aggregation, 2015-2024 incidents)",
               EMS_SODA, out_file=CROSSWALK_CSV)

    adoption = pd.read_csv(ADOPTION_CSV)
    print(f"\nAdoption table: {len(adoption)} precincts, confidence mix: "
          f"{adoption['confidence'].value_counts().to_dict()}")
    log_source("S11", "B-HEARD precinct adoption schedule (NYC Mayor's Office of "
                      "Community Mental Health announcements; operational counts "
                      "validated against NYC IBO Jan 2026 precinct-level report)",
               "https://mentalhealth.cityofnewyork.us/b-heard", out_file=ADOPTION_CSV)

    steps = build_exposure(xwalk, adoption)
    steps.to_csv(EXPOSURE_CSV, index=False)
    print(f"\nExposure step table: {len(steps)} rows "
          f"({steps['communitydistrict'].nunique()} CDs x 2 bounds)")

    # ---- validation ------------------------------------------------------
    print("\nValidation")
    earliest = pd.to_datetime(steps["effective_from"]).min()
    assert earliest >= BHEARD_LAUNCH, \
        f"exposure begins {earliest.date()}, before the B-HEARD launch"
    print(f"  no exposure before {BHEARD_LAUNCH.date()}: OK "
          f"(discovery period 2017-2020 unaffected)")

    # The two bounds must BRACKET the independently published counts: the late
    # bound is a lower bound on how many precincts were live, the early bound an
    # upper bound. Exact agreement is not expected -- OCMH published expansions
    # by neighborhood, not by precinct -- but a published count falling outside
    # [late, early] would mean the adoption table is wrong, not merely imprecise.
    failures = []
    for date_str, published in IBO_OPERATIONAL_COUNTS.items():
        d = pd.Timestamp(date_str)
        lo = int((pd.to_datetime(adoption["adoption_latest"]) <= d).sum())
        hi = int((pd.to_datetime(adoption["adoption_earliest"]) <= d).sum())
        ok = lo <= published <= hi
        if not ok:
            failures.append((date_str, lo, published, hi))
        print(f"  {date_str}: bounds [{lo:2d}, {hi:2d}] vs IBO {published:2d} "
              f"-- {'brackets' if ok else 'OUTSIDE BOUNDS'}")
    assert not failures, (
        "B-HEARD adoption bounds do not bracket the published operational counts: "
        f"{failures}. Widen adoption_earliest/adoption_latest in "
        f"{ADOPTION_CSV.name} rather than guessing precinct-level dates.")

    daily = expand_daily(steps, bound="early")
    final = daily[daily["date"] == daily["date"].max()]
    print(f"\n  CDs with any exposure by 2024-12-31: {(final['exposure'] > 0).sum()} of 59")
    print(f"  CDs fully covered (>=0.99): {(final['exposure'] >= 0.99).sum()}")
    print(f"  mean exposure across all 59 CDs: {final['exposure'].sum() / 59:.3f}")

    # Round-trip check: the step table must reproduce the same coverage the
    # crosswalk implies once every precinct has adopted.
    implied = (xwalk[xwalk["policeprecinct"].isin(adoption["precinct"])]
               .groupby("communitydistrict")["w_precinct_in_cd"].sum().clip(upper=1.0))
    rebuilt = final.set_index("communitydistrict")["exposure"]
    diff = (implied - rebuilt.reindex(implied.index).fillna(0)).abs().max()
    assert diff < 1e-6, f"step table disagrees with crosswalk by {diff:.2e}"
    print(f"  step table round-trips against the crosswalk (max diff {diff:.1e}): OK")
    print(f"\nWrote {CROSSWALK_CSV.name}, {EXPOSURE_CSV.name}")


if __name__ == "__main__":
    main()
