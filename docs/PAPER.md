# Public attention to police violence and emergency help-seeking in New York City, 2015–2024

Abrahim Mahmud

*Four display items (Tables 1–2, Figures 1–2). Supplementary Methods S1, the pre-registered reading S2, Tables
S1–S10 and Figures S1–S6 are in the Supplementary Material (`docs/SUPPLEMENT.md`). Data and code availability:
Methods.*

---

## Abstract
 Publicised police violence is linked to worse mental health and fewer police-related 911 calls; its effect on
mental-health help-seeking is untested at daily resolution. We asked whether national attention to police violence
increases, decreases or leaves unchanged what New York City communities ask emergency medical services for. In the NYC
EMS Incident Dispatch Data, 2015–2024, each dispatch was linked to community district, day and an attention index
built from Wikipedia pageviews and Google searches. A stacked episode event study with randomization inference took
the share and count of dispatches coded emotionally disturbed person (EDP) as outcomes and cardiac and asthma as
falsification outcomes. A discovery period (2017–2020) was explored freely; two confirmation periods, before and
during the rollout of the city's Behavioral Health Emergency Assistance Response Division (B-HEARD) programme, were
analysed once under a code-level freeze (five disclosed breaches) after every hypothesis, estimator and reading rule
was committed. Neither period rejected the pre-specified null after correction over eight tests. The first-week mean
change in EDP share was −0.00059 (95% CI −0.0032 to 0.0021) before B-HEARD and −0.00019 (−0.0024 to 0.0020) during it,
against a mean share of 0.086; falsification outcomes were quiet. The pre-registered reading disfavours a sustained
shift at or above the pre-freeze minimum detectable effect and a transient dip-and-rebound of the declared minimum
effect of interest (−0.005); it does not exclude a sustained shift of that minimum, though the estimated intervals do.
Within these bounds, no detectable first-week change in mental-health help-seeking followed a rise in national
attention.

---

## Introduction

Policing is increasingly treated as a structural determinant of health whose reach extends past the people directly
stopped, arrested or killed to the communities that watch, read and hear about them. Population research links
exposure to police violence with worse self-reported mental health, higher psychological distress and higher
psychiatric service use, concentrated among Black Americans and in the neighbourhoods policed most intensively,¹⁻⁴ and
with worse school outcomes for young people.¹⁴ ¹⁵ The field's most visible dispute has been over how exposure is
measured: the flagship estimate attenuates to non-significance when victims' armed status is recoded.¹ ⁸ The exposure
in that literature is almost always an *incident*, and the outcome is almost always measured after a person has
already sought care.

A second, less studied channel runs through the decision to seek help at all. In New York City a 911 call reporting a
mental-health crisis dispatches an ambulance and, for most of the study period, the police. When a police killing
dominates the news, a person deciding whether to call on behalf of a relative in crisis may weigh the arrival of
officers differently than they did the week before. Desmond, Papachristos and Kirk documented such a withdrawal in
police-related 911 calls after a publicised beating in Milwaukee;⁵ Ang and colleagues found 911 calls fell by roughly
a quarter across thirteen cities after the murder of George Floyd and attributed the size of the response to salience
and media attention.⁶ Attention, not incidence, is the mechanism those results point at, and neither study measured
it. The two channels run in opposite directions: publicised police violence raises distress and with it the demand for
care,⁴ ⁷ while the anticipated arrival of officers at a mental-health call cuts the other way.⁵ ⁶ We pre-specified a
decline because the call brought police as well as an ambulance; the test is two-sided because the opposite prediction
has comparable support.

On the health side, Das and colleagues found depression-related emergency department visits among African Americans
rose by about 11% in the four months from a police killing of an unarmed African American, across 75 counties.⁷ Their
design, like every administrative-outcome study we know of, works at the county-month, which cannot say whether a
response peaks on the first day or the twentieth, whether it is sustained or rebounds, or whether what changed was
distress or the willingness to summon help. On the exposure side the closest antecedent is Curtis and colleagues, who
timed poor mental-health days against 49 highly publicised acts of anti-Black violence chosen for their salience;⁴
their exposure is publicity rather than incidence, but it is a list of discrete events selected after the fact, with
no measure of how much attention each drew. Attention has been measured on its own terms⁹ but not, to our knowledge,
carried to a health outcome at the resolution of a day.

This study addresses three gaps. The exposure is a continuous daily index of national *attention*, rebuilt from what
the public chose to look up — Wikipedia pageviews of articles about people killed by police and Google searches about
police violence — in which episodes are defined by the index rather than by the analyst, so that anniversaries,
verdicts and video releases count when they draw attention and killings do not when they draw none. The outcome is
observed at the community district and the day, so the shape of the response inside the first week is estimable. And
the outcome sits at the help-seeking decision itself — an emergency medical dispatch coded as a mental-health crisis —
with codes for conditions that should not respond to news (cardiac, asthma) as falsification outcomes.

We asked whether high-attention episodes increase, decrease or leave unchanged the share of emergency medical
dispatches coded as mental-health crises in the first week after attention rises, in New York City's 59 community
districts between July 2015 and December 2024. The decade was split into a discovery period, explored freely, and two
confirmation periods on which every hypothesis, estimator, sensitivity and interpretation rule was committed in
advance; the deviations, including five breaches of the freeze, are set out in Methods and Limitations. The primary
hypothesis predicted a decline; the test is two-sided.

