# Comparable Work, and What It Means for This Project

A review of the literature this project sits inside: what those studies did, what they
found, how our design differs, and what we should take from them to get to a complete,
defensible research delivery.

**Provenance.** Entries marked **[full text]** were read in full or in substantial part.
Entries marked **[abstract]** were read from the abstract, publisher summary, or a
citation inside another paper that we did read. Numbers are quoted as those sources
report them. Full citations are in §8.

---

## 1. The four literatures this project sits inside

Our question — *does public attention to police violence move acute mental-health
service demand?* — sits at the intersection of four bodies of work that mostly do not
cite each other. Positioning the paper means being explicit about which one we are
contributing to.

### Strand A — Population mental health effects of police violence (survey-based)

This is the strand that gave the project its premise: police killings damage the mental
health of people who were not present.

**Bor, Venkataramani, Williams & Tsai (2018), *The Lancet*** — the canonical paper.
BRFSS 2013–2015, 103,710 Black respondents; exposure is police killings of *unarmed*
Black Americans in the respondent's own state in the three months before interview;
outcome is self-reported poor mental health days in the past 30. Identification comes
from quasi-random timing: respondents interviewed shortly after a killing are compared
with respondents in the same state interviewed shortly before, with state and time
controls. Effects appear only for killings of unarmed victims; no effect for killings of
armed victims, and no effect on white respondents — two internal placebo tests that do a
lot of the paper's persuasive work. The authors scale their estimate to roughly 55
million excess poor mental health days per year among Black Americans. **[abstract +
publisher summaries]**

**Nix & Lozada (2021), *Police Practice & Research*** — the reassessment. They argue 93
cases in the Mapping Police Violence database were miscoded as "unarmed" (about 30% of
the relevant cases); recoding or dropping them attenuates Bor et al.'s estimate to
statistical non-significance. Bor et al. published a reply disputing the recoding. **The
lesson for us is not who won.** It is that the single most contested part of that
literature is *how the exposure variable was constructed* — and our exposure variable
(raw daily tweet counts, z-scored) has had less scrutiny than theirs. §5.5. **[abstract]**

**Curtis et al. (2021), *PNAS*** — the same BRFSS outcome, but the exposure is a curated
set of 49 *publicized* incidents: police killings, decisions not to indict or convict,
and hate-crime murders. This is the closest antecedent to our conceptual move — the
exposure is publicity, not incidence. They still work at the level of discrete named
events rather than a continuous attention series. **[abstract]**

**Sewell & Jefferson (2016) and Sewell, Jefferson & Lee (2016)** — NYC-specific,
neighbourhood-level: living in a neighbourhood where pedestrian stops more often become
invasive is associated with worse self-rated health and higher psychological distress,
with distinct patterns by gender. Cross-sectional, survey-based (NYC Community Health
Survey nested in Stop-Question-Frisk data), so no temporal identification — but it
establishes the NYC neighbourhood as a meaningful unit for this outcome, which is the
unit we use. **[abstract]**

### Strand B — Administrative acute-care utilization (the closest relatives)

This is where our paper actually belongs, and where our contribution has to be defended.

**Das, Singh, Kulkarni & Bruckner (2020), *Social Science & Medicine*** — the nearest
prior work. Exposure: police killings of unarmed African Americans. Outcome:
depression-related ED visits per 100,000, among African Americans. Panel of 75 counties
across 5 states, 2013–2015, 2,700 county-months. Linear county fixed effects,
controlling for number of hospitals and violent-crime arrests. Finding: **+11% in
depression-related ED visits in the concurrent month and the three months following**.
**[abstract + publisher summary]**

> This is the study to beat, and the comparison is favourable in one specific way:
> **they work at county-month resolution, so they cannot say anything about timing
> within a month.** "Concurrent month plus three months" is the finest temporal claim
> their design supports. Our CD-day panel is roughly 30× finer in time and finer in
> geography. If our project has a defensible headline contribution, it is *the shape of
> the response inside the first month* — which means the lag profile has to be estimated
> properly (§5.3), because it is the whole contribution.

**Packard, Verzani, Finsaas et al. (2024), *Social Psychiatry and Psychiatric
Epidemiology*** — NYC, and the closest model for our heterogeneity analysis. 180 ZCTAs ×
month, 2006–2014 (19,440 ZCTA-months). Exposure: monthly rate of policing incidents
(stops, arrests, summonses) per 1,000 residents. Outcome: psychiatric hospitalization
days among youth 10–24, from SPARCS discharge records. **Multilevel negative binomial
with a log-population offset**, random ZCTA intercepts and slopes, ACS covariates, and
**policing × %Black-tertile interactions**. Result: one additional policing incident per
1,000 residents → 0.3% more psychiatric hospitalization days (IRR 1.003, 95% CI
1.001–1.005), **stronger in the highest-%Black tertile** (IRR 1.005, 1.000–1.009).
**[full text]**

