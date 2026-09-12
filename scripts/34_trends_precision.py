"""Per-year precision and zero-censoring of the Google Trends components.

WHY THIS EXISTS (finding T6)
-----------------------------
T6 claims Trends measurement precision degrades about fivefold over the decade,
so the treatment carries year-varying attenuation and a 2021-2024 null cannot be
read as an absence of effect. If true that would bear directly on the
confirmatory result, because C2 is 2021-2024.

The argument is that Google rescales each request window to that window's own
maximum, so a decade-long fall in search share collapses the number of distinct
values a daily series can take. The second half of that does not follow from the
first: rescaling to the window maximum is precisely what keeps every window
spanning 0-100 regardless of the underlying level.

So this measures it rather than arguing about it, from the committed artifact
and with no refetch: per component and year, how many distinct values the series
takes, how coarse its implied quantization step is, and what share of days are
zero.

ZERO-CENSORING IS THE OTHER FAILURE MODE, and it is not the same as coarseness.
A series can span 0-100 with fine resolution and still be uninformative if most
of its days are zero, and a table of "availability" that counts a zero as an
observation will report it as fully available. Both are recorded here.

Outputs:
  data/reference/trends_precision_by_year.csv
      component, year, n_days, n_distinct, nonzero_days, zero_share,
      quant_step (median gap between adjacent distinct values), rel_step
"""

import numpy as np
import pandas as pd

from config import CAI_D_COMPONENTS, DATA_REFERENCE
from provenance import log_source

d = pd.read_csv(DATA_REFERENCE / "cai_trends_daily.csv", parse_dates=["date"])
d["year"] = d["date"].dt.year

rows = []
for (comp, yr), g in d.groupby(["component", "year"]):
    v = g["value"].dropna().to_numpy()
    if not len(v):
        continue
    u = np.unique(v)
    # The quantization step is the smallest gap between distinct observed values;
    # the median gap is used because a single outlier gap is not the grid.
    step = float(np.median(np.diff(u))) if len(u) > 1 else float("nan")
    rows.append({
        "component": comp, "year": int(yr), "n_days": len(v),
        "n_distinct": len(u),
        "nonzero_days": int((v > 0).sum()),
        "zero_share": float((v == 0).mean()),
        "max_value": float(v.max()),
        "quant_step": step,
        # Relative to the series' own scale, which is the quantity that governs
        # how much information a day carries.
        "rel_step": step / float(v.max()) if v.max() else float("nan"),
        "in_cai_d": comp in CAI_D_COMPONENTS,
    })

out = pd.DataFrame(rows).sort_values(["component", "year"])
out.to_csv(DATA_REFERENCE / "trends_precision_by_year.csv", index=False)

for comp, g in out.groupby("component"):
    early = g[(g["year"] >= 2015) & (g["year"] <= 2019)]
    late = g[g["year"] >= 2021]
    tag = "IN CAI-D" if bool(g["in_cai_d"].iloc[0]) else "retired, not in CAI-D"
    print(f"\n{comp}  ({tag})")
    print(f"  rel. quantization step   2015-19 {early['rel_step'].mean():.4f}"
          f"   2021-24 {late['rel_step'].mean():.4f}"
          f"   ratio {late['rel_step'].mean() / early['rel_step'].mean():.2f}x")
    print(f"  distinct values per year 2015-19 {early['n_distinct'].mean():.1f}"
          f"   2021-24 {late['n_distinct'].mean():.1f}")
    print(f"  non-zero days per year   2015-19 {early['nonzero_days'].mean():.0f}"
          f"   2021-24 {late['nonzero_days'].mean():.0f}")

print("\n" + out.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

log_source("S20",
           "Per-year precision and zero-censoring of the Google Trends components: "
           "distinct values, implied quantization step and zero share, used to test "
           "the claimed decade-long precision decay (finding T6)",
           "derived from data/reference/cai_trends_daily.csv",
           out_file=DATA_REFERENCE / "trends_precision_by_year.csv")
