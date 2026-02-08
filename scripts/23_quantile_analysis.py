"""
Step 23: Quantile-Based Analysis

This script splits awareness into quintiles to examine non-linear effects and
compare MH call patterns across different levels of awareness.

Method:
- Split awareness into quintiles (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
- Compare MH call patterns across quantiles
- Create box plots showing distributions
- Run regressions within each quantile
- Examine interaction effects between quantiles and demographics
"""

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("QUANTILE-BASED ANALYSIS")
print("=" * 80)

# Load panel
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
df = pd.read_parquet(panel_path)
df["incident_date"] = pd.to_datetime(df["incident_date"])

print(f"\nLoaded panel: {len(df):,} rows")
print(f"Date range: {df['incident_date'].min()} to {df['incident_date'].max()}")

# Filter to analysis sample
df_analysis = df[(df["total_calls"] >= 5) & df["mh_share"].notna()].copy()
print(f"Analysis sample: {len(df_analysis):,} rows")

# Create awareness quantiles
print("\n" + "=" * 80)
print("CREATING AWARENESS QUINTILES")
print("=" * 80)

# Use awareness_z for quantiles
df_analysis = df_analysis[df_analysis["awareness_z"].notna()].copy()

# Create quintiles
df_analysis['awareness_quantile'], quantile_bins = pd.qcut(
    df_analysis['awareness_z'], 
    q=5, 
    labels=['0-20', '20-40', '40-60', '60-80', '80-100'],
    retbins=True,
    duplicates='drop'
)

print(f"Quantile distribution:")
print(df_analysis['awareness_quantile'].value_counts().sort_index())

print(f"\nQuantile boundaries:")
for i, (label, low, high) in enumerate(zip(['0-20', '20-40', '40-60', '60-80', '80-100'], 
                                            quantile_bins[:-1], quantile_bins[1:])):
    print(f"  {label}: [{low:.3f}, {high:.3f}]")

# ============================================================================
# Analysis 1: Descriptive Statistics by Quantile
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 1: DESCRIPTIVE STATISTICS BY QUANTILE")
print("=" * 80)

quantile_stats = df_analysis.groupby('awareness_quantile').agg({
    'mh_share': ['mean', 'std', 'count'],
    'mh_calls': ['mean', 'std'],
    'total_calls': ['mean', 'std'],
    'awareness_z': ['mean', 'std']
}).round(6)

print("\nSummary statistics by quantile:")
print(quantile_stats)

# Save descriptive stats
quantile_stats_out = OUTPUTS_TABLES / "quantile_analysis_descriptive_stats.csv"
quantile_stats.to_csv(quantile_stats_out)
print(f"\n✓ Saved descriptive statistics to: {quantile_stats_out}")

# ============================================================================
# Analysis 2: Box Plots
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 2: BOX PLOTS BY QUANTILE")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Box plot 1: mh_share by quantile (with individual data points)
ax1 = axes[0, 0]
quantile_data = [df_analysis[df_analysis['awareness_quantile'] == q]['mh_share'].dropna() 
                  for q in ['0-20', '20-40', '40-60', '60-80', '80-100']]
bp1 = ax1.boxplot(quantile_data, labels=['0-20', '20-40', '40-60', '60-80', '80-100'], 
                  patch_artist=True, showmeans=True)
# Color the boxes
for patch in bp1['boxes']:
    patch.set_facecolor('lightblue')
    patch.set_alpha(0.7)

# Add individual data points (dots) to show distribution
for i, (q, data) in enumerate(zip(['0-20', '20-40', '40-60', '60-80', '80-100'], quantile_data)):
    # Jitter x positions slightly to avoid overlap
    x_jittered = np.random.normal(i+1, 0.04, size=len(data))
    ax1.scatter(x_jittered, data, alpha=0.2, s=8, color='darkblue', zorder=3)

