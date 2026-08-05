from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceSystem(StrEnum):
    """String enum for platforms"""

    notion = "notion"

class Reference(BaseModel):
    """An explicit link to another document."""

    target_id: str              # id of the thing pointed at
    kind: str                   # "mention" | "relation" | "parent"
    label: str | None = None    # relation property's name e.g. "blocked_by" ****

class Provenance(BaseModel):
    source: SourceSystem
    tenant_id: str                              # Graphiti group_id (the customer)
    native_id: str                              # e.g. Notion's page id, GDrive's file id, etc.
    url: str | None = None
    author: str | None = None
    last_editor: str | None = None
    parent_path: list[str] = Field(default_factory=list)                 # e.g. ["Engineering", "Decisions", "Q3 pricing"]
    collection: str | None = None               # for Notion, the data source name, if its a db row
    created_at: datetime | None = None
    last_edited_at: datetime | None = None      # will get turned into Graphiti reference_time

class Document(BaseModel):
    id: str                             # e.g. f"notion:{native_id}"
    title: str
    body_markdown: str
    provenance: Provenance
    references: list[Reference] = []
    doc_type: str | None = None         # ontology hint: "decision", "meeting_note"
    raw: dict | None = None             # raw data, nothing downstream should use this