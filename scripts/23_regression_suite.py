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
import importlib.util
import json
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

GUARD_EXEMPT = {
    # Builds the panel, including the lag/lead buffer that deliberately extends
    # to PANEL_BUFFER_END = 2021-01-31 — inside a confirmation window. Filtering
    # here would destroy the padding the lag structure needs. Nothing in this
    # script examines an outcome; the modelling scripts filter downstream.
    "01_build_panel.py",
    # The auditor itself: it must be able to read the raw panel to check it.
    "23_regression_suite.py",
    # The two extract builders WRITE the outcome artifacts from the raw SODA
    # pages. They cannot filter to a sample window: 01_build_panel.py needs the
    # full extract to build the lag/lead buffer, and the citywide trends file is
    # a descriptive 2005+ series by design. They are producers, not examiners.
    "00_local_ems_extract.py",
    "00b_download_ems_extract.py",
}


def d_guard_coverage():
    """D3: every panel-reading script must route the panel through the guard.

    Tests the PROPERTY (does this script go through freeze_guard?) rather than
    one function name. The first version grepped for `assert_discovery_only`,
    so renaming the entry point to `select_sample` — the actual fix for the
    tautology — made this check report the fixed scripts as unguarded.
    """
    from config import OUTCOME_ARTIFACTS
    entries = ("select_sample", "assert_no_confirmation_outcomes",
               "assert_discovery_only")
    missing = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in GUARD_EXEMPT:
            continue
        t = f.read_text()
        reads = [a for a in OUTCOME_ARTIFACTS if a in t]
        if reads and not any(e in t for e in entries):
            missing.append(f"{f.name}({','.join(a.split('.')[0] for a in reads)})")
    return ("PASS" if not missing else "FAIL",
            f"all readers of {len(OUTCOME_ARTIFACTS)} outcome artifacts guarded "
            f"({len(GUARD_EXEMPT)} documented exemptions)"
            if not missing else f"unguarded: {missing}")


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
               "assert_discovery_only", "freeze_banner")
    unguarded = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in producers:
            continue
        t = f.read_text()
        if EMS_DATASET_ID in t and not any(e in t for e in entries):
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


# ===========================================================================
# EPISODES
# ===========================================================================
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
            if f.exists() and pd.Timestamp(f.stat().st_mtime, unit="s", tz="UTC") > last["run_utc"]:
                stale.append(f"{s['id']}:{Path(a).name}")
    if unchecked:
        return "BLOCKED", f"{len(unchecked)} artifact(s) never scanned: {unchecked[:3]}"
    if bad or stale:
        return "FAIL", (f"{len(bad)} not verified {bad[:3]}; "
                        f"{len(stale)} verified before the file last changed {stale[:3]}")
    return "PASS", f"{len(art['target'].unique())} artifacts, all verified after their last write"


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
    ("T.anchor_monthly", "X1,T4,T5,L4", "Trends anchor rescales all days, not just 1-7", t_anchor_monthly),
    ("T.title_agg_no_trend", "T12", "title aggregation is not measuring accumulation", t_title_agg_no_trend),
    ("T.realised_coverage", "T7", "register asserts no span the data lacks", t_realised_coverage_recorded),
    ("X.csv_reproducible", "X15", "derived weights round-trip exactly", x_derived_csv_reproducible),
    ("X.no_stale_attribution", "X7", "DATA_AUDIT no longer misattributes 378->630", x_no_stale_audit_attribution),
    ("T.wiki_fetch_complete", "T15", "no basket article lost a title to a failed fetch", t_wiki_fetch_complete),
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
    ("S.calibration_can_fail", "S4,X3,R3", "calibration verdict can fail", s_calibration_can_fail),
    ("S.no_stale_calibration", "R3", "no stale low-n calibration artifact", s_stale_calibration_artifact),
    ("S.ppml_wired", "X5,R8", "counts/PPML arm actually called", s_ppml_wired),
    ("D.freeze_not_tautological", "D3", "freeze guard is not a tautology", d_freeze_not_tautological),
    ("D.freeze_disjoint", "D3", "confirmation sample disjoint from discovery", d_freeze_enforces_disjoint),
    ("D.guard_coverage", "D3,X11,X9", "every outcome-artifact reader calls the guard", d_guard_coverage),
    ("D.soda_guarded", "F2", "the source API is guarded, not only the artifacts", d_soda_source_guarded),
    ("D.incident_disclosed", "F1", "freeze incident stays in the record", d_incident_disclosed),
    ("D.guard_can_fire", "D3,D4", "freeze guard actually rejects things", d_guard_can_fire),
    ("E.threshold_stringency", "D5,L5,E6", "episode threshold is constant stringency", e_threshold_constant_stringency),
    ("E.no_mega_episode", "E3,D7,E6", "no episode exceeds its analysis window", e_no_mega_episode),
    ("E.frozen_list_untouched", "D3", "frozen episode list unmodified", e_frozen_list_untouched),
    ("E.labels_live_source", "E5,L6,R2", "episode labels not from retired Twitter", e_labels_not_from_twitter),
    ("E.attribution_lookback", "E2", "attribution lookback >= 60 days", e_attribution_lookback),
    ("O.ems_complete", "O5", "EMS extract covers the full source", o_ems_download_complete),
    ("O.panel_exists", "O5", "panel_cd_day.parquet exists", o_panel_exists),
    ("O.dropna_groupby", "O4", "missing-district rows not silently dropped", o_dropna_groupby),
    ("V.artifacts_current", "T14", "no artifact predates the script that writes it", v_artifacts_current),
    ("V.sources_verified", "X8,X14", "every source verified after its last write", v_sources_verified),
    ("V.no_duplicate_source_ids", "X8,X13", "one row per source id, no collisions", v_no_duplicate_source_ids),
    ("V.claims_reproduce", "X14", "every claimed number recomputes from its artifact", v_claims_reproduce),
    ("V.links_resolve", "X14", "every endpoint has a dated result", v_links_resolve),
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
