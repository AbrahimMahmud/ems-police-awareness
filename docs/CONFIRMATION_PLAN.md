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
| 15 | **Freeze incidents F1, F2 and F3** | **NO — these are accesses** |
| 16 | Randomization scheme on C1: circular shift within each block | yes |
| 17 | Two C1 episodes' windows leave the stratum: first-week containment rule | yes |
| 18 | **Coverage diagnostic over the 2015–2016 outcome extract (O2)** | **NO — a declared, scoped access; disclosed here before it was run** |
| 19 | Interpretation rules restated against the measured power (Phase H) | yes |
| 20 | Spliced `user + automated` Wikipedia series as a sensitivity arm (L7) | yes |
| 21 | C1 null: circular shift **within each block**, sampled not exact; one implementation | yes |
| 22 | The pooled stratum's null is calibrated on its own three-window geometry | yes |
| 23 | CP2 specification audit: reading rules made mechanical, denominator diagnostic, sealed run fixed to its draw count and committed, EDPT/EDPE in the EDP family, full-span panel | yes |
| 24 | Placebo admissibility follows first-week containment; scheme renamed `circular_within_block_fw7`; C1 and pooled recalibrated | yes |
| 25 | Pre-registered fallback for a stratum whose null fails calibration at 1,000 simulations | yes |

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

*F4, found 2026-09-13 by the CP2 audit: the precinct–district crosswalk (S14) was built from a SODA server-side count of dispatches per precinct × district pooled over 2015–2024 — a geography weight with no call type and no date, but a read of confirmation-period dispatch counts that no exemption declared. See addendum §23.10 and PAPER_MASTER §5.3.*

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

**F3** — a third access, taken on 2026-09-09 and found on 2026-09-13 in the
findings register itself. The refutation of finding O2 computed record-level
statistics from the outcome extract for 2014–2016 — missing-district rates by
year, sub-window and call type; the INJALS code's monthly counts and last
timestamp; INJMAJ's share across the 2015/16 boundary; an estimated step in the
mental-health share — and wrote them into the finding's corrected claim, where
they were read as evidence rather than as an access while this section said
there had been two. No artifact or API guard can see an agent opening a file.
The declared-access mechanism of §18 exists because of this: a read that has to
happen is scoped, disclosed and logged before it happens, and the coverage facts
the paper cites are the ones from that declared read, not from F3.

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

## 18. A declared coverage diagnostic over the 2015–2016 outcome extract (finding O2)

**Disclosed before it is run, and before the code that runs it exists.** Finding
O2 records two structural breaks inside the 2015–2016 confirmation window that
neither the panel builder nor the event study can see: the share of dispatches
with no community district falls sharply at 2016-01-01 (a geocoding regime
change), and the INJALS call code is retired inside the window. Whether the
confirmation sample straddles breaks like these is a question about *coverage*,
and it has to be answered before CP2 can be discharged — a confirmatory estimate
run across a discontinuity nobody knew about is not a confirmatory estimate.

Answering it means reading confirmation-window rows of the outcome extract, which
the freeze protects. "It is only metadata" is exactly the reasoning that produced
incidents F1 and F2, so this is not treated as an assumption. It is a **declared
access**, approved by Abrahim Mahmud on 2026-09-13 as a narrow exception, with its
scope fixed here first and a check that holds it there:

- **What is read.** `data/processed/ems_cd_day_calltype.parquet` — the district
  × day × call-type extract, all years — through a named exemption in
  `freeze_guard` (`declared_access("O2_coverage_breaks", ...)`). The function
  refuses any exemption not declared in `config.FREEZE_EXEMPTIONS`, refuses a
  caller other than the script the declaration names, prints a banner, and
  appends a row to `data/reference/freeze_access_log.csv` every time it runs, so
  each access is on the record whether or not anyone writes it up.
- **What is emitted, and nothing else.** (a) Per `final_call_type`: the first and
  last `incident_date` on which the code appears. (b) Per calendar year: the
  share of dispatched calls whose community district is missing. **No call count
  by period, no outcome mean or share of any call group, no district-level value,
  and nothing crossed with the attention index or the episode list.**
