# Composite Awareness Index (CAI) - design specification

Purpose: replace the unverifiable single-source Twitter measure with a
composite index built ENTIRELY from public, re-fetchable sources, so any
reader can rebuild the treatment variable from scratch. The legacy Twitter
series (2017-2020) becomes a validation benchmark only, never load-bearing.

Construction rules in this document are FROZEN before any contact with
extension-period outcome data (see CONFIRMATION_PLAN.md; same discipline).

## 1. Victim/event registry
- Primary: Mapping Police Violence (all police killings incl. non-shootings,
  2013+; public download) -- verified reachable 2026-07-13.
- Cross-check: Washington Post Fatal Force v2 (shootings, 2015+).
- Existing curation table retained for name reconciliation.
- Registry fields: name, date, race, means, state/city, wikipedia article.

## 2. Daily components, 2015-01-01..2024-12-31
| id | source | what it measures | status |
|----|--------|------------------|--------|
| wiki | Wikimedia pageviews, victim articles | information-seeking, victim-anchored | pipeline built |
| gdelt_news | GDELT DOC 2.0 timelinevol, frozen query set ("police shooting" OR "police killing" OR "killed by police" OR "police brutality") | online news supply | verified reachable |
| gdelt_tv | GDELT TV API, same queries, CNN+MSNBC+FoxNews mention share | broadcast salience | reachable (station param) |
| trends_us | Google Trends, topic "Police brutality" + victim-name terms, US | search attention, national | via pytrends |
| trends_nyc | same, geo = NYC DMA (501) | search attention, LOCAL | via pytrends |
| nyt | NYT Article Search API count/day (optional; free key) | elite/print coverage | pending key |
| twitter_legacy | existing files, 2017-2020 | validation benchmark ONLY | in hand |

## 3. Construction (frozen)
1. Each component: log(1+x), standardized on the 2017-2019 window (pre-Floyd,
   avoids outlier-defined scale; the exact failure mode of the legacy z-score).
2. CAI = unweighted mean of available standardized components (no fitted
   weights = no overfitting). PCA-weighted version as robustness only.
3. Sub-indices: CAI_black (victim-anchored components restricted to Black
   victims via registry), CAI_nyc (trends_nyc + NYT-metro when available).
4. Missing components on a day: mean over non-missing; component availability
   flag retained.

## 4. Validation battery (report regardless of results)
- Pairwise component correlations (full period + excluding Floyd episode).
- Benchmark: corr(CAI, legacy Twitter) on 2017-2020, target r >= 0.7.
- Peak-alignment: top-20 CAI days must map to nameable events (table).
- Component lead-lag: co-movement within 0-1 days (news vs search vs wiki).
- NYC-vs-national: corr(trends_nyc, trends_us) quantifies how much the
  citywide-awareness assumption costs.

## 5. Why this answers the verifiability problem
Every component: public API/download + fetch script + SHA256 + access date in
data/reference/data_sources.csv. The paper's data section can state: "the
awareness index can be reconstructed end-to-end from public sources by
running scripts/09-10." Twitter provenance (still owed by the data's
originator) becomes a nice-to-have, not a blocker.

## 6. Build order
1. 10_build_victim_registry.py (MPV + WaPo + curation reconcile)
2. 11_fetch_awareness_components.py (wiki/gdelt_news/gdelt_tv/trends; hashed)
3. 12_build_cai.py (construction rules above; validation battery output)
4. Gate: validation reviewed -> CAI becomes the instrument for
   CONFIRMATION_PLAN W1; discovery-period results re-expressed in CAI as a
   robustness column.
