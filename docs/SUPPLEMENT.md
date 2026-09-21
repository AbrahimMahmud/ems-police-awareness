# Supplementary material — Public attention to police violence and emergency help-seeking in New York City, 2015–2024

*Companion to `docs/PAPER.md`. Every result number here is a claim in `docs/CLAIMS_REGISTER.csv` that recomputes
from its artifact, and every numeric cell of every table below sits inside a claim (`V.claims_cover_exhibits`).
The regions marked in comments are generated from the sealed files and the reference tables by the scripts named
there and are refreshed by `ops/paste_generated.py`; the prose is hand-written. Sections S1.1–S1.10 hold the
Methods detail the main text summarises; S2 is the pre-registered reading exactly as the reader wrote it; S3–S4 are
the tables; S5 the figures; S6 the record.*

---

## S1. Supplementary Methods

### S1.1 The freeze, the record and the five incidents

The confirmation strata were protected by a code-level freeze: every exploratory script draws its sample through
one guard function pinned by name to the discovery window, the sealed confirmatory script alone derives its window
from a single flag, and a regression suite of automated checks (91 at the time of writing) verifies that no other
script can read confirmation-period outcome values without passing through the guard. The hypotheses, the
estimator, the primary inference, the calibration precondition, the sensitivity battery, the multiple-testing
family and the rules for reading every possible result were committed to the repository in dated documents before
the freeze was lifted (`docs/CONFIRMATION_PLAN.md`, the frozen text with a numbered addendum §1–§30;
`docs/PRE_ANALYSIS_NOTE.md`); every deviation from the originally frozen text is listed there. The
pre-registration is internal: its timestamps are git commits, no externally timestamped deposit was made, and that
remedy was foreclosed once the sealed run read the confirmation outcomes.

