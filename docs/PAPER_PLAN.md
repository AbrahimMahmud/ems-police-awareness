# Paper plan: structure, display items, and drafting rules

Working title (noun-phrase, not a claim — the estimate cannot support a claim title):

> **Public attention to police violence and emergency help-seeking in New York City, 2015–2024**

This document is the drafting spec. It fixes the venue decision, the section
skeleton with word budgets, every display item, the reporting-checklist
obligations, and the language rules. It is built from a survey of ~30 recent
quantitative papers in AJPH, *Journal of Urban Health*, *JAMA Network Open*,
*SSM–Population Health*, *Social Science & Medicine*, *American Journal of
Epidemiology* and *Prehospital Emergency Care*, plus the anchor papers in this
literature and the STROBE/RECORD checklists.

---

## 0. The decision that comes before drafting

**Has the confirmatory run happened?** If not — and per `GATE_C_MEMO.md` it has
not, since Gate C is open and the extension freeze is intact — there is a route
that is strictly better than conventional submission:

**Registered Report.** PCI Registered Reports recognises six levels of bias
control, and **Levels 1–5 cover already-existing data**; Level 2 is "key
variables not yet observed", which describes the 40 frozen extension episodes
exactly. *Nature Human Behaviour* independently accepts secondary-data RRs and
names "proposing key analyses in an unseen holdout sample" as acceptable bias
control. Stage 1 (Introduction + Methods, reviewed before results exist) yields
in-principle acceptance that **cannot be revoked based on the outcome**; Stage 1
review averages ~9 weeks. 123 journals accept a positively recommended PCI-RR
submission without further review.

This converts the project's weakest asset — a primary estimate that may return
inconclusive — into its strongest. Given permutation inference already returned
p ≈ 0.26 on discovery, that is not a hypothetical benefit.

The window closes the moment the confirmatory analysis runs. **Decide before
Phase D, not after.**

If the RR route is declined, deposit the frozen pre-registration to OSF with its
timestamp and cite it in Methods; PCI-RR's Level-1/Level-2 vocabulary is
standard and reviewers recognise it even outside the RR format.

---

## 1. Venue and the constraints it imposes

| | Primary | Catch |
|---|---|---|
| Journal | **Journal of Urban Health** | **SSM – Population Health** |
| Main text | ~4,000 w excl. abstract/refs/display | 8,000 w **including** refs, tables, figures |
| Display items | **4 total** | counted inside the 8,000 |
| References | 50 | counted inside the 8,000 |
| Abstract | unstructured, ≤250 w | ≤250 w |
| APC | hybrid; OA optional | gold OA, ~US$3,610 |

JUH has the right precedents on both sides: NYC EMS administrative data at
neighbourhood scale, and police-shooting exposure as a health variable.

**Two venue facts that change drafting:**

- **AJPH is effectively out.** ~4% acceptance for research articles, and its
  editorial policy appears to treat preprints as prior publication. It also
  limits figures to a single panel ("2 individual panels may be permitted" only
  for direct comparison), which forbids the episode small-multiples figure
  outright. *Verify the preprint policy with the editorial office before
  acting — the live page could not be rendered during research.*
- **Prehospital Emergency Care instructions could not be verified.** The only
  publicly reachable author-instructions document is a decade-plus obsolete (it
  requests floppy disks). Get current requirements from Taylor & Francis or
  NAEMSP before drafting to it.

**Four display items is the binding constraint on this paper.** Plan the
supplement from the first draft, not at revision.

---

## 2. Template

This literature splits into two paper shapes:

- **Template A** — public health (AJPH/JUH/JAMA NO/AJE/SSM-PH). 3,000–4,000
  words, structured or short abstract, no standalone literature review, Methods
  with named subsections, Results with no interpretation, Discussion in a fixed
  five-move order, **labelled and long Limitations**.
- **Template B** — social science (*ASR*, *QJE*). 12,000–20,000 words, theory
  section with its own heading, numbered equations, contribution as an
  enumerated list, limitations dissolved into the Discussion.

**Use Template A**, for two reasons. It converts upward to Template B far more
easily than the reverse. And more importantly, Template A has a mature,
unembarrassed register for exactly this evidentiary situation — "we did not find
conclusive evidence … effect estimates indicated" — whereas Template B's grammar
("I find that X leads to Y") has nowhere comfortable to stand when the estimate
is imprecise.

