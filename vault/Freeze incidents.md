---
tags: [record, freeze]
updated: 2026-09-21
---
# Freeze incidents F1–F5

Five accesses to confirmation-period outcome data before the sealed run, each disclosed in
`docs/CONFIRMATION_PLAN.md` §15, `docs/PAPER_MASTER.md` §5.3, `docs/PRE_ANALYSIS_NOTE.md` §11.4 and the paper
(Methods, Limitation 9). Register rows F1–F5 in `docs/AUDIT_FINDINGS.csv`; `D.incident_disclosed` holds them.
No value from any of them appears here.

| id | found | what was read | what came of it |
|---|---|---|---|
| F1 | 2026-09-10 | a citywide annual aggregate of the mental-health call share, confirmation years included (an audit agent) | nothing kept; the outcome files gained the guard |
| F2 | 2026-09-11 | the source API: call-type birth dates, whole-period and annual totals, monthly counts across the B-HEARD boundary, precinct-level EDPM counts for June 2021 across the pilot precincts | **a specification decision** — EDPM retained in the EDP family — so the primary outcome's composition is not fully blind; the guard now covers the source dataset |
| F3 | 2026-09-13 (taken 2026-09-09) | record-level 2014–16 statistics computed while refuting finding O2, written into the findings register | nothing kept; the declared-access mechanism (§18) exists because of it; the coverage facts the paper cites come from the declared read |
| F4 | 2026-09-13 | the precinct–district crosswalk built from a server-side count of all dispatches per precinct × district over 2015–2024 (a geography weight, no call type, no date) | **kept**: the weights sit inside the B-HEARD exposure covariate (`data/reference/precinct_cd_crosswalk.csv`, `bheard_cd_exposure.csv`) |
| F5 | 2026-09-20, at the lift | three regression-suite checks that derived their sample from the freeze flag selected the confirmation sample in the gate run made to verify the lifted state | nothing kept; the checks are pinned to discovery, the suite is scanned by `D.discovery_scripts_pinned` |

**Disposition.** Materiality is for the reader to judge; the record is complete. The standard remedy — an
externally timestamped pre-registration — was open until the lift and is foreclosed by it (PAPER_MASTER §5.3,
finding P58). The paper's account of the five was corrected by the CP3 audit (findings P59–P62; see [[Audits]]):
the record's own nouns, what was kept, and that F1–F3 precede the commitments.

Related: [[Record]] · [[Design]] · [[Audits]] · [[Lessons]]