---

## Methods

### Study design and pre-registration

We conducted a quasi-experimental panel study — a stacked episode event study — of New York City emergency medical
dispatches by community district and day. The exposure is citywide: every district is exposed on the same day, so the
design carries no untreated comparison group. Identification is within episode and within district across a 29-day
window: each coefficient for days 0 to 7 is the district's day-of-week-adjusted change from the day before the episode
began, with the episode × district level absorbed, and the remaining pre-episode days carry their own coefficients.
Randomization inference over placebo episode dates supplies the null distribution, not a counterfactual. Cardiac and
asthma dispatches, which should not respond to news, therefore carry the burden an untreated group carries elsewhere,
and are part of the identification argument.

The decade was divided into a **discovery** period (1 January 2017 to 31 December 2020), explored freely, and two
**confirmation** periods (the strata of the pre-registration), protected by a code-level freeze whose five recorded
breaches — two of which left something in the analysis — are disclosed in Limitation 10 and in full in S1.1: **C1**, 1
July 2015 to 31 December 2016 together with 1 January to 31 May 2021 — every confirmation month before the B-HEARD
mental-health response programme launched; the 2021 block falls inside the pandemic — and **C2**, 1 June 2021 to 31
December 2024, in which B-HEARD was rolling out precinct by precinct. C1's lower bound is a data constraint:
Wikimedia's pageview interface begins on 1 July 2015. The freeze let no exploratory script read confirmation-period
outcome values and was enforced by a regression suite of automated checks; every hypothesis, estimator, inference rule
and reading rule was committed in dated documents before it was lifted. The pre-registration is internal (git
timestamps; no external deposit).

### Setting and data sources

New York City has 59 community districts, the finest geography at which the dispatch data carry a stable identifier
across the decade; dispatches without a district are retained in citywide totals and excluded from district shares.
The **NYC EMS Incident Dispatch Data** (Fire Department of the City of New York, via NYC OpenData, dataset 76xm-jjuj)
record every emergency medical dispatch with an incident timestamp, a dispatcher-assigned final call type, a
disposition and a community district; we downloaded the complete set (29,978,154 records) and used dispatches from
December 2014 to December 2024, with the extract's hash in a provenance register (S1.2). **Wikipedia pageviews** are
daily article-level views by human readers (Wikimedia REST API, 1 July 2015 onward); **Google Trends** is United
States daily search interest for the *police brutality* topic (S1.2). **B-HEARD adoption** dates by precinct were
compiled from Mayor's Office announcements and validated against the Independent Budget Office's 2026 precinct-level
report¹² (31 precincts; adoption dates carried as an earliest and a latest bound, Limitation 6), and mapped to
community districts through a crosswalk built from the dispatch data's own precinct and district fields (Table S8).
The **victim registry** (Mapping Police Violence) labels episodes and never gates basket membership.

### Measures

**Exposure.** The daily attention index averages two standardised components — the log of pageviews summed across the
article basket and the log of national search interest in police brutality — each standardised once on a fixed
2017–2019 reference window and never re-standardised inside an analysis sample (S1.3); it has no city-local component.
The **strict** basket (109 articles), in which public evidence names law enforcement as the actor in the person's
death, is the primary exposure; the **broad** basket (118 articles) adds the articles in which no evidence establishes
who acted, and a **spliced** series adds Wikimedia's automated-agent class from April 2020; both are pre-registered
sensitivities.

**Episodes.** An attention episode begins on the first day of a run of days on which the index lies in the top 10% of
its own calendar year, and ends when the run ends; it is a burst of attention, not a killing. The originally frozen
rule produced a single episode covering the whole summer of 2020 and was replaced by this shock rule while blind to
every outcome (Deviations). The adopted list holds 74 episodes in the strict basket (29 in discovery, 15 in C1, 30 in
C2) and 75 in the broad (Table S6; Figure 2).

**Outcome.** For each community district and day we counted dispatches whose final call type carries the Fire
Department's *emotionally disturbed person* prefix (EDP, EDPC, EDPE, EDPM, EDPT, EDPW, T-EDP; the agency's term,
retained because it names the codes) and divided by all dispatches sent and not cancelled or duplicated (S1.2, S1.5).
This **EDP share** is the primary outcome; a **narrow mental-health share** adds altered-mental-status and
suicide-related codes. Every outcome is also modelled as a **count**, by Poisson pseudo-maximum likelihood with the
district-day's total dispatches as a log offset: a rate on the same denominator, so a functional-form check rather
than an answer to the denominator, which the raw count without an offset addresses as a diagnostic (Table 2).
District-days with fewer than five dispatches are excluded. Falsification outcomes are the cardiac and asthma
families; injury is reported as a marker of street activity.

**Covariate.** B-HEARD exposure — the share of a district's dispatches in precincts that had adopted the programme by
that date, under either bound — enters every specification and, in C2, a secondary interaction with the first-week
effect.

### Statistical analysis

