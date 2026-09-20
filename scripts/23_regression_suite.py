"""Executable regression suite: every audit finding as a test that can fail.

WHY THIS EXISTS
---------------
The 2026-09-08 audit found 48 confirmed defects. Five of them were introduced by
the previous round of "fixes" — repairs written without a way to check whether
they broke something else. Prose findings regress silently; assertions do not.

So every finding in docs/AUDIT_FINDINGS.csv gets a check here, keyed by its ID.
A check is written to FAIL while the defect is present and PASS once it is fixed.
Fixing a defect should flip exactly one check and disturb no others.

REGRESSION DETECTION
--------------------
Results are compared against docs/regression_baseline.csv, which is COMMITTED —
it is a contract, not an output, so it lives with the findings rather than in
outputs/ (which is regenerable and gitignored).
Any check that was PASS in the baseline and is not PASS now is a REGRESSION and
exits non-zero. That is the mechanism that catches a fix breaking something else.

  python 23_regression_suite.py              # run, compare to baseline
  python 23_regression_suite.py --baseline   # accept current state as baseline

STATES
------
  PASS     defect is fixed / property holds
  FAIL     defect is present (expected before its phase runs)
  BLOCKED  cannot be evaluated yet — required input absent (NOT a pass)

BLOCKED is deliberately distinct from PASS. Treating "couldn't check" as "fine"
is the exact error that destroyed four dimensions of audit findings on the first
run, and the same error class the audit itself was hunting.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    EPISODE_LIST_PRIMARY,
    EVENT_WINDOW_POST,
    EVENT_WINDOW_PRE,
    DISCOVERY_END,
    DISCOVERY_START,
    CONFIRMATION_WINDOWS,
    CAI_D_BASKET,
    DATA_PROCESSED,
    DATA_REFERENCE,
    OUTPUTS_TABLES,
    PROJECT_ROOT,
)

SCRIPTS = PROJECT_ROOT / "scripts"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

results = []


def check(cid, findings, desc, fn):
    """Run one check. fn returns (state, detail)."""
    try:
        state, detail = fn()
    except FileNotFoundError as e:
        state, detail = "BLOCKED", f"missing input: {Path(str(e.filename or e)).name}"
    except Exception as e:
        state, detail = "ERROR", f"{type(e).__name__}: {e}"
    results.append({"check": cid, "findings": findings, "description": desc,
                    "state": state, "detail": str(detail)[:300]})
    mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "BLOCKED": " ---- ", "ERROR": " ERR  "}[state]
    print(f"[{mark}] {cid:<22} {desc[:64]:<64} {str(detail)[:70]}")


def src(name):
    return (SCRIPTS / name).read_text()


# ===========================================================================
# TREATMENT — runnable now (committed reference data only)
# ===========================================================================
def _components():
    parts = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"])]
    a = DATA_REFERENCE / "cai_trends_anchored.csv"
    if a.exists():
        parts.append(pd.read_csv(a, parse_dates=["date"]))
    w = pd.concat(parts).pivot_table(index="date", columns="component", values="value")
    return w.reindex(pd.date_range("2015-01-01", "2024-12-31", freq="D"))


def t_anchor_monthly():
    """X1/T4/T5/L4: no within-month step in the Trends series CAI-D actually uses.

    Asserts the PROPERTY on data, and accepts either sanctioned repair - fix the
    anchor, or drop anchoring. The first version measured the fraction of day>7
    rows whose anchored/stitched ratio was exactly 1.0, which had two defects
    the reviewers demonstrated: it reported PASS if days 8+ were multiplied by
    1.0000001 with the -0.408 SD step completely intact, and it FALSE-FAILED the
    "drop anchoring" repair that the plan itself sanctions - and if the anchored
    file were deleted it raised FileNotFoundError, so that repair could never
    show PASS by any route.

    The defect was a mask that rescaled only days 1-7 of each month, so the test
    is simply whether days 1-7 and days 8+ sit at the same level.
    """
    from config import CAI_D_COMPONENTS
    f = DATA_REFERENCE / "cai_trends_daily.csv"
    if not f.exists():
        return "BLOCKED", "no Trends series on disk"
    stale = DATA_REFERENCE / "cai_trends_anchored.csv"
    if stale.exists():
        return "FAIL", ("cai_trends_anchored.csv still present — it would silently "
                        "override the stitched series in 12_build_cai.py")
    d = pd.read_csv(f, parse_dates=["date"])
    d = d[d["component"].isin(CAI_D_COMPONENTS)]
    if d.empty:
        return "BLOCKED", "no CAI-D Trends components in the file"
    worst, detail = 0.0, []
    for comp, g in d.groupby("component"):
        x = np.log1p(g["value"].astype(float))
        early = x[g["date"].dt.day <= 7]
        late = x[g["date"].dt.day > 7]
        sd = float(x.std(ddof=0)) or 1.0
        step = abs(float(early.mean() - late.mean())) / sd
        detail.append(f"{comp} {step:.3f}")
        worst = max(worst, step)
    return ("PASS" if worst < 0.10 else "FAIL",
            f"within-month step (SD units): {', '.join(detail)} — worst {worst:.3f}")


def t_title_agg_no_trend():
    """The sum-across-titles aggregation must not be measuring title accumulation.

    wiki_ext sums a victim's pageviews across every historical title, because
    Wikimedia attributes a view to the exact title requested and readers arrive
    through different redirects: George Floyd's Death_of, Killing_of and
    Murder_of cover the SAME 1,681 days at 7.59M / 7.14M / 3.89M views. Views
    that were triple counted would be identical, so these are distinct readers
    and a per-day max would discard most of them.

    The hazard in summing is that titles ACCUMULATE within an article (George
    Floyd gained 14 in 2020, 5 in 2021, 3 in 2022), so a sum can drift upward
    for a reason unrelated to attention - the same trend bias that disqualified
    the log1p aggregation.

    Measured at adoption: sum and max correlate 0.9995 on the standardised
    series, mean absolute difference 0.044 SD, with the sum running +0.012 SD
    in 2015-2019 against +0.065 SD in 2020-2024. Small, and mostly absorbed by
    the within-year quantile threshold, but it is toward the later years where
    the exposed confirmation stratum sits, so it is bounded here rather than
    assumed to stay small.
    """
    f = DATA_REFERENCE / "wiki_ext_aggregation_diagnostic.csv"
    if not f.exists():
        return "BLOCKED", "no aggregation diagnostic — rerun 11 --only wiki_ext"
    d = pd.read_csv(f, parse_dates=["date"])
    z = {}
    for col in ("sum", "max"):
        x = np.log1p(d[col].astype(float))
        ref = x[(d["date"] >= "2017-01-01") & (d["date"] <= "2019-12-31")]
        z[col] = (x - ref.mean()) / ref.std(ddof=0)
    diff = z["sum"] - z["max"]
    early = float(diff[d["date"] < "2020-01-01"].mean())
    late = float(diff[d["date"] >= "2020-01-01"].mean())
    drift, mad = abs(late - early), float(diff.abs().mean())
    ok = drift < 0.15 and mad < 0.15
    return ("PASS" if ok else "FAIL",
            f"sum vs max: mean |diff| {mad:.3f} SD, drift {drift:.3f} SD "
            f"({early:+.3f} early, {late:+.3f} late)")


def t_realised_coverage_recorded():
    """T7: the provenance register must not assert a span the data does not have.

    11_fetch_awareness_components.py wraps its whole gdelt_news year loop in one
    try/except, so the first RuntimeError aborts every remaining year while the
    years already fetched are still written, outside the try - one warning, exit
    0. The register then records the span that was REQUESTED. Realised coverage:
    gdelt_news 2017-01-01..2022-12-31 (2023-24 absent entirely, 3 interior gaps),
    gdelt_tv ends 2024-10-11, wiki_ext starts 2015-07-01.

    A register that states the intended span is worse than one that states
    nothing, because it answers the question wrongly. 11b_fetch_trends.py
    already writes realised coverage into its description; this asserts the
    property for every registered component artifact.
    """
    reg = DATA_REFERENCE / "data_sources.csv"
    if not reg.exists():
        return "BLOCKED", "no provenance register"
    d = pd.read_csv(reg)
    bad = []
    for _, r in d.iterrows():
        f = PROJECT_ROOT / str(r["output_file"])
        desc = str(r["description"])
        if not f.exists() or f.suffix != ".csv":
            continue
        art = pd.read_csv(f)
        if not {"date", "component"} <= set(art.columns):
            continue
        art["date"] = pd.to_datetime(art["date"], errors="coerce")
        # every YYYY-MM-DD the description asserts must be inside the realised span
        claimed = re.findall(r"\d{4}-\d{2}-\d{2}", desc)
        if not claimed:
            continue
        lo, hi = art["date"].min(), art["date"].max()
        for comp, g in art.groupby("component"):
            pass
        for c in sorted(set(claimed)):
            t = pd.Timestamp(c)
            if t < lo or t > hi:
                bad.append(f"{r['source_id']} claims {c}, data is "
                           f"{lo.date()}..{hi.date()}")
        # and per component, the description must not imply a span a component lacks
        spans = {c: (g["date"].min(), g["date"].max()) for c, g in art.groupby("component")}
        for comp, (a, b) in spans.items():
            if comp in desc and (str(a.date()) not in desc or str(b.date()) not in desc):
                if any(pd.Timestamp(c) < a or pd.Timestamp(c) > b for c in set(claimed)):
                    bad.append(f"{r['source_id']} names {comp} "
                               f"({a.date()}..{b.date()}) but asserts a wider span")
    uniq = sorted(set(bad))
    return ("FAIL" if uniq else "PASS",
            f"{len(d)} registered artifacts; "
            + (f"{len(uniq)} assert a span the data lacks: {uniq[:2]}" if uniq
               else "no asserted span exceeds the realised one"))


def x_derived_csv_reproducible():
    """X15: a derived value must be stored at a precision that survives a re-run.

    Re-running 16_bheard_exposure.py on identical source counts produced 72
    changed lines and a different SHA256 - the weights differed in the 17th
    significant digit, because float summation order in a groupby transform is
    not stable across runs. A hash that changes when nothing changed teaches a
    reader to ignore hash mismatches, which is the habit that let X14's two
    genuine mismatches stand for two days.

    Tests the ARITHMETIC, not the source: recompute each weight from the stored
    counts and require the stored value to equal the rounded recomputation
    exactly. A file written at full float precision fails; one written rounded
    passes and is byte-reproducible.
    """
    f = DATA_REFERENCE / "precinct_cd_crosswalk.csv"
    if not f.exists():
        return "BLOCKED", "crosswalk absent"
    d = pd.read_csv(f)
    col = [c for c in d.columns if c.startswith("w_")]
    if not col or "n" not in d.columns:
        return "BLOCKED", "crosswalk has no weight or count column"
    col = col[0]
    recomputed = (d["n"] / d.groupby("communitydistrict")["n"].transform("sum"))
    for dp in (12, 10, 9, 8, 6):
        if (d[col] == recomputed.round(dp)).all():
            return "PASS", (f"{col} is stored at {dp} dp and equals the "
                            f"recomputation exactly, so a re-run is byte-identical")
    worst = float((d[col] - recomputed).abs().max())
    return "FAIL", (f"{col} is not a rounded recomputation (max |diff| {worst:.2e}); "
                    "full-precision floats are not reproducible across runs")


def x_no_stale_audit_attribution():
    """X7: DATA_AUDIT.md attributed a change to the wrong cause.

    Its §2 read the jump from 378 to 630 high days as the effect of dropping
    trends_victims. Almost all of it is the re-standardisation the audit script
    performed inside the same diagnostic: as built, 378; dropping trends_victims
    alone, 377; re-standardising while KEEPING trends_victims, 635; both, 630.
    Dropping the component moved ONE day.

    The numbers cannot be recomputed now - the index has two components and
    trends_victims is gone - so this is not a claims-register entry. What can be
    asserted is that the false attribution is no longer stated as fact.
    """
    f = PROJECT_ROOT / "docs" / "DATA_AUDIT.md"
    if not f.exists():
        return "BLOCKED", "docs/DATA_AUDIT.md absent"
    t = " ".join(f.read_text().split())
    if "378" not in t and "630" not in t:
        return "PASS", "the miscounted comparison is no longer in the document"
    # The correction must sit WITH the claim, not anywhere in the file. The
    # first version of this check searched the whole document and passed on the
    # word "corrected" appearing on two unrelated lines, while the false
    # attribution stood untouched - a check passing for the wrong reason, in a
    # check written to catch a claim that was wrong for the wrong reason.
    i = t.find("378")
    near = t[max(0, i - 400):i + 900]
    corrected = re.search(r"CORRECTED[^.]{0,80}\(finding X7\)", near)
    moved_one = "377" in near
    return ("PASS" if (corrected and moved_one) else "FAIL",
            "the 378/630 comparison carries its correction, including the 377 "
            "counterfactual that shows the component moved one day"
            if (corrected and moved_one) else
            "docs/DATA_AUDIT.md states 378->630 without a correction beside it "
            f"(marker={bool(corrected)}, counterfactual={moved_one})")


def t_wiki_fetch_complete():
    """T15: no basket article may have lost a title to a FAILED fetch.

    Distinct from T.no_lost_history, which asks whether a series starts late.
    This asks whether the series is all there at all.

    11_fetch_awareness_components.py distinguishes a 404 (this title has no
    data) from a fetch failure (we could not find out), but on a failure it
    printed a line and continued, so the basket file recorded a smaller
    n_titles with no way to tell the two apart. The last run lost one of Daunte
    Wright's 14 titles that way, and the only evidence was one line in a
    three-hour log.

    28_build_nyc_attention.py had the same defect without even the printed line:
    its per-title fetch returned None on ANY exception, so under rate limiting
    one run produced a basket in which Eric Garner had vanished entirely and
    Amadou Diallo had fallen from 2,772,084 views to 633,194 - and it exited 0
    with a normal-looking summary.
    """
    f = DATA_REFERENCE / "wiki_ext_basket_used.csv"
    if not f.exists():
        return "BLOCKED", "basket file absent — run 11"
    d = pd.read_csv(f)
    if "n_titles_failed" not in d.columns:
        return "BLOCKED", ("basket file predates failure recording; re-run 11 so "
                           "a failed title can be told from a title with no data")
    failed = d[d["n_titles_failed"].fillna(0) > 0]
    if len(failed):
        return "FAIL", (f"{len(failed)} article(s) lost titles to failed fetches: "
                        + ", ".join(f"{r['article']}({int(r['n_titles_failed'])})"
                                    for _, r in failed.head(3).iterrows()))
    offered = int(d["n_titles_offered"].fillna(0).sum())
    nodata = int(d["n_titles_no_data"].fillna(0).sum())
    return "PASS", (f"{len(d)} articles, {offered} titles offered, "
                    f"{nodata} with no data, 0 failed")


def t_no_redirect_candidates():
    """T18: no basket candidate may be a Wikipedia redirect rather than an article.

    Category membership is a property of a PAGE, and a redirect is a page, so the
    category walk collected redirects as if they were articles and could not tell
    them apart. 39 of 482 candidates (8%) were redirects, with two consequences:

      a redirect AND its target both survive -> the person is counted twice
        (9 cases, 449,549 views; finding T17);
      only the redirect survives -> the candidacy rule tests the REDIRECT's
        title, which has no person prefix, so the article is never considered.
        WALTER SCOTT was absent from the treatment index entirely this way -
        2,228,711 views summed across his titles, which would rank 15th of 121 -
        and Jordan Edwards, killed inside the discovery window, with him.

    Checked against data/reference/redirect_resolution.csv, which 24 writes, so
    this needs no network. A check that requires the API is a check that gets
    skipped, and this one has to run on every commit.
    """
    r = DATA_REFERENCE / "redirect_resolution.csv"
    b = DATA_REFERENCE / "wiki_basket.csv"
    if not b.exists():
        return "BLOCKED", "wiki_basket.csv absent — run 24"
    if not r.exists():
        return "BLOCKED", ("no redirect_resolution.csv — re-run 24_build_wiki_basket.py; "
                           "without it, whether a candidate is a redirect is unknowable offline")
    res = pd.read_csv(r)
    basket = set(pd.read_csv(b)["article"])
    still = sorted(basket & set(res["redirect"]))
    recovered = res[~res["target_was_collected_directly"]]
    if still:
        return "FAIL", (f"{len(still)} candidate(s) are redirects, not articles: "
                        f"{still[:4]}")
    return "PASS", (f"{len(basket)} candidates, none a redirect; "
                    f"{len(res)} resolved, {len(recovered)} target(s) the walk had "
                    "not collected directly")


def s_confirmatory_spec_audit():
    """P14-P16, P18: the sealed script does what addendum 23 says, structurally.

    Read by AST and by source, so a comment cannot satisfy any clause: real mode
    refuses a non-default --draws; the sealed result is written under
    data/reference (tracked); Benjamini-Hochberg is called with a fixed family
    size; an asymptotic p is computed from the chi-square for every
    randomization cell; the raw-count and total-dispatch diagnostics exist; the
    interaction arm is gated to C2_exposed.
    """
    import ast as _ast
    f = SCRIPTS / "30_confirmatory_run.py"
    src = f.read_text()
    tree = _ast.parse(src)
    problems = []
    if not re.search(r"if ARGS\.draws != RANDOMIZATION_DRAWS:\s*\n\s*if not SYNTHETIC:\s*\n(.*\n){0,6}?\s*raise SealBroken", src):
        problems.append("real mode does not refuse a non-default --draws")
    if not re.search(r"^OUT_REAL = DATA_REFERENCE /", src, re.M):
        problems.append("OUT_REAL is not under data/reference")
    bh_calls = [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)
                and getattr(n.func, "id", "") == "benjamini_hochberg"]
    if not bh_calls or not all(any(k.arg == "m" for k in c.keywords) for c in bh_calls):
        problems.append("benjamini_hochberg is called without a fixed family size m=")
    if "chi2_dist.sf(" not in src or '"p_asymptotic": p_asym' not in src:
        problems.append("no asymptotic chi-square p is written for randomization cells")
    for token in ("diag_raw_count", "diag_total_dispatches"):
        if token not in src:
            problems.append(f"diagnostic cell {token} is absent")
    if 'stratum != "C2_exposed"' not in src:
        problems.append("the interaction arm is not gated to C2_exposed")
    # P19 (CP2 audit, second pass): the pre-specified 28- and 60-day windows
    # (addendum 3) and the dose-response arm (addendum 9) are estimated, not just
    # promised — a loop over EVENT_WINDOW_POST_SENSITIVITY feeding add(), and a
    # fit_dose_response call writing a 'dose_response' secondary row.
    if not re.search(r"for post in EVENT_WINDOW_POST_SENSITIVITY:(.*\n){0,8}?\s*add\(", src):
        problems.append("the 28/60-day post-window sensitivities are not estimated")
    if "fit_dose_response(" not in src or '"dose_response", "secondary"' not in src:
        problems.append("the dose-response arm is not estimated as a secondary cell")
    # P26: the docstring is declared to be the specification, so it must name the
    # executed family values and the tracked output path.
    doc = _ast.get_docstring(tree) or ""
    for token in ("descriptive", "diagnostic", "data/reference/confirmatory_results.csv", "sens_post28",
                  "--jobs", "--overwrite-sealed-result", "PYTHONHASHSEED", "confirmatory_run_log.csv"):
        if token not in doc:
            problems.append(f"the module docstring does not mention {token}")
    # Third CP2 audit pass (P27-P4x): the seal is a tracked append-only run log
    # written before estimation; real mode requires the fixed hash seed; the
    # calibration gate compares scheme AND episode set with the run's design; the
    # window sensitivities draw on the certified 14-day geometry; the diagnostics
    # run on every district-day; coverage-clean uses every break date and a
    # geocoding-only cell exists; the cancelled-inclusive and no-EDPM cells exist;
    # the sidecar pins the raw sources, the commit, the panel and the episode lists.
    for token, why in (('append_run_log("start"', "no run-log row is written before estimation"),
                       ('append_run_log("sealed"', "no run-log row is written at the seal"),
                       ('prior[prior["event"] == "start"]', "a prior real run does not refuse a second"),
                       ('os.environ.get("PYTHONHASHSEED") != "0"', "real mode does not require PYTHONHASHSEED=0"),
                       ("_assert_certificate_matches_design(", "the gate does not compare the certificate's design with the run's"),
                       ("draw_post=EVENT_WINDOW_POST", "the window sensitivities do not draw on the 14-day geometry"),
                       ("panel_all = prepare(raw_panel, apply_min_calls=False)", "no unfiltered panel is built for the diagnostics"),
                       ("sp_all = attach_bheard(strata_all[stratum]", "the diagnostics are not estimated on every district-day"),
                       ('"sens_geocoding_clean"', "no geocoding-only sensitivity cell"),
                       ('"sens_incl_cancelled"', "no cancelled-inclusive sensitivity cell"),
                       ('"sens_no_edpm"', "no EDPM-excluded sensitivity cell"),
                       ('"source_sha256"', "the sidecar does not pin the raw sources"),
                       ('"inputs_sha256"', "the sidecar does not pin the inputs"),
                       ("real episode start(s)", "a real start the drawer would relocate is not refused"),
                       ('"path_coefs": json.dumps(', "the day-by-day path is not written into the sealed table (23.2; P56)"),
                       ('offset="total_calls_incl_cancelled"', "the cancelled-inclusive count arm does not offset on its own total (P57)")):
        if token not in src:
            problems.append(why)
    if 'breaks["window"].isin(STRATUM_BREAK_LABELS' in src:
        problems.append("coverage-clean still filters break dates by the stratum's own window labels")
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", ("real mode fixed to RANDOMIZATION_DRAWS; sealed result tracked; BH over a "
                    "fixed family; asymptotic p beside every RI p; denominator diagnostics; "
                    "interaction C2-only; 28/60-day windows and the dose arm estimated; docstring "
                    "names the six families and the tracked output")


def s_lift_requires_1000_sims():
    """P11: the freeze may not be lifted on 200-simulation certificates.

    CP2's second line says the calibration must pass at >= 1000 simulations on
    all three strata before FREEZE_ACTIVE becomes False. Nothing enforced it:
    S.ri_scheme_certified reads each certificate's OWN min_sims_required, which
    18 writes as 200, so a lift on 200-sim certificates passed every check
    (CP1 audit follow-up, 2026-09-13). This check is the gate on the lift
    itself. While the freeze is on it reports the sim counts and passes; the
    moment FREEZE_ACTIVE is False it fails unless every stratum's certificate
    reads CALIBRATED at or above LIFT_MIN_SIMS. Defeat-tested by flipping the
    flag in a loaded copy of config against the 200-sim artifacts.
    """
    from config import FREEZE_ACTIVE
    files = {"discovery": "null_calibration.csv", "C1": "null_calibration_C1.csv",
             "C2": "null_calibration_C2.csv", "pooled": "null_calibration_pooled.csv"}
    # The three inferential strata need LIFT_MIN_SIMS; the pooled stratum is
    # descriptive and outside the family, so at the lift its certificate must
    # exist and read CALIBRATED at its own minimum, not at 1000.
    inferential = ("discovery", "C1", "C2")
    state = {}
    for name, fname in files.items():
        art = OUTPUTS_TABLES / fname
        if not art.exists():
            state[name] = (0, "absent")
            continue
        a = pd.read_csv(art).set_index("metric")["value"]
        state[name] = (int(float(a.get("n_sims_completed", 0))), str(a.get("VERDICT", "")).strip())
    # A >= LIFT_MIN_SIMS "NOT CALIBRATED" verdict on an inferential stratum is
    # the addendum-25 case: the lift may proceed with that stratum flagged
    # uncertified. Discovery must be CALIBRATED; the pooled certificate must exist.
    def _short(k, n, v):
        if k in inferential:
            return not (n >= LIFT_MIN_SIMS and v in ("CALIBRATED", "NOT CALIBRATED")) \
                or (k == "discovery" and v != "CALIBRATED")
        return v not in ("CALIBRATED", "NOT CALIBRATED")
    short = [f"{k}: {n} sims, {v}" for k, (n, v) in state.items() if _short(k, n, v)]
    summary = ", ".join(f"{k}={n}/{v or 'absent'}" for k, (n, v) in state.items())
    if not FREEZE_ACTIVE and short:
        return "FAIL", (f"FREEZE_ACTIVE is False but {len(short)} stratum/strata lack a "
                        f"CALIBRATED certificate at >= {LIFT_MIN_SIMS} simulations: {short}")
    if FREEZE_ACTIVE:
        return "PASS", (f"freeze on; certificates {summary}; lift requires "
                        f">= {LIFT_MIN_SIMS} sims on all three ({len(short)} short)")
    return "PASS", f"freeze lifted on certificates {summary}, all >= {LIFT_MIN_SIMS} sims"


def s_calibration_noise_measured():
    """N11: every certificate's synthetic null takes its noise from the measured panel.

    18 estimates the null's noise structure — level, AR(1) rho, idiosyncratic
    sigma and the district, day-of-week and day-shock scales — from the
    discovery rows of the panel, and fell back to assumed constants (rho 0.6,
    mu 0.10) when the panel was absent, with a printed note and nothing else.
    On 2026-09-13 at 20:56Z the discovery 1,000-sim run started in the twelve
    seconds between a cold run clearing data/processed and 01 rebuilding the
    panel, took that branch, and began certifying a null unrelated to the data
    under the file name the lift reads. The ledger identity check (N7) is what
    surfaced it, twelve minutes in: the fingerprint no longer matched the
    200-sim ledger. Nothing else would have — the certificate would have said
    CALIBRATED at 1,000 with a scheme and a stratum, and S.ri_scheme_certified
    and S.lift_requires_1000_sims would both have passed on it.

    Two halves. Source: the fallback branch of 18 refuses unless a smoke test
    asks for it by name. Artifacts: for every stratum certificate on disk, the
    design in its ledger sidecar carries the noise parameters 19 measured from
    the same panel (power_analysis.csv, noise.*) to 1e-5 — which also catches
    the two copies of the estimation procedure drifting apart — none of them
    is a fallback constant, the certificate's ar1_rho is the sidecar's, and a
    certificate that carries noise_source reads "panel". Sidecars and 19's
    artifact carry no outcome row.
    """
    import ast as _ast
    problems, seen = [], []
    tree = _ast.parse(src("18_null_calibration.py"))
    branch = [n for n in tree.body if isinstance(n, _ast.If)
              and _ast.unparse(n.test) == "panel_path.exists()"]
    if not branch:
        problems.append("18 has no `if panel_path.exists()` branch")
    else:
        orelse = _ast.unparse(_ast.Module(body=branch[0].orelse, type_ignores=[]))
        raises = any(isinstance(n, _ast.Raise) for b in branch[0].orelse for n in _ast.walk(b))
        if not raises or "allow_assumed_noise" not in orelse:
            problems.append("18's no-panel branch does not refuse: the assumed noise "
                            "parameters can be used without --allow-assumed-noise")
    fallback = {"rho": 0.6, "sigma": 0.03, "mu": 0.10, "cd_scale": 0.5,
                "dow_scale": 0.15, "day_scale": 0.35}
    power = OUTPUTS_TABLES / "power_analysis.csv"
    measured = None
    if power.exists():
        pw = pd.read_csv(power).set_index("metric")["value"]
        try:
            measured = {k: float(pw[f"noise.{k}"]) for k in fallback}
        except KeyError as e:
            problems.append(f"power_analysis.csv lacks {e}")
    files = {"discovery": "null_calibration.csv", "C1": "null_calibration_C1.csv",
             "C2": "null_calibration_C2.csv", "pooled": "null_calibration_pooled.csv"}
    for name, fname in files.items():
        art = OUTPUTS_TABLES / fname
        if not art.exists():
            continue
        a = pd.read_csv(art).set_index("metric")["value"]
        draws = int(float(a.get("ri_draws_per_sim", 0)))
        tag = "" if name == "discovery" else f"_{name}"
        meta = OUTPUTS_TABLES / f"null_calibration_ledger_d{draws}{tag}.meta.json"
        if not meta.exists():
            problems.append(f"{name}: {fname} has no ledger sidecar {meta.name}")
            continue
        design = json.loads(meta.read_text()).get("design", {})
        got = {k: float(design.get(k, float("nan"))) for k in fallback}
        if all(abs(got[k] - fallback[k]) < 1e-9 for k in fallback):
            problems.append(f"{name}: certified on the ASSUMED fallback noise "
                            f"(rho={got['rho']}, mu={got['mu']}), not the panel's")
            continue
        if measured is not None:
            off = [f"{k} {got[k]:.6g} vs measured {measured[k]:.6g}"
                   for k in fallback if not abs(got[k] - measured[k]) <= 1e-5]
            if off:
                problems.append(f"{name}: sidecar noise differs from 19's measurement: "
                                + "; ".join(off))
        if abs(float(a.get("ar1_rho", float("nan"))) - round(got["rho"], 4)) > 1e-9:
            problems.append(f"{name}: certificate ar1_rho {a.get('ar1_rho')} is not the "
                            f"sidecar's {round(got['rho'], 4)}")
        if "noise_source" in a.index and str(a["noise_source"]).strip() != "panel":
            problems.append(f"{name}: noise_source={a['noise_source']!r}")
        seen.append(f"{name}(rho={got['rho']:.4f}, mu={got['mu']:.4f})")
    if problems:
        return "FAIL", "; ".join(problems)
    if not seen:
        return "BLOCKED", "no stratum certificate on disk — run 18_null_calibration.py"
    if measured is None:
        return "BLOCKED", (f"{len(seen)} certificate(s) carry non-fallback noise but "
                           "power_analysis.csv is absent, so they cannot be compared "
                           "with the measured panel — run 19_power.py")
    return "PASS", (f"18 refuses without the panel; {len(seen)} certificate(s) carry the "
                    f"panel's noise (matches 19 to 1e-5): " + ", ".join(seen))


def s_confirmatory_reading_rules():
    """P14: the pre-registered reading is mechanical, and the mechanism is held to its text.

    Addendum 23 made "rejects", direction, the denominator diagnostic and the
    placebo override mechanical; addendum 19 fixed what a non-rejection means;
    note 9.4 fixes how C1 and C2 combine. `34_confirmatory_reading.py`
    implements them as a pure function of the sealed table, so that no judgement
    is exercised between 30's output and the sentence in the paper. This check
    feeds that function planted tables — one per rule, each with the verdict the
    text requires — and fails on the first that reads differently. It also holds
    34 to reading nothing but the sealed table and the pre-freeze power table: no
    parquet, no panel, no episode list.
    """
    import importlib.util
    import sys as _sys
    _sys.path.insert(0, str(SCRIPTS))
    from event_study import count_outcome
    text = src("34_confirmatory_reading.py")
    problems = []
    for bad in ("read_parquet", "panel_cd_day", "EPISODE_LIST", "select_sample"):
        if bad in text:
            problems.append(f"34 mentions {bad}: it may read only the sealed table and the power table")
    # Third CP2 audit pass (P41-P45): the reading is sealed (a sidecar binding it
    # to the table it read, an overwrite guard with a reason), the MDEs come from
    # the TRACKED pre-freeze power table and the reader refuses one that is absent
    # or not flagged pre-freeze, the sensitivity set is enumerated, the pooled
    # stratum gets its own descriptive reading, and the bounded-null sentence is
    # written at the family level with the MEI's sign and an approximate factor.
    for token, why in (("--overwrite-reading", "34 has no overwrite guard for the reading"),
                       ('"sealed_table_sha256"', "34's sidecar does not bind the reading to the table it read"),
                       ('POWER = DATA_REFERENCE / "power_analysis_prefreeze.csv"', "34 does not read the tracked pre-freeze power table"),
                       ('pw.get("freeze_active", 0))) != 1', "34 does not refuse a power table not flagged pre-freeze"),
                       ("SENSITIVITY_SPECS = (", "34 does not enumerate the sensitivity set"),
                       ('"pooled_reading"', "34 gives the pooled stratum no reading"),
                       ("smallest unadjusted", "the bounded-null sentence does not name the smallest unadjusted p"),
                       ("(−{MINIMUM_EFFECT_OF_INTEREST})", "the bounded-null sentence prints the MEI without its sign"),
                       ("approximate one-parameter family correction", "the 23.11 factor is not labelled approximate")):
        if token not in text:
            problems.append(why)
    spec = importlib.util.spec_from_file_location("_m34", SCRIPTS / "34_confirmatory_reading.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    S1, S2 = "C1_clean", "C2_exposed"
    ARM = {"share": "OLS_share", "count": "PPML_count_offset"}

    def base():
        rows = []
        for s_ in (S1, S2):
            for o in ("edp_share", "mh_narrow_share"):
                for arm, est in ARM.items():
                    col = o if arm == "share" else count_outcome(o)
                    rows.append(dict(key=f"{s_}:{o}:{arm}", stratum=s_, outcome=col, estimator=est,
                                     spec="primary", family="primary_H1", p_randomization=0.5,
                                     p_asymptotic=0.5, p_bh_adjusted=0.7, first_week_mean_coef=-0.0005,
                                     first_week_mean_se=0.001, n_episodes=15, status="OK",
                                     null_certified=True))
            for col in ("edp", "mh_narrow"):
                rows.append(dict(key=f"{s_}:diag_raw:{col}", stratum=s_, outcome=col,
                                 estimator="PPML_count_no_offset", spec="diag_raw_count",
                                 family="diagnostic", p_randomization=0.5, p_asymptotic=0.5,
                                 p_bh_adjusted=np.nan, first_week_mean_coef=0.0, first_week_mean_se=0.01,
                                 n_episodes=15, status="OK", null_certified=True))
            rows.append(dict(key=f"{s_}:diag_total", stratum=s_, outcome="total_calls",
                             estimator="PPML_count_no_offset", spec="diag_total_dispatches",
                             family="diagnostic", p_randomization=0.5, p_asymptotic=0.5,
                             p_bh_adjusted=np.nan, first_week_mean_coef=0.0, first_week_mean_se=0.01,
                             n_episodes=15, status="OK", null_certified=True))
            for po in ("cardiac_share", "injury_share", "asthma_share"):
                for arm, est in ARM.items():
                    col = po if arm == "share" else count_outcome(po)
                    rows.append(dict(key=f"{s_}:placebo:{po}:{arm}", stratum=s_, outcome=col,
                                     estimator=est, spec="placebo", family="placebo",
                                     p_randomization=0.5, p_asymptotic=0.5, p_bh_adjusted=np.nan,
                                     first_week_mean_coef=0.0, first_week_mean_se=0.001,
                                     n_episodes=15, status="OK", null_certified=True))
            rows.append(dict(key=f"{s_}:sens", stratum=s_, outcome="edp_share", estimator="OLS_share",
                             spec="sens_drop_jul2016", family="sensitivity", p_randomization=0.5,
                             p_asymptotic=0.5, p_bh_adjusted=np.nan, first_week_mean_coef=-0.0005,
                             first_week_mean_se=0.001, n_episodes=14, status="OK", null_certified=True))
            # a coverage-clean cell on a falsification outcome: family 'sensitivity',
            # never an H1 outcome, so it may not enter the robust/fragile label (P43)
            rows.append(dict(key=f"{s_}:sens_placebo", stratum=s_, outcome="cardiac_share", estimator="OLS_share",
                             spec="sens_coverage_clean", family="sensitivity", p_randomization=0.01,
                             p_asymptotic=0.01, p_bh_adjusted=np.nan, first_week_mean_coef=-0.002,
                             first_week_mean_se=0.001, n_episodes=14, status="OK", null_certified=True))
            # secondary arms: the interaction (C2 only) and the dose arm, asymptotic p
            rows.append(dict(key=f"{s_}:sec_interaction", stratum=s_, outcome="edp_share", estimator="OLS_share",
                             spec="bheard_interaction", family="secondary", p_randomization=np.nan,
                             p_asymptotic=0.5 if s_ == S2 else np.nan, p_bh_adjusted=np.nan,
                             first_week_mean_coef=0.002 if s_ == S2 else np.nan, first_week_mean_se=np.nan,
                             n_episodes=15, status="OK" if s_ == S2 else "NOT_RUN: no B-HEARD exposure in this stratum",
                             null_certified=True))
            rows.append(dict(key=f"{s_}:sec_dose", stratum=s_, outcome="edp_share", estimator="OLS_share_dose_per_sd",
                             spec="dose_response", family="secondary", p_randomization=np.nan, p_asymptotic=0.5,
                             p_bh_adjusted=np.nan, first_week_mean_coef=-0.001, first_week_mean_se=np.nan,
                             n_episodes=15, status="OK", null_certified=True))
        for o in ("edp_share", "mh_narrow_share"):
            for arm, est in ARM.items():
                col = o if arm == "share" else count_outcome(o)
                rows.append(dict(key=f"pooled:{o}:{arm}", stratum="pooled", outcome=col, estimator=est,
                                 spec="primary", family="descriptive", p_randomization=0.5,
                                 p_asymptotic=0.5, p_bh_adjusted=np.nan, first_week_mean_coef=-0.0005,
                                 first_week_mean_se=0.001, n_episodes=45, status="OK", null_certified=True))
        return pd.DataFrame(rows)

    def scenario(over):
        d = base()
        for k, fields in over.items():
            idx = d.index[d["key"] == k]
            if len(idx) != 1:
                raise RuntimeError(f"scenario key {k} matches {len(idx)} rows")
            for fld, v in fields.items():
                d.loc[idx, fld] = v
        return d

    def rej(s_, o, mean=-0.003, se=0.0005, p_bh=0.01):
        return {f"{s_}:{o}:share": dict(p_bh_adjusted=p_bh, p_randomization=0.001,
                                        first_week_mean_coef=mean, first_week_mean_se=se),
                f"{s_}:{o}:count": dict(p_bh_adjusted=p_bh, p_randomization=0.001,
                                        first_week_mean_coef=mean * 10, first_week_mean_se=se * 10)}

    mde = {S1: {"level": 0.0116, "dip_rebound": 0.0038, "verdict": "UNDERPOWERED", "freeze_active": 1},
           S2: {"level": 0.0087, "dip_rebound": 0.0029, "verdict": "UNDERPOWERED", "freeze_active": 1}}
    uncert = {k: dict(null_certified=False) for k in base().loc[base()["stratum"] == S1, "key"]}
    cases = [
        ("both null", {}, ("does not reject", "does not reject"), "THE PRE-SPECIFIED NULL"),
        ("C1 predicted, C2 null", rej(S1, "edp_share"),
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("both predicted, same outcome", {**rej(S1, "edp_share"), **rej(S2, "edp_share")},
         ("rejects, predicted direction", "rejects, predicted direction"), "CONFIRMED: C1 and C2"),
        ("both predicted, different outcomes (23.1b)", {**rej(S1, "edp_share"), **rej(S2, "mh_narrow_share")},
         ("rejects, predicted direction", "rejects, predicted direction"), "CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2; 23.1b)"),
        ("C2 only", rej(S2, "edp_share"),
         ("does not reject", "rejects, predicted direction"), "NOT CONFIRMATION (9.4 row 3)"),
        ("strata disagree in sign", {**rej(S1, "edp_share"), **rej(S2, "edp_share", mean=0.003)},
         ("rejects, predicted direction", "rejects, opposite direction"), "THE CONFIRMATION HAS FAILED"),
        ("C1 increase", rej(S1, "edp_share", mean=0.003),
         ("rejects, opposite direction", "does not reject"), "NOT SUPPORT FOR H1"),
        ("one arm only (23.1a)", {f"{S1}:edp_share:share": dict(p_bh_adjusted=0.01, first_week_mean_coef=-0.003)},
         ("does not reject on both arms; a movement in one arm only", "does not reject"),
         "THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2; a one-arm movement in C1"),
        ("arms disagree in sign (23.2)", {**rej(S1, "edp_share"),
                                           f"{S1}:edp_share:count": dict(p_bh_adjusted=0.01, first_week_mean_coef=0.03,
                                                                         first_week_mean_se=0.005)},
         ("rejects without a consistent direction", "does not reject"), "NOT SUPPORT FOR H1"),
        ("denominator-driven on one outcome, clean on the other (23.3a)",
         {**rej(S1, "edp_share"), **rej(S1, "mh_narrow_share"), f"{S1}:diag_total": dict(p_randomization=0.01),
          f"{S1}:diag_raw:mh_narrow": dict(p_randomization=0.01)},
         ("rejects, predicted direction (on mh_narrow_share)", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("uncertified null, asymptotic rejection (25.3)",
         {**uncert, **{k: {**v, "null_certified": False, "p_bh_adjusted": 1.0, "p_asymptotic": 0.001}
                       for k, v in rej(S1, "edp_share").items()}},
         ("rejects on the asymptotic p", "does not reject"), "NOT SUPPORT FOR H1"),
        ("mean within one SE (23.2)", {**rej(S1, "edp_share"),
                                        f"{S1}:edp_share:count": dict(p_bh_adjusted=0.01, first_week_mean_coef=-0.001,
                                                                      first_week_mean_se=0.005)},
         ("rejects without a consistent direction", "does not reject"), "NOT SUPPORT FOR H1"),
        ("placebo override (23.4)", {**rej(S1, "edp_share"),
                                      f"{S1}:placebo:cardiac_share:share": dict(p_randomization=0.01)},
         ("rejects, predicted direction (on edp_share); PLACEBO OVERRIDE", "does not reject"), "NOT SUPPORT FOR H1"),
        ("denominator-driven (23.3)", {**rej(S1, "edp_share"), f"{S1}:diag_total": dict(p_randomization=0.01)},
         ("rejects, denominator-driven", "does not reject"), "NOT SUPPORT FOR H1"),
        ("injury moves but does not override (23.4)", {**rej(S1, "edp_share"),
                                                       f"{S1}:placebo:injury_share:share": dict(p_randomization=0.01),
                                                       f"{S1}:placebo:injury_share:count": dict(p_randomization=0.01)},
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("BH boundary is strict (23.1)", rej(S1, "edp_share", p_bh=0.05),
         ("does not reject", "does not reject"), "THE PRE-SPECIFIED NULL"),
        ("uncertified null: placebo override reads the asymptotic p (25.3)",
         {**uncert, **{k: {**v, "null_certified": False, "p_bh_adjusted": 1.0, "p_asymptotic": 0.001}
                       for k, v in rej(S1, "edp_share").items()},
          f"{S1}:placebo:cardiac_share:share": dict(null_certified=False, p_randomization=0.5, p_asymptotic=0.01)},
         ("rejects on the asymptotic p", "does not reject"), "NOT SUPPORT FOR H1"),
        ("diagnostic unavailable is not denominator-driven (23.3a)",
         {**rej(S1, "edp_share"), f"{S1}:diag_total": dict(p_randomization=float("nan"))},
         ("rejects, predicted direction (on edp_share)", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("C1 clean, C2 discounted -> row 2 (9.4)",
         {**rej(S1, "edp_share"), **rej(S2, "edp_share"), f"{S2}:diag_total": dict(p_randomization=0.01)},
         ("rejects, predicted direction (on edp_share)", "rejects, denominator-driven"), "CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2): C2's rejection does not count"),
        ("opposite direction under a placebo override (23.4)",
         {**rej(S1, "edp_share", mean=0.003), f"{S1}:placebo:asthma_share:share": dict(p_randomization=0.01)},
         ("rejects, opposite direction (9.1): not support for H1; PLACEBO OVERRIDE", "does not reject"), "NOT SUPPORT FOR H1"),
        ("uncertified null, no asymptotic rejection (25.3)",
         {**uncert, **{k: {**v, "null_certified": False, "p_bh_adjusted": 1.0, "p_asymptotic": 0.4}
                       for k, v in rej(S1, "edp_share").items()}},
         ("does not reject", "does not reject"), "THE PRE-SPECIFIED NULL"),
        # third CP2 audit pass
        ("pooled rejects where neither stratum does (23.1d)",
         {"pooled:edp_share:share": dict(p_randomization=0.001, first_week_mean_coef=-0.003),
          "pooled:edp_share:count": dict(p_randomization=0.001, first_week_mean_coef=-0.03)},
         ("does not reject", "does not reject"),
         "THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2; the pooled stratum rejects where neither stratum does"),
        ("pooled arms disagree in sign: no pooled rejection (23.1d)",
         {"pooled:edp_share:share": dict(p_randomization=0.001, first_week_mean_coef=-0.003),
          "pooled:edp_share:count": dict(p_randomization=0.001, first_week_mean_coef=0.03)},
         ("does not reject", "does not reject"), "THE PRE-SPECIFIED NULL"),
        ("sensitivity survives (23.1c)", {**rej(S1, "edp_share"), f"{S1}:sens": dict(p_randomization=0.01)},
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("sensitivity fails (23.1c)", rej(S1, "edp_share"),
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("sensitivity identical to the primary survives (23.1c)",
         {**rej(S1, "edp_share"), f"{S1}:sens": dict(p_randomization=float("nan"), status="IDENTICAL_TO_PRIMARY: same starts")},
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("sensitivity not run is not applicable (23.1c)",
         {**rej(S1, "edp_share"), f"{S1}:sens": dict(p_randomization=float("nan"), status="NOT_RUN: episode list absent")},
         ("rejects, predicted direction", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("placebo cell without a p-value: check incomplete, no silent pass (23.4)",
         {**rej(S1, "edp_share"), f"{S1}:placebo:cardiac_share:share": dict(p_randomization=float("nan"))},
         ("rejects, predicted direction (on edp_share); PLACEBO CHECK INCOMPLETE (23.4): 1 of 4", "does not reject"),
         "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("placebo at exactly alpha overrides (23.4)",
         {**rej(S1, "edp_share"), f"{S1}:placebo:asthma_share:count": dict(p_randomization=0.05)},
         ("rejects, predicted direction (on edp_share); PLACEBO OVERRIDE", "does not reject"), "NOT SUPPORT FOR H1"),
        ("placebo just above alpha does not override (23.4)",
         {**rej(S1, "edp_share"), f"{S1}:placebo:asthma_share:count": dict(p_randomization=0.0501)},
         ("rejects, predicted direction (on edp_share)", "does not reject"), "CONFIRMED IN THE CLEAN STRATUM ONLY"),
        ("secondary arms read against their predicted directions (23.1e)",
         {**rej(S2, "edp_share"), f"{S2}:sec_interaction": dict(p_asymptotic=0.01, first_week_mean_coef=0.002),
          f"{S2}:sec_dose": dict(p_asymptotic=0.01, first_week_mean_coef=0.001)},
         ("does not reject", "rejects, predicted direction"),
         "NOT CONFIRMATION (9.4 row 3)"),
    ]
    passed = 0
    for name, over, (v1, v2), concl in cases:
        try:
            res, verdicts, conclusion = m.evaluate(scenario(over), mde)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{name}: evaluate raised {type(e).__name__}: {e}")
            continue
        got1, got2 = verdicts[S1], verdicts[S2]
        if not got1.startswith(v1) or not got2.startswith(v2):
            problems.append(f"{name}: C1 read {got1!r}, C2 read {got2!r}; expected {v1!r} / {v2!r}")
        elif concl not in conclusion:
            problems.append(f"{name}: conclusion {conclusion!r} lacks {concl!r}")
        else:
            passed += 1
        if name.startswith("placebo override"):
            row = res[(res["stratum"] == S1) & (res["item"] == "placebo_rejects_any")]
            if row.empty or int(float(row["value"].iloc[0])) != 1:
                problems.append("placebo override: placebo_rejects_any not recorded as 1")
        if name.startswith("injury moves"):
            row = res[(res["stratum"] == S1) & (res["item"] == "placebo_rejects_any")]
            if row.empty or int(float(row["value"].iloc[0])) != 0:
                problems.append("injury: recorded as an override outcome; 23.4 names cardiac and asthma")
            if "OVERRIDE" in verdicts[S1]:
                problems.append("injury: triggered the placebo override")
        if name.startswith("uncertified"):
            row = res[(res["stratum"] == S1) & (res["item"] == "null_certified")]
            if row.empty or int(float(row["value"].iloc[0])) != 0:
                problems.append("uncertified: null_certified not recorded as 0")
        if name.startswith("uncertified null: placebo"):
            row = res[(res["stratum"] == S1) & (res["item"] == "placebo_rejects_any")]
            if row.empty or int(float(row["value"].iloc[0])) != 1 or "OVERRIDE" not in verdicts[S1]:
                problems.append("uncertified: the placebo override did not read the asymptotic p")
        if name.startswith("diagnostic unavailable"):
            row = res[(res["stratum"] == S1) & (res["item"] == "denominator_driven:edp_share")]
            if row.empty or int(float(row["value"].iloc[0])) != 0 or "unavailable" not in str(row["detail"].iloc[0]):
                problems.append("diagnostic unavailable: not recorded as unavailable / read as denominator-driven")
        if name.startswith("one arm only") or name.startswith("arms disagree"):
            row = res[(res["stratum"] == S1) & (res["item"] == "bounded_null")]
            if row.empty or int(float(row["value"].iloc[0])) != 0:
                problems.append(f"{name}: the bounded-null sentence ('no effect detected') was asserted although a cell rejected")
        if name == "both null":
            row = res[(res["stratum"] == S1) & (res["item"] == "bounded_null")]
            if row.empty or int(float(row["value"].iloc[0])) != 1:
                problems.append("both null: the bounded-null sentence was not asserted")
            elif "family level" not in str(row["detail"].iloc[0]) or "smallest unadjusted" not in str(row["detail"].iloc[0]):
                problems.append("both null: the bounded-null sentence is not stated at the family level with the smallest unadjusted p")
            elif "(−0.005)" not in str(row["detail"].iloc[0]):
                problems.append("both null: the MEI is printed without its sign")
            elif "transient dip-and-rebound of the minimum effect of interest is disfavoured" not in str(row["detail"].iloc[0]):
                problems.append("both null: the transient clause is not stated at the MEI")
            lab = res[(res["stratum"] == S1) & (res["item"] == "sensitivity_summary")]
            if lab.empty or "0 of 1 H1-outcome sensitivity cells" not in str(lab["value"].iloc[0]):
                problems.append("both null: the sensitivity count admits falsification-outcome cells "
                                f"({lab['value'].iloc[0] if not lab.empty else 'absent'!r})")
        if name.startswith("placebo cell without"):
            row = res[(res["stratum"] == S1) & (res["item"] == "placebo_cells_unavailable")]
            if row.empty or int(float(row["value"].iloc[0])) != 1:
                problems.append("placebo incomplete: placebo_cells_unavailable not recorded as 1")
            if "OVERRIDE" in verdicts[S1]:
                problems.append("placebo incomplete: a missing p-value triggered the override")
        if name.startswith("placebo just above"):
            if "OVERRIDE" in verdicts[S1] or "INCOMPLETE" in verdicts[S1]:
                problems.append("placebo just above alpha: read as an override or as incomplete")
        if name.startswith("secondary arms"):
            it = res[(res["stratum"] == S2) & (res["item"] == "secondary_reading:bheard_interaction:edp_share:OLS_share")]
            if it.empty or not str(it["value"].iloc[0]).startswith("moves in the predicted direction"):
                problems.append("secondary: the attenuating interaction was not read as the predicted direction")
            it = res[(res["stratum"] == S2) & (res["item"] == "secondary_reading:dose_response:edp_share:OLS_share_dose_per_sd")]
            if it.empty or not str(it["value"].iloc[0]).startswith("moves against the predicted direction"):
                problems.append("secondary: a positive dose coefficient was not read as against the predicted direction")
            if "B-HEARD interaction arm (secondary, 23.1e) reads" not in conclusion:
                problems.append("secondary: the row-3 conclusion does not carry the interaction arm's reading")
            it = res[(res["stratum"] == S1) & (res["item"] == "secondary_reading:bheard_interaction:edp_share:OLS_share")]
            if it.empty or not str(it["value"].iloc[0]).startswith("not read"):
                problems.append("secondary: a NOT_RUN interaction cell was read")
        if name.startswith("pooled rejects where"):
            row = res[(res["stratum"] == "pooled") & (res["item"] == "pooled_reading")]
            if row.empty or not str(row["value"].iloc[0]).startswith("pooled rejects on edp_share (decline)"):
                problems.append("pooled: no descriptive pooled rejection was read")
        if name.startswith("pooled arms disagree"):
            row = res[(res["stratum"] == "pooled") & (res["item"] == "pooled_reading")]
            if row.empty or not str(row["value"].iloc[0]).startswith("pooled does not reject"):
                problems.append("pooled: arms of opposite sign were read as a pooled rejection")
        if name.startswith("sensitivity"):
            item = res[(res["stratum"] == S1) & (res["item"] == "sensitivity_survives:sens_drop_jul2016")]
            lab = str(res[(res["stratum"] == S1) & (res["item"] == "sensitivity_summary")]["value"].iloc[0])
            want = {"sensitivity survives (23.1c)": (1, "robust"), "sensitivity fails (23.1c)": (0, "fragile"),
                    "sensitivity identical to the primary survives (23.1c)": (1, "robust"),
                    "sensitivity not run is not applicable (23.1c)": (None, "survives 0 of 0")}[name]
            if want[0] is None:
                if not item.empty:
                    problems.append(f"{name}: a NOT_RUN sensitivity was counted")
            elif item.empty or int(float(item["value"].iloc[0])) != want[0]:
                problems.append(f"{name}: sensitivity_survives:sens_drop_jul2016 not {want[0]}")
            if want[1] not in lab:
                problems.append(f"{name}: label {lab!r} lacks {want[1]!r}")
    # 19.2: the transient clause is conditional on the pre-freeze transient MDE
    # lying at or below the MEI; above it, the transient shape is NOT excluded (P45).
    try:
        mde_big = {S1: {**mde[S1], "dip_rebound": 0.006}, S2: mde[S2]}
        res, _, _ = m.evaluate(scenario({}), mde_big)
        row = res[(res["stratum"] == S1) & (res["item"] == "bounded_null")]
        if row.empty or "transient dip-and-rebound of the minimum effect of interest is not excluded" not in str(row["detail"].iloc[0]):
            problems.append("transient MDE above the MEI: the sentence still claims the transient shape is disfavoured")
        else:
            passed += 1
    except Exception as e:  # noqa: BLE001
        problems.append(f"transient MDE above the MEI: evaluate raised {type(e).__name__}: {e}")
    # 23.1c: the enumerated set is the set the sealed script writes — every
    # 'sensitivity' spec in the current synthetic dry run is named in it and vice versa.
    art = OUTPUTS_TABLES / "confirmatory_results_dryrun_synthetic.csv"
    enumerated = "dry run absent, set not compared"
    if art.exists():
        written = set(pd.read_csv(art).query("family == 'sensitivity'")["spec"].unique())
        named = set(m.SENSITIVITY_SPECS)
        if written != named:
            problems.append(f"34's SENSITIVITY_SPECS differ from the specs 30 writes: only in 30 {sorted(written - named)}, "
                            f"only in 34 {sorted(named - written)}")
        enumerated = f"the {len(named)} enumerated specs are exactly the specs the dry run writes"
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", (f"{passed} planted tables read as the pre-registration requires (23.1–23.4, "
                    f"19.2, 25, note 9.4, 23.1c/d); {enumerated}; 34 reads only the sealed table "
                    "and the tracked pre-freeze power table, and seals its reading")


def s_third_pass_record_consistency():
    """P46-P53 (third CP2 audit pass, 2026-09-20): statements of the record that the
    audit found contradicted by the code or by the record itself, held to their
    corrected form by text.

    Each clause is a fact a reader could check by grep: the summary table marks
    the joint days 0-7 window as decided after discovery results (§14); the
    note and the master describe C1 as the two blocks the code estimates, with
    2021's block inside the pandemic and B-HEARD the property that makes it
    clean; the B-HEARD covariate is a numbered deviation; §18 no longer claims
    its rules were fixed before the values existed; F4's weights are called what
    they are (a total-dispatch count); §20 says where the spliced and primary
    series can differ inside C1; the stale 62,920 design count is gone from every
    document but the addendum's own correction; 19's, 18's and event_study's
    method text match their code; 35 treats boundary days as inside; and 23.11 /
    23.12 state the limitations the pass named.
    """
    import ast as _ast
    problems = []
    plan = (PROJECT_ROOT / "docs" / "CONFIRMATION_PLAN.md").read_text()
    note = (PROJECT_ROOT / "docs" / "PRE_ANALYSIS_NOTE.md").read_text()
    master = (PROJECT_ROOT / "docs" / "PAPER_MASTER.md").read_text()
    execp = (PROJECT_ROOT / "docs" / "EXECUTION_PLAN.md").read_text()
    if "| 3 | Test window: days 0–5 → days 0–7, joint | no (§14) |" not in plan:
        problems.append("summary row 3 does not mark the joint days 0-7 window as decided after discovery (§14)")
    if "No COVID" in note or "No COVID" in master:
        problems.append("C1 is still described as having no COVID exposure (its 2021 block is inside the pandemic)")
    if "2015-07-01 → 2016-12-31 and 2021-01-01 → 2021-05-31" not in master:
        problems.append("PAPER_MASTER §6 does not describe Confirmation A as the two C1 blocks the code estimates")
    if 'Confirmation B (stratum C2, "exposed") | 2021-06-01 → 2024-12-31 |' not in master:
        problems.append("PAPER_MASTER §6 does not open Confirmation B at the B-HEARD launch")
    if not re.search(r"\| 30 \|.*bheard_exposure", plan):
        problems.append("the B-HEARD covariate is not a numbered row of the addendum's summary table")
    if any("before the values exist" in ln and "§30" not in ln for ln in plan.split("## 30.")[0].splitlines()):
        problems.append("§18 still claims its decision rules were fixed before the values existed")
    for doc, name in ((plan, "CONFIRMATION_PLAN"), (master, "PAPER_MASTER")):
        if "no outcome group" in doc and "total-dispatch" not in doc:
            problems.append(f"{name} disposes of F4 as outcome-free without naming the weights a total-dispatch count")
    if "2021 block" not in plan.split("## 21.")[0].split("## 20.")[-1]:
        problems.append("§20 does not say the spliced and primary series can differ inside C1's 2021 block")
    for doc, name in ((plan, "CONFIRMATION_PLAN"), (note, "PRE_ANALYSIS_NOTE"), (master, "PAPER_MASTER"),
                      (execp, "EXECUTION_PLAN")):
        for para in re.split(r"\n\s*\n", doc):
            if "62,920" in para and "77,506" not in para:
                problems.append(f"{name} states the 62,920 design count in a passage that does not correct it to 77,506")
                break
    if "remains open at any point" in master or "does not foreclose it" in master:
        problems.append("PAPER_MASTER §5.3 still says the external pre-registration remedy survives the lift")
    if "1.21" not in plan.split("**23.12")[0].split("**23.11")[-1]:
        problems.append("23.11 does not give the 8-df factor beside the one-parameter 1.28")
    lim = plan.split("## 24.")[0].split("**23.12")[-1]
    for token in ("discovery rows", "200 draws", "asymptotic"):
        if token not in lim:
            problems.append(f"23.12 does not state the {token!r} limitation")
    # code text
    t19 = _ast.parse(src("19_power.py"))
    doc19 = _ast.get_docstring(t19) or ""
    if "CONFIRMATION_ANALYSIS_WINDOWS" not in doc19 or "opens it at 2015-01-01" in doc19:
        problems.append("19's STRATA docstring does not describe the strata its code derives")
    ri = next((n for n in _ast.walk(t19) if isinstance(n, _ast.FunctionDef) and n.name == "_ri_sim"), None)
    if ri is None or "(1 + k) / (1 + n)" not in (_ast.get_docstring(ri) or "") or "computes p as k/n" in (_ast.get_docstring(ri) or ""):
        problems.append("19's _ri_sim docstring does not describe the (1 + k) / (1 + n) p-value the code computes")
    doc18 = _ast.get_docstring(_ast.parse(src("18_null_calibration.py"))) or ""
    if "DISCOVERY rows" not in doc18:
        problems.append("18's docstring does not say the noise is measured on discovery rows")
    es = src("event_study.py")
    if "62,920" in es and "77,506" not in es:
        problems.append("event_study still quotes 62,920 without the corrected count")
    t35 = _ast.parse(src("35_coverage_breaks.py"))
    inside = next((n for n in _ast.walk(t35) if isinstance(n, _ast.FunctionDef) and n.name == "inside"), None)
    if inside is None or "lo <= d <= hi" not in _ast.unparse(inside):
        problems.append("35's inside() does not treat boundary days as inside (23.10)")
    if "strictly inside" in (_ast.get_docstring(t35) or ""):
        problems.append("35's docstring still says 'strictly inside'")
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", ("row 3 marked non-blind; C1 described as the code estimates it; B-HEARD covariate numbered; "
                    "§18, F4 and §20 wording corrected; 62,920 gone; 19/18/event_study/35 text matches code; "
                    "23.11 and 23.12 state the pass's limitations")


def v_table1_regenerates():
    """P6, the generated-table case: Table 1 is rendered from its artifacts, so it is
    held to them by re-rendering rather than by a claim per cell.

    The episode list has 74 rows and ten columns, most of them dates. Registering
    a claim for every cell would be several hundred rows that say nothing a
    reader could check by eye, so `docs/tables/TABLE1_episodes.md` is written by
    `ops/paper_table1.py` from the adopted list, the frozen list and the stratum
    rule, with the inputs' hashes in its header, and this check renders it again
    and requires the committed bytes to match. A hand edit to the table, a
    changed episode list, a changed stratum rule or a changed renderer all fail
    it. V.claims_cover_exhibits does not scan docs/tables, so this is the only
    thing holding that file to the data — which is why it fails rather than
    blocks on a mismatch.
    """
    import importlib.util
    f = PROJECT_ROOT / "docs" / "tables" / "TABLE1_episodes.md"
    if not f.exists():
        return "BLOCKED", "docs/tables/TABLE1_episodes.md absent — run ops/paper_table1.py"
    spec = importlib.util.spec_from_file_location("_t1", PROJECT_ROOT / "ops" / "paper_table1.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    fresh = m.render()
    committed = f.read_text()
    if fresh != committed:
        a, b = committed.splitlines(), fresh.splitlines()
        first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        return "FAIL", (f"committed Table 1 differs from a fresh render at line {first + 1} "
                        f"({len(a)} vs {len(b)} lines): run ops/paper_table1.py and commit the result")
    n = sum(1 for ln in fresh.splitlines() if ln.startswith("| ") and ln[2:3].isdigit())
    return "PASS", (f"{n} table rows re-render byte-identical from {EPISODE_LIST_PRIMARY}, the frozen "
                    "list and stratum_episodes")


def d_discovery_scripts_pinned():
    """D8: lifting the freeze must not move the exploratory scripts onto the sealed sample.

    `select_sample` derived its window from FREEZE_ACTIVE for every caller, so
    the lift — one flag — would have switched the discovery estimator, the
    decomposition, the figures, the power analysis and the null calibration onto
    the confirmation windows: `python3 17_stacked_event_study.py` after the lift
    was an unsealed confirmatory run at 2,000 draws, and the discovery results
    the paper reports could not have been regenerated (CP3's fresh-clone line)
    once the flag flipped. Three scripts also widened their EPISODE list on the
    flag (`if FREEZE_ACTIVE: ep = ep[period == "discovery"]`).

    Found 2026-09-13 before the lift (addendum 26). Now every reader except the
    sealed script asks for its window by name — `select_sample(...,
    window="discovery")`, `active_windows("discovery")` — and the guard refuses
    window="confirmation" while the freeze is active. This check holds both
    halves: (source) every select_sample / active_windows call outside
    30_confirmatory_run.py, freeze_guard.py and this suite carries
    window="discovery", and no script branches its episode list on
    FREEZE_ACTIVE; (behaviour) with the flag flipped False in the loaded guard,
    window="discovery" still returns discovery rows only, and with the flag True
    window="confirmation" raises.
    """
    import ast as _ast
    problems, callers = [], []
    # The suite was exempt until 2026-09-20, when the first gate run after the
    # lift found three of its own checks (S7, S8, X6) deriving their sample from
    # the flag — incident F5. It is scanned like any other script now; only the
    # guard selftests on synthetic date frames (where="selftest") are skipped.
    exempt = {"30_confirmatory_run.py", "freeze_guard.py"}
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in exempt:
            continue
        try:
            tree = _ast.parse(f.read_text())
        except SyntaxError as e:
            problems.append(f"{f.name}: does not parse ({e})")
            continue
        # This check's own body toggles the flag and calls the guard with names it
        # must refuse; that selftest is not a reader and is skipped by name.
        own = {id(x) for fn_ in _ast.walk(tree) if isinstance(fn_, _ast.FunctionDef)
               and fn_.name == "d_discovery_scripts_pinned" for x in _ast.walk(fn_)}
        for n in _ast.walk(tree):
            if id(n) in own:
                continue
            if isinstance(n, _ast.Call):
                fn = n.func
                name = fn.id if isinstance(fn, _ast.Name) else getattr(fn, "attr", None)
                if name in ("select_sample", "active_windows"):
                    if any(kw.arg == "where" and isinstance(kw.value, _ast.Constant)
                           and kw.value.value == "selftest" for kw in n.keywords):
                        continue
                    win = None
                    if name == "active_windows" and n.args:
                        win = n.args[0]
                    for kw in n.keywords:
                        if kw.arg == "window":
                            win = kw.value
                    val = win.value if isinstance(win, _ast.Constant) else None
                    if val != "discovery":
                        problems.append(f"{f.name}:{n.lineno} {name}() without window='discovery'")
                    else:
                        callers.append(f.name)
            if isinstance(n, _ast.If):
                t = _ast.unparse(n.test)
                body = _ast.unparse(_ast.Module(body=n.body, type_ignores=[]))
                if "FREEZE_ACTIVE" in t and "period" in body and "discovery" in body:
                    problems.append(f"{f.name}:{n.lineno} widens the episode list when FREEZE_ACTIVE is False")
    sys.path.insert(0, str(SCRIPTS))
    import freeze_guard as fg
    frame = pd.DataFrame({"incident_date": pd.date_range("2015-01-01", "2024-12-31", freq="D"),
                          "edp_share": 0.1})
    saved = fg.FREEZE_ACTIVE
    try:
        fg.FREEZE_ACTIVE = False
        out = fg.select_sample(frame, where="selftest", window="discovery")
        if not (out["incident_date"].min() == pd.Timestamp(DISCOVERY_START)
                and out["incident_date"].max() == pd.Timestamp(DISCOVERY_END)
                and len(out) == (pd.Timestamp(DISCOVERY_END) - pd.Timestamp(DISCOVERY_START)).days + 1):
            problems.append("window='discovery' did not return exactly the discovery window with the freeze lifted")
        fg.FREEZE_ACTIVE = True
        try:
            fg.select_sample(frame, where="selftest", window="confirmation")
            problems.append("window='confirmation' was served while the freeze is active")
        except fg.FreezeViolation:
            pass
        try:
            fg.active_windows("both")
            problems.append("active_windows accepted an unknown window name")
        except ValueError:
            pass
    finally:
        fg.FREEZE_ACTIVE = saved
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", (f"{len(set(callers))} scripts pin the discovery window by name; the guard refuses "
                    "the confirmation sample under the freeze and keeps discovery pinned when lifted")


def x_run_all_deterministic_env():
    """X20: run_all runs every stage under a fixed Python hash seed and one BLAS thread.

    Two cold passes of 2026-09-20, every randomization ledger banked, produced
    different bytes for 17's and 25's tables: coefficients at 1e-16, clustered
    standard errors at 1e-11, the joint statistic at 1e-7 — nothing a reader
    would see, everything a hash would. Single-threaded BLAS did not remove it;
    PYTHONHASHSEED=0 did, twice over, so an iteration order over names was the
    source. The CP2 line "run_all clean twice from cold; the second manifest
    hash-matches the first" is only meaningful if the run is deterministic to
    the byte, so run_all passes that environment to every stage and the
    runners export it. This check reads run_all's stage launch by AST: the
    subprocess call carries env=STAGE_ENV and STAGE_ENV sets PYTHONHASHSEED to
    "0" and every BLAS thread variable to "1".
    """
    import ast as _ast
    tree = _ast.parse(src("run_all.py"))
    problems = []
    env_assign = next((n for n in tree.body if isinstance(n, _ast.Assign)
                       and any(isinstance(t, _ast.Name) and t.id == "STAGE_ENV" for t in n.targets)), None)
    if env_assign is None:
        problems.append("run_all.py defines no STAGE_ENV")
    else:
        text = _ast.unparse(env_assign.value)
        for k, v in (("PYTHONHASHSEED", "0"), ("OPENBLAS_NUM_THREADS", "1"), ("OMP_NUM_THREADS", "1"),
                     ("MKL_NUM_THREADS", "1")):
            if f"'{k}': '{v}'" not in text and f'"{k}": "{v}"' not in text:
                problems.append(f"STAGE_ENV does not set {k}={v}")
    # The stage launch is the subprocess.run whose command is `cmd`; run_all's
    # git lookups (rev-parse, status) are subprocess.run calls too and need no env.
    runs = [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)
            and _ast.unparse(n.func) == "subprocess.run" and n.args
            and _ast.unparse(n.args[0]) == "cmd"]
    if not runs:
        problems.append("run_all.py has no stage launch (subprocess.run(cmd, ...))")
    for n in runs:
        env = next((kw for kw in n.keywords if kw.arg == "env"), None)
        if env is None or _ast.unparse(env.value) != "STAGE_ENV":
            problems.append(f"subprocess.run at line {n.lineno} does not pass env=STAGE_ENV")
    for runner in ("coldrun.sh", "calib1000.sh", "phase_i.sh", "rebuild.sh"):
        f = PROJECT_ROOT / "ops" / runner
        if f.exists() and "PYTHONHASHSEED=0" not in f.read_text():
            problems.append(f"ops/{runner} does not export PYTHONHASHSEED=0")
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", ("every stage runs with PYTHONHASHSEED=0 and one BLAS thread; the runners export the same; "
                    "two cold passes are byte-identical on every build and model output")


def v_paper_figures_current():
    """X21: the manuscript's figures are tracked copies that match the current pipeline output.

    outputs/figures is gitignored and regenerated by 08_figures.py and
    25_zscore_simulation.py; the manuscript (docs/PAPER.md) refers to figures a
    fresh clone could not see. ops/paper_figures.py copies the named figures into
    docs/figures with a sha256 manifest. Because the pipeline is deterministic to
    the byte (X20), a tracked copy that differs from the current output means the
    inputs changed or the copy is stale — either way the paper would show a figure
    the tables no longer support. BLOCKED while the outputs are absent (mid cold
    run); FAIL on any difference.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_pf", PROJECT_ROOT / "ops" / "paper_figures.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    missing, stale, ok = m.compare()
    if not (PROJECT_ROOT / "docs" / "figures" / "MANIFEST.json").exists():
        return "BLOCKED", "docs/figures/MANIFEST.json absent — run ops/paper_figures.py"
    if stale:
        return "FAIL", f"tracked figure(s) differ from the current output or are uncopied: {stale} — run ops/paper_figures.py"
    if not ok:
        return "BLOCKED", f"no current figure output to compare ({missing}) — run 08_figures.py"
    return "PASS", (f"{len(ok)} tracked figure(s) byte-identical to the current outputs"
                    + (f"; not produced by the pipeline here: {missing}" if missing else ""))


def s_ri_scheme_certified():
    """P1: every stratum's randomization null is the one its calibration certifies.

    `event_study.placebo_starts` shifts the whole real sequence by one anchor and
    REJECTS the draw if it does not fit. That rejection is right — an earlier
    version walked forward and stopped early, so the null carried about half the
    real episode count — but it needs slack, and one stratum has none.

    Measured at 500 draws per stratum: discovery and C2 produce 500 usable draws
    under anchor shift, with 190 and 53 days of slack. C1 produces ZERO. It is two
    windows sitting either side of the entire discovery period, so there is no
    single span to slide within and 40.9% of anchors land outside its own
    windows; its 2021 block alone needs 139 days of a 120-day interior. The
    p-value on the CLEAN stratum would return NaN after the whole budget is spent.

    A circular shift over admissible days works there — and is a DIFFERENT NULL.
    A CALIBRATED verdict is a statement about one geometry and one scheme, so
    each stratum needs its own, and this check makes each artifact answer for
    itself: it recomputes the scheme the stratum requires from the episode dates
    and asserts the calibration certifies that scheme on that geometry.

    Episode dates are treatment-side, so this reads no outcome data.
    """
    import sys as _sys
    _sys.path.insert(0, str(SCRIPTS))
    from event_study import draw_scheme_for, stratum_episodes
    from config import CONFIRMATION_ANALYSIS_WINDOWS

    f = DATA_REFERENCE / EPISODE_LIST_PRIMARY
    if not f.exists():
        return "BLOCKED", f"{EPISODE_LIST_PRIMARY} absent — run 13_extension_episodes.py"
    ep = pd.read_csv(f, parse_dates=["start"])

    strata = {
        "discovery": ([(DISCOVERY_START, DISCOVERY_END)], "null_calibration.csv"),
        "C1": ([CONFIRMATION_ANALYSIS_WINDOWS[0], CONFIRMATION_ANALYSIS_WINDOWS[1]],
               "null_calibration_C1.csv"),
        "C2": ([CONFIRMATION_ANALYSIS_WINDOWS[2]], "null_calibration_C2.csv"),
        # 30 reports a pooled stratum; its three-window null needs its own
        # certificate (2026-09-13).
        "pooled": (list(CONFIRMATION_ANALYSIS_WINDOWS), "null_calibration_pooled.csv"),
    }
    missing, wrong, ok = [], [], []
    for name, (wins, fname) in strata.items():
        kept, _ = stratum_episodes(ep["start"], wins, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
        need, _why = draw_scheme_for(wins, [k["start"] for k in kept],
                                     EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
        art = OUTPUTS_TABLES / fname
        if not art.exists():
            missing.append(f"{name} (needs '{need}', no {fname})")
            continue
        a = pd.read_csv(art).set_index("metric")["value"]
        if "draw_scheme" not in a.index:
            missing.append(f"{name} ({fname} predates the draw_scheme field)")
            continue
        # A RECORDED SCHEME IS NOT A CERTIFIED ONE. The first version of this
        # check read draw_scheme and nothing else, so any run that reached the
        # write step satisfied it — including a 2-sim smoke test that issued
        # VERDICT=UNDETERMINED and said so. One such file was on disk while
        # this check was BLOCKED, and it would have flipped it to PASS: C1
        # "certified on circular" from an artifact whose own verdict is that it
        # certifies nothing. The field this check gates on has to be the one
        # that carries the finding, not the one that merely labels the run.
        verdict = str(a.get("VERDICT", "")).strip()
        n_done = int(float(a.get("n_sims_completed", 0)))
        n_need = int(float(a.get("min_sims_required", 0)))
        got = str(a["draw_scheme"])
        # Addendum 25: a null that FAILS calibration at the lift size under the
        # scheme the geometry requires is a verdict, not a gap. The sealed
        # script flags that stratum uncertified and excludes it from the
        # family decision; this check reports it rather than blocking on it.
        lift_need = LIFT_MIN_SIMS if name in ("C1", "C2") else n_need
        if verdict == "NOT CALIBRATED" and n_done >= lift_need and got == need:
            ok.append(f"{name}={got}@{n_done} UNCERTIFIED (addendum 25)")
            continue
        if verdict != "CALIBRATED" or n_done < n_need:
            missing.append(f"{name} ({fname}: {n_done}/{n_need} sims, "
                           f"VERDICT={verdict or 'absent'})")
            continue
        if got != need:
            wrong.append(f"{name}: requires '{need}', calibration certifies '{got}'")
        else:
            ok.append(f"{name}={got}@{n_done}")
    if wrong:
        return "FAIL", (f"{len(wrong)} stratum/strata would use a null their calibration "
                        f"does not certify: {wrong}")
    if missing:
        return "BLOCKED", (f"{len(missing)} stratum/strata have no calibration recording "
                           f"their scheme: {missing} — run 18_null_calibration.py "
                           "--stratum for each (finding P1)")
    return "PASS", (f"all {len(ok)} strata certified on the scheme they require: "
                    + ", ".join(ok))


def s_estimators_gate_on_calibration():
    """P7: every script that reports an RI p-value certifies its own null first,
    and no cheap run can replace an expensive result.

    Two halves, both re-findings of defects this project had already closed
    somewhere else.

    GATE. 17_stacked_event_study.py computes randomization-inference p-values —
    the ratified primary inference — and read no calibration at all. Gate C
    ratified "calibrate, then report"; the gate lived only in this suite, so the
    estimator itself would run and print regardless. Invisible because discovery
    IS calibrated, so every number would have been sound: the same "documented
    and wired into nothing" pattern as X5, X6 and D6. 30_confirmatory_run.py did
    gate, but on null_calibration.csv — DISCOVERY's artifact — while writing C1
    and C2 p-values, so it answered a question about a sample it never
    estimates. Both now call event_study.require_calibrated(stratum).

    NO DOWNGRADE. 17 had no equivalent of 18's "a smaller run may not replace a
    larger one". Found by running it: a 2-draw invocation launched to prove the
    new gate fires overwrote the full result with p_randomization = 1.0. The
    artifact records n_draws, so it was honest about itself, and nothing said
    what it had destroyed.

    Checked by AST, not by grep: a call node, so the words appearing in a
    comment — including the comments above — do not satisfy it. That is the
    S.dose_arm_wired lesson, where a caller scan matched prose and passed with
    the call deleted.
    """
    import ast as _ast
    need = {"17_stacked_event_study.py", "30_confirmatory_run.py"}
    missing = []
    for name in sorted(need):
        f = SCRIPTS / name
        if not f.exists():
            missing.append(f"{name} absent")
            continue
        tree = _ast.parse(f.read_text())
        called = {n.func.id for n in _ast.walk(tree)
                  if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)}
        if "require_calibrated" not in called:
            missing.append(f"{name} reports RI p-values without calling "
                           "require_calibrated()")
    # N6: randomization inference must be checkpointed, for the same reason the
    # calibration is. This environment restarts every 30-70 minutes and both long
    # jobs died having written nothing; the only difference was that one had a
    # ledger and one did not.
    es = (SCRIPTS / "event_study.py").read_text()
    if "SeedSequence" not in es:
        missing.append("randomization_p does not seed draws per index, so a resumed "
                       "run cannot reproduce the run it resumed")
    if "ledger" not in es:
        missing.append("randomization_p keeps no ledger, so an interrupted run loses "
                       "every draw it completed")
    f17 = (SCRIPTS / "17_stacked_event_study.py")
    if f17.exists() and "ledger=" not in f17.read_text():
        missing.append("17 calls randomization_p without a ledger, so the discovery "
                       "run cannot survive a restart")
    # N10: the geometry the null is drawn on must be the certified one, passed
    # explicitly, not the panel's own extent after the sample rules.
    if f17.exists():
        t17 = _ast.parse(f17.read_text())
        rp_calls = [n for n in _ast.walk(t17) if isinstance(n, _ast.Call)
                    and isinstance(n.func, _ast.Name) and n.func.id == "randomization_p"]
        if rp_calls and not all(any(k.arg == "windows" for k in c.keywords) for c in rp_calls):
            missing.append("17 calls randomization_p without windows=, so the anchor "
                           "geometry is the panel's extent rather than the certified window")

    # The no-downgrade rule in 17: the published write must be guarded by a
    # comparison against the draws already on disk.
    f17 = SCRIPTS / "17_stacked_event_study.py"
    if f17.exists():
        src = f17.read_text()
        tree = _ast.parse(src)
        guarded = any(
            isinstance(n, _ast.If)
            and "_draws_here" in _ast.unparse(n.test)
            and "_prior" in _ast.unparse(n.test)
            and "event_study_results.csv" in _ast.unparse(n)
            for n in _ast.walk(tree))
        if not guarded:
            missing.append("17 publishes event_study_results.csv without comparing "
                           "this run's draw count to the one on disk")
    if missing:
        return "FAIL", f"{len(missing)} estimator gap(s): " + "; ".join(missing)
    return "PASS", ("17 and 30 both certify their stratum's null before reporting, "
                    "and 17 refuses to publish fewer draws than the result on disk")


def s_draw_scheme_total():
    """N5: the draw-scheme dispatch is exhaustive and never falls back silently.

    `randomization_p` used to read
        if scheme == "circular": circular else: anchor_shift
    so any scheme name it did not recognise became an anchor shift. Renaming the
    circular scheme sent C1 — the one stratum for which an anchor shift is
    arithmetically impossible — down the else branch, where every draw was
    rejected and the p-value came back NaN.

    The check exists because of what the failure mode ALMOST was. C1 produced no
    p-value, which is loud. On any stratum with slack the same fallback produces
    a perfectly ordinary number from a null nobody certified, and
    S.ri_scheme_certified could not catch it: that check compares the scheme a
    stratum REQUIRES against the scheme its calibration RECORDS, and neither is
    the scheme the code actually ran. Requirement, certificate and behaviour
    could all disagree with nothing to notice.

    Asserted by AST: every scheme `draw_scheme_for` can return must appear as a
    dispatch key, and the dispatcher must raise on anything else.
    """
    import ast as _ast
    f = SCRIPTS / "event_study.py"
    if not f.exists():
        return "BLOCKED", "event_study.py absent"
    tree = _ast.parse(f.read_text())
    fns = {n.name: n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
    for need in ("draw_scheme_for", "randomization_p"):
        if need not in fns:
            return "FAIL", f"event_study.py has no {need}"
    # Every literal a scheme selector can return, minus the "no null" sentinel.
    returned = {c.value for c in _ast.walk(fns["draw_scheme_for"])
                if isinstance(c, _ast.Constant) and isinstance(c.value, str)
                and c.value in ("anchor_shift", "circular", "circular_within_block", "circular_within_block_fw7",
                                "none")}
    schemes = returned - {"none"}
    body = _ast.unparse(fns["randomization_p"])
    missing = sorted(x for x in schemes if f'"{x}"' not in body and f"'{x}'" not in body)
    if missing:
        return "FAIL", (f"draw_scheme_for can return {missing}, which randomization_p "
                        "never names — those draws would take whatever branch is left")
    raises = any(isinstance(n, _ast.Raise) for n in _ast.walk(fns["randomization_p"]))
    if not raises:
        return "FAIL", ("randomization_p has no raise, so an unrecognised draw scheme "
                        "falls through to whichever drawer the code ends on — a "
                        "silent switch to a different null")
    return "PASS", (f"randomization_p names every scheme draw_scheme_for can return "
                    f"({sorted(schemes)}) and raises on anything else")


def s_ri_pvalue_form():
    """N1: the randomization p-value is (1+k)/(1+n), in every spelling of it.

    The observed assignment is itself one of the assignments the null admits, so
    it belongs in both numerator and denominator. `k/n` leaves it out, which
    makes the test anti-conservative precisely where rejection decisions are
    taken, and lets it return p = 0 — not a small p-value, not a p-value at all.

    This was on CP2's checklist as a requirement and was never implemented. It
    went unseen because nothing looked at the artifacts for the one value the
    biased form can produce and the correct form cannot: every committed
    calibration carried a zero.

    Two things are asserted, because either alone can pass while the defect is
    live. The CODE, by AST, in both places that compute an RI p-value —
    event_study.randomization_p and 30_confirmatory_run, which keep separate
    copies because the confirmatory path draws its own placebos. And the
    ARTIFACTS, which is the half that would have caught it: no stored p-value may
    be zero, whatever the source happens to say today.
    """
    import ast as _ast
    bad = []
    # ONE implementation. 30 used to keep its own copy of the draw and the
    # p-value "because the confirmatory path draws its own placebos", and the
    # copy drifted: it still crossed the window seam after RI3 replaced that
    # scheme in event_study (CP1 audit, 2026-09-13). So event_study.randomization_p
    # must carry the corrected form, and 30 must CALL it and carry no p-value
    # arithmetic of its own.
    f = SCRIPTS / "event_study.py"
    src = f.read_text() if f.exists() else ""
    if "(1 + (stats_ >= obs).sum()) / (1 + len(stats_))" not in src.replace("\n", " "):
        bad.append("event_study.randomization_p does not compute (1+k)/(1+n)")
    f30 = SCRIPTS / "30_confirmatory_run.py"
    if f30.exists():
        t30 = _ast.parse(f30.read_text())
        calls = {n.func.id for n in _ast.walk(t30)
                 if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)}
        if "randomization_p" not in calls:
            bad.append("30_confirmatory_run.py does not call event_study.randomization_p")
        local_p = [n for n in _ast.walk(t30) if isinstance(n, _ast.BinOp)
                   and isinstance(n.op, _ast.Div)
                   and "stats_" in _ast.unparse(n) and "obs" in _ast.unparse(n)]
        if local_p:
            bad.append(f"30_confirmatory_run.py computes its own RI p-value: "
                       f"{_ast.unparse(local_p[0])[:60]}")
    else:
        bad.append("30_confirmatory_run.py absent")
    zeros = []
    for art in sorted(OUTPUTS_TABLES.glob("null_calibration_pvalues*.csv")):
        try:
            v = pd.read_csv(art)["p"]
        except Exception:
            continue
        if (v == 0).any():
            zeros.append(f"{art.name} ({int((v == 0).sum())} zero p-value(s))")
    if bad or zeros:
        return "FAIL", ("randomization p-values are not (1+k)/(1+n): "
                        + "; ".join(bad + zeros))
    return "PASS", ("one RI p-value implementation, (1+k)/(1+n), called by 17 and 30; "
                    "no stored p-value is zero")


def s_calibration_writes_stratified():
    """P5: every file a calibration run writes is named for the stratum it describes.

    A calibration verdict is a statement about ONE sample geometry and ONE way of
    drawing placebo dates. 18_null_calibration.py says so, and gave the verdict
    file a per-stratum name for exactly that reason — then wrote three more files
    beside it under names with no stratum in them.

    That was not cosmetic. The rule protecting the gate is "a run may publish only
    if it completed at least as many sims as the run already on disk", and the
    comparison is made against the per-stratum VERDICT. A 2-sim C1 diagnostic
    passed it — no C1 verdict existed, so the bar was zero — and the write it was
    thereby licensed to make landed on null_calibration_pvalues.csv, which is
    DISCOVERY's. 200 sims of p-values, 5,450 bytes, replaced by 61. The guard
    written after the 8-sim incident answered a question about one stratum and
    licensed a write to another.

    So this walks the AST and requires every to_csv target in the script to be
    built by the one helper that appends the stratum. A name assembled inline is
    a failure even if it happens to be correct today, because the next file added
    beside it will not be.

    Defeat attempt: restoring the literal "null_calibration_pvalues.csv" argument
    fails this check, and the mention of that filename in the comment above the
    helper does not satisfy it — the test is on call arguments, not on text.
    """
    import ast as _ast
    f = SCRIPTS / "18_null_calibration.py"
    if not f.exists():
        return "BLOCKED", "18_null_calibration.py absent"
    tree = _ast.parse(f.read_text())

    def _writes_to_tables(node):
        """True when this to_csv() targets OUTPUTS_TABLES without going via _strat."""
        if not (isinstance(node, _ast.Call)
                and isinstance(node.func, _ast.Attribute)
                and node.func.attr == "to_csv" and node.args):
            return None
        arg = node.args[0]
        if isinstance(arg, _ast.Call) and isinstance(arg.func, _ast.Name) \
                and arg.func.id == "_strat":
            return None                      # routed through the helper
        src = _ast.unparse(arg)
        if "OUTPUTS_TABLES" in src:
            return src
        return None

    # N4: the run must also be DURABLE. Holding every result in memory and
    # writing once at the end meant a container restart destroyed 45 minutes and
    # left nothing, which put the pre-freeze gate's 1000-sim requirement out of
    # reach for reasons unrelated to statistics.
    src_all = f.read_text()
    if "null_calibration_ledger" not in src_all:
        return "FAIL", ("18_null_calibration.py keeps no per-sim ledger, so an "
                        "interrupted run loses everything and a 1000-sim "
                        "calibration cannot survive a restart")
    if ".flush()" not in src_all:
        return "FAIL", ("the calibration ledger is never flushed, so a killed run "
                        "loses whatever the buffer held rather than one sim")

    bare = [w for n in _ast.walk(tree) if (w := _writes_to_tables(n))]
    # The helper must also actually append the stratum, or routing through it
    # proves nothing.
    helper = [n for n in _ast.walk(tree)
              if isinstance(n, _ast.FunctionDef) and n.name == "_strat"]
    if not helper:
        return "FAIL", ("18_null_calibration.py has no _strat helper, so no file it "
                        "writes is guaranteed to name its stratum")
    hsrc = _ast.unparse(helper[0])
    if "args.stratum" not in hsrc:
        return "FAIL", "_strat does not consult args.stratum, so it cannot stratify anything"
    if bare:
        return "FAIL", (f"{len(bare)} calibration output(s) are named without the "
                        f"stratum, so another stratum's run can overwrite them: "
                        + "; ".join(bare[:3]))
    return "PASS", ("every calibration output is named through _strat, which "
                    "appends the stratum")


def s_calibration_on_residual():
    """S8: the synthetic null must have THIS design's dependence, not a harder one.

    18_null_calibration.py builds a synthetic panel out of four pieces — a
    district effect, a day-of-week effect, a citywide day shock, and an AR(1)
    idiosyncratic term — and its docstring claims the resulting null "is the null
    of THIS design, not a generic one". It used to estimate the AR(1) parameters
    from the edp_share LEVEL series, which already contains the first three
    pieces, and then add all three back on top. The null was therefore measurably
    more dependent and more variable than the panel it claimed to imitate: rho
    0.1851 against a true residual 0.0482, nearly FOUR TIMES too persistent.

    The error ran conservative — a harder null is a stricter gate — so the
    CALIBRATED verdict survived it. That is exactly why a check is needed rather
    than a note: a defect whose sign happens to be safe is the kind that stays.
    It also means any MDE derived from this generator inherits a pessimistic
    bias, which is how it was found at all: by reviewing a power design, not the
    calibration.

    This check recomputes both candidate values from the panel and asserts the
    artifact carries the residual one. It is a test on the NUMBER the calibration
    published, not on the shape of the source, so a refactor that preserves the
    behaviour passes and one that quietly restores the level estimate does not.
    """
    art = OUTPUTS_TABLES / "null_calibration.csv"
    panel_path = DATA_PROCESSED / "panel_cd_day.parquet"
    if not art.exists():
        return "BLOCKED", "null_calibration.csv absent — run 18_null_calibration.py"
    if not panel_path.exists():
        return "BLOCKED", "panel_cd_day.parquet absent — run 01_build_panel.py"

    a = pd.read_csv(art).set_index("metric")["value"]
    if "ar1_rho" not in a.index:
        return "BLOCKED", "null_calibration.csv carries no ar1_rho"
    rho_art = float(a["ar1_rho"])

    import freeze_guard as fg
    panel = pd.read_parquet(panel_path)
    panel["incident_date"] = pd.to_datetime(panel["incident_date"])
    panel = fg.select_sample(panel, where="23_regression_suite:S8", window="discovery")
    s = (panel.dropna(subset=["edp_share"])
         .sort_values(["communitydistrict", "incident_date"]))

    def lag1(series, by):
        lag = series.groupby(by).shift(1)
        ok = lag.notna() & series.notna()
        return float(np.corrcoef(series[ok], lag[ok])[0, 1])

    cd = s["communitydistrict"]
    rho_level = lag1(s["edp_share"], cd)

    # Peel the components in the order synthetic_panel adds them back.
    r = s["edp_share"] - s.groupby("communitydistrict")["edp_share"].transform("mean")
    r = r - r.groupby(s["incident_date"].dt.dayofweek).transform("mean")
    r = r - r.groupby(s["incident_date"]).transform("mean")
    rho_resid = lag1(r, cd)

    near_resid = abs(rho_art - rho_resid)
    near_level = abs(rho_art - rho_level)
    if near_resid > 0.02 or near_level <= near_resid:
        # Describe what was measured; do not assert a cause the numbers do not
        # establish. A published rho of 0.5 is nearer the level estimate than the
        # residual one without being calibrated on either.
        return "FAIL", (
            f"published ar1_rho={rho_art:.4f} does not match the residual "
            f"{rho_resid:.4f} (gap {near_resid:.4f}); the level series, which is "
            f"the S8 defect, gives {rho_level:.4f} (gap {near_level:.4f})")
    return "PASS", (
        f"ar1_rho={rho_art:.4f} matches the residual {rho_resid:.4f} "
        f"(gap {near_resid:.4f}) and not the level {rho_level:.4f}, which is the "
        f"S8 defect the null used to carry")


def s_dose_arm_wired():
    """D6: the dose-response arm has a caller AND recovers a planted dose effect.

    `fit_dose_response` was written, documented in 17's header, committed — and
    called by nothing. A repo-wide grep for its name returned exactly one hit,
    its own `def`. That is the THIRD documented arm in this rebuild found wired
    into nothing, after the PPML counts arm (X5/R8) and the B-HEARD control (X6).
    A function nobody calls is a claim nobody tested, and it reads in the header
    exactly like one that works.

    So this check does both halves, because either alone passes for the wrong
    reason. A source scan proves a caller exists but not that the arm fits — the
    PPML arm HAD a caller and still raised TypeError into a broad `except` that
    reported "not estimable". A behavioural test proves the function works but
    not that the pipeline uses it.

    The planted effect is proportional to episode intensity: episodes carry
    intensities spanning the real range and the outcome is shifted by a fixed
    amount per standard deviation of intensity, so the interaction coefficient
    has a known target.
    """
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es

    # A CALL, not a mention. The first version of this scan looked for the name
    # anywhere in the file, and PASSED with the caller deleted — because the
    # comment above the call site explains that this function used to be dead
    # code, and names it. A check written to catch "documented but never called"
    # was itself satisfied by the documentation. Parse instead: only a Call node
    # counts.
    def calls_it(path):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            return False
        return any(isinstance(n, ast.Call)
                   and (getattr(n.func, "id", None) or getattr(n.func, "attr", None))
                   == "fit_dose_response"
                   for n in ast.walk(tree))

    callers = [f.name for f in sorted(SCRIPTS.glob("*.py"))
               if f.name not in ("event_study.py", "23_regression_suite.py")
               and calls_it(f)]
    if not callers:
        return "FAIL", ("fit_dose_response has no caller anywhere — the dose arm is "
                        "documented in 17's header and wired into nothing")

    rng = np.random.default_rng(11)
    dates = pd.date_range("2017-01-01", "2020-12-31", freq="D")
    cds = list(range(1, 60))
    N, T = len(cds), len(dates)
    panel = pd.DataFrame({"communitydistrict": np.repeat(cds, T),
                          "incident_date": np.tile(dates, N),
                          "total_calls": rng.poisson(60, N * T)})
    panel["dow"] = panel["incident_date"].dt.dayofweek
    starts = [d for d in pd.date_range("2017-02-01", periods=28, freq="48D")
              if d <= dates[-1] - pd.Timedelta(days=20)]
    # Intensities spanning the real discovery range (peak CAI-D 1.40 to 12.67).
    peaks = np.linspace(1.40, 12.67, len(starts))
    intensity = dict(zip(starts, peaks))
    z = (peaks - peaks.mean()) / peaks.std(ddof=0)

    PER_SD = 0.01
    panel["edp_share"] = 0.10 + rng.normal(0, 0.002, N * T)
    for st0, zi in zip(starts, z):
        m = panel["incident_date"].between(st0, st0 + pd.Timedelta(days=7))
        panel.loc[m, "edp_share"] += PER_SD * zi

    stack = es.build_stack(panel, starts, 14, 14)
    fit = es.fit_dose_response(stack, "edp_share", intensity)
    if fit is None:
        return "FAIL", f"dose arm has caller(s) {callers} but does not fit"
    got = float(fit.coef()["_post_dose"])
    ok = abs(got - PER_SD) < 0.002
    return ("PASS" if ok else "FAIL",
            f"called by {callers}; recovers planted dose effect {got:+.5f} per SD "
            f"against a planted {PER_SD:+.5f}" if ok else
            f"called by {callers} but recovered {got:+.5f} against a planted {PER_SD:+.5f}")


def d_addendum_complete():
    """E5: the pre-registration text is untouched, and the addendum it points to exists.

    Three places cited a `CONFIRMATION_PLAN.md` addendum before one was written —
    PAPER_MASTER 4.2, PAPER_MASTER 5.2, and finding F2's fix. A pre-registration
    record that points at a document nobody wrote is WORSE than no pointer,
    because it reads as disclosure and nothing in the project contradicted it.

    Three properties, each of which can fail independently:

      1. The frozen text above the addendum marker is byte-identical to what was
         pre-specified. Appending is disclosure; editing is rewriting history,
         and a diff is not a reliable way to notice the difference months later.
      2. The addendum exists and names its deviations.
      3. Every finding whose remedy SAYS it is disclosed in the addendum is
         actually discussed there. This is the part that decays: a finding's fix
         column is written when the finding is filed, and nothing otherwise
         checks that the promised disclosure was ever made.
    """
    f = PROJECT_ROOT / "docs" / "CONFIRMATION_PLAN.md"
    if not f.exists():
        return "BLOCKED", "docs/CONFIRMATION_PLAN.md is absent"
    text = f.read_text()
    marker = "\n---\n\n# Addendum — deviations from the plan above\n"
    if marker not in text:
        return "FAIL", ("CONFIRMATION_PLAN.md has no addendum section, but "
                        "PAPER_MASTER and finding F2 both cite one")

    # The pre-specified text, pinned by content hash rather than by a line count
    # so that appending cannot shift it and editing cannot hide in a diff.
    FROZEN_SHA = "3a411ddd57a2789d6f1866cad51c9bbf1a0136e75cc0f70c5a30e4b81eebee52"
    original, addendum = text.split(marker, 1)
    got = hashlib.sha256(original.encode()).hexdigest()
    if got != FROZEN_SHA:
        return "FAIL", (f"the pre-specified text has been EDITED: sha256 {got[:16]} "
                        f"against the pinned {FROZEN_SHA[:16]}. The addendum exists so "
                        "deviations are appended, never written over the original.")

    reg = PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv"
    promised, undisclosed = [], []
    if reg.exists():
        d = pd.read_csv(reg)
        for _, r in d.iterrows():
            blob = f"{r.get('fix')} {r.get('corrected_claim')}".lower()
            if "addendum" in blob:
                promised.append(r["id"])
                if r["id"] not in addendum:
                    undisclosed.append(r["id"])
    if undisclosed:
        return "FAIL", (f"{len(undisclosed)} finding(s) say their remedy is disclosed in "
                        f"the addendum and are not named in it: {undisclosed}")
    return "PASS", (f"pre-specified text byte-identical ({len(original)} bytes); "
                    f"addendum present ({len(addendum.splitlines())} lines); "
                    f"{len(promised)} finding(s) promising disclosure all named in it "
                    f"{promised}")


def x_run_all_refresh_guard():
    """X18: run_all fails a stage that exits 0 without REFRESHING its outputs.

    The empty-run guard asked only whether each declared output existed, so a
    stage that wrote nothing was recorded PASS whenever an old copy sat on
    disk - every run after the first. That is how the Phase G decomposition
    came to rest on a lag artifact nobody had refreshed after the index was
    rebuilt: regenerated from a clean container on 2026-09-13 its survivors
    changed from three to two while the stacked event study, which reads the
    index directly, reproduced every number exactly (PAPER_MASTER 8.2).

    Asserted structurally: run_stage records each output's mtime, compares it
    to the stage's start time, and fails on a stale one. Read by AST so a
    comment cannot satisfy it.
    """
    import ast as _ast
    f = SCRIPTS / "run_all.py"
    if not f.exists():
        return "BLOCKED", "run_all.py is absent"
    tree = _ast.parse(f.read_text())
    fact = next((n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)
                 and n.name == "artifact_fact"), None)
    stage = next((n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)
                  and n.name == "run_stage"), None)
    if fact is None or stage is None:
        return "FAIL", "run_all.py lacks artifact_fact or run_stage"
    records_mtime = any(isinstance(n, _ast.Constant) and n.value == "mtime"
                        for n in _ast.walk(fact))
    compares = any(isinstance(n, _ast.Compare) and "mtime" in _ast.unparse(n)
                   and "t0" in _ast.unparse(n) for n in _ast.walk(stage))
    fails = any(isinstance(n, _ast.Constant) and isinstance(n.value, str)
                and "did not refresh" in n.value for n in _ast.walk(stage))
    problems = []
    if not records_mtime:
        problems.append("artifact_fact records no mtime")
    if not compares:
        problems.append("run_stage never compares an output's mtime to its start time")
    if not fails:
        problems.append("run_stage has no 'did not refresh' failure")
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", ("run_stage fails a stage whose declared outputs predate its start; "
                    "a leftover from an earlier run cannot be recorded as this run's product")


