"""Lossless, conservative export from Virelion Intelligence to CardiAtlas JSONL.

This module intentionally emits CardiAtlas-shaped dictionaries without importing
CardiAtlas. Intelligence remains independently installable, while the generated
JSONL can be validated/loaded by `cardiatlas load`.

The exporter does not convert Intelligence claims/opportunities into Atlas
scientific claims. Source metadata becomes evidence records, and discovered
datasets become dataset records linked to database evidence records.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import DatasetRecord, SourceRecord

_SCHEMA_VERSION = "0.3"


def _unique(values: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _source_type(source: SourceRecord) -> str:
    if source.source_type == "clinical":
        return "clinical"
    if source.pmid:
        return "pubmed"
    if source.doi:
        return "doi"
    return "other"


def _source_evidence_level(source: SourceRecord) -> str:
    if source.source_type == "clinical":
        return "database"
    if source.source_type == "literature" and source.authority == "primary":
        return "primary"
    return "curated"


def source_to_atlas_evidence(source: SourceRecord) -> dict[str, Any]:
    """Map one discovered source to a provenance-preserving Atlas EvidenceRecord."""
    if not source.source_id.strip():
        raise ValueError("source_id must be non-empty for CardiAtlas export")
    identifier = source.pmid or source.doi or source.accession or source.source_id
    name = source.title.strip() or identifier
    return {
        "id": f"evidence:{source.source_id}",
        "record_type": "evidence",
        "name": name,
        "description": source.abstract or "",
        "source_ids": [source.source_id],
        "tags": _unique([*source.tags, "virelion-intelligence"]),
        "metadata": {
            "virelion_intelligence_source": source.model_dump(mode="json"),
            "export_semantics": "source_metadata_only",
        },
        "schema_version": _SCHEMA_VERSION,
        "source_type": _source_type(source),
        "source_identifier": identifier,
        "citation": source.title.strip() or identifier,
        "evidence_level": _source_evidence_level(source),
        "polarity": "unknown",
        "organism": None,
        "tissue": None,
        "assay": None,
        "year": source.published_at.year if source.published_at else None,
        "source_url": source.url,
        "extracted_claim": "",
        "context": {
            "intelligence_source_type": source.source_type,
            "authority": source.authority,
        },
    }


def _repository(value: str) -> str:
    normalized = value.strip().casefold()
    mapping = {
        "geo": "GEO",
        "sra": "SRA",
        "arrayexpress": "ArrayExpress",
        "array express": "ArrayExpress",
        "dbgap": "dbGaP",
        "dbgap ": "dbGaP",
    }
    return mapping.get(normalized, "other")


def _modality(assay: str | None) -> tuple[list[str], str]:
    if not assay or not assay.strip():
        return [], "unknown"
    token = " ".join(assay.strip().casefold().replace("_", " ").replace("-", " ").split())
    exact = {
        "rna seq": ("bulk_rna", "bulk"),
        "bulk rna seq": ("bulk_rna", "bulk"),
        "bulk rna": ("bulk_rna", "bulk"),
        "scrna": ("scrna", "cell"),
        "scrna seq": ("scrna", "cell"),
        "single cell rna seq": ("scrna", "cell"),
        "single cell transcriptomics": ("scrna", "cell"),
        "snrna": ("snrna", "nucleus"),
        "snrna seq": ("snrna", "nucleus"),
        "single nucleus rna seq": ("snrna", "nucleus"),
        "single nucleus transcriptomics": ("snrna", "nucleus"),
        "proteomics": ("proteomics", "unknown"),
        "imaging": ("imaging", "unknown"),
        "ecg": ("ecg", "unknown"),
        "physiology": ("physiology", "unknown"),
        "clinical": ("clinical", "unknown"),
    }
    mapped = exact.get(token)
    if mapped is None:
        return ["other"], "unknown"
    return [mapped[0]], mapped[1]


def dataset_to_atlas_records(dataset: DatasetRecord) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return database evidence and, when valid, a linked Atlas dataset record.

    Intelligence keeps missing-accession datasets as review candidates. CardiAtlas
    requires a non-empty accession, so those candidates export as evidence only
    rather than receiving an invented accession or producing invalid JSONL.
    """
    if not dataset.dataset_id.strip():
        raise ValueError("dataset_id must be non-empty for CardiAtlas export")
    evidence_id = f"evidence:{dataset.dataset_id}"
    repository = _repository(dataset.source)
    name = dataset.title.strip() or dataset.accession.strip() or dataset.dataset_id
    evidence_source_type = {
        "GEO": "geo",
        "SRA": "sra",
        "ArrayExpress": "arrayexpress",
    }.get(repository, "other")
    original = dataset.model_dump(mode="json")
    evidence = {
        "id": evidence_id,
        "record_type": "evidence",
        "name": name,
        "description": "",
        "source_ids": [dataset.dataset_id],
        "tags": ["virelion-intelligence", "dataset-metadata"],
        "metadata": {
            "virelion_intelligence_dataset": original,
            "export_semantics": "database_metadata_only",
        },
        "schema_version": _SCHEMA_VERSION,
        "source_type": evidence_source_type,
        "source_identifier": dataset.accession.strip() or dataset.dataset_id,
        "citation": dataset.title.strip() or dataset.accession.strip() or dataset.dataset_id,
        "evidence_level": "database",
        "polarity": "unknown",
        "organism": dataset.species,
        "tissue": dataset.tissue,
        "assay": dataset.assay,
        "year": None,
        "source_url": dataset.url,
        "extracted_claim": "",
        "context": {
            "identity_status": dataset.identity_status,
            "suitability_status": dataset.suitability_status,
            "metadata_quality": dataset.metadata_quality,
        },
    }

    if not dataset.accession.strip():
        return evidence, None

    modalities, cell_or_nucleus = _modality(dataset.assay)
    quality_flags = _unique([
        f"intelligence.identity_status:{dataset.identity_status}",
        f"intelligence.suitability_status:{dataset.suitability_status}",
        *(f"intelligence.note:{note}" for note in dataset.metadata_notes),
    ])
    atlas_dataset = {
        "id": f"dataset:{dataset.dataset_id}",
        "record_type": "dataset",
        "name": name,
        "description": "",
        "source_ids": [dataset.dataset_id],
        "tags": ["virelion-intelligence"],
        "metadata": {
            "virelion_intelligence_dataset": original,
            "cell_type": dataset.cell_type,
            "control": dataset.control,
            "platform": dataset.platform,
            "replicate_count": dataset.replicate_count,
            "suitability_score": dataset.suitability_score,
        },
        "schema_version": _SCHEMA_VERSION,
        "accession": dataset.accession,
        "repository": repository,
        "study_title": dataset.title,
        "organism": dataset.species or "",
        "tissue": dataset.tissue or "",
        "modalities": modalities,
        "cell_or_nucleus": cell_or_nucleus,
        "conditions": _unique([dataset.condition, dataset.control]),
        "sample_count": dataset.sample_count,
        "cell_count": None,
        "release_date": None,
        "source_url": dataset.url,
        "evidence_ids": [evidence_id],
        "study_id": None,
        "region": None,
        "timepoints": [],
        "quality_flags": quality_flags,
    }
    return evidence, atlas_dataset


def export_records(
    sources: Iterable[SourceRecord],
    datasets: Iterable[DatasetRecord],
) -> list[dict[str, Any]]:
    """Build deterministic, de-duplicated CardiAtlas records."""
    by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        record = source_to_atlas_evidence(source)
        by_id[record["id"]] = record
    for dataset in datasets:
        evidence, record = dataset_to_atlas_records(dataset)
        by_id[evidence["id"]] = evidence
        if record is not None:
            by_id[record["id"]] = record
    return [by_id[key] for key in sorted(by_id)]


def write_cardiatlas_jsonl(
    output: str | Path,
    *,
    sources: Iterable[SourceRecord],
    datasets: Iterable[DatasetRecord],
) -> int:
    """Write deterministic UTF-8 JSONL consumable by `cardiatlas load`."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = export_records(sources, datasets)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False))
            handle.write("\n")
    return len(records)
