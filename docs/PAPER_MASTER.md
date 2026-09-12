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
- **Wikipedia's `agent=user` classification allegedly changed in April 2020**,
  non-retroactively, which would split the sample at the largest treatment
  episode. **Tested and the mechanism does not hold.** Comparing Apr 1–May 20
  against Feb–Mar within each year (so Floyd, May 25, is outside the window), the
  basket runs **+2.1 SD** above its non-event-year norm in 2020 — but an
  11-article *evergreen* control (Photosynthesis, Chess, DNA, …) moves +0.02,
  essentially flat. A reclassification is article-agnostic and would move the
  control too. 2021 shows a larger anomaly still (**+5.5 SD**) from the Chauvin
  verdict and Daunte Wright, events nobody disputes. This bounds any
  classification effect to less than the event signal; it does not prove none
  occurred.
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
- **What we gave up:** the index is honestly a **national** attention index, with
  no city-local component at all. That is a decision taken on evidence, not a
  gap — both candidate local components were measured and both failed. See §4.3.

### Layer 3 — technical

`CAI_D_COMPONENTS = ("wiki_ext", "trends_us")` — `scripts/config.py`.
Built by `scripts/12_build_cai.py`. Two components, one measuring reading and one
measuring searching; they correlate 0.479, which is the point of a composite.

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
**A gap found on 2026-09-11, and its root cause (finding T18).** Category
membership on Wikipedia is a property of a *page*, and a redirect is a page — so
the category walk collected redirects alongside articles and could not tell them
apart. **39 of 482 candidates (8%) were redirects.** Two consequences, filed as
separate defects before the common cause was found:

- **Duplicates.** A redirect and its target both survived into the basket, so the
  person was counted twice — `Eric_Garner` beside `Killing_of_Eric_Garner`,
  `Freddie_Gray` beside `Killing_of_Freddie_Gray`, eight in all.
- **Losses.** Where only the redirect was collected, the candidacy rule tested the
  *redirect's* title, which usually has no person prefix, so the article was never
  considered. **Walter Scott was absent from the treatment index entirely** —
  shot in the back while fleeing in April 2015, on video, one of the defining
  cases of the study period. Summed across his historical titles he carries
  2,228,711 views, which would rank him **15th of 121** basket articles, and the
  redirect that stood in for him peaks on **2016-07-08**, the Sterling/Castile week
  that is this index's strongest content validation. Jordan Edwards, killed
  2017-04-29 inside the discovery window, was lost the same way.

Redirects are now resolved at the point of collection, which fixes both at source.

`scripts/27_finalise_basket.py` applies the scope rule and writes
`data/reference/wikipedia_article_resolution.csv`.

Current basket: **120 articles / 119 people**, span 2013-01-27→2024,
**27 killed after 2020**. Every include/exclude decision with its reason is in
`data/reference/basket_decisions.csv`.

**How we ask Wikidata, and the three things it was getting wrong** (findings N1,
N2, N3). Deciding whether an article belongs in the basket needs three facts:
when the person died, where, and who killed them. We look those up in Wikidata.
Until 2026-09-12 we asked through a query language called SPARQL, and we now ask
through Wikipedia's ordinary web API instead. We only switched after running both
ways over the same 164 articles and comparing every field. Everything that
differed, the new way got right:

1. **Names with accents in them were being filed under a mangled spelling.** The
   old query turned `José` into `Jos%C3%A9` before sending it, and then filed the
   answer under that mangled name. The basket spells it `José`, so the two could
   never be matched up, and the article looked like one Wikidata knew nothing
   about. That is not a harmless filing error. José Campos Torres was then dated
   by matching his *name* against a list of victims, which matched the wrong
   person and gave him a 2014 date. Wikidata says he was killed in **1977** —
   outside the study period entirely. A spelling mismatch put an out-of-scope
   article into the treatment index, labelled "in range".
2. **Some articles came back empty and nothing said so.** Ma'Khia Bryant, one of
   the central events of April 2021, simply had no answer. The new route finds
   her at once. We now refuse to finish the basket unless every candidate article
   has been asked about, because "Wikidata has nothing on this person" and "we
   never got round to asking" are completely different facts, and only the first
   is a reason to leave someone out.