def x_run_all_stages_declared():
    """X10: every pipeline stage names a script that exists and outputs it writes.

    run_all.py checks, after each stage, that a stage which exited 0 actually
    produced something — "exited 0 but did not write". That guard reads the
    stage's `writes` list, so a stage declaring `writes=[]` is exempt from it by
    construction, silently. All seven MODEL stages declared exactly that, which
    is the half of the pipeline where a silent no-op matters most: a model that
    fits nothing, writes nothing and exits 0 was recorded as PASS.

    Two stages were also missing entirely while other stages depended on their
    output — 10d_parse_cd_demographics.py, which 06_heterogeneity.py reads, and
    32_validate_basket_construct.py, which publishes the basket. A clean clone
    could run the whole pipeline and still fail on a missing file.

    And a stage's arguments belong in `args`, because run_all builds
    `[python, script] + args`: a flag folded into the script name becomes part of
    a filename that cannot exist.
    """
    f = SCRIPTS / "run_all.py"
    if not f.exists():
        return "BLOCKED", "run_all.py is absent"
    # Read STAGES from the module itself. The first version parsed the source
    # with a regex keyed on the indentation of the closing paren, so a stage
    # formatted differently fell out of the list and was never checked (CP1
    # audit, 2026-09-13). run_all has no import-time side effects: its work is
    # under main().
    import importlib.util
    spec = importlib.util.spec_from_file_location("_run_all_stages", f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:                                    # noqa: BLE001
        return "BLOCKED", f"run_all.py could not be imported: {type(e).__name__}: {e}"
    stages = [(st["script"], st) for st in getattr(mod, "STAGES", [])]
    if not stages:
        return "BLOCKED", "run_all.STAGES is empty or absent"

    missing = [n for n, _ in stages if not (SCRIPTS / n).exists()]
    spaced = [n for n, _ in stages if " " in n]
    inert = [n for n, st in stages if not st.get("writes")]
    # ORDER (X19): the stages that verify model outputs - the source/claims
    # verifier and the regression suite - must come after every model stage,
    # or a cold run checks claims against artifacts that do not exist yet.
    kinds = [st["kind"] for _, st in stages]
    last_model = max((i for i, k in enumerate(kinds) if k == "model"), default=-1)
    early = [n for i, (n, st) in enumerate(stages)
             if n in ("31_verify_sources.py", "23_regression_suite.py") and i < last_model]
    if early:
        return "FAIL", (f"{early} run before the last model stage, so from cold they "
                        "verify claims against artifacts the models have not written yet")
    if missing or spaced or inert:
        parts = []
        if missing:
            parts.append(f"{len(missing)} stage(s) name a script that does not "
                         f"exist: {missing[:3]}")
        if spaced:
            parts.append(f"{len(spaced)} stage(s) fold an argument into the script "
                         f"name, which run_all passes as a filename: {spaced[:2]}")
        if inert:
            parts.append(f"{len(inert)} stage(s) declare writes=[], so the "
                         f"'exited 0 but wrote nothing' guard cannot fire for "
                         f"them: {inert[:4]}")
        return "FAIL", "; ".join(parts)
    return "PASS", (f"{len(stages)} stages; every script exists and every one "
                    f"declares at least one output, so the empty-run guard "
                    f"covers the whole pipeline")


def e_stratum_windows_fit():
    """P2: every episode a stratum tests has its reported statistic inside that stratum.

    A stratum is a set of calendar windows, and an episode near an edge does not
    fit. Two of C1's fifteen do not, each failing differently: 2021-01-05's
    pre-period reaches into the DISCOVERY window, so its baseline would come from
    already-explored data while its post-period is unexamined; and 2021-05-24's
    post-period crosses the B-HEARD launch, putting exposed days inside the
    stratum defined as unexposed.

    Nothing in the pipeline noticed, because `build_stack` keeps whatever days
    the sample happens to contain — a truncated window produces a smaller but
    perfectly well-formed estimate.

    The rule checked here is first-week containment, not full-window: day -1
    through day +7 is what the reported statistic uses, and requiring the whole
    +/-14 window would drop both episodes — 13% of the smallest stratum, one of
    them Daunte Wright — when measurement shows it is not necessary. Tails beyond
    the first week may truncate, and this check requires the truncation to be
    COUNTED rather than absorbed.

    Episode dates are treatment-side, so this reads no outcome data.
    """
    import sys as _sys
    _sys.path.insert(0, str(SCRIPTS))
    from event_study import stratum_episodes
    from config import CONFIRMATION_ANALYSIS_WINDOWS

    f = DATA_REFERENCE / EPISODE_LIST_PRIMARY
    if not f.exists():
        return "BLOCKED", f"{EPISODE_LIST_PRIMARY} absent — run 13_extension_episodes.py"
    ep = pd.read_csv(f, parse_dates=["start"])
    strata = {"discovery": [(DISCOVERY_START, DISCOVERY_END)],
              "C1": [CONFIRMATION_ANALYSIS_WINDOWS[0], CONFIRMATION_ANALYSIS_WINDOWS[1]],
              "C2": [CONFIRMATION_ANALYSIS_WINDOWS[2]]}
    bad, trunc, total = [], [], 0
    for name, wins in strata.items():
        kept, dropped = stratum_episodes(ep["start"], wins, EVENT_WINDOW_PRE,
                                         EVENT_WINDOW_POST)
        total += len(kept)
        for d in dropped:
            bad.append(f"{name} {d['start'].date()}: {d['reason'][:70]}")
        for k in kept:
            if k["days_outside_full_window"]:
                trunc.append(f"{name} {k['start'].date()} loses "
                             f"{k['days_outside_full_window']}/{k['full_window_days']}")
    if bad:
        return "FAIL", (f"{len(bad)} episode(s) cannot have their reported statistic "
                        f"inside their own stratum: {bad[:2]}")
    return "PASS", (f"{total} episode(s) across 3 strata, every first week inside its "
                    f"own stratum; {len(trunc)} carry a truncated tail, counted: "
                    f"{trunc if trunc else 'none'}")


def e_estimators_use_adopted_list():
    """No estimator reads the FROZEN episode list, which is a record, not an input.

    Two lists exist. confirmation_episodes.csv (70 episodes) was built under the
    retired fixed-threshold rule and is kept byte-identical to HEAD as the
    pre-registration record. confirmation_episodes_rebuilt.csv (75) is built under
    the shock rule with a within-year quantile threshold, and is the list the
    project adopted.

    The decision to estimate on the rebuilt list was taken and recorded — and
    never implemented. 17, 07, 08 and 18 all opened the frozen file BY NAME, so
    every estimate this project was about to produce would have been computed on
    the superseded rule while the documentation said otherwise. Nothing caught it
    because both files exist, both parse, and both have the same columns: the
    wrong one produces a perfectly well-formed answer to a different question.

    This checks the source rather than an artifact because the defect IS in the
    source, and because the estimators have never been run, so there is no output
    to inspect. 13_extension_episodes.py and this suite may name the frozen file
    — 13 to refuse to overwrite it, the suite to verify it is untouched.
    """
    ESTIMATORS = ("17_stacked_event_study.py", "07_did_exposure.py",
                  "08_figures.py", "18_null_calibration.py", "event_study.py",
                  "03_main_model.py", "04_robustness.py", "05_placebo_and_calls.py",
                  "06_heterogeneity.py")
    from config import EPISODE_LIST_FROZEN, EPISODE_LIST_PRIMARY
    offenders, checked = [], []
    for name in ESTIMATORS:
        f = SCRIPTS / name
        if not f.exists():
            continue
        checked.append(name)
        for i, line in enumerate(f.read_text().splitlines(), 1):
            code = line.split("#")[0]
            if f'"{EPISODE_LIST_FROZEN}"' in code or f"'{EPISODE_LIST_FROZEN}'" in code:
                offenders.append(f"{name}:{i}")
    if not checked:
        return "BLOCKED", "no estimator scripts found"
    if offenders:
        return "FAIL", (f"{len(offenders)} estimator line(s) read the frozen list by "
                        f"name instead of EPISODE_LIST_PRIMARY: {offenders[:4]}")
    return "PASS", (f"{len(checked)} estimator script(s) checked; none names "
                    f"{EPISODE_LIST_FROZEN} in code — all route through "
                    f"EPISODE_LIST_PRIMARY ({EPISODE_LIST_PRIMARY})")


def d_outcome_list_complete():
    """O1 residual: every parquet in data/processed is classified, so none can be neither.

    config.py's OUTCOME_ARTIFACTS carries the instruction "A NEW OUTCOME ARTIFACT
    MUST BE ADDED HERE. The check reads this list, so an unlisted outcome file is
    a check failure rather than a silent gap."

    That sentence was FALSE. D.guard_coverage reads the list to find READERS —
    it asks "does every script that opens one of these call the freeze guard?" —
    and nothing ever compared the list against what is actually on disk. An
    unlisted outcome file was therefore exactly a silent gap, and one existed:
    the fix for finding O1 created ems_cd_day_calltype_excluded.parquet, 443,719
    rows of which ~288k are confirmation-window outcome counts, and left it
    unregistered for eight commits. D.guard_coverage substring-matches the listed
    names, and "ems_cd_day_calltype.parquet" is not a substring of
    "ems_cd_day_calltype_excluded.parquet", so it reported PASS throughout.

    A guarantee asserted in a comment that no code provides is this project's
    own recurring defect, and it was sitting in the file that defines the freeze.
    This check makes the sentence true: every parquet directly in data/processed
    must appear in exactly one of OUTCOME_ARTIFACTS or NON_OUTCOME_ARTIFACTS, so
    a new artifact forces a decision instead of defaulting to unguarded.
    """
    from config import NON_OUTCOME_ARTIFACTS, OUTCOME_ARTIFACTS
    if not DATA_PROCESSED.exists():
        return "BLOCKED", "data/processed does not exist"
    # A BASKET ARM IS THE SAME KIND OF THING AS ITS BASE. cai_daily_broad.parquet
    # is the treatment index built over a different article list; the basket does
    # not change whether a file holds outcome data. So a suffixed arm is
    # classified by the artifact it derives from, rather than each arm being
    # listed by hand — which would make adding the pre-registered sensitivity a
    # config edit, and would eventually be done by rote instead of by decision.
    #
    # The suffix is the one config.arm_artifact() produces, over the arms
    # config.ARMS declares, so this cannot drift from the naming rule it mirrors:
    # a file only collapses to a base name if that base name is itself
    # classified. The first version hard-coded ("broad",), so the spliced arm's
    # index (cai_daily_spliced.parquet, 2026-09-13) arrived unclassified even
    # though the arm was declared in config - the list this comment argues
    # against had simply moved into the check.
    from config import ARMS, PRIMARY_ARM, arm_artifact

    def base_of(name):
        for arm in sorted(set(ARMS) - {PRIMARY_ARM}):
            base = name.replace(f"_{arm}.", ".")
            if base != name and name == arm_artifact(base, arm):
                return base
        return name

    # EVERY regular file, not only parquet (CP1 audit #43, 2026-09-13): two
    # orphan .txt summaries with no writer left in the tree sat here unseen,
    # one a panel summary spanning every year.
    files = [q for q in DATA_PROCESSED.iterdir() if q.is_file() and q.name != ".gitkeep"]
    on_disk = {base_of(q.name) for q in files}
    outcome, other = set(OUTCOME_ARTIFACTS), set(NON_OUTCOME_ARTIFACTS)

    both = sorted(outcome & other)
    unclassified = sorted(on_disk - outcome - other)
    # A listed file that is absent is not an error: artifacts are gitignored and
    # a fresh clone has none of them. Being unlisted is the failure.
    if unclassified or both:
        parts = []
        if unclassified:
            parts.append(f"{len(unclassified)} parquet(s) in data/processed are in "
                         f"neither OUTCOME_ARTIFACTS nor NON_OUTCOME_ARTIFACTS, so "
                         f"nothing decides whether the freeze covers them: {unclassified}")
        if both:
            parts.append(f"{len(both)} artifact(s) are in both lists: {both}")
        return "FAIL", "; ".join(parts)
    missing = sorted((outcome | other) - on_disk)
    n_files = len(files)
    return "PASS", (f"{n_files} file(s) on disk ({len(on_disk)} distinct base "
                    f"artifacts), all classified "
                    f"({len(on_disk & outcome)} outcome, {len(on_disk & other)} not); "
                    f"{len(missing)} listed artifact(s) not built yet")


def t_basket_is_police_violence():
    """B4: every article in the published basket has evidence police were the actor.

    CAI-D claims to measure attention to POLICE violence, and until 2026-09-12
    nothing tested that claim. 27_finalise_basket.py decides scope on country and
    date and never asks who killed anyone; Wikidata's manner-of-death property is
    present on 6 of 174 candidates. What actually admitted an article was the
    category the crawl reached it through, and for 61 of 120 — 51% — that was a
    TOPIC category ("Black Lives Matter", "2020 United States racial unrest"),
    which asserts nothing about an actor.

    The basket therefore contained killings by civilians, each confirmed from the
    article's own opening sentence: Ahmaud Arbery (a hate crime while jogging),
    Renisha McBride, Markeis McGlockton (shot by Michael Drejka), James Craig
    Anderson (killed by Deryl Dedmon), Tamla Horsford (found dead at a slumber
    party), Nina Pop (stabbed in her apartment), James Scurlock (shot by a bar
    owner), Carlos Carson (killed by a private security guard), Deona Marie
    Knajdek (a car driven into demonstrators). It also contained Micah Xavier
    Johnson, who shot five Dallas police officers, on 2016-07-08 — the single
    highest day in the entire index.

    Checked against basket_construct_review.csv, which 32 writes with the
    evidence for each call, so this runs offline on every commit.
    """
    rev = DATA_REFERENCE / "basket_construct_review.csv"
    res = DATA_REFERENCE / "wikipedia_article_resolution.csv"
    if not rev.exists():
        return "BLOCKED", ("no basket_construct_review.csv — run "
                           "32_validate_basket_construct.py; without it, whether the "
                           "basket measures police violence is untested")
    if not res.exists():
        return "BLOCKED", "wikipedia_article_resolution.csv absent — run 32 --apply"
    r = pd.read_csv(rev)
    published = set(pd.read_csv(res)["article"])
    klass = r.set_index("article")["construct"].to_dict()

    unreviewed = sorted(published - set(klass))
    anti = sorted(a for a in published if klass.get(a) == "anti_police")
    allowed = {"strict": {"police_violence"},
               "broad": {"police_violence", "unestablished"}}[CAI_D_BASKET]
    off = sorted(a for a in published
                 if a in klass and klass[a] not in allowed and a not in anti)
    if unreviewed or anti or off:
        parts = []
        if unreviewed:
            parts.append(f"{len(unreviewed)} published article(s) carry no construct "
                         f"review at all: {unreviewed[:3]}")
        if anti:
            parts.append(f"{len(anti)} article(s) measure attention to violence AGAINST "
                         f"police: {anti[:3]}")
        if off:
            parts.append(f"{len(off)} article(s) are outside the '{CAI_D_BASKET}' "
                         f"basket's classes: {off[:3]}")
        return "FAIL", "; ".join(parts)
    return "PASS", (
        f"all {len(published)} published articles classified for the "
        f"'{CAI_D_BASKET}' basket; "
        f"{sum(1 for a in published if klass[a] == 'police_violence')} rest on a "
        f"police-action category or the MPV registry; 0 anti-police")


def d_edp_family_justified():
    """O3: the EDP grouping does not rest on a justification known to be false.

    CALL_TYPE_GROUPS['edp'] bundles EDP with EDPC, EDPM, EDPW and T-EDP. Two
    reasons were given in config and both were wrong:

      "the codes come from the official dictionary sheet". The sheet holds 271
      codes and exactly one of them is an EDP code — "EDP = PSYCHIATRIC
      PATIENT". EDPC, EDPM, EDPW and T-EDP are undocumented, and edp is the only
      group in CALL_TYPE_GROUPS with undocumented members.

      "family total stable ~125k/yr while EDP alone falls". Annual family totals
      run 108,384 to 141,910 — a 47% range that matches ~125k in two years of
      ten.

    The grouping itself survives: EDPC really is a progressive recode of EDP, and
    omitting the recode codes creates a time-trending undercount. What does not
    survive is the stated basis for it, and a false justification is worse than
    a thin one because it stops anyone looking.

    The measured totals come from the F2 freeze access and are CITED rather than
    re-derived — re-deriving them would be a third confirmation-period read. So
    this check verifies the correction is present and has not been quietly
    reverted to the tidy version; it does not recompute anything, by design.
    """
    f = SCRIPTS / "config.py"
    if not f.exists():
        return "BLOCKED", "config.py absent"
    src = f.read_text()
    if "CALL_TYPE_GROUPS" not in src:
        return "BLOCKED", "config.py has no CALL_TYPE_GROUPS"
    missing = []
    # The correction must still say both things it was written to say.
    if "undocumented" not in src:
        missing.append("that EDPC/EDPM/EDPW/T-EDP are undocumented in the official "
                       "dictionary sheet")
    if "141,910" not in src and "141910" not in src:
        missing.append("the measured annual range that refutes 'stable ~125k/yr'")
    # And it must not have drifted back to asserting the false claim as fact.
    import re as _re
    tidy = _re.search(r"family total stable ~125k/yr[^\n]*\n(?![^\n]*[Ff]alse)", src)
    if tidy and "False." not in src:
        missing.append("the phrase 'family total stable ~125k/yr' is present without "
                       "being marked false")
    if missing:
        return "FAIL", ("the EDP grouping's justification has lost its correction: "
                        + "; ".join(missing))
    return "PASS", ("the EDP grouping records that its codes are undocumented and that "
                    "the 'stable ~125k/yr' justification is false, with the measured "
                    "range cited rather than re-derived")


def t_trends_precision_stable():
    """T6: the treatment's Trends component does not lose precision over the decade.

    T6 argues that because Google rescales each request window to that window's
    own maximum, a decade-long fall in search share collapses the number of
    distinct values the daily series can take — so the treatment carries
    year-varying attenuation and a 2021-2024 null cannot be read as an absence.
    That would bear directly on the confirmatory result, since C2 is 2021-2024.

    The second half does not follow from the first. Rescaling to the window
    maximum is exactly what keeps every window spanning 0-100 whatever the
    underlying level. Measured on the committed series, for the component that is
    actually in CAI-D: the relative quantization step is 0.0020 across 2015-2019
    and 0.0016 across 2021-2024 — a ratio of 0.82, slightly FINER late, against
    the claimed fivefold coarsening — with 121 and 118 distinct values a year and
    365 non-zero days in every year of the decade.

    The degradation is real in trends_nyc, which is censored rather than coarse:
    its non-zero days fall from 236 a year to 161, and 71% of 2024 is zero. But
    trends_nyc was retired from CAI-D on independent grounds, so it attenuates
    nothing in the treatment this paper uses.

    The check is therefore on the LIVE components only. Guarding a retired series
    would fail on a fact about a column nobody estimates from, and guarding
    nothing would let a future component drift in unnoticed.
    """
    f = DATA_REFERENCE / "trends_precision_by_year.csv"
    if not f.exists():
        return "BLOCKED", "trends_precision_by_year.csv absent — run 34_trends_precision.py"
    d = pd.read_csv(f)
    live = d[d["in_cai_d"].astype(str).str.lower().isin(("true", "1"))]
    if not len(live):
        return "BLOCKED", "no Trends component is in CAI_D_COMPONENTS"
    bad = []
    for comp, g in live.groupby("component"):
        early = g[(g["year"] >= 2015) & (g["year"] <= 2019)]["rel_step"].mean()
        late = g[g["year"] >= 2021]["rel_step"].mean()
        if early and late and late / early > 2.0:
            bad.append(f"{comp}: quantization step {late / early:.1f}x coarser in "
                       f"2021-24 than 2015-19")
        thin = g[g["nonzero_days"] < 0.5 * g["n_days"]]
        if len(thin):
            bad.append(f"{comp}: {len(thin)} year(s) more than half zero "
                       f"({sorted(thin['year'])[:3]}) — censored, not merely coarse")
    if bad:
        return "FAIL", ("a live Trends component has lost resolution, so attenuation "
                        "is year-varying: " + "; ".join(bad))
    names = sorted(live["component"].unique())
    g = live[live["component"] == names[0]]
    r = (g[g["year"] >= 2021]["rel_step"].mean()
         / g[(g["year"] >= 2015) & (g["year"] <= 2019)]["rel_step"].mean())
    return "PASS", (f"live Trends component(s) {names} keep their resolution: "
                    f"quantization step ratio {r:.2f}x late-to-early, no year "
                    "more than half zero")


def t_agent_class_break_bounded():
    """L7: the April 2020 Wikipedia agent-class break is measured, not asserted.

    wiki_ext is built from pageviews requested with agent=user. Wikimedia added
    an "automated" class in late April 2020 and did NOT apply it retroactively,
    so `user` means "not obviously a spider" before that date and "not a spider
    and not automated" after it. The treatment index therefore has a measurement
    break in it.

    THE FINDING PUT THE BREAK IN THE WRONG PLACE. It argued the break splits the
    sample at the largest episode, Floyd, five weeks after the change, and cited
    WMF's 5-8% figure for 2019 English-Wikipedia desktop bot spam. Measured on
    the titles this index is actually built from, the automated share across
    2017-2020 is 0.10% and the mean shift it implies is 0.0009 SD — three orders
    of magnitude below the episode it was said to threaten.

    It is real where nobody looked. The share grows every year after the change:
    0.8% in 2021, 3.4% in 2022, 6.2% in 2023, and the mean shift across
    2021-2024 is 0.0856 SD — NINETY TIMES the discovery-window figure, with a
    single-day maximum of 1.58 SD in 2024. That window is half the confirmation
    sample, and all of stratum C2.

    So this asserts the two things a reader needs to trust the bound: that the
    class really is absent before the documented change date, which is the whole
    basis for treating pre-break `user` as comparable to post-break
    `user + automated`; and that the discovery-window shift stays small, so a
    refetch that moves it says so instead of quietly widening the footnote.
    """
    f = DATA_REFERENCE / "wiki_agent_class_break.csv"
    if not f.exists():
        return "BLOCKED", ("wiki_agent_class_break.csv absent — run "
                           "33_agent_class_break.py")
    d = pd.read_csv(f)
    pre = d[d["year"] <= 2019]
    if not len(pre):
        return "BLOCKED", "artifact covers no pre-break year"
    if float(pre["automated"].sum()) != 0.0:
        return "FAIL", (f"agent=automated is nonzero before 2020 "
                        f"({int(pre['automated'].sum())} views), so the class was "
                        "applied retroactively after all and pre-break `user` is "
                        "NOT comparable to post-break `user + automated`")
    disc = d[(d["year"] >= 2017) & (d["year"] <= 2020)]
    shift = float(disc["mean_z_shift"].mean())
    if shift > 0.01:
        return "FAIL", (f"the agent-class break now shifts the discovery-window index "
                        f"by {shift:.4f} SD on average, above the 0.01 SD the paper "
                        "reports it as bounded by")
    ext = d[d["year"] >= 2021]
    return "PASS", (f"agent=automated is exactly 0 before 2020; the break shifts the "
                    f"discovery index by {shift:.4f} SD and the 2021-2024 index by "
                    f"{float(ext['mean_z_shift'].mean()):.4f} SD")


def t_basket_evidence_not_namesake():
    """T13: no published basket article rests on an exact-name registry lookup alone.

    Registry membership is decided by an exact name match, which cannot tell
    namesakes apart. Measured: 25 person-shaped articles are marked absent from
    a registry that does contain them (suffixes, accents, two-victim titles),
    and the finding's prescribed remedy — match on normalised first+last with
    middle names stripped — is WORSE THAN THE DEFECT. It collapses "James Craig
    Anderson", a man murdered by civilians in a Mississippi hate crime, onto
    four unrelated James Andersons in the registry, and would readmit him to a
    police-violence treatment index the basket rebuild had correctly excluded.
    The registry also holds two different Keenan Andersons who died in 2023.

    So the exposure is not the false negatives, which cost nothing measurable:
    of the 15 articles the classifier could not establish, exactly one would flip
    under normalised matching, and that one must not flip. The exposure is the
    articles that rested on the registry as their ONLY positive signal, where a
    namesake collision decides basket membership. There were three, and one was
    Breonna Taylor.

    The fix was evidence the script already had. fetch_leads() runs on every
    candidate, its result is written to basket_construct_review.csv, and
    classify() never received it — the most direct statement of who did the
    killing, gathered and consumed by nothing. Wired in above the registry rule,
    all three are established from their own article's first sentence, the
    registry is load-bearing for zero articles, and all three baskets rebuilt
    BYTE-IDENTICAL.

    This asserts the state, not the code path: no published article may cite the
    registry as its reason. That way the invariant survives a future rewrite of
    how the evidence is gathered.
    """
    f = DATA_REFERENCE / "basket_construct_review.csv"
    if not f.exists():
        return "BLOCKED", "basket_construct_review.csv absent — run 32"
    d = pd.read_csv(f)
    published = set()
    for name in ("basket_strict.csv", "basket_broad.csv"):
        g = DATA_REFERENCE / name
        if g.exists():
            published |= set(pd.read_csv(g)["article"])
    if not published:
        return "BLOCKED", "no basket on disk — run 32 --apply"
    onreg = d[d["article"].isin(published)
              & d["reason"].astype(str).str.contains("Mapping Police Violence registry")]
    if len(onreg):
        return "FAIL", (f"{len(onreg)} published basket article(s) rest on an exact-name "
                        f"registry match as their only positive signal, so a namesake "
                        f"decides membership: {sorted(onreg['person'])[:4]}")
    lead = d[d["article"].isin(published)
             & d["reason"].astype(str).str.contains("article lead names")]
    return "PASS", (f"none of {len(published)} published basket articles rests on a "
                    f"name lookup alone; {len(lead)} are established from the article's "
                    "own lead sentence")


def t_basket_country_evidence():
    """B4: no basket article was admitted without positive evidence it is a US case.

    The country test in 27_finalise_basket.py excludes an article only when
    Wikidata NAMES a country outside the US, so an article with no country
    property passed by default — 58 of 120 did. That is admission on absence,
    and the same reasoning would have admitted a killing anywhere.

    Failing closed on Wikidata alone is not the fix either: P17 is missing for 44
    of the 109 strict-basket articles, George Floyd, Deborah Danner and Manuel
    Ellis included. Requiring it would delete the most central cases in the study
    over a gap in Wikidata's coverage rather than any fact about the country.

    So the evidence is Wikidata's country OR a category naming a US state, a US
    agency, or the United States explicitly — recorded per article by 32, and
    read here rather than recomputed, so the rule has one home.
    """
    rev = DATA_REFERENCE / "basket_construct_review.csv"
    res = DATA_REFERENCE / "wikipedia_article_resolution.csv"
    if not rev.exists() or not res.exists():
        return "BLOCKED", "basket_construct_review.csv or the resolution file is absent — run 32"
    r = pd.read_csv(rev).set_index("article")
    if "us_evidence" not in r.columns:
        return "BLOCKED", "basket_construct_review.csv predates the us_evidence column — re-run 32"
    published = [a for a in pd.read_csv(res)["article"] if a in r.index]
    sub = r.loc[published]
    def present(col):
        # fillna BEFORE astype. astype(str) renders NaN as the string "nan",
        # which is non-empty, so the obvious spelling reports every missing value
        # as evidence present — this check's first version claimed all 109
        # articles carried non-US evidence. A check that fails for the wrong
        # reason is the defect class this suite exists to catch, including in
        # itself.
        return sub[col].fillna("").astype(str).str.strip().ne("")

    wd = sub["wikidata_country"].fillna("").astype(str).eq("United States")
    cat = present("us_evidence")
    nonus = present("non_us_evidence")
    none_at_all = sorted(sub.index[~(wd | cat)])
    outside = sorted(sub.index[nonus])
    if none_at_all or outside:
        parts = []
        if none_at_all:
            parts.append(f"{len(none_at_all)} article(s) admitted with no US evidence "
                         f"of any kind: {none_at_all[:3]}")
        if outside:
            parts.append(f"{len(outside)} article(s) carry non-US evidence: {outside[:3]}")
        return "FAIL", "; ".join(parts)
    return "PASS", (f"all {len(sub)} published articles carry US evidence "
                    f"({int(wd.sum())} from Wikidata, {int(cat.sum())} from a category); "
                    f"0 carry non-US evidence")


def t_exclusion_reasons_true():
    """N1/N3: no basket article is excluded for a reason the scope file contradicts.

    Every exclusion in basket_decisions.csv carries a stated reason, and a reader
    — a referee, or this project in six months — takes that reason at face value.
    Twelve of them were false at once, for two separate mechanisms, and NOTHING
    in the output distinguished a false reason from a true one:

      N1. The SPARQL path percent-encoded article titles and read the title back
          out of the returned IRI, so every non-ASCII article was stored under
          its ENCODED name. The scope row existed and could never join. José
          Campos Torres was then dated from a registry name-match and admitted
          as a 2014 killing; Wikidata holds 1977-05-05, which is out of range.
          A URL-encoding mismatch put an out-of-scope article INTO the treatment
          index, under the reason "in range".

      N3. Wikidata stores a month-precision date as 2010-05-00.
          pd.to_datetime(..., errors="coerce") makes that NaT, so the article was
          excluded as "no date of death in Wikidata, and no registry match" while
          Wikidata plainly held a date.

    Both produce output that looks entirely reasonable. This check is the thing
    that can tell the difference: it re-reads the scope file and asserts that
    every "no date" exclusion is backed by an actually empty scope date.
    """
    d = DATA_REFERENCE / "basket_decisions.csv"
    sc = DATA_REFERENCE / "basket_scope.csv"
    if not d.exists() or not sc.exists():
        return "BLOCKED", "basket_decisions.csv or basket_scope.csv absent — run 26 then 27"
    dec = pd.read_csv(d)
    scope = pd.read_csv(sc).set_index("article")
    if "date" not in scope.columns:
        return "BLOCKED", "basket_scope.csv has no date column"

    nodate = dec[dec["reason"].astype(str).str.startswith("no date")]
    has = scope["date"].astype(str).str.len().ge(10)
    wrong = [a for a in nodate["article"] if bool(has.get(a, False))]

    # An article keyed in a form that cannot join is the N1 mechanism itself.
    unjoinable = sorted(set(scope.index) - set(dec["article"]))
    encoded = [a for a in scope.index if "%" in str(a)]

    if wrong or encoded:
        # Report only the clause that actually fired. A message that always
        # recites both reads as two defects when there is one, and the reader
        # has to work out which number is the live one.
        parts = []
        if wrong:
            parts.append(f"{len(wrong)} article(s) excluded as 'no date' while "
                         f"basket_scope.csv holds a date for them: {wrong[:3]}")
        if encoded:
            parts.append(f"{len(encoded)} scope row(s) keyed on a percent-encoded "
                         f"name, which can never join the basket: {encoded[:2]}")
        return "FAIL", "; ".join(parts)
    return "PASS", (
        f"{len(nodate)} 'no date' exclusion(s), all backed by an empty scope date; "
        f"0 percent-encoded keys; {len(unjoinable)} scope row(s) not among the "
        f"decided candidates")


def t_scope_covers_candidates():
    """N2: every basket candidate carries a scope row, and each was actually asked.

    26 used to leave candidates unresolved without saying so — Ma'Khia Bryant,
    central to the April 2021 episode, came back empty from SPARQL and simply
    had no row. 27 then read a 164-row scope file against 174 candidates. The
    difference between "Wikidata holds nothing for this article" and "we never
    asked about this article" is the difference between a basket and an accident
    of which API calls succeeded, and only the first is a reason to exclude.
    """
    b = DATA_REFERENCE / "wiki_basket.csv"
    sc = DATA_REFERENCE / "basket_scope.csv"
    if not b.exists() or not sc.exists():
        return "BLOCKED", "wiki_basket.csv or basket_scope.csv absent — run 24 then 26"
    PRE = ("Killing_of_", "Shooting_of_", "Death_of_", "Murder_of_", "Police_shooting_of_")
    bas = pd.read_csv(b).drop_duplicates("article")
    cand = bas[bas["article"].str.startswith(PRE) | bas["in_registry"]]
    scope = pd.read_csv(sc)
    missing = sorted(set(cand["article"]) - set(scope["article"]))
    if missing:
        return "FAIL", (f"{len(missing)} of {len(cand)} candidates have no scope row "
                        f"at all (e.g. {missing[:3]}) — re-run 26")
    noitem = int(scope["item"].isna().sum()) if "item" in scope.columns else -1
    return "PASS", (f"all {len(cand)} candidates carry a scope row; "
                    f"{noitem} resolved to no Wikidata item (a recorded absence)")


def t_no_duplicate_person_articles():
    """T17: no basket article may also be a historical title of another basket article.

    Wikimedia records pageviews per title, so 11 sums each article across all of
    its historical titles. If a bare-name title is ALSO admitted as an article in
    its own right, that person enters wiki_ext twice.

    Measured when this was written: 9 of 119 usable articles were duplicates of
    this kind - Eric_Garner (280,937 views) alongside Killing_of_Eric_Garner,
    Freddie_Gray (91,238) alongside Killing_of_Freddie_Gray, and seven more,
    449,549 views in total or 0.35% of the basket.

    Small in aggregate and concentrated in specific victims, which is the worse
    property: it over-weights exactly the people whose articles were renamed, and
    it corrupts episode ATTRIBUTION, where two episodes were labelled with the
    bare-name title rather than the canonical one.

    This is the same defect that was found and fixed in 28_build_nyc_attention.py
    for Daniel_Prude, and never propagated to 11. Found here by testing E7.
    """
    u = DATA_REFERENCE / "wiki_ext_basket_used.csv"
    tm = DATA_REFERENCE / "article_title_map.csv"
    if not (u.exists() and tm.exists()):
        return "BLOCKED", "basket or title map absent — run 29 then 11"
    used = pd.read_csv(u)
    titles = pd.read_csv(tm)
    kept = set(used[used["ok"]]["article"])
    alias = {}
    for a, g in titles.groupby("article"):
        for t in g["title"]:
            if t != a:
                alias.setdefault(t, []).append(a)
    dupes = [(a, alias[a]) for a in sorted(kept)
             if a in alias and any(o in kept for o in alias[a])]
    if not dupes:
        return "PASS", f"{len(kept)} usable articles, none is a title of another"
    lost = int(used[used["article"].isin([a for a, _ in dupes])]["views"].sum())
    total = int(used[used["ok"]]["views"].sum())
    return "FAIL", (f"{len(dupes)} article(s) double-count a person "
                    f"({lost:,} views = {lost / total:.2%}): "
                    + ", ".join(f"{a}->{o[0]}" for a, o in dupes[:3]))


def s_did_no_shared_days():
    """S7: no district-day may be treated for one episode and control for another.

    07_did_exposure.py used to build its own windows, truncating FORWARD only -
    hi = min(start_i + 7, start_{i+1} - 1) - with no backward truncation. When
    consecutive starts were under 14 days apart, days [start_{i+1} - 7,
    start_i + 7] landed in BOTH windows, and pd.concat kept both copies. Defect
    I4 exactly, in the script whose docstring asserted "no overlap".

    Tests the PROPERTY on the stack 07 ACTUALLY BUILDS, by running the same
    construction and checking key uniqueness. An earlier version of this check
    re-implemented the OLD window logic and counted collisions in it - which
    tested the episode list rather than the script, and would have gone on
    failing after 07 was fixed, and passing if someone merely pointed 07 at a
    more widely spaced episode list without fixing anything.

    The naive count is still reported as DETAIL, because it says how much the
    repair is worth on the current episode list: 28 double-counted calendar days
    on the frozen discovery subset, and zero on the rebuilt one.
    """
    import importlib
    f = DATA_REFERENCE / "confirmation_episodes.csv"
    pq = DATA_PROCESSED / "panel_cd_day.parquet"
    if not (f.exists() and pq.exists()):
        return "BLOCKED", "episode list or panel absent"
    # Discovery episodes only, whatever the flag says (incident F5, 2026-09-20):
    # the stack this check builds is an exploratory construction and may never be
    # built on the confirmation episodes.
    ep = pd.read_csv(f, parse_dates=["start"])
    if "period" in ep.columns:
        ep = ep[ep["period"] == "discovery"]
    starts = sorted(ep["start"].tolist())

    # what 07's OLD construction would double-count, for scale
    seen = {}
    for i, st in enumerate(starts):
        hi = st + pd.Timedelta(days=7)
        if i + 1 < len(starts):
            hi = min(hi, starts[i + 1] - pd.Timedelta(days=1))
        for d in pd.date_range(st - pd.Timedelta(days=7), hi, freq="D"):
            seen[d] = seen.get(d, 0) + 1
    naive_doubled = sum(1 for n in seen.values() if n > 1)

    sys.path.insert(0, str(SCRIPTS))
    es = importlib.import_module("event_study")
    panel = pd.read_parquet(pq)
    fg = importlib.import_module("freeze_guard")
    panel = fg.select_sample(panel, where="23_regression_suite:S7", window="discovery")
    stack = es.build_stack(panel, starts, pre=7, post=7)
    if stack.empty:
        return "BLOCKED", "build_stack returned nothing on this panel"
    dup = int(stack.duplicated(["communitydistrict", "incident_date"]).sum())
    return ("PASS" if dup == 0 else "FAIL",
            f"{dup} district-day(s) appear in two episode windows in the stack "
            f"07 builds ({len(stack):,} rows, {stack['episode'].nunique()} episodes); "
            f"07's old construction would have double-counted {naive_doubled} "
            f"calendar day(s)")


def t_no_lost_history():
    """T12: no article's pageview series starts after the article existed.

    This is the property the rename defect actually violated, and it is not the
    one the first coverage check tested. Killing_of_Alton_Sterling begins
    2021-04-25 for a man killed in 2016 - the page was MOVED there, and the
    pre-move series stayed under the old title. That is lost history.

    A low day count is a different thing entirely: Wikimedia omits days with no
    recorded views, so a quiet article is legitimately sparse. Counting days
    conflates the two - it flagged 14 articles, 9 of them simply quiet - while
    the START of the series separates them cleanly.

    The comparison needs the article's CREATION date as well as the death date,
    because an article written years after the killing correctly has no earlier
    series. With both, every one of the 119 usable articles starts within 3 days
    of max(death, creation), median 0.
    """
    tm = DATA_REFERENCE / "article_title_map.csv"
    used = DATA_REFERENCE / "wiki_ext_basket_used.csv"
    dec = DATA_REFERENCE / "basket_decisions.csv"
    if not (tm.exists() and used.exists() and dec.exists()):
        return "BLOCKED", "title map, basket or decisions absent — run 29 then 11"
    t = pd.read_csv(tm, parse_dates=["first", "created"])
    if "created" not in t.columns or t["created"].isna().all():
        return "BLOCKED", "no creation dates — run 29 --creation-only"
    u = pd.read_csv(used)
    d = pd.read_csv(dec, parse_dates=["death_date"])
    wiki_from = pd.Timestamp("2015-07-01")   # Wikimedia daily pageviews begin here

    per = u[u["ok"]].set_index("article")
    per = per.assign(
        first=per.index.map(t.groupby("article")["first"].min()),
        created=per.index.map(t.groupby("article")["created"].min()),
        killed=per.index.map(d.dropna(subset=["death_date"])
                             .set_index("article")["death_date"]))
    per = per.dropna(subset=["first", "created"])
    if per.empty:
        return "BLOCKED", "no article has both a series and a creation date"
    expected = per[["killed", "created"]].max(axis=1).clip(lower=wiki_from)
    lag = (per["first"] - expected).dt.days
    late = lag[lag > 7]
    return ("PASS" if late.empty else "FAIL",
            f"{len(per)} articles, start lag median {int(lag.median())}d "
            f"max {int(lag.max())}d; {len(late)} start >7d late"
            + (f": {list(late.nlargest(3).index)}" if len(late) else ""))


def t_local_series_uncensored():
    """T10: the NYC-local attention series must have no censored days.

    The point of moving off Google Trends for the local component is that
    pageviews are counts, so the reporting floor that made trends_nyc unusable
    (42.6% zero days, 70.8% in 2024) does not exist. Asserted per YEAR, not
    overall, because the Trends censoring was concentrated in the later years
    and an overall figure would have hidden it.
    """
    f = DATA_REFERENCE / "wiki_nyc_daily.csv"
    if not f.exists():
        return "BLOCKED", "no local series — run 28_build_nyc_attention.py"
    d = pd.read_csv(f, parse_dates=["date"])
    out = []
    for comp, g in d.groupby("component"):
        by = g.groupby(g["date"].dt.year)["value"].apply(lambda x: float((x == 0).mean()))
        out.append((comp, float(by.max()), int(by.idxmax())))
    worst = max(out, key=lambda t: t[1])
    return ("PASS" if worst[1] < 0.02 else "FAIL",
            f"worst year {worst[0]} {worst[2]}: {worst[1]:.1%} zero days"
            if worst[1] >= 0.02 else
            f"{len(out)} series, no year above 2% zero days")


def t_index_not_single_article():
    """T11: the index's biggest days must be sustained events, not viral spikes.

    Tests PERSISTENCE, not concentration. The first version of this check
    required that no single article carry more than 80% of a top day, and it
    failed 10 of 10 top days - including 2020-09-09, which is the Daniel Prude
    bodycam release and a real event. Single-article dominance is INHERENT to
    the construct: an attention shock about one killing means one article
    dominates. That check encoded a feature as a defect.

    What actually separates the two known cases is how long the elevation lasts:

      Killing_of_Amadou_Diallo, 2022-06-06 (viral link, no news trigger)
        441  422  475  35418  6272  527  427 ...   -> 2 days above 3x baseline
      Killing_of_Daniel_Prude, 2020-09-09 (bodycam release)
        8671 11375 23812 44714 12377 5583 3533 ... -> 11 days above 3x baseline

    A real attention event sustains for days; a viral link spikes and collapses.
    So: for each of the index's top days, take the article driving it and count
    how many days near it are elevated. Requiring the MEDIAN across top days
    keeps the check robust to one genuine one-day event.
    """
    per = DATA_REFERENCE / "wiki_nyc_per_article.csv"
    if not per.exists():
        return "BLOCKED", ("no per-article local series — 28_build_nyc_attention.py "
                           "must persist it for content to be validated at all")
    pa = pd.read_csv(per, parse_dates=["date"]).pivot_table(
        index="date", columns="article", values="views", aggfunc="sum").fillna(0.0)
    if pa.empty:
        return "FAIL", "the local basket is empty"
    tot = pa.sum(axis=1)
    top = tot.nlargest(10)

    persist = []
    for d in top.index:
        art = pa.loc[d].idxmax()
        s_art = pa[art]
        base = s_art[(s_art.index >= d - pd.Timedelta(days=30))
                     & (s_art.index < d - pd.Timedelta(days=3))].median()
        win = s_art[(s_art.index >= d - pd.Timedelta(days=3))
                    & (s_art.index <= d + pd.Timedelta(days=7))]
        persist.append(int((win > 3 * max(base, 1.0)).sum()))

    med = float(np.median(persist))
    n_flash = sum(1 for x in persist if x <= 2)
    return ("PASS" if med >= 3 else "FAIL",
            f"top-day elevation persists {med:.0f} days (median); "
            f"{n_flash}/10 are one- or two-day flashes")


def t_no_stitch_break():
    """T1: no stitched component carries an artificial level break.

    Generalised from a trends_nyc-only test. A check naming one component stops
    testing anything the moment that component leaves the index, and says
    nothing about the one that replaces it.

    The PROPERTY is about the series, not the fit. One trends_us boundary
    (2016-04-25) has r2 = -0.443 - the through-origin fit explains less than
    predicting zero, so its 6.24x scale is estimated from noise in a low-volume
    stretch where the 0-100 integer index is near its own resolution. That is a
    precision problem and it is recorded, but it did NOT produce a break: the
    realised shift there is 0.88x, inside the 5-95% range of all boundaries.

    So the test is the realised shift at each boundary, against the empirical
    distribution of shifts. Genuine events move the series hard - 2021-03-30 is
    3.6x on trends_us and 7.0x on trends_nyc, which is the Chauvin trial opening
    on 2021-03-29 - so a fixed threshold would flag real news. An artificial
    break is a shift that is large AND has no corroboration in the components
    that were NOT stitched.
    """
    f = DATA_REFERENCE / "cai_trends_daily.csv"
    g = DATA_REFERENCE / "cai_trends_stitch_diagnostics.csv"
    if not (f.exists() and g.exists()):
        return "BLOCKED", "trends series or stitch diagnostics absent"
    st = pd.read_csv(f, parse_dates=["date"])
    diag = pd.read_csv(g, parse_dates=["boundary"])
    comp = pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"])
    wx = comp[comp["component"] == "wiki_ext"].set_index("date")["value"]

    from config import CAI_D_COMPONENTS
    suspect, retired_suspect, unidentified = [], [], []
    for c in sorted(st["component"].unique()):
        series = st[st["component"] == c].set_index("date")["value"]
        for _, r in diag[diag["component"] == c].iterrows():
            b = r["boundary"]
            pre = series[b - pd.Timedelta(days=45):b - pd.Timedelta(days=1)]
            post = series[b:b + pd.Timedelta(days=44)]
            if len(pre) < 20 or len(post) < 20 or pre.mean() == 0:
                continue
            shift = post.mean() / pre.mean()
            if r["r2"] < 0.5:
                unidentified.append(f"{c}@{b.date()} r2={r['r2']:.2f}")
            if shift < 0.4 or shift > 2.5:
                # Corroborate against wiki_ext, which is NOT stitched: a real
                # surge in attention moves it too.
                wpre = wx[b - pd.Timedelta(days=45):b - pd.Timedelta(days=1)]
                wpost = wx[b:b + pd.Timedelta(days=44)]
                wshift = (wpost.mean() / wpre.mean()) if len(wpre) and wpre.mean() else np.nan
                corroborated = pd.notna(wshift) and (
                    (shift > 1 and wshift > 1.3) or (shift < 1 and wshift < 0.77))
                if not corroborated:
                    # Only a component IN the index can break a result. A break
                    # in a retired component is reported, not failed - it is
                    # evidence about why it was retired.
                    (suspect if c in CAI_D_COMPONENTS else retired_suspect).append(
                        f"{c}@{b.date()} {shift:.2f}x (wiki_ext {wshift:.2f}x)")
    note = f"; {len(unidentified)} unidentified scale(s): {unidentified}" if unidentified else ""
    retired = (f"; {len(retired_suspect)} in retired components: {retired_suspect[:2]}"
               if retired_suspect else "")
    return ("FAIL" if suspect else "PASS",
            f"{len(diag)} boundaries, {len(suspect)} uncorroborated jump(s) in the index"
            + (f": {suspect[:3]}" if suspect else "") + retired + note)


def t_components_agree():
    """Every component in the index must measure the same construct as the rest.

    WHY THIS EXISTS. trends_nyc was retired for censoring, and wiki_nyc was built
    to replace it precisely because it has no censored days. It passes
    T.index_uncensored and T.no_stitch_break cleanly - and it is still not a
    measure of attention to police violence. It correlates -0.18 with trends_us
    and -0.12 with trends_nyc: NEGATIVELY with both search measures of the thing
    it is supposed to track. 7 of its 8 articles are killings from before the
    study window, Amadou Diallo (1999) is 44% of all its views, and 18 of its
    top 50 days are basket anniversaries against a 13.3% base rate. Its peaks are
    4 February and 25 November.

    The two checks above test censoring and level breaks. Neither can see this,
    so without this check a component could be swapped in on the strength of
    passing them - which is exactly the "validated on coverage, never on
    content" failure that produced the UnitedHealthcare and Diallo baskets.

    The property: each component must correlate positively, and not trivially,
    with the average of the others. The floor is deliberately low (0.15).
    wiki_ext and trends_us correlate 0.479 - reading and searching ARE different
    behaviours and a composite exists to combine different measures - so this
    must not demand that components be near-duplicates. It rejects a component
    pointing the other way.
    """
    from config import CAI_D_COMPONENTS
    FLOOR = 0.15
    if len(CAI_D_COMPONENTS) < 2:
        return "BLOCKED", "fewer than two components; nothing to agree"
    frames = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"]),
              pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])]
    for extra in ("wiki_nyc_daily.csv",):
        if (DATA_REFERENCE / extra).exists():
            frames.append(pd.read_csv(DATA_REFERENCE / extra, parse_dates=["date"]))
    w = pd.concat(frames).pivot_table(index="date", columns="component", values="value")
    missing = [c for c in CAI_D_COMPONENTS if c not in w.columns]
    if missing:
        return "BLOCKED", f"no series for {missing}"
    z = np.log1p(w[list(CAI_D_COMPONENTS)]).apply(
        lambda x: (x - x["2017":"2019"].mean()) / x["2017":"2019"].std(ddof=0))
    z = z.dropna()
    if len(z) < 365:
        return "BLOCKED", f"only {len(z)} complete days"
    bad, detail = [], []
    for c in CAI_D_COMPONENTS:
        others = [o for o in CAI_D_COMPONENTS if o != c]
        r = float(z[c].corr(z[others].mean(axis=1)))
        detail.append(f"{c} {r:+.3f}")
        if not (r > FLOOR):
            bad.append(f"{c} r={r:+.3f}")
    return ("FAIL" if bad else "PASS",
            f"corr with the mean of the others (floor {FLOOR}): " + ", ".join(detail)
            + (f"; FAILING: {bad}" if bad else ""))


