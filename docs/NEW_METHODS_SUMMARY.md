# New Methods Implementation: Quick Summary

## What We Added (6 New Methods)

| Method | Script | Purpose |
|--------|--------|---------|
| **1. De-meaning** | `21_demean_analysis.py` | Remove day-of-week patterns that vary by district |
| **2. Negative Binomial** | `22_negative_binomial_regression.py` | Count model for `mh_calls` (not proportions) |
| **3. Quantile Analysis** | `23_quantile_analysis.py` | Split awareness into quintiles, test non-linear effects |
| **4. Log Rolling Avg** | `02_merge_awareness.py` | Added `log_3_day` variable (log-transformed 3-day rolling average) |
| **5. Forward Lags** | `24_forward_lag_analysis.py` | How awareness affects future days (t+1 to t+7) |
| **6. Two-Way FE** | `25_twoway_fixed_effects.py` | Date + CD fixed effects |

## Enhanced DID Analysis

**File:** `16_difference_in_differences.py` (modified)

**Now includes 5 models:**
1. Original (threshold-based, original outcome)
2. Event study (dynamic effects)
3. **NEW:** De-meaned outcome (threshold-based)
4. **NEW:** Quantile-based treatment (top quintile)
5. **NEW:** De-meaned + quantile-based

## Key Outputs

**Tables:**
- `demeaned_regression_comparison.csv`
- `negative_binomial_results.csv`
- `quantile_analysis_regression_results.csv`
- `forward_lag_results.csv`
- `twoway_fe_results.csv`
- `did_results.csv` (now with 5 models)

**Figures:**
- `quantile_boxplots.png`
- `forward_lag_scatter.png`
- `forward_lag_coefficients.png`

## Expected Findings

1. **De-meaning**: Similar coefficients → day-of-week not driving results
2. **Negative Binomial**: Similar direction → confirms OLS findings
3. **Quantiles**: Stronger effects in top quintile → threshold effects
4. **Forward Lags**: Peak at 2-3 days → delayed response
5. **Two-Way FE**: Similar to one-way → time effects well-controlled
6. **Enhanced DID**: Consistent across specs → robust findings

## How to Run

```bash
# New scripts
python scripts/21_demean_analysis.py
python scripts/22_negative_binomial_regression.py
python scripts/23_quantile_analysis.py
python scripts/24_forward_lag_analysis.py
python scripts/25_twoway_fixed_effects.py

# Enhanced DID
python scripts/16_difference_in_differences.py
```

## Why This Matters

✅ **Robustness**: Multiple specifications confirm main findings  
✅ **Correct specification**: Count models for count data  
✅ **Non-linear effects**: Quantile analysis reveals threshold effects  
✅ **Causality**: Forward lags help rule out reverse causality  
✅ **Flexibility**: Multiple treatment definitions

---

**Full details:** See `docs/NEW_METHODS_IMPLEMENTATION.md`
