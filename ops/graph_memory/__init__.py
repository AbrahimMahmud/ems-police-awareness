"""ems-graph — a small, portable memory graph for this project.

Nodes are typed statements (intent, decision, finding, provenance, open_question,
next_action, rule) with a trust score in [0, 1], citations (commit, file:line,
document section) and a session tag; edges relate them (cites, supersedes,
supports, blocks). Storage is one sqlite file at ~/.local/share/ems-graph/
graph_memory.sqlite (the same path the local Mac setup uses) and an
append-only, git-tracked export at docs/graph/graph_memory.jsonl so the graph
travels with the repository and can be re-imported anywhere:

    graph-memory add --type decision --text "..." --trust 0.9 --cite "commit:bbd146a" --cite "docs/EXECUTION_PLAN.md:40"
    graph-memory link <from_id> <rel> <to_id>
    graph-memory search "freeze" --min-trust 0
    graph-memory list --type next_action
    graph-memory export docs/graph/graph_memory.jsonl     # git-tracked copy
    graph-memory import docs/graph/graph_memory.jsonl     # rebuild the sqlite from the export

Nothing here reads outcome data. Statements are text; keep confirmation-window
values out of them until the paper is public (the vault's AGENTS.md says the same).
"""
from .core import Graph, DEFAULT_DB

__all__ = ["Graph", "DEFAULT_DB"]