**Estimator.** For each episode we stacked the 14 days before and after its start in every district and fitted *y* ~
*i*(relative day, reference = −1) + B-HEARD exposure | episode × district + day of week, by ordinary least squares for
shares and Poisson pseudo-maximum likelihood with a log offset for counts, with standard errors clustered on the
calendar date. The test statistic is a joint Wald test that the eight coefficients for days 0 to 7 are all zero; the
mean of those coefficients is reported as an effect size and is not the test, because a dip that rebounds averages to
near zero (S1.6).

**Inference.** The primary p-value is by episode-level randomization inference at 2,000 placebo draws preserving the
real episodes' spacing — an anchor shift on a contiguous period (discovery, C2) and a circular within-block shift on
the two-block period C1 (S1.6) — with the asymptotic joint-Wald p reported beside it, never instead of it, because
formula-based inference has proved anti-conservative on these data. Randomization p-values are reported only for a
period whose null was certified on 1,000 synthetic no-effect panels (Table S9). The certificate covers the share-arm
estimator on the EDP share without the B-HEARD covariate, at 200 placebo draws per panel; the count arm, the narrow
mental-health outcome, the covariate and the sealed run's 2,000-draw resolution are not separately certified (S1.6).

**The family and what lies outside it.** The primary family — fixed before the freeze lifted, though its second
outcome and its joint statistic were adopted after discovery results had been seen (Deviations) — is two outcomes ×
two arms × two periods = eight tests, controlled by Benjamini–Hochberg at *q* = 0.05. A cell rejects when its adjusted
p is below 0.05; a period rejects on an outcome when both arms reject with the same sign of the first-week mean; and a
cardiac or asthma cell at unadjusted p ≤ 0.05 voids every rejection in its period. B-HEARD reduces mental-health EMS
call rates in adopting precincts¹¹ — the hypothesised direction — and, by removing police from mental-health calls,
attenuates the mechanism under test, so a rejection in C1 alone is confirmation and in C2 alone is not. Outside the
family sit the pooled estimate (descriptive); ten pre-specified sensitivities on both arms, reported beside the
primary and never substituted for it (Table S4; S1.7); the denominator diagnostics (raw counts without an offset,
total dispatches); and two secondary arms with asymptotic p only, the B-HEARD interaction (C2) and a dose-response arm
(first-week effect per standard deviation of peak episode intensity, predicted negative).

**Power and the reading of a non-rejection.** Before the freeze lifted, the minimum detectable effect at 80% power was
computed by simulation for each period against a pre-declared minimum effect of interest of −0.005 in the EDP share,
for a sustained first-week shift and for a dip-and-rebound of the same size (Table S10). Every period is underpowered
for the sustained shape and adequately powered for the transient one. Two mismatches separate the bound from the test
it bounds: it is computed at nominal α while the non-rejection is a corrected p, so the plan quotes an approximate
inflation beside it (the one-parameter factor 1.28 for α/8; 1.21 for the eight-df statistic; both upper bounds on a
Benjamini–Hochberg correction); and it is measured against the asymptotic test while the p-value is a randomization p,
recorded as a limitation rather than corrected (S1.8; Table S10 gives the randomization-based bound where the
pre-freeze table could compute it). The reading of a non-rejection was fixed in advance: no effect detected; a
sustained shift at or above the period's minimum detectable effect is disfavoured; a sustained shift of the minimum
effect of interest is not excluded; a transient effect of that size is disfavoured. The rules are code that takes only
the sealed result table and the pre-freeze power table as input; its verbatim output is S2.

**The sealed run.** The confirmatory script ran once after the lift at the pre-specified 2,000 draws per cell and
wrote its table with a sidecar pinning source hashes, inputs, commit and seed (restarts and byte-reproducibility:
S1.9).

**Exploratory analyses.** Discovery-period estimates and an outcome decomposition (65 outcome-by-window tests under a
Bonferroni threshold) are exploratory, not tests of the hypothesis (S1.10; Figures S2–S4).

### Deviations from the frozen pre-registration

Disclosed in full in the plan's numbered summary table. Three bear on interpretation: the episode construct (regime
rule → shock rule, replaced while blind to outcomes) and, adopted after discovery results had been seen and not blind,
the test window (days 0–5 → 0–7, joint) and the second primary outcome. The rest, including the five freeze incidents
(Limitation 10, S1.1) and two hypotheses not run (Limitation 12), are listed there.

### Ethics and data availability

The dispatch data are public and contain no personal identifiers; an institutional determination that the study is not
human-subjects research is pending. The dispatch data (NYC OpenData dataset 76xm-jjuj), Wikimedia pageviews and Google
Trends are public interfaces. Code, the frozen pre-registration, the provenance and claims registers, the regression
suite and the sealed confirmatory table with its run log are at https://github.com/abrahimmahmud/ems-police-awareness
(branch `analysis-rework`).

---

## Results

### Discovery period (exploratory)

The discovery-period estimates are exploratory and are reported in S1.10: over the 29 episodes beginning in that
window no mental-health outcome moves in the first week on either arm, and of the 65 outcome-by-window decomposition
tests only two rises in injury dispatches on days 0 to 2 survive a Bonferroni threshold; neither falsification outcome
does.

