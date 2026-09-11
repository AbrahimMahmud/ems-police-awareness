# Paper master document

**Everything the paper needs, in one place, maintained continuously.**

Rule for this document: **every method gets three layers.**

1. **What we did** — plain words, with an everyday analogy. A smart reader with no
   statistics background can stop here and still follow the paper.
2. **Why** — what the alternatives were and what we gave up.
3. **The technical statement** — the exact claim, with the file and function that
   implements it.

If a method cannot be explained in layer 1, that usually means the method is not
yet clear enough to defend.

**Maintenance rule:** this file is updated *in the same commit* as the change it
describes — a new number, a fixed defect, a decision taken. Not at the end of a
phase.

> **Provenance note.** This document was started on 2026-09-10, later than it
> should have been. It is written from contemporaneous evidence — commit
> messages, `docs/AUDIT_FINDINGS.csv`, `docs/REBUILD_PLAN.md`, and committed
> artifacts — not from recollection. Where a number could not be sourced to an
> artifact it is marked TODO rather than guessed.

---

## 1. The question, in one paragraph

When a police killing gets a lot of public attention, do the people of New York
City change what they ask 911 for?

Specifically: when someone is having a mental-health crisis, calling 911 usually
brings both an ambulance and the police. If a killing is in the news, some people
may decide that calling is too risky — for themselves, or for the person they are
trying to help. If that happens, we would expect fewer mental-health calls to EMS
in the days after a big attention episode. Or the opposite could happen: attention
to a crisis could make people *more* likely to call. Or nothing changes.

We test which, using every EMS dispatch in New York City, in each of the city's 59
community districts, on each day.

**We frame the question three ways — increase, decrease, or no change — so that no
result is a disappointment.** A precisely estimated zero is a finding.

---

## 2. Glossary, in plain words

**Community district** — New York City is divided into 59 neighbourhood-sized
administrative areas. Think of them as the city's "zip codes for planning".
Manhattan has 12, Brooklyn 18, and so on. They are our geographic unit.

**EMS** — Emergency Medical Services: the ambulance system. When you call 911 for
a medical emergency, a dispatcher assigns your call a *call type* code and sends a
unit.

**EDP** — "Emotionally Disturbed Person", the NYPD/FDNY dispatch code for a
mental-health crisis call. It is the label the system uses, not ours. Our main
outcome is what share of a district's 911 medical calls on a given day carry this
code (or a related mental-health code).

**Call share** — mental-health calls divided by all calls, in one district on one
day. We use a share rather than a raw count because the total number of calls
swings for reasons that have nothing to do with us (weather, holidays, COVID).
*Analogy:* if you want to know whether a restaurant is getting more vegetarian
orders, "12 veggie meals today" tells you less than "12 out of 80".
*But see §5.4 — this choice bit us, and counts are now reported alongside shares.*

**Fixed effect** — a way of saying "compare each thing only to itself". A district
fixed effect means we never compare Staten Island to the Bronx; we only ask
whether the Bronx changed relative to its own usual level.
*Analogy:* grading students on improvement rather than on raw score.

**Event study** — instead of asking "is treatment associated with the outcome on
average", we line up every attention episode at day zero and watch what the
outcome does on day −14, −13, … −1, 0, +1, … +14. The days *before* the episode
are the test of whether we are fooling ourselves: if the outcome was already
moving before the news broke, the "effect" is not an effect.

**Randomization inference** — instead of trusting a formula for how uncertain our
estimate is, we re-run the whole analysis hundreds of times using *fake* episode
dates, and ask how often chance alone produces something as big as what we saw.
*Analogy:* to know whether a coin is loaded, flip a known-fair coin a thousand
times and see how often it does what yours did. We use this as our **primary**
p-value, because the formula-based one has already proved untrustworthy on this
data (p = 0.019 by formula against 0.26 by permutation).

**Pre-registration and "the freeze"** — we wrote down our hypotheses and locked
away part of the data *before* looking at it. See §6.

**Placebo outcome** — a call type that should *not* respond to police-violence
news, like cardiac arrest or asthma. If our "effect" shows up there too, it is not
about mental health; it is something wrong with the analysis.

**Confound** — something else that changed at the same time and could produce the
same pattern. Our worst one is B-HEARD (§5.5).

---

## 3. Data sources

| What | Source | Span | Status |
|---|---|---|---|
| EMS dispatches | NYC OpenData `76xm-jjuj` | 2005–2026 (we use 2014-12→2024-12) | **29,978,154 rows downloaded, complete** |
| Victim registry | Mapping Police Violence | 2013–2024 | 13,241 killings |
| Wikipedia pageviews | Wikimedia REST API | **2015-07-01**→2024 | 121 articles, 111 people |
| Google Trends | pytrends | 2015–2024 | national + NYC DMA |
| GDELT news / TV | GDELT 2.0 | 2017–2022 / 2015–2024 | supply tier only |
| Demographics | ACS 2019 by community district | — | 59 districts |
| B-HEARD adoption | NYC, precinct-level | June 2021→ | 31 precincts |

### 3.1 Known flaws in each source — stated up front

- **Wikipedia pageviews do not exist before 2015-07-01.** The API starts there.
  This is a hard floor on the treatment measure, not a choice. Earlier data exists
  in a different dataset (`pagecounts-raw`) that counts bots, so splicing it would
  create exactly the level break we are trying to avoid.
- **Wikipedia records pageviews per article title, and does not carry them across a
  page rename.** Many of these articles were renamed from "Shooting of X" to
  "Killing of X" during 2020–21. See §5.2 — this destroyed most of the signal
  before we caught it.
- **Google Trends returns a sample, not a census**, and rescales to 0–100 against a
  moving base. The same query issued twice returns different numbers.
- **Mapping Police Violence has real coverage gaps**, and they are not random with
  respect to our hypothesis. See §5.6.
- **The EMS call-type vocabulary changes over time.** Codes are born and retired
  mid-sample; EDPC phases in around mid-2018.

---

## 4. How we measure attention (the treatment)

### Layer 1 — what we did, in plain words

We wanted a number for "how much is the country paying attention to police
violence today". We build it from things people *chose to look up*:

- how many people read Wikipedia articles about people killed by police, and
- how many people searched Google for police brutality, nationally and in New York.

We deliberately do **not** use how much the news *covered* it. News coverage
measures what editors decided to publish. We want to measure what the public
actually sought out — that is the thing that could plausibly change whether
someone picks up the phone.

*Analogy:* to measure interest in a film, count ticket sales, not the number of
posters the studio printed.

We average those signals and express the result in standard deviations — "how
unusual is today compared to a normal day".

### Layer 2 — why, and what we gave up

- **Why not news volume?** It measures supply, not demand. We keep a separate
  news-based index (CAI-S) purely as a falsification check: on days when coverage
  is high but public attention is *not*, we should see no effect.
- **Why not Twitter?** The project originally used a Twitter volume series. It was
  retired because its collection methodology is undocumented and it cannot be
  re-fetched by anyone else. A measure a referee cannot reproduce is not a measure.
- **What we gave up:** the index is now honestly a **national** attention index
  plus one NYC-local search component. See §4.3.

### Layer 3 — technical

`CAI_D_COMPONENTS = ("wiki_ext", "trends_us", "trends_nyc")` — `scripts/config.py`.
Built by `scripts/12_build_cai.py`.

Each component is log1p-transformed and standardised on the 2017-01-01→2019-12-31
reference window (deliberately excluding 2020). A day is scored **only if every
component is present**; the composite is then **re-standardised after averaging**.

Current state: **3,472 scored days**, mean `0.000000`, SD `1.000000` on the
reference window, asserted in the build rather than assumed.

### 4.1 The article basket — which victims count

**Layer 1.** We need a list of which killings to track attention for. The obvious
approach — "everyone in the victim registry" — does not work, because most victims
have no Wikipedia article and therefore no attention to measure. So we ask
Wikipedia itself which killings it has articles about.

**Layer 2.** The original basket was chosen by ranking victims on the retired
Twitter series, which stops in 2020. That basket contained **zero victims killed
after 2020** — so the index structurally could not see attention in the extension
years. We also cannot gate the basket on the registry (§5.6).

**Layer 3.** `scripts/24_build_wiki_basket.py` walks the live Wikipedia category
tree; `scripts/26_resolve_basket_scope.py` resolves date/country from Wikidata;
`scripts/27_finalise_basket.py` applies the scope rule and writes
`data/reference/wikipedia_article_resolution.csv`.

