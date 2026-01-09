"""
Create visualization showing the distribution of awareness and high awareness event days.

This helps explain what constitutes a "high awareness event day" in the analysis.
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

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("VISUALIZING AWARENESS DISTRIBUTION")
print("=" * 80)

# Load data
df = pd.read_parquet(DATA_PROCESSED / "panel_cd_day_awareness.parquet")
df['incident_date'] = pd.to_datetime(df['incident_date'])

# Get unique dates with awareness_z
df_dates = df[['incident_date', 'awareness_z']].drop_duplicates().dropna()
df_dates = df_dates.sort_values('incident_date')

print(f"\nTotal days with awareness data: {len(df_dates):,}")
print(f"Date range: {df_dates['incident_date'].min().date()} to {df_dates['incident_date'].max().date()}")

# Calculate statistics
awareness_data = df_dates['awareness_z']
print(f"\nAwareness z-score statistics:")
print(f"  Mean: {awareness_data.mean():.3f}")
print(f"  Std: {awareness_data.std():.3f}")
print(f"  Min: {awareness_data.min():.3f}")
print(f"  Max: {awareness_data.max():.3f}")
print(f"  Median: {awareness_data.median():.3f}")

# Count days above thresholds
thresholds = [1.0, 1.5, 2.0]
for threshold in thresholds:
    n_above = (awareness_data > threshold).sum()
    pct_above = n_above / len(awareness_data) * 100
    print(f"\n  Threshold: {threshold} SD")
    print(f"    Days above: {n_above} ({pct_above:.2f}%)")

# ============================================================================
# Figure 1: Distribution of awareness_z
# ============================================================================
print("\n1. Creating awareness distribution plot...")

fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Top panel: Histogram
ax1 = axes[0]
ax1.hist(awareness_data, bins=100, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)
ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='Mean (0)')
ax1.axvline(1.0, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='1.0 SD threshold')
ax1.axvline(1.5, color='darkorange', linestyle='--', linewidth=1.5, alpha=0.7, label='1.5 SD threshold')
ax1.axvline(2.0, color='coral', linestyle='--', linewidth=1.5, alpha=0.7, label='2.0 SD threshold')

# Shade high awareness regions
ax1.axvspan(1.0, awareness_data.max(), alpha=0.2, color='orange', label='High awareness (1.0 SD)')
ax1.axvspan(1.5, awareness_data.max(), alpha=0.2, color='darkorange', label='Very high (1.5 SD)')
ax1.axvspan(2.0, awareness_data.max(), alpha=0.2, color='coral', label='Extreme (2.0 SD)')

ax1.set_xlabel('Awareness z-score (standard deviations from mean)', fontweight='bold', fontsize=11)
ax1.set_ylabel('Number of Days', fontweight='bold', fontsize=11)
ax1.set_title('Distribution of Daily Awareness Levels\n(Twitter Activity About Police Killings)', 
             fontsize=13, fontweight='bold', pad=15)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3, linestyle='--', axis='y')

# Add text annotations
ax1.text(0.5, 0.95, f'Total days: {len(awareness_data):,}\nMean: {awareness_data.mean():.2f}\nStd: {awareness_data.std():.2f}',
         transform=ax1.transAxes, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Bottom panel: Time series
ax2 = axes[1]
ax2.plot(df_dates['incident_date'], df_dates['awareness_z'], 
         linewidth=0.5, alpha=0.6, color='steelblue', label='Daily awareness')
ax2.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
ax2.axhline(1.0, color='orange', linestyle='--', linewidth=1, alpha=0.5)
ax2.axhline(1.5, color='darkorange', linestyle='--', linewidth=1, alpha=0.5)
ax2.axhline(2.0, color='coral', linestyle='--', linewidth=1, alpha=0.5)

# Highlight high awareness periods
high_awareness = df_dates[df_dates['awareness_z'] > 2.0]
if len(high_awareness) > 0:
    ax2.scatter(high_awareness['incident_date'], high_awareness['awareness_z'],
               color='red', s=30, alpha=0.7, zorder=5, label='Extreme awareness (>2.0 SD)')

ax2.set_xlabel('Date', fontweight='bold', fontsize=11)
ax2.set_ylabel('Awareness z-score', fontweight='bold', fontsize=11)
ax2.set_title('Awareness Over Time: Daily Twitter Activity', 
             fontsize=13, fontweight='bold', pad=15)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--')

# Highlight analysis period
ax2.axvspan(pd.to_datetime('2017-01-01'), pd.to_datetime('2020-12-31'), 
           alpha=0.1, color='yellow', label='Analysis Period (2017-2020)')

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "awareness_distribution.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'awareness_distribution.png'}")

# ============================================================================
# Figure 2: High awareness events timeline
# ============================================================================
print("\n2. Creating high awareness events timeline...")

fig, ax = plt.subplots(figsize=(14, 6))

# Plot all awareness
ax.plot(df_dates['incident_date'], df_dates['awareness_z'], 
        linewidth=0.5, alpha=0.4, color='gray', label='All days')

# Highlight different threshold levels
for threshold, color, label in [(1.0, 'orange', '1.0 SD'), 
                                 (1.5, 'darkorange', '1.5 SD'),
                                 (2.0, 'red', '2.0 SD')]:
    high_days = df_dates[df_dates['awareness_z'] > threshold]
    if len(high_days) > 0:
        ax.scatter(high_days['incident_date'], high_days['awareness_z'],
                  color=color, s=50, alpha=0.7, zorder=5, label=f'>{threshold} SD ({len(high_days)} days)')

# Add threshold lines
ax.axhline(1.0, color='orange', linestyle='--', linewidth=1, alpha=0.5)
ax.axhline(1.5, color='darkorange', linestyle='--', linewidth=1, alpha=0.5)
ax.axhline(2.0, color='red', linestyle='--', linewidth=1, alpha=0.5)
ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)

# Annotate highest awareness day
highest = df_dates.loc[df_dates['awareness_z'].idxmax()]
ax.annotate(f"May 29, 2020\n(awareness_z = {highest['awareness_z']:.1f})",
           xy=(highest['incident_date'], highest['awareness_z']),
           xytext=(10, 10), textcoords='offset points',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
           fontsize=9, fontweight='bold')

ax.set_xlabel('Date', fontweight='bold', fontsize=12)
ax.set_ylabel('Awareness z-score (standard deviations)', fontweight='bold', fontsize=12)
ax.set_title('High Awareness Event Days: Timeline of Twitter Activity About Police Killings', 
            fontsize=14, fontweight='bold', pad=15)
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3, linestyle='--')

# Highlight analysis period
ax.axvspan(pd.to_datetime('2017-01-01'), pd.to_datetime('2020-12-31'), 
          alpha=0.1, color='yellow')

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "high_awareness_timeline.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ✓ Saved: {OUTPUTS_FIGURES / 'high_awareness_timeline.png'}")

# ============================================================================
# Summary statistics table
# ============================================================================
print("\n3. Creating summary statistics...")

summary_stats = []
for threshold in [0.5, 1.0, 1.5, 2.0, 3.0]:
    n_above = (awareness_data > threshold).sum()
    pct_above = n_above / len(awareness_data) * 100
    if n_above > 0:
        mean_awareness = awareness_data[awareness_data > threshold].mean()
        summary_stats.append({
            'threshold_sd': threshold,
            'n_days': n_above,
            'pct_days': pct_above,
            'mean_awareness': mean_awareness,
            'max_awareness': awareness_data[awareness_data > threshold].max()
        })

df_summary = pd.DataFrame(summary_stats)
print("\nSummary by threshold:")
print(df_summary.to_string(index=False))

print("\n" + "=" * 80)
print("AWARENESS VISUALIZATION COMPLETE")
print("=" * 80)
print(f"\nGenerated figures:")
print(f"  1. awareness_distribution.png - Distribution and time series")
print(f"  2. high_awareness_timeline.png - Timeline of high awareness events")
print("\n" + "=" * 80)

