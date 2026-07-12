# Data provenance registry

Every data source used anywhere in this project. Machine-readable log with file
hashes: `data/reference/data_sources.csv` (appended automatically by fetch
scripts). Update this file whenever a source is added, replaced, or re-downloaded.

## Primary sources

### S1. NYC EMS Incident Dispatch Data
- **Provider**: FDNY via NYC Open Data, dataset id `76xm-jjuj`
- **URL**: https://data.cityofnewyork.us/Public-Safety/EMS-Incident-Dispatch-Data/76xm-jjuj
- **Access**: full CSV export (~6.5 GB) downloaded by Abrahim Mahmud (original UROP
  download; export date to be pinned — NYC OpenData updates this dataset, so the
  row count of our export, 27.5M rows through 2025-08-31, dates it to ~Sep 2025)
- **Files in project**: processed extracts `data/processed/ems_cd_day_calltype.parquet`
  (2016–2021, produced by `scripts/00_local_ems_extract.py`),
  `data/processed/ems_citywide_day_trends.parquet` (2005–2025)
- **Role**: outcome variables (all EMS call counts/shares)
- **Cite as**: Fire Department of the City of New York. "EMS Incident Dispatch Data."
  NYC Open Data. https://data.cityofnewyork.us/d/76xm-jjuj
- **Companion data dictionary**: `data/raw/EMS_incident_dispatch_data_description (1).xlsx`
  (NYC Open Data attachment; source of disposition-code and call-type descriptions)

### S2. Twitter per-victim daily tweet counts (2017–2020)
- **Provider**: supplied by Prof. Justin Steil (MIT DUSP)
- **File**: `data/raw/211118_tweet_count_name_date.csv` (45,183 rows; date, victim
  name, city, tweet/retweet/quote counts)
- **Collection methodology**: **OPEN ITEM — awaiting details from Prof. Steil**
  (collector, query terms, API, filtering). Required for the paper's data section.
- **Role**: awareness measure (victim-level); race attribution via S4/S6

### S3. Twitter daily aggregate tweet counts (2017–2020)
- **Provider**: same as S2
- **File**: `data/raw/220126_final_daily_tweet_count.csv` (1,461 days)
- **Verified relationship**: exact daily aggregation of S2 (1,459/1,461 days
  identical, 2 off-by-one days) — S2 and S3 are ONE dataset at two granularities,
  not two sources. The single-source awareness series is built from S3.
- **Role**: primary awareness measure

### S4. Washington Post Fatal Force database (cleaned)
- **Provider**: Washington Post (original), cleaned copy supplied by Prof. Steil
- **File**: `data/raw/fatalpoliceshootingsCLEANED.csv` (6,007 records, 2015-01 to
  2021-04; v1 schema with race, city, state, coordinates)
- **Original source**: https://github.com/washingtonpost/data-police-shootings
- **Role**: victim race attribution for race-specific awareness indices
- **Cite as**: The Washington Post. "Fatal Force" database. 2015–2021.

### S5. 2010 Census SF1 demographic profile by community district
- **Provider**: NYC Department of City Planning (Census 2010 SF1)
- **File**: `data/raw/sf1_dp_cd_demoprofile.xlsx`
- **Role**: legacy demographic vintage (heterogeneity robustness comparison)

### S6. Victim curation table (manual)
- **Provider**: constructed in-project from public news reporting (per-row source
  notes in the file); **verification by Abrahim pending** for low-confidence rows
- **File**: `data/reference/victim_curation_table.csv` (~100 victims not matched
  to S4: non-shooting deaths, pre-2015 cases, name variants)
- **Role**: race/incident-type attribution for tweet volume unmatched to S4

## Public augmentation sources (added 2026-07-12, after network-policy change)

### S7. ACS 2015–2019 5-year demographic profile, NTA2020 level
- **Provider**: NYC Department of City Planning (official ACS publication)
- **URL**: https://s-media.nyc.gov/agencies/dcp/assets/files/excel/data-tools/census/acs/demo_2019_acs5yr_nta.xlsx
- **Accessed**: 2026-07-12 via `scripts/09_fetch_public_data.py`
- **Processing**: NTA2020 GeoIDs embed the community district (e.g. BK0301 =
  Brooklyn CD 3), so aggregation to the 59 CDs is exact
- **File in project**: `data/reference/acs_2019_cd_demographics.csv`
- **Role**: period-matched demographics (primary vintage for heterogeneity)
- **Cite as**: U.S. Census Bureau, American Community Survey 2015–2019 5-Year
  Estimates; tabulated by NYC Department of City Planning.
- **Note**: U.S. Census Bureau API route abandoned 2026-07-12 (now requires API key)

### S8. Wikipedia daily pageviews (per-article)
- **Provider**: Wikimedia Foundation, Pageviews REST API
- **Endpoint**: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{article}/daily/20170101/20201231
- **Accessed**: 2026-07-12 via `scripts/09_fetch_public_data.py`
- **Article resolution**: automated for top-150 victims by tweet volume — title
  variants (Killing/Shooting/Murder/Death of X) checked via the Wikipedia REST
  summary API (S9), accepted only if the article summary mentions police;
  resolution log with per-victim status: `data/reference/wikipedia_article_resolution.csv`
- **Files in project**: `data/reference/wikipedia_pageviews_victims.csv`
- **Role**: independent cross-validation of the Twitter awareness measure
  (r = 0.75 in logs; 0.66 excluding the Floyd episode); candidate extension
  instrument beyond 2020
- **Cite as**: Wikimedia Foundation. Pageviews Analysis API.

### S9. Wikipedia REST summary API (article resolution only)
- **Endpoint**: https://en.wikipedia.org/api/rest_v1/page/summary/{title}
- **Role**: existence check + police-mention verification during S8 resolution;
  no data from this endpoint enters the analysis

## Planned sources (not yet fetched)

- **NYC Well contact volumes** (NYC Open Data) — substitution outcome; granularity TBD
- **NYC 311 Service Requests** (NYC Open Data `erm2-nwe9`) — substitution outcome
- **NYPD Calls for Service** (NYC Open Data, 2018+) — Desmond-style 911 replication
- **Google Trends, NYC metro** — NYC-local attention validation
- **Zip-code level EMS re-extract** — finer exposure geography (requires local rerun of script 00)

## Software environment
- Python 3.11; key packages: pandas, duckdb, statsmodels, pyfixest, scipy,
  matplotlib (versions pinned in `requirements.txt` at paper submission)
