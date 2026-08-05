from dataclasses import dataclass, field

from brain.connectors.notion.crawl import crawl
from brain.connectors.store.raw import put


@dataclass
class CrawlResult:
    pages: int = 0
    errors: list[str] = field(default_factory=list)

async def crawl_workspace(tenant_id: str, *, limit: int | None = None, on_progress = None) -> CrawlResult:
    result = CrawlResult()
    async for page_id, payload in crawl(limit=limit):
        try:
            put("notion", page_id, payload)
            result.pages += 1
        except Exception as e:
            result.errors.append(f"{page_id}: {e}")
        if on_progress:
            on_progress(result.pages)

    return result