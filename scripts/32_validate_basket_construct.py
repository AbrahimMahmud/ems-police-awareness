"""Does each basket article describe POLICE violence? Decided on evidence, per article.

WHY THIS EXISTS
---------------
CAI-D is supposed to measure public attention to police violence. Nothing in the
pipeline ever tested that. `27_finalise_basket.py` decides scope on two facts —
country and date — and never asks who did the killing. Wikidata's manner-of-death
property (P1196) is present on 6 of 174 candidates, so it cannot gate anything,
and where it is present it is unreliable: Wikidata records Eric Garner's manner
of death as "natural causes".

What actually admitted articles to the basket was the category the crawl reached
them through, and `24_build_wiki_basket.py` records only the FIRST one it hit in
breadth-first order. For 61 of 120 included articles — 51% — that first category
was a TOPIC: "Black Lives Matter" (57) or "2020/2021 United States racial unrest"
(4). A topic category is not a claim about who killed anyone, and the basket
carried no other evidence either way.

It was not harmless. The basket admitted killings by civilians (Ahmaud Arbery,
Renisha McBride, Markeis McGlockton, James Craig Anderson), a death at a party
that police merely investigated (Tamla Horsford), and Micah Xavier Johnson — the
Dallas gunman who killed five police officers, whose article dates to 2016-07-08,
the single highest day in the whole treatment index.

WHAT THIS SCRIPT DOES
---------------------
It fetches every candidate article's FULL category set and its opening sentence,
and classifies each one from that evidence:

  police_violence  a category asserting police action, or presence in the
                   Mapping Police Violence registry
  anti_police      the subject is categorised as a perpetrator — attention to
                   violence AGAINST police is the opposite construct
  unestablished    nothing in the evidence establishes police as the actor

The distinction that does the work is between a category that names an ACTOR and
one that names a TOPIC:

  ACTOR    "African Americans shot dead by law enforcement officers in Ohio",
           "Deaths in police custody in the United States", "Cleveland Division
           of Police", "Los Angeles County Sheriff's Department", "Law
           enforcement in Wisconsin". Wikipedia files an incident under a named
           agency when that agency was involved.
  TOPIC    "Law enforcement controversies in the United States", "Police
           brutality in the United States", "Protests against police brutality".

Both appear on real police shootings, but only the topic ones appear on deaths
police had nothing to do with. Tamla Horsford carries "Law enforcement
controversies in the United States" and died at a party. Carlos Carson carries
"Police brutality in the United States" and "Police brutality in the 2020s", and
his article's first sentence says he "was assaulted and killed by a private
security guard". Jacob Blake carries the controversy category too — and also
"Law enforcement in Wisconsin", because an officer shot him. Only the second kind
of category survives that test, so only the second kind counts.

Registry presence counts as a POSITIVE signal and never as a gate. Mapping Police
Violence lists only police killings, so being in it establishes the actor; NOT
being in it establishes nothing, because MPV omits Daniel Prude, Sandra Bland,
Marvin Scott, Javier Ambler and Leneal Frazier (finding T9). Using absence to
exclude would delete the most on-hypothesis events in the study.

THE CANARIES ARE THE POINT
--------------------------
A classifier built from patterns can drift into looking principled while being
wrong, which is the failure this whole script exists to undo. So it carries two
lists of cases whose answer was verified against the articles themselves, and it
REFUSES TO WRITE if any of them lands on the wrong side. Every rule element below
was added or demoted because a canary caught it:

  - "Police brutality in X" started as an actor signal. Carlos Carson forced its
    demotion; his article says a private security guard killed him.
  - The named-agency patterns were added because Tamir Rice, Anthony Weber and
    Leneal Frazier are unambiguous police killings that carry no "killed by law
    enforcement" category at all.
  - Non-fatal cases (Charles Kinsey, Jacob Blake) are IN. The construct is
    attention to police violence, not to police killings, and Kenosha followed a
    shooting the victim survived.

Outputs:
  data/reference/basket_construct_review.csv   one row per candidate, with the
      classification, the category it rests on, and the article's own first
      sentence as citable evidence
  data/reference/basket_strict.csv   (--apply) police_violence only: the primary
  data/reference/basket_broad.csv    (--apply) primary + unestablished: the
      pre-registered sensitivity. anti_police is in NEITHER.
"""

import argparse
import json
import re

import pandas as pd

import wikimedia as wm
from config import CAI_D_BASKET, DATA_PROCESSED, DATA_REFERENCE
from provenance import log_source

CAT_CACHE = DATA_PROCESSED / "wiki_category_cache"

# A category that names WHO ACTED.
ACTOR = re.compile(r"""
    (shot|killed|murder(s|ed)?|deaths?)\s+(dead\s+)?by\s+(law\s+enforcement|police)
  | deaths?\s+in\s+police\s+custody
  | asphyxia-related\s+deaths\s+by\s+law\s+enforcement
  | victims?\s+of\s+police\s+brutality
  | filmed\s+killings\s+by\s+law\s+enforcement
  | police\s+shootings?
  | \bpolice\s+department\b | \bdivision\s+of\s+police\b
  | \bsheriff'?s\s+(department|office)\b
  | \blaw\s+enforcement\s+in\s+\w
  | \bhighway\s+patrol\b | \bstate\s+police\b | \bborder\s+patrol\b
  | \bdepartment\s+of\s+corrections\b
""", re.I | re.X)