> Note the direction: their gradient runs *toward* higher-%Black neighbourhoods. Ours
> runs away from them. §5.7 is about that.

**Bruckner-adjacent George Floyd work (2024), *SSM–Mental Health*** — Black ED visits
diagnosed as schizophrenia/psychosis rose by a reported 4.26 percentage points in June
2020, framed as an empirical test of the "protest psychosis" thesis. Monthly resolution,
single event. **[abstract]**

**"An EMS-Based Crisis Response Model for Mental Health–Related EMS Calls" (2026),
*Psychiatric Services*** — **the only study we found that uses our exact dataset.** NYC
EMS Incident Dispatch Data, January 2019–December 2024, aggregated to monthly rates at
the level of 76 NYPD precincts (31 of which adopted B-HEARD). Staggered-adoption
difference-in-differences. Finding: significant reductions in mental-health EMS call
rates in adopting precincts, emerging roughly a year after implementation, statistically
detectable by March 2023. **[abstract]** Two consequences for us:

1. **It validates the data source** for exactly this outcome, and gives us a citable
   precedent for classifying "mental health–related EMS calls" from dispatch codes.
2. **It defines a hard boundary on our sample.** B-HEARD launched June 2021 and changes
   how mental-health 911 calls are dispatched and recorded. Our analysis window ends in
   2020, so we are clean — but we must say so explicitly, because any reviewer who knows
   this dataset will ask, and it is the reason we cannot simply extend the panel to 2025
   when the Twitter series is refreshed.

### Strand C — Call-for-service behavior after police violence (the threat to our outcome)

This strand is not about mental health at all, and it is the most dangerous one for us,
because it says our denominator moves.

**Desmond, Papachristos & Kirk (2016), *American Sociological Review*** — Milwaukee, the
publicized beating of Frank Jude. Interrupted time series on police-related 911 calls,
controlling for crime, prior call patterns and neighbourhood characteristics. Residents —
especially in Black neighbourhoods — became far less likely to report crime; the effect
persisted **over a year**, a net loss of roughly **22,200 calls**. **[abstract]**

**Ang, Bencsik, Bruhn & Derenoncourt (2024), NBER WP 32243** — 13 major US cities around
George Floyd's murder. Their innovation is a denominator that civilians cannot suppress:
the **call-to-shot ratio**, 911 calls divided by ShotSpotter-detected gunshots, which
separates *willingness to engage police* from *underlying crime*. Daily data, 73 days
before and 73 days after, Newey–West standard errors plus **randomization inference
against randomly chosen placebo dates**. Findings: call-to-shot ratio down **>50%**;
gunshots more than doubled; **911 call volume down ~25%, staying depressed through the
end of 2020**. Declines were **comparable across majority-white, majority-Black and
majority-Hispanic neighbourhoods** — explicitly contrary to the Strand A/D pattern where
effects concentrate in Black and Hispanic communities. They attribute the size of their
effect versus Mikdash & Zaiour (2022), who find 3–6% gunfire effects and no call-volume
change for lower-profile Minneapolis killings, to **salience and media attention** — and
name it as the natural area for future work. **[full text]**

> That last sentence is, almost word for word, an invitation to write our paper. It is
> the single best framing hook available to us: *Ang et al. document that the aggregate
> response scales with salience but cannot measure salience; we have a daily salience
> series.*
>
> It is also our biggest threat. Our outcome is `mh_calls / total_calls`. If awareness
> spikes cause total EMS call volume to fall — and this literature says exactly that
> happens to 911 volume — then our share rises with no change whatever in the number of
> people in crisis. §5.2.

**Ang (2021), *QJE*** — LA public high school students; hyperlocal dynamic
difference-in-differences comparing students living within 0.50 miles of a police killing
to those 0.50–3 miles away. Persistent falls in GPA, higher incidence of emotional
disturbance, lower high-school completion and college enrolment; **driven entirely by
Black and Hispanic students, largest for killings of unarmed victims**. Standard errors
clustered by ZIP code, with robustness to multiway clustering (Cameron, Gelbach & Miller
2011) and to cohort-by-cohort event studies to avoid contaminated comparisons in
staggered designs. **[full text]**

**Legewie & Fagan (2019), *ASR*** — NYC, Operation Impact police surges; DID off the
staggered timing of surges across neighbourhoods; ~250,000 adolescents. Test scores fall
for African-American boys, no discernible effect for African-American girls or Hispanic
students. **[abstract]** The relevant thing for us is structural: **this is the NYC
template for getting causal identification out of a citywide policy shock — by exploiting
the fact that it did not hit every neighbourhood at the same time.** Our exposure hits
every district on the same day, which is precisely our identification problem (§5.1).

