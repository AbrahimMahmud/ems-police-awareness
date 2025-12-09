"""
Step 10d: Parse CD demographics from hierarchical Excel structure.

The Excel file has sections for each CD with variables as rows.
This script extracts and pivots the data into one row per CD.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

print("=" * 80)
print("PARSING CD DEMOGRAPHICS FROM HIERARCHICAL STRUCTURE")
print("=" * 80)

# Load Excel file
xlsx_file = DATA_RAW / "sf1_dp_cd_demoprofile.xlsx"
print(f"\nLoading: {xlsx_file.name}")

df = pd.read_excel(xlsx_file, sheet_name='CD Profiles', engine='openpyxl', header=None)

print(f"Shape: {df.shape}")

# Find CD sections
# Pattern: "Bronx Community District 1", "Manhattan Community District 1", etc.
cd_sections = []
current_cd = None
current_cd_row = None

for i, row in df.iterrows():
    row0 = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
    
    # Check if this is a CD header row
    cd_match = re.search(r'(Bronx|Manhattan|Brooklyn|Queens|Staten Island)\s+Community\s+District\s+(\d+)', row0, re.IGNORECASE)
    if cd_match:
        borough = cd_match.group(1)
        cd_num = int(cd_match.group(2))
        
        # Convert to borough code + CD
        borough_codes = {
            'Manhattan': 1,
            'Bronx': 2,
            'Brooklyn': 3,
            'Queens': 4,
            'Staten Island': 5
        }
        borough_code = borough_codes.get(borough, 0)
        cd_code = borough_code * 100 + cd_num
        
        cd_sections.append({
            'row': i,
            'borough': borough,
            'cd_num': cd_num,
            'cd_code': cd_code,
            'name': row0.strip()
        })
        print(f"  Found: {row0.strip()} -> CD {cd_num} (code: {cd_code})")

print(f"\n✓ Found {len(cd_sections)} community districts")

# Extract data for each CD
# The structure after CD name is:
# - Row i+2: Header with "2000", "2010", "Change 2000-2010"
# - Row i+3: Subheaders "Number", "Percent"
# - Row i+4+: Data rows

all_cd_data = []

for cd_info in cd_sections:
    start_row = cd_info['row']
    cd_data = {'communitydistrict': cd_info['cd_code']}
    
    # Find the data section (skip header rows)
    data_start = start_row + 4  # Skip CD name, blank, header, subheader
    
    # Extract variables until next CD section or end
    end_row = cd_sections[cd_sections.index(cd_info) + 1]['row'] if cd_sections.index(cd_info) < len(cd_sections) - 1 else len(df)
    
    # Key variables to extract (2010 data - columns 7-8 are 2010 Number and Percent)
    # Column structure: 0=variable name, 7=2010 Number, 8=2010 Percent
    key_vars = [
        ('Total Population', 'total_population', 7, 'number'),
        ('White Nonhispanic', 'pct_white', 8, 'percent'),
        ('Black Nonhispanic', 'pct_black', 8, 'percent'),
        ('Hispanic Origin', 'pct_hispanic', 8, 'percent'),
        ('Asian and Pacific Islander Nonhispanic', 'pct_asian', 8, 'percent'),
        ('Total Households', 'total_households', 7, 'number'),
        ('Owner occupied', 'pct_owner_occupied', 8, 'percent'),
        ('Renter occupied', 'pct_renter_occupied', 8, 'percent'),
    ]
    
    # Scan through data rows
    for i in range(data_start, min(data_start + 300, end_row)):  # Increased search range
        row = df.iloc[i]
        var_name_col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        var_name_col1 = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        
        # Combine column 0 and 1 for variable name (some variables span multiple columns)
        full_var_name = f"{var_name_col0} {var_name_col1}".strip()
        
        # Check if this matches a key variable
        for key_var, col_name, col_idx, var_type in key_vars:
            # Match if key_var appears in the variable name
            if key_var.lower() in full_var_name.lower() or key_var.lower() in var_name_col0.lower():
                # Extract value from specified column
                if col_idx < len(row):
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        try:
                            val_float = float(val)
                            # Only store if not already set (avoid duplicates)
                            if col_name not in cd_data:
                                cd_data[col_name] = val_float
                        except (ValueError, TypeError):
                            pass
                break
    
    # Extract additional variables that might be in different positions
    # Look for variables in column 0 or 1
    for i in range(data_start, min(data_start + 300, end_row)):
        row = df.iloc[i]
        var_name_col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        var_name_col1 = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        full_var_name = f"{var_name_col0} {var_name_col1}".strip().lower()
        
        # Look for income-related
        if ('income' in full_var_name or 'median' in full_var_name) and 'median_income' not in cd_data:
            # Try multiple columns
            for col_idx in [7, 8, 5, 6]:
                if col_idx < len(row):
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        try:
                            val_float = float(val)
                            if val_float > 0:  # Reasonable income value
                                cd_data['median_income'] = val_float
                                break
                        except:
                            pass
        
        # Look for education (bachelor's degree)
        if ('bachelor' in full_var_name or 'college' in full_var_name or 
            'degree' in full_var_name) and 'pct_college' not in cd_data:
            if len(row) > 8:
                val = row.iloc[8]  # Percent column
                if pd.notna(val):
                    try:
                        val_float = float(val)
                        if 0 <= val_float <= 100:  # Valid percentage
                            cd_data['pct_college'] = val_float
                    except:
                        pass
        
        # Look for poverty
        if 'poverty' in full_var_name and 'pct_poverty' not in cd_data:
            if len(row) > 8:
                val = row.iloc[8]  # Percent column
                if pd.notna(val):
                    try:
                        val_float = float(val)
                        if 0 <= val_float <= 100:
                            cd_data['pct_poverty'] = val_float
                    except:
                        pass
    
    all_cd_data.append(cd_data)

# Create DataFrame
df_cd = pd.DataFrame(all_cd_data)

print(f"\n✓ Extracted data for {len(df_cd)} community districts")
print(f"  Columns: {list(df_cd.columns)}")
print(f"\nFirst few rows:")
print(df_cd.head(10))

# Keep both CD code and CD number
df_cd['cd_code'] = df_cd['communitydistrict']  # Original 3-digit code (201, 301, 401, etc.)
df_cd['cd_number'] = df_cd['communitydistrict'].apply(lambda x: x % 100 if x >= 100 else x)
# For merge, we need to match panel's 3-digit codes, so keep the original code
# The merge script will handle conversion

# Save
output_path = DATA_PROCESSED / "cd_demographics_clean.parquet"
df_cd.to_parquet(output_path, index=False)
print(f"\n✓ Saved to: {output_path}")

csv_path = DATA_PROCESSED / "cd_demographics_clean.csv"
df_cd.to_csv(csv_path, index=False)
print(f"✓ Saved as CSV: {csv_path}")

print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
print(f"\nExtracted {len(df_cd)} CDs with {len(df_cd.columns)-1} demographic variables")
print("\nVariables extracted:")
for col in df_cd.columns:
    if col != 'communitydistrict' and col != 'cd_number':
        non_null = df_cd[col].notna().sum()
        print(f"  - {col}: {non_null}/{len(df_cd)} CDs have data")

print("\nNext: Run merge script")
print("  python scripts/11_merge_demographics.py")

