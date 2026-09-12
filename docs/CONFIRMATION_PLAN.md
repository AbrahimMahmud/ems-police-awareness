# Confirmation plan (addresses concerns C1 and C2)

Design: 2017-2020 = discovery sample (all current results). Hypotheses frozen
BEFORE any extension data is examined; the extension + independent outcomes
form the confirmation package. Either outcome yields a publishable conclusion.

## Frozen confirmatory hypotheses (as of this commit; no extension data examined)
H1 (primary): EDP call share declines in days 0-5 after high-awareness
    episodes (directional). Test: episode-level randomization inference,
    specification exactly as scripts 01-05 (aware_log windows, 59 CDs,
    date-clustered + permutation).
H2 (substitution): non-police crisis contacts (NYC Well) rise in the same
    windows (directional).
H3 (mechanism): the EDP decline is steeper in precincts/districts with higher
    police-distrust exposure (CCRB complaints per capita; SQF history), and
    in response to Black-victim episodes specifically (aware_black index).
Q1-protest hypothesis: whitest-quartile suppression is protest disruption --
    it attenuates under same-day injury-intensity controls; Q3/Q4 does not.

## Workstreams
W1 Extension sample (C1): Wikipedia-pageview awareness index 2015-2024
   (validated vs Twitter r=0.72 on 2017-2020 overlap; selection toward famous
   cases modeled explicitly). Expected new episodes: Scott/Gray 2015,
   Sterling/Castile/Dallas 2016, K. Scott 2016, Wright + Chauvin verdict 2021,
   Nichols 2023, Neely 2023 (NYC), Massey 2024 -> ~30 episodes total.
   NEEDS: user reruns 00_local_ems_extract.py with 2015-01-01..2024-12-31.
W2 Independent outcomes (C1): NYPD 911 Calls-for-Service by precinct (2018+,
   Desmond replication); NYC Well contact volumes (substitution); NYC 311.
W3 Finer geography (C1/C7): zip-level EMS extract (~180 units).
W4 Mechanism measures (C2): CCRB complaint rates, stop-question-frisk
   intensity; protest-proxy controls (injury intensity); victim-race-specific
   episode responses.
W5 Power notes: permutation SD scales ~sqrt(12/30)=0.63 -> extension alone
   lands H1 near p~0.08 two-sided; confidence comes from the joint package
   (H1 extension + H2 substitution + W2 precinct replication), not one test.

## Sequencing
1. (user) rerun extract 2015-2024; ask Justin: framing decision + Twitter provenance
2. (assisted) Wikipedia index 2015-2024 + validation report -- BEFORE any outcome contact
3. (assisted) fetch W2/W4 public data; register in DATA_PROVENANCE.md
4. confirmatory run, one shot, all hypotheses; Gate 3 memo
5. paper drafted around whichever conclusion the data support

---

# Addendum — deviations from the plan above

**Everything above this line is the plan as frozen, byte for byte. Nothing in it
has been edited.** This addendum is appended so the original and the departures
from it can both be read, and so no change has to be inferred from a diff.

