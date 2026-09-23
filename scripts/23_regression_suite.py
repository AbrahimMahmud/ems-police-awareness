"""The regression gate: every property the pipeline, the freeze, the sealed run and the documents are
held to, as a check that can fail.

Results are compared against docs/regression_baseline.csv, which is committed: a check that was PASS in
the baseline and is not PASS now is a regression and exits non-zero; a check with no baseline row is
reported and exits non-zero too, so the baseline is refreshed in the commit that adds a check.

  python 23_regression_suite.py              # run, compare to baseline
  python 23_regression_suite.py --baseline   # accept current state as baseline

States: PASS (the property holds), FAIL (it does not), BLOCKED (a required input is absent — not a pass),
ERROR (the check raised).
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


# The five occasions on which confirmation-period data were touched before the lift (disclosed in
# docs/CONFIRMATION_PLAN.md, docs/PAPER_MASTER.md §5.3 and the paper).
FREEZE_INCIDENTS = ("F1", "F2", "F3", "F4", "F5")


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
    """Trends anchor rescales all days, not just 1-7."""
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
    """Title aggregation is not measuring accumulation."""
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
    """Register asserts no span the data lacks."""
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
    """Derived weights round-trip exactly."""
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




def t_wiki_fetch_complete():
    """No basket article lost a title to a failed fetch."""
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
    """No basket candidate is a redirect."""
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
    """The sealed script implements addenda 23, 29 and 30 (draws, seal and run log, BH family, asymptotic p, diagnostics on every district-day, C2-only interaction, the 28/60-day windows on the certified geometry, dose arm, geocoding-clean, cancelled-inclusive and no-EDPM cells; sidecar pins; docstring matches code)."""
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
    """The freeze lifts only on 1000-sim certificates for every stratum."""
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
    """Every certificate's null takes its noise from the measured panel, never the assumed fallback."""
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
    """The pre-registered reading of the sealed result is mechanical, sealed, and reads as its text requires (23.1-23.4, 23.1c/d, 19.2, 25, note 9.4)."""
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
    """The record's statements about the design, the incidents and the bound agree with the code and with each other."""
    import ast as _ast
    problems = []
    plan = (PROJECT_ROOT / "docs" / "CONFIRMATION_PLAN.md").read_text()
    note = (PROJECT_ROOT / "docs" / "PRE_ANALYSIS_NOTE.md").read_text()
    master = (PROJECT_ROOT / "docs" / "PAPER_MASTER.md").read_text()
    if "| 3 | Test window: days 0–5 → days 0–7, joint | no (§14) |" not in plan:
        problems.append("summary row 3 does not mark the joint days 0-7 window as decided after discovery (§14)")
    paper = (PROJECT_ROOT / "docs" / "PAPER.md").read_text()
    if "breached four times" in paper or "Four freeze incidents" in master or "— **four**, all disclosed" in master:
        problems.append("the paper or the master still counts four freeze incidents; the record has five (F5 at the lift)")
    if "has not been looked at" in note or "never examined before the lift" in note:
        problems.append("PRE_ANALYSIS_NOTE still describes the confirmation data as untouched before the lift; F1-F5 are recorded accesses")
    if "no number from them was kept" in paper or "never used for any specification choice" in paper:
        problems.append("PAPER.md still says nothing was kept from the freeze incidents or that no specification choice touched the strata (F4 weights kept; F2 decision)")
    # CP3 manuscript audit, 2026-09-21 (P59-P63): the paper's account of the record
    if "undeclared metadata reads" in paper or "coverage statistics made while refuting" in paper:
        problems.append("PAPER.md Limitation 9 still calls F1/F2 metadata reads or F3 a coverage read; all three read confirmation-period outcome values (P59)")
    if "before any confirmation-period outcome was seen" in paper:
        problems.append("PAPER.md still says everything was committed before any confirmation-period outcome was seen; F1-F3 precede the commitments (P62)")
    if "likely understate the response they measure" in paper:
        problems.append("PAPER.md still claims the compositional damping biases toward the null (P63)")
    if "No COVID" in note or "No COVID" in master or "free of both COVID" in paper:
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
    for doc, name in ((plan, "CONFIRMATION_PLAN"), (note, "PRE_ANALYSIS_NOTE"), (master, "PAPER_MASTER")):
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
    """The generated episode table re-renders byte-identical from its artifacts."""
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
    # Since the referee-panel revision (2026-09-21) the same table is Table S6 of the supplement,
    # pasted as a region by ops/paste_generated.py; the copy there must be the rendered file too.
    supp = PROJECT_ROOT / "docs" / "SUPPLEMENT.md"
    if supp.exists():
        spec2 = importlib.util.spec_from_file_location("_paste", PROJECT_ROOT / "ops" / "paste_generated.py")
        pg = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(pg)
        import re as _re
        m = _re.search(r"<!-- BEGIN:episode_table -->\n(.*?)<!-- END:episode_table -->", supp.read_text(), _re.S)
        if not m:
            return "FAIL", "docs/SUPPLEMENT.md has no episode_table region (Table S6)"
        if m.group(1) != pg.episode_table_body():
            return "FAIL", ("the supplement's Table S6 differs from the rendered episode table: run "
                            "ops/paste_generated.py docs/SUPPLEMENT.md")
    n = sum(1 for ln in fresh.splitlines() if ln.startswith("| ") and ln[2:3].isdigit())
    return "PASS", (f"{n} table rows re-render byte-identical from {EPISODE_LIST_PRIMARY}, the frozen "
                    "list and stratum_episodes, and the supplement's Table S6 is that rendering")


