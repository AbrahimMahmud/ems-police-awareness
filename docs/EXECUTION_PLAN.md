# Plan: from here to the finished paper

## Context

The question is whether public awareness of police violence changes what New
Yorkers ask EMS for. The pipeline that answers it is largely repaired — the
outcome data is whole, the estimator's defects are fixed and verified against a
planted effect, the freeze guard can reject things, the episode construct is a
bounded shock rule.

**But no analytic estimate exists yet, not even on discovery.** Of the 17 tables
an estimation run produces, 2 exist, and both predate the last change to the
estimator module they came from. `outputs/figures/` has never held a figure.

Three things block that run, and this session's investigation found all three to
be different from what the code and documents say they are:

1. **The basket rebuild is blocked by a misdiagnosed network failure.** All five
   non-passing checks descend from one stalled chain, and the reason it stalled
   is not the reason recorded in the code.
2. **Roughly half the treatment basket has no evidence of measuring police
   violence.** 61 of 120 articles were admitted through a topic category, and
   nothing downstream ever tests who did the killing.
3. **The calibration that gates the primary estimator has been destroyed** by a
   smoke-test run, and the artifact is gitignored, so it is not recoverable from
   git.

This plan runs from here to a finished paper, continuously, with no sign-off
gates. Barriers get resolved, not deferred. **The endpoint is a conclusion**: a
confirmatory result on data never examined, or an explicit, evidenced finding
that the design cannot deliver one. Both are publishable; neither is a failure.

---

## Standing rules

**Every change passes the gate before the next begins**
```
cd scripts
../.venv/bin/python 23_regression_suite.py     # target flips, nothing else moves, exit 0
../.venv/bin/python 20_data_audit.py           # flag count non-increasing
../.venv/bin/python -c "import ast,pathlib;[ast.parse(p.read_text()) for p in pathlib.Path('.').glob('*.py')]"
```

**Every new check gets a defeat attempt before baselining.** Make it pass with
the defect intact; make it fail with a valid alternative fix. This has caught
something nearly every time it has been tried.

**Any unintended flip stops the work**, including a flip toward PASS.

**`docs/PAPER_MASTER.md` updates in the same commit as the change it describes**,
in language a non-specialist can follow. **Baseline refreshed in the same commit
as the fix**, never separately.

**Background jobs are polled by PID file or sentinel file, never `pgrep -f`.**
A `pgrep -f` pattern matches the shell whose command line contains it, so a
waiter waits on itself. This has cost four incidents.

**Constraints:** all work on `analysis-rework` (no other branch;
this is the standing instruction). No AI-assistant attribution in any commit,
document, or artifact.
`data/reference/confirmation_episodes.csv` stays byte-identical to HEAD.

---

## Decisions taken (recorded, with reasoning)

| Decision | Call | Reason |
|---|---|---|
| **Basket construct** | **Strict primary** (verified law-enforcement killings) **+ broad basket as a pre-registered sensitivity** | Confirmed with the user. Lets the paper say the result does not depend on where the line was drawn, instead of asserting it. |
| **Attention to violence *against* police** (Micah Xavier Johnson, Gonzalo Lopez) | **Exclude from every basket, and disclose**, including what removing them does to the 2016-07-08 index peak | Confirmed with the user. It is the opposite construct, and it currently sits on the index's headline validation day. |
| **Episode list the estimators consume** | The **rebuilt** list (`confirmation_episodes_rebuilt.csv`); frozen file stays untouched as an artifact; the diff is a disclosed deviation | Already decided; never implemented. 17, 07, 08 and 18 all still read the frozen file. |
| **CAI-D composition** | `wiki_ext` + `trends_us` (national) | `trends_nyc` retired on three independent grounds; `wiki_nyc` rejected. |
| **Freeze posture** | Hold the line; no third confirmation-window access | Conservative default taken when the question was dismissed; reversible, and recorded as such. |
| **Freeze incidents F1, F2** | Disclose in full; proceed | Neither touched an H1 test. The gaps that allowed them are closed. |

---

# Phase A — Unblock the network path

**The diagnosis in the code is wrong, and that is why the retries failed.**
`26_resolve_basket_scope.py:30-32` states the endpoint "is currently
rate-limiting to 1 request/minute during an outage." Measured this session:

