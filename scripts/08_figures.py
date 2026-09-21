"""Publication figures. Reads ONLY saved tables/parquets (REWORK_PLAN §7) —
no estimation happens here, so figures can never disagree with tables.

Style: colorblind-validated palette (blue #2a78d6 primary, violet #4a3aa7
secondary, gray #52514e reference/placebo), thin marks, direct labels,
one axis per panel. Outputs PNG (300dpi) + PDF to outputs/figures/.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from freeze_guard import select_sample
from config import (
    EPISODE_LIST_PRIMARY,
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    DATA_REFERENCE,
    FREEZE_ACTIVE,
    OUTPUTS_FIGURES,
    OUTPUTS_TABLES,
)

OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

BLUE, VIOLET, GRAY, RED = "#2a78d6", "#4a3aa7", "#52514e", "#e34948"
plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 300, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "font.family": "DejaVu Sans",
})


def save(fig, name):
    fig.savefig(OUTPUTS_FIGURES / f"{name}.png", bbox_inches="tight")
    fig.savefig(OUTPUTS_FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"saved {name}")


# ---------------------------------------------------------------------------
# Figure 1: raw outcome and raw treatment in calendar time, episodes marked.
# Raw data comes before any coefficient plot (Wing et al. 2024, Annu Rev Public
# Health, recommendation 1). Two stacked panels sharing an x-axis: the citywide
# mental-health call share on top, the composite awareness index beneath.
# ---------------------------------------------------------------------------
aw = pd.read_parquet(DATA_PROCESSED / "cai_daily.parquet")
aw["date"] = pd.to_datetime(aw["date"])

ep = pd.read_csv(DATA_REFERENCE / EPISODE_LIST_PRIMARY,
                 parse_dates=["start", "end", "peak_date"])
# Discovery episodes whatever the flag says (D8, addendum 26).
ep = ep[ep["period"] == "discovery"]

panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
panel["incident_date"] = pd.to_datetime(panel["incident_date"])
# Figures are a way of examining outcomes, so they are inside the freeze too.
panel = select_sample(panel, where="08_figures", window="discovery")
# The column is `mh_narrow`, not `mh_narrow_calls`. The latter exists only as a
# METRIC LABEL string in 01_build_panel.py's QC output, and this line has been
# raising KeyError on Figure 1 — the first figure — so 08 has never produced
# anything. The suite never caught it because no check runs the figures.
city = (panel.groupby("incident_date")[["mh_narrow", "total_calls"]].sum()
        .assign(share=lambda d: d["mh_narrow"] / d["total_calls"]))
# Plot exactly what select_sample permitted. The previous form widened to the
# FULL panel range once the freeze lifted, which would have drawn discovery
# and confirmation on one axis and called it the confirmation figure.
win = slice(str(city.index.min().date()), str(city.index.max().date()))
city = city.loc[win]
awp = aw.set_index("date").loc[win]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.2), sharex=True,
                               gridspec_kw={"height_ratios": [1, 1], "hspace": 0.12})

ax1.plot(city.index, 100 * city["share"], color=BLUE, lw=0.7)
ax1.set_ylabel("Mental-health share\nof EMS calls (%)")

ax2.plot(awp.index, awp["cai_d"], color="#444444", lw=0.7)
ax2.axhline(0, color="#999999", lw=0.6, ls=":")
ax2.set_ylabel("Composite awareness\nindex (CAI-D, SD units)")

for ax in (ax1, ax2):
    for _, e in ep.iterrows():
        ax.axvspan(e["start"], e["end"] + pd.Timedelta(days=1), color=BLUE, alpha=0.12, lw=0)
    # dashed markers for the two events that confound this outcome series
    for when, lab in ((pd.Timestamp("2020-03-01"), "COVID emergency"),
                      (pd.Timestamp("2021-06-01"), "B-HEARD launch")):
        if awp.index.min() <= when <= awp.index.max():
            ax.axvline(when, color="#b00020", lw=0.9, ls="--")
            if ax is ax1:
                ax.annotate(lab, xy=(when, ax.get_ylim()[1]), xytext=(3, -10),
                            textcoords="offset points", fontsize=7, color="#b00020")

ax1.set_title("Mental-health EMS call share and public attention to police violence, "
              "New York City, %s–%s" % (str(city.index.min().year), str(city.index.max().year)))
ax2.set_xlabel("")
save(fig, "fig1_raw_series")

# ---------------------------------------------------------------------------
# Figure 2: primary IRF with leads (pre-trend region)
# ---------------------------------------------------------------------------
irf = pd.read_csv(OUTPUTS_TABLES / "irf_main.csv").sort_values("k")
ci = 1.96 * irf["se_date_cluster"]

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.axhline(0, color=GRAY, lw=0.8)
ax.axvline(-0.5, color=GRAY, lw=0.8, ls=":")
ax.axvspan(irf["k"].min() - 0.5, -0.5, color=GRAY, alpha=0.08, lw=0)
ax.fill_between(irf["k"], irf["coef"] - ci, irf["coef"] + ci, color=BLUE, alpha=0.18, lw=0)
ax.plot(irf["k"], irf["coef"], color=BLUE, lw=1.6, marker="o", ms=3)
ax.text(-7.5, ax.get_ylim()[1] * 0.92, "leads\n(pre-trend check)", ha="center",
        fontsize=8, color=GRAY)
ax.set_xlabel("Days relative to awareness (negative = awareness in the future)")
ax.set_ylabel("Effect on narrow mental-health\ncall share (per SD of the attention index)")
ax.set_title("Impulse response: awareness and the narrow mental-health call share\n"
             "(95% CI, SEs clustered by date)")
save(fig, "fig2_irf_primary")

# ---------------------------------------------------------------------------
# Figure 3: binned windows, jointly vs alone
# ---------------------------------------------------------------------------
dec = pd.read_csv(OUTPUTS_TABLES / "decomposition_windows.csv")
wn = dec[dec["outcome"] == "mh_narrow_share"].copy()
worder = ["w02", "w35", "w68", "w911", "w1214"]
wlabel = {"w02": "days 0–2", "w35": "days 3–5", "w68": "days 6–8",
          "w911": "days 9–11", "w1214": "days 12–14"}
wn = wn.set_index("window").loc[worder].reset_index()
x = np.arange(len(wn))

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.axhline(0, color=GRAY, lw=0.8)
for dx, (suffix, color, label) in enumerate(
        [("alone", BLUE, "window entered alone"),
         ("joint", VIOLET, "all windows jointly")]):
    ax.errorbar(x + (dx - 0.5) * 0.16, wn[f"coef_{suffix}"],
                yerr=1.96 * wn[f"se_{suffix}"], fmt="o", ms=5, lw=1.4,
                capsize=3, color=color, label=label)
ax.set_xticks(x, [wlabel[w] for w in wn["window"]])
ax.set_ylabel("Effect on narrow mental-health call share")
ax.set_xlabel("Awareness window (days before outcome)")
ax.legend(frameon=False, fontsize=9)
ax.set_title("Narrow mental-health call share by awareness window, discovery period\n"
             "(windows correlate ρ≈0.8; both views shown; 95% CI, date-clustered)")
save(fig, "fig3_windows")

# ---------------------------------------------------------------------------
# Figure 4: decomposition forest (days 3-5 window, all five windows entered jointly —
# the specification the paper's Results report; no p-values are printed, so that the
# figure carries no number the claims register does not)
# ---------------------------------------------------------------------------
order = [("edp_share", "EDP (police co-response)"),
         ("altmen_share", "Other mental-health alerts"),
         ("suicide_jump_share", "Suicide-related"),
         ("od_poison_drug_share", "Overdose / poison / drug"),
         ("injury_share", "Injury (protest channel)"),
         ("cardiac_share", "Cardiac (placebo)"),
         ("asthma_share", "Asthma (placebo)")]
d35 = dec[dec["window"] == "w35"].set_index("outcome")

fig, ax = plt.subplots(figsize=(7, 3.8))
ax.axvline(0, color=GRAY, lw=0.8)
ys = np.arange(len(order))[::-1]
for y_pos, (col, label) in zip(ys, order):
    r = d35.loc[col]
    is_placebo = "placebo" in label
    color = GRAY if is_placebo else (VIOLET if "protest" in label else BLUE)
    ax.errorbar(r["coef_joint"], y_pos, xerr=1.96 * r["se_joint"],
                fmt="o", ms=6, lw=1.6, capsize=3, color=color)
ax.set_yticks(ys, [label for _, label in order])
ax.set_xlabel("Effect of awareness (days 3–5 window) on call-type share")
ax.set_title("Outcome decomposition, days 3–5 window: effect of awareness by call type\n"
             "(each outcome estimated separately, all five windows jointly; 95% CI, date-clustered)")
save(fig, "fig4_decomposition")

# ---------------------------------------------------------------------------
# Figures 6 and 6b: the sealed run's day-by-day coefficient paths (days 0-7),
# read from data/reference/confirmatory_results.csv (the one-shot table; no
# estimation here). One series per panel, so no legend; 95% intervals from the
# path SEs; the first-week mean, which the plan reports as the effect size,
# drawn as a dashed reference. The joint Wald test is on the shape of this
# path, not on its mean, which is why a rejection can carry no direction.
# ---------------------------------------------------------------------------
import json as _json

conf = pd.read_csv(DATA_REFERENCE / "confirmatory_results.csv")
_STRATA = [("C1_clean", "C1 (clean of B-HEARD; 15 episodes)"),
           ("C2_exposed", "C2 (B-HEARD exposed; 30 episodes)")]
_ARMS = [("OLS_share", "share arm", "Change in share"),
         ("PPML_count_offset", "count arm", "Log points (offset on total dispatches)")]


def _path_figure(outcome_share, outcome_count, name, title):
    # One scale per row (sharey="row"), so the C1/C2 contrast the text draws is the
    # contrast on the page; the in-image title is gone, the caption carries it.
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.0), sharex=True, sharey="row")
    for i, (est, arm, ylab) in enumerate(_ARMS):
        outcome = outcome_share if est == "OLS_share" else outcome_count
        for j, (stratum, slab) in enumerate(_STRATA):
            ax = axes[i, j]
            r = conf[(conf["stratum"] == stratum) & (conf["spec"] == "primary")
                     & (conf["outcome"] == outcome) & (conf["estimator"] == est)].iloc[0]
            path = np.array(_json.loads(r["path_coefs"]), dtype=float)
            ses = np.array(_json.loads(r["path_ses"]), dtype=float)
            days = np.arange(len(path))
            ax.axhline(0, color=GRAY, lw=0.8)
            ax.axhline(r["first_week_mean_coef"], color=GRAY, lw=1.0, ls="--")
            ax.errorbar(days, path, yerr=1.96 * ses, fmt="o-", ms=6, lw=1.6,
                        capsize=2.5, color=BLUE, mec="white", mew=1.0)
            ax.set_title(f"{slab}\n{arm}: RI p = {r['p_randomization']:.3f}, "
                         f"BH-adjusted {r['p_bh_adjusted']:.3f}", fontsize=9)
            if j == 0:
                ax.set_ylabel(ylab, fontsize=9, labelpad=8)
            if i == 1:
                ax.set_xlabel("Days since the episode began (day −1 is the reference)")
            ax.set_xticks(days)
            ax.margins(y=0.15)
    fig.tight_layout()
    save(fig, name)


_path_figure("edp_share", "edp", "fig6_conf_paths_edp",
             "Sealed confirmatory run: day-by-day first-week coefficients, EDP outcome (95% CI, date-clustered)")
_path_figure("mh_narrow_share", "mh_narrow", "fig6b_conf_paths_mh",
             "Sealed confirmatory run: day-by-day first-week coefficients, narrow mental-health outcome (95% CI)")

# ---------------------------------------------------------------------------
# Figure 7: the attention index over the whole decade with every adopted episode
# shaded by the stratum whose analysis window holds its start. Treatment side
# only (no outcome is drawn), so it sits outside the freeze; the discovery
# figure above stays as it is.
# ---------------------------------------------------------------------------
from config import CONFIRMATION_ANALYSIS_WINDOWS, DISCOVERY_START, DISCOVERY_END, BHEARD_LAUNCH

ep_all = pd.read_csv(DATA_REFERENCE / EPISODE_LIST_PRIMARY, parse_dates=["start", "end", "peak_date"])
_windows = {"discovery": [(DISCOVERY_START, DISCOVERY_END)],
            "C1": [CONFIRMATION_ANALYSIS_WINDOWS[0], CONFIRMATION_ANALYSIS_WINDOWS[1]],
            "C2": [CONFIRMATION_ANALYSIS_WINDOWS[2]]}
_stratum_color = {"discovery": GRAY, "C1": BLUE, "C2": "#eb6834"}   # validated categorical slots 1 and 2; gray for the explored period


def _stratum_of(start):
    for name, wins in _windows.items():
        if any(pd.Timestamp(a) <= start <= pd.Timestamp(b) for a, b in wins):
            return name
    return None


aw_full = aw[(aw["date"] >= "2015-07-01")].set_index("date")
fig, ax = plt.subplots(figsize=(10, 3.6))
for name, wins in _windows.items():
    for a, b in wins:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=_stratum_color[name], alpha=0.06, lw=0)
ax.plot(aw_full.index, aw_full["cai_d"], color="#0b0b0b", lw=0.6)
seen = set()
for r in ep_all.itertuples():
    st = _stratum_of(r.start)
    if st is None:
        continue
    ax.axvspan(r.start, r.end + pd.Timedelta(days=1), color=_stratum_color[st], alpha=0.35, lw=0,
               label=f"{st} episode" if st not in seen else None)
    seen.add(st)
ax.axvline(pd.Timestamp(BHEARD_LAUNCH), color=GRAY, lw=0.8, ls=":")
ax.set_ylim(top=ax.get_ylim()[1] * 1.18)
ymax = ax.get_ylim()[1]
ax.annotate("B-HEARD launch", xy=(pd.Timestamp(BHEARD_LAUNCH), ymax * 0.62), xytext=(4, 0),
            textcoords="offset points", fontsize=8, color=GRAY)
_label_pos = {"C1": pd.Timestamp("2016-03-01"), "discovery": pd.Timestamp("2018-12-01"), "C2": pd.Timestamp("2023-02-01")}
for name, when in _label_pos.items():
    ax.annotate({"C1": "C1 (clean)", "discovery": "discovery (explored)", "C2": "C2 (B-HEARD exposed)"}[name],
                xy=(when, ymax * 0.93), ha="center", fontsize=8.5, color=_stratum_color[name])
ax.annotate("C1", xy=(pd.Timestamp("2021-03-15"), ymax * 0.93), ha="center", fontsize=8.5, color=_stratum_color["C1"])
ax.set_ylabel("Attention index (SD units)")
ax.set_xlabel("")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=8, frameon=False, ncol=3)
# no in-image title: the paper's caption (Figure 2) defines the index, the shading and the line
save(fig, "fig7_attention_decade")

# ---------------------------------------------------------------------------
# Figure 5: bridge from legacy result to corrected specification
# ---------------------------------------------------------------------------
# FIGURE 5 IS RETIRED, and skipped rather than crashed.
#
# It compared the original specification to the corrected one, step by step. Its
# input, bridge_legacy_to_primary.csv, comes from 03b_bridge_legacy.py, which
# reads awareness_legacy_lags.parquet, which 02_build_awareness.py builds from
# the raw Twitter exports named in config — and those files are NOT in the
# repository. The chain is dead at the source, so this figure cannot be rebuilt
# from a clean clone by anyone, including us.
#
# Its argument is carried instead by 25_zscore_simulation.py, which plants a
# known effect and shows what within-window standardisation does to it. A
# simulation that anyone can re-run is a better exhibit than a comparison
# against a series nobody can obtain.
_bridge = OUTPUTS_TABLES / "bridge_legacy_to_primary.csv"
if not _bridge.exists():
    print("figure 5 skipped: bridge_legacy_to_primary.csv is unbuildable "
          "(the legacy Twitter raw files are not in the repository). The "
          "z-scoring simulation exhibit replaces it.")
    raise SystemExit(0)
br = pd.read_csv(_bridge)
br5 = br.iloc[:5].copy()
steps = ["Original specification\n(z-score, broad MH, CD cluster)",
         "+ cluster SEs by date",
         "+ all lags & leads",
         "+ log awareness\n(removes outlier leverage)",
         "+ narrow MH outcome\n(= corrected primary)"]

fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.axhline(0, color=GRAY, lw=0.8)
x = np.arange(len(br5))
colors = [GRAY, GRAY, GRAY, RED, BLUE]
for i in x:
    ax.errorbar(i, br5.loc[i, "lag7_coef"], yerr=1.96 * br5.loc[i, "lag7_se"],
                fmt="o", ms=6, lw=1.6, capsize=3, color=colors[i])
ax.set_xticks(x, steps, fontsize=8)
ax.set_ylabel("Lag-7 coefficient (95% CI)")
ax.set_title("Why the original lag-7 finding does not survive:\n"
             "one correction at a time from the original to the corrected specification")
save(fig, "fig5_bridge")

print("All figures written to", OUTPUTS_FIGURES)
