# What Exactly is the "Day of High Awareness Event"?

## Direct Answer

**The "high awareness event day" is the actual calendar date when Twitter activity about police killings (`awareness_z`) exceeds a specified threshold (e.g., 1.5 standard deviations above the mean).**

## Important Distinction

The high awareness event day is **NOT necessarily the date of the actual police killing**. It is the date when **public awareness/Twitter activity peaked**.

### Example Timeline

```
Day 1 (May 25, 2020): Police killing occurs
  → awareness_z might be low (news hasn't spread yet)

Day 2 (May 26, 2020): News starts spreading
  → awareness_z increases

Day 3 (May 27, 2020): Major news coverage begins
  → awareness_z = 6.97 (above 2.0 SD threshold)
  → **THIS is the high awareness event day** (even though killing was 2 days earlier)

Day 4 (May 28, 2020): Protests begin, social media explodes
  → awareness_z = 9.86 (above threshold)
  → **THIS is also a high awareness event day**

Day 5 (May 29, 2020): Peak of public attention
  → awareness_z = 20.43 (extreme awareness)
  → **THIS is the highest awareness event day**
```

## How We Identify High Awareness Event Days

### Step-by-Step Process

1. **Calculate daily awareness**: For each calendar date, we have `awareness_z` (z-scored Twitter activity)

2. **Apply threshold**: A day is a "high awareness event day" if:
   ```
   awareness_z > threshold
   ```
   Where threshold is typically 1.0, 1.5, or 2.0 standard deviations

3. **Use that date as event day**: The calendar date where `awareness_z > threshold` becomes the "event_date" or "treatment day"

4. **Create windows around it**: For analysis, we look at:
   - 14 days before the event day
   - The event day itself (day 0)
   - 14 days after the event day

### Code Implementation

```python
# From scripts/16_difference_in_differences.py

# Step 1: Identify high awareness days
threshold = 1.5  # Standard deviations
df_analysis["treated"] = (df_analysis["awareness_z"] > threshold).astype(int)

# Step 2: Get the actual dates
treated_dates = df_analysis[df_analysis["treated"] == 1]["incident_date"].drop_duplicates()

# Step 3: For each treated date, create event window
for event_date in treated_dates:
    window_start = event_date - pd.Timedelta(days=14)
    window_end = event_date + pd.Timedelta(days=14)
    
    # Mark all days in window with their distance from event_date
    mask = (df_analysis["incident_date"] >= window_start) & 
           (df_analysis["incident_date"] <= window_end)
    df_analysis.loc[mask, "event_time"] = (
        df_analysis.loc[mask, "incident_date"] - event_date
    ).dt.days
```

## Real Examples from the Data

### Example 1: May 29, 2020
- **Event Date**: May 29, 2020
- **Awareness z-score**: 20.43 (extremely high)
- **What happened**: This was the peak of public awareness about George Floyd's killing
- **Note**: The actual killing was May 25, 2020 (4 days earlier)
- **Why this day**: This is when Twitter activity was highest, likely due to:
  - Sustained news coverage
  - Protests and public events
  - Social media amplification

### Example 2: May 28, 2020
- **Event Date**: May 28, 2020
- **Awareness z-score**: 9.86
- **What happened**: Early peak of awareness, protests beginning
- **Note**: Also related to George Floyd, but a different peak day

### Example 3: June 2, 2020
- **Event Date**: June 2, 2020
- **Awareness z-score**: 9.16
- **What happened**: Continued high awareness, possibly related to:
  - Ongoing protests
  - Policy responses
  - Additional incidents

## Why This Approach?

### Advantages

1. **Captures actual public awareness**: Uses the day when people were actually paying attention, not just when an incident occurred

2. **Accounts for information diffusion**: Recognizes that awareness takes time to build and spread

3. **Multiple event days per incident**: A single killing can generate multiple high awareness days as:
   - News breaks (Day 1)
   - Protests occur (Day 3)
   - Policy responses (Day 7)
   - Each peak becomes its own "event day"

4. **Policy-relevant**: The day of high awareness is when mental health resources should be mobilized, which may be different from the day of the incident

### Limitations

1. **Not tied to specific incidents**: We can't always say "this event day corresponds to that specific killing"

2. **Multiple incidents may cluster**: Several killings might contribute to awareness on the same day

3. **Media-driven**: High awareness days reflect media coverage patterns, which may not perfectly align with actual incidents

## Comparison: Event Day vs. Killing Date

### Approach 1: High Awareness Days (What We Use)
- **Definition**: Days when `awareness_z > threshold`
- **Advantage**: Captures when public attention was actually high
- **Use**: Main analysis, DID, threshold analysis

### Approach 2: Actual Killing Dates (Alternative)
- **Definition**: Days when police killings actually occurred
- **Advantage**: Directly tied to specific incidents
- **Use**: Some trend charts (script 15 has a version using very high threshold to approximate killing dates)

### Why We Prefer High Awareness Days

1. **Causal mechanism**: Mental health effects are likely driven by awareness, not just the incident itself
2. **Policy relevance**: Interventions should target high awareness periods
3. **Measurement**: We can measure awareness directly, but killing dates may be incomplete or delayed in reporting

## Summary

**The "high awareness event day" is the calendar date when Twitter activity about police killings exceeded a threshold (e.g., 1.5 SD above mean). This is the day when public awareness peaked, which may be the same day as a killing, or days later when news spreads and public attention builds.**

---

*For technical details, see:*
- `scripts/16_difference_in_differences.py`: How event days are identified for DID
- `scripts/15_trend_charts.py`: How event days are used in trend analysis
- `scripts/14_analysis_by_awareness_threshold.py`: How thresholds are applied

