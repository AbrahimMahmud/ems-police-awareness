# Pre-analysis note — **RECONSTRUCTED AFTER THE FACT**

> **Read this box before anything else.**
>
> **This document was assembled on 2026-09-12. It is not a pre-registration and
> it does not carry a timestamp from before the analysis began.** It is a
> reconstruction: it gathers, in one place and in plain language, commitments
> that were made at different times between the original freeze and today, and
> it says for each one whether it was made while blind to the confirmation-period
> outcomes.
>
> The project's actual frozen record is the text above the addendum line in
> [`CONFIRMATION_PLAN.md`](CONFIRMATION_PLAN.md), which is preserved byte for
> byte, together with the deviation addendum appended below it. Where this note
> and that document differ, **that document is the record and this one is the
> explanation**.
>
> Writing it after the fact is worth something only because of what it admits.
> A reconstruction that quietly presented itself as a pre-registration would be
> worse than no document at all, because it would convert a real limitation into
> a false credential. §11 is the ledger of what was and was not decided blind,
> and it is the part of this note that a sceptical reader should read first.
>
> **Nothing in this note was written with access to any confirmation-window
> outcome.** At the time of writing `config.FREEZE_ACTIVE` is `True`, the
> confirmation windows (2015-01-01→2016-12-31 and 2021-01-01→2024-12-31) have
> never been modelled, and the two accesses that did occur are disclosed in §11.4
> rather than described as non-events.

---

## 1. The question

When a police killing gets a lot of public attention, do New Yorkers change what
they ask 911 for?

The specific mechanism: in New York, calling 911 about someone in a mental-health
crisis usually brings both an ambulance and the police. If a killing is dominating
the news, some people may decide that calling is too dangerous — for themselves,
or for the person they are trying to help. If that is true, mental-health calls to
EMS should fall in the days after a big attention episode.

Three outcomes are possible and the study is framed so that all three are
reportable:

* **a decline** — people withdraw from a system they have come to see as risky;
* **an increase** — attention to a crisis makes people more willing to call;
* **no change**, estimated precisely enough to rule out an effect of interesting
  size.

**A precisely estimated zero is a result, not a failure.** This is stated here,
before the answer is known, because the value of saying it afterwards is nil.

## 2. The outcome — what is counted

For each of New York City's **59 community districts** on each **day**, we count
mental-health EMS dispatches and divide by all EMS dispatches that district had
that day. Two primary outcomes:

| Outcome | What it is |
|---|---|
| `edp_share` | "emotionally disturbed person" dispatches ÷ all dispatches |
| `mh_narrow_share` | EDP + altered mental status + suicide/jump ÷ all dispatches |

The share is the primary form because the hypothesis is **compositional** — it is
about what people ask for, relative to everything else they ask for, not about how
busy the ambulance service is. District-days with fewer than **5** total calls are
excluded from share calculations because a share of 1/2 is not a measurement
(`config.MIN_TOTAL_CALLS_FOR_SHARE`).

Every outcome is **also** estimated as a raw count, with the log of total calls as
an offset, and both are always reported. This is not decoration. The project's
most striking discovery-period pattern — a visible move in EDP share after the
2020 Floyd protests — **does not survive in counts**: EDP counts were flat while
the denominator rose 6.4%, because injury calls rose about 20% (`PAPER_MASTER.md`
§5.4). A compositional finding that lives only in the denominator is not a finding
about demand, and reporting one arm is exactly how such a reversal goes unnoticed.

**Placebo outcomes** — cardiac, injury and asthma shares and counts — are
estimated identically. There is no plausible route by which attention to a police
killing changes whether someone has a heart attack, so a movement there is
evidence that the design is picking up something other than what it claims.

Two known imperfections in the outcome, stated because they bound what it can
mean. First, the extract drops cancelled and never-sent dispatches, and that
filter is not neutral: it removes **7.47% of EDP calls against 0.76–0.77% of
altered-mental-status and asthma calls**, a 9.9× ratio, so it removes exactly the
calls most likely to be affected (finding O1). The excluded calls are now kept in
their own file so the cancelled-inclusive version can be run rather than promised;
including them raises the mean mental-health share from 0.1083 to 0.1119 (+3.3%)
and the two series correlate 0.9758. Second, the EDP family contains call codes
that the FDNY data dictionary does not document (EDPC, EDPM, EDPW, T-EDP); they
are included because EDPC is observably a progressive recode of EDP and omitting
it would create a time-trending undercount, but that rests on a pattern in the
data rather than on documentation (finding O3).