- A trivial SPARQL query returns **HTTP 200 in 0.3 s**. There is no outage.
- Wikimedia's edge (`server: envoy`) runs a **per-IP token bucket shared across
  hosts**. In the same second, `www.wikidata.org` returned 200 while
  `en.wikipedia.org` returned 429 with `Retry-After: 49`; minutes later
  `www.wikidata.org` itself returned 429. Observed `Retry-After`: 2, 5, 49, 52 s.
- **26 is the only Wikimedia client in the repo that ignores `Retry-After`**
  (`26:74` waits a fixed 70 s). 11, 24, 28 and 29 all honour it.
- **26's cache key embeds the batch size** (`26:111`, `scope_{i:04d}_{len(chunk)}`),
  so `--batch 25` cannot reuse `--batch 40` files. "the cache makes it
  resumable" (`26:80`) is false precisely when you follow the retry advice in
  `27_finalise_basket.py:129` ("use --batch 50").
- **`11_fetch_awareness_components.py` has no pageviews cache at all.** It
  refetches ~500 title-series every run, and writes `wiki_ext` even when titles
  failed (`11:185-201` records `n_titles_failed` and continues) — a rate-limit
  interruption silently degrades the treatment index.

**A1.** Kill the two deadlocked waiters by explicit PID (`ps -eo pid,args`,
never `pkill -f`). Both are spinning on `pgrep -f "python 26_resolve_basket_scope"`,
which matches their own parent shells; 26 itself is not running.

**A2.** New `scripts/wikimedia.py` — one HTTP client for every Wikimedia host:
honours `Retry-After`, holds a single global pacer, caches each request on disk,
and takes a cross-process lock so only one client draws on the shared bucket at a
time. Replace the five hand-rolled retry blocks in 11, 24, 26, 28, 29. Reuse the
existing cache-file pattern from `24` (`wiki_cat_cache`) and `29`
(`wiki_probe_cache`).

**A3.** Re-key 26's cache on a hash of the chunk's article list, so batch size
never invalidates it. Add `action=wbgetentities&sites=enwiki&titles=` as a second
transport (verified working: 10 articles, HTTP 200, 0.5 s, returns QID, label,
sitelink and claims in one call). **Adopt it only if it passes an equivalence
test**: for the 145 articles already resolved by SPARQL it must return identical
`article/item/date/country/manner`, or the differences are reported rather than
adopted. Changing transport must not change data.

**A4.** Give 11 a per-title pageviews cache, and make it **refuse to write**
`wiki_ext` when any title fetch failed. A recorded failure that still ships the
degraded series is the T15 defect with a receipt.

**A5.** Correct the false statements at `26:30-32` and `26:80`; file them as
findings (the project's own recurring class — an assertion that reads as
established because nobody re-checked it, living in a code comment).

**Gate:** suite + audit + defeat attempts on the equivalence test.

---

# Phase B — Basket construct validity

The largest research risk in the project, and it was invisible to every existing
check because all of them validate coverage rather than content.

Measured: `wiki_basket.csv` records the category each article was reached
through. Of the 120 included articles, **57 entered via "Black Lives Matter"**
and 4 more via "2020/2021 United States racial unrest" — **61 of 120 (51%)
through a topic category**. `27_finalise_basket.decide()` tests country and date
only; it never tests who did the killing. Wikidata's `manner of death` (P1196) is
present on **6 of 164** rows, so it cannot gate anything, and where it is present
it is unreliable (Eric Garner: "natural causes").

Consequences already visible in the basket:

- Civilian killings admitted as police violence — Ahmaud Arbery, Renisha
  McBride, Markeis McGlockton, James Craig Anderson, and others.
- `Micah_Xavier_Johnson` — the Dallas gunman who killed five officers — is in the
  index, and his date, 2016-07-08, is the index's top attention day.
- **`country` is present on only 80 of 164 rows**, so `NON_US` excluded just 2
  articles; **58 of 120 included articles were admitted with no country check
  at all**.
- Registry date fallback matches wrong people: `Killing_of_José_Campos_Torres`
  is dated 2014-08-07 (he was killed in 1977); `Murder_of_James_Craig_Anderson`
  is dated 2013-01-27 (2011). 43 of 120 included articles take their date from
  this fallback, and the date decides scope.

