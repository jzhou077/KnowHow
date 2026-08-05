import asyncio
import logging

from brain.config import settings
from brain.connectors.notion.client import NotionClient
from brain.connectors.notion.crawl import crawl
from brain.store import raw

logging.basicConfig(level=logging.INFO)

async def main():
    client = NotionClient(settings.notion_token)
    async for record_id, payload in crawl(client, limit=10):
        raw.put("notion", record_id, payload)

asyncio.run(main())