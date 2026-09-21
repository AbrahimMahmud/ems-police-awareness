# Public attention to police violence and emergency help-seeking in New York City, 2015–2024

*Manuscript. Target: Journal of Urban Health, Template A (public health): ~4,000 words main text, four
display items, RECORD reporting (PAPER_PLAN.md). Every result number in this document is a claim in
`docs/CLAIMS_REGISTER.csv` that recomputes from its artifact — a committed file, or one the pipeline regenerates
from the recorded inputs; a result number without a claim is a check failure, not a typo. The confirmatory
Results, the Discussion and the Abstract were written after the sealed confirmatory run of 2026-09-21 from the
sealed table and its pre-registered reading, which is reproduced verbatim in the Supplement (S2). Supplementary
Methods S1, Tables S1–S10 and Figures S1–S6 are in `docs/SUPPLEMENT.md`.*

---

## Abstract

Publicised police violence is linked to worse mental health and fewer police-related 911 calls; its effect on
mental-health help-seeking is untested at daily resolution. We asked whether national attention to police
violence increases, decreases, or leaves unchanged what New York City communities ask emergency medical
services for. In the NYC EMS Incident Dispatch Data, 2015–2024, each dispatch was linked to its community
district and day and to a publicly reconstructible attention index from Wikipedia pageviews and Google
searches. A stacked episode event study took mental-health dispatch shares and counts as outcomes, cardiac and
asthma as falsification outcomes, and randomization inference. After an exploratory period (2017–2020)
examined freely, two confirmation strata, before and after B-HEARD, stayed under a code-level freeze (five
disclosed breaches) until every hypothesis, estimator, sensitivity and reading rule was committed, then
analysed once by a
sealed script. Both return the pre-specified null: no primary cell rejects after correction,
falsification outcomes are quiet, a sustained EDP-share shift of at least the pre-freeze minimum detectable
effect (0.01156 in the clean stratum and 0.00875 in the exposed one; about 0.0148 and 0.0112 under the
approximate family correction) is disfavoured at 80% power, as is a transient dip-and-rebound of the minimum
effect of interest (−0.005); a sustained shift of that minimum is not excluded. A rise-then-fall pattern in
the clean stratum's first week, mean near zero, is reported as a hypothesis, not evidence. Within these bounds,
no first-week change in mental-health help-seeking large enough to detect follows a rise in national attention.

---

## Introduction

Policing is increasingly treated as a structural determinant of health: a set of institutional practices whose
reach extends past the people directly stopped, arrested or killed to the communities that watch, read and hear
about them. A body of population research links exposure to police violence with worse self-reported mental
health, higher psychological distress and higher psychiatric service use, concentrated among Black Americans and
in the neighbourhoods policed most intensively,¹⁻⁴ and with worse school outcomes for the young people who live
there.¹⁴ ¹⁵ The exposure in that literature is almost always an *incident* — a killing in the respondent's state
in the preceding months, a policing rate in the respondent's neighbourhood — and the outcome is almost always
measured after a person has already sought care.

There is a second, less studied channel by which publicised police violence could change health outcomes, and it
runs through the decision to seek help at all. In New York City a 911 call reporting a mental-health crisis
dispatches an ambulance and, for most of the study period, the police. When a police killing dominates the news,
a person deciding whether to call on behalf of a relative in crisis may weigh the arrival of officers differently
than they did the week before. Desmond, Papachristos and Kirk documented exactly this kind of withdrawal after a
single publicised beating in Milwaukee, in police-related 911 calls, lasting more than a year;⁵ Ang and
colleagues found 911 call volume fell by roughly a quarter across thirteen cities after the murder of George
Floyd while gunshots detected by acoustic sensors rose, and attributed the gap between that response and the
smaller responses to lower-profile killings to salience and media attention.⁶ Attention, not incidence, is the
mechanism those results point at, and neither study measured it. Attention has been measured on its own terms —
on Twitter, the names of earlier Black victims of police violence surged collectively after the murder of George
Floyd⁹ — but not, to our knowledge, carried to a health outcome at the resolution of a day.

The closest quantified antecedent on the health side is Das and colleagues, who found depression-related
emergency department visits among African Americans rose by about 11% in the month of a police killing of an
unarmed African American and the three months following, across 75 counties⁷ — a class of finding whose
sensitivity to how victims' armed status is coded has since been contested⁸ (the attention measure used here
makes no use of armed status). Their design, like every administrative-outcome study we know of, works at the
county-month. It cannot say whether the response peaks on the first day or the twentieth, whether it is a sustained
shift or a dip that rebounds, or whether what changed was distress or the willingness to summon help — two forces
that push the same instrument in opposite directions.

