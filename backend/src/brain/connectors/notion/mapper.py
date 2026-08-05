from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable, Iterator

from brain.models import Document, Provenance, Reference, SourceSystem

log = logging.getLogger(__name__)

LIST_TYPES = {"bulleted_list_item", "numbered_list_item", "to_do", "toggle"}

class WorkspaceIndex:
    """Built in one pass over every raw page before normalization
    
    Necessary because don't know relations between pages from a single page in isolation, need the whole workspace
    """

    def __init__(self) -> None:
        self.titles: dict[str, str] = {}
        self.parents: dict[str, str | None] = {}
        self.users: dict[str, str] = {}
        self.collections: dict[str, str] = {} # data_source id maps to name

    def add_page(self, page: dict[str, Any]) -> None:
        page_id = page["id"]
        self.titles[page_id] = extract_title(page.get("properties", {})) or "Untitled"
        self.parents[page_id] = parent_id_of(page)

    def add_users(self, users: Iterable[dict[str, Any]]) -> None:
        for user in users:
            if user.get("id") and user.get("name"):
                self.users[user["id"]] = user["name"]

    def add_data_source(self, ds: dict[str, Any]) -> None:
        name = "".join(t.get("plain_text", "") for t in ds.get("title", []))
        self.collections[ds["id"]] = name or "Untitled"

    def user(self, user_id: str | None) -> str | None:
        return self.users.get(user_id) if user_id else None

    def title(self, page_id: str | None) -> str | None:
        if not page_id:
            return None
        return self.titles.get(page_id) or self.collections.get(page_id)

    def path(self, page_id: str, max_depth: int = 12) -> list[str]:
        output: list[str] = []
        seen = {page_id}
        curr = self.parents.get(page_id)

        while curr and len(output) < max_depth and curr not in seen:
            seen.add(curr)
            label = self.title(curr)
            if label:
                output.append(label)
            curr = self.parents.get(curr)

        return list(reversed(output))

def parent_id_of(page: dict[str, Any]) -> str | None:
    parent = page.get("parent") or {}
    parent_type = parent.get("type")
    if parent_type in ("page_id", "database_id", "data_source_id", "block_id"):
        return parent.get(parent_type)
    return None         # workspace root




# Handling rich text

def rich_text_to_md(
    rich: list[dict[str, Any]] | None,
    refs: list[Reference],
    index: WorkspaceIndex
) -> str:

    parts: list[str] = []
    for text in rich or []:
        if text.get("type") == "mention":
            parts.append(_mention_to_md(text, refs, index))
            continue
            
        converted_text = text.get("plain_text", "")
        if not converted_text:
            continue
            
        annotations = text.get("annotations") or {}
        if annotations.get("code"):
            converted_text = f"`{converted_text}`"
        if annotations.get("bold"):
            converted_text = f"**{converted_text}**"
        if annotations.get("italic"):
            converted_text = f"*{converted_text}*"
        if annotations.get("strikethrough"):
            converted_text = f"~~{converted_text}~~"
        if text.get("href"):
            converted_text = f"[{converted_text}]({text['href']})"
        parts.append(converted_text)

    return "".join(parts)

def _mention_to_md(
    text: dict[str, Any],
    refs: list[Reference],
    index: WorkspaceIndex
) -> str:
    mention = text.get("mention") or {}
    kind = mention.get("type")
    plain = text.get("plain_text", "")

    if kind in ("page", "database", "data_source"):
        target = (mention.get(kind) or {}).get("id")

        if target:
            title = index.title(target) or plain
            refs.append(
                Reference(
                    target_id=f"notion:{target}",
                    kind="mention",
                    target_title=title
                )
            )
            return title
    elif kind == "user":
        uid = (mention.get("user") or {}).get("id")
        return index.user(uid) or plain

    return plain



# Handling blocks

