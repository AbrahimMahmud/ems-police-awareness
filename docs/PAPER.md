# Public attention to police violence and emergency help-seeking in New York City, 2015–2024

*Manuscript draft. Drafting order (PAPER_PLAN.md): Methods → RECORD → Introduction →
Limitations → Results → Discussion → Abstract. The confirmatory Results, the
Discussion paragraphs that read them and the Abstract were written after the
sealed confirmatory run of 2026-09-21 (PAPER_MASTER.md §8b), from the reader's
sentences only. Every number in this document is a claim in
`docs/CLAIMS_REGISTER.csv` that recomputes from a committed artifact; a number
without a claim is a check failure, not a typo.*

*Target: Journal of Urban Health, Template A (public health). ~4,000 words main
text, four display items, RECORD reporting. Language rules: PAPER_PLAN.md §7.*

---

## Abstract

Publicised police violence is linked to worse mental health and fewer
police-related 911 calls; whether it changes mental-health help-seeking is
untested at daily resolution. We asked whether public attention to police
violence increases, decreases, or leaves unchanged what New York City communities
ask emergency medical services for. In the NYC EMS Incident Dispatch Data (New
York City, 2015–2024), each dispatch was linked to its community district and day
and to a publicly reconstructible attention index from Wikipedia pageviews and
Google searches. A quasi-experimental stacked episode event study took the share
and count of mental-health dispatches as outcomes, cardiac and asthma dispatches
as falsification outcomes, and randomization inference. After a freely examined
exploratory period (2017–2020), two confirmation strata, before and after the
B-HEARD programme, were held under a code-level freeze until every hypothesis,
estimator, sensitivity and reading rule was committed, then analysed once by a
sealed script and read mechanically. Both strata return the pre-specified null:
no primary cell rejects after correction, falsification outcomes are quiet, and a
sustained shift in the mental-health share at or above the pre-freeze minimum
detectable effect (0.01156 in the clean stratum, 0.00875 in the exposed one) is
disfavoured at 80% power, as is a transient dip-and-rebound of the minimum effect
of interest; a sustained shift of that minimum (−0.005) is not excluded. Fourteen
of 24 clean-stratum sensitivity cells fall below unadjusted p = 0.05 and are
reported, not read as evidence. Within these bounds, attention to police violence
does not measurably change first-week mental-health help-seeking.

---

## Introduction

Policing is increasingly treated as a structural determinant of health: a set of
institutional practices whose reach extends past the people directly stopped,
arrested or killed to the communities that watch, read and hear about them. A body
of population research links exposure to police violence with worse self-reported
mental health, higher psychological distress and higher psychiatric service use,
concentrated among Black Americans and in the neighbourhoods policed most
intensively,¹⁻⁴ and with worse school outcomes for the young people who live
there.¹⁴ ¹⁵ The exposure in that literature is almost always an *incident* —
a killing in the respondent's state in the preceding months, a policing rate in the
respondent's neighbourhood — and the outcome is almost always measured after a
person has already sought care.

There is a second, less studied channel by which publicised police violence could
change health outcomes, and it runs through the decision to seek help at all. In
New York City a 911 call reporting a mental-health crisis dispatches an ambulance
and, for most of the study period, the police. When a police killing dominates the
news, a person deciding whether to call on behalf of a relative in crisis may weigh
the arrival of officers differently than they did the week before. Desmond,
Papachristos and Kirk documented exactly this kind of withdrawal after a single
publicised beating in Milwaukee, in police-related 911 calls, lasting more than a
year;⁵ Ang and colleagues found 911 call volume fell by roughly a quarter across
thirteen cities after the murder of George Floyd while gunshots detected by
acoustic sensors rose, and attributed the gap between that response and the
smaller responses to lower-profile killings to salience and media attention.⁶
Attention, not incidence, is the mechanism those results point at, and neither
study measured it. Attention has been measured on its own terms — Wikipedia
pageviews for earlier victims of police violence surged collectively after the
murder of George Floyd⁹ — but not, to our knowledge, carried to a health outcome
at the resolution of a day.

The closest quantified antecedent on the health side is Das and colleagues, who
found depression-related emergency department visits among African Americans
rose by about 11% in the month of a police killing of an unarmed African American
and the three months following, across 75 counties⁷ — a class of finding whose
sensitivity to how victims' armed status is coded has since been contested.⁸ Their
design, like every
administrative-outcome study we know of, works at the county-month. It therefore
cannot say whether the response peaks on the first day or the twentieth, whether
it is a sustained shift or a dip that rebounds, or whether what changed was
distress or the willingness to summon help — two forces that push the same
instrument in opposite directions.

This study addresses three gaps in that literature at once. First, the exposure
is *attention*, measured daily from what the public chose to look up — Wikipedia
pageviews of articles about people killed by police and Google searches about
police violence — rather than the occurrence of an incident, so that
anniversaries, verdicts and video releases count when they draw attention and
killings do not when they draw none. Second, the outcome is observed at the
community district and the day, roughly thirty times finer in time than the prior
work, so the shape of the response inside the first week is estimable. Third, the
outcome sits at the help-seeking decision itself — an emergency medical dispatch
coded as a mental-health crisis — rather than downstream of it, with dispatch
codes for conditions that should not respond to news (cardiac, asthma) as
falsification outcomes and injury calls as a marker of street activity.

We asked whether high-attention episodes increase, decrease or leave unchanged the
share of emergency medical dispatches coded as mental-health crises in the first
week after attention rises, in New York City's 59 community districts between
July 2015 and December 2024. The primary hypothesis, fixed before the confirmatory
sample was examined, predicted a decline; the test is two-sided, so a rise is a
rejection of the null in the direction opposite to prediction and is reported as
such. The design splits the decade into an exploratory period, examined freely,
and two sealed confirmatory periods on which every specification, hypothesis,
sensitivity and interpretation rule was written down before any confirmation-period
outcome value was seen — with the exceptions the record numbers and this paper
discloses: the second primary outcome and the joint first-week statistic were
adopted after discovery results had been seen, and one code in the primary
outcome's family was retained on the strength of confirmation-period counts read
in a disclosed breach of the freeze (Methods, Limitations).