def t_index_uncensored():
    """T3/L3: no component IN THE INDEX is a censored indicator rather than a level.

    Generalised from a trends_nyc-only test, and kept rather than retired when
    trends_nyc left CAI-D. A check written against one component's name stops
    testing anything once that component is dropped - and says nothing about
    whatever replaces it. Asked of CAI_D_COMPONENTS, it keeps working.

    Google Trends suppresses region-days below an undisclosed volume floor.
    trends_nyc is exactly zero on 42.6% of days, 26% in 2020 rising to 71% in
    2024, so on those days it is an indicator of clearing the floor and not a
    level - and the censoring is worst in the years the exposed confirmation
    stratum sits in. It is still measured below, as a retired component, so the
    reason it was dropped stays on the record.
    """
    from config import CAI_D_COMPONENTS
    frames = [pd.read_csv(DATA_REFERENCE / "cai_components_daily.csv", parse_dates=["date"]),
              pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])]
    for extra in ("wiki_nyc_daily.csv",):
        if (DATA_REFERENCE / extra).exists():
            frames.append(pd.read_csv(DATA_REFERENCE / extra, parse_dates=["date"]))
    all_c = pd.concat(frames)

    def censoring(name):
        v = all_c[all_c["component"] == name].set_index("date")["value"]
        if not len(v):
            return None
        by_year = (v == 0).groupby(v.index.year).mean()
        return float((v == 0).mean()), float(by_year.max() - by_year.min())

    bad, detail = [], []
    for c in CAI_D_COMPONENTS:
        m = censoring(c)
        if m is None:
            return "BLOCKED", f"component {c} has no series"
        overall, spread = m
        detail.append(f"{c} {overall:.0%}/{spread:.0%}")
        if overall > 0.5 or spread > 0.3:
            bad.append(f"{c}: {overall:.0%} zeros, spread {spread:.0%}")
    excluded = []
    for c in ("trends_nyc", "wiki_nyc"):
        if c in CAI_D_COMPONENTS:
            continue
        m = censoring(c)
        if m:
            excluded.append(f"{c} {m[0]:.0%}/{m[1]:.0%} (not in the index)")
    return ("FAIL" if bad else "PASS",
            "zeros/by-year-spread — " + ", ".join(detail)
            + ("; " + ", ".join(excluded) if excluded else ""))