def block_to_md(
    block: dict[str, Any],
    refs: list[Reference],
    index: WorkspaceIndex,
    depth: int = 0
) -> str:
    block_type = block.get("type", "")
    data = block.get(block_type) or {}
    indent = "  " * depth
    text = rich_text_to_md(data.get("rich_text"), refs, index)
    line = ""

    if block_type == "paragraph":
        line = text
    elif block_type.startswith("heading_"):
        level = int(block_type[-1])
        line = f"{'#' * level} {text}"
    elif block_type == "bulleted_list_item":
        line = f"{indent}- {text}"
    elif block_type == "numbered_list_item":
        line = f"{indent}1. {text}"
    elif block_type == "to_do":
        box = "x" if data.get("checked") else " "
        line = f"{indent}- [{box}] {text}"
    elif block_type == "toggle":
        line = f"{indent}- {text}"
    elif block_type == "quote":
        line = f"> {text}"
    elif block_type == "callout":
        icon = (data.get("icon") or {}).get("emoji", "")
        line = f"> {icon} {text}".strip()
    elif block_type == "code":
        lang = data.get("language", "")
        line = f"```{lang}\n{text}\n```"
    elif block_type == "equation":
        line = f"$$ {data.get('expression', '')} $$"
    elif block_type == "divider":
        line = "---"
    elif block_type == "table":
        return table_to_md(block, refs, index)
    elif block_type in ("image", "file", "pdf", "video", "audio"):
        caption = rich_text_to_md(data.get("caption"), refs, index)
        line = f"[{block_type}: {caption}]" if caption else f"[{block_type}]"
    elif block_type == "bookmark" or block_type == "link_preview":
        line = f"[link]({data.get('url', '')})"
    elif block_type in ("child_page", "child_database"):
        # A separate Document. Record the edge; do NOT inline the subtree.
        refs.append(
            Reference(
                target_id=f"notion:{block["id"]}",
                kind="child",
                target_title=data.get("title") or index.title(block["id"])
            )
        )
        return ""
    elif block_type == "synced_block":
        if (data.get("synced_from") or {}).get("block_id"):
            return ""       # mirror of content ingested somewhere else
    elif block_type in ("unsupported", "table_of_contents", "breadcrumb"):
        return ""
    else:
        line = text

    parts = [line] if line else []
    child_depth = depth + 1 if block_type in LIST_TYPES else depth
    for child in block.get("children") or []:
        rendered = block_to_md(child, refs, index, child_depth)
        if rendered:
            parts.append(rendered)
    return "\n".join(parts)

def table_to_md(
    block: dict[str, Any],
    refs: list[Reference],
    index: WorkspaceIndex
) -> str:
    rows: list[list[str]] = []
    for child in block.get("children") or []:
        if child.get("type") != "table_row":
            continue
        cells = (child.get("table_row") or {}).get("cells") or []
        rows.append([rich_text_to_md(cell, refs, index) for cell in cells])
    if not rows:
        return ""

    has_header = bool((block.get("table") or {}).get("has_column_header"))
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]

    output: list[str] = []
    header = rows[0] if has_header else [""] * width
    body = rows[1:] if has_header else rows
    output.append("| " + " | ".join(header) + " |")
    output.append("| " + " | ".join(["---"] * width) + " |")
    for row in body:
        output.append("| " + " | ".join(row) + " |")
    return "\n".join(output)



# Handling properties

def extract_title(props: dict[str, Any]) -> str:
    for prop in (props or {}).values():
        if prop.get("type") == "title":
            return "".join(x.get("plain_text", "") for x in prop.get("title", []))
    return ""