### Confirmation periods

**The family (Table 1).** Neither period rejects the pre-specified null on either primary outcome after the
Benjamini–Hochberg correction over the family of eight. In C1 the first-week mean change in the EDP share is −0.00059
(95% interval −0.0032 to 0.0021) and in the EDP count +0.00945 log points; the smallest unadjusted randomization p
among the four C1 cells is 0.0115, on the EDP share, whose adjusted p is 0.056, and the narrow mental-health share's
adjusted p is 0.076. In C2 the EDP share changes by −0.00019 (−0.0024 to 0.0020) and the smallest unadjusted
randomization p is 0.4523. The asymptotic joint-Wald p is below 0.05 in all four C1 cells (0.0010 to 0.0291) and
between 0.44 and 0.78 in C2; the family decision rests on the randomization p alone. Under a within-period family of
four rather than the pre-registered eight, C1's three smallest adjusted p-values would be 0.028, 0.028 and 0.038,
against 0.0895 for the narrow mental-health count. The null being certified and no falsification outcome rejecting,
the pre-registered rules read each non-rejection against the pre-freeze power: a sustained first-week shift in the EDP
share at or above the minimum detectable effect (0.01156 in C1 and 0.00875 in C2; 0.01480 and 0.01120 under the
approximate eight-test inflation) is disfavoured at 80% power, a sustained shift of the minimum effect of interest,
−0.005, is not excluded, and a transient dip-and-rebound of that size is disfavoured, the pre-freeze minimum
detectable effects for that shape being 0.00382 and 0.00290. The pre-specified conclusion is a bounded null in both
periods.

**The shape of the first week (Figure 1).** In C1 the eight EDP-share coefficients for days 0 to 7 are +0.0006,
+0.0028, +0.0012, −0.0025, +0.0003, −0.0032, −0.0017 and −0.0023: positive on days 0 to 2 and 4, negative on days 3
and 5 to 7, with no single day's interval excluding zero. The count arm has the same sign on seven of the eight days,
with day 1 at +0.0432 log points the only coefficient in either arm whose interval excludes zero, and averages
+0.00945. The one-degree-of-freedom Wald statistic for the first-week mean is 0.19 against the joint statistic of
25.32. In C2 both arms are flat within their intervals; the narrow mental-health outcome behaves similarly, though its
C1 share path opens below zero (Figure S1).

**Outside the family (Table 2).** Of C1's 24 sensitivity cells on the primary outcomes, 14 lie at unadjusted
randomization p ≤ 0.05 (range 0.0045 to 0.3573), while every share-arm first-week mean among them stays between
−0.00168 and −0.00036; of C2's 30, none does (p from 0.0565; Table 2). No cardiac, asthma or injury cell reaches p ≤
0.05 in either period, so the override rule had nothing to act on. Among the denominator diagnostics, C1's raw EDP
count without an offset has a first-week mean of −0.0118 log points (randomization p 0.0115) and total dispatches
−0.0158 (p 0.5422); in C2 the two are −0.0044 (p 0.3368) and −0.0100 (p 0.7481). The pooled sample, read
descriptively, does not reject on both arms. The secondary dose-response arm, with asymptotic p only, moves against
the predicted direction in C1 — +0.00131 in the EDP share per standard deviation of episode intensity (p 0.0309) and
+0.00151 in the narrow mental-health share (p 0.0187) — and does not move in C2 (Table 2); over the discovery period
it is −0.00017 (p 0.768). The B-HEARD interaction in C2 does not move on any outcome (asymptotic p from 0.7732 to
0.9761).

---

## Discussion

This study asked whether the share of New York City emergency medical dispatches coded as mental-health crises moves
in the week after national attention to police violence rises, with the inference confirmatory in the pre-registered
sense: hypotheses, estimator, null, sensitivities and the sentence to be written for every possible result were
committed before the freeze lifted (Limitation 10 describes the five incidents), and the confirmatory table was
produced by one sealed script run once and read by code.

**What the reading says.** Both periods return the pre-specified null: a sustained first-week shift in the EDP share
at or above the pre-freeze minimum detectable effect is disfavoured at 80% power, a sustained shift of the declared
minimum effect of interest, −0.005, is not excluded, and a transient dip-and-rebound of that size — the shape the
mechanism work had made most plausible, and the one the design was powered for — is disfavoured (Table 1B). The
falsification outcomes are quiet. That bound was fixed before the lift against the asymptotic joint test, which spends
eight degrees of freedom on what, for a sustained shift, is a one-parameter alternative. The estimates themselves are
more precise than the bound assumed: the first-week mean's interval on the EDP share is −0.0032 to 0.0021 in C1 and
−0.0024 to 0.0020 in C2, both excluding a sustained first-week decline of −0.005, as do the count arms (−0.005 on a
mean share of 0.086 is about −0.06 log points). Those intervals are normal approximations, not the pre-registered
inference, and this study's own calibration found asymptotic inference anti-conservative on these data (S1.6); the
pre-registered reading stands as the conclusion, and the intervals are reported as what the estimates on their own
bound.