---

## 3. Section skeleton with word budgets

### Title
Noun-phrase, with place and period in it (RECORD 1.2). Must name the data type
and, ideally, the linkage (RECORD 1.1, 1.3). Not a claim.

### Abstract — ≤250 w
Must name: NYC EMS Incident Dispatch Data by name, New York City, 2015–2024, and
that EMS records are linked to community districts and to a publicly
reconstructible attention index. Name the design with a standard term (STROBE
1a): "panel", "event study", "quasi-experimental".

**Frame the question three-way.** Following the strongest construction found in
the survey (*JAMA Netw Open*, Kim et al. 2024, on bail reform): *"Did gun
violence increase, decrease, or remain unchanged after…"*. Ours:

> Does public attention to police violence increase, decrease, or leave
> unchanged what New York City communities ask emergency services for?

This is not a rhetorical trick — it is the accurate description of what was
tested, and it means no result can disappoint the question.

### Introduction — 500–700 w, 4–6 paragraphs, no subheadings, no lit-review section

1. **Framing.** Policing as a structural determinant of health. (The dominant
   current opener in JUH/AJE.)
2. **Mechanism.** Why publicized police violence should affect what people ask
   of emergency services — direct and vicarious exposure; legal cynicism.
3. **Prior work with one quantified anchor and its limitation.** This is where
   the gap is built, not asserted.
4. **The gap, three legs, in this order:** (i) prior exposures are *incidence*,
   not *attention*; (ii) temporal resolution is monthly or coarser, so the shape
   of response inside the first week is unobserved; (iii) prior outcomes sit
   downstream of a help-seeking decision (hospitalisation, ED visit) rather than
   at the decision itself (EMS activation).
5. **Objectives**, with pre-specified hypotheses named (STROBE 3).

The contribution statement is the **last two sentences of the Introduction**, as
objectives — not a separate enumerated block. That is Template B.

`docs/RELATED_WORK.md` compresses into paragraphs 3–4 here plus one Discussion
paragraph. There is no other place for it; no paper in the survey had a
"Related Work" heading.

### Methods — 900–1,300 w, with subheadings

- *Study setting* — NYC, 59 community districts, 2015–2024. Gloss "community
  district" in one clause; a national readership does not know the unit.
- *Data sources* — one paragraph per source, each naming custodian, years,
  access date. EMS dispatch; ACS 2015–19; Wikipedia pageviews; Google Trends;
  B-HEARD adoption; precinct↔CD crosswalk.
- *Measures* — exposure, then outcome, then covariates, in that order.
- *Statistical analysis* — the model, fixed effects, SEs, the primary inference,
  and the sensitivity battery. **Designate primary vs exploratory here.**
- *Ethics* — one line. NYC EMS dispatch data are public and de-identified;
  obtain and cite a written MIT COUHES non-human-subjects determination.

**Methods vs supplement rule** used throughout this literature: the Methods carry
everything needed to *judge whether the design identifies anything*; the
supplement carries everything needed to *reproduce it*.

### Results — 700–1,000 w, fixed order, **no interpretation**

1. Sample description with denominators
2. Raw pattern (ties to Figure 1)
3. Primary result — estimate, interval, and effect size **on a scale a reader
   can feel**
4. Decomposition, in the pre-declared order
5. Heterogeneity
6. Sensitivity and falsification, compressed, ending with whether conclusions
   changed

Every "this suggests" belongs in the Discussion. Public health enforces this far
more strictly than economics.

### Discussion — 800–1,100 w, five moves in this order

1. **Restatement opening with the design, not the finding.** Every strong paper
   in the survey does this: "This study leveraged…", "To our knowledge, this
   cohort study is the first to…". Our durable contributions do not depend on
   the p-value: daily resolution inside the first post-event week; a verifiable
   multi-source attention index replacing a non-reproducible social-media
   measure; EMS activation as the help-seeking decision itself; a genuine
   discovery/confirmation split with a frozen episode list. **Say these first.**
2. **Mechanism** — what would have to be true for the pattern to be real.
3. **Comparison to prior work**, including work that disagrees.
4. **Limitations** — see §6.
5. **Implications / conclusion.**

---

## 4. Display items — the four that go in the main text

Chosen so that the argument survives even if the primary estimate is null.