The freeze was breached five times, four before it lifted and one at the lift, each disclosed and none declared
in advance (`CONFIRMATION_PLAN.md` §15, `PAPER_MASTER.md` §5.3). F1: an automated audit computed the citywide
annual mental-health call share for every year, confirmation years included. F2: a check of call-type birth dates
queried the source API for first-record dates, whole-period and annual totals per call type, citywide monthly
counts across the B-HEARD boundary and precinct-level EDPM counts for June 2021 compared across the three pilot
precincts — and a specification decision, retaining EDPM in the EDP family, was taken on that comparison, so the
composition of the primary outcome is not fully blind. F3: a refutation of an audit finding computed record-level
2014–16 statistics from the outcome extract (missing-district rates, one code's monthly counts and last date,
another's share across the 2015/16 boundary, an estimated step in the mental-health share) and wrote them into the
findings register. F4: the precinct-to-district crosswalk that carries B-HEARD exposure was built from a count of
all dispatches per precinct and district pooled over 2015–2024 — a geography weight with no call type or date,
but a read of confirmation-period counts that no exemption declared, and the one thing kept from the five: it is
inside the B-HEARD exposure covariate of the estimating equation (Table S8). F5: in the gate run made to verify
the lifted state before it was committed, three regression checks that had derived their sample from the freeze
flag selected the confirmation sample once — one fitted the primary specification with and without the B-HEARD
covariate and printed only the largest difference between the two coefficient vectors, the others a shared-days
count and a residual autocorrelation. A separate, declared and logged read of coverage — first and last dates per
code and the yearly missing-district rate, no outcome value — produced the coverage sensitivities. No test of the
hypothesis was read from any of the five; what was kept from them is the F4 weights and the F2 decision, both
stated; their materiality is for the reader to judge and the record is complete.

### S1.2 Data sources in detail

**Emergency medical dispatches.** The NYC EMS Incident Dispatch Data (Fire Department of the City of New York, via
NYC OpenData, dataset 76xm-jjuj) record every emergency medical dispatch in the city with an incident timestamp, a
dispatcher-assigned final call type, a disposition and a community district. The complete set was downloaded
through the open-data API in seven-column pages; the extract's cryptographic hash and page count are recorded in a
provenance register; the page cache itself is not tracked, so a replicator re-downloads from the live dataset and
the register detects a changed source rather than absorbing it. Records whose disposition marks a cancelled,
never-sent or duplicate call, and special-event, standby and transfer incidents, are excluded from numerator and
denominator alike; the filter falls more heavily on EDP than on the comparison families, which is why the
cancelled-inclusive sensitivity restores them (finding O1 in the plan).

**Wikipedia pageviews.** Daily article-level pageviews for human readers (`agent=user`) from the Wikimedia REST
API, 1 July 2015 onward. Pageviews are recorded per title and are not carried across a page move, so every
historical title of each article was resolved through the MediaWiki redirects and revisions interfaces and summed;
without this step the attention to Alton Sterling in the week of his killing, for example, was absent from the
series. The `agent=user` definition changed non-retroactively in April 2020; the spliced sensitivity series adds
the `automated` class to the strict basket so that the series is comparable across the decade, and is identical to
the primary before 2020 by construction.

**Google Trends.** United States daily search interest for the *police brutality* topic, fetched in overlapping
windows and stitched on the overlaps. Trends returns a sample rescaled to each request window; the stitching
diagnostics are committed (`data/reference/cai_trends_stitch_diagnostics.csv`).

**Demographics.** American Community Survey 2015–2019 five-year estimates by community district (New York City
Department of City Planning), used only to describe the setting and to classify districts for an exploratory
heterogeneity analysis by racial composition (not pre-specified; its hypothesis was formed from discovery results).

**B-HEARD adoption.** The precinct-by-precinct rollout dates of the Behavioral Health Emergency Assistance Response
Division, compiled from Mayor's Office announcements and validated against the Independent Budget Office's January
2026 precinct-level report; adoption dates are carried as an earliest and a latest bound because most rest on
low-confidence evidence. Exposure reaches community districts through the crosswalk of Table S8.

**Victim registry.** Mapping Police Violence, used only to label episodes and to supply positive evidence that an
article concerns a police killing; it is never a gate on basket membership.

### S1.3 The attention index and the article basket

The daily attention index averages two standardised components: the sum of pageviews across the article basket,
and national search interest in police brutality. Each component is log-transformed and standardised once, on a
fixed 2017–2019 reference window that contains no George Floyd, and the average is re-standardised on the same
window. The index is never re-standardised inside an analysis sample; the simulation of Figure S5 shows that
within-sample standardisation multiplies a planted coefficient by the within-sample standard deviation of the
regressor, which varies more than threefold across ordinary robustness samples. News coverage (GDELT) is
deliberately excluded from the index — it measures supply — and is kept as a separate falsification series. The
index has no city-local component; the two candidates built for that role were rejected on measurement (one is
censored on a quarter to three quarters of days; the other cannot be made both local and disjoint from the
national basket), so the exposure is national attention.

Candidate articles were collected by walking Wikipedia's category tree for people killed by law enforcement in
the United States, resolving redirects at the point of collection, and resolving each person's date and country of
death from Wikidata. Each article was then classified on public evidence — a category naming law enforcement as
the actor, the article's first sentence, or membership in Mapping Police Violence — into *police violence*,
*unestablished*, or *anti-police* (violence against officers). The strict basket, in which the evidence names law
enforcement as the actor, is the primary exposure; the broad basket adds the articles in which no evidence
establishes who acted, and is a pre-registered sensitivity. Attention to violence against police is in neither.
The basket with every include and exclude reason is `data/reference/basket_decisions.csv` and
`basket_construct_review.csv`; neither uses victims' armed status.

### S1.4 Episodes

An attention episode begins on the first day of a run of days on which the index lies in the top 10% of its own
calendar year, and ends when the run ends. The within-year quantile keeps stringency constant across years; a
fixed threshold selected a share of days that varied several-fold from year to year. Each episode carries two
labels: the registry deaths of the preceding 60 days whose articles drew attention inside the window (the
candidate events of Table S6, empty when the registry holds no recent death), and the articles actually read
during the window, ranked by share of basket pageviews. An episode is a burst of attention, not a killing. The
originally frozen episode rule was a *regime* rule that produced a single episode covering the whole summer of
2020; it was replaced by this *shock* rule while blind to every outcome, and the change is disclosed as a
deviation. The frozen list is preserved byte-identical in the repository beside the adopted list (Table S6).

### S1.5 Outcome families and dispatch codes

Table S7 lists every call type in the extract with its family and its first and last date. The EDP family is the
codes carrying the *emotionally disturbed person* prefix; the narrow mental-health family adds the altered-mental-
status and suicide-related codes; the falsification families are cardiac and asthma; injury is carried as a marker
of street activity; every other code counts in the denominator only. Codes are born and retired across the decade
(EDPC phases in during 2018; EDPM appears on 3 June 2021), and four of the seven EDP codes (EDPC, EDPM, EDPW,
T-EDP) are absent from the FDNY data dictionary and are assigned to the family by their prefix. District-days with
fewer than five dispatches are excluded from the analysis sample in both arms; the three denominator-diagnostic
cells run on the panel without that minimum.

### S1.6 Estimator, randomization inference and the calibration precondition

**Estimator.** For each episode the 14 days before and 14 days after its start are stacked in every community
district, any district-day claimed by two episode windows is assigned to the nearer episode so that no
observation is used twice, and

*y* ~ *i*(relative day, reference = −1) + B-HEARD exposure | episode × district + day of week

is fitted by ordinary least squares for shares and by Poisson pseudo-maximum likelihood with a log offset for
counts, with standard errors clustered on the calendar date, since treatment is citywide and assigned at the date.
Day −1 remains in the sample as the omitted level. The test statistic for the primary hypothesis is a joint Wald
test that the eight coefficients for days 0 to 7 are all zero; the mean of those coefficients is reported as an
effect size and is not the test. A dip followed by a rebound averages to near zero and is invisible to a mean but
not to the joint test. Post-episode windows of 28 and 60 days are sensitivities. The B-HEARD exposure covariate is
identically zero before June 2021, is dropped as collinear, and leaves the discovery and C1 estimates numerically
unchanged, which an automated check asserts.

**Primary inference.** The primary p-value is by episode-level randomization inference: the episode start dates
are relocated to placebo dates that preserve the real episodes' spacing, the estimator is re-run, and the p-value
is (1 + *k*)/(1 + *n*) where *k* is the number of *n* = 2,000 placebo statistics at least as large as the observed
one. Where a stratum is a single contiguous calendar block (discovery, C2) one anchor is drawn uniformly and the
real episodes' inter-episode gaps are laid down from it in a random order, so the multiset of gaps — and with it
the clustering — is preserved on every draw while their sequence is not; where a stratum is two blocks (C1) one
circular shift is drawn within each block so that the number of episodes per block is preserved on every draw.
The two schemes are differently constructed nulls, each certified on its own geometry. The asymptotic joint-Wald
p-value is reported beside the randomization p-value and never instead of it, because on these data formula-based
inference has proved anti-conservative.

**Calibration precondition.** Before any p-value is reported for a stratum, the share-arm estimator (without the
B-HEARD covariate) and the randomization procedure are run, at 200 placebo draws per simulation, on 1,000
synthetic panels (200 for the descriptive pooled sample) built to contain no effect but carrying the serial
dependence, district levels, day-of-week pattern and citywide day shock measured on the discovery rows of the real
panel, on that stratum's own episode geometry and draw scheme — separately for discovery, C1, C2 and the pooled
sample, whose three-window geometry is its own null. The count arm, the narrow mental-health outcome, the
covariate and the sealed run's 2,000-draw resolution are not separately certified; the plan states this as a
limitation (addendum 23.12). The stratum's p-values are reported only if the empirical rejection rate at α = 0.05
lies inside its binomial band and the p-values are uniform against the exact discrete lattice of (1 + *k*)/(1 + *n*)
by a Kolmogorov–Smirnov test with a simulated null (Table S9). The confirmatory script refuses to run without a
current certificate for each stratum naming the scheme it draws. A stratum whose null fails calibration at 1,000
simulations is, by a rule written before that verdict existed, estimated and reported with its randomization
p-values flagged uncertified and excluded from the family decision; its primary inference is then the asymptotic
p, labelled, and a rejection on it cannot count as confirmation (addendum §25; not invoked).

### S1.7 The family, the secondary arms, the sensitivities and the reading rules

**Multiple testing.** The primary family — fixed before the freeze lifted, though its second outcome and its joint
statistic were adopted after discovery results had been seen — is two outcomes (EDP share, narrow mental-health
share) × two arms (share, count) × two strata (C1, C2) = eight tests, controlled by Benjamini–Hochberg at
*q* = 0.05. The pooled estimate (a re-description of the same eight), the sensitivities (robustness readings of
tests already in the family), the two secondary arms (asymptotic p-value only) and the falsification outcomes are
outside the family, each for the reason given in the plan; every result row carries its family membership so
that a reader can recompute the correction under a different definition.

**Secondary arms.** Two pre-registered secondary arms are estimated outside the family and report asymptotic
p-values only, because permuting episode dates holds district exposure fixed and so cannot test a cross-district
contrast: the B-HEARD interaction (C2 only), the first-week coefficient interacted with the district's B-HEARD
exposure, and the dose-response arm, the first-week effect on the share per standard deviation of the episode's
peak attention intensity, whose predicted sign is the hypothesis's (a decline per standard deviation). Both are
read for direction by a pre-specified rule in the two inferential strata and never enter the conclusion; the
pooled dose-response rows are descriptive.

**Sensitivities, pre-specified.** (i) Dropping the July 2016 episode, which contains the killings of Alton
Sterling and Philando Castile and the Dallas attack on police officers; (ii) the broad basket; (iii) the spliced
Wikipedia series; (iv) the late B-HEARD bound; (v) coverage-clean estimates that drop every episode whose window
contains a dispatch code born or retired inside a confirmation window, or the geocoding step at 1 January 2016 at
which the share of dispatches with no district fell by two thirds — a demonstration rather than a correction,
chosen over month-year fixed effects because it changes the sample and not the estimator, so it stays comparable
with the calibrated null — and (vi) a geocoding-clean estimate that drops only the episodes containing that step;
(vii) 28- and 60-day post windows, whose placebo draws keep the certified 14-day geometry; (viii) the outcomes with
cancelled and other never-sent dispositions restored to numerator and denominator; (ix) EDP without the EDPM code,
the one code whose inclusion was decided on confirmation-period counts. Every sensitivity is estimated on both
arms; a branch whose episode set in a stratum is the primary's by construction — the same episode starts, no EDPM
dispatch in the stratum, no coverage break inside any episode window — is marked identical to the primary on its
share row rather than re-estimated under a new seed. Robust means a rejection survives every applicable
sensitivity at unadjusted randomization *p* ≤ 0.05, fragile that it survives none; the set is enumerated in the
reader and held equal to what the sealed run writes.

**Falsification and diagnostics.** Cardiac and asthma shares and counts in every stratum; a placebo cell with
unadjusted randomization *p* ≤ 0.05 overrides every primary rejection in its stratum, which is then reported as
not supporting the hypothesis. Injury is estimated and reported beside them but does not override, because the
exploratory decomposition found it responds to attention episodes. Three diagnostic cells per stratum — each
primary outcome's raw count without an offset, and total dispatches — decide whether a share-arm rejection is
denominator-driven.

**Reading rules.** A family cell *rejects* when its adjusted *p* is below 0.05; a stratum rejects on an outcome
when both arms reject with the same sign of the first-week mean, and direction is that sign. Rejections are read
by rules that are asymmetric across strata: a rejection in C1 alone is confirmation in the clean stratum; a
rejection in C2 alone is not confirmation, because B-HEARD moves the outcome in the hypothesised direction. A
share-arm rejection accompanied by a movement in total dispatches but not in the raw count is denominator-driven;
any placebo rejection within a stratum voids its primary rejections, and a placebo cell that produced no
*p*-value is reported as an incomplete check rather than a passed one. The pooled stratum is read descriptively
(both arms at unadjusted *p* ≤ 0.05 with the same sign) and overturns nothing; the two secondary arms are read
against the directions the plan fixes and never enter the conclusion. These rules are implemented as code
(`34_confirmatory_reading.py`) that reads only the sealed result table and the tracked pre-freeze power table,
seals its own output against the table it read, and is held to its text by planted tables in the regression
suite, so that no judgement intervenes between the sealed numbers and the sentences it returns; those sentences
are reproduced in S2.

### S1.8 Power and the reading of a non-rejection

Before the freeze lifted, the minimum detectable effect at 80% power was computed by simulation for each stratum
against a pre-declared minimum effect of interest of −0.005 in the EDP share, for two effect shapes — a sustained
level shift over the first week and a dip-and-rebound of the same size (Table S10); the power table covers the
EDP share only, so no separate minimum detectable effect exists for the narrow mental-health share. Every stratum
is underpowered for the sustained shape and adequately powered for the transient shape. The minimum detectable
effect is measured against the asymptotic joint-Wald test at the nominal α = 0.05, while the non-rejection it
bounds is a Benjamini–Hochberg-adjusted randomization p; the plan states the bound at the nominal level, quotes
beside it an approximate one-parameter inflation of 1.28 for the eight-test correction (1.21 for the
eight-degree-of-freedom statistic), and records both the difference of tests and the uncorrected placebo override
as limitations of the bound rather than correcting them (addendum 23.11–23.12). The reading of a non-rejection was
therefore fixed in advance: no effect detected; a sustained shift at or above that stratum's minimum detectable
effect is disfavoured; a sustained shift of the minimum effect of interest is not excluded; a transient effect of
that size is disfavoured.

### S1.9 The sealed run and reproducibility

The sealed run (`30_confirmatory_run.py`) draws exactly the pre-specified 2,000 placebos per cell and writes its
result to a tracked file once; it keeps a tracked log of every start and seal, refuses to run without the fixed
hash seed the byte-reproducible pipeline requires, and writes each cell's day-by-day coefficient path so a
rejection without a consistent direction can be shown without a second read (Figure 1, Figure S1). The run was
started seven times before it sealed (20 September 2026 09:29 to 21 September 03:24 UTC): once at the lift, once
after the compute container was suspended, once to raise the number of workers, and twice each — an automatic
retry and a hand relaunch with fewer workers — after each of two kills of the worker pool by the memory limit on
the pooled stratum's cells. Each start is a dated row of the run log: the original start carries no reason, each
relaunch by hand carries the reason given at the time, and the runner's two automatic retries repeat the reason of
the start they retried (the sealed table's `overwrite_reason` column carries the last reason only); the log
records the source hashes of the sealed script, the estimator and the configuration at every start, identical
across the seven, and the sidecar pins the seal-time commit. Every cell resumed from a ledger keyed to its own seed
and design, so no number depends on the restarts.

Python 3.11 with pyfixest, package versions pinned in the repository's lock file, under a fixed hash seed
(`PYTHONHASHSEED=0`) and one linear-algebra thread, so that two cold passes of the pipeline are byte-identical.
One driver script regenerates every build, discovery and check artifact from the recorded inputs and records a
manifest (commit, input hashes, row counts); the null-calibration certificates and the pre-freeze power table are
produced by separate resumable runners (hours of compute) and their hashes are pinned in the sealed run's sidecar;
the sealed run and its reading are one-shot by design and are committed with sidecars naming their source hashes,
inputs, commit and seed, and a second real start requires a recorded reason.

### S1.10 Exploratory analyses

Discovery-period estimates and an outcome decomposition across thirteen outcomes in four dispatch families and
five three-day windows (65 tests under a Bonferroni threshold; Figure S4) are reported as exploratory and are not
tests of the hypothesis. A heterogeneity analysis by district racial composition, whose hypothesis was formed from
discovery results, and a distributed-lag specification of the continuous attention index (Figures S2–S3) were also
estimated on the discovery period; their tables are in the repository.

---

## S2. The pre-registered reading, as the reader wrote it

The sealed run wrote its table once; the pre-registered reading (`34_confirmatory_reading.py`; CONFIRMATION_PLAN
addendum §23, §19 rule 2, §25, 23.1c–e; PRE_ANALYSIS_NOTE §9) is a function of that table and the pre-freeze power
table. Its sentences follow exactly as it wrote them; each is held to `data/reference/confirmatory_reading.csv` by
a registered claim.

<!-- BEGIN:phase_i_prose -->
**Confirmatory strata.** The sealed run (`30_confirmatory_run.py`) wrote its table once; the pre-registered reading (`34_confirmatory_reading.py`; CONFIRMATION_PLAN addendum §23, §19 rule 2, §25, 23.1c–e; PRE_ANALYSIS_NOTE §9) is a function of that table and the pre-freeze power table, and its sentences are quoted here as it wrote them.

*C1, the clean stratum.* Primary family (23.1–23.4), C1: “does not reject”. Against the pre-freeze power (§19 rule 2), C1: “no effect detected at the family level (smallest unadjusted randomization p among the stratum's primary cells 0.0115); a sustained level shift at or above the pre-freeze MDE 0.01156 in absolute value (about 0.01480 under the approximate one-parameter family correction of 23.11) is disfavoured at 80% power; a sustained shift of the minimum effect of interest (−0.005) is not excluded; a transient dip-and-rebound of the minimum effect of interest is disfavoured (its pre-freeze MDE is 0.00382, at or below 0.005 in absolute value)”. Sensitivities (§9.5, 23.1c), C1: “primary does not reject; 14 of 24 H1-outcome sensitivity cells at p <= 0.05 (reported, not substituted)”. Falsification outcomes (23.4), C1: “no cardiac or asthma cell at p <= 0.05 (4 of 4 override cells with a p-value)”.

*C2, the B-HEARD-exposed stratum.* Primary family (23.1–23.4), C2: “does not reject”. Against the pre-freeze power (§19 rule 2), C2: “no effect detected at the family level (smallest unadjusted randomization p among the stratum's primary cells 0.4523); a sustained level shift at or above the pre-freeze MDE 0.00875 in absolute value (about 0.01120 under the approximate one-parameter family correction of 23.11) is disfavoured at 80% power; a sustained shift of the minimum effect of interest (−0.005) is not excluded; a transient dip-and-rebound of the minimum effect of interest is disfavoured (its pre-freeze MDE is 0.00290, at or below 0.005 in absolute value)”. Sensitivities (§9.5, 23.1c), C2: “primary does not reject; 0 of 30 H1-outcome sensitivity cells at p <= 0.05”. Falsification outcomes (23.4), C2: “no cardiac or asthma cell at p <= 0.05 (4 of 4 override cells with a p-value)”.

*Pooled (descriptive, 23.1d).* “pooled does not reject on both arms (descriptive)”.

*Secondary arms (23.1e; asymptotic p, outside the family).* C1 dose-response (per SD of peak intensity), EDP share (share, per SD intensity): “moves against the predicted direction (asymptotic p = 0.0309; coef +0.001309)”; C1 dose-response (per SD of peak intensity), narrow MH share (share, per SD intensity): “moves against the predicted direction (asymptotic p = 0.0187; coef +0.001508)”; C2 dose-response (per SD of peak intensity), EDP share (share, per SD intensity): “no movement (asymptotic p = 0.2412 > 0.05)”; C2 dose-response (per SD of peak intensity), narrow MH share (share, per SD intensity): “no movement (asymptotic p = 0.1820 > 0.05)”; C2 B-HEARD interaction, EDP share (share): “no movement (asymptotic p = 0.7732 > 0.05)”; C2 B-HEARD interaction, EDP count (count): “no movement (asymptotic p = 0.8496 > 0.05)”; C2 B-HEARD interaction, narrow MH share (share): “no movement (asymptotic p = 0.9761 > 0.05)”; C2 B-HEARD interaction, narrow MH count (count): “no movement (asymptotic p = 0.8933 > 0.05)”.

**Conclusion under note §9.4 as amended by addendum 23:** “THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2”.
<!-- END:phase_i_prose -->

---

## S3. The sealed run's tables (Tables S1–S5)

Rendered from `data/reference/confirmatory_results.csv` and `confirmatory_reading.csv` by `ops/phase_i_tables.py`;
every numeric cell is a registered claim. Table S6, the episode list under the adopted shock rule with the frozen
list beside it, is `docs/tables/TABLE1_episodes.md`, generated by `ops/paper_table1.py` and re-rendered by the
regression suite, which requires identical bytes.

<!-- BEGIN:phase_i_tables -->
**Table S1 — The pre-specified primary family: two outcomes × two arms × two strata.** First-week mean coefficient with its date-clustered SE, the joint Wald statistic on days 0–7, the randomization p at 2,000 draws, the Benjamini–Hochberg-adjusted p over the family of eight, and the asymptotic p beside it.

| stratum | outcome | arm | episodes | first-week mean | SE | joint χ² | RI p | BH p | asymptotic p |
|---|---|---|---|---|---|---|---|---|---|
| C1 | EDP share | share | 15 | −0.00059 | 0.00136 | 25.32 | 0.0115 | 0.0560 | 0.0014 |
| C1 | EDP count | count | 15 | 0.00945 | 0.01623 | 26.11 | 0.0140 | 0.0560 | 0.0010 |
| C1 | narrow MH share | share | 15 | −0.00074 | 0.00157 | 22.57 | 0.0285 | 0.0760 | 0.0040 |
| C1 | narrow MH count | count | 15 | −0.00013 | 0.01420 | 17.09 | 0.0895 | 0.1789 | 0.0291 |
| C2 | EDP share | share | 30 | −0.00019 | 0.00114 | 6.04 | 0.6522 | 0.7453 | 0.6430 |
| C2 | EDP count | count | 30 | 0.00591 | 0.01127 | 4.75 | 0.7861 | 0.7861 | 0.7843 |
| C2 | narrow MH share | share | 30 | −0.00067 | 0.00133 | 7.98 | 0.4523 | 0.6597 | 0.4352 |
| C2 | narrow MH count | count | 30 | 0.00197 | 0.01079 | 7.57 | 0.4948 | 0.6597 | 0.4764 |

**Table S2 — The pre-registered reading, applied by code (addendum §23, §19 rule 2, §25).**

| stratum | null certified | stratum rejects | placebo rejects | pre-freeze MDE, sustained | × family correction | pre-freeze MDE, transient |
|---|---|---|---|---|---|---|
| C1 | 1 | 0 | 0 | 0.01156 | 0.01480 | 0.00382 |
| C1 reading | does not reject | | | | | |
| C2 | 1 | 0 | 0 | 0.00875 | 0.01120 | 0.00290 |
| C2 reading | does not reject | | | | | |

*Conclusion under note §9.4 as amended: THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2*

**Table S3 — Falsification outcomes and the denominator diagnostic, per stratum (unadjusted randomization p; addendum §23.3–23.4).** Cardiac and asthma cells at p ≤ 0.05 override the stratum's primary rejections; injury is reported but does not override (§23.4); the no-offset counts are the denominator diagnostic (§23.3).
 The pooled rows are descriptive (23.1d): the override rule reads C1 and C2 only.
| stratum | outcome | arm | episodes | first-week mean | RI p | asymptotic p |
|---|---|---|---|---|---|---|
| C1 | EDP count | count, no offset | 15 | −0.01180 | 0.0115 | 0.0004 |
| C1 | narrow MH count | count, no offset | 15 | −0.01965 | 0.0775 | 0.0188 |
| C1 | total dispatches | count, no offset | 15 | −0.01585 | 0.5422 | 0.5039 |
| C1 | cardiac share | share | 15 | 0.00121 | 0.2609 | 0.1240 |
| C1 | cardiac count | count | 15 | 0.01385 | 0.5597 | 0.4286 |
| C1 | injury share | share | 15 | −0.00185 | 0.3453 | 0.2919 |
| C1 | injury count | count | 15 | −0.01192 | 0.3713 | 0.2632 |
| C1 | asthma share | share | 15 | 0.00018 | 0.1619 | 0.0987 |
| C1 | asthma count | count | 15 | 0.03038 | 0.5792 | 0.4267 |
| C2 | EDP count | count, no offset | 30 | −0.00442 | 0.3368 | 0.3222 |
| C2 | narrow MH count | count, no offset | 30 | −0.00840 | 0.1054 | 0.0778 |
| C2 | total dispatches | count, no offset | 30 | −0.01004 | 0.7481 | 0.8067 |
| C2 | cardiac share | share | 30 | 0.00118 | 0.7736 | 0.7327 |
| C2 | cardiac count | count | 30 | 0.00988 | 0.8866 | 0.8643 |
| C2 | injury share | share | 30 | −0.00004 | 0.2074 | 0.1856 |
| C2 | injury count | count | 30 | −0.00124 | 0.2039 | 0.1796 |
| C2 | asthma share | share | 30 | 0.00032 | 0.9630 | 0.9576 |
| C2 | asthma count | count | 30 | 0.03192 | 0.9675 | 0.9670 |
| pooled | EDP count | count, no offset | 45 | −0.00614 | 0.0215 | 0.0143 |
| pooled | narrow MH count | count, no offset | 45 | −0.01184 | 0.0260 | 0.0086 |
| pooled | total dispatches | count, no offset | 45 | −0.01215 | 0.5697 | 0.6621 |
| pooled | cardiac share | share | 45 | 0.00122 | 0.5462 | 0.4826 |
| pooled | cardiac count | count | 45 | 0.01105 | 0.7461 | 0.7106 |
| pooled | injury share | share | 45 | −0.00018 | 0.0965 | 0.0998 |
| pooled | injury count | count | 45 | −0.00196 | 0.1329 | 0.1460 |
| pooled | asthma share | share | 45 | 0.00024 | 0.7016 | 0.6930 |
| pooled | asthma count | count | 45 | 0.03191 | 0.9315 | 0.9163 |

**Table S4 — Pre-registered sensitivities, reported beside the primary and never substituted for it (note §9.5).** IDENTICAL means the cell is the primary by construction — the branch's episode starts in that stratum equal the primary's, the stratum has no EDPM dispatch (C1, EDP without EDPM), or no episode window contains a coverage break (C2) — so no second p-value is printed (addendum §23.6); the sealed table's status column gives the reason per cell.

| stratum | sensitivity | outcome | arm | episodes | first-week mean | RI p |
|---|---|---|---|---|---|---|
| C1 | broad basket | EDP share | share | IDENTICAL_TO_PRIMARY | | |
| C1 | broad basket | narrow MH share | share | IDENTICAL_TO_PRIMARY | | |
| C1 | spliced Wikipedia series | EDP share | share | IDENTICAL_TO_PRIMARY | | |
| C1 | spliced Wikipedia series | narrow MH share | share | IDENTICAL_TO_PRIMARY | | |
| C1 | EDP without EDPM | EDP share without EDPM | share | IDENTICAL_TO_PRIMARY | | |
| C1 | EDP without EDPM | EDP count without EDPM | count | IDENTICAL_TO_PRIMARY | | |
| C1 | post window 28 days | EDP share | share | 15 | −0.00048 | 0.0070 |
| C1 | post window 28 days | EDP count | count | 15 | 0.01081 | 0.0170 |
| C1 | post window 28 days | narrow MH share | share | 15 | −0.00057 | 0.0460 |
| C1 | post window 28 days | narrow MH count | count | 15 | 0.00145 | 0.1769 |
| C1 | post window 60 days | EDP share | share | 15 | −0.00047 | 0.0190 |
| C1 | post window 60 days | EDP count | count | 15 | 0.01007 | 0.0320 |
| C1 | post window 60 days | narrow MH share | share | 15 | −0.00059 | 0.0625 |
| C1 | post window 60 days | narrow MH count | count | 15 | 0.00085 | 0.2159 |
| C1 | drop July 2016 | EDP share | share | 14 | −0.00141 | 0.0090 |
| C1 | drop July 2016 | EDP count | count | 14 | 0.00115 | 0.0060 |
| C1 | drop July 2016 | narrow MH share | share | 14 | −0.00168 | 0.0325 |
| C1 | drop July 2016 | narrow MH count | count | 14 | −0.00765 | 0.0645 |
| C1 | coverage-clean | EDP share | share | 13 | −0.00098 | 0.0260 |
| C1 | coverage-clean | EDP count | count | 13 | 0.00729 | 0.0155 |
| C1 | geocoding-clean | EDP share | share | 14 | −0.00054 | 0.0090 |
| C1 | geocoding-clean | EDP count | count | 14 | 0.01075 | 0.0045 |
| C1 | coverage-clean | narrow MH share | share | 12 | −0.00036 | 0.0520 |
| C1 | coverage-clean | narrow MH count | count | 12 | −0.00014 | 0.1154 |
| C1 | geocoding-clean | narrow MH share | share | 14 | −0.00036 | 0.0455 |
| C1 | geocoding-clean | narrow MH count | count | 14 | 0.00282 | 0.0730 |
| C1 | coverage-clean | cardiac share | share | 13 | 0.00202 | 0.1639 |
| C1 | coverage-clean | cardiac count | count | 13 | 0.02326 | 0.2924 |
| C1 | coverage-clean | injury share | share | 14 | −0.00122 | 0.5967 |
| C1 | coverage-clean | injury count | count | 14 | −0.00737 | 0.5647 |
| C1 | coverage-clean | asthma share | share | 14 | 0.00010 | 0.2429 |
| C1 | coverage-clean | asthma count | count | 14 | 0.02959 | 0.7096 |
| C1 | cancelled dispositions included | EDP share, cancelled included | share | 15 | −0.00094 | 0.0580 |
| C1 | cancelled dispositions included | EDP count, cancelled included | count | 15 | 0.00471 | 0.0235 |
| C1 | cancelled dispositions included | narrow MH share, cancelled included | share | 15 | −0.00105 | 0.3553 |
| C1 | cancelled dispositions included | narrow MH count, cancelled included | count | 15 | −0.00251 | 0.3573 |
| C2 | geocoding-clean | EDP share | share | IDENTICAL_TO_PRIMARY | | |
| C2 | geocoding-clean | narrow MH share | share | IDENTICAL_TO_PRIMARY | | |
| C2 | coverage-clean | injury share | share | IDENTICAL_TO_PRIMARY | | |
| C2 | post window 28 days | EDP share | share | 30 | −0.00021 | 0.6177 |
| C2 | post window 28 days | EDP count | count | 30 | 0.00572 | 0.7141 |
| C2 | post window 28 days | narrow MH share | share | 30 | −0.00071 | 0.3678 |
| C2 | post window 28 days | narrow MH count | count | 30 | 0.00183 | 0.3638 |
| C2 | post window 60 days | EDP share | share | 30 | −0.00018 | 0.6427 |
| C2 | post window 60 days | EDP count | count | 30 | 0.00545 | 0.7591 |
| C2 | post window 60 days | narrow MH share | share | 30 | −0.00071 | 0.4318 |
| C2 | post window 60 days | narrow MH count | count | 30 | 0.00136 | 0.4293 |
| C2 | broad basket | EDP share | share | 31 | 0.00023 | 0.6682 |
| C2 | broad basket | EDP count | count | 31 | 0.00786 | 0.5987 |
| C2 | broad basket | narrow MH share | share | 31 | −0.00021 | 0.5957 |
| C2 | broad basket | narrow MH count | count | 31 | 0.00375 | 0.5692 |
| C2 | spliced Wikipedia series | EDP share | share | 30 | 0.00004 | 0.5637 |
| C2 | spliced Wikipedia series | EDP count | count | 30 | 0.00723 | 0.6262 |
| C2 | spliced Wikipedia series | narrow MH share | share | 30 | −0.00048 | 0.6222 |
| C2 | spliced Wikipedia series | narrow MH count | count | 30 | 0.00247 | 0.5447 |
| C2 | coverage-clean | EDP share | share | 28 | −0.00016 | 0.4693 |
| C2 | coverage-clean | EDP count | count | 28 | 0.00688 | 0.6052 |
| C2 | coverage-clean | narrow MH share | share | 27 | −0.00047 | 0.2699 |
| C2 | coverage-clean | narrow MH count | count | 27 | 0.00408 | 0.1964 |
| C2 | coverage-clean | cardiac share | share | 25 | 0.00081 | 0.8901 |
| C2 | coverage-clean | cardiac count | count | 25 | 0.00242 | 0.9370 |
| C2 | coverage-clean | asthma share | share | 28 | 0.00020 | 0.9340 |
| C2 | coverage-clean | asthma count | count | 28 | 0.01475 | 0.8411 |
| C2 | cancelled dispositions included | EDP share, cancelled included | share | 30 | −0.00039 | 0.0670 |
| C2 | cancelled dispositions included | EDP count, cancelled included | count | 30 | 0.00408 | 0.0825 |
| C2 | cancelled dispositions included | narrow MH share, cancelled included | share | 30 | −0.00083 | 0.0655 |
| C2 | cancelled dispositions included | narrow MH count, cancelled included | count | 30 | 0.00093 | 0.0565 |
| C2 | EDP without EDPM | EDP share without EDPM | share | 30 | −0.00096 | 0.9285 |
| C2 | EDP without EDPM | EDP count without EDPM | count | 30 | −0.00060 | 0.9835 |
| C2 | late B-HEARD bound | EDP share | share | 30 | −0.00019 | 0.6352 |
| C2 | late B-HEARD bound | EDP count | count | 30 | 0.00582 | 0.7751 |
| C2 | late B-HEARD bound | narrow MH share | share | 30 | −0.00068 | 0.4483 |
| C2 | late B-HEARD bound | narrow MH count | count | 30 | 0.00189 | 0.4978 |
| pooled | post window 28 days | EDP share | share | 45 | −0.00037 | 0.2329 |
| pooled | post window 28 days | EDP count | count | 45 | 0.00762 | 0.1744 |
| pooled | post window 28 days | narrow MH share | share | 45 | −0.00078 | 0.2499 |
| pooled | post window 28 days | narrow MH count | count | 45 | 0.00158 | 0.0995 |
| pooled | post window 60 days | EDP share | share | 45 | −0.00031 | 0.2789 |
| pooled | post window 60 days | EDP count | count | 45 | 0.00776 | 0.1934 |
| pooled | post window 60 days | narrow MH share | share | 45 | −0.00074 | 0.2459 |
| pooled | post window 60 days | narrow MH count | count | 45 | 0.00155 | 0.1129 |
| pooled | drop July 2016 | EDP share | share | 44 | −0.00067 | 0.2519 |
| pooled | drop July 2016 | EDP count | count | 44 | 0.00465 | 0.2309 |
| pooled | drop July 2016 | narrow MH share | share | 44 | −0.00115 | 0.2354 |
| pooled | drop July 2016 | narrow MH count | count | 44 | −0.00112 | 0.1274 |
| pooled | broad basket | EDP share | share | 46 | −0.00005 | 0.5402 |
| pooled | broad basket | EDP count | count | 46 | 0.00908 | 0.2984 |
| pooled | broad basket | narrow MH share | share | 46 | −0.00043 | 0.5222 |
| pooled | broad basket | narrow MH count | count | 46 | 0.00301 | 0.2994 |
| pooled | spliced Wikipedia series | EDP share | share | 45 | −0.00018 | 0.2989 |
| pooled | spliced Wikipedia series | EDP count | count | 45 | 0.00869 | 0.2219 |
| pooled | spliced Wikipedia series | narrow MH share | share | 45 | −0.00060 | 0.3708 |
| pooled | spliced Wikipedia series | narrow MH count | count | 45 | 0.00219 | 0.1534 |
| pooled | coverage-clean | EDP share | share | 41 | −0.00034 | 0.2484 |
| pooled | coverage-clean | EDP count | count | 41 | 0.00856 | 0.1619 |
| pooled | geocoding-clean | EDP share | share | 44 | −0.00028 | 0.3233 |
| pooled | geocoding-clean | EDP count | count | 44 | 0.00829 | 0.2144 |
| pooled | coverage-clean | narrow MH share | share | 39 | −0.00042 | 0.2264 |
| pooled | coverage-clean | narrow MH count | count | 39 | 0.00393 | 0.0350 |
| pooled | geocoding-clean | narrow MH share | share | 44 | −0.00060 | 0.3748 |
| pooled | geocoding-clean | narrow MH count | count | 44 | 0.00275 | 0.1544 |
| pooled | coverage-clean | cardiac share | share | 38 | 0.00127 | 0.7326 |
| pooled | coverage-clean | cardiac count | count | 38 | 0.00892 | 0.8891 |
| pooled | coverage-clean | injury share | share | 44 | −0.00001 | 0.1559 |
| pooled | coverage-clean | injury count | count | 44 | −0.00076 | 0.1964 |
| pooled | coverage-clean | asthma share | share | 42 | 0.00014 | 0.7781 |
| pooled | coverage-clean | asthma count | count | 42 | 0.02183 | 0.9390 |
| pooled | cancelled dispositions included | EDP share, cancelled included | share | 45 | −0.00063 | 0.0170 |
| pooled | cancelled dispositions included | EDP count, cancelled included | count | 45 | 0.00516 | 0.0075 |
| pooled | cancelled dispositions included | narrow MH share, cancelled included | share | 45 | −0.00100 | 0.0665 |
| pooled | cancelled dispositions included | narrow MH count, cancelled included | count | 45 | 0.00036 | 0.0180 |
| pooled | EDP without EDPM | EDP share without EDPM | share | 45 | −0.00063 | 0.3183 |
| pooled | EDP without EDPM | EDP count without EDPM | count | 45 | 0.00529 | 0.4113 |
| pooled | late B-HEARD bound | EDP share | share | 45 | −0.00036 | 0.2534 |
| pooled | late B-HEARD bound | EDP count | count | 45 | 0.00756 | 0.1959 |
| pooled | late B-HEARD bound | narrow MH share | share | 45 | −0.00077 | 0.2584 |
| pooled | late B-HEARD bound | narrow MH count | count | 45 | 0.00157 | 0.1219 |

**Table S5 — The pooled stratum (descriptive, outside the family) and the two secondary arms, the B-HEARD interaction (C2) and the dose-response arm (asymptotic p only; note §10, addendum §9).** The reader applies rule 23.1e to the secondary arms in C1 and C2; the pooled dose-response rows are descriptive and are not read.

| stratum | item | outcome | arm | episodes | coefficient | RI p | asymptotic p |
|---|---|---|---|---|---|---|---|
| pooled | primary design | EDP share | share | 45 | −0.00036 | 0.2329 | 0.2340 |
| pooled | primary design | EDP count | count | 45 | 0.00762 | 0.1824 | 0.1710 |
| pooled | primary design | narrow MH share | share | 45 | −0.00077 | 0.2599 | 0.2382 |
| pooled | primary design | narrow MH count | count | 45 | 0.00163 | 0.1124 | 0.1013 |
| C1 | dose-response (per SD of peak intensity) | EDP share | share, per SD intensity | 15 | 0.00131 | — | 0.0309 |
| C1 | dose-response (per SD of peak intensity) | narrow MH share | share, per SD intensity | 15 | 0.00151 | — | 0.0187 |
| C2 | dose-response (per SD of peak intensity) | EDP share | share, per SD intensity | 30 | 0.00065 | — | 0.2412 |
| C2 | dose-response (per SD of peak intensity) | narrow MH share | share, per SD intensity | 30 | 0.00074 | — | 0.1820 |
| pooled | dose-response (per SD of peak intensity) | EDP share | share, per SD intensity | 45 | 0.00080 | — | 0.0364 |
| pooled | dose-response (per SD of peak intensity) | narrow MH share | share, per SD intensity | 45 | 0.00110 | — | 0.0050 |
| C2 | B-HEARD interaction | EDP share | share | 30 | 0.00026 | — | 0.7732 |
| C2 | B-HEARD interaction | EDP count | count | 30 | 0.00200 | — | 0.8496 |
| C2 | B-HEARD interaction | narrow MH share | share | 30 | 0.00003 | — | 0.9761 |
| C2 | B-HEARD interaction | narrow MH count | count | 30 | −0.00120 | — | 0.8933 |
<!-- END:phase_i_tables -->

---

## S4. Codes, linkage, calibration and power (Tables S7–S10)

<!-- BEGIN:supp_tables -->
**Table S7 — Every dispatch call type in the extract (206 codes), its outcome family and its first and last date in the data (RECORD 7.1).** Families are `config.CALL_TYPE_GROUPS`; a code outside every family counts in the denominator only. Source: `data/reference/ems_call_code_span.csv` (`35_coverage_breaks.py`).

| code | family | first date | last date |
|---|---|---|---|
| `EDP` | EDP (primary) | 2014-12-01 | 2024-12-31 |
| `EDPC` | EDP (primary) | 2018-07-06 | 2024-12-31 |
| `EDPE` | EDP (primary) | 2024-04-10 | 2024-12-31 |
| `EDPM` | EDP (primary) | 2021-06-03 | 2024-12-31 |
| `EDPT` | EDP (primary) | 2023-03-01 | 2024-12-31 |
| `EDPW` | EDP (primary) | 2018-10-28 | 2021-08-25 |
| `T-EDP` | EDP (primary) | 2020-06-05 | 2024-12-31 |
| `ALTMEN` | altered mental status (narrow MH) | 2014-12-01 | 2024-12-31 |
| `ALTMFC` | altered mental status (narrow MH) | 2014-12-24 | 2024-03-30 |
| `ALTMFT` | altered mental status (narrow MH) | 2021-03-10 | 2022-12-24 |
| `ASTHFC` | asthma (falsification) | 2014-12-01 | 2024-12-19 |
| `ASTHFT` | asthma (falsification) | 2021-12-19 | 2023-05-21 |
| `ASTHMB` | asthma (falsification) | 2014-12-01 | 2024-12-31 |
| `ARREFC` | cardiac (falsification) | 2015-03-17 | 2024-04-24 |
| `ARREFT` | cardiac (falsification) | 2022-11-21 | 2022-12-03 |
| `ARREST` | cardiac (falsification) | 2014-12-01 | 2024-12-31 |
| `CARD` | cardiac (falsification) | 2014-12-01 | 2024-12-31 |
| `CARDFC` | cardiac (falsification) | 2014-12-28 | 2024-06-29 |
| `CARDFT` | cardiac (falsification) | 2021-01-06 | 2023-01-14 |
| `CVA` | cardiac (falsification) | 2014-12-01 | 2024-12-31 |
| `CVAC` | cardiac (falsification) | 2014-12-01 | 2024-12-31 |
| `CVACFC` | cardiac (falsification) | 2015-01-13 | 2024-03-31 |
| `CVACFT` | cardiac (falsification) | 2022-11-01 | 2022-11-01 |
| `CVAFC` | cardiac (falsification) | 2015-03-09 | 2023-11-27 |
| `INJALS` | injury (marker) | 2014-12-01 | 2015-12-16 |
| `INJMAJ` | injury (marker) | 2014-12-01 | 2024-12-31 |
| `INJMIN` | injury (marker) | 2014-12-01 | 2024-12-31 |
| `INJURY` | injury (marker) | 2014-12-01 | 2024-12-31 |
| `MVAINJ` | injury (marker) | 2014-12-01 | 2024-12-31 |
| `TRAUMA` | injury (marker) | 2014-12-01 | 2024-12-31 |
| `ABDPFC` | other (denominator only) | 2014-12-02 | 2024-07-13 |
| `ABDPFT` | other (denominator only) | 2015-06-20 | 2023-01-16 |
| `ABDPN` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `ABDPRF` | other (denominator only) | 2022-06-08 | 2023-03-30 |
| `ACTIVE` | other (denominator only) | 2016-10-01 | 2024-12-07 |
| `ALTMRF` | other (denominator only) | 2022-06-08 | 2023-03-29 |
| `AMPMAJ` | other (denominator only) | 2014-12-02 | 2024-12-29 |
| `AMPMIN` | other (denominator only) | 2014-12-01 | 2024-12-27 |
| `ANAPFC` | other (denominator only) | 2014-12-01 | 2024-09-09 |
| `ANAPFT` | other (denominator only) | 2023-01-17 | 2023-01-17 |
| `ANAPH` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `ANAPRF` | other (denominator only) | 2021-04-19 | 2023-03-30 |
| `ARRERF` | other (denominator only) | 2022-06-08 | 2023-03-08 |
| `ASTHRF` | other (denominator only) | 2022-06-29 | 2023-03-18 |
| `BURNHM` | other (denominator only) | 2024-04-15 | 2024-12-31 |
| `BURNHZ` | other (denominator only) | 2024-04-11 | 2024-12-30 |
| `BURNMA` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `BURNMI` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `CARDBR` | other (denominator only) | 2017-03-28 | 2024-12-31 |
| `CARDRF` | other (denominator only) | 2022-06-08 | 2023-03-31 |
| `CDBRFC` | other (denominator only) | 2020-01-30 | 2024-07-27 |
| `CDBRFT` | other (denominator only) | 2022-10-28 | 2023-10-27 |
| `CDBRRF` | other (denominator only) | 2022-04-05 | 2023-03-30 |
| `CHILDA` | other (denominator only) | 2014-12-03 | 2024-12-31 |
| `CHOKE` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `CHOKFC` | other (denominator only) | 2014-12-02 | 2024-03-17 |
| `CHOKRF` | other (denominator only) | 2022-06-21 | 2023-03-16 |
| `COLD` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `COVINF` | other (denominator only) | 2020-03-24 | 2020-05-05 |
| `CVACRF` | other (denominator only) | 2022-06-11 | 2023-03-24 |
| `CVARF` | other (denominator only) | 2022-06-20 | 2023-03-23 |
| `DIFFBR` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `DIFFFC` | other (denominator only) | 2014-12-01 | 2024-09-11 |
| `DIFFFT` | other (denominator only) | 2022-10-27 | 2022-11-18 |
| `DIFFRF` | other (denominator only) | 2015-01-20 | 2023-05-05 |
| `DOA` | other (denominator only) | 2014-12-22 | 2024-12-27 |
| `DOAU` | other (denominator only) | 2024-02-06 | 2024-07-03 |
| `DROWN` | other (denominator only) | 2014-12-04 | 2024-12-24 |
| `DRUGFT` | other (denominator only) | 2022-11-04 | 2022-11-21 |
| `DRUGRF` | other (denominator only) | 2022-06-10 | 2023-03-28 |
| `ELECT` | other (denominator only) | 2014-12-04 | 2024-12-31 |
| `GYNHEM` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `GYNMAJ` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `HEAT` | other (denominator only) | 2014-12-27 | 2024-12-28 |
| `HYPTN` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `INBLED` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `INBLFC` | other (denominator only) | 2014-12-30 | 2024-03-06 |
| `INBLFT` | other (denominator only) | 2022-11-02 | 2023-01-24 |
| `INBLRF` | other (denominator only) | 2022-06-08 | 2023-03-30 |
| `INHALE` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `MCI21` | other (denominator only) | 2015-03-31 | 2024-12-31 |
| `MCI21P` | other (denominator only) | 2014-12-01 | 2018-01-02 |
| `MCI22` | other (denominator only) | 2018-01-04 | 2024-12-31 |
| `MCI22P` | other (denominator only) | 2014-12-05 | 2018-01-02 |
| `MCI23` | other (denominator only) | 2018-01-02 | 2024-12-04 |
| `MCI23P` | other (denominator only) | 2014-12-02 | 2017-12-28 |
| `MCI24` | other (denominator only) | 2018-01-30 | 2024-08-26 |
| `MCI24P` | other (denominator only) | 2015-01-21 | 2017-12-28 |
| `MCI25` | other (denominator only) | 2018-01-08 | 2024-11-01 |
| `MCI25P` | other (denominator only) | 2014-12-17 | 2018-01-02 |
| `MCI26` | other (denominator only) | 2015-04-08 | 2015-04-08 |
| `MCI26P` | other (denominator only) | 2014-12-02 | 2017-02-06 |
| `MCI28` | other (denominator only) | 2019-12-13 | 2022-04-18 |
| `MCI28P` | other (denominator only) | 2015-07-31 | 2017-08-30 |
| `MCI29` | other (denominator only) | 2018-01-13 | 2024-12-09 |
| `MCI29P` | other (denominator only) | 2014-12-02 | 2017-11-13 |
| `MCI30P` | other (denominator only) | 2015-02-23 | 2017-12-11 |
| `MCI31` | other (denominator only) | 2018-03-24 | 2024-01-04 |
| `MCI31P` | other (denominator only) | 2015-04-06 | 2017-12-19 |
| `MCI32` | other (denominator only) | 2018-01-02 | 2024-12-31 |
| `MCI32P` | other (denominator only) | 2014-12-03 | 2018-01-02 |
| `MCI33` | other (denominator only) | 2018-05-02 | 2024-11-18 |
| `MCI33P` | other (denominator only) | 2015-02-25 | 2017-12-01 |
| `MCI34` | other (denominator only) | 2018-03-16 | 2024-08-28 |
| `MCI34P` | other (denominator only) | 2015-01-21 | 2017-12-12 |
| `MCI35` | other (denominator only) | 2018-02-13 | 2024-06-09 |
| `MCI35P` | other (denominator only) | 2014-12-17 | 2017-12-24 |
| `MCI38` | other (denominator only) | 2018-05-07 | 2024-08-15 |
| `MCI38P` | other (denominator only) | 2015-08-12 | 2017-07-28 |
| `MCI40` | other (denominator only) | 2018-03-11 | 2020-10-04 |
| `MCI40P` | other (denominator only) | 2015-03-05 | 2016-05-27 |
| `MCI42` | other (denominator only) | 2020-01-28 | 2024-06-21 |
| `MCI42P` | other (denominator only) | 2015-05-19 | 2017-08-03 |
| `MCI43` | other (denominator only) | 2014-12-25 | 2024-12-31 |
| `MCI43P` | other (denominator only) | 2014-12-02 | 2017-12-30 |
| `MCI44` | other (denominator only) | 2018-02-06 | 2021-08-31 |
| `MCI44P` | other (denominator only) | 2014-12-10 | 2017-07-26 |
| `MCI50` | other (denominator only) | 2019-09-02 | 2022-04-12 |
| `MCI50P` | other (denominator only) | 2016-09-15 | 2017-10-31 |
| `MCI57` | other (denominator only) | 2021-03-23 | 2021-06-04 |
| `MCI59` | other (denominator only) | 2016-09-12 | 2024-12-25 |
| `MCI59P` | other (denominator only) | 2014-12-18 | 2017-11-13 |
| `MCI76` | other (denominator only) | 2017-02-17 | 2024-12-30 |
| `MCI77` | other (denominator only) | 2017-02-07 | 2024-12-31 |
| `MCI80` | other (denominator only) | 2016-05-29 | 2024-12-19 |
| `MCI80P` | other (denominator only) | 2014-12-05 | 2017-12-17 |
| `MEDRFC` | other (denominator only) | 2015-07-19 | 2023-07-19 |
| `MEDRRF` | other (denominator only) | 2022-06-08 | 2023-03-30 |
| `MEDRXN` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `MEDVAC` | other (denominator only) | 2014-12-21 | 2024-12-31 |
| `MVA` | other (denominator only) | 2014-12-03 | 2024-12-28 |
| `MVAINM` | other (denominator only) | 2019-04-20 | 2022-08-04 |
| `MVAINS` | other (denominator only) | 2021-07-09 | 2021-07-09 |
| `OBCOMP` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `OBLAB` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `OBMAJ` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `OBMIS` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `OBOUT` | other (denominator only) | 2014-12-02 | 2024-12-29 |
| `OTHER` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `PD13` | other (denominator only) | 2014-12-04 | 2024-12-31 |
| `PD13C` | other (denominator only) | 2014-12-10 | 2024-12-31 |
| `PEDFC` | other (denominator only) | 2014-12-03 | 2024-08-20 |
| `PEDFT` | other (denominator only) | 2021-03-20 | 2022-12-05 |
| `PEDRF` | other (denominator only) | 2014-12-09 | 2023-05-31 |
| `PEDSTR` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `PEDSTS` | other (denominator only) | 2024-02-06 | 2024-02-06 |
| `RAPE` | other (denominator only) | 2014-12-01 | 2017-09-17 |
| `RESPFC` | other (denominator only) | 2014-12-01 | 2024-06-06 |
| `RESPFT` | other (denominator only) | 2021-07-13 | 2023-01-23 |
| `RESPIR` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `RESPRF` | other (denominator only) | 2020-04-05 | 2023-03-06 |
| `SAFE` | other (denominator only) | 2017-09-12 | 2024-12-31 |
| `SEIZFC` | other (denominator only) | 2015-01-15 | 2023-12-15 |
| `SEIZFT` | other (denominator only) | 2023-08-09 | 2023-08-09 |
| `SEIZR` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `SEIZRF` | other (denominator only) | 2021-12-20 | 2023-03-20 |
| `SHOT` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `SICK` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `SICKFC` | other (denominator only) | 2014-12-01 | 2024-12-28 |
| `SICKFT` | other (denominator only) | 2015-04-28 | 2024-12-04 |
| `SICKRF` | other (denominator only) | 2014-12-03 | 2024-06-12 |
| `SICMFC` | other (denominator only) | 2020-01-31 | 2024-03-26 |
| `SICMFT` | other (denominator only) | 2022-10-31 | 2022-10-31 |
| `SICMIN` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `SICMRF` | other (denominator only) | 2022-06-09 | 2023-03-30 |
| `SICPED` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `STAB` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `STATEP` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `STATFC` | other (denominator only) | 2014-12-01 | 2024-03-21 |
| `STATFT` | other (denominator only) | 2022-11-24 | 2022-11-24 |
| `STATRF` | other (denominator only) | 2022-06-08 | 2023-03-24 |
| `STNDBM` | other (denominator only) | 2020-06-19 | 2024-12-30 |
| `STRANS` | other (denominator only) | 2015-02-23 | 2023-07-10 |
| `T-ABDP` | other (denominator only) | 2020-06-17 | 2024-12-26 |
| `T-ACTV` | other (denominator only) | 2022-02-03 | 2024-05-01 |
| `T-ALTM` | other (denominator only) | 2020-09-13 | 2024-12-29 |
| `T-ARST` | other (denominator only) | 2020-06-03 | 2024-12-29 |
| `T-ASTH` | other (denominator only) | 2020-11-02 | 2024-11-01 |
| `T-CARD` | other (denominator only) | 2020-09-01 | 2024-12-31 |
| `T-CDBR` | other (denominator only) | 2020-12-15 | 2024-11-20 |
| `T-CVAC` | other (denominator only) | 2020-11-19 | 2024-11-15 |
| `T-DFBR` | other (denominator only) | 2020-06-14 | 2024-12-31 |
| `T-INBL` | other (denominator only) | 2020-06-11 | 2024-09-19 |
| `T-INJ` | other (denominator only) | 2020-06-11 | 2024-12-31 |
| `T-MVAI` | other (denominator only) | 2020-08-24 | 2024-10-14 |
| `T-OBST` | other (denominator only) | 2020-10-06 | 2024-12-29 |
| `T-OTHR` | other (denominator only) | 2020-07-03 | 2024-08-17 |
| `T-SHOT` | other (denominator only) | 2022-01-12 | 2024-12-30 |
| `T-SICK` | other (denominator only) | 2020-06-09 | 2024-12-31 |
| `T-STAB` | other (denominator only) | 2022-01-09 | 2024-12-28 |
| `T-STEP` | other (denominator only) | 2020-09-30 | 2024-12-23 |
| `T-TEXT` | other (denominator only) | 2020-06-02 | 2024-12-31 |
| `T-TRMA` | other (denominator only) | 2020-06-05 | 2024-12-30 |
| `T-UNC` | other (denominator only) | 2020-06-22 | 2024-12-31 |
| `T-UNKN` | other (denominator only) | 2020-06-12 | 2024-12-27 |
| `TRAUMS` | other (denominator only) | 2024-08-18 | 2024-08-18 |
| `UNC` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `UNCFC` | other (denominator only) | 2014-12-03 | 2024-03-10 |
| `UNCFT` | other (denominator only) | 2014-12-23 | 2024-03-17 |
| `UNCRF` | other (denominator only) | 2016-10-30 | 2023-03-27 |
| `UNKNOW` | other (denominator only) | 2014-12-01 | 2024-12-31 |
| `VENOM` | other (denominator only) | 2014-12-10 | 2024-12-11 |
| `DRUG` | overdose / poison / drug | 2014-12-01 | 2024-12-31 |
| `DRUGFC` | overdose / poison / drug | 2015-05-19 | 2024-01-03 |
| `JUMPDN` | suicide-related (narrow MH) | 2014-12-01 | 2024-12-31 |
| `JUMPUP` | suicide-related (narrow MH) | 2014-12-01 | 2024-12-31 |

**Table S8 — The precinct–district crosswalk that carries B-HEARD exposure onto community districts (RECORD 12.3).** Built from the dispatch data's own precinct and community-district fields (a count of dispatches per precinct × district over 2015–2024; freeze incident F4); the concentration statistics say how cleanly a precinct maps to one district. Source: `data/reference/precinct_cd_crosswalk.csv` (`16_bheard_exposure.py`).

| statistic | value |
|---|---|
| precincts in the crosswalk | 77 |
| precinct × district pairs | 131 |
| median share of a precinct's dispatches in its modal district | 1.000 |
| minimum share in the modal district | 0.488 |
| precincts with at least 0.90 of dispatches in the modal district | 67 |

**Table S9 — The null-calibration certificates that precede every randomization p-value.** Synthetic panels with no effect, carrying the dependence measured on the discovery rows, on each stratum's own episode geometry and draw scheme; the empirical rejection rate at α = 0.05 must lie inside its binomial band and the p-values must be uniform on the exact lattice (Kolmogorov–Smirnov with a simulated null). Sources: `outputs/tables/null_calibration_*.csv` (`18_null_calibration.py`, regenerated by `ops/calib1000.sh`; hashes pinned in the sealed run's sidecar).

| stratum | draw scheme | episodes | simulations | rejection rate at α = 0.05 | KS p (uniformity) | verdict |
|---|---|---|---|---|---|---|
| discovery | anchor_shift | 29 | 1,000 | 0.045 | 0.2944 | CALIBRATED |
| C1 | circular_within_block_fw7 | 15 | 1,000 | 0.049 | 0.9930 | CALIBRATED |
| C2 | anchor_shift | 30 | 1,000 | 0.054 | 0.8221 | CALIBRATED |
| pooled | circular_within_block_fw7 | 45 | 200 | 0.040 | 0.5492 | CALIBRATED |

**Table S10 — The pre-freeze power table (EDP share only): the minimum detectable effect at 80% power for a sustained first-week shift and for a dip-and-rebound, against the declared minimum effect of interest of −0.005.** Source: `data/reference/power_analysis_prefreeze.csv` (`19_power.py`, computed before the lift; `freeze_active=1`). The MDE is measured against the asymptotic joint-Wald test at nominal α; the plan's addendum 23.11–23.12 states the bound's limitations.

| stratum | MDE, sustained shift | MDE, dip-and-rebound | MDE ÷ minimum effect of interest | verdict |
|---|---|---|---|---|
| discovery | 0.00950 | 0.00291 | 1.901 | UNDERPOWERED |
| C1 | 0.01156 | 0.00382 | 2.312 | UNDERPOWERED |
| C2 | 0.00875 | 0.00290 | 1.750 | UNDERPOWERED |
<!-- END:supp_tables -->

**Linkage flow (RECORD 6.3).** (1) Each dispatch record carries an incident timestamp, a final call type, a
disposition, a community district and a police precinct. (2) Records failing the disposition filter (S1.2) are
excluded. (3) The remaining records are counted by community district, day and call type, and call types are
mapped to families (Table S7); the district-day panel holds each family's count, its share of the district-day's
dispatches, and the total. (4) Separately, dispatches are counted by precinct × community district over the whole
period to form the crosswalk of Table S8, which converts each precinct's B-HEARD adoption bound into a
district-level exposure share by date. (5) The attention index is joined to the panel by calendar date; no
record-level linkage to any external dataset occurs.

---

## S5. Supplementary figures

- **Figure S1.** The sealed run's day-by-day first-week coefficients for the narrow mental-health outcome, both
  arms, C1 and C2 (the EDP outcome is Figure 1 of the paper). `docs/figures/fig6b_conf_paths_mh.png`.
- **Figure S2.** Impulse response of the narrow mental-health share to the continuous attention index (effect per
  standard deviation) by relative day, leads shown as a pre-trend check, 95% intervals (distributed-lag
  specification, exploratory; discovery period). `docs/figures/fig2_irf_primary.png`.
- **Figure S3.** The same share by three-day awareness window, each window entered alone and all jointly.
  `docs/figures/fig3_windows.png`.
- **Figure S4.** Outcome decomposition: the days 3–5 window's coefficient for each of seven dispatch shares with
  all five windows entered jointly, falsification outcomes in grey (discovery period).
  `docs/figures/fig4_decomposition.png`.
- **Figure S5.** The z-scoring simulation: within-sample standardisation multiplies a planted coefficient by the
  within-sample standard deviation of the regressor. `docs/figures/zscore_simulation.png`.
- **Figure S6.** Daily citywide narrow mental-health dispatch share with the attention index beneath over the
  discovery period (2017–2020), attention episodes shaded and the COVID emergency marked.
  `docs/figures/fig1_raw_series.png`.

---

## S6. The record

`docs/CONFIRMATION_PLAN.md` (frozen text; addendum §1–§30; summary table of deviations with a blindness column),
`docs/PRE_ANALYSIS_NOTE.md` (hypotheses, the interpretation table §9.4, the ledger of what is and is not
pre-specified), `docs/PAPER_MASTER.md` (the source document, including §5.3 on the incidents and §8b on the sealed
result), `docs/AUDIT_FINDINGS.csv` (every audit finding with the check that holds its fix), `docs/CLAIMS_REGISTER.csv`
(every result number), `docs/regression_baseline.csv` (the gate), `data/reference/freeze_access_log.csv` (declared
accesses), `data/reference/confirmatory_run_log.csv` (every start and the seal). All at
`https://github.com/abrahimmahmud/ems-police-awareness`, branch `analysis-rework`.
