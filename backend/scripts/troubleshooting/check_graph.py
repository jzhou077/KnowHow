from __future__ import annotations

import asyncio
import logging
import sys
 
from brain.config import settings
from brain.graph.client import make_graphiti

FREE_NODE_LIMIT = 200_000
FREE_RELATIONSHIP_LIMIT = 400_000

async def main() -> list[str]:
    lines: list[str] = []
    graph = make_graphiti()
    try:
        driver = graph.driver
 
        lines.append(f"uri: {settings.neo4j_uri}")
        if settings.neo4j_uri.startswith("bolt://"):
            lines.append("  ^ plain bolt, so this is local Docker, not Aura")
        lines.append("")
 
        # --- node counts by label ---
        records, _, _ = await driver.execute_query(
            "MATCH (n) RETURN labels(n) AS labels, count(*) AS count "
            "ORDER BY count DESC",
            routing_="r",
        )
        total_nodes = sum(r["count"] for r in records)
        lines.append(f"nodes: {total_nodes:,}")
        for record in records:
            labels = "/".join(record["labels"]) or "(no label)"
            lines.append(f"  {labels:<28} {record['count']:>8,}")
        if total_nodes > FREE_NODE_LIMIT * 0.8:
            lines.append(
                f"  WARNING: {total_nodes:,} of the Aura Free limit of "
                f"{FREE_NODE_LIMIT:,} nodes"
            )
        lines.append("")
 
        # --- relationship counts by type ---
        records, _, _ = await driver.execute_query(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count "
            "ORDER BY count DESC",
            routing_="r",
        )
        total_rels = sum(r["count"] for r in records)
        lines.append(f"relationships: {total_rels:,}")
        for record in records:
            lines.append(f"  {record['type']:<28} {record['count']:>8,}")
        if total_rels > FREE_RELATIONSHIP_LIMIT * 0.8:
            lines.append(
                f"  WARNING: {total_rels:,} of the Aura Free limit of "
                f"{FREE_RELATIONSHIP_LIMIT:,} relationships"
            )
        lines.append("")
 
        # --- tenants present ---
        records, _, _ = await driver.execute_query(
            "MATCH (n:Entity) RETURN n.group_id AS tenant, count(*) AS count "
            "ORDER BY count DESC",
            routing_="r",
        )
        lines.append("tenants (group_id on entities):")
        for record in records:
            lines.append(f"  {str(record['tenant']):<28} {record['count']:>8,}")
        if not records:
            lines.append("  (none - no entities in the graph)")
        lines.append("")
 
        # --- the temporal signal ---
        records, _, _ = await driver.execute_query(
            "MATCH (e:Episodic) "
            "RETURN count(e) AS episodes, "
            "       count(DISTINCT e.valid_at) AS distinct_times, "
            "       min(e.valid_at) AS earliest, "
            "       max(e.valid_at) AS latest",
            routing_="r",
        )
        if records:
            row = records[0]
            lines.append(f"episodes: {row['episodes']:,}")
            lines.append(f"  distinct reference times: {row['distinct_times']:,}")
            lines.append(f"  earliest: {row['earliest']}")
            lines.append(f"  latest:   {row['latest']}")
            if row["episodes"] > 1 and row["distinct_times"] <= 1:
                lines.append(
                    "  BROKEN: every episode has the same reference_time. "
                    "reference_time is falling back to ingest time instead of "
                    "the document's last_edited_at. Fix episodes.py and "
                    "re-ingest - nothing downstream is trustworthy until you do."
                )
        lines.append("")
 
        # --- facts with usable validity windows ---
        records, _, _ = await driver.execute_query(
            "MATCH ()-[r:RELATES_TO]->() "
            "RETURN count(r) AS total, "
            "       count(r.valid_at) AS with_valid_at, "
            "       count(r.invalid_at) AS superseded",
            routing_="r",
        )
        if records:
            row = records[0]
            lines.append(f"facts: {row['total']:,}")
            lines.append(f"  with a valid_at date: {row['with_valid_at']:,}")
            lines.append(f"  superseded (invalid_at set): {row['superseded']:,}")
            if row["total"] and row["superseded"] == 0:
                lines.append(
                    "  note: nothing has been superseded yet. Expected on a "
                    "small workspace, but the demo needs at least one "
                    "contradiction to show."
                )
        lines.append("")
 
        # --- indexes ---
        records, _, _ = await driver.execute_query(
            "SHOW INDEXES YIELD name, type, state", routing_="r"
        )
        lines.append(f"indexes: {len(records)}")
        not_online = [r for r in records if r["state"] != "ONLINE"]
        by_type: dict[str, int] = {}
        for record in records:
            by_type[record["type"]] = by_type.get(record["type"], 0) + 1
        for index_type, count in sorted(by_type.items()):
            lines.append(f"  {index_type:<28} {count:>8}")
        if not_online:
            lines.append(f"  WARNING: {len(not_online)} index(es) not ONLINE yet")
        if not records:
            lines.append("  WARNING: no indexes. Run scripts/init_graph.py.")
 
        return lines
    finally:
        await graph.close()
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    print("\n".join(asyncio.run(main())))