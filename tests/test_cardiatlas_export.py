from __future__ import annotations

import json
from datetime import datetime, timezone

from virelion_intelligence.cardiatlas_export import (
    dataset_to_atlas_records,
    export_records,
    source_to_atlas_evidence,
    write_cardiatlas_jsonl,
)
from virelion_intelligence.models import DatasetRecord, SourceRecord


def _source(**overrides):
    data = dict(
        source_id="pubmed:123",
        source_type="literature",
        title="Cardiac regeneration study",
        url="https://pubmed.ncbi.nlm.nih.gov/123/",
        published_at=datetime(2025, 2, 3, tzinfo=timezone.utc),
        pmid="123",
        abstract="Observed source abstract.",
        authority="primary",
        tags=["pubmed"],
    )
    data.update(overrides)
    return SourceRecord(**data)


def _dataset(**overrides):
    data = dict(
        dataset_id="geo:GSE123",
        source="GEO",
        accession="GSE123",
        title="Heart single-nucleus study",
        url="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123",
        species="Homo sapiens",
        tissue="heart",
        condition="MI",
        control="sham",
        assay="single nucleus RNA-seq",
        sample_count=8,
        replicate_count=None,
        metadata_quality=0.57,
        identity_status="REVIEW_REQUIRED",
        suitability_score=51.0,
        suitability_status="REVIEW_REQUIRED",
        metadata_notes=["replicate count unresolved"],
    )
    data.update(overrides)
    return DatasetRecord(**data)


def test_source_export_is_metadata_evidence_not_fabricated_claim():
    record = source_to_atlas_evidence(_source())
    assert record["record_type"] == "evidence"
    assert record["source_type"] == "pubmed"
    assert record["source_identifier"] == "123"
    assert record["evidence_level"] == "primary"
    assert record["polarity"] == "unknown"
    assert record["extracted_claim"] == ""
    assert record["description"] == "Observed source abstract."
    assert record["metadata"]["export_semantics"] == "source_metadata_only"


def test_clinical_source_is_database_evidence():
    record = source_to_atlas_evidence(
        _source(
            source_id="clinicaltrials:NCT1",
            source_type="clinical",
            pmid=None,
            accession="NCT1",
            authority="primary",
        )
    )
    assert record["source_type"] == "clinical"
    assert record["evidence_level"] == "database"
    assert record["extracted_claim"] == ""


def test_dataset_export_preserves_review_state_and_links_evidence():
    evidence, dataset = dataset_to_atlas_records(_dataset())
    assert dataset is not None
    assert evidence["source_type"] == "geo"
    assert evidence["evidence_level"] == "database"
    assert evidence["extracted_claim"] == ""
    assert dataset["repository"] == "GEO"
    assert dataset["modalities"] == ["snrna"]
    assert dataset["cell_or_nucleus"] == "nucleus"
    assert dataset["conditions"] == ["MI", "sham"]
    assert dataset["evidence_ids"] == [evidence["id"]]
    assert "intelligence.identity_status:REVIEW_REQUIRED" in dataset["quality_flags"]
    assert "intelligence.note:replicate count unresolved" in dataset["quality_flags"]


def test_unknown_assay_is_not_guessed():
    _, dataset = dataset_to_atlas_records(_dataset(assay="spatial multi-omic custom assay"))
    assert dataset is not None
    assert dataset["modalities"] == ["other"]
    assert dataset["cell_or_nucleus"] == "unknown"
    assert dataset["metadata"]["virelion_intelligence_dataset"]["assay"] == "spatial multi-omic custom assay"


def test_missing_accession_exports_evidence_only_without_inventing_identity():
    evidence, dataset = dataset_to_atlas_records(
        _dataset(accession="", identity_status="AMBIGUOUS")
    )
    assert dataset is None
    assert evidence["source_identifier"] == "geo:GSE123"
    assert evidence["context"]["identity_status"] == "AMBIGUOUS"
    assert evidence["extracted_claim"] == ""


def test_empty_titles_use_existing_identifiers_not_invented_text():
    source = source_to_atlas_evidence(_source(title=""))
    assert source["name"] == "123"
    evidence, dataset = dataset_to_atlas_records(_dataset(title=""))
    assert evidence["name"] == "GSE123"
    assert dataset is not None
    assert dataset["name"] == "GSE123"


def test_export_is_deterministic_and_deduplicated():
    records = export_records([_source(), _source()], [_dataset()])
    ids = [item["id"] for item in records]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert len(records) == 3


def test_jsonl_writer_emits_one_object_per_line(tmp_path):
    output = tmp_path / "atlas.jsonl"
    count = write_cardiatlas_jsonl(output, sources=[_source()], datasets=[_dataset()])
    lines = output.read_text(encoding="utf-8").splitlines()
    assert count == 3
    assert len(lines) == 3
    payloads = [json.loads(line) for line in lines]
    assert all(item["schema_version"] == "0.3" for item in payloads)
    assert [item["id"] for item in payloads] == sorted(item["id"] for item in payloads)