## 3. The treatment — what "attention" means

The treatment is **CAI-D**, a daily national index of public attention to police
violence, built from two public and re-fetchable components
(`config.CAI_D_COMPONENTS`):

* `wiki_ext` — Wikipedia pageviews, summed over a basket of articles about people
  killed by police;
* `trends_us` — United States Google Trends interest in police-violence terms.

From that daily index, **episodes** are cut: a local peak in attention, with its
onset, bounded so that no episode is longer than the 14-day window it is analysed
in. An episode is a *shock* ("attention to a specific killing began on day X"),
not a *regime* ("attention was high for a stretch"). The entry bar is the top 10%
of days **within each calendar year**, with a looser exit bar at the top 25% so
that an episode captures the slow tail of a shock and not only its onset.

Two features of this index matter for reading any result and are not negotiable
afterwards:

* **It is national.** Both candidate NYC-local components were built and both
  were rejected on measurement (`PAPER_MASTER.md` §4.3): the Google Trends NYC
  series is censored on **42.6% of days overall, rising from 26% in 2020 to 71%
  in 2024**, and the NYC Wikipedia basket cannot be both local and disjoint from
  the national one — 67% of its views come from three articles already in the
  national basket, and Eric Garner alone is 61%. So the study tests whether
  *national* attention moves *New York* demand. **New Yorkers' own attention
  cannot be separately identified**, and no claim may imply otherwise.
* **Its precision degrades over the decade.** The two attention indicators
  correlate **0.90 in 2020 against 0.14 in 2024**. A null in 2021–2024 is
  therefore harder to interpret than a null in 2017–2020, and §9 treats it that
  way rather than reading it as evidence of absence.

The basket is **strict** by default: only articles where the evidence names law
enforcement as the actor. The **broad** basket, which also admits nine killings
where nothing establishes who acted (Ahmaud Arbery, Renisha McBride, Markeis
McGlockton, James Craig Anderson, Tamla Horsford, Nina Pop, James Scurlock, Carlos
Carson, Deona Marie Knajdek), is a pre-specified sensitivity. Attention to
violence *against* police — the Dallas attack of July 2016, in which five officers
were killed — is in neither basket.

## 4. The design, and why the data is split in two

The data is split into two parts. The first was explored freely. Predictions were
written down. The second was locked away and has not been looked at.

| | Window | Status |
|---|---|---|
| **Discovery** | 2017-01-01 → 2020-12-31 | explored freely — this is the design working as intended |
| **Confirmation C1 "clean"** | 2015-07-01 → 2016-12-31 **and** 2021-01-01 → 2021-05-31 | never examined |
| **Confirmation C2 "exposed"** | 2021-06-01 → 2024-12-31 | never examined |

**Why split at all.** A pattern found by looking at data is worth much less than a
prediction that survives on data nobody has seen, because the first kind of
pattern can always be found: with enough outcomes, lags, subgroups and
specifications, something always looks significant. Calling the shot before the
shot is the only cheap way to tell the two apart.

**Why C1 and C2 are separate.** They are contaminated differently and it is not a
matter of degree:

* **C1 is clean.** No COVID, and B-HEARD had not launched. The cleanest
  confirmation sample in this design runs *backward* in time, which is unusual and
  is the reason the 2015–2016 window is worth as much as it is.
* **C2 carries B-HEARD.** From 2021-06-01 New York began routing some
  mental-health 911 calls to a health-led rather than police-led response,
  precinct by precinct. **It pushes the outcome in the same direction as the
  hypothesis.** An uncontrolled 2021–2024 estimate would confuse a policy
  roll-out with a behavioural response, and the two are not distinguishable by
  looking at the total.
* C2 also carries the degraded Trends precision described in §3.

C1 starts **2015-07-01** rather than 2015-01-01 because the Wikimedia daily
pageviews API begins on that date. Before it the treatment is not noisy, it does
not exist. Those 181 days are dropped explicitly and counted in the run log.

## 5. Hypotheses, and their directions

**H1 (primary).** High-attention episodes change first-week mental-health EMS call
composition.

* **Predicted direction: a decline**, in the days immediately after an episode
  begins. This direction was fixed before the confirmation sample existed and has
  not changed (`CONFIRMATION_PLAN.md`, "What has NOT changed").
* **The test is two-sided**, ratified at Gate C §6.1 — a joint test that the eight
  first-week coefficients are all zero, against any alternative.
