# Effect of Police Shooting Awareness on Mental Health EMS Calls in NYC

MIT UROP research project investigating how public awareness of fatal police shootings affects mental health-related emergency medical service calls in New York City, with analysis of heterogeneous effects across community districts.

## Research Questions

1. Do increases in public awareness of fatal police shootings lead to changes in mental health-related EMS calls?
2. What is the temporal profile of these effects (immediate vs. delayed)?
3. Do effects vary across community districts based on demographic characteristics?

## Project Structure

```
project_package/
├── data/
│   ├── raw/                    # Original data files
│   └── processed/              # Cleaned/merged data
├── scripts/
│   ├── 01_data_cleaning.py     # Clean EMS data and create panel
│   ├── 02_merge_awareness.py   # Merge Twitter awareness data
│   ├── 03_regression_analysis.py  # Distributed lag regression models
│   ├── 04_visualizations.py    # Create impulse response plots
│   ├── 10d_parse_cd_demographics.py  # Parse demographic data
│   ├── 11_merge_demographics.py  # Merge demographics with panel
│   ├── 12_heterogeneous_effects.py  # Heterogeneous effects analysis
│   └── run_analysis.py          # Run main analysis pipeline
├── outputs/
│   ├── figures/                 # Visualizations
│   └── tables/                  # Regression results
├── docs/                        # Documentation
│   ├── METHODOLOGY.md           # Detailed methodology and reasoning
│   ├── HETEROGENEOUS_EFFECTS_RESULTS.md  # Results summary
│   ├── ems_research_paper.pdf   # Research paper
│   └── research_paper.tex       # LaTeX research paper
└── notebooks/                   # Original Jupyter notebook
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Data Files

Place the following files in `data/raw/`:
- `EMS_Incident_Dispatch_Data*.csv` (NYC EMS dispatch data)
- `211118_tweet_count_name_date.csv` (Twitter awareness data, part 1)
- `220126_final_daily_tweet_count.csv` (Twitter awareness data, part 2)
- `sf1_dp_cd_demoprofile.xlsx` (Community district demographics - optional, for heterogeneity analysis)

### 3. Run Main Analysis

```bash
python scripts/run_analysis.py
```

This runs the complete pipeline:
1. Clean EMS data and create daily panel
2. Merge Twitter awareness data and create lagged variables
3. Run distributed lag regression models
4. Create impulse response function visualizations

### 4. Run Heterogeneous Effects Analysis (Optional)

```bash
# First, parse demographics
python scripts/10d_parse_cd_demographics.py

# Then merge with panel
python scripts/11_merge_demographics.py

# Finally, run heterogeneous effects analysis
python scripts/12_heterogeneous_effects.py
```

## Key Findings

### Main Effects
- **7-day lag effect**: Statistically significant increase in mental health call share (β = 0.0014, SE = 0.00038, p < 0.001)
- **Cumulative effect (0-7 days)**: 0.0008 increase per 1σ awareness spike
- **Citywide impact**: ~0.04 additional mental health calls per week per standard deviation increase in awareness
- **Placebo test**: No effect on total call volume, supporting mental health-specific interpretation

### Heterogeneous Effects
- **% Black districts**: Effect decreases with % Black, becomes negative in highest quartile
- **% Hispanic districts**: Effect decreases but remains positive
- **% White districts**: Effect increases with % White
- **% Asian districts**: Effect increases with % Asian

See `docs/HETEROGENEOUS_EFFECTS_RESULTS.md` for detailed results.

## Methodology

We use a distributed lag model with community district fixed effects:

```
mh_share_it = α_i + Σ(β_k · awareness_{t-k}) + X_it'γ + ε_it
```

Where:
- `mh_share_it`: Mental health calls / total calls in district i on day t
- `awareness_{t-k}`: Z-scored Twitter activity at lag k (k = 0, 1, 2, 3, 7, 14, 21, 28)
- `α_i`: Community district fixed effects
- `X_it`: Day of week, month×year interactions, holidays
- Standard errors clustered at community district level

See `docs/METHODOLOGY.md` for detailed explanation of methodological choices and reasoning.

## Data Sources

### EMS Data
- **Source**: NYC OpenData
- **Time period**: 2005-2025
- **Level**: Community district × day
- **Mental health codes**: EDP, ALTMEN, ALTMFC, ALTMFT, JUMPDN, JUMPUP, JUMPDC, OD, ODC, POISON, DRUG

### Twitter Awareness Data
- **Time period**: 2017-2020
- **Level**: Citywide daily counts
- **Processing**: Combined from two datasets, z-scored

### Demographics
- **Source**: 2010 U.S. Census via NYC Department of City Planning
- **Variables**: Race/ethnicity percentages, housing tenure, income, education

## Output Files

### Tables (`outputs/tables/`)
- `dl_model_params_with_cdfe.csv`: Regression coefficients and standard errors
- `ir_mhshare_cdfe.csv`: Impulse response function coefficients
- `heterogeneous_effects_interactions.csv`: Interaction term coefficients
- `heterogeneous_effects_stratified.csv`: Stratified analysis results

### Figures (`outputs/figures/`)
- `ir_mhshare_cdfe_fixed.png`: Impulse response function plot
- `heterogeneous_effects_pct_*.png`: Heterogeneous effects by demographic quartiles

## Documentation

- **`docs/METHODOLOGY.md`**: Detailed methodology, data processing decisions, and analytical choices
- **`docs/HETEROGENEOUS_EFFECTS_RESULTS.md`**: Results summary and interpretation
- **`docs/research_paper.tex`**: Complete research paper (LaTeX format)

## Contact

MIT Undergraduate Research Opportunities Program (UROP)  
Under Professor Justin Steil, Department of Urban Studies and Planning  
Massachusetts Institute of Technology  
Student: Abrahim Mahmud