### Strand D — Measuring collective attention

**Wu, Gallagher, Alshaabi et al. (2023), *PLOS ONE*** — "Say their names." Uses the
Storywrangler API over a 10% sample of English tweets to track victims' names as 2-grams
from 2009 onward, across 3,737 police-involved deaths of Black victims from Fatal
Encounters. Two details matter enormously for us:

- They use **relative frequency** — a name's usage normalized by total daily word volume
  — explicitly because raw counts confound attention with fluctuations in overall
  platform activity. We use raw counts (§5.5).
- **George Floyd's name became the 7th most-used 2-gram on Twitter on 29 May 2020, four
  days after his death.** That is *exactly* our highest-awareness event day
  (`awareness_z = 20.43`), derived from a completely independent data pipeline. This is a
  free external validation of our awareness series and we should cite it as one.

They also document the decay: after 2014 events, attention to names decayed by an order
of magnitude after the initial spike; after Floyd it declined only 33%, i.e. attention was
unusually persistent in mid-2020. **[full text]**

**Weitzel, Chew, Miller et al. (2023), *JMIR Public Health & Surveillance*** — Crisis Text
Line conversations after the Uvalde school shooting. SARIMA model trained on three months
of pre-event data forecasts the counterfactual; actual volume is compared against it.
**The spike peaked the day after the shooting and was back inside the forecast interval
by day 4.** **[full text]**

> This is the sharpest available benchmark for what a collective-trauma response to
> acute help-seeking services *looks like in time*: immediate, and over within a week.
> Our result — nothing at lags 0–3, a spike at lag 7 — is the opposite shape. That is
> either our most interesting finding or our most likely artifact, and §5.3 argues we
> cannot currently tell which.

---

## 2. Reference table

| Study | Exposure | Outcome | Unit | Design | Headline |
|---|---|---|---|---|---|
| Bor et al. 2018 | Police killings of unarmed Black people, state, prior 3 mo | Poor mental health days (BRFSS) | Person | Quasi-experimental interview timing | Adverse effect; null for armed victims and for white respondents |
| Nix & Lozada 2021 | Same, recoded armed/unarmed | Same | Person | Replication | Attenuates to non-significance |
| Curtis et al. 2021 | 49 *publicized* anti-Black violence incidents | Poor mental health days (BRFSS) | Person | Event-based | Adverse effect |
| Das et al. 2020 | Police killings of unarmed African Americans | Depression ED visits /100k | County-month | County FE | +11%, concurrent month + 3 months |
| Packard et al. 2024 | Policing incidents /1,000 residents | Psychiatric hospitalization days, ages 10–24 | ZCTA-month (NYC) | Multilevel NB, pop. offset, ×%Black | IRR 1.003; **stronger** in highest-%Black tertile |
| B-HEARD study 2026 | B-HEARD program adoption | MH-related EMS calls | Precinct-month (NYC) | Staggered DID | Reductions ~1 yr post-adoption |
| Desmond et al. 2016 | One publicized beating | Police-related 911 calls | Neighbourhood, time series | Interrupted time series | −22,200 calls, >1 year |
| Ang et al. 2024 | George Floyd's murder | Call-to-shot ratio; 911 volume | City-day, 13 cities | Time-series break, Newey–West + randomization inference | Ratio −50%+; **volume −25%**, months |
| Ang 2021 | Police killing within 0.50 mi | GPA, emotional disturbance, completion | Student | Hyperlocal dynamic DID | Persistent harm; Black/Hispanic only |
| Legewie & Fagan 2019 | Operation Impact surges | Test scores | Student × neighbourhood (NYC) | Staggered DID | Harm to African-American boys |
| Wu et al. 2023 | — | Collective attention (relative tweet frequency) | Name-day | Descriptive | Floyd peak = 29 May 2020, day +4 |
| Weitzel et al. 2023 | Uvalde shooting | Crisis Text Line volume | Day | SARIMA counterfactual event study | Peak day +1, over by day +4 |
| **This project** | **Daily citywide Twitter volume, z-scored (continuous)** | **MH share of EMS calls** | **CD-day (NYC), 2017–2020** | **Distributed lag, CD FE, clustered by CD** | **β₇ = 0.00139 (SE 0.00038)** |

---

## 3. Where our design sits

Reading down the table, our design is distinctive on three axes and weak on a fourth.

**Temporal resolution — strongest axis.** Every administrative-outcome study in Strand B
works at the month. We work at the day. Das et al. can say "the effect is present in the
concurrent month and three months after"; nobody in this literature can currently say
whether the acute response peaks on day 1, day 7, or day 20. That question is
answerable with our data and is not answerable with theirs.

