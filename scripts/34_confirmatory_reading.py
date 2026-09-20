"""34_confirmatory_reading — the pre-registered reading of the sealed result, applied mechanically.

Reads ONE file — the sealed output of `30_confirmatory_run.py` — and the
pre-freeze power table, and writes the verdict the pre-registration fixes for
those numbers. Every rule it applies is written down before the freeze lifted:

  * PRE_ANALYSIS_NOTE.md §9 (interpretation) and §10 (the family), as amended by
  * CONFIRMATION_PLAN.md addendum §23.1–23.4 (what "rejects" means, direction,
    the denominator diagnostic, the placebo override on cardiac and asthma),
  * addendum §19 rule 2 (a non-rejection is a bounded null whose bound is the
    pre-freeze MDE) and §23.11 (the family-correction factor quoted beside it),
  * addendum §25 (a stratum whose null is uncertified enters the family as p = 1
    and its primary inference is the asymptotic p, labelled).

It exists so that no judgement is exercised between the sealed table and the
sentence in the paper: the paper quotes this file, and this file is a pure
function of the sealed one. It reads no panel, no episode list and no outcome
row; the only outcome-derived numbers it touches are the statistics 30 already
sealed. Under the freeze it runs only on the synthetic dry run (`--synthetic`),
which is how it is tested.

Output (long format; `stratum,item,value,rule,detail`):
  real mode      data/reference/confirmatory_reading.csv   (tracked, beside the seal)
  synthetic mode outputs/tables/confirmatory_reading_dryrun_synthetic.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
import signal
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import (BH_Q, DATA_REFERENCE, FREEZE_ACTIVE, H1_OUTCOMES, OUTPUTS_TABLES,
                    MINIMUM_EFFECT_OF_INTEREST, PROJECT_ROOT)
from event_study import count_outcome

signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not traceback

ALPHA = 0.05                       # unadjusted level for placebo, diagnostic and sensitivity cells
FAMILY_CORRECTION_FACTOR = 1.28    # addendum 23.11: (z_.9969 + z_.8)/(z_.975 + z_.8) at the Bonferroni bound
INFERENTIAL = ("C1_clean", "C2_exposed")
# Addendum 23.4: the override is defined on cardiac and asthma. Injury is estimated
# and reported in the falsification family but does not override — the discovery
# decomposition found the injury channel responds to attention episodes (protest
# injuries), so a movement in injury is a plausible effect of the treatment rather
# than evidence that the design measures something else.
OVERRIDE_PLACEBOS = ("cardiac_share", "cardiac", "asthma_share", "asthma")
POWER_KEY = {"C1_clean": "C1", "C2_exposed": "C2"}

parser = argparse.ArgumentParser()
parser.add_argument("--synthetic", action="store_true",
                    help="read the synthetic dry run instead of the sealed result (the only "
                         "mode that runs while FREEZE_ACTIVE is True)")
parser.add_argument("--overwrite-reading", default=None, metavar="REASON",
                    help="replace an existing real reading of the SAME sealed table; the reason is "
                         "written into the sidecar. Never needed on a first reading.")
ARGS = parser.parse_args() if __name__ == "__main__" else parser.parse_args([])

SEALED = DATA_REFERENCE / "confirmatory_results.csv"
DRYRUN = OUTPUTS_TABLES / "confirmatory_results_dryrun_synthetic.csv"
OUT_REAL = DATA_REFERENCE / "confirmatory_reading.csv"
OUT_SYNTHETIC = OUTPUTS_TABLES / "confirmatory_reading_dryrun_synthetic.csv"
# The pre-freeze power table, TRACKED (data/reference/power_analysis_prefreeze.csv,
# committed before the lift), so the bound a non-rejection is read against is
# sealed with the specification and cannot be a post-lift recomputation (addendum
# 19 rule 7; third CP2 audit pass, 2026-09-20).
POWER = DATA_REFERENCE / "power_analysis_prefreeze.csv"
# The pre-specified sensitivity set the robust/fragile label is computed over (note
# 9.5, addenda 3, 18, 20, 29, 30). Nothing outside it enters the label.
SENSITIVITY_SPECS = ("sens_drop_jul2016", "sens_broad_basket", "sens_spliced_wiki", "sens_coverage_clean",
                     "sens_geocoding_clean", "sens_bheard_late_bound", "sens_post28", "sens_post60",
                     "sens_incl_cancelled", "sens_no_edpm")


class ReadingRefused(RuntimeError):
    pass


def load():
    if ARGS.synthetic:
        if not DRYRUN.exists():
            raise ReadingRefused(f"{DRYRUN} absent — run 30_confirmatory_run.py --dry-run-synthetic")
        d = pd.read_csv(DRYRUN)
        if not (d["data_source"] == "SYNTHETIC").all():
            raise ReadingRefused("the dry-run file carries non-synthetic rows")
        return d, OUT_SYNTHETIC
    if FREEZE_ACTIVE:
        raise ReadingRefused("FREEZE_ACTIVE is True: the sealed result cannot exist yet; "
                             "use --synthetic to exercise the rules on the dry run")
    if not SEALED.exists():
        raise ReadingRefused(f"{SEALED} absent — Phase I has not run")
    d = pd.read_csv(SEALED)
    if not (d["data_source"] == "REAL").all():
        raise ReadingRefused("the sealed file carries non-REAL rows")
    if int(d["freeze_active_at_run"].max()) != 0:
        raise ReadingRefused("the sealed file says it was written with the freeze active")
    return d, OUT_REAL


def power_mdes():
    """Pre-freeze MDEs per stratum (addendum 19 rule 2), from the TRACKED pre-freeze
    table only. Refuses if it is absent or was not written under the freeze: an
    MDE computed after the lift is post hoc (rule 7) and may not enter rule 2."""
    if not POWER.exists():
        raise ReadingRefused(f"{POWER} absent: the pre-freeze power table is the only bound a "
                             "non-rejection may be read against (addendum 19 rule 7)")
    pw = pd.read_csv(POWER).set_index("metric")["value"]
    if int(float(pw.get("freeze_active", 0))) != 1:
        raise ReadingRefused(f"{POWER.name} was not written with the freeze active; a post-lift "
                             "power figure is post hoc (addendum 19 rule 7)")
    out = {}
    for s, key in POWER_KEY.items():
        try:
            out[s] = {"level": float(pw[f"{key}.mde_worst_profile"]),
                      "dip_rebound": float(pw[f"{key}.mde_best_profile"]),
                      "verdict": str(pw.get(f"{key}.POWER_VERDICT", "")),
                      "freeze_active": int(float(pw.get("freeze_active", 1)))}
        except KeyError:
            continue
    return out


def cell(d, stratum, family, spec, outcome, estimator):
    m = ((d["stratum"] == stratum) & (d["family"] == family) & (d["spec"] == spec)
         & (d["outcome"] == outcome) & (d["estimator"] == estimator))
    hit = d[m]
    if len(hit) > 1:
        raise ReadingRefused(f"{stratum}/{spec}/{outcome}/{estimator}: {len(hit)} rows, expected one")
    return hit.iloc[0] if len(hit) == 1 else None


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def sign_word(v):
    if v is None or np.isnan(v):
        return "none"
    return "decline" if v < 0 else "increase" if v > 0 else "zero"


def read_stratum(d, s, rows, mde):
    """Apply 23.1–23.4 and 19.2 to one inferential stratum. Returns its 9.4 input."""
    def add(item, value, rule, detail=""):
        rows.append({"stratum": s, "item": item, "value": value, "rule": rule, "detail": detail})

    certified = d.loc[d["stratum"] == s, "null_certified"]
    cert = bool(certified.iloc[0]) if len(certified) and certified.notna().any() else True
    add("null_certified", int(cert), "addendum 25",
        "" if cert else "randomization p reported, not used in the family; asymptotic p is the "
                        "primary inference and a rejection on it cannot count as confirmation")

    arms = {"share": "OLS_share", "count": "PPML_count_offset"}
    reject_on, one_arm, discordant, denom, directions = {}, {}, {}, {}, {}
    share_means = {}   # primary share-arm first-week mean per outcome (23.1e reads the interaction against it)
    # Addendum 25.3: in an uncertified stratum EVERY rule reads the asymptotic p —
    # the primary cells, the placebo override and the denominator diagnostic —
    # because the randomization p there rests on a null that failed its test.
    pcol = "p_randomization" if cert else "p_asymptotic"
    min_unadj = np.nan
    for o in H1_OUTCOMES:
        cells = {}
        for arm, est in arms.items():
            col = o if arm == "share" else count_outcome(o)
            c = cell(d, s, "primary_H1", "primary", col, est)
            if c is None:
                add(f"cell_missing:{o}:{arm}", 1, "23.1", "no primary cell; counts as p = 1 in the family")
                cells[arm] = None
                continue
            p_bh, p_ri, p_as = f(c["p_bh_adjusted"]), f(c["p_randomization"]), f(c["p_asymptotic"])
            mean, se = f(c["first_week_mean_coef"]), f(c.get("first_week_mean_se", np.nan))
            if cert:
                rej = bool(not np.isnan(p_bh) and p_bh < BH_Q)
            else:
                # Addendum 25.3: an uncertified stratum's primary inference is the
                # asymptotic joint-Wald p, per cell at 0.05, labelled; a rejection
                # on it is "not certified" and cannot count as confirmation.
                rej = bool(not np.isnan(p_as) and p_as < ALPHA)
            cells[arm] = dict(rej=rej, mean=mean, se=se, p_bh=p_bh, p_ri=p_ri, p_as=p_as,
                              status=str(c["status"]))
            if arm == "share":
                share_means[o] = mean
            add(f"p_randomization:{o}:{arm}", p_ri, "note §7", str(c["status"]))
            pu = p_ri if cert else p_as
            if not np.isnan(pu):
                min_unadj = pu if np.isnan(min_unadj) else min(min_unadj, pu)
            add(f"p_bh_adjusted:{o}:{arm}", p_bh, "note §10; 23.1 (m = 8, q = %.2f)" % BH_Q)
            add(f"p_asymptotic:{o}:{arm}", p_as, "note §7 (beside, never instead)")
            add(f"first_week_mean_coef:{o}:{arm}", mean, "note §6; 23.2")
            add(f"first_week_mean_se:{o}:{arm}", se, "23.2")
            add(f"rejects_bh:{o}:{arm}", int(rej) if cert else 0, "23.1",
                "BH-adjusted randomization p below %.2f" % BH_Q + ("" if cert else "; uncertified null enters as p = 1"))
            if not cert:
                add(f"rejects_asymptotic:{o}:{arm}", int(rej), "25.3",
                    f"asymptotic p below {ALPHA} in an uncertified stratum; labelled, cannot count as confirmation")
        both = all(v is not None and v["rej"] for v in cells.values())
        signs = {arm: np.sign(v["mean"]) for arm, v in cells.items() if v is not None and not np.isnan(v["mean"])}
        same_sign = len(signs) == 2 and len(set(signs.values())) == 1 and 0 not in signs.values()
        reject_on[o] = both and same_sign
        any_rej = any(v is not None and v["rej"] for v in cells.values())
        # 23.2 governs both-arms rejections with opposite signs (a rejection
        # without a consistent direction); 23.1a governs a one-arm rejection.
        discordant[o] = both and not same_sign
        one_arm[o] = any_rej and not both
        add(f"rejects_on_outcome:{o}", int(reject_on[o]), "23.1",
            "both arms reject with the same sign of the first-week mean" if reject_on[o]
            else ("both arms reject with opposite signs: a rejection without a consistent direction (23.2)"
                  if discordant[o] else
                  "rejection in one arm only: a movement in one arm, not a rejection in 9.4 (23.1a, 23.3)"
                  if one_arm[o] else "no arm rejects"))
        if one_arm[o]:
            which = [arm for arm, v in cells.items() if v is not None and v["rej"]]
            add(f"one_arm_movement:{o}", ",".join(which), "23.1a",
                "share only: read by 23.3 (denominator diagnostic); count only: a count movement the share "
                "did not follow, not claimed as a change in demand (note 9.2)")
        # 23.2 direction, over the rejecting cells
        if reject_on[o]:
            within_se = any(v["se"] is not None and not np.isnan(v["se"]) and abs(v["mean"]) <= v["se"]
                            for v in cells.values())
            directions[o] = "inconsistent" if within_se else sign_word(cells["share"]["mean"])
            add(f"direction:{o}", directions[o], "23.2",
                "mean within one asymptotic SE of zero in an arm: a rejection without a consistent "
                "direction, reported with the day-by-day path" if within_se else
                "sign of the first-week mean coefficient over the rejecting cells")
        # 23.3 denominator diagnostic, for any share-arm rejection
        share_rej = cells["share"] is not None and cells["share"]["rej"]
        if share_rej:
            tot = cell(d, s, "diagnostic", "diag_total_dispatches", "total_calls", "PPML_count_no_offset")
            raw = cell(d, s, "diagnostic", "diag_raw_count", count_outcome(o), "PPML_count_no_offset")
            p_tot = f(tot[pcol]) if tot is not None else np.nan
            p_raw = f(raw[pcol]) if raw is not None else np.nan
            if np.isnan(p_tot) or np.isnan(p_raw):
                # A diagnostic that produced no p-value is unavailable; it is not
                # evidence either way (23.3a, third audit pass). The rejection stands
                # with the caveat recorded.
                denom[o] = False
                add(f"denominator_driven:{o}", 0, "23.3",
                    f"diagnostic unavailable (total-dispatch p = {p_tot}, raw-count p = {p_raw}); the share "
                    "rejection is reported with this caveat, not discounted")
            else:
                denom[o] = bool(p_tot <= ALPHA and p_raw > ALPHA)
                add(f"denominator_driven:{o}", int(denom[o]), "23.3",
                    f"total-dispatch diagnostic p = {p_tot:.4f}, raw-count diagnostic p = {p_raw:.4f}"
                    + ("" if cert else " (asymptotic; uncertified stratum, 25.3)"))
        else:
            denom[o] = False
    # 23.4 placebo override, within the stratum, unadjusted, on cardiac and asthma
    plac_all = d[(d["stratum"] == s) & (d["family"] == "placebo")]
    plac = plac_all[plac_all["outcome"].isin(OVERRIDE_PLACEBOS)]
    plac_rej = plac[plac[pcol].astype(float) <= ALPHA]
    # An override cell that produced no p-value cannot reject, and its absence
    # may not read as a placebo that passed: the check is reported as incomplete
    # (23.4, third audit pass). Four cells are expected: cardiac and asthma, both arms.
    have_p = {(r.outcome, r.estimator) for r in plac.itertuples() if not np.isnan(f(getattr(r, pcol)))}
    expected = {("cardiac_share", "OLS_share"), ("cardiac", "PPML_count_offset"),
                ("asthma_share", "OLS_share"), ("asthma", "PPML_count_offset")}
    plac_missing = sorted(expected - have_p)
    add("placebo_rejects_any", int(len(plac_rej) > 0), "23.4",
        "; ".join(f"{r.outcome}/{r.estimator} p = {float(getattr(r, pcol)):.4f}" for r in plac_rej.itertuples())
        or f"no cardiac or asthma cell at p <= {ALPHA} ({len(have_p)} of {len(expected)} override cells with a p-value)"
        + ("" if cert else "; asymptotic p (uncertified stratum, 25.3)"))
    add("placebo_cells_unavailable", len(plac_missing), "23.4",
        ("; ".join(f"{o}/{e}" for o, e in plac_missing) + ": no p-value, so the placebo check is incomplete")
        if plac_missing else "every override cell carries a p-value")
    for r in plac_all[~plac_all["outcome"].isin(OVERRIDE_PLACEBOS)].itertuples():
        add(f"falsification_reported_only:{r.outcome}:{r.estimator}", f(r.p_randomization), "23.4",
            "injury is reported, not an override outcome: the discovery decomposition found it responds "
            "to attention episodes (protest injuries)")
    # 23.3a: a denominator-driven rejection is discounted per outcome and does not
    # veto a clean rejection on the other outcome; the stratum rejects when at least
    # one outcome rejects on both arms, same sign, and is not denominator-driven.
    clean = [o for o in H1_OUTCOMES if reject_on[o] and not denom[o]]
    discounted = [o for o in H1_OUTCOMES if reject_on[o] and denom[o]]
    stratum_rejects = bool(clean)
    add("stratum_rejects", int(stratum_rejects), "23.1, 23.3a",
        f"rejects on {', '.join(clean)}" + (f"; the {', '.join(discounted)} rejection is denominator-driven and discounted" if discounted else "")
        if stratum_rejects else
        ("every both-arms rejection is denominator-driven (23.3)" if discounted else "no primary outcome rejects on both arms"))
    rejected_outcomes = clean   # for the 9.4 same-outcome rule (23.1b)

    # The 9.4 input, after the overrides
    any_cell = any(one_arm.values()) or any(discordant.values()) or any(reject_on.values())
    m = mde.get(s, {})
    lvl, dip = m.get("level", np.nan), m.get("dip_rebound", np.nan)
    add("mde_level_prefreeze", lvl, "19.2", f"{m.get('verdict', 'power table absent')}; worst-profile MDE at nominal alpha")
    add("mde_dip_rebound_prefreeze", dip, "19.2", "best-profile MDE at nominal alpha")
    add("mde_level_family_corrected", lvl * FAMILY_CORRECTION_FACTOR if not np.isnan(lvl) else np.nan,
        "23.11", f"nominal-level MDE x {FAMILY_CORRECTION_FACTOR} at the Bonferroni bound")
    if not stratum_rejects:
        if any(discordant.values()) and not discounted:
            verdict = "rejects without a consistent direction (23.2): neither confirmation nor disconfirmation"
        elif discounted:
            verdict = "rejects, denominator-driven (23.3): not claimed as a change in demand"
        elif any(one_arm.values()):
            which = "; ".join(f"{o} ({v})" for o, v in one_arm.items() if v)
            verdict = f"does not reject on both arms; a movement in one arm only in {which} is reported (23.1a)"
        else:
            verdict = "does not reject"
        if not any_cell:
            add("bounded_null", 1, "19.2",
                f"no effect detected at the family level (smallest unadjusted {'randomization' if cert else 'asymptotic'} "
                f"p among the stratum's primary cells {min_unadj:.4f}); a sustained level shift at or above the "
                f"pre-freeze MDE {lvl:.5f} in absolute value (about {lvl * FAMILY_CORRECTION_FACTOR:.5f} under the "
                f"approximate one-parameter family correction of 23.11) is disfavoured at 80% power; a sustained "
                f"shift of the minimum effect of interest (−{MINIMUM_EFFECT_OF_INTEREST}) is not excluded; "
                + (f"a transient dip-and-rebound of the minimum effect of interest is disfavoured (its pre-freeze "
                   f"MDE is {dip:.5f}, at or below {MINIMUM_EFFECT_OF_INTEREST} in absolute value)"
                   if not np.isnan(dip) and dip <= MINIMUM_EFFECT_OF_INTEREST else
                   f"a transient dip-and-rebound of the minimum effect of interest is not excluded (its pre-freeze "
                   f"MDE is {dip:.5f}, above {MINIMUM_EFFECT_OF_INTEREST} in absolute value)"))
        else:
            add("bounded_null", 0, "19.2, 23.1a",
                "not asserted: a primary cell rejected, so 'no effect detected' would be false on this table; "
                f"the pre-freeze bound for the sustained shape ({lvl:.5f}) is stated beside the movement")
    else:
        dirs = {directions[o] for o in clean}
        if "inconsistent" in dirs and dirs == {"inconsistent"}:
            verdict = "rejects without a consistent direction (23.2): neither confirmation nor disconfirmation"
        elif dirs - {"inconsistent"} == {"decline"}:
            verdict = "rejects, predicted direction" + (" (on " + ", ".join(o for o in clean if directions[o] == "decline") + ")")
        elif dirs - {"inconsistent"} == {"increase"}:
            verdict = "rejects, opposite direction (9.1): not support for H1"
        else:
            verdict = "rejects, directions differ across outcomes: reported with both paths"
        if discounted:
            verdict += f"; the {', '.join(discounted)} rejection is denominator-driven (23.3) and discounted"
        if len(plac_rej):
            # Every rejection in the stratum, whatever its direction: an
            # opposite-direction rejection under an override is not evidence for
            # the opposite channel either (23.4, third audit pass).
            verdict += "; PLACEBO OVERRIDE (23.4): not supporting H1 and not evidence for the opposite channel"
        elif plac_missing:
            verdict += (f"; PLACEBO CHECK INCOMPLETE (23.4): {len(plac_missing)} of {len(expected)} override "
                        "cells have no p-value, so the override could not be evaluated on them")
        if not cert:
            verdict = verdict.replace("rejects", "rejects on the asymptotic p", 1) + \
                      "; UNCERTIFIED NULL (addendum 25): not certified, cannot count as confirmation"
    add("reading_9_4_input", verdict, "23.1–23.4, 19.2, 25")
    add("rejected_outcomes", ",".join(rejected_outcomes) if rejected_outcomes else "", "23.1b",
        "outcomes on which the stratum rejects cleanly; 9.4 row 1 needs a common outcome across strata")

    # 9.5 sensitivities: reported beside, never substituted; unadjusted; the set
    # is enumerated (SENSITIVITY_SPECS) and only H1-outcome cells enter the label.
    sens = d[(d["stratum"] == s) & (d["family"] == "sensitivity")]
    for r in sens.itertuples():
        p = f(getattr(r, pcol))
        add(f"sensitivity_p:{r.spec}:{r.outcome}:{r.estimator}", p, "9.5",
            str(r.status) + (f"; n_episodes {r.n_episodes}" if not np.isnan(p) else ""))
    h1_cols = set(H1_OUTCOMES) | {count_outcome(o) for o in H1_OUTCOMES} \
        | {f"{o}_incl_cancelled" for o in H1_OUTCOMES} | {count_outcome(f"{o}_incl_cancelled") for o in H1_OUTCOMES} \
        | {"edp_ex_edpm_share", "edp_ex_edpm"}
    sens_h1 = sens[sens["spec"].isin(SENSITIVITY_SPECS) & sens["outcome"].isin(h1_cols)]
    if stratum_rejects:
        # A rejection SURVIVES a sensitivity when every estimated cell of that
        # sensitivity on a rejecting outcome stays at p <= alpha; a cell recorded
        # IDENTICAL_TO_PRIMARY survives by construction; a NOT_RUN cell is not
        # applicable and does not count (23.1c, third audit pass).
        base = {o for o in clean} | {count_outcome(o) for o in clean} \
            | {f"{o}_incl_cancelled" for o in clean} | {count_outcome(f"{o}_incl_cancelled") for o in clean} \
            | ({"edp_ex_edpm_share", "edp_ex_edpm"} if "edp_share" in clean else set())
        results = {}
        for spec in SENSITIVITY_SPECS:
            cells_ = sens_h1[(sens_h1["spec"] == spec) & sens_h1["outcome"].isin(base)]
            if cells_.empty or cells_["status"].astype(str).str.startswith("NOT_RUN").all():
                continue
            ok = []
            for r in cells_.itertuples():
                st = str(r.status)
                if st.startswith("IDENTICAL_TO_PRIMARY"):
                    ok.append(True)
                elif st.startswith("OK"):
                    ok.append(bool(f(getattr(r, pcol)) <= ALPHA))
            if ok:
                results[spec] = all(ok)
                add(f"sensitivity_survives:{spec}", int(results[spec]), "9.5, 23.1c")
        n, k = len(results), sum(results.values())
        label = ("robust: survives every applicable sensitivity" if n and k == n
                 else "fragile: survives no applicable sensitivity" if n and k == 0
                 else f"survives {k} of {n} applicable sensitivities")
    else:
        ran = sens_h1[sens_h1["status"].astype(str).str.startswith("OK")]
        n_hit = int((ran[pcol].astype(float) <= ALPHA).sum())
        label = (f"primary does not reject; {n_hit} of {len(ran)} H1-outcome sensitivity cells at p <= {ALPHA}"
                 + (" (reported, not substituted)" if n_hit else ""))
    add("sensitivity_summary", label, "9.5, 23.1c")

    # secondary arms (the B-HEARD interaction, C2 only; the dose-response arm):
    # asymptotic p only, outside the family (note §5, §10; addendum 9)
    # Each is read mechanically against the direction the note fixes (23.1e):
    # the dose arm's predicted sign is H1's (a decline per SD of intensity); the
    # interaction's predicted sign is OPPOSITE to the stratum's primary first-week
    # mean on that outcome (attenuation where B-HEARD has already removed
    # police contact, note §7), stated only when that mean is negative.
    sec = d[(d["stratum"] == s) & (d["family"] == "secondary")]
    for r in sec.itertuples():
        p_sec, coef = f(r.p_asymptotic), f(r.first_week_mean_coef)
        add(f"secondary_p_asymptotic:{r.spec}:{r.outcome}:{r.estimator}", p_sec,
            "note §5, §10; addendum 9", f"coef {coef:.6f}; {r.status}")
        if not str(r.status).startswith("OK") or np.isnan(p_sec) or np.isnan(coef):
            reading = f"not read ({r.status})"
        else:
            if r.spec == "dose_response":
                predicted = -1.0
            else:
                share_o = r.outcome if str(r.outcome).endswith("_share") else f"{r.outcome}_share"
                mean_o = share_means.get(share_o, np.nan)
                predicted = 1.0 if (not np.isnan(mean_o) and mean_o < 0) else np.nan
            if np.isnan(predicted):
                reading = "no predicted direction (the primary first-week mean is not negative); reported only"
            elif p_sec > ALPHA:
                reading = f"no movement (asymptotic p = {p_sec:.4f} > {ALPHA})"
            elif np.sign(coef) == predicted:
                reading = f"moves in the predicted direction (asymptotic p = {p_sec:.4f}; coef {coef:+.6f})"
            else:
                reading = f"moves against the predicted direction (asymptotic p = {p_sec:.4f}; coef {coef:+.6f})"
        add(f"secondary_reading:{r.spec}:{r.outcome}:{r.estimator}", reading, "23.1e",
            "descriptive; outside the family; never enters the 9.4 conclusion")
    return verdict, rejected_outcomes


def conclusion_9_4(v1, v2, common_outcomes=()):
    """The asymmetric C1/C2 table of note §9.4, with 23.x readings folded in.

    23.1b: row 1 ("Confirmed") requires the two strata to reject on at least one
    COMMON outcome in the same direction; rejections on different outcomes only
    are row 2 with C2's rejection reported as partial agreement.
    """
    def kind(v):
        if v.startswith("does not reject"):
            return "no"
        if v.startswith("rejects on the asymptotic p"):
            return "other"
        if v.startswith("rejects, predicted direction") and "OVERRIDE" not in v and "UNCERTIFIED" not in v:
            return "pred"
        if v.startswith("rejects, opposite"):
            return "opp"
        return "other"   # denominator-driven, inconsistent, overridden, uncertified
    k1, k2 = kind(v1), kind(v2)
    if k1 == "pred" and k2 == "pred" and common_outcomes:
        return ("CONFIRMED: C1 and C2 both reject in the predicted direction on "
                + ", ".join(common_outcomes) + " (9.4 row 1)")
    if k1 == "pred" and k2 == "pred":
        return ("CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2; 23.1b): C2 rejects in the same direction "
                "but on a different outcome — partial agreement, reported, not row 1")
    if k1 == "pred" and k2 == "no":
        return "CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2): reported with C2's lower treatment precision and B-HEARD"
    if k1 == "pred" and k2 == "other":
        # C2's rejection is discounted, overridden, directionless or uncertified:
        # that is C2 failing to add to C1, not C1 failing (9.4 row 2; third audit pass).
        return f"CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2): C2's rejection does not count — {v2}"
    if k1 == "no" and k2 == "pred":
        return "NOT CONFIRMATION (9.4 row 3): a C2-only decline cannot be separated from B-HEARD; the interaction arm speaks to it"
    if {k1, k2} == {"pred", "opp"}:
        return "THE CONFIRMATION HAS FAILED (9.4 row 4): the strata reject in opposite directions; both estimates in print"
    if k1 == "no" and k2 == "no":
        moved = [n for n, v in (("C1", v1), ("C2", v2)) if "one arm" in v]
        return ("THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2"
                + (f"; a one-arm movement in {', '.join(moved)} is reported under 23.1a" if moved else ""))
    parts = []
    for name, k, v in (("C1", k1, v1), ("C2", k2, v2)):
        if k == "opp":
            parts.append(f"{name}: null rejected opposite to prediction (9.1) — evidence for the opposite channel, not H1")
        elif k == "other":
            parts.append(f"{name}: {v}")
        elif k == "no":
            parts.append(f"{name}: does not reject (bounded null, 19.2)")
        else:
            parts.append(f"{name}: rejects in the predicted direction")
    return "NOT SUPPORT FOR H1 AS PRE-SPECIFIED; " + "; ".join(parts)


def evaluate(d, mde):
    """The whole reading as a pure function of the sealed table and the pre-freeze
    MDEs: (long-format rows, per-stratum 9.4 inputs, the 9.4 conclusion). The
    regression suite calls this on planted tables to hold every rule to its text."""
    rows = []
    fam = d[d["family"] == "primary_H1"]
    n_fam = len(fam)
    if n_fam != 8:
        raise ReadingRefused(f"the primary family has {n_fam} rows, not 8")
    rows.append({"stratum": "family", "item": "family_size", "value": n_fam, "rule": "note §10", "detail": "2 outcomes x 2 arms x 2 strata"})
    n_rej = int((fam["p_bh_adjusted"].astype(float) < BH_Q).sum())
    rows.append({"stratum": "family", "item": "family_rejections_bh", "value": n_rej,
                 "rule": "23.1", "detail": f"cells with BH-adjusted p < {BH_Q}"})
    out = {s: read_stratum(d, s, rows, mde) for s in INFERENTIAL}
    verdicts = {s: v for s, (v, _) in out.items()}
    rejected = {s: r for s, (_, r) in out.items()}
    common = sorted(set(rejected["C1_clean"]) & set(rejected["C2_exposed"]))
    concl = conclusion_9_4(verdicts["C1_clean"], verdicts["C2_exposed"], common)
    rows.append({"stratum": "family", "item": "conclusion_9_4", "value": concl, "rule": "note §9.4 as amended by 23",
                 "detail": f"C1: {verdicts['C1_clean']} | C2: {verdicts['C2_exposed']}"})
    # pooled: descriptive, promised, never overturns a stratum-level disagreement.
    # Its own reading (23.1d, third audit pass): both arms at unadjusted p <= alpha
    # with the same sign on an outcome = "pooled rejects (descriptive)".
    pooled = d[(d["stratum"] == "pooled") & (d["family"] == "descriptive")]
    pooled_rej = []
    for r in pooled.itertuples():
        rows.append({"stratum": "pooled", "item": f"p_randomization:{r.outcome}:{r.estimator}",
                     "value": f(r.p_randomization), "rule": "note §9.4 (descriptive)",
                     "detail": f"mean coef {f(r.first_week_mean_coef):.6f}; {r.status}"})
    for o in H1_OUTCOMES:
        sh = pooled[(pooled["outcome"] == o) & (pooled["estimator"] == "OLS_share")]
        ct = pooled[(pooled["outcome"] == count_outcome(o)) & (pooled["estimator"] == "PPML_count_offset")]
        if len(sh) == 1 and len(ct) == 1:
            ps, pc = f(sh["p_randomization"].iloc[0]), f(ct["p_randomization"].iloc[0])
            ms, mc = f(sh["first_week_mean_coef"].iloc[0]), f(ct["first_week_mean_coef"].iloc[0])
            if ps <= ALPHA and pc <= ALPHA and np.sign(ms) == np.sign(mc) and ms != 0:
                pooled_rej.append(f"{o} ({sign_word(ms)})")
    pooled_verdict = ("pooled rejects on " + ", ".join(pooled_rej) + " (descriptive, unadjusted; does not overturn the strata)"
                      if pooled_rej else "pooled does not reject on both arms (descriptive)")
    rows.append({"stratum": "pooled", "item": "pooled_reading", "value": pooled_verdict,
                 "rule": "note §9.4 (descriptive); 23.1d", "detail": ""})
    if verdicts["C2_exposed"].startswith("rejects") and not verdicts["C1_clean"].startswith("rejects"):
        inter = [r for r in rows if r["stratum"] == "C2_exposed"
                 and str(r["item"]).startswith("secondary_reading:bheard_interaction:")]
        if inter:
            concl += "; the B-HEARD interaction arm (secondary, 23.1e) reads: " + "; ".join(
                f"{str(r['item']).split(':')[2]}: {r['value']}" for r in inter)
        for row in rows:
            if row["item"] == "conclusion_9_4":
                row["value"] = concl
    if pooled_rej and not any(v.startswith("rejects") for v in verdicts.values()):
        concl += "; the pooled stratum rejects where neither stratum does — reported, it overturns nothing (9.4)"
        for row in rows:
            if row["item"] == "conclusion_9_4":
                row["value"] = concl
    res = pd.DataFrame(rows, columns=["stratum", "item", "value", "rule", "detail"])
    return res, verdicts, concl


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    d, out = load()
    src_table = DRYRUN if ARGS.synthetic else SEALED
    table_sha = _sha(src_table)
    side = out.with_suffix(".meta.json")
    if not ARGS.synthetic and out.exists():
        prev = json.loads(side.read_text()) if side.exists() else {}
        if prev.get("sealed_table_sha256") == table_sha and not ARGS.overwrite_reading:
            raise ReadingRefused(f"{out.name} already exists for this sealed table ({table_sha[:12]}); the "
                                 "reading is written once. Pass --overwrite-reading 'reason' to replace it; "
                                 "the reason is recorded in the sidecar.")
    res, verdicts, concl = evaluate(d, power_mdes())
    res["data_source"] = "SYNTHETIC" if ARGS.synthetic else "REAL"
    res.to_csv(out, index=False)
    from provenance import code_fingerprint
    import datetime as _dt
    side.write_text(json.dumps({
        "sealed_table": str(src_table.relative_to(PROJECT_ROOT)),
        "sealed_table_sha256": table_sha,
        "power_table": str(POWER.relative_to(PROJECT_ROOT)), "power_table_sha256": _sha(POWER),
        "reader_code_sha256": code_fingerprint(Path(__file__)),
        "reader_source_sha256": _sha(Path(__file__)),
        "reading_sha256": _sha(out),
        "overwrite_reason": ARGS.overwrite_reading or "",
        "written_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }, indent=1) + "\n")
    print(f"wrote {out} ({len(res)} rows){' — SYNTHETIC: says nothing about any hypothesis' if ARGS.synthetic else ''}")
    for s in INFERENTIAL:
        print(f"  {s}: {verdicts[s]}")
    print(f"  {concl}")


if __name__ == "__main__":
    try:
        main()
    except ReadingRefused as e:
        print(f"REFUSED: {e}")
        sys.exit(3)
