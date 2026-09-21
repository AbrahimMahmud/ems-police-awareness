# Status — 2026-09-21 ~05:30Z

- **CP3 done.** Full manuscript audit wf_0df7b965-8dc (8 finders, 61 raw / 57 unique findings, three-lens refutation of
  the ten highest → 5 survived, completeness critic → 6 items). Every surviving item fixed, every unverified item that
  held on inspection fixed; filed as **P59–P63**, held by `S.third_pass_record_consistency` tokens (defeat-tested).
  Commit `663153d`.
- **What the paper had wrong about the record**: F1/F2 called metadata reads and F3 a coverage read; "never used for
  any specification choice"; "no number from them was kept" (F4 weights are in the B-HEARD covariate); "before any
  confirmation-period outcome was seen"; the closing bias-direction claim. All rewritten from CONFIRMATION_PLAN §15 /
  PAPER_MASTER §5.3. Also: disposition filter in the outcome definition; H2/H3 not run (Limitation 12); nine pooled
  cells added to Table 4; captions from the sealed table's reasons; Figure 2 units; Figure 3 joint spec; Wu et al.
  cited for what it measured; the family-corrected bound beside the nominal in Abstract and Discussion.
- **Phase I sealed 2026-09-21 03:24:13Z**; reading = the pre-specified null in both strata (see [[Decisions]]).
- **Manuscript complete** (`docs/PAPER.md`; PAPER_MASTER §8b). Abstract 250 words. Main text ~8,200 words excl.
  tables (Methods ~4,000) vs ~4,000; nine display items vs four → the author's editorial pass is the one open item.
- **Claims**: 1,354 registered, 1,354 verify. **Findings**: 164 filed, 164 fixed. **Gate**: 90/90 twice after every edit.
- **References 11–13 confirmed** (PubMed, Mannheim repository, IBO). RECORD 6.2 code-list comparison pending.
- **Next**: [[Next actions]]. Plan of record: `docs/EXECUTION_PLAN.md` (Status block at the top); `docs/HANDOFF_2026-09-21.md`.

Environment note: compute advances only while a session is active; the worker pool fits at two workers; monitor
scripts stay grep-and-cut (embedded python in a single-quoted string prints nothing).
