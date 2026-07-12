# Confirmation plan (addresses concerns C1 and C2)

Design: 2017-2020 = discovery sample (all current results). Hypotheses frozen
BEFORE any extension data is examined; the extension + independent outcomes
form the confirmation package. Either outcome yields a publishable conclusion.

## Frozen confirmatory hypotheses (as of this commit; no extension data examined)
H1 (primary): EDP call share declines in days 0-5 after high-awareness
    episodes (directional). Test: episode-level randomization inference,
    specification exactly as scripts 01-05 (aware_log windows, 59 CDs,
    date-clustered + permutation).
H2 (substitution): non-police crisis contacts (NYC Well) rise in the same
    windows (directional).
H3 (mechanism): the EDP decline is steeper in precincts/districts with higher
    police-distrust exposure (CCRB complaints per capita; SQF history), and
    in response to Black-victim episodes specifically (aware_black index).
Q1-protest hypothesis: whitest-quartile suppression is protest disruption --
    it attenuates under same-day injury-intensity controls; Q3/Q4 does not.

## Workstreams
W1 Extension sample (C1): Wikipedia-pageview awareness index 2015-2024
   (validated vs Twitter r=0.72 on 2017-2020 overlap; selection toward famous
   cases modeled explicitly). Expected new episodes: Scott/Gray 2015,
   Sterling/Castile/Dallas 2016, K. Scott 2016, Wright + Chauvin verdict 2021,
   Nichols 2023, Neely 2023 (NYC), Massey 2024 -> ~30 episodes total.
   NEEDS: user reruns 00_local_ems_extract.py with 2015-01-01..2024-12-31.
W2 Independent outcomes (C1): NYPD 911 Calls-for-Service by precinct (2018+,
   Desmond replication); NYC Well contact volumes (substitution); NYC 311.
W3 Finer geography (C1/C7): zip-level EMS extract (~180 units).
W4 Mechanism measures (C2): CCRB complaint rates, stop-question-frisk
   intensity; protest-proxy controls (injury intensity); victim-race-specific
   episode responses.
W5 Power notes: permutation SD scales ~sqrt(12/30)=0.63 -> extension alone
   lands H1 near p~0.08 two-sided; confidence comes from the joint package
   (H1 extension + H2 substitution + W2 precinct replication), not one test.

## Sequencing
1. (user) rerun extract 2015-2024; ask Justin: framing decision + Twitter provenance
2. (assisted) Wikipedia index 2015-2024 + validation report -- BEFORE any outcome contact
3. (assisted) fetch W2/W4 public data; register in DATA_PROVENANCE.md
4. confirmatory run, one shot, all hypotheses; Gate 3 memo
5. paper drafted around whichever conclusion the data support