Current basket: **121 articles / 111 people**, span 2013-01-27→2024,
**24 killed after 2020**. Every include/exclude decision with its reason is in
`data/reference/basket_decisions.csv`.

The basket is deliberately **not ranked by attention** — that would let the index
select its own inputs, which is the defect that retired `trends_victims`.

### 4.2 What an "episode" is

**Layer 1.** An episode is a burst of unusual attention. We find the days when the
index is far above normal, and treat the start of each burst as an event.

**Layer 2 — DECIDED 2026-09-10, and this is a change to the pre-registered
construct.** The original rule was a *regime* rule: "attention was high for a
stretch". On 2020 that rule produces a single 184-day episode swallowing the
entire Floyd summer — one observation in a ±14 day design, hiding at least eight
distinct shocks including **Daniel Prude**, a Black man killed during a
mental-health crisis and the single most on-hypothesis event in the dataset.

No parameter tweak inside the regime family removes it; it is a true feature of
2020. So the construct changes to a **shock** rule: "attention to a specific
killing began on day X."

This is legitimate **only because we are still blind to every outcome** — the same
argument that licenses rebuilding the episode list at all, and worthless after the
confirmatory run. It is disclosed in the `CONFIRMATION_PLAN.md` addendum.

**Layer 3.** `scripts/13_extension_episodes.py`. The threshold also changes from a
fixed level to a **fixed within-year quantile**, because a fixed cut is not a
constant stringency: it selected 10.7%–66.4% of days depending on the year.

Status: **implemented** (`scripts/13_extension_episodes.py`, 2026-09-10). Frozen
list = 70 episodes; rebuilt list = 72 episodes. The stringency really is constant
now — the rule selects 10.1%–10.3% of days in every year — and no episode spans
more than 14 days from start to end, against 235 under the regime rule. The
frozen file stays byte-identical on disk; the rebuilt list is written separately
to `data/reference/confirmation_episodes_rebuilt.csv`, and the diff between them
is published as a disclosed deviation.

### 4.3 What the index can and cannot claim

`trends_nyc` was the only nominally NYC-local component, and it is censored:
42.6% of its days are exactly zero — Google's low-volume reporting floor — rising
from 26% censored in 2020 to 71% in 2024.

**The refetch helped and did not solve it.** On 2026-09-10 the series was refetched
with the "Police brutality" topic entity and a wider term basket, which cut the
zero share from 79% to 42.6% and removed the 4.48× stitching break (that break was
caused by an all-zero overlap window). But on 26–71% of days, depending on the
year, the series is still not a level at all: it is an indicator of clearing
Google's reporting floor. The censoring is worst in 2021–2024, which is exactly
where the exposed confirmation stratum sits, so it is not a limitation we can
caveat and move past.

**DECIDED, after the refetch:** retire `trends_nyc` from CAI-D and replace it with
`wiki_nyc`, built from Wikipedia pageviews on NYC police-incident articles
(`scripts/28_build_nyc_attention.py`). Pageviews are a census, not a sampled index
rescaled to 0–100, so `wiki_nyc` has **no censored days in any year**. The cost is
a thin basket (§9), which bounds the locality claim; the benefit is that the
city-local component is a measurement rather than a threshold indicator.

**Do not claim this is "a return to the frozen spec."** The design document names
a topic *and* victim-name terms; we implemented the first, dropped the second, and
have now replaced the component altogether. It is a corrected measurement,
disclosed as such.

---

## 5. How we measure demand (the outcome), and everything that went wrong

### 5.1 The outcome

**Layer 1.** For each of the 59 districts on each day, we count mental-health 911
medical calls and divide by all calls.

**Layer 3.** `data/processed/panel_cd_day.parquet` — **89,857 rows**, 59 districts,
2016-12-01→2021-01-31 (buffered discovery window). Mean EDP share **0.0856**, mean
total calls per district-day **65.9**. Built by `scripts/01_build_panel.py`.
Districts with fewer than 5 calls on a day are excluded from share calculations.

### 5.2 What went wrong — this section is the methods contribution

Write this up as an asset, not a confession. Most of it is generalisable to anyone
doing attention-and-administrative-data work.

