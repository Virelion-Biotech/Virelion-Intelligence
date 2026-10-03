from __future__ import annotations

from .models import DatasetRecord


UNRESOLVED = {"", "unknown", "unresolved", "ambiguous", "n/a", "na", "none"}


def metadata_quality(dataset: DatasetRecord) -> float:
    fields = [dataset.species, dataset.tissue, dataset.cell_type, dataset.condition, dataset.control, dataset.assay, dataset.platform]
    present = sum(1 for value in fields if value and value.strip().casefold() not in UNRESOLVED)
    return round(present / len(fields), 3)


def identity_check(dataset: DatasetRecord) -> tuple[str, list[str]]:
    notes: list[str] = []
    if not dataset.accession:
        return "AMBIGUOUS", ["missing dataset accession"]
    if dataset.sample_count is None:
        notes.append("sample count unresolved")
    if dataset.condition and dataset.control and dataset.condition.casefold() == dataset.control.casefold():
        notes.append("condition and control labels are identical")
    if dataset.replicate_count is None:
        notes.append("replicate count unresolved")
    if notes:
        return "REVIEW_REQUIRED", notes
    return "RESOLVED", notes


def assess_dataset(dataset: DatasetRecord) -> DatasetRecord:
    q = metadata_quality(dataset)
    identity, notes = identity_check(dataset)
    dataset.metadata_quality = q
    dataset.identity_status = identity
    dataset.metadata_notes = list(dict.fromkeys(dataset.metadata_notes + notes))
    score = q * 70
    if dataset.sample_count:
        score += min(dataset.sample_count, 100) / 100 * 15
    if dataset.replicate_count:
        score += min(dataset.replicate_count, 10) / 10 * 15
    dataset.suitability_score = round(min(score, 100), 2)
    dataset.suitability_status = "ACCEPTED" if identity == "RESOLVED" and q >= 0.75 else "REVIEW_REQUIRED"
    return dataset