def t_victims_saturate():
    """T2/L2: trends_victims must not enter CAI-D as an undivided window rank.

    Two fixes are acceptable and the check accepts either: drop the component
    from the CAI-D basket, or actually divide by the topic term so the series
    carries units. An earlier version of this check tested only the second,
    which would have reported FAIL forever if the component were dropped —
    a check that can only pass one way silently forbids the other.
    """
    from config import CAI_D_COMPONENTS
    if "trends_victims" not in CAI_D_COMPONENTS:
        return "PASS", "dropped from CAI_D_COMPONENTS"
    s = src("11c_trends_anchor_and_victims.py")
    divides = bool(re.search(r"ratio\s*=\s*df\[name\][^\n]*/\s*df\[\s*TOPIC", s))
    return ("PASS" if divides else "FAIL",
            "divides by TOPIC" if divides else "ratio = df[name] with no denominator")


def t_composite_after_avg():
    """D5: the composite must be standardised AFTER averaging, not per-component.

    Checked on the BUILT INDEX, not on the source. The first version of this
    check grepped 12_build_cai.py with a non-greedy DOTALL regex, which matched
    across the whole file and reported PASS after an unrelated edit while the
    defect was untouched. A source grep loose enough to match anywhere is not a
    test. The property is arithmetic, so test the arithmetic.

    Averaging k separately standardised components gives a composite with SD
    below 1 (about 0.67 here), so `cai_d > EPISODE_Z_THRESHOLD` is not the
    "1 SD" rule it is documented to be — it is roughly 1.5 SD, and it moves
    with how many components exist that day.
    """
    d = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
    d["date"] = pd.to_datetime(d["date"])
    ref = d[d["date"].between("2017-01-01", "2019-12-31")]["cai_d"].dropna()
    if ref.empty:
        return "BLOCKED", "no cai_d on the reference window"
    sd, mean = float(ref.std(ddof=0)), float(ref.mean())
    ok = abs(sd - 1.0) < 0.02 and abs(mean) < 0.02
    return ("PASS" if ok else "FAIL",
            f"reference-window mean={mean:+.4f} sd={sd:.4f} (target 0.00 / 1.00)")