**The z-scoring artifact.** The original specification standardised the awareness
measure *within the analysis window*, so the variable's scale depended on what else
was in the sample. Change the window and the same real attention gets a different
number — the coefficient moves for reasons unrelated to EMS calls. Demonstrated by
simulation (§7.4) rather than on the retired series.

**The Wikipedia rename bug.** Wikimedia records pageviews per *title* and does not
carry them across a page move, so resolving each victim to their article's current
canonical title discarded everything before the rename — including the attention
spike at the killing, which is the entire signal. `Shooting_of_Alton_Sterling`
holds 1,861,004 views from 2016-07-06; `Killing_of_Alton_Sterling`, the title the
basket used, holds 128,855 from 2021-04-25. That is 6.5% of his attention, and
nothing at all from the week he was killed.

This was diagnosed in the first audit and a fix was written — and **never applied
to the production basket**, so the defect was still corrupting every CAI-D value a
day after the audit that found it. Historical titles are now discovered from the
MediaWiki redirects API rather than guessed from prefixes, and summed. That
returned **79,082,746 views** across **106 of 127 articles**: Michael Brown 13.7×,
Philando Castile 8.4×, Breonna Taylor 7.4×, Tamir Rice 6.1×, Eric Garner 4.5×.
119 of the 121 basket articles now return a usable series.

**The validation that matters is the content, not the size.** The top attention day
of the decade is now 2016-07-08 — Alton Sterling and Philando Castile — ahead of
the Floyd sequence, and the index peak moved from 2021-04-21 to 2020-05-30. Before
the fix, Sterling and Castile contributed *nothing* to the week they were killed,
which is why Sandra Bland's **anniversary** appeared to dominate July 2016. Both
artifacts are gone.

**The index scaling defect.** The index was the mean of whatever components existed
that day. How many existed swung from 2 to 4 across the decade, and the spread of a
mean moves with the number of terms averaged — so the index's SD tracked *data
availability*, not attention (0.770 on 2-component days, 0.693 on 3, 1.034 on 4).
Worse, averaging k separately standardised series does not give unit variance: the
measured SD was **0.6699**, so the documented "1 SD" episode threshold was really
about 1.5 SD.

**The endogenous component.** `trends_victims` was present only on days when search
volume cleared Google's reporting floor — i.e. on high-attention days. In a
mean-of-available index, its presence pushed the index up precisely when attention
was high, *by construction*. The index partly measured itself.

**Fifteen checks that could pass for the wrong reason.** See §7.5. This is the most
transferable lesson in the project.

### 5.3 The freeze incident (2026-09-10) — disclosed

During an automated audit, an agent computed the citywide mental-health call share
by year for 2005–2026, including confirmation years, in order to demonstrate that
`ems_citywide_day_trends.parquet` had no freeze guard. It deliberately did not
restate the values.

