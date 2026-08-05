"""Clears the graph and ledger, then re-ingest from raw store."""

import argparse
import asyncio
import logging

from graphiti_core.utils.maintenance.graph_data_operations import clear_data

from brain.graph.client import make_graphiti
from brain.ingest.done import LEDGER
from brain.pipelines.ingest import ingest_all

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="acme")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--yes", action="store_true", help="skip confirmation")
    args = parser.parse_args()

    # just so i dont accidentally run this
    if not args.yes:  # noqa: SIM102
        if input("Are you sure you want to DELETE EVERY NODE in the graph? Type 'yes': ").strip() != "yes":
            print("aborted")
            return
        
    graph = make_graphiti()
    try:
        await clear_data(graph.driver)
        await graph.build_indices_and_constraints()
        print("graph cleared, indices built")
    finally:
        await graph.close()

    LEDGER.unlink(missing_ok=True)
    print(f"Removed {LEDGER}")

    result = await ingest_all(
        args.tenant, 
        limit=args.limit,
        on_progress=lambda r: print(f" ingested={r.ingested} errors={len(r.errors)}", end="\r")
    )
    print(f"ingested: {result.ingested}, skipped: {result.skipped}")
    for err in result.errors:
        print(f"ERROR: {err}")
    
asyncio.run(main())