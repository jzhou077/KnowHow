"""
mock_data.py

Fake data standing in for the backend. Every function here is what your
backend teammate will eventually replace with a real API call — keep the
function names and return shapes the same and the UI won't need to change.

"""

# Data sources shown as connectable cards on the home screen.
# Slack has been removed per product decision. Iconkeys map to the
# ICON_* constants in style.py.
SOURCE_CATALOG = [
    {"id": "notion", "name": "Notion", "icon": "notion", "connected": False},
    {"id": "gmail", "name": "Gmail", "icon": "email", "connected": False},
    {"id": "google_drive", "name": "Google Drive", "icon": "google_drive", "connected": False},
    {"id": "github", "name": "GitHub", "icon": "github", "connected": False},
    {"id": "upload", "name": "Upload Files", "icon": "upload", "connected": False},
]


def get_source_catalog():
    """Returns the list of connectable source types and their status."""
    return SOURCE_CATALOG
