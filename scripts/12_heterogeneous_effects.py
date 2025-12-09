"""
Step 12: Heterogeneous Effects Analysis

This script analyzes how the effect of police shooting awareness on mental health
EMS calls varies across community districts based on their demographic characteristics.

Analyses:
1. Models with interaction terms (awareness × demographics)
2. Stratified analysis by demographic quartiles
3. Visualizations of heterogeneous effects
"""

import pandas as pd
import numpy as np
import patsy
import statsmodels.api as sm
from scipy import stats
import matplotlib.pyplot as plt
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"

# Ensure directories exist
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("HETEROGENEOUS EFFECTS ANALYSIS")
print("=" * 80)

# Load merged panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
if not panel_path.exists():
    raise FileNotFoundError(
        f"Merged panel not found: {panel_path}\n"
        f"Please run script 11 first: python scripts/11_merge_demographics.py"
    )

print(f"\nLoading merged panel from: {panel_path}")
df = pd.read_parquet(panel_path)

print(f"Panel shape: {df.shape}")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")
print(f"Community districts: {df['communitydistrict'].nunique()}")

# Filter to usable rows
df_model = df[df["total_calls"] >= 5].copy()
df_model = df_model.dropna(subset=["mh_share", "communitydistrict"])

# Lag variables
lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

df_model = df_model.loc[df_model[lag_cols].notna().any(axis=1)].copy()

print(f"\nModel sample: {len(df_model):,} rows")
print(f"Rows with demographics: {df_model['pct_black'].notna().sum():,}")

# Prepare CD fixed effects
df_model["cd_int"] = pd.to_numeric(df_model["communitydistrict"], errors="coerce")
df_model = df_model.dropna(subset=["cd_int"])
df_model["cd_int"] = df_model["cd_int"].astype("int64")
df_model["cd_str"] = df_model["cd_int"].astype(str)

# ============================================================================
# Analysis 1: Interaction Terms Model
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 1: INTERACTION TERMS MODEL")
print("=" * 80)

# Select demographic variables for interactions
demo_vars_for_interaction = ['pct_black', 'pct_hispanic', 'pct_white', 'pct_asian']
available_demo_vars = [v for v in demo_vars_for_interaction if v in df_model.columns]

print(f"\nUsing demographic variables: {available_demo_vars}")

# Create interaction terms for key lags (0, 1, 7, 14 days)
key_lags = [0, 1, 7, 14]
interaction_lags = [f"awarez_lag{k}" for k in key_lags if f"awarez_lag{k}" in lag_cols]

print(f"\nCreating interactions for lags: {[int(re.search(r'(\d+)', l).group(1)) for l in interaction_lags]}")

# Build formula with interactions
interaction_terms = []
for lag_col in interaction_lags:
    for demo_var in available_demo_vars:
        interaction_col = f"{lag_col}_x_{demo_var}"
        if interaction_col in df_model.columns:
            interaction_terms.append(interaction_col)

formula_parts = [
    "mh_share ~",
    " + ".join(lag_cols),  # Main lag effects
    " + " + " + ".join(interaction_terms) if interaction_terms else "",  # Interactions
    " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"  # Controls
]

formula_interaction = " ".join([p for p in formula_parts if p])

print(f"\nFormula (first 200 chars): {formula_interaction[:200]}...")
print(f"Total terms: {len(formula_interaction.split('+'))}")

# Fit model
y, X = patsy.dmatrices(formula_interaction, data=df_model, return_type="dataframe")
groups = df_model.loc[y.index, "cd_int"].to_numpy(dtype="int64")

print(f"\nFitting model...")
print(f"  Observations: {len(y):,}")
print(f"  Parameters: {X.shape[1]}")

mod_interaction = sm.OLS(y, X, missing="drop").fit(
    cov_type="cluster", cov_kwds={"groups": groups}
)

print(f"  R-squared: {mod_interaction.rsquared:.4f}")

# Extract interaction coefficients
print("\n" + "=" * 80)
print("INTERACTION COEFFICIENTS")
print("=" * 80)

interaction_results = []
for interaction_col in interaction_terms:
    if interaction_col in mod_interaction.params.index:
        coef = mod_interaction.params[interaction_col]
        try:
            se = mod_interaction.bse[interaction_col]
            if pd.isna(se) or se == 0:
                se = np.nan
        except (KeyError, AttributeError):
            se = np.nan
        
        # Parse lag and demographic variable
        match = re.match(r"awarez_lag(\d+)_x_(.+)", interaction_col)
        if match:
            lag = int(match.group(1))
            demo_var = match.group(2)
            
            interaction_results.append({
                'lag': lag,
                'demographic': demo_var,
                'coefficient': coef,
                'se': se,
                't_stat': coef / se if not pd.isna(se) and se > 0 else np.nan,
                'p_value': 2 * (1 - stats.norm.cdf(abs(coef/se))) if not pd.isna(se) and se > 0 else np.nan
            })

df_interactions = pd.DataFrame(interaction_results)
if len(df_interactions) > 0:
    df_interactions = df_interactions.sort_values(['demographic', 'lag'])
    print("\nInteraction Effects:")
    print(df_interactions.to_string(index=False))
    
    # Save
    interaction_output = OUTPUTS_TABLES / "heterogeneous_effects_interactions.csv"
    df_interactions.to_csv(interaction_output, index=False)
    print(f"\n✓ Saved to: {interaction_output}")
else:
    print("\n⚠️  No interaction coefficients found")

