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

## 7. Amendment: supply vs demand tiers (delivery is not consumption)

News/TV volume measures what media DELIVERED; searches and pageviews measure
what the public actually DID upon becoming aware. These are different objects
and are kept in separate tiers:

- **CAI-D (demand tier) = the awareness measure.** Components: wiki,
  trends_us, trends_nyc. Every component requires an act by an aware person.
  This is the treatment variable in all outcome models.
- **CAI-S (supply tier) = exposure opportunity.** Components: gdelt_news,
  gdelt_tv. Never enters outcome models as "awareness." Three uses:
  1. *Conversion diagnostics*: daily attention-per-coverage ratio; days with
     high supply but low demand ("delivery without uptake") are identified
     and tabulated.
  2. *Discriminating test*: on supply/demand divergence days, outcomes should
     follow CAI-D, not CAI-S, if behavior responds to awareness rather than
     to whatever else co-moves with news cycles. This is a falsification
     test the single-source design could never run.
  3. *Candidate instrument* (exploratory only): supply shocks as an IV for
     demand-side awareness; exclusion restriction is debatable (protest
     coverage may affect EMS directly), so IV results are labeled exploratory.
- Optional refinement: consumption-weight gdelt_tv by coarse public channel
  ratings (mention share x approximate audience = gross impressions); only if
  monthly ratings can be sourced publicly and reproducibly.
- Rationale kept on record: demand-side digital measures under-represent
  older/offline populations; CAI-S is retained partly because TV reaches
  them. If CAI-D and CAI-S correlate > 0.8 daily, the distinction is noted
  as immaterial in practice; if they diverge, the two-tier separation is
  doing real work.
