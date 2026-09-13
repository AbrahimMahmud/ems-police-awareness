# Public attention to police violence and emergency help-seeking in New York City, 2015–2024

*Manuscript draft. Drafting order (PAPER_PLAN.md): Methods → RECORD → Introduction →
Limitations → Results → Discussion → Abstract. Sections marked* **[PHASE I PENDING]**
*are written after the sealed confirmatory run and are empty until then. Every number
in this document is a claim in `docs/CLAIMS_REGISTER.csv` that recomputes from a
committed artifact; a number without a claim is a check failure, not a typo.*

*Target: Journal of Urban Health, Template A (public health). ~4,000 words main
text, four display items, RECORD reporting. Language rules: PAPER_PLAN.md §7.*

---

## Abstract **[PHASE I PENDING]**

*≤250 words, unstructured. Must name: NYC EMS Incident Dispatch Data, New York City,
2015–2024, linkage of dispatch records to community districts and to a publicly
reconstructible attention index; the design ("stacked episode event study",
"quasi-experimental"); the three-way question. Written last.*

> Does public attention to police violence increase, decrease, or leave unchanged
> what New York City communities ask emergency medical services for?

---

## Introduction

Policing is increasingly treated as a structural determinant of health: a set of
institutional practices whose reach extends past the people directly stopped,
arrested or killed to the communities that watch, read and hear about them. A body
of population research links exposure to police violence with worse self-reported
mental health, higher psychological distress and higher psychiatric service use,
concentrated among Black Americans and in the neighbourhoods policed most
intensively.¹⁻⁴ The exposure in that literature is almost always an *incident* —
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
study measured it.

The closest quantified antecedent on the health side is Das and colleagues, who
found depression-related emergency department visits among African Americans
rose by about 11% in the month of a police killing of an unarmed African American
and the three months following, across 75 counties.⁷ Their design, like every
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
sensitivity and interpretation rule was written down before any outcome value was
seen.

---

## Methods

### Study design and pre-registration

We conducted a quasi-experimental panel study — a stacked episode event study —
of New York City emergency medical dispatches by community district and day. The
decade was divided into a **discovery** period (1 January 2017 to 31 December
2020), used to build the pipeline and explore the data, and two **confirmation**
strata never used for any specification choice: **C1**, 1 July 2015 to 31 December
2016 together with 1 January to 31 May 2021 — the months free of both COVID-19
and the B-HEARD mental-health response programme — and **C2**, 1 June 2021 to
31 December 2024, in which B-HEARD was rolling out precinct by precinct. The
lower bound of C1 is a data constraint, not a choice: Wikimedia's pageview
interface begins on 1 July 2015.

The confirmation strata were protected by a code-level freeze: every analysis
script draws its sample through one guard function whose active window is derived
from a single flag, and a regression suite of automated checks (82 at the time of
writing) verifies that no script can read confirmation-period outcome values
without passing through it. The hypotheses, the estimator, the primary inference,
the calibration precondition, the sensitivity battery, the multiple-testing family
and the rules for reading every possible result were committed to the repository
in dated documents before the freeze was lifted (`docs/CONFIRMATION_PLAN.md`,
`docs/PRE_ANALYSIS_NOTE.md`); every deviation from the originally frozen text is
listed there and summarised below. Three occasions on which confirmation-period
outcome data were touched before the freeze lifted are disclosed in *Limitations*
and in the plan; none entered a model or a test of the hypothesis.

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
describe the setting and to classify districts for the pre-specified heterogeneity
analysis.