---

## Methods

### Study design and pre-registration

We conducted a quasi-experimental panel study — a stacked episode event study —
of New York City emergency medical dispatches by community district and day. The
decade was divided into a **discovery** period (1 January 2017 to 31 December
2020), used to build the pipeline and explore the data, and two **confirmation**
strata never used for any specification choice: **C1**, 1 July 2015 to 31 December
2016 together with 1 January to 31 May 2021 — every confirmation month before the
B-HEARD mental-health response programme launched; the 2015–16 block is also free
of COVID-19, the 2021 block is not — and **C2**, 1 June 2021 to 31 December 2024,
in which B-HEARD was rolling out precinct by precinct. The
lower bound of C1 is a data constraint, not a choice: Wikimedia's pageview
interface begins on 1 July 2015.

The confirmation strata were protected by a code-level freeze: every analysis
script draws its sample through one guard function whose active window is derived
from a single flag, and a regression suite of automated checks (90 at the time of
writing) verifies that no script can read confirmation-period outcome values
without passing through it. The hypotheses, the estimator, the primary inference,
the calibration precondition, the sensitivity battery, the multiple-testing family
and the rules for reading every possible result were committed to the repository
in dated documents before the freeze was lifted (`docs/CONFIRMATION_PLAN.md`,
`docs/PRE_ANALYSIS_NOTE.md`); every deviation from the originally frozen text is
listed there and summarised below. Five occasions on which confirmation-period
outcome data were touched — four before the freeze lifted and one in the gate run
that verified the lifted state — are disclosed in *Limitations* and in the plan.
Two of them shaped the analysis: the EDPM code's membership of the primary
outcome's family was retained on confirmation-period precinct counts read in one
of them, and the district weights behind the B-HEARD covariate were counted from
confirmation-period dispatches in another; one fitted the primary specification
on the confirmation sample once and printed only the largest difference between
two coefficient vectors. No test of the hypothesis was read from any of them.

### Setting

New York City is divided into 59 community districts, neighbourhood-scale
administrative areas used for planning and service delivery; they are the finest geography at which the dispatch data
carry a stable identifier across the decade and the unit at which demographic
composition is measured. Dispatches without a community district are retained in
citywide totals and excluded from district shares.

### Data sources

**Emergency medical dispatches.** The NYC EMS Incident Dispatch Data (Fire
Department of the City of New York, via NYC OpenData, dataset 76xm-jjuj) record
every emergency medical dispatch in the city with an incident timestamp, a
dispatcher-assigned final call type, a disposition and a community district.
We downloaded the complete set (29,978,154 records) through the open-data API in
seven-column pages and used dispatches from December 2014 to December 2024. The
extract, its page-level cache and its cryptographic hash are recorded in a
provenance register; the download is reproducible.

**Wikipedia pageviews.** Daily article-level pageviews for human readers
(`agent=user`) from the Wikimedia REST API, 1 July 2015 onward, for a basket of
articles about people killed by law enforcement in the United States (below).
Pageviews are recorded per title and are not carried across a page move, so every
historical title of each article was resolved through the MediaWiki redirects and
revisions interfaces and summed; without this step the attention to Alton
Sterling in the week of his killing, for example, was absent from the series.

**Google Trends.** United States daily search interest for the *police brutality*
topic, fetched in overlapping windows and stitched on the overlaps. Trends returns
a sample rescaled to each request window; the stitching diagnostics are committed.

**Demographics.** American Community Survey 2015–2019 five-year estimates by
community district (New York City Department of City Planning), used only to
describe the setting and to classify districts for an exploratory heterogeneity
analysis by racial composition (not pre-specified; its hypothesis was formed from
discovery results).

**B-HEARD adoption.** The precinct-by-precinct rollout dates of New York City's
Behavioral Health Emergency Assistance Response Division, which from 1 June 2021
diverts some mental-health 911 calls from a police response, compiled from
Mayor's Office announcements and validated against the Independent Budget Office's
2026 precinct-level report¹² (31 precincts; adoption dates carried as an earliest
and a latest bound because 17 of 31 rest on low-confidence evidence), mapped to
community districts through a crosswalk built from the dispatch data's own
precinct and district fields.

**Victim registry.** Mapping Police Violence, used only to label episodes and to
supply positive evidence that an article concerns a police killing; it is never a
gate on basket membership, because it omits several of the deaths most relevant
to the hypothesis (see *Limitations*).

### Measures

**Exposure: the attention index.** The daily attention index averages two
standardised components: the sum of pageviews across the article basket, and
national search interest in police brutality. Each component is log-transformed
and standardised once, on a fixed 2017–2019 reference window that contains no
George Floyd, and the average is re-standardised on the same window. The index
is never re-standardised inside an analysis sample; a simulation reported in the
supplement shows that within-sample standardisation multiplies a planted
coefficient by the within-sample standard deviation of the regressor, which
varies more than threefold across ordinary robustness samples. News coverage
(GDELT) is deliberately excluded from the index — it measures supply — and is
kept as a separate falsification series. The index has no city-local component;
the two candidates built for that role were rejected on measurement (one is
censored on a quarter to three quarters of days; the other cannot be made both
local and disjoint from the national basket), so the exposure is national
attention and is described as such throughout.

**The article basket.** Candidate articles were collected by walking Wikipedia's
category tree for people killed by law enforcement in the United States, resolving
redirects at the point of collection, and resolving each person's date and country
of death from Wikidata. Each article was then classified on public evidence — a
category naming law enforcement as the actor, the article's first sentence, or
membership in Mapping Police Violence — into *police violence*, *unestablished*,
or *anti-police* (violence against officers). The **strict** basket (109
articles), in which the evidence names law enforcement as the actor, is the
primary exposure; the **broad** basket (118 articles) adds the nine articles in
which no evidence establishes who acted, and is a pre-registered sensitivity.
Attention to violence against police is in neither, and the effect of that
exclusion on the index's highest day is reported. A third pre-registered
sensitivity series (**spliced**) adds Wikimedia's `automated` agent class,
introduced non-retroactively in April 2020, to the strict basket so that the
series is comparable across the decade; it is identical to the primary before
2020 by construction.