This study addresses three gaps. The exposure is national *attention*, measured daily from what the public
chose to look up — Wikipedia pageviews of articles about people killed by police and Google searches
about police violence — rather than the occurrence of an incident, so that anniversaries, verdicts and video
releases count when they draw attention and killings do not when they draw none. The outcome is observed at the
community district and the day, so the shape of the response inside the first week is estimable. And the outcome
sits at the help-seeking decision itself — an emergency medical dispatch coded as a mental-health crisis — with
dispatch codes for conditions that should not respond to news (cardiac, asthma) as falsification outcomes.

We asked whether high-attention episodes increase, decrease or leave unchanged the share of emergency medical
dispatches coded as mental-health crises in the first week after attention rises, in New York City's 59 community
districts between July 2015 and December 2024. The primary hypothesis predicted a decline; the test is two-sided.
The design splits the decade into an exploratory period,
examined freely, and two sealed confirmatory periods on which every specification, hypothesis, sensitivity and
interpretation rule was written down before any confirmation-period outcome entered a model or test — with two
disclosed exceptions: the second primary outcome and the joint first-week statistic were adopted after discovery
results had been seen, and one code in the primary family was retained on confirmation-period counts read in a
breach of the freeze (Methods, Limitations).

---

## Methods

### Study design and pre-registration

We conducted a quasi-experimental panel study — a stacked episode event study — of New York City emergency
medical dispatches by community district and day. The decade was divided into a **discovery** period (1 January
2017 to 31 December 2020), used to build the pipeline and explore the data, and two **confirmation** strata
protected from specification choices by a freeze whose five recorded breaches — one of which did inform a
specification decision — are disclosed below (Deviations; Limitation 9) and in full in Supplementary Methods S1.1:
**C1**, 1 July 2015 to 31 December 2016 together with 1 January to 31 May 2021 — every confirmation month before
the B-HEARD mental-health response programme launched; the 2015–16 block is also free of COVID-19, the 2021 block
is not — and **C2**, 1 June 2021 to 31 December 2024, in which B-HEARD was rolling out precinct by precinct. The
lower bound of C1 is a data constraint: Wikimedia's pageview interface begins on 1 July 2015.

The confirmation strata were protected by a code-level freeze that let no exploratory script read
confirmation-period outcome values, enforced by a regression suite of automated checks (S1.1). The hypotheses,
the estimator, the primary inference, the calibration precondition, the sensitivity battery, the multiple-testing
family and the rules for reading every possible result were committed to the repository in dated documents before
the freeze was lifted (`docs/CONFIRMATION_PLAN.md`, `docs/PRE_ANALYSIS_NOTE.md`); the pre-registration is internal
(git timestamps; no external deposit), and every deviation from the originally frozen text is listed there and
summarised below. The five occasions on which confirmation-period outcome data were touched before the sealed
run, two of which shaped the analysis (the EDPM code's membership of the primary family; the district weights
behind the B-HEARD covariate), are disclosed in *Limitations* and S1.1; no test of the hypothesis was read from
any of them.

### Setting and data sources

New York City is divided into 59 community districts, the finest geography at which the dispatch data carry a
stable identifier across the decade. Dispatches without a district are
retained in citywide totals and excluded from district shares. The **NYC EMS Incident Dispatch Data**
(Fire Department of the City of New York, via NYC OpenData, dataset 76xm-jjuj) record every emergency medical
dispatch with an incident timestamp, a dispatcher-assigned final call type, a disposition and a community
district. We downloaded the complete set (29,978,154 records) through the open-data API in seven-column pages and
used dispatches from December 2014 to December 2024; the extract's hash is recorded in a provenance register
(S1.2). **Wikipedia pageviews** are daily article-level views by human readers from the Wikimedia REST API, 1 July
2015 onward, with every historical title of each article resolved and summed. **Google Trends** is United States
daily search interest for the *police brutality* topic, fetched in overlapping windows and stitched. **B-HEARD
adoption** dates by precinct were compiled from Mayor's Office announcements and validated against the Independent
Budget Office's 2026 precinct-level report¹² (31 precincts; adoption dates carried as an earliest and a latest
bound because 17 of 31 rest on low-confidence evidence), and mapped to community districts through a crosswalk
built from the dispatch data's own precinct and district fields (Table S8). The **victim registry** (Mapping Police
Violence) labels episodes and supplies evidence that an article concerns a police killing; it never gates basket
membership. Demographics (ACS 2015–2019) describe the setting.

