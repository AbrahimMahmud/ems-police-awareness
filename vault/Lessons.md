---
tags: [craft, lessons]
updated: 2026-09-21
---
# Lessons — what went wrong and the rule each produced

Consolidated from the handoffs (`docs/HANDOFF_2026-09-13.md`, `_09-20.md`, `_09-21.md` §4). Each line: the
failure, then the rule.

**The record and the paper**
- The paper paraphrased the record more softly than the record (metadata reads; nothing kept; committed before
  any outcome was seen). → Use the record's own nouns; hold the wording with a suite token (P59–P63).
- A generator loop over two strata dropped nine sealed pooled cells from an exhibit. → Every "per stratum" table
  loops over every stratum in the sealed file.
- Methods definitions drifted from the code (the disposition filter, the episode label, the freeze architecture).
  → Read the generator and the docstring before writing the sentence.
- A citation marker inserted into a claim's anchor sentence broke the claim (C161). → Grep the register for the
  sentence before adding a reference.
- A numeral-leading table label counted as a value; a mechanical rename spliced into prose ("60 dayss"). → Labels
  never begin with a numeral; rename by whole-cell match.
- The abstract's first draft ignored the plan's specification. → Read PAPER_PLAN's section spec before drafting.

**The freeze**
- "It is only metadata" produced F1 and F2; an exemption for the suite produced F5. → No reasoning about
  harmlessness replaces a guard; scan everything, whitelist by name and reason.
- A refutation wrote record-level confirmation statistics into the findings register (F3). → A read that has to
  happen is declared, scoped and logged first (§18).

**Compute and the environment**
- The container suspends minutes after the session goes idle; a sealed run stopped at 09:36Z. → Babysit long runs
  from an active session (Monitor cycles, a fallback check-in); relaunch with a recorded reason.
- Four, then three workers exceeded the memory cgroup on the pooled 60-day cells. → Two workers; parallelism
  changes no number.
- A run was assumed started from a log line that preceded it. → Verify by PID, never infer.
- A grep for the script's own name matched the shell running it. → Match `[s]pawn_main` or PID files.
- A sidecar was stamped before the last edit to a hashed source. → Stamp last.
- A Monitor filter with python embedded in a single-quoted string printed nothing for 30 minutes. → Monitor
  scripts stay grep-and-cut.
- A workflow prompt written before the run finished described one resume when there were seven starts. →
  Re-read every factual statement in a prompt before launching it.
- Two spec-audit tokens were satisfied elsewhere in the file. → Exact-line tokens; always run the defeat attempt.

**Determinism**
- Two cold passes differed at 1e-16 from hash randomization. → `PYTHONHASHSEED=0` and one BLAS thread for every
  stage and for the gate (X20).

Related: [[00 Project]] · [[Audits]] · [[Freeze incidents]] · [[Tooling]] · [[Decisions]]