* Therefore: **a significant increase is a rejection of the null, and is not
  support for H1.** It would be reported as evidence against the avoidance
  mechanism and in favour of the opposite channel. Saying this now costs nothing;
  saying it afterwards would be worthless.
* The window is **event-time days 0 to 7**. The frozen text says days 0–5; the
  move to 0–7 was made when the estimator was rebuilt and is disclosed as
  deviation 3.

**H1 secondary — the B-HEARD contrast (C2 only).** Where the police had *already*
been partly removed from the mental-health response, an attention shock has less
police contact to deter. The avoidance mechanism therefore implies the first-week
effect is **attenuated** in districts with higher B-HEARD exposure — a positive
interaction coefficient if the main effect is negative. This is stated as the
direction the mechanism implies; the test is two-sided, the arm is explicitly
secondary, and a sign in the other direction is informative rather than decisive,
because B-HEARD also changes which calls are recorded at all.

**H2 (substitution) and H3 (mechanism) cannot currently be run.** H2 needs NYC
Well contact volumes; H3 needs CCRB complaint rates and stop-question-frisk
intensity. Neither dataset is in the repository. **H1 alone is therefore the
confirmation package**, which is materially weaker than the joint package the
original power note assumed. This is a gap, not a resolved deviation
(`CONFIRMATION_PLAN.md` deviation 12).

## 6. The estimator

**In plain language.** For each attention episode, line up the 14 days before and
the 14 days after in every district, and compare each day to **the day before the
news broke**. Do it within each episode separately, so one event's aftermath is
never used as the quiet baseline for another event.

**Technically.** A stacked episode event study,

```
y  ~  i(rel_day, ref = -1) + bheard_exposure  |  episode × district  +  day-of-week
```

with standard errors clustered on the **date**. Fitted twice for every outcome:
ordinary least squares on the share, and Poisson pseudo-maximum-likelihood on the
count with a log-total-calls offset.

Five specification points, each of which was wrong at some stage of this project
and each of which is now fixed and verified:

1. **Day −1 stays in the sample** as the named omitted level. Deleting it made
   every coefficient read against day −14 instead (findings S2/D1).
2. **A district-day claimed by two episode windows goes to the nearer episode**
   and is used exactly once, so no observation is a control for one event while
   treated in another. An earlier rule deleted both copies and lost 28% of window
   district-days and the entire first week of 5 of 30 episodes (S5/E4).
3. **Clustering is on the date**, because treatment is citywide and assigned at
   the date level. Clustering on district assumed independence that does not
   exist and produced error bars roughly 3× too narrow (S6, and I1 before it).
4. **The test statistic is the joint Wald χ² on the day 0–7 coefficients**, not
   their mean. A dip followed by a rebound — this project's own hypothesised
   mechanism — averages to about zero: on a planted dip-then-rebound the joint
   statistic reads **χ² = 1527** while the mean reads **+0.001** (S3/R7). The mean
   is still reported, as an effect size, and is never the test.
5. **B-HEARD exposure is in the specification from the start**, not added when it
   becomes non-zero. In C1 it is identically zero, is dropped as collinear, and
   the estimate is numerically identical to the estimator without it — checked
   arithmetically in the run, because if an all-zero column moves the answer then
   the precinct-to-district crosswalk is wrong (X6).

Verification that the estimator recovers what it should: a planted −0.010
first-week share effect comes back as **−0.01043**; a planted proportional rate
change of log(0.85) = −0.1625 comes back as **−0.1446**; 0 duplicate
district-days; all 30 test episodes retain their reference day.

## 7. Why randomization inference is the primary p-value

**In plain language.** Instead of trusting a formula for how much the estimate
would bounce around by chance, we simulate it: shuffle the episode dates to places
where nothing in particular happened, re-run the whole estimator, and see how
often pure chance produces a result as large as the real one.

**Why it is primary and not a robustness column.** On this data the formula-based
answer has already been shown to be wrong in the dangerous direction: **p = 0.019
clustered against p = 0.26 by permutation**. Anyone reporting the clustered number
would have reported a result that is not there. The asymptotic joint Wald p-value
is still printed beside the randomization p-value, and never instead of it.

**Draws: 2,000** (`config.RANDOMIZATION_DRAWS`), with the real episodes' spacing
preserved in every draw — attention episodes cluster in time, and a null built
from uniformly scattered dates would understate how often clustered dates produce
a large statistic by accident.