**Episodes.** An attention episode begins on the first day of a run of days on
which the index lies in the top 10% of its own calendar year, and ends when the
run ends. The within-year quantile keeps stringency constant across years; a fixed
threshold selected a share of days that varied several-fold from year to year. Each
episode carries two labels: the person in the victim registry whose death drew
most attention in the window, and — because attention is driven by verdicts,
video releases and anniversaries at least as often as by new killings — the
articles actually read during the window, ranked by share of basket pageviews.
An episode is a burst of attention, not a killing, and the manuscript never
describes it as the latter. The originally frozen episode rule was a *regime*
rule that produced a single episode covering the whole summer of 2020;
it was replaced by this *shock* rule while blind to every outcome, and the
change is disclosed as a deviation. The frozen list (70 episodes) is preserved
byte-identical in the repository; the adopted list holds 74 episodes in the
strict basket (29 in discovery, 15 in C1, 30 in C2) and 75 in the broad.

**Outcome.** For each community district and day we counted dispatches whose
final call type carries the *emotionally disturbed person* prefix (EDP, EDPC,
EDPE, EDPM, EDPT, EDPW, T-EDP) and divided by all dispatches. This **EDP share** is the
primary outcome. A **narrow mental-health share** adds altered-mental-status and
suicide-related codes. Because a share can move when its denominator does, every
outcome is also modelled as a **count**, with the district-day's total dispatches
as an offset. District-days with fewer than five dispatches are excluded from
the analysis sample in both arms. Falsification outcomes are the cardiac and asthma families,
which should not respond to news about policing; the injury family is reported
as a marker of street activity. Call-type codes are born and retired across the
decade (EDPC phases in during 2018; EDPM appears on 3 June 2021), and the full
code list with each code's first and last date is in the supplement.

**Covariates.** B-HEARD exposure — the share of a community district's
dispatches falling in precincts that had adopted the programme by that date,
under the earliest and the latest adoption bound — enters every specification.
It is identically zero before June 2021, is dropped as collinear, and leaves the
discovery and C1 estimates numerically unchanged, which an automated check
asserts. In C2 it is a covariate in the primary specification and, in a
pre-specified secondary specification, is interacted with the first-week effect.

### Statistical analysis

**Estimator.** For each episode we stacked the 14 days before and 14 days after
its start in every community district, assigning any district-day claimed by two
episode windows to the nearer episode so that no observation is used twice, and
fitted

*y* ~ *i*(relative day, reference = −1) + B-HEARD exposure | episode × district +
day of week,

by ordinary least squares for shares and by Poisson pseudo-maximum likelihood
with a log offset for counts, with standard errors clustered on the calendar
date, since treatment is citywide and assigned at the date. Day −1 remains in the
sample as the omitted level. The test statistic for the primary hypothesis is a
joint Wald test that the eight coefficients for days 0 to 7 are all zero; the
mean of those coefficients is reported as an effect size and is not the test. A
dip followed by a rebound — the shape the avoidance mechanism most plausibly
takes — averages to near zero and is invisible to a mean but not to the joint
test. Post-episode windows of 28 and 60 days are sensitivities.

**Primary inference.** The primary p-value is by episode-level randomization
inference: the episode start dates are relocated to placebo dates that preserve
the real episodes' spacing, the estimator is re-run, and the p-value is
(1 + *k*)/(1 + *n*) where *k* is the number of *n* = 2,000 placebo statistics at
least as large as the observed one. Where a stratum is a single contiguous
calendar block (discovery, C2) one anchor is drawn uniformly and the real
episodes' inter-episode gaps are laid down from it in a random order, so the
multiset of gaps — and with it the clustering — is preserved on every draw while
their sequence is not; where a stratum is two blocks (C1) one circular shift is
drawn within each block so that the number of episodes per block is preserved on
every draw. The two schemes are differently constructed nulls, each certified on
its own geometry. The asymptotic joint-Wald p-value is
reported beside the randomization p-value and never instead of it, because on
these data formula-based inference has proved anti-conservative. The run draws
exactly the pre-specified 2,000 placebos and writes its result to a tracked
file once.

**Calibration precondition.** Before any p-value is reported for a stratum, the
share-arm estimator (without the B-HEARD covariate) and the randomization
procedure are run, at 200 placebo draws per simulation, on 1,000 synthetic panels
(200 for the descriptive pooled sample) built to contain no effect but carrying
the serial dependence, district levels, day-of-week pattern and citywide day
shock measured on the discovery rows of the real panel, on that stratum's own
episode geometry and draw scheme — separately for C1, C2 and the pooled sample,
whose three-window geometry is its own null. The count arm, the narrow
mental-health outcome, the covariate and the sealed run's 2,000-draw resolution
are not separately certified; the plan states this as a limitation. The stratum's p-values are reported only if
the empirical rejection rate at α = 0.05 lies inside its binomial band and the
p-values are uniform against the exact discrete lattice of (1 + *k*)/(1 + *n*)
by a Kolmogorov–Smirnov test with a simulated null. The confirmatory script
refuses to run without a current certificate for each stratum naming the scheme
it draws. A stratum whose null fails calibration at 1,000 simulations is, by a
rule written before that verdict existed, estimated and reported with its
randomization p-values flagged uncertified and excluded from the family
decision; its primary inference is then the asymptotic p, labelled, and a
rejection on it cannot count as confirmation.