3. **Dates were being invented one digit at a time.** Wikidata can say "May 2010"
   without saying which day, and writes that as `2010-05-00`. The old route
   quietly turned it into `2010-05-01` — a specific day nobody claimed — and our
   own code then failed to read the raw form at all and recorded the article as
   having *no* date. We now keep what Wikidata actually says and note how precise
   it is.

Between them, **twelve articles had been excluded from the basket for a reason
that was false**. The count of articles turned away for "no date resolvable" fell
from 28 to 16 once both problems were fixed; the other twelve moved to reasons
that are true. Nothing in the old output looked wrong — that is the point, and it
is why `T.exclusion_reasons_true` now re-reads the evidence behind every stated
reason rather than trusting the sentence.

The basket is deliberately **not ranked by attention** — that would let the index
select its own inputs, which is the defect that retired `trends_victims`.

**Does the basket actually contain police violence?** (findings B1, B2.) Nobody
had ever checked, and the answer was no.

The basket is built by walking Wikipedia's category tree, and the walk records
only the **first** category it reaches an article through. For **61 of the 120
articles — just over half — that first category was a topic**: "Black Lives
Matter" (57 articles) or "2020/2021 United States racial unrest" (4). A topic
category says what conversation an article belongs to. It says nothing about who
killed anyone. And nothing downstream asked: the scope rule tests *when* and
*where* a death happened, never *who did it*. Wikidata's "manner of death" field,
the obvious place to look, is filled in for 6 of 174 candidates — and where it is
filled in it is not reliable, since Wikidata records Eric Garner's manner of
death as "natural causes".

So the treatment index — the thing this whole paper measures attention *with* —
contained nine killings in which the police were not involved at all. Each one is
confirmed by the first sentence of its own Wikipedia article: Ahmaud Arbery
(murdered while jogging), Renisha McBride, Markeis McGlockton (shot by Michael
Drejka), James Craig Anderson (killed by Deryl Dedmon), Tamla Horsford (found
dead after a slumber party), Nina Pop (stabbed in her apartment), James Scurlock
(shot by a bar owner), Carlos Carson (killed by a private security guard), and
Deona Marie Knajdek (killed by a man who drove into a crowd).

It also contained **Micah Xavier Johnson, who shot five Dallas police officers**
— attention to violence *against* police, which is the opposite of what we are
trying to measure. His date, 2016-07-08, is the single highest day in the entire
index.

`scripts/32_validate_basket_construct.py` now decides this per article, from
public evidence anyone can re-check. The distinction that does the work is
between a category that names **who acted** and one that names **a subject**:

| Names an actor — counts | Names a topic — does not |
|---|---|
| "African Americans shot dead by law enforcement officers in Ohio" | "Law enforcement controversies in the United States" |
| "Deaths in police custody in the United States" | "Police brutality in the United States" |
| "Cleveland Division of Police", "Law enforcement in Wisconsin" | "Protests against police brutality" |

Both kinds appear on real police shootings. Only the topic kind also appears on
deaths the police had nothing to do with — Tamla Horsford died at a party and
carries the controversy category; Carlos Carson carries two police-brutality
categories and his article says a private security guard killed him. Jacob Blake
carries the controversy category too, *and* "Law enforcement in Wisconsin",
because an officer shot him. Only the second kind survives that test.

Being in the Mapping Police Violence registry counts **for** an article and never
against one. MPV lists only police killings, so appearing in it settles the
question; not appearing settles nothing, because MPV omits Daniel Prude, Sandra
Bland, Marvin Scott, Javier Ambler and Leneal Frazier (§5.6).

The script carries **25 test cases whose answers were verified against the
articles themselves** — sixteen police killings and shootings that must be kept,
nine civilian killings that must not — and it refuses to write a basket at all if
the rule stops agreeing with any of them. Every rule in it was added or demoted
because one of those cases caught it.

**Two baskets result**, and the paper reports both:

- **Strict (109 articles) — primary.** Evidence names law enforcement as the
  actor. This is what CAI-D is built from.
- **Broad (118) — pre-registered sensitivity.** Adds the nine articles where
  nothing establishes who acted, so the paper can *show* whether the result
  depends on where the line was drawn instead of asserting that it does not.
- Attention to violence against police is in **neither**, and what removing it
  does to the 2016-07-08 peak is reported rather than quietly absorbed.

**Where, as well as who** (finding B2). The old country test excluded an article
only when Wikidata *named* a country outside the US, so an article with no
country listed passed by default — 58 of 120 did, and only 2 were ever excluded
this way. That is admission on absence, and the same reasoning would have
admitted a killing anywhere. Simply demanding a Wikidata country is not the fix:
it is missing for 44 of the 109 strict-basket articles, George Floyd and Deborah
Danner among them, which is a gap in Wikidata rather than a fact about the
country. The categories do carry it — all 109 sit under a US state, a US agency,
or an explicit United States category, and none under a non-US one — and that is
now recorded per article and checked.

### 4.2 What an "episode" is

**Layer 1.** An episode is a burst of unusual attention. We find the days when the
index is far above normal, and treat the start of each burst as an event.

**An episode is not a killing, and the paper must not imply that it is.** Measured
across the 75 rebuilt episodes, the article drawing the most attention in the
window belongs to someone who died **more than a year earlier in 52 of them
(69%)**, and within the 60-day attribution lookback in only **9 (12%)**. Episode 33
(2019-07-16) is Eric Garner, 1,825 days after his death — the week the DOJ
declined to charge Pantaleo. Episode 73 (2024-08-09) is Michael Brown, 3,653 days
— the Ferguson tenth anniversary, to the day.

That is not a defect in the treatment. Attention to police violence on the
anniversary of a killing, or on the day charges are declined, **is** attention to
police violence, and it is exactly the kind of salience shock the hypothesis is
about. But it changes what the estimand means: this design tests whether *bursts
of public attention* move EMS demand, where those bursts are driven by
anniversaries, trials, verdicts and prosecutorial decisions at least as often as
by new killings. Any sentence implying "after a police killing" would be false.

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
list = 70 episodes; rebuilt list = 75 episodes. The stringency really is constant
now — the rule selects 10.1%–10.3% of days in every year — and no episode spans
more than 14 days from start to end, against 235 under the regime rule. The
frozen file stays byte-identical on disk; the rebuilt list is written separately
to `data/reference/confirmation_episodes_rebuilt.csv`, and the diff between them
is published as a disclosed deviation.

### 4.3 What the index can and cannot claim

`trends_nyc` was the only nominally NYC-local component. It is **retired from
CAI-D as of 2026-09-11**, and the replacement built for it was rejected too. The
index is national. Both decisions were made on measurements, and both
measurements are worth stating, because "we have a local component" was load-
bearing for the paper's framing.

**Why `trends_nyc` had to go — three independent reasons.**

1. **It is censored.** 42.6% of its days are exactly zero — Google suppresses
   region-days below an undisclosed volume floor — rising from 26% censored in
   2020 to 71% in 2024. On those days it is not a level at all; it is an
   indicator of clearing the floor. The censoring is worst in 2021–2024, exactly
   where the exposed confirmation stratum sits. A 2026-09-10 refetch with the
   "Police brutality" topic entity and a wider term basket cut the zero share
   from 79% to 42.6% and removed a 4.48× stitching break, but did not solve it.
2. **Stitching breaks it.** Two boundaries (2015-12-27, 2022-07-23) drop the
   level to 0.32× and 0.26× with no corroborating move in `wiki_ext` — because a
   censored overlap window leaves too few positive days to estimate a scale
   from. This is a *consequence* of (1), which is why it could not be tuned away.
3. **It costs almost nothing to drop.** The national-only index correlates
   **0.9695** with the index as previously built, and keeps the same top days.