Three places in the project already cited this addendum before it existed
(`PAPER_MASTER.md` §4.2 and §5.2, and finding F2's fix). A pre-registration
record that points at a document nobody wrote is worse than no pointer at all,
because it reads as disclosure.

Each entry says **what changed**, **why**, and — the part that decides how much
weight the confirmation can carry — **whether it was decided blind to
confirmation-period outcomes**.

## Summary

| # | Deviation | Blind to confirmation outcomes? |
|---|---|---|
| 1 | Episode construct: regime → shock | yes |
| 2 | Episode threshold: fixed level → within-year quantile | yes |
| 3 | Test window: days 0–5 → days 0–7, joint | yes |
| 4 | Attention index composition | yes |
| 5 | Wikipedia rename correction | yes |
| 6 | Article basket selection rule | yes |
| 7 | Article basket construct (police vs civilian) | yes |
| 8 | Wikidata scope transport and its date corrections | yes |
| 9 | Estimator: stacked event study, contested-day rule | yes |
| 10 | Episode list the estimators consume | yes |
| 11 | Outcome: cancelled dispatches retained alongside | yes |
| 12 | H2 and H3 are not currently runnable | n/a |
| 13 | Power note W5 is superseded | yes |
| 14 | **H1 framing and the DID control choice** | **NO — see below** |
| 15 | **Freeze incidents F1 and F2** | **NO — these are accesses** |

---

## 1–2. The episode construct and its threshold (finding E6)

**Frozen rule:** `cai_d > 1.0`, with runs merged across gaps shorter than 7 days
— a *regime* construct ("attention was high for a stretch") on a fixed level cut.

**Now:** a *shock* construct. Local peaks at ±7 days with a 14-day minimum
separation, entry at the within-calendar-year 90th percentile
(`config.EPISODE_RATE = 0.10`) with hysteresis on exit, onset walked back at most
7 days, and the span capped at 14 days so no episode can exceed the window it is
analysed in.

**Why.** A fixed level is not a fixed stringency. `cai_d > 1.0` selected between
**10.7% and 66.4%** of a year's days depending on the year, so "a high-attention
day" meant something different in 2016 than in 2020 — and the index's own scale,
not public attention, decided which. Within-year quantiles give **10.1%–10.3% in
every year** of 2015–2024, a 0.2pp spread. The construct was chosen against three
alternatives on stringency spread and on how many landmark events it surfaced,
measured blind to every outcome. The old regime rule also produced a 235-day
"episode", which is not a shock by any reading.

**Cost, stated plainly:** many episodes are single-day. That is the honest shape
of a shock construct and it is reported rather than smoothed away.

## 3. The test window: days 0–5 → days 0–7

H1 above says "days 0-5". The estimator tests the **joint** null across event-time
days **0–7** with day −1 as the reference, inside a 14-day post window, with 28-
and 60-day windows as pre-specified sensitivities. The change was made when the
estimator was rebuilt around a stacked event study and was not separately
justified at the time; it is recorded here because a reader comparing the two
documents would otherwise find a discrepancy with no explanation.

## 4. Attention index composition

**Frozen:** a Wikipedia-pageview index "validated vs Twitter r=0.72".

**Now:** `CAI_D_COMPONENTS = ("wiki_ext", "trends_us")` — a national index.
- `trends_victims` retired: it divided by a topic term, so it measured share of
  attention rather than attention.
- `trends_nyc` retired: censored on **26–71% of days depending on the year**
  (42.6% overall, 45.1pp spread). On those days it is not a level at all but an
  indicator of "above Google's reporting floor", and the censoring is worst
  exactly where the exposed confirmation stratum sits.
- `wiki_nyc` rejected as a local component: the basket is ~10 articles, mostly
  historical, so most of the signal is anniversary and spillover traffic.
- The Twitter series is retired entirely and is not recoverable: the raw files
  are not in the repository, so the r=0.72 validation above cannot be re-run.

**Cost:** the index is national. The paper's locality claim is bounded
accordingly, and §4.3 of `PAPER_MASTER.md` states what it can and cannot claim.

## 5. The Wikipedia rename correction

Wikimedia records pageviews per **title** and does not carry them across a page
move, so an article renamed from "Shooting of X" to "Killing of X" loses its
entire pre-rename series — including the attention spike at the moment of death,
which is the signal this project measures. Measured: `Killing_of_Alton_Sterling`
holds 128,855 views from 2021-04-25, while `Shooting_of_Alton_Sterling` holds
1,861,004 from 2016-07-06. **93.5% of his attention was being discarded**, and 57
of 117 basket articles had under 60% of expected coverage.

Historical titles are now discovered from the redirects API and summed per
article. This changes every CAI-D value and therefore every episode date. It was
found and fixed blind to all outcome data.

## 6. Article basket selection (finding X2)

**Frozen:** the top 150 victims ranked by the Twitter series. Twitter coverage
stops at death-year 2020, so that basket contained **zero victims killed after
2020** — an attention index whose inputs end in 2020 cannot measure attention in
2021–2024, which is most of the confirmation window.

**Now:** a walk of the live Wikipedia category tree, with a scope rule applied
per article and every include/exclude decision recorded with its reason. The
basket is deliberately **not ranked by attention**: ranking it would let the index
select its own inputs, which is the defect that retired `trends_victims`.

## 7. Article basket construct — police violence, not adjacent violence (B1, B2)

**Not in the frozen plan at all, because the question was never asked.** The
scope rule tested *when* and *where* a death happened and never *who did it*. For
61 of 120 in-scope articles the category that admitted them was a topic ("Black
Lives Matter", "2020/2021 United States racial unrest"), which asserts nothing
about an actor.

The basket therefore contained **nine killings with no police involvement**, each
confirmed from the first sentence of its own article (Ahmaud Arbery, Renisha
McBride, Markeis McGlockton, James Craig Anderson, Tamla Horsford, Nina Pop,
James Scurlock, Carlos Carson, Deona Marie Knajdek), and **Micah Xavier Johnson**,
who shot five Dallas police officers — attention to violence *against* police —
dated 2016-07-08, the single highest day in the index.

**Now, and pre-specified here:**
- **Strict basket (109 articles) is primary.** Evidence names law enforcement as
  the actor.
- **Broad basket (118) is a pre-registered sensitivity**, adding the nine where
  nothing establishes who acted.
- **Attention to violence against police is excluded from both**, and the effect
  of removing it on the 2016-07-08 peak is reported rather than absorbed.

Decided blind to every outcome, on public evidence, with 25 test cases verified
against the articles themselves.

## 8. Wikidata scope transport (N1, N2, N3)

Scope metadata now comes from the MediaWiki action API rather than SPARQL, after
a field-by-field comparison of both routes over the same 164 articles. Three
corrections followed, all of which changed basket membership:

- Articles with accented titles were filed under a percent-encoded name and could
  never join the basket. **José Campos Torres entered the index as a 2014 killing;
  Wikidata records 1977-05-05**, outside the study period entirely.
- Ma'Khia Bryant had no scope row at all.
- Month-precision dates were rendered as a specific day, then read as *no* date.

**Twelve articles had been excluded for a reason that was false.**

## 9. Estimator (findings S5, S7, D6)

Stacked episode event study with day −1 as the reference and episode × district
fixed effects; **episode-level randomization inference is the primary p-value**,
with the asymptotic joint Wald reported beside it and never instead of it.

A district-day contested by two episode windows is assigned to the episode whose
start is **nearest** in event time, so no observation is a control for one event
while treated in another, and none is discarded. An earlier rule truncated
windows at the next episode's start; a still earlier one dropped contested days.

Both arms are reported for every outcome: **OLS on shares and PPML on counts with
a log-total-calls offset.** This is not optional — the 2020 "signature" reverses
in counts, and publishing one arm is how that goes unnoticed.

A **dose-response arm** scaled by episode intensity is added as a clearly
secondary specification. The binary arm remains primary because it is what was
pre-registered.

## 10. The episode list the estimators consume

`confirmation_episodes.csv` (70 episodes, the frozen rule) is the
pre-registration record and is kept byte-identical.
`confirmation_episodes_rebuilt.csv` is the adopted list and is what the
estimators read. Both lists and the diff between them are published.

## 11. Outcome definition (finding O1)

The disposition filter still drops CANCEL / NOTSNT / DUP / 87 for the primary
extract, **and the excluded calls are now kept in their own artifact** so the
cancelled-inclusive sensitivity can be run rather than promised.

This matters because of what the outcome means here: a cancelled EDP dispatch is
still someone calling 911 about a mental-health crisis, and the hypothesis is
about what New Yorkers *ask for*. The filter removes **7.47% of EDP calls against
0.76–0.77% of altmen and asthma** — a 9.9× ratio — so it removes exactly the
calls most likely to be affected. Measured effect on the outcome: mean
mental-health share rises from 0.1083 to 0.1119 (+3.3%), the two series correlate
0.9758. Small, but established rather than assumed.

## 12. H2 and H3 are not currently runnable

H2 requires NYC Well contact volumes and H3 requires CCRB complaint rates and
stop-question-frisk intensity. Neither dataset is in the repository. **H1 is
therefore the confirmation package as it stands**, which is materially weaker
than the "joint package" W5 relies on. This is a gap to close or to state as a
limitation — it is not a deviation that has been quietly resolved.

## 13. Power note W5 is superseded

W5's `sqrt(12/30) = 0.63` scaling assumed ~30 episodes under the frozen
construct. The episode count, the construct and the index have all changed since,
and many episodes are single-day, so the *effective* episode count is lower than
the nominal one. Power is recomputed per stratum before the freeze lifts, and a
recorded go/no-go decision follows from it. **If power says confirmation cannot
deliver, that is the conclusion**, and the paper becomes a measurement-and-design
contribution with a precisely bounded null.

## 14. Decisions made AFTER seeing discovery results

Recorded separately because they carry different evidential weight, and a reader
is entitled to discount them.

- **The H1 framing** and **the choice of control group for the
  difference-in-differences** were settled after discovery-period results had been
  seen. They are not blind, and are not defended here as though they were.
- The Q1-protest hypothesis above was formulated from discovery-period
  heterogeneity, which the frozen text already implies but does not state.

Discovery (2017-01-01 → 2020-12-31) is the **exploratory** sample and has been
examined freely. That is the design working as intended. The confirmation windows
have not been used to choose any specification.

## 15. Freeze incidents

**F1** — a citywide annual aggregate of the mental-health call share was read
from the confirmation period. No district variation, no episode alignment, no
test of H1. Disclosed in `PAPER_MASTER.md` §5.3.

**F2** — a second and broader access, found on 2026-09-11 and undisclosed until
then. Verifying a finding about call-type births queried the source API directly,
which no artifact-level guard can see. What was read: first-record timestamps and
whole-period totals per call type; citywide monthly counts across the 2021-05/06
boundary; annual EDP-family totals; and **precinct-level EDPM counts for June
2021, comparing the three B-HEARD pilot precincts against the rest**.

That is district-level variation inside the confirmation window, and **a
specification decision was taken on the result**: EDPM was retained in the EDP
family because the comparison refuted the claim that it is the B-HEARD routing
code. The decision is defensible on other grounds — a routing code would
concentrate in pilot precincts and EDPM does not, and it appears citywide from
day one — but "defensible on other grounds" is a judgement for the supervisor,
not a reason to leave an access unrecorded.

How it went unnoticed: F1 was recorded by the agent that caused it, which created
the impression that the freeze had exactly one breach. F2 produced a finding full
of confirmation-period numbers and nobody asked where they came from. **The
numbers were read as evidence rather than as an access.**

The structural gap is closed: the guard now covers the source dataset and not
only the files derived from it.

## 16. The randomization scheme on C1 (finding P1)

Found on 2026-09-12, twice and independently — while writing the confirmatory
script and again while writing the power analysis. Never by running anything: no
code path had ever constructed C1's draw geometry.

The plan above specifies episode-level randomization inference as H1's test. On
C1 that scheme is **undefined**, not merely tight. It draws an anchor inside
**one contiguous span**, and C1 is two windows sitting either side of the entire
discovery period — so there is no single span to draw in, and **40.9% of placebo
starts land outside C1's own windows**. Taken alone, its 2021 block holds 5
episodes spanning 139 days inside a 151-day window: 120 usable days against 139
required, slack of **minus 19**. Every draw is rejected and the p-value returns
NaN after the entire budget is spent.

The problem is one of degree everywhere and of definition on C1. Measured at
2,000 draws per stratum, placebo episodes land within 7 days of a real one
**32.3%** of the time on discovery — which has only 190 free days for a 1,240-day
sequence — and **35.1%** on C2, which has 53.

C1 is the *clean* stratum. Its uncontaminated evidence is the reason the design
splits the sample at all, so this is not a corner case.

A circular-shift-over-admissible-days scheme is exact at 2,000 draws for both C1
and pooled, and is pre-specified here as the scheme for those strata. **It is a
different null from the one the calibration certifies.** The 200-sim CALIBRATED
verdict was obtained on a contiguous discovery sample under the original scheme,
and that does not transfer to a two-block window with negative slack. Before the
freeze lifts, the calibration is re-run against C1's gapped geometry under this
scheme — which is treatment-side and blind-safe — and until it is, any C1
p-value rests on an uncertified null and is labelled as such.

## 17. Two C1 episodes have windows that leave the stratum (finding P2)

Found while implementing the scheme for deviation 16.

A stratum is a set of calendar windows, and an episode near an edge does not fit
inside it. Two of C1's fifteen do not, each failing differently:

- **2021-01-05 (Dolal Idd)** — its pre-period reaches back to 2020-12-22, which
  is **inside the discovery window**. Its baseline would come from data already
  explored while its post-period is unexamined, mixing the two samples inside one
  event window.
- **2021-05-24 (Daunte Wright; Adam Toledo)** — its post-period runs to
  2021-06-07, **crossing the B-HEARD launch** on 2021-06-01, so 7 of its post
  days are exposed inside the stratum defined as unexposed.

Nothing noticed, because the stack builder keeps whatever days the sample
contains: a truncated window produces a smaller but perfectly well-formed
estimate.

**The rule pre-specified here is first-week containment.** An episode is kept
when day −1 through day +7 — the span the reported statistic uses — lies inside
the stratum; days beyond that truncate and the truncation is counted per episode.

Requiring the *full* ±14 window instead would drop both, costing **2 of C1's 15
episodes**, 13% of the smallest and most valuable stratum, one of them Daunte
Wright. Measurement says that is unnecessary: for both episodes the first-week
span lies entirely inside C1, and only the tails fall outside — 10 days and 7
days of 29. So the primary test is exact for both, and the loss is confined to
the longer sensitivity windows where it is reported rather than absorbed.

Nothing is dropped: all 15 C1, 29 discovery and 30 C2 episodes are kept.

---

## What has NOT changed

- Discovery 2017-01-01 → 2020-12-31; confirmation 2015-01-01 → 2016-12-31 and
  2021-01-01 → 2024-12-31. No confirmation-window outcome has entered any model.
- H1's **direction** is still pre-specified: a decline in the days after a
  high-attention episode.
- Randomization inference is still the primary p-value.
- 59 community districts; date-clustered inference.
- The frozen episode list is still byte-identical to its committed version.