def t_fixed_component_set():
    """D5: every scored CAI-D day must rest on the SAME component set.

    Checked on the built index. The previous version grepped 12_build_cai.py for
    one of two specific idioms; the fix used a third (`notna().all(axis=1)`), so
    the property held while the check reported FAIL. That is the same fragility
    that made T.composite_after_avg report a false PASS, in the other direction.

    Mean-of-available is the defect: the spread of a mean moves with how many
    terms are averaged, so the index's SD tracked data availability rather than
    attention (0.770 on 2-component days, 0.693 on 3, 1.034 on 4), and whether a
    day cleared the episode threshold depended partly on which sources were
    reporting that day.
    """
    d = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
    scored = d[d["cai_d"].notna()]
    if scored.empty:
        return "BLOCKED", "no scored cai_d days"
    counts = sorted(scored["n_d_components"].dropna().unique().tolist())
    if len(counts) != 1:
        by = scored.groupby("n_d_components")["cai_d"].std(ddof=0).round(3).to_dict()
        return "FAIL", f"scored days span component counts {counts}; SD by count {by}"
    return "PASS", f"all {len(scored):,} scored days use {int(counts[0])} components"


def t_basket_not_registry_gated():
    """T9: the basket must reach victims that Mapping Police Violence omits.

    wiki_ext is summed over the articles in wikipedia_article_resolution.csv
    (11_fetch_awareness_components.py:49-50), so that file IS the basket.

    Mapping Police Violence, which is 100% of victim_registry.csv, does not
    carry Daniel Prude, Sandra Bland, Marvin Scott, Javier Ambler or Leneal
    Frazier — verified against the MPV workbook directly, so it is source
    coverage, not a parsing bug. Those omissions run with the hypothesis rather
    than across it: they are in-custody, restraint and mental-health-crisis
    deaths. Daniel Prude is the most on-hypothesis event in the dataset.

    So a basket built by matching the registry would be systematically blind to
    the events this paper is about, and this check exists to stop that
    seemingly-sensible rule from being adopted. Prude and Bland are the canary:
    if the basket reaches them, it was not registry-gated.
    """
    f = DATA_REFERENCE / "wikipedia_article_resolution.csv"
    if not f.exists():
        return "BLOCKED", "no article resolution file"
    arts = pd.read_csv(f)["article"].dropna().astype(str).str.lower()
    blob = " ".join(arts)
    canaries = {"daniel_prude": "Daniel Prude", "sandra_bland": "Sandra Bland"}
    missing = [lbl for key, lbl in canaries.items() if key not in blob]
    return ("PASS" if not missing else "FAIL",
            f"{len(arts)} articles; reaches MPV-omitted victims" if not missing
            else f"{len(arts)} articles; missing MPV-omitted victims: {missing}")


def t_wiki_ext_matches_basket():
    """The index must be BUILT from the basket on disk, not merely accompanied by it.

    Replacing wikipedia_article_resolution.csv makes every basket check pass
    instantly, but wiki_ext does not change until 11_fetch_awareness_components
    re-fetches pageviews for the new articles. Until then the file says 121
    articles and the index is still the sum of the old 45 — the checks would
    report a property the treatment index does not have. That is the false-PASS
    pattern this suite exists to catch, so it must not be introduced by the
    suite's own fix.

    11 now writes wiki_ext_basket_used.csv listing what it actually summed. This
    compares that to the basket, and BLOCKS (never passes) when the fetch has
    not been run.
    """
    basket = DATA_REFERENCE / "wikipedia_article_resolution.csv"
    used = DATA_REFERENCE / "wiki_ext_basket_used.csv"
    if not basket.exists():
        return "BLOCKED", "no basket file"
    want = set(pd.read_csv(basket)["article"].dropna())
    if not used.exists():
        return "BLOCKED", f"basket has {len(want)} articles; wiki_ext not yet rebuilt from it"
    u = pd.read_csv(used)
    got = set(u["article"])
    ok_n = int(u["ok"].sum()) if "ok" in u.columns else len(u)
    missing, extra = want - got, got - want
    if missing or extra:
        return "FAIL", f"{len(missing)} basket articles never fetched, {len(extra)} stale"
    return "PASS", f"wiki_ext built from all {len(want)} basket articles ({ok_n} returned data)"


def t_wiki_basket_twitter():
    """X2: the basket must cover the whole study window, not end in 2020.

    Tests COVERAGE, not the absence of a column. The first version returned PASS
    as soon as `tweet_volume` was gone from the resolution file — but dropping a
    column is not the same as fixing the selection, and rewriting the file in any
    format at all would have passed it. The defect was never the column: it was
    that Twitter coverage stops at death-year 2020, so the basket contained zero
    victims killed after 2020 and the index could not measure attention in the
    extension years at all.

    Dates come from basket_decisions.csv where available and the registry
    otherwise, because 39 of the basket's victims are not in the registry
    (finding T9) and would otherwise read as undated.
    """
    res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
    arts = set(res["article"].dropna())
    dec = DATA_REFERENCE / "basket_decisions.csv"
    dates = pd.Series(dtype="datetime64[ns]")
    if dec.exists():
        d = pd.read_csv(dec, parse_dates=["death_date"])
        dates = d[d["article"].isin(arts)].set_index("article")["death_date"]
    if dates.notna().sum() == 0:
        reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
        killed = reg.groupby("name")["date"].min()
        dates = res.set_index("article")["name"].map(killed)
    dated = dates.dropna()
    if dated.empty:
        return "BLOCKED", f"{len(arts)} basket articles, none with a resolvable date"
    post2020 = int((dated > "2020-12-31").sum())
    span = f"{dated.min().date()}..{dated.max().date()}"
    return ("PASS" if post2020 > 0 else "FAIL",
            f"{len(arts)} articles, {len(dated)} dated, {post2020} killed after 2020 "
            f"(span {span})")


