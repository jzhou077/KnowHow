"""
integrations/notion_graph.py


>>> SWAP POINT FOR BACKEND <<<
This whole file only needs to keep returning the same shapes:
    get_graph()             -> {"nodes": [...], "edges": [...]}
    get_node_detail(node_id) -> dict | None

When the real backend is ready, it can either:
  (a) keep exporting markdown files in this same frontmatter format into
      data/notion_pages/, and this parser keeps working as-is, or
  (b) replace the body of get_graph()/get_node_detail() with a real API
      call that returns the same node/edge shape.
Nothing in UserInterface.py or graph_view.py has to change either way.

Node shape:   {"id": str, "label": str, "type": "project"|"document"|"person"|"topic", "meta": dict}
Edge shape:   {"source": str, "target": str, "relation": str}
"""

import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "notion_pages"

# Small, easy-to-extend keyword -> topic map. Add a line here and any page
# whose title/type mentions the keyword gets linked to that Topic node.
TOPIC_KEYWORDS = {
    "SSO & Identity": ["SSO", "SAML", "OIDC", "Identity"],
    "Data Infrastructure": ["Iceberg", "Data Pipeline", "Data Infrastructure"],
    "Platform": ["Platform", "Control Plane"],
    "Mobile": ["Mobile App"],
    "Website": ["Website"],
    "Onboarding": ["Onboarding"],
}

_FRONTMATTER_RE = re.compile(r"^- (\w[\w ]*): (.+)$")
_MENTION_RE = re.compile(r"@([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?)")
_LABELED_PEOPLE_RE = re.compile(
    r"\*\*(Author|Reviewers|Approved by)\:\*\*\s*(.+)"
)


def _parse_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = lines[0].lstrip("#").strip() if lines else path.stem

    meta = {}
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            body_start = i + 1
            break
        m = _FRONTMATTER_RE.match(line.strip())
        if m:
            meta[m.group(1).strip().lower()] = m.group(2).strip()

    body = "\n".join(lines[body_start:]).strip()

    page_id = meta.get("id", path.stem).replace("`", "").replace("notion:", "")

    return {
        "id": page_id,
        "title": title,
        "path": meta.get("path", ""),
        "last_edited_at": meta.get("last_edited_at", ""),
        "author": meta.get("author", ""),
        "collection": meta.get("collection", ""),
        "references": meta.get("references", ""),
        "body": body,
    }


def _excerpt(body: str, max_len: int = 260) -> str:
    """First real paragraph of the body, skipping headings/bullets/blank lines."""
    for para in body.split("\n\n"):
        clean = para.strip().lstrip("#").strip()
        if clean and not clean.startswith("-") and not clean.startswith("|"):
            return clean[:max_len] + ("…" if len(clean) > max_len else "")
    return ""


def _find_people(body: str) -> set:
    names = set(_MENTION_RE.findall(body))
    for _, value in _LABELED_PEOPLE_RE.findall(body):
        for part in re.split(r",| and ", value):
            cleaned = re.sub(r"[\(\)@]|CTO|acting", "", part).strip()
            if cleaned and len(cleaned.split()) <= 3:
                names.add(cleaned)
    return {n.strip() for n in names if n.strip()}


def _matching_topics(title: str, page_type: str):
    hay = f"{title} {page_type}".lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.lower() in hay for kw in keywords):
            yield topic


def build_graph():
    if not DATA_DIR.exists():
        return {"nodes": [], "edges": []}

    pages = [_parse_page(p) for p in sorted(DATA_DIR.glob("*.md"))]
    pages_by_title = {p["title"].lower(): p for p in pages}

    nodes = {}
    edges = []

    def add_node(node_id, label, node_type, meta=None):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": node_type, "meta": meta or {}}
        return node_id

    def add_edge(source, target, relation):
        if source and target and source != target:
            edges.append({"source": source, "target": target, "relation": relation})

    for page in pages:
        page_type = "project" if page["collection"].lower() == "projects" else "document"
        node_id = f"page:{page['id']}"
        add_node(
            node_id,
            page["title"],
            page_type,
            {
                "path": page["path"],
                "author": page["author"],
                "last_edited_at": page["last_edited_at"],
                "collection": page["collection"],
                "references": page["references"],
                "excerpt": _excerpt(page["body"]),
            },
        )

        # Author -> authored -> Page
        if page["author"]:
            person_id = f"person:{page['author']}"
            add_node(person_id, page["author"], "person", {"role": "Author"})
            add_edge(person_id, node_id, "authored")

        # Other people mentioned in the body (reviewers, approvers, decision owners)
        for name in _find_people(page["body"]):
            if name == page["author"]:
                continue
            person_id = f"person:{name}"
            add_node(person_id, name, "person", {"role": "Mentioned"})
            add_edge(person_id, node_id, "mentioned in")

        # Doc -> belongs to -> Project, matched by "Project: <Title>" in the body
        proj_match = re.search(r"^- Project: (.+)$", page["body"], re.MULTILINE)
        if proj_match:
            target_title = proj_match.group(1).strip().lower()
            target_page = pages_by_title.get(target_title)
            if target_page:
                add_edge(node_id, f"page:{target_page['id']}", "belongs to")

        # Topics
        for topic in _matching_topics(page["title"], page.get("path", "")):
            topic_id = f"topic:{topic}"
            add_node(topic_id, topic, "topic", {})
            add_edge(node_id, topic_id, "about")

    return {"nodes": list(nodes.values()), "edges": edges}


def get_graph():
    """Public entry point — returns the full graph for the Notion source."""
    return build_graph()


def get_node_detail(node_id: str):
    """Detail content for the side panel when a node is clicked."""
    graph = build_graph()
    node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
    if not node:
        return None

    connections = [
        e for e in graph["edges"] if e["source"] == node_id or e["target"] == node_id
    ]
    node_lookup = {n["id"]: n for n in graph["nodes"]}
    related = []
    for e in connections:
        other_id = e["target"] if e["source"] == node_id else e["source"]
        other = node_lookup.get(other_id)
        if other:
            related.append({"label": other["label"], "type": other["type"], "relation": e["relation"]})

    return {**node, "related": related}