**Exposure as a continuous attention series — genuinely novel.** Strand A and B code
discrete events (a killing happened / didn't; an incident was publicized / wasn't).
Strand D measures attention beautifully but never links it to a health outcome. We are
the only design that puts a *continuous, daily, intensity-graded* attention measure on the
right-hand side of a health-utilization regression. Ang et al. (2024) explicitly name
this — the mediating role of salience — as the open question their own design cannot
answer.

**Outcome — pre-hospital, not hospital.** Strand B measures people who reached an ED or
were admitted. EMS dispatch is upstream of both: it captures the moment a crisis becomes
a 911 call. That is a genuinely different margin and closer in time to the event.

**Identification — weakest axis, and this is the whole problem.** Every other study in
the table gets its leverage from *cross-sectional* variation in exposure: distance to a
killing (Ang), which precinct adopted (B-HEARD), which neighbourhood was surged (Legewie
& Fagan), which state had a killing (Bor), which county (Das), policing rate by ZCTA
(Packard). **Our awareness measure is citywide: every community district gets the
identical value on the identical day.** After month×year fixed effects, our main
coefficient is identified purely off day-to-day wiggle in a single national time series,
in a panel whose 85,139 rows contain roughly 1,460 independent draws of the treatment.
This has consequences that run through most of §5.

---

## 4. What is genuinely new here

Stated as claims we could defend in a seminar:

1. **First study to link public attention to police violence to pre-hospital emergency
   demand.** Strand B stops at the ED door. No prior work uses EMS dispatch as the
   outcome for this exposure.
2. **First daily-resolution estimate of the response profile.** The entire prior
   administrative literature is monthly. Whatever the true within-month shape is, no one
   has estimated it.
3. **First use of a continuous attention series rather than a binary event indicator**,
   answering the question Ang et al. (2024) leave open about the role of salience.
4. **A test the literature has never run.** Strand C says willingness to call 911 falls
   after police violence; Strand A/B says distress rises. Those two forces act in
   opposite directions *on the same measurement instrument*, and no study has separated
   them. We can — see §5.7 — because our data distinguish mental-health calls that
   typically summon police (EDP) from those that typically do not (overdose, poisoning).
   That is arguably a better paper than the one we are currently writing.

---

## 5. Where the current design falls short of the field's standard

Each item is anchored to code and paired with the paper that shows the fix. These are
ordered by how much they threaten the headline result.

### 5.1 The standard errors are clustered on the wrong dimension

`scripts/03_regression_analysis.py:35` clusters on `cd_int`. But `awarez_lag*` is
citywide — constant across all 71 districts within a day. Clustering by district assumes
independence *across* districts, and a common daily shock violates that assumption
exactly. The residuals of 71 districts on the same day are correlated by construction;
the effective number of independent treatment observations is the number of days
(~1,460), not the number of district-days (85,139). Our reported SEs are very likely too
small, and the p < 0.001 headline is the thing most exposed.

**Fix, in order of preference.** (a) **Driscoll–Kraay** standard errors, which are built
for precisely this case — panels with large T, cross-sectional dependence from common
shocks, and serial correlation. (b) Two-way clustering on district *and* date (Cameron,
Gelbach & Miller 2011, as used for robustness in Ang 2021). (c) A block bootstrap over
dates. (d) **Randomization inference**: re-estimate against randomly chosen placebo event
dates, which is what Ang et al. (2024) do for their aggregate time-series break and report
alongside Newey–West. Whichever we pick, report the main table with *all* of them, and
lead with the most conservative. If the result survives Driscoll–Kraay, it is a much
stronger paper than it is today. See Bertrand, Duflo & Mullainathan (2004) and Abadie,
Athey, Imbens & Wooldridge (2023) for the general argument.

### 5.2 The outcome is a share, and this literature says the denominator moves

`mh_share = mh_calls / total_calls`. Ang et al. (2024) find 911 call volume fell ~25%
after George Floyd's murder and stayed down for months; Desmond et al. (2016) find a
year-long call deficit after a single publicized beating. If awareness spikes depress
non-mental-health EMS calls even modestly, our share rises **mechanically**, with no
change in the number of people in crisis. Our May–June 2020 observations sit inside
exactly the window Ang et al. document.

The existing placebo on `total_calls` is the right instinct but too weak to carry this:
it is a single OLS-on-levels test (`scripts/03_regression_analysis.py:29-30`, rescaled by
100) with the same mis-specified clustering as the main model, and a null there is as
easily low power as it is evidence.

