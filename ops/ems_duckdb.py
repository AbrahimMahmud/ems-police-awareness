#!/usr/bin/env python3
"""ems-duckdb — read-only SQL over views of the project's sources, aggregates only.

    python3 ops/ems_duckdb.py "SELECT year(incident_date) AS y, count(*) FROM panel GROUP BY 1 ORDER BY 1"
    python3 ops/ems_duckdb.py --views

Views: one per parquet in data/processed (name = file stem) and per CSV in data/reference
(prefix ref_). Outcome views (config.OUTCOME_ARTIFACTS) are filtered to the discovery window
while config.FREEZE_ACTIVE is True, and to the confirmation windows once it is False, through
the same constants freeze_guard uses — this tool is a convenience over the same sample rule,
not a second guard. The guard here is on OUTPUT: a query must aggregate (GROUP BY or an
aggregate function), may not SELECT *, may return at most 200 rows, and INSTALL/LOAD/COPY/
ATTACH/httpfs and file functions are refused in the caller's SQL. Record-level rows never reach the caller.
"""
from __future__ import annotations

import argparse
import re
import signal
import sys

signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not traceback
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from config import (CONFIRMATION_WINDOWS, DISCOVERY_END, DISCOVERY_START, FREEZE_ACTIVE,  # noqa: E402
                    OUTCOME_ARTIFACTS)

FORBIDDEN = re.compile(r"\b(install|load|copy|attach|export|import|pragma|create|insert|update|delete|drop|alter|httpfs|read_csv|read_parquet|glob)\b", re.I)
AGG = re.compile(r"\b(count|sum|avg|min|max|median|quantile|stddev|var_pop|var_samp|approx_count_distinct|group\s+by)\b", re.I)
MAX_ROWS = 200


def window_clause(col="incident_date"):
    if FREEZE_ACTIVE:
        return f"{col} BETWEEN DATE '{DISCOVERY_START}' AND DATE '{DISCOVERY_END}'"
    return " OR ".join(f"({col} BETWEEN DATE '{a}' AND DATE '{b}')" for a, b in CONFIRMATION_WINDOWS)


def connect():
    con = duckdb.connect(database=":memory:", read_only=False)
    views = []
    for p in sorted((ROOT / "data/processed").glob("*.parquet")):
        name = p.stem
        cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p}')").fetchall()]
        date_col = next((c for c in cols if "date" in c.lower()), None)
        if p.name in OUTCOME_ARTIFACTS and date_col:
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{p}') WHERE {window_clause(date_col)}")
            views.append((name, f"outcome artifact: rows limited to the active sample on {date_col}"))
        else:
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{p}')")
            views.append((name, "treatment/reference"))
    for p in sorted((ROOT / "data/reference").glob("*.csv")):
        name = "ref_" + re.sub(r"[^a-zA-Z0-9_]", "_", p.stem)
        try:
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_csv_auto('{p}', header=true, all_varchar=true)")
            views.append((name, "reference csv"))
        except Exception:  # noqa: BLE001
            continue
    return con, views


def run(sql):
    if FORBIDDEN.search(sql):
        raise SystemExit("refused: only SELECT aggregates are allowed (no INSTALL/LOAD/COPY/ATTACH/DDL/file functions)")
    if re.search(r"select\s+\*", sql, re.I) or not AGG.search(sql):
        raise SystemExit("refused: the query must aggregate (GROUP BY or an aggregate function) and may not SELECT *")
    con, _ = connect()
    rel = con.execute(sql)
    rows = rel.fetchmany(MAX_ROWS + 1)
    if len(rows) > MAX_ROWS:
        raise SystemExit(f"refused: more than {MAX_ROWS} rows; aggregate further")
    cols = [d[0] for d in rel.description]
    print(" | ".join(cols))
    for r in rows:
        print(" | ".join("" if v is None else str(v) for v in r))
    print(f"({len(rows)} row(s); freeze {'ACTIVE — discovery window' if FREEZE_ACTIVE else 'LIFTED — confirmation windows'} on outcome views)", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="?")
    ap.add_argument("--views", action="store_true")
    a = ap.parse_args()
    if a.views or not a.sql:
        _, views = connect()
        for n, note in views:
            print(f"{n:45s} {note}")
    else:
        run(a.sql)
