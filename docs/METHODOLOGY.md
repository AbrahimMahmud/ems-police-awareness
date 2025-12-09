# Methodology and Research Design

This document explains the methodology, data processing decisions, and analytical choices made in this research project.

## Research Question

**How does public awareness of fatal police shootings affect mental health-related emergency medical service calls in New York City, and do these effects vary across community districts based on demographic characteristics?**

## Data Sources and Processing

### 1. EMS Data Cleaning (`01_data_cleaning.py`)

**Why we filter certain calls:**
- **Special events, standby, transfers**: These are non-routine calls that don't reflect typical emergency mental health needs
- **Cancellations and duplicates**: These don't represent actual service utilization
- **Disposition code 87**: Specific exclusion category in NYC EMS data

**Why we aggregate to district-day level:**
- Community districts are the appropriate geographic unit for policy analysis in NYC
- Daily aggregation captures temporal variation while maintaining sufficient sample size
- Mental health share (mh_calls/total_calls) is more stable than raw counts

**Why we restrict to days with ≥5 calls:**
- Prevents unstable estimates of mental health share when total calls are very low
- Ensures meaningful variation in the outcome variable

### 2. Twitter Awareness Measure (`02_merge_awareness.py`)

**Why use Twitter data:**
- Provides real-time, daily-level measure of public attention
- Captures both media coverage and organic public discussion
- Available at citywide level, matching the geographic scope of police shooting awareness

**Why z-score the awareness measure:**
- Standardizes across different scales of the two Twitter datasets
- Allows interpretation in terms of "typical variation" (standard deviations)
- Makes coefficients comparable across different awareness spikes

**Why create lags 0-28 days:**
- Captures immediate effects (lag 0)
- Short-term effects (1-3 days)
- Medium-term effects (7 days - key finding)
- Longer-term persistence (14, 21, 28 days)

### 3. Control Variables

**Day of week fixed effects:**
- Mental health calls vary systematically by day of week (e.g., weekends)
- Controls for day-of-week patterns unrelated to awareness

**Month × Year interactions:**
- Controls for seasonal patterns (e.g., winter depression)
- Controls for long-term trends (e.g., increasing mental health awareness over time)
- More flexible than separate month and year effects

**Federal holidays:**
- Mental health calls may spike on holidays
- Controls for holiday effects separate from awareness

**Community district fixed effects:**
- Controls for all time-invariant district characteristics
- Accounts for baseline differences in mental health needs, service availability, demographics
- Critical for causal identification

**Why we exclude COVID phase:**
- Perfectly collinear with month×year fixed effects for 2020-2021
- Would cause multicollinearity and missing standard errors

### 4. Regression Model Specification (`03_regression_analysis.py`)

**Why distributed lag model:**
- Allows effects to vary over time
- Captures delayed responses (key finding: 7-day lag)
- More flexible than single lag or cumulative measures

**Why clustered standard errors:**
- Errors are correlated within community districts over time
- Accounts for serial correlation and heteroskedasticity
- Standard approach for panel data

**Why community district fixed effects:**
- Controls for unobserved time-invariant characteristics
- Improves causal identification
- Reduces omitted variable bias

**Why we examine mh_share rather than mh_calls:**
- Controls for overall EMS utilization patterns
- More interpretable: represents composition of calls
- Less sensitive to changes in total call volume

**Placebo test (total_calls):**
- If awareness affects total calls, it suggests general EMS utilization increase rather than mental health-specific effect
- Finding: no effect on total calls, supporting mental health-specific interpretation

### 5. Demographic Data Processing (`10d_parse_cd_demographics.py`)

**Why use 2010 Census data:**
- Most comprehensive community district-level demographic data available
- Time-invariant for our analysis period (2017-2020)
- Sufficient variation across districts for heterogeneity analysis

**Why extract specific variables:**
- **Race/ethnicity percentages**: Test hypotheses about differential effects by community composition
- **Housing tenure**: Proxy for socioeconomic status
- **Income and education**: Additional socioeconomic measures (when available)

**Why hierarchical parsing:**
- Excel file structure has sections for each CD with variables as rows
- Requires custom parsing to extract structured data
- Ensures accurate matching of variables to CDs

### 6. Heterogeneous Effects Analysis (`12_heterogeneous_effects.py`)

**Why interaction terms:**
- Tests whether effects vary continuously with demographic characteristics
- More statistically powerful than stratified analysis
- Allows for non-linear relationships

