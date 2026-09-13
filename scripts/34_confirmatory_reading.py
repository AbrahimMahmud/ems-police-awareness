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
import sys

import numpy as np
import pandas as pd

from config import (BH_Q, DATA_REFERENCE, FREEZE_ACTIVE, H1_OUTCOMES, OUTPUTS_TABLES,
                    MINIMUM_EFFECT_OF_INTEREST)
from event_study import count_outcome

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
ARGS = parser.parse_args() if __name__ == "__main__" else parser.parse_args([])

SEALED = DATA_REFERENCE / "confirmatory_results.csv"
DRYRUN = OUTPUTS_TABLES / "confirmatory_results_dryrun_synthetic.csv"
OUT_REAL = DATA_REFERENCE / "confirmatory_reading.csv"
OUT_SYNTHETIC = OUTPUTS_TABLES / "confirmatory_reading_dryrun_synthetic.csv"
POWER = OUTPUTS_TABLES / "power_analysis.csv"


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
    """Pre-freeze MDEs per stratum (addendum 19 rule 2). Absent → NaN, stated."""
    if not POWER.exists():
        return {}
    pw = pd.read_csv(POWER).set_index("metric")["value"]
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
    reject_on, one_arm, denom, directions = {}, {}, {}, {}
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
            rej = bool(cert and not np.isnan(p_bh) and p_bh < BH_Q)
            cells[arm] = dict(rej=rej, mean=mean, se=se, p_bh=p_bh, p_ri=p_ri, p_as=p_as,
                              status=str(c["status"]))
            add(f"p_randomization:{o}:{arm}", p_ri, "note §7", str(c["status"]))
            add(f"p_bh_adjusted:{o}:{arm}", p_bh, "note §10; 23.1 (m = 8, q = %.2f)" % BH_Q)
            add(f"p_asymptotic:{o}:{arm}", p_as, "note §7 (beside, never instead)")
            add(f"first_week_mean_coef:{o}:{arm}", mean, "note §6; 23.2")
            add(f"first_week_mean_se:{o}:{arm}", se, "23.2")
            add(f"rejects_bh:{o}:{arm}", int(rej), "23.1",
                "BH-adjusted randomization p below %.2f" % BH_Q + ("" if cert else "; uncertified null enters as p = 1"))
        both = all(v is not None and v["rej"] for v in cells.values())
        signs = {arm: np.sign(v["mean"]) for arm, v in cells.items() if v is not None and not np.isnan(v["mean"])}
        same_sign = len(signs) == 2 and len(set(signs.values())) == 1 and 0 not in signs.values()
        reject_on[o] = both and same_sign
        any_rej = any(v is not None and v["rej"] for v in cells.values())
        one_arm[o] = any_rej and not reject_on[o]
        add(f"rejects_on_outcome:{o}", int(reject_on[o]), "23.1",
            "both arms reject with the same sign of the first-week mean" if reject_on[o]
            else ("rejection in one arm only or with opposite signs: read by 23.3, not a rejection in 9.4"
                  if one_arm[o] else "no arm rejects"))
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
            p_tot = f(tot["p_randomization"]) if tot is not None else np.nan
            p_raw = f(raw["p_randomization"]) if raw is not None else np.nan
            denom[o] = bool(not np.isnan(p_tot) and p_tot <= ALPHA and (np.isnan(p_raw) or p_raw > ALPHA))
            add(f"denominator_driven:{o}", int(denom[o]), "23.3",
                f"total-dispatch diagnostic p = {p_tot:.4f}, raw-count diagnostic p = {p_raw:.4f}")
        else:
            denom[o] = False
    # 23.4 placebo override, within the stratum, unadjusted, on cardiac and asthma
    plac_all = d[(d["stratum"] == s) & (d["family"] == "placebo")]
    plac = plac_all[plac_all["outcome"].isin(OVERRIDE_PLACEBOS)]
    plac_rej = plac[plac["p_randomization"].astype(float) <= ALPHA]
    add("placebo_rejects_any", int(len(plac_rej) > 0), "23.4",
        "; ".join(f"{r.outcome}/{r.estimator} p = {float(r.p_randomization):.4f}" for r in plac_rej.itertuples())
        or f"no cardiac or asthma cell at p <= {ALPHA} ({len(plac)} cells)")
    for r in plac_all[~plac_all["outcome"].isin(OVERRIDE_PLACEBOS)].itertuples():
        add(f"falsification_reported_only:{r.outcome}:{r.estimator}", f(r.p_randomization), "23.4",
            "injury is reported, not an override outcome: the discovery decomposition found it responds "
            "to attention episodes (protest injuries)")
    stratum_rejects = any(reject_on.values())
    add("stratum_rejects", int(stratum_rejects), "23.1",
        "rejects on at least one primary outcome" if stratum_rejects else "no primary outcome rejects on both arms")

    # The 9.4 input, after the overrides
    if not stratum_rejects:
        verdict = "does not reject"
        m = mde.get(s, {})
        lvl, dip = m.get("level", np.nan), m.get("dip_rebound", np.nan)
        add("mde_level_prefreeze", lvl, "19.2", f"{m.get('verdict', 'power table absent')}; worst-profile MDE at nominal alpha")
        add("mde_dip_rebound_prefreeze", dip, "19.2", "best-profile MDE at nominal alpha")
        add("mde_level_family_corrected", lvl * FAMILY_CORRECTION_FACTOR if not np.isnan(lvl) else np.nan,
            "23.11", f"nominal-level MDE x {FAMILY_CORRECTION_FACTOR} at the Bonferroni bound")
        add("bounded_null", 1, "19.2",
            f"no effect detected; a sustained level shift at or above {lvl:.5f} (about "
            f"{lvl * FAMILY_CORRECTION_FACTOR:.5f} under the family correction) is disfavoured at 80% "
            f"power; a sustained shift of the minimum effect of interest ({MINIMUM_EFFECT_OF_INTEREST}) "
            f"is not excluded; a transient dip-and-rebound at or above {dip:.5f} is disfavoured")
    else:
        rej_outcomes = [o for o in H1_OUTCOMES if reject_on[o]]
        dirs = {directions[o] for o in rej_outcomes}
        if any(denom[o] for o in rej_outcomes):
            verdict = "rejects, denominator-driven (23.3): not claimed as a change in demand"
        elif "inconsistent" in dirs:
            verdict = "rejects without a consistent direction (23.2): neither confirmation nor disconfirmation"
        elif dirs == {"decline"}:
            verdict = "rejects, predicted direction"
        elif dirs == {"increase"}:
            verdict = "rejects, opposite direction (9.1): not support for H1"
        else:
            verdict = "rejects, directions differ across outcomes: reported with both paths"
        if len(plac_rej):
            verdict += "; PLACEBO OVERRIDE (23.4): not supporting H1"
        if not cert:
            verdict += "; UNCERTIFIED NULL (addendum 25): cannot count as confirmation"
    add("reading_9_4_input", verdict, "23.1–23.4, 19.2, 25")

    # 9.5 sensitivities: reported beside, never substituted; unadjusted
    sens = d[(d["stratum"] == s) & (d["family"] == "sensitivity")]
    for r in sens.itertuples():
        p = f(r.p_randomization)
        add(f"sensitivity_p:{r.spec}:{r.outcome}:{r.estimator}", p, "9.5",
            str(r.status) + (f"; n_episodes {r.n_episodes}" if not np.isnan(p) else ""))
    ran = sens[sens["p_randomization"].notna()]
    if stratum_rejects:
        # a rejection survives a sensitivity when the same outcome's cells stay at p <= alpha
        surv = [bool(float(r.p_randomization) <= ALPHA) for r in ran.itertuples()
                if r.outcome in [o for o in H1_OUTCOMES if reject_on[o]]
                or r.outcome in [count_outcome(o) for o in H1_OUTCOMES if reject_on[o]]]
        label = ("robust: survives every sensitivity" if surv and all(surv)
                 else "fragile: survives no sensitivity" if surv and not any(surv)
                 else f"survives {sum(surv)} of {len(surv)} sensitivity cells")
    else:
        n_hit = int((ran["p_randomization"].astype(float) <= ALPHA).sum())
        label = (f"primary does not reject; {n_hit} of {len(ran)} sensitivity cells at p <= {ALPHA}"
                 + (" (reported, not substituted)" if n_hit else ""))
    add("sensitivity_summary", label, "9.5")

    # secondary: the B-HEARD interaction arm (C2 only), asymptotic p only (note §10)
    sec = d[(d["stratum"] == s) & (d["family"] == "secondary")]
    for r in sec.itertuples():
        add(f"bheard_interaction_p_asymptotic:{r.outcome}:{r.estimator}", f(r.p_asymptotic),
            "note §5, §10", f"coef {f(r.first_week_mean_coef):.6f}; {r.status}")
    return verdict


