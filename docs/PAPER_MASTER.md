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
| Wikipedia pageviews | Wikimedia REST API | **2015-07-01**→2024 | 120 articles in scope, 109 in the strict basket |
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

**What removing the anti-police articles actually does** — measured, because
this exclusion lands on the most load-bearing day in the project. 2016-07-08 is
the index's highest day and its strongest validation (Alton Sterling and Philando
Castile), and it is also the day after the Dallas attack. A reader is entitled to
ask whether that peak was ever about Sterling and Castile at all.

`scripts/33_antipolice_sensitivity.py` rebuilds the index with both articles added
back, through the same construction, and reports both:

| | published (excluded) | counterfactual (included) |
|---|---|---|
| cai_d on 2016-07-08 | **12.5693** | 13.1356 |
| rank of that day | **1 of 3,472** | 1 of 3,472 |

**2016-07-08 is the highest day either way.** The excluded articles add 205,332
views that day, which raises the index by 0.57 standard deviations — real, but not
what put that day on top. The validation survives its own strongest objection.

Two things not to round away. Micah Xavier Johnson's articles carry **3,775,980
views** across 3,099 days, which would place him among the largest dozen articles
in a 107-article basket; this is not a marginal exclusion. And the two articles
have traffic on **3,105 of the index's 3,472 days**, so they were contributing
throughout rather than only in July 2016 — the largest single-day effect is
**1.03 standard deviations, on 2017-08-16**, inside the discovery window.

**One signal was being gathered and ignored, and it mattered.** The classifier
fetches each article's opening sentence — the most direct statement anywhere of
who did the killing — writes it into the review file, and never consulted it. The
decision rested on categories plus membership of the victim registry, and registry
membership is an **exact name match**.

That is a thin thread to hang a basket on. The registry holds four different
James Andersons, none of whom is the James Craig Anderson this basket must
exclude, and two different Keenan Andersons who died in 2023. Three published
articles rested on that lookup as their only positive evidence, and one of them
was **Breonna Taylor** — her membership decided by whether a name string matched,
while her own article's first sentence says plainly that Louisville Metro police
officers forced entry into her apartment.

The lead sentence is now read first, and only as a *positive* signal: a miss
costs nothing, because the category and registry rules still apply, so it is
tuned for precision rather than coverage. Its canaries are tested on the sentence
alone rather than on the final classification — an article that also carries a
police category would come out right whatever the lead rule did, so testing the
outcome would let the rule rot unnoticed. The case it has to survive is David
Dorn, "a 77-year-old retired police captain", who was killed by looters: the
words are in his lead and he is not a police-violence case. Measured at **zero
false positives** across all thirteen civilian killings in the candidate set.

**All three baskets rebuilt byte-identical.** Nothing about the treatment index
changed; what changed is that no published article's membership now depends on a
name lookup that cannot tell two people apart. Two further articles were
corrected on construct along the way — Adama Traoré and Luana Barbosa dos Reis
*are* police killings, in France and Brazil, and remain excluded on country
rather than on a mistaken reading of what happened to them.

**The broad arm now exists, and the two agree.** The sensitivity was
pre-registered but not buildable — the episode list it needs had never been
produced, so the confirmatory script recorded it as `NOT_RUN`. Both arms are now
built, side by side, neither overwriting the other:

| | strict (primary) | broad (sensitivity) |
|---|---|---|
| articles | 109 | 118 |
| episodes | 74 | 75 |
| top attention day | 2016-07-08 | 2016-07-08 |

The two indices correlate **0.9975** across all 3,472 scored days, differ by
0.051 standard deviations on average, and share **71** episode start dates —
three appear only in the strict arm, four only in the broad. The largest
single-day gap is 2.79 SD, on 2022-01-08.

That is worth saying plainly: **the nine disputed articles barely move the
index.** It does not make the strict/broad decision unimportant — it makes the
paper's claim about what the index *measures* defensible without resting on a
result that happens to survive. The line was drawn on evidence about who did the
killing, and the arm on the other side of it is published rather than described.

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
across the 74 rebuilt episodes, the article drawing the most attention in the
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
list = 70 episodes; rebuilt list = 74 episodes. The stringency really is constant
now — the rule selects 10.1%–10.3% of days in every year — and no episode spans
more than 14 days from start to end, against 235 under the regime rule. The
frozen file stays byte-identical on disk; the rebuilt list is written separately
to `data/reference/confirmation_episodes_rebuilt.csv`, and the diff between them
is published as a disclosed deviation.

**Which episode list the models actually use.** There are two, and until
2026-09-12 the code used the wrong one.

`confirmation_episodes.csv` holds 70 episodes built under the old fixed-threshold
rule. It is the **pre-registration record** — evidence of what was specified
before any of this was rebuilt — and it is kept byte-identical to its committed
version, with a check that fails if a single byte moves.
`confirmation_episodes_rebuilt.csv` holds 74 episodes under the shock rule with a
within-year threshold, and is the list this project adopted.

The decision to estimate on the rebuilt list was taken, written down, and never
carried into the code. All four estimators — the stacked event study, the
difference-in-differences, the figures, and the null calibration — opened the
frozen file by name. Nothing caught it, because both files exist, both parse, and
both have identical columns: the wrong one produces a perfectly well-formed
answer to a different question. The filename now lives in one place
(`config.EPISODE_LIST_PRIMARY`) and a check reads the estimator sources and fails
if any of them names the frozen file in code.

One consequence, stated rather than absorbed: the null calibration that was
running when this was found is calibrated to the **frozen** list's geometry — 30
discovery episodes rather than the rebuilt list's 28 — so it has to be re-run
against the adopted list before it can gate anything.

**Episodes cluster, and that costs information.** 36 of the 74 rebuilt episodes
have another episode starting within 28 days, and the closest pair start 10 days
apart. The definition matters and is part of the claim: measured start-to-start
at 28 days inclusive it is 36; measured from one episode's end to the next one's
start it is 51. A bare count is not checkable, so the register carries the rule
as well as the number.

