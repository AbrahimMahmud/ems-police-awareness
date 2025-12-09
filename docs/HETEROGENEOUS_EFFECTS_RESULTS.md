# Heterogeneous Effects Analysis Results

## Overview

This analysis examines how the effect of police shooting awareness on mental health EMS calls varies across NYC community districts based on their demographic characteristics.

## Key Findings

### 1. Interaction Terms Model

**Model Specification:**
- Outcome: `mh_share` (mental health calls / total calls)
- Main effects: Awareness lags (0, 1, 2, 3, 7, 14, 21, 28 days)
- Interactions: Awareness × Demographics (for lags 0, 1, 7, 14)
- Controls: Day of week, month×year, holidays, community district fixed effects
- Standard errors: Clustered at community district level

**Sample:** 84,547 observations across 59 community districts

**Key Interaction Coefficients (14-day lag):**
- **% Hispanic × Awareness (lag 14)**: -0.000192 (SE: 0.000092, **p = 0.037**) ✓ Significant
- **% Black × Awareness (lag 14)**: -0.000187 (SE: 0.000097, p = 0.053) * Marginally significant
- **% White × Awareness (lag 14)**: -0.000183 (SE: 0.000093, p = 0.050) * Marginally significant
- **% Asian × Awareness (lag 14)**: -0.000202 (SE: 0.000106, p = 0.056) * Marginally significant

**Interpretation:**
- Negative interaction coefficients suggest that districts with higher percentages of these groups show **smaller** positive effects (or larger negative effects) from awareness
- The effect is statistically significant for % Hispanic at the 14-day lag

### 2. Stratified Analysis by Demographic Quartiles

**Analysis:** Separate models for each quartile of each demographic variable, focusing on the 7-day lag coefficient (key finding from main analysis).

#### By % Black Quartiles:
- **Q1 (Lowest % Black)**: 0.00250 (SE: 0.00068) ✓ **Strongest positive effect**
- **Q2**: 0.00244 (SE: 0.00086)
- **Q3**: 0.00108 (SE: 0.00072)
- **Q4 (Highest % Black)**: -0.00035 (SE: 0.00049) ✗ **Negative effect**

**Pattern:** Effect decreases (and becomes negative) as % Black increases

#### By % Hispanic Quartiles:
- **Q1 (Lowest % Hispanic)**: 0.00251 (SE: 0.00088) ✓ **Strongest positive effect**
- **Q2**: 0.00162 (SE: 0.00085)
- **Q3**: 0.00089 (SE: 0.00070)
- **Q4 (Highest % Hispanic)**: 0.00074 (SE: 0.00044)

**Pattern:** Effect decreases as % Hispanic increases, but remains positive

#### By % White Quartiles:
- **Q1 (Lowest % White)**: 0.00065 (SE: 0.00037)
- **Q2**: 0.00044 (SE: 0.00076)
- **Q3**: 0.00112 (SE: 0.00085)
- **Q4 (Highest % White)**: 0.00374 (SE: 0.00066) ✓ **Strongest positive effect**

**Pattern:** Effect increases as % White increases

#### By % Asian Quartiles:
- **Q1 (Lowest % Asian)**: 0.00040 (SE: 0.00037)
- **Q2**: 0.00139 (SE: 0.00069)
- **Q3**: 0.00133 (SE: 0.00098)
- **Q4 (Highest % Asian)**: 0.00276 (SE: 0.00079) ✓ **Strongest positive effect**

**Pattern:** Effect increases as % Asian increases

## Key Insights

### 1. **Racial/Ethnic Heterogeneity is Significant**
- The effect of police shooting awareness on mental health calls **varies systematically** by district demographics
- Districts with **lower % Black and % Hispanic** show stronger positive effects
- Districts with **higher % White and % Asian** show stronger positive effects

### 2. **Potential Explanations**
- **Differential exposure**: Districts with higher % Black/Hispanic may have different baseline awareness or different responses to awareness
- **Resource availability**: Districts with different demographics may have different access to mental health resources
- **Social networks**: Information diffusion may vary by community characteristics
- **Baseline mental health**: Different districts may have different baseline mental health needs

### 3. **Policy Implications**
- Effects are **not uniform** across all districts
- Districts with higher % Black populations show **negative or null effects** at the 7-day lag
- This suggests the mechanism may differ by community characteristics
- Targeted interventions may be needed based on district demographics

## Statistical Significance

### Significant Findings (p < 0.05):
- **% Hispanic × Awareness (lag 14)**: p = 0.037

### Marginally Significant (p < 0.10):
- **% Black × Awareness (lag 14)**: p = 0.053
- **% White × Awareness (lag 14)**: p = 0.050
- **% Asian × Awareness (lag 14)**: p = 0.056

## Files Generated

1. **Interaction Effects Table**: `outputs/tables/heterogeneous_effects_interactions.csv`
   - All interaction coefficients with standard errors and p-values

2. **Stratified Analysis Table**: `outputs/tables/heterogeneous_effects_stratified.csv`
   - 7-day lag coefficients by demographic quartile

3. **Visualizations**: `outputs/figures/heterogeneous_effects_*.png`
   - Bar charts showing effects by quartile for each demographic variable

## Next Steps

1. **Interpret the negative effect in high % Black districts**
   - Is this a suppression effect?
   - Different mechanism?
   - Data quality issue?

2. **Additional analyses**:
   - Income interactions (if income data becomes available)
   - Education interactions
   - Combined demographic profiles

3. **Robustness checks**:
   - Different lag specifications
   - Alternative demographic categorizations
   - Sensitivity to model specification

## Notes

- All models include community district fixed effects
- Standard errors clustered at community district level
- Sample restricted to days with ≥5 total calls
- Demographics from 2010 Census (may not reflect current composition)

