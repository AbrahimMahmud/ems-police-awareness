# IRF Issue Diagnosis and Fix

## Problem Summary

The Impulse Response Function (IRF) plot appears flat, and most lag coefficients have missing standard errors. This indicates a serious model specification issue.

## Root Cause: Perfect Multicollinearity

### The Issue

The model includes both:
- `C(covid_phase)` - COVID phase fixed effects (0, 1, 2)
- `C(month):C(year)` - Month×year interaction fixed effects

**COVID Phase Definitions:**
- Phase 0: Before 2020-03-01
- Phase 1: 2020-03-01 to 2020-06-30 (March, April, May, June 2020)
- Phase 2: 2020-07-01 onwards (July 2020+)

**The Problem:**
COVID phases 1 and 2 are **perfectly collinear** with the month×year interactions:
- Phase 1 = March 2020 + April 2020 + May 2020 + June 2020
- Phase 2 = July 2020 + August 2020 + ... (all months from July 2020 onwards)

Since the model already includes `C(month):C(year)`, the COVID phase variables add no new information and create perfect multicollinearity.

### Evidence from Model Output

1. **Extreme COVID Phase Coefficients:**
   - `C(covid_phase)[T.1]`: 372,742,399.88 (SE: 8,481,674,006,281.55)
   - `C(covid_phase)[T.2]`: 4,040,975,457.22 (SE: missing)

2. **Extreme Month×Year Coefficients for 2020:**
   - Many 2020 month×year interactions have coefficients around -372,742,399 or -4,040,975,457
   - These are the exact negatives of the COVID phase coefficients, confirming perfect collinearity

3. **Missing Standard Errors:**
   - Only 1 out of 8 lag coefficients has a standard error (lag 7)
   - All other lags have missing SEs due to numerical instability

4. **Small IRF Coefficients:**
   - All coefficients are in the range -0.0006 to 0.0014
   - This is why the plot appears flat (the scale is very small)

## Solution

**Remove `C(covid_phase)` from the model specification.**

The `C(month):C(year)` interactions already capture all time trends, including:
- Seasonal patterns
- Year-over-year changes
- COVID period effects (through 2020-2021 month×year interactions)

### Why This Fix Works

1. **Eliminates Multicollinearity:** Removes the redundant COVID phase variables
2. **Preserves Time Controls:** Month×year interactions still control for all temporal patterns
3. **Improves Numerical Stability:** Model can properly estimate standard errors
4. **Maintains Model Validity:** No loss of control variables, just removes redundancy

## Implementation

Update `scripts/03_regression_analysis.py` to remove `C(covid_phase)` from all model formulas:

**Before:**
```python
formula = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday + C(covid_phase)"
)
```

**After:**
```python
formula = (
    "mh_share ~ "
    + " + ".join(lag_cols)
    + " + C(dow) + C(month):C(year) + is_holiday"
)
```

## Expected Outcomes After Fix

1. **All standard errors should be estimable** (no more missing SEs)
2. **COVID phase coefficients will disappear** (removed from model)
3. **Month×year coefficients should be reasonable** (no more extreme values)
4. **IRF plot should show proper confidence intervals** for all lags
5. **Coefficients may remain small** (this could be the true effect size, or indicate other issues)

## Next Steps After Fix

1. Re-run the full analysis pipeline
2. Check that all lag coefficients have standard errors
3. Verify IRF plot shows confidence intervals for all lags
4. If coefficients are still very small, investigate:
   - Whether awareness data has sufficient variation
   - Whether the effect is genuinely small
   - Whether there are other specification issues