**Fix.** Promote the **count** model to primary, as Das et al. and Packard et al. both
do. `scripts/22_negative_binomial_regression.py` already exists — but change the
exposure. It currently offsets by `total_other_calls`, which re-introduces the very
denominator we are trying to escape. Offset by **district population** instead (Packard
et al. use log population 10–24). Then report three outcomes side by side in the main
table: mental-health call count, non-mental-health call count, and the share. If the
count rises and non-MH calls are flat, we have a real effect. If the count is flat and
only the share moves, we have Ang et al.'s denominator, and the honest paper is about
that.

### 5.3 "The effect is at 7 days" is not currently identified

Two separate problems compound here.

**Omitted adjacent lags.** `scripts/02_merge_awareness.py:48` builds all 29 lags, but
`scripts/03_regression_analysis.py:17` fits only `[0, 1, 2, 3, 7, 14, 21, 28]`. Lags 4, 5
and 6 are excluded. Awareness is strongly serially correlated — a spike persists for
days, which is precisely what Wu et al. document — so **β₇ absorbs the effect of days 4–6**.
The defensible statement from this specification is "somewhere in days 4–7," not "at day
7." Since the within-month response shape is our central contribution (§3), this is not a
detail; it is the contribution.

**Multiple comparisons.** Eight lags are tested and exactly one is significant. Under the
null, the chance that at least one of eight independent tests clears α = 0.05 is about
34%. The result is currently indistinguishable from that.

**Fix.** (a) Estimate the **full 0–28 lag profile**, not a subset. (b) Report the
**cumulative effect** (Σβ over 0–7 and 0–14) with a joint F-test as the headline number —
cumulative effects are robust to how the response is distributed across adjacent days,
which is the entire problem here. (c) Apply **Romano–Wolf stepdown** p-values across the
lag family. (d) Better still, replace the unconstrained lag set with a **constrained
distributed-lag basis** — Gasparrini's DLNM framework, standard in daily-time-series
health epidemiology, models the lag dimension with a spline instead of 29 free
parameters. It is far more efficient, it produces the smooth exposure–lag–response
surface that is the natural figure for our contribution, and it comes with an established
model-selection procedure (AIC/BIC over basis choices).

**And a substantive point to confront directly.** Weitzel et al. find crisis-line volume
peaks at day +1 and is gone by day +4. Das et al. find effects in the concurrent month.
A null at days 0–3 and a spike only at day 7 is not what the literature predicts. If it
survives (a)–(d), it needs a mechanism: EMS activation is a higher-threshold behavior
than texting a crisis line and may reflect accumulating deterioration rather than acute
distress; our exposure is dated to the *attention peak*, which Wu et al. show already lags
the incident by ~4 days, so day 7 post-attention is roughly day 11 post-incident. That
argument is available, but it has to be made, not assumed.

### 5.4 The two-way fixed effects model is unidentified, and the DID is not a DID

**`scripts/25_twoway_fixed_effects.py:142`** puts `C(date_str)` in the same formula as the
citywide `awarez_lag*` terms. Date fixed effects absorb *all* variation in a citywide
daily variable — the design matrix is rank-deficient, and `sm.OLS`'s pseudo-inverse
returns a minimum-norm solution rather than an error. **Whatever numbers that model
reports for the awareness coefficients are meaningless.** The weekly-bin variant a few
lines later (`C(year_week)`) *is* identified, since the lags still vary across days within
a week, and it is a genuinely informative check — that one should be reported and the
daily-date-FE one dropped.

**`scripts/16_difference_in_differences.py:127`** fits `mh_share ~ treated * post + ...`
where `treated = (awareness_z > 1.5)` at line 72 and `post = (event_time >= 0)` at line
115. Both are functions of the *same* citywide date variable; every district is treated on
the same days; there is no untreated comparison group. This is a threshold contemporaneous
effect with an interaction term, not a difference-in-differences. The README currently
presents its coefficient (0.00205) as confirmation "using an alternative identification
strategy" — it is the same time-series variation relabelled, and a reviewer who reads the
code will say so. Either build a real control group (see §6, Legewie & Fagan) or rename
it honestly to "threshold event-window estimate."

### 5.5 The awareness measure needs the treatment Wu et al. give theirs

`scripts/02_merge_awareness.py:39` z-scores raw summed daily tweet counts. Three problems:

- **No normalization for platform volume.** Wu et al. use relative frequency precisely
  because total Twitter activity trends and fluctuates; raw counts confound "more
  attention to police violence" with "more tweeting in general." Divide by total daily
  tweet volume, or at minimum detrend the series.
- **A 20.43-SD maximum.** A z-score with a single observation twenty standard deviations
  out is not a standardized variable in any useful sense; a linear-in-z coefficient is
  dominated by the George Floyd period. The "per 1 SD increase" interpretation in the
  README and paper does not describe anything that happens in most of the data.