### Measures

**Exposure.** The daily attention index averages two standardised components — the log of pageviews summed across
the article basket and the log of national search interest in police brutality — each standardised once on a fixed
2017–2019 reference window and never re-standardised inside an analysis sample (S1.3). The index has no city-local
component, so the exposure is national attention and is described as such throughout. The **strict** basket (109
articles), in which public evidence names law enforcement as the actor in the person's death, is the primary
exposure; the **broad** basket (118 articles) adds the articles in which no evidence establishes who acted, and a
**spliced** series adds Wikimedia's automated-agent class from April 2020 so that the series is comparable across
the decade; both are pre-registered sensitivities.

**Episodes.** An attention episode begins on the first day of a run of days on which the index lies in the top 10%
of its own calendar year, and ends when the run ends; it is a burst of attention, not a killing. The originally
frozen episode rule produced a single episode covering the whole summer of 2020 and was replaced by this shock rule
while blind to every outcome (Deviations). The frozen list (70 episodes) is preserved byte-identical in the
repository; the adopted list holds 74 episodes in the strict basket (29 in discovery, 15 in C1, 30 in C2) and 75 in
the broad (Table S6; Figure 2).

**Outcome.** For each community district and day we counted dispatches whose final call type carries the
*emotionally disturbed person* prefix (EDP, EDPC, EDPE, EDPM, EDPT, EDPW, T-EDP) and divided by all dispatches that
were sent and not cancelled or duplicated (S1.2, S1.5). This **EDP share** is the primary outcome; a **narrow
mental-health share** adds altered-mental-status and suicide-related codes. Because a share can move when its
denominator does, every outcome is also modelled as a **count** with the district-day's total dispatches as an
offset. District-days with fewer than five dispatches are excluded in both arms. Falsification outcomes are the
cardiac and asthma families; injury is reported as a marker of street activity.

**Covariate.** B-HEARD exposure — the share of a district's dispatches falling in precincts that had adopted the
programme by that date, under the earliest and the latest bound — enters every specification; it is zero before
June 2021 and in C2 is also interacted with the first-week effect in a secondary specification.

### Statistical analysis

**Estimator.** For each episode we stacked the 14 days before and after its start in every district and fitted
*y* ~ *i*(relative day, reference = −1) + B-HEARD exposure | episode × district + day of week, by ordinary least
squares for shares and Poisson pseudo-maximum likelihood with a log offset for counts, with standard errors
clustered on the calendar date. The test statistic is a joint Wald test that the eight coefficients for days 0 to 7
are all zero; the mean of those coefficients is reported as an effect size and is not the test, because a dip
followed by a rebound averages to near zero and is invisible to a mean but not to the joint test (S1.6).

**Inference.** The primary p-value is by episode-level randomization inference at 2,000 placebo draws preserving
the real episodes' spacing — an anchor-shift null on a contiguous stratum (discovery, C2) and a circular
within-block shift on the two-block stratum (C1) — with the asymptotic joint-Wald p reported beside it, never
instead of it. Before any p-value is
reported for a stratum, its null is certified on 1,000 synthetic no-effect panels carrying the dependence measured
on the discovery rows (200 for the descriptive pooled sample): the rejection rate at α = 0.05 must lie inside its
binomial band and the p-values must be uniform on the exact lattice (Table S9). The confirmatory script refuses to
run without a current certificate, and a stratum that failed calibration would have been reported with its
randomization p flagged uncertified under a rule written before the verdict existed (S1.6).

