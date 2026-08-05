"""Writes every normalized Document to data/normalized/*.md and reads them."""

import logging
from pathlib import Path

from brain.connectors.notion import build_index, iter_documents
from brain.store import raw

logging.basicConfig(level=logging.INFO)

OUT_PATH = Path("data/normalized")
TENANT = "acme"

def main() -> None:
    index = build_index(raw.iter_all("notion"))
    OUT_PATH.mkdir(parents=True, exist_ok=True)

    count = 0
    for doc in iter_documents(raw.iter_all("notion"), index, TENANT):
        slug = doc.id.split(":", 1)[1]
        header = (
            f"# {doc.title}\n\n"
            f"- id: `{doc.id}`\n"
            f"- path: {' / '.join(doc.provenance.parent_path) or '(top level)'}\n"
            f"- last_edited_at: {doc.provenance.last_edited_at}\n"
            f"- author: {doc.provenance.author}\n"
            f"- collection: {doc.provenance.collection}\n"
            f"- references: {len(doc.references)}\n\n"
            "---\n\n"
        )
        (OUT_PATH / f"{slug}.md").write_text(header + doc.body_markdown)
        count += 1

    print(f"wrote {count} documents to {OUT_PATH}")

main()