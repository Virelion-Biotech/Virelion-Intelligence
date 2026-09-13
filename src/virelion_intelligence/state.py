from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

class DiscoveryState:
    """Durable pagination state keyed by source plus exact query/window fingerprint."""
    def __init__(self, path: str | Path = "data/discovery_state.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, dict[str, object]] = {}
        if self.path.exists(): self.data = json.loads(self.path.read_text(encoding="utf-8"))
    def get(self, source: str, query: str) -> dict[str, object]: return dict(self.data.get(self.key(source, query), {}))
    def set(self, source: str, query: str, **values: object) -> None:
        key=self.key(source,query); entry=dict(self.data.get(key,{})); entry.update(values); entry["updated_at"]=datetime.now(timezone.utc).isoformat(); self.data[key]=entry; self.path.write_text(json.dumps(self.data,indent=2,sort_keys=True),encoding="utf-8")
    @staticmethod
    def key(source: str, query: str) -> str: return f"{source}:{query.strip().casefold()}"