- **Where it goes.** `data/reference/ems_call_code_span.csv` and
  `data/reference/ems_missing_district_rate_by_year.csv`, committed, so the
  access leaves an artifact with exactly the declared columns rather than a line
  in a log. A third file, `ems_coverage_breaks.csv`, holds the two decision
  rules below evaluated on those two files and on the code lists and windows in
  `config`; it is a pure function of them and carries no value that is not
  already in them. It exists so the paper's counts of breaks can be claims over
  an artifact rather than a reading of a log. (Declared after the first run,
  which emitted (a) and (b) only; nothing further was read to produce it.)
- **How the scope is enforced.** `D.declared_access_scoped` requires that every
  exemption in `config.FREEZE_EXEMPTIONS` is used by exactly the script it names
  and by no other, that each declared output exists with exactly the declared
  columns, that this section exists, and that the access log records the run.
  Defeat-tested before it is baselined: add an outcome column to the output and
  the check must fail; call the exemption from another script and it must fail.
- **What is decided from it — pre-specified now, before the values exist.**
  1. A call code whose first or last date falls inside a confirmation *analysis*
     window is a **within-window break** for every outcome group containing it.
     The primary estimates are unchanged. For each affected outcome and stratum,
     a pre-specified **coverage-clean sensitivity** re-estimates with every
     episode dropped whose ±14-day window contains *any* break date belonging to
     a code in that outcome's group(s) or the geocoding step of rule 2 — one
     cell per outcome, arm and stratum, not one per break, so the sensitivity is
     the same size whether a window holds one break or seventeen — and the
     result is reported beside the primary with the codes and dates named. A
     sensitivity that drops no episode is recorded as identical to the primary
     and not re-run. (The EDP-family births already disclosed in
     `config.CALL_TYPE_GROUPS` — EDPC mid-2018, T-EDP 2020-06-05, EDPM
     2021-06-03 — are expected to appear here and are handled the same way.)
  2. If the missing-district share changes by more than a factor of two between
     adjacent years inside a confirmation analysis window, the year boundary is a
     **geocoding break**. The primary estimates are unchanged; a pre-specified
     sensitivity drops every episode whose ±14-day window crosses the boundary
     and is reported beside the primary. It is a *demonstration*, not a
     correction: finding O2's refutation measured the artifact a proportional
     change in geocoding induces in a share at about 0.0002 on the mental-health
     share — far below the first-week statistic's resolution — and concluded
     that neither month-year fixed effects nor dropping episodes is warranted in
     the primary. The sensitivity exists so that a reader can see that rather
     than take it on trust, and it is chosen over month-year fixed effects
     because it changes the sample and not the estimator, so it stays comparable
     with the calibrated null.
  3. Neither rule reads or uses an outcome value, and neither can change which
     estimate is primary.
- **Blind?** No. This is a read of confirmation-period outcome coverage. It is
  listed in the summary table as an access, in the same column as F1 and F2, and
  the difference between it and them is that the scope was written down before
  the read and a check enforces it afterwards.

## 19. Interpretation rules restated against the measured power (Phase H)

**Blind.** Power was computed by simulation on the discovery panel's dependence
structure and the strata's episode geometry (`scripts/19_power.py`); no
confirmation-window outcome was read. The figures are in `PAPER_MASTER.md` §7.5b
and the claims register (C97–C106) and are not restated here, so that they have
one home.

**What Phase H found, in one sentence.** Against the minimum effect of interest
(`config.MINIMUM_EFFECT_OF_INTEREST`, −0.005 of mental-health call share), every
stratum is **underpowered for a sustained level shift** and **adequately powered
for a transient dip-and-rebound** of the same size. The frozen H1 is stated as a
decline over the first week, which is the sustained shape.

**Decision, 2026-09-13.** The confirmatory run proceeds as pre-specified. Power
does not change the test; it changes what a non-rejection is allowed to mean,
and that meaning is fixed now:

1. **The test is unchanged.** Estimator, statistic, draw schemes, strata, arms,
   sensitivities and the multiple-testing family are as pre-specified in
   `PRE_ANALYSIS_NOTE.md` §6–§10 and above. Nothing in this section adds,
   removes or re-weights a test.
