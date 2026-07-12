"""Fetch public augmentation data (REWORK_PLAN task D1/D2; GATE2 memo §6).

Requires network access to api.census.gov and wikimedia.org (environment
network policy updated 2026-07-12; applies to sessions started after that).

Outputs (committed, small):
  data/reference/acs_2019_cd_demographics.csv   ACS 5yr 2015-2019 race shares by CD
                                                (PUMA->CD crosswalk, 2010 PUMA vintage)
  data/reference/wikipedia_pageviews_victims.csv daily enwiki pageviews for top victims
"""

import json
import time
import urllib.request

import pandas as pd

from config import DATA_REFERENCE, OUTPUTS_TABLES

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}

# --- 1. ACS 2015-2019 5-year, table B03002, NYC PUMAs (2010 vintage) ---
# NYC PUMAs 2010: 3701-3710 Bronx, 3801-3810 Manhattan, 3901-3903 SI,
# 4001-4018 Brooklyn, 4101-4114 Queens. PUMA->CD: mostly 1:1; four merged
# pairs noted in the crosswalk below (both CDs receive the PUMA value).
PUMA_TO_CDS = {
    # Bronx (CD codes 201-212)
    3701: [208], 3702: [212], 3703: [210], 3704: [211], 3705: [203, 206],
    3706: [207], 3707: [205], 3708: [204], 3709: [209], 3710: [201, 202],
    # Manhattan (101-112)
    3801: [112], 3802: [109, 110], 3803: [111], 3804: [108], 3805: [107],
    3806: [106], 3807: [105], 3808: [104], 3809: [103], 3810: [101, 102],
    # Staten Island (501-503)
    3901: [503], 3902: [502], 3903: [501],
    # Brooklyn (301-318)
    4001: [301], 4002: [304], 4003: [303], 4004: [302], 4005: [306],
    4006: [308], 4007: [316], 4008: [305], 4009: [318], 4010: [317],
    4011: [309], 4012: [307], 4013: [310], 4014: [312], 4015: [314],
    4016: [315], 4017: [311], 4018: [313],
    # Queens (401-414)
    4101: [401], 4102: [403], 4103: [407], 4104: [411], 4105: [413],
    4106: [408], 4107: [404, 406], 4108: [402, 405], 4109: [409],
    4110: [412], 4111: [410], 4112: [414],
}

url = ("https://api.census.gov/data/2019/acs/acs5?get=NAME,B03002_001E,"
       "B03002_003E,B03002_004E,B03002_012E,B03002_006E"
       "&for=public%20use%20microdata%20area:*&in=state:36")
req = urllib.request.Request(url, headers=UA)
rows = json.loads(urllib.request.urlopen(req, timeout=60).read())
acs = pd.DataFrame(rows[1:], columns=rows[0])
acs["puma"] = acs["public use microdata area"].astype(int)
acs = acs[acs["puma"].isin(PUMA_TO_CDS)]
for c in ["B03002_001E", "B03002_003E", "B03002_004E", "B03002_012E", "B03002_006E"]:
    acs[c] = pd.to_numeric(acs[c])

out = []
for _, r in acs.iterrows():
    for cd in PUMA_TO_CDS[r["puma"]]:
        out.append({
            "communitydistrict": cd, "puma_2010": r["puma"],
            "pct_white_acs": 100 * r["B03002_003E"] / r["B03002_001E"],
            "pct_black_acs": 100 * r["B03002_004E"] / r["B03002_001E"],
            "pct_hispanic_acs": 100 * r["B03002_012E"] / r["B03002_001E"],
            "pct_asian_acs": 100 * r["B03002_006E"] / r["B03002_001E"],
            "total_pop_acs": r["B03002_001E"],
        })
acs_cd = pd.DataFrame(out).sort_values("communitydistrict")
assert len(acs_cd) == 59, f"expected 59 CDs, got {len(acs_cd)}"
acs_cd.to_csv(DATA_REFERENCE / "acs_2019_cd_demographics.csv", index=False)
print(f"ACS: {len(acs_cd)} CDs written")

# --- 2. Wikipedia daily pageviews for top victims ---
ARTICLES = {
    "George Floyd": "Killing_of_George_Floyd",
    "Breonna Taylor": "Killing_of_Breonna_Taylor",
    "Rayshard Brooks": "Killing_of_Rayshard_Brooks",
    "Stephon Clark": "Shooting_of_Stephon_Clark",
    "Laquan McDonald": "Murder_of_Laquan_McDonald",
    "Elijah McClain": "Killing_of_Elijah_McClain",
    "Atatiana Jefferson": "Killing_of_Atatiana_Jefferson",
    "Alton Sterling": "Shooting_of_Alton_Sterling",
    "Philando Castile": "Killing_of_Philando_Castile",
    "Daniel Prude": "Death_of_Daniel_Prude",
    "Walter Wallace Jr.": "Killing_of_Walter_Wallace_Jr.",
    "Jordan Edwards": "Shooting_of_Jordan_Edwards",
}
pv_rows = []
for name, article in ARTICLES.items():
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
         f"en.wikipedia/all-access/user/{article}/daily/20170101/20201231")
    try:
        req = urllib.request.Request(u, headers=UA)
        items = json.loads(urllib.request.urlopen(req, timeout=60).read())["items"]
        for it in items:
            pv_rows.append({"name": name, "article": article,
                            "date": pd.to_datetime(it["timestamp"][:8]),
                            "views": it["views"]})
    except Exception as e:  # article may postdate window
        print(f"  {article}: {e}")
    time.sleep(0.5)
pv = pd.DataFrame(pv_rows)
pv.to_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", index=False)
print(f"Wikipedia: {len(pv):,} article-days for {pv['name'].nunique()} victims")