**The family and what lies outside it.** The primary family — fixed before the freeze lifted, though its second
outcome and its joint statistic were adopted after discovery results had been seen (Deviations) — is two outcomes ×
two arms × two strata = eight tests, controlled by Benjamini–Hochberg at *q* = 0.05. Outside it, each for the reason
given in the plan (S1.7): the pooled estimate (descriptive); ten pre-specified sensitivities on both arms (the July
2016 episode dropped; the broad basket; the spliced series; the late B-HEARD bound; coverage-clean and
geocoding-clean episode sets; 28- and 60-day post windows; cancelled dispositions restored; EDP without EDPM),
reported beside the primary and never substituted for it; the falsification outcomes, where a cardiac or asthma
cell at unadjusted p ≤ 0.05 overrides every primary rejection in its stratum; three denominator diagnostics per
stratum (each primary outcome's raw count without an offset, and total dispatches); and two secondary arms with
asymptotic p only, the B-HEARD interaction (C2) and a dose-response arm (the first-week effect per standard
deviation of the episode's peak intensity, predicted negative). A family cell rejects when its adjusted p is below
0.05; a stratum rejects on an outcome when both arms reject with the same sign of the first-week mean; a rejection
in C1 alone is confirmation, in C2 alone it is not, because B-HEARD moves the outcome in the hypothesised direction.

**Power and the reading of a non-rejection.** Before the freeze lifted, the minimum detectable effect at 80% power
was computed by simulation for each stratum against a pre-declared minimum effect of interest of −0.005 in the EDP
share (about 6% of the discovery-period mean), for a sustained first-week shift and for a dip-and-rebound of the
same size (Table S10). Every stratum is underpowered for the sustained shape (minimum detectable effects of 1.75 to
2.31 times the minimum effect of interest) and adequately powered for the transient shape; the minimum detectable
effect is measured against the asymptotic test at nominal α while the non-rejection it bounds is a corrected
randomization p, a difference the plan records as a limitation with an approximate correction factor quoted beside
the bound (S1.8). The reading of a non-rejection was therefore fixed in advance: no effect detected; a sustained
shift at or above the stratum's minimum detectable effect is disfavoured; a sustained shift of the minimum effect
of interest is not excluded; a transient effect of that size is disfavoured. Every reading rule is implemented as
code that reads only the sealed result table and the pre-freeze power table; its sentences are reproduced verbatim
in S2, and the Results below restate them in prose with every number held to the sealed files by a registered
claim.

**The sealed run.** The confirmatory script ran once after the lift, at exactly the pre-specified 2,000 draws per
cell, and wrote its table to a tracked file with a sidecar pinning source hashes, inputs, commit and seed. It was
started seven times (a container suspension, two out-of-memory kills of the worker pool, worker-count changes),
every start a dated row of a tracked run log and every cell resumed from a ledger keyed to its own seed and design,
so no number depends on the restarts; the pipeline is byte-reproducible (S1.9).

**Exploratory analyses.** Discovery-period estimates and an outcome decomposition across thirteen outcomes in four
dispatch families and five three-day windows (65 tests under a Bonferroni threshold) are exploratory, not tests of
the hypothesis; a distributed-lag specification and a heterogeneity analysis are in S1.10 and Figures S2–S4.

### Deviations from the frozen pre-registration

Disclosed in full, with dates and original wording, in the plan's numbered summary table: the episode construct
(regime rule → shock rule, blind to outcomes); the test window (days 0–5 → 0–7, joint) and the second primary
outcome, adopted after discovery results had been seen and marked non-blind; the B-HEARD covariate and its bounds;
the within-block randomization scheme; the sensitivity set; the reading rules for a non-rejection and for an
uncertified null; the disposition filter; the five freeze incidents (Limitation 9, S1.1); two hypotheses not run
(Limitation 12).

### Ethics

The dispatch data are public and contain no personal identifiers. **[MIT COUHES non-human-subjects determination:
pending — Abrahim.]**

---

## Results

### Discovery period (exploratory)

The panel holds 217,356 district-days across the 59 community districts from December 2014 to December 2024; the
discovery analysis window holds 86,199 of them. In that window the mean EDP share is 0.0856 and the mean
district-day carries 66.1 dispatches. Twenty-nine attention episodes begin inside the discovery window (Table S6;
Figure 2).

Stacked over those 29 episodes with day −1 as reference, the first-week coefficient on the EDP share is −0.00123
(randomization *p* = 0.697, 2,000 draws) and on the EDP count −0.01084 (*p* = 0.527); on the narrow mental-health
share −0.00103 (*p* = 0.886) and count −0.00615 (*p* = 0.822). Share and count arms agree in sign in every case. The
estimates move in the fourth decimal across the 14-, 28- and 60-day post windows. Read against the minimum effect of
interest of −0.005, the EDP share estimate is about a quarter of it.

Across the 65 outcome-by-window decomposition tests (Figure S4), under a Bonferroni threshold of α = 0.000769, 2
survive and both are injury in days 0–2: injury share (+0.00159, *p* = 0.00004) and log injury count (+0.01048,
*p* = 0.00008); the injury-share coefficient for days 12–14 (+0.00104, *p* = 0.00172) does not. No mental-health
outcome survives (smallest *p* 0.044 in the mental-health family; the narrow mental-health count, in the volume
family, reaches *p* 0.014 in days 6–8 and does not survive either); neither falsification outcome survives (cardiac
share *p* = 0.082 and asthma share *p* = 0.076 at their strongest).

### Confirmatory strata

**The family (Table 1).** Neither stratum rejects the pre-registered null on either primary outcome after the
Benjamini–Hochberg correction over the family of eight. In C1, the clean stratum, the joint test sits close to the
threshold on three of the four cells: the smallest unadjusted randomization p among its four primary cells is
0.0115, on the EDP share, whose adjusted p is 0.056; the narrow mental-health share's adjusted p is 0.076. In C2,
the B-HEARD-exposed stratum, the smallest unadjusted randomization p is 0.4523. The reader therefore returns "does
not reject" for both strata, and — the null being certified and no falsification cell rejecting — reads each
against the pre-freeze power (§19 rule 2): a sustained level shift at or above the pre-freeze minimum detectable
effect of the EDP share (0.01156 in C1 and 0.00875 in C2; about 0.01480 and 0.01120 under the approximate
eight-test correction) is disfavoured at 80% power; a sustained shift of the minimum effect of interest, −0.005, is
not excluded; a transient dip-and-rebound of that size is disfavoured, its pre-freeze minimum detectable effects
being 0.00382 and 0.00290. The reader's conclusion under the note's §9.4 is "THE PRE-SPECIFIED NULL (9.4 row 5): a
bounded null in both strata, read by addendum 19 rule 2".

**The shape of the first week (Figure 1).** The joint statistic tests the eight daily coefficients together, and
in C1 what it responds to is a shape, not a level. On the EDP share the path is positive on days 0 to 2 and negative
on days 3, 5, 6 and 7, so that the first-week mean, −0.00059, is a small fraction of any single day's coefficient;
the count arm traces the same shape and averages to +0.00945 log points. The two arms' means thus straddle zero,
which is one reason the pre-registered two-arms rule could not have read a rejection as a directional effect even
had the adjusted p crossed the threshold. In C2 the path is flat within its intervals on both arms. The narrow
mental-health outcome shows the same picture in both strata (Figure S1).

**Outside the family (Table 2).** Of C1's 24 sensitivity cells on the primary outcomes, 14 lie at unadjusted
randomization p ≤ 0.05, on the same shape; of C2's 30, none does. No cardiac or asthma cell reaches p ≤ 0.05 in
either stratum, so the override rule had nothing to act on. Among the denominator diagnostics, C1's raw EDP count
without an offset has a randomization p of 0.0115 while total dispatches have 0.5422; in C2 the two are 0.3368 and
0.7481. The pooled stratum, read descriptively, does not reject on both arms. The secondary dose-response arm moves
against the predicted direction in C1 — a larger, not smaller, first-week share per standard deviation of episode
intensity, at asymptotic p 0.0309 on the EDP share and 0.0187 on the narrow share — and in C2 it does not move
(0.2412 and 0.1820); the B-HEARD interaction in C2 does not move on any outcome (asymptotic p from 0.7732 to 0.9761).
The reader's transcript is S2; the full tables S1–S5.

---

## Discussion

This study asked a narrow question with an unusually strict design: whether the share of New York City emergency
medical dispatches coded as mental-health crises moves in the week after national attention to police violence
rises. The outcome sits at the help-seeking decision, observed by community district and day, fine enough to
see the shape of a response inside the first week, and the inference is confirmatory in the pre-registered sense: the hypotheses, the
estimator, the null the p-values rest on, the sensitivities and the sentence to be written for every possible result
were committed before any confirmation-period outcome entered a model or test, except as the five recorded freeze
incidents describe (Limitation 9), and the confirmatory table was produced by one sealed script run once and read by
code.

**What the reading says.** Both strata return the pre-specified null. A sustained first-week shift in the EDP share
at or above the pre-freeze minimum detectable effect (0.01156 in C1 and 0.00875 in C2 at nominal α; about 0.0148 and
0.0112 under the approximate family correction the plan quotes beside it) is disfavoured at 80% power; a sustained
shift of the declared minimum effect of interest, −0.005, is not excluded; a transient dip-and-rebound of that size
is disfavoured, the design having been powered for that shape (pre-freeze minimum detectable effects 0.00382 and
0.00290). The falsification outcomes are quiet in both strata. On the mechanism the study set out to test, the
avoidance account predicted a first-week decline in help-seeking; the confirmation strata neither show it nor rule
out a sustained decline of the size the study declared it cares about, and they disfavour a transient
dip-and-rebound of that size, the shape the mechanism work had made the most plausible.

**What C1 actually shows, and why it is not read as an effect.** Three unadjusted randomization p-values below
0.03 in the clean stratum and fourteen of twenty-four sensitivity cells below 0.05 invite the question whether a
signal hides behind the correction; Figure 1 answers it. The joint test is a test of the eight
daily coefficients together, and what it responds to in C1 is a shape — a rise over days 0 to 2 followed by a fall
over days 3 to 7 — traced identically by both arms, with first-week means so close to zero that they straddle it.
That shape is not the hypothesised decline, and it is not the dip-and-rebound the study was powered for; it is the
reverse order. The pre-registered rules require a corrected rejection on both arms with the same sign before a
direction is read, and this pattern would have failed the sign test even had the correction been cleared. Two
further facts belong beside it. C1's raw EDP count without an offset fell in the first week (randomization p 0.0115)
while total dispatches did not (0.5422), a small general contraction in dispatching that the design cannot separate
from a mental-health-specific one. And the dose-response arm, outside the family, is positive in every stratum:
the more intense the episode, the higher the first-week share. Taken together these are a hypothesis a later study
could pre-register — a short rise in mental-health dispatches at the peak of national attention, subsiding within
the week — and not a finding of this one.

**Relation to prior work.** The closest antecedents measured incidents rather than attention, and outcomes at
the county-month or coarser: Das and colleagues' rise in depression-related emergency visits among African
Americans around police killings of unarmed African Americans,⁷ Desmond, Papachristos and Kirk's year-long fall in
police-related 911 calls in Milwaukee's Black neighbourhoods after one publicised beating,⁵ and Ang and
colleagues' citywide fall in 911 calls after the murder of George Floyd, attributed to salience;⁶ outside policing,
crisis-service use after a publicised mass shooting has been studied with a comparable event-study design.¹⁰ Our
design speaks to the same channel at the day rather than the month, with the attention those authors invoke as the
mechanism measured directly and with codes that should not respond to news carried as falsification outcomes. The
outcome here is a medical dispatch, not a police-related call, so an avoidance response would run through the
anticipated presence of officers at a medical call rather than through crime reporting; and the discovery period
contains the 2020 episodes on which the earlier evidence rests, where the pooled estimate is a bounded null on every
mental-health outcome and the only movements surviving the corrected threshold are rises in injury dispatches in the
first three days, consistent with street activity rather than with withdrawal from care.

**What the design cannot say.** The attention index is national, so the estimand is the effect of national
attention on New York help-seeking and not of New Yorkers' own attention; and the confirmation strata hold few
independent episodes, so a non-rejection bounds a sustained shift at the pre-freeze minimum detectable effect and no
smaller. Within those bounds, the primary family does not support the concern that national attention to publicised
police violence suppresses calls for emergency medical help in mental-health crises at the citywide scale in the
week after attention rises, nor does it show an increase. What would move the question is a local measure of attention,
more independent episodes, and a pre-registered test of the within-week shape the clean stratum suggests.

### Limitations

1. **The exposure is a national attention index with no local component.** The estimand is an intention-to-treat
   effect of national attention on New York City help-seeking; New Yorkers' own attention is not separately
   identified.
2. **Few independent shocks; estimates imprecise.** The panel is large but the number of independent attention
   episodes is small (29 in discovery, 15 in the clean confirmation stratum, 30 in the exposed one); randomization
   inference at the episode level is primary. The design is underpowered against the pre-declared minimum effect
   for a sustained first-week shift in every stratum and adequately powered for a transient dip-and-rebound; a
   non-rejection is a bounded null, with the bound stated, not an absence.
3. **Share outcomes are compositional.** A rise in injury dispatches mechanically depresses every other share;
   counts with a total-dispatch offset are reported beside shares for every outcome.
4. **Dispatch-code drift** (RECORD 19.1). The EDPC code phased in during 2018; EDPM appeared on 3 June 2021; 22
   outcome-group codes are born or retired inside the confirmation windows. Codes are grouped into families so that
   a recode within a family does not move the family; the coverage-clean sensitivities drop every episode whose
   window contains a break. Four of the seven EDP codes (EDPC, EDPM, EDPW, T-EDP) are absent from the FDNY data
   dictionary and are assigned to the family by their prefix.
5. **B-HEARD** overlaps the whole of C2 and moves the outcome in the hypothesised direction, on adoption dates that
   are low-confidence for 17 of 31 precincts; exposure is carried as bounds, and a C2-only rejection would not have
   counted as confirmation.
6. **A call type is a dispatcher's classification of a caller's account**, not a diagnosis; a dispatch measures a
   decision to summon help, not need.
7. **The victim registry omits events the study is about** (Daniel Prude, Sandra Bland and others), so the basket is
   not gated on registry membership.
8. **Measurement breaks in the exposure series.** Wikipedia pageviews begin on 1 July 2015; the human-reader
   definition changed non-retroactively in April 2020, which the spliced sensitivity series addresses; Google Trends
   returns a sample, not a census, and its reliability across studies is itself contested.¹³
9. **The freeze was breached five times, four before it lifted and one at the lift,** each disclosed and none
   declared in advance (S1.1). Three of the four early breaches read confirmation-period outcome values (a citywide
   annual mental-health share; precinct-level EDPM counts and annual family totals; record-level 2014–16 statistics
   including an estimated step in the mental-health share); the fourth counted the crosswalk weights that carry
   B-HEARD exposure, which were kept and sit inside the estimating equation's covariate; the fifth was a gate run at
   the lift. One specification decision, retaining EDPM in the primary family, was taken on the second, so the
   primary outcome's composition is not fully blind. No test of the hypothesis was read from any of them. The
   pre-registration's timestamps are internal git commits; the external-deposit remedy was foreclosed at the lift.
10. **The episode construct changed after the original freeze** while blind to outcomes; **the test window and the
    second primary outcome changed after discovery results had been seen** and are not blind — the plan marks and
    discounts them.
11. **Generalisability.** New York City's density, unified EMS system and B-HEARD programme are distinctive.
12. **Two of the three pre-registered hypotheses were not run.** H2 (substitution toward the NYC Well helpline) and
    H3 (mechanism, through complaint and stop rates) need data that are not in the repository; H1 alone is the
    confirmation package, materially weaker than the joint package the original power note assumed.

Where a limitation biases toward the null — the national index attenuates any local response — the estimates
understate a response of the kind the index can detect. The compositional damping of the share arm by injury
dispatches runs the other way: a rise in injury calls lowers the mental-health share, the direction the hypothesis
predicts, so it would exaggerate rather than mask a decline; the count arm, reported beside every share, carries no
such damping.

---

## Display items

<!-- BEGIN:paper_tables -->
**Table 1 — The pre-specified primary family and its pre-registered reading.** A: two outcomes × two arms × two strata; first-week mean coefficient (date-clustered SE), the joint Wald statistic on days 0–7 (8 df), the randomization p at 2,000 draws and the Benjamini–Hochberg-adjusted p over the family of eight. The test is the joint statistic; the mean is the effect size. B: the reading applied by code (addendum §23, §19 rule 2): whether the stratum's null was certified, whether it rejects, whether a falsification cell rejects, the pre-freeze minimum detectable effects for a sustained shift (nominal α; under the approximate eight-test correction) and for a transient dip-and-rebound, and the sentence the rules return.

*A. The family*

| stratum | outcome | arm | episodes | first-week mean (SE) | joint χ² | RI p | BH p |
|---|---|---|---|---|---|---|---|
| C1 | EDP share | share | 15 | −0.00059 (0.00136) | 25.32 | 0.0115 | 0.0560 |
| C1 | EDP count | count | 15 | 0.00945 (0.01623) | 26.11 | 0.0140 | 0.0560 |
| C1 | narrow MH share | share | 15 | −0.00074 (0.00157) | 22.57 | 0.0285 | 0.0760 |
| C1 | narrow MH count | count | 15 | −0.00013 (0.01420) | 17.09 | 0.0895 | 0.1789 |
| C2 | EDP share | share | 30 | −0.00019 (0.00114) | 6.04 | 0.6522 | 0.7453 |
| C2 | EDP count | count | 30 | 0.00591 (0.01127) | 4.75 | 0.7861 | 0.7861 |
| C2 | narrow MH share | share | 30 | −0.00067 (0.00133) | 7.98 | 0.4523 | 0.6597 |
| C2 | narrow MH count | count | 30 | 0.00197 (0.01079) | 7.57 | 0.4948 | 0.6597 |

*B. The reading*

| stratum | null certified | stratum rejects | placebo rejects | MDE, sustained (nominal α) | under family correction | MDE, transient | reading |
|---|---|---|---|---|---|---|---|
| C1 | yes | no | no | 0.01156 | 0.01480 | 0.00382 | does not reject |
| C2 | yes | no | no | 0.00875 | 0.01120 | 0.00290 | does not reject |

*Conclusion returned by the reader (note §9.4 as amended by addendum §23): THE PRE-SPECIFIED NULL (9.4 row 5): a bounded null in both strata, read by addendum 19 rule 2*

**Table 2 — Outside the family, per stratum: sensitivities, falsification, the denominator diagnostics and the secondary arms.** H1-outcome sensitivity cells are the pre-registered sensitivities on the two primary outcomes and their cancelled-inclusive and EDP-without-EDPM variants, both arms, estimated (cells identical to the primary by construction are not counted); falsification cells are the cardiac and asthma shares and counts, and their coverage-clean variants, plus injury. Counts at p ≤ 0.05 use the unadjusted randomization p. The denominator diagnostics are the raw EDP count without an offset and total dispatches (randomization p). The dose-response arm is the first-week effect on the share per SD of the episode's peak intensity, asymptotic p only; the B-HEARD interaction exists in C2 only. The pooled row is descriptive.

| stratum | H1-outcome sensitivity cells | at p ≤ 0.05 | falsification cells | at p ≤ 0.05 | raw EDP count, RI p | total dispatches, RI p | dose-response, EDP share: coef (asymptotic p) | dose-response, narrow MH share: coef (p) | B-HEARD interaction, EDP share: coef (p) |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 24 | 14 | 6 | 0 | 0.0115 | 0.5422 | 0.00131 (0.0309) | 0.00151 (0.0187) | — |
| C2 | 30 | 0 | 6 | 0 | 0.3368 | 0.7481 | 0.00065 (0.2412) | 0.00074 (0.1820) | 0.00026 (0.7732) |
| pooled (descriptive) | 38 | 4 | 6 | 0 | 0.0215 | 0.5697 | 0.00080 (0.0364) | 0.00110 (0.0050) | — |
<!-- END:paper_tables -->

**Figure 1.** The sealed run's day-by-day first-week coefficients for the EDP outcome, share arm above and count
arm below, C1 left and C2 right, with 95% intervals (date-clustered) and the first-week mean as a dashed line; the
joint test is on the eight coefficients together. `docs/figures/fig6_conf_paths_edp.png`; the narrow mental-health
outcome is Figure S1.

**Figure 2.** National attention to police violence, July 2015 to December 2024, with every adopted episode shaded by
the stratum whose analysis window holds its start and the B-HEARD launch marked; treatment side only.
`docs/figures/fig7_attention_decade.png`.

*Supplement:* Supplementary Methods S1; the reader's transcript S2; Tables S1–S5 (the sealed run's family, reading,
falsification and diagnostics, sensitivities, pooled and secondary arms), S6 (the episode list), S7 (the code list,
RECORD 7.1), S8 (the crosswalk, RECORD 12.3), S9 (calibration certificates), S10 (the pre-freeze power table);
Figures S1–S6.

---

## RECORD reporting checklist (extension of STROBE for routinely collected health data)

| Checklist item | Requirement | Where addressed |
|---|---|---|
| RECORD 1.1–1.3 | Data type, database name, geography, timeframe, linkage in title and abstract | Title; Abstract (names NYC EMS Incident Dispatch Data, New York City, 2015–2024, linkage to community districts and to the attention index) |
| RECORD 6.1 | Codes/algorithms used to identify the population | Methods, *Outcome*: the EDP family code by code and the disposition filter; the narrow mental-health family's codes in Table S7 |
| RECORD 6.2 | Validation of those codes | No external validation of the dispatch codes exists yet: Kang, Lu & Pang (2026, *Psychiatric Services*)¹¹ analyse the same EMS Incident Dispatch Data (monthly precinct-level rates of nonviolent mental-health-related calls, January 2019 to December 2024; 31 adopting precincts of 76), and a comparison of their call classification with ours (which disaggregates call families and handles the mid-2018 EDPC recode explicitly) awaits their code list and is pending; four of the seven EDP codes are undocumented in the FDNY data dictionary (Limitation 4) |
| RECORD 6.3 | Linkage flow | Supplement S4, *Linkage flow* |
| RECORD 7.1 | Complete code list | Table S7 |
| RECORD 12.1 | Data cleaning | Methods, *Outcome*; the disposition filter (S1.2) |
| RECORD 12.2 | Linkage description | Methods, *Setting and data sources*; S4 |
| RECORD 12.3 | Linkage quality | Table S8 |
| RECORD 13.1 | Selection of persons/units | The 59-district whitelist and the ≥5-dispatch rule, Methods |
| RECORD 19.1 | Changing eligibility over time | Limitation 4 (code drift), Methods *Outcome*, Table S7 |
| RECORD 22.1 | Access to protocol, data, code | The public repository: frozen pre-registration whose timestamps are git commits (internal; no externally timestamped deposit exists — Limitation 9), provenance register with hashes, claims register, regression suite (S6) |

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
