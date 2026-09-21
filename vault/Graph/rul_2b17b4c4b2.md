---
id: rul_2b17b4c4b2
type: rule
trust: 1.0
created: 2026-09-20T04:03:03+00:00
session: "claude-code 2026-09-13/20 (analysis-rework)"
superseded_by: null
tags: [graph, rule]
---

# rul_2b17b4c4b2

**rule** · trust 1.00

Every change passes the regression gate (scripts/23_regression_suite.py, run twice) before the next; artifact-pending failures are documented in EXECUTION_PLAN; every new check gets a defeat attempt; the baseline is refreshed in the same commit.

**Cites**

- `docs/EXECUTION_PLAN.md:394`

Index: [[Graph memory#Rules]] · hub: [[00 Project]]
