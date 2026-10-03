from __future__ import annotations

import json
import copy
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class DiscoveryState:
    """Durable pagination state keyed by source plus exact query/window fingerprint."""

    def __init__(self, path: str | Path = "data/discovery_state.json", *, autocommit: bool = True) -> None:
        self.autocommit = autocommit
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, dict[str, object]] = {}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, source: str, query: str) -> dict[str, object]:
        return dict(self.data.get(self.key(source, query), {}))

    def set(self, source: str, query: str, **values: object) -> None:
        key = self.key(source, query)
        entry = dict(self.data.get(key, {}))
        entry.update(values)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.data[key] = entry
        if self.autocommit:
            self.commit()

    def snapshot(self):
        return copy.deepcopy(self.data)

    def restore(self, snapshot):
        self.data = copy.deepcopy(snapshot)

    def commit(self) -> None:
        # Publish a complete checkpoint only after its records are durable.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            try:
                json.dump(self.data, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def key(source: str, query: str) -> str:
        return f"{source}:{query.strip().casefold()}"
