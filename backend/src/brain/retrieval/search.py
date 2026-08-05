from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.helpers import parse_db_date
from graphiti_core.nodes import EntityNode
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_filters import SearchFilters

log = logging.getLogger(__name__)

DEFAULT_LIMIT = 10

# Result types, these are custom not Graphiti's so that if Graphiti ever changes anything or we decide to swap to a different graph library,
# we would not have to rewrite the whole codebase and instead just this file
# same idea as having our own generalized Document model, everything downstream is not library-specific

@dataclass(frozen=True) # frozen just makes attributes immutable
class Source:
    """Where a fact came from; one ingested document"""

    title: str | None = None
    url: str | None = None
    path: str | None = None
    last_edited_at: datetime | None = None

@dataclass(frozen=True)
class Fact:
    uuid: str
    statement: str
    relation: str
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    sources: tuple[Source, ...] = ()
    superseded: tuple[Fact, ...] = ()
    source_uuid: str | None = None
    target_uuid: str | None = None

    @property
    def is_current(self)->bool:
        return self.invalid_at is None
    
@dataclass(frozen=True)
class Entity:
    """A node in the graph (e.g. person, project, decision, or policy)"""

    uuid: str
    name: str
    labels: tuple[str, ...] = ()
    summary: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphSlice:
    """A set of entities and the facts connecting them. (for frontend to draw)"""
    entities: tuple[Entity, ...] = ()
    facts: tuple[Fact, ...] = ()
    total_facts: int = 0
    truncated: bool = False         # not really relevant for demo, just for actual product cuz wouldn't wanna load 5 million nodes/edges for company

# Cypher queries

# UNWIND takes a list and expands it into individual rows
# MATCH searches graph for things that fit your query
# WHERE filters and RETURN returns

_EPISODES_BY_UUID = """
UNWIND $uuids AS episode_uuid
MATCH (e:Episodic {uuid: episode_uuid})
WHERE e.group_id = $group_id
RETURN e.uuid AS uuid,
       e.name AS name,
       e.source_description AS source_description,
       e.valid_at AS valid_at
"""

# Finds older facts between the same two entities that have since been invalidated
_SUPERSEDED_SIBLINGS = """
UNWIND $pairs AS pair
MATCH (a:Entity {uuid: pair.source})-[r:RELATES_TO]->(b:Entity {uuid: pair.target})
WHERE r.group_id = $group_id
    AND r.uuid <> pair.uuid
    AND (r.invalid_at IS NOT NULL OR r.expired_at IS NOT NULL)
RETURN pair.uuid AS current_uuid,
       r.uuid AS uuid,
       r.name AS name,
       r.fact AS fact,
       r.valid_at AS valid_at,
       r.invalid_at AS invalid_at
"""

# Everything around a single entity (literally its neighborhood)
_NEIGHBORHOOD = """
MATCH (centre:Entity {uuid: $uuid})-[r:RELATES_TO]-(other:Entity)
WHERE r.group_id = $group_id AND other.group_id = $group_id
RETURN r.uuid AS uuid,
       r.name AS name,
       r.fact AS fact,
       r.valid_at AS valid_at,
       r.invalid_at AS invalid_at,
       r.source_node_uuid AS source_node_uuid,
       r.target_node_uuid AS target_node_uuid,
       other.uuid AS other_uuid,
       other.name AS other_name,
       labels(other) AS other_labels
LIMIT $limit
"""

_WHOLE_GRAPH = """
MATCH (source:Entity)-[r:RELATES_TO]->(target:Entity)
WHERE r.group_id = $group_id
  AND ($include_superseded OR (r.invalid_at IS NULL AND r.expired_at IS NULL))
RETURN r.uuid AS uuid,
       r.name AS name,
       r.fact AS fact,
       r.valid_at AS valid_at,
       r.invalid_at AS invalid_at,
       source.uuid AS source_uuid,
       source.name AS source_name,
       labels(source) AS source_labels,
       source.summary AS source_summary,
       target.uuid AS target_uuid,
       target.name AS target_name,
       labels(target) AS target_labels,
       target.summary AS target_summary
LIMIT $limit
"""
 
_WHOLE_GRAPH_COUNT = """
MATCH (:Entity)-[r:RELATES_TO]->(:Entity)
WHERE r.group_id = $group_id
  AND ($include_superseded OR (r.invalid_at IS NULL AND r.expired_at IS NULL))
RETURN count(r) AS total
"""

# Public functions

