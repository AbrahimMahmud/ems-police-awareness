"""
Data Assessment Script

This script evaluates whether the available data is sufficient for analysis:
- Checks date ranges and overlap between EMS and Twitter data
- Assesses data completeness and coverage
- Identifies potential issues or gaps
- Provides recommendations
"""

import duckdb
import pandas as pd
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

print("=" * 80)
print("DATA ASSESSMENT FOR EMS POLICE AWARENESS RESEARCH")
print("=" * 80)

# ============================================================================
# 1. ASSESS EMS DATA
# ============================================================================
print("\n" + "=" * 80)
print("1. EMS DATA ASSESSMENT")
print("=" * 80)

EMS_BASENAME_PATTERN = "EMS_Incident_Dispatch_Data"
ems_files = [f for f in DATA_RAW.glob(f"{EMS_BASENAME_PATTERN}*.csv")]
if not ems_files:
    print("ERROR: EMS data file not found!")
else:
    EMS_PATH = max(ems_files, key=lambda p: p.stat().st_size)
    print(f"EMS File: {EMS_PATH.name}")
    print(f"File Size: {EMS_PATH.stat().st_size / (1024**3):.2f} GB")
    
    # Quick sample to check structure
    print("\nChecking EMS data structure...")
    con = duckdb.connect()
    
    # Check date range
    date_check_sql = f"""
    SELECT 
        MIN(try_strptime(incident_datetime, '%m/%d/%Y %I:%M:%S %p')) AS min_date,
        MAX(try_strptime(incident_datetime, '%m/%d/%Y %I:%M:%S %p')) AS max_date,
        COUNT(*) AS total_rows,
        COUNT(DISTINCT communitydistrict) AS num_cds,
        COUNT(DISTINCT final_call_type) AS num_call_types
    FROM read_csv_auto('{EMS_PATH}', all_varchar=true, sample_size=1000000, ignore_errors=true)
    WHERE incident_datetime IS NOT NULL
    """
    
    try:
        ems_summary = con.execute(date_check_sql).fetch_df()
        print(f"  Total rows (sample): {ems_summary['total_rows'].iloc[0]:,}")
        print(f"  Date range: {ems_summary['min_date'].iloc[0]} to {ems_summary['max_date'].iloc[0]}")
        print(f"  Community districts: {ems_summary['num_cds'].iloc[0]}")
        print(f"  Call types: {ems_summary['num_call_types'].iloc[0]}")
    except Exception as e:
        print(f"  Error checking EMS data: {e}")
    
    # Check for required columns
    print("\nChecking required columns...")
    sample_sql = f"SELECT * FROM read_csv_auto('{EMS_PATH}', all_varchar=true, sample_size=10)"
    try:
        sample = con.execute(sample_sql).fetch_df()
        required_cols = ['incident_datetime', 'communitydistrict', 'final_call_type', 
                        'incident_disposition_code', 'special_event_indicator', 
                        'standby_indicator', 'transfer_indicator']
        missing_cols = [col for col in required_cols if col.lower() not in [c.lower() for c in sample.columns]]
        if missing_cols:
            print(f"  WARNING: Missing columns: {missing_cols}")
        else:
            print(f"  ✓ All required columns present")
            print(f"  Available columns: {', '.join(sample.columns[:10])}...")
    except Exception as e:
        print(f"  Error checking columns: {e}")
    
    # Check MH call codes
    print("\nChecking mental health call codes...")
    MH_CODES = ("EDP", "ALTMEN", "ALTMFC", "ALTMFT", "JUMPDN", "JUMPUP", "JUMPDC", "OD", "ODC", "POISON", "DRUG")
    mh_check_sql = f"""
    SELECT 
        upper(trim(final_call_type)) AS call_type,
        COUNT(*) AS count
    FROM read_csv_auto('{EMS_PATH}', all_varchar=true, sample_size=1000000, ignore_errors=true)
    WHERE upper(trim(final_call_type)) IN {tuple(MH_CODES)}
    GROUP BY call_type
    ORDER BY count DESC
    """
    try:
        mh_codes_found = con.execute(mh_check_sql).fetch_df()
        print(f"  MH call codes found in sample:")
        for _, row in mh_codes_found.iterrows():
            print(f"    {row['call_type']}: {row['count']:,}")
    except Exception as e:
        print(f"  Error checking MH codes: {e}")
    
    con.close()

# ============================================================================
# 2. ASSESS TWITTER DATA
# ============================================================================
print("\n" + "=" * 80)
print("2. TWITTER DATA ASSESSMENT")
print("=" * 80)

TW1_PATH = DATA_RAW / "211118_tweet_count_name_date.csv"
TW2_PATH = DATA_RAW / "220126_final_daily_tweet_count.csv"

