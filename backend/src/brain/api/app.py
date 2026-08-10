from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from graphiti_core import Graphiti
from pydantic import BaseModel
from starlette.responses import JSONResponse

from brain.config import settings
from brain.graph.client import ensure_schema, make_graphiti
from brain.mcp.server import bind_graph, mcp
from mcp.server.transport_security import TransportSecuritySettings
from brain.retrieval import (
    Entity,
    Fact,
    Source,
    get_whole_graph,
    neighborhood,
    search_entities,
    search_facts,
)

log = logging.getLogger(__name__)

# Startup and shutdown
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Everything that has to be open while the server runs.
    
    This is a single function split in two by the `yield` keyword. Everything before runs at startup. Everything after runs at shutdown.
    """

    # AsyncExitStacks lets multiple things share one lifespan without nesting `async with`
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())

        graph = make_graphiti()
        await ensure_schema(graph)
        stack.push_async_callback(graph.close)
        app.state.graph = graph

        bind_graph(graph, settings.tenant_id)

        log.info("routes: %s", [getattr(r, "path", None) for r in app.routes])
        yield

app = FastAPI(title="Company Brain", lifespan=lifespan)

# CORS stuff
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"], allow_headers=["*"])

# Auth
bearer = HTTPBearer(auto_error=False)

def tenant_from_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if credentials is None:
        print("no bearer token")
        raise HTTPException(status_code=401, detail="missing bearer token")
    
    tenant = settings.api_tokens.get(credentials.credentials)
    if tenant is None:
        raise HTTPException(status_code=401, detail="unknown token: token not found")
    
    return tenant

def get_graph(req: Request) -> Graphiti:
    return req.app.state.graph

Tenant = Annotated[str, Depends(tenant_from_token)]
Graph = Annotated[Graphiti, Depends(get_graph)]

# @app.middleware("http")
# async def guard_mounted_mcp(req: Request, call_next):
#     """Auth for /mcp"""

#     if req.url.path.startswith("/mcp"):
#         header = req.headers.get("authorization", "")
#         token = header.removeprefix("Bearer ").strip()
#         if token not in settings.api_tokens:
#             return JSONResponse({"error": "unauthorized"}, status_code=401)
#     return await call_next(req)

# Response shapes

class SourceOut(BaseModel):
    title: str | None = None
    url: str | None = None
    path: str | None = None
    last_edited_at: datetime | None = None

class FactOut(BaseModel):
    uuid: str
    statement: str
    relation: str
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    is_current: bool
    sources: list[SourceOut] = []
    superseded: list["FactOut"] = []
    source_uuid: str | None = None
    target_uuid: str | None = None

FactOut.model_rebuild()  # needed because FactOut refers to itself

class EntityOut(BaseModel):
    uuid: str
    name: str
    labels: list[str] = []
    summary: str | None = None
    attributes: dict = {}

class SearchResponse(BaseModel):
    query: str
    facts: list[FactOut]

class EntityResponse(BaseModel):
    query: str
    entities: list[EntityOut]

class GraphResponse(BaseModel):
    center_uuid: str
    entities: list[EntityOut]
    facts: list[FactOut]

class WholeGraphResponse(BaseModel):
    entities: list[EntityOut]
    facts: list[FactOut]
    total_facts: int
    truncated: bool

def _source_out(source: Source) -> SourceOut:
    return SourceOut(
        title=source.title,
        url=source.url,
        path=source.path,
        last_edited_at=source.last_edited_at,
    )
 
def _fact_out(fact: Fact) -> FactOut:
    return FactOut(
        uuid=fact.uuid,
        statement=fact.statement,
        relation=fact.relation,
        valid_at=fact.valid_at,
        invalid_at=fact.invalid_at,
        is_current=fact.is_current,
        sources=[_source_out(s) for s in fact.sources],
        superseded=[_fact_out(f) for f in fact.superseded],
        source_uuid=fact.source_uuid,
        target_uuid=fact.target_uuid
    )

def _entity_out(entity: Entity) -> EntityOut:
    return EntityOut(
        uuid=entity.uuid,
        name=entity.name,
        labels=list(entity.labels),
        summary=entity.summary,
        attributes=entity.attributes,
    )

# Routes

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/search", response_model=SearchResponse)
async def api_search(
    graph: Graph,
    tenant: Tenant,
    query: Annotated[str, Query(min_length=1, description="what to search for")],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    history: Annotated[bool, Query(description="include superseded facts")] = False,
) -> SearchResponse:
    
    facts = await search_facts(graph, query, tenant_id=tenant, limit=limit, include_superseded=history)
    return SearchResponse(query=query, facts=[_fact_out(f) for f in facts])

@app.get("/api/entities", response_model=EntityResponse)
async def api_entities(
    graph: Graph,
    tenant: Tenant,
    query: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    entity_type: str | None = None,
) -> EntityResponse:
    
    entities = await search_entities(graph, query, tenant_id=tenant, limit=limit, entity_labels=[entity_type] if entity_type else None)
    return EntityResponse(query=query, entities=[_entity_out(e) for e in entities])

@app.get("/api/graph", response_model=GraphResponse)
async def api_graph(
    graph: Graph,
    tenant: Tenant,
    entity_uuid: Annotated[str, Query(description="center of the neighborhood")],
    limit: Annotated[int, Query(ge=1, le=100)] = 25
) -> GraphResponse:
    """what frontend is supposed to draw"""
    entities, facts = await neighborhood(graph, entity_uuid, tenant_id=tenant, limit=limit)

    return GraphResponse(center_uuid=entity_uuid, entities=[_entity_out(e) for e in entities], facts=[_fact_out(fact) for fact in facts])

@app.get("/api/graph/all", response_model=WholeGraphResponse)
async def api_graph_all(
    graph: Graph,
    tenant: Tenant,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,      # between 1 and 2000 but defaults to 500
    history: Annotated[bool, Query(description="include superseded facts")] = False
) -> WholeGraphResponse:
    """The whole graph for visualization."""
    result = await get_whole_graph(graph, tenant_id=tenant, limit=limit, include_superseded=history)

    return WholeGraphResponse(
        entities=[_entity_out(entity) for entity in result.entities],
        facts=[_fact_out(fact) for fact in result.facts],
        total_facts=result.total_facts,
        truncated=result.truncated
    )

# MCP endpoint
app.mount("/", mcp.streamable_http_app(
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            "backend-production-2b42f.up.railway.app",
            "127.0.0.1:*",
            "localhost:*",
        ],
        allowed_origins=["https://claude.ai", "https://claude.com"],
    )
))