**Why `wiki_nyc` — built specifically to replace it — was rejected.** It is built
from Wikipedia pageviews on NYC police-incident articles and delivers what it was
designed for: **no censored days in any year**, correlating **0.54** with
`wiki_ext` and **0.62** with `trends_us`, so it is measuring the right thing. It
fails on something else — it cannot be made *both* local *and* disjoint from the
national basket.

- The basket is **11 NYC articles**, and **3 of them are already in the national
  `wiki_ext` basket**: Eric Garner, Akai Gurley, Deborah Danner. Those three are
  **59% of all `wiki_nyc` views**, and **Eric Garner alone is 53%**. Adding the
  component as built would give those three victims most of a third of the
  index — double-counting, not locality.
- Making it disjoint leaves **8 articles**, and the most recent killing among
  them is **2012** (Ramarley Graham; the rest run from 1975 to 2006). **None is
  inside the study window**, which begins 2015-07-01.
- The disjoint series carries variance the national components do not explain —
  R² is **0.454** — but that residual is not local news. **6 of its 8 largest
  positive residuals are Amadou Diallo**: a single-day viral spike on 2022-06-06
  and anniversary runs around 4 February.
- Tested directly against seven NYC police-violence events inside the window
  (Delrawn Small, Deborah Danner, Saheed Vassell, Kawaski Trawick, Daniel Prude's
  bodycam release, Jordan Neely, Win Rozario), the residual is inconsistent and
  **negative for three of them**. It does not reliably detect NYC events.
- Substituting it still **drops 2016-07-08 (Sterling and Castile) out of the
  index's top five**, losing the strongest content validation the index has.

So the component is not rejected for measuring the wrong thing — it is rejected
because its local content *is* its national content, and what remains once the
overlap is removed is a set of pre-2015 cases whose independent movement is
Diallo anniversary traffic. It survives as a validation exhibit, never as
treatment.

> **These numbers were wrong twice before they were right, and that is the
> finding (T14, T15).** An earlier version of this section rejected `wiki_nyc` on
> the *opposite* grounds — a **−0.18** correlation with `trends_us` and
> anniversary-dominated peaks. Those came from a **stale artifact**:
> `28_build_nyc_attention.py` had been given the historical-title fix and never
> re-run, so the series was still canonical-title-only and was missing Eric
> Garner entirely. Re-running it exposed two further defects in the same script —
> a category fetch that ignored the API's continuation cursor, so consecutive
> runs produced **different baskets**; and a per-title pageview fetch that
> returned `None` on any exception, so one rate-limited run produced a basket
> with Eric Garner **gone** and Diallo down from 2,772,084 views to 633,194,
> exiting 0 with a normal-looking summary. Only the third rebuild, with both
> fixed, is the one reported above.
>
> The conclusion survived all three revisions. **None of the original reasons
> did.** An artifact is only as current as its last run, and a measurement quoted
> from a file nobody regenerated is a claim nobody checked — which is why
> `V.artifacts_current` now compares every artifact against a fingerprint of its
> generating script's code.

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

**And the fix is now provably complete, not merely larger.** "More views" is not
evidence that nothing is still missing. The defect's actual signature is a series
that *starts late* — `Killing_of_Alton_Sterling` began 2021-04-25 for a man killed
in 2016, because the page was **moved** to that title and the earlier history
stayed behind. A low day count is a different thing: Wikimedia omits days with no
recorded views, so a quiet article is legitimately sparse, and a coverage
threshold cannot tell the two apart. It flagged 14 articles, 9 of them merely
quiet.

Separating them needs each article's **creation date**, since an article written
years after a killing correctly has no earlier series. With creation dates
resolved from the MediaWiki API for all 559 titles, every one of the **119** usable
articles starts within **3 days** of `max(death, article creation)`, median **0**.
Nothing is still hidden behind a rename. `T.no_lost_history` asserts it, and
restoring the defect for one victim makes the check fail with a 1,754-day lag.

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

