from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .models import PaperRecord
from .normalize import canonical_title, normalize_doi, normalize_pmid


@dataclass(frozen=True)
class DuplicateDecision:
    duplicate: bool
    basis: str
    matched_id: str | None = None
    similarity: float = 0.0


def dedupe_against(candidate: PaperRecord, existing: list[PaperRecord], threshold: float = 0.94) -> DuplicateDecision:
    doi = normalize_doi(candidate.doi)
    pmid = normalize_pmid(candidate.pmid)
    title = canonical_title(candidate.title)
    for item in existing:
        if doi and normalize_doi(item.doi) == doi:
            return DuplicateDecision(True, "doi", item.paper_id, 1.0)
        if pmid and normalize_pmid(item.pmid) == pmid:
            return DuplicateDecision(True, "pmid", item.paper_id, 1.0)
    best: tuple[float, PaperRecord] | None = None
    for item in existing:
        score = SequenceMatcher(None, title, canonical_title(item.title)).ratio()
        if best is None or score > best[0]:
            best = (score, item)
    if best and best[0] >= threshold:
        return DuplicateDecision(True, "title", best[1].paper_id, best[0])
    return DuplicateDecision(False, "none", None, best[0] if best else 0.0)
