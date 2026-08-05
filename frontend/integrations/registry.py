"""
integrations/registry.py

Single place that lists every data source the sidebar can show. Adding a
new source later is meant to be exactly two steps:

  1. Create integrations/<id>_mock.py (or _real.py) exposing:
         connect(progress_callback=None) -> ConnectionResult
         disconnect() -> None
         get_graph() -> {"nodes": [...], "edges": [...]}
         get_node_detail(node_id) -> dict | None
  2. Add one entry to SOURCES below.

Nothing in UserInterface.py needs to change — it only ever reads from
this registry, never hardcodes a source list itself.
"""

from integrations import notion_mock

SOURCES = {
    "notion": {
        "name": "Notion",
        "icon": "notion",
        "module": notion_mock,
        "available": True,   # has a real (mock) connect flow wired up
    },
    "gmail": {
        "name": "Gmail",
        "icon": "email",
        "module": None,
        "available": False,  # not built yet — home screen shows "Coming soon"
    },
    "google_drive": {
        "name": "Google Drive",
        "icon": "google_drive",
        "module": None,
        "available": False,
    },
}


def get_source(source_id):
    return SOURCES.get(source_id)


def list_sources():
    return SOURCES
