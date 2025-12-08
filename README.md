# EMS Police Awareness Research Project

MIT UROP investigating the effect of public awareness of fatal police shootings on mental health-related EMS call volume in NYC.

## Research Questions

1. Do increases in public attention lead to changes in MH-related EMS calls at the community district (CD) × day level?
2. Are effects concentrated in particular CDs by socioeconomic/demographic characteristics?
3. What is the temporal profile (immediate vs. persistent over days/weeks)?

## Project Structure

```
ems-police-awareness/
├── data/
│   ├── raw/                    # Original data files (not in git)
│   │   ├── EMS_Incident_Dispatch_Data.csv
│   │   ├── 211118_tweet_count_name_date.csv
│   │   └── 220126_final_daily_tweet_count.csv
│   └── processed/              # Cleaned/merged data
│       ├── panel_cd_day.parquet
│       └── panel_cd_day_awareness.parquet
├── scripts/
│   ├── 01_data_cleaning.py     # Clean EMS data
│   ├── 02_merge_awareness.py   # Merge Twitter awareness data
│   ├── 03_regression_analysis.py  # Run distributed lag models
│   ├── 04_visualizations.py    # Create figures
│   └── run_analysis.py         # Run entire pipeline
├── outputs/
│   ├── figures/                # Plots and visualizations
│   └── tables/                 # Regression results
├── notebooks/                  # Jupyter notebooks for exploration
└── docs/                       # Documentation
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Data Files

Ensure the following files are in `data/raw/`:

- `EMS_Incident_Dispatch_Data*.csv` (NYC 911 EMS dispatch data - script will find the file automatically)
- `211118_tweet_count_name_date.csv` (Twitter awareness data, part 1)
- `220126_final_daily_tweet_count.csv` (Twitter awareness data, part 2)

### 3. Run Analysis Pipeline

**Option 1: Run all steps at once**
```bash
python scripts/run_analysis.py
```

**Option 2: Run steps individually**
```bash
# Step 1: Clean EMS data
python scripts/01_data_cleaning.py

# Step 2: Merge awareness data
python scripts/02_merge_awareness.py

# Step 3: Run regressions
python scripts/03_regression_analysis.py

# Step 4: Create visualizations
python scripts/04_visualizations.py
```

## Data Sources

### NYC EMS Data
- **Source**: NYC OpenData
- **Time period**: 2005-01-01 onwards
- **Level**: Community district × day
- **Key variables**: `incident_datetime`, `communitydistrict`, `final_call_type`

### Twitter Awareness Data
- **Time period**: 2017-01-01 onwards (estimated)
- **Level**: Citywide daily counts
- **Processing**: Combined from two datasets, z-scored

### Mental Health Call Codes
```python
MH_CODES = ("EDP", "ALTMEN", "ALTMFC", "ALTMFT", "JUMPDN", 
            "JUMPUP", "JUMPDC", "OD", "ODC", "POISON", "DRUG")
```

## Methodology

### Model Specification

Distributed lag model with community district fixed effects:

```
mh_share_it = α_i + β₀·awareness_t + β₁·awareness_{t-1} + ... 
              + β₂₈·awareness_{t-28} + X_it·γ + ε_it
```

Where:
- `mh_share_it`: MH calls / total calls in district i on day t
- `awareness_t`: Z-scored citywide Twitter activity on day t
- `α_i`: Community district fixed effects
- `X_it`: Day of week, month×year, holidays, COVID phases
- Standard errors clustered at community district level

### Sample Restrictions
- Days with ≥5 total calls
- Exclude: special events, standby calls, transfers, cancellations, duplicates

## Preliminary Findings

- Small uptick in MH share approximately 7 days after awareness spikes
- 7-day lag coefficient: ~0.0014 (statistically significant)
- Cumulative 0-7 day effect: ~0.0008 increase per 1σ awareness
- Translates to ~0.04 additional MH calls citywide per week
- Effect is modest with wide confidence intervals
- No significant effect on total call volume (placebo test)

## Next Steps

1. **Heterogeneity analysis**: Which CDs respond most/first?
2. **Refine classifications**: Review MH call code definitions
3. **Better awareness measures**: Add Google Trends, news data, topic filtering
4. **Link demographics**: CD-level socioeconomic characteristics

## Important Notes

- All dates in UTC
- Missing community district values are dropped
- COVID phases: 0 (pre-COVID), 1 (March-June 2020), 2 (July 2020+)
- Panel is unbalanced (some CD-days have <5 calls)

## Contact

MIT UROP under Prof. Justin Steil
Student: Abrahim Mahmud

---

## Code Corrections

The analysis scripts have been corrected from the original Colab notebook to work locally:

- **Fixed SQL formatting**: Proper SQL syntax for IN clauses with tuple values
- **Fixed file paths**: Uses local `data/raw/` and `data/processed/` instead of Google Drive
- **Fixed file names**: Handles EMS file with date suffix, correct Twitter file names
- **Added error handling**: Validates input files and data before processing
- **Replaced display()**: Uses `print()` for compatibility outside Jupyter
- **Fixed hardcoded values**: Cumulative effects computed dynamically

---

**Last Updated**: January 2025
