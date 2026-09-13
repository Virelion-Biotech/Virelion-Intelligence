from datetime import datetime, timezone

from virelion_intelligence.dedupe import DedupeCandidate, deduplicate
from virelion_intelligence.models import Claim, Evidence, EvidenceLevel
from virelion_intelligence.validation import validate_dataset_identity, validate_provenance


def test_deduplicate_prefers_first_record():
    records = [
        DedupeCandidate("a", "Cardiac regeneration", doi="10.1000/X"),
        DedupeCandidate("b", "Cardiac regeneration", doi="10.1000/x"),
    ]
    unique, duplicates = deduplicate(records)
    assert [x.key for x in unique] == ["a"]
    assert list(duplicates.values()) == [["b"]]


def test_provenance_requires_evidence():
    claim = Claim(
        claim_id="C1",
        source_id="S1",
        text="A finding",
        claim_type="SOURCE_FACT",
        evidence_level=EvidenceLevel.E2,
        extraction_confidence=0.9,
    )
    evidence = Evidence(
        evidence_id="E1",
        claim_id="C1",
        source_id="S1",
        supporting_text="A finding was observed.",
        evidence_level=EvidenceLevel.E2,
        evidence_depth="M1",
        confidence=0.95,
    )
    assert validate_provenance([claim], [evidence]) == []


def test_unresolved_dataset_is_blocked():
    accepted, reason = validate_dataset_identity("UNRESOLVED")
    assert accepted is False
    assert "blocked" in reason
