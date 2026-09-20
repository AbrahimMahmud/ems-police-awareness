from __future__ import annotations

import argparse
import json
import signal
import sys

signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` must not traceback

from .core import DEFAULT_DB, Graph, NODE_TYPES, RELATIONS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="graph-memory", description="ems project memory graph (sqlite + jsonl export)")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("--type", required=True, choices=NODE_TYPES); a.add_argument("--text", required=True)
    a.add_argument("--trust", type=float, default=0.5); a.add_argument("--cite", action="append", default=[]); a.add_argument("--session")
    l = sub.add_parser("link"); l.add_argument("src"); l.add_argument("rel", choices=RELATIONS); l.add_argument("dst")
    s = sub.add_parser("search"); s.add_argument("term"); s.add_argument("--min-trust", type=float, default=0.0); s.add_argument("--type", choices=NODE_TYPES); s.add_argument("--json", action="store_true")
    ls = sub.add_parser("list"); ls.add_argument("--type", choices=NODE_TYPES); ls.add_argument("--json", action="store_true"); ls.add_argument("--all", action="store_true")
    e = sub.add_parser("export"); e.add_argument("path")
    i = sub.add_parser("import"); i.add_argument("path")
    args = ap.parse_args(argv)
    g = Graph(args.db)
    if args.cmd == "add":
        print(g.add(args.type, args.text, args.trust, args.cite, args.session))
    elif args.cmd == "link":
        g.link(args.src, args.rel, args.dst); print("linked")
    elif args.cmd in ("search", "list"):
        rows = g.search(args.term, args.min_trust, args.type) if args.cmd == "search" else g.list(args.type, getattr(args, "all", False))
        if args.json:
            print(json.dumps(rows, indent=1, ensure_ascii=False))
        else:
            for r in rows:
                cites = "; ".join(r["citations"]) if r["citations"] else "-"
                print(f"[{r['type']:13s} trust {r['trust']:.2f}] {r['id']}\n    {r['text']}\n    cites: {cites}")
            print(f"{len(rows)} node(s)", file=sys.stderr)
    elif args.cmd == "export":
        print(g.export(args.path))
    elif args.cmd == "import":
        n, m = g.import_(args.path); print(f"imported {n} node(s), {m} edge(s)")


if __name__ == "__main__":
    main()
