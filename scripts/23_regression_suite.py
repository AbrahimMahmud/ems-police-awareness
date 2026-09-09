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
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
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
    """X1/T4: the 'weekly' anchor is monthly, so only days 1-7 are rescaled."""
    st = pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])
    an = pd.read_csv(DATA_REFERENCE / "cai_trends_anchored.csv", parse_dates=["date"])
    s = st[st.component == "trends_us"].set_index("date")["value"]
    a = an[an.component == "trends_us"].set_index("date")["value"]
    j = pd.concat([s.rename("s"), a.rename("a")], axis=1).dropna()
    j = j[j.s > 0]
    late = j[j.index.day > 7]
    ratio_late = (late.a / late.s)
    # defect present when late-month days are EXACTLY unrescaled (ratio == 1)
    untouched = float((ratio_late.sub(1).abs() < 1e-9).mean())
    return ("FAIL" if untouched > 0.99 else "PASS",
            f"{untouched:.1%} of day>7 rows unrescaled (defect if ~100%)")


def t_nyc_break():
    """T1: trends_nyc level break from the scale=1.0 stitching fallback."""
    st = pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])
    n = st[st.component == "trends_nyc"].set_index("date")["value"]
    pre = n.loc["2019-01-01":"2021-05-31"]
    post = n.loc["2021-10-01":"2024-12-31"]
    pre_p, post_p = pre[pre > 0], post[post > 0]
    if not len(pre_p) or not len(post_p):
        return "BLOCKED", "no positive values on one side"
    ratio = post_p.median() / pre_p.median()
    return ("FAIL" if ratio > 2.0 else "PASS",
            f"post/pre median positive = {ratio:.2f}x (defect if >2)")


def t_nyc_censored():
    """T3/L3: trends_nyc is mostly exact zeros, censoring rate drifts hugely."""
    st = pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])
    n = st[st.component == "trends_nyc"].set_index("date")["value"]
    z = (n == 0).groupby(n.index.year).mean()
    overall = float((n == 0).mean())
    spread = float(z.max() - z.min())
    return ("FAIL" if overall > 0.5 or spread > 0.3 else "PASS",
            f"{overall:.0%} zeros overall, by-year spread {spread:.0%}")


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
    """T-const: CAI-D must require a fixed component set, not mean-of-available."""
    s = src("12_build_cai.py")
    requires = "isna().any(axis=1)" in s or "dropna(subset=avail_d" in s
    return ("PASS" if requires else "FAIL",
            "requires all components" if requires else "mean-of-available: SD varies by component count")


def t_wiki_basket_twitter():
    """X2: wiki_ext article basket is selected by retired Twitter volume."""
    res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
    if "tweet_volume" not in res.columns:
        return "PASS", "no tweet_volume column"
    reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])
    killed = reg.groupby("name")["date"].min()
    have = res[res.article.notna()].copy()
    have["killed"] = have["name"].map(killed)
    post2020 = int((have["killed"] > "2020-12-31").sum())
    return ("FAIL" if post2020 == 0 else "PASS",
            f"{post2020} basket victims killed after 2020 (defect if 0)")


# ===========================================================================
# ESTIMATOR — static source checks, runnable now
# ===========================================================================
def s_reference_day():
    """S2/D1: day -1 is deleted, so the omitted category becomes day -14."""
    s = src("event_study.py")
    deletes = 'stack["rel_day"] != EVENT_REFERENCE_DAY' in s
    sets_ref = ("Treatment(reference=" in s) or ("i(rel_day" in s and "ref=" in s)
    return ("PASS" if (sets_ref and not deletes) else "FAIL",
            "reference set explicitly" if sets_ref and not deletes
            else "day -1 dropped from sample; patsy omits the lowest level instead")


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
    """S3/R7: H1 is a joint test; a mean of coefficients is a 1-df contrast."""
    s = src("event_study.py")
    is_mean = "coef().loc[wanted].mean()" in s
    has_wald = "wald" in s.lower() or "chi2" in s.lower() or "f.cdf" in s.lower()
    return ("PASS" if has_wald and not is_mean else "FAIL",
            "joint test" if has_wald and not is_mean else "1-df mean of 8 coefficients")


def s_cluster_by_date():
    """S6: treatment is assigned at date level; hetero vcov is wrong."""
    s = src("event_study.py")
    return ("PASS" if 'vcov="hetero"' not in s and "vcov='hetero'" not in s else "FAIL",
            "clustered" if 'vcov="hetero"' not in s else "vcov=hetero with date-level treatment")


def s_prewindow_truncation():
    """S4: build_stack truncates forward only; collisions delete both copies."""
    s = src("event_study.py")
    back = "prev_end" in s or "max(s - pd.Timedelta" in s or "starts[i - 1]" in s
    return ("PASS" if back else "FAIL",
            "pre-window truncated" if back else "forward-only; both copies deleted on collision")


def s_calibration_can_fail():
    """S4/X3/R3: the calibration verdict must be able to fail."""
    s = src("18_null_calibration.py")
    has_min = "MIN_SIMS" in s or ("n_sims" in s and "raise" in s)
    has_uniform = "kstest" in s or "ks_1samp" in s or "uniform" in s.lower()
    ok = has_min and has_uniform
    return ("PASS" if ok else "FAIL",
            "min-n enforced + uniformity test" if ok
            else "wide binomial band only; passes at any n")


def s_stale_calibration_artifact():
    """R3: the committed PASS artifact came from a 12-sim smoke test."""
    f = OUTPUTS_TABLES / "null_calibration.csv"
    if not f.exists():
        return "PASS", "no stale artifact"
    d = pd.read_csv(f).set_index("metric")["value"].to_dict()
    n = float(d.get("n_sims_completed", 0))
    return ("FAIL" if n < 200 else "PASS", f"artifact has n_sims={n:.0f} (needs >=200)")


def s_ppml_wired():
    """X5/R8: the counts arm is documented but never called."""
    s = src("17_stacked_event_study.py")
    return ("PASS" if "counts=True" in s else "FAIL",
            "counts arm called" if "counts=True" in s else "PPML/offset documented but dead code")


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


def d_guard_coverage():
    """D3: every script reading the panel must call the guard."""
    missing = []
    for f in SCRIPTS.glob("*.py"):
        t = f.read_text()
        if "panel_cd_day.parquet" in t and "assert_discovery_only" not in t:
            missing.append(f.name)
    return ("PASS" if not missing else "FAIL",
            "all covered" if not missing else f"unguarded: {sorted(missing)}")


# ===========================================================================
# EPISODES
# ===========================================================================
def e_threshold_constant_stringency():
    """E/T: a fixed 1.0 threshold is a different quantile every year."""
    f = DATA_PROCESSED / "cai_daily.parquet"
    if not f.exists():
        return "BLOCKED", "cai_daily.parquet absent"
    d = pd.read_parquet(f)
    d["date"] = pd.to_datetime(d["date"])
    d = d.set_index("date")
    q = d.groupby(d.index.year)["cai_d"].apply(lambda s: (s > 1.0).mean())
    spread = float(q.max() - q.min())
    return ("FAIL" if spread > 0.10 else "PASS",
            f"share above threshold ranges {q.min():.1%}-{q.max():.1%} by year")


def e_no_mega_episode():
    """E/T2.4: no episode may exceed the window it is analysed with."""
    f = DATA_REFERENCE / "confirmation_episodes.csv"
    ep = pd.read_csv(f, parse_dates=["start", "end"])
    span = (ep["end"] - ep["start"]).dt.days.max()
    return ("FAIL" if span > 28 else "PASS", f"longest episode {span} days (cap 28)")


def e_labels_not_from_twitter():
    """E/R2/X: episode labels ranked by the retired Twitter volume."""
    s = src("13_extension_episodes.py")
    return ("PASS" if "tweet_volume" not in s else "FAIL",
            "labels from live source" if "tweet_volume" not in s
            else "candidate_events ranked by retired tweet_volume")


def e_attribution_lookback():
    """E2: 14-day lookback is shorter than the death-to-attention lag."""
    s = src("13_extension_episodes.py")
    m = re.search(r"Timedelta\(days=(\d+)\)", s)
    days = int(m.group(1)) if m else 0
    return ("PASS" if days >= 60 else "FAIL", f"lookback {days}d (needs >=60)")


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
# META — the register and the suite must not drift apart
# ===========================================================================
def m_register_sync():
    """Every tag resolves to a finding, and every blocking finding has a check.

    Without this, a finding can be silently dropped from the register or a check
    can be tagged with an ID that no longer exists, and coverage looks fine while
    the defect goes untested. That is the same "couldn't check reads as fine"
    failure the suite exists to prevent, applied to the suite itself.
    """
    reg = pd.read_csv(PROJECT_ROOT / "docs" / "AUDIT_FINDINGS.csv")
    known = set(reg["id"])
    tagged = {f.strip() for _, fids, _, _ in CHECKS for f in fids.split(",")}
    unknown = sorted(tagged - known)
    blocking = set(reg.loc[reg["severity"] == "blocking", "id"])
    uncovered = sorted(blocking - tagged)
    if unknown:
        return "FAIL", f"tags with no finding: {unknown}"
    if uncovered:
        return "FAIL", f"blocking findings with no check: {uncovered}"
    return "PASS", f"{len(tagged)}/{len(known)} findings tagged; all {len(blocking)} blocking covered"


# ===========================================================================
CHECKS = [
    ("T.anchor_monthly", "X1,T4", "Trends anchor rescales all days, not just 1-7", t_anchor_monthly),
    ("T.nyc_break", "T1", "trends_nyc has no artificial level break", t_nyc_break),
    ("T.nyc_censoring", "T3,L3", "trends_nyc is a level, not a censored indicator", t_nyc_censored),
    ("T.victims_topic_units", "T2,L2", "trends_victims divided by topic term", t_victims_saturate),
    ("T.composite_after_avg", "D5", "composite standardised after averaging", t_composite_after_avg),
    ("T.fixed_component_set", "D5", "CAI-D requires a fixed component set", t_fixed_component_set),
    ("T.wiki_basket_live", "X2", "wiki basket not selected by retired Twitter", t_wiki_basket_twitter),
    ("S.reference_day", "S2,D1", "event-time reference is day -1", s_reference_day),
    ("S.placebo_count", "S1,E1,L1,X4,D2", "placebo draws keep the real episode count", s_placebo_count),
    ("S.joint_test", "S3,R7", "H1 uses a joint test, not a 1-df mean", s_joint_test),
    ("S.cluster_by_date", "S6", "SEs clustered by date, not hetero", s_cluster_by_date),
    ("S.prewindow_truncation", "S5,E4", "pre-window truncated at previous episode", s_prewindow_truncation),
    ("S.calibration_can_fail", "S4,X3,R3", "calibration verdict can fail", s_calibration_can_fail),
    ("S.no_stale_calibration", "R3", "no stale low-n calibration artifact", s_stale_calibration_artifact),
    ("S.ppml_wired", "X5,R8", "counts/PPML arm actually called", s_ppml_wired),
    ("D.freeze_not_tautological", "D3", "freeze guard is not a tautology", d_freeze_not_tautological),
    ("D.freeze_disjoint", "D3", "confirmation sample disjoint from discovery", d_freeze_enforces_disjoint),
    ("D.guard_coverage", "D3", "every panel reader calls the guard", d_guard_coverage),
    ("E.threshold_stringency", "D5,L5", "episode threshold is constant stringency", e_threshold_constant_stringency),
    ("E.no_mega_episode", "E3,D7", "no episode exceeds its analysis window", e_no_mega_episode),
    ("E.labels_live_source", "E5,L6,R2", "episode labels not from retired Twitter", e_labels_not_from_twitter),
    ("E.attribution_lookback", "E2", "attribution lookback >= 60 days", e_attribution_lookback),
    ("O.ems_complete", "O5", "EMS extract covers the full source", o_ems_download_complete),
    ("O.panel_exists", "O5", "panel_cd_day.parquet exists", o_panel_exists),
    ("O.dropna_groupby", "O4", "missing-district rows not silently dropped", o_dropna_groupby),
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

    for r in fixed:
        print(f"  FIXED      {r['check']} ({r['findings']})")
    for r in regressions:
        print(f"  REGRESSION {r['check']} was PASS, now {r['state']}: {r['detail']}")

    if regressions:
        print(f"\n{len(regressions)} REGRESSION(S) — a change broke something that previously held.")
        return 1
    print("\nno regressions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
