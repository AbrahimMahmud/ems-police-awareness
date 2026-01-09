"""
Create comprehensive, publication-ready visualizations from all analysis results.

This script generates:
1. Progressive regression robustness figure
2. Awareness threshold effects comparison
3. DID event study plot
4. Call statistics trends over time
5. Distributed lag vs threshold comparison
6. Summary dashboard
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CREATING COMPREHENSIVE VISUALIZATIONS")
print("=" * 80)

# ============================================================================
# 1. Progressive Regression Robustness Plot
# ============================================================================
print("\n1. Creating progressive regression robustness plot...")

df_prog = pd.read_csv(OUTPUTS_TABLES / "regression_progressive_lag7_comparison.csv")
df_prog['model_num'] = range(1, len(df_prog) + 1)

fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(len(df_prog))
colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(df_prog)))

# Plot coefficients with error bars
ax.errorbar(x_pos, df_prog['lag7_coef'], 
            yerr=1.96 * df_prog['lag7_se'],
            fmt='o', markersize=10, capsize=5, capthick=2,
            color='steelblue', linewidth=2, label='Coefficient ± 95% CI')

# Add confidence interval shading
for i, row in df_prog.iterrows():
    ax.fill_between([i-0.2, i+0.2], row['lag7_ci_low'], row['lag7_ci_hi'],
                     alpha=0.3, color=colors[i])

ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Null effect')
ax.set_xlabel('Model Specification', fontweight='bold')
ax.set_ylabel('Coefficient on Awareness (Lag 7)\nΔ mh_share per 1σ awareness', fontweight='bold')
ax.set_title('Robustness Check: Progressive Addition of Controls\n(All models show positive, significant effect at lag 7)', 
             fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x_pos)
ax.set_xticklabels([f"M{i+1}" for i in range(len(df_prog))], rotation=0)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='best')

# Add model labels on the right
model_labels = [
    'Awareness only',
    '+ Day of week',
    '+ Month×Year',
    '+ Holiday',
    '+ CD fixed effects'
]
for i, label in enumerate(model_labels):
    ax.text(len(df_prog) + 0.3, df_prog.iloc[i]['lag7_coef'], 
            label, va='center', fontsize=8, style='italic')

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "progressive_regression_robustness.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'progressive_regression_robustness.png'}")

# ============================================================================
# 2. Awareness Threshold Effects Comparison
# ============================================================================
print("\n2. Creating awareness threshold effects comparison...")

df_thresh = pd.read_csv(OUTPUTS_TABLES / "awareness_threshold_analysis.csv")
thresholds = df_thresh['threshold'].unique()
lags = sorted(df_thresh['lag'].unique())

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

for idx, threshold in enumerate(sorted(thresholds)):
    ax = axes[idx]
    df_t = df_thresh[df_thresh['threshold'] == threshold].sort_values('lag')
    
    # Plot coefficients
    ax.errorbar(df_t['lag'], df_t['coefficient'],
                yerr=1.96 * df_t['se'],
                fmt='o-', markersize=8, capsize=4, capthick=2,
                color='steelblue', linewidth=2, label='Coefficient ± 95% CI')
    
    # Shade confidence intervals
    ax.fill_between(df_t['lag'], df_t['ci_low'], df_t['ci_hi'],
                    alpha=0.2, color='steelblue')
    
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel('Lag (days)', fontweight='bold')
    if idx == 0:
        ax.set_ylabel('Effect on mh_share\n(percentage points)', fontweight='bold')
    ax.set_title(f'Threshold: {threshold} SD\n(High awareness days)', 
                 fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(df_t['lag'])

# Add significance markers
for idx, threshold in enumerate(sorted(thresholds)):
    ax = axes[idx]
    df_t = df_thresh[df_thresh['threshold'] == threshold].sort_values('lag')
    for _, row in df_t.iterrows():
        if abs(row['t_stat']) > 1.96:  # Significant at 5%
            ax.plot(row['lag'], row['coefficient'], 'o', 
                   markersize=12, markerfacecolor='none', 
                   markeredgecolor='red', markeredgewidth=2)

plt.suptitle('Awareness Threshold Effects: Impact of High Awareness Days\non Mental Health Call Share', 
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "awareness_threshold_effects.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'awareness_threshold_effects.png'}")

# ============================================================================
# 3. DID Event Study Plot
# ============================================================================
print("\n3. Creating DID event study plot...")

df_did_events = pd.read_csv(OUTPUTS_TABLES / "did_event_study_coefficients.csv")
df_did_events = df_did_events[df_did_events['se'] > 0]  # Filter out zero SEs
df_did_events = df_did_events.sort_values('event_time')

if len(df_did_events) > 0:
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot coefficients
    ax.errorbar(df_did_events['event_time'], df_did_events['coefficient'],
                yerr=1.96 * df_did_events['se'],
                fmt='o-', markersize=8, capsize=4, capthick=2,
                color='steelblue', linewidth=2, label='Coefficient ± 95% CI')
    
    # Shade confidence intervals
    ax.fill_between(df_did_events['event_time'], 
                    df_did_events['ci_low'], df_did_events['ci_hi'],
                    alpha=0.2, color='steelblue')
    
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.axvline(0, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='Event time = 0')
    ax.set_xlabel('Days Relative to High Awareness Event', fontweight='bold')
    ax.set_ylabel('Effect on mh_share\n(percentage points)', fontweight='bold')
    ax.set_title('Difference-in-Differences Event Study:\nEffect of High Awareness Days on Mental Health Calls', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best')
    
    plt.tight_layout()
    plt.savefig(OUTPUTS_FIGURES / "did_event_study.png", 
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'did_event_study.png'}")
else:
    print("  ⚠ No valid DID event study data to plot")

# ============================================================================
# 4. Call Statistics Trends Over Time
# ============================================================================
print("\n4. Creating call statistics trends over time...")

df_calls = pd.read_csv(OUTPUTS_TABLES / "call_statistics_summary.csv")
df_calls_year = df_calls[df_calls['level'] == 'year'].copy()
df_calls_year = df_calls_year.sort_values('group')

fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Top panel: Total calls and MH calls
ax1 = axes[0]
ax1_twin = ax1.twinx()

ax1.plot(df_calls_year['group'], df_calls_year['total_calls'] / 1e6, 
         'o-', color='steelblue', linewidth=2, markersize=6, label='Total Calls')
ax1_twin.plot(df_calls_year['group'], df_calls_year['mh_calls'] / 1e6, 
              's-', color='coral', linewidth=2, markersize=6, label='MH Calls')

ax1.set_xlabel('Year', fontweight='bold')
ax1.set_ylabel('Total Calls (millions)', fontweight='bold', color='steelblue')
ax1_twin.set_ylabel('MH Calls (millions)', fontweight='bold', color='coral')
ax1.set_title('EMS Call Volume Trends: 2005-2025', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='steelblue')
ax1_twin.tick_params(axis='y', labelcolor='coral')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='upper left')
ax1_twin.legend(loc='upper right')

# Bottom panel: MH share over time
ax2 = axes[1]
ax2.plot(df_calls_year['group'], df_calls_year['mh_share'] * 100, 
         'o-', color='darkgreen', linewidth=2, markersize=6, label='MH Share (%)')
ax2.fill_between(df_calls_year['group'], 
                 (df_calls_year['mh_share'] * 100) - 1, 
                 (df_calls_year['mh_share'] * 100) + 1,
                 alpha=0.2, color='darkgreen')

ax2.set_xlabel('Year', fontweight='bold')
ax2.set_ylabel('Mental Health Call Share (%)', fontweight='bold')
ax2.set_title('Mental Health Call Share Over Time', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='best')

# Highlight analysis period (2017-2020)
ax2.axvspan(2017, 2020, alpha=0.1, color='yellow', label='Analysis Period')

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "call_statistics_trends.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'call_statistics_trends.png'}")

# ============================================================================
# 5. Distributed Lag vs Threshold Comparison
# ============================================================================
print("\n5. Creating distributed lag vs threshold comparison...")

df_comp = pd.read_csv(OUTPUTS_TABLES / "trend_vs_threshold_comparison.csv")
df_dl = df_comp[df_comp['approach'] == 'Distributed Lag'].copy()
df_thresh_did = df_comp[df_comp['approach'] == 'Threshold (DID)'].copy()
df_thresh_did = df_thresh_did[df_thresh_did['se'] > 0]  # Filter valid SEs

fig, ax = plt.subplots(figsize=(12, 6))

# Plot distributed lag
if len(df_dl) > 0:
    ax.errorbar(df_dl['time_period'], df_dl['coefficient'],
                yerr=1.96 * df_dl['se'],
                fmt='o-', markersize=8, capsize=4, capthick=2,
                color='steelblue', linewidth=2, label='Distributed Lag Model ± 95% CI')
    ax.fill_between(df_dl['time_period'], df_dl['ci_low'], df_dl['ci_hi'],
                    alpha=0.2, color='steelblue')

# Plot threshold DID (if valid data)
if len(df_thresh_did) > 0:
    ax.plot(df_thresh_did['time_period'], df_thresh_did['coefficient'],
            's--', markersize=8, color='coral', linewidth=2, 
            alpha=0.7, label='Threshold DID (High Awareness Days)')

ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax.set_xlabel('Days (Lag for DL, Event Time for DID)', fontweight='bold')
ax.set_ylabel('Effect on mh_share\n(percentage points)', fontweight='bold')
ax.set_title('Comparison: Distributed Lag vs. Threshold (DID) Approaches', 
             fontsize=13, fontweight='bold', pad=15)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='best')

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "distributed_lag_vs_threshold.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'distributed_lag_vs_threshold.png'}")

# ============================================================================
# 6. Summary Dashboard (Multi-panel)
# ============================================================================
print("\n6. Creating summary dashboard...")

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Panel 1: Progressive regression (top left)
ax1 = fig.add_subplot(gs[0, 0])
x_pos = np.arange(len(df_prog))
ax1.errorbar(x_pos, df_prog['lag7_coef'], 
            yerr=1.96 * df_prog['lag7_se'],
            fmt='o', markersize=6, capsize=3, color='steelblue', linewidth=1.5)
ax1.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax1.set_ylabel('Coefficient', fontsize=9)
ax1.set_title('Progressive Models\n(Lag 7)', fontsize=10, fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels([f"M{i+1}" for i in range(len(df_prog))], fontsize=7)
ax1.grid(True, alpha=0.3)

# Panel 2: Threshold effects (top middle)
ax2 = fig.add_subplot(gs[0, 1])
df_t1 = df_thresh[(df_thresh['threshold'] == 1.0) & (df_thresh['lag'] == 7)].iloc[0]
ax2.barh(0, df_t1['coefficient'], xerr=1.96*df_t1['se'], 
         color='steelblue', alpha=0.7, capsize=5)
ax2.axvline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax2.set_xlabel('Effect', fontsize=9)
ax2.set_title('Threshold Effect\n(1.0 SD, Lag 7)', fontsize=10, fontweight='bold')
ax2.set_yticks([])
ax2.grid(True, alpha=0.3, axis='x')

# Panel 3: Call trends (top right)
ax3 = fig.add_subplot(gs[0, 2])
ax3.plot(df_calls_year['group'], df_calls_year['mh_share'] * 100, 
         'o-', color='darkgreen', linewidth=1.5, markersize=4)
ax3.set_xlabel('Year', fontsize=9)
ax3.set_ylabel('MH Share (%)', fontsize=9)
ax3.set_title('MH Call Share\nOver Time', fontsize=10, fontweight='bold')
ax3.grid(True, alpha=0.3)

# Panel 4: Distributed lag (middle, full width)
ax4 = fig.add_subplot(gs[1, :])
if len(df_dl) > 0:
    ax4.errorbar(df_dl['time_period'], df_dl['coefficient'],
                yerr=1.96 * df_dl['se'],
                fmt='o-', markersize=6, capsize=3, color='steelblue', linewidth=1.5)
    ax4.fill_between(df_dl['time_period'], df_dl['ci_low'], df_dl['ci_hi'],
                     alpha=0.2, color='steelblue')
ax4.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax4.set_xlabel('Lag (days)', fontsize=10, fontweight='bold')
ax4.set_ylabel('Effect on mh_share', fontsize=10, fontweight='bold')
ax4.set_title('Distributed Lag Model: Full Impulse Response', 
              fontsize=11, fontweight='bold')
ax4.grid(True, alpha=0.3)

# Panel 5: Descriptive stats (bottom left)
ax5 = fig.add_subplot(gs[2, 0])
df_desc = pd.read_csv(OUTPUTS_TABLES / "descriptive_stats_all_variables.csv")
key_vars = ['mh_share', 'mh_calls', 'total_calls', 'pct_white', 'pct_black']
df_desc_key = df_desc[df_desc['variable'].isin(key_vars)]
ax5.barh(range(len(df_desc_key)), df_desc_key['mean'], color='steelblue', alpha=0.7)
ax5.set_yticks(range(len(df_desc_key)))
ax5.set_yticklabels(df_desc_key['variable'], fontsize=8)
ax5.set_xlabel('Mean Value', fontsize=9)
ax5.set_title('Key Variables\n(Means)', fontsize=10, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='x')

# Panel 6: Model comparison (bottom middle)
ax6 = fig.add_subplot(gs[2, 1])
df_models = pd.read_csv(OUTPUTS_TABLES / "regression_progressive_comparison.csv")
ax6.plot(df_models['model'], df_models['r_squared'], 
         'o-', color='darkgreen', linewidth=1.5, markersize=6)
ax6.set_xlabel('Model', fontsize=9)
ax6.set_ylabel('R²', fontsize=9)
ax6.set_title('Model Fit\n(R-squared)', fontsize=10, fontweight='bold')
ax6.set_xticklabels([f"M{i+1}" for i in range(len(df_models))], fontsize=7, rotation=45)
ax6.grid(True, alpha=0.3)

# Panel 7: Summary stats (bottom right)
ax7 = fig.add_subplot(gs[2, 2])
ax7.axis('off')
summary_text = f"""
KEY FINDINGS:

• Lag 7 Effect: {df_prog.iloc[-1]['lag7_coef']:.4f}
  (SE: {df_prog.iloc[-1]['lag7_se']:.4f})

• Total Observations: {df_models.iloc[-1]['n_obs']:,}

• R² (Full Model): {df_models.iloc[-1]['r_squared']:.3f}

• Mean MH Share: {df_desc[df_desc['variable']=='mh_share']['mean'].iloc[0]:.1%}

• Analysis Period: 2017-2020
"""
ax7.text(0.1, 0.5, summary_text, fontsize=9, family='monospace',
         verticalalignment='center', transform=ax7.transAxes)

plt.suptitle('Research Summary Dashboard: Police Awareness and Mental Health Calls', 
             fontsize=14, fontweight='bold', y=0.98)
plt.savefig(OUTPUTS_FIGURES / "summary_dashboard.png", 
            bbox_inches='tight', facecolor='white', dpi=300)
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'summary_dashboard.png'}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION COMPLETE")
print("=" * 80)
print(f"\nAll figures saved to: {OUTPUTS_FIGURES}")
print("\nGenerated figures:")
print("  1. progressive_regression_robustness.png")
print("  2. awareness_threshold_effects.png")
print("  3. did_event_study.png")
print("  4. call_statistics_trends.png")
print("  5. distributed_lag_vs_threshold.png")
print("  6. summary_dashboard.png")
print("\n" + "=" * 80)

