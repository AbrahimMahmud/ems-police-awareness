# Related work

The literature this project sits inside, what those studies did, and where our
design differs. Written to feed the paper's related-work section (D1) and the
methods contribution (D2).

Entries marked **[full text]** were read in full or substantial part; **[abstract]**
means abstract, publisher summary, or a citation inside a paper we did read.
Numbers are quoted as those sources report them. Citations in §7.

---

## 1. Four strands, which mostly do not cite each other

Our question — *does public attention to police violence change what communities
ask emergency services for?* — sits between four literatures. Being explicit about
which one we contribute to is most of the positioning work.

### A. Population mental health effects (survey-based)

The strand that gave the project its original premise.

**Bor et al. (2018), *The Lancet*.** BRFSS 2013-2015, 103,710 Black respondents.
Exposure: police killings of *unarmed* Black Americans in the respondent's state in
the prior three months. Outcome: self-reported poor mental health days. Identified
off quasi-random interview timing. Effects appear only for unarmed victims — none
for armed victims, none for white respondents. Those two internal placebos carry
most of the paper's persuasive weight. **[abstract]**

**Nix & Lozada (2021).** The reassessment: 93 Mapping Police Violence cases were
miscoded as unarmed; recoding attenuates Bor et al.'s estimate to non-significance.
Bor et al. replied disputing the recoding. **The lesson is not who won — it is that
the field's most public fight was about how the exposure variable was built.** That
is the direct argument for the CAI's verifiability-first design
(`AWARENESS_INDEX_DESIGN.md` §5) and it belongs in D2. **[abstract]**

**Curtis et al. (2021), *PNAS*.** Same BRFSS outcome, but exposure is 49 *publicized*
incidents — police killings, non-indictments, hate-crime murders. The closest
antecedent to our conceptual move (publicity, not incidence), though still discrete
named events rather than a continuous attention series. **[abstract]**

**Sewell & Jefferson (2016); Sewell, Jefferson & Lee (2016).** NYC, neighbourhood
level: living where pedestrian stops more often turn invasive is associated with
worse self-rated health and higher psychological distress. Cross-sectional, so no
temporal identification, but it establishes the NYC neighbourhood as a meaningful
unit for this outcome. **[abstract]**

### B. Administrative acute-care utilization — the closest relatives

**Das et al. (2020), *Social Science & Medicine*.** The nearest prior work. Exposure:
police killings of unarmed African Americans. Outcome: depression-related ED visits
per 100,000 among African Americans. 75 counties across 5 states, 2013-2015, 2,700
county-months, county fixed effects. Result: **+11% in the concurrent month and the
three months following**. **[abstract]**

> County-month resolution means "concurrent month plus three" is the finest temporal
> claim their design supports. Our CD-day panel is ~30× finer in time. The shape of
> the response *inside* the first month is a question their data cannot answer and
> ours can — which is exactly why the first-week joint test (Gate C §1) is the right
> primary object, and why getting its inference right is the whole contribution.

**Packard et al. (2024), *Social Psychiatry and Psychiatric Epidemiology*.** NYC, and
the model for our heterogeneity work. 180 ZCTAs × month, 2006-2014. Exposure:
policing incidents per 1,000 residents. Outcome: psychiatric hospitalization days,
ages 10-24, from SPARCS. Multilevel negative binomial, log-population offset,
policing × %Black-tertile interactions. Result: IRR 1.003 (95% CI 1.001-1.005),
**stronger in the highest-%Black tertile** (IRR 1.005). **[full text]**

> Their gradient runs *toward* higher-%Black neighbourhoods. Ours is non-monotonic —
> suppression in the whitest quartile (Q1: −0.00108, p = 0.02) and the two Blackest
> (Q3/Q4 ≈ −0.00074, p ≈ 0.09) but not Q2. This needs engaging head-on in the paper
> rather than left for a referee. Two things make it defensible: the outcomes differ
> (hospitalization is downstream of a decision to seek care; EMS activation *is* the
> decision), and Ang et al. (2024) find their call-reporting effects comparable
> across majority-white, -Black and -Hispanic neighbourhoods, explicitly contrasting
> with the Black/Hispanic-concentrated results in Ang (2021) and Legewie & Fagan
> (2019). A flat or non-monotonic gradient is not disqualifying in this literature.

**"An EMS-Based Crisis Response Model for Mental Health-Related EMS Calls" (2026),
*Psychiatric Services*.** The only study we have found using our exact dataset: NYC
EMS Incident Dispatch Data, Jan 2019-Dec 2024, monthly precinct-level rates, 76
precincts (31 B-HEARD adopters), staggered-adoption DID. Adoption **reduces**
mental-health EMS call rates, emerging ~1 year post-implementation. **[abstract]**