2. **A non-rejection is a bounded null, and the bound is the pre-freeze MDE.**
   In any stratum where the primary family does not reject, the result is
   reported as: *no effect detected; a sustained level shift at or above that
   stratum's worst-profile MDE is disfavoured at 80% power; a sustained shift of
   the size the paper declared it cares about is not excluded; a transient
   dip-and-rebound at or above that size is disfavoured.* The MDEs quoted are
   the ones computed before the freeze lifted (`outputs/tables/power_analysis.csv`
   as registered by C97–C106). They are not recomputed afterwards for the
   purpose of interpretation.
3. **The "precise null / underpowered" row of §9.1 is resolved in advance.**
   For the sustained shape the "precise null" reading is unavailable in every
   stratum; for the transient shape it is available in every stratum. No
   post-hoc reclassification from a confidence interval seen after the fact.
4. **A rejection is read by §9.1–§9.4 unchanged.** Power neither strengthens nor
   weakens a rejection; the placebo override (§9.3), the two-arms rule (§9.2)
   and the asymmetric C1/C2 table (§9.4) apply as written.
5. **The paper's framing is fixed whatever the sign.** It is a
   measurement-and-design contribution carrying (a) a confirmatory result on the
   transient shape, (b) a bounded null or a rejection on the sustained shape,
   and (c) the discovery-period findings as exploratory. None of these three
   moves to the headline because of the result.
6. **Sensitivities added since the note** — the coverage-break sensitivities of
   §18 and the spliced Wikipedia series of §20 — are reported beside the primary
   in the `sensitivity` family and never substituted for it (§9.5, §10).
7. **Any power figure computed after the freeze lifts is post hoc** and is
   labelled as such wherever it appears; it does not enter rule 2.

**Why proceed at all, stated so it can be disagreed with.** The alternative was
to stop at the bounded discovery null and never open the sealed sample. The
design is powered for the shape this project's own mechanism work
(`event_study.py`, findings S3/R7) says a help-seeking response would most
plausibly take, the pre-registration is the paper's inferential spine, and a
one-shot test whose reading is fixed in advance cannot be made worse by being
run. What it can be is uninformative about the sustained shape — and rule 2
says so in every stratum where that is the outcome.

## 20. A spliced Wikipedia series for the April 2020 agent-class break (finding L7)

**Blind.** Treatment-side only: it changes how attention is measured and touches
no outcome. Written 2026-09-13 before the freeze lifted.

**The break.** `wiki_ext` is built from pageviews requested with `agent=user`.
Wikimedia added an `automated` class in late April 2020 and did not apply it
retroactively, so `user` means "not obviously a spider" before that date and
"not a spider and not automated" after it. Measured on this basket
(`PAPER_MASTER.md` §5.1a, `data/reference/wiki_agent_class_break.csv`): the
class is exactly zero through 2019 and first appears on 2020-04-29; the shift it
implies in the standardised index is about 0.001 SD across discovery and about
0.09 SD across 2021–2024 — half the confirmation sample and all of C2. It is a
footnote for the discovery result and a live measurement problem for the
confirmatory one.

**The series.** The decade-long comparable series is `user + automated`: before
the break `automated` is identically zero, so the sum equals `user` there and
equals the pre-break definition of `user` afterwards. No splice date is chosen;
the series is the sum on every day. (`all-agents` was proposed and is rejected —
it adds spider traffic, a larger contamination than the one being removed.)

**The arm.** Built by the same pipeline as the broad-basket arm, under the arm
name `spliced`, on the strict basket: `11_fetch_awareness_components.py --arm
spliced` fetches `agent=automated` for every title `wiki_ext` already sums over
and writes `wiki_ext` alone to `cai_components_daily_spliced.csv`;
`12_build_cai.py --arm spliced` builds `cai_daily_spliced.parquet` with every
other component shared with the primary; `13_extension_episodes.py --arm
spliced` writes `confirmation_episodes_rebuilt_spliced.csv`. Every artifact and
provenance id carries the `_spliced` suffix, so the arm cannot overwrite the
primary (the P3 lesson).

