"""Verify every data source, every link, and every number claimed about them.

WHY THIS EXISTS
---------------
This project's recurring failure is not a wrong number. It is a number that
reads as established because nobody re-checked it: a provenance row whose hash
stopped matching its file two commits ago, a documented endpoint that has moved,
a coverage figure quoted from an artifact that has since been rebuilt. Prose
does not notice; a scan does.

So there are three registers and one scan over them:

  data/reference/source_register.json      what every source IS (edited by hand)
  docs/CLAIMS_REGISTER.csv                 every number claimed about them
  data/reference/source_verification_log.csv   what happened on each scan

and docs/SOURCE_REGISTER.md is GENERATED from the first and the third, so the
document a reader reviews and the scan a machine runs cannot drift apart.

A FAILED SCAN IS A RESULT, NOT A RETRY-UNTIL-GREEN
--------------------------------------------------
The log is append-only. A source that fails today and passes tomorrow leaves
BOTH records, because "when did this last actually work" is the question the log
exists to answer. Statuses are deliberately distinguished:

  verified      checked, and it holds
  mismatch      checked, and it does NOT hold - the artifact differs from record
  absent        the artifact is not on disk
  failed        the endpoint answered with an error status
  unreachable   the endpoint could not be contacted at all (network, DNS, TLS)
  unverifiable  can never be checked from this repository - a privately supplied
                file, or an upstream service that no longer exists. This is a
                real, permanent category, not a euphemism for "not done yet".
  template      the URL is a format string, not an address; skipped explicitly
  skipped       not attempted on this run (--offline)

"unreachable" is never recorded as "verified". A source we could not reach is a
source we do not know about.

CLAIMS
------
Each row of CLAIMS_REGISTER.csv names a document, a template containing {}, an
artifact, and an expression over that artifact. The scan computes the value,
renders it into the template, and requires the result to appear VERBATIM in the
document. So a number goes wrong in either direction and the check fails: edit
the document and the rendered text is no longer found; rebuild the data and the
computed value no longer matches what the document says.

Scope is the paper-facing documents. docs/AUDIT_FINDINGS.csv is deliberately
excluded: its corrected_claim fields are dated records of what was true when a
defect was found, and re-verifying them against today's data would erase their
meaning.

  python 31_verify_sources.py --scan        everything, including the network
  python 31_verify_sources.py --offline     artifacts and claims only
  python 31_verify_sources.py --claims-only claims only (what the suite runs)
"""

import argparse
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATA_REFERENCE, PROJECT_ROOT

REGISTER_JSON = DATA_REFERENCE / "source_register.json"
CLAIMS_CSV = PROJECT_ROOT / "docs" / "CLAIMS_REGISTER.csv"
LOG_CSV = DATA_REFERENCE / "source_verification_log.csv"
REGISTER_MD = PROJECT_ROOT / "docs" / "SOURCE_REGISTER.md"
PROVENANCE_CSV = DATA_REFERENCE / "data_sources.csv"

UA = {"User-Agent": "ems-police-awareness-research/1.0 (academic; contact via repository)"}
LOG_COLUMNS = ["run_utc", "run_id", "kind", "source_id", "target", "status", "detail"]

# Statuses that mean "this was checked and it holds".
GOOD = {"verified", "unverifiable", "template", "skipped"}


