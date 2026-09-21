---
tags: [pipeline]
updated: 2026-09-21
---
# Pipeline

`scripts/run_all.py` runs the stages below in order (`--kind fetch|build|check|model`; fetch stages need network and are excluded from cold runs because upstream mutates). Each stage declares what it writes; a stage that exits 0 without refreshing its outputs fails (X18). The manifest is `outputs/run_manifest.json`.

| kind | script | args | writes |
|---|---|---|---|
| fetch | `09_fetch_public_data.py` |  | acs_2019_cd_demographics.csv |
| fetch | `10_build_victim_registry.py` |  | victim_registry.csv |
| build | `10d_parse_cd_demographics.py` |  | cd_demographics_clean.parquet |
| fetch | `24_build_wiki_basket.py` |  | wiki_basket.csv |
| fetch | `26_resolve_basket_scope.py` |  | basket_scope.csv |
| fetch | `27_finalise_basket.py` |  | basket_decisions.csv |
| fetch | `32_validate_basket_construct.py` | --apply | basket_construct_review.csv, basket_strict.csv, basket_broad.csv, wikipedia_article_resolution.csv |
| fetch | `29_resolve_article_titles.py` |  | article_title_map.csv, rename_recovery.csv |
| fetch | `11_fetch_awareness_components.py` |  | cai_components_daily.csv, wiki_ext_basket_used.csv |
| fetch | `11b_fetch_trends.py` |  | cai_trends_daily.csv |
| fetch | `28_build_nyc_attention.py` |  | wiki_nyc_daily.csv |
| fetch | `00b_download_ems_extract.py` |  | ems_cd_day_calltype.parquet, ems_cd_day_calltype_excluded.parquet, ems_citywide_day_trends.parquet |
| fetch | `16_bheard_exposure.py` |  | precinct_cd_crosswalk.csv, bheard_cd_exposure.csv |
| build | `01_build_panel.py` |  | panel_cd_day.parquet |
| build | `35_coverage_breaks.py` |  | ems_call_code_span.csv, ems_missing_district_rate_by_year.csv, ems_coverage_breaks.csv |
| build | `12_build_cai.py` |  | cai_daily.parquet |
| build | `02b_build_cai_lags.py` |  | awareness_lags.parquet |
| build | `13_extension_episodes.py` |  | confirmation_episodes_rebuilt.csv |
| build | `12_build_cai.py` | --arm broad | cai_daily_broad.parquet |
| build | `12_build_cai.py` | --arm spliced | cai_daily_spliced.parquet |
| build | `13_extension_episodes.py` | --arm broad | confirmation_episodes_rebuilt_broad.csv |
| build | `13_extension_episodes.py` | --arm spliced | confirmation_episodes_rebuilt_spliced.csv |
| check | `22_pipeline_check.py` | --stage panel --stage treatment --stage episodes --stage bheard | pipeline_check.csv |
| check | `20_data_audit.py` |  | data_audit.csv |
| model | `17_stacked_event_study.py` |  | event_study_results.csv, event_study_path.csv |
| model | `03_main_model.py` |  | irf_main.csv, joint_tests.csv |
| model | `04_robustness.py` |  | robustness_counts_permutation.csv |
| model | `05_placebo_and_calls.py` |  | decomposition_windows.csv |
| model | `06_heterogeneity.py` |  | heterogeneity_results.csv |
| model | `07_did_exposure.py` |  | did_exposure_results.csv |
| model | `08_figures.py` |  | fig1_raw_series.png |
| model | `33_antipolice_sensitivity.py` |  | antipolice_sensitivity.csv |
| model | `25_zscore_simulation.py` |  | zscore_simulation.csv, zscore_simulation_params.csv |
| check | `31_verify_sources.py` | --offline | source_verification_log.csv, SOURCE_REGISTER.md |
| check | `23_regression_suite.py` |  | regression_suite.csv |
| check | `22_pipeline_check.py` | --stage outputs | pipeline_check.csv |

**Not stages** (hours of resumable compute, driven by `ops/` runners): `18_null_calibration.py` (certificates), `19_power.py` (MDEs), `30_confirmatory_run.py` (the seal, once), `34_confirmatory_reading.py` (its reading).

**The gate**: `23_regression_suite.py` (90 checks, baseline in `docs/regression_baseline.csv`; see [[Gate and checks]]); `31_verify_sources.py --offline` (provenance and every claim); `22_pipeline_check.py`.

**Runners** (`ops/README.md`): `rebuild.sh`, `calib1000.sh`, `coldrun.sh`, `phase_i.sh`; generators `paper_table1.py`, `phase_i_tables.py`.

Related: [[Data inventory]] · [[Gate and checks]] · [[Phase I]] · [[Status]]