**The redirect that hid a victim.** Wikipedia category membership is a property of
a *page*, and a redirect is a page — so the category walk collected redirects
alongside articles and could not tell them apart. 39 of 482 candidates were
redirects. Where a redirect *and* its target both survived, the person was counted
twice (nine victims, 449,549 views). Where only the redirect survived, the
candidacy rule tested the redirect's title — which has no "Killing of" prefix — so
the article was never considered at all. **Walter Scott**, shot in the back while
fleeing in April 2015 and filmed, one of the defining cases of the period, was
absent from the treatment index entirely. So was Jordan Edwards, killed inside the
discovery window.

**An error path that produced a plausible basket.** Wikidata returned HTTP 503
eight times, the scope resolver raised, and the finaliser went on to build a
basket against a *stale* scope file from a previous session — excluding 29
articles with the reason "no date resolvable", when the truth for many was "we
never asked". `Killing_of_Adam_Toledo` was dropped that way. Nothing in the output
distinguished a real absence from a failed fetch; only the `FAIL` line in the run
manifest showed it. The finaliser now refuses to decide anything unless every
candidate has a scope row.

**A rate limit that deleted the largest case.** The NYC basket builder returned
`None` on *any* exception when fetching a title's pageviews, so a 429 was
indistinguishable from "this title has no data". One run hit three rate limits and
produced a basket in which Eric Garner had **vanished** and Amadou Diallo had
fallen from 2,772,084 views to 633,194 — and it exited 0 with a normal-looking
summary. Consecutive runs disagreed about which victims existed.

**Fifteen checks that could pass for the wrong reason.** See §7.5. This is the most
transferable lesson in the project.

**The pattern behind all of them.** Every defect in this section is the same shape:
*an error path that is indistinguishable from success*. A rename that silently
drops history, a rate limit read as "no data", a truncated API response read as "no
categories", a failed query read as "no date", a redirect read as an article. None
announced itself; each produced output that looked exactly like correct output. The
methodological claim this paper can make is not that we avoided these — we did not
— but that we built the apparatus that finds them, and that the apparatus found
them repeatedly *after* the point where a careful project would normally have
stopped looking.

### 5.3 The freeze incidents — **two**, both disclosed

**F1 (2026-09-10).** During an automated audit, an agent computed the citywide
mental-health call share by year for 2005–2026, including confirmation years, in
order to demonstrate that `ems_citywide_day_trends.parquet` had no freeze guard.
It deliberately did not restate the values.

Narrow — a citywide annual aggregate of a level series, with no episode alignment,
no treatment merge, no district variation, and no test of H1 — but real.

**F2 (found 2026-09-11, and it had never been recorded).** Verifying finding O3
required knowing when each EDP-family call type was born, and that question was
answered by querying NYC OpenData `76xm-jjuj` **directly**. The SODA API is not an
artifact, so no freeze guard sees it: coverage is a list of files in
`data/processed/`, and a direct query bypasses all of it.

What was read, precisely: first-record timestamps and whole-period totals per call
type; citywide monthly counts across the 2021-05/06 boundary; annual EDP-family
totals including 2016 and 2024; and — the part that matters — **precinct-level
EDPM counts for June 2021**, with the three B-HEARD pilot precincts compared
against the rest.

That is **district-level variation in the confirmation window, compared across the
B-HEARD boundary**, and it is materially more than F1. It did not touch the
attention index, episode dates, event-time alignment, or any test of H1. But **a
specification decision was taken on the result**: EDPM was retained in the EDP
family because the comparison refuted the claim that it is the B-HEARD routing
code. That is exactly the class of decision the freeze exists to keep uninformed
by confirmation data.

The decision is defensible on other grounds — a routing code would concentrate in
pilot precincts, and EDPM appears citywide from its first day — but "defensible on
other grounds" is a judgement for the supervisor, not a reason to leave an access
unrecorded.

**Why it went unnoticed for a day.** F1 was reported by the agent that caused it,
which created the impression the freeze had exactly one breach. F2 produced a
finding full of confirmation-period numbers and nobody asked where they came
from: the numbers were read as *evidence*, not as an *access*.

Materiality for both is for the supervisor to judge, not us. Both gaps are now
closed in code: outcome artifacts outside the guard's coverage (F1), and the
source API that no artifact guard can see (F2).