What this costs is smaller than expected, and in a different place. Because
contested district-days go to the *nearer* episode, a first-week day is lost only
to a *later* start within 14 days — and the minimum gaps are large enough that
the total first-week loss is **2 episode-days out of 592** across all three
strata. The loss lands in the **pre-period** instead, 9–15% of it, which is
exactly what the pre-trend test spends. So clustering does not thin the estimate;
it thins the evidence that the estimate is credible.

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
total calls per district-day **66.1**. Built by `scripts/01_build_panel.py`.
Districts with fewer than 5 calls on a day are excluded from share calculations.

### 5.1c Does the Trends component lose resolution over the decade?

It was argued that it must. Google returns integers rescaled to each request
window's own maximum, US search interest in police violence falls sharply across
the decade, and the request windows are fixed — so the daily series should
collapse toward a handful of distinct values by 2024, loading the confirmation
window with measurement error the discovery window does not carry.

The mechanism is right and the conclusion does not follow from it. Rescaling to
the window maximum is precisely what keeps every window spanning 0–100 whatever
the underlying level. Measured on `trends_us`, the only Trends series in the
index: the quantization step relative to the series' own scale is **0.0020**
across 2015–2019 and **0.0016** across 2021–2024 — a ratio of **0.82**, slightly
*finer* late, against a claimed fivefold coarsening — with 121 and 118 distinct
values a year and **365 non-zero days in every year of the decade**.

Resolution does collapse in `trends_nyc`, and by a different mechanism than the
one proposed: not coarseness but censoring, with non-zero days falling from 236 a
year to 161 and 71% of 2024 at zero. That series was retired from the index on
independent grounds, so it attenuates nothing estimated here — which is the only
reason this is a paragraph rather than a problem.

### 5.1d Coverage breaks inside the confirmation window — read under a declared exemption

**Layer 1.** Before the sealed half of the data is analysed, we checked whether
the *way calls are recorded* changes inside it: whether any call code appears or
disappears there, and whether the share of calls with no district changes. We
did this without looking at any call volume or any outcome, and we wrote down
what we would look at, and what we would do about it, before we looked.

**Layer 2.** Finding O2 named two such breaks in 2015–2016 — a geocoding regime
change at 2016-01-01 and the retirement of the INJALS injury code — and asked
for a coverage table before CP2. Producing it means reading confirmation-window
rows of the outcome extract, which the freeze protects, and "it is only
metadata" is the reasoning behind both freeze incidents in §5.3. So the read was
made a **declared access**: its scope is written in the `CONFIRMATION_PLAN.md`
addendum (§18) and in `config.FREEZE_EXEMPTIONS`; it runs only through
`freeze_guard.declared_access`, which refuses any undeclared exemption or any
caller other than `35_coverage_breaks.py` and appends a row to
`data/reference/freeze_access_log.csv` every time; the outputs go through
`declared_output`, which refuses any column the declaration does not name; and
`D.declared_access_scoped` holds all of that and fails if an output is widened
(defeat-tested). What was emitted is per call code its first and last date, and
per year the share of calls with no district. No count by period, no mean, no
share of any call group.

**Layer 3.** `data/reference/ems_call_code_span.csv`,
`ems_missing_district_rate_by_year.csv`, `ems_coverage_breaks.csv`. Of the
codes in any outcome group, **20 outcome-group codes** are born or retired
strictly inside a confirmation analysis window:

| window | outcome-group codes born or retired inside it | which |
|---|---|---|
| C1a, 2015-07→2016-12 | 1 | INJALS retired 2015-12-16 (injury placebo); and the geocoding step at 2016-01-01 |
| C1b, 2021-01→2021-05 | 2 | CARDFT born 2021-01-06 (cardiac placebo); ALTMFT born 2021-03-10 (altmen, inside the narrow mental-health family) |
| C2, 2021-06→2024-12 | 17 | EDPM born 2021-06-03 and EDPW retired 2021-08-25 (EDP family, both already disclosed in `config`); the other 15 are FC/FT dispatch variants across the cardiac, asthma, altmen and drug groups |

The share of dispatched calls with no community district is **2.97%** in 2015
and **0.91%** in 2016 — a ratio of **0.31**, the only adjacent-year change
beyond a factor of two anywhere in 2014–2024 — and sits between 0.87% and 0.98%
in every later year. So the geocoding break is real, dated to 2016-01-01, and
confined to the first half of C1a.

**What follows is pre-specified, not chosen.** The primary estimates do not
change. For each break, addendum §18 fixes a sensitivity: re-estimate the
affected group in the affected stratum with every episode dropped whose ±14-day
window contains the break date, and report it beside the primary. On the
rebuilt episode list that touches episode 4 (2015-12-28; both C1a breaks),
episode 40 (2021-01-05; CARDFT) and episode 41 (2021-03-12; ALTMFT) in C1, and
the C2 episodes around EDPM's birth and EDPW's retirement. The geocoding
sensitivity is expected to show nothing: O2's own refutation measured the
artifact a proportional geocoding change induces in a *share* at about 0.0002
on the mental-health share, well below the first-week statistic's resolution.
The value of running it anyway is that a reader sees the number rather than the
assurance.

### 5.1a A measurement break inside the treatment series

`wiki_ext` counts Wikipedia pageviews filtered to `agent=user`. In late April
2020 Wikimedia added a third agent class, `automated`, and **did not apply it
retroactively** — so `user` means "not obviously a spider" before that date and
"not a spider and not automated" after it. The treatment index has a measurement
break in it, five weeks before the largest episode in the study.

That is where this was expected to bite, and it does not. Measured on the
articles this index is actually built from — not on Wikipedia as a whole, which
is where the often-quoted 5–8% bot-spam figure comes from — the automated share
across 2017–2020 is **0.10%**, and the shift it implies in the standardised
index averages **0.0009 SD**. Against a Floyd episode whose index sits several
standard deviations up, that is not a correction anyone would notice.

**It is large where nobody had looked.** The automated class grows every year
after it is introduced: 0.8% of views in 2021, 3.4% in 2022, 6.2% in 2023. Across
2021–2024 the mean shift is **0.0856 SD — ninety times the discovery-window
figure** — with a single-day maximum of 1.58 SD in 2024. That window is half the
confirmation sample and the whole of stratum C2.

