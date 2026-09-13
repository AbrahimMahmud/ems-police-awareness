# Plan: from here to the finished paper

## Context

The question is whether public awareness of police violence changes what New
Yorkers ask EMS for. The pipeline that answers it is largely repaired — the
outcome data is whole, the estimator's defects are fixed and verified against a
planted effect, the freeze guard can reject things, the episode construct is a
bounded shock rule.

When this plan was written no analytic estimate existed, and three things blocked
one — each of which turned out to be different from what the code and documents
said it was:

1. **A misdiagnosed network failure.** Not rate limiting on Wikidata but a token
   bucket on the shared client IP, with one client ignoring `Retry-After`.
2. **A treatment index that had never been tested for its construct.** 61 of 120
   articles admitted through a topic category; nothing asked who did the killing.
3. **A destroyed calibration**, overwritten by a smoke test, in a gitignored file.

All three are resolved. The estimates now run, the basket measures police
violence and says so per article, both basket arms exist side by side, and Gate C
is discharged on **all three strata**, each on the scheme its own geometry
requires.

**What this plan is now for.** The blockers are gone, so the remaining work is no
longer repair — it is (a) producing the discovery estimate, (b) establishing
whether the design has the power to say anything on confirmation, and (c) one
measured risk that could still undo the confirmatory path: C1's null may not
survive the sim count CP2 requires. That risk is now the schedule's first item,
because it is cheap to test and expensive to discover late.

This plan runs from here to a finished paper, continuously, with no sign-off
gates. Barriers get resolved, not deferred. **The endpoint is a conclusion**: a
confirmatory result on data never examined, or an explicit, evidenced finding
that the design cannot deliver one. Both are publishable; neither is a failure.

---

## Status (2026-09-13 ~08:20Z) — fresh container, CP1 remediation committed, C1 certified

**Read this block first; everything below it under "Status (2026-09-12…)" is the
historical record of the previous session and is kept for its reasoning.**

| | |
|---|---|
| Branch | `analysis-rework`; commits `34211cc`…`HEAD` on top of the handoff's `e541632` |
| Environment | **A fresh container.** No `data/processed`, no `outputs/tables`, no scratchpad survived. Everything regenerable was regenerated from committed inputs: the EMS extract re-downloaded with an unchanged provenance hash (S1b), the panel and both basket arms byte-identical, discovery re-calibrated (CALIBRATED, rejection 0.05, lattice KS p 0.7516). |
| Environment, the rule | **Compute advances only while a session is active.** The container is suspended or reset when the session is idle (a 4-hour usage-limit pause advanced the ledger by zero rows; it came back with `up 1 min` and an empty process table). Every long job is checkpointed and driven by the runners in `ops/`, which are relaunched blind after any restart. Poll by PID file, never `pgrep -f`. |
| Decisions (user, 2026-09-13) | **Continue to Phase I** as pre-registered, with the reading of a non-rejection fixed against the measured power (addendum §19). Branch stays `analysis-rework`, no attribution. **O2 diagnostic: disclosed first, then run** as a declared access (addendum §18; done). Deliverable: a Markdown manuscript in the repo. |
| CP1 | **Done as an adversarial audit** (8 finders by failure class, 3-lens refutation where the usage limit allowed): 60 raw findings, of which the confirmed and self-verified ones are filed as O2-close, X16, N7–N10, X17, P8–P10 and the pending items in remediation groups A–E below. |
| Gate | 80 checks: 77 PASS, 1 BLOCKED, 2 FAIL, run twice with identical results. Every non-PASS is artifact-pending in this container: `S.ri_scheme_certified` BLOCKED until C2's certificate regenerates (C1's landed 08:08Z and satisfies it), `V.claims_reproduce` (26 of 128 absent, 4 reading the 2-draw smoke estimator until the 500-draw run lands) and `M.status_honest` (X14, tagged to it). `main()` reports an unbaselined check as a failing condition; the baseline covers every check. |
| Findings | 102: 99 fixed, 0 open, 3 unverified (P1, P5, RI3). **C1 certified 2026-09-13** under `circular_within_block`, 200 × 200: rejection 0.04, KS D 0.083, lattice p 0.1229, median p 0.4776, CALIBRATED — but their check covers both confirmation strata, so they stay unverified until C2's certificate regenerates here and the check passes. |
| Claims | 128 registered. C1's §7.4 row and prose are re-registered as C65, C66, C128–C131 and verify. Claims on regenerated artifacts (the C2 rows, §8 p-values, decomposition, power) re-establish as the chain writes them and are read from the artifact, never "fixed" to the old numbers. |

### What the CP1 audit found that changes Phase I

- **The sealed confirmatory script drew C1's null with the seam-crossing shift** that RI3 replaced in `event_study`, kept its own copy of the estimator, selected episodes by a second rule, was not checkpointed, and would have crashed after all estimation on a stale dictionary key. It now calls the certified machinery (`randomization_p`, `draw_scheme_for`, `stratum_episodes`) with per-cell identity-keyed ledgers and optional cell parallelism; the retired helpers are gone; addendum §21 discloses the within-block scheme the record had never described. `S.confirmatory_uses_certified_machinery` holds it.
- **Checkpoint ledgers were keyed on filenames.** Both now carry a design fingerprint; a ledger from another design is quarantined, never pooled (N7). Failed sims are recorded, not dropped (N8).
- **B-HEARD was attached to 17's panel and absent from its formula** (X17); the estimator takes covariates in one place now.
- **The freeze had undisclosed reads**: the O2 register row held record-level 2015–16 numbers from the 2026-09-09 refutation (disclosed as F3, addendum §15); two claim expressions averaged over the buffered panel's confirmation rows; the source verifier loaded whole outcome parquets; 00b printed per-year missing-district rates. All closed: the claims verifier filters every outcome artifact to the discovery window before eval, `realised()` reads footers only, 00b prints counts, 22 selects the sample, and the guard checks are AST-based.
- **Power was computed on the wrong C1 calendar** (2015-01-01 rather than 2015-07-01; 181 extra days). 19 now takes its calendar from `CONFIRMATION_ANALYSIS_WINDOWS` with assertions; the re-run is the last step of the rebuild chain, and C100–C102 are re-registered if they move.