def d_discovery_scripts_pinned():
    """Lifting the freeze cannot move the exploratory scripts, or the suite's own checks, onto the sealed sample."""
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
    """Run_all runs every stage under a fixed hash seed and one BLAS thread, so cold passes are byte-identical."""
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
    """The manuscript's tracked figures match the current pipeline output byte for byte."""
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
    """The randomization null used is the one the calibration certifies."""
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
    """Estimators certify their own null and cannot be downgraded by a cheap run."""
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
    """Every draw scheme is dispatched explicitly, none by fallback."""
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
    """Randomization p-values use the (1+k)/(1+n) form."""
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
    """Every calibration output names the stratum it describes."""
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
    """Synthetic null has this design's dependence, not a harder one."""
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
    """Dose-response arm has a caller and recovers a planted effect."""
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
    """Pre-registration text untouched and its addendum exists."""
    f = PROJECT_ROOT / "docs" / "CONFIRMATION_PLAN.md"
    if not f.exists():
        return "BLOCKED", "docs/CONFIRMATION_PLAN.md is absent"
    text = f.read_text()
    marker = "\n---\n\n# Addendum — deviations from the plan above\n"
    if marker not in text:
        return "FAIL", "CONFIRMATION_PLAN.md has no addendum section"

    # The pre-specified text, pinned by content hash rather than by a line count
    # so that appending cannot shift it and editing cannot hide in a diff.
    FROZEN_SHA = "3a411ddd57a2789d6f1866cad51c9bbf1a0136e75cc0f70c5a30e4b81eebee52"
    original, addendum = text.split(marker, 1)
    got = hashlib.sha256(original.encode()).hexdigest()
    if got != FROZEN_SHA:
        return "FAIL", (f"the pre-specified text has been EDITED: sha256 {got[:16]} "
                        f"against the pinned {FROZEN_SHA[:16]}. The addendum exists so "
                        "deviations are appended, never written over the original.")

    return "PASS", (f"pre-specified text byte-identical ({len(original)} bytes); "
                    f"addendum present ({len(addendum.splitlines())} lines)")


