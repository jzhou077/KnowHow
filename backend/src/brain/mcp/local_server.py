from __future__ import annotations
 
import asyncio
import logging
import sys
 
from brain.config import settings
from brain.graph.client import make_graphiti
from brain.mcp.server import bind_graph, mcp
 
logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stderr,
    format="%(levelname)s %(name)s: %(message)s",
)
 
log = logging.getLogger("brain.mcp.stdio")
 
 
async def main() -> None:
    graph = make_graphiti()
    bind_graph(graph, settings.tenant_id)
    log.info("stdio MCP server starting for tenant %s", settings.tenant_id)
 
    try:
        await mcp.run_stdio_async()
    finally:
        await graph.close()
        log.info("stdio MCP server stopped")
 
 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass