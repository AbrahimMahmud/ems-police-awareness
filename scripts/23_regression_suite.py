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
    """S4/X3/R3: the calibration verdict must be able to fail."""
    s = src("18_null_calibration.py")
    has_min = "MIN_SIMS" in s or ("n_sims" in s and "raise" in s)
    has_uniform = "kstest" in s or "ks_1samp" in s or "uniform" in s.lower()
    ok = has_min and has_uniform
    return ("PASS" if ok else "FAIL",
            "min-n enforced + uniformity test" if ok
            else "wide binomial band only; passes at any n")


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
GUARD_EXEMPT = {
    # Builds the panel, including the lag/lead buffer that deliberately extends
    # to PANEL_BUFFER_END = 2021-01-31 — inside a confirmation window. Filtering
    # here would destroy the padding the lag structure needs. Nothing in this
    # script examines an outcome; the modelling scripts filter downstream.
    "01_build_panel.py",
    # The auditor itself: it must be able to read the raw panel to check it.
    "23_regression_suite.py",
}


def d_guard_coverage():
    """D3: every panel-reading script must route the panel through the guard.

    Tests the PROPERTY (does this script go through freeze_guard?) rather than
    one function name. The first version grepped for `assert_discovery_only`,
    so renaming the entry point to `select_sample` — the actual fix for the
    tautology — made this check report the fixed scripts as unguarded.
    """
    entries = ("select_sample", "assert_no_confirmation_outcomes",
               "assert_discovery_only")
    missing = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in GUARD_EXEMPT:
            continue
        t = f.read_text()
        if "panel_cd_day.parquet" in t and not any(e in t for e in entries):
            missing.append(f.name)
    return ("PASS" if not missing else "FAIL",
            f"all panel readers guarded ({len(GUARD_EXEMPT)} documented exemptions)"
            if not missing else f"unguarded: {missing}")


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
    ("T.basket_not_registry_gated", "T9", "basket reaches victims MPV omits", t_basket_not_registry_gated),
    ("T.wiki_ext_matches_basket", "X2,T9", "wiki_ext built from the current basket", t_wiki_ext_matches_basket),
    ("T.wiki_basket_live", "X2", "wiki basket not selected by retired Twitter", t_wiki_basket_twitter),
    ("S.reference_day", "S2,D1", "event-time reference is day -1", s_reference_day),
    ("S.placebo_count", "S1,E1,L1,X4,D2", "placebo draws keep the real episode count", s_placebo_count),
    ("S.joint_test", "S3,R7", "statistic sees a dip-then-rebound", s_joint_test),
    ("S.cluster_by_date", "S6", "SEs clustered by date, not hetero", s_cluster_by_date),
    ("S.prewindow_truncation", "S5,E4", "contested district-days reassigned, not deleted", s_prewindow_truncation),
    ("S.calibration_can_fail", "S4,X3,R3", "calibration verdict can fail", s_calibration_can_fail),
    ("S.no_stale_calibration", "R3", "no stale low-n calibration artifact", s_stale_calibration_artifact),
    ("S.ppml_wired", "X5,R8", "counts/PPML arm actually called", s_ppml_wired),
    ("D.freeze_not_tautological", "D3", "freeze guard is not a tautology", d_freeze_not_tautological),
    ("D.freeze_disjoint", "D3", "confirmation sample disjoint from discovery", d_freeze_enforces_disjoint),
    ("D.guard_coverage", "D3", "every panel reader calls the guard", d_guard_coverage),
    ("D.guard_can_fire", "D3,D4", "freeze guard actually rejects things", d_guard_can_fire),
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