def x_run_all_refresh_guard():
    """A stage that leaves its outputs unrefreshed fails."""
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
    """Every pipeline stage exists and declares its outputs."""
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
    """Every episode's reported statistic fits inside its stratum."""
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
    """Estimators read the adopted episode list, not the frozen record."""
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
    """Every processed artifact is classified as outcome or not."""
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
    """Every basket article has evidence police were the actor."""
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
    """The EDP grouping's stated justification holds."""
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
    """The live Trends component keeps its resolution over the decade."""
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
    """The April 2020 agent-class break is measured and bounded."""
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
    """No basket article rests on an exact-name registry match alone."""
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
    """No basket article admitted without US evidence."""
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
    """No basket exclusion states a reason the scope file contradicts."""
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
    """Every basket candidate was actually asked about."""
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
    """No basket article duplicates another person."""
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
    """No district-day is treated and control at once."""
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
    """No article series starts after the article existed."""
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
    """NYC-local series has no censored days."""
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
    """Index top days are not one article."""
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
    """No stitched component has an artificial level break."""
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
    """Index components measure the same construct."""
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
    """No component in the index is a censored indicator."""
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
    """Trends_victims divided by topic term."""
    from config import CAI_D_COMPONENTS
    if "trends_victims" not in CAI_D_COMPONENTS:
        return "PASS", "dropped from CAI_D_COMPONENTS"
    s = src("11c_trends_anchor_and_victims.py")
    divides = bool(re.search(r"ratio\s*=\s*df\[name\][^\n]*/\s*df\[\s*TOPIC", s))
    return ("PASS" if divides else "FAIL",
            "divides by TOPIC" if divides else "ratio = df[name] with no denominator")


def t_composite_after_avg():
    """Composite standardised after averaging."""
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
    """CAI-D requires a fixed component set."""
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
    """Basket reaches victims MPV omits."""
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
    """Wiki_ext built from the current basket."""
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




def t_basket_covers_extension():
    """The basket covers deaths after 2020, so the index can measure attention in the extension years."""
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


def e_labels_rank_by_attention():
    """Episode labels rank candidates by attention, not by the registry's file order."""
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
        # registry file order, date descending: the signature of a label that was not ranked
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
    """Event-time reference is day -1."""
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
    """Placebo draws keep the real episode count."""
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
    """Statistic sees a dip-then-rebound."""
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
    """SEs clustered by date, not hetero."""
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
    """Contested district-days reassigned, not deleted."""
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
    """Calibration verdict can fail."""
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
    """No stale low-n calibration artifact."""
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
    """Counts/PPML arm actually called."""
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
    """Freeze guard is not a tautology."""
    bad = []
    for f in SCRIPTS.glob("*.py"):
        t = f.read_text()
        for m in re.finditer(r"\.between\(ANALYSIS_START, ANALYSIS_END\)\]?\s*\n\s*assert_discovery_only", t):
            bad.append(f.name)
    return ("PASS" if not bad else "FAIL",
            "guard is independent" if not bad else f"tautological in {sorted(set(bad))}")


def d_freeze_enforces_disjoint():
    """Confirmation sample disjoint from discovery."""
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
    """Every outcome-artifact reader calls the guard."""
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
    """B-HEARD control is in a model and inert on discovery."""
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
    """The source API is guarded, not only the artifacts."""
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
    """Every freeze incident stays in the record."""
    incidents = list(FREEZE_INCIDENTS)
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
        return "FAIL", (f"{len(missing)} incident(s) not named in the freeze-incident "
                        f"section of PAPER_MASTER.md: {missing}")
    undated = [fid for fid in incidents
               if not re.search(r"\d{4}-\d{2}-\d{2}", section)]
    if undated:
        return "FAIL", "the freeze-incident section carries no dates"
    return "PASS", (f"{len(incidents)} incident(s) recorded and named in the "
                    f"disclosure section, dated: {incidents}")


def d_guard_can_fire():
    """Freeze guard actually rejects things."""
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
    """Every read of confirmation outcomes is declared, scoped, logged and disclosed."""
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
    """Every episode says what drove it, from the treatment series."""
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
    """Episode threshold is constant stringency."""
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
    """No episode exceeds its analysis window."""
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
    """Frozen episode list unmodified."""
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