**Why stratified analysis:**
- Easier to interpret: shows effects for specific demographic groups
- Doesn't assume linearity in interactions
- Provides robustness check for interaction results

**Why quartiles:**
- Ensures sufficient sample size in each group
- Captures meaningful variation in demographics
- Standard approach in heterogeneity analysis

**Why focus on 7-day lag:**
- Main finding from primary analysis
- Represents key temporal pattern
- Most policy-relevant (week-long response window)

## Key Analytical Decisions

### 1. Lag Specification

We examine lags at {0, 1, 2, 3, 7, 14, 21, 28} days rather than all intermediate lags:
- **Computational efficiency**: Fewer parameters to estimate
- **Statistical power**: More observations per parameter
- **Interpretability**: Focuses on key time points
- **Prior expectations**: Based on mental health response literature

### 2. Sample Restrictions

We restrict to days with ≥5 total calls:
- **Statistical stability**: Prevents extreme mh_share values from small denominators
- **Practical relevance**: Focuses on districts with meaningful EMS activity
- **Robustness**: Results are similar with different thresholds (tested)

### 3. Mental Health Call Classification

We include 11 call types as mental health-related:
- **EDP, ALTMEN, ALTMFC, ALTMFT**: Direct mental health calls
- **JUMPDN, JUMPUP, JUMPDC**: Suicide-related
- **OD, ODC, POISON, DRUG**: Substance-related (often co-occurring with mental health)

**Why include substance-related:**
- Substance use often co-occurs with mental health crises
- Overdoses may be suicide attempts or mental health-related
- Broader definition captures more mental health-related distress

### 4. Standard Error Clustering

We cluster at community district level:
- **Serial correlation**: Errors correlated within districts over time
- **Heteroskedasticity**: Variance may differ across districts
- **Standard practice**: Appropriate for panel data with fixed effects

### 5. Model Selection

We use OLS with fixed effects rather than:
- **Poisson/Negative Binomial**: mh_share is continuous, not count
- **Logit**: mh_share is not binary
- **Random effects**: Fixed effects preferred when interested in within-district variation

## Limitations and Robustness

### 1. Measurement of Awareness

**Limitation**: Twitter data may not perfectly reflect individual-level exposure
- Some people highly aware without Twitter
- Some see Twitter content without internalizing it

**Mitigation**: Twitter activity likely correlated with broader media coverage and public discourse

### 2. Measurement of Mental Health

**Limitation**: EMS calls capture only acute crises, not less severe cases
- May underestimate total mental health impact
- Effects we document may be "tip of iceberg"

**Mitigation**: Acute crises are policy-relevant and measurable

### 3. Temporal Mismatch

**Limitation**: Twitter data covers 2017-2020, EMS data extends to 2025
- Cannot examine effects in more recent years
- Analysis period limited to 2017-2020

**Mitigation**: 2017-2020 includes several high-profile incidents, providing substantial variation

### 4. Demographic Data

**Limitation**: 2010 Census data may not reflect current composition
- Gentrification and demographic shifts in some areas
- May misclassify some districts

**Mitigation**: For examining heterogeneity, 2010 data still captures meaningful variation across districts

### 5. Causality

**Limitation**: Cannot definitively establish causality
- Unobserved time-varying factors could confound
- Reverse causality possible (though unlikely)

**Mitigation**: 
- Placebo test (no effect on total calls) supports causal interpretation
- Specific temporal pattern (7-day lag) suggests causal mechanism
- Fixed effects control for many confounders

## Robustness Checks

1. **Different lag specifications**: Results robust to alternative lag sets
2. **Different sample restrictions**: Results similar with different call thresholds
3. **Alternative mental health definitions**: Results robust to excluding substance-related calls
4. **Different clustering**: Results similar with alternative standard error specifications
5. **Placebo tests**: No effect on total calls supports mental health-specific interpretation

## Next Steps and Extensions

1. **Mechanism investigation**: Qualitative research on how communities interpret and respond to awareness
2. **Additional outcomes**: Hospitalizations, outpatient visits, survey-based measures
3. **Longer-term effects**: Effects beyond 28 days, cumulative impacts
4. **Event-specific analysis**: Which types of events generate strongest responses
5. **Income and SES**: Examine effects by socioeconomic status (data limitations prevented this)

