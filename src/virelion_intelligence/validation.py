from __future__ import annotations

import re
from pathlib import Path

from .models import Claim, DatasetRecord, Evidence, SourceRecord

PLACEHOLDERS = ("% >>> REPLACE", "Headline one", "XXXX.XXXXX", "example.com", "Paper title")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)


def validate_source(source: SourceRecord) -> list[str]:
    errors: list[str] = []
    if not source.title.strip():
        errors.append("source title is empty")
    if not source.url.startswith(("http://", "https://")):
        errors.append("source URL must be HTTP(S)")
    if source.doi and not DOI_RE.match(source.doi):
        errors.append(f"invalid DOI: {source.doi}")
    return errors


def validate_claim_evidence(claim: Claim, evidence: Evidence, source: SourceRecord) -> list[str]:
    errors: list[str] = []
    if claim.source_id != source.source_id or evidence.source_id != source.source_id:
        errors.append("claim/evidence/source linkage mismatch")
    if evidence.claim_id != claim.claim_id:
        errors.append("evidence claim linkage mismatch")
    if not evidence.supporting_text.strip():
        errors.append("evidence has no supporting text")
    if claim.evidence_level == "E0":
        errors.append("unverified claim cannot pass publication validation")
    return errors


def validate_dataset(dataset: DatasetRecord) -> list[str]:
    errors: list[str] = []
    if dataset.identity_status in {"UNRESOLVED", "AMBIGUOUS"}:
        errors.append("dataset identity is unresolved")
    if dataset.suitability_status == "ACCEPTED" and dataset.identity_status != "RESOLVED":
        errors.append("accepted dataset must have RESOLVED identity")
    if dataset.sample_count is not None and dataset.sample_count == 0:
        errors.append("dataset has zero samples")
    return errors


def validate_report_text(text: str) -> list[str]:
    return [f"placeholder text remains: {p}" for p in PLACEHOLDERS if p in text]


def check_secret_paths(root: Path) -> list[str]:
    offenders: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and (path.name == ".env" or "logs" in path.parts):
            offenders.append(str(path.relative_to(root)))
    return offenders
