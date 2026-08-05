import asyncio
import logging
import random
from typing import Any, AsyncIterator, Callable

from aiolimiter import AsyncLimiter
from notion_client import AsyncClient
from notion_client.errors import APIResponseError, HTTPResponseError

log = logging.getLogger(__name__)

NOTION_VERSION = "2026-03-11"

class NotionClient:
    def __init__(self, token: str, *, rate: float = 2.5, concurrency: int = 5):
        self._api = AsyncClient(auth=token, notion_version=NOTION_VERSION)
        self._limiter = AsyncLimiter(rate, 1)
        self._sem = asyncio.Semaphore(concurrency)

    @property
    def api(self):
        return self._api

    async def call(self, fn: Callable, **kwargs) -> Any:
        delay = 1.0
        attempts = 6
        for attempt in range(attempts):
            try:
                async with self._sem:
                    async with self._limiter:
                        return await fn(**kwargs)
            except APIResponseError as e:
                if e.code != "rate_limited" and not (e.status and e.status >= 500):
                    raise
            except (HTTPResponseError, asyncio.TimeoutError):
                pass
            await asyncio.sleep(delay + random.uniform(0, 0.3))
            delay = min(delay*2, 30)   
        raise RuntimeError("Notion: retries exhausted")

    async def paginate(self, fn, **kwargs) -> AsyncIterator[dict]:
        cursor = None
        while True:
            keywords = dict(kwargs, page_size=100)
            if cursor:
                keywords["start_cursor"] = cursor

            res = await self.call(fn, **keywords)
            
            for item in res.get("results", []):
                yield item
            
            if not res.get("has_more"):
                return

            cursor = res["next_cursor"]
