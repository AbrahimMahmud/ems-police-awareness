"""Resolve scope metadata for every candidate basket article, from Wikidata.

WHY THIS EXISTS (finding T9)
-----------------------------
24_build_wiki_basket.py walks the live Wikipedia category tree and returns ~143
person-shaped articles. Deciding which belong in the CAI-D basket needs three
facts per article: WHEN the death occurred, WHERE, and whether law enforcement
caused it. Those decide in-scope vs out-of-scope, and getting them wrong puts
either the wrong attention or no attention into the treatment index.

The obvious shortcut — keep only articles that match the victim registry — is
WRONG here, and that is finding T9. Mapping Police Violence, which is 100% of
the registry, does not carry Daniel Prude, Sandra Bland, Marvin Scott, Javier
Ambler, Eurie Martin or Leneal Frazier. Verified directly against the MPV
workbook, not inferred: those names are absent from the source, so this is MPV's
coverage rather than a parsing bug. The omissions are not random with respect to
this paper's hypothesis — they are disproportionately in-custody, restraint and
mental-health-crisis deaths, which are precisely the events most likely to move
mental-health EMS demand. Registry-gating the basket would delete the most
on-hypothesis events in the study, Daniel Prude first among them.

So scope is resolved from a source that is independent of the registry, and the
registry is used only to attach race and to cross-check.

The alternative to this script was hand-classifying 56 people from memory. That
is the same error class this project keeps finding — an assertion that feels
obvious, is never checked, and turns out wrong. Every date here is fetched and
cached, so a referee can re-run it.

Wikidata note: the endpoint is currently rate-limiting to 1 request/minute
during an outage, so EVERY article goes in ONE batched query and the response is
cached to disk.

Outputs:
  data/reference/basket_scope.csv   article, item, label, date, country, manner
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from config import DATA_PROCESSED, DATA_REFERENCE

UA = "ems-police-awareness-research/1.0 (academic; contact via repository)"
ENDPOINT = "https://query.wikidata.org/sparql"
CACHE = DATA_PROCESSED / "wikidata_cache"

PERSON_PREFIXES = ("Killing_of_", "Shooting_of_", "Death_of_", "Murder_of_",
                   "Police_shooting_of_")


def run_sparql(query, tag, max_attempts=8):
    """One cached SPARQL request, with backoff tuned for a 1 req/min limit."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{tag}.json"
    if path.exists():
        print(f"  cached: {path.name}")
        return json.loads(path.read_text())["results"]["bindings"]
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            path.write_text(json.dumps(data))
            return data["results"]["bindings"]
        except urllib.error.HTTPError as e:
            wait = 70 if e.code == 429 else 20 * (attempt + 1)
            print(f"    HTTP {e.code}; waiting {wait}s (attempt {attempt + 1}/{max_attempts})")
            time.sleep(wait)
        except Exception as e:
            print(f"    {type(e).__name__}: {e}; retrying")
            time.sleep(30)
    raise RuntimeError("Wikidata did not answer; rerun later — the cache makes it resumable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=200, help="articles per query")
    args = ap.parse_args()

    b = pd.read_csv(DATA_REFERENCE / "wiki_basket.csv")
    cand = b[b["article"].str.startswith(PERSON_PREFIXES) | b["in_registry"]].copy()
    arts = sorted(cand["article"].unique())
    print(f"resolving scope for {len(arts)} candidate articles")

    rows = []
    for i in range(0, len(arts), args.batch):
        chunk = arts[i:i + args.batch]
        vals = " ".join(
            "<https://en.wikipedia.org/wiki/%s>" % urllib.parse.quote(a, safe="_(),'-.")
            for a in chunk)
        q = """
SELECT ?article ?item ?itemLabel ?dod ?pit ?countryLabel ?mannerLabel WHERE {
  VALUES ?article { %s }
  ?article schema:about ?item .
  OPTIONAL { ?item wdt:P570 ?dod . }
  OPTIONAL { ?item wdt:P585 ?pit . }
  OPTIONAL { ?item wdt:P17  ?country . }
  OPTIONAL { ?item wdt:P1196 ?manner . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % vals
        print(f"  batch {i // args.batch + 1}: {len(chunk)} articles")
        for r in run_sparql(q, f"scope_{i:04d}_{len(chunk)}"):
            rows.append({
                "article": r["article"]["value"].split("/wiki/")[1],
                "item": r["item"]["value"].split("/")[-1],
                "label": r.get("itemLabel", {}).get("value"),
                "date": (r.get("dod") or r.get("pit") or {}).get("value", "")[:10],
                "country": r.get("countryLabel", {}).get("value"),
                "manner": r.get("mannerLabel", {}).get("value"),
            })

    out = pd.DataFrame(rows).drop_duplicates("article")
    # articles Wikidata returned nothing for — recorded, never silently dropped
    missing = sorted(set(arts) - set(out["article"]))
    for a in missing:
        out = pd.concat([out, pd.DataFrame([{"article": a, "item": None, "label": None,
                                             "date": "", "country": None, "manner": None}])],
                        ignore_index=True)
    out.to_csv(DATA_REFERENCE / "basket_scope.csv", index=False)

    have = out["date"].astype(str).str.len().ge(10)
    print(f"\n{len(out)} articles; {int(have.sum())} with a resolved date, "
          f"{len(missing)} unresolved by Wikidata")
    if len(missing):
        print("unresolved (need manual dates, recorded not dropped):")
        for a in missing[:20]:
            print("   ", a)
    yr = pd.to_datetime(out.loc[have, "date"], errors="coerce").dt.year
    print("\nby decade of death:")
    print(yr.floordiv(10).mul(10).value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