ax1.set_xlabel('Awareness Quantile', fontsize=11)
ax1.set_ylabel('mh_share', fontsize=11)
ax1.set_title('Distribution of mh_share by Awareness Quantile\n(Box: quartiles, Dots: individual observations)', 
              fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# Box plot 2: mh_calls by quantile (with individual data points)
ax2 = axes[0, 1]
quantile_data_calls = [df_analysis[df_analysis['awareness_quantile'] == q]['mh_calls'].dropna() 
                       for q in ['0-20', '20-40', '40-60', '60-80', '80-100']]
bp2 = ax2.boxplot(quantile_data_calls, labels=['0-20', '20-40', '40-60', '60-80', '80-100'],
                  patch_artist=True, showmeans=True)
# Color the boxes
for patch in bp2['boxes']:
    patch.set_facecolor('lightcoral')
    patch.set_alpha(0.7)

# Add individual data points (dots) to show distribution
for i, (q, data) in enumerate(zip(['0-20', '20-40', '40-60', '60-80', '80-100'], quantile_data_calls)):
    # Jitter x positions slightly to avoid overlap
    x_jittered = np.random.normal(i+1, 0.04, size=len(data))
    ax2.scatter(x_jittered, data, alpha=0.2, s=8, color='darkred', zorder=3)

ax2.set_xlabel('Awareness Quantile', fontsize=11)
ax2.set_ylabel('mh_calls', fontsize=11)
ax2.set_title('Distribution of mh_calls by Awareness Quantile\n(Box: quartiles, Dots: individual observations)', 
              fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

# Box plot 3: Mean mh_share by quantile (bar chart)
ax3 = axes[1, 0]
mean_by_quantile = df_analysis.groupby('awareness_quantile')['mh_share'].mean()
ax3.bar(range(len(mean_by_quantile)), mean_by_quantile.values, alpha=0.7, color='steelblue')
ax3.set_xticks(range(len(mean_by_quantile)))
ax3.set_xticklabels(mean_by_quantile.index)
ax3.set_xlabel('Awareness Quantile', fontsize=11)
ax3.set_ylabel('Mean mh_share', fontsize=11)
ax3.set_title('Mean mh_share by Awareness Quantile', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# Box plot 4: Scatter of awareness_z vs mh_share (colored by quantile)
ax4 = axes[1, 1]
for q, color in zip(['0-20', '20-40', '40-60', '60-80', '80-100'], 
                     ['blue', 'green', 'orange', 'red', 'purple']):
    df_q = df_analysis[df_analysis['awareness_quantile'] == q]
    ax4.scatter(df_q['awareness_z'], df_q['mh_share'], alpha=0.2, s=8, label=q, color=color)
ax4.set_xlabel('Awareness (z-score)', fontsize=11)
ax4.set_ylabel('mh_share', fontsize=11)
ax4.set_title('Relationship: Awareness vs mh_share\n(Dots: individual observations, colored by quantile)', 
              fontsize=12, fontweight='bold')
ax4.legend(title='Quantile', fontsize=9, loc='upper left')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
boxplot_out = OUTPUTS_FIGURES / "quantile_boxplots.png"
plt.savefig(boxplot_out, dpi=180, bbox_inches='tight')
plt.close()

print(f"✓ Saved box plots to: {boxplot_out}")

# ============================================================================
# Analysis 3: Regressions Within Each Quantile
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 3: REGRESSIONS WITHIN EACH QUANTILE")
print("=" * 80)

lag_use = [0, 1, 2, 3, 7, 14, 21, 28]
lag_cols = [f"awarez_lag{k}" for k in lag_use]

# Prepare CD fixed effects
df_analysis["cd_int"] = pd.to_numeric(df_analysis["communitydistrict"], errors="coerce")
df_analysis = df_analysis.dropna(subset=["cd_int"])
df_analysis["cd_int"] = df_analysis["cd_int"].astype("int64")
df_analysis["cd_str"] = df_analysis["cd_int"].astype(str)

# Ensure date variables
if "dow" not in df_analysis.columns:
    df_analysis["dow"] = df_analysis["incident_date"].dt.dayofweek
if "month" not in df_analysis.columns:
    df_analysis["month"] = df_analysis["incident_date"].dt.month
if "year" not in df_analysis.columns:
    df_analysis["year"] = df_analysis["incident_date"].dt.year

quantile_regression_results = []

for quantile in ['0-20', '20-40', '40-60', '60-80', '80-100']:
    df_quant = df_analysis[df_analysis['awareness_quantile'] == quantile].copy()
    df_quant = df_quant.loc[df_quant[lag_cols].notna().any(axis=1)].copy()
    
    if len(df_quant) < 100:
        print(f"\n⚠️  {quantile}: Insufficient data ({len(df_quant)} rows), skipping")
        continue
    
    print(f"\n{quantile} quantile: {len(df_quant):,} observations")
    
    formula_quant = "mh_share ~ " + " + ".join(lag_cols) + " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
    y_quant, X_quant = patsy.dmatrices(formula_quant, data=df_quant, return_type="dataframe")
    groups_quant = df_quant.loc[y_quant.index, "cd_int"].to_numpy(dtype="int64")
    
    mod_quant = sm.OLS(y_quant, X_quant, missing="drop").fit(
        cov_type="cluster",
        cov_kwds={"groups": groups_quant}
    )
    
    print(f"  R-squared: {mod_quant.rsquared:.4f}")
    
    # Extract lag 7 coefficient
    if "awarez_lag7" in mod_quant.params.index:
        coef = mod_quant.params["awarez_lag7"]
        se = mod_quant.bse["awarez_lag7"]
        print(f"  Lag 7 coefficient: {coef:.6f} (SE: {se:.6f})")
        
        quantile_regression_results.append({
            'quantile': quantile,
            'n_obs': int(mod_quant.nobs),
            'r_squared': mod_quant.rsquared,
            'lag7_coef': coef,
            'lag7_se': se,
            'lag7_ci_low': coef - 1.96 * se,
            'lag7_ci_hi': coef + 1.96 * se
        })

if quantile_regression_results:
    df_quant_reg = pd.DataFrame(quantile_regression_results)
    quantile_reg_out = OUTPUTS_TABLES / "quantile_analysis_regression_results.csv"
    df_quant_reg.to_csv(quantile_reg_out, index=False)
    print(f"\n✓ Saved regression results to: {quantile_reg_out}")
    
    print("\nLag 7 Coefficients by Quantile:")
    print(df_quant_reg[['quantile', 'lag7_coef', 'lag7_se', 'n_obs']].to_string(index=False))

# ============================================================================
# Analysis 4: Interaction Effects with Demographics
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS 4: INTERACTION EFFECTS WITH DEMOGRAPHICS")
print("=" * 80)

# Check if demographics are available
demo_path = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
if demo_path.exists():
    print("Loading demographics...")
    df_demo = pd.read_parquet(demo_path)
    
    # Merge demographics (take first row per CD for time-invariant values)
    demo_cols = [c for c in df_demo.columns 
                 if c not in df_analysis.columns or c == "communitydistrict"]
    if demo_cols:
        df_demo_unique = df_demo[["communitydistrict"] + 
                                 [c for c in demo_cols if c != "communitydistrict"]].drop_duplicates(
            subset=["communitydistrict"]
        )
        df_analysis = df_analysis.merge(df_demo_unique, on="communitydistrict", how="left")
        
        # Create interaction: quantile × demographics
        available_demos = ['pct_black', 'pct_hispanic', 'pct_white', 'pct_asian']
        available_demos = [d for d in available_demos if d in df_analysis.columns]
        
        if available_demos:
            print(f"Creating interactions with: {available_demos}")
            
            # Create dummy variables for top quantile
            df_analysis['top_quantile'] = (df_analysis['awareness_quantile'] == '80-100').astype(int)
            
            # Run regression with interactions
            interaction_terms = []
            for demo in available_demos:
                interaction_col = f"top_quantile_x_{demo}"
                df_analysis[interaction_col] = df_analysis['top_quantile'] * df_analysis[demo]
                interaction_terms.append(interaction_col)
            
            if interaction_terms:
                formula_interaction = (
                    "mh_share ~ " + " + ".join(lag_cols) + 
                    " + top_quantile + " + " + ".join(available_demos) + 
                    " + " + " + ".join(interaction_terms) +
                    " + C(dow) + C(month):C(year) + is_holiday + C(cd_str)"
                )
                
                df_interaction = df_analysis.loc[df_analysis[lag_cols].notna().any(axis=1)].copy()
                y_int, X_int = patsy.dmatrices(formula_interaction, data=df_interaction, return_type="dataframe")
                groups_int = df_interaction.loc[y_int.index, "cd_int"].to_numpy(dtype="int64")
                
                mod_interaction = sm.OLS(y_int, X_int, missing="drop").fit(
                    cov_type="cluster",
                    cov_kwds={"groups": groups_int}
                )
                
                print(f"  Observations: {int(mod_interaction.nobs):,}")
                print(f"  R-squared: {mod_interaction.rsquared:.4f}")
                
                # Extract interaction coefficients
                interaction_results = []
                for term in interaction_terms:
                    if term in mod_interaction.params.index:
                        coef = mod_interaction.params[term]
                        se = mod_interaction.bse[term]
                        demo_var = term.replace('top_quantile_x_', '')
                        interaction_results.append({
                            'demographic': demo_var,
                            'interaction_coef': coef,
                            'interaction_se': se,
                            'ci_low': coef - 1.96 * se,
                            'ci_hi': coef + 1.96 * se
                        })
                        print(f"  {term}: {coef:.6f} (SE: {se:.6f})")
                
                if interaction_results:
                    df_interaction_results = pd.DataFrame(interaction_results)
                    interaction_out = OUTPUTS_TABLES / "quantile_analysis_interactions.csv"
                    df_interaction_results.to_csv(interaction_out, index=False)
                    print(f"\n✓ Saved interaction results to: {interaction_out}")
        else:
            print("⚠️  No demographic variables available for interactions")
    else:
        print("⚠️  No demographic columns to merge")
else:
    print("⚠️  Demographics file not found, skipping interaction analysis")

print("\n" + "=" * 80)
print("QUANTILE-BASED ANALYSIS COMPLETE")
print("=" * 80)