def conclusion_9_4(v1, v2):
    """The asymmetric C1/C2 table of note §9.4, with 23.x readings folded in."""
    def kind(v):
        if v.startswith("does not reject"):
            return "no"
        if v.startswith("rejects, predicted direction") and "OVERRIDE" not in v and "UNCERTIFIED" not in v:
            return "pred"
        if v.startswith("rejects, opposite"):
            return "opp"
        return "other"   # denominator-driven, inconsistent, overridden, uncertified
    k1, k2 = kind(v1), kind(v2)
    if k1 == "pred" and k2 == "pred":
        return "CONFIRMED: C1 and C2 both reject in the predicted direction (9.4 row 1)"
    if k1 == "pred" and k2 == "no":
        return "CONFIRMED IN THE CLEAN STRATUM ONLY (9.4 row 2): reported with C2's lower treatment precision and B-HEARD"
    if k1 == "no" and k2 == "pred":
        return "NOT CONFIRMATION (9.4 row 3): a C2-only decline cannot be separated from B-HEARD; the interaction arm speaks to it"
    if {k1, k2} == {"pred", "opp"}:
        return "THE CONFIRMATION HAS FAILED (9.4 row 4): the strata reject in opposite directions; both estimates in print"
    if k1 == "no" and k2 == "no":
        return "THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2"
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
    verdicts = {s: read_stratum(d, s, rows, mde) for s in INFERENTIAL}
    concl = conclusion_9_4(verdicts["C1_clean"], verdicts["C2_exposed"])
    rows.append({"stratum": "family", "item": "conclusion_9_4", "value": concl, "rule": "note §9.4 as amended by 23",
                 "detail": f"C1: {verdicts['C1_clean']} | C2: {verdicts['C2_exposed']}"})
    # pooled: descriptive, promised, never overturns a stratum-level disagreement
    pooled = d[(d["stratum"] == "pooled") & (d["family"] == "descriptive")]
    for r in pooled.itertuples():
        rows.append({"stratum": "pooled", "item": f"p_randomization:{r.outcome}:{r.estimator}",
                     "value": f(r.p_randomization), "rule": "note §9.4 (descriptive)",
                     "detail": f"mean coef {f(r.first_week_mean_coef):.6f}; {r.status}"})
    res = pd.DataFrame(rows, columns=["stratum", "item", "value", "rule", "detail"])
    return res, verdicts, concl


def main():
    d, out = load()
    res, verdicts, concl = evaluate(d, power_mdes())
    res["data_source"] = "SYNTHETIC" if ARGS.synthetic else "REAL"
    res.to_csv(out, index=False)
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
