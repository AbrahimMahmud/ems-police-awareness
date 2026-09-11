"""One writer for the provenance register, keyed by source_id.

WHY THIS EXISTS (finding X8)
----------------------------
Seven scripts each wrote data/reference/data_sources.csv with mode="a", so every
re-run appended another row for the same source. The register held 21 rows under
9 distinct IDs — S11 four times, S14/S15/S1b three times each — and every one of
them claimed to be the provenance of the same artifact with a different SHA256.
A register with four answers for one source does not record provenance; it
records that nobody looked.

The rule here is that data_sources.csv is CURRENT STATE: exactly one row per
source_id, describing the artifact that is on disk right now. Superseded rows are
not deleted — they move to data_sources_history.csv, which is append-only. So
"when did this artifact's hash change, and to what" is still answerable, and
"what produced the file I am reading" has exactly one answer.

Both properties are asserted by V.no_duplicate_source_ids in the regression suite.
"""

import hashlib
from datetime import datetime, timezone

from pathlib import Path

import pandas as pd

from config import DATA_REFERENCE, PROJECT_ROOT

SOURCES_LOG = DATA_REFERENCE / "data_sources.csv"
SOURCES_HISTORY = DATA_REFERENCE / "data_sources_history.csv"
COLUMNS = ["source_id", "description", "url", "accessed_utc", "sha256",
           "payload_sha256", "output_file"]


def _rel(path):
    p = Path(path).resolve()
    try:
        return str(p.relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(p)


def log_source(source_id, description, url, payload_bytes=None, out_file=None):
    """Record (or replace) the provenance row for one source.

    TWO hashes, because they answer different questions and the old single
    column silently answered whichever one the caller happened to pass:

      sha256          the artifact ON DISK. Re-computable from the repository,
                      so it is the one anything can actually verify.
      payload_sha256  the bytes RECEIVED from the endpoint. Not re-computable
                      without re-fetching, and upstream may have changed since,
                      so it is a record of the fetch, never a test.

    Before this split, S7/S8/S10 recorded the payload and S1b/S11-S15 recorded
    the artifact, in one column named "sha256". Anything comparing that column
    to a file would have reported the ACS and MPV artifacts as corrupt.
    """
    row = {
        "source_id": source_id,
        "description": description,
        "url": url,
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": (hashlib.sha256(Path(out_file).read_bytes()).hexdigest()
                   if out_file else ""),
        "payload_sha256": (hashlib.sha256(payload_bytes).hexdigest()
                           if payload_bytes else ""),
        # Repo-relative: an absolute path is a fact about one machine, and a
        # register that a fresh clone cannot resolve cannot be verified.
        "output_file": _rel(out_file) if out_file else "",
    }

    cur = pd.read_csv(SOURCES_LOG) if SOURCES_LOG.exists() else pd.DataFrame(columns=COLUMNS)
    superseded = cur[cur["source_id"] == source_id]
    if len(superseded):
        superseded.to_csv(SOURCES_HISTORY, mode="a",
                          header=not SOURCES_HISTORY.exists(), index=False)
    keep = cur[cur["source_id"] != source_id]
    out = pd.concat([keep, pd.DataFrame([row])], ignore_index=True)
    out = out.sort_values("source_id", kind="stable")
    out.to_csv(SOURCES_LOG, index=False)

    changed = ""
    if len(superseded) and "sha256" in superseded.columns:
        prev = superseded["sha256"].iloc[-1]
        changed = " (unchanged)" if prev == row["sha256"] else f" (was {str(prev)[:12]})"
    print(f"provenance: {source_id} -> {row['sha256'][:12]}{changed}")
    return row
