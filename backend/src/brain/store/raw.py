import json
from pathlib import Path

RAW = Path("data/raw")

def put(source: str, native_id: str, payload: dict) -> None:
    path = RAW / source / f"{native_id}.json"      # pathlib overloads / operator so that it just joins strings with a '/'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True))

def iter_all(source: str):
    for file in (RAW / source).rglob("*.json"):     # .glob() only returns files from that file level whereas rglob recursively yields all files (including directories) in that subtree
        yield json.loads(file.read_text())