So the break is a footnote for the discovery result and a live measurement
problem for the confirmatory one, which is the reverse of how it was filed. The
comparable series across the decade is `user` before the break and
`user + automated` after it — which is what pre-break `user` already was. The
frequently proposed alternative, refetching everything under `all-agents`, is
wrong in direction: it adds spider traffic, a larger contamination than the one
being removed.

The class really is absent beforehand, which is what licenses that splice:
`automated` is **exactly zero** on every day through 2019 and first appears on
**2020-04-29**. That is checked rather than cited.

**The spliced series exists as a pre-registered sensitivity arm** (addendum
§20; `config.ARMS["spliced"]`, built by the same pipeline as the broad basket
under the `_spliced` suffix, on the strict basket). Measured against the
primary index over the 3,472 scored days: the two are **identical on 100%** of
days through 2019 — the construction guarantee, asserted by a check rather than
assumed — correlate **0.9996** overall, and differ after the break by
**+0.0660 SD** on average across 2021–2024 with a single-day maximum of
**0.9758 SD**. The episode lists share **72** of their 74 starts. So the arm
changes nothing the discovery result rests on and is a live sensitivity for
C2, which is what the break's location implied.

### 5.1b What each episode actually is

Episodes were named by asking which recently-killed person in Mapping Police
Violence drew the most attention in the window. That is a reasonable question,
and it is not the question the episode table asks, which is *what is this
episode about*. The difference cost more than it looks.

**Forty-five per cent of episodes had no name at all** — 33 of 74, and 16 of 29
in discovery. The largest of them is the second-biggest attention episode in the
entire discovery window, 2020-08-24 to 09-07. No registry of *killings* keyed on
*date of death* can explain it: Jacob Blake was shot on 2020-08-23 and survived,
and Daniel Prude's death became public when the video was released on
2020-09-02, five months after he died — and Prude is not in Mapping Police
Violence at all.

**Where it did produce a name, it was usually the wrong one.** The week of
2020-09-22 was labelled "Dijon Kizzee" while 87% of basket attention was Breonna
Taylor — that was the week a grand jury declined to indict the officers in her
case. 2015-07-23 was labelled "Samuel DuBose; Jonathan Sanders" while 83% was
Sandra Bland, two days after her dashcam video was released. 2017-06-16 was
"Michael Brown; Jordan Edwards" while 76% was Philando Castile, the day Officer
Yanez was acquitted. 2017-12-07 was blank while 78% was Daniel Shaver, the day
Philip Brailsford was acquitted.

The pattern is the same every time, and it is the hypothesis of a finding filed
months ago: **attention is driven by events that are not deaths** — a video
release, an indictment, a verdict — and a death-date registry cannot see them.
Widening the lookback window does not fix this and actively makes it worse,
because it lets long-past deaths capture episodes they had nothing to do with.

So each episode now carries a second name, built from the treatment series
itself: the basket articles people actually read during the window, ranked by
share and aggregated by person. It needs no death date and makes no assumption
that a death was the trigger. **Every episode is now accounted for**, and the
2020-08-24 episode reads as what it plainly was: Jacob Blake, 47% of basket
attention.

Both names are kept. They answer different questions, and where they disagree
the disagreement is the finding.

This also turns "densely clustered periods cannot separate individual killings"
from an assertion into a number. The leading person's share of attention is
55% for the George Floyd episode, 47% for Jacob Blake's, 87% for the Breonna
Taylor grand-jury week — and a median of **37% across discovery**, with only 11
of 29 episodes having anyone above half. That is the measurable form of the
claim, reported per episode rather than asserted once.

*(The identification of the specific triggering events above — which verdict,
which video — is read off the articles themselves and should be cited as such in
the final text. What the data establishes on its own is who was being read.)*

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
returned **79,439,814 views**. Of the **116** articles the title resolver covered,
**112** turned out to have more than one historical title: Michael Brown 13.7×,
Philando Castile 8.4×, Breonna Taylor 7.4×, Tamir Rice 6.1×, Eric Garner 4.5×.
Of the **109** articles in the published basket, **107** now return a usable
series.

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
resolved from the MediaWiki API for all 530 titles, every one of the **107** usable
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

**A fourth arm found wired into nothing, and a check that passed for the wrong
reason about it.** `fit_dose_response` — the specification that scales the effect
by how big each episode actually was, rather than treating a peak of 12.67 and
one of 1.40 identically — was written, documented in the estimator's own header,
committed, and called by nothing. A search for its name across the repository
returned exactly one hit: its own definition. That is the third such arm in this
rebuild, after the count-model arm and the B-HEARD control.

The check written to catch that then did the same thing in miniature. Its first
version looked for the function's name anywhere in a file — and it passed with
the call deleted, because the comment *above* the call site explains that this
function used to be dead code and names it. A check meant to catch "documented
but never called" was satisfied by the documentation. It now parses each script
and counts only an actual call, and the defeat test deliberately leaves the
comment in place to prove the distinction holds.

**The pipeline could not have produced the figures, and nothing said so.**
`08_figures.py` read a column called `mh_narrow_calls`. The panel's column is
`mh_narrow`; `mh_narrow_calls` exists only as a metric *label* in the QC output of
another script. So the figure script raised on Figure 1 — the first figure — and
had never produced anything at all. No check caught it because no check runs the
figures.

Underneath that sat a worse one. `run_all.py` verifies, after each stage, that a
stage which exited 0 actually wrote something. That guard reads the stage's
declared outputs — so a stage declaring *no* outputs is exempt from it, silently.
**All seven model stages declared exactly that**, which is the half of the
pipeline where a silent no-op matters most: a model that fits nothing, writes
nothing and exits 0 was recorded as a pass. Two stages were missing from the
pipeline entirely while other stages read their output, so a clean clone could
run everything and still fail on a missing file.

Figure 5 is retired rather than fixed. It compared the original specification to
the corrected one, and its input traces back through two scripts to raw Twitter
exports that are **not in the repository** — the chain is dead at the source, so
nobody can rebuild that figure, including us. Its argument is carried instead by
the z-scoring simulation, which plants a known effect and shows what within-window
standardisation does to it. A simulation anyone can re-run is a better exhibit
than a comparison against a series nobody can obtain.