**The scheme has to differ between strata, and that is arithmetic, not choice.**
The calibrated draw scheme lays the real episodes' spacing down from one uniformly
drawn anchor and rejects any draw that does not fit inside the sample. C1 is two
blocks of calendar time separated by the four discovery years, and its 2021 block
holds 5 episodes spanning 139 days inside a 151-day window: once the 14-day
pre-period and 14-day post-period are reserved, 120 days remain and the sequence
**cannot fit**. Every draw would be rejected and the primary p-value for the
cleanest stratum in the design would come back empty.

So, pre-specified now rather than discovered later:

* where the calibrated scheme is feasible (one contiguous block with room), it is
  used unchanged — this is C2, with 53 days of anchor slack, and any discovery
  replication, with 190;
* otherwise placebo dates are drawn by **circular shift** over the stratum's
  *admissible* days — the days whose reference day and whole first week lie inside
  the sample, which is exactly the coverage the statistic requires. C1 has **685**
  such days and the pooled sample **1,995**, both below 2,000, so every shift is
  enumerated and the test is **exact** rather than sampled;
* the scheme used is recorded per result row, so no reader has to infer which null
  produced which p-value.

**The honest caveat, stated before the fact.** The circular-shift null is *not*
the null certified by the 200-simulation calibration. It is the same estimator and
the same statistic under a different randomization scheme, adopted because the
calibrated scheme is impossible on a gapped sample. Re-running the calibration
against a gapped synthetic sample before the freeze lifts would close the gap; if
that is not done, C1's and the pooled p-values carry this caveat in print.

## 8. The calibration precondition

Before the confirmatory run may happen at all, the estimator must be shown not to
cry wolf. It is run end-to-end on **200 synthetic panels built to contain no
effect**, carrying the real design's serial correlation and a citywide day shock.
A trustworthy test rejects about 5% of the time and its p-values are uniform.

Current artifact (`outputs/tables/null_calibration.csv`):

```
VERDICT                   CALIBRATED
empirical rejection rate  0.0500   nominal 0.05, band [0.0198, 0.0802]
median p                  0.5000
KS uniformity             p = 0.5617
AR(1) rho                 0.0482   estimated from the real (discovery) panel
n sims                    200      minimum required 200
```

Uniformity is the property that matters: a correct rejection rate with a
badly-shaped distribution still means a broken statistic. **An uncalibrated
randomization p-value is not a weak p-value, it is not a p-value**, and
`30_confirmatory_run.py` refuses to run unless this artifact reads `CALIBRATED` at
or above its own minimum simulation count. That refusal exists because the
committed `CALIBRATED` verdict was once produced by a 12-simulation smoke test
against a band wide enough to contain any estimate — a gate that could not fail
(findings S4, X3, R3).

## 9. Interpretation rules, committed in advance

These are the rules for reading the result. They are written now so that they
cannot be chosen to suit the answer.

**9.1 What each outcome means.**

| Result on the primary outcomes | Reported as |
|---|---|
| Significant **decline** in first-week mental-health share **and** count | Support for H1 in the predicted direction |
| Significant **increase** | The null is rejected in the direction **opposite** to prediction. Not support for H1; reported as evidence for the opposite channel |
| No rejection, with a confidence interval that excludes effects of interesting size | A precise null — a result, reported as one |
| No rejection, with a wide interval | Underpowered, reported as uninformative rather than as "no effect" |

**9.2 The two arms must agree.** A movement in the share arm with no corresponding
movement in the count arm is reported as **denominator-driven** and is not claimed
as a change in demand. This rule exists because the project's most eye-catching
discovery-period pattern is exactly that (§2, `PAPER_MASTER.md` §5.4).

**9.3 Placebos override.** If a placebo outcome (cardiac, injury, asthma) rejects
at a level comparable to or stronger than the primary outcomes, the primary result
is reported as **not supporting H1**, whatever its own p-value. A design that
moves heart attacks is not measuring what it claims to measure.

**9.4 When C1 and C2 disagree.** C1 is the clean stratum and is the confirmatory
test. C2 is confirmatory-with-a-confound that moves in the hypothesis's own
direction. The rules are asymmetric on purpose:

| C1 | C2 | Conclusion |
|---|---|---|
| rejects, predicted direction | rejects, same direction | **Confirmed.** The strongest available result |
| rejects | does not reject | **Confirmed in the clean stratum only.** Reported with C2's lower treatment precision (0.90 → 0.14 indicator correlation) and B-HEARD stated as the reason the two need not agree. Not generalised past the clean window |
| does not reject | rejects, predicted direction | **Not confirmation.** B-HEARD pushes C2 the same way H1 does, so a C2-only decline cannot be separated from the policy. The B-HEARD interaction arm is what speaks to it, and it is secondary |
| rejects one way | rejects the other way | **The confirmation has failed.** Reported as a failure, with both estimates in print |
| does not reject | does not reject | **The pre-specified null**, with the interval reported and §9.1's precise/underpowered distinction applied |

