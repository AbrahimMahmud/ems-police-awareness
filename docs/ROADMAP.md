# Final product and roadmap

## Final product (three deliverables, one repo)

D1. MAIN PAPER: "Public awareness of police violence and emergency
    help-seeking in New York City, 2015-2024." Confirmatory finding (either
    direction) on EDP-share suppression; heterogeneity/mechanism section;
    substitution outcomes. Target: public-health or social-science journal
    (with Justin). The discovery/confirmation split and pre-registered
    hypotheses (CONFIRMATION_PLAN.md) are the paper's inferential spine.
D2. METHODS CONTRIBUTION (section of D1 or standalone note): the bridge
    result (z-scored social-media attention measures manufacture outlier-
    leveraged effects) + the CAI as a verifiable, multi-source replacement,
    validated against the Werther-effect and attention-index literatures.
D3. REPLICATION PACKAGE: this repo -- one-command pipeline (00-12 + run_all),
    hashed public-source provenance, frozen-rule documents with git
    timestamps, all figures regenerated from committed tables.

## Design upgrades adopted from the methods literature

U1. PRIMARY CONFIRMATORY ESTIMATOR becomes a STACKED EPISODE EVENT STUDY
    (replaces the continuous distributed-lag as primary; DL becomes
    secondary): each CAI-D episode is an event; windows -14..+14; clean
    control days (no adjacent episode); quasi-Poisson/PPML counts and share
    OLS; episode-level randomization inference as the primary p-value.
    (Borusyak et al. 2024; Wing et al. stacked DiD; Werther-effect ITS
    practice of Poisson event models.)
U2. LONGER POST-WINDOWS as sensitivity (+28, +60 days): celebrity-suicide
    ITS studies find media-event effects persisting up to ~9 weeks; our
    14-day windows may truncate genuine dynamics.
U3. IDENTITY-MATCHED EXPOSURE retained as H3 (victim-race x district),
    now with literature grounding: Werther studies find imitation strongest
    for same-identity audiences.
U4. CAI stands on established ground (Da-Engelberg-Gao search-attention;
    composite indices outperform single sources) -- cite as lineage.

## Ordered steps to the final product

Phase A - inputs (user):            A1 extended EMS extract (script ready);
                                    A2 Justin: framing + provenance + gate
                                    ratification; A3 curation-row check.
Phase B - confirmation build (asst): B1 episode list 2015-2024 from CAI-D
                                    (committed BEFORE outcome contact);
                                    B2 stacked event-study estimator (U1)
                                    coded + synthetic-null calibrated;
                                    B3 substitution/mechanism fetchers
                                    (NYC Well, 311, NYPD CFS, CCRB, SQF).
GATE C - freeze audit (user+Justin): confirm episode list + estimator spec;
                                    after this, one shot at the data.
Phase D - confirmatory run (asst):  D1 H1-H3 on extension sample; D2 full
                                    robustness (windows U2, transforms,
                                    leave-one-out, divergence-day
                                    falsification); D3 Gate-3 memo + all
                                    figures (episode small-multiples, CAI
                                    validation, gradient, event-study).
Phase E - writing (user, assisted): E1 paper skeleton from memos; E2 methods
                                    + data sections from PROVENANCE/DESIGN
                                    docs; E3 results per D3; E4 Justin review
                                    loop; E5 replication-package freeze
                                    (pin versions, final run_all, README).
