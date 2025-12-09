"""
Step 11: Merge Community District Demographics with EMS Panel

This script:
1. Loads the processed CD demographics
2. Loads the EMS panel with awareness data
3. Merges demographics to the panel
4. Creates interaction variables for heterogeneous effects analysis
5. Saves merged panel
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

print("=" * 80)
print("MERGING DEMOGRAPHICS WITH EMS PANEL")
print("=" * 80)

# Load datasets
print("\n1. Loading EMS panel with awareness data...")
panel_path = DATA_PROCESSED / "panel_cd_day_awareness.parquet"
if not panel_path.exists():
    raise FileNotFoundError(
        f"EMS panel not found: {panel_path}\n"
        f"Please run the main analysis pipeline first:\n"
        f"  python scripts/run_analysis.py"
    )

df_panel = pd.read_parquet(panel_path)
print(f"  ✓ Loaded {len(df_panel):,} rows")
print(f"  Date range: {df_panel['incident_date'].min()} to {df_panel['incident_date'].max()}")
print(f"  Community districts: {df_panel['communitydistrict'].nunique()}")

print("\n2. Loading CD demographics...")
demo_path = DATA_PROCESSED / "cd_demographics_clean.parquet"
if not demo_path.exists():
    raise FileNotFoundError(
        f"CD demographics not found: {demo_path}\n"
        f"Please run processing scripts first:\n"
        f"  python scripts/09_download_nyc_cd_demographics.py\n"
        f"  python scripts/10_process_cd_demographics.py"
    )

df_demo = pd.read_parquet(demo_path)
print(f"  ✓ Loaded {len(df_demo):,} rows")
print(f"  Community districts: {df_demo['communitydistrict'].nunique()}")

# Check CD overlap
print("\n3. Checking community district overlap...")

# Ensure CD columns are numeric and handle any issues
df_panel['communitydistrict'] = pd.to_numeric(df_panel['communitydistrict'], errors='coerce')
df_demo['communitydistrict'] = pd.to_numeric(df_demo['communitydistrict'], errors='coerce')

# Remove NaN values for comparison
panel_cds = set(df_panel['communitydistrict'].dropna().unique())
demo_cds = set(df_demo['communitydistrict'].dropna().unique())

common_cds = panel_cds & demo_cds
only_panel = panel_cds - demo_cds
only_demo = demo_cds - panel_cds

print(f"  CDs in panel: {len(panel_cds)}")
print(f"  CDs in demographics: {len(demo_cds)}")
print(f"  Common CDs: {len(common_cds)}")

# Show sample CD values from each dataset
panel_sample = sorted([int(cd) for cd in list(panel_cds)[:15]])
demo_sample = sorted([int(cd) for cd in list(demo_cds)[:15]])
print(f"\n  Sample CDs from panel: {panel_sample}")
print(f"  Sample CDs from demographics: {demo_sample}")

# Initialize merge keys
merge_key_panel = 'communitydistrict'
merge_key_demo = 'communitydistrict'

# Check if demographics has cd_code column (3-digit) or just cd_number
has_cd_code = 'cd_code' in df_demo.columns
has_cd_number = 'cd_number' in df_demo.columns

# Function to extract CD number from 3-digit code
def extract_cd_from_panel(cd_val):
    if pd.isna(cd_val):
        return np.nan
    cd_int = int(cd_val)
    if cd_int >= 100:
        cd_num = cd_int % 100
        return cd_num if cd_num != 0 else cd_int
    return cd_int

if has_cd_code:
    # Use 3-digit codes directly - this should match panel!
    print(f"\n  Demographics has cd_code column (3-digit format)")
    demo_cds_code = set(df_demo['cd_code'].dropna().unique())
    common_cds_code = panel_cds & demo_cds_code
    print(f"  CDs matching on 3-digit codes: {len(common_cds_code)}")
    
    if len(common_cds_code) > 0:
        print(f"    ✓ Found {len(common_cds_code)} matching CDs using 3-digit codes!")
        merge_key_panel = 'communitydistrict'
        merge_key_demo = 'cd_code'
        common_cds = common_cds_code
    else:
        # Try converting panel to CD numbers
        print(f"    Trying conversion to CD numbers...")
        df_panel['cd_for_merge'] = df_panel['communitydistrict'].apply(extract_cd_from_panel)
        panel_cds_converted = set(df_panel['cd_for_merge'].dropna().unique())
        common_cds_converted = panel_cds_converted & demo_cds
        print(f"    After conversion: {len(common_cds_converted)} matching CDs")
        
        if len(common_cds_converted) > 0:
            merge_key_panel = 'cd_for_merge'
            merge_key_demo = 'communitydistrict' if not has_cd_number else 'cd_number'
            common_cds = common_cds_converted
        else:
            merge_key_panel = 'cd_for_merge'
            merge_key_demo = 'communitydistrict'
else:
    # Demographics only has CD numbers, need to convert panel
    print("\n  Demographics uses CD numbers, converting panel CDs...")
    df_panel['cd_for_merge'] = df_panel['communitydistrict'].apply(extract_cd_from_panel)
    panel_cds_converted = set(df_panel['cd_for_merge'].dropna().unique())
    common_cds_converted = panel_cds_converted & demo_cds
    
    if len(common_cds_converted) > 0:
        print(f"    ✓ Found {len(common_cds_converted)} matching CDs after conversion!")
        merge_key_panel = 'cd_for_merge'
        merge_key_demo = 'communitydistrict'
        common_cds = common_cds_converted
    else:
        merge_key_panel = 'cd_for_merge'
        merge_key_demo = 'communitydistrict'

if only_panel:
    only_panel_clean = [cd for cd in only_panel if pd.notna(cd)]
    if only_panel_clean:
        print(f"  ⚠️  CDs only in panel (will have missing demographics): {sorted(only_panel_clean)[:20]}")
        if len(only_panel_clean) > 20:
            print(f"      ... and {len(only_panel_clean) - 20} more")
if only_demo:
    only_demo_clean = [cd for cd in only_demo if pd.notna(cd)]
    if only_demo_clean:
        print(f"  ⚠️  CDs only in demographics (will be dropped): {sorted(only_demo_clean)[:20]}")
        if len(only_demo_clean) > 20:
            print(f"      ... and {len(only_demo_clean) - 20} more")

# Merge
print("\n4. Merging datasets...")
print(f"  Merge keys: panel['{merge_key_panel}'] = demographics['{merge_key_demo}']")

df_merged = df_panel.merge(
    df_demo,
    left_on=merge_key_panel,
    right_on=merge_key_demo,
    how='left',
    suffixes=('', '_demo')
)

# Drop temporary merge column if it exists
if 'cd_for_merge' in df_merged.columns:
    df_merged = df_merged.drop(columns=['cd_for_merge'])

print(f"  ✓ Merged panel: {len(df_merged):,} rows")

# Check which rows have demographics (check if any demo columns are non-null)
demo_cols = [col for col in df_merged.columns if col.endswith('_demo') or col in df_demo.columns]
if demo_cols:
    # Check if any demo column has non-null values
    has_demo = df_merged[demo_cols[0]].notna()
    rows_with_demo = has_demo.sum()
    print(f"  Rows with demographics: {rows_with_demo:,}")
    if rows_with_demo == 0:
        print(f"  ⚠️  WARNING: No rows have demographics data!")
        print(f"  Checking merge keys...")
        print(f"    Panel merge key sample: {df_panel['cd_for_merge'].head() if 'cd_for_merge' in df_panel.columns else df_panel['communitydistrict'].head()}")
        print(f"    Demo merge key sample: {df_demo['communitydistrict'].head()}")
else:
    rows_with_demo = 0
    print(f"  ⚠️  No demographic columns found in merged data")

# Check for missing demographics
missing_demo = df_merged['communitydistrict'].isin(only_panel).sum()
if missing_demo > 0:
    print(f"  ⚠️  Rows with missing demographics: {missing_demo:,}")

# Create interaction variables for analysis
print("\n5. Creating interaction variables...")

# Identify demographic variables (user may need to adjust these column names)
# These are placeholders - update based on actual column names from processed data
demo_vars = {
    'income': None,  # Will be set based on actual column names
    'pct_black': None,
    'pct_hispanic': None,
    'pct_white': None,
    'pct_asian': None,
    'pct_college': None,
    'poverty_rate': None,
}

# Try to find these variables automatically
for var_name in demo_vars.keys():
    # Search for columns containing the variable name
    matches = [col for col in df_merged.columns if var_name in col.lower()]
    if matches:
        demo_vars[var_name] = matches[0]
        print(f"  ✓ Found {var_name}: {matches[0]}")

# Create interaction terms with awareness lags
print("\n6. Creating awareness × demographics interaction terms...")

lag_cols = [col for col in df_merged.columns if col.startswith('awarez_lag')]
print(f"  Found {len(lag_cols)} awareness lag variables")

interactions_created = []
for demo_var_name, demo_col in demo_vars.items():
    if demo_col and demo_col in df_merged.columns:
        # Check if variable is numeric
        if pd.api.types.is_numeric_dtype(df_merged[demo_col]):
            # Create interactions with each lag
            for lag_col in lag_cols:
                interaction_col = f"{lag_col}_x_{demo_var_name}"
                df_merged[interaction_col] = df_merged[lag_col] * df_merged[demo_col]
                interactions_created.append(interaction_col)
            print(f"  ✓ Created interactions: {demo_var_name} × {len(lag_cols)} lags")
        else:
            print(f"  ⚠️  Skipping {demo_var_name} (not numeric)")

print(f"\n  Total interaction variables created: {len(interactions_created)}")

# Create categorical variables for stratified analysis
print("\n7. Creating categorical variables for stratified analysis...")

for demo_var_name, demo_col in demo_vars.items():
    if demo_col and demo_col in df_merged.columns:
        if pd.api.types.is_numeric_dtype(df_merged[demo_col]):
            # Create quartiles
            quartile_col = f"{demo_var_name}_quartile"
            df_merged[quartile_col] = pd.qcut(
                df_merged[demo_col],
                q=4,
                labels=['Q1', 'Q2', 'Q3', 'Q4'],
                duplicates='drop'
            )
            print(f"  ✓ Created quartiles: {quartile_col}")

# Save merged panel
print("\n8. Saving merged panel...")
output_path = DATA_PROCESSED / "panel_cd_day_awareness_demographics.parquet"
df_merged.to_parquet(output_path, index=False)
print(f"  ✓ Saved to: {output_path}")

# Save summary statistics
print("\n9. Generating summary statistics...")
summary_stats = {
    'total_rows': len(df_merged),
    'date_range': (df_merged['incident_date'].min(), df_merged['incident_date'].max()),
    'community_districts': df_merged['communitydistrict'].nunique(),
    'rows_with_demographics': df_merged['communitydistrict'].isin(common_cds).sum(),
    'interaction_variables': len(interactions_created),
}

summary_path = DATA_PROCESSED / "merged_panel_summary.txt"
with open(summary_path, 'w') as f:
    f.write("MERGED PANEL SUMMARY\n")
    f.write("=" * 80 + "\n\n")
    for key, value in summary_stats.items():
        f.write(f"{key}: {value}\n")
    f.write("\n\nDemographic Variables:\n")
    for var_name, var_col in demo_vars.items():
        if var_col:
            f.write(f"  {var_name}: {var_col}\n")
    f.write("\n\nInteraction Variables Created:\n")
    for inter_var in interactions_created[:20]:  # First 20
        f.write(f"  - {inter_var}\n")
    if len(interactions_created) > 20:
        f.write(f"  ... and {len(interactions_created) - 20} more\n")

print(f"  ✓ Saved summary to: {summary_path}")

print("\n" + "=" * 80)
print("MERGE COMPLETE!")
print("=" * 80)
print(f"\nMerged panel saved to: {output_path}")
print(f"Summary statistics: {summary_path}")
print("\nNext steps:")
print("  1. Review the merged panel and summary statistics")
print("  2. Run heterogeneous effects analysis:")
print("     python scripts/12_heterogeneous_effects.py")