**The z-scoring artifact, measured — and the headline turned out to be the other
way round.** `scripts/25_zscore_simulation.py` plants a known effect and estimates
it three ways: with the awareness measure on its fixed 2017–2019 scale, with it
re-standardised inside the analysis window, and with it merely re-centred inside
the window. Everything is labelled SIMULATED, every row of every file it writes.

Re-centring turns out to be harmless — the episode × district fixed effect absorbs
it exactly. **Only the division does damage**, and the damage is an exact identity
rather than an asymptotic argument: the z-scored coefficient equals the true one
multiplied by the within-window standard deviation of the regressor, verified to
about 1e-16 on every fit.

That identity is what makes the result uncomfortable. The multiplier is a property
of *which rows are in the sample*, so it moves when the sample does — and it moves
far more with **composition** than with window length:

| | the multiplier runs | |
|---|---|---|
| window length (same episodes, 15 → 45 realised days) | 2.203 → 2.092 | **1.05×** |
| sample composition (same window, different episodes) | 1.104 → 3.515 | **3.18×** |

We had expected window length to be the story. It is the weak channel. The strong
one is composition, and the numbers are blunt: **dropping a single episode — the
one starting 2020-05-26 — moves the coefficient 25%**, and an ordinary robustness
column labelled "exclude 2020" roughly halves it. The planted effect is
byte-identical in every one of those runs. A reader would see a coefficient
collapse under a routine sensitivity and conclude the finding was fragile, when
what actually moved was the unit the coefficient is denominated in.

This is why the measure is standardised once, on a fixed reference window that
contains no George Floyd, and never re-standardised inside a sample.

### 5.3 The freeze incidents — **three**, all disclosed

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

**F3 (2026-09-09; found 2026-09-13, in the register itself).** The refutation
of finding O2 — the one that measured how little the 2015–16 geocoding break
could move a share — did so by computing record-level statistics from the
outcome extract for 2014–2016: missing-district rates by year, by sub-window and
by call type, the INJALS code's monthly counts and last timestamp, INJMAJ's share
across the year boundary, and the estimated step in the mental-health share
itself. The numbers were written into the finding's corrected claim, where they
sat for four days as *evidence* while this section said the freeze had been
breached exactly twice and recorded a decision not to take "a third access". It
had already been taken. No artifact guard or API guard can see an agent opening
a gitignored file, which is why the fix is procedural as much as structural:
a read of the confirmation window that has to happen is now **declared** —
scoped in `config.FREEZE_EXEMPTIONS`, disclosed in the addendum first, logged
on every run (§5.1d) — and the audit prompts used since forbid opening outcome
files at all. The coverage facts the paper cites come from that declared access,
not from F3.

Materiality for all three is for the supervisor to judge, not us. The gaps are
closed in code where code can close them: outcome artifacts outside the guard's
coverage (F1), the source API that no artifact guard can see (F2), and a
declared-access path with a log for the reads that must happen (F3).

**The posture taken from 2026-09-11, and it is reversible.** Three outcome-side
questions remain open — the disposition filter (O1), two structural breaks that
sit *inside* the 2015–2016 confirmation window (O2), and how EDPM is handled
(O3) — and none can be fully settled without looking at confirmation outcomes
again. Rather than take a third access, the decision is to **hold the line
strictly**:

- O1 is resolved on discovery data and the FDNY data dictionary only.
- O2's handling: the coverage facts were established on 2026-09-13 under a
  **declared, scoped, logged access** disclosed before it ran (§5.1d, addendum
  §18) — after F3 showed the "third access" this paragraph had declined to take
  had already happened undeclared. The breaks are carried as pre-specified
  sensitivities, never as a change to the primary.
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
| Confirmation A | 2015-07-01 → 2016-12-31 | **no outcome has entered a model or test** (accesses disclosed in §5.3 and §5.1d) — no COVID, no B-HEARD |
| Confirmation B | 2021-01-01 → 2024-12-31 | **no outcome has entered a model or test** (accesses disclosed in §5.3 and §5.1d) — B-HEARD control required |

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

**Layer 1.** Before trusting our method on real data, we ran it two hundred times
on fake data built to contain *no* effect. A trustworthy method should cry wolf
about 5% of the time. Ours cries wolf **5.0%** of the time, and the full spread of
its answers is the right shape.

**Layer 3.** `scripts/18_null_calibration.py`, 200 sims × 200 draws:

```
VERDICT                   CALIBRATED
empirical rejection rate  0.05     nominal 0.05, band [0.0198, 0.0802]
KS uniformity (lattice)   p = 0.7516
AR(1) rho                 0.0482   estimated from the real panel
```

These are the figures **regenerated on 2026-09-13** from a clean container under
the corrected code — the (1+k)/(1+n) p-value form, the lattice uniformity test,
and per-draw seeding (findings RI1, RI2, N6). The run they replace, made before
those corrections, read 0.06 and 0.6767; both verdicts are CALIBRATED and both
sit inside the band, and the numbers moved because the placebo draws and the
test moved, not the design.

Uniformity is the property that matters — a correct rejection rate with a
non-uniform distribution still means a broken statistic. The synthetic panel
carries a **citywide day shock**; without one the null is easier than reality and
would certify an estimator whose error bars are ~3× too narrow.

The gate refuses a verdict below 200 sims (verified: a 4-sim run prints
UNDETERMINED and exits 2). The artifact it replaced read CALIBRATED from 12 sims
with no real panel. A run that completes fewer sims than the one already on disk
now refuses to publish at all, because an 8-sim smoke test once overwrote the
200-sim verdict and said nothing about it (§5.2).

The verdict above is the one calibrated against the **adopted** episode list. An
earlier 200-sim run used the frozen list's 30 discovery episodes rather than the
adopted list's 29, and had to be redone once that was noticed — the null a
calibration certifies is a statement about a specific episode geometry, not a
general property of the estimator. Both runs came back CALIBRATED and inside the
band (0.05 against 0.06), so nothing turned on it, but the second run is the one
that describes the design being estimated.

**A calibration certifies one stratum, not the estimator.** That sounds obvious
written down and was not obvious in the code: a single `null_calibration.csv`
held one verdict, and nothing said which sample geometry or which way of drawing
placebo dates it described.

