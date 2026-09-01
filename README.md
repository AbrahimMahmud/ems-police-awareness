# Effect of Police Shooting Awareness on Mental Health EMS Calls in NYC

MIT UROP research project investigating how public awareness of fatal police shootings affects mental health-related emergency medical service calls in New York City, with analysis of heterogeneous effects across community districts.

## Research Questions

1. Do increases in public awareness of fatal police shootings lead to changes in mental health-related EMS calls?
2. What is the temporal profile of these effects (immediate vs. delayed)?
3. Do effects vary across community districts based on demographic characteristics?
4. Are findings robust across different model specifications and analytical approaches?

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
│   ├── 03b_progressive_regressions.py  # Progressive model specification
│   ├── 04_visualizations.py    # Create impulse response plots
│   ├── 05_descriptive_statistics.py  # Comprehensive descriptive stats
│   ├── 06_call_statistics_summary.py  # Call volume statistics
│   ├── 10d_parse_cd_demographics.py  # Parse demographic data
│   ├── 11_merge_demographics.py  # Merge demographics with panel
│   ├── 12_heterogeneous_effects.py  # Heterogeneous effects analysis
│   ├── 13_regression_by_demographics.py  # Demographics as predictors
│   ├── 14_analysis_by_awareness_threshold.py  # Threshold-based analysis
│   ├── 15_trend_charts.py      # Event-based trend charts
│   ├── 16_difference_in_differences.py  # DID analysis
│   ├── 17_trend_vs_threshold.py  # Comparison of approaches
│   ├── 18_comprehensive_visualizations.py  # Publication-ready figures
│   ├── 19_visualize_awareness_distribution.py  # Awareness distribution plots
│   ├── 20_create_event_day_summary.py  # Event day documentation
│   └── run_analysis.py          # Run main analysis pipeline
├── outputs/
│   ├── figures/                 # Visualizations
│   └── tables/                  # Regression results
└── docs/                        # Documentation
    ├── LITERATURE_REVIEW.md     # Comparable work, positioning, and research agenda
    ├── METHODOLOGY.md           # Detailed methodology and reasoning
    ├── RESULTS_INTERPRETATION.md  # Comprehensive results interpretation
    ├── AWARENESS_EVENT_DEFINITION.md  # Definition of high awareness days
    ├── HIGH_AWARENESS_EVENT_DAY_EXPLANATION.md  # Detailed event day explanation
    ├── HETEROGENEOUS_EFFECTS_RESULTS.md  # Heterogeneous effects results
    ├── ems_research_paper.pdf   # Research paper
    └── research_paper.tex       # LaTeX research paper
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

### 4. Run Additional Analyses

```bash
# Progressive regression models (robustness check)
python scripts/03b_progressive_regressions.py

# Descriptive statistics
python scripts/05_descriptive_statistics.py

# Call statistics summary
python scripts/06_call_statistics_summary.py

# Awareness threshold analysis
python scripts/14_analysis_by_awareness_threshold.py

# Difference-in-differences analysis
python scripts/16_difference_in_differences.py

# Trend charts (20 days before/after events)
python scripts/15_trend_charts.py

# Comprehensive visualizations
python scripts/18_comprehensive_visualizations.py

# Awareness distribution and event day summaries
python scripts/19_visualize_awareness_distribution.py
python scripts/20_create_event_day_summary.py
```

### 5. Run Heterogeneous Effects Analysis (Optional)

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
- **7-day lag effect**: Statistically significant increase in mental health call share (β = 0.00139, SE = 0.00038, p < 0.001)
- **Robustness**: Effect remains stable across progressive model specifications (0.00139 in full model)
- **Cumulative effect (0-7 days)**: 0.0008 increase per 1σ awareness spike
- **Citywide impact**: ~0.08 additional mental health calls per district per day, or ~4.7 calls citywide per day (~33 calls per week)
- **Placebo test**: No effect on total call volume, supporting mental health-specific interpretation

