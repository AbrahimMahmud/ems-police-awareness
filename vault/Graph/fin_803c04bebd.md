---
id: fin_803c04bebd
type: finding
trust: 0.95
created: 2026-09-20T04:03:03+00:00
session: "claude-code 2026-09-13/20 (analysis-rework)"
superseded_by: null
tags: [graph, finding]
---

# fin_803c04bebd

**finding** · trust 0.95

N11 (2026-09-13 21:08Z): 18_null_calibration.py fell back to assumed noise parameters when the panel was absent; a 1,000-sim discovery certificate on rho=0.6 was 25 sims in when the ledger identity check (N7) exposed it. Fixed: 18 refuses without the panel; S.calibration_noise_measured.

**Cites**

- `docs/AUDIT_FINDINGS.csv`
- `commit:93b2d5f`

Index: [[Graph memory#Findings]] · hub: [[00 Project]]
