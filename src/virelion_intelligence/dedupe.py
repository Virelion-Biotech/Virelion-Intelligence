from __future__ import annotations

from dataclasses import dataclass

from .normalize import canonical_publication_key, normalize_title


@dataclass(frozen=True)
class DedupeCandidate:
    key: str
    title: str
    doi: str | None = None
    pmid: str | None = None


def deduplicate(records: list[DedupeCandidate]) -> tuple[list[DedupeCandidate], dict[str, list[str]]]:
    """Exact DOI/PMID/title-key deduplication; preserves first occurrence."""
    seen: dict[str, DedupeCandidate] = {}
    duplicates: dict[str, list[str]] = {}
    for record in records:
        key = canonical_publication_key(record.title, record.doi, record.pmid)
        if key in seen:
            duplicates.setdefault(key, []).append(record.key)
        else:
            seen[key] = record
    return list(seen.values()), duplicates
