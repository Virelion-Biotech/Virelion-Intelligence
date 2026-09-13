from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Any


@dataclass(frozen=True)
class Query:
    text: str
    start: datetime
    end: datetime
    limit: int = 100


@dataclass(frozen=True)
class RawRecord:
    source: str
    external_id: str
    payload: dict[str, Any]


class SourceAdapter(Protocol):
    source_id: str

    def search(self, query: Query) -> list[RawRecord]:
        ...

    def fetch(self, external_id: str) -> RawRecord:
        ...


class StaticAdapter:
    """Minimal deterministic adapter for fixtures and pipeline integration tests."""

    source_id = "static"

    def __init__(self, records: list[RawRecord] | None = None):
        self.records = records or []

    def search(self, query: Query) -> list[RawRecord]:
        return self.records[: query.limit]

    def fetch(self, external_id: str) -> RawRecord:
        for record in self.records:
            if record.external_id == external_id:
                return record
        raise KeyError(external_id)
