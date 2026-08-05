"""
integrations/notion_mock.py

Fake Notion CONNECTION flow only (OAuth-style handshake simulation). The
actual knowledge graph data lives in integrations/notion_graph.py — kept
separate so this file has one job: simulate "connecting."

>>> SWAP POINT FOR BACKEND <<<
When the real integration is ready, create integrations/notion_real.py
with the same connect()/disconnect() functions, and point
integrations/registry.py at it instead of this module. Nothing in
UserInterface.py needs to change.
"""

import time
import random
from datetime import datetime

from integrations.base import ConnectionResult
from integrations.notion_graph import get_graph as _get_graph  # re-exported below
from integrations.notion_graph import get_node_detail as _get_node_detail  # re-exported below

CONNECTION_STEPS = [
    ("Opening secure connection to Notion...", 20),
    ("Verifying workspace access...", 45),
    ("Fetching pages and databases...", 75),
    ("Building your knowledge graph...", 100),
]


def connect(progress_callback=None) -> ConnectionResult:
    """
    Simulates connecting to Notion.

    Real version would: redirect through Notion OAuth, exchange the
    returned code for an access token, then call Notion's /search endpoint
    to confirm access.
    """
    graph = _get_graph()
    for label, percent in CONNECTION_STEPS:
        if progress_callback:
            progress_callback(label, percent)
        time.sleep(random.uniform(0.4, 0.7))

    return ConnectionResult(
        success=True,
        connected_at=datetime.now().strftime("%I:%M %p"),
        account_label="yourcompany.notion.site",
        item_count=len(graph["nodes"]),
    )


def disconnect():
    """Real version would revoke the stored access token."""
    return None


# Re-exported so integrations/registry.py + UserInterface.py can call
# source["module"].get_graph() / get_node_detail() the same way for every
# source, regardless of which module backs it.
get_graph = _get_graph
get_node_detail = _get_node_detail