It matters because the three strata do not share a way of drawing them. The
method shifts the whole real sequence of episode dates by one random anchor and
throws the draw away if the sequence no longer fits. Discovery and C2 have room —
190 and 53 days of slack, and 500 of 500 draws land. **C1 has none.** It is two
windows sitting either side of the whole discovery period, so there is no single
stretch to slide within: 41% of anchors land outside C1 entirely, and its 2021
block alone would need 139 days of a 120-day interior. Every draw is rejected, so
the p-value on the *clean* stratum — the one the whole design exists to obtain —
comes back as nothing at all, after spending its entire budget getting there.

A circular shift over the days C1 actually contains works, and is a **different
null**. It keeps each episode's position relative to the others, so clustering
survives; it does not keep calendar gaps across the seam between the two windows.
So each stratum is now calibrated separately, each verdict records the scheme and
geometry it certifies, and a check recomputes what each stratum requires and
refuses a verdict that certifies something else. All three are now discharged, at
200 simulations × 200 draws each:

| stratum | scheme | geometry | episodes | rejection at α=.05 | KS p | verdict |
|---|---|---|---|---|---|---|
| discovery | anchor shift | contiguous | 29 | 0.05 | 0.7516 | CALIBRATED |
| C2 | anchor shift | contiguous | 30 | 0.06 | 0.4878 | CALIBRATED |
| C1 | circular, within block | gapped | 15 | 0.04 | 0.1229 | CALIBRATED |

C1's certificate under the within-block scheme landed on **2026-09-13**, 200
simulations × 200 draws: rejection rate **0.04** against the band
[0.0198, 0.0802], KS statistic **0.083**, lattice p = **0.1229**, median
p-value **0.4776**. The verdict that certified the seam-crossing scheme was moved
aside rather than left in place to be misread: a calibration certifies one
scheme; when the scheme is replaced the certificate does not carry over, and an
artifact that says CALIBRATED about a null nobody draws from any more is worse
than no artifact. C1 remains the weakest of the three strata — a KS p of 0.12 is
a pass, not a comfortable one — and the 1,000-simulation certificate the
pre-freeze gate requires is the run that decides whether the within-block null
is uniform, not this one. Its predecessor's history is kept below because it is
how the seam was found.

**Under the seam-crossing shift, C1 passed by a margin worth stating rather than
burying, and then the margin turned out to be a symptom.** Its KS statistic was
0.0875 against a critical value of 0.0960 at 200 simulations, and its p-values
leaned the wrong way: mean 0.457 against 0.5. The rejection rate at α = 0.05 was
exactly 0.05, which is reassuring only because 0.05 is the one α that test
examines. (These figures describe the superseded certificate, which was moved
aside; they are history, not a claim about the null now in use.)

The pre-freeze gate requires uniformity at 1,000 simulations, where the critical
value falls to 0.0429 — less than half the statistic observed. So a 1,000-run was
started, and killed by an unrelated container restart forty-five minutes in. That
turned out to be the luckiest failure in the project, because looking into it
found the reason C1 is non-uniform, and it is not sample size.

**C1's null does not reproduce C1's design.** The stratum really has ten episodes
in its 2015–16 block and five in its 2021 block. The circular shift treats the
two blocks' admissible days as one sequence and slides through it, so the split
it produces is whatever a uniform shift implies — and block 1 holds 520 of the
641 admissible days. The null therefore places a mean of **12.1** episodes there
rather than ten, its most common draw is thirteen, and it reproduces the real
ten-five split on **12.4% of draws**. The placebo designs differ structurally
from the design being tested: different episodes per block, different effective
sample, different fixed-effect structure. Non-uniform p-values are the expected
consequence, not a surprise.

Two alternative explanations were checked and rejected, and both turned out to
be real defects that simply were not *this* defect.

The p-values are discrete — they live on a lattice of 1/201 — and were compared
against a *continuous* uniform, which the code's own comment said not to do. On a
perfectly calibrated lattice null that inflates the false-failure rate to 6.4% at
1,000 simulations against a nominal 5%. The first attempt to fix it, passing the
lattice CDF to the same test, made it **worse** (7.1%), because the test computes
its p-value from the null distribution of the statistic for a continuous
reference no matter which CDF it is given. The p-value is now obtained by
simulating the exact lattice null, which assumes nothing: measured false-failure
rate 4.8% at 200 simulations. And the randomization p-value formula was wrong
too (below).

Neither accounted for C1. Correcting the formula moved it from 0.0900 to 0.0875;
correcting the uniformity test left it at **p = 0.066**, still the weakest of
the three by a wide margin and still passing only because 0.05 is the threshold.
A perfect null on this lattice has a median statistic of 0.028 at 1,000
simulations against C1's 0.0924.

The fix was to shift **within each block** rather than across both: one shift per
block, wrapping inside it. The ten-five split then holds on every draw,
clustering inside each block survives, and the seam disappears entirely. There
are 520 × 121 = 62,920 distinct placebo designs available that way, against the
2,000 draws the design calls for. This is a further departure from the
pre-registered null and is disclosed as one — but the alternative is a null that
is not a null of this design.

**And the check that enforces that could be cleared by a run measuring nothing.**
It read the `draw_scheme` field and stopped there, so any run reaching the write
step satisfied it. One such file was on disk: a 2-sim diagnostic for C1 recording
`draw_scheme=circular` beside its own `VERDICT=UNDETERMINED`. It would have
flipped the gate on the confirmatory path from BLOCKED to PASS — C1 "certified"
from an artifact whose verdict is that it certifies nothing. A check must gate on
the field that carries the finding, not the one that labels the run, so the
verdict and the completed-sim count are now read first and `draw_scheme` is only
consulted once they hold.

The same run did real damage on the way. The rule that a smaller run must not
overwrite a larger one was applied to the verdict file and to nothing beside it:
the p-value list was published unconditionally and carried **no stratum in its
name**, while the size comparison was made against the *per-stratum* verdict. A
2-sim C1 run therefore passed the test — no C1 verdict existed, so the bar was
zero — and overwrote discovery's 200-sim p-value list, 5,450 bytes down to 61.
The protection written after the 8-sim incident re-created the 8-sim incident,
one file to the left. Every file a calibration run writes now carries its
stratum, sidecars included.

