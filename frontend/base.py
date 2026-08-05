"""
integrations/base.py



Every integration module (see notion_mock.py) should expose three functions:

   
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectionResult:
    success: bool
    connected_at: str                  # e.g. "3:45 PM"
    account_label: Optional[str] = None  # e.g. workspace/site name shown to the user
    item_count: Optional[int] = None     # how many items were found/indexed
    error: Optional[str] = None          # set this on failure, leave None on success


@dataclass
class ConnectedPage:
    title: str
    edited_label: str    # human-friendly, e.g. "Edited 2 hours ago"
    icon: str = "📄"
