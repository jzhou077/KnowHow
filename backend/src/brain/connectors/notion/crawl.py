from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from notion_client.errors import APIResponseError

from .client import NotionClient

log = logging.getLogger(__name__)

# Helpers

async def fetch_users(client: NotionClient) -> list[dict[str, Any]]:
    """Returns every person in the Notion workplace."""

    return [user async for user in client.paginate(client.api.users.list)]

async def iter_search(client: NotionClient, object_type: str) -> AsyncIterator[dict[str, Any]]:
    """Every page or data source that the integration can see.
    
    *** NOTE: Notion search API is backed by an index so very recently created pages may not appear yet
    """
    async for obj in client.paginate(client.api.search, filter={"property": "object", "value": object_type}):
        yield obj

async def fetch_data_source(client: NotionClient, data_source_id: str) -> dict[str, Any]:
    """The full definition of a database table (including schema).
    
    Need this because regular search turns Notion databases into skeleton objects. This gives
    property definitions (what the Select options are, what a Relation points at).
    """
    return await client.call(client.api.data_sources.retrieve, data_source_id=data_source_id)

async def iter_data_source_rows(client: NotionClient, data_source_id: str) -> AsyncIterator[dict[str, Any]]:
    """Every row of one database table.
    
    Each row is a Notion page.
    """

    async for row in client.paginate(client.api.data_sources.query, data_source_id=data_source_id):
        yield row

async def fetch_blocks(client: NotionClient, block_id: str) -> list[dict[str, Any]]:
    """The full content tree of one page.

    Because Notion is annoying and only returns one level at a time, this function is recursively called
    to get all of the content from one page.
    """
    output: list[dict[str, Any]] = []
    async for block in client.paginate(client.api.blocks.children.list, block_id=block_id):
        block_type = block.get("type")

        if block_type in ("child_page", "child_database"):
            output.append(block)    
            continue                #do not go inside, otherwise double counting

        if block.get("has_children"):
            try:
                block["children"] = await fetch_blocks(client, block["id"])
            except APIResponseError as e:
                # a block can become unreadable mid-crawl (e.g. permissions change, someone deletes)
                # this safeguards against losing the whole crawl and only loses that one block
                log.warning(f"could not read children of {block["id"]}: {e.code}")
                block["children"] = []

        output.append(block)

    return output

# Filtering and de-duplication

def is_skippable(page: dict[str, Any]) -> bool:
    """Skips deleted or archived pages because feeding them to graph means agent can accidentally 
    output information others can't even see
    """
    return bool(page.get("archived") or page.get("in_trash"))

async def iter_unique_pages(client: NotionClient, data_source_ids: list[str]) -> AsyncIterator[dict[str, Any]]:
    """Every page in the workspace, each exactly once
    
    Necessary because we do two searches, one for databases and one general search. Without this,
    would crawl and store twice. Rows come first because the version returned by a data source query is richer.
    """

    seen: set[str] = set()

    for ds_id in data_source_ids:
        async for row in iter_data_source_rows(client, ds_id):
            if row["id"] not in seen:
                seen.add(row["id"])
                yield row

    async for page in iter_search(client, "page"):
        if page["id"] not in seen:
            seen.add(page["id"])
            yield page

# Main entry point

async def crawl(client: NotionClient, *, limit: int | None = None) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    """Walks the whole Notion workspace
    
    Yields (record_id, payload) pairs. Three kinds of payloads come out, each tagged with a "kind" field:
        - "users"           once at the start
        - "data_source"     once per db table
        - "page"            once per page, with full block tree

    limit caps the number of pages.
    """
    
    # 1. users
    users = await fetch_users(client)
    log.info("found %d users", len(users))
    yield "_users", {"kind": "users", "users": users}

    # 2. DB schemas
    data_source_ids: list[str] = []
    async for ds in iter_search(client, "data_source"):
        ds_id = ds["id"]
        try:
            full = await fetch_data_source(client, ds_id)
        except APIResponseError as e:
            log.warning(f"could not read data source {ds_id}: {e.code}")
            continue
        data_source_ids.append(ds_id)
        yield f"ds_{ds_id}", {"kind": "data_source", "data_source": full}

    log.info(f"found {len(data_source_ids)} data sources")

    # 3. Pages
    count = 0
    async for page in iter_unique_pages(client, data_source_ids):
        if is_skippable(page):
            continue

        page_id = page["id"]
        try:
            blocks = await fetch_blocks(client, page_id)
        except APIResponseError as e:
            log.warning(f"skipping page {page_id}: {e.code}")
            continue

        yield page_id, {"kind": "page", "page": page, "blocks": blocks}

        count += 1
        if count % 25 == 0:
            log.info(f"crawled {count} pages")

        if limit is not None and count >= limit:
            log.info(f"stopping at limit: {limit}")
            return
        
        log.info(f"done: {count} pages")