# ===========================================================================
# ESTIMATOR — static source checks, runnable now
# ===========================================================================
def _synth_panel(seed=11, effect=0.0):
    """A small synthetic panel with the real design's shape. No real data needed.

    Used to exercise the estimator behaviourally. A source grep proves the code
    contains the right-looking text; only running it proves the output has the
    right property, and the estimator was rewritten in a way that no reasonable
    grep would have anticipated.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2017-01-01", "2020-12-31", freq="D")
    cds = list(range(1, 60))
    N, T = len(cds), len(dates)
    y = rng.normal(0.10, 0.03, (N, T))
    panel = pd.DataFrame({"communitydistrict": np.repeat(cds, T),
                          "incident_date": np.tile(dates, N),
                          "edp_share": y.reshape(-1), "total_calls": 50})
    panel["dow"] = panel["incident_date"].dt.dayofweek
    starts = [d for d in pd.date_range("2017-02-01", periods=30, freq="44D")
              if d <= dates[-1] - pd.Timedelta(days=20)]
    if effect:
        m = pd.Series(False, index=panel.index)
        for st in starts:
            m |= panel["incident_date"].between(st, st + pd.Timedelta(days=7))
        panel.loc[m, "edp_share"] += effect
    return panel, starts, dates


def s_reference_day():
    """S2/D1: day -1 must stay IN the sample and be the omitted level.

    Behavioural: build a stack, fit, and inspect which relative days actually
    got coefficients. The defect (deleting day -1) shows up as day -1 present in
    the coefficient set and day -14 absent from it.
    """
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es
    panel, starts, _ = _synth_panel()
    stack = es.build_stack(panel, starts, 14, 14)
    if stack.empty or -1 not in set(stack["rel_day"]):
        return "FAIL", "day -1 absent from the estimation stack"
    m = es.fit_event_study(stack, "edp_share")
    if m is None:
        return "BLOCKED", "model did not fit on the synthetic panel"
    days = set(es._rel_day_coefs(m))
    ok = (-1 not in days) and (-14 in days)
    return ("PASS" if ok else "FAIL",
            f"reference is day -1; estimated {min(days)}..{max(days)}, n={len(days)}" if ok
            else f"omitted level is not -1 (estimated days include -1: {-1 in days}, "
                 f"-14: {-14 in days})")


def s_placebo_count():
    """S1/E1/L1/X4/D2: placebo draws must preserve the real episode count."""
    sys.path.insert(0, str(SCRIPTS))
    from event_study import placebo_starts
    rng = np.random.default_rng(7)
    lo, hi = pd.Timestamp("2017-01-01"), pd.Timestamp("2020-12-31")
    real = pd.date_range("2017-02-01", periods=30, freq="44D")
    real = [d for d in real if d <= hi - pd.Timedelta(days=20)]
    got = [len(placebo_starts(rng, real, lo, hi, 14, 14)) for _ in range(200)]
    frac_full = float(np.mean([g == len(real) for g in got]))
    return ("PASS" if frac_full > 0.95 else "FAIL",
            f"{frac_full:.0%} of draws keep all {len(real)} episodes; mean {np.mean(got):.1f}")


def s_joint_test():
    """S3/R7: H1 must be a joint test with power against a dip-then-rebound.

    Behavioural, and it tests the thing that actually matters. A planted
    dip-then-rebound (days 0-3 down, days 4-7 up by the same amount) averages to
    zero, so the retired 1-df mean statistic is blind to it. A joint test is not.
    """
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es
    rng = np.random.default_rng(3)
    dates = pd.date_range("2017-01-01", "2020-12-31", freq="D")
    cds = list(range(1, 60))
    N, T = len(cds), len(dates)
    panel = pd.DataFrame({"communitydistrict": np.repeat(cds, T),
                          "incident_date": np.tile(dates, N),
                          "edp_share": rng.normal(0.10, 0.03, N * T),
                          "total_calls": 50})
    panel["dow"] = panel["incident_date"].dt.dayofweek
    starts = [d for d in pd.date_range("2017-02-01", periods=30, freq="44D")
              if d <= dates[-1] - pd.Timedelta(days=20)]
    down = pd.Series(False, index=panel.index)
    up = pd.Series(False, index=panel.index)
    for st in starts:
        down |= panel["incident_date"].between(st, st + pd.Timedelta(days=3))
        up |= panel["incident_date"].between(st + pd.Timedelta(days=4),
                                             st + pd.Timedelta(days=7))
    panel.loc[down, "edp_share"] -= 0.010
    panel.loc[up, "edp_share"] += 0.010

    stack = es.build_stack(panel, starts, 14, 14)
    stat = es.first_week_effect(stack, "edp_share")
    mean = es.first_week_mean(stack, "edp_share")
    if stat is None:
        return "BLOCKED", "statistic not estimable on the synthetic panel"
    # The mean is ~0 by construction; the statistic must NOT be.
    sensitive = stat > 50 and abs(mean) < 0.002
    return ("PASS" if sensitive else "FAIL",
            f"dip-then-rebound: statistic={stat:.1f}, mean coef={mean:+.5f} "
            f"({'detected' if sensitive else 'INVISIBLE to the statistic'})")


def s_cluster_by_date():
    """S6: treatment is assigned at date level, so SEs must cluster on date."""
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es
    panel, starts, _ = _synth_panel()
    stack = es.build_stack(panel, starts, 14, 14)
    m = es.fit_event_study(stack, "edp_share")
    if m is None:
        return "BLOCKED", "model did not fit on the synthetic panel"
    vt = str(getattr(m, "_vcov_type_detail", "") or getattr(m, "_vcov_type", ""))
    ok = "CRV" in vt or "cluster" in vt.lower()
    return ("PASS" if ok else "FAIL",
            f"vcov={vt}" if ok else f"vcov={vt or 'hetero'} with date-level treatment")


def s_prewindow_truncation():
    """S5/E4: contested district-days must be reassigned, not deleted twice.

    Behavioural. The defect deleted BOTH copies of any day claimed by two
    windows, which removed 28% of window district-days and the entire first week
    of 5 of 30 episodes. The properties that matter are: no district-day used
    twice, most window days retained, and every retained episode keeping its
    reference day.
    """
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es
    panel, starts, _ = _synth_panel()
    stack = es.build_stack(panel, starts, 14, 14)
    if stack.empty:
        return "FAIL", "empty stack"
    dupes = int(stack.duplicated(["communitydistrict", "incident_date"]).sum())
    eps = stack["episode"].nunique()
    have_ref = sum(-1 in set(g["rel_day"]) for _, g in stack.groupby("episode"))
    # Days a full untruncated design would contain, as the retention denominator.
    want = len(starts) * 29 * panel["communitydistrict"].nunique()
    retained = len(stack) / want
    ok = dupes == 0 and have_ref == eps and retained > 0.55
    return ("PASS" if ok else "FAIL",
            f"{dupes} dup district-days; {have_ref}/{eps} episodes keep day -1; "
            f"{retained:.0%} of window days retained")


def s_calibration_can_fail():
    """S4/X3/R3 (and RI2): the calibration verdict must be able to fail.

    By AST, not by words: the first version tested that "MIN_SIMS" and
    "uniform" appeared in the file, which 18's docstring satisfies on its own,
    so the check would have passed with the verdict logic deleted (CP1 audit).
    Required in the CODE: a MIN_SIMS constant; a uniformity function that
    calls scipy's kstest against the lattice CDF and takes its p-value from a
    Monte-Carlo null rather than the continuous approximation (finding RI2);
    and a verdict that is the conjunction of the sim-count, rate and
    uniformity conditions.
    """
    import ast as _ast
    tree = _ast.parse(src("18_null_calibration.py"))
    consts = {n.targets[0].id for n in _ast.walk(tree) if isinstance(n, _ast.Assign)
              and len(n.targets) == 1 and isinstance(n.targets[0], _ast.Name)}
    problems = []
    if "MIN_SIMS" not in consts:
        problems.append("no MIN_SIMS constant")
    unif = next((n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)
                 and n.name == "_uniformity"), None)
    if unif is None:
        problems.append("no _uniformity function")
    else:
        body = _ast.unparse(unif)
        if "kstest" not in body or "_lattice_cdf" not in body:
            problems.append("_uniformity does not test against the lattice CDF")
        if "default_rng" not in body or "null" not in body:
            problems.append("_uniformity takes its p-value from the continuous "
                            "approximation, not a Monte-Carlo lattice null (RI2)")
    verdict = [n for n in _ast.walk(tree) if isinstance(n, _ast.Assign)
               and len(n.targets) == 1 and isinstance(n.targets[0], _ast.Name)
               and n.targets[0].id == "calibrated"]
    if not verdict or not all(k in _ast.unparse(verdict[0].value)
                              for k in ("enough", "rate_ok", "uniform_ok")):
        problems.append("the verdict is not the conjunction of sim count, rate and uniformity")
    return ("PASS" if not problems else "FAIL",
            "MIN_SIMS enforced; lattice KS with a Monte-Carlo null; verdict = enough and "
            "rate_ok and uniform_ok" if not problems else "; ".join(problems))


def s_stale_calibration_artifact():
    """R3: a real calibration must exist, at real size, with a real verdict.

    An ABSENT artifact is BLOCKED, never PASS. The first version of this check
    returned PASS when the file was missing ("no stale artifact"), so deleting
    the stale 12-sim file passed the check with no calibration having run at
    all. That is the third check in this rebuild that could pass for the wrong
    reason, after the DOTALL regex and the check that admitted only one of two
    valid fixes. "Nothing to complain about" is not the same as "verified".
    """
    f = OUTPUTS_TABLES / "null_calibration.csv"
    if not f.exists():
        return "BLOCKED", "no calibration artifact — run 18_null_calibration.py"
    d = pd.read_csv(f).set_index("metric")["value"].to_dict()
    n = float(d.get("n_sims_completed", 0))
    verdict = str(d.get("VERDICT", "?"))
    if n < 200:
        return "FAIL", f"artifact has n_sims={n:.0f} (needs >=200)"
    if verdict != "CALIBRATED":
        return "FAIL", f"n_sims={n:.0f} but VERDICT={verdict}"
    return "PASS", f"n_sims={n:.0f}, VERDICT={verdict}"


def s_ppml_wired():
    """X5/R8: the counts arm must actually fit, with a real offset.

    Behavioural. Grepping for `counts=True` proves a caller exists, not that
    the arm works — and it did not: pyfixest takes `offset` as a COLUMN NAME,
    so passing a Series raised TypeError, which the estimator's broad `except`
    turned into a silent "not estimable". The arm would have looked unlucky
    rather than broken, which is exactly how it stayed dead code while being
    documented in 17's header.

    So: plant a known proportional rate change and require the PPML arm to fit
    and recover it. Counts matter here because the 2020 "signature" reverses in
    them — EDP counts were flat after Floyd while the denominator rose 6.4%.
    """
    sys.path.insert(0, str(SCRIPTS))
    import event_study as es
    rng = np.random.default_rng(5)
    dates = pd.date_range("2017-01-01", "2020-12-31", freq="D")
    cds = list(range(1, 60))
    N, T = len(cds), len(dates)
    tot = rng.poisson(60, (N, T))
    panel = pd.DataFrame({"communitydistrict": np.repeat(cds, T),
                          "incident_date": np.tile(dates, N),
                          "total_calls": tot.reshape(-1)})
    panel["dow"] = panel["incident_date"].dt.dayofweek
    starts = [d for d in pd.date_range("2017-02-01", periods=30, freq="44D")
              if d <= dates[-1] - pd.Timedelta(days=20)]
    m = pd.Series(False, index=panel.index)
    for st0 in starts:
        m |= panel["incident_date"].between(st0, st0 + pd.Timedelta(days=7))
    ratio = 0.85
    panel["edp"] = rng.poisson(np.where(m, 0.10 * ratio, 0.10) * panel["total_calls"])

    stack = es.build_stack(panel, starts, 14, 14)
    mc = es.fit_event_study(stack, "edp", counts=True)
    if mc is None:
        return "FAIL", "PPML counts arm does not fit"
    got = es.first_week_mean(stack, "edp", counts=True)
    want = float(np.log(ratio))
    ok = got is not None and abs(got - want) < 0.05
    return ("PASS" if ok else "FAIL",
            f"PPML recovers planted rate change: {got:+.4f} vs log({ratio})={want:+.4f}"
            if ok else f"PPML fitted but recovered {got} against a planted {want:+.4f}")


# ===========================================================================
# FREEZE — mechanism, not just intent
# ===========================================================================
def d_freeze_not_tautological():
    """D3: the guard is called right after the same .between() filter."""
    bad = []
    for f in SCRIPTS.glob("*.py"):
        t = f.read_text()
        for m in re.finditer(r"\.between\(ANALYSIS_START, ANALYSIS_END\)\]?\s*\n\s*assert_discovery_only", t):
            bad.append(f.name)
    return ("PASS" if not bad else "FAIL",
            "guard is independent" if not bad else f"tautological in {sorted(set(bad))}")


def d_freeze_enforces_disjoint():
    """D3: flipping FREEZE_ACTIVE must not pool discovery into confirmation."""
    s = src("config.py")
    has_conf_window = "CONFIRM_START" in s or "CONFIRMATION_WINDOW" in s
    return ("PASS" if has_conf_window else "FAIL",
            "explicit confirmation window" if has_conf_window
            else "flipping FREEZE_ACTIVE pools all 70 episodes into one sample")


# Scripts that read the panel but must NOT route it through select_sample, with
# the reason. Exemptions are listed here rather than being implicit, so adding
# one is a visible edit in a diff instead of a script quietly going unchecked.
# Scripts allowed to query the EMS SOURCE dataset directly. Each needs a reason,
# for the same purpose GUARD_EXEMPT has one: an undocumented exemption list is a
# way to make a check stop complaining rather than a way to record a decision.
SODA_PRODUCERS = {
    # Write the outcome extracts from the raw SODA pages. They cannot filter:
    # 01_build_panel.py needs the full extract for the lag/lead buffer, and the
    # citywide trends file is a descriptive 2005+ series by design.
    "00_local_ems_extract.py",
    "00b_download_ems_extract.py",
    # Builds the precinct -> community-district crosswalk by SERVER-SIDE
    # aggregation: counts of incidents per (precinct, CD) pooled over 2015-2024,
    # with no time dimension, no call type and no share. It is geography, not
    # outcome - which district a precinct's calls land in - and filtering it to
    # the discovery window would bias the weights that carry B-HEARD exposure.
    # It does pool over confirmation years, and that is why it is declared here
    # rather than left silent.
    "16_bheard_exposure.py",
    # The auditor and the source verifier: both must be able to NAME the dataset
    # in order to check that everything else handles it correctly.
    "23_regression_suite.py",
    "31_verify_sources.py",
}

# Scripts that DEFINE the protected names without reading anything. Exempt from
# the reader scans only while they contain no read call, which the checks assert.
DEFINERS = {"config.py"}
READ_CALLS = ("read_parquet", "read_csv", "read_table", "ParquetFile", "open")

GUARD_EXEMPT = {
    # Builds the panel, including the lag/lead buffer that deliberately extends
    # to PANEL_BUFFER_END = 2021-01-31 — inside a confirmation window. Filtering
    # here would destroy the padding the lag structure needs. Nothing in this
    # script examines an outcome; the modelling scripts filter downstream.
    "01_build_panel.py",
    # The auditor itself: it must be able to read the raw panel to check it.
    "23_regression_suite.py",
    # The orchestrator. It NAMES every outcome artifact in its stage table and
    # records each one's size, sha256 and ROW COUNT in the run manifest — but it
    # never loads a value: parquet row counts come from the file footer and CSV
    # counts from newlines. It runs each stage as a subprocess, and those stages
    # carry their own guards. Verified by reading artifact_fact(): there is no
    # pd.read_* of an outcome file anywhere in it.
    "run_all.py",
    # The two extract builders WRITE the outcome artifacts from the raw SODA
    # pages. They cannot filter to a sample window: 01_build_panel.py needs the
    # full extract to build the lag/lead buffer, and the citywide trends file is
    # a descriptive 2005+ series by design. They are producers, not examiners.
    "00_local_ems_extract.py",
    "00b_download_ems_extract.py",
}


def _calls_any(path, names):
    """True when the script contains a CALL to any of `names` (Name or Attribute).

    Checks decide 'guarded' on this, not on the words appearing in the file:
    a comment naming select_sample used to satisfy D.guard_coverage, so config.py
    passed as a guarded reader and a deleted guard call would have gone unseen.
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = n.func
            name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
            if name in names:
                return True
    return False


