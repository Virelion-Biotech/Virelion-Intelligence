from virelion_intelligence.datasets import assess_dataset
from virelion_intelligence.dedupe import dedupe_against
from virelion_intelligence.models import DatasetRecord, Evidence, EvidenceLevel, Claim, SourceRecord
from virelion_intelligence.normalize import normalize_doi, normalize_pmid
from virelion_intelligence.validation import validate_claim_evidence, validate_dataset


def test_doi_and_pmid_normalization():
    assert normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"
    assert normalize_pmid("PMID: 12345") == "12345"


def test_dedupe_prefers_exact_doi():
    first = SourceRecord(source_id="S1", source_type="literature", title="Cardiac regeneration", url="https://example.org", doi="10.1000/test")
    second = SourceRecord(source_id="S2", source_type="literature", title="Other", url="https://example.org", doi="10.1000/other")
    from virelion_intelligence.pipeline import source_to_paper
    a = source_to_paper(first)
    b = source_to_paper(first)
    b.paper_id = "P2"
    decision = dedupe_against(b, [a])
    assert decision.duplicate is True
    assert decision.basis == "doi"


def test_provenance_requires_matching_source_and_evidence():
    source = SourceRecord(source_id="S1", source_type="literature", title="Finding", url="https://example.org")
    claim = Claim(claim_id="C1", source_id="S1", text="A finding", claim_type="SOURCE_FACT", evidence_level=EvidenceLevel.E2, extraction_confidence=0.9)
    evidence = Evidence(evidence_id="E1", claim_id="C1", source_id="S1", supporting_text="A finding was observed.", evidence_level=EvidenceLevel.E2, evidence_depth="M1", confidence=0.95)
    assert validate_claim_evidence(claim, evidence, source) == []


def test_unresolved_dataset_is_not_accepted():
    dataset = DatasetRecord(dataset_id="D1", source="GEO", accession="GSE123", title="test")
    assessed = assess_dataset(dataset)
    errors = validate_dataset(assessed)
    assert assessed.suitability_status == "REVIEW_REQUIRED"
    assert any("identity" in error for error in errors)