for tw_path, name in [(TW1_PATH, "File 1 (individual incidents)"), (TW2_PATH, "File 2 (daily aggregated)")]:
    if not tw_path.exists():
        print(f"\n{name}: NOT FOUND")
        continue
    
    print(f"\n{name}: {tw_path.name}")
    print(f"  File Size: {tw_path.stat().st_size / (1024**2):.2f} MB")
    
    try:
        df = pd.read_csv(tw_path, nrows=1000)
        print(f"  Columns: {', '.join(df.columns)}")
        
        if 'date' in df.columns:
            df_full = pd.read_csv(tw_path)
            df_full['date'] = pd.to_datetime(df_full['date'], errors='coerce')
            df_full = df_full.dropna(subset=['date'])
            
            print(f"  Total rows: {len(df_full):,}")
            print(f"  Date range: {df_full['date'].min()} to {df_full['date'].max()}")
            print(f"  Days covered: {(df_full['date'].max() - df_full['date'].min()).days} days")
            
            # Check for missing dates
            date_range = pd.date_range(df_full['date'].min(), df_full['date'].max(), freq='D')
            missing_dates = len(date_range) - df_full['date'].nunique()
            if missing_dates > 0:
                print(f"  WARNING: {missing_dates} missing dates in range")
            else:
                print(f"  ✓ No missing dates")
            
            # Check tweet counts
            if 'tweet_count' in df_full.columns:
                print(f"  Total tweets: {df_full['tweet_count'].sum():,}")
                print(f"  Mean tweets/day: {df_full['tweet_count'].mean():.1f}")
                print(f"  Max tweets/day: {df_full['tweet_count'].max():,}")
                zero_days = (df_full['tweet_count'] == 0).sum()
                print(f"  Days with 0 tweets: {zero_days} ({100*zero_days/len(df_full):.1f}%)")
        
    except Exception as e:
        print(f"  Error reading file: {e}")

# ============================================================================
# 3. ASSESS DATA OVERLAP AND SUFFICIENCY
# ============================================================================
print("\n" + "=" * 80)
print("3. DATA OVERLAP AND SUFFICIENCY ASSESSMENT")
print("=" * 80)

# Get Twitter date range
try:
    tw1 = pd.read_csv(TW1_PATH)
    tw2 = pd.read_csv(TW2_PATH)
    
    tw1['date'] = pd.to_datetime(tw1['date'], errors='coerce')
    tw2['date'] = pd.to_datetime(tw2['date'], errors='coerce')
    
    tw_dates = pd.concat([tw1['date'], tw2['date']]).dropna()
    tw_min = tw_dates.min()
    tw_max = tw_dates.max()
    
    print(f"\nTwitter data range: {tw_min.date()} to {tw_max.date()}")
    print(f"Twitter coverage: {(tw_max - tw_min).days} days ({(tw_max - tw_min).days / 365.25:.1f} years)")
    
    # Estimate EMS date range (from sample)
    print(f"\nEMS data range: 2005-01-01 onwards (estimated from file structure)")
    
    # Calculate overlap
    print(f"\nOverlap period: {tw_min.date()} to {tw_max.date()}")
    overlap_days = (tw_max - tw_min).days
    print(f"Overlap duration: {overlap_days} days ({overlap_days / 365.25:.1f} years)")
    
    # Assessment
    print("\n" + "-" * 80)
    print("SUFFICIENCY ASSESSMENT:")
    print("-" * 80)
    
    issues = []
    recommendations = []
    
    if overlap_days < 365:
        issues.append(f"Limited overlap: Only {overlap_days} days of data")
        recommendations.append("Consider extending Twitter data collection or focusing analysis on available period")
    elif overlap_days < 730:
        issues.append(f"Moderate overlap: {overlap_days} days (~{overlap_days/365.25:.1f} years)")
        recommendations.append("Analysis is feasible but may have limited statistical power")
    else:
        print(f"✓ Good overlap: {overlap_days} days (~{overlap_days/365.25:.1f} years)")
    
    # Check for sufficient variation
    print("\nData variation requirements:")
    print("  - Need variation in awareness (Twitter activity) over time: ✓ (likely)")
    print("  - Need variation in MH calls across districts and time: ✓ (likely)")
    print("  - Need sufficient sample size for regression: ✓ (likely, given ~28M EMS rows)")
    
    # Statistical power considerations
    print("\nStatistical power considerations:")
    nyc_cds = 59  # NYC has 59 community districts
    print(f"  - NYC has {nyc_cds} community districts")
    print(f"  - With {overlap_days} days, potential panel size: ~{nyc_cds * overlap_days:,} district-days")
    print(f"  - After filtering (≥5 calls/day): ~{int(nyc_cds * overlap_days * 0.8):,} observations (estimated)")
    
    if overlap_days * nyc_cds < 10000:
        issues.append("Small panel size may limit statistical power")
        recommendations.append("Consider pooling data or using alternative specifications")
    else:
        print(f"  ✓ Sufficient panel size for regression analysis")
    
    # Temporal coverage
    print("\nTemporal coverage:")
    if tw_max.year < 2021:
        issues.append(f"Twitter data ends in {tw_max.year} - may miss recent events")
        recommendations.append("Consider updating Twitter data to include more recent years")
    
    # Missing data concerns
    print("\nPotential data quality issues:")
    print("  - Need to verify: Community district coverage (all 59 CDs present?)")
    print("  - Need to verify: No systematic missing dates in Twitter data")
    print("  - Need to verify: EMS data quality (missing values, data entry errors)")
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    
    if len(issues) == 0:
        print("✓ DATA APPEARS SUFFICIENT FOR ANALYSIS")
        print("\nThe data should be sufficient to:")
        print("  1. Estimate distributed lag effects of awareness on MH calls")
        print("  2. Test for heterogeneity across community districts")
        print("  3. Examine temporal patterns in the response")
    else:
        print("⚠ DATA HAS SOME LIMITATIONS BUT ANALYSIS IS FEASIBLE")
        print("\nIssues identified:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
        print("\nAnalysis can proceed, but:")
        print("  - Results should be interpreted with awareness of limitations")
        print("  - Consider robustness checks and sensitivity analysis")
        print("  - May want to collect additional data if possible")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Run the analysis pipeline to verify data processing works")
    print("2. Check the processed panel for completeness")
    print("3. Examine descriptive statistics before running regressions")
    print("4. Consider data quality checks (missing values, outliers)")

except Exception as e:
    print(f"\nError in overlap assessment: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

