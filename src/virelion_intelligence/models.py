from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class EvidenceLevel(str, Enum):
    E0 = "E0"  # unverified
    E1 = "E1"  # secondary source
    E2 = "E2"  # primary publication
    E3 = "E3"  # primary + public code/data
    E4 = "E4"  # independent reproduction
    E5 = "E5"  # replicated across independent studies


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
    raw_payload_path: str | None = None


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
    evidence_depth: str = "M0"
    confidence: float = Field(ge=0, le=1)


class DatasetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: str
    accession: str
    title: str
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


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    pipeline_version: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_start: datetime
    window_end: datetime
    status: str = "CREATED"
    counts: dict[str, int] = Field(default_factory=dict)
