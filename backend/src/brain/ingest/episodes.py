"""This is where a Document becomes a Graphiti episode."""

import logging

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

from brain.models import Document
from brain.ontology import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES

log = logging.getLogger(__name__)

def _reference_time(doc: Document):
    """Have this as a function so that we know why there is an error if there is no useable timestamp rather than spending bunch of time debugging."""
    timestamp = doc.provenance.last_edited_at or doc.provenance.created_at
    if timestamp is None:
        raise ValueError(f"{doc.id} has no useable timestamp")
    return timestamp

async def ingest_document(graph: Graphiti, doc: Document) -> None:
    await graph.add_episode(
        name=doc.title,
        episode_body=doc.body_markdown,
        source=EpisodeType.text,             # read what this is later
        source_description=f"notion/{'/'.join(doc.provenance.parent_path)}",
        reference_time=_reference_time(doc),
        group_id=doc.provenance.tenant_id,
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP
    )