"""Build the calendar-date lag/lead table for the CAI treatment variables.

This is the file every outcome model reads. It replaces the Twitter-derived
awareness_lags.parquet retired at Gate C (GATE_C_MEMO.md §6): same column
contract, different — and publicly reconstructible — source.

Column contract (unchanged, so downstream scripts need no edits):
    {variant}_lag{k}   k in LAGS   (0..28)
    {variant}_lead{j}  j in LEADS  (1..14)
    {PRIMARY_AWARENESS}_w{lo}{hi}  rolling-window means over ROLLING_WINDOWS

Lags are built on the DATE table and merged to the panel by calendar date,
never by row-shift within a district (REWORK_PLAN I6).

Input:  data/processed/cai_daily.parquet   (from 12_build_cai.py)
Output: data/processed/awareness_lags.parquet
        outputs/tables/qc_cai_lags.csv

Run order note: 12_build_cai.py must run BEFORE this script. The numbering is
historical — 02b marks where this sits in the modelling pipeline, not the
order in which the inputs are fetched.
"""

import numpy as np
import pandas as pd

from config import (
    AWARENESS_VARIANTS,
    DATA_PROCESSED,
    LAGS,
    LEADS,
    OUTPUTS_TABLES,
    PANEL_BUFFER_END,
    PANEL_BUFFER_START,
    PRIMARY_AWARENESS,
    ROLLING_WINDOWS,
)

DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

cai_path = DATA_PROCESSED / "cai_daily.parquet"
if not cai_path.exists():
    raise SystemExit(
        f"{cai_path} not found. Run 12_build_cai.py first — it builds the "
        "composite index this script lags."
    )

cai = pd.read_parquet(cai_path)
cai["date"] = pd.to_datetime(cai["date"])

missing = [v for v in AWARENESS_VARIANTS if v not in cai.columns]
if missing:
    raise SystemExit(
        f"cai_daily.parquet is missing {missing}. Rebuild it with the current "
        "12_build_cai.py, which writes the race-matched sub-indices."
    )

# Buffer the date grid so lag 28 and lead 14 are defined across the whole
# analysis window. Days outside the index's own coverage stay NaN and the
# models drop them explicitly.
grid = pd.DataFrame({"date": pd.date_range(PANEL_BUFFER_START, PANEL_BUFFER_END, freq="D")})
grid = grid.merge(cai[["date", *AWARENESS_VARIANTS]], on="date", how="left").sort_values("date")
grid = grid.reset_index(drop=True)

cols = {}
for var in AWARENESS_VARIANTS:
    for k in LAGS:
        cols[f"{var}_lag{k}"] = grid[var].shift(k)
    for j in LEADS:
        cols[f"{var}_lead{j}"] = grid[var].shift(-j)
lag_tbl = pd.concat([grid[["date"]], pd.DataFrame(cols)], axis=1)

# Rolling windows for the primary variant, and for the race-matched sub-index
# so heterogeneity models can use the same window definition.
win_cols = {}
for var in (PRIMARY_AWARENESS, "cai_d_black"):
    if var not in AWARENESS_VARIANTS:
        continue
    for lo, hi in ROLLING_WINDOWS:
        src = [f"{var}_lag{k}" for k in range(lo, hi + 1)]
        win_cols[f"{var}_w{lo}{hi}"] = lag_tbl[src].mean(axis=1)
lag_tbl = pd.concat([lag_tbl, pd.DataFrame(win_cols)], axis=1)

lag_tbl.to_parquet(DATA_PROCESSED / "awareness_lags.parquet", index=False)

# ---------------------------------------------------------------------------
# QC: coverage per variant over the buffered grid, and the correlation between
# the primary index and its race-matched sub-index (they are not independent —
# the sub-index is a component of the composite).
# ---------------------------------------------------------------------------
qc = [
    {"metric": "grid_rows", "value": len(lag_tbl)},
    {"metric": "grid_first_date", "value": str(lag_tbl["date"].min().date())},
    {"metric": "grid_last_date", "value": str(lag_tbl["date"].max().date())},
    {"metric": "n_columns", "value": lag_tbl.shape[1]},
]
for var in AWARENESS_VARIANTS:
    n = int(grid[var].notna().sum())
    qc.append({"metric": f"days_observed_{var}", "value": n})
    qc.append({"metric": f"coverage_{var}", "value": round(n / len(grid), 4)})
if {"cai_d", "cai_d_black"} <= set(grid.columns):
    qc.append({"metric": "corr_cai_d_vs_cai_d_black",
               "value": round(float(grid["cai_d"].corr(grid["cai_d_black"])), 3)})

pd.DataFrame(qc).to_csv(OUTPUTS_TABLES / "qc_cai_lags.csv", index=False)

print(f"awareness_lags.parquet: {len(lag_tbl):,} rows x {lag_tbl.shape[1]} cols "
      f"({lag_tbl['date'].min().date()} -> {lag_tbl['date'].max().date()})")
print(f"Primary treatment: {PRIMARY_AWARENESS}")
for var in AWARENESS_VARIANTS:
    n = int(grid[var].notna().sum())
    print(f"  {var:16s} {n:5,} days observed ({n / len(grid):.1%} of grid)")
if grid["cai_d_black"].notna().sum() < grid["cai_d"].notna().sum():
    print("  NOTE: the race-matched sub-index covers fewer days than CAI-D. "
          "H3 is limited to the window where it is observed.")
