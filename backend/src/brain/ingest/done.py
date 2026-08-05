"""For document IDs that have already been ingested.

So that a crash mid-ingestion for 500 pages doesn't mean you have to redo those extractions again
"""

from pathlib import Path

LEDGER = Path("data/ingested.txt")

def load() -> set[str]:
    """Reads the ledger once, at the start of a run."""
    if not LEDGER.exists():
        return set()
    return {line.strip() for line in LEDGER.read_text().splitlines() if line.strip()}

def mark(doc_id: str) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as file:
        file.write(f"{doc_id}\n")
        file.flush()        # just means that if jittleyang crashes midway then you only lose that one document/page rather than the whole shebang