**Multiple testing.** The primary family — fixed before the freeze lifted, though
its second outcome and its joint statistic were adopted after discovery results
had been seen (Deviations) — is two outcomes (EDP share, narrow mental-health
share) × two arms (share, count) × two strata (C1, C2) = eight tests, controlled
by Benjamini–Hochberg at *q* = 0.05. The pooled
estimate (a re-description of the same eight), the sensitivities (robustness
readings of tests already in the family), the B-HEARD interaction (secondary,
asymptotic p-value only) and the falsification outcomes are outside the family,
each for the reason given in the plan; every result row carries its family
membership so that a reader can recompute the correction under a different
definition.

**Sensitivities and falsification, pre-specified.** (i) Dropping the July 2016
episode, which contains the killings of Alton Sterling and Philando Castile and
the Dallas attack on police officers; (ii) the broad basket; (iii) the spliced
Wikipedia series; (iv) the late B-HEARD bound; (v) coverage-clean estimates that
drop every episode whose window contains a dispatch code born or retired inside
a confirmation window, or the geocoding step at 1 January 2016 at which the share
of dispatches with no district fell by two thirds — a demonstration rather than a
correction, chosen over month-year fixed effects because it changes the sample
and not the estimator, so it stays comparable with the calibrated null — and (vi)
a geocoding-clean estimate that drops only the episodes containing that step;
(vii) the 28- and post window 60 dayss, whose placebo draws keep the certified
14-day geometry; (viii) the outcomes with cancelled and other never-sent
dispositions restored to numerator and denominator; (ix) EDP without the EDPM
code, the one code whose inclusion was decided on confirmation-period counts.
Every sensitivity runs on both arms. Robust means a rejection survives every
applicable sensitivity at unadjusted randomization *p* ≤ 0.05, fragile that it
survives none; the set is enumerated in the reader and held equal to what the
sealed run writes.
Falsification: cardiac and asthma shares and counts in every stratum; a placebo
cell with unadjusted randomization *p* ≤ 0.05 overrides every primary rejection
in its stratum, which is then reported as not supporting the hypothesis. Injury
is estimated and reported beside them but does not override, because the
exploratory decomposition found it responds to attention episodes. A
family cell *rejects* when its adjusted *p* is below 0.05; a stratum rejects on
an outcome when both arms reject with the same sign of the first-week mean, and
direction is that sign. Two diagnostic cells per stratum — the outcome's raw
count without an offset, and total dispatches — decide whether a share-arm
rejection is denominator-driven.

**Power and the reading of a non-rejection.** Before the freeze lifted, the
minimum detectable effect at 80% power was computed by simulation for each
stratum against a pre-declared minimum effect of interest of −0.005 in the
mental-health share (about 6% of the discovery-period mean), for two effect
shapes — a sustained level shift over the first week and a dip-and-rebound of
the same size. Every stratum is underpowered for the sustained shape (minimum
detectable effects of 1.75 to 2.31 times the minimum effect of interest) and
adequately powered for the transient shape. The reading of a non-rejection was
therefore fixed in advance: no effect detected; a sustained shift at or above
that stratum's minimum detectable effect is disfavoured; a sustained shift of
the minimum effect of interest is not excluded; a transient effect of that size
is disfavoured. Rejections are read by the pre-specified rules, which are
asymmetric across strata: a rejection in C1 alone is confirmation in the clean
stratum; a rejection in C2 alone is not confirmation, because B-HEARD moves the
outcome in the hypothesised direction. A stratum rejects on an outcome only when
both arms reject with the same sign; a share-arm rejection accompanied by a
movement in total dispatches but not in the raw count is denominator-driven; any
placebo rejection within a stratum voids its primary rejections, and a placebo
cell that produced no *p*-value is reported as an incomplete check rather than a
passed one. The pooled stratum is read descriptively (both arms at unadjusted
*p* ≤ 0.05 with the same sign) and overturns nothing; the two secondary arms are
read against the directions the plan fixes and never enter the conclusion. These
rules are implemented as code that reads only the sealed result table and the
tracked pre-freeze power table, seals its own output against the table it read,
and is held to its text by planted tables in the regression suite, so that no
judgement intervenes between the sealed numbers and the sentences reported
below; the sentences in the confirmatory Results are the reader's own, quoted
verbatim and each held to the reading file by a registered claim. The sealed run
keeps a tracked log of every start and seal, refuses to run without the fixed
hash seed the byte-reproducible pipeline requires, and writes each cell's
day-by-day coefficient path so a rejection without a consistent direction can be
shown without a second read. The run was started seven times before it sealed
(20 September 2026 09:29 to 21 September 03:24 UTC): once at the lift, once
after the container was suspended, and twice each — an automatic retry and a
hand relaunch with fewer workers — after the worker pool was killed by the
memory limit on the pooled stratum's cells. Each start is a dated row of the
run log with its reason; every cell resumed from a ledger keyed to its own
seed and design, so no number depends on the restarts.

**Exploratory analyses.** Discovery-period estimates and an outcome
decomposition across thirteen outcomes in four dispatch families and five
three-day windows (65 tests under a Bonferroni threshold) are reported as
exploratory and are not tests of the hypothesis. A heterogeneity analysis by
district racial composition, whose hypothesis was formed from discovery results,
and a distributed-lag specification of the continuous attention index were also
estimated on the discovery period; their tables are in the repository and, apart
from the impulse-response figure, they are not reported here.

**Software and reproducibility.** Python 3.11 with pyfixest; every table and
figure regenerates from the committed repository by one driver script that
records a manifest (commit, input hashes, row counts). Every number in this
manuscript is registered as a claim that an automated check recomputes from its
artifact.

### Deviations from the frozen pre-registration

