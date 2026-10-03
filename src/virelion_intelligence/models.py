from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceLevel(str, Enum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"


class EvidenceDepth(str, Enum):
    M0 = "M0"  # metadata only
    M1 = "M1"  # abstract
    M2 = "M2"  # full-text text
    M3 = "M3"  # full text + figures/tables
    M4 = "M4"  # full text + linked data/code


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: str
    title: str
    url: str
    accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: datetime | None = None
    publisher: str | None = None
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    accession: str | None = None
    abstract: str | None = None
    authority: str = "unknown"
    content_hash: str | None = None
    raw_payload_path: str | None = None
    tags: list[str] = Field(default_factory=list)


class PaperRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    title: str
    abstract: str | None = None
    url: str
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    publisher: str | None = None
    journal: str | None = None
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    domains: list[str] = Field(default_factory=list)
    content_hash: str | None = None
    relevance_score: float = Field(default=0, ge=0, le=100)
    fulltext_status: str = "metadata_only"


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    source_id: str
    text: str
    claim_type: str
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    extraction_confidence: float = Field(ge=0, le=1)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    claim_id: str
    source_id: str
    supporting_text: str
    location: str | None = None
    section: str | None = None
    figure: str | None = None
    population: dict[str, Any] = Field(default_factory=dict)
    intervention: str | None = None
    comparator: str | None = None
    outcome: str | None = None
    limitations: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    evidence_depth: EvidenceDepth = EvidenceDepth.M0
    confidence: float = Field(ge=0, le=1)


class DatasetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: str
    accession: str
    title: str
    url: str | None = None
    species: str | None = None
    tissue: str | None = None
    cell_type: str | None = None
    condition: str | None = None
    control: str | None = None
    assay: str | None = None
    platform: str | None = None
    sample_count: int | None = Field(default=None, ge=0)
    replicate_count: int | None = Field(default=None, ge=0)
    metadata_quality: float = Field(default=0, ge=0, le=1)
    identity_status: str = "UNRESOLVED"
    suitability_score: float = Field(default=0, ge=0, le=100)
    suitability_status: str = "REVIEW_REQUIRED"
    metadata_notes: list[str] = Field(default_factory=list)


class Opportunity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    opportunity_type: str
    title: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)
    dataset_ids: list[str] = Field(default_factory=list)
    virelion_modules: list[str] = Field(default_factory=list)
    scientific_importance: float = Field(ge=0, le=5)
    evidence_strength: float = Field(ge=0, le=5)
    reproducibility: float = Field(ge=0, le=5)
    data_availability: float = Field(ge=0, le=5)
    computational_feasibility: float = Field(ge=0, le=5)
    virelion_relevance: float = Field(ge=0, le=5)
    differentiation: float = Field(ge=0, le=5)
    translational_potential: float = Field(ge=0, le=5)
    overall_score: float = Field(ge=0, le=10)
    recommended_action: str = "WATCH"


class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float = Field(ge=0, le=1)
    rationale: str | None = None


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    pipeline_version: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    window_start: datetime
    window_end: datetime
    status: str = "CREATED"
    counts: dict[str, int] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)

    @field_validator("window_end")
    @classmethod
    def end_after_start(cls, value: datetime, info):
        start = info.data.get("window_start")
        if start and value < start:
            raise ValueError("window_end must be >= window_start")
        return value