**The pooled estimate is descriptive.** It is reported because it was promised,
and it never overturns a stratum-level disagreement: pooling a clean sample with a
confounded one produces an average whose interpretation depends on the mix.

**9.5 Sensitivities do not replace the primary.** The July 2016 drop, the broad
basket and the `late` B-HEARD bound are reported beside the primary, never
substituted for it. A result that survives none of them is reported as fragile; a
result that survives all of them is reported as robust; the primary number is the
same number either way.

**9.6 If power says confirmation cannot deliver, that is the conclusion.** The
paper then becomes a measurement-and-design contribution with a precisely bounded
null. Both outcomes are publishable and neither is a failure — and this sentence
is in the plan (`EXECUTION_PLAN.md`, "Honest risks") rather than being invented at
the end.

## 10. Multiple testing

The pre-specified **primary family** is:

> 2 outcomes (`edp_share`, `mh_narrow_share`) × 2 arms (share OLS, count PPML) ×
> 2 strata (C1, C2) = **8 tests**, controlled by **Benjamini–Hochberg at q = 0.05**.

`REWORK_PLAN.md` finding I3 committed this project to a Benjamini–Hochberg
correction; the *family* is defined here for the first time, and the family
definition is the part that matters, because a correction is only as meaningful as
the set it is applied over.

What is deliberately **outside** the family, and why:

* **The pooled estimate**, because it is a re-description of the same eight
  observations. Including it would make the correction depend on how many times
  the same data is summarised.
* **The sensitivities** (July 2016 dropped, broad basket, `late` B-HEARD bound),
  because they are robustness readings of tests already in the family, not
  additional chances to reject.
* **The B-HEARD interaction arm**, which is secondary and reports an asymptotic
  p-value only: permuting episode dates holds district exposure fixed, so the
  randomization null does not test the cross-district contrast this coefficient
  speaks to.
* **The placebos**, which are falsification. A correction that made it *harder*
  for a placebo to reject would weaken the check, which is backwards.

Every result row carries its family membership, so a reader who disagrees with
this definition can recompute the correction from the published table.

## 11. What is, and is not, pre-specified — the ledger

### 11.1 Pre-specified in the original frozen text

The direction of H1 (a decline); randomization inference as the primary p-value;
59 community districts; date-clustered inference; the discovery/confirmation split
and its dates; the frozen episode list, kept byte-identical.

### 11.2 Deviations, disclosed and dated

`CONFIRMATION_PLAN.md`'s addendum lists **15** deviations from the frozen plan.
**Twelve are recorded as decided blind to every confirmation-period outcome** —
the episode construct and threshold, the test window, the index composition, the
Wikipedia rename correction, the basket selection rule, the basket construct, the
Wikidata scope transport, the estimator, the episode list consumed, the outcome
definition, and the superseding of the original power note.

Being blind is not the same as being harmless. Some of these are large. The
Wikipedia rename correction alone changed every value of the index and therefore
every episode date: **93.5% of Alton Sterling's attention was being discarded**,
because Wikimedia does not carry pageviews across a page move and the pre-rename
title held 1,861,004 views against the canonical title's 128,855. The episode
construct changed from "attention was high for a stretch" to "attention to a
specific killing began on day X" because the old rule produced a single 184-day
episode swallowing the entire 2020 summer, hiding at least eight distinct shocks
including Daniel Prude — a Black man killed during a mental-health crisis, and the
most on-hypothesis event in the dataset. These are corrections a reader should
want made; they are also changes to a pre-registered construct, and they are
listed as such.

### 11.3 The three rows not marked "decided blind"

* **Row 12 — H2 and H3 are not runnable.** Marked "n/a": a missing dataset is not
  a decision.
* **Row 14 — decisions taken after discovery results had been seen.** Three of
  them: **the H1 framing**, **the choice of control group for the
  difference-in-differences**, and **the Q1 protest-disruption hypothesis**, which
  was formulated from discovery-period heterogeneity. These are not blind and are
  not defended here as though they were. A reader is entitled to discount them,
  and the confirmatory run in this note does not rest on any of the three: H1's
  *direction* predates them, and the difference-in-differences is not part of the
  confirmatory package.
