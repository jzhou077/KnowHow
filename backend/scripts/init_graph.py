import asyncio

from brain.graph.client import make_graphiti


async def main() -> None:
    graph = make_graphiti()
    try:
        await graph.build_indices_and_constraints()
        print("built indices and constraints")
    finally:
        await graph.close()

asyncio.run(main())