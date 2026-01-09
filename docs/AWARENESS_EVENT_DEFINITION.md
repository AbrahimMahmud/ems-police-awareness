# Definition of "High Awareness Event Days"

## Overview

A **high awareness event day** is defined as any day where public awareness of police killings (as measured by Twitter activity) exceeds a specified threshold above the mean level of awareness.

## How Awareness is Measured

### 1. Raw Data Source
- **Twitter tweet counts** about fatal police shootings
- Two data sources merged:
  - `211118_tweet_count_name_date.csv`: Daily tweet counts for individual incidents (2017-2018)
  - `220126_final_daily_tweet_count.csv`: Final daily tweet count aggregations (2018-2020)
- Combined into a single daily time series: `tweet_count_all`

### 2. Standardization (Z-Scoring)
The raw tweet counts are standardized to create `awareness_z`:

```python
awareness_z = (tweet_count_all - mean(tweet_count_all)) / std(tweet_count_all)
```

**Why z-score?**
- Standardizes across different scales of the two Twitter datasets
- Allows interpretation in terms of "typical variation" (standard deviations)
- Makes coefficients comparable across different awareness spikes
- Accounts for baseline differences in Twitter activity over time

### 3. Interpretation of `awareness_z`
- **Mean**: 0 (by construction)
- **Standard deviation**: 1 (by construction)
- **Positive values**: Above-average awareness (more tweets than typical)
- **Negative values**: Below-average awareness (fewer tweets than typical)
- **Value of 1.0**: One standard deviation above mean (84th percentile)
- **Value of 2.0**: Two standard deviations above mean (98th percentile)

## Definition of High Awareness Days

A day is classified as a **high awareness event day** if:

```
awareness_z > threshold
```

Where `threshold` is typically:
- **1.0 standard deviation**: Moderate high awareness (top ~16% of days)
- **1.5 standard deviations**: High awareness (top ~7% of days)
- **2.0 standard deviations**: Very high awareness (top ~2% of days)

## Geographic Scope

**Important**: The awareness measure is **citywide**, not district-specific.

- All community districts share the same `awareness_z` value on a given day
- This reflects that information about police shootings spreads across the entire city through:
  - Media coverage (TV, newspapers, online news)
  - Social media (Twitter, Facebook, etc.)
  - Word of mouth and community networks

## Examples from the Data

Based on the analysis scripts, here are examples of what high awareness days look like:

### Actual High Awareness Days (Top Examples)

**Highest awareness days (awareness_z > 2.0 SD):**
- **2020-05-29**: awareness_z = 20.43 (George Floyd killing aftermath)
- **2020-05-28**: awareness_z = 9.86
- **2020-06-02**: awareness_z = 9.16 (Protests peak)
- **2020-06-01**: awareness_z = 8.94
- **2020-06-08**: awareness_z = 8.53
- **2020-05-30**: awareness_z = 8.37
- **2020-06-03**: awareness_z = 8.32
- **2020-06-14**: awareness_z = 7.98
- **2020-05-27**: awareness_z = 6.97
- **2020-06-04**: awareness_z = 6.59

**Note**: The highest awareness days cluster around **late May/early June 2020**, corresponding to:
- The killing of George Floyd (May 25, 2020)
- Nationwide protests and civil unrest
- Extensive media coverage and social media activity
- Policy discussions and public discourse

This demonstrates that high awareness days capture major events that generate sustained public attention.

### Threshold = 1.0 SD
- Days where awareness is in the **top 16%** of all days
- These are days with noticeably elevated Twitter activity about police killings
- May include:
  - Days when major police killing incidents occur
  - Days with significant media coverage of police violence
  - Days with protests or public events related to police killings

### Threshold = 1.5 SD
- Days where awareness is in the **top 7%** of all days
- These are days with very high Twitter activity
- Typically correspond to:
  - High-profile police killing incidents
  - Major news events or breaking stories
  - Significant public response (protests, vigils, etc.)

### Threshold = 2.0 SD
- Days where awareness is in the **top 2%** of all days
- These are days with extremely high Twitter activity
- Usually correspond to:
  - Very high-profile incidents (national news)
  - Major policy announcements or legal decisions
  - Large-scale public events or movements

