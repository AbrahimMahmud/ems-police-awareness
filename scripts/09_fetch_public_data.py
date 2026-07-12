"""Fetch public augmentation data (REWORK_PLAN task D1/D2; GATE2 memo §6).

Sources:
  1. NYC DCP ACS 2015-2019 5-year demographic profile at NTA2020 level
     (s-media.nyc.gov, official DCP publication). NTA2020 GeoIDs embed the
     community district (e.g. BK0301 = Brooklyn CD 3, NTA 01), so aggregation
     to the 59 CDs is exact -- no crosswalk approximation.
     Note: the Census API route was abandoned (now requires an API key).
  2. Wikimedia REST API daily pageviews for top awareness victims, 2017-2020.

Outputs (committed, small):
  data/reference/acs_2019_cd_demographics.csv
  data/reference/wikipedia_pageviews_victims.csv
"""

import io
import json
import time
import urllib.request

import pandas as pd

from config import DATA_REFERENCE, VALID_CDS

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}
BORO = {"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5}

# --- 1. ACS 2015-2019 by NTA2020, aggregated exactly to community districts ---
ACS_URL = ("https://s-media.nyc.gov/agencies/dcp/assets/files/excel/data-tools/"
           "census/acs/demo_2019_acs5yr_nta.xlsx")
raw = urllib.request.urlopen(urllib.request.Request(ACS_URL, headers=UA), timeout=120).read()
nta = pd.ExcelFile(io.BytesIO(raw)).parse("DemData")

nta["boro"] = nta["GeoID"].str[:2].map(BORO)
nta["cd_num"] = pd.to_numeric(nta["GeoID"].str[2:4], errors="coerce")
nta["communitydistrict"] = nta["boro"] * 100 + nta["cd_num"]
nta = nta[nta["communitydistrict"].isin(VALID_CDS)]

counts = ["Pop_1E", "WtNHE", "BlNHE", "Hsp1E", "AsnNHE"]
cd = nta.groupby("communitydistrict", as_index=False)[counts].sum()
cd["pct_white_acs"] = 100 * cd["WtNHE"] / cd["Pop_1E"]
cd["pct_black_acs"] = 100 * cd["BlNHE"] / cd["Pop_1E"]
cd["pct_hispanic_acs"] = 100 * cd["Hsp1E"] / cd["Pop_1E"]
cd["pct_asian_acs"] = 100 * cd["AsnNHE"] / cd["Pop_1E"]
cd = cd.rename(columns={"Pop_1E": "total_pop_acs"})
cd = cd[["communitydistrict", "total_pop_acs", "pct_white_acs", "pct_black_acs",
         "pct_hispanic_acs", "pct_asian_acs"]].sort_values("communitydistrict")
assert len(cd) == 59, f"expected 59 CDs, got {len(cd)}"
assert cd[["pct_white_acs", "pct_black_acs", "pct_hispanic_acs", "pct_asian_acs"]].max().max() <= 100
cd.to_csv(DATA_REFERENCE / "acs_2019_cd_demographics.csv", index=False)
print(f"ACS 2015-2019: {len(cd)} CDs (source: DCP demo_2019_acs5yr_nta.xlsx)")
bs = cd[cd["communitydistrict"] == 303].iloc[0]
print(f"  sanity: Bed-Stuy (CD 303) pct_black_acs = {bs['pct_black_acs']:.1f}")

# --- 2. Wikipedia daily pageviews for top victims ---
# Article titles change over time (Shooting_of_ -> Killing_of_ renames);
# candidates are tried in order and the first with substantial coverage wins.
ARTICLES = {
    "George Floyd": ["Killing_of_George_Floyd"],
    "Breonna Taylor": ["Killing_of_Breonna_Taylor"],
    "Rayshard Brooks": ["Killing_of_Rayshard_Brooks"],
    "Stephon Clark": ["Shooting_of_Stephon_Clark"],
    "Laquan McDonald": ["Murder_of_Laquan_McDonald"],
    "Elijah McClain": ["Death_of_Elijah_McClain", "Killing_of_Elijah_McClain"],
    "Atatiana Jefferson": ["Killing_of_Atatiana_Jefferson"],
    "Alton Sterling": ["Shooting_of_Alton_Sterling"],
    "Philando Castile": ["Shooting_of_Philando_Castile", "Killing_of_Philando_Castile"],
    "Daniel Prude": ["Death_of_Daniel_Prude"],
    "Walter Wallace Jr.": ["Killing_of_Walter_Wallace"],
    "Jordan Edwards": ["Shooting_of_Jordan_Edwards", "Murder_of_Jordan_Edwards"],
}


def fetch_views(article):
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
         f"en.wikipedia/all-access/user/{article}/daily/20170101/20201231")
    for attempt in range(4):
        try:
            req = urllib.request.Request(u, headers=UA)
            return json.loads(urllib.request.urlopen(req, timeout=60).read())["items"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"rate-limited after retries: {article}")


pv_rows = []
for name, candidates in ARTICLES.items():
    best, best_article = [], None
    for article in candidates:
        try:
            items = fetch_views(article)
        except Exception as e:
            print(f"  {article}: {e}")
            items = []
        if len(items) > len(best):
            best, best_article = items, article
        time.sleep(1.0)
    for it in best:
        pv_rows.append({"name": name, "article": best_article,
                        "date": pd.to_datetime(it["timestamp"][:8]),
                        "views": it["views"]})
    print(f"  {name}: {len(best)} days via {best_article}")
pv = pd.DataFrame(pv_rows)
pv.to_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", index=False)
print(f"Wikipedia: {len(pv):,} article-days, {pv['name'].nunique()} victims")