Disclosed in full, with dates and original wording, in `docs/CONFIRMATION_PLAN.md`.
The material ones: the episode construct changed from a regime rule to a shock
rule with a within-year threshold (blind to outcomes); the frozen one-sided test
of the EDP share on days 0–5 became a two-sided joint statistic on days 0–7 with
a second primary outcome, the narrow mental-health share — both adopted after
discovery-period results had been seen and therefore not blind, which the plan
records and discounts (its §14); the stratification into C1 and C2, the eight-test
family, the both-arms rule and the B-HEARD covariate in every specification were
decided blind before the lift; the attention index lost its
Twitter component (undocumented collection, not reproducible) and its New York
Trends component (censored); the randomization null on C1 was redefined twice,
finally as a within-block circular shift, because the frozen scheme is undefined
on a two-block stratum; and the confirmation window's lower bound is 1 July 2015
rather than 1 January 2015 because Wikipedia pageviews begin there. The
hypothesis's direction, the primary inference, the 59 districts and date-level
clustering are unchanged.

### Ethics

The dispatch data are public and contain no personal identifiers. **[Written
MIT COUHES non-human-subjects determination: pending — Abrahim.]**

---

## Results

### Discovery period (exploratory)

*Sample, raw pattern, primary estimates, decomposition, heterogeneity,
sensitivities — in that order, no interpretation. Drafted from PAPER_MASTER.md
§8; every number below has a claim.*

The panel holds 217,356 district-days across the 59 community districts from
December 2014 to December 2024; the discovery analysis window holds 86,199 of
them. In that window the mean EDP share is 0.0856 and the mean district-day
carries 66.1 dispatches. Twenty-nine attention episodes begin inside the discovery window.

Stacked over those 29 episodes with day −1 as reference, the first-week
coefficient on the EDP share is −0.00123 (randomization *p* = 0.697, 2,000 draws)
and on the EDP count −0.01084 (*p* = 0.527); on the narrow mental-health share
−0.00103 (*p* = 0.886) and count −0.00615 (*p* = 0.822). Share and count arms
agree in sign in every case. The estimates move in the fourth decimal across the
14-, 28- and post window 60 dayss. Read against the minimum effect of interest of
−0.005, the EDP share estimate is about a quarter of it.

Across the 65 outcome-by-window decomposition tests, under a Bonferroni threshold
of α = 0.000769, 2 survive and both are injury in days 0–2: injury share
(+0.00159, *p* = 0.00004) and log injury count (+0.01048, *p* = 0.00008); the
injury-share coefficient for days 12–14 (+0.00104, *p* = 0.00172) does not. No
mental-health outcome survives (smallest *p* 0.044); neither falsification
outcome survives (cardiac share *p* = 0.082 and asthma share *p* = 0.076 at
their strongest).

### Confirmatory strata

**Confirmatory strata.** The sealed run (`30_confirmatory_run.py`) wrote its table once; the pre-registered reading (`34_confirmatory_reading.py`; CONFIRMATION_PLAN addendum §23, §19 rule 2, §25, 23.1c–e; PRE_ANALYSIS_NOTE §9) is a function of that table and the pre-freeze power table, and its sentences are quoted here as it wrote them.

