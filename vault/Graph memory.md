---
tags: [graph, index]
nodes: 51
edges: 20
---

# Graph memory

Rendered from `docs/graph/graph_memory.jsonl` by `python3 -m graph_memory.obsidian` (run from `ops/`; see [[Tooling]]). 51 nodes (48 current, 3 superseded), 20 edges. Each node is a note under `Graph/`; its edges are wikilinks, so Obsidian's graph view is the memory graph. Node texts are rendered with result values replaced by a marker (vault rule: no unpublished results); the cited artifact holds the value. Superseded nodes are listed under their type, struck through.

Related: [[00 Project]] · [[Decisions]] · [[Status]] · [[Lessons]] · [[Timeline]]

## Intent

- [[int_e3e19a4370]] — Question: does public attention to police violence (CAI-D index: Wikipedia pageviews + Google Trends, article basket of police-violence vict
- [[int_1488070d80]] — Deliverable: a Markdown manuscript in the repository (docs/PAPER.md) with the repository at CP3, on branch analysis-rework, commits authored

## Decisions

- [[dec_d0fd80ead0]] — 2026-09-13 (user): continue to Phase I (the sealed confirmatory run) as pre-registered, with the reading of a non-rejection fixed in advance
- [[dec_613460fc4e]] — 2026-09-13 (user): work on branch analysis-rework with no AI attribution; commits authored Abrahim Mahmud <abrahimm1205@gmail.com>; push to 
- [[dec_fe00afa1e9]] — 2026-09-13 (user): the O2 coverage diagnostic is disclosed first (addendum 18), then run as a declared, logged access
- [[dec_3732c36bbd]] — 2026-09-13: addendum 25 — if a stratum's null fails calibration at 1,000 simulations, the sealed run proceeds with that stratum flagged UNCE
- [[dec_d034901957]] — 2026-09-13: the reading of the sealed result is code (scripts/34_confirmatory_reading.py), a pure function of the sealed table; the paper qu
- [[dec_22441645da]] — 2026-09-13: after the lift only the sealed script reads the confirmation sample; every exploratory script pins the discovery window by name 
- [[dec_8dcde14a5c]] — 2026-09-13: the placebo override (addendum 23.4) is cardiac and asthma; injury is estimated and reported but does not override, because the 
- [[dec_e4cf5f6cb8]] — 2026-09-13: the sealed script also estimates the pre-specified 28- and 60-day windows (sens_post28/60) and the dose-response arm (secondary,
- [[dec_2b6f67ee03]] — 2026-09-20: the discovery randomization p-values in PAPER_MASTER 8 and PAPER.md are the 2,000-draw values (moved from the 500-draw first pas
- [[dec_357147b3d6]] — Remediate every surviving third-pass finding before the lift, in code where the seal or the reading could otherwise be defeated (run log, ha
- [[dec_7c12f79546]] — Lift the confirmation freeze on 2026-09-20 (FREEZE_ACTIVE = False, one commit) after all three inferential strata certified at 1,000 sims an
- [[dec_5f799ecaa5]] — Phase I's seven starts (suspension 09:36Z, OOM kills 13:48Z and 20:17Z, worker-count changes) are disclosed in the run log, the sealed table

## Rules

- [[rul_2b17b4c4b2]] — Every change passes the regression gate (scripts/23_regression_suite.py, run twice) before the next; artifact-pending failures are documente
- [[rul_775b4f70ec]] — No number reaches the paper without a CLAIMS_REGISTER.csv entry that reproduces it (V.claims_reproduce, V.claims_cover_exhibits); generated 
- [[rul_b9109de5e3]] — FREEZE: no script reads confirmation-window outcomes (2015-07..2016-12, 2021..2024) except declared accesses in config.FREEZE_EXEMPTIONS, lo
- [[rul_e92e530bd5]] — Register CSVs use CRLF row terminators; edit with the csv module (lineterminator='\r\n'), never by hand
- [[rul_2bc5eaad61]] — Poll long jobs by PID file or sentinel; never pgrep -f / pkill -f with a pattern that appears in your own command line (it kills the shell)
- [[rul_07297b17af]] — The legacy lag-7 result is superseded and is never restated as established; methods are not adjusted to recover any result; specification ch
- [[rul_6cfef9d926]] — The lift forecloses the external pre-registration remedy for F1–F4; PAPER_MASTER §5.3 says so, and records that proceeding to Phase I on the
- [[rul_44eeea12cd]] — Table labels never begin with a numeral (V.claims_cover_exhibits treats a numeral-leading cell as a value needing a claim); the sealed run's
- [[rul_c4760800ce]] — When the paper paraphrases the record, use the record's own nouns and hold the wording with a suite token
- [[rul_05a5f5c147]] — The vault (vault/) is organised as a hub (00 Project) plus topic notes (Design, Data inventory, Pipeline, Record, Freeze incidents, Phase I,

## Status snapshots

- [[sta_7871942417]] — 2026-09-21 05:30Z: CP3 done
- ~~[[sta_6b8b4d4043]] — 2026-09-20 05:55Z: gate 90/90 twice, baseline refreshed, 206/206 claims; discovery certified at 1,000 sims (⟨value: see the cited artifact⟩,~~ (superseded by [[sta_7a67a4d68a]])
- ~~[[sta_7a67a4d68a]] — 2026-09-21 03:50Z: Phase I sealed 03:24:13Z (166 cells, 2,000 draws, seven start rows with reasons); reading = the pre-specified null in bot~~ (superseded by [[sta_7871942417]])

## Findings

- [[fin_803c04bebd]] — N11 (2026-09-13 21:08Z): 18_null_calibration.py fell back to assumed noise parameters when the panel was absent; a 1,000-sim discovery certi
- [[fin_e23b6b5ddc]] — D8 (2026-09-13 21:40Z): lifting the freeze would have switched every exploratory script onto the confirmation sample
- [[fin_337bd8252d]] — P19–P26 (second CP2 specification audit, one finder completed): windows/dose arm not estimated; one-arm and opposite-sign readings; uncertif
- [[fin_8626188210]] — C1 CALIBRATED at 1,000 sims under circular_within_block_fw7 (rejection ⟨value: see the cited artifact⟩, KS p ⟨value: see the cited artifact⟩
- [[fin_3a68582349]] — Power (pre-freeze, 19_power.py): every stratum is UNDERPOWERED for a sustained ⟨value: see the cited artifact⟩ shift (MDE/MEI 1.75–2.31) and
- [[fin_4479d754b1]] — X20 (2026-09-20 04:07Z): two cold passes with banked ledgers differed at the byte level in 17's and 25's tables (coefficients 1e-16, cluster
- [[fin_3d16193e93]] — Third CP2 specification audit (wf_f524dc75): 57 raw findings, 5 confirmed, 5 killed, 6 critic items; filed as P27–P58 in addendum §30 with r
- [[fin_3c9011f63a]] — F5 (2026-09-20, at the lift): the first gate run with FREEZE_ACTIVE=False selected the confirmation sample in three suite checks (S7 shared-
- [[fin_0c1f3069c5]] — Confirmatory reading (sealed 2026-09-21): bounded null in C1 (clean) and C2 (B-HEARD-exposed)
- [[fin_038e9c9ba8]] — CP3 survivors (P59-P63): PAPER.md called F1/F2 metadata reads and F3 a coverage read (all read outcome values); said the strata were never u

## Provenance

- [[pro_583ee5caf2]] — Branch analysis-rework, commits 2026-09-13/20: ed8a883 … 20c6265, bbd146a (gate clean 87/87, 206/206 claims)
- [[pro_1111e891a5]] — Regression gate: 87 checks (docs/regression_baseline.csv); findings register 124 rows, all fixed; claims register 206 rows, all verified at 
- [[pro_899c12d9df]] — Environment: this container was suspended 2026-09-13 22:40Z → 2026-09-20 03:42Z on the usage limit; filesystem intact, processes gone; runne
- [[pro_b1e397a543]] — 2026-09-20 04:36Z: two deterministic cold passes (PYTHONHASHSEED=0) — COLD IDENTITY OK, every build and model output byte-identical; only th

## Open questions

- [[ope_46faa49046]] — The Registered Report route (PAPER_MASTER 10, supervisor decision) is foreclosed by running Phase I; stated to the user on 2026-09-13
- [[ope_f8aece8864]] — The second specification audit's other seven finders, refuters and critic did not run (session/model usage limits); a third run with the Opu
- [[ope_bebb2939e2]] — Local tooling on the user's Mac (context-capsule, ems-graph-memory MCP, ems-duckdb MCP, Obsidian vault at ~/Downloads/abrahimm/EMS, uv.lock)

## Next actions

- [[nex_7e08fc52d7]] — 1
- [[nex_50c24f7f8e]] — 2
- [[nex_d084c112cf]] — 3
- [[nex_7fa4aafe82]] — 4
- [[nex_5634eecce9]] — When C2's 1,000-sim certificate lands: S.lift_requires_1000_sims satisfied → update PAPER_MASTER §7.4 (all four rows) and PAPER.md calibrati
- [[nex_110b74fcf0]] — Author's editorial pass on docs/PAPER.md: Methods detail to Supplementary Methods, Tables 4-6 to Supplementary Tables, nine display items to
- ~~[[nex_14c7208cc4]] — CP3 full manuscript audit (8 finders, 3-lens refuters, critic) on the completed PAPER.md; then EXECUTION_PLAN status/session log, HANDOFF_20~~ (superseded by [[nex_110b74fcf0]])
