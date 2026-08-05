from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from brain.graph.client import ensure_schema, make_graphiti
from brain.retrieval import format_entities, format_facts, search_entities, search_facts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--entities", action="store_true", help="search for entities (nodes) instead of facts (edges)")
    parser.add_argument("--history", action="store_true", help="include facts that are no longer true")
    parser.add_argument("--type", action="append", dest="types", help="restrict to an entity or relation type; repeatable")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()

async def main(args: argparse.Namespace) -> str:
    graph = make_graphiti()
    await ensure_schema(graph)

    try:
        if args.entities:
            entities = await search_entities(
                graph,
                args.query,
                tenant_id = args.tenant,
                limit = args.limit,
                entity_labels = args.types
            )
            return format_entities(entities)
        
        facts = await search_facts(
            graph,
            args.query,
            tenant_id = args.tenant,
            limit = args.limit,
            relation_types = args.types,
            include_superseded = args.history
        )
        return format_facts(facts)
    
    finally:
        await graph.close()

if __name__ == "__main__":
    args = parse_args()
    
    # logs need to go to stderr and not stdout because MCP server's protocol uses stdout and logging to stdout would corrupt it
    logging.basicConfig(
        level = logging.DEBUG if args.verbose else logging.WARNING,
        stream = sys.stderr,
    )
    print(asyncio.run(main(args)))