**What C1 shows, and why it is not read as an effect.** Three unadjusted randomization p-values below 0.03 in C1 and
fourteen of twenty-four sensitivity cells below 0.05 invite the question whether a signal hides behind the correction.
The sensitivity cells re-estimate the same four primary cells on overlapping samples — one result seen many times, not
fourteen — and Figure 1 shows what that result is. The joint test responds in C1 to a sequence, not a level:
coefficients above zero early and below it later, with a reversal on day 4, none individually distinguishable from
zero in the share arm, and a first-week mean whose own one-degree-of-freedom statistic is under one per cent of the
joint statistic. The eight coefficients are strongly positively correlated (mean off-diagonal correlation 0.49 in the
pre-freeze noise model), which is why the joint p can be small while every marginal interval crosses zero. That
sequence is not the hypothesised decline; it is the transient shape the study was powered for with its sign reversed,
and the joint statistic's power does not depend on that sign. Two pre-registered guards stood between it and a
directional reading, neither strong: on the EDP outcome the arms' first-week means straddle zero (−0.00059 in the
share arm, +0.00945 log points in the count arm), so the same-sign rule would have blocked a direction even had the
correction been cleared; on the narrow mental-health outcome both arms are negative and what blocks it is the
both-arms rule, its count arm being at randomization p 0.0895 with a mean (−0.00013) 0.009 standard errors from zero,
so its sign carries no information. For the same reason the period-level reading would not change under a
within-period family of four (Results). Two further facts. The raw EDP count without an offset and total dispatches
both fell in C1's first week (−0.0118 and −0.0158 log points) and differ in precision rather than size; only the first
reaches randomization p ≤ 0.05, and the design cannot separate a mental-health-specific contraction from the slightly
larger general one it is too imprecise to detect. And the dose-response arm, outside the family with asymptotic p
only, moves against its prediction in C1, does not move in C2 and is small and negative over discovery; as a contrast
on the first-week mean it does not corroborate a within-week excursion. A rise then a fall is what two channels of
different latency would produce (distress first, avoidance after), and also what street activity around the same
episodes would produce — the signature the discovery-period decomposition found in injury dispatches; this design
separates none of them. Taken together these are a hypothesis a later study could pre-register — a short rise in
mental-health dispatches at the peak of national attention, subsiding within the week — and not a finding of this one.

**Relation to prior work.** The closest antecedents measured incidents rather than attention, and outcomes at the
county-month or coarser — the rise in depression-related emergency visits around police killings,⁷ the year-long fall
in police-related 911 calls after one publicised beating,⁵ the citywide fall in 911 calls after the murder of George
Floyd⁶ — with Curtis and colleagues closest on the exposure side, timing a self-reported outcome against publicised
events chosen for their salience;⁴ outside policing, crisis-service use after a publicised mass shooting has been
studied with a comparable event-study design.¹⁰ Our design speaks to the same channel at the day rather than the
month, with the attention those authors invoke measured directly. The outcome here is a medical dispatch, not a
police-related call, so avoidance would run through the anticipated presence of officers at a medical call; in C2 that
presence was being withdrawn by B-HEARD in adopting precincts,¹¹ which makes C2 the weaker test as well as the
confounded period. The discovery period contains the 2020 episodes on which the earlier evidence rests; there the
pooled estimate is a bounded null on every mental-health outcome and the only movements surviving the corrected
threshold are rises in injury dispatches in the first three days, consistent with street activity rather than
withdrawal from care. The effects this literature reports are concentrated in Black communities,¹ ³ ¹⁴ ¹⁵ and this
study's estimand is a citywide average (Limitation 2); the exploratory discovery-period split by district racial
composition does not discriminate between mechanisms (S1.10). Within its bounds — national attention, a citywide
average, few independent episodes — the primary family does not support the concern that national attention to
publicised police violence suppresses calls for emergency medical help in mental-health crises in the week after
attention rises, nor does it show an increase.

### Limitations

