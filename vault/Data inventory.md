---
tags: [data]
updated: 2026-09-21
---
# Data inventory

*Paths, schemas and row counts only (parquet metadata and CSV line counts; no values). Generated 2026-09-20 by a metadata scan; regenerate the same way.*

## data/processed (gitignored, rebuilt by `run_all.py`; the raw page cache `ems_pages/` and the Wikimedia caches are kept across cold runs)

| file | rows | columns |
|---|---|---|
| `awareness_lags.parquet` | 3,684 | date, cai_d_lag0, cai_d_lag1, cai_d_lag2, cai_d_lag3, cai_d_lag4, cai_d_lag5, cai_d_lag6, cai_d_lag7, cai_d_lag8, cai_d_lag9, cai_d_lag10, cai_d_lag11, cai_d_lag12, cai_d_lag13, cai_d_lag14, cai_d_lag15, cai_d_lag16, cai_d_lag17, cai_d_lag18, cai_d_lag19, cai_d_lag20, cai_d_lag21, cai_d_lag22, cai_d_lag23, cai_d_lag24, cai_d_lag25, cai_d_lag26, cai_d_lag27, cai_d_lag28, cai_d_lead1, cai_d_lead2, cai_d_lead3, cai_d_lead4, cai_d_lead5, cai_d_lead6, cai_d_lead7, cai_d_lead8, cai_d_lead9, cai_d_lead10, cai_d_lead11, cai_d_lead12, cai_d_lead13, cai_d_lead14, cai_d_black_lag0, cai_d_black_lag1, cai_d_black_lag2, cai_d_black_lag3, cai_d_black_lag4, cai_d_black_lag5, cai_d_black_lag6, cai_d_black_lag7, cai_d_black_lag8, cai_d_black_lag9, cai_d_black_lag10, cai_d_black_lag11, cai_d_black_lag12, cai_d_black_lag13, cai_d_black_lag14, cai_d_black_lag15, cai_d_black_lag16, cai_d_black_lag17, cai_d_black_lag18, cai_d_black_lag19, cai_d_black_lag20, cai_d_black_lag21, cai_d_black_lag22, cai_d_black_lag23, cai_d_black_lag24, cai_d_black_lag25, cai_d_black_lag26, cai_d_black_lag27, cai_d_black_lag28, cai_d_black_lead1, cai_d_black_lead2, cai_d_black_lead3, cai_d_black_lead4, cai_d_black_lead5, cai_d_black_lead6, cai_d_black_lead7, cai_d_black_lead8, cai_d_black_lead9, cai_d_black_lead10, cai_d_black_lead11, cai_d_black_lead12, cai_d_black_lead13, cai_d_black_lead14, cai_d_nonblack_lag0, cai_d_nonblack_lag1, cai_d_nonblack_lag2, cai_d_nonblack_lag3, cai_d_nonblack_lag4, cai_d_nonblack_lag5, cai_d_nonblack_lag6, cai_d_nonblack_lag7, cai_d_nonblack_lag8, cai_d_nonblack_lag9, cai_d_nonblack_lag10, cai_d_nonblack_lag11, cai_d_nonblack_lag12, cai_d_nonblack_lag13, cai_d_nonblack_lag14, cai_d_nonblack_lag15, cai_d_nonblack_lag16, cai_d_nonblack_lag17, cai_d_nonblack_lag18, cai_d_nonblack_lag19, cai_d_nonblack_lag20, cai_d_nonblack_lag21, cai_d_nonblack_lag22, cai_d_nonblack_lag23, cai_d_nonblack_lag24, cai_d_nonblack_lag25, cai_d_nonblack_lag26, cai_d_nonblack_lag27, cai_d_nonblack_lag28, cai_d_nonblack_lead1, cai_d_nonblack_lead2, cai_d_nonblack_lead3, cai_d_nonblack_lead4, cai_d_nonblack_lead5, cai_d_nonblack_lead6, cai_d_nonblack_lead7, cai_d_nonblack_lead8, cai_d_nonblack_lead9, cai_d_nonblack_lead10, cai_d_nonblack_lead11, cai_d_nonblack_lead12, cai_d_nonblack_lead13, cai_d_nonblack_lead14, cai_s_lag0, cai_s_lag1, cai_s_lag2, cai_s_lag3, cai_s_lag4, cai_s_lag5, cai_s_lag6, cai_s_lag7, cai_s_lag8, cai_s_lag9, cai_s_lag10, cai_s_lag11, cai_s_lag12, cai_s_lag13, cai_s_lag14, cai_s_lag15, cai_s_lag16, cai_s_lag17, cai_s_lag18, cai_s_lag19, cai_s_lag20, cai_s_lag21, cai_s_lag22, cai_s_lag23, cai_s_lag24, cai_s_lag25, cai_s_lag26, cai_s_lag27, cai_s_lag28, cai_s_lead1, cai_s_lead2, cai_s_lead3, cai_s_lead4, cai_s_lead5, cai_s_lead6, cai_s_lead7, cai_s_lead8, cai_s_lead9, cai_s_lead10, cai_s_lead11, cai_s_lead12, cai_s_lead13, cai_s_lead14, cai_d_w02, cai_d_w35, cai_d_w68, cai_d_w911, cai_d_w1214, cai_d_black_w02, cai_d_black_w35, cai_d_black_w68, cai_d_black_w911, cai_d_black_w1214 |
| `cai_daily.parquet` | 3,653 | date, gdelt_news, gdelt_tv, trends_nyc, trends_us, wiki_black, wiki_ext, wiki_nonblack, n_d_components, n_s_components, cai_d, cai_s, cai_d_black, cai_d_nonblack |
| `cai_daily_broad.parquet` | 3,653 | date, gdelt_news, gdelt_tv, trends_nyc, trends_us, wiki_black, wiki_ext, wiki_nonblack, n_d_components, n_s_components, cai_d, cai_s, cai_d_black, cai_d_nonblack |
| `cai_daily_spliced.parquet` | 3,653 | date, gdelt_news, gdelt_tv, trends_nyc, trends_us, wiki_black, wiki_ext, wiki_nonblack, n_d_components, n_s_components, cai_d, cai_s, cai_d_black, cai_d_nonblack |
| `cd_demographics_clean.parquet` | 59 | communitydistrict, pct_white, pct_black, pct_asian, pct_hispanic, total_households, pct_renter_occupied, pct_owner_occupied, cd_code, cd_number |
| `ems_cd_day_calltype.parquet` | 4,876,509 | incident_date, communitydistrict, final_call_type, n_calls |
| `ems_cd_day_calltype_excluded.parquet` | 443,719 | incident_date, communitydistrict, final_call_type, disp, n_calls |
| `ems_citywide_day_trends.parquet` | 39,037 | incident_date, call_group, n_calls |
| `panel_cd_day.parquet` | 217,356 | incident_date, communitydistrict, altmen, asthma, cardiac, edp, injury, od_poison_drug, other, suicide_jump, total_calls, mh_narrow, mh_broad, mh_narrow_share, mh_broad_share, edp_share, altmen_share, suicide_jump_share, od_poison_drug_share, cardiac_share, injury_share, asthma_share, dow, month, year |
| `ems_pages/` | 60 files | cache directory |
| `wiki_pageviews_cache/` | 956 files | cache directory |
| `wiki_category_cache/` | 19 files | cache directory |
| `wikimedia_state/` | 2 files | cache directory |