# ---------------------------------------------------------------------------
# registers
# ---------------------------------------------------------------------------
def load_register():
    d = json.loads(REGISTER_JSON.read_text())
    ids = [s["id"] for s in d["sources"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"source_register.json has duplicate ids: {dupes}")
    return d["sources"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def realised(path):
    """Row count and date span AS THEY ARE, not as intended."""
    p = Path(path)
    try:
        d = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    except Exception as e:
        return f"unreadable: {type(e).__name__}"
    span = ""
    for c in d.columns:
        if "date" in str(c).lower():
            s = pd.to_datetime(d[c], errors="coerce").dropna()
            if len(s):
                span = f", {s.min().date()}..{s.max().date()}"
            break
    return f"{len(d):,} rows{span}"


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def check_link(url, probe=None):
    """HEAD, falling back to a ranged GET. Returns (status, detail).

    An API ROOT is not an address. Requesting
    .../metrics/pageviews/per-article/ with no path parameters returns 404, and
    recording that as a failure would be a false statement about a working
    endpoint - while skipping it would verify nothing at all. So an entry that
    is a root carries a `probe`: a concrete request whose success really does
    demonstrate that the endpoint serves us. The probe is what gets fetched and
    what the log records.
    """
    if "{" in url and not probe:
        return "template", "format string, and no concrete probe is registered"
    target = probe or url
    ctx = ssl.create_default_context()
    ca = Path("/root/.ccr/ca-bundle.crt")
    if ca.exists():
        ctx.load_verify_locations(str(ca))

    # A 429 says "ask again later", not "this endpoint is broken". Conflating a
    # rate limit with a permanent failure is the exact mistake that once made
    # this project report Alton Sterling's pre-rename title as having no data
    # when it had 1.86M views, so it is handled explicitly here too.
    for attempt in range(3):
        status, detail = _try_link(target, ctx, probe)
        if status != "ratelimited":
            return status, detail
        time.sleep(min(30, 5 * 2 ** attempt))
    return "unreachable", "rate limited (HTTP 429) after 3 attempts - not a verdict on the endpoint"


def _try_link(target, ctx, probe=None):
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(target, headers=dict(UA), method=method)
        if method == "GET":
            req.add_header("Range", "bytes=0-2047")
        try:
            with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
                ct = r.headers.get("Content-Type", "")
                final = r.geturl()
                moved = f" -> {final}" if final.rstrip("/") != target.rstrip("/") else ""
                via = f" (probe {probe})" if probe else ""
                return "verified", f"{method} {r.status} {ct}{moved}{via}"
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 405, 501):
                continue          # server refuses HEAD; try the ranged GET
            if e.code in (429, 503):
                return "ratelimited", ""
            if e.code in (401, 403, 407, 451):
                # A statement about OUR access, not about the resource. This
                # container reaches the internet through an egress proxy that
                # answers 403 for hosts outside its policy, so calling this
                # "failed" would assert something about the source that we
                # have not established.
                return "unreachable", (f"{method} HTTP {e.code} {e.reason} - our access, "
                                       "not necessarily the resource (egress policy?)")
            return "failed", f"{method} HTTP {e.code} {e.reason}"
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
            # ONLY transport failures are a statement about reachability. A
            # bare `except Exception` here caught a NameError in the success
            # path above and reported every working endpoint as "unreachable" -
            # a bug in this file, recorded as a fact about the internet. Any
            # other exception is ours and must surface.
            if method == "HEAD":
                continue
            return "unreachable", f"{type(e).__name__}: {e}"
    return "unreachable", "no method succeeded"


def check_artifact(src, rel):
    """Existence, hash against the provenance register, and realised coverage."""
    p = PROJECT_ROOT / rel
    if not p.exists():
        if src["status"] in ("retired", "unverifiable"):
            return "unverifiable", "artifact absent, and the source is " + src["status"]
        return "absent", "artifact is not on disk"

    digest = sha256_of(p)
    detail = f"sha256 {digest[:16]}, {realised(p)}"
    if not PROVENANCE_CSV.exists():
        return "verified", detail + "; no provenance register to compare against"
    prov = pd.read_csv(PROVENANCE_CSV)
    row = prov[(prov["source_id"] == src["id"]) & (prov["output_file"] == rel)]
    if not len(row):
        return "verified", detail + "; not registered in data_sources.csv"
    recorded = str(row["sha256"].iloc[-1] or "")
    if not recorded or recorded == "nan":
        return "verified", detail + "; register holds a payload hash only"
    if recorded == digest:
        return "verified", detail + "; matches the provenance register"

    # A PINNED exemption, for an artifact that cannot be re-registered by
    # re-running its fetch. It must name the exact bytes being accepted, so the
    # moment the file changes again the pin stops matching and this fails - it
    # excuses one specific file, never the check.
    pin = (src.get("accepted_hashes") or {}).get(rel)
    if pin and pin.get("sha256") == digest:
        return "verified", (f"{detail}; provenance register is stale and cannot be "
                            f"refreshed — accepted {pin.get('dated')}: {pin.get('reason')}")

    return "mismatch", (f"{detail}; provenance register says {recorded[:16]} "
                        f"(registered {row['accessed_utc'].iloc[-1]})")


def _normalise(text):
    """Collapse whitespace, and map the typographic minus to ASCII.

    Whitespace: a claim is about what the document SAYS, not how it is
    line-wrapped, so reflowing a paragraph must not break every claim whose text
    straddles a line break.

    U+2212 MINUS SIGN: the document is written in proper typography and says
    "-0.18" with a real minus, while Python renders a hyphen-minus. Only the
    minus is mapped - NOT the en dash, which is a range separator here ("2015-
    2024") and mapping it would create false matches rather than prevent false
    failures.
    """
    return " ".join(text.replace("\u2212", "-").split())


def check_claim(row, doc_cache):
    """Recompute a claimed number and require the document to say it."""
    doc = PROJECT_ROOT / str(row["doc"])
    if not doc.exists():
        return "absent", f"document {row['doc']} does not exist"
    if doc not in doc_cache:
        # Whitespace-normalised, because a claim is about what the document
        # SAYS, not how it happens to be line-wrapped. Without this, reflowing
        # a paragraph breaks every claim whose text straddles a line break -
        # which would train us to loosen the templates until they stop testing
        # anything.
        doc_cache[doc] = _normalise(doc.read_text())
    text = doc_cache[doc]

    # pandas reads an empty CSV cell as NaN, and str(nan) == "nan" - which is a
    # perfectly good relative path that does not exist, so a claim needing no
    # artifact would report "absent" instead of running.
    art = row.get("artifact")
    art = "" if art is None or (isinstance(art, float) and pd.isna(art)) else str(art).strip()
    d = None
    if art:
        p = PROJECT_ROOT / art
        if not p.exists():
            return "absent", f"artifact {art} does not exist"
        d = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)

    try:
        # A deliberately small namespace: enough to express an aggregation
        # over the artifact, not enough to reach the filesystem or the network
        # by accident. The expressions are ours and committed, so this is a
        # legibility constraint rather than a sandbox.
        safe = {"len": len, "sum": sum, "sorted": sorted, "min": min, "max": max,
                "int": int, "float": float, "round": round, "str": str,
                "abs": abs, "set": set, "list": list, "any": any, "all": all}
        # Everything goes in GLOBALS, not locals: a generator expression inside
        # eval gets its own scope and sees only globals, so names passed as
        # locals are invisible inside "sum(... for p in ...)".
        ns = {"__builtins__": safe, "d": d, "pd": pd, "np": np, "json": json,
              "Path": Path, "PROJECT_ROOT": PROJECT_ROOT}
        value = eval(str(row["expr"]), ns)
    except Exception as e:
        return "failed", f"expression raised {type(e).__name__}: {e}"

    try:
        rendered = str(row["fmt"]).format(value)
    except Exception as e:
        return "failed", f"format {row['fmt']!r} failed on {value!r}: {e}"

    expect = _normalise(str(row["template"]).replace("{}", rendered))
    if expect in text:
        return "verified", f"computed {rendered}; document agrees"
    # Distinguish "the number moved" from "the sentence was rewritten".
    stem = _normalise(str(row["template"]).split("{}")[0]).strip()
    if stem and stem in text:
        return "mismatch", (f"computed {rendered}, but the document does not say "
                            f"{expect!r} (the surrounding wording is present, so "
                            f"the number differs)")
    return "mismatch", (f"computed {rendered}; the claim's wording is not in "
                        f"{row['doc']} at all - the register is stale")