1. **The exposure is a national attention index with no local component.** The estimand is an intention-to-treat
   effect of national attention on New York City help-seeking; New Yorkers' own attention is not separately
   identified. 2. **The estimand is a citywide average.** The confirmation package holds no pre-specified test by
   neighbourhood racial composition. The effects this study is set against are concentrated in Black communities —
   among Black respondents,¹ in the highest-percentage-Black tertile of New York ZIP-code areas,³ in Black and
   Hispanic students¹⁴ ¹⁵ — and an effect confined to a minority of districts would be diluted here in proportion to
   their share of dispatches; the bound applies to the citywide average, not to any district group. Ang and colleagues
   report declines of comparable size across majority-White, -Black and -Hispanic neighbourhoods,⁶ so a flat gradient
   is not by itself disqualifying. 3. **Few independent shocks; estimates imprecise.** The panel is large but the
   number of independent attention episodes is small (29 in discovery, 15 in the clean confirmation stratum, 30 in the
   exposed one); randomization inference at the episode level is primary, and a non-rejection is a bounded null, with
   the bound stated and the estimated interval beside it, not an absence. 4. **Share outcomes are compositional.** A
   rise in injury dispatches mechanically depresses every other share. The count arm with a total-dispatch offset is a
   rate on the same denominator and does not remove the damping; the raw count without an offset, reported as a
   denominator diagnostic, is the arm free of it. 5. **Dispatch-code drift** (RECORD 19.1). The EDPC code phased in
   during 2018; EDPM appeared on 3 June 2021; 22 outcome-group codes are born or retired inside the confirmation
   windows. Codes are grouped into families, the coverage-clean sensitivities drop every episode whose window contains
   a break, and four of the seven EDP codes (EDPC, EDPM, EDPW, T-EDP), absent from the FDNY data dictionary, are
   assigned by their prefix. 6. **B-HEARD** overlaps the whole of C2, reduces mental-health EMS call rates in adopting
   precincts¹¹ and partly removes the police presence the avoidance mechanism turns on, on adoption dates that are
   low-confidence for 17 of 31 precincts; exposure is carried as bounds, and C2 is the weaker test. 7. **A call type
   is a dispatcher's classification of a caller's account**, not a diagnosis; a dispatch measures a decision to summon
   help, not need. 8. **The victim registry omits events the study is about** (Daniel Prude, Sandra Bland and others),
   so it never gates the basket. 9. **Measurement breaks in the exposure series.** Wikipedia pageviews begin on 1 July
   2015; the human-reader definition changed non-retroactively in April 2020, which the spliced sensitivity series
   addresses; Google Trends returns a sample, not a census, and its reliability is contested.¹³ 10. **The freeze was
   breached five times, four before it lifted and one at the lift,** each disclosed and none declared in advance
   (S1.1). Three of the four early breaches read confirmation-period outcome values; the fourth counted the crosswalk
   weights that carry B-HEARD exposure, which were kept inside the covariate; the fifth was a gate run at the lift.
   One specification decision, retaining EDPM in the primary family, was taken on the second, so the primary outcome's
   composition is not fully blind; nor are the test window and the second primary outcome (Deviations). No test of the
   hypothesis was read from any of them. 11. **Generalisability.** New York City's density, unified EMS system and
   B-HEARD programme are distinctive. 12. **Two of the three pre-registered hypotheses were not run.** H2
   (substitution toward the NYC Well helpline) and H3 (mechanism, through complaint and stop rates) need data not in
   the repository.

Where a limitation biases toward the null — the national index attenuates any local response, and a citywide average
dilutes a concentrated one — the estimates understate a response of the kind the index can detect. The compositional
damping of the share arm by injury dispatches runs the other way: a rise in injury calls lowers the mental-health
share, the direction the hypothesis predicts, so it would exaggerate rather than mask a decline; the count arm with a
total-dispatch offset is a rate on the same denominator and does not remove it, and the arm free of it is the raw
count without an offset (Table 2).

For practice the result is reassurance of a narrow kind: in a city where a mental-health 911 call brought police for
most of the study period, we did not detect a first-week withdrawal from emergency medical help-seeking when national
attention to police violence rose, and the estimated intervals exclude a sustained decline of the size we declared
material, though the pre-registered bound does not. It is not evidence that the anticipated presence of officers does
not deter calls: a continuous deterrent would not appear in a week-after-attention design, and withdrawal from
police-related calling need not extend to medical dispatch. The informative next design measures local rather than
national attention, assembles more independent episodes, pre-registers tests of the neighbourhood gradient and of
within-week shape, and seals the full relative-day path so that a pre-trend can be shown.

---

## Display items