- **A look-ahead leak.** `scripts/02_merge_awareness.py:60-63` builds
  `tweet_count_3day_rolling` with `center=True`, so `log_3_day` at day *t* includes day
  *t+1*. That variable is the **main predictor** in the negative binomial model
  (`scripts/22_negative_binomial_regression.py:85`). Any contemporaneous coefficient on
  it is contaminated with future information. (Same flag for `mh_calls_3day_rolling`,
  also centered, if it is ever used as an outcome.) Use a trailing window.

**Fix.** Normalize by platform volume; make the **rank/quintile** specification
(`scripts/23_quantile_analysis.py`) or a log transform the primary form rather than a
robustness check; use trailing windows; and report the estimate **excluding May–June
2020** to demonstrate the finding is not one event wearing a distribution's clothes.

### 5.6 2020 is doing too much work, and month×year FE does not absorb it

Our window ends in a year that contains, simultaneously: the COVID-19 emergency and its
waves, an EMS system under unprecedented load, mass protests, curfews, and the largest
attention spike in the series. Month×year fixed effects absorb *level* shifts by calendar
month; they do not absorb day-to-day COVID dynamics, and June 2020's month dummy cannot
distinguish "protest" from "pandemic" from "attention."

**Fix.** Follow Ang et al. (2024), who restrict to the post-COVID-emergency period and
control for residential time from Google mobility data. We should add daily NYC COVID
case/hospitalization counts and mobility controls, and — the strongest single robustness
test available to us — **report the estimate on 2017–2019 alone**. If the effect holds
without 2020, the paper is essentially bulletproof on this point. If it does not, that is
a finding worth reporting honestly, and it reframes the paper as being about the George
Floyd period specifically, which is still publishable and is what Ang et al. did.

### 5.7 The heterogeneity result runs against the literature — which is an opportunity, not a problem

Our gradient (effects strongest in high-%White and high-%Asian districts, null to negative
in the highest-%Black quartile) runs opposite to Bor et al., Curtis et al., Ang 2021,
Legewie & Fagan, and Packard et al., all of whom find effects concentrated in Black and
Hispanic populations. `docs/EMS_IMPLICATIONS_SUMMARY.md` currently converts this into an
operational targeting rule — allocate more resources to high-%White/Asian districts —
which is the one reading we should not lead with, because it treats *measured EMS calls*
as if it were *distress*.

Strand C gives the alternative reading, and it is well-supported: after publicized police
violence, people in the most affected communities **call 911 less**. Desmond et al. and
Ang et al. document this directly. If distress rises and willingness to summon an
emergency response falls, the two effects cancel — most completely in the communities
where both are strongest. A null in high-%Black districts is then a *measurement*
result about help-seeking, not a *health* result about distress.

Ang et al. (2024) are also a useful precedent for not panicking: they find call-to-shot
declines comparable across majority-white, majority-Black and majority-Hispanic
neighbourhoods, explicitly noting the contrast with the Black/Hispanic-concentrated
results in Ang (2021) and Legewie & Fagan (2019). A reverse or flat gradient is not
disqualifying in this literature.

**And here is the test, using only data we already have.** Split mental-health calls by
whether the dispatch type typically summons a police co-response. `EDP` (emotionally
disturbed person) calls bring officers; `OD`, `ODC`, `POISON`, `DRUG` calls generally do
not. Under the help-seeking-suppression hypothesis, EDP calls should fall *relative to*
overdose calls in high-%Black districts after awareness spikes; under the pure-distress
hypothesis, both rise together. **This is a clean, novel test that distinguishes the two
mechanisms, and no one in this literature has run it.** It requires no new data, and it
is a stronger contribution than the current headline.

Two supporting fixes: (a) run the heterogeneity model **with date fixed effects** — the
interaction terms have genuine cross-sectional variation and are identified even when the
main effect is not (`scripts/12_heterogeneous_effects.py:101` currently uses CD FE and
month×year only), which makes the heterogeneity the most credibly identified part of the
whole project; (b) replace the 2010 Census demographics with **ACS 2015–2019 five-year
estimates**, as Packard et al. do — 2010 data for a 2017–2020 window is a gratuitous
weakness in a decade of NYC gentrification.

### 5.8 Smaller items

- **Exposure classification needs a citation.** Our 11 mental-health dispatch codes are a
  judgment call, and the substance-related codes (`OD`, `ODC`, `POISON`, `DRUG`) are the
  contestable half. The B-HEARD paper classifies mental-health EMS calls from this same
  dataset — align with it or justify the divergence, and report the main result with and
  without substance-related calls as a headline robustness row, not a footnote.