**And for all of that, nothing made the estimator look.** `17_stacked_event_study.py`
— the ratified primary estimator, the one that computes the randomization
p-values — read no calibration artifact at all. Gate C ratified the ordering
"calibrate, then report", and the gate lived only inside the regression suite, so
the estimator itself would run and print regardless of what any verdict said.

It stayed invisible because discovery *is* calibrated, so every number it would
have produced was sound. That is the failure mode rather than a defence of it: a
guarantee nothing enforces is one that holds until the day it doesn't, and this
project has closed the identical "documented and wired into nothing" pattern
three times already — for PPML, for the B-HEARD control, and for the dose-response
arm.

The confirmatory script did gate, and gated on the wrong thing: it read
`null_calibration.csv`, which is *discovery's*, while writing p-values for C1 and
C2. A calibration certifies one geometry and one draw scheme, and those strata
share neither — so the gate answered a question about a sample that script never
estimates, and C1, whose scheme is new and whose uniformity is marginal, is
exactly the stratum it could never have protected. Both now call one
stratum-aware `require_calibrated()`, and each run prints which null its p-values
rest on.

One more thing fell out of testing that gate. Running the estimator with two
draws to prove it refuses an uncalibrated null **overwrote the full result**,
reporting a randomization p of 1.000 from two draws. The no-downgrade rule
written after the 8-simulation incident had been applied to the calibration
script and to nothing else. It now applies here too, and a small run leaves its
own sidecar instead of the main artifact.

**This section was wrong until 2026-09-12, and the reason is worth keeping.** It
quoted a rejection rate of 0.065 and an AR(1) rho of 0.185, and closed with an
open item saying the day shock was "assumed rather than estimated". Finding S8
established that those numbers described a null more dependent than this design
actually has: rho was estimated from the outcome's *level* series, which already
contains the district, day-of-week and day-shock components the synthetic panel
then added back on top — so the AR(1) was nearly four times too persistent and the
variance 1.40× too wide. Each component is now estimated after the previous one is
removed, and the implied total SD is 0.0429 against the panel's 0.0428.

The error ran in the **conservative** direction: a more dependent null is a harder
test, so the CALIBRATED verdict survived it. That is exactly why it lasted. A
defect whose sign happens to be safe is the kind nobody goes looking for, and it
was found by reviewing a *power* design rather than the calibration itself. The
numbers above are now in the claims register, so a future drift fails a check
instead of sitting in prose.

### 7.5b Power — the design cannot deliver a confirmation

**This is the result that decides what the paper is.** `scripts/19_power.py`
computes a minimum detectable effect per stratum by simulation, at 200 null sims
and 200 scan sims, with no gate breaches. Against the minimum effect of interest
of **−0.005**:

| stratum | MDE, worst profile | MDE, best profile | MDE ÷ MEI | verdict |
|---|---|---|---|---|
| discovery | 0.00950 | 0.00291 | 1.901 | UNDERPOWERED |
| C1 | 0.01235 | 0.00382 | 2.471 | UNDERPOWERED |
| C2 | 0.00875 | 0.00290 | 1.750 | UNDERPOWERED |

**Every stratum is underpowered**, including the one the whole discovery /
confirmation split exists to obtain. C1 is the worst of the three at nearly two
and a half times the effect the paper has said it would care about — which is
what fifteen episodes buys.

Under the randomization-inference procedure that is actually the ratified primary
inference, discovery's MDE is **0.01023** — roughly twice the MEI, and close to
the −0.010 effect that was planted to verify the estimator recovers anything at
all. The design can see the effect it was built to prove it could see, and not
much smaller.

**The verdict is shape-dependent, and that is worth more than the headline.** Two
effect profiles were simulated. A *sustained level shift* of half a percentage
point is invisible everywhere: MDE 0.0095 to 0.0124. A *dip-and-rebound* of the
same size is detectable everywhere: MDE 0.0029 to 0.0038, comfortably below the
MEI. So this design is not uniformly blind — it is blind to exactly the shape
that a persistent change in help-seeking would take, and sensitive to a transient
one. The go/no-go is taken on the worst profile, which is the conservative and
correct choice, but a reader should know the design has a shape it can see.

**What follows, and it was pre-committed.** `EXECUTION_PLAN.md` Phase H and
`REBUILD_PLAN.md:495` both say in advance that an underpowered verdict is a
legitimate conclusion rather than a failed run. So: **the confirmatory design
cannot deliver a confirmation**, and the paper becomes a measurement-and-design
contribution with a precisely bounded null. §8's discovery null stops being a
null of unknown resolution and becomes a bounded one — we did not detect an
effect, and we can now say how large an effect would have had to be before we
could have.

That is a real ending. It was written into the plan before the number existed,
which is the only reason it can be stated without it looking like a
rationalisation after the fact.

**What it does not license.** It does not say there is no effect. It says this
design, on this sample, with these episode counts, could not have found one of
the size the paper cares about unless it took a particular shape. A larger
episode set, a longer panel, or a sharper treatment measure would each move the
MDE, and none of them is available here.

### 7.5 The verification apparatus — and its own failure mode

`scripts/23_regression_suite.py` turns every audit finding into an executable
check — **80 checks** at present. States are PASS / FAIL / **BLOCKED** / ERROR,
where BLOCKED means "could not evaluate" and is deliberately *not* a pass.

They all pass as of the basket rebuild completing on 2026-09-12 — no FAIL, no
BLOCKED, no ERROR — and the live state is always in
`outputs/tables/regression_suite.csv` rather than in this sentence. When they do
not all pass, this document says which and why instead of rounding up: the
version of this paragraph written a few hours earlier named six failures and two
blocked checks, all of them the same unfinished rebuild.

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

**The findings register now says whether each finding is actually closed.** It
did not before, and the gap was subtle: every entry has a `fix` column, but that
column is written when the finding is *filed*. It describes what should be done,
not what was. A register full of prescriptions reads like a register full of
completions, and whether anything had actually been fixed was recoverable only by
reading the check suite and matching tags by eye.