async def search_facts(
    graph: Graphiti,
    query: str,
    *,
    tenant_id: str,
    limit: int = DEFAULT_LIMIT,
    center_entity_uuid: str | None = None,
    relation_types: Sequence[str] | None = None,
    include_superseded: bool = False,
    with_history: bool = True,
) -> list[Fact]:
    """Finds facts that match the query, each with provenance and a validity window.
    
    Args:
        - tenant_id: the customer that this search runs for
        - center_entity_uuid: if given, results are reranked by how close they are to this entity rather than just text relevance alone 
        (useful for follow-up questions about a known thing)
        - relation_types: restrict to specific edge types e.g. ["Supersedes"]
        - include_superseded: keep facts that are no longer true (off by default)
        - with_history: attached superseded predecessors to each fact
    """

    # the receipes are module-level singletons, objects that get created once and then reused everywhere rather than being constructed fresh each time its needed
    # so mutating one would change it for every other caller, which we obviously don't want so we take a copy before setting the limit
    recipe = EDGE_HYBRID_SEARCH_RRF if center_entity_uuid is None else EDGE_HYBRID_SEARCH_NODE_DISTANCE
    config = recipe.model_copy(deep=True)
    config.limit = limit

    search_filter = SearchFilters()
    if relation_types:
        search_filter = SearchFilters(edge_types=list(relation_types))

    results = await graph.search_(
        query=query,
        config=config,
        group_ids=[tenant_id],
        center_node_uuid=center_entity_uuid,
        search_filter=search_filter
    )

    edges: list[EntityEdge] = list(results.edges)
    if not include_superseded:
        edges = [e for e in edges if e.invalid_at is None and e.expired_at is None] # filtering out for valid/not expired edges
    
    if not edges:
        return []
    
    sources_by_episode = await _load_sources(graph, edges, tenant_id)
    history = await _load_history(graph, edges, tenant_id) if with_history else {}

    return [
        Fact(
            uuid=edge.uuid,
            statement=edge.fact,
            relation=edge.name,
            valid_at=edge.valid_at,
            invalid_at=edge.invalid_at,
            sources=tuple(
                sources_by_episode[ep] 
                for ep in (edge.episodes or []) 
                if ep in sources_by_episode
            ),
            superseded=tuple(history.get(edge.uuid, ())),
            source_uuid=edge.source_node_uuid,
            target_uuid=edge.target_node_uuid
        )
        for edge in edges
    ]

async def search_entities(
    graph: Graphiti,
    query: str,
    *,
    tenant_id: str,
    limit: int = DEFAULT_LIMIT,
    entity_labels: Sequence[str] | None = None
) -> list[Entity]:
    """Finds entities (people, projects, etc.) matching query
    
    Use this to resolve a name with a uuid before calling search_facts with center_entity_uuid
    or to answer "who is X" style questions
    """
    config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
    config.limit = limit

    search_filter = SearchFilters()
    if entity_labels:
        search_filter = SearchFilters(node_labels=list(entity_labels))

    results = await graph.search_(
        query=query,
        config=config,
        group_ids=[tenant_id],
        search_filter=search_filter
    )

    return [_to_entity(node) for node in results.nodes]

async def neighborhood(
    graph: Graphiti,
    entity_uuid: str,
    *,
    tenant_id: str,
    limit: int = 25
) -> tuple[list[Entity], list[Fact]]:
    """
    Returns neighbors and incident edges of a node in format (entities, facts) 
    """

    records, _, _ = await graph.driver.execute_query(
        _NEIGHBORHOOD,
        uuid=entity_uuid,
        group_id=tenant_id,
        limit=limit,
        routing_="r"
    )

    entities: dict[str, Entity] = {}
    facts: list[Fact] = []
    for record in records:
        other_uuid = record["other_uuid"]
        if other_uuid not in entities:
            entities[other_uuid] = Entity(
                uuid=other_uuid, 
                name=record["other_name"], 
                labels=tuple(label for label in record["other_labels"] if label != "Entity")
            )
        facts.append(
            Fact(
                uuid = record["uuid"],
                statement = record["fact"],
                relation = record["name"],
                valid_at = parse_db_date(record["valid_at"]),
                invalid_at = parse_db_date(record["invalid_at"]),
                source_uuid=record["source_node_uuid"],
                target_uuid = record["target_node_uuid"]
            )
        )
    return list(entities.values()), facts

async def get_whole_graph(graph: Graphiti, *, tenant_id: str, limit: int = 500, include_superseded: bool = False) -> GraphSlice:
    records, _, _ = await graph.driver.execute_query(
        _WHOLE_GRAPH,
        group_id=tenant_id,
        include_superseded=include_superseded,
        limit=limit,
        routing_="r"
    )

    entities: dict[str, Entity] = {}
    facts: list[Fact] = []

    for record in records:
        for prefix in ("source", "target"):
            uuid = record[f"{prefix}_uuid"]
            if uuid not in entities:
                entities[uuid] = Entity(
                    uuid=uuid,
                    name=record[f"{prefix}_name"],
                    labels=tuple(label for label in record[f"{prefix}_labels"] if label != "Entity"),
                    summary=record[f"{prefix}_summary"] or None
                )
                
        
        facts.append(
            Fact(
                uuid=record["uuid"],
                statement=record["fact"],
                relation=record["name"],
                source_uuid=record["source_uuid"],
                target_uuid=record["target_uuid"],
                valid_at=parse_db_date(record["valid_at"]),
                invalid_at=parse_db_date(record["invalid_at"])
            )
        )
    
    count_records, _, _ = await graph.driver.execute_query(
        _WHOLE_GRAPH_COUNT,
        group_id=tenant_id,
        include_superseded=include_superseded,
        routing_="r"
    )
    total = count_records[0]["total"] if count_records else len(facts)

    return GraphSlice(
        entities=tuple(entities.values()),
        facts=tuple(facts),
        total_facts=total,
        truncated = total > len(facts)
    )

