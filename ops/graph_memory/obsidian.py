"""Render the memory graph as Obsidian notes: one note per node, wikilinked by its edges.

    python3 -m graph_memory.obsidian [--export docs/graph/graph_memory.jsonl] [--vault vault]

Reads the git-tracked JSONL export (never the sqlite, so any clone renders the same notes),
writes `<vault>/Graph/<node id>.md` for every node and `<vault>/Graph memory.md` as the index
grouped by type, and deletes node notes whose node is no longer in the export. Obsidian's graph
view then shows the typed nodes and their `cites / supersedes / supports / blocks / answers /
follows` edges as links, and every note links back to the index and the project hub.

The vault's rule (vault/AGENTS.md) is "paths, schemas and aggregate counts only — no unpublished
results". Node texts are the project's working memory and may quote a coefficient, a p-value or
a minimum detectable effect; the renderer therefore replaces any number with three or more
decimals, and any explicit p-value, with a marker that points at the cited artifact. Integer
counts (rows, cells, claims, findings) are aggregates and stay.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT_NUMBER = re.compile(r"(?<![\w.])[−-]?\d*\.\d{3,}(?![\w.])")
P_VALUE = re.compile(r"\b(p|p-value|p-values)\s*(=|<=|>=|<|>|≤|≥)?\s*[−-]?0\.\d+", re.IGNORECASE)
MARKER = "⟨value: see the cited artifact⟩"
TYPE_ORDER = ("intent", "decision", "rule", "status", "finding", "provenance", "open_question", "next_action")
TYPE_TITLE = {"intent": "Intent", "decision": "Decisions", "rule": "Rules", "status": "Status snapshots",
              "finding": "Findings", "provenance": "Provenance", "open_question": "Open questions",
              "next_action": "Next actions"}


def redact(text: str) -> str:
    text = P_VALUE.sub(lambda m: f"{m.group(1)} {MARKER}", text)
    return RESULT_NUMBER.sub(MARKER, text)


def load(export: Path):
    nodes, edges = {}, []
    for line in export.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("kind") == "node":
            nodes[rec["id"]] = rec
        elif rec.get("kind") == "edge":
            edges.append(rec)
    return nodes, edges


def render_node(n, out_edges, in_edges, nodes):
    fm = ["---", f"id: {n['id']}", f"type: {n['type']}", f"trust: {n['trust']}",
          f"created: {n.get('created_utc', '')}", f"session: \"{(n.get('session') or '').replace(chr(34), '')}\"",
          f"superseded_by: {n.get('superseded_by') or 'null'}",
          f"tags: [graph, {n['type']}]", "---", ""]
    body = [f"# {n['id']}", "", f"**{n['type']}** · trust {n['trust']:.2f}"
            + (f" · superseded by [[{n['superseded_by']}]]" if n.get("superseded_by") else ""), "",
            redact(n["text"]), ""]
    if n.get("citations"):
        body += ["**Cites**", ""] + [f"- `{c}`" for c in n["citations"]] + [""]
    if out_edges:
        body += ["**Edges out**", ""] + [f"- {e['rel']} → [[{e['dst']}]]" + (f" ({nodes[e['dst']]['type']})" if e['dst'] in nodes else "") for e in out_edges] + [""]
    if in_edges:
        body += ["**Edges in**", ""] + [f"- [[{e['src']}]] {e['rel']} → this" + (f" ({nodes[e['src']]['type']})" if e['src'] in nodes else "") for e in in_edges] + [""]
    body += [f"Index: [[Graph memory#{TYPE_TITLE[n['type']]}]] · hub: [[00 Project]]", ""]
    return "\n".join(fm + body)


def render_index(nodes, edges, export_rel):
    live = [n for n in nodes.values() if not n.get("superseded_by")]
    lines = ["---", "tags: [graph, index]", f"nodes: {len(nodes)}", f"edges: {len(edges)}", "---", "",
             "# Graph memory", "",
             f"Rendered from `{export_rel}` by `python3 -m graph_memory.obsidian` (run from `ops/`; see [[Tooling]]). "
             f"{len(nodes)} nodes ({len(live)} current, {len(nodes) - len(live)} superseded), {len(edges)} edges. "
             "Each node is a note under `Graph/`; its edges are wikilinks, so Obsidian's graph view is the memory graph. "
             "Node texts are rendered with result values replaced by a marker (vault rule: no unpublished results); "
             "the cited artifact holds the value. Superseded nodes are listed under their type, struck through.", "",
             "Related: [[00 Project]] · [[Decisions]] · [[Status]] · [[Lessons]] · [[Timeline]]", ""]
    for t in TYPE_ORDER:
        group = sorted((n for n in nodes.values() if n["type"] == t), key=lambda n: (bool(n.get("superseded_by")), n.get("created_utc", "")))
        if not group:
            continue
        lines += [f"## {TYPE_TITLE[t]}", ""]
        for n in group:
            first = redact(n["text"]).split(". ")[0][:140].rstrip(".")
            item = f"[[{n['id']}]] — {first}"
            lines.append(f"- ~~{item}~~ (superseded by [[{n['superseded_by']}]])" if n.get("superseded_by") else f"- {item}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="graph_memory.obsidian")
    ap.add_argument("--export", default=str(ROOT / "docs" / "graph" / "graph_memory.jsonl"))
    ap.add_argument("--vault", default=str(ROOT / "vault"))
    args = ap.parse_args(argv)
    export, vault = Path(args.export), Path(args.vault)
    nodes, edges = load(export)
    graph_dir = vault / "Graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    out = {nid: [] for nid in nodes}
    inc = {nid: [] for nid in nodes}
    for e in edges:
        out.setdefault(e["src"], []).append(e)
        inc.setdefault(e["dst"], []).append(e)
    written = set()
    for nid, n in nodes.items():
        (graph_dir / f"{nid}.md").write_text(render_node(n, out.get(nid, []), inc.get(nid, []), nodes), encoding="utf-8")
        written.add(f"{nid}.md")
    stale = [p for p in graph_dir.glob("*.md") if p.name not in written]
    for p in stale:
        p.unlink()
    try:
        export_rel = export.resolve().relative_to(ROOT)
    except ValueError:
        export_rel = export
    (vault / "Graph memory.md").write_text(render_index(nodes, edges, export_rel), encoding="utf-8")
    print(f"wrote {len(written)} node note(s) and Graph memory.md under {vault}; removed {len(stale)} stale note(s); {len(edges)} edge(s)")


if __name__ == "__main__":
    main()
