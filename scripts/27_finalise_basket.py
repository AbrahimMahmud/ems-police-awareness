"""Finalise the CAI-D Wikipedia article basket, with every decision recorded.

WHY THIS EXISTS
---------------
`wiki_ext` is summed over the articles listed in wikipedia_article_resolution.csv
(11_fetch_awareness_components.py:49-50), so that file IS the treatment index's
input. The committed version was selected by ranking victims on the retired
Twitter series and keeping the top 150 (09_fetch_public_data.py:83,148). Twitter
coverage stops at death-year 2020, so the basket contains ZERO victims killed
after 2020 (finding X2) — a treatment index whose inputs end in 2020 cannot
measure attention in 2021-2024.

This script replaces that selection with one that is public, re-runnable, and
blind to every outcome:

  24_build_wiki_basket.py    walk the live Wikipedia category tree
  26_resolve_basket_scope.py resolve date/country/manner from Wikidata
  27 (this)                  apply the scope rule and write the basket

WHAT IT DOES NOT DO
-------------------
It does not gate on the victim registry (finding T9). Mapping Police Violence,
which is 100% of the registry, does not carry Daniel Prude, Sandra Bland, Marvin
Scott, Javier Ambler or Leneal Frazier — checked against the MPV workbook
directly. Those omissions run WITH this paper's hypothesis rather than across it:
they are in-custody, restraint and mental-health-crisis deaths. Registry-gating
would delete the most on-hypothesis events in the study while looking
principled, so the registry supplies dates and race where it can and decides
nothing.

It also does not rank victims. Ranking the basket by attention would let the
index choose its own inputs, which is the defect that retired trends_victims.

EVERY article gets a row in the decisions file with the reason it was kept or
dropped, so the scope rule is reviewable rather than implicit.

Outputs:
  data/reference/wikipedia_article_resolution.csv   the basket wiki_ext reads
  data/reference/basket_decisions.csv               every include/exclude + reason
"""

import argparse
import re
import shutil
import unicodedata

import pandas as pd

from config import DATA_REFERENCE

PERSON_PREFIXES = ("Killing_of_", "Shooting_of_", "Death_of_", "Murder_of_",
                   "Police_shooting_of_")
IN_RANGE = ("2013-01-01", "2024-12-31")   # registry era; see docs/REBUILD_PLAN.md

# Countries other than the US are out of scope: the outcome is NYC EMS demand,
# and attention to a killing by French or Canadian police is a different
# treatment. Recorded per article rather than assumed.
NON_US = {"France", "Canada", "Brazil", "United Kingdom", "Australia"}


def norm(x):
    """Normalise a name for matching: accents, punctuation, suffixes, nicknames."""
    x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    x = re.sub(r'"[^"]*"', " ", x)          # Emantic "EJ" Fitzgerald Bradford
    x = x.lower().replace(".", "").replace(",", "").replace("'", "").replace("-", " ")
    x = re.sub(r"\b(jr|sr|ii|iii|iv)\b", " ", x)
    return " ".join(x.split())


def first_last(k):
    p = k.split()
    return f"{p[0]} {p[-1]}" if len(p) >= 2 else k