**Figure 1 — Raw series with episodes marked.** Daily mental-health call share
citywide, with CAI-D episodes marked, and the CAI-D series itself in a stacked
panel. *Raw data must come before any coefficient plot* — this is the current
expectation and the first recommendation in the Wing et al. (2024, *Annu Rev
Public Health*) DiD guidance, which explicitly says to plot raw data in calendar
time rather than jumping to an event study. Convention: solid coloured vertical
line = focal episode, dashed = confounding event (COVID emergency, B-HEARD
launch), shaded band = period. Consider normalising to the day before the
episode.

**Figure 2 — Event-study coefficient plot.** Relative time on x, coefficient on
y, reference period marked with a vertical dotted line, **horizontal line at the
null**, 95% CIs as whiskers. Caption must spell out the null line explicitly —
a public-health reader should not have to infer it.

**Figure 3 — Outcome decomposition forest plot.** EDP / ALTMEN / suicide-related
/ OD-drug / cardiac / asthma / injury / total, each with CI, null reference line,
placebos in a visually distinct block. **This is the figure that carries the
argument**, because it shows the placebo nulls and the EDP/injury pattern in one
frame.

**Table 1 — The frozen episode list.** Date, event, CAI-D peak, B-HEARD window
flag, clean-control-window flag, discovery vs extension. This table *is* the
credibility of the pre-registration — it is the object that was frozen before
outcome contact. Main text, not supplement. Wing et al. recommend an adoption
timeline table as emerging best practice for exactly this reason.

### Supplement inventory

- **Permutation/randomization-inference histogram.** Placebo coefficients with a
  vertical line at the observed estimate. *If the venue allows a fifth display
  item, promote this to the main text* — randomization inference is the primary
  p-value, so this figure is the honest visual representation of the headline
  result.
- Map of the 59 community districts shaded by demographic composition, or by
  district-specific estimate. A map of *unit-specific coefficients* (as in
  Santaularia et al. 2025, *AJE*, Fig 3) is the best way to display
  non-monotonic heterogeneity without claiming a gradient that isn't there.
- Episode small-multiples (barred at AJPH by the single-panel rule; fine at JUH,
  AJE, JAMA NO, SSM-PH).
- CAI validation battery: component correlations, peak alignment, NYC-vs-national
  Trends correlation, CAI-D vs CAI-S divergence days.
- Full dispatch-code crosswalk with years of validity (RECORD 7.1).
- Linkage/exclusion flow diagram (RECORD 6.3).
- Alternative estimators, window sensitivities (+28/+60), transform
  sensitivities, leave-one-out, drop-Floyd, drop-2020.
- Descriptive Table 1 equivalent (panel characteristics).
- The bridge result: legacy z-score vs log, as the methods demonstration.

### Caption rules
Object → definitions (treatment, control, sample, period) → statistical detail
(clustering, adjustment, estimator) → graphical conventions **spelled out** →
abbreviations. Place and time in every caption.

### Colour and accessibility
Colour is standard and free online. Never encode the only distinction in
red-vs-green; make colour redundant with line type, position, or direct
labelling, and check greyscale legibility. Print quality 300 dpi minimum.

---

## 5. Reporting checklist obligations

**RECORD, not plain STROBE, and not RECORD-PE.** RECORD is the extension for
routinely collected health data, which is exactly what EMS dispatch records are.
RECORD-PE is pharmacoepidemiology-specific and does not apply.

The items that actually change the draft:

| Item | What it demands | What we must do |
|---|---|---|
| 1.1–1.3 | Data type, database name, geography, timeframe, and linkage in title/abstract | Rewrite the abstract to name all four |
| **6.2** | **Cite validation of the codes used to identify the population** | **Cite Kang, Lu & Pang (2026, *Psychiatric Services*, doi:10.1176/appi.ps.20250528) as the validation precedent for mental-health call classification on this exact dataset — and state where we differ (disaggregated call families; explicit handling of the mid-2018 EDPC recode)** |
| 6.3 | Flow diagram of the linkage process | Supplement figure |
| 7.1 | Complete code list for exposures, outcomes, confounders | Supplementary table: every dispatch code, its family, its years of validity |
| 12.3 | Linkage **quality evaluation**, not just description | The precinct×CD crosswalk needs a validation section, not only a description |
| 13.1 | Why these units were selected | The 59-district whitelist rationale belongs in the main text |
| **19.1** | Discuss **changing eligibility over time** | **The EDPC recode phased in mid-2018 and the retired legacy OD/POISON codes. Put this in Limitations explicitly — a reviewer who finds it unaided will treat the paper as unreliable** |
| 22.1 | How to access protocol, data, code | The replication package, the frozen episode list with its git timestamp, and the CAI provenance/hash log. This item is what turns the pre-registration discipline from a private virtue into a reportable one |

