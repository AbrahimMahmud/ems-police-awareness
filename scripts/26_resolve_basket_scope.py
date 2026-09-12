"""Resolve scope metadata for every candidate basket article, from Wikidata.

WHY THIS EXISTS (finding T9)
-----------------------------
24_build_wiki_basket.py walks the live Wikipedia category tree and returns ~174
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
obvious, is never checked, and turns out wrong. Every fact here is fetched and
cached, so a referee can re-run it.

WHY THE TRANSPORT CHANGED (findings N1, N2, N3 — 2026-09-12)
-------------------------------------------------------------
This script used to send one batched SPARQL query per chunk to
query.wikidata.org. It now uses the MediaWiki action API
(action=wbgetentities&sites=enwiki&titles=), which maps Wikipedia titles to
items and returns their claims in the same call.

The change was made only after running both routes over the same 164 articles
and comparing field by field. `manner` agreed on all 164. Everything that
differed, the action API got right:

  N1. THREE ARTICLES WERE KEYED ON A NAME THAT COULD NEVER JOIN. The SPARQL
      VALUES clause percent-encoded each title, and the result was read back
      with `.split("/wiki/")[1]`, so every non-ASCII article was stored under
      its ENCODED name — "Killing_of_Jos%C3%A9_Campos_Torres" against a basket
      that holds "Killing_of_José_Campos_Torres". The scope row existed and was
      unreachable. 27_finalise_basket.py then found no date, fell through to the
      registry, matched a different person, and admitted José Campos Torres as a
      2014 killing. Wikidata holds 1977-05-05, which is out of range: the
      article should have been excluded, and a URL-encoding mismatch put it in
      the treatment index instead.

  N2. MA'KHIA BRYANT WAS SILENTLY UNRESOLVED. SPARQL returned nothing for her;
      the action API returns Q123298430, 2021-04-20, United States. She is one
      of the April 2021 episode's central events.

  N3. DATE PRECISION WAS FABRICATED. Wikidata encodes a month-precision date as
      2011-10-00 and a year-precision one as 2015-00-00. SPARQL's xsd:dateTime
      rendering silently turned those into 2011-10-01 and 2015-01-01, inventing
      a day the source does not claim. Three articles were affected. The day is
      now preserved as returned and the precision recorded in its own column, so
      a scope rule at a window boundary can see what it is actually resting on.

The action API also returned strictly MORE: 82 countries against 80, 112 dates
against 111. No field, on any article, was worse.

CACHING IS PER ARTICLE, ON PURPOSE
-----------------------------------
The old cache key was `scope_{offset:04d}_{len(chunk)}`, so changing --batch
changed every key and discarded every previously fetched byte — which is exactly
what this script's own failure message tells a reader to do when Wikidata
refuses. "The cache makes it resumable" was false precisely when it mattered.
Each article is now cached under a hash of its own title, so batch size is a
request-shaping detail and nothing more, and an interrupted run resumes at the
article it stopped on.

Rate limiting is handled in scripts/wikimedia.py: Wikimedia's edge runs a token
bucket keyed on the CLIENT IP and shared across every Wikimedia host, and it
says how long to wait in Retry-After. This script used to ignore that header and
sleep a fixed 70s.

Outputs:
  data/reference/basket_scope.csv
      article, item, label, date, date_precision, country, manner
"""

import argparse
import json
import urllib.parse

import pandas as pd

import wikimedia as wm
from config import DATA_PROCESSED, DATA_REFERENCE

CACHE = DATA_PROCESSED / "wikidata_entity_cache"

PERSON_PREFIXES = ("Killing_of_", "Shooting_of_", "Death_of_", "Murder_of_",
                   "Police_shooting_of_")

# date of death, then point in time for articles whose item is the EVENT rather
# than the person; country; manner of death.
CLAIMS = {"P570": "dod", "P585": "pit", "P17": "country_qid", "P1196": "manner_qid"}

EMPTY = {"item": None, "label": None, "dod": None, "pit": None,
         "country_qid": None, "manner_qid": None}


def _first(claims, pid):
    """First non-novalue claim for pid. Dates keep Wikidata's own precision."""
    for c in claims.get(pid, []):
        ds = c.get("mainsnak", {}).get("datavalue")
        if not ds:
            continue
        v = ds["value"]
        if isinstance(v, dict) and "time" in v:
            return v["time"][1:11]          # +2011-10-00T00:00:00Z -> 2011-10-00
        if isinstance(v, dict) and "id" in v:
            return v["id"]
        return v
    return None


def _cache_file(title):
    return CACHE / f"{wm._key_for('enwiki:' + title)}.json"