> Two consequences. It **validates the data source** for exactly this outcome and
> gives us a precedent for classifying mental-health EMS calls from dispatch codes.
> And it identifies a **confound in 45% of our extension episodes** — see
> `GATE_C_MEMO.md` §2 and `scripts/16_bheard_exposure.py`. That is the single most
> consequential thing this literature review turned up.

**"Protest psychosis" ED study (2024), *SSM-Mental Health*.** Black ED visits for
schizophrenia/psychosis rose a reported 4.26 percentage points in June 2020.
Monthly, single event. **[abstract]**

### C. Call-for-service behavior — the mechanism we are testing

**Desmond, Papachristos & Kirk (2016), *ASR*.** Milwaukee, the publicized beating of
Frank Jude. Interrupted time series on police-related 911 calls, controlling for
crime, prior call patterns, neighbourhood characteristics. Residents — especially in
Black neighbourhoods — reported crime far less afterwards; the effect ran **over a
year**, a net loss of ~22,200 calls. **[abstract]**

> Already our named mechanism. The *duration* is the underused part: a year-long
> effect is an argument for ROADMAP U2's longer post-windows (+28, +60), because a
> ±14-day window may be truncating real dynamics.

**Ang, Bencsik, Bruhn & Derenoncourt (2024), NBER WP 32243.** 13 cities around George
Floyd's murder. Their instrument is a denominator civilians cannot suppress: the
**call-to-shot ratio**, 911 calls ÷ ShotSpotter-detected gunshots, separating
willingness to engage police from underlying crime. Daily, 73 days each side,
Newey-West SEs plus **randomization inference against randomly chosen placebo
dates**. Call-to-shot ratio down >50%; gunshots more than doubled; **911 call volume
down ~25%, depressed through end-2020**. Declines comparable across
majority-white, -Black and -Hispanic neighbourhoods. **[full text]**

> Three things for us. (i) **The framing hook**: they attribute the gap between their
> effect and Mikdash & Zaiour's (3-6% on lower-profile killings) to *salience and
> media attention*, and name it as "natural areas for future work." That is this
> paper's contribution, stated by someone else, in a top-tier working paper. (ii)
> **Independent corroboration** of the avoidance mechanism, with a magnitude. (iii)
> They arrived at randomization inference for the same reason we did — an aggregate
> time-series break with few independent events — which is a citable precedent for
> making permutation the primary p-value rather than a robustness column.

**Ang (2021), *QJE*.** LA students; hyperlocal dynamic DID, within 0.50 mi of a
killing vs 0.50-3 mi. Persistent falls in GPA, higher emotional disturbance, lower
completion and college enrolment; driven entirely by Black and Hispanic students,
largest for unarmed victims. SEs clustered by ZIP, with multiway clustering and
cohort-by-cohort event studies as robustness. **[full text]**

**Legewie & Fagan (2019), *ASR*.** NYC Operation Impact surges; DID off staggered
timing across neighbourhoods; ~250,000 adolescents. Test scores fall for
African-American boys. **[abstract]** Structurally this is the NYC template for
getting identification out of a citywide policy shock — by exploiting the fact that
it did not arrive everywhere at once.

### D. Measuring collective attention

**Wu et al. (2023), *PLOS ONE*.** "Say their names." Storywrangler over a 10% sample
of English tweets, victims' names as 2-grams, 3,737 police-involved deaths. Two
details matter for the CAI. They use **relative frequency** — usage normalized by
total daily volume — explicitly because raw counts confound attention with platform
activity, which is the same failure mode as the legacy z-score. And **George Floyd's
name became the 7th most-used 2-gram on 29 May 2020, four days after his death** —
independently reproducing the peak date our own series and the anchored Trends
component both produce. They also document decay: attention to names fell by an
order of magnitude after 2014 spikes, but only 33% after Floyd. **[full text]**

> Cite as lineage in `AWARENESS_INDEX_DESIGN.md` alongside Da-Engelberg-Gao, and as
> external validation of the peak-alignment battery (§4 of that document).

**Weitzel et al. (2023), *JMIR Public Health & Surveillance*.** Crisis Text Line
volume after the Uvalde shooting; SARIMA on three months of pre-event data supplies
the counterfactual. **Peak at day +1, back inside the forecast interval by day +4.**
**[full text]**

