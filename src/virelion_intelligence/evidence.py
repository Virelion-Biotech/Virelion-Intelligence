from __future__ import annotations

import json
import uuid

from .llm import LLMClient
from .models import Claim, Evidence, EvidenceDepth, EvidenceLevel, SourceRecord

SYSTEM_PROMPT = """You are a biomedical evidence extraction engine. Never invent facts. Extract only what is explicitly supported by the provided source text. Return JSON with claim and evidence objects. Distinguish reported findings from interpretation and limitations."""


def heuristic_claim(source: SourceRecord) -> tuple[Claim, Evidence]:
    claim_id = f"C-{uuid.uuid4().hex[:12]}"
    evidence_id = f"E-{uuid.uuid4().hex[:12]}"
    text = source.abstract.strip() if source.abstract and source.abstract.strip() else ""
    # Without an abstract/full-text excerpt, a title alone is metadata rather than substantive evidence.
    level = EvidenceLevel.E2 if text and source.source_type == "literature" and source.authority == "primary" else EvidenceLevel.E1
    evidence_text = text or source.title.strip()
    depth = EvidenceDepth.M1 if text else EvidenceDepth.M0
    claim = Claim(
        claim_id=claim_id,
        source_id=source.source_id,
        text=evidence_text,
        claim_type="source_summary" if text else "metadata_summary",
        evidence_level=level,
        extraction_confidence=0.65 if text else 0.45,
    )
    evidence = Evidence(
        evidence_id=evidence_id,
        claim_id=claim_id,
        source_id=source.source_id,
        supporting_text=evidence_text,
        evidence_level=level,
        evidence_depth=depth,
        confidence=0.65 if text else 0.45,
    )
    return claim, evidence


def extract_from_source(source: SourceRecord, llm: LLMClient | None = None) -> tuple[Claim, Evidence]:
    if llm is None:
        return heuristic_claim(source)
    prompt = {
        "source_id": source.source_id,
        "title": source.title,
        "abstract": source.abstract,
        "url": source.url,
        "publisher": source.publisher,
        "publication_date": source.published_at.isoformat() if source.published_at else None,
    }
    data = llm.json([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
    ])
    claim_data = data.get("claim") or {}
    evidence_data = data.get("evidence") or {}
    claim_id = f"C-{uuid.uuid4().hex[:12]}"
    evidence_id = f"E-{uuid.uuid4().hex[:12]}"
    level = EvidenceLevel(claim_data.get("evidence_level", "E1"))
    claim = Claim(
        claim_id=claim_id,
        source_id=source.source_id,
        text=str(claim_data.get("text", "")).strip(),
        claim_type=str(claim_data.get("claim_type", "finding")),
        evidence_level=level,
        extraction_confidence=float(claim_data.get("confidence", 0)),
    )
    evidence = Evidence(
        evidence_id=evidence_id,
        claim_id=claim_id,
        source_id=source.source_id,
        supporting_text=str(evidence_data.get("supporting_text", "")).strip(),
        location=evidence_data.get("location"),
        section=evidence_data.get("section"),
        figure=evidence_data.get("figure"),
        population=evidence_data.get("population") or {},
        intervention=evidence_data.get("intervention"),
        comparator=evidence_data.get("comparator"),
        outcome=evidence_data.get("outcome"),
        limitations=evidence_data.get("limitations") or [],
        evidence_level=level,
        evidence_depth=EvidenceDepth(evidence_data.get("evidence_depth", "M1")),
        confidence=float(evidence_data.get("confidence", 0)),
    )
    return claim, evidence
