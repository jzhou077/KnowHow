"""
integrations/base.py

This file defines the SHAPE of data every integration hands back to the UI —
mock or real. It's the "contract" your backend developer codes against.

Every integration module (see notion_mock.py) should expose:

    connect(progress_callback=None) -> ConnectionResult
        Runs the connection flow (OAuth, token exchange, etc). If a
        progress_callback is given, call it as: progress_callback(label, percent)
        so the UI can show live status while this runs.

    disconnect() -> None
        Revokes/removes the connection.

    get_graph() -> {"nodes": [GraphNode-shaped dicts], "edges": [GraphEdge-shaped dicts]}
        The full knowledge graph for this source.

    get_node_detail(node_id) -> dict | None
        Full detail + related connections for one node, shown in the side
        panel when a person picks that node from the graph.

Swapping mock -> real later just means writing a new module (e.g.
integrations/notion_real.py) that returns these same shapes, then pointing
integrations/registry.py at it. Nothing in UserInterface.py has to change.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectionResult:
    success: bool
    connected_at: str                    # e.g. "3:45 PM"
    account_label: Optional[str] = None  # e.g. workspace/site name shown to the user
    item_count: Optional[int] = None     # how many items were found/indexed
    error: Optional[str] = None          # set this on failure, leave None on success


@dataclass
class GraphNode:
    id: str
    label: str
    type: str            # "project" | "document" | "person" | "topic"
    meta: dict            # freeform: author, path, excerpt, etc.


@dataclass
class GraphEdge:
    source: str           # a GraphNode.id
    target: str           # a GraphNode.id
    relation: str          # e.g. "authored", "belongs to", "about"