* **Row 15 — the two freeze incidents.** These are accesses, not decisions, and
  are set out below because one of them carried a decision with it.

### 11.4 The freeze incidents, and the one specification decision that is not blind

**F1 (2026-09-10).** An audit agent computed the citywide mental-health call share
by year for 2005–2026, including confirmation years, to demonstrate that one
outcome file had no freeze guard. Narrow — a citywide annual aggregate, no district
variation, no episode alignment, no test of H1 — but real.

**F2 (found 2026-09-11, previously unrecorded).** Establishing when each EDP-family
call type was born was done by querying the NYC OpenData source API directly, which
no file-level guard can see. What was read: first-record timestamps and whole-period
totals per call type; citywide monthly counts across the 2021-05/06 boundary;
annual EDP-family totals; and **precinct-level EDPM counts for June 2021, comparing
the three B-HEARD pilot precincts against the rest**. That last item is
district-level variation inside the confirmation window, compared across the
B-HEARD boundary.

**And a specification decision was taken on it:** EDPM was retained in the EDP
family because the comparison refuted the claim that it is the B-HEARD routing
code. The decision is defensible on other grounds — a routing code would
concentrate in pilot precincts and EDPM does not, and it appears citywide from its
first day — but "defensible on other grounds" is a judgement for the supervisor,
not a reason to leave an access unrecorded. **So the composition of the EDP family,
which is the primary outcome, is not fully blind.** That is the single most
material qualification in this note.

How F2 went unnoticed for a day is worth recording too: it produced a finding full
of confirmation-period numbers and nobody asked where they came from. **The numbers
were read as evidence rather than as an access.**

Both structural gaps are now closed in code — outcome files outside the guard's
coverage, and the source API that no file guard could see — and the posture taken
since is to hold the line strictly rather than take a third access, at the stated
cost that a genuine problem inside the 2015–2016 window will be **disclosed but
not fixable** once found.

### 11.5 First specified in this note, blind but not in the frozen text

These are commitments made on 2026-09-12, with `FREEZE_ACTIVE` still `True` and no
confirmation outcome examined. They are blind; they are **not** in the original
frozen record, and they should be read as decisions of this document:

* the **C1 / C2 stratification** and the treatment of C1's two blocks as one
  stratum (the strata themselves come from `EXECUTION_PLAN.md` Phase I);
* the **interpretation rules** in §9, including the asymmetric C1/C2 rule and the
  requirement that both arms agree;
* the **multiple-testing family** in §10;
* the **circular-shift randomization scheme** for gapped strata, and its caveat;
* the **B-HEARD interaction arm** as a secondary, direction-predicted test;
* the decision to run the confirmatory analysis as a **single sealed script**
  written before the freeze lifts (`scripts/30_confirmatory_run.py`).

### 11.6 Known limitations that no pre-specification can remove

1. The treatment index is **national**; local attention is not separately
   identifiable (§3).
2. The victim registry omits events the paper is about, and the omissions run
   *with* the hypothesis: Daniel Prude, Sandra Bland, Marvin Scott, Javier Ambler
   and Leneal Frazier are absent from Mapping Police Violence itself, and they are
   disproportionately in-custody, restraint and mental-health-crisis deaths
   (finding T9).
3. Wikipedia pageviews do not exist before 2015-07-01. A hard floor.
4. B-HEARD adoption dates are **17 of 31 low confidence**, which is why exposure
   is carried as bounds rather than a point date, and why a result that flips
   between the bounds must be reported as depending on data we do not have.
5. The EDPC recode begins mid-2018, inside the discovery window.
6. H1 is the whole confirmation package (§5).

## 12. What would make this note worthless

Stated plainly so that it can be checked against what actually happens:

* running the confirmatory analysis and *then* adjusting any of §5, §6, §9 or §10;
* reporting the share arm without the count arm, or either stratum without the
  other;
* dropping the placebos from the write-up if they are inconvenient;
* re-running the analysis with a different specification and reporting the second
  run;
* describing this document as a pre-registration.

The mechanism against the first four is that the analysis is a single sealed
script, `scripts/30_confirmatory_run.py`, written and committed **before**
`config.FREEZE_ACTIVE` is set to `False`. It refuses to run while the freeze
holds, refuses to run without a `CALIBRATED` verdict on the null calibration, and
refuses to overwrite a result that already exists. Lifting the freeze is then one
flag and one command, with nothing left to decide — because *after* is when
improvisation becomes p-hacking.

The mechanism against the fifth is this document's own first paragraph.