- **The ≥5 calls/day restriction** should get a sensitivity curve (0, 3, 5, 10) in the
  appendix rather than an assertion that it does not matter.
- **`docs/research_paper.tex` was deleted** in commit `b53746f` but is still referenced
  twice in the README. The paper currently has no editable source.
- **Internal inconsistencies** to reconcile before anything is submitted: baseline MH
  calls per district-day is 8.4 in `RESULTS_INTERPRETATION.md` and 7.9 in
  `EMS_IMPLICATIONS_SUMMARY.md`; the citywide scaling uses 59 districts while the panel
  has 71.

---

## 6. What to borrow, paper by paper

| From | Borrow |
|---|---|
| **Ang et al. 2024** | The framing hook (they name salience as the open question); randomization inference over placebo dates; a denominator civilians cannot suppress; the finding that call *volume* falls — which is our §5.2 threat and our §5.7 opportunity |
| **Bor et al. 2018** | Internal placebo design: their armed/unarmed contrast is the model. Our analogue is high-profile *police* violence vs. equally-covered non-police violent news — if only the former moves calls, the interpretation tightens enormously |
| **Nix & Lozada 2021** | The warning: exposure construction is what gets attacked. Pre-empt it by reporting our estimate under several attention measures |
| **Das et al. 2020** | Counts per capita as the outcome; the monthly benchmark our daily estimate should reproduce when aggregated — a good consistency check to report |
| **Packard et al. 2024** | Negative binomial with population offset; interaction-with-racial-composition structure; ACS rather than 2010 Census |
| **B-HEARD study** | Dispatch-code classification precedent; the post-2021 sample boundary; precinct-level aggregation as an alternative geography for robustness |
| **Legewie & Fagan 2019** | The NYC template for getting cross-sectional identification out of a citywide shock. Our candidate: exposure varies across districts through *who is watching* — differential Twitter penetration, or distance to protest sites, or district-level proximity to the incident when it is local (Eric Garner, Delrawn Small) |
| **Wu et al. 2023** | Relative-frequency normalization; the independent confirmation that 29 May 2020 is the attention peak; attention-decay dynamics to motivate the lag structure |
| **Weitzel et al. 2023** | The SARIMA-forecast counterfactual as an alternative event-study design that needs no control group — well suited to a citywide shock; and the day+1/day+4 benchmark our lag profile must be compared against |
| **Gasparrini 2010/2014** | The constrained distributed-lag basis, and the exposure–lag–response surface as our central figure |
| **Desmond et al. 2016** | Interrupted time series with crime and prior-call controls; the long-duration effect suggests we should look past 28 days |

---

## 7. Plan to a full research delivery

**Stage 1 — Restore the pipeline (blocking).** Return the EMS dispatch CSVs and both
tweet-count CSVs to `data/raw/`; rerun `run_analysis.py` through scripts 21–26. Nothing
below is possible until the parquet and output tables exist again. Restore or rewrite
`research_paper.tex`.

**Stage 2 — Fix inference and the outcome (this is where the paper is won or lost).**
Driscoll–Kraay and two-way-clustered standard errors plus randomization inference (§5.1);
count models with a population offset, reporting MH calls, non-MH calls and share
together (§5.2); full 0–28 lag profile with cumulative effects and Romano–Wolf correction
(§5.3); delete or repair the unidentified TWFE model and rename the "DID" (§5.4). At the
end of this stage we will know whether we have a result. **Everything downstream should
wait for that answer.**

**Stage 3 — Harden the exposure.** Platform-volume normalization, trailing windows, log
and quintile forms as primary, estimates with and without May–June 2020, COVID and
mobility controls, 2017–2019-only estimate (§5.5, §5.6).

**Stage 4 — Make the heterogeneity the contribution.** Date fixed effects in the
interaction models; ACS demographics; and the EDP-vs-overdose split test that separates
distress from help-seeking suppression (§5.7). This is the part of the project with the
most credible identification and the most novel question, and the paper should probably be
reorganized around it.

**Stage 5 — Assemble the deliverable.** A paper with a single pre-specified main table
(one outcome, one lag structure, three standard-error columns), the exposure–lag–response
figure as Figure 1, robustness in an appendix rather than the body; the poster built from
that same figure; a replication package with a `make`-style entry point and a data
dictionary; and the limitations section written around §5.2 and §5.7 rather than around
generic caveats — reviewers will find those two anyway, and the paper is far stronger for
raising them first.

**One honest note on framing.** If Stage 2 does not survive — if the day-7 coefficient
dissolves under proper standard errors or turns out to be a denominator artifact — the
project is not dead. "Public attention to police violence does not measurably shift
mental-health EMS demand, but does shift the composition of who calls" is a real finding,
it is consistent with Strand C, and it is more interesting than a fragile positive.
Building the pipeline so that a null is publishable is the difference between a research
project and a result we are hoping for.