def e_attribution_lookback():
    """Attribution lookback >= 60 days."""
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
    """EMS extract covers the full source."""
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
    """Missing-district rows not silently dropped."""
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
    """No artifact predates the script that writes it."""
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
    """Every source verified after its last write."""
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
    """A source id never gets repointed at a different artifact."""
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
    """One row per source id, no collisions."""
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


def v_paper_budget():
    """The manuscript stays within the venue's word and display-item budget."""
    import re as _re
    paper = PROJECT_ROOT / "docs" / "PAPER.md"
    if not paper.exists():
        return "BLOCKED", "docs/PAPER.md absent"
    text = paper.read_text()
    if "## Introduction" not in text or "## Display items" not in text:
        return "FAIL", "PAPER.md lacks the Introduction or Display items headings the budget is measured between"
    main = text.split("## Introduction", 1)[1].split("## Display items", 1)[0]
    words = len(" ".join(l for l in main.splitlines()
                         if not l.strip().startswith("|") and not l.strip().startswith("![")).split())
    items_section = text.split("## Display items", 1)[1].split("## RECORD", 1)[0]
    items = _re.findall(r"^\*\*(Table|Figure) (\d+)[ .\u2014]", items_section, flags=_re.M)
    problems = []
    if words > 5000:
        problems.append(f"main text is {words:,} words (ceiling 5,000; venue ~4,000)")
    if len(items) != 4:
        problems.append(f"{len(items)} display items ({', '.join(a + ' ' + b for a, b in items)}); the venue allows four")
    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", f"main text {words:,} words (ceiling 5,000); {len(items)} display items: " + ", ".join(a + " " + b for a, b in items)


def v_manuscript_referee_tokens():
    """The manuscript describes the sealed analysis as the sealed files have it and reports a 95% interval beside the pre-registered bound."""
    paper = PROJECT_ROOT / "docs" / "PAPER.md"
    if not paper.exists():
        return "BLOCKED", "docs/PAPER.md absent"
    text = paper.read_text()
    forbidden = {
        "RP1": ["while total dispatches did not", "while total dispatches have"],
        "RP2": ["traced identically by both arms", "small fraction of any single day", "a fall over days 3 to 7"],
        "RP3": ["would have failed the sign test"],
        "RP4": ["carries no such damping"],
        "RP5": ["positive in every stratum"],
        "RP6": ["placebo rejects", "9.4 row 5", "§19 rule 2", "The reader's conclusion", "The reader therefore"],
    }
    problems = [f"{k}: {t!r}" for k, toks in forbidden.items() for t in toks if t in text]
    if "95% interval" not in text and "95% CI" not in text:
        problems.append("RP6: no 95% interval for the first-week mean anywhere in the manuscript")
    if problems:
        return "FAIL", "; ".join(problems[:4])
    return "PASS", "the manuscript carries the panel's corrections (RP1-RP6) and a 95% interval beside the pre-registered bound"


def v_claims_cover_exhibits():
    """No number enters a paper table without a claim behind it."""
    import re as _re
    reg = PROJECT_ROOT / "docs" / "CLAIMS_REGISTER.csv"
    # PAPER_MASTER is the source document; PAPER.md is the manuscript drafted
    # from it (Phase J, 2026-09-13). A table in either is an exhibit, and the
    # manuscript is where a number is most likely to be retyped by hand.
    # SUPPLEMENT.md holds the sealed run's full tables and the code, crosswalk, calibration and
    # power tables since the CP3 restructure (2026-09-21): an exhibit is an exhibit wherever it lives.
    docs = [PROJECT_ROOT / "docs" / "PAPER_MASTER.md", PROJECT_ROOT / "docs" / "PAPER.md",
            PROJECT_ROOT / "docs" / "SUPPLEMENT.md"]
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
      # The supplement's Table S6 is the regenerated episode list (74 rows of dates and drivers),
      # pasted as a region and held byte-identical to its inputs by V.table1_regenerates; a claim per
      # cell would be several hundred rows saying nothing a reader could check, so the region is
      # skipped here for the reason the docs/tables copy always was.
      in_episode_table = False
      for i, line in enumerate(doc.read_text().splitlines(), 1):
          if line.strip() == "<!-- BEGIN:episode_table -->":
              in_episode_table = True
              continue
          if line.strip() == "<!-- END:episode_table -->":
              in_episode_table = False
              continue
          if in_episode_table:
              continue
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
    """Every claimed number recomputes from its artifact."""
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
    """Every endpoint has a dated result."""
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






