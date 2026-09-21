---
id: rul_b9109de5e3
type: rule
trust: 1.0
created: 2026-09-20T04:03:03+00:00
session: "claude-code 2026-09-13/20 (analysis-rework)"
superseded_by: null
tags: [graph, rule]
---

# rul_b9109de5e3

**rule** · trust 1.00

FREEZE: no script reads confirmation-window outcomes (2015-07..2016-12, 2021..2024) except declared accesses in config.FREEZE_EXEMPTIONS, logged to freeze_access_log.csv, and the sealed 30_confirmatory_run.py after config.FREEZE_ACTIVE = False. data/reference/confirmation_episodes.csv stays byte-identical.

**Cites**

- `scripts/freeze_guard.py`
- `docs/PAPER_MASTER.md:1108`

Index: [[Graph memory#Rules]] · hub: [[00 Project]]
