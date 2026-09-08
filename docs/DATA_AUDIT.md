# Data audit — 2026-09-08

Full integrity check of every committed reference input, run before the discovery
pipeline is re-run under CAI-D. Reproducible via `scripts/20_data_audit.py`;
machine-readable results in `outputs/tables/data_audit.csv` (35 checks, 14 flagged).

**This audit touched no outcome data.** It reads only `data/reference/` and the
treatment-side files in `data/processed/`. The confirmation freeze is unaffected,
and that fact is what makes the corrections below legitimate — see §5.

---

## 1. The serious finding: CAI-D is not consistently scaled over time

The index is an unweighted mean of whatever components exist on a given day, and
how many exist swings sharply across the panel.

| Components available | Days | SD of CAI-D | Days flagged `cai_d > 1.0` |
|---|---|---|---|
| 2 | 63 | 0.770 | **25.4%** |
| 3 | 2,087 | 0.693 | **6.2%** |
| 4 | 1,503 | 1.034 | **15.4%** |

Two consequences:

- **The episode rule is not a constant-SD rule.** `cai_d > 1.0` is applied to a
  series whose spread ranges from 0.693 to 1.034 depending on which sources
  happened to exist that day. Whether a day becomes an episode depends partly on
  data availability rather than on attention.
- **It is visible in the frozen episode list.** 2022 produces 12 episodes, 9 of
  them single-day, on an average of 3.01 components; 2024 produces one episode.
  Across the whole list, **34 of 70 episodes are single days**, many with peak
  values barely over the threshold.

Component availability by year (fraction of days present):

| Year | wiki_ext | trends_us | trends_nyc | trends_victims | gdelt_news | gdelt_tv |
|---|---|---|---|---|---|---|
| 2015 | 0.50 | 1.00 | 1.00 | 0.45 | 0.00 | 1.00 |
| 2016 | 1.00 | 1.00 | 1.00 | 0.57 | 0.00 | 1.00 |
| 2017 | 1.00 | 1.00 | 1.00 | 0.05 | 0.99 | 1.00 |
| 2018 | 1.00 | 1.00 | 1.00 | 0.74 | 1.00 | 1.00 |
| 2019 | 1.00 | 1.00 | 1.00 | 0.39 | 1.00 | 1.00 |
| 2020 | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 |
| 2021 | 1.00 | 1.00 | 1.00 | 0.56 | 1.00 | 1.00 |
| 2022 | 1.00 | 1.00 | 1.00 | 0.01 | 1.00 | 1.00 |
| 2023 | 1.00 | 1.00 | 1.00 | 0.66 | 0.00 | 1.00 |
| 2024 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | 0.78 |

**Fix.** Standardise the composite on the reference window *after* averaging,
rather than averaging separately-standardised components; or hold the component
set fixed. Either way the threshold must be re-derived on the corrected index.

---

## 2. One component's availability is caused by the treatment

`trends_victims` is present on 45% of 2015 days, 5% of 2017, 1% of 2022, and 0%
of 2024. That missingness is not random.

**On days when `trends_victims` exists, the other three components average
+0.560 SD higher than on days when it does not.**

The mechanism is mechanical: Google Trends only returns a victim-name series once
search volume clears its reporting floor. So the component's *presence* is itself
an attention signal, and averaging over "available" components lifts the index
precisely on high-attention days — partly by construction rather than by
measurement. A referee is entitled to say the index partly measures itself.

**Fix.** Drop `trends_victims` from CAI-D. The cost is small: the three always-on
components correlate **0.985** with the index as built. The effect on the episode
list is not small — 378 high days as built versus 630 without it — which is
precisely the §1 scaling problem restated.

---

## 3. Wikipedia: a 2015 hole and four resolver failures

**Coverage hole — a hard limit, not a defect.** `wiki_ext` begins
**2015-07-01** because the Wikimedia pageviews API itself begins there
(`11_fetch_awareness_components.py:7`). No fetch can recover January–June 2015.
Twelve extension episodes start in 2015 and those before July were therefore
defined with no Wikipedia component at all. The correct response is to **drop
that window from the analysis sample**, not to try to repair it: an index built
from a different component set is not the same measurement.

`gdelt_news` is missing for 2015–2016 and 2023–2024. It sits in the supply tier
so it does not enter CAI-D, but it disables the divergence-day falsification test
in those years.

**The resolver bug reaches CAI-D, not just H3.** `wiki_ext` is built from the same
`wikipedia_article_resolution.csv` article list
(`11_fetch_awareness_components.py:49-50`), so the four near-empty series below
contribute almost nothing to the composite index and therefore to the episode
list — not merely to the race sub-indices.

**Resolver accepted low-traffic redirects.** Four victims resolved to
`Killing_of_*` titles that carry almost no traffic, when the real articles are
titled `Shooting_of_*`:

| Victim | Killed | Resolved to | Days | Total views |
|---|---|---|---|---|
| Walter Scott | 2015-04-04 | `Killing_of_Walter_Scott` | 1 | 19 |
| Corey Jones | 2015-10-18 | `Killing_of_Corey_Jones` | 1 | 3 |
| Willie McCoy | 2019-02-09 | `Killing_of_Willie_McCoy` | 1 | 4 |
| Scout Schultz | 2017-09-16 | `Killing_of_Scout_Schultz` | 5 | 5 |

The acceptance test confirmed a title existed but never checked that it carried
plausible traffic. Walter Scott matters specifically: `CONFIRMATION_PLAN.md:23`
names "Scott/Gray 2015" as an expected extension episode.

**Not a problem:** the other short series are legitimate. 26 of 45 victims have
series shorter than the full window because their article postdates the killing,
which is correct behaviour, not a gap.

**Fix.** Add minimum-days and minimum-traffic checks to the resolver, retry the
title variants for the four failures, and re-fetch. Doing this also discharges
Gate C blocking item B (per-victim pageviews across 2015–2024).

---

## 4. Smaller defects

- **Crosswalk column is misnamed.** `precinct_cd_crosswalk.csv`'s
  `w_precinct_in_cd` is normalised **by community district** — it sums to exactly
  1.0000 for all 59 CDs, and to 1.0 for only 24 of 77 precincts. The arithmetic is
  correct for computing CD-level B-HEARD exposure; the name says the opposite of
  what the column does and will mislead anyone reading the Methods. Rename it, and
  write the linkage-quality evaluation RECORD 12.3 requires, which does not exist.
- **B-HEARD adoption dates are mostly low-confidence:** 17 low, 11 medium, 3 high
  out of 31 precincts. That belongs in the limitations, not only in the memo.
- **Provenance keys collide.** `S10` labels both Mapping Police Violence and the
  precinct crosswalk; `S11` labels both the CAI components and the B-HEARD
  adoption schedule. Re-key before any source ID is cited in a Methods section.
- **Coverage claim disagrees with itself.** The resolution file implies 87.9% of
  tweet volume covered; the commit message and docs say 82.8%. Settle on one.
- **Episode 45 spans 128 days** (2020-05-26 to 2020-10-01). The merge-gap-under-7-
  days rule collapses the entire 2020 summer into a single event, which under a
  ±14-day stacked design is one observation and re-imports issue I2's outlier
  problem through the episode definition.

---

## 5. What is clean

Most of the data is sound, and that is worth recording as explicitly as the
defects:

- **`victim_registry.csv`** — 13,241 rows, 2013-01-01 to 2024-12-31, zero
  duplicate rows, zero null names or dates, 1,029–1,188 records per year, which
  matches Mapping Police Violence's published scale.
- **`acs_2019_cd_demographics.csv`** — exactly 59 districts, no duplicates, four
  race shares summing to 86.7–98.9% (remainder is other/multiracial), nothing out
  of range.
- **`bheard_cd_exposure.csv`** — every exposure within [0, 1], no effective date
  before the June 2021 launch.
- **`awareness_lags.parquet`** — no date gaps, no duplicate dates, every CAI-D lag
  and lead complete across the 2017–2020 analysis window.
- **Episode labels are correct.** An earlier reading flagged episodes naming
  victims killed years outside their window. That was an artifact of namesakes —
  the registry contains 97 repeated names, and matching on the first occurrence
  picked the wrong person. Checking every killing date per name, **0 of 140 labels
  are out of window.** No relabelling is needed.

---

## 6. Correcting the frozen episode list without breaking the freeze

Findings §1, §2 and §3 all feed the episode list, which is frozen. Rebuilding a
frozen artifact is normally exactly what a pre-registration forbids.

**It is legitimate here, and only here, because no outcome has been touched.** A
freeze exists to prevent outcome-informed selection. A correction made while
still blind to every outcome cannot be outcome-informed, and the audit that
motivated it read no EMS data at all. The repo state supports this: no
extension-period estimate exists anywhere, and `outputs/tables/` contains only
treatment-side files.

Procedure, to be followed in order:

1. **Commit this audit first**, so the documented reason predates the change.
2. Fix the index construction (§1, §2) and the resolver (§3).
3. Regenerate the episode list to a **new file**, leaving
   `confirmation_episodes.csv` untouched as the original frozen artifact.
4. **Publish the diff** — episodes added, dropped, boundaries moved — so the
   change is auditable rather than asserted.
5. Obtain Justin's sign-off on the corrected list before any outcome contact.

If this correction is made after the confirmatory run instead, it is worthless
and looks like specification search. Now is the only moment it is free.
