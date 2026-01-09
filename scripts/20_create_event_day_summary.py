"""
Create a summary visualization and table showing what high awareness event days are
and how they relate to actual incidents.

This helps clarify exactly which days we use as "event days" in the analysis.
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
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CREATING EVENT DAY SUMMARY")
print("=" * 80)

# Load data
df = pd.read_parquet(DATA_PROCESSED / "panel_cd_day_awareness.parquet")
df['incident_date'] = pd.to_datetime(df['incident_date'])

# Get unique dates with awareness
df_dates = df[['incident_date', 'awareness_z']].drop_duplicates().dropna()
df_dates = df_dates.sort_values('incident_date')

# Filter to analysis period
df_dates = df_dates[df_dates['incident_date'].between('2017-01-01', '2020-12-31')]

print(f"\nAnalysis period: 2017-2020")
print(f"Total days: {len(df_dates):,}")

# Create summary for different thresholds
thresholds = [1.0, 1.5, 2.0]
summary_data = []

for threshold in thresholds:
    high_days = df_dates[df_dates['awareness_z'] > threshold].copy()
    high_days = high_days.sort_values('awareness_z', ascending=False)
    
    n_days = len(high_days)
    pct_days = n_days / len(df_dates) * 100
    
    summary_data.append({
        'threshold_sd': threshold,
        'n_event_days': n_days,
        'pct_of_days': pct_days,
        'mean_awareness': high_days['awareness_z'].mean() if n_days > 0 else np.nan,
        'max_awareness': high_days['awareness_z'].max() if n_days > 0 else np.nan,
        'top_event_date': high_days.iloc[0]['incident_date'].date() if n_days > 0 else None,
        'top_event_awareness': high_days.iloc[0]['awareness_z'] if n_days > 0 else np.nan,
    })
    
    print(f"\nThreshold: {threshold} SD")
    print(f"  Event days: {n_days} ({pct_days:.2f}% of period)")
    if n_days > 0:
        print(f"  Top event day: {high_days.iloc[0]['incident_date'].date()} (awareness_z = {high_days.iloc[0]['awareness_z']:.2f})")

df_summary = pd.DataFrame(summary_data)
summary_out = OUTPUTS_TABLES / "event_day_summary.csv"
df_summary.to_csv(summary_out, index=False)
print(f"\n✓ Saved summary to: {summary_out}")

# Create detailed list of high awareness event days
print("\n" + "=" * 80)
print("DETAILED EVENT DAY LIST (Threshold = 1.5 SD)")
print("=" * 80)

threshold = 1.5
high_days = df_dates[df_dates['awareness_z'] > threshold].copy()
high_days = high_days.sort_values('awareness_z', ascending=False)

event_day_list = []
for idx, row in high_days.iterrows():
    event_day_list.append({
        'event_date': row['incident_date'].date(),
        'awareness_z': row['awareness_z'],
        'days_above_threshold': row['awareness_z'] - threshold,
        'percentile': (df_dates['awareness_z'] <= row['awareness_z']).sum() / len(df_dates) * 100
    })

df_event_days = pd.DataFrame(event_day_list)
event_days_out = OUTPUTS_TABLES / "high_awareness_event_days_list.csv"
df_event_days.to_csv(event_days_out, index=False)
print(f"\n✓ Saved event days list to: {event_days_out}")
print(f"\nTop 10 high awareness event days:")
print(df_event_days.head(10).to_string(index=False))

# Create visualization
print("\n" + "=" * 80)
print("CREATING VISUALIZATION")
print("=" * 80)

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Top panel: Timeline with event days marked
ax1 = axes[0]
ax1.plot(df_dates['incident_date'], df_dates['awareness_z'], 
         linewidth=0.5, alpha=0.4, color='gray', label='All days')

# Mark event days at different thresholds
colors = {'1.0': 'orange', '1.5': 'darkorange', '2.0': 'red'}
for threshold in [1.0, 1.5, 2.0]:
    high_days = df_dates[df_dates['awareness_z'] > threshold]
    if len(high_days) > 0:
        ax1.scatter(high_days['incident_date'], high_days['awareness_z'],
                   color=colors[str(threshold)], s=40, alpha=0.7, 
                   label=f'>{threshold} SD ({len(high_days)} event days)', zorder=5)

# Add threshold lines
for threshold in [1.0, 1.5, 2.0]:
    ax1.axhline(threshold, color=colors[str(threshold)], linestyle='--', 
               linewidth=1, alpha=0.5)
ax1.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)

# Annotate top event day
top_day = df_dates.loc[df_dates['awareness_z'].idxmax()]
ax1.annotate(f"Top Event Day:\n{top_day['incident_date'].date()}\n(awareness_z = {top_day['awareness_z']:.1f})",
            xy=(top_day['incident_date'], top_day['awareness_z']),
            xytext=(20, 20), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
            fontsize=10, fontweight='bold')

ax1.set_xlabel('Date', fontweight='bold', fontsize=12)
ax1.set_ylabel('Awareness z-score', fontweight='bold', fontsize=12)
ax1.set_title('High Awareness Event Days: Calendar Dates When Awareness Exceeded Threshold\n(Event Day = Date When awareness_z > Threshold, NOT Necessarily Killing Date)', 
             fontsize=13, fontweight='bold', pad=15)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3, linestyle='--')

# Highlight analysis period
ax1.axvspan(pd.to_datetime('2017-01-01'), pd.to_datetime('2020-12-31'), 
           alpha=0.1, color='yellow')

# Bottom panel: Distribution of awareness with thresholds
ax2 = axes[1]
ax2.hist(df_dates['awareness_z'], bins=100, color='steelblue', alpha=0.7, 
         edgecolor='black', linewidth=0.5)

# Add threshold lines
for threshold, color in [(1.0, 'orange'), (1.5, 'darkorange'), (2.0, 'red')]:
    ax2.axvline(threshold, color=color, linestyle='--', linewidth=2, 
               label=f'{threshold} SD threshold')
    # Shade region above threshold
    ax2.axvspan(threshold, df_dates['awareness_z'].max(), alpha=0.2, color=color)

ax2.axvline(0, color='red', linestyle='--', linewidth=1.5, label='Mean (0)')
ax2.set_xlabel('Awareness z-score (standard deviations)', fontweight='bold', fontsize=11)
ax2.set_ylabel('Number of Days', fontweight='bold', fontsize=11)
ax2.set_title('Distribution of Awareness Levels\n(Event Days = Days Above Threshold)', 
             fontsize=12, fontweight='bold', pad=15)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--', axis='y')

# Add text box with key information
info_text = f"""Key Points:
• Event day = Calendar date when awareness_z > threshold
• NOT necessarily the date of actual police killing
• Example: May 29, 2020 (awareness_z = 20.43) was 4 days
  after May 25, 2020 killing - represents when public
  attention peaked, not when incident occurred
• Total event days (1.5 SD): {len(df_dates[df_dates['awareness_z'] > 1.5])}"""
ax2.text(0.98, 0.98, info_text, transform=ax2.transAxes, 
        fontsize=9, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / "event_day_explanation.png", 
            bbox_inches='tight', facecolor='white')
plt.close()
print(f"✓ Saved visualization to: {OUTPUTS_FIGURES / 'event_day_explanation.png'}")

print("\n" + "=" * 80)
print("EVENT DAY SUMMARY COMPLETE")
print("=" * 80)
print(f"\nGenerated files:")
print(f"  1. {summary_out}")
print(f"  2. {event_days_out}")
print(f"  3. {OUTPUTS_FIGURES / 'event_day_explanation.png'}")
print("\n" + "=" * 80)