def resolve_articles(titles, batch):
    """title -> claim record. Cached per article, so --batch cannot invalidate it."""
    out, need = {}, []
    for t in titles:
        p = _cache_file(t)
        if p.exists():
            try:
                out[t] = json.loads(p.read_text())
                continue
            except json.JSONDecodeError:
                p.unlink(missing_ok=True)
        need.append(t)
    print(f"  {len(out)} cached, {len(need)} to fetch")

    for i in range(0, len(need), batch):
        chunk = need[i:i + batch]
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
               "&sites=enwiki&sitefilter=enwiki&languages=en"
               "&props=claims%7Clabels%7Csitelinks&titles="
               + urllib.parse.quote("|".join(t.replace("_", " ") for t in chunk),
                                    safe="|"))
        d = wm.get_json(url, label=f"scope batch {i // batch + 1}")

        # Key on the sitelink the API returns, NEVER on a name this script
        # encoded. That inversion is finding N1: the old path read the title
        # back out of a percent-encoded IRI and stored the encoded form.
        by_title = {}
        for qid, ent in d.get("entities", {}).items():
            if "missing" in ent:
                continue
            sl = ent.get("sitelinks", {}).get("enwiki", {}).get("title")
            if not sl:
                continue
            cl = ent.get("claims", {})
            by_title[sl.replace(" ", "_")] = {
                "item": qid,
                "label": ent.get("labels", {}).get("en", {}).get("value"),
                **{n: _first(cl, pid) for pid, n in CLAIMS.items()},
            }

        CACHE.mkdir(parents=True, exist_ok=True)
        for t in chunk:
            # An article Wikidata holds no item for is cached as EMPTY. That is a
            # real absence and must be distinguishable from "we never asked" —
            # the distinction 27_finalise_basket.py refuses to finalise without.
            rec = by_title.get(t, dict(EMPTY))
            _cache_file(t).write_text(json.dumps(rec))
            out[t] = rec
        print(f"  batch {i // batch + 1}: {len(chunk)} asked, "
              f"{sum(1 for t in chunk if out[t]['item'])} resolved", flush=True)
    return out


def label_qids(qids, batch=45):
    """QID -> English label, for country and manner."""
    qids = sorted({q for q in qids if q})
    lab = {}
    for i in range(0, len(qids), batch):
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
               "&props=labels&languages=en&ids=" + "|".join(qids[i:i + batch]))
        d = wm.get_json(url, cache_dir=CACHE, label="qid labels")
        for q, e in d.get("entities", {}).items():
            lab[q] = e.get("labels", {}).get("en", {}).get("value")
    return lab


def precision_of(date):
    """What Wikidata actually claims: a day, a month, or only a year."""
    if not date:
        return "none"
    if date.endswith("-00-00"):
        return "year"
    if date.endswith("-00"):
        return "month"
    return "day"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=45,
                    help="articles per request; affects pacing only, never the cache")
    args = ap.parse_args()

    b = pd.read_csv(DATA_REFERENCE / "wiki_basket.csv")
    cand = b[b["article"].str.startswith(PERSON_PREFIXES) | b["in_registry"]].copy()
    arts = sorted(cand["article"].unique())
    print(f"resolving scope for {len(arts)} candidate articles")

    rec = resolve_articles(arts, args.batch)
    lab = label_qids([r["country_qid"] for r in rec.values()]
                     + [r["manner_qid"] for r in rec.values()])

    rows = []
    for a in arts:
        r = rec[a]
        date = r["dod"] or r["pit"] or ""
        rows.append({"article": a, "item": r["item"], "label": r["label"],
                     "date": date, "date_precision": precision_of(date),
                     "country": lab.get(r["country_qid"]),
                     "manner": lab.get(r["manner_qid"])})
    out = pd.DataFrame(rows)

    # EVERY candidate gets a row, including the ones Wikidata holds nothing for.
    # A missing row and an empty row mean different things, and only one of them
    # is a reason to exclude an article.
    assert len(out) == len(arts), "every candidate must carry a scope row"
    out.to_csv(DATA_REFERENCE / "basket_scope.csv", index=False)

    have = out["date"].astype(str).str.len().ge(10)
    unresolved = out["item"].isna().sum()
    print(f"\n{len(out)} articles; {int(have.sum())} with a date, "
          f"{int(out['country'].notna().sum())} with a country, "
          f"{int(unresolved)} with no Wikidata item at all")
    print("  date precision: "
          + ", ".join(f"{k}={v}" for k, v in out["date_precision"].value_counts().items()))
    if unresolved:
        print("no Wikidata item (a real absence, recorded not dropped):")
        for a in out.loc[out["item"].isna(), "article"].head(20):
            print("   ", a)

    yr = pd.to_datetime(out.loc[have, "date"].str.replace("-00", "-01", regex=False),
                        errors="coerce").dt.year
    print("\nby decade of death:")
    print(yr.floordiv(10).mul(10).value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