# Formatting

def format_facts(facts: Sequence[Fact], *, max_sources: int = 2) -> str:
    if not facts:
        return "No matching facts found."
    return "\n\n".join(_format_fact(fact, max_sources=max_sources) for fact in facts)

def format_entities(entities: Sequence[Entity]) -> str:
    if not entities:
        return "No matching entities found."
    
    blocks = []
    for entity in entities:
        header = entity.name
        if entity.labels:
            header += f"  [{', '.join(entity.labels)}]"
        lines = [header]

        if entity.summary:
            lines.append(f"  {entity.summary}")
        
        for key, value in entity.attributes.items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        
        lines.append(f"  {entity.uuid}")
        blocks.append("\n".join(lines))
        return "\n\n".join(blocks)
    
# internal formatting helper functions
def _format_fact(fact: Fact, *, max_sources: int) -> str:
    lines = [f"{fact.statement}{_window(fact.valid_at, fact.invalid_at)}"]

    for source in fact.sources[:max_sources]:
        lines.append(f"  Source: {_source_label(source)}")
        if source.url:
            lines.append(f"          {source.url}")
    
    for old in fact.superseded:
        lines.append(f'  Supersedes: "{old.statement}"{_window(old.valid_at, old.invalid_at)}')

    return "\n".join(lines)

def _source_label(source: Source) -> str:
    label = source.title or "untitled document"
    if source.path:
        label += f" ({source.path})"
    if source.last_edited_at:
        label += f", lasted edited {_day(source.last_edited_at)}"
    return label

def _window(valid_at: datetime | None, invalid_at: datetime | None) -> str:
    if valid_at and invalid_at:
        return f" - valid {_day(valid_at)} to {_day(invalid_at)}"
    if valid_at:
        return f" — valid since {_day(valid_at)}"
    if invalid_at:
        return f" — no longer true as of {_day(invalid_at)}"
    
    return " - no dates extracted"

def _day(value: datetime) -> str:
    return value.date().isoformat()

# More internal tools

async def _load_sources(graph: Graphiti, edges: Sequence[EntityEdge], tenant_id: str) -> dict[str, Source]:
    """Fetch episodes backing these edges"""

    uuids = sorted({ep for edge in edges for ep in (edge.episodes or [])})
    if not uuids:
        return {}
    
    records, _, _ = await graph.driver.execute_query(_EPISODES_BY_UUID, uuids=uuids, group_id=tenant_id, routing_="r")

    sources: dict[str, Source] = {}
    for record in records:
        meta = _parse_source_description(record["source_description"])
        sources[record["uuid"]] = Source(
            title = record["name"],
            url = meta.get("url"),
            path = meta.get("path"),
            last_edited_at = parse_db_date(record["valid_at"])
        )
    return sources

async def _load_history(graph: Graphiti, edges: Sequence[EntityEdge], tenant_id: str) -> dict[str, list[Fact]]:
    """For each edge, the invalidated facts between the same two entities."""
    pairs = [
        {
            "uuid": edge.uuid,
            "source": edge.source_node_uuid,
            "target": edge.target_node_uuid
        } for edge in edges
    ]
    if not pairs:
        return []
    
    try:
        records, _, _ = await graph.driver.execute_query(_SUPERSEDED_SIBLINGS, pairs=pairs, group_id=tenant_id, routing="r")
    except Exception:
        log.warning("Could not load fact history", exc_info=True)
        return {}
    
    history: dict[str, list[Fact]] = {}
    for record in records:
        history.setdefault(record["current_uuid"], []).append(
            Fact(
                uuid=record["uuid"],
                statement=record["fact"],
                relation=record["name"],
                valid_at=parse_db_date(record["valid_at"]),
                invalid_at=parse_db_date(record["invalid_at"])
            )
        )

    for facts in history.values():
        facts.sort(key=lambda f: f.invalid_at or f.valid_at or datetime.min, reverse=True)
    return history

def _parse_source_description(raw: str | None) -> dict[str, Any]:
    """Reads the metadata blob from ingest/episodes.py"""

    if not raw:
        return {}
    text = raw.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.debug("source_description looked like JSON but did not parse %r", raw)
    return {"path": text}

def _to_entity(node: EntityNode) -> Entity:
    """Turns Graphiti EntityNode into our generalized Entity class."""

    attributes = dict(node.attributes or {})
    attributes.pop("name_embedding", None)      # embeddings are large and have no meaning to a reader or LLM

    return Entity(
        uuid = node.uuid,
        name = node.name,
        labels = tuple(label for label in (node.labels or []) if label != "Entity"),
        summary = node.summary or None,
        attributes = attributes
    )