# A category that names a TOPIC. Never sufficient on its own — see the docstring.
TOPIC = re.compile(r"""
    law\s+enforcement\s+controvers
  | police\s+brutality\s+in\b
  | protests?\s+against\s+police
""", re.I | re.X)

# WHERE it happened. Wikidata's country property (P17) is absent on 44 of the 109
# strict-basket articles — George Floyd, Deborah Danner and Manuel Ellis among
# them — so a country gate resting on P17 alone would demand excluding the most
# central cases in the study. That is a coverage gap in Wikidata, not evidence
# about the country. The category graph does carry it: every one of those 109
# articles sits under a US state, a US agency, or an explicit "in the United
# States" category, and none sits under a non-US one.
_STATES = ("Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
           "Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|"
           "Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|"
           "Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|"
           "New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|"
           "Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|"
           "Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia")
US = re.compile(r"\b(in|of)\s+the\s+United\s+States\b|\bUnited\s+States\b|\bAmerican\b"
                r"|\b(in|of)\s+(" + _STATES + r")\b", re.I)
NON_US = re.compile(r"\b(France|French|Canada|Canadian|Brazil|Brazilian|United\s+Kingdom|"
                    r"British|England|Australia|Australian|Germany|German)\b", re.I)


# Attention to violence AGAINST police measures the opposite of this treatment.
PERPETRATOR = re.compile(r"""
    (murder|killing|deaths?)s?\s+of\s+(american\s+)?(police|law\s+enforcement)
  | people\s+who\s+killed\s+(police|law\s+enforcement)
  | attacks?\s+on\s+(police|law\s+enforcement)
  | \b(american\s+)?(mass\s+)?murderers\b
  | \b(spree|mass)\s+(shooters|killers)\b
""", re.I | re.X)

# Verified against the articles themselves, not recalled. If the rule stops
# agreeing with these, the rule changed meaning and must not be applied silently.
MUST_BE_POLICE = [
    "George Floyd", "Daniel Prude", "Eric Garner", "Tamir Rice", "Sandra Bland",
    "Breonna Taylor", "Walter Scott", "Elijah McClain", "Deborah Danner",
    "Charles Kinsey", "Jacob Blake", "Anthony Weber", "Leneal Frazier",
    "Casey Goodson", "Manuel Ellis", "Javier Ambler",
]
MUST_NOT_BE_POLICE = [
    "Ahmaud Arbery", "Renisha McBride", "Markeis McGlockton",
    "James Craig Anderson", "Tamla Horsford", "Nina Pop", "James Scurlock",
    "Carlos Carson", "Deona Marie Knajdek",
]


def fetch_categories(articles, batch=45):
    """Every non-hidden category of each article, following continuations."""
    out = {a: [] for a in articles}
    for i in range(0, len(articles), batch):
        chunk = articles[i:i + batch]
        cont = {}
        while True:
            d = wm.api("en.wikipedia.org",
                       {"prop": "categories", "cllimit": "max", "clshow": "!hidden",
                        "titles": "|".join(t.replace("_", " ") for t in chunk), **cont},
                       cache_dir=CAT_CACHE, label=f"categories {i // batch + 1}")
            for pg in d.get("query", {}).get("pages", {}).values():
                t = pg.get("title", "").replace(" ", "_")
                out.setdefault(t, []).extend(
                    c["title"].replace("Category:", "") for c in pg.get("categories", []))
            if "continue" not in d:
                break
            cont = d["continue"]
        print(f"  categories: {i + len(chunk)}/{len(articles)}", flush=True)
    return out


def fetch_leads(articles, batch=20):
    """First sentence of each article — the evidence a reader can check."""
    out = {}
    for i in range(0, len(articles), batch):
        chunk = articles[i:i + batch]
        d = wm.api("en.wikipedia.org",
                   {"prop": "extracts", "exintro": 1, "explaintext": 1,
                    "exlimit": "max", "redirects": 1,
                    "titles": "|".join(t.replace("_", " ") for t in chunk)},
                   cache_dir=CAT_CACHE, label=f"extracts {i // batch + 1}")
        for pg in d.get("query", {}).get("pages", {}).values():
            txt = (pg.get("extract") or "").strip().replace("\n", " ")
            out[pg.get("title", "").replace(" ", "_")] = txt.split(". ")[0][:400]
        print(f"  leads: {i + len(chunk)}/{len(articles)}", flush=True)
    return out