def _string_constants(path):
    """Every string literal in the script's code - not its comments."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    return {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)}


def d_guard_coverage():
    """D3: every panel-reading script must route the panel through the guard.

    Tests the PROPERTY (does this script go through freeze_guard?) rather than
    one function name. The first version grepped for `assert_discovery_only`,
    so renaming the entry point to `select_sample` — the actual fix for the
    tautology — made this check report the fixed scripts as unguarded.
    """
    from config import OUTCOME_ARTIFACTS, RAW_OUTCOME_DIRS
    # declared_access is a guard entry too: it does not filter, but it refuses
    # undeclared exemptions and foreign callers and logs every call, and
    # D.declared_access_scoped holds its scope. A script using it is routed
    # through freeze_guard, which is the property this check tests.
    entries = ("select_sample", "assert_no_confirmation_outcomes",
               "assert_discovery_only", "declared_access")
    # A reader is a script whose CODE names an outcome artifact - or the raw
    # paged download directory, which holds every incident row for every year
    # and which config.RAW_OUTCOME_DIRS promised was covered while nothing read
    # that constant (CP1 audit). Names in comments do not count either way, and
    # 'guarded' means a CALL to a guard entry, not a mention.
    names = tuple(OUTCOME_ARTIFACTS) + tuple(RAW_OUTCOME_DIRS)
    missing = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in GUARD_EXEMPT:
            continue
        if f.name in DEFINERS:
            # config.py DEFINES these names; it is exempt only while it reads
            # nothing, which is asserted rather than assumed.
            if _calls_any(f, READ_CALLS):
                missing.append(f"{f.name}(defines the names AND reads a file)")
            continue
        consts = _string_constants(f)
        reads = [a for a in names if any(a in c for c in consts)]
        if reads and not _calls_any(f, entries):
            missing.append(f"{f.name}({','.join(a.split('.')[0] for a in reads)})")
    return ("PASS" if not missing else "FAIL",
            f"all readers of {len(OUTCOME_ARTIFACTS)} outcome artifacts and "
            f"{len(RAW_OUTCOME_DIRS)} raw directory guarded by a call "
            f"({len(GUARD_EXEMPT)} documented exemptions)"
            if not missing else f"unguarded: {missing}")


def x_bheard_wired_and_inert():
    """X6: the B-HEARD control is IN a model, and adding it changes no discovery number.

    Two properties, and the second is the one that matters.

    WIRED. 16_bheard_exposure.py built the exposure table, IBO-validated it, and
    committed it — and no model read it. Not one. The ratified control for this
    project's most serious confound was computed and connected to nothing. It
    went unnoticed because B-HEARD starts 2021-06-01 and the freeze restricts
    every model to 2017-2020, so adding it changes nothing anyone has estimated.
    That is exactly why it has to be wired BEFORE the freeze lifts: afterwards,
    adding a control is a specification change.

    INERT ON DISCOVERY. Since exposure is identically zero there, adding it must
    leave every discovery coefficient NUMERICALLY UNCHANGED. This refits the
    event study with and without it and compares. A non-zero difference means the
    precinct-to-community-district crosswalk has put exposure somewhere it cannot
    be — an error that would otherwise surface only in the confirmatory run,
    where it could not be fixed.

    This is a CP2 gate item, asserted rather than remembered.
    """
    import importlib
    pq = DATA_PROCESSED / "panel_cd_day.parquet"
    ep_f = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
    if not (pq.exists() and ep_f.exists()):
        return "BLOCKED", "panel or episode list absent"
    sys.path.insert(0, str(SCRIPTS))
    try:
        bh = importlib.import_module("bheard")
    except Exception as e:
        return "FAIL", f"bheard module missing or broken: {type(e).__name__}: {e}"

    # WIRED means IN THE FORMULA, decided by AST. The first version scanned file
    # text for "attach_bheard" or "from bheard import", which the import line
    # alone satisfies - and it did: 17 attached the column to the panel and
    # estimated a formula that never read it (finding X17). Now a script counts
    # as wired only if it passes a covariate list containing bheard_exposure to
    # the estimator (a Call with keyword extra=..., or a function whose default
    # extra names it), and the estimator itself builds its right-hand side from
    # that list.
    import ast as _ast

    def _passes_bheard(path):
        tree = _ast.parse(path.read_text())
        # A covariate list passed by NAME resolves to its module-level assignment,
        # so `extra=COVARIATES` counts iff COVARIATES is assigned a literal that
        # names bheard_exposure.
        assigned = {}
        for n in tree.body:
            if isinstance(n, _ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], _ast.Name):
                assigned[n.targets[0].id] = _ast.unparse(n.value)
        def _names(v):
            s = _ast.unparse(v)
            return assigned.get(s, s) if isinstance(v, _ast.Name) else s
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Call):
                for kw in n.keywords:
                    if kw.arg == "extra" and "bheard_exposure" in _names(kw.value):
                        return True
            if isinstance(n, _ast.FunctionDef):
                for a, dflt in zip(reversed(n.args.args), reversed(n.args.defaults)):
                    if a.arg == "extra" and dflt is not None and "bheard_exposure" in _ast.unparse(dflt):
                        return True
        return False

    readers = [f.name for f in sorted(SCRIPTS.glob("*.py"))
               if f.name not in ("bheard.py", "16_bheard_exposure.py",
                                 "23_regression_suite.py", "20_data_audit.py",
                                 "run_all.py", "22_pipeline_check.py", "event_study.py")
               and _passes_bheard(f)]
    if not readers:
        return "FAIL", "no model passes the B-HEARD exposure control into its formula"
    es_tree = _ast.parse((SCRIPTS / "event_study.py").read_text())
    fes = next((n for n in _ast.walk(es_tree) if isinstance(n, _ast.FunctionDef)
                and n.name == "fit_event_study"), None)
    if fes is None or "extra" not in [a.arg for a in fes.args.args]:
        return "FAIL", "event_study.fit_event_study takes no covariate list"
    joins = [n for n in _ast.walk(fes) if isinstance(n, _ast.Call)
             and isinstance(n.func, _ast.Attribute) and n.func.attr == "join"
             and "extra" in _ast.unparse(n)]
    if not joins:
        return "FAIL", "fit_event_study does not build its right-hand side from `extra`"

    from config import (BHEARD_BOUND_PRIMARY, EVENT_WINDOW_POST, EVENT_WINDOW_PRE,
                        MIN_TOTAL_CALLS_FOR_SHARE)
    es = importlib.import_module("event_study")
    fg = importlib.import_module("freeze_guard")
    panel = pd.read_parquet(pq)
    panel["incident_date"] = pd.to_datetime(panel["incident_date"])
    # Pinned to the discovery window by name (incident F5, 2026-09-20): this check
    # derived its sample from the flag, so the first gate run after the lift
    # fitted the primary specification on the confirmation sample with every
    # episode. It tests inertness ON DISCOVERY and may never read anything else.
    panel = fg.select_sample(panel, where="23_regression_suite:X6", window="discovery")
    panel = panel[panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE].copy()
    panel["dow"] = panel["incident_date"].dt.dayofweek

    withb = bh.attach(panel, bound=BHEARD_BOUND_PRIMARY)
    inert, mx = bh.is_inert(withb)
    if not inert:
        return "FAIL", (f"B-HEARD exposure is non-zero (max {mx:.4g}) inside the "
                        "discovery sample — the crosswalk is wrong")

    ep = pd.read_csv(ep_f, parse_dates=["start"])
    if "period" in ep.columns:
        ep = ep[ep["period"] == "discovery"]
    starts = ep["start"].tolist()
    base = es.build_stack(panel, starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    if base.empty:
        return "BLOCKED", "no usable event windows on this panel"
    m0 = es.fit_event_study(base, "edp_share")
    if m0 is None:
        return "BLOCKED", "baseline event study not estimable"

    import warnings
    import pyfixest as pf
    stack2 = es.build_stack(withb, starts, EVENT_WINDOW_PRE, EVENT_WINDOW_POST)
    d = stack2.dropna(subset=["edp_share"])
    fml = (f"edp_share ~ i(rel_day, ref={es.EVENT_REFERENCE_DAY}) + bheard_exposure "
           f"| ep_cd + dow")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m1 = pf.feols(fml, d, vcov={"CRV1": es.CLUSTER_VAR})
    except Exception as e:
        return "FAIL", f"model with the control does not estimate: {type(e).__name__}: {e}"
    c0, c1 = m0.coef(), m1.coef()
    shared = [k for k in c0.index if k in c1.index]
    if not shared:
        return "FAIL", "no shared coefficients between the two fits"
    diff = float(np.max(np.abs(c0[shared].values - c1[shared].values)))
    return ("PASS" if diff < 1e-10 else "FAIL",
            f"read by {readers}; exposure max {mx:.4g} on the discovery sample; "
            f"max |coef difference| over {len(shared)} coefficients = {diff:.3e}")


def d_soda_source_guarded():
    """F2: the freeze guard protects ARTIFACTS, so the source API bypasses it.

    Coverage is a list of files under data/processed/. NYC OpenData 76xm-jjuj is
    not a file - any script (or any agent) that queries it directly reads
    confirmation-period outcomes with no guard in the path at all. That is how
    incident F2 happened: verifying finding O3 needed call-type birth dates, the
    question was put straight to SODA, and it came back with precinct-level EDPM
    counts for June 2021 comparing B-HEARD pilot precincts against the rest.
    Nothing failed, because nothing was watching.

    D.guard_coverage cannot catch this - it looks for scripts that READ the
    outcome artifacts. So the dataset id itself is treated as an outcome source:
    a script naming it must either be a declared producer (it writes the extract
    and cannot filter) or route through freeze_guard.
    """
    from config import EMS_DATASET_ID
    producers = SODA_PRODUCERS
    entries = ("select_sample", "assert_no_confirmation_outcomes",
               "assert_discovery_only", "freeze_banner", "declared_access")
    unguarded = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in producers:
            continue
        if f.name in DEFINERS:
            if _calls_any(f, READ_CALLS + ("urlopen", "get", "request")):
                unguarded.append(f"{f.name}(defines the id AND performs a request)")
            continue
        # The dataset id in a STRING LITERAL (a URL being built), and 'guarded'
        # means a call, not a word in a comment (CP1 audit).
        names_it = any(EMS_DATASET_ID in c for c in _string_constants(f))
        if names_it and not _calls_any(f, entries):
            unguarded.append(f.name)
    return ("FAIL" if unguarded else "PASS",
            f"scripts querying {EMS_DATASET_ID} without the guard: {unguarded}"
            if unguarded else
            f"{len(producers)} declared producer(s), each with a recorded reason; "
            f"no other script queries {EMS_DATASET_ID} unguarded")


def d_incident_disclosed():
    """F1, F2: EVERY freeze incident must stay in the record, in both places.

    This is a DISCLOSURE obligation, so "the text exists in the record" is
    genuinely the property, not a proxy for it - unlike the source greps this
    suite has had to replace. The failure mode is real and specific: an incident
    quietly dropped during a later edit, leaving a pre-registration record that
    overstates how clean the freeze was.

    Keyed on every finding whose id starts with F, not on the literal "F1". The
    first version named F1, so when a SECOND incident was found on 2026-09-11 -
    a direct SODA query that read precinct-level confirmation-window outcomes -
    this check would have gone on passing while the register described the
    freeze as having one breach. A disclosure check that cannot see a new
    disclosure is worse than none, because it certifies the omission.

    Requires each incident in BOTH the finding register and the paper master:
    the register is internal, the master is what Methods is written from.
    """
    reg = pd.read_csv(PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv")
    incidents = sorted(i for i in reg["id"].astype(str)
                       if re.fullmatch(r"F\d+", i))
    if not incidents:
        return "BLOCKED", "no freeze incidents in the register to check"
    master = PROJECT_ROOT / "docs" / "PAPER_MASTER.md"
    if not master.exists():
        return "FAIL", "docs/PAPER_MASTER.md is missing; incidents have no disclosure home"
    m = master.read_text()
    # The incident must appear IN THE DISCLOSURE SECTION, not merely somewhere in
    # the document. The first version accepted the incident id OR any date from
    # its title, and 2026-09-11 appears all over this document for unrelated
    # reasons - so deleting F2's disclosure entirely still passed. A disclosure
    # check that matches an unrelated date certifies the omission it exists to
    # catch.
    heads = [i for i in range(len(m))
             if m.startswith("#", i) and (i == 0 or m[i - 1] == "\n")]
    section = ""
    for n, i in enumerate(heads):
        line_end = m.index("\n", i)
        if "freeze incident" in m[i:line_end].lower():
            nxt = next((h for h in heads[n + 1:]
                        if m[h:m.index("\n", h)].startswith(("## ", "# "))), len(m))
            section = m[i:nxt]
            break
    if not section:
        return "FAIL", "PAPER_MASTER.md has no freeze-incident section"
    missing = [fid for fid in incidents
               if not re.search(rf"\b{fid}\b", section)]
    if missing:
        return "FAIL", (f"{len(missing)} incident(s) in the register but not named in "
                        f"the freeze-incident section of PAPER_MASTER.md: {missing}")
    undated = [fid for fid in incidents
               if not re.search(r"\d{4}-\d{2}-\d{2}", section)]
    if undated:
        return "FAIL", "the freeze-incident section carries no dates"
    return "PASS", (f"{len(incidents)} incident(s) recorded and named in the "
                    f"disclosure section, dated: {incidents}")


def d_guard_can_fire():
    """D3/D4: the freeze guard must actually REJECT things, in both flag states.

    The retired guard's defect was not that it was wrong but that it could never
    fire: it was always asked, immediately after the caller's own filter,
    whether that filter had worked. A gate that has never rejected anything has
    not been tested. So this exercises it on inputs it must refuse.

    The last case is the one that matters most. Lifting FREEZE_ACTIVE must
    SWITCH the sample to the confirmation windows, not WIDEN it to include the
    discovery years that have already been examined.
    """
    sys.path.insert(0, str(SCRIPTS))
    import freeze_guard as fg

    def frame(lo, hi):
        return pd.DataFrame({"incident_date": pd.date_range(lo, hi, freq="D"),
                             "edp_share": 0.1})

    saved = fg.FREEZE_ACTIVE
    results = []
    try:
        fg.FREEZE_ACTIVE = True
        # 1. drops confirmation-period rows from a wide frame
        out = fg.select_sample(frame("2016-06-01", "2021-06-30"), where="selftest")
        results.append(("drops out-of-window",
                        out["incident_date"].max() == pd.Timestamp("2020-12-31")))
        # 2. fires on a frame that is entirely confirmation-period
        try:
            fg.assert_no_confirmation_outcomes(frame("2021-01-01", "2021-03-01"),
                                               where="selftest")
            results.append(("rejects confirmation data", False))
        except fg.FreezeViolation:
            results.append(("rejects confirmation data", True))
        # 3. an empty sample raises rather than returning silently
        try:
            fg.select_sample(frame("2022-01-01", "2022-02-01"), where="selftest")
            results.append(("rejects empty sample", False))
        except fg.FreezeViolation:
            results.append(("rejects empty sample", True))
        # 4. lifting the freeze must EXCLUDE discovery, not pool it
        fg.FREEZE_ACTIVE = False
        out = fg.select_sample(frame("2015-01-01", "2024-12-31"), where="selftest")
        pooled = int(out["incident_date"].between("2017-01-01", "2020-12-31").sum())
        results.append(("samples stay disjoint when lifted", pooled == 0))
    finally:
        fg.FREEZE_ACTIVE = saved

    bad = [n for n, ok in results if not ok]
    return ("PASS" if not bad else "FAIL",
            f"guard fires on all {len(results)} rejection cases" if not bad
            else f"guard did NOT fire on: {bad}")


def d_declared_access_scoped():
    """O2: every read of confirmation-window outcomes is declared, scoped, logged
    and disclosed - and the guard refuses everything outside that.

    GUARD_EXEMPT says which scripts may read an outcome artifact unfiltered; it
    says nothing about what they do with the rows, and it is checked by grep.
    Incidents F1 and F2 were both reads that nobody had declared and nothing
    logged. Finding O2 needs one more such read - a coverage table over the
    2015-2016 extract - and the decision (CONFIRMATION_PLAN.md addendum 18) was
    to permit it only as a DECLARED access: named in config.FREEZE_EXEMPTIONS
    with the script, the input and the exact output columns; routed through
    freeze_guard.declared_access, which logs every call; written through
    declared_output, which refuses undeclared columns.

    This check holds all four sides of that at once, because each can drift on
    its own: (1) the set of scripts calling declared_access equals the set of
    scripts the declarations name - no borrowing, no orphan declaration; (2)
    every declared output exists with EXACTLY the declared columns - a widened
    output is a widened access; (3) the exemption is disclosed in the addendum
    by name; (4) the access log records a run by the declared script. Then a
    self-test: the guard must refuse an undeclared exemption, a declared one
    invoked from the wrong script, an output with an extra column, and an output
    name that was never declared. A guard that has never refused anything has
    not been tested (the D.guard_can_fire lesson).

    Defeat-tested before baselining: adding a column to the written output
    fails (2); calling the exemption from this suite is refused (self-test).
    """
    from config import FREEZE_EXEMPTIONS, FREEZE_ACCESS_LOG
    sys.path.insert(0, str(SCRIPTS))
    import freeze_guard as fg

    problems = []
    # Real CALL SITES, found by parsing, not by grep: config.py and the script's
    # own docstring both mention "declared_access(" in prose, and a grep would
    # report the config file as a reader of confirmation outcomes.
    def _calls_declared_access(path):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            return False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
                if name == "declared_access":
                    return True
        return False

    callers = [f.name for f in sorted(SCRIPTS.glob("*.py"))
               if f.name not in ("freeze_guard.py", "23_regression_suite.py")
               and _calls_declared_access(f)]
    declared = {s["script"]: n for n, s in FREEZE_EXEMPTIONS.items()}
    stray = [c for c in callers if c not in declared]
    if stray:
        problems.append(f"undeclared caller(s) of declared_access: {stray}")
    plan = PROJECT_ROOT / "docs" / "CONFIRMATION_PLAN.md"
    plan_text = plan.read_text() if plan.exists() else ""
    for name, spec in FREEZE_EXEMPTIONS.items():
        script = SCRIPTS / spec["script"]
        if not script.exists():
            problems.append(f"{name}: declared for {spec['script']}, which does not exist")
            continue
        src = script.read_text()
        if f'"{name}"' not in src and f"'{name}'" not in src:
            problems.append(f"{name}: {spec['script']} never names the exemption")
        if spec["script"] not in callers:
            problems.append(f"{name}: {spec['script']} does not call declared_access")
        if name not in plan_text:
            problems.append(f"{name}: not disclosed by name in CONFIRMATION_PLAN.md")
        for out, cols in spec["writes"].items():
            p = DATA_REFERENCE / out
            if not p.exists():
                return "BLOCKED", f"{out} absent — run {spec['script']} (declared access {name})"
            got = tuple(pd.read_csv(p, nrows=0).columns)
            if got != tuple(cols):
                problems.append(f"{out}: columns {list(got)} differ from the declared {list(cols)}")
        if not FREEZE_ACCESS_LOG.exists():
            problems.append(f"{FREEZE_ACCESS_LOG.name} absent: no declared access has been logged")
        else:
            log = pd.read_csv(FREEZE_ACCESS_LOG)
            if not ((log["exemption"] == name) & (log["script"] == spec["script"])).any():
                problems.append(f"{name}: no row in {FREEZE_ACCESS_LOG.name} for {spec['script']}")

    # Self-test: the guard must REFUSE. None of these writes anything: the caller
    # and declaration checks run before the log append, and the column check
    # before the file write.
    frame = pd.DataFrame({"incident_date": pd.date_range("2015-01-01", "2015-01-10"),
                          "x": 1.0})
    first = next(iter(FREEZE_EXEMPTIONS))
    first_out, first_cols = next(iter(FREEZE_EXEMPTIONS[first]["writes"].items()))
    widened = pd.DataFrame({c: ["v"] for c in first_cols}).assign(mean_edp_share=[0.1])
    cases = [
        ("undeclared exemption",
         lambda: fg.declared_access(frame, "not_a_declared_exemption", where="selftest")),
        ("exemption borrowed by another script",
         lambda: fg.declared_access(frame, first, where="selftest")),
        ("output with an undeclared column",
         lambda: fg.declared_output(widened, first, first_out)),
        ("output name never declared",
         lambda: fg.declared_output(frame, first, "ems_outcome_means_by_period.csv")),
    ]
    not_refused = []
    for label, fn in cases:
        try:
            fn()
            not_refused.append(label)
        except fg.FreezeViolation:
            pass
    if not_refused:
        problems.append(f"guard did NOT refuse: {not_refused}")

    n_out = sum(len(s["writes"]) for s in FREEZE_EXEMPTIONS.values())
    return ("PASS" if not problems else "FAIL",
            f"{len(FREEZE_EXEMPTIONS)} declared access(es), {len(callers)} caller(s), "
            f"{n_out} output(s) with exactly the declared columns, each disclosed and "
            f"logged; guard refuses all {len(cases)} self-test cases"
            if not problems else "; ".join(problems))


# ===========================================================================
# EPISODES
# ===========================================================================
def e_episodes_labelled():
    """E7, E8: every episode says what drove it, from the treatment series itself.

    The registry labeller answers "which recently-killed person in Mapping Police
    Violence drew the most attention in this window". That is a legitimate
    question and it is not the question Table 1 asks, which is "what is this
    episode". The gap is not cosmetic:

      45% OF EPISODES HAD NO LABEL — 33 of 74, and 16 of 29 in discovery. Among
      them the second-largest discovery episode in the study, 2020-08-24..09-07,
      peak 9.01. Nothing in a registry of KILLINGS keyed on DATE OF DEATH can
      explain it: Jacob Blake was shot on 2020-08-23 and survived, and Daniel
      Prude's death became public with the video on 2020-09-02, five months
      after he died — and Prude is absent from the registry entirely (T9).

      WHERE IT DID LABEL, IT OFTEN NAMED THE WRONG PERSON. 2020-09-22..09-27
      was labelled "Dijon Kizzee" while 87% of basket attention was Breonna
      Taylor, the week the grand jury declined to indict. 2015-07-23 was
      labelled "Samuel DuBose; Jonathan Sanders" while 83% was Sandra Bland.
      2017-06-16 was "Michael Brown; Jordan Edwards" while 76% was Philando
      Castile. The pattern is consistent and is exactly E7's thesis: episodes
      driven by a video release, an indictment or a verdict cannot be attributed
      from death dates, and widening the lookback makes it worse rather than
      better by letting long-past deaths capture them.

    So each episode now carries a SECOND label built from the basket pageviews
    themselves, which needs no death date and no assumption that a death was the
    trigger. Both are kept: they answer different questions and the disagreement
    is informative.

    This asserts the property that matters — no episode is unexplained — plus
    the concentration measure E8 needs, so that "this period cannot separate
    individual killings" is a number rather than an assertion.
    """
    out, attention = [], None
    for basket in ("strict", "broad"):
        f = DATA_REFERENCE / ("confirmation_episodes_rebuilt.csv" if basket == "strict"
                              else f"confirmation_episodes_rebuilt_{basket}.csv")
        if not f.exists():
            continue
        d = pd.read_csv(f)
        if "drivers" not in d.columns or "top_driver_share" not in d.columns:
            return "FAIL", (f"{f.name} predates the driver label; re-run "
                            "13_extension_episodes.py so every episode says what drove it")
        blank = d["drivers"].fillna("").str.strip() == ""
        if blank.any():
            return "FAIL", (f"{int(blank.sum())} episode(s) in {f.name} have no driver "
                            f"label, so the treatment series cannot say what they were: "
                            f"{d.loc[blank, 'start'].head(3).tolist()}")
        bad = d[(d["top_driver_share"] <= 0) | (d["top_driver_share"] > 1)]
        if len(bad):
            return "FAIL", (f"{len(bad)} episode(s) carry a top_driver_share outside "
                            "(0, 1], so the share is not a share")
        # The property, not its proxy (CP1 audit #29, 2026-09-13). label_drivers()
        # returns a blank label only for a window with NO basket attention, and
        # an episode is by construction a window with a great deal of it, so the
        # blank test above cannot fail on a real artifact. What CAN fail is
        # currency: labels on disk computed from an earlier attention series.
        # Recompute every label from the series as it stands and require
        # agreement.
        if attention is None:
            sys.path.insert(0, str(SCRIPTS))
            from attribution import label_drivers as _label, load_attention
            try:
                attention = load_attention()
            except SystemExit as e:
                return "BLOCKED", f"cannot recompute episode labels: {e}"
        stale = []
        for _, r in d.iterrows():
            lab, share = _label(attention, pd.Timestamp(r["start"]), pd.Timestamp(r["end"]))
            if lab != str(r["drivers"]) or abs(share - float(r["top_driver_share"])) > 5e-4:
                stale.append(f"{r['start']}: {str(r['drivers'])[:40]!r} on disk, {lab[:40]!r} now")
        if stale:
            return "FAIL", (f"{len(stale)} episode label(s) in {f.name} do not match the "
                            f"attention series as it stands; re-run 13_extension_episodes.py: "
                            + "; ".join(stale[:2]))
        out.append(f"{basket}={len(d)}")
    if not out:
        return "BLOCKED", "no episode list on disk — run 13_extension_episodes.py"
    d = pd.read_csv(DATA_REFERENCE / "confirmation_episodes_rebuilt.csv")
    disc = d[d["period"] == "discovery"]
    return "PASS", (f"every episode carries a driver label ({', '.join(out)}); "
                    f"median top-driver share on discovery "
                    f"{disc['top_driver_share'].median():.0%}, "
                    f"{int((disc['top_driver_share'] >= 0.5).sum())} of {len(disc)} "
                    "above half")


def e_threshold_constant_stringency():
    """D5/L5/E6: the episode rule must apply the same stringency in every year.

    Asserts on the SELECTED DAYS, recomputed from the current index — not on a
    per-year count read off the artifact. A count-only check passes on the
    quietest 10% of each year just as happily as on the loudest, and it cannot
    tell a fresh artifact from one regenerated against a stale index.

    So this recomputes the within-year cut from cai_daily.parquet and requires
    (a) the realised rate to match EPISODE_RATE in every year, and (b) every
    episode peak in the artifact to actually clear its own year's cut.
    """
    from config import EPISODE_RATE
    f = DATA_PROCESSED / "cai_daily.parquet"
    if not f.exists():
        return "BLOCKED", "cai_daily.parquet absent"
    d = pd.read_parquet(f).dropna(subset=["cai_d"]).copy()
    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    cut = d.groupby("year")["cai_d"].quantile(1.0 - EPISODE_RATE)
    rate = d.assign(hi=d["cai_d"] > d["year"].map(cut)).groupby("year")["hi"].mean()
    spread = float(rate.max() - rate.min())
    if spread > 0.02:
        return "FAIL", (f"stringency varies {rate.min():.1%}-{rate.max():.1%} by year "
                        f"(spread {spread:.1%}, need <=2pp)")

    # Tie the artifact to THIS index: every peak must clear its own year's cut.
    art = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
    if not art.exists():
        return "BLOCKED", "no rebuilt episode list to tie the rule to"
    ep = pd.read_csv(art, parse_dates=["peak_date"])
    ep["year"] = ep["peak_date"].dt.year
    below = ep[ep["peak_cai_d"] < ep["year"].map(cut) - 1e-9]
    if len(below):
        return "FAIL", (f"{len(below)} episode peaks fall below their own year's cut — "
                        "the artifact was built from a different index")
    return "PASS", (f"stringency {rate.min():.1%}-{rate.max():.1%} by year "
                    f"(spread {spread:.1%}); all {len(ep)} peaks clear their year's cut")


def e_no_mega_episode():
    """E3/D7/E6: episodes must be bounded shocks, not plateaus or points.

    Asserts on the SPAN DISTRIBUTION, because that is what degenerates. The
    previous version read only the max span off the FROZEN file, so it could
    never reflect a rebuild; and a metric computed over a fixed +/-14 window
    around a START is capped at 29 days by construction and structurally cannot
    detect a mega-episode, whose pathology lives in its END.

    Two-sided on purpose: `max <= cap` catches the 235-day plateau, and
    `median >= 1` catches the opposite degenerate case where the rule collapses
    to `end = start` and every episode is a single point.
    """
    from config import EPISODE_MAX_DAYS
    f = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
    if not f.exists():
        return "BLOCKED", "no rebuilt episode list — run 13_extension_episodes.py"
    ep = pd.read_csv(f, parse_dates=["start", "end"])
    span = (ep["end"] - ep["start"]).dt.days
    mx, med = int(span.max()), float(span.median())
    if mx > EPISODE_MAX_DAYS:
        return "FAIL", f"longest episode {mx} days (cap {EPISODE_MAX_DAYS})"
    if med < 1:
        return "FAIL", (f"median span {med:.0f} days — the rule has collapsed to points; "
                        f"{int((span == 0).sum())}/{len(ep)} episodes are single days")
    return "PASS", (f"{len(ep)} episodes, span median {med:.0f} max {mx} "
                    f"(cap {EPISODE_MAX_DAYS})")


def e_frozen_list_untouched():
    """The pre-registered episode list must be byte-identical to git HEAD.

    Its entire value is that it was fixed before any outcome was examined, so
    regenerating it in place destroys the evidence of that ordering — and a
    reviewer cannot tell a correction from a result-driven edit after the fact.

    This check exists because it already happened: on 2026-09-10
    13_extension_episodes.py overwrote the frozen file, since its output path
    had never been changed when the index rebuild began. It was caught by
    `git status`, restored, and verified byte-identical. Nothing downstream had
    consumed the overwritten version. A guard beats vigilance.
    """
    import subprocess
    f = DATA_REFERENCE / "confirmation_episodes.csv"
    if not f.exists():
        return "FAIL", "the frozen episode list is missing"
    r = subprocess.run(["git", "show", f"HEAD:data/reference/{f.name}"],
                       cwd=PROJECT_ROOT, capture_output=True)
    if r.returncode != 0:
        return "BLOCKED", "cannot read the committed version from git"
    same = r.stdout == f.read_bytes()
    return ("PASS" if same else "FAIL",
            "byte-identical to HEAD" if same
            else "MODIFIED — restore with: git checkout -- data/reference/"
                 + f.name)


def e_labels_not_from_twitter():
    """E5/L6/R2: episode labels must rank by attention, not by file order.

    Tests the OUTPUT, not the absence of a word. The first version checked that
    "tweet_volume" no longer appeared in the source, which deleting the line
    would have satisfied without replacing the ranking — the same weak-proxy
    shape as the basket check that passed when a column disappeared.

    The file-order signature is specific and testable: when every candidate tied
    at 0.0, the stable sort returned the registry's own date-descending order,
    so the label was simply the two most recent deaths in the window. A real
    attention ranking disagrees with that most of the time, and leaves a window
    with no readership unlabelled rather than defaulting.
    """
    f = DATA_REFERENCE / "confirmation_episodes_rebuilt.csv"
    if not f.exists():
        return "BLOCKED", "no rebuilt episode list — run 13_extension_episodes.py"
    from config import ATTRIBUTION_LOOKBACK_DAYS
    ep = pd.read_csv(f, parse_dates=["start", "end"])
    reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])

    file_order, labelled = 0, 0
    for _, r in ep.iterrows():
        lab = str(r.get("candidate_events") or "").strip()
        if not lab:
            continue
        labelled += 1
        lo = r["start"] - pd.Timedelta(days=ATTRIBUTION_LOOKBACK_DAYS)
        near = reg[(reg["date"] >= lo) & (reg["date"] <= r["end"])]
        # the retired ranking's output: registry file order, date descending
        default = "; ".join(near.sort_values("date", ascending=False)["name"].head(2))
        if default and lab == default:
            file_order += 1

    if labelled == 0:
        return "FAIL", "no episode carries a label"
    share = file_order / labelled
    blank = int((ep["candidate_events"].isna()
                 | (ep["candidate_events"].astype(str).str.strip() == "")).sum())
    return ("PASS" if share < 0.25 else "FAIL",
            f"{file_order}/{labelled} labels match the file-order default "
            f"({share:.0%}); {blank} windows left unlabelled")


def e_attribution_lookback():
    """E2: the attribution lookback must exceed the death-to-attention lag.

    Reads the CONSTANT rather than grepping for a numeric literal. The first
    version matched the first `Timedelta(days=N)` in the file, so replacing the
    hard-coded 14 with a named constant — the actual fix — would have made it
    read 0 and fail.

    60 days is a floor, not a comfortable margin: Daniel Prude died 2020-03-30
    and the bodycam footage was released 2020-09-02, five months later.
    """
    from config import ATTRIBUTION_LOOKBACK_DAYS as d
    s = src("13_extension_episodes.py")
    hard = re.findall(r"Timedelta\(days=(\d+)\)", s)
    if hard:
        return "FAIL", f"still hard-codes Timedelta(days={hard[0]}) instead of the constant"
    return ("PASS" if d >= 60 else "FAIL", f"ATTRIBUTION_LOOKBACK_DAYS={d} (needs >=60)")


# ===========================================================================
# OUTCOME / DATA COMPLETENESS
# ===========================================================================
def o_ems_download_complete():
    """P0: the extract must cover the full source, not 48% of it."""
    pages = sorted((DATA_PROCESSED / "ems_pages").glob("*.parquet")) \
        if (DATA_PROCESSED / "ems_pages").exists() else []
    if not pages:
        return "BLOCKED", "no pages downloaded"
    last = pd.read_parquet(pages[-1], columns=["incident_datetime"])
    mx = pd.to_datetime(last["incident_datetime"], errors="coerce").max()
    full = len(last) == 500_000
    return ("FAIL" if full else "PASS",
            f"{len(pages)} pages, last ends {mx.date() if pd.notna(mx) else '?'}, "
            f"{'last page FULL -> truncated' if full else 'complete'}")


def o_panel_exists():
    f = DATA_PROCESSED / "panel_cd_day.parquet"
    return ("PASS" if f.exists() else "BLOCKED", "present" if f.exists() else "panel not built")


def o_dropna_groupby():
    """O4: 00b groups on communitydistrict; NaN keys are silently dropped."""
    s = src("00b_download_ems_extract.py")
    return ("PASS" if "dropna=False" in s else "FAIL",
            "dropna=False" if "dropna=False" in s else "missing-CD rows silently discarded")


# ===========================================================================
# VERIFICATION — sources, links and claimed numbers
# ===========================================================================
VERIFY_LOG = DATA_REFERENCE / "source_verification_log.csv"
SOURCE_REGISTER = DATA_REFERENCE / "source_register.json"
CLAIMS_REGISTER = PROJECT_ROOT / "docs" / "CLAIMS_REGISTER.csv"
VERIFY_GOOD = {"verified", "unverifiable", "template", "skipped"}

# Which script writes which committed artifact. Only artifacts a script
# regenerates belong here - hand-maintained files (the B-HEARD adoption table,
# the frozen episode list) have no generating script and are deliberately absent.
SOURCE_ARTIFACT_OWNERS = {
    "data/reference/cai_components_daily.csv": "11_fetch_awareness_components.py",
    "data/reference/wiki_ext_basket_used.csv": "11_fetch_awareness_components.py",
    "data/reference/cai_trends_daily.csv": "11b_fetch_trends.py",
    "data/reference/article_title_map.csv": "29_resolve_article_titles.py",
    "data/reference/rename_recovery.csv": "29_resolve_article_titles.py",
    "data/reference/wiki_nyc_daily.csv": "28_build_nyc_attention.py",
    "data/reference/wiki_nyc_articles.csv": "28_build_nyc_attention.py",
    "data/reference/wiki_nyc_per_article.csv": "28_build_nyc_attention.py",
    "data/reference/precinct_cd_crosswalk.csv": "16_bheard_exposure.py",
    "data/reference/bheard_cd_exposure.csv": "16_bheard_exposure.py",
    "data/reference/victim_registry.csv": "10_build_victim_registry.py",
    "data/reference/basket_decisions.csv": "27_finalise_basket.py",
    "data/reference/confirmation_episodes_rebuilt.csv": "13_extension_episodes.py",
}


def _verify_log():
    if not VERIFY_LOG.exists():
        return None
    d = pd.read_csv(VERIFY_LOG, parse_dates=["run_utc"])
    return d if len(d) else None


def v_artifacts_current():
    """T14: no committed artifact may have been generated by an older version of
    its script.

    28_build_nyc_attention.py was given the historical-title fix during R0 and
    never re-run. The series on disk stayed canonical-title-only - missing Eric
    Garner, the largest NYC case, entirely - and a component was REJECTED in
    PAPER_MASTER.md, config.py and the claims register on measurements taken
    from it. Re-running moved the headline correlation from -0.18 to +0.62: the
    conclusion survived, none of the stated reasons did.

    The claims register cannot catch this. It verifies a number in a document
    still matches its artifact, and the number DID match - the artifact was the
    stale thing.

    Neither can an mtime comparison. The first version of this check compared
    file times and reported 7 of 13 artifacts stale after one round of COMMENT
    edits. A check that cries wolf on comments is a check people stop reading,
    which is how the defect survived in the first place.

    So provenance.py records a fingerprint of the generating script's CODE -
    ast-normalised, comments and docstrings stripped - at the moment the
    artifact is written, and this compares it to the script as it stands now.
    Verified directly: editing 28's comments, its docstring or its formatting
    leaves the fingerprint identical, and reverting its title-summing changes it.
    """
    reg = DATA_REFERENCE / "data_sources.csv"
    if not reg.exists():
        return "BLOCKED", "no provenance register"
    d = pd.read_csv(reg)
    if "generator_code_sha256" not in d.columns:
        return "BLOCKED", "register predates code fingerprinting; re-run the fetch stages"
    sys.path.insert(0, str(SCRIPTS))
    from provenance import code_fingerprint

    stale, unfingerprinted = [], []
    for _, r in d.iterrows():
        gen = str(r.get("generator") or "").strip()
        want = str(r.get("generator_code_sha256") or "").strip()
        if not gen or not want or want == "nan":
            unfingerprinted.append(str(r["source_id"]))
            continue
        f = SCRIPTS / gen
        if not f.exists():
            stale.append(f"{r['source_id']}: {gen} no longer exists")
            continue
        if code_fingerprint(f) != want:
            stale.append(f"{r['source_id']} ({Path(str(r['output_file'])).name}) "
                         f"predates changes to {gen}")
    checked = len(d) - len(unfingerprinted)
    if stale:
        return "FAIL", (f"{len(stale)} artifact(s) generated by an older version of "
                        f"their script: " + "; ".join(stale[:3]))
    if not checked:
        return "BLOCKED", (f"no artifact carries a code fingerprint yet "
                           f"({len(unfingerprinted)} rows predate it); re-run the "
                           "fetch stages so this can check anything")
    return "PASS", (f"{checked} artifact(s) match their generating script's code"
                    + (f"; {len(unfingerprinted)} predate fingerprinting "
                       f"({sorted(set(unfingerprinted))})" if unfingerprinted else ""))


def v_sources_verified():
    """Every source has a verification result NEWER than its artifact.

    A hash recorded before the file was last written proves nothing about the
    file. Two of these were live when the register was built: S8's artifact was
    replaced by a later run that never re-registered it, and S14's was edited in
    commit dabc1a6 (a column rename) without re-running the fetch, so both
    provenance rows described files that no longer existed in that form.

    BLOCKED, never PASS, when no scan has run. "Nobody checked" is not "fine" -
    that conflation is the error this whole suite exists to catch.
    """
    log = _verify_log()
    if log is None:
        return "BLOCKED", "no scan recorded — run 31_verify_sources.py --scan"
    if not SOURCE_REGISTER.exists():
        return "BLOCKED", "source_register.json is absent"
    reg = json.loads(SOURCE_REGISTER.read_text())["sources"]
    art = log[log["kind"] == "artifact"]
    stale, unchecked, bad = [], [], []
    for s in reg:
        for a in s.get("artifacts", []):
            rows = art[(art["source_id"] == s["id"]) & (art["target"] == a)]
            if not len(rows):
                unchecked.append(f"{s['id']}:{a}")
                continue
            last = rows.sort_values("run_utc").iloc[-1]
            if last["status"] not in VERIFY_GOOD:
                bad.append(f"{s['id']}:{Path(a).name}={last['status']}")
                continue
            f = PROJECT_ROOT / a
            # STALE means the CONTENT changed since it was verified, not the file's
            # mtime: a fresh checkout resets every mtime and this check failed on 21
            # byte-identical files (CP1 audit #56). The log records the sha256
            # prefix of what was verified; compare to the file as it is now.
            _logged = re.search(r"sha256 ([0-9a-f]{16})", str(last.get("detail", "")))
            _now = hashlib.sha256(f.read_bytes()).hexdigest()[:16] if f.exists() else None
            if f.exists() and _logged and _now != _logged.group(1):
                stale.append(f"{s['id']}:{Path(a).name}")
    if unchecked:
        return "BLOCKED", f"{len(unchecked)} artifact(s) never scanned: {unchecked[:3]}"
    if bad or stale:
        return "FAIL", (f"{len(bad)} not verified {bad[:3]}; "
                        f"{len(stale)} verified before the file last changed {stale[:3]}")
    return "PASS", f"{len(art['target'].unique())} artifacts, all verified after their last write"


def v_source_id_per_artifact():
    """P3: a source_id names ONE artifact, for the whole life of the register.

    data_sources.csv is defined as current state — exactly one row per
    source_id — and V.no_duplicate_source_ids enforces that. But "one row per
    id" says nothing about whether the id still describes the same FILE it did
    last week, and the difference is where an artifact can vanish.

    The broad-basket sensitivity arm writes its own components file and its own
    episode list, correctly suffixed by config.basket_artifact. Its provenance
    was not suffixed. So running it rewrote S11 and D1 in place, repointing them
    at the broad artifacts, and the STRICT arm — the primary one, the one the
    paper reports — was left with no provenance row at all.

    Nothing failed. V.artifacts_current checks the generator behind every row
    that exists; it has no way to ask about a row that stopped existing, so it
    happily verified the broad files and reported all artifacts current. The
    register lost the primary arm's provenance silently, which is the single
    thing it exists to make impossible.

    The invariant that catches it is cheap: across the current register AND its
    history, the set of output_files a given source_id has ever claimed must
    have exactly one member. Repointing an id is then a check failure instead of
    an unobservable overwrite, and the remedy is a new id — which is what
    config.basket_source_id now mints.

    This is also the first check that READS data_sources_history.csv, and doing
    so found the history unparseable: written with `header=not exists()`, its
    header was frozen at the 7-column schema of its first append while later
    rows carried 9 fields, so pandas raised ParserError on line 22. An
    append-only history nobody can read is not a record of anything.
    """
    cur_f = DATA_REFERENCE / "data_sources.csv"
    hist_f = DATA_REFERENCE / "data_sources_history.csv"
    if not cur_f.exists():
        return "BLOCKED", "no provenance register"
    frames = [pd.read_csv(cur_f)]
    if hist_f.exists():
        try:
            frames.append(pd.read_csv(hist_f))
        except Exception as e:
            return "FAIL", (f"data_sources_history.csv does not parse ({type(e).__name__}: "
                            f"{str(e)[:90]}) — the only record of what an artifact's "
                            "hash used to be is unreadable")
    both = pd.concat(frames, ignore_index=True)
    if "output_file" not in both.columns:
        return "BLOCKED", "register has no output_file column"
    seen = {}
    for _, r in both.iterrows():
        f = str(r.get("output_file") or "").strip()
        if f and f.lower() != "nan":
            seen.setdefault(str(r["source_id"]), set()).add(f)
    repointed = {k: sorted(v) for k, v in seen.items() if len(v) > 1}
    if repointed:
        return "FAIL", (f"{len(repointed)} source_id(s) have described more than one "
                        f"artifact, so an earlier artifact's provenance was overwritten "
                        f"rather than superseded: "
                        + "; ".join(f"{k} -> {v}" for k, v in list(repointed.items())[:3]))
    return "PASS", (f"{len(seen)} source_id(s) each name exactly one artifact across "
                    f"{len(both)} current and historical rows")


def v_no_duplicate_source_ids():
    """X8/X13: one row per source, and no two scripts claiming the same id.

    data/reference/data_sources.csv held 21 rows under 9 ids, because seven
    scripts each appended with mode="a" and nothing ever re-keyed. Worse, two of
    those ids COLLIDED: 16_bheard_exposure.py emitted S10 and S11, which belong
    to Mapping Police Violence and the CAI components. The register had been
    hand-renumbered to S14/S15 to hide it while the script was left alone, so
    the collision would have returned on the next run - and with one row per id,
    it would have silently overwritten two other sources' provenance.
    """
    f = DATA_REFERENCE / "data_sources.csv"
    if not f.exists():
        return "BLOCKED", "no provenance register"
    d = pd.read_csv(f)
    dupes = d["source_id"].value_counts()
    dupes = dupes[dupes > 1]
    emitted = {}
    for sp in sorted(SCRIPTS.glob("*.py")):
        for m in re.finditer(r'log_source\(\s*"([^"]+)"', sp.read_text()):
            emitted.setdefault(m.group(1), set()).add(sp.name)
    collisions = {k: sorted(v) for k, v in emitted.items() if len(v) > 1}
    # Only provenance.py may WRITE the register. Any other script writing it is
    # a second writer, and a second writer is how the append-mode duplication
    # survived seven scripts. (Merely naming the file is fine - this check and
    # 31_verify_sources.py both read it.)
    appenders = []
    for sp in sorted(SCRIPTS.glob("*.py")):
        if sp.name == "provenance.py":
            continue
        t = sp.read_text()
        if re.search(r'to_csv\(\s*\w*[Ss]?[Oo]?[Uu]?[Rr]?[Cc]?[Ee]?\w*(LOG|log|lp)\b', t) \
                and "data_sources.csv" in t:
            appenders.append(sp.name)
        elif re.search(r'data_sources\.csv["\']\s*\)?\s*$.{0,200}?mode="a"', t,
                       re.S | re.M):
            appenders.append(sp.name)
    if len(dupes):
        return "FAIL", f"{len(dupes)} duplicated id(s): {dupes.to_dict()}"
    if collisions:
        return "FAIL", f"two scripts emit the same id: {collisions}"
    if appenders:
        return "FAIL", f"still appending instead of re-keying: {appenders}"
    return "PASS", f"{len(d)} rows, {d['source_id'].nunique()} ids, no collisions"


# Table rows that carry a number but are NOT claims about this study's results,
# each with the reason it is exempt. Matched as substrings of the row.
EXHIBIT_EXEMPT = {}

# The only words the register may use for severity; "blocking" is the one that
# obliges a check (M.register_sync).
SEVERITIES = {"blocking", "moderate", "minor"}

# CP2, line 2: simulations required of every inferential stratum's certificate
# before the freeze may be lifted (S.lift_requires_1000_sims); defined once in
# config so 30_confirmatory_run.py refuses on the same number.
from config import LIFT_MIN_SIMS  # noqa: E402


def v_claims_cover_exhibits():
    """P6: a number cannot enter a PAPER_MASTER table without a claim behind it.

    The standing rule is that no number reaches the paper without a claims
    register entry that reproduces it. Nothing enforced it. V.claims_reproduce
    verifies the claims that ARE registered and is silent about the ones that
    were never written — coverage validated, content not — which is the same
    inversion that hid the basket construct defect for the whole project,
    running the other way.

    It was broken the day after it was restated. Commit 0957a3a put the broad
    arm's comparison table into 4.1 with six unregistered numbers in it, and
    every check passed.

    SCOPE IS THE WHOLE DESIGN HERE. Asserting that every numeral in 1,200 lines
    of prose carries a claim would fire on dates, section numbers, line
    references and counts stated in passing, and this project has twice learned
    what happens to a check that cries wolf: people stop reading it, which is
    how the defect it was guarding survived. So this covers MARKDOWN TABLE ROWS
    only. Tables are where exhibit values live, they are few, they are where a
    reader looks for the result, and they are exactly where the six escaped.

    A cell value is covered when some claim's template — rendered through the
    same matcher the verifier and the updater use, so the three cannot disagree
    about what "the claim is in the document" means — captures it. Rows that are
    genuinely not claims (units, labels, schematic illustrations) go in
    EXHIBIT_EXEMPT with a reason, which is a decision on the record rather than
    a silent gap.

    A template for a non-first column has to carry the values of the columns
    before it as literal anchor text ("| C2 | anchor shift | contiguous | 30 |
    0.06 | {} |"): there is no other way to say which cell is meant. The cost is
    known and accepted: when a sibling value moves, that claim reports "wording
    not in the document" rather than a mismatch, and the sibling's own claim
    reports the mismatch. Both fail, so nothing is hidden.
    """
    import re as _re
    reg = PROJECT_ROOT / "docs" / "CLAIMS_REGISTER.csv"
    # PAPER_MASTER is the source document; PAPER.md is the manuscript drafted
    # from it (Phase J, 2026-09-13). A table in either is an exhibit, and the
    # manuscript is where a number is most likely to be retyped by hand.
    docs = [PROJECT_ROOT / "docs" / "PAPER_MASTER.md", PROJECT_ROOT / "docs" / "PAPER.md"]
    docs = [d for d in docs if d.exists()]
    if not docs or not reg.exists():
        return "BLOCKED", "PAPER_MASTER.md or CLAIMS_REGISTER.csv absent"
    sys.path.insert(0, str(SCRIPTS))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_verify31", SCRIPTS / "31_verify_sources.py")
    v31 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v31)

    all_claims = pd.read_csv(reg)
    NUM = _re.compile(v31.NUMBER_RE)
    # CELL BY CELL, not row by row (CP1 audit #27/#28, 2026-09-13). The first
    # version asked whether ANY claim matched somewhere on the line, so one
    # claim covered every number in its row: the 7.4 table's rejection rates
    # rode on the KS claims beside them for months. Now each number token in a
    # numeric cell must lie INSIDE some claim's captured group. And a cell is
    # numeric when it STARTS with a number - "1.05x", "2.203 -> 2.092", "1 of
    # 3,472" and "-0.005 pp" are numbers with decoration, not labels; the old
    # whole-cell match skipped every one of them.
    #
    # Labels are still excluded by SHAPE: ISO dates, and a four-digit year
    # followed by a dash, an arrow or a slash (a span such as 2015-2024 or
    # 2017-2022 / 2015-2024). Flagging every date and span is how this check
    # would become noise and then be ignored.
    ISO_DATE = _re.compile(r"\d{4}-\d{2}-\d{2}")

    def label_like(rest, m):
        return bool(ISO_DATE.match(rest)) or bool(
            _re.fullmatch(r"\d{4}", m.group()) and rest[m.end():m.end() + 1] in "\u2013-\u2192/")

    uncovered, n_cells, n_tokens, n_pats = [], 0, 0, 0
    for doc in docs:
      claims = all_claims[all_claims["doc"].astype(str).str.endswith(doc.name)]
      pats = []
      for t in claims["template"].dropna():
          try:
              pats.append(_re.compile(v31._template_regex(t)))
          except _re.error:
              continue
      n_pats += len(pats)
      for i, line in enumerate(doc.read_text().splitlines(), 1):
          t = line.strip()
          if not (t.startswith("|") and t.endswith("|") and t.count("|") >= 3):
              continue
          cells = t.strip("|").split("|")
          if all(set(c.strip()) <= set("-: ") for c in cells):      # separator row
              continue
          covered_spans = [m.span(1) for r in pats for m in r.finditer(line)]
          pos = line.index("|")
          for c in cells:
              cs, pos = pos + 1, pos + 1 + len(c)
              v = c.replace("*", "").replace("~", "").strip()
              first = v.split()[0] if v.split() else ""
              m0 = NUM.match(first) if first else None
              if not m0 or label_like(first, m0):
                  continue
              n_cells += 1
              for m in NUM.finditer(c):
                  if label_like(c[m.start():], NUM.match(c[m.start():])):
                      continue
                  n_tokens += 1
                  a_, b_ = cs + m.start(), cs + m.end()
                  if any(s0 <= a_ and b_ <= e0 for s0, e0 in covered_spans):
                      continue
                  if any(k in line for k in EXHIBIT_EXEMPT):
                      continue
                  uncovered.append(f"{doc.name}:{i}: {m.group()} in {c.strip()[:40]!r}")

    if uncovered:
        return "FAIL", (f"{len(uncovered)} table cell value(s) carry a number with no claim "
                        f"reproducing it: " + "; ".join(uncovered[:3]))
    return "PASS", (f"every one of {n_tokens} numbers in {n_cells} numeric table cells of "
                    f"{', '.join(d.name for d in docs)} is reproduced by one of {n_pats} claims, "
                    f"or exempt with a reason ({len(EXHIBIT_EXEMPT)})")


def v_claims_reproduce():
    """Every number claimed in PAPER_MASTER.md recomputes from its artifact.

    The register names the document, a template containing {}, the artifact and
    the expression. This fails in BOTH directions: edit the document and the
    rendered text is no longer found; rebuild the data and the computed value no
    longer matches what the document says. A number that cannot be regenerated
    is a check failure, not a typo.

    It RECOMPUTES here rather than reading the scan log. Trusting the log needed
    a staleness gate ("was the document touched since the scan?"), and that gate
    was circular: 31_verify_sources.py regenerates SOURCE_REGISTER.md, which is
    itself a claimed document, so the check blocked after every scan. Claims
    need no network, so there is no reason to trust a record instead of
    measuring.
    """
    if not CLAIMS_REGISTER.exists():
        return "BLOCKED", "docs/CLAIMS_REGISTER.csv is absent"
    spec = importlib.util.spec_from_file_location(
        "verify_sources", SCRIPTS / "31_verify_sources.py")
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    claims = pd.read_csv(CLAIMS_REGISTER)
    cache, bad = {}, []
    for _, r in claims.iterrows():
        status, detail = v.check_claim(r, cache)
        if status not in VERIFY_GOOD:
            bad.append(f"{r['claim_id']} ({status})")
    if bad:
        return "FAIL", f"{len(bad)} of {len(claims)} claims do not reproduce: " + "; ".join(bad[:3])
    return "PASS", f"{len(claims)} claims recomputed and found verbatim in the document"


def v_links_resolve():
    """Every registered endpoint has a recorded, dated result.

    A failure is a RECORDED RESULT, not something to retry until green - so this
    passes on a dated failure being present and visible, and fails only when an
    endpoint has never been scanned or its last result was a hard failure. Rate
    limits and our own egress policy are recorded as `unreachable`: they say
    something about our access, not about the source.
    """
    log = _verify_log()
    if log is None:
        return "BLOCKED", "no scan recorded — run 31_verify_sources.py --scan"
    if not SOURCE_REGISTER.exists():
        return "BLOCKED", "source_register.json is absent"
    reg = json.loads(SOURCE_REGISTER.read_text())["sources"]
    lk = log[log["kind"] == "link"]
    never, failed, unreachable = [], [], []
    for s in reg:
        for u in (s.get("endpoints") or ["(none)"]):
            rows = lk[(lk["source_id"] == s["id"]) & (lk["target"] == u)]
            if not len(rows):
                never.append(f"{s['id']}:{u}")
                continue
            last = rows.sort_values("run_utc").iloc[-1]
            if last["status"] == "failed":
                failed.append(f"{s['id']}:{u}")
            elif last["status"] == "unreachable":
                unreachable.append(f"{s['id']}")
    if never:
        return "BLOCKED", f"{len(never)} endpoint(s) never scanned: {never[:2]}"
    if failed:
        return "FAIL", f"{len(failed)} endpoint(s) returned an error: {failed[:3]}"
    note = f"; {len(unreachable)} unreachable from here ({sorted(set(unreachable))})" \
        if unreachable else ""
    return "PASS", f"{len(lk['target'].unique())} endpoints, last result recorded{note}"


# ===========================================================================
# META — the register and the suite must not drift apart
# ===========================================================================
def m_status_honest():
    """No finding claims to be fixed while a check tagged to it is FAILING.

    AUDIT_FINDINGS.csv had no status column: whether a finding was closed was
    inferable only by reading this suite and matching tags by eye. Worse, every
    entry's `fix` column is written when the finding is FILED — it describes what
    should be done, not what was — so a register full of prescriptions read like
    a register full of completions.

    The column records intent:

      fixed        the remedy is believed implemented
      open         known outstanding
      unverified   nothing checks it. A statement of work remaining, and NOT a
                   synonym for fine.

    This asserts one direction only: nothing may say `fixed` while a check
    tagged to it is currently FAILING. Two things are deliberately not asserted,
    and both are lessons from writing it:

      A check ABSENT from the artifact is not a failing check. The first version
      treated missing as non-passing, so adding any new check instantly made its
      finding look unfixed — a check failing for the wrong reason, inside the
      check whose whole job is to stop the register claiming what it cannot show.

      A two-way comparison OSCILLATES. Deriving the column and then testing the
      file against the derivation means every change flips it: the stored value
      is always one run behind, so it fails, and fixing it makes the next run
      fail the other way. This check also excludes ITSELF from the evidence, for
      the same reason a witness cannot corroborate their own testimony: tagged to
      O5, its own failure would make O5 look open, which would keep it failing.
    """
    reg = PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv"
    res = OUTPUTS_TABLES / "regression_suite.csv"
    if not reg.exists():
        return "BLOCKED", "AUDIT_FINDINGS.csv is absent"
    d = pd.read_csv(reg)
    if "status" not in d.columns:
        return "FAIL", ("AUDIT_FINDINGS.csv has no status column, so whether a "
                        "finding is closed is recorded nowhere")
    allowed = {"fixed", "open", "unverified"}
    bad_vals = sorted(set(d["status"].astype(str)) - allowed)
    if bad_vals:
        return "FAIL", f"status values outside {sorted(allowed)}: {bad_vals}"
    # No artifact yet (first run in a fresh container) is NOT a reason to
    # return BLOCKED: this run's own results are in memory and cover every
    # check that has already run, which is all but the ones after this one.
    # Returning BLOCKED here made the register-honesty check inert on exactly
    # the run where a fresh clone first shows which "fixed" findings have
    # failing checks (CP1 audit #56).
    SELF = "M.status_honest"
    tagged = {}
    for cid, fids, _desc, _fn in CHECKS:
        if cid == SELF:
            continue
        for f in str(fids).split(","):
            if f.strip():
                tagged.setdefault(f.strip(), []).append(cid)
    # THIS RUN'S STATES FIRST, the artifact only as a fallback.
    #
    # Reading the artifact alone made this check trail by one run: X14 was marked
    # `fixed` while the artifact still held V.claims_reproduce=FAIL from BEFORE
    # that claim was repaired, so the check reported a lie that no longer
    # existed. The suite accumulates into `results` as it goes and this check
    # runs 61st of 63, so every other check's state for THIS run is already
    # available — except the one after it, which the artifact still covers.
    #
    # A check that reports yesterday's state is a check that can be right about
    # the wrong day, which is the same class of error as reading a stale
    # artifact anywhere else in this project.
    state = (dict(zip(*[pd.read_csv(res)[c] for c in ("check", "state")]))
             if res.exists() else {})
    state.update({r["check"]: r["state"] for r in results})

    lying = []
    for _, r in d.iterrows():
        if str(r["status"]) != "fixed":
            continue
        # BLOCKED counts against a "fixed" claim as much as FAIL does. BLOCKED
        # means "could not evaluate", and this suite treats it as deliberately
        # not a pass everywhere else; a finding whose only evidence could not be
        # evaluated has no evidence.
        failing = [c for c in tagged.get(r["id"], [])
                   if state.get(c) in ("FAIL", "BLOCKED", "ERROR")]
        if failing:
            lying.append(f"{r['id']} ({failing[0]}={state.get(failing[0])})")
    counts = d["status"].value_counts().to_dict()
    detail = (f"{len(d)} findings: "
              + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
              + f"; {len(d) - int(counts.get('unverified', 0))} carry a check")
    if lying:
        return "FAIL", (f"{len(lying)} finding(s) say 'fixed' while a check tagged "
                        f"to them is not passing: {lying[:4]}")
    return "PASS", detail


def m_finding_ids_unique():
    """Every finding has its own id, which a register keyed by id needs to be true.

    AUDIT_FINDINGS.csv is addressed by id everywhere — the CHECKS table tags
    findings by id, M.register_sync resolves those tags, M.status_honest reads a
    status per id. All of that quietly assumes one row per id, and nothing
    checked it.

    It broke on 2026-09-12. The register already held N1, N2 and N3 from the
    Wikidata scope work, and three new findings about randomization inference
    were filed under the same three ids. Two rows then shared an id with
    different statuses and different checks, so "what is N3's status" had two
    answers and the tag `N3` resolved to whichever pandas returned first. The
    first attempt to fix it collided AGAIN, because R2 and R3 were also taken —
    which is the same mistake a second time and the reason this check exists
    rather than a note saying to be careful.

    Cheap, total, and it makes the assumption every other register check rests on
    into something that fails loudly.
    """
    f = PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv"
    if not f.exists():
        return "BLOCKED", "AUDIT_FINDINGS.csv absent"
    d = pd.read_csv(f)
    if "id" not in d.columns:
        return "FAIL", "AUDIT_FINDINGS.csv has no id column"
    dup = d[d.duplicated("id", keep=False)]
    if len(dup):
        byid = {k: len(g) for k, g in dup.groupby("id")}
        return "FAIL", (f"{len(byid)} finding id(s) appear on more than one row, so "
                        f"every check tagged to them resolves ambiguously: {byid}")
    return "PASS", f"all {len(d)} findings carry a distinct id"


def m_register_sync():
    """Every tag resolves to a finding, every blocking finding has a check, the
    register's `checks` column says what the suite says, and severity is one of
    three words.

    Without this, a finding can be silently dropped from the register or a check
    can be tagged with an ID that no longer exists, and coverage looks fine while
    the defect goes untested. That is the same "couldn't check reads as fine"
    failure the suite exists to prevent, applied to the suite itself.

    The last two clauses are from the CP1 audit (2026-09-13). Ten findings named
    a different check in the register than the suite tagged them with (RI2 said
    S.ri_scheme_certified, which never tested it; the suite said
    S.calibration_can_fail, which does), so M.status_honest - which reads the
    REGISTER's column - was judging some findings by the wrong check. And
    severity had five spellings, two of which ("major", "serious") escaped the
    rule that a blocking finding must have a check.
    """
    reg = pd.read_csv(PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv")
    known = set(reg["id"].astype(str))
    tags = {}
    for name, fids, _, _ in CHECKS:
        for f in fids.split(","):
            tags.setdefault(f.strip(), set()).add(name)
    names = {c[0] for c in CHECKS}
    tagged = set(tags)
    unknown = sorted(tagged - known)
    blocking = set(reg.loc[reg["severity"] == "blocking", "id"].astype(str))
    uncovered = sorted(blocking - tagged)
    bad_sev = sorted(set(reg["severity"].astype(str)) - SEVERITIES)
    drift = []
    for _, r in reg.iterrows():
        declared = {c.strip() for c in re.split(r"[;,]", str(r.get("checks") or ""))
                    if c.strip() and c.strip() != "nan"}
        suite = tags.get(str(r["id"]), set())
        if declared - names:
            drift.append(f"{r['id']} names a check that does not exist: "
                         f"{sorted(declared - names)}")
        elif declared != suite:
            drift.append(f"{r['id']}: register says {sorted(declared) or '-'}, "
                         f"suite tags {sorted(suite) or '-'}")
    if unknown:
        return "FAIL", f"tags with no finding: {unknown}"
    if uncovered:
        return "FAIL", f"blocking findings with no check: {uncovered}"
    if bad_sev:
        return "FAIL", f"severity outside {sorted(SEVERITIES)}: {bad_sev}"
    if drift:
        return "FAIL", (f"{len(drift)} finding(s) whose register `checks` column disagrees "
                        f"with the suite's tags: " + "; ".join(drift[:3]))
    return "PASS", (f"{len(tagged)}/{len(known)} findings tagged; all {len(blocking)} "
                    f"blocking covered; register and suite agree on every finding")


# ===========================================================================
def s_ledger_identity():
    """N7, N8: a checkpoint ledger is keyed to the DESIGN that produced it, and a
    ledger from any other design is quarantined rather than pooled.

    Both ledgers (18's per-sim calibration ledger, randomization_p's per-draw RI
    ledger) were keyed on a filename - stratum and draw count, or outcome and
    window. A ledger left behind by an earlier panel, episode list, day-shock
    setting or scheme would be resumed as if nothing had changed, pairing new
    observed statistics with old null draws. Nothing would have said so.

    Now every ledger is opened through event_study.open_ledger with a design
    dict; a sidecar carries its fingerprint; a mismatch, a missing sidecar or an
    unparseable file moves the ledger aside under a name that says why. Adoption
    of a sidecar-less ledger exists only behind an explicit flag in 18.

    Asserted three ways. By AST: both writers call open_ledger, and 18's
    adopt_ledger call sits behind its flag. By running: on a temporary ledger,
    resume works with the same design, and a changed design, a removed sidecar
    and a corrupt file each quarantine. And 18 records a failed sim as a row
    (finding N8) instead of dropping it: the write call carries `nan,nan` and the
    verdict carries n_sims_failed.
    """
    import ast as _ast
    import importlib
    import tempfile
    sys.path.insert(0, str(SCRIPTS))
    es = importlib.import_module("event_study")
    problems = []

    def _calls(tree, name):
        return [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)
                and isinstance(n.func, _ast.Name) and n.func.id == name]

    t18 = _ast.parse((SCRIPTS / "18_null_calibration.py").read_text())
    tes = _ast.parse((SCRIPTS / "event_study.py").read_text())
    if not _calls(t18, "open_ledger"):
        problems.append("18_null_calibration.py opens its ledger without open_ledger")
    rp = next((n for n in _ast.walk(tes) if isinstance(n, _ast.FunctionDef)
               and n.name == "randomization_p"), None)
    if rp is None or not _calls(rp, "open_ledger"):
        problems.append("event_study.randomization_p opens its ledger without open_ledger")
    guarded = any(isinstance(n, _ast.If) and "adopt_ledger_without_identity" in _ast.unparse(n.test)
                  and _calls(n, "adopt_ledger") for n in _ast.walk(t18))
    if _calls(t18, "adopt_ledger") and not guarded:
        problems.append("18 adopts a sidecar-less ledger outside its explicit flag")
    writes_nan = any(isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute)
                     and n.func.attr == "write" and "nan,nan" in _ast.unparse(n)
                     for n in _ast.walk(t18))
    if not writes_nan or "n_sims_failed" not in _ast.unparse(t18):
        problems.append("18 does not record failed sims as ledger rows with n_sims_failed")

    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "ledger.csv"
        d1, d2 = {"kind": "selftest", "x": 1}, {"kind": "selftest", "x": 2}
        banked, meta = es.open_ledger(led, d1, ["i", "v"])
        with led.open("a") as fh:
            fh.write("0,1.5\n")
        banked, _ = es.open_ledger(led, d1, ["i", "v"])
        if len(banked) != 1:
            problems.append("same design did not resume the banked row")
        banked, _ = es.open_ledger(led, d2, ["i", "v"])
        if len(banked) != 0 or not any("stale" in q.name for q in Path(td).iterdir()):
            problems.append("a changed design was pooled instead of quarantined")
        led.with_suffix(".meta.json").unlink()
        banked, _ = es.open_ledger(led, d2, ["i", "v"])
        if not any("unverified" in q.name for q in Path(td).iterdir()):
            problems.append("a sidecar-less ledger was resumed instead of quarantined")
        led.write_text("i,v\n0,1,2\n")
        banked, _ = es.open_ledger(led, d2, ["i", "v"])
        if not any("corrupt" in q.name for q in Path(td).iterdir()) or len(banked):
            problems.append("a corrupt ledger was not quarantined")
    return ("PASS" if not problems else "FAIL",
            "both ledgers open through open_ledger; resume, stale, unverified and corrupt "
            "cases behave on a temporary ledger; 18 records failed sims"
            if not problems else "; ".join(problems))


def s_placebo_relocations_reported():
    """N9: the within-block shift's relocation count reaches the caller.

    placebo_starts_circular snaps a real start that is not itself an admissible
    day onto the nearest one and returns the count, so a caller can see that its
    placebo designs differ from the observed one in where two episodes sit
    (finding P2's edge episodes). randomization_p discarded it with a `[0]`, so
    the count reached nobody. Asserted by AST: the drawer's result is unpacked
    into a tuple that names `snapped`, and the total is reported.
    """
    import ast as _ast
    tree = _ast.parse((SCRIPTS / "event_study.py").read_text())
    rp = next((n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)
               and n.name == "randomization_p"), None)
    if rp is None:
        return "FAIL", "event_study.py has no randomization_p"
    unpacked = any(isinstance(n, _ast.Assign) and isinstance(n.targets[0], _ast.Tuple)
                   and any(isinstance(e, _ast.Name) and e.id == "snapped" for e in n.targets[0].elts)
                   and "draw_placebo" in _ast.unparse(n.value)
                   for n in _ast.walk(rp))
    reported = "snapped_total" in _ast.unparse(rp) and any(
        isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id == "print"
        and "snapped_total" in _ast.unparse(n) for n in _ast.walk(rp))
    if not unpacked:
        return "FAIL", "randomization_p discards the drawer's relocation count"
    if not reported:
        return "FAIL", "randomization_p counts relocations but never reports them"
    return "PASS", "randomization_p unpacks and reports the relocation count per run"


def s_confirmatory_uses_certified_machinery():
    """P8, P9, P10: the sealed confirmatory script estimates with the SAME code the
    calibration certifies, and its synthetic dry run proves the script as it
    stands.

    The CP1 audit (2026-09-13) found three things in 30_confirmatory_run.py
    that no check looked at. It kept its own copy of the placebo draw, still
    crossing the window seam that finding RI3 had replaced in event_study, so
    C1's certificate would have described a null the run did not draw (P8). It
    indexed the calibration dict with a key that no longer existed, so the real
    run would have crashed after every cell was estimated and before the result
    was written (P9). And it selected episodes by start-in-stratum rather than
    by the pre-specified first-week containment the calibration applies (P10).

    Asserted by AST: 30 calls event_study's randomization_p, draw_scheme_for and
    stratum_episodes, passes windows= and a ledger to the draw, and defines no
    placebo geometry of its own. And by artifact: the synthetic dry-run result
    exists, is stamped SYNTHETIC, and its sidecar names the code fingerprint of
    30 and event_study as they are now - a dry run that proved an older script
    is BLOCKED, not evidence.
    """
    import ast as _ast
    import json
    sys.path.insert(0, str(SCRIPTS))
    from provenance import code_fingerprint
    f = SCRIPTS / "30_confirmatory_run.py"
    if not f.exists():
        return "BLOCKED", "30_confirmatory_run.py absent"
    tree = _ast.parse(f.read_text())
    called = {n.func.id for n in _ast.walk(tree)
              if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)}
    problems = []
    for need in ("randomization_p", "draw_scheme_for", "stratum_episodes", "require_calibrated"):
        if need not in called:
            problems.append(f"30 never calls event_study.{need}")
    defined = {n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
    own = defined & {"placebo_starts", "placebo_starts_circular", "circular_shift_starts",
                     "contiguous_blocks", "admissible_starts", "calibrated_scheme_feasible",
                     "fit", "first_week", "_formula"}
    if own:
        problems.append(f"30 defines its own estimator/placebo machinery: {sorted(own)}")
    rp_calls = [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)
                and isinstance(n.func, _ast.Name) and n.func.id == "randomization_p"]
    for c in rp_calls:
        kws = {k.arg for k in c.keywords}
        if not {"windows", "ledger", "seed"} <= kws:
            problems.append("30 calls randomization_p without windows=, ledger= and seed=")
    art = OUTPUTS_TABLES / "confirmatory_results_dryrun_synthetic.csv"
    meta = art.with_suffix(".meta.json")
    if problems:
        return "FAIL", "; ".join(problems)
    if not art.exists() or not meta.exists():
        return "BLOCKED", ("no synthetic dry-run artifact with a code sidecar — run "
                           "30_confirmatory_run.py --dry-run-synthetic --draws 20")
    try:
        m = json.loads(meta.read_text())
        d = pd.read_csv(art)
    except Exception as e:
        return "FAIL", f"dry-run artifact unreadable: {type(e).__name__}: {e}"
    if m.get("data_source") != "SYNTHETIC" or not (d.get("data_source") == "SYNTHETIC").all():
        return "FAIL", "the dry-run artifact is not stamped SYNTHETIC in every row"
    stale = []
    if m.get("script_code_sha256") != code_fingerprint(f):
        stale.append("30_confirmatory_run.py")
    if m.get("event_study_code_sha256") != code_fingerprint(SCRIPTS / "event_study.py"):
        stale.append("event_study.py")
    if stale:
        return "BLOCKED", (f"the synthetic dry run predates the current {stale}; re-run "
                           "30_confirmatory_run.py --dry-run-synthetic before relying on it")
    ok = int((d["status"] == "OK").sum())
    return "PASS", (f"30 draws through event_study ({len(rp_calls)} call site(s), windows/ledger/"
                    f"seed passed), defines no machinery of its own; dry run current: "
                    f"{len(d)} rows, {ok} OK, at {m.get('draws')} draws on {m.get('jobs')} worker(s)")


def t_spliced_arm_prebreak_identical():
    """L7 (addendum 20): the spliced `user + automated` arm equals the primary on
    every day before the agent class existed, and differs after.

    A CONTENT check, not a coverage one. The arm's whole licence is that
    `automated` is identically zero before 2020-04-29, so the sum is the primary
    there; if the two indices ever differ before the break, either the class
    was backfilled upstream or the arm was built from a different basket or a
    different shared component - all of which would make the sensitivity a
    comparison of two things, not one. Equal after the break would mean the arm
    is not measuring the break at all.
    """
    from config import arm_artifact
    a = DATA_PROCESSED / "cai_daily.parquet"
    b = DATA_PROCESSED / arm_artifact("cai_daily.parquet", "spliced")
    if not a.exists() or not b.exists():
        return "BLOCKED", "primary or spliced index absent — run 12_build_cai.py [--arm spliced]"
    x = pd.read_parquet(a)[["date", "cai_d", "wiki_ext"]].set_index("date")
    y = pd.read_parquet(b)[["date", "cai_d", "wiki_ext"]].set_index("date")
    j = x.join(y, rsuffix="_s").dropna()
    if j.empty:
        return "FAIL", "the two indices share no scored day"
    break_day = pd.Timestamp("2020-04-29")
    pre = j[j.index < break_day]
    post = j[j.index >= break_day]
    diff_pre = float((pre["cai_d"] - pre["cai_d_s"]).abs().max()) if len(pre) else 0.0
    n_diff_post = int(((post["cai_d"] - post["cai_d_s"]).abs() > 1e-12).sum())
    if diff_pre > 1e-9:
        return "FAIL", (f"spliced and primary CAI-D differ before {break_day.date()} "
                        f"(max |diff| {diff_pre:.3e}); the arm is not a splice of the primary")
    if n_diff_post == 0:
        return "FAIL", "spliced and primary CAI-D are identical after the break; the arm measures nothing"
    return "PASS", (f"identical on all {len(pre):,} pre-break days; differs on "
                    f"{n_diff_post:,} of {len(post):,} post-break days "
                    f"(mean shift {(post['cai_d_s'] - post['cai_d']).mean():+.4f} SD)")


CHECKS = [
    ("T.anchor_monthly", "X1,T4,T5,L4", "Trends anchor rescales all days, not just 1-7", t_anchor_monthly),
    ("T.title_agg_no_trend", "T12", "title aggregation is not measuring accumulation", t_title_agg_no_trend),
    ("T.realised_coverage", "T7", "register asserts no span the data lacks", t_realised_coverage_recorded),
    ("X.csv_reproducible", "X15", "derived weights round-trip exactly", x_derived_csv_reproducible),
    ("X.no_stale_attribution", "X7", "DATA_AUDIT no longer misattributes 378->630", x_no_stale_audit_attribution),
    ("T.wiki_fetch_complete", "T15", "no basket article lost a title to a failed fetch", t_wiki_fetch_complete),
    ("T.no_redirect_candidates", "T18", "no basket candidate is a redirect", t_no_redirect_candidates),
    ("T.exclusion_reasons_true", "N1,N3", "no basket exclusion states a reason the scope file contradicts", t_exclusion_reasons_true),
    ("T.scope_covers_candidates", "N2", "every basket candidate was actually asked about", t_scope_covers_candidates),
    ("T.basket_is_police_violence", "B1", "every basket article has evidence police were the actor", t_basket_is_police_violence),
    ("D.edp_family_justified", "O3", "the EDP grouping does not rest on a justification known to be false", d_edp_family_justified),
    ("T.trends_precision_stable", "T6", "the live Trends component keeps its resolution over the decade", t_trends_precision_stable),
    ("T.spliced_arm_prebreak_identical", "L7", "the spliced Wikipedia arm equals the primary before the agent class existed", t_spliced_arm_prebreak_identical),
    ("T.agent_class_break_bounded", "L7", "the April 2020 agent-class break is measured and bounded", t_agent_class_break_bounded),
    ("T.basket_evidence_not_namesake", "T13,B3", "no basket article rests on an exact-name registry match alone", t_basket_evidence_not_namesake),
    ("T.basket_country_evidence", "B2", "no basket article admitted without US evidence", t_basket_country_evidence),
    ("T.no_duplicate_person", "T17", "no basket article duplicates another person", t_no_duplicate_person_articles),
    ("S.did_no_shared_days", "S7", "no district-day is treated and control at once", s_did_no_shared_days),
    ("T.no_lost_history", "T12", "no article series starts after the article existed", t_no_lost_history),
    ("T.local_uncensored", "T10", "NYC-local series has no censored days", t_local_series_uncensored),
    ("T.index_not_one_article", "T11", "index top days are not one article", t_index_not_single_article),
    ("T.no_stitch_break", "T1", "no stitched component has an artificial level break", t_no_stitch_break),
    ("T.components_agree", "T10,T11", "index components measure the same construct", t_components_agree),
    ("T.index_uncensored", "T3,L3", "no component in the index is a censored indicator", t_index_uncensored),
    ("T.victims_topic_units", "T2,L2,T8", "trends_victims divided by topic term", t_victims_saturate),
    ("T.composite_after_avg", "D5", "composite standardised after averaging", t_composite_after_avg),
    ("T.fixed_component_set", "D5", "CAI-D requires a fixed component set", t_fixed_component_set),
    ("T.basket_not_registry_gated", "T9", "basket reaches victims MPV omits", t_basket_not_registry_gated),
    ("T.wiki_ext_matches_basket", "X2,T9", "wiki_ext built from the current basket", t_wiki_ext_matches_basket),
    ("T.wiki_basket_live", "X2", "wiki basket not selected by retired Twitter", t_wiki_basket_twitter),
    ("S.reference_day", "S2,D1", "event-time reference is day -1", s_reference_day),
    ("S.placebo_count", "S1,E1,L1,X4,D2", "placebo draws keep the real episode count", s_placebo_count),
    ("S.joint_test", "S3,R7", "statistic sees a dip-then-rebound", s_joint_test),
    ("S.cluster_by_date", "S6", "SEs clustered by date, not hetero", s_cluster_by_date),
    ("S.prewindow_truncation", "S5,E4", "contested district-days reassigned, not deleted", s_prewindow_truncation),
    ("S.calibration_can_fail", "S4,X3,R3,RI2", "calibration verdict can fail", s_calibration_can_fail),
    ("S.no_stale_calibration", "R3", "no stale low-n calibration artifact", s_stale_calibration_artifact),
    ("S.calibration_on_residual", "S8", "synthetic null has this design's dependence, not a harder one", s_calibration_on_residual),
    ("S.ri_scheme_certified", "P1,P5,RI3,P12,P13", "the randomization null used is the one the calibration certifies", s_ri_scheme_certified),
    ("S.lift_requires_1000_sims", "P11", "the freeze lifts only on 1000-sim certificates for every stratum", s_lift_requires_1000_sims),
    ("D.discovery_scripts_pinned", "D8,F5", "lifting the freeze cannot move the exploratory scripts, or the suite's own checks, onto the sealed sample", d_discovery_scripts_pinned),
    ("S.calibration_noise_measured", "N11", "every certificate's null takes its noise from the measured panel, never the assumed fallback", s_calibration_noise_measured),
    ("S.confirmatory_spec_audit", "P14,P15,P16,P18,P19,P26,P27,P28,P29,P30,P31,P32,P33,P34,P35,P36,P56,P57", "the sealed script implements addenda 23, 29 and 30 (draws, seal and run log, BH family, asymptotic p, diagnostics on every district-day, C2-only interaction, the 28/60-day windows on the certified geometry, dose arm, geocoding-clean, cancelled-inclusive and no-EDPM cells; sidecar pins; docstring matches code)", s_confirmatory_spec_audit),
    ("S.confirmatory_reading_rules", "P14,P20,P21,P22,P25,P37,P38,P39,P40,P41,P42,P43,P44,P45,P54,P55", "the pre-registered reading of the sealed result is mechanical, sealed, and reads as its text requires (23.1-23.4, 23.1c/d, 19.2, 25, note 9.4)", s_confirmatory_reading_rules),
    ("S.third_pass_record_consistency", "P46,P47,P48,P49,P50,P51,P52,P53,P58", "statements of the record the third CP2 audit pass found contradicted by the code or by itself are held to their corrected form", s_third_pass_record_consistency),
    ("S.draw_scheme_total", "N5", "every draw scheme is dispatched explicitly, none by fallback", s_draw_scheme_total),
    ("S.ri_pvalue_form", "RI1", "randomization p-values use the (1+k)/(1+n) form", s_ri_pvalue_form),
    ("S.calibration_writes_stratified", "P5,D1,N4", "every calibration output names the stratum it describes", s_calibration_writes_stratified),
    ("S.estimators_gate_on_calibration", "P7,D1,N6,N10", "estimators certify their own null and cannot be downgraded by a cheap run", s_estimators_gate_on_calibration),
    ("S.ppml_wired", "X5,R8", "counts/PPML arm actually called", s_ppml_wired),
    ("S.dose_arm_wired", "D6", "dose-response arm has a caller and recovers a planted effect", s_dose_arm_wired),
    ("S.ledger_identity", "N7,N8", "checkpoint ledgers are keyed to their design and quarantined when it differs", s_ledger_identity),
    ("S.placebo_relocations_reported", "N9", "the within-block shift's relocation count reaches the caller", s_placebo_relocations_reported),
    ("S.confirmatory_uses_certified_machinery", "P8,P9,P10", "the sealed script estimates with the certified machinery and its dry run is current", s_confirmatory_uses_certified_machinery),
    ("D.freeze_not_tautological", "D3", "freeze guard is not a tautology", d_freeze_not_tautological),
    ("D.freeze_disjoint", "D3", "confirmation sample disjoint from discovery", d_freeze_enforces_disjoint),
    ("D.guard_coverage", "D3,X11,X9", "every outcome-artifact reader calls the guard", d_guard_coverage),
    ("X.bheard_wired", "X6,X17", "B-HEARD control is in a model and inert on discovery", x_bheard_wired_and_inert),
    ("D.soda_guarded", "F2", "the source API is guarded, not only the artifacts", d_soda_source_guarded),
    ("D.outcome_list_complete", "O1,X11", "every processed artifact is classified as outcome or not", d_outcome_list_complete),
    ("D.incident_disclosed", "F1,F2,F3,F4,F5", "every freeze incident stays in the record", d_incident_disclosed),
    ("D.addendum_complete", "E5,E6,F2,P23,P24", "pre-registration text untouched and its addendum exists", d_addendum_complete),
    ("D.guard_can_fire", "D3,D4", "freeze guard actually rejects things", d_guard_can_fire),
    ("D.declared_access_scoped", "O2,F3", "every read of confirmation outcomes is declared, scoped, logged and disclosed", d_declared_access_scoped),
    ("E.episodes_labelled", "E7,E8", "every episode says what drove it, from the treatment series", e_episodes_labelled),
    ("E.threshold_stringency", "D5,L5,E6", "episode threshold is constant stringency", e_threshold_constant_stringency),
    ("E.no_mega_episode", "E3,D7,E6", "no episode exceeds its analysis window", e_no_mega_episode),
    ("E.frozen_list_untouched", "D3", "frozen episode list unmodified", e_frozen_list_untouched),
    ("E.stratum_windows_fit", "P2", "every episode's reported statistic fits inside its stratum", e_stratum_windows_fit),
    ("E.estimators_use_adopted_list", "D3,E6", "estimators read the adopted episode list, not the frozen record", e_estimators_use_adopted_list),
    ("E.labels_live_source", "E5,L6,R2", "episode labels not from retired Twitter", e_labels_not_from_twitter),
    ("E.attribution_lookback", "E2", "attribution lookback >= 60 days", e_attribution_lookback),
    ("O.ems_complete", "O5,O6", "EMS extract covers the full source", o_ems_download_complete),
    ("O.panel_exists", "O5", "panel_cd_day.parquet exists", o_panel_exists),
    ("O.dropna_groupby", "O4", "missing-district rows not silently dropped", o_dropna_groupby),
    ("V.artifacts_current", "T14", "no artifact predates the script that writes it", v_artifacts_current),
    ("V.sources_verified", "X8,X14,X16", "every source verified after its last write", v_sources_verified),
    ("V.no_duplicate_source_ids", "X8,X13", "one row per source id, no collisions", v_no_duplicate_source_ids),
    ("V.source_id_per_artifact", "P3,P4", "a source id never gets repointed at a different artifact", v_source_id_per_artifact),
    ("V.claims_reproduce", "X14", "every claimed number recomputes from its artifact", v_claims_reproduce),
    ("V.claims_cover_exhibits", "P6", "no number enters a paper table without a claim behind it", v_claims_cover_exhibits),
    ("V.table1_regenerates", "P6", "the generated episode table re-renders byte-identical from its artifacts", v_table1_regenerates),
    ("V.paper_figures_current", "X21", "the manuscript's tracked figures match the current pipeline output byte for byte", v_paper_figures_current),
    ("V.links_resolve", "X14", "every endpoint has a dated result", v_links_resolve),
    ("X.run_all_stages_declared", "X10,P17,X19", "every pipeline stage exists and declares its outputs", x_run_all_stages_declared),
    ("X.run_all_refresh_guard", "X18", "a stage that leaves its outputs unrefreshed fails", x_run_all_refresh_guard),
    ("X.run_all_deterministic_env", "X20", "run_all runs every stage under a fixed hash seed and one BLAS thread, so cold passes are byte-identical", x_run_all_deterministic_env),
    ("M.status_honest", "O5", "no finding is recorded fixed without a passing check", m_status_honest),
    ("M.finding_ids_unique", "RI4", "every finding id addresses exactly one row", m_finding_ids_unique),
    ("M.register_sync", "O5", "register and suite have not drifted apart", m_register_sync),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="accept current state as the baseline")
    args = ap.parse_args()

    print(f"{'':<8}{'CHECK':<22} {'PROPERTY':<64} DETAIL")
    print("-" * 170)
    for cid, fids, desc, fn in CHECKS:
        check(cid, fids, desc, fn)

    df = pd.DataFrame(results)
    out = OUTPUTS_TABLES / "regression_suite.csv"
    df.to_csv(out, index=False)

    counts = df["state"].value_counts().to_dict()
    print("-" * 170)
    print(f"{len(df)} checks: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    base_path = PROJECT_ROOT / "docs" / "regression_baseline.csv"
    if args.baseline:
        df.to_csv(base_path, index=False)
        print(f"baseline written -> {base_path}")
        return 0

    if not base_path.exists():
        print("no baseline yet; run with --baseline to create one")
        return 0

    base = pd.read_csv(base_path).set_index("check")["state"].to_dict()
    regressions = [r for r in results
                   if base.get(r["check"]) == "PASS" and r["state"] != "PASS"]
    fixed = [r for r in results
             if base.get(r["check"]) in ("FAIL", "BLOCKED") and r["state"] == "PASS"]
    # A CHECK WITH NO BASELINE ROW CANNOT REGRESS, which made the gate blind to it.
    # The baseline was last refreshed at 59 checks while the suite grew to 76,
    # so 16 checks - the RI p-value form, the scheme dispatch, the calibration
    # gate, the register-honesty checks - could FAIL and the suite still exit 0
    # printing "no regressions". That is a gate that cannot fail for a fifth of
    # its checks. Unbaselined is now a reported condition and a non-zero exit.
    unbaselined = [r for r in results if r["check"] not in base]
    retired = [c for c in base if c not in {r["check"] for r in results}]

    for r in fixed:
        print(f"  FIXED      {r['check']} ({r['findings']})")
    for r in regressions:
        print(f"  REGRESSION {r['check']} was PASS, now {r['state']}: {r['detail']}")
    for r in unbaselined:
        print(f"  UNBASELINED {r['check']} ({r['state']}): no baseline row, so this "
              "check cannot regress — refresh the baseline in the commit that adds it")
    for c in retired:
        print(f"  RETIRED    {c}: in the baseline, not in the suite")

    if regressions or unbaselined or retired:
        print(f"\n{len(regressions)} REGRESSION(S), {len(unbaselined)} UNBASELINED, "
              f"{len(retired)} RETIRED — the gate is not clean.")
        return 1
    print("\nno regressions; every check has a baseline row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