## data/reference (tracked; treatment side, registers, the sealed inputs)

| file | rows (excl. header) | columns |
|---|---|---|
| `acs_2019_cd_demographics.csv` | 59 | communitydistrict, total_pop_acs, pct_white_acs, pct_black_acs, pct_hispanic_acs, pct_asian_acs |
| `article_title_map.csv` | 530 | article, title, days, views, first, last, created |
| `basket_broad.csv` | 118 | name, article |
| `basket_construct_review.csv` | 174 | article, person, scope_decision, in_registry, construct, reason, evidence_category, n_categories, wikidata_country, us_evidence, non_us_evidence, article_first_ |
| `basket_decisions.csv` | 174 | article, person, death_date, date_source, wd_precision, country, in_registry, decision, reason |
| `basket_scope.csv` | 174 | article, item, label, date, date_precision, country, manner |
| `basket_strict.csv` | 109 | name, article |
| `bheard_cd_exposure.csv` | 74 | bound, communitydistrict, effective_from, exposure |
| `bheard_precinct_adoption.csv` | 31 | precinct, borough, phase, adoption_earliest, adoption_latest, confidence, evidence |
| `cai_components_daily.csv` | 9,232 | date, component, value |
| `cai_components_daily_broad.csv` | 3,472 | date, component, value |
| `cai_components_daily_spliced.csv` | 3,472 | date, component, value |
| `cai_trends_daily.csv` | 7,306 | date, component, value |
| `cai_trends_stitch_diagnostics.csv` | 58 | component, boundary, scale, n_positive, span_days, r2 |
| `confirmation_episodes.csv` | 70 | episode, start, end, n_high_days, peak_date, peak_cai_d, candidate_events, period |
| `confirmation_episodes_rebuilt.csv` | 74 | episode, start, end, n_high_days, peak_date, peak_cai_d, candidate_events, drivers, top_driver_share, period |
| `confirmation_episodes_rebuilt_broad.csv` | 75 | episode, start, end, n_high_days, peak_date, peak_cai_d, candidate_events, drivers, top_driver_share, period |
| `confirmation_episodes_rebuilt_spliced.csv` | 74 | episode, start, end, n_high_days, peak_date, peak_cai_d, candidate_events, drivers, top_driver_share, period |
| `data_sources.csv` | 36 | source_id, description, url, accessed_utc, sha256, payload_sha256, output_file, generator, generator_code_sha256 |
| `data_sources_history.csv` | 118 | source_id, description, url, accessed_utc, sha256, payload_sha256, output_file, generator, generator_code_sha256 |
| `ems_call_code_span.csv` | 206 | final_call_type, first_date, last_date |
| `ems_coverage_breaks.csv` | 23 | window, group, final_call_type, kind, date |
| `ems_missing_district_rate_by_year.csv` | 11 | year, missing_district_rate |
| `freeze_access_log.csv` | 8 | accessed_utc, exemption, script, git_commit, rows_total, rows_confirmation_window, date_min, date_max, disclosure |
| `precinct_cd_crosswalk.csv` | 131 | policeprecinct, communitydistrict, n, w_cd_calls_from_precinct |
| `redirect_resolution.csv` | 54 | redirect, target, target_was_collected_directly |
| `rename_recovery.csv` | 116 | article, n_titles, canonical_views, all_titles_views, gain, titles |
| `source_verification_log.csv` | 18,782 | run_utc, run_id, kind, source_id, target, status, detail |
| `trends_precision_by_year.csv` | 20 | component, year, n_days, n_distinct, nonzero_days, zero_share, max_value, quant_step, rel_step, in_cai_d |
| `victim_curation_table.csv` | 101 | name, tweet_volume, row_type, race, incident_type, incident_date, city, note, confidence, verified |
| `victim_registry.csv` | 13,241 | name, date, race, cause, city, state, mental_illness, source, race_code, in_wapo, wiki_article |
| `wiki_agent_class_break.csv` | 10 | year, user, automated, mean_share, max_share, mean_z_shift, max_z_shift, share_of_total |
| `wiki_basket.csv` | 511 | name, article, category, in_registry, death_date |
| `wiki_ext_aggregation_diagnostic.csv` | 3,472 | date, sum, max, n_articles |
| `wiki_ext_aggregation_diagnostic_broad.csv` | 3,472 | date, sum, max, n_articles |
| `wiki_ext_aggregation_diagnostic_spliced.csv` | 3,472 | date, sum, max, n_articles |
| `wiki_ext_basket_used.csv` | 109 | article, days, views, ok, reason, n_titles, n_titles_offered, n_titles_no_data, n_titles_failed |
| `wiki_ext_basket_used_broad.csv` | 118 | article, days, views, ok, reason, n_titles, n_titles_offered, n_titles_no_data, n_titles_failed |
| `wiki_ext_basket_used_spliced.csv` | 109 | article, days, views, ok, reason, n_titles, n_titles_offered, n_titles_no_data, n_titles_failed |
| `wiki_nyc_articles.csv` | 543 | article, keep, reason, locality, n_categories |
| `wiki_nyc_daily.csv` | 6,944 | date, component, value |
| `wiki_nyc_per_article.csv` | 55,552 | date, article, views |
| `wiki_nyc_validation.csv` | 14 | metric, value, note |
| `wiki_pageviews_by_article.csv` | 231,503 | article, date, views |
| `wiki_pageviews_by_article_broad.csv` | 244,571 | article, date, views |
| `wiki_pageviews_by_article_spliced.csv` | 231,503 | article, date, views |
| `wikipedia_article_resolution.csv` | 109 | name, article |
| `wikipedia_article_resolution_legacy.csv` | 150 | name, tweet_volume, volume_share, article, pageview_days |
| `wikipedia_pageviews_victims.csv` | 25,211 | name, article, date, views |

## data/raw (tracked inputs)

- `.gitkeep`
- `EMS_incident_dispatch_data_description (1).xlsx`
- `nyc_opendata_search_results.json`
- `sf1_dp_cd_demoprofile.xlsx`

## outputs (gitignored except `run_manifest.json`)

- `outputs/tables/*.csv|json`: model tables, calibration certificates and ledgers (kept across cold runs), randomization ledgers, the synthetic dry run of 30.
- `outputs/figures/*.png|pdf`: fig1_raw_series, fig2_irf_primary, fig3_windows, fig4_decomposition, fig5_bridge, zscore_simulation (`08_figures.py`, `25_zscore_simulation.py`).

## The sealed artifacts (tracked, `data/reference/`, 2026-09-21)

Schemas and counts in [[Phase I]]: `confirmatory_results.csv` (166 rows × 36), `confirmatory_results.meta.json`,
`confirmatory_run_log.csv` (8 rows: 7 starts, 1 sealed), `confirmatory_reading.csv` (175 rows × 6) with its sidecar,
`power_analysis_prefreeze.csv` (276 metric rows), `freeze_access_log.csv` (15 declared accesses).

Related: [[Pipeline]] · [[Phase I]] · [[00 Project]]