> The sharpest published benchmark for the timing of acute help-seeking after a
> collective-trauma event, and the reason the *first week* — not days 3-5 — is the
> defensible pre-registered window (`GATE_C_MEMO.md` §1). Also a design worth
> borrowing: a forecast-based counterfactual needs no control group, which suits a
> citywide shock.

---

## 2. Reference table

| Study | Exposure | Outcome | Unit | Design | Headline |
|---|---|---|---|---|---|
| Bor et al. 2018 | Killings of unarmed Black people, state, 3 mo | Poor mental health days | Person | Interview-timing quasi-experiment | Adverse; null for armed victims and white respondents |
| Nix & Lozada 2021 | Same, recoded | Same | Person | Replication | Attenuates to non-significance |
| Curtis et al. 2021 | 49 publicized incidents | Poor mental health days | Person | Event-based | Adverse |
| Das et al. 2020 | Killings of unarmed African Americans | Depression ED visits /100k | County-month | County FE | +11%, concurrent + 3 months |
| Packard et al. 2024 | Policing incidents /1,000 | Psychiatric hospitalization days | ZCTA-month (NYC) | Multilevel NB, pop. offset | IRR 1.003; stronger in highest-%Black tertile |
| B-HEARD study 2026 | Program adoption | MH-related EMS calls | Precinct-month (NYC) | Staggered DID | Reductions ~1 yr post-adoption |
| Desmond et al. 2016 | One publicized beating | Police-related 911 calls | Neighbourhood TS | Interrupted time series | −22,200 calls, >1 year |
| Ang et al. 2024 | George Floyd's murder | Call-to-shot ratio; 911 volume | City-day, 13 cities | TS break + randomization inference | Ratio −50%+; volume −25%, months |
| Ang 2021 | Killing within 0.50 mi | GPA, emotional disturbance | Student | Hyperlocal dynamic DID | Persistent harm; Black/Hispanic only |
| Legewie & Fagan 2019 | Operation Impact surges | Test scores | Student (NYC) | Staggered DID | Harm to African-American boys |
| Wu et al. 2023 | — | Collective attention | Name-day | Descriptive | Floyd peak 29 May 2020 (day +4) |
| Weitzel et al. 2023 | Uvalde shooting | Crisis Text Line volume | Day | SARIMA counterfactual | Peak day +1, over by day +4 |
| **This project** | **CAI-D, continuous daily attention, 2015-2024** | **EDP / narrow-MH share and counts** | **CD-day (59 CDs, NYC)** | **Stacked episode event study; randomization inference** | **First-week composition shift; see GATE2 memo** |

---

## 3. Where this project sits

**Temporal resolution.** Every administrative-outcome study in Strand B works at the
month. We work at the day. Nobody in this literature can currently say whether the
acute response peaks at day 1, day 7, or day 20 — Weitzel et al. can, but on a crisis
text line rather than emergency dispatch, and for a school shooting rather than
police violence.

**Continuous attention exposure.** Strands A and B code discrete events. Strand D
measures attention well but never links it to a health outcome. The CAI puts a
continuous, multi-source, daily, verifiable attention measure on the right-hand side
of a health-utilization regression. Ang et al. (2024) name this as the open question
their design cannot address.

**Pre-hospital outcome.** Strand B measures people who reached an ED or were
admitted. EMS dispatch is upstream of both: it is the moment a crisis becomes a 911
call, which is precisely where a help-seeking decision is made and therefore where
avoidance would show up first.

**Separating distress from help-seeking.** Strand C says willingness to call 911
falls after police violence; Strands A and B say distress rises. The two act in
opposite directions *on the same measurement instrument*, and no prior study
separates them. Our EDP-vs-overdose decomposition does — EDP calls summon police,
overdose calls generally do not — and the placebo call types (cardiac, asthma) bound
the compositional artifact. This is the project's strongest claim to novelty.

**Where we are weaker.** Every other study gets leverage from cross-sectional
variation in exposure: distance to a killing, which precinct adopted, which
neighbourhood was surged, which state or county had an incident. Our attention
measure is citywide. Cross-sectional identification exists only in the heterogeneity
and DID designs, which is why those carry more of the inferential weight than their
usual supporting role — and why the DID's power problem (REWORK_PLAN §5.2,
GATE_C_MEMO §5) matters more than it otherwise would.

---

## 4. What to borrow