### Remediation groups (tracked in the session, mirrored here)

- **A — freeze exposures: done.** F3 disclosed (addendum §15, PAPER_MASTER §5.3, register row tagged to `D.incident_disclosed`, which now names every F-finding); `check_claim` filters outcome artifacts to the discovery window before eval; footer-only `realised()`; 00b prints counts only; 22's `check_episodes` uses `select_sample`; `ems_pages` is a raw outcome directory for coverage; `D.guard_coverage`, `D.soda_guarded`, `S.calibration_can_fail`, `X.bheard_wired` and `D.declared_access_scoped` are AST-based.
- **B — confirmatory script: done** (`S.confirmatory_uses_certified_machinery`; synthetic dry run 105 rows, exit 0, sidecar stamped).
- **C — ledger identity: done** (`S.ledger_identity`).
- **D — gate integrity: part done.** Done: unbaselined/retired checks fail `main()`; a template without exactly one `{}` is `malformed`; `M.status_honest` first-run BLOCKED; `V.sources_verified` compares hashes not mtimes; arm suffixes collapse over `config.ARMS`. Remaining: cell-level exhibit coverage incl. unit/arrow cells; U+2212 in `_template_regex`/`NUMBER_RE`; templates embedding sibling values; register `checks` column vs CHECKS tags and severity vocabulary; `source_register.json` vs `data_sources.csv` ids and `check_artifact` 'verified' with no row; run_all stale-output PASS; 19's early-exit bypass of no-downgrade; `X.run_all_stages_declared` regex; `E.episodes_labelled` tautology; duplicate constants; 09 clobbering `wikipedia_article_resolution.csv`; `fetch_leads` truncation materiality; non-parquet legacy files in `data/processed`.
- **E — documents: done** except the numbers that the chain regenerates (§7.4 C2 row, §7.5b power, §8 p-values), which re-establish from artifacts.
- **L7 spliced arm: done** (addendum §20; 11 → 12 → 13 under `--arm spliced`; identical on all 1,764 pre-break days, differs on 1,708 of 1,708 post-break days, `T.spliced_arm_prebreak_identical`; §5.1a; C122–C127).
- **Rebuild chain (ops/rebuild.sh), in flight:** 500-draw discovery estimator → 05, 03, 04, 06, 07, 08, 33 → C2 calibration → 19 power; then `ops/calib1000.sh` (1000 sims × 3 strata). Progress: `wc -l outputs/tables/ri_ledger_*.csv`, `outputs/tables/null_calibration_ledger_d200_C2.csv`.
- **Then CP2** (checklist below, plus: 1000-sim certificates on all three strata; planted-effect recovery; run_all clean twice from cold; B-HEARD inert; final adversarial audit of the specification) → `FREEZE_ACTIVE = False` in one commit → **Phase I** → **Phase J** (`docs/PAPER.md`).

## Status as of 2026-09-12 16:15Z — Phases A–E done, F part-done, all three strata calibrated (historical)

*Phases A–E below are the record of work already completed, kept for the
reasoning rather than as a to-do list. The live work is Phase F's seven
unverified findings, then G, H and CP2.*

**Tree clean at `0957a3a`, pushed to `analysis-rework`.**

| | |
|---|---|
| Checks | **65: 65 pass** once re-baselined (the last BLOCKED check now passes — verified directly) |
| Claims | 55 reproducing, **but 6 numbers in §4.1 are unregistered** (see below) |
| Findings | 82: **73 fixed, 1 open, 8 unverified** |
| Background jobs | none — the 3-stratum calibration finished 08:19Z |

**Gate C is discharged on all three strata**, each on the scheme its geometry
requires, 200 sims × 200 draws:

| stratum | scheme | geometry | episodes | rejection | KS p | verdict |
|---|---|---|---|---|---|---|
| discovery | anchor_shift | contiguous | 29 | 0.06 | 0.680 | CALIBRATED |
| C2 | anchor_shift | contiguous | 30 | 0.06 | 0.450 | CALIBRATED |
| **C1** | **circular** | **gapped** | 15 | 0.05 | **0.074** | CALIBRATED |

`S.ri_scheme_certified` evaluates to PASS on these artifacts, so the suite is
65/65 after a re-run and baseline refresh, and P1 and P5 can move to `fixed`.

### ⚠⚠ SUPERSEDED — do NOT re-run C1 at 1000 sims yet (20:05Z)

The section below said to recheck C1 at 1000 simulations. **That run was started,
was killed by a container restart at ~45 minutes having written nothing, and
should not simply be restarted** — because investigating the restart turned up
the reason C1's null is non-uniform, and it is not sample size.

**C1's circular-shift null does not reproduce C1's own design.** The real
stratum has **10 episodes in the 2015–16 block and 5 in the 2021 block**. The
circular scheme concatenates the admissible days of both blocks and shifts
through them, so the split it produces is whatever a uniform shift implies:
block 1 is 520 of 641 admissible days (81%), so the null puts a mean of **12.1**
episodes there, its modal draw is 13 (42.7% of draws), and it reproduces the
real 10/5 split **only 12.4% of the time**. The placebo designs differ
structurally from the design being tested — different episodes per block,
different effective sample, different fixed-effect structure — which is a
textbook source of non-uniform p-values and explains D ≈ 0.09 without appealing
to anything else.

**The fix is a within-block circular shift**: draw one shift per block and wrap
inside it. The 10/5 split is then preserved on every draw, clustering inside
each block survives, and the seam disappears. Feasibility checked: 520 × 121 =
**62,920 distinct placebo designs**, against 2,000 draws needed. This is a
further deviation from the pre-registered null and gets disclosed as one — but
the alternative is a null that is not a null of this design, which is not
defensible.

Two more defects were found in the same look, both of which the 1000-sim run
would have inherited:

