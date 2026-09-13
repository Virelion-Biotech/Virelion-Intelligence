from __future__ import annotations

from collections.abc import Iterable

from .models import Claim, Evidence


def validate_provenance(claims: Iterable[Claim], evidence: Iterable[Evidence]) -> list[str]:
    evidence_list = list(evidence)
    evidence_by_claim = {e.claim_id for e in evidence_list}
    errors: list[str] = []
    for claim in claims:
        if not claim.source_id:
            errors.append(f"{claim.claim_id}: missing source_id")
        if claim.claim_id not in evidence_by_claim:
            errors.append(f"{claim.claim_id}: no supporting evidence")
    for item in evidence_list:
        if not item.source_id:
            errors.append(f"{item.evidence_id}: missing source_id")
        if not item.supporting_text.strip():
            errors.append(f"{item.evidence_id}: empty supporting_text")
    return errors


def validate_dataset_identity(identity_status: str) -> tuple[bool, str]:
    normalized = identity_status.strip().upper()
    if normalized == "RESOLVED":
        return True, "accepted"
    if normalized in {"UNRESOLVED", "REVIEW_REQUIRED", "AMBIGUOUS"}:
        return False, "automatic acceptance blocked"
    return False, f"unknown identity status: {identity_status}"