**How it is reported.** `30_confirmatory_run.py` runs it as `sens_spliced_wiki`
in the `sensitivity` family, on both H1 outcomes and both arms, in every
stratum, using the spliced episode list — exactly as the broad basket is run.
It is reported beside the primary and never substituted for it (§9.5, §10). If
the spliced episode list is absent at run time the cell is recorded `NOT_RUN`
with the reason rather than skipped.

**What it can show.** In C1 the two series are identical by construction
(automated is zero before 2020), so any difference there is a rounding check.
In C2 a result that moves between the arms is a result that depends on how
Wikimedia classifies traffic, and is reported as such.

## 21. The C1 randomization null is a within-block circular shift, and the confirmatory script draws it from the same code the calibration certifies (findings RI3, P1, P8, P9, P10; CP1 audit)

**Blind.** Treatment-side geometry; no outcome read. The scheme was adopted on
2026-09-12 (`event_study.placebo_starts_circular`) and is disclosed here on
2026-09-13, which is later than it should have been: §16 above and
`PRE_ANALYSIS_NOTE.md` §7 still describe the version it replaced.

**What §16 pre-specified, and why it was replaced.** §16 says C1's placebo
dates are drawn by a circular shift over the stratum's admissible days taken as
one sequence. Measured (finding RI3): C1 really has ten episodes in its 2015–16
block and five in its 2021 block, and a shift through the concatenated
sequence — block 1 being 520 of 641 admissible days — put a mean of 12.1
episodes in block 1, reproducing the real 10/5 split on 12.4% of draws. The
placebo designs were structurally unlike the design under test, which is why
C1's null p-values were non-uniform. **The scheme now in force draws one
uniform shift per window and wraps inside it**, so the number of episodes in
each window is preserved on every draw and clustering inside a window survives.
On a single-window stratum it is arithmetically identical to the anchor-shift
null, so discovery and C2 are untouched. It is named `circular_within_block`,
and `S.ri_scheme_certified` requires C1's certificate to name it.

**Two consequences for what §16 and the note say.**

1. *Sampled, not exact.* §16 and the note say C1's test is exact because the
   685 admissible shifts are fewer than 2,000 draws. Under the within-block
   scheme there are 520 × 121 = 62,920 distinct placebo designs, so the 2,000
   pre-specified draws are a sample of them; `ri_exact` is 0 for every cell.
2. *One implementation.* The sealed script had kept its own copy of the
   seam-crossing shift and would have drawn C1's null with it while gating on
   a certificate for the within-block null — the certificate would have
   described a null the run did not draw. The copy is removed: the script calls
   `event_study.randomization_p` with the stratum's windows, and the scheme is
   chosen by `event_study.draw_scheme_for` from the geometry, exactly as the
   calibration does. The regression suite requires that the script carries no
   randomization arithmetic of its own.

**Also fixed in the script before any run, each disclosed here because the
script is the specification:** episodes are selected by the first-week
containment rule of §17 through the same function the calibration uses
(previously by start-in-stratum, which agreed only by measurement); every cell
seeds its draws from its own identity and banks them in a per-cell ledger
whose sidecar fingerprints the design, so a run interrupted by a container
restart resumes exactly and a ledger from a different panel or episode list is
quarantined rather than pooled; cells may be distributed across processes
without changing any number; the coverage-clean (§18) and spliced (§20)
sensitivities are estimated as `sens_coverage_clean` and `sens_spliced_wiki`
in the `sensitivity` family; and a defect that would have crashed the run
after all estimation and before writing its result (a stale dictionary key)
is corrected. A synthetic dry run proceeds without calibration certificates so
the machinery can be proven on a fresh clone; the real run still refuses.

---

## 22. The pooled stratum's null is calibrated on its own geometry (finding P12)

**Blind.** Treatment-side geometry; no outcome read. Found 2026-09-13 while
preparing the CP2 checklist.