**The randomization p-value uses the wrong formula.** `event_study.py:618` is
`(stats_ >= obs).mean()` — that is `k/n`. CP2's own checklist requires
`(1+k)/(1+n)`, and the artifacts show why: **p = 0 appears in all three strata**,
and zero is not a valid p-value. The form is anti-conservative exactly where
rejection decisions are made. Measured correction on the existing artifacts:
C1's KS p moves 0.0736 → 0.0881, discovery 0.6803 → 0.7718, C2 0.4502 → 0.4747.
Real, required, and **not enough to rescue C1** — its D only moves 0.0900 →
0.0875.

**The uniformity test ignores the lattice its own comment tells it to respect.**
`18_null_calibration.py:269-272` says "the randomization p-values are discrete on
a grid of 1/draws, so compare against that lattice rather than a continuous
uniform, which would reject purely on granularity" — and the next line calls
`stats.kstest(pvals, "uniform")`, the continuous uniform. A comment describing a
fix that was never made. Measured: on a *perfectly* calibrated lattice null the
false-failure rate of `ks_p > 0.05` is 5.3% at 200 sims and **6.7% at 1000**.
Small, real, and it grows with exactly the sim count CP2 demands.

Granularity is therefore **not** C1's problem: a perfect null on this lattice has
median D 0.0276 at 1000 sims and a 95th percentile of 0.0448, while C1 sits at
0.0875 — roughly three times the median and well past the tail.

**Revised order: fix all three, then calibrate once.** Re-running 1000 sims under
the current scheme would spend five hours confirming a null we already have a
mechanistic reason to reject.

### ⚠ The original finding (still true, now explained)

**C1 passed uniformity by 0.006 and will probably fail at 1000 sims.** Its KS
statistic is D = 0.0900 against a critical value of 0.0960 at n=200. CP2 requires
≥1000 sims, where the critical value is **0.0429 — less than half the observed
D**. The p-values also tilt the wrong way: mean 0.457, median 0.4275, and 13.5%
below 0.10 against a nominal 10%. So the circular-shift null is mildly
**anti-conservative**, and the α=0.05 rate test passes only because 0.05 is the
one α it checks.

C1 is the clean stratum — the one the whole discovery/confirmation split exists
to obtain — and `circular` is the new scheme written for it this session. If its
D is near its point estimate, C1 fails CP2 and the scheme needs rework.

**Decided, and then overtaken by what the run revealed** — see the superseded
block above. The instinct was right: it was cheap to test and expensive to
discover late, and testing it early is exactly what surfaced the scheme defect.

**The environment will not hold a long job.** This is now measured rather than
feared: the run died at ~45 minutes to a container restart, having written
nothing, because `18_null_calibration.py` only writes at the end. CP2 needs 1000
sims on three strata, ~18 h of compute, in a container that restarts.

So the calibration has to become **resumable**, and the existing seeding makes
that nearly free: `SEEDS = np.random.SeedSequence(18_20260908).spawn(args.sims)`
means sim *i* always gets the same seed regardless of how many sims a run asks
for — **the first 200 seeds of a 1000-sim run are exactly the 200 already
computed**. Persist each finished sim as `(index, obs, p)` to a sidecar, skip
indices already present on startup, and a 1000-sim calibration becomes any number
of short runs that survive restarts, with the 200 sims already spent on each
stratum carried over rather than thrown away.

**Phase A done.** The blockage was never rate limiting — Wikimedia runs a token
bucket on the *client IP shared across hosts*, and `26` was the only client
ignoring `Retry-After`, with a cache key that embedded the batch size. The action
API resolved all 174 candidates in one request and exposed three defects (N1–N3)
that had been changing basket membership; twelve articles had carried a false
exclusion reason.

**Phase B done.** The treatment index had never been tested for its construct:
half the basket entered via the topic category "Black Lives Matter", and nothing
asked who did the killing. Nine civilian killings and the Dallas gunman were in
it. Strict basket **109**, broad **118**, anti-police in neither — and removing
the anti-police articles leaves 2016-07-08 the top day either way (12.5693 vs
13.1356, rank 1 both).

**Phase C done.** Walter Scott recovered at rank 15 of 107, 0 duplicate people, 0
failed title fetches, 74 episodes. The whole basket build reproduces
**byte-identically** on a second run against live APIs.

**Phase D done.** Gate C discharged on the adopted 29-episode geometry:
CALIBRATED, rejection 0.06, KS p 0.680.

**Phase E done.** All four deliverables written, reviewed and gated —
`19_power.py`, `25_zscore_simulation.py`, `30_confirmatory_run.py`,
`docs/PRE_ANALYSIS_NOTE.md`, plus the `CONFIRMATION_PLAN.md` addendum (16
deviations). The freeze seal was tested adversarially and holds.

**Phase F mostly done.** `config`'s promise made real, three lying docstrings
corrected, the dose arm wired, `run_all` stages declared, the findings register
given a falsifiable status column.

### What the last commit found (`0957a3a`) — three defects, one self-inflicted

The broad arm built cleanly (correlation 0.9975 with strict, 71 shared episode
starts, both ranking 2016-07-08 first). Committing it surfaced three defects in
the same family — a register or guard that answers a question about one object
and licenses a write to another:

- **P3.** `basket_artifact()` gave the broad arm its own files; nothing gave it
  its own source ids. So `log_source` read the broad series and episode list as
  new versions of the strict ones and superseded them, leaving the **primary
  arm with no provenance row at all**. `V.artifacts_current` passed throughout —
  it verifies the script behind every row present and cannot ask about a row
  that stopped existing. Fixed with `config.basket_source_id()` and
  `V.source_id_per_artifact`.
- **P4.** The append-only history that would have shown P3 immediately **could
  not be parsed**: written with `header=not exists()`, its header froze at 7
  columns while later rows carried 9. Nothing in the repo read it. Repaired in
  place; 41 rows across 11 ids now parse.
- **P5.** `S.ri_scheme_certified` read the `draw_scheme` label and never the
  verdict, so a 2-sim `UNDETERMINED` C1 diagnostic **would have flipped the gate
  on the confirmatory path to PASS**. That same 2-sim run had already overwritten
  discovery's 200-sim p-value list (5,450 → 61 bytes), because the "don't
  publish a smaller run" rule covered the verdict file and nothing beside it.