Narrow — a citywide annual aggregate of a level series, with no episode alignment,
no treatment merge, no district variation, and no test of H1 — but real. Recorded
as an incident; materiality is for the supervisor to judge, not us. The gap that
allowed it (outcome files outside the guard's coverage) is being closed.

### 5.4 Counts vs shares — a finding that reverses

The 2020 "signature" in shares does **not** survive in counts: EDP call *counts*
were flat after Floyd, while the denominator rose 6.4% because injury calls rose
~20%. A compositional finding that exists only in the denominator is not a finding.

**Both arms are now reported for every outcome and window** — OLS on shares, and
PPML on counts with a log total-calls offset. Verified to recover a planted
proportional rate change (−0.1446 against a planted log(0.85) = −0.1625).

### 5.5 B-HEARD — the confound that matters most

From June 2021 New York diverts some mental-health 911 calls away from police
response, rolled out precinct by precinct. **It pushes the outcome in the same
direction as our hypothesis.** It does not exist anywhere in the discovery window,
which is why the discovery estimates are clean — and why the 2021–2024 confirmation
arm requires the control.

17 of the 31 precinct dates are low confidence, 11 medium, 3 high. A pre-registered
control resting on low-confidence dates belongs in the limitations, not a footnote;
it is carried as exposure **bounds** rather than a point date for exactly that
reason.

### 5.6 The registry omits the events the paper is about (finding T9)

Mapping Police Violence is 100% of our victim registry. Checked directly against
the MPV workbook: **Daniel Prude, Sandra Bland, Marvin Scott, Javier Ambler and
Leneal Frazier are absent from MPV itself.** Not a parsing bug — the registry is a
faithful date-filtered subset.

The omissions run *with* the hypothesis, not across it: they are disproportionately
in-custody, restraint and mental-health-crisis deaths — exactly the events most
likely to move mental-health EMS demand. Daniel Prude is the most on-hypothesis
event in the study.

Consequence: the article basket must **not** be gated on registry membership, and
the coverage gap is a stated limitation.

---

## 6. The design, and the freeze

**Layer 1.** We split the data in two. We explored the first part freely. We wrote
down our predictions. Then we locked the second part away and have not looked at
it. If our prediction holds on data we have never seen, that is worth far more than
a pattern found by looking.

*Analogy:* calling your shot before the pool shot, not after.

| | Window | Status |
|---|---|---|
| Discovery | 2017-01-01 → 2020-12-31 | explored |
| Confirmation A | 2015-07-01 → 2016-12-31 | **never examined** — no COVID, no B-HEARD |
| Confirmation B | 2021-01-01 → 2024-12-31 | **never examined** — B-HEARD control required |

The cleanest confirmation sample runs **backward**. 2015–2016 has never been looked
at *and* carries none of the confounds.

**Layer 3.** `scripts/freeze_guard.py`. Discovery and confirmation are separate
named constants; the active window is *derived* from `FREEZE_ACTIVE`, never
hand-set. Lifting the freeze **switches** the sample and excludes discovery — there
is deliberately no state in which both are returned.

Verified to reject four things it should, including that one:
`D.guard_can_fire`. A gate that has never rejected anything has not been tested.

---

## 7. Every statistical choice

### 7.1 The estimator

**Layer 1.** For each attention episode, we line up the 14 days before and 14 days
after, and compare each day to the day before the news broke. We do this within
each episode separately, so we never compare one event's aftermath to another
event's build-up.

**Layer 3.** `scripts/event_study.py`, `scripts/17_stacked_event_study.py`.
`y ~ i(rel_day, ref=-1) | ep_cd + dow`, clustered on `incident_date`.

Day −1 stays **in** the sample and is named as the omitted level. Contested
district-days go to the **nearer** episode rather than being deleted.

Verified: recovers a planted −0.010 first-week effect as **−0.01043**; 0 duplicate
district-days; all 30 test episodes retain their reference day.

### 7.2 Why randomization inference is the primary p-value

Formula-based standard errors have already proved anti-conservative on this data
(p = 0.019 clustered against 0.26 permutation). We re-draw placebo episode dates
preserving the real episodes' spacing, and report the share of placebo statistics
at least as extreme as the observed one.

Placebo draws now keep **all** episodes 100% of the time; the previous
implementation kept all 30 in only 11% of draws and averaged 16, which inflated the
null's spread and gutted the p-value.

### 7.3 The test statistic

H1 is a **joint** test that the eight first-week coefficients are all zero — a Wald
χ², two-sided. The mean of those coefficients is reported as an effect size but is
**not** the test.

Why this matters: a dip-then-rebound — the project's *own* hypothesised mechanism —
averages to roughly zero. On a planted dip-then-rebound the joint statistic reads
**χ² = 1527** while the mean reads **+0.001**. The retired statistic was blind to
the thing it was written to detect.

### 7.4 What the null calibration proves

**Layer 1.** Before trusting our method on real data, we ran it hundreds of times on
fake data built to contain *no* effect. A trustworthy method should cry wolf about
5% of the time. Ours cries wolf 6.5% of the time — close enough, and the full
spread of its answers is the right shape.

**Layer 3.** `scripts/18_null_calibration.py`, 200 sims × 200 draws:

```
VERDICT                   CALIBRATED
empirical rejection rate  0.065    nominal 0.05, band [0.0198, 0.0802]
median p                  0.5025
KS uniformity             p = 0.562
AR(1) rho                 0.185    estimated from the real panel
```

Uniformity is the property that matters — a correct rejection rate with a
non-uniform distribution still means a broken statistic. The synthetic panel
carries a **citywide day shock**; without one the null is easier than reality and
would certify an estimator whose error bars are ~3× too narrow.

The gate refuses a verdict below 200 sims (verified: a 4-sim run prints
UNDETERMINED and exits 2). The artifact it replaced read CALIBRATED from 12 sims
with no real panel.

*Open:* 0.065 is inside the band but above nominal, and the 0.35σ day shock is
currently assumed rather than estimated. Under investigation.

### 7.5 The verification apparatus — and its own failure mode

`scripts/23_regression_suite.py` turns every audit finding into an executable
check. **38 checks, 37 passing.** States are PASS / FAIL / **BLOCKED** / ERROR,
where BLOCKED means "could not evaluate" and is deliberately *not* a pass.

**The most transferable lesson in this project:** at least fifteen checks were
found that could pass for the wrong reason —

- a DOTALL regex that matched elsewhere after an unrelated edit;
- a check admitting only one of two valid fixes;
- PASS returned when the required artifact was **absent**;
- a grep for a function name that the fix then renamed;
- PASS because a column disappeared;
- a match on the first numeric literal, defeated by naming a constant;
- a check defeated by multiplying the untouched values by 1.0000001.

**Rule:** where the property is arithmetic, test the arithmetic. A source grep
proves the code *says* the right thing, not that the output *has* the right
property. And a new check is not done until someone has actively tried to defeat
it.

### 7.6 The source and claims registers

The recurring failure in this project is not a wrong number. It is a number that
*reads as established because nobody re-checked it*. So three registers, all
committed, all machine-verified by `scripts/31_verify_sources.py`:

| Register | What it holds |
|---|---|
| `data/reference/source_register.json` | what every source **is** — publisher, endpoint, what we take, realised coverage, terms, known flaws. `docs/SOURCE_REGISTER.md` is **generated** from it, so the document a reader reviews and the scan a machine runs cannot drift apart. |
| `docs/CLAIMS_REGISTER.csv` | every number this document claims, mapped to the artifact and the expression that produces it. |
| `data/reference/source_verification_log.csv` | **append-only.** Every result ever recorded, including failures. |

**A failed scan is a recorded result, not a retry-until-green.** Statuses are
kept distinct: `verified`, `mismatch`, `absent`, `failed`, `unreachable`,
`unverifiable`, `template`, `skipped`. *Unverifiable* is a real, permanent
category — the retired Twitter files can never be re-checked and must say so
rather than sitting silently absent. *Unreachable* says something about our
access, not about the source: a rate limit or this container's egress policy is
never recorded as a verdict on an endpoint.

Claims are checked **in both directions**: the scan recomputes the value from
the artifact, renders it into the registered template, and requires the result
to appear verbatim in the document. Edit the document and the text is no longer
found; rebuild the data and the value no longer matches. A number that cannot be
regenerated is a check failure, not a typo. Every claim in this document is
registered and currently reproduces.

Four checks hold it in place — `V.sources_verified` (which **BLOCKS, never
passes, when no scan has run**), `V.no_duplicate_source_ids`,
`V.claims_reproduce`, `V.links_resolve` — and each was defeated on purpose
before being accepted: a claim edited to a wrong value fails; truncating the
underlying data fails; a deliberately dead URL fails; a returning id collision
fails; a second script appending to the register fails; an artifact touched
after its scan fails; and deleting the log **blocks** rather than passing.

**What building it found.** The register was not bookkeeping — writing it
surfaced six defects, none of which was visible in any artifact:

- `data_sources.csv` held **21 rows under 9 ids**, because seven scripts each
  appended with `mode="a"` and nothing ever re-keyed.
- Two of those ids **collided**: `16_bheard_exposure.py` emitted S10 and S11,
  which belong to Mapping Police Violence and the CAI components. The CSV had
  been hand-renumbered to hide it while the script was left alone, so the
  collision would have returned on the next run — and with one row per id it
  would have silently overwritten two other sources' provenance.
- The `sha256` column meant **two different things**: the network payload for
  S7/S10, the artifact for the rest. Anything comparing it to a file would have
  called the ACS and MPV artifacts corrupt.
- **Two artifact hashes had genuinely stopped matching.** One was repaired by
  re-running its fetch. The other, `wikipedia_pageviews_victims.csv`, **cannot
  be**: its basket was chosen by the retired Twitter measure, so the artifact
  behind the race-split components cannot be regenerated from live sources at
  all. Its bytes are pinned with a dated reason instead — and that is a
  limitation of the paper, not a bookkeeping note.
- Derived CSVs were **not byte-reproducible**: re-running the crosswalk on
  identical counts changed 72 lines and the SHA256, differing only in the 17th
  significant digit of a float. A hash that changes when nothing changed is how
  a reader learns to ignore hash mismatches.
- `20_data_audit.py` — one of the two commands this project runs as its gate —
  **had been raising `FileNotFoundError` on its first statement** ever since
  anchoring was retired, and then `KeyError` twice more. It produced no audit at
  all, while "audit flags non-increasing" was being recorded as satisfied. It
  now runs: **45 checks, 16 flagged.** Its Wikipedia block was also auditing the
  retired top-150 basket rather than the live one, so the rename defect could
  have survived it untouched.

---

## 8. Results

*Empty by design.* No confirmatory estimate exists. `17_stacked_event_study.py`
has never been run on real outcomes.

Discovery-period results under CAI-D will be filled in here as they arrive, with
the plain-language reading beside each number.

---

## 9. Limitations, in the order a referee will raise them

1. **The treatment is largely a national attention index.** One NYC-local search
   component, and it is heavily censored.
2. **Registry coverage gaps correlate with the hypothesis** (§5.6).
3. **Wikipedia pageviews do not exist before 2015-07-01.** Hard floor.
4. **Google Trends is a sample, not a census**, and its precision degrades over the
   decade — so a null in 2021–2024 is harder to interpret than a null in 2017–2020.
5. **B-HEARD contaminates the 2021–2024 arm** in the same direction as H1, on
   adoption dates that are 17-of-31 low-confidence.
6. **The EDPC recode (mid-2018)** sits inside the discovery window.
7. **The episode construct changed** after the original freeze, while blind to
   outcomes (§4.2) — disclosed, dated, with original wording preserved.
8. **One freeze incident** (§5.3).
9. **We do not use armed/unarmed status**, which is our protection against the Nix
   & Lozada critique of MPV coding — stated explicitly because a reader who knows
   that literature will ask.

---

## 10. Open decisions, with owners

| Decision | Owner | Status |
|---|---|---|
| Materiality of the freeze incident | Justin | open |
| Sign-off on the rebuilt episode list (70→94, 6 shared starts) | Justin | open |
| Jordan Neely: pre-specified in `CONFIRMATION_PLAN.md:23-25` but killed by a civilian, not police | Justin + Abrahim | open |
| Registered Report vs conventional submission | Justin | open |
| H2 (NYC Well) and H3 — in, out, or amended | Justin | open |
| `trends_nyc`: broaden the basket | **decided** 2026-09-10 | implementing |
| Episode construct: regime → shock | **decided** 2026-09-10 | implementing |
| Bridge exhibit → simulation instead | **decided** 2026-09-09 | pending |

---

## 11. Paper skeleton and display items

See `docs/PAPER_PLAN.md` for the full version. Summary:

**Drafting order** (not reading order): Methods → RECORD checklist → Introduction
→ Limitations → Results → Discussion → Abstract.

**Main text, four display items:**
1. Raw series — daily mental-health call share with CAI-D beneath, episodes marked.
2. Event-study plot from the stacked estimator, day −1 reference, null line drawn.
3. Outcome decomposition forest plot, placebos visually blocked off. *This figure
   carries the argument.*
4. Table 1 — the frozen episode list. The credibility of the pre-registration made
   visible.

---

## 12. Reading list

See `docs/RELATED_WORK.md`. The four that matter most to our defence:

- **Bor et al.** — the mental-health spillover result our question builds on.
- **Nix & Lozada** — the MPV miscoding critique. Our protection is that we do not
  use armed/unarmed status; say so explicitly.
- **Wu et al. (2023, PLOS ONE)** — normalised tweet counts to relative frequency
  for the same reason our raw-count index needs care.
- **Hölzl, Keusch & Sajons (2025, *Social Science Research*)** — Google Trends
  reliability across 360 studies. The single most likely methods objection.