`30_confirmatory_run.py` reports every cell for C1, C2 and **pooled** (C1 + C2,
three calendar windows, 45 episodes). Its calibration gate read C1's and C2's
certificates and let the pooled cells rest on the two of them together. Neither
describes the pooled null: a within-block shift over three windows is a
different placebo geometry from a shift over two or over one, and the note's own
rule — an uncalibrated randomization p-value is not a p-value — applies to a
descriptive stratum as much as to an inferential one. So `18_null_calibration.py
--stratum pooled` now calibrates the three-window geometry under the same scheme
(`circular_within_block`), the confirmatory script gates the pooled cells on
`null_calibration_pooled.csv` alone, and `S.ri_scheme_certified` requires that
certificate to name the scheme the geometry needs.

What does not change: the pooled estimate stays **descriptive** and outside the
primary family (`PRE_ANALYSIS_NOTE.md` §9.4, §10), so the 1,000-simulation
requirement of the pre-freeze gate applies to the three inferential strata
(discovery, C1, C2; `S.lift_requires_1000_sims`) and the pooled certificate is
required to exist and read CALIBRATED at its own minimum of 200.

---

## 23. What the CP2 specification audit found, and what changes before the lift (findings P14, P15, P16, P17, P18, O6, F4)

**Blind.** Written 2026-09-13 from an adversarial audit of the specification
documents and the sealed script; no outcome value was read. Six of eight attack
finders completed (the other two, and every refuter, failed on a session limit),
so each item below was verified by hand against the cited lines before it was
acted on. The interpretation rules of `PRE_ANALYSIS_NOTE.md` §9 are amended
here; where this section and §9 differ, this section governs.

**23.1 "Rejects" is defined.** A family cell rejects when its Benjamini–Hochberg
adjusted randomization p-value (q = 0.05, family of exactly eight; a cell that
produces no p-value counts as p = 1 in the family) is below 0.05. A **stratum
rejects on an outcome** when both arms (share and count) for that outcome
reject with the same sign of the first-week mean coefficient. A **stratum
rejects** when it rejects on at least one of the two primary outcomes. A
stratum whose cells reject in one arm only, or with opposite signs across arms,
is read by 23.3 and does not count as a rejection in §9.4.

**23.2 Direction is the sign of the first-week mean coefficient** (the effect
size §6 already reports), taken over the rejecting cells. A rejection whose two
arms disagree in sign, or whose mean coefficient is within one asymptotic
standard error of zero in either arm, is reported as *a rejection without a
consistent direction* — the joint statistic has detected a shape the mean does
not summarise — and is a new row of §9.4: it is neither confirmation nor
disconfirmation, and is reported with the day-by-day path.

**23.3 The two-arms rule is made mechanical with a denominator diagnostic.**
The count arm's log-total offset is the same denominator the share divides by,
so the two arms cannot by themselves separate a change in demand from a change
in the denominator. The sealed script therefore estimates, per stratum and
outside every family, two diagnostic cells: PPML on the outcome's **raw count
with no offset**, and PPML on **total dispatches**. A share-arm rejection is
reported as *denominator-driven* when the total-dispatch diagnostic has
randomization p ≤ 0.05 and the raw-count diagnostic does not; it is then not
claimed as a change in demand.

**23.4 The placebo override is defined.** A placebo cell (cardiac or asthma
share or count) *rejects* when its unadjusted randomization p ≤ 0.05. The
override of §9.3 applies within a stratum: if any placebo cell in that stratum
rejects, every primary rejection in that stratum is reported as not supporting
H1. Placebo p-values are uncorrected on purpose — a correction would make the
falsification easier to pass.

**23.4a The reading is code.** Rules 23.1–23.4, §19 rule 2 and §25 are
implemented by `34_confirmatory_reading.py`, a pure function of the sealed table
and the pre-freeze power table that writes `data/reference/confirmatory_reading.csv`;
the paper quotes that file, so no judgement is exercised between the seal and the
sentence. `S.confirmatory_reading_rules` feeds the function planted tables, one
per rule and per row of §9.4, and requires the verdict this text fixes for each.
Written 2026-09-13 before the lift.

**23.5 The sealed run takes no draw count.** `--draws` other than the
pre-specified `RANDOMIZATION_DRAWS` is refused in real mode (the docstring said
so; the code only printed a note). The sealed result is written to a
**tracked** path (`data/reference/confirmatory_results.csv`) so that the one-shot
is visible in the commit history, not to the gitignored `outputs/`. The
asymptotic joint-Wald p is computed for every randomization cell and written
beside the randomization p, as §7 of the note promised and no code did.

