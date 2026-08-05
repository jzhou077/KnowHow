import argparse
import asyncio
import logging

from brain.pipelines.ingest import ingest_all

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    result = await ingest_all(
        args.tenant,
        limit=args.limit,
        on_progress=lambda r: print(f" ingested={r.ingested} errors={len(r.errors)}", end="\r")
    )

    print(f"\ningested {result.ingested}, skipped {result.skipped}")
    for err in result.errors:
        print(f"ERROR {err}")

asyncio.run(main())