Each of the 102 findings now carries a status — `fixed`, `open`, or `unverified` —
and the check that guards it asserts one direction only: **nothing may say
`fixed` while a check tagged to it is not passing.** `unverified` means nothing
checks it, which is a statement of work remaining and not a synonym for fine.
Current state: **99 fixed, 0 open, 3 unverified** — the three (P1, P5, RI3) are held until C1's certificate under the within-block scheme exists, because a BLOCKED check is not evidence.

Writing that check taught two things worth keeping, both of which are the same
defect it exists to prevent, committed inside it:

- **Absent is not failing.** The first version treated a check missing from the
  last run's results as non-passing, so *adding* any new check instantly made its
  finding look unfixed.
- **A two-way comparison oscillates, and a witness cannot corroborate their own
  testimony.** Deriving the column and then testing the file against the
  derivation means the stored value is always one run behind: it fails, and
  fixing it makes the next run fail the other way. And this check is itself
  tagged to a finding, so its own failure would have made that finding look open,
  which would have kept it failing. It excludes itself from its own evidence.

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

Six checks hold the registers in place — `V.sources_verified` (which **BLOCKS, never
passes, when no scan has run**), `V.no_duplicate_source_ids`,
`V.source_id_per_artifact`, `V.claims_reproduce`, `V.claims_cover_exhibits`,
`V.links_resolve` — and each was defeated on purpose
before being accepted: a claim edited to a wrong value fails; truncating the
underlying data fails; a deliberately dead URL fails; a returning id collision
fails; a second script appending to the register fails; an artifact touched
after its scan fails; an unregistered number added to a table fails **while the
same number in prose does not**; and deleting the log **blocks** rather than
passing.

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
- **The rule that every number carries a claim was enforced by nothing.** It is
  stated in three documents, and until now `V.claims_reproduce` was the whole of
  its enforcement — a check that takes the register as its *input* and verifies
  each entry against its artifact. It can only ever report on numbers somebody
  already chose to register; a number added to the paper with no entry is
  invisible to it. Coverage validated, content not, which is the same inversion
  that let half the basket enter through a topic category while every check
  reported it complete. The commit that most recently restated the rule is the
  one that broke it: six numbers entered §4.1 with the broad arm and nothing
  failed. `V.claims_cover_exhibits` now requires every **markdown table row**
  carrying a numeric cell to be matched by a claim, through the same matcher the
  verifier and the claims updater use, so the three cannot disagree about what
  "the claim is in the document" means. Tables only, on purpose — asserting it
  over 1,200 lines of prose would fire on dates, section numbers and counts
  stated in passing, and a check that cries wolf is one people stop reading,
  which is how the defect it guards survived in the first place. On its first
  run it found two uncovered rows, one of them in the calibration table added by
  the very commit that restated the rule.
- **The register could lose an artifact silently, and did.** The rule was "one
  row per source id, describing the file on disk right now" — which says nothing
  about whether an id still describes the same file it did last week. The broad
  basket arm writes its own components series and its own episode list, correctly
  suffixed; its *provenance* was not suffixed, so `log_source` read the broad
  files as new versions of the strict ones and superseded them. After that run,
  `data_sources.csv` described the broad artifacts under D1 and S11, and the
  **strict arm — the primary one, the one this paper reports — had no provenance
  row at all**. Nothing failed: `V.artifacts_current` checks the generating
  script behind every row that exists and cannot ask about a row that stopped
  existing. An id now belongs to an artifact (`config.basket_source_id`), and
  `V.source_id_per_artifact` fails if any id has ever named two files.
- **The history that would have caught it could not be read.** Superseded rows go
  to an append-only `data_sources_history.csv`, which is what makes "when did
  this hash change, and to what" answerable. It was written with
  `header=not exists()`, so its header froze at the seven columns the register
  had on the first supersede while later rows carried nine — a file that raises
  `ParserError` on line 22 for any reader. Nothing in the repository read it,
  which is exactly why the defect survived the whole rebuild. Repaired in place:
  **41 historical rows across 11 ids now parse**, and the new check reads them.
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

**These are discovery-period results, 2017–2020, and they are exploratory.** The
confirmation sample has entered no model and no test of H1; the accesses that
have touched it are disclosed in §5.3 and §5.1d. Nothing below tests H1 in the sense
the design reserves that word for; it describes what the explorable half of the
data looks like once the pipeline is repaired. The randomization p-values use
**500 draws**, not the 2,000 pre-specified for the confirmatory run.

### 8.1 The mental-health share does not move

Twenty-nine discovery episodes, stacked, with day −1 as the reference and the
joint test taken over days 0–7.

| outcome | arm | first-week coefficient | randomization p |
|---|---|---|---|
| EDP share | OLS on shares | −0.00123 | 0.695 |
| EDP count | PPML with offset | −0.01084 | 0.519 |
| Narrow MH share | OLS on shares | −0.00103 | 0.880 |
| Narrow MH count | PPML with offset | −0.00615 | 0.826 |

Both arms point the same way — down — and neither comes close to conventional
significance. **That the two arms agree is worth stating**, because this project
has been caught by the opposite: the 2020 "signature" that looked like a shift
in composition existed only in the denominator and reversed when counts were
modelled. Here it does not reverse. The estimates are stable across the 14-, 28-
and 60-day post windows as well, moving in the fourth decimal.

**Read against the minimum effect of interest, −0.005**, the EDP share estimate
is about a quarter of it and the narrow-MH estimate about a fifth. So the data
are consistent with no effect, and equally consistent with an effect several
times smaller than the one the paper has declared it would care about.

**What this does not establish.** It does not show there is no effect. §7.5b
measures how large an effect would have had to be before this design could have
found it: under a sustained level shift the discovery sample is underpowered
against −0.005 by a factor of about 1.9, while a transient dip-and-rebound of
that size would have been detectable. So this is a *bounded* null — evidence of
nothing detected, with the bound stated — and limitation 12 says so in the
terms a referee will use.

### 8.2 The placebos are quiet, and one channel is not

The decomposition runs 65 outcome-by-window tests. Under a Bonferroni threshold
across all of them — α = 0.000769 — exactly **three** survive, and all three are
the same thing:

| outcome | window | coefficient | p |
|---|---|---|---|
| injury share | days 0–2 | +0.00144 | 0.00019 |
| injury share | days 12–14 | +0.00110 | 0.00071 |
| log injury count | days 0–2 | +0.00962 | 0.00050 |

Nothing in the mental-health family survives — its smallest p anywhere is 0.066,
which across thirty tests is what noise looks like. Neither placebo survives:
cardiac share and asthma share reach 0.222 and 0.097 at their strongest, which is
the behaviour a placebo is included to demonstrate and the reason the injury
result can be read as something rather than as one more draw from a wide net.

**The plain reading is a street-activity channel, not a help-seeking one.**
Injury calls rise in the first three days after attention rises, in both share
and count, while every mental-health measure stays flat. That is what a protest
mechanism looks like and it is not what this paper set out to measure.

**The alternatives it does not rule out** are real and should be stated before
anyone gets attached to the story. The days 12–14 coefficient is nearly as large
as the days 0–2 one, which no simple protest account predicts and which is more
consistent with episode windows overlapping something seasonal. "Injury" is a
dispatch call type, not an adjudicated cause, so a change in how incidents are
coded during a period of heightened activity would produce the same number. And
the decomposition is estimated on shares within a total that is itself moving:
`log1p_injury` rising tells us the count rose, but a compositional finding that
lives only in the denominator is exactly the error this project already made
once.

### 8.3 What the figures show

`08_figures.py` produced output for the first time in this project's history —
until 2026-09-12 its first figure raised `KeyError` on a column name and no check
ran it, so it had never generated anything. Four figures now exist: the raw
series with episodes marked, the primary impulse response, the window
decomposition, and the outcome decomposition with placebos blocked visually.

The event-study path for both primary outcomes sits close to zero throughout,
with no pre-trend and no post-episode step: the largest first-week daily
coefficient is −0.0024 for narrow MH on day 0, against a series whose
district-day standard deviation is 0.047.

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
4. **Google Trends is a sample, not a census.** This limitation used to add "and
   its precision degrades over the decade", which measurement does not support:
   on `trends_us`, the only Trends series in the index, the quantization step
   relative to the series' own scale is *finer* late than early (ratio 0.82) with
   365 non-zero days in every year (§5.1c). The degradation is real in
   `trends_nyc`, which is retired. The sampling limitation stands; the decay does
   not.
4b. **A null in 2021–2024 is nonetheless harder to read than one in 2017–2020**,
   for a different reason than was assumed: Wikipedia's `agent=user` filter
   changed meaning in April 2020 and was not applied retroactively, and the size
   of that break grows every year afterwards — 0.0009 SD across the discovery
   window against 0.0856 SD across 2021–2024 (§5.1a). The conclusion survives;
   the mechanism behind it was wrong.
5. **B-HEARD contaminates the 2021–2024 arm** in the same direction as H1, on
   adoption dates that are 17-of-31 low-confidence.
6. **The EDPC recode (mid-2018)** sits inside the discovery window.
7. **The episode construct changed** after the original freeze, while blind to
   outcomes (§4.2) — disclosed, dated, with original wording preserved.
8. **Two freeze incidents** (§5.3), one of which carried a specification decision.
9. **We do not use armed/unarmed status**, which is our protection against the Nix
   & Lozada critique of MPV coding — stated explicitly because a reader who knows
   that literature will ask.
10. **The one channel that moves is a dispatch code, not an adjudicated cause.**
   Injury calls rise in days 0–2 after attention episodes (§8.2), and "injury" is
   what a dispatcher entered under time pressure. A change in *coding* during
   periods of heightened street activity would produce the identical number, and
   nothing in this design separates the two.
11. **The injury result's timing does not fit the story it suggests.** The days
   12–14 coefficient is nearly as large as days 0–2. A protest-activity account
   predicts a sharp, short-lived rise; two separated bumps are at least as
   consistent with episode windows coinciding with something seasonal. This is
   stated before anyone becomes attached to the mechanism, not after.
12. **The discovery null is bounded, not empty — and the bound is wide.** §8
   reports no detectable movement in the mental-health share, and §7.5b now says
   how large an effect would have had to be before this design could have found
   it: **1.9 times the minimum effect of interest on discovery, 2.5 on C1**, under
   a sustained level shift. "We did not detect it" therefore means "we could not
   have detected it unless it were roughly twice the size we said would matter, or
   unless it took a transient shape". That is a real statement and a weak one, and
   the paper should present it as both.
13. **The confirmation window has recording breaks inside it, mapped under a
   declared read.** Twenty outcome-group codes are born or retired inside the
   confirmation analysis windows and the missing-district share drops by two
   thirds at 2016-01-01 (§5.1d). They were found by reading confirmation-period
   *coverage* — dates and a missingness rate, no outcome value — through a
   logged, scope-checked exemption disclosed before it ran. That is still a read
   of the sealed sample, and it is listed beside F1 and F2 in the addendum's
   summary table rather than presented as blind. The breaks themselves are
   handled by pre-specified sensitivities, never by changing the primary.

---

## 10. Open decisions, with owners

| Decision | Owner | Status |
|---|---|---|
| Materiality of the freeze incidents (§5.3) | Justin | open |
| Sign-off on the rebuilt episode list (70 → 74 strict; 75 in the broad arm) | Justin | open |
| Jordan Neely: pre-specified in `CONFIRMATION_PLAN.md:23-25` but killed by a civilian, not police | Justin + Abrahim | open |
| Registered Report vs conventional submission | Justin | open |
| H2 (NYC Well) and H3 — in, out, or amended | Justin | open |
| `trends_nyc`: retire from CAI-D; `wiki_nyc` rejected as its replacement; index is national | **decided** 2026-09-11 | done |
| Episode construct: regime → shock | **decided** 2026-09-10 | done |
| Bridge exhibit → simulation instead | **decided** 2026-09-09 | done (`25_zscore_simulation.py`) |
| After Phase H: run Phase I as pre-registered, with the reading of a non-rejection fixed in advance (addendum §19) | **decided** 2026-09-13 by Abrahim; Justin to confirm | decided |
| O2 coverage diagnostic as a declared, scoped, logged access (addendum §18) | **decided** 2026-09-13 by Abrahim | done |

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