## How High Awareness Days Are Used in Analysis

### 1. Threshold Analysis (`14_analysis_by_awareness_threshold.py`)
- Creates binary indicators: `high_awareness_1.0sd`, `high_awareness_1.5sd`, `high_awareness_2.0sd`
- Uses these as independent variables in regression models
- Examines effects at different lags (0, 1, 2, 3, 7, 14 days)

### 2. Difference-in-Differences Analysis (`16_difference_in_differences.py`)
- **Treatment group**: Days with `awareness_z > 1.5 SD`
- **Control group**: Days with `awareness_z ≤ 1.5 SD`
- Compares mental health call outcomes between treated and control days
- Creates event windows: 14 days before to 14 days after each high awareness day

### 3. Trend Charts (`15_trend_charts.py`)
- Identifies high awareness event dates
- Creates windows around each event (±20 days)
- Plots average mental health call share in the days surrounding events
- Shows both:
  - By awareness threshold (high awareness days)
  - By actual police killing dates (very high threshold, 2.0 SD)

## Key Characteristics

### Temporal Pattern
- High awareness days are **not evenly distributed** over time
- They cluster around:
  - Actual police killing incidents
  - Media coverage spikes
  - Public events and protests
  - Policy announcements

### Frequency
From the analysis:
- **1.0 SD threshold**: ~16% of days (relatively common)
- **1.5 SD threshold**: ~7% of days (moderately rare)
- **2.0 SD threshold**: ~2% of days (rare events)

### Relationship to Actual Events
- High awareness days **correlate with** but are **not identical to** actual police killing dates
- Some high awareness days may be:
  - The day of a killing (immediate awareness)
  - Days after a killing (sustained coverage)
  - Days with multiple killings
  - Days with major news coverage of past killings
  - Days with protests or public events

## Why This Definition Matters

1. **Policy Relevance**: High awareness days represent periods when public attention is focused on police violence, making them policy-relevant intervention points

2. **Causal Identification**: Using thresholds (rather than continuous measures) allows for clearer causal interpretation in DID designs

3. **Heterogeneity**: Different thresholds capture different types of events (routine vs. extreme)

4. **Robustness**: Multiple thresholds allow us to test whether effects are consistent across different definitions of "high awareness"

## Limitations

1. **Twitter as Proxy**: Twitter activity may not perfectly capture all forms of awareness (TV news, conversations, etc.)

2. **Citywide Measure**: All districts get the same awareness value, even though local awareness may vary

3. **Threshold Choice**: The specific thresholds (1.0, 1.5, 2.0 SD) are somewhat arbitrary, though they correspond to meaningful percentiles

4. **Temporal Aggregation**: Daily aggregation may miss within-day variation in awareness

## What Exactly is the "Event Day"?

**The high awareness event day is the actual calendar date when `awareness_z > threshold`.**

**Important**: This is **NOT necessarily the date of the actual police killing**. It is the date when **public awareness/Twitter activity peaked**, which may be:
- The same day as a killing (immediate awareness)
- Days after a killing (when news spreads)
- Days with sustained coverage or protests
- Days with multiple incidents contributing to awareness

**Example**: George Floyd was killed on May 25, 2020, but the highest awareness day was May 29, 2020 (awareness_z = 20.43), when public attention and protests peaked.

## Summary

**A high awareness event day is a day when Twitter activity about police killings exceeds a specified number of standard deviations above the mean, indicating elevated public attention to police violence. The "event day" is the calendar date when this threshold is exceeded, which may differ from the actual incident date. These days serve as natural experiments to study the causal effects of awareness on mental health outcomes.**

*For a detailed explanation of exactly which day we use, see: `docs/HIGH_AWARENESS_EVENT_DAY_EXPLANATION.md`*

---

*For technical details, see:*
- `scripts/02_merge_awareness.py`: How awareness_z is calculated
- `scripts/14_analysis_by_awareness_threshold.py`: How thresholds are applied
- `scripts/16_difference_in_differences.py`: How high awareness days are used in DID

