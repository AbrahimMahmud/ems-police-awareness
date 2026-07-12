"""Build the CD x day analysis panel from the local EMS extracts (REWORK_PLAN I7, I10, I11).

Input:  data/processed/ems_cd_day_calltype.parquet  (from 00_local_ems_extract.py, run locally)
Output: data/processed/panel_cd_day.parquet         balanced CD x day panel, 59 valid CDs,
                                                    outcome-group counts and shares
        outputs/tables/qc_panel.csv                 QC metrics
        outputs/tables/qc_dropped_districts.csv     call volume in excluded pseudo-districts
        outputs/tables/sample_definition.csv        single source of truth for every N (I17)

Panel rules:
  - Only the 59 real community districts (config.VALID_CDS); park/airport/joint-interest
    codes are dropped and their volumes logged.
  - Balanced grid: every valid CD x every date in the buffered range; missing cells are
    explicit zeros (a CD-day with no rows in the extract means zero dispatched calls
    after the documented exclusions).
  - Shares are NA where total_calls < MIN_TOTAL_CALLS_FOR_SHARE; count outcomes keep zeros.
"""

import sys

import numpy as np
import pandas as pd

from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    CALL_TYPE_GROUPS,
    DATA_PROCESSED,
    EMS_EXTRACT_CD_DAY,
    MH_BROAD_GROUPS,
    MH_NARROW_GROUPS,
    MIN_TOTAL_CALLS_FOR_SHARE,
    OUTPUTS_TABLES,
    PANEL_BUFFER_END,
    PANEL_BUFFER_START,
    VALID_CDS,
)

OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

extract_path = sys.argv[1] if len(sys.argv) > 1 else EMS_EXTRACT_CD_DAY
ext = pd.read_parquet(extract_path)
ext["incident_date"] = pd.to_datetime(ext["incident_date"])
ext = ext[ext["incident_date"].between(PANEL_BUFFER_START, PANEL_BUFFER_END)]

# --- classify call types into outcome groups ---
code_to_group = {}
for group, codes in CALL_TYPE_GROUPS.items():
    for c in codes:
        assert c not in code_to_group, f"call code {c} assigned to two groups"
        code_to_group[c] = group
ext["group"] = ext["final_call_type"].map(code_to_group).fillna("other")

# --- district validity (I7) ---
ext["valid_cd"] = ext["communitydistrict"].isin(VALID_CDS)
dropped = (
    ext[~ext["valid_cd"]]
    .groupby("communitydistrict")["n_calls"].sum()
    .sort_values(ascending=False)
    .rename("total_calls_in_period")
    .reset_index()
)
dropped.to_csv(OUTPUTS_TABLES / "qc_dropped_districts.csv", index=False)
share_dropped = ext.loc[~ext["valid_cd"], "n_calls"].sum() / ext["n_calls"].sum()

ems = ext[ext["valid_cd"]]

# --- pivot to CD x day with group counts ---
wide = (
    ems.pivot_table(index=["incident_date", "communitydistrict"],
                    columns="group", values="n_calls", aggfunc="sum", fill_value=0)
    .reset_index()
)
for g in list(CALL_TYPE_GROUPS) + ["other"]:
    if g not in wide.columns:
        wide[g] = 0

# --- balanced grid with explicit zeros ---
dates = pd.date_range(PANEL_BUFFER_START, PANEL_BUFFER_END, freq="D")
grid = pd.MultiIndex.from_product([dates, VALID_CDS],
                                  names=["incident_date", "communitydistrict"]).to_frame(index=False)
panel = grid.merge(wide, on=["incident_date", "communitydistrict"], how="left")
group_cols = list(CALL_TYPE_GROUPS) + ["other"]
panel[group_cols] = panel[group_cols].fillna(0).astype(int)

panel["total_calls"] = panel[group_cols].sum(axis=1)
panel["mh_narrow"] = panel[list(MH_NARROW_GROUPS)].sum(axis=1)
panel["mh_broad"] = panel[list(MH_BROAD_GROUPS)].sum(axis=1)

# --- shares (NA below the min-calls threshold) ---
ok = panel["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE
for out in ["mh_narrow", "mh_broad", "edp", "altmen", "suicide_jump",
            "od_poison_drug", "cardiac", "injury", "asthma"]:
    panel[f"{out}_share"] = np.where(ok, panel[out] / panel["total_calls"], np.nan)

# --- calendar controls ---
panel["dow"] = panel["incident_date"].dt.dayofweek
panel["month"] = panel["incident_date"].dt.month
panel["year"] = panel["incident_date"].dt.year

out_path = DATA_PROCESSED / "panel_cd_day.parquet"
panel.to_parquet(out_path, index=False)

# --- QC and the single source of truth for sample sizes (I17) ---
in_window = panel[panel["incident_date"].between(ANALYSIS_START, ANALYSIS_END)]
analysis_sample = in_window[in_window["total_calls"] >= MIN_TOTAL_CALLS_FOR_SHARE]

qc = pd.DataFrame([
    {"metric": "extract_rows", "value": len(ext)},
    {"metric": "pct_calls_in_dropped_pseudo_districts", "value": round(100 * share_dropped, 3)},
    {"metric": "n_dropped_district_codes", "value": len(dropped)},
    {"metric": "panel_rows_balanced", "value": len(panel)},
    {"metric": "n_districts", "value": panel["communitydistrict"].nunique()},
    {"metric": "date_min", "value": str(panel["incident_date"].min().date())},
    {"metric": "date_max", "value": str(panel["incident_date"].max().date())},
    {"metric": "zero_call_cd_days_pct", "value": round(100 * (panel["total_calls"] == 0).mean(), 2)},
    {"metric": "mean_total_calls_per_cd_day", "value": round(in_window["total_calls"].mean(), 2)},
    {"metric": "mean_mh_narrow_share", "value": round(analysis_sample["mh_narrow_share"].mean(), 4)},
    {"metric": "mean_mh_broad_share", "value": round(analysis_sample["mh_broad_share"].mean(), 4)},
])
qc.to_csv(OUTPUTS_TABLES / "qc_panel.csv", index=False)

sample_def = pd.DataFrame([
    {"quantity": "analysis_window", "value": f"{ANALYSIS_START}..{ANALYSIS_END}"},
    {"quantity": "n_districts", "value": 59},
    {"quantity": "cd_days_in_window", "value": len(in_window)},
    {"quantity": f"cd_days_with_ge{MIN_TOTAL_CALLS_FOR_SHARE}_calls", "value": len(analysis_sample)},
    {"quantity": "total_calls_in_window", "value": int(in_window["total_calls"].sum())},
    {"quantity": "mh_narrow_calls_in_window", "value": int(in_window["mh_narrow"].sum())},
    {"quantity": "mh_broad_calls_in_window", "value": int(in_window["mh_broad"].sum())},
])
sample_def.to_csv(OUTPUTS_TABLES / "sample_definition.csv", index=False)

print(f"panel_cd_day.parquet: {len(panel):,} rows "
      f"({panel['incident_date'].min().date()} -> {panel['incident_date'].max().date()}, "
      f"{panel['communitydistrict'].nunique()} districts)")
print(f"Dropped pseudo-districts: {len(dropped)} codes, {100*share_dropped:.2f}% of call volume")
print(f"Analysis sample (>= {MIN_TOTAL_CALLS_FOR_SHARE} calls, {ANALYSIS_START[:4]}-{ANALYSIS_END[:4]}): "
      f"{len(analysis_sample):,} CD-days")
print(qc.to_string(index=False))
