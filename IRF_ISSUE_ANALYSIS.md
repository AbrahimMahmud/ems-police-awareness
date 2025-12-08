# IRF Issue Analysis: Missing Standard Errors

## Problem Summary

From the diagnostic output:
- **Only 1 out of 8 lag coefficients has standard errors** (lag 7)
- **Coefficients are very small** (~0.0005 to 0.0014)
- **COVID phase coefficients are extreme** (billions), indicating numerical issues

## Root Cause Analysis

### Why Standard Errors Are Missing

When statsmodels calculates **clustered standard errors**, it needs:
1. Sufficient variation within each cluster (community district)
2. No perfect multicollinearity
3. Numerically stable covariance matrix

**The problem**: Most lag variables likely have:
- **Perfect or near-perfect multicollinearity** with the fixed effects or controls
- **Insufficient variation within clusters** to identify the effect
- **Rank deficiency** in the design matrix

### Why Only Lag 7 Has Standard Errors

This is particularly suspicious. Possible explanations:
1. **Lag 7 happens to have unique variation** that's not collinear with other variables
2. **Lag 7 might be the only lag with sufficient within-cluster variation**
3. **Numerical coincidence** - lag 7 might be the only one that passes the covariance matrix inversion

### Why Coefficients Are So Small

The coefficients (~0.0005-0.0014) suggest:
1. **The true effect might genuinely be very small** (which is plausible)
2. **But we can't tell if it's statistically significant** without standard errors
3. **The flat line in the plot is misleading** - we're only seeing coefficients, not confidence intervals

## Technical Details

### Model Specification
```
mh_share ~ awarez_lag0 + awarez_lag1 + ... + awarez_lag28
         + C(dow) + C(month):C(year) + is_holiday + C(covid_phase) + C(cd_str)
```

### The Issue
With 59 community districts and month×year interactions, we have:
- 59 CD fixed effects
- ~60+ month×year interactions (depending on date range)
- 7 day-of-week dummies
- 3 COVID phase dummies
- 8 lag variables

**Total: ~140+ parameters**

If the number of observations per cluster is small, or if lag variables are highly correlated with fixed effects, the covariance matrix becomes rank-deficient.

## Solutions

### Solution 1: Use Robust Standard Errors (Not Clustered)
**Pros**: Will give standard errors for all parameters
**Cons**: Doesn't account for within-CD correlation (less conservative)

### Solution 2: Reduce Model Complexity
- Remove month×year interactions, use simpler time trends
- Use fewer fixed effects
- Reduce number of lags

### Solution 3: Use Alternative Estimation
- Two-way fixed effects (CD + time)
- Use `plm` package (panel linear models)
- Use `fixest` package (fast fixed effects)

### Solution 4: Check for Multicollinearity
- Calculate variance inflation factors (VIF)
- Remove perfectly collinear variables
- Use principal components or regularization

### Solution 5: Use Different Lag Structure
- Instead of individual lags, use polynomial or Almon lag structure
- This reduces the number of parameters

## Recommended Fix

**Immediate action**: Try Solution 1 first (robust SEs) to see if we get standard errors. If that works, we can then:
1. Check if results are similar
2. If similar, use robust SEs (they're still valid, just less conservative)
3. If different, investigate multicollinearity issues

**Long-term**: Consider Solution 3 (alternative estimation methods) which are designed for this type of panel data.

## Impact on Results

**Current situation**:
- We have coefficient estimates but can't assess statistical significance
- The flat line in the plot is misleading (no confidence intervals)
- We can't draw valid conclusions about the effect

**What we need**:
- Standard errors for all lag coefficients
- Confidence intervals for the IRF plot
- Ability to test statistical significance

## Next Steps

1. **Run model with robust SEs** (not clustered) to see if we get standard errors
2. **Check for multicollinearity** using VIF or correlation matrices
3. **Consider alternative estimation** if issues persist
4. **Re-run IRF plot** once we have proper standard errors