# ---------------------------------------------------------------------------
# document generation
# ---------------------------------------------------------------------------
def write_markdown(sources, log):
    latest = {}
    if len(log):
        for _, r in log.iterrows():
            latest.setdefault((r["source_id"], r["kind"], r["target"]), None)
            latest[(r["source_id"], r["kind"], r["target"])] = r
    lines = [
        "# Source register",
        "",
        "**Generated by `scripts/31_verify_sources.py`. Do not edit by hand** —",
        "edit `data/reference/source_register.json` and re-run the scan. The",
        "document and the scan are generated from one file so they cannot",
        "disagree.",
        "",
        f"Sources: {len(sources)} "
        f"({sum(s['status'] == 'live' for s in sources)} live, "
        f"{sum(s['status'] == 'retired' for s in sources)} retired, "
        f"{sum(s['status'] == 'unverifiable' for s in sources)} unverifiable).",
        "",
        "Every verification result ever recorded, including failures, is in",
        "`data/reference/source_verification_log.csv`, which is append-only.",
        "",
    ]
    if len(log):
        last = log["run_utc"].max()
        tail = log[log["run_utc"] == last]
        counts = tail["status"].value_counts().to_dict()
        lines += [f"Last scan: **{last}** — "
                  + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())), ""]
    else:
        lines += ["**No scan has been run.** Nothing below has been verified.", ""]

    for s in sources:
        lines += [f"## {s['id']} — {s['name']}", "",
                  f"- **Status**: {s['status']}",
                  f"- **Publisher**: {s['publisher']}"]
        if s.get("dataset_id"):
            lines.append(f"- **Dataset id**: `{s['dataset_id']}`")
        if s.get("landing_page"):
            lines.append(f"- **Landing page**: {s['landing_page']}")
        for u in s.get("endpoints", []):
            r = latest.get((s["id"], "link", u))
            mark = f" — _{r['status']}_ ({r['detail']})" if r is not None else " — _never scanned_"
            lines.append(f"- **Endpoint**: `{u}`{mark}")
        if not s.get("endpoints"):
            lines.append("- **Endpoint**: none — not obtained over the network")
        lines += [f"- **Access**: {s['access']}",
                  f"- **What we take**: {s['we_take']}",
                  f"- **Role**: {s['role']}"]
        for a in s.get("artifacts", []):
            r = latest.get((s["id"], "artifact", a))
            mark = f" — _{r['status']}_ ({r['detail']})" if r is not None else " — _never scanned_"
            lines.append(f"- **Artifact**: `{a}`{mark}")
        if s.get("cite_as"):
            lines.append(f"- **Cite as**: {s['cite_as']}")
        if s.get("terms_url"):
            lines.append(f"- **Terms**: {s['terms_url']}")
        if s.get("known_flaws"):
            lines += ["- **Known flaws**:"]
            lines += [f"  - {f}" for f in s["known_flaws"]]
        lines.append("")
    REGISTER_MD.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true", help="everything, network included")
    ap.add_argument("--offline", action="store_true", help="artifacts and claims only")
    ap.add_argument("--claims-only", action="store_true", help="claims only, no network")
    args = ap.parse_args()
    if not (args.scan or args.offline or args.claims_only):
        ap.error("choose --scan, --offline or --claims-only")

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_id = hashlib.sha256(run_utc.encode()).hexdigest()[:8]
    sources = load_register()
    rows = []

    def rec(kind, sid, target, status, detail):
        rows.append({"run_utc": run_utc, "run_id": run_id, "kind": kind,
                     "source_id": sid, "target": target, "status": status,
                     "detail": str(detail)[:400]})
        mark = "  ok  " if status in GOOD else f"{status.upper():^6}"
        print(f"[{mark}] {sid:<5} {kind:<8} {str(target)[:58]:<58} {str(detail)[:64]}")

    if not args.claims_only:
        print("\n== endpoints ==")
        for s in sources:
            probes = s.get("probes", {})
            for u in s.get("endpoints", []):
                if s["status"] == "unverifiable":
                    rec("link", s["id"], u, "unverifiable", "source cannot be re-obtained")
                elif args.offline:
                    rec("link", s["id"], u, "skipped", "--offline")
                else:
                    rec("link", s["id"], u, *check_link(u, probes.get(u)))
                    time.sleep(1.5)
            if not s.get("endpoints"):
                rec("link", s["id"], "(none)", "unverifiable" if s["status"] == "unverifiable"
                    else "template", "no endpoint: not obtained over the network")

        print("\n== artifacts ==")
        for s in sources:
            for a in s.get("artifacts", []):
                rec("artifact", s["id"], a, *check_artifact(s, a))

    print("\n== claims ==")
    if not CLAIMS_CSV.exists():
        print(f"  {CLAIMS_CSV.name} does not exist — no claims registered")
    else:
        claims = pd.read_csv(CLAIMS_CSV)
        cache = {}
        for _, r in claims.iterrows():
            rec("claim", str(r.get("source_id") or "-"), r["claim_id"],
                *check_claim(r, cache))

    log = pd.DataFrame(rows, columns=LOG_COLUMNS)
    prior = pd.read_csv(LOG_CSV) if LOG_CSV.exists() else pd.DataFrame(columns=LOG_COLUMNS)
    # APPEND-ONLY. A scan never erases what an earlier scan found.
    pd.concat([prior, log], ignore_index=True).to_csv(LOG_CSV, index=False)

    if not args.claims_only:
        write_markdown(sources, pd.concat([prior, log], ignore_index=True))
        print(f"\nregenerated {REGISTER_MD.relative_to(PROJECT_ROOT)}")

    counts = log["status"].value_counts().to_dict()
    bad = [r for r in rows if r["status"] not in GOOD]
    print("-" * 100)
    print(f"{len(log)} results: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"appended to {LOG_CSV.relative_to(PROJECT_ROOT)} "
          f"({len(prior) + len(log)} rows total, append-only)")
    for r in bad:
        print(f"  {r['status'].upper():<12} {r['source_id']:<5} {r['target']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