*C1, the clean stratum.* Primary family (23.1–23.4), C1: “does not reject”. Against the pre-freeze power (§19 rule 2), C1: “no effect detected at the family level (smallest unadjusted randomization p among the stratum's primary cells 0.0115); a sustained level shift at or above the pre-freeze MDE 0.01156 in absolute value (about 0.01480 under the approximate one-parameter family correction of 23.11) is disfavoured at 80% power; a sustained shift of the minimum effect of interest (−0.005) is not excluded; a transient dip-and-rebound of the minimum effect of interest is disfavoured (its pre-freeze MDE is 0.00382, at or below 0.005 in absolute value)”. Sensitivities (§9.5, 23.1c), C1: “primary does not reject; 14 of 24 H1-outcome sensitivity cells at p <= 0.05 (reported, not substituted)”. Falsification outcomes (23.4), C1: “no cardiac or asthma cell at p <= 0.05 (4 of 4 override cells with a p-value)”.

*C2, the B-HEARD-exposed stratum.* Primary family (23.1–23.4), C2: “does not reject”. Against the pre-freeze power (§19 rule 2), C2: “no effect detected at the family level (smallest unadjusted randomization p among the stratum's primary cells 0.4523); a sustained level shift at or above the pre-freeze MDE 0.00875 in absolute value (about 0.01120 under the approximate one-parameter family correction of 23.11) is disfavoured at 80% power; a sustained shift of the minimum effect of interest (−0.005) is not excluded; a transient dip-and-rebound of the minimum effect of interest is disfavoured (its pre-freeze MDE is 0.00290, at or below 0.005 in absolute value)”. Sensitivities (§9.5, 23.1c), C2: “primary does not reject; 0 of 30 H1-outcome sensitivity cells at p <= 0.05”. Falsification outcomes (23.4), C2: “no cardiac or asthma cell at p <= 0.05 (4 of 4 override cells with a p-value)”.

*Pooled (descriptive, 23.1d).* “pooled does not reject on both arms (descriptive)”.

*Secondary arms (23.1e; asymptotic p, outside the family).* C1 dose-response (per SD of peak intensity), EDP share (share, per SD intensity): “moves against the predicted direction (asymptotic p = 0.0309; coef +0.001309)”; C1 dose-response (per SD of peak intensity), narrow MH share (share, per SD intensity): “moves against the predicted direction (asymptotic p = 0.0187; coef +0.001508)”; C2 dose-response (per SD of peak intensity), EDP share (share, per SD intensity): “no movement (asymptotic p = 0.2412 > 0.05)”; C2 dose-response (per SD of peak intensity), narrow MH share (share, per SD intensity): “no movement (asymptotic p = 0.1820 > 0.05)”; C2 B-HEARD interaction, EDP share (share): “no movement (asymptotic p = 0.7732 > 0.05)”; C2 B-HEARD interaction, EDP count (count): “no movement (asymptotic p = 0.8496 > 0.05)”; C2 B-HEARD interaction, narrow MH share (share): “no movement (asymptotic p = 0.9761 > 0.05)”; C2 B-HEARD interaction, narrow MH count (count): “no movement (asymptotic p = 0.8933 > 0.05)”.

**Conclusion under note §9.4 as amended by addendum 23:** “THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2”.

**Table 2 — The pre-specified primary family: two outcomes × two arms × two strata.** First-week mean coefficient with its date-clustered SE, the joint Wald statistic on days 0–7, the randomization p at 2,000 draws, the Benjamini–Hochberg-adjusted p over the family of eight, and the asymptotic p beside it.

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

**Table 3 — The pre-registered reading, applied by code (addendum §23, §19 rule 2, §25).**

| stratum | null certified | stratum rejects | placebo rejects | pre-freeze MDE, sustained | × family correction | pre-freeze MDE, transient |
|---|---|---|---|---|---|---|
| C1 | 1 | 0 | 0 | 0.01156 | 0.01480 | 0.00382 |
| C1 reading | does not reject | | | | | |
| C2 | 1 | 0 | 0 | 0.00875 | 0.01120 | 0.00290 |
| C2 reading | does not reject | | | | | |

*Conclusion under note §9.4 as amended: THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2*

**Table 4 — Falsification outcomes and the denominator diagnostic, per stratum (unadjusted randomization p; addendum §23.3–23.4).** Cardiac and asthma cells at p ≤ 0.05 override the stratum's primary rejections; injury is reported but does not override (§23.4); the no-offset counts are the denominator diagnostic (§23.3).

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

**Table 5 — Pre-registered sensitivities, reported beside the primary and never substituted for it (note §9.5).** IDENTICAL means the arm's episode starts in that stratum equal the primary's, so no second p-value is printed (addendum §23.6).

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

**Table 6 — The pooled stratum (descriptive, outside the family) and the two secondary arms, the B-HEARD interaction (C2) and the dose-response arm (asymptotic p only; note §10, addendum §9).**

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

---

## Discussion

This study asked a narrow question with an unusually strict design: whether the
share of New York City emergency medical dispatches coded as mental-health crises
moves in the week after public attention to police violence rises. Three features
distinguish it from the prior literature. The exposure is attention itself,
measured daily from what the public looked up, so that verdicts, anniversaries
and video releases count when they draw attention and killings do not when they
draw none. The outcome sits at the help-seeking decision, observed by community
district and day — fine enough to see the shape of a response inside the first
week rather than a monthly average of it. And the inference is confirmatory in
the literal sense: the hypotheses, the estimator, the null the p-values rest on,
the sensitivities and the sentence to be written for every possible result were
committed before any confirmation-period outcome was seen, and the confirmatory
table was produced by one sealed script run once. The Results section reports the
pre-registered reading of that table verbatim; nothing in this section adds to
it or subtracts from it.

**What the reading says.** Neither stratum rejects the pre-registered null on
either primary outcome after the Benjamini–Hochberg correction over the family of
eight, and the reading in both is the bounded null of the plan's §19 rule 2: a
sustained level shift at or above the pre-freeze minimum detectable effect —
0.01156 of the share in C1, 0.00875 in C2 — is disfavoured at 80% power; a
sustained shift of the minimum effect of interest, −0.005, is not excluded; a
transient dip-and-rebound of that size is disfavoured, the design having been
powered for that shape (pre-freeze MDEs 0.00382 and 0.00290). The falsification
outcomes are quiet in both strata, so the null is not an artefact of a placebo
movement, and the pooled stratum does not reject on both arms. Two features of
the table are reported because the plan requires them to be reported and read
as no more than the plan allows. In C1 the smallest unadjusted randomization p
among the four primary cells is 0.0115, and 14 of the 24 sensitivity cells on
the primary outcomes lie at unadjusted p ≤ 0.05; the pre-registered rules do not
substitute an unadjusted p for the corrected family result, and this paper does
not either. The secondary dose-response arm in C1 moves against the predicted
direction — a larger, not smaller, first-week share per standard deviation of
episode intensity, at asymptotic p of 0.03 and 0.02 on the two outcomes —
outside the family and descriptive; in C2 neither the dose arm nor the B-HEARD
interaction moves. On the mechanism the study set out to test: the avoidance
account predicted a first-week decline in help-seeking; the confirmation strata
neither show it nor rule out a sustained decline of the size the study declared
it cares about, and they disfavour the transient dip-and-rebound the mechanism
work had made the most plausible shape.

**Relation to prior work.** The closest antecedents measured incidents rather
than attention and outcomes at the county-month or coarser. Das and colleagues
found depression-related emergency department visits among African Americans
rising by about 11% in the months around police killings of unarmed African
Americans;⁷ Desmond, Papachristos and Kirk documented a year-long fall in
police-related 911 calls in Milwaukee's Black neighbourhoods after one publicised
beating;⁵ Ang and colleagues found 911 call volume falling by roughly a quarter
across thirteen cities after the murder of George Floyd, with comparable declines
across majority-White, majority-Black and majority-Hispanic neighbourhoods, and
attributed the size of that response to salience.⁶ Outside policing, the use of crisis services after a publicised mass shooting
has been studied with a comparable event-study design.¹⁰ Our design speaks to the
same channel — whether publicised police violence changes the decision to summon
help — but at the day rather than the month, with the attention that those
authors invoke as the mechanism measured directly, and with dispatch codes that
should not respond to news (cardiac, asthma) carried as falsification outcomes
through every stratum. Two features of the setting matter for the comparison.
First, the outcome is a medical dispatch, not a police-related call: New York's
mental-health 911 calls dispatched an ambulance and, until B-HEARD, the police, so
an avoidance response would run through the anticipated presence of officers at
a medical call rather than through crime reporting. Second, the discovery period
contains the 2020 episodes on which the earlier evidence rests, and in it the
EDP share moved in the predicted direction after the murder of George Floyd while
the count did not — a compositional movement carried by a rise in injury calls
that the decomposition attributes to street activity rather than to withdrawal
from care, and that no mental-health outcome survives the corrected threshold
(Results). The confirmatory strata are the test of whether anything of that kind
holds outside the year the hypothesis was formed in.

**What the design cannot say.** The limitations below are ordered as a referee
would raise them. Two bear directly on how the confirmatory reading should be
carried into policy: the attention index is national, so the estimand is the
effect of national attention on New York help-seeking and not of New Yorkers'
own attention; and the confirmation strata hold few independent episodes, so a
non-rejection bounds a sustained shift at the pre-freeze minimum detectable
effect and no smaller, while a transient dip-and-rebound of the size the study
declared it cares about is the shape the design was powered for.

**Implications.** The design delivered the result it was built to deliver: a
bounded null, read by rules fixed before the confirmation outcomes were seen,
from a script run once. Within the bounds stated, the estimates do not support
the concern that publicised police violence suppresses calls for emergency
medical help in mental-health crises at the citywide scale in the week after
attention rises — nor the opposite — and the discovery-period injury pattern
remains exploratory. What would move the question is not more of the same
test. The attention measure is national, so New Yorkers' own attention is
unmeasured; the B-HEARD interaction, the one arm with district-level exposure
variation, showed no movement in C2; and the number of independent episodes in
each stratum is what bounds the power. The C1 sensitivity pattern and the
positive dose-response coefficients are hypotheses a later study could
pre-register, not findings of this one.

### Limitations

Ordered as a referee would raise them; each converted into what the estimate
remains valid for.

1. **The exposure is a national attention index with no local component.** Both
   local candidates were built and rejected on measurement. The estimand is
   therefore an intention-to-treat effect of national attention on New York City
   help-seeking; New Yorkers' own attention is not separately identified, and no
   sentence in this paper should be read as if it were.
2. **Few independent shocks; estimates imprecise.** The panel is large but the
   number of independent attention episodes is small (29 in discovery, 15 in the
   clean confirmation stratum, 30 in the exposed one). Randomization inference at
   the episode level is the appropriate reference distribution and is primary;
   formula-based standard errors have proved anti-conservative on these data.
   The design is underpowered against the pre-declared minimum effect for a
   sustained first-week shift in every stratum, and adequately powered for a
   transient dip-and-rebound; a non-rejection is a bounded null, with the bound
   stated, not an absence.
3. **Share outcomes are compositional.** A rise in injury dispatches mechanically
   depresses every other share. Counts with a total-dispatch offset are reported
   beside shares for every outcome, and a movement present in one arm only is
   reported as denominator-driven and not claimed as a change in demand.
4. **Dispatch-code drift** (RECORD 19.1). The EDPC code phased in during 2018,
   inside the discovery window; EDPM appeared on 3 June 2021; 22 outcome-group
   codes are born or retired inside the confirmation windows. Codes are grouped
   into families so that a recode within a family does not move the family; the
   coverage-clean sensitivities drop every episode whose window contains a break.
5. **B-HEARD** overlaps the whole of C2 and moves the outcome in the hypothesised
   direction, on adoption dates that are low-confidence for 17 of 31 precincts.
   Exposure is carried as bounds rather than a date, enters every specification,
   and the interpretation rules treat a C2-only rejection as not confirmation.
6. **A call type is a dispatcher's classification of a caller's account**, not a
   clinical diagnosis, and an EMS dispatch measures a decision to summon help,
   not underlying need. The injury signal in the discovery period is a dispatch
   code and cannot be separated from a change in coding during periods of
   heightened street activity.
7. **The victim registry omits events the study is about.** Mapping Police
   Violence lacks Daniel Prude, Sandra Bland and others whose deaths in custody
   or in crisis are the most on-hypothesis events in the decade; the basket is
   therefore not gated on registry membership, and the registry label of an
   episode is reported beside a label built from what was read.
8. **Measurement breaks in the exposure series.** Wikipedia pageviews begin on
   1 July 2015; the `agent=user` definition changed non-retroactively in April
   2020 with a shift that is negligible in discovery and material in 2021–2024,
   which the spliced sensitivity series addresses; Google Trends returns a
   sample, not a census, and its reliability across studies is itself contested.¹³
9. **The freeze was breached five times, four before it lifted and one at the
   lift,** each disclosed: two undeclared metadata reads during automated
   audits, one of which informed a specification decision about the EDPM code;
   one record-level read of 2015–16 coverage statistics made while refuting an
   audit finding; a precinct-to-district crosswalk counted over every year; and,
   in the gate run made to verify the lifted state before it was committed, three
   regression checks that had derived their sample from the freeze flag selected
   the confirmation sample once — one of them fitted the primary specification
   with and without the B-HEARD covariate on it and printed only the largest
   difference between the two coefficient vectors, the others a shared-days count
   and a residual autocorrelation. A separate, declared and logged read of
   coverage — first and last dates per code and the yearly missing-district rate,
   no outcome value — produced the coverage sensitivities. No test of the
   hypothesis was read from any of them and no number from them was kept; their
   materiality is for the reader to judge and the record is complete
   (`CONFIRMATION_PLAN.md` §15, `PAPER_MASTER.md` §5.3).
10. **The episode construct changed after the original freeze** while blind to
    outcomes; **the test window and the second primary outcome changed after
    discovery results had been seen** and are not blind — the plan marks them so
    and discounts them (its §14). Original wording is preserved and the frozen
    list is committed byte-identical.
11. **Generalisability.** New York City's density, its unified EMS system and the
    B-HEARD programme are distinctive; the estimates describe this city.

Where a limitation biases toward the null — the national index attenuates any
local response; the share arm is compositionally damped by injury — the estimates
likely understate the response they measure.

---

## Display items

1. **Figure 1.** Daily citywide narrow mental-health dispatch share with the
   attention index beneath over the discovery period (2017–2020), attention
   episodes shaded and the COVID emergency marked. `08_figures.py`; tracked copy
   `docs/figures/fig1_raw_series.png`.
2. **Figure 2.** Impulse response of the narrow mental-health share to the
   continuous attention index by relative day, leads shown as a pre-trend check,
   95% intervals (distributed-lag specification, exploratory; discovery period).
   `docs/figures/fig2_irf_primary.png`. `fig3_windows.png` shows the same share by
   three-day awareness window, each window entered alone and all jointly.
3. **Figure 3.** Outcome decomposition: the days 3–5 window's coefficient for
   each of seven dispatch shares, falsification outcomes in grey (discovery
   period, each outcome estimated separately). `docs/figures/fig4_decomposition.png`.
4. **Table 1.** The episode list: start, end, peak, registry label, driver label
   with share, stratum, and the frozen-versus-adopted difference. Generated from
   the two episode lists by `ops/paper_table1.py` as `docs/tables/TABLE1_episodes.md`
   and held to them by the regression suite, which re-renders it and requires
   identical bytes.

5. **Table 2.** The pre-specified primary family (two outcomes × two arms × two
   strata) from the sealed run. **Table 3.** The pre-registered reading applied by
   code. **Table 4.** Falsification outcomes and the denominator diagnostic.
   **Table 5.** Pre-registered sensitivities. **Table 6.** The pooled stratum and the
   two secondary arms. All five rendered from `data/reference/confirmatory_results.csv`
   and `confirmatory_reading.csv` by `ops/phase_i_tables.py`, every cell a registered claim.

Supplement: randomization histograms per stratum; the calibration certificates;
the power table; the z-scoring simulation (`docs/figures/zscore_simulation.png`); the basket with every include/exclude
reason; the full dispatch-code list with years of validity (RECORD 7.1); the
linkage flow (RECORD 6.3); the crosswalk validation (RECORD 12.3); the
sensitivity grid; the audit register.

---

## RECORD reporting checklist (extension of STROBE for routinely collected health data)

| Checklist item | Requirement | Where addressed |
|---|---|---|
| RECORD 1.1–1.3 | Data type, database name, geography, timeframe, linkage in title and abstract | Title; Abstract (names NYC EMS Incident Dispatch Data, New York City, 2015–2024, linkage to community districts and to the attention index) |
| RECORD 6.1 | Codes/algorithms used to identify the population | Methods, *Outcome*: the EDP family and the narrow mental-health family, code by code |
| RECORD 6.2 | Validation of those codes | No external validation of the dispatch codes exists yet: Kang, Lu & Pang (2026, *Psychiatric Services*)¹¹ work on the same dataset, and a comparison of their classification with ours (which disaggregates call families and handles the mid-2018 EDPC recode explicitly) is pending |
| RECORD 6.3 | Linkage flow | Supplement figure: dispatch → district; precinct → district crosswalk |
| RECORD 7.1 | Complete code list | Supplement table: every code, family, first and last date |
| RECORD 12.1 | Data cleaning | Methods, *Outcome*; disposition filter (finding O1) in the plan |
| RECORD 12.2 | Linkage description | Methods, *B-HEARD adoption* |
| RECORD 12.3 | Linkage quality | Supplement: crosswalk validation against the dispatch data's own precinct field |
| RECORD 13.1 | Selection of persons/units | The 59-district whitelist and the ≥5-dispatch rule, Methods |
| RECORD 19.1 | Changing eligibility over time | Limitations 4 (code drift), Methods *Outcome* |
| RECORD 22.1 | Access to protocol, data, code | The public repository: frozen pre-registration with git timestamps, provenance register with hashes, claims register, regression suite |

---

## References

1. Bor J, Venkataramani AS, Williams DR, Tsai AC. Police killings and their spillover effects on the mental health of black Americans: a population-based, quasi-experimental study. *Lancet*. 2018;392(10144):302-310.
2. Sewell AA, Jefferson KA. Collateral damage: the health effects of invasive police encounters in New York City. *J Urban Health*. 2016;93(Suppl 1):42-67.
3. Packard SE, Verzani Z, Finsaas MC, et al. Maintaining disorder: estimating the association between policing and psychiatric hospitalization among youth in New York City by neighborhood racial composition, 2006-2014. *Soc Psychiatry Psychiatr Epidemiol*. 2024;60(1):125-137.
4. Curtis DS, Washburn T, Lee H, et al. Highly public anti-Black violence is associated with poor mental health days for Black Americans. *Proc Natl Acad Sci USA*. 2021;118(17):e2019624118.
5. Desmond M, Papachristos AV, Kirk DS. Police violence and citizen crime reporting in the black community. *Am Sociol Rev*. 2016;81(5):857-876.
6. Ang D, Bencsik P, Bruhn JM, Derenoncourt E. *Community engagement with law enforcement after high-profile acts of police violence*. NBER Working Paper 32243; 2024.
7. Das A, Singh P, Kulkarni AK, Bruckner TA. Emergency Department visits for depression following police killings of unarmed African Americans. *Soc Sci Med*. 2020;269:113561.
8. Nix J, Lozada MJ. Police killings of unarmed Black Americans: a reassessment of community mental health spillover effects. *Police Pract Res*. 2021;22(3):1330-1339.
9. Wu HH, Gallagher RJ, Alshaabi T, et al. Say their names: resurgence in the collective attention toward Black victims of fatal police violence following the death of George Floyd. *PLoS One*. 2023;18(1):e0279225.
10. Weitzel KJ, Chew RF, Miller AB, Oppenheimer CW, Lowe A, Yaros A. The use of crisis services following the mass school shooting in Uvalde, Texas: quasi-experimental event study. *JMIR Public Health Surveill*. 2023;9:e42811.
11. Kang, Lu, Pang. An EMS-based crisis response model for mental health-related EMS calls: a quasi-experimental study. *Psychiatr Serv*. 2026. doi:10.1176/appi.ps.20250528.
12. New York City Independent Budget Office. *B-HEARD: a look at precinct level data*. 2026.
13. Hölzl, Keusch, Sajons. [Systematic review of Google Trends use across 360 studies; title to be confirmed against the source before submission.] *Soc Sci Res*. 2025;126:103099.
14. Ang D. The effects of police violence on inner-city students. *Q J Econ*. 2021;136(1):115-168.
15. Legewie J, Fagan J. Aggressive policing and the educational performance of minority youth. *Am Sociol Rev*. 2019;84(2):220-247.
