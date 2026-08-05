"""Ingest normalized documents into graph."""

import logging
from dataclasses import dataclass, field

from brain.connectors.notion import build_index, iter_documents
from brain.graph.client import ensure_schema, make_graphiti
from brain.ingest import done
from brain.ingest.episodes import ingest_document
from brain.store import raw

log = logging.getLogger(__name__)

@dataclass
class IngestResult():
    ingested: int = 0
    skipped: int = 0
    
    # have to do field() and not just list() because mutable objects are shared across all instances
    errors: list[str] = field(default_factory=list)

# on_progress is a callback
async def ingest_all(
        tenant_id: str, *, limit: int | None = None, on_progress=None
) -> IngestResult:
    result = IngestResult()
    previously_ingested = done.load()

    index = build_index(raw.iter_all("notion"))
    graph = make_graphiti()

    try:
        await ensure_schema(graph)
        
        for doc in iter_documents(raw.iter_all("notion"), index, tenant_id):
            if doc.id in previously_ingested:
                result.skipped += 1
                continue

            try:
                await ingest_document(graph, doc)
                done.mark(doc.id)
                result.ingested += 1
            except Exception as e:
                log.exception("failed to ingest %s", doc.id)
                result.errors.append(f"{doc.id}: {e}")

            if on_progress:
                on_progress(result)
            if limit is not None and result.ingested >= limit:
                break
    finally:
        await graph.close()
    
    return result