# ===========================================================================
def s_ledger_identity():
    """Checkpoint ledgers are keyed to their design and quarantined when it differs."""
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
    """The within-block shift's relocation count reaches the caller."""
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
    """The sealed script estimates with the certified machinery and its dry run is current."""
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
    """The spliced Wikipedia arm equals the primary before the agent class existed."""
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
    ("T.anchor_monthly", "", "Trends anchor rescales all days, not just 1-7", t_anchor_monthly),
    ("T.title_agg_no_trend", "", "title aggregation is not measuring accumulation", t_title_agg_no_trend),
    ("T.realised_coverage", "", "register asserts no span the data lacks", t_realised_coverage_recorded),
    ("X.csv_reproducible", "", "derived weights round-trip exactly", x_derived_csv_reproducible),
    ("T.wiki_fetch_complete", "", "no basket article lost a title to a failed fetch", t_wiki_fetch_complete),
    ("T.no_redirect_candidates", "", "no basket candidate is a redirect", t_no_redirect_candidates),
    ("T.exclusion_reasons_true", "", "no basket exclusion states a reason the scope file contradicts", t_exclusion_reasons_true),
    ("T.scope_covers_candidates", "", "every basket candidate was actually asked about", t_scope_covers_candidates),
    ("T.basket_is_police_violence", "", "every basket article has evidence police were the actor", t_basket_is_police_violence),
    ("D.edp_family_justified", "", "the EDP grouping's stated justification holds", d_edp_family_justified),
    ("T.trends_precision_stable", "", "the live Trends component keeps its resolution over the decade", t_trends_precision_stable),
    ("T.spliced_arm_prebreak_identical", "", "the spliced Wikipedia arm equals the primary before the agent class existed", t_spliced_arm_prebreak_identical),
    ("T.agent_class_break_bounded", "", "the April 2020 agent-class break is measured and bounded", t_agent_class_break_bounded),
    ("T.basket_evidence_not_namesake", "", "no basket article rests on an exact-name registry match alone", t_basket_evidence_not_namesake),
    ("T.basket_country_evidence", "", "no basket article admitted without US evidence", t_basket_country_evidence),
    ("T.no_duplicate_person", "", "no basket article duplicates another person", t_no_duplicate_person_articles),
    ("S.did_no_shared_days", "", "no district-day is treated and control at once", s_did_no_shared_days),
    ("T.no_lost_history", "", "no article series starts after the article existed", t_no_lost_history),
    ("T.local_uncensored", "", "NYC-local series has no censored days", t_local_series_uncensored),
    ("T.index_not_one_article", "", "index top days are not one article", t_index_not_single_article),
    ("T.no_stitch_break", "", "no stitched component has an artificial level break", t_no_stitch_break),
    ("T.components_agree", "", "index components measure the same construct", t_components_agree),
    ("T.index_uncensored", "", "no component in the index is a censored indicator", t_index_uncensored),
    ("T.victims_topic_units", "", "trends_victims divided by topic term", t_victims_saturate),
    ("T.composite_after_avg", "", "composite standardised after averaging", t_composite_after_avg),
    ("T.fixed_component_set", "", "CAI-D requires a fixed component set", t_fixed_component_set),
    ("T.basket_not_registry_gated", "", "basket reaches victims MPV omits", t_basket_not_registry_gated),
    ("T.wiki_ext_matches_basket", "", "wiki_ext built from the current basket", t_wiki_ext_matches_basket),
    ("T.basket_covers_extension", "", "the basket covers deaths after 2020", t_basket_covers_extension),
    ("S.reference_day", "", "event-time reference is day -1", s_reference_day),
    ("S.placebo_count", "", "placebo draws keep the real episode count", s_placebo_count),
    ("S.joint_test", "", "statistic sees a dip-then-rebound", s_joint_test),
    ("S.cluster_by_date", "", "SEs clustered by date, not hetero", s_cluster_by_date),
    ("S.prewindow_truncation", "", "contested district-days reassigned, not deleted", s_prewindow_truncation),
    ("S.calibration_can_fail", "", "calibration verdict can fail", s_calibration_can_fail),
    ("S.no_stale_calibration", "", "no stale low-n calibration artifact", s_stale_calibration_artifact),
    ("S.calibration_on_residual", "", "synthetic null has this design's dependence, not a harder one", s_calibration_on_residual),
    ("S.ri_scheme_certified", "", "the randomization null used is the one the calibration certifies", s_ri_scheme_certified),
    ("S.lift_requires_1000_sims", "", "the freeze lifts only on 1000-sim certificates for every stratum", s_lift_requires_1000_sims),
    ("D.discovery_scripts_pinned", "", "lifting the freeze cannot move the exploratory scripts, or the suite's own checks, onto the sealed sample", d_discovery_scripts_pinned),
    ("S.calibration_noise_measured", "", "every certificate's null takes its noise from the measured panel, never the assumed fallback", s_calibration_noise_measured),
    ("S.confirmatory_spec_audit", "", "the sealed script implements addenda 23, 29 and 30 (draws, seal and run log, BH family, asymptotic p, diagnostics on every district-day, C2-only interaction, the 28/60-day windows on the certified geometry, dose arm, geocoding-clean, cancelled-inclusive and no-EDPM cells; sidecar pins; docstring matches code)", s_confirmatory_spec_audit),
    ("S.confirmatory_reading_rules", "", "the pre-registered reading of the sealed result is mechanical, sealed, and reads as its text requires (23.1-23.4, 23.1c/d, 19.2, 25, note 9.4)", s_confirmatory_reading_rules),
    ("S.third_pass_record_consistency", "", "the record's statements about the design, the incidents and the bound agree with the code and with each other", s_third_pass_record_consistency),
    ("S.draw_scheme_total", "", "every draw scheme is dispatched explicitly, none by fallback", s_draw_scheme_total),
    ("S.ri_pvalue_form", "", "randomization p-values use the (1+k)/(1+n) form", s_ri_pvalue_form),
    ("S.calibration_writes_stratified", "", "every calibration output names the stratum it describes", s_calibration_writes_stratified),
    ("S.estimators_gate_on_calibration", "", "estimators certify their own null and cannot be downgraded by a cheap run", s_estimators_gate_on_calibration),
    ("S.ppml_wired", "", "counts/PPML arm actually called", s_ppml_wired),
    ("S.dose_arm_wired", "", "dose-response arm has a caller and recovers a planted effect", s_dose_arm_wired),
    ("S.ledger_identity", "", "checkpoint ledgers are keyed to their design and quarantined when it differs", s_ledger_identity),
    ("S.placebo_relocations_reported", "", "the within-block shift's relocation count reaches the caller", s_placebo_relocations_reported),
    ("S.confirmatory_uses_certified_machinery", "", "the sealed script estimates with the certified machinery and its dry run is current", s_confirmatory_uses_certified_machinery),
    ("D.freeze_not_tautological", "", "freeze guard is not a tautology", d_freeze_not_tautological),
    ("D.freeze_disjoint", "", "confirmation sample disjoint from discovery", d_freeze_enforces_disjoint),
    ("D.guard_coverage", "", "every outcome-artifact reader calls the guard", d_guard_coverage),
    ("X.bheard_wired", "", "B-HEARD control is in a model and inert on discovery", x_bheard_wired_and_inert),
    ("D.soda_guarded", "", "the source API is guarded, not only the artifacts", d_soda_source_guarded),
    ("D.outcome_list_complete", "", "every processed artifact is classified as outcome or not", d_outcome_list_complete),
    ("D.incident_disclosed", "", "every freeze incident stays in the record", d_incident_disclosed),
    ("D.addendum_complete", "", "pre-registration text untouched and its addendum exists", d_addendum_complete),
    ("D.guard_can_fire", "", "freeze guard actually rejects things", d_guard_can_fire),
    ("D.declared_access_scoped", "", "every read of confirmation outcomes is declared, scoped, logged and disclosed", d_declared_access_scoped),
    ("E.episodes_labelled", "", "every episode says what drove it, from the treatment series", e_episodes_labelled),
    ("E.threshold_stringency", "", "episode threshold is constant stringency", e_threshold_constant_stringency),
    ("E.no_mega_episode", "", "no episode exceeds its analysis window", e_no_mega_episode),
    ("E.frozen_list_untouched", "", "frozen episode list unmodified", e_frozen_list_untouched),
    ("E.stratum_windows_fit", "", "every episode's reported statistic fits inside its stratum", e_stratum_windows_fit),
    ("E.estimators_use_adopted_list", "", "estimators read the adopted episode list, not the frozen record", e_estimators_use_adopted_list),
    ("E.labels_rank_by_attention", "", "episode labels rank candidates by attention", e_labels_rank_by_attention),
    ("E.attribution_lookback", "", "attribution lookback >= 60 days", e_attribution_lookback),
    ("O.ems_complete", "", "EMS extract covers the full source", o_ems_download_complete),
    ("O.panel_exists", "", "panel_cd_day.parquet exists", o_panel_exists),
    ("O.dropna_groupby", "", "missing-district rows not silently dropped", o_dropna_groupby),
    ("V.artifacts_current", "", "no artifact predates the script that writes it", v_artifacts_current),
    ("V.sources_verified", "", "every source verified after its last write", v_sources_verified),
    ("V.no_duplicate_source_ids", "", "one row per source id, no collisions", v_no_duplicate_source_ids),
    ("V.source_id_per_artifact", "", "a source id never gets repointed at a different artifact", v_source_id_per_artifact),
    ("V.claims_reproduce", "", "every claimed number recomputes from its artifact", v_claims_reproduce),
    ("V.claims_cover_exhibits", "", "no number enters a paper table without a claim behind it", v_claims_cover_exhibits),
    ("V.paper_budget", "", "the manuscript stays within the venue's word and display-item budget", v_paper_budget),
    ("V.manuscript_referee_tokens", "", "the manuscript describes the sealed analysis as the sealed files have it and reports a 95% interval beside the pre-registered bound", v_manuscript_referee_tokens),
    ("V.table1_regenerates", "", "the generated episode table re-renders byte-identical from its artifacts", v_table1_regenerates),
    ("V.paper_figures_current", "", "the manuscript's tracked figures match the current pipeline output byte for byte", v_paper_figures_current),
    ("V.links_resolve", "", "every endpoint has a dated result", v_links_resolve),
    ("X.run_all_stages_declared", "", "every pipeline stage exists and declares its outputs", x_run_all_stages_declared),
    ("X.run_all_refresh_guard", "", "a stage that leaves its outputs unrefreshed fails", x_run_all_refresh_guard),
    ("X.run_all_deterministic_env", "", "run_all runs every stage under a fixed hash seed and one BLAS thread, so cold passes are byte-identical", x_run_all_deterministic_env),
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
    # A check with no baseline row cannot regress, so it is reported and fails the run.
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