**The posture taken from 2026-09-11, and it is reversible.** Three outcome-side
questions remain open — the disposition filter (O1), two structural breaks that
sit *inside* the 2015–2016 confirmation window (O2), and how EDPM is handled
(O3) — and none can be fully settled without looking at confirmation outcomes
again. Rather than take a third access, the decision is to **hold the line
strictly**:

- O1 is resolved on discovery data and the FDNY data dictionary only.
- O2's handling is **pre-specified blind**: the confirmatory specification must be
  robust to both alleged breaks whether or not they are real, with each carried as
  a pre-registered sensitivity rather than a measured correction.
- O3 is closed on the record already taken; nothing further is derived from it.

The cost is accepted openly: if a genuine break does sit in 2015–2016, we will
find it only after the freeze lifts, and at that point it can be **disclosed but
not fixed**. That is the price of not spending the window's remaining credibility.

This is a floor, not a ceiling. The alternative — finishing the outcome definition
properly and then depositing a timestamped external pre-registration (OSF, or
PCI-RR as a Registered Report), so an external timestamp replaces the internal
freeze as the credibility mechanism — is the standard remedy once an internal
freeze has known breaches, and remains open at any point. Holding the line now
does not foreclose it; taking a third access would have.

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
check — **56 checks** at present. States are PASS / FAIL / **BLOCKED** / ERROR,
where BLOCKED means "could not evaluate" and is deliberately *not* a pass.

They do **not** all pass right now, and this document says so rather than
rounding up. Six fail and two are blocked, and all eight are the same piece of
unfinished work: the article basket is mid-rebuild, so the counts derived from it
have moved, two artifacts still predate the script that writes them, and the null
calibration is being regenerated after a smoke-test run overwrote it. Each is
named with its remedy in `outputs/tables/regression_suite.csv`.

The pass count is deliberately not quoted here. It changes with every run, so a
number in prose would either be wrong or would have to be edited constantly —
and a claim nobody can keep current is a claim nobody checks.

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

Four checks hold the registers in place — `V.sources_verified` (which **BLOCKS, never
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
  now runs: **42 checks, 2 flagged.** Its Wikipedia block was also auditing the
  retired top-150 basket rather than the live one, so the rename defect could
  have survived it untouched. Both remaining flags are data limitations rather
  than defects: B-HEARD's 17 low-confidence adoption dates, and 16 basket
  articles for which Wikidata publishes no date of death, whose coverage
  therefore cannot be assessed and is not assumed to be fine.

---

## 8. Results

*Empty by design.* No confirmatory estimate exists. `17_stacked_event_study.py`
has never been run on real outcomes.

Discovery-period results under CAI-D will be filled in here as they arrive, with
the plain-language reading beside each number.

---

## 9. Limitations, in the order a referee will raise them

1. **The treatment is a national attention index, with no local component.**
   Both candidates were built and both were rejected on measurement (§4.3):
   `trends_nyc` is censored on 26–71% of days depending on the year, and
   `wiki_nyc` cannot be both local and disjoint from the national basket —
   67% of its views come from three articles already in `wiki_ext`, and removing
   them leaves four articles whose most recent killing is from 1999. The paper
   therefore tests whether *national* attention moves NYC demand, and treats the
   presence of an NYC killing in an episode as a heterogeneity dimension rather
   than as treatment. **We cannot separately identify New Yorkers' own attention
   from national attention**, and no claim in the paper should imply otherwise.
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
| Sign-off on the rebuilt episode list (70 → 75) | Justin | open |
| Jordan Neely: pre-specified in `CONFIRMATION_PLAN.md:23-25` but killed by a civilian, not police | Justin + Abrahim | open |
| Registered Report vs conventional submission | Justin | open |
| H2 (NYC Well) and H3 — in, out, or amended | Justin | open |
| `trends_nyc`: retire from CAI-D; `wiki_nyc` rejected as its replacement; index is national | **decided** 2026-09-11 | done |
| Episode construct: regime → shock | **decided** 2026-09-10 | done |
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