### Robustness Analysis
- **Progressive models**: Effect increases from 0.00053 (awareness only) to 0.00142 (with month×year controls), then stabilizes at 0.00139 (full model)
- **Threshold analysis**: High awareness days (1.0 SD) show significant effect at lag 7 (0.00315, p < 0.05)
- **Difference-in-differences**: Confirms main finding using alternative identification strategy (DID coefficient = 0.00205)

### Heterogeneous Effects
- **% Black districts**: Effect decreases with % Black, becomes negative in highest quartile
- **% Hispanic districts**: Effect decreases but remains positive
- **% White districts**: Effect increases with % White
- **% Asian districts**: Effect increases with % Asian

### High Awareness Event Days
- **Definition**: Calendar dates when Twitter activity about police killings exceeded a threshold (typically 1.0, 1.5, or 2.0 standard deviations)
- **Important**: Event days represent when **public awareness peaked**, not necessarily the date of the actual police killing
- **Example**: George Floyd was killed May 25, 2020, but the highest awareness event day was May 29, 2020 (awareness_z = 20.43)
- **Frequency**: 35 high awareness days (1.5 SD threshold) during 2017-2020 analysis period

See `docs/RESULTS_INTERPRETATION.md` for comprehensive results and interpretation.

## Methodology

### Main Approach: Distributed Lag Model

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

### Alternative Approaches

1. **Progressive Model Specification**: Progressively add controls to assess robustness
2. **Awareness Threshold Analysis**: Binary indicators for high awareness days (1.0, 1.5, 2.0 SD thresholds)
3. **Difference-in-Differences**: High awareness days as treatment, normal days as control
4. **Event Study**: Dynamic effects around high awareness events (±14 days)

See `docs/METHODOLOGY.md` for detailed explanation of methodological choices and reasoning.

## Data Sources

### EMS Data
- **Source**: NYC OpenData
- **Time period**: 2005-2025 (analysis period: 2017-2020)
- **Level**: Community district × day
- **Mental health codes**: EDP, ALTMEN, ALTMFC, ALTMFT, JUMPDN, JUMPUP, JUMPDC, OD, ODC, POISON, DRUG
- **Sample**: 85,139 district-day observations (2017-2020, ≥5 calls per day)

### Twitter Awareness Data
- **Time period**: 2017-2020
- **Level**: Citywide daily counts
- **Processing**: Combined from two datasets, z-scored to create `awareness_z`
- **High awareness days**: Days where `awareness_z > threshold` (1.0, 1.5, or 2.0 SD)
- **Key insight**: Event days represent when public awareness peaked, which may be days after actual incidents

### Demographics
- **Source**: 2010 U.S. Census via NYC Department of City Planning
- **Variables**: Race/ethnicity percentages (White, Black, Hispanic, Asian), housing tenure
- **Note**: Using 2010 Census data for analysis period 2017-2020 (time-invariant district characteristics)

## Output Files

### Tables (`outputs/tables/`)
- `ir_mhshare_cdfe.csv`: Impulse response function coefficients
- `regression_progressive_lag7_comparison.csv`: Progressive model robustness check
- `regression_progressive_model_*.csv`: Individual progressive model results
- `awareness_threshold_analysis.csv`: Threshold-based analysis results
- `awareness_threshold_*sd_params.csv`: Threshold model parameters
- `did_results.csv`: Difference-in-differences results
- `did_event_study_coefficients.csv`: DID event study coefficients
- `call_statistics_summary.csv`: Call volume statistics
- `descriptive_stats_all_variables.csv`: Comprehensive descriptive statistics
- `trend_chart_*.csv`: Event-based trend data
- `trend_vs_threshold_comparison.csv`: Comparison of approaches
- `event_day_summary.csv`: High awareness event day summary
- `high_awareness_event_days_list.csv`: Complete list of event days
- `heterogeneous_effects_interactions.csv`: Interaction term coefficients
- `heterogeneous_effects_stratified.csv`: Stratified analysis results