# ============================================================================
# Analysis 2: Stratified Analysis by Quartiles
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 2: STRATIFIED ANALYSIS BY DEMOGRAPHIC QUARTILES")
print("=" * 80)

stratified_results = []

for demo_var in available_demo_vars:
    quartile_col = f"{demo_var}_quartile"
    
    if quartile_col not in df_model.columns:
        print(f"\n⚠️  {quartile_col} not found, skipping stratified analysis for {demo_var}")
        continue
    
    print(f"\nAnalyzing by {demo_var} quartiles...")
    
    for quartile in ['Q1', 'Q2', 'Q3', 'Q4']:
        df_strat = df_model[df_model[quartile_col] == quartile].copy()
        
        if len(df_strat) < 100:
            print(f"  {quartile}: Insufficient data ({len(df_strat)} rows), skipping")
            continue
        
        # Run model for this quartile
        formula_strat = (
            "mh_share ~ "
            + " + ".join(lag_cols)
            + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
        )
        
        y_strat, X_strat = patsy.dmatrices(formula_strat, data=df_strat, return_type="dataframe")
        groups_strat = df_strat.loc[y_strat.index, "cd_int"].to_numpy(dtype="int64")
        
        mod_strat = sm.OLS(y_strat, X_strat, missing="drop").fit(
            cov_type="cluster", cov_kwds={"groups": groups_strat}
        )
        
        # Extract lag 7 coefficient (key finding from main analysis)
        lag7_col = "awarez_lag7"
        if lag7_col in mod_strat.params.index:
            coef = mod_strat.params[lag7_col]
            try:
                se = mod_strat.bse[lag7_col]
                if pd.isna(se) or se == 0:
                    se = np.nan
            except:
                se = np.nan
            
            stratified_results.append({
                'demographic': demo_var,
                'quartile': quartile,
                'n_obs': len(y_strat),
                'lag7_coef': coef,
                'lag7_se': se,
                'lag7_ci_low': coef - 1.96 * se if not pd.isna(se) and se > 0 else np.nan,
                'lag7_ci_hi': coef + 1.96 * se if not pd.isna(se) and se > 0 else np.nan,
            })
            
            se_str = f"{se:.6f}" if not pd.isna(se) and se > 0 else "NaN"
            print(f"  {quartile}: coef={coef:.6f}, se={se_str}, n={len(y_strat):,}")

df_stratified = pd.DataFrame(stratified_results)
if len(df_stratified) > 0:
    stratified_output = OUTPUTS_TABLES / "heterogeneous_effects_stratified.csv"
    df_stratified.to_csv(stratified_output, index=False)
    print(f"\n✓ Saved stratified results to: {stratified_output}")

# ============================================================================
# Visualization: Stratified Effects
# ============================================================================

print("\n" + "=" * 80)
print("CREATING VISUALIZATIONS")
print("=" * 80)

if len(df_stratified) > 0:
    # Plot stratified effects for each demographic
    for demo_var in available_demo_vars:
        df_plot = df_stratified[df_stratified['demographic'] == demo_var].copy()
        
        if len(df_plot) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        quartiles = ['Q1', 'Q2', 'Q3', 'Q4']
        x_pos = np.arange(len(quartiles))
        coefs = []
        ci_lows = []
        ci_his = []
        
        for q in quartiles:
            row = df_plot[df_plot['quartile'] == q]
            if len(row) > 0:
                coefs.append(row.iloc[0]['lag7_coef'])
                ci_lows.append(row.iloc[0]['lag7_ci_low'])
                ci_his.append(row.iloc[0]['lag7_ci_hi'])
            else:
                coefs.append(np.nan)
                ci_lows.append(np.nan)
                ci_his.append(np.nan)
        
        # Plot coefficients
        ax.bar(x_pos, coefs, alpha=0.7, color='steelblue', label='Coefficient')
        
        # Plot confidence intervals
        has_ci = [not (pd.isna(lo) or pd.isna(hi)) for lo, hi in zip(ci_lows, ci_his)]
        if any(has_ci):
            errors_low = [c - lo if not pd.isna(lo) else 0 for c, lo in zip(coefs, ci_lows)]
            errors_hi = [hi - c if not pd.isna(hi) else 0 for c, hi in zip(coefs, ci_his)]
            ax.errorbar(x_pos, coefs, yerr=[errors_low, errors_hi], 
                       fmt='none', color='black', capsize=5, capthick=2)
        
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(quartiles)
        ax.set_xlabel(f'{demo_var.replace("pct_", "% ").title()} Quartile', fontsize=12)
        ax.set_ylabel('Effect on mh_share (7-day lag)', fontsize=12)
        ax.set_title(f'Heterogeneous Effects by {demo_var.replace("pct_", "% ").title()}\n7-Day Lag Coefficient', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend()
        
        plt.tight_layout()
        
        plot_path = OUTPUTS_FIGURES / f"heterogeneous_effects_{demo_var}.png"
        plt.savefig(plot_path, dpi=180, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved plot: {plot_path}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

print(f"\nResults saved:")
print(f"  - Interaction effects: {OUTPUTS_TABLES / 'heterogeneous_effects_interactions.csv'}")
print(f"  - Stratified analysis: {OUTPUTS_TABLES / 'heterogeneous_effects_stratified.csv'}")
print(f"  - Visualizations: {OUTPUTS_FIGURES / 'heterogeneous_effects_*.png'}")

print("\n" + "=" * 80)

