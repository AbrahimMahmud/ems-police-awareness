---
tags: [verification, audits]
updated: 2026-09-21
---
# Adversarial audits

The pattern, each time: finders by failure class (one prompt each, read-only, outcome data forbidden except the
sealed artifacts) → three-lens refutation of the highest findings (literal truth, materiality, novelty; a finding
survives with two votes) → a completeness critic. Findings that survive, and unverified ones that hold on
inspection, are fixed and filed in `docs/AUDIT_FINDINGS.csv` with a check that holds the fix
([[Gate and checks]]). Workflow scripts live in the session scratchpad; the results are in the register and the
execution plan's session log.

| pass | when | scope | raw → filed |
|---|---|---|---|
| CP1 | 2026-09-13 | the confirmatory machinery and the freeze (8 finders) | 60 raw; O2-close, X16, N7–N10, D8 … remediation groups A–E |
| CP2, first and second specification audits | 2026-09-13 | the sealed run's specification before the lift | P19–P26 (addendum §30) |
| CP2, third specification audit | 2026-09-20 (wf_f524dc75) | the sealed run, the reader, the record | 57 raw, 5 confirmed, 5 killed, 6 critic → **P27–P58** (rules 23.1c/d/e; run log, hash seed, design gate, unfiltered diagnostics, both-arms cells, path columns, pinned sidecars; record corrections) |
| CP3, blind half | 2026-09-20 (wf_f6cc235c) | the manuscript's outcome-independent parts | 38 raw, 9 confirmed, 8 critic → fixed in PAPER.md and `08_figures.py` (five incidents, non-blind deviations, figure titles neutralised, citations) |
| CP3, full | 2026-09-21 (wf_0df7b965) | the completed manuscript against the sealed result, its reading, the claims and the record (8 finders: results-vs-reading, numbers-vs-claims, methods-vs-code, record-vs-paper, overstatement, consistency, reproducibility, references-and-display) | 61 raw, 57 unique, 10 refuted → 5 survived, 6 critic → **P59–P63** plus every unverified item that held |

**CP3's five survivors** (all about the paper's account of the record, see [[Freeze incidents]]): F1/F2 called
metadata reads and F3 a coverage read; "never used for any specification choice"; "no number from them was
kept"; "before any confirmation-period outcome was seen"; the compositional damping said to bias toward the
null. **The critic's additions**: the disposition filter absent from the outcome definition; H2/H3 never run and
absent from Limitations; RECORD 6.1/6.2 overstated; display items never cross-referenced; the Nix & Lozada answer
(no armed status used) never given. **Also fixed from the unverified list**: the family-corrected bound beside
the nominal one; the placebo inference withdrawn; the Floyd sentence; the dose arm defined in Methods; three
diagnostic cells; the EDP share named as the power outcome; the run-log rows described as they are; the
reproducibility statement; nine pooled cells restored to Table 4; captions from the sealed table's reasons;
Figure 2's units; Figure 3 from the joint specification; Wu et al. cited for what it measured.

**Method notes.** Fixes are prepared while refuters run and applied only after the workflow returns, so refuters
judge the text the finders saw; a dry run on copies asserts every anchor once. Concurrency here is
min(16, CPUs − 2) = 2, so a 39-agent audit takes about 100 minutes.

Related: [[00 Project]] · [[Record]] · [[Manuscript]] · [[Gate and checks]] · [[Lessons]]