def classify(cats, in_registry):
    actor = sorted({c for c in cats if ACTOR.search(c)})
    topic = sorted({c for c in cats if TOPIC.search(c) and c not in actor})
    perp = sorted({c for c in cats if PERPETRATOR.search(c)})
    if perp:
        return "anti_police", f"categorised as a perpetrator: {perp[0]}", perp[0]
    if actor:
        return "police_violence", f"police-action category: {actor[0]}", actor[0]
    if in_registry:
        return "police_violence", "listed in the Mapping Police Violence registry", ""
    if topic:
        return ("unestablished",
                f"only a topic category, which does not name an actor: {topic[0]}", topic[0])
    return "unestablished", f"no law-enforcement category among {len(cats)}", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write basket_strict.csv and basket_broad.csv")
    args = ap.parse_args()

    dec = pd.read_csv(DATA_REFERENCE / "basket_decisions.csv")
    arts = sorted(dec["article"].unique())
    print(f"classifying {len(arts)} candidate articles")
    cats = fetch_categories(arts)
    leads = fetch_leads(arts)

    rows = []
    for _, r in dec.iterrows():
        cs = cats.get(r["article"], [])
        reg = bool(r["in_registry"]) if pd.notna(r["in_registry"]) else False
        klass, why, cat = classify(cs, reg)
        us = sorted({c for c in cs if US.search(c)})
        nonus = sorted({c for c in cs if NON_US.search(c)})
        rows.append({"article": r["article"], "person": r["person"],
                     "scope_decision": r["decision"], "in_registry": reg,
                     "construct": klass, "reason": why, "evidence_category": cat,
                     "n_categories": len(cs),
                     "wikidata_country": r.get("country"),
                     "us_evidence": us[0] if us else "",
                     "non_us_evidence": nonus[0] if nonus else "",
                     "article_first_sentence": leads.get(r["article"], "")})
    d = pd.DataFrame(rows)
    d.to_csv(DATA_REFERENCE / "basket_construct_review.csv", index=False)

    # ---- canaries. Refuse to write a basket from a rule that has drifted. ----
    by_person = d.set_index("person")["construct"].to_dict()
    bad = ([f"{p}: expected police_violence, got {by_person.get(p, 'ABSENT')}"
            for p in MUST_BE_POLICE if by_person.get(p) != "police_violence"]
           + [f"{p}: expected NOT police_violence, got police_violence"
              for p in MUST_NOT_BE_POLICE if by_person.get(p) == "police_violence"])
    if bad:
        raise SystemExit(
            "CANARY FAILURE — the classification rule no longer agrees with cases "
            "verified against the articles themselves:\n  " + "\n  ".join(bad)
            + "\nbasket_construct_review.csv was written for inspection; no basket "
              "was produced.")
    print(f"\ncanaries: {len(MUST_BE_POLICE)} police and "
          f"{len(MUST_NOT_BE_POLICE)} non-police cases all classified correctly")
    _p = d[d["construct"] == "police_violence"]
    print(f"US evidence: {int((_p['wikidata_country'] == 'United States').sum())} from "
          f"Wikidata, {int(_p['us_evidence'].astype(bool).sum())} from a category, "
          f"{int((~_p['us_evidence'].astype(bool)).sum())} with none; "
          f"{int(_p['non_us_evidence'].astype(bool).sum())} carrying non-US evidence")

    inc = d[d["scope_decision"] == "include"]
    print(f"\nin scope: {len(inc)} articles")
    for k, n in inc["construct"].value_counts().items():
        print(f"  {k:16s} {n}")
    print("\nremoved from the strict basket:")
    print(inc[inc["construct"] != "police_violence"]
          [["person", "construct", "reason"]].to_string(index=False, max_colwidth=58))

    strict = inc[inc["construct"] == "police_violence"]
    broad = inc[inc["construct"] != "anti_police"]
    print(f"\nstrict basket {len(strict)} articles; broad basket {len(broad)}; "
          f"anti-police excluded from both: {int((inc['construct'] == 'anti_police').sum())}")

    if args.apply:
        for name, frame in (("basket_strict.csv", strict), ("basket_broad.csv", broad)):
            frame[["person", "article"]].rename(columns={"person": "name"}).to_csv(
                DATA_REFERENCE / name, index=False)
            print(f"wrote {name}: {len(frame)} articles")

        # This script owns the file the rest of the pipeline reads. 27 decides
        # WHEN and WHERE a killing happened; only this one asks WHO acted, so
        # letting 27 publish the basket would ship a treatment index whose
        # construct has never been tested — which is how it shipped until now.
        chosen = {"strict": strict, "broad": broad}[CAI_D_BASKET]
        out = DATA_REFERENCE / "wikipedia_article_resolution.csv"
        chosen[["person", "article"]].rename(columns={"person": "name"}).to_csv(
            out, index=False)
        print(f"wrote {out.name} from the {CAI_D_BASKET} basket: "
              f"{len(chosen)} articles (config.CAI_D_BASKET)")
        log_source("D3",
                   f"Basket construct review: {len(strict)} police_violence, "
                   f"{int((inc['construct'] == 'unestablished').sum())} unestablished, "
                   f"{int((inc['construct'] == 'anti_police').sum())} anti_police",
                   "English Wikipedia category graph (S15) + MPV registry (S10)",
                   out_file=DATA_REFERENCE / "basket_construct_review.csv")
    else:
        print("\ndry run — pass --apply to write basket_strict.csv / basket_broad.csv")


if __name__ == "__main__":
    main()