**B1. `scripts/32_validate_basket_construct.py`** — one row per candidate with a
decision and a *cited* source, never hand-classification from memory (the error
class the repo correctly warns about at `26:25-28`). Signals, all public and
re-runnable: the article's **full** category set via `prop=categories` (24 records
only the first category BFS reached, via `articles.setdefault`), Wikidata claims
(P157 killed-by, P1196, P31), and registry membership as corroboration only —
never as a gate (finding T9). Writes `data/reference/basket_construct_review.csv`.

**B2. Two baskets.** `basket_strict.csv` requires a positive law-enforcement
signal; `basket_broad.csv` is the current rule minus the anti-police exclusions.
`CAI_D_BASKET` selects; the broad arm is pre-registered as a sensitivity.

**B3. Repair the scope rule in 27** — a country test that fails closed rather
than admitting on absence, an explicit anti-police exclusion with a recorded
reason, and a date-fallback that refuses a registry match whose date is outside
the article's own plausible range.

**B4. New checks, each with a defeat attempt:** `T.basket_is_police_violence`
(no included article lacks a positive law-enforcement signal),
`T.basket_country_checked` (no article admitted on a missing country),
`T.basket_date_plausible` (no registry-fallback date contradicts Wikidata or the
article's creation date).

**Gate:** the 120→strict diff is published in `basket_decisions.csv` with a true
reason per article; PAPER_MASTER §4.1 rewritten around it.

---

# Phase C — Finish the rebuild chain, then re-register everything

Run `26 → 27 → 29 → 11 → 28 → 12 → 13` with one Wikimedia client at a time.
Then close the five non-passing checks and re-establish every number that moved.

- `T.no_duplicate_person` (FAIL — 9 articles double-count a person, 449,549
  views, 0.35%), `V.artifacts_current` (FAIL — 2 stale artifacts),
  `V.claims_reproduce` (FAIL), `T.wiki_fetch_complete` (BLOCKED),
  `T.no_redirect_candidates` (BLOCKED).
- **C04/C05/C06 are real mismatches** (computed 120/119/27 against 121/111/24 in
  the document). **C20 and C22 are false failures** — the claim matcher cannot
  see a template that markdown wrapped across a newline (`PAPER_MASTER.md:274-275`,
  `:278-279`). A check failing for the wrong reason is its own finding: fix the
  matcher, then re-verify.
- Confirm Walter Scott (2,228,711 views, would rank 15 of 121, peaks 2016-07-08)
  and Jordan Edwards are in the **index**, not merely the basket; confirm the 9
  duplicates are gone; re-check the index top days.
- Re-run `31_verify_sources.py`, `22_pipeline_check.py`, `20_data_audit.py`.

---

# Phase D — Protect and restore the calibration gate

`outputs/tables/null_calibration.csv` currently reads `n_sims_completed,8`,
`ri_draws_per_sim,20`, `VERDICT,UNDETERMINED`. **An 8-sim smoke test overwrote
the 200-sim CALIBRATED artifact** that discharged Gate C §6.3, and
`outputs/tables/` is gitignored, so it is not recoverable. A 200×200 run is in
flight to restore it.

Worse, and separate: **`17_stacked_event_study.py` never reads the calibration
file.** The gate exists only inside the regression suite, so the primary
estimator will run uncalibrated and report p-values without complaint.

- **D1.** Write the artifact only when `n_sims >= MIN_SIMS`, or key it by n and
  have the gate read the largest. A smoke test must not be able to destroy the
  gating evidence.
- **D2.** Make 17 read the calibration and refuse to report an RI p-value when
  the verdict is not CALIBRATED.
- **D3.** Report the corrected-null verdict (rho 0.0482, sigma 0.0390, implied
  total SD 0.0429 against the panel's 0.0428) and record whether Gate C still
  holds after the S8 fix.

---

# Phase E — The four missing deliverables

None of `19_power.py`, `25_zscore_simulation.py`, `30_confirmatory_run.py`,
`docs/PRE_ANALYSIS_NOTE.md` exists. Two designs were produced and **all four
reviewers returned `needs_revision`**, with measured critiques. Those reviews are
input to a rewrite, not code to adopt.

**E1. `19_power.py`.** Must fix, at minimum: the Roth diagnostic converts a joint-
Wald MDE through a mean and is **optimistic by a measured 1.66×** (the fix is one
line, solving for the λ-matched slope); **30.8% of placebo draws land within 7
days of a real episode**, so the RI bracket will not close and the run ends
UNDETERMINED after spending its whole budget; the refactor recipe "delete lines
82-142" of 18 **deletes the lines defining `starts`** (109-111) and 18 dies with
`NameError`; a cross-route gate whose threshold is arithmetically unreachable.
MDE must be on the **effective** episode count — 38 of 75 rebuilt episodes have a
neighbour within ±28 days, which truncates windows and reduces informative N.

**E2. `25_zscore_simulation.py` — rewrite, not revise.** §5.2 of PAPER_MASTER
describes standardising the **regressor** within the analysis window; the design
standardises the **outcome**. It aims at the wrong object. Also: it aborts on its
own defaults (`w < max(FIRST_WEEK_DAYS)+1` is off by one, so L=7 blocks every
run), and `outputs_labelled_simulated` can never pass because it looks for a row
label in the column index.

**E3. `30_confirmatory_run.py`** — written, committed and sealed *before* the
freeze lifts, and dry-run on synthetic confirmation-period outcomes with the real
panel's shape and no real values.

**E4. `docs/PRE_ANALYSIS_NOTE.md`** — reconstructed, clearly labelled as such.

**E5. The `CONFIRMATION_PLAN.md` addendum does not exist**, though
`PAPER_MASTER.md:268`, `:280` and finding F2 all assert it does. Write it, with
the original text byte-identical, listing every deviation: the construct change,
the threshold rule, index composition, the rename correction, the basket
construct rule, F1 and F2, and that the H1 reframe and DID control choice were
made after seeing discovery results.

---

# Phase F — Finish the audit that was cut off

**Workflow 1 completed 12 of 12 diagnoses but only 4 of ~36 refuters.** O2 was
refuted 3/3 and O1 1/1 — both on grounds that the *fix* was defective, not the
observation. **O3, S7, D6, X6, X10, T6, L7, E7, E8 and T13 were never attacked at
all**; their diagnoses stand unrefuted only because nobody tried. Re-run the
refutation phase for those ten with three diverse lenses each.

Also outstanding from the register:

- **S8 is blocking and has no check**, so `M.register_sync` now returns FAIL
  rather than the stale "61/71 … PASS" it last recorded. 11 findings are
  untagged: S8, D6, L7, O1, O2, O3, X10, T6, E7, E8, T13.
- **`AUDIT_FINDINGS.csv` has no status column** — what is fixed is inferable only
  from the suite. Add one, and reconcile all 72 rows.
- **`fit_dose_response` (`event_study.py:159-224`) has no callers anywhere.** The
  D6 dose-response arm is documented and wired into nothing — the exact pattern
  just closed for PPML (X5) and B-HEARD (X6).
- **Stale docstrings asserting the removed rule**: `17_stacked_event_study.py:17-20`
  ("windows are truncated at the next episode's start, and any day belonging to
  more than one episode window is dropped" — both halves false),
  `07_did_exposure.py:12-13`, `GATE_C_MEMO.md:136`, `REBUILD_PLAN.md:376-381`,
  `13_extension_episodes.py:5-9`.
- **`PAPER_MASTER.md:816`** says "One freeze incident" while §5.3 documents two.
- **`run_all.py` wiring**: all seven model stages declare `writes=[]`, so the
  "exited 0 but wrote nothing" guard at `:239-241` is inert for every model;
  stage 17's declared dependency (`confirmation_episodes_rebuilt.csv`) is not the
  file it reads; `10d_parse_cd_demographics.py` and `03b_bridge_legacy.py` are
  not stages although stages depend on their outputs.

---

# ◆ CP1 — Deep audit: everything except the estimate

Adversarial re-audit across all dimensions, ≥3 diverse-lens refuters per finding,
loop-until-dry. Hunt the classes this rebuild keeps finding: checks that pass (or
fail) for the wrong reason; error paths indistinguishable from success; second
sources of truth; silent truncation; **metrics validated on coverage but never on
content** — the class that hid the basket construct defect for the whole project.

**Exit:** 0 unverified findings, 0 blocking open, suite green, audit flags
non-increasing, `31_verify_sources.py` re-run and its log committed.

---

# Phase G — Run discovery (2017–2020)

Freeze stays ON. Fix the mechanical blockers first: `06_heterogeneity.py` needs
`cd_demographics_clean.parquet` (run `10d_parse_cd_demographics.py`, offline, raw
xlsx present); `08_figures.py:60-61` references `mh_narrow_calls`, which does not
exist — the column is `mh_narrow`; Figure 5 depends on a bridge artifact whose
chain is dead at missing legacy Twitter raw files, so it is replaced by the
simulation exhibit (E2) or dropped.

Then 17, 03, 04, 05, 06, 07 — on the **rebuilt** episode list, both arms for
every outcome (OLS on shares *and* PPML on counts with the offset; the 2020
signature reverses in counts), placebo outcomes reported beside the primary.
Rewrite `GATE2_PRELIMINARY_RESULTS.md` and fill `PAPER_MASTER.md §8`, which is
currently empty by design.

# Phase H — Power, and an honest go/no-go

MDE on the effective episode count, per stratum. Roth pre-trend diagnostic with
the corrected conversion. **If power says confirmation cannot deliver, that is
the conclusion**, and the paper becomes a measurement-and-design contribution
with a precisely bounded null. A real ending, not a failure mode.

---

# ◆ CP2 — Pre-freeze audit: the irreversible gate

All must hold **before** `FREEZE_ACTIVE = False`.

- [ ] Every check PASS. No FAIL, no BLOCKED, no ERROR. Baseline refreshed.
- [ ] Calibration passes KS uniformity at ≥1000 sims on the corrected null, and
      17 refuses to run without it.
- [ ] Estimator recovers a planted effect; RI p uses the (1+k)/(1+n) form.
- [ ] `run_all.py` clean twice from cold; manifest committed; model stages
      declare their outputs so the empty-run guard is live.
- [ ] Adding B-HEARD leaves discovery numerically unchanged.
- [ ] Power reports an MDE per stratum; go/no-go recorded.
- [ ] `CONFIRMATION_PLAN.md` addendum committed **first**.
- [ ] `30_confirmatory_run.py` committed and dry-run on synthetic outcomes.
- [ ] Interpretation rules and the multiple-testing correction pre-committed.
- [ ] Basket construct review complete: every included article carries a positive
      law-enforcement signal, or a recorded reason.
- [ ] `PAPER_MASTER.md` current through Phase H.
- [ ] A final adversarial audit of the **specification**, not the code.

**Then, and only then: `FREEZE_ACTIVE = False`.** One commit, greppable.

---

# Phase I — The confirmatory run

| Stratum | Window | Contamination |
|---|---|---|
| **C1 clean** | 2015-07-01→2016-12-31 **and** 2021-01-01→2021-05-31 | none |
| **C2 exposed** | 2021-06-01→2024-12-31 | B-HEARD, degraded Trends precision |

B-HEARD launched 2021-06-01, so Jan–May 2021 is also clean. Its precinct stagger
(exposure 4e-06 to 1.0) is identification in C2, not only nuisance —
pre-specify it as such. Episode counts recompute after the basket rebuild.

Run C1 and C2 together in one sealed execution; report separately and pooled.
Everything is pre-specified, so running all strata at once is not p-hacking — the
one-shot constraint is about changing the specification after seeing results.

**Pre-register two sensitivities:** dropping the July 2016 episode (it contains
Sterling, Castile *and* the Dallas attack, in which five officers were killed —
attention to violence against police plausibly moves EMS demand the other way),
and the broad-basket arm from Phase B. Primary p-value: episode-level
randomization inference, 2000 draws. Freeze results the moment they exist.

# Phase J — Figures, tables, and the paper

Four main-text items: raw series with episodes marked and COVID/B-HEARD dashed;
the event-study plot, day −1 reference; the outcome decomposition forest plot
with placebos visually blocked (**this carries the argument**); Table 1, the
episode list with the frozen-vs-rebuilt diff. Supplement: permutation histogram,
district map, distributed-lag IRF, z-scoring simulation, CAI validation battery,
sensitivity grid.

Drafting order: **Methods → RECORD checklist → Introduction → Limitations →
Results → Discussion → Abstract.** Methods is fully determined already and is
half of a Registered Report. Introduction frames three ways — increase, decrease,
unchanged — so no result disappoints it. Limitations written **before** Results
exist, strongest objection first.

**"What went wrong and how we caught it" is the methods contribution**: the
z-scoring artifact, the rename bug that discarded 93.5% of Alton Sterling's
attention, the scaling defect, the endogenous component, the registry gap, the
basket-construct defect, and the checks that could pass for the wrong reason.
Write it as an asset.

---

# ◆ CP3 — Final audit

Fresh clone reproduces every table and figure via `run_all.py`. Every number
traces to a committed artifact with a `CLAIMS_REGISTER` entry that reproduces it.
Every limitation and every deviation appears in the paper. Adversarial read of
the *paper*: what would a referee attack, and is it answered in the text? COUHES
non-human-subjects determination in writing; OSF deposit with timestamp.

---

## Verification, throughout

- Re-run `31_verify_sources.py` at every checkpoint and before any number enters
  the paper. The log is append-only, so the history of what was verified when —
  **including failures** — is itself part of the record.
- **No number reaches the paper without a `CLAIMS_REGISTER` entry that
  reproduces it.** A number that cannot be regenerated is a check failure.
- **Interpretation is held to the same standard as data.** Every claim about what
  a result *means* names the artifact it rests on and states the alternative it
  does not rule out. Every reversal in this project was an interpretation that
  outran its evidence: the 2020 signature that vanished in counts, "0 of 140
  labels correct" from a check that could not detect the error, and the
  conclusion that the NYC censoring was unresolvable.
- Gate after every change; defeat attempt on every new check; deep adversarial
  audit at CP1, CP2, CP3; audit flag count monotonically non-increasing.
- Nothing touches confirmation outcomes before CP2 clears.

## Honest risks

- **Power may kill the confirmatory run.** Then the conclusion is the bounded
  null plus the measurement contribution.
- **The strict basket may be materially smaller than 120**, which reduces the
  treatment index's signal in exchange for measuring the right construct. The
  broad arm bounds what that trade cost.
- **The index is national.** `trends_nyc` is censored on 26–71% of days by year
  and `wiki_nyc` was rejected, so the locality claim is bounded.
- **2021–2024 is contaminated** by B-HEARD in the hypothesis's own direction, on
  adoption dates that are 17-of-31 low-confidence.
- **A defect found after CP2 cannot be fixed by changing the specification.** It
  gets disclosed and bounded instead. This is the cost of the design and the
  reason CP2 is exhaustive.

---

## Session log — where execution stopped

**2026-09-11 20:51Z.** Phase A part-done:

- **A1 DONE.** Two background retry loops were deadlocked and have been killed
  (PIDs 7082, 8430). Both spun on `pgrep -f "python 26_resolve_basket_scope"`,
  which matches the parent shell whose own command line contains that string, so
  each waited on itself forever. 26 was not running at all. This is the fourth
  incident of this kind; the rule is now in Standing rules above.
- **A2 DONE (module written, callers not yet migrated).** `scripts/wikimedia.py`
  — one paced, cross-process-locked, `Retry-After`-honouring, request-keyed
  client. Callers 11, 24, 26, 28, 29 still hold their own retry blocks and must
  be migrated next.
- **A3/A4/A5 NOT STARTED.**
- **In flight:** `18_null_calibration.py --sims 200 --draws 200` (restoring the
  clobbered Gate C artifact). If it is not running when work resumes, re-run it —
  the current `outputs/tables/null_calibration.csv` reads `n_sims_completed,8`,
  `VERDICT,UNDETERMINED`, and that file is gitignored so it cannot be recovered.

**Wikidata scope state:** `basket_scope.csv` holds 164 rows against 174
candidates; **29 articles have no scope row**, so `27_finalise_basket.py`
correctly refuses to finalise. Those 29 are the immediate work of Phase C.