| From | Borrow |
|---|---|
| Ang et al. 2024 | The framing hook; randomization inference as primary; the idea of a denominator civilians cannot suppress; the ~25% volume drop as a citable magnitude for the mechanism |
| Bor et al. 2018 | Internal placebo design — their armed/unarmed contrast is the model for our cardiac/asthma placebos and for a possible police-violence vs other-violent-news contrast |
| Nix & Lozada 2021 | The warning that exposure construction is what gets attacked; the case for D2 |
| Das et al. 2020 | Counts per capita as an outcome; a monthly-aggregated version of our estimate as a consistency check against their +11% |
| Packard et al. 2024 | NB with population offset; the racial-composition interaction structure; ACS vintage |
| B-HEARD study 2026 | Dispatch-code classification precedent; **the confound in §2 of the Gate C memo**; precinct-level aggregation as an alternative geography |
| Legewie & Fagan 2019 | The NYC template for extracting cross-sectional identification from a citywide shock |
| Desmond et al. 2016 | ITS with crime and prior-call controls; the >1-year duration, arguing for longer post-windows |
| Wu et al. 2023 | Relative-frequency normalization; independent confirmation of the 29 May 2020 peak; decay dynamics for window choice |
| Weitzel et al. 2023 | The day+1/day+4 timing prior; a forecast-based counterfactual needing no control group |

---

## 5. Bibliography

Ang, D. (2021). The effects of police violence on inner-city students. *Quarterly Journal of Economics*, 136(1), 115-168.

Ang, D., Bencsik, P., Bruhn, J. M., & Derenoncourt, E. (2024). *Community engagement with law enforcement after high-profile acts of police violence*. NBER Working Paper 32243.

Bor, J., Venkataramani, A. S., Williams, D. R., & Tsai, A. C. (2018). Police killings and their spillover effects on the mental health of black Americans: a population-based, quasi-experimental study. *The Lancet*, 392(10144), 302-310.

Curtis, D. S., Washburn, T., Lee, H., Smith, K. R., Kim, J., Martz, C. D., Kramer, M. R., & Chae, D. H. (2021). Highly public anti-Black violence is associated with poor mental health days for Black Americans. *PNAS*, 118(17), e2019624118.

Da, Z., Engelberg, J., & Gao, P. (2011). In search of attention. *Journal of Finance*, 66(5), 1461-1499.

Das, A., Singh, P., Kulkarni, A. K., & Bruckner, T. A. (2020). Emergency Department visits for depression following police killings of unarmed African Americans. *Social Science & Medicine*, 269, 113561.

Desmond, M., Papachristos, A. V., & Kirk, D. S. (2016). Police violence and citizen crime reporting in the black community. *American Sociological Review*, 81(5), 857-876.

Legewie, J., & Fagan, J. (2019). Aggressive policing and the educational performance of minority youth. *American Sociological Review*, 84(2), 220-247.

Nix, J., & Lozada, M. J. (2021). Police killings of unarmed Black Americans: a reassessment of community mental health spillover effects. *Police Practice & Research*, 22(3), 1330-1339.

Packard, S. E., Verzani, Z., Finsaas, M. C., et al. (2024). Maintaining disorder: estimating the association between policing and psychiatric hospitalization among youth in New York City by neighborhood racial composition, 2006-2014. *Social Psychiatry and Psychiatric Epidemiology*, 60(1), 125-137.

Sewell, A. A., & Jefferson, K. A. (2016). Collateral damage: the health effects of invasive police encounters in New York City. *Journal of Urban Health*, 93(Suppl 1), 42-67.

Sewell, A. A., Jefferson, K. A., & Lee, H. (2016). Living under surveillance: gender, psychological distress, and stop-question-and-frisk policing in New York City. *Social Science & Medicine*, 159, 1-13.

Weitzel, K. J., Chew, R. F., Miller, A. B., Oppenheimer, C. W., Lowe, A., & Yaros, A. (2023). The use of crisis services following the mass school shooting in Uvalde, Texas: quasi-experimental event study. *JMIR Public Health and Surveillance*, 9, e42811.

Wu, H. H., Gallagher, R. J., Alshaabi, T., Adams, J. L., Minot, J. R., Arnold, M. V., Foucault Welles, B., Harp, R., Dodds, P. S., & Danforth, C. M. (2023). Say their names: resurgence in the collective attention toward Black victims of fatal police violence following the death of George Floyd. *PLOS ONE*, 18(1), e0279225.

*An EMS-based crisis response model for mental health-related EMS calls: a quasi-experimental study.* (2026). *Psychiatric Services*. doi:10.1176/appi.ps.20250528.

*Black emergency department visits for schizophrenia/psychosis following the police killing of George Floyd: an empirical test of "protest psychosis."* (2024). *SSM-Mental Health*.

New York City Independent Budget Office. (2026). *B-HEARD: a look at precinct level data.*