def victim_name(title):
    t = title.replace("_", " ")
    for pre in ("Killing of ", "Shooting of ", "Death of ", "Murder of ",
                "Police shooting of "):
        if t.startswith(pre):
            t = t[len(pre):]
            break
    return t.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="overwrite wikipedia_article_resolution.csv (keeps a _legacy copy)")
    args = ap.parse_args()

    basket = pd.read_csv(DATA_REFERENCE / "wiki_basket.csv")
    scope = pd.read_csv(DATA_REFERENCE / "basket_scope.csv")
    reg = pd.read_csv(DATA_REFERENCE / "victim_registry.csv", parse_dates=["date"])

    # ---- registry lookups: exact, then first+last. Both, because article titles
    # ---- carry short names ("Antwon Rose Jr.") where MPV carries full ones
    # ---- ("Antwon Michael Rose II"), and exact matching alone silently loses them.
    reg["k"] = reg["name"].map(norm)
    exact = reg.groupby("k")["date"].min()
    fl = reg.assign(fl=reg["k"].map(first_last)).groupby("fl")["date"].min()

    df = basket[basket["article"].str.startswith(PERSON_PREFIXES)
                | basket["in_registry"]].copy()
    df["person"] = df["article"].map(victim_name)
    # "Killing of Dhal Apet and Lueth Mo" covers two victims; date on the first.
    df["k"] = df["person"].str.split(" and ").str[0].map(norm)

    sc = scope.set_index("article")
    df["wd_date"] = pd.to_datetime(df["article"].map(sc["date"]), errors="coerce")
    df["country"] = df["article"].map(sc["country"])
    df["reg_date"] = df["k"].map(exact)
    df["reg_date"] = df["reg_date"].fillna(df["k"].map(first_last).map(fl))
    df["death_date"] = df["wd_date"].fillna(df["reg_date"])
    df["date_source"] = df.apply(
        lambda r: "wikidata" if pd.notna(r["wd_date"])
        else ("registry" if pd.notna(r["reg_date"]) else "unresolved"), axis=1)

    # ---- the scope rule, applied one reason at a time ----
    def decide(r):
        if r["country"] in NON_US:
            return "exclude", f"not a US killing (country={r['country']})"
        if pd.isna(r["death_date"]):
            return "exclude", "no date resolvable from Wikidata or the registry"
        d = r["death_date"]
        if d < pd.Timestamp(IN_RANGE[0]):
            return "exclude", f"before the registry era ({d.date()})"
        if d > pd.Timestamp(IN_RANGE[1]):
            return "exclude", f"after the study window ({d.date()})"
        return "include", f"in range ({d.date()}, {r['date_source']})"

    df[["decision", "reason"]] = df.apply(lambda r: pd.Series(decide(r)), axis=1)
    df = df.sort_values(["decision", "death_date", "article"])

    cols = ["article", "person", "death_date", "date_source", "country",
            "in_registry", "decision", "reason"]
    df[cols].to_csv(DATA_REFERENCE / "basket_decisions.csv", index=False)

    keep = df[df["decision"] == "include"].copy()
    print(f"candidates {len(df)} -> included {len(keep)} articles "
          f"({keep['k'].nunique()} distinct people)")
    print(f"  dates: {(keep['date_source'] == 'wikidata').sum()} wikidata, "
          f"{(keep['date_source'] == 'registry').sum()} registry")
    print(f"  not in the victim registry: {int((~keep['in_registry'].fillna(False)).sum())} "
          "— these are the MPV coverage gaps (finding T9)")
    print("\nexclusions by reason:")
    exc = df[df["decision"] == "exclude"]["reason"].str.replace(r"\(.*\)", "", regex=True)
    print(exc.value_counts().to_string())

    post2020 = int((keep["death_date"] > "2020-12-31").sum())
    print(f"\nvictims killed after 2020: {post2020}   (the retired basket had 0)")

    for canary in ["daniel prude", "sandra bland", "george floyd", "elijah mcclain"]:
        print(f"  canary {canary:<16} included: {canary in set(keep['k'])}")

    out = DATA_REFERENCE / "wikipedia_article_resolution.csv"
    if args.apply:
        legacy = DATA_REFERENCE / "wikipedia_article_resolution_legacy.csv"
        if out.exists() and not legacy.exists():
            shutil.copy(out, legacy)
            print(f"\nkept the Twitter-selected basket at {legacy.name}")
        keep[["person", "article"]].rename(columns={"person": "name"}).to_csv(
            out, index=False)
        print(f"wrote {out.name}: {len(keep)} articles")
    else:
        print("\ndry run — pass --apply to overwrite wikipedia_article_resolution.csv")


if __name__ == "__main__":
    main()