**B-HEARD adoption.** The precinct-by-precinct rollout dates of New York City's
Behavioral Health Emergency Assistance Response Division, which from 1 June 2021
diverts some mental-health 911 calls from a police response, compiled from
Mayor's Office announcements and validated against the Independent Budget Office's
2026 precinct-level report (31 precincts; adoption dates carried as an earliest
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
final call type falls in the *emotionally disturbed person* family (EDP, EDPC,
EDPM, EDPW, T-EDP) and divided by all dispatches. This **EDP share** is the
primary outcome. A **narrow mental-health share** adds altered-mental-status and
suicide-related codes. Because a share can move when its denominator does, every
outcome is also modelled as a **count**, with the district-day's total dispatches
as an offset. District-days with fewer than five dispatches are excluded from
share calculations. Falsification outcomes are the cardiac and asthma families,
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
calendar block (discovery, C2) the whole sequence is shifted by one uniformly
drawn anchor; where it is two blocks (C1) one circular shift is drawn within each
block so that the number of episodes per block is preserved on every draw. On a
single block the two schemes are identical. Formula-based clustered standard
errors are reported beside the randomization p-value and never instead of it,
because on these data they have proved anti-conservative.

**Calibration precondition.** Before any p-value is reported for a stratum, the
full estimator and randomization procedure is run on 200 synthetic panels built
to contain no effect but carrying the real panel's serial dependence, district
levels, day-of-week pattern and a citywide day shock, on that stratum's own
episode geometry and draw scheme. The stratum's p-values are reported only if
the empirical rejection rate at α = 0.05 lies inside its binomial band and the
p-values are uniform against the exact discrete lattice of (1 + *k*)/(1 + *n*)
by a Kolmogorov–Smirnov test with a simulated null. The confirmatory script
refuses to run without a current certificate for each stratum naming the scheme
it draws.

**Multiple testing.** The pre-specified primary family is two outcomes (EDP
share, narrow mental-health share) × two arms (share, count) × two strata (C1,
C2) = eight tests, controlled by Benjamini–Hochberg at *q* = 0.05. The pooled
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
the stratum, or the geocoding step at 1 January 2016 at which the share of
dispatches with no district fell by two thirds — a demonstration rather than a
correction, chosen over month-year fixed effects because it changes the sample
and not the estimator, so it stays comparable with the calibrated null.
Falsification: cardiac and asthma shares and counts in every stratum. A placebo
that rejects at a level comparable to the primary outcomes overrides them: the
primary result is then reported as not supporting the hypothesis whatever its own
p-value.

**Power and the reading of a non-rejection.** Before the freeze lifted, the
minimum detectable effect at 80% power was computed by simulation for each
stratum against a pre-declared minimum effect of interest of −0.005 in the
mental-health share (about 6% of the discovery-period mean), for two effect
shapes — a sustained level shift over the first week and a dip-and-rebound of
the same size. Every stratum is underpowered for the sustained shape (minimum
detectable effects of 1.75 to 2.47 times the minimum effect of interest) and
adequately powered for the transient shape. The reading of a non-rejection was
therefore fixed in advance: no effect detected; a sustained shift at or above
that stratum's minimum detectable effect is disfavoured; a sustained shift of
the minimum effect of interest is not excluded; a transient effect of that size
is disfavoured. Rejections are read by the pre-specified rules, which are
asymmetric across strata: a rejection in C1 alone is confirmation in the clean
stratum; a rejection in C2 alone is not confirmation, because B-HEARD moves the
outcome in the hypothesised direction.

**Exploratory analyses.** Discovery-period estimates, an outcome decomposition
across eight dispatch families and three post-episode windows (65 tests under a
Bonferroni threshold), heterogeneity by district racial composition, and a
distributed-lag specification are reported as exploratory and are not tests of
the hypothesis.

**Software and reproducibility.** Python 3.11 with pyfixest; every table and
figure regenerates from the committed repository by one driver script that
records a manifest (commit, input hashes, row counts). Every number in this
manuscript is registered as a claim that an automated check recomputes from its
artifact.

### Deviations from the frozen pre-registration

Disclosed in full, with dates and original wording, in `docs/CONFIRMATION_PLAN.md`.
The material ones: the episode construct changed from a regime rule to a shock
rule with a within-year threshold (blind to outcomes); the test window moved from
days 0–5 to days 0–7 when the estimator was rebuilt; the attention index lost its
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

### Discovery period (exploratory) **[numbers re-verify when the 500-draw estimator lands]**

*Sample, raw pattern, primary estimates, decomposition, heterogeneity,
sensitivities — in that order, no interpretation. Drafted from PAPER_MASTER.md
§8; every number below has a claim.*

The buffered discovery panel holds 89,857 district-days across the 59 community
districts. The mean EDP share is 0.0856 and the mean district-day carries 66.1
dispatches. Twenty-nine attention episodes begin inside the discovery window.

Stacked over those 29 episodes with day −1 as reference, the first-week
coefficient on the EDP share is −0.00123 (randomization *p* = 0.695, 500 draws)
and on the EDP count −0.01084 (*p* = 0.519); on the narrow mental-health share
−0.00103 (*p* = 0.880) and count −0.00615 (*p* = 0.826). Share and count arms
agree in sign in every case. The estimates move in the fourth decimal across the
14-, 28- and 60-day post windows. Read against the minimum effect of interest of
−0.005, the EDP share estimate is about a quarter of it.

Across the 65 outcome-by-window decomposition tests, under a Bonferroni threshold
of α = 0.000769, 2 survive and both are injury in days 0–2: injury share
(+0.00159, *p* = 0.00004) and log injury count (+0.01048, *p* = 0.00008); the
injury-share coefficient for days 12–14 (+0.00104, *p* = 0.00172) does not. No
mental-health outcome survives (smallest *p* 0.044); neither falsification
outcome survives (cardiac share *p* = 0.082 and asthma share *p* = 0.076 at
their strongest).

### Confirmatory strata **[PHASE I PENDING]**

*C1, C2, pooled; primary family with Benjamini–Hochberg; sensitivities; falsification;
B-HEARD interaction. Read by PRE_ANALYSIS_NOTE.md §9 and CONFIRMATION_PLAN.md §19.*

---

## Discussion **[PHASE I PENDING]**

*Five moves: (1) restatement opening with the design — daily resolution inside the
first week; a verifiable multi-source attention index replacing a non-reproducible
social-media measure; EMS activation as the help-seeking decision; a genuine
discovery/confirmation split with a frozen episode list; (2) mechanism; (3)
comparison to prior work including Ang et al. (comparable declines across
majority-White, -Black and -Hispanic neighbourhoods) and Packard et al.; (4)
Limitations below; (5) implications.*

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
   inside the discovery window; EDPM appeared on 3 June 2021; 20 outcome-group
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
   sample, not a census.
9. **The freeze was breached three times before it lifted,** each disclosed: two
   undeclared metadata reads during automated audits, one of which informed a
   specification decision about the EDPM code, and one record-level read of
   2015–16 coverage statistics made while refuting an audit finding. A fourth,
   declared and logged read of coverage — first and last dates per code and the
   yearly missing-district rate, no outcome value — produced the coverage
   sensitivities. None entered a model or a test of the hypothesis; their
   materiality is for the reader to judge and the record is complete.
10. **The episode construct and the test window changed after the original
    freeze**, while blind to outcomes; original wording is preserved and the
    frozen list is committed byte-identical.
11. **Generalisability.** New York City's density, its unified EMS system and the
    B-HEARD programme are distinctive; the estimates describe this city.

Where a limitation biases toward the null — the national index attenuates any
local response; the share arm is compositionally damped by injury — the estimates
likely understate the response they measure.

---

## Display items

1. **Figure 1.** Daily citywide mental-health dispatch share with the attention
   index beneath, attention episodes marked (solid), COVID emergency and B-HEARD
   launch dashed, discovery and confirmation periods shaded. `08_figures.py`.
2. **Figure 2.** Stacked event-study coefficients by relative day, reference day
   −1 dotted, null line drawn, 95% intervals; both primary outcomes.
3. **Figure 3.** Outcome decomposition forest plot across the eight dispatch
   families with falsification outcomes blocked visually — *carries the argument*.
4. **Table 1.** The episode list: start, end, peak, registry label, driver label
   with share, stratum, and the frozen-versus-adopted difference.

Supplement: randomization histograms per stratum; the calibration certificates;
the power table; the z-scoring simulation; the basket with every include/exclude
reason; the full dispatch-code list with years of validity (RECORD 7.1); the
linkage flow (RECORD 6.3); the crosswalk validation (RECORD 12.3); the
sensitivity grid; the audit register.

---

## RECORD reporting checklist (extension of STROBE for routinely collected health data)

| Checklist item | Requirement | Where addressed |
|---|---|---|
| RECORD 1.1–1.3 | Data type, database name, geography, timeframe, linkage in title and abstract | Title; Abstract (names NYC EMS Incident Dispatch Data, New York City, 2015–2024, linkage to community districts and to the attention index) |
| RECORD 6.1 | Codes/algorithms used to identify the population | Methods, *Outcome*: the EDP family and the narrow mental-health family, code by code |
| RECORD 6.2 | Validation of those codes | Kang, Lu & Pang (2026, *Psychiatric Services*) classify mental-health EMS calls on this dataset; we differ by disaggregating call families and by handling the mid-2018 EDPC recode explicitly |
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
13. Hölzl, Keusch, Sajons. [Google Trends reliability across 360 studies.] *Soc Sci Res*. 2025;126:103099.
14. Ang D. The effects of police violence on inner-city students. *Q J Econ*. 2021;136(1):115-168.
15. Legewie J, Fagan J. Aggressive policing and the educational performance of minority youth. *Am Sociol Rev*. 2019;84(2):220-247.
