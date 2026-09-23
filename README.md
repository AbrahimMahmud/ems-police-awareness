# Public attention to police violence and emergency help-seeking in New York City, 2015–2024

A pre-registered, sealed-confirmation study of whether national attention to police violence changes what
New York City communities ask emergency medical services for. The outcome is the share (and count) of
emergency medical dispatches coded to the Fire Department's emotionally disturbed person (EDP) family, by
community district and day; the exposure is a daily attention index rebuilt from public sources (Wikipedia
pageviews of articles about people killed by police, and United States Google search interest in police
brutality); the design is a stacked episode event study with episode-level randomization inference.

The manuscript is `docs/PAPER.md`; its supplementary material is `docs/SUPPLEMENT.md`.

## Result

Neither confirmation period rejects the pre-specified null after correction over the family of eight tests.
The first-week mean change in the EDP share is −0.00059 (95% CI −0.0032 to 0.0021) before B-HEARD and
−0.00019 (−0.0024 to 0.0020) during its rollout, against a mean share of 0.086; the falsification outcomes
(cardiac, asthma) are quiet. The pre-registered reading is a bounded null in both periods.

## Design and record

- **Pre-registration.** `docs/CONFIRMATION_PLAN.md` (frozen text plus a dated addendum of every deviation) and
  `docs/PRE_ANALYSIS_NOTE.md` (hypotheses, the interpretation table, the reading rules). The confirmation
  periods were protected by a code-level freeze (`scripts/freeze_guard.py`); the five occasions on which
  confirmation-period data were touched before the lift are disclosed in the plan, in `docs/PAPER_MASTER.md`
  §5.3 and in the paper's Limitations, and logged in `data/reference/freeze_access_log.csv`.
- **Sealed run.** `scripts/30_confirmatory_run.py` ran once after the lift and wrote
  `data/reference/confirmatory_results.csv` with a sidecar pinning source hashes, inputs, commit and seed;
  every start is a row of `data/reference/confirmatory_run_log.csv`. `scripts/34_confirmatory_reading.py`
  applies the pre-registered reading rules mechanically (`data/reference/confirmatory_reading.csv`).
- **Claims.** Every result number in the paper, the supplement and the master document is a row of
  `docs/CLAIMS_REGISTER.csv` that recomputes from its artifact (`scripts/31_verify_sources.py`).
- **Gate.** `scripts/23_regression_suite.py` holds the pipeline, the freeze, the sealed run and the
  documents to their stated properties against `docs/regression_baseline.csv`.
- **Master document.** `docs/PAPER_MASTER.md` is the source document the paper was drafted from: data,
  measurement, design, every statistical choice, results and limitations, with the reasoning.

## Layout

```
scripts/     the pipeline (numbered stages), the estimator (event_study.py), the freeze guard, the gate
ops/         restart-tolerant runners for the long jobs; the generators for the paper's tables and figures
data/reference/   committed inputs and the sealed outputs (episode lists, baskets, calibration certificates,
                  the confirmatory table and its reading, the run log)
data/processed/   built panels and caches (regenerated; not tracked)
outputs/     tables and figures written by the pipeline (regenerated; not tracked, except the copies the
             manuscript uses in docs/figures)
docs/        the manuscript, the supplement, the master document, the pre-registration, the claims register,
             the regression baseline, the paper plan, related work, data provenance, the source register
tests/       the gate's synthetic-data checks (run on a clone with no data)
```

## Reproducing

```
uv sync                                   # Python 3.11 with the pinned estimation libraries
bash ops/rebuild.sh                       # download the dispatch extract, build the panel, calibrate the
                                          # randomization nulls, run the discovery-period estimators
cd scripts && PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 23_regression_suite.py
uv run pytest                             # the synthetic-data part of the gate
```

The confirmatory run is sealed; `bash ops/phase_i.sh` re-runs it only against a current calibration
certificate and refuses to overwrite a sealed result without a recorded reason. The pipeline is
byte-reproducible under the fixed seed and single-threaded BLAS the runners set.

## Data

NYC EMS Incident Dispatch Data (Fire Department of the City of New York, NYC OpenData 76xm-jjuj); Wikimedia
REST pageviews; Google Trends; Mapping Police Violence; American Community Survey 2015–2019; B-HEARD precinct
adoption dates compiled from Mayor's Office announcements and the Independent Budget Office's precinct-level
report. Provenance and hashes: `docs/DATA_PROVENANCE.md`, `docs/SOURCE_REGISTER.md`,
`data/reference/data_sources.csv`.
