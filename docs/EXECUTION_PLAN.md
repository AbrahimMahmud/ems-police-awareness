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

## Status (2026-09-21 ~22:50Z) — MANUSCRIPT REVISED ON A FIVE-REFEREE PANEL at `d999d84`; restructured to the venue's budget at `03e3d8e`; gate 92/92 twice; what remains is the author's decisions listed below

**Read this block first; the blocks below it are the record of how the result was produced (CP3 at 05:30Z, the seal at 04:00Z, the lift on 2026-09-20).**

| | |
|---|---|
| Branch | `analysis-rework`, pushed through `d999d84` (the panel revision) plus this record commit; the Obsidian vault is no longer in the repository (`vault/` gitignored since `6ace8f5`; delivered as a zip). |
| Restructure (`03e3d8e`, ~17:45Z) | `docs/PAPER.md` cut to the venue's shape: prose Results, four display items (Table 1 family + reading, Table 2 outside the family, Figure 1 first-week paths, Figure 2 the decade of attention); Methods detail, the reader's transcript, the sealed run's full tables (S1–S5), the code list, crosswalk, calibration and power tables (S7–S10) and the exploratory figures in a new `docs/SUPPLEMENT.md`. New generators `ops/paper_confirmatory_tables.py`, `ops/supplement_tables.py`, `ops/paste_generated.py`, `ops/refresh_generated_claims.py`; figures fig6/fig6b (paths) and fig7 (decade) in `08_figures.py`. `V.paper_budget` (finding W1) holds the main text under 5,000 words and the display items at four. |
| Referee panel (wf_a3619d51-50e, 19:00–22:10Z) | Five lenses (epidemiologist, statistician, domain, reproducibility, editor), 50 comments; 41 of 47 major/moderate comments fact-checked against the sealed files (the last six editor checks and the synthesis fell to a usage limit). Record with the disposition of every comment: `docs/REFEREE_PANEL_2026-09-21.md`. |
| What the panel found wrong (fixed, RP1–RP6, `V.manuscript_referee_tokens`) | Diagnostics reported by p alone and "total dispatches did not" fall (their mean fell by more); the C1 path tidied past its coefficients; the same-sign rule said to block both outcomes (it blocks only EDP; narrow MH is blocked by its count arm's p 0.0895); the offset count arm called free of compositional damping (it is a rate on the share's denominator); the dose-response arm "positive in every stratum" (negative over discovery); no interval anywhere while "not excluded" was said four times. |
| Manuscript now | Abstract 250 words around the estimate (−0.00059, 95% CI −0.0032 to 0.0021 before B-HEARD; −0.00019, −0.0024 to 0.0020 during it; mean share 0.086); Introduction with the two channels, Curtis et al., Nix & Lozada on Bor; Methods with the identifying assumption, the count arm as a functional-form check, the certification scope, the two mismatches behind the bound, B-HEARD's direction (Kang) and attenuation; Results reporting only (eight C1 coefficients, 1-df Wald 0.19 vs 25.32, asymptotic p, within-period family of four, ranges, both diagnostics' coefficients, discovery dose-response); discovery estimates moved verbatim to S1.10; Discussion reconciles the bound with the realised precision and keeps the pre-registered reading as the conclusion; Limitation 2 (citywide average); implications paragraph. **4,998 words main text** (ceiling 5,000; the venue's ~4,000 was not reached without cutting substance the panel asked for). |
| Display items | Table 1A: interval (95%) and asymptotic p; 1B: episodes, district-day observations, plain headers; Table 2 in two panels (ranges, override/injury split, diagnostics with coefficients). Figure 1: one scale per row, no in-image title; Figure 2: standalone caption. Supplement: Table S6 embedded as a regenerated region (S3.1); Table S10 with the randomization-based MDE. |
| Claims | **1,582 registered, 1,582 verify** (292 hand-written + 1,290 generated); 88 new hand claims for the revision's prose numbers (C1400–C1487), 43 dropped with their sentences, 25 re-pointed to the supplement with the discovery text. |
| Findings | **171 filed, 171 fixed, 0 open** (W1 the budget; RP1–RP6 the panel). |
| Gate | **92 checks, 92/92 twice** after the revision (and twice after the restructure at 91). New: `V.paper_budget`, `V.manuscript_referee_tokens`; `V.claims_cover_exhibits` scans the supplement and skips the regenerated episode table; `V.table1_regenerates` holds the supplement's copy. |
| Open for the author | (1) the venue's ~4,000 words: a further ~1,000 would have to come from substance (candidates: Limitations 7–9 and 11–12 to the supplement; the within-period-family sentence; the guards sentence); (2) the within-period family-of-four disclosure and the intervals-beside-the-bound framing are additions to what the pre-registration reads out — strike if unwanted (the reading stands either way); (3) the raw outcome series as a main-text figure in place of Table 2 (epidemiologist); (4) a Figure S7 from the discovery heterogeneity split needs a tracked generator; (5) a counted linkage flow for RECORD 6.3 (records removed by the disposition filter, dispatches without a district, district-days under the five-dispatch rule) needs registered numbers; (6) the ethics determination, affiliations, funding and conflict lines; (7) RECORD 6.2's code-list comparison with Kang, Lu & Pang. |
| Memory | capsule, graph export, `HANDOFF_2026-09-21.md` §1/§2/§5 revised; the vault (outside the repo) updated and re-zipped. |

---

## Status (2026-09-21 ~05:30Z) — CP3 DONE: the full manuscript audit ran (39 agents) and every surviving item is fixed and held by the suite; the manuscript is complete at `663153d`; what remains is the author's editorial pass

**Read this block first; the two blocks below it (04:00Z: the seal and the paste; 2026-09-20 09:30Z: the lift) are the record of how the result was produced.**

| | |
|---|---|
| Branch | `analysis-rework`, pushed through `663153d` (CP3 remediation). Working tree clean after this commit's companions (execution plan, handoff, vault, graph, capsule). |
| CP3, full audit | wf_0df7b965-8dc, 03:36–05:15Z: eight finders (results-vs-reading, numbers-vs-claims, methods-vs-code, record-vs-paper, overstatement, consistency, reproducibility, references-and-display), **61 raw findings, 57 unique**, three-lens refutation of the ten highest (**5 survived**: Limitation 9 called F1/F2 metadata reads and F3 a coverage read; Methods said the strata were never used for a specification choice; Limitations said no number from the incidents was kept; the Discussion said everything was committed before any confirmation outcome was seen; the closing paragraph claimed the compositional damping biases toward the null), a completeness critic (6 items: the disposition filter absent from the outcome definition, H2/H3 never run and absent from Limitations, RECORD 6.1/6.2 overstated, the word and display-item budget, the corrupted label, the Nix & Lozada answer never given). **Every surviving item is fixed; every unverified item that held on inspection is fixed too** (the family-corrected bound beside the nominal one in Abstract and Discussion, the placebo inference withdrawn, the Floyd sentence replaced, the dose arm defined in Methods, three diagnostic cells, the EDP share named as the power outcome with the MDE-vs-test limitation, the run-log rows described as they are, the reproducibility statement, the nine pooled cells added to Table 4, captions from the sealed table's reasons, Figure 2's units, Figure 3 from the joint specification, Wu et al. cited for what it measured, the note's §4 table, the master's heading and limitation 12). Filed as **P59–P63**, held by `S.third_pass_record_consistency` (three new tokens, each defeat-tested). |
| Manuscript | Complete. Abstract 250 words to PAPER_PLAN's specification. Main text about 8,200 words excluding tables (Methods about 4,000) against ~4,000; nine display items against four: **the author's editorial pass is the one open item** (Supplementary Methods for the estimator, randomization, calibration, sensitivity and power detail; Supplementary Tables for 4–6). References 11–13 confirmed against their sources (PubMed, the Mannheim repository, the IBO report); RECORD 6.2's code-list comparison waits on Kang, Lu & Pang's methods. |
| Claims | **1,354 registered, 1,354 verify** (226 hand-written + 1,128 generated by `ops/phase_i_tables.py`); every numeric table cell in both documents covered. |
| Findings | **164 filed, 164 fixed, 0 open** (P59–P63 this pass). |
| Gate | 90 checks, 90/90 twice after the remediation and twice after the close-out edits. |
| Memory | vault `Status`/`Next actions`/`Decisions`, graph nodes and export, capsule — at the CP3 state. `HANDOFF_2026-09-21.md` revised. |

---

## Status (2026-09-21 ~04:00Z) — PHASE I SEALED 03:24:13Z; the reading is the pre-specified null in both strata; PAPER_MASTER §8b and the paper's confirmatory Results, Discussion and Abstract are written from it; 1,269 claims verify; gate 90/90 twice; CP3's full audit in flight

**Read this block first; the "Status (2026-09-20 ~09:30Z)" block below it is the
record of the lift and of Phase I's start, kept for its reasoning.**

| | |
|---|---|
| Branch | `analysis-rework`, pushed through `01dabeb`: `34d4b9e` (the sealed table, sidecar, run log and reading), `bbbe1e2` (§8b, Results, Discussion, Abstract, 1,063 claims), `01dabeb` (vault, graph, capsule). Working tree clean. |
| Phase I | **Sealed 2026-09-21 03:24:13Z** (`data/reference/confirmatory_results.csv` + `.meta.json`): 166 cells at 2,000 draws, 157 estimated, 9 `IDENTICAL_TO_PRIMARY`; `git_commit` b046fb6, `pythonhashseed` 0, two workers at the seal. **Seven start rows** in `confirmatory_run_log.csv` (09:29:42Z under `4e3dce1`; 10:34:56Z after the container suspension; 13:48:34Z the runner's automatic retry after the first OOM kill and 13:50:33Z the hand relaunch with two workers; 15:23:5xZ three workers for speed; 20:17:4xZ the automatic retry after the second OOM kill and 20:19:27Z the hand relaunch with two workers); the hand relaunches carry their reasons, the two automatic retries repeat the reason of the start they retried, the original start carries none; the sealed table's `overwrite_reason` carries the last. Parallelism changes no number: every cell is seeded from its own identity and banked in its own ledger. Wall clock 17 h 55 min. |
| Reading | `34_confirmatory_reading.py` once, sealed to the table it read (175 rows, `.meta.json`). **The pre-specified null (PAN 9.4 row 5), read by addendum §19 rule 2, in both strata.** C1 and C2 "does not reject"; a sustained shift at or above the pre-freeze MDE (0.01156 / 0.00875 of the share) is disfavoured at 80% power; the MEI −0.005 is not excluded; the transient dip-and-rebound of the MEI is disfavoured (MDEs 0.00382 / 0.00290); cardiac and asthma quiet in both (4 of 4 override cells). Reported, not read: C1's smallest unadjusted randomization p 0.0115 and 14 of 24 H1-outcome sensitivity cells at p ≤ 0.05 (C2: 0.4523; 0 of 30); C1's dose-response arm moves against the predicted direction (asymptotic p 0.0309 / 0.0187, positive), C2's dose and B-HEARD-interaction arms do not move; pooled does not reject on both arms (descriptive). |
| Manuscript | `docs/PAPER.md` complete in the PAPER_PLAN order. Confirmatory Results = the reader's sentences quoted verbatim (`prose.md`) + Tables 2–6 (`tables.md`); Methods states the seal and the seven starts; Discussion's "What the reading says" and "Implications" and the Abstract (unstructured, 250 words; names the NYC EMS Incident Dispatch Data, New York City, 2015–2024, the linkage, the design, the three-way question) written from the reading only. No PHASE I PENDING markers. Main text about 7,086 words excluding tables (Methods about 3,465) against the venue's ~4,000: the author's editorial pass (Supplementary Methods) is the open item, with reference 13's title and the RECORD 6.2 comparison. |
| Claims | **1,269 registered, 1,269 verify**: 206 + 1,056 generated by `ops/phase_i_tables.py` (per-document ids from C210) + C1300–C1306 (Discussion/Abstract numbers read from `confirmatory_reading.csv`). Every number in every numeric table cell of both documents sits inside a claim. |
| Gate | **90 checks, 90/90 PASS** twice after the paste and twice after the Abstract. The first lifted-and-pasted run failed two checks, both mechanical: `V.claims_reproduce` (C161's anchor sentence had gained its citation marker ¹²) and `V.claims_cover_exhibits` (48 cells: the labels "28-day post window" / "60-day post window" start with a numeral, which the check reads as a value). Fixed by carrying the marker in the template and renaming the labels "post window 28 days" / "post window 60 days" in the generator, both documents and the register; the regenerated tables and claims match the register row for row. |
| Findings | 159 filed, 159 fixed, 0 open. Freeze lifted since `4e3dce1`; F1–F5 disclosed (PAPER_MASTER §5.3, addendum §15, PAPER.md Methods and Limitation 9). |
| CP3 | Blind half done 2026-09-20 (wf_f6cc235c, every item but the word budget fixed). **Full audit launched 2026-09-21 03:5xZ** (wf_0df7b965-8dc: eight finders — results-vs-reading, numbers-vs-claims, methods-vs-code, record-vs-paper, overstatement, consistency, reproducibility, references-and-display — three-lens refuters, completeness critic; prompts corrected for the seven starts before launch). Triage, fix, gate twice, commit follow. |
| Memory | vault `Status`/`Next actions`/`Decisions`, graph (5 nodes, 4 links; export 60 lines), capsule entry — all at the sealed state. |

---

## Status (2026-09-20 ~09:30Z) — FREEZE LIFTED at `4e3dce1` after C2 certified at 1,000 (09:16Z) and the gate ran clean lifted (incident F5 found by that run, disclosed, pinned); Phase I's sealed run started 09:29:42Z (run log start row, commit 4e3dce1) — resumable, hours; then 34, tables, §8b, the paper's Results/Discussion/Abstract, CP3

**Read this block first; everything below it under "Status (2026-09-12…)" is the
historical record of the previous session and is kept for its reasoning.**

| | |
|---|---|
| Branch | `analysis-rework`; commits `34211cc`…`ac2e9e2` on top of the handoff's `e541632`, pushed. Working tree carries the registers the cold run rewrites as it goes (`data_sources*.csv`, `source_verification_log.csv`, `freeze_access_log.csv`, `outputs/run_manifest.json`); they are committed once the two cold passes agree. |
| Environment | **Suspended for a week.** The session paused on the usage limit at 22:40Z on 2026-09-13 and resumed 2026-09-20 03:42Z with `up 6 min`: every process gone, the filesystem intact (ledgers, certificates, model artifacts, scratchpad). The discovery calibration resumed from its 719 banked sims at 03:43Z through `ops/calib1000.sh`; the cold passes were relaunched through `ops/coldrun.sh`. Before that: **a fresh container.** No `data/processed`, no `outputs/tables`, no scratchpad survived. Everything regenerable was regenerated from committed inputs: the EMS extract re-downloaded with an unchanged provenance hash (S1b), the panel and both basket arms byte-identical, discovery re-calibrated (CALIBRATED, rejection 0.05, lattice KS p 0.7516). |
| Environment, the rule | **Compute advances only while a session is active.** The container is suspended or reset when the session is idle (a 4-hour usage-limit pause advanced the ledger by zero rows; it came back with `up 1 min` and an empty process table). Every long job is checkpointed and driven by the runners in `ops/`, which are relaunched blind after any restart. Poll by PID file, never `pgrep -f`. |
| Decisions (user, 2026-09-13) | **Continue to Phase I** as pre-registered, with the reading of a non-rejection fixed against the measured power (addendum §19). Branch stays `analysis-rework`, no attribution. **O2 diagnostic: disclosed first, then run** as a declared access (addendum §18; done). Deliverable: a Markdown manuscript in the repo. |
| CP1 | **Done as an adversarial audit** (8 finders by failure class, 3-lens refutation where the usage limit allowed): 60 raw findings, of which the confirmed and self-verified ones are filed as O2-close, X16, N7–N10, X17, P8–P10 and the pending items in remediation groups A–E below. |
| Gate | **90 checks, 90/90 PASS at 05:52Z 2026-09-20 (the first run after the third audit pass had two failures, both the finding-count claims 126→158, updated), baseline refreshed at 90; 206 of 206 claims verify.** Checks added 2026-09-20: X.run_all_deterministic_env, V.paper_figures_current, S.third_pass_record_consistency; S.confirmatory_spec_audit and S.confirmatory_reading_rules extended (32 planted tables, the enumerated sensitivity set, the sealed reading, the pinned thresholds). The eight §8 randomization p-values are their 2,000-draw values (0.697, 0.527, 0.886, 0.822). Discovery's 1,000-sim certificate (05:10Z: rejection 0.045, KS p 0.2944) replaced the 200-sim numbers in §7.4 through the claims (C70/C121 re-anchored at three decimals). |
| Findings | 159: 159 fixed, 0 open, 0 unverified (F5 at the lift, disclosed). Third CP2 specification audit (8 finders, 3-lens refuters capped at 10, completeness critic; run wf_f524dc75, 57 raw findings, 5 confirmed, 5 killed, 6 critic items) triaged by hand in full and filed as **P27–P58** (addendum §30; rules 23.1c/d/e): run log and hash-seed requirement on the sealed run, certificate-vs-design gate, 14-day draw geometry for the window sensitivities, unfiltered diagnostics, cross-window coverage-clean and a geocoding-only cell, cancelled-inclusive and no-EDPM cells on both arms, day-by-day path columns, pinned sidecars; the reading sealed, on the tracked pre-freeze power table, with the sensitivity set enumerated, the pooled and secondary arms read, the placebo check unable to fail open; the record corrected (row 3 non-blind, C1's 2021 block inside COVID, PAPER_MASTER §6 strata, B-HEARD covariate numbered as row 30, §18/F4/§20 wording, 62,920→77,506, three docstrings, §5.3's remedy foreclosed by the lift). Earlier: N11, D8, P19–P26 (2026-09-13), X20, X21 (2026-09-20). **C1 certified 2026-09-13 20:56Z** under `circular_within_block_fw7` (0.049, KS p 0.9930); **discovery certified at 1,000 on 2026-09-20 05:10Z** (0.045, KS p 0.2944); **C2 certified at 1,000 on 2026-09-20 09:16Z** (0.054, KS p 0.8221); pooled at 200 (descriptive). CP2 complete; the lift follows. |
| Claims | 206 registered; every registered claim whose artifact exists verifies (121 at 20:56Z, the rest deleted by the cold run's clear and regenerating); the rest wait on the cold run's model stages, which the cold-run runner deleted before rebuilding. C1's §7.4 row and prose are re-registered as C65, C66, C128–C131 and verify; C132–C149 close the cell-level exhibit coverage. Claims on regenerated artifacts (the C2 rows, §8 p-values, decomposition, power) re-establish as the chain writes them and are read from the artifact, never "fixed" to the old numbers. |
| Manuscript | `docs/PAPER.md` started 2026-09-13 in the PAPER_PLAN drafting order: Introduction, Methods (with the deviations subsection), Limitations, display-item list, RECORD table and references are drafted; Abstract, confirmatory Results and Discussion are marked **PHASE I PENDING**. Every number in it is registered: C150–C187 address PAPER.md directly (design counts, panel moments, discovery estimates, MDE ratios) and verify except where the artifact is still regenerating; `V.claims_cover_exhibits` scans PAPER.md's tables as well as PAPER_MASTER's. Unsourced figures found by a prose sweep (district population range, the 184-day regime episode, the fixed-threshold selection range, the F3-derived 0.0002) were removed rather than registered. |

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
- **D — gate integrity: done (2026-09-13 ~09:00Z).** Unbaselined/retired checks fail `main()`; a template without exactly one `{}` is `malformed`; `M.status_honest` first-run BLOCKED; `V.sources_verified` compares hashes; arm suffixes collapse over `config.ARMS`. **Cell-level exhibit coverage**: `V.claims_cover_exhibits` now requires every number in every numeric table cell of PAPER_MASTER (cells that start with a number, decoration included: `1.05×`, `2.203 → 2.092`, `1 of 3,472`) to sit inside a claim's captured group — 57 numbers in 52 cells, 0 exemptions, claims C132–C149 added (the §7.4 rejection rates, the §3 counts, the anti-police rank cells, the z-score multiplier table via a fresh `25_zscore_simulation.py` run, the O2 code counts, the strict-arm cells). U+2212 in `NUMBER_RE` and `_template_regex` (either minus, never the en dash); the updater keeps the document's typography. `M.register_sync` requires the register's `checks` column to equal the suite's tags for every finding and a three-word severity vocabulary — 10 rows reconciled (RI2 and N5 had named a check that never tested them), `major`/`serious` normalised to `blocking` (64 blocking, all covered). `X.run_all_stages_declared` imports `STAGES` instead of regex-parsing the source. `E.episodes_labelled` recomputes every driver label from the attention series (the blank test could not fail). `D.outcome_list_complete` enumerates every file in `data/processed` (two orphan `.txt` summaries with no writer deleted). run_all fails a stage that exits 0 without refreshing its declared outputs. 19's early UNDETERMINED exit honours no-downgrade. `MIN_SIMS_FOR_VERDICT` and `NOMINAL_ALPHA` defined once in config for 18 and 19. 09 writes `wikipedia_article_resolution_legacy.csv` and 10/21 read it, so a fetch can no longer overwrite the published basket; 32 registers the basket it publishes (D7). `31` reports an artifact with no provenance row as `unregistered` instead of "verified" — ten were: 00b, 11 (all arms) and 16 now register every file they write (S1c, S1d, S11a–c, S15b); 28 and 29 were re-fetched live to register theirs and **upstream had moved** (one more article with a historical title, 533 titles against 530, more recovered views), which would have changed the frozen treatment input `article_title_map.csv` — so the fetch was reverted to the committed bytes, the code edits with it, and the three side files stay pinned until a deliberate treatment rebuild; the two committed inputs (S5, S6) and the Trends stitch diagnostic (S12; 11b registers it as S12b next fetch) are pinned. `fetch_leads`' first-sentence cut measured **immaterial and correct**: on the full intro 2 of 13 unestablished articles would flip to police_violence — McGlockton and Scurlock, both civilian killings whose intros name the investigating agency.
- **E — documents: done** except the numbers that the chain regenerates (§7.4 C2 row, §7.5b power, §8 p-values), which re-establish from artifacts.
- **L7 spliced arm: done** (addendum §20; 11 → 12 → 13 under `--arm spliced`; identical on all 1,764 pre-break days, differs on 1,708 of 1,708 post-break days, `T.spliced_arm_prebreak_identical`; §5.1a; C122–C127).
- **2026-09-20 03:42Z–04:20Z, after the week-long suspension.** Gate clean (87/87 twice, 206/206 claims) once the §8 p-values moved to their 2,000-draw values (`bbd146a`). Cold passes 1 and 2 both clean (24 stages each) but six outputs differed by hash: three were the check stages' timestamped reports (suite table, verification log, source register) and three were 17's and 25's tables, which differed at 1e-16 in coefficients and 1e-11 in clustered SEs — Python hash randomization ordering something behind the design matrix; single-threaded BLAS did not remove it, `PYTHONHASHSEED=0` made two runs byte-identical. **X20**: run_all passes `STAGE_ENV` (seed 0, one BLAS thread) to every stage, the runners export it, the cold comparison requires identity on build/model outputs and lists reports separately; `X.run_all_deterministic_env`. Cold passes relaunched 04:20Z under it. Also built at the user's request: repo-tracked memory tooling (`ops/graph_memory`, `context-capsule`, `vault/`, `ops/ems_duckdb.py`, `pyproject.toml`/`uv.lock`, `tests/` — 12 synthetic-data tests passing; `docs/LOCAL_SETUP.md`). The third audit run (`wf_f524dc75-8a5`, Opus model) is in flight.
- **Second CP2 specification audit (21:49Z–22:01Z, workflow `wf_1061c617-ea4`).** Re-launched on the final specification with the same eight attack classes; one finder (estimand-and-test) completed before the session usage limit stopped the other seven, every refuter and the critic. Its eight findings were triaged by hand against the cited lines and every one was real; all acted on before the lift: **P19** the 28/60-day windows (addendum §3) and the dose arm (§9) were promised and estimated by no cell — 30 now runs `sens_post28`/`sens_post60` (sensitivity, both outcomes, both arms, every stratum) and `dose_response` (secondary, asymptotic p); **P20** a one-arm or opposite-sign rejection was read as a bounded null with the words 'no effect detected' — addendum §23.1a, 34 and the planted tables; **P21** addendum §25.3 (asymptotic p as the uncertified stratum's inference) was not implemented — §25.3a, 34; **P22** a denominator-driven outcome vetoed a clean rejection on the other — §23.3a; **P23** the anchor-shift null permutes the gaps and the record described a rigid shift, and §21 claimed the two schemes coincide on one window — §27, wording corrected in the note, PAPER_MASTER §7.4 and 30's docstring; **P24** the strata, the eight-test family and the both-arms rule had no numbered deviation and the note's ledger counts were stale — §28, §14 names the second outcome and the joint statistic, note §11.2–11.4 corrected; **P25** §9.4 row 1 was returned for rejections on different outcomes — §23.1b; **P26** 30's docstring contradicted its code — rewritten, held by `S.confirmatory_spec_audit`. `S.confirmatory_reading_rules` now plants 17 tables (defeat-tested against five broken readers); the dry run re-stamped with the new cells. The other seven finders are re-run when the limit allows and before the lift if time permits; their absence is recorded here rather than papered over.
- **D8, found while preparing the lift (21:40Z).** `select_sample` derived every caller's window from `FREEZE_ACTIVE`, so the lift would have moved 17, 05, 03, 04, 06, 07, 08, 18, 19, 22 and 25 onto the confirmation sample (an unsealed confirmatory run one command away; the discovery results irreproducible from a fresh clone after the lift — CP3's first line). The guard now takes `window=` (`discovery` pinned whatever the flag; `confirmation` refused under the freeze; derived only for 30), every exploratory reader passes it, 07/08/17 filter to discovery episodes unconditionally; `D.discovery_scripts_pinned` (AST + behavioural, defeat-tested three ways); addendum §26; PAPER_MASTER §5.2 Layer 3. Numbers unchanged under the freeze — cold pass 2 runs the pinned code and its manifest must match pass 1. Gate 87 checks.
- **Table 1 generated (21:45Z).** `ops/paper_table1.py` renders the 74-episode list with the stratum each episode is tested in (first-week containment) and the frozen list's matching start within ±7 days, into `docs/tables/TABLE1_episodes.md`; the register's per-cell rule is met for this generated file by `V.table1_regenerates`, which re-renders it and requires identical bytes (defeat-tested: an edited date, an appended row). Treatment-side only; runs under the freeze. Gate 86 checks.
- **Phase I tooling written before the lift (21:30Z).** `34_confirmatory_reading.py` applies addendum 23.1–23.4, §19 rule 2, §25 and note §9.4 to the sealed table as a pure function and writes `data/reference/confirmatory_reading.csv` (tracked, beside the seal); under the freeze it runs only on the synthetic dry run. `S.confirmatory_reading_rules` feeds it 13 planted tables (one per rule and per §9.4 row, the strict BH boundary, the uncertified-null case) and was defeat-tested five ways (BH `<=`, no placebo override, one-arm rejection, direction ignoring the SE, a panel read). 30 now writes `first_week_mean_se` (the input 23.2 needs) via `first_week_mean(return_se=True)`; `BH_Q` is defined once in config; the dry run re-stamped (rc 0, 107 rows). `ops/phase_i.sh` runs 30 (resumable, `--jobs 4`, a seal refusal is not retried) then 34 and is documented in `ops/README.md`. run_all gained the two basket arms as build stages (`12/13 --arm broad|spliced`; their products had been deleted by the cold clear and rebuilt by nothing, leaving `T.spliced_arm_prebreak_identical` BLOCKED), and the manifest records each stage's args; the arm episode lists rebuilt byte-identical to the tracked ones.
- **N11, a near-miss caught by N7 (21:08Z).** The discovery 1,000-sim run started at 20:56:02Z, twelve seconds after the relaunched cold run cleared `data/processed` (20:55:49Z) and two minutes before 01 rebuilt the panel; 18 fell back to assumed noise (rho 0.6, mu 0.10) with a printed note, quarantined the 200-sim ledger as STALE because the design fingerprint no longer matched, and started certifying a null unrelated to the data under `null_calibration.csv`. Seen in the ledger diff at 21:08Z; killed at 21:09Z after 25 fallback sims; the wrong-design ledger moved to the scratchpad, the quarantined ledger restored under its own sidecar (fingerprint 99976377) and the run restarted — `calibrated to the real panel: rho=0.0482`, `resuming: 200 sim(s) … identity verified`, 800 to run. 18 now refuses without the panel (exit 3; `--allow-assumed-noise` for smoke tests only) and writes `noise_source`; `S.calibration_noise_measured` compares every certificate's sidecar with 19's measured noise; `ops/calib1000.sh` retries 30× so a refusal during a cold pass's two-minute rebuild window is waited out. The 200-sim discovery and C2 certificates, C1's 1,000 and pooled's 200 all carry the panel's parameters (checked).
- **C1 under the corrected drawer is CALIBRATED at 1,000 sims** (20:56Z: rejection 0.049, KS D 0.0155, lattice p 0.9930, median p 0.4975; `null_calibration_n1000_C1.csv`). §7.4's C1 row and prose re-registered (C65, C66, C128–C131) and verified; P1, P5, RI3, P12, P13 closed; `S.ri_scheme_certified` PASS. `calib1000.sh` moved on to discovery at 1,000 (20:56Z), then C2.
- **Pooled under the corrected drawer is CALIBRATED at 200 sims** (19:00Z: rejection 0.04, KS D 0.057, p 0.549). `calib1000.sh` started C1 at 1,000 at 18:59Z; the cold runs follow.
- **C1 under the corrected drawer is NOT CALIBRATED at 200 sims** (18:00Z: rejection 0.035 inside the band, lattice KS D 0.097, p 0.0455, median p 0.433). Addendum §25 pre-registers the fallback before the 1,000-sim verdict: cells estimated and written with the randomization p flagged uncertified and entering BH as p = 1; C1's primary inference becomes the asymptotic p, labelled, and a C1 rejection on it cannot confirm. Implemented in 30 (`_uncertified_certificate`) and accepted by `S.ri_scheme_certified` / `S.lift_requires_1000_sims`. The stratum is not redefined and the scheme is not changed again.
- **Compute plan from 17:45Z** (`scratchpad` runners, relaunched blind after each restart): `calibfix.sh` rebuilt the build stages on the full-span panel and is re-certifying C1 then pooled at 200 sims under `circular_within_block_fw7`; it then hands over to `calib1000.sh` (C1, discovery, C2 at 1,000). `coldrun.sh` waits for `calibfix.done` and then runs `run_all` twice from cold (the first clear already happened at 17:14Z when the runner was killed mid-wait, which is why every model artifact is currently absent). Cold pass 1 failed twice before it could reach the models — at 19:05Z on `31_verify_sources.py` running before the model stages (X19, fixed in `8188f9a`) and at 20:49Z when 17 at 2,000 draws hit run_all's 5,400 s stage timeout (per-stage `timeout` of six hours for 17 in `ac2e9e2`, seeded ledgers kept across passes) — and was relaunched at 20:52Z; 17 has been running since 20:57Z. The synthetic dry run of 30 was re-stamped after the addendum-23 edits. Two more container restarts today (13:xxZ and ~17:12Z), each on a usage-limit pause.
- **Container restart during a usage-limit pause (10:18Z–12:11Z)** killed `19_power.py` mid-run and both runners; relaunched 12:14Z from their state files (calib_C2 skipped as done, power19 restarted). The rule stands: compute advances only while the session is active.
- **Rebuild chain (ops/rebuild.sh), in flight:** the 500-draw discovery estimator finished 09:00Z and **reproduced every §8 number exactly** in this fresh container (coefficients −0.00123/−0.01084/−0.00103/−0.00615, randomization p 0.695/0.519/0.880/0.826) → 05, 03, 04, 06, 07, 08, 33 → C2 calibration → 19 power; then `ops/calib1000.sh` (1000 sims × 3 strata). Alongside: `18 --stratum pooled --sims 200` (new, P12) and the re-stamp of 30's synthetic dry run after the pooled-certificate edit.
- **Two CP2 gaps found while preparing the checklist (2026-09-13):** nothing enforced the 1,000-sim requirement at the lift (P11 → `S.lift_requires_1000_sims`), and the pooled stratum's p-values rested on C1's and C2's certificates with no calibration of its own three-window geometry (P12 → `18 --stratum pooled`, `STRATUM_CALIBRATION["pooled"] = ("pooled",)`, addendum §22).
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
each block survives, and the seam disappears. Feasibility checked: 542 × 143 =
**77,506 distinct placebo designs** under first-week containment (addendum §24;
the 520 × 121 first written here counted full-post containment), against 2,000
draws needed. This is a
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

*Status column added 2026-09-13; each tick names the evidence.*

- [x] Every check PASS. No FAIL, no BLOCKED, no ERROR. Baseline refreshed.
      *(90 checks, 90/90 PASS twice at 05:52Z 2026-09-20 after the third
      specification audit's remediation, baseline refreshed in the same commit
      (`0eaf45d`); every check added since 2026-09-13 defeat-tested. Re-run once
      more on C2's 1,000-sim certificate, immediately before the lift commit.)*
- [x] Calibration passes KS uniformity at ≥1000 sims **on all three strata**,
      against the **lattice** rather than a continuous uniform, after C1's scheme
      is replaced with the within-block shift. *(C1: CALIBRATED at 1,000 under
      `circular_within_block_fw7`, 0.049/0.9930 (20:56Z). Discovery (0.05/0.7516)
      and C2 (0.05/0.4838) hold at 200 while `ops/calib1000.sh` extends them to
      1,000 — discovery restarted 21:09Z on the panel after the N11 near-miss, C2
      follows. Pooled 0.04/0.5492 at 200 (descriptive; its own minimum).
      `S.lift_requires_1000_sims` fails the suite if `FREEZE_ACTIVE` is False
      on any certificate below 1,000 sims — added 2026-09-13, finding P11;
      `S.calibration_noise_measured` requires every certificate's null to carry
      the panel's measured noise — N11. **Done 2026-09-20 09:16Z: discovery 0.045 / KS p 0.2944 (05:10Z), C1 0.049 / 0.9930, C2 0.054 / 0.8221 (band [0.0365, 0.0635]), all at 1,000; pooled 0.04 / 0.5492 at 200, descriptive, its own minimum; `S.lift_requires_1000_sims` satisfied.**)*
- [x] Estimator recovers a planted effect; **RI p uses the (1+k)/(1+n) form**.
      *(`S.ri_pvalue_form` — one implementation, the form asserted;
      `S.dose_arm_wired` and the PPML check recover planted effects; 19 measures
      recovery of the planted −0.005 profile per stratum.)*
- [x] 17 refuses to report an RI p-value on an uncalibrated null, per stratum,
      and a cheap run cannot overwrite an expensive result *(done, `5fd53f3`;
      `S.estimators_gate_on_calibration`, `S.no_downgrade`)*.
- [x] `run_all.py` clean twice from cold; manifest committed; model stages
      declare their outputs so the empty-run guard is live. *(Done 2026-09-20
      04:55Z: two passes of 24 stages, every build and model output byte-identical
      under the fixed hash seed — X20 — the check stages' reports differing only by
      timestamp; `outputs/run_manifest.json` committed from pass 2.)* *(Guard live and now
      also fails a stage that leaves its outputs unrefreshed. **Cold is defined**:
      every file under `outputs/tables` that a run_all stage writes is deleted
      first, and `data/processed` is cleared except the raw page cache
      (`ems_pages/`, so 00b rebuilds from cached pages) and the
      calibration/power products of 18 and 19, which are not run_all stages —
      they cost hours, are resumable through their ledgers, and enter the
      model stages as certified inputs recorded in the manifest. The
      randomization ledgers are kept too: seeded, identity-keyed checkpoints of
      a deterministic computation, so keeping them changes no number (the first
      cold pass lost 17 to run_all's 90-minute default timeout at 2,000 draws;
      17 now carries a six-hour stage timeout). Fetch stages
      are excluded: upstream mutates (28/29 moved on 2026-09-13), and the
      treatment inputs are frozen. `--kind build --kind check --kind model`,
      twice; the second run's manifest must hash-match the first. 17 runs at
      the pre-registered 2,000 draws in run_all, so §8's "500 draws" becomes
      2,000 after the first cold run.)*
- [x] Adding B-HEARD leaves discovery numerically unchanged.
      *(`X.bheard_wired` refits with and without the control and requires every
      coefficient identical; the control is in the formula since `10256d4`.)*
- [x] Power reports an MDE per stratum against the MEI of **−0.005**; the
      MDE-to-MEI ratio and the go/no-go are recorded as claims. *(C97–C106
      registered and verifying; 19 re-ran on the corrected C1 calendar 12:59Z —
      C1 0.01156 / 0.00382 / 2.312, C2 0.00875 / 0.00290 / 1.750, discovery
      0.00950 / 0.00291 / 1.901, all UNDERPOWERED for the sustained shape;
      `power_analysis.csv` is kept across cold passes and its noise parameters
      are what `S.calibration_noise_measured` compares the certificates to.)*
- [x] `CONFIRMATION_PLAN.md` addendum committed **first** *(§15–§21, through
      `ed8a883`)*.
- [x] `30_confirmatory_run.py` committed and dry-run on synthetic outcomes
      *(105 rows, exit 0, stamped sidecar; `S.confirmatory_uses_certified_machinery`)*.
- [x] Interpretation rules and the multiple-testing correction pre-committed
      *(addendum §19 fixes the reading of a non-rejection against the pre-freeze
      MDE; the family and correction are PAN §6–§10 and are not changed by it)*.
- [x] Basket construct review complete: every included article carries a positive
      law-enforcement signal, or a recorded reason *(`T.basket_is_police_violence`;
      `fetch_leads` first-sentence rule measured correct, 2026-09-13)*.
- [x] `PAPER_MASTER.md` current through Phase H *(§7.4 all three strata, §7.5b
      power, §8.1 bounded null, §5.3 three incidents; cell-level exhibit coverage
      holds it to its claims)*.
- [x] A final adversarial audit of the **specification**, not the code.
      *(Run 2026-09-13 as an 8-finder / 3-lens workflow: six finders completed
      (46 raw findings); the two remaining finders, every refuter and the critic
      failed on the session limit, so every finding acted on was verified by hand
      against the cited lines. Filed and fixed before the lift: P13 (placebo
      admissibility snapped C1's edge episodes — measured 397/400 draws with a
      1-day gap; scheme renamed `circular_within_block_fw7`, C1 and pooled
      recalibrated), P14 (reading rules made mechanical), P15 (denominator
      diagnostic), P16 (fixed draws, tracked seal, BH over eight, asymptotic p),
      P17 (panel spanned only the discovery buffer), P18 (family labels,
      identical sensitivities, interaction C2-only), O6 (EDPT/EDPE), F4 (the
      crosswalk's all-years SODA count). Addendum §23–§24. The reading rules
      are code (`34_confirmatory_reading.py`, addendum §23.4a) held to planted
      tables by `S.confirmatory_reading_rules`. The refutation phase
      can be resumed from the workflow's run id once the limit allows; its
      absence is recorded here rather than papered over.)*

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

**2026-09-21 ~22:50Z — The manuscript restructured to the venue's budget (`03e3d8e`) and revised on a five-referee panel (`d999d84`). See the Status block at the top.**

- **Restructure (17:00–17:45Z).** `docs/SUPPLEMENT.md` created (S1 Supplementary Methods, S2 the reader's
  transcript, S3 Tables S1–S6, S4 Tables S7–S10 and the linkage flow, S5 Figures S1–S6, S6 the record); the
  paper's Results rewritten as prose from the sealed files with a claim per number; four display items; new
  generators and the paste tool with named regions; `V.paper_budget` (W1) added and defeat-tested; gate 91/91
  twice. The Obsidian vault left the repository (`6ace8f5`, `d56852e`) at the user's request.
- **Referee panel (wf_a3619d51-50e).** Five lenses, ten comments each, every major/moderate comment fact-checked
  by a separate agent against the sealed files (41 of 47 ran; the fact-checks caught two suggested rewrites that
  would themselves have been wrong — "no coefficient distinguishable from zero" is false for the C1 count arm's
  day 1, and the offered counterfactual sentence mis-stated the day −1 reference — and both were written the
  corrected way). The synthesis stage fell to a usage limit; the disposition of every comment is
  `docs/REFEREE_PANEL_2026-09-21.md`.
- **Fixes applied after the panel returned**, prepared while it ran: intervals (mean ± 1.96 SE, normal
  approximation on the date-clustered SE) beside the verbatim pre-registered reading in Abstract, Results, Table
  1A and Discussion; the C1 path described from `path_coefs` (positive days 0–2 and 4, negative 3 and 5–7; no
  share-arm interval excludes zero; the count arm agrees in sign on seven of eight days, day 1 the only
  coefficient whose interval excludes zero); the two guards outcome by outcome; the within-period family of four
  (0.028, 0.028, 0.038; 0.0895) with the period-level reading unchanged; both diagnostics by coefficient; the
  count arm as a rate on the same denominator; the dose-response arm including discovery (−0.00017, p 0.768);
  the identifying assumption; the certification scope; the two mismatches behind the bound with Table S10's new
  randomization-MDE column; Kang cited for B-HEARD's direction, the mechanism attenuation, Curtis as the closest
  antecedent, Nix & Lozada on Bor; Limitation 2 (citywide average); implications; plain language throughout;
  Table S6 embedded; captions rewritten; front matter in place of the drafting note. Every new number is a hand
  claim computed by the same expression its prose was rendered from (`rf_paper.py` in the session scratchpad).
- **Budget.** Six trim passes brought the main text from 6,284 words after the additions to 4,998; the
  exploratory discovery estimates moved verbatim to S1.10 (their 25 claims re-pointed); Limitation 11 (the
  non-blind changes, already in Deviations and Limitation 10) folded away. The venue's ~4,000 is an author
  decision now: the remaining words are substance the panel asked for.
- **Gate.** `V.manuscript_referee_tokens` (RP1–RP6); the exhibits check skips the `episode_table` region;
  `V.table1_regenerates` compares the supplement's copy; baseline refreshed; 92/92 twice. Register 1,582 claims;
  findings 171. Commit `d999d84`, pushed.
- **Lessons.** A whitespace-tolerant replacer (tokens joined by `\s+`) is the right tool for editing prose that
  was wrapped by hand; a span captured as `t[a:j - len(marker)]` when `j` is the marker's start truncates the
  tail (caught by a claim that failed to reproduce: the discovery text lost its last sentence); a table header
  that begins with a numeral ("95% interval") is a value to the exhibits check.

**2026-09-21 ~05:30Z — CP3 complete; the manuscript is finished to the extent the assistant can finish it. See the Status block at the top.**

- **The full CP3 audit** (wf_0df7b965-8dc, 39 agents at two concurrent, 03:36–05:15Z)
  on the committed manuscript: 61 raw findings from eight finders, 57 unique, the
  ten highest refuted by three lenses (5 survived), a completeness critic (6).
  The refuters killed five of the ten on materiality or novelty (the
  family-correction factor, "nor the opposite", the MDE-vs-test limitation, the
  Table 5 caption, the external-deposit disclosure); each was nonetheless applied
  where it made the text more exact, because the cost was a sentence.
- **What the paper had wrong about the record** (the five that survived): it
  called F1 and F2 metadata reads and F3 a coverage read when all three read
  outcome values; it said the strata were never used for a specification choice
  (F2's EDPM decision; F4's weights); it said no number from the incidents was
  kept (the F4 weights are in the B-HEARD exposure covariate); it said everything
  was committed before any confirmation outcome was seen (F1–F3 precede the
  commitments); it claimed the compositional damping biases toward the null (it
  runs in the predicted direction). All rewritten from CONFIRMATION_PLAN §15 and
  PAPER_MASTER §5.3 and held by suite tokens (P59–P63).
- **What the critic added**: the outcome definition omitted the disposition
  filter; H2/H3 were never run and the Limitations had dropped the note's own
  item on it; RECORD 6.1/6.2 overstated the code listing and omitted the four
  undocumented EDP codes; the display items were never cross-referenced; the
  Nix & Lozada answer (no armed status used) was never given. All fixed.
- **Tables and figures**: the nine pooled falsification and diagnostic cells the
  generator had dropped are in Table 4 / 8b.3; IDENTICAL is defined by the sealed
  table's three reasons; the pooled dose rows are marked descriptive; the
  generated claims were regenerated wholesale (1,128) and the register holds
  1,354 claims, all verifying. Figure 2's axis is in SD units; Figure 3 is drawn
  from the joint specification the Results report, without printed p-values.
- **Prepared while the refuters ran, applied after they finished**, so the
  refuters judged the text the finders saw; dry-run on copies first (every anchor
  asserted once). Two mechanical lessons: a Monitor filter that embeds python in
  a single-quoted string silently prints nothing (keep monitor scripts to grep and
  cut); a mechanical label rename can splice into prose ("60 dayss").
- **Committed `663153d`**, pushed; gate 90/90 twice before, twice after the
  close-out edits.

**2026-09-21 ~04:00Z — Phase I sealed and read; the manuscript's confirmatory sections written from the reading. See the Status block at the top.**

- **The run, 09:29:42Z → 03:24:13Z.** After the second OOM kill (20:17Z, a
  worker at 4.96 GB on the pooled stratum's 60-day cells under three workers) the
  pool ran two workers to the end; the last cells were the pooled 60-day windows.
  30 sealed the table (166 cells; 157 estimated, 9 identical to the primary by
  construction), wrote the sidecar (raw source hashes, input hashes, commit
  b046fb6, hash seed 0) and the run log's `sealed` row with the table's hash; 34
  read it once and sealed the reading to it (175 rows). Committed `34d4b9e`.
  Every one of the seven starts is a run-log row; the hand relaunches carry the
  reason given at the time (suspension, fewer workers after each OOM kill, three
  workers for speed), the two automatic retries repeat the reason of the start
  they retried, and the original start carries none; the sealed table's
  `overwrite_reason` column carries the last reason only, which §8b and Methods
  say.
- **The reading is the pre-specified null in both strata** (PAN 9.4 row 5,
  addendum §19 rule 2). C1 and C2 "does not reject" after BH over the family of
  eight; a sustained shift at or above the pre-freeze MDE (0.01156 / 0.00875) is
  disfavoured at 80% power; the MEI −0.005 is not excluded; the transient
  dip-and-rebound of the MEI is disfavoured (0.00382 / 0.00290); placebos quiet.
  Reported because the plan requires it and read as no more than the plan
  allows: C1's smallest unadjusted p 0.0115 and 14 of 24 sensitivity cells at
  p ≤ 0.05; C1's dose-response arm positive (asymptotic p 0.0309 / 0.0187) —
  against the predicted decline, outside the family, descriptive. C2: 0 of 30
  sensitivity cells; no movement on the dose or B-HEARD-interaction arms.
  Pooled: does not reject on both arms (descriptive).
- **The paste.** `ops/phase_i_tables.py --docs docs/PAPER_MASTER.md docs/PAPER.md`
  → `tables.md` (8b.1–8b.5), `prose.md` (the reader's sentences, each a claim
  anchored on its prefix), `claims.csv` (1,056 rows, per-document ids);
  `paste_phase_i.py` inserted §8b before §9 and PAPER.md's confirmatory Results
  (Tables 2–6). §8b's introduction and Methods' seal paragraph state the seven
  starts with the run log as the record. Discussion's two pending paragraphs and
  the Abstract were written from the reading's sentences only (C1300–C1306 hold
  their numbers); the two PHASE I PENDING markers and the abstract's drafting
  note removed; the Abstract cut to PAPER_PLAN's specification (250 words,
  unstructured, dataset/place/period/linkage/design/three-way question).
- **Gate.** The first run on the pasted documents failed two checks:
  `V.claims_reproduce` — C161's anchor "precinct-level report (31 precincts" had
  gained the citation marker ¹² when the IBO reference was added — and
  `V.claims_cover_exhibits` — 48 cells whose label "28-day post window" starts
  with a numeral, which the cell rule reads as a value needing a claim. Both
  mechanical: the template now carries the marker; the labels are "post window
  28 days" / "post window 60 days" in the generator, both documents and the
  register (the regenerated `claims.csv` matches the register's 1,056 rows on
  template, expression and document). Then 90/90 twice, and twice again after
  the Abstract. Committed `bbbe1e2` (paper, master, register, generator) and
  `01dabeb` (vault, graph, capsule); pushed.
- **CP3, full audit launched** (wf_0df7b965-8dc) on the committed manuscript:
  eight attack classes, three-lens refuters, completeness critic; the prompts
  written before the run finished described one resume and were corrected to
  the seven starts before launch. The Phase I fallback check-in trigger was
  deleted (the run it guarded is sealed).
- **Word budget, for the author**: main text about 7,086 words excluding
  tables, Methods about 3,465, against ~4,000 for the venue. The proposal
  stands: Methods' estimator, randomization, calibration and sensitivity detail
  to a Supplementary Methods, the main text keeping the design, the freeze, the
  family and the reading rules. Nothing numeric moves without its claim.

**2026-09-20 ~06:20Z — CP2's last two lines are compute; the specification is closed. See the Status block at the top.**

What happened since the week-long suspension lifted at 03:42Z, in order: the
runners were relaunched from `ops/`; the discovery certificate reached 1,000
simulations (05:10Z: rejection 0.045, KS p 0.2944, CALIBRATED) and the §7.4
numbers moved through the claims; two cold passes were byte-identical on every
build and model output (04:55Z; the manifest is committed at `fa4656f`); the
third adversarial audit of the specification completed (wf_f524dc75: 8 finders,
57 raw findings, 3-lens refuters on the ten highest, a completeness critic) and
every surviving item was fixed blind as P27–P58 (addendum §30; rules 23.1c/d/e;
the sealed run's run log, hash-seed requirement, certificate-vs-design gate,
14-day draw geometry for the window cells, unfiltered diagnostics, cross-window
coverage-clean and geocoding-only cell, cancelled-inclusive and no-EDPM cells on
both arms, day-by-day path columns, pinned sidecars; the reader sealed, on the
tracked pre-freeze power table, with the sensitivity set enumerated, the pooled
and secondary arms read and the placebo check unable to fail open; the record
corrected where it contradicted the code); the panel gained eight columns with
every existing column byte-identical; the dry run was re-stamped on the final
code (166 cells; sidecar hashes match every source); the gate ran clean twice at
90 checks with every new check defeat-tested; `ops/phase_i_tables.py` now also
renders the confirmatory Results prose as the reader's own sentences, each held
by a claim (`prose.md`; 18 quoted sentences verify on the synthetic reading).
Committed and pushed at `0eaf45d`.

- **In flight** (relaunch from `ops/` after any restart): `calib1000.sh` (C2 at
  1,000 since 05:15Z, ~3 sims/min under contention); `coldrun.sh` (two passes
  relaunched 05:57Z because the build changed; the manifest and the registers it
  rewrites are committed when the passes agree).
- **Then, in order**: C2's certificate → §7.4's C2 row and the "discharged at"
  sentence, PAPER.md's calibration prose → gate clean, baseline → the lift commit
  (`FREEZE_ACTIVE = False`, one line; PAPER_MASTER §5.3 already says what it
  forecloses) → `ops/phase_i.sh` (30 at 2,000 draws with the run log, then 34
  once) → `ops/phase_i_tables.py --docs docs/PAPER_MASTER.md docs/PAPER.md` →
  PAPER_MASTER §8b and PAPER.md's confirmatory Results (the quoted reading and
  the tables), Discussion and Abstract → CP3 → HANDOFF.
- **Phase I started 09:29:42Z and was suspended with the container at 09:36:54Z**,
  five minutes after the session went idle (compute advances only while a
  session is active — the rule above, met again). Relaunched 10:34:50Z through
  `ops/phase_i.sh` with `PHASE_I_RESUME_REASON`, which passes 30 the
  `--overwrite-sealed-result` reason a second real start requires (P27); the
  reason is in the run log's second start row and will be in every row of the
  sealed table; every cell resumed from its identity-keyed ledger (2,000, 2,000,
  1,183, 1,194, 62, 62 banked draws verified), so no number depends on the
  restart. The run is now babysat from an active session (Monitor cycles).
- **13:48:00Z: the process pool was killed by the memory cgroup** (OOM: one of
  four workers reached 3.9 GB on the pooled stratum's cells; `dmesg` records the
  kill). The runner's automatic retry (run-log start row 3, 13:48:34Z, four
  workers again) was stopped by hand at 13:49Z and the run relaunched at
  13:50:30Z with `PHASE_I_JOBS=2` and the reason (start row 4): parallelism
  changes no number, every cell being seeded from its own identity and banked in
  its own ledger. Slower, but within memory. Lesson filed in the handoff: the
  stop command greps for the worker processes by a bracketed pattern; a grep for
  the script's own name in a command whose text contains it kills the shell
  running it (the `pgrep -f` lesson in another form).
- **CP3, blind half (wf_f6cc235c, 15:24–16:35Z)**: five finders on the parts of
  the manuscript that do not depend on the confirmatory result, three-lens
  refuters, a critic; 38 raw, 9 confirmed (all in PAPER.md's account of the
  record: the Methods counted three freeze breaches and said none entered a model;
  Limitation 10 called the test-window change blind; the anchor-shift null was
  described as a rigid shift and the two schemes as identical on one block; the
  calibration paragraph said "the full estimator" was certified; the family and
  the Introduction called everything pre-specified without the §14 exceptions), 8
  critic items (fig3/fig4 titles asserting a decline the discovery result does
  not show; Figure 1–3 captions describing other figures; the decomposition's
  dimensions misstated; heterogeneity called pre-specified and announced as
  reported; RECORD 6.2 and reference 13 resting on unread sources; six references
  uncited; the main text over the venue's word budget). Every item but the word
  budget fixed in PAPER.md and 08_figures.py (titles neutralised, tracked
  figures refreshed) with the gate clean; the word budget (about 6,200 words
  before the references, Methods about 3,200) is left for the author's editorial
  pass after the Results and Discussion are written.
- **15:23:54Z: relaunched with three workers** (start row 5) while the run is on
  C2's cells: two workers held 1.9 and 2.6 GB with 9.7 GB free, and at two
  workers the remaining C2 and pooled cells projected to more than twenty hours.
  If the pooled cells push a worker past the cgroup again, back to two.
- **20:17:13Z: second out-of-memory kill** (a worker at 4.96 GB on the pooled
  stratum's 60-day cells under three workers; `dmesg`). The automatic three-worker
  retry (start row 6) was stopped by hand at 20:19Z and the run relaunched
  20:19:25Z with two workers and the reason (start row 7). 108 distinct cells were
  banked at the kill; the pooled stratum's remaining cells run at two workers to
  the end.
- **The lift (09:2xZ)**: C2 certified at 1,000 (0.054 / 0.8221); §7.4 updated;
  `FREEZE_ACTIVE = False`; the gate run to verify the lifted state found three
  suite checks (S7, S8, X6) selecting the confirmation sample — the suite had
  been exempt from D8's scan — and X.bheard_wired FAILED on it. Recorded as
  incident F5 (addendum §15, PAPER_MASTER §5.3, register F5): the checks printed
  a shared-days count (0), a residual AR(1) (0.0622 vs 0.0482) and a coefficient
  difference (6.117e-05); nothing of H1. The three checks are pinned to the
  discovery window and episodes, the suite is scanned by D8 (defeat-tested), and
  the flag was committed only after the gate ran clean lifted.
- **Cold passes on the eight-column panel**: two passes 05:57–06:10Z, every
  build and model output byte-identical (COLD IDENTITY OK; the three differing
  files are the check stages' timestamped reports). `coldrun.sh`'s clear now
  also keeps the reader's dry run (`confirmatory_reading_dryrun*`), which it had
  been deleting; `34 --synthetic` regenerates it in seconds.
- **Lifted**: `FREEZE_ACTIVE` is False since the lift commit of 2026-09-20; before
  it no confirmation outcome had entered a model or test except as F5 records.

**2026-09-13 ~21:50Z — CP2 in its last stretch; compute is the clock. See the Status block at the top.**

What happened since 17:45Z, in order: C1 certified at 1,000 simulations under the
corrected drawer (20:56Z; P1, P5, RI3, P12, P13 closed; addendum §25 not invoked);
the discovery 1,000-sim run started twelve seconds after a cold pass cleared the
panel and calibrated a null on assumed noise until the ledger identity check
exposed it — killed, restored, restarted on the panel, and 18 now refuses to run
without the panel (N11, `S.calibration_noise_measured`); the reading of the
sealed result was made code (`34_confirmatory_reading.py`, addendum §23.4a,
`S.confirmatory_reading_rules` on 13 planted tables) and the Phase I runner and
table generator were written and tested on the synthetic dry run; Table 1 is
generated and held by re-rendering (`V.table1_regenerates`); and, while preparing
the lift commit, the guard was found to derive every caller's window from the
flag, so the lift would have moved every exploratory script onto the sealed
sample — fixed by naming the window at every call (D8, addendum §26,
`D.discovery_scripts_pinned`). Gate 87 checks; findings 116/116 fixed; every
non-PASS is artifact-pending on the cold passes.

- **In flight** (relaunch from `ops/` after any restart): `calib1000.sh`
  (discovery 1,000 since 21:09Z, ~3 sims/min under contention, then C2);
  `coldrun.sh` pass 1 (17 at 2,000 draws on the six cells, the narrow-MH cells
  still to bank; then 05/03/04/06/07/08/33/25 and 31/23/22), then pass 2 with
  every ledger banked, then the manifest comparison.
- **Then, in order**: gate clean twice with the baseline refreshed → `outputs/run_manifest.json`
  committed → 1,000-sim certificates on discovery and C2 → the lift commit
  (`FREEZE_ACTIVE = False`, one line) → `ops/phase_i.sh` (30 at 2,000 draws,
  `--jobs 4`, then 34) → `ops/phase_i_tables.py` → PAPER_MASTER §8b and the
  PAPER.md Results, Discussion and Abstract → CP3.
- **Untouched**: `FREEZE_ACTIVE` is True. No confirmation outcome has entered a
  model or test; the declared accesses are the ones §5.3 lists.

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
