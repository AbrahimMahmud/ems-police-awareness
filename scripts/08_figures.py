"""Publication figures. Reads ONLY saved tables/parquets (REWORK_PLAN §7) —
no estimation happens here, so figures can never disagree with tables.

Style: colorblind-validated palette (blue #2a78d6 primary, violet #4a3aa7
secondary, gray #52514e reference/placebo), thin marks, direct labels,
one axis per panel. Outputs PNG (300dpi) + PDF to outputs/figures/.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DATA_PROCESSED, OUTPUTS_FIGURES, OUTPUTS_TABLES

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
# Figure 1: awareness series with episodes (data section)
# ---------------------------------------------------------------------------
aw = pd.read_parquet(DATA_PROCESSED / "awareness_daily.parquet")
ep = pd.read_csv(OUTPUTS_TABLES / "awareness_episodes.csv", parse_dates=["start", "end", "peak_date"])

fig, ax = plt.subplots(figsize=(9, 3.2))
ax.plot(aw["date"], aw["tweet_count"], color=BLUE, lw=0.8)
ax.set_yscale("log")
ax.set_ylabel("Daily tweets (log scale)")
for _, e in ep.iterrows():
    ax.axvspan(e["start"], e["end"] + pd.Timedelta(days=1), color=BLUE, alpha=0.12, lw=0)
label_eps = ep.nlargest(6, "peak_z").drop_duplicates("top_victim").nlargest(4, "peak_z")
for _, e in label_eps.iterrows():
    ax.annotate(e["top_victim"], xy=(e["peak_date"], e["peak_tweets"]),
                xytext=(0, 6), textcoords="offset points",
                ha="center", fontsize=8, color="#0b0b0b")
ax.set_ylim(top=aw["tweet_count"].max() * 6)
ax.set_title("Public awareness of police killings, 2017–2020 (shaded: high-awareness episodes)")
save(fig, "fig1_awareness_series")

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
ax.set_ylabel("Effect on narrow mental-health\ncall share (per log-point awareness)")
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
ax.set_title("Early-week decline in mental-health call share after awareness\n"
             "(windows correlate ρ≈0.8; both views shown; 95% CI, date-clustered)")
save(fig, "fig3_windows")

# ---------------------------------------------------------------------------
# Figure 4: decomposition forest (days 3-5 window, alone)
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
    ax.errorbar(r["coef_alone"], y_pos, xerr=1.96 * r["se_alone"],
                fmt="o", ms=6, lw=1.6, capsize=3, color=color)
    if r["p_alone"] < 0.1:
        ax.annotate(f"p={r['p_alone']:.3f}", xy=(r["coef_alone"], y_pos),
                    xytext=(0, 7), textcoords="offset points", ha="center",
                    fontsize=8, color=color)
ax.set_yticks(ys, [label for _, label in order])
ax.set_xlabel("Effect of awareness (days 3–5 window) on call-type share")
ax.set_title("The decline is specific to police-adjacent mental-health calls\n"
             "(each outcome estimated separately; 95% CI, date-clustered)")
save(fig, "fig4_decomposition")

# ---------------------------------------------------------------------------
# Figure 5: bridge from legacy result to corrected specification
# ---------------------------------------------------------------------------
br = pd.read_csv(OUTPUTS_TABLES / "bridge_legacy_to_primary.csv")
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
