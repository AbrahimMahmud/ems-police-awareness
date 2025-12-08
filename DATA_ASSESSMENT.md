# Data Sufficiency Assessment

## Current Data Files

### 1. EMS Data
- **File**: `EMS_Incident_Dispatch_Data_20251017.csv`
- **Size**: 6.2 GB
- **Rows**: ~28.7 million
- **Date Range**: 2005-01-01 onwards (starts from sample: `01/01/2005 02:02:20 AM`)
- **Coverage**: All NYC community districts, all call types

### 2. Twitter Awareness Data

#### File 1: `211118_tweet_count_name_date.csv`
- **Size**: 1.9 MB
- **Rows**: ~45,184
- **Date Range**: 2017-01-01 to 2020-12-31
- **Structure**: Individual incidents (person killed, date, tweet counts)
- **Coverage**: 4 years

#### File 2: `220126_final_daily_tweet_count.csv`
- **Size**: 96 KB
- **Rows**: ~1,462
- **Date Range**: 2017-01-01 to 2020-12-27
- **Structure**: Daily aggregated counts
- **Coverage**: ~4 years

## Key Findings

### ✅ Strengths

1. **Large EMS Dataset**: ~28.7M rows provides excellent statistical power
2. **Long EMS Time Series**: 2005-2024 (estimated) = ~20 years of data
3. **Complete Coverage**: All community districts and call types
4. **Good Data Quality**: Files appear well-structured

### ⚠️ Limitations

1. **Limited Overlap Period**: 
   - Twitter data: 2017-2020 (4 years)
   - EMS data: 2005+ (20+ years)
   - **Overlap: Only 4 years (2017-2020)**
   - This is the critical limitation

2. **Recent Data Gap**:
   - Twitter data ends in 2020
   - Missing 2021-2024 period (important events like 2020 protests aftermath, COVID impacts)
   - Cannot analyze recent trends

3. **Pre-2017 Gap**:
   - No Twitter data before 2017
   - Cannot analyze earlier periods (e.g., 2014-2016 which had significant events)

## Sufficiency Assessment

### For Your Research Questions:

#### 1. "Do increases in public attention lead to changes in MH-related EMS calls?"
**Answer: PARTIALLY SUFFICIENT**
- ✅ 4 years of overlap provides enough data for distributed lag models
- ✅ Large sample size (28M+ EMS rows) ensures statistical power
- ⚠️ Limited to 2017-2020 period only
- ⚠️ Cannot test if effects changed over time or in different contexts

#### 2. "Are effects concentrated in particular CDs by socioeconomic/demographic characteristics?"
**Answer: SUFFICIENT (with caveat)**
- ✅ 59 community districts × 4 years = ~86,000 district-days (after filtering)
- ✅ Sufficient for heterogeneity analysis
- ⚠️ Need to merge in CD-level demographic data (not currently in dataset)
- ⚠️ 4 years may limit ability to detect rare but important events

#### 3. "What is the temporal profile (immediate vs. persistent over days/weeks)?"
**Answer: SUFFICIENT**
- ✅ 4 years provides enough variation to estimate lag effects
- ✅ Distributed lag model (0-28 days) is feasible
- ✅ Can distinguish immediate vs. delayed effects

## Statistical Power Considerations

### Panel Size
- **Potential observations**: 59 CDs × 1,461 days = 86,199 district-days
- **After filtering** (≥5 calls/day): ~70,000-80,000 observations (estimated)
- **Assessment**: ✅ Sufficient for regression with fixed effects

### Variation Requirements
- **Awareness variation**: ✅ Twitter data shows daily variation
- **Outcome variation**: ✅ MH calls vary across districts and time
- **Exposure variation**: ✅ Need to verify sufficient spikes in awareness

## Recommendations

### ✅ Proceed with Analysis
The data is **sufficient to draw conclusions** for the 2017-2020 period, with these caveats:

1. **Scope Limitations**: Results apply to 2017-2020 only
   - Cannot generalize to other time periods
   - Important to note this in paper

2. **Missing Context**: 
   - 2020 had COVID-19 pandemic (already controlled for in model)
   - 2020 had major protests (may be captured in awareness measure)
   - Cannot compare to pre-2017 or post-2020 periods

3. **Data Quality Checks Needed**:
   - Verify all 59 community districts are present
   - Check for systematic missing dates in Twitter data
   - Validate MH call code classifications
   - Check for data entry errors or outliers

### 🔧 Suggested Improvements

1. **Extend Twitter Data** (if possible):
   - Collect 2021-2024 data to extend analysis period
   - Would allow testing of temporal stability of effects
   - Would increase statistical power

2. **Add Pre-2017 Data** (if possible):
   - Historical Twitter data would enable before/after comparisons
   - Could test if effects changed over time

3. **Merge Demographic Data**:
   - Add CD-level socioeconomic characteristics
   - Enable heterogeneity analysis by demographics
   - Would address research question #2 more fully

4. **Data Validation**:
   - Run `scripts/00_assess_data.py` after installing dependencies
   - Check processed panel for completeness
   - Examine descriptive statistics

## Conclusion

**YES, the data is sufficient to draw conclusions**, but with important limitations:

### What You CAN Do:
- ✅ Estimate causal effects of awareness on MH calls (2017-2020)
- ✅ Test for heterogeneity across community districts
- ✅ Examine temporal lag structure (immediate vs. delayed effects)
- ✅ Run placebo tests (total calls)
- ✅ Calculate effect sizes and confidence intervals

### What You CANNOT Do:
- ❌ Generalize beyond 2017-2020 period
- ❌ Compare to pre-2017 or post-2020 periods
- ❌ Test if effects changed over longer time horizons
- ❌ Analyze recent events (2021-2024)

### Next Steps:
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run data assessment**: `python scripts/00_assess_data.py`
3. **Run analysis pipeline**: `python scripts/run_analysis.py`
4. **Review results** and interpret with awareness of temporal limitations
5. **Consider collecting additional data** if time/resources permit

## Data Quality Checklist

Before finalizing analysis, verify:
- [ ] All 59 community districts present in panel
- [ ] No systematic missing dates in Twitter data
- [ ] MH call codes correctly classified
- [ ] Date ranges match expectations
- [ ] No data entry errors or outliers
- [ ] Sufficient variation in awareness measure
- [ ] Panel is balanced (or document imbalance)

---

**Assessment Date**: January 2025
**Assessor**: Based on file inspection and project requirements