- **Self-inflicted, caught by launching it:** `12_build_cai.py` inferred which
  components the basket determines from whatever the arm's file happened to
  contain. Re-running `11` for the broad arm without `--only wiki_ext` refetches
  GDELT, and any drift since the strict fetch would have entered the comparison
  **as a basket effect**. Now declared in `config.BASKET_DEPENDENT_COMPONENTS`.

### ⚠⚠⚠ The environment restarts every 30–70 minutes, and that now governs everything (21:15Z)

Three restarts observed this session, each confirmed by `uptime` reading `up 0
min`. Two of them destroyed long jobs that had written nothing:

| killed | job | elapsed | saved |
|---|---|---|---|
| ~20:02Z | C1 calibration, 1000 sims | ~45 min | nothing |
| ~21:15Z | Phase G, `17_stacked_event_study.py` | ~33 min | nothing |

`18_null_calibration.py` was made resumable in `89e1937` and survives this —
its ledger carried 51 C1 sims through the 20:02Z restart untouched.
**`17_stacked_event_study.py` was not, and Phase G cannot ever finish**: it needs
~1.7 h at 1000 draws and the longest observed uptime is ~70 minutes.

This is no longer an annoyance to work around. It is a hard constraint on what
this project can compute at all, and every remaining compute-bound deliverable —
Phase G, the 1000-sim calibrations CP2 demands, Phase H's power simulation —
sits on the wrong side of it.

**N6. Make `randomization_p` resumable, the same way and for the same reasons.**
17 holds a single `rng` and draws in a sequential loop (`17:103`, `17:203`,
`17:216`), so a resumed run cannot reproduce an interrupted one. The fix is the
one already proven in 18: per-draw seeds from a `SeedSequence`, so draw *i*
always gets the same seed however many draws a run requests, plus a ledger keyed
by draw index that is flushed per draw. That buys two things at once — the run
survives a restart, and the result stops depending on worker completion order,
which is the property 18's seeding was introduced to give.

Scope it to `event_study.randomization_p` so 17 and 30 both inherit it; 30 draws
its own placebos on the sealed path and needs it just as much, since the
confirmatory run is the longest job in the project.

**Verify the same way 18 was verified**: run N draws, truncate the ledger to a
third of them, restart, and require the completed ledger to be *exactly equal* to
the uninterrupted one. That test is what proved 18's version and it is the only
thing that distinguishes real resumability from a cache that quietly changes the
answer.

### Immediate next steps, in order (revised 20:05Z, superseded above)

Items 1–6 below are **done and pushed** (commits `0957a3a` … `f1fa360`): all
three strata calibrated at 200 sims, P1/P5 closed, the broad arm's six numbers
and the per-stratum calibration numbers registered, `V.claims_cover_exhibits`
added, and the estimators gated on their own null. Phase F then closed T13, E7
and E8 by attacking them. **69 checks pass, 72 claims reproduce, every blocking
finding is fixed, four unverified moderate findings remain.**

The live queue is now:

**N1. Fix the randomization p-value form.** `event_study.py:618` →
`(1 + (stats_ >= obs).sum()) / (1 + len(stats_))`. It is on CP2's checklist, it
is the difference between a valid permutation test and an invalid one, and p = 0
currently appears in every stratum's artifact. Touches every RI p-value in the
project, so it lands first and alone, with the three strata re-derived from the
stored placebo counts to show exactly what moved.

**N2. Make the KS uniformity test respect the lattice**, as its own comment has
always said it should. Compare against the discrete `(1+k)/(1+draws)`
distribution rather than a continuous uniform. Defeat attempt: a perfectly
calibrated lattice null must fail at ≈5%, not 6.7%.

**N3. Replace C1's scheme with a within-block circular shift** and make
`draw_scheme_for` name it, so `S.ri_scheme_certified` requires a calibration that
certifies *it* rather than the seam-crossing version. Verify the 10/5 split is
preserved on every draw, and that the discovery and C2 schemes are untouched —
they are single-block and must be numerically identical before and after.

**N4. Make `18_null_calibration.py` resumable**, per the sidecar design above.
Without it CP2's 1000-sim requirement is unreachable in this environment.

**N5. Then calibrate, once**, at 1000 sims across all three strata, in restart-
surviving chunks. Only after N1–N4, so the run measures the design rather than
the defects.

### Order of work from 21:15Z

