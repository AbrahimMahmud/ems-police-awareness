"""Core estimation: full impulse response with corrected inference (REWORK_PLAN I1, I3, I6).

Primary specification (docs/PRE_ANALYSIS_NOTE.md):
    mh_narrow_share ~ aware_log lags 0..28 + leads 1..14
                      | CD FE + day-of-week FE + month x year FE
    sample: 2017-2020, 59 CDs, total_calls >= 5, all lags/leads observed
    primary inference: SEs clustered by DATE
    primary test: joint Wald test that lag-0..7 coefficients are all zero

Outputs (outputs/tables/):
    irf_main.csv              every lag/lead coefficient with SEs and p-values under
                              four vcov estimators: CD cluster (legacy), date cluster
                              (primary), two-way CD x date, Driscoll-Kraay
    irf_main_bh.csv           lag coefficients with Benjamini-Hochberg adjusted p (date-clustered)
    joint_tests.csv           joint Wald tests (lags 0-7, all lags, all leads) under each vcov
    se_comparison.csv         lag-7 row of the four-way SE table (headline comparison)
    irf_windows.csv           rolling-window (binned) IRF, date-clustered
    progressive_controls.csv  controls added one at a time (meeting note), date-clustered
Usage:
    python 03_main_model.py [--outcome mh_narrow_share] [--aware aware_log]
"""

import argparse

import numpy as np
import pandas as pd
import pyfixest as pf
import statsmodels.api as sm
from scipy import stats

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DATA_PROCESSED,
    LAGS,
    LEADS,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    PRIMARY_AWARENESS,
    ROLLING_WINDOWS,
)

parser = argparse.ArgumentParser()
parser.add_argument("--outcome", default="mh_narrow_share")
parser.add_argument("--aware", default=PRIMARY_AWARENESS)
args = parser.parse_args()
OUTCOME, AWARE = args.outcome, args.aware

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Assemble estimation sample
# ---------------------------------------------------------------------------
panel = pd.read_parquet(DATA_PROCESSED / "panel_cd_day.parquet")
lags = pd.read_parquet(DATA_PROCESSED / "awareness_lags.parquet")

lag_cols = [f"{AWARE}_lag{k}" for k in LAGS]
lead_cols = [f"{AWARE}_lead{j}" for j in LEADS]
win_cols = [f"{PRIMARY_AWARENESS}_w{lo}{hi}" for lo, hi in ROLLING_WINDOWS]
keep = ["date"] + lag_cols + lead_cols + [c for c in win_cols if c in lags.columns]

