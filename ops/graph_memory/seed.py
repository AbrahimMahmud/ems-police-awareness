"""Seed the memory graph with this project's standing knowledge. Idempotent: node ids
are derived from (type, text), so re-running updates trust/citations and adds nothing
twice. Run after each session's decisions land, then export to docs/graph/.

    python3 -m graph_memory.seed && graph-memory export ../docs/graph/graph_memory.jsonl
"""
from __future__ import annotations

from .core import DEFAULT_DB, Graph

SESSION = "claude-code 2026-09-13/20 (analysis-rework)"

INTENT = [
    (1.0, "Question: does public attention to police violence (CAI-D index: Wikipedia pageviews + Google Trends, article basket of police-violence victims) change the share of NYC EMS dispatches that are mental-health (EDP) calls across the 59 community districts? Design: stacked episode event study, episode-level randomization inference, a discovery/confirmation split with a sealed confirmation sample.", ["docs/PAPER_MASTER.md:1", "docs/PRE_ANALYSIS_NOTE.md:1"]),
    (1.0, "Deliverable: a Markdown manuscript in the repository (docs/PAPER.md) with the repository at CP3, on branch analysis-rework, commits authored by Abrahim Mahmud with no AI attribution.", ["docs/EXECUTION_PLAN.md:40"]),
]
DECISIONS = [
    (1.0, "2026-09-13 (user): continue to Phase I (the sealed confirmatory run) as pre-registered, with the reading of a non-rejection fixed in advance against the measured power (addendum 19).", ["docs/CONFIRMATION_PLAN.md:468", "docs/EXECUTION_PLAN.md:40"]),
    (1.0, "2026-09-13 (user): work on branch analysis-rework with no AI attribution; commits authored Abrahim Mahmud <abrahimm1205@gmail.com>; push to origin analysis-rework.", ["docs/EXECUTION_PLAN.md:40"]),
    (1.0, "2026-09-13 (user): the O2 coverage diagnostic is disclosed first (addendum 18), then run as a declared, logged access.", ["docs/CONFIRMATION_PLAN.md", "data/reference/freeze_access_log.csv"]),
    (0.95, "2026-09-13: addendum 25 — if a stratum's null fails calibration at 1,000 simulations, the sealed run proceeds with that stratum flagged UNCERTIFIED_NULL (p = 1 in the family; asymptotic p as its labelled inference). Written before the 1,000-sim verdict; not invoked (C1 calibrated at 1,000).", ["docs/CONFIRMATION_PLAN.md:788", "commit:32492a3"]),
    (0.95, "2026-09-13: the reading of the sealed result is code (scripts/34_confirmatory_reading.py), a pure function of the sealed table; the paper quotes its output; S.confirmatory_reading_rules holds it to 17 planted tables (addendum 23.4a, 23.1a, 23.1b, 23.3a, 25.3a).", ["scripts/34_confirmatory_reading.py", "commit:93b2d5f", "commit:12da608"]),
    (0.95, "2026-09-13: after the lift only the sealed script reads the confirmation sample; every exploratory script pins the discovery window by name (select_sample(..., window='discovery')); addendum 26, finding D8.", ["scripts/freeze_guard.py", "commit:5124555"]),
    (0.9, "2026-09-13: the placebo override (addendum 23.4) is cardiac and asthma; injury is estimated and reported but does not override, because the discovery decomposition found injury responds to attention episodes (protest injuries).", ["docs/CONFIRMATION_PLAN.md", "commit:29ac33f"]),
    (0.9, "2026-09-13: the sealed script also estimates the pre-specified 28- and 60-day windows (sens_post28/60) and the dose-response arm (secondary, asymptotic p) — addendum 29, finding P19.", ["scripts/30_confirmatory_run.py", "commit:12da608"]),
    (0.9, "2026-09-20: the discovery randomization p-values in PAPER_MASTER 8 and PAPER.md are the 2,000-draw values (moved from the 500-draw first pass by the claim updater; prose says 2,000 draws).", ["commit:bbd146a"]),
]
RULES = [
    (1.0, "Every change passes the regression gate (scripts/23_regression_suite.py, run twice) before the next; artifact-pending failures are documented in EXECUTION_PLAN; every new check gets a defeat attempt; the baseline is refreshed in the same commit.", ["docs/EXECUTION_PLAN.md:394"]),
    (1.0, "No number reaches the paper without a CLAIMS_REGISTER.csv entry that reproduces it (V.claims_reproduce, V.claims_cover_exhibits); generated tables are held by re-rendering instead (V.table1_regenerates).", ["docs/CLAIMS_REGISTER.csv", "scripts/31_verify_sources.py"]),
    (1.0, "FREEZE: no script reads confirmation-window outcomes (2015-07..2016-12, 2021..2024) except declared accesses in config.FREEZE_EXEMPTIONS, logged to freeze_access_log.csv, and the sealed 30_confirmatory_run.py after config.FREEZE_ACTIVE = False. data/reference/confirmation_episodes.csv stays byte-identical.", ["scripts/freeze_guard.py", "docs/PAPER_MASTER.md:1108"]),
    (1.0, "Register CSVs use CRLF row terminators; edit with the csv module (lineterminator='\\r\\n'), never by hand.", ["docs/AUDIT_FINDINGS.csv"]),
    (1.0, "Poll long jobs by PID file or sentinel; never pgrep -f / pkill -f with a pattern that appears in your own command line (it kills the shell). Compute advances only while the session is active; runners live in ops/ and are relaunched blind after any restart.", ["ops/README.md"]),
    (0.9, "The legacy lag-7 result is superseded and is never restated as established; methods are not adjusted to recover any result; specification changes after the lift are not made.", ["docs/PRE_ANALYSIS_NOTE.md:348"]),
]
FINDINGS = [
    (0.95, "N11 (2026-09-13 21:08Z): 18_null_calibration.py fell back to assumed noise parameters when the panel was absent; a 1,000-sim discovery certificate on rho=0.6 was 25 sims in when the ledger identity check (N7) exposed it. Fixed: 18 refuses without the panel; S.calibration_noise_measured.", ["docs/AUDIT_FINDINGS.csv", "commit:93b2d5f"]),
    (0.95, "D8 (2026-09-13 21:40Z): lifting the freeze would have switched every exploratory script onto the confirmation sample. Fixed by the window= argument on the guard and D.discovery_scripts_pinned.", ["commit:5124555"]),
    (0.9, "P19–P26 (second CP2 specification audit, one finder completed): windows/dose arm not estimated; one-arm and opposite-sign readings; uncertified asymptotic reading; denominator precedence; anchor-shift misdescribed (gaps permuted); inferential structure unnumbered; row-1 common outcome; 30's docstring stale. All fixed before the lift.", ["commit:12da608", "commit:20c6265"]),
    (0.9, "C1 CALIBRATED at 1,000 sims under circular_within_block_fw7 (rejection 0.049, KS p 0.993); discovery and C2 200-sim certificates CALIBRATED, being extended to 1,000; pooled 200 CALIBRATED.", ["outputs/tables/null_calibration_C1.csv", "docs/PAPER_MASTER.md:1236"]),
    (0.9, "Power (pre-freeze, 19_power.py): every stratum is UNDERPOWERED for a sustained −0.005 shift (MDE/MEI 1.75–2.31) and adequately powered for a transient dip-and-rebound; the bounded-null reading is fixed by addendum 19 rule 2.", ["outputs/tables/power_analysis.csv", "docs/PAPER_MASTER.md:1384"]),
]
PROVENANCE = [
    (1.0, "Branch analysis-rework, commits 2026-09-13/20: ed8a883 … 20c6265, bbd146a (gate clean 87/87, 206/206 claims). Handoff base e541632.", ["commit:bbd146a"]),
    (0.9, "Regression gate: 87 checks (docs/regression_baseline.csv); findings register 124 rows, all fixed; claims register 206 rows, all verified at 2026-09-20 03:50Z.", ["docs/regression_baseline.csv", "docs/AUDIT_FINDINGS.csv", "docs/CLAIMS_REGISTER.csv"]),
    (0.9, "Environment: this container was suspended 2026-09-13 22:40Z → 2026-09-20 03:42Z on the usage limit; filesystem intact, processes gone; runners relaunched from ops/.", ["docs/EXECUTION_PLAN.md:40"]),
]
OPEN = [
    (0.8, "The Registered Report route (PAPER_MASTER 10, supervisor decision) is foreclosed by running Phase I; stated to the user on 2026-09-13.", ["docs/PAPER_MASTER.md:1793"]),
    (0.8, "The second specification audit's other seven finders, refuters and critic did not run (session/model usage limits); a third run with the Opus model was launched 2026-09-20 03:50Z (wf_f524dc75-8a5).", ["docs/EXECUTION_PLAN.md"]),
    (0.7, "Local tooling on the user's Mac (context-capsule, ems-graph-memory MCP, ems-duckdb MCP, Obsidian vault at ~/Downloads/abrahimm/EMS, uv.lock) is not in the repository; repo-tracked equivalents were built 2026-09-20 (ops/graph_memory, ops/context_capsule.py, vault/, pyproject.toml) — they need reconciling with the Mac copies.", ["docs/LOCAL_SETUP.md"]),
]
NEXT = [
    (0.9, "1. Cold passes 1 and 2 match (ops/coldrun.sh) → commit outputs/run_manifest.json and the registers the cold run rewrites.", ["ops/coldrun.sh"]),
    (0.9, "2. Discovery and C2 certificates at 1,000 sims (ops/calib1000.sh; discovery resumed at 719/1000 on 2026-09-20 03:43Z, then C2 from 200) → S.lift_requires_1000_sims satisfied → gate clean → baseline.", ["ops/calib1000.sh"]),
    (0.9, "3. The lift: config.FREEZE_ACTIVE = False in one greppable commit; then ops/phase_i.sh (30 at 2,000 draws, --jobs 4; then 34) → data/reference/confirmatory_results.csv and confirmatory_reading.csv.", ["ops/phase_i.sh", "scripts/config.py:627"]),
    (0.9, "4. ops/phase_i_tables.py → PAPER_MASTER 8b and PAPER.md Results (tables + claims), Discussion, Abstract; figures into docs/figures; CP3 audit; EXECUTION_PLAN session log.", ["ops/phase_i_tables.py", "docs/PAPER.md"]),
]


def seed(db=DEFAULT_DB):
    g = Graph(db)
    ids = {}
    for ntype, items in (("intent", INTENT), ("decision", DECISIONS), ("rule", RULES), ("finding", FINDINGS),
                         ("provenance", PROVENANCE), ("open_question", OPEN), ("next_action", NEXT)):
        for trust, text, cites in items:
            ids.setdefault(ntype, []).append(g.add(ntype, text, trust, cites, SESSION))
    # a few edges that carry meaning
    for a in ids["next_action"][1:]:
        g.link(a, "follows", ids["next_action"][ids["next_action"].index(a) - 1])
    g.link(ids["decision"][0], "cites", ids["finding"][4])          # continue to Phase I cites the power finding
    g.link(ids["finding"][1], "supports", ids["decision"][5])        # D8 supports the pinning decision
    return g, ids


if __name__ == "__main__":
    g, ids = seed()
    print({k: len(v) for k, v in ids.items()}, "->", g.path)
