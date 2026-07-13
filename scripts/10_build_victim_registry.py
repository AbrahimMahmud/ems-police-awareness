"""Build the victim/event registry (AWARENESS_INDEX_DESIGN.md §1).

Primary: Mapping Police Violence (all police killings incl. non-shootings,
2013+). Cross-check: WaPo Fatal Force (shootings). Merged with the Wikipedia
article resolution table so victim-anchored components know which article
belongs to whom.

Output: data/reference/victim_registry.csv (one row per killing, 2013-2024)
"""

import hashlib
import io
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from config import DATA_REFERENCE, SHOOTINGS_DB_CSV

MPV_URL = "https://mappingpoliceviolence.us/s/MPVDatasetDownload.xlsx"
UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic research)"}

raw = urllib.request.urlopen(urllib.request.Request(MPV_URL, headers=UA), timeout=180).read()
mpv = pd.ExcelFile(io.BytesIO(raw)).parse("2013-2026 Police Killings")

reg = pd.DataFrame({
    "name": mpv["Victim's name"].astype(str).str.strip(),
    "date": pd.to_datetime(mpv["Date of Incident (month/day/year)"], errors="coerce"),
    "race": mpv["Victim's race"].astype(str).str.strip(),
    "cause": mpv["Cause of death"].astype(str).str.strip(),
    "city": mpv["City"].astype(str).str.strip(),
    "state": mpv["State"].astype(str).str.strip(),
    "mental_illness": mpv["Symptoms of mental illness?"].astype(str).str.strip(),
    "source": "MPV",
})
reg = reg[reg["date"].between("2013-01-01", "2024-12-31")]
reg = reg[reg["name"].str.lower() != "name withheld by police"]

RACE_MAP = {"Black": "B", "White": "W", "Hispanic": "H", "Asian": "A",
            "Native American": "N", "Pacific Islander": "A", "Unknown Race": "U", "Unknown race": "U"}
reg["race_code"] = reg["race"].map(RACE_MAP).fillna("U")

# WaPo cross-check: flag registry names present in WaPo (validates coverage)
wapo = pd.read_csv(SHOOTINGS_DB_CSV)
wapo_names = set(wapo["cleaned_name"].astype(str).str.strip().str.lower())
reg["in_wapo"] = reg["name"].str.lower().isin(wapo_names)

# attach Wikipedia articles where resolved
res = pd.read_csv(DATA_REFERENCE / "wikipedia_article_resolution.csv")
res["key"] = res["name"].str.strip().str.lower()
art = res.dropna(subset=["article"]).set_index("key")["article"]
reg["wiki_article"] = reg["name"].str.strip().str.lower().map(art)

out = DATA_REFERENCE / "victim_registry.csv"
reg.to_csv(out, index=False)

# provenance row
row = pd.DataFrame([{
    "source_id": "S10", "description": "Mapping Police Violence dataset (police killings 2013+)",
    "url": MPV_URL, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sha256": hashlib.sha256(raw).hexdigest(), "output_file": str(out),
}])
log = DATA_REFERENCE / "data_sources.csv"
row.to_csv(log, mode="a", header=not log.exists(), index=False)

shoot_2017_20 = reg[reg["date"].between("2017-01-01", "2020-12-31")]
print(f"Registry: {len(reg):,} killings 2013-2024 | race codes: {reg['race_code'].value_counts().to_dict()}")
print(f"2017-2020 subset: {len(shoot_2017_20):,} | in WaPo: {shoot_2017_20['in_wapo'].mean():.1%} "
      f"| with Wikipedia article: {shoot_2017_20['wiki_article'].notna().sum()}")
print(f"Non-shooting causes present: {sorted(reg['cause'].unique())[:8]}")
