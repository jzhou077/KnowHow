import asyncio

from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF

from brain.graph.client import make_graphiti


async def main():
    g = make_graphiti()
    try:
        cfg = EDGE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        cfg.limit = 3
        r = await g.search_(query="enterprise sso integration", config=cfg, group_ids=["MeridianSystems"])
        for e in r.edges:
            print(e.fact[:50], "->", e.episodes)
    finally:
        await g.close()

asyncio.run(main())