<!-- BEGIN:paper_tables -->
**Table 1 — The pre-specified primary family and its pre-registered reading, New York City community districts, confirmation periods C1 (July 2015–December 2016 and January–May 2021, before B-HEARD) and C2 (June 2021–December 2024, during the B-HEARD rollout).** A: two outcomes × two arms × two periods. The first-week mean is the average of the eight daily coefficients for days 0–7 relative to the day before the episode began, with its standard error clustered on the calendar date and the normal-approximation 95% interval on that standard error (mean ± 1.96 SE); it is the reported effect size and not the test. The test is the joint Wald statistic that all eight coefficients are zero (8 df), with its randomization p at 2,000 placebo draws (primary), the asymptotic p beside it (anti-conservative on these data; S1.6) and the Benjamini–Hochberg-adjusted p over the family of eight. Shares are fractions of a district-day's dispatches; counts are log points under a total-dispatch offset. B: the pre-registered rules applied by code to the sealed table (verbatim output in S2): the episodes and district-day observations behind each period's estimates, whether the randomization null was certified (the certificate covers the share arm on the EDP share without the covariate; S1.6), whether the period rejects on either outcome under the two-arms rule, whether a cardiac or asthma cell rejects, the pre-freeze minimum detectable effects at 80% power for a sustained first-week shift (at nominal α, and inflated by the plan's approximate one-parameter factor of 1.28 for a Bonferroni-style α/8; the factor matched to the eight-df statistic is 1.21, and both are upper bounds on a Benjamini–Hochberg correction) and for a dip-and-rebound, and the reading the rules return.

*A. The family*

| period | outcome | arm | first-week mean (SE) | interval (95%) | joint χ² (8 df) | randomization p | asymptotic p | BH-adjusted p |
|---|---|---|---|---|---|---|---|---|
| C1 | EDP share | share | −0.00059 (0.00136) | −0.0032 to 0.0021 | 25.32 | 0.0115 | 0.0014 | 0.0560 |
| C1 | EDP count | count | 0.00945 (0.01623) | −0.0224 to 0.0413 | 26.11 | 0.0140 | 0.0010 | 0.0560 |
| C1 | narrow mental-health share | share | −0.00074 (0.00157) | −0.0038 to 0.0023 | 22.57 | 0.0285 | 0.0040 | 0.0760 |
| C1 | narrow mental-health count | count | −0.00013 (0.01420) | −0.0280 to 0.0277 | 17.09 | 0.0895 | 0.0291 | 0.1789 |
| C2 | EDP share | share | −0.00019 (0.00114) | −0.0024 to 0.0020 | 6.04 | 0.6522 | 0.6430 | 0.7453 |
| C2 | EDP count | count | 0.00591 (0.01127) | −0.0162 to 0.0280 | 4.75 | 0.7861 | 0.7843 | 0.7861 |
| C2 | narrow mental-health share | share | −0.00067 (0.00133) | −0.0033 to 0.0019 | 7.98 | 0.4523 | 0.4352 | 0.6597 |
| C2 | narrow mental-health count | count | 0.00197 (0.01079) | −0.0192 to 0.0231 | 7.57 | 0.4948 | 0.4764 | 0.6597 |

*B. The reading*

| period | episodes | district-day observations | null certified (share arm, EDP share) | period rejects | falsification outcome rejects | minimum detectable effect, sustained shift (nominal α) | × 1.28 (α/8, one-parameter) | minimum detectable effect, dip-and-rebound | reading |
|---|---|---|---|---|---|---|---|---|---|
| C1, primary family | 15 | 23,128 | yes | no | no | 0.01156 | 0.01480 | 0.00382 | does not reject |
| C2, primary family | 30 | 45,017 | yes | no | no | 0.00875 | 0.01120 | 0.00290 | does not reject |

**Table 2 — Outside the primary family, per period: the pre-registered sensitivities, the falsification outcomes, the denominator diagnostics and the secondary arms.** A: H1-outcome sensitivity cells are the pre-registered sensitivities on the two primary outcomes (and their cancelled-inclusive and EDP-without-EDPM variants), both arms, that were estimated — a cell identical to the primary by construction is not counted, so the two periods' batteries differ (C1's basket and EDP-without-EDPM branches are identical to its primary; C1 has no B-HEARD-bound branch). They re-estimate the same four primary cells on overlapping samples and are one result seen many times, not independent tests: the tally counts cells at unadjusted randomization p ≤ 0.05, and the ranges show that no share-arm first-week mean moves away from zero (every cell is Table S4). Override cells are the cardiac and asthma shares and counts in the primary specification, four per period; one at unadjusted randomization p ≤ 0.05 would have voided the period's primary rejections. Injury is reported beside them as a marker of street activity and does not override; the coverage-clean variants of all three are in Table S4 and none reaches p ≤ 0.05. B: the denominator diagnostics are the raw EDP count without an offset and total dispatches, first-week mean in log points with the randomization p of the joint test. The dose-response arm is the first-week effect on the share per standard deviation of the episode's peak intensity, asymptotic p only; the B-HEARD interaction exists in C2 only. The pooled rows are descriptive.

*A. Sensitivities and falsification outcomes*

| period | H1-outcome sensitivity cells | at p ≤ 0.05 | randomization p, range | first-week mean, share arm, range | override cells (cardiac, asthma) | at p ≤ 0.05 | injury cells | at p ≤ 0.05 |
|---|---|---|---|---|---|---|---|---|
| C1 | 24 | 14 | 0.0045 to 0.3573 | −0.00168 to −0.00036 | 4 | 0 | 2 | 0 |
| C2 | 30 | 0 | 0.0565 to 0.9835 | −0.00096 to 0.00023 | 4 | 0 | 2 | 0 |
| pooled (descriptive) | 38 | 4 | 0.0075 to 0.5402 | −0.00115 to −0.00005 | 4 | 0 | 2 | 0 |

*B. Denominator diagnostics and secondary arms*

| period | raw EDP count, no offset: first-week mean (randomization p) | total dispatches: first-week mean (randomization p) | dose-response, EDP share: coefficient per SD (asymptotic p) | dose-response, narrow mental-health share: coefficient (p) | B-HEARD interaction, EDP share: coefficient (p) |
|---|---|---|---|---|---|
| C1 | −0.01180 (0.0115) | −0.01585 (0.5422) | 0.00131 (0.0309) | 0.00151 (0.0187) | — |
| C2 | −0.00442 (0.3368) | −0.01004 (0.7481) | 0.00065 (0.2412) | 0.00074 (0.1820) | 0.00026 (0.7732) |
| pooled (descriptive) | −0.00614 (0.0215) | −0.01215 (0.5697) | 0.00080 (0.0364) | 0.00110 (0.0050) | — |
<!-- END:paper_tables -->

**Figure 1.** First-week coefficient paths for the EDP outcome from the sealed confirmatory run, New York City
community districts. Points are the estimated change on each of days 0 to 7 relative to the day before the episode
began (day −1), with 95% intervals from standard errors clustered on the calendar date; the solid horizontal line
is no change and the dashed line is the first-week mean, the reported effect size and not the test. Rows are the
two arms (share above; count in log points below) and share one scale; columns are the confirmation periods, C1
(left; before B-HEARD, 15 episodes) and C2 (right; during the B-HEARD rollout, 30 episodes); each panel's
heading carries the joint test's randomization p and its Benjamini–Hochberg-adjusted p. The marginal intervals are
not the test: the eight coefficients are strongly positively correlated, so the joint statistic can be small in p
while every interval crosses zero. The sealed table retains the days 0 to 7 coefficients only, so no pre-episode
path is shown; the design's defence against a pre-trend is the episode-level randomization null.
`docs/figures/fig6_conf_paths_edp.png`; the narrow mental-health outcome is Figure S1.

**Figure 2.** Daily national attention to police violence over the study period, July 2015 to December 2024. The
series is the attention index: the mean of two components standardised on a fixed 2017–2019 window — log Wikipedia
pageviews summed across the 109-article strict basket and log United States search interest in police
brutality — so the vertical axis is in standard deviations of that reference window. Shading marks the 74
adopted attention episodes from their first to their last high day, coloured by the analysis period containing each
episode's start: blue for C1 (July 2015–December 2016 and January–May 2021), grey for the discovery period
(2017–2020) and orange for C2 (June 2021–December 2024); the lighter background bands mark the periods themselves.
The dotted vertical line is the B-HEARD launch, 1 June 2021. Only the exposure is drawn; no outcome series appears.
`docs/figures/fig7_attention_decade.png`.

*Supplement:* Supplementary Methods S1; the pre-registered reading S2; Tables S1–S5 (the sealed run's family,
reading, falsification and diagnostics, sensitivities, pooled and secondary arms), S6 (the episode list), S7 (the
code list, RECORD 7.1), S8 (the crosswalk, RECORD 12.3), S9 (calibration certificates), S10 (the pre-freeze power
table); Figures S1–S6.

---

## RECORD reporting checklist (extension of STROBE for routinely collected health data)

| Checklist item | Requirement | Where addressed |
|---|---|---|
| RECORD 1.1–1.3 | Data type, database name, geography, timeframe, linkage in title and abstract | Title; Abstract (names NYC EMS Incident Dispatch Data, New York City, 2015–2024, linkage to community districts and to the attention index) |
| RECORD 6.1 | Codes/algorithms used to identify the population | Methods, *Outcome*: the EDP family code by code and the disposition filter; the narrow mental-health family's codes in Table S7 |
| RECORD 6.2 | Validation of those codes | No external validation of the dispatch codes exists yet: Kang, Lu & Pang (2026, *Psychiatric Services*)¹¹ analyse the same EMS Incident Dispatch Data (monthly precinct-level rates of nonviolent mental-health-related calls, January 2019 to December 2024; 31 adopting precincts of 76), and a comparison of their call classification with ours (which disaggregates call families and handles the mid-2018 EDPC recode explicitly) awaits their code list and is pending; four of the seven EDP codes are undocumented in the FDNY data dictionary (Limitation 5) |
| RECORD 6.3 | Linkage flow | Supplement S4, *Linkage flow* |
| RECORD 7.1 | Complete code list | Table S7 |
| RECORD 12.1 | Data cleaning | Methods, *Outcome*; the disposition filter (S1.2) |
| RECORD 12.2 | Linkage description | Methods, *Setting and data sources*; S4 |
| RECORD 12.3 | Linkage quality | Table S8 |
| RECORD 13.1 | Selection of persons/units | The 59-district whitelist and the ≥5-dispatch rule, Methods |
| RECORD 19.1 | Changing eligibility over time | Limitation 5 (code drift), Methods *Outcome*, Table S7 |
| RECORD 22.1 | Access to protocol, data, code | The public repository https://github.com/abrahimmahmud/ems-police-awareness (branch `analysis-rework`; Methods, *Ethics and data availability*; Supplement S6): frozen pre-registration whose timestamps are git commits (internal; no externally timestamped deposit exists — Limitation 10), provenance register with hashes, claims register, regression suite, sealed confirmatory table and run log |

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
11. Kang B, Lu Y-F, Pang J. An EMS-based crisis response model for mental health–related EMS calls: a quasi-experimental study. *Psychiatr Serv*. 2026;77(7):616–622. doi:10.1176/appi.ps.20250528.
12. New York City Independent Budget Office. *B-HEARD: a look at precinct level data*. January 2026. https://www.ibo.nyc.gov/assets/ibo/downloads/pdf/public-safety/2026/2026-january-bheard-a-look-at-precinct-level-data.pdf
13. Hölzl J, Keusch F, Sajons C. The (mis)use of Google Trends data in the social sciences – a systematic review, critique, and recommendations. *Soc Sci Res*. 2025;126:103099. doi:10.1016/j.ssresearch.2024.103099.
14. Ang D. The effects of police violence on inner-city students. *Q J Econ*. 2021;136(1):115-168.
15. Legewie J, Fagan J. Aggressive policing and the educational performance of minority youth. *Am Sociol Rev*. 2019;84(2):220-247.