N1–N5 are **done and pushed** (`f970f4a`, `90b7abf`, `89e1937`), as are L7, T6
and O3 (`9624544`, `e07f02c`, `21a4653`). **74 checks: 73 pass, 1 BLOCKED**
(C1's recalibration, honestly pending), 77 claims reproduce, audit 42/2. Every
finding is closed except **O2**, which is deliberately untouched: closing it
means reading 2015–16 confirmation outcome data, and that is the user's decision,
not mine.

1. **N6, resumable randomization inference** — above. Nothing compute-bound can
   finish until this exists, so it comes before the thing it unblocks.
2. **Phase G, the discovery run**, at 1000 draws on both H1 outcomes, then 03–08.
   Restart-surviving once N6 lands. This is the first analytic estimate the
   project will have produced.
3. **Write `PAPER_MASTER` §8**, which is empty by design, from the artifacts.
   Both arms — OLS on shares *and* PPML on counts, because the 2020 signature is
   known to reverse in counts — with placebo outcomes reported beside the
   primary, every number registered as a claim, and the draw count stated.
   **Discovery is exploratory**: nothing here confirms or refutes H1, and each
   reading names the alternative it does not rule out.
4. **Restart the C1 calibration** (resumable, 51 of 1000 banked).

Left for the user, not attempted: **O2**'s freeze-policy decision, and lifting
`FREEZE_ACTIVE`.

### The original list, for the record

1. **Start the C1 1000-sim calibration in the background** (decided above). It is
   the long pole and everything else runs alongside it.
2. **Re-run the suite, refresh the baseline, close P1 and P5.** Both are tagged
   to `S.ri_scheme_certified`, which now passes on real 200-sim artifacts. P5 is
   currently recorded `unverified` precisely because a BLOCKED check is not
   evidence of a fix; that condition is now met.
3. **Register the broad arm's six numbers.** §4.1 states 118 articles, 75
   episodes, correlation 0.9975, mean |diff| 0.051 SD, 71 shared starts and a
   2.79 SD maximum gap — **none of them in `CLAIMS_REGISTER.csv`**, against this
   project's own standing rule that no number reaches the paper unregistered. I
   introduced this in the last commit.
4. **Write the per-stratum calibration into `PAPER_MASTER` §7.4** with claims for
   C1 and C2 (only discovery's four numbers are registered today), and state
   C1's marginal uniformity in the text rather than leaving it in an artifact.
5. **Close the "unregistered number" gap structurally.** Nothing asserts that
   every number in the paper *is* registered — `V.claims_reproduce` only checks
   the ones that are, which is how item 3 happened silently. Add
   `V.claims_cover_exhibits` over a bounded, low-noise region: **numeric cells in
   markdown tables**, which is where exhibit values live, plus an explicit
   allowlist carrying a reason per exemption. Scope it tightly — a check that
   flags every numeral in prose is one people stop reading, and this project has
   already learned that lesson twice.
6. **Gate `17_stacked_event_study.py` on the calibration.** It is the estimator
   Phase G runs and it **does not read `null_calibration.csv` at all** (only 18,
   19, 23, 25 and 30 do). Discovery is calibrated, so the numbers would be sound
   today — but the gate is documented and wired into nothing, which is the exact
   pattern already closed for PPML, B-HEARD and the dose arm.

### Two process failures, recorded

`git add -A` swept three unreviewed subagent files into `dc79a21` under an
unrelated message, and `git add docs/` did it again with the pre-analysis note.
Both are corrected in the history and all four files have since been reviewed.
**Stage named paths, never directories, while anything else is writing.**

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

**The container is suspended or reset whenever the session is idle, and every
process dies with it.** Compute advances only while a session is active; the
filesystem survives. Anything long is checkpointed and driven by the runners in
`ops/`, which skip completed steps and resume ledgers when relaunched blind.

**Background jobs are polled by PID file or sentinel file, never `pgrep -f`.**
A `pgrep -f` pattern matches the shell whose command line contains it, so a
waiter waits on itself. This has cost four incidents.

**Constraints:** all work on `analysis-rework` (the session's designated
`claude/...` branch is not used — the standing instruction is this branch and no
other). No Claude attribution in any commit, document, or artifact — including
commit trailers. `data/reference/confirmation_episodes.csv` stays byte-identical
to HEAD.

**This plan has a durable copy in the repo at `docs/EXECUTION_PLAN.md`**, last
written 03:56Z and now stale. The scratch plan file does not survive the
container, so every update here must be mirrored there, in the same commit as
the work it describes. Its "Session log — where execution stopped" section is
the handoff record.

**The 10-minute update chain has lapsed.** A check-in queued at 05:00Z was
delivered ~11 h late and `list_triggers` shows nothing enabled, so the
self-re-arming chain broke when the session was interrupted. Re-arm it on
resuming, and re-arm it again on *every* firing — recurring routines are capped
at hourly here, so the 10-minute cadence exists only as a one-shot that
rebuilds itself.

---

## Decisions taken (recorded, with reasoning)

| Decision | Call | Reason |
|---|---|---|
| **Basket construct** | **Strict primary** (verified law-enforcement killings) **+ broad basket as a pre-registered sensitivity** | Confirmed with the user. Lets the paper say the result does not depend on where the line was drawn, instead of asserting it. |
| **Attention to violence *against* police** (Micah Xavier Johnson, Gonzalo Lopez) | **Exclude from every basket, and disclose**, including what removing them does to the 2016-07-08 index peak | Confirmed with the user. It is the opposite construct, and it currently sits on the index's headline validation day. |
| **Minimum effect of interest** | **−0.005 — half a percentage point of mental-health call share** | Confirmed with the user. Against a discovery baseline of 0.1083 (SD 0.0467) that is **4.6% relative, 0.11 SD**. Chosen deliberately as neither of the two numbers the project had named: not the −0.010 planted to test the estimator, and not GATE2's −0.00108, because setting the bar from a result already seen is circular. Power is now judged against a standard set independently of the results, and Phase H is unblocked. |
| **C1 uniformity recheck** | **Run C1 at 1000 sims immediately, in the background** | Confirmed with the user. It passed at 200 sims by 0.006 in D and the 1000-sim critical value is less than half the observed D, so this is the most likely single point of failure at CP2 — and it is the cheapest stratum to recheck. |
| **Episode list the estimators consume** | The **rebuilt** list (`confirmation_episodes_rebuilt.csv`); frozen file stays untouched as an artifact; the diff is a disclosed deviation | **Implemented and verified 16:20Z.** `config.EPISODE_LIST_PRIMARY` names the rebuilt file and 17, 07, 08 and 18 all read it through that constant. Earlier plan text saying this was "never implemented" was stale. |
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

Seven findings are still `unverified` — **L7, O2, O3, T6, E7, E8, T13** — which
in this register means nothing checks them, not that they are fine. All are
`moderate`, so `M.register_sync` (which only requires checks on `blocking`) does
not force the issue; the plan does.

Read in full, they are **not one kind of thing**, and treating them as one queue
is how they have stayed open. Three are limitations, two are runnable
treatment-side robustness fetches, one needs an external document, and one needs
a freeze-policy decision:

| | kind | side | what closing it takes |
|---|---|---|---|
| **E7** | limitation | episodes | Confirm `ATTRIBUTION_LOOKBACK_DAYS = 60` and write the limitation: episodes triggered by a video release, indictment or verdict rather than by a death cannot be attributed from the registry at all. The fix text already concludes "keep 60 — it is a guard". Cheap. |
| **E8** | limitation | episodes | Report the 2020 episodes as Floyd and Blake, note Prude falls inside the Blake window rather than carrying his own, and optionally add a p85 sensitivity arm where Prude clears the bar alone. Do **not** tune the separation parameter around it. |
| **T13** | probably stale | treatment | Exact-name matching marked 25 basket articles absent from a registry containing them. The basket has been rebuilt since this was filed, and registry membership is corroboration only, never a gate (T9) — so **first measure whether it is still live** before writing normalised name matching. If the impact is confined to audit coverage stats, say so and close it. |
| **L7** | real defect | treatment | **The most consequential of the seven.** Wikipedia's `agent=user` filter changed meaning in April 2020, non-retroactively — so `wiki_ext`'s measurement regime changes **five weeks before 2020-05-26**, the single most influential episode in the study (dropping it alone moves the coefficient 25%). Refetch the decade under `agent=all-agents` as a robustness series, report the correlation and the by-period ratio, and state the break in Methods with the WMF citation. Treatment-side, blind-safe, runnable now. |
| **T6** | real defect | treatment | Trends quantization precision degrades ~5× over the decade, so attenuation is year-specific and a 2021–2024 null is not interpretable as an absence. Needs a refetch on a payload that stays off the floor (11 uses four phrases, 11b uses one literal string — they disagree), plus a per-year signal-to-quantization diagnostic. Treatment-side but the slowest and most fragile item here, since pytrends is rate-limited and non-deterministic. |
| **O3** | needs a document | outcome | EDPM is born on the exact day B-HEARD launches and T-EDP inside the largest discovery episode. Requires FDNY documentation on what EDPM denotes. The cheap half is independent: replace `config.py:57-59`'s comment with the actual annual family totals, and report T-EDP separately (≈0.2% of the family, so exclusion is cheap). |
| **O2** | **needs a freeze decision** | outcome | Two hard breaks sit **inside the 2015–2016 confirmation window**: geocoding completeness triples on 2016-01-01 and INJALS is retired. The fix is a QC break table — per call code first/last date and month-over-month step, per year the missing-district rate — and that table reads confirmation-window outcome data. See below. |

### The O2 question, which must be settled before CP2

CP2 cannot be discharged without knowing whether the confirmation sample has
structural breaks in it, and finding out means running a coverage diagnostic over
2015–2016 outcome data that the freeze protects. **These are not the same kind of
access** — a per-code first/last-date and missingness table reports nothing about
the outcome's relationship to treatment, and it is exactly the check that would
stop the confirmatory run from being estimated across a discontinuity nobody
knew about. But "it's only metadata" is precisely the reasoning that produced
freeze incidents F1 and F2, so it does not get to be an assumption.

**Proposal:** permit it, narrowly and on the record — routed through
`select_sample` with an explicit named exemption, emitting only counts, dates and
missingness rates and never an outcome mean by period or treatment, committed as
a disclosed deviation in the `CONFIRMATION_PLAN.md` addendum before it is run.
If that is not acceptable, the alternative is to exclude every episode whose
window crosses 2016-01-01 unconditionally and lose the pre-2016 half of C1 — a
real cost to the clean stratum, chosen blind.

**This is a decision to take before CP2, not now.** Nothing else in the plan
depends on it.

### The rest of Phase F

Re-run the refutation phase for the findings never attacked — three diverse
lenses each, plus the two missing lenses on O3. Their diagnoses stand unrefuted
only because nobody tried, and **every diagnosis that *was* attacked fell**.

**Close the two defects the refuters found** (detailed under *Status at resume*):
register `ems_cd_day_calltype_excluded.parquet` in `config.OUTCOME_ARTIFACTS`,
`run_all.py:90`'s `writes`, and `DATA_PROVENANCE.md`; then make the guard
enumerate `data/processed/*.parquet` against that list so `config.py:71-82`'s
promise is one a check actually keeps — with a defeat attempt that drops a new
outcome file in and confirms the suite fails. Add a `drop_reason` column (or
correct the misleading comment at `00b:138`), lift the disposition list into a
single `config.EXCLUDED_DISPOSITIONS`, and bring `00_local_ems_extract.py` back
into step with `00b`.

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
- **`run_all.py` wiring — DONE, verified 16:20Z.** All seven model stages now
  declare non-empty `writes`, so the "exited 0 but wrote nothing" guard is live
  for every model, and stage 17 `needs` the rebuilt episode list it actually
  reads. Remaining: `10d_parse_cd_demographics.py` and `03b_bridge_legacy.py`
  are still not stages although stages depend on their outputs.

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

Freeze stays ON. Two prerequisites, the first newly found and the more important:

**G0. `17_stacked_event_study.py` must gate on the calibration.** It does not
read `outputs/tables/null_calibration.csv` at all — only 18, 19, 23, 25 and 30
do. So the primary estimator will report randomization-inference p-values
without ever checking that the null producing them is certified. Discovery *is*
CALIBRATED, so today's numbers would be sound; the defect is that nothing
enforces it, which is the same "documented and wired into nothing" pattern
already closed for PPML (X5), B-HEARD (X6) and the dose arm (D6). 17 must read
the artifact for the stratum it is estimating and refuse to emit an RI p-value
unless that stratum's verdict is CALIBRATED. Needs a defeat attempt: point it at
an UNDETERMINED artifact and confirm it refuses.

**G1. Mechanical blockers — checked, all clear.** `cd_demographics_clean.parquet`
exists (10.8 KB), so `06_heterogeneity.py` is unblocked. `08_figures.py:61`'s bad
`mh_narrow_calls` reference is corrected (the surviving mention is the comment
explaining it), and Figure 5 now skips cleanly when
`bridge_legacy_to_primary.csv` is absent — which it is, since the legacy Twitter
raw files are genuinely not on disk. 08 also calls `select_sample`, so the
figures are inside the freeze.

**G2. Nothing runs the figures.** `08_figures.py:63-64` records that its Figure 1
had been raising `KeyError` on its first statement, so **08 had never produced
anything**, "and the suite never caught it because no check runs the figures."
That is the same class as the `20_data_audit.py` incident — a gate command that
was itself broken while being recorded as satisfied. Phase G running 08 is the
proof it works once; a check that asserts each declared figure file exists and
post-dates its script is what keeps it working. Cheap, and it closes a hole the
code itself has already documented.

Then 17, 03, 04, 05, 06, 07 — on the **rebuilt** episode list, both arms for
every outcome (OLS on shares *and* PPML on counts with the offset; the 2020
signature reverses in counts), placebo outcomes reported beside the primary.
Rewrite `GATE2_PRELIMINARY_RESULTS.md` and fill `PAPER_MASTER.md §8`, which is
currently empty by design.

# Phase H — Power, and an honest go/no-go

**Unblocked.** The minimum effect of interest is **−0.005** (half a percentage
point of mental-health call share; 4.6% relative, 0.11 SD against a discovery
baseline of 0.1083, SD 0.0467). Write it into `config`, `PAPER_MASTER` §7.5b and
`PRE_ANALYSIS_NOTE.md` as a pre-specified constant, and delete the "reports
against both numbers the project has ever named" fallback from §7.5b — that
paragraph exists only because no MEI had been chosen, and it now overstates the
ambiguity.

Then: MDE on the **effective** episode count, per stratum, against −0.005. Roth
pre-trend diagnostic with the corrected λ-matched conversion (the mean-based one
is optimistic by a measured 1.66×). Report the MDE-to-MEI ratio per stratum as
the go/no-go statistic, and record it in the claims register.

Two things already measured that constrain what this can conclude:
- The first-week statistic loses almost nothing to episode clustering — **2
  episode-days of 592** across all three strata. The loss lands in the
  pre-period, 9–15% of it, so clustering costs *credibility* (the pre-trend
  test) rather than precision.
- C1 carries 15 episodes against C2's 30 and discovery's 29, so the clean
  stratum is the least powered one — and, per the status section, also the one
  whose null is least certain.

**If power says confirmation cannot deliver against −0.005, that is the
conclusion**, and the paper becomes a measurement-and-design contribution with a
precisely bounded null. A real ending, not a failure mode.

---

# ◆ CP2 — Pre-freeze audit: the irreversible gate

All must hold **before** `FREEZE_ACTIVE = False`.

- [ ] Every check PASS. No FAIL, no BLOCKED, no ERROR. Baseline refreshed.
- [ ] Calibration passes KS uniformity at ≥1000 sims **on all three strata**,
      against the **lattice** rather than a continuous uniform, after C1's scheme
      is replaced with the within-block shift. Requires the resumable
      calibration (N4) to be reachable at all in this environment.
- [ ] Estimator recovers a planted effect; **RI p uses the (1+k)/(1+n) form** —
      currently it does not, and p = 0 appears in every stratum's artifact.
- [x] 17 refuses to report an RI p-value on an uncalibrated null, per stratum,
      and a cheap run cannot overwrite an expensive result *(done, `5fd53f3`)*.
- [ ] `run_all.py` clean twice from cold; manifest committed; model stages
      declare their outputs so the empty-run guard is live.
- [ ] Adding B-HEARD leaves discovery numerically unchanged.
- [ ] Power reports an MDE per stratum against the MEI of **−0.005**; the
      MDE-to-MEI ratio and the go/no-go are recorded as claims.
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
  **This rule was enforced by nothing until now**, and it was broken in
  `0957a3a`: six numbers entered §4.1 unregistered. `V.claims_reproduce` only
  verifies claims that *are* registered, so the coverage side was invisible —
  the same "validated on coverage, never on content" inversion that hid the
  basket construct defect, running the other way. Closing it is item 5 of the
  immediate steps.
- **Interpretation is held to the same standard as data.** Every claim about what
  a result *means* names the artifact it rests on and states the alternative it
  does not rule out. Every reversal in this project was an interpretation that
  outran its evidence: the 2020 signature that vanished in counts, "0 of 140
  labels correct" from a check that could not detect the error, and the
  conclusion that the NYC censoring was unresolvable.
- Gate after every change; defeat attempt on every new check; deep adversarial
  audit at CP1, CP2, CP3; audit flag count monotonically non-increasing.
- Nothing touches confirmation outcomes before CP2 clears — with the O2 coverage
  diagnostic as the one candidate exception, to be decided explicitly rather
  than assumed (see Phase F).

### How each immediate step is proved

| step | proof |
|---|---|
| **N1** p-value form | Every stratum's stored placebo counts re-derived under both forms, printed side by side, and `p = 0` gone from all three. A check asserts no artifact contains a zero p-value, since zero is the signature of the biased form. |
| **N2** lattice KS | Simulate a *perfectly* calibrated lattice null at 200 and 1000 sims; the corrected test must fail ≈5% of the time at both. The current test fails 5.3% and 6.7% — that gap is the defect, and closing it is the proof. |
| **N3** within-block shift | The 10/5 split holds on **every** draw (currently 12.4%). Discovery and C2 are single-block, so their draws must come back **bit-identical** before and after — if they move, the change has leaked beyond C1. `draw_scheme_for` names the new scheme, so a calibration certifying the old one no longer satisfies `S.ri_scheme_certified`. |
| **N4** resumable calibration | Kill a run mid-flight and restart it: the sidecar shows the completed indices, the restart skips them, and the pooled result equals an uninterrupted run of the same size **exactly** — which the fixed seed sequence guarantees and the test must confirm rather than assume. |
| **N5** calibrate | `n_sims_completed,1000` on all three. **Either outcome is a result**: CALIBRATED discharges CP2's hardest line; a failure after N1–N4 is a finding about the design rather than about its defects. Record the KS statistic either way. |
| P1, P5 → fixed | `23_regression_suite.py` reports 65/65 with no regressions, and `M.status_honest` passes without either finding claiming more than its check supports. |
| broad-arm claims | `31_verify_sources.py --claims-only` recomputes all six from `cai_daily_broad.parquet` and `confirmation_episodes_rebuilt_broad.csv` and reports `verified`, not `template` or `skipped`. |
| `V.claims_cover_exhibits` | Defeat attempt: add an unregistered numeric table cell to `PAPER_MASTER.md` and confirm FAIL; register it and confirm PASS. Then confirm it does **not** fire on prose numerals — a noisy version of this check is worse than none. |
| 17's calibration gate | Defeat attempt: point 17 at an UNDETERMINED artifact and confirm it refuses to emit an RI p-value; restore and confirm it runs. |
| figures produce output | `08_figures.py` exits 0 **and** its declared `writes` exist and post-date it — `run_all.py`'s empty-run guard is now live for model stages, so this is already half-enforced. |
| Phase H go/no-go | An MDE per stratum against the MEI of **−0.005**, with the ratio registered as a claim. |

## Honest risks

- **C1's null is wrong, and the reason is now known.** No longer a risk — a
  diagnosis. The circular scheme reproduces C1's real 10/5 block split on only
  12.4% of draws, because it shifts through the two blocks' admissible days as
  one sequence and block 1 is 81% of them. The placebo designs are structurally
  unlike the design under test, which is why D ≈ 0.09 while a perfect null on the
  same lattice sits at 0.028. The remaining risk is that the within-block fix
  does not fully resolve it — in which case the next candidate is the statistic's
  dependence on block composition itself, and the honest fallback is to report C1
  by block rather than pooled.
- **Two defects the calibration would have inherited**: the RI p-value uses
  `k/n` rather than `(1+k)/(1+n)` (p = 0 appears in every artifact), and the
  uniformity test compares lattice-valued p-values against a continuous uniform
  despite a comment saying not to (6.7% false failures at 1000 sims). Both are
  fixed before any further calibration runs.
- **The environment cannot hold a long job.** Measured: a 5-hour run died at ~45
  minutes to a container restart with nothing written, because the script only
  writes at the end. CP2 needs ~18 h of calibration. Until the calibration is
  resumable, CP2's 1000-sim line is not reachable at all — which makes N4 a
  gating item, not an optimisation.
- **Power may kill the confirmatory run.** Now measurable: the MEI is −0.005 and
  C1 carries 15 episodes. If the MDE exceeds it, the conclusion is the bounded
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

**2026-09-13 ~08:00Z — fresh container; see the Status block at the top.**

What happened, in order: the handoff was read against the repository (its branch
state was accurate; the environment it described was gone); the outcome side was
rebuilt from committed inputs and reproduced (EMS extract hash unchanged, panel
and episode lists byte-identical, the four §8 first-week estimates recovered to
the stated precision at 2 draws); the user decided the four open questions; the
O2 coverage diagnostic was disclosed, then built as a declared, logged,
scope-checked access and run (20 within-window code breaks, geocoding step at
2016-01-01); addendum §§19–21 and PAN §9.7 pre-committed the reading of a
non-rejection, the spliced arm and the within-block scheme; the CP1 adversarial
audit ran and its findings were remediated in groups (C and B complete, A/D/E
partly); the confirmatory script was rebuilt on the certified machinery.

- **In flight** (relaunch `ops/rebuild.sh` then `ops/calib1000.sh` after any restart):
  C1 200-sim calibration under the within-block scheme; then the 500-draw
  discovery estimator (its 2-draw ledgers will be extended), the secondary
  models, C2's calibration, the power run; then 1000 sims on all three strata.
- **Untouched**: `FREEZE_ACTIVE` stays True. The only confirmation-window
  reads this session are the declared O2 access (logged in
  `data/reference/freeze_access_log.csv`) and — to be disclosed as F3 — the
  2026-09-09 refutation numbers already sitting in the O2 register row.
- **Next**: remediation A (freeze exposures, F3), D (gate integrity), the L7
  arm, 19's C1 calendar and re-run, C1/C2 certificates → close P1/P5/RI3 and
  re-establish the §7.4 rows and claims → CP2 → freeze lift → Phase I → Phase J.


**2026-09-12 23:30Z, at `1731c92`.**

**PHASE G IS DONE.** The first analytic estimate this project has produced. See
`PAPER_MASTER` §8 and §9 of `GATE2_PRELIMINARY_RESULTS.md`. Headline: the
mental-health share does not move in either arm at any window, both arms agree
(no reversal in counts, which this project has been caught by before), and the
only thing surviving Bonferroni across 65 decomposition tests is the **injury
channel** — days 0–2, in share and in count, with both placebos quiet. That
reverses the GATE2 memo's emphasis: it proposed a protest channel *alongside* a
help-seeking story, and on the rebuilt pipeline the protest channel is what
survives.

**It is a null of unknown resolution.** Power against the −0.005 MEI has not
been computed. Phase H is the next thing that makes §8 interpretable as an
absence rather than a silence.

**The environment restarts every 30–70 minutes.** Four restarts observed. Both
long paths — `18_null_calibration.py` and `event_study.randomization_p` — are
checkpointed and verified by the same test: truncate the ledger, restart, require
the completed ledger to be *exactly equal* to the uninterrupted one. Phase G only
finished because of this; it had died twice before. **Anything long added later
must be checkpointed too**, and the retry wrapper pattern in
`scratchpad/phase_g.sh` is the template.

- **In flight:** the 1000-sim recalibration of all three strata under the new
  within-block scheme, C1 first. Resumable — relaunch
  `scratchpad/calib_all_1000.sh` after any restart. ~4.5 sims/min, so C1 alone is
  ~3.5 h. Progress: `wc -l outputs/tables/null_calibration_ledger_d200_C1.csv`.
- **Gate:** 74 checks, 73 pass, 1 BLOCKED (`S.ri_scheme_certified`, honestly
  pending that recalibration), 0 fail. 91 claims reproduce. Audit 42/2.
- **Held at `unverified` on purpose:** P1, P5, N3 — their check is BLOCKED, and a
  BLOCKED check is not evidence. They clear when C1 certifies.
- **Untouched, and the supervisor's call:** **O2**. Closing it means reading
  2015–16 confirmation outcome data. `FREEZE_ACTIVE` stays on.
- **Next:** C1 certifies → close P1/P5/N3, restore §7.4's C1 row → **Phase H**,
  the MDE against −0.005 per stratum, which is what tells us whether the
  confirmatory run can say anything at all.
