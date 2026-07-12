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

import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_REFERENCE, TWEETS_PER_VICTIM_CSV, VALID_CDS

SOURCES_LOG = DATA_REFERENCE / "data_sources.csv"


def log_source(source_id, description, url, payload_bytes=None, out_file=None):
    """Append a provenance row (see docs/DATA_PROVENANCE.md) with content hash."""
    if payload_bytes is None and out_file is not None:
        payload_bytes = open(out_file, "rb").read()
    row = pd.DataFrame([{
        "source_id": source_id,
        "description": description,
        "url": url,
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(payload_bytes).hexdigest() if payload_bytes else "",
        "output_file": str(out_file) if out_file else "",
    }])
    header = not SOURCES_LOG.exists()
    row.to_csv(SOURCES_LOG, mode="a", header=header, index=False)

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
log_source("S7", "NYC DCP ACS 2015-2019 demographic profile, NTA2020 level", ACS_URL,
           payload_bytes=raw, out_file=DATA_REFERENCE / "acs_2019_cd_demographics.csv")
print(f"ACS 2015-2019: {len(cd)} CDs (source: DCP demo_2019_acs5yr_nta.xlsx)")
bs = cd[cd["communitydistrict"] == 303].iloc[0]
print(f"  sanity: Bed-Stuy (CD 303) pct_black_acs = {bs['pct_black_acs']:.1f}")

# --- 2. Wikipedia daily pageviews: automated article resolution ---
# For the top WIKI_TOP_N victims by tweet volume (~99%+ of volume-weighted
# signal), try title variants and accept an article only if it exists AND its
# summary mentions police (guards against same-name false positives). Manual
# overrides handle known renames the variant list misses.
WIKI_TOP_N = 150
TITLE_PREFIXES = ["Killing of", "Shooting of", "Murder of", "Death of", ""]
# Verified titles (previous run + manual research) skip resolution entirely.
MANUAL_TITLES = {
    "george floyd": "Killing_of_George_Floyd",
    "breonna taylor": "Killing_of_Breonna_Taylor",
    "rayshard brooks": "Killing_of_Rayshard_Brooks",
    "stephon clark": "Shooting_of_Stephon_Clark",
    "laquan mcdonald": "Murder_of_Laquan_McDonald",
    "elijah mcclain": "Death_of_Elijah_McClain",
    "atatiana jefferson": "Killing_of_Atatiana_Jefferson",
    "alton sterling": "Shooting_of_Alton_Sterling",
    "philando castile": "Shooting_of_Philando_Castile",
    "daniel prude": "Death_of_Daniel_Prude",
    "jordan edwards": "Shooting_of_Jordan_Edwards",
    "walter wallace jr.": "Killing_of_Walter_Wallace",
    "botham shem jean": "Murder_of_Botham_Jean",
    "freddie gray": "Death_of_Freddie_Gray",
    "tony timpa": "Tony_Timpa",
    "terence crutcher": "Shooting_of_Terence_Crutcher",
    "korryn gaines": "Korryn_Gaines",
    "ronald greene": "Death_of_Ronald_Greene",
    "dion johnson": "Shooting_of_Dion_Johnson",
    "deon kay": "Shooting_of_Deon_Kay",
    "jonathan price": "Murder_of_Jonathan_Price",
    "micah xavier johnson": "2016_shooting_of_Dallas_police_officers",
}
POLICE_WORDS = ("police", "officer", "law enforcement", "deputy", "trooper")


def summary_lookup(title):
    """Return the canonical article title if it exists and mentions police."""
    u = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(u, headers=UA)
            s = json.loads(urllib.request.urlopen(req, timeout=30).read())
            text = (s.get("extract") or "").lower()
            canonical = s.get("titles", {}).get("canonical") or title
            return canonical if any(w in text for w in POLICE_WORDS) else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            return None  # 404 etc: title doesn't exist
        except Exception:
            return None
    return None


def resolve_article(name):
    key = name.strip().lower()
    if key in MANUAL_TITLES:
        return MANUAL_TITLES[key]
    for prefix in TITLE_PREFIXES:
        title = f"{prefix} {name.strip()}".strip().replace(" ", "_")
        hit = summary_lookup(title)
        if hit:
            return hit
        time.sleep(0.5)
    return None


pv_victims = pd.read_csv(TWEETS_PER_VICTIM_CSV)
top_names = (pv_victims.groupby("name")["tweet_count"].sum()
             .sort_values(ascending=False).head(WIKI_TOP_N))
total_vol = pv_victims["tweet_count"].sum()


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


pv_rows, res_rows = [], []
for name, vol in top_names.items():
    article = resolve_article(name)
    n_days = 0
    if article:
        try:
            items = fetch_views(article)
            n_days = len(items)
            for it in items:
                pv_rows.append({"name": name, "article": article,
                                "date": pd.to_datetime(it["timestamp"][:8]),
                                "views": it["views"]})
        except Exception as e:
            print(f"  {name}: pageviews failed for {article}: {e}")
            article = None
    res_rows.append({"name": name, "tweet_volume": int(vol),
                     "volume_share": vol / total_vol,
                     "article": article, "pageview_days": n_days})
    time.sleep(0.4)

res = pd.DataFrame(res_rows)
res.to_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv", index=False)
pv = pd.DataFrame(pv_rows)
pv.to_csv(DATA_REFERENCE / "wikipedia_pageviews_victims.csv", index=False)
log_source("S8", f"Wikimedia pageviews, top-{WIKI_TOP_N} victims, en.wikipedia 2017-2020",
           "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/",
           out_file=DATA_REFERENCE / "wikipedia_pageviews_victims.csv")
resolved = res[res["article"].notna()]
print(f"Wikipedia: resolved {len(resolved)}/{len(res)} of top-{WIKI_TOP_N} victims "
      f"({100 * resolved['volume_share'].sum():.1f}% of ALL tweet volume); "
      f"{len(pv):,} article-days")
print("Unresolved with largest volume:")
print(res[res["article"].isna()].head(8)[["name", "tweet_volume"]].to_string(index=False))