**23.6 Cells that would re-estimate the primary design under a new seed are not
run.** A broad-basket or spliced sensitivity whose episode starts in a stratum
equal the primary's is recorded `IDENTICAL_TO_PRIMARY`, as the coverage-clean
cells already were, rather than printing a second p-value for one estimate.
The late B-HEARD bound is filed in the `sensitivity` family (§9.5), not
`secondary`; pooled primary-bound cells are `descriptive`; the interaction arm
runs in C2 only, as §5 of the note states.

**23.7 The EDP family is every EDP-prefixed code.** The declared coverage span
table (§18) lists EDPT (first seen 2023-03-01) and EDPE (2024-04-10), both
inside C2 and both absent from `config.CALL_TYPE_GROUPS["edp"]`, which held
EDP, EDPC, EDPM, EDPW and T-EDP. A family that omits two later codes of the same
prefix carries a downward break in the EDP share from 2023. They are added
under the stated rule — every EDP-prefixed dispatch code — with no outcome
value read; the two births become within-window breaks under §18 rule 1 and
enter the coverage-clean sensitivity for C2.

**23.8 The panel spans the extract.** `01_build_panel.py` was hard-bounded to
the discovery buffer (2016-12-01..2021-01-31), so after the lift no
confirmation-window row would have existed for the sealed script to read.
`PANEL_BUFFER_START/END` now cover 2014-12-01..2024-12-31; which rows a script
may see is decided by `freeze_guard.select_sample` alone. The five-dispatch
minimum applies to both arms (it already did in the estimator and the sealed
script; the note and PAPER_MASTER said "share calculations").

**23.9 Dispositions of the frozen text.** H3's Black-victim clause is not run:
its index (`aware_black`) was retired with the Twitter measure and CCRB/SQF data
are not in the repository; the Q1-protest hypothesis is exploratory, formed on
discovery heterogeneity (§14), and is not tested on the confirmation sample.
The second primary outcome (`mh_narrow_share`) and the joint two-sided
statistic over days 0–7 were adopted after discovery results had been seen; §14
already discounts the H1 framing on that ground and now names both. "What has
NOT changed" below keeps the frozen text's 2015-01-01; the analysis window
begins 2015-07-01 because the pageview series does (§18, note §4).

**23.10 Two accesses the record had not named.** The precinct–district
crosswalk (S14) was built by a server-side SODA count of dispatches per
precinct × district pooled over 2015–2024: a geography weight, no call type and
no date, but a read of confirmation-period dispatch counts, recorded as
incident **F4** in §15 and PAPER_MASTER §5.3. §18 rule 2's justification cites
the 0.0002 step estimate from the F3 refutation; the rule stands on its
pre-specified form, and the figure is now labelled as F3-derived where it
appears. Rule 1 as implemented treats a code born or retired on a window's
boundary day as inside it; the text is read the same way.

**23.11 Power under the family correction.** Rule 2 of §19 reads a
non-rejection against a minimum detectable effect computed at the per-test
nominal α = 0.05. Under the eight-test correction the effective threshold is
stricter, so the detectable effect is larger by a factor of roughly
(z₀.₉₉₆₉ + z₀.₈)/(z₀.₉₇₅ + z₀.₈) ≈ 1.28 at the Bonferroni bound; the bounded
null is stated at the nominal level and this factor is quoted beside it.

**23.12 What the calibration certificates do not cover**, stated as a
limitation: the synthetic null is OLS on a Gaussian EDP share with no covariate
and a white-noise citywide day shock; the PPML arm, the narrow mental-health
outcome and the B-HEARD control are not separately certified, and size is
certified at α = 0.05 with a global uniformity test rather than at the
correction's effective threshold.

## 24. Placebo admissibility follows first-week containment (finding P13)

**Blind.** Treatment-side geometry; found 2026-09-13 by the CP2 audit and
confirmed by measurement before any outcome was read.