def properties_to_md(
    props: dict[str, Any],
    refs: list[Reference],
    index: WorkspaceIndex
) -> str:
    """Renders page properties as text.
    
    Goes inside episode body for Graphiti, not metadata because metadata is invisible to extraction
    """
    lines: list[str] = []
    for name, prop in (props or {}).items():
        prop_type = prop.get("type")
        val: Any = None

        if prop_type == "title":
            continue
        elif prop_type == "relation":
            titles = []
            for relation in prop.get("relation") or []:
                relation_id = relation.get("id")
                if not relation_id:
                    continue
                title = index.title(relation_id) or relation_id
                titles.append(title)
                refs.append(
                    Reference(
                        target_id=f"notion:{relation_id}",
                        kind="relation",
                        label=name,
                        target_title=title
                    )
                )
            val = ", ".join(titles)
        elif prop_type == "rich_text":
            val = rich_text_to_md(prop.get("rich_text"), refs, index)
        elif prop_type == "select":
            val = (prop.get("select") or {}).get("name")
        elif prop_type == "status":
            val = (prop.get("status") or {}).get("name")
        elif prop_type == "multi_select":
            val = ", ".join(obj.get("name", "") for obj in prop.get("multi_select") or [])
        elif prop_type in ("people", "created_by", "last_edited_by"):
            raw = prop.get("prop_type")
            people = raw if isinstance(raw, list) else [raw]
            val = ", ".join(index.user(person.get("id")) or person.get("name") or "" for person in people if person)
        elif prop_type == "date":
            date = prop.get("date") or {}
            val = " to ".join(x for x in (date.get("start"), date.get("end")) if x)
        elif prop_type in ("created_time", "last_edited_time", "url", "email", "phone_number", "number", "checkbox"):
            val = prop.get(prop_type)
        elif prop_type == "formula":
            f = prop.get("formula") or {}
            val = f.get(f.get("type", ""))
        elif prop_type == "rollup":
            r = prop.get("rollup") or {}
            val = r.get(r.get("type", ""))
        elif prop_type == "files":
            val = ", ".join(file.get("name", "") for file in prop.get("files") or [])

        if val not in (None, "", [], False):
            lines.append(f"- {name}: {val}")

    return "\n".join(lines)



# entry point

def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def to_document(
    page: dict[str, Any],
    blocks: list[dict[str, Any]],
    index: WorkspaceIndex,
    tenant_id: str
) -> Document:
    refs: list[Reference] = []
    props = page.get("properties") or {}

    title = extract_title(props) or "Untitled"
    front = properties_to_md(props, refs, index)

    body_parts: list[str] = [f"# {title}"]
    if front:
        body_parts.append(front)
    for block in blocks:
        rendered = block_to_md(block, refs, index)
        if rendered:
            body_parts.append(rendered)
    
    parent_id = parent_id_of(page)
    if parent_id:
        refs.append(
            Reference(
                target_id=f"notion:{parent_id}",
                kind="parent",
                target_title=index.title(parent_id)
            )
        )
    
    parent = page.get("parent") or {}
    collection = None
    if parent.get("type") in ("database_id", "data_source_id"):
        collection = index.title(parent_id)

    prov = Provenance(
        source=SourceSystem.notion,
        tenant_id=tenant_id,
        native_id=page["id"],
        url=page.get("url"),
        author=index.user((page.get("created_by") or {}).get("id")),
        last_editor=index.user((page.get("last_edited_by") or {}).get("id")),
        parent_path=index.path(page["id"]),
        collection=collection,
        created_at=parse_timestamp(page.get("created_time")),
        last_edited_at=parse_timestamp(page.get("last_edited_time"))
    )

    return Document(
        id=f"notion:{page["id"]}",
        title=title,
        body_markdown="\n\n".join(body_parts).strip(),
        provenance=prov,
        references=dedupe_refs(refs),
        doc_type=collection
    )

def dedupe_refs(refs: list[Reference]) -> list[Reference]:
    seen: set[tuple[str, str, str | None]] = set()
    output: list[Reference] = []
    for ref in refs:
        key = (ref.target_id, ref.kind, ref.label)
        if key in seen:
            continue
        seen.add(key)
        output.append(ref)
    return output

# payloads are jsons
def build_index(payloads: Iterable[dict[str, Any]]) -> WorkspaceIndex:
    index = WorkspaceIndex()
    pages = users = sources = 0

    for payload in payloads:
        kind = payload.get("kind")
        if kind == "page":
            index.add_page(payload["page"])
            pages += 1
        elif kind == "users":
            index.add_users(payload["users"])
            users += 1
        elif kind == "data_source":
            index.add_data_source(payload["data_source"])
            sources += 1
        else:
            log.warning(f"unknown payload kind: {kind}")
    
    log.info("index built: %d pages, %d users, %d data sources", pages, users, sources)
    return index

def iter_documents(
    payloads: Iterable[dict[str, Any]],
    index: WorkspaceIndex,
    tenant_id: str
) -> Iterator[Document]:
    for payload in payloads:
        if payload.get("kind") != "page":
            continue

        page = payload["page"]
        try:
            yield to_document(page, payload["blocks"], index, tenant_id)
        except Exception:
            log.exception("could not normalize page %s", page.get("id"))