df = panel.merge(lags[keep], left_on="incident_date", right_on="date", how="left")
df = df[df["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
df = df[df["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]
df = df.dropna(subset=[OUTCOME] + lag_cols + lead_cols)
df["month_year"] = df["year"] * 100 + df["month"]
df["date_id"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)

print(f"Estimation sample: {len(df):,} CD-days, {df['communitydistrict'].nunique()} districts, "
      f"{df['incident_date'].nunique()} dates "
      f"({df['incident_date'].min().date()} -> {df['incident_date'].max().date()})")

rhs = " + ".join(lag_cols + lead_cols)
fml = f"{OUTCOME} ~ {rhs} | communitydistrict + dow + month_year"

# ---------------------------------------------------------------------------
# Fit under three pyfixest vcovs + Driscoll-Kraay via statsmodels
# ---------------------------------------------------------------------------
VCOVS = {
    "cd_cluster": {"CRV1": "communitydistrict"},
    "date_cluster": {"CRV1": "date_id"},
    "twoway": {"CRV1": "communitydistrict+date_id"},
}
fits = {name: pf.feols(fml, df, vcov=v) for name, v in VCOVS.items()}

# Driscoll-Kraay: statsmodels OLS on the same design with absorbed FEs as dummies.
X = pd.get_dummies(
    df[lag_cols + lead_cols + ["communitydistrict", "dow", "month_year"]],
    columns=["communitydistrict", "dow", "month_year"], drop_first=True, dtype=float,
)
X = sm.add_constant(X)
dk_maxlags = 14  # serial correlation horizon; matches lead window
mod_dk = sm.OLS(df[OUTCOME].to_numpy(), X).fit(
    cov_type="nw-groupsum",
    cov_kwds={"time": pd.factorize(df["date_id"])[0], "maxlags": dk_maxlags},
)

# ---------------------------------------------------------------------------
# IRF table: coefficient identical across columns, SEs differ
# ---------------------------------------------------------------------------
terms = lag_cols + lead_cols
rows = []
for t in terms:
    k = int(t.split("lag")[-1]) if "_lag" in t else -int(t.split("lead")[-1])
    row = {"term": t, "k": k, "coef": fits["date_cluster"].coef()[t]}
    for name, m in fits.items():
        row[f"se_{name}"] = m.se()[t]
        row[f"p_{name}"] = m.pvalue()[t]
    row["se_dk"] = mod_dk.bse[t]
    row["p_dk"] = mod_dk.pvalues[t]
    rows.append(row)
irf = pd.DataFrame(rows).sort_values("k").reset_index(drop=True)
irf.to_csv(OUTPUTS_TABLES / "irf_main.csv", index=False)

# BH adjustment across the 29 lag p-values (primary inference: date cluster)
lag_mask = irf["k"] >= 0
pvals = irf.loc[lag_mask, "p_date_cluster"].to_numpy()
order = np.argsort(pvals)
bh = np.empty_like(pvals)
n = len(pvals)
prev = 1.0
for rank_from_end, idx in enumerate(order[::-1]):
    rank = n - rank_from_end
    prev = min(prev, pvals[idx] * n / rank)
    bh[idx] = prev
irf_bh = irf.loc[lag_mask, ["term", "k", "coef", "se_date_cluster", "p_date_cluster"]].copy()
irf_bh["p_bh"] = bh
irf_bh.to_csv(OUTPUTS_TABLES / "irf_main_bh.csv", index=False)

# ---------------------------------------------------------------------------
# Joint Wald tests under each vcov
# ---------------------------------------------------------------------------
def wald(coefs: pd.Series, vcov: pd.DataFrame, names: list, n_clusters: int) -> dict:
    """Eigenvalue-truncated Wald test with a small-cluster F correction.

    Two-way clustered vcovs need not be positive semi-definite, and blocks of
    highly collinear lag terms make V near-singular, which turns the naive
    chi-square Wald test anti-conservative (verified on synthetic null data).
    We therefore (a) work in the eigenspace of V, dropping eigenvalues below
    tol * max_eigenvalue (generalized/pseudo-inverse Wald with effective rank
    q_eff), and (b) refer W/q_eff to an F(q_eff, G-1) distribution, the standard
    finite-cluster correction.
    """
    b = coefs.loc[names].to_numpy()
    V = vcov.loc[names, names].to_numpy()
    V = (V + V.T) / 2
    eigval, eigvec = np.linalg.eigh(V)
    tol = 1e-9 * eigval.max()
    keep = eigval > tol
    q_eff = int(keep.sum())
    b_rot = eigvec.T @ b
    stat = float((b_rot[keep] ** 2 / eigval[keep]).sum())
    f_stat = stat / q_eff
    p = 1 - stats.f.cdf(f_stat, q_eff, max(n_clusters - 1, 1))
    return {"W": round(stat, 2), "q_eff": q_eff, "q_nominal": len(names),
            "F": round(f_stat, 3), "p": p}


# Synthetic-null validation (see commit history): Wald tests with many collinear
# restrictions (all_lags q=29, all_leads q=14) over-reject even under the null,
# under every vcov. They are kept as labeled diagnostics only. The PRIMARY test
# (lags 0-7, q=8) and the 1-df mean-of-leads pre-trend test are well behaved.
test_sets = {
    "lags_0_7 [PRIMARY]": [f"{AWARE}_lag{k}" for k in range(0, 8)],
    "all_lags [DIAGNOSTIC: over-rejects under null]": lag_cols,
    "all_leads [DIAGNOSTIC: over-rejects under null]": lead_cols,
}


def mean_leads_test(coefs: pd.Series, vcov: pd.DataFrame, n_clusters: int) -> dict:
    """1-df pre-trend test: average lead coefficient = 0 (well-conditioned)."""
    c = pd.Series(0.0, index=coefs.index)
    c.loc[lead_cols] = 1.0 / len(lead_cols)
    est = float(c @ coefs)
    se = float(np.sqrt(c @ vcov.loc[c.index, c.index].to_numpy() @ c))
    t = est / se
    p = 2 * (1 - stats.t.cdf(abs(t), max(n_clusters - 1, 1)))
    return {"W": round(t ** 2, 2), "q_eff": 1, "q_nominal": 1, "F": round(t ** 2, 3), "p": p}
G = {"cd_cluster": df["communitydistrict"].nunique(),
     "date_cluster": df["incident_date"].nunique(),
     "twoway": df["communitydistrict"].nunique(),  # min of the two dimensions
     "driscoll_kraay": df["incident_date"].nunique()}
jt_rows = []
for test_name, names in test_sets.items():
    for vc_name, m in fits.items():
        V = pd.DataFrame(m._vcov, index=m._coefnames, columns=m._coefnames)
        res = wald(m.coef(), V, names, G[vc_name])
        jt_rows.append({"test": test_name, "vcov": vc_name, **res})
    Vdk = pd.DataFrame(mod_dk.cov_params(), index=mod_dk.params.index,
                       columns=mod_dk.params.index)
    res = wald(mod_dk.params, Vdk, names, G["driscoll_kraay"])
    jt_rows.append({"test": test_name, "vcov": "driscoll_kraay", **res})

for vc_name, m in fits.items():
    V = pd.DataFrame(m._vcov, index=m._coefnames, columns=m._coefnames)
    res = mean_leads_test(m.coef(), V, G[vc_name])
    jt_rows.append({"test": "mean_leads (pretrend, 1df)", "vcov": vc_name, **res})
Vdk = pd.DataFrame(mod_dk.cov_params(), index=mod_dk.params.index,
                   columns=mod_dk.params.index)
res = mean_leads_test(mod_dk.params, Vdk, G["driscoll_kraay"])
jt_rows.append({"test": "mean_leads (pretrend, 1df)", "vcov": "driscoll_kraay", **res})
joint = pd.DataFrame(jt_rows)
joint.to_csv(OUTPUTS_TABLES / "joint_tests.csv", index=False)

# Headline four-way comparison at lag 7 (continuity with the original paper)
lag7 = irf[irf["k"] == 7].iloc[0]
se_cmp = pd.DataFrame([{
    "coef_lag7": lag7["coef"],
    "se_cd_cluster": lag7["se_cd_cluster"], "p_cd_cluster": lag7["p_cd_cluster"],
    "se_date_cluster": lag7["se_date_cluster"], "p_date_cluster": lag7["p_date_cluster"],
    "se_twoway": lag7["se_twoway"], "p_twoway": lag7["p_twoway"],
    "se_dk": lag7["se_dk"], "p_dk": lag7["p_dk"],
    "n_obs": len(df), "n_dates": df["incident_date"].nunique(),
}])
se_cmp.to_csv(OUTPUTS_TABLES / "se_comparison.csv", index=False)

# ---------------------------------------------------------------------------
# Rolling-window (binned) IRF — meeting note
# ---------------------------------------------------------------------------
have_wins = [c for c in win_cols if c in df.columns]
if AWARE == PRIMARY_AWARENESS and have_wins:
    fml_w = f"{OUTCOME} ~ {' + '.join(have_wins)} | communitydistrict + dow + month_year"
    m_w = pf.feols(fml_w, df.dropna(subset=have_wins), vcov={"CRV1": "date_id"})
    wtab = pd.DataFrame({"term": have_wins,
                         "coef": [m_w.coef()[c] for c in have_wins],
                         "se_date_cluster": [m_w.se()[c] for c in have_wins],
                         "p_date_cluster": [m_w.pvalue()[c] for c in have_wins]})
    wtab.to_csv(OUTPUTS_TABLES / "irf_windows.csv", index=False)

# ---------------------------------------------------------------------------
# Progressive controls (meeting note), date-clustered throughout
# ---------------------------------------------------------------------------
prog_specs = {
    "1_awareness_only": f"{OUTCOME} ~ {rhs}",
    "2_plus_dow": f"{OUTCOME} ~ {rhs} | dow",
    "3_plus_month_year": f"{OUTCOME} ~ {rhs} | dow + month_year",
    "4_plus_cd_fe": fml,
}
prog_rows = []
for name, f_ in prog_specs.items():
    m = pf.feols(f_, df, vcov={"CRV1": "date_id"})
    V = pd.DataFrame(m._vcov, index=m._coefnames, columns=m._coefnames)
    res = wald(m.coef(), V, test_sets["lags_0_7 [PRIMARY]"], G["date_cluster"])
    prog_rows.append({"model": name,
                      "lag7_coef": m.coef()[f"{AWARE}_lag7"],
                      "lag7_se": m.se()[f"{AWARE}_lag7"],
                      "joint_lags07_p": res["p"],
                      "r2": m._r2})
prog = pd.DataFrame(prog_rows)
prog.to_csv(OUTPUTS_TABLES / "progressive_controls.csv", index=False)

# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------
print("\n=== Four-way SE comparison at lag 7 ===")
print(se_cmp.T.to_string(header=False))
print("\n=== Joint tests ===")
print(joint.to_string(index=False))
print("\n=== Progressive controls (lag 7, date-clustered) ===")
print(prog.to_string(index=False))
sig_leads = int((irf.loc[irf['k'] < 0, 'p_date_cluster'] < 0.05).sum())
print(f"\nLeads significant at 5% (date-clustered): {sig_leads}/{len(LEADS)} "
      f"(expect ~{round(0.05*len(LEADS))} under no pre-trend)")
