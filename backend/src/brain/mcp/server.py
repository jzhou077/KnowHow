from __future__ import annotations

import logging

from graphiti_core import Graphiti
from mcp.server import MCPServer

from brain.ontology import ENTITY_TYPES
from brain.retrieval import format_entities, format_facts, search_entities, search_facts

log = logging.getLogger(__name__)

mcp = MCPServer("company-brain")

# Wiring

# these tools need an open Graphiti connection but this module must not create one
# instead it binds to one that is already created by api/app.py

_graph: Graphiti | None = None
_tenant_id: str | None = None

def bind_graph(graph: Graphiti, tenant_id: str) -> None:
    """Called once at startup by api/app.py"""
    global _graph, _tenant_id
    _graph = graph
    _tenant_id = tenant_id
    log.info("mcp tools bound to tenant %s", tenant_id)

def _context() -> tuple[Graphiti, str]:
    if _graph is None or _tenant_id is None:
        raise RuntimeError("MCP tools are not connected to the graph. bind_graph() must run during application startup")
    
    return _graph, _tenant_id

# Tools

@mcp.tool()
async def search_company_knowledge(query: str, limit: int = 8) -> str:
    """Search this company's internal knowledge for facts about how things
    currently work: decisions that were made, who owns what, which tools and
    policies are in force.
 
    Call this before answering any question about this specific company's
    practices, systems, people or history. General knowledge is not a
    substitute -- the answer depends on what this company actually decided,
    and that is only written down here.
 
    Each result carries the document it came from, when that document was last
    edited, and the span of time the fact has been true for. Where a fact
    replaced an earlier one, the earlier one appears beneath it. Cite the
    source document when you use a fact. If two facts disagree, prefer the one
    from the more recently edited document and say that there is a conflict.
 
    Args:
        query: a natural-language description of what you need to know.
        limit: how many facts to return; keep it small unless the question is
            genuinely broad.
    """
    
    graph, tenant = _context()
    facts = await search_facts(graph, query, tenant_id=tenant, limit=min(limit, 25))
    
    return format_facts(facts)

@mcp.tool()
async def find_entity(name: str, entity_type: str | None = None) -> str:
    """Look up a specific person, project, decision or policy by name.
 
    Use this when the question is about a named thing -- "who is Priya",
    "what is the Atlas project" -- rather than about a topic. The result
    includes a short summary of the thing and its identifier.
 
    Use search_company_knowledge instead when you want facts and relationships
    rather than a description of one thing.
 
    Args:
        name: the name to look up. Approximate spelling is fine.
        entity_type: optionally narrow the search. Valid values are listed in
            the error message if you pass an invalid one.
    """

    graph, tenant = _context()

    labels = None
    if entity_type:
        if entity_type not in ENTITY_TYPES:
            valid = ", ".join(sorted(ENTITY_TYPES))
            return f"'{entity_type}' is not a known entity type. Valid types: {valid}"
        labels = [entity_type]

    entities = await search_entities(graph, name, tenant_id=tenant, limit=5, entity_labels=labels)

    return format_entities(entities)

@mcp.tool()
async def history_of(query: str, limit: int = 10) -> str:
    """Show how something changed over time, including things that used to be
    true and no longer are.
 
    Use this when the question is about change rather than current state:
    "when did we switch", "what did we use before", "has this policy always
    been like this", "why did this change".
 
    Results include facts that have since been superseded, each with the dates
    it was valid between. Present them in order and name the document that
    caused each change. Do not present a superseded fact as if it were still
    true.
 
    Args:
        query: the topic whose history you want.
        limit: how many facts to return.
    """

    graph, tenant = _context()
    
    facts = await search_facts(graph, query, tenant_id=tenant, limit=min(limit, 25), include_superseded=True)
    facts.sort(key=lambda f: (f.valid_at is None, f.valid_at))

    return format_facts(facts)