Also relevant: STROBE 10 ("explain how the study size was arrived at") is the
honest place to say the panel is large but the number of independent shocks is
small; STROBE 19 requires discussing **direction and magnitude** of potential
bias, not merely its existence; STROBE 20 requires discussing "multiplicity of
analyses", which is the explicit licence and obligation to describe the
exploratory/confirmatory split.

---

## 6. Limitations — order and construction

Public-health limitations sections are long (Bor et al.'s runs eight items and
~500 words, roughly 8% of the article) and ordered **strongest objection first,
each answered rather than merely conceded.**

The move to imitate, from Bor et al. (2018): name the objection, **convert it
into a defined estimand**, then state what the estimate remains valid for —
they answer exposure misclassification by declaring an intention-to-treat
interpretation and noting the estimate is still a valid measure of population
impact.

Our order:

1. **Exposure is a national attention index, not district-level awareness.**
   → intention-to-treat interpretation.
2. **Few independent episodes; estimates imprecise.** Randomization inference is
   the appropriate reference distribution and we report it as primary.
3. **Share outcomes are compositional** — injury growth mechanically depresses
   other shares. Counts reported alongside. *A referee raises this first if we
   don't.*
4. **Dispatch-code drift** (EDPC recode) and what we did about it — RECORD 19.1.
5. **B-HEARD overlap** in the extension window and how it is handled.
6. **Call type is a dispatcher's classification of a caller's account**, not a
   clinical diagnosis; EMS activation measures a decision to summon, not
   underlying need.
7. **Generalisability** — NYC's density, EMS system and B-HEARD program are
   distinctive.

Where a limitation biases toward the null, say so — it strengthens the paper
("these results likely understate…" is a standard and effective construction).

---

## 7. Language rules for this paper

### Causal register — what we can and cannot afford

The verb ladder in this literature runs: *associated with* → *may be associated
with / appeared to* → *predicts* → *we estimate that* → design-conditional
causal → flat causal. Public-health journals default to the first; only
economics and sociology use the last.

**Causal language in public health is a purchase, and robustness is the
currency.** Bor et al. make exactly one causal claim, and it appears in the
first paragraph of the Discussion, immediately after "these findings were robust
to a wide array of specification checks", and is paid for by an eight-part
limitations paragraph. With randomization-inference p ≈ 0.26 we cannot buy that.
**This paper lives in rows 1–4 of the ladder throughout.**

The one place we can go slightly stronger is **specificity**, which is a claim
about the data rather than about causation. Bor et al.'s formulation is worth
adapting directly to call types: any confounder that would bias the primary
estimate away from the null would also be expected to bias the placebo estimates
away from the null — and they are null.

### Reporting an inconclusive result

Never "there was no effect". The standard two-clause construction: *we did not
find conclusive evidence of X … although effect estimates indicated Y*. "Null and
imprecise" is a respectable phrase in wide use. Report the interval and name its
width. Where a signal survives some specifications and not others, say exactly
that and say which is trusted. Flag unexpected nulls as unexpected rather than
burying them. A placebo that undercuts our own result gets reported in the same
voice as one that supports it.

Draft sentences for the primary result (numbers to be replaced after the CAI-D
re-run):

> We did not find conclusive evidence that attention spikes changed the share of
> emergency medical activations coded as police-adjacent mental-health calls.
> Joint tests across the first post-episode week were compatible with a change in
> call composition, but episode-level randomization inference — the appropriate
> reference distribution given the number of independent episodes — did not
> distinguish the estimated effect from chance. We therefore report this as a
> suggestive compositional shift rather than an established effect.

> Placebo outcomes were null, as pre-specified. A null placebo constrains the
> space of confounders but does not by itself establish that the estimated change
> in police-adjacent calls is real.

### Placebos
Never present a placebo without its substantive rationale. Desmond et al.'s
model: state the placebo, then state *why* it should be unaffected. Pick one
term — "falsification test", "negative control outcome", or "nonequivalent
dependent variable" — and use it consistently.

### Heterogeneity
Our quartile pattern is non-monotonic and we cannot explain it. Do not
manufacture an explanation. State what each competing mechanism would predict
and note that current precision discriminates between neither. **And engage Ang,
Bencsik, Bruhn & Derenoncourt directly**: their call declines were comparable in
majority-white, majority-Black and majority-Hispanic neighbourhoods, which means
a flat or non-monotonic gradient is *not* disqualifying in this literature. Cite
them, and turn the untested part into a stated, testable prediction.

### Race and ethnicity
Capitalise **Black** and **White** (AMA style since 2021). Frame police violence
as a manifestation of structural racism rather than treating race as the causal
variable; current AJPH guidance is "measure racism, not just race". Justify in
Methods why racial composition is assessed, how districts were classified, what
the categories are, and who selected them — for us: ACS respondent
self-classification into OMB categories, used because police violence is
racialized in its incidence and in whom it is likely to be salient to.

Never write "Black districts" without first defining the measure — write
"predominantly Black community districts (≥X% Black residents, 2015–2019 ACS)".
Avoid "minority"/"minority neighborhoods" (dated), and "police brutality" in
analytic prose (rhetorical register).

### The exposure is attention, not violence
Be scrupulous. Write "attention episodes", "high-attention days", "publicized
incidents". Never let "police violence" drift into being the exposure variable —
that is a different paper, and reviewers will conflate the two if allowed.

### Mechanics
- **"We"** throughout; never "the authors". Passive only for data operations
  ("data were aggregated"), never for analytic choices.
- Tense: Methods and Results past; Discussion past for findings, present for
  interpretation; captions present.
- **Report confidence intervals everywhere; p-values sparingly** — with a CI a
  p-value is redundant. Give p to two decimals. Never "NS", never "p < .05"
  alone, never "trending toward significance".
- **Anchor every estimate to a scale a reader can feel.** A coefficient of
  −0.0005 on a share means nothing; percentage points against the mean share,
  the relative change, and approximate citywide activations per high-attention
  day mean something.
- **Do not abbreviate "community district" to CD** in the manuscript. Avoid
  invented abbreviations generally; if the composite index keeps a coined
  acronym, define it once and use it sparingly.
- Avoid: "proves", "demonstrates that X causes Y", "the effect of attention on…"
  as a bare noun phrase, "significant" meaning "important", "robust" without
  saying to what, "the first study to…" without "to our knowledge", "impact" as
  a verb.

---

## 8. What blocks drafting right now

| # | Blocker | Owner |
|---|---|---|
| 1 | Registered Report decision — closes permanently once confirmation runs | Justin + Abrahim |
| 2 | Re-run the discovery pipeline under CAI-D; every number in the draft depends on it | analysis |
| 3 | Gate C §5 power recomputation | analysis |
| 4 | Read Hölzl, Keusch & Sajons (2025), *Social Science Research* 126:103099 — a systematic review of Google Trends misuse across 360 studies. Both the best precedent for our methods contribution and its closest competitor; CAI-D leans on Trends for two of three components | Abrahim |
| 5 | Read Kang et al. (2026) in full and draft the two-paragraph "how we differ" passage | Abrahim |
| 6 | MIT COUHES non-human-subjects determination in writing | Abrahim |
| 7 | OSF deposit of the frozen pre-registration with timestamp | Abrahim |
| 8 | Confirm JUH word/display limits and AJPH preprint policy from the live pages | Abrahim |

---

## 9. On splitting the methods contribution

**Keep the z-scoring result inside this paper.** Two or three paragraphs plus one
supplementary figure. It is short, it is decisive, and it pre-empts the reviewer
who asks why we did not z-score. Publishing it separately first would strip this
paper of its one unambiguous contribution and leave an inconclusive EMS result
standing alone.

A standalone methods paper is viable later, but only with real added work: a
simulation showing analytically when z-scoring a heavy-tailed attention series
manufactures outlier-leveraged significance, plus re-analysis of two or three
published attention-measure studies showing transformation-dependence. Without
those it is a note, not a paper. *Social Science Research* is the target, as the
direct continuation of Hölzl et al. Submit this paper first regardless — if the
methods paper lands first, this one reads as "an application of our own method",
which reviewers treat as weaker.
