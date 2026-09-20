from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(os.environ.get("EMS_GRAPH_DB", Path.home() / ".local/share/ems-graph/graph_memory.sqlite"))
NODE_TYPES = ("intent", "decision", "finding", "provenance", "open_question", "next_action", "rule", "status")
RELATIONS = ("cites", "supersedes", "supports", "blocks", "answers", "follows")

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY, type TEXT NOT NULL, text TEXT NOT NULL, trust REAL NOT NULL,
  citations TEXT NOT NULL, session TEXT, created_utc TEXT NOT NULL, superseded_by TEXT
);
CREATE TABLE IF NOT EXISTS edges (
  src TEXT NOT NULL, rel TEXT NOT NULL, dst TEXT NOT NULL, created_utc TEXT NOT NULL,
  PRIMARY KEY (src, rel, dst)
);
CREATE INDEX IF NOT EXISTS nodes_type ON nodes(type);
"""


def _now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _node_id(ntype, text):
    return ntype[:3] + "_" + hashlib.sha256(f"{ntype}|{text}".encode()).hexdigest()[:10]


class Graph:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.executescript(SCHEMA)

    # -- write ---------------------------------------------------------------
    def add(self, ntype, text, trust=0.5, citations=(), session=None, created_utc=None, nid=None):
        if ntype not in NODE_TYPES:
            raise ValueError(f"type must be one of {NODE_TYPES}")
        trust = float(trust)
        if not 0.0 <= trust <= 1.0:
            raise ValueError("trust must lie in [0, 1]")
        nid = nid or _node_id(ntype, text)
        self.con.execute(
            "INSERT OR REPLACE INTO nodes(id,type,text,trust,citations,session,created_utc,superseded_by) "
            "VALUES(?,?,?,?,?,?,?,COALESCE((SELECT superseded_by FROM nodes WHERE id=?),NULL))",
            (nid, ntype, text, trust, json.dumps(list(citations)), session, created_utc or _now(), nid))
        self.con.commit()
        return nid

    def link(self, src, rel, dst):
        if rel not in RELATIONS:
            raise ValueError(f"rel must be one of {RELATIONS}")
        for n in (src, dst):
            if self.con.execute("SELECT 1 FROM nodes WHERE id=?", (n,)).fetchone() is None:
                raise KeyError(f"no node {n}")
        self.con.execute("INSERT OR IGNORE INTO edges(src,rel,dst,created_utc) VALUES(?,?,?,?)", (src, rel, dst, _now()))
        if rel == "supersedes":
            self.con.execute("UPDATE nodes SET superseded_by=? WHERE id=?", (src, dst))
        self.con.commit()

    # -- read ----------------------------------------------------------------
    def search(self, term, min_trust=0.0, ntype=None, include_superseded=False):
        q = "SELECT id,type,text,trust,citations,session,created_utc,superseded_by FROM nodes WHERE trust>=? AND lower(text) LIKE ?"
        args = [min_trust, f"%{term.lower()}%"]
        if ntype:
            q += " AND type=?"; args.append(ntype)
        if not include_superseded:
            q += " AND superseded_by IS NULL"
        q += " ORDER BY trust DESC, created_utc DESC"
        return [self._row(r) for r in self.con.execute(q, args)]

    def list(self, ntype=None, include_superseded=False):
        q = "SELECT id,type,text,trust,citations,session,created_utc,superseded_by FROM nodes"
        conds, args = [], []
        if ntype:
            conds.append("type=?"); args.append(ntype)
        if not include_superseded:
            conds.append("superseded_by IS NULL")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY type, created_utc"
        return [self._row(r) for r in self.con.execute(q, args)]

    def edges(self, nid=None):
        q, args = "SELECT src,rel,dst,created_utc FROM edges", []
        if nid:
            q += " WHERE src=? OR dst=?"; args = [nid, nid]
        return [dict(src=s, rel=r, dst=d, created_utc=c) for s, r, d, c in self.con.execute(q, args)]

    @staticmethod
    def _row(r):
        return dict(id=r[0], type=r[1], text=r[2], trust=r[3], citations=json.loads(r[4]),
                    session=r[5], created_utc=r[6], superseded_by=r[7])

    # -- portability -----------------------------------------------------------
    def export(self, path):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            for n in self.list(include_superseded=True):
                fh.write(json.dumps({"kind": "node", **n}, ensure_ascii=False) + "\n")
            for e in self.edges():
                fh.write(json.dumps({"kind": "edge", **e}, ensure_ascii=False) + "\n")
        return path

    def import_(self, path):
        n_nodes = n_edges = 0
        pending = []
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            if j["kind"] == "node":
                self.add(j["type"], j["text"], j["trust"], j["citations"], j.get("session"), j.get("created_utc"), nid=j["id"])
                if j.get("superseded_by"):
                    self.con.execute("UPDATE nodes SET superseded_by=? WHERE id=?", (j["superseded_by"], j["id"]))
                n_nodes += 1
            else:
                pending.append(j)
        for e in pending:
            self.con.execute("INSERT OR IGNORE INTO edges(src,rel,dst,created_utc) VALUES(?,?,?,?)",
                             (e["src"], e["rel"], e["dst"], e.get("created_utc") or _now()))
            n_edges += 1
        self.con.commit()
        return n_nodes, n_edges
