---
id: rul_2bc5eaad61
type: rule
trust: 1.0
created: 2026-09-20T04:03:03+00:00
session: "claude-code 2026-09-13/20 (analysis-rework)"
superseded_by: null
tags: [graph, rule]
---

# rul_2bc5eaad61

**rule** · trust 1.00

Poll long jobs by PID file or sentinel; never pgrep -f / pkill -f with a pattern that appears in your own command line (it kills the shell). Compute advances only while the session is active; runners live in ops/ and are relaunched blind after any restart.

**Cites**

- `ops/README.md`

Index: [[Graph memory#Rules]] · hub: [[00 Project]]