The within-block shift (§21) drew placebo starts over days whose full ±14-day
window lies inside the block. Two of C1's fifteen episodes (2021-01-05 and
2021-05-24, §17) lie inside the block by first-week containment but not by the
full window, so the drawer *snapped* each to the block's first or last
admissible day — positions 0 and N−1 — and a circular shift of those two
positions puts them on **consecutive days**. Measured over 400 C1 draws: 397
carried two placebo episodes one day apart against a real minimum gap of 16
days, and `build_stack` then hands nearly all of one episode's days to the
other. The null was drawing designs structurally unlike the real one; C1's
weak uniformity margin (§7.4) is consistent with that.

The fix makes admissibility the same rule that keeps a real episode: a placebo
may start on any day whose day −1 through day +7 lie inside the window. Every
kept episode is then on an admissible day, nothing snaps (asserted and
counted), and the shift preserves the real gaps except across the seam, which
§21 already discloses (the cyclic complement of the 2021 block's 139-day span in
143 admissible days is 4 days, so most draws contain one 4-day gap). The scheme
is renamed **`circular_within_block_fw7`** so that the C1 and pooled
certificates issued under the snapping drawer stop satisfying
`S.ri_scheme_certified`; both strata are recalibrated at 200 and then 1,000
simulations before the lift. Discovery and C2 use the anchor shift and are
untouched.

---

## 25. If a stratum's null cannot be certified at 1,000 simulations

**Blind. Written 2026-09-13 at 18:00Z, after C1's 200-simulation run under
`circular_within_block_fw7` returned NOT CALIBRATED (rejection 0.035 inside
the band; lattice KS D = 0.097, p = 0.0455; median simulated p 0.433) and
before any 1,000-simulation verdict existed.** No outcome value has been read.

C1's null has been the least uniform of the four at every stage — p = 0.066
under the seam-crossing shift, 0.123 under the snapping drawer, 0.0455 under
the corrected one — and its geometry explains why: five episodes spanning 139
of the 2021 block's 143 admissible days leave a circular shift four days of
slack, so most placebo designs carry a 4-day gap the real design does not
(§24). The 1,000-simulation run decides. If it certifies C1, nothing here
applies. If it returns NOT CALIBRATED:

1. **The sealed run proceeds.** C1's cells are estimated exactly as specified;
   their randomization p-values are written and flagged `UNCERTIFIED_NULL`.
2. **C1's cells are excluded from the family decision**: they enter the
   Benjamini–Hochberg step as p = 1, so the family stays eight and the
   correction is unchanged for C2's four cells.
3. **C1's primary inference is the asymptotic joint-Wald p** (date-clustered),
   labelled asymptotic. On discovery that p was anti-conservative (0.019
   clustered against 0.26 by permutation), so a C1 rejection on it is reported
   as *not certified* and cannot count as confirmation under §9.4; a C1
   non-rejection is read by §19 rule 2 unchanged. C1's estimates, intervals and
   day-by-day paths are reported in full: the clean years are still described,
   they are not confirmed.
4. **The same rule applies to C2 and to the pooled stratum** at their own
   sizes (1,000 and 200), and to no other case: a certificate that is absent,
   below size, or issued for another scheme still refuses the run.
5. **What is not done.** The stratum is not redefined (dropping the 2021 block
   would discard 5 of 15 clean episodes, including the Chauvin-verdict weeks),
   the draw scheme is not changed again, and no alternative null is tried on
   the sealed data. Any of those after the verdict would be a choice made in
   view of the result.

`S.ri_scheme_certified` and `S.lift_requires_1000_sims` treat a ≥1,000-sim
NOT CALIBRATED verdict under the required scheme as this case rather than as a
missing certificate; `30_confirmatory_run.py` implements items 1–3.

---

## What has NOT changed

- Discovery 2017-01-01 → 2020-12-31; confirmation 2015-01-01 → 2016-12-31 and
  2021-01-01 → 2024-12-31. No confirmation-window outcome has entered any model.
- H1's **direction** is still pre-specified: a decline in the days after a
  high-attention episode.
- Randomization inference is still the primary p-value.
- 59 community districts; date-clustered inference.
- The frozen episode list is still byte-identical to its committed version.