### Figures (`outputs/figures/`)
- `ir_mhshare_cdfe_fixed.png`: Impulse response function plot
- `progressive_regression_robustness.png`: Robustness across model specifications
- `awareness_threshold_effects.png`: Effects at different thresholds
- `did_event_study.png`: Difference-in-differences event study
- `call_statistics_trends.png`: Call volume trends over time
- `distributed_lag_vs_threshold.png`: Comparison of approaches
- `summary_dashboard.png`: Multi-panel summary figure
- `awareness_distribution.png`: Distribution of awareness levels
- `high_awareness_timeline.png`: Timeline of high awareness events
- `event_day_explanation.png`: Visual explanation of event days
- `trend_chart_awareness_threshold.png`: Trends around high awareness days
- `trend_chart_killing_dates.png`: Trends around actual killing dates
- `heterogeneous_effects_pct_*.png`: Heterogeneous effects by demographic quartiles

## Documentation

- **`docs/LITERATURE_REVIEW.md`**: Comparable studies, how their designs differ from ours, and the resulting research agenda
- **`docs/METHODOLOGY.md`**: Detailed methodology, data processing decisions, and analytical choices
- **`docs/RESULTS_INTERPRETATION.md`**: Comprehensive results interpretation with all findings
- **`docs/AWARENESS_EVENT_DEFINITION.md`**: Technical definition of high awareness event days
- **`docs/HIGH_AWARENESS_EVENT_DAY_EXPLANATION.md`**: Detailed explanation of what event days are and why they matter
- **`docs/HETEROGENEOUS_EFFECTS_RESULTS.md`**: Heterogeneous effects results summary
- **`docs/research_paper.tex`**: Complete research paper (LaTeX format, updated with all analyses)

## Key Concepts

### High Awareness Event Days
- **What they are**: Calendar dates when Twitter activity about police killings exceeded a threshold (e.g., 1.5 standard deviations above mean)
- **Why they matter**: Represent when public attention peaked, which may differ from actual incident dates
- **Example**: May 29, 2020 had the highest awareness (z = 20.43), 4 days after the May 25, 2020 killing
- **Policy relevance**: Mental health interventions should target high awareness periods, not just incident dates

### Awareness Measure
- **Raw data**: Daily Twitter tweet counts about fatal police shootings
- **Processing**: Z-scored (standardized) to create `awareness_z` (mean = 0, SD = 1)
- **Interpretation**: Values represent standard deviations from mean awareness
- **Geographic scope**: Citywide (all districts share same value on a given day)

## Analysis Workflow

1. **Data Preparation**
   - Clean EMS data (`01_data_cleaning.py`)
   - Merge awareness data (`02_merge_awareness.py`)
   - Parse and merge demographics (`10d_parse_cd_demographics.py`, `11_merge_demographics.py`)

2. **Main Analysis**
   - Distributed lag models (`03_regression_analysis.py`)
   - Progressive robustness check (`03b_progressive_regressions.py`)
   - Descriptive statistics (`05_descriptive_statistics.py`)

3. **Alternative Approaches**
   - Threshold analysis (`14_analysis_by_awareness_threshold.py`)
   - Difference-in-differences (`16_difference_in_differences.py`)
   - Trend charts (`15_trend_charts.py`)

4. **Visualization and Documentation**
   - Comprehensive figures (`18_comprehensive_visualizations.py`)
   - Awareness distribution (`19_visualize_awareness_distribution.py`)
   - Event day summaries (`20_create_event_day_summary.py`)

5. **Heterogeneous Effects** (optional)
   - Interaction models (`12_heterogeneous_effects.py`)
   - Demographic regressions (`13_regression_by_demographics.py`)

## Contact

MIT Undergraduate Research Opportunities Program (UROP)  
Under Professor Justin Steil, Department of Urban Studies and Planning  
Massachusetts Institute of Technology  
Student: Abrahim Mahmud