---

## 8. Bibliography

Abadie, A., Athey, S., Imbens, G. W., & Wooldridge, J. M. (2023). When should you adjust standard errors for clustering? *Quarterly Journal of Economics*, 138(1), 1–35.

Ang, D. (2021). The effects of police violence on inner-city students. *Quarterly Journal of Economics*, 136(1), 115–168.

Ang, D., Bencsik, P., Bruhn, J. M., & Derenoncourt, E. (2024). *Community engagement with law enforcement after high-profile acts of police violence*. NBER Working Paper 32243.

Bertrand, M., Duflo, E., & Mullainathan, S. (2004). How much should we trust differences-in-differences estimates? *Quarterly Journal of Economics*, 119(1), 249–275.

Bor, J., Venkataramani, A. S., Williams, D. R., & Tsai, A. C. (2018). Police killings and their spillover effects on the mental health of black Americans: a population-based, quasi-experimental study. *The Lancet*, 392(10144), 302–310.

Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2011). Robust inference with multiway clustering. *Journal of Business & Economic Statistics*, 29(2), 238–249.

Curtis, D. S., Washburn, T., Lee, H., Smith, K. R., Kim, J., Martz, C. D., Kramer, M. R., & Chae, D. H. (2021). Highly public anti-Black violence is associated with poor mental health days for Black Americans. *PNAS*, 118(17), e2019624118.

Das, A., Singh, P., Kulkarni, A. K., & Bruckner, T. A. (2020). Emergency Department visits for depression following police killings of unarmed African Americans. *Social Science & Medicine*, 269, 113561.

Desmond, M., Papachristos, A. V., & Kirk, D. S. (2016). Police violence and citizen crime reporting in the black community. *American Sociological Review*, 81(5), 857–876.

Driscoll, J. C., & Kraay, A. C. (1998). Consistent covariance matrix estimation with spatially dependent panel data. *Review of Economics and Statistics*, 80(4), 549–560.

Gasparrini, A. (2010). Distributed lag non-linear models. *Statistics in Medicine*, 29(21), 2224–2234.

Gasparrini, A. (2014). Modeling exposure–lag–response associations with distributed lag non-linear models. *Statistics in Medicine*, 33(5), 881–899.

Legewie, J., & Fagan, J. (2019). Aggressive policing and the educational performance of minority youth. *American Sociological Review*, 84(2), 220–247.

Mikdash, M., & Zaiour, R. (2022). Does (all) police violence cause enduring effects on crime reporting? (As discussed in Ang et al. 2024.)

Nix, J., & Lozada, M. J. (2021). Police killings of unarmed Black Americans: a reassessment of community mental health spillover effects. *Police Practice & Research*, 22(3), 1330–1339.

Packard, S. E., Verzani, Z., Finsaas, M. C., et al. (2024). Maintaining disorder: estimating the association between policing and psychiatric hospitalization among youth in New York City by neighborhood racial composition, 2006–2014. *Social Psychiatry and Psychiatric Epidemiology*, 60(1), 125–137.

Romano, J. P., & Wolf, M. (2005). Stepwise multiple testing as formalized data snooping. *Econometrica*, 73(4), 1237–1282.

Sewell, A. A., & Jefferson, K. A. (2016). Collateral damage: the health effects of invasive police encounters in New York City. *Journal of Urban Health*, 93(Suppl 1), 42–67.

Sewell, A. A., Jefferson, K. A., & Lee, H. (2016). Living under surveillance: gender, psychological distress, and stop-question-and-frisk policing in New York City. *Social Science & Medicine*, 159, 1–13.

Weitzel, K. J., Chew, R. F., Miller, A. B., Oppenheimer, C. W., Lowe, A., & Yaros, A. (2023). The use of crisis services following the mass school shooting in Uvalde, Texas: quasi-experimental event study. *JMIR Public Health and Surveillance*, 9, e42811.

Wu, H. H., Gallagher, R. J., Alshaabi, T., Adams, J. L., Minot, J. R., Arnold, M. V., Foucault Welles, B., Harp, R., Dodds, P. S., & Danforth, C. M. (2023). Say their names: resurgence in the collective attention toward Black victims of fatal police violence following the death of George Floyd. *PLOS ONE*, 18(1), e0279225.

*An EMS-based crisis response model for mental health–related EMS calls: a quasi-experimental study.* (2026). *Psychiatric Services*. doi:10.1176/appi.ps.20250528.

*Black emergency department visits for schizophrenia/psychosis following the police killing of George Floyd: an empirical test of "protest psychosis."* (2024). *SSM–Mental Health*.
