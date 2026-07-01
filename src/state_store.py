import json
from pathlib import Path


def load_seen(seen_file: str) -> set:
    path = Path(seen_file)
    if not path.exists():
        return set()
    return set(json.loads(path.read_text()))


def save_seen(seen_file: str, seen: set) -> None:
    path = Path(